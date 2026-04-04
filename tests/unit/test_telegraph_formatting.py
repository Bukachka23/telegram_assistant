"""Tests for Markdown → Telegraph Node conversion."""

import pytest

from bot.infrastructure.telegraph.formatting import (
    build_page_content,
    html_to_nodes,
    md_to_telegraph_nodes,
)


class TestHtmlToNodes:
    def test_plain_text_paragraph(self):
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

    def test_code_block_flattens_pre_code(self):
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

    def test_unsupported_tag_keeps_children(self):
        # <div> is not in Telegraph's allowed tags — children should still appear
        nodes = html_to_nodes("<div><p>inside div</p></div>")
        assert any(
            isinstance(n, dict) and n.get("tag") == "p"
            for n in nodes
        )


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
        assert "'tag': 'b'" in flat

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

    def test_empty_markdown(self):
        nodes = md_to_telegraph_nodes("")
        assert nodes == []

    def test_whitespace_only(self):
        nodes = md_to_telegraph_nodes("   \n\n  ")
        assert nodes == []


class TestBuildPageContent:
    def test_includes_metadata_header(self):
        nodes = build_page_content(
            "Hello world",
            model="claude-sonnet",
            agent="researcher",
            date="2026-04-04",
        )
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
        assert len(nodes) > 1

    def test_empty_body_still_has_metadata(self):
        nodes = build_page_content(
            "",
            model="test",
            agent="default",
            date="2026-01-01",
        )
        assert len(nodes) >= 1
        assert nodes[0]["tag"] == "p"

    def test_metadata_uses_italic(self):
        nodes = build_page_content(
            "body",
            model="m",
            agent="a",
            date="d",
        )
        first = nodes[0]
        children = first.get("children", [])
        assert any(
            isinstance(c, dict) and c.get("tag") == "i"
            for c in children
        )
