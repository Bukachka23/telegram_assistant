"""Obsidian vault tools for LLM function calling."""

from bot.services.vault import VaultService
from bot.tools.registry import ToolRegistry


def register_vault_tools(registry: ToolRegistry, vault: VaultService) -> None:
    """Register all vault tools with the registry."""

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
        fn=lambda query, max_results=10: _search(vault, query, max_results),
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
        fn=lambda path: vault.read(path).content,
    )

    registry.register(
        name="list_notes",
        description="List all markdown files in a vault folder.",
        parameters={
            "type": "object",
            "properties": {
                "folder": {
                    "type": "string",
                    "description": "Folder path (empty for default folder)",
                },
            },
            "required": [],
        },
        fn=lambda folder="": "\n".join(vault.list_notes(folder)),
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
        fn=lambda path, content: f"Created: {vault.create(path, content).path}",
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
        fn=lambda path, content: f"Appended to: {vault.append(path, content).path}",
    )


def _search(vault: VaultService, query: str, max_results: int) -> str:
    """Format search results as a readable string."""
    notes = vault.search(query, max_results=max_results)
    if not notes:
        return f"No notes found matching '{query}'"
    lines = [f"Found {len(notes)} note(s):"]
    for note in notes:
        lines.append(f"\n📄 {note.path}\n{note.content}")
    return "\n".join(lines)
