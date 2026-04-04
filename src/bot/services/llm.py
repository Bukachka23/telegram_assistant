import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from bot.config.constants import ASYNC_TOOL_PREFIX, MAX_TOKENS, MAX_TOOL_ROUNDS, TEMPERATURE
from bot.domain.models import AgentProfile, Message, Role, TokenUsage, ToolCall, ToolResult
from bot.domain.models.metrics import RequestMetric
from bot.infrastructure.openrouter.openrouter import OpenRouterClient
from bot.services.conversation import ConversationManager
from bot.shared.agents.registry import get_agent, get_default_agent
from bot.tools.registry import ToolRegistry

if TYPE_CHECKING:
    from bot.infrastructure.storage.metrics_storage import MetricsStore

logger = logging.getLogger(__name__)

AsyncToolExecutor = Callable[..., Awaitable[str]]


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
            tz_offset_hours: int = 0,
            metrics_store: "MetricsStore | None" = None,
    ) -> None:
        self._client = client
        self._conversations = conversations
        self._registry = registry
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._tz = timezone(timedelta(hours=tz_offset_hours))
        self._async_executors: dict[str, AsyncToolExecutor] = {}
        self._filtered_schema_cache: dict[tuple[str, ...], list[dict]] = {}
        self._metrics_store = metrics_store

    def register_async_tool(self, name: str, executor: AsyncToolExecutor) -> None:
        """Register an async executor for tools that need await."""
        self._async_executors[name] = executor

    async def stream_response(self, user_id: int, user_text: str) -> AsyncIterator[str]:
        """Process a user message and yield streaming text chunks."""
        self._record_user_message(user_id, user_text)

        agent = self._get_agent_profile(user_id)
        model = self._conversations.get_model(user_id)
        tools_schema = self._filter_tools_schema(agent.allowed_tools)
        system_prompt = self._build_system_prompt(agent.prompt)

        t_start = time.monotonic()
        t_first_token: float | None = None
        last_usage: TokenUsage | None = None
        tool_names_collected: list[str] = []
        error_text = ""

        for _ in range(MAX_TOOL_ROUNDS):
            messages = self._conversations.get_messages_for_api(
                user_id, system_prompt=system_prompt
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
                    if t_first_token is None:
                        t_first_token = time.monotonic()
                    text_parts.append(delta.text)
                    yield delta.text
                if delta.tool_calls:
                    tool_calls.extend(delta.tool_calls)
                if delta.usage:
                    last_usage = delta.usage

            if tool_calls:
                tool_names_collected.extend(tc.name for tc in tool_calls)

            should_continue = await self._process_stream_results(
                user_id, text_parts, tool_calls, agent.allowed_tools
            )
            if not should_continue:
                await self._emit_metric(
                    model=model, t_start=t_start, t_first_token=t_first_token,
                    usage=last_usage, tool_names=tool_names_collected, error_text=error_text,
                )
                return

        error_text = "max tool rounds exceeded"
        await self._emit_metric(
            model=model, t_start=t_start, t_first_token=t_first_token,
            usage=last_usage, tool_names=tool_names_collected, error_text=error_text,
        )
        logger.error("Max tool rounds (%d) exceeded for user %d", MAX_TOOL_ROUNDS, user_id)
        yield "⚠️ Reached maximum tool call depth. Please try a simpler request."

    async def complete_side_context(
            self,
            *,
            messages: list[dict[str, Any]],
            model: str,
            allowed_tools: list[str] | None = None,
            temperature: float | None = None,
            max_tokens: int | None = None,
    ) -> str:
        """Run the same tool loop against an isolated message context."""
        tools_schema = self._filter_tools_schema(allowed_tools)
        effective_temp = temperature if temperature is not None else self._temperature
        effective_tokens = max_tokens if max_tokens is not None else self._max_tokens
        working_messages = [dict(msg) for msg in messages]

        for _ in range(MAX_TOOL_ROUNDS):
            text, tool_calls = await self._fetch_completion(
                working_messages, model, tools_schema, effective_temp, effective_tokens
            )

            if text:
                working_messages.append({"role": Role.ASSISTANT.value, "content": text})
                return text

            if not tool_calls:
                logger.warning("LLM returned empty side-context response")
                return ""

            await self._apply_tools_to_context(working_messages, tool_calls, allowed_tools)

        logger.error("Max tool rounds (%d) exceeded for side-context completion", MAX_TOOL_ROUNDS)
        return "⚠️ Reached maximum tool call depth. Please try a narrower research request."

    async def _process_stream_results(
            self, user_id: int, text_parts: list[str], tool_calls: list[ToolCall], allowed_tools: list[str]
    ) -> bool:
        """Evaluate the results of a streaming round."""
        if text_parts:
            self._record_assistant_text(user_id, "".join(text_parts))
            return False

        if tool_calls:
            await self._execute_tool_calls(user_id, tool_calls, allowed_tools=allowed_tools)
            return True

        logger.warning("LLM returned empty response for user %d", user_id)
        return False

    async def _fetch_completion(
            self, messages: list[dict[str, Any]], model: str, tools: list[dict] | None, temp: float, tokens: int
    ) -> tuple[str, list[ToolCall]]:
        """Fetch a complete response from the LLM, aggregating text and tool calls."""
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []

        async for delta in self._client.stream_completion(
                messages=messages, model=model, tools=tools, temperature=temp, max_tokens=tokens
        ):
            if delta.text:
                text_parts.append(delta.text)
            if delta.tool_calls:
                tool_calls.extend(delta.tool_calls)

        return "".join(text_parts), tool_calls

    async def _apply_tools_to_context(
            self, messages: list[dict[str, Any]], tool_calls: list[ToolCall], allowed_tools: list[str] | None
    ) -> None:
        """Execute tools and append both the calls and results to the isolated message context."""
        messages.append(
            {
                "role": Role.ASSISTANT.value,
                "content": "",
                "tool_calls": self._format_tool_calls(tool_calls),
            }
        )
        results = await asyncio.gather(
            *[self._execute_single_tool(tc, allowed_tools=allowed_tools) for tc in tool_calls]
        )
        messages.extend(
                {
                    "role": Role.TOOL.value,
                    "content": result.content,
                    "tool_call_id": result.tool_call_id,
                }
                for result in results
            )

    async def _execute_tool_calls(self, user_id: int, tool_calls: list[ToolCall], *, allowed_tools: list[str]) -> None:
        self._record_tool_calls_intent(user_id, tool_calls)
        results = await asyncio.gather(
            *[self._execute_single_tool(tc, allowed_tools=allowed_tools) for tc in tool_calls]
        )
        for result in results:
            self._record_tool_result(user_id, result)

    async def _execute_single_tool(self, tool_call: ToolCall, *, allowed_tools: list[str] | None = None) -> ToolResult:
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

    def _build_system_prompt(self, base_prompt: str) -> str:
        """Prepend the current local datetime so the LLM can schedule correctly."""
        now = datetime.now(self._tz)
        offset_h = int(self._tz.utcoffset(now).total_seconds() // 3600)  # type: ignore[union-attr]
        time_line = f"Current date and time: {now.strftime('%A, %Y-%m-%d %H:%M')} (UTC{offset_h:+d})"
        return f"{time_line}\n\n{base_prompt}"

    def _get_agent_profile(self, user_id: int) -> AgentProfile:
        agent_name = self._conversations.get_active_agent(user_id)
        return get_agent(agent_name) or get_default_agent()

    def _filter_tools_schema(self, allowed_tools: list[str] | None) -> list[dict] | None:
        if not allowed_tools:
            return None
        cache_key = tuple(sorted(allowed_tools))
        cached = self._filtered_schema_cache.get(cache_key)
        if cached is not None:
            return cached
        filtered = [
            tool for tool in self._registry.to_openrouter_schema()
            if tool["function"]["name"] in allowed_tools
        ]
        self._filtered_schema_cache[cache_key] = filtered
        return filtered

    def _record_user_message(self, user_id: int, text: str) -> None:
        self._conversations.add_message(user_id, Message(role=Role.USER, content=text))

    def _record_assistant_text(self, user_id: int, text: str) -> None:
        self._conversations.add_message(user_id, Message(role=Role.ASSISTANT, content=text))

    def _record_tool_calls_intent(self, user_id: int, tool_calls: list[ToolCall]) -> None:
        self._conversations.add_message(
            user_id, Message(role=Role.ASSISTANT, content="", tool_calls=self._format_tool_calls(tool_calls))
        )

    @staticmethod
    def _format_tool_calls(tool_calls: list[ToolCall]) -> list[dict[str, Any]]:
        return [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.name, "arguments": tc.arguments},
            }
            for tc in tool_calls
        ]

    async def _emit_metric(
        self,
        *,
        model: str,
        t_start: float,
        t_first_token: float | None,
        usage: TokenUsage | None,
        tool_names: list[str],
        error_text: str,
    ) -> None:
        """Record a request metric. Fire-and-forget — never breaks a response."""
        if self._metrics_store is None:
            return
        try:
            t_end = time.monotonic()
            metric = RequestMetric(
                model=model,
                tokens_in=usage.prompt_tokens if usage else 0,
                tokens_out=usage.completion_tokens if usage else 0,
                cost_usd=usage.cost if usage else None,
                latency_ms=int((t_end - t_start) * 1000),
                ttfb_ms=int((t_first_token - t_start) * 1000) if t_first_token else 0,
                tool_names=",".join(tool_names),
                is_error=bool(error_text),
                error_text=error_text,
            )
            await self._metrics_store.record(metric)
        except Exception:
            logger.warning("Failed to emit request metric", exc_info=True)

    def _record_tool_result(self, user_id: int, result: ToolResult) -> None:
        self._conversations.add_message(
            user_id, Message(role=Role.TOOL, content=result.content, tool_call_id=result.tool_call_id)
        )
