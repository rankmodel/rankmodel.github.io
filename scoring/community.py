from math import log1p
import logging
logger = logging.getLogger(__name__)

def compute_trending_rank_score(trending_rank: int, total_trending: int = 20) -> float:
    if trending_rank <= 0:
        return 0.0
    if trending_rank == 1:
        return 100.0
    
    score = (total_trending - trending_rank + 1) / total_trending * 100
    return max(0.0, score)

def compute_community_score(model_data: dict) -> float:
    downloads = model_data.get('downloads', 0)
    likes = model_data.get('likes', 0)
    trending = model_data.get('trending_score', 0)
    
    log_downloads = log1p(downloads)
    log_likes = log1p(likes)
    
    downloads_score = min((log_downloads / log1p(1_000_000)) * 100, 100.0)
    likes_score = min((log_likes / log1p(50_000)) * 100, 100.0)
    trending_score = float(trending)
    
    final_score = (downloads_score * 0.4) + (likes_score * 0.4) + (trending_score * 0.2)
    return max(0.0, min(100.0, final_score))
