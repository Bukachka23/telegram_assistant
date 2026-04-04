"""Tests for shared async decorators."""

import asyncio

import pytest

from bot.shared.decorators import (
    cache_with_ttl,
    chain_fallbacks,
    enforce_timeout,
    retry_with_backoff,
    validate_output,
)


@pytest.mark.asyncio
async def test_cache_with_ttl_returns_cached_value_before_expiry() -> None:
    calls = 0

    @cache_with_ttl(ttl_seconds=0.05)
    async def compute(value: int) -> int:
        nonlocal calls
        await asyncio.sleep(0)
        calls += 1
        return value + calls

    first = await compute(10)
    second = await compute(10)

    assert first == 11
    assert second == 11
    assert calls == 1


@pytest.mark.asyncio
async def test_cache_with_ttl_recomputes_after_expiry() -> None:
    calls = 0

    @cache_with_ttl(ttl_seconds=0.01)
    async def compute(value: int) -> int:
        nonlocal calls
        await asyncio.sleep(0)
        calls += 1
        return value + calls

    first = await compute(5)
    await asyncio.sleep(0.02)
    second = await compute(5)

    assert first == 6
    assert second == 7
    assert calls == 2


@pytest.mark.asyncio
async def test_chain_fallbacks_uses_next_successful_function() -> None:
    async def fallback_one(_: str) -> str:
        await asyncio.sleep(0)
        msg = "fallback one failed"
        raise LookupError(msg)

    async def fallback_two(value: str) -> str:
        await asyncio.sleep(0)
        return f"fallback:{value}"

    @chain_fallbacks(
        fallback_functions=[fallback_one, fallback_two],  # type: ignore
        handled_exceptions=(LookupError,),
    )
    async def primary(_: str) -> str:
        await asyncio.sleep(0)
        msg = "primary failed"
        raise LookupError(msg)

    result = await primary("ok")

    assert result == "fallback:ok"


@pytest.mark.asyncio
async def test_chain_fallbacks_reraises_last_handled_exception() -> None:
    async def fallback(_: str) -> str:
        await asyncio.sleep(0)
        msg = "fallback failed"
        raise LookupError(msg)

    @chain_fallbacks(
        fallback_functions=[fallback],
        handled_exceptions=(LookupError,),
    )
    async def primary(_: str) -> str:
        await asyncio.sleep(0)
        msg = "primary failed"
        raise LookupError(msg)

    with pytest.raises(LookupError, match="fallback failed"):
        await primary("ignored")


@pytest.mark.asyncio
async def test_enforce_timeout_raises_timeout_error() -> None:
    @enforce_timeout(timeout_seconds=0.01)
    async def slow() -> str:
        await asyncio.sleep(0.05)
        return "done"

    with pytest.raises(TimeoutError, match="timed out"):
        await slow()


@pytest.mark.asyncio
async def test_retry_with_backoff_retries_until_success() -> None:
    attempts = 0

    @retry_with_backoff(
        max_attempts=3,
        base_delay_seconds=0.001,
        backoff_multiplier=1,
        handled_exceptions=(LookupError,),
    )
    async def flaky() -> str:
        nonlocal attempts
        await asyncio.sleep(0)
        attempts += 1
        if attempts < 3:
            msg = "temporary failure"
            raise LookupError(msg)
        return "ok"

    result = await flaky()

    assert result == "ok"
    assert attempts == 3


@pytest.mark.asyncio
async def test_retry_with_backoff_reraises_final_exception() -> None:
    attempts = 0

    @retry_with_backoff(
        max_attempts=2,
        base_delay_seconds=0.001,
        backoff_multiplier=1,
        handled_exceptions=(LookupError,),
    )
    async def always_fails() -> str:
        nonlocal attempts
        await asyncio.sleep(0)
        attempts += 1
        msg = "still failing"
        raise LookupError(msg)

    with pytest.raises(LookupError, match="still failing"):
        await always_fails()

    assert attempts == 2


@pytest.mark.asyncio
async def test_validate_output_accepts_valid_result() -> None:
    @validate_output()
    async def build_payload() -> list[int]:
        await asyncio.sleep(0)
        return [1, 2, 3]

    result = await build_payload()

    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_validate_output_rejects_invalid_result() -> None:
    @validate_output()
    async def build_payload() -> list[int]:
        await asyncio.sleep(0)
        return ["bad"]  # type: ignore

    with pytest.raises(ValueError, match="Output validation failed"):
        await build_payload()


def test_validate_output_requires_return_annotation() -> None:
    with pytest.raises(TypeError, match="requires a return type annotation"):

        @validate_output()
        async def build_payload():
            await asyncio.sleep(0)
            return "missing annotation"
