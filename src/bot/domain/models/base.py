from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(frozen=True)
class Message:
    """A single message in a conversation."""

    role: Role
    content: str
    tool_call_id: str | None = None
    tool_calls: list[dict] | None = None


@dataclass
class Conversation:
    """A conversation session with message history."""

    user_id: int
    messages: list[Message] = field(default_factory=list)
    model: str = ""
    active_agent: str = "default"
    telegraph_enabled: bool = True
    last_active: datetime = field(default_factory=lambda: datetime.now(UTC))

    def add(self, message: Message) -> None:
        self.messages.append(message)
        self.last_active = datetime.now(UTC)

    def trim(self, max_messages: int) -> None:
        """Keep only the last N messages (preserving system prompts)."""
        if len(self.messages) <= max_messages:
            return
        system: list[Message] = []
        rest: list[Message] = []
        for m in self.messages:
            (system if m.role == Role.SYSTEM else rest).append(m)
        self.messages = system + rest[-(max_messages - len(system)) :]
