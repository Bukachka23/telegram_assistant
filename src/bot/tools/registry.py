from collections.abc import Callable
from typing import Any

from bot.domain.models import Tool


class ToolRegistry:
    """Registry of tools available for LLM function calling."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, name: str, description: str, parameters: dict[str, Any], fn: Callable[..., str]) -> None:
        """Register a tool."""
        self._tools[name] = Tool(name=name, description=description, parameters=parameters, fn=fn,)

    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        """Execute a tool by name with arguments. Returns result string."""
        tool = self._tools.get(name)
        if not tool:
            return f"Error: unknown tool '{name}'"
        try:
            return tool.fn(**arguments)
        except Exception as e:  # noqa: BLE001
            return f"Error: {e}"

    def to_openrouter_schema(self) -> list[dict]:
        """Export all tools as OpenRouter function calling schema."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self._tools.values()
        ]

    @property
    def names(self) -> list[str]:
        return list(self._tools.keys())
