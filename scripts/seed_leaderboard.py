#!/usr/bin/env python3
"""
Seed the ModelRank leaderboard with top models from HuggingFace.

Usage:
    python scripts/seed_leaderboard.py
    python scripts/seed_leaderboard.py --task text-generation --limit 50
    python scripts/seed_leaderboard.py --models mistralai/Mistral-7B-v0.1 meta-llama/Llama-2-7b-hf
"""
import sys
import os
import time
import argparse
import logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

from data.fetcher import HFDataFetcher
from data.cache import ModelCache
from scoring.engine import compute_composite_score, get_achievements

logging.basicConfig(level=logging.WARNING)
console = Console()


def seed_from_hf(task: str = 'text-generation', sort: str = 'downloads', limit: int = 20, delay: float = 0.5):
    """Fetch and score top models from HuggingFace."""
    fetcher = HFDataFetcher()
    cache = ModelCache()

    console.print(Panel(f"[bold cyan]ModelRank Leaderboard Seeder[/bold cyan]\nFetching top {limit} models{f' for task: {task}' if task else ''}", expand=False))

    with console.status("[cyan]Fetching model list from HuggingFace...", spinner="dots"):
        model_list = fetcher.fetch_model_list(task=task, sort=sort, limit=limit)

    console.print(f"[green]✓[/green] Found {len(model_list)} models to process")

    scored = []
    failed = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task_id = progress.add_task("Scoring models...", total=len(model_list))

        for raw_model in model_list:
            model_id = raw_model.get('id', '')
            if not model_id:
                progress.advance(task_id)
                continue

            progress.update(task_id, description=f"[cyan]Scoring: {model_id[:40]}...")

            try:
                model_data = fetcher.fetch_model_info(model_id)
                if not model_data:
                    failed.append(model_id)
                    progress.advance(task_id)
                    continue

                eval_results = fetcher.fetch_eval_results(model_id)
                score = compute_composite_score(model_data, eval_results)
                cache.set_score(model_id, score)
                scored.append({'model_id': model_id, 'score': score['composite'], 'tier': score['tier']})
            except Exception as e:
                failed.append(model_id)
                console.print(f"[red]  ✗ Failed: {model_id}: {e}[/red]")

            time.sleep(delay)  # Rate limit protection
            progress.advance(task_id)

    # Display results
    scored.sort(key=lambda x: x['score'], reverse=True)

    table = Table(title=f"Seeded Leaderboard ({len(scored)} models)")
    table.add_column("Rank", style="cyan", justify="right")
    table.add_column("Model", style="white")
    table.add_column("Score", style="green", justify="right")
    table.add_column("Tier", style="magenta", justify="center")

    for i, m in enumerate(scored[:20], 1):
        table.add_row(str(i), m['model_id'], f"{m['score']:.2f}", m['tier'])

    console.print(table)
    console.print(f"\n[bold green]✓ Seeded {len(scored)} models[/bold green]" + (f" | [red]{len(failed)} failed[/red]" if failed else ""))

    return scored


def seed_specific_models(model_ids: list):
    """Score and cache specific model IDs."""
    fetcher = HFDataFetcher()
    cache = ModelCache()

    console.print(Panel(f"[bold cyan]Seeding {len(model_ids)} specific models[/bold cyan]", expand=False))
    scored = []

    for model_id in model_ids:
        with console.status(f"[cyan]Scoring {model_id}...", spinner="dots"):
            try:
                model_data = fetcher.fetch_model_info(model_id)
                eval_results = fetcher.fetch_eval_results(model_id)
                score = compute_composite_score(model_data, eval_results)
                cache.set_score(model_id, score)
                scored.append(model_id)
                console.print(f"[green]✓[/green] {model_id}: {score['composite']:.2f} ({score['tier']})")
            except Exception as e:
                console.print(f"[red]✗[/red] {model_id}: {e}")

    return scored


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Seed the ModelRank leaderboard with HuggingFace models')
    parser.add_argument('--task', help='Pipeline task filter (e.g., text-generation)', default=None)
    parser.add_argument('--limit', type=int, default=20, help='Number of models to fetch')
    parser.add_argument('--sort', default='downloads', choices=['downloads', 'likes', 'trending'], help='Sort order')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between API calls (seconds)')
    parser.add_argument('--models', nargs='+', help='Specific model IDs to score')
    args = parser.parse_args()

    if args.models:
        seed_specific_models(args.models)
    else:
        seed_from_hf(task=args.task, sort=args.sort, limit=args.limit, delay=args.delay)
