#!/usr/bin/env python3
"""
ModelRank Static Asset Generator
=================================
Generates static files for GitHub Pages deployment:

  static_output/
  ├── index.html              ← Leaderboard landing page
  ├── leaderboard.json        ← Full leaderboard data (for API consumers)
  ├── badges/
  │   ├── {org}/{model}/score.svg
  │   ├── {org}/{model}/tier.svg
  │   ├── {org}/{model}/rank.svg
  │   └── {org}/{model}/shields.json   ← Shields.io endpoint
  └── models/
      └── {org}/{model}.json  ← Per-model score data

Usage:
    python scripts/generate_static_assets.py
    python scripts/generate_static_assets.py --limit 100
"""
import os
import sys
import json
import base64
import argparse
import pathlib
import logging

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)

OUTPUT_DIR = pathlib.Path('static_output')

TIER_COLORS = {
    'S': '#a855f7',
    'A': '#3b82f6',
    'B': '#22c55e',
    'C': '#eab308',
    'D': '#ef4444',
}

SHIELDS_COLORS = {
    'S': 'blueviolet',
    'A': 'blue',
    'B': 'green',
    'C': 'yellow',
    'D': 'red',
}


def score_color(score: float) -> str:
    if score >= 80: return '#22c55e'
    if score >= 60: return '#eab308'
    if score >= 40: return '#f97316'
    return '#ef4444'


def generate_score_badge(model_id: str, score: float, tier: str, rank: int) -> str:
    """Generate a clean score SVG badge."""
    color = score_color(score)
    tier_color = TIER_COLORS.get(tier, '#6366f1')
    name = model_id.split('/')[-1][:22]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="36">
  <defs>
    <linearGradient id="bg{rank}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#0f0f23"/>
      <stop offset="100%" stop-color="#1a1a36"/>
    </linearGradient>
    <filter id="glow{rank}">
      <feGaussianBlur stdDeviation="1.5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="200" height="36" rx="7" fill="url(#bg{rank})" stroke="{tier_color}" stroke-width="1.2"/>
  <rect x="0" y="0" width="4" height="36" rx="3" fill="{tier_color}"/>
  <text x="12" y="13" font-family="-apple-system,system-ui,sans-serif" font-size="8" fill="#64748b" font-weight="600" letter-spacing="0.6">MODELRANK</text>
  <text x="12" y="27" font-family="-apple-system,system-ui,sans-serif" font-size="12" fill="#f1f5f9" font-weight="600">{name}</text>
  <text x="155" y="13" font-family="-apple-system,system-ui,sans-serif" font-size="8" fill="#64748b" text-anchor="middle">SCORE</text>
  <text x="155" y="28" font-family="-apple-system,system-ui,sans-serif" font-size="15" fill="{color}" font-weight="900" text-anchor="middle" filter="url(#glow{rank})">{score:.0f}</text>
  <rect x="178" y="8" width="18" height="20" rx="4" fill="{tier_color}"/>
  <text x="187" y="22" font-family="-apple-system,system-ui,sans-serif" font-size="11" fill="#000" font-weight="900" text-anchor="middle">{tier}</text>
</svg>'''


def generate_tier_badge(tier: str) -> str:
    tier_color = TIER_COLORS.get(tier, '#6366f1')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="100" height="28">
  <rect width="100" height="28" rx="6" fill="#0f0f23" stroke="{tier_color}" stroke-width="1.2"/>
  <text x="36" y="13" font-family="-apple-system,system-ui,sans-serif" font-size="7" fill="#64748b" letter-spacing="0.5">MODELRANK</text>
  <rect x="62" y="4" width="32" height="20" rx="5" fill="{tier_color}"/>
  <text x="78" y="18" font-family="-apple-system,system-ui,sans-serif" font-size="12" fill="#000" font-weight="900" text-anchor="middle">{tier}</text>
  <text x="5" y="18" font-family="-apple-system,system-ui,sans-serif" font-size="8" fill="#94a3b8">Tier</text>
</svg>'''


def generate_rank_badge(rank: int, total: int) -> str:
    color = '#22c55e' if rank <= 3 else ('#eab308' if rank <= 10 else '#94a3b8')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="110" height="28">
  <rect width="110" height="28" rx="6" fill="#0f0f23" stroke="{color}" stroke-width="1.2"/>
  <text x="4" y="12" font-family="-apple-system,system-ui,sans-serif" font-size="7" fill="#64748b" letter-spacing="0.5">MODELRANK RANK</text>
  <text x="4" y="24" font-family="-apple-system,system-ui,sans-serif" font-size="13" fill="{color}" font-weight="800">#{rank}</text>
  <text x="50" y="24" font-family="-apple-system,system-ui,sans-serif" font-size="9" fill="#64748b">/ {total}</text>
</svg>'''


def generate_shields_json(model_id: str, score: float, tier: str, rank: int) -> dict:
    """Shields.io endpoint JSON — embed in any README via img.shields.io/endpoint."""
    return {
        "schemaVersion": 1,
        "label": "ModelRank",
        "message": f"{score:.0f} ({tier}) #{rank}",
        "color": SHIELDS_COLORS.get(tier, 'grey'),
        "labelColor": "0f0f23",
        "style": "flat-square",
        "namedLogo": "huggingface",
        "logoColor": "white",
        "cacheSeconds": 86400,
    }


def generate_leaderboard_html(models: list, base_url: str) -> str:
    """Generate a standalone leaderboard HTML page for GitHub Pages."""
    rows = ''
    for i, item in enumerate(models, 1):
        mid = item.get('model_id', '')
        s = item.get('score', {})
        bd = s.get('breakdown', {})
        tier = s.get('tier', 'C')
        composite = s.get('composite', 0)
        tier_color = TIER_COLORS.get(tier, '#ccc')
        sc = score_color(composite)
        hf_url = f'https://huggingface.co/{mid}'
        badge_url = f'{base_url}/badges/{mid}/score.svg'
        rows += f'''
        <tr>
          <td style="color:#64748b;font-size:13px;padding:10px 8px;">{i}</td>
          <td style="padding:10px 8px;">
            <a href="{hf_url}" target="_blank" style="color:#a5b4fc;font-weight:600;text-decoration:none;font-size:13px;">{mid}</a>
          </td>
          <td style="padding:10px 8px;text-align:center;">
            <span style="color:{sc};font-weight:800;font-size:15px;">{composite:.1f}</span>
          </td>
          <td style="padding:10px 8px;text-align:center;">
            <span style="background:{tier_color};color:#000;font-weight:800;font-size:11px;padding:2px 10px;border-radius:12px;">{tier}</span>
          </td>
          <td style="padding:10px 8px;text-align:center;color:#94a3b8;font-size:12px;">{bd.get("benchmarks",0):.0f}</td>
          <td style="padding:10px 8px;text-align:center;color:#94a3b8;font-size:12px;">{bd.get("efficiency",0):.0f}</td>
          <td style="padding:10px 8px;text-align:center;color:#94a3b8;font-size:12px;">{bd.get("community",0):.0f}</td>
          <td style="padding:10px 8px;">
            <img src="{badge_url}" height="24" style="vertical-align:middle;" onerror="this.style.display='none'"/>
          </td>
        </tr>'''

    updated = __import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>ModelRank — HuggingFace Model Leaderboard</title>
  <meta name="description" content="Composite scoring and tier rankings for HuggingFace models. Independent benchmarks, efficiency, community, and freshness scores."/>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap" rel="stylesheet"/>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0;}}
    body{{background:#080818;color:#e2e8f0;font-family:'Inter',system-ui,sans-serif;min-height:100vh;}}
    .header{{text-align:center;padding:48px 20px 24px;}}
    .header h1{{font-size:clamp(28px,5vw,48px);font-weight:900;letter-spacing:-1px;color:#f1f5f9;}}
    .header p{{color:#64748b;font-size:15px;margin-top:8px;}}
    .badge-embed{{background:#12122a;border:1px solid #2d2d50;border-radius:10px;padding:12px 16px;margin:16px auto;max-width:700px;font-family:monospace;font-size:12px;color:#94a3b8;overflow-x:auto;}}
    .stats{{display:flex;gap:16px;justify-content:center;flex-wrap:wrap;padding:0 20px 24px;}}
    .stat{{background:#0f0f23;border:1px solid #2d2d50;border-radius:10px;padding:12px 20px;text-align:center;}}
    .stat-n{{font-size:24px;font-weight:900;color:#a5b4fc;}}
    .stat-l{{font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;}}
    .table-wrap{{overflow-x:auto;padding:0 16px 48px;max-width:1100px;margin:0 auto;}}
    table{{width:100%;border-collapse:collapse;}}
    thead th{{padding:10px 8px;text-align:left;font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:0.8px;border-bottom:1px solid #2d2d50;}}
    tbody tr{{border-bottom:1px solid #12122a;transition:background 0.15s;}}
    tbody tr:hover{{background:#0f0f23;}}
    .updated{{text-align:center;color:#334155;font-size:11px;padding-bottom:24px;}}
    .gh-link{{display:inline-flex;align-items:center;gap:6px;background:#1a1a36;border:1px solid #2d2d50;color:#a5b4fc;padding:6px 14px;border-radius:6px;font-size:12px;text-decoration:none;margin-top:12px;}}
    .gh-link:hover{{background:#2d2d50;}}
  </style>
</head>
<body>
  <div class="header">
    <h1>🏆 ModelRank</h1>
    <p>Independent composite scoring for HuggingFace models</p>
    <a class="gh-link" href="https://github.com/rankmodel/rankmodel1" target="_blank">
      ⭐ Star on GitHub
    </a>
  </div>
  <div class="stats">
    <div class="stat"><div class="stat-n">{len(models)}</div><div class="stat-l">Models Ranked</div></div>
    <div class="stat"><div class="stat-n">5</div><div class="stat-l">Dimensions</div></div>
    <div class="stat"><div class="stat-n">13</div><div class="stat-l">Benchmarks</div></div>
    <div class="stat"><div class="stat-n">Free</div><div class="stat-l">Always</div></div>
  </div>
  <div class="badge-embed">
    📌 Embed a badge in your README:<br/>
    <code>![ModelRank](https://rankmodel.github.io/rankmodel1/badges/YOUR_ORG/YOUR_MODEL/score.svg)</code>
  </div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>#</th><th>Model</th><th>Score</th><th>Tier</th>
          <th>Bench</th><th>Effic</th><th>Comm</th><th>Badge</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
  <div class="updated">Last updated: {updated} · Auto-updated daily by GitHub Actions</div>
</body>
</html>'''


def main(limit: int = 200):
    from data.cache import ModelCache

    cache = ModelCache()
    models = cache.get_leaderboard(limit=limit)
    total = len(models)

    if not models:
        logger.warning('No models in cache — run seed_leaderboard.py first')
        return

    base_url = 'https://rankmodel.github.io/rankmodel1'

    # Create output dirs
    (OUTPUT_DIR / 'badges').mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / 'models').mkdir(parents=True, exist_ok=True)

    logger.info(f'Generating static assets for {total} models → {OUTPUT_DIR}/')

    leaderboard_data = []

    for rank, item in enumerate(models, 1):
        mid = item.get('model_id', '')
        if not mid:
            continue
        s = item.get('score', {})
        composite = s.get('composite', 0)
        tier = s.get('tier', 'C')

        # Create badge dirs  e.g. static_output/badges/mistralai/Mistral-7B-v0.1/
        parts = mid.split('/', 1)
        org = parts[0] if len(parts) == 2 else 'unknown'
        model_name = parts[1] if len(parts) == 2 else parts[0]
        badge_dir = OUTPUT_DIR / 'badges' / org / model_name
        badge_dir.mkdir(parents=True, exist_ok=True)

        # Write SVG badges
        (badge_dir / 'score.svg').write_text(
            generate_score_badge(mid, composite, tier, rank), encoding='utf-8')
        (badge_dir / 'tier.svg').write_text(
            generate_tier_badge(tier), encoding='utf-8')
        (badge_dir / 'rank.svg').write_text(
            generate_rank_badge(rank, total), encoding='utf-8')

        # Write Shields.io JSON endpoint
        (badge_dir / 'shields.json').write_text(
            json.dumps(generate_shields_json(mid, composite, tier, rank), indent=2),
            encoding='utf-8')

        # Write per-model JSON
        model_json = {**s, 'model_id': mid, 'rank': rank,
                      'badge_url': f'{base_url}/badges/{mid}/score.svg',
                      'shields_url': f'{base_url}/badges/{mid}/shields.json'}
        (OUTPUT_DIR / 'models' / f'{org}__{model_name}.json').write_text(
            json.dumps(model_json, indent=2), encoding='utf-8')

        leaderboard_data.append({
            'rank': rank, 'model_id': mid,
            'composite': composite, 'tier': tier,
            'breakdown': s.get('breakdown', {}),
            'badge_url': f'{base_url}/badges/{mid}/score.svg',
            'shields_url': f'{base_url}/badges/{mid}/shields.json',
        })

        if rank % 10 == 0:
            logger.info(f'  {rank}/{total} done...')

    # Write leaderboard.json (full API-consumable data)
    (OUTPUT_DIR / 'leaderboard.json').write_text(
        json.dumps({
            'updated_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
            'total': total,
            'models': leaderboard_data,
        }, indent=2), encoding='utf-8')

    # Write index.html leaderboard page
    (OUTPUT_DIR / 'index.html').write_text(
        generate_leaderboard_html(models, base_url), encoding='utf-8')

    # Write a _headers file for GitHub Pages (proper SVG MIME type + CORS for badges)
    (OUTPUT_DIR / '_headers').write_text(
        '/badges/*\n  Content-Type: image/svg+xml\n  Cache-Control: public, max-age=3600\n  Access-Control-Allow-Origin: *\n\n'
        '/leaderboard.json\n  Content-Type: application/json\n  Cache-Control: public, max-age=3600\n  Access-Control-Allow-Origin: *\n\n'
        '/models/*\n  Content-Type: application/json\n  Access-Control-Allow-Origin: *\n'
    )

    # Write .nojekyll so GitHub Pages serves files as-is
    (OUTPUT_DIR / '.nojekyll').write_text('')

    logger.info(f'\n✅ Static assets generated in {OUTPUT_DIR}/')
    logger.info(f'   {total} score.svg badges')
    logger.info(f'   {total} shields.json endpoints')
    logger.info(f'   leaderboard.json ({len(leaderboard_data)} entries)')
    logger.info(f'   index.html leaderboard page')
    logger.info(f'\n📌 Badge URL pattern:')
    logger.info(f'   {base_url}/badges/ORG/MODEL/score.svg')
    logger.info(f'\n📌 Shields.io embed:')
    logger.info(f'   https://img.shields.io/endpoint?url={base_url}/badges/ORG/MODEL/shields.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate static badge and leaderboard assets')
    parser.add_argument('--limit', type=int, default=200)
    args = parser.parse_args()
    main(limit=args.limit)
