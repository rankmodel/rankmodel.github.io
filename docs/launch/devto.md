# Dev.to article

**Title:** I built an AI model leaderboard nobody can buy

**Intro:**
Every major leaderboard is owned by a lab, gated behind a paywall, or optimized to
make one model look good. As a developer picking models, you are left guessing. So
I built ModelRank: a conflict-of-interest-free leaderboard that scores open-weight
models with transparent, reproducible signals.

**Why independence matters:**
We do not train or host models. That means we have no incentive to rank our own
higher. The weighting lives in one config file (`config/settings.py`) and anyone
can audit it.

**How scoring works:**
Five dimensions — benchmarks (70%), recency (15%), community (10%), efficiency (5%),
and reproducibility (reserved). Plus ELO head-to-head so you can compare any two
models directly.

**Use it in your workflow:**
- Hover any model id in VS Code and see its score.
- Pull scores into your agents via the LangChain or LlamaIndex tools.
- Embed a free badge in your README.

**Try it:** https://rankmodel.github.io
**Code:** https://github.com/rankmodel/rankmodel.github.io

If this is useful, a star helps an independent project grow. What should we score
next?
