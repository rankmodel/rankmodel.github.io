#!/usr/bin/env python3
"""
ModelRank — Model DNA Card Generator
=====================================
Generates a "Spotify Wrapped"-style shareable card for any model.
Output: brand/dna/{org}_{model}.png + HTML embed code.

This is the virality engine: model creators share their DNA card on
social media, every card links back to ModelRank.

Usage:
  python scripts/generate_model_dna.py mistralai/Mistral-7B-v0.1
  python scripts/generate_model_dna.py meta-llama/Llama-3.1-8B --format html
  python scripts/generate_model_dna.py --batch top10   # top 10 from leaderboard

Dependencies:
  pip install pillow requests
"""

import argparse
import json
import os
import sys
import textwrap
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# ────────────────────────────────────────────────────────────────────────────
# Design constants
# ────────────────────────────────────────────────────────────────────────────

WIDTH, HEIGHT = 800, 480
BG_COLOR = "#0d1117"       # GitHub dark
ACCENT_PURPLE = "#a855f7"  # S-tier
ACCENT_BLUE = "#3b82f6"    # A-tier
ACCENT_GREEN = "#22c55e"   # B-tier / efficiency
ACCENT_YELLOW = "#eab308"  # C-tier
ACCENT_RED = "#ef4444"     # D-tier
TEXT_PRIMARY = "#f0f6fc"
TEXT_SECONDARY = "#8b949e"

TIER_COLORS: dict[str, str] = {
    "S": ACCENT_PURPLE,
    "A": ACCENT_BLUE,
    "B": ACCENT_GREEN,
    "C": ACCENT_YELLOW,
    "D": ACCENT_RED,
}

DIM_COLORS: dict[str, str] = {
    "benchmarks":     "#6366f1",
    "efficiency":     "#22c55e",
    "community":      "#f59e0b",
    "recency":        "#06b6d4",
    "reproducibility":"#ec4899",
}

DIM_LABELS: dict[str, str] = {
    "benchmarks":     "🧠 Benchmarks",
    "efficiency":     "⚡ Efficiency",
    "community":      "🔥 Community",
    "recency":        "🕐 Recency",
    "reproducibility":"✅ Reproducibility",
}

API_BASE = os.getenv("MODELRANK_API", "http://localhost:8000")

# ────────────────────────────────────────────────────────────────────────────
# Data fetching
# ────────────────────────────────────────────────────────────────────────────

def fetch_score(model_id: str) -> Optional[dict]:
    """Fetch model score from the ModelRank API."""
    if not REQUESTS_AVAILABLE:
        print("WARNING: 'requests' not installed. Using mock data.")
        return _mock_score(model_id)
    try:
        url = f"{API_BASE}/score/{model_id}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        print(f"WARNING: Cannot reach ModelRank API at {API_BASE}. Using mock data.")
        return _mock_score(model_id)
    except requests.HTTPError as e:
        print(f"WARNING: API returned {e.response.status_code} for {model_id}. Using mock data.")
        return _mock_score(model_id)
    except Exception as e:
        print(f"WARNING: Unexpected error: {e}. Using mock data.")
        return _mock_score(model_id)


def fetch_leaderboard(limit: int = 10) -> list[dict]:
    """Fetch top N models from the leaderboard."""
    if not REQUESTS_AVAILABLE:
        return []
    try:
        url = f"{API_BASE}/leaderboard?limit={limit}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"WARNING: Could not fetch leaderboard: {e}")
        return []


def _mock_score(model_id: str) -> dict:
    """Return plausible mock data when the API is offline."""
    return {
        "model_id": model_id,
        "composite": 78.4,
        "tier": "B",
        "global_rank": 42,
        "breakdown": {
            "benchmarks": 80.1,
            "efficiency": 91.3,
            "community": 65.0,
            "recency": 72.0,
            "reproducibility": 0.0,
        },
        "elo": 1205,
    }

# ────────────────────────────────────────────────────────────────────────────
# Image generation
# ────────────────────────────────────────────────────────────────────────────

def hex_to_rgb(h: str) -> tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def draw_rounded_rect(
    draw: "ImageDraw.ImageDraw",
    xy: tuple[int, int, int, int],
    radius: int,
    fill: str,
) -> None:
    """Draw a rounded rectangle on an ImageDraw canvas."""
    x1, y1, x2, y2 = xy
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.ellipse([x1, y1, x1 + 2*radius, y1 + 2*radius], fill=fill)
    draw.ellipse([x2 - 2*radius, y1, x2, y1 + 2*radius], fill=fill)
    draw.ellipse([x1, y2 - 2*radius, x1 + 2*radius, y2], fill=fill)
    draw.ellipse([x2 - 2*radius, y2 - 2*radius, x2, y2], fill=fill)


def load_font(size: int, bold: bool = False) -> "ImageFont.FreeTypeFont":
    """Load a system font, falling back to default if unavailable."""
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate_png(score_data: dict, output_path: Path) -> None:
    """Generate a Model DNA card PNG image."""
    if not PIL_AVAILABLE:
        print("ERROR: Pillow is required for PNG generation. Run: pip install pillow")
        sys.exit(1)

    model_id: str = score_data.get("model_id", "unknown/model")
    composite: float = score_data.get("composite", 0.0)
    tier: str = score_data.get("tier", "D")
    rank: int = score_data.get("global_rank", 0)
    breakdown: dict = score_data.get("breakdown", {})
    elo: int = score_data.get("elo", 1200)
    tier_color = TIER_COLORS.get(tier, ACCENT_RED)

    # Create image
    img = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(BG_COLOR))
    draw = ImageDraw.Draw(img)

    # Top gradient bar (simulate with colored rectangles)
    gradient_colors = [ACCENT_PURPLE, ACCENT_BLUE, ACCENT_GREEN]
    bar_h = 6
    seg_w = WIDTH // len(gradient_colors)
    for i, col in enumerate(gradient_colors):
        draw.rectangle([i * seg_w, 0, (i + 1) * seg_w, bar_h], fill=hex_to_rgb(col))

    # ModelRank logo (top-left)
    logo_font = load_font(18, bold=True)
    draw.text((24, 20), "ModelRank", font=logo_font, fill=hex_to_rgb(ACCENT_PURPLE))
    draw.text((24, 42), "Independent LLM Standard", font=load_font(11), fill=hex_to_rgb(TEXT_SECONDARY))

    # Model name (large, center-left)
    parts = model_id.split("/")
    org = parts[0] if len(parts) > 1 else ""
    name = parts[1] if len(parts) > 1 else model_id

    org_font = load_font(14)
    name_font = load_font(28, bold=True)
    draw.text((24, 80), org, font=org_font, fill=hex_to_rgb(TEXT_SECONDARY))
    # Truncate long names
    display_name = name if len(name) <= 28 else name[:25] + "..."
    draw.text((24, 100), display_name, font=name_font, fill=hex_to_rgb(TEXT_PRIMARY))

    # Composite score (right side, large)
    score_font = load_font(72, bold=True)
    tier_font = load_font(42, bold=True)
    score_str = f"{composite:.1f}"
    draw.text((WIDTH - 200, 70), score_str, font=score_font, fill=hex_to_rgb(TEXT_PRIMARY))

    # Tier badge
    draw_rounded_rect(draw, (WIDTH - 120, 155, WIDTH - 30, 200), 12, tier_color)
    draw.text((WIDTH - 95, 160), f"Tier {tier}", font=load_font(20, bold=True), fill=(255, 255, 255))

    # Global rank
    rank_text = f"#{rank} Global" if rank else "Unranked"
    draw.text((WIDTH - 200, 210), rank_text, font=load_font(14), fill=hex_to_rgb(TEXT_SECONDARY))
    draw.text((WIDTH - 200, 230), f"ELO {elo}", font=load_font(14), fill=hex_to_rgb(TEXT_SECONDARY))

    # Dimension bars
    dims = ["benchmarks", "efficiency", "community", "recency"]
    bar_start_y = 185
    bar_x = 24
    bar_w_max = 360
    bar_h_dim = 18
    spacing = 34

    draw.text((bar_x, bar_start_y - 24), "SCORE BREAKDOWN", font=load_font(11), fill=hex_to_rgb(TEXT_SECONDARY))

    for i, dim in enumerate(dims):
        val = breakdown.get(dim, 0.0)
        y = bar_start_y + i * spacing
        color = DIM_COLORS.get(dim, "#ffffff")
        label = DIM_LABELS.get(dim, dim)

        # Background track
        draw.rectangle([bar_x, y, bar_x + bar_w_max, y + bar_h_dim],
                        fill=(*hex_to_rgb("#21262d"), ))

        # Filled portion
        fill_w = int(bar_w_max * (val / 100))
        if fill_w > 0:
            draw_rounded_rect(draw, (bar_x, y, bar_x + fill_w, y + bar_h_dim), 4, color)

        # Label + value
        draw.text((bar_x, y - 14), label, font=load_font(11), fill=hex_to_rgb(TEXT_SECONDARY))
        draw.text((bar_x + bar_w_max + 8, y), f"{val:.1f}", font=load_font(12, bold=True), fill=hex_to_rgb(TEXT_PRIMARY))

    # Footer
    footer_y = HEIGHT - 36
    draw.line([(0, footer_y - 8), (WIDTH, footer_y - 8)], fill=hex_to_rgb("#21262d"), width=1)
    draw.text((24, footer_y), "rankmodel.github.io", font=load_font(11), fill=hex_to_rgb(TEXT_SECONDARY))
    draw.text((WIDTH - 280, footer_y), "Free badge: rankmodel.github.io/badges", font=load_font(11), fill=hex_to_rgb(TEXT_SECONDARY))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG", optimize=True)
    print(f"✅ DNA card saved: {output_path}")


# ────────────────────────────────────────────────────────────────────────────
# HTML embed code generation
# ────────────────────────────────────────────────────────────────────────────

def generate_html_embed(score_data: dict, model_id: str) -> str:
    """Generate an HTML embed snippet for the model DNA card."""
    composite = score_data.get("composite", 0.0)
    tier = score_data.get("tier", "D")
    tier_color = TIER_COLORS.get(tier, ACCENT_RED)
    slug = model_id.replace("/", "_")

    return textwrap.dedent(f"""\
    <!-- ModelRank DNA Card for {model_id} -->
    <!-- Paste this into your model README or website -->
    <a href="https://rankmodel.github.io/model/{model_id}" target="_blank" rel="noopener">
      <img
        src="https://rankmodel.github.io/badges/{model_id}/dna.png"
        alt="ModelRank DNA Card — {model_id} — Score: {composite:.1f} Tier: {tier}"
        width="400"
        style="border-radius: 8px;"
      />
    </a>
    
    <!-- Or use the live badge (always up to date): -->
    [![ModelRank Score](https://rankmodel.github.io/badges/{model_id}/score.svg)](https://rankmodel.github.io)
    [![ModelRank Tier](https://rankmodel.github.io/badges/{model_id}/tier.svg)](https://rankmodel.github.io)
    """)


# ────────────────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Model DNA Card — a shareable scorecard for any LLM.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        Examples:
          python scripts/generate_model_dna.py mistralai/Mistral-7B-v0.1
          python scripts/generate_model_dna.py meta-llama/Llama-3.1-8B --format html
          python scripts/generate_model_dna.py --batch top10
        """),
    )
    parser.add_argument(
        "model_id",
        nargs="?",
        help="HuggingFace model ID (e.g., mistralai/Mistral-7B-v0.1)",
    )
    parser.add_argument(
        "--format",
        choices=["png", "html", "both"],
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "--output",
        help="Output path for PNG (default: brand/dna/<slug>.png)",
    )
    parser.add_argument(
        "--batch",
        choices=["top10", "top25"],
        help="Generate DNA cards for top N models from the leaderboard",
    )
    parser.add_argument(
        "--api",
        default=API_BASE,
        help=f"ModelRank API base URL (default: {API_BASE})",
    )
    args = parser.parse_args()

    if not args.model_id and not args.batch:
        parser.print_help()
        sys.exit(1)

    model_ids: list[str] = []

    if args.batch:
        limit = 10 if args.batch == "top10" else 25
        print(f"Fetching top {limit} models from leaderboard...")
        entries = fetch_leaderboard(limit)
        if not entries:
            print("ERROR: Could not fetch leaderboard. Is the API running?")
            sys.exit(1)
        model_ids = [e.get("model_id", "") for e in entries if e.get("model_id")]
        print(f"  Found {len(model_ids)} models to process.")
    else:
        model_ids = [args.model_id]

    for mid in model_ids:
        print(f"\nProcessing: {mid}")

        score_data = fetch_score(mid)
        if not score_data:
            print(f"  SKIP: No score data found for {mid}")
            continue

        slug = mid.replace("/", "_")
        output_path = Path(args.output) if args.output else Path(f"brand/dna/{slug}.png")

        if args.format in ("png", "both"):
            generate_png(score_data, output_path)

        if args.format in ("html", "both"):
            embed = generate_html_embed(score_data, mid)
            print("\n📋 HTML embed code:")
            print("─" * 60)
            print(embed)
            print("─" * 60)

    print(f"\n🎉 Done! Share your model's DNA card at rankmodel.github.io")


if __name__ == "__main__":
    main()
