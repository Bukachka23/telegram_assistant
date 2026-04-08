import logging
from typing import TYPE_CHECKING

from aiogram import Dispatcher

from bot.handlers import OwnerOnlyMiddleware
from bot.handlers.commands import setup_commands
from bot.handlers.messages import setup_messages
from bot.infrastructure.storage.memory_storage import MemoryStore
from bot.services.conversation import ConversationManager
from bot.services.health import HealthService
from bot.services.llm import LLMService
from bot.services.metrics import MetricsService
from bot.services.monitors import MonitorService
from bot.services.scheduler import BotSchedulerService
from bot.services.telegraph import TelegraphPublishService
from bot.services.vault import VaultService
from bot.services.web_search_router import WebSearchRouter
from bot.tools.memory_tools import build_memory_async_tools
from bot.tools.scheduler_tools import (
    build_list_schedules_executor,
    build_remove_schedule_executor,
    build_schedule_executor,
)
from bot.tools.vault_tools import build_vault_async_tools

if TYPE_CHECKING:
    from telethon import TelegramClient

    from bot.domain.protocols import DeepResearchServiceProtocol
    from bot.infrastructure.search.tavily import TavilySearchClient

logger = logging.getLogger(__name__)


def _wire_llm_tools(
    *,
    llm: LLMService,
    vault: VaultService,
    memory: MemoryStore,
    scheduler: BotSchedulerService,
    userbot: "TelegramClient | None",
    monitor_service: MonitorService,
    owner_user_id: int,
    tavily: "TavilySearchClient | None",
    search_router: WebSearchRouter,
) -> None:
    """Register all async tool executors with the LLM service."""
    for tool_name, executor in build_vault_async_tools(vault).items():
        llm.register_async_tool(tool_name, executor)

    if userbot:
        from bot.handlers.channels import setup_channel_monitoring  # noqa: PLC0415
        from bot.services.channels import ChannelService  # noqa: PLC0415

        channel_service = ChannelService(
            userbot,
            monitor_service=monitor_service,
            owner_user_id=owner_user_id,
        )
        llm.register_async_tool("fetch_messages", channel_service.fetch_messages)
        llm.register_async_tool("search_channel", channel_service.search_channel)
        setup_channel_monitoring(
            userbot=userbot,
            monitor_service=monitor_service,
        )

    if tavily:
        llm.register_async_tool("web_search", search_router.search)

    for tool_name, executor in build_memory_async_tools(memory).items():
        llm.register_async_tool(tool_name, executor)

    llm.register_async_tool("schedule", build_schedule_executor(scheduler))
    llm.register_async_tool("list_schedules", build_list_schedules_executor(scheduler))
    llm.register_async_tool("remove_schedule", build_remove_schedule_executor(scheduler))


def _build_dispatcher(
    *,
    owner_user_id: int,
    conversations: ConversationManager,
    monitor_service: MonitorService,
    deep_research: "DeepResearchServiceProtocol",
    health: HealthService,
    telegraph_service: TelegraphPublishService | None,
    metrics_service: MetricsService,
    llm: LLMService,
    draft_interval_ms: int,
) -> Dispatcher:
    """Build the aiogram dispatcher and attach all routers/middleware."""
    dp = Dispatcher()
    dp.update.middleware(OwnerOnlyMiddleware(owner_user_id=owner_user_id))
    dp.include_router(
        setup_commands(
            conversations=conversations,
            monitor_service=monitor_service,
            deep_research=deep_research,
            health=health,
            telegraph=telegraph_service,
            metrics=metrics_service,
        )
    )
    dp.include_router(
        setup_messages(
            llm=llm,
            conversations=conversations,
            draft_interval_ms=draft_interval_ms,
            telegraph=telegraph_service,
        )
    )
    return dp


def _log_startup(
    *,
    settings,
    userbot: "TelegramClient | None",
    telegraph_service: TelegraphPublishService | None,
    monitor_count: int,
) -> None:
    """Log a startup summary once the app is fully wired."""
    logger.info("Starting Telegram Assistant Bot...")
    logger.info("Model: %s", settings.llm.default_model)
    logger.info("Vault: %s", settings.vault.path)
    logger.info("Telethon: %s", "connected" if userbot else "disabled")
    logger.info("Telegraph: %s", "enabled" if telegraph_service else "disabled")
    logger.info("Monitors: %d channels", monitor_count)
