"""Tests for MetricsStore — SQLite request metrics storage."""

from datetime import UTC, datetime, timedelta

import aiosqlite
import pytest

from bot.domain.models.metrics import RequestMetric
from bot.infrastructure.storage.metrics_storage import MetricsStore


@pytest.fixture
async def store(tmp_path):
    db_path = str(tmp_path / "test.db")
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    s = MetricsStore(db_path=db_path, db=db)
    await s.init()
    yield s
    await db.close()


def _metric(**overrides) -> RequestMetric:
    defaults = {
        "model": "test-model",
        "tokens_in": 100,
        "tokens_out": 200,
        "cost_usd": 0.01,
        "latency_ms": 1500,
        "ttfb_ms": 300,
        "tool_names": "",
        "is_error": False,
        "error_text": "",
    }
    defaults.update(overrides)
    return RequestMetric(**defaults)


class TestMetricsStoreInit:
    async def test_init_creates_table(self, store: MetricsStore):
        count = await store.count()
        assert count == 0


class TestMetricsStoreRecord:
    async def test_record_and_count(self, store: MetricsStore):
        await store.record(_metric())
        assert await store.count() == 1

    async def test_record_multiple(self, store: MetricsStore):
        await store.record(_metric(model="model-a"))
        await store.record(_metric(model="model-b"))
        await store.record(_metric(model="model-a"))
        assert await store.count() == 3

    async def test_record_with_null_cost(self, store: MetricsStore):
        await store.record(_metric(cost_usd=None))
        assert await store.count() == 1

    async def test_record_with_error(self, store: MetricsStore):
        await store.record(_metric(is_error=True, error_text="timeout"))
        assert await store.count() == 1

    async def test_record_with_tool_names(self, store: MetricsStore):
        await store.record(_metric(tool_names="web_search,recall_memory"))
        assert await store.count() == 1


class TestMetricsStoreQuery:
    async def test_query_returns_aggregated_by_model(self, store: MetricsStore):
        await store.record(_metric(model="claude", tokens_in=100, tokens_out=200, latency_ms=1000))
        await store.record(_metric(model="claude", tokens_in=200, tokens_out=400, latency_ms=2000))
        await store.record(_metric(model="gemini", tokens_in=50, tokens_out=100, latency_ms=500))

        rows = await store.query(days=7)
        assert len(rows) == 2

        claude = next(r for r in rows if r["model"] == "claude")
        assert claude["requests"] == 2
        assert claude["avg_tokens_in"] == 150
        assert claude["avg_tokens_out"] == 300

        gemini = next(r for r in rows if r["model"] == "gemini")
        assert gemini["requests"] == 1

    async def test_query_filters_by_days(self, store: MetricsStore):
        # Record with recent timestamp
        await store.record(_metric(model="recent"))

        # Insert an old row directly
        db = store._get_db()
        old_date = (datetime.now(UTC) - timedelta(days=10)).isoformat()
        await db.execute(
            "INSERT INTO request_metrics"
            " (model, tokens_in, tokens_out, cost_usd, latency_ms,"
            " ttfb_ms, tool_names, is_error, error_text, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("old-model", 100, 200, 0.01, 1000, 300, "", 0, "", old_date),
        )
        await db.commit()

        rows = await store.query(days=7)
        assert len(rows) == 1
        assert rows[0]["model"] == "recent"

    async def test_query_all_with_days_zero(self, store: MetricsStore):
        await store.record(_metric(model="recent"))

        db = store._get_db()
        old_date = (datetime.now(UTC) - timedelta(days=100)).isoformat()
        await db.execute(
            "INSERT INTO request_metrics"
            " (model, tokens_in, tokens_out, cost_usd, latency_ms,"
            " ttfb_ms, tool_names, is_error, error_text, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("ancient", 50, 80, None, 500, 100, "", 0, "", old_date),
        )
        await db.commit()

        rows = await store.query(days=0)
        assert len(rows) == 2

    async def test_query_orders_by_request_count_desc(self, store: MetricsStore):
        await store.record(_metric(model="rare"))
        for _ in range(5):
            await store.record(_metric(model="popular"))

        rows = await store.query(days=7)
        assert rows[0]["model"] == "popular"
        assert rows[1]["model"] == "rare"

    async def test_query_error_count(self, store: MetricsStore):
        await store.record(_metric(model="m", is_error=False))
        await store.record(_metric(model="m", is_error=True))
        await store.record(_metric(model="m", is_error=True))

        rows = await store.query(days=7)
        assert rows[0]["error_count"] == 2


class TestMetricsStoreToolNames:
    async def test_query_tool_names(self, store: MetricsStore):
        await store.record(_metric(tool_names="web_search,recall_memory"))
        await store.record(_metric(tool_names="web_search"))
        await store.record(_metric(tool_names=""))

        names = await store.query_tool_names(days=7)
        assert len(names) == 2
        assert "web_search,recall_memory" in names
        assert "web_search" in names
