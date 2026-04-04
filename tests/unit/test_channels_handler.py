"""Tests for channel monitoring handlers."""

import bot.handlers.channels as channels_handler
from bot.domain.models import PersistedMonitor


def test_returns_monitor_for_matching_chat_id_and_keyword() -> None:
    monitors = [
        PersistedMonitor(chat_id=1001, title="Python", keywords=["asyncio"], owner_user_id=1),
        PersistedMonitor(chat_id=2002, title="AI", keywords=["llm"], owner_user_id=1),
    ]

    result = channels_handler._find_matching_monitor(monitors, 1001, "Asyncio tips and tricks")

    assert result == monitors[0]


def test_returns_none_for_different_chat_id() -> None:
    monitors = [
        PersistedMonitor(chat_id=1001, title="Python", keywords=["asyncio"], owner_user_id=1)
    ]

    result = channels_handler._find_matching_monitor(monitors, 2002, "Asyncio tips and tricks")

    assert result is None


def test_returns_monitor_when_keywords_are_empty() -> None:
    monitors = [PersistedMonitor(chat_id=1001, title="Python", keywords=[], owner_user_id=1)]

    result = channels_handler._find_matching_monitor(monitors, 1001, "Anything at all")

    assert result == monitors[0]


def test_private_channel_without_username_still_matches_by_chat_id() -> None:
    monitor = PersistedMonitor(
        owner_user_id=1,
        chat_id=-100123,
        title="Private Channel",
        keywords=["supplements"],
        username="",
        source_type="forwarded_private",
    )

    result = channels_handler._find_matching_monitor([monitor], -100123, "Supplements update")

    assert result == monitor


def test_build_notification_includes_channel_title_and_keywords() -> None:
    monitor = PersistedMonitor(
        owner_user_id=1,
        chat_id=1001,
        title="Python",
        keywords=["asyncio", "telethon"],
    )

    result = channels_handler._build_notification(text="Useful asyncio update", monitor=monitor, chat_title="Python News")

    assert "📢 **Python News**" in result
    assert "Useful asyncio update" in result
    assert "Matched keywords: asyncio, telethon" in result


def test_truncates_long_message_preview() -> None:
    monitor = PersistedMonitor(owner_user_id=1, chat_id=1001, title="Python", keywords=[])
    text = "a" * 350

    result = channels_handler._build_notification(text=text, monitor=monitor, chat_title="Python News")

    assert "a" * 300 in result
    assert "a" * 301 not in result
    assert "..." in result
    assert "Matched keywords: all" in result
