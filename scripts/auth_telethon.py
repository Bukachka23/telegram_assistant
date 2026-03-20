"""One-time Telethon authentication script.

Run this ONCE to create the session file:
    python scripts/auth_telethon.py

It will ask for your phone number and verification code.
After success, a 'userbot.session' file is created.
The bot will use this session file automatically.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bot.config import load_settings


async def main() -> None:
    settings = load_settings()

    if not settings.telegram_api_id or not settings.telegram_api_hash:
        print("❌ Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env first")
        sys.exit(1)

    from telethon import TelegramClient

    client = TelegramClient(
        "userbot", settings.telegram_api_id, settings.telegram_api_hash
    )

    print("🔐 Telethon Authentication")
    print("=" * 40)
    print("This will send a code to your Telegram app.")
    print("Check 'Telegram' service messages in your app.\n")

    await client.start()

    me = await client.get_me()
    print(f"\n✅ Authenticated as: {me.first_name} (ID: {me.id})")
    print("📁 Session saved to: userbot.session")
    print(f"\n💡 Set OWNER_USER_ID={me.id} in your .env if not already set.")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
