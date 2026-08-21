#!/usr/bin/env python3
"""
ModelRank — GitHub Discussions Bootstrap Script
================================================
Creates the 3 pinned community discussion topics via the GitHub GraphQL API.

Requirements:
  - GitHub Personal Access Token with `write:discussion` scope
  - pip install requests

Usage:
  export GITHUB_TOKEN=your_pat_here
  python scripts/setup_discussions.py

  # Or pass token directly:
  python scripts/setup_discussions.py --token ghp_...
"""

import argparse
import os
import sys
from typing import Optional

try:
    import requests
except ImportError:
    print("ERROR: 'requests' is not installed. Run: pip install requests")
    sys.exit(1)

REPO_OWNER = "rankmodel"
REPO_NAME = "rankmodel.github.io"
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

# ────────────────────────────────────────────────────────────────────────────
# Discussion content
# ────────────────────────────────────────────────────────────────────────────

DISCUSSIONS: list[dict[str, str]] = [
    {
        "title": "[VOTE] Should we increase the Efficiency weight from 5% → 15%?",
        "body": """\
## Weight Vote: Efficiency Dimension 📊

Right now, ModelRank weights **Efficiency** at **5%** of the composite score.

Efficiency is defined as `composite_benchmark_score / log(params_billions + 1)` — it rewards small models that punch above their weight.

---

### The argument for increasing to 15%
- In 2026, running costs matter as much as raw quality
- A 7B model scoring 85 is more *useful* for 99% of use cases than a 70B model scoring 87
- Small models are the future of local AI

### The argument for keeping at 5%
- Benchmark performance is the most objective signal; it should stay dominant
- Raising efficiency could unfairly penalize large models built for complex tasks

---

## 🗳️ Vote in the comments

Reply with one of:
- 👍 **Keep at 5%** — benchmarks should stay primary
- 🚀 **Increase to 15%** — efficiency matters more than we're reflecting
- ❤️ **Something else** — comment with your preferred weight and rationale

**We will implement the community's decision in the next scoring update.** This is YOUR leaderboard.

The vote closes in 7 days. Current tally will be pinned as a comment.
""",
    },
    {
        "title": "Missing Models 🤖 — What should we rank next?",
        "body": """\
## Help Us Grow the Leaderboard

We currently rank **954+ open-weight models**, but we know we're missing some good ones.

**Drop a comment with the model(s) you want ranked:**

```
Model: org/model-name
Why: [one sentence — what makes it interesting?]
Known benchmarks: [optional — any MMLU-Pro / GPQA scores you have]
```

---

### How we prioritize

The model with the most 👍 reactions on its comment gets ranked first. We aim to index new submissions within **24 hours of verification**.

### What qualifies?
- Must be on HuggingFace (we pull benchmark data from HF's Open LLM Leaderboard + evals)
- Must be open-weight (not API-only)
- Any parameter size, any architecture

---

### Already ranked
See the full list at [rankmodel.github.io](https://rankmodel.github.io).

### Want to submit programmatically?
```bash
# Install the badge (creates a backlink, which triggers indexing)
# Paste this in your model card README:
![ModelRank Score](https://rankmodel.github.io/badges/your-org/your-model/score.svg)
```

Every badge install notifies us. It's the fastest way to get ranked.
""",
    },
    {
        "title": "[DEBATE] Is 10x cost worth it for a 5% accuracy improvement? 🔥",
        "body": """\
## The Great AI Cost Debate

Here's the data point that started ModelRank:

| Model | Cost/1M tokens | ModelRank Score | Tier |
|-------|---------------|----------------|------|
| Mistral-7B | ~$0.004 | 78 | B |
| Llama 3.1 8B | ~$0.006 | 80 | A |
| GPT-4o | ~$0.10 | 91 | S |
| Claude 3.5 Sonnet | ~$0.15 | 93 | S |

*GPT-4o costs 25× more than Mistral-7B for a 13-point score difference.*

---

### The question

**For your specific use case, when is the 25× cost premium worth it?**

I'll start with my own breakdown:

| Task | Worth premium? | Why |
|------|---------------|-----|
| Complex multi-step reasoning | ✅ Yes | Frontier models are genuinely better |
| Summarization | ❌ No | 7B class handles it at 95% quality |
| Simple Q&A / RAG | ❌ No | Speed + cost wins |
| Code generation | ⚠️ Depends | Qwen-Coder/DeepSeek-Coder are surprisingly competitive |
| Long document analysis | ✅ Yes | Context window + coherence matters |
| Creative writing | 🤷 Subjective | Preference-based, community signals matter |

---

## What's your experience?

- Where have you been **burned by over-paying** for a model?
- Where has a **cheap model surprised you**?
- What's your rule of thumb for model selection?

Fire away. No wrong answers. This is the debate that needs to happen.
""",
    },
]


# ────────────────────────────────────────────────────────────────────────────
# GraphQL helpers
# ────────────────────────────────────────────────────────────────────────────

def graphql(query: str, variables: dict, token: str) -> dict:
    """Execute a GitHub GraphQL query and return the response data."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        GITHUB_GRAPHQL_URL,
        json={"query": query, "variables": variables},
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if "errors" in data:
        errors = "\n".join(e.get("message", str(e)) for e in data["errors"])
        raise RuntimeError(f"GitHub GraphQL error:\n{errors}")
    return data["data"]


def get_repo_id(token: str) -> str:
    """Fetch the node ID of the repository."""
    query = """
    query GetRepo($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        id
        discussionCategories(first: 10) {
          nodes { id name }
        }
      }
    }
    """
    data = graphql(query, {"owner": REPO_OWNER, "name": REPO_NAME}, token)
    repo = data["repository"]
    categories = repo["discussionCategories"]["nodes"]
    print(f"  Repo ID: {repo['id']}")
    print(f"  Available discussion categories:")
    for cat in categories:
        print(f"    [{cat['id']}] {cat['name']}")
    # Prefer "General" category, fall back to first available
    general = next((c for c in categories if c["name"] == "General"), categories[0] if categories else None)
    if general is None:
        raise RuntimeError(
            "No discussion categories found. Enable Discussions in your repo settings first."
        )
    print(f"  Using category: {general['name']} ({general['id']})")
    return repo["id"], general["id"]


def create_discussion(
    repo_id: str, category_id: str, title: str, body: str, token: str
) -> str:
    """Create a single discussion and return its URL."""
    mutation = """
    mutation CreateDiscussion($repoId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
      createDiscussion(input: {
        repositoryId: $repoId,
        categoryId: $categoryId,
        title: $title,
        body: $body
      }) {
        discussion {
          id
          url
          number
        }
      }
    }
    """
    data = graphql(
        mutation,
        {
            "repoId": repo_id,
            "categoryId": category_id,
            "title": title,
            "body": body,
        },
        token,
    )
    return data["createDiscussion"]["discussion"]


# ────────────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bootstrap ModelRank GitHub Discussions with 3 pinned community topics."
    )
    parser.add_argument(
        "--token",
        default=os.getenv("GITHUB_TOKEN"),
        help="GitHub Personal Access Token (or set GITHUB_TOKEN env var)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be created without making API calls",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("=== DRY RUN MODE — No API calls will be made ===\n")
        for i, disc in enumerate(DISCUSSIONS, 1):
            print(f"Discussion {i}: {disc['title']}")
            print(f"Body preview: {disc['body'][:200]}...")
            print()
        return

    if not args.token:
        print(
            "ERROR: GitHub token required.\n"
            "  Set GITHUB_TOKEN env var or use --token flag.\n"
            "  Token needs 'write:discussion' scope."
        )
        sys.exit(1)

    print(f"\n🚀 Setting up GitHub Discussions for {REPO_OWNER}/{REPO_NAME}\n")

    try:
        print("Fetching repository info...")
        repo_id, category_id = get_repo_id(args.token)
    except requests.HTTPError as e:
        print(f"ERROR: HTTP {e.response.status_code} — check your token permissions.")
        sys.exit(1)
    except RuntimeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    created: list[dict] = []

    for i, disc in enumerate(DISCUSSIONS, 1):
        print(f"\nCreating Discussion {i}/{len(DISCUSSIONS)}: {disc['title'][:60]}...")
        try:
            result = create_discussion(
                repo_id, category_id, disc["title"], disc["body"], args.token
            )
            created.append(result)
            print(f"  ✅ Created: {result['url']}")
        except RuntimeError as e:
            print(f"  ❌ Failed: {e}")
        except requests.HTTPError as e:
            print(f"  ❌ HTTP {e.response.status_code}: {e}")

    print(f"\n{'='*60}")
    print(f"✅ Created {len(created)}/{len(DISCUSSIONS)} discussions.")
    print("\n📌 Next steps:")
    print("  1. Visit each discussion URL above and pin it (requires repo admin)")
    print("  2. Lock the 'Weight Vote' discussion to prevent early gaming")
    print("  3. Add a welcoming first comment from the maintainer account")
    print("\nDiscussion URLs:")
    for d in created:
        print(f"  #{d['number']}: {d['url']}")


if __name__ == "__main__":
    main()
