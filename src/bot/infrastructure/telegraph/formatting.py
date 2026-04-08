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
        self._skipped_tags: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        mapped = _TAG_MAP.get(tag, tag)

        # <br> is a void element — treat as self-closing
        if mapped == "br":
            self._add_node({"tag": "br"})
            return

        # Flatten <pre><code>...</code></pre> — Telegraph uses just <pre>
        if mapped == "code" and self._stack and self._stack[-1]["tag"] == "pre":
            self._skipped_tags.append(tag)
            return

        # Skip tags Telegraph doesn't support (children still promoted)
        if mapped not in _ALLOWED_TAGS:
            self._skipped_tags.append(tag)
            return

        node: dict[str, Any] = {"tag": mapped}

        attr_dict = {k: v for k, v in attrs if v is not None}
        if "href" in attr_dict:
            node["attrs"] = {"href": attr_dict["href"]}
        elif "src" in attr_dict:
            node["attrs"] = {"src": attr_dict["src"]}

        self._stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        mapped = _TAG_MAP.get(tag, tag)

        # Void elements have no end tag to process
        if mapped == "br":
            return

        # Was this tag skipped on open? Pop it from skipped list.
        if self._skipped_tags and self._skipped_tags[-1] == tag:
            self._skipped_tags.pop()
            return

        if not self._stack:
            return

        if self._stack[-1]["tag"] != mapped:
            return

        node = self._stack.pop()
        self._add_node(node)

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

    def _add_node(self, node: dict[str, Any]) -> None:
        """Append a finished node to its parent or root."""
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
