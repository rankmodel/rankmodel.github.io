"""LLM-judge "vibe-check" for ModelRank head-to-head comparisons.

Given two models, an impartial LLM judge compares them and returns a verdict
(``A`` / ``B`` / ``tie``) plus a short rationale. The result is persisted via
``ModelCache.record_head_to_head`` (``judge_type="llm"``), feeding the ELO ratings.

The LLM call is injectable (``llm_call``) so the logic is unit-testable without
network access; the default call hits an OpenAI-compatible ``/chat/completions``
endpoint configured via environment variables (``JUDGE_API_BASE`` / ``JUDGE_API_KEY``
/ ``JUDGE_MODEL``).
"""

import json
import os
import time
import uuid
import urllib.error
import urllib.request
from typing import Callable, Dict, Any, Optional, Tuple

from data.cache import ModelCache

DEFAULT_SYSTEM = (
    "You are an impartial evaluator of open-weight AI models. "
    "You will be given two models with their public metadata. "
    "Decide which model is better overall for general use, or whether they are tied. "
    "Respond with EXACTLY one of the tokens A, B, or TIE on the first line, "
    "followed by a concise justification."
)


def build_judge_prompt(model_a: Dict[str, Any], model_b: Dict[str, Any]) -> str:
    def summarize(m: Dict[str, Any]) -> str:
        return (
            f"Model: {m.get('model_id', m.get('id', '?'))}\n"
            f"  params: {m.get('params', '?')}  license: {m.get('license', '?')}\n"
            f"  downloads: {m.get('downloads', '?')}  likes: {m.get('likes', '?')}\n"
            f"  pipeline_tag: {m.get('pipeline_tag', '?')}  context: {m.get('context_window', '?')}"
        )

    return summarize(model_a) + "\n\n" + summarize(model_b)


def parse_verdict(raw: str) -> str:
    """Extract A / B / tie from a free-form judge response."""
    if not raw:
        return "tie"
    text = raw.strip().upper()
    for tok, verdict in (("TIE", "tie"), ("B", "B"), ("A", "A")):
        if text.startswith(tok):
            return verdict
    if "MODEL B" in text:
        return "B"
    if "MODEL A" in text:
        return "A"
    if text.startswith("B "):
        return "B"
    if text.startswith("A "):
        return "A"
    # last resort: tally explicit letters
    if text.count("B") > text.count("A"):
        return "B"
    if text.count("A") > text.count("B"):
        return "A"
    return "tie"


def _default_llm_call(prompt: str) -> str:
    base = os.getenv("JUDGE_API_BASE", "https://api.openai.com/v1")
    key = os.getenv("JUDGE_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    model = os.getenv("JUDGE_MODEL", "gpt-4o-mini")
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": DEFAULT_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 300,
        }
    ).encode()
    req = urllib.request.Request(
        base.rstrip("/") + "/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"]


def judge_comparison(
    model_a: Dict[str, Any],
    model_b: Dict[str, Any],
    llm_call: Callable[[str], str] = _default_llm_call,
) -> Tuple[str, str]:
    """Compare two model metadata dicts; returns (verdict, raw_rationale)."""
    prompt = build_judge_prompt(model_a, model_b)
    raw = llm_call(prompt)
    return parse_verdict(raw), raw


def run_llm_judge(
    model_a_id: str,
    model_b_id: str,
    cache: Optional[ModelCache] = None,
    llm_call: Callable[[str], str] = _default_llm_call,
    judge_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Fetch two models, judge them, and persist the head-to-head result.

    Returns ``None`` if either model is not cached; otherwise a dict with the
    ``review_id``, ``verdict``, and ``rationale``.
    """
    cache = cache or ModelCache()
    ma = cache.get_model(model_a_id)
    mb = cache.get_model(model_b_id)
    if not ma or not mb:
        return None
    verdict, rationale = judge_comparison(ma, mb, llm_call)
    review_id = f"llm-{uuid.uuid4().hex[:12]}"
    cache.record_head_to_head(
        review_id,
        model_a_id,
        model_b_id,
        verdict,
        "llm",
        judge_id or os.getenv("JUDGE_MODEL", "gpt-4o-mini"),
    )
    return {
        "review_id": review_id,
        "verdict": verdict,
        "rationale": rationale,
        "model_a": model_a_id,
        "model_b": model_b_id,
    }
