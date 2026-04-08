"""Tests for system health service."""

from datetime import UTC, datetime, timedelta

import pytest

from bot.services.health import HealthReport, HealthService
from bot.services.health_formatter import format_health_report


@pytest.fixture
def health() -> HealthService:
    return HealthService(
        start_time=datetime.now(UTC) - timedelta(hours=2, minutes=15),
        model="test/model-v1",
        vault_path="/tmp/vault",
    )


class TestHealthReport:
    def test_format_telegram_contains_key_sections(self):
        report = HealthReport(
            uptime=timedelta(hours=3, minutes=42),
            python_version="3.14.0",
            platform="Darwin arm64",
            model="anthropic/claude-sonnet-4",
            memory_count=42,
            monitor_count=3,
            vault_path="/home/user/vault",
            vault_note_count=120,
            telethon_connected=True,
            tavily_available=True,
            deep_research_available=True,
        )
        text = format_health_report(report)

        assert "System Status" in text
        assert "3h 42m" in text
        assert "3.14.0" in text
        assert "anthropic/claude-sonnet-4" in text
        assert "✅ Telethon" in text
        assert "✅ Web search" in text
        assert "✅ Deep research" in text
        assert "42" in text
        assert "120" in text
        assert "Issues" not in text

    def test_format_telegram_shows_errors(self):
        report = HealthReport(
            uptime=timedelta(minutes=5),
            python_version="3.14.0",
            platform="Linux x86_64",
            model="test-model",
            memory_count=0,
            monitor_count=0,
            vault_path="/tmp",
            vault_note_count=0,
            telethon_connected=False,
            tavily_available=False,
            deep_research_available=True,
            errors=["Memory store: connection failed"],
        )
        text = format_health_report(report)

        assert "❌ Telethon" in text
        assert "❌ Web search" in text
        assert "Issues" in text
        assert "Memory store: connection failed" in text

    def test_format_uptime_days(self):
        report = HealthReport(
            uptime=timedelta(days=2, hours=5),
            python_version="3.14.0",
            platform="Linux",
            model="m",
            memory_count=0,
            monitor_count=0,
            vault_path="/tmp",
            vault_note_count=0,
            telethon_connected=False,
            tavily_available=False,
            deep_research_available=False,
        )
        text = format_health_report(report)
        assert "2d 5h" in text


class TestHealthService:
    @pytest.mark.asyncio
    async def test_check_returns_report_with_correct_model(self, health):
        report = await health.check()

        assert report.model == "test/model-v1"
        assert report.vault_path == "/tmp/vault"
        assert report.uptime.total_seconds() > 0

    @pytest.mark.asyncio
    async def test_check_without_stores_returns_zero_counts(self, health):
        report = await health.check()

        assert report.memory_count == 0
        assert report.monitor_count == 0
        assert report.vault_note_count == 0
        assert report.errors == []

    @pytest.mark.asyncio
    async def test_check_reflects_service_flags(self, health):
        health.set_telethon_connected(connected=True)
        health.set_tavily_available(available=True)
        health.set_deep_research_available(available=True)

        report = await health.check()

        assert report.telethon_connected is True
        assert report.tavily_available is True
        assert report.deep_research_available is True

    @pytest.mark.asyncio
    async def test_check_captures_store_errors_gracefully(self, health):
        class BrokenStore:
            async def list_recent(self, **kwargs):
                msg = "db locked"
                raise RuntimeError(msg)

            async def _count(self):
                msg = "db locked"
                raise RuntimeError(msg)

        health.set_memory_store(BrokenStore())
        report = await health.check()

        assert report.memory_count == 0
        assert any("Memory store" in e for e in report.errors)
