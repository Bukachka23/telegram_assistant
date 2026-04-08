from dataclasses import dataclass, field

from bot.domain.protocols import MonitorDisplay


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
class PersistedMonitor(MonitorDisplay):
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
