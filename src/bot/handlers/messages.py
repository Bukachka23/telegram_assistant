"""Message handler: free-text → LLM pipeline with streaming via sendMessageDraft."""

import logging
import time

from aiogram import Bot, Router
from aiogram.types import Message

from bot.domain.exceptions import LLMError
from bot.services.llm import LLMService

logger = logging.getLogger(__name__)

router = Router(name="messages")


def setup_messages(
    llm: LLMService,
    draft_interval_ms: int = 150,
    min_chunk_chars: int = 20,
) -> Router:
    """Configure the free-text message handler with streaming."""

    @router.message()
    async def handle_message(message: Message, bot: Bot) -> None:
        if not message.from_user or not message.text:
            return

        user_id = message.from_user.id
        chat_id = message.chat.id

        await bot.send_chat_action(chat_id, "typing")

        try:
            await _stream_response(
                bot=bot,
                chat_id=chat_id,
                llm=llm,
                user_id=user_id,
                user_text=message.text,
                draft_interval_ms=draft_interval_ms,
                min_chunk_chars=min_chunk_chars,
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
    min_chunk_chars: int,
) -> None:
    """Stream LLM response to user via sendMessageDraft, then finalize."""
    accumulated = ""
    draft_id = int(time.time() * 1000) % (2**31 - 1)
    last_draft_time = 0.0
    interval = draft_interval_ms / 1000.0
    use_drafts = True  # Disable if sendMessageDraft fails

    async for chunk in llm.stream_response(user_id, user_text):
        accumulated += chunk
        now = time.monotonic()

        if not use_drafts:
            continue  # Just accumulate, don't try drafts

        enough_time = now - last_draft_time >= interval
        enough_text = len(accumulated) >= min_chunk_chars
        if enough_time and enough_text:
            try:
                await bot.send_message_draft(
                    chat_id=chat_id,
                    draft_id=draft_id,
                    text=accumulated,
                )
                last_draft_time = now
            except Exception as e:
                logger.debug("sendMessageDraft failed, falling back: %s", e)
                use_drafts = False

    # Send the final message (this replaces the draft)
    if accumulated:
        await bot.send_message(chat_id=chat_id, text=accumulated)
    else:
        await bot.send_message(chat_id=chat_id, text="🤔 No response generated.")
