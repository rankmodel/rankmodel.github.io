# ModelRank — Project Definition (Spec / PRD)

> Single source of truth for **what ModelRank is, how it is built, and every entity
> that makes up the project** — both the *product* (the independent AI-model
> leaderboard) and the *agency* (the autonomous agent "company" that grows it).
>
> Grounded in the current codebase (`/Users/shrey/Downloads/modelrank`): `data/schema.sql`,
> `config/settings.py`, `config/pricing.py`, `main.py`, `agency/`. Where the running
> code and the marketing narrative disagree, the discrepancy is called out in
> §11 (Open Questions).

---

## 1. Overview

**ModelRank** is an independent, conflict-of-interest-free leaderboard for open-weight
AI models. It does not train or host models, so it has zero incentive to rank any
model higher than its measured quality. It sits *on top of* HuggingFace, Ollama and
every hub and answers one question: *"which AI model should I actually use?"*

Two coupled layers make up the project:

| Layer | Purpose | Primary code |
|-------|---------|--------------|
| **Product** | Scrape public signals → compute a transparent 5D score + ELO → publish a leaderboard, embeddable badges, REST API, and a Gradio UI. | `scoring/`, `data/`, `api/`, `badges/`, `ui/`, `config/` |
| **Agency** | A Paperclip-style company of AI agents that keeps data fresh, generates content, recruits creators, and converts free-badge reach into dev-paid revenue. | `agency/` (manifest + runtime) + a live Paperclip server |

**Mission.** Make "which model should I use?" a solved question, with scoring no
vendor can buy, rig, or own. Independence, transparency, and "free badge forever"
are non-negotiable product principles.

**North-star metrics.** (1) Backlinks from free embeddable badges, (2) ranked-model
coverage (150 → 1,000+), (3) dev revenue (Verified / Featured / Glow / Enterprise),
(4) share of voice wherever models are compared.

---

## 2. System Architecture & Components

```
main.py                 CLI: api | ui | score | leaderboard
api/                    FastAPI REST (server.py) + premium (premium.py)  → ~10 endpoints
scoring/                composite engine, ELO, benchmarks, efficiency, community, recency, reproducibility
data/                   HFDataFetcher, ModelCache (SQLite/WAL), schema.sql, NotebookLM integration
badges/                 SVG + premium (glow/featured) generators, templates
config/                 settings.py (scoring weights, tiers, achievements), pricing.py (plans, products)
scripts/                static asset + outreach generators
ui/app.py               Gradio leaderboard
ai-services/            auxiliary agent/context services (monitor, context_engine, agent_cli)
agency/                 Paperclip-style growth company: GOAL.md, manifest.json, agency.py, activity.jsonl
static_output/          GitHub Pages CDN (leaderboard HTML, badges, pages)
```

**Data flow.** `HFDataFetcher` pulls model metadata + eval results from the HuggingFace
API → `scoring/engine.compute_composite_score` produces a `Score` → cached in SQLite
(`models`, `eval_results`, `scores`) → surfaced via API / UI / badge generators /
static-site generators. The Agency regenerates assets, drafts posts, and publishes on
heartbeat schedules.

---

## 3. Scoring Methodology (the core IP)

### 3.1 Composite 5D score (0–100)

> ⚠️ **Discrepancy.** `config/settings.py` (`SCORING_WEIGHTS`) and `README.md` state
> different weights. The spec records the *implemented* values; see §11.

| Dimension | Implemented weight (`settings.py`) | Documented (`README.md`) | Measures |
|-----------|-----------------------------------|--------------------------|----------|
| 🧠 Benchmarks | **0.70** | 0.40 | MMLU-Pro, GPQA, HLE, GSM8K, HumanEval (+8 more) |
| 🕐 Recency | **0.15** | 0.10 (Freshness) | 180-day half-life decay |
| 🔥 Community | **0.10** | 0.20 | Downloads + likes + trending rank |
| ⚡ Efficiency | **0.05** | 0.20 | Score per billion params (rewards small models) |
| ✅ Reproducibility | **0.00** | 0.10 (Verified) | Source credibility + benchmark diversity |

### 3.2 Benchmark weights (inside the Benchmarks dimension)

| Benchmark | Weight |
|-----------|--------|
| MMLU-Pro | 0.25 |
| GPQA | 0.20 |
| HLE | 0.20 |
| GSM8K | 0.20 |
| HumanEval | 0.15 |

### 3.3 Head-to-head ELO

`P(A > B) = 1 / (1 + 10^((ELO_B − ELO_A) / 400))` — win probabilities between any two
models, independent of the composite score.

### 3.4 Tiers

Numeric composite → letter tier (score ≥ threshold): **S ≥ 90, A ≥ 80, B ≥ 70,
C ≥ 60, D < 60.** Tier colors: S `#a855f7`, A `#3b82f6`, B `#22c55e`, C `#eab308`,
D `#ef4444`.

### 3.5 Achievements

Badges/medals awarded to a model when it meets a condition (see `ACHIEVEMENT_TYPES`):
`trending_top10`, `efficiency_king`, `community_favorite`, `benchmark_champion`,
`abliterated`, `quantized_ready`, `top_1`, `top_3`, `top_10`.

---

## 4. Domain Data Model — Entities

This is the canonical list of **product entities**. Persisted entities map to
`data/schema.sql`; derived/designed entities are marked *(designed)* where not yet
materialized in code.

### 4.1 `Model`
The unit being ranked.
- **`model_id`** (PK, TEXT) — HF path, e.g. `meta-llama/Llama-3.1-8B`.
- **`data`** (TEXT/JSON) — normalized model metadata (params, license, context window,
  downloads, likes, trending rank, VRAM tier, multilingual, safety flags, …).
- **`timestamp`** (INT) — Unix epoch when cached (TTL 24h for metadata).
- *Relations:* 1 `Model` → 1 `Score`, 0..* `EvalResult`, 0..* `Achievement`,
  0..* `Badge`, 0..* `Review` (as A or B).

### 4.2 `EvalResult`
A single benchmark observation for a model.
- **`model_id`** (PK, TEXT).
- **`results`** (TEXT/JSON) — array of eval-result objects (benchmark_id, raw score,
  normalized score).
- **`timestamp`** (INT) — cached (TTL 6h).
- *Relations:* belongs to one `Model`; feeds the Benchmarks dimension of `Score`.

### 4.3 `Score`
The computed ranking record for a model (the thing the leaderboard sorts on).
- **`model_id`** (PK, TEXT).
- **`score_data`** (TEXT/JSON) — full score dict: `composite` (0–100), `tier`,
  `breakdown` (per-dimension scores), `elo`, extended signals (context window, VRAM
  tier, license, multilingual, safety, momentum, …), optional `global_rank`.
- **`timestamp`** (INT).
- *Relations:* belongs to one `Model`; derived from `EvalResult` + `Model.data`.

### 4.4 `ScoringDimension` *(designed/config)*
A weighted component of the composite. Fields: `key` (benchmarks|efficiency|community|
recency|reproducibility), `weight`, `color`. Defined in `config/settings.py`.

### 4.5 `Benchmark` *(designed/config)*
A named evaluation. Fields: `benchmark_id`, `weight` (within Benchmarks dimension),
`source`. Defined in `config/settings.py` (`BENCHMARK_WEIGHTS`).

### 4.6 `Achievement`
Awarded medal for a model.
- **`model_id`** (PK part), **`achievement_type`** (PK part), **`awarded_at`** (INT).
- *Relations:* many-to-one `Model`.

### 4.7 `Tier` *(designed/config)*
Score band. Fields: `letter` (S/A/B/C/D), `min_score`, `color`. Defined in
`config/settings.py` (`TIERS`).

### 4.8 `Leaderboard` / `LeaderboardEntry` *(derived)*
Not a stored table (computed from `Score` + `Model`). Entry fields: `rank`,
`model_id`, `tier`, `composite`, `downloads`. `leaderboard_bounds` *is* stored:
`benchmark_id` (PK), `min_score`, `max_score`, `total_models`, `timestamp` — used to
normalize benchmark scores across the population.

### 4.9 `Badge`
Embeddable SVG (the viral growth engine). Fields: `model_id`, `type`
(score|tier|rank|dimension|achievement|animated|featured), `style`
(flat|default|glow|minimal|premium), `plan` (gating), `verified` flag. Generated by
`badges/generator.py` + `badges/premium_generator.py`. Every badge is a backlink to
the leaderboard.

### 4.10 `Plan` (Subscription)
A recurring paid tier. Fields: `key` (free|pro|featured|enterprise), `name`,
`price_monthly`, `price_annual`, `api_calls_per_day`, `badge_types[]`, `badge_styles[]`,
`leaderboard_placement`, `research_reports`, `compare_models`, `history_days`,
`priority_indexing`, `verified_checkmark`, `custom_branding`, `webhook_alerts`,
`csv_export`, `white_label`, `sla`. Defined in `config/pricing.py` (`PLANS`).
*(Free badge stays free forever; monetization is visibility/trust, never the score.)*

### 4.11 `Product` (one-off)
Non-subscription purchases. Fields: `key`, `name`, `price`, `description`,
`delivery`. Defined in `config/pricing.py` (`PRODUCTS`): `research_report` ($49),
`featured_week` ($49), `featured_month` ($149), `org_certification` ($999/yr).

### 4.12 `User` / `Account` *(designed)*
A human or org that authenticates and holds a `Plan`. Fields: `user_id`, `email`,
`plan_key`, `created_at`, `stripe_customer_id`. Not yet materialized in code.

### 4.13 `APIKey` / `RateLimit` *(designed)*
Programmatic access credential + limiter. Fields: `key`, `user_id`, `plan_key`,
`per_day`, `per_minute`. Limits per plan in `config/pricing.py` (`API_LIMITS`):
free 50/day·5/min, pro 1000/day·60/min, featured 5000/day·200/min, enterprise
unlimited.

### 4.14 `Organization` *(designed)*
A HF org / lab enrolled in `org_certification`. Fields: `org_id`, `name`,
`certified_until`, `models[]`. Powers the annual certification product.

### 4.15 `Review` / `Comparison` *(designed — "H2H")*
A head-to-head judgment between two models (human or LLM-judge), feeding ELO and the
"LLM-Judge Vibe-Check" research. Fields: `review_id`, `model_a`, `model_b`,
`verdict` (A|B|tie), `judge_type` (human|llm), `judge_id`, `created_at`. Referenced by
goal PALA-7 (Community Scoring + LLM-Judge design). **Not yet implemented in code.**

### 4.16 `Judge` *(designed)*
An LLM used to vibe-check / compare models. Fields: `judge_id`, `model`, `prompt_set`,
`calibration`. Powers `Review` generation.

### 4.17 `ActivityLog` / `Routine` run *(agency)*
Append-only record of every agency action. Fields: `ts`, `agent`, `routine`,
`action`, `status` (executed|blocked), `details`. Stored as `agency/activity.jsonl`.

---

## 5. Monetization Model

Open-core hybrid. The **free badge is the growth flywheel** (every placement is a
backlink). Revenue solves real problems, never gates the score:

| Stream | Entity | Price |
|--------|--------|-------|
| Verified Pro Badges | `Plan.pro` / `Badge` | $29/mo |
| Featured Leaderboard | `Plan.featured` / `Product.featured_*` | $99/mo or $49–149 one-off |
| Research Reports (NotebookLM) | `Product.research_report` | $49/report |
| API Access Tiers | `Plan` + `APIKey` | Free / $29 / $99 / Enterprise |
| Org Certification | `Product.org_certification` + `Organization` | $999/yr |

Target segments (from `pricing.py`): Independent Model Creators → `pro`; AI Startups →
`featured`; AI Labs / MLOps → `enterprise`.

---

## 6. The ModelRank Agency (autonomous company) — entities

A Paperclip-style control plane. Source of truth: `agency/manifest.json`
(agents + routines), `agency/GOAL.md` (mission), `agency/agency.py` (reference
runtime). Can be lifted onto a live Paperclip server (as done in this engagement).

### 6.1 `Company`
The agency itself — "ModelRank Agency". Owns all agents, routines, goals, budgets.

### 6.2 `Agent`
A role with a budget and reporting line. Core manifest agents:

| Agent key | Title | Budget/mo | Reports to |
|-----------|-------|-----------|------------|
| `ceo` | Chief Executive Agent | $0 | — |
| `cmo` | Growth & Distribution Agent | $500 | ceo |
| `devrel` | Developer Relations Agent | $0 | ceo |
| `eng` | Platform Engineering Agent | $0 | ceo |
| `outreach` | Creator Outreach Agent | $100 | cmo |
| `analyst` | Revenue & Analytics Agent | $0 | ceo |

Plus the execution agents stood up in this engagement (run on the live Paperclip
server against the `nine/ag/claude-sonnet-4-6` provider): CEO, Step1–Step5 (build
phases), Research, Docs, **Marketing/GTM Lead** (`b3b496b4`), **Community/Scoring
Researcher** (`f8b09542`, PALA-7), **H2H UX Researcher** (`726a7993`, *no task
assigned*).

### 6.3 `Routine` (heartbeat)
Scheduled agent loop. `schedule` (hourly/daily/weekly/monthly), `action`,
`approval_required` (gate). Manifest routines: `hourly_badge_sync`,
`daily_asset_refresh`, `daily_social_draft`, `weekly_newsletter` (gated),
`weekly_outreach` (gated), `weekly_revenue_review`, `monthly_strategy`.

### 6.4 `Goal`
A strategic objective the company pursues (15 created for the 2.0 Master Plan).
Top-level parent goal id `06516b64-728d-4cf6-ba72-b24939d17b63`.

### 6.5 `Issue` / `Task` (PALA-*)
A unit of work assigned to an agent. Issues created: `PALA-1` … `PALA-13` (plus
meta "Review silent active run" issues assigned to CEO). Example mapping:
PALA-2/3/4/5/6 → Marketing/GTM Lead; PALA-7 → Community/Scoring Researcher.

### 6.6 `Run`
A single execution of an agent on a task (Paperclip run). Fields: `run_id`,
`agent_id`, `task_id`, `status` (running|succeeded|failed|cancelled), `log`.

### 6.7 `Budget` / `ApprovalGate`
`budget_usd_per_month` per agent; `budget_hard_stop` auto-pauses on exceed; governed
(paid/public) actions require `approval_required` clearance.

---

## 7. ModelRank 2.0 Master Plan — Phases & Goals

The build is organized into **5 phases** executed by the agent company. (Phase
boundaries and goal IDs are the working plan; the 15 goals decompose into the
PALA-* issues.)

- **Phase 1 — Foundation.** Scoring engine, data pipeline, leaderboard, badges.
  *(Delivered by Step1–Step5 agents — succeeded.)*
- **Phase 2 — Growth & Content.** Marketing/SEO content + strategy, DevRel/outreach.
  *(PALA-2/3/5/6 → Marketing; PALA-7 → Community — in progress.)*
- **Phase 3 — Premium & UX.** Podcasts, Find-My-Model quiz, premium UI.
  *(PALA-4, etc. — blocked, pending Phase 1/2.)*
- **Phase 4 — Monetization.** Stripe Pro badges + PR bot. *(PALA-3 Monetization.)*
- **Phase 5 — Community & Intelligence.** Community scoring + LLM-judge vibe-check,
  H2H comparisons. *(PALA-7 + H2H UX Researcher.)*

Status as of this writing: Phase 1 complete; Community (PALA-7) complete; Marketing
partial (PALA-2/PALA-3 pending re-run after a quota blackout); H2H researcher has no
assigned task yet.

---

## 8. API Surface (entities as endpoints)

`api/server.py` (FastAPI, port 8000) exposes ~10 endpoints, e.g.:
`GET /score/{model_id}`, `GET /leaderboard`, `GET /badge/{model_id}`,
`GET /models`, `POST /compare`, premium endpoints in `api/premium.py`
(`/subscribe`, `/verify`, `/featured`, research-report, webhook alerts). No API key
required to *use* ModelRank; `HF_TOKEN` only raises rate limits. A zero-dependency
Python SDK (`api/client.py` → `ModelRankClient`) wraps every endpoint for reuse by
integrations (LangChain/LlamaIndex tool, VS Code hover provider).

---

## 9. Roadmap

- [x] 150+ seeded models, 5D scoring, ELO, badges, pricing
- [x] Shareable "Model DNA" cards (Spotify-Wrapped for models)
- [x] ModelRank Agency (Paperclip-style autonomous company)
- [~] Interactive "Best model for my use case" quiz — **recommendation engine built** (`scoring/recommend.py` + `GET /recommend` + `python main.py recommend`); UI quiz shell still pending
- [x] Community scoring + LLM-judge vibe-check (PALA-7 / H2H) — `scoring/judge.py` + `reviews`/`elo_ratings` data layer; Gradio verdict feed + ELO standings board; `GET /reviews` + `GET /elo-leaderboard` endpoints; `static_output/head-to-head.html` community page + `head-to-head.json`
- [x] VS Code extension (hover a model name → see its score) — `vscode-extension/` hover provider built on `ModelRankClient` (`GET /score/{model_id}`)
- [x] LangChain / LlamaIndex integration — `integrations/` exposes agent tools (`modelrank_score`, `modelrank_compare`, `modelrank_recommend`, `modelrank_head_to_head`) wrapping `ModelRankClient`; adapters build LangChain `Tool` / LlamaIndex `FunctionTool` objects lazily (optional deps)
- [x] Weekly automated newsletter (`scripts/generate_weekly.py`, wired to the `weekly_newsletter` agency routine; emits `static_output/weekly.html` + `weekly.json`)
- [ ] Weekly podcast episode (audio) — optional
- [ ] Community scoring + LLM-judge vibe-check (PALA-7 / H2H)

---

## 10. Operating Constraints (from this engagement)

- **LLM backend.** Agents run on the local **9router** OpenAI-compatible proxy
  (`localhost:20128/v1`, key `sk-b92540e6eaea968b-17bu8i-…`), provider
  `nine/ag/claude-sonnet-4-6` (antigravity/Claude). A queueing proxy
  (`/Users/shrey/.paperclip/queue-proxy.js`, port 20129) **serializes** requests per
  provider and **retries on 429 quota** so free-tier limits don't starve agents.
- **Dispatch rule.** An active agent only auto-dispatches a `Run` for a task in
  `todo`/`in_progress` state; `blocked` tasks never run. Re-triggering a failed run
  requires toggling the task status (e.g. `blocked → todo`).
- **Quota.** The free antigravity account has a per-window usage quota (resets
  ~every 28 min); running many agents exhausts it — the queue proxy absorbs this.

## 11. Open Questions / Inconsistencies

1. **Scoring weights — reconciled.** `README.md` now documents 70/15/10/5/0 across
    Benchmarks/Recency/Community/Efficiency/Reproducibility (matching
    `config/settings.py`). The Gradio About tab (`ui/app.py`) and the static
    methodology cards (`index.html` + `methodology.html`) were updated to the same
    values; the stale "40/20/20/10/10" displays are gone.
2. **Community scoring & H2H — implemented.** `scoring/judge.py` adds
   `run_llm_judge()`, which fetches two cached models, asks an impartial LLM judge
   (OpenAI-compatible `/chat/completions`, endpoint configurable via
   `JUDGE_API_BASE`/`JUDGE_API_KEY`/`JUDGE_MODEL`; the LLM call is injectable for
   tests), parses the `A`/`B`/`tie` verdict, and persists it through
   `ModelCache.record_head_to_head` (feeding ELO). 6 new tests; 45/45 pass.
3. **H2H UX Researcher — now assigned.** The `h2h_researcher` agent is registered in
    `agency/manifest.json` (corresponds to the live Paperclip agent `726a7993`),
    owning the community scoring + LLM-judge vibe-check surface. Implemented in code:
    `cache.get_reviews()` / `cache.get_elo_leaderboard()` + `GET /reviews` +
    `GET /elo-leaderboard` + the "⚖️ Judge & ELO" tab's verdict feed and ELO standings
    board in `ui/app.py`.
4. **User/Account/APIKey/Organization — data layer implemented.** `data/schema.sql`
   now has `users`, `api_keys`, `organizations`; `ModelCache` adds
   `create/get_user`, API-key create/validate/revoke (`get_api_key_plan`), and
   org create/certify/get. 3 new tests; 48/48 pass. Remaining: the surrounding
   auth flows + Stripe webhooks that consume these tables are not yet wired.
5. **Benchmark count — reconciled.** The hero stat in `index.html` said "15 Benchmarks";
    corrected to "5 Benchmarks" to match `BENCHMARK_WEIGHTS` (MMLU-Pro, GPQA, HLE,
    GSM8K, HumanEval). The README's methodology table already lists these 5.
6. **ELO storage — implemented.** `data/schema.sql` now has `elo_ratings`
   (rating + W/L/D + match count) and `reviews` (match history); `scoring/elo.py`
   holds the pure ELO math (`expected_score`, `update_ratings`) and
   `ModelCache.get_elo_rating` / `record_head_to_head` persist ratings. Verified
   against the standard formula; 39/39 tests pass.

---

*Maintained alongside the codebase. Update when entities are added, renamed, or
their fields change.*
