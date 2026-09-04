"""maxmatch: A Faster Deterministic Algorithm for Fully Dynamic Maximal Matching.

This package is a pure-Python reproduction of the deterministic fully
dynamic maximal matching algorithm of Chuzhoy, Khanna, and Song
(arXiv:2605.00797v1, STOC 2026).

Two operating modes are exposed through :class:`MaximalMatcher`:

* ``"basic"`` -- :math:`\\tilde O(n^{2/3})` amortised update time via a
  single-level :math:`z`-subgraph system.
* ``"multilevel"`` -- :math:`n^{1/2+o(1)}` amortised update time via a
  recursive :math:`k`-level system with :math:`k = \\Theta(\\log n)`.

The supporting modules provide:

* :class:`DynamicGraph` -- a thin adjacency-set wrapper that stands in
  for the paper's BST-based adjacency layer.
* :class:`ZSubgraphSystem` and :class:`MultiLevelSystem` -- the
  combinatorial state used by both modes.
* The :math:`z`-system construction primitives
  :func:`build_z_system`, :func:`build_multi_level_system`,
  :func:`edge_switch_inside_B`, and :func:`promote_u_vertex`.
* The edge colouring utilities :class:`GreedyColorer`,
  :class:`VizingColorer`, :func:`recolor_for_edge`,
  :func:`find_edge_of_color`, :func:`color_single_edge`,
  :func:`alternating_path`, and :func:`flip_path`.
* :func:`check_maximal_matching` and :func:`check_z_system_invariants`
  -- standalone invariant validators used by the test suite.
* :class:`UpdateAccountant` and the :mod:`maxmatch.simulation` /
  :mod:`maxmatch.parallel` modules -- engineering utilities for empirical
  benchmarking and reproducibility.

Reference:
    Chuzhoy, J., Khanna, S., Song, J. (2026).  *A Faster Deterministic
    Algorithm for Fully Dynamic Maximal Matching*.  arXiv:2605.00797v1.
"""

from maxmatch.accounting import UpdateAccountant
from maxmatch.coloring import (
    GreedyColorer,
    VizingColorer,
    alternating_path,
    backtrack_color,
    color_single_edge,
    find_edge_of_color,
    flip_path,
    missing_colors,
    recolor_for_edge,
)
from maxmatch.graph import DynamicGraph
from maxmatch.invariants import check_maximal_matching, check_z_system_invariants
from maxmatch.matcher import MaximalMatcher
from maxmatch.matching import build_partner_map, greedy_maximal_matching, partner_of
from maxmatch.parallel import compare_modes, run_parallel_benchmarks
from maxmatch.simulation import random_update_sequence, replay_updates
from maxmatch.types import Edge, EdgeColorer, Graph, Matching, Vertex, canonical_edge
from maxmatch.visualize import (
    visualize_graph_adjacency,
    visualize_matching,
    visualize_system,
)
from maxmatch.z_system import (
    MultiLevelSystem,
    ZSubgraphSystem,
    build_multi_level_system,
    build_z_system,
    edge_switch_inside_B,
    promote_u_vertex,
)

__version__ = "0.5.0"

__all__ = [
    "MaximalMatcher",
    "DynamicGraph",
    "GreedyColorer",
    "VizingColorer",
    "ZSubgraphSystem",
    "MultiLevelSystem",
    "Edge",
    "Matching",
    "Vertex",
    "Graph",
    "EdgeColorer",
    "canonical_edge",
    "greedy_maximal_matching",
    "partner_of",
    "build_partner_map",
    "check_maximal_matching",
    "check_z_system_invariants",
    "UpdateAccountant",
    "random_update_sequence",
    "replay_updates",
    "visualize_system",
    "visualize_matching",
    "visualize_graph_adjacency",
    "run_parallel_benchmarks",
    "compare_modes",
    "backtrack_color",
    "missing_colors",
    "alternating_path",
    "flip_path",
    "color_single_edge",
    "recolor_for_edge",
    "find_edge_of_color",
    "build_z_system",
    "build_multi_level_system",
    "edge_switch_inside_B",
    "promote_u_vertex",
]
