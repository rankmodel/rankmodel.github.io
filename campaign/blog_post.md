---
layout: post
title: "We ranked 120 open LLMs. The efficient small models are embarrassingly good."
---

Most leaderboards are vanity galleries for the biggest, most expensive models money can buy. ModelRank isn't. We're an independent, open leaderboard with no model to sell and no API to push. So we asked a simple question: what actually happens when you score open models on more than just raw benchmark bragging rights?

The answer made the small models look very, very good.

## How we score: five dimensions, zero sales pitch

Every model in our index gets a transparent composite score built from five dimensions. Here are the weights we apply today:

- **Benchmarks (70%)** — normalized performance across MMLU-Pro, GPQA, HLE, GSM8K, HumanEval and friends. The raw "is it smart" signal.
- **Efficiency (5%)** — performance relative to size and hardware cost. Smaller and leaner wins.
- **Community (10%)** — downloads, likes, and real-world adoption on the hubs.
- **Recency (15%)** — how fresh the release is. A 2026 model shouldn't lose to a 2022 relic by default.
- **Reproducibility (currently 0% weight)** — we compute and display a reproducibility score for every model (measuring eval diversity and verifiability), but right now it carries a 0% weight in the composite while we validate the signal. It's shown, not hidden.

Benchmarks dominate by design. But efficiency is where the story gets interesting, because the raw-smart leader and the efficient leader are not the same model at all.

## The real top 5 (by composite score)

Pulled live from our index of 120 open models:

| Rank | Model | Composite | Tier | Efficiency |
|------|-------|-----------|------|------------|
| 1 | `zai-org/GLM-5.2` | 87.35 | A | 27.13 |
| 2 | `prism-ml/Bonsai-27B-gguf` | 86.79 | A | 34.00 |
| 3 | `deepseek-ai/DeepSeek-V4-Pro` | 86.22 | A | 27.00 |
| 4 | `deepseek-ai/DeepSeek-V4-Flash` | 84.28 | A | 27.49 |
| 5 | `deepseek-ai/DeepSeek-V3.2` | 82.40 | A | 27.14 |

GLM-5.2 tops the chart at 87.35. Impressive. Now look at its efficiency score: 27.13.

## The efficiency leaders tell a different story

When we sort purely by our efficiency dimension, the podium flips completely:

- **`HuggingFaceTB/SmolLM2-135M` — efficiency score 99.91.** The most efficient model in our entire index. It's a 135-million-parameter model. It beats the #1 composite model on efficiency by nearly 73 points.
- `Qwen/Qwen2-0.5B` — 88.39
- `Qwen/Qwen2.5-0.5B` — 88.29
- `Qwen/Qwen2.5-1.5B` — 74.64
- `google/gemma-3-1b-it` — 74.62
- `Qwen/Qwen3-4B-Instruct-2507` — 65.38, and it still lands in **tier B** with a composite of 70.85.

Here's the honest, defiant point: the single most efficient model we've ranked is a 135M-parameter model that fits in your pocket. The top composite model is an efficiency also-ran at 27.13. A 4B model (`Qwen3-4B-Instruct-2507`) delivers tier-B quality at more than 2.4x the efficiency of the overall #1.

## Small vs large, in real numbers

We're not going to invent cost-per-token figures. What we can say from real fields in our data:

- The most efficient model (`SmolLM2-135M`) scores **99.91** on efficiency; the top composite model scores **27.13**. That's not a rounding error. That's a different job.
- A 4B model reaches **tier B (composite 70.85)** while staying at **65.38** efficiency. The 27B+ flagship models cluster around 27-34 on efficiency. Same leaderboard, very different tradeoffs.

If your workload fits in a small model, you are leaving enormous efficiency on the table by defaulting to the biggest name. Bigger is not automatically better. It's just louder.

## Why this matters

A leaderboard that only rewards size is a leaderboard that serves vendors, not users. We're independent precisely so we can show you the model that sips compute and still gets the job done. No conflict of interest, no hosted model to promote, full methodology in the open.

Think we're wrong? Open a PR with your benchmark. The scores are computed from public signals and the code is right there. Rank us.

- Browse the live leaderboard: https://rankmodel.github.io
- Source and methodology: https://github.com/rankmodel/rankmodel.github.io
