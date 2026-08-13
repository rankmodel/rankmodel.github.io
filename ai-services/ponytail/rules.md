# Ponytail Multi-Agent Coordination Rules for ModelRank

## 🌐 Context DB & Memory Engine
ModelRank is equipped with a 100x high-performance Context DB located at:
`/Users/shrey/Downloads/modelrank/ai-services/data/memory.db`

All agents (Cursor, Windsurf, Claude Desktop, Cline, Antigravity) are connected to this central knowledge hub and event bus via the Model Context Protocol (MCP) server `ai-services/codebase-memory-mcp/server.py` or the Python SDK `ai-services/context_engine.py`.

---

## 🔒 1. Concurrency & File Collision Protocol
To prevent duplicate work, overwrite hazards, or merge conflicts when multiple agents edit simultaneously:
- **Check Lock Status**: Query `active_locks` or call `acquire_file_lock(file_path, agent_id, purpose)` before modifying high-impact files (`scoring/engine.py`, `data/fetcher.py`, `scripts/generate_static_assets.py`, `api/server.py`).
- **Release Lock**: Call `release_file_lock(file_path, agent_id)` immediately upon completing your changes.
- **Lock TTL**: Default lock expiration is 300 seconds (5 minutes). Locks auto-expire safely.

---

## 📡 2. Inter-Agent Communication Channels
Use `send_agent_message` and `read_agent_messages` on the following channels:
- **`ongoing-edits`**: Real-time stream of file creations, modifications, and deletions (automatically tracked by `ai-services/monitor.py`).
- **`architecture`**: Broadcast architectural changes, database schema migrations, and design decisions (ADRs).
- **`review`**: Request peer agent review on complex logic or performance refactors.
- **`tasks`**: Assign, hand off, or claim multi-agent work items.

---

## 🧠 3. Codebase Knowledge & Symbol Lookup
Instead of blind searching across files:
- Use `search_codebase(query)` for instant FTS5 full-text & snippet searches.
- Use `get_symbol_info(symbol_name)` for AST signatures, line ranges, and complexity.
- Use `get_file_context(file_path)` to view dependencies, callers, symbols, and summaries.
- Use `get_codebase_memories(category)` to inspect ADRs, scoring weights, and design principles.

---

## 🚀 4. Core Architecture Invariants
- **Scoring Dimensions**: 5D composite scoring (Benchmark 40%, Efficiency 20%, Community 20%, Recency 10%, Extended 10%). Tiers: S (>=85), A (75-84.9), B (65-74.9), C (50-64.9), D (<50).
- **Test Integrity**: Always verify that all 27 unit tests pass via `pytest tests/` before completing tasks.
- **Static Asset Generation**: Frontend pages (`index.html`, `quiz.html`, `collections.html`, `pricing.html`, `methodology.html`) in `static_output/` must be kept in sync using `python scripts/generate_static_assets.py`.
- **Clean Logging & Documentation**: Preserve docstrings, use clean type hints, and record significant decisions with `record_codebase_memory`.
