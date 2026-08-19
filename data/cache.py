import sqlite3
import threading
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import time

from config.settings import CACHE_DB_PATH
from scoring.elo import DEFAULT_RATING, update_ratings

logger = logging.getLogger(__name__)

class ModelCache:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            self.db_path = Path(CACHE_DB_PATH)
        else:
            self.db_path = Path(db_path)
            
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.execute('PRAGMA synchronous=NORMAL')
        self._init_db()

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

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
                self.conn.executescript(schema_sql)
        except Exception as e:
            logger.error(f"Error initializing database: {e}")

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT data, timestamp FROM models WHERE model_id = ?", (model_id,))
            row = cursor.fetchone()
            if row:
                data, timestamp = row
                if time.time() - timestamp < 24 * 3600:
                    return json.loads(data)
            return None

    def set_model(self, model_id: str, model_data: Dict[str, Any]):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO models (model_id, data, timestamp) VALUES (?, ?, ?) ON CONFLICT(model_id) DO UPDATE SET data=excluded.data, timestamp=excluded.timestamp",
                (model_id, json.dumps(model_data), int(time.time()))
            )
            self.conn.commit()

    def get_eval_results(self, model_id: str) -> list:
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT results, timestamp FROM eval_results WHERE model_id = ?", (model_id,))
            row = cursor.fetchone()
            if row:
                results, timestamp = row
                if time.time() - timestamp < 6 * 3600:
                    return json.loads(results)
            return []

    def set_eval_results(self, model_id: str, results: list):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO eval_results (model_id, results, timestamp) VALUES (?, ?, ?) ON CONFLICT(model_id) DO UPDATE SET results=excluded.results, timestamp=excluded.timestamp",
                (model_id, json.dumps(results), int(time.time()))
            )
            self.conn.commit()

    def get_score(self, model_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT score_data FROM scores WHERE model_id = ?", (model_id,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None

    def set_score(self, model_id: str, score_data: Dict[str, Any]):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO scores (model_id, score_data, timestamp) VALUES (?, ?, ?) ON CONFLICT(model_id) DO UPDATE SET score_data=excluded.score_data, timestamp=excluded.timestamp",
                (model_id, json.dumps(score_data), int(time.time()))
            )
            self.conn.commit()

    def get_size(self) -> int:
        """Return total number of scored models in the database."""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM scores")
            row = cursor.fetchone()
            return row[0] if row else 0

    def get_total_models(self, tier: Optional[str] = None, task: Optional[str] = None) -> int:
        """Return total count of models matching optional filters."""
        with self.lock:
            cursor = self.conn.cursor()
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
            cursor = self.conn.cursor()
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
            cursor = self.conn.cursor()
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
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO leaderboard_bounds (benchmark_id, min_score, max_score, total_models, timestamp) VALUES (?, ?, ?, ?, ?) ON CONFLICT(benchmark_id) DO UPDATE SET min_score=excluded.min_score, max_score=excluded.max_score, total_models=excluded.total_models, timestamp=excluded.timestamp",
                (benchmark_id, min_score, max_score, total_models, int(time.time()))
            )
            self.conn.commit()

    def get_achievements(self, model_id: str) -> List[str]:
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT achievement_type FROM achievements WHERE model_id = ?", (model_id,))
            rows = cursor.fetchall()
            return [row[0] for row in rows]

    def set_achievement(self, model_id: str, achievement_type: str):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO achievements (model_id, achievement_type, awarded_at) VALUES (?, ?, ?)",
                (model_id, achievement_type, int(time.time()))
            )
            self.conn.commit()

    # ---- Head-to-head ELO + comparison history (open-question #6 / #2) ----

    def get_elo_rating(self, model_id: str) -> float:
        """Return the current ELO rating for a model (defaults to 1500)."""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT rating FROM elo_ratings WHERE model_id = ?", (model_id,))
            row = cursor.fetchone()
            return row[0] if row else DEFAULT_RATING

    def get_elo_record(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Return the full ELO record (rating + W/L/D + match count) for a model."""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT model_id, rating, wins, losses, draws, matches, updated_at "
                "FROM elo_ratings WHERE model_id = ?",
                (model_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "model_id": row[0],
                "rating": row[1],
                "wins": row[2],
                "losses": row[3],
                "draws": row[4],
                "matches": row[5],
                "updated_at": row[6],
            }

    def record_head_to_head(
        self,
        review_id: str,
        model_a: str,
        model_b: str,
        verdict: str,            # 'A' | 'B' | 'tie'
        judge_type: str,         # 'human' | 'llm'
        judge_id: str = None,
    ):
        """Log a head-to-head comparison and update both models' ELO ratings.

        Idempotent on ``review_id`` (INSERT OR IGNORE) so replays are safe.
        """
        outcome = {"A": 1.0, "B": 0.0, "tie": 0.5}.get(verdict, 0.5)
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO reviews "
                "(review_id, model_a, model_b, verdict, judge_type, judge_id, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (review_id, model_a, model_b, verdict, judge_type, judge_id, int(time.time())),
            )
            cursor.execute("SELECT rating FROM elo_ratings WHERE model_id = ?", (model_a,))
            row = cursor.fetchone()
            ra = row[0] if row else DEFAULT_RATING
            cursor.execute("SELECT rating FROM elo_ratings WHERE model_id = ?", (model_b,))
            row = cursor.fetchone()
            rb = row[0] if row else DEFAULT_RATING
            new_a, new_b = update_ratings(ra, rb, outcome)
            deltas = {
                "A": ((1, 0, 0), (0, 1, 0)),
                "B": ((0, 1, 0), (1, 0, 0)),
                "tie": ((0, 0, 1), (0, 0, 1)),
            }[verdict]
            for mid, old, new, inc in (
                (model_a, ra, new_a, deltas[0]),
                (model_b, rb, new_b, deltas[1]),
            ):
                w, l, d = inc
                cursor.execute(
                    "INSERT INTO elo_ratings (model_id, rating, wins, losses, draws, matches, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, 1, ?) "
                    "ON CONFLICT(model_id) DO UPDATE SET "
                    "rating=excluded.rating, "
                    "wins=wins+excluded.wins, losses=losses+excluded.losses, "
                    "draws=draws+excluded.draws, matches=matches+1, updated_at=excluded.updated_at",
                    (mid, new, w, l, d, int(time.time())),
                )
                self.conn.commit()

    def get_reviews(
        self,
        limit: int = 50,
        model_id: Optional[str] = None,
        judge_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return recent head-to-head verdicts (community + LLM judge feed).

        ``model_id`` filters to reviews where the model appears as A or B.
        ``judge_type`` filters by 'human' | 'llm'. Most-recent first.
        """
        with self.lock:
            cursor = self.conn.cursor()
            clauses = []
            params: List[Any] = []
            if model_id:
                clauses.append("(model_a = ? OR model_b = ?)")
                params.extend([model_id, model_id])
            if judge_type:
                clauses.append("judge_type = ?")
                params.append(judge_type)
            where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
            cursor.execute(
                f"SELECT review_id, model_a, model_b, verdict, judge_type, judge_id, created_at "
                f"FROM reviews{where} ORDER BY created_at DESC LIMIT ?",
                params + [limit],
            )
            rows = cursor.fetchall()
        return [
            {
                "review_id": r[0],
                "model_a": r[1],
                "model_b": r[2],
                "verdict": r[3],
                "judge_type": r[4],
                "judge_id": r[5],
                "created_at": r[6],
            }
            for r in rows
        ]

    def get_elo_leaderboard(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return models ranked by ELO rating (head-to-head community standings)."""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT model_id, rating, wins, losses, draws, matches, updated_at "
                "FROM elo_ratings ORDER BY rating DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
        return [
            {
                "model_id": r[0],
                "rating": r[1],
                "wins": r[2],
                "losses": r[3],
                "draws": r[4],
                "matches": r[5],
                "updated_at": r[6],
            }
            for r in rows
        ]

    # ---- Monetization entities (open-question #4) ----

    def create_user(self, user_id: str, email: str = None, plan_key: str = "free",
                    stripe_customer_id: str = None) -> None:
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO users (user_id, email, plan_key, stripe_customer_id, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, email, plan_key, stripe_customer_id, int(time.time())),
            )
            self.conn.commit()

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT user_id, email, plan_key, stripe_customer_id, created_at FROM users WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "user_id": row[0], "email": row[1], "plan_key": row[2],
                "stripe_customer_id": row[3], "created_at": row[4],
            }

    def create_api_key(self, key: str, user_id: str, plan_key: str) -> None:
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO api_keys (key, user_id, plan_key, created_at, revoked_at) "
                "VALUES (?, ?, ?, ?, NULL)",
                (key, user_id, plan_key, int(time.time())),
            )
            self.conn.commit()

    def get_api_key_plan(self, key: str) -> Optional[str]:
        """Return the plan_key for a valid (non-revoked) API key, else None."""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT plan_key FROM api_keys WHERE key = ? AND revoked_at IS NULL",
                (key,),
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def revoke_api_key(self, key: str) -> None:
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE api_keys SET revoked_at = ? WHERE key = ?",
                (int(time.time()), key),
            )
            self.conn.commit()

    def create_organization(self, org_id: str, name: str = None,
                            certified_until: int = None) -> None:
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO organizations (org_id, name, certified_until, created_at) "
                "VALUES (?, ?, ?, ?)",
                (org_id, name, certified_until, int(time.time())),
            )
            self.conn.commit()

    def certify_organization(self, org_id: str, certified_until: int) -> None:
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE organizations SET certified_until = ? WHERE org_id = ?",
                (certified_until, org_id),
            )
            self.conn.commit()

    def get_organization(self, org_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT org_id, name, certified_until, created_at FROM organizations WHERE org_id = ?",
                (org_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {"org_id": row[0], "name": row[1],
                    "certified_until": row[2], "created_at": row[3]}

    def clear_expired(self):
        now = int(time.time())
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM models WHERE ? - timestamp >= ?", (now, 24 * 3600))
            cursor.execute("DELETE FROM eval_results WHERE ? - timestamp >= ?", (now, 6 * 3600))
            cursor.execute("DELETE FROM scores WHERE ? - timestamp >= ?", (now, 24 * 3600))
            cursor.execute("DELETE FROM leaderboard_bounds WHERE ? - timestamp >= ?", (now, 24 * 3600))
            self.conn.commit()
