"""Entry point: starts aiogram bot + Telethon userbot on a shared asyncio loop."""

import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher

from bot.config import load_settings
from bot.domain.models import ChannelFilter
from bot.handlers import OwnerOnlyMiddleware
from bot.handlers.channels import setup_channel_monitoring
from bot.handlers.commands import setup_commands
from bot.handlers.messages import setup_messages
from bot.infrastructure.openrouter import OpenRouterClient
from bot.infrastructure.telethon_client import create_telethon_client
from bot.services.channels import ChannelService
from bot.services.conversation import ConversationManager
from bot.services.llm import LLMService
from bot.services.vault import VaultService
from bot.tools.channel_tools import register_channel_tools
from bot.tools.registry import ToolRegistry
from bot.tools.vault_tools import register_vault_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def _try_connect_telethon(api_id: int, api_hash: str):
    """Try to connect Telethon using an existing session. Returns client or None."""
    session_path = Path("userbot.session")
    if not session_path.exists():
        logger.warning(
            "No Telethon session found. "
            "Run 'python scripts/auth_telethon.py' first for channel features."
        )
        return None

    client = create_telethon_client(api_id=api_id, api_hash=api_hash)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.warning(
                "Telethon session expired. "
                "Run 'python scripts/auth_telethon.py' to re-authenticate."
            )
            await client.disconnect()
            return None
        logger.info("Telethon userbot connected")
        return client
    except Exception as e:
        logger.warning("Telethon connection failed: %s", e)
        return None


async def run() -> None:
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

    # --- Tools ---
    registry = ToolRegistry()
    register_vault_tools(registry, vault)
    register_channel_tools(registry)

    # --- LLM Service ---
    llm = LLMService(
        client=openrouter,
        conversations=conversations,
        registry=registry,
        max_tokens=settings.llm.max_tokens,
        temperature=settings.llm.temperature,
    )

    # --- Wire async channel tools to LLM ---
    if userbot:
        channel_service = ChannelService(userbot)
        llm.register_async_tool("fetch_messages", channel_service.fetch_messages)
        llm.register_async_tool("search_channel", channel_service.search_channel)

    # --- Aiogram Bot ---
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    # Auth middleware — must be first
    dp.update.middleware(OwnerOnlyMiddleware(owner_user_id=settings.owner_user_id))

    # Routers (order matters: commands before catch-all messages)
    monitor_config = settings.channels.monitor
    dp.include_router(setup_commands(conversations, monitor_config))
    dp.include_router(
        setup_messages(
            llm=llm,
            draft_interval_ms=settings.streaming.draft_interval_ms,
            min_chunk_chars=settings.streaming.min_chunk_chars,
        )
    )

    # --- Channel Monitoring ---
    if userbot and settings.channels.monitor:
        filters = [
            ChannelFilter(username=m.username, keywords=m.keywords)
            for m in settings.channels.monitor
        ]
        setup_channel_monitoring(
            userbot=userbot,
            bot_token=settings.bot_token,
            owner_chat_id=settings.owner_user_id,
            monitors=filters,
        )

    # --- Start ---
    logger.info("Starting Telegram Assistant Bot...")
    logger.info("Model: %s", settings.llm.default_model)
    logger.info("Vault: %s", settings.vault.path)
    logger.info("Telethon: %s", "connected" if userbot else "disabled")
    logger.info("Monitors: %d channels", len(settings.channels.monitor))

    try:
        await dp.start_polling(bot)
    finally:
        await openrouter.close()
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
