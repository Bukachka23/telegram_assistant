"""One-time Telethon authentication script.

Run this ONCE to create the session file:
    python scripts/auth_telethon.py

It will ask for your phone number and verification code.
After success, a session file is created.
The bot will use this session file automatically.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bot.config.config import load_settings


async def main() -> None:
    settings = load_settings()

    if not settings.telegram_api_id or not settings.telegram_api_hash:
        print("❌ Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env")
        sys.exit(1)

    from telethon import TelegramClient

    # Save session in data/ if it exists (Docker), otherwise current dir
    data_dir = Path("data")
    if data_dir.is_dir():
        session_path = "data/userbot"
    else:
        session_path = "userbot"

    client = TelegramClient(
        session_path,
        settings.telegram_api_id,
        settings.telegram_api_hash,
    )

    print("🔐 Telethon Authentication")
    print("=" * 40)
    print("A code will be sent to your Telegram app.")
    print("Check 'Telegram' service messages.\n")

    await client.start()  # type: ignore

    me = await client.get_me()
    first_name = getattr(me, "first_name", "Unknown")
    user_id = getattr(me, "id", "?")
    print(f"\n✅ Authenticated as: {first_name} (ID: {user_id})")
    print(f"📁 Session saved to: {session_path}.session")
    print(
        f"\n💡 Set OWNER_USER_ID={user_id} in your .env"
        " if not already set."
    )

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
