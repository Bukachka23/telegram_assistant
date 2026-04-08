import logging
import re

import httpx

from bot.config.constants import DEFAULT_MAX_RESULTS, REQUEST_TIMEOUT
from bot.domain.protocols import SearchClientProtocol
from bot.infrastructure.search.configs import WIKIPEDIA_API, WIKIPEDIA_USER_AGENT

logger = logging.getLogger(__name__)

_RE_HTML_TAG = re.compile(r"<[^>]+>")

_UNAVAILABLE_MSG = (
    "Wikipedia search is currently unavailable (API error). "
    "Please use source='web' or another source for this query."
)


class WikipediaSearchClient(SearchClientProtocol):
    """Async client for the English Wikipedia search API."""

    def __init__(self, *, timeout: float = REQUEST_TIMEOUT) -> None:
        self._client = httpx.AsyncClient(timeout=timeout, headers={"User-Agent": WIKIPEDIA_USER_AGENT})

    async def close(self) -> None:
        await self._client.aclose()

    async def search(self, query: str, *, max_results: int = DEFAULT_MAX_RESULTS) -> str:
        """Search Wikipedia and return formatted results with snippets."""
        try:
            results = await self._search_articles(query, max_results)
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Wikipedia API returned HTTP %s for '%s' — source marked unavailable",
                exc.response.status_code,
                query,
            )
            return _UNAVAILABLE_MSG
        except httpx.HTTPError as exc:
            logger.warning("Wikipedia request failed for '%s': %s", query, exc)
            return _UNAVAILABLE_MSG

        if not results:
            return f"No Wikipedia articles found for '{query}'"

        lines = [f"Wikipedia results for '{query}':"]
        for article in results:
            title = article.get("title", "")
            snippet = self._clean_snippet(article.get("snippet", ""))
            pageid = article.get("pageid", 0)
            url = f"https://en.wikipedia.org/?curid={pageid}"
            lines.extend((f"\n📖 {title}", f"   {url}"))
            if snippet:
                lines.append(f"   {snippet}")

        return "\n".join(lines)

    async def _search_articles(self, query: str, max_results: int) -> list[dict]:
        """Fetch raw search results. Raises ``httpx.HTTPError`` on any HTTP failure."""
        response = await self._client.get(
            WIKIPEDIA_API,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": max_results,
                "format": "json",
                "utf8": 1,
            },
        )
        response.raise_for_status()
        return response.json().get("query", {}).get("search", [])

    @staticmethod
    def _clean_snippet(snippet: str) -> str:
        """Remove HTML tags from Wikipedia search snippets."""
        return _RE_HTML_TAG.sub("", snippet)
