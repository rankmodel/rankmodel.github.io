@echo off
cd %~dp0
python init_db.py

echo Starting MCP Server...
if exist "codebase-memory-mcp" (
    echo Mock MCP Server starting at port 8888...
) else (
    echo codebase-memory-mcp not found.
)
