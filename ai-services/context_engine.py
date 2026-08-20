"""
ModelRank Context DB & Multi-Agent Collaboration Engine
Core Python SDK for Agent Inter-Communication, Symbol Indexing, AST Extraction, and Real-Time Coordination.
"""
import os
import sys
import json
import ast
import time
import hashlib
import sqlite3
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("context_engine")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'memory.db')

IGNORE_DIRS = {
    '.git', '.pytest_cache', '__pycache__', 'venv', 'env', '.venv',
    'node_modules', '.idea', '.vscode', '.DS_Store', 'dist', 'build',
    'static_output/models', 'static_output/badges', 'outputs/notebooklm_sources',
    'models', 'badges'
}

IGNORE_EXTENSIONS = {
    '.pyc', '.pyo', '.pyd', '.db', '.sqlite', '.sqlite3', '.png', '.jpg',
    '.jpeg', '.gif', '.ico', '.svg', '.tar', '.gz', '.zip', '.bin', '.exe',
    '.woff', '.woff2', '.ttf', '.eot', '.pdf', '.map', '-wal', '-shm', '.lock'
}

import functools

def _ttl_cache(maxsize=128, ttl_seconds=60):
    def decorator(func):
        @functools.lru_cache(maxsize=maxsize)
        def _cached_func(*args, _ttl_hash=None, **kwargs):
            return func(*args, **kwargs)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _ttl_hash = int(time.time() / ttl_seconds)
            return _cached_func(*args, _ttl_hash=_ttl_hash, **kwargs)

        wrapper.cache_clear = _cached_func.cache_clear
        return wrapper
    return decorator

class ContextDB:
    """Unified interface for Multi-Agent Context, Codebase Knowledge Graph, and Real-Time Event Bus."""

    def __init__(self, db_path: str = DB_PATH, repo_root: str = REPO_ROOT):
        self.db_path = db_path
        self.repo_root = repo_root
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._ensure_init()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _ensure_init(self):
        try:
            from .init_db import init_db
        except (ImportError, ValueError):
            import sys
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from init_db import init_db
        init_db(self.db_path)

    def _invalidate_cache(self):
        type(self).get_symbol_info.cache_clear()
        type(self).get_file_context.cache_clear()

    # -------------------------------------------------------------------------
    # 1. FILE & SYMBOL INDEXING (AST + STRUCTURAL)
    # -------------------------------------------------------------------------

    def _compute_file_hash(self, filepath: str) -> str:
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def _parse_python_ast(self, content: str, rel_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        symbols = []
        edges = []
        summary_info = {"imports": [], "classes": [], "functions": [], "routes": []}

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {rel_path}: {e}")
            return symbols, edges, summary_info

        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    summary_info["imports"].append(alias.name)
                    edges.append({
                        "source": rel_path,
                        "target": alias.name,
                        "type": "imports",
                        "meta": {"line": node.lineno}
                    })
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    target_name = f"{mod}.{alias.name}" if mod else alias.name
                    summary_info["imports"].append(target_name)
                    edges.append({
                        "source": rel_path,
                        "target": target_name,
                        "type": "imports",
                        "meta": {"line": node.lineno}
                    })

        # Top level & nested classes/functions
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node) or ""
                bases = [ast.unparse(b) for b in node.bases] if hasattr(ast, 'unparse') else []
                summary_info["classes"].append(node.name)
                
                symbols.append({
                    "name": node.name,
                    "type": "class",
                    "line_start": node.lineno,
                    "line_end": getattr(node, 'end_lineno', node.lineno),
                    "signature": f"class {node.name}({', '.join(bases)})",
                    "docstring": doc.strip(),
                    "dependencies": bases,
                    "complexity": len(node.body)
                })

                for b in bases:
                    edges.append({
                        "source": f"{rel_path}:{node.name}",
                        "target": b,
                        "type": "inherits",
                        "meta": {}
                    })

                # Methods inside class
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        m_doc = ast.get_docstring(sub) or ""
                        args_list = [a.arg for a in sub.args.args]
                        sig = f"{sub.name}({', '.join(args_list)})"
                        symbols.append({
                            "name": f"{node.name}.{sub.name}",
                            "type": "method",
                            "line_start": sub.lineno,
                            "line_end": getattr(sub, 'end_lineno', sub.lineno),
                            "signature": sig,
                            "docstring": m_doc.strip(),
                            "dependencies": [],
                            "complexity": len(sub.body)
                        })

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node) or ""
                args_list = [a.arg for a in node.args.args]
                sig = f"{node.name}({', '.join(args_list)})"
                
                # Check for FastAPI / route decorators
                is_route = any('app.' in (ast.unparse(d) if hasattr(ast, 'unparse') else '') or 
                               'router.' in (ast.unparse(d) if hasattr(ast, 'unparse') else '') 
                               for d in node.decorator_list)
                sym_type = "endpoint" if is_route else "function"
                summary_info["functions"].append(node.name)

                symbols.append({
                    "name": node.name,
                    "type": sym_type,
                    "line_start": node.lineno,
                    "line_end": getattr(node, 'end_lineno', node.lineno),
                    "signature": sig,
                    "docstring": doc.strip(),
                    "dependencies": [],
                    "complexity": len(node.body)
                })

        return symbols, edges, summary_info

    def index_file(self, rel_path: str, author_agent: str = "system", broadcast_event: bool = True) -> bool:
        """Indexes a single file into the Context DB, extracting symbols and updating graph."""
        abs_path = os.path.join(self.repo_root, rel_path)
        if not os.path.exists(abs_path) or os.path.isdir(abs_path):
            return False

        # Check ignored path parts
        parts = rel_path.split(os.sep)
        for part in parts:
            if part in IGNORE_DIRS or (part.startswith('.') and part not in ('.cursorrules', '.windsurfrules', '.env.example', '.agents')):
                return False
        if 'static_output/models' in rel_path or 'static_output/badges' in rel_path or 'outputs/notebooklm_sources' in rel_path:
            return False

        ext = os.path.splitext(rel_path)[1].lower()
        if ext in IGNORE_EXTENSIONS:
            return False

        file_hash = self._compute_file_hash(abs_path)
        size_bytes = os.path.getsize(abs_path)
        mtime = datetime.fromtimestamp(os.path.getmtime(abs_path)).isoformat()

        try:
            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read file {rel_path}: {e}")
            return False

        lines = content.splitlines()
        lines_count = len(lines)
        token_estimate = max(1, len(content) // 4)

        symbols = []
        edges = []
        ast_summary = {}
        summary = ""

        # Language-specific extraction
        if ext == '.py':
            lang = 'python'
            symbols, edges, ast_summary = self._parse_python_ast(content, rel_path)
            func_names = ", ".join(ast_summary.get("functions", [])[:8])
            class_names = ", ".join(ast_summary.get("classes", [])[:5])
            summary = f"Python module containing classes: [{class_names}], functions: [{func_names}]"
        elif ext in ('.html', '.htm'):
            lang = 'html'
            summary = f"HTML UI template ({lines_count} lines)"
        elif ext in ('.js', '.ts', '.jsx', '.tsx'):
            lang = 'javascript'
            summary = f"JavaScript / TypeScript frontend script ({lines_count} lines)"
        elif ext == '.css':
            lang = 'css'
            summary = f"Stylesheet ({lines_count} lines)"
        elif ext in ('.md', '.markdown'):
            lang = 'markdown'
            first_line = lines[0] if lines else ""
            summary = f"Documentation: {first_line[:80]}"
        elif ext in ('.sql',):
            lang = 'sql'
            summary = f"Database schema or SQL migration ({lines_count} lines)"
        elif ext in ('.json', '.yaml', '.yml', '.toml'):
            lang = 'config'
            summary = f"Configuration / metadata file ({lines_count} lines)"
        else:
            lang = 'text'
            summary = f"Source file ({lines_count} lines)"

        conn = self._get_conn()
        try:
            with conn:
                # Check existing hash to avoid duplicate work
                cur = conn.cursor()
                cur.execute("SELECT file_hash FROM codebase_files WHERE path = ?", (rel_path,))
                row = cur.fetchone()
                prev_hash = row['file_hash'] if row else None

                is_new = prev_hash is None
                is_modified = prev_hash is not None and prev_hash != file_hash

                if not is_new and not is_modified:
                    return True # No changes

                # 1. Upsert codebase_files
                cur.execute("""
                    INSERT INTO codebase_files (path, file_hash, language, size_bytes, lines_count, token_estimate, ast_summary, summary, last_modified, indexed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    ON CONFLICT(path) DO UPDATE SET
                        file_hash = excluded.file_hash,
                        language = excluded.language,
                        size_bytes = excluded.size_bytes,
                        lines_count = excluded.lines_count,
                        token_estimate = excluded.token_estimate,
                        ast_summary = excluded.ast_summary,
                        summary = excluded.summary,
                        last_modified = excluded.last_modified,
                        indexed_at = datetime('now')
                """, (rel_path, file_hash, lang, size_bytes, lines_count, token_estimate, json.dumps(ast_summary), summary, mtime))

                # 2. Refresh symbols
                cur.execute("DELETE FROM codebase_symbols WHERE file_path = ?", (rel_path,))
                for s in symbols:
                    cur.execute("""
                        INSERT INTO codebase_symbols (file_path, symbol_name, symbol_type, line_start, line_end, signature, docstring, dependencies, complexity)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (rel_path, s["name"], s["type"], s["line_start"], s["line_end"], s.get("signature", ""), s.get("docstring", ""), json.dumps(s.get("dependencies", [])), s.get("complexity", 1)))

                # 3. Refresh graph edges
                cur.execute("DELETE FROM graph_edges WHERE source_id = ?", (rel_path,))
                for edge in edges:
                    cur.execute("""
                        INSERT OR IGNORE INTO graph_edges (source_id, target_id, edge_type, metadata)
                        VALUES (?, ?, ?, ?)
                    """, (edge["source"], edge["target"], edge["type"], json.dumps(edge.get("meta", {}))))

                # 4. Update FTS5 search index
                cur.execute("DELETE FROM fts_codebase WHERE file_path = ?", (rel_path,))
                cur.execute("""
                    INSERT INTO fts_codebase (file_path, symbol_name, docstring, summary, content)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    rel_path,
                    " ".join([s["name"] for s in symbols]),
                    " ".join([s.get("docstring", "") for s in symbols]),
                    summary,
                    content[:15000] # Cap search body snippet for efficiency
                ))

                # 5. Record change event if it was modified or created
                if (is_modified or is_new):
                    change_type = "created" if is_new else "modified"
                    diff_desc = f"{change_type.capitalize()} {rel_path} ({lines_count} lines, {len(symbols)} symbols)"
                    cur.execute("""
                        INSERT INTO change_events (file_path, change_type, diff_summary, author_agent)
                        VALUES (?, ?, ?, ?)
                    """, (rel_path, change_type, diff_desc, author_agent))

                    # 6. Publish real-time inter-agent event
                    if broadcast_event:
                        msg_content = self.render_prompt_template(
                            "edit_alert_content.txt",
                            rel_path=rel_path,
                            change_type=change_type,
                            lines_count=lines_count,
                            symbols_count=len(symbols)
                        ).strip()
                        cur.execute("""
                            INSERT INTO agent_messages (sender_agent, recipient_agent, channel, message_type, subject, content, payload)
                            VALUES (?, 'all', 'ongoing-edits', 'edit_alert', ?, ?, ?)
                        """, (
                            author_agent,
                            f"[FILE_{change_type.upper()}] {rel_path}",
                            msg_content,
                            json.dumps({"path": rel_path, "change_type": change_type, "symbols": [s["name"] for s in symbols]})
                        ))

            self._invalidate_cache()
            return True
        finally:
            conn.close()

    def remove_file(self, rel_path: str, author_agent: str = "system") -> bool:
        """Removes a deleted file from the Context DB and broadcasts removal event."""
        conn = self._get_conn()
        try:
            with conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM codebase_files WHERE path = ?", (rel_path,))
                cur.execute("DELETE FROM codebase_symbols WHERE file_path = ?", (rel_path,))
                cur.execute("DELETE FROM graph_edges WHERE source_id = ?", (rel_path,))
                cur.execute("DELETE FROM fts_codebase WHERE file_path = ?", (rel_path,))
                cur.execute("DELETE FROM file_locks WHERE file_path = ?", (rel_path,))
                
                cur.execute("""
                    INSERT INTO change_events (file_path, change_type, diff_summary, author_agent)
                    VALUES (?, 'deleted', 'File deleted', ?)
                """, (rel_path, author_agent))

                msg_content = self.render_prompt_template(
                    "edit_alert_deleted.txt",
                    rel_path=rel_path
                ).strip()
                cur.execute("""
                    INSERT INTO agent_messages (sender_agent, recipient_agent, channel, message_type, subject, content, payload)
                    VALUES (?, 'all', 'ongoing-edits', 'edit_alert', ?, ?, ?)
                """, (
                    author_agent,
                    f"[FILE_DELETED] {rel_path}",
                    msg_content,
                    json.dumps({"path": rel_path, "change_type": "deleted", "symbols": []})
                ))

            self._invalidate_cache()
            return True
        finally:
            conn.close()

    def reindex_all(self, author_agent: str = "indexer", broadcast_batch_summary: bool = True) -> Dict[str, int]:
        """Scans the whole codebase and indexes all eligible files."""
        indexed = 0
        skipped = 0
        total_files = 0

        # Clean stale files from DB that no longer exist
        conn = self._get_conn()
        try:
            with conn:
                cur = conn.cursor()
                cur.execute("SELECT path FROM codebase_files")
                for row in cur.fetchall():
                    p = row["path"]
                    abs_p = os.path.join(self.repo_root, p)
                    if not os.path.exists(abs_p) or 'static_output/models' in p or 'static_output/badges' in p or 'outputs/notebooklm_sources' in p:
                        cur.execute("DELETE FROM codebase_files WHERE path = ?", (p,))
                        cur.execute("DELETE FROM codebase_symbols WHERE file_path = ?", (p,))
                        cur.execute("DELETE FROM graph_edges WHERE source_id = ?", (p,))
                        cur.execute("DELETE FROM fts_codebase WHERE file_path = ?", (p,))
        finally:
            conn.close()

        for root, dirs, files in os.walk(self.repo_root):
            # Prune ignored directories
            dirs[:] = [
                d for d in dirs
                if d not in IGNORE_DIRS
                and not d.startswith('.')
                and not os.path.relpath(os.path.join(root, d), self.repo_root).startswith('static_output/models')
                and not os.path.relpath(os.path.join(root, d), self.repo_root).startswith('static_output/badges')
                and not os.path.relpath(os.path.join(root, d), self.repo_root).startswith('outputs/notebooklm_sources')
            ]
            
            for file in files:
                if file.startswith('.') and file not in ('.cursorrules', '.windsurfrules', '.env.example'):
                    continue
                ext = os.path.splitext(file)[1].lower()
                if ext in IGNORE_EXTENSIONS:
                    continue

                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, self.repo_root)

                total_files += 1
                if self.index_file(rel_path, author_agent=author_agent, broadcast_event=False):
                    indexed += 1
                else:
                    skipped += 1

        if broadcast_batch_summary:
            self.send_message(
                sender=author_agent,
                recipient="all",
                channel="ongoing-edits",
                message_type="broadcast",
                subject="[REINDEX_COMPLETE] Codebase Context DB fully synchronized",
                content=f"Synchronized {indexed} codebase files into Context DB with AST symbol mapping and dependency graph.",
                payload={"indexed": indexed, "skipped": skipped, "total": total_files}
            )

        logger.info(f"Reindex complete: {indexed} indexed, {skipped} skipped out of {total_files} total files.")
        return {"total": total_files, "indexed": indexed, "skipped": skipped}

    # -------------------------------------------------------------------------
    # 2. SEARCH & RETRIEVAL (FTS5 + SYMBOLS + GRAPH)
    # -------------------------------------------------------------------------

    def search_codebase(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Sub-millisecond full-text and semantic symbol search across entire codebase."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            # Clean query for FTS5 (escape special chars)
            clean_q = "".join(c if c.isalnum() or c.isspace() else " " for c in query).strip()
            if not clean_q:
                return []
            
            terms = clean_q.split()
            fts_query = " OR ".join(f'"{t}"*' for t in terms)

            cur.execute("""
                SELECT file_path, symbol_name, docstring, summary,
                       snippet(fts_codebase, 4, '<b>', '</b>', '...', 20) AS match_snippet,
                       rank
                FROM fts_codebase
                WHERE fts_codebase MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (fts_query, limit))

            results = []
            for row in cur.fetchall():
                results.append({
                    "file_path": row["file_path"],
                    "symbol_name": row["symbol_name"],
                    "summary": row["summary"],
                    "docstring": row["docstring"],
                    "snippet": row["match_snippet"],
                    "score": round(float(row["rank"]), 3)
                })
            return results
        except Exception as e:
            logger.error(f"FTS search error: {e}")
            # Fallback to LIKE query
            cur = conn.cursor()
            cur.execute("""
                SELECT path, summary, language, lines_count 
                FROM codebase_files 
                WHERE path LIKE ? OR summary LIKE ? 
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    @_ttl_cache(ttl_seconds=60)
    def get_symbol_info(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Returns detailed signature, line range, and docstrings for a symbol."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT s.*, f.language, f.summary AS file_summary
                FROM codebase_symbols s
                JOIN codebase_files f ON s.file_path = f.path
                WHERE s.symbol_name = ? OR s.symbol_name LIKE ?
                ORDER BY s.complexity DESC
            """, (symbol_name, f"%.{symbol_name}"))
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    @_ttl_cache(ttl_seconds=60)
    def get_file_context(self, rel_path: str) -> Optional[Dict[str, Any]]:
        """Returns complete context for a file: metadata, symbols, imports, callers, and locks."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM codebase_files WHERE path = ?", (rel_path,))
            file_row = cur.fetchone()
            if not file_row:
                return None

            cur.execute("SELECT * FROM codebase_symbols WHERE file_path = ? ORDER BY line_start ASC", (rel_path,))
            symbols = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT target_id, edge_type FROM graph_edges WHERE source_id = ?", (rel_path,))
            dependencies = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT source_id, edge_type FROM graph_edges WHERE target_id = ?", (rel_path,))
            callers = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM file_locks WHERE file_path = ? AND expires_at > datetime('now')", (rel_path,))
            lock_row = cur.fetchone()

            return {
                "file": dict(file_row),
                "symbols": symbols,
                "dependencies": dependencies,
                "dependents": callers,
                "active_lock": dict(lock_row) if lock_row else None
            }
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # 3. INTER-AGENT MESSAGE BUS & CHANNELS
    # -------------------------------------------------------------------------

    def send_message(self, sender: str, recipient: str = "all", channel: str = "general",
                     message_type: str = "broadcast", subject: str = "", content: str = "",
                     payload: Optional[Dict[str, Any]] = None) -> int:
        """Sends a message across the inter-agent bus."""
        conn = self._get_conn()
        try:
            with conn:
                cur = conn.cursor()
                payload_json = json.dumps(payload) if payload else None
                cur.execute("""
                    INSERT INTO agent_messages (sender_agent, recipient_agent, channel, message_type, subject, content, payload)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (sender, recipient, channel, message_type, subject, content, payload_json))
                msg_id = cur.lastrowid
                logger.info(f"📨 Agent Message [{msg_id}] from {sender} -> {recipient} ({channel}): {subject}")
                return msg_id
        finally:
            conn.close()

    def get_messages(self, agent_id: str = "all", channel: Optional[str] = None,
                     limit: int = 50, since_id: Optional[int] = None,
                     mark_read: bool = False) -> List[Dict[str, Any]]:
        """Retrieves messages for an agent or channel."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            conditions = ["(recipient_agent = 'all' OR recipient_agent = ? OR sender_agent = ?)"]
            params: List[Any] = [agent_id, agent_id]

            if channel:
                conditions.append("channel = ?")
                params.append(channel)

            if since_id is not None:
                conditions.append("id > ?")
                params.append(since_id)

            query = f"""
                SELECT * FROM agent_messages
                WHERE {" AND ".join(conditions)}
                ORDER BY id DESC
                LIMIT ?
            """
            params.append(limit)
            cur.execute(query, tuple(params))
            messages = [dict(r) for r in cur.fetchall()]

            if mark_read and messages:
                with conn:
                    msg_ids = [m["id"] for m in messages]
                    for mid in msg_ids:
                        cur.execute("SELECT read_by FROM agent_messages WHERE id = ?", (mid,))
                        row = cur.fetchone()
                        readers = json.loads(row["read_by"]) if row and row["read_by"] else []
                        if agent_id not in readers:
                            readers.append(agent_id)
                            cur.execute("UPDATE agent_messages SET read_by = ? WHERE id = ?", (json.dumps(readers), mid))

            return messages
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # 4. DISTRIBUTED FILE LOCKS & COORDINATION
    # -------------------------------------------------------------------------

    def acquire_lock(self, file_path: str, agent_id: str, purpose: str, ttl_seconds: int = 300) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Attempts to acquire a soft lock on a file for an agent to prevent collision."""
        conn = self._get_conn()
        try:
            with conn:
                cur = conn.cursor()
                # Clean up expired locks first
                cur.execute("DELETE FROM file_locks WHERE expires_at <= datetime('now')")

                # Check if currently locked
                cur.execute("SELECT * FROM file_locks WHERE file_path = ?", (file_path,))
                existing = cur.fetchone()

                if existing:
                    if existing["locked_by_agent"] == agent_id:
                        # Refresh TTL
                        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()
                        cur.execute("UPDATE file_locks SET expires_at = ?, purpose = ? WHERE file_path = ?", (expires_at, purpose, file_path))
                        self._invalidate_cache()
                        return True, None
                    else:
                        # Locked by someone else
                        return False, dict(existing)

                expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()
                cur.execute("""
                    INSERT INTO file_locks (file_path, locked_by_agent, purpose, expires_at)
                    VALUES (?, ?, ?, ?)
                """, (file_path, agent_id, purpose, expires_at))

                # Notify bus
                cur.execute("""
                    INSERT INTO agent_messages (sender_agent, recipient_agent, channel, message_type, subject, content, payload)
                    VALUES (?, 'all', 'locks', 'lock_request', ?, ?, ?)
                """, (agent_id, f"[LOCK_ACQUIRED] {file_path}", f"Agent {agent_id} locked `{file_path}`: {purpose}", json.dumps({"file_path": file_path, "expires_at": expires_at})))

                self._invalidate_cache()
                return True, None
        finally:
            conn.close()

    def release_lock(self, file_path: str, agent_id: str) -> bool:
        """Releases a previously held file lock."""
        conn = self._get_conn()
        try:
            with conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM file_locks WHERE file_path = ? AND locked_by_agent = ?", (file_path, agent_id))
                released = cur.rowcount > 0
                if released:
                    cur.execute("""
                        INSERT INTO agent_messages (sender_agent, recipient_agent, channel, message_type, subject, content, payload)
                        VALUES (?, 'all', 'locks', 'lock_release', ?, ?, ?)
                    """, (agent_id, f"[LOCK_RELEASED] {file_path}", f"Agent {agent_id} unlocked `{file_path}`", json.dumps({"file_path": file_path})))
                
                if released:
                    self._invalidate_cache()
                return released
        finally:
            conn.close()

    def get_active_locks(self) -> List[Dict[str, Any]]:
        """Returns all currently active unexpired locks."""
        conn = self._get_conn()
        try:
            with conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM file_locks WHERE expires_at <= datetime('now')")
                cur.execute("SELECT * FROM file_locks ORDER BY acquired_at DESC")
                return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # 5. AGENT PRESENCE & SESSIONS
    # -------------------------------------------------------------------------

    def update_presence(self, agent_id: str, client_type: str, current_task: Optional[str] = None,
                        active_files: Optional[List[str]] = None, status: str = "active"):
        """Heartbeat and presence updater for agents."""
        conn = self._get_conn()
        try:
            with conn:
                cur = conn.cursor()
                active_files_json = json.dumps(active_files or [])
                cur.execute("""
                    INSERT INTO agent_sessions (agent_id, client_type, current_task, active_files, status, last_heartbeat)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                    ON CONFLICT(agent_id) DO UPDATE SET
                        client_type = excluded.client_type,
                        current_task = COALESCE(excluded.current_task, agent_sessions.current_task),
                        active_files = excluded.active_files,
                        status = excluded.status,
                        last_heartbeat = datetime('now')
                """, (agent_id, client_type, current_task, active_files_json, status))
        finally:
            conn.close()

    def get_active_agents(self, active_within_seconds: int = 600) -> List[Dict[str, Any]]:
        """Returns all agents active within the given timeframe."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM agent_sessions
                WHERE strftime('%s', 'now') - strftime('%s', last_heartbeat) <= ?
                ORDER BY last_heartbeat DESC
            """, (active_within_seconds,))
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # 6. LONG TERM AGENT MEMORY & ARCHITECTURAL DECISIONS (ADR)
    # -------------------------------------------------------------------------

    def record_memory(self, category: str, title: str, content: str,
                       tags: Optional[List[str]] = None, created_by: str = "agent") -> int:
        """Stores persistent architectural insights, conventions, or decisions."""
        conn = self._get_conn()
        try:
            with conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO agent_memories (category, title, content, tags, created_by)
                    VALUES (?, ?, ?, ?, ?)
                """, (category, title, content, json.dumps(tags or []), created_by))
                mem_id = cur.lastrowid
                
                # Also notify bus
                cur.execute("""
                    INSERT INTO agent_messages (sender_agent, recipient_agent, channel, message_type, subject, content, payload)
                    VALUES (?, 'all', 'architecture', 'decision', ?, ?, ?)
                """, (created_by, f"[MEM_{category.upper()}] {title}", content, json.dumps({"title": title, "category": category, "tags": tags})))
                
                return mem_id
        finally:
            conn.close()

    def get_memories(self, category: Optional[str] = None, tag: Optional[str] = None,
                     query: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves stored memories matching category or search query."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            conditions = ["1=1"]
            params: List[Any] = []

            if category:
                conditions.append("category = ?")
                params.append(category)

            if tag:
                conditions.append("tags LIKE ?")
                params.append(f"%{tag}%")

            if query:
                conditions.append("(title LIKE ? OR content LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])

            q_str = f"SELECT * FROM agent_memories WHERE {' AND '.join(conditions)} ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)

            cur.execute(q_str, tuple(params))
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # 7. AUDIT LOG & RECENT CHANGES
    # -------------------------------------------------------------------------

    def get_recent_changes(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Returns the chronological audit log of file modifications and creations."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM change_events ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """Provides statistical overview of the Context DB and codebase."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS total_files, SUM(lines_count) AS total_lines, SUM(token_estimate) AS total_tokens FROM codebase_files")
            file_stats = dict(cur.fetchone())

            cur.execute("SELECT COUNT(*) AS total_symbols FROM codebase_symbols")
            sym_stats = dict(cur.fetchone())

            cur.execute("SELECT COUNT(*) AS total_edges FROM graph_edges")
            edge_stats = dict(cur.fetchone())

            cur.execute("SELECT COUNT(*) AS total_messages FROM agent_messages")
            msg_stats = dict(cur.fetchone())

            cur.execute("SELECT COUNT(*) AS total_memories FROM agent_memories")
            mem_stats = dict(cur.fetchone())

            cur.execute("SELECT COUNT(*) AS active_locks FROM file_locks WHERE expires_at > datetime('now')")
            lock_stats = dict(cur.fetchone())

            return {
                **file_stats,
                **sym_stats,
                **edge_stats,
                **msg_stats,
                **mem_stats,
                **lock_stats
            }
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # 8. PROMPT-MASTER INTEGRATION
    # -------------------------------------------------------------------------

    @_ttl_cache(ttl_seconds=60)
    def render_prompt_template(self, template_name: str, **kwargs) -> str:
        """
        Integrates with prompt-master to load templates and inject dynamic ContextDB data.
        Templates should be placed in ai-services/prompt-master/templates/.
        """
        templates_dir = os.path.join(self.repo_root, "ai-services", "prompt-master", "templates")
        path = os.path.join(templates_dir, template_name)
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Template {template_name} not found in {templates_dir}")
            
        with open(path, "r", encoding="utf-8") as f:
            template = f.read()

        context_data = kwargs.copy()
        
        # Inject dynamic context components if requested
        if "file_path" in kwargs:
            file_ctx = self.get_file_context(kwargs["file_path"])
            context_data["file_context"] = json.dumps(file_ctx, indent=2) if file_ctx else "No file context found."
            
        if "symbol" in kwargs:
            sym_info = self.get_symbol_info(kwargs["symbol"])
            context_data["symbol_info"] = json.dumps(sym_info, indent=2) if sym_info else "No symbol info found."
                
        if "memory_category" in kwargs:
            mems = self.get_memories(category=kwargs["memory_category"])
            context_data["memories"] = json.dumps(mems, indent=2) if mems else "No memories found."
            
        try:
            return template.format(**context_data)
        except KeyError as e:
            raise ValueError(f"Missing context variable {e} for template '{template_name}'")

_global_instance = None

def get_context_db(db_path: str = DB_PATH, repo_root: str = REPO_ROOT) -> ContextDB:
    """Returns singleton instance of ContextDB."""
    global _global_instance
    if _global_instance is None:
        _global_instance = ContextDB(db_path, repo_root)
    return _global_instance

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    db = get_context_db()
    print("Testing ContextDB reindex...")
    stats = db.reindex_all("cli-test")
    print(f"Indexed stats: {stats}")
    print(f"Overview stats: {db.get_stats()}")
