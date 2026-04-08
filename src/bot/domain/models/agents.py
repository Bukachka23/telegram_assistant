from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentProfile:
    """A built-in assistant profile selectable per user session."""

    name: str
    command: str
    display_name: str
    prompt: str
    temperature: float
    max_tokens: int
    allowed_tools: list[str] = field(default_factory=list)
