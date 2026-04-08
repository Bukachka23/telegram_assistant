import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

import aiosqlite

from bot.domain.models.metrics import RequestMetric
from bot.infrastructure.storage.schemas import (
    METRIC_INSERT,
    METRIC_QUERY_AGGREGATED,
    METRIC_QUERY_TOOL_NAMES,
    METRIC_SCHEMA,
)

logger = logging.getLogger(__name__)


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
        await db.executescript(METRIC_SCHEMA)
        await db.commit()
        count = await self.count()
        logger.info("Metrics store ready: %d records in %s", count, self._db_path)

    async def record(self, metric: RequestMetric) -> None:
        """Insert a metric row. Errors are logged and swallowed."""
        try:
            db = self._get_db()
            await db.execute(METRIC_INSERT, (
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
        except Exception:
            logger.warning("Failed to record metric", exc_info=True)

    async def query(self, days: int = 7) -> list[aiosqlite.Row]:
        """Return aggregated metrics grouped by model."""
        db = self._get_db()
        if days > 0:
            cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
            sql = METRIC_QUERY_AGGREGATED.format(where="WHERE created_at >= ?")
            cursor = await db.execute(sql, (cutoff,))
        else:
            sql = METRIC_QUERY_AGGREGATED.format(where="")
            cursor = await db.execute(sql)
        return await cursor.fetchall()

    async def query_tool_names(self, days: int = 7) -> list[str]:
        """Return non-empty tool_names strings within the time window."""
        db = self._get_db()
        if days > 0:
            cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
            sql = METRIC_QUERY_TOOL_NAMES.format(and_where="AND created_at >= ?")
            cursor = await db.execute(sql, (cutoff,))
        else:
            sql = METRIC_QUERY_TOOL_NAMES.format(and_where="")
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
