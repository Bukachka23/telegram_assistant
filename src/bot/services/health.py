from __future__ import annotations

import platform
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from bot.domain.models.health import HealthReport

if TYPE_CHECKING:
    from bot.infrastructure.storage.memory_storage import MemoryStore
    from bot.infrastructure.storage.metrics_storage import MetricsStore
    from bot.infrastructure.storage.monitor_storage import MonitorStore
    from bot.services.conversation import ConversationManager
    from bot.services.vault import VaultService


class HealthService:
    """Collects system health metrics from running components."""

    def __init__(
        self,
        *,
        start_time: datetime,
        model: str,
        vault_path: str,
    ) -> None:
        self._start_time = start_time
        self._model = model
        self._vault_path = vault_path
        self._memory_store: MemoryStore | None = None
        self._monitor_store: MonitorStore | None = None
        self._vault_service: VaultService | None = None
        self._conversations: ConversationManager | None = None
        self._telethon_connected = False
        self._tavily_available = False
        self._deep_research_available = False
        self._telegraph_available = False
        self._metrics_store: MetricsStore | None = None
        self._owner_user_id: int = 0

    def set_memory_store(self, store: MemoryStore) -> None:
        self._memory_store = store

    def set_monitor_store(self, store: MonitorStore) -> None:
        self._monitor_store = store

    def set_vault_service(self, vault: VaultService) -> None:
        self._vault_service = vault

    def set_conversations(self, conversations: ConversationManager) -> None:
        self._conversations = conversations

    def set_telethon_connected(self, *, connected: bool) -> None:
        self._telethon_connected = connected

    def set_tavily_available(self, *, available: bool) -> None:
        self._tavily_available = available

    def set_deep_research_available(self, *, available: bool) -> None:
        self._deep_research_available = available

    def set_telegraph_available(self, *, available: bool) -> None:
        self._telegraph_available = available

    def set_metrics_store(self, store: MetricsStore) -> None:
        self._metrics_store = store

    def set_owner_user_id(self, owner_id: int) -> None:
        self._owner_user_id = owner_id

    async def check(self) -> HealthReport:
        """Run all health checks and return a report."""
        errors: list[str] = []
        memory_count = await self._safe_memory_count(errors)
        monitor_count = await self._safe_monitor_count(errors)
        vault_note_count = await self._safe_vault_count(errors)
        request_count = await self._safe_request_count(errors)
        live_model = (
            self._conversations.get_model(self._owner_user_id)
            if self._conversations and self._owner_user_id
            else self._model
        )

        return HealthReport(
            uptime=datetime.now(UTC) - self._start_time,
            python_version=platform.python_version(),
            platform=f"{platform.system()} {platform.machine()}",
            model=live_model,
            memory_count=memory_count,
            monitor_count=monitor_count,
            vault_path=self._vault_path,
            vault_note_count=vault_note_count,
            telethon_connected=self._telethon_connected,
            tavily_available=self._tavily_available,
            deep_research_available=self._deep_research_available,
            telegraph_available=self._telegraph_available,
            request_count=request_count,
            errors=errors,
        )

    async def _safe_memory_count(self, errors: list[str]) -> int:
        if self._memory_store is None:
            return 0
        try:
            return await self._memory_store.count()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Memory store: {exc}")
            return 0

    async def _safe_monitor_count(self, errors: list[str]) -> int:
        if self._monitor_store is None or not self._owner_user_id:
            return 0
        try:
            monitors = await self._monitor_store.list_monitors(self._owner_user_id)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Monitor store: {exc}")
            return 0
        else:
            return len(monitors)

    async def _safe_vault_count(self, errors: list[str]) -> int:
        if self._vault_service is None:
            return 0
        try:
            return await self._vault_service.count_notes()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Vault: {exc}")
            return 0

    async def _safe_request_count(self, errors: list[str]) -> int:
        if self._metrics_store is None:
            return 0
        try:
            return await self._metrics_store.count()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Metrics store: {exc}")
            return 0
