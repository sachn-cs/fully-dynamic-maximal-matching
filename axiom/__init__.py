"""axiom: A Faster Deterministic Algorithm for Fully Dynamic Maximal Matching.

This package is a pure-Python reproduction of the deterministic fully
dynamic maximal matching algorithm of Chuzhoy, Khanna, and Song
(arXiv:2605.00797v1, STOC 2026).

Two operating modes are exposed through :class:`Matcher`:

* ``"basic"`` -- :math:`\\tilde O(n^{2/3})` amortised update time via a
  single-level :math:`z`-subgraph system.
* ``"multilevel"`` -- :math:`n^{1/2+o(1)}` amortised update time via a
  recursive :math:`k`-level system with :math:`k = \\Theta(\\log n)`.

The supporting modules provide:

* :class:`Adjacency` -- a thin adjacency-set wrapper that stands in
  for the paper's BST-based adjacency layer.
* :class:`System` and :class:`Hierarchy` -- the
  combinatorial state used by both modes.
* The :math:`z`-system construction primitives
  :func:`build`, :func:`build_hierarchy`,
  :func:`switch`, and :func:`promote`.
* The edge colouring utilities :class:`Greedy`,
  :class:`Vizing`, :func:`recolor`,
  :func:`find`, :func:`color_one`,
  :func:`alternating`, and :func:`flip`.
* :func:`check_maximal_matching` and :func:`valid`
  -- standalone invariant validators used by the test suite.
* :class:`Ledger` and the :mod:`axiom.simulation` /
  :mod:`axiom.parallel` modules -- engineering utilities for empirical
  benchmarking and reproducibility.

Reference:
    Chuzhoy, J., Khanna, S., Song, J. (2026).  *A Faster Deterministic
    Algorithm for Fully Dynamic Maximal Matching*.  arXiv:2605.00797v1.
"""

from axiom.ledger import Ledger
from axiom.color import (
    Greedy,
    Vizing,
    alternating,
    backtrack,
    color_one,
    find,
    flip,
    missing,
    recolor,
)
from axiom.graph import Adjacency
from axiom.invariant import check_maximal_matching, valid
from axiom.core import Matcher
from axiom.matching import partners, greedy, partner_in
from axiom.parallel import compare_modes, run_parallel_benchmarks
from axiom.simulation import random_update_sequence, replay_updates
from axiom.types import Edge, Colorer, Graph, Matching, Vertex, canonical
from axiom.visualize import (
    visualize_graph_adjacency,
    visualize_matching,
    visualize_system,
)
from axiom.hierarchy import Hierarchy, build_hierarchy
from axiom.system import (
    System,
    build,
    switch,
    promote,
)

__version__ = "0.5.0"

__all__ = [
    "Matcher",
    "Adjacency",
    "Greedy",
    "Vizing",
    "System",
    "Hierarchy",
    "Edge",
    "Matching",
    "Vertex",
    "Graph",
    "Colorer",
    "canonical",
    "greedy",
    "partner_in",
    "partners",
    "check_maximal_matching",
    "valid",
    "Ledger",
    "random_update_sequence",
    "replay_updates",
    "visualize_system",
    "visualize_matching",
    "visualize_graph_adjacency",
    "run_parallel_benchmarks",
    "compare_modes",
    "backtrack",
    "missing",
    "alternating",
    "flip",
    "color_one",
    "recolor",
    "find",
    "build",
    "build_hierarchy",
    "switch",
    "promote",
]
