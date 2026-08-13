#!/bin/bash
cd "$(dirname "$0")"
python3 init_db.py
python3 seed_memory.py

echo "Starting ModelRank Multi-Agent Services..."
if [ "$1" = "watch" ]; then
    exec python3 monitor.py --interval 2.0
elif [ "$1" = "mcp" ]; then
    exec python3 codebase-memory-mcp/server.py
else
    echo "Usage: ./start.sh [watch|mcp]"
    python3 agent_cli.py status
fi
