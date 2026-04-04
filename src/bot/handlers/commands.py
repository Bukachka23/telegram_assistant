import logging
from collections.abc import Awaitable, Callable, Sequence
from typing import TYPE_CHECKING, Any

from aiogram import F, Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.config.constants import (
    MODEL_COMMAND_MIN_PARTS,
    MONITOR_COMMAND_MIN_PARTS,
    VAULT_COMMAND_MIN_PARTS,
)
from bot.domain.exceptions import LLMError, TelegraphError
from bot.domain.models import ForwardedChatLike, MonitorDisplay
from bot.domain.protocols import DeepResearchServiceProtocol, MonitorServiceProtocol
from bot.services.conversation import ConversationManager
from bot.services.formatting import split_for_telegram
from bot.services.telegraph import TelegraphPublishService
from bot.shared.agents.registry import (
    get_agent,
    get_agent_by_command,
    get_default_agent,
    list_agents,
)

if TYPE_CHECKING:
    from bot.services.health import HealthService

logger = logging.getLogger(__name__)


def _agent_commands() -> list[str]:
    """Return all built-in agent command names."""
    return [agent.command for agent in list_agents()]


def _build_agent_status_text(active_agent_name: str) -> str:
    """Build a status message for the current and available agent modes."""
    active_agent = get_agent(active_agent_name) or get_default_agent()
    lines = [
        f"🤖 Current agent: `{active_agent.display_name}`",
        "Use `/agent <mode>` or one of the direct commands below to switch.",
        "",
        "**Available agents:**",
    ]
    lines.extend(
        f"• `/{agent.command}` — {agent.display_name}"
        for agent in list_agents()
    )
    return "\n".join(lines)


def _build_agent_switch_text(command: str) -> str:
    """Build a confirmation message after switching the active agent."""
    agent = get_agent_by_command(command) or get_default_agent()
    return f"🤖 Active agent: `{agent.display_name}`"


def _build_unknown_command_text(command: str) -> str:
    """Build a help message for unknown slash commands."""
    return (
        f"❌ Unknown command: `{command}`\n\n"
        "Use `/agent` to see available assistant modes and commands."
    )


def _parse_monitor_keywords(raw_keywords: str) -> list[str]:
    """Parse comma-separated keyword text into a clean list."""
    if not raw_keywords.strip():
        return []
    return [keyword.strip() for keyword in raw_keywords.split(",") if keyword.strip()]


def _monitor_identifier_text(monitor: MonitorDisplay) -> str:
    """Build a stable display identifier for a monitor."""
    return monitor.username or f"id:{monitor.chat_id}"


def _extract_forwarded_chat(message: Message) -> ForwardedChatLike | None:
    """Extract a forwarded channel/chat object from an aiogram message."""
    origin = getattr(message, "forward_origin", None)
    if not origin:
        return None
    chat = getattr(origin, "chat", None)
    if chat is not None:
        return chat
    return getattr(origin, "sender_chat", None)


async def _handle_monitor_list(
    *, message: Message, owner_user_id: int, monitor_service: MonitorServiceProtocol
) -> None:
    monitors = await monitor_service.list_monitors(owner_user_id)
    if not monitors:
        await message.answer("No active monitors.")
        return

    lines = ["**Active monitors:**"]
    for monitor in monitors:
        keywords = ", ".join(monitor.keywords) if monitor.keywords else "(all)"
        lines.append(f"• {monitor.title} — {_monitor_identifier_text(monitor)} — {keywords}")
    await message.answer("\n".join(lines), parse_mode="Markdown")


async def _handle_monitor_add(*, message: Message, args: Sequence[str], owner_user_id: int,
                              monitor_service: MonitorServiceProtocol) -> None:
    if len(args) < MONITOR_COMMAND_MIN_PARTS:
        monitor_service.begin_pending_add(owner_user_id, [])
        await message.answer("📨 Forward me a message from the private channel you want to monitor.")
        return

    target = args[2]
    if target.startswith("@"):
        keywords = _parse_monitor_keywords(" ".join(args[3:]))
        try:
            monitor = await monitor_service.add_public_monitor(
                owner_user_id=owner_user_id,
                channel_ref=target,
                keywords=keywords,
            )
        except ValueError as error:
            await message.answer(f"❌ {error}")
            return

        await message.answer(f"✅ Monitoring {monitor.title} ({_monitor_identifier_text(monitor)})")
        return

    keywords = _parse_monitor_keywords(" ".join(args[2:]))
    monitor_service.begin_pending_add(owner_user_id, keywords)
    await message.answer("📨 Forward me a message from the private channel you want to monitor.")


async def _handle_monitor_remove(*, message: Message, args: Sequence[str], owner_user_id: int,
                                 monitor_service: MonitorServiceProtocol) -> None:
    if len(args) < MONITOR_COMMAND_MIN_PARTS:
        await message.answer("Usage: /monitor remove @channel_or_chat_id")
        return

    identifier = args[2]
    removed = await monitor_service.remove_monitor(owner_user_id, identifier)
    if removed:
        await message.answer(f"✅ Removed {identifier}")
    else:
        await message.answer(f"❌ {identifier} not found in monitors")


def _extract_query(text: str | None) -> str | None:
    """Extract and validate the query string from the command text."""
    if not text:
        return None

    args = text.split(maxsplit=1)
    if len(args) < MODEL_COMMAND_MIN_PARTS or not args[1].strip():
        return None

    return args[1].strip()


async def _execute_deep_research(
    *,
    deep_research: DeepResearchServiceProtocol,
    query: str,
    model: str,
    user_id: int,
    send_message: Callable[..., Awaitable[Any]],
) -> str | None:
    """Execute the deep research service and handle any resulting exceptions."""
    try:
        return await deep_research.run(query=query, model=model, on_progress=send_message)
    except LLMError as error:
        logger.exception("Deep research failed for user %d", user_id)
        await send_message(f"⚠️ Deep research failed: {error}")
        return None
    except Exception:
        logger.exception("Unexpected deep research error for user %d", user_id)
        await send_message("⚠️ Deep research failed. Please try again.")
        return None


def setup_commands(  # noqa: PLR0915
    conversations: ConversationManager,
    monitor_service: MonitorServiceProtocol,
    deep_research: DeepResearchServiceProtocol | None = None,
    health: "HealthService | None" = None,
    telegraph: TelegraphPublishService | None = None,
) -> Router:
    """Configure command handlers with dependencies."""
    router = Router(name="commands")

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
            "`/status` — system health check\n"
            "`/monitor` — list active monitors\n"
            "`/monitor add @channel kw1, kw2` — monitor a public channel\n"
            "`/monitor add [kw1, kw2]` — then forward a private channel message\n"
            "`/vault search <query>` — search vault notes\n"
            "`/clear` — clear conversation history",
            parse_mode="Markdown",
        )

    @router.message(Command("agent"))
    async def cmd_agent(message: Message) -> None:
        if not message.from_user:
            return
        args = (message.text or "").split(maxsplit=1)
        user_id = message.from_user.id

        if len(args) == 1:
            text = _build_agent_status_text(conversations.get_active_agent(user_id))
            await message.answer(text, parse_mode="Markdown")
            return

        selected_agent = get_agent_by_command(args[1].strip())
        if not selected_agent:
            await message.answer(_build_unknown_command_text(args[1].strip()), parse_mode="Markdown")
            return

        conversations.set_active_agent(user_id, selected_agent.name)
        await message.answer(_build_agent_switch_text(selected_agent.command), parse_mode="Markdown")

    @router.message(Command(*_agent_commands()))
    async def cmd_agent_switch(message: Message) -> None:
        if not message.from_user or not message.text:
            return

        command = message.text.split(maxsplit=1)[0]
        selected_agent = get_agent_by_command(command)
        if not selected_agent:
            await message.answer(_build_unknown_command_text(command), parse_mode="Markdown")
            return

        conversations.set_active_agent(message.from_user.id, selected_agent.name)
        await message.answer(_build_agent_switch_text(selected_agent.command), parse_mode="Markdown")

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

    @router.message(Command("status"))
    async def cmd_status(message: Message) -> None:
        if not message.from_user:
            return
        if health is None:
            await message.answer("⚠️ Health check is not available.")
            return
        try:
            report = await health.check()
            await message.answer(report.format_telegram(), parse_mode="Markdown")
        except Exception:
            logger.exception("Health check failed for user %d", message.from_user.id)
            await message.answer("⚠️ Health check failed.")

    @router.message(Command("deep"))
    async def cmd_deep(message: Message) -> None:
        """Handle the /deep command to perform deep research."""
        if not message.from_user:
            return

        if deep_research is None:
            await message.answer("⚠️ Deep research is not available right now.")
            return

        query = _extract_query(message.text)
        if not query:
            await message.answer("Usage: /deep <question>")
            return

        user_id = message.from_user.id
        model = conversations.get_model(user_id)
        answer = await _execute_deep_research(
            deep_research=deep_research,
            query=query,
            model=model,
            user_id=user_id,
            send_message=message.answer,
        )

        if answer:
            if telegraph:
                try:
                    result = await telegraph.publish(
                        answer,
                        title=query[:60],
                        model=model,
                        agent="researcher",
                    )
                except TelegraphError:
                    logger.warning("Telegraph publish failed for deep research")
                    await message.answer("⚠️ Telegra.ph unavailable, sending inline.")
                else:
                    await message.answer(
                        f"{result.preview}\n\n📄 Deep research: {result.url}",
                    )
                    return

            for chunk in split_for_telegram(answer):
                await message.answer(chunk, parse_mode="HTML")

    @router.message(Command("monitor"))
    async def cmd_monitor(message: Message) -> None:
        if not message.from_user:
            return

        args = (message.text or "").split()
        owner_user_id = message.from_user.id

        if len(args) == 1:
            await _handle_monitor_list(
                message=message, owner_user_id=owner_user_id, monitor_service=monitor_service)
        elif args[1] == "add":
            await _handle_monitor_add(
                message=message, args=args, owner_user_id=owner_user_id, monitor_service=monitor_service)
        elif args[1] == "remove":
            await _handle_monitor_remove(
                message=message, args=args, owner_user_id=owner_user_id, monitor_service=monitor_service)
        else:
            await message.answer(
                "Usage:\n"
                "/monitor — list monitors\n"
                "/monitor add @channel keyword1, keyword2\n"
                "/monitor add keyword1, keyword2 (then forward a private channel message)\n"
                "/monitor remove @channel_or_chat_id"
            )

    @router.message()
    async def cmd_monitor_forward(message: Message) -> None:
        if not message.from_user or not monitor_service.has_pending_add(message.from_user.id):
            raise SkipHandler

        forwarded_chat = _extract_forwarded_chat(message)
        if forwarded_chat is None:
            raise SkipHandler

        try:
            monitor = await monitor_service.add_forwarded_monitor(
                owner_user_id=message.from_user.id,
                forwarded_chat=forwarded_chat,
            )
        except ValueError as error:
            await message.answer(f"❌ {error}")
            return

        await message.answer(f"✅ Monitoring {monitor.title} ({_monitor_identifier_text(monitor)})")

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
        await message.answer(_build_unknown_command_text(command), parse_mode="Markdown")

    return router
