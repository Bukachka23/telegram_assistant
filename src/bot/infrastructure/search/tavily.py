import logging

import httpx

from bot.config.constants import DEFAULT_MAX_RESULTS, REQUEST_TIMEOUT
from bot.domain.exceptions import WebSearchError
from bot.domain.protocols import SearchClientProtocol
from bot.infrastructure.search.configs import TAVILY_SEARCH_URL

logger = logging.getLogger(__name__)


class TavilySearchClient(SearchClientProtocol):
    """Async client for Tavily Search API."""

    def __init__(self, api_key: str, *, timeout: float = REQUEST_TIMEOUT) -> None:
        self._api_key = api_key
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def search(self, query: str, *, max_results: int = DEFAULT_MAX_RESULTS) -> str:
        """Search the web and return formatted results string."""
        try:
            response = await self._client.post(
                TAVILY_SEARCH_URL,
                json={
                    "api_key": self._api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "basic",
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            msg = f"Tavily Search request failed: {e}"
            raise WebSearchError(msg) from e

        data = response.json()
        results = data.get("results", [])

        if not results:
            return f"No web results found for '{query}'"

        lines = [f"Web results for '{query}':"]
        for r in results:
            title = r.get("title", "No title")
            url = r.get("url", "")
            content = r.get("content", "No description")
            lines.append(f"\n🔗 {title}\n{url}\n{content}")

        return "\n".join(lines)
