import asyncio
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from telethon import TelegramClient

    from bot.domain.protocols import SupportsGetEntity
    from bot.infrastructure.search.tavily import TavilySearchClient

import aiosqlite
from aiogram import Bot, Dispatcher

from bot.config.config import load_settings
from bot.config.constants import PROJECT_ROOT
from bot.handlers import OwnerOnlyMiddleware
from bot.handlers.commands import setup_commands
from bot.handlers.messages import setup_messages
from bot.infrastructure.openrouter.openrouter import OpenRouterClient
from bot.infrastructure.telegraph.client import TelegraphClient
from bot.services.conversation import ConversationManager
from bot.services.deep_research import DeepResearchService
from bot.services.health import HealthService
from bot.services.llm import AsyncToolExecutor, LLMService
from bot.services.memory import MemoryStore
from bot.services.monitors import MonitorService, MonitorStore
from bot.services.scheduler import BotSchedulerService
from bot.services.telegraph import TelegraphPublishService
from bot.services.vault import VaultService
from bot.services.web_search_router import WebSearchRouter
from bot.tools.channel_tools import register_channel_tools
from bot.tools.memory_tools import register_memory_tools
from bot.tools.registry import ToolRegistry
from bot.tools.scheduler_tools import (
    build_list_schedules_executor,
    build_remove_schedule_executor,
    build_schedule_executor,
    register_scheduler_tools,
)
from bot.tools.vault_tools import build_vault_async_tools, register_vault_tools
from bot.tools.web_tools import register_web_tools

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
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


def _find_session() -> Path | None:
    """Find userbot.session in stable project-relative locations."""
    candidates = (
        PROJECT_ROOT / "data" / "userbot.session",
        PROJECT_ROOT / "userbot.session",
        Path("data/userbot.session"),
        Path("userbot.session"),
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


async def _try_connect_telethon(api_id: int, api_hash: str) -> "TelegramClient | None":
    """Try to connect Telethon using an existing session. Returns client or None."""
    session = _find_session()
    if not session:
        logger.warning("No Telethon session found. Run 'python scripts/auth_telethon.py' first for channel features.")
        return None

    # Lazy import: Telethon is heavy (~25ms) and only needed when a session exists
    from bot.infrastructure.telethon.telethon_client import create_telethon_client  # noqa: PLC0415

    session_name = str(session.with_suffix(""))
    client = create_telethon_client(
        api_id=api_id, api_hash=api_hash, session_name=session_name
    )
    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.warning("Telethon session expired. Run 'python scripts/auth_telethon.py' to re-authenticate.")
            await cast("Awaitable[None]", client.disconnect())
            return None
    except Exception as e:  # noqa: BLE001
        logger.warning("Telethon connection failed: %s", e)
        return None
    else:
        logger.info("Telethon userbot connected")
        return client


def _save_executor(memory: MemoryStore) -> AsyncToolExecutor:
    """Wrap MemoryStore.save to return a string (async tool contract)."""

    async def executor(fact: str, category: str = "") -> str:
        row_id = await memory.save(fact, category=category)
        return f"Memory saved (id={row_id})"

    return executor


def _recall_executor(memory: MemoryStore) -> AsyncToolExecutor:
    """Wrap MemoryStore.recall to return a formatted string."""

    async def executor(query: str, limit: int = 5) -> str:
        results = await memory.recall(query, limit=limit)
        if not results:
            return f"No memories found for '{query}'"
        lines = [f"Found {len(results)} memory(ies):"]
        for r in results:
            created = r.get("created_at")
            suffix = f" (saved: {created[:10]})" if created else ""
            lines.append(f"- [{r['category'] or 'general'}] {r['fact']}{suffix}")
        return "\n".join(lines)

    return executor


async def run() -> None:  # noqa: PLR0912, PLR0914, PLR0915
    """Initialize all components and start both clients."""
    settings = load_settings()

    # --- Validate required secrets ---
    if not settings.bot_token:
        logger.error("BOT_TOKEN not set in .env")
        sys.exit(1)
    if not settings.openrouter_api_key:
        logger.error("OPENROUTER_API_KEY not set in .env")
        sys.exit(1)

    # --- Infrastructure ---
    openrouter = OpenRouterClient(api_key=settings.openrouter_api_key)

    tavily = None
    if settings.tavily_api_key:
        from bot.infrastructure.search.tavily import TavilySearchClient  # noqa: PLC0415

        tavily = TavilySearchClient(api_key=settings.tavily_api_key)
    else:
        logger.warning("TAVILY_API_KEY not set. Web search disabled.")

    search_router = _build_search_router(tavily)

    # --- Shared SQLite connection (one file, one connection) ---
    db_file = Path(settings.memory_db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    shared_db = await aiosqlite.connect(db_file)
    shared_db.row_factory = aiosqlite.Row

    # --- Memory & monitor persistence ---
    memory = MemoryStore(db_path=settings.memory_db_path, db=shared_db)
    await memory.init()
    monitor_store = MonitorStore(db_path=settings.memory_db_path, db=shared_db)
    await monitor_store.init()

    # Telethon: connect only if session exists (non-blocking)
    userbot = None
    if settings.telegram_api_id and settings.telegram_api_hash:
        userbot = await _try_connect_telethon(
            settings.telegram_api_id, settings.telegram_api_hash
        )

    # --- Services ---
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

    # --- Tools ---
    registry = ToolRegistry()
    register_vault_tools(registry)
    register_channel_tools(registry)
    if tavily:
        register_web_tools(registry)
    register_memory_tools(registry)
    register_scheduler_tools(registry)

    # --- LLM Service ---
    llm = LLMService(
        client=openrouter,
        conversations=conversations,
        registry=registry,
        max_tokens=settings.llm.max_tokens,
        temperature=settings.llm.temperature,
        tz_offset_hours=settings.scheduler.tz_offset_hours,
    )
    deep_research = DeepResearchService(llm=llm)

    # --- Health Service ---
    health = HealthService(
        start_time=datetime.now(UTC),
        model=settings.llm.default_model,
        vault_path=settings.vault.path,
    )
    health.set_memory_store(memory)
    health.set_monitor_store(monitor_store)
    health.set_vault_service(vault)
    health.set_conversations(conversations)
    health.set_telethon_connected(connected=userbot is not None)
    health.set_tavily_available(available=tavily is not None)
    health.set_deep_research_available(available=True)
    health.set_owner_user_id(settings.owner_user_id)

    # --- Telegraph (optional, graceful if disabled) ---
    telegraph_client: TelegraphClient | None = None
    telegraph_service: TelegraphPublishService | None = None
    if settings.telegraph.enabled:
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
        except Exception:  # noqa: BLE001
            logger.warning("Telegraph account creation failed. Publishing disabled.")
            await telegraph_client.close()
            telegraph_client = None

    health.set_telegraph_available(available=telegraph_service is not None)

    # --- Wire async vault tools to LLM ---
    for tool_name, executor in build_vault_async_tools(vault).items():
        llm.register_async_tool(tool_name, executor)

    # --- Wire async channel tools to LLM ---
    if userbot:
        from bot.handlers.channels import setup_channel_monitoring  # noqa: PLC0415
        from bot.services.channels import ChannelService  # noqa: PLC0415

        channel_service = ChannelService(
            userbot,
            monitor_service=monitor_service,
            owner_user_id=settings.owner_user_id,
        )
        llm.register_async_tool("fetch_messages", channel_service.fetch_messages)
        llm.register_async_tool("search_channel", channel_service.search_channel)

        setup_channel_monitoring(
            userbot=userbot,
            monitor_service=monitor_service,
        )

    if tavily:
        llm.register_async_tool("web_search", search_router.search)

    # --- Wire memory tools to LLM ---
    llm.register_async_tool("save_memory", _save_executor(memory))
    llm.register_async_tool("recall_memory", _recall_executor(memory))

    # --- Scheduler ---
    scheduler = BotSchedulerService(
        jobs_file=str(PROJECT_ROOT / "data" / "jobs.json"),
        owner_chat_id=settings.owner_user_id,
        tz_offset_hours=settings.scheduler.tz_offset_hours,
    )
    llm.register_async_tool("schedule", build_schedule_executor(scheduler))
    llm.register_async_tool("list_schedules", build_list_schedules_executor(scheduler))
    llm.register_async_tool("remove_schedule", build_remove_schedule_executor(scheduler))

    # --- Aiogram Bot ---
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    # Auth middleware — must be first
    dp.update.middleware(OwnerOnlyMiddleware(owner_user_id=settings.owner_user_id))

    # Routers (order matters: commands before catch-all messages)
    dp.include_router(
        setup_commands(
            conversations=conversations,
            monitor_service=monitor_service,
            deep_research=deep_research,
            health=health,
            telegraph=telegraph_service,
        )
    )
    dp.include_router(
        setup_messages(
            llm=llm,
            conversations=conversations,
            draft_interval_ms=settings.streaming.draft_interval_ms,
            telegraph=telegraph_service,
        )
    )

    # --- Start scheduler ---
    async def _send_reminder(chat_id: int, text: str) -> None:
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        except Exception:  # noqa: BLE001
            logger.warning("Reminder Markdown send failed, retrying as plain text")
            await bot.send_message(chat_id=chat_id, text=text)

    scheduler.start(asyncio.get_running_loop(), _send_reminder)

    # --- Start ---
    logger.info("Starting Telegram Assistant Bot...")
    logger.info("Model: %s", settings.llm.default_model)
    logger.info("Vault: %s", settings.vault.path)
    logger.info("Telethon: %s", "connected" if userbot else "disabled")
    logger.info("Telegraph: %s", "enabled" if telegraph_service else "disabled")
    logger.info(
        "Monitors: %d channels",
        len(await monitor_service.list_monitors(settings.owner_user_id)),
    )

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.stop()
        await openrouter.close()
        if tavily:
            await tavily.close()
        await search_router.close()
        await memory.close()
        await monitor_store.close()
        await shared_db.close()
        if telegraph_client:
            await telegraph_client.close()
        if userbot:
            await cast("Awaitable[None]", userbot.disconnect())
        await bot.session.close()
        logger.info("Shutdown complete")


def main() -> None:
    """CLI entry point."""
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")


if __name__ == "__main__":
    main()
