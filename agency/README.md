# ModelRank Agency

A **Paperclip-style company of AI agents** that grows [ModelRank](https://github.com/rankmodel/rankmodel1).
Modeled on [paperclipai/paperclip](https://github.com/paperclipai/paperclip): define a
mission, hire agents with roles + budgets + heartbeats, gate the spend, and let them run.

- `GOAL.md` — mission + north-star metrics.
- `manifest.json` — the org chart: agents (roles, budgets, permissions) and routines
  (schedules, actions, approval gates). Single source of truth.
- `agency.py` — reference runtime (safe by default).
- `activity.jsonl` — append-only log of every action (generated).

## Run it

```sh
python agency/agency.py --list            # show the org chart
python agency/agency.py --dry-run         # plan all routines, mutate nothing
python agency/agency.py --run             # execute enabled, non-gated routines
python agency/agency.py --run --approve   # also clear approval gates
python agency/agency.py --agent cmo       # run only the CMO's routines
python agency/agency.py --budget-report   # monthly spend vs budgets
```

### Agents

| Agent | Title | Budget/mo | Reports to |
|-------|-------|-----------|------------|
| `ceo` | Chief Executive Agent | $0 | — |
| `cmo` | Growth & Distribution Agent | $500 | ceo |
| `devrel` | Developer Relations Agent | $0 | ceo |
| `eng` | Platform Engineering Agent | $0 | ceo |
| `outreach` | Creator Outreach Agent | $100 | cmo |
| `analyst` | Revenue & Analytics Agent | $0 | ceo |

### Routines (heartbeats)

`hourly_badge_sync` · `daily_asset_refresh` · `daily_social_draft` ·
`weekly_newsletter` (gated) · `weekly_outreach` (gated) ·
`weekly_revenue_review` · `monthly_strategy`.

## Lift into real Paperclip

`manifest.json` is already shaped like a Paperclip company definition (agents with
`reports_to` + `budget_usd_per_month` + `permissions`; routines with `schedule` +
`approval_required`). To run it on a real Paperclip server:

1. Stand up Paperclip (`pnpm dev`).
2. Create a company "ModelRank Agency" and import the agents/routines from this
   manifest (map `action` names to Paperclip skills/plugins).
3. Wire `approval_gates` to Paperclip's approval workflow and `budget_hard_stop`
   to its auto-pause behavior.

The lightweight `agency.py` runtime keeps the loops alive here until then.
