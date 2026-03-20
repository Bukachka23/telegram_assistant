# Tips For Refactoring

Structured as: Category -> Tip -> Why -> Example.

## Modularity And Scope

### Tip: Keep Code Modular
Why: Smaller functions/classes are easier to test, reuse, and change without side effects.
Example:
```python
# Bad

def process_data(data):
    # Load data
    # Clean data
    # Analyze data
    # Save results
    pass

# Good

def load_data(path):
    pass

def clean_data(data):
    pass

def analyze_data(data):
    pass

def save_results(results):
    pass
```

### Tip: Single Responsibility Over God Objects
Why: Large classes and functions accumulate hidden coupling and become change magnets.
Example:
```python
# Bad
class Application:
    def __init__(self):
        self.db = Database()
        self.cache = Cache()
        self.email = EmailService()
        self.users = []
        self.orders = []

    def create_user(self): ...
    def delete_user(self): ...
    def send_email(self): ...
    def process_payment(self): ...
    def generate_report(self): ...

# Good
class UserService:
    def create_user(self): ...
    def delete_user(self): ...

class PaymentService:
    def process_payment(self): ...

class ReportingService:
    def generate_report(self): ...
```

### Tip: Decompose Long Functions
Why: Long functions hide intent and often mix responsibilities.
Example:
```python
# Bad

def process_order(order_data):
    # 200+ lines of mixed responsibilities
    pass

# Good

def process_order(order_data: OrderData) -> Order:
    order = create_order(order_data)
    order = apply_discounts(order)
    order = calculate_shipping(order)
    return order
```

## Reuse And Duplication

### Tip: DRY (Don't Repeat Yourself)
Why: Duplication multiplies maintenance cost and bugs.
Example:
```python
# Bad

def print_user_details(name, age):
    print(f"Name: {name}")
    print(f"Age: {age}")


def print_product_details(product, price):
    print(f"Product: {product}")
    print(f"Price: {price}")

# Good

def print_details(label, value):
    print(f"{label}: {value}")
```

### Tip: Prefer Built-ins Over Custom Utilities
Why: Standard libraries are optimized, tested, and widely understood.
Example:
```python
# Bad

def find_max(items):
    max_val = items[0]
    for num in items:
        if num > max_val:
            max_val = num
    return max_val

# Good
max_val = max(items)
```

## Data Modeling And Contracts

### Tip: Model Data Explicitly (Avoid Passing Dicts)
Why: Explicit models are safer, self-documenting, and IDE-friendly.
Example:
```python
# Bad

def process_user(user_dict):
    if user_dict["status"] == "active":
        send_email(user_dict["email"])
        log_activity(f"Processed {user_dict['name']}")

# Good
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: int
    email: str
    full_name: str
    status: str
    last_login: Optional[datetime] = None


def process_user(user: User):
    if user.status == "active":
        send_email(user.email)
        log_activity(f"Processed {user.full_name}")
```

### Tip: Replace Arrays With Objects For Records
Why: Named fields prevent index bugs and communicate intent.
Example:
```python
# Bad
team = ["Liverpool", 15]
name = team[0]
wins = int(team[1])

# Good
from dataclasses import dataclass

@dataclass
class TeamPerformance:
    name: str
    wins: int

team = TeamPerformance("Liverpool", 15)
```

### Tip: Use Enums For Known Choices
Why: Enums prevent typos and improve autocomplete and validation.
Example:
```python
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"


def process_order(order, status: OrderStatus):
    if status == OrderStatus.PENDING:
        ...
```

### Tip: Replace Data Value With Object When Behavior Grows
Why: Encapsulation reduces scattered validation/formatting logic.
Example:
```python
# Bad
class Order:
    def __init__(self, address):
        self.address = address

    def format_shipping_label(self):
        if not self.address:
            raise ValueError("Address cannot be empty")
        return self.address.upper()

# Good
class Address:
    def __init__(self, value):
        self.value = value

    def format_for_shipping(self):
        if not self.value:
            raise ValueError("Address cannot be empty")
        return self.value.upper()

class Order:
    def __init__(self, address):
        self.address = Address(address)
```

## Control Flow And Readability

### Tip: Prefer Guard Clauses To Deep Nesting
Why: Flat control flow is easier to scan and maintain.
Example:
```python
# Good

def process_payment(order, user):
    if not order.is_valid:
        return False
    if not user.has_payment_method:
        return False
    payment_method = user.get_payment_method()
    if not payment_method.has_sufficient_funds(order.total):
        return False
    ...
```

### Tip: Avoid Catch-All Except
Why: Bare exceptions hide programming errors and make debugging harder.
Example:
```python
# Good
try:
    user_data = get_user_from_api(user_id)
    process_user_data(user_data)
except ConnectionError as e:
    logger.error(f"API connection failed: {e}")
except ValueError as e:
    logger.error(f"Invalid user data: {e}")
except Exception as e:
    logger.critical("Unexpected error", exc_info=True)
    raise
```

### Tip: Don't Use Exceptions For Normal Control Flow
Why: Exceptions should be exceptional; status returns keep flow explicit.
Example:
```python
# Good

def get_weather_forecast(city: str) -> dict[str, str]:
    result = fetch_from_primary_api(city)
    if result["status"] == "error":
        result = fetch_from_backup_api(city)
    return result
```

## API And Call-Site Clarity

### Tip: Use Keyword-Only Arguments For Optional Flags
Why: Eliminates "mystery booleans" in call sites.
Example:
```python
# Good

def create_user(name, email, *, admin=False, notify=True, temporary=False):
    ...

create_user("John", "john@example.com", admin=True, notify=False)
```

### Tip: Avoid Boolean Blindness
Why: Explicit options make usage self-documenting.
Example:
```python
from dataclasses import dataclass

@dataclass
class OrderOptions:
    send_confirmation: bool = True
    apply_discount: bool = False
    priority_shipping: bool = False

process_order(order, OrderOptions(priority_shipping=True))
```

### Tip: Avoid Wildcard Imports
Why: Explicit imports improve readability and tooling support.
Example:
```python
# Good
from dataclasses import dataclass
```

## Naming And Documentation

### Tip: Use Descriptive Variable Names
Why: Clarity beats brevity in most application code.
Example:
```python
# Bad
a = 10

# Good
number_of_users = 10
```

### Tip: Write Useful Docstrings For Public APIs
Why: Communicates intent, inputs, outputs, and edge cases.
Example:
```python

def celsius_to_fahrenheit(celsius):
    """
    Convert temperature from Celsius to Fahrenheit.

    Args:
        celsius: Temperature in degrees Celsius (float or int)

    Returns:
        Temperature in degrees Fahrenheit
    """
    return celsius * 9 / 5 + 32
```

## Iteration And Comprehensions

### Tip: Use List Comprehensions For Simple Transforms Only
Why: Complex comprehensions reduce readability.
Example:
```python
# Good for simple transforms
adult_names = [u["name"].upper() for u in users if u["age"] >= 18]

# Prefer a loop for complex logic
valid_numbers = []
for value in user_inputs:
    try:
        valid_numbers.append(int(value))
    except ValueError:
        print(f"Invalid input skipped: {value}")
```

## Constants And Configuration

### Tip: Replace Magic Numbers/Strings With Named Constants
Why: Centralizes meaning and avoids scattered edits.
Example:
```python
MINIMUM_AGE = 18
PREMIUM_DISCOUNT_RATE = 0.15
```

### Tip: Centralize Configurable Values
Why: Hardcoded values spread maintenance and complicate localization.
Example:
```python
# Good
translator = LokaliseTranslator(LANGUAGE)

st.title(translator("dashboard_title"))
```

## Filesystem And Paths

### Tip: Prefer Pathlib Over os.path
Why: Object-oriented paths are clearer and less error-prone.
Example:
```python
from pathlib import Path

data_dir = Path("data") / "processed"
data_dir.mkdir(parents=True, exist_ok=True)

filepath = data_dir / "output.csv"
filepath.write_text("results\n")
```

## Object-Oriented Refactorings

### Tip: Move Method
Why: A method belongs where its data is.
Example:
```python
# Move calculate_discount from ClassA to ClassB where it is used
```

### Tip: Move Field
Why: A field should live with the behavior that uses it most.
Example:
```python
# Move discount_rate from ClassA to ClassB
```

### Tip: Extract Class
Why: Split multiple responsibilities into focused classes.
Example:
```python
# Extract Customer from Order
```

### Tip: Inline Class
Why: Remove classes that add no real behavior.
Example:
```python
# Inline Discount into Order
```

### Tip: Hide Delegate
Why: Reduce client knowledge of internal object graphs.
Example:
```python
# employee.get_manager() delegates to department.get_manager()
```

### Tip: Remove Middle Man
Why: Avoid layers that only forward calls.
Example:
```python
# Expose department when Employee only delegates
```

### Tip: Introduce Foreign Method
Why: Add missing behavior when you can’t modify a library class.
Example:
```python
# Add next_week(self, date) in Billing
```

### Tip: Introduce Local Extension
Why: Extend external types via subclassing or wrapping.
Example:
```python
# ExtendedDate(datetime) with next_week()
```

### Tip: Self Encapsulate Field
Why: Centralize field access for validation or lazy loading.
Example:
```python
# Use @property for _price
```

### Tip: Change Value To Reference (Use With Care)
Why: Shared references can reduce duplication when objects are immutable and identical.
Example:
```python
# Use a class-level cache for Currency
```

### Tip: Change Reference To Value (Use With Care)
Why: Value objects are simpler when shared state is unnecessary.
Example:
```python
# Use @dataclass(frozen=True) for Currency
```

## Anti-Patterns And Smells

### Tip: Feature Envy
Why: Logic should live with the data it uses most.
Example:
```python
# Move calculate_total into Order
```

### Tip: Design Pattern Overengineering
Why: Simple problems rarely need heavy patterns.
Example:
```python
# Use a dict of functions instead of an Abstract Factory
```

### Tip: Avoid Static-Only Utility Classes
Why: Modules are a natural namespace in Python.
Example:
```python
# Prefer data_processing.py with top-level functions
```

### Tip: Avoid Overriding Dunder Methods For Surprising Behavior
Why: Unexpected construction semantics confuse users and tools.
Example:
```python
# Use a factory function instead of __new__ magic
```
