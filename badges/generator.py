import base64
from pathlib import Path
from typing import Literal
from badges.templates import (BadgeTemplate, load_template, get_score_color,
                               get_rank_color, score_to_stars, DIMENSION_META)
from config.settings import TIER_COLORS, ACHIEVEMENT_TYPES

BadgeType = Literal['score', 'rank', 'tier', 'dimension', 'achievement']

class BadgeGenerator:
    def __init__(self):
        self._template_cache = {}
    
    def _get_template(self, badge_type: str) -> BadgeTemplate:
        if badge_type not in self._template_cache:
            self._template_cache[badge_type] = load_template(badge_type)
        return self._template_cache[badge_type]
    
    def _generate_flat_badge(self, label: str, value: str, color: str) -> str:
        # Approximate width calculation (7px per char + padding)
        lw = len(label) * 7 + 14
        vw = len(str(value)) * 7 + 14
        tw = lw + vw
        
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{tw}" height="20">
    <linearGradient id="b" x2="0" y2="100%">
        <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
        <stop offset="1" stop-opacity=".1"/>
    </linearGradient>
    <mask id="a">
        <rect width="{tw}" height="20" rx="3" fill="#fff"/>
    </mask>
    <g mask="url(#a)">
        <rect width="{lw}" height="20" fill="#555"/>
        <rect x="{lw}" width="{vw}" height="20" fill="{color}"/>
        <rect width="{tw}" height="20" fill="url(#b)"/>
    </g>
    <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
        <text x="{lw/2}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
        <text x="{lw/2}" y="14">{label}</text>
        <text x="{lw + vw/2}" y="15" fill="#010101" fill-opacity=".3">{value}</text>
        <text x="{lw + vw/2}" y="14">{value}</text>
    </g>
</svg>"""
    
    def generate_score_badge(self, score: float, tier: str, style: str = 'default') -> str:
        color = get_score_color(score)
        if style == 'flat':
            return self._generate_flat_badge("modelrank", f"{score:.1f} ({tier})", color)
            
        template = self._get_template('score')
        return template.render(
            score=round(score, 1),
            color=color,
            tier=tier
        )
    
    def generate_rank_badge(self, rank: int, total: int, style: str = 'default') -> str:
        rank_color, medal_icon = get_rank_color(rank)
        if style == 'flat':
            return self._generate_flat_badge("rank", f"#{rank} of {total}", rank_color)
            
        template = self._get_template('rank')
        return template.render(
            rank=rank,
            total=total,
            rank_color=rank_color,
            medal_icon=medal_icon
        )
    
    def generate_tier_badge(self, tier: str, style: str = 'default') -> str:
        tier_color = TIER_COLORS.get(tier, '#cccccc')
        if style == 'flat':
            return self._generate_flat_badge("tier", tier, tier_color)
            
        template = self._get_template('tier')
        tier_glow = tier_color + '66'
        return template.render(
            tier=tier,
            tier_color=tier_color,
            tier_glow=tier_glow
        )
    
    def generate_dimension_badge(self, dimension: str, value: float, style: str = 'default') -> str:
        meta = DIMENSION_META.get(dimension, {'icon': '📊', 'label': dimension.title(), 'color': '#6366f1'})
        if style == 'flat':
            return self._generate_flat_badge(meta['label'], f"{value:.1f}", meta['color'])
            
        template = self._get_template('dimension')
        stars = score_to_stars(value)
        return template.render(
            dimension_icon=meta['icon'],
            dimension_label=meta['label'],
            dimension_color=meta['color'],
            value=round(value, 1),
            stars=stars
        )
    
    def generate_achievement_badge(self, achievement_type: str, style: str = 'default') -> str:
        ach_meta = next((a for a in ACHIEVEMENT_TYPES if a['id'] == achievement_type), None)
        if not ach_meta:
            ach_meta = {'icon': '🏆', 'name': achievement_type, 'color': '#fbbf24'}
        color = ach_meta['color']
        
        if style == 'flat':
            return self._generate_flat_badge("achievement", ach_meta.get('name', achievement_type), color)
            
        template = self._get_template('achievement')
        # Darken color by 30%
        color_dark = color
        if color.startswith('#') and len(color) == 7:
            r = max(0, int(int(color[1:3], 16) * 0.7))
            g = max(0, int(int(color[3:5], 16) * 0.7))
            b = max(0, int(int(color[5:7], 16) * 0.7))
            color_dark = f'#{r:02x}{g:02x}{b:02x}'
        return template.render(
            achievement_icon=ach_meta.get('icon', '🏆'),
            achievement_text=ach_meta.get('name', achievement_type),
            achievement_color=color,
            achievement_color_dark=color_dark
        )
    
    def generate_badge(self, model_id: str, score_data: dict, badge_type: str, dimension: str = None, achievement_type: str = None, style: str = 'default') -> str:
        if badge_type == 'score':
            return self.generate_score_badge(score_data.get('composite', 0.0), score_data.get('tier', 'C'), style=style)
        elif badge_type == 'tier':
            return self.generate_tier_badge(score_data.get('tier', 'C'), style=style)
        elif badge_type == 'rank':
            return self.generate_rank_badge(score_data.get('rank', 999), 1000, style=style)
        elif badge_type == 'dimension':
            if not dimension:
                dimension = 'benchmarks'
            breakdown = score_data.get('breakdown', {})
            return self.generate_dimension_badge(dimension, breakdown.get(dimension, 0.0), style=style)
        elif badge_type == 'achievement':
            if not achievement_type:
                achievement_type = 'verified'
            return self.generate_achievement_badge(achievement_type, style=style)
        else:
            raise ValueError(f"Unknown badge type: {badge_type}")
            
    def generate_all_badges(self, model_id: str, score_data: dict, achievements: list, style: str = 'default') -> dict:
        composite = score_data.get('composite', 0.0)
        tier = score_data.get('tier', 'D')
        rank = score_data.get('rank', 9999)
        result = {
            'score': self.generate_score_badge(composite, tier, style=style),
            'rank': self.generate_rank_badge(rank, 1000, style=style),
            'tier': self.generate_tier_badge(tier, style=style),
            'dimensions': {},
            'achievements': []
        }
        breakdown = score_data.get('breakdown', {})
        for dim, val in breakdown.items():
            result['dimensions'][dim] = self.generate_dimension_badge(dim, val, style=style)
        for ach in achievements:
            ach_type = ach.get('type', '') if isinstance(ach, dict) else ach
            if ach_type:
                result['achievements'].append(self.generate_achievement_badge(ach_type, style=style))
        return result
    
    def svg_to_png_base64(self, svg_str: str) -> str:
        try:
            import cairosvg
            png_bytes = cairosvg.svg2png(bytestring=svg_str.encode('utf-8'))
            return base64.b64encode(png_bytes).decode('utf-8')
        except ImportError:
            print("Warning: cairosvg not available. Returning original SVG.")
            return svg_str
            
    def svg_to_markdown(self, svg_str: str, alt_text: str = 'ModelRank Badge') -> str:
        b64 = base64.b64encode(svg_str.encode('utf-8')).decode('utf-8')
        return f"![{alt_text}](data:image/svg+xml;base64,{b64})"

def generate_badge(badge_type: str, value: str, label: str = '', style: str = 'default', **kwargs) -> str:
    gen = BadgeGenerator()
    if badge_type == 'score':
        return gen.generate_score_badge(float(value), kwargs.get('tier', 'B'), style=style)
    elif badge_type == 'rank':
        return gen.generate_rank_badge(int(value), int(kwargs.get('total', 1000)), style=style)
    elif badge_type == 'tier':
        return gen.generate_tier_badge(value, style=style)
    elif badge_type == 'dimension':
        return gen.generate_dimension_badge(label, float(value), style=style)
    elif badge_type == 'achievement':
        return gen.generate_achievement_badge(value, style=style)
    else:
        raise ValueError(f"Unknown badge type: {badge_type}")
