# Cline / Roo-Code Agent Guidelines for ModelRank

## MCP Connection
- Config: `.vscode/cline_mcp.json`
- Server: `python ai-services/codebase-memory-mcp/server.py`

## Features
- Access to FTS5 symbol search across 90+ files.
- Soft file-locking for atomic changes.
- Direct messaging to peer agents on `ongoing-edits` channel.
