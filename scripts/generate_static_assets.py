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
    """Generate a standalone leaderboard HTML page for GitHub Pages using Tailwind & daisyUI."""
    rows = ''
    for i, item in enumerate(models, 1):
        mid = item.get('model_id', '')
        s = item.get('score', {})
        bd = s.get('breakdown', {})
        tier = s.get('tier', 'C')
        composite = s.get('composite', 0)
        
        tier_badges = {
            'S': 'badge-secondary',
            'A': 'badge-primary',
            'B': 'badge-success',
            'C': 'badge-warning',
            'D': 'badge-error'
        }
        tier_badge = tier_badges.get(tier, 'badge-ghost')
        
        hf_url = f'https://huggingface.co/{mid}'
        badge_url = f'{base_url}/badges/{mid}/score.svg'
        
        rows += f'''
        <tr class="hover:bg-base-200 transition-colors">
          <td class="text-base-content/50 font-mono text-sm">{i}</td>
          <td>
            <a href="{hf_url}" target="_blank" class="link link-hover text-primary font-semibold">{mid}</a>
          </td>
          <td class="text-center">
            <span class="font-black text-lg">{composite:.1f}</span>
          </td>
          <td class="text-center">
            <div class="badge {tier_badge} badge-sm font-bold uppercase">{tier}</div>
          </td>
          <td class="text-center text-base-content/60 text-sm hidden md:table-cell">{bd.get("benchmarks",0):.0f}</td>
          <td class="text-center text-base-content/60 text-sm hidden md:table-cell">{bd.get("efficiency",0):.0f}</td>
          <td class="text-center text-base-content/60 text-sm hidden lg:table-cell">{bd.get("community",0):.0f}</td>
          <td>
            <img src="{badge_url}" class="h-6" alt="Score Badge" onerror="this.style.display='none'"/>
          </td>
        </tr>'''

    updated = __import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    return f'''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>ModelRank — HuggingFace Model Leaderboard</title>
  <meta name="description" content="Composite scoring and tier rankings for HuggingFace models. Independent benchmarks, efficiency, community, and freshness scores."/>
  
  <link href="https://cdn.jsdelivr.net/npm/daisyui@4.10.1/dist/full.min.css" rel="stylesheet" type="text/css" />
  <script src="https://cdn.tailwindcss.com"></script>
  
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap" rel="stylesheet"/>
  <style>
    body {{ font-family: 'Inter', system-ui, sans-serif; }}
  </style>
</head>
<body class="min-h-screen bg-base-300 text-base-content">
  
  <div class="container mx-auto px-4 py-12 max-w-6xl">
    
    <div class="text-center mb-12">
      <h1 class="text-4xl md:text-5xl font-black tracking-tight text-white mb-4">🏆 ModelRank</h1>
      <p class="text-base-content/70 text-lg">Independent composite scoring for HuggingFace models</p>
      
      <div class="mt-6">
        <a href="https://github.com/rankmodel/rankmodel1" target="_blank" class="btn btn-outline btn-sm rounded-full">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
          Star on GitHub
        </a>
      </div>
    </div>
    
    <div class="stats stats-vertical lg:stats-horizontal shadow bg-base-100 w-full mb-8 border border-base-200">
      <div class="stat place-items-center">
        <div class="stat-title text-xs font-bold uppercase tracking-wider">Models Ranked</div>
        <div class="stat-value text-primary">{len(models)}</div>
      </div>
      <div class="stat place-items-center">
        <div class="stat-title text-xs font-bold uppercase tracking-wider">Dimensions</div>
        <div class="stat-value text-secondary">5</div>
      </div>
      <div class="stat place-items-center">
        <div class="stat-title text-xs font-bold uppercase tracking-wider">Benchmarks</div>
        <div class="stat-value text-accent">13</div>
      </div>
      <div class="stat place-items-center">
        <div class="stat-title text-xs font-bold uppercase tracking-wider">Always</div>
        <div class="stat-value text-success">Free</div>
      </div>
    </div>
    
    <div class="alert alert-info shadow-sm mb-12 flex-col sm:flex-row bg-base-100 border border-base-200 text-base-content">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-info shrink-0 w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
      <div>
        <h3 class="font-bold">Embed a badge in your README</h3>
        <code class="text-xs mt-2 block bg-base-300 p-2 rounded">![ModelRank]({base_url}/badges/ORG/MODEL/score.svg)</code>
      </div>
    </div>
    
    <div class="bg-base-100 rounded-xl shadow border border-base-200 overflow-x-auto">
      <table class="table table-zebra table-pin-rows">
        <thead class="bg-base-200 text-base-content/70">
          <tr>
            <th>#</th>
            <th>Model</th>
            <th class="text-center">Score</th>
            <th class="text-center">Tier</th>
            <th class="text-center hidden md:table-cell">Bench</th>
            <th class="text-center hidden md:table-cell">Effic</th>
            <th class="text-center hidden lg:table-cell">Comm</th>
            <th>Badge</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>
    </div>
    
    <div class="text-center mt-12 text-xs text-base-content/50">
      <p>Last updated: {updated} · Auto-updated daily by GitHub Actions</p>
    </div>
    
  </div>
</body>
</html>'''


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
