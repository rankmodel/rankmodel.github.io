"""Framework-agnostic ModelRank tools.

These are plain Python objects (``name`` / ``description`` / ``run``) that wrap
:class:`api.client.ModelRankClient`. The LangChain and LlamaIndex adapters in
this package wrap the exact same ``run`` methods, so behavior is identical
everywhere. Results are returned as JSON strings, which is what an LLM agent
expects.
"""

import json
from typing import Any, Dict, List, Optional

from api.client import ModelRankClient


def _as_json(payload: Any) -> str:
    if isinstance(payload, (dict, list)):
        return json.dumps(payload, indent=2)
    return str(payload)


class ModelRankTool:
    """Base tool. Subclasses implement :meth:`_run`."""

    name: str = ""
    description: str = ""

    def __init__(self, client: Optional[ModelRankClient] = None):
        self.client = client or ModelRankClient()

    def _run(self, *args, **kwargs) -> Any:
        raise NotImplementedError

    def run(self, *args, **kwargs) -> str:
        return _as_json(self._run(*args, **kwargs))


class ModelRankScoreTool(ModelRankTool):
    name = "modelrank_score"
    description = (
        "Get ModelRank's independent composite score (0-100), tier, and 5-dimension "
        "breakdown for a HuggingFace model id (e.g. 'meta-llama/Llama-3.1-8B'). "
        "Use to answer 'how good is this model?'."
    )

    def _run(self, model_id: str, refresh: bool = False) -> Dict[str, Any]:
        return self.client.score(model_id, refresh=refresh)


class ModelRankCompareTool(ModelRankTool):
    name = "modelrank_compare"
    description = (
        "Head-to-head comparison (ELO win probabilities + per-dimension winners) between "
        "two HuggingFace model ids. Use to answer 'which of these two models is better?'."
    )

    def _run(self, model_a: str, model_b: str) -> Dict[str, Any]:
        return self.client.compare(model_a, model_b)


class ModelRankRecommendTool(ModelRankTool):
    name = "modelrank_recommend"
    description = (
        "Recommend the best open-weight models for a use case "
        "(coding|chat|research|local|multilingual|general). Returns a ranked list."
    )

    def _run(self, use_case: str = "general", limit: int = 10) -> Dict[str, Any]:
        return self.client.recommend(use_case=use_case, limit=limit)


class ModelRankHeadToHeadTool(ModelRankTool):
    name = "modelrank_head_to_head"
    description = (
        "Run ModelRank's LLM-judge vibe-check on two cached HuggingFace model ids and "
        "return the verdict (A/B/tie) plus rationale and updated ELO. Use to settle "
        "which model wins a direct comparison."
    )

    def _run(self, model_a: str, model_b: str) -> Dict[str, Any]:
        return self.client.judge_llm(model_a, model_b)


def get_modelrank_tools(client: Optional[ModelRankClient] = None) -> List[ModelRankTool]:
    """Return all plain ModelRank tools (always available)."""
    return [
        ModelRankScoreTool(client),
        ModelRankCompareTool(client),
        ModelRankRecommendTool(client),
        ModelRankHeadToHeadTool(client),
    ]
