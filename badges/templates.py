import os
import re
from pathlib import Path
from config.settings import BADGE_OUTPUT_DIR, TIER_COLORS, RANK_COLORS, DIMENSION_COLORS, ACHIEVEMENT_TYPES

BRAND_TEMPLATES_DIR = Path('brand/templates/')

class BadgeTemplate:
    def __init__(self, template_name: str):
        self.path = BRAND_TEMPLATES_DIR / f"{template_name}.svg"
        if not self.path.exists():
            raise FileNotFoundError(f"Template not found at {self.path}")
        with open(self.path, 'r', encoding='utf-8') as f:
            self.template_str = f.read()
    
    def render(self, **kwargs) -> str:
        rendered = self.template_str
        for k, v in kwargs.items():
            rendered = rendered.replace(f"{{{k}}}", str(v))
        
        # Check for unfilled placeholders
        unfilled = re.findall(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}', rendered)
        if unfilled:
            import logging
            logging.getLogger(__name__).warning(f"Possibly unfilled placeholders in template: {', '.join(unfilled)}")
            
        return rendered

def load_template(badge_type: str) -> BadgeTemplate:
    mapping = {
        'score': 'score_badge',
        'rank': 'rank_badge',
        'tier': 'tier_badge',
        'dimension': 'dimension_badge',
        'achievement': 'achievement_badge'
    }
    filename = mapping.get(badge_type, f"{badge_type}_badge")
    return BadgeTemplate(filename)

def get_score_color(score: float) -> str:
    if score > 90:
        return '#22c55e'
    elif score > 80:
        return '#84cc16'
    elif score > 70:
        return '#eab308'
    elif score > 60:
        return '#f97316'
    else:
        return '#ef4444'

def get_rank_color(rank: int) -> tuple[str, str]:
    if rank == 1:
        return ('#fbbf24', '🥇')
    elif rank == 2:
        return ('#94a3b8', '🥈')
    elif rank == 3:
        return ('#cd7c3a', '🥉')
    else:
        return ('#6366f1', '🏅')

def score_to_stars(score: float) -> str:
    filled = min(5, max(0, round(score / 20)))
    empty = 5 - filled
    return '★' * filled + '☆' * empty

DIMENSION_META = {
    'benchmarks': {'icon': '🧠', 'label': 'Benchmarks', 'color': '#6366f1'},
    'efficiency': {'icon': '⚡', 'label': 'Efficiency', 'color': '#22c55e'},
    'community': {'icon': '🔥', 'label': 'Community', 'color': '#f59e0b'},
    'recency': {'icon': '🕐', 'label': 'Freshness', 'color': '#06b6d4'},
    'reproducibility': {'icon': '✅', 'label': 'Verified', 'color': '#ec4899'}
}
