"""Tests for OpenRouter client."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.infrastructure.openrouter.openrouter import OpenRouterClient
from bot.infrastructure.openrouter.utils import parse_sse
from bot.domain.models import StreamDelta


def _make_sse_lines(chunks: list[dict]) -> list[str]:
    """Build SSE lines from chunk dicts."""
    lines = []
    for chunk in chunks:
        lines.append(f"data: {json.dumps(chunk)}")
    lines.append("data: [DONE]")
    return lines


def _text_chunk(text: str, finish: str | None = None) -> dict:
    """Build a text content chunk."""
    choice: dict = {"delta": {"content": text}, "finish_reason": finish}
    return {"choices": [choice]}


def _tool_chunk(index: int, call_id: str = "", name: str = "", args: str = "") -> dict:
    """Build a tool call chunk."""
    tc: dict = {"index": index, "function": {}}
    if call_id:
        tc["id"] = call_id
    if name:
        tc["function"]["name"] = name
    if args:
        tc["function"]["arguments"] = args
    choice: dict = {"delta": {"tool_calls": [tc]}, "finish_reason": None}
    return {"choices": [choice]}


class TestOpenRouterClient:
    @pytest.mark.asyncio
    async def test_stream_text_response(self):
        lines = _make_sse_lines([
            _text_chunk("Hello"),
            _text_chunk(" world"),
            _text_chunk("!", "stop"),
        ])

        client = OpenRouterClient(api_key="test-key")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = MagicMock(return_value=_async_iter(lines))

        deltas: list[StreamDelta] = []
        async for delta in parse_sse(mock_response):
            deltas.append(delta)

        assert len(deltas) == 3
        assert deltas[0].text == "Hello"
        assert deltas[1].text == " world"
        assert deltas[2].text == "!"

    @pytest.mark.asyncio
    async def test_stream_tool_calls(self):
        lines = _make_sse_lines([
            _tool_chunk(0, call_id="call_1", name="search_vault"),
            _tool_chunk(0, args='{"query":'),
            _tool_chunk(0, args='"test"}'),
        ])

        client = OpenRouterClient(api_key="test-key")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = MagicMock(return_value=_async_iter(lines))

        deltas: list[StreamDelta] = []
        async for delta in parse_sse(mock_response):
            deltas.append(delta)

        assert len(deltas) == 1  # Tool calls yielded at [DONE]
        assert len(deltas[0].tool_calls) == 1
        tc = deltas[0].tool_calls[0]
        assert tc.name == "search_vault"
        assert tc.arguments == '{"query":"test"}'

    @pytest.mark.asyncio
    async def test_empty_sse_lines_skipped(self):
        lines = ["", "keep-alive", "data: [DONE]"]

        client = OpenRouterClient(api_key="test-key")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = MagicMock(return_value=_async_iter(lines))

        deltas = [d async for d in parse_sse(mock_response)]
        assert deltas == []


async def _async_iter(items):
    for item in items:
        yield item
