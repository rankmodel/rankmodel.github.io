"""Lightweight Python client for the ModelRank REST API.

Wraps the public endpoints (score, leaderboard, compare, recommend, head-to-head
reviews + ELO, and the LLM/human judge) so the data layer can be reused by
integrations — a LangChain/LlamaIndex tool, a VS Code hover provider, or any
script. Uses only the standard library (``urllib``) so it has no extra deps.

The network call is injectable (``requester``) for testing without a live server.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional


DEFAULT_BASE_URL = "https://api.modelrank.com"


def _default_requester(method: str, url: str, headers: Dict[str, str], data: Optional[bytes]) -> str:
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


class ModelRankError(RuntimeError):
    """Raised when the API returns a non-2xx status."""


class ModelRankClient:
    """Minimal SDK for the ModelRank API.

    Example:
        >>> client = ModelRankClient()  # or ModelRankClient("http://localhost:8000")
        >>> client.score("meta-llama/Llama-3.1-8B")
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        api_key: Optional[str] = None,
        requester: Optional[Callable[[str, str, Dict[str, str], Optional[bytes]], str]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._requester = requester or _default_requester

    # ---- internals ----

    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None,
                 json_body: Optional[Dict[str, Any]] = None) -> Any:
        url = self.base_url + path
        if params:
            clean = {k: str(v) for k, v in params.items() if v is not None}
            if clean:
                url += "?" + urllib.parse.urlencode(clean)
        headers = {"Accept": "application/json"}
        data = None
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            raw = self._requester(method, url, headers, data)
        except urllib.error.HTTPError as e:
            raise ModelRankError(f"{method} {path} -> HTTP {e.code}: {e.read().decode('utf-8', 'replace')}") from e
        if not raw:
            return None
        return json.loads(raw)

    # ---- endpoints ----

    def score(self, model_id: str, refresh: bool = False) -> Dict[str, Any]:
        return self._request("GET", f"/score/{model_id}", params={"refresh": refresh})

    def leaderboard(self, limit: int = 50, tier: Optional[str] = None,
                    task: Optional[str] = None, offset: int = 0) -> Dict[str, Any]:
        return self._request("GET", "/leaderboard", params={
            "limit": limit, "tier": tier, "task": task, "offset": offset})

    def compare(self, model_a: str, model_b: str) -> Dict[str, Any]:
        return self._request("GET", "/compare", params={"model_a": model_a, "model_b": model_b})

    def recommend(self, use_case: str = "general", limit: int = 10) -> Dict[str, Any]:
        return self._request("GET", "/recommend", params={"use_case": use_case, "limit": limit})

    def reviews(self, limit: int = 50, model_id: Optional[str] = None,
                judge_type: Optional[str] = None) -> Dict[str, Any]:
        return self._request("GET", "/reviews", params={
            "limit": limit, "model_id": model_id, "judge_type": judge_type})

    def elo(self, model_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/elo/{model_id}")

    def elo_leaderboard(self, limit: int = 50) -> Dict[str, Any]:
        return self._request("GET", "/elo-leaderboard", params={"limit": limit})

    def judge_human(self, model_a: str, model_b: str, verdict: str) -> Dict[str, Any]:
        if verdict not in ("A", "B", "tie"):
            raise ValueError("verdict must be one of: A, B, tie")
        return self._request("POST", "/judge/human", json_body={
            "model_a": model_a, "model_b": model_b, "verdict": verdict})

    def judge_llm(self, model_a: str, model_b: str) -> Dict[str, Any]:
        return self._request("GET", f"/judge/{model_a}/{model_b}")
