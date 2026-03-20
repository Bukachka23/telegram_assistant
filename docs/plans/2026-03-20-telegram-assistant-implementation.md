# Telegram Assistant Bot — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a personal Telegram bot with LLM streaming, Obsidian vault tools, and channel monitoring.

**Architecture:** Clean layered design (domain → services → infrastructure → handlers) with aiogram 3.26 for bot, Telethon for channel parsing, OpenRouter for LLM with tool calling, and sendMessageDraft for real-time streaming.

**Tech Stack:** Python 3.11+, aiogram 3.26, Telethon, httpx, Pydantic v2, pyyaml, python-dotenv

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `config.example.yaml`
- Create: `README.md`
- Create: all `__init__.py` files for package structure

**Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "telegram-assistant"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "aiogram>=3.26",
    "telethon>=1.42",
    "httpx>=0.27",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0",
    "aiofiles>=23.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.24", "pytest-cov>=5.0", "ruff>=0.4"]

[project.scripts]
telegram-assistant = "bot.main:main"

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "UP", "B"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

**Step 2: Create .gitignore, config.example.yaml, README.md**

**Step 3: Create all package directories and __init__.py files**

```
src/bot/__init__.py
src/bot/domain/__init__.py
src/bot/services/__init__.py
src/bot/infrastructure/__init__.py
src/bot/handlers/__init__.py
src/bot/tools/__init__.py
tests/__init__.py
tests/unit/__init__.py
```

**Step 4: Install dependencies**

Run: `pip install -e ".[dev]"`

**Step 5: Commit**

```bash
git init && git add -A && git commit -m "chore: project scaffolding"
```

---

### Task 2: Domain Layer — Models & Exceptions

**Files:**
- Create: `src/bot/domain/models.py`
- Create: `src/bot/domain/exceptions.py`

Domain models: Message, Conversation, Note, ChannelFilter, ToolCall, ToolResult.
Custom exceptions: VaultError, LLMError, ChannelError.

**Step 1: Write tests for domain models**

Test: `tests/unit/test_models.py`

**Step 2: Implement models and exceptions**

**Step 3: Run tests, commit**

---

### Task 3: Configuration

**Files:**
- Create: `src/bot/config.py`
- Create: `.env` (template)

Pydantic Settings model loading .env + config.yaml. Validated at import time.

**Step 1: Write test for config loading**

Test: `tests/unit/test_config.py`

**Step 2: Implement config.py**

**Step 3: Run tests, commit**

---

### Task 4: Infrastructure — OpenRouter Client

**Files:**
- Create: `src/bot/infrastructure/openrouter.py`

Async httpx client: streaming chat completions, tool call parsing, SSE chunk processing.

**Step 1: Write tests (mocked httpx)**

Test: `tests/unit/test_openrouter.py`

**Step 2: Implement OpenRouter client**

**Step 3: Run tests, commit**

---

### Task 5: Infrastructure — Telethon Client

**Files:**
- Create: `src/bot/infrastructure/telethon_client.py`

Telethon userbot client factory. Session management. Shared with channel handlers.

**Step 1: Implement Telethon client setup**

**Step 2: Commit**

---

### Task 6: Services — Conversation Manager

**Files:**
- Create: `src/bot/services/conversation.py`

In-memory session store. Timeout-based cleanup. Add/get messages per user.

**Step 1: Write tests**

Test: `tests/unit/test_conversation.py`

**Step 2: Implement conversation service**

**Step 3: Run tests, commit**

---

### Task 7: Services — Vault Service

**Files:**
- Create: `src/bot/services/vault.py`

Read/write/search/list operations on local Obsidian vault directory.

**Step 1: Write tests (using tmp_path fixture)**

Test: `tests/unit/test_vault.py`

**Step 2: Implement vault service**

**Step 3: Run tests, commit**

---

### Task 8: Tools — Registry + Vault Tools + Channel Tools

**Files:**
- Create: `src/bot/tools/registry.py`
- Create: `src/bot/tools/vault_tools.py`
- Create: `src/bot/tools/channel_tools.py`

Tool registry maps name → callable + OpenRouter JSON schema. Vault and channel tools registered.

**Step 1: Write tests for registry**

Test: `tests/unit/test_tools.py`

**Step 2: Implement registry, vault tools, channel tools**

**Step 3: Run tests, commit**

---

### Task 9: Services — LLM Orchestration

**Files:**
- Create: `src/bot/services/llm.py`

Orchestrates: build prompt → call OpenRouter → handle tool loop → yield streamed text.

**Step 1: Write tests (mocked OpenRouter client)**

Test: `tests/unit/test_llm.py`

**Step 2: Implement LLM service**

**Step 3: Run tests, commit**

---

### Task 10: Services — Channel Service

**Files:**
- Create: `src/bot/services/channels.py`

Channel monitoring config, on-demand message fetching, keyword matching.

**Step 1: Implement channel service**

**Step 2: Commit**

---

### Task 11: Handlers — Commands + Messages + Channels

**Files:**
- Create: `src/bot/handlers/commands.py`
- Create: `src/bot/handlers/messages.py`
- Create: `src/bot/handlers/channels.py`

aiogram routers: auth middleware, command handlers, message→LLM pipeline with streaming, Telethon channel event handlers.

**Step 1: Implement auth middleware**

**Step 2: Implement command handlers**

**Step 3: Implement message handler with streaming**

**Step 4: Implement channel event handlers**

**Step 5: Commit**

---

### Task 12: Main Entry Point

**Files:**
- Create: `src/bot/main.py`

Starts aiogram polling + Telethon client on shared asyncio loop. Graceful shutdown.

**Step 1: Implement main.py**

**Step 2: Manual smoke test**

**Step 3: Commit**

---
