"""Command handlers: /start, /model, /monitor, /vault, /clear."""

import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.services.conversation import ConversationManager

logger = logging.getLogger(__name__)

router = Router(name="commands")


def setup_commands(
    conversations: ConversationManager,
    monitor_config: list,
) -> Router:
    """Configure command handlers with dependencies."""

    @router.message(CommandStart())
    async def cmd_start(message: Message) -> None:
        await message.answer(
            "👋 **Telegram Assistant**\n\n"
            "Send me any message and I'll respond using an LLM.\n"
            "I can also search your Obsidian vault and Telegram channels.\n\n"
            "**Commands:**\n"
            "/model — show or switch LLM model\n"
            "/monitor — manage channel monitors\n"
            "/vault search <query> — search vault notes\n"
            "/clear — clear conversation history",
            parse_mode="Markdown",
        )

    @router.message(Command("model"))
    async def cmd_model(message: Message) -> None:
        if not message.from_user:
            return
        args = (message.text or "").split(maxsplit=1)
        user_id = message.from_user.id

        if len(args) < 2:
            current = conversations.get_model(user_id)
            await message.answer(f"Current model: `{current}`", parse_mode="Markdown")
            return

        new_model = args[1].strip()
        conversations.set_model(user_id, new_model)
        await message.answer(f"✅ Switched to `{new_model}`", parse_mode="Markdown")

    @router.message(Command("clear"))
    async def cmd_clear(message: Message) -> None:
        if not message.from_user:
            return
        conversations.clear(message.from_user.id)
        await message.answer("🗑 Conversation cleared.")

    @router.message(Command("monitor"))
    async def cmd_monitor(message: Message) -> None:
        args = (message.text or "").split()

        # /monitor — list active monitors
        if len(args) == 1:
            if not monitor_config:
                await message.answer("No active monitors.")
                return
            lines = ["**Active monitors:**"]
            for m in monitor_config:
                kw = ", ".join(m.keywords) if m.keywords else "(all)"
                lines.append(f"• {m.username} — {kw}")
            await message.answer("\n".join(lines), parse_mode="Markdown")
            return

        # /monitor add @channel kw1, kw2
        if args[1] == "add" and len(args) >= 3:
            username = args[2]
            keywords = (
                [k.strip() for k in " ".join(args[3:]).split(",")]
                if len(args) > 3
                else []
            )
            # Import here to avoid circular dependency
            from bot.config import ChannelMonitorEntry

            monitor_config.append(
                ChannelMonitorEntry(username=username, keywords=keywords)
            )
            await message.answer(f"✅ Monitoring {username}")
            return

        # /monitor remove @channel
        if args[1] == "remove" and len(args) >= 3:
            username = args[2]
            before = len(monitor_config)
            monitor_config[:] = [m for m in monitor_config if m.username != username]
            if len(monitor_config) < before:
                await message.answer(f"✅ Removed {username}")
            else:
                await message.answer(f"❌ {username} not found in monitors")
            return

        await message.answer(
            "Usage:\n"
            "/monitor — list monitors\n"
            "/monitor add @channel keyword1, keyword2\n"
            "/monitor remove @channel"
        )

    @router.message(Command("vault"))
    async def cmd_vault(message: Message) -> None:
        args = (message.text or "").split(maxsplit=2)
        if len(args) < 3 or args[1] != "search":
            await message.answer("Usage: /vault search <query>")
            return
        # Vault search is handled by sending through LLM pipeline
        # so the user gets a natural language summary
        await message.answer(
            f"💡 Tip: Just ask me naturally, e.g., *\"Find my notes about {args[2]}\"*",
            parse_mode="Markdown",
        )

    return router
