#!/usr/bin/env python3
"""
ModelRank Agent Collaboration CLI & Control Panel
Allows developers and autonomous agents to inspect context, query symbols, lock files, and exchange messages.
"""
import sys
import os
import json
import argparse
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from context_engine import get_context_db
from monitor import CodebaseMonitor

db = get_context_db()

def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║   🏆 MODELRANK MULTI-AGENT CONTEXT & COLLABORATION ENGINE 100x   ║
╚═══════════════════════════════════════════════════════════════════╝""")

def cmd_status(args):
    print_banner()
    stats = db.get_stats()
    agents = db.get_active_agents()
    locks = db.get_active_locks()

    print("\n📊 CODEBASE CONTEXT METRICS:")
    print(f"  • Indexed Files:     {stats.get('total_files', 0):,}")
    print(f"  • Lines of Code:     {stats.get('total_lines', 0):,}")
    print(f"  • Estimated Tokens:  {stats.get('total_tokens', 0):,}")
    print(f"  • AST Symbols:       {stats.get('total_symbols', 0):,}")
    print(f"  • Graph Edges:       {stats.get('total_edges', 0):,}")
    print(f"  • Agent Messages:    {stats.get('total_messages', 0):,}")
    print(f"  • Stored Memories:   {stats.get('total_memories', 0):,}")

    print("\n🔒 ACTIVE FILE LOCKS:")
    if not locks:
        print("  (None — all files free for concurrent editing)")
    else:
        for l in locks:
            print(f"  • {l['file_path']} -> locked by [{l['locked_by_agent']}] until {l['expires_at']} (Reason: {l['purpose']})")

    print("\n🤖 ACTIVE AGENTS:")
    if not agents:
        print("  (No active heartbeats in last 10m)")
    else:
        for a in agents:
            print(f"  • {a['agent_id']} ({a['client_type']}) - Status: {a['status']} - Task: {a.get('current_task', 'N/A')}")
    print()

def cmd_search(args):
    query = " ".join(args.query)
    results = db.search_codebase(query, limit=args.limit)
    print(f"\n🔍 Search results for '{query}' ({len(results)} found):\n")
    if not results:
        print("  No matching files or symbols found.")
        return

    for i, r in enumerate(results, 1):
        print(f"[{i}] {r['file_path']}  (Score: {r['score']})")
        if r.get('symbol_name'):
            print(f"    Symbols: {r['symbol_name']}")
        if r.get('summary'):
            print(f"    Summary: {r['summary']}")
        if r.get('snippet'):
            clean_snippet = r['snippet'].replace('<b>', '\033[1m\033[33m').replace('</b>', '\033[0m')
            print(f"    Match:\n      {clean_snippet.replace(chr(10), chr(10) + '      ')}")
        print()

def cmd_symbol(args):
    sym_name = args.name
    results = db.get_symbol_info(sym_name)
    print(f"\n🧬 Symbol Info for '{sym_name}' ({len(results)} found):\n")
    if not results:
        print(f"  Symbol '{sym_name}' not found.")
        return

    for r in results:
        print(f"• Name:       {r['symbol_name']} ({r['symbol_type']})")
        print(f"  File:       {r['file_path']}:{r['line_start']}-{r['line_end']}")
        if r.get('signature'):
            print(f"  Signature:  {r['signature']}")
        if r.get('docstring'):
            print(f"  Docstring:  {r['docstring']}")
        if r.get('dependencies'):
            print(f"  Deps:       {r['dependencies']}")
        print(f"  Complexity: {r['complexity']}")
        print()

def cmd_file(args):
    ctx = db.get_file_context(args.path)
    if not ctx:
        print(f"❌ File '{args.path}' not found in Context DB.")
        return

    f = ctx["file"]
    print(f"\n📄 File Context: {f['path']}")
    print(f"  Language:    {f['language']}")
    print(f"  Lines:       {f['lines_count']} ({f['size_bytes']} bytes)")
    print(f"  Summary:     {f['summary']}")
    print(f"  Last Mod:    {f['last_modified']}")
    
    if ctx.get("active_lock"):
        l = ctx["active_lock"]
        print(f"  ⚠️ LOCKED by {l['locked_by_agent']} until {l['expires_at']} ({l['purpose']})")

    print(f"\n  AST Symbols ({len(ctx['symbols'])}):")
    for s in ctx["symbols"]:
        print(f"    • {s['symbol_type'].upper():<10} {s['symbol_name']:<30} L{s['line_start']}-{s['line_end']}")

    if ctx.get("dependencies"):
        print(f"\n  Outgoing Imports/Deps ({len(ctx['dependencies'])}):")
        for d in ctx["dependencies"][:10]:
            print(f"    -> {d['edge_type']} {d['target_id']}")

    if ctx.get("dependents"):
        print(f"\n  Incoming Callers/Dependents ({len(ctx['dependents'])}):")
        for d in ctx["dependents"][:10]:
            print(f"    <- {d['edge_type']} from {d['source_id']}")
    print()

def cmd_feed(args):
    msgs = db.get_messages(agent_id="all", channel=args.channel, limit=args.limit)
    print(f"\n📡 Inter-Agent Event Feed (Channel: {args.channel or 'ALL'}, Limit: {args.limit}):\n")
    if not msgs:
        print("  No messages recorded.")
        return

    for m in reversed(msgs):
        ts = m['created_at']
        sender = m['sender_agent']
        channel = m['channel']
        subject = m['subject']
        m_type = m['message_type']
        print(f"[{ts}] [{channel.upper()}] <{sender}> {subject} ({m_type})")
        if args.verbose and m.get('content'):
            print(f"     Content: {m['content']}")
        if args.verbose and m.get('payload'):
            print(f"     Payload: {m['payload']}")
    print()

def cmd_broadcast(args):
    sender = args.sender or "cli-user"
    channel = args.channel or "general"
    content = " ".join(args.message)
    subject = args.subject or (content[:50] + "..." if len(content) > 50 else content)
    
    msg_id = db.send_message(
        sender=sender,
        recipient="all",
        channel=channel,
        message_type="broadcast",
        subject=subject,
        content=content
    )
    print(f"✅ Broadcast sent! Message ID: {msg_id}")

def cmd_lock(args):
    agent_id = args.agent or "cli-agent"
    acquired, existing = db.acquire_lock(
        file_path=args.path,
        agent_id=agent_id,
        purpose=args.purpose,
        ttl_seconds=args.ttl
    )
    if acquired:
        print(f"✅ Lock ACQUIRED on '{args.path}' for {args.ttl}s (Agent: {agent_id})")
    else:
        print(f"❌ Lock FAILED: '{args.path}' is already locked by {existing['locked_by_agent']} until {existing['expires_at']}")

def cmd_unlock(args):
    agent_id = args.agent or "cli-agent"
    released = db.release_lock(args.path, agent_id)
    if released:
        print(f"✅ Lock RELEASED on '{args.path}'")
    else:
        print(f"⚠️ Could not release lock (maybe not held by {agent_id} or already expired).")

def cmd_reindex(args):
    print("🔄 Running full codebase reindex...")
    stats = db.reindex_all(author_agent="cli-reindex")
    print(f"✅ Reindex complete: {stats}")

def cmd_watch(args):
    monitor = CodebaseMonitor(poll_interval=args.interval, agent_id="cli-watch")
    monitor.start_monitoring()

def cmd_memories(args):
    mems = db.get_memories(category=args.category, query=args.query, limit=args.limit)
    print(f"\n🧠 Agent Architectural Memories & Decisions ({len(mems)} found):\n")
    for m in mems:
        print(f"• [{m['category'].upper()}] {m['title']} (by {m['created_by']} on {m['created_at']})")
        print(f"  Tags: {m.get('tags', '[]')}")
        print(f"  Content:\n    {m['content'].replace(chr(10), chr(10) + '    ')}")
        print()

def main():
    parser = argparse.ArgumentParser(description="ModelRank Multi-Agent Collaboration CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # status
    p_status = subparsers.add_parser("status", help="Show context DB stats, active locks, and agents")

    # search
    p_search = subparsers.add_parser("search", help="Full-text and semantic search over codebase")
    p_search.add_argument("query", nargs="+", help="Keywords to search")
    p_search.add_argument("--limit", type=int, default=10)

    # symbol
    p_symbol = subparsers.add_parser("symbol", help="Look up symbol definition, signature, and callers")
    p_symbol.add_argument("name", help="Symbol name (e.g. compute_composite_score)")

    # file
    p_file = subparsers.add_parser("file", help="Inspect AST symbols, dependencies, and lock for a file")
    p_file.add_argument("path", help="Relative file path")

    # feed
    p_feed = subparsers.add_parser("feed", help="View inter-agent message and edit event feed")
    p_feed.add_argument("--channel", type=str, help="Filter by channel ('ongoing-edits', 'architecture', 'locks')")
    p_feed.add_argument("--limit", type=int, default=25)
    p_feed.add_argument("-v", "--verbose", action="store_true")

    # broadcast
    p_bcast = subparsers.add_parser("broadcast", help="Publish a message to all agents")
    p_bcast.add_argument("message", nargs="+", help="Message content")
    p_bcast.add_argument("--subject", type=str, help="Message subject")
    p_bcast.add_argument("--channel", type=str, default="general", help="Channel name")
    p_bcast.add_argument("--sender", type=str, default="cli-user", help="Sender agent name")

    # lock
    p_lock = subparsers.add_parser("lock", help="Acquire a file lock")
    p_lock.add_argument("path", help="File path to lock")
    p_lock.add_argument("purpose", help="Reason for editing")
    p_lock.add_argument("--agent", type=str, default="cli-agent", help="Agent identifier")
    p_lock.add_argument("--ttl", type=int, default=300, help="Lock duration in seconds")

    # unlock
    p_unlock = subparsers.add_parser("unlock", help="Release a file lock")
    p_unlock.add_argument("path", help="File path to unlock")
    p_unlock.add_argument("--agent", type=str, default="cli-agent", help="Agent identifier")

    # reindex
    p_reindex = subparsers.add_parser("reindex", help="Re-crawl and reindex all codebase files")

    # watch
    p_watch = subparsers.add_parser("watch", help="Start continuous live monitoring daemon")
    p_watch.add_argument("--interval", type=float, default=2.0, help="Poll interval in seconds")

    # memories
    p_mems = subparsers.add_parser("memories", help="List stored architectural decisions and conventions")
    p_mems.add_argument("--category", type=str, help="Filter by category ('architecture_decision', 'convention')")
    p_mems.add_argument("--query", type=str, help="Search query")
    p_mems.add_argument("--limit", type=int, default=15)

    args = parser.parse_args()

    if not args.command or args.command == "status":
        cmd_status(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "symbol":
        cmd_symbol(args)
    elif args.command == "file":
        cmd_file(args)
    elif args.command == "feed":
        cmd_feed(args)
    elif args.command == "broadcast":
        cmd_broadcast(args)
    elif args.command == "lock":
        cmd_lock(args)
    elif args.command == "unlock":
        cmd_unlock(args)
    elif args.command == "reindex":
        cmd_reindex(args)
    elif args.command == "watch":
        cmd_watch(args)
    elif args.command == "memories":
        cmd_memories(args)

if __name__ == '__main__':
    main()
