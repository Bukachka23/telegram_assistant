import logging
import re

import httpx

from bot.config.constants import DEFAULT_MAX_RESULTS, MAX_ARXIV_AUTHORS, REQUEST_TIMEOUT
from bot.domain.protocols import SearchClientProtocol
from bot.infrastructure.search.configs import ARXIV_API

logger = logging.getLogger(__name__)

_RE_ENTRY_BLOCKS = re.compile(r"<entry>(.*?)</entry>", re.DOTALL)
_RE_AUTHOR_NAMES = re.compile(r"<name>(.*?)</name>")
_RE_ARXIV_ID = re.compile(r"<id>(.*?)</id>")
_TAG_PATTERNS: dict[str, re.Pattern[str]] = {
    "title": re.compile(r"<title[^>]*>(.*?)</title>", re.DOTALL),
    "summary": re.compile(r"<summary[^>]*>(.*?)</summary>", re.DOTALL),
    "published": re.compile(r"<published[^>]*>(.*?)</published>", re.DOTALL),
}


class ArxivSearchClient(SearchClientProtocol):
    """Async client for arXiv Atom feed search API."""

    def __init__(self, *, timeout: float = REQUEST_TIMEOUT) -> None:
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def search(self, query: str, *, max_results: int = DEFAULT_MAX_RESULTS) -> str:
        """Search arXiv papers and return formatted results."""
        entries = await self._fetch_entries(query, max_results)
        if not entries:
            return f"No arXiv papers found for '{query}'"

        lines = [f"arXiv results for '{query}':"]
        lines.extend(self._format_entry(entry) for entry in entries)
        return "\n".join(lines)

    async def _fetch_entries(self, query: str, max_results: int) -> list[dict]:
        try:
            response = await self._client.get(
                ARXIV_API,
                params={
                    "search_query": f"all:{query}",
                    "start": 0,
                    "max_results": max_results,
                    "sortBy": "relevance",
                    "sortOrder": "descending",
                },
            )
            response.raise_for_status()
            return self._parse_atom_feed(response.text)
        except httpx.HTTPError:
            logger.warning("arXiv search failed for '%s'", query, exc_info=True)
            return []

    @staticmethod
    def _format_entry(entry: dict) -> str:
        title = entry.get("title", "Untitled")
        authors = entry.get("authors", "")
        summary = entry.get("summary", "")[:300]
        link = entry.get("link", "")
        published = entry.get("published", "")[:10]

        parts = [f"\n📄 {title}"]
        if authors:
            parts.append(f"   Authors: {authors}")
        if published:
            parts.append(f"   Published: {published}")
        parts.append(f"   {link}")
        if summary:
            cleaned = " ".join(summary.split())
            parts.append(f"   {cleaned}")

        return "\n".join(parts)

    @staticmethod
    def _parse_atom_feed(xml_text: str) -> list[dict]:
        """Minimal Atom XML parsing without lxml dependency."""
        entries = []
        entry_blocks = _RE_ENTRY_BLOCKS.findall(xml_text)

        for block in entry_blocks:
            title = _extract_tag(block, "title")
            summary = _extract_tag(block, "summary")
            published = _extract_tag(block, "published")

            link_match = _RE_ARXIV_ID.search(block)
            link = link_match.group(1) if link_match else ""

            author_names = _RE_AUTHOR_NAMES.findall(block)
            authors = ", ".join(author_names[:MAX_ARXIV_AUTHORS])
            if len(author_names) > MAX_ARXIV_AUTHORS:
                authors += f" et al. ({len(author_names)} authors)"

            entries.append({
                "title": title,
                "summary": summary,
                "link": link,
                "published": published,
                "authors": authors,
            })

        return entries


def _extract_tag(text: str, tag: str) -> str:
    """Extract text content from an XML tag using precompiled patterns where available."""
    pattern = _TAG_PATTERNS.get(tag) or re.compile(rf"<{tag}[^>]*>(.*?)</{tag}>", re.DOTALL)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""
