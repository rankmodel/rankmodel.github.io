# r/LocalLLaMA

**Title: We ranked 120 open LLMs on efficiency, not just size. The 135M-param model beat the flagships.**

Body:
Most leaderboards reward the biggest model with the biggest marketing budget. We built ModelRank, an independent open leaderboard, because "which model should I actually run locally?" deserves a conflict-free answer.

Real data point: in our index of 120 open models, the single most efficient model by our efficiency dimension is `HuggingFaceTB/SmolLM2-135M` at an efficiency score of 99.91. The top composite model overall, `zai-org/GLM-5.2` (87.35, tier A), scores just 27.13 on efficiency. A 4B model, `Qwen/Qwen3-4B-Instruct-2507`, reaches tier B (composite 70.85) at 65.38 efficiency.

We score five dimensions: benchmarks (70%), recency (15%), community (10%), efficiency (5%), and reproducibility (computed and shown, currently 0% weight). All weights and code are public.

If you run models at home, the efficient small ones are embarrassingly good. Help us improve it: https://github.com/rankmodel/rankmodel.github.io ⭐

---

# r/MachineLearning

**Title: [R] ModelRank: a transparent 5-dimension scoring framework for open LLMs (120 models, methodology public)**

Body:
We released ModelRank, an independent leaderboard that scores open models across five transparent dimensions rather than a single opaque benchmark average.

Problem: nearly every popular leaderboard is operated by an entity that trains or hosts models, creating a structural conflict of interest. We have no model to sell.

Methodology (weights public in `config/settings.py`): benchmarks 70%, recency 15%, community 10%, efficiency 5%, reproducibility 0% (computed and displayed, weight pending validation). Each model carries a full breakdown so the composite is fully explainable.

Real result from our data: the most efficient model is `HuggingFaceTB/SmolLM2-135M` (efficiency 99.91), while the highest composite score is `zai-org/GLM-5.2` (87.35, tier A, efficiency 27.13). The efficiency and composite rankings diverge sharply, which is exactly why we report both.

We'd welcome critique of the weighting and the normalization approach. Source: https://github.com/rankmodel/rankmodel.github.io ⭐

---

# r/selfhosted

**Title: An open leaderboard that actually rates small/self-hostable models on efficiency (not just the 70B giants)**

Body:
If you self-host, you already know the 70B-and-up crowd isn't your reality. Most leaderboards ignore that. ModelRank is an independent, open leaderboard that scores 120 open models on efficiency alongside raw benchmarks.

Real data point: the most efficient model in our index is `HuggingFaceTB/SmolLM2-135M` at 99.91 efficiency, and `Qwen/Qwen3-4B-Instruct-2507` lands in tier B (composite 70.85) with 65.38 efficiency. Small models that run on modest hardware score dramatically higher on efficiency than the flagship composite leaders.

It's built with Python + FastAPI + Gradio and a SQLite cache of HuggingFace data. We don't host or train models, so we're not steering you toward anything we profit from.

Check it out and tell us what to add: https://rankmodel.github.io ⭐

---

# r/artificial

**Title: Why an independent AI leaderboard matters when every big one has a conflict of interest**

Body:
Almost every well-known AI model leaderboard is run by an organization that trains, hosts, or sells the models it ranks. That's a built-in conflict of interest. ModelRank is an independent, open alternative with no model to promote.

We ranked 120 open models on five transparent dimensions: benchmarks (70%), recency (15%), community (10%), efficiency (5%), and reproducibility (shown, 0% weight today). From our real data, the top composite model is `zai-org/GLM-5.2` at 87.35, but the most efficient model is `HuggingFaceTB/SmolLM2-135M` at 99.91, a 135M-parameter model that out-efficiency-kings the flagships by a mile.

The point isn't that small models win everything. It's that "best" depends on what you weight, and today most rankings quietly weight what benefits their owners. Ours are public.

See the methodology and challenge a ranking: https://github.com/rankmodel/rankmodel.github.io ⭐
