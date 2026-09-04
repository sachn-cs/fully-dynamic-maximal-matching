"""Minimal example: basic mode on a path graph."""

from __future__ import annotations

import sys
import os

_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_src = os.path.join(_repo_root, "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from axiom import DynamicMaximalMatching


def main() -> None:
    n = 10
    algo = DynamicMaximalMatching(n, mode="basic")

    # Build a path
    for i in range(n - 1):
        algo.insert(i, i + 1)

    print("Matching size:", algo.size())
    print("Is maximal:", algo.maximal())
    print("Stats:", algo.stats())


if __name__ == "__main__":
    main()
