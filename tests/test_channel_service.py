"""Tests for channel service resilience and formatting."""

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from bot.domain.exceptions import ChannelError
from bot.domain.models import PersistedMonitor
from bot.services.channels import ChannelService


class FakeTelegramClient:
    """Small async fake for ChannelService tests."""

    def __init__(self, messages: list[SimpleNamespace]) -> None:
        self._messages = messages
        self.entity_calls = 0
        self.message_calls = 0
        self.search_queries: list[str] = []
        self.slow_message_calls = 0
        self.entity_inputs: list[str | int] = []

    async def get_entity(self, channel: str | int) -> str | int:
        await asyncio.sleep(0)
        self.entity_calls += 1
        self.entity_inputs.append(channel)
        return channel

    async def get_messages(
        self,
        entity: str,
        *,
        limit: int,
        search: str | None = None,
    ) -> list[SimpleNamespace]:
        await asyncio.sleep(0)
        del entity
        self.message_calls += 1
        if search is not None:
            self.search_queries.append(search)
        return self._messages[:limit]


class SlowThenSuccessfulClient(FakeTelegramClient):
    async def get_messages(
        self,
        entity: str,
        *,
        limit: int,
        search: str | None = None,
    ) -> list[SimpleNamespace]:
        del entity, search
        self.message_calls += 1
        if self.message_calls == 1:
            await asyncio.sleep(0.02)
        else:
            await asyncio.sleep(0)
        return self._messages[:limit]


class AlwaysSlowClient(FakeTelegramClient):
    async def get_messages(
        self,
        entity: str,
        *,
        limit: int,
        search: str | None = None,
    ) -> list[SimpleNamespace]:
        del entity, limit, search
        self.message_calls += 1
        await asyncio.sleep(0.02)
        return self._messages


class FakeMonitorService:
    def __init__(self, monitor: PersistedMonitor | None = None) -> None:
        self._monitor = monitor
        self.lookups: list[tuple[int, str]] = []

    async def resolve_for_owner(
        self,
        owner_user_id: int,
        channel_ref: str,
    ) -> PersistedMonitor | None:
        self.lookups.append((owner_user_id, channel_ref))
        return self._monitor


def _message(text: str, *, days_ago: int = 0) -> SimpleNamespace:
    return SimpleNamespace(
        text=text,
        date=datetime.now(UTC) - timedelta(days=days_ago),
    )


@pytest.mark.asyncio
async def test_fetch_messages_filters_and_formats_results() -> None:
    client = FakeTelegramClient(
        [
            _message("Asyncio release notes"),
            _message("Other update"),
        ]
    )
    service = ChannelService(client)

    result = await service.fetch_messages("@python", query="asyncio")

    assert "Messages from @python (1):" in result
    assert "Asyncio release notes" in result
    assert "Other update" not in result


@pytest.mark.asyncio
async def test_fetch_messages_retries_after_timeout_and_succeeds() -> None:
    client = SlowThenSuccessfulClient([_message("Recovered message")])
    service = ChannelService(
        client,
        request_timeout_seconds=0.005,
        retry_max_attempts=2,
        retry_base_delay_seconds=0.001,
    )

    result = await service.fetch_messages("@python")

    assert "Recovered message" in result
    assert client.message_calls == 2
    assert client.entity_calls == 2


@pytest.mark.asyncio
async def test_fetch_messages_wraps_final_timeout_as_channel_error() -> None:
    client = AlwaysSlowClient([_message("Never returned")])
    service = ChannelService(
        client,
        request_timeout_seconds=0.005,
        retry_max_attempts=2,
        retry_base_delay_seconds=0.001,
    )

    with pytest.raises(ChannelError, match="Failed to fetch from @python"):
        await service.fetch_messages("@python")

    assert client.message_calls == 2


@pytest.mark.asyncio
async def test_search_channel_passes_search_query_and_filters_old_messages() -> None:
    client = FakeTelegramClient(
        [
            _message("Fresh asyncio match", days_ago=1),
            _message("Old asyncio match", days_ago=30),
        ]
    )
    service = ChannelService(client)

    result = await service.search_channel("@python", query="asyncio", days=7)

    assert "Search results for 'asyncio' in @python (1):" in result
    assert "Fresh asyncio match" in result
    assert "Old asyncio match" not in result
    assert client.search_queries == ["asyncio"]


@pytest.mark.asyncio
async def test_fetch_messages_resolves_persisted_private_monitor_before_telethon_lookup() -> None:
    client = FakeTelegramClient([_message("Private channel update")])
    monitor_service = FakeMonitorService(
        PersistedMonitor(
            owner_user_id=504576529,
            chat_id=-1002283310339,
            title="GlebRepich",
            username="",
            keywords=[],
            source_type="forwarded_private",
        )
    )
    service = ChannelService(
        client,
        monitor_service=monitor_service,
        owner_user_id=504576529,
    )

    result = await service.fetch_messages("GlebRepich")

    assert "Messages from GlebRepich (1):" in result
    assert client.entity_inputs == [-1002283310339]
    assert monitor_service.lookups == [(504576529, "GlebRepich")]


@pytest.mark.asyncio
async def test_search_channel_uses_persisted_monitor_resolution() -> None:
    client = FakeTelegramClient([_message("Private asyncio match")])
    monitor_service = FakeMonitorService(
        PersistedMonitor(
            owner_user_id=504576529,
            chat_id=-1002283310339,
            title="GlebRepich",
            username="",
            keywords=[],
            source_type="forwarded_private",
        )
    )
    service = ChannelService(
        client,
        monitor_service=monitor_service,
        owner_user_id=504576529,
    )

    result = await service.search_channel("GlebRepich", query="asyncio")

    assert "Search results for 'asyncio' in GlebRepich (1):" in result
    assert client.entity_inputs == [-1002283310339]
    assert client.search_queries == ["asyncio"]
