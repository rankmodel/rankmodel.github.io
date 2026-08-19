"""Tests for ModelRank integrations (plain tools + framework adapters)."""

import json

import pytest

from api.client import ModelRankClient
from integrations.base import (
    ModelRankScoreTool,
    ModelRankCompareTool,
    ModelRankRecommendTool,
    ModelRankHeadToHeadTool,
    get_modelrank_tools,
)
from integrations import langchain as lc_mod
from integrations import llama_index as li_mod


class FakeClient(ModelRankClient):
    """ModelRankClient whose _requester returns canned payloads per path suffix."""

    def __init__(self, responses=None):
        self._responses = responses or {}
        super().__init__(base_url="http://fake", requester=self._fake)

    def _fake(self, method, url, headers, data):
        for suffix, payload in self._responses.items():
            if suffix in url:
                return json.dumps(payload)
        return json.dumps({"ok": True})


def test_score_tool_returns_json():
    client = FakeClient({"/score/meta-llama/Llama-3.1-8B": {"composite": 82.0, "tier": "A"}})
    tool = ModelRankScoreTool(client)
    assert tool.name == "modelrank_score"
    out = json.loads(tool.run("meta-llama/Llama-3.1-8B"))
    assert out["composite"] == 82.0


def test_compare_tool_returns_json():
    client = FakeClient({"/compare": {"overall_winner": "A"}})
    out = json.loads(ModelRankCompareTool(client).run("A", "B"))
    assert out["overall_winner"] == "A"


def test_recommend_tool_returns_json():
    client = FakeClient({"/recommend": {"use_case": "coding", "results": []}})
    out = json.loads(ModelRankRecommendTool(client).run("coding", 5))
    assert out["use_case"] == "coding"


def test_head_to_head_tool_runs_llm_judge():
    client = FakeClient({"/judge/A/B": {"verdict": "B", "rationale": "reasons better"}})
    out = json.loads(ModelRankHeadToHeadTool(client).run("A", "B"))
    assert out["verdict"] == "B"


def test_get_modelrank_tools_returns_all_four():
    tools = get_modelrank_tools(FakeClient())
    assert {t.name for t in tools} == {
        "modelrank_score",
        "modelrank_compare",
        "modelrank_recommend",
        "modelrank_head_to_head",
    }


def test_langchain_adapter_requires_dep():
    with pytest.raises(ImportError):
        lc_mod.get_modelrank_langchain_tools(FakeClient())


def test_llama_index_adapter_requires_dep():
    with pytest.raises(ImportError):
        li_mod.get_modelrank_llama_index_tools(FakeClient())
