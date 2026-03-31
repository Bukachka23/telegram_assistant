import functools
from collections.abc import Awaitable, Callable, Sequence

from bot.shared.constants import P, R


async def _try_call(
    func: Callable[P, Awaitable[R]],
    handled_exceptions: tuple[type[Exception], ...],
    *args: P.args,
    **kwargs: P.kwargs,
) -> tuple[bool, R | None, Exception | None]:
    """Execute a function and capture only handled exceptions."""
    try:
        return True, await func(*args, **kwargs), None
    except handled_exceptions as error:
        return False, None, error


def chain_fallbacks(
    fallback_functions: Sequence[Callable[P, Awaitable[R]]],
    handled_exceptions: tuple[type[Exception], ...],
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Try fallback async callables sequentially when handled exceptions occur."""
    if not fallback_functions:
        msg = "fallback_functions must contain at least one callable"
        raise ValueError(msg)
    if not handled_exceptions:
        msg = "handled_exceptions must contain at least one exception type"
        raise ValueError(msg)

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            succeeded, result, error = await _try_call(
                func,
                handled_exceptions,
                *args,
                **kwargs,
            )
            if succeeded:
                return result

            last_error = error
            for fallback in fallback_functions:
                succeeded, result, error = await _try_call(
                    fallback,
                    handled_exceptions,
                    *args,
                    **kwargs,
                )
                if succeeded:
                    return result
                last_error = error

            if last_error is None:
                msg = "fallback chain ended without a captured exception"
                raise RuntimeError(msg)
            raise last_error

        return wrapper

    return decorator
