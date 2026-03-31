from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel, Field


class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class MonitorDisplay(Protocol):
    chat_id: int
    username: str
    title: str
    keywords: list[str]


class ForwardedChatLike(Protocol):
    id: int
    title: str
    username: str | None


class LLMConfig(BaseModel):
    default_model: str = "anthropic/claude-sonnet-4"
    max_tokens: int = 4096
    temperature: float = 0.7


class VaultConfig(BaseModel):
    path: str = "/home/pi/obsidian-vault"
    default_folder: str = "notes"


class ConversationConfig(BaseModel):
    session_timeout_minutes: int = 30
    max_history_messages: int = 50


class StreamingConfig(BaseModel):
    draft_interval_ms: int = 800


class ChannelMonitorEntry(BaseModel):
    username: str
    keywords: list[str] = Field(default_factory=list)


class ChannelsConfig(BaseModel):
    monitor: list[ChannelMonitorEntry] = Field(default_factory=list)


class ForwardedChat(Protocol):
    id: int
    title: str
    username: str | None


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
    last_active: datetime = field(default_factory=lambda: datetime.now(UTC))

    def add(self, message: Message) -> None:
        self.messages.append(message)
        self.last_active = datetime.now(UTC)

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
class AgentProfile:
    """A built-in assistant profile selectable per user session."""

    name: str
    command: str
    display_name: str
    prompt: str
    temperature: float
    max_tokens: int
    allowed_tools: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PersistedMonitor:
    """A persisted channel monitor keyed by Telegram chat ID."""

    owner_user_id: int
    chat_id: int
    username: str = ""
    title: str = ""
    keywords: list[str] = field(default_factory=list)
    source_type: str = ""
    created_at: str = ""

    def matches(self, text: str) -> bool:
        if not self.keywords:
            return True
        lower = text.lower()
        return any(keyword.lower() in lower for keyword in self.keywords)


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


@dataclass(frozen=True)
class Tool:
    """A registered tool with its schema and implementation."""

    name: str
    description: str
    parameters: dict[str, Any]
    fn: Callable[..., str]


@dataclass(frozen=True)
class StreamDelta:
    """A single chunk from a streaming response."""

    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str | None = None
