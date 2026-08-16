"""Tests for use-case recommendation (scoring/recommend.py + endpoints)."""

import pytest

from data.cache import ModelCache
from scoring.recommend import recommend, available_use_cases


@pytest.fixture
def cache(tmp_path):
    c = ModelCache(db_path=str(tmp_path / "rec.db"))
    c.set_model("A", {"model_id": "A"})
    c.set_model("B", {"model_id": "B"})
    c.set_score(
        "A",
        {"composite": 80, "tier": "A", "breakdown": {"benchmarks": 90, "efficiency": 50, "community": 60, "recency": 70, "reproducibility": 0}},
    )
    c.set_score(
        "B",
        {"composite": 70, "tier": "B", "breakdown": {"benchmarks": 60, "efficiency": 90, "community": 50, "recency": 60, "reproducibility": 0}},
    )
    return c


def test_available_use_cases():
    assert "general" in available_use_cases()
    assert {"coding", "chat", "research", "local", "multilingual"} <= set(available_use_cases())


def test_coding_favors_benchmarks(cache):
    res = recommend("coding", cache, limit=5)
    assert res[0]["model_id"] == "A"  # A has much higher benchmarks


def test_local_favors_efficiency(cache):
    res = recommend("local", cache, limit=5)
    assert res[0]["model_id"] == "B"  # B has much higher efficiency


def test_unknown_use_case_falls_back(cache):
    # unknown -> base weights (benchmarks 0.70, efficiency 0.05, ...) -> A wins
    res = recommend("nonexistent", cache, limit=5)
    assert res[0]["model_id"] == "A"
