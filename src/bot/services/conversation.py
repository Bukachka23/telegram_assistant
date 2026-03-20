"""Session-based conversation memory management."""

import logging
from datetime import datetime, timedelta

from bot.domain.models import Conversation, Message, Role

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a helpful personal assistant in Telegram. "
    "You have access to tools for searching and managing an Obsidian vault, "
    "and for querying Telegram channels. Use tools when the user's request "
    "requires accessing their notes or channel data. Be concise."
)


class ConversationManager:
    """Manages per-user conversation sessions with timeout-based cleanup."""

    def __init__(
        self,
        default_model: str,
        session_timeout_minutes: int = 30,
        max_history: int = 50,
    ) -> None:
        self._sessions: dict[int, Conversation] = {}
        self._default_model = default_model
        self._timeout = timedelta(minutes=session_timeout_minutes)
        self._max_history = max_history

    def get_or_create(self, user_id: int) -> Conversation:
        """Get existing session or create a new one. Expired sessions reset."""
        session = self._sessions.get(user_id)
        if session and (datetime.now() - session.last_active) < self._timeout:
            return session
        return self._new_session(user_id)

    def add_message(self, user_id: int, message: Message) -> None:
        """Add a message to the user's conversation."""
        session = self.get_or_create(user_id)
        session.add(message)
        session.trim(self._max_history)

    def get_messages_for_api(self, user_id: int) -> list[dict]:
        """Return messages formatted for OpenRouter API."""
        session = self.get_or_create(user_id)
        result = []
        for msg in session.messages:
            entry: dict = {"role": msg.role.value, "content": msg.content}
            if msg.tool_call_id:
                entry["tool_call_id"] = msg.tool_call_id
            if msg.tool_calls:
                entry["tool_calls"] = msg.tool_calls
            result.append(entry)
        return result

    def get_model(self, user_id: int) -> str:
        """Get the current model for a user's session."""
        return self.get_or_create(user_id).model

    def set_model(self, user_id: int, model: str) -> None:
        """Switch the model for a user's session."""
        self.get_or_create(user_id).model = model

    def clear(self, user_id: int) -> None:
        """Clear a user's conversation history."""
        self._sessions.pop(user_id, None)

    def _new_session(self, user_id: int) -> Conversation:
        """Create and store a fresh session with system prompt."""
        session = Conversation(user_id=user_id, model=self._default_model)
        session.add(Message(role=Role.SYSTEM, content=_SYSTEM_PROMPT))
        self._sessions[user_id] = session
        return session
