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


def generate_leaderboard_html(models: list, base_url: str) -> str:
    """Generate a standalone leaderboard HTML page for GitHub Pages using Tailwind & daisyUI."""
    rows = ''
    for i, item in enumerate(models, 1):
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
        
        rows += f'''
        <tr class="hover:bg-white/5 transition-colors border-b border-white/5 group model-row" data-name="{mid.lower()}" data-tier="{tier}">
          <td class="px-4 py-4 text-center font-mono text-gray-400">{medal}</td>
          <td class="px-4 py-4">
            <a href="{hf_url}" target="_blank" class="block hover:opacity-80 transition-opacity">
              <div class="text-xs text-gray-500 font-medium mb-1">{org}</div>
              <div class="text-base font-bold text-gray-100">{model_name}</div>
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
</head>
<body class="min-h-screen text-gray-200">
  
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
          <a href="#methodology" class="hover:text-white transition-colors">Methodology</a>
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
    
    <!-- Filter Bar (Sticky) -->
    <div class="glass-card rounded-2xl p-4 mb-8 shadow-2xl sticky top-4 z-30 flex flex-col md:flex-row gap-4 items-center justify-between animate-fade-in">
      <div class="relative w-full md:w-72">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
        <input type="text" id="searchInput" placeholder="Search models..." class="w-full bg-surface border border-white/10 rounded-xl pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors">
      </div>
      
      <div class="flex items-center gap-2 overflow-x-auto w-full md:w-auto pb-2 md:pb-0 hide-scrollbar" id="tierFilters">
        <button class="tier-btn active px-4 py-1.5 rounded-lg text-sm font-bold bg-white/10 text-white transition-colors" data-tier="all">ALL</button>
        <button class="tier-btn px-4 py-1.5 rounded-lg text-sm font-bold text-gray-400 hover:bg-white/5 transition-colors" data-tier="S">S</button>
        <button class="tier-btn px-4 py-1.5 rounded-lg text-sm font-bold text-gray-400 hover:bg-white/5 transition-colors" data-tier="A">A</button>
        <button class="tier-btn px-4 py-1.5 rounded-lg text-sm font-bold text-gray-400 hover:bg-white/5 transition-colors" data-tier="B">B</button>
        <button class="tier-btn px-4 py-1.5 rounded-lg text-sm font-bold text-gray-400 hover:bg-white/5 transition-colors" data-tier="C">C</button>
        <button class="tier-btn px-4 py-1.5 rounded-lg text-sm font-bold text-gray-400 hover:bg-white/5 transition-colors" data-tier="D">D</button>
      </div>
      
      <div class="flex items-center gap-3 w-full md:w-auto justify-end">
        <button id="compareBtn" class="px-4 py-2 rounded-xl text-sm font-bold bg-blue-600 hover:bg-blue-700 text-white transition-colors opacity-50 cursor-not-allowed" disabled>
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
      
      // Filter function
      function filterTable() {{
        const query = searchInput.value.toLowerCase();
        rows.forEach(row => {{
          const name = row.getAttribute('data-name');
          const tier = row.getAttribute('data-tier');
          
          const matchesSearch = name.includes(query);
          const matchesTier = currentTier === 'all' || tier === currentTier;
          
          if (matchesSearch && matchesTier) {{
            row.classList.remove('hidden-row');
          }} else {{
            row.classList.add('hidden-row');
          }}
        }});
      }}
      
      // Search event
      if(searchInput) {{ searchInput.addEventListener('input', filterTable); }}
      
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
    }});
  </script>
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

def generate_methodology_html() -> str:
    """Generate the methodology page."""
    return """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>ModelRank Scoring Methodology — How We Evaluate Open-Weight AI Models</title>
  <link href="https://cdn.jsdelivr.net/npm/daisyui@4.10.1/dist/full.min.css" rel="stylesheet" type="text/css" />
  <script src="https://cdn.tailwindcss.com"></script>
  <style>body { font-family: 'Inter', system-ui, sans-serif; }</style>
</head>
<body class="min-h-screen bg-base-300 text-base-content">
  <div class="container mx-auto px-4 py-12 max-w-4xl">
    <div class="mb-8"><a href="index.html" class="btn btn-outline btn-sm">← Back to Leaderboard</a></div>
    <h1 class="text-4xl md:text-5xl font-black mb-6 tracking-tight">ModelRank Scoring Methodology — How We Evaluate Open-Weight AI Models</h1>
    <p class="text-xl text-base-content/70 mb-12">Built for developers, not marketing teams. Every score is reproducible, open-source, and conflict-of-interest-free.</p>
    
    <div class="space-y-12">
      <section>
        <h2 class="text-2xl font-bold mb-4 border-b border-base-200 pb-2">Section 1 — The 5 Dimensions</h2>
        <p class="text-base-content/80">Our composite score combines 5 key areas: Benchmarks (accuracy), Efficiency (speed/VRAM), Community (momentum/stars), Architecture (context length, types), and Freshness (recency).</p>
      </section>

      <section>
        <h2 class="text-2xl font-bold mb-4 border-b border-base-200 pb-2">Section 2 — Benchmark Coverage</h2>
        <div class="overflow-x-auto">
          <table class="table table-zebra table-sm">
            <thead><tr><th>Benchmark</th><th>Focus</th></tr></thead>
            <tbody>
              <tr><td>MMLU-Pro</td><td>General Knowledge</td></tr>
              <tr><td>GPQA Diamond</td><td>Expert Reasoning</td></tr>
              <tr><td>HLE, GSM8K</td><td>Math & Logic</td></tr>
              <tr><td>HumanEval, MBPP</td><td>Coding</td></tr>
              <tr><td>ARC-C, HellaSwag</td><td>Common Sense</td></tr>
              <tr><td>WinoGrande, TruthfulQA, BBQ, BoolQ, PIQA</td><td>Factuality & Bias</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 class="text-2xl font-bold mb-4 border-b border-base-200 pb-2">Section 3 — Normalization</h2>
        <p class="text-base-content/80">Raw benchmark scores (0-1) are converted to a 0-100 scale using confidence weighting and coverage bonuses for multi-domain models.</p>
      </section>

      <section>
        <h2 class="text-2xl font-bold mb-4 border-b border-base-200 pb-2">Section 4 — Tier System</h2>
        <ul class="list-disc pl-5 text-base-content/80">
          <li><span class="text-secondary font-bold">S Tier (90-100)</span>: State-of-the-art models (e.g., Llama 3 70B, Qwen 2 72B)</li>
          <li><span class="text-primary font-bold">A Tier (80-89)</span>: Excellent general-purpose models</li>
          <li><span class="text-success font-bold">B Tier (70-79)</span>: Solid performance, often smaller efficient models</li>
          <li><span class="text-warning font-bold">C Tier (60-69)</span>: Usable for specific basic tasks</li>
          <li><span class="text-error font-bold">D Tier (0-59)</span>: Legacy or specialized niche models</li>
        </ul>
      </section>

      <section>
        <h2 class="text-2xl font-bold mb-4 border-b border-base-200 pb-2">Section 5 — ELO Comparison</h2>
        <p class="text-base-content/80">We use the Bradley-Terry model for head-to-head win rates. <code>P(A beats B) = 1/(1+10^((ELO_B-ELO_A)/400))</code>.</p>
      </section>

      <section>
        <h2 class="text-2xl font-bold mb-4 border-b border-base-200 pb-2">Section 6 — What We DON'T measure</h2>
        <p class="text-base-content/80">Currently excluding: human preference (LMSYS), API latency, API cost, and alignment safety scoring (see future roadmap).</p>
      </section>

      <section>
        <h2 class="text-2xl font-bold mb-4 border-b border-base-200 pb-2">Section 7 — Data Sources</h2>
        <p class="text-base-content/80">Metrics sourced daily from HuggingFace Hub API, Open LLM Leaderboard V2 eval results, and live community momentum tracking.</p>
      </section>

      <section>
        <h2 class="text-2xl font-bold mb-4 border-b border-base-200 pb-2">Section 8 — Limitations & Known Issues</h2>
        <p class="text-base-content/80">Be aware of potential benchmark contamination risk, HF download gaming via automated bots, and assumptions in our freshness decay formula.</p>
      </section>

      <section>
        <h2 class="text-2xl font-bold mb-4 border-b border-base-200 pb-2">Section 9 — Changelog</h2>
        <p class="text-base-content/80">v1.0 (Initial release), v2.0 (10-parameter extended metadata release).</p>
      </section>
    </div>
  </div>
</body>
</html>"""

def generate_api_html() -> str:
    """Generate the API reference page."""
    return """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>ModelRank API Reference</title>
  <link href="https://cdn.jsdelivr.net/npm/daisyui@4.10.1/dist/full.min.css" rel="stylesheet" type="text/css" />
  <script src="https://cdn.tailwindcss.com"></script>
  <style>body { font-family: 'Inter', system-ui, sans-serif; }</style>
</head>
<body class="min-h-screen bg-base-300 text-base-content">
  <div class="container mx-auto px-4 py-12 max-w-5xl">
    <div class="mb-8"><a href="index.html" class="btn btn-outline btn-sm">← Back to Leaderboard</a></div>
    
    <div class="mb-12">
      <h1 class="text-4xl md:text-5xl font-black mb-4">ModelRank API Reference</h1>
      <p class="text-xl text-base-content/70">Integrate objective AI scoring into your apps.</p>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
      <div class="col-span-2 card bg-base-100 shadow border border-base-200 p-6">
        <h2 class="text-xl font-bold mb-4">Authentication & Base URL</h2>
        <p class="mb-2 text-sm text-base-content/70">Base URL:</p>
        <code class="block bg-base-300 p-3 rounded-lg mb-4 text-primary font-mono text-sm">https://your-api.com</code>
        <p class="mb-2 text-sm text-base-content/70">Auth Header (Pro only):</p>
        <code class="block bg-base-300 p-3 rounded-lg font-mono text-sm">X-API-Key: mr_xxxxxx</code>
      </div>
      <div class="card bg-base-100 shadow border border-base-200 p-6">
        <h2 class="text-xl font-bold mb-4">Rate Limits</h2>
        <ul class="space-y-3">
          <li class="flex justify-between items-center text-sm border-b border-base-200 pb-2">
            <span class="font-bold text-success">Free</span>
            <span class="font-mono">100 req/hr</span>
          </li>
          <li class="flex justify-between items-center text-sm">
            <span class="font-bold text-primary">Pro API Key</span>
            <span class="font-mono">5,000 req/hr</span>
          </li>
        </ul>
      </div>
    </div>

    <div class="space-y-12">
      
      <!-- Endpoint 1 -->
      <div class="card bg-base-100 shadow border border-base-200 p-6">
        <div class="flex items-center gap-3 mb-4">
          <span class="badge badge-success font-mono font-bold">GET</span>
          <h3 class="text-xl font-bold font-mono">/score/{model_id}</h3>
        </div>
        <p class="text-base-content/80 mb-6">Returns the full composite score and basic tier info for a model.</p>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h4 class="text-xs uppercase font-bold text-base-content/50 mb-2">Example Request</h4>
            <div class="mockup-code text-sm">
              <pre data-prefix="$"><code>curl https://your-api.com/score/mistralai/Mistral-7B-v0.1</code></pre>
            </div>
            <button class="btn btn-xs mt-2" onclick="navigator.clipboard.writeText('curl https://your-api.com/score/mistralai/Mistral-7B-v0.1')">Copy</button>
          </div>
          <div>
            <h4 class="text-xs uppercase font-bold text-base-content/50 mb-2">Example Response</h4>
            <div class="mockup-code text-sm bg-base-300">
              <pre><code>{
  "model_id": "mistralai/Mistral-7B-v0.1",
  "composite": 85.4,
  "tier": "A",
  "rank": 14
}</code></pre>
            </div>
          </div>
        </div>
      </div>

      <!-- Endpoint 2 -->
      <div class="card bg-base-100 shadow border border-base-200 p-6">
        <div class="flex items-center gap-3 mb-4">
          <span class="badge badge-success font-mono font-bold">GET</span>
          <h3 class="text-xl font-bold font-mono">/score/{model_id}/extended</h3>
        </div>
        <p class="text-base-content/80 mb-6">Score + 10 extended metadata signals (context window, vram tier, license score, etc).</p>
      </div>

      <!-- Endpoint 3 -->
      <div class="card bg-base-100 shadow border border-base-200 p-6">
        <div class="flex items-center gap-3 mb-4">
          <span class="badge badge-success font-mono font-bold">GET</span>
          <h3 class="text-xl font-bold font-mono">/shields/{model_id}</h3>
        </div>
        <p class="text-base-content/80 mb-6">Shields.io JSON endpoint for dynamic README badges.</p>
      </div>

      <!-- Endpoint 4 -->
      <div class="card bg-base-100 shadow border border-base-200 p-6">
        <div class="flex items-center gap-3 mb-4">
          <span class="badge badge-success font-mono font-bold">GET</span>
          <h3 class="text-xl font-bold font-mono">/badge/{model_id}</h3>
        </div>
        <p class="text-base-content/80 mb-6">Returns an SVG badge. Supports query params: <code>?type=score|tier|rank</code></p>
      </div>

      <!-- Endpoint 5 -->
      <div class="card bg-base-100 shadow border border-base-200 p-6">
        <div class="flex items-center gap-3 mb-4">
          <span class="badge badge-success font-mono font-bold">GET</span>
          <h3 class="text-xl font-bold font-mono">/leaderboard</h3>
        </div>
        <p class="text-base-content/80 mb-6">Paginated leaderboard list. Supports: <code>?limit=50&amp;offset=0&amp;tier=A&amp;task=text-generation</code></p>
      </div>

      <!-- Endpoint 6 -->
      <div class="card bg-base-100 shadow border border-base-200 p-6">
        <div class="flex items-center gap-3 mb-4">
          <span class="badge badge-success font-mono font-bold">GET</span>
          <h3 class="text-xl font-bold font-mono">/compare</h3>
        </div>
        <p class="text-base-content/80 mb-6">ELO comparison head-to-head. Supports: <code>?model_a=X&amp;model_b=Y</code></p>
      </div>

      <!-- Endpoint 7 -->
      <div class="card bg-base-100 shadow border border-base-200 p-6">
        <div class="flex items-center gap-3 mb-4">
          <span class="badge badge-success font-mono font-bold">GET</span>
          <h3 class="text-xl font-bold font-mono">/achievements/{model_id}</h3>
        </div>
        <p class="text-base-content/80 mb-6">Fetch unlockable achievement badges for a specific model.</p>
      </div>

      <!-- Endpoint 8 -->
      <div class="card bg-base-100 shadow border border-base-200 p-6">
        <div class="flex items-center gap-3 mb-4">
          <span class="badge badge-warning font-mono font-bold text-black">POST</span>
          <h3 class="text-xl font-bold font-mono">/score/batch</h3>
        </div>
        <p class="text-base-content/80 mb-6">Score up to 20 models simultaneously.</p>
      </div>

      <!-- Endpoint 9 -->
      <div class="card bg-base-100 shadow border border-base-200 p-6">
        <div class="flex items-center gap-3 mb-4">
          <span class="badge badge-success font-mono font-bold">GET</span>
          <h3 class="text-xl font-bold font-mono">/health</h3>
        </div>
        <p class="text-base-content/80 mb-6">API health check.</p>
      </div>

    </div>
  </div>
</body>
</html>"""

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

    # Trust Building Pages
    (OUTPUT_DIR / 'methodology.html').write_text(generate_methodology_html(), encoding='utf-8')
    logger.info('   methodology.html trust page')
    (OUTPUT_DIR / 'api.html').write_text(generate_api_html(), encoding='utf-8')
    logger.info('   api.html reference page')
    (OUTPUT_DIR / 'changelog.json').write_text(generate_changelog_json(), encoding='utf-8')
    logger.info('   changelog.json')

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
