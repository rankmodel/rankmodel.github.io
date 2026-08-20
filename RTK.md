# RTK (Rules, Tech, Knowledge)

## RULES (Non-negotiable conventions)
- **Formatting**: `black`, `ruff`, and `isort`. Type hints are strictly enforced.
- **Security**: No secrets in commits. Use `.env`.
- **TDD**: Tests must be written before core logic updates.
- **Atomic Commits**: Conventional Commits (feat, fix, chore, docs).
- **Destructive Operations**: Always prompt before DB migrations or mass deletions.

## TECH (Stack & ADRs)
- **Python 3.10+**: Core runtime (FastAPI, Gradio).
- **SQLite**: Primary database (WAL mode) for zero-config persistence.
- **HuggingFace API**: Model registry and benchmark sourcing.
- **Gradio**: Interactive UI for leaderboard and model judging.
- **FastAPI**: REST endpoints for headless integrations and ELO scoring.

### Architecture Decision Records (ADR)
- **ADR-001**: Used SQLite over Postgres to keep the project serverless and embeddable via GitHub Pages + CI/CD.
- **ADR-002**: Pure Python dependencies (avoiding heavy node_modules) to maintain simplicity.

## KNOWLEDGE (Domain & Gotchas)
- **Domain Glossary**:
  - `Composite Score`: The 5D weighted score (70% benchmarks, 15% recency, 10% community, 5% efficiency).
  - `ELO`: Head-to-head performance derived from human and LLM judges.
  - `Model DNA`: Radial representation of model performance.
- **Known Gotchas**:
  - HuggingFace API rate limits: Ensure `HF_TOKEN` is used when fetching >50 models.
  - SQLite locking: `database is locked` can occur during heavy concurrent API writes.
- **Environment Variables**:
  - `HF_TOKEN=<set-me>`
  - `JUDGE_API_KEY=<set-me>`
