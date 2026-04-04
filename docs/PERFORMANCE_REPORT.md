# 🔍 Performance Profiling Report — Telegram Assistant Bot

**Date:** 2026-04-02  
**Scope:** `src/bot/` (73 files, ~5,207 LOC)  
**Project type:** Async Telegram Bot (aiogram + Telethon + OpenRouter LLM)  
**Classification:** **I/O-bound** application (LLM API calls, Telegram API, web search, SQLite)

---

## 📊 Executive Summary

| Category | Severity | Issues Found |
|----------|----------|-------------|
| 🔴 Critical (I/O & Async) | High | 4 |
| 🟠 Moderate (Memory & Data Structures) | Medium | 5 |
| 🟡 Minor (Python Idioms) | Low | 6 |
| 🟢 Good Practices Already Used | — | 8 |

**Overall Assessment:** The codebase is well-structured with clean separation of concerns. The main performance risks are concentrated in the **I/O-bound hot paths** (LLM streaming, web search, formatting) and **startup time** (~1.1s import chain). No catastrophic algorithmic issues found.

---

## ✅ Good Practices Already in Place

1. **Async I/O throughout** — httpx AsyncClient, aiosqlite, aiogram async handlers
2. **Connection reuse** — `httpx.AsyncClient` instances are reused (not created per-request)
3. **Streaming SSE parsing** — OpenRouter client uses `aiter_lines()` (not buffering full response)
4. **FTS5 for memory search** — SQLite full-text search is indexed, not brute-force
5. **Retry with backoff** — Channel fetching has proper retry + timeout decorators
6. **Conversation trimming** — `Conversation.trim()` prevents unbounded message growth
7. **Frozen dataclasses** — `AgentProfile`, `Message`, `Note`, `HealthReport` are `frozen=True` (hashable, safe)
8. **TYPE_CHECKING imports** — Heavy modules imported only at type-check time in several files

---

## 🔴 Critical Issues (High Impact)

### C1. Unprecompiled Regex Patterns in Hot Path — `formatting.py`

**File:** `src/bot/services/formatting.py`  
**Impact:** Called on **every single LLM response** sent to Telegram  
**Severity:** 🔴 High (cumulative cost per message)

The `md_to_tg_html()` function calls `re.sub()` / `re.split()` / `re.match()` with raw string patterns **~15 times per invocation** without precompiling. Python's `re` module caches compiled patterns internally (up to 512), but:
- The cache lookup adds overhead on each call
- With 15+ patterns, this adds measurable latency for every message

```python
# CURRENT (formatting.py) — recompiled on every call
text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", text)
text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
text = re.sub(r"(?<!\w)\*([^*\n]+?)\*(?!\w)", r"<i>\1</i>", text)
```

**Recommendation:** Precompile all 15 regex patterns as module-level constants:
```python
_RE_BOLD_ITALIC = re.compile(r"\*\*\*(.+?)\*\*\*")
_RE_BOLD = re.compile(r"\*\*(.+?)\*\*")
_RE_ITALIC = re.compile(r"(?<!\w)\*([^*\n]+?)\*(?!\w)")
# ... etc
```

**Estimated gain:** 1.2–2x faster formatting per message (matters most for long LLM responses with heavy Markdown).

---

### C2. Sequential Tool Execution — `llm.py`

**File:** `src/bot/services/llm.py` (lines 138–141, 150–157)  
**Impact:** When LLM requests **multiple tools** in one round  
**Severity:** 🔴 High (multiplied latency)

Tool calls are executed **sequentially** even when they're independent:

```python
# CURRENT — sequential execution
async def _execute_tool_calls(self, user_id, tool_calls, *, allowed_tools):
    for tool_call in tool_calls:
        result = await self._execute_single_tool(tool_call, ...)
        self._record_tool_result(user_id, result)
```

When the LLM requests 3 tool calls (e.g., `web_search` + `recall_memory` + `fetch_messages`), each waits for the previous to finish. For I/O-bound tools, this is pure wasted time.

**Recommendation:** Use `asyncio.gather()` for parallel execution, then record results in order:
```python
async def _execute_tool_calls(self, user_id, tool_calls, *, allowed_tools):
    self._record_tool_calls_intent(user_id, tool_calls)
    results = await asyncio.gather(
        *[self._execute_single_tool(tc, allowed_tools=allowed_tools) for tc in tool_calls]
    )
    for result in results:
        self._record_tool_result(user_id, result)
```

**Estimated gain:** Up to Nx speedup where N = number of concurrent tool calls (typically 2–3x for multi-tool rounds).

---

### C3. Startup Import Chain — ~1.1 seconds

**File:** `src/bot/main.py`  
**Impact:** Cold start / restart time  
**Severity:** 🔴 Moderate-High (Docker, serverless deployments)

Import profiling reveals:
```
bot.main total: ~1,088ms (1.1 seconds)
├── aiogram.types: 638ms (58.6%) — massive type registry
├── pydantic_settings: 155ms
├── telethon: ~25ms
├── aiohttp: ~17ms
└── rest: ~253ms
```

**`aiogram.types` alone takes 638ms** — it eagerly loads the entire Telegram Bot API type system.

**Recommendations:**
1. **Lazy-import Telethon** — it's only needed if a session exists. Move to inside `_try_connect_telethon()`
2. **Lazy-import search clients** — ArxivSearchClient, GitHubSearchClient, etc. are only needed when their search is invoked
3. For aiogram, there's no easy fix (it's the framework), but awareness helps for deployment decisions

**Estimated gain:** ~200-400ms reduction in cold start if Telethon + search clients are lazy-imported.

---

### C4. Blocking Vault Search on Filesystem — `vault.py`

**File:** `src/bot/services/vault.py`  
**Impact:** Blocks the event loop during search  
**Severity:** 🔴 High (event loop stall)

`VaultService.search()` uses synchronous file I/O (`Path.read_text()`, `Path.rglob()`) which **blocks the async event loop**:

```python
def search(self, query, *, max_results=10):
    for md_file in self._root.rglob("*.md"):  # BLOCKING
        content = file_path.read_text(encoding="utf-8")  # BLOCKING
```

If the vault has hundreds of markdown files, this can stall all async operations.

**Recommendation:** Wrap in `asyncio.to_thread()` or use `aiofiles`:
```python
async def search(self, query, *, max_results=10):
    return await asyncio.to_thread(self._search_sync, query, max_results=max_results)
```

Also, `list_notes()` and `read()` have the same issue — they're called from the `/status` health check path.

**Estimated gain:** Prevents event loop blocking for 10–500ms per vault search depending on vault size.

---

## 🟠 Moderate Issues (Medium Impact)

### M1. `_filter_tools_schema()` Regenerates Schema Every Stream Round

**File:** `src/bot/services/llm.py` (line 67, 85)  
**Impact:** Called at least once per user message, more during tool loops

```python
def _filter_tools_schema(self, allowed_tools):
    return [
        tool for tool in self._registry.to_openrouter_schema()  # Rebuilds full schema
        if tool["function"]["name"] in allowed_tools  # Linear search
    ]
```

`to_openrouter_schema()` creates new dicts every call. With `MAX_TOOL_ROUNDS=10`, this rebuilds up to 10 times per message.

**Recommendation:** Cache the schema per agent (it doesn't change during runtime):
```python
@functools.lru_cache(maxsize=16)
def _get_cached_schema(self, tools_key: tuple[str, ...]) -> list[dict]:
    ...
```

---

### M2. `Conversation.trim()` Iterates Full History Twice

**File:** `src/bot/services/conversation.py` (lines in `trim()`)

```python
def trim(self, max_messages):
    system = [m for m in self.messages if m.role == Role.SYSTEM]  # O(n)
    rest = [m for m in self.messages if m.role != Role.SYSTEM]    # O(n)
    self.messages = system + rest[-(max_messages - len(system)):]
```

Called on **every message** added. Two full passes over the list.

**Recommendation:** Single-pass partition:
```python
def trim(self, max_messages):
    if len(self.messages) <= max_messages:
        return
    system = []
    rest = []
    for m in self.messages:
        (system if m.role == Role.SYSTEM else rest).append(m)
    self.messages = system + rest[-(max_messages - len(system)):]
```

**Estimated gain:** Minor (~2x less iteration), but happens on every message.

---

### M3. `MonitorService.resolve_for_owner()` — Linear Scan Every Resolution

**File:** `src/bot/services/monitors.py` (line ~84)

Every channel resolution fetches **all monitors from SQLite** then does a linear scan:
```python
async def resolve_for_owner(self, owner_user_id, channel_ref):
    monitors = await self._store.list_monitors(owner_user_id)  # DB query
    for monitor in monitors:  # O(n) scan
        ...
```

**Recommendation:** Add a SQL query with WHERE clause to resolve directly in the database, or cache the monitor list with TTL (using the existing `cache_with_ttl` decorator!).

---

### M4. SSE Parsing Creates Intermediate Strings

**File:** `src/bot/infrastructure/openrouter/utils.py`

```python
async for line in response.aiter_lines():
    if line.startswith("data: "):
        yield line[6:]  # String slice creates new string
```

For long streaming responses, this creates thousands of intermediate string objects. The impact is low per-string but cumulative.

**Recommendation:** This is acceptable for current scale. If throughput increases, consider using `memoryview` or `orjson` for parsing.

---

### M5. `cache_with_ttl` Never Evicts Expired Entries

**File:** `src/bot/shared/decorators/cache_with_ttl.py`

The TTL cache only evicts entries when they're accessed. Stale entries for unused keys accumulate forever:
```python
if cached_entry is not None:
    timestamp, cached_value = cached_entry
    if current_time - timestamp < ttl_seconds:
        return cached_value
    del cache_store[cache_key]  # Only cleans THIS key
```

**Recommendation:** Add periodic cleanup or max size limit:
```python
# Add max_size and cleanup on every N calls
if len(cache_store) > max_size:
    now = time.monotonic()
    cache_store = {k: v for k, v in cache_store.items() if now - v[0] < ttl_seconds}
```

---

## 🟡 Minor Issues (Low Impact)

### L1. Uncompiled Regex in `arxiv.py` and `wikipedia.py`

```python
# arxiv.py — called per search result
entry_blocks = re.findall(r"<entry>(.*?)</entry>", xml_text, re.DOTALL)
# wikipedia.py
return re.sub(r"<[^>]+>", "", snippet)
```

These are in non-hot paths (search results) but should still be precompiled for consistency.

---

### L2. `_build_cycle_summary()` in Deep Research Uses `.split()` + Join

```python
cleaned = " ".join(findings.split())  # Normalize whitespace
```

For large research findings (potentially multi-KB), this creates many intermediate strings. Use a compiled regex instead:
```python
_RE_WHITESPACE = re.compile(r'\s+')
cleaned = _RE_WHITESPACE.sub(' ', findings).strip()
```

---

### L3. String Concatenation in Loop — `_recall_executor()`

**File:** `src/bot/main.py` (line ~127)
```python
for r in results:
    line = f"- [{r['category'] or 'general'}] {r['fact']}"
    if r.get("created_at"):
        line += f" (saved: {r['created_at'][:10]})"  # += in loop
    lines.append(line)
```

Low impact (max 5 results by default), but the `+=` creates a new string each time.

---

### L4. `ToolRegistry.to_openrouter_schema()` Rebuilds List Every Call

```python
def to_openrouter_schema(self) -> list[dict]:
    return [{"type": "function", "function": {...}} for tool in self._tools.values()]
```

Tools don't change at runtime. This could be cached after registration is complete.

---

### L5. `_resolve_source()` Checks Keywords with `any()` + `in`

**File:** `src/bot/services/web_search_router.py`
```python
for keywords, name in keyword_map:
    if any(kw in query_lower for kw in keywords):
        return name
```

For 5 keyword sets × ~8 keywords each = 40 substring searches. Minor, but a single compiled regex per source would be faster.

---

### L6. Dual SQLite Connection for Same Database

**File:** `src/bot/main.py` (lines 150–153)
```python
memory = MemoryStore(db_path=settings.memory_db_path)
await memory.init()
monitor_store = MonitorStore(db_path=settings.memory_db_path)  # Same DB!
await monitor_store.init()
```

Both `MemoryStore` and `MonitorStore` open **separate connections** to the **same SQLite database**. This doubles the connection overhead and can cause write contention under WAL mode.

**Recommendation:** Share a single `aiosqlite.Connection` via a connection factory or pool.

---

## 📈 Optimization Priority Matrix

| # | Issue | Impact | Effort | Priority |
|---|-------|--------|--------|----------|
| **C2** | Parallel tool execution | 🔴 2-3x latency reduction | Low (5 lines) | **P0** |
| **C4** | Async vault search | 🔴 Event loop unblocking | Low (3 lines) | **P0** |
| **C1** | Precompile regex patterns | 🔴 1.2-2x formatting speed | Low (30 min) | **P1** |
| **M1** | Cache tools schema | 🟠 Reduce per-message overhead | Low (10 lines) | **P1** |
| **M3** | Cache/query monitor resolution | 🟠 Reduce DB queries | Medium | **P2** |
| **C3** | Lazy imports | 🟠 200-400ms faster startup | Medium | **P2** |
| **L6** | Shared SQLite connection | 🟡 Reduce connection overhead | Medium | **P2** |
| **M2** | Single-pass conversation trim | 🟡 Minor CPU savings | Low (5 lines) | **P3** |
| **M5** | TTL cache eviction | 🟡 Prevent memory leak | Low (10 lines) | **P3** |
| **L1-L5** | Minor idiom improvements | 🟢 Negligible | Low | **P4** |

---

## 🔧 Quick Wins (Can Be Done Now)

### Quick Win 1: Parallel Tool Execution (~5 lines change in `llm.py`)
```python
import asyncio

# In _execute_tool_calls:
results = await asyncio.gather(
    *[self._execute_single_tool(tc, allowed_tools=allowed_tools) for tc in tool_calls]
)
```

### Quick Win 2: Async Vault Search (~3 lines change in `vault.py`)
```python
import asyncio

async def search(self, query, *, max_results=10):
    return await asyncio.to_thread(self._search_sync, query, max_results=max_results)
```

### Quick Win 3: Precompile Top 5 Hottest Regex (~15 lines in `formatting.py`)
```python
_RE_FENCED_CODE = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
_RE_INLINE_CODE = re.compile(r"`([^`\n]+)`")
_RE_BOLD_ITALIC = re.compile(r"\*\*\*(.+?)\*\*\*")
_RE_BOLD = re.compile(r"\*\*(.+?)\*\*")
_RE_ITALIC = re.compile(r"(?<!\w)\*([^*\n]+?)\*(?!\w)")
```

---

## 🏁 Conclusion

The Telegram Assistant Bot is **well-architected for its I/O-bound nature**. The codebase follows clean patterns with proper async/await, connection reuse, and data modeling. The most impactful optimizations are:

1. **Parallelize tool execution** — immediate latency improvement for multi-tool responses
2. **Unblock the event loop** — move vault filesystem operations off the main thread  
3. **Precompile regex** — reduce per-message formatting overhead

These 3 changes alone would address the most significant performance bottlenecks with minimal code changes.
