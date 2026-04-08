import logging
from pathlib import Path
from typing import TYPE_CHECKING, cast

import aiosqlite
from aiogram import Bot

from bot.config.constants import PROJECT_ROOT
from bot.infrastructure.openrouter.openrouter import OpenRouterClient
from bot.infrastructure.storage.memory_storage import MemoryStore
from bot.infrastructure.storage.monitor_storage import MonitorStore
from bot.infrastructure.telegraph.client import TelegraphClient
from bot.services.scheduler import BotSchedulerService
from bot.services.web_search_router import WebSearchRouter

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from telethon import TelegramClient

    from bot.infrastructure.search.tavily import TavilySearchClient

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


async def _try_connect_telethon(api_id: int, api_hash: str) -> "TelegramClient | None":
    """Try to connect Telethon using an existing session. Returns client or None."""
    session = _find_session()
    if not session:
        logger.warning("No Telethon session found. Run 'python scripts/auth_telethon.py' first for channel features.")
        return None

    from bot.infrastructure.telethon.telethon_client import create_telethon_client  # noqa: PLC0415

    session_name = str(session.with_suffix(""))
    client = create_telethon_client(
        api_id=api_id,
        api_hash=api_hash,
        session_name=session_name,
    )
    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.warning("Telethon session expired. Run 'python scripts/auth_telethon.py' to re-authenticate.")
            await cast("Awaitable[None]", client.disconnect())
            return None
    except Exception as error:  # noqa: BLE001
        logger.warning("Telethon connection failed: %s", error)
        return None
    else:
        logger.info("Telethon userbot connected")
        return client


async def _open_shared_db(db_path: str) -> aiosqlite.Connection:
    """Open the shared SQLite connection used by all stores."""
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    shared_db = await aiosqlite.connect(db_file)
    shared_db.row_factory = aiosqlite.Row
    return shared_db


async def _shutdown(
    *,
    scheduler: BotSchedulerService,
    openrouter: OpenRouterClient,
    tavily: "TavilySearchClient | None",
    search_router: WebSearchRouter,
    memory: MemoryStore,
    monitor_store: MonitorStore,
    shared_db: aiosqlite.Connection,
    telegraph_client: TelegraphClient | None,
    userbot: "TelegramClient | None",
    bot: Bot,
) -> None:
    """Gracefully close runtime resources in reverse dependency order."""
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
