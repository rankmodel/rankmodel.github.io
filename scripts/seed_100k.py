#!/usr/bin/env python3
"""
Seed 100k models incrementally.
Due to Hugging Face API rate limits and computation overhead, 
this script uses batching, checkpointing, and sleep intervals.
"""
import sys
import os
import time
import argparse
import logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.fetcher import HFDataFetcher
from data.cache import ModelCache
from scoring.engine import compute_composite_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_100k")

def seed_batch(start_idx: int, batch_size: int, task: str = None, sort: str = 'downloads', delay: float = 0.5):
    fetcher = HFDataFetcher()
    cache = ModelCache()
    
    logger.info(f"Fetching models {start_idx} to {start_idx + batch_size}...")
    # NOTE: In a real scenario for 100k, we'd use paginated GraphQL or the `search` endpoint with `limit` and `cursor`.
    # Here we mock the pagination logic since HF standard API doesn't allow offset > 10,000 easily.
    model_list = fetcher.fetch_model_list(task=task, sort=sort, limit=batch_size)
    
    success = 0
    for raw_model in model_list:
        model_id = raw_model.get('id', '')
        if not model_id or cache.get_score(model_id):
            continue
            
        try:
            model_data = fetcher.fetch_model_info(model_id)
            eval_results = fetcher.fetch_eval_results(model_id)
            if model_data:
                score = compute_composite_score(model_data, eval_results)
                cache.set_score(model_id, score)
                success += 1
                logger.info(f"[{success}] Seeded {model_id} (Score: {score['composite']})")
        except Exception as e:
            logger.error(f"Failed to seed {model_id}: {e}")
            
        time.sleep(delay)
        
    logger.info(f"Batch complete. Added {success} new models.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Batch seed 100k models gracefully.')
    parser.add_argument('--start', type=int, default=0, help='Starting offset')
    parser.add_argument('--batch', type=int, default=1000, help='Models per batch')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between API calls')
    args = parser.parse_args()
    
    seed_batch(args.start, args.batch, delay=args.delay)
