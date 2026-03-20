## 8. Type Hints and Protocols

### Modern Type Hints (Python 3.10+)

```python
# Use built-in types directly (no imports needed)
def process_items(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}

# Union types with |
def find_user(user_id: int) -> User | None:
    ...

# Type aliases with `type` statement (Python 3.12+)
type UserId = int
type UserMap = dict[UserId, User]

# Older Python: use TypeAlias
from typing import TypeAlias
UserId: TypeAlias = int
```

### Protocols — Structural Subtyping (Duck Typing)

Protocols enable static duck typing — define what methods/attributes an object must have:

```python
from typing import Protocol, runtime_checkable

class Drawable(Protocol):
    def draw(self) -> None: ...

class Circle:
    def draw(self) -> None:
        print("Drawing circle")

class Square:
    def draw(self) -> None:
        print("Drawing square")

def render(shape: Drawable) -> None:
    shape.draw()

# Both work — no inheritance required!
render(Circle())
render(Square())

# Runtime checking (optional)
@runtime_checkable
class Drawable(Protocol):
    def draw(self) -> None: ...

isinstance(Circle(), Drawable)  # True
```

### Type Hints Best Practices

```python
from typing import Callable, Iterable, Mapping, Sequence
from collections.abc import Iterator

# Use abstract types for parameters (accept more)
def process_items(items: Iterable[str]) -> None:
    for item in items:
        print(item)

# Use concrete types for return values (be specific)
def get_items() -> list[str]:
    return ["a", "b", "c"]

# Callable types
Handler = Callable[[Request], Response]
def register_handler(handler: Handler) -> None: ...

# Generic functions (Python 3.12+)
def first[T](items: Sequence[T]) -> T | None:
    return items[0] if items else None

# Older Python
from typing import TypeVar
T = TypeVar("T")
def first(items: Sequence[T]) -> T | None:
    return items[0] if items else None
```

### Type Checkers

| Tool | Strengths |
|------|-----------|
| **mypy** | Most mature, extensive configuration |
| **Pyright** | Fast, excellent VS Code integration |
| **Ruff** | Linting + some type checking, very fast |

Configuration in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_ignores = true

[[tool.mypy.overrides]]
module = "third_party.*"
ignore_missing_imports = true
```