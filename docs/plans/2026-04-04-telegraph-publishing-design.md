# Telegraph Publishing for Long Responses — Design Document

**Date:** 2026-04-04  
**Status:** Approved design, ready for implementation

---

## 1. Problem

When the LLM (especially deep research) generates long responses, they get chopped into multiple Telegram messages via `split_for_telegram()`. Telegram caps at 4096 chars per message, so a deep research synthesis can become 3–5+ sequential messages — cluttered, hard to read, breaks formatting continuity.

## 2. Solution

Publish long responses to **Telegra.ph** and send a preview + link back to chat. The chat stays clean; the full answer lives on a well-formatted, mobile-friendly page.

## 3. Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| When to publish | **Hybrid** — deep research always, regular chat by threshold | Deep research is inherently long; threshold catches other long responses automatically |
| Regular chat UX | **Link + short preview** (~300 char teaser) | User knows what the answer is about without opening browser |
| Deep research UX | **Progress stays in chat, only final answer goes to Telegra.ph** | Live progress gives confidence; only the synthesis needs Telegra.ph |
| Page branding | **Metadata header** (model, agent, date) + formatted answer | Useful when revisiting old pages |
| Threshold | **Configurable in config.yaml**, default 8000 chars | Lets owner tune after living with it |
| Failure handling | **Fallback with notice** — split messages + "⚠️ Telegra.ph unavailable" | Transparent; owner knows why chat got cluttered |

## 4. Architecture

### 4.1 New Components

```
src/bot/infrastructure/telegraph/
    __init__.py
    client.py              # Async httpx client for Telegra.ph API
    formatting.py          # Markdown → Telegraph Nodes (via mistune)

src/bot/services/
    telegraph.py           # TelegraphPublishService — threshold, preview, orchestration
```

### 4.2 Data Flow — Regular Chat

```
LLM streams full response → accumulated text
  → telegraph_service.should_publish(accumulated)?
    YES → telegraph_service.publish(text, title, model, agent)
          → returns TelegraphResult(url, preview)
          → send: "{preview}\n\n📄 Full response: {url}"
    NO  → current behavior: split_for_telegram → send chunks
  
  On TelegraphError:
    → "⚠️ Telegra.ph unavailable, sending inline."
    → fallback to split_for_telegram
```

### 4.3 Data Flow — Deep Research

```
/deep <question>
  → progress messages inline (unchanged)
  → final synthesis returned
    → ALWAYS telegraph_service.publish(answer, title=query[:60], ...)
    → send: "{preview}\n\n📄 Deep research: {url}"
  
  On TelegraphError:
    → "⚠️ Telegra.ph unavailable, sending inline."
    → fallback to split_for_telegram
```

### 4.4 Startup & Lifecycle

```
main.py → run():
  if settings.telegraph.enabled:
      client = TelegraphClient(author_name, author_url)
      await client.init()          # POST /createAccount (ephemeral)
      service = TelegraphPublishService(client, threshold)
  else:
      service = None

  # Pass to handlers (None = disabled, handlers skip publish logic)
  setup_commands(..., telegraph=service)
  setup_messages(..., telegraph=service)
  
  finally:
      if telegraph_client:
          await telegraph_client.close()
```

## 5. Component Details

### 5.1 TelegraphClient (`infrastructure/telegraph/client.py`)

```python
class TelegraphClient:
    BASE_URL = "https://api.telegra.ph"
    
    def __init__(self, author_name: str, author_url: str = "") -> None:
        self._client = httpx.AsyncClient(base_url=self.BASE_URL, timeout=15.0)
        self._author_name = author_name
        self._author_url = author_url
        self._access_token: str | None = None
    
    async def init(self) -> None:
        """Create anonymous Telegraph account. Called once at startup."""
        # POST /createAccount
        # {short_name: "TgBot", author_name: ..., author_url: ...}
        # → stores self._access_token
        
    async def create_page(self, title: str, content: list[dict]) -> str:
        """Publish a page. Returns the page URL."""
        # POST /createPage
        # {access_token, title, author_name, author_url, content (JSON nodes), return_url: true}
        # → returns result["url"]
        # Raises TelegraphError on failure
        
    async def close(self) -> None:
        await self._client.aclose()
```

**Design notes:**
- No persistent token storage. Account is ephemeral — recreated on each restart. Telegra.ph accounts are free and unlimited.
- Pages created under the account persist forever (Telegra.ph never deletes pages).

### 5.2 Content Formatting (`infrastructure/telegraph/formatting.py`)

**Approach:** Markdown → HTML via `mistune` library, then HTML → Telegraph Node tree via Python's built-in `html.parser`.

```python
def md_to_telegraph_nodes(markdown: str) -> list[dict]:
    """Convert Markdown to Telegraph Node format."""
    html = mistune.html(markdown)
    return html_to_nodes(html)

def html_to_nodes(html: str) -> list[dict]:
    """Convert HTML to Telegraph's Node tree."""
    # Uses html.parser.HTMLParser subclass
    # Tag mapping:
    #   <h1>-<h4>  → h3/h4
    #   <p>        → p
    #   <strong>   → b
    #   <em>       → i
    #   <pre>      → pre
    #   <code>     → code
    #   <a>        → a (preserve href)
    #   <blockquote> → blockquote
    #   <ul>/<li>  → ul/li
    #   <br>       → br
    #   text nodes → plain strings

def build_page_content(
    body_md: str, *, model: str, agent: str, date: str
) -> list[dict]:
    """Build full page: metadata header + formatted body."""
    header = f"🧠 {model} · {agent} · {date}"
    meta_nodes = [{"tag": "p", "children": [{"tag": "em", "children": [header]}]}]
    body_nodes = md_to_telegraph_nodes(body_md)
    return meta_nodes + body_nodes
```

**Dependency:** `mistune` (pure Python, ~150KB, zero dependencies).

### 5.3 TelegraphPublishService (`services/telegraph.py`)

```python
@dataclass(frozen=True)
class TelegraphResult:
    url: str
    preview: str

class TelegraphPublishService:
    PREVIEW_LENGTH = 300
    
    def __init__(
        self,
        client: TelegraphClient,
        threshold_chars: int = 8000,
    ) -> None:
        self._client = client
        self._threshold = threshold_chars
    
    def should_publish(self, text: str) -> bool:
        return len(text) > self._threshold
    
    async def publish(
        self, text: str, *, title: str, model: str, agent: str,
    ) -> TelegraphResult:
        date = datetime.now(UTC).strftime("%Y-%m-%d")
        nodes = build_page_content(text, model=model, agent=agent, date=date)
        url = await self._client.create_page(title=title[:256], content=nodes)
        preview = self._build_preview(text)
        return TelegraphResult(url=url, preview=preview)
    
    def _build_preview(self, text: str) -> str:
        """First ~300 chars, cleaned of markdown artifacts, ending at word boundary."""
        cleaned = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        cleaned = cleaned.strip()
        if len(cleaned) <= self.PREVIEW_LENGTH:
            return cleaned
        cut = cleaned[:self.PREVIEW_LENGTH].rfind(" ")
        if cut < self.PREVIEW_LENGTH // 2:
            cut = self.PREVIEW_LENGTH
        return cleaned[:cut].rstrip() + "…"
```

### 5.4 Handler Integration

**`handlers/messages.py`** — `_stream_response` receives `telegraph: TelegraphPublishService | None`:

```python
# After streaming completes:
if accumulated and telegraph and telegraph.should_publish(accumulated):
    try:
        result = await telegraph.publish(
            accumulated, title=user_text[:60], model=model, agent=agent_name
        )
        await bot.send_message(
            chat_id, f"{result.preview}\n\n📄 Full response: {result.url}"
        )
        return
    except TelegraphError:
        logger.warning("Telegraph publish failed, falling back to inline")
        await bot.send_message(chat_id, "⚠️ Telegra.ph unavailable, sending inline.")

# Existing behavior (fallback or short response):
await _send_formatted(bot=bot, chat_id=chat_id, text=accumulated)
```

**`handlers/commands.py`** — `cmd_deep` receives `telegraph: TelegraphPublishService | None`:

```python
# After deep research returns final answer:
if answer and telegraph:
    try:
        result = await telegraph.publish(
            answer, title=query[:60], model=model, agent="researcher"
        )
        await message.answer(f"{result.preview}\n\n📄 Deep research: {result.url}")
        return
    except TelegraphError:
        logger.warning("Telegraph publish failed for deep research")
        await message.answer("⚠️ Telegra.ph unavailable, sending inline.")

# Fallback:
for chunk in split_for_telegram(answer):
    await message.answer(chunk, parse_mode="HTML")
```

## 6. Config

### 6.1 New Pydantic model (`domain/models/config.py`)

```python
class TelegraphConfig(BaseModel):
    enabled: bool = True
    threshold_chars: int = 8000
    author_name: str = "Telegram Assistant"
    author_url: str = ""
```

### 6.2 Settings integration (`config/config.py`)

```python
class Settings(BaseSettings):
    # ... existing fields ...
    telegraph: TelegraphConfig = Field(default_factory=TelegraphConfig)
```

### 6.3 config.yaml addition

```yaml
telegraph:
  enabled: true
  threshold_chars: 8000
  author_name: "Telegram Assistant"
  author_url: ""
```

## 7. Error Handling

| Error | Source | Handling |
|-------|--------|----------|
| `TelegraphError` | Account creation fails at startup | Log warning, `telegraph_service = None`, bot runs without it |
| `TelegraphError` | Page creation fails at publish time | Fallback with notice → split messages in chat |
| Network timeout | `httpx.HTTPError` in client | Wrapped as `TelegraphError`, same fallback |
| Invalid content | Malformed nodes | Caught in client, wrapped as `TelegraphError` |

**New exception (`domain/exceptions.py`):**

```python
class TelegraphError(BotError):
    """Raised when Telegraph API operations fail."""
```

## 8. File Inventory

### New files (4 production + 3 test)

| File | Purpose | Est. LOC |
|------|---------|----------|
| `src/bot/infrastructure/telegraph/__init__.py` | Package export | ~5 |
| `src/bot/infrastructure/telegraph/client.py` | Async API client | ~80 |
| `src/bot/infrastructure/telegraph/formatting.py` | Markdown → Nodes | ~100 |
| `src/bot/services/telegraph.py` | Publish service + TelegraphResult | ~70 |
| `tests/unit/test_telegraph_client.py` | Client tests | ~100 |
| `tests/unit/test_telegraph_formatting.py` | Formatting tests | ~120 |
| `tests/unit/test_telegraph_service.py` | Service + threshold + fallback tests | ~100 |

### Modified files (8)

| File | Change | Est. delta |
|------|--------|-----------|
| `domain/models/config.py` | Add `TelegraphConfig` | +10 LOC |
| `domain/models/__init__.py` | Re-export new types | +3 LOC |
| `domain/exceptions.py` | Add `TelegraphError` | +4 LOC |
| `config/config.py` | Add `telegraph` to `Settings` | +3 LOC |
| `config.yaml` | Add `telegraph` section | +5 lines |
| `handlers/messages.py` | Publish path + fallback | +25 LOC |
| `handlers/commands.py` | Deep research publish + fallback | +25 LOC |
| `main.py` | Wire client, service, cleanup, health | +25 LOC |

### Dependency

| Package | Version | Size | Note |
|---------|---------|------|------|
| `mistune` | >=3.0 | ~150KB | Pure Python, zero deps |

### Totals

| Category | LOC |
|----------|-----|
| Production code | ~360 |
| Tests | ~320 |
| **Total** | **~680** |

## 9. Implementation Order

```
Step 1: Foundation — domain + config (no behavior change)
  • TelegraphConfig in domain/models/config.py
  • TelegraphError in domain/exceptions.py  
  • telegraph field in Settings
  • telegraph section in config.yaml
  • Add mistune to pyproject.toml

Step 2: Infrastructure — Telegraph client  
  • TelegraphClient (init, create_page, close)
  • Tests for client (mocked HTTP)

Step 3: Formatting — Markdown → Nodes
  • html_to_nodes parser
  • md_to_telegraph_nodes (mistune + parser)
  • build_page_content (metadata header)
  • Tests for formatting edge cases

Step 4: Service — publish orchestration
  • TelegraphPublishService (should_publish, publish, preview)
  • TelegraphResult dataclass
  • Tests for threshold logic, preview building

Step 5: Integration — handlers + main.py
  • Wire into handlers/messages.py (regular chat)
  • Wire into handlers/commands.py (deep research)
  • Wire lifecycle in main.py (init, pass to handlers, cleanup)
  • Update health service

Step 6: Verification
  • All existing tests pass
  • Manual test: short response stays inline
  • Manual test: long response publishes + preview
  • Manual test: /deep publishes + progress stays in chat
  • Manual test: telegraph disabled in config → no change
  • Manual test: simulate telegraph failure → fallback with notice
```

## 10. Validation Criteria

- [ ] Short responses (<8000 chars) stay inline in chat — unchanged behavior
- [ ] Long responses (>8000 chars) publish to Telegra.ph → preview + link in chat
- [ ] `/deep` always publishes to Telegra.ph regardless of length
- [ ] `/deep` progress messages still appear inline during research
- [ ] Telegra.ph page has metadata header (model, agent, date)
- [ ] Telegra.ph page has correct formatting (headings, code, bold, links)
- [ ] `telegraph.enabled: false` → everything works as before
- [ ] Telegra.ph API failure → fallback to split messages + notice
- [ ] Telegra.ph init failure at startup → bot runs normally, feature disabled
- [ ] `/status` shows Telegraph availability
- [ ] All existing tests pass unchanged
