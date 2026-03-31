import logging
from pathlib import Path

from bot.domain.exceptions import VaultError
from bot.domain.models import Note
from bot.shared.constants import MAX_RESULTS

logger = logging.getLogger(__name__)


class VaultService:
    """Read and write operations on a local Obsidian vault directory."""

    def __init__(self, vault_path: str, *, default_folder: str = "notes") -> None:
        self._root = Path(vault_path)
        self._default_folder = default_folder

    def search(self, query: str, *, max_results: int = MAX_RESULTS) -> list[Note]:
        """Full-text search across all markdown files in the vault."""
        if not self._root.exists():
            msg = f"Vault not found: {self._root}"
            raise VaultError(msg)

        query_lower = query.lower()
        results: list[Note] = []

        for md_file in self._root.rglob("*.md"):
            note = self._search_file(md_file, query_lower)
            if note:
                results.append(note)
                if len(results) >= max_results:
                    break

        return results

    def read(self, path: str) -> Note:
        """Read a specific note by relative path."""
        full_path = self._resolve(path)
        self._ensure_exists(full_path, path)

        content = full_path.read_text(encoding="utf-8")
        return Note(path=path, content=content)

    def list_notes(self, *, folder: str = "") -> list[str]:
        """List markdown files in a folder (or default folder)."""
        target_folder = folder or self._default_folder
        target_path = self._resolve(target_folder)

        if not target_path.exists() or not target_path.is_dir():
            msg = f"Folder not found: {target_folder}"
            raise VaultError(msg)

        return sorted(str(f.relative_to(self._root)) for f in target_path.rglob("*.md"))

    def create(self, path: str, content: str) -> Note:
        """Create a new note. Raises if it already exists."""
        full_path = self._resolve(path)
        if full_path.exists():
            msg = f"Note already exists: {path}"
            raise VaultError(msg)

        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        logger.info("Created note: %s", path)

        return Note(path=path, content=content)

    def append(self, path: str, content: str) -> Note:
        """Append content to an existing note."""
        full_path = self._resolve(path)
        self._ensure_exists(full_path, path)

        with full_path.open("a", encoding="utf-8") as f:
            f.write(f"\n{content}")

        updated = full_path.read_text(encoding="utf-8")
        logger.info("Appended to note: %s", path)

        return Note(path=path, content=updated)

    def _resolve(self, path: str) -> Path:
        """Resolve relative path to absolute, preventing path traversal."""
        resolved = (self._root / path).resolve()
        if not str(resolved).startswith(str(self._root.resolve())):
            msg = f"Path traversal denied: {path}"
            raise VaultError(msg)
        return resolved

    def _search_file(self, file_path: Path, query_lower: str) -> Note | None:
        """Check a single file for the query and return a Note if matched."""
        content = self._safe_read_text(file_path)
        if not content or query_lower not in content.lower():
            return None

        rel_path = str(file_path.relative_to(self._root))
        snippet = self._snippet(content, query_lower)
        return Note(path=rel_path, content=snippet)

    @staticmethod
    def _ensure_exists(full_path: Path, original_path: str) -> None:
        """Verify that a file exists, raising VaultError if not."""
        if not full_path.exists():
            msg = f"Note not found: {original_path}"
            raise ValueError(msg)

    @staticmethod
    def _safe_read_text(file_path: Path) -> str | None:
        """Safely read text from a file, returning None on OS errors."""
        try:
            return file_path.read_text(encoding="utf-8")
        except OSError:
            return None

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
