"""Domain models re-exported for backward-compatible imports."""

from bot.domain.models.agents import AgentProfile
from bot.domain.models.base import Conversation, Message, Role
from bot.domain.models.config import (
    ChannelMonitorEntry,
    ChannelsConfig,
    ConversationConfig,
    LLMConfig,
    StreamingConfig,
    TelegraphConfig,
    VaultConfig,
)
from bot.domain.models.metrics import RequestMetric
from bot.domain.models.monitors import ChannelFilter, PersistedMonitor
from bot.domain.models.research import JudgeDecision, ResearchState
from bot.domain.models.tools import StreamDelta, TokenUsage, Tool, ToolCall, ToolResult
from bot.domain.models.vault import Note
from bot.domain.protocols import ForwardedChatLike, MonitorDisplay

__all__ = [
    "AgentProfile",
    "ChannelFilter",
    "ChannelMonitorEntry",
    "ChannelsConfig",
    "Conversation",
    "ConversationConfig",
    "ForwardedChatLike",
    "JudgeDecision",
    "LLMConfig",
    "Message",
    "MonitorDisplay",
    "Note",
    "PersistedMonitor",
    "RequestMetric",
    "ResearchState",
    "Role",
    "StreamDelta",
    "StreamingConfig",
    "TelegraphConfig",
    "TokenUsage",
    "Tool",
    "ToolCall",
    "ToolResult",
    "VaultConfig",
]
