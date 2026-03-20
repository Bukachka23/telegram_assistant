"""Telethon event handlers for real-time channel monitoring."""

import logging

from telethon import TelegramClient, events

from bot.domain.models import ChannelFilter

logger = logging.getLogger(__name__)


def setup_channel_monitoring(
    userbot: TelegramClient,
    bot_token: str,
    owner_chat_id: int,
    monitors: list[ChannelFilter],
) -> None:
    """Register Telethon event handlers for monitored channels.

    When a message in a monitored channel matches keywords,
    it forwards a notification to the owner via the bot.
    """
    if not monitors:
        logger.info("No channel monitors configured")
        return

    channel_usernames = [m.username for m in monitors]
    logger.info("Monitoring channels: %s", channel_usernames)

    @userbot.on(events.NewMessage(chats=channel_usernames))
    async def on_channel_message(event: events.NewMessage.Event) -> None:
        if not event.message or not event.message.text:
            return

        text = event.message.text
        chat = await event.get_chat()
        chat_title = getattr(chat, "title", str(chat.id))

        # Check if message matches any monitor's keywords
        for monitor in monitors:
            if monitor.username.lstrip("@") not in str(getattr(chat, "username", "")):
                continue
            if not monitor.matches(text):
                continue

            # Send notification to owner via bot API
            preview = text[:300] + ("..." if len(text) > 300 else "")
            notification = (
                f"📢 **{chat_title}**\n\n"
                f"{preview}\n\n"
                f"_Matched keywords: {', '.join(monitor.keywords) or 'all'}_"
            )

            try:
                # Use Telethon to send message as userbot to self (Saved Messages)
                await userbot.send_message("me", notification)
                logger.info("Forwarded message from %s to owner", chat_title)
            except Exception as e:
                logger.error("Failed to forward from %s: %s", chat_title, e)
            break
