import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import aiosqlite

from bot.infrastructure.storage.memory_storage import MemoryStore
from bot.infrastructure.storage.metrics_storage import MetricsStore as MetricsDBStore
from bot.infrastructure.storage.monitor_storage import MonitorStore
from bot.infrastructure.telegraph.client import TelegraphClient
from bot.services.conversation import ConversationManager
from bot.services.health import HealthService
from bot.services.telegraph import TelegraphPublishService
from bot.services.vault import VaultService
from bot.services.web_search_router import WebSearchRouter
from bot.tools.channel_tools import register_channel_tools
from bot.tools.memory_tools import register_memory_tools
from bot.tools.registry import ToolRegistry
from bot.tools.scheduler_tools import (
    register_scheduler_tools,
)
from bot.tools.vault_tools import register_vault_tools
from bot.tools.web_tools import register_web_tools

if TYPE_CHECKING:
    from telethon import TelegramClient

    from bot.infrastructure.search.tavily import TavilySearchClient

logger = logging.getLogger(__name__)


def _build_search_router(tavily: "TavilySearchClient | None") -> WebSearchRouter:
    """Create and configure the multi-source web search router."""
    from bot.infrastructure.search.arxiv import ArxivSearchClient  # noqa: PLC0415
    from bot.infrastructure.search.github import GitHubSearchClient  # noqa: PLC0415
    from bot.infrastructure.search.huggingface import HuggingFaceSearchClient  # noqa: PLC0415
    from bot.infrastructure.search.reddit import RedditSearchClient  # noqa: PLC0415
    from bot.infrastructure.search.stackoverflow import StackOverflowSearchClient  # noqa: PLC0415
    from bot.infrastructure.search.wikipedia import WikipediaSearchClient  # noqa: PLC0415

    return WebSearchRouter(
        tavily=tavily,
        github=GitHubSearchClient(),
        huggingface=HuggingFaceSearchClient(),
        stackoverflow=StackOverflowSearchClient(),
        arxiv=ArxivSearchClient(),
        wikipedia=WikipediaSearchClient(),
        reddit=RedditSearchClient(),  # type: ignore  # noqa: PGH003
    )


async def _build_persistence(
    db_path: str,
    shared_db: aiosqlite.Connection,
) -> tuple[MemoryStore, MonitorStore, MetricsDBStore]:
    """Build and initialize storage-backed persistence services."""
    memory = MemoryStore(db_path=db_path, db=shared_db)
    await memory.init()
    monitor_store = MonitorStore(db_path=db_path, db=shared_db)
    await monitor_store.init()
    metrics_db = MetricsDBStore(db_path=db_path, db=shared_db)
    await metrics_db.init()
    return memory, monitor_store, metrics_db


def _build_tool_registry(*, web_search_enabled: bool) -> ToolRegistry:
    """Register all tool schemas in the shared registry."""
    registry = ToolRegistry()
    register_vault_tools(registry)
    register_channel_tools(registry)
    if web_search_enabled:
        register_web_tools(registry)
    register_memory_tools(registry)
    register_scheduler_tools(registry)
    return registry


def _build_health_service(
    *,
    model: str,
    vault_path: str,
    memory: MemoryStore,
    monitor_store: MonitorStore,
    vault: VaultService,
    conversations: ConversationManager,
    userbot: "TelegramClient | None",
    tavily_available: bool,
    metrics_db: MetricsDBStore,
    owner_user_id: int,
) -> HealthService:
    """Build and configure the health service."""
    health = HealthService(
        start_time=datetime.now(UTC),
        model=model,
        vault_path=vault_path,
    )
    health.set_memory_store(memory)
    health.set_monitor_store(monitor_store)
    health.set_vault_service(vault)
    health.set_conversations(conversations)
    health.set_telethon_connected(connected=userbot is not None)
    health.set_tavily_available(available=tavily_available)
    health.set_deep_research_available(available=True)
    health.set_metrics_store(metrics_db)
    health.set_owner_user_id(owner_user_id)
    return health


async def _build_telegraph_service(settings) -> tuple[TelegraphClient | None, TelegraphPublishService | None]:
    """Create and initialize the optional Telegraph publishing service."""
    if not settings.telegraph.enabled:
        return None, None

    telegraph_client = TelegraphClient(
        author_name=settings.telegraph.author_name,
        author_url=settings.telegraph.author_url,
    )
    try:
        await telegraph_client.init()
        telegraph_service = TelegraphPublishService(
            client=telegraph_client,
            threshold_chars=settings.telegraph.threshold_chars,
        )
        logger.info(
            "Telegraph publishing enabled (threshold: %d chars)",
            settings.telegraph.threshold_chars,
        )
        return telegraph_client, telegraph_service
    except Exception:  # noqa: BLE001
        logger.warning("Telegraph account creation failed. Publishing disabled.")
        await telegraph_client.close()
        return None, None
