# Launch Drafts — honest, ready to post

Every claim below is backed by public data on rankmodel.github.io. No fabricated
screenshots, no fake metrics. Replace `[handle]` before posting.

---

## Show HN

**Title:** Show HN: ModelRank — an independent, open-source leaderboard for HuggingFace models

**Body:**
We got tired of leaderboards published by the same labs that build the models, so
we built one that can't be paid to move a score.

ModelRank ranks 954+ open-weight models on a transparent 5-dimension composite:
benchmarks (70%), recency (15%), community (10%), efficiency (5%), and a reserved
reproducibility slot. Every model gets a free, embeddable SVG badge for its README,
and the full ranking is published as a CSV anyone can audit.

What makes it different:
- The composite score is computed only from public benchmark + HuggingFace data.
- No paid placements for the score, ever (labeled visibility is the only paid option).
- Head-to-head ELO with human + LLM-judge verdicts.
- MIT licensed, scores reproducible in minutes.

We published the raw data so you can fork it and prove us wrong. What would make
this actually useful to you?

Live: https://rankmodel.github.io
Raw data: https://rankmodel.github.io/full_rankings_2026-08-20.csv

---

## Reddit — r/LocalLLaMA

**Title:** We ranked 954 open models by a transparent 5D score — and published the raw CSV so you can fact-check us

**Body:**
Not another "my leaderboard is best" post. We built ModelRank because the
conflict-of-interest in AI benchmarking bugged us: the orgs rating models often
build them.

The scoring is open (benchmarks 70%, recency 15%, community 10%, efficiency 5%),
the weights are in `config/settings.py`, and the full ranking is a CSV you can
download and challenge. Every model gets a free badge.

Genuinely curious: which models do you think we under- or over-rank, and what
benchmark would you add? Link: https://rankmodel.github.io

---

## X / Twitter thread (15 tweets, honest)

1/ Most AI leaderboards are built by the labs they rank. We built one that can't
be paid to move a score. Introducing ModelRank. 🧵
2/ The problem: when the rater owns the model, "independent" is a slogan, not a fact.
3/ Our fix: a composite score from PUBLIC data only. Benchmarks 70%, recency 15%,
community 10%, efficiency 5%.
4/ 954+ open-weight models ranked today. All on HuggingFace.
5/ Every model gets a free, embeddable SVG badge. One line in your README.
6/ The whole ranking is a CSV. Fork it, audit it, prove us wrong. That's the point.
7/ Head-to-head ELO: submit a human or LLM-judge verdict, watch the ladder move.
8/ Efficiency scoring means a 7B can outrank a 70B on score-per-parameter.
9/ We take NO paid placements for the score. Labeled visibility only.
10/ MIT licensed. Reproduce any score in minutes.
11/ Reproducibility dimension is reserved at 0% until we can weight it honestly.
12/ VS Code extension: hover a model id, see its score live.
13/ CI action: fail the build if a model drops below your min score.
14/ Roadmap is public. Vote on it in Discussions.
15/ Independence is the only product. Star if you want more independent tooling:
https://github.com/rankmodel/rankmodel.github.io
