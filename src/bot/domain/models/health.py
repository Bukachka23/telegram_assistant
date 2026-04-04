from dataclasses import dataclass, field
from datetime import timedelta

from bot.config.constants import SECONDS_PER_MINUTE


@dataclass(frozen=True)
class HealthReport:
    """Snapshot of system health metrics."""

    uptime: timedelta
    python_version: str
    platform: str
    model: str
    memory_count: int
    monitor_count: int
    vault_path: str
    vault_note_count: int
    telethon_connected: bool
    tavily_available: bool
    deep_research_available: bool
    telegraph_available: bool = False
    request_count: int = 0
    errors: list[str] = field(default_factory=list)

    def format_telegram(self) -> str:
        """Render as a compact Telegram-friendly status message."""
        uptime_text = self._format_uptime()

        lines = [
            "📊 **System Status**\n",
            f"⏱ Uptime: {uptime_text}",
            f"🐍 Python: {self.python_version}",
            f"💻 Platform: {self.platform}",
            f"🤖 Model: `{self.model}`\n",
            "**Services:**",
            f"  {'✅' if self.telethon_connected else '❌'} Telethon userbot",
            f"  {'✅' if self.tavily_available else '❌'} Web search (Tavily)",
            f"  {'✅' if self.deep_research_available else '❌'} Deep research",
            f"  {'✅' if self.telegraph_available else '❌'} Telegraph publishing\n",
            "**Data:**",
            f"  🧠 Memories: {self.memory_count}",
            f"  📡 Monitors: {self.monitor_count}",
            f"  📓 Vault notes: {self.vault_note_count}",
            f"  📁 Vault path: `{self.vault_path}`",
            f"  📊 Tracked requests: {self.request_count}",
        ]

        if self.errors:
            lines.append("\n⚠️ **Issues:**")
            lines.extend(f"  • {error}" for error in self.errors)

        return "\n".join(lines)

    def _format_uptime(self) -> str:
        total_seconds = int(self.uptime.total_seconds())
        if total_seconds < SECONDS_PER_MINUTE:
            return f"{total_seconds}s"
        minutes, seconds = divmod(total_seconds, SECONDS_PER_MINUTE)
        hours, minutes = divmod(minutes, SECONDS_PER_MINUTE)
        days, hours = divmod(hours, 24)
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        return " ".join(parts) or f"{seconds}s"
