"""Tests for usage/token capture from OpenRouter SSE stream."""

import json
from unittest.mock import MagicMock

from bot.domain.models import StreamDelta, TokenUsage
from bot.infrastructure.openrouter.utils import parse_sse


def _make_sse_lines(chunks: list[dict]) -> list[str]:
    lines = []
    for chunk in chunks:
        lines.append(f"data: {json.dumps(chunk)}")
    lines.append("data: [DONE]")
    return lines


async def _async_iter(items):
    for item in items:
        yield item


def _text_chunk(text: str, finish: str | None = None) -> dict:
    choice: dict = {"delta": {"content": text}, "finish_reason": finish}
    return {"choices": [choice]}


def _usage_chunk(prompt: int, completion: int, total: int, cost: float | None = None) -> dict:
    """A final chunk with usage data and finish_reason=stop."""
    usage: dict = {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
    }
    if cost is not None:
        usage["cost"] = cost
    choice: dict = {"delta": {}, "finish_reason": "stop"}
    return {"choices": [choice], "usage": usage}


def _text_with_usage_chunk(text: str, prompt: int, completion: int, total: int) -> dict:
    """A chunk with both text content and usage in the same message."""
    usage = {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
    }
    choice: dict = {"delta": {"content": text}, "finish_reason": "stop"}
    return {"choices": [choice], "usage": usage}


class TestUsageCapture:
    async def test_usage_captured_from_final_chunk(self):
        lines = _make_sse_lines([
            _text_chunk("Hello"),
            _text_chunk(" world"),
            _usage_chunk(100, 200, 300),
        ])
        mock_response = MagicMock()
        mock_response.aiter_lines = MagicMock(return_value=_async_iter(lines))

        deltas: list[StreamDelta] = []
        async for delta in parse_sse(mock_response):
            deltas.append(delta)

        # The last delta should carry the usage
        usage_deltas = [d for d in deltas if d.usage is not None]
        assert len(usage_deltas) == 1
        usage = usage_deltas[0].usage
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 200
        assert usage.total_tokens == 300

    async def test_usage_with_cost(self):
        lines = _make_sse_lines([
            _text_chunk("Hi"),
            _usage_chunk(50, 80, 130, cost=0.0042),
        ])
        mock_response = MagicMock()
        mock_response.aiter_lines = MagicMock(return_value=_async_iter(lines))

        deltas = [d async for d in parse_sse(mock_response)]
        usage_deltas = [d for d in deltas if d.usage is not None]
        assert len(usage_deltas) == 1
        assert usage_deltas[0].usage.cost == 0.0042

    async def test_no_usage_when_not_provided(self):
        lines = _make_sse_lines([
            _text_chunk("Hello", "stop"),
        ])
        mock_response = MagicMock()
        mock_response.aiter_lines = MagicMock(return_value=_async_iter(lines))

        deltas = [d async for d in parse_sse(mock_response)]
        assert all(d.usage is None for d in deltas)

    async def test_usage_on_text_delta_when_same_chunk(self):
        lines = _make_sse_lines([
            _text_chunk("Start "),
            _text_with_usage_chunk("end", 60, 90, 150),
        ])
        mock_response = MagicMock()
        mock_response.aiter_lines = MagicMock(return_value=_async_iter(lines))

        deltas = [d async for d in parse_sse(mock_response)]
        usage_deltas = [d for d in deltas if d.usage is not None]
        assert len(usage_deltas) == 1
        assert usage_deltas[0].text == "end"
        assert usage_deltas[0].usage.total_tokens == 150

    async def test_usage_attached_to_tool_call_delta(self):
        """When tool calls are made, usage should still be captured."""
        tc_chunk = {
            "choices": [{
                "delta": {"tool_calls": [{"index": 0, "id": "call_1", "function": {"name": "web_search", "arguments": '{"q":"test"}'}}]},
                "finish_reason": None,
            }],
        }
        finish_chunk = {
            "choices": [{"delta": {}, "finish_reason": "tool_calls"}],
            "usage": {"prompt_tokens": 200, "completion_tokens": 50, "total_tokens": 250},
        }
        lines = _make_sse_lines([tc_chunk, finish_chunk])
        mock_response = MagicMock()
        mock_response.aiter_lines = MagicMock(return_value=_async_iter(lines))

        deltas = [d async for d in parse_sse(mock_response)]
        # Should have tool calls delta with usage
        assert any(d.tool_calls for d in deltas)
        usage_deltas = [d for d in deltas if d.usage is not None]
        assert len(usage_deltas) == 1
        assert usage_deltas[0].usage.prompt_tokens == 200
