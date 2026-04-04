from collections.abc import Awaitable, Callable

from bot.config.constants import ASYNC_TOOL_PREFIX
from bot.services.vault import VaultService
from bot.tools.registry import ToolRegistry

AsyncToolExecutor = Callable[..., Awaitable[str]]


def register_vault_tools(registry: ToolRegistry) -> None:
    """Register all vault tool schemas with the registry."""
    async_ = lambda **_kw: ASYNC_TOOL_PREFIX  # noqa: E731

    registry.register(
        name="search_vault",
        description=(
            "Search for notes in the Obsidian vault by keyword. "
            "Returns matching note paths and snippets."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to find in notes",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default 10)",
                },
            },
            "required": ["query"],
        },
        fn=async_,
    )

    registry.register(
        name="read_note",
        description="Read the full content of a specific note by its path.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to the note",
                },
            },
            "required": ["path"],
        },
        fn=async_,
    )

    registry.register(
        name="list_vault_folders",
        description=(
            "List all immediate subdirectories inside a vault folder. "
            "Call with no arguments to see the top-level vault structure "
            "and discover available folder names before calling list_notes."
        ),
        parameters={
            "type": "object",
            "properties": {
                "folder": {
                    "type": "string",
                    "description": "Folder to inspect (empty = vault root)",
                },
            },
            "required": [],
        },
        fn=async_,
    )

    registry.register(
        name="list_notes",
        description=(
            "List all markdown notes inside a vault folder. "
            "Use list_vault_folders first if you are unsure of the exact folder name."
        ),
        parameters={
            "type": "object",
            "properties": {
                "folder": {
                    "type": "string",
                    "description": "Exact folder path as returned by list_vault_folders",
                },
            },
            "required": ["folder"],
        },
        fn=async_,
    )

    registry.register(
        name="create_note",
        description="Create a new note in the Obsidian vault.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path for the new note",
                },
                "content": {
                    "type": "string",
                    "description": "Markdown content of the note",
                },
            },
            "required": ["path", "content"],
        },
        fn=async_,
    )

    registry.register(
        name="append_note",
        description="Append content to an existing note in the Obsidian vault.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to the existing note",
                },
                "content": {
                    "type": "string",
                    "description": "Content to append",
                },
            },
            "required": ["path", "content"],
        },
        fn=async_,
    )


def build_vault_async_tools(vault: VaultService) -> dict[str, AsyncToolExecutor]:
    """Build async executor functions for all vault tools."""

    async def search_vault(query: str, max_results: int = 10) -> str:
        notes = await vault.search(query, max_results=max_results)
        if not notes:
            return f"No notes found matching '{query}'"
        lines = [f"Found {len(notes)} note(s):"]
        lines.extend(f"\n📄 {note.path}\n{note.content}" for note in notes)
        return "\n".join(lines)

    async def read_note(path: str) -> str:
        note = await vault.read(path)
        return note.content

    async def list_vault_folders(folder: str = "") -> str:
        folders = await vault.list_folders(folder=folder)
        if not folders:
            return "No subfolders found" + (f" in '{folder}'" if folder else " in vault root")
        header = f"Folders in '{folder}':" if folder else "Top-level vault folders:"
        return header + "\n" + "\n".join(f"  📁 {f}" for f in folders)

    async def list_notes(folder: str = "") -> str:
        notes = await vault.list_notes(folder=folder)
        return "\n".join(notes)

    async def create_note(path: str, content: str) -> str:
        note = await vault.create(path, content)
        return f"Created: {note.path}"

    async def append_note(path: str, content: str) -> str:
        note = await vault.append(path, content)
        return f"Appended to: {note.path}"

    return {
        "search_vault": search_vault,
        "read_note": read_note,
        "list_vault_folders": list_vault_folders,
        "list_notes": list_notes,
        "create_note": create_note,
        "append_note": append_note,
    }
