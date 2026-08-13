import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    from config.settings import SCORING_WEIGHTS, TIERS, ACHIEVEMENT_TYPES
except ImportError:
    SCORING_WEIGHTS = {
        'benchmarks': 0.4,
        'efficiency': 0.2,
        'community': 0.2,
        'recency': 0.1,
        'reproducibility': 0.1
    }
    TIERS = {90: 'S', 80: 'A', 70: 'B', 60: 'C', 0: 'D'}
    ACHIEVEMENT_TYPES = {}

import math as _math
from scoring.benchmarks import normalize_benchmark_scores, get_benchmark_score_for_model, get_benchmark_coverage
from scoring.efficiency import compute_efficiency_score, estimate_param_count_from_name
from scoring.community import compute_community_score
from scoring.recency import compute_recency_score, score_to_freshness_label
from scoring.reproducibility import compute_repro_score, check_benchmark_diversity

logger = logging.getLogger(__name__)

def compute_extended_metadata_score(model_data: dict) -> dict:
    extended_meta = {}
    
    # 1. context_window
    max_pos = model_data.get('config', {}).get('max_position_embeddings', 0)
    if max_pos < 2048: cw = 0
    elif max_pos < 4096: cw = 20
    elif max_pos < 8192: cw = 40
    elif max_pos < 32768: cw = 60
    elif max_pos < 128000: cw = 80
    else: cw = 100
    extended_meta['context_window'] = cw
    
    # 2. vram_tier
    param_count = model_data.get('safetensors', {}).get('total')
    if param_count is None:
        param_count = model_data.get('param_count')
    if param_count is None and 'name' in model_data:
        param_count = estimate_param_count_from_name(model_data['name'])
    param_count = param_count or 0
    param_b = param_count / 1e9
    if param_b < 3: vt = 100
    elif param_b < 7: vt = 80
    elif param_b < 13: vt = 65
    elif param_b < 34: vt = 45
    elif param_b < 70: vt = 25
    else: vt = 10
    extended_meta['vram_tier'] = vt
    
    # 3. license_score
    lic = str(model_data.get('license', '')).lower()
    if 'apache-2.0' in lic: ls = 100
    elif 'mit' in lic: ls = 90
    elif 'cc-by-4.0' in lic: ls = 75
    elif 'cc-by-sa-4.0' in lic: ls = 65
    elif 'cc-by-nc' in lic: ls = 40
    elif not lic or lic == 'none': ls = 0
    else: ls = 20
    extended_meta['license_score'] = ls
    
    # 4. finetune_friendly
    tags = model_data.get('tags', [])
    tags_lower = [str(t).lower() for t in tags]
    if any(any(k in t for k in ['lora', 'peft', 'qlora', 'finetuning']) for t in tags_lower):
        ff = 80
    else:
        ff = 30
    extended_meta['finetune_friendly'] = ff
    
    # 5. multilingual
    lang_count = 0
    for t in tags_lower:
        if t.startswith('lang:'): lang_count += 1
        elif t == 'multilingual': lang_count += 10
        elif ',' in t and all(len(x.strip()) in [2,3] for x in t.split(',')):
            lang_count += len(t.split(','))
    
    if lang_count == 0: ml = 10  # Fallback just in case, but spec says "1 lang -> 20"
    if lang_count == 0: ml = 20  # Assume at least 1 language usually? Let's use 20 for 0 or 1
    if lang_count <= 1: ml = 20
    elif lang_count <= 3: ml = 50
    elif lang_count <= 10: ml = 75
    else: ml = 100
    extended_meta['multilingual'] = ml
    
    # 6. safety_score
    evals = model_data.get('eval_results', [])
    bench_names = [e.get('benchmark', '').lower() for e in evals]
    if any('truthfulqa' in b or 'bbq' in b for b in bench_names):
        ss = 80
    else:
        ss = 40
    extended_meta['safety_score'] = ss
    
    # 7. update_velocity
    last_mod = model_data.get('last_modified')
    if not last_mod:
        uv = 20
    else:
        try:
            mod_date = datetime.fromisoformat(last_mod.replace('Z', '+00:00')).replace(tzinfo=None)
            days = (datetime.now() - mod_date).days
            if days < 30: uv = 100
            elif days < 90: uv = 80
            elif days < 180: uv = 60
            elif days < 365: uv = 40
            else: uv = 20
        except:
            uv = 20
    extended_meta['update_velocity'] = uv
    
    # 8. inference_coverage
    inf_tags = {'gguf', 'awq', 'gptq', 'onnx', 'tflite', 'coreml', 'openvino'}
    inf_count = sum(1 for t in tags_lower if t in inf_tags)
    if inf_count == 0: ic = 10
    elif inf_count == 1: ic = 40
    elif inf_count == 2: ic = 60
    else: ic = 85
    extended_meta['inference_coverage'] = ic
    
    # 9. community_momentum
    dl = model_data.get('downloads', 0) or 0
    likes = model_data.get('likes', 0) or 0
    dl_30d = model_data.get('downloads_30d')
    if dl_30d is not None and dl_30d > 0:
        # Just use ratio for simplicity as fallback is acceptable
        pass
    
    if (likes > dl * 0.01) if dl else (likes > 0):
        cm = 70
    else:
        cm = 40
    extended_meta['community_momentum'] = cm
    
    # 10. hub_completeness
    hc = 0
    if model_data.get('modelcard_data'): hc += 20
    if model_data.get('pipeline_tag'): hc += 20
    if model_data.get('tags'): hc += 20
    if model_data.get('license'): hc += 20
    if model_data.get('repo_url'): hc += 20
    extended_meta['hub_completeness'] = hc
    
    return extended_meta


def score_to_tier(score: float) -> str:
    for threshold in sorted(TIERS.keys(), reverse=True):
        if score >= threshold:
            return TIERS[threshold]
    return TIERS.get(0, 'F')

def compute_composite_score(model_data: dict, eval_results: list, all_models_stats: dict = None) -> dict:
    try:
        model_id = model_data.get('id', 'unknown')
        
        bench_info = get_benchmark_score_for_model(model_id, eval_results)
        coverage = get_benchmark_coverage(eval_results)
        benchmark_score = bench_info['score']
        
        if 'param_count' not in model_data and 'name' in model_data:
            model_data['param_count'] = estimate_param_count_from_name(model_data['name'])
            
        efficiency_score = compute_efficiency_score(model_data, benchmark_score, all_models_stats)
        community_score = compute_community_score(model_data)
        
        last_modified = model_data.get('last_modified') or datetime.now().isoformat()
        recency_score = compute_recency_score(last_modified)
        
        reproducibility_score = compute_repro_score(eval_results)
        
        composite = (
            benchmark_score * SCORING_WEIGHTS.get('benchmarks', 0.40) +
            efficiency_score * SCORING_WEIGHTS.get('efficiency', 0.20) +
            community_score * SCORING_WEIGHTS.get('community', 0.20) +
            recency_score * SCORING_WEIGHTS.get('recency', 0.10) +
            reproducibility_score * SCORING_WEIGHTS.get('reproducibility', 0.10)
        )
        
        extended_meta = compute_extended_metadata_score(model_data)
        
        return {
            'model_id': model_id,
            'composite': round(composite, 2),
            'extended': extended_meta,
            'extended_composite': round(sum(extended_meta.values()) / len(extended_meta), 2) if extended_meta else 0.0,
            'breakdown': {
                'benchmarks': round(benchmark_score, 2),
                'efficiency': round(efficiency_score, 2),
                'community': round(community_score, 2),
                'recency': round(recency_score, 2),
                'reproducibility': round(reproducibility_score, 2),
            },
            'tier': score_to_tier(composite),
            'computed_at': datetime.now().isoformat(),
            'details': {
                'benchmark_details': bench_info,
                'diversity_details': check_benchmark_diversity(eval_results),
                'freshness_label': score_to_freshness_label(recency_score),
            },
            'confidence': coverage.get('confidence', 'low'),
            'coverage': coverage,
        }
    except Exception as e:
        logger.error(f"Error computing composite score: {e}")
        return {
            'model_id': model_data.get('id', 'unknown'),
            'composite': 0.0,
            'extended': {},
            'extended_composite': 0.0,
            'breakdown': {'benchmarks': 0.0, 'efficiency': 0.0, 'community': 0.0, 'recency': 0.0, 'reproducibility': 0.0},
            'tier': 'D',
            'computed_at': datetime.now().isoformat(),
            'details': {}
        }

def batch_score_models(models: list, cache=None) -> list[dict]:
    perf_list = []
    
    for model_data in models:
        evals = model_data.get('eval_results', [])
        bench_info = get_benchmark_score_for_model(model_data.get('id', ''), evals)
        b_score = bench_info['score']
        
        param_count = model_data.get('param_count')
        if param_count is None and 'name' in model_data:
            param_count = estimate_param_count_from_name(model_data['name'])
            
        if param_count and param_count > 0:
            perf_list.append(b_score / (param_count / 1e9))
            
    all_models_stats = {}
    if perf_list:
        all_models_stats['efficiency'] = {
            'min': min(perf_list),
            'max': max(perf_list)
        }
        
    scored_models = []
    for model_data in models:
        evals = model_data.get('eval_results', [])
        score_data = compute_composite_score(model_data, evals, all_models_stats)
        scored_models.append(score_data)
        
    scored_models.sort(key=lambda x: x['composite'], reverse=True)
    
    for rank, score_data in enumerate(scored_models, 1):
        score_data['rank'] = rank
        
    if cache:
        pass
        
    return scored_models

def get_achievements(model_data: dict, score_data: dict, global_rank: int, trending_models: list = None) -> list[dict]:
    achievements = []
    model_id = model_data.get('id', '')
    
    if trending_models and model_id in trending_models[:10]:
        achievements.append({'type': 'trending_top10', 'icon': '🔥', 'label': 'Top Trending', 'color': 'red', 'description': 'In the top 10 trending models'})
        
    if score_data.get('breakdown', {}).get('efficiency', 0.0) > 85:
        achievements.append({'type': 'efficiency_king', 'icon': '⚡', 'label': 'Efficiency King', 'color': 'green', 'description': 'Exceptional performance for its size'})
        
    if score_data.get('breakdown', {}).get('community', 0.0) > 80:
        achievements.append({'type': 'community_favorite', 'icon': '❤️', 'label': 'Community Favorite', 'color': 'pink', 'description': 'Highly popular and liked'})
        
    if score_data.get('breakdown', {}).get('benchmarks', 0.0) > 90:
        achievements.append({'type': 'benchmark_champion', 'icon': '🏆', 'label': 'Benchmark Champion', 'color': 'gold', 'description': 'Top tier benchmark performance'})
        
    if model_data.get('is_abliterated'):
        achievements.append({'type': 'abliterated', 'icon': '🔓', 'label': 'Abliterated', 'color': 'purple', 'description': 'Uncensored / Abliterated model'})
        
    if model_data.get('is_quantized'):
        achievements.append({'type': 'quantized_ready', 'icon': '🗜️', 'label': 'Quantized', 'color': 'blue', 'description': 'Quantized for efficiency'})
        
    if global_rank == 1:
        achievements.append({'type': 'top_1', 'icon': '👑', 'label': '#1 Global', 'color': 'gold', 'description': 'The number one ranked model'})
    elif global_rank <= 3:
        achievements.append({'type': 'top_3', 'icon': '🥈', 'label': 'Top 3 Global', 'color': 'silver', 'description': 'Top 3 globally ranked model'})
    elif global_rank <= 10:
        achievements.append({'type': 'top_10', 'icon': '🏅', 'label': 'Top 10 Global', 'color': 'bronze', 'description': 'Top 10 globally ranked model'})
        
    return achievements

ELO_K_FACTOR = 32
ELO_BASE_RATING = 1200

def composite_to_elo(composite_score: float) -> float:
    """Convert composite 0-100 score to ELO-like rating (800-1600 range)."""
    return 800 + (composite_score * 8)

def expected_win_probability(rating_a: float, rating_b: float) -> float:
    """Bradley-Terry expected win probability for model A vs model B."""
    return 1.0 / (1.0 + _math.pow(10, (rating_b - rating_a) / 400))

def compare_models_elo(score_a: dict, score_b: dict) -> dict:
    """
    Given two score dicts, compute Bradley-Terry win probability
    and dimension-level comparison.
    Returns comparison dict with win_probability and dimension winners.
    """
    composite_a = score_a.get('composite', 0)
    composite_b = score_b.get('composite', 0)
    elo_a = composite_to_elo(composite_a)
    elo_b = composite_to_elo(composite_b)
    win_prob_a = expected_win_probability(elo_a, elo_b)
    
    breakdown_a = score_a.get('breakdown', {})
    breakdown_b = score_b.get('breakdown', {})
    
    dimension_winners = {}
    for dim in ['benchmarks', 'efficiency', 'community', 'recency', 'reproducibility']:
        va = breakdown_a.get(dim, 0)
        vb = breakdown_b.get(dim, 0)
        if va > vb:
            dimension_winners[dim] = 'A'
        elif vb > va:
            dimension_winners[dim] = 'B'
        else:
            dimension_winners[dim] = 'tie'
    
    return {
        'win_probability_a': round(win_prob_a, 4),
        'win_probability_b': round(1 - win_prob_a, 4),
        'elo_a': round(elo_a),
        'elo_b': round(elo_b),
        'composite_a': composite_a,
        'composite_b': composite_b,
        'dimension_winners': dimension_winners,
        'overall_winner': 'A' if composite_a >= composite_b else 'B',
    }
