# ModelRank Multi-Agent Context DB & Collaboration Guide

## Overview
ModelRank features an automated, real-time, 100x high-performance Context DB located at `ai-services/data/memory.db`. It provides continuous codebase indexing, AST symbol extraction, dependency graph construction, sub-millisecond FTS5 search, inter-agent messaging bus, presence tracking, distributed file locking, and persistent architectural memory (ADRs).

## Key Components

### 1. Context Engine (`ai-services/context_engine.py`)
- **AST Parser**: Extracts classes, functions, methods, docstrings, signatures, and cyclomatic complexity across Python files.
- **Dependency Graph**: Constructs `imports`, `calls`, and `inherits` relationships.
- **FTS5 Search**: Instant full-text search with BM25 ranking and keyword highlighting.
- **Inter-Agent Message Bus**: Pub/sub messaging across channels (`ongoing-edits`, `architecture`, `locks`, `review`, `tasks`).
- **Distributed File Locks**: Soft-locking with automatic expiration (TTL) to prevent race conditions during concurrent multi-agent editing.

### 2. Continuous Codebase Monitor (`ai-services/monitor.py`)
- Background daemon that polls the workspace for file creations, modifications, and deletions.
- Instantly indexes changed files, updates AST symbols, logs to `change_events`, and broadcasts alerts to the `ongoing-edits` channel.

### 3. Model Context Protocol Server (`ai-services/codebase-memory-mcp/server.py`)
- Standard JSON-RPC 2.0 stdio server providing MCP tools to Cursor, Windsurf, Claude Desktop, Cline, and Antigravity.

### 4. Agent CLI (`ai-services/agent_cli.py`)
- Fast terminal interface for developers and agents to inspect stats, query symbols, lock files, search code, and broadcast updates.

## Quick CLI Commands
```bash
# Check system status, active locks, and agents
python3 ai-services/agent_cli.py status

# Sub-millisecond code search
python3 ai-services/agent_cli.py search "composite score"

# Inspect AST symbol info
python3 ai-services/agent_cli.py symbol compute_composite_score

# View inter-agent message feed
python3 ai-services/agent_cli.py feed -v

# Broadcast a message to all agents
python3 ai-services/agent_cli.py broadcast "Refactored scoring weights" --channel architecture

# Start continuous monitor daemon
python3 ai-services/monitor.py --interval 2.0
```
