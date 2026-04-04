"""Tests for scheduler service and tools."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from bot.services.scheduler import BotSchedulerService
from bot.tools.scheduler_tools import (
    build_list_schedules_executor,
    build_remove_schedule_executor,
    build_schedule_executor,
)


@pytest.fixture
def scheduler(tmp_path) -> BotSchedulerService:
    return BotSchedulerService(
        jobs_file=str(tmp_path / "jobs.json"),
        owner_chat_id=12345,
    )


class TestBotSchedulerService:
    def test_add_oneshot_job(self, scheduler):
        job = scheduler.add_job(
            name="test-reminder",
            message="Check email",
            delay_seconds=3600,
        )
        assert job["name"] == "test-reminder"
        assert job["type"] == "once"
        assert job["message"] == "Check email"

    def test_add_cron_job(self, scheduler):
        job = scheduler.add_job(
            name="morning-check",
            message="Good morning!",
            cron_expr="0 9 * * *",
            once=False,
        )
        assert job["name"] == "morning-check"
        assert job["type"] == "cron"

    def test_list_jobs(self, scheduler):
        scheduler.add_job(name="a", message="msg a", delay_seconds=60)
        scheduler.add_job(name="b", message="msg b", delay_seconds=120)

        jobs = scheduler.list_jobs()
        names = {j["name"] for j in jobs}
        assert names == {"a", "b"}

    def test_remove_job(self, scheduler):
        scheduler.add_job(name="temp", message="will remove", delay_seconds=60)
        assert scheduler.remove_job("temp") is True
        assert scheduler.remove_job("temp") is False
        assert scheduler.list_jobs() == []

    def test_replace_job_by_name(self, scheduler):
        scheduler.add_job(name="x", message="v1", delay_seconds=60)
        scheduler.add_job(name="x", message="v2", delay_seconds=120)

        jobs = scheduler.list_jobs()
        assert len(jobs) == 1
        assert jobs[0]["message"] == "v2"

    def test_requires_exactly_one_trigger(self, scheduler):
        with pytest.raises(ValueError, match="exactly one"):
            scheduler.add_job(name="bad", message="m")
        with pytest.raises(ValueError, match="exactly one"):
            scheduler.add_job(name="bad", message="m", delay_seconds=10, cron_expr="* * * * *")

    def test_jobs_persist_across_instances(self, tmp_path):
        jobs_file = str(tmp_path / "persist.json")
        sched1 = BotSchedulerService(jobs_file=jobs_file, owner_chat_id=1)
        sched1.add_job(name="persist-me", message="hello", delay_seconds=9999)

        sched2 = BotSchedulerService(jobs_file=jobs_file, owner_chat_id=1)
        jobs = sched2.list_jobs()
        assert len(jobs) == 1
        assert jobs[0]["name"] == "persist-me"


class TestSchedulerToolExecutors:
    @pytest.mark.asyncio
    async def test_schedule_executor_creates_job(self, scheduler):
        executor = build_schedule_executor(scheduler)
        result = await executor(name="test", message="hi", delay_seconds=60)
        assert "Scheduled 'test'" in result
        assert "one-shot" in result

    @pytest.mark.asyncio
    async def test_schedule_executor_returns_error_on_bad_input(self, scheduler):
        executor = build_schedule_executor(scheduler)
        result = await executor(name="bad", message="m")
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_list_executor_shows_jobs(self, scheduler):
        scheduler.add_job(name="a", message="msg", delay_seconds=300)
        executor = build_list_schedules_executor(scheduler)
        result = await executor()
        assert "a" in result
        assert "one-shot" in result

    @pytest.mark.asyncio
    async def test_list_executor_empty(self, scheduler):
        executor = build_list_schedules_executor(scheduler)
        result = await executor()
        assert "No scheduled tasks" in result

    @pytest.mark.asyncio
    async def test_remove_executor_deletes(self, scheduler):
        scheduler.add_job(name="del-me", message="x", delay_seconds=60)
        executor = build_remove_schedule_executor(scheduler)

        result = await executor("del-me")
        assert "Deleted" in result

        result = await executor("del-me")
        assert "not found" in result


class TestSchedulerTrigger:
    @pytest.mark.asyncio
    async def test_trigger_sends_telegram_message(self, tmp_path):
        send_fn = AsyncMock()
        sched = BotSchedulerService(
            jobs_file=str(tmp_path / "trigger.json"),
            owner_chat_id=42,
            tick_seconds=0.5,
        )
        loop = asyncio.get_running_loop()
        sched.start(loop, send_fn)

        try:
            sched.add_job(name="now", message="Fire!", delay_seconds=0)
            # Give the scheduler thread time to tick and dispatch
            for _ in range(20):
                await asyncio.sleep(0.2)
                if send_fn.call_count > 0:
                    break

            send_fn.assert_called_once()
            call_args = send_fn.call_args
            assert call_args[0][0] == 42
            assert "Fire!" in call_args[0][1]
            assert "Reminder" in call_args[0][1]
        finally:
            sched.stop()
