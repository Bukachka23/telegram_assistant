
from aiogram.types import Message

from bot.config.constants import MODEL_COMMAND_MIN_PARTS
from bot.domain.protocols import ForwardedChatLike, MonitorDisplay


def build_unknown_command_text(command: str) -> str:
    """Build a help message for unknown slash commands."""
    return (
        f"❌ Unknown command: `{command}`\n\n"
        "Use `/agent` to see available assistant modes and commands."
    )


def parse_monitor_keywords(raw_keywords: str) -> list[str]:
    """Parse comma-separated keyword text into a clean list."""
    if not raw_keywords.strip():
        return []
    return [keyword.strip() for keyword in raw_keywords.split(",") if keyword.strip()]


def monitor_identifier_text(monitor: MonitorDisplay) -> str:
    """Build a stable display identifier for a monitor."""
    return monitor.username or f"id:{monitor.chat_id}"


def parse_stats_days(text: str | None) -> int | None:
    """Parse /stats argument into days. Returns None on invalid input."""
    if not text:
        return 7
    args = text.split(maxsplit=1)
    if len(args) == 1:
        return 7
    arg = args[1].strip().lower()
    if arg == "today":
        return 1
    if arg == "all":
        return 0
    try:
        days = int(arg)
    except ValueError:
        return None
    else:
        return max(days, 0)


def extract_forwarded_chat(message: Message) -> ForwardedChatLike | None:
    """Extract a forwarded channel/chat object from an aiogram message."""
    origin = getattr(message, "forward_origin", None)
    if not origin:
        return None
    chat = getattr(origin, "chat", None)
    if chat is not None:
        return chat
    return getattr(origin, "sender_chat", None)


def extract_query(text: str | None) -> str | None:
    """Extract and validate the query string from the command text."""
    if not text:
        return None

    args = text.split(maxsplit=1)
    if len(args) < MODEL_COMMAND_MIN_PARTS or not args[1].strip():
        return None

    return args[1].strip()
