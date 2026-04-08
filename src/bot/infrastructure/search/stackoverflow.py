import logging

import httpx

from bot.config.constants import DEFAULT_MAX_RESULTS, REQUEST_TIMEOUT
from bot.domain.protocols import SearchClientProtocol
from bot.infrastructure.search.configs import STACKOVERFLOW_API

logger = logging.getLogger(__name__)


class StackOverflowSearchClient(SearchClientProtocol):
    """Async client for Stack Overflow public search API."""

    def __init__(self, *, timeout: float = REQUEST_TIMEOUT) -> None:
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def search(self, query: str, *, max_results: int = DEFAULT_MAX_RESULTS) -> str:
        """Search Stack Overflow questions and return formatted results."""
        questions = await self._search_questions(query, max_results)
        if not questions:
            return f"No Stack Overflow results for '{query}'"

        lines = [f"Stack Overflow results for '{query}':"]
        for question in questions:
            title = question.get("title", "")
            score = question.get("score", 0)
            answers = question.get("answer_count", 0)
            is_answered = question.get("is_answered", False)
            link = question.get("link", "")
            tags = question.get("tags", [])

            status = "✅" if is_answered else "❓"
            header = f"\n{status} {title} (score: {score}, answers: {answers})"
            if tags:
                header += f"\n   [{', '.join(tags[:5])}]"
            lines.extend((header, f"   {link}"))

        return "\n".join(lines)

    async def _search_questions(self, query: str, max_results: int) -> list[dict]:
        try:
            response = await self._client.get(
                f"{STACKOVERFLOW_API}/search/advanced",
                params={
                    "q": query,
                    "order": "desc",
                    "sort": "relevance",
                    "site": "stackoverflow",
                    "pagesize": max_results,
                    "filter": "!nNPvSNdWme",
                },
            )
            response.raise_for_status()
            return response.json().get("items", [])
        except httpx.HTTPError:
            logger.warning("Stack Overflow search failed for '%s'", query, exc_info=True)
            return []
