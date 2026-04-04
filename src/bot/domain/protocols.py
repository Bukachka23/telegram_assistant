from collections.abc import Awaitable, Callable
from typing import Protocol

from bot.domain.models import PersistedMonitor

ResolvedChannel = str | int
MessageFetcher = Callable[[ResolvedChannel, int, str | None], Awaitable[list]]


class TelegramEntity(Protocol):
    """Minimal structural type for a Telethon entity (channel / chat / user)."""

    id: int
    username: str | None
    title: str | None


class MonitorResolver(Protocol):
    async def resolve_for_owner(self, owner_user_id: int, channel_ref: str) -> PersistedMonitor | None: ...


class SupportsGetEntity(Protocol):
    async def get_entity(self, channel_ref: str) -> TelegramEntity: ...
