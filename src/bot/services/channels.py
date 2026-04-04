import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from telethon.errors import RPCError

from bot.config.constants import (
    CHANNEL_REQUEST_BASE_DELAY_SECONDS,
    CHANNEL_REQUEST_MAX_ATTEMPTS,
    CHANNEL_REQUEST_TIMEOUT_SECONDS,
    DAYS,
    LIMIT_CHANNELS,
    LIMIT_MESSAGES,
)
from bot.domain.exceptions import ChannelError
from bot.domain.protocols import MessageFetcher, MonitorResolver, ResolvedChannel
from bot.shared.decorators import enforce_timeout, retry_with_backoff

logger = logging.getLogger(__name__)


from bot.domain.models import PersistedMonitor  # noqa: E402 — after logger


def _find_matching_monitor(
    monitors: list[PersistedMonitor], chat_id: int, text: str
) -> PersistedMonitor | None:
    """Return the first monitor whose chat_id and keywords match *text*."""
    return next(
        (m for m in monitors if m.chat_id == chat_id and m.matches(text)),
        None,
    )


class ChannelService:
    """Fetches and searches messages from channels accessible to the userbot."""

    def __init__(
        self,
        client: Any,  # noqa: ANN401
        *,
        monitor_service: MonitorResolver | None = None,
        owner_user_id: int | None = None,
        request_timeout_seconds: float = CHANNEL_REQUEST_TIMEOUT_SECONDS,
        retry_max_attempts: int = CHANNEL_REQUEST_MAX_ATTEMPTS,
        retry_base_delay_seconds: float = CHANNEL_REQUEST_BASE_DELAY_SECONDS,
    ) -> None:
        self._client = client
        self._monitor_service = monitor_service
        self._owner_user_id = owner_user_id
        self._fetch_messages_with_resilience: MessageFetcher = retry_with_backoff(
            max_attempts=retry_max_attempts,
            base_delay_seconds=retry_base_delay_seconds,
            handled_exceptions=(TimeoutError,),
        )(
            enforce_timeout(timeout_seconds=request_timeout_seconds)(
                self._fetch_messages_once
            )
        )

    async def fetch_messages(self, channel: str, *, limit: int = LIMIT_MESSAGES, query: str = "") -> str:
        """Fetch recent messages from a channel, optionally filtered by keyword."""
        limit = min(limit, 100)
        resolved_channel = await self._resolve_channel(channel)
        try:
            messages = await self._fetch_messages_with_resilience(
                resolved_channel,
                limit,
                None,
            )
        except (OSError, RPCError, TimeoutError, ValueError) as error:
            msg = f"Failed to fetch from {channel}: {error}"
            raise ChannelError(msg) from error

        lines = []
        for message in messages:
            if not message.text:
                continue
            if query and query.lower() not in message.text.lower():
                continue
            ts = message.date.strftime("%Y-%m-%d %H:%M") if message.date else "?"
            lines.append(f"[{ts}] {message.text[:500]}")

        if not lines:
            suffix = f" matching '{query}'" if query else ""
            return f"No messages found in {channel}{suffix}"
        header = f"Messages from {channel} ({len(lines)}):"
        return f"{header}\n\n" + "\n\n".join(lines)

    async def search_channel(self, channel: str, query: str, *, days: int = DAYS, limit: int = LIMIT_CHANNELS) -> str:
        """Search a channel for messages matching a query within a time window."""
        limit = min(limit, 100)
        cutoff = datetime.now(UTC) - timedelta(days=days)
        resolved_channel = await self._resolve_channel(channel)

        try:
            messages = await self._fetch_messages_with_resilience(
                resolved_channel,
                limit,
                query,
            )
        except (OSError, RPCError, TimeoutError, ValueError) as error:
            msg = f"Failed to search {channel}: {error}"
            raise ChannelError(msg) from error

        lines = []
        for message in messages:
            if not message.text:
                continue
            if message.date and message.date < cutoff:
                continue
            ts = message.date.strftime("%Y-%m-%d %H:%M") if message.date else "?"
            lines.append(f"[{ts}] {message.text[:500]}")

        if not lines:
            return (
                f"No messages in {channel} matching "
                f"'{query}' (last {days} days)"
            )
        header = f"Search results for '{query}' in {channel} ({len(lines)}):"
        return f"{header}\n\n" + "\n\n".join(lines)

    async def _resolve_channel(self, channel_ref: str) -> ResolvedChannel:
        """Resolve a channel reference through persisted monitors when available."""
        if self._monitor_service is None or self._owner_user_id is None:
            return channel_ref

        monitor = await self._monitor_service.resolve_for_owner(
            self._owner_user_id,
            channel_ref,
        )
        if monitor is None:
            return channel_ref
        return monitor.chat_id

    async def _fetch_messages_once(self, channel: ResolvedChannel, limit: int, search_query: str | None) -> list[Any]:
        """Fetch messages from Telethon once, without retries or formatting."""
        entity = await self._client.get_entity(channel)
        if search_query:
            return cast("list[Any]", await self._client.get_messages(
                entity, limit=limit, search=search_query,
            ))
        return cast("list[Any]", await self._client.get_messages(entity, limit=limit))
