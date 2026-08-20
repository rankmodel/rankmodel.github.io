#!/usr/bin/env python3
"""
ModelRank — Social Preview / OG Image Generator
================================================
Renders a 1200x630px OG image (the universal standard for GitHub, Twitter,
LinkedIn and Slack link previews) plus an HTML/CSS fallback.

Design: premium split layout — dark editorial left column (logo lockup,
headline, tagline, footer) and a brand-gradient panel on the right carrying
the "leaderboard" motif (ascending ranked bars + star).

Usage:
  python scripts/generate_social_preview.py
  python scripts/generate_social_preview.py --output assets/social-preview.png

Dependencies:
  pip install pillow
"""

import argparse
import math
import os
import sys
import textwrap
from pathlib import Path

W, H = 1200, 630

INDIGO = (76, 29, 149)      # #4c1d95
BLUE   = (37, 99, 235)      # #2563eb
DARK   = (10, 11, 20)       # #0a0b14
DARK2  = (17, 19, 32)       # #111320
MUTED  = (148, 163, 184)    # #94a3b8
WHITE  = (255, 255, 255)
ACCENT = (165, 180, 252)    # #a5b4fc
GREEN  = (74, 222, 128)     # #4ade80

# Logo mark geometry (512 coordinate space)
BARS = [(150, 300, 64, 100), (234, 250, 64, 150), (318, 190, 64, 210)]
STAR_C = (350, 150)
STAR_PTS = [(math.radians(-90 + i * 36), 46 if i % 2 == 0 else 19) for i in range(10)]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_font(size, bold=True):
    from PIL import ImageFont
    cand = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    if not bold:
        cand = [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ] + cand
    for p in cand:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _grad_pixels(draw, x0, y0, w, h, c1, c2):
    for yy in range(h):
        for xx in range(w):
            t = max(0.0, min(1.0, xx / max(w, 1) * 0.6 + yy / max(h, 1) * 0.4))
            draw.point((x0 + xx, y0 + yy), (
                int(c1[0] + (c2[0] - c1[0]) * t),
                int(c1[1] + (c2[1] - c1[1]) * t),
                int(c1[2] + (c2[2] - c1[2]) * t),
            ))


def _rounded_gradient(img, box, c1, c2, radius):
    from PIL import Image, ImageDraw
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    tmp = Image.new("RGB", (w, h))
    _grad_pixels(ImageDraw.Draw(tmp), 0, 0, w, h, c1, c2)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    img.paste(tmp, (x0, y0), mask)


def _draw_mark(draw, x, y, size, color=WHITE):
    s = size / 512.0
    for (bx, by, bw, bh) in BARS:
        draw.rounded_rectangle(
            [x + bx * s, y + by * s, x + (bx + bw) * s, y + (by + bh) * s],
            radius=14 * s, fill=color,
        )
    star = [(x + (STAR_C[0] + rad * math.cos(a)) * s,
             y + (STAR_C[1] + rad * math.sin(a)) * s) for a, rad in STAR_PTS]
    draw.polygon(star, fill=color)


def _draw_logo_lockup(img, x, y, size):
    from PIL import ImageDraw
    _rounded_gradient(img, (x, y, x + size, y + size), INDIGO, BLUE, int(size * 0.22))
    _draw_mark(ImageDraw.Draw(img), x, y, size, WHITE)


# ─────────────────────────────────────────────────────────────────────────────
# PNG generator
# ─────────────────────────────────────────────────────────────────────────────

def generate_png(output_path: Path) -> None:
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W, H), DARK)
    draw = ImageDraw.Draw(img)

    # subtle top accent bar
    _grad_pixels(draw, 0, 0, W, 8, INDIGO, BLUE)

    # ── Right brand-gradient panel carrying the leaderboard motif ──────────────
    px0, py0, pw, ph = 690, 44, 470, H - 88
    _rounded_gradient(img, (px0, py0, px0 + pw, py0 + ph), INDIGO, BLUE, 28)

    baseline = py0 + ph - 96
    bar_area_w = pw - 130
    n = 5
    bw = 42
    gap = (bar_area_w - n * bw) / (n - 1)
    start_x = px0 + 65
    heights = [120, 168, 216, 264, 312]
    for i in range(n):
        bx = start_x + i * (bw + gap)
        top = baseline - heights[i]
        draw.rounded_rectangle([bx, top, bx + bw, baseline], radius=10, fill=WHITE)
    # star atop the tallest bar
    tall_cx = start_x + (n - 1) * (bw + gap) + bw / 2
    star_cy = baseline - heights[-1] - 34
    sr_out, sr_in = 26, 11
    star = []
    for i in range(10):
        ang = math.radians(-90 + i * 36)
        rad = sr_out if i % 2 == 0 else sr_in
        star.append((tall_cx + rad * math.cos(ang), star_cy + rad * math.sin(ang)))
    draw.polygon(star, fill=WHITE)
    # panel label
    lbl = _load_font(15)
    draw.text((px0 + 65, py0 + 40), "5-DIMENSION SCORE", font=lbl, fill=(226, 232, 240))

    # ── Left editorial column ──────────────────────────────────────────────────
    _draw_logo_lockup(img, 60, 56, 72)
    wm = _load_font(38)
    sub = _load_font(16)
    draw.text((60 + 72 + 20, 60), "ModelRank", font=wm, fill=WHITE)
    draw.text((60 + 72 + 20, 106), "rankmodel.github.io", font=sub, fill=MUTED)

    h1 = _load_font(58)
    h2 = _load_font(58)
    draw.text((60, 232), "The independent leaderboard", font=h1, fill=WHITE)
    draw.text((60, 300), "for open AI models.", font=h2, fill=ACCENT)

    tag = _load_font(21)
    draw.text((60, 402), "Ranked across 5 dimensions. Zero paid placements.", font=tag, fill=MUTED)
    draw.text((60, 436), "Verifiable by anyone, anywhere.", font=tag, fill=MUTED)

    foot = _load_font(15)
    draw.text((60, 560), "github.com/rankmodel", font=foot, fill=MUTED)
    cta = _load_font(17)
    draw.text((W - 470, 560), "Free badges for your README  →", font=cta, fill=GREEN)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG", optimize=True)
    print(f"✅  Social preview saved → {output_path}  ({W}x{H}px)")


# ─────────────────────────────────────────────────────────────────────────────
# HTML/CSS fallback (pixel-matched)
# ─────────────────────────────────────────────────────────────────────────────

def generate_html(output_path: Path) -> None:
    html = textwrap.dedent("""\
    <!DOCTYPE html>
    <html lang="en"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=1200">
    <title>ModelRank Social Preview</title>
    <style>
      * { margin:0; padding:0; box-sizing:border-box; }
      body { width:1200px; height:630px; background:#0a0b14; overflow:hidden;
             font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; color:#fff; }
      .top { height:8px; background:linear-gradient(90deg,#4c1d95,#2563eb); }
      .panel { position:absolute; right:44px; top:44px; width:470px; height:542px;
               border-radius:28px; background:linear-gradient(135deg,#4c1d95,#2563eb); }
      .panel-label { position:absolute; left:65px; top:84px; color:#e2e8f0; font-size:15px; letter-spacing:1px; }
      .lockup { position:absolute; left:60px; top:56px; width:72px; height:72px; border-radius:16px;
                background:linear-gradient(135deg,#4c1d95,#2563eb); }
      .wm { position:absolute; left:152px; top:60px; font-size:38px; font-weight:800; }
      .sub { position:absolute; left:152px; top:106px; color:#94a3b8; font-size:16px; }
      .h1 { position:absolute; left:60px; top:232px; font-size:58px; font-weight:800; }
      .h2 { position:absolute; left:60px; top:300px; font-size:58px; font-weight:800; color:#a5b4fc; }
      .t1 { position:absolute; left:60px; top:402px; color:#94a3b8; font-size:21px; }
      .t2 { position:absolute; left:60px; top:436px; color:#94a3b8; font-size:21px; }
      .foot { position:absolute; left:60px; top:560px; color:#94a3b8; font-size:15px; }
      .cta { position:absolute; left:730px; top:560px; color:#4ade80; font-size:17px; font-weight:600; }
    </style></head><body>
      <div class="top"></div>
      <div class="panel"></div>
      <div class="panel-label">5-DIMENSION SCORE</div>
      <div class="lockup"></div>
      <div class="wm">ModelRank</div>
      <div class="sub">rankmodel.github.io</div>
      <div class="h1">The independent leaderboard</div>
      <div class="h2">for open AI models.</div>
      <div class="t1">Ranked across 5 dimensions. Zero paid placements.</div>
      <div class="t2">Verifiable by anyone, anywhere.</div>
      <div class="foot">github.com/rankmodel</div>
      <div class="cta">Free badges for your README  →</div>
    </body></html>
    """)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"✅  HTML fallback saved → {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the ModelRank OG social preview.")
    parser.add_argument("--output", "-o", default="assets/social-preview.png")
    parser.add_argument("--html-output", default="brand/social_preview.html")
    parser.add_argument("--html-only", action="store_true")
    parser.add_argument("--png-only", action="store_true")
    args = parser.parse_args()

    print("\n🎨  ModelRank Social Preview Generator")
    if not args.html_only:
        try:
            generate_png(Path(args.output))
            # keep og-image and brand copy in sync
            for extra in ["assets/og-image.png", "brand/social_preview.png"]:
                if extra != str(args.output):
                    generate_png(Path(extra))
        except Exception as e:
            print(f"⚠️   PNG generation failed: {e}")
    if not args.png_only:
        try:
            generate_html(Path(args.html_output))
        except Exception as e:
            print(f"⚠️   HTML generation failed: {e}")


if __name__ == "__main__":
    main()
