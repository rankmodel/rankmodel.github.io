import re
from math import exp
import logging
logger = logging.getLogger(__name__)
from typing import Optional, Dict, Any

PARAM_TIERS = {
    7: 'small',
    13: 'medium',
    34: 'large',
    70: 'xlarge',
    999: 'massive'
}

def estimate_param_count_from_name(model_id: str) -> Optional[int]:
    # Match patterns like 8x7b, 8*7b, 70b, 13B, 7.2B
    moe_pattern = re.compile(r'(\d+)[x\*]([\d\.]+)b', re.IGNORECASE)
    moe_match = moe_pattern.search(model_id)
    if moe_match:
        experts = int(moe_match.group(1))
        params = float(moe_match.group(2))
        return int(experts * params * 1_000_000_000)
        
    std_pattern = re.compile(r'([\d\.]+)b', re.IGNORECASE)
    std_match = std_pattern.search(model_id)
    if std_match:
        params = float(std_match.group(1))
        return int(params * 1_000_000_000)
        
    return None

def compute_efficiency_score(model_data: dict, benchmark_score: float, all_models_stats: dict = None) -> float:
    param_count = model_data.get('safetensors', {}).get('total')
    if param_count is None:
        param_count = model_data.get('param_count')
    if param_count is None:
        return 50.0
        
    if param_count == 0:
        return 50.0

    perf_per_billion = benchmark_score / (param_count / 1e9)
    
    if all_models_stats and 'efficiency' in all_models_stats:
        eff_min = all_models_stats['efficiency'].get('min', 0.0)
        eff_max = all_models_stats['efficiency'].get('max', 1.0)
        if eff_max > eff_min:
            score = (perf_per_billion - eff_min) / (eff_max - eff_min) * 100
        else:
            score = 50.0
    else:
        # Sigmoid scaling
        score = 1 / (1 + exp(-0.1 * (perf_per_billion - 10))) * 100
        
    if model_data.get('is_quantized'):
        score += 5.0
        
    if param_count > 70_000_000_000 and benchmark_score < 70.0:
        score -= 5.0
        
    return max(0.0, min(100.0, score))
