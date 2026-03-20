"""Convert LLM Markdown output to Telegram-compatible HTML."""

import re
from html import escape


def md_to_tg_html(text: str) -> str:
    """Convert standard Markdown to Telegram HTML.

    Telegram supports: <b>, <i>, <u>, <s>, <code>, <pre>,
    <blockquote>, <a href="">, <tg-spoiler>.

    Handles: headers, bold, italic, strikethrough, code blocks,
    inline code, blockquotes, links, tables, horizontal rules.
    """
    # 1. Extract fenced code blocks before any processing
    code_blocks: list[str] = []
    text = _extract_fenced_code(text, code_blocks)

    # 2. Extract inline code
    inline_codes: list[str] = []
    text = _extract_inline_code(text, inline_codes)

    # 3. Escape HTML in remaining text
    text = escape(text)

    # 4. Convert Markdown → HTML (order matters)
    text = _convert_headers(text)
    text = _convert_bold_italic(text)
    text = _convert_strikethrough(text)
    text = _convert_blockquotes(text)
    text = _convert_links(text)
    text = _convert_tables(text)
    text = _convert_horizontal_rules(text)
    text = _convert_list_items(text)

    # 5. Restore inline code
    text = _restore_inline_code(text, inline_codes)

    # 6. Restore code blocks
    text = _restore_code_blocks(text, code_blocks)

    # 7. Clean up excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def _extract_fenced_code(text: str, store: list[str]) -> str:
    """Replace ```lang\\ncode\\n``` with placeholders."""

    def replacer(m: re.Match) -> str:
        lang = m.group(1) or ""
        code = m.group(2)
        store.append((lang, code))
        return f"\x00CODEBLOCK{len(store) - 1}\x00"

    return re.sub(
        r"```(\w*)\n(.*?)```",
        replacer,
        text,
        flags=re.DOTALL,
    )


def _extract_inline_code(text: str, store: list[str]) -> str:
    """Replace `code` with placeholders."""

    def replacer(m: re.Match) -> str:
        store.append(m.group(1))
        return f"\x00INLINE{len(store) - 1}\x00"

    return re.sub(r"`([^`\n]+)`", replacer, text)


def _convert_headers(text: str) -> str:
    """Convert # headers to bold text."""
    # ### Header → \n<b>Header</b>\n
    return re.sub(
        r"^#{1,6}\s+(.+)$",
        r"\n<b>\1</b>\n",
        text,
        flags=re.MULTILINE,
    )


def _convert_bold_italic(text: str) -> str:
    """Convert **bold** and *italic*."""
    # Bold+italic ***text*** → <b><i>text</i></b>
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", text)
    # Bold **text** → <b>text</b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Italic *text* (but not inside words like file*name)
    text = re.sub(r"(?<!\w)\*([^\*\n]+?)\*(?!\w)", r"<i>\1</i>", text)
    return text


def _convert_strikethrough(text: str) -> str:
    """Convert ~~text~~ to strikethrough."""
    return re.sub(r"~~(.+?)~~", r"<s>\1</s>", text)


def _convert_blockquotes(text: str) -> str:
    """Convert > quote lines to blockquote tags."""
    lines = text.split("\n")
    result: list[str] = []
    in_quote = False

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("&gt; "):
            # &gt; is escaped '>'
            content = stripped[5:]
            if not in_quote:
                result.append("<blockquote>")
                in_quote = True
            result.append(content)
        else:
            if in_quote:
                result.append("</blockquote>")
                in_quote = False
            result.append(line)

    if in_quote:
        result.append("</blockquote>")

    return "\n".join(result)


def _convert_links(text: str) -> str:
    """Convert [text](url) to <a> tags."""
    return re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2">\1</a>',
        text,
    )


def _convert_tables(text: str) -> str:
    """Convert Markdown tables to preformatted text.

    Telegram has no table support, so we render them as <pre> blocks.
    """
    lines = text.split("\n")
    result: list[str] = []
    table_lines: list[str] = []
    in_table = False

    for line in lines:
        is_table_row = bool(re.match(r"^\s*\|.*\|\s*$", line))

        if is_table_row:
            if not in_table:
                in_table = True
            table_lines.append(line)
        else:
            if in_table:
                result.append(_render_table(table_lines))
                table_lines = []
                in_table = False
            result.append(line)

    if in_table:
        result.append(_render_table(table_lines))

    return "\n".join(result)


def _render_table(lines: list[str]) -> str:
    """Render table lines as a <pre> block."""
    # Filter out separator rows (|---|---|)
    content = []
    for line in lines:
        if re.match(r"^\s*\|[\s\-:|]+\|\s*$", line):
            continue
        content.append(line)
    return "<pre>" + "\n".join(content) + "</pre>"


def _convert_horizontal_rules(text: str) -> str:
    """Convert --- to a simple line."""
    return re.sub(r"^-{3,}\s*$", "—" * 20, text, flags=re.MULTILINE)


def _convert_list_items(text: str) -> str:
    """Convert - item to • item for unordered lists."""
    return re.sub(r"^(\s*)[-*]\s+", r"\1• ", text, flags=re.MULTILINE)


def _restore_inline_code(text: str, store: list[str]) -> str:
    """Replace inline code placeholders with <code> tags."""
    for i, code in enumerate(store):
        text = text.replace(
            f"\x00INLINE{i}\x00",
            f"<code>{escape(code)}</code>",
        )
    return text


def _restore_code_blocks(text: str, store: list) -> str:
    """Replace code block placeholders with <pre><code> tags."""
    for i, (lang, code) in enumerate(store):
        escaped = escape(code.rstrip())
        if lang:
            replacement = (
                f'<pre><code class="language-{escape(lang)}">'
                f"{escaped}</code></pre>"
            )
        else:
            replacement = f"<pre><code>{escaped}</code></pre>"
        text = text.replace(f"\x00CODEBLOCK{i}\x00", replacement)
    return text
