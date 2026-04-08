# Memory Schema
MEMORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fact TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
USING fts5(fact, category, content=memories, content_rowid=id);

CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
    INSERT INTO memories_fts(rowid, fact, category)
    VALUES (new.id, new.fact, new.category);
END;

CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, fact, category)
    VALUES ('delete', old.id, old.fact, old.category);
END;
"""

# Monitor Schema
MONITOR_SCHEMA = """
CREATE TABLE IF NOT EXISTS channel_monitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL UNIQUE,
    username TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL,
    keywords_json TEXT NOT NULL DEFAULT '[]',
    source_type TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_channel_monitors_owner_user_id
ON channel_monitors(owner_user_id);
"""


# Metric Storage
METRIC_SCHEMA = """
CREATE TABLE IF NOT EXISTS request_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model TEXT NOT NULL,
    tokens_in INTEGER NOT NULL DEFAULT 0,
    tokens_out INTEGER NOT NULL DEFAULT 0,
    cost_usd REAL,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    ttfb_ms INTEGER NOT NULL DEFAULT 0,
    tool_names TEXT NOT NULL DEFAULT '',
    is_error INTEGER NOT NULL DEFAULT 0,
    error_text TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_request_metrics_created_at
ON request_metrics(created_at);

CREATE INDEX IF NOT EXISTS idx_request_metrics_model
ON request_metrics(model);
"""

METRIC_INSERT = """
INSERT INTO request_metrics
    (model, tokens_in, tokens_out, cost_usd, latency_ms, ttfb_ms,
     tool_names, is_error, error_text, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

METRIC_QUERY_AGGREGATED = """
SELECT
    model,
    COUNT(*) as requests,
    CAST(AVG(tokens_in) AS INTEGER) as avg_tokens_in,
    CAST(AVG(tokens_out) AS INTEGER) as avg_tokens_out,
    AVG(latency_ms) as avg_latency_ms,
    AVG(ttfb_ms) as avg_ttfb_ms,
    SUM(cost_usd) as total_cost,
    SUM(is_error) as error_count
FROM request_metrics
{where}
GROUP BY model
ORDER BY requests DESC
"""

METRIC_QUERY_TOOL_NAMES = """
SELECT tool_names FROM request_metrics
WHERE tool_names != '' {and_where}
"""
