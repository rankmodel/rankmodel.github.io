#!/usr/bin/env python3
"""
ModelRank Codebase Memory & Multi-Agent MCP Server
Implements standard JSON-RPC 2.0 Model Context Protocol over stdio for:
- Cursor
- Windsurf
- Claude Desktop
- Cline
- Antigravity / Gemini CLI
"""
import sys
import os
import json
import logging
from typing import Dict, Any, List, Optional

# Set up paths
SERVICE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

from context_engine import get_context_db

# Configure stderr logging so stdout is exclusively JSON-RPC
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mcp_server")

db = get_context_db()

TOOLS = [
    {
        "name": "search_codebase",
        "description": "Fast sub-millisecond full-text and semantic search across all codebase files, AST symbols (classes, functions, endpoints), docstrings, and summaries.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keywords or symbol name (e.g. 'compute_composite_score', 'leaderboard', 'HFDataFetcher', 'weights')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default 10)",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_file_context",
        "description": "Retrieves comprehensive architectural and AST context for a file: defined symbols, imported modules, calling dependencies, line counts, and active file locks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative file path (e.g. 'scoring/engine.py', 'data/fetcher.py', 'scripts/generate_static_assets.py')"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "get_symbol_info",
        "description": "Looks up exact definitions, signatures, line numbers, docstrings, and complexity for a function, class, or method.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol_name": {
                    "type": "string",
                    "description": "Name of the symbol (e.g. 'compute_composite_score', 'HFDataFetcher', 'ModelCache')"
                }
            },
            "required": ["symbol_name"]
        }
    },
    {
        "name": "send_agent_message",
        "description": "Broadcasts or sends a direct message to other AI agents (Cursor, Windsurf, Claude, Antigravity) across the inter-agent communication bus.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sender": {
                    "type": "string",
                    "description": "Your agent identifier (e.g. 'cursor', 'windsurf', 'claude', 'antigravity')"
                },
                "recipient": {
                    "type": "string",
                    "description": "Recipient agent ID or 'all' for broadcast",
                    "default": "all"
                },
                "channel": {
                    "type": "string",
                    "description": "Channel/topic ('general', 'ongoing-edits', 'architecture', 'locks', 'review', 'tasks')",
                    "default": "general"
                },
                "message_type": {
                    "type": "string",
                    "description": "Type of message ('broadcast', 'edit_alert', 'query', 'response', 'task_handoff', 'lock_request', 'decision')",
                    "default": "broadcast"
                },
                "subject": {
                    "type": "string",
                    "description": "Brief title or summary of message"
                },
                "content": {
                    "type": "string",
                    "description": "Detailed message text"
                },
                "payload": {
                    "type": "object",
                    "description": "Optional structured data (e.g. diffs, affected file list, line ranges)"
                }
            },
            "required": ["sender", "subject", "content"]
        }
    },
    {
        "name": "read_agent_messages",
        "description": "Retrieves recent messages from the inter-agent bus to see what other agents have announced, requested, or modified.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Your agent identifier to filter messages for you or broadcasts",
                    "default": "all"
                },
                "channel": {
                    "type": "string",
                    "description": "Optional channel filter ('ongoing-edits', 'architecture', 'locks', 'review')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of messages to retrieve (default 20)",
                    "default": 20
                },
                "since_id": {
                    "type": "integer",
                    "description": "Optional message ID offset to only fetch newer messages"
                }
            }
        }
    },
    {
        "name": "acquire_file_lock",
        "description": "Acquires an exclusive soft-lock on a file before making major edits, preventing collisions with other agents. Locks auto-expire after 5 minutes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative file path to lock"
                },
                "agent_id": {
                    "type": "string",
                    "description": "Your agent identifier"
                },
                "purpose": {
                    "type": "string",
                    "description": "Reason for editing / locking this file"
                },
                "ttl_seconds": {
                    "type": "integer",
                    "description": "Lock duration in seconds (default 300)",
                    "default": 300
                }
            },
            "required": ["file_path", "agent_id", "purpose"]
        }
    },
    {
        "name": "release_file_lock",
        "description": "Releases a file lock after editing is finished.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative file path"
                },
                "agent_id": {
                    "type": "string",
                    "description": "Your agent identifier"
                }
            },
            "required": ["file_path", "agent_id"]
        }
    },
    {
        "name": "record_codebase_memory",
        "description": "Records persistent architectural decisions, conventions, pitfalls, or insights into the shared Context DB.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["architecture_decision", "convention", "pitfall", "user_preference", "todo", "insight"],
                    "description": "Category of memory"
                },
                "title": {
                    "type": "string",
                    "description": "Short summary title"
                },
                "content": {
                    "type": "string",
                    "description": "Full explanation and context"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keyword tags"
                },
                "created_by": {
                    "type": "string",
                    "description": "Your agent identifier",
                    "default": "agent"
                }
            },
            "required": ["category", "title", "content"]
        }
    },
    {
        "name": "get_codebase_memories",
        "description": "Queries the shared architectural memory bank, ADRs, conventions, and design decisions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Optional category filter ('architecture_decision', 'convention', 'pitfall', 'insight')"
                },
                "query": {
                    "type": "string",
                    "description": "Optional search term"
                },
                "limit": {
                    "type": "integer",
                    "default": 15
                }
            }
        }
    },
    {
        "name": "get_recent_changes",
        "description": "Retrieves the real-time audit log of file creations, edits, and deletions across the workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 20
                }
            }
        }
    },
    {
        "name": "get_active_agents",
        "description": "Inspects active agent sessions, currently edited files, and active locks.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]

def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {"listChanged": False},
            "resources": {},
            "prompts": {}
        },
        "serverInfo": {
            "name": "modelrank-codebase-memory",
            "version": "2.0.0"
        }
    }

def handle_tools_list() -> Dict[str, Any]:
    return {"tools": TOOLS}

def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if name == "search_codebase":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 10)
            res = db.search_codebase(query, limit=limit)
            return {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}

        elif name == "get_file_context":
            fp = arguments.get("file_path", "")
            res = db.get_file_context(fp)
            if not res:
                return {"content": [{"type": "text", "text": f"File '{fp}' not found in Context DB."}], "isError": True}
            return {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}

        elif name == "get_symbol_info":
            sym = arguments.get("symbol_name", "")
            res = db.get_symbol_info(sym)
            return {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}

        elif name == "send_agent_message":
            msg_id = db.send_message(
                sender=arguments.get("sender", "agent"),
                recipient=arguments.get("recipient", "all"),
                channel=arguments.get("channel", "general"),
                message_type=arguments.get("message_type", "broadcast"),
                subject=arguments.get("subject", ""),
                content=arguments.get("content", ""),
                payload=arguments.get("payload")
            )
            return {"content": [{"type": "text", "text": f"Message [{msg_id}] sent successfully."}]}

        elif name == "read_agent_messages":
            msgs = db.get_messages(
                agent_id=arguments.get("agent_id", "all"),
                channel=arguments.get("channel"),
                limit=arguments.get("limit", 20),
                since_id=arguments.get("since_id")
            )
            return {"content": [{"type": "text", "text": json.dumps(msgs, indent=2)}]}

        elif name == "acquire_file_lock":
            acquired, existing = db.acquire_lock(
                file_path=arguments.get("file_path", ""),
                agent_id=arguments.get("agent_id", "agent"),
                purpose=arguments.get("purpose", "editing"),
                ttl_seconds=arguments.get("ttl_seconds", 300)
            )
            if acquired:
                return {"content": [{"type": "text", "text": f"Lock acquired on {arguments.get('file_path')}."}]}
            else:
                return {
                    "content": [{"type": "text", "text": f"File is currently locked by {existing.get('locked_by_agent')} until {existing.get('expires_at')} for: {existing.get('purpose')}"}],
                    "isError": True
                }

        elif name == "release_file_lock":
            rel = db.release_lock(arguments.get("file_path", ""), arguments.get("agent_id", ""))
            return {"content": [{"type": "text", "text": "Lock released." if rel else "Lock was not held or already expired."}]}

        elif name == "record_codebase_memory":
            m_id = db.record_memory(
                category=arguments.get("category", "insight"),
                title=arguments.get("title", ""),
                content=arguments.get("content", ""),
                tags=arguments.get("tags", []),
                created_by=arguments.get("created_by", "agent")
            )
            return {"content": [{"type": "text", "text": f"Memory [{m_id}] recorded successfully."}]}

        elif name == "get_codebase_memories":
            mems = db.get_memories(
                category=arguments.get("category"),
                query=arguments.get("query"),
                limit=arguments.get("limit", 15)
            )
            return {"content": [{"type": "text", "text": json.dumps(mems, indent=2)}]}

        elif name == "get_recent_changes":
            changes = db.get_recent_changes(limit=arguments.get("limit", 20))
            return {"content": [{"type": "text", "text": json.dumps(changes, indent=2)}]}

        elif name == "get_active_agents":
            agents = db.get_active_agents()
            locks = db.get_active_locks()
            stats = db.get_stats()
            return {"content": [{"type": "text", "text": json.dumps({"active_agents": agents, "active_locks": locks, "stats": stats}, indent=2)}]}

        else:
            return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True}

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}

def run_server():
    logger.info("Starting ModelRank Codebase Memory MCP Server...")
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "initialize":
                resp_result = handle_initialize(params)
            elif method == "tools/list":
                resp_result = handle_tools_list()
            elif method == "tools/call":
                resp_result = handle_tool_call(params.get("name", ""), params.get("arguments", {}))
            elif method == "ping":
                resp_result = {}
            elif method.startswith("notifications/"):
                continue # Ignore one-way notifications
            else:
                resp_result = None

            if req_id is not None:
                if resp_result is not None:
                    response = {"jsonrpc": "2.0", "id": req_id, "result": resp_result}
                else:
                    response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method {method} not found"}}
                
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

        except Exception as e:
            logger.error(f"Server loop error: {e}", exc_info=True)

if __name__ == '__main__':
    run_server()
