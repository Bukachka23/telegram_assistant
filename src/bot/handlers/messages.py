"""Message handler: free-text → LLM pipeline with streaming via sendMessageDraft."""

import logging
import time

from aiogram import Bot, Router
from aiogram.types import Message

from bot.domain.exceptions import LLMError
from bot.services.llm import LLMService

logger = logging.getLogger(__name__)

router = Router(name="messages")

_MAX_TG_TEXT = 4096


def _clip(text: str) -> str:
    """Clip text to Telegram's max message length."""
    if len(text) <= _MAX_TG_TEXT:
        return text
    return "… " + text[-(_MAX_TG_TEXT - 2) :]


def setup_messages(
    llm: LLMService,
    draft_interval_ms: int = 800,
) -> Router:
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
            logger.error("LLM error for user %d: %s", user_id, e)
            await message.answer(f"⚠️ LLM error: {e}")
        except Exception:
            logger.exception("Unexpected error for user %d", user_id)
            await message.answer("⚠️ Something went wrong. Please try again.")

    return router


async def _stream_response(
    bot: Bot,
    chat_id: int,
    llm: LLMService,
    user_id: int,
    user_text: str,
    draft_interval_ms: int,
) -> None:
    """Stream LLM response to user via sendMessageDraft, then finalize."""
    draft_id = int(time.time() * 1000) % 2_147_483_647 or 1
    interval = draft_interval_ms / 1000.0
    accumulated = ""
    last_send = 0.0
    use_drafts = True

    # Immediate feedback: show "thinking" before LLM responds
    try:
        await bot.send_message_draft(
            chat_id=chat_id, draft_id=draft_id, text="Thinking…"
        )
    except Exception as e:
        logger.debug("sendMessageDraft not supported: %s", e)
        use_drafts = False

    async for chunk in llm.stream_response(user_id, user_text):
        accumulated += chunk

        if not use_drafts:
            continue

        now = time.time()
        if now - last_send >= interval:
            try:
                await bot.send_message_draft(
                    chat_id=chat_id,
                    draft_id=draft_id,
                    text=_clip(accumulated),
                )
                last_send = now
            except Exception as e:
                logger.debug("sendMessageDraft failed: %s", e)
                use_drafts = False

    # Finalize with sendMessage
    await bot.send_message(
        chat_id=chat_id,
        text=_clip(accumulated) or "🤔 No response generated.",
    )
