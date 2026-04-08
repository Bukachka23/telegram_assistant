from bot.config.constants import ASYNC_TOOL_PREFIX
from bot.tools.registry import ToolRegistry


def register_channel_tools(registry: ToolRegistry) -> None:
    """Register channel tool schemas only."""
    registry.register(
        name="fetch_messages",
        description=(
            "Fetch recent messages from a public Telegram channel. "
            "Returns message texts with timestamps."
        ),
        parameters={
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Channel username (e.g., '@python_news')",
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of messages to fetch (default 20, max 100)",
                },
                "query": {
                    "type": "string",
                    "description": "Optional keyword filter",
                },
            },
            "required": ["channel"],
        },
        fn=lambda **_: f"{ASYNC_TOOL_PREFIX}fetch_messages",
    )

    registry.register(
        name="search_channel",
        description=(
            "Search a public Telegram channel for messages matching a query. "
            "Returns matching messages with context."
        ),
        parameters={
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Channel username (e.g., '@ai_news')",
                },
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "days": {
                    "type": "integer",
                    "description": "Search within last N days (default 7)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results (default 20)",
                },
            },
            "required": ["channel", "query"],
        },
        fn=lambda **_: f"{ASYNC_TOOL_PREFIX}search_channel",
    )
