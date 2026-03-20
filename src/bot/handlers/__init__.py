"""Handlers package — auth middleware and router setup."""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update


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
        # Extract user from the update
        if isinstance(event, Update):
            message = event.message or event.callback_query
            if message:
                user = getattr(message, "from_user", None)
                if user and user.id != self._owner_id:
                    return None  # Silently ignore

        return await handler(event, data)
