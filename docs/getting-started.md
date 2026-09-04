# Getting Started

This guide walks you through installing and running FDMM for the first time.

## Prerequisites

- **Python 3.10** or later
- **pip** (included with Python)
- **Git**

## Installation

### Option 1: Install from Source (Recommended)

```bash
git clone https://github.com/sachncs/fully-dynamic-maximal-matching.git
cd fully-dynamic-maximal-matching
pip install -e ".[dev]"
```

### Option 2: Virtual Environment (Recommended for Development)

```bash
git clone https://github.com/sachncs/fully-dynamic-maximal-matching.git
cd fully-dynamic-maximal-matching
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\activate    # Windows
pip install -e ".[dev]"
```

## Verify Installation

```bash
pytest tests/ -v
```

All tests should pass. If any fail, check your Python version and ensure all dependencies are installed.

## First Steps

### Basic Mode

```python
from maxmatch import DynamicMaximalMatching

# Create an algorithm instance with 50 vertices
algo = DynamicMaximalMatching(n=50, mode="basic")

# Insert some edges
algo.insert_edge(0, 1)
algo.insert_edge(2, 3)
algo.insert_edge(4, 5)

# Check the matching
print("Matching size:", algo.matching_size())
print("Is maximal:", algo.is_maximal())

# Delete an edge
algo.delete_edge(0, 1)
print("After deletion:", algo.is_maximal())
```

### Multi-Level Mode

```python
from maxmatch import DynamicMaximalMatching

algo = DynamicMaximalMatching(n=50, mode="multilevel")

algo.insert_edge(0, 1)
algo.insert_edge(1, 2)
algo.insert_edge(2, 3)

print("Matching size:", algo.matching_size())
print("Statistics:", algo.statistics())
```

### Simulation

```python
from maxmatch import DynamicMaximalMatching
from maxmatch.simulation import random_update_sequence, replay_updates
import random

algo = DynamicMaximalMatching(50, mode="basic")
rng = random.Random(42)

# Generate 200 random updates
updates = list(random_update_sequence(50, 200, rng))
replay_updates(algo, updates)

assert algo.is_maximal()
print("Final statistics:", algo.statistics())
```

## Command-Line Demo

```bash
fdmm --n 20 --mode basic --updates 200
```

Or:

```bash
python scripts/demo.py --n 50 --mode multilevel --updates 500
```

## What's Next?

- Read the [Architecture Overview](architecture.md) to understand the algorithm internals
- Check the [FAQ](faq.md) for common questions
- See the [full API documentation](index.md) for detailed reference
- Review the [paper restatement](paper_restatement.md) for the theoretical background
