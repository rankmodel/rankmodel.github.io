# GitHub Discussions

## Discussion 1

title: Weight Vote: should Efficiency go from 5% to 15%?

body:
Right now our composite weights Efficiency at just 5% (Benchmarks 70%, Recency 15%, Community 10%, Efficiency 5%, Reproducibility 0% shown).

But the data keeps embarrassing the big models. In our index of 120 open LLMs, the most efficient model is `HuggingFaceTB/SmolLM2-135M` at an efficiency score of 99.91, while the top composite model `zai-org/GLM-5.2` (87.35, tier A) scores only 27.13 on efficiency. A 4B model, `Qwen/Qwen3-4B-Instruct-2507`, reaches tier B (70.85) at 65.38 efficiency.

Should we give efficiency more say? Vote below.

**Poll: Where should the Efficiency weight land?**
- Keep it at 5% (benchmarks should dominate)
- Raise it to 10% (small nudge toward efficiency)
- Raise it to 15% (efficiency deserves real weight)
- Something else (comment with your number + reasoning)

Drop your vote and a one-line reason. We'll revisit the weights based on this thread.

---

## Discussion 2

title: Missing Models: which models did we miss?

body:
We've scored 120 open models so far, pulled from HuggingFace signals. That's a start, not a finish. The index is only as good as its coverage, and we know we're missing plenty.

**Help us fill the gaps.**

Comment below with:
1. The model's HuggingFace link (e.g. `https://huggingface.co/ORG/MODEL`)
2. One sentence on why it deserves a spot

We'll prioritize the most-requested, most-justified additions and re-score them. Independent coverage only works if the community tells us what to cover.

Examples we'd love eyes on: niche efficient models, strong regional releases, and anything you're actually running in production that isn't on the board yet.

---

## Discussion 3

title: The Great Debate: is higher accuracy worth 10x the cost?

body:
Our top composite model, `zai-org/GLM-5.2`, scores 87.35. The most efficient model in the index, `HuggingFaceTB/SmolLM2-135M`, scores 99.91 on efficiency but a much lower composite. That gap is the whole debate in miniature.

Here's the honest framing: we do NOT publish measured dollar cost-per-token. Cost depends on your hardware, your quantization, your volume, and your negotiator. Anyone quoting you a fixed "$0.00X per 1K tokens" for a self-hosted model is guessing. What we can show is the efficiency dimension, a normalized signal of performance relative to size and hardware burden.

So the philosophical question stands regardless of price tags:

If Model A is 8 points higher on benchmarks but needs 10x the VRAM and 10x the latency of Model B, when is A actually the right call? For a one-shot hard reasoning task? Sure. For a million-call-a-day production pipeline? Probably not.

Where do YOU draw the line between "worth the compute" and "overpriced intelligence"? No right answer, just a tradeoff we think more people should make on purpose instead of by default.
