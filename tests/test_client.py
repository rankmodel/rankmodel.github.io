"""Tests for the ModelRankClient SDK (api/client.py)."""

import json
import urllib.error

import pytest

from api.client import ModelRankClient, ModelRankError


class FakeRequester:
    """Captures calls and returns canned JSON responses keyed by path prefix."""

    def __init__(self, responses=None):
        self.calls = []
        self.responses = responses or {}

    def __call__(self, method, url, headers, data):
        self.calls.append((method, url, headers, data))
        for prefix, payload in self.responses.items():
            if url.endswith(prefix) or prefix in url:
                return json.dumps(payload) if not isinstance(payload, str) else payload
        return json.dumps({"ok": True})

    def last(self):
        return self.calls[-1]


def test_score_builds_url_and_returns_json():
    fake = FakeRequester({"/score/meta-llama/Llama-3.1-8B": {"composite": 82.0, "tier": "A"}})
    client = ModelRankClient(base_url="http://localhost:8000", requester=fake)
    out = client.score("meta-llama/Llama-3.1-8B")
    assert out["composite"] == 82.0
    method, url, _, _ = fake.last()
    assert method == "GET"
    assert url.startswith("http://localhost:8000/score/meta-llama/Llama-3.1-8B")


def test_reviews_passes_filters():
    fake = FakeRequester({"/reviews": {"total": 0, "reviews": []}})
    client = ModelRankClient(base_url="http://localhost:8000", requester=fake)
    client.reviews(limit=10, model_id="Qwen/Qwen3.5-9B", judge_type="llm")
    _, url, _, _ = fake.last()
    assert "limit=10" in url and "model_id=Qwen%2FQwen3.5-9B" in url and "judge_type=llm" in url


def test_judge_human_posts_body_and_validates_verdict():
    fake = FakeRequester({"/judge/human": {"verdict": "A"}})
    client = ModelRankClient(base_url="http://localhost:8000", requester=fake)
    client.judge_human("A", "B", "A")
    method, _, _, data = fake.last()
    assert method == "POST"
    assert json.loads(data) == {"model_a": "A", "model_b": "B", "verdict": "A"}
    with pytest.raises(ValueError):
        client.judge_human("A", "B", "X")


def test_api_key_sent_in_header():
    fake = FakeRequester({"/leaderboard": {"total": 0, "models": []}})
    client = ModelRankClient(base_url="http://localhost:8000", api_key="sk-test", requester=fake)
    client.leaderboard(limit=5)
    _, _, headers, _ = fake.last()
    assert headers["Authorization"] == "Bearer sk-test"


def test_http_error_raises_modelrank_error():
    class Boom:
        code = 500
        def read(self):
            return b"boom"

    def requester(method, url, headers, data):
        raise urllib.error.HTTPError(url, 500, "Server Error", headers, None)

    client = ModelRankClient(base_url="http://localhost:8000", requester=requester)
    with pytest.raises(ModelRankError):
        client.leaderboard()
