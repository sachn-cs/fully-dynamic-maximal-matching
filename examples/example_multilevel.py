"""Minimal example: multilevel mode on a random graph."""

from __future__ import annotations

import sys
import os

_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_src = os.path.join(_repo_root, "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from axiom import DynamicMaximalMatching
from axiom.simulation import random_update_sequence
import random


def main() -> None:
    n = 20
    algo = DynamicMaximalMatching(n, mode="multilevel")
    rng = random.Random(7)
    updates = list(random_update_sequence(n, 100, rng))
    for op, u, v in updates:
        if op == "insert":
            algo.insert_edge(u, v)
        else:
            algo.delete_edge(u, v)
        assert algo.is_maximal()

    print("Matching size:", algo.matching_size())
    print("Stats:", algo.statistics())


if __name__ == "__main__":
    main()
