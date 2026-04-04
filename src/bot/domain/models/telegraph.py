from dataclasses import dataclass


@dataclass(frozen=True)
class TelegraphResult:
    """Published Telegraph page result."""

    url: str
    preview: str
