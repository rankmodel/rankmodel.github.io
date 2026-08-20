#!/usr/bin/env python3
"""Generate a ModelRank badge (Markdown / HTML / SVG) for any model.

Examples
--------
    # Look up a model we already rank and emit a Markdown badge
    python scripts/generate_badge.py --model meta-llama/Llama-3.1-8B

    # Build a badge from values you supply (no lookup needed)
    python scripts/generate_badge.py --model my-org/my-model \
        --score 81.4 --tier A --format svg

    # Emit an HTML snippet for your README
    python scripts/generate_badge.py --model Qwen/Qwen3.5-9B --format html
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


CACHE_DB_PATH = Path("data/modelrank.db")
LEADERBOARD_JSON = Path("static_output/leaderboard.json")
BASE_URL = "https://rankmodel.github.io"


def _load_leaderboard() -> dict[str, dict]:
    """Load ranked models from the local cache, best-effort."""
    models: dict[str, dict] = {}
    if LEADERBOARD_JSON.exists():
        try:
            data = json.loads(LEADERBOARD_JSON.read_text(encoding="utf-8"))
            for entry in data:
                models[entry.get("model_id", "")] = entry
        except (json.JSONDecodeError, OSError):
            pass
    return models


def _lookup(model_id: str) -> Optional[dict]:
    """Find a model in the local leaderboard cache, if present."""
    return _load_leaderboard().get(model_id)


def _svg_badge(model_id: str, label: str, value: str, color: str) -> str:
    text = f"ModelRank {label}: {value}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="260" height="20" '
        f'role="img" aria-label="{text}">'
        f'<rect width="260" height="20" rx="4" fill="#0a0a0f"/>'
        f'<text x="8" y="14" fill="#a855f7" font-family="Inter,Arial,sans-serif" '
        f'font-size="11" font-weight="700">{text}</text>'
        f'<a href="{BASE_URL}/badges/{model_id}/score.svg" target="_blank">'
        f'<rect width="260" height="20" fill="transparent"/></a></svg>'
    )


def _render(model_id: str, score: Optional[float], tier: Optional[str],
            style: str, fmt: str) -> str:
    if style == "score":
        value = f"{score:.1f}" if score is not None else "N/A"
    elif style == "tier":
        value = tier or "N/A"
    else:  # rank handled by caller; default to score
        value = f"{score:.1f}" if score is not None else "N/A"

    if fmt == "svg":
        return _svg_badge(model_id, style.capitalize(), value, "#a855f7")
    if fmt == "html":
        return (
            f'<a href="{BASE_URL}">'
            f'<img alt="ModelRank {style} {value}" '
            f'src="{BASE_URL}/badges/{model_id}/{style}.svg"></a>'
        )
    # markdown
    return f'![ModelRank {style} {value}]({BASE_URL}/badges/{model_id}/{style}.svg)'


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a ModelRank badge.")
    parser.add_argument("--model", required=True, help="HuggingFace id, e.g. org/model")
    parser.add_argument("--style", choices=["score", "tier", "rank"], default="score")
    parser.add_argument("--format", choices=["md", "html", "svg"], default="md")
    parser.add_argument("--score", type=float, default=None, help="Override score (0-100)")
    parser.add_argument("--tier", default=None, help="Override tier (S/A/B/C/D)")
    args = parser.parse_args()

    try:
        found = _lookup(args.model)
        score = args.score if args.score is not None else (found or {}).get("score", {}).get("composite")
        tier = args.tier or (found or {}).get("tier")
        if score is None and args.style in ("score", "rank"):
            print(f"Model '{args.model}' not found in local cache and no --score given.",
                  file=sys.stderr)
            return 2
        print(_render(args.model, score, tier, args.style, args.format))
        return 0
    except (OSError, ValueError) as exc:  # pragma: no cover - defensive
        print(f"Failed to generate badge: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
