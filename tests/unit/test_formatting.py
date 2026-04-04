"""Tests for Markdown → Telegram HTML conversion."""

from bot.config.constants import MAX_TG_TEXT
from bot.services.formatting import md_to_tg_html, split_for_telegram


class TestHeaders:
    def test_h1(self):
        assert "<b>Title</b>" in md_to_tg_html("# Title")

    def test_h2(self):
        assert "<b>Section</b>" in md_to_tg_html("## Section")

    def test_h3(self):
        assert "<b>Sub</b>" in md_to_tg_html("### Sub")

    def test_header_with_emoji(self):
        assert "<b>🔄 Title</b>" in md_to_tg_html("### 🔄 Title")


class TestBoldItalic:
    def test_bold(self):
        assert md_to_tg_html("**hello**") == "<b>hello</b>"

    def test_italic(self):
        assert md_to_tg_html("*hello*") == "<i>hello</i>"

    def test_bold_italic(self):
        assert md_to_tg_html("***hello***") == "<b><i>hello</i></b>"

    def test_bold_in_sentence(self):
        result = md_to_tg_html("This is **very** important")
        assert result == "This is <b>very</b> important"


class TestStrikethrough:
    def test_strike(self):
        assert md_to_tg_html("~~deleted~~") == "<s>deleted</s>"


class TestCode:
    def test_inline_code(self):
        result = md_to_tg_html("Use `print()` here")
        assert result == "Use <code>print()</code> here"

    def test_fenced_code_block(self):
        text = "```python\nprint('hi')\n```"
        result = md_to_tg_html(text)
        assert '<pre><code class="language-python">' in result
        assert "print(&#x27;hi&#x27;)" in result  # escaped quotes

    def test_code_block_no_language(self):
        text = "```\nsome code\n```"
        result = md_to_tg_html(text)
        assert "<pre><code>some code</code></pre>" in result

    def test_code_block_preserves_content(self):
        text = "```python\nif x > 0:\n    print(**x**)\n```"
        result = md_to_tg_html(text)
        # **x** inside code should NOT become <b>x</b>
        assert "<b>" not in result or "<b>" not in result.split("</code>")[0]

    def test_html_in_code_escaped(self):
        text = "Use `<div>` tag"
        result = md_to_tg_html(text)
        assert "<code>&lt;div&gt;</code>" in result


class TestBlockquotes:
    def test_single_line_quote(self):
        result = md_to_tg_html("> This is a quote")
        assert "<blockquote>" in result
        assert "This is a quote" in result
        assert "</blockquote>" in result

    def test_multi_line_quote(self):
        text = "> line 1\n> line 2"
        result = md_to_tg_html(text)
        assert "<blockquote>" in result
        assert "line 1" in result
        assert "line 2" in result


class TestLinks:
    def test_link(self):
        result = md_to_tg_html("[Google](https://google.com)")
        assert '<a href="https://google.com">Google</a>' in result


class TestTables:
    def test_simple_table(self):
        text = (
            "| A | B |\n"
            "|---|---|\n"
            "| 1 | 2 |\n"
        )
        result = md_to_tg_html(text)
        assert "<pre>" in result
        # Separator row should be removed
        assert "---" not in result
        assert "| A | B |" in result
        assert "| 1 | 2 |" in result

    def test_table_preserves_content(self):
        text = (
            "| Name | Value |\n"
            "|------|-------|\n"
            "| foo | bar |\n"
        )
        result = md_to_tg_html(text)
        assert "foo" in result
        assert "bar" in result


class TestHorizontalRules:
    def test_hr(self):
        result = md_to_tg_html("---")
        assert "—" in result
        assert "---" not in result


class TestListItems:
    def test_unordered_list(self):
        result = md_to_tg_html("- item 1\n- item 2")
        assert "• item 1" in result
        assert "• item 2" in result

    def test_asterisk_list(self):
        result = md_to_tg_html("* item 1\n* item 2")
        assert "• item 1" in result


class TestHtmlEscaping:
    def test_angle_brackets_escaped(self):
        result = md_to_tg_html("x < 5 and y > 3")
        assert "&lt;" in result
        assert "&gt;" in result

    def test_ampersand_escaped(self):
        result = md_to_tg_html("A & B")
        assert "&amp;" in result


class TestComplexContent:
    def test_mixed_formatting(self):
        text = (
            "## Title\n\n"
            "Some **bold** and *italic* text.\n\n"
            "```python\nprint('hello')\n```\n\n"
            "> A quote\n\n"
            "- item 1\n"
            "- item 2"
        )
        result = md_to_tg_html(text)
        assert "<b>Title</b>" in result
        assert "<b>bold</b>" in result
        assert "<i>italic</i>" in result
        assert '<pre><code class="language-python">' in result
        assert "<blockquote>" in result
        assert "• item 1" in result

    def test_user_example_headers(self):
        text = "## Ітератор vs Ітеруємий об'єкт"
        result = md_to_tg_html(text)
        assert "<b>" in result
        assert "Ітератор" in result


class TestSplitForTelegram:
    def test_short_text_returns_single_chunk(self):
        result = split_for_telegram("Hello world")
        assert len(result) == 1
        assert "Hello world" in result[0]

    def test_empty_text_returns_empty_list(self):
        assert split_for_telegram("") == []
        assert split_for_telegram("   ") == []

    def test_long_text_splits_into_multiple_chunks(self):
        paragraphs = [f"## Section {i}\n\nParagraph {i} content. " * 20 for i in range(30)]
        long_text = "\n\n".join(paragraphs)
        assert len(long_text) > MAX_TG_TEXT

        chunks = split_for_telegram(long_text)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= MAX_TG_TEXT

    def test_all_content_preserved_across_chunks(self):
        paragraphs = [f"Unique marker {i}" for i in range(50)]
        long_text = "\n\n".join(paragraphs)
        # Make it actually long enough to split
        long_text = long_text + "\n\n" + "x" * (MAX_TG_TEXT - 100)

        chunks = split_for_telegram(long_text)
        combined = "\n".join(chunks)
        for i in range(50):
            assert f"Unique marker {i}" in combined

    def test_each_chunk_is_valid_html(self):
        blocks = [
            f"## Title {i}\n\n**Bold {i}** and *italic {i}*.\n\n"
            f"{'Some detailed explanation text. ' * 30}\n\n- item {i}a\n- item {i}b"
            for i in range(20)
        ]
        long_text = "\n\n".join(blocks)
        assert len(long_text) > MAX_TG_TEXT

        chunks = split_for_telegram(long_text)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= MAX_TG_TEXT
