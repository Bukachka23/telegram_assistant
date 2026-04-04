import logging

import httpx

from bot.config.constants import DEFAULT_MAX_RESULTS, HF_API_BASE, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


class HuggingFaceSearchClient:
    """Async client for HuggingFace model search API."""

    def __init__(self, *, timeout: float = REQUEST_TIMEOUT) -> None:
        self._client = httpx.AsyncClient(timeout=timeout, headers={"User-Agent": "telegram-assistant-bot"})

    async def close(self) -> None:
        await self._client.aclose()

    async def search(self, query: str, *, max_results: int = DEFAULT_MAX_RESULTS) -> str:
        """Search HuggingFace models and return formatted results."""
        models = await self._search_models(query, max_results)
        if not models:
            return f"No HuggingFace models found for '{query}'"

        lines = [f"HuggingFace results for '{query}':"]
        for model in models:
            model_id = model.get("modelId", model.get("id", ""))
            downloads = model.get("downloads", 0)
            likes = model.get("likes", 0)
            pipeline = model.get("pipeline_tag") or ""

            header = f"\n🤗 {model_id} (↓{downloads:,} ❤️{likes})"
            if pipeline:
                header += f" [{pipeline}]"
            lines.extend((header, f"https://huggingface.co/{model_id}"))

        return "\n".join(lines)

    async def _search_models(self, query: str, max_results: int) -> list[dict]:
        try:
            response = await self._client.get(
                f"{HF_API_BASE}/models",
                params={
                    "search": query,
                    "sort": "downloads",
                    "direction": "-1",
                    "limit": max_results,
                },
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            logger.warning("HuggingFace search failed for '%s'", query, exc_info=True)
            return []
