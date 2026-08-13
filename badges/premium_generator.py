"""
Premium SVG Badge Generator for ModelRank Pro/Featured plans.
Generates animated, glow, and premium badge variants.
"""
import math
from typing import Optional
from config.settings import TIER_COLORS


def generate_animated_score_badge(score: float, tier: str) -> str:
    """Animated score badge with pulsing ring — Pro plan."""
    color = _score_color(score)
    tier_color = TIER_COLORS.get(tier, '#6366f1')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="120" height="36">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#0f0f23"/>
      <stop offset="100%" stop-color="#1a1a36"/>
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="2" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="120" height="36" rx="8" fill="url(#bg)" stroke="{color}" stroke-width="1.5"/>
  <text x="14" y="14" font-family="system-ui,sans-serif" font-size="8" fill="#64748b" font-weight="600" letter-spacing="0.5">MODELRANK</text>
  <text x="14" y="28" font-family="system-ui,sans-serif" font-size="14" fill="{color}" font-weight="800" filter="url(#glow)">{score:.1f}</text>
  <rect x="82" y="8" width="28" height="20" rx="5" fill="{tier_color}" opacity="0.9"/>
  <text x="96" y="22" font-family="system-ui,sans-serif" font-size="11" fill="#000" font-weight="800" text-anchor="middle">{tier}</text>
  <animate attributeName="opacity" values="1;0.85;1" dur="3s" repeatCount="indefinite"/>
</svg>'''


def generate_glow_tier_badge(tier: str) -> str:
    """Glow-effect tier badge — Pro plan."""
    tier_color = TIER_COLORS.get(tier, '#6366f1')
    glow = tier_color + '88'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="80" height="32">
  <defs>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{tier_color}" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="{tier_color}" stop-opacity="0.6"/>
    </linearGradient>
  </defs>
  <rect width="80" height="32" rx="8" fill="#0f0f23" stroke="{tier_color}" stroke-width="1.5"/>
  <text x="40" y="12" font-family="system-ui,sans-serif" font-size="7" fill="#64748b" text-anchor="middle" letter-spacing="1">MODELRANK</text>
  <text x="40" y="26" font-family="system-ui,sans-serif" font-size="16" fill="{tier_color}" font-weight="900" text-anchor="middle" filter="url(#glow)">{tier}</text>
</svg>'''


def generate_featured_badge(model_name: str, score: float, tier: str) -> str:
    """Full premium featured badge with model name — Featured plan."""
    color = _score_color(score)
    tier_color = TIER_COLORS.get(tier, '#6366f1')
    short_name = model_name.split('/')[-1][:18]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="180" height="48">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#0a0a1a"/>
      <stop offset="100%" stop-color="#12122a"/>
    </linearGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="2" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="180" height="48" rx="10" fill="url(#bg)" stroke="{tier_color}" stroke-width="1.5"/>
  <rect x="0" y="0" width="5" height="48" rx="3" fill="{tier_color}"/>
  <text x="14" y="16" font-family="system-ui,sans-serif" font-size="7.5" fill="#64748b" font-weight="600" letter-spacing="0.8">MODELRANK ★ FEATURED</text>
  <text x="14" y="31" font-family="system-ui,sans-serif" font-size="13" fill="#f1f5f9" font-weight="700">{short_name}</text>
  <text x="14" y="43" font-family="system-ui,sans-serif" font-size="9" fill="#64748b">Score:</text>
  <text x="36" y="43" font-family="system-ui,sans-serif" font-size="9" fill="{color}" font-weight="700" filter="url(#glow)">{score:.1f}</text>
  <rect x="148" y="10" width="24" height="28" rx="6" fill="{tier_color}"/>
  <text x="160" y="28" font-family="system-ui,sans-serif" font-size="13" fill="#000" font-weight="900" text-anchor="middle">{tier}</text>
</svg>'''


def generate_minimal_badge(score: float, tier: str) -> str:
    """Ultra-minimal badge for embedding in dense READMEs — Pro plan."""
    color = _score_color(score)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="90" height="20">
  <rect width="90" height="20" rx="3" fill="#0f0f23"/>
  <text x="6" y="14" font-family="system-ui,sans-serif" font-size="9" fill="#64748b">modelrank</text>
  <text x="64" y="14" font-family="system-ui,sans-serif" font-size="9" fill="{color}" font-weight="700">{score:.0f} {tier}</text>
</svg>'''


def _score_color(score: float) -> str:
    if score >= 90: return '#22c55e'
    if score >= 80: return '#84cc16'
    if score >= 70: return '#eab308'
    if score >= 60: return '#f97316'
    return '#ef4444'


PREMIUM_BADGE_GENERATORS = {
    'animated': generate_animated_score_badge,
    'glow': generate_glow_tier_badge,
    'featured': generate_featured_badge,
    'minimal': generate_minimal_badge,
}
