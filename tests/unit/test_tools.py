"""Tests for tool registry and vault tools."""

from pathlib import Path

import pytest

from bot.services.vault import VaultService
from bot.tools.channel_tools import register_channel_tools
from bot.tools.registry import ToolRegistry
from bot.tools.vault_tools import register_vault_tools


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
    register_vault_tools(reg, vault)
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
    def test_search_vault(self, registry: ToolRegistry):
        result = registry.execute("search_vault", {"query": "Python"})
        assert "python.md" in result

    def test_search_vault_no_results(self, registry: ToolRegistry):
        result = registry.execute("search_vault", {"query": "nonexistent_xyz"})
        assert "No notes found" in result

    def test_read_note(self, registry: ToolRegistry):
        result = registry.execute("read_note", {"path": "notes/python.md"})
        assert "Decorators" in result

    def test_list_notes(self, registry: ToolRegistry):
        result = registry.execute("list_notes", {})
        assert "python.md" in result
        assert "rust.md" in result

    def test_create_note(self, registry: ToolRegistry):
        result = registry.execute(
            "create_note",
            {"path": "notes/new.md", "content": "# New"},
        )
        assert "Created" in result

    def test_append_note(self, registry: ToolRegistry):
        result = registry.execute(
            "append_note",
            {"path": "notes/python.md", "content": "## Extra"},
        )
        assert "Appended" in result

    def test_error_handling(self, registry: ToolRegistry):
        result = registry.execute("read_note", {"path": "missing.md"})
        assert "Error" in result


class TestChannelToolPlaceholders:
    def test_fetch_messages_is_async_placeholder(self, registry: ToolRegistry):
        result = registry.execute("fetch_messages", {"channel": "@test"})
        assert result.startswith("ASYNC_TOOL:")

    def test_search_channel_is_async_placeholder(self, registry: ToolRegistry):
        result = registry.execute(
            "search_channel", {"channel": "@test", "query": "q"}
        )
        assert result.startswith("ASYNC_TOOL:")
