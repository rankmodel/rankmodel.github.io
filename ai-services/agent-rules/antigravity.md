# Antigravity Agent Guidelines for ModelRank

You are Antigravity, the Google DeepMind agentic coding assistant working on ModelRank.

## Context DB & MCP Integration
- Database Location: `/Users/shrey/Downloads/modelrank/ai-services/data/memory.db`
- MCP Server: `/Users/shrey/Downloads/modelrank/ai-services/codebase-memory-mcp/server.py`
- Python SDK: `ai_services.context_engine.get_context_db()`

## Coordination Protocol
1. **Check Ongoing Edits**: Query recent messages from the `ongoing-edits` channel before modifying core files.
2. **Locking**: When modifying shared components (e.g. `scoring/engine.py`, `scripts/generate_static_assets.py`), acquire a soft lock via `acquire_lock` and release it when done.
3. **Record Decisions**: Whenever implementing architectural enhancements, record an ADR with `record_memory(category='architecture_decision', title=..., content=...)`.
4. **Monitoring**: The background daemon `ai-services/monitor.py` continuously indexes ongoing changes and publishes them to the message bus.
