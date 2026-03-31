import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

from aiogram import Bot, Dispatcher

from bot.handlers import OwnerOnlyMiddleware
from bot.handlers.channels import setup_channel_monitoring
from bot.handlers.commands import setup_commands
from bot.handlers.messages import setup_messages
from bot.infrastructure.open_router.openrouter import OpenRouterClient
from bot.infrastructure.telegram_client.telethon_client import create_telethon_client
from bot.infrastructure.websearch_engine.tavily_search import TavilySearchClient
from bot.services.channels import ChannelService
from bot.services.conversation import ConversationManager
from bot.services.deep_research import DeepResearchService
from bot.services.llm import AsyncToolExecutor, LLMService
from bot.services.memory import MemoryStore
from bot.services.monitors import MonitorService, MonitorStore
from bot.services.vault import VaultService
from bot.shared.config import load_settings
from bot.shared.constants import PROJECT_ROOT
from bot.tools.channel_tools import register_channel_tools
from bot.tools.memory_tools import register_memory_tools
from bot.tools.registry import ToolRegistry
from bot.tools.vault_tools import register_vault_tools
from bot.tools.web_tools import register_web_tools

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


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


async def _try_connect_telethon(api_id: int, api_hash: str) -> Any | None:
    """Try to connect Telethon using an existing session. Returns client or None."""
    session = _find_session()
    if not session:
        logger.warning(
            "No Telethon session found. "
            "Run 'python scripts/auth_telethon.py' first for channel features."
        )
        return None

    session_name = str(session.with_suffix(""))
    client = create_telethon_client(
        api_id=api_id, api_hash=api_hash, session_name=session_name
    )
    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.warning(
                "Telethon session expired. "
                "Run 'python scripts/auth_telethon.py' to re-authenticate."
            )
            await client.disconnect()
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
            line = f"- [{r['category'] or 'general'}] {r['fact']}"
            if r.get("created_at"):
                line += f" (saved: {r['created_at'][:10]})"
            lines.append(line)
        return "\n".join(lines)

    return executor


async def run() -> None:  # noqa: PLR0915
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
        tavily = TavilySearchClient(api_key=settings.tavily_api_key)
    else:
        logger.warning("TAVILY_API_KEY not set. Web search disabled.")

    # --- Memory & monitor persistence ---
    memory = MemoryStore(db_path=settings.memory_db_path)
    await memory.init()
    monitor_store = MonitorStore(db_path=settings.memory_db_path)
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
    monitor_service = MonitorService(store=monitor_store, client=userbot)

    # --- Tools ---
    registry = ToolRegistry()
    register_vault_tools(registry, vault)
    register_channel_tools(registry)
    if tavily:
        register_web_tools(registry)
    register_memory_tools(registry)

    # --- LLM Service ---
    llm = LLMService(
        client=openrouter,
        conversations=conversations,
        registry=registry,
        max_tokens=settings.llm.max_tokens,
        temperature=settings.llm.temperature,
    )
    deep_research = DeepResearchService(llm=llm)

    # --- Wire async channel tools to LLM ---
    if userbot:
        channel_service = ChannelService(
            userbot,
            monitor_service=monitor_service,
            owner_user_id=settings.owner_user_id,
        )
        llm.register_async_tool("fetch_messages", channel_service.fetch_messages)
        llm.register_async_tool("search_channel", channel_service.search_channel)

    if tavily:
        llm.register_async_tool("web_search", tavily.search)

    # --- Wire memory tools to LLM ---
    llm.register_async_tool("save_memory", _save_executor(memory))
    llm.register_async_tool("recall_memory", _recall_executor(memory))

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
        )
    )
    dp.include_router(
        setup_messages(
            llm=llm,
            draft_interval_ms=settings.streaming.draft_interval_ms,
        )
    )

    # --- Channel Monitoring ---
    if userbot:
        setup_channel_monitoring(
            userbot=userbot,
            monitor_service=monitor_service,
        )

    # --- Start ---
    logger.info("Starting Telegram Assistant Bot...")
    logger.info("Model: %s", settings.llm.default_model)
    logger.info("Vault: %s", settings.vault.path)
    logger.info("Telethon: %s", "connected" if userbot else "disabled")
    logger.info(
        "Monitors: %d channels",
        len(await monitor_service.list_monitors(settings.owner_user_id)),
    )

    try:
        await dp.start_polling(bot)
    finally:
        await openrouter.close()
        if tavily:
            await tavily.close()
        await memory.close()
        await monitor_store.close()
        if userbot:
            await userbot.disconnect()
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
