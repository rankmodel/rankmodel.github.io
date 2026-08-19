"""Tests for the LLM-judge head-to-head vibe-check (scoring/judge.py)."""

import pytest

from data.cache import ModelCache
from scoring.judge import (
    build_judge_prompt,
    parse_verdict,
    judge_comparison,
    run_llm_judge,
)


@pytest.fixture
def cache(tmp_path):
    c = ModelCache(db_path=str(tmp_path / "judge.db"))
    return c


def _seed(cache, mid):
    cache.set_model(
        mid,
        {
            "model_id": mid,
            "params": 7e9,
            "license": "mit",
            "downloads": 1000,
            "likes": 10,
            "pipeline_tag": "text-generation",
            "context_window": 8192,
        },
    )


def test_parse_verdict_tokens():
    assert parse_verdict("A\nbecause it is stronger") == "A"
    assert parse_verdict("B\nmodel b is better") == "B"
    assert parse_verdict("TIE\nneither wins") == "tie"
    assert parse_verdict("") == "tie"


def test_parse_verdict_keywords():
    assert parse_verdict("The better model is B.") == "B"
    # "Verdict: A" -> no token prefix, keyword MODEL A absent, letter tally -> A
    assert parse_verdict("Verdict: A") == "A"


def test_build_prompt_contains_both_models():
    p = build_judge_prompt({"model_id": "modelA"}, {"model_id": "modelB"})
    assert "modelA" in p and "modelB" in p


def test_judge_comparison_uses_injected_call():
    calls = []

    def fake(prompt):
        calls.append(prompt)
        return "B\nmodel b wins"

    verdict, rationale = judge_comparison({"model_id": "A"}, {"model_id": "B"}, llm_call=fake)
    assert verdict == "B"
    assert "model b wins" in rationale
    assert len(calls) == 1


def test_run_llm_judge_records_and_updates_elo(cache):
    _seed(cache, "modelA")
    _seed(cache, "modelB")

    def fake(_prompt):
        return "B\nmodel b is stronger"

    res = run_llm_judge("modelA", "modelB", cache=cache, llm_call=fake)
    assert res is not None
    assert res["verdict"] == "B"
    assert res["model_a"] == "modelA" and res["model_b"] == "modelB"
    # B won -> B rated above A
    assert cache.get_elo_rating("modelB") > cache.get_elo_rating("modelA")


def test_run_llm_judge_missing_model(cache):
    _seed(cache, "modelA")
    assert run_llm_judge("modelA", "ghost", cache=cache, llm_call=lambda p: "A") is None


def test_get_reviews_lists_most_recent_first(cache):
    _seed(cache, "modelA")
    _seed(cache, "modelB")
    cache.record_head_to_head("r1", "modelA", "modelB", "A", "human")
    cache.record_head_to_head("r2", "modelA", "modelB", "B", "llm")
    reviews = cache.get_reviews(limit=10)
    assert len(reviews) == 2
    assert reviews[0]["review_id"] == "r2"  # newest first


def test_get_reviews_filters_by_model_and_type(cache):
    _seed(cache, "modelA")
    _seed(cache, "modelB")
    _seed(cache, "modelC")
    cache.record_head_to_head("r1", "modelA", "modelB", "A", "human")
    cache.record_head_to_head("r2", "modelA", "modelC", "B", "llm")
    assert len(cache.get_reviews(model_id="modelC")) == 1
    assert len(cache.get_reviews(judge_type="llm")) == 1
    assert len(cache.get_reviews(model_id="modelC", judge_type="human")) == 0


def test_get_elo_leaderboard_ranked_desc(cache):
    _seed(cache, "modelA")
    _seed(cache, "modelB")
    cache.record_head_to_head("r1", "modelA", "modelB", "A", "human")
    cache.record_head_to_head("r2", "modelA", "modelB", "A", "human")
    board = cache.get_elo_leaderboard(limit=10)
    assert len(board) == 2
    assert board[0]["model_id"] == "modelA"  # won twice -> highest
    assert board[0]["rating"] > board[1]["rating"]
