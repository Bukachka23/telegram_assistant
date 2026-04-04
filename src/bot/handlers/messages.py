import logging
import time

from aiogram import Bot, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message

from bot.config.constants import MAX_TG_TEXT
from bot.domain.exceptions import LLMError
from bot.services.formatting import split_for_telegram
from bot.services.llm import LLMService

logger = logging.getLogger(__name__)

router = Router(name="messages")


def _clip(text: str) -> str:
    """Clip text to Telegram's max message length."""
    if len(text) <= MAX_TG_TEXT:
        return text
    return "… " + text[-(MAX_TG_TEXT - 2) :]


def setup_messages(*, llm: LLMService, draft_interval_ms: int = 800) -> Router:
    """Configure the free-text message handler with streaming."""

    @router.message()
    async def handle_message(message: Message, bot: Bot) -> None:
        if not message.from_user or not message.text:
            return

        user_id = message.from_user.id
        chat_id = message.chat.id

        try:
            await _stream_response(
                bot=bot,
                chat_id=chat_id,
                llm=llm,
                user_id=user_id,
                user_text=message.text,
                draft_interval_ms=draft_interval_ms,
            )
        except LLMError as e:
            logger.exception("LLM error for user %d", user_id)
            await message.answer(f"⚠️ LLM error: {e}")
        except Exception:
            logger.exception("Unexpected error for user %d", user_id)
            await message.answer("⚠️ Something went wrong. Please try again.")

    return router


async def _send_draft(*, bot: Bot, chat_id: int, draft_id: int, text: str) -> bool:
    """Send a streaming draft. Returns False if unsupported."""
    try:
        await bot.send_message_draft(chat_id=chat_id, draft_id=draft_id, text=_clip(text))
    except TelegramAPIError as e:
        logger.debug("sendMessageDraft failed: %s", e)
        return False
    else:
        return True


async def _send_formatted(*, bot: Bot, chat_id: int, text: str) -> None:
    """Send final message with HTML formatting, splitting if too long."""
    chunks = split_for_telegram(text)
    if not chunks:
        await bot.send_message(chat_id=chat_id, text=_clip(text))
        return

    try:
        for chunk in chunks:
            await bot.send_message(chat_id=chat_id, text=chunk, parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        logger.debug("HTML send failed, falling back to plain text")
        await bot.send_message(chat_id=chat_id, text=_clip(text))


async def _stream_response(
    *,
    bot: Bot,
    chat_id: int,
    llm: LLMService,
    user_id: int,
    user_text: str,
    draft_interval_ms: int,
) -> None:
    """Stream LLM response via sendMessageDraft, then send formatted final."""
    draft_id = int(time.time() * 1000) % 2_147_483_647 or 1
    interval = draft_interval_ms / 1000.0
    accumulated = ""
    last_send = 0.0

    # Immediate feedback
    use_drafts = await _send_draft(bot=bot, chat_id=chat_id, draft_id=draft_id, text="Thinking…")

    async for chunk in llm.stream_response(user_id, user_text):
        accumulated += chunk

        if not use_drafts:
            continue

        now = time.time()
        if now - last_send >= interval:
            use_drafts = await _send_draft(bot=bot, chat_id=chat_id, draft_id=draft_id, text=accumulated)
            last_send = now

    # Send final formatted message (HTML with Markdown conversion)
    if accumulated:
        await _send_formatted(bot=bot, chat_id=chat_id, text=accumulated)
    else:
        await bot.send_message(chat_id=chat_id, text="🤔 No response generated.")
