"""Lightweight benchmark for FDMM update throughput.

This is an engineering utility, not part of the paper's baseline algorithm.
Run with::

    python benchmarks/bench_fdmm.py --n 200 --updates 5000 --mode basic
"""

from __future__ import annotations

import argparse
import random
import sys
import time

_repo_root = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))
_src = __import__("os").path.join(_repo_root, "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from axiom.core import Matcher
from axiom.simulation import random_update_sequence


def bench(n: int, mode: str, updates: int, seed: int) -> dict[str, float]:
    algo = Matcher(n, mode=mode)
    rng = random.Random(seed)
    seq = list(random_update_sequence(n, updates, rng))

    start = time.perf_counter()
    for op, u, v in seq:
        if op == "insert":
            algo.insert(u, v)
        else:
            algo.delete(u, v)
    elapsed = time.perf_counter() - start

    assert algo.maximal(), "matching is not maximal after benchmark sequence"
    stats = algo.stats()
    return {
        "n": float(n),
        "mode": mode,
        "updates": float(updates),
        "elapsed_sec": elapsed,
        "updates_per_sec": updates / elapsed if elapsed > 0 else float("inf"),
        "matching_size": float(stats["matching_size"]),
        "phase_rebuilds": float(stats.get("phase_rebuilds", 0)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="FDMM benchmark")
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--mode", choices=["basic", "multilevel"], default="basic")
    parser.add_argument("--updates", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    result = bench(args.n, args.mode, args.updates, args.seed)
    for k, v in result.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
