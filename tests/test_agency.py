"""Tests for the ModelRank Agency manifest and reference runtime."""

import json
from pathlib import Path

import pytest

AGENCY_DIR = Path(__file__).resolve().parent.parent / "agency"
MANIFEST = AGENCY_DIR / "manifest.json"


def test_manifest_is_valid_json():
    data = json.loads(MANIFEST.read_text())
    assert data["company"]
    assert isinstance(data["agents"], list)
    assert isinstance(data["routines"], list)


def test_every_routine_references_a_known_agent():
    data = json.loads(MANIFEST.read_text())
    agent_ids = {a["id"] for a in data["agents"]}
    for r in data["routines"]:
        assert r["agent_id"] in agent_ids, f"routine {r['id']} -> unknown agent {r['agent_id']}"


def test_agent_budgets_are_numeric_and_hard_stop_present():
    data = json.loads(MANIFEST.read_text())
    assert data.get("budget_hard_stop") is True
    for a in data["agents"]:
        assert isinstance(a["budget_usd_per_month"], (int, float))


def test_routine_actions_are_wired_in_runtime():
    import importlib.util

    spec = importlib.util.spec_from_file_location("agency_runtime", AGENCY_DIR / "agency.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    data = json.loads(MANIFEST.read_text())
    for r in data["routines"]:
        assert r["action"] in mod.ACTIONS, f"action {r['action']} not wired in agency.py"


def test_dry_run_plans_without_mutating():
    import importlib.util
    import io
    from contextlib import redirect_stdout

    spec = importlib.util.spec_from_file_location("agency_runtime", AGENCY_DIR / "agency.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.main([])
    assert rc == 0
    assert "DRY-RUN" in buf.getvalue()
