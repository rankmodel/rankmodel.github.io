#!/usr/bin/env python3
"""
Daily incremental leaderboard refresh for ModelRank.

Each run it:
  1. Loads the set of model IDs already ranked (the "latest leaderboard").
  2. Pulls *new* models from HuggingFace, sorted by recency
     (``createdAt`` by default — i.e. the freshest open models on the hub),
     excluding anything already ranked.
  3. Scores up to ``--daily`` of them with the same composite engine the
     site uses.
  4. Enforces a hard cap of ``--cap`` total models by removing the oldest
     entries (FIFO on insertion time), so the leaderboard always reflects
     the freshest ~``--cap`` open models and never grows unbounded.

Note on HuggingFace pagination: the public ``/api/models`` endpoint ignores
the ``offset`` parameter, so we cannot page by offset. Instead we fetch the
newest ``--fetch-limit`` models (recency-sorted) in a single call and dedup
against the existing leaderboard. If that still isn't enough new candidates,
a second pass uses ``--backup-sort`` (e.g. ``lastModified``).

This is the companion to scripts/seed_leaderboard.py: instead of rebuilding
from scratch, it *grows and trims* the leaderboard day over day.

Usage:
    python scripts/daily_refresh.py --daily 500 --cap 2000
    python scripts/daily_refresh.py --daily 500 --cap 2000 --sort createdAt --backup-sort lastModified
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("daily_refresh")


def _fetch_candidates(fetcher, task, sort, fetch_limit, already):
    """Return up to ``fetch_limit`` candidate model IDs not already ranked."""
    batch = fetcher.fetch_model_list(task=task, sort=sort, limit=fetch_limit)
    out = []
    for raw in batch:
        mid = raw.get("id") or raw.get("model_id")
        if mid and mid not in already:
            out.append(mid)
    return out


def refresh(task: str = "text-generation", sort: str = "createdAt",
            backup_sort: str = "lastModified", daily: int = 500, cap: int = 2000,
            delay: float = 0.1, fetch_limit: int = 1500):
    fetcher = HFDataFetcher()
    cache = ModelCache()

    before = cache.get_size()
    already = cache.get_scored_ids()
    logger.info("Leaderboard currently holds %d models; %d already ranked", before, len(already))

    candidates = _fetch_candidates(fetcher, task, sort, fetch_limit, already)
    if len(candidates) < daily:
        logger.info("Primary sort yielded %d new; trying backup sort '%s'", len(candidates), backup_sort)
        extra = _fetch_candidates(fetcher, task, backup_sort, fetch_limit, already | set(candidates))
        candidates.extend(extra)

    logger.info("Found %d candidate new models to score (target %d)", len(candidates), daily)

    added = 0
    failed = []
    for mid in candidates:
        if added >= daily:
            break
        try:
            model_data = fetcher.fetch_model_info(mid)
            if not model_data:
                failed.append(mid)
                continue
            eval_results = fetcher.fetch_eval_results(mid)
            score = compute_composite_score(model_data, eval_results)
            cache.set_score(mid, score)
            added += 1
            if added % 25 == 0:
                logger.info("  ranked %d/%d new models (latest: %s -> %.1f)", added, daily, mid, score.get("composite", 0))
        except Exception as e:
            failed.append(mid)
            logger.warning("  failed to rank %s: %s", mid, e)
        time.sleep(delay)

    after_add = cache.get_size()
    removed = cache.prune_oldest(cap)
    final = cache.get_size()

    logger.info(
        "Refresh complete: +%d ranked, %d failed, pruned %d oldest (cap=%d). "
        "Leaderboard size %d -> %d -> %d",
        added, len(failed), removed, cap, before, after_add, final,
    )
    if failed:
        logger.info("Failed model IDs (first 20): %s", ", ".join(failed[:20]))

    return {"added": added, "failed": len(failed), "removed": removed,
            "before": before, "after": final}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Incrementally refresh the ModelRank leaderboard from HuggingFace")
    parser.add_argument("--task", default="text-generation", help="HF pipeline task filter")
    parser.add_argument("--sort", default="createdAt", help="Primary recency sort (createdAt|lastModified|downloads|likes|trending)")
    parser.add_argument("--backup-sort", default="lastModified", help="Second-pass sort if primary yields too few new models")
    parser.add_argument("--daily", type=int, default=500, help="Max new models to rank this run")
    parser.add_argument("--cap", type=int, default=2000, help="Hard cap on total models kept")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between HF API calls (seconds)")
    parser.add_argument("--fetch-limit", type=int, default=1500, help="How many newest models to pull per sort pass")
    args = parser.parse_args()

    refresh(
        task=args.task, sort=args.sort, backup_sort=args.backup_sort,
        daily=args.daily, cap=args.cap, delay=args.delay, fetch_limit=args.fetch_limit,
    )
    sys.exit(0)
