-- ModelRank SQLite Schema (aligned with cache.py runtime schema)
-- Uses WAL mode for concurrent read performance

CREATE TABLE IF NOT EXISTS models (
    model_id TEXT PRIMARY KEY,
    data TEXT NOT NULL,           -- JSON blob of normalized model metadata
    timestamp INTEGER NOT NULL    -- Unix epoch when cached
);

CREATE TABLE IF NOT EXISTS eval_results (
    model_id TEXT PRIMARY KEY,
    results TEXT NOT NULL,        -- JSON array of eval result objects
    timestamp INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS scores (
    model_id TEXT PRIMARY KEY,
    score_data TEXT NOT NULL,     -- JSON blob of full score dict
    timestamp INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS achievements (
    model_id TEXT NOT NULL,
    achievement_type TEXT NOT NULL,
    awarded_at INTEGER NOT NULL,
    PRIMARY KEY (model_id, achievement_type)
);

CREATE TABLE IF NOT EXISTS leaderboard_bounds (
    benchmark_id TEXT PRIMARY KEY,
    min_score REAL,
    max_score REAL,
    total_models INTEGER,
    timestamp INTEGER NOT NULL
);

-- Head-to-head ELO + comparison history (open-question #6 / #2)
CREATE TABLE IF NOT EXISTS elo_ratings (
    model_id   TEXT PRIMARY KEY,
    rating     REAL NOT NULL DEFAULT 1500.0,
    wins       INTEGER NOT NULL DEFAULT 0,
    losses     INTEGER NOT NULL DEFAULT 0,
    draws      INTEGER NOT NULL DEFAULT 0,
    matches    INTEGER NOT NULL DEFAULT 0,
    updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id  TEXT PRIMARY KEY,
    model_a    TEXT NOT NULL,
    model_b    TEXT NOT NULL,
    verdict    TEXT NOT NULL,        -- 'A' | 'B' | 'tie'
    judge_type TEXT NOT NULL,        -- 'human' | 'llm'
    judge_id   TEXT,
    created_at INTEGER NOT NULL
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_models_timestamp      ON models(timestamp);
CREATE INDEX IF NOT EXISTS idx_scores_timestamp      ON scores(timestamp);
CREATE INDEX IF NOT EXISTS idx_eval_results_timestamp ON eval_results(timestamp);
CREATE INDEX IF NOT EXISTS idx_elo_rating           ON elo_ratings(rating);
CREATE INDEX IF NOT EXISTS idx_reviews_created      ON reviews(created_at);

-- Monetization entities (open-question #4): users, API keys, org certification
CREATE TABLE IF NOT EXISTS users (
    user_id           TEXT PRIMARY KEY,
    email             TEXT UNIQUE,
    plan_key          TEXT NOT NULL DEFAULT 'free',
    stripe_customer_id TEXT,
    created_at        INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS api_keys (
    key          TEXT PRIMARY KEY,
    user_id      TEXT NOT NULL,
    plan_key     TEXT NOT NULL,
    created_at   INTEGER NOT NULL,
    revoked_at   INTEGER
);

CREATE TABLE IF NOT EXISTS organizations (
    org_id           TEXT PRIMARY KEY,
    name             TEXT,
    certified_until  INTEGER,
    created_at       INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_api_keys_user     ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email      ON users(email);
