<p align="center">
  <h1 align="center">fdmm</h1>
  <p align="center">A Faster Deterministic Algorithm for Fully Dynamic Maximal Matching — Python reproduction of arXiv:2605.00797v1.</p>
  <p align="center">
    <a href="#installation"><img src="https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue" alt="Python"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
    <a href="https://github.com/sachncs/fully-dynamic-maximal-matching/actions"><img src="https://img.shields.io/github/actions/workflow/status/sachncs/fully-dynamic-maximal-matching/ci.yml?branch=master" alt="CI"></a>
    <a href="https://github.com/sachncs/fully-dynamic-maximal-matching"><img src="https://img.shields.io/badge/arXiv-2605.00797v1-b31b1b" alt="arXiv"></a>
    <a href="https://mypy-lang.org/"><img src="https://img.shields.io/badge/mypy-strict-green.svg" alt="Checked with mypy"></a>
    <a href="https://github.com/sachncs/fully-dynamic-maximal-matching/stargazers"><img src="https://img.shields.io/github/stars/sachncs/fully-dynamic-maximal-matching" alt="Stars"></a>
  </p>
</p>

**fdmm** is a Python reproduction of *A Faster Deterministic Algorithm for Fully
Dynamic Maximal Matching* by Chuzhoy, Khanna, and Song (STOC 2026,
arXiv:2605.00797v1). It maintains a **maximal matching** in an undirected
graph under online edge insertions and deletions in amortised
*Õ(n<sup>1/2+o(1)</sup>)* update time.

---

## Features

- **Two operating modes** — `basic` for the single-level *Õ(n<sup>2/3</sup>)*
  algorithm and `multilevel` for the *n<sup>1/2+o(1)</sup>* k-level recursive
  version with `k = Θ(log n)`.
- **z-subgraph system** — full implementation of the (A, B, U) partition,
  the `S = A ∪ B` saturation, the `Λ(u)` and `L(a)` index lists, and the six
  invariants from Section 2 of the paper.
- **Deterministic edge colouring** — Vizing's classical alternating-path
  recolouring for `(Δ+1)`-colourings, plus the faster degree-ordered greedy
  (`abb_edge_color`) used to partition `M` into colour classes.
- **Comprehensive invariant checks** — independent checkers for maximality
  and every z-system property, callable from tests or debugging scripts.
- **Empirical accounting** — explicit counters (`UpdateAccountant`) for the
  number of rebuilds, rematch scan sizes, stale cleanups, and greedy
  fallbacks. Useful for diagnosing where time is spent; not a proof of the
  amortised bound.
- **Reproducible simulation** — seeded random update sequences with replay
  utilities for stress tests and benchmarks.
- **Zero runtime dependencies** — pure Python with the standard library; only
  the optional `.[dev]` extras (`pytest`, `mypy`, `ruff`, `hypothesis`) are
  pulled in for development.
- **Strict type checking** — every public signature is annotated; the
  repository enables `mypy --strict`.

---

## Installation

### From source

```bash
git clone https://github.com/sachncs/fully-dynamic-maximal-matching.git
cd fully-dynamic-maximal-matching
pip install -e .
```

### With dev dependencies

```bash
pip install -e ".[dev]"
```

### In an isolated environment

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
pip install -e ".[dev]"
```

**Requirements**: Python >= 3.10

---

## Quick Start

### Python API

```python
from maxmatch import DynamicMaximalMatching

# Initialise on 100 vertices in basic mode
algo = DynamicMaximalMatching(n=100, mode="basic")

# Insert edges
algo.insert_edge(0, 1)
algo.insert_edge(2, 3)

# Delete edges
algo.delete_edge(0, 1)

# Query
assert algo.is_maximal()
print("Matching size:", algo.matching_size())
print("Stats:", algo.statistics())
```

### Command-Line Interface

Run the built-in demo:

```bash
fdmm --n 20 --mode basic --updates 200
fdmm --n 50 --mode multilevel --updates 500
```

Or call the demo script directly:

```bash
python scripts/demo.py --n 20 --mode basic --updates 200
```

### Replay a Prepared Sequence

```python
from maxmatch import DynamicMaximalMatching
from maxmatch.simulation import random_update_sequence, replay_updates
import random

algo = DynamicMaximalMatching(50, mode="basic")
rng = random.Random(42)
updates = list(random_update_sequence(50, 200, rng))
replay_updates(algo, updates)
assert algo.is_maximal()
print(algo.statistics())
```

---

## Configuration

### Update-Counter Reference

`algo.statistics()` returns every counter from `UpdateAccountant`:

| Counter             | Description                                                |
|---------------------|------------------------------------------------------------|
| `total_updates`     | Total insert + delete operations                           |
| `total_insertions`  | Insertions only                                            |
| `total_deletions`   | Deletions only (including no-op deletes of absent edges)   |
| `phase_rebuilds`    | Times the z-system was rebuilt from scratch                |
| `subphase_rebuilds` | Times `M_1` was augmented at a subphase boundary          |
| `rematch_u_scans`   | Cumulative vertex count scanned during U-rematching        |
| `rematch_b_scans`   | Same, for B-rematching                                     |
| `rematch_a_scans`   | Same, for A-rematching                                     |
| `greedy_rebuilds`   | Fallbacks to full greedy reconstruction of `M*`            |
| `stale_cleanups`    | Edges removed from `M*` because they had been deleted      |

> These counters are empirical bookkeeping, **not** a proof of the amortised
> bound. See `docs/audit_report.md` for a per-component fidelity table.

### Mode Schedule

| Mode         | `z`                  | `phase_length`        | Amortised bound          |
|--------------|----------------------|-----------------------|--------------------------|
| `basic`      | `⌈n^(2/3)⌉`          | `⌈n^(4/3)⌉`           | `Õ(n^(2/3))`             |
| `multilevel` | `n, n/2, …, √n`      | `⌈n^(4/3)⌉`           | `n^(1/2+o(1))`           |

---

## API Reference

### `DynamicMaximalMatching(n, mode="basic")`

| Method | Description |
|--------|-------------|
| `insert_edge(u, v)` | Insert an undirected edge and repair the matching |
| `delete_edge(u, v)` | Delete an undirected edge and repair the matching |
| `get_matching()` | Return a copy of the current maximal matching |
| `is_maximal()` | Verify that the current matching is maximal |
| `matching_size()` | Number of edges in the matching |
| `partner(v)` | Return the partner of vertex `v` in the matching, or `None` |
| `statistics()` | Runtime statistics (n, m, matching size, update counters, etc.) |
| `augment_m1_at_subphase_boundary()` | Augment `M_1` at the next subphase boundary |
| `try_augment_m1(start, matched_in_m1)` | BFS for an `M_1` augmenting path starting at `start` |
| `flip_augmenting_path(path)` | Flip edges along an augmenting path |

### Construction Primitives (`fdmm.z_system`)

| Function | Description |
|----------|-------------|
| `build_z_system(graph, z)` | Build a fresh `ZSubgraphSystem` from a graph |
| `build_multi_level_system(graph, level_zs)` | Stack z-systems for the recursive algorithm |
| `edge_switch_inside_B(...)` | Alternating-path capacity recovery inside `B` |
| `promote_u_vertex(...)` | Try to promote a `U`-vertex into `B` |

### Edge Colouring (`fdmm.edge_coloring`)

| Function | Description |
|----------|-------------|
| `abb_edge_color(graph, delta)` | Degree-ordered greedy `(Δ+1)`-colouring |
| `vizing_edge_color(graph, delta)` | Classical Vizing recolouring with backtracking fallback |
| `color_single_edge`, `alternating_path`, `flip_path` | Building-block primitives |

### Invariants and Accounting

| Function / Class | Description |
|------------------|-------------|
| `check_maximal_matching(graph, matching)` | Brute-force maximality verifier |
| `check_z_system_invariants(system)` | Verifies every z-system property |
| `check_multi_level_i3(multi)` | I3 check (returns False when constant is unknown) |
| `UpdateAccountant` | Counters for empirical cost auditing |
| `random_update_sequence`, `replay_updates` | Reproducible trace generation |
| `run_parallel_benchmarks`, `compare_modes` | Multiprocessing benchmark drivers |
| `visualise_system`, `visualise_matching` | ASCII renderers for debugging |

---

## Project Structure

```
fdmm/
├── pyproject.toml          # Build & tool config
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── .github/                # CI, issue & PR templates, dependabot
├── src/
│   └── fdmm/               # SDK package
│       ├── __init__.py     # Public API exports
│       ├── types.py        # Vertex, Edge, Matching, canonical_edge
│       ├── graph.py        # DynamicGraph
│       ├── matching.py     # Greedy matcher and partner helpers
│       ├── edge_coloring.py# abb_edge_color / vizing_edge_color
│       ├── z_system.py     # ZSubgraphSystem, MultiLevelSystem, builders
│       ├── dynamic_matching.py  # DynamicMaximalMatching
│       ├── updates.py      # Insertion / deletion / rematch handlers
│       ├── invariants.py   # Standalone invariant checkers
│       ├── accounting.py   # UpdateAccountant
│       ├── simulation.py   # Random update generators
│       ├── parallel.py     # Multiprocessing benchmark driver
│       ├── visualise.py    # ASCII renderers
│       └── cli.py          # Console-script entry point
├── tests/
│   └── test_fdmm.py
├── benchmarks/
│   └── bench_fdmm.py
├── scripts/
│   └── demo.py
├── examples/
│   ├── example_basic.py
│   └── example_multilevel.py
└── docs/
    ├── index.md
    ├── getting-started.md
    ├── architecture.md
    ├── faq.md
    ├── paper_restatement.md
    └── audit_report.md
```

---

## Testing

```bash
pytest                          # run the full suite
pytest -k invariants            # invariant checkers only
pytest --cov=fdmm tests/        # coverage report
```

---

## Build

```bash
python -m build                 # sdist + wheel
```

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Type check
mypy src/

# All checks
pytest && ruff check src/ tests/ && mypy src/
```

### Code Style

- Line length: 88
- Quotes: double (`"`)
- Formatting: ruff (auto-format with `ruff format`)
- Type hints: required on every public signature
- Docstrings: Google-style, covering parameters, returns, raised exceptions,
  side effects, and complexity
- No semi-private naming (`_foo`) on public helpers — all identifiers are
  public; use `_`-prefix only for genuinely internal scratch state.

### Commit Conventions

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add ABB+26 deterministic edge colouring
fix: handle edge case in stale-edge cleanup
docs: add API reference for previously private helpers
refactor: convert semi-private helpers to public API
test: add parity tests for cached vs streamed memory
chore: update ruff config
```

---

## Release

Versions follow [Semantic Versioning](https://semver.org/). Releases are tagged
via `version:X.Y.Z` commits in [CHANGELOG.md](CHANGELOG.md) and published to
PyPI via the CI workflow.

---

## Tech Stack

| Category      | Technology                                    |
|---------------|-----------------------------------------------|
| Language      | Python 3.10+                                  |
| Build         | setuptools (pyproject.toml)                   |
| Lint / Format | [ruff](https://docs.astral.sh/ruff/)          |
| Type Check    | [mypy](https://mypy-lang.org/) (strict)       |
| Testing       | [pytest](https://docs.pytest.org/), pytest-cov, hypothesis |
| CI            | GitHub Actions                                |

---

## Roadmap

See [CHANGELOG.md](CHANGELOG.md) for the full release history and pending
items.

- **v0.4.x** — Current: basic and multilevel modes, comprehensive test
  suite, simulation utilities, visualisation, parallel benchmarking.
- **v0.5.0** — Subphase-aware M₁ augmentation, exact phase constants.
- **v1.0.0** — ABB+26 deterministic edge colouring, incremental M*
  maintenance, PyPI release.

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Development setup
- Pull request process
- Coding standards
- Test expectations

## Code of Conduct

This project follows the [Contributor Covenant v2.1](CODE_OF_CONDUCT.md).
By participating you agree to abide by its terms.

## Security

Report vulnerabilities to **sachncs@gmail.com** — see [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) © 2026 Sachin

---

*Based on "A Faster Deterministic Algorithm for Fully Dynamic Maximal Matching" by Julia Chuzhoy, Sanjeev Khanna, and Junkai Song (arXiv:2605.00797v1).*
