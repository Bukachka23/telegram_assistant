"""Obsidian vault read/write operations."""

import logging
from pathlib import Path

from bot.domain.exceptions import VaultError
from bot.domain.models import Note

logger = logging.getLogger(__name__)


class VaultService:
    """Read and write operations on a local Obsidian vault directory."""

    def __init__(self, vault_path: str, default_folder: str = "notes") -> None:
        self._root = Path(vault_path)
        self._default_folder = default_folder

    def search(self, query: str, max_results: int = 10) -> list[Note]:
        """Full-text search across all markdown files in the vault."""
        if not self._root.exists():
            raise VaultError(f"Vault not found: {self._root}")

        query_lower = query.lower()
        results: list[Note] = []

        for md_file in self._root.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
            except OSError:
                continue
            if query_lower in content.lower():
                rel = str(md_file.relative_to(self._root))
                results.append(Note(path=rel, content=self._snippet(content, query_lower)))
                if len(results) >= max_results:
                    break

        return results

    def read(self, path: str) -> Note:
        """Read a specific note by relative path."""
        full_path = self._resolve(path)
        if not full_path.exists():
            raise VaultError(f"Note not found: {path}")
        content = full_path.read_text(encoding="utf-8")
        return Note(path=path, content=content)

    def list_notes(self, folder: str = "") -> list[str]:
        """List markdown files in a folder (or default folder)."""
        target = self._root / (folder or self._default_folder)
        if not target.exists():
            raise VaultError(f"Folder not found: {target}")
        return sorted(
            str(f.relative_to(self._root))
            for f in target.rglob("*.md")
        )

    def create(self, path: str, content: str) -> Note:
        """Create a new note. Raises if it already exists."""
        full_path = self._resolve(path)
        if full_path.exists():
            raise VaultError(f"Note already exists: {path}")
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        logger.info("Created note: %s", path)
        return Note(path=path, content=content)

    def append(self, path: str, content: str) -> Note:
        """Append content to an existing note."""
        full_path = self._resolve(path)
        if not full_path.exists():
            raise VaultError(f"Note not found: {path}")
        with open(full_path, "a", encoding="utf-8") as f:
            f.write(f"\n{content}")
        updated = full_path.read_text(encoding="utf-8")
        logger.info("Appended to note: %s", path)
        return Note(path=path, content=updated)

    def _resolve(self, path: str) -> Path:
        """Resolve relative path to absolute, preventing path traversal."""
        resolved = (self._root / path).resolve()
        if not str(resolved).startswith(str(self._root.resolve())):
            raise VaultError(f"Path traversal denied: {path}")
        return resolved

    @staticmethod
    def _snippet(content: str, query: str, context: int = 200) -> str:
        """Extract a snippet around the first match."""
        idx = content.lower().find(query)
        if idx == -1:
            return content[:context]
        start = max(0, idx - context // 2)
        end = min(len(content), idx + len(query) + context // 2)
        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet += "..."
        return snippet
