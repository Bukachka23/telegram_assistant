"""Domain models for the Telegram assistant bot."""

from dataclasses import dataclass, field
from datetime import datetime
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
    last_active: datetime = field(default_factory=datetime.now)

    def add(self, message: Message) -> None:
        self.messages.append(message)
        self.last_active = datetime.now()

    def trim(self, max_messages: int) -> None:
        """Keep only the last N messages (preserving system prompt)."""
        if len(self.messages) <= max_messages:
            return
        system = [m for m in self.messages if m.role == Role.SYSTEM]
        rest = [m for m in self.messages if m.role != Role.SYSTEM]
        self.messages = system + rest[-(max_messages - len(system)) :]


@dataclass(frozen=True)
class Note:
    """An Obsidian vault note."""

    path: str
    content: str
    name: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            object.__setattr__(self, "name", self.path.rsplit("/", 1)[-1])


@dataclass(frozen=True)
class ChannelFilter:
    """A channel monitoring configuration."""

    username: str
    keywords: list[str] = field(default_factory=list)

    def matches(self, text: str) -> bool:
        if not self.keywords:
            return True
        lower = text.lower()
        return any(kw.lower() in lower for kw in self.keywords)


@dataclass(frozen=True)
class ToolCall:
    """An LLM tool call request."""

    id: str
    name: str
    arguments: str  # JSON string


@dataclass(frozen=True)
class ToolResult:
    """Result of executing a tool."""

    tool_call_id: str
    content: str
    is_error: bool = False
