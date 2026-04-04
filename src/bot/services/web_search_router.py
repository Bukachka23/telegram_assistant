from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from bot.config.constants import (
    ARXIV_KEYWORDS,
    DEFAULT_MAX_RESULTS,
    GITHUB_KEYWORDS,
    HUGGINGFACE_KEYWORDS,
    REDDIT_KEYWORDS,
    STACKOVERFLOW_KEYWORDS,
    WIKIPEDIA_KEYWORDS,
)

if TYPE_CHECKING:
    from bot.domain.protocols import SearchClientProtocol

logger = logging.getLogger(__name__)


class WebSearchRouter:
    """Routes search queries to the best source based on keywords or explicit source."""

    def __init__(
        self,
        *,
        tavily: SearchClientProtocol | None = None,
        github: SearchClientProtocol | None = None,
        huggingface: SearchClientProtocol | None = None,
        stackoverflow: SearchClientProtocol | None = None,
        arxiv: SearchClientProtocol | None = None,
        wikipedia: SearchClientProtocol | None = None,
        reddit: SearchClientProtocol | None = None,
    ) -> None:
        self._tavily = tavily
        self._github = github
        self._huggingface = huggingface
        self._stackoverflow = stackoverflow
        self._arxiv = arxiv
        self._wikipedia = wikipedia
        self._reddit = reddit

    async def close(self) -> None:
        for client in (self._github, self._huggingface, self._stackoverflow,
                       self._arxiv, self._wikipedia, self._reddit):
            if client:
                await client.close()

    async def search(
        self,
        query: str,
        *,
        max_results: int = DEFAULT_MAX_RESULTS,
        source: str = "auto",
    ) -> str:
        """Search using the specified or auto-detected source."""
        resolved = self._resolve_source(query, source)
        logger.info("Web search: source=%s (resolved from %s) query='%s'", resolved, source, query[:80])

        dispatch = {
            "github": self._search_github,
            "huggingface": self._search_huggingface,
            "stackoverflow": self._search_stackoverflow,
            "arxiv": self._search_arxiv,
            "wikipedia": self._search_wikipedia,
            "reddit": self._search_reddit,
        }
        handler = dispatch.get(resolved, self._search_tavily)
        return await handler(query, max_results)

    @staticmethod
    def _resolve_source(query: str, source: str) -> str:
        if source != "auto":
            return source

        query_lower = query.lower()
        keyword_map = [
            (GITHUB_KEYWORDS, "github"),
            (HUGGINGFACE_KEYWORDS, "huggingface"),
            (STACKOVERFLOW_KEYWORDS, "stackoverflow"),
            (ARXIV_KEYWORDS, "arxiv"),
            (WIKIPEDIA_KEYWORDS, "wikipedia"),
            (REDDIT_KEYWORDS, "reddit"),
        ]
        for keywords, name in keyword_map:
            if any(kw in query_lower for kw in keywords):
                return name
        return "web"

    async def _search_tavily(self, query: str, max_results: int) -> str:
        if self._tavily is None:
            return "Web search (Tavily) is not configured."
        return await self._tavily.search(query, max_results=max_results)

    async def _search_github(self, query: str, max_results: int) -> str:
        if self._github is None:
            return "GitHub search is not available."
        return await self._github.search(query, max_results=max_results)

    async def _search_huggingface(self, query: str, max_results: int) -> str:
        if self._huggingface is None:
            return "HuggingFace search is not available."
        return await self._huggingface.search(query, max_results=max_results)

    async def _search_stackoverflow(self, query: str, max_results: int) -> str:
        if self._stackoverflow is None:
            return "Stack Overflow search is not available."
        return await self._stackoverflow.search(query, max_results=max_results)

    async def _search_arxiv(self, query: str, max_results: int) -> str:
        if self._arxiv is None:
            return "arXiv search is not available."
        return await self._arxiv.search(query, max_results=max_results)

    async def _search_wikipedia(self, query: str, max_results: int) -> str:
        if self._wikipedia is None:
            return "Wikipedia search is not available."
        return await self._wikipedia.search(query, max_results=max_results)

    async def _search_reddit(self, query: str, max_results: int) -> str:
        if self._reddit is None:
            return "Reddit search is not available."
        return await self._reddit.search(query, max_results=max_results)
