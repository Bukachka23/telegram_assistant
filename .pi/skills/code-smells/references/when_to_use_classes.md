## 5. Classes and Object-Oriented Design

### When to Use Classes

| Use Classes When | Use Functions/Modules When |
|------------------|---------------------------|
| Managing mutable state | Pure transformations |
| Multiple related methods share data | Single operation |
| Polymorphism is needed | Simple data containers |
| Clear lifecycle (init, operations, cleanup) | Stateless utilities |

### Class Design Guidelines

#### Keep Classes Focused

```python
# ❌ BAD: God class
class Application:
    def __init__(self):
        self.users = []
        self.orders = []
        self.products = []
    
    def create_user(self): ...
    def delete_user(self): ...
    def create_order(self): ...
    def process_payment(self): ...
    def send_email(self): ...
    def generate_report(self): ...

# ✅ GOOD: Focused classes
class UserRepository:
    def create(self, data: UserData) -> User: ...
    def delete(self, user_id: int) -> None: ...

class OrderService:
    def create_order(self, user: User, items: list[Item]) -> Order: ...

class PaymentProcessor:
    def process(self, order: Order) -> PaymentResult: ...
```

#### Prefer Composition Over Inheritance

```python
# ❌ BAD: Deep inheritance
class Animal: ...
class Mammal(Animal): ...
class Dog(Mammal): ...
class GoldenRetriever(Dog): ...

# ✅ GOOD: Composition
from dataclasses import dataclass

@dataclass
class Movement:
    speed: float
    style: str  # "walk", "swim", "fly"

@dataclass
class Sound:
    noise: str
    volume: float

@dataclass
class Animal:
    name: str
    movement: Movement
    sound: Sound

dog = Animal(
    name="Buddy",
    movement=Movement(speed=15.0, style="walk"),
    sound=Sound(noise="bark", volume=0.8)
)
```

#### Encapsulation with Properties

```python
class BankAccount:
    def __init__(self, initial_balance: float = 0):
        self._balance = initial_balance
        self._transactions: list[float] = []
    
    @property
    def balance(self) -> float:
        """Read-only balance."""
        return self._balance
    
    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit must be positive")
        self._balance += amount
        self._transactions.append(amount)
    
    def withdraw(self, amount: float) -> None:
        if amount > self._balance:
            raise ValueError("Insufficient funds")
        self._balance -= amount
        self._transactions.append(-amount)
```
