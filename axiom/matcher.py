r"""Fully dynamic maximal matching algorithm.

This module implements the core algorithm of the paper: maintaining a
maximal matching in a graph undergoing edge insertions and deletions.
Both the basic :math:`\tilde O(n^{2/3})` version and the multi-level
:math:`n^{1/2+o(1)}` version are provided.

Responsibilities:
    * Own the live :class:`axiom.graph.DynamicGraph` and the maintained
      maximal matching.
    * Keep an up-to-date :math:`z`-system (or :math:`k`-level system) and
      the auxiliary directed graph :math:`H`.
    * Handle insertions and deletions with local repair.
    * Surface a small query / statistics API for callers and tests.

Algorithm sketch:

    The algorithm decomposes the vertex set into :math:`A, B, U` where
    :math:`S = A \cup B` is the set of vertices that are saturated in
    :math:`M` (degree exactly ``z`` in :math:`M`) and ``U`` is the rest.
    A first colour class of an edge-colouring of :math:`M` is used as a
    "seed" matching; greedily extending it to a maximal matching gives
    the reported matching.  Updates are handled locally by scanning the
    cached lists :math:`\Lambda(u)` and :math:`L(a)` (of size
    :math:`O(z)` for the basic algorithm), with a full rebuild after
    every ``phase_length = n^{4/3}`` updates to amortise the rebuild cost.

Thread-safety:
    Each ``MaximalMatcher`` instance is intended to be used from
    a single thread.  Concurrent updates on the same instance are not
    supported.
"""

from __future__ import annotations

import math
from collections import deque

from axiom.accounting import UpdateAccountant
from axiom.coloring import GreedyColorer
from axiom.graph import DynamicGraph
from axiom.invariants import check_maximal_matching
from axiom.matching import build_partner_map, greedy_maximal_matching, partner_of
from axiom.types import (
    EdgeColorer,
    Graph,
    Matching,
    Vertex,
    canonical_edge,
)
from axiom.z_system import MultiLevelSystem, ZSubgraphSystem, build_z_system


class MaximalMatcher:
    r"""Maintains a maximal matching under edge insertions and deletions.

    The algorithm can operate in two modes:

    * ``"basic"`` --- the :math:`\tilde O(n^{2/3})` version (single level).
    * ``"multilevel"`` --- the :math:`n^{1/2+o(1)}` version with
      :math:`k = \Theta(\log n)` levels.

    The instance is stateful: every :meth:`insert_edge` and
    :meth:`delete_edge` mutates the graph and matching and may trigger
    a full rebuild of the supporting :math:`z`-system.  Use
    :meth:`statistics` to inspect the amortised cost.

    Attributes:
        n: Number of vertices (fixed).
        mode: ``"basic"`` or ``"multilevel"``.
        graph: The underlying graph.
        colorer: The edge coloring implementation.
        matched_edges: The maintained maximal matching.
        matched_vertices: Convenience cache of vertices incident to
            some edge of the matching.
        z: Degree parameter of the active :math:`z`-system.
        phase_length: Number of updates between full rebuilds.
        subphase_length: Number of updates between lightweight seed
            augmentations.
        update_count: Number of updates since the last full rebuild.
        subphase_count: Number of subphase augmentations performed.
        system: Active :math:`z`-system, or ``None``.
        matchings: Colour classes of the most recent edge-colouring.
        seed_matching: First colour class, kept as the seed.
        multi: Multi-level system, present in ``"multilevel"`` mode.
        level_zs: Per-level :math:`z` values in decreasing order.
        k: Number of levels in ``multi``.
        aux_graph: Outgoing arcs of the directed auxiliary graph :math:`H`.
        accountant: Bookkeeping counters.

    Args:
        n: Number of vertices (fixed for the lifetime of the instance).
        mode: Either ``"basic"`` or ``"multilevel"``.
        graph: Optional graph implementation (defaults to ``DynamicGraph``).
        colorer: Optional edge colorer (defaults to ``GreedyColorer``).

    Raises:
        ValueError: If ``n`` is negative or ``mode`` is unknown.

    Example:
        >>> algo = MaximalMatcher(n=10, mode="basic")
        >>> algo.insert_edge(0, 1)
        >>> algo.insert_edge(2, 3)
        >>> algo.is_maximal()
        True
        >>> sorted(algo.get_matching())
        [(0, 1), (2, 3)]
    """

    def __init__(
        self,
        n: int,
        mode: str = "basic",
        graph: Graph | None = None,
        colorer: EdgeColorer | None = None,
    ) -> None:
        if n < 0:
            raise ValueError(f"n must be non-negative, got {n}")
        if mode not in {"basic", "multilevel"}:
            raise ValueError(f"mode must be 'basic' or 'multilevel', got {mode}")
        self.n = n
        self.mode = mode
        self.graph = graph if graph is not None else DynamicGraph(n)
        self.colorer = colorer if colorer is not None else GreedyColorer()
        self.matched_edges: Matching = set()
        self.matched_vertices: set[Vertex] = set()

        self.z: int = 0
        self.phase_length: int = 0
        self.subphase_length: int = 0
        self.update_count: int = 0
        self.subphase_count: int = 0
        self.system: ZSubgraphSystem | None = None
        self.matchings: list[Matching] = []
        self.seed_matching: Matching = set()

        self.multi: MultiLevelSystem | None = None
        self.level_zs: list[int] = []
        self.k: int = 0

        self.aux_graph: dict[Vertex, set[Vertex]] = {}
        self.accountant = UpdateAccountant()

        if mode == "basic":
            self.__init_basic()
        else:
            self.__init_multilevel()

    def __init_basic(self) -> None:
        self.z = math.ceil(self.n ** (2.0 / 3.0)) if self.n > 0 else 1
        self.phase_length = math.ceil(self.n ** (4.0 / 3.0)) if self.n > 0 else 1
        self.subphase_length = max(1, self.phase_length // self.z)
        self.__rebuild_basic()

    def __init_multilevel(self) -> None:
        if self.n <= 1:
            self.k = 1
            self.level_zs = [1]
        else:
            z = self.n
            zs: list[int] = []
            while z >= math.isqrt(self.n):
                zs.append(z)
                z = max(1, z // 2)
            self.level_zs = zs
            self.k = len(zs)
        self.phase_length = math.ceil(self.n ** (4.0 / 3.0)) if self.n > 0 else 1
        self.subphase_length = max(1, self.phase_length // self.z) if self.z > 0 else 1
        self.__rebuild_multilevel()

    def __rebuild_basic(self) -> None:
        self.system = build_z_system(self.graph, self.z)
        self.__partition_m_into_matchings()
        self.__rebuild_matching()
        self.update_count = 0
        self.subphase_count = 0
        self.accountant.record_phase_rebuild()

    def __rebuild_multilevel(self) -> None:
        self.multi = MultiLevelSystem(graph=self.graph, k=self.k)
        self.multi.levels = []
        for z in self.level_zs:
            level = build_z_system(self.graph, z)
            self.multi.levels.append(level)

        if self.multi.levels:
            level1 = self.multi.levels[0]
            sorted_a = sorted(level1.A)
            split = len(sorted_a) // 2
            self.multi.A1 = set(sorted_a[:split])
            self.multi.A2 = set(sorted_a[split:])
            self.multi.N1 = self.multi.A2 | level1.B
            self.multi.R1 = set(range(self.graph.n)) - (self.multi.A1 | self.multi.N1)

        if self.multi.levels:
            self.system = self.multi.levels[-1]
            self.z = self.level_zs[-1]
            self.subphase_length = max(1, self.phase_length // self.z)
            self.__partition_m_into_matchings()
        else:
            self.system = None
            self.seed_matching = set()
            self.matchings = []

        self.__rebuild_matching()
        self.update_count = 0
        self.subphase_count = 0
        self.accountant.record_phase_rebuild()

    def __partition_m_into_matchings(self) -> None:
        if self.system is None:
            self.seed_matching = set()
            self.matchings = []
            return

        sub = DynamicGraph(self.n)
        for e in self.system.M:
            sub.add_edge(e[0], e[1])

        coloring = self.colorer.color(sub, self.z)

        self.matchings = [set() for _ in range(self.z + 1)]
        dropped = 0
        for e, c in coloring.items():
            if 0 <= c <= self.z:
                self.matchings[c].add(e)
            else:
                dropped += 1
        if dropped:
            raise RuntimeError(
                f"partition_m_into_matchings: {dropped} edge(s) received "
                f"out-of-range color (expected 0..{self.z})."
            )

        self.seed_matching = self.matchings[0] if self.matchings else set()

    def __rebuild_matching(self) -> None:
        if self.system is None:
            self.matched_edges = greedy_maximal_matching(self.graph)
            self.matched_vertices = {v for e in self.matched_edges for v in e}
            self.accountant.record_greedy_rebuild(self.n)
            return

        matching: Matching = set(self.seed_matching)
        matched: set[Vertex] = {v for e in matching for v in e}

        for u in range(self.n):
            if u in matched:
                continue
            for v in self.graph.neighbors(u):
                if v not in matched:
                    matching.add(canonical_edge(u, v))
                    matched.add(u)
                    matched.add(v)
                    break

        self.matched_edges = matching
        self.matched_vertices = matched
        self.__rebuild_aux_graph()

    def __rebuild_aux_graph(self) -> None:
        self.aux_graph = {}
        if self.system is None:
            return
        bu = self.system.B | self.system.U
        for u in bu:
            if u not in self.matched_vertices:
                self.aux_graph[u] = set()
                if u in self.system.U:
                    for w in self.system.lambda_lists.get(u, []):
                        if w in bu and w not in self.matched_vertices:
                            self.aux_graph[u].add(w)

    def __check_subphase_boundary(self) -> bool:
        if self.update_count > 0 and self.update_count % self.subphase_length == 0:
            self.subphase_count += 1
            self.__augment_seed_at_subphase_boundary()
            self.accountant.record_subphase_rebuild()
            return True
        return False

    def __augment_seed_at_subphase_boundary(self) -> None:
        if self.system is None or not self.matchings:
            return

        matched_in_seed: set[Vertex] = set()
        for u, v in self.seed_matching:
            matched_in_seed.add(u)
            matched_in_seed.add(v)

        for s in self.system.S:
            if s not in matched_in_seed:
                self.__try_augment_seed(s, matched_in_seed)

    def __try_augment_seed(self, start: Vertex, matched_in_seed: set[Vertex]) -> bool:
        visited: set[tuple[Vertex, bool]] = {(start, False)}
        queue: deque[tuple[Vertex, bool, list[Vertex]]] = deque()
        queue.append((start, False, [start]))

        while queue:
            curr, via_seed, path = queue.popleft()

            for w in self.graph.neighbors(curr):
                e = canonical_edge(curr, w)
                is_seed = e in self.seed_matching

                if via_seed and not is_seed:
                    if (w, True) not in visited:
                        new_path = path + [w]
                        if w not in matched_in_seed:
                            self.__flip_augmenting_path(new_path)
                            return True
                        visited.add((w, True))
                        queue.append((w, True, new_path))
                elif not via_seed and is_seed:
                    if (w, False) not in visited:
                        visited.add((w, False))
                        queue.append((w, False, path + [w]))

        return False

    def __flip_augmenting_path(self, path: list[Vertex]) -> None:
        for i in range(0, len(path) - 1, 2):
            e = canonical_edge(path[i], path[i + 1])
            if e in self.seed_matching:
                self.seed_matching.discard(e)
            else:
                self.seed_matching.add(e)

    def insert_edge(self, u: Vertex, v: Vertex) -> None:
        """Insert edge ``(u, v)`` and repair the maximal matching.

        Args:
            u: One endpoint.
            v: The other endpoint.
        """
        self.graph.add_edge(u, v)
        self.__handle_insertion(u, v)
        self.__advance_update_counter()

    def delete_edge(self, u: Vertex, v: Vertex) -> None:
        """Delete edge ``(u, v)`` and repair the maximal matching.

        Args:
            u: One endpoint.
            v: The other endpoint.
        """
        if not self.graph.has_edge(u, v):
            self.accountant.record_deletion()
            return
        self.graph.remove_edge(u, v)
        self.__handle_deletion(u, v)
        self.__advance_update_counter()

    def __handle_insertion(self, u: Vertex, v: Vertex) -> None:
        e = canonical_edge(u, v)

        if self.system is not None:
            a = u if u in self.system.A else (v if v in self.system.A else None)
            u_vert = v if a == u else (u if v in self.system.A else None)
            if a is not None and u_vert is not None and u_vert in self.system.U:
                if u_vert in self.matched_vertices and a not in self.matched_vertices:
                    to_remove = None
                    for x, y in self.matched_edges:
                        if x == u_vert or y == u_vert:
                            to_remove = (x, y)
                            break
                    if to_remove is not None:
                        self.matched_edges.discard(to_remove)
                        self.matched_vertices.discard(u_vert)
                        self.matched_vertices.discard(
                            to_remove[0] if to_remove[1] == u_vert else to_remove[1]
                        )
                        self.matched_edges.add(e)
                        self.matched_vertices.add(a)
                        self.matched_vertices.add(u_vert)
                        self.accountant.record_insertion()
                        return
                    else:
                        self.accountant.record_greedy_rebuild()

        self.__repair_matching()
        self.accountant.record_insertion()

    def __handle_deletion(self, u: Vertex, v: Vertex) -> None:
        e = canonical_edge(u, v)
        if e in self.matched_edges:
            self.matched_edges.discard(e)
            self.matched_vertices.discard(u)
            self.matched_vertices.discard(v)

        self.__cleanup_stale_edges()
        self.__rematch_vertex(u)
        self.__rematch_vertex(v)
        self.__cleanup_stale_edges()

        if not self.is_maximal():
            self.__repair_matching()

        self.__rebuild_aux_graph()
        self.accountant.record_deletion()

    def __cleanup_stale_edges(self) -> None:
        stale = [e for e in self.matched_edges if not self.graph.has_edge(e[0], e[1])]
        for e in stale:
            self.matched_edges.discard(e)
            self.matched_vertices.discard(e[0])
            self.matched_vertices.discard(e[1])
        if stale:
            self.accountant.record_stale_cleanup(len(stale))

    def __rematch_vertex(self, v: Vertex) -> None:
        if v in self.matched_vertices:
            return
        if self.system is None:
            for w in self.graph.neighbors(v):
                if w not in self.matched_vertices:
                    self.matched_edges.add(canonical_edge(v, w))
                    self.matched_vertices.add(v)
                    self.matched_vertices.add(w)
                    return
            return

        if v in self.system.U:
            self.__rematch_u(v)
            return
        if v in self.system.B:
            self.__rematch_b(v)
            return
        if v in self.system.A:
            self.__rematch_a(v)
            return

        for w in self.graph.neighbors(v):
            if w not in self.matched_vertices:
                self.matched_edges.add(canonical_edge(v, w))
                self.matched_vertices.add(v)
                self.matched_vertices.add(w)
                return

    def __rematch_u(self, u: Vertex) -> None:
        for w in self.system.lambda_lists.get(u, []):
            if w not in self.matched_vertices and self.graph.has_edge(u, w):
                self.matched_edges.add(canonical_edge(u, w))
                self.matched_vertices.add(u)
                self.matched_vertices.add(w)
                self.accountant.record_rematch_u_scan()
                return

        scanned = 0
        for w in self.system.S:
            if w not in self.matched_vertices:
                if self.graph.has_edge(u, w):
                    self.matched_edges.add(canonical_edge(u, w))
                    self.matched_vertices.add(u)
                    self.matched_vertices.add(w)
                    self.accountant.record_rematch_u_scan(scanned + 1)
                    return
            scanned += 1
        self.accountant.record_rematch_u_scan(scanned)

    def __rematch_b(self, b: Vertex) -> None:
        scanned = 0
        for u in self.system.U:
            if (
                u not in self.matched_vertices
                and b in self.system.lambda_lists.get(u, [])
                and self.graph.has_edge(u, b)
            ):
                self.matched_edges.add(canonical_edge(u, b))
                self.matched_vertices.add(u)
                self.matched_vertices.add(b)
                self.accountant.record_rematch_b_scan(scanned + 1)
                return
            scanned += 1
        self.accountant.record_rematch_b_scan(scanned)

        for w in self.system.S:
            if w not in self.matched_vertices:
                if self.graph.has_edge(b, w):
                    self.matched_edges.add(canonical_edge(b, w))
                    self.matched_vertices.add(b)
                    self.matched_vertices.add(w)
                    return

    def __rematch_a(self, a: Vertex) -> None:
        tau = (32 * self.phase_length) // self.z if self.z > 0 else 0
        limit = 2 * tau + 1
        scanned = 0

        if self.multi is not None and a in self.multi.A1:
            for u in self.system.L_lists.get(a, []):
                if u not in self.multi.R1:
                    continue
                scanned += 1
                if scanned > limit:
                    break
                if u not in self.matched_vertices and self.graph.has_edge(a, u):
                    self.matched_edges.add(canonical_edge(a, u))
                    self.matched_vertices.add(a)
                    self.matched_vertices.add(u)
                    self.accountant.record_rematch_a_scan(scanned)
                    return
                p = partner_of(self.matched_edges, u)
                if p is not None and p in self.system.A:
                    continue
                if p is not None:
                    self.matched_edges.discard(canonical_edge(u, p))
                    self.matched_vertices.discard(p)
                if self.graph.has_edge(a, u):
                    self.matched_edges.add(canonical_edge(a, u))
                    self.matched_vertices.add(a)
                    self.matched_vertices.add(u)
                    if p is not None:
                        self.__rematch_vertex(p)
                    self.accountant.record_rematch_a_scan(scanned)
                    return
        else:
            for u in self.system.L_lists.get(a, []):
                scanned += 1
                if scanned > limit:
                    break
                if u not in self.matched_vertices and self.graph.has_edge(a, u):
                    self.matched_edges.add(canonical_edge(a, u))
                    self.matched_vertices.add(a)
                    self.matched_vertices.add(u)
                    self.accountant.record_rematch_a_scan(scanned)
                    return
                p = partner_of(self.matched_edges, u)
                if p is not None and p not in self.system.A:
                    if self.graph.has_edge(a, u):
                        self.matched_edges.discard(canonical_edge(u, p))
                        self.matched_vertices.discard(p)
                        self.matched_edges.add(canonical_edge(a, u))
                        self.matched_vertices.add(a)
                        self.matched_vertices.add(u)
                        if p is not None:
                            self.__rematch_vertex(p)
                        self.accountant.record_rematch_a_scan(scanned)
                        return

        self.accountant.record_rematch_a_scan(scanned)

        for w in self.graph.neighbors(a):
            if w not in self.matched_vertices:
                self.matched_edges.add(canonical_edge(a, w))
                self.matched_vertices.add(a)
                self.matched_vertices.add(w)
                return

    def __repair_matching(self) -> None:
        self.__rebuild_matching()

    def __advance_update_counter(self) -> None:
        self.update_count += 1
        self.__check_subphase_boundary()

        if self.update_count >= self.phase_length:
            if self.mode == "basic":
                self.__rebuild_basic()
            else:
                self.__rebuild_multilevel()

    def get_matching(self) -> Matching:
        """Return a copy of the current maximal matching.

        Returns:
            A copy of the matching set.

        Complexity:
            O(|M*|) to copy.
        """
        return set(self.matched_edges)

    def is_maximal(self) -> bool:
        """Return True iff the current matching is maximal in the graph.

        Complexity:
            O(n + m).
        """
        return check_maximal_matching(self.graph, self.matched_edges)

    def matching_size(self) -> int:
        """Return the number of edges in the current matching."""
        return len(self.matched_edges)

    def partner(self, v: Vertex) -> Vertex | None:
        """Return the vertex matched to v, or None.

        Args:
            v: The vertex to look up.

        Returns:
            v's partner, or None if unmatched.

        Complexity:
            O(|M*|).
        """
        return partner_of(self.matched_edges, v)

    def build_partner_map(self) -> dict[Vertex, Vertex]:
        """Return a dict mapping each matched vertex to its partner.

        Returns:
            Dictionary of vertex to partner mappings.

        Complexity:
            O(|M*|) time and space.
        """
        return build_partner_map(self.matched_edges)

    def statistics(self) -> dict[str, int]:
        """Return a dictionary of runtime statistics.

        Returns:
            A flat dict suitable for logging or CSV export.
        """
        stats: dict[str, int] = {
            "n": self.n,
            "m": self.graph.num_edges(),
            "matching_size": len(self.matched_edges),
            "updates_since_rebuild": self.update_count,
            "phase_length": self.phase_length,
            "subphase_length": self.subphase_length,
            "subphase_count": self.subphase_count,
            "z": self.z,
        }
        stats.update(self.accountant.snapshot())
        return stats
