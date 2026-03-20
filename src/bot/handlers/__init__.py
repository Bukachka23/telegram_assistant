"""Handlers package — auth middleware and router setup."""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

logger = logging.getLogger(__name__)


class OwnerOnlyMiddleware(BaseMiddleware):
    """Silently drop all messages from non-owner users."""

    def __init__(self, owner_user_id: int) -> None:
        self._owner_id = owner_user_id

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Update):
            user_id = self._extract_user_id(event)
            if user_id is not None and user_id != self._owner_id:
                logger.debug("Ignoring update from user %d", user_id)
                return None

        return await handler(event, data)

    @staticmethod
    def _extract_user_id(update: Update) -> int | None:
        """Extract user ID from any update type."""
        for source in (update.message, update.callback_query,
                       update.edited_message, update.inline_query):
            if source:
                user = getattr(source, "from_user", None)
                if user:
                    return user.id
        return None
