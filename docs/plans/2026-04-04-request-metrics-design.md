# Request Metrics & /stats Command — Design Document

**Date:** 2026-04-04  
**Status:** Approved design, ready for implementation

---

## 1. Problem

The bot has no visibility into model performance, cost, or usage patterns. Model selection is based on gut feeling rather than data. OpenRouter returns token counts and sometimes cost in every response, but the bot throws all of it away.

## 2. Solution

Capture per-request metrics passively (tokens, latency, cost, tool usage) into SQLite, and expose them via a `/stats` command that aggregates by model over a configurable time window.

## 3. Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Time window | **Configurable** — `/stats`, `/stats 30`, `/stats today` | Need both "how did today's experiment go?" and "which model is cheapest this month?" |
| Storage | **Same SQLite database, new table** | Follow existing MemoryStore/MonitorStore pattern. One DB, one connection. |
| Granularity | **One row per user message** | Maps to user experience. Multi-round tool calls aggregated into one entry. |
| Cost data | **Parse from OpenRouter response** | Token usage always present in final SSE chunk. Cost sometimes included. No config maintenance. |
| Tool tracking | **Tool names list** | Comma-separated string column. Know which tools each model uses without a child table. |
| Output format | **Text summary** | Compact Telegram message with emoji. No Telegra.ph, no sub-commands for v1. |

## 4. Architecture

### 4.1 Data Capture Flow

```
User sends message
  → LLMService.stream_response() starts timer
    → OpenRouterClient.stream_completion() streams chunks
      → parse_sse() extracts usage from final chunk → TokenUsage
    → First text chunk → record TTFB
    → Tool calls → record tool names
    → Error → record error_text
  → Timer stops
  → MetricsStore.record(RequestMetric) — fire-and-forget
```

### 4.2 Query Flow

```
/stats [days]
  → MetricsService.build_stats(days)
    → MetricsStore.query(days) → raw rows
    → Aggregate by model: avg tokens, avg latency, total cost, error rate
    → Count tool names across all rows
    → Format as Telegram text
  → Send to chat
```

## 5. Component Details

### 5.1 TokenUsage & StreamDelta changes (`domain/models/tools.py`)

```python
@dataclass(frozen=True)
class TokenUsage:
    """Token counts from an LLM response."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float | None = None

@dataclass(frozen=True)
class StreamDelta:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str | None = None
    usage: TokenUsage | None = None  # NEW
```

### 5.2 SSE Parser changes (`infrastructure/openrouter/utils.py`)

Extract `usage` from the final chunk before `[DONE]`. Attach it to the last yielded `StreamDelta`.

```python
# In parse_sse, track last_usage across chunks:
usage_data = chunk.get("usage")
if usage_data:
    last_usage = TokenUsage(
        prompt_tokens=usage_data.get("prompt_tokens", 0),
        completion_tokens=usage_data.get("completion_tokens", 0),
        total_tokens=usage_data.get("total_tokens", 0),
        cost=usage_data.get("cost"),
    )

# When yielding the final delta or tool calls, attach usage
```

### 5.3 RequestMetric (`domain/models/metrics.py`)

```python
@dataclass(frozen=True)
class RequestMetric:
    """A single user-message-level metric record."""
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float | None
    latency_ms: int
    ttfb_ms: int
    tool_names: str       # comma-separated
    is_error: bool
    error_text: str
```

### 5.4 MetricsStore (`infrastructure/storage/metrics_storage.py`)

Same pattern as MemoryStore — accepts shared SQLite connection, creates table on init.

```sql
CREATE TABLE IF NOT EXISTS request_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model TEXT NOT NULL,
    tokens_in INTEGER NOT NULL DEFAULT 0,
    tokens_out INTEGER NOT NULL DEFAULT 0,
    cost_usd REAL,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    ttfb_ms INTEGER NOT NULL DEFAULT 0,
    tool_names TEXT NOT NULL DEFAULT '',
    is_error INTEGER NOT NULL DEFAULT 0,
    error_text TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_request_metrics_created_at
ON request_metrics(created_at);

CREATE INDEX IF NOT EXISTS idx_request_metrics_model
ON request_metrics(model);
```

Methods:
- `init()` — create table
- `record(metric: RequestMetric)` — insert row, fire-and-forget (errors logged, not raised)
- `query(days: int)` — return aggregated rows grouped by model
- `query_tool_names(days: int)` — return raw tool_names strings for counting
- `count()` — total rows
- `close()` — close if owns connection

### 5.5 MetricsService (`services/metrics.py`)

Aggregation + formatting logic, fully testable without a database.

```python
class MetricsService:
    def __init__(self, store: MetricsStore) -> None: ...

    async def build_stats(self, days: int = 7) -> str:
        """Build the /stats output text."""
        # 1. Query model aggregates
        # 2. Query tool names, count with Counter
        # 3. Format as Telegram text

    def format_model_stats(self, rows: list) -> str: ...
    def format_tool_stats(self, tool_names: list[str]) -> str: ...
```

Output format:
```
📊 Stats (last 7 days) — 70 requests

🤖 claude-sonnet-4 — 47 req
  📝 Tokens: 1.2K in / 2.9K out avg
  ⏱ Latency: 3.2s avg · TTFB 0.8s
  💰 Cost: $0.42
  ❌ Errors: 2 (4.3%)

🤖 gemini-flash — 23 req
  📝 Tokens: 980 in / 1.6K out avg
  ⏱ Latency: 1.1s avg · TTFB 0.3s
  💰 Cost: $0.03
  ❌ Errors: 0

🔧 Tools: web_search ×31 · recall_memory ×18 · search_vault ×5
```

### 5.6 LLM Service changes (`services/llm.py`)

Wrap `stream_response` with timing and metric collection:

```python
async def stream_response(self, user_id, user_text):
    t_start = time.monotonic()
    t_first_token = None
    last_usage = None
    tool_names_collected = []
    error_text = ""

    # ... existing streaming + tool loop ...
    # On first text chunk: t_first_token = time.monotonic()
    # On each delta.usage: last_usage = delta.usage
    # On each tool call: tool_names_collected.append(tc.name)
    # On error: error_text = str(error)

    t_end = time.monotonic()
    await self._record_metric(...)  # fire-and-forget
```

`_record_metric` swallows all exceptions — metrics must never break a response.

### 5.7 `/stats` command (`handlers/commands.py`)

```python
@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    args = (message.text or "").split(maxsplit=1)
    if len(args) > 1:
        arg = args[1].strip()
        days = 1 if arg == "today" else (0 if arg == "all" else int(arg))
    else:
        days = 7
    text = await metrics_service.build_stats(days=days)
    await message.answer(text, parse_mode="Markdown")
```

### 5.8 Wiring in `main.py`

```python
# After shared_db setup:
metrics_store = MetricsStore(db_path=settings.memory_db_path, db=shared_db)
await metrics_store.init()

metrics_service = MetricsService(store=metrics_store)

# Pass to LLMService:
llm = LLMService(..., metrics_store=metrics_store)

# Pass to commands:
setup_commands(..., metrics=metrics_service)

# Health:
health.set_metrics_store(metrics_store)

# Cleanup:
# (uses shared_db, closed by shared_db.close())
```

## 6. Edge Cases

| Case | Handling |
|------|----------|
| OpenRouter doesn't return `usage` | tokens_in/out = 0, cost = null |
| Metric recording fails (DB error) | Log warning, swallow exception, response unaffected |
| No data in time window | "No requests recorded in the last N days." |
| Cost is null for all requests | Show "Cost: n/a" |
| `/stats abc` (invalid argument) | Show usage hint |
| Tool calls span multiple rounds | All tool names collected across all rounds |
| `complete_side_context` (deep research internal) | NOT tracked — only user-facing stream_response |

## 7. File Inventory

### New files (5 production + 3 test)

| File | Purpose | Est. LOC |
|------|---------|----------|
| `src/bot/domain/models/metrics.py` | `RequestMetric` dataclass | ~25 |
| `src/bot/infrastructure/storage/metrics_storage.py` | `MetricsStore` — table, record, query | ~90 |
| `src/bot/services/metrics.py` | `MetricsService` — aggregation + formatting | ~110 |
| `tests/unit/test_metrics_storage.py` | Store record, query, filtering | ~90 |
| `tests/unit/test_metrics_service.py` | Formatting, edge cases, tool counting | ~100 |
| `tests/unit/test_metrics_capture.py` | Usage parsing from SSE, TokenUsage | ~80 |

### Modified files (7)

| File | Change | Est. delta |
|------|--------|-----------|
| `domain/models/tools.py` | Add `TokenUsage`, `usage` to `StreamDelta` | +15 |
| `domain/models/__init__.py` | Re-export new types | +5 |
| `infrastructure/openrouter/utils.py` | Parse `usage` from final SSE chunk | +15 |
| `services/llm.py` | Timing, tool tracking, metric emission | +40 |
| `handlers/commands.py` | `/stats` handler + `/start` help update | +25 |
| `main.py` | Wire store, service, pass to handlers | +20 |
| `services/health.py` | Add request count to `/status` | +5 |

### Totals

| Category | LOC |
|----------|-----|
| Production code | ~350 |
| Tests | ~270 |
| **Total** | **~620** |

## 8. Implementation Order

```
Phase 1: Domain models + storage (no behavior change)
  • RequestMetric dataclass
  • TokenUsage dataclass + StreamDelta change
  • MetricsStore with SQLite table
  • Tests for storage

Phase 2: SSE parser — capture usage
  • Parse usage from final SSE chunk
  • Attach to StreamDelta
  • Tests for parsing

Phase 3: LLM service — timing + metric emission
  • Wrap stream_response with timing
  • Collect tool names across rounds
  • Fire-and-forget record to MetricsStore
  • Tests for capture logic

Phase 4: MetricsService — aggregation + formatting
  • Query + aggregate by model
  • Tool name counting
  • Format as Telegram text
  • Tests for formatting + edge cases

Phase 5: /stats command + main.py wiring
  • Command handler with argument parsing
  • Wire MetricsStore + MetricsService in main.py
  • Update /start help text
  • Add request count to /status

Phase 6: Verification
  • Full test suite passes
  • Import chain works
  • Manual: make a request, run /stats, see data
```

## 9. Validation Criteria

- [ ] Every `stream_response` call records a metric row
- [ ] Token counts match what OpenRouter returns in `usage`
- [ ] Latency and TTFB are realistic (not zero, not wildly off)
- [ ] Cost is captured when OpenRouter provides it, `null` otherwise
- [ ] Tool names are recorded across multi-round conversations
- [ ] Errors are recorded with error text but don't break responses
- [ ] `/stats` shows per-model breakdown with correct aggregates
- [ ] `/stats 30` and `/stats today` filter correctly
- [ ] Empty time window shows helpful "no data" message
- [ ] Metric recording failure never affects user response
- [ ] `/status` shows total request count
- [ ] All existing tests pass unchanged
