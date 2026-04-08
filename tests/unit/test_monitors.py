"""Tests for persisted channel monitor storage."""

import asyncio
from collections.abc import AsyncGenerator
from types import SimpleNamespace

import pytest

from bot.infrastructure.storage.monitor_storage import MonitorStore
from bot.services.monitors import MonitorService


@pytest.fixture
async def store(tmp_path) -> AsyncGenerator[MonitorStore, None]:
    monitor_store = MonitorStore(str(tmp_path / "monitors.db"))
    await monitor_store.init()
    yield monitor_store
    await monitor_store.close()


@pytest.mark.asyncio
async def test_init_creates_monitor_schema(tmp_path) -> None:
    db_path = tmp_path / "nested" / "monitors.db"
    store = MonitorStore(str(db_path))

    await store.init()

    assert db_path.exists()
    await store.close()


@pytest.mark.asyncio
async def test_upsert_and_list_monitors(store: MonitorStore) -> None:
    await store.upsert_monitor(
        owner_user_id=1,
        chat_id=1001,
        username="@python",
        title="Python News",
        keywords=["asyncio", "telethon"],
        source_type="public_username",
    )

    monitors = await store.list_monitors(owner_user_id=1)

    assert len(monitors) == 1
    assert monitors[0].chat_id == 1001
    assert monitors[0].username == "@python"
    assert monitors[0].keywords == ["asyncio", "telethon"]


@pytest.mark.asyncio
async def test_upsert_replaces_existing_monitor_for_same_chat(store: MonitorStore) -> None:
    await store.upsert_monitor(
        owner_user_id=1,
        chat_id=1001,
        username="@python",
        title="Python News",
        keywords=["asyncio"],
        source_type="public_username",
    )
    await store.upsert_monitor(
        owner_user_id=1,
        chat_id=1001,
        username="@python",
        title="Python Updates",
        keywords=["ai"],
        source_type="public_username",
    )

    monitors = await store.list_monitors(owner_user_id=1)

    assert len(monitors) == 1
    assert monitors[0].title == "Python Updates"
    assert monitors[0].keywords == ["ai"]


@pytest.mark.asyncio
async def test_get_monitor_by_chat_id_returns_persisted_monitor(store: MonitorStore) -> None:
    await store.upsert_monitor(
        owner_user_id=1,
        chat_id=-100123,
        username="",
        title="Private Channel",
        keywords=[],
        source_type="forwarded_private",
    )

    monitor = await store.get_monitor_by_chat_id(-100123)

    assert monitor is not None
    assert monitor.title == "Private Channel"
    assert monitor.source_type == "forwarded_private"


@pytest.mark.asyncio
async def test_remove_monitor_by_username(store: MonitorStore) -> None:
    await store.upsert_monitor(
        owner_user_id=1,
        chat_id=1001,
        username="@python",
        title="Python News",
        keywords=[],
        source_type="public_username",
    )

    removed = await store.remove_monitor(owner_user_id=1, identifier="@python")
    monitors = await store.list_monitors(owner_user_id=1)

    assert removed is True
    assert monitors == []


@pytest.mark.asyncio
async def test_remove_monitor_by_chat_id_string(store: MonitorStore) -> None:
    await store.upsert_monitor(
        owner_user_id=1,
        chat_id=-100123,
        username="",
        title="Private Channel",
        keywords=[],
        source_type="forwarded_private",
    )

    removed = await store.remove_monitor(owner_user_id=1, identifier="-100123")
    monitors = await store.list_monitors(owner_user_id=1)

    assert removed is True
    assert monitors == []


class FakeTelethonClient:
    def __init__(self, entity) -> None:
        self._entity = entity
        self.calls: list[str] = []

    async def get_entity(self, channel_ref: str):
        self.calls.append(channel_ref)
        return self._entity


@pytest.mark.asyncio
async def test_begin_pending_add_marks_owner_as_waiting(store: MonitorStore) -> None:
    service = MonitorService(store=store, client=None)

    service.begin_pending_add(owner_user_id=1, keywords=["python"])
    await asyncio.sleep(0)

    assert service.has_pending_add(1) is True


@pytest.mark.asyncio
async def test_add_public_monitor_resolves_and_persists_channel(store: MonitorStore) -> None:
    entity = SimpleNamespace(id=2001, title="Public Channel", username="publicchan")
    service = MonitorService(store=store, client=FakeTelethonClient(entity))

    monitor = await service.add_public_monitor(
        owner_user_id=1,
        channel_ref="@publicchan",
        keywords=["ai"],
    )
    persisted = await store.list_monitors(1)

    assert monitor.chat_id == 2001
    assert monitor.username == "@publicchan"
    assert monitor.keywords == ["ai"]
    assert persisted[0].title == "Public Channel"


@pytest.mark.asyncio
async def test_add_forwarded_monitor_persists_private_channel_and_clears_pending(
    store: MonitorStore,
) -> None:
    service = MonitorService(store=store, client=None)
    forwarded_chat = SimpleNamespace(id=-10055, title="Private Channel", username=None)
    service.begin_pending_add(owner_user_id=1, keywords=["gym"])

    monitor = await service.add_forwarded_monitor(
        owner_user_id=1,
        forwarded_chat=forwarded_chat,
    )

    assert monitor.chat_id == -10055
    assert monitor.title == "Private Channel"
    assert monitor.source_type == "forwarded_private"
    assert monitor.keywords == ["gym"]
    assert service.has_pending_add(1) is False


@pytest.mark.asyncio
async def test_add_forwarded_monitor_rejects_invalid_forward_and_keeps_pending(
    store: MonitorStore,
) -> None:
    service = MonitorService(store=store, client=None)
    service.begin_pending_add(owner_user_id=1, keywords=[])

    with pytest.raises(ValueError, match="forwarded channel"):
        await service.add_forwarded_monitor(
            owner_user_id=1,
            forwarded_chat=SimpleNamespace(title="Missing ID"),
        )

    assert service.has_pending_add(1) is True
