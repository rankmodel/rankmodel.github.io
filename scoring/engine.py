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
        
        return {
            'model_id': model_id,
            'composite': round(composite, 2),
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
