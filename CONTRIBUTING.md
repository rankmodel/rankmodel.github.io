# Contributing to ModelRank

Thank you for contributing!

## Setup

```bash
git clone https://github.com/rankmodel/rankmodel1.git
cd modelrank
pip install -r requirements.txt -r requirements-optional.txt
cp .env.example .env
```

## Running

```bash
make api   # FastAPI at :8000
make ui    # Gradio UI at :7860
```

## Tests

```bash
make test  # or: pytest tests/ -v
```

## Code Style

- Format: `black --line-length 100`
- Lint: `ruff check .`
- Type hints on all public functions

## Pull Request Process

1. Open an issue for major changes first
2. Ensure all tests pass
3. Update README if behavior changes
4. Keep PRs focused on a single concern

## Adding a New Benchmark

1. Add entry to `BENCHMARK_META` in `scoring/benchmarks.py`
2. Add all dataset name aliases to `ALIAS_MAP`
3. Add a test case in `tests/test_scoring.py`

## Bug Reports

Open a GitHub issue with Python version, reproduction steps, and log output.
