import re
from html import escape

from bot.config.constants import MAX_TG_TEXT

_CHUNK_SAFETY_MARGIN = 200
_MAX_CHUNK = MAX_TG_TEXT - _CHUNK_SAFETY_MARGIN

# Precompiled regex patterns
_RE_DOUBLE_NEWLINE = re.compile(r"\n{2,}")
_RE_TRIPLE_NEWLINE = re.compile(r"\n{3,}")
_RE_FENCED_CODE = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
_RE_INLINE_CODE = re.compile(r"`([^`\n]+)`")
_RE_HEADERS = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
_RE_BOLD_ITALIC = re.compile(r"\*\*\*(.+?)\*\*\*")
_RE_BOLD = re.compile(r"\*\*(.+?)\*\*")
_RE_ITALIC = re.compile(r"(?<!\w)\*([^*\n]+?)\*(?!\w)")
_RE_STRIKETHROUGH = re.compile(r"~~(.+?)~~")
_RE_LINKS = re.compile(r"\[([^]]+)]\(([^)]+)\)")
_RE_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
_RE_TABLE_SEPARATOR = re.compile(r"^\s*\|[\s\-:|]+\|\s*$")
_RE_HORIZONTAL_RULE = re.compile(r"^-{3,}\s*$", re.MULTILINE)
_RE_LIST_ITEM = re.compile(r"^(\s*)[-*]\s+", re.MULTILINE)


def split_for_telegram(text: str) -> list[str]:
    """Split raw Markdown into chunks that fit Telegram's message limit."""
    if not text.strip():
        return []

    html_single = md_to_tg_html(text)
    if len(html_single) <= MAX_TG_TEXT:
        return [html_single]

    blocks = _split_into_blocks(text)
    chunks: list[str] = []
    current_blocks: list[str] = []
    current_len = 0

    for block in blocks:
        block_html = md_to_tg_html(block)
        block_len = len(block_html)

        if block_len > _MAX_CHUNK:
            if current_blocks:
                chunks.append(md_to_tg_html("\n\n".join(current_blocks)))
                current_blocks = []
                current_len = 0
            chunks.extend(_hard_split_html(block_html))
            continue

        if current_len + block_len + 2 > _MAX_CHUNK and current_blocks:
            chunks.append(md_to_tg_html("\n\n".join(current_blocks)))
            current_blocks = []
            current_len = 0

        current_blocks.append(block)
        current_len += block_len + 2

    if current_blocks:
        chunks.append(md_to_tg_html("\n\n".join(current_blocks)))

    return chunks or [html_single[:MAX_TG_TEXT]]


def _split_into_blocks(text: str) -> list[str]:
    """Split Markdown text into logical blocks on double newlines."""
    raw_blocks = _RE_DOUBLE_NEWLINE.split(text.strip())
    return [block for block in raw_blocks if block.strip()]


def _hard_split_html(html: str) -> list[str]:
    """Last-resort character split for a single block that exceeds the limit."""
    parts: list[str] = []
    while len(html) > MAX_TG_TEXT:
        cut = html[:MAX_TG_TEXT].rfind("\n")
        if cut < MAX_TG_TEXT // 2:
            cut = MAX_TG_TEXT
        parts.append(html[:cut])
        html = html[cut:].lstrip()
    if html:
        parts.append(html)
    return parts


def md_to_tg_html(text: str) -> str:
    """Convert standard Markdown to Telegram HTML."""
    # 1. Extract fenced code blocks before any processing
    text, code_blocks = _extract_fenced_code(text)

    # 2. Extract inline code
    text, inline_codes = _extract_inline_code(text)

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
    text = _RE_TRIPLE_NEWLINE.sub("\n\n", text)

    return text.strip()


def _extract_fenced_code(text: str) -> tuple[str, list[tuple[str, str]]]:
    r"""Replace langncode\n with placeholders and return extracted data."""
    store: list[tuple[str, str]] = []

    def replacer(m: re.Match) -> str:
        lang = m.group(1) or ""
        code = m.group(2)
        store.append((lang, code))
        return f"\x00CODEBLOCK{len(store) - 1}\x00"

    processed_text = _RE_FENCED_CODE.sub(replacer, text)
    return processed_text, store


def _extract_inline_code(text: str) -> tuple[str, list[str]]:
    """Replace `code` with placeholders and return extracted data."""
    store: list[str] = []

    def replacer(m: re.Match) -> str:
        store.append(m.group(1))
        return f"\x00INLINE{len(store) - 1}\x00"

    processed_text = _RE_INLINE_CODE.sub(replacer, text)
    return processed_text, store


def _convert_headers(text: str) -> str:
    """Convert # headers to bold text."""
    return _RE_HEADERS.sub(r"\n<b>\1</b>\n", text)


def _convert_bold_italic(text: str) -> str:
    """Convert **bold** and *italic*."""
    text = _RE_BOLD_ITALIC.sub(r"<b><i>\1</i></b>", text)
    text = _RE_BOLD.sub(r"<b>\1</b>", text)
    return _RE_ITALIC.sub(r"<i>\1</i>", text)


def _convert_strikethrough(text: str) -> str:
    """Convert ~~text~~ to strikethrough."""
    return _RE_STRIKETHROUGH.sub(r"<s>\1</s>", text)


def _convert_blockquotes(text: str) -> str:
    """Convert > quote lines to blockquote tags."""
    lines = text.split("\n")
    result: list[str] = []
    in_quote = False

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("&gt; "):
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
    return _RE_LINKS.sub(r'<a href="\2">\1</a>', text)


def _convert_tables(text: str) -> str:
    """Convert Markdown tables to preformatted text."""
    lines = text.split("\n")
    result: list[str] = []
    table_lines: list[str] = []
    in_table = False

    for line in lines:
        is_table_row = bool(_RE_TABLE_ROW.match(line))

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
    content = []
    for line in lines:
        if _RE_TABLE_SEPARATOR.match(line):
            continue
        content.append(line)
    return "<pre>" + "\n".join(content) + "</pre>"


def _convert_horizontal_rules(text: str) -> str:
    """Convert --- to a simple line."""
    return _RE_HORIZONTAL_RULE.sub("—" * 20, text)


def _convert_list_items(text: str) -> str:
    """Convert - item to • item for unordered lists."""
    return _RE_LIST_ITEM.sub(r"\1• ", text)


def _restore_inline_code(text: str, store: list[str]) -> str:
    """Replace inline code placeholders with <code> tags."""
    for i, code in enumerate(store):
        text = text.replace(
            f"\x00INLINE{i}\x00",
            f"<code>{escape(code)}</code>",
        )
    return text


def _restore_code_blocks(text: str, store: list[tuple[str, str]]) -> str:
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
