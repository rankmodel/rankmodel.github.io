import gradio as gr
import pandas as pd
import plotly.graph_objects as go
import json
import base64
from datetime import datetime
from typing import Optional

from data.fetcher import HFDataFetcher
from data.cache import ModelCache
from scoring.engine import compute_composite_score, get_achievements
from badges.generator import BadgeGenerator
from config.settings import TIER_COLORS, DIMENSION_COLORS

try:
    from data.notebooklm_integration import ModelPodcastGenerator
    podcast_gen = ModelPodcastGenerator()
except ImportError:
    podcast_gen = None

fetcher = HFDataFetcher()
cache = ModelCache()
badge_gen = BadgeGenerator()

# ---- Helpers ----

def format_number(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)

def format_params(n: Optional[int]) -> str:
    if n is None:
        return "Unknown"
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n/1_000_000:.0f}M"
    return str(n)

def svg_to_html_img(svg_str: str, height: int = 28) -> str:
    b64 = base64.b64encode(svg_str.encode('utf-8')).decode('utf-8')
    return f'<img src="data:image/svg+xml;base64,{b64}" style="margin: 4px; height: {height}px; display: inline-block;"/>'

def score_html_card(model_id: str, score: dict, model_data: dict) -> str:
    tier = score.get('tier', 'C')
    tier_color = TIER_COLORS.get(tier, '#cccccc')
    composite = score.get('composite', 0)
    breakdown = score.get('breakdown', {})
    freshness = score.get('details', {}).get('freshness_label', '')
    param_str = format_params(model_data.get('param_count'))
    downloads = format_number(model_data.get('downloads', 0))
    likes = format_number(model_data.get('likes', 0))
    tags = model_data.get('tags', [])[:6]
    pipeline = model_data.get('pipeline_tag', '')

    dim_labels = {
        'benchmarks': ('🧠', 'Benchmarks'),
        'efficiency': ('⚡', 'Efficiency'),
        'community': ('🔥', 'Community'),
        'recency': ('🕐', 'Freshness'),
        'reproducibility': ('✅', 'Verified'),
    }
    dim_colors = {
        'benchmarks': '#6366f1',
        'efficiency': '#22c55e',
        'community': '#f59e0b',
        'recency': '#06b6d4',
        'reproducibility': '#ec4899',
    }

    def score_color(v):
        if v >= 80: return '#22c55e'
        if v >= 60: return '#eab308'
        if v >= 40: return '#f97316'
        return '#ef4444'

    tags_html = ''.join(
        f'<span style="background:#1e1e3f;color:#a5b4fc;padding:2px 8px;border-radius:12px;font-size:11px;margin:2px;display:inline-block;">{t}</span>'
        for t in tags
    )

    dim_bars = ''
    for k, (icon, label) in dim_labels.items():
        v = breakdown.get(k, 0)
        color = dim_colors.get(k, '#6366f1')
        dim_bars += f'''
        <div style="margin:8px 0;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                <span style="color:#e2e8f0;font-size:13px;">{icon} {label}</span>
                <span style="color:{score_color(v)};font-weight:700;font-size:14px;">{v:.1f}</span>
            </div>
            <div style="background:#2d2d50;border-radius:6px;height:8px;overflow:hidden;">
                <div style="background:{color};width:{min(v,100):.0f}%;height:8px;border-radius:6px;transition:width 0.3s;"></div>
            </div>
        </div>'''

    html = f'''
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f0f23;color:#e2e8f0;border-radius:16px;padding:24px;border:1px solid #2d2d50;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px;flex-wrap:wrap;gap:12px;">
            <div>
                <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;">Model</div>
                <div style="font-size:20px;font-weight:700;color:#f1f5f9;">{model_id.split('/')[-1]}</div>
                <div style="font-size:12px;color:#64748b;">{model_id}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;">Score</div>
                <div style="font-size:42px;font-weight:900;color:{score_color(composite)};line-height:1;">{composite:.1f}</div>
                <div style="margin-top:6px;">
                    <span style="background:{tier_color};color:#000;font-weight:800;font-size:13px;padding:3px 14px;border-radius:20px;">{tier} Tier</span>
                </div>
            </div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:20px;">
            <div style="background:#1a1a36;border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:11px;color:#64748b;">Parameters</div>
                <div style="font-size:18px;font-weight:700;color:#a5b4fc;">{param_str}</div>
            </div>
            <div style="background:#1a1a36;border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:11px;color:#64748b;">Downloads</div>
                <div style="font-size:18px;font-weight:700;color:#34d399;">{downloads}</div>
            </div>
            <div style="background:#1a1a36;border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:11px;color:#64748b;">Likes</div>
                <div style="font-size:18px;font-weight:700;color:#f472b6;">{likes}</div>
            </div>
        </div>

        {f'<div style="margin-bottom:12px;font-size:12px;"><span style="color:#64748b;">Task: </span><span style="color:#a5b4fc;">{pipeline}</span></div>' if pipeline else ''}
        {f'<div style="margin-bottom:12px;font-size:12px;"><span style="color:#64748b;">Freshness: </span><span style="color:#06b6d4;">{freshness}</span></div>' if freshness else ''}

        <div style="margin:16px 0;">
            <div style="font-size:12px;color:#64748b;margin-bottom:10px;text-transform:uppercase;letter-spacing:0.05em;">Score Breakdown</div>
            {dim_bars}
        </div>

        {f'<div style="margin-top:12px;">{tags_html}</div>' if tags else ''}
    </div>'''
    return html

def create_radar_chart(score_data: dict, title: str = '') -> go.Figure:
    categories = ['Benchmarks', 'Efficiency', 'Community', 'Freshness', 'Verified']
    dims = score_data.get('breakdown', {})
    values = [
        dims.get('benchmarks', 0),
        dims.get('efficiency', 0),
        dims.get('community', 0),
        dims.get('recency', 0),
        dims.get('reproducibility', 0)
    ]
    values.append(values[0])
    categories.append(categories[0])

    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(99, 102, 241, 0.3)',
        line=dict(color='#6366f1', width=2),
        name=title or 'Score'
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor='#2d2d50', tickcolor='#64748b', tickfont=dict(color='#64748b', size=9)),
            angularaxis=dict(gridcolor='#2d2d50', tickcolor='#94a3b8', tickfont=dict(color='#94a3b8', size=11)),
            bgcolor='#0f0f23',
        ),
        showlegend=bool(title),
        legend=dict(font=dict(color='white')),
        paper_bgcolor='#0f0f23',
        plot_bgcolor='#0f0f23',
        font=dict(color='white'),
        margin=dict(l=40, r=40, t=40, b=40),
        title=dict(text=title, font=dict(color='white', size=13)) if title else None,
    )
    return fig

def create_comparison_radar(score1: dict, score2: dict, label1: str, label2: str) -> go.Figure:
    categories = ['Benchmarks', 'Efficiency', 'Community', 'Freshness', 'Verified']
    def vals(s):
        d = s.get('breakdown', {})
        v = [d.get('benchmarks',0), d.get('efficiency',0), d.get('community',0), d.get('recency',0), d.get('reproducibility',0)]
        v.append(v[0])
        return v
    cats = categories + [categories[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=vals(score1), theta=cats, fill='toself', name=label1.split('/')[-1], fillcolor='rgba(99,102,241,0.3)', line=dict(color='#6366f1', width=2)))
    fig.add_trace(go.Scatterpolar(r=vals(score2), theta=cats, fill='toself', name=label2.split('/')[-1], fillcolor='rgba(239,68,68,0.3)', line=dict(color='#ef4444', width=2)))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor='#2d2d50'), angularaxis=dict(gridcolor='#2d2d50'), bgcolor='#0f0f23'),
        showlegend=True, legend=dict(font=dict(color='white', size=12), bgcolor='#1a1a36'),
        paper_bgcolor='#0f0f23', font=dict(color='white'),
        margin=dict(l=40, r=40, t=40, b=40),
    )
    return fig

def create_leaderboard_df(models: list, search: str = '') -> pd.DataFrame:
    if not models:
        return pd.DataFrame(columns=['Rank', 'Model', 'Score', 'Tier', 'Bench', 'Effic', 'Comm', 'Downloads', 'Task', 'Ach'])
    tier_emojis = {'S': '💜 S', 'A': '💙 A', 'B': '💚 B', 'C': '💛 C', 'D': '❤️ D'}
    df_data = []
    for idx, item in enumerate(models):
        m = item.get('model', {})
        s = item.get('score', {})
        model_id = item.get('model_id', '')
        if search and search.lower() not in model_id.lower():
            continue
        tier = s.get('tier', 'C')
        bd = s.get('breakdown', {})
        df_data.append({
            'Rank': idx + 1,
            'Model': model_id,
            'Score': f"{s.get('composite', 0):.1f}",
            'Tier': tier_emojis.get(tier, tier),
            'Bench': f"{bd.get('benchmarks', 0):.0f}",
            'Effic': f"{bd.get('efficiency', 0):.0f}",
            'Comm': f"{bd.get('community', 0):.0f}",
            'Downloads': format_number(m.get('downloads', 0)),
            'Task': m.get('pipeline_tag', ''),
            'Ach': len(s.get('achievements', [])),
        })
    return pd.DataFrame(df_data)

def get_cache_stats() -> str:
    try:
        total = cache.get_size() if hasattr(cache, 'get_size') else 0
        s_count = cache.get_total_models(tier='S') if hasattr(cache, 'get_total_models') else 0
        a_count = cache.get_total_models(tier='A') if hasattr(cache, 'get_total_models') else 0
        return f'''
        <div style="display:flex;gap:16px;padding:12px 0;flex-wrap:wrap;">
            <div style="background:#1a1a36;border-radius:10px;padding:10px 18px;border:1px solid #2d2d50;">
                <div style="font-size:10px;color:#64748b;text-transform:uppercase;">Total Scored</div>
                <div style="font-size:22px;font-weight:700;color:#a5b4fc;">{total}</div>
            </div>
            <div style="background:#1a1a36;border-radius:10px;padding:10px 18px;border:1px solid #2d2d50;">
                <div style="font-size:10px;color:#64748b;text-transform:uppercase;">S Tier</div>
                <div style="font-size:22px;font-weight:700;color:#a855f7;">{s_count}</div>
            </div>
            <div style="background:#1a1a36;border-radius:10px;padding:10px 18px;border:1px solid #2d2d50;">
                <div style="font-size:10px;color:#64748b;text-transform:uppercase;">A Tier</div>
                <div style="font-size:22px;font-weight:700;color:#3b82f6;">{a_count}</div>
            </div>
        </div>'''
    except:
        return ''

def score_model(model_id: str):
    if not model_id or not model_id.strip():
        err = '<div style="color:#ef4444;padding:12px;background:#1a0f0f;border-radius:8px;">⚠️ Please enter a model ID (e.g., <code>mistralai/Mistral-7B-v0.1</code>)</div>'
        return err, None, '', '', ''
    model_id = model_id.strip()
    try:
        model_data = fetcher.fetch_model_info(model_id)
        if not model_data:
            err = f'<div style="color:#ef4444;padding:12px;background:#1a0f0f;border-radius:8px;">❌ Model <b>{model_id}</b> not found on HuggingFace.</div>'
            return err, None, '', '', ''
        eval_results = fetcher.fetch_eval_results(model_id)
        score = compute_composite_score(model_data, eval_results)
        cache.set_score(model_id, score)
        radar_chart = create_radar_chart(score)
        b_score = badge_gen.generate_badge(model_id, score, 'score')
        b_tier = badge_gen.generate_badge(model_id, score, 'tier')
        badges_html = f'<div style="padding:8px 0;">{svg_to_html_img(b_tier)}{svg_to_html_img(b_score)}</div>'
        achievements = get_achievements(model_data, score, 0)
        if achievements:
            ach_html = '<div style="padding:8px 0;display:flex;flex-wrap:wrap;gap:6px;">'
            for a in achievements:
                a_badge = badge_gen.generate_badge(model_id, score, 'achievement', achievement_type=a['type'])
                ach_html += svg_to_html_img(a_badge)
            ach_html += '</div>'
        else:
            ach_html = '<p style="color:#64748b;font-size:13px;">No achievements earned yet.</p>'
        card_html = score_html_card(model_id, score, model_data)
        tier_color = TIER_COLORS.get(score.get('tier', 'C'), '#ccc')
        success_msg = f'<div style="color:#22c55e;padding:10px 12px;background:#0f1f0f;border-radius:8px;border-left:3px solid #22c55e;">✅ Successfully scored <b>{model_id}</b> — Tier <b style="color:{tier_color}">{score.get("tier")}</b> | Score: <b>{score.get("composite", 0):.2f}</b></div>'
        return card_html, radar_chart, badges_html, ach_html, success_msg
    except Exception as e:
        err = f'<div style="color:#ef4444;padding:12px;background:#1a0f0f;border-radius:8px;">❌ Error scoring model: {str(e)}</div>'
        return err, None, '', '', ''

def compare_models(model_id_1: str, model_id_2: str):
    if not model_id_1 or not model_id_2:
        return '<div style="color:#f59e0b;padding:12px;">⚠️ Please enter both model IDs to compare.</div>', None, None
    try:
        def fetch_score(mid):
            md = fetcher.fetch_model_info(mid.strip())
            ev = fetcher.fetch_eval_results(mid.strip())
            sc = compute_composite_score(md, ev)
            return md, sc
        md1, sc1 = fetch_score(model_id_1)
        md2, sc2 = fetch_score(model_id_2)
        radar = create_comparison_radar(sc1, sc2, model_id_1, model_id_2)
        bd1 = sc1.get('breakdown', {})
        bd2 = sc2.get('breakdown', {})
        dim_labels = [('🧠 Benchmarks', 'benchmarks'), ('⚡ Efficiency', 'efficiency'), ('🔥 Community', 'community'), ('🕐 Freshness', 'recency'), ('✅ Verified', 'reproducibility')]
        winner_composite = model_id_1 if sc1.get('composite', 0) >= sc2.get('composite', 0) else model_id_2
        rows = ''
        for label, key in dim_labels:
            v1 = bd1.get(key, 0)
            v2 = bd2.get(key, 0)
            w1 = '🏆' if v1 > v2 else ('🤝' if v1 == v2 else '')
            w2 = '🏆' if v2 > v1 else ('🤝' if v1 == v2 else '')
            c1 = '#22c55e' if v1 >= v2 else '#64748b'
            c2 = '#22c55e' if v2 >= v1 else '#64748b'
            rows += f'<tr><td style="padding:8px;color:#94a3b8;">{label}</td><td style="padding:8px;text-align:center;color:{c1};font-weight:700;">{w1} {v1:.1f}</td><td style="padding:8px;text-align:center;color:{c2};font-weight:700;">{w2} {v2:.1f}</td></tr>'
        comp_html = f'''
        <div style="font-family:-apple-system,sans-serif;background:#0f0f23;color:#e2e8f0;border-radius:12px;padding:20px;border:1px solid #2d2d50;">
            <div style="text-align:center;margin-bottom:16px;padding:12px;background:#1a1a36;border-radius:8px;">
                <span style="color:#64748b;font-size:12px;">Winner: </span>
                <span style="color:#fbbf24;font-weight:700;font-size:16px;">👑 {winner_composite.split('/')[-1]}</span>
            </div>
            <table style="width:100%;border-collapse:collapse;">
                <thead><tr>
                    <th style="padding:8px;text-align:left;color:#64748b;font-size:11px;text-transform:uppercase;">Dimension</th>
                    <th style="padding:8px;text-align:center;color:#6366f1;font-size:12px;">{model_id_1.split('/')[-1]}<br><small style="color:#64748b;font-weight:normal;">{sc1.get('composite',0):.1f} ({sc1.get('tier','')})</small></th>
                    <th style="padding:8px;text-align:center;color:#ef4444;font-size:12px;">{model_id_2.split('/')[-1]}<br><small style="color:#64748b;font-weight:normal;">{sc2.get('composite',0):.1f} ({sc2.get('tier','')})</small></th>
                </tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>'''
        return comp_html, radar, None
    except Exception as e:
        return f'<div style="color:#ef4444;padding:12px;">❌ Error: {str(e)}</div>', None, None

def load_leaderboard(task_filter: str, tier_filter: str, limit: int, search: str = '') -> pd.DataFrame:
    try:
        task = task_filter if task_filter != 'All' else None
        tier = tier_filter if tier_filter != 'All' else None
        models = cache.get_leaderboard(limit=limit, task=task, tier=tier)
        return create_leaderboard_df(models, search)
    except Exception as e:
        print(f'Error loading leaderboard: {e}')
        return pd.DataFrame()

def generate_custom_badge(model_id: str, badge_type: str, dimension: str, style: str):
    if not model_id:
        return 'Please enter a model ID to generate a badge.', ''
    try:
        score = cache.get_score(model_id)
        if not score:
            model_data = fetcher.fetch_model_info(model_id)
            if not model_data:
                return 'Model not found.', ''
            eval_results = fetcher.fetch_eval_results(model_id)
            score = compute_composite_score(model_data, eval_results)
        dim = dimension if badge_type == 'dimension' else None
        svg = badge_gen.generate_badge(model_id, score, badge_type, dimension=dim, style=style)
        html_preview = svg_to_html_img(svg)
        embed_code = f'![ModelRank](https://api.modelrank.com/badge/{model_id}?type={badge_type}'
        if dim: embed_code += f'&dimension={dim}'
        if style != 'default': embed_code += f'&style={style}'
        embed_code += ')'
        return html_preview, embed_code
    except Exception as e:
        return f'Error: {e}', ''

async def generate_ui_podcast(model_id: str):
    if not model_id:
        return None, '<div style="color:#f59e0b;padding:12px;">⚠️ Please enter a model ID.</div>'
    if podcast_gen is None:
        return None, '<div style="color:#ef4444;padding:12px;">❌ notebooklm-py not installed. Run: <code>pip install notebooklm-py[browser]</code> then <code>notebooklm login</code></div>'
    try:
        out_path = await podcast_gen.generate_podcast(model_id)
        if out_path:
            return str(out_path), f'<div style="color:#22c55e;padding:12px;">✅ Podcast generated for <b>{model_id}</b></div>'
        return None, '<div style="color:#ef4444;padding:12px;">❌ Failed to generate podcast.</div>'
    except Exception as e:
        return None, f'<div style="color:#ef4444;padding:12px;">❌ Error: {str(e)}</div>'

# ---- Theme ----
theme = gr.themes.Soft(
    primary_hue='indigo',
    secondary_hue='blue',
    neutral_hue='slate'
).set(
    body_background_fill='#0a0a1a',
    body_text_color='#e2e8f0',
    block_background_fill='#0f0f23',
    block_label_text_color='#94a3b8',
    block_title_text_color='#e2e8f0',
    button_primary_background_fill='#6366f1',
    button_primary_background_fill_hover='#4f46e5',
    input_background_fill='#1a1a36',
)

# ---- Build UI ----
CSS = '''
    .gradio-container { max-width: 1200px; }
    .tab-nav button { font-size: 14px !important; }
    footer { display: none !important; }
    .svelte-1gfkn6j { border-color: #2d2d50 !important; }
'''

# ---- Build UI ----
with gr.Blocks(title='ModelRank — HuggingFace Model Leaderboard') as demo:
    gr.HTML('''
    <div style="text-align:center;padding:24px 0 12px;font-family:-apple-system,sans-serif;">
        <div style="font-size:32px;font-weight:900;color:#f1f5f9;letter-spacing:-0.5px;">🏆 ModelRank</div>
        <div style="font-size:15px;color:#64748b;margin-top:6px;">Composite scoring & leaderboard for HuggingFace models</div>
    </div>''')

    stats_html = gr.HTML(value=get_cache_stats)

    with gr.Tabs():
        with gr.Tab('🔍 Score a Model'):
            with gr.Row():
                model_input = gr.Textbox(
                    label='Model ID',
                    placeholder='e.g., mistralai/Mistral-7B-v0.1 or meta-llama/Llama-3-8B',
                    scale=5
                )
                analyze_btn = gr.Button('⚡ Analyze', variant='primary', scale=1)

            status_msg = gr.HTML()

            with gr.Row():
                with gr.Column(scale=6):
                    score_card = gr.HTML(label='Score Card')
                with gr.Column(scale=5):
                    radar_plot = gr.Plot(label='Radar Chart')

            with gr.Row():
                with gr.Column():
                    gr.Markdown('**Badges**')
                    badges_html = gr.HTML()
                with gr.Column():
                    gr.Markdown('**Achievements**')
                    achievements_html = gr.HTML()

            analyze_btn.click(
                fn=score_model,
                inputs=[model_input],
                outputs=[score_card, radar_plot, badges_html, achievements_html, status_msg]
            )
            model_input.submit(
                fn=score_model,
                inputs=[model_input],
                outputs=[score_card, radar_plot, badges_html, achievements_html, status_msg]
            )

        with gr.Tab('⚔️ Compare Models'):
            with gr.Row():
                cmp_model1 = gr.Textbox(label='Model A', placeholder='mistralai/Mistral-7B-v0.1', scale=4)
                cmp_model2 = gr.Textbox(label='Model B', placeholder='meta-llama/Llama-3-8B', scale=4)
                cmp_btn = gr.Button('⚔️ Compare', variant='primary', scale=1)
            cmp_result = gr.HTML()
            cmp_radar = gr.Plot(label='Head-to-Head Radar')
            cmp_btn.click(fn=compare_models, inputs=[cmp_model1, cmp_model2], outputs=[cmp_result, cmp_radar, gr.State()])

        with gr.Tab('🏆 Leaderboard'):
            with gr.Row():
                search_box = gr.Textbox(label='Search', placeholder='Filter by model name...', scale=3)
                task_dropdown = gr.Dropdown(choices=['All', 'text-generation', 'text-classification', 'image-generation', 'text-to-image', 'feature-extraction'], value='All', label='Task', scale=2)
                tier_dropdown = gr.Dropdown(choices=['All', 'S', 'A', 'B', 'C', 'D'], value='All', label='Tier', scale=1)
                limit_slider = gr.Slider(minimum=10, maximum=200, step=10, value=50, label='Limit', scale=2)
                refresh_btn = gr.Button('🔄 Refresh', scale=1)

            leaderboard_df = gr.Dataframe(
                headers=['Rank', 'Model', 'Score', 'Tier', 'Bench', 'Effic', 'Comm', 'Downloads', 'Task', 'Ach'],
                interactive=False,
                wrap=True
            )

            refresh_btn.click(fn=load_leaderboard, inputs=[task_dropdown, tier_dropdown, limit_slider, search_box], outputs=[leaderboard_df])
            search_box.change(fn=load_leaderboard, inputs=[task_dropdown, tier_dropdown, limit_slider, search_box], outputs=[leaderboard_df])
            demo.load(fn=load_leaderboard, inputs=[task_dropdown, tier_dropdown, limit_slider, search_box], outputs=[leaderboard_df])

        with gr.Tab('🎨 Badge Studio'):
            with gr.Row():
                badge_model_id = gr.Textbox(label='Model ID', placeholder='mistralai/Mistral-7B-v0.1', scale=4)
            with gr.Row():
                badge_type = gr.Radio(choices=['score', 'rank', 'tier', 'dimension', 'achievement'], value='score', label='Badge Type')
                badge_style = gr.Radio(choices=['default', 'flat'], value='default', label='Style')
                badge_dim = gr.Dropdown(choices=['benchmarks', 'efficiency', 'community', 'recency', 'reproducibility'], label='Dimension (if type=dimension)')
                generate_badge_btn = gr.Button('🎨 Generate', variant='primary')
            badge_preview = gr.HTML(label='Preview')
            badge_embed = gr.Textbox(label='Markdown Embed Code')
            generate_badge_btn.click(fn=generate_custom_badge, inputs=[badge_model_id, badge_type, badge_dim, badge_style], outputs=[badge_preview, badge_embed])

        with gr.Tab('🎙️ Podcast Studio'):
            gr.HTML('''
            <div style="background:#1a1a36;border-radius:12px;padding:20px;margin-bottom:16px;border:1px solid #2d2d50;">
                <div style="font-size:16px;font-weight:700;color:#e2e8f0;margin-bottom:8px;">🎙️ AI Deep Dive Podcast</div>
                <div style="color:#94a3b8;font-size:14px;line-height:1.6;">Generate a 5-minute technical podcast using Google NotebookLM, discussing the model's architecture, benchmarks, and best use cases. Requires <code style="background:#0f0f23;padding:2px 6px;border-radius:4px;">notebooklm-py</code> to be installed and <code style="background:#0f0f23;padding:2px 6px;border-radius:4px;">notebooklm login</code> to be run.</div>
            </div>''')
            with gr.Row():
                podcast_model_id = gr.Textbox(label='Model ID', placeholder='mistralai/Mistral-7B-v0.1', scale=5)
                generate_podcast_btn = gr.Button('🎙️ Generate Podcast', variant='primary', scale=1)
            podcast_status = gr.HTML()
            podcast_audio = gr.Audio(label='Generated Podcast', interactive=False)
            generate_podcast_btn.click(fn=generate_ui_podcast, inputs=[podcast_model_id], outputs=[podcast_audio, podcast_status])

        with gr.Tab('ℹ️ About'):
            gr.Markdown('''
## About ModelRank

ModelRank uses a composite scoring methodology to evaluate HuggingFace models across **5 dimensions**.

### Scoring Formula
| Dimension | Weight | Description |
|-----------|--------|-------------|
| 🧠 Benchmarks | 40% | Aggregated performance on MMLU-Pro, GPQA, HLE, GSM8K, HumanEval |
| ⚡ Efficiency | 20% | Benchmark performance relative to parameter count |
| 🔥 Community | 20% | Downloads, likes, and trending score |
| 🕐 Freshness | 10% | Exponential decay based on days since last update |
| ✅ Verified | 10% | Source quality and benchmark diversity |

### Tier System
| Tier | Score Range | Description |
|------|-------------|-------------|
| 💜 S | 90-100 | State of the art |
| 💙 A | 80-89 | Excellent |
| 💚 B | 70-79 | Solid |
| 💛 C | 60-69 | Niche |
| ❤️ D | <60 | Legacy |

### API
Start the REST API with `python main.py api` and access docs at `http://localhost:8000/docs`.
''')

if __name__ == '__main__':
    demo.launch(server_name='0.0.0.0', server_port=7860, share=False, theme=theme, css=CSS)
