# Changelog

All notable changes to ModelRank are documented here.

## [Unreleased]
- Renamed repo and site to `rankmodel.github.io` (clean root URL).
- Humanized README and newsletter copy (direct prose, no filler).
- Added favicon, Open Graph / Twitter meta tags, and a generated social preview.
- Weekly newsletter page is now part of the automated deploy.

## [1.0.0] - 2026-08
- Independent 5-dimension scoring: benchmarks, efficiency, community, recency, reproducibility.
- Leaderboard UI (Gradio) with use-case recommender and Judge/ELO tabs.
- REST API: `score`, `leaderboard`, `compare`, `recommend`, `reviews`, `elo-leaderboard`, `judge`.
- Community head-to-head: LLM-judge vibe-check, ELO standings, and a verdict feed.
- Free embeddable badges (score / tier / rank) and shareable Model DNA cards.
- Python client SDK (`api/client.py`) plus LangChain and LlamaIndex tool adapters.
- VS Code extension that shows a model's score and breakdown on hover.
- ModelRank Weekly newsletter (Markdown + X thread + public page).
- ModelRank Agency: a Paperclip-style autonomous growth company.
- 79 passing tests.
