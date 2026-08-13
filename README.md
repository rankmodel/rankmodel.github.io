# 🏆 ModelRank

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/tests-27%20passing-brightgreen.svg)](tests/)
[![Models Ranked](https://img.shields.io/badge/models%20ranked-71%2B-blue.svg)](https://rankmodel.github.io/rankmodel1/leaderboard.json)

> **The independent standard for evaluating open-weight AI models. Composite scoring, tier rankings, ELO comparison, embeddable SVG badges, and a viral distribution flywheel — all free, open-source, and conflict-of-interest-free.**

🌐 **[Live Leaderboard](https://rankmodel.github.io/rankmodel1)** · 💰 **[Pricing](https://rankmodel.github.io/rankmodel1/pricing.html)** · 📚 **[Methodology](https://rankmodel.github.io/rankmodel1/methodology.html)** · 🔌 **[API Docs](https://rankmodel.github.io/rankmodel1/api.html)** · 🤗 **[HuggingFace Space](https://huggingface.co/spaces/pal404error/modelrank)**

---

## ✨ What Makes ModelRank Different

| Feature | ModelRank | Chatbot Arena | Open LLM Leaderboard | Artificial Analysis |
|---------|-----------|---------------|---------------------|---------------------|
| Embeddable badges | ✅ Free SVG | ❌ | ❌ | ❌ |
| Composite 5D score | ✅ | ❌ Pref only | ❌ Benchmarks only | ✅ Perf+Cost |
| Open source | ✅ MIT | ✅ | ✅ | ❌ |
| Efficiency scoring | ✅ | ❌ | ❌ | ✅ |
| Community signals | ✅ | ❌ | ❌ | ❌ |
| No API cost to use | ✅ | ✅ | ✅ | ❌ Paywalled |
| Daily auto-updates | ✅ | ✅ | ✅ | ✅ |

---

## 🚀 Quick Start

```bash
git clone https://github.com/rankmodel/rankmodel1.git
cd modelrank
pip install -r requirements.txt
cp .env.example .env  # add your HF_TOKEN

# Score a model
python main.py score --model mistralai/Mistral-7B-v0.1

# Start leaderboard UI
python main.py ui   # → http://localhost:7860

# Start REST API
python main.py api  # → http://localhost:8000/docs

# Regenerate static assets (badges, leaderboard.json, HTML pages)
python scripts/generate_static_assets.py --limit 200

# Generate outreach campaign for top 20 model creators
python scripts/generate_outreach.py --top 20

# Generate NotebookLM research briefing
python -m data.notebooklm_integration --briefing
```

---

## 📐 Scoring Methodology

ModelRank uses a **5-dimension weighted composite score** (0-100):

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| 🧠 **Benchmarks** | 40% | MMLU-Pro, GPQA Diamond, HLE, GSM8K, HumanEval + 8 more |
| ⚡ **Efficiency** | 20% | Benchmark score per billion parameters (rewards small models) |
| 🔥 **Community** | 20% | Log-normalized downloads + likes + trending rank |
| 🕐 **Freshness** | 10% | Exponential decay (180-day half-life from last update) |
| ✅ **Verified** | 10% | Source credibility + benchmark diversity bonus |

**Extended Metadata (10 additional signals):** Context window, VRAM tier, license score, finetune friendliness, multilingual coverage, safety score, update velocity, inference provider coverage, community momentum, hub completeness.

### Tier System

| Tier | Score | Examples |
|------|-------|---------|
| 💜 **S** | 90–100 | GPT-4 class, absolute bleeding edge |
| 💙 **A** | 80–89 | Llama-3.1-70B, Qwen2.5-72B |
| 💚 **B** | 70–79 | Mistral-7B, Phi-3, Gemma-2-9B |
| 💛 **C** | 60–69 | Solid but outclassed by newer models |
| ❤️ **D** | <60 | Legacy / niche |

### ELO Head-to-Head Comparison

Uses the **Bradley-Terry model**:
```
P(A beats B) = 1 / (1 + 10^((ELO_B - ELO_A) / 400))
```

---

## 🏷️ Embed Badges in Your README

Get a free ModelRank badge for your HuggingFace model in seconds:

```markdown
<!-- Standard SVG badge (GitHub Pages CDN, always-on) -->
![ModelRank Score](https://rankmodel.github.io/rankmodel1/badges/ORG/MODEL/score.svg)
![ModelRank Tier](https://rankmodel.github.io/rankmodel1/badges/ORG/MODEL/tier.svg)
![ModelRank Rank](https://rankmodel.github.io/rankmodel1/badges/ORG/MODEL/rank.svg)

<!-- Shields.io style (works with img.shields.io, more customizable) -->
![ModelRank](https://img.shields.io/endpoint?url=https://rankmodel.github.io/rankmodel1/badges/ORG/MODEL/shields.json)
```

Replace `ORG/MODEL` with your model's HuggingFace path (e.g. `mistralai/Mistral-7B-v0.1`).

---

## 🔌 API Reference

Base URL: `https://your-deployment.com` (or run locally with `python main.py api`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/score/{model_id}` | Full composite score |
| GET | `/score/{model_id}/extended` | Score + 10 extended metadata signals |
| GET | `/shields/{model_id}` | **Shields.io JSON endpoint** |
| GET | `/badge/{model_id}?type=score\|tier\|rank` | SVG badge |
| GET | `/leaderboard?limit=N&tier=A&task=text-generation` | Paginated leaderboard |
| GET | `/compare?model_a=...&model_b=...` | ELO win probability |
| GET | `/achievements/{model_id}` | Achievement badges |
| POST | `/score/batch` | Score up to 20 models |
| GET | `/meta` | Version, stats, links |
| GET | `/health` | Health check + leaderboard stats |

Full interactive docs: `http://localhost:8000/docs`

---

## 🤖 CI/CD Integration (GitHub Action)

Add ModelRank score checking to your CI/CD pipeline:

```yaml
- name: Check ModelRank Score
  uses: rankmodel/rankmodel1/.github/actions/modelrank-check@main
  with:
    model_id: 'your-org/your-model'
    min_score: '70'          # Fail if score drops below 70
    min_tier: 'B'            # Fail if tier drops below B
```

---

## 🗂️ Project Structure

```
modelrank/
├── main.py                        # CLI entrypoint
├── api/
│   ├── server.py                  # FastAPI REST API (10 endpoints)
│   └── premium.py                 # Premium plan endpoints
├── scoring/
│   ├── engine.py                  # Composite score + ELO + 10-param extended
│   ├── benchmarks.py              # Benchmark normalization (frontier + classic fallback)
│   ├── efficiency.py              # Parameter efficiency scoring
│   ├── community.py               # Community scoring
│   ├── recency.py                 # Freshness scoring
│   └── reproducibility.py        # Reproducibility scoring
├── data/
│   ├── fetcher.py                 # HuggingFace API client
│   ├── cache.py                   # SQLite WAL cache (WAL mode)
│   ├── models.py                  # Pydantic models
│   └── notebooklm_integration.py  # NotebookLM research briefings
├── badges/
│   ├── generator.py               # SVG badge generation (score/tier/rank)
│   └── premium_generator.py       # Animated/glow/featured pro badges
├── config/
│   ├── settings.py                # All config + env vars
│   └── pricing.py                 # Free/Pro/Featured/Enterprise plans
├── scripts/
│   ├── generate_static_assets.py  # Builds index.html + all badges + pricing/methodology/api pages
│   ├── seed_leaderboard.py        # Bulk model ingestion from HuggingFace
│   ├── generate_outreach.py       # Personalized DM generator for model creators
│   └── setup_brand.py             # Brand asset setup
├── static_output/                 # GitHub Pages CDN output
│   ├── index.html                 # Live leaderboard (71+ models)
│   ├── pricing.html               # Premium landing page
│   ├── methodology.html           # Trust/methodology documentation
│   ├── api.html                   # API reference
│   ├── leaderboard.json           # Machine-readable leaderboard
│   ├── changelog.json             # Version history
│   └── badges/                   # 71+ SVG badges + shields.json endpoints
├── outputs/
│   ├── outreach_campaign.md       # Ready-to-send DMs for model creators
│   ├── notebooklm_briefing.md     # AI research briefing for NotebookLM
│   ├── notebooklm_briefing_v2.md  # Strategic competitive analysis
│   ├── modelrank_weekly_1.md      # First ModelRank Weekly newsletter
│   └── notebooklm_sources/        # Source files for NotebookLM upload
├── .github/
│   ├── workflows/
│   │   ├── update_leaderboard.yml # Daily scoring cron
│   │   └── deploy_pages.yml       # GitHub Pages deployment
│   └── actions/modelrank-check/   # CI/CD GitHub Action
├── tests/
│   └── test_scoring.py            # 27 unit tests (all passing)
└── ui/app.py                      # Gradio web interface
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

## 🎙️ NotebookLM Integration

Generate AI research briefings and competitive analysis:

```bash
# Full leaderboard briefing (ready to upload to NotebookLM)
python -m data.notebooklm_integration --briefing

# Export all model research docs as NotebookLM sources
python -m data.notebooklm_integration --export-all

# Score a specific model with a research document
python -m data.notebooklm_integration mistralai/Mistral-7B-v0.1
```

Output files in `outputs/notebooklm_sources/` are ready for direct upload to [NotebookLM](https://notebooklm.google.com) to generate a research podcast.

---

## 📦 Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_TOKEN` | — | HuggingFace token (strongly recommended) |
| `CACHE_DB_PATH` | `data/modelrank.db` | SQLite DB path |
| `API_PORT` | `8000` | API port |
| `MODELRANK_ADMIN_SECRET` | — | Admin endpoint protection |
| `NOTEBOOKLM_ENABLED` | `false` | Enable NotebookLM podcast generation |

---

## 🧪 Testing

```bash
make test
# or: pytest tests/ -v
# Output: 27 passed in 0.07s
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). PRs welcome!

### Roadmap
- [ ] VS Code extension (hover on model name → show score)
- [ ] "Best Model for Use Case" interactive quiz
- [ ] Weekly automated ModelRank newsletter
- [ ] arXiv methodology paper
- [ ] LangChain / LlamaIndex integration
- [ ] "Model DNA" shareable cards (Spotify Wrapped for models)

## 📄 License

[MIT](LICENSE) — ModelRank is independent and has no affiliation with HuggingFace, Meta, Google, or any model creator.
