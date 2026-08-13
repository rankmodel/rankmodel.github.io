#!/bin/bash
cd "$(dirname "$0")"

echo "Configuring AI Agent Environments..."
BASE_DIR="$(pwd)"

# 1. Claude Desktop
OS=$(uname)
if [ "$OS" = "Darwin" ]; then
    CLAUDE_DIR="$HOME/Library/Application Support/Claude"
elif [ "$OS" = "Linux" ]; then
    CLAUDE_DIR="$HOME/.config/Claude"
else
    CLAUDE_DIR="$HOME/AppData/Roaming/Claude"
fi

mkdir -p "$CLAUDE_DIR"
CLAUDE_CONF="$CLAUDE_DIR/claude_desktop_config.json"
if [ ! -f "$CLAUDE_CONF" ]; then
    echo '{"mcpServers": {}}' > "$CLAUDE_CONF"
fi
# Simple merge strategy: append .new if it exists, since jq might not be available
echo "Generating Claude MCP config to $CLAUDE_CONF.new"
cat > "$CLAUDE_CONF.new" << EOF
{
  "mcpServers": {
    "codebase-memory": {
      "command": "python",
      "args": ["$BASE_DIR/codebase-memory-mcp/server.py"]
    }
  }
}
EOF

# 2. Cursor
CURSOR_CONF="../.cursorrules"
if [ ! -f "$CURSOR_CONF" ]; then
    echo "Importing ponytail rules & DB config for Cursor..."
    cat > "$CURSOR_CONF" << EOF
# Cursor Rules
IMPORT "$BASE_DIR/ponytail/rules.md"
MCP_SERVER_DB "$BASE_DIR/data/memory.db"
EOF
else
    echo "Cursor config already exists. Skipping."
fi

# 3. Windsurf
WINDSURF_CONF="../.windsurfrules"
if [ ! -f "$WINDSURF_CONF" ]; then
    echo "Importing ponytail rules & DB config for Windsurf..."
    cat > "$WINDSURF_CONF" << EOF
# Windsurf Rules
IMPORT "$BASE_DIR/ponytail/rules.md"
MCP_SERVER_DB "$BASE_DIR/data/memory.db"
EOF
else
    echo "Windsurf config already exists. Skipping."
fi

# 4. Cline
CLINE_DIR="../.vscode"
mkdir -p "$CLINE_DIR"
CLINE_CONF="$CLINE_DIR/cline_mcp.json"
if [ ! -f "$CLINE_CONF" ]; then
    echo "Generating Cline config..."
    cat > "$CLINE_CONF" << EOF
{
  "mcpServers": {
    "memory": {
      "command": "python",
      "args": ["$BASE_DIR/codebase-memory-mcp/server.py"]
    }
  }
}
EOF
else
    echo "Cline config already exists. Skipping."
fi

# 5. Generic
GENERIC_CONF="gemini-context.json"
if [ ! -f "$GENERIC_CONF" ]; then
    echo "Generating Generic Gemini config..."
    cat > "$GENERIC_CONF" << EOF
{
  "system_instructions": "You are connected to a codebase memory graph.",
  "endpoint": "$BASE_DIR/data/memory.db"
}
EOF
else
    echo "Generic config already exists. Skipping."
fi

echo "Done!"
