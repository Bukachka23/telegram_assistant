import logging
from datetime import UTC, datetime, timedelta

from bot.domain.models import Conversation, Message, Role
from bot.shared.agents.registry import get_default_agent
from bot.shared.constants import MAX_HISTORY, SESSION_TIMEOUT_MINUTES

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages per-user conversation sessions with timeout-based cleanup."""

    def __init__(
        self,
        default_model: str,
        *,
        session_timeout_minutes: int = SESSION_TIMEOUT_MINUTES,
        max_history: int = MAX_HISTORY,
    ) -> None:
        self._sessions: dict[int, Conversation] = {}
        self._default_model = default_model
        self._timeout = timedelta(minutes=session_timeout_minutes)
        self._max_history = max_history

    def get_or_create(self, user_id: int) -> Conversation:
        """Get existing session or create a new one. Expired sessions reset."""
        session = self._sessions.get(user_id)
        if session and (datetime.now(UTC) - session.last_active) < self._timeout:
            return session
        return self._new_session(user_id)

    def add_message(self, user_id: int, message: Message) -> None:
        """Add a message to the user's conversation."""
        session = self.get_or_create(user_id)
        session.add(message)
        session.trim(self._max_history)

    def get_messages_for_api(
        self,
        user_id: int,
        *,
        system_prompt: str | None = None,
    ) -> list[dict]:
        """Return messages formatted for OpenRouter API."""
        session = self.get_or_create(user_id)
        result = []
        for index, msg in enumerate(session.messages):
            content = msg.content
            if index == 0 and msg.role == Role.SYSTEM and system_prompt is not None:
                content = system_prompt
            entry: dict = {"role": msg.role.value, "content": content}
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

    def get_active_agent(self, user_id: int) -> str:
        """Return the active agent name for a user's session."""
        return self.get_or_create(user_id).active_agent

    def set_active_agent(self, user_id: int, agent_name: str) -> None:
        """Switch the active agent for a user's session."""
        self.get_or_create(user_id).active_agent = agent_name

    def clear(self, user_id: int) -> None:
        """Clear a user's conversation history."""
        self._sessions.pop(user_id, None)

    def _new_session(self, user_id: int) -> Conversation:
        """Create and store a fresh session with the default agent prompt."""
        default_agent = get_default_agent()
        session = Conversation(
            user_id=user_id,
            model=self._default_model,
            active_agent=default_agent.name,
        )
        session.add(Message(role=Role.SYSTEM, content=default_agent.prompt))
        self._sessions[user_id] = session
        return session
