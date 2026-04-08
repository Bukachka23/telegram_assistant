import logging

import httpx

from bot.config.constants import DEFAULT_MAX_RESULTS, REQUEST_TIMEOUT
from bot.domain.protocols import SearchClientProtocol
from bot.infrastructure.search.configs import GITHUB_API_BASE, GITHUB_HEADERS

logger = logging.getLogger(__name__)


class GitHubSearchClient(SearchClientProtocol):
    """Async client for GitHub public search API."""

    def __init__(self, *, timeout: float = REQUEST_TIMEOUT) -> None:
        self._client = httpx.AsyncClient(timeout=timeout, headers=GITHUB_HEADERS)

    async def close(self) -> None:
        await self._client.aclose()

    async def search(self, query: str, *, max_results: int = DEFAULT_MAX_RESULTS) -> str:
        """Search GitHub repositories and return formatted results."""
        repos = await self._search_repos(query, max_results)
        if not repos:
            return f"No GitHub repositories found for '{query}'"

        lines = [f"GitHub results for '{query}':"]
        for repo in repos:
            name = repo.get("full_name", "")
            desc = (repo.get("description") or "")[:200]
            stars = repo.get("stargazers_count", 0)
            lang = repo.get("language") or ""
            url = repo.get("html_url", "")
            updated = (repo.get("updated_at") or "")[:10]

            header = f"\n⭐ {name} ({stars:,} stars)"
            if lang:
                header += f" [{lang}]"
            if updated:
                header += f" • updated {updated}"
            lines.extend((header, url))
            if desc:
                lines.append(desc)

        return "\n".join(lines)

    async def _search_repos(self, query: str, max_results: int) -> list[dict]:
        try:
            response = await self._client.get(
                f"{GITHUB_API_BASE}/search/repositories",
                params={"q": query, "sort": "stars", "per_page": max_results},
            )
            response.raise_for_status()
            return response.json().get("items", [])
        except httpx.HTTPError:
            logger.warning("GitHub repo search failed for '%s'", query, exc_info=True)
            return []
