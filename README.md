# Telegram Assistant Bot

A personal Telegram bot powered by LLMs via OpenRouter. Supports streaming responses, Obsidian vault integration, Telegram channel monitoring, deep multi-cycle research, scheduled reminders, web search across multiple sources, and Telegra.ph publishing for long answers.

---

## Features

- **LLM Chat** — OpenRouter backend, any model, real-time streaming via `sendMessageDraft`
- **Agent Modes** — switch between specialized assistants (Default, Explanatory, Math Tutor, Researcher) per conversation
- **Obsidian Vault** — search, read, create, append notes via LLM tool calling
- **Deep Research** — multi-cycle research loop with judge/synthesize phases (`/deep`)
- **Web Search** — intelligent routing across Tavily, GitHub, HuggingFace, arXiv, StackOverflow, Wikipedia, Reddit
- **Channel Monitoring** — real-time keyword alerts from public and private Telegram channels
- **Scheduled Reminders** — natural-language scheduling via LLM tool (`schedule`, `list_schedules`, `remove_schedule`)
- **Persistent Memory** — save and recall notes across conversations (`save_memory`, `recall_memory`)
- **Telegra.ph Publishing** — auto-publish long responses to Telegra.ph with a preview link
- **Usage Metrics** — per-model token usage, cost, latency, and TTFB via `/stats`
- **System Health** — full status report via `/status`
- **Userbot (Telethon)** — optional userbot for private channel access and message search

---

## Requirements

- Python 3.12+
- Telegram Bot Token ([BotFather](https://t.me/botfather))
- [OpenRouter](https://openrouter.ai) API key
- Tavily API key *(optional, enables web search)*
- Telegram API ID + Hash *(optional, enables Telethon userbot for private channels)*

---

## Setup

```bash
# 1. Clone and install
pip install -e ".[dev]"

# 2. Configure secrets
cp .env.example .env
# Edit .env with your values

# 3. Configure settings
cp config.example.yaml config.yaml
# Edit config.yaml with your model, vault path, etc.

# 4. (Optional) Authenticate Telethon userbot for private channel access
python scripts/auth_telethon.py

# 5. Run
telegram-assistant
```

---

## Configuration

### `.env` — secrets

```env
BOT_TOKEN=your_telegram_bot_token
OPENROUTER_API_KEY=your_openrouter_key
TAVILY_API_KEY=your_tavily_key           # optional
TELEGRAM_API_ID=123456                   # optional, for Telethon userbot
TELEGRAM_API_HASH=abc123                 # optional, for Telethon userbot
OWNER_USER_ID=123456789                  # your Telegram user ID
```

### `config.yaml` — settings

```yaml
llm:
  default_model: "anthropic/claude-sonnet-4"
  max_tokens: 4096
  temperature: 0.7

vault:
  path: "/path/to/your/obsidian-vault"
  default_folder: "notes"

conversation:
  session_timeout_minutes: 30
  max_history_messages: 50

streaming:
  draft_interval_ms: 800        # streaming draft update interval

scheduler:
  tz_offset_hours: 2            # your UTC offset for reminders

telegraph:
  enabled: true
  threshold_chars: 8000         # publish to Telegra.ph above this length
  author_name: "Telegram Assistant"
  author_url: ""
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and command overview |
| `/agent` | Show current agent mode and available modes |
| `/agent <mode>` | Switch agent mode |
| `/assistant` | Switch to Default Assistant |
| `/explanatory` | Switch to Explanatory mode (detailed step-by-step) |
| `/math_tutor` | Switch to Math Tutor (no tools) |
| `/researcher` | Switch to Researcher mode (all tools enabled) |
| `/model` | Show current LLM model |
| `/model <name>` | Switch LLM model (e.g. `openai/gpt-4o`) |
| `/deep <question>` | Run multi-cycle deep research |
| `/telegraph` | Toggle Telegra.ph publishing for long responses |
| `/stats` | Usage stats for last 7 days |
| `/stats <n>` | Stats for last N days |
| `/stats today` | Stats for today |
| `/stats all` | All-time stats |
| `/status` | System health check |
| `/monitor` | List active channel monitors |
| `/monitor add @channel kw1, kw2` | Monitor a public channel with keywords |
| `/monitor add kw1, kw2` | Start private channel setup (then forward a message) |
| `/monitor remove @channel` | Remove a monitor |
| `/vault search <query>` | Search vault notes |
| `/clear` | Clear conversation history |

---

## Agent Modes

| Mode | Command | Description |
|------|---------|-------------|
| Default Assistant | `/assistant` | General-purpose assistant with all tools |
| Explanatory | `/explanatory` | Step-by-step explanations, lower temperature |
| Math Tutor | `/math_tutor` | Math-focused, no tools, strict reasoning |
| Researcher | `/researcher` | Multi-source research with all tools |

---

## LLM Tools

The following tools are available to agents (subject to per-agent allow-list):

| Tool | Description |
|------|-------------|
| `search_vault` | Full-text search across Obsidian vault |
| `read_note` | Read a specific vault note |
| `list_vault_folders` | List folders in the vault |
| `list_notes` | List notes in a folder |
| `create_note` | Create a new note |
| `append_note` | Append content to an existing note |
| `fetch_messages` | Fetch recent messages from a monitored channel |
| `search_channel` | Search messages in a channel |
| `web_search` | Route a query to the best search source |
| `save_memory` | Persist a memory entry to SQLite |
| `recall_memory` | Retrieve stored memory entries |
| `schedule` | Create a one-shot or recurring reminder |
| `list_schedules` | List scheduled jobs |
| `remove_schedule` | Remove a scheduled job by name |

---

## Web Search Sources

Queries are routed automatically based on keywords or explicit source prefix:

| Source | When used |
|--------|-----------|
| Tavily | General web search fallback (requires API key) |
| GitHub | Code, repositories, open-source |
| HuggingFace | Models, datasets, ML papers |
| arXiv | Research papers, academic topics |
| StackOverflow | Programming questions, debugging |
| Wikipedia | Definitions, concepts, background |
| Reddit | Community discussion, opinions |

---

## Project Structure

```
src/bot/
├── bootstrap.py              # Composition root — wires everything together
├── bootstrap_factories.py    # Infrastructure and service factory helpers
├── bootstrap_runtime.py      # Session discovery, DB open, shutdown lifecycle
├── bootstrap_wiring.py       # LLM tool wiring and dispatcher setup
├── main.py                   # Entry point
│
├── config/
│   ├── agents.py             # Agent profiles and registry
│   ├── config.py             # Settings loader (YAML + .env)
│   └── constants.py          # Shared constants
│
├── domain/
│   ├── exceptions.py         # Domain exceptions
│   ├── models/               # Pydantic data models
│   └── protocols.py          # Abstract interfaces
│
├── handlers/
│   ├── channels.py           # Telethon channel monitoring handler
│   ├── messages.py           # Streaming message handler
│   ├── middleware.py         # Owner-only middleware
│   └── commands/             # Command handlers package
│       ├── agent.py          # /agent, mode-switch commands
│       ├── commands.py       # Router setup (setup_commands)
│       ├── info.py           # /start, /model, /status, /stats, /clear, /telegraph, /vault
│       ├── monitor.py        # /monitor commands
│       ├── research.py       # /deep command
│       └── utils.py          # Shared handler helpers
│
├── infrastructure/
│   ├── openrouter/           # OpenRouter HTTP client and SSE parser
│   ├── scheduler/            # PersistentScheduler (file-backed, thread-based)
│   ├── search/               # Search clients (Tavily, GitHub, HuggingFace, arXiv, etc.)
│   ├── storage/              # SQLite stores (memory, monitors, metrics)
│   ├── telegraph/            # Telegra.ph client and HTML formatter
│   └── telethon/             # Telethon client factory
│
├── prompts/                  # System prompts for each agent mode
│
├── services/
│   ├── channels.py           # Channel message fetch and search
│   ├── conversation.py       # Conversation session and history management
│   ├── deep_research.py      # Multi-cycle research orchestration
│   ├── formatting.py         # Telegram message splitting
│   ├── health.py             # System health aggregation
│   ├── health_formatter.py   # Health report renderer
│   ├── llm.py                # LLM orchestration with streaming and tool loop
│   ├── llm_metrics.py        # Request metric emission helper
│   ├── metrics.py            # Metrics aggregation and formatting
│   ├── monitors.py           # Channel monitor management
│   ├── scheduler.py          # Bot scheduler service (bridges thread ↔ async)
│   ├── telegraph.py          # Telegra.ph publishing service
│   ├── tool_executor.py      # Sync and async tool execution
│   ├── vault.py              # Obsidian vault read/write
│   └── web_search_router.py  # Multi-source search routing
│
├── shared/
│   ├── decorators/           # cache_with_ttl, retry_with_backoff, enforce_timeout, etc.
│   └── types.py              # Shared type aliases
│
└── tools/                    # LLM tool schema registration and executors
    ├── channel_tools.py
    ├── memory_tools.py
    ├── registry.py
    ├── scheduler_tools.py
    ├── vault_tools.py
    └── web_tools.py
```

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run focused architecture suite
pytest -q tests/unit/test_llm.py tests/unit/test_commands.py tests/unit/test_health.py \
  tests/unit/test_main.py tests/unit/test_scheduler.py tests/unit/test_monitors.py \
  tests/unit/test_deep_research.py

# Lint
ruff check src tests

# Compile check
python -m compileall src/bot
```

### Tech Stack

| Layer | Library |
|-------|---------|
| Telegram bot | [aiogram 3](https://docs.aiogram.dev) |
| Telegram userbot | [Telethon](https://docs.telethon.dev) |
| LLM backend | [OpenRouter](https://openrouter.ai) via `httpx` |
| Settings | [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| Storage | [aiosqlite](https://aiosqlite.omnilib.dev) |
| Scheduling | [croniter](https://github.com/kiorky/croniter) + custom thread-based scheduler |
| HTML formatting | [mistune](https://mistune.lepture.com) |
