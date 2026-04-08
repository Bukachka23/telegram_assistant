# Telegram Assistant Bot — Design Document

**Date**: 2026-03-20
**Status**: Approved

## Overview

A personal Telegram bot running on Raspberry Pi 5 that provides LLM-powered assistance with Obsidian vault integration and public channel monitoring.

## Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Bot framework | aiogram 3.26 | Telegram Bot API, polling mode |
| Channel client | Telethon | Userbot for reading public channels |
| LLM provider | OpenRouter (httpx) | Any model, tool calling, streaming |
| Streaming | `sendMessageDraft` | Real-time token display |
| Vault sync | Syncthing (external) | Bidirectional MacBook ↔ Pi sync |
| Config validation | Pydantic | Typed settings from .env + config.yaml |

## Architecture

Clean layered design. Dependencies point inward only.

```
┌─────────────────────────────────────┐
│  Interfaces (Telegram handlers)     │  ← aiogram routers + Telethon events
├─────────────────────────────────────┤
│  Application (Services)             │  ← LLM, Vault, Channel, Conversation
├─────────────────────────────────────┤
│  Domain (Models & Types)            │  ← Pydantic models, dataclasses, enums
├─────────────────────────────────────┤
│  Infrastructure (External I/O)      │  ← OpenRouter client, filesystem, Telethon
└─────────────────────────────────────┘
```

Single asyncio event loop shared by aiogram and Telethon.

## Project Structure

```
telegram-assistant/
├── pyproject.toml
├── README.md
├── .env                          # Secrets (gitignored)
├── config.yaml                   # Settings (committed)
├── config.example.yaml           # Template
├── .gitignore
├── src/
│   └── bot/
│       ├── __init__.py
│       ├── main.py               # Entry point: starts both clients
│       ├── config.py             # Loads .env + config.yaml → typed Settings
│       │
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── models.py         # Message, Conversation, Note, ChannelFilter
│       │   └── exceptions.py     # Custom domain exceptions
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── llm.py            # LLM orchestration + tool execution loop
│       │   ├── vault.py          # Obsidian vault read/write
│       │   ├── channels.py       # Channel monitoring + on-demand queries
│       │   └── conversation.py   # Session memory management
│       │
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   ├── openrouter.py     # httpx client for OpenRouter API
│       │   └── telethon_client.py # Telethon userbot setup
│       │
│       ├── handlers/
│       │   ├── __init__.py
│       │   ├── commands.py       # /start, /model, /vault, /monitor, /clear
│       │   ├── messages.py       # Free-text → LLM pipeline + streaming
│       │   └── channels.py       # Telethon event handlers for monitoring
│       │
│       └── tools/
│           ├── __init__.py
│           ├── registry.py       # Tool registry: name → callable mapping
│           ├── vault_tools.py    # search_vault, read_note, list_notes, create_note, append_note
│           └── channel_tools.py  # fetch_messages, search_channel
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── unit/
        ├── test_vault.py
        ├── test_conversation.py
        └── test_llm.py
```

## Data Flow — User Message

```
User message
  → handlers/messages.py (auth check, get session)
  → services/llm.py (build messages array, send to OpenRouter)
  → infrastructure/openrouter.py (POST streaming request)
  → services/llm.py (process streamed chunks)
    → if tool_call: execute tool → append result → call LLM again (loop)
    → if text: stream to Telegram via sendMessageDraft
  → handlers/messages.py (sendMessageDraft chunks, then sendMessage to finalize)
  → conversation session updated
```

### Streaming Detail

OpenRouter streams SSE chunks. As text accumulates, the bot calls `sendMessageDraft` every ~150ms (configurable) with the growing text. Telegram animates the transition. `sendMessage` finalizes when stream ends.

### Tool Execution Loop

1. LLM responds with `tool_calls` → execute each → append results
2. Call LLM again with tool results
3. Repeat until LLM responds with text
4. Stream final text to user

## Channel Monitoring

### Real-time (background)

Telethon event handlers watch configured channels. Messages matching keywords are forwarded to owner.

```yaml
channels:
  monitor:
    - username: "@python_news"
      keywords: ["asyncio", "pydantic"]
    - username: "@ai_news"
      keywords: ["claude", "llm"]
```

### On-demand (via LLM tools)

User asks natural language question → LLM calls `fetch_messages` or `search_channel` tools → summarizes results.

## Obsidian Vault Tools

| Tool | Description |
|------|-------------|
| `search_vault(query)` | Full-text search across vault notes |
| `read_note(path)` | Read a specific note's content |
| `list_notes(folder)` | List notes in a folder |
| `create_note(path, content)` | Create a new note |
| `append_note(path, content)` | Append to existing note |

Vault path configured in `config.yaml`. Syncthing keeps it in sync with MacBook.

## Configuration

### .env (secrets, gitignored)

```env
BOT_TOKEN=...
OPENROUTER_API_KEY=sk-or-...
TELEGRAM_API_ID=...
TELEGRAM_API_HASH=...
OWNER_USER_ID=...
```

### config.yaml (settings, committed)

```yaml
llm:
  default_model: "anthropic/claude-sonnet-4"
  max_tokens: 4096
  temperature: 0.7

vault:
  path: "/home/.pi/obsidian-vault"
  default_folder: "notes"

conversation:
  session_timeout_minutes: 30
  max_history_messages: 50

streaming:
  draft_interval_ms: 150
  min_chunk_chars: 20

channels:
  monitor: []
```

Both load into a single `Settings` Pydantic model. Validated at startup.

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/model` | Show current model |
| `/model <name>` | Switch model |
| `/monitor` | List active monitors |
| `/monitor add @ch kw1, kw2` | Add monitor |
| `/monitor remove @ch` | Remove monitor |
| `/vault search <query>` | Search vault |
| `/clear` | Clear conversation history |

Everything else goes through natural language → LLM.

## Security

- Single owner: middleware checks `from_user.id == OWNER_USER_ID`
- Unauthorized users silently ignored
- Telethon session file stored securely on Pi
- No sensitive data in config.yaml (committed to git)

## Deployment

- Raspberry Pi 5, polling mode (no webhooks needed)
- Syncthing for vault sync with MacBook
- Single asyncio process, no containers
