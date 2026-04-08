from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from bot.config.constants import CRON_TYPES, JOB, TICK_SECONDS, TIMEOUT_BACK_LOOP

if TYPE_CHECKING:
    from collections.abc import Callable


class PersistentScheduler:
    """A small persistent scheduler for LLM or automation projects."""

    def __init__(
        self,
        jobs_file: str,
        on_trigger: Callable[[JOB], Any],
        *,
        tz: timezone = timezone(timedelta(hours=8)),
        tick_seconds: float = TICK_SECONDS,
        trigger_async: bool = True,
        logger: logging.Logger | None = None,
    ) -> None:
        self.jobs_file = Path(jobs_file).resolve()
        self.on_trigger = on_trigger
        self.timezone = tz
        self.tick_seconds = tick_seconds
        self.trigger_async = trigger_async
        self.log = logger or logging.getLogger(__name__)

        self._jobs_lock = threading.Lock()
        self._jobs: list[JOB] = []
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        self._load_jobs()

    def start(self) -> None:
        """Start background loop if not already running."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, name="scheduler-loop", daemon=True)
        self._thread.start()
        self.log.info("[scheduler] started (%d jobs loaded)", len(self._jobs))

    def stop(self, timeout: float = TIMEOUT_BACK_LOOP) -> None:
        """Stop background loop."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        self._thread = None

    def _build_base_job(self, name: str, message: str, payload: dict[str, Any] | None) -> JOB:
        """Build the shared job fields (name, message, payload, timestamps)."""
        now = datetime.now(self.timezone)
        return {
            "name": name,
            "message": message,
            "payload": payload or {},
            "created": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "created_ts": time.time(),
        }

    def _configure_cron_job(self, job: JOB, cron_expr: str, job_type: Literal["cron", "once_cron"]) -> None:
        """Set cron type and expression on a job dict."""
        self._require_croniter()
        job.update({"type": job_type, "cron_expr": str(cron_expr)})

    def _upsert_job(self, job: JOB) -> None:
        """Replace any existing job with the same name and persist to disk."""
        with self._jobs_lock:
            self._jobs[:] = [j for j in self._jobs if j.get("name") != job["name"]]
            self._jobs.append(job)
            self._save_jobs_locked()

    def add_job(
        self,
        *,
        name: str,
        message: str = "",
        delay_seconds: float | None = None,
        cron_expr: str | None = None,
        once: bool = True,
        payload: dict[str, Any] | None = None,
    ) -> JOB:
        """Create or replace a job by name."""
        self._validate_job_params(name, delay_seconds, cron_expr)
        job = self._build_base_job(name, message, payload)

        if delay_seconds is not None:
            self._configure_delay_job(job, delay_seconds)
        else:
            if cron_expr is None:
                msg = "cron_expr must be provided for cron jobs"
                raise ValueError(msg)
            job_type: Literal["cron", "once_cron"] = "once_cron" if once else "cron"
            self._configure_cron_job(job, cron_expr, job_type)

        self._upsert_job(job)
        self.log.info("[scheduler] added job: %s {%s}", name, job["type"])
        return dict(job)

    def list_jobs(self) -> list[JOB]:
        """Return a shallow copy of all jobs."""
        with self._jobs_lock:
            return [dict(j) for j in self._jobs]

    def remove_job(self, name: str) -> bool:
        """Remove a job by name. Returns True if deleted."""
        with self._jobs_lock:
            before = len(self._jobs)
            self._jobs[:] = [j for j in self._jobs if j.get("name") != name]
            changed = len(self._jobs) < before
            if changed:
                self._save_jobs_locked()

        if changed:
            self.log.info("[scheduler] removed job: %s", name)
        return changed

    def tick_once(self) -> None:
        """Run one scheduling check — useful for tests."""
        self._check_due_jobs()

    def _load_jobs(self) -> None:
        if not self.jobs_file.exists():
            self._jobs = []
            return

        try:
            with self.jobs_file.open(encoding="utf-8") as fh:
                data = json.load(fh)
                self._jobs = data if isinstance(data, list) else []
        except Exception:
            self.log.exception("[scheduler] failed to load jobs")
            self._jobs = []

    def _save_jobs_locked(self) -> None:
        self.jobs_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.jobs_file.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(self._jobs, fh, ensure_ascii=False, indent=2)
        tmp.replace(self.jobs_file)

    def _check_due_jobs(self) -> None:
        now = time.time()
        to_trigger: list[JOB] = []

        with self._jobs_lock:
            remaining: list[JOB] = []
            for job in self._jobs:
                should_trigger, should_retain = self._classify_job(job, now)
                if should_trigger:
                    to_trigger.append(dict(job))
                if should_retain:
                    remaining.append(job)

            self._jobs[:] = remaining
            if to_trigger:
                self._save_jobs_locked()

        for job in to_trigger:
            self._dispatch(job)

    def _classify_job(self, job: JOB, now: float) -> tuple[bool, bool]:
        """Classify a job as due and/or to be retained."""
        job_type = job.get("type")

        if job_type == "once":
            is_due = now >= float(job.get("trigger_at", 0))
            return is_due, not is_due

        if job_type not in CRON_TYPES:
            return False, True

        try:
            next_ts = self._next_cron_timestamp(job, now)
        except Exception:
            self.log.exception("[scheduler] cron error for %s", job.get("name", "?"))
            return False, True

        if now < next_ts:
            return False, True

        if job_type == "cron":
            job["last_run"] = now
            return True, True

        return True, False

    def _next_cron_timestamp(self, job: JOB, now_ts: float) -> float:
        croniter = self._require_croniter()
        last_run = job.get("last_run")
        if not isinstance(last_run, int | float):
            last_run = job.get("created_ts", now_ts - 60)
        base_dt = datetime.fromtimestamp(float(last_run), self.timezone)
        return croniter(job["cron_expr"], base_dt).get_next(datetime).timestamp()

    def _dispatch(self, job: JOB) -> None:
        self.log.info("[scheduler] triggering: %s", job.get("name", "?"))
        if self.trigger_async:
            threading.Thread(target=self._trigger_job, args=(job,), daemon=True).start()
        else:
            self._trigger_job(job)

    def _trigger_job(self, job: JOB) -> None:
        try:
            self.on_trigger(dict(job))
        except Exception:
            self.log.exception("[scheduler] job failed")

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._check_due_jobs()
            except Exception:
                self.log.exception("[scheduler] loop error")
            self._stop_event.wait(self.tick_seconds)

    @staticmethod
    def _validate_job_params(name: str, delay_seconds: float | None, cron_expr: str | None) -> None:
        """Raise ValueError if scheduling params are invalid."""
        if not name or not isinstance(name, str):
            msg = "name must be a non-empty string"
            raise ValueError(msg)

        if (delay_seconds is not None) == bool(cron_expr):
            msg = "provide exactly one of delay_seconds or cron_expr"
            raise ValueError(msg)

    @staticmethod
    def _configure_delay_job(job: JOB, delay_seconds: float) -> None:
        """Set type='once' and trigger_at on a job dict. Raises ValueError if delay < 0."""
        delay_value = float(delay_seconds)
        if delay_value < 0:
            msg = "delay_seconds must be >= 0"
            raise ValueError(msg)

        job.update({"type": "once", "trigger_at": time.time() + delay_value})

    @staticmethod
    def _require_croniter() -> Any:  # noqa: ANN401
        try:
            from croniter import croniter  # type: ignore[import-untyped]  # noqa: PLC0415
        except ImportError as exc:
            msg = "croniter is required for cron-based jobs"
            raise RuntimeError(msg) from exc

        return croniter
