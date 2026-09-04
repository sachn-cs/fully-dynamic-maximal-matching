"""Minimal demo of the FDMM algorithm.

Usage::

    python scripts/demo.py [--n N] [--mode {basic,multilevel}]

Example::

    python scripts/demo.py --n 10 --mode basic
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time

_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_src = os.path.join(_repo_root, "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from axiom.matcher import MaximalMatcher  # noqa: E402
from axiom.simulation import random_update_sequence  # noqa: E402


def run_demo(n: int, mode: str, num_updates: int, seed: int = 42) -> int:
    """Run a demo sequence of random insertions and deletions.

    Args:
        n: Number of vertices.
        mode: ``"basic"`` or ``"multilevel"``.
        num_updates: Total number of update operations.
        seed: Random seed for reproducibility.

    Returns:
        0 on success, 1 on failure.
    """
    print(f"=== FDMM Demo: n={n}, mode={mode}, updates={num_updates} ===\n")

    algo = MaximalMatcher(n, mode=mode)
    rng = random.Random(seed)
    updates = list(random_update_sequence(n, num_updates, rng))

    start = time.perf_counter()
    for op, u, v in updates:
        if op == "insert":
            algo.insert_edge(u, v)
        else:
            algo.delete_edge(u, v)

        if not algo.is_maximal():
            print(f"ERROR: Matching is not maximal at step {op} ({u},{v})!")
            return 1

    elapsed = time.perf_counter() - start
    stats = algo.statistics()

    print(f"Completed {num_updates} updates in {elapsed:.3f}s")
    print(f"Final graph edges: {stats['m']}")
    print(f"Matching size: {stats['matching_size']}")
    print(f"Rebuilds triggered: {stats.get('phase_rebuilds', 0)}")
    print(f"Maximal: {algo.is_maximal()}")
    print("\nDemo finished successfully.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="FDMM Demo")
    parser.add_argument("--n", type=int, default=20, help="Number of vertices")
    parser.add_argument(
        "--mode",
        choices=["basic", "multilevel"],
        default="basic",
        help="Algorithm mode",
    )
    parser.add_argument(
        "--updates", type=int, default=200, help="Number of update operations"
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    return run_demo(args.n, args.mode, args.updates, args.seed)


if __name__ == "__main__":
    sys.exit(main())
