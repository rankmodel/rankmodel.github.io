# 🤝 Contributing to ModelRank

You found the independent AI leaderboard. Here's how to make it better.

ModelRank exists because the AI benchmarking industry has a conflict-of-interest problem — and the only answer to that problem is a community of people who refuse to let it stand. Whether you write Python, write prose, or just write tweets, there is a contribution here with your name on it.

**Every contribution type is celebrated equally.** Code is not more valuable than community. A well-placed Reddit comment that sends 500 developers to the leaderboard is worth exactly as much as a bug fix.

---

## ⚡ Quick Setup (For Code Contributors)

```bash
git clone https://github.com/rankmodel/rankmodel.github.io.git
cd modelrank
pip install -r requirements.txt -r requirements-optional.txt
cp .env.example .env
```

Start the services:

```bash
make api   # FastAPI REST API at :8000  →  http://localhost:8000/docs
make ui    # Gradio leaderboard UI at :7860  →  http://localhost:7860
```

Run the test suite:

```bash
make test
# or
pytest tests/ -v
```

That's it. You're running an independent AI leaderboard on your laptop.

---

## 🌍 Non-Code Contributions (This Section Is Critical)

You do not need to write a single line of code to have a meaningful impact on ModelRank. Here's the menu:

### 📬 Submit a Missing Model
Think a model deserves to be on the leaderboard? [Open an issue](https://github.com/rankmodel/rankmodel.github.io/issues/new?template=model-submission.md) and paste the HuggingFace URL. That's the entire process. We'll run the scoring pipeline and add it to the verified set.

### 📝 Fix Documentation Typos
See something wrong in the docs or README? Click **Edit this page** on any page (pencil icon on GitHub) and submit a one-line PR. First-time contributors have landed PRs this way in under 3 minutes.

### 🗳️ Vote in GitHub Discussions
The scoring dimension weights — how much Benchmarks vs. Recency vs. Community matters — are decided by community vote. [Join the Discussions](https://github.com/rankmodel/rankmodel.github.io/discussions) and cast your vote. Your opinion moves the algorithm.

### 📣 Share on Social Media
Share ModelRank where developers hang out. Suggested platforms and angles:

- **Twitter/X:** "Finally, an LLM leaderboard with no conflict of interest. 954+ models, open source, free badges."
- **Reddit:** r/LocalLLaMA, r/MachineLearning, r/singularity — share when you notice a model ranked differently than you expected.
- **LinkedIn:** Great for the "independent benchmarking matters" angle if you work in enterprise AI.
- **Hacker News:** Show HN posts and Ask HN discussions welcome. The methodology is defensible and the code is open.

### ✍️ Write a Blog Post or Review
Write a post about how you used ModelRank to choose a model. We will link it from the README's community section and share it in the [ModelRank Weekly newsletter](https://rankmodel.github.io/weekly.html). Drop a link in [Discussions](https://github.com/rankmodel/rankmodel.github.io/discussions) and we'll find it.

### 🎨 Design Contributions
- New SVG badge templates (the badge system is the viral growth engine — better designs = more embeds)
- README screenshots and demo images
- Social preview cards
- Any visual asset that makes the project more trustworthy at first glance

Open a PR or [start a Discussion](https://github.com/rankmodel/rankmodel.github.io/discussions) with your design. Design PRs are merged fast.

---

## 💻 Code Contributions

### Adding a New Benchmark

Want to add a benchmark to the scoring system? Here's the exact process:

1. **Add the benchmark metadata** to `BENCHMARK_META` in `scoring/benchmarks.py`
   - Include: name, weight (as a fraction of the Benchmarks dimension), source URL, and normalization bounds
2. **Register all dataset name aliases** in `ALIAS_MAP` (HuggingFace dataset names vary; we normalize them)
3. **Write a test case** in `tests/test_scoring.py` — at minimum, test that a known model gets a reasonable score
4. **Update the methodology page** in `docs/methodology.md` (a sentence or two explaining what the benchmark measures)
5. Open a PR. Link to the benchmark's paper or dataset card.

Benchmark additions that come with a clear rationale for *why this benchmark resists gaming* are prioritized for review.

### Improving the Scoring Engine

The core scoring logic lives in `scoring/`. The main entry point is `scoring/engine.py`. If you believe the normalization, weighting, or ELO formula can be improved, open an issue first to discuss. Changes to the scoring formula require a Discussion vote if they shift any model's score by more than 5 points.

### Building a New Integration

We have LangChain and LlamaIndex integrations in `integrations/`. New integrations welcome: AutoGen, CrewAI, Semantic Kernel, DSPy — if there's an agentic framework, ModelRank should plug into it. Use the existing integrations as a template; they are intentionally thin wrappers around `ModelRankClient`.

### Bug Fixes

No process required. Find a bug, open an issue, fix it, open a PR. Keep the PR focused. Tests are required.

---

## 📋 Pull Request Process

1. **Open an issue first** for major changes (new benchmarks, scoring changes, architecture decisions)
2. **Ensure all tests pass** — `make test` must exit 0
3. **Update documentation** if behavior changes (README, docstrings, `docs/`)
4. **Keep PRs focused on a single concern** — atomic PRs merge faster and are easier to review

PRs that add tests for previously untested behavior are especially welcome.

---

## 🐛 Bug Reports

[Open a GitHub issue](https://github.com/rankmodel/rankmodel.github.io/issues/new) and include:

- Python version (`python --version`)
- Exact reproduction steps (the command you ran)
- Full log output (paste the traceback)
- What you expected to happen vs. what actually happened

The more specific, the faster we fix it.

---

## 🖊️ Code Style

We keep it simple and enforced by CI:

- **Format:** `black --line-length 100`
- **Lint:** `ruff check .`
- **Type hints:** required on all public functions
- **Docstrings:** required on all public classes and non-trivial functions

Run both before pushing:

```bash
black --line-length 100 .
ruff check .
```

---

## 🏅 Recognition

This project follows the [all-contributors](https://allcontributors.org/) specification. **Contributions of any kind welcome** — code, docs, design, community, ideas, bug reports.

Every contributor will be listed in the project's contributor graph and recognized in the [ModelRank Weekly newsletter](https://rankmodel.github.io/weekly.html) when their contribution ships.

Open source is a team sport. We keep score of every player.

---

<p align="center">
  Questions? Open a <a href="https://github.com/rankmodel/rankmodel.github.io/discussions">Discussion</a>. We read everything.
</p>
