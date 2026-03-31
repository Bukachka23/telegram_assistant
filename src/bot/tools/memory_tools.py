from bot.shared.constants import ASYNC_TOOL_PREFIX
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
