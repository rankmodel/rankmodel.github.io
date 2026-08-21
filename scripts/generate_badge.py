#!/usr/bin/env python3
"""ModelRank Badge Generator — CLI tool for developers.

Generates HTML, Markdown, or reStructuredText badge snippets for any model
on the ModelRank leaderboard.  Supports both live API lookup and an offline
placeholder mode so no network connection is required.

Examples
--------
    # Live score badge (Markdown, default)
    python scripts/generate_badge.py score mistralai/Mistral-7B-v0.1

    # HTML format
    python scripts/generate_badge.py score mistralai/Mistral-7B-v0.1 --format html

    # All badge types in one shot
    python scripts/generate_badge.py all meta-llama/Llama-3.1-8B

    # Side-by-side comparison snippet
    python scripts/generate_badge.py compare mistralai/Mistral-7B-v0.1 meta-llama/Llama-3.1-8B

    # Offline placeholder — no API call made
    python scripts/generate_badge.py score --offline some-org/some-model

    # Copy result to clipboard
    python scripts/generate_badge.py score mistralai/Mistral-7B-v0.1 --copy

    # Full README section ready to paste
    python scripts/generate_badge.py all meta-llama/Llama-3.1-8B --readme-section
"""

from __future__ import annotations

import argparse
import sys
import textwrap
import urllib.parse
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL: str = "https://rankmodel.github.io"
API_BASE: str = "http://localhost:8000"
SHIELDS_BASE: str = "https://img.shields.io/badge"

# Tier display colours (shields.io uses hex without #)
TIER_COLORS: dict[str, str] = {
    "S": "a855f7",
    "A": "3b82f6",
    "B": "22c55e",
    "C": "eab308",
    "D": "ef4444",
}

# Dimension display colours
DIMENSION_COLORS: dict[str, str] = {
    "benchmarks": "6366f1",
    "efficiency": "22c55e",
    "community": "f59e0b",
    "recency": "06b6d4",
}

# Scoring weights (informational, used in README section)
SCORE_WEIGHTS: dict[str, float] = {
    "Benchmarks": 0.70,
    "Recency": 0.15,
    "Community": 0.10,
    "Efficiency": 0.05,
}

# Badge types supported by the `all` subcommand
ALL_BADGE_TYPES: list[str] = ["score", "tier", "rank"]

# Output format choices
FORMAT_CHOICES: list[str] = ["markdown", "html", "rst", "svg"]


# ---------------------------------------------------------------------------
# Optional dependency helpers
# ---------------------------------------------------------------------------


def _try_copy_to_clipboard(text: str) -> None:
    """Attempt to copy *text* to the system clipboard via pyperclip.

    Silently skips if pyperclip is not installed or an error occurs.

    Args:
        text: The string to place on the clipboard.
    """
    try:
        import pyperclip  # type: ignore[import]

        pyperclip.copy(text)
        print("[✓] Copied to clipboard.", file=sys.stderr)
    except ImportError:
        print(
            "[!] pyperclip not installed — skipping clipboard copy. "
            "Install with: pip install pyperclip",
            file=sys.stderr,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[!] Clipboard copy failed: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------


def _fetch_model_data(model_id: str, base_url: str = API_BASE) -> Optional[dict[str, Any]]:
    """Fetch model score data from the ModelRank REST API.

    Args:
        model_id: The HuggingFace-style model identifier (org/name).
        base_url: Base URL of the ModelRank API server.

    Returns:
        Parsed JSON response dict on success, or ``None`` on failure.
    """
    try:
        import os as _os

        # Allow running from any cwd by adding project root to path
        _project_root = str(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
        if _project_root not in sys.path:
            sys.path.insert(0, _project_root)

        from api.client import ModelRankClient  # type: ignore[import]

        client = ModelRankClient(base_url=base_url)
        data: dict[str, Any] = client.score(model_id)
        return data
    except ImportError:
        print(
            "[!] Could not import api.client — falling back to offline mode.",
            file=sys.stderr,
        )
        return None
    except Exception as exc:  # noqa: BLE001
        print(f"[!] API request failed for '{model_id}': {exc}", file=sys.stderr)
        return None


def _fetch_compare_data(
    model_a: str, model_b: str, base_url: str = API_BASE
) -> Optional[dict[str, Any]]:
    """Fetch a head-to-head comparison from the API.

    Args:
        model_a: First model identifier.
        model_b: Second model identifier.
        base_url: Base URL of the ModelRank API server.

    Returns:
        Parsed JSON dict, or ``None`` on failure.
    """
    try:
        import os as _os

        _project_root = str(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
        if _project_root not in sys.path:
            sys.path.insert(0, _project_root)

        from api.client import ModelRankClient  # type: ignore[import]

        client = ModelRankClient(base_url=base_url)
        data: dict[str, Any] = client.compare(model_a, model_b)
        return data
    except ImportError:
        print("[!] Could not import api.client.", file=sys.stderr)
        return None
    except Exception as exc:  # noqa: BLE001
        print(f"[!] Compare API request failed: {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Score / tier extraction helpers
# ---------------------------------------------------------------------------


def _extract_score(data: dict[str, Any]) -> Optional[float]:
    """Pull the composite score out of an API response dict.

    Handles several common response shapes gracefully.

    Args:
        data: Raw API response dictionary.

    Returns:
        Float score 0-100, or ``None`` if not found.
    """
    # Shape 1: {"score": {"composite": 82.1, ...}}
    if isinstance(data.get("score"), dict):
        val = data["score"].get("composite")
        if val is not None:
            return float(val)
    # Shape 2: {"composite": 82.1}
    if "composite" in data:
        return float(data["composite"])
    # Shape 3: {"score": 82.1}
    if isinstance(data.get("score"), (int, float)):
        return float(data["score"])
    return None


def _extract_tier(data: dict[str, Any]) -> Optional[str]:
    """Pull the tier string from an API response dict.

    Args:
        data: Raw API response dictionary.

    Returns:
        One of 'S', 'A', 'B', 'C', 'D', or ``None``.
    """
    tier = data.get("tier")
    if isinstance(tier, str) and tier.upper() in TIER_COLORS:
        return tier.upper()
    return None


def _extract_rank(data: dict[str, Any]) -> Optional[int]:
    """Pull the overall rank from an API response dict.

    Args:
        data: Raw API response dictionary.

    Returns:
        Integer rank, or ``None`` if absent.
    """
    rank = data.get("rank")
    if isinstance(rank, int):
        return rank
    return None


def _extract_dimensions(data: dict[str, Any]) -> dict[str, float]:
    """Extract per-dimension scores from an API response dict.

    Args:
        data: Raw API response dictionary.

    Returns:
        Mapping of dimension name to float score (may be empty).
    """
    dims: dict[str, float] = {}
    raw = data.get("dimensions") or (data.get("score") if isinstance(data.get("score"), dict) else {})
    if isinstance(raw, dict):
        for key in DIMENSION_COLORS:
            if key in raw and raw[key] is not None:
                try:
                    dims[key] = float(raw[key])
                except (TypeError, ValueError):
                    pass
    return dims


# ---------------------------------------------------------------------------
# Badge URL builders
# ---------------------------------------------------------------------------


def _badge_image_url(model_id: str, badge_type: str) -> str:
    """Return the canonical hosted badge SVG URL on rankmodel.github.io.

    Args:
        model_id: HuggingFace model identifier.
        badge_type: One of 'score', 'tier', 'rank', etc.

    Returns:
        Absolute URL string.
    """
    return f"{BASE_URL}/badges/{model_id}/{badge_type}.svg"


# ---------------------------------------------------------------------------
# Badge renderers
# ---------------------------------------------------------------------------


def _svg_badge(model_id: str, badge_type: str, score: Optional[float] = None, tier: Optional[str] = None, rank: Optional[int] = None) -> str:
    """Generate raw SVG string by delegating to generate_static_assets."""
    import sys, os
    _project_root = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)
    from scripts.generate_static_assets import generate_score_badge, generate_tier_badge, generate_rank_badge
    
    if badge_type == "score":
        return generate_score_badge(model_id, score or 0.0, tier or "D", rank or 0)
    elif badge_type == "tier":
        return generate_tier_badge(tier or "?")
    elif badge_type == "rank":
        return generate_rank_badge(rank or 0, 150) # default total
    return ""


def _render_badge(
    *,
    model_id: str,
    badge_type: str,
    label: str,
    message: str,
    color: str,
    fmt: str,
    link: str = BASE_URL,
    score: Optional[float] = None,
    tier: Optional[str] = None,
    rank: Optional[int] = None,
) -> str:
    """Render a single badge in the requested output format.

    Args:
        model_id: HuggingFace model identifier.
        badge_type: Badge type slug (score, tier, rank, …).
        label: Left-side label text.
        message: Right-side message text.
        color: Hex colour (without ``#``).
        fmt: Output format — 'markdown', 'html', 'rst', or 'svg'.
        link: URL the badge should link to.
        score: Optional score.
        tier: Optional tier.
        rank: Optional rank.

    Returns:
        Formatted badge snippet string.
    """
    if fmt == "svg":
        return _svg_badge(model_id, badge_type, score=score, tier=tier, rank=rank)

    img_url = _badge_image_url(model_id, badge_type)
    alt_text = f"ModelRank {label}: {message}"

    if fmt == "html":
        return (
            f'<a href="{link}" target="_blank" rel="noopener noreferrer">'
            f'<img alt="{alt_text}" src="{img_url}"/>'
            f"</a>"
        )
    if fmt == "rst":
        return (
            f".. image:: {img_url}\n"
            f"   :target: {link}\n"
            f"   :alt: {alt_text}"
        )
    # Default: markdown
    return f"[![{alt_text}]({img_url})]({link})"


def _offline_badge(model_id: str, badge_type: str, fmt: str) -> str:
    """Generate a placeholder badge without any API call.

    Args:
        model_id: HuggingFace model identifier.
        badge_type: Badge type slug.
        fmt: Output format.

    Returns:
        Badge snippet pointing to the canonical hosted URL.
    """
    label_map: dict[str, str] = {
        "score": "Score",
        "tier": "Tier",
        "rank": "Rank",
    }
    message_map: dict[str, str] = {
        "score": "N/A",
        "tier": "?",
        "rank": "#?",
    }
    color_map: dict[str, str] = {
        "score": "a855f7",
        "tier": "a855f7",
        "rank": "3b82f6",
    }

    label = label_map.get(badge_type, badge_type.capitalize())
    message = message_map.get(badge_type, "?")
    color = color_map.get(badge_type, "a855f7")

    return _render_badge(
        model_id=model_id,
        badge_type=badge_type,
        label=label,
        message=message,
        color=color,
        fmt=fmt,
    )


def _score_badge(
    model_id: str,
    score: Optional[float],
    tier: Optional[str],
    fmt: str,
) -> str:
    """Render a score badge with the live score embedded.

    Args:
        model_id: HuggingFace model identifier.
        score: Composite score 0-100 (None → 'N/A').
        tier: Tier string for colour selection (None → purple).
        fmt: Output format.

    Returns:
        Badge snippet string.
    """
    message = f"{score:.1f}" if score is not None else "N/A"
    color = TIER_COLORS.get(tier or "", "a855f7")
    return _render_badge(
        model_id=model_id,
        badge_type="score",
        label="Score",
        message=message,
        color=color,
        fmt=fmt,
        score=score,
        tier=tier,
    )


def _tier_badge(model_id: str, tier: Optional[str], fmt: str) -> str:
    """Render a tier badge.

    Args:
        model_id: HuggingFace model identifier.
        tier: Tier string (S/A/B/C/D).
        fmt: Output format.

    Returns:
        Badge snippet string.
    """
    message = tier or "?"
    color = TIER_COLORS.get(tier or "", "a855f7")
    return _render_badge(
        model_id=model_id,
        badge_type="tier",
        label="Tier",
        message=message,
        color=color,
        fmt=fmt,
        tier=tier,
    )


def _rank_badge(model_id: str, rank: Optional[int], fmt: str) -> str:
    """Render a leaderboard-rank badge.

    Args:
        model_id: HuggingFace model identifier.
        rank: Integer rank (1-indexed), or None.
        fmt: Output format.

    Returns:
        Badge snippet string.
    """
    message = f"#{rank}" if rank is not None else "#?"
    return _render_badge(
        model_id=model_id,
        badge_type="rank",
        label="Rank",
        message=message,
        color="3b82f6",
        fmt=fmt,
        rank=rank,
    )


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------


def cmd_score(args: argparse.Namespace) -> int:
    """Handle the ``score`` subcommand.

    Fetches (or fakes) the composite score badge for a single model.

    Args:
        args: Parsed CLI namespace.

    Returns:
        Exit code (0 = success, non-zero = failure).
    """
    model_id: str = args.model
    fmt: str = args.format

    if args.offline:
        output = _offline_badge(model_id, "score", fmt)
    else:
        data = _fetch_model_data(model_id, base_url=args.api_base)
        if data is None:
            print(
                f"[!] Could not fetch data for '{model_id}'. "
                "Use --offline for a placeholder badge.",
                file=sys.stderr,
            )
            return 1

        score = _extract_score(data)
        tier = _extract_tier(data)

        if score is None:
            print(
                f"[!] Warning: no composite score found for '{model_id}'.",
                file=sys.stderr,
            )

        output = _score_badge(model_id, score, tier, fmt)

    print(output)
    if args.copy:
        _try_copy_to_clipboard(output)
    return 0


def cmd_tier(args: argparse.Namespace) -> int:
    """Handle the ``tier`` subcommand.

    Args:
        args: Parsed CLI namespace.

    Returns:
        Exit code.
    """
    model_id: str = args.model
    fmt: str = args.format

    if args.offline:
        output = _offline_badge(model_id, "tier", fmt)
    else:
        data = _fetch_model_data(model_id, base_url=args.api_base)
        if data is None:
            print(
                f"[!] Could not fetch data for '{model_id}'. Use --offline.",
                file=sys.stderr,
            )
            return 1
        tier = _extract_tier(data)
        output = _tier_badge(model_id, tier, fmt)

    print(output)
    if args.copy:
        _try_copy_to_clipboard(output)
    return 0


def cmd_all(args: argparse.Namespace) -> int:
    """Handle the ``all`` subcommand.

    Outputs score, tier, and rank badges one per line (and optionally a
    full README section when --readme-section is given).

    Args:
        args: Parsed CLI namespace.

    Returns:
        Exit code.
    """
    model_id: str = args.model
    fmt: str = args.format
    lines: list[str] = []

    if args.offline:
        for badge_type in ALL_BADGE_TYPES:
            lines.append(_offline_badge(model_id, badge_type, fmt))
    else:
        data = _fetch_model_data(model_id, base_url=args.api_base)
        if data is None:
            print(
                f"[!] Could not fetch data for '{model_id}'. "
                "Falling back to offline placeholders.",
                file=sys.stderr,
            )
            for badge_type in ALL_BADGE_TYPES:
                lines.append(_offline_badge(model_id, badge_type, fmt))
        else:
            score = _extract_score(data)
            tier = _extract_tier(data)
            rank = _extract_rank(data)
            lines.append(_score_badge(model_id, score, tier, fmt))
            lines.append(_tier_badge(model_id, tier, fmt))
            lines.append(_rank_badge(model_id, rank, fmt))

    if args.readme_section:
        output = _build_readme_section(model_id, lines, fmt)
    else:
        output = "\n".join(lines)

    print(output)
    if args.copy:
        _try_copy_to_clipboard(output)
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    """Handle the ``compare`` subcommand.

    Outputs a comparison snippet showing which model wins per dimension.

    Args:
        args: Parsed CLI namespace.

    Returns:
        Exit code.
    """
    model_a: str = args.model_a
    model_b: str = args.model_b
    fmt: str = args.format

    if args.offline:
        output = _build_offline_compare(model_a, model_b, fmt)
    else:
        data = _fetch_compare_data(model_a, model_b, base_url=args.api_base)

        if data is None:
            # Try fetching each model separately and comparing locally
            print("[!] Compare endpoint unavailable — fetching models separately.", file=sys.stderr)
            data_a = _fetch_model_data(model_a, base_url=args.api_base)
            data_b = _fetch_model_data(model_b, base_url=args.api_base)

            if data_a is None or data_b is None:
                print(
                    "[!] Could not fetch model data. Use --offline for placeholders.",
                    file=sys.stderr,
                )
                return 1

            output = _build_local_compare(model_a, model_b, data_a, data_b, fmt)
        else:
            output = _build_api_compare(model_a, model_b, data, fmt)

    print(output)
    if args.copy:
        _try_copy_to_clipboard(output)
    return 0


# ---------------------------------------------------------------------------
# Comparison builders
# ---------------------------------------------------------------------------


def _build_api_compare(
    model_a: str,
    model_b: str,
    data: dict[str, Any],
    fmt: str,
) -> str:
    """Build a comparison snippet from the API's compare endpoint response.

    Args:
        model_a: First model identifier.
        model_b: Second model identifier.
        data: Raw API compare response.
        fmt: Output format.

    Returns:
        Formatted comparison string.
    """
    # The compare response may contain nested model data or a top-level winner
    model_a_data: dict[str, Any] = data.get("model_a") or data.get(model_a) or {}
    model_b_data: dict[str, Any] = data.get("model_b") or data.get(model_b) or {}
    return _build_local_compare(model_a, model_b, model_a_data, model_b_data, fmt)


def _build_local_compare(
    model_a: str,
    model_b: str,
    data_a: dict[str, Any],
    data_b: dict[str, Any],
    fmt: str,
) -> str:
    """Build a comparison snippet by diffing two model data dicts locally.

    Args:
        model_a: First model identifier.
        model_b: Second model identifier.
        data_a: API data for model A.
        data_b: API data for model B.
        fmt: Output format.

    Returns:
        Multi-line formatted comparison snippet.
    """
    score_a = _extract_score(data_a)
    score_b = _extract_score(data_b)
    tier_a = _extract_tier(data_a)
    tier_b = _extract_tier(data_b)
    dims_a = _extract_dimensions(data_a)
    dims_b = _extract_dimensions(data_b)

    short_a = model_a.split("/")[-1]
    short_b = model_b.split("/")[-1]

    rows: list[str] = []

    # Overall winner
    if score_a is not None and score_b is not None:
        winner = short_a if score_a >= score_b else short_b
        rows.append(f"### ModelRank Comparison: {short_a} vs {short_b}")
        rows.append("")
        rows.append(f"**Overall winner: {winner}** ({score_a:.1f} vs {score_b:.1f})")
        rows.append("")

    # Per-model badge lines
    rows.append(f"**{short_a}**")
    rows.append(_score_badge(model_a, score_a, tier_a, fmt))
    rows.append(_tier_badge(model_a, tier_a, fmt))
    rows.append("")
    rows.append(f"**{short_b}**")
    rows.append(_score_badge(model_b, score_b, tier_b, fmt))
    rows.append(_tier_badge(model_b, tier_b, fmt))
    rows.append("")

    # Per-dimension breakdown
    all_dims = set(dims_a) | set(dims_b)
    if all_dims:
        rows.append("#### Dimension Breakdown")
        rows.append("")
        rows.append(f"| Dimension | {short_a} | {short_b} | Winner |")
        rows.append("|-----------|" + "-------|" * 3)
        for dim in sorted(all_dims):
            sa = dims_a.get(dim)
            sb = dims_b.get(dim)
            sa_str = f"{sa:.1f}" if sa is not None else "N/A"
            sb_str = f"{sb:.1f}" if sb is not None else "N/A"
            if sa is not None and sb is not None:
                w = f"✅ {short_a}" if sa >= sb else f"✅ {short_b}"
            else:
                w = "—"
            rows.append(f"| {dim.capitalize()} | {sa_str} | {sb_str} | {w} |")
        rows.append("")

    rows.append(
        f"[View full comparison on ModelRank]"
        f"({BASE_URL}/compare?"
        f"a={urllib.parse.quote(model_a)}&b={urllib.parse.quote(model_b)})"
    )
    return "\n".join(rows)


def _build_offline_compare(model_a: str, model_b: str, fmt: str) -> str:
    """Build a placeholder comparison snippet without any API data.

    Args:
        model_a: First model identifier.
        model_b: Second model identifier.
        fmt: Output format.

    Returns:
        Formatted placeholder comparison string.
    """
    short_a = model_a.split("/")[-1]
    short_b = model_b.split("/")[-1]
    rows: list[str] = [
        f"### ModelRank Comparison: {short_a} vs {short_b}",
        "",
        f"**{short_a}**",
        _offline_badge(model_a, "score", fmt),
        _offline_badge(model_a, "tier", fmt),
        "",
        f"**{short_b}**",
        _offline_badge(model_b, "score", fmt),
        _offline_badge(model_b, "tier", fmt),
        "",
        f"[View on ModelRank]({BASE_URL})",
    ]
    return "\n".join(rows)


# ---------------------------------------------------------------------------
# README section builder
# ---------------------------------------------------------------------------


def _build_readme_section(model_id: str, badge_lines: list[str], fmt: str) -> str:
    """Compose a full README section with badges and leaderboard info.

    Args:
        model_id: HuggingFace model identifier.
        badge_lines: Pre-rendered badge snippet strings.
        fmt: Output format (used for section formatting hints).

    Returns:
        Complete README-ready section string.
    """
    short_name = model_id.split("/")[-1]
    weights_rows = "\n".join(
        f"| {dim} | {int(w * 100)}% |" for dim, w in SCORE_WEIGHTS.items()
    )
    badges_block = " ".join(badge_lines)

    section = textwrap.dedent(f"""\
        ## ModelRank Score

        {badges_block}

        This model is ranked on **[ModelRank]({BASE_URL})** — the independent LLM
        leaderboard with zero bias and 954+ models evaluated across 5 dimensions.

        ### Scoring Dimensions

        | Dimension | Weight |
        |-----------|--------|
        {weights_rows}

        ### Install & Use

        ```bash
        pip install modelrank
        ```

        ```python
        from api.client import ModelRankClient

        client = ModelRankClient()
        data = client.score("{model_id}")
        print(data)
        ```

        📊 [View {short_name} on the Leaderboard]({BASE_URL}/models/{urllib.parse.quote(model_id)})
        🏆 [Full Leaderboard]({BASE_URL})
        ⭐ [Star us on GitHub](https://github.com/rankmodel/rankmodel.github.io)
    """)
    return section


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Construct and return the top-level argument parser with subcommands.

    Returns:
        Configured :class:`argparse.ArgumentParser` instance.
    """
    parser = argparse.ArgumentParser(
        prog="generate_badge",
        description=(
            "ModelRank Badge Generator — produce Markdown, HTML, or RST badge snippets "
            "for any model on the leaderboard."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              %(prog)s score mistralai/Mistral-7B-v0.1
              %(prog)s score mistralai/Mistral-7B-v0.1 --format html
              %(prog)s all meta-llama/Llama-3.1-8B --readme-section
              %(prog)s compare mistralai/Mistral-7B-v0.1 meta-llama/Llama-3.1-8B
              %(prog)s score some-org/some-model --offline --copy
        """),
    )

    # Global flags on the top-level parser (for --help display only).
    # Actual parsing uses the two-pass approach in main() so these flags
    # are accepted on EITHER side of the subcommand name.
    parser.add_argument(
        "--format",
        choices=FORMAT_CHOICES,
        default="markdown",
        metavar="FORMAT",
        help=f"Output format. One of: {', '.join(FORMAT_CHOICES)}. Default: markdown",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip API calls and emit placeholder badges.",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy the output to the clipboard (requires pyperclip).",
    )
    parser.add_argument(
        "--api-base",
        default=API_BASE,
        metavar="URL",
        help=f"ModelRank API base URL. Default: {API_BASE}",
    )

    subparsers = parser.add_subparsers(dest="subcommand", metavar="SUBCOMMAND")
    subparsers.required = True

    # --- score ---
    p_score = subparsers.add_parser(
        "score",
        help="Generate a composite score badge for a single model.",
    )
    p_score.add_argument("model", metavar="MODEL_ID", help="HuggingFace model id, e.g. org/name")
    p_score.set_defaults(func=cmd_score)

    # --- tier ---
    p_tier = subparsers.add_parser(
        "tier",
        help="Generate a tier badge (S/A/B/C/D) for a single model.",
    )
    p_tier.add_argument("model", metavar="MODEL_ID", help="HuggingFace model id")
    p_tier.set_defaults(func=cmd_tier)

    # --- all ---
    p_all = subparsers.add_parser(
        "all",
        help="Generate score, tier, and rank badges for a single model.",
    )
    p_all.add_argument("model", metavar="MODEL_ID", help="HuggingFace model id")
    p_all.add_argument(
        "--readme-section",
        action="store_true",
        help="Emit a full README section (badges + install instructions + leaderboard link).",
    )
    p_all.set_defaults(func=cmd_all)

    # --- compare ---
    p_compare = subparsers.add_parser(
        "compare",
        help="Generate a head-to-head comparison snippet for two models.",
    )
    p_compare.add_argument("model_a", metavar="MODEL_A", help="First model id")
    p_compare.add_argument("model_b", metavar="MODEL_B", help="Second model id")
    p_compare.set_defaults(func=cmd_compare)

    return parser


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> int:
    """Parse arguments and dispatch to the appropriate subcommand handler.

    Global flags (--offline, --format, --copy, --api-base) are accepted both
    before and after the subcommand name by using a two-pass parse strategy:
    first extract global options with ``parse_known_args``, then parse the
    remaining tokens (subcommand + its own args) with the full parser.

    Returns:
        Shell exit code (0 on success).
    """
    import sys as _sys

    # Pass 1 — extract global flags from anywhere in argv.
    global_parser = argparse.ArgumentParser(add_help=False)
    global_parser.add_argument("--format", choices=FORMAT_CHOICES, default="markdown")
    global_parser.add_argument("--offline", action="store_true", default=False)
    global_parser.add_argument("--copy", action="store_true", default=False)
    global_parser.add_argument("--api-base", default=API_BASE, dest="api_base")
    global_parser.add_argument("--model", help="Shorthand for running 'score <model>'")

    global_args, remaining = global_parser.parse_known_args()

    # If --model is given and no valid subcommand is in remaining, default to score
    if global_args.model and not any(arg in remaining for arg in ["score", "tier", "all", "compare"]):
        remaining = ["score", global_args.model] + remaining

    # Pass 2 — parse the remainder: subcommand + its own positional/optional args.
    parser = _build_parser()
    args = parser.parse_args(remaining)

    # Inject the global options into the subcommand namespace.
    args.format = global_args.format
    args.offline = global_args.offline
    args.copy = global_args.copy
    args.api_base = global_args.api_base

    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("\n[!] Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:  # noqa: BLE001
        print(f"[✗] Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
