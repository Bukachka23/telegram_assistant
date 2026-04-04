from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, Field


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


class SchedulerConfig(BaseModel):
    # UTC offset for the owner's local timezone.
    # Vienna = 2 (CEST summer) or 1 (CET winter).
    tz_offset_hours: int = 0


class TelegraphConfig(BaseModel):
    enabled: bool = True
    threshold_chars: int = 8000
    author_name: str = "Telegram Assistant"
    author_url: str = ""


class ForwardedChat(Protocol):
    id: int
    title: str
    username: str | None


@dataclass(frozen=True)
class Note:
    """An Obsidian vault note."""

    path: str
    content: str
    name: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            object.__setattr__(self, "name", self.path.rsplit("/", 1)[-1])
