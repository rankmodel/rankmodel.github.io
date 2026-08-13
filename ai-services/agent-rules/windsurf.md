# Windsurf / Cascade Agent Guidelines for ModelRank

## Memory & MCP Integration
- Configuration: `.windsurfrules` -> Imports `ai-services/ponytail/rules.md`
- Context Database: `ai-services/data/memory.db`

## Best Practices
- Verify tests pass with `pytest tests/`.
- Respect active locks in `file_locks` table.
- Broadcast important refactors to the `architecture` channel.
