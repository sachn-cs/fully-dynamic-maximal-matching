"""Command-line interface for the FDMM reproduction.

A thin wrapper around :class:`MaximalMatcher` plus the
:func:`random_update_sequence` generator.  It is useful as a smoke
test: it runs a fixed number of random updates, asserts maximality
after each one, and prints timing statistics on exit.

This is an engineering utility, not part of the paper's baseline
algorithm.

Example::

    $ axiom --n 50 --mode basic --updates 1000 --seed 7
    Completed 1000 updates in 0.08s
    Final edges: 463
    Matching size: 25
    Maximal: True
"""

from __future__ import annotations

import argparse
import random
import sys
import time

from axiom.matcher import MaximalMatcher
from axiom.simulation import random_update_sequence


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``axiom`` console script.

    Args:
        argv: Optional list of arguments.  When ``None`` (the default)
            :mod:`argparse` reads from ``sys.argv``.

    Returns:
        Process exit code: ``0`` on success, ``1`` if maximality was
        violated at any step.
    """
    parser = argparse.ArgumentParser(
        description="Fully Dynamic Maximal Matching (FDMM) demo"
    )
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
    args = parser.parse_args(argv)

    algo = MaximalMatcher(args.n, mode=args.mode)
    rng = random.Random(args.seed)
    updates = list(random_update_sequence(args.n, args.updates, rng))

    start = time.perf_counter()
    for op, u, v in updates:
        if op == "insert":
            algo.insert_edge(u, v)
        else:
            algo.delete_edge(u, v)
        if not algo.is_maximal():
            # Maximality is the basic correctness invariant of the
            # algorithm; if it ever fails the reproduction has a bug.
            print(f"ERROR: Matching not maximal after {op} ({u},{v})")
            return 1
    elapsed = time.perf_counter() - start

    stats = algo.statistics()
    print(f"Completed {args.updates} updates in {elapsed:.3f}s")
    print(f"Final edges: {stats['m']}")
    print(f"Matching size: {stats['matching_size']}")
    print(f"Maximal: {algo.is_maximal()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
