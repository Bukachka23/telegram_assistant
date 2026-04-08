from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from bot.config.constants import ASYNC_TOOL_PREFIX, SECONDS_PER_MINUTE

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from bot.services.scheduler import BotSchedulerService
    from bot.tools.registry import ToolRegistry


def register_scheduler_tools(registry: ToolRegistry) -> None:
    """Register scheduler tool stubs (async dispatch via LLMService)."""
    registry.register(
        name="schedule",
        description=(
            "Create a scheduled reminder. "
            "The system prompt always contains the current local date and time — use it. "
            "For a specific wall-clock time ('at 17:00', 'tomorrow at 9:00') use cron_expr "
            "(e.g. '0 17 * * *' = at 17:00 every day) with once=true for a one-shot reminder. "
            "Use delay_seconds ONLY for relative delays ('in 30 minutes' = 1800). "
            "Never pass delay_seconds=0 unless the user explicitly asked to be reminded right now."
        ),
        parameters={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Unique task name (used to identify, replace, or remove)",
                },
                "message": {
                    "type": "string",
                    "description": (
                        "Reminder text sent when task fires. "
                        "Use plain text only — no Markdown, no **bold**, no _italic_. "
                        "URLs can be included as plain text."
                    ),
                },
                "delay_seconds": {
                    "type": "number",
                    "description": "Delay in seconds for one-shot reminder (e.g. 3600 = 1 hour)",
                },
                "cron_expr": {
                    "type": "string",
                    "description": "Cron expression for recurring tasks (e.g. '0 9 * * *')",
                },
                "once": {
                    "type": "boolean",
                    "description": "For cron: run only once at next match (default true)",
                },
            },
            "required": ["name", "message"],
        },
        fn=lambda **_: f"{ASYNC_TOOL_PREFIX}schedule",
    )

    registry.register(
        name="list_schedules",
        description="List all scheduled tasks with their status and next trigger time.",
        parameters={
            "type": "object",
            "properties": {},
        },
        fn=lambda **_: f"{ASYNC_TOOL_PREFIX}list_schedules",
    )

    registry.register(
        name="remove_schedule",
        description="Delete a scheduled task by name.",
        parameters={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Task name to delete",
                },
            },
            "required": ["name"],
        },
        fn=lambda **_: f"{ASYNC_TOOL_PREFIX}remove_schedule",
    )


def build_schedule_executor(scheduler: BotSchedulerService) -> Callable[..., Awaitable[str]]:
    """Build the async executor for the 'schedule' tool."""

    async def executor(  # noqa: RUF029
        name: str,
        message: str = "",
        delay_seconds: float | None = None,
        cron_expr: str | None = None,
        *,
        once: bool = True,
    ) -> str:
        try:
            job = scheduler.add_job(
                name=name,
                message=message,
                delay_seconds=delay_seconds,
                cron_expr=cron_expr,
                once=once,  # keyword-only forwarded
            )
        except ValueError as exc:
            return f"Error: {exc}"

        return _format_created_job(job, scheduler.tz)

    return executor


def build_list_schedules_executor(scheduler: BotSchedulerService) -> Callable[[], Awaitable[str]]:
    """Build the async executor for the 'list_schedules' tool."""

    async def executor() -> str:  # noqa: RUF029
        jobs = scheduler.list_jobs()
        return _format_job_list(jobs, scheduler.tz)

    return executor


def build_remove_schedule_executor(scheduler: BotSchedulerService) -> Callable[[str], Awaitable[str]]:
    """Build the async executor for the 'remove_schedule' tool."""

    async def executor(name: str) -> str:  # noqa: RUF029
        deleted = scheduler.remove_job(name)
        if deleted:
            return f"✅ Deleted scheduled task '{name}'"
        return f"❌ Task '{name}' not found"

    return executor


def _format_created_job(job: dict[str, Any], tz: timezone) -> str:
    job_type = job.get("type", "")
    name = job.get("name", "")

    if job_type == "once":
        trigger_at = datetime.fromtimestamp(float(job["trigger_at"]), tz)
        when = trigger_at.strftime("%Y-%m-%d %H:%M:%S")
        return f"✅ Scheduled '{name}' — one-shot at {when}"
    if job_type == "once_cron":
        return f"✅ Scheduled '{name}' — one-shot cron: {job.get('cron_expr', '?')}"
    return f"✅ Scheduled '{name}' — recurring cron: {job.get('cron_expr', '?')}"


def _format_job_list(jobs: list[dict[str, Any]], tz: timezone) -> str:
    if not jobs:
        return "No scheduled tasks."

    now = datetime.now(tz).timestamp()
    lines = [f"Scheduled tasks ({len(jobs)}):"]

    for job in jobs:
        name = job.get("name", "?")
        message = (job.get("message") or "")[:60]
        job_type = job.get("type", "")

        if job_type == "once":
            remaining = max(0, int(float(job.get("trigger_at", 0)) - now))
            lines.append(f"  ⏱ {name} (one-shot, {_format_remaining(remaining)}): {message}")
        else:
            cron = job.get("cron_expr", "?")
            kind = "once" if job_type == "once_cron" else "recurring"
            lines.append(f"  🔁 {name} ({kind}, {cron}): {message}")

    return "\n".join(lines)


def _format_remaining(seconds: int) -> str:
    if seconds < SECONDS_PER_MINUTE:
        return f"{seconds}s"
    minutes, secs = divmod(seconds, SECONDS_PER_MINUTE)
    hours, minutes = divmod(minutes, SECONDS_PER_MINUTE)
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m {secs}s"
