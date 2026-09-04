"""Invariant checkers for the :math:`z`-subgraph system and maximal matching.

These functions provide standalone validation that can be called from tests
or debugging scripts.  They do not modify state; they are read-only
diagnostics intended to make regressions visible immediately during
development.

Mathematical background:
    The :math:`z`-subgraph system carries six invariants whose conjunction
    guarantees the :math:`\tilde O(n^{2/3})` per-update cost of the
    basic algorithm (Section 2 of the paper).  They are validated
    individually by the methods of :class:`ZSubgraphSystem` and bundled
    here so that external code (tests, benchmarks) can call a single
    entry point.

    Invariant (I3) for the multi-level system requires a precise
    constant that the paper excerpt omits; we therefore refuse to give
    a definitive answer rather than risk silently accepting a false
    positive.
"""

from __future__ import annotations

from axiom.types import Graph, Matching, Vertex
from axiom.z_system import MultiLevelSystem, ZSubgraphSystem


def check_z_system_invariants(system: ZSubgraphSystem) -> bool:
    """Return ``True`` iff every invariant of ``system`` holds.

    Thin wrapper around :meth:`ZSubgraphSystem.check_all_invariants`;
    surfaced as a module-level function so callers do not need to import
    the ``z_system`` module directly.

    Complexity:
        :math:`O(n + m)`.
    """
    return system.check_all_invariants()


def check_maximal_matching(graph: Graph, matching: Matching) -> bool:
    """Return ``True`` iff ``matching`` is maximal in ``graph``.

    A matching is maximal when no edge can be added to it without
    violating the matching property.  This is distinct from being of
    maximum cardinality: a maximal matching is a local optimum, not a
    global one.

    Args:
        graph: The host graph.
        matching: Candidate matching.

    Returns:
        ``True`` iff every unmatched vertex has only matched neighbours.

    Complexity:
        :math:`O(n + m)` -- each vertex is examined once and every
        edge of an unmatched vertex is inspected.
    """
    matched_vertices: set[Vertex] = set()
    for u, v in matching:
        matched_vertices.add(u)
        matched_vertices.add(v)

    for u in range(graph.n):
        if u in matched_vertices:
            continue
        for w in graph.neighbors(u):
            if w not in matched_vertices:
                return False
    return True


def check_multi_level_i3(multi: MultiLevelSystem) -> bool:
    """Return ``True`` iff invariant (I3) is satisfied for ``multi``.

    Wraps :meth:`MultiLevelSystem.level_1_invariant_I3` and converts
    the unavoidable :class:`NotImplementedError` into a ``False``
    answer.  This makes the invariant conservative: the checker will
    *never* silently pass.

    **Fidelity note:** The paper states (I3) as ``O(r / z)`` but does
    not give the exact constant in the excerpt.  This module makes no
    attempt to guess it.
    """
    try:
        return multi.level_1_invariant_I3()
    except NotImplementedError:
        return False
