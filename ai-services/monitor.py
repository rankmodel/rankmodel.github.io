#!/usr/bin/env python3
"""
ModelRank Continuous Codebase Monitor & Event Streamer
Watches for ongoing edits, updates Context DB in real time, and broadcasts change notifications.
"""
import os
import sys
import time
import argparse
import logging
from datetime import datetime
from typing import Dict, Set

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from context_engine import get_context_db, IGNORE_DIRS, IGNORE_EXTENSIONS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("codebase_monitor")

class CodebaseMonitor:
    def __init__(self, poll_interval: float = 2.0, agent_id: str = "monitor-daemon"):
        self.poll_interval = poll_interval
        self.agent_id = agent_id
        self.db = get_context_db()
        self.repo_root = self.db.repo_root
        self.file_snapshots: Dict[str, float] = {} # rel_path -> mtime
        self._running = False

    def _should_track(self, rel_path: str) -> bool:
        parts = rel_path.split(os.sep)
        for part in parts:
            if part in IGNORE_DIRS or (part.startswith('.') and part not in ('.cursorrules', '.windsurfrules', '.env.example', '.agents')):
                return False
        if 'static_output/models' in rel_path or 'static_output/badges' in rel_path or 'outputs/notebooklm_sources' in rel_path:
            return False
        ext = os.path.splitext(rel_path)[1].lower()
        if ext in IGNORE_EXTENSIONS:
            return False
        return True

    def scan_workspace(self) -> Dict[str, float]:
        """Scans current workspace files and their mtimes."""
        current_files = {}
        for root, dirs, files in os.walk(self.repo_root):
            dirs[:] = [
                d for d in dirs
                if d not in IGNORE_DIRS
                and not d.startswith('.')
                and not os.path.relpath(os.path.join(root, d), self.repo_root).startswith('static_output/models')
                and not os.path.relpath(os.path.join(root, d), self.repo_root).startswith('static_output/badges')
                and not os.path.relpath(os.path.join(root, d), self.repo_root).startswith('outputs/notebooklm_sources')
            ]
            for f in files:
                if f.startswith('.') and f not in ('.cursorrules', '.windsurfrules', '.env.example'):
                    continue
                abs_path = os.path.join(root, f)
                rel_path = os.path.relpath(abs_path, self.repo_root)
                if self._should_track(rel_path):
                    try:
                        current_files[rel_path] = os.path.getmtime(abs_path)
                    except OSError:
                        pass
        return current_files

    def sync_pass(self) -> Dict[str, int]:
        """Performs a single diff check against previous snapshot."""
        current_files = self.scan_workspace()
        
        created = 0
        modified = 0
        deleted = 0

        # Check for new or modified files
        for rel_path, mtime in current_files.items():
            prev_mtime = self.file_snapshots.get(rel_path)
            if prev_mtime is None:
                # New file
                if self.db.index_file(rel_path, author_agent=self.agent_id, broadcast_event=True):
                    created += 1
                    logger.info(f"✨ Detected NEW file: {rel_path}")
            elif mtime > prev_mtime:
                # Modified file
                if self.db.index_file(rel_path, author_agent=self.agent_id, broadcast_event=True):
                    modified += 1
                    logger.info(f"📝 Detected MODIFIED file: {rel_path}")

        # Check for deleted files
        for rel_path in list(self.file_snapshots.keys()):
            if rel_path not in current_files:
                self.db.remove_file(rel_path, author_agent=self.agent_id)
                deleted += 1
                logger.info(f"🗑️ Detected DELETED file: {rel_path}")

        self.file_snapshots = current_files

        # Clean expired locks and send presence heartbeat
        self.db.update_presence(
            agent_id=self.agent_id,
            client_type="monitor",
            current_task="Continuous codebase change monitoring",
            status="active"
        )

        return {"created": created, "modified": modified, "deleted": deleted}

    def start_monitoring(self):
        """Runs the continuous monitoring loop."""
        logger.info(f"🚀 Starting continuous codebase monitoring (interval: {self.poll_interval}s)...")
        # Initial snapshot
        self.file_snapshots = self.scan_workspace()
        logger.info(f"👀 Tracking {len(self.file_snapshots)} codebase files.")
        self._running = True

        try:
            while self._running:
                deltas = self.sync_pass()
                if deltas["created"] > 0 or deltas["modified"] > 0 or deltas["deleted"] > 0:
                    logger.info(f"⚡ Sync cycle: +{deltas['created']} ~{deltas['modified']} -{deltas['deleted']}")
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user.")
            self._running = False

def main():
    parser = argparse.ArgumentParser(description="Continuous Codebase Monitor for Context DB")
    parser.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run a single sync pass and exit")
    parser.add_argument("--agent-id", type=str, default="monitor-daemon", help="Agent identifier")
    args = parser.parse_args()

    monitor = CodebaseMonitor(poll_interval=args.interval, agent_id=args.agent_id)
    if args.once:
        monitor.file_snapshots = monitor.scan_workspace()
        res = monitor.sync_pass()
        print(f"Sync pass result: {res}")
    else:
        monitor.start_monitoring()

if __name__ == '__main__':
    main()
