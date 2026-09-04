"""Multiprocessing support for parallel update processing.

This module provides utilities for running multiple
:class:`MaximalMatcher` instances in parallel, useful for
benchmarking and comparing the basic and multilevel modes.

**Engineering utility** -- not part of the paper's baseline algorithm.

Process / thread safety:
    * Each worker process builds and tears down its own
      :class:`MaximalMatcher` instance; nothing is shared
      across processes.
    * The ``multiprocessing.Pool`` used by :func:`run_parallel_benchmarks`
      forks its workers, so the algorithm must be safe to import
      without side effects.  This is ensured by the lack of mutable
      module-level state.
"""

from __future__ import annotations

import multiprocessing
from dataclasses import dataclass
from typing import TYPE_CHECKING

from axiom.simulation import random_update_sequence

if TYPE_CHECKING:
    pass


@dataclass
class BenchmarkResult:
    """Result from a single benchmark run.

    Attributes:
        n: Number of vertices.
        mode: Algorithm mode (``"basic"`` or ``"multilevel"``).
        updates: Number of update operations replayed.
        elapsed_sec: Wall-clock time elapsed in seconds.
        updates_per_sec: ``updates / elapsed_sec`` (``inf`` when no
            time elapsed, e.g. on empty input).
        matching_size: :math:`|M^*|` after the run.
        is_maximal: ``True`` iff ``is_maximal()`` returned ``True``.
        phase_rebuilds: Count of full phase rebuilds triggered.
        subphase_rebuilds: Count of subphase augmentations triggered.
    """

    n: int
    mode: str
    updates: int
    elapsed_sec: float
    updates_per_sec: float
    matching_size: int
    is_maximal: bool
    phase_rebuilds: int
    subphase_rebuilds: int


def run_benchmark_worker(
    n: int,
    mode: str,
    updates: int,
    seed: int,
) -> BenchmarkResult:
    """Worker function for parallel benchmark execution.

    Built and discarded inside one worker process; no shared state.
    """
    import time

    from axiom.matcher import MaximalMatcher

    algo = MaximalMatcher(n, mode=mode)
    rng = __import__("random").Random(seed)
    seq = list(random_update_sequence(n, updates, rng))

    start = time.perf_counter()
    for op, u, v in seq:
        if op == "insert":
            algo.insert_edge(u, v)
        else:
            algo.delete_edge(u, v)
    elapsed = time.perf_counter() - start

    stats = algo.statistics()
    return BenchmarkResult(
        n=n,
        mode=mode,
        updates=updates,
        elapsed_sec=elapsed,
        updates_per_sec=updates / elapsed if elapsed > 0 else float("inf"),
        matching_size=stats["matching_size"],
        is_maximal=algo.is_maximal(),
        phase_rebuilds=stats.get("phase_rebuilds", 0),
        subphase_rebuilds=stats.get("subphase_rebuilds", 0),
    )


def run_parallel_benchmarks(
    configs: list[tuple[int, str, int, int]],
    max_workers: int | None = None,
) -> list[BenchmarkResult]:
    """Run multiple benchmarks in parallel.

    Each entry of ``configs`` describes one benchmark as a tuple
    ``(n, mode, updates, seed)``.  The workers run on independent
    processes so the GIL does not interfere.

    Args:
        configs: List of ``(n, mode, updates, seed)`` tuples.
        max_workers: Maximum number of parallel workers; ``None``
            (the default) leaves the choice to :mod:`multiprocessing`,
            which defaults to the number of CPU cores.

    Returns:
        List of :class:`BenchmarkResult` objects in the same order as
        ``configs``.

    Example:
        >>> configs = [
        ...     (100, "basic", 1000, 42),
        ...     (100, "multilevel", 1000, 42),
        ...     (200, "basic", 1000, 42),
        ... ]
        >>> results = run_parallel_benchmarks(configs)
        >>> for r in results:
        ...     print(f"{r.mode}: {r.updates_per_sec:.0f} ops/sec")
    """
    with multiprocessing.Pool(processes=max_workers) as pool:
        results = pool.starmap(
            run_benchmark_worker,
            configs,
        )
    return list(results)


def compare_modes(
    n: int,
    updates: int,
    seed: int = 42,
    max_workers: int | None = None,
) -> dict[str, BenchmarkResult]:
    """Compare basic and multilevel modes on the same graph size.

    Runs the same update sequence (seeded identically) against both
    modes and returns the per-mode results keyed by mode name.  This is
    the typical one-shot entry point used by the README's "Comparing
    modes" snippet.

    Args:
        n: Number of vertices.
        updates: Number of update operations.
        seed: Random seed for reproducibility.
        max_workers: Maximum parallel workers.

    Returns:
        Dict mapping mode name (``"basic"`` / ``"multilevel"``) to
        :class:`BenchmarkResult`.
    """
    configs = [
        (n, "basic", updates, seed),
        (n, "multilevel", updates, seed),
    ]
    results = run_parallel_benchmarks(configs, max_workers)
    return {r.mode: r for r in results}
