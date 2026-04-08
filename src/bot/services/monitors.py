import logging

from bot.domain.models import PersistedMonitor
from bot.domain.protocols import ForwardedChatLike, MonitorServiceProtocol, SupportsGetEntity
from bot.infrastructure.storage.monitor_storage import MonitorStore

logger = logging.getLogger(__name__)


class MonitorService(MonitorServiceProtocol):
    """Orchestrates public and private monitor setup on top of MonitorStore."""

    def __init__(self, store: MonitorStore, client: SupportsGetEntity | None) -> None:
        self._store = store
        self._client = client
        self._pending_adds: dict[int, list[str]] = {}
        self._monitors_cache: dict[int, list[PersistedMonitor]] = {}

    def begin_pending_add(self, owner_user_id: int, keywords: list[str]) -> None:
        """Mark the owner as waiting to forward a private channel message."""
        self._pending_adds[owner_user_id] = keywords

    def has_pending_add(self, owner_user_id: int) -> bool:
        """Return whether the owner is waiting to complete private setup."""
        return owner_user_id in self._pending_adds

    async def add_public_monitor(self, *, owner_user_id: int, channel_ref: str, keywords: list[str]) \
            -> PersistedMonitor:
        """Resolve a public channel reference and persist it as a monitor."""
        if self._client is None:
            msg = "Telethon is not available for channel resolution"
            raise ValueError(msg)

        entity = await self._client.get_entity(channel_ref)
        username = self._normalize_username(getattr(entity, "username", "") or channel_ref)
        entity_chat_id = int(entity.id)
        title = getattr(entity, "title", username or str(entity_chat_id))
        monitor = await self._store.upsert_monitor(
            owner_user_id=owner_user_id,
            chat_id=entity_chat_id,
            username=username,
            title=title,
            keywords=keywords,
            source_type="public_username",
        )
        self._invalidate_monitors_cache()
        return monitor

    async def add_forwarded_monitor(self, *, owner_user_id: int, forwarded_chat: ForwardedChatLike) -> PersistedMonitor:
        """Persist a monitor from a forwarded channel/chat object."""
        if not self.has_pending_add(owner_user_id):
            msg = "no pending private monitor setup for this user"
            raise ValueError(msg)

        chat_id = getattr(forwarded_chat, "id", None)
        title = getattr(forwarded_chat, "title", None)
        if chat_id is None or not title:
            msg = "forwarded channel information is incomplete"
            raise ValueError(msg)

        keywords = self._pending_adds[owner_user_id]
        username = self._normalize_username(getattr(forwarded_chat, "username", "") or "")
        source_type = "forwarded_private" if not username else "forwarded_channel"
        monitor = await self._store.upsert_monitor(
            owner_user_id=owner_user_id,
            chat_id=int(chat_id),
            username=username,
            title=title,
            keywords=keywords,
            source_type=source_type,
        )
        self._pending_adds.pop(owner_user_id, None)
        self._invalidate_monitors_cache()
        return monitor

    async def list_monitors(self, owner_user_id: int) -> list[PersistedMonitor]:
        """List persisted monitors for one owner, using the in-memory cache."""
        if owner_user_id not in self._monitors_cache:
            self._monitors_cache[owner_user_id] = await self._store.list_monitors(owner_user_id)
        return self._monitors_cache[owner_user_id]

    async def get_monitor_by_chat_id(self, chat_id: int) -> PersistedMonitor | None:
        """Return one persisted monitor by Telegram chat ID.

        Searches the in-memory cache when warm; falls back to the DB otherwise.
        """
        for monitors in self._monitors_cache.values():
            for monitor in monitors:
                if monitor.chat_id == chat_id:
                    return monitor
        return await self._store.get_monitor_by_chat_id(chat_id)

    async def resolve_for_owner(self, owner_user_id: int, channel_ref: str) -> PersistedMonitor | None:
        """Resolve a free-form channel reference against persisted monitors."""
        monitors = await self.list_monitors(owner_user_id)
        normalized_ref = channel_ref.strip()
        try:
            numeric_ref = int(normalized_ref)
        except ValueError:
            numeric_ref = None
        normalized_name = normalized_ref.lstrip("@").lower()

        for monitor in monitors:
            if numeric_ref is not None and monitor.chat_id == numeric_ref:
                return monitor
            if monitor.username and monitor.username.lstrip("@").lower() == normalized_name:
                return monitor
            if monitor.title.lower() == normalized_ref.lower():
                return monitor
        return None

    async def remove_monitor(self, owner_user_id: int, identifier: str) -> bool:
        """Remove a persisted monitor for one owner."""
        removed = await self._store.remove_monitor(owner_user_id, identifier)
        if removed:
            self._invalidate_monitors_cache()
        return removed

    def _invalidate_monitors_cache(self) -> None:
        """Clear the in-memory monitor cache so the next read hits the DB."""
        self._monitors_cache.clear()

    @staticmethod
    def _normalize_username(username: str) -> str:
        normalized = username.strip()
        if not normalized:
            return ""
        return normalized if normalized.startswith("@") else f"@{normalized}"
