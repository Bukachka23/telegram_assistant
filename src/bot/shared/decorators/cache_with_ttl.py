import functools
import time
from collections.abc import Awaitable, Callable, Hashable

from bot.shared.constants import P, R

CacheKey = tuple[tuple[Hashable, ...], tuple[tuple[str, Hashable], ...]]


def _freeze_value(value: object) -> Hashable:
    """Convert common Python values into a stable hashable representation."""
    if isinstance(value, Hashable):
        return value
    if isinstance(value, dict):
        return tuple(sorted((str(key), _freeze_value(item)) for key, item in value.items()))
    if isinstance(value, list | tuple):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, set):
        return tuple(sorted(_freeze_value(item) for item in value))
    return repr(value)


def _make_cache_key(args: tuple[object, ...], kwargs: dict[str, object]) -> CacheKey:
    """Build a deterministic cache key from args and kwargs."""
    frozen_args = tuple(_freeze_value(arg) for arg in args)
    frozen_kwargs = tuple(sorted((key, _freeze_value(value)) for key, value in kwargs.items()))
    return frozen_args, frozen_kwargs


def cache_with_ttl(ttl_seconds: float) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Cache async function results for a limited time based on call arguments."""
    if ttl_seconds <= 0:
        msg = "ttl_seconds must be greater than 0"
        raise ValueError(msg)

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        cache_store: dict[CacheKey, tuple[float, R]] = {}

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            cache_key = _make_cache_key(args, kwargs)
            current_time = time.monotonic()
            cached_entry = cache_store.get(cache_key)

            if cached_entry is not None:
                timestamp, cached_value = cached_entry
                if current_time - timestamp < ttl_seconds:
                    return cached_value
                del cache_store[cache_key]

            result = await func(*args, **kwargs)
            cache_store[cache_key] = (current_time, result)
            return result

        return wrapper

    return decorator
