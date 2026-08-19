"""Tests for the judge / ELO REST endpoints in api/server.py."""

import pytest
from fastapi.testclient import TestClient

import api.server as s
from data.cache import ModelCache


@pytest.fixture
def client(tmp_path):
    db = str(tmp_path / "api.db")
    c = ModelCache(db_path=db)
    c.set_model("A", {"model_id": "A", "params": 7e9})
    c.set_model("B", {"model_id": "B", "params": 13e9})
    with TestClient(s.app) as client:
        s.cache = c  # override the lifespan-created global with an isolated DB
        yield client


def test_judge_human_endpoint(client):
    r = client.post("/judge/human", json={"model_a": "A", "model_b": "B", "verdict": "A"})
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] == "A"
    assert body["elo"]["a"] > body["elo"]["b"]


def test_judge_human_invalid_verdict(client):
    r = client.post("/judge/human", json={"model_a": "A", "model_b": "B", "verdict": "X"})
    assert r.status_code == 400


def test_elo_endpoint(client):
    client.post("/judge/human", json={"model_a": "A", "model_b": "B", "verdict": "B"})
    e = client.get("/elo/A")
    assert e.status_code == 200
    data = e.json()
    assert data["matches"] == 1
    assert data["rating"] < 1500  # A lost -> rating drops below default


def test_judge_llm_endpoint(client, monkeypatch):
    def fake(model_a, model_b, cache=None, llm_call=None, judge_id=None):
        return {
            "review_id": "x",
            "verdict": "A",
            "rationale": "A is better",
            "model_a": model_a,
            "model_b": model_b,
        }

    monkeypatch.setattr(s, "run_llm_judge", fake)
    r = client.get("/judge/A/B")
    assert r.status_code == 200
    assert r.json()["verdict"] == "A"


def test_reviews_feed_endpoint(client):
    client.post("/judge/human", json={"model_a": "A", "model_b": "B", "verdict": "A"})
    r = client.get("/reviews")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["reviews"][0]["model_a"] == "A"
    assert body["reviews"][0]["verdict"] == "A"


def test_reviews_feed_filters_by_model(client):
    client.post("/judge/human", json={"model_a": "A", "model_b": "B", "verdict": "A"})
    r = client.get("/reviews", params={"model_id": "B"})
    assert r.status_code == 200
    assert r.json()["total"] == 1
    r = client.get("/reviews", params={"model_id": "Z"})
    assert r.json()["total"] == 0


def test_reviews_feed_invalid_judge_type(client):
    r = client.get("/reviews", params={"judge_type": "bogus"})
    assert r.status_code == 400


def test_elo_leaderboard_endpoint(client):
    client.post("/judge/human", json={"model_a": "A", "model_b": "B", "verdict": "A"})
    client.post("/judge/human", json={"model_a": "A", "model_b": "B", "verdict": "A"})
    r = client.get("/elo-leaderboard")
    assert r.status_code == 200
    standings = r.json()["standings"]
    assert len(standings) == 2
    # A won twice -> should outrank B
    assert standings[0]["model_id"] == "A"
    assert standings[0]["rating"] > standings[1]["rating"]
