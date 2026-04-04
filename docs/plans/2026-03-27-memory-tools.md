yes,# Memory Tools Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add persistent long-term memory to the bot via `save_memory` and `recall_memory` tools backed by SQLite.

**Architecture:** Memory is two tools registered in ToolRegistry. `save_memory` stores a fact with category/keywords. `recall_memory` does FTS5 full-text search over stored facts. SQLite is the storage engine — embedded, zero-config, stdlib. The LLM decides when to save and when to recall based on system prompt instructions.

**Tech Stack:** SQLite3 (stdlib), aiosqlite (async wrapper), existing ToolRegistry pattern.

---

### Task 1: Add aiosqlite dependency

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add aiosqlite to dependencies**

In `pyproject.toml`, add `"aiosqlite>=0.20"` to the `dependencies` list.

**Step 2: Install**

Run: `pip install -e .` (local) or rebuild Docker image.

**Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "feat(memory): add aiosqlite dependency"
```

---

### Task 2: Create MemoryStore service

**Files:**
- Create: `src/bot/services/memory.py`
- Test: `tests/unit/test_memory.py`

**Step 1: Write the failing tests**

```python
"""Tests for MemoryStore."""

import pytest

from bot.services.memory import MemoryStore


@pytest.fixture
async def store(tmp_path) -> MemoryStore:
    db_path = str(tmp_path / "memory.db")
    s = MemoryStore(db_path)
    await s.init()
    yield s
    await s.close()


class TestSave:
    async def test_save_and_recall(self, store: MemoryStore):
        await store.save(fact="User prefers dark mode", category="preference")
        results = await store.recall("dark mode")
        assert len(results) >= 1
        assert "dark mode" in results[0]["fact"]

    async def test_save_with_keywords(self, store: MemoryStore):
        await store.save(
            fact="Meeting with Alex on Friday",
            category="event",
        )
        results = await store.recall("Alex")
        assert len(results) >= 1

    async def test_recall_no_results(self, store: MemoryStore):
        results = await store.recall("nonexistent topic xyz")
        assert results == []

    async def test_recall_respects_limit(self, store: MemoryStore):
        for i in range(10):
            await store.save(fact=f"Python tip number {i}", category="knowledge")
        results = await store.recall("Python", limit=3)
        assert len(results) == 3

    async def test_recall_returns_newest_first(self, store: MemoryStore):
        await store.save(fact="Old fact about cats", category="knowledge")
        await store.save(fact="New fact about cats", category="knowledge")
        results = await store.recall("cats")
        assert results[0]["fact"] == "New fact about cats"

    async def test_list_recent(self, store: MemoryStore):
        await store.save(fact="Fact one", category="preference")
        await store.save(fact="Fact two", category="event")
        results = await store.list_recent(limit=5)
        assert len(results) == 2
        assert results[0]["fact"] == "Fact two"
```

**Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=. pytest tests/unit/test_memory.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'bot.services.memory'`

**Step 3: Write the implementation**

```python
"""Persistent memory store backed by SQLite FTS5."""

import logging
import sqlite3
from datetime import UTC, datetime

import aiosqlite

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fact TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
USING fts5(fact, category, content=memories, content_rowid=id);

CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
    INSERT INTO memories_fts(rowid, fact, category)
    VALUES (new.id, new.fact, new.category);
END;

CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, fact, category)
    VALUES ('delete', old.id, old.fact, old.category);
END;
"""


class MemoryStore:
    """SQLite-backed long-term memory with full-text search."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def init(self) -> None:
        """Open database and create schema."""
        self._db = await aiosqlite.connect(self._db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(_SCHEMA)
        await self._db.commit()
        count = await self._count()
        logger.info("Memory store ready: %d memories in %s", count, self._db_path)

    async def close(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()

    async def save(self, fact: str, category: str = "") -> int:
        """Save a fact. Returns the row id."""
        now = datetime.now(UTC).isoformat()
        async with self._db.execute(
            "INSERT INTO memories (fact, category, created_at) VALUES (?, ?, ?)",
            (fact, category, now),
        ) as cursor:
            row_id = cursor.lastrowid
        await self._db.commit()
        logger.info("Memory saved [%d]: %s", row_id, fact[:80])
        return row_id

    async def recall(self, query: str, *, limit: int = 5) -> list[dict]:
        """Full-text search for memories matching query. Newest first."""
        async with self._db.execute(
            """
            SELECT m.id, m.fact, m.category, m.created_at
            FROM memories_fts fts
            JOIN memories m ON m.id = fts.rowid
            WHERE memories_fts MATCH ?
            ORDER BY m.id DESC
            LIMIT ?
            """,
            (query, limit),
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def list_recent(self, *, limit: int = 10) -> list[dict]:
        """Return the most recent memories."""
        async with self._db.execute(
            "SELECT id, fact, category, created_at FROM memories ORDER BY id DESC LIMIT ?",
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def _count(self) -> int:
        async with self._db.execute("SELECT COUNT(*) FROM memories") as cursor:
            row = await cursor.fetchone()
        return row[0] if row else 0
```

**Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=. pytest tests/unit/test_memory.py -v`
Expected: All 7 PASS

**Step 5: Commit**

```bash
git add src/bot/services/memory.py tests/unit/test_memory.py
git commit -m "feat(memory): add MemoryStore with SQLite FTS5"
```

---

### Task 3: Create memory tools

**Files:**
- Create: `src/bot/tools/memory_tools.py`
- Modify: `tests/unit/test_memory.py` (add tool registration tests)

**Step 1: Write the failing tests**

Append to `tests/unit/test_memory.py`:

```python
from bot.tools.memory_tools import register_memory_tools
from bot.tools.registry import ToolRegistry


@pytest.fixture
def registry() -> ToolRegistry:
    reg = ToolRegistry()
    register_memory_tools(reg)
    return reg


class TestMemoryToolRegistration:
    def test_tools_registered(self, registry: ToolRegistry):
        assert "save_memory" in registry.names
        assert "recall_memory" in registry.names

    def test_both_are_async_placeholders(self, registry: ToolRegistry):
        save_result = registry.execute("save_memory", {"fact": "test"})
        assert save_result.startswith("ASYNC_TOOL:")
        recall_result = registry.execute("recall_memory", {"query": "test"})
        assert recall_result.startswith("ASYNC_TOOL:")

    def test_schema_save_memory(self, registry: ToolRegistry):
        tool = registry.get("save_memory")
        assert "fact" in tool.parameters["required"]

    def test_schema_recall_memory(self, registry: ToolRegistry):
        tool = registry.get("recall_memory")
        assert "query" in tool.parameters["required"]
```

**Step 2: Run to verify fail**

Run: `PYTHONPATH=. pytest tests/unit/test_memory.py::TestMemoryToolRegistration -v`
Expected: FAIL

**Step 3: Write the implementation**

```python
from bot.config.constants import ASYNC_TOOL_PREFIX
from bot.tools.registry import ToolRegistry


def register_memory_tools(registry: ToolRegistry) -> None:
    """Register memory tools with the registry."""
    registry.register(
        name="save_memory",
        description=(
            "Save an important fact to long-term memory. Use when the user shares "
            "preferences, makes decisions, mentions contacts, schedules events, or "
            "explicitly asks you to remember something. Write the fact as a clear, "
            "self-contained statement."
        ),
        parameters={
            "type": "object",
            "properties": {
                "fact": {
                    "type": "string",
                    "description": (
                        "A clear, self-contained factual statement. "
                        "Include names, dates, and context. "
                        "Bad: 'He likes it'. Good: 'User prefers dark mode in all apps'."
                    ),
                },
                "category": {
                    "type": "string",
                    "description": "Category: preference, decision, contact, event, fact, or project",
                },
            },
            "required": ["fact"],
        },
        fn=lambda **_: f"{ASYNC_TOOL_PREFIX}save_memory",
    )

    registry.register(
        name="recall_memory",
        description=(
            "Search long-term memory for relevant facts from past conversations. "
            "Use when the user references past context, says 'remember', 'last time', "
            "'we discussed', or asks something that might relate to earlier conversations."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search terms to find relevant memories",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default 5)",
                },
            },
            "required": ["query"],
        },
        fn=lambda **_: f"{ASYNC_TOOL_PREFIX}recall_memory",
    )
```

**Step 4: Run tests**

Run: `PYTHONPATH=. pytest tests/unit/test_memory.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/bot/tools/memory_tools.py tests/unit/test_memory.py
git commit -m "feat(memory): add save_memory and recall_memory tools"
```

---

### Task 4: Wire memory into main.py and agents

**Files:**
- Modify: `src/bot/main.py`
- Modify: `src/bot/shared/agents/configs.py`
- Modify: `src/bot/shared/config.py`

**Step 1: Add memory config to Settings**

In `src/bot/shared/config.py`, add to `Settings`:
```python
    memory_db_path: str = "data/memory.db"
```

**Step 2: Add tools to ALL_TOOL_NAMES**

In `src/bot/shared/agents/configs.py`, add to `ALL_TOOL_NAMES`:
```python
    "save_memory",
    "recall_memory",
```

**Step 3: Wire in main.py**

Add import:
```python
from bot.services.memory import MemoryStore
from bot.tools.memory_tools import register_memory_tools
```

After infrastructure section, add:
```python
    # --- Memory ---
    memory = MemoryStore(db_path=settings.memory_db_path)
    await memory.init()
```

After tool registration:
```python
    register_memory_tools(registry)
```

After LLM service creation, register async executors:
```python
    llm.register_async_tool("save_memory", memory.save)
    llm.register_async_tool("recall_memory", _recall_formatter(memory))
```

Add helper (before `run()`):
```python
async def _format_recall(memory: MemoryStore, query: str, limit: int = 5) -> str:
    results = await memory.recall(query, limit=limit)
    if not results:
        return f"No memories found for '{query}'"
    lines = [f"Found {len(results)} memory(ies):"]
    for r in results:
        line = f"- [{r['category'] or 'general'}] {r['fact']}"
        if r.get("created_at"):
            line += f" (saved: {r['created_at'][:10]})"
        lines.append(line)
    return "\n".join(lines)


def _recall_formatter(memory: MemoryStore):
    async def executor(query: str, limit: int = 5) -> str:
        return await _format_recall(memory, query, limit)
    return executor
```

Add `save_memory` formatting — the default `memory.save` returns an int (row_id), but async executor must return a string. Create a wrapper:
```python
def _save_formatter(memory: MemoryStore):
    async def executor(fact: str, category: str = "") -> str:
        row_id = await memory.save(fact, category)
        return f"Memory saved (id={row_id})"
    return executor
```

Use: `llm.register_async_tool("save_memory", _save_formatter(memory))`

In finally block, add:
```python
        await memory.close()
```

**Step 4: Run full test suite**

Run: `PYTHONPATH=. pytest tests/unit/ -v`
Expected: All pass

**Step 5: Commit**

```bash
git add src/bot/main.py src/bot/shared/agents/agents.py src/bot/shared/config.py
git commit -m "feat(memory): wire memory store and tools into bot"
```

---

### Task 5: Update system prompt

**Files:**
- Modify: `src/bot/shared/prompt/system_prompt.py`

**Step 1: Add memory section to system prompt**

Add a new tool category in the `## Tools` section:
```
**Long-term memory** — save and recall facts across conversations
```

Add a new subsection after Web Search:

```
### Memory (save_memory, recall_memory)
Your long-term memory across conversations. This is how you remember things
between sessions.

**save_memory — when to use:**
- User shares a preference: "I like dark mode", "I'm vegetarian"
- User makes a decision: "Let's go with Option A"
- User mentions contacts: "Alex is my teammate, he handles backend"
- User shares plans/events: "I have a demo on Friday"
- User explicitly asks: "remember this", "keep this in mind"
- Important project context: "We're migrating from Django to FastAPI"
- Do NOT save: chitchat, temporary questions, tool outputs, things
  already in the vault

**recall_memory — when to use:**
- User references past conversations: "like we discussed", "remember when"
- User mentions a topic you may have saved context about
- Start of a new session when the user continues a previous topic
- When you sense a question connects to something from before
- When the user asks "what do you know about me" or "what do you remember"

**Writing good facts for save_memory:**
- Self-contained: "User prefers VS Code over PyCharm" not "He prefers it"
- Include names and dates: "Meeting with Alex scheduled for 2026-04-01"
- One fact per save — don't combine unrelated things
```

**Step 2: Run tests**

Run: `PYTHONPATH=. pytest tests/unit/ -v`
Expected: All pass

**Step 3: Commit**

```bash
git add src/bot/shared/prompts/system_prompt.py
git commit -m "feat(memory): update system prompt with memory tool guidance"
```

---

### Task 6: Add data directory to Docker setup

**Files:**
- Modify: `docker-compose.yml` (volume already mapped: `./data:/app/data`)
- Modify: `.gitignore`
- Modify: `.dockerignore`

**Step 1: Verify Docker volume**

The `docker-compose.yml` already maps `./data:/app/data`. The default `memory_db_path` is `data/memory.db`, so this works out of the box.

**Step 2: Add data/memory.db to .gitignore**

```
data/memory.db
data/memory.db-wal
data/memory.db-shm
```

**Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: ignore memory database files"
```

---

**Summary of new/modified files:**

| File | Action |
|------|--------|
| `pyproject.toml` | Add `aiosqlite` dependency |
| `src/bot/services/memory.py` | **New** — MemoryStore (SQLite + FTS5) |
| `src/bot/tools/memory_tools.py` | **New** — save_memory + recall_memory tool defs |
| `src/bot/shared/config.py` | Add `memory_db_path` setting |
| `src/bot/shared/agents/configs.py` | Add memory tools to ALL_TOOL_NAMES |
| `src/bot/shared/prompt/system_prompt.py` | Add memory usage guidance |
| `src/bot/main.py` | Wire MemoryStore, register tools + async executors |
| `.gitignore` | Ignore memory.db files |
| `tests/unit/test_memory.py` | **New** — store + tool registration tests |
