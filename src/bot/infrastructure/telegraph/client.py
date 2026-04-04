import json
import logging
from typing import Any

import httpx

from bot.domain.exceptions import TelegraphError

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.telegra.ph"
_TIMEOUT = 15.0
_MAX_TITLE_LENGTH = 256


class TelegraphClient:
    """Async client for the Telegra.ph API."""

    def __init__(self, author_name: str, author_url: str = "") -> None:
        self._client = httpx.AsyncClient(base_url=_BASE_URL, timeout=_TIMEOUT)
        self._author_name = author_name
        self._author_url = author_url
        self._access_token: str | None = None

    async def init(self) -> None:
        """Create an anonymous Telegraph account and store the access token."""
        data = _post_body(
            short_name="TgBot",
            author_name=self._author_name,
            author_url=self._author_url,
        )
        result = await self._request("/createAccount", data)
        self._access_token = result["access_token"]
        logger.info("Telegraph account created (short_name=TgBot)")

    async def create_page(self, title: str, content: list[dict]) -> str:
        """Publish a page and return its URL.

        Args:
            title: Page title (max 256 chars).
            content: List of Telegraph Node dicts.

        Returns:
            The public URL of the created page.

        Raises:
            TelegraphError: If the client is not initialized or the API call fails.
        """
        if self._access_token is None:
            msg = "Telegraph client not initialized — call init() first"
            raise TelegraphError(msg)

        data = _post_body(
            access_token=self._access_token,
            title=title[:_MAX_TITLE_LENGTH],
            author_name=self._author_name,
            author_url=self._author_url,
            content=json.dumps(content),
            return_url="true",
        )
        result = await self._request("/createPage", data)
        url: str = result["url"]
        logger.info("Telegraph page created: %s", url)
        return url

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def _request(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        """Send a POST request and return the result dict."""
        try:
            response = await self._client.post(path, json=data)
        except httpx.HTTPError as exc:
            msg = f"Telegraph request failed: {exc}"
            raise TelegraphError(msg) from exc

        body = response.json()
        if not body.get("ok"):
            error = body.get("error", "unknown error")
            action = "page creation" if "Page" in path else "account creation"
            msg = f"Telegraph {action} failed: {error}"
            raise TelegraphError(msg)

        return body["result"]


def _post_body(**kwargs: str) -> dict[str, str]:
    """Build a POST body, dropping None values."""
    return {k: v for k, v in kwargs.items() if v is not None}
