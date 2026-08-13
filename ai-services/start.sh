#!/bin/bash
cd "$(dirname "$0")"
python3 init_db.py

echo "Starting MCP Server..."
if [ -d "codebase-memory-mcp" ]; then
    echo "Mock MCP Server starting at port 8888..."
else
    echo "codebase-memory-mcp not found."
fi
