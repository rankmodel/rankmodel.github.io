# AGENTS.md — ModelRank Agency

Guidance for human and AI contributors working on the ModelRank Agency.

## 1. Purpose

The ModelRank Agency is a control plane for the autonomous "company" that grows
ModelRank. Read `GOAL.md` first, then `manifest.json` to see the current org chart
and routines.

## 2. Repo Map (agency/)

- `GOAL.md` — mission, north-star metrics, operating principles.
- `manifest.json` — the org chart: agents (roles, budgets, permissions) + routines
  (schedules, actions, approval gates). This is the single source of truth.
- `agency.py` — reference runtime. Loads the manifest, executes routines, enforces
  budgets, and writes the activity log. Safe by default (`--dry-run`).
- `activity.jsonl` — append-only log of every executed/blocked routine (generated).
- `README.md` — how to run and how to lift this into Paperclip.

## 3. Core Rules

1. **Company-scoped.** Every agent and routine belongs to the ModelRank Agency;
   keep changes inside `agency/`.
2. **Manifest is the contract.** To add/change an agent or routine, edit
   `manifest.json`. Keep `agency.py` in sync with the action names it references.
3. **Control-plane invariants.**
   - Approval gates for governed (paid / public) actions.
   - Budget hard-stop: an agent pauses when its monthly spend is exceeded.
   - Activity logging for every mutating action.
4. **Additive updates.** Prefer extending the org chart over rewriting it.
5. **No secrets.** Agents must never read `.env` or API keys into logs. Credentials
   are injected at runtime only.

## 4. Verification

```sh
python agency/agency.py --dry-run          # print the plan, log nothing mutating
python -m pytest tests/test_agency.py -q   # manifest + runtime sanity checks
```

## 5. Definition of Done

A routine is done when: it is declared in `manifest.json`, its action is wired in
`agency.py`, it respects its approval gate and budget, and it is covered by
`tests/test_agency.py`.
