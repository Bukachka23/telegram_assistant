import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from bot.config.constants import ASYNC_TOOL_PREFIX
from bot.domain.models import ToolCall, ToolResult
from bot.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

AsyncToolExecutor = Callable[..., Awaitable[str]]


class ToolExecutionService:
    """Executes sync and async LLM tool calls."""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry
        self._async_executors: dict[str, AsyncToolExecutor] = {}

    def register_async_tool(self, name: str, executor: AsyncToolExecutor) -> None:
        """Register an async executor for tools that need await."""
        self._async_executors[name] = executor

    async def execute_tools_in_order(
        self,
        tool_calls: tuple[ToolCall, ...],
        *,
        allowed_tools: list[str] | None,
    ) -> list[ToolResult]:
        """Execute tool calls concurrently while preserving the original call order."""
        logger.debug(
            "Executing tool calls in original order: %s",
            [(index, tc.id, tc.name) for index, tc in enumerate(tool_calls, start=1)],
        )
        return await asyncio.gather(
            *[
                self._execute_single_tool(tc, allowed_tools=allowed_tools)
                for tc in tool_calls
            ]
        )

    @staticmethod
    def format_tool_calls(tool_calls: list[ToolCall]) -> list[dict[str, Any]]:
        return [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.name, "arguments": tc.arguments},
            }
            for tc in tool_calls
        ]

    async def _execute_single_tool(
        self,
        tool_call: ToolCall,
        *,
        allowed_tools: list[str] | None = None,
    ) -> ToolResult:
        if allowed_tools is not None and tool_call.name not in allowed_tools:
            content = f"Error: tool '{tool_call.name}' is not available for the active agent"
            return ToolResult(tool_call_id=tool_call.id, content=content, is_error=True)

        try:
            args = self._parse_arguments(tool_call)
        except ValueError as error:
            return ToolResult(tool_call_id=tool_call.id, content=f"Error: {error}", is_error=True)

        logger.info("Executing tool: %s(%s)", tool_call.name, args)

        sync_result = self._registry.execute(tool_call.name, args)
        if sync_result.startswith(ASYNC_TOOL_PREFIX):
            return await self._execute_async_tool(tool_call, args)

        return ToolResult(tool_call_id=tool_call.id, content=sync_result)

    @staticmethod
    def _parse_arguments(tool_call: ToolCall) -> dict[str, Any]:
        try:
            return json.loads(tool_call.arguments)
        except json.JSONDecodeError as error:
            msg = f"invalid tool arguments: {error}"
            raise ValueError(msg) from error

    async def _execute_async_tool(self, tool_call: ToolCall, args: dict[str, Any]) -> ToolResult:
        executor = self._async_executors.get(tool_call.name)
        if not executor:
            return ToolResult(
                tool_call_id=tool_call.id,
                content=f"Error: async tool '{tool_call.name}' not available",
                is_error=True,
            )

        try:
            content = await executor(**args)
            return ToolResult(tool_call_id=tool_call.id, content=content)
        except Exception as error:
            logger.exception("Async tool %s failed", tool_call.name)
            return ToolResult(
                tool_call_id=tool_call.id,
                content=(
                    f"Tool '{tool_call.name}' failed: {error}. "
                    "Answer the user's question using your own knowledge. "
                    "Mention that real-time search was unavailable."
                ),
                is_error=True,
            )
