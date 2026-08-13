"""
Unit tests for Context DB, AST Indexer, Inter-Agent Messaging, File Locks, and MCP Tools.
"""
import os
import sys
import tempfile
import sqlite3
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICE_DIR = os.path.join(BASE_DIR, 'ai-services')
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

from context_engine import ContextDB

@pytest.fixture
def temp_context_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_memory.db")
        db = ContextDB(db_path=db_path, repo_root=BASE_DIR)
        yield db

class TestContextDBIndexing:
    def test_init_creates_all_tables(self, temp_context_db):
        conn = temp_context_db._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r["name"] for r in cur.fetchall()}
        conn.close()

        expected = {
            "prompts", "codebase_files", "codebase_symbols", "graph_nodes",
            "graph_edges", "agent_messages", "agent_sessions", "file_locks",
            "agent_memories", "change_events", "shared_tasks", "fts_codebase"
        }
        for table in expected:
            assert table in tables, f"Missing table: {table}"

    def test_index_single_python_file(self, temp_context_db):
        success = temp_context_db.index_file("scoring/engine.py", author_agent="test-agent")
        assert success is True

        ctx = temp_context_db.get_file_context("scoring/engine.py")
        assert ctx is not None
        assert ctx["file"]["language"] == "python"
        assert len(ctx["symbols"]) > 0

        # Check symbol names include compute_composite_score
        sym_names = [s["symbol_name"] for s in ctx["symbols"]]
        assert "compute_composite_score" in sym_names

    def test_search_fts5(self, temp_context_db):
        temp_context_db.index_file("scoring/engine.py", author_agent="test-agent")
        results = temp_context_db.search_codebase("composite score benchmark")
        assert len(results) > 0
        assert results[0]["file_path"] == "scoring/engine.py"

class TestInterAgentMessaging:
    def test_send_and_retrieve_message(self, temp_context_db):
        msg_id = temp_context_db.send_message(
            sender="cursor-agent",
            recipient="windsurf-agent",
            channel="architecture",
            message_type="query",
            subject="Refactoring scoring weights",
            content="Can we adjust benchmark weight to 0.45?"
        )
        assert msg_id > 0

        msgs = temp_context_db.get_messages(agent_id="windsurf-agent", channel="architecture")
        assert len(msgs) == 1
        assert msgs[0]["sender_agent"] == "cursor-agent"
        assert msgs[0]["subject"] == "Refactoring scoring weights"

    def test_broadcast_message(self, temp_context_db):
        temp_context_db.send_message(
            sender="antigravity",
            recipient="all",
            channel="ongoing-edits",
            subject="Updated static assets",
            content="Generated new leaderboard index.html"
        )

        msgs = temp_context_db.get_messages(agent_id="cursor-agent")
        assert len(msgs) >= 1
        assert any(m["subject"] == "Updated static assets" for m in msgs)

class TestFileLocks:
    def test_acquire_and_release_lock(self, temp_context_db):
        file_path = "scoring/engine.py"
        
        # Acquire
        acquired, _ = temp_context_db.acquire_lock(file_path, "agent-1", "updating formula", ttl_seconds=60)
        assert acquired is True

        # Second agent tries to acquire
        acquired_2, existing = temp_context_db.acquire_lock(file_path, "agent-2", "competing edit", ttl_seconds=60)
        assert acquired_2 is False
        assert existing["locked_by_agent"] == "agent-1"

        # Release
        released = temp_context_db.release_lock(file_path, "agent-1")
        assert released is True

        # Agent 2 can now acquire
        acquired_3, _ = temp_context_db.acquire_lock(file_path, "agent-2", "competing edit", ttl_seconds=60)
        assert acquired_3 is True

class TestAgentMemories:
    def test_record_and_query_memory(self, temp_context_db):
        m_id = temp_context_db.record_memory(
            category="architecture_decision",
            title="ADR-Test: Scoring Tiers",
            content="S-Tier is defined as >= 85.",
            tags=["tiers", "scoring"],
            created_by="test-agent"
        )
        assert m_id > 0

        mems = temp_context_db.get_memories(category="architecture_decision", query="S-Tier")
        assert len(mems) == 1
        assert mems[0]["title"] == "ADR-Test: Scoring Tiers"
