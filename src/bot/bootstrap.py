import asyncio
import logging
import sys
from typing import TYPE_CHECKING, cast

from aiogram import Bot

from bot.bootstrap_factories import (
    _build_health_service,
    _build_persistence,
    _build_search_router,
    _build_telegraph_service,
    _build_tool_registry,
)
from bot.bootstrap_runtime import _find_session, _open_shared_db, _shutdown, _try_connect_telethon
from bot.bootstrap_wiring import _build_dispatcher, _log_startup, _wire_llm_tools
from bot.config.config import load_settings
from bot.config.constants import PROJECT_ROOT
from bot.infrastructure.openrouter.openrouter import OpenRouterClient
from bot.services.conversation import ConversationManager
from bot.services.deep_research import DeepResearchService
from bot.services.llm import LLMService
from bot.services.metrics import MetricsService
from bot.services.monitors import MonitorService
from bot.services.scheduler import BotSchedulerService
from bot.services.vault import VaultService

if TYPE_CHECKING:
    from bot.domain.protocols import DeepResearchServiceProtocol, SupportsGetEntity

logger = logging.getLogger(__name__)


async def run() -> None:  # noqa: PLR0914
    """Initialize all components and start both clients."""
    settings = load_settings()

    if not settings.bot_token:
        logger.error("BOT_TOKEN not set in .env")
        sys.exit(1)
    if not settings.openrouter_api_key:
        logger.error("OPENROUTER_API_KEY not set in .env")
        sys.exit(1)

    openrouter = OpenRouterClient(api_key=settings.openrouter_api_key)

    tavily = None
    if settings.tavily_api_key:
        from bot.infrastructure.search.tavily import TavilySearchClient  # noqa: PLC0415

        tavily = TavilySearchClient(api_key=settings.tavily_api_key)
    else:
        logger.warning("TAVILY_API_KEY not set. Web search disabled.")

    search_router = _build_search_router(tavily)
    shared_db = await _open_shared_db(settings.memory_db_path)
    memory, monitor_store, metrics_db = await _build_persistence(
        settings.memory_db_path,
        shared_db,
    )

    userbot = None
    if settings.telegram_api_id and settings.telegram_api_hash:
        userbot = await _try_connect_telethon(
            settings.telegram_api_id,
            settings.telegram_api_hash,
        )

    conversations = ConversationManager(
        default_model=settings.llm.default_model,
        session_timeout_minutes=settings.conversation.session_timeout_minutes,
        max_history=settings.conversation.max_history_messages,
    )
    vault = VaultService(
        vault_path=settings.vault.path,
        default_folder=settings.vault.default_folder,
    )
    monitor_service = MonitorService(
        store=monitor_store,
        client=cast("SupportsGetEntity | None", userbot),
    )
    registry = _build_tool_registry(web_search_enabled=tavily is not None)

    llm = LLMService(
        client=openrouter,
        conversations=conversations,
        registry=registry,
        max_tokens=settings.llm.max_tokens,
        temperature=settings.llm.temperature,
        tz_offset_hours=settings.scheduler.tz_offset_hours,
        metrics_store=metrics_db,
    )
    deep_research: DeepResearchServiceProtocol = DeepResearchService(llm=llm)
    metrics_service = MetricsService(store=metrics_db)
    health = _build_health_service(
        model=settings.llm.default_model,
        vault_path=settings.vault.path,
        memory=memory,
        monitor_store=monitor_store,
        vault=vault,
        conversations=conversations,
        userbot=userbot,
        tavily_available=tavily is not None,
        metrics_db=metrics_db,
        owner_user_id=settings.owner_user_id,
    )

    telegraph_client, telegraph_service = await _build_telegraph_service(settings)
    health.set_telegraph_available(available=telegraph_service is not None)

    scheduler = BotSchedulerService(
        jobs_file=str(PROJECT_ROOT / "data" / "jobs.json"),
        owner_chat_id=settings.owner_user_id,
        tz_offset_hours=settings.scheduler.tz_offset_hours,
    )
    _wire_llm_tools(
        llm=llm,
        vault=vault,
        memory=memory,
        scheduler=scheduler,
        userbot=userbot,
        monitor_service=monitor_service,
        owner_user_id=settings.owner_user_id,
        tavily=tavily,
        search_router=search_router,
    )

    bot = Bot(token=settings.bot_token)
    dp = _build_dispatcher(
        owner_user_id=settings.owner_user_id,
        conversations=conversations,
        monitor_service=monitor_service,
        deep_research=deep_research,
        health=health,
        telegraph_service=telegraph_service,
        metrics_service=metrics_service,
        llm=llm,
        draft_interval_ms=settings.streaming.draft_interval_ms,
    )

    async def _send_reminder(chat_id: int, text: str) -> None:
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        except Exception:  # noqa: BLE001
            logger.warning("Reminder Markdown send failed, retrying as plain text")
            await bot.send_message(chat_id=chat_id, text=text)

    scheduler.start(asyncio.get_running_loop(), _send_reminder)
    _log_startup(
        settings=settings,
        userbot=userbot,
        telegraph_service=telegraph_service,
        monitor_count=len(await monitor_service.list_monitors(settings.owner_user_id)),
    )

    try:
        await dp.start_polling(bot)
    finally:
        await _shutdown(
            scheduler=scheduler,
            openrouter=openrouter,
            tavily=tavily,
            search_router=search_router,
            memory=memory,
            monitor_store=monitor_store,
            shared_db=shared_db,
            telegraph_client=telegraph_client,
            userbot=userbot,
            bot=bot,
        )
