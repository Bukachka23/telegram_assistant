from datetime import timedelta

from bot.config.constants import SECONDS_PER_MINUTE
from bot.domain.models.health import HealthReport


def format_health_report(report: HealthReport) -> str:
    """Render a health report as a compact Telegram-friendly status message."""
    uptime_text = _format_uptime(report.uptime)

    lines = [
        "📊 **System Status**\n",
        f"⏱ Uptime: {uptime_text}",
        f"🐍 Python: {report.python_version}",
        f"💻 Platform: {report.platform}",
        f"🤖 Model: `{report.model}`\n",
        "**Services:**",
        f"  {'✅' if report.telethon_connected else '❌'} Telethon userbot",
        f"  {'✅' if report.tavily_available else '❌'} Web search (Tavily)",
        f"  {'✅' if report.deep_research_available else '❌'} Deep research",
        f"  {'✅' if report.telegraph_available else '❌'} Telegraph publishing\n",
        "**Data:**",
        f"  🧠 Memories: {report.memory_count}",
        f"  📡 Monitors: {report.monitor_count}",
        f"  📓 Vault notes: {report.vault_note_count}",
        f"  📁 Vault path: `{report.vault_path}`",
        f"  📊 Tracked requests: {report.request_count}",
    ]

    if report.errors:
        lines.append("\n⚠️ **Issues:**")
        lines.extend(f"  • {error}" for error in report.errors)

    return "\n".join(lines)


def _format_uptime(uptime: timedelta) -> str:
    total_seconds = int(uptime.total_seconds())
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
