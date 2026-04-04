"""SQLite-backed storage for request metrics."""

import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

import aiosqlite

from bot.domain.models.metrics import RequestMetric

logger = logging.getLogger(__name__)

_SCHEMA = """
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

_INSERT = """
INSERT INTO request_metrics
    (model, tokens_in, tokens_out, cost_usd, latency_ms, ttfb_ms,
     tool_names, is_error, error_text, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

_QUERY_AGGREGATED = """
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

_QUERY_TOOL_NAMES = """
SELECT tool_names FROM request_metrics
WHERE tool_names != '' {and_where}
"""


class MetricsStore:
    """SQLite-backed storage for per-request telemetry."""

    def __init__(self, db_path: str, *, db: aiosqlite.Connection | None = None) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = db
        self._owns_connection: bool = db is None

    def _get_db(self) -> aiosqlite.Connection:
        if self._db is None:
            msg = "MetricsStore not initialized — call init() first"
            raise RuntimeError(msg)
        return self._db

    async def init(self) -> None:
        """Open (or reuse) a database connection and ensure the schema exists."""
        if self._owns_connection:
            db_path = Path(self._db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self._db = await aiosqlite.connect(db_path)
            self._db.row_factory = aiosqlite.Row
        db = self._get_db()
        await db.executescript(_SCHEMA)
        await db.commit()
        count = await self.count()
        logger.info("Metrics store ready: %d records in %s", count, self._db_path)

    async def record(self, metric: RequestMetric) -> None:
        """Insert a metric row. Errors are logged and swallowed."""
        try:
            db = self._get_db()
            await db.execute(_INSERT, (
                metric.model,
                metric.tokens_in,
                metric.tokens_out,
                metric.cost_usd,
                metric.latency_ms,
                metric.ttfb_ms,
                metric.tool_names,
                int(metric.is_error),
                metric.error_text,
                datetime.now(UTC).isoformat(),
            ))
            await db.commit()
        except Exception:  # noqa: BLE001
            logger.warning("Failed to record metric", exc_info=True)

    async def query(self, days: int = 7) -> list[aiosqlite.Row]:
        """Return aggregated metrics grouped by model."""
        db = self._get_db()
        if days > 0:
            cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
            sql = _QUERY_AGGREGATED.format(where="WHERE created_at >= ?")
            cursor = await db.execute(sql, (cutoff,))
        else:
            sql = _QUERY_AGGREGATED.format(where="")
            cursor = await db.execute(sql)
        return await cursor.fetchall()

    async def query_tool_names(self, days: int = 7) -> list[str]:
        """Return non-empty tool_names strings within the time window."""
        db = self._get_db()
        if days > 0:
            cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
            sql = _QUERY_TOOL_NAMES.format(and_where="AND created_at >= ?")
            cursor = await db.execute(sql, (cutoff,))
        else:
            sql = _QUERY_TOOL_NAMES.format(and_where="")
            cursor = await db.execute(sql)
        rows = await cursor.fetchall()
        return [row["tool_names"] for row in rows]

    async def count(self) -> int:
        """Return total number of metric records."""
        db = self._get_db()
        cursor = await db.execute("SELECT COUNT(*) FROM request_metrics")
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def close(self) -> None:
        """Close the connection only when this store owns it."""
        if self._owns_connection and self._db:
            await self._db.close()
