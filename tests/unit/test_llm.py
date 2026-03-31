"""Tests for LLM orchestration service."""

import asyncio
import json
from unittest.mock import MagicMock

import pytest

from bot.domain.models import ToolCall
from bot.infrastructure.open_router.openrouter import OpenRouterClient, StreamDelta
from bot.services.conversation import ConversationManager
from bot.services.llm import LLMService
from bot.shared.agents.registry import get_agent, get_default_agent
from bot.tools.registry import ToolRegistry


@pytest.fixture
def registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(
        name="search_vault",
        description="Search notes",
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        fn=lambda query: f"found: {query}",
    )
    reg.register(
        name="fetch_messages",
        description="Fetch channel messages",
        parameters={
            "type": "object",
            "properties": {"channel": {"type": "string"}},
            "required": ["channel"],
        },
        fn=lambda **_: "ASYNC_TOOL:fetch_messages",
    )
    reg.register(
        name="custom_tool",
        description="Not allowed for built-in agents",
        parameters={"type": "object", "properties": {}},
        fn=lambda: "custom",
    )
    return reg


@pytest.fixture
def conversations() -> ConversationManager:
    return ConversationManager(default_model="test-model")


@pytest.fixture
def mock_client() -> OpenRouterClient:
    return MagicMock(spec=OpenRouterClient)


@pytest.fixture
def llm_service(
    mock_client: OpenRouterClient,
    conversations: ConversationManager,
    registry: ToolRegistry,
) -> LLMService:
    return LLMService(
        client=mock_client,
        conversations=conversations,
        registry=registry,
    )


async def _async_iter(items):
    for item in items:
        await asyncio.sleep(0)
        yield item


@pytest.mark.asyncio
async def test_simple_text_response_uses_default_agent_config(
    llm_service: LLMService,
    mock_client: OpenRouterClient,
) -> None:
    mock_client.stream_completion = MagicMock(
        return_value=_async_iter([
            StreamDelta(text="Hello "),
            StreamDelta(text="world!"),
        ])
    )

    chunks = [chunk async for chunk in llm_service.stream_response(1, "hi")]

    assert chunks == ["Hello ", "world!"]
    _, kwargs = mock_client.stream_completion.call_args
    tool_names = {tool["function"]["name"] for tool in kwargs["tools"]}
    assert kwargs["temperature"] == get_default_agent().temperature
    assert kwargs["max_tokens"] == get_default_agent().max_tokens
    assert kwargs["messages"][0]["content"] == get_default_agent().prompt
    assert tool_names == {"search_vault", "fetch_messages"}


@pytest.mark.asyncio
async def test_switched_agent_uses_own_prompt_settings_and_tool_filter(
    llm_service: LLMService,
    mock_client: OpenRouterClient,
    conversations: ConversationManager,
) -> None:
    conversations.set_active_agent(1, "math_tutor")
    mock_client.stream_completion = MagicMock(
        return_value=_async_iter([StreamDelta(text="step-by-step")])
    )

    chunks = [chunk async for chunk in llm_service.stream_response(1, "solve this")]

    assert chunks == ["step-by-step"]
    _, kwargs = mock_client.stream_completion.call_args
    math_tutor = get_agent("math_tutor")
    assert math_tutor is not None
    assert kwargs["temperature"] == math_tutor.temperature
    assert kwargs["max_tokens"] == math_tutor.max_tokens
    assert kwargs["messages"][0]["content"] == math_tutor.prompt
    assert kwargs["tools"] is None


@pytest.mark.asyncio
async def test_unknown_active_agent_falls_back_to_default_config(
    llm_service: LLMService,
    mock_client: OpenRouterClient,
    conversations: ConversationManager,
) -> None:
    conversations.set_active_agent(1, "missing")
    mock_client.stream_completion = MagicMock(
        return_value=_async_iter([StreamDelta(text="fallback")])
    )

    chunks = [chunk async for chunk in llm_service.stream_response(1, "hi")]

    assert chunks == ["fallback"]
    _, kwargs = mock_client.stream_completion.call_args
    assert kwargs["temperature"] == get_default_agent().temperature
    assert kwargs["max_tokens"] == get_default_agent().max_tokens
    assert kwargs["messages"][0]["content"] == get_default_agent().prompt


@pytest.mark.asyncio
async def test_tool_call_then_text(
    llm_service: LLMService,
    mock_client: OpenRouterClient,
) -> None:
    call_count = 0

    def make_stream(*args, **kwargs):
        del args, kwargs
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _async_iter([
                StreamDelta(
                    tool_calls=[
                        ToolCall(
                            id="call_1",
                            name="search_vault",
                            arguments=json.dumps({"query": "test"}),
                        )
                    ]
                )
            ])
        return _async_iter([StreamDelta(text="Got: found: test")])

    mock_client.stream_completion = MagicMock(side_effect=make_stream)

    chunks = [chunk async for chunk in llm_service.stream_response(1, "find test")]

    assert chunks == ["Got: found: test"]
    assert call_count == 2


@pytest.mark.asyncio
async def test_async_tool_execution(
    llm_service: LLMService,
    mock_client: OpenRouterClient,
) -> None:
    async def mock_executor(**kwargs) -> str:
        del kwargs
        await asyncio.sleep(0)
        return "async result"

    llm_service.register_async_tool("fetch_messages", mock_executor)

    call_count = 0

    def make_stream(*args, **kwargs):
        del args, kwargs
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _async_iter([
                StreamDelta(
                    tool_calls=[
                        ToolCall(
                            id="c1",
                            name="fetch_messages",
                            arguments=json.dumps({"channel": "@test"}),
                        )
                    ]
                )
            ])
        return _async_iter([StreamDelta(text="done")])

    mock_client.stream_completion = MagicMock(side_effect=make_stream)

    chunks = [chunk async for chunk in llm_service.stream_response(1, "do async")]

    assert chunks == ["done"]


@pytest.mark.asyncio
async def test_invalid_tool_arguments_are_recorded_as_tool_error(
    llm_service: LLMService,
    mock_client: OpenRouterClient,
    conversations: ConversationManager,
) -> None:
    call_count = 0

    def make_stream(*args, **kwargs):
        del args, kwargs
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _async_iter([
                StreamDelta(
                    tool_calls=[
                        ToolCall(
                            id="c1",
                            name="search_vault",
                            arguments="not json{",
                        )
                    ]
                )
            ])
        return _async_iter([StreamDelta(text="handled")])

    mock_client.stream_completion = MagicMock(side_effect=make_stream)

    chunks = [chunk async for chunk in llm_service.stream_response(1, "bad call")]

    assert chunks == ["handled"]
    messages = conversations.get_messages_for_api(1)
    tool_messages = [message for message in messages if message["role"] == "tool"]
    assert any("Error" in message["content"] for message in tool_messages)


@pytest.mark.asyncio
async def test_disallowed_tool_call_is_rejected_for_active_agent(
    llm_service: LLMService,
    mock_client: OpenRouterClient,
    conversations: ConversationManager,
) -> None:
    conversations.set_active_agent(1, "math_tutor")
    call_count = 0

    def make_stream(*args, **kwargs):
        del args, kwargs
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _async_iter([
                StreamDelta(
                    tool_calls=[
                        ToolCall(
                            id="c1",
                            name="search_vault",
                            arguments=json.dumps({"query": "integrals"}),
                        )
                    ]
                )
            ])
        return _async_iter([StreamDelta(text="handled")])

    mock_client.stream_completion = MagicMock(side_effect=make_stream)

    chunks = [chunk async for chunk in llm_service.stream_response(1, "use tool")]

    assert chunks == ["handled"]
    messages = conversations.get_messages_for_api(1)
    tool_messages = [message for message in messages if message["role"] == "tool"]
    assert any("not available for the active agent" in message["content"] for message in tool_messages)
