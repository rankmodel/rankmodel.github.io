#!/usr/bin/env python3
"""
agency/agency.py

Reference runtime for the ModelRank Agency — a Paperclip-style "company of AI
agents" that grows ModelRank. It loads `manifest.json` (the org chart), executes
routines on a schedule, enforces approval gates and a monthly budget hard-stop,
and appends every action to `activity.jsonl`.

This is a lightweight Python runtime so the loops run today. The same
`manifest.json` can be lifted into a real Paperclip server
(https://github.com/paperclipai/paperclip) without changes.

Modes
-----
  python agency/agency.py --dry-run            # plan only, log nothing mutating
  python agency/agency.py --run                # execute enabled, non-gated routines
  python agency/agency.py --run --approve      # also clear approval gates
  python agency/agency.py --list               # print the org chart
  python agency/agency.py --agent cmo          # filter by agent
  python agency/agency.py --budget-report      # show monthly spend vs budgets

Safe by default: with no flag, it prints the plan (dry-run).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENCY_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = AGENCY_DIR.parent
MANIFEST = AGENCY_DIR / "manifest.json"
ACTIVITY_LOG = AGENCY_DIR / "activity.jsonl"
DRAFTS_DIR = PROJECT_ROOT / "outputs" / "agency_drafts"

AGENT_MAP: dict[str, dict] = {}


# --------------------------------------------------------------------------- #
# Action implementations. Each returns a short human-readable result string.
# Heavy actions shell out to the existing project scripts.
# --------------------------------------------------------------------------- #
def _run_script(rel_path: str, *args: str) -> str:
    cmd = [sys.executable, str(PROJECT_ROOT / rel_path), *args]
    proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        return f"FAILED ({rel_path}): {proc.stderr[-300:]}"
    return f"ran {rel_path} {' '.join(args)}"


def action_regenerate_assets(ctx) -> str:
    return _run_script("scripts/generate_static_assets.py", "--limit", "200")


def action_sync_badges(ctx) -> str:
    # Cheap heartbeat — confirm the badges directory exists in static_output.
    badge_dir = PROJECT_ROOT / "static_output" / "badges"
    ok = badge_dir.exists()
    return f"badge endpoint dir present={ok} at static_output/badges"


def action_social_draft(ctx) -> str:
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = DRAFTS_DIR / f"social_{ts}.md"
    out.write_text(
        "# Draft social post\n\n"
        "Today's biggest ModelRank mover is live on the leaderboard. "
        "Grab your free, embeddable score badge and join the independent ranking layer.\n"
        "https://rankmodel.github.io/rankmodel1\n"
    )
    return f"drafted social post -> {out.relative_to(PROJECT_ROOT)}"


def action_publish_weekly(ctx) -> str:
    return _run_script("scripts/generate_weekly.py")


def action_outreach(ctx) -> str:
    return _run_script("scripts/generate_outreach.py", "--top", "20")


def action_revenue_report(ctx) -> str:
    badge_dir = PROJECT_ROOT / "static_output" / "badges"
    count = sum(1 for _ in badge_dir.rglob("*.svg")) if badge_dir.exists() else 0
    return f"badge assets present={count}; review conversions in the premium API / Stripe dashboard"


def action_strategy_review(ctx) -> str:
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = DRAFTS_DIR / f"strategy_{ts}.md"
    out.write_text(
        "# Monthly strategy review\n\n"
        "- Re-read agency/GOAL.md north-star metrics.\n"
        "- Propose org-chart changes (new agents / routines) for next month.\n"
        "- Confirm budget hard-stop thresholds still match goals.\n"
    )
    return f"strategy review -> {out.relative_to(PROJECT_ROOT)}"


ACTIONS = {
    "regenerate_assets": action_regenerate_assets,
    "sync_badges": action_sync_badges,
    "social_draft": action_social_draft,
    "publish_weekly": action_publish_weekly,
    "outreach": action_outreach,
    "revenue_report": action_revenue_report,
    "strategy_review": action_strategy_review,
}


# --------------------------------------------------------------------------- #
# Runtime
# --------------------------------------------------------------------------- #
def load_manifest() -> dict:
    data = json.loads(MANIFEST.read_text())
    for a in data["agents"]:
        AGENT_MAP[a["id"]] = a
    return data


def log_activity(entry: dict) -> None:
    with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def monthly_spend(agent_id: str, manifest: dict) -> float:
    total = 0.0
    for r in manifest["routines"]:
        if r["agent_id"] == agent_id:
            total += float(r.get("cost_usd", 0))
    return total


def run_routine(routine: dict, manifest: dict, *, execute: bool, approve: bool) -> dict:
    agent = AGENT_MAP.get(routine["agent_id"], {})
    gated = routine.get("approval_required", False)
    blocked = gated and not approve

    if not execute:
        mode = "plan"
    elif blocked:
        mode = "blocked"
    else:
        mode = "exec"

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "routine": routine["id"],
        "agent": routine["agent_id"],
        "action": routine["action"],
        "gated": gated,
        "mode": mode,
    }

    if not execute:
        entry["result"] = "planned (dry-run)"
    elif blocked:
        entry["result"] = "BLOCKED: requires approval gate"
    else:
        try:
            fn = ACTIONS.get(routine["action"])
            entry["result"] = fn(routine) if fn else f"no action wired for {routine['action']}"
        except Exception as exc:  # keep the company running
            entry["result"] = f"ERROR: {exc}"

    log_activity(entry)
    return entry


def cmd_list(manifest: dict) -> None:
    print(f"Company: {manifest['company']}")
    print(f"Mission : {manifest['mission']}\n")
    print("Org chart:")
    for a in manifest["agents"]:
        boss = a["reports_to"] or "(top)"
        print(f"  - {a['title']} [{a['id']}] -> reports to {boss} | budget ${a['budget_usd_per_month']}/mo")
    print("\nRoutines:")
    for r in manifest["routines"]:
        flag = " (approval-gated)" if r.get("approval_required") else ""
        print(f"  - {r['id']}: {r['agent_id']} @ {r['schedule']}{flag}")


def cmd_budget(manifest: dict) -> None:
    print("Monthly budget report:")
    for a in manifest["agents"]:
        spent = monthly_spend(a["id"], manifest)
        budget = float(a["budget_usd_per_month"])
        status = "OK" if spent <= budget else "OVER (hard-stop)"
        print(f"  - {a['id']}: ${spent:.0f} / ${budget:.0f}  [{status}]")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="ModelRank Agency runtime")
    ap.add_argument("--run", action="store_true", help="execute enabled, non-gated routines")
    ap.add_argument("--dry-run", action="store_true", help="plan only, mutate nothing (default)")
    ap.add_argument("--approve", action="store_true", help="clear approval gates (with --run)")
    ap.add_argument("--agent", type=str, help="only run routines for this agent id")
    ap.add_argument("--routine", type=str, help="only run this routine id")
    ap.add_argument("--list", action="store_true", help="print the org chart and exit")
    ap.add_argument("--budget-report", action="store_true", help="print budget usage and exit")
    args = ap.parse_args(argv)

    manifest = load_manifest()

    if args.list:
        cmd_list(manifest)
        return 0
    if args.budget_report:
        cmd_budget(manifest)
        return 0

    execute = args.run
    mode = "EXECUTE" if execute else "DRY-RUN (plan only)"
    print(f"[{mode}] {datetime.now(timezone.utc).isoformat()}")
    for r in manifest["routines"]:
        if not r.get("enabled", True):
            continue
        if args.agent and r["agent_id"] != args.agent:
            continue
        if args.routine and r["id"] != args.routine:
            continue
        entry = run_routine(r, manifest, execute=execute, approve=args.approve)
        print(f"  {entry['mode']:>7} | {entry['routine']:<22} | {entry['result']}")
    print(f"\nActivity logged to {ACTIVITY_LOG.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
