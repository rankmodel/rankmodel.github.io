"""
ModelRank Context DB & Multi-Agent Collaboration Engine
Database Schema & Initialization
"""
import sqlite3
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("context_db_init")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'memory.db')

SCHEMA_SQL = """
-- Enable WAL mode for high concurrency
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

-- 1. Prompts & Templates
CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category TEXT DEFAULT 'general',
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Codebase Files Registry
CREATE TABLE IF NOT EXISTS codebase_files (
    path TEXT PRIMARY KEY,
    file_hash TEXT NOT NULL,
    language TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    lines_count INTEGER NOT NULL,
    token_estimate INTEGER DEFAULT 0,
    ast_summary TEXT, -- JSON structure of symbols, imports, exports
    summary TEXT,     -- High-level semantic summary of file purpose
    last_modified DATETIME NOT NULL,
    indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. Codebase Symbols (AST nodes: classes, functions, methods, routes, endpoints)
CREATE TABLE IF NOT EXISTS codebase_symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    symbol_name TEXT NOT NULL,
    symbol_type TEXT NOT NULL, -- 'function', 'class', 'method', 'endpoint', 'variable', 'table'
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    signature TEXT,
    docstring TEXT,
    dependencies TEXT, -- JSON array of called functions or imported modules
    complexity INTEGER DEFAULT 1,
    FOREIGN KEY (file_path) REFERENCES codebase_files(path) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_symbols_name ON codebase_symbols(symbol_name);
CREATE INDEX IF NOT EXISTS idx_symbols_file ON codebase_symbols(file_path);
CREATE INDEX IF NOT EXISTS idx_symbols_type ON codebase_symbols(symbol_type);

-- 4. Knowledge & Dependency Graph (Nodes & Edges)
CREATE TABLE IF NOT EXISTS graph_nodes (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL, -- 'file', 'symbol', 'module', 'architecture_component', 'agent'
    data TEXT -- JSON attributes
);

CREATE TABLE IF NOT EXISTS graph_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    edge_type TEXT NOT NULL, -- 'imports', 'calls', 'inherits', 'modifies', 'depends_on', 'defines'
    weight REAL DEFAULT 1.0,
    metadata TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, target_id, edge_type)
);

CREATE INDEX IF NOT EXISTS idx_edges_source ON graph_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON graph_edges(target_id);

-- 5. Inter-Agent Message Bus & Pub/Sub Channel
CREATE TABLE IF NOT EXISTS agent_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_agent TEXT NOT NULL,
    recipient_agent TEXT DEFAULT 'all', -- 'all' for broadcast or specific agent ID
    channel TEXT DEFAULT 'general',    -- 'general', 'ongoing-edits', 'architecture', 'locks', 'review', 'tasks'
    message_type TEXT NOT NULL,         -- 'broadcast', 'edit_alert', 'query', 'response', 'task_handoff', 'lock_request', 'decision'
    subject TEXT NOT NULL,
    content TEXT NOT NULL,
    payload TEXT,                      -- JSON with file_paths, line ranges, diffs, code snippets
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    read_by TEXT DEFAULT '[]'          -- JSON array of agent IDs that acknowledged
);

CREATE INDEX IF NOT EXISTS idx_messages_recipient ON agent_messages(recipient_agent);
CREATE INDEX IF NOT EXISTS idx_messages_channel ON agent_messages(channel);
CREATE INDEX IF NOT EXISTS idx_messages_created ON agent_messages(created_at);

-- 6. Agent Presence & Active Sessions
CREATE TABLE IF NOT EXISTS agent_sessions (
    agent_id TEXT PRIMARY KEY,
    client_type TEXT NOT NULL, -- 'antigravity', 'cursor', 'windsurf', 'claude', 'cline', 'gemini', 'cli'
    current_task TEXT,
    active_files TEXT DEFAULT '[]', -- JSON array of file paths currently being viewed/edited
    status TEXT DEFAULT 'active',   -- 'active', 'idle', 'editing', 'planning'
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_heartbeat DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 7. Distributed File Locks (Concurrency & Collision Protection)
CREATE TABLE IF NOT EXISTS file_locks (
    file_path TEXT PRIMARY KEY,
    locked_by_agent TEXT NOT NULL,
    purpose TEXT NOT NULL,
    acquired_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL
);

-- 8. Long-term Agent Memory & Architectural Decisions (ADR)
CREATE TABLE IF NOT EXISTS agent_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL, -- 'architecture_decision', 'convention', 'pitfall', 'user_preference', 'todo', 'insight'
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT DEFAULT '[]', -- JSON array
    created_by TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_memories_cat ON agent_memories(category);

-- 9. Real-time File Change Events / Audit Trail
CREATE TABLE IF NOT EXISTS change_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    change_type TEXT NOT NULL, -- 'created', 'modified', 'deleted'
    diff_summary TEXT,
    author_agent TEXT DEFAULT 'unknown',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 10. Multi-Agent Tasks & Backlog
CREATE TABLE IF NOT EXISTS shared_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    assigned_to TEXT,
    status TEXT DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'blocked'
    priority INTEGER DEFAULT 2,    -- 1: high, 2: medium, 3: low
    dependencies TEXT DEFAULT '[]',-- JSON array of task IDs
    created_by TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);

-- 11. Full-Text Search (FTS5) for Sub-millisecond Codebase Knowledge Retrieval
CREATE VIRTUAL TABLE IF NOT EXISTS fts_codebase USING fts5(
    file_path,
    symbol_name,
    docstring,
    summary,
    content,
    tokenize = 'porter unicode61'
);
"""

def init_db(db_path=DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executescript(SCHEMA_SQL)

    # Migrations for existing tables if created by earlier versions
    try:
        cursor.execute("ALTER TABLE prompts ADD COLUMN category TEXT DEFAULT 'general'")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE prompts ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE prompts ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
    logger.info(f"Context DB successfully initialized at: {db_path}")

if __name__ == '__main__':
    init_db()
