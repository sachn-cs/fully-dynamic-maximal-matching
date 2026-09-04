# FDMM Documentation

## Overview

FDMM is a Python reproduction of *"A Faster Deterministic Algorithm for
Fully Dynamic Maximal Matching"* (arXiv:2605.00797v1).

Repository: `https://github.com/sachncs/fully-dynamic-maximal-matching`

## Modules

- `fdmm.graph` — Dynamic undirected graph data structure.
- `fdmm.matching` — Greedy maximal matching and partner helpers.
- `fdmm.edge_coloring` — Deterministic edge colouring
  (:func:`abb_edge_color`, :func:`vizing_edge_color`, and the
  alternating-path primitives :func:`recolour_for_edge`,
  :func:`find_edge_of_color`, :func:`alternating_path`, :func:`flip_path`,
  :func:`color_single_edge`).
- `fdmm.z_system` — The :math:`z`-subgraph system, multi-level system,
  and the construction routines :func:`build_z_system`,
  :func:`build_multi_level_system`, :func:`edge_switch_inside_B`,
  :func:`promote_u_vertex`.
- `fdmm.dynamic_matching` — Core fully-dynamic maximal matching
  algorithm; exposes :meth:`DynamicMaximalMatching.augment_m1_at_subphase_boundary`,
  :meth:`DynamicMaximalMatching.try_augment_m1`, and
  :meth:`DynamicMaximalMatching.flip_augmenting_path` for advanced
  callers that need to drive :math:`M_1` augmentation directly.
- `fdmm.updates` — Insertion, deletion, and rematch handlers
  (`rematch_u`, `rematch_b`, `rematch_a`).
- `fdmm.invariants` — Standalone invariant checkers.
- `fdmm.accounting` — Explicit update-work counters.
- `fdmm.simulation` — Random update generators and replay utilities.
- `fdmm.parallel` — Multiprocessing benchmark driver
  (:func:`run_parallel_benchmarks`, :func:`compare_modes`,
  :func:`run_benchmark_worker`).
- `fdmm.visualise` — ASCII rendering of the :math:`z`-subgraph system
  and matching state.
- `maxmatch.cli` — Command-line entry point.

## Quick Start

```python
from maxmatch import DynamicMaximalMatching

algo = DynamicMaximalMatching(n=100, mode="basic")
algo.insert_edge(0, 1)
algo.insert_edge(2, 3)
assert algo.is_maximal()
print(algo.matching_size())
```

## API Reference

See inline docstrings for full API documentation.  Key public classes:

* :class:`fdmm.graph.DynamicGraph`
* :class:`fdmm.z_system.ZSubgraphSystem`
* :class:`fdmm.z_system.MultiLevelSystem`
* :class:`fdmm.dynamic_matching.DynamicMaximalMatching`
* :class:`fdmm.accounting.UpdateAccountant`

The package-level ``__all__`` exports the public surface in full:
``DynamicMaximalMatching``, ``DynamicGraph``, ``ZSubgraphSystem``,
``MultiLevelSystem``, the type aliases (``Edge``, ``Matching``,
``Vertex``, ``canonical_edge``), all matching / invariant helpers,
every :math:`z`-system and edge-colouring primitive listed above, and
the simulation / parallel / visualise / cli entry points.

## Additional Documents

- `docs/getting-started.md` — step-by-step getting started guide.
- `docs/architecture.md` — internal architecture with ASCII diagrams.
- `docs/faq.md` — frequently asked questions.
- `docs/paper_restatement.md` — Extracted paper content, notation, and UNKNOWNs.
- `docs/audit_report.md` — Section-by-section audit of code vs. paper.
