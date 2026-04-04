"""Telegraph publishing service — threshold check, formatting, preview."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from bot.infrastructure.telegraph.formatting import build_page_content

if TYPE_CHECKING:
    from bot.infrastructure.telegraph.client import TelegraphClient

logger = logging.getLogger(__name__)

_PREVIEW_LENGTH = 300
_MAX_TITLE_LENGTH = 256
_RE_MD_HEADERS = re.compile(r"^#{1,6}\s+", re.MULTILINE)


@dataclass(frozen=True)
class TelegraphResult:
    """Published Telegraph page result."""

    url: str
    preview: str


class TelegraphPublishService:
    """Decides when and how to publish responses to Telegra.ph."""

    def __init__(
        self,
        client: TelegraphClient,
        threshold_chars: int = 8000,
    ) -> None:
        self._client = client
        self._threshold = threshold_chars

    def should_publish(self, text: str) -> bool:
        """Return True if text exceeds the character threshold."""
        return len(text) > self._threshold

    async def publish(
        self,
        text: str,
        *,
        title: str,
        model: str,
        agent: str,
    ) -> TelegraphResult:
        """Format, publish to Telegra.ph, and return URL + preview.

        Raises:
            TelegraphError: If the API call fails.
        """
        date = datetime.now(UTC).strftime("%Y-%m-%d")
        nodes = build_page_content(text, model=model, agent=agent, date=date)
        url = await self._client.create_page(
            title=title[:_MAX_TITLE_LENGTH],
            content=nodes,
        )
        preview = self._build_preview(text)
        return TelegraphResult(url=url, preview=preview)

    @staticmethod
    def _build_preview(text: str) -> str:
        """Extract a ~300-char teaser, cleaned of Markdown artifacts."""
        cleaned = _RE_MD_HEADERS.sub("", text).strip()
        if len(cleaned) <= _PREVIEW_LENGTH:
            return cleaned
        cut = cleaned[:_PREVIEW_LENGTH].rfind(" ")
        if cut < _PREVIEW_LENGTH // 2:
            cut = _PREVIEW_LENGTH
        return cleaned[:cut].rstrip() + "\u2026"
