#!/usr/bin/env python3
"""
ModelRank — Social Preview Card Generator
==========================================
Generates a 1200×630px OG image (the universal standard for GitHub, Twitter,
LinkedIn, and Slack link previews) and an HTML/CSS fallback.

Usage:
  python scripts/generate_social_preview.py
  python scripts/generate_social_preview.py --output brand/custom_preview.png
  python scripts/generate_social_preview.py --html-only

Dependencies:
  pip install pillow
"""

import argparse
import os
import sys
import textwrap
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# Design tokens
# ─────────────────────────────────────────────────────────────────────────────

W, H = 1200, 630

C = {
    "bg":          (13, 17, 23),       # #0d1117  GitHub dark
    "bg2":         (22, 27, 34),       # #161b22  card bg
    "border":      (48, 54, 61),       # #30363d  divider
    "purple":      (168, 85, 247),     # #a855f7  S-tier / brand
    "blue":        (59, 130, 246),     # #3b82f6  A-tier
    "green":       (34, 197, 94),      # #22c55e  B-tier / efficiency
    "yellow":      (234, 179, 8),      # #eab308  C-tier
    "red":         (239, 68, 68),      # #ef4444  D-tier
    "indigo":      (99, 102, 241),     # #6366f1  benchmarks
    "cyan":        (6, 182, 212),      # #06b6d4  recency
    "amber":       (245, 158, 11),     # #f59e0b  community
    "text":        (240, 246, 252),    # #f0f6fc  primary text
    "muted":       (139, 148, 158),    # #8b949e  secondary text
    "white":       (255, 255, 255),
}

MODELS_TICKER = [
    ("Mistral-7B",    82, "A"),
    ("Llama-3.1-8B",  80, "A"),
    ("GPT-4o",        91, "S"),
    ("Qwen2.5-7B",    84, "A"),
    ("DeepSeek-R1",   88, "S"),
]

TIER_COLORS = {"S": C["purple"], "A": C["blue"], "B": C["green"],
               "C": C["yellow"], "D": C["red"]}

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_font(size: int, bold: bool = False):
    """Load a system TrueType font, degrading gracefully to the default."""
    from PIL import ImageFont
    candidates_bold = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]
    candidates_regular = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    for path in (candidates_bold if bold else candidates_regular):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_rounded_rect(draw, xy: tuple, radius: int, fill: tuple,
                        outline: Optional[tuple] = None, width: int = 1) -> None:
    """Draw a rounded rectangle (Pillow doesn't have native support pre-10.x)."""
    x1, y1, x2, y2 = xy
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.ellipse([x1, y1, x1 + radius*2, y1 + radius*2], fill=fill)
    draw.ellipse([x2 - radius*2, y1, x2, y1 + radius*2], fill=fill)
    draw.ellipse([x1, y2 - radius*2, x1 + radius*2, y2], fill=fill)
    draw.ellipse([x2 - radius*2, y2 - radius*2, x2, y2], fill=fill)
    if outline:
        draw.arc([x1, y1, x1 + radius*2, y1 + radius*2], 180, 270, fill=outline, width=width)
        draw.arc([x2 - radius*2, y1, x2, y1 + radius*2], 270, 360, fill=outline, width=width)
        draw.arc([x1, y2 - radius*2, x1 + radius*2, y2], 90, 180, fill=outline, width=width)
        draw.arc([x2 - radius*2, y2 - radius*2, x2, y2], 0, 90, fill=outline, width=width)
        draw.line([x1 + radius, y1, x2 - radius, y1], fill=outline, width=width)
        draw.line([x1 + radius, y2, x2 - radius, y2], fill=outline, width=width)
        draw.line([x1, y1 + radius, x1, y2 - radius], fill=outline, width=width)
        draw.line([x2, y1 + radius, x2, y2 - radius], fill=outline, width=width)


def _draw_gradient_bar(draw, x1: int, y1: int, x2: int, y2: int,
                        colors: list[tuple]) -> None:
    """Draw a horizontal gradient by blending N color stops."""
    total_w = x2 - x1
    seg_w = total_w // (len(colors) - 1)
    for i in range(len(colors) - 1):
        c_start = colors[i]
        c_end = colors[i + 1]
        seg_x1 = x1 + i * seg_w
        seg_x2 = seg_x1 + seg_w
        for px in range(seg_x1, min(seg_x2, x2)):
            t = (px - seg_x1) / max(seg_w, 1)
            r = int(c_start[0] + t * (c_end[0] - c_start[0]))
            g = int(c_start[1] + t * (c_end[1] - c_start[1]))
            b = int(c_start[2] + t * (c_end[2] - c_start[2]))
            draw.line([(px, y1), (px, y2)], fill=(r, g, b))


# ─────────────────────────────────────────────────────────────────────────────
# PNG generator
# ─────────────────────────────────────────────────────────────────────────────

def generate_png(output_path: Path) -> None:
    """Render the 1200×630 social preview card as a PNG."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("ERROR: Pillow is required.  Run: pip install pillow")
        sys.exit(1)

    img = Image.new("RGB", (W, H), C["bg"])
    draw = ImageDraw.Draw(img)

    # ── Top gradient bar ──────────────────────────────────────────────────────
    _draw_gradient_bar(draw, 0, 0, W, 8,
                       [C["purple"], C["blue"], C["green"], C["cyan"]])

    # ── Background card panel ─────────────────────────────────────────────────
    _draw_rounded_rect(draw, (40, 30, W - 40, H - 30), 16, C["bg2"])

    # ── Logo — top-left ───────────────────────────────────────────────────────
    logo_font   = _load_font(26, bold=True)
    sub_font    = _load_font(14)
    draw.text((72, 58), "ModelRank", font=logo_font, fill=C["purple"])
    draw.text((72, 90), "rankmodel.github.io", font=sub_font, fill=C["muted"])

    # ── Independence pill — top-right ─────────────────────────────────────────
    pill_label  = "100% Independent · Zero Paid Placements"
    pill_font   = _load_font(13)
    pill_w      = 320
    _draw_rounded_rect(draw, (W - 72 - pill_w, 60, W - 72, 86), 13,
                       (30, 38, 50), outline=C["border"])
    draw.text((W - 72 - pill_w + 12, 66), pill_label,
              font=pill_font, fill=C["muted"])

    # ── Main headline ─────────────────────────────────────────────────────────
    h1_font = _load_font(88, bold=True)
    h2_font = _load_font(60, bold=True)
    tag_font = _load_font(22)

    draw.text((72, 145), "STOP GUESSING.", font=h1_font, fill=C["text"])
    draw.text((72, 248), "START RANKING.", font=h2_font, fill=C["purple"])

    tagline = "The Independent LLM Standard.  150+ Models.  5 Dimensions.  Zero Bias."
    draw.text((72, 330), tagline, font=tag_font, fill=C["muted"])

    # ── Divider ───────────────────────────────────────────────────────────────
    draw.line([(72, 375), (W - 72, 375)], fill=C["border"], width=1)

    # ── Model score ticker pills ──────────────────────────────────────────────
    pill_y      = 395
    pill_h      = 50
    pill_gap    = 14
    ticker_font = _load_font(15, bold=True)
    tier_font   = _load_font(13, bold=True)
    cur_x       = 72

    for name, score, tier in MODELS_TICKER:
        tier_color = TIER_COLORS.get(tier, C["muted"])
        label      = f" {name}  {score}"
        # Estimate pill width: ~9px per char average
        est_w = max(len(label) * 9 + 54, 120)
        if cur_x + est_w > W - 72:
            break
        # Background pill
        _draw_rounded_rect(draw, (cur_x, pill_y, cur_x + est_w, pill_y + pill_h),
                           10, (30, 38, 50), outline=C["border"])
        # Tier color dot
        draw.ellipse([cur_x + 12, pill_y + 17, cur_x + 24, pill_y + 29],
                     fill=tier_color)
        # Model name + score
        draw.text((cur_x + 32, pill_y + 14), f"{name}  {score}",
                  font=ticker_font, fill=C["text"])
        # Tier letter badge
        badge_x = cur_x + est_w - 28
        _draw_rounded_rect(draw, (badge_x, pill_y + 11, badge_x + 20, pill_y + 37),
                           4, tier_color)
        draw.text((badge_x + 4, pill_y + 14), tier, font=tier_font, fill=C["white"])
        cur_x += est_w + pill_gap

    # ── Bottom bar ────────────────────────────────────────────────────────────
    bar_y = H - 80
    draw.rectangle([40, bar_y, W - 40, bar_y + 1], fill=C["border"])

    footer_font = _load_font(14)
    star_font   = _load_font(16, bold=True)
    draw.text((72, bar_y + 16), "⭐  github.com/rankmodel/rankmodel.github.io",
              font=footer_font, fill=C["muted"])
    draw.text((W - 340, bar_y + 14), "Free embeddable badges for your models →",
              font=star_font, fill=C["green"])

    # ── Right-side dimension bars (decorative) ────────────────────────────────
    dim_data = [
        ("Benchmarks", 0.87, C["indigo"]),
        ("Efficiency",  0.91, C["green"]),
        ("Community",   0.74, C["amber"]),
        ("Recency",     0.82, C["cyan"]),
    ]
    bar_x1     = W - 310
    bar_x2     = W - 60
    bar_bw     = bar_x2 - bar_x1
    dim_y_start = 145
    dim_spacing = 48
    dim_label_f = _load_font(13)
    dim_val_f   = _load_font(13, bold=True)

    for i, (label, val, color) in enumerate(dim_data):
        dy = dim_y_start + i * dim_spacing
        # Track
        _draw_rounded_rect(draw, (bar_x1, dy + 18, bar_x2, dy + 32), 4, C["border"])
        # Fill
        fill_w = int(bar_bw * val)
        if fill_w > 8:
            _draw_rounded_rect(draw, (bar_x1, dy + 18, bar_x1 + fill_w, dy + 32),
                               4, color)
        draw.text((bar_x1, dy), label, font=dim_label_f, fill=C["muted"])
        draw.text((bar_x2 + 6, dy + 16), f"{int(val*100)}", font=dim_val_f, fill=C["text"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG", optimize=True)
    print(f"✅  Social preview saved → {output_path}  ({W}×{H}px)")
    print(f"    Upload to: GitHub repo Settings → Social Preview → Upload image")


# ─────────────────────────────────────────────────────────────────────────────
# HTML/CSS fallback generator
# ─────────────────────────────────────────────────────────────────────────────

def generate_html(output_path: Path) -> None:
    """Write a pixel-accurate HTML/CSS version (screenshot with any browser)."""
    html = textwrap.dedent("""\
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=1200">
      <title>ModelRank Social Preview</title>
      <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { width: 1200px; height: 630px; background: #0d1117;
               font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               overflow: hidden; }
        .bar { height: 8px;
               background: linear-gradient(90deg, #a855f7, #3b82f6, #22c55e, #06b6d4); }
        .card { margin: 30px 40px; padding: 28px 32px;
                background: #161b22; border-radius: 16px;
                height: calc(630px - 60px);
                border: 1px solid #30363d; position: relative; }
        .logo { color: #a855f7; font-size: 26px; font-weight: 700; }
        .logo-sub { color: #8b949e; font-size: 13px; margin-top: 2px; }
        .indie-pill { position: absolute; top: 28px; right: 32px;
                      border: 1px solid #30363d; border-radius: 14px;
                      padding: 6px 14px; color: #8b949e; font-size: 12px; }
        .h1 { font-size: 88px; font-weight: 800; color: #f0f6fc;
               line-height: 1; margin-top: 30px; letter-spacing: -2px; }
        .h2 { font-size: 60px; font-weight: 800; color: #a855f7;
               line-height: 1; margin-top: 8px; letter-spacing: -1px; }
        .tagline { color: #8b949e; font-size: 18px; margin-top: 18px; }
        .divider { height: 1px; background: #30363d; margin: 22px 0; }
        .ticker { display: flex; gap: 12px; flex-wrap: wrap; }
        .pill { display: flex; align-items: center; gap: 8px;
                background: #1e2631; border: 1px solid #30363d;
                border-radius: 10px; padding: 10px 14px; font-size: 14px; }
        .dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
        .pill-name { color: #f0f6fc; font-weight: 600; }
        .tier-badge { border-radius: 4px; padding: 2px 6px;
                      font-weight: 700; font-size: 12px; color: #fff; }
        .bottom { position: absolute; bottom: 28px; left: 32px; right: 32px;
                  display: flex; justify-content: space-between; align-items: center;
                  border-top: 1px solid #30363d; padding-top: 16px; }
        .bottom-left { color: #8b949e; font-size: 13px; }
        .bottom-right { color: #22c55e; font-size: 14px; font-weight: 600; }
        .dims { position: absolute; right: 32px; top: 120px; width: 250px; }
        .dim-row { margin-bottom: 20px; }
        .dim-label { color: #8b949e; font-size: 12px; margin-bottom: 4px;
                     display: flex; justify-content: space-between; }
        .dim-track { background: #30363d; border-radius: 4px; height: 10px; }
        .dim-fill { height: 10px; border-radius: 4px; }
      </style>
    </head>
    <body>
      <div class="bar"></div>
      <div class="card">
        <div class="logo">ModelRank</div>
        <div class="logo-sub">rankmodel.github.io</div>
        <div class="indie-pill">100% Independent &middot; Zero Paid Placements</div>

        <div class="h1">STOP GUESSING.</div>
        <div class="h2">START RANKING.</div>
        <p class="tagline">The Independent LLM Standard. &nbsp;150+ Models. &nbsp;5 Dimensions. &nbsp;Zero Bias.</p>
        <div class="divider"></div>

        <div class="ticker">
          <div class="pill">
            <div class="dot" style="background:#3b82f6"></div>
            <span class="pill-name">Mistral-7B &nbsp;82</span>
            <span class="tier-badge" style="background:#3b82f6">A</span>
          </div>
          <div class="pill">
            <div class="dot" style="background:#3b82f6"></div>
            <span class="pill-name">Llama-3.1-8B &nbsp;80</span>
            <span class="tier-badge" style="background:#3b82f6">A</span>
          </div>
          <div class="pill">
            <div class="dot" style="background:#a855f7"></div>
            <span class="pill-name">GPT-4o &nbsp;91</span>
            <span class="tier-badge" style="background:#a855f7">S</span>
          </div>
          <div class="pill">
            <div class="dot" style="background:#3b82f6"></div>
            <span class="pill-name">Qwen2.5-7B &nbsp;84</span>
            <span class="tier-badge" style="background:#3b82f6">A</span>
          </div>
          <div class="pill">
            <div class="dot" style="background:#a855f7"></div>
            <span class="pill-name">DeepSeek-R1 &nbsp;88</span>
            <span class="tier-badge" style="background:#a855f7">S</span>
          </div>
        </div>

        <div class="dims">
          <div class="dim-row">
            <div class="dim-label"><span>Benchmarks</span><span style="color:#f0f6fc">87</span></div>
            <div class="dim-track"><div class="dim-fill" style="width:87%;background:#6366f1"></div></div>
          </div>
          <div class="dim-row">
            <div class="dim-label"><span>Efficiency</span><span style="color:#f0f6fc">91</span></div>
            <div class="dim-track"><div class="dim-fill" style="width:91%;background:#22c55e"></div></div>
          </div>
          <div class="dim-row">
            <div class="dim-label"><span>Community</span><span style="color:#f0f6fc">74</span></div>
            <div class="dim-track"><div class="dim-fill" style="width:74%;background:#f59e0b"></div></div>
          </div>
          <div class="dim-row">
            <div class="dim-label"><span>Recency</span><span style="color:#f0f6fc">82</span></div>
            <div class="dim-track"><div class="dim-fill" style="width:82%;background:#06b6d4"></div></div>
          </div>
        </div>

        <div class="bottom">
          <span class="bottom-left">⭐ github.com/rankmodel/rankmodel.github.io</span>
          <span class="bottom-right">Free embeddable badges for your models &rarr;</span>
        </div>
      </div>
    </body>
    </html>
    """)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"✅  HTML fallback saved → {output_path}")
    print(f"    Screenshot at 1200×630 with: chrome --headless --screenshot={output_path.with_suffix('.png')} {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the ModelRank 1200×630 OG social preview card.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        After generation:
          1. Go to GitHub → Settings → Social Preview → Upload image
          2. Upload brand/social_preview.png
          3. The image will appear on all GitHub, Twitter, and LinkedIn link cards.
        """),
    )
    parser.add_argument(
        "--output", "-o",
        default="brand/social_preview.png",
        help="Output PNG path (default: brand/social_preview.png)",
    )
    parser.add_argument(
        "--html-output",
        default="brand/social_preview.html",
        help="Output HTML path (default: brand/social_preview.html)",
    )
    parser.add_argument(
        "--html-only",
        action="store_true",
        help="Skip PNG generation; only write the HTML/CSS fallback",
    )
    parser.add_argument(
        "--png-only",
        action="store_true",
        help="Skip HTML generation; only write the PNG",
    )
    args = parser.parse_args()

    print("\n🎨  ModelRank Social Preview Generator")
    print("=" * 42)

    if not args.html_only:
        try:
            generate_png(Path(args.output))
        except SystemExit:
            raise
        except Exception as e:
            print(f"⚠️   PNG generation failed: {e}")
            print("    Falling back to HTML-only mode.")
            args.html_only = True

    if not args.png_only:
        try:
            generate_html(Path(args.html_output))
        except Exception as e:
            print(f"⚠️   HTML generation failed: {e}")

    print("\n📋  Next steps:")
    print("    1. Open brand/social_preview.html in a browser to verify design")
    print("    2. Upload brand/social_preview.png to GitHub → Settings → Social Preview")
    print("    3. The CI action .github/workflows/social-preview.yml keeps it fresh automatically")


if __name__ == "__main__":
    main()
