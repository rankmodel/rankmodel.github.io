from datetime import datetime
import logging
logger = logging.getLogger(__name__)
from math import exp, log
from typing import Union

HALF_LIFE_DAYS = 180
BOOST_WINDOW_DAYS = 7
PENALTY_THRESHOLD_DAYS = 730

def compute_recency_score(last_modified: Union[str, datetime]) -> float:
    if isinstance(last_modified, str):
        try:
            last_modified = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
        except ValueError:
            return 0.0
            
    now = datetime.now(last_modified.tzinfo)
    days_old = (now - last_modified).days
    if days_old < 0:
        days_old = 0
        
    base = 100 * exp(-days_old * log(2) / HALF_LIFE_DAYS)
    
    if days_old < BOOST_WINDOW_DAYS:
        base = min(100.0, base + 10)
    if days_old > PENALTY_THRESHOLD_DAYS:
        base = max(0.0, base - 10)
        
    return max(0.0, min(100.0, base))

def score_to_freshness_label(score: float) -> str:
    if score > 90:
        return 'Just Released'
    elif score > 70:
        return 'Fresh'
    elif score > 50:
        return 'Recent'
    elif score > 30:
        return 'Aging'
    else:
        return 'Legacy'
