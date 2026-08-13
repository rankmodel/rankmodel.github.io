import logging
from math import log1p
from typing import List, Optional, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

BENCHMARK_META = {
    # Core frontier benchmarks (high weight)
    'mmlu-pro':  {'name': 'MMLU-Pro',  'weight': 0.20, 'higher_is_better': True, 'max_possible': 100},
    'gpqa':      {'name': 'GPQA',      'weight': 0.20, 'higher_is_better': True, 'max_possible': 100},
    'hle':       {'name': 'HLE',       'weight': 0.15, 'higher_is_better': True, 'max_possible': 100},
    'gsm8k':     {'name': 'GSM8K',     'weight': 0.10, 'higher_is_better': True, 'max_possible': 100},
    'humaneval': {'name': 'HumanEval', 'weight': 0.10, 'higher_is_better': True, 'max_possible': 100},
    # Open LLM Leaderboard v2 benchmarks
    'bbh':       {'name': 'BBH',       'weight': 0.08, 'higher_is_better': True, 'max_possible': 100},
    'ifeval':    {'name': 'IFEval',    'weight': 0.07, 'higher_is_better': True, 'max_possible': 100},
    'musr':      {'name': 'MuSR',      'weight': 0.05, 'higher_is_better': True, 'max_possible': 100},
    'math':      {'name': 'MATH',      'weight': 0.05, 'higher_is_better': True, 'max_possible': 100},
    # Classic benchmarks that are only used as fallback
    'arc':       {'name': 'ARC',        'weight': 0.0, 'fallback_weight': 0.25, 'higher_is_better': True, 'max_possible': 100},
    'hellaswag': {'name': 'HellaSwag',  'weight': 0.0, 'fallback_weight': 0.25, 'higher_is_better': True, 'max_possible': 100},
    'truthfulqa':{'name': 'TruthfulQA', 'weight': 0.0, 'fallback_weight': 0.25, 'higher_is_better': True, 'max_possible': 100},
    'winogrande':{'name': 'WinoGrande', 'weight': 0.0, 'fallback_weight': 0.25, 'higher_is_better': True, 'max_possible': 100},
}

CLASSIC_BENCHMARKS = {'arc', 'hellaswag', 'truthfulqa', 'winogrande'}
FRONTIER_BENCHMARKS = {'mmlu-pro', 'gpqa', 'hle', 'gsm8k', 'humaneval', 'bbh', 'ifeval', 'musr', 'math'}

ALIAS_MAP = {
    # MMLU-Pro
    'mmlu': 'mmlu-pro',
    'mmlu_pro': 'mmlu-pro',
    'mmlu-pro': 'mmlu-pro',
    'leaderboard_mmlu_pro': 'mmlu-pro',
    'open-llm-leaderboard/mmlu-pro': 'mmlu-pro',
    'cais/mmlu': 'mmlu-pro',
    'mmlu-pro (5-shot)': 'mmlu-pro',
    # GPQA
    'gpqa': 'gpqa',
    'gpqa_diamond': 'gpqa',
    'gpqa diamond': 'gpqa',
    'leaderboard_gpqa': 'gpqa',
    'open-llm-leaderboard/gpqa': 'gpqa',
    'idavidrein/gpqa': 'gpqa',
    # HLE
    'hle': 'hle',
    'humanity_last_exam': 'hle',
    "humanity's_last_exam": 'hle',
    'leaderboard_hle': 'hle',
    # GSM8K
    'gsm8k': 'gsm8k',
    'gsm8k_cot': 'gsm8k',
    'gsm8k (5-shot)': 'gsm8k',
    'leaderboard_gsm8k': 'gsm8k',
    # HumanEval
    'humaneval': 'humaneval',
    'human_eval': 'humaneval',
    'humaneval_plus': 'humaneval',
    'openai_humaneval': 'humaneval',
    'code_eval': 'humaneval',
    # BBH
    'bbh': 'bbh',
    'bigbench_hard': 'bbh',
    'big_bench_hard': 'bbh',
    'leaderboard_bbh': 'bbh',
    # IFEval
    'ifeval': 'ifeval',
    'if_eval': 'ifeval',
    'leaderboard_ifeval': 'ifeval',
    # MuSR
    'musr': 'musr',
    'leaderboard_musr': 'musr',
    # MATH
    'math': 'math',
    'math lvl 5': 'math',
    'math_level5': 'math',
    'leaderboard_math_hard': 'math',
    # ARC
    'arc': 'arc',
    'arc_challenge': 'arc',
    'arc_easy': 'arc',
    # HellaSwag
    'hellaswag': 'hellaswag',
    # TruthfulQA
    'truthfulqa': 'truthfulqa',
    'truthful_qa': 'truthfulqa',
    # WinoGrande
    'winogrande': 'winogrande',
}


def _resolve_benchmark_id(b_id: str) -> str:
    b_id = b_id.lower()
    return ALIAS_MAP.get(b_id, b_id)

def normalize_benchmark_scores(eval_results: list, leaderboard_bounds: dict = None) -> float:
    if not eval_results:
        return 0.0
        
    total_score = 0.0
    total_weight = 0.0
    
    # First pass: check if any frontier benchmarks are present
    found_frontier = any(
        _resolve_benchmark_id(r.get('dataset_id', '')) in FRONTIER_BENCHMARKS
        for r in eval_results
    )
    
    for result in eval_results:
        raw_id = result.get('dataset_id', '')
        b_id = _resolve_benchmark_id(raw_id)
        if b_id not in BENCHMARK_META:
            continue
            
        meta = BENCHMARK_META[b_id]
        score = result.get('value', result.get('score', 0.0))
        if 0 < score <= 1.0:
            score *= 100.0
            
        if leaderboard_bounds and b_id in leaderboard_bounds:
            b_min = leaderboard_bounds[b_id].get('min', 0.0)
            b_max = leaderboard_bounds[b_id].get('max', 100.0)
            if b_max > b_min:
                norm_score = (score - b_min) / (b_max - b_min) * 100
            else:
                norm_score = score
        else:
            norm_score = score
        
        # Use frontier weight if frontier benchmarks exist; otherwise use fallback_weight
        if found_frontier:
            w = meta['weight']
        else:
            w = meta.get('fallback_weight', meta['weight'])
            
        total_score += norm_score * w
        total_weight += w
        
    if total_weight > 0:
        # Apply a confidence penalty when only classic benchmarks found (classic benchmarks are easier, inflate scores)
        raw = total_score / total_weight
        if not found_frontier:
            # Classic-only: cap at 75 and apply 0.85 confidence factor
            raw = min(raw * 0.85, 75.0)
        return max(0.0, min(100.0, raw))
    return 0.0

def get_benchmark_score_for_model(model_id: str, eval_results: list, bounds_fetcher=None) -> dict:
    bounds = bounds_fetcher() if bounds_fetcher else None
    
    found = []
    missing = []
    details = {}
    
    found_ids = set()
    for result in eval_results:
        raw_id = result.get('dataset_id', '')
        b_id = _resolve_benchmark_id(raw_id)
        if b_id in BENCHMARK_META:
            found_ids.add(b_id)
            found.append(b_id)
            val = result.get('value', result.get('score', 0.0))
            if 0 < val <= 1.0:
                val *= 100.0
            details[b_id] = val
            
    for b_id in BENCHMARK_META:
        if b_id not in found_ids:
            missing.append(b_id)
            
    score = normalize_benchmark_scores(eval_results, bounds)
    
    return {
        'score': score,
        'benchmarks_found': found,
        'benchmarks_missing': missing,
        'details': details
    }

def get_benchmark_coverage(eval_results: list) -> dict:
    """
    Returns coverage statistics for how many of the key benchmarks are present.
    Useful for confidence scoring and flagging insufficient eval data.
    """
    found_ids = set()
    for result in eval_results:
        raw_id = result.get('dataset_id', '')
        b_id = _resolve_benchmark_id(raw_id)
        if b_id in BENCHMARK_META:
            found_ids.add(b_id)
    
    total = len(BENCHMARK_META)
    found = len(found_ids)
    coverage_pct = (found / total) * 100 if total > 0 else 0
    
    return {
        'total_benchmarks': total,
        'found_benchmarks': found,
        'missing_benchmarks': [b for b in BENCHMARK_META if b not in found_ids],
        'coverage_percent': round(coverage_pct, 1),
        'confidence': 'high' if coverage_pct >= 80 else ('medium' if coverage_pct >= 40 else 'low')
    }
