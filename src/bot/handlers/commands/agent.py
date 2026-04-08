from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config.agents import (
    get_agent,
    get_agent_by_command,
    get_default_agent,
    list_agents,
)
from bot.handlers.commands.utils import build_unknown_command_text
from bot.services.conversation import ConversationManager


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


def register_agent_handlers(router: Router, conversations: ConversationManager) -> None:
    """Register agent selection and switching handlers."""

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
            await message.answer(
                build_unknown_command_text(args[1].strip()),
                parse_mode="Markdown",
            )
            return

        conversations.set_active_agent(user_id, selected_agent.name)
        await message.answer(
            _build_agent_switch_text(selected_agent.command),
            parse_mode="Markdown",
        )

    @router.message(Command(*_agent_commands()))
    async def cmd_agent_switch(message: Message) -> None:
        if not message.from_user or not message.text:
            return

        command = message.text.split(maxsplit=1)[0]
        selected_agent = get_agent_by_command(command)
        if not selected_agent:
            await message.answer(
                build_unknown_command_text(command),
                parse_mode="Markdown",
            )
            return

        conversations.set_active_agent(message.from_user.id, selected_agent.name)
        await message.answer(
            _build_agent_switch_text(selected_agent.command),
            parse_mode="Markdown",
        )
