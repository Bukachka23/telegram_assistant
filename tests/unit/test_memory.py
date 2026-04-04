"""Tests for MemoryStore and memory tools."""

from collections.abc import AsyncGenerator

import pytest

from bot.services.memory import MemoryStore
from bot.tools.memory_tools import register_memory_tools
from bot.tools.registry import ToolRegistry


@pytest.fixture
async def store(tmp_path) -> AsyncGenerator[MemoryStore, None]:
    db_path = str(tmp_path / "memory.db")
    s = MemoryStore(db_path)
    await s.init()
    yield s
    await s.close()


@pytest.mark.asyncio
async def test_init_creates_missing_parent_directory(tmp_path) -> None:
    db_path = tmp_path / "nested" / "memory.db"
    store = MemoryStore(str(db_path))

    await store.init()

    assert db_path.exists()
    await store.close()


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
        assert tool is not None
        assert "fact" in tool.parameters["required"]

    def test_schema_recall_memory(self, registry: ToolRegistry):
        tool = registry.get("recall_memory")
        assert tool is not None
        assert "query" in tool.parameters["required"]
