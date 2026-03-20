## 9. Design Patterns in Python

### Repository Pattern

Abstracts data access, making business logic independent of storage:

```python
from abc import ABC, abstractmethod
from typing import Protocol

# Define the interface
class UserRepository(Protocol):
    def get_by_id(self, user_id: int) -> User | None: ...
    def save(self, user: User) -> User: ...
    def delete(self, user_id: int) -> None: ...

# SQL implementation
class SQLUserRepository:
    def __init__(self, session: Session):
        self._session = session
    
    def get_by_id(self, user_id: int) -> User | None:
        return self._session.query(UserModel).get(user_id)
    
    def save(self, user: User) -> User:
        model = UserModel(**user.dict())
        self._session.add(model)
        self._session.commit()
        return User.from_orm(model)
    
    def delete(self, user_id: int) -> None:
        self._session.query(UserModel).filter_by(id=user_id).delete()
        self._session.commit()

# In-memory implementation for testing
class InMemoryUserRepository:
    def __init__(self):
        self._users: dict[int, User] = {}
        self._counter = 0
    
    def get_by_id(self, user_id: int) -> User | None:
        return self._users.get(user_id)
    
    def save(self, user: User) -> User:
        if user.id is None:
            self._counter += 1
            user = user.copy(id=self._counter)
        self._users[user.id] = user
        return user
    
    def delete(self, user_id: int) -> None:
        self._users.pop(user_id, None)
```

### Dependency Injection

```python
from typing import Protocol

class EmailSender(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...

class UserService:
    def __init__(
        self,
        repository: UserRepository,
        email_sender: EmailSender
    ):
        self._repository = repository
        self._email_sender = email_sender
    
    def create_user(self, data: UserCreate) -> User:
        user = User(**data.dict())
        saved_user = self._repository.save(user)
        self._email_sender.send(
            to=user.email,
            subject="Welcome!",
            body="Your account has been created."
        )
        return saved_user

# Composition root — where dependencies are wired
def create_app() -> FastAPI:
    # Create concrete implementations
    db_session = create_session()
    repository = SQLUserRepository(db_session)
    email_sender = SMTPEmailSender(config.smtp_host)
    
    # Inject dependencies
    user_service = UserService(repository, email_sender)
    
    # Use in routes
    app = FastAPI()
    app.state.user_service = user_service
    return app
```

### Factory Pattern

```python
from abc import ABC, abstractmethod
from enum import Enum

class NotificationType(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

class Notifier(ABC):
    @abstractmethod
    def send(self, message: str) -> None: ...

class EmailNotifier(Notifier):
    def send(self, message: str) -> None:
        print(f"Email: {message}")

class SMSNotifier(Notifier):
    def send(self, message: str) -> None:
        print(f"SMS: {message}")

class PushNotifier(Notifier):
    def send(self, message: str) -> None:
        print(f"Push: {message}")

class NotifierFactory:
    _notifiers: dict[NotificationType, type[Notifier]] = {
        NotificationType.EMAIL: EmailNotifier,
        NotificationType.SMS: SMSNotifier,
        NotificationType.PUSH: PushNotifier,
    }
    
    @classmethod
    def create(cls, notification_type: NotificationType) -> Notifier:
        notifier_class = cls._notifiers.get(notification_type)
        if notifier_class is None:
            raise ValueError(f"Unknown type: {notification_type}")
        return notifier_class()

# Usage
notifier = NotifierFactory.create(NotificationType.EMAIL)
notifier.send("Hello!")
```

### Strategy Pattern

```python
from typing import Protocol

class PricingStrategy(Protocol):
    def calculate(self, base_price: float) -> float: ...

class RegularPricing:
    def calculate(self, base_price: float) -> float:
        return base_price

class PremiumPricing:
    discount: float = 0.1
    
    def calculate(self, base_price: float) -> float:
        return base_price * (1 - self.discount)

class SeasonalPricing:
    def __init__(self, multiplier: float):
        self.multiplier = multiplier
    
    def calculate(self, base_price: float) -> float:
        return base_price * self.multiplier

class Order:
    def __init__(self, pricing_strategy: PricingStrategy):
        self._pricing = pricing_strategy
    
    def get_total(self, items: list[Item]) -> float:
        base_total = sum(item.price for item in items)
        return self._pricing.calculate(base_total)

# Usage — strategy is swappable
regular_order = Order(RegularPricing())
premium_order = Order(PremiumPricing())
sale_order = Order(SeasonalPricing(multiplier=0.7))
```