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
import math

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


def generate_mini_radar_svg(scores: dict) -> str:
    # scores = {'benchmarks': 82.0, 'efficiency': 46.3, 'community': 67.7, 'recency': 45.0, 'reproducibility': 55.0}
    dims = ['benchmarks', 'efficiency', 'community', 'recency', 'reproducibility']
    cx, cy, r = 30, 30, 22
    # Polygon points for score area
    points = []
    for i, dim in enumerate(dims):
        angle = math.pi * 2 * i / 5 - math.pi / 2
        val = scores.get(dim, 50) / 100 * r
        points.append((cx + val * math.cos(angle), cy + val * math.sin(angle)))
    # Background pentagon (full scale)
    bg_pts = []
    for i in range(5):
        angle = math.pi * 2 * i / 5 - math.pi / 2
        bg_pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    bg_str = ' '.join(f'{x:.1f},{y:.1f}' for x,y in bg_pts)
    pts_str = ' '.join(f'{x:.1f},{y:.1f}' for x,y in points)
    # Build SVG
    lines = ''.join(f'<line x1="{cx}" y1="{cy}" x2="{bx:.1f}" y2="{by:.1f}" stroke="#ffffff15" stroke-width="0.5"/>' for bx,by in bg_pts)
    return f'''<svg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
  <polygon points="{bg_str}" fill="none" stroke="#ffffff15" stroke-width="0.8"/>
  {lines}
  <polygon points="{pts_str}" fill="#3b82f680" stroke="#3b82f6" stroke-width="1.2"/>
</svg>'''


def generate_model_dna_svg(model_id: str, composite: float, tier: str, rank: int, breakdown: dict) -> str:
    """Generate a shareable 'Model DNA' card (radar + score + tier + bars)."""
    dims = [
        ('Benchmarks', breakdown.get('benchmarks', 50), '#3b82f6'),
        ('Efficiency', breakdown.get('efficiency', 50), '#22c55e'),
        ('Community', breakdown.get('community', 50), '#a855f7'),
        ('Freshness', breakdown.get('recency', breakdown.get('freshness', 50)), '#eab308'),
        ('Verified', breakdown.get('reproducibility', 50), '#ef4444'),
    ]
    cx, cy, r = 210, 215, 110
    n = len(dims)

    def _ang(i):
        return math.pi * 2 * i / n - math.pi / 2

    bg_pts = ' '.join(f'{cx + r * math.cos(_ang(i)):.1f},{cy + r * math.sin(_ang(i)):.1f}' for i in range(n))
    data_pts = ' '.join(f'{cx + (d[1] / 100 * r) * math.cos(_ang(i)):.1f},{cy + (d[1] / 100 * r) * math.sin(_ang(i)):.1f}' for i, d in enumerate(dims))

    axis_lines = ''
    labels = ''
    for i, (name, val, color) in enumerate(dims):
        ax, ay = cx + r * math.cos(_ang(i)), cy + r * math.sin(_ang(i))
        axis_lines += f'<line x1="{cx}" y1="{cy}" x2="{ax:.1f}" y2="{ay:.1f}" stroke="#ffffff18" stroke-width="1"/>'
        lx, ly = cx + (r + 22) * math.cos(_ang(i)), cy + (r + 22) * math.sin(_ang(i))
        labels += f'<text x="{lx:.1f}" y="{ly:.1f}" font-family="system-ui,sans-serif" font-size="10" fill="{color}" font-weight="700" text-anchor="middle">{name}</text>'

    bars = ''
    for i, (name, val, color) in enumerate(dims):
        y = 408 + i * 20
        bars += f'<text x="24" y="{y + 10}" font-family="system-ui,sans-serif" font-size="10" fill="{color}" font-weight="700">{name}</text>'
        bars += f'<rect x="100" y="{y}" width="{(val / 100 * 270):.0f}" height="9" rx="4" fill="{color}"/>'
        bars += f'<text x="378" y="{y + 10}" font-family="system-ui,sans-serif" font-size="10" fill="#cbd5e1" text-anchor="end">{val:.0f}</text>'

    tier_color = TIER_COLORS.get(tier, '#6366f1')
    parts = model_id.split('/', 1)
    org = parts[0] if len(parts) == 2 else ''
    name = parts[1] if len(parts) == 2 else model_id

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="420" height="520" viewBox="0 0 420 520">
  <defs>
    <linearGradient id="bgdna" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0f0f23"/>
      <stop offset="100%" stop-color="#171732"/>
    </linearGradient>
    <filter id="dneglow"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="420" height="520" rx="20" fill="url(#bgdna)" stroke="{tier_color}" stroke-width="2"/>
  <text x="210" y="34" font-family="system-ui,sans-serif" font-size="16" fill="#f1f5f9" font-weight="900" text-anchor="middle" letter-spacing="1">🧬 MODEL DNA</text>
  <text x="210" y="52" font-family="system-ui,sans-serif" font-size="9" fill="#64748b" text-anchor="middle" letter-spacing="2">MODELRANK · INDEPENDENT AI SCORE</text>
  <text x="210" y="80" font-family="system-ui,sans-serif" font-size="13" fill="#94a3b8" text-anchor="middle">{org}</text>
  <text x="210" y="100" font-family="system-ui,sans-serif" font-size="20" fill="#fff" font-weight="800" text-anchor="middle">{name}</text>
  {axis_lines}
  <polygon points="{bg_pts}" fill="none" stroke="#ffffff22" stroke-width="1"/>
  <polygon points="{data_pts}" fill="#3b82f655" stroke="{tier_color}" stroke-width="2"/>
  {labels}
  <text x="210" y="372" font-family="system-ui,sans-serif" font-size="46" fill="{tier_color}" font-weight="900" text-anchor="middle" filter="url(#dneglow)">{composite:.1f}</text>
  <text x="210" y="392" font-family="system-ui,sans-serif" font-size="11" fill="#64748b" text-anchor="middle">COMPOSITE · TIER {tier} · RANK #{rank}</text>
  {bars}
  <text x="210" y="510" font-family="system-ui,sans-serif" font-size="8" fill="#475569" text-anchor="middle">modelrank.github.io/rankmodel1</text>
</svg>'''


def generate_dna_html(base_url: str) -> str:
    """Generate the interactive 'Model DNA' share page."""
    return f'''<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>ModelRank — Model DNA Cards</title>
  <meta name="description" content="Your model's personality, scored. Get a shareable Model DNA card showing the 5-dimension breakdown."/>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{ darkMode: 'class', theme: {{ extend: {{ colors: {{ base: '#0a0a0f', surface: '#13131a' }}, fontFamily: {{ sans: ['Inter','system-ui','sans-serif'] }} }} }} }};
  </script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet"/>
  <style>body {{ background-color:#0a0a0f; color:#f1f5f9; font-family:'Inter',sans-serif; }} .glass-card {{ background:rgba(19,19,26,0.7); backdrop-filter:blur(12px); border:1px solid rgba(255,255,255,0.05); }}</style>
</head>
<body class="min-h-screen">
  <header class="pt-16 pb-12 border-b border-white/5 relative overflow-hidden">
    <div class="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-purple-600/10 blur-[120px] rounded-full pointer-events-none"></div>
    <div class="container mx-auto px-4 max-w-4xl relative z-10 text-center">
      <a href="index.html" class="text-xl font-black flex items-center gap-2 text-white absolute left-0 top-0">🏆 ModelRank</a>
      <h1 class="text-4xl md:text-5xl font-black text-white mb-3">🧬 Model DNA</h1>
      <p class="text-lg text-gray-400">Your model's personality, scored. Pick a model, grab a shareable card.</p>
    </div>
  </header>
  <main class="container mx-auto px-4 py-12 max-w-4xl">
    <div class="glass-card rounded-2xl p-6 mb-8 flex flex-col md:flex-row gap-4 items-center">
      <input id="search" placeholder="Search a model (e.g. Llama, Qwen, gemma)..." class="flex-1 bg-surface border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-purple-500"/>
      <select id="picker" class="bg-surface border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-purple-500"></select>
    </div>
    <div id="card" class="flex justify-center"></div>
    <div id="actions" class="flex flex-wrap justify-center gap-4 mt-8 hidden">
      <button id="copyBtn" class="px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-bold transition-colors">Copy markdown</button>
      <button id="shareBtn" class="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-bold transition-colors">Share on X</button>
      <a id="dlBtn" class="px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-bold transition-colors" download>Download SVG</a>
    </div>
  </main>
  <script>
    const BASE = '{base_url}';
    let models = [];
    async function load() {{
      const res = await fetch('leaderboard.json');
      const data = await res.json();
      models = (data.models || []).sort((a,b)=>a.rank-b.rank);
      const sel = document.getElementById('picker');
      models.forEach(m => {{
        const o = document.createElement('option');
        o.value = m.model_id; o.textContent = `#${{m.rank}}  ${{m.model_id}}  (${{m.composite.toFixed(1)}})`;
        sel.appendChild(o);
      }});
      if (models[0]) render(models[0].model_id);
    }}
    function render(mid) {{
      const card = document.getElementById('card');
      const img = `${{BASE}}/dna/${{encodeURIComponent(mid)}}.svg`;
      card.innerHTML = `<img src="${{img}}" alt="Model DNA for ${{mid}}" class="rounded-2xl shadow-2xl max-w-full" style="width:420px"/>`;
      document.getElementById('actions').classList.remove('hidden');
      window._mid = mid; window._img = img;
      document.getElementById('dlBtn').href = img;
    }}
    document.getElementById('picker').addEventListener('change', e => render(e.target.value));
    document.getElementById('search').addEventListener('input', e => {{
      const q = e.target.value.toLowerCase();
      const m = models.find(x => x.model_id.toLowerCase().includes(q));
      if (m) render(m.model_id);
    }});
    document.getElementById('copyBtn').addEventListener('click', () => {{
      const md = `![ModelRank Model DNA](${{window._img}})\\n\\nScored by @ModelRank — independent AI leaderboard`;
      navigator.clipboard.writeText(md);
      const b = document.getElementById('copyBtn'); b.textContent='Copied!'; setTimeout(()=>b.textContent='Copy markdown',1500);
    }});
    document.getElementById('shareBtn').addEventListener('click', () => {{
      const url = `https://twitter.com/intent/tweet?text=${{encodeURIComponent('My model '${{window._mid}}' just got its Model DNA from @ModelRank 🧬 '${{window._img}})}}`;
      window.open(url, '_blank');
    }});
    load();
  </script>
</body>
</html>'''


def generate_sitemap(models: list, base_url: str) -> str:
    """Generate sitemap.xml for SEO."""
    today = __import__('datetime').datetime.now().strftime('%Y-%m-%d')
    urls = f'''  <url>
    <loc>{base_url}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{base_url}/methodology.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{base_url}/quiz.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
   <url>
    <loc>{base_url}/collections.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{base_url}/dna.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{base_url}/pricing.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>'''
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>'''

def generate_robots_txt(base_url: str) -> str:
    return f'''User-agent: *
Allow: /

Sitemap: {base_url}/sitemap.xml
'''

def generate_leaderboard_html(models: list, base_url: str) -> str:
    """Generate a standalone leaderboard HTML page for GitHub Pages using Tailwind & daisyUI."""
    rows = ''
    # Cap HTML generation to top 100 models for performance; remaining models accessed via API search
    for i, item in enumerate(models[:100], 1):
        mid = item.get('model_id', '')
        s = item.get('score', {})
        bd = s.get('breakdown', {})
        tier = s.get('tier', 'C')
        composite = s.get('composite', 0)
        
        # Color codes for tiers
        tier_colors = {
            'S': 'text-purple-400 border-purple-400 bg-purple-400/10',
            'A': 'text-blue-400 border-blue-400 bg-blue-400/10',
            'B': 'text-green-400 border-green-400 bg-green-400/10',
            'C': 'text-yellow-400 border-yellow-400 bg-yellow-400/10',
            'D': 'text-red-400 border-red-400 bg-red-400/10'
        }
        score_colors = {
            'S': 'text-purple-400',
            'A': 'text-blue-400',
            'B': 'text-green-400',
            'C': 'text-yellow-400',
            'D': 'text-red-400'
        }
        
        tier_style = tier_colors.get(tier, 'text-gray-400 border-gray-400 bg-gray-400/10')
        score_style = score_colors.get(tier, 'text-gray-400')
        
        hf_url = f'https://huggingface.co/{mid}'
        badge_url = f'{base_url}/badges/{mid}/score.svg'
        
        parts = mid.split('/', 1)
        org = parts[0] if len(parts) > 1 else ''
        model_name = parts[1] if len(parts) > 1 else mid
        
        medal = '🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else f'#{i}'
        
        radar_svg = generate_mini_radar_svg(bd)
        
        b_score = bd.get("benchmarks", 0)
        e_score = bd.get("efficiency", 0)
        c_score = bd.get("community", 0)
        
        copy_code = f'![ModelRank]({badge_url})'
        
        ext = s.get('extended', {})
        param_score = ext.get('vram_tier', 50)
        if param_score >= 100: size_tier = 'edge'
        elif param_score >= 65: size_tier = 'consumer'
        elif param_score >= 25: size_tier = 'prosumer'
        else: size_tier = 'datacenter'

        is_uncensored = 'true' if ext.get('safety_score', 0) >= 80 else 'false'
        is_multilingual = 'true' if ext.get('multilingual', 0) >= 50 else 'false'
        is_code = 'true' if 'code' in mid.lower() or 'coder' in mid.lower() else 'false'
        
        tags_html = ''
        if is_code == 'true': tags_html += '<span class="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 uppercase font-bold">Code</span> '
        if is_multilingual == 'true': tags_html += '<span class="text-[9px] px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 uppercase font-bold">Multi</span> '
        if is_uncensored == 'true': tags_html += '<span class="text-[9px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20 uppercase font-bold">Uncensored</span> '
        if size_tier == 'edge': tags_html += '<span class="text-[9px] px-1.5 py-0.5 rounded bg-green-500/10 text-green-400 border border-green-500/20 uppercase font-bold">&lt;3B Edge</span> '
        elif size_tier == 'consumer': tags_html += '<span class="text-[9px] px-1.5 py-0.5 rounded bg-teal-500/10 text-teal-400 border border-teal-500/20 uppercase font-bold">3-13B</span> '
        
        import json
        bd_json = json.dumps(bd).replace('"', '&quot;')
        
        rows += f'''
        <tr class="hover:bg-white/5 transition-colors border-b border-white/5 group model-row cursor-pointer" 
            data-name="{mid.lower()}" data-tier="{tier}" data-size="{size_tier}" data-composite="{composite:.1f}"
            data-uncensored="{is_uncensored}" data-multilingual="{is_multilingual}" data-code="{is_code}" data-breakdown="{bd_json}">
          <td class="px-4 py-4 text-center font-mono text-gray-400">{medal}</td>
          <td class="px-4 py-4">
            <a href="{hf_url}" target="_blank" class="block hover:opacity-80 transition-opacity">
              <div class="text-xs text-gray-500 font-medium mb-1">{org}</div>
              <div class="text-base font-bold text-gray-100">{model_name}</div>
              <div class="flex flex-wrap gap-1 mt-1.5">{tags_html}</div>
            </a>
          </td>
          <td class="px-4 py-4 text-center">
            <span class="font-black text-2xl {score_style} font-mono">{composite:.1f}</span>
          </td>
          <td class="px-4 py-4 text-center">
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold border {tier_style} uppercase">{tier}</span>
          </td>
          <td class="px-4 py-4 text-center hidden md:table-cell w-20">
            {radar_svg}
          </td>
          <td class="px-4 py-4 hidden md:table-cell w-32">
            <div class="flex items-center justify-between text-xs mb-1">
              <span class="text-gray-400 font-mono">{b_score:.0f}</span>
            </div>
            <div class="w-full bg-gray-800 rounded-full h-1.5">
              <div class="bg-blue-500 h-1.5 rounded-full" style="width: {b_score}%"></div>
            </div>
          </td>
          <td class="px-4 py-4 hidden md:table-cell w-32">
            <div class="flex items-center justify-between text-xs mb-1">
              <span class="text-gray-400 font-mono">{e_score:.0f}</span>
            </div>
            <div class="w-full bg-gray-800 rounded-full h-1.5">
              <div class="bg-green-500 h-1.5 rounded-full" style="width: {e_score}%"></div>
            </div>
          </td>
          <td class="px-4 py-4 hidden lg:table-cell w-32">
            <div class="flex items-center justify-between text-xs mb-1">
              <span class="text-gray-400 font-mono">{c_score:.0f}</span>
            </div>
            <div class="w-full bg-gray-800 rounded-full h-1.5">
              <div class="bg-purple-500 h-1.5 rounded-full" style="width: {c_score}%"></div>
            </div>
          </td>
          <td class="px-4 py-4 text-center">
            <button onclick="copyBadge(this, '{copy_code}')" class="p-2 hover:bg-white/10 rounded-lg transition-colors text-gray-400 hover:text-white" title="Copy embed code">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </button>
          </td>
          <td class="px-4 py-4 text-center text-gray-500 font-mono text-sm">
            0
          </td>
          <td class="px-4 py-4 text-center">
            <input type="checkbox" class="compare-checkbox w-4 h-4 rounded border-gray-700 bg-gray-800 text-blue-500 focus:ring-blue-500" data-model="{mid}" data-score="{composite}" data-bench="{b_score}" data-effic="{e_score}" data-comm="{c_score}">
          </td>
        </tr>'''

    updated = __import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    
    return f'''<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>ModelRank — The independent standard for open-weight AI</title>
  <meta name="description" content="Composite scoring and tier rankings for HuggingFace models. Independent benchmarks, efficiency, community, and freshness scores."/>
  
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            base: '#0a0a0f',
            surface: '#13131a',
            border: '#232330'
          }},
          fontFamily: {{
            sans: ['Inter', 'system-ui', 'sans-serif'],
            mono: ['JetBrains Mono', 'monospace']
          }}
        }}
      }}
    }}
  </script>
  
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700;800&display=swap" rel="stylesheet"/>
  <style>
    body {{ background-color: #0a0a0f; color: #f1f5f9; font-family: 'Inter', sans-serif; }}
    .glass-card {{ background: rgba(19, 19, 26, 0.7); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }}
    .stat-bar {{ transition: width 1s cubic-bezier(0.4, 0, 0.2, 1); }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .animate-fade-in {{ animation: fadeIn 0.5s ease-out forwards; }}
    
    /* Smooth hiding for filters */
    .model-row {{ transition: opacity 0.2s, transform 0.2s; }}
    .hidden-row {{ display: none !important; }}
  </style>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "WebApplication",
    "name": "ModelRank",
    "url": "{base_url}/",
    "description": "The independent standard and composite scoring system for open-weight AI models.",
    "applicationCategory": "DeveloperApplication",
    "operatingSystem": "All",
    "offers": {{
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD"
    }}
  }}
  </script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="min-h-screen text-gray-200 relative">
  <!-- DNA Modal -->
  <div id="dnaModal" class="fixed inset-0 z-[100] flex items-center justify-center hidden opacity-0 transition-opacity duration-300">
    <div id="dnaModalBg" class="absolute inset-0 bg-black/80 backdrop-blur-sm cursor-pointer"></div>
    <div id="dnaModalContent" class="relative glass-card border border-white/10 rounded-2xl w-full max-w-2xl mx-4 p-8 transform scale-95 transition-all duration-300 shadow-2xl overflow-hidden">
      <button id="closeDnaBtn" class="absolute top-4 right-4 text-gray-500 hover:text-white transition-colors bg-white/5 hover:bg-white/10 p-2 rounded-full z-10">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
      </button>
      <div class="flex flex-col md:flex-row gap-8 items-center">
        <div class="flex-1 w-full max-w-[300px] aspect-square relative">
          <canvas id="dnaChartCanvas"></canvas>
        </div>
        <div class="flex-1 w-full">
          <h2 id="dnaModalTitle" class="text-3xl font-black text-white mb-2 break-all">Model</h2>
          <div class="flex items-center gap-2 mb-6">
            <span id="dnaModalTier" class="px-3 py-1 rounded-full text-sm font-bold border">A</span>
            <span id="dnaModalScore" class="text-xl font-mono text-gray-400">0.0</span>
          </div>
          <div class="space-y-4 text-sm font-mono text-gray-400" id="dnaModalStats">
            <!-- Stats injected via JS -->
          </div>
          <a id="dnaModalLink" href="#" target="_blank" class="mt-8 flex items-center justify-center gap-2 w-full bg-white/10 hover:bg-white/20 text-white font-bold py-3 px-6 rounded-xl transition-colors">
            View on HuggingFace <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
          </a>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Hero Section -->
  <header class="relative overflow-hidden pt-16 pb-24 border-b border-white/5">
    <!-- Abstract background glow -->
    <div class="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-blue-600/10 blur-[120px] rounded-full pointer-events-none"></div>
    <div class="absolute top-20 right-0 w-[400px] h-[400px] bg-purple-600/10 blur-[120px] rounded-full pointer-events-none"></div>
    
    <div class="container mx-auto px-4 max-w-7xl relative z-10">
      <nav class="flex items-center justify-between mb-16">
        <div class="text-2xl font-black tracking-tight flex items-center gap-2">
          🏆 ModelRank
        </div>
        <div class="flex items-center gap-6 text-sm font-medium text-gray-400">
          <a href="#" class="text-white">Leaderboard</a>
          <a href="methodology.html" class="hover:text-white transition-colors">Methodology</a>
          <a href="quiz.html" class="hover:text-white transition-colors">Quiz</a>
          <a href="collections.html" class="hover:text-white transition-colors">Collections</a>
          <a href="dna.html" class="hover:text-white transition-colors">Model DNA</a>
          <a href="pricing.html" class="hover:text-white transition-colors">Pricing</a>
          <a href="https://github.com/rankmodel/rankmodel1" class="hover:text-white transition-colors flex items-center gap-2">
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path fill-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clip-rule="evenodd"></path></svg>
            GitHub
          </a>
        </div>
      </nav>
      
      <div class="text-center max-w-4xl mx-auto mt-10">
        <h1 class="text-5xl md:text-7xl font-black tracking-tighter text-white mb-6 drop-shadow-lg">
          The independent standard for <br/><span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">open-weight AI</span>
        </h1>
        <p class="text-xl text-gray-400 mb-10 max-w-2xl mx-auto">Objective composite scoring and rankings for {len(models)} models across benchmarks, efficiency, and community usage.</p>
        
        <div class="flex flex-wrap justify-center gap-4 text-sm font-medium text-gray-300">
          <div class="px-4 py-2 rounded-full border border-white/10 bg-white/5 backdrop-blur flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-blue-500"></span>
            {len(models)} Models Ranked
          </div>
          <div class="px-4 py-2 rounded-full border border-white/10 bg-white/5 backdrop-blur flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-green-500"></span>
            15 Benchmarks
          </div>
          <div class="px-4 py-2 rounded-full border border-white/10 bg-white/5 backdrop-blur flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-purple-500"></span>
            5 Dimensions
          </div>
          <div class="px-4 py-2 rounded-full border border-white/10 bg-white/5 backdrop-blur flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-yellow-500"></span>
            Free Forever
          </div>
        </div>
      </div>
    </div>
  </header>

  <!-- Main Content -->
  <main class="container mx-auto px-4 max-w-7xl -mt-8 relative z-20 mb-32">
    
    <!-- Advanced Filter Bar (Sticky) -->
    <div class="glass-card rounded-2xl p-4 mb-8 shadow-2xl sticky top-4 z-30 flex flex-col gap-4 animate-fade-in">
      <div class="flex flex-col md:flex-row gap-4 items-center justify-between w-full">
        <div class="relative w-full md:w-80">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
          <input type="text" id="searchInput" placeholder="Search 1000+ models..." class="w-full bg-surface border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors">
        </div>
        
        <div class="flex items-center gap-2 overflow-x-auto w-full md:w-auto pb-2 md:pb-0 hide-scrollbar" id="tierFilters">
          <button class="tier-btn active px-4 py-2 rounded-lg text-sm font-bold bg-white/10 text-white transition-colors" data-tier="all">ALL TIERS</button>
          <button class="tier-btn px-4 py-2 rounded-lg text-sm font-bold text-gray-400 hover:bg-white/5 transition-colors" data-tier="S">S</button>
          <button class="tier-btn px-4 py-2 rounded-lg text-sm font-bold text-gray-400 hover:bg-white/5 transition-colors" data-tier="A">A</button>
          <button class="tier-btn px-4 py-2 rounded-lg text-sm font-bold text-gray-400 hover:bg-white/5 transition-colors" data-tier="B">B</button>
          <button class="tier-btn px-4 py-2 rounded-lg text-sm font-bold text-gray-400 hover:bg-white/5 transition-colors" data-tier="C">C</button>
          <button class="tier-btn px-4 py-2 rounded-lg text-sm font-bold text-gray-400 hover:bg-white/5 transition-colors" data-tier="D">D</button>
        </div>
      </div>
      
      <div class="flex flex-wrap items-center gap-3 pt-3 border-t border-white/5">
        <select id="sizeFilter" class="bg-surface border border-white/10 rounded-lg px-3 py-1.5 text-xs text-gray-300 font-semibold focus:outline-none focus:border-blue-500">
          <option value="all">Any Size</option>
          <option value="edge">&lt;3B (Edge/Mobile)</option>
          <option value="consumer">3B - 13B (Consumer GPU)</option>
          <option value="prosumer">14B - 34B (Prosumer)</option>
          <option value="datacenter">35B+ (Datacenter)</option>
        </select>
        
        <select id="categoryFilter" class="bg-surface border border-white/10 rounded-lg px-3 py-1.5 text-xs text-gray-300 font-semibold focus:outline-none focus:border-blue-500">
          <option value="all">Any Category</option>
          <option value="code">Code Generation</option>
          <option value="multilingual">Multilingual</option>
          <option value="uncensored">Uncensored / Abliterated</option>
        </select>
        
        <div class="flex-grow"></div>
        
        <button id="compareBtn" class="px-4 py-1.5 rounded-lg text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white transition-colors opacity-50 cursor-not-allowed" disabled>
          Compare (0/2)
        </button>
      </div>
    </div>
    
    <!-- Leaderboard Table -->
    <div class="glass-card rounded-2xl overflow-hidden shadow-2xl animate-fade-in" style="animation-delay: 0.1s">
      <div class="overflow-x-auto">
        <table class="w-full text-left whitespace-nowrap">
          <thead class="bg-white/5 border-b border-white/5 text-xs uppercase tracking-wider font-semibold text-gray-400">
            <tr>
              <th class="px-4 py-4 text-center">Rank</th>
              <th class="px-4 py-4">Model</th>
              <th class="px-4 py-4 text-center">Score</th>
              <th class="px-4 py-4 text-center">Tier</th>
              <th class="px-4 py-4 text-center hidden md:table-cell">Profile</th>
              <th class="px-4 py-4 hidden md:table-cell">Benchmarks</th>
              <th class="px-4 py-4 hidden md:table-cell">Efficiency</th>
              <th class="px-4 py-4 hidden lg:table-cell">Community</th>
              <th class="px-4 py-4 text-center">Embed</th>
              <th class="px-4 py-4 text-center">Change</th>
              <th class="px-4 py-4 text-center">Compare</th>
            </tr>
          </thead>
          <tbody id="leaderboardBody" class="divide-y divide-white/5 text-sm">
            {rows}
          </tbody>
        </table>
    </div>
    
    <div class="mt-8 text-center" id="loadMoreContainer">
      <button id="loadMoreBtn" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-full shadow-lg transition-all transform hover:scale-105">
        Load 100,000+ Models (API)
      </button>
      <p class="text-sm text-gray-500 mt-3 hidden" id="loadingText">Fetching massive model index...</p>
    </div>
    
    <!-- Methodology Section -->
    <div id="methodology" class="mt-32 mb-16 animate-fade-in" style="animation-delay: 0.2s">
      <div class="text-center mb-12">
        <h2 class="text-3xl font-black text-white mb-4">Methodology</h2>
        <p class="text-gray-400 max-w-2xl mx-auto">A transparent, reproducible scoring system that looks beyond simple benchmarks to capture the full picture of a model's utility.</p>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div class="glass-card p-6 rounded-2xl">
          <div class="text-2xl mb-2">🧠</div>
          <h3 class="font-bold text-white mb-1">Benchmarks</h3>
          <div class="text-xs text-blue-400 font-bold mb-3">40% WEIGHT</div>
          <p class="text-sm text-gray-400 leading-relaxed">Aggregated scores from MMLU, HumanEval, GSM8K, and TruthfulQA. Adjusted for model contamination.</p>
        </div>
        <div class="glass-card p-6 rounded-2xl">
          <div class="text-2xl mb-2">⚡</div>
          <h3 class="font-bold text-white mb-1">Efficiency</h3>
          <div class="text-xs text-green-400 font-bold mb-3">20% WEIGHT</div>
          <p class="text-sm text-gray-400 leading-relaxed">Throughput (tokens/sec), memory footprint, and param-to-performance ratio on standard hardware.</p>
        </div>
        <div class="glass-card p-6 rounded-2xl">
          <div class="text-2xl mb-2">🔥</div>
          <h3 class="font-bold text-white mb-1">Community</h3>
          <div class="text-xs text-purple-400 font-bold mb-3">20% WEIGHT</div>
          <p class="text-sm text-gray-400 leading-relaxed">Downloads, GitHub stars, and community integrations across the HuggingFace ecosystem.</p>
        </div>
        <div class="glass-card p-6 rounded-2xl">
          <div class="text-2xl mb-2">🕐</div>
          <h3 class="font-bold text-white mb-1">Freshness</h3>
          <div class="text-xs text-yellow-400 font-bold mb-3">10% WEIGHT</div>
          <p class="text-sm text-gray-400 leading-relaxed">Time since last update or release. Penalizes abandoned models and rewards actively maintained ones.</p>
        </div>
        <div class="glass-card p-6 rounded-2xl">
          <div class="text-2xl mb-2">✅</div>
          <h3 class="font-bold text-white mb-1">Verified</h3>
          <div class="text-xs text-red-400 font-bold mb-3">10% WEIGHT</div>
          <p class="text-sm text-gray-400 leading-relaxed">Open weights, reproducible evaluation code, and clear licensing (MIT/Apache preferred).</p>
        </div>
      </div>
    </div>
    
    <!-- Trust & Embed Section -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-16">
      <div class="glass-card p-8 rounded-2xl">
        <h3 class="text-2xl font-black text-white mb-6">Why trust ModelRank?</h3>
        <ul class="space-y-4">
          <li class="flex items-start gap-3">
            <svg class="w-6 h-6 text-blue-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            <div>
              <h4 class="font-bold text-gray-200">Open Source</h4>
              <p class="text-sm text-gray-400">MIT licensed and fully auditable methodology.</p>
            </div>
          </li>
          <li class="flex items-start gap-3">
            <svg class="w-6 h-6 text-blue-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            <div>
              <h4 class="font-bold text-gray-200">No Conflicts of Interest</h4>
              <p class="text-sm text-gray-400">We don't train or host models. Independent evaluation only.</p>
            </div>
          </li>
          <li class="flex items-start gap-3">
            <svg class="w-6 h-6 text-blue-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            <div>
              <h4 class="font-bold text-gray-200">Reproducible</h4>
              <p class="text-sm text-gray-400">All evaluation data is sourced from public HuggingFace APIs.</p>
            </div>
          </li>
          <li class="flex items-start gap-3">
            <svg class="w-6 h-6 text-blue-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            <div>
              <h4 class="font-bold text-gray-200">Updated Daily</h4>
              <p class="text-sm text-gray-400">Fully automated via GitHub Actions cron jobs.</p>
            </div>
          </li>
        </ul>
        <div class="mt-8 flex flex-wrap gap-4">
          <a href="#methodology" class="text-sm text-blue-400 hover:text-blue-300 transition-colors">View methodology &rarr;</a>
          <a href="https://github.com/rankmodel/rankmodel1" class="text-sm text-blue-400 hover:text-blue-300 transition-colors">View source code &rarr;</a>
          <a href="#" class="text-sm text-blue-400 hover:text-blue-300 transition-colors">API docs &rarr;</a>
        </div>
      </div>
      
      <div class="glass-card p-8 rounded-2xl">
        <h3 class="text-2xl font-black text-white mb-6">Embed Badges</h3>
        <p class="text-gray-400 text-sm mb-6">Showcase your model's rank anywhere with markdown.</p>
        
        <div class="space-y-6">
          <div>
            <div class="text-xs font-bold text-gray-500 uppercase mb-2">Score Badge</div>
            <div class="bg-surface p-3 rounded-lg border border-white/5 font-mono text-xs text-gray-300 overflow-x-auto whitespace-nowrap">
              ![ModelRank]({base_url}/badges/ORG/MODEL/score.svg)
            </div>
          </div>
          <div>
            <div class="text-xs font-bold text-gray-500 uppercase mb-2">Shields.io (Works anywhere)</div>
            <div class="bg-surface p-3 rounded-lg border border-white/5 font-mono text-xs text-gray-300 overflow-x-auto whitespace-nowrap">
              ![ModelRank](https://img.shields.io/endpoint?url={base_url}/badges/ORG/MODEL/shields.json)
            </div>
          </div>
        </div>
      </div>
    </div>
    
  </main>
  
  <!-- Compare Modal -->
  <div id="compareModal" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 hidden flex items-center justify-center opacity-0 transition-opacity">
    <div class="glass-card w-full max-w-4xl mx-4 rounded-3xl p-8 transform scale-95 transition-transform" id="compareModalContent">
      <div class="flex justify-between items-center mb-8">
        <h2 class="text-2xl font-black text-white">Model Comparison</h2>
        <button id="closeCompare" class="text-gray-400 hover:text-white">
          <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>
      <div class="grid grid-cols-2 gap-8" id="compareGrid">
        <!-- Content injected via JS -->
      </div>
    </div>
  </div>
  
  <!-- Toast -->
  <div id="toast" class="fixed bottom-4 right-4 bg-blue-600 text-white px-6 py-3 rounded-xl shadow-2xl font-medium transform translate-y-20 opacity-0 transition-all z-50">
    Copied to clipboard!
  </div>

  <footer class="border-t border-white/10 bg-surface/50 mt-12 py-12">
    <div class="container mx-auto px-4 max-w-7xl flex flex-col md:flex-row justify-between items-center gap-6">
      <div>
        <div class="text-xl font-black text-white mb-2">ModelRank</div>
        <p class="text-sm text-gray-500 max-w-md">ModelRank is an independent project and has no affiliation with Hugging Face. Data updated daily via GitHub Actions.</p>
        <p class="text-xs text-gray-600 mt-2">Last updated: {updated}</p>
      </div>
      <div class="flex flex-wrap gap-6 text-sm font-medium">
        <a href="https://github.com/rankmodel/rankmodel1" class="text-gray-400 hover:text-white transition-colors">GitHub</a>
        <a href="pricing.html" class="text-gray-400 hover:text-white transition-colors">Pricing</a>
        <a href="#" class="text-gray-400 hover:text-white transition-colors">API</a>
        <a href="#methodology" class="text-gray-400 hover:text-white transition-colors">Methodology</a>
        <a href="#" class="text-gray-400 hover:text-white transition-colors">Contact</a>
      </div>
    </div>
  </footer>

  <script>
    // --- Vanilla JS Interactions ---
    
    // Copy badge code
    function copyBadge(btn, code) {{
      navigator.clipboard.writeText(code).then(() => {{
        const toast = document.getElementById('toast');
        toast.style.transform = 'translateY(0)';
        toast.style.opacity = '1';
        setTimeout(() => {{
          toast.style.transform = 'translateY(20px)';
          toast.style.opacity = '0';
        }}, 2000);
      }});
    }}
    
    document.addEventListener('DOMContentLoaded', () => {{
      const searchInput = document.getElementById('searchInput');
      const tierBtns = document.querySelectorAll('.tier-btn');
      const rows = document.querySelectorAll('.model-row');
      const checkboxes = document.querySelectorAll('.compare-checkbox');
      const compareBtn = document.getElementById('compareBtn');
      const compareModal = document.getElementById('compareModal');
      const compareModalContent = document.getElementById('compareModalContent');
      const closeCompare = document.getElementById('closeCompare');
      const compareGrid = document.getElementById('compareGrid');
      
      let currentTier = 'all';
      let selectedModels = [];
      const sizeFilter = document.getElementById('sizeFilter');
      const categoryFilter = document.getElementById('categoryFilter');
      
      // Filter function
      function filterTable() {{
        const query = searchInput.value.toLowerCase();
        const selectedSize = sizeFilter ? sizeFilter.value : 'all';
        const selectedCat = categoryFilter ? categoryFilter.value : 'all';
        
        rows.forEach(row => {{
          const name = row.getAttribute('data-name');
          const tier = row.getAttribute('data-tier');
          const size = row.getAttribute('data-size');
          const isCode = row.getAttribute('data-code') === 'true';
          const isMulti = row.getAttribute('data-multilingual') === 'true';
          const isUncensored = row.getAttribute('data-uncensored') === 'true';
          
          const matchesSearch = name.includes(query);
          const matchesTier = currentTier === 'all' || tier === currentTier;
          const matchesSize = selectedSize === 'all' || size === selectedSize;
          
          let matchesCat = true;
          if (selectedCat === 'code' && !isCode) matchesCat = false;
          if (selectedCat === 'multilingual' && !isMulti) matchesCat = false;
          if (selectedCat === 'uncensored' && !isUncensored) matchesCat = false;
          
          if (matchesSearch && matchesTier && matchesSize && matchesCat) {{
            row.classList.remove('hidden-row');
          }} else {{
            row.classList.add('hidden-row');
          }}
        }});
      }}
      
      // Search event
      if(searchInput) {{ searchInput.addEventListener('input', filterTable); }}
      if(sizeFilter) {{ sizeFilter.addEventListener('change', filterTable); }}
      if(categoryFilter) {{ categoryFilter.addEventListener('change', filterTable); }}
      
      // Tier filter events
      tierBtns.forEach(btn => {{
        btn.addEventListener('click', (e) => {{
          // Update active states
          tierBtns.forEach(b => {{
            b.classList.remove('bg-white/10', 'text-white');
            b.classList.add('text-gray-400');
          }});
          e.target.classList.remove('text-gray-400');
          e.target.classList.add('bg-white/10', 'text-white');
          
          currentTier = e.target.getAttribute('data-tier');
          filterTable();
        }});
      }});
      
      // Compare checkboxes
      checkboxes.forEach(cb => {{
        cb.addEventListener('change', (e) => {{
          if (e.target.checked) {{
            if (selectedModels.length >= 2) {{
              e.target.checked = false; // Max 2
              return;
            }}
            selectedModels.push({{
              id: e.target.getAttribute('data-model'),
              score: e.target.getAttribute('data-score'),
              bench: e.target.getAttribute('data-bench'),
              effic: e.target.getAttribute('data-effic'),
              comm: e.target.getAttribute('data-comm')
            }});
          }} else {{
            selectedModels = selectedModels.filter(m => m.id !== e.target.getAttribute('data-model'));
          }}
          
          // Update button
          compareBtn.textContent = `Compare (${{selectedModels.length}}/2)`;
          if (selectedModels.length === 2) {{
            compareBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            compareBtn.removeAttribute('disabled');
          }} else {{
            compareBtn.classList.add('opacity-50', 'cursor-not-allowed');
            compareBtn.setAttribute('disabled', 'true');
          }}
        }});
      }});
      
      // Open compare modal
      if(compareBtn) {{
        compareBtn.addEventListener('click', () => {{
          if (selectedModels.length !== 2) return;
          
          const m1 = selectedModels[0];
          const m2 = selectedModels[1];
          
          const renderModel = (m) => `
            <div class="bg-surface p-6 rounded-2xl border border-white/5">
              <div class="text-sm text-gray-500 mb-1">${{m.id.split('/')[0] || ''}}</div>
              <div class="text-xl font-bold text-white mb-6 truncate" title="${{m.id}}">${{m.id.split('/')[1] || m.id}}</div>
              
              <div class="text-4xl font-black font-mono text-center mb-8">${{parseFloat(m.score).toFixed(1)}}</div>
              
              <div class="space-y-4">
                <div>
                  <div class="flex justify-between text-xs mb-1"><span class="text-gray-400">Benchmarks</span><span class="font-mono text-white">${{m.bench}}</span></div>
                  <div class="w-full bg-gray-800 rounded-full h-2"><div class="bg-blue-500 h-2 rounded-full" style="width: ${{m.bench}}%"></div></div>
                </div>
                <div>
                  <div class="flex justify-between text-xs mb-1"><span class="text-gray-400">Efficiency</span><span class="font-mono text-white">${{m.effic}}</span></div>
                  <div class="w-full bg-gray-800 rounded-full h-2"><div class="bg-green-500 h-2 rounded-full" style="width: ${{m.effic}}%"></div></div>
                </div>
                <div>
                  <div class="flex justify-between text-xs mb-1"><span class="text-gray-400">Community</span><span class="font-mono text-white">${{m.comm}}</span></div>
                  <div class="w-full bg-gray-800 rounded-full h-2"><div class="bg-purple-500 h-2 rounded-full" style="width: ${{m.comm}}%"></div></div>
                </div>
              </div>
            </div>
          `;
          
          compareGrid.innerHTML = renderModel(m1) + renderModel(m2);
          
          compareModal.classList.remove('hidden');
          // Trigger reflow
          void compareModal.offsetWidth;
          compareModal.classList.remove('opacity-0');
          compareModalContent.classList.remove('scale-95');
        }});
      }}
      
      // Close compare modal
      function closeModal() {{
        compareModal.classList.add('opacity-0');
        compareModalContent.classList.add('scale-95');
        setTimeout(() => compareModal.classList.add('hidden'), 300);
      }}
      
      if(closeCompare) closeCompare.addEventListener('click', closeModal);
      if(compareModal) {{
        compareModal.addEventListener('click', (e) => {{
          if (e.target === compareModal) closeModal();
        }});
      }}
      
      // Load More logic
      const loadMoreBtn = document.getElementById('loadMoreBtn');
      const loadingText = document.getElementById('loadingText');
      if (loadMoreBtn) {{
        loadMoreBtn.addEventListener('click', () => {{
          loadMoreBtn.classList.add('hidden');
          loadingText.classList.remove('hidden');
          
          fetch('search_index.json')
            .then(res => res.json())
            .then(data => {{
              loadingText.textContent = `Successfully loaded ${{data.length}} models into memory. Advanced UI rendering in development.`;
            }})
            .catch(err => {{
              loadingText.textContent = 'Error loading models.';
              console.error(err);
            }});
        }});
      }}
    }});
    
    // --- DNA Modal Logic ---
    const dnaModal = document.getElementById('dnaModal');
    const dnaModalBg = document.getElementById('dnaModalBg');
    const closeDnaBtn = document.getElementById('closeDnaBtn');
    let dnaChart = null;

    function openDnaModal(name, tier, composite, breakdown) {{
      document.getElementById('dnaModalTitle').textContent = name;
      document.getElementById('dnaModalTier').textContent = tier;
      document.getElementById('dnaModalScore').textContent = composite;
      
      const tierColors = {{
        'S': {{ bg: 'bg-purple-400/10', text: 'text-purple-400', border: 'border-purple-400', hex: '#c084fc' }},
        'A': {{ bg: 'bg-blue-400/10', text: 'text-blue-400', border: 'border-blue-400', hex: '#60a5fa' }},
        'B': {{ bg: 'bg-green-400/10', text: 'text-green-400', border: 'border-green-400', hex: '#4ade80' }},
        'C': {{ bg: 'bg-yellow-400/10', text: 'text-yellow-400', border: 'border-yellow-400', hex: '#facc15' }},
        'D': {{ bg: 'bg-red-400/10', text: 'text-red-400', border: 'border-red-400', hex: '#f87171' }}
      }};
      const color = tierColors[tier] || tierColors['C'];
      
      const tierEl = document.getElementById('dnaModalTier');
      tierEl.className = `px-3 py-1 rounded-full text-sm font-bold border ${{color.bg}} ${{color.text}} ${{color.border}}`;
      
      document.getElementById('dnaModalLink').href = `https://huggingface.co/${{name}}`;
      
      const statsHtml = Object.entries(breakdown).map(([k, v]) => `
        <div class="flex justify-between items-center mb-2">
          <span class="capitalize text-gray-300">${{k}}</span>
          <span class="font-bold text-white">${{Number(v).toFixed(1)}}</span>
        </div>
        <div class="w-full bg-white/5 rounded-full h-1.5 mb-4">
          <div class="h-1.5 rounded-full" style="width: ${{v}}%; background-color: ${{color.hex}};"></div>
        </div>
      `).join('');
      document.getElementById('dnaModalStats').innerHTML = statsHtml;
      
      // Render Radar Chart
      const ctx = document.getElementById('dnaChartCanvas').getContext('2d');
      if (dnaChart) dnaChart.destroy();
      
      Chart.defaults.color = 'rgba(255, 255, 255, 0.6)';
      dnaChart = new Chart(ctx, {{
        type: 'radar',
        data: {{
          labels: ['Benchmarks', 'Efficiency', 'Community', 'Recency', 'Reproducibility'],
          datasets: [{{
            label: 'DNA',
            data: [
              breakdown.benchmarks || 0,
              breakdown.efficiency || 0,
              breakdown.community || 0,
              breakdown.recency || 0,
              breakdown.reproducibility || 0
            ],
            backgroundColor: `${{color.hex}}33`,
            borderColor: color.hex,
            pointBackgroundColor: color.hex,
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: color.hex,
            borderWidth: 2,
          }}]
        }},
        options: {{
          scales: {{
            r: {{
              angleLines: {{ color: 'rgba(255, 255, 255, 0.1)' }},
              grid: {{ color: 'rgba(255, 255, 255, 0.1)' }},
              pointLabels: {{ font: {{ family: 'Inter', size: 10, weight: 'bold' }} }},
              ticks: {{ display: false, min: 0, max: 100 }}
            }}
          }},
          plugins: {{ legend: {{ display: false }} }}
        }}
      }});
      
      dnaModal.classList.remove('hidden');
      setTimeout(() => dnaModal.classList.remove('opacity-0'), 10);
    }}
    
    function closeDna() {{
      dnaModal.classList.add('opacity-0');
      setTimeout(() => dnaModal.classList.add('hidden'), 300);
    }}
    
    closeDnaBtn.addEventListener('click', closeDna);
    dnaModalBg.addEventListener('click', closeDna);
    
    // Attach click events to rows
    document.querySelectorAll('.model-row').forEach(row => {{
      row.addEventListener('click', (e) => {{
        // Prevent if clicking on link or copy button
        if (e.target.closest('a') || e.target.closest('button')) return;
        
        const name = row.getAttribute('data-name');
        const tier = row.getAttribute('data-tier');
        const composite = row.getAttribute('data-composite');
        const breakdown = JSON.parse(row.getAttribute('data-breakdown'));
        openDnaModal(name, tier, composite, breakdown);
      }});
    }});
  </script>
</body>
</html>'''



def generate_quiz_html() -> str:
    """Generate the interactive recommendation quiz."""
    return """<!DOCTYPE html>
<html lang="en" class="dark" data-theme="dark">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>ModelRank — Best Model for Your Use Case</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://cdn.jsdelivr.net/npm/daisyui@3.9.0/dist/full.css" rel="stylesheet" type="text/css" />
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: { base: '#0a0a0f', surface: '#13131a', border: '#232330' },
          fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'], mono: ['JetBrains Mono', 'monospace'] }
        }
      }
    }
  </script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700;800&display=swap" rel="stylesheet"/>
  <style>
    body { background-color: #0a0a0f; color: #f1f5f9; font-family: 'Inter', sans-serif; }
    .glass-card { background: rgba(19, 19, 26, 0.7); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }
    .step-panel { display: none; opacity: 0; transform: translateX(20px); transition: all 0.4s ease-out; }
    .step-panel.active { display: block; opacity: 1; transform: translateX(0); }
    .card-option { cursor: pointer; transition: all 0.2s; border: 2px solid transparent; }
    .card-option:hover { background: rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.1); }
    .card-option.selected { border-color: #3b82f6; background: rgba(59, 130, 246, 0.1); }
  </style>
</head>
<body class="min-h-screen text-gray-200">
  <header class="pt-8 pb-4 border-b border-white/5">
    <div class="container mx-auto px-4 max-w-4xl flex justify-between items-center">
      <a href="index.html" class="text-xl font-black flex items-center gap-2 text-white">🏆 ModelRank</a>
      <div class="text-sm font-medium text-gray-400">
        <a href="index.html" class="hover:text-white mr-4">Leaderboard</a>
        <a href="collections.html" class="hover:text-white">Collections</a>
      </div>
    </div>
  </header>

  <main class="container mx-auto px-4 py-12 max-w-4xl">
    <div class="mb-8">
      <div class="flex justify-between text-xs font-bold text-gray-500 mb-2">
        <span>Step <span id="step-counter">1</span> of 3</span>
      </div>
      <div class="w-full bg-gray-800 rounded-full h-1.5">
        <div id="progress-bar" class="bg-blue-500 h-1.5 rounded-full transition-all duration-300" style="width: 33%"></div>
      </div>
    </div>

    <!-- Step 1 -->
    <div id="step-1" class="step-panel active">
      <h1 class="text-3xl font-black text-white mb-2">What is your primary use case?</h1>
      <p class="text-gray-400 mb-8">Select the task that represents 80%+ of what you'll use the model for.</p>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4" id="use-case-options">
        <div class="glass-card p-6 rounded-2xl card-option" data-value="chat">
          <div class="text-3xl mb-3">💬</div>
          <h3 class="text-lg font-bold text-white mb-1">Chat / Assistant</h3>
          <p class="text-sm text-gray-400">Conversational AI, customer support, general Q&A</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="code">
          <div class="text-3xl mb-3">💻</div>
          <h3 class="text-lg font-bold text-white mb-1">Code Generation</h3>
          <p class="text-sm text-gray-400">Write, explain, debug code — Python, JS, Go</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="rag">
          <div class="text-3xl mb-3">📖</div>
          <h3 class="text-lg font-bold text-white mb-1">RAG / Knowledge Base</h3>
          <p class="text-sm text-gray-400">Retrieve and summarize long documents</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="research">
          <div class="text-3xl mb-3">🔬</div>
          <h3 class="text-lg font-bold text-white mb-1">Research / Reasoning</h3>
          <p class="text-sm text-gray-400">Complex multi-step reasoning, PhD-level questions</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="multilingual">
          <div class="text-3xl mb-3">🌍</div>
          <h3 class="text-lg font-bold text-white mb-1">Multilingual</h3>
          <p class="text-sm text-gray-400">Support for non-English languages</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="edge">
          <div class="text-3xl mb-3">🏎️</div>
          <h3 class="text-lg font-bold text-white mb-1">Edge / On-device</h3>
          <p class="text-sm text-gray-400">Must run on laptop/mobile without cloud</p>
        </div>
      </div>
    </div>

    <!-- Step 2 -->
    <div id="step-2" class="step-panel">
      <button class="text-sm text-gray-400 hover:text-white flex items-center gap-1 mb-4" onclick="goToStep(1)">
        ← Back
      </button>
      <h1 class="text-3xl font-black text-white mb-2">What hardware will you run it on?</h1>
      <p class="text-gray-400 mb-8">This helps us filter out models that won't fit in your memory.</p>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4" id="hardware-options">
        <div class="glass-card p-6 rounded-2xl card-option" data-value="cloud">
          <div class="text-3xl mb-3">☁️</div>
          <h3 class="text-lg font-bold text-white mb-1">Cloud / API</h3>
          <p class="text-sm text-gray-400">Use via API, no local hardware constraints</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="high">
          <div class="text-3xl mb-3">🖥️</div>
          <h3 class="text-lg font-bold text-white mb-1">High-end GPU</h3>
          <p class="text-sm text-gray-400">RTX 4090, A100, 80GB+ VRAM</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="mid">
          <div class="text-3xl mb-3">💻</div>
          <h3 class="text-lg font-bold text-white mb-1">Mid-range GPU</h3>
          <p class="text-sm text-gray-400">RTX 3080/4070, 16-24GB VRAM</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="potato">
          <div class="text-3xl mb-3">🥔</div>
          <h3 class="text-lg font-bold text-white mb-1">Potato</h3>
          <p class="text-sm text-gray-400">CPU only or 8GB RAM — must be tiny</p>
        </div>
      </div>
    </div>

    <!-- Step 3 -->
    <div id="step-3" class="step-panel">
      <button class="text-sm text-gray-400 hover:text-white flex items-center gap-1 mb-4" onclick="goToStep(2)">
        ← Back
      </button>
      <h1 class="text-3xl font-black text-white mb-2">What's your priority?</h1>
      <p class="text-gray-400 mb-8">Trade-off between quality and speed.</p>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4" id="priority-options">
        <div class="glass-card p-6 rounded-2xl card-option" data-value="quality">
          <div class="text-3xl mb-3">🏆</div>
          <h3 class="text-lg font-bold text-white mb-1">Best quality</h3>
          <p class="text-sm text-gray-400">Highest possible score, I don't care about speed</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="balanced">
          <div class="text-3xl mb-3">⚡</div>
          <h3 class="text-lg font-bold text-white mb-1">Balanced</h3>
          <p class="text-sm text-gray-400">Good quality + reasonable speed</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="speed">
          <div class="text-3xl mb-3">🚀</div>
          <h3 class="text-lg font-bold text-white mb-1">Speed first</h3>
          <p class="text-sm text-gray-400">Fastest inference, good enough quality</p>
        </div>
      </div>
    </div>

    <!-- Results -->
    <div id="results" class="step-panel">
      <button class="text-sm text-gray-400 hover:text-white flex items-center gap-1 mb-4" onclick="goToStep(1); resetSelections();">
        ← Start Over
      </button>
      <h1 class="text-3xl font-black text-white mb-2">Top Recommendations</h1>
      <p class="text-gray-400 mb-8">Based on your selections: <span id="summary-text" class="text-blue-400 font-bold"></span></p>
      
      <div id="loading" class="text-center py-12">
        <span class="loading loading-spinner loading-lg text-primary"></span>
        <p class="mt-4 text-gray-400">Analyzing models...</p>
      </div>

      <div id="recommendations-container" class="space-y-4 hidden"></div>

      <div class="mt-8 flex gap-4 hidden" id="action-buttons">
        <a href="index.html" class="btn btn-outline">Compare all models</a>
        <button onclick="shareResults()" class="btn btn-primary">Share Results</button>
      </div>
    </div>
  </main>

  <script>
    let selections = { useCase: '', hardware: '', priority: '' };
    const LEADERBOARD_URL = 'leaderboard.json';
    let leaderboardData = null;

    function resetSelections() {
      selections = { useCase: '', hardware: '', priority: '' };
      document.querySelectorAll('.card-option').forEach(el => el.classList.remove('selected'));
    }

    function goToStep(step) {
      document.querySelectorAll('.step-panel').forEach(el => el.classList.remove('active'));
      document.getElementById(`step-${step}`)?.classList.add('active');
      document.getElementById('step-counter').innerText = step;
      document.getElementById('progress-bar').style.width = `${(step/3)*100}%`;
    }

    function handleSelection(step, key, value, el) {
      selections[key] = value;
      const parent = el.closest('.grid');
      parent.querySelectorAll('.card-option').forEach(card => card.classList.remove('selected'));
      el.classList.add('selected');
      
      setTimeout(() => {
        if (step < 3) {
          goToStep(step + 1);
        } else {
          showResults();
        }
      }, 300);
    }

    document.getElementById('use-case-options').addEventListener('click', e => {
      const card = e.target.closest('.card-option');
      if(card) handleSelection(1, 'useCase', card.dataset.value, card);
    });
    document.getElementById('hardware-options').addEventListener('click', e => {
      const card = e.target.closest('.card-option');
      if(card) handleSelection(2, 'hardware', card.dataset.value, card);
    });
    document.getElementById('priority-options').addEventListener('click', e => {
      const card = e.target.closest('.card-option');
      if(card) handleSelection(3, 'priority', card.dataset.value, card);
    });

    function calcFit(model, useCase, hardware, priority) {
      let score = model.composite;
      const b = model.breakdown || {};
      
      // Use case adjustments
      if (useCase === 'code') score += (b.benchmarks || 0) * 0.3;
      if (useCase === 'edge') score += (b.efficiency || 0) * 0.5 - (model.composite * 0.2);
      if (useCase === 'multilingual') score += (b.community || 0) * 0.2;
      if (useCase === 'research') score += (b.benchmarks || 0) * 0.4;
      
      // Hardware filter
      const eff = b.efficiency || 0;
      if (hardware === 'potato') { if (eff < 70) score -= 40; else score += 20; }
      if (hardware === 'mid') { if (eff < 40) score -= 20; }
      
      // Priority
      if (priority === 'speed') score += (b.efficiency || 0) * 0.3;
      if (priority === 'quality') score += (b.benchmarks || 0) * 0.2;
      
      return score;
    }

    async function fetchLeaderboard() {
      if (leaderboardData) return leaderboardData;
      try {
        const res = await fetch(LEADERBOARD_URL);
        leaderboardData = await res.json();
        return leaderboardData;
      } catch (err) {
        console.error(err);
        return { models: [] };
      }
    }

    async function showResults() {
      document.querySelectorAll('.step-panel').forEach(el => el.classList.remove('active'));
      document.getElementById('results').classList.add('active');
      document.getElementById('progress-bar').style.width = '100%';
      
      const labels = {
        chat: 'Chat', code: 'Code', rag: 'RAG', research: 'Research', multilingual: 'Multilingual', edge: 'Edge',
        cloud: 'Cloud', high: 'High-end GPU', mid: 'Mid-range GPU', potato: 'Potato PC',
        quality: 'Quality', balanced: 'Balanced', speed: 'Speed'
      };
      document.getElementById('summary-text').innerText = `${labels[selections.useCase]} on ${labels[selections.hardware]} (${labels[selections.priority]})`;
      
      const data = await fetchLeaderboard();
      document.getElementById('loading').classList.add('hidden');
      
      const scored = data.models.map(m => ({
        ...m,
        fit: calcFit(m, selections.useCase, selections.hardware, selections.priority)
      })).sort((a, b) => b.fit - a.fit).slice(0, 3);
      
      const container = document.getElementById('recommendations-container');
      container.innerHTML = '';
      container.classList.remove('hidden');
      document.getElementById('action-buttons').classList.remove('hidden');

      scored.forEach((m, idx) => {
        const parts = m.model_id.split('/');
        const name = parts.length > 1 ? parts[1] : m.model_id;
        const org = parts.length > 1 ? parts[0] : '';
        const html = `
          <div class="glass-card p-6 rounded-2xl flex flex-col md:flex-row gap-6 items-center border-l-4 ${idx===0 ? 'border-l-blue-500' : 'border-l-gray-600'}">
            <div class="text-4xl font-black text-gray-500">#${idx+1}</div>
            <div class="flex-1">
              <div class="text-xs text-gray-500">${org}</div>
              <h3 class="text-xl font-bold text-white"><a href="https://huggingface.co/${m.model_id}" target="_blank" class="hover:underline">${name}</a></h3>
              <p class="text-sm text-gray-400 mt-1">Score: <span class="text-blue-400 font-bold">${m.composite.toFixed(1)}</span> • Tier: <span class="badge badge-sm badge-outline">${m.tier}</span> • Efficiency: ${m.breakdown?.efficiency?.toFixed(1)||'N/A'}</p>
              <p class="text-sm text-gray-300 mt-2 bg-white/5 p-2 rounded italic">"Best fit due to high ${selections.priority==='speed'||selections.hardware==='potato'?'efficiency':'benchmark performance'} for this hardware."</p>
            </div>
            <div>
              <img src="${m.badge_url}" alt="Score Badge" class="h-8">
            </div>
          </div>
        `;
        container.innerHTML += html;
      });
      
      window.shareText = `ModelRank recommends ${scored[0]?.model_id || 'these models'} for ${labels[selections.useCase]} on ${labels[selections.hardware]}. Check it out at ModelRank!`;
    }
    
    function shareResults() {
      const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(window.shareText)}`;
      window.open(url, '_blank');
    }
  </script>
</body>
</html>"""


def generate_collections_html() -> str:
    """Generate the curated collections page."""
    return """<!DOCTYPE html>
<html lang="en" class="dark" data-theme="dark">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>ModelRank — Model Collections</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://cdn.jsdelivr.net/npm/daisyui@3.9.0/dist/full.css" rel="stylesheet" type="text/css" />
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: { base: '#0a0a0f', surface: '#13131a', border: '#232330' },
          fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'], mono: ['JetBrains Mono', 'monospace'] }
        }
      }
    }
  </script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700;800&display=swap" rel="stylesheet"/>
  <style>
    body { background-color: #0a0a0f; color: #f1f5f9; font-family: 'Inter', sans-serif; }
    .glass-card { background: rgba(19, 19, 26, 0.7); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }
    details > summary { list-style: none; }
    details > summary::-webkit-details-marker { display: none; }
  </style>
</head>
<body class="min-h-screen text-gray-200">
  <header class="pt-16 pb-12 border-b border-white/5 relative overflow-hidden">
    <div class="absolute top-0 right-0 w-[400px] h-[400px] bg-purple-600/10 blur-[120px] rounded-full pointer-events-none"></div>
    <div class="container mx-auto px-4 max-w-6xl relative z-10">
      <nav class="flex items-center justify-between mb-12">
        <a href="index.html" class="text-2xl font-black tracking-tight flex items-center gap-2 text-white">🏆 ModelRank</a>
        <div class="flex items-center gap-6 text-sm font-medium text-gray-400">
          <a href="index.html" class="hover:text-white">Leaderboard</a>
          <a href="dna.html" class="hover:text-white">Model DNA</a>
          <a href="quiz.html" class="hover:text-white">Quiz</a>
        </div>
      </nav>
      <h1 class="text-4xl md:text-5xl font-black text-white mb-4">Model Collections</h1>
      <p class="text-xl text-gray-400">Curated lists of top performers by category</p>
      <p class="text-sm text-gray-500 mt-2" id="last-updated">Last updated: fetching...</p>
    </div>
  </header>

  <main class="container mx-auto px-4 py-12 max-w-6xl">
    <div class="grid grid-cols-1 gap-6" id="collections-container">
      <div class="text-center py-12"><span class="loading loading-spinner loading-lg text-primary"></span></div>
    </div>
  </main>

  <script>
    async function loadCollections() {
      try {
        const res = await fetch('leaderboard.json');
        const data = await res.json();
        document.getElementById('last-updated').innerText = 'Last updated: ' + (data.updated_at || new Date().toISOString());
        
        const models = data.models || [];
        
        const collections = [
          {
            id: 'top-overall',
            title: '🏆 Top Overall',
            desc: 'Top 10 models by composite score',
            models: [...models].sort((a,b) => b.composite - a.composite).slice(0, 10)
          },
          {
            id: 'efficiency',
            title: '⚡ Efficiency Champions',
            desc: 'Top 10 by efficiency score (best for edge/CPU)',
            models: [...models].sort((a,b) => (b.breakdown?.efficiency||0) - (a.breakdown?.efficiency||0)).slice(0, 10)
          },
          {
            id: 'code',
            title: '💻 Best for Code',
            desc: 'Models excelling in coding benchmarks (simulated)',
            models: [...models].filter(m => m.model_id.toLowerCase().includes('coder') || m.model_id.toLowerCase().includes('code') || m.composite > 75).slice(0, 10)
          },
          {
            id: 'trending',
            title: '🔥 Trending Right Now',
            desc: 'Top 10 by community score',
            models: [...models].sort((a,b) => (b.breakdown?.community||0) - (a.breakdown?.community||0)).slice(0, 10)
          },
          {
            id: 'fresh',
            title: '🆕 Freshest Models',
            desc: 'Top 10 by recency score',
            models: [...models].sort((a,b) => (b.breakdown?.recency||0) - (a.breakdown?.recency||0)).slice(0, 10)
          },
          {
            id: 'sa-tier',
            title: '💜 S & A Tier Only',
            desc: 'Elite models scoring 80+',
            models: [...models].filter(m => m.tier === 'S' || m.tier === 'A').sort((a,b) => b.composite - a.composite)
          }
        ];

        const container = document.getElementById('collections-container');
        container.innerHTML = '';
        
        collections.forEach(col => {
          let rowsHtml = '';
          col.models.forEach(m => {
            const parts = m.model_id.split('/');
            const name = parts.length > 1 ? parts[1] : m.model_id;
            rowsHtml += `
              <div class="flex items-center justify-between p-3 border-b border-white/5 hover:bg-white/5">
                <div class="flex items-center gap-3">
                  <span class="text-gray-500 font-mono text-sm">#${m.rank}</span>
                  <a href="https://huggingface.co/${m.model_id}" class="text-white font-bold hover:underline">${name}</a>
                </div>
                <div class="flex items-center gap-4">
                  <span class="text-blue-400 font-mono font-bold">${m.composite.toFixed(1)}</span>
                  <span class="badge badge-sm badge-outline">${m.tier}</span>
                  <button onclick="navigator.clipboard.writeText('![ModelRank](${m.badge_url})')" class="btn btn-xs btn-ghost text-gray-400">Copy Badge</button>
                </div>
              </div>
            `;
          });

          const html = `
            <details class="glass-card rounded-2xl group" ${col.id === 'top-overall' ? 'open' : ''}>
              <summary class="p-6 cursor-pointer flex justify-between items-center">
                <div>
                  <h2 class="text-2xl font-black text-white">${col.title}</h2>
                  <p class="text-gray-400 text-sm mt-1">${col.desc} — ${col.models.length} models</p>
                </div>
                <div class="text-gray-500 transition-transform group-open:rotate-180">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
                </div>
              </summary>
              <div class="px-6 pb-6 pt-2 border-t border-white/5">
                ${rowsHtml}
              </div>
            </details>
          `;
          container.innerHTML += html;
        });

      } catch (err) {
        document.getElementById('collections-container').innerHTML = '<p class="text-red-500">Failed to load collections.</p>';
      }
    }
    loadCollections();
  </script>
</body>
</html>"""

def generate_pricing_html() -> str:
    """Generate the premium pricing landing page for ModelRank Pro."""
    return '''<!DOCTYPE html>
<html data-theme="dark" lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ModelRank Pro — Embeddable AI Model Badges & Rankings</title>
  <meta name="description" content="Get premium embeddable badges, priority scoring, and detailed research reports for your HuggingFace models.">
  <link href="https://cdn.jsdelivr.net/npm/daisyui@4/dist/full.min.css" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-base-200">
  <!-- Navbar -->
  <div class="navbar bg-base-100 shadow-sm border-b border-base-200">
    <div class="flex-1">
      <a href="index.html" class="btn btn-ghost text-xl font-black">🏆 ModelRank</a>
    </div>
    <div class="flex-none gap-2">
      <a href="index.html" class="btn btn-ghost">Leaderboard</a>
      <a href="#pricing" class="btn btn-primary">Get Pro</a>
    </div>
  </div>

  <!-- Hero Section -->
  <div class="hero min-h-[50vh] bg-base-200 py-16">
    <div class="hero-content text-center">
      <div class="max-w-3xl">
        <h1 class="text-5xl md:text-6xl font-black tracking-tight mb-6">The Trust Signal Every AI Model Needs</h1>
        <p class="py-4 text-xl text-base-content/70">ModelRank gives your HuggingFace model a composite score, tier badge, and leaderboard rank — automatically.</p>
        <div class="flex gap-4 justify-center mt-8">
          <a href="index.html" class="btn btn-outline btn-lg">See the Leaderboard</a>
          <a href="#pricing" class="btn btn-primary btn-lg">Get Pro Badges</a>
        </div>
      </div>
    </div>
  </div>

  <!-- Social Proof Bar -->
  <div class="container mx-auto px-4 -mt-8 relative z-10">
    <div class="stats shadow w-full border border-base-300 bg-base-100 flex flex-col md:flex-row">
      <div class="stat place-items-center py-6">
        <div class="stat-value text-primary">100+</div>
        <div class="stat-title font-bold uppercase tracking-wider text-xs mt-2">Models Ranked</div>
      </div>
      <div class="stat place-items-center py-6 border-t md:border-t-0 md:border-l border-base-300">
        <div class="stat-value text-secondary">5</div>
        <div class="stat-title font-bold uppercase tracking-wider text-xs mt-2">Scoring Dimensions</div>
      </div>
      <div class="stat place-items-center py-6 border-t md:border-t-0 md:border-l border-base-300">
        <div class="stat-value text-accent">13</div>
        <div class="stat-title font-bold uppercase tracking-wider text-xs mt-2">Benchmarks Tracked</div>
      </div>
    </div>
  </div>

  <!-- Badge Gallery -->
  <div class="container mx-auto px-4 py-24">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-black mb-4">Beautiful Embeddable Badges</h2>
      <p class="text-base-content/70 text-lg">Showcase your model's quality directly in your README.</p>
    </div>
    
    <div class="grid md:grid-cols-2 gap-12 max-w-5xl mx-auto">
      <!-- Free Badges -->
      <div class="card bg-base-100 border border-base-300 shadow-xl">
        <div class="card-body">
          <h3 class="card-title text-2xl font-bold border-b border-base-300 pb-4 mb-4">Free Badges</h3>
          
          <div class="space-y-8">
            <div>
              <p class="text-sm font-bold text-base-content/50 uppercase tracking-wide mb-3">Score Badge</p>
              <div class="bg-base-300 p-6 rounded-lg flex justify-center items-center mb-2">
                <!-- Static plain badge -->
                <svg xmlns="http://www.w3.org/2000/svg" width="200" height="36">
                  <defs>
                    <linearGradient id="bg_free" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stop-color="#0f0f23"/>
                      <stop offset="100%" stop-color="#1a1a36"/>
                    </linearGradient>
                  </defs>
                  <rect width="200" height="36" rx="7" fill="url(#bg_free)" stroke="#3b82f6" stroke-width="1.2"/>
                  <rect x="0" y="0" width="4" height="36" rx="3" fill="#3b82f6"/>
                  <text x="12" y="13" font-family="-apple-system,system-ui,sans-serif" font-size="8" fill="#64748b" font-weight="600" letter-spacing="0.6">MODELRANK</text>
                  <text x="12" y="27" font-family="-apple-system,system-ui,sans-serif" font-size="12" fill="#f1f5f9" font-weight="600">Llama-3-8B</text>
                  <text x="155" y="13" font-family="-apple-system,system-ui,sans-serif" font-size="8" fill="#64748b" text-anchor="middle">SCORE</text>
                  <text x="155" y="28" font-family="-apple-system,system-ui,sans-serif" font-size="15" fill="#22c55e" font-weight="900" text-anchor="middle">85</text>
                  <rect x="178" y="8" width="18" height="20" rx="4" fill="#3b82f6"/>
                  <text x="187" y="22" font-family="-apple-system,system-ui,sans-serif" font-size="11" fill="#000" font-weight="900" text-anchor="middle">A</text>
                </svg>
              </div>
            </div>
            
            <div>
              <p class="text-sm font-bold text-base-content/50 uppercase tracking-wide mb-3">Tier &amp; Rank Badges</p>
              <div class="bg-base-300 p-6 rounded-lg flex flex-wrap gap-4 justify-center items-center mb-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="100" height="28">
                  <rect width="100" height="28" rx="6" fill="#0f0f23" stroke="#a855f7" stroke-width="1.2"/>
                  <text x="36" y="13" font-family="-apple-system,system-ui,sans-serif" font-size="7" fill="#64748b" letter-spacing="0.5">MODELRANK</text>
                  <rect x="62" y="4" width="32" height="20" rx="5" fill="#a855f7"/>
                  <text x="78" y="18" font-family="-apple-system,system-ui,sans-serif" font-size="12" fill="#000" font-weight="900" text-anchor="middle">S</text>
                  <text x="5" y="18" font-family="-apple-system,system-ui,sans-serif" font-size="8" fill="#94a3b8">Tier</text>
                </svg>
                <svg xmlns="http://www.w3.org/2000/svg" width="110" height="28">
                  <rect width="110" height="28" rx="6" fill="#0f0f23" stroke="#22c55e" stroke-width="1.2"/>
                  <text x="4" y="12" font-family="-apple-system,system-ui,sans-serif" font-size="7" fill="#64748b" letter-spacing="0.5">MODELRANK RANK</text>
                  <text x="4" y="24" font-family="-apple-system,system-ui,sans-serif" font-size="13" fill="#22c55e" font-weight="800">#1</text>
                  <text x="50" y="24" font-family="-apple-system,system-ui,sans-serif" font-size="9" fill="#64748b">/ 100</text>
                </svg>
              </div>
            </div>
            
            <div class="mockup-code bg-base-300 text-xs">
              <pre data-prefix="$"><code>![ModelRank](https://.../score.svg)</code></pre>
            </div>
          </div>
        </div>
      </div>

      <!-- Pro Badges -->
      <div class="card bg-base-100 border border-primary/50 shadow-2xl relative overflow-hidden">
        <div class="absolute top-0 right-0 bg-primary text-primary-content text-xs font-bold px-4 py-1 rounded-bl-lg z-10">PRO</div>
        <div class="card-body relative z-0">
          <div class="absolute inset-0 bg-gradient-to-br from-primary/5 to-secondary/5 -z-10"></div>
          <h3 class="card-title text-2xl font-bold border-b border-primary/20 pb-4 mb-4 text-primary">Pro Badges</h3>
          
          <div class="space-y-8">
            <div>
              <p class="text-sm font-bold text-base-content/50 uppercase tracking-wide mb-3 flex items-center gap-2">
                Animated Gold Badge
                <span class="badge badge-xs badge-secondary">NEW</span>
              </p>
              <div class="bg-base-300 p-6 rounded-lg flex justify-center items-center mb-2 border border-warning/30 shadow-[0_0_15px_rgba(250,204,21,0.15)] relative overflow-hidden">
                <!-- Gold Animated Badge SVG -->
                <svg xmlns="http://www.w3.org/2000/svg" width="220" height="40">
                  <defs>
                    <linearGradient id="goldbg" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stop-color="#3f2b00"/>
                      <stop offset="50%" stop-color="#1f1500"/>
                      <stop offset="100%" stop-color="#3f2b00"/>
                    </linearGradient>
                    <linearGradient id="shimmer" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stop-color="rgba(255,215,0,0)"/>
                      <stop offset="50%" stop-color="rgba(255,215,0,0.4)"/>
                      <stop offset="100%" stop-color="rgba(255,215,0,0)"/>
                    </linearGradient>
                    <filter id="goldglow">
                      <feGaussianBlur stdDeviation="2" result="blur"/>
                      <feMerge>
                        <feMergeNode in="blur"/>
                        <feMergeNode in="SourceGraphic"/>
                      </feMerge>
                    </filter>
                  </defs>
                  
                  <rect width="220" height="40" rx="8" fill="url(#goldbg)" stroke="#fbbf24" stroke-width="1.5"/>
                  
                  <!-- Shimmer animation -->
                  <rect width="220" height="40" rx="8" fill="url(#shimmer)">
                    <animate attributeName="x" from="-220" to="220" dur="2.5s" repeatCount="indefinite" />
                  </rect>
                  
                  <rect x="0" y="0" width="5" height="40" rx="4" fill="#fbbf24"/>
                  
                  <text x="15" y="15" font-family="-apple-system,system-ui,sans-serif" font-size="9" fill="#fcd34d" font-weight="700" letter-spacing="1">MODELRANK PRO</text>
                  <text x="15" y="30" font-family="-apple-system,system-ui,sans-serif" font-size="13" fill="#fff" font-weight="600">Mistral-Large</text>
                  
                  <text x="165" y="15" font-family="-apple-system,system-ui,sans-serif" font-size="8" fill="#fcd34d" text-anchor="middle">SCORE</text>
                  <text x="165" y="31" font-family="-apple-system,system-ui,sans-serif" font-size="17" fill="#fbbf24" font-weight="900" text-anchor="middle" filter="url(#goldglow)">96</text>
                  
                  <rect x="190" y="9" width="20" height="22" rx="4" fill="#fbbf24"/>
                  <text x="200" y="24" font-family="-apple-system,system-ui,sans-serif" font-size="12" fill="#000" font-weight="900" text-anchor="middle">S</text>
                </svg>
              </div>
            </div>
            
            <div>
              <p class="text-sm font-bold text-base-content/50 uppercase tracking-wide mb-3">Glow Effect Badge</p>
              <div class="bg-base-300 p-6 rounded-lg flex flex-wrap gap-4 justify-center items-center mb-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="120" height="32">
                  <defs>
                    <filter id="neon">
                      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                      <feMerge>
                        <feMergeNode in="coloredBlur"/>
                        <feMergeNode in="SourceGraphic"/>
                      </feMerge>
                    </filter>
                  </defs>
                  <rect width="120" height="32" rx="8" fill="#000" stroke="#a855f7" stroke-width="1.5" filter="url(#neon)"/>
                  <rect width="120" height="32" rx="8" fill="#000" stroke="#a855f7" stroke-width="1.5"/>
                  <text x="40" y="14" font-family="-apple-system,system-ui,sans-serif" font-size="8" fill="#d8b4fe" letter-spacing="0.5">MODELRANK</text>
                  <rect x="75" y="5" width="38" height="22" rx="5" fill="#a855f7"/>
                  <text x="94" y="20" font-family="-apple-system,system-ui,sans-serif" font-size="14" fill="#000" font-weight="900" text-anchor="middle">S+</text>
                  <text x="8" y="20" font-family="-apple-system,system-ui,sans-serif" font-size="9" fill="#e9d5ff" font-weight="600">Tier</text>
                </svg>
              </div>
            </div>
            
            <div class="mockup-code bg-base-300 text-xs border border-primary/30">
              <pre data-prefix="$" class="text-primary"><code>![ModelRank](https://.../pro-score.svg)</code></pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Pricing Cards Section -->
  <div id="pricing" class="container mx-auto px-4 py-24 bg-base-300/50 rounded-3xl mb-24">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-black mb-4">Simple, transparent pricing</h2>
      <p class="text-base-content/70 text-lg">Choose the right plan for your open-source model.</p>
    </div>
    
    <div class="grid lg:grid-cols-3 gap-8 max-w-6xl mx-auto items-center">
      
      <!-- Free Plan -->
      <div class="card bg-base-100 shadow-xl border border-base-200 hover:border-base-300 transition-colors">
        <div class="card-body">
          <h3 class="text-2xl font-black">Free</h3>
          <div class="my-4">
            <span class="text-5xl font-black">$0</span>
            <span class="text-base-content/50">/mo</span>
          </div>
          <p class="text-sm text-base-content/70 mb-6">Essential trust signals for any model.</p>
          <ul class="space-y-4 mb-8">
            <li class="flex items-center gap-3">
              <svg class="w-5 h-5 text-success shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
              <span>Score Badge</span>
            </li>
            <li class="flex items-center gap-3">
              <svg class="w-5 h-5 text-success shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
              <span>Tier Badge</span>
            </li>
            <li class="flex items-center gap-3">
              <svg class="w-5 h-5 text-success shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
              <span>Rank Badge</span>
            </li>
            <li class="flex items-center gap-3">
              <svg class="w-5 h-5 text-success shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
              <span>Public Leaderboard Listing</span>
            </li>
            <li class="flex items-center gap-3">
              <svg class="w-5 h-5 text-success shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
              <span>Standard SVG Badges</span>
            </li>
          </ul>
          <div class="card-actions mt-auto">
            <a href="index.html" class="btn btn-outline btn-block">Get Started Free</a>
          </div>
        </div>
      </div>
      
      <!-- Pro Plan -->
      <div class="card bg-base-100 shadow-2xl border-2 border-primary scale-105 z-10 relative">
        <div class="absolute top-0 right-0 left-0 bg-primary text-primary-content text-center text-sm font-bold py-1">MOST POPULAR</div>
        <div class="card-body pt-10">
          <h3 class="text-2xl font-black text-primary">Pro</h3>
          <div class="my-4">
            <span class="text-5xl font-black">$29</span>
            <span class="text-base-content/50">/mo</span>
          </div>
          <p class="text-sm text-base-content/70 mb-6">For serious model creators who want to stand out.</p>
          <p class="text-sm font-bold mb-2">Everything in Free, plus:</p>
          <ul class="space-y-4 mb-8">
            <li class="flex items-center gap-3">
              <svg class="w-5 h-5 text-primary shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
              <span class="font-medium text-base-content">Animated Gold Badge</span>
            </li>
            <li class="flex items-center gap-3">
              <svg class="w-5 h-5 text-primary shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
              <span class="font-medium text-base-content">Glow Effect Badge</span>
            </li>
            <li class="flex items-center gap-3">
              <svg class="w-5 h-5 text-primary shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
              <span>Priority re-scoring (&lt;1hr)</span>
            </li>
            <li class="flex items-center gap-3">
              <svg class="w-5 h-5 text-primary shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
              <span>Shields.io endpoint</span>
            </li>
            <li class="flex items-center gap-3">
              <svg class="w-5 h-5 text-primary shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
              <span>API access</span>
            </li>
            <li class="flex items-center gap-3">
              <svg class="w-5 h-5 text-primary shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
              <span>Featured in Weekly Report</span>
            </li>
          </ul>
          <div class="card-actions mt-auto">
            <a href="#" class="btn btn-primary btn-block">Buy Pro &rarr;</a>
          </div>
        </div>
      </div>
      
      <!-- Featured Plan -->
      <div class="card bg-base-100 shadow-xl border border-base-200 hover:border-base-300 transition-colors">
        <div class="card-body">
          <h3 class="text-2xl font-black">Featured</h3>
          <div class="my-4">
            <span class="text-5xl font-black">$149</span>
            <span class="text-base-content/50">one-time</span>
          </div>
          <p class="text-sm text-base-content/70 mb-6">Maximum visibility for a major model launch.</p>
          <ul class="space-y-4 mb-8">
            <li class="flex items-center gap-3">
              <svg class="w-5 h-5 text-warning shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
              <span class="font-bold">Permanent Featured Placement</span>
            </li>
            <li class="flex items-center gap-3">
              <svg class="w-5 h-5 text-warning shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
              <span>Homepage leaderboard row highlight</span>
            </li>
            <li class="flex items-center gap-3">
              <svg class="w-5 h-5 text-warning shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
              <span>Custom research report</span>
            </li>
            <li class="flex items-center gap-3">
              <svg class="w-5 h-5 text-warning shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
              <span>Direct outreach to your community</span>
            </li>
            <li class="flex items-center gap-3">
              <svg class="w-5 h-5 text-warning shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
              <span>"Verified Featured" badge</span>
            </li>
          </ul>
          <div class="card-actions mt-auto">
            <a href="#" class="btn btn-outline btn-block">Get Featured &rarr;</a>
          </div>
        </div>
      </div>
      
    </div>
  </div>

  <!-- How It Works -->
  <div class="container mx-auto px-4 py-16 mb-16 border-t border-base-300">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-black mb-4">How It Works</h2>
    </div>
    
    <div class="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
      <div class="text-center p-6">
        <div class="w-16 h-16 bg-primary/20 text-primary rounded-2xl flex items-center justify-center mx-auto mb-6">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
        </div>
        <h3 class="text-xl font-bold mb-3">1. We score your model</h3>
        <p class="text-base-content/70">Using 5 dimensions + 13 benchmarks to calculate an objective composite score.</p>
      </div>
      
      <div class="text-center p-6">
        <div class="w-16 h-16 bg-secondary/20 text-secondary rounded-2xl flex items-center justify-center mx-auto mb-6">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>
        </div>
        <h3 class="text-xl font-bold mb-3">2. Embed your badge</h3>
        <p class="text-base-content/70">Copy a simple one-line markdown snippet into your HuggingFace README or GitHub.</p>
      </div>
      
      <div class="text-center p-6">
        <div class="w-16 h-16 bg-accent/20 text-accent rounded-2xl flex items-center justify-center mx-auto mb-6">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" /></svg>
        </div>
        <h3 class="text-xl font-bold mb-3">3. Developers trust your model</h3>
        <p class="text-base-content/70">A verified, objective signal builds confidence and increases downloads.</p>
      </div>
    </div>
  </div>

  <!-- FAQ Section -->
  <div class="container mx-auto px-4 py-16 max-w-3xl mb-24">
    <div class="text-center mb-12">
      <h2 class="text-3xl font-black mb-4">Frequently Asked Questions</h2>
    </div>
    
    <div class="join join-vertical w-full bg-base-100 border border-base-300">
      <div class="collapse collapse-arrow join-item border border-base-300">
        <input type="radio" name="my-accordion-4" checked="checked" /> 
        <div class="collapse-title text-xl font-medium">How is the score calculated?</div>
        <div class="collapse-content">
          <p class="text-base-content/70">We use a composite scoring algorithm that evaluates 5 dimensions: independent benchmarks, computational efficiency, community engagement, model architecture, and freshness. All scores are objective and verified.</p>
        </div>
      </div>
      <div class="collapse collapse-arrow join-item border border-base-300">
        <input type="radio" name="my-accordion-4" /> 
        <div class="collapse-title text-xl font-medium">Do I need an account?</div>
        <div class="collapse-content">
          <p class="text-base-content/70">No! The free tier works instantly for any publicly available HuggingFace model. Just copy the badge URL. For Pro and Featured tiers, we'll send you a secure management link.</p>
        </div>
      </div>
      <div class="collapse collapse-arrow join-item border border-base-300">
        <input type="radio" name="my-accordion-4" /> 
        <div class="collapse-title text-xl font-medium">Can I embed badges in my README?</div>
        <div class="collapse-content">
          <p class="text-base-content/70">Yes. All badges are served as highly-optimized SVGs that work perfectly in HuggingFace model cards, GitHub READMEs, and personal websites.</p>
        </div>
      </div>
      <div class="collapse collapse-arrow join-item border border-base-300">
        <input type="radio" name="my-accordion-4" /> 
        <div class="collapse-title text-xl font-medium">What is the refund policy?</div>
        <div class="collapse-content">
          <p class="text-base-content/70">We offer a 14-day money-back guarantee for Pro subscriptions if you're not satisfied with the premium badges or priority scoring.</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Footer -->
  <footer class="footer items-center p-8 bg-neutral text-neutral-content">
    <aside class="items-center grid-flow-col">
      <span class="text-xl font-black mr-2">🏆 ModelRank</span> 
      <p>Copyright &copy; 2026 - All rights reserved</p>
    </aside> 
    <nav class="grid-flow-col gap-4 md:place-self-center md:justify-self-end">
      <a href="index.html" class="link link-hover">Leaderboard</a>
      <a href="https://github.com/rankmodel/rankmodel1" class="link link-hover">GitHub</a>
      <a href="#" class="link link-hover">Back to top ↑</a>
    </nav>
  </footer>
</body>
</html>'''


def generate_methodology_html() -> str:
    """Generate the methodology page."""
    return """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>ModelRank Scoring Methodology — How We Evaluate Open-Weight AI Models</title>
  <link href="https://cdn.jsdelivr.net/npm/daisyui@3.9.0/dist/full.css" rel="stylesheet" type="text/css" />
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: { base: '#0a0a0f', surface: '#13131a', border: '#232330' },
          fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'], mono: ['JetBrains Mono', 'monospace'] }
        }
      }
    }
  </script>
  <style>body { background-color: #0a0a0f; color: #f1f5f9; font-family: 'Inter', sans-serif; } .glass-card { background: rgba(19, 19, 26, 0.7); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }</style>
</head>
<body class="min-h-screen text-gray-200">
  <div class="container mx-auto px-4 py-12 max-w-4xl">
    <div class="mb-8"><a href="index.html" class="btn btn-outline btn-sm border-white/20 text-gray-300 hover:bg-white/10 hover:border-white/30">← Back to Leaderboard</a></div>
    <h1 class="text-4xl md:text-5xl font-black mb-6 tracking-tight text-white">ModelRank Scoring Methodology</h1>
    <p class="text-xl text-gray-400 mb-12">Built for developers, not marketing teams. Every score is reproducible, open-source, and conflict-of-interest-free.</p>
    
    <div class="space-y-12">
      <section>
        <h2 class="text-3xl font-bold mb-6 text-white">1. The Five Dimensions</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="glass-card p-6 rounded-2xl border-t-4 border-blue-500">
            <h3 class="font-bold text-xl mb-1 text-white">Benchmarks (40%)</h3>
            <p class="text-sm text-gray-400 mb-2">Evaluates logical reasoning, coding, math, and knowledge.</p>
            <p class="text-xs text-gray-500">Sources: HuggingFace Evals, Open LLM Leaderboard V2. A 90/100 means top-tier reasoning. Limitation: Does not capture creative writing preference.</p>
          </div>
          <div class="glass-card p-6 rounded-2xl border-t-4 border-green-500">
            <h3 class="font-bold text-xl mb-1 text-white">Efficiency (20%)</h3>
            <p class="text-sm text-gray-400 mb-2">Throughput, VRAM usage, and parameter-to-performance ratio.</p>
            <p class="text-xs text-gray-500">Sources: Context length metadata, param count. A 90/100 means runs fast on consumer GPUs. Limitation: Static estimates, not real-time profiling.</p>
          </div>
          <div class="glass-card p-6 rounded-2xl border-t-4 border-purple-500">
            <h3 class="font-bold text-xl mb-1 text-white">Community (20%)</h3>
            <p class="text-sm text-gray-400 mb-2">Usage, momentum, and mindshare.</p>
            <p class="text-xs text-gray-500">Sources: HF Downloads, likes. A 90/100 means mass adoption. Limitation: Can be skewed by early hype or bots.</p>
          </div>
          <div class="glass-card p-6 rounded-2xl border-t-4 border-yellow-500">
            <h3 class="font-bold text-xl mb-1 text-white">Freshness (10%)</h3>
            <p class="text-sm text-gray-400 mb-2">Time since release and update frequency.</p>
            <p class="text-xs text-gray-500">Sources: Last modified dates. A 90/100 means updated this week. Limitation: Penalizes stable, completed models over time.</p>
          </div>
          <div class="glass-card p-6 rounded-2xl border-t-4 border-red-500">
            <h3 class="font-bold text-xl mb-1 text-white">Reproducibility (10%)</h3>
            <p class="text-sm text-gray-400 mb-2">Open weights, clear license, verified origin.</p>
            <p class="text-xs text-gray-500">Sources: Hub metadata, safetensors presence. A 90/100 means fully open (MIT/Apache) and safe.</p>
          </div>
        </div>
      </section>

      <section>
        <h2 class="text-3xl font-bold mb-6 text-white">2. Benchmark Coverage Table</h2>
        <div class="glass-card rounded-2xl overflow-hidden">
          <table class="table w-full">
            <thead class="bg-white/5 text-gray-300">
              <tr><th>Benchmark</th><th>Domain</th><th>Source</th><th>Weight</th><th>Notes</th></tr>
            </thead>
            <tbody class="text-sm text-gray-400">
              <tr class="border-b border-white/5"><td>MMLU-Pro</td><td>General knowledge</td><td>HuggingFace Evals</td><td>20%</td><td>...</td></tr>
              <tr class="border-b border-white/5"><td>GPQA Diamond</td><td>PhD-level reasoning</td><td>idavidrein/gpqa</td><td>20%</td><td>...</td></tr>
              <tr class="border-b border-white/5"><td>HLE</td><td>Expert-level</td><td>...</td><td>15%</td><td>Humanity's Last Exam</td></tr>
              <tr class="border-b border-white/5"><td>GSM8K</td><td>Math word problems</td><td>...</td><td>10%</td><td></td></tr>
              <tr class="border-b border-white/5"><td>HumanEval</td><td>Code generation</td><td>openai/...</td><td>10%</td><td></td></tr>
              <tr class="border-b border-white/5"><td>BBH</td><td>Big-Bench Hard</td><td>...</td><td>8%</td><td></td></tr>
              <tr class="border-b border-white/5"><td>IFEval</td><td>Instruction following</td><td>...</td><td>7%</td><td></td></tr>
              <tr class="border-b border-white/5"><td>MuSR</td><td>Multi-step reasoning</td><td>...</td><td>5%</td><td></td></tr>
              <tr class="border-b border-white/5"><td>MATH</td><td>Advanced math</td><td>...</td><td>5%</td><td></td></tr>
              <tr class="border-b border-white/5"><td>ARC-Challenge</td><td>Science reasoning</td><td>...</td><td>fallback</td><td></td></tr>
              <tr class="border-b border-white/5"><td>HellaSwag</td><td>Commonsense NLI</td><td>...</td><td>fallback</td><td></td></tr>
              <tr class="border-b border-white/5"><td>TruthfulQA</td><td>Factual accuracy</td><td>...</td><td>fallback</td><td></td></tr>
              <tr><td>WinoGrande</td><td>Winograd schema</td><td>...</td><td>fallback</td><td></td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 class="text-3xl font-bold mb-4 text-white">3. Normalization & Confidence</h2>
        <p class="text-gray-400">Raw benchmark values from HF are 0.0-1.0, we multiply by 100. Frontier benchmarks (MMLU-Pro, GPQA etc.) take priority. When only classic benchmarks found: 0.85x confidence penalty, capped at 75/100. Coverage confidence: high/medium/low based on how many benchmarks found.</p>
      </section>

      <section>
        <h2 class="text-3xl font-bold mb-6 text-white">4. Tier System</h2>
        <div class="glass-card rounded-2xl overflow-hidden">
          <table class="table w-full">
            <thead class="bg-white/5 text-gray-300">
              <tr><th>Tier</th><th>Score Range</th><th>Current Examples</th></tr>
            </thead>
            <tbody class="text-sm text-gray-400">
              <tr class="border-b border-white/5"><td><span class="text-purple-400 font-bold">S</span></td><td>90-100</td><td>(none yet — GPT-4 class)</td></tr>
              <tr class="border-b border-white/5"><td><span class="text-blue-400 font-bold">A</span></td><td>80-89</td><td>gemma-4-31B-it (82.97), Qwen3.5-9B (81.52)</td></tr>
              <tr class="border-b border-white/5"><td><span class="text-green-400 font-bold">B</span></td><td>70-79</td><td>DeepSeek-R1 (78.3), phi-4 (72.89)</td></tr>
              <tr class="border-b border-white/5"><td><span class="text-yellow-400 font-bold">C</span></td><td>60-69</td><td>gpt-oss-20b (69.81)</td></tr>
              <tr><td><span class="text-red-400 font-bold">D</span></td><td>&lt;60</td><td>Legacy models</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 class="text-3xl font-bold mb-4 text-white">5. ELO Comparison Formula</h2>
        <div class="glass-card p-6 rounded-2xl mb-4">
          <p class="font-mono text-blue-400 text-center text-lg">P(A beats B) = 1 / (1 + 10^((ELO_B - ELO_A) / 400))</p>
        </div>
        <p class="text-gray-400">Example: Qwen3.5-9B (81.52) vs DeepSeek-R1 (78.3)<br>
        • ELO_A = 800 + 81.52*8 = 1452, ELO_B = 800 + 78.3*8 = 1426<br>
        • P(Qwen beats DeepSeek) = 1 / (1 + 10^((1426 - 1452) / 400)) = 0.537 = 53.7% win probability</p>
      </section>

      <section>
        <h2 class="text-3xl font-bold mb-4 text-white">6. Extended Metadata (10 signals)</h2>
        <p class="text-gray-400">context_window, vram_tier, license_score, finetune_friendly, multilingual, safety_score, update_velocity, inference_coverage, community_momentum, hub_completeness.</p>
      </section>

      <section>
        <h2 class="text-3xl font-bold mb-4 text-white">7. What We Don't Measure (Honest Limitations)</h2>
        <ul class="list-disc pl-5 text-gray-400 space-y-2">
          <li>Human preference (requires live inference infrastructure)</li>
          <li>API latency and cost per token</li>
          <li>Alignment and safety (beyond TruthfulQA)</li>
          <li>Benchmark contamination (we can't verify if models saw test data)</li>
          <li>Dialect/regional language performance</li>
        </ul>
      </section>

      <section>
        <h2 class="text-3xl font-bold mb-6 text-white">8. Changelog</h2>
        <div class="glass-card rounded-2xl overflow-hidden">
          <table class="table w-full">
            <thead class="bg-white/5 text-gray-300">
              <tr><th>Version</th><th>Date</th><th>Changes</th></tr>
            </thead>
            <tbody class="text-sm text-gray-400">
              <tr class="border-b border-white/5"><td>2.0.0</td><td>2026-08-13</td><td>10 extended metadata signals, Shields.io endpoint, pricing page</td></tr>
              <tr class="border-b border-white/5"><td>1.1.0</td><td>2026-08-13</td><td>GitHub Pages CDN, 71 models, HuggingFace Space</td></tr>
              <tr><td>1.0.0</td><td>2026-08-13</td><td>Initial: 5D scoring, ELO, SVG badges, 27 tests</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 class="text-3xl font-bold mb-4 text-white">9. Cite ModelRank</h2>
        <div class="mockup-code bg-base-300 text-sm">
          <pre><code>@software{modelrank2026,
  author = {ModelRank Team},
  title = {ModelRank: Composite Scoring and Embeddable Badges for Open-Weight AI Models},
  year = {2026},
  url = {https://github.com/rankmodel/rankmodel1},
  license = {MIT}
}</code></pre>
        </div>
      </section>
    </div>
  </div>
</body>
</html>"""

def generate_api_html() -> str:
    """Generate the API reference page."""
    return """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>ModelRank API Reference</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://cdn.jsdelivr.net/npm/daisyui@4/dist/full.min.css" rel="stylesheet" type="text/css" />
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            base: '#0a0a0f',
            surface: '#13131a',
            border: '#232330'
          },
          fontFamily: {
            sans: ['Inter', 'system-ui', 'sans-serif'],
            mono: ['JetBrains Mono', 'monospace']
          }
        }
      }
    }
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700;800&display=swap" rel="stylesheet"/>
  <style>
    body { background-color: #0a0a0f; color: #f1f5f9; font-family: 'Inter', sans-serif; }
    .sidebar { background: rgba(19, 19, 26, 0.7); backdrop-filter: blur(12px); border-right: 1px solid rgba(255, 255, 255, 0.05); }
    .glass-card { background: rgba(19, 19, 26, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }
    
    pre { margin: 0; }
    .method-get { color: #10b981; background: rgba(16, 185, 129, 0.1); border-color: rgba(16, 185, 129, 0.2); }
    .method-post { color: #3b82f6; background: rgba(59, 130, 246, 0.1); border-color: rgba(59, 130, 246, 0.2); }
    
    .code-dark { background: #000 !important; border: 1px solid #333; }
    .string { color: #a5d6ff; }
    .number { color: #79c0ff; }
    .boolean { color: #ff7b72; }
    .key { color: #7ee787; }
  </style>
  <script>
    function copyText(button, text) {
      navigator.clipboard.writeText(text);
      const orig = button.innerText;
      button.innerText = 'Copied!';
      setTimeout(() => button.innerText = orig, 2000);
    }
  </script>
</head>
<body class="min-h-screen text-gray-200" data-theme="dark">

  <div class="flex flex-col md:flex-row min-h-screen">
    
    <!-- Sidebar -->
    <aside class="w-full md:w-64 lg:w-72 sidebar md:h-screen md:sticky top-0 z-20 flex-shrink-0">
      <div class="p-6">
        <a href="index.html" class="text-2xl font-black flex items-center gap-2 mb-8 text-white hover:text-gray-300 transition-colors">
          🏆 ModelRank
        </a>
        
        <nav class="space-y-8">
          <div>
            <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Getting Started</h4>
            <ul class="space-y-2 text-sm">
              <li><a href="#overview" class="text-gray-300 hover:text-white block py-1">Overview & Auth</a></li>
              <li><a href="#rate-limits" class="text-gray-300 hover:text-white block py-1">Rate Limits</a></li>
            </ul>
          </div>
          
          <div>
            <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Leaderboard & Scoring</h4>
            <ul class="space-y-2 text-sm">
              <li><a href="#get-health" class="text-gray-300 hover:text-white block py-1 flex items-center justify-between"><span>Health</span> <span class="text-[10px] bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded">GET</span></a></li>
              <li><a href="#get-meta" class="text-gray-300 hover:text-white block py-1 flex items-center justify-between"><span>Metadata</span> <span class="text-[10px] bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded">GET</span></a></li>
              <li><a href="#get-score" class="text-gray-300 hover:text-white block py-1 flex items-center justify-between"><span>Score</span> <span class="text-[10px] bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded">GET</span></a></li>
              <li><a href="#get-score-ext" class="text-gray-300 hover:text-white block py-1 flex items-center justify-between"><span>Extended Score</span> <span class="text-[10px] bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded">GET</span></a></li>
              <li><a href="#post-score-batch" class="text-gray-300 hover:text-white block py-1 flex items-center justify-between"><span>Batch Score</span> <span class="text-[10px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded">POST</span></a></li>
            </ul>
          </div>

          <div>
            <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Badges & Embedding</h4>
            <ul class="space-y-2 text-sm">
              <li><a href="#get-badge" class="text-gray-300 hover:text-white block py-1 flex items-center justify-between"><span>SVG Badge</span> <span class="text-[10px] bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded">GET</span></a></li>
              <li><a href="#get-shields" class="text-gray-300 hover:text-white block py-1 flex items-center justify-between"><span>Shields.io JSON</span> <span class="text-[10px] bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded">GET</span></a></li>
              <li><a href="#get-embed" class="text-gray-300 hover:text-white block py-1 flex items-center justify-between"><span>HTML Embed</span> <span class="text-[10px] bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded">GET</span></a></li>
            </ul>
          </div>
          
          <div>
            <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Leaderboard Data</h4>
            <ul class="space-y-2 text-sm">
              <li><a href="#get-leaderboard" class="text-gray-300 hover:text-white block py-1 flex items-center justify-between"><span>Leaderboard</span> <span class="text-[10px] bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded">GET</span></a></li>
              <li><a href="#get-trending" class="text-gray-300 hover:text-white block py-1 flex items-center justify-between"><span>Trending</span> <span class="text-[10px] bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded">GET</span></a></li>
            </ul>
          </div>
          
          <div>
            <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Comparison</h4>
            <ul class="space-y-2 text-sm">
              <li><a href="#get-compare" class="text-gray-300 hover:text-white block py-1 flex items-center justify-between"><span>Head-to-head</span> <span class="text-[10px] bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded">GET</span></a></li>
              <li><a href="#get-achievements" class="text-gray-300 hover:text-white block py-1 flex items-center justify-between"><span>Achievements</span> <span class="text-[10px] bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded">GET</span></a></li>
            </ul>
          </div>
          
          <div>
            <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Premium</h4>
            <ul class="space-y-2 text-sm">
              <li><a href="#get-premium-plans" class="text-gray-300 hover:text-white block py-1 flex items-center justify-between"><span>Plans</span> <span class="text-[10px] bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded">GET</span></a></li>
              <li><a href="#get-premium-pitch" class="text-gray-300 hover:text-white block py-1 flex items-center justify-between"><span>Investor Pitch</span> <span class="text-[10px] bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded">GET</span></a></li>
            </ul>
          </div>
        </nav>
      </div>
    </aside>
    
    <!-- Main Content -->
    <main class="flex-1 overflow-y-auto">
      <div class="max-w-6xl mx-auto p-6 md:p-12 lg:p-16">
        
        <header class="mb-16">
          <h1 class="text-4xl md:text-5xl font-black mb-4 text-white">API Reference</h1>
          <p class="text-xl text-gray-400 max-w-2xl">Integrate objective AI scoring and rankings into your applications.</p>
        </header>
        
        <!-- Overview -->
        <section id="overview" class="mb-20 scroll-mt-24">
          <h2 class="text-2xl font-bold mb-6 text-white border-b border-white/10 pb-4">Overview</h2>
          
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div class="glass-card rounded-2xl p-6">
              <h3 class="text-lg font-bold mb-4 text-white">Base URL</h3>
              <p class="text-sm text-gray-400 mb-4">All API requests should be prefixed with this base URL.</p>
              <div class="bg-black/50 border border-white/10 rounded-xl p-4 flex justify-between items-center">
                <code class="font-mono text-blue-400 text-sm">https://your-deployment.com</code>
                <button onclick="copyText(this, 'https://your-deployment.com')" class="text-xs bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-lg transition-colors">Copy</button>
              </div>
            </div>
            
            <div class="glass-card rounded-2xl p-6">
              <h3 class="text-lg font-bold mb-4 text-white">Authentication</h3>
              <p class="text-sm text-gray-400 mb-4">Free tier doesn't require auth. Pro tier requires an API key passed in the headers.</p>
              <div class="bg-black/50 border border-white/10 rounded-xl p-4 flex justify-between items-center">
                <code class="font-mono text-purple-400 text-sm">X-API-Key: mr_xxxxxxxx</code>
                <button onclick="copyText(this, 'X-API-Key: mr_xxxxxxxx')" class="text-xs bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-lg transition-colors">Copy</button>
              </div>
            </div>
          </div>
        </section>
        
        <!-- Rate Limits -->
        <section id="rate-limits" class="mb-20 scroll-mt-24">
          <h2 class="text-2xl font-bold mb-6 text-white border-b border-white/10 pb-4">Rate Limits & Info</h2>
          
          <div class="glass-card rounded-2xl overflow-hidden mb-8">
            <table class="w-full text-left">
              <thead class="bg-white/5 border-b border-white/10 text-xs uppercase tracking-wider text-gray-400">
                <tr>
                  <th class="p-4">Plan</th>
                  <th class="p-4">Rate Limit</th>
                  <th class="p-4">Auth Required</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-white/5 text-sm">
                <tr class="hover:bg-white/5">
                  <td class="p-4 font-bold text-white">Free</td>
                  <td class="p-4 font-mono text-gray-400">100 req/hr</td>
                  <td class="p-4 text-gray-400">No</td>
                </tr>
                <tr class="hover:bg-white/5">
                  <td class="p-4 font-bold text-blue-400">Pro</td>
                  <td class="p-4 font-mono text-gray-400">5,000 req/hr</td>
                  <td class="p-4 text-gray-400">Yes</td>
                </tr>
                <tr class="hover:bg-white/5">
                  <td class="p-4 font-bold text-purple-400">Enterprise</td>
                  <td class="p-4 font-mono text-gray-400">Unlimited</td>
                  <td class="p-4 text-gray-400">Yes</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <div class="flex flex-col sm:flex-row gap-6">
            <div class="glass-card rounded-xl p-5 flex-1 border-blue-500/30 bg-blue-500/5">
              <h4 class="font-bold text-blue-400 mb-2 flex items-center gap-2">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg>
                SDKs
              </h4>
              <p class="text-sm text-gray-400">Coming soon: Python SDK, JavaScript SDK</p>
            </div>
            <div class="glass-card rounded-xl p-5 flex-1 border-purple-500/30 bg-purple-500/5">
              <h4 class="font-bold text-purple-400 mb-2 flex items-center gap-2">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/></svg>
                Versioning
              </h4>
              <p class="text-sm text-gray-400">Current API version is <code class="bg-black/50 px-1.5 py-0.5 rounded text-white font-mono">v2.0.0</code></p>
            </div>
          </div>
        </section>

        <!-- Divider -->
        <div class="w-full h-px bg-gradient-to-r from-transparent via-white/20 to-transparent my-16"></div>

        <!-- Endpoints Block Generator -->
        
        <!-- GET /health -->
        <section id="get-health" class="mb-24 scroll-mt-24">
          <div class="flex items-center gap-3 mb-4">
            <span class="method-get px-2.5 py-1 rounded border text-xs font-bold tracking-widest font-mono">GET</span>
            <h2 class="text-2xl font-bold font-mono text-white">/health</h2>
          </div>
          <p class="text-gray-400 mb-8">System health and leaderboard stats.</p>
          
          <div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
            <div>
              <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Parameters</h4>
              <div class="glass-card rounded-xl p-6 text-sm text-gray-400 text-center italic">
                No parameters required.
              </div>
            </div>
            
            <div class="space-y-4">
              <div>
                <div class="flex justify-between items-center mb-2">
                  <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider">Example Request</h4>
                  <button onclick="copyText(this, 'curl https://your-deployment.com/health')" class="text-xs text-gray-400 hover:text-white">Copy</button>
                </div>
                <pre class="code-dark rounded-xl p-4 text-sm font-mono overflow-x-auto"><span class="text-gray-400">$</span> curl https://your-deployment.com/health</pre>
              </div>
              
              <div>
                <div class="flex justify-between items-center mb-2">
                  <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider">Example Response</h4>
                  <button onclick="copyText(this, '{&quot;status&quot;:&quot;ok&quot;,&quot;uptime_seconds&quot;:86400}')" class="text-xs text-gray-400 hover:text-white">Copy</button>
                </div>
                <pre class="code-dark rounded-xl p-4 text-sm font-mono overflow-x-auto text-gray-300">{
  <span class="key">"status"</span>: <span class="string">"ok"</span>,
  <span class="key">"uptime_seconds"</span>: <span class="number">86400</span>
}</pre>
              </div>
            </div>
          </div>
        </section>

        <!-- GET /meta -->
        <section id="get-meta" class="mb-24 scroll-mt-24">
          <div class="flex items-center gap-3 mb-4">
            <span class="method-get px-2.5 py-1 rounded border text-xs font-bold tracking-widest font-mono">GET</span>
            <h2 class="text-2xl font-bold font-mono text-white">/meta</h2>
          </div>
          <p class="text-gray-400 mb-8">Version, links, and leaderboard metadata.</p>
          
          <div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
            <div>
              <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Parameters</h4>
              <div class="glass-card rounded-xl p-6 text-sm text-gray-400 text-center italic">
                No parameters required.
              </div>
            </div>
            
            <div class="space-y-4">
              <div>
                <div class="flex justify-between items-center mb-2">
                  <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider">Example Request</h4>
                  <button onclick="copyText(this, 'curl https://your-deployment.com/meta')" class="text-xs text-gray-400 hover:text-white">Copy</button>
                </div>
                <pre class="code-dark rounded-xl p-4 text-sm font-mono overflow-x-auto"><span class="text-gray-400">$</span> curl https://your-deployment.com/meta</pre>
              </div>
              
              <div>
                <div class="flex justify-between items-center mb-2">
                  <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider">Example Response</h4>
                  <button onclick="copyText(this, '{...}')" class="text-xs text-gray-400 hover:text-white">Copy</button>
                </div>
                <pre class="code-dark rounded-xl p-4 text-sm font-mono overflow-x-auto text-gray-300">{
  <span class="key">"version"</span>: <span class="string">"2.0.0"</span>,
  <span class="key">"total_models"</span>: <span class="number">71</span>,
  <span class="key">"last_updated"</span>: <span class="string">"2026-08-13T15:25:01Z"</span>
}</pre>
              </div>
            </div>
          </div>
        </section>

        <!-- GET /score/{model_id} -->
        <section id="get-score" class="mb-24 scroll-mt-24">
          <div class="flex items-center gap-3 mb-4">
            <span class="method-get px-2.5 py-1 rounded border text-xs font-bold tracking-widest font-mono">GET</span>
            <h2 class="text-2xl font-bold font-mono text-white">/score/{model_id}</h2>
          </div>
          <p class="text-gray-400 mb-8">Get the full composite score and basic tier details for a specific model.</p>
          
          <div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
            <div>
              <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Parameters</h4>
              <div class="glass-card rounded-xl overflow-hidden">
                <table class="w-full text-left text-sm">
                  <thead class="bg-white/5 border-b border-white/10 text-gray-400">
                    <tr><th class="p-3">Name</th><th class="p-3">Type</th><th class="p-3">Description</th></tr>
                  </thead>
                  <tbody class="divide-y divide-white/5 text-gray-300">
                    <tr>
                      <td class="p-3 font-mono text-blue-400">model_id</td>
                      <td class="p-3 text-gray-500">path</td>
                      <td class="p-3">HuggingFace model ID (e.g. <code>Qwen/Qwen3.5-9B</code>)</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            
            <div class="space-y-4">
              <div>
                <div class="flex justify-between items-center mb-2">
                  <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider">Example Request</h4>
                  <button onclick="copyText(this, 'curl https://your-deployment.com/score/Qwen/Qwen3.5-9B')" class="text-xs text-gray-400 hover:text-white">Copy</button>
                </div>
                <pre class="code-dark rounded-xl p-4 text-sm font-mono overflow-x-auto"><span class="text-gray-400">$</span> curl https://your-deployment.com/score/Qwen/Qwen3.5-9B</pre>
              </div>
              
              <div>
                <div class="flex justify-between items-center mb-2">
                  <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider">Example Response</h4>
                  <button onclick="copyText(this, 'JSON response')" class="text-xs text-gray-400 hover:text-white">Copy</button>
                </div>
                <pre class="code-dark rounded-xl p-4 text-sm font-mono overflow-x-auto text-gray-300">{
  <span class="key">"model_id"</span>: <span class="string">"Qwen/Qwen3.5-9B"</span>,
  <span class="key">"composite"</span>: <span class="number">81.52</span>,
  <span class="key">"tier"</span>: <span class="string">"A"</span>,
  <span class="key">"breakdown"</span>: {
    <span class="key">"benchmarks"</span>: <span class="number">82.0</span>,
    <span class="key">"efficiency"</span>: <span class="number">46.3</span>,
    <span class="key">"community"</span>: <span class="number">67.7</span>,
    <span class="key">"recency"</span>: <span class="number">74.2</span>,
    <span class="key">"reproducibility"</span>: <span class="number">55.0</span>
  },
  <span class="key">"computed_at"</span>: <span class="string">"2026-08-13T15:25:01Z"</span>,
  <span class="key">"confidence"</span>: <span class="string">"high"</span>,
  <span class="key">"coverage"</span>: {
    <span class="key">"found_benchmarks"</span>: <span class="number">8</span>,
    <span class="key">"total_benchmarks"</span>: <span class="number">13</span>,
    <span class="key">"coverage_percent"</span>: <span class="number">61.5</span>
  }
}</pre>
              </div>
            </div>
          </div>
        </section>

        <!-- GET /score/{model_id}/extended -->
        <section id="get-score-ext" class="mb-24 scroll-mt-24">
          <div class="flex items-center gap-3 mb-4">
            <span class="method-get px-2.5 py-1 rounded border text-xs font-bold tracking-widest font-mono">GET</span>
            <h2 class="text-2xl font-bold font-mono text-white">/score/{model_id}/extended</h2>
          </div>
          <p class="text-gray-400 mb-8">Score + 10 extended metadata signals (context window, vram tier, license score, etc).</p>
          
          <div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
            <div>
              <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Parameters</h4>
              <div class="glass-card rounded-xl overflow-hidden">
                <table class="w-full text-left text-sm">
                  <thead class="bg-white/5 border-b border-white/10 text-gray-400">
                    <tr><th class="p-3">Name</th><th class="p-3">Type</th><th class="p-3">Description</th></tr>
                  </thead>
                  <tbody class="divide-y divide-white/5 text-gray-300">
                    <tr>
                      <td class="p-3 font-mono text-blue-400">model_id</td>
                      <td class="p-3 text-gray-500">path</td>
                      <td class="p-3">HuggingFace model ID</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            
            <div class="space-y-4">
              <div>
                <div class="flex justify-between items-center mb-2">
                  <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider">Example Request</h4>
                  <button onclick="copyText(this, 'curl https://your-deployment.com/score/Qwen/Qwen3.5-9B/extended')" class="text-xs text-gray-400 hover:text-white">Copy</button>
                </div>
                <pre class="code-dark rounded-xl p-4 text-sm font-mono overflow-x-auto"><span class="text-gray-400">$</span> curl https://your-deployment.com/score/Qwen/Qwen3.5-9B/extended</pre>
              </div>
            </div>
          </div>
        </section>

        <!-- POST /score/batch -->
        <section id="post-score-batch" class="mb-24 scroll-mt-24">
          <div class="flex items-center gap-3 mb-4">
            <span class="method-post px-2.5 py-1 rounded border text-xs font-bold tracking-widest font-mono">POST</span>
            <h2 class="text-2xl font-bold font-mono text-white">/score/batch</h2>
          </div>
          <p class="text-gray-400 mb-8">Score multiple models at once (up to 20).</p>
          
          <div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
            <div>
              <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Parameters</h4>
              <div class="glass-card rounded-xl p-6 text-sm text-gray-300">
                <p class="mb-2">Accepts a JSON body with an array of model IDs.</p>
                <pre class="bg-black/50 p-3 rounded font-mono text-xs">{ "models": ["Qwen/Qwen3.5-9B", "google/gemma-4-31B-it"] }</pre>
              </div>
            </div>
            
            <div class="space-y-4">
              <div>
                <div class="flex justify-between items-center mb-2">
                  <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider">Example Request</h4>
                  <button onclick="copyText(this, 'curl -X POST ...')" class="text-xs text-gray-400 hover:text-white">Copy</button>
                </div>
                <pre class="code-dark rounded-xl p-4 text-sm font-mono overflow-x-auto"><span class="text-gray-400">$</span> curl -X POST https://your-deployment.com/score/batch \
  -H "Content-Type: application/json" \
  -d '{"models": ["Qwen/Qwen3.5-9B"]}'</pre>
              </div>
            </div>
          </div>
        </section>

        <!-- GET /badge/{model_id} -->
        <section id="get-badge" class="mb-24 scroll-mt-24">
          <div class="flex items-center gap-3 mb-4">
            <span class="method-get px-2.5 py-1 rounded border text-xs font-bold tracking-widest font-mono">GET</span>
            <h2 class="text-2xl font-bold font-mono text-white">/badge/{model_id}</h2>
          </div>
          <p class="text-gray-400 mb-8">Get an SVG badge for your model's README.</p>
          
          <div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
            <div>
              <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Parameters</h4>
              <div class="glass-card rounded-xl overflow-hidden">
                <table class="w-full text-left text-sm">
                  <thead class="bg-white/5 border-b border-white/10 text-gray-400">
                    <tr><th class="p-3">Name</th><th class="p-3">Type</th><th class="p-3">Description</th></tr>
                  </thead>
                  <tbody class="divide-y divide-white/5 text-gray-300">
                    <tr>
                      <td class="p-3 font-mono text-blue-400">model_id</td>
                      <td class="p-3 text-gray-500">path</td>
                      <td class="p-3">HuggingFace model ID</td>
                    </tr>
                    <tr>
                      <td class="p-3 font-mono text-purple-400">type</td>
                      <td class="p-3 text-gray-500">query</td>
                      <td class="p-3"><code>score</code> (default), <code>tier</code>, or <code>rank</code></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            
            <div class="space-y-4">
              <div>
                <div class="flex justify-between items-center mb-2">
                  <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider">Example Request</h4>
                  <button onclick="copyText(this, 'curl https://your-deployment.com/badge/Qwen/Qwen3.5-9B?type=score')" class="text-xs text-gray-400 hover:text-white">Copy</button>
                </div>
                <pre class="code-dark rounded-xl p-4 text-sm font-mono overflow-x-auto"><span class="text-gray-400">$</span> curl https://your-deployment.com/badge/Qwen/Qwen3.5-9B?type=score</pre>
              </div>
            </div>
          </div>
        </section>

        <!-- GET /shields/{model_id} -->
        <section id="get-shields" class="mb-24 scroll-mt-24">
          <div class="flex items-center gap-3 mb-4">
            <span class="method-get px-2.5 py-1 rounded border text-xs font-bold tracking-widest font-mono">GET</span>
            <h2 class="text-2xl font-bold font-mono text-white">/shields/{model_id}</h2>
          </div>
          <p class="text-gray-400 mb-8">Shields.io JSON endpoint for dynamic README badges.</p>
          
          <div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
            <div>
              <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Parameters</h4>
              <div class="glass-card rounded-xl overflow-hidden">
                <table class="w-full text-left text-sm">
                  <thead class="bg-white/5 border-b border-white/10 text-gray-400">
                    <tr><th class="p-3">Name</th><th class="p-3">Type</th><th class="p-3">Description</th></tr>
                  </thead>
                  <tbody class="divide-y divide-white/5 text-gray-300">
                    <tr>
                      <td class="p-3 font-mono text-blue-400">model_id</td>
                      <td class="p-3 text-gray-500">path</td>
                      <td class="p-3">HuggingFace model ID</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            
            <div class="space-y-4">
              <div>
                <div class="flex justify-between items-center mb-2">
                  <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider">Example Request</h4>
                  <button onclick="copyText(this, 'curl https://your-deployment.com/shields/Qwen/Qwen3.5-9B')" class="text-xs text-gray-400 hover:text-white">Copy</button>
                </div>
                <pre class="code-dark rounded-xl p-4 text-sm font-mono overflow-x-auto"><span class="text-gray-400">$</span> curl https://your-deployment.com/shields/Qwen/Qwen3.5-9B</pre>
              </div>
              
              <div>
                <div class="flex justify-between items-center mb-2">
                  <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider">Example Response</h4>
                  <button onclick="copyText(this, 'JSON response')" class="text-xs text-gray-400 hover:text-white">Copy</button>
                </div>
                <pre class="code-dark rounded-xl p-4 text-sm font-mono overflow-x-auto text-gray-300">{
  <span class="key">"schemaVersion"</span>: <span class="number">1</span>,
  <span class="key">"label"</span>: <span class="string">"ModelRank"</span>,
  <span class="key">"message"</span>: <span class="string">"82 (A)"</span>,
  <span class="key">"color"</span>: <span class="string">"blue"</span>,
  <span class="key">"namedLogo"</span>: <span class="string">"huggingface"</span>
}</pre>
              </div>
            </div>
          </div>
        </section>

        <!-- GET /embed/{model_id} -->
        <section id="get-embed" class="mb-24 scroll-mt-24">
          <div class="flex items-center gap-3 mb-4">
            <span class="method-get px-2.5 py-1 rounded border text-xs font-bold tracking-widest font-mono">GET</span>
            <h2 class="text-2xl font-bold font-mono text-white">/embed/{model_id}</h2>
          </div>
          <p class="text-gray-400 mb-8">HTML embed snippet.</p>
        </section>

        <!-- GET /leaderboard -->
        <section id="get-leaderboard" class="mb-24 scroll-mt-24">
          <div class="flex items-center gap-3 mb-4">
            <span class="method-get px-2.5 py-1 rounded border text-xs font-bold tracking-widest font-mono">GET</span>
            <h2 class="text-2xl font-bold font-mono text-white">/leaderboard</h2>
          </div>
          <p class="text-gray-400 mb-8">Get the paginated ranked leaderboard.</p>
          
          <div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
            <div>
              <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Parameters</h4>
              <div class="glass-card rounded-xl overflow-hidden">
                <table class="w-full text-left text-sm">
                  <thead class="bg-white/5 border-b border-white/10 text-gray-400">
                    <tr><th class="p-3">Name</th><th class="p-3">Type</th><th class="p-3">Description</th></tr>
                  </thead>
                  <tbody class="divide-y divide-white/5 text-gray-300">
                    <tr>
                      <td class="p-3 font-mono text-purple-400">limit</td>
                      <td class="p-3 text-gray-500">query</td>
                      <td class="p-3">Max results (default: 50, max: 100)</td>
                    </tr>
                    <tr>
                      <td class="p-3 font-mono text-purple-400">offset</td>
                      <td class="p-3 text-gray-500">query</td>
                      <td class="p-3">Pagination offset (default: 0)</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            
            <div class="space-y-4">
              <div>
                <div class="flex justify-between items-center mb-2">
                  <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider">Example Request</h4>
                  <button onclick="copyText(this, 'curl https://your-deployment.com/leaderboard?limit=3')" class="text-xs text-gray-400 hover:text-white">Copy</button>
                </div>
                <pre class="code-dark rounded-xl p-4 text-sm font-mono overflow-x-auto"><span class="text-gray-400">$</span> curl "https://your-deployment.com/leaderboard?limit=3"</pre>
              </div>
              
              <div>
                <div class="flex justify-between items-center mb-2">
                  <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider">Example Response</h4>
                  <button onclick="copyText(this, 'JSON response')" class="text-xs text-gray-400 hover:text-white">Copy</button>
                </div>
                <pre class="code-dark rounded-xl p-4 text-sm font-mono overflow-x-auto text-gray-300">{
  <span class="key">"models"</span>: [
    {<span class="key">"rank"</span>: <span class="number">1</span>, <span class="key">"model_id"</span>: <span class="string">"google/gemma-4-31B-it"</span>, <span class="key">"composite"</span>: <span class="number">82.97</span>, <span class="key">"tier"</span>: <span class="string">"A"</span>},
    {<span class="key">"rank"</span>: <span class="number">2</span>, <span class="key">"model_id"</span>: <span class="string">"Qwen/Qwen3.5-9B"</span>, <span class="key">"composite"</span>: <span class="number">81.52</span>, <span class="key">"tier"</span>: <span class="string">"A"</span>},
    {<span class="key">"rank"</span>: <span class="number">3</span>, <span class="key">"model_id"</span>: <span class="string">"deepseek-ai/DeepSeek-R1"</span>, <span class="key">"composite"</span>: <span class="number">78.3</span>, <span class="key">"tier"</span>: <span class="string">"B"</span>}
  ],
  <span class="key">"total"</span>: <span class="number">71</span>,
  <span class="key">"limit"</span>: <span class="number">3</span>,
  <span class="key">"offset"</span>: <span class="number">0</span>
}</pre>
              </div>
            </div>
          </div>
        </section>

        <!-- GET /trending -->
        <section id="get-trending" class="mb-24 scroll-mt-24">
          <div class="flex items-center gap-3 mb-4">
            <span class="method-get px-2.5 py-1 rounded border text-xs font-bold tracking-widest font-mono">GET</span>
            <h2 class="text-2xl font-bold font-mono text-white">/trending</h2>
          </div>
          <p class="text-gray-400 mb-8">Trending models by momentum.</p>
        </section>

        <!-- GET /compare -->
        <section id="get-compare" class="mb-24 scroll-mt-24">
          <div class="flex items-center gap-3 mb-4">
            <span class="method-get px-2.5 py-1 rounded border text-xs font-bold tracking-widest font-mono">GET</span>
            <h2 class="text-2xl font-bold font-mono text-white">/compare</h2>
          </div>
          <p class="text-gray-400 mb-8">ELO head-to-head win probability.</p>
          
          <div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
            <div>
              <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Parameters</h4>
              <div class="glass-card rounded-xl overflow-hidden">
                <table class="w-full text-left text-sm">
                  <thead class="bg-white/5 border-b border-white/10 text-gray-400">
                    <tr><th class="p-3">Name</th><th class="p-3">Type</th><th class="p-3">Description</th></tr>
                  </thead>
                  <tbody class="divide-y divide-white/5 text-gray-300">
                    <tr>
                      <td class="p-3 font-mono text-purple-400">model_a</td>
                      <td class="p-3 text-gray-500">query</td>
                      <td class="p-3">First HuggingFace model ID</td>
                    </tr>
                    <tr>
                      <td class="p-3 font-mono text-purple-400">model_b</td>
                      <td class="p-3 text-gray-500">query</td>
                      <td class="p-3">Second HuggingFace model ID</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            
            <div class="space-y-4">
              <div>
                <div class="flex justify-between items-center mb-2">
                  <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider">Example Request</h4>
                  <button onclick="copyText(this, 'curl \"https://your-deployment.com/compare?model_a=Qwen/Qwen3.5-9B&model_b=deepseek-ai/DeepSeek-R1\"')" class="text-xs text-gray-400 hover:text-white">Copy</button>
                </div>
                <pre class="code-dark rounded-xl p-4 text-sm font-mono overflow-x-auto"><span class="text-gray-400">$</span> curl "https://your-deployment.com/compare?model_a=Qwen/Qwen3.5-9B&model_b=deepseek-ai/DeepSeek-R1"</pre>
              </div>
              
              <div>
                <div class="flex justify-between items-center mb-2">
                  <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider">Example Response</h4>
                  <button onclick="copyText(this, 'JSON response')" class="text-xs text-gray-400 hover:text-white">Copy</button>
                </div>
                <pre class="code-dark rounded-xl p-4 text-sm font-mono overflow-x-auto text-gray-300">{
  <span class="key">"win_probability_a"</span>: <span class="number">0.5672</span>,
  <span class="key">"win_probability_b"</span>: <span class="number">0.4328</span>,
  <span class="key">"elo_a"</span>: <span class="number">1452</span>,
  <span class="key">"elo_b"</span>: <span class="number">1426</span>,
  <span class="key">"overall_winner"</span>: <span class="string">"A"</span>,
  <span class="key">"dimension_winners"</span>: {
    <span class="key">"benchmarks"</span>: <span class="string">"A"</span>,
    <span class="key">"efficiency"</span>: <span class="string">"A"</span>,
    <span class="key">"community"</span>: <span class="string">"B"</span>,
    <span class="key">"recency"</span>: <span class="string">"A"</span>,
    <span class="key">"reproducibility"</span>: <span class="string">"tie"</span>
  }
}</pre>
              </div>
            </div>
          </div>
        </section>

        <!-- GET /achievements/{model_id} -->
        <section id="get-achievements" class="mb-24 scroll-mt-24">
          <div class="flex items-center gap-3 mb-4">
            <span class="method-get px-2.5 py-1 rounded border text-xs font-bold tracking-widest font-mono">GET</span>
            <h2 class="text-2xl font-bold font-mono text-white">/achievements/{model_id}</h2>
          </div>
          <p class="text-gray-400 mb-8">Fetch unlockable achievement badges for a model.</p>
        </section>

        <!-- Premium Endpoints -->
        <section id="get-premium-plans" class="mb-24 scroll-mt-24">
          <div class="flex items-center gap-3 mb-4">
            <span class="method-get px-2.5 py-1 rounded border text-xs font-bold tracking-widest font-mono">GET</span>
            <h2 class="text-2xl font-bold font-mono text-white">/premium/plans</h2>
          </div>
          <p class="text-gray-400 mb-8">Pricing tiers for API access.</p>
        </section>

        <section id="get-premium-pitch" class="mb-24 scroll-mt-24">
          <div class="flex items-center gap-3 mb-4">
            <span class="method-get px-2.5 py-1 rounded border text-xs font-bold tracking-widest font-mono">GET</span>
            <h2 class="text-2xl font-bold font-mono text-white">/premium/pitch</h2>
          </div>
          <p class="text-gray-400 mb-8">Investor pitch data (Pro only).</p>
        </section>
        
        <!-- Footer -->
        <footer class="border-t border-white/10 pt-12 pb-24 mt-24">
          <div class="flex flex-col md:flex-row justify-between items-center gap-6">
            <div class="flex gap-6 text-sm font-medium">
              <a href="https://github.com/rankmodel/rankmodel1" class="text-gray-400 hover:text-white transition-colors">GitHub</a>
              <a href="index.html#methodology" class="text-gray-400 hover:text-white transition-colors">Methodology</a>
              <a href="pricing.html" class="text-gray-400 hover:text-white transition-colors">Pricing</a>
              <a href="index.html" class="text-gray-400 hover:text-white transition-colors">Leaderboard</a>
            </div>
            <div class="text-right">
              <p class="text-green-400 text-sm flex items-center gap-2 justify-end">
                <span class="w-2 h-2 rounded-full bg-green-500 inline-block animate-pulse"></span>
                API status: All systems operational
              </p>
              <p class="text-gray-500 text-xs mt-2">Questions? Open an issue on <a href="https://github.com/rankmodel/rankmodel1/issues" class="text-blue-400 hover:underline">GitHub</a></p>
            </div>
          </div>
        </footer>
        
      </div>
    </main>
  </div>
</body>
</html>"""

def generate_trending_data(models: list) -> dict:
    """
    Compute trending models. Since we don't have historical data yet,
    use a proxy: high community score + high recency score = trending.
    Models with community > 70 and recency > 60 are "trending".
    Returns top 5 trending with a reason string.
    """
    trending = []
    for rank, item in enumerate(models, 1):
        s = item.get('score', {})
        b = s.get('breakdown', {})
        comm = b.get('community', 0)
        rec = b.get('recency', b.get('freshness', 0))
        trend_score = comm * 0.6 + rec * 0.4
        if trend_score > 55:
            reason = []
            if comm > 75: reason.append(f"{comm:.0f}/100 community")
            if rec > 65: reason.append(f"{rec:.0f}/100 freshness")
            trending.append({
                'model_id': item['model_id'],
                'composite': s.get('composite', 0),
                'tier': s.get('tier', 'D'),
                'trend_score': round(trend_score, 1),
                'reason': ' · '.join(reason) or 'Rising fast',
                'rank': rank
            })
    trending.sort(key=lambda x: x['trend_score'], reverse=True)
    return {'trending': trending[:8], 'generated_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z'}


def generate_changelog_json() -> str:
    """Generate the machine-readable changelog JSON."""
    return """{
  "version": "2.0.0",
  "released": "2026-08-13",
  "entries": [
    {"version": "2.0.0", "date": "2026-08-13", "type": "major", "changes": ["10 extended metadata scoring parameters", "Shields.io endpoint", "Premium pricing page", "NotebookLM integration", "Outreach engine"]},
    {"version": "1.1.0", "date": "2026-08-13", "type": "minor", "changes": ["GitHub Pages CDN for badges", "66 models seeded", "HuggingFace Space"]},
    {"version": "1.0.0", "date": "2026-08-13", "type": "major", "changes": ["Initial release", "5-dimension composite scoring", "ELO comparison", "SVG badges", "Gradio UI", "FastAPI", "27 tests"]}
  ]
}"""


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
                      'shields_url': f'{base_url}/badges/{mid}/shields.json',
                      'dna_url': f'{base_url}/dna/{mid}.svg'}
        (OUTPUT_DIR / 'models' / f'{org}__{model_name}.json').write_text(
            json.dumps(model_json, indent=2), encoding='utf-8')

        # Write shareable "Model DNA" card
        dna_path = OUTPUT_DIR / 'dna' / f'{mid}.svg'
        dna_path.parent.mkdir(parents=True, exist_ok=True)
        dna_path.write_text(
            generate_model_dna_svg(mid, composite, tier, rank, s.get('breakdown', {})),
            encoding='utf-8')

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

    # Write search_index.json (lightweight for frontend 100k array load)
    search_index = [{'id': m['model_id'], 'c': m['composite'], 't': m['tier']} for m in leaderboard_data]
    (OUTPUT_DIR / 'search_index.json').write_text(json.dumps(search_index), encoding='utf-8')
    logger.info('   search_index.json generated')

    # Write index.html leaderboard page
    (OUTPUT_DIR / 'index.html').write_text(
        generate_leaderboard_html(models, base_url), encoding='utf-8')
    logger.info('   index.html leaderboard page')

    # Write Model DNA share page
    (OUTPUT_DIR / 'dna.html').write_text(
        generate_dna_html(base_url), encoding='utf-8')
    logger.info('   dna.html — shareable Model DNA cards')
    
    (OUTPUT_DIR / 'sitemap.xml').write_text(generate_sitemap(models, base_url), encoding='utf-8')
    logger.info('   sitemap.xml generated')
    
    (OUTPUT_DIR / 'robots.txt').write_text(generate_robots_txt(base_url), encoding='utf-8')
    logger.info('   robots.txt generated')
    
    logger.info('\n✅ Static assets generated in static_output/')

    # Write pricing.html landing page
    (OUTPUT_DIR / 'pricing.html').write_text(
        generate_pricing_html(), encoding='utf-8')
    logger.info('   pricing.html landing page')

    # Write a _headers file for GitHub Pages (proper SVG MIME type + CORS for badges)
    (OUTPUT_DIR / '_headers').write_text(
        '/badges/*\n  Content-Type: image/svg+xml\n  Cache-Control: public, max-age=3600\n  Access-Control-Allow-Origin: *\n\n'
        '/leaderboard.json\n  Content-Type: application/json\n  Cache-Control: public, max-age=3600\n  Access-Control-Allow-Origin: *\n\n'
        '/models/*\n  Content-Type: application/json\n  Access-Control-Allow-Origin: *\n'
    )

    # Write .nojekyll so GitHub Pages serves files as-is
    (OUTPUT_DIR / '.nojekyll').write_text('')

    # Trust Building Pages
    (OUTPUT_DIR / 'methodology.html').write_text(generate_methodology_html(), encoding='utf-8')
    logger.info('   methodology.html — FULL VERSION')
    (OUTPUT_DIR / 'quiz.html').write_text(generate_quiz_html(), encoding='utf-8')
    logger.info('   quiz.html — model recommendation quiz')
    (OUTPUT_DIR / 'collections.html').write_text(generate_collections_html(), encoding='utf-8')
    logger.info('   collections.html — curated collections')
    (OUTPUT_DIR / 'api.html').write_text(generate_api_html(), encoding='utf-8')
    logger.info('   api.html reference page')
    (OUTPUT_DIR / 'changelog.json').write_text(generate_changelog_json(), encoding='utf-8')
    logger.info('   changelog.json')
    
    (OUTPUT_DIR / 'trending.json').write_text(
        json.dumps(generate_trending_data(models), indent=2), encoding='utf-8')
    logger.info('   trending.json')

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
