from dataclasses import dataclass, field
from datetime import timedelta


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
