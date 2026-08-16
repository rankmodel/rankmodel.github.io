# 🏆 ModelRank

<p align="center">
  <img src="https://img.shields.io/badge/ModelRank-Independent%20AI%20Leaderboard-8A2BE2" alt="ModelRank">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/models%20ranked-150%2B-8A2BE2" alt="models">
</p>

<p align="center">
  <b>The independent standard for open-weight AI.</b><br>
  A conflict-of-interest-free leaderboard that sits <i>on top of</i> HuggingFace, Ollama & every hub —
  transparent 5D scoring, head-to-head ELO, and free embeddable badges.
</p>

<p align="center">
  <img src="https://rankmodel.github.io/rankmodel1/badges/meta-llama/Llama-3.1-8B/score.svg" alt="Live ModelRank badge example" width="320">
</p>

<p align="center">
  🌐 <a href="https://rankmodel.github.io/rankmodel1">Live Leaderboard</a> ·
  🤗 <a href="https://huggingface.co/spaces/pal404error/modelrank">HuggingFace Space</a> ·
  💰 <a href="https://rankmodel.github.io/rankmodel1/pricing.html">Pricing</a> ·
  📚 <a href="https://rankmodel.github.io/rankmodel1/methodology.html">Methodology</a> ·
  🎙️ <a href="https://notebooklm.google.com">Weekly Podcast</a>
</p>

<p align="center">
  <a href="https://github.com/rankmodel/rankmodel1/stargazers"><img src="https://img.shields.io/github/stars/rankmodel/rankmodel1?style=social" alt="Stars"></a>
  <a href="https://star-history.com/#rankmodel/rankmodel1&Date"><img src="https://api.star-history.com/svg?repos=rankmodel/rankmodel1&type=Date" alt="Star History" width="420"></a>
</p>

> ⭐ **If ModelRank helps you cut through AI-model hype, star the repo** — it's free, and stars are how an independent project like this grows.

---

## 🎯 Mission

**Make "which AI model should I actually use?" a solved question** — with scoring that no model vendor can buy, rig, or own.

- 🔍 **Independence first.** Zero conflict of interest: we don't train or host models, so we have no incentive to rank our own higher.
- 📊 **Transparency by default.** Every score is reproducible from public signals — benchmarks, efficiency, community, freshness, provenance.
- 🌍 **Free for everyone, forever.** The badge — our growth engine — is free; we monetize *visibility & trust*, never the score.
- 🤖 **Self-improving.** An autonomous agent "company" keeps the data fresh, the content flowing, and the community growing.

## ✨ Why ModelRank exists

HuggingFace tells you **what models exist**. ModelRank tells you **which ones are actually good** — with a transparent, weighted score and head-to-head win probabilities, not a black box.

We are **not** a model factory and we don't host weights. We have **zero incentive** to rank our own models higher, because we don't make any. That independence is the whole point.

> 🔥 *A 7B model just beat a 70B model on efficiency. ModelRank is the only leaderboard that shows you.*

## 🚀 Try it in 10 seconds

```bash
pip install -e .
python main.py score --model mistralai/Mistral-7B-v0.1
```

Or run the **live leaderboard UI** (Gradio):

```bash
python main.py ui   # → http://localhost:7860
```

Or hit the **REST API**:

```bash
python main.py api  # → http://localhost:8000/docs
```

No API key needed to *use* ModelRank. (Add `HF_TOKEN` for higher HuggingFace rate limits.)

## 🏷️ Get your free badge (the viral part)

Paste this into **your** model's README and you're on the leaderboard:

```markdown
![ModelRank Score](https://rankmodel.github.io/rankmodel1/badges/ORG/MODEL/score.svg)
![ModelRank Tier](https://rankmodel.github.io/rankmodel1/badges/ORG/MODEL/tier.svg)
```

Replace `ORG/MODEL` with your HuggingFace path (e.g. `meta-llama/Llama-3.1-8B`).
Every badge is a backlink to the leaderboard — that's how we grow.

## 📐 How models are scored (composite, 0–100)

> **Weights live in `config/settings.py` (`SCORING_WEIGHTS`) — that file is the single
> source of truth**, not this README. The composite is currently a **4 active-dimension**
> blend: `reproducibility` is reserved in the schema but weighted `0.00` until its
> signals are wired in (so "5D" today means 4 weighted dimensions + 1 reserved).

| Dimension | Weight | Measures |
|-----------|--------|----------|
| 🧠 **Benchmarks** | 70% | MMLU-Pro (0.25), GPQA (0.20), HLE (0.20), GSM8K (0.20), HumanEval (0.15) |
| 🕐 **Recency** | 15% | 180-day half-life decay (formerly "Freshness") |
| 🔥 **Community** | 10% | Downloads + likes + trending rank |
| ⚡ **Efficiency** | 5% | Score per billion params (rewards small models) |
| ✅ **Reproducibility** | 0% | Source credibility + benchmark diversity (reserved) |

Plus **ELO head-to-head** (`P(A>B) = 1 / (1 + 10^((ELO_B-ELO_A)/400))`) and extended
signals (context window, VRAM tier, license, multilingual, safety, momentum, …).
Benchmarks are normalized against population bounds (`leaderboard_bounds`) so the
score is comparable across the whole catalog.

## ⚖️ How we compare

| Feature | ModelRank | Chatbot Arena | Open LLM LB | Artificial Analysis |
|---------|-----------|---------------|-------------|---------------------|
| Embeddable **free** badges | ✅ | ❌ | ❌ | ❌ |
| Composite 5D score | ✅ | pref-only | bench-only | perf+cost |
| Open source (MIT) | ✅ | ✅ | ✅ | ❌ |
| Efficiency scoring | ✅ | ❌ | ❌ | ✅ |
| Community signals | ✅ | ❌ | ❌ | ❌ |
| **Independent / no COI** | ✅ | ⚠️ | ⚠️ | ❌ |

## 💸 Revenue model (open-core hybrid)

The **free badge is the growth engine** — it stays free, forever. Devs pay for **visibility & trust**, never for the score:

- **Verified** — prove ownership / provenance.
- **Featured** — bought placement on the leaderboard & weekly newsletter.
- **Glow** — animated premium badges for paid tiers.
- **Enterprise API** — SLA, rate limits, white-label.
- **CI gating** — fail builds below a score/tier.

See [Pricing](https://rankmodel.github.io/rankmodel1/pricing.html). Free core drives adoption; paid tier solves real problems. We never cripple the free badge.

## 🤝 CI/CD (GitHub Action)

```yaml
- uses: rankmodel/rankmodel1/.github/actions/modelrank-check@main
  with:
    model_id: 'your-org/your-model'
    min_score: '70'
    min_tier: 'B'
```

## 🤖 The ModelRank Agency

ModelRank also ships as a **Paperclip-style company of AI agents** that grows itself
— modeled on [paperclipai/paperclip](https://github.com/paperclipai/paperclip). A
CEO, CMO, DevRel, Platform Eng, Outreach, and Analytics agent run daily/weekly
heartbeats (regenerate assets, draft posts, publish the newsletter, recruit
creators) under approval gates and a budget hard-stop. See
[`agency/`](agency/) — `python agency/agency.py --list`.

## 🗂️ Project structure

```
main.py                 # CLI: api | ui | score | leaderboard
api/                    # FastAPI REST (10 endpoints) + premium
scoring/                # composite engine, ELO, benchmarks, efficiency, community, recency
data/                   # HF fetcher, SQLite cache, NotebookLM integration
badges/                 # SVG + premium (glow/featured) generators
config/                 # settings + pricing tiers
scripts/                # static asset + outreach generators
agency/                 # Paperclip-style autonomous growth company (agents + routines)
static_output/          # GitHub Pages CDN (leaderboard, badges, pages)
ui/app.py               # Gradio leaderboard
tests/                  # 34 passing unit tests
```

## 🗺️ Roadmap

- [x] 150+ seeded models, 5D scoring, ELO, badges, pricing
- [x] Shareable **"Model DNA"** cards (Spotify-Wrapped for models)
- [x] **ModelRank Agency** — Paperclip-style autonomous growth company
- [ ] Interactive **"Best model for my use case"** quiz
- [ ] VS Code extension (hover a model name → see its score)
- [ ] LangChain / LlamaIndex integration
- [ ] Weekly automated **ModelRank** newsletter + podcast

## 🧪 Tests

```bash
make test   # 39 passed
```

## 📄 License

[MIT](LICENSE) — ModelRank is independent and has no affiliation with HuggingFace, Meta, Google, or any model creator.
