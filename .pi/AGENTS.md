# AGENTS.md — Telegram Assistant

> Project instructions for the pi coding agent. Loaded automatically at startup.

## Project Overview

Personal Telegram bot powered by OpenRouter LLM with tool calling, Obsidian vault integration, Telegram channel monitoring, a cron-based scheduler, and long-term memory. It is a **single-user (owner-only)** bot — all messages from non-owner users are silently dropped by middleware.

**Framework:** aiogram 3.x (bot) + Telethon (userbot for channel access)
**Python:** 3.11+
**Database:** SQLite via `aiosqlite` (FTS5 virtual table for memory search)
**Key integrations:** OpenRouter (LLM), Tavily / GitHub / HuggingFace / StackOverflow / arXiv / Wikipedia (search), Obsidian vault (local filesystem), croniter (scheduling)

---

## Repository Structure

```
src/bot/
├── main.py              # Entry point — wires all components and starts polling
├── config/              # Settings (pydantic-settings), agent definitions, constants
│   ├── config.py        # load_settings() — merges .env + config.yaml
│   ├── constants.py     # All magic numbers and shared strings
│   ├── agents.py        # AgentProfile definitions (default, explanatory, math_tutor, researcher)
│   └── agent_registry.py# get_agent(), get_default_agent(), list_agents()
├── domain/              # Pure Python domain layer — no I/O, no framework imports
│   ├── models/          # Dataclasses: Message, Conversation, Tool, AgentProfile, Note, etc.
│   ├── exceptions.py    # BotError, VaultError, LLMError, ChannelError, WebSearchError
│   └── protocols.py     # Structural protocols: TelegramEntity, MonitorResolver, SupportsGetEntity
├── handlers/            # aiogram routers (thin layer — delegate to services)
│   ├── commands.py      # All slash commands
│   ├── messages.py      # Catch-all message handler (streaming LLM response)
│   ├── channels.py      # Telethon real-time monitor event handler
│   └── middleware.py    # OwnerOnlyMiddleware
├── infrastructure/      # External adapters — I/O only, no business logic
│   ├── openrouter/      # OpenRouter HTTP client (streaming completions)
│   ├── search/          # Search clients: tavily, github, huggingface, stackoverflow, arxiv, wikipedia
│   ├── storage/         # monitor_storage.py — SQLite CRUD for channel_monitors table
│   ├── telethon/        # Telethon client factory
│   └── scheduler_core.py# Thread-based PersistentScheduler with JSON job file
├── prompts/             # LLM system prompt strings — pure text, no logic
├── services/            # Core business logic
│   ├── llm.py           # LLMService — tool-calling loop, streaming, agent orchestration
│   ├── conversation.py  # ConversationManager — per-user session, history, model, agent
│   ├── memory.py        # MemoryStore — SQLite FTS5 long-term memory
│   ├── vault.py         # VaultService — Obsidian markdown CRUD + full-text search
│   ├── channels.py      # ChannelService — Telethon message fetch/search with retry
│   ├── monitors.py      # MonitorService — monitor setup, pending-add flow, resolution
│   ├── scheduler.py     # BotSchedulerService — bridges thread scheduler with async bot loop
│   ├── deep_research.py # DeepResearchService — multi-cycle research loop (run/judge/synthesize)
│   ├── web_search_router.py # Routes queries to the best search source by keyword
│   ├── health.py        # HealthService — /status report
│   └── formatting.py    # split_for_telegram() — chunks long text for Telegram limits
├── shared/              # Cross-cutting utilities
│   ├── agents/          # registry.py — re-exports agent_registry functions
│   └── decorators.py    # enforce_timeout, retry_with_backoff
└── tools/               # LLM tool definitions (schema + sync stub)
    ├── registry.py      # ToolRegistry — register(), execute(), to_openrouter_schema()
    ├── vault_tools.py   # Vault tool schemas + build_vault_async_tools()
    ├── channel_tools.py # Channel tool schemas
    ├── web_tools.py     # Web search tool schema
    ├── memory_tools.py  # Memory tool schemas
    └── scheduler_tools.py # Scheduler tool schemas + executor builders

scripts/
└── auth_telethon.py     # One-time Telethon session authentication

tests/
├── unit/                # Unit tests (all async, pytest-asyncio)
└── *.py                 # Legacy integration-style tests

config.example.yaml      # Template for config.yaml
.env.example             # Template for .env secrets
Makefile                 # dev commands (test, lint, docker)
Dockerfile               # Multi-stage Python 3.12-slim build
```

---

## Architecture & Patterns

**Layering:** `domain` → `config` → `services` → `infrastructure` → `handlers`

- Business logic lives exclusively in `services/`. Handlers are thin — they parse Telegram input and call a service method.
- `domain/` is framework-free. No aiogram, no aiosqlite, no httpx.
- `infrastructure/` is I/O-only. No business decisions, no domain rules.

### Two-Tier Tool Execution (critical)

Tools that only need sync computation are registered directly in `ToolRegistry` with a sync callable. Tools that require `await` (vault, channels, web search, memory, scheduler) use a **two-step pattern**:

1. Register a sync stub in `ToolRegistry` that returns `"ASYNC_TOOL:<name>"` (the `ASYNC_TOOL_PREFIX` sentinel).
2. Register an async executor in `LLMService` via `register_async_tool(name, executor)`.

`LLMService._execute_single_tool()` detects the sentinel and delegates to the async executor. **Never register a coroutine directly as a sync tool.**

### Agent System

Each `AgentProfile` (in `config/agents.py`) has:
- `prompt` — system prompt string from `prompts/`
- `allowed_tools` — list of tool names this agent may call
- `temperature`, `max_tokens` — per-agent LLM settings

`LLMService` reads the active agent from `ConversationManager` on every message. To add a new agent: add a profile to `AGENTS` dict in `config/agents.py` and add its prompt to `prompts/`.

### Config Loading

`load_settings()` in `config/config.py` merges two sources:
- `.env` — secrets: `BOT_TOKEN`, `OPENROUTER_API_KEY`, `TAVILY_API_KEY`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `OWNER_USER_ID`
- `config.yaml` — settings: LLM model, vault path, conversation timeouts, streaming interval, scheduler TZ

`VAULT_PATH` env var overrides `config.yaml` (for Docker). Never hard-code paths — always go through `Settings`.

### Telethon (optional)

Telethon is loaded lazily and is entirely optional. If `userbot.session` is missing or expired, channel features (`fetch_messages`, `search_channel`, monitors) are disabled — the bot continues running with all other features intact.

---

## How to Run

```bash
# Install (editable + dev extras)
pip install -e ".[dev]"

# Configure
cp config.example.yaml config.yaml   # Edit: LLM model, vault path, timezone
cp .env.example .env                  # Edit: tokens, API keys, OWNER_USER_ID

# (Optional) Authenticate Telethon for channel features
python scripts/auth_telethon.py

# Run
telegram-assistant
# or
python -m bot.main
```

```bash
# Docker
make build
make run          # starts in background
make logs         # follow logs
make down         # stop + remove volumes
```

**Runtime data** is stored in `data/`: `memory.db`, `jobs.json`, `userbot.session`.

---

## How to Test

```bash
# All tests
make test
# or: pytest tests

# With coverage
make test-cov
# or: pytest tests --cov=src

# Single file
pytest tests/unit/test_llm.py -v

# Single test
pytest tests/unit/test_llm.py::test_name -v
```

Test conventions:
- All tests are `async def` — `asyncio_mode = "auto"` handles it automatically.
- Mock external I/O (OpenRouter, aiosqlite, Telethon) — never make real API calls.
- `PYTHONPATH=src` is set via `pyproject.toml`; no manual path manipulation needed.
- `tests/` ignores `ANN`, `ARG`, `S101`, `SLF001` rules — don't add type hints to test files.

---

## Code Style & Linting

```bash
make ruff_check    # ruff check .
make ruff_fix      # ruff check --fix .
make ruff_format   # ruff format .
```

**Rules:**
- Line length: **120** characters
- Quotes: **double**
- Docstring convention: **Google** (`[lint.pydocstyle] convention = "google"`)
- `ruff.toml` is the single source of truth — do not add `.flake8` or `setup.cfg`
- Docstrings are NOT required on every function (D100–D107 are ignored), but write them on public service methods
- Prompt files (`prompts/*.py`) are exempt from E501 and RUF001 — long lines and special chars are intentional
- `ERA` (eradicate) is disabled — commented-out code is allowed

---

## Git Workflow

- **Branch naming:** `feature/short-description` or `fix/issue-description`
- **Commits:** descriptive imperative ("Add vault search caching", not "Added caching")
- Run `make ruff_check` and `make test` before committing

**Critical git rule:**
- NEVER use `git add -A` or `git add .`
- Always `git add <specific files>` you modified

---

## Coding Conventions

### Naming
- Services: noun-based classes — `VaultService`, `MemoryStore`, `MonitorService`
- Tools: snake_case verb-noun — `search_vault`, `fetch_messages`, `save_memory`
- Domain models: `@dataclass(frozen=True)` for immutable records, `@dataclass` for mutable sessions
- Constants: `UPPER_SNAKE_CASE` in `config/constants.py` — no magic numbers elsewhere

### Async
- All service methods that touch I/O must be `async def`
- Sync filesystem operations are wrapped with `asyncio.to_thread()` (see `VaultService`)
- Never `asyncio.run()` inside async context

### Error Handling
- Raise domain exceptions (`VaultError`, `LLMError`, `ChannelError`) from services
- Handlers catch and convert to user-friendly messages
- Use `logger.exception()` (not `logger.error()`) to capture tracebacks

### Type Hints
- Required on all public functions (ANN rules enabled; `*args`/`**kwargs` exempted)
- Use `Protocol` for structural typing instead of ABCs where possible
- Use `TYPE_CHECKING` guard for type-only imports

---

## Critical Rules

- **NEVER** read a file partially before editing — read the whole file first.
- **ALWAYS** run `make test` after any logic change.
- **NEVER** commit `.env`, `config.yaml`, `*.session`, or `data/` files.
- **ALWAYS** register async tool executors in `main.py` via `llm.register_async_tool()` — not inside service constructors.
- **NEVER** put business logic in handlers — handlers parse input and call services only.
- **NEVER** query SQLite directly from services — use `MemoryStore` or `MonitorStore`.
- **ALWAYS** add new constants to `config/constants.py`, not inline.
- **ALWAYS** add new tools to `ALL_TOOL_NAMES` in `config/agents.py` (otherwise agents can't use them).

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `src/bot/main.py` | Entry point — wires every component; start here to trace any feature |
| `src/bot/config/constants.py` | All magic values — timeouts, limits, API bases, DB schema |
| `src/bot/config/agents.py` | Agent profiles and `ALL_TOOL_NAMES` — update when adding tools/agents |
| `src/bot/services/llm.py` | LLM orchestration — tool loop, streaming, agent switching |
| `src/bot/tools/registry.py` | Sync tool registry — schema cache, execute dispatch |
| `src/bot/domain/models/base.py` | `Message`, `Conversation`, `Role` — core message types |
| `src/bot/services/memory.py` | SQLite FTS5 long-term memory store |
| `src/bot/services/monitors.py` | Channel monitor setup (public URL + forwarded private channel) |
| `src/bot/infrastructure/openrouter/openrouter.py` | OpenRouter streaming HTTP client |
| `config.example.yaml` | Template — copy to `config.yaml` |
| `ruff.toml` | Linting/formatting configuration |

---

## Known Gotchas

- **Two-tier tool execution:** Forgetting to register an async executor via `llm.register_async_tool()` will cause the LLM to get `"ASYNC_TOOL:<name>"` as the tool result and produce garbage responses. Always wire async tools in `main.py`.

- **`ALL_TOOL_NAMES` in `config/agents.py`:** New tools must be listed here or agents with `allowed_tools=list(ALL_TOOL_NAMES)` will never call them. The LLM schema filter in `LLMService._filter_tools_schema()` silently omits unrecognised names.

- **Telethon negative IDs:** Telegram supergroups/channels have negative `chat_id` values (e.g. `-1001234567890`). The `MonitorStore` stores and queries by `int` — never treat them as strings.

- **Conversation trim preserves system messages:** `Conversation.trim()` always keeps `Role.SYSTEM` messages at the head; only user/assistant/tool messages are pruned. Don't add extra system messages mid-conversation.

- **`PROJECT_ROOT` resolution:** `constants.py` resolves the project root from `__file__` depth. If you move `constants.py`, update the `parent` chain accordingly.

- **Docker vault path:** The vault is mounted as a volume. Use `VAULT_PATH` env var to override the `config.yaml` path inside the container — hardcoding paths in `config.yaml` will break Docker deployments.

- **Scheduler timezone:** `BotSchedulerService` uses `tz_offset_hours` from `config.yaml`. cron expressions are interpreted in the configured timezone. Always confirm the TZ offset before testing scheduler features.
