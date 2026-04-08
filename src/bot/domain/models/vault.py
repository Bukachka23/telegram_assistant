from dataclasses import dataclass


@dataclass(frozen=True)
class Note:
    """An Obsidian vault note."""

    path: str
    content: str
    name: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            object.__setattr__(self, "name", self.path.rsplit("/", 1)[-1])
