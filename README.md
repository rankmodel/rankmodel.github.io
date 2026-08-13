# 🏆 ModelRank

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Gradio](https://img.shields.io/badge/UI-Gradio-FF7C00.svg)](https://gradio.app)

> **Composite scoring, tier rankings, ELO-based model comparison, dynamic SVG badges, and AI podcast generation for the HuggingFace ecosystem.**

ModelRank evaluates HuggingFace models across 5 dimensions and produces a composite score (0-100), tier assignment (S/A/B/C/D), leaderboard rank, embeddable SVG badges, and head-to-head ELO win probabilities for any model.

---

## ✨ Features

- **🧠 Composite Scoring** — 5-dimension weighted scoring across Benchmarks, Efficiency, Community, Freshness, and Verification
- **📊 Tier System** — S/A/B/C/D grades with color-coded tier badges
- **⚔️ ELO Comparison** — Head-to-head Bradley-Terry win probability with per-dimension breakdown
- **🎨 Dynamic SVG Badges** — Embeddable score, tier, rank, dimension, and achievement badges
- **🏅 Achievements** — Milestone badges: Efficiency King, Community Favorite, Benchmark Champion, and more
- **🎙️ Podcast Generation** — AI deep-dive podcasts via Google NotebookLM (optional)
- **⚡ FastAPI Backend** — Full REST API with pagination, batch scoring, comparison, and health checks
- **🖥️ Gradio UI** — Interactive leaderboard, radar charts, model comparison, search, badge studio
- **📦 SQLite Cache** — WAL-mode local database with TTL-based invalidation
- **🔧 CLI Interface** — Score models and view leaderboard from your terminal

---

## 🚀 Quick Start

```bash
# Clone and install
git clone https://github.com/yourusername/modelrank.git
cd modelrank
pip install -r requirements.txt

# Configure (optional)
cp .env.example .env

# Score a model
python main.py score --model mistralai/Mistral-7B-v0.1

# Start UI
python main.py ui   # → http://localhost:7860

# Start API
python main.py api  # → http://localhost:8000/docs
```

---

## 📐 Scoring Methodology

| Dimension | Weight | Description |
|-----------|--------|-------------|
| 🧠 **Benchmarks** | 40% | MMLU-Pro, GPQA, HLE, GSM8K, HumanEval accuracy |
| ⚡ **Efficiency** | 20% | Benchmark performance per billion parameters |
| 🔥 **Community** | 20% | Log-normalized downloads + likes + trending rank |
| 🕐 **Freshness** | 10% | Exponential decay (180-day half-life from last update) |
| ✅ **Verified** | 10% | Source credibility + benchmark diversity bonus |

### Tier System

| Tier | Score | Description |
|------|-------|-------------|
| 💜 S | 90–100 | State of the art |
| 💙 A | 80–89 | Excellent |
| 💚 B | 70–79 | Solid |
| 💛 C | 60–69 | Niche |
| ❤️ D | <60 | Legacy |

### ELO-Based Comparison

ModelRank uses the **Bradley-Terry model** for head-to-head comparison:
```
P(A beats B) = 1 / (1 + 10^((ELO_B - ELO_A) / 400))
```
Composite scores map to an 800–1600 ELO scale. The `/compare` API endpoint returns per-dimension winners and overall win probability.

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check + cache stats |
| GET | `/score/{model_id}` | Full composite score |
| GET | `/badge/{model_id}` | SVG badge |
| GET | `/leaderboard` | Ranked leaderboard (paginated) |
| POST | `/score/batch` | Score up to 20 models |
| GET | `/compare?model_a=...&model_b=...` | ELO head-to-head comparison |
| GET | `/achievements/{model_id}` | Earned achievements |
| GET | `/embed/{model_id}` | HTML badge embed snippet |

### Embed Badges in Your Model Card

```markdown
![Score](http://localhost:8000/badge/org/model?type=score)
![Tier](http://localhost:8000/badge/org/model?type=tier)
![Rank](http://localhost:8000/badge/org/model?type=rank)
```

---

## 🏅 Achievements

| Badge | Trigger |
|-------|---------|
| ⚡ Efficiency King | Efficiency score > 85 |
| ❤️ Community Favorite | Community score > 80 |
| 🏆 Benchmark Champion | Benchmark score > 90 |
| 🔥 Top Trending | HF top-10 trending |
| 🔓 Abliterated | Uncensored model |
| 📦 Quantized Ready | GGUF/AWQ/GPTQ available |
| 👑 #1 Global | Leaderboard rank 1 |

---

## 🗂️ Project Structure

```
modelrank/
├── main.py              # CLI entrypoint
├── api/server.py        # FastAPI REST API
├── ui/app.py            # Gradio web interface
├── scoring/
│   ├── engine.py        # Composite score + ELO comparison
│   ├── benchmarks.py    # Benchmark normalization + coverage
│   ├── efficiency.py    # Param efficiency scoring
│   ├── community.py     # Community scoring
│   ├── recency.py       # Freshness scoring
│   └── reproducibility.py
├── data/
│   ├── fetcher.py       # HuggingFace API client
│   ├── cache.py         # SQLite WAL cache
│   └── models.py        # Pydantic models
├── badges/              # SVG badge generation
├── scripts/
│   └── seed_leaderboard.py  # Bulk ingestion
├── tests/
│   └── test_scoring.py  # Unit tests
├── .env.example         # Configuration reference
├── Makefile             # Dev commands
└── pyproject.toml       # Package config
```

---

## 🧪 Testing

```bash
make test
# or: pytest tests/ -v
```

---

## 🎙️ Podcast Generation (Optional)

```bash
pip install notebooklm-py[browser]
notebooklm login
python -m data.notebooklm_integration mistralai/Mistral-7B-v0.1
```

Or use the **Podcast Studio** tab in the UI.

---

## 📦 Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_TOKEN` | — | HuggingFace token (recommended) |
| `CACHE_DB_PATH` | `data/modelrank.db` | DB path |
| `API_PORT` | `8000` | API port |
| `ALLOWED_ORIGINS` | `*` | CORS origins |

See [`.env.example`](.env.example) for all options.

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). PRs welcome!

## 📄 License

[MIT](LICENSE)
