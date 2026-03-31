import json
import logging
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

from bot.domain.models import AgentProfile, Message, Role, ToolCall, ToolResult
from bot.infrastructure.open_router.openrouter import OpenRouterClient
from bot.services.conversation import ConversationManager
from bot.shared.agents.registry import get_agent, get_default_agent
from bot.shared.constants import ASYNC_TOOL_PREFIX, MAX_TOKENS, MAX_TOOL_ROUNDS, TEMPERATURE
from bot.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

AsyncToolExecutor = Callable[..., Coroutine[Any, Any, str]]


class LLMService:
    """Orchestrates LLM calls with tool execution and streaming."""

    def __init__(
        self,
        client: OpenRouterClient,
        conversations: ConversationManager,
        registry: ToolRegistry,
        *,
        max_tokens: int = MAX_TOKENS,
        temperature: float = TEMPERATURE,
    ) -> None:
        self._client = client
        self._conversations = conversations
        self._registry = registry
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._async_executors: dict[str, AsyncToolExecutor] = {}

    def register_async_tool(self, name: str, executor: AsyncToolExecutor) -> None:
        """Register an async executor for tools that need await."""
        self._async_executors[name] = executor

    async def stream_response(self, user_id: int, user_text: str) -> AsyncIterator[str]:
        """Process a user message and yield streaming text chunks."""
        self._record_user_message(user_id, user_text)

        agent = self._get_agent_profile(user_id)
        model = self._conversations.get_model(user_id)
        tools_schema = self._filter_tools_schema(agent.allowed_tools)

        for _ in range(MAX_TOOL_ROUNDS):
            messages = self._conversations.get_messages_for_api(
                user_id,
                system_prompt=agent.prompt,
            )
            text_parts: list[str] = []
            tool_calls: list[ToolCall] = []

            async for delta in self._client.stream_completion(
                messages=messages,
                model=model,
                tools=tools_schema,
                temperature=agent.temperature,
                max_tokens=agent.max_tokens,
            ):
                if delta.text:
                    text_parts.append(delta.text)
                    yield delta.text
                if delta.tool_calls:
                    tool_calls.extend(delta.tool_calls)

            if text_parts:
                self._record_assistant_text(user_id, "".join(text_parts))
                return

            if tool_calls:
                await self._execute_tool_calls(user_id, tool_calls, allowed_tools=agent.allowed_tools)
                continue

            logger.warning("LLM returned empty response for user %d", user_id)
            return

        logger.error(
            "Max tool rounds (%d) exceeded for user %d",
            MAX_TOOL_ROUNDS,
            user_id,
        )
        yield "⚠️ Reached maximum tool call depth. Please try a simpler request."

    async def _execute_tool_calls(self, user_id: int, tool_calls: list[ToolCall], *, allowed_tools: list[str]) -> None:
        """Execute tool calls and add results to conversation."""
        self._record_tool_calls_intent(user_id, tool_calls)

        for tool_call in tool_calls:
            result = await self._execute_single_tool(tool_call, allowed_tools=allowed_tools)
            self._record_tool_result(user_id, result)

    async def _execute_single_tool(self, tool_call: ToolCall, *, allowed_tools: list[str] | None = None) -> ToolResult:
        """Execute a single tool call, routing to sync or async executor."""
        if allowed_tools is not None and tool_call.name not in allowed_tools:
            content = f"Error: tool '{tool_call.name}' is not available for the active agent"
            return ToolResult(tool_call_id=tool_call.id, content=content, is_error=True)

        try:
            args = self._parse_arguments(tool_call)
        except ValueError as error:
            return ToolResult(
                tool_call_id=tool_call.id,
                content=f"Error: {error}",
                is_error=True,
            )

        logger.info("Executing tool: %s(%s)", tool_call.name, args)

        sync_result = self._registry.execute(tool_call.name, args)
        if sync_result.startswith(ASYNC_TOOL_PREFIX):
            return await self._execute_async_tool(tool_call, args)

        return ToolResult(tool_call_id=tool_call.id, content=sync_result)

    @staticmethod
    def _parse_arguments(tool_call: ToolCall) -> dict[str, Any]:
        """Parse tool arguments, raising ValueError if invalid."""
        try:
            return json.loads(tool_call.arguments)
        except json.JSONDecodeError as error:
            msg = f"invalid tool arguments: {error}"
            raise ValueError(msg) from error

    async def _execute_async_tool(self, tool_call: ToolCall, args: dict[str, Any]) -> ToolResult:
        """Execute an async tool and handle potential errors."""
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

    def _get_agent_profile(self, user_id: int) -> AgentProfile:
        """Return the active agent profile for a user's session."""
        agent_name = self._conversations.get_active_agent(user_id)
        return get_agent(agent_name) or get_default_agent()

    def _filter_tools_schema(self, allowed_tools: list[str]) -> list[dict] | None:
        """Return only the tools allowed for the active agent."""
        if not allowed_tools:
            return None
        return [
            tool
            for tool in self._registry.to_openrouter_schema()
            if tool["function"]["name"] in allowed_tools
        ]

    def _record_user_message(self, user_id: int, text: str) -> None:
        self._conversations.add_message(
            user_id,
            Message(role=Role.USER, content=text),
        )

    def _record_assistant_text(self, user_id: int, text: str) -> None:
        self._conversations.add_message(user_id, Message(role=Role.ASSISTANT, content=text))

    def _record_tool_calls_intent(self, user_id: int, tool_calls: list[ToolCall]) -> None:
        formatted_calls = [
            {
                "id": tool_call.id,
                "type": "function",
                "function": {
                    "name": tool_call.name,
                    "arguments": tool_call.arguments,
                },
            }
            for tool_call in tool_calls
        ]
        self._conversations.add_message(
            user_id,
            Message(role=Role.ASSISTANT, content="", tool_calls=formatted_calls),
        )

    def _record_tool_result(self, user_id: int, result: ToolResult) -> None:
        self._conversations.add_message(
            user_id,
            Message(
                role=Role.TOOL,
                content=result.content,
                tool_call_id=result.tool_call_id,
            ),
        )
