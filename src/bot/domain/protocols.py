from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from bot.domain.models import ForwardedChatLike, MonitorDisplay, PersistedMonitor

ResolvedChannel = str | int
MessageFetcher = Callable[[ResolvedChannel, int, str | None], Awaitable[list]]


class TelegramEntity(Protocol):
    """Minimal structural type for a Telethon entity (channel / chat / user)."""

    id: int
    username: str | None
    title: str | None


ProgressCallback = Callable[[str], Awaitable[None]]


class MonitorResolver(Protocol):
    async def resolve_for_owner(self, owner_user_id: int, channel_ref: str) -> PersistedMonitor | None: ...


class SupportsGetEntity(Protocol):
    async def get_entity(self, channel_ref: str) -> TelegramEntity: ...


class SearchClientProtocol(Protocol):
    """Structural interface for any search source accepted by WebSearchRouter."""

    async def search(self, query: str, *, max_results: int = 5) -> str: ...
    async def close(self) -> None: ...


class MonitorServiceProtocol(Protocol):
    """Structural interface for monitor management used by command handlers."""

    async def list_monitors(self, owner_user_id: int) -> Sequence[MonitorDisplay]: ...
    def begin_pending_add(self, owner_user_id: int, keywords: list[str]) -> None: ...
    def has_pending_add(self, owner_user_id: int) -> bool: ...
    async def add_public_monitor(
        self, *, owner_user_id: int, channel_ref: str, keywords: list[str]
    ) -> MonitorDisplay: ...
    async def add_forwarded_monitor(
        self, *, owner_user_id: int, forwarded_chat: ForwardedChatLike
    ) -> MonitorDisplay: ...
    async def remove_monitor(self, owner_user_id: int, identifier: str) -> bool: ...


class DeepResearchServiceProtocol(Protocol):
    """Structural interface for the deep research service used by command handlers."""

    async def run(
        self,
        *,
        query: str,
        model: str,
        on_progress: ProgressCallback | None = None,
        max_cycles: int = 3,
    ) -> str: ...


class LLMServiceProtocol(Protocol):
    """Structural interface for the LLM service used by DeepResearchService."""

    async def complete_side_context(
        self,
        *,
        messages: list[dict],
        model: str,
        allowed_tools: list[str] | None,
        temperature: float | None,
        max_tokens: int | None,
    ) -> str: ...
