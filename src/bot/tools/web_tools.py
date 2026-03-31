from bot.shared.constants import ASYNC_TOOL_PREFIX
from bot.tools.registry import ToolRegistry


def register_web_tools(registry: ToolRegistry) -> None:
    """Register web search tools with the registry."""
    registry.register(
        name="web_search",
        description=(
            "Search the web for real-time information. "
            "Use when you need current news, live data, prices, recent events, "
            "or anything beyond your training data."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to return (default 5, max 20)",
                },
            },
            "required": ["query"],
        },
        fn=lambda **_: f"{ASYNC_TOOL_PREFIX}web_search",
    )
