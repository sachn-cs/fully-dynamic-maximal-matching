"""Comprehensive unit tests for the FDMM reproduction.

Tests cover graph layer, edge colouring, :math:`z`-system construction and
invariants, dynamic update maintenance, accounting counters, simulation
utilities, and stress tests.
"""

from __future__ import annotations

import random

import pytest

from axiom.coloring import VizingColorer
from axiom.graph import DynamicGraph
from axiom.invariants import check_maximal_matching
from axiom.core import Matcher
from axiom.matching import build_partner_map, greedy_maximal_matching, partner_of
from axiom.simulation import random_update_sequence, replay_updates
from axiom.types import canonical_edge
from axiom.z_system import MultiLevelSystem, ZSubgraphSystem, build_z_system

# ------------------------------------------------------------------
# Graph layer
# ------------------------------------------------------------------


class TestDynamicGraph:
    """Tests for :class:`axiom.graph.DynamicGraph`."""

    def test_empty_graph(self) -> None:
        g = DynamicGraph(5)
        assert g.n == 5
        assert g.num_edges() == 0
        assert g.degree(0) == 0

    def test_add_edge(self) -> None:
        g = DynamicGraph(4)
        g.add_edge(0, 1)
        assert g.has_edge(0, 1)
        assert g.has_edge(1, 0)
        assert g.degree(0) == 1
        assert g.degree(1) == 1

    def test_remove_edge(self) -> None:
        g = DynamicGraph(4)
        g.add_edge(0, 1)
        g.remove_edge(0, 1)
        assert not g.has_edge(0, 1)
        assert g.degree(0) == 0

    def test_duplicate_insert_ignored(self) -> None:
        g = DynamicGraph(3)
        g.add_edge(0, 1)
        g.add_edge(0, 1)
        assert g.num_edges() == 1

    def test_self_loop_ignored(self) -> None:
        g = DynamicGraph(3)
        g.add_edge(0, 0)
        assert g.num_edges() == 0

    def test_neighbors(self) -> None:
        g = DynamicGraph(4)
        g.add_edge(0, 1)
        g.add_edge(0, 2)
        assert set(g.neighbors(0)) == {1, 2}

    def test_edges_iterator(self) -> None:
        g = DynamicGraph(4)
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        edges = set(g.edges())
        assert edges == {(0, 1), (1, 2)}

    def test_invalid_vertex(self) -> None:
        g = DynamicGraph(3)
        with pytest.raises(ValueError):
            g.degree(5)

    def test_copy(self) -> None:
        g = DynamicGraph(3)
        g.add_edge(0, 1)
        h = g.copy()
        h.remove_edge(0, 1)
        assert g.has_edge(0, 1)
        assert not h.has_edge(0, 1)

    def test_single_vertex(self) -> None:
        g = DynamicGraph(1)
        g.add_edge(0, 0)
        assert g.num_edges() == 0
        assert list(g.edges()) == []

    def test_zero_vertices(self) -> None:
        g = DynamicGraph(0)
        assert g.num_edges() == 0
        assert list(g.edges()) == []

    def test_complete_graph(self) -> None:
        n = 5
        g = DynamicGraph(n)
        for i in range(n):
            for j in range(i + 1, n):
                g.add_edge(i, j)
        assert g.num_edges() == n * (n - 1) // 2
        for v in range(n):
            assert g.degree(v) == n - 1

    def test_bipartite_graph(self) -> None:
        n, m = 3, 4
        g = DynamicGraph(n + m)
        for i in range(n):
            for j in range(m):
                g.add_edge(i, n + j)
        assert g.num_edges() == n * m
        for i in range(n):
            assert g.degree(i) == m
        for j in range(m):
            assert g.degree(n + j) == n

    def test_edges_no_duplicates(self) -> None:
        g = DynamicGraph(3)
        g.add_edge(0, 1)
        g.add_edge(1, 0)
        assert len(list(g.edges())) == 1

    def test_remove_nonexistent_edge(self) -> None:
        g = DynamicGraph(3)
        g.remove_edge(0, 1)
        assert g.num_edges() == 0

    def test_large_graph_degree(self) -> None:
        n = 1000
        g = DynamicGraph(n)
        for i in range(n - 1):
            g.add_edge(i, i + 1)
        assert g.num_edges() == n - 1
        assert g.degree(0) == 1
        assert g.degree(n - 1) == 1

    def test_copy_isolation(self) -> None:
        g = DynamicGraph(5)
        g.add_edge(0, 1)
        g.add_edge(2, 3)
        h = g.copy()
        h.add_edge(0, 2)
        assert not g.has_edge(0, 2)
        assert h.has_edge(0, 2)

    def test_neighbors_on_isolated_vertex(self) -> None:
        g = DynamicGraph(5)
        g.add_edge(0, 1)
        assert set(g.neighbors(2)) == set()

    def test_strict_self_loop_raises(self) -> None:
        g = DynamicGraph(3)
        with pytest.raises(ValueError):
            g.add_edge(0, 0, strict=True)

    def test_strict_duplicate_raises(self) -> None:
        g = DynamicGraph(3)
        g.add_edge(0, 1)
        with pytest.raises(ValueError):
            g.add_edge(0, 1, strict=True)

    def test_strict_missing_delete_raises(self) -> None:
        g = DynamicGraph(3)
        with pytest.raises(ValueError):
            g.remove_edge(0, 1, strict=True)


# ------------------------------------------------------------------
# Edge colouring
# ------------------------------------------------------------------


class TestEdgeColoring:
    """Tests for :mod:`axiom.coloring`."""

    def _is_proper(self, graph: DynamicGraph, coloring: dict) -> bool:
        for u in range(graph.n):
            seen: set[int] = set()
            for v in graph.neighbors(u):
                e = canonical_edge(u, v)
                c = coloring[e]
                if c in seen:
                    return False
                seen.add(c)
        return True

    def test_triangle(self) -> None:
        g = DynamicGraph(3)
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 0)
        coloring = VizingColorer().color(g, 2)
        assert len(set(coloring.values())) <= 3
        assert self._is_proper(g, coloring)

    def test_star(self) -> None:
        g = DynamicGraph(5)
        for i in range(1, 5):
            g.add_edge(0, i)
        coloring = VizingColorer().color(g, 4)
        assert len(set(coloring.values())) <= 5
        assert self._is_proper(g, coloring)

    def test_path(self) -> None:
        g = DynamicGraph(4)
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        coloring = VizingColorer().color(g, 2)
        assert len(set(coloring.values())) <= 3
        assert self._is_proper(g, coloring)

    def test_empty_graph(self) -> None:
        g = DynamicGraph(3)
        coloring = VizingColorer().color(g, 0)
        assert coloring == {}

    def test_cycle(self) -> None:
        g = DynamicGraph(5)
        for i in range(5):
            g.add_edge(i, (i + 1) % 5)
        coloring = VizingColorer().color(g, 2)
        assert len(set(coloring.values())) <= 3
        assert self._is_proper(g, coloring)

    def test_complete_graph_odd(self) -> None:
        n = 5
        g = DynamicGraph(n)
        for i in range(n):
            for j in range(i + 1, n):
                g.add_edge(i, j)
        coloring = VizingColorer().color(g, n - 1)
        assert len(set(coloring.values())) <= n
        assert self._is_proper(g, coloring)

    def test_complete_graph_even(self) -> None:
        n = 6
        g = DynamicGraph(n)
        for i in range(n):
            for j in range(i + 1, n):
                g.add_edge(i, j)
        coloring = VizingColorer().color(g, n - 1)
        assert len(set(coloring.values())) <= n
        assert self._is_proper(g, coloring)

    def test_disconnected_components(self) -> None:
        g = DynamicGraph(6)
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 0)
        g.add_edge(3, 4)
        g.add_edge(4, 5)
        g.add_edge(5, 3)
        coloring = VizingColorer().color(g, 2)
        assert len(set(coloring.values())) <= 3
        assert self._is_proper(g, coloring)

    def test_single_edge(self) -> None:
        g = DynamicGraph(2)
        g.add_edge(0, 1)
        coloring = VizingColorer().color(g, 1)
        assert len(set(coloring.values())) == 1
        assert self._is_proper(g, coloring)

    def test_two_parallel_paths(self) -> None:
        g = DynamicGraph(6)
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(3, 4)
        g.add_edge(4, 5)
        coloring = VizingColorer().color(g, 2)
        assert len(set(coloring.values())) <= 3
        assert self._is_proper(g, coloring)

    def test_coloring_all_edges_present(self) -> None:
        g = DynamicGraph(4)
        g.add_edge(0, 1)
        g.add_edge(0, 2)
        g.add_edge(1, 2)
        coloring = VizingColorer().color(g, 2)
        assert len(coloring) == g.num_edges()
        for e in g.edges():
            assert e in coloring


# ------------------------------------------------------------------
# Matching helpers
# ------------------------------------------------------------------


class TestMatchingHelpers:
    """Tests for :mod:`axiom.matching`."""

    def test_greedy_maximal_matching(self) -> None:
        g = DynamicGraph(4)
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        m = greedy_maximal_matching(g)
        assert check_maximal_matching(g, m)

    def test_greedy_empty_graph(self) -> None:
        g = DynamicGraph(3)
        m = greedy_maximal_matching(g)
        assert m == set()

    def test_partner_of(self) -> None:
        m = {(0, 1), (2, 3)}
        assert partner_of(m, 0) == 1
        assert partner_of(m, 3) == 2
        assert partner_of(m, 5) is None

    def test_build_partner_map(self) -> None:
        m = {(0, 1), (2, 3)}
        pmap = build_partner_map(m)
        assert pmap == {0: 1, 1: 0, 2: 3, 3: 2}


# ------------------------------------------------------------------
# z-Subgraph system
# ------------------------------------------------------------------


class TestZSubgraphSystem:
    """Tests for :class:`axiom.z_system.ZSubgraphSystem`."""

    def test_basic_properties(self) -> None:
        g = DynamicGraph(6)
        g.add_edge(0, 1)
        g.add_edge(0, 2)
        g.add_edge(1, 2)
        g.add_edge(3, 4)
        g.add_edge(4, 5)

        system = ZSubgraphSystem(graph=g, z=2)
        system.A = {0, 1, 2}
        system.B = {3, 4}
        system.U = {5}
        system.M = {(0, 1), (3, 4)}
        system.build_lambda_and_L()

        assert system.S == {0, 1, 2, 3, 4}
        assert system.degree_in_M(0) == 1
        assert system.degree_in_M(5) == 0
        assert system.check_P2()

    def test_lambda_lists(self) -> None:
        g = DynamicGraph(4)
        g.add_edge(0, 1)
        g.add_edge(0, 2)
        g.add_edge(0, 3)
        system = ZSubgraphSystem(graph=g, z=2)
        system.U = {0}
        system.B = {1, 2}
        system.A = {3}
        system.build_lambda_and_L()
        assert set(system.lambda_lists[0]) == {1, 2}
        assert set(system.L_lists[3]) == {0}

    def test_maximal_matching_check(self) -> None:
        g = DynamicGraph(4)
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        system = ZSubgraphSystem(graph=g, z=2)
        assert system.is_maximal_matching({(0, 1), (2, 3)})
        assert not system.is_maximal_matching({(0, 1)})

    def test_empty_graph_maximal(self) -> None:
        g = DynamicGraph(3)
        system = ZSubgraphSystem(graph=g, z=1)
        assert system.is_maximal_matching(set())

    def test_single_edge_maximal(self) -> None:
        g = DynamicGraph(2)
        g.add_edge(0, 1)
        system = ZSubgraphSystem(graph=g, z=1)
        assert system.is_maximal_matching({(0, 1)})

    def test_check_degree_bounds_empty(self) -> None:
        g = DynamicGraph(3)
        system = ZSubgraphSystem(graph=g, z=1)
        system.A = set()
        system.B = set()
        system.U = {0, 1, 2}
        assert system.check_degree_bounds()

    def test_P1_violation(self) -> None:
        g = DynamicGraph(4)
        for i in range(3):
            g.add_edge(3, i)
        system = ZSubgraphSystem(graph=g, z=1)
        system.U = {3}
        system.B = {0, 1, 2}
        system.A = set()
        assert not system.check_P1()

    def test_P2_violation(self) -> None:
        g = DynamicGraph(3)
        g.add_edge(0, 2)
        system = ZSubgraphSystem(graph=g, z=1)
        system.A = {0}
        system.B = set()
        system.U = {1, 2}
        system.M = {(0, 2)}
        assert not system.check_P2()

    def test_all_invariants_on_empty(self) -> None:
        g = DynamicGraph(0)
        system = ZSubgraphSystem(graph=g, z=0)
        assert system.check_all_invariants()

    def test_degree_in_M_on_unmatched_vertex(self) -> None:
        g = DynamicGraph(4)
        g.add_edge(0, 1)
        system = ZSubgraphSystem(graph=g, z=1)
        system.M = {(0, 1)}
        assert system.degree_in_M(2) == 0

    def test_neighbors_in_M(self) -> None:
        g = DynamicGraph(4)
        g.add_edge(0, 1)
        g.add_edge(0, 2)
        system = ZSubgraphSystem(graph=g, z=2)
        system.M = {(0, 1), (0, 2)}
        assert set(system.neighbors_in_M(0)) == {1, 2}
        assert set(system.neighbors_in_M(1)) == {0}


# ------------------------------------------------------------------
# z-System construction
# ------------------------------------------------------------------


class TestBuildZSystem:
    """Tests for :func:`axiom.z_system.build_z_system`."""

    def test_build_on_empty_graph(self) -> None:
        g = DynamicGraph(4)
        system = build_z_system(g, z=1)
        assert system.check_degree_bounds()
        assert system.check_U_degree_in_U()

    def test_build_on_path(self) -> None:
        g = DynamicGraph(5)
        for i in range(4):
            g.add_edge(i, i + 1)
        system = build_z_system(g, z=2)
        assert system.check_degree_bounds()
        assert system.check_P2()

    def test_build_step_one_partition(self) -> None:
        """Verify that A, B, U are defined from M, not from G-degree."""
        g = DynamicGraph(4)
        # star: vertex 0 has degree 3, leaves degree 1
        for i in range(1, 4):
            g.add_edge(0, i)
        system = build_z_system(g, z=2)
        # M is a greedy maximal matching with cap 2.
        # It will contain (0,1) and (0,2).  Vertex 0 now has degree 2 in M -> S.
        # Leaves 1 and 2 have degree 1 in M (< 2) -> U.
        # Vertex 3 has degree 0 in M -> U.
        assert 0 in system.S
        assert system.degree_in_M(0) == 2
        assert 1 in system.U or 1 in system.S
        assert 2 in system.U or 2 in system.S
        assert 3 in system.U

    def test_build_invariants(self) -> None:
        g = DynamicGraph(10)
        for i in range(9):
            g.add_edge(i, i + 1)
        system = build_z_system(g, z=2)
        assert system.check_degree_bounds()
        assert system.check_P2()
        assert system.check_lambda_lists()
        assert system.check_L_lists()


# ------------------------------------------------------------------
# Dynamic maximal matching algorithm
# ------------------------------------------------------------------


class TestMatcher:
    """End-to-end tests for :class:`axiom.core.Matcher`."""

    def test_basic_init(self) -> None:
        algo = Matcher(10, mode="basic")
        assert algo.n == 10
        assert algo.mode == "basic"
        assert algo.is_maximal()

    def test_multilevel_init(self) -> None:
        algo = Matcher(10, mode="multilevel")
        assert algo.mode == "multilevel"
        assert algo.is_maximal()

    def test_insert_then_delete_basic(self) -> None:
        algo = Matcher(4, mode="basic")
        algo.insert_edge(0, 1)
        assert algo.is_maximal()
        algo.insert_edge(1, 2)
        assert algo.is_maximal()
        algo.insert_edge(2, 3)
        assert algo.is_maximal()

        algo.delete_edge(0, 1)
        assert algo.is_maximal()
        algo.delete_edge(1, 2)
        assert algo.is_maximal()
        algo.delete_edge(2, 3)
        assert algo.is_maximal()

    def test_insert_then_delete_multilevel(self) -> None:
        algo = Matcher(4, mode="multilevel")
        algo.insert_edge(0, 1)
        assert algo.is_maximal()
        algo.insert_edge(1, 2)
        assert algo.is_maximal()
        algo.insert_edge(2, 3)
        assert algo.is_maximal()

        algo.delete_edge(0, 1)
        assert algo.is_maximal()
        algo.delete_edge(1, 2)
        assert algo.is_maximal()
        algo.delete_edge(2, 3)
        assert algo.is_maximal()

    def test_triangle_updates(self) -> None:
        algo = Matcher(3, mode="basic")
        algo.insert_edge(0, 1)
        algo.insert_edge(1, 2)
        algo.insert_edge(2, 0)
        assert algo.is_maximal()
        assert algo.matching_size() >= 1

        algo.delete_edge(0, 1)
        assert algo.is_maximal()

    def test_star_updates(self) -> None:
        algo = Matcher(5, mode="basic")
        for i in range(1, 5):
            algo.insert_edge(0, i)
        assert algo.is_maximal()
        assert algo.matching_size() == 1

        algo.delete_edge(0, 1)
        assert algo.is_maximal()

    def test_path_updates(self) -> None:
        algo = Matcher(5, mode="basic")
        for i in range(4):
            algo.insert_edge(i, i + 1)
        assert algo.is_maximal()

        for i in range(4):
            algo.delete_edge(i, i + 1)
        assert algo.is_maximal()

    def test_statistics(self) -> None:
        algo = Matcher(5, mode="basic")
        algo.insert_edge(0, 1)
        stats = algo.statistics()
        assert stats["n"] == 5
        assert stats["m"] == 1
        assert stats["matching_size"] == 1
        assert "total_updates" in stats

    def test_rebuild_triggered(self) -> None:
        algo = Matcher(2, mode="basic")
        algo.phase_length = 3
        algo.insert_edge(0, 1)
        assert algo.update_count == 1
        algo.insert_edge(0, 1)
        assert algo.update_count == 2
        algo.insert_edge(0, 1)
        assert algo.update_count == 0
        assert algo.is_maximal()

    def test_is_maximal_after_sequence(self) -> None:
        algo = Matcher(6, mode="basic")
        edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)]
        for u, v in edges:
            algo.insert_edge(u, v)
            assert algo.is_maximal()

        for u, v in edges:
            algo.delete_edge(u, v)
            assert algo.is_maximal()

    def test_invalid_mode(self) -> None:
        with pytest.raises(ValueError):
            Matcher(5, mode="fast")

    def test_negative_vertices(self) -> None:
        with pytest.raises(ValueError):
            Matcher(-1)

    def test_empty_graph_basic(self) -> None:
        algo = Matcher(0, mode="basic")
        assert algo.is_maximal()
        assert algo.matching_size() == 0

    def test_empty_graph_multilevel(self) -> None:
        algo = Matcher(0, mode="multilevel")
        assert algo.is_maximal()
        assert algo.matching_size() == 0

    def test_single_vertex_graph(self) -> None:
        algo = Matcher(1, mode="basic")
        algo.insert_edge(0, 0)
        assert algo.is_maximal()
        assert algo.matching_size() == 0

    def test_complete_graph_basic(self) -> None:
        n = 6
        algo = Matcher(n, mode="basic")
        for i in range(n):
            for j in range(i + 1, n):
                algo.insert_edge(i, j)
        assert algo.is_maximal()
        assert algo.matching_size() == n // 2

    def test_complete_graph_then_remove_all(self) -> None:
        n = 5
        algo = Matcher(n, mode="basic")
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
        for u, v in edges:
            algo.insert_edge(u, v)
        assert algo.is_maximal()
        for u, v in edges:
            algo.delete_edge(u, v)
        assert algo.is_maximal()
        assert algo.matching_size() == 0

    def test_bipartite_graph(self) -> None:
        n, m = 3, 4
        algo = Matcher(n + m, mode="basic")
        for i in range(n):
            for j in range(m):
                algo.insert_edge(i, n + j)
        assert algo.is_maximal()
        assert algo.matching_size() >= min(n, m)

    def test_repeated_insert_delete_same_edge(self) -> None:
        algo = Matcher(2, mode="basic")
        for _ in range(20):
            algo.insert_edge(0, 1)
            assert algo.is_maximal()
            algo.delete_edge(0, 1)
            assert algo.is_maximal()

    def test_random_stress_basic(self) -> None:
        n = 10
        rng = random.Random(42)
        algo = Matcher(n, mode="basic")
        edges: set[tuple[int, int]] = set()
        for _ in range(200):
            u = rng.randrange(n)
            v = rng.randrange(n)
            if u == v:
                continue
            e = (min(u, v), max(u, v))
            if e not in edges:
                edges.add(e)
                algo.insert_edge(e[0], e[1])
            else:
                edges.remove(e)
                algo.delete_edge(e[0], e[1])
            assert algo.is_maximal()

    def test_random_stress_multilevel(self) -> None:
        n = 10
        rng = random.Random(123)
        algo = Matcher(n, mode="multilevel")
        edges: set[tuple[int, int]] = set()
        for _ in range(200):
            u = rng.randrange(n)
            v = rng.randrange(n)
            if u == v:
                continue
            e = (min(u, v), max(u, v))
            if e not in edges:
                edges.add(e)
                algo.insert_edge(e[0], e[1])
            else:
                edges.remove(e)
                algo.delete_edge(e[0], e[1])
            assert algo.is_maximal()

    def test_alternating_insert_delete_path(self) -> None:
        algo = Matcher(4, mode="basic")
        for _ in range(10):
            algo.insert_edge(0, 1)
            assert algo.is_maximal()
            algo.insert_edge(1, 2)
            assert algo.is_maximal()
            algo.insert_edge(2, 3)
            assert algo.is_maximal()
            algo.delete_edge(0, 1)
            assert algo.is_maximal()
            algo.delete_edge(1, 2)
            assert algo.is_maximal()
            algo.delete_edge(2, 3)
            assert algo.is_maximal()

    def test_matching_is_subset_of_edges(self) -> None:
        algo = Matcher(5, mode="basic")
        algo.insert_edge(0, 1)
        algo.insert_edge(1, 2)
        algo.insert_edge(2, 3)
        matching = algo.get_matching()
        for e in matching:
            assert algo.graph.has_edge(e[0], e[1])

    def test_delete_nonexistent_edge(self) -> None:
        algo = Matcher(3, mode="basic")
        algo.delete_edge(0, 1)
        assert algo.is_maximal()

    def test_get_matching_returns_copy(self) -> None:
        algo = Matcher(2, mode="basic")
        algo.insert_edge(0, 1)
        m1 = algo.get_matching()
        m2 = algo.get_matching()
        assert m1 is not m2

    def test_accounting_counters(self) -> None:
        algo = Matcher(4, mode="basic")
        algo.insert_edge(0, 1)
        algo.insert_edge(1, 2)
        algo.delete_edge(0, 1)
        stats = algo.statistics()
        assert stats["total_updates"] == 3
        assert stats["total_insertions"] == 2
        assert stats["total_deletions"] == 1

    def test_partner_method(self) -> None:
        algo = Matcher(4, mode="basic")
        algo.insert_edge(0, 1)
        assert algo.partner(0) == 1
        assert algo.partner(1) == 0
        assert algo.partner(2) is None

    def test_phase_transition(self) -> None:
        algo = Matcher(4, mode="basic")
        algo.phase_length = 5
        for _i in range(5):
            algo.insert_edge(0, 1)
        assert algo.update_count == 0  # rebuild triggered
        assert algo.is_maximal()

    def test_rematch_after_deleting_matching_edge(self) -> None:
        algo = Matcher(4, mode="basic")
        algo.insert_edge(0, 1)
        algo.insert_edge(2, 3)
        assert algo.matching_size() == 2
        algo.delete_edge(0, 1)
        assert algo.is_maximal()
        # The remaining edge (2,3) should still be in the matching
        assert (2, 3) in algo.get_matching()

    def test_multilevel_levels_exist(self) -> None:
        algo = Matcher(50, mode="multilevel")
        assert algo.k >= 1
        assert algo.system is not None

    def test_rematch_u_no_phantom_edge_from_stale_list(self) -> None:
        """Regression: a stale lambda list must not produce a phantom edge."""
        from axiom.core import Matcher
        from axiom.types import canonical_edge

        algo = Matcher(4, mode="basic")
        algo.insert_edge(0, 1)
        algo.insert_edge(0, 2)
        algo.rebuild_basic()
        # Place vertex 0 in U and ensure it is unmatched in M_star.
        algo.system.U.add(0)
        algo.system.A.discard(0)
        algo.system.B.discard(0)
        for e in list(algo.matched_edges):
            if 0 in e:
                algo.matched_edges.discard(e)
                algo.matched_vertices.discard(e[0])
                algo.matched_vertices.discard(e[1])
        assert 0 not in algo.matched_vertices
        # Inject a stale lambda list that claims 3 is a neighbour of 0.
        algo.system.lambda_lists[0] = [1, 2, 3]
        # Ensure 1 and 2 are already matched so they are skipped.
        algo.matched_vertices.add(1)
        algo.matched_vertices.add(2)
        algo._Matcher__rematch_u(0)
        # Phantom edge (0,3) must not be added.
        assert canonical_edge(0, 3) not in algo.matched_edges

    def test_partition_m_color_range_error(self) -> None:
        """Regression: out-of-range colors from abb_edge_color must raise."""
        algo = Matcher(4, mode="basic")
        algo.insert_edge(0, 1)
        algo.insert_edge(1, 2)
        algo.rebuild_basic()
        # Monkey-patch abb_edge_color to return an invalid color.
        import axiom.dynamic_matching as dm

        original_color = dm.abb_edge_color

        def bad_color(graph, delta):
            return {(0, 1): 0, (1, 2): delta + 5}

        dm.abb_edge_color = bad_color
        try:
            with pytest.raises(RuntimeError):
                algo.partition_m_into_matchings()
        finally:
            dm.abb_edge_color = original_color


# ------------------------------------------------------------------
# Multi-level system
# ------------------------------------------------------------------


class TestMultiLevelSystem:
    """Tests for :class:`axiom.z_system.MultiLevelSystem`."""

    def test_empty(self) -> None:
        g = DynamicGraph(4)
        mls = MultiLevelSystem(graph=g, k=2)
        assert mls.k == 2
        assert not mls.levels

    def test_with_levels(self) -> None:
        g = DynamicGraph(4)
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        mls = MultiLevelSystem(graph=g, k=2)
        mls.levels = [
            ZSubgraphSystem(graph=g, z=2, A={0}, B={1}, U={2, 3}),
            ZSubgraphSystem(graph=g, z=1, A={0}, B={1}, U={2, 3}),
        ]
        assert len(mls.levels) == 2

    def test_level_1_invariant_I3_empty(self) -> None:
        g = DynamicGraph(0)
        mls = MultiLevelSystem(graph=g, k=1)
        with pytest.raises(NotImplementedError):
            mls.level_1_invariant_I3()

    def test_check_multi_level_i3_returns_false(self) -> None:
        from axiom.invariants import check_multi_level_i3

        g = DynamicGraph(0)
        mls = MultiLevelSystem(graph=g, k=1)
        assert check_multi_level_i3(mls) is False


# ------------------------------------------------------------------
# Simulation utilities
# ------------------------------------------------------------------


class TestSimulation:
    """Tests for :mod:`axiom.simulation`."""

    def test_random_update_sequence(self) -> None:
        rng = random.Random(7)
        updates = list(random_update_sequence(5, 20, rng))
        assert len(updates) == 20
        for op, u, v in updates:
            assert op in ("insert", "delete")
            assert 0 <= u < 5
            assert 0 <= v < 5

    def test_replay_updates(self) -> None:
        algo = Matcher(4, mode="basic")
        updates = [("insert", 0, 1), ("insert", 1, 2), ("delete", 0, 1)]
        replay_updates(algo, updates)
        assert algo.is_maximal()


# ------------------------------------------------------------------
# Performance sanity checks
# ------------------------------------------------------------------


class TestPerformance:
    """Lightweight performance sanity checks."""

    def test_large_graph_basic(self) -> None:
        n = 100
        algo = Matcher(n, mode="basic")
        for i in range(n - 1):
            algo.insert_edge(i, i + 1)
        assert algo.is_maximal()
        assert algo.matching_size() == n // 2

    def test_large_graph_multilevel(self) -> None:
        n = 100
        algo = Matcher(n, mode="multilevel")
        for i in range(n - 1):
            algo.insert_edge(i, i + 1)
        assert algo.is_maximal()
        assert algo.matching_size() == n // 2

    def test_dense_graph_basic(self) -> None:
        n = 20
        algo = Matcher(n, mode="basic")
        for i in range(n):
            for j in range(i + 1, n):
                algo.insert_edge(i, j)
        assert algo.is_maximal()
        assert algo.matching_size() == n // 2
