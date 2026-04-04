from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta, timezone

from bot.config.constants import TICK_SECONDS, TZ_OFFSET_HOURS
from bot.infrastructure.scheduler_core import PersistentScheduler

logger = logging.getLogger(__name__)

SendFn = Callable[[int, str], Awaitable[None]]
Job = dict[str, object]


class BotSchedulerService:
    """Bridges the thread-based PersistentScheduler with the async bot event loop."""

    def __init__(
        self,
        *,
        jobs_file: str,
        owner_chat_id: int,
        tz_offset_hours: int = TZ_OFFSET_HOURS,
        tick_seconds: float = TICK_SECONDS,
    ) -> None:
        self._owner_chat_id = owner_chat_id
        self._loop: asyncio.AbstractEventLoop | None = None
        self._send_fn: SendFn | None = None
        self._tz = timezone(timedelta(hours=tz_offset_hours))

        self._scheduler = PersistentScheduler(
            jobs_file=jobs_file,
            on_trigger=self._on_trigger,
            tz=self._tz,
            tick_seconds=tick_seconds,
            trigger_async=True,
        )

    def start(self, loop: asyncio.AbstractEventLoop, send_fn: SendFn) -> None:
        """Start the scheduler background thread."""
        if not callable(send_fn):
            msg = f"send_fn must be callable, got {type(send_fn)!r}"
            raise TypeError(msg)

        self._loop = loop
        self._send_fn = send_fn
        self._scheduler.start()
        job_count = len(self._scheduler.list_jobs())
        logger.info("Scheduler started (%d jobs loaded)", job_count)

    def stop(self) -> None:
        """Stop the scheduler background thread."""
        self._scheduler.stop()
        logger.info("Scheduler stopped")

    def add_job(
        self,
        *,
        name: str,
        message: str,
        delay_seconds: float | None = None,
        cron_expr: str | None = None,
        once: bool = True,
    ) -> Job:
        """Add a scheduled job. Returns the job dict."""
        return self._scheduler.add_job(  # type: ignore[return-value]
            name=name,
            message=message,
            delay_seconds=delay_seconds,
            cron_expr=cron_expr,
            once=once,
        )

    def list_jobs(self) -> list[Job]:
        """Return all scheduled jobs."""
        return self._scheduler.list_jobs()  # type: ignore[return-value]

    def remove_job(self, name: str) -> bool:
        """Remove a job by name. Returns True if deleted."""
        return self._scheduler.remove_job(name)  # type: ignore[return-value]

    @property
    def tz(self) -> timezone:
        return self._tz

    def _on_trigger(self, job: Job) -> None:
        """Called from the scheduler thread when a job fires."""
        loop = self._loop
        send_fn = self._send_fn

        if loop is None or send_fn is None:
            logger.warning("Scheduler triggered but bot not ready: %s", job.get("name"))
            return

        message = str(job.get("message", "")).strip()
        # Show only the user-facing message — never expose the internal job name.
        # Fallback to a generic header when the job has no message.
        text = f"⏰ {message}" if message else "⏰ Reminder"

        asyncio.run_coroutine_threadsafe(self._safe_send(send_fn, text), loop)

    async def _safe_send(self, send_fn: SendFn, text: str) -> None:
        """Send a reminder message to the owner, catching any errors."""
        try:
            await send_fn(self._owner_chat_id, text)
        except Exception:
            logger.exception("Failed to send scheduled reminder")
