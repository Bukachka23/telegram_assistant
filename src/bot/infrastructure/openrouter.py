"""Async OpenRouter API client with streaming and tool calling support."""

import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

import httpx

from bot.domain.exceptions import LLMError
from bot.domain.models import ToolCall

logger = logging.getLogger(__name__)

_BASE_URL = "https://openrouter.ai/api/v1"


@dataclass(frozen=True)
class StreamDelta:
    """A single chunk from a streaming response."""

    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str | None = None


class OpenRouterClient:
    """Async client for OpenRouter chat completions API."""

    def __init__(self, api_key: str, timeout: float = 120.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=_BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def stream_completion(
        self,
        messages: list[dict],
        model: str,
        *,
        tools: list[dict] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[StreamDelta]:
        """Stream chat completion, yielding deltas with text or tool calls."""
        payload: dict = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools

        try:
            async with self._client.stream(
                "POST", "/chat/completions", json=payload
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    raise LLMError(
                        f"OpenRouter {response.status_code}: {body.decode()}"
                    )
                async for delta in self._parse_sse(response):
                    yield delta
        except httpx.HTTPError as e:
            raise LLMError(f"OpenRouter request failed: {e}") from e

    async def _parse_sse(
        self, response: httpx.Response
    ) -> AsyncIterator[StreamDelta]:
        """Parse SSE stream into StreamDelta objects."""
        tool_calls_acc: dict[int, dict] = {}

        async for line in response.aiter_lines():
            if not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                # Yield accumulated tool calls if any
                if tool_calls_acc:
                    yield StreamDelta(
                        tool_calls=self._build_tool_calls(tool_calls_acc)
                    )
                return

            try:
                chunk = json.loads(data)
            except json.JSONDecodeError:
                continue

            choice = chunk.get("choices", [{}])[0]
            delta = choice.get("delta", {})
            finish = choice.get("finish_reason")

            # Text content
            text = delta.get("content") or ""

            # Tool call chunks (streamed incrementally)
            for tc in delta.get("tool_calls", []):
                idx = tc["index"]
                if idx not in tool_calls_acc:
                    tool_calls_acc[idx] = {
                        "id": tc.get("id", ""),
                        "name": tc.get("function", {}).get("name", ""),
                        "arguments": "",
                    }
                if tc.get("id"):
                    tool_calls_acc[idx]["id"] = tc["id"]
                fn = tc.get("function", {})
                if fn.get("name"):
                    tool_calls_acc[idx]["name"] = fn["name"]
                tool_calls_acc[idx]["arguments"] += fn.get("arguments", "")

            if text:
                yield StreamDelta(text=text, finish_reason=finish)
            elif finish and not tool_calls_acc:
                yield StreamDelta(finish_reason=finish)

    @staticmethod
    def _build_tool_calls(acc: dict[int, dict]) -> list[ToolCall]:
        """Convert accumulated tool call chunks into ToolCall objects."""
        return [
            ToolCall(
                id=tc["id"],
                name=tc["name"],
                arguments=tc["arguments"],
            )
            for tc in sorted(acc.values(), key=lambda x: x["id"])
        ]
