import functools
import inspect
from collections.abc import Awaitable, Callable

from pydantic import TypeAdapter, ValidationError

from bot.shared.constants import P, R


def validate_output() -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Validate an async function return value against its type annotation."""

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        signature = inspect.signature(func)
        return_annotation = signature.return_annotation

        if return_annotation is inspect.Signature.empty:
            msg = f"Function {func.__name__} requires a return type annotation"
            raise TypeError(msg)

        adapter = TypeAdapter(return_annotation)

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            raw_result = await func(*args, **kwargs)
            try:
                return adapter.validate_python(raw_result)
            except ValidationError as error:
                msg = f"Output validation failed for {func.__name__}"
                raise ValueError(msg) from error

        return wrapper

    return decorator
