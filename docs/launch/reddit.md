# Reddit posts

Post each to the relevant subreddit, spaced across the launch window. Lead with the
problem, not the product. Always end with a star CTA.

## r/LocalLLaMA
**Title:** I built an independent leaderboard for open-weight models (no lab owns it)

Most rankings are run by the people shipping the models, so the incentives are
off. ModelRank scores open-weight models on benchmarks, efficiency, community,
recency, and reproducibility, with head-to-head ELO you can vote on. Badges are
free to embed.

- Live: https://rankmodel.github.io
- Code: https://github.com/rankmodel/rankmodel.github.io

Would love feedback on the weighting. What should count more: efficiency or
community signal?

## r/MachineLearning
**Title:** [Project] ModelRank: transparent, reproducible scoring for open LLMs

A conflict-of-interest-free leaderboard with a documented methodology, an open
Python SDK, and agent tooling for LangChain and LlamaIndex. Scores are normalized
against population bounds so they are comparable across the whole catalog.

## r/selfhosted
**Title:** Self-hostable AI model leaderboard with free embeddable badges

ModelRank runs locally (FastAPI + Gradio), seeds from HuggingFace, and generates
SVG badges you can drop into any README. Good for tracking your own fine-tunes.

## r/artificial
**Title:** Why we need leaderboards that no model vendor controls

Short opinion post linking to the methodology and the live site. Ask the community
what a trustworthy ranking should measure.
