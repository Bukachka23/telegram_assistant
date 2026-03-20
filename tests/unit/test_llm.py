"""Tests for LLM orchestration service."""

import json
from unittest.mock import MagicMock

import pytest

from bot.domain.models import ToolCall
from bot.infrastructure.openrouter import OpenRouterClient, StreamDelta
from bot.services.conversation import ConversationManager
from bot.services.llm import LLMService
from bot.tools.registry import ToolRegistry


@pytest.fixture
def registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(
        name="echo",
        description="Echo input",
        parameters={
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
        fn=lambda text: f"echoed: {text}",
    )
    return reg


@pytest.fixture
def conversations() -> ConversationManager:
    return ConversationManager(default_model="test-model")


@pytest.fixture
def mock_client() -> OpenRouterClient:
    client = MagicMock(spec=OpenRouterClient)
    return client


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
        yield item


class TestLLMService:
    @pytest.mark.asyncio
    async def test_simple_text_response(self, llm_service: LLMService, mock_client):
        mock_client.stream_completion = MagicMock(
            return_value=_async_iter([
                StreamDelta(text="Hello "),
                StreamDelta(text="world!"),
            ])
        )

        chunks = []
        async for chunk in llm_service.stream_response(1, "hi"):
            chunks.append(chunk)

        assert chunks == ["Hello ", "world!"]

    @pytest.mark.asyncio
    async def test_saves_messages_to_conversation(
        self, llm_service: LLMService, mock_client, conversations
    ):
        mock_client.stream_completion = MagicMock(
            return_value=_async_iter([StreamDelta(text="reply")])
        )

        async for _ in llm_service.stream_response(1, "hi"):
            pass

        msgs = conversations.get_messages_for_api(1)
        roles = [m["role"] for m in msgs]
        assert "user" in roles
        assert "assistant" in roles

    @pytest.mark.asyncio
    async def test_tool_call_then_text(
        self, llm_service: LLMService, mock_client
    ):
        # First call returns tool call, second returns text
        call_count = 0

        def make_stream(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _async_iter([
                    StreamDelta(
                        tool_calls=[
                            ToolCall(
                                id="call_1",
                                name="echo",
                                arguments=json.dumps({"text": "test"}),
                            )
                        ]
                    )
                ])
            return _async_iter([StreamDelta(text="Got: echoed: test")])

        mock_client.stream_completion = MagicMock(side_effect=make_stream)

        chunks = []
        async for chunk in llm_service.stream_response(1, "echo test"):
            chunks.append(chunk)

        assert chunks == ["Got: echoed: test"]
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_tool_execution(
        self, llm_service: LLMService, mock_client, registry
    ):
        # Register an async placeholder tool
        registry.register(
            name="async_tool",
            description="test",
            parameters={"type": "object", "properties": {}},
            fn=lambda **_: "ASYNC_TOOL:async_tool",
        )

        async def mock_executor(**kwargs):
            return "async result"

        llm_service.register_async_tool("async_tool", mock_executor)

        call_count = 0

        def make_stream(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _async_iter([
                    StreamDelta(
                        tool_calls=[
                            ToolCall(id="c1", name="async_tool", arguments="{}")
                        ]
                    )
                ])
            return _async_iter([StreamDelta(text="done")])

        mock_client.stream_completion = MagicMock(side_effect=make_stream)

        chunks = [c async for c in llm_service.stream_response(1, "do async")]
        assert chunks == ["done"]

    @pytest.mark.asyncio
    async def test_invalid_tool_arguments(
        self, llm_service: LLMService, mock_client, conversations
    ):
        call_count = 0

        def make_stream(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _async_iter([
                    StreamDelta(
                        tool_calls=[
                            ToolCall(id="c1", name="echo", arguments="not json{")
                        ]
                    )
                ])
            return _async_iter([StreamDelta(text="handled")])

        mock_client.stream_completion = MagicMock(side_effect=make_stream)

        chunks = [c async for c in llm_service.stream_response(1, "bad call")]
        assert chunks == ["handled"]

        # Tool error should be in conversation
        msgs = conversations.get_messages_for_api(1)
        tool_msgs = [m for m in msgs if m["role"] == "tool"]
        assert any("Error" in m["content"] for m in tool_msgs)
