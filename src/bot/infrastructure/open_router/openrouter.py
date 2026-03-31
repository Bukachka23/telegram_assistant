import logging
from collections.abc import AsyncIterator

import httpx

from bot.domain.exceptions import LLMError
from bot.domain.models import StreamDelta
from bot.infrastructure.open_router.utils import build_payload, check_response_status, parse_sse
from bot.shared.constants import BASE_URL, OPENROUTER_MAX_TOKENS, TIMEOUT

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Async client for OpenRouter chat completions API."""

    def __init__(self, api_key: str, timeout: float = TIMEOUT) -> None:
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
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
        payload = build_payload(messages, model, tools, temperature, max_tokens)

        try:
            async with self._client.stream("POST", "/chat/completions", json=payload) as response:
                await check_response_status(response)
                async for delta in parse_sse(response):
                    yield delta
        except httpx.HTTPError as e:
            msg = f"OpenRouter request failed: {e}"
            raise LLMError(msg) from e
