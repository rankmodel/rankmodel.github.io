"""
ModelRank Architecture & Context Memory Seeder
Seeds long-term memory, ADRs, conventions, and inter-agent communication channels.
"""
import os
import sys
import json
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from context_engine import get_context_db

logger = logging.getLogger("seed_memory")
logging.basicConfig(level=logging.INFO)

MEMORIES = [
    {
        "category": "architecture_decision",
        "title": "ADR-001: 5-Dimensional Composite Scoring Engine",
        "content": (
            "ModelRank evaluates AI models across 5 calibrated dimensions:\n"
            "1. Benchmarks (40%): MMLU, GSM8K, HumanEval, ARC, HellaSwag, Chatbot Arena ELO\n"
            "2. Efficiency (20%): Parameter efficiency, quantization readiness (GGUF, AWQ, GPTQ), context window\n"
            "3. Community (20%): HF downloads, likes, trending rank, discussions\n"
            "4. Recency (10%): Exponential time decay based on release date\n"
            "5. Extended Metadata & Capability (10%): Context window length, license permissiveness, architecture\n\n"
            "Tier distribution: S-Tier (>=85), A-Tier (75-84.9), B-Tier (65-74.9), C-Tier (50-64.9), D-Tier (<50)."
        ),
        "tags": ["scoring", "algorithm", "weights", "tiers", "benchmarks"]
    },
    {
        "category": "architecture_decision",
        "title": "ADR-002: Dual Data Persistence Layer",
        "content": (
            "ModelRank uses SQLite for fast structured local storage (`data/modelrank.db`) with WAL mode, "
            "and static JSON dumps (`static_output/leaderboard.json`, `static_output/models/*.json`) for "
            "zero-cost GitHub Pages serverless CDN deployment. The Context DB (`ai-services/data/memory.db`) "
            "is separated to provide an independent, high-throughput inter-agent event bus and codebase knowledge graph."
        ),
        "tags": ["database", "sqlite", "caching", "cdn", "github-pages"]
    },
    {
        "category": "convention",
        "title": "CONV-001: Inter-Agent Concurrency & File Locking Protocol",
        "content": (
            "When multiple agents (Antigravity, Cursor, Windsurf, Claude, Cline) are operating on the repository:\n"
            "1. Before editing critical files (e.g. `scoring/engine.py`, `scripts/generate_static_assets.py`), "
            "agents should check or acquire a file lock via `ContextDB.acquire_lock()` or MCP `acquire_file_lock`.\n"
            "2. File locks auto-expire after 300 seconds (5 min) to prevent deadlocks.\n"
            "3. File edits are automatically detected and broadcasted to the `ongoing-edits` channel by `monitor.py`.\n"
            "4. Agents must announce breaking API changes or schema modifications to the `architecture` channel."
        ),
        "tags": ["agents", "concurrency", "locks", "communication", "protocol"]
    },
    {
        "category": "convention",
        "title": "CONV-002: Standalone Static Asset Generation",
        "content": (
            "`scripts/generate_static_assets.py` builds the complete GitHub Pages static distribution in `static_output/`.\n"
            "Pages include: `index.html` (interactive daisyUI/Tailwind leaderboard), `methodology.html`, `quiz.html`, "
            "`collections.html`, `pricing.html`, `sitemap.xml`, `robots.txt`, and badges (`static_output/badges/`).\n"
            "Always verify static build passes via `python scripts/generate_static_assets.py` after frontend edits."
        ),
        "tags": ["frontend", "static_output", "tailwind", "daisyui", "assets"]
    },
    {
        "category": "architecture_decision",
        "title": "ADR-003: NotebookLM Research Podcast Pipeline",
        "content": (
            "`data/notebooklm_integration.py` creates rich markdown briefing documents optimized for NotebookLM "
            "in `outputs/notebooklm_sources/`. If `notebooklm-py` is installed with browser automation, it triggers "
            "automated podcast generation. Otherwise, documents are exported ready for manual upload."
        ),
        "tags": ["notebooklm", "podcast", "briefings", "audio"]
    },
    {
        "category": "insight",
        "title": "INSIGHT-001: 100x Multi-Agent Context Acceleration",
        "content": (
            "The Context DB enables sub-millisecond FTS5 search across all 90+ codebase files and 220+ AST symbols. "
            "Agents can instantly look up function signatures, class inheritance, callers, and file summaries without "
            "wasting prompt tokens or doing slow file-by-file exploration."
        ),
        "tags": ["context", "fts5", "ast", "performance", "symbols"]
    }
]

PROMPTS = [
    {
        "name": "modelrank_agent_system",
        "category": "system",
        "content": (
            "You are a specialized AI Agent working on the ModelRank codebase. "
            "You have direct access to the Context DB (`ai-services/data/memory.db`) via MCP tools or Python SDK. "
            "Always check recent change alerts, respect file locks, maintain clean docstrings, and log major decisions."
        )
    },
    {
        "name": "modelrank_code_reviewer",
        "category": "review",
        "content": (
            "Review code changes for ModelRank: verify scoring weight normalization, check SQLite parameter binding "
            "safety, ensure Tailwind/daisyUI responsiveness without clunky styling, and verify all 27 unit tests pass."
        )
    }
]

def seed_memories():
    db = get_context_db()
    for mem in MEMORIES:
        m_id = db.record_memory(
            category=mem["category"],
            title=mem["title"],
            content=mem["content"],
            tags=mem["tags"],
            created_by="system-init"
        )
        logger.info(f"Seeded memory [{m_id}]: {mem['title']}")

    conn = db._get_conn()
    try:
        with conn:
            cur = conn.cursor()
            for p in PROMPTS:
                cur.execute("""
                    INSERT INTO prompts (name, category, content)
                    VALUES (?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        category = excluded.category,
                        content = excluded.content,
                        updated_at = datetime('now')
                """, (p["name"], p["category"], p["content"]))
                logger.info(f"Seeded prompt: {p['name']}")
    finally:
        conn.close()

    logger.info("Memory and prompts seeding complete!")

if __name__ == '__main__':
    seed_memories()
