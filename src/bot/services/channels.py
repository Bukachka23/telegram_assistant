"""Channel monitoring and on-demand query service."""

import logging
from datetime import datetime, timedelta, timezone

from telethon import TelegramClient

from bot.domain.exceptions import ChannelError

logger = logging.getLogger(__name__)


class ChannelService:
    """Fetches and searches messages from public Telegram channels via Telethon."""

    def __init__(self, client: TelegramClient) -> None:
        self._client = client

    async def fetch_messages(
        self,
        channel: str,
        limit: int = 20,
        query: str = "",
    ) -> str:
        """Fetch recent messages from a channel, optionally filtered by keyword."""
        limit = min(limit, 100)
        try:
            entity = await self._client.get_entity(channel)
            messages = await self._client.get_messages(entity, limit=limit)
        except Exception as e:
            raise ChannelError(f"Failed to fetch from {channel}: {e}") from e

        lines = []
        for msg in messages:
            if not msg.text:
                continue
            if query and query.lower() not in msg.text.lower():
                continue
            ts = msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else "?"
            lines.append(f"[{ts}] {msg.text[:500]}")

        if not lines:
            return f"No messages found in {channel}" + (f" matching '{query}'" if query else "")
        return f"Messages from {channel} ({len(lines)}):\n\n" + "\n\n".join(lines)

    async def search_channel(
        self,
        channel: str,
        query: str,
        days: int = 7,
        limit: int = 20,
    ) -> str:
        """Search a channel for messages matching a query within a time window."""
        limit = min(limit, 100)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        try:
            entity = await self._client.get_entity(channel)
            messages = await self._client.get_messages(
                entity, limit=limit, search=query
            )
        except Exception as e:
            raise ChannelError(f"Failed to search {channel}: {e}") from e

        lines = []
        for msg in messages:
            if not msg.text:
                continue
            if msg.date and msg.date < cutoff:
                continue
            ts = msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else "?"
            lines.append(f"[{ts}] {msg.text[:500]}")

        if not lines:
            return f"No messages in {channel} matching '{query}' (last {days} days)"
        return f"Search results for '{query}' in {channel} ({len(lines)}):\n\n" + "\n\n".join(lines)
