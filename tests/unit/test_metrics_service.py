"""Tests for MetricsService — aggregation and /stats formatting."""

from unittest.mock import AsyncMock

import pytest

from bot.services.metrics import MetricsService


def _make_row(
    model="test-model",
    requests=10,
    avg_tokens_in=500,
    avg_tokens_out=1200,
    avg_latency_ms=2500,
    avg_ttfb_ms=600,
    total_cost=0.15,
    error_count=1,
):
    """Build a dict that mimics an aiosqlite.Row from the aggregated query."""
    return {
        "model": model,
        "requests": requests,
        "avg_tokens_in": avg_tokens_in,
        "avg_tokens_out": avg_tokens_out,
        "avg_latency_ms": avg_latency_ms,
        "avg_ttfb_ms": avg_ttfb_ms,
        "total_cost": total_cost,
        "error_count": error_count,
    }


class FakeMetricsStore:
    def __init__(self, rows=None, tool_names=None, count=0):
        self._rows = rows or []
        self._tool_names = tool_names or []
        self._count = count

    async def query(self, days=7):
        return self._rows

    async def query_tool_names(self, days=7):
        return self._tool_names

    async def count(self):
        return self._count


class TestBuildStats:
    async def test_no_data_shows_empty_message(self):
        store = FakeMetricsStore()
        service = MetricsService(store=store)
        text = await service.build_stats(days=7)
        assert "No requests" in text

    async def test_single_model_stats(self):
        store = FakeMetricsStore(
            rows=[_make_row(model="claude-sonnet", requests=47, avg_tokens_in=1200,
                            avg_tokens_out=2900, avg_latency_ms=3200, avg_ttfb_ms=800,
                            total_cost=0.42, error_count=2)],
        )
        service = MetricsService(store=store)
        text = await service.build_stats(days=7)

        assert "last 7 days" in text
        assert "claude-sonnet" in text
        assert "47" in text
        assert "1.2K" in text  # avg tokens in
        assert "2.9K" in text  # avg tokens out
        assert "3.2s" in text  # latency
        assert "0.8s" in text  # ttfb
        assert "$0.42" in text
        assert "2" in text  # errors

    async def test_multiple_models(self):
        store = FakeMetricsStore(
            rows=[
                _make_row(model="claude", requests=30),
                _make_row(model="gemini", requests=15),
            ],
        )
        service = MetricsService(store=store)
        text = await service.build_stats(days=7)
        assert "claude" in text
        assert "gemini" in text

    async def test_null_cost_shows_na(self):
        store = FakeMetricsStore(
            rows=[_make_row(total_cost=None)],
        )
        service = MetricsService(store=store)
        text = await service.build_stats(days=7)
        assert "n/a" in text

    async def test_zero_errors_shows_clean(self):
        store = FakeMetricsStore(
            rows=[_make_row(error_count=0)],
        )
        service = MetricsService(store=store)
        text = await service.build_stats(days=7)
        assert "0" in text

    async def test_tool_names_counted(self):
        store = FakeMetricsStore(
            rows=[_make_row()],
            tool_names=["web_search,recall_memory", "web_search", "search_vault"],
        )
        service = MetricsService(store=store)
        text = await service.build_stats(days=7)
        assert "web_search" in text
        assert "×2" in text  # web_search appears twice
        assert "recall_memory" in text
        assert "search_vault" in text

    async def test_today_window_label(self):
        store = FakeMetricsStore(rows=[_make_row()])
        service = MetricsService(store=store)
        text = await service.build_stats(days=1)
        assert "today" in text.lower() or "last 1 day" in text.lower()

    async def test_all_time_window_label(self):
        store = FakeMetricsStore(rows=[_make_row()])
        service = MetricsService(store=store)
        text = await service.build_stats(days=0)
        assert "all time" in text.lower()

    async def test_total_requests_in_header(self):
        store = FakeMetricsStore(
            rows=[
                _make_row(model="a", requests=30),
                _make_row(model="b", requests=20),
            ],
        )
        service = MetricsService(store=store)
        text = await service.build_stats(days=7)
        assert "50 requests" in text


class TestFormatTokens:
    def test_format_small_number(self):
        assert MetricsService._format_tokens(500) == "500"

    def test_format_thousands(self):
        assert MetricsService._format_tokens(1200) == "1.2K"

    def test_format_exact_thousand(self):
        assert MetricsService._format_tokens(1000) == "1.0K"

    def test_format_large(self):
        assert MetricsService._format_tokens(15600) == "15.6K"

    def test_format_zero(self):
        assert MetricsService._format_tokens(0) == "0"


class TestFormatLatency:
    def test_format_milliseconds(self):
        assert MetricsService._format_latency_ms(800) == "0.8s"

    def test_format_seconds(self):
        assert MetricsService._format_latency_ms(3200) == "3.2s"

    def test_format_zero(self):
        assert MetricsService._format_latency_ms(0) == "0.0s"
