from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


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
class TokenUsage:
    """Token counts from an LLM response."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float | None = None


@dataclass(frozen=True)
class StreamDelta:
    """A single chunk from a streaming response."""

    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str | None = None
    usage: TokenUsage | None = None
