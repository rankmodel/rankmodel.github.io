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

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_models_timestamp      ON models(timestamp);
CREATE INDEX IF NOT EXISTS idx_scores_timestamp      ON scores(timestamp);
CREATE INDEX IF NOT EXISTS idx_eval_results_timestamp ON eval_results(timestamp);
