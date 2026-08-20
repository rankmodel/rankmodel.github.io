# 🏆 ModelRank

<p align="center">
  <img src="https://img.shields.io/badge/ModelRank-Independent%20AI%20Leaderboard-8A2BE2" alt="ModelRank">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/models%20ranked-150%2B-8A2BE2" alt="models">
</p>

<p align="center">
  <b>The independent standard for open-weight AI.</b><br>
  A leaderboard that sits on top of HuggingFace, Ollama, and every hub. It uses
  transparent 5-dimension scoring, head-to-head ELO, and free embeddable badges.
</p>

<p align="center">
  <img src="https://rankmodel.github.io/badges/meta-llama/Llama-3.1-8B/score.svg" alt="Live ModelRank badge example" width="320">
</p>

<p align="center">
  🌐 <a href="https://rankmodel.github.io">Live Leaderboard</a> ·
  🤗 <a href="https://huggingface.co/spaces/pal404error/modelrank">HuggingFace Space</a> ·
  💰 <a href="https://rankmodel.github.io/pricing.html">Pricing</a> ·
  📚 <a href="https://rankmodel.github.io/methodology.html">Methodology</a> ·
  📰 <a href="https://rankmodel.github.io/weekly.html">Weekly</a>
</p>

<p align="center">
  <a href="https://github.com/rankmodel/rankmodel.github.io/stargazers"><img src="https://img.shields.io/github/stars/rankmodel/rankmodel.github.io?style=social" alt="Stars"></a>
  <a href="https://star-history.com/#rankmodel/rankmodel.github.io&Date"><img src="https://api.star-history.com/svg?repos=rankmodel/rankmodel.github.io&type=Date" alt="Star History" width="420"></a>
</p>

> ⭐ **If ModelRank helps you cut through AI-model hype, star the repo.** It is free, and stars are how an independent project grows.

---

## Why ModelRank

HuggingFace tells you what models exist. ModelRank tells you which ones are actually good, using a transparent, weighted score and head-to-head win probabilities instead of a black box.

We are not a model factory and we do not host weights. We have no reason to rank our own models higher, because we do not make any. Independence is the point.

A 7B model can beat a 70B model on efficiency. ModelRank is built to surface that.

## Features

- **Transparent 5-dimension scoring.** Benchmarks, efficiency, community, recency, and reproducibility, all weighted and reproducible from public signals.
- **Head-to-head ELO.** Compare any two models and see live win probabilities from community and LLM-judge verdicts.
- **Free embeddable badges.** Drop a score or tier badge into your README. Every badge links back to the leaderboard.
- **Agent-ready.** A zero-dependency Python client, plus LangChain and LlamaIndex tools.
- **VS Code extension.** Hover any `org/model` id and see its score and breakdown instantly.
- **ModelRank Weekly.** A data-driven newsletter on the model landscape, published every week.

## Try it in 10 seconds

```bash
pip install -e .
python main.py score --model mistralai/Mistral-7B-v0.1
```

Or run the live leaderboard UI (Gradio):

```bash
python main.py ui   # → http://localhost:7860
```

Or hit the REST API:

```bash
python main.py api  # → http://localhost:8000/docs
```

No API key is needed to use ModelRank. Add `HF_TOKEN` for higher HuggingFace rate limits.

## Get your free badge

Paste this into your model's README and you are on the leaderboard:

```markdown
![ModelRank Score](https://rankmodel.github.io/badges/ORG/MODEL/score.svg)
![ModelRank Tier](https://rankmodel.github.io/badges/ORG/MODEL/tier.svg)
```

Replace `ORG/MODEL` with your HuggingFace path (for example `meta-llama/Llama-3.1-8B`).
Every badge is a backlink to the leaderboard, which is how the community grows.

## How models are scored (composite, 0 to 100)

| Dimension | Weight | Measures |
|-----------|--------|----------|
| 🧠 **Benchmarks** | 70% | MMLU-Pro (0.25), GPQA (0.20), HLE (0.20), GSM8K (0.20), HumanEval (0.15) |
| 🕐 **Recency** | 15% | 180-day half-life decay |
| 🔥 **Community** | 10% | Downloads + likes + trending rank |
| ⚡ **Efficiency** | 5% | Score per billion params (rewards small models) |
| ✅ **Reproducibility** | 0% | Source credibility + benchmark diversity (reserved) |

Plus ELO head-to-head (`P(A>B) = 1 / (1 + 10^((ELO_B-ELO_A)/400))`) and extended
signals (context window, VRAM tier, license, multilingual, safety, momentum, and so on).
Benchmarks are normalized against population bounds so the score is comparable across
the whole catalog.

## How we compare

| Feature | ModelRank | Chatbot Arena | Open LLM LB | Artificial Analysis |
|---------|-----------|---------------|-------------|---------------------|
| Embeddable free badges | ✅ | ❌ | ❌ | ❌ |
| Composite 5D score | ✅ | pref-only | bench-only | perf+cost |
| Open source (MIT) | ✅ | ✅ | ✅ | ❌ |
| Efficiency scoring | ✅ | ❌ | ❌ | ✅ |
| Community signals | ✅ | ❌ | ❌ | ❌ |
| Independent, no conflicts of interest | ✅ | ⚠️ | ⚠️ | ❌ |

## Community head-to-head (ELO + LLM judge)

Beyond the composite score, ModelRank runs direct comparisons between models
and tracks them with an ELO rating. Anyone can judge a pair, either a human verdict or
an impartial LLM vibe-check, and every verdict feeds the community standings.

```bash
# Record a human verdict
curl -X POST http://localhost:8000/judge/human \
  -H "Content-Type: application/json" \
  -d '{"model_a":"Qwen/Qwen3.5-9B","model_b":"deepseek-ai/DeepSeek-R1","verdict":"A"}'

# See the community standings
curl "http://localhost:8000/elo-leaderboard?limit=10"

# Run the LLM-judge vibe-check (set JUDGE_API_BASE / JUDGE_API_KEY / JUDGE_MODEL)
curl "http://localhost:8000/judge/Qwen/Qwen3.5-9B/deepseek-ai/DeepSeek-R1"
```

The same data powers the public [Head-to-Head](https://rankmodel.github.io/head-to-head.html)
page (ELO standings + verdict feed) and the Judge and ELO tab in the Gradio UI.

## VS Code extension

Hover any HuggingFace model id in your editor, such as `meta-llama/Llama-3.1-8B` or
`Qwen/Qwen3.5-9B`, and get its ModelRank score, tier, and 5-dimension breakdown, fetched
live from the API. Built on `ModelRankClient` (`vscode-extension/`, run `npm install && npm run compile`).

## Python client and agent tools

```python
from api.client import ModelRankClient

client = ModelRankClient()                       # or ModelRankClient(base_url="http://localhost:8000")
top = client.leaderboard(limit=10)
score = client.score("mistralai/Mistral-7B-v0.1")
cmp = client.compare("Qwen/Qwen3.5-9B", "deepseek-ai/DeepSeek-R1")
```

Drop ModelRank into your own agents via the `integrations/` package:

```python
from integrations.langchain import get_modelrank_langchain_tools   # LangChain
from integrations.llama_index import get_modelrank_llama_index_tools  # LlamaIndex
```

Tools: `modelrank_score`, `modelrank_compare`, `modelrank_recommend`, `modelrank_head_to_head`.

## Use ModelRank in CI

Fail a build when a model drops below a score or tier:

```yaml
- uses: rankmodel/rankmodel.github.io/.github/actions/modelrank-check@main
  with:
    model_id: 'your-org/your-model'
    min_score: '70'
    min_tier: 'B'
```

## License

[MIT](LICENSE). ModelRank is independent and has no affiliation with HuggingFace, Meta, Google, or any model creator.
