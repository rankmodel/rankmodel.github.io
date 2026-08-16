#!/usr/bin/env python3
"""
ModelRank - AI Model Rating & Badge System
Run with: python main.py [api|ui|score|leaderboard]
"""
import sys
import argparse

def run_api():
    from api.server import app
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000, reload=False)

def run_ui():
    from ui.app import demo, theme, CSS
    demo.launch(server_name='0.0.0.0', server_port=7860, theme=theme, css=CSS)

def score_model(model_id: str):
    try:
        from data.fetcher import HFDataFetcher
        from scoring.engine import compute_composite_score, get_achievements
        from badges.generator import BadgeGenerator
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich import print as rprint
    except ImportError as e:
        import traceback
        traceback.print_exc()
        print(f"Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)
        
    console = Console()
    with console.status(f"[cyan]Fetching data for {model_id}...", spinner="dots"):
        fetcher = HFDataFetcher()
        model_data = fetcher.fetch_model_info(model_id)
        
    if not model_data:
        console.print(f"[red]Model {model_id} not found![/red]")
        return
        
    with console.status("[cyan]Computing scores...", spinner="dots"):
        eval_results = fetcher.fetch_eval_results(model_id)
        score = compute_composite_score(model_data, eval_results)
        # get_achievements requires (model_data, score_data, global_rank)
        # We pass dummy global_rank for CLI single score
        achievements = get_achievements(model_data, score, 0)
        
    # Display results
    console.print(Panel(f"[bold white]{model_id}[/bold white] - Tier: [bold cyan]{score.get('tier', 'N/A')}[/bold cyan] - Score: [bold green]{score.get('composite', 0):.2f}[/bold green]"))
    
    table = Table(title="Score Breakdown")
    table.add_column("Dimension", style="cyan")
    table.add_column("Score", justify="right", style="green")
    
    dims = score.get('breakdown', {})
    for k, v in dims.items():
        table.add_row(k.capitalize(), f"{v:.2f}")
        
    console.print(table)
    
    if achievements:
        console.print("\n[bold yellow]Achievements:[/bold yellow]")
        for a in achievements:
            console.print(f"🏆 {a['label']}: {a['description']}")
            
    console.print(f"\n[dim]Markdown Badge: [![ModelRank](https://api.modelrank.com/badge/{model_id}?type=score)](https://modelrank.com)[/dim]")

def run_recommend(use_case: str, limit: int = 10):
    try:
        from data.cache import ModelCache
        from scoring.recommend import recommend, available_use_cases
        from rich.table import Table
        from rich.console import Console
    except ImportError as e:
        print(f"Missing dependency: {e}")
        sys.exit(1)

    if use_case not in available_use_cases():
        print(f"Unknown use-case '{use_case}'. Available: {', '.join(available_use_cases())}")
        sys.exit(1)

    cache = ModelCache()
    rows = recommend(use_case, cache, limit=limit)
    console = Console()
    table = Table(title=f"ModelRank — best for: {use_case}")
    table.add_column("Rank", justify="right", style="cyan")
    table.add_column("Model", style="white")
    table.add_column("Use-case score", justify="right", style="green")
    table.add_column("Tier", justify="center", style="magenta")
    for i, r in enumerate(rows, 1):
        table.add_row(str(i), r["model_id"], f"{r['use_case_score']:.2f}", r.get("tier") or "?")
    console.print(table)


def run_leaderboard(limit: int = 20, tier: str = None):
    try:
        from data.cache import ModelCache
        from rich.table import Table
        from rich.console import Console
    except ImportError:
        print("Missing dependencies.")
        sys.exit(1)
        
    console = Console()
    cache = ModelCache()
    models = cache.get_leaderboard(limit=limit, tier=tier)
    
    table = Table(title=f"ModelRank Leaderboard (Top {len(models)})")
    table.add_column("Rank", justify="right", style="cyan", no_wrap=True)
    table.add_column("Model", style="white")
    table.add_column("Tier", justify="center", style="magenta")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Downloads", justify="right", style="yellow")
    
    for idx, m in enumerate(models):
        tier_str = m.get('score', {}).get('tier', 'C')
        score = f"{m.get('score', {}).get('composite', 0):.2f}"
        dl = m.get('model', {}).get('downloads', 0)
        dl_str = f"{dl/1000000:.1f}M" if dl >= 1000000 else f"{dl/1000:.1f}K" if dl >= 1000 else str(dl)
        table.add_row(str(idx + 1), m.get('model_id', ''), tier_str, score, dl_str)
        
    console.print(table)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ModelRank CLI')
    parser.add_argument('command', choices=['api', 'ui', 'score', 'leaderboard', 'recommend'], help='Command to run')
    parser.add_argument('--model', '-m', help='Model ID for score command')
    parser.add_argument('--limit', '-n', type=int, default=20, help='Number of models for leaderboard')
    parser.add_argument('--tier', '-t', help='Filter by tier')
    parser.add_argument('--use-case', '-u', default='general', help='Use case for recommend (coding|chat|research|local|multilingual|general)')
    args = parser.parse_args()
    
    if args.command == 'api': run_api()
    elif args.command == 'ui': run_ui()
    elif args.command == 'score':
        if not args.model: parser.error('--model required for score command')
        score_model(args.model)
    elif args.command == 'leaderboard': run_leaderboard(args.limit, args.tier)
    elif args.command == 'recommend': run_recommend(args.use_case, args.limit)
