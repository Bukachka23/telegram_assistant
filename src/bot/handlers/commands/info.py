import logging
from typing import TYPE_CHECKING

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.config.constants import MODEL_COMMAND_MIN_PARTS, VAULT_COMMAND_MIN_PARTS
from bot.handlers.commands.utils import build_unknown_command_text, parse_stats_days
from bot.services.conversation import ConversationManager
from bot.services.health_formatter import format_health_report
from bot.services.metrics import MetricsService
from bot.services.telegraph import TelegraphPublishService

if TYPE_CHECKING:
    from bot.services.health import HealthService

logger = logging.getLogger(__name__)


def register_info_handlers(
    router: Router,
    conversations: ConversationManager,
    health: "HealthService | None" = None,
    telegraph: TelegraphPublishService | None = None,
    metrics: MetricsService | None = None,
) -> None:
    """Register informational and utility command handlers."""

    @router.message(CommandStart())
    async def cmd_start(message: Message) -> None:
        await message.answer(
            "👋 **Telegram Assistant**\n\n"
            "Send me any message and I'll respond using an LLM.\n"
            "I can also search your Obsidian vault and Telegram channels.\n\n"
            "**Commands:**\n"
            "`/agent` — show current agent, available modes, or switch with `/agent <mode>`\n"
            "`/assistant`, `/explanatory`, `/math_tutor`, `/researcher` — direct agent mode switches\n"
            "`/model` — show or switch LLM model\n"
            "`/deep <question>` — run multi-cycle deep research\n"
            "`/telegraph` — toggle Telegra.ph publishing for long responses\n"
            "`/stats` — model usage, cost, and latency statistics\n"
            "`/status` — system health check\n"
            "`/monitor` — list active monitors\n"
            "`/monitor add @channel kw1, kw2` — monitor a public channel\n"
            "`/monitor add [kw1, kw2]` — then forward a private channel message\n"
            "`/vault search <query>` — search vault notes\n"
            "`/clear` — clear conversation history",
            parse_mode="Markdown",
        )

    @router.message(Command("model"))
    async def cmd_model(message: Message) -> None:
        if not message.from_user:
            return
        args = (message.text or "").split(maxsplit=1)
        user_id = message.from_user.id

        if len(args) < MODEL_COMMAND_MIN_PARTS:
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

    @router.message(Command("telegraph"))
    async def cmd_telegraph(message: Message) -> None:
        if not message.from_user:
            return
        if telegraph is None:
            await message.answer("⚠️ Telegra.ph publishing is not configured.")
            return
        new_state = conversations.toggle_telegraph(message.from_user.id)
        icon = "✅" if new_state else "❌"
        label = "enabled" if new_state else "disabled"
        await message.answer(
            f"{icon} Telegra.ph publishing **{label}**",
            parse_mode="Markdown",
        )

    @router.message(Command("stats"))
    async def cmd_stats(message: Message) -> None:
        if not message.from_user:
            return
        if metrics is None:
            await message.answer("⚠️ Metrics are not available.")
            return
        days = parse_stats_days(message.text)
        if days is None:
            await message.answer(
                "Usage: `/stats` `/stats 30` `/stats today` `/stats all`",
                parse_mode="Markdown",
            )
            return
        text = await metrics.build_stats(days=days)
        await message.answer(text, parse_mode="Markdown")

    @router.message(Command("status"))
    async def cmd_status(message: Message) -> None:
        if not message.from_user:
            return
        if health is None:
            await message.answer("⚠️ Health check is not available.")
            return
        try:
            report = await health.check()
            await message.answer(format_health_report(report), parse_mode="Markdown")
        except Exception:
            logger.exception("Health check failed for user %d", message.from_user.id)
            await message.answer("⚠️ Health check failed.")

    @router.message(Command("vault"))
    async def cmd_vault(message: Message) -> None:
        args = (message.text or "").split(maxsplit=2)
        if len(args) < VAULT_COMMAND_MIN_PARTS or args[1] != "search":
            await message.answer("Usage: /vault search <query>")
            return
        await message.answer(
            f'💡 Tip: Just ask me naturally, e.g., *"Find my notes about {args[2]}"*',
            parse_mode="Markdown",
        )

    @router.message(F.text.startswith("/"))
    async def cmd_unknown(message: Message) -> None:
        if not message.text:
            return
        command = message.text.split(maxsplit=1)[0]
        await message.answer(
            build_unknown_command_text(command),
            parse_mode="Markdown",
        )
