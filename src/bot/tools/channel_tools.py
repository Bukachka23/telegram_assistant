"""Channel query tools for LLM function calling.

These tools are async (Telethon) but the registry expects sync callables.
They are registered as thin wrappers that are invoked via the async LLM service.
"""

from bot.tools.registry import ToolRegistry


def register_channel_tools(registry: ToolRegistry) -> None:
    """Register channel tool schemas only.

    The actual execution is handled by ChannelService (async),
    so we register placeholders that the LLM service routes manually.
    """

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
        fn=lambda **_: "ASYNC_TOOL:fetch_messages",
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
        fn=lambda **_: "ASYNC_TOOL:search_channel",
    )
