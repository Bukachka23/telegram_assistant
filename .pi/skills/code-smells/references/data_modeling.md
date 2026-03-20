## 7. Data Modeling

### Dataclasses — The Modern Default

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class User:
    id: int
    email: str
    name: str
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    roles: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate after initialization."""
        if "@" not in self.email:
            raise ValueError(f"Invalid email: {self.email}")

# Immutable dataclass
@dataclass(frozen=True)
class Money:
    amount: float
    currency: str
    
    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")
        return Money(self.amount + other.amount, self.currency)
```

### Pydantic — When Validation Matters

```python
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(max_length=100)
    
    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        return v

class User(BaseModel):
    id: int
    email: EmailStr
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True  # Allows ORM model conversion

# Automatic validation
try:
    user = UserCreate(
        email="invalid",
        password="weak",
        name="John"
    )
except ValidationError as e:
    print(e.errors())
```

### When to Use What

| Tool | Use Case |
|------|----------|
| **dataclass** | Internal data structures, simple DTOs |
| **dataclass(frozen=True)** | Value objects, immutable data |
| **Pydantic BaseModel** | API input validation, configuration |
| **NamedTuple** | Lightweight immutable records |
| **TypedDict** | Dict with known structure (for JSON) |
| **Enum** | Fixed set of choices |

### Avoid Passing Dictionaries

```python
# ❌ BAD: Dictionary — no type safety, unclear structure
def process_user(user_dict):
    if user_dict["status"] == "active":  # KeyError if missing
        send_email(user_dict["email"])    # Typo "mail" won't be caught
        log(f"Processed {user_dict['name']}")  # What fields exist?

# ✅ GOOD: Explicit data class
@dataclass
class User:
    id: int
    email: str
    name: str
    status: str

def process_user(user: User) -> None:
    if user.status == "active":
        send_email(user.email)
        log(f"Processed {user.name}")
```