# GOAL.md — ModelRank Agency

> If [ModelRank](https://github.com/rankmodel/rankmodel1) is the product, the
> **ModelRank Agency** is the autonomous company that makes it the #1 independent
> open-weight model leaderboard on the internet.

## Mission

Make **ModelRank** the default, trust-first ranking layer that sits *on top of*
HuggingFace, Ollama, and every hub — and turn that reach into dev-paid revenue
via premium badges, without ever charging for the score.

## Success Metrics (North Stars)

1. **Backlinks** — free embeddable badges placed in model READMEs (the viral flywheel).
2. **Ranked models** — coverage of the open-weight long tail (150 → 1,000+).
3. **Dev revenue** — Verified / Featured / Glow / Enterprise conversions.
4. **Share of voice** — ModelRank mentioned wherever people compare models.

## Operating Principles

- **Independence is the product.** We never rank our own models higher because
  we make none. Every agent action must preserve conflict-of-interest-free trust.
- **Free badge forever.** Growth is funded by the free badge's backlink flywheel,
  not by paywalling the score.
- **Agents propose, humans approve spend.** Paid/visibility actions are gated
  behind approval gates. Budget hard-stop auto-pauses any agent that exceeds its
  monthly allowance.
- **Everything is logged.** Every mutating action writes to the activity log so
  the company is inspectable and reversible.

## How This Maps to Paperclip

This directory is a **Paperclip-style company definition** for ModelRank. Paperclip
(<https://github.com/paperclipai/paperclip>) is a control plane for AI-agent
companies: define a goal, hire agents with roles + budgets + heartbeats, and they
run the business. `manifest.json` is this company's org chart; `agency.py` is a
lightweight reference runtime so the loops run today, and the same manifest can be
lifted into a real Paperclip server.
