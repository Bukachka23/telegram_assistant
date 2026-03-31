"""Telethon userbot client for reading public channels."""

import logging

from telethon import TelegramClient

logger = logging.getLogger(__name__)


def create_telethon_client(
    api_id: int,
    api_hash: str,
    session_name: str = "userbot",
) -> TelegramClient:
    """Create a Telethon client for userbot operations.

    First run requires phone number + auth code (interactive).
    Subsequent runs reuse the saved session file.
    """
    return TelegramClient(session_name, api_id, api_hash)
