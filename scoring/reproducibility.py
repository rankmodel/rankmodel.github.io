from statistics import mean
import logging
logger = logging.getLogger(__name__)

SOURCE_SCORES = {
    'verified': 100,
    'community': 50,
    'open_llm_leaderboard': 90,
    'unverified': 20,
    'unknown': 10
}

def compute_repro_score(eval_results: list) -> float:
    if not eval_results:
        return 0.0
        
    scores = []
    for result in eval_results:
        if result.get('verified', False):
            scores.append(100.0)
        else:
            source = result.get('source', 'unknown').lower()
            scores.append(float(SOURCE_SCORES.get(source, 20.0)))
            
    base_score = mean(scores)
    
    unique_datasets = {res.get('dataset_id') for res in eval_results if res.get('dataset_id')}
    if len(unique_datasets) >= 3:
        base_score += 10.0
        
    return max(0.0, min(100.0, base_score))

def check_benchmark_diversity(eval_results: list) -> dict:
    datasets = list({res.get('dataset_id') for res in eval_results if res.get('dataset_id')})
    count = len(datasets)
    bonus = 10.0 if count >= 3 else 0.0
    
    return {
        'count': count,
        'datasets': datasets,
        'diversity_bonus': bonus
    }
