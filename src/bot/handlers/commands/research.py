import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.domain.exceptions import LLMError, TelegraphError
from bot.domain.protocols import DeepResearchServiceProtocol
from bot.handlers.commands.utils import extract_query
from bot.services.conversation import ConversationManager
from bot.services.formatting import split_for_telegram
from bot.services.telegraph import TelegraphPublishService

logger = logging.getLogger(__name__)


async def _execute_deep_research(
    *,
    deep_research: DeepResearchServiceProtocol,
    query: str,
    model: str,
    user_id: int,
    send_message: Callable[..., Awaitable[Any]],
) -> str | None:
    """Execute the deep research service and handle any resulting exceptions."""
    try:
        return await deep_research.run(query=query, model=model, on_progress=send_message)
    except LLMError as error:
        logger.exception("Deep research failed for user %d", user_id)
        await send_message(f"⚠️ Deep research failed: {error}")
        return None
    except Exception:
        logger.exception("Unexpected deep research error for user %d", user_id)
        await send_message("⚠️ Deep research failed. Please try again.")
        return None


def register_research_handlers(
    router: Router,
    conversations: ConversationManager,
    deep_research: DeepResearchServiceProtocol | None = None,
    telegraph: TelegraphPublishService | None = None,
) -> None:
    """Register deep research handlers."""

    @router.message(Command("deep"))
    async def cmd_deep(message: Message) -> None:
        if not message.from_user:
            return

        if deep_research is None:
            await message.answer("⚠️ Deep research is not available right now.")
            return

        query = extract_query(message.text)
        if not query:
            await message.answer("Usage: /deep <question>")
            return

        user_id = message.from_user.id
        model = conversations.get_model(user_id)
        answer = await _execute_deep_research(
            deep_research=deep_research,
            query=query,
            model=model,
            user_id=user_id,
            send_message=message.answer,
        )

        if answer:
            if telegraph and conversations.is_telegraph_enabled(user_id):
                try:
                    result = await telegraph.publish(
                        answer,
                        title=query[:60],
                        model=model,
                        agent="researcher",
                    )
                except TelegraphError:
                    logger.warning("Telegraph publish failed for deep research")
                    await message.answer("⚠️ Telegra.ph unavailable, sending inline.")
                else:
                    await message.answer(
                        f"{result.preview}\n\n📄 Deep research: {result.url}",
                    )
                    return

            for chunk in split_for_telegram(answer):
                await message.answer(chunk, parse_mode="HTML")
