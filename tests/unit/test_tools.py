"""Tests for tool registry and vault tools."""

from pathlib import Path

import pytest

from bot.services.vault import VaultService
from bot.tools.channel_tools import register_channel_tools
from bot.tools.registry import ToolRegistry
from bot.tools.vault_tools import build_vault_async_tools, register_vault_tools


@pytest.fixture
def vault(tmp_path: Path) -> VaultService:
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "python.md").write_text("# Python\nDecorators and generators")
    (notes / "rust.md").write_text("# Rust\nOwnership model")
    return VaultService(str(tmp_path), default_folder="notes")


@pytest.fixture
def registry(vault: VaultService) -> ToolRegistry:
    reg = ToolRegistry()
    register_vault_tools(reg)
    register_channel_tools(reg)
    return reg


class TestToolRegistry:
    def test_registered_tools(self, registry: ToolRegistry):
        names = registry.names
        assert "search_vault" in names
        assert "read_note" in names
        assert "list_notes" in names
        assert "create_note" in names
        assert "append_note" in names
        assert "fetch_messages" in names
        assert "search_channel" in names

    def test_openrouter_schema(self, registry: ToolRegistry):
        schema = registry.to_openrouter_schema()
        assert len(schema) == 7
        assert all(t["type"] == "function" for t in schema)
        assert all("name" in t["function"] for t in schema)
        assert all("parameters" in t["function"] for t in schema)

    def test_unknown_tool(self, registry: ToolRegistry):
        result = registry.execute("nonexistent", {})
        assert "Error" in result

    def test_get_existing_tool(self, registry: ToolRegistry):
        tool = registry.get("search_vault")
        assert tool is not None
        assert tool.name == "search_vault"

    def test_get_missing_tool(self, registry: ToolRegistry):
        assert registry.get("missing") is None


class TestVaultToolExecution:
    """Vault tools are async — test via the async executors."""

    @pytest.fixture
    def executors(self, vault: VaultService) -> dict[str, object]:
        return build_vault_async_tools(vault)  # type: ignore

    async def test_search_vault(self, executors):
        result = await executors["search_vault"](query="Python")
        assert "python.md" in result

    async def test_search_vault_no_results(self, executors):
        result = await executors["search_vault"](query="nonexistent_xyz")
        assert "No notes found" in result

    async def test_read_note(self, executors):
        result = await executors["read_note"](path="notes/python.md")
        assert "Decorators" in result

    async def test_list_notes(self, executors):
        result = await executors["list_notes"]()
        assert "python.md" in result
        assert "rust.md" in result

    async def test_create_note(self, executors):
        result = await executors["create_note"](path="notes/new.md", content="# New")
        assert "Created" in result

    async def test_append_note(self, executors):
        result = await executors["append_note"](path="notes/python.md", content="## Extra")
        assert "Appended" in result

    async def test_error_handling(self, executors):
        with pytest.raises(Exception):
            await executors["read_note"](path="missing.md")

    def test_registry_returns_async_sentinel(self, registry: ToolRegistry):
        """Sync registry.execute returns ASYNC_TOOL: for vault tools."""
        result = registry.execute("search_vault", {"query": "test"})
        assert result.startswith("ASYNC_TOOL:")


class TestChannelToolPlaceholders:
    def test_fetch_messages_is_async_placeholder(self, registry: ToolRegistry):
        result = registry.execute("fetch_messages", {"channel": "@test"})
        assert result.startswith("ASYNC_TOOL:")

    def test_search_channel_is_async_placeholder(self, registry: ToolRegistry):
        result = registry.execute(
            "search_channel", {"channel": "@test", "query": "q"}
        )
        assert result.startswith("ASYNC_TOOL:")
