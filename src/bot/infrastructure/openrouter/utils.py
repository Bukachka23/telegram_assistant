import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from bot.domain.exceptions import LLMError
from bot.domain.models import StreamDelta, TokenUsage, ToolCall


async def parse_sse(response: httpx.Response) -> AsyncIterator[StreamDelta]:
    """Parse SSE stream into StreamDelta objects."""
    tool_calls_acc: dict[int, dict] = {}
    last_usage: TokenUsage | None = None

    async for data in iter_sse_data(response):
        if data == "[DONE]":
            break

        chunk = parse_json_chunk(data)
        if not chunk:
            continue

        choice = chunk.get("choices", [{}])[0]
        delta = choice.get("delta", {})
        finish = choice.get("finish_reason")

        usage = _extract_usage(chunk)
        if usage is not None:
            last_usage = usage

        accumulate_tool_calls(delta.get("tool_calls", []), tool_calls_acc)

        text = delta.get("content") or ""
        if text:
            yield StreamDelta(text=text, finish_reason=finish, usage=usage)
        elif finish and not tool_calls_acc:
            yield StreamDelta(finish_reason=finish, usage=usage)

    # Yield accumulated tool calls if any after stream ends or [DONE] is received
    if tool_calls_acc:
        yield StreamDelta(tool_calls=build_tool_calls(tool_calls_acc), usage=last_usage)


def build_payload(messages: list[dict], model: str, tools: list[dict] | None, temperature: float, max_tokens: int) \
        -> dict[str, Any]:
    """Construct the JSON payload for the API request."""
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }
    if tools:
        payload["tools"] = tools
    return payload


async def check_response_status(response: httpx.Response) -> None:
    """Raise LLMError if the response status is not 200 OK."""
    if response.status_code != httpx.codes.OK:
        body = await response.aread()
        msg = f"OpenRouter {response.status_code}: {body.decode()}"
        raise LLMError(msg)


async def iter_sse_data(response: httpx.Response) -> AsyncIterator[str]:
    """Yield raw data payloads from Server-Sent Events lines."""
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            yield line[6:]


def parse_json_chunk(data: str) -> dict | None:
    """Parse JSON data, returning None if invalid."""
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None


def accumulate_tool_calls(tc_chunks: list[dict], acc: dict[int, dict]) -> None:
    """Update the tool calls accumulator in-place with new chunks."""
    for tc in tc_chunks:
        idx = tc["index"]
        if idx not in acc:
            acc[idx] = {
                "id": tc.get("id", ""),
                "name": tc.get("function", {}).get("name", ""),
                "arguments": "",
            }
        if tc.get("id"):
            acc[idx]["id"] = tc["id"]

        fn = tc.get("function", {})
        if fn.get("name"):
            acc[idx]["name"] = fn["name"]
        acc[idx]["arguments"] += fn.get("arguments", "")


def build_tool_calls(acc: dict[int, dict]) -> list[ToolCall]:
    """Convert accumulated tool call chunks into ToolCall objects in provider order."""
    return [
        ToolCall(
            id=tc["id"],
            name=tc["name"],
            arguments=tc["arguments"],
        )
        for _, tc in sorted(acc.items())
    ]


def _extract_usage(chunk: dict) -> TokenUsage | None:
    """Extract token usage from a chunk if present."""
    usage = chunk.get("usage")
    if not usage:
        return None
    return TokenUsage(
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
        cost=usage.get("cost"),
    )
