import asyncio
import functools
from collections.abc import Awaitable, Callable

from bot.config.constants import P, R


def enforce_timeout(
    timeout_seconds: float,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Cancel an async function if it exceeds the configured timeout."""
    if timeout_seconds <= 0:
        msg = "timeout_seconds must be greater than 0"
        raise ValueError(msg)

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds,
                )
            except TimeoutError as error:
                func_name = getattr(func, "__name__", repr(func))
                msg = (
                    f"Function {func_name} timed out "
                    f"after {timeout_seconds}s"
                )
                raise TimeoutError(msg) from error

        return wrapper

    return decorator
