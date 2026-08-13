#!/usr/bin/env bash
# run.sh
# Starts AI services on demand

SERVICE=$1

if [ -z "$SERVICE" ]; then
    echo "Usage: ./run.sh <service_name>"
    echo "Available services:"
    echo "  - ponytail"
    echo "  - notebooklm-py"
    echo "  - prompt-master"
    echo "  - codebase-memory-mcp"
    echo "  - caveman"
    echo "  - ai-specs"
    echo "  - guide"
    echo "  - agent-rules"
    echo "  - prompt-optimizer"
    echo "  - textgrad"
    echo "  - Trace"
    echo "  - awesome-ai-agents-2026"
    echo "  - junior-to-senior"
    echo "  - grill-me"
    echo "  - interface-kit"
    exit 1
fi

if [ -d "$SERVICE" ]; then
    echo "Starting $SERVICE..."
    # Mock startup script
    echo "$SERVICE is now running (mock)."
else
    echo "Service '$SERVICE' not found."
    exit 1
fi
