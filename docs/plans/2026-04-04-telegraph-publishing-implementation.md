# Telegraph Publishing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Publish long LLM responses and deep research results to Telegra.ph, sending a preview + link back to chat instead of cluttering it with split messages.

**Architecture:** A Telegraph client (httpx) creates an anonymous account at startup and publishes pages on demand. A publish service checks a configurable character threshold and orchestrates formatting + publishing. Markdown is converted to Telegraph Nodes via `mistune` (Markdown→HTML) + a custom HTML→Nodes parser. Handlers call the service and fall back to split messages with a notice if Telegraph fails.

**Tech Stack:** Python 3.11+, httpx (existing), mistune (new dep), html.parser (stdlib), pydantic (existing)

**Pre-existing test failures:** 5 tests fail before this work (test_llm x3, test_scheduler x1, test_tools x1). These are unrelated. Our verification baseline is 217 passing tests.

---

### Task 1: Add `mistune` dependency + domain foundation

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/bot/domain/exceptions.py`
- Modify: `src/bot/domain/models/config.py`
- Modify: `src/bot/domain/models/__init__.py`
- Modify: `src/bot/config/config.py`
- Modify: `config.yaml`
- Test: `tests/unit/test_config.py` (existing — verify it still passes)

**Step 1: Add mistune to dependencies**

In `pyproject.toml`, add `"mistune>=3.0"` to the `dependencies` list:

```python
dependencies = [
    "aiogram>=3.26.0",
    "telethon>=1.42.0",
    "httpx>=0.28.1",
    "pydantic>=2.12.5",
    "pydantic-settings>=2.13.1",
    "pyyaml>=6.0.3",
    "python-dotenv>=1.2.2",
    "aiofiles>=25.1.0",
    "aiosqlite>=0.22.1",
    "croniter>=2.0",
    "mistune>=3.0",
]
```

Run: `cd /Users/bukachiyboss/Documents/PROJECTS/TELEGRAM_ASSISTANT && uv sync`

**Step 2: Add TelegraphError exception**

In `src/bot/domain/exceptions.py`, add after `WebSearchError`:

```python
class TelegraphError(BotError):
    """Raised when Telegraph API operations fail."""
```

**Step 3: Add TelegraphConfig pydantic model**

In `src/bot/domain/models/config.py`, add after `SchedulerConfig`:

```python
class TelegraphConfig(BaseModel):
    enabled: bool = True
    threshold_chars: int = 8000
    author_name: str = "Telegram Assistant"
    author_url: str = ""
```

**Step 4: Re-export TelegraphConfig**

In `src/bot/domain/models/__init__.py`, add `TelegraphConfig` to the imports from `config` and to `__all__`.

**Step 5: Add telegraph field to Settings**

In `src/bot/config/config.py`, import `TelegraphConfig` and add to `Settings`:

```python
telegraph: TelegraphConfig = Field(default_factory=TelegraphConfig)
```

**Step 6: Add telegraph section to config.yaml**

```yaml
telegraph:
  enabled: true
  threshold_chars: 8000
  author_name: "Telegram Assistant"
  author_url: ""
```

**Step 7: Install dependency and verify**

Run:
```bash
uv sync
python -m pytest tests/unit/test_config.py -v
```
Expected: all config tests pass. `import mistune` works.

**Step 8: Commit**

```bash
git add -A
git commit -m "feat(telegraph): add mistune dep, TelegraphError, TelegraphConfig, and config wiring"
```

---

### Task 2: Telegraph API client

**Files:**
- Create: `src/bot/infrastructure/telegraph/__init__.py`
- Create: `src/bot/infrastructure/telegraph/client.py`
- Create: `tests/unit/test_telegraph_client.py`

**Step 1: Write the tests**

Create `tests/unit/test_telegraph_client.py`:

```python
"""Tests for Telegraph API client."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from bot.domain.exceptions import TelegraphError
from bot.infrastructure.telegraph.client import TelegraphClient


def _mock_response(status_code: int, json_data: dict) -> httpx.Response:
    """Build a fake httpx.Response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_data
    response.text = json.dumps(json_data)
    return response


class TestTelegraphClientInit:
    @pytest.mark.asyncio
    async def test_init_creates_account_and_stores_token(self):
        client = TelegraphClient(author_name="Test Bot")
        mock_response = _mock_response(200, {
            "ok": True,
            "result": {"access_token": "test-token-123", "short_name": "TestBot"},
        })

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response):
            await client.init()

        assert client._access_token == "test-token-123"

    @pytest.mark.asyncio
    async def test_init_raises_on_api_error(self):
        client = TelegraphClient(author_name="Test Bot")
        mock_response = _mock_response(200, {"ok": False, "error": "Bad request"})

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(TelegraphError, match="account creation failed"):
                await client.init()

    @pytest.mark.asyncio
    async def test_init_raises_on_http_error(self):
        client = TelegraphClient(author_name="Test Bot")

        with patch.object(
            client._client, "post", new_callable=AsyncMock, side_effect=httpx.HTTPError("timeout")
        ):
            with pytest.raises(TelegraphError, match="request failed"):
                await client.init()


class TestTelegraphClientCreatePage:
    @pytest.mark.asyncio
    async def test_create_page_returns_url(self):
        client = TelegraphClient(author_name="Test Bot")
        client._access_token = "test-token"

        mock_response = _mock_response(200, {
            "ok": True,
            "result": {"url": "https://telegra.ph/Test-Page-04-04"},
        })

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
            url = await client.create_page(
                title="Test Page",
                content=[{"tag": "p", "children": ["Hello"]}],
            )

        assert url == "https://telegra.ph/Test-Page-04-04"
        call_kwargs = mock_post.call_args
        body = call_kwargs[1]["json"] if "json" in call_kwargs[1] else call_kwargs[0][1]
        assert body["title"] == "Test Page"
        assert body["access_token"] == "test-token"

    @pytest.mark.asyncio
    async def test_create_page_raises_without_init(self):
        client = TelegraphClient(author_name="Test Bot")

        with pytest.raises(TelegraphError, match="not initialized"):
            await client.create_page(title="Test", content=[])

    @pytest.mark.asyncio
    async def test_create_page_raises_on_api_error(self):
        client = TelegraphClient(author_name="Test Bot")
        client._access_token = "test-token"
        mock_response = _mock_response(200, {"ok": False, "error": "CONTENT_TOO_BIG"})

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(TelegraphError, match="page creation failed"):
                await client.create_page(title="Test", content=[])

    @pytest.mark.asyncio
    async def test_create_page_raises_on_http_error(self):
        client = TelegraphClient(author_name="Test Bot")
        client._access_token = "test-token"

        with patch.object(
            client._client, "post", new_callable=AsyncMock, side_effect=httpx.HTTPError("connection error")
        ):
            with pytest.raises(TelegraphError, match="request failed"):
                await client.create_page(title="Test", content=[])


class TestTelegraphClientClose:
    @pytest.mark.asyncio
    async def test_close_closes_http_client(self):
        client = TelegraphClient(author_name="Test Bot")

        with patch.object(client._client, "aclose", new_callable=AsyncMock) as mock_close:
            await client.close()

        mock_close.assert_called_once()
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_telegraph_client.py -v`
Expected: ImportError — module not found

**Step 3: Create the package init**

Create `src/bot/infrastructure/telegraph/__init__.py`:

```python
from bot.infrastructure.telegraph.client import TelegraphClient

__all__ = ["TelegraphClient"]
```

**Step 4: Implement the client**

Create `src/bot/infrastructure/telegraph/client.py`:

```python
import json
import logging
from typing import Any

import httpx

from bot.domain.exceptions import TelegraphError

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.telegra.ph"
_TIMEOUT = 15.0


class TelegraphClient:
    """Async client for the Telegra.ph API."""

    def __init__(self, author_name: str, author_url: str = "") -> None:
        self._client = httpx.AsyncClient(base_url=_BASE_URL, timeout=_TIMEOUT)
        self._author_name = author_name
        self._author_url = author_url
        self._access_token: str | None = None

    async def init(self) -> None:
        """Create an anonymous Telegraph account and store the access token."""
        data = self._post_body(
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

        data = self._post_body(
            access_token=self._access_token,
            title=title[:256],
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

    @staticmethod
    def _post_body(**kwargs: Any) -> dict[str, Any]:
        """Build a POST body, dropping None values."""
        return {k: v for k, v in kwargs.items() if v is not None}
```

**Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/unit/test_telegraph_client.py -v`
Expected: all tests PASS

**Step 6: Commit**

```bash
git add -A
git commit -m "feat(telegraph): add TelegraphClient with init, create_page, and tests"
```

---

### Task 3: Markdown → Telegraph Nodes formatting

**Files:**
- Create: `src/bot/infrastructure/telegraph/formatting.py`
- Modify: `src/bot/infrastructure/telegraph/__init__.py`
- Create: `tests/unit/test_telegraph_formatting.py`

**Step 1: Write the tests**

Create `tests/unit/test_telegraph_formatting.py`:

```python
"""Tests for Markdown → Telegraph Node conversion."""

import pytest

from bot.infrastructure.telegraph.formatting import (
    build_page_content,
    html_to_nodes,
    md_to_telegraph_nodes,
)


class TestHtmlToNodes:
    def test_plain_text(self):
        nodes = html_to_nodes("<p>Hello world</p>")
        assert nodes == [{"tag": "p", "children": ["Hello world"]}]

    def test_bold(self):
        nodes = html_to_nodes("<p><strong>bold</strong> text</p>")
        assert nodes == [{"tag": "p", "children": [{"tag": "b", "children": ["bold"]}, " text"]}]

    def test_italic(self):
        nodes = html_to_nodes("<p><em>italic</em> text</p>")
        assert nodes == [{"tag": "p", "children": [{"tag": "i", "children": ["italic"]}, " text"]}]

    def test_link(self):
        nodes = html_to_nodes('<p><a href="https://example.com">link</a></p>')
        assert nodes == [
            {"tag": "p", "children": [
                {"tag": "a", "attrs": {"href": "https://example.com"}, "children": ["link"]},
            ]},
        ]

    def test_code_block(self):
        nodes = html_to_nodes("<pre><code>x = 1</code></pre>")
        assert nodes == [{"tag": "pre", "children": ["x = 1"]}]

    def test_inline_code(self):
        nodes = html_to_nodes("<p>use <code>pip</code> here</p>")
        assert nodes == [{"tag": "p", "children": ["use ", {"tag": "code", "children": ["pip"]}, " here"]}]

    def test_heading_h1_becomes_h3(self):
        nodes = html_to_nodes("<h1>Title</h1>")
        assert nodes == [{"tag": "h3", "children": ["Title"]}]

    def test_heading_h2_becomes_h4(self):
        nodes = html_to_nodes("<h2>Subtitle</h2>")
        assert nodes == [{"tag": "h4", "children": ["Subtitle"]}]

    def test_blockquote(self):
        nodes = html_to_nodes("<blockquote><p>quoted</p></blockquote>")
        assert nodes == [{"tag": "blockquote", "children": [{"tag": "p", "children": ["quoted"]}]}]

    def test_unordered_list(self):
        nodes = html_to_nodes("<ul><li>one</li><li>two</li></ul>")
        assert nodes == [
            {"tag": "ul", "children": [
                {"tag": "li", "children": ["one"]},
                {"tag": "li", "children": ["two"]},
            ]},
        ]

    def test_nested_formatting(self):
        nodes = html_to_nodes("<p><strong><em>bold italic</em></strong></p>")
        assert nodes == [
            {"tag": "p", "children": [
                {"tag": "b", "children": [{"tag": "i", "children": ["bold italic"]}]},
            ]},
        ]

    def test_empty_html(self):
        nodes = html_to_nodes("")
        assert nodes == []

    def test_br_tag(self):
        nodes = html_to_nodes("<p>line1<br>line2</p>")
        assert nodes == [{"tag": "p", "children": ["line1", {"tag": "br"}, "line2"]}]


class TestMdToTelegraphNodes:
    def test_simple_paragraph(self):
        nodes = md_to_telegraph_nodes("Hello world")
        assert any(
            isinstance(node, dict) and "Hello world" in str(node.get("children", []))
            for node in nodes
        )

    def test_heading(self):
        nodes = md_to_telegraph_nodes("# My Title")
        assert any(
            isinstance(node, dict) and node.get("tag") in ("h3", "h4")
            for node in nodes
        )

    def test_bold_text(self):
        nodes = md_to_telegraph_nodes("This is **bold** text")
        flat = str(nodes)
        assert "'tag': 'b'" in flat or '"tag": "b"' in flat

    def test_code_block(self):
        md = "```python\nx = 1\n```"
        nodes = md_to_telegraph_nodes(md)
        flat = str(nodes)
        assert "pre" in flat

    def test_link(self):
        nodes = md_to_telegraph_nodes("[click](https://example.com)")
        flat = str(nodes)
        assert "https://example.com" in flat

    def test_list(self):
        md = "- item one\n- item two"
        nodes = md_to_telegraph_nodes(md)
        flat = str(nodes)
        assert "li" in flat


class TestBuildPageContent:
    def test_includes_metadata_header(self):
        nodes = build_page_content(
            "Hello world",
            model="claude-sonnet",
            agent="researcher",
            date="2026-04-04",
        )
        # First node should be the metadata
        first = nodes[0]
        assert first["tag"] == "p"
        meta_text = str(first)
        assert "claude-sonnet" in meta_text
        assert "researcher" in meta_text
        assert "2026-04-04" in meta_text

    def test_includes_body_after_metadata(self):
        nodes = build_page_content(
            "# Title\n\nSome content",
            model="test",
            agent="default",
            date="2026-01-01",
        )
        # Should have more than just the metadata node
        assert len(nodes) > 1

    def test_empty_body(self):
        nodes = build_page_content(
            "",
            model="test",
            agent="default",
            date="2026-01-01",
        )
        # At least the metadata node
        assert len(nodes) >= 1
        assert nodes[0]["tag"] == "p"
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_telegraph_formatting.py -v`
Expected: ImportError — module not found

**Step 3: Implement the formatting module**

Create `src/bot/infrastructure/telegraph/formatting.py`:

```python
"""Convert Markdown to Telegra.ph Node format."""

from html.parser import HTMLParser
from typing import Any

import mistune

# Telegraph-supported tags
_ALLOWED_TAGS = frozenset({
    "a", "aside", "b", "blockquote", "br", "code", "em", "figcaption",
    "figure", "h3", "h4", "hr", "i", "img", "li", "ol", "p", "pre",
    "s", "strong", "u", "ul",
})

# Map HTML tags to Telegraph equivalents
_TAG_MAP: dict[str, str] = {
    "h1": "h3",
    "h2": "h4",
    "h3": "h3",
    "h4": "h4",
    "h5": "h4",
    "h6": "h4",
    "strong": "b",
    "em": "i",
    "del": "s",
    "strike": "s",
}


class _NodeBuilder(HTMLParser):
    """Parse HTML and build a Telegraph Node tree."""

    def __init__(self) -> None:
        super().__init__()
        self._root: list[Any] = []
        self._stack: list[dict[str, Any]] = []
        self._skip_depth: int = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        mapped = _TAG_MAP.get(tag, tag)

        # Skip tags Telegraph doesn't support (but keep their children)
        if mapped not in _ALLOWED_TAGS:
            self._skip_depth += 1
            return

        node: dict[str, Any] = {"tag": mapped}

        # Flatten <pre><code>...</code></pre> — Telegraph uses just <pre>
        if mapped == "code" and self._stack and self._stack[-1]["tag"] == "pre":
            # Don't create a child code node; text will go into pre directly
            self._skip_depth += 1
            return

        attr_dict = {k: v for k, v in attrs if v is not None}
        if "href" in attr_dict:
            node["attrs"] = {"href": attr_dict["href"]}
        elif "src" in attr_dict:
            node["attrs"] = {"src": attr_dict["src"]}

        self._stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        mapped = _TAG_MAP.get(tag, tag)

        if self._skip_depth > 0:
            self._skip_depth -= 1
            return

        if not self._stack:
            return

        if self._stack[-1]["tag"] != mapped:
            return

        node = self._stack.pop()

        # Only add children key if there are children
        if "children" not in node:
            # Self-closing tags like br have no children
            pass

        if self._stack:
            parent = self._stack[-1]
            parent.setdefault("children", []).append(node)
        else:
            self._root.append(node)

    def handle_data(self, data: str) -> None:
        if not data:
            return

        if self._stack:
            self._stack[-1].setdefault("children", []).append(data)
        elif data.strip():
            self._root.append(data)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        mapped = _TAG_MAP.get(tag, tag)
        if mapped not in _ALLOWED_TAGS:
            return

        node: dict[str, Any] = {"tag": mapped}
        attr_dict = {k: v for k, v in attrs if v is not None}
        if "src" in attr_dict:
            node["attrs"] = {"src": attr_dict["src"]}

        if self._stack:
            self._stack[-1].setdefault("children", []).append(node)
        else:
            self._root.append(node)

    def get_nodes(self) -> list[Any]:
        """Return the built node tree. Call after feeding all HTML."""
        return self._root


def html_to_nodes(html: str) -> list[dict]:
    """Convert an HTML string to a list of Telegraph Node dicts."""
    if not html.strip():
        return []
    parser = _NodeBuilder()
    parser.feed(html)
    return parser.get_nodes()


def md_to_telegraph_nodes(markdown: str) -> list[dict]:
    """Convert Markdown to Telegraph Node format via mistune."""
    if not markdown.strip():
        return []
    html = mistune.html(markdown)
    return html_to_nodes(html)


def build_page_content(
    body_md: str,
    *,
    model: str,
    agent: str,
    date: str,
) -> list[dict]:
    """Build a complete Telegraph page: metadata header + formatted body."""
    header_text = f"\U0001f9e0 {model} \u00b7 {agent} \u00b7 {date}"
    meta_node: dict[str, Any] = {
        "tag": "p",
        "children": [{"tag": "i", "children": [header_text]}],
    }

    body_nodes = md_to_telegraph_nodes(body_md) if body_md.strip() else []
    return [meta_node, *body_nodes]
```

**Step 4: Update package init**

Update `src/bot/infrastructure/telegraph/__init__.py`:

```python
from bot.infrastructure.telegraph.client import TelegraphClient
from bot.infrastructure.telegraph.formatting import build_page_content, html_to_nodes, md_to_telegraph_nodes

__all__ = ["TelegraphClient", "build_page_content", "html_to_nodes", "md_to_telegraph_nodes"]
```

**Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/unit/test_telegraph_formatting.py -v`
Expected: all tests PASS

**Step 6: Commit**

```bash
git add -A
git commit -m "feat(telegraph): add Markdown → Telegraph Nodes formatting with tests"
```

---

### Task 4: Telegraph publish service

**Files:**
- Create: `src/bot/services/telegraph.py`
- Create: `tests/unit/test_telegraph_service.py`

**Step 1: Write the tests**

Create `tests/unit/test_telegraph_service.py`:

```python
"""Tests for Telegraph publish service."""

import re
from unittest.mock import AsyncMock

import pytest

from bot.domain.exceptions import TelegraphError
from bot.services.telegraph import TelegraphPublishService, TelegraphResult


class FakeTelegraphClient:
    def __init__(self, url: str = "https://telegra.ph/Test-04-04") -> None:
        self.url = url
        self.error: Exception | None = None
        self.last_title: str | None = None
        self.last_content: list | None = None

    async def create_page(self, title: str, content: list[dict]) -> str:
        self.last_title = title
        self.last_content = content
        if self.error:
            raise self.error
        return self.url


class TestShouldPublish:
    def test_below_threshold_returns_false(self):
        service = TelegraphPublishService(client=FakeTelegraphClient(), threshold_chars=100)
        assert service.should_publish("short text") is False

    def test_above_threshold_returns_true(self):
        service = TelegraphPublishService(client=FakeTelegraphClient(), threshold_chars=10)
        assert service.should_publish("this is longer than ten chars") is True

    def test_exact_threshold_returns_false(self):
        text = "x" * 100
        service = TelegraphPublishService(client=FakeTelegraphClient(), threshold_chars=100)
        assert service.should_publish(text) is False

    def test_threshold_plus_one_returns_true(self):
        text = "x" * 101
        service = TelegraphPublishService(client=FakeTelegraphClient(), threshold_chars=100)
        assert service.should_publish(text) is True


class TestPublish:
    @pytest.mark.asyncio
    async def test_publish_returns_result_with_url_and_preview(self):
        fake_client = FakeTelegraphClient(url="https://telegra.ph/My-Page")
        service = TelegraphPublishService(client=fake_client)

        long_text = "This is a fairly long response. " * 20
        result = await service.publish(
            long_text, title="Test Question", model="claude-sonnet", agent="default",
        )

        assert isinstance(result, TelegraphResult)
        assert result.url == "https://telegra.ph/My-Page"
        assert len(result.preview) <= 310  # ~300 + "…"
        assert result.preview.endswith("…") or len(long_text) <= 300

    @pytest.mark.asyncio
    async def test_publish_short_text_preview_is_full_text(self):
        fake_client = FakeTelegraphClient()
        service = TelegraphPublishService(client=fake_client)

        result = await service.publish(
            "Short answer", title="Q", model="m", agent="a",
        )

        assert result.preview == "Short answer"

    @pytest.mark.asyncio
    async def test_publish_truncates_title_to_256(self):
        fake_client = FakeTelegraphClient()
        service = TelegraphPublishService(client=fake_client)

        long_title = "x" * 300
        await service.publish("body", title=long_title, model="m", agent="a")

        assert fake_client.last_title is not None
        assert len(fake_client.last_title) <= 256

    @pytest.mark.asyncio
    async def test_publish_passes_content_nodes_to_client(self):
        fake_client = FakeTelegraphClient()
        service = TelegraphPublishService(client=fake_client)

        await service.publish(
            "# Hello\n\nWorld", title="Test", model="claude", agent="researcher",
        )

        assert fake_client.last_content is not None
        assert len(fake_client.last_content) > 0
        # First node should be metadata
        assert fake_client.last_content[0]["tag"] == "p"

    @pytest.mark.asyncio
    async def test_publish_raises_telegraph_error_on_failure(self):
        fake_client = FakeTelegraphClient()
        fake_client.error = TelegraphError("API down")
        service = TelegraphPublishService(client=fake_client)

        with pytest.raises(TelegraphError, match="API down"):
            await service.publish("text", title="T", model="m", agent="a")


class TestPreview:
    @pytest.mark.asyncio
    async def test_preview_strips_markdown_headers(self):
        fake_client = FakeTelegraphClient()
        service = TelegraphPublishService(client=fake_client)

        text = "# Big Header\n\nActual content here that matters."
        result = await service.publish(text, title="T", model="m", agent="a")

        assert not result.preview.startswith("#")
        assert "Actual content" in result.preview

    @pytest.mark.asyncio
    async def test_preview_ends_at_word_boundary(self):
        fake_client = FakeTelegraphClient()
        service = TelegraphPublishService(client=fake_client)

        # Build text that's longer than 300 chars
        text = "word " * 100
        result = await service.publish(text, title="T", model="m", agent="a")

        # Should not cut mid-word (no trailing partial "wor…")
        assert result.preview.endswith("…")
        # The part before "…" should end with a full word
        before_ellipsis = result.preview[:-1].rstrip()
        assert before_ellipsis.endswith("word")


class TestTelegraphResult:
    def test_frozen_dataclass(self):
        result = TelegraphResult(url="https://telegra.ph/test", preview="hello")
        assert result.url == "https://telegra.ph/test"
        assert result.preview == "hello"

        with pytest.raises(AttributeError):
            result.url = "changed"  # type: ignore[misc]
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_telegraph_service.py -v`
Expected: ImportError

**Step 3: Implement the service**

Create `src/bot/services/telegraph.py`:

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/unit/test_telegraph_service.py -v`
Expected: all tests PASS

**Step 5: Commit**

```bash
git add -A
git commit -m "feat(telegraph): add TelegraphPublishService with threshold, preview, and tests"
```

---

### Task 5: Wire into handlers and main.py

**Files:**
- Modify: `src/bot/handlers/messages.py`
- Modify: `src/bot/handlers/commands.py`
- Modify: `src/bot/main.py`
- Modify: `src/bot/services/health.py`
- Modify: `src/bot/domain/models/health.py`

**Step 1: Modify `handlers/messages.py`**

Add telegraph support to `setup_messages` and `_stream_response`.

In `src/bot/handlers/messages.py`:

1. Add import at top:
```python
from bot.domain.exceptions import LLMError, TelegraphError
from bot.services.telegraph import TelegraphPublishService
```
(Replace the existing `from bot.domain.exceptions import LLMError` line.)

2. Update `setup_messages` signature:
```python
def setup_messages(
    *,
    llm: LLMService,
    draft_interval_ms: int = 800,
    telegraph: TelegraphPublishService | None = None,
) -> Router:
```

3. Update the `_stream_response` call inside `handle_message` to pass `telegraph`:
```python
            await _stream_response(
                bot=bot,
                chat_id=chat_id,
                llm=llm,
                user_id=user_id,
                user_text=message.text,
                draft_interval_ms=draft_interval_ms,
                telegraph=telegraph,
            )
```

4. Update `_stream_response` signature and body:
```python
async def _stream_response(
    *,
    bot: Bot,
    chat_id: int,
    llm: LLMService,
    user_id: int,
    user_text: str,
    draft_interval_ms: int,
    telegraph: TelegraphPublishService | None = None,
) -> None:
    """Stream LLM response via sendMessageDraft, then send formatted final."""
    draft_id = int(time.time() * 1000) % 2_147_483_647 or 1
    interval = draft_interval_ms / 1000.0
    accumulated = ""
    last_send = 0.0

    # Immediate feedback
    use_drafts = await _send_draft(bot=bot, chat_id=chat_id, draft_id=draft_id, text="Thinking…")

    async for chunk in llm.stream_response(user_id, user_text):
        accumulated += chunk

        if not use_drafts:
            continue

        now = time.time()
        if now - last_send >= interval:
            use_drafts = await _send_draft(bot=bot, chat_id=chat_id, draft_id=draft_id, text=accumulated)
            last_send = now

    # Send final message
    if not accumulated:
        await bot.send_message(chat_id=chat_id, text="🤔 No response generated.")
        return

    # Try Telegraph for long responses
    if telegraph and telegraph.should_publish(accumulated):
        try:
            result = await telegraph.publish(
                accumulated,
                title=user_text[:60],
                model=llm._conversations.get_model(user_id),
                agent=llm._conversations.get_active_agent(user_id),
            )
            await bot.send_message(
                chat_id=chat_id,
                text=f"{result.preview}\n\n📄 Full response: {result.url}",
            )
            return
        except TelegraphError:
            logger.warning("Telegraph publish failed, falling back to inline")
            await bot.send_message(
                chat_id=chat_id,
                text="⚠️ Telegra.ph unavailable, sending inline.",
            )

    await _send_formatted(bot=bot, chat_id=chat_id, text=accumulated)
```

**Step 2: Modify `handlers/commands.py`**

1. Add import at top (alongside existing imports):
```python
from bot.domain.exceptions import LLMError, TelegraphError
from bot.services.telegraph import TelegraphPublishService
```
(Replace the existing `from bot.domain.exceptions import LLMError` line.)

2. Update `setup_commands` signature:
```python
def setup_commands(  # noqa: PLR0915
    conversations: ConversationManager,
    monitor_service: MonitorServiceProtocol,
    deep_research: DeepResearchServiceProtocol | None = None,
    health: "HealthService | None" = None,
    telegraph: TelegraphPublishService | None = None,
) -> Router:
```

3. Update `cmd_deep` to publish via Telegraph:

Replace the existing block at the end of `cmd_deep`:
```python
        if answer:
            for chunk in split_for_telegram(answer):
                await message.answer(chunk, parse_mode="HTML")
```

With:
```python
        if answer:
            if telegraph:
                try:
                    result = await telegraph.publish(
                        answer,
                        title=query[:60],
                        model=model,
                        agent="researcher",
                    )
                    await message.answer(
                        f"{result.preview}\n\n📄 Deep research: {result.url}",
                    )
                    return
                except TelegraphError:
                    logger.warning("Telegraph publish failed for deep research")
                    await message.answer("⚠️ Telegra.ph unavailable, sending inline.")

            for chunk in split_for_telegram(answer):
                await message.answer(chunk, parse_mode="HTML")
```

**Step 3: Add Telegraph to health service**

In `src/bot/services/health.py`:

1. Add after `self._deep_research_available = False`:
```python
        self._telegraph_available = False
```

2. Add setter after `set_deep_research_available`:
```python
    def set_telegraph_available(self, *, available: bool) -> None:
        self._telegraph_available = available
```

3. In the `check` method, add `telegraph_available=self._telegraph_available` to the `HealthReport(...)` constructor.

In `src/bot/domain/models/health.py`:

1. Add field after `deep_research_available`:
```python
    telegraph_available: bool = False
```

2. Add line in `format_telegram` after the deep research service line:
```python
            f"  {'✅' if self.telegraph_available else '❌'} Telegraph publishing\n",
```

(Remove the `\n` from the deep research line since Telegraph now follows it, and put `\n` on the Telegraph line instead.)

**Step 4: Wire in `main.py`**

In `src/bot/main.py`:

1. Add imports after existing infrastructure imports:
```python
from bot.infrastructure.telegraph.client import TelegraphClient
from bot.services.telegraph import TelegraphPublishService
```

2. Add Telegraph initialization block after the `health` service setup (after `health.set_owner_user_id(...)`) and before the "Wire async vault tools" section:

```python
    # --- Telegraph (optional, graceful if disabled) ---
    telegraph_client: TelegraphClient | None = None
    telegraph_service: TelegraphPublishService | None = None
    if settings.telegraph.enabled:
        telegraph_client = TelegraphClient(
            author_name=settings.telegraph.author_name,
            author_url=settings.telegraph.author_url,
        )
        try:
            await telegraph_client.init()
            telegraph_service = TelegraphPublishService(
                client=telegraph_client,
                threshold_chars=settings.telegraph.threshold_chars,
            )
            logger.info(
                "Telegraph publishing enabled (threshold: %d chars)",
                settings.telegraph.threshold_chars,
            )
        except Exception:  # noqa: BLE001
            logger.warning("Telegraph account creation failed. Publishing disabled.")
            await telegraph_client.close()
            telegraph_client = None

    health.set_telegraph_available(available=telegraph_service is not None)
```

3. Update the `setup_commands` call to pass `telegraph`:
```python
    dp.include_router(
        setup_commands(
            conversations=conversations,
            monitor_service=monitor_service,
            deep_research=deep_research,
            health=health,
            telegraph=telegraph_service,
        )
    )
```

4. Update the `setup_messages` call to pass `telegraph`:
```python
    dp.include_router(
        setup_messages(
            llm=llm,
            draft_interval_ms=settings.streaming.draft_interval_ms,
            telegraph=telegraph_service,
        )
    )
```

5. Add `Telegraph: ...` log line after the Telethon log:
```python
    logger.info("Telegraph: %s", "enabled" if telegraph_service else "disabled")
```

6. Add cleanup in the `finally` block, before `await bot.session.close()`:
```python
        if telegraph_client:
            await telegraph_client.close()
```

**Step 5: Run all tests**

Run: `python -m pytest tests/ -v --tb=short`
Expected: 217+ passing (same baseline plus our new tests), same 5 pre-existing failures.

**Step 6: Commit**

```bash
git add -A
git commit -m "feat(telegraph): wire Telegraph publishing into handlers, health, and main.py"
```

---

### Task 6: Integration verification

**Step 1: Run full test suite**

```bash
python -m pytest tests/ -v --tb=short
```

Expected: All new tests pass, pre-existing failures unchanged.

**Step 2: Verify import chain**

```bash
python -c "
from bot.infrastructure.telegraph.client import TelegraphClient
from bot.infrastructure.telegraph.formatting import md_to_telegraph_nodes, build_page_content, html_to_nodes
from bot.services.telegraph import TelegraphPublishService, TelegraphResult
from bot.domain.exceptions import TelegraphError
from bot.domain.models.config import TelegraphConfig
print('All imports OK')
"
```

**Step 3: Verify config loading**

```bash
python -c "
from bot.config.config import load_settings
s = load_settings()
print(f'Telegraph enabled: {s.telegraph.enabled}')
print(f'Threshold: {s.telegraph.threshold_chars}')
print(f'Author: {s.telegraph.author_name}')
"
```

**Step 4: Verify formatting end-to-end**

```bash
python -c "
from bot.infrastructure.telegraph.formatting import build_page_content
import json

nodes = build_page_content(
    '# Research Findings\n\nThe **key insight** is that \`async\` works well.\n\n- Point one\n- Point two\n\n\`\`\`python\nx = 42\n\`\`\`',
    model='claude-sonnet-4',
    agent='researcher',
    date='2026-04-04',
)
print(json.dumps(nodes, indent=2, ensure_ascii=False))
"
```

**Step 5: Lint check**

```bash
ruff check src/bot/infrastructure/telegraph/ src/bot/services/telegraph.py tests/unit/test_telegraph_*.py
```

**Step 6: Final commit (if any lint fixes needed)**

```bash
git add -A
git commit -m "chore(telegraph): lint fixes and verification"
```
