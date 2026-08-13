#!/usr/bin/env bash
# run.sh - Starts AI services on demand
cd "$(dirname "$0")"

SERVICE=$1
shift

if [ -z "$SERVICE" ]; then
    echo "Usage: ./run.sh <service_name|command> [args...]"
    echo "Available commands:"
    echo "  - status       Show Context DB metrics and active locks"
    echo "  - watch        Start continuous codebase watcher daemon"
    echo "  - mcp          Run JSON-RPC MCP server over stdio"
    echo "  - search <q>   Fast FTS5 search across codebase"
    echo "  - symbol <s>   Lookup AST symbol info"
    echo "  - feed         View inter-agent message feed"
    echo "  - broadcast    Broadcast message to all agents"
    echo "  - memories     View architectural decisions"
    exit 1
fi

if [ "$SERVICE" = "mcp" ]; then
    exec python3 codebase-memory-mcp/server.py
elif [ "$SERVICE" = "watch" ]; then
    exec python3 monitor.py "$@"
else
    exec python3 agent_cli.py "$SERVICE" "$@"
fi
