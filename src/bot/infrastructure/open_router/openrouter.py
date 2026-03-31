import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from bot.domain.exceptions import LLMError
from bot.domain.models import ToolCall
from bot.shared.base import StreamDelta
from bot.shared.constants import BASE_URL, OPENROUTER_MAX_TOKENS

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Async client for OpenRouter chat completions API."""

    def __init__(self, api_key: str, timeout: float = 120.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
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
            temperature: float = OPENROUTER_MAX_TOKENS,
            max_tokens: int = OPENROUTER_MAX_TOKENS,
    ) -> AsyncIterator[StreamDelta]:
        """Stream chat completion, yielding deltas with text or tool calls."""
        payload = self._build_payload(messages, model, tools, temperature, max_tokens)

        try:
            async with self._client.stream("POST", "/chat/completions", json=payload) as response:
                await self._check_response_status(response)
                async for delta in self._parse_sse(response):
                    yield delta
        except httpx.HTTPError as e:
            raise LLMError(f"OpenRouter request failed: {e}") from e

    async def _parse_sse(self, response: httpx.Response) -> AsyncIterator[StreamDelta]:
        """Parse SSE stream into StreamDelta objects."""
        tool_calls_acc: dict[int, dict] = {}

        async for data in self._iter_sse_data(response):
            if data == "[DONE]":
                break

            chunk = self._parse_json_chunk(data)
            if not chunk:
                continue

            choice = chunk.get("choices", [{}])[0]
            delta = choice.get("delta", {})
            finish = choice.get("finish_reason")

            self._accumulate_tool_calls(delta.get("tool_calls", []), tool_calls_acc)

            text = delta.get("content") or ""
            if text:
                yield StreamDelta(text=text, finish_reason=finish)
            elif finish and not tool_calls_acc:
                yield StreamDelta(finish_reason=finish)

        # Yield accumulated tool calls if any after stream ends or [DONE] is received
        if tool_calls_acc:
            yield StreamDelta(tool_calls=self._build_tool_calls(tool_calls_acc))

    @staticmethod
    def _build_payload(
            messages: list[dict],
            model: str,
            tools: list[dict] | None,
            temperature: float,
            max_tokens: int
    ) -> dict[str, Any]:
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

    @staticmethod
    async def _check_response_status(response: httpx.Response) -> None:
        """Raise LLMError if the response status is not 200 OK."""
        if response.status_code != 200:
            body = await response.aread()
            raise LLMError(f"OpenRouter {response.status_code}: {body.decode()}")

    @staticmethod
    async def _iter_sse_data(response: httpx.Response) -> AsyncIterator[str]:
        """Yield raw data payloads from Server-Sent Events lines."""
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                yield line[6:]

    @staticmethod
    def _parse_json_chunk(data: str) -> dict | None:
        """Parse JSON data, returning None if invalid."""
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _accumulate_tool_calls(tc_chunks: list[dict], acc: dict[int, dict]) -> None:
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
