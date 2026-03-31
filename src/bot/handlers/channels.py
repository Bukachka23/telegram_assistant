import logging

from telethon import TelegramClient, events

from bot.domain.models import PersistedMonitor
from bot.services.monitors import MonitorService
from bot.shared.constants import CHANNEL_MAX_LENGTH_MESSAGE

logger = logging.getLogger(__name__)


def _build_notification(*, text: str, monitor: PersistedMonitor, chat_title: str) -> str:
    """Build a short notification message for a matched channel post."""
    preview = text[:300] + ("..." if len(text) > CHANNEL_MAX_LENGTH_MESSAGE else "")
    matched_keywords = ", ".join(monitor.keywords) or "all"
    return (
        f"📢 **{chat_title}**\n\n"
        f"{preview}\n\n"
        f"_Matched keywords: {matched_keywords}_"
    )


def setup_channel_monitoring(*, userbot: TelegramClient, monitor_service: MonitorService) -> None:
    """Register Telethon event handlers backed by persisted monitor records."""

    @userbot.on(events.NewMessage())
    async def on_channel_message(event: events.NewMessage.Event) -> None:
        if not event.message or not event.message.text:
            return

        chat = await event.get_chat()
        chat_id = getattr(chat, "id", None)
        if chat_id is None:
            return

        monitor = await monitor_service.get_monitor_by_chat_id(int(chat_id))
        if not monitor or not monitor.matches(event.message.text):
            return

        chat_title = getattr(chat, "title", str(chat_id))
        notification = _build_notification(text=event.message.text, monitor=monitor, chat_title=chat_title)

        try:
            await userbot.send_message("me", notification)
            logger.info("Forwarded message from %s to Saved Messages", chat_title)
        except Exception:
            logger.exception("Failed to forward from %s", chat_title)
