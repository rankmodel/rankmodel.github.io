import sqlite3
import threading
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import time

from config.settings import CACHE_DB_PATH

logger = logging.getLogger(__name__)

class ModelCache:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            self.db_path = Path(CACHE_DB_PATH)
        else:
            self.db_path = Path(db_path)
            
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        schema_path = Path(__file__).parent / 'schema.sql'
        try:
            if schema_path.exists():
                with open(schema_path, "r") as f:
                    schema_sql = f.read()
            else:
                schema_sql = """
                CREATE TABLE IF NOT EXISTS models (
                    model_id TEXT PRIMARY KEY,
                    data TEXT,
                    timestamp INTEGER
                );
                CREATE TABLE IF NOT EXISTS eval_results (
                    model_id TEXT PRIMARY KEY,
                    results TEXT,
                    timestamp INTEGER
                );
                CREATE TABLE IF NOT EXISTS scores (
                    model_id TEXT PRIMARY KEY,
                    score_data TEXT,
                    timestamp INTEGER
                );
                CREATE TABLE IF NOT EXISTS achievements (
                    model_id TEXT,
                    achievement_type TEXT,
                    awarded_at INTEGER,
                    PRIMARY KEY (model_id, achievement_type)
                );
                CREATE TABLE IF NOT EXISTS leaderboard_bounds (
                    benchmark_id TEXT PRIMARY KEY,
                    min_score REAL,
                    max_score REAL,
                    total_models INTEGER,
                    timestamp INTEGER
                );
                """
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('PRAGMA journal_mode=WAL')
                    conn.execute('PRAGMA synchronous=NORMAL')
                    conn.executescript(schema_sql)
        except Exception as e:
            logger.error(f"Error initializing database: {e}")

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT data, timestamp FROM models WHERE model_id = ?", (model_id,))
                row = cursor.fetchone()
                if row:
                    data, timestamp = row
                    if time.time() - timestamp < 24 * 3600:
                        return json.loads(data)
                return None

    def set_model(self, model_id: str, model_data: Dict[str, Any]):
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO models (model_id, data, timestamp) VALUES (?, ?, ?) ON CONFLICT(model_id) DO UPDATE SET data=excluded.data, timestamp=excluded.timestamp",
                    (model_id, json.dumps(model_data), int(time.time()))
                )

    def get_eval_results(self, model_id: str) -> list:
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT results, timestamp FROM eval_results WHERE model_id = ?", (model_id,))
                row = cursor.fetchone()
                if row:
                    results, timestamp = row
                    if time.time() - timestamp < 6 * 3600:
                        return json.loads(results)
                return []

    def set_eval_results(self, model_id: str, results: list):
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO eval_results (model_id, results, timestamp) VALUES (?, ?, ?) ON CONFLICT(model_id) DO UPDATE SET results=excluded.results, timestamp=excluded.timestamp",
                    (model_id, json.dumps(results), int(time.time()))
                )

    def get_score(self, model_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT score_data FROM scores WHERE model_id = ?", (model_id,))
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return None

    def set_score(self, model_id: str, score_data: Dict[str, Any]):
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO scores (model_id, score_data, timestamp) VALUES (?, ?, ?) ON CONFLICT(model_id) DO UPDATE SET score_data=excluded.score_data, timestamp=excluded.timestamp",
                    (model_id, json.dumps(score_data), int(time.time()))
                )

    def get_size(self) -> int:
        """Return total number of scored models in the database."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM scores")
                row = cursor.fetchone()
                return row[0] if row else 0

    def get_total_models(self, tier: Optional[str] = None, task: Optional[str] = None) -> int:
        """Return total count of models matching optional filters."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = "SELECT COUNT(*) FROM scores s JOIN models m ON s.model_id = m.model_id"
                conditions = []
                params = []
                if tier:
                    conditions.append("json_extract(s.score_data, '$.tier') = ?")
                    params.append(tier)
                if task:
                    conditions.append("json_extract(m.data, '$.pipeline_tag') = ?")
                    params.append(task)
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                cursor.execute(query, params)
                row = cursor.fetchone()
                return row[0] if row else 0

    def get_leaderboard(self, limit: int = 100, offset: int = 0, tier: Optional[str] = None, task: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = "SELECT s.model_id, s.score_data, m.data FROM scores s JOIN models m ON s.model_id = m.model_id"
                conditions = []
                params = []
                if tier:
                    conditions.append("json_extract(s.score_data, '$.tier') = ?")
                    params.append(tier)
                if task:
                    conditions.append("json_extract(m.data, '$.pipeline_tag') = ?")
                    params.append(task)
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                # Sort by composite score descending
                query += " ORDER BY CAST(json_extract(s.score_data, '$.composite') AS REAL) DESC"
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                results = []
                for model_id, score_data_str, model_data_str in rows:
                    results.append({
                        "model_id": model_id,
                        "score": json.loads(score_data_str),
                        "model": json.loads(model_data_str)
                    })
                return results

    def get_leaderboard_bounds(self, benchmark_id: str) -> Optional[Dict[str, float]]:
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT min_score, max_score, total_models FROM leaderboard_bounds WHERE benchmark_id = ?", (benchmark_id,))
                row = cursor.fetchone()
                if row:
                    return {
                        "min_score": row[0],
                        "max_score": row[1],
                        "total_models": row[2]
                    }
                return None

    def set_leaderboard_bounds(self, benchmark_id: str, min_score: float, max_score: float, total_models: int):
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO leaderboard_bounds (benchmark_id, min_score, max_score, total_models, timestamp) VALUES (?, ?, ?, ?, ?) ON CONFLICT(benchmark_id) DO UPDATE SET min_score=excluded.min_score, max_score=excluded.max_score, total_models=excluded.total_models, timestamp=excluded.timestamp",
                    (benchmark_id, min_score, max_score, total_models, int(time.time()))
                )

    def get_achievements(self, model_id: str) -> List[str]:
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT achievement_type FROM achievements WHERE model_id = ?", (model_id,))
                rows = cursor.fetchall()
                return [row[0] for row in rows]

    def set_achievement(self, model_id: str, achievement_type: str):
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO achievements (model_id, achievement_type, awarded_at) VALUES (?, ?, ?)",
                    (model_id, achievement_type, int(time.time()))
                )

    def clear_expired(self):
        now = int(time.time())
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM models WHERE ? - timestamp >= ?", (now, 24 * 3600))
                cursor.execute("DELETE FROM eval_results WHERE ? - timestamp >= ?", (now, 6 * 3600))
                cursor.execute("DELETE FROM scores WHERE ? - timestamp >= ?", (now, 24 * 3600))
                cursor.execute("DELETE FROM leaderboard_bounds WHERE ? - timestamp >= ?", (now, 24 * 3600))
