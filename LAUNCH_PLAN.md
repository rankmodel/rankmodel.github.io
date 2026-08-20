# Launch plan: the 48-hour blitz

Goal: **star velocity**, not total stars. Concentrate the push into one window so the
trending signal spikes, then sustain with the weekly newsletter and Discussions.

Pre-launch checklist (do once):
- [ ] Repo social preview uploaded in Settings → `assets/social-preview.png`
- [ ] `README.md` (manifesto + FAQ) merged to `main`
- [ ] Discussions #3/#4/#5 live and pinned
- [ ] `campaign/` posts drafted and ready to paste

## Hour-by-hour

**Hour 0 — Ship the package.**
Merge all Phase 1 changes (README, social preview, methodology). Trigger a site rebuild
so `og:image` points at the new card. Pin a welcome comment: "We're building this in public."

**Hour 2 — Long-form.**
Post the blog (`campaign/blog_post.md`, also `_posts/2026-08-20-why-smaller-models-win.md`)
to DEV.to and Medium with a canonical link back to the GitHub repo. Lead with the
efficiency data point, not the feature list.

**Hour 4 — Show HN.**
Submit `campaign/HN_POST.txt`. Reply to the first comment within the hour. Stay in the
thread; HN rewards responsiveness.

**Hour 6 — Reddit.**
Post `campaign/reddit.md` to r/LocalLLaMA first (highest fit), then r/MachineLearning.
Include a screenshot of the ranking chart. Avoid cross-posting all at once; space them.

**Hour 12 — X thread.**
Post `campaign/X_THREAD.txt` (10 tweets). Pin the thread. Reply to every reply for the
first few hours.

**Hour 24 — Read the room.**
Pull stargazer sources (`gh api repos/rankmodel/rankmodel.github.io/traffic/popular/referrers`).
If Cost/Efficiency is what people click, surface it higher in the README and weekly.
Adjust the pinned comment to the hottest angle.

**Hour 36 — Second wave.**
Cross-post to r/selfhosted and r/artificial. Reply in the HN thread with a "what we
learned" update. Thank new contributors by name in Discussions.

**Hour 48 — Trending check.**
Watch the GitHub Trending page every 5 minutes. If we hit the top 10, push a small
update (a new model or a methodology tweak) and pin: "We're #N on Trending. AMA in the
issues." Keep the momentum with the weekly newsletter.

## Sustain (week 1+)
- Ship `ModelRank Weekly` every week (automated).
- Convert Discussion votes into real weight changes in `config/settings.py`.
- Recruit 2–3 `good first issue` contributors and run all-contributors on them.

## What I will NOT do
Fabricate benchmark numbers. Every claim in the campaign copy is pulled from the real
leaderboard. Credibility is the product; a viral lie is a dead project.
