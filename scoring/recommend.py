"""Use-case-aware model recommendations ("best model for my use case").

Re-ranks the cached leaderboard using per-use-case dimension-weight presets applied
to each model's stored 5D ``breakdown`` (0-100 per dimension). This lets a developer
ask "what's best for coding?" without re-fetching benchmarks, and is the engine
behind the Find-My-Model quiz / H2H recommendation surface.
"""

from typing import Dict, Any, List, Optional

DIMENSIONS = ["benchmarks", "efficiency", "community", "recency", "reproducibility"]

# Per-use-case weight presets (keys must match DIMENSIONS). Missing dims default to 0.
PRESETS: Dict[str, Dict[str, float]] = {
    "coding": {"benchmarks": 0.80, "efficiency": 0.05, "community": 0.05, "recency": 0.10, "reproducibility": 0.00},
    "chat": {"benchmarks": 0.45, "efficiency": 0.10, "community": 0.30, "recency": 0.15, "reproducibility": 0.00},
    "research": {"benchmarks": 0.85, "efficiency": 0.05, "community": 0.00, "recency": 0.10, "reproducibility": 0.00},
    "local": {"benchmarks": 0.45, "efficiency": 0.40, "community": 0.05, "recency": 0.10, "reproducibility": 0.00},
    "multilingual": {"benchmarks": 0.55, "efficiency": 0.10, "community": 0.10, "recency": 0.10, "reproducibility": 0.00},
}


def _weights_for(use_case: str) -> Dict[str, float]:
    if use_case in PRESETS:
        return {d: PRESETS[use_case].get(d, 0.0) for d in DIMENSIONS}
    # unknown / "general" -> fall back to the canonical base weights
    from config.settings import SCORING_WEIGHTS

    return {d: float(SCORING_WEIGHTS.get(d, 0.0)) for d in DIMENSIONS}


def _weighted_score(breakdown: Dict[str, float], weights: Dict[str, float]) -> float:
    total = 0.0
    wsum = 0.0
    for d in DIMENSIONS:
        w = weights.get(d, 0.0)
        v = breakdown.get(d)
        if v is None:
            continue
        total += w * v
        wsum += w
    return total / wsum if wsum else 0.0


def recommend(use_case: str, cache, limit: int = 10) -> List[Dict[str, Any]]:
    """Return the top ``limit`` models for ``use_case``, re-ranked by preset weights."""
    weights = _weights_for(use_case)
    models = cache.get_leaderboard(limit=1000)
    results = []
    for m in models:
        score = m.get("score") or {}
        breakdown = score.get("breakdown") or {}
        if not breakdown:
            continue
        results.append(
            {
                "model_id": m["model_id"],
                "use_case_score": round(_weighted_score(breakdown, weights), 2),
                "tier": score.get("tier"),
                "base_composite": score.get("composite"),
            }
        )
    results.sort(key=lambda x: x["use_case_score"], reverse=True)
    return results[:limit]


def available_use_cases() -> List[str]:
    return sorted(set(["general"] + list(PRESETS.keys())))
