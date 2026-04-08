from collections.abc import Sequence

from aiogram import Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Command
from aiogram.types import Message

from bot.config.constants import MONITOR_COMMAND_MIN_PARTS
from bot.domain.protocols import MonitorServiceProtocol
from bot.handlers.commands.utils import (
    extract_forwarded_chat,
    monitor_identifier_text,
    parse_monitor_keywords,
)


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
        lines.append(
            f"• {monitor.title} — {monitor_identifier_text(monitor)} — {keywords}"
        )
    await message.answer("\n".join(lines), parse_mode="Markdown")


async def _handle_monitor_add(
    *,
    message: Message,
    args: Sequence[str],
    owner_user_id: int,
    monitor_service: MonitorServiceProtocol,
) -> None:
    if len(args) < MONITOR_COMMAND_MIN_PARTS:
        monitor_service.begin_pending_add(owner_user_id, [])
        await message.answer(
            "📨 Forward me a message from the private channel you want to monitor."
        )
        return

    target = args[2]
    if target.startswith("@"):
        keywords = parse_monitor_keywords(" ".join(args[3:]))
        try:
            monitor = await monitor_service.add_public_monitor(
                owner_user_id=owner_user_id,
                channel_ref=target,
                keywords=keywords,
            )
        except ValueError as error:
            await message.answer(f"❌ {error}")
            return

        await message.answer(
            f"✅ Monitoring {monitor.title} ({monitor_identifier_text(monitor)})"
        )
        return

    keywords = parse_monitor_keywords(" ".join(args[2:]))
    monitor_service.begin_pending_add(owner_user_id, keywords)
    await message.answer(
        "📨 Forward me a message from the private channel you want to monitor."
    )


async def _handle_monitor_remove(
    *,
    message: Message,
    args: Sequence[str],
    owner_user_id: int,
    monitor_service: MonitorServiceProtocol,
) -> None:
    if len(args) < MONITOR_COMMAND_MIN_PARTS:
        await message.answer("Usage: /monitor remove @channel_or_chat_id")
        return

    identifier = args[2]
    removed = await monitor_service.remove_monitor(owner_user_id, identifier)
    if removed:
        await message.answer(f"✅ Removed {identifier}")
    else:
        await message.answer(f"❌ {identifier} not found in monitors")


def register_monitor_handlers(router: Router, monitor_service: MonitorServiceProtocol) -> None:
    """Register monitor management handlers."""

    @router.message(Command("monitor"))
    async def cmd_monitor(message: Message) -> None:
        if not message.from_user:
            return

        args = (message.text or "").split()
        owner_user_id = message.from_user.id

        if len(args) == 1:
            await _handle_monitor_list(
                message=message,
                owner_user_id=owner_user_id,
                monitor_service=monitor_service,
            )
        elif args[1] == "add":
            await _handle_monitor_add(
                message=message,
                args=args,
                owner_user_id=owner_user_id,
                monitor_service=monitor_service,
            )
        elif args[1] == "remove":
            await _handle_monitor_remove(
                message=message,
                args=args,
                owner_user_id=owner_user_id,
                monitor_service=monitor_service,
            )
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

        forwarded_chat = extract_forwarded_chat(message)
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

        await message.answer(
            f"✅ Monitoring {monitor.title} ({monitor_identifier_text(monitor)})"
        )
