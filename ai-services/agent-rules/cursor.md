# Cursor Agent Guidelines for ModelRank

## Memory & MCP Integration
- Database: `/Users/shrey/Downloads/modelrank/ai-services/data/memory.db`
- Rules: Imported from `ai-services/ponytail/rules.md`

## Workflow
1. **Search Context**: Use `search_codebase` or `get_symbol_info` to pinpoint functions before writing edits.
2. **File Locks**: Acquire file locks prior to multi-file refactors.
3. **Notify Changes**: File saves will be detected automatically by `monitor.py` and broadcast to peer agents.
