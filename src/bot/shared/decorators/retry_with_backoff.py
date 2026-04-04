import asyncio
import functools
from collections.abc import Awaitable, Callable
from typing import cast

from bot.config.constants import BACKOFF_MULTIPLIER, BASE_DELAY_SECONDS, MAX_ATTEMPTS, P, R


async def _call_once(
    func: Callable[P, Awaitable[R]],
    handled_exceptions: tuple[type[Exception], ...],
    *args: P.args,
    **kwargs: P.kwargs,
) -> tuple[bool, R | None, Exception | None]:
    """Execute a function once and capture only retryable exceptions."""
    try:
        return True, await func(*args, **kwargs), None
    except handled_exceptions as error:
        return False, None, error


def retry_with_backoff(
    max_attempts: int = MAX_ATTEMPTS,
    base_delay_seconds: float = BASE_DELAY_SECONDS,
    backoff_multiplier: float = BACKOFF_MULTIPLIER,
    handled_exceptions: tuple[type[Exception], ...] = (TimeoutError,),
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Retry an async function with exponential backoff for handled exceptions."""
    if max_attempts < 1:
        msg = "max_attempts must be at least 1"
        raise ValueError(msg)
    if base_delay_seconds <= 0:
        msg = "base_delay_seconds must be greater than 0"
        raise ValueError(msg)
    if backoff_multiplier < 1:
        msg = "backoff_multiplier must be at least 1"
        raise ValueError(msg)
    if not handled_exceptions:
        msg = "handled_exceptions must contain at least one exception type"
        raise ValueError(msg)

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            delay = base_delay_seconds
            last_error: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                succeeded, result, error = await _call_once(
                    func,
                    handled_exceptions,
                    *args,
                    **kwargs,
                )
                if succeeded:
                    return cast("R", result)

                last_error = error
                if attempt == max_attempts:
                    if last_error is None:
                        msg = "retry loop ended without a captured exception"
                        raise RuntimeError(msg)
                    raise last_error

                await asyncio.sleep(delay)
                delay *= backoff_multiplier

            msg = "unreachable retry state"
            raise RuntimeError(msg)

        return wrapper

    return decorator
