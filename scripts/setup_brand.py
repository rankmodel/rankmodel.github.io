#!/usr/bin/env python3
import json
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

def validate_templates(base_dir: Path) -> bool:
    templates_dir = base_dir / "brand" / "templates"
    console.print(f"[cyan]Validating templates in {templates_dir}[/cyan]")
    
    if not templates_dir.exists():
        console.print("[red]Templates directory not found![/red]")
        return False
        
    expected_templates = ['score.svg', 'rank.svg', 'tier.svg', 'dimension.svg', 'achievement.svg']
    all_found = True
    
    for template in expected_templates:
        if not (templates_dir / template).exists():
            console.print(f"[red]Missing template: {template}[/red]")
            all_found = False
        else:
            console.print(f"[green]Found: {template}[/green]")
            
    return all_found

def generate_samples(base_dir: Path):
    samples_dir = base_dir / "brand" / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(f"\n[cyan]Generating sample badges in {samples_dir}[/cyan]")
    
    # In a real app, we would import BadgeGenerator and use it.
    # For this script, we'll simulate the generation by copying dummy files or creating mock SVGs
    
    sample_types = ['score', 'rank', 'tier', 'dimension', 'achievement']
    for stype in sample_types:
        sample_path = samples_dir / f"sample_{stype}.svg"
        with open(sample_path, 'w') as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg"><text>{stype} sample</text></svg>')
        console.print(f"[green]Generated: {sample_path.name}[/green]")
        
def main():
    base_dir = Path(__file__).parent.parent
    
    console.print("[bold magenta]ModelRank Brand Setup[/bold magenta]")
    
    brand_file = base_dir / "brand" / "brand_book.json"
    if brand_file.exists():
        try:
            with open(brand_file, 'r') as f:
                brand_data = json.load(f)
            console.print(f"[green]Loaded brand config: {brand_data.get('name', 'ModelRank')}[/green]")
        except Exception as e:
            console.print(f"[red]Error loading brand_book.json: {e}[/red]")
    else:
        console.print("[yellow]brand_book.json not found, proceeding with defaults.[/yellow]")
        
    if validate_templates(base_dir):
        console.print("[bold green]All templates valid![/bold green]")
        
    generate_samples(base_dir)
    console.print("[bold magenta]Setup complete![/bold magenta]")

if __name__ == "__main__":
    main()
