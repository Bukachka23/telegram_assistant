from collections.abc import Callable
from typing import Any

from bot.domain.models import Tool


class ToolRegistry:
    """Registry of tools available for LLM function calling."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._schema_cache: list[dict] | None = None

    def register(self, name: str, description: str, parameters: dict[str, Any], fn: Callable[..., str]) -> None:
        """Register a tool."""
        self._tools[name] = Tool(name=name, description=description, parameters=parameters, fn=fn,)
        self._schema_cache = None  # Invalidate on registration

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
        if self._schema_cache is None:
            self._schema_cache = [
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
        return self._schema_cache

    @property
    def names(self) -> list[str]:
        return list(self._tools.keys())
