## 4. Clean Architecture & SOLID Principles

### Clean Architecture Overview

Clean Architecture organizes code into concentric layers where **dependencies point inward**:

```
┌───────────────────────────────────────────┐
│           Frameworks & Drivers            │  ← Web frameworks, databases
│  ┌───────────────────────────────────┐    │
│  │       Interface Adapters          │    │  ← Controllers, presenters
│  │  ┌───────────────────────────┐    │    │
│  │  │    Application Layer      │    │    │  ← Use cases, services
│  │  │  ┌───────────────────┐    │    │    │
│  │  │  │   Domain Layer    │    │    │    │  ← Entities, business rules
│  │  │  └───────────────────┘    │    │    │
│  │  └───────────────────────────┘    │    │
│  └───────────────────────────────────┘    │
└───────────────────────────────────────────┘
```

**The Dependency Rule**: Source code dependencies must point inward only. Nothing in an inner circle can know anything about something in an outer circle.

### SOLID Principles in Python

#### S — Single Responsibility Principle

```python
# ❌ BAD: Class does too many things
class UserService:
    def create_user(self, data): ...
    def send_welcome_email(self, user): ...
    def generate_pdf_report(self, user): ...
    def update_analytics(self, user): ...

# ✅ GOOD: Each class has one responsibility
class UserService:
    def __init__(self, repository: UserRepository):
        self._repository = repository
    
    def create_user(self, data: UserData) -> User:
        user = User.from_data(data)
        return self._repository.save(user)

class EmailService:
    def send_welcome_email(self, user: User) -> None: ...

class ReportService:
    def generate_report(self, user: User) -> Report: ...
```

#### O — Open/Closed Principle

```python
from abc import ABC, abstractmethod
from typing import Protocol

# ✅ Open for extension, closed for modification
class PaymentProcessor(Protocol):
    def process(self, amount: float) -> bool: ...

class StripeProcessor:
    def process(self, amount: float) -> bool:
        # Stripe-specific logic
        return True

class PayPalProcessor:
    def process(self, amount: float) -> bool:
        # PayPal-specific logic
        return True

# Adding new payment method doesn't require modifying existing code
class CryptoProcessor:
    def process(self, amount: float) -> bool:
        return True
```

#### L — Liskov Substitution Principle

```python
# ❌ BAD: Square violates LSP for Rectangle
class Rectangle:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

class Square(Rectangle):
    def __init__(self, side: int):
        super().__init__(side, side)
    
    # Setting width should also set height — breaks expectations!

# ✅ GOOD: Use composition or separate hierarchies
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

class Rectangle(Shape):
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height
    
    def area(self) -> float:
        return self.width * self.height

class Square(Shape):
    def __init__(self, side: float):
        self.side = side
    
    def area(self) -> float:
        return self.side ** 2
```

#### I — Interface Segregation Principle

```python
from typing import Protocol

# ❌ BAD: Fat interface
class Worker(Protocol):
    def work(self) -> None: ...
    def eat(self) -> None: ...
    def sleep(self) -> None: ...

# Robot can't eat or sleep!

# ✅ GOOD: Segregated interfaces
class Workable(Protocol):
    def work(self) -> None: ...

class Eatable(Protocol):
    def eat(self) -> None: ...

class Human:
    def work(self) -> None: ...
    def eat(self) -> None: ...

class Robot:
    def work(self) -> None: ...

def assign_work(worker: Workable) -> None:
    worker.work()
```

#### D — Dependency Inversion Principle

```python
from typing import Protocol

# ❌ BAD: High-level depends on low-level
class MySQLDatabase:
    def query(self, sql: str) -> list: ...

class UserService:
    def __init__(self):
        self.db = MySQLDatabase()  # Tight coupling!

# ✅ GOOD: Both depend on abstraction
class Database(Protocol):
    def query(self, sql: str) -> list: ...

class MySQLDatabase:
    def query(self, sql: str) -> list: ...

class PostgreSQLDatabase:
    def query(self, sql: str) -> list: ...

class UserService:
    def __init__(self, db: Database):  # Dependency injection
        self.db = db

# At composition root:
db = MySQLDatabase()
service = UserService(db)
```
