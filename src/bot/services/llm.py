"""LLM orchestration: prompt building, tool loop, streaming."""

import json
import logging
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

from bot.domain.exceptions import LLMError
from bot.domain.models import Message, Role, ToolCall, ToolResult
from bot.infrastructure.openrouter import OpenRouterClient, StreamDelta
from bot.services.conversation import ConversationManager
from bot.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

_MAX_TOOL_ROUNDS = 10
_ASYNC_TOOL_PREFIX = "ASYNC_TOOL:"

# Type for async tool executors (channel tools)
AsyncToolExecutor = Callable[..., Coroutine[Any, Any, str]]


class LLMService:
    """Orchestrates LLM calls with tool execution and streaming."""

    def __init__(
        self,
        client: OpenRouterClient,
        conversations: ConversationManager,
        registry: ToolRegistry,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> None:
        self._client = client
        self._conversations = conversations
        self._registry = registry
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._async_executors: dict[str, AsyncToolExecutor] = {}

    def register_async_tool(self, name: str, executor: AsyncToolExecutor) -> None:
        """Register an async executor for tools that need await (e.g., channel tools)."""
        self._async_executors[name] = executor

    async def stream_response(self, user_id: int, user_text: str) -> AsyncIterator[str]:
        """Process a user message and yield streaming text chunks.

        Handles the full tool-calling loop:
        1. Send messages to LLM
        2. If tool calls → execute → add results → call LLM again
        3. If text → yield chunks
        """
        # Add user message to conversation
        self._conversations.add_message(
            user_id, Message(role=Role.USER, content=user_text)
        )

        model = self._conversations.get_model(user_id)
        tools_schema = self._registry.to_openrouter_schema() or None

        for _ in range(_MAX_TOOL_ROUNDS):
            messages = self._conversations.get_messages_for_api(user_id)
            text_parts: list[str] = []
            tool_calls: list[ToolCall] = []

            async for delta in self._client.stream_completion(
                messages=messages,
                model=model,
                tools=tools_schema,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            ):
                if delta.text:
                    text_parts.append(delta.text)
                    yield delta.text
                if delta.tool_calls:
                    tool_calls.extend(delta.tool_calls)

            # If we got text, save and done
            if text_parts:
                full_text = "".join(text_parts)
                self._conversations.add_message(
                    user_id, Message(role=Role.ASSISTANT, content=full_text)
                )
                return

            # If we got tool calls, execute and loop
            if tool_calls:
                await self._execute_tool_calls(user_id, tool_calls)
                continue

            # Neither text nor tools — unexpected
            logger.warning("LLM returned empty response for user %d", user_id)
            return

        logger.error("Max tool rounds (%d) exceeded for user %d", _MAX_TOOL_ROUNDS, user_id)
        yield "⚠️ Reached maximum tool call depth. Please try a simpler request."

    async def _execute_tool_calls(
        self, user_id: int, tool_calls: list[ToolCall]
    ) -> None:
        """Execute tool calls and add results to conversation."""
        # Add assistant message with tool_calls metadata
        self._conversations.add_message(
            user_id,
            Message(
                role=Role.ASSISTANT,
                content="",
                tool_calls=[
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": tc.arguments},
                    }
                    for tc in tool_calls
                ],
            ),
        )

        # Execute each tool
        for tc in tool_calls:
            result = await self._execute_single_tool(tc)
            self._conversations.add_message(
                user_id,
                Message(
                    role=Role.TOOL,
                    content=result.content,
                    tool_call_id=result.tool_call_id,
                ),
            )

    async def _execute_single_tool(self, tc: ToolCall) -> ToolResult:
        """Execute a single tool call, routing to sync or async executor."""
        try:
            args = json.loads(tc.arguments)
        except json.JSONDecodeError as e:
            return ToolResult(
                tool_call_id=tc.id,
                content=f"Error: invalid tool arguments: {e}",
                is_error=True,
            )

        logger.info("Executing tool: %s(%s)", tc.name, args)

        # Check for async tools (channel tools)
        sync_result = self._registry.execute(tc.name, args)
        if sync_result.startswith(_ASYNC_TOOL_PREFIX):
            executor = self._async_executors.get(tc.name)
            if executor:
                try:
                    content = await executor(**args)
                except Exception as e:
                    content = f"Error: {e}"
                    logger.exception("Async tool %s failed", tc.name)
                return ToolResult(tool_call_id=tc.id, content=content)
            return ToolResult(
                tool_call_id=tc.id,
                content=f"Error: async tool '{tc.name}' not available",
                is_error=True,
            )

        return ToolResult(tool_call_id=tc.id, content=sync_result)
