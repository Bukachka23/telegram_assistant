"""Tests for vault service."""

from pathlib import Path

import pytest

from bot.domain.exceptions import VaultError
from bot.services.vault import VaultService


@pytest.fixture
def vault(tmp_path: Path) -> VaultService:
    """Create a vault with sample notes."""
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "python.md").write_text("# Python\nDecorators and async patterns")
    (notes / "rust.md").write_text("# Rust\nOwnership and borrowing")

    projects = tmp_path / "projects"
    projects.mkdir()
    (projects / "bot.md").write_text("# Bot Project\nTelegram assistant with Python")

    return VaultService(str(tmp_path), default_folder="notes")


class TestSearch:
    async def test_finds_matching_notes(self, vault: VaultService):
        results = await vault.search("python")
        assert len(results) >= 1
        paths = [r.path for r in results]
        assert any("python.md" in p for p in paths)

    async def test_case_insensitive(self, vault: VaultService):
        results = await vault.search("PYTHON")
        assert len(results) >= 1

    async def test_no_results(self, vault: VaultService):
        results = await vault.search("nonexistent_xyz")
        assert results == []

    async def test_max_results(self, vault: VaultService):
        results = await vault.search("a", max_results=1)
        assert len(results) <= 1

    async def test_missing_vault_raises(self, tmp_path: Path):
        svc = VaultService(str(tmp_path / "missing"))
        with pytest.raises(VaultError, match="Vault not found"):
            await svc.search("test")


class TestRead:
    async def test_read_existing(self, vault: VaultService):
        note = await vault.read("notes/python.md")
        assert "Decorators" in note.content
        assert note.name == "python.md"

    async def test_read_missing_raises(self, vault: VaultService):
        with pytest.raises(VaultError, match="not found"):
            await vault.read("notes/missing.md")


class TestListNotes:
    async def test_list_default_folder(self, vault: VaultService):
        notes = await vault.list_notes()
        assert len(notes) == 2
        assert "notes/python.md" in notes

    async def test_list_specific_folder(self, vault: VaultService):
        notes = await vault.list_notes(folder="projects")
        assert len(notes) == 1
        assert "projects/bot.md" in notes

    async def test_missing_folder_raises(self, vault: VaultService):
        with pytest.raises(VaultError, match="Folder not found"):
            await vault.list_notes(folder="nonexistent")


class TestCreate:
    async def test_create_new_note(self, vault: VaultService):
        note = await vault.create("notes/new.md", "# New Note\nContent")
        assert note.content == "# New Note\nContent"
        assert (await vault.read("notes/new.md")).content == "# New Note\nContent"

    async def test_create_with_subfolder(self, vault: VaultService):
        await vault.create("notes/deep/nested.md", "nested content")
        assert (await vault.read("notes/deep/nested.md")).content == "nested content"

    async def test_create_existing_raises(self, vault: VaultService):
        with pytest.raises(VaultError, match="already exists"):
            await vault.create("notes/python.md", "overwrite attempt")


class TestAppend:
    async def test_append_to_existing(self, vault: VaultService):
        await vault.append("notes/python.md", "## New Section")
        note = await vault.read("notes/python.md")
        assert "## New Section" in note.content
        assert "Decorators" in note.content  # Original preserved

    async def test_append_missing_raises(self, vault: VaultService):
        with pytest.raises(VaultError, match="not found"):
            await vault.append("notes/missing.md", "content")


class TestPathTraversal:
    async def test_traversal_blocked(self, vault: VaultService):
        with pytest.raises(VaultError, match="traversal"):
            await vault.read("../../etc/passwd")
