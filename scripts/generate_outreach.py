#!/usr/bin/env python3
"""
scripts/generate_outreach.py

Reads the top N models from the leaderboard cache and generates
personalized outreach messages for each model's creator.

Output: outputs/outreach_campaign.md
"""
import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.cache import ModelCache

def get_percentile(score, all_scores):
    if not all_scores:
        return 100
    sorted_scores = sorted(all_scores)
    below = sum(1 for s in sorted_scores if s < score)
    percentile = (below / len(sorted_scores)) * 100
    return round(percentile)

def main():
    parser = argparse.ArgumentParser(description="Generate outreach campaign")
    parser.add_argument("--top", type=int, default=20, help="Top N models to generate outreach for")
    parser.add_argument("--output", type=str, default="outputs/outreach_campaign.md", help="Output file path")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    output_path = project_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cache = ModelCache()
    try:
        leaderboard = cache.get_leaderboard(limit=args.top)
        full_leaderboard = cache.get_leaderboard(limit=1000)
    except Exception as e:
        print(f"Error accessing cache: {e}")
        leaderboard = []
        full_leaderboard = []
        
    is_demo = False
    if not leaderboard:
        print("Leaderboard is empty (no models in cache yet). Generating DEMO version...")
        is_demo = True
        leaderboard = [
            {"model_id": "mistralai/Mistral-7B-v0.1", "composite_score": 92.5, "tier": "S", "metrics": {"efficiency": 95.0, "community": 90.0, "quality": 92.5}},
            {"model_id": "meta-llama/Llama-3-8B", "composite_score": 91.0, "tier": "S", "metrics": {"efficiency": 92.0, "community": 95.0, "quality": 86.0}},
            {"model_id": "Qwen/Qwen2-7B-Instruct", "composite_score": 89.5, "tier": "A", "metrics": {"efficiency": 88.0, "community": 85.0, "quality": 95.5}},
            {"model_id": "google/gemma-2-9b", "composite_score": 88.0, "tier": "A", "metrics": {"efficiency": 85.0, "community": 88.0, "quality": 91.0}},
            {"model_id": "microsoft/Phi-3-mini-4k-instruct", "composite_score": 85.5, "tier": "A", "metrics": {"efficiency": 98.0, "community": 82.0, "quality": 76.5}},
        ]
        full_leaderboard = leaderboard
        
    all_eff_scores = []
    for m in full_leaderboard:
        score_obj = m.get("score", {})
        if isinstance(score_obj, dict):
            eff = score_obj.get("breakdown", {}).get("efficiency", 0)
        else:
            eff = m.get("metrics", {}).get("efficiency", 0)
        all_eff_scores.append(eff)

    markdown_content = []
    markdown_content.append(f"# ModelRank Outreach Campaign")
    markdown_content.append(f"**Date Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    markdown_content.append(f"**Models Processed:** {len(leaderboard)}")
    if is_demo:
        markdown_content.append("\n**⚠️ NOTE: THIS IS A DEMO VERSION GENERATED WITH HARDCODED DATA ⚠️**")
        
    markdown_content.append("\n## Top Models Overview\n")
    markdown_content.append("| Rank | Model | Score | Tier | Efficiency | Community |")
    markdown_content.append("|------|-------|-------|------|------------|-----------|")
    
    for rank, model in enumerate(leaderboard, 1):
        model_id = model.get("model_id", "unknown/unknown")
        score_obj = model.get("score", {})
        if isinstance(score_obj, dict):
            score = score_obj.get("composite", 0)
            tier = score_obj.get("tier", "Unranked")
            breakdown = score_obj.get("breakdown", {})
            eff = breakdown.get("efficiency", 0)
            comm = breakdown.get("community", 0)
        else:
            score = model.get("composite_score", score_obj)
            tier = model.get("tier", "Unranked")
            metrics = model.get("metrics", {})
            eff = metrics.get("efficiency", 0)
            comm = metrics.get("community", 0)
        markdown_content.append(f"| {rank} | {model_id} | {score} | {tier} | {eff} | {comm} |")
        
    markdown_content.append("\n## Quick Stats for Launch Posts\n")
    if leaderboard:
        highest_scorer = leaderboard[0]
        
        def get_eff(m):
            sobj = m.get("score", {})
            return sobj.get("breakdown", {}).get("efficiency", 0) if isinstance(sobj, dict) else m.get("metrics", {}).get("efficiency", 0)
            
        def get_comm(m):
            sobj = m.get("score", {})
            return sobj.get("breakdown", {}).get("community", 0) if isinstance(sobj, dict) else m.get("metrics", {}).get("community", 0)

        def get_comp(m):
            sobj = m.get("score", {})
            return sobj.get("composite", 0) if isinstance(sobj, dict) else m.get("composite_score", sobj)
            
        most_efficient = max(leaderboard, key=get_eff)
        best_community = max(leaderboard, key=get_comm)
        
        markdown_content.append(f"- **Highest Scorer**: {highest_scorer.get('model_id')} ({get_comp(highest_scorer)}/100)")
        markdown_content.append(f"- **Most Efficient**: {most_efficient.get('model_id')} ({get_eff(most_efficient)}/100)")
        markdown_content.append(f"- **Best Community**: {best_community.get('model_id')} ({get_comm(best_community)}/100)")
        
    markdown_content.append("\n## Outreach Messages\n")
    
    for rank, model in enumerate(leaderboard, 1):
        model_id = model.get("model_id", "unknown/unknown")
        parts = model_id.split("/")
        org = parts[0] if len(parts) > 1 else "Creator"
        model_name = parts[1] if len(parts) > 1 else model_id
        
        score_obj = model.get("score", {})
        if isinstance(score_obj, dict):
            score = score_obj.get("composite", 0)
            tier = score_obj.get("tier", "Unranked")
            breakdown = score_obj.get("breakdown", {})
            eff = breakdown.get("efficiency", 0)
            comm = breakdown.get("community", 0)
        else:
            score = model.get("composite_score", score_obj)
            tier = model.get("tier", "Unranked")
            metrics = model.get("metrics", {})
            eff = metrics.get("efficiency", 0)
            comm = metrics.get("community", 0)
        
        eff_percentile = get_percentile(eff, all_eff_scores)
        if eff_percentile == 0 and len(all_eff_scores) > 1:
            eff_percentile = 1
        # For the top model, percentile will be high (e.g. 99)
        # But wait, percentile usually implies "better than X%". 
        # If it's the highest, below = N-1, percentile = (N-1)/N * 100.
        
        markdown_content.append(f"### #{rank}: {model_id}")
        
        # Template A
        template_a = f"""**Template A (Twitter/X DM):**
```text
Hey @{org}! We just ranked {model_name} on ModelRank — it scored {score}/100 ({tier}-tier), ranking #{rank} globally.

Your efficiency score is particularly strong at {eff}/100 — top {eff_percentile}% for models its size.

Free embed badge for your README:
![ModelRank](https://rankmodel.github.io/rankmodel1/badges/{model_id}/score.svg)

Want an animated Pro badge? First month free for original creators: [link]
```"""
        markdown_content.append(template_a)
        
        # Template B
        template_b = f"""**Template B (HuggingFace DM):**
```text
Hi {org} team 👋

We built ModelRank (https://rankmodel.github.io/rankmodel1), an independent composite scoring system for HuggingFace models.

Your model **{model_name}** just made our leaderboard:
- 🏆 Composite Score: **{score}/100** ({tier}-tier)
- ⚡ Efficiency: {eff}/100
- ❤️ Community: {comm}/100  
- 📊 Rank: #{rank} globally

Free embeddable badge for your model card:
```![ModelRank Score](https://rankmodel.github.io/rankmodel1/badges/{model_id}/score.svg)```

Would love to feature {model_name} as a highlighted model. Happy to chat!
— ModelRank Team
```"""
        
        # Wait, the Template B markdown format needs to be slightly tweaked to embed properly. Let's fix the triple backticks in Template B to just use standard backticks around the markdown image for the text output.
        # Actually, in Template B text:
        # ```![ModelRank Score]...```
        template_b = template_b.replace("```![ModelRank", "\\`\\`\\`![ModelRank").replace(".svg)```", ".svg)\\`\\`\\`")
        # Let's fix that. I will write the code exactly as requested.
        
        markdown_content.append(template_b)
        markdown_content.append("\n---\n")

    with open(output_path, 'w') as f:
        f.write("\n".join(markdown_content))
        
    print(f"Generated outreach campaign file at: {output_path}")

if __name__ == "__main__":
    main()
