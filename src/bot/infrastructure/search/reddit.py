import logging
from datetime import UTC, datetime

import httpx

from bot.config.constants import (
    DEFAULT_MAX_RESULTS,
    REDDIT_API_BASE,
    REDDIT_CACHE_TTL_SECONDS,
    REDDIT_RATE_LIMIT_STATUS,
    REDDIT_USER_AGENT,
    REQUEST_TIMEOUT,
)
from bot.shared.decorators import cache_with_ttl

logger = logging.getLogger(__name__)

_RATE_LIMIT_MSG = (
    "Reddit search is temporarily rate-limited. "
    "Please try again in a few minutes or use source='web'."
)
_UNAVAILABLE_MSG = (
    "Reddit search is currently unavailable (API error). "
    "Please try again or use source='web'."
)


class RedditSearchClient:
    """Async client for the Reddit public JSON search API (no auth required)."""

    def __init__(self, *, timeout: float = REQUEST_TIMEOUT) -> None:
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": REDDIT_USER_AGENT},
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    @cache_with_ttl(ttl_seconds=REDDIT_CACHE_TTL_SECONDS)
    async def search(self, query: str, *, max_results: int = DEFAULT_MAX_RESULTS) -> str:
        """Search Reddit and return formatted results."""
        try:
            posts = await self._search_posts(query, max_results)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == REDDIT_RATE_LIMIT_STATUS:
                logger.warning("Reddit rate limit hit for query '%s'", query)
                return _RATE_LIMIT_MSG
            logger.warning("Reddit API HTTP %d for query '%s'", exc.response.status_code, query)
            return _UNAVAILABLE_MSG
        except httpx.HTTPError:
            logger.warning("Reddit search failed for '%s'", query, exc_info=True)
            return _UNAVAILABLE_MSG

        if not posts:
            return f"No Reddit posts found for '{query}'"

        lines = [f"Reddit results for '{query}':"]
        for post in posts:
            title = post.get("title", "")
            subreddit = post.get("subreddit", "")
            score = post.get("score", 0)
            comments = post.get("num_comments", 0)
            permalink = post.get("permalink", "")
            selftext = (post.get("selftext") or "").strip()[:200]
            created = post.get("created_utc")

            date_str = ""
            if created:
                date_str = f" · {datetime.fromtimestamp(created, UTC).strftime('%Y-%m-%d')}"

            lines.extend([
                f"\n🟠 r/{subreddit} — {title}",
                f"   https://reddit.com{permalink}",
                f"   ↑{score} · {comments} comments{date_str}",
            ])
            if selftext:
                ellipsis = "..." if len(selftext) == 200 else ""  # noqa: PLR2004
                lines.append(f"   {selftext}{ellipsis}")

        return "\n".join(lines)

    async def _search_posts(self, query: str, max_results: int) -> list[dict]:
        """Fetch raw post data from Reddit's public JSON search endpoint."""
        response = await self._client.get(
            f"{REDDIT_API_BASE}/search.json",
            params={
                "q": query,
                "limit": max_results,
                "sort": "relevance",
                "t": "all",
                "type": "link",
            },
        )
        response.raise_for_status()
        children = response.json().get("data", {}).get("children", [])
        return [child["data"] for child in children]
