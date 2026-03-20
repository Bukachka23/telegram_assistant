## 6. Functions and Methods

### Function Design Principles

#### Keep Functions Small and Focused

```python
# ❌ BAD: Long function doing everything
def process_order(order_data):
    # Validate input (20 lines)
    # Create order object (15 lines)
    # Calculate totals (25 lines)
    # Apply discounts (30 lines)
    # Process payment (40 lines)
    # Send confirmation (20 lines)
    # Update inventory (25 lines)
    # Log analytics (15 lines)
    pass

# ✅ GOOD: Small, focused functions
def process_order(order_data: OrderData) -> Order:
    validated_data = validate_order_data(order_data)
    order = create_order(validated_data)
    order = apply_pricing(order)
    process_payment(order)
    send_confirmation(order)
    update_inventory(order)
    return order

def validate_order_data(data: OrderData) -> ValidatedOrderData:
    """Validate and return clean order data."""
    ...

def create_order(data: ValidatedOrderData) -> Order:
    """Create order from validated data."""
    ...
```

#### Use Guard Clauses (Early Returns)

```python
# ❌ BAD: Deep nesting
def process_user(user):
    if user is not None:
        if user.is_active:
            if user.has_permission:
                # actual logic buried here
                return do_something(user)
    return None

# ✅ GOOD: Guard clauses flatten the structure
def process_user(user: User | None) -> Result | None:
    if user is None:
        return None
    if not user.is_active:
        return None
    if not user.has_permission:
        return None
    
    return do_something(user)
```

#### Avoid Mutable Default Arguments

```python
# ❌ BAD: Mutable default (shared across calls!)
def append_item(item, items=[]):
    items.append(item)
    return items

# ✅ GOOD: Use None and create new list
def append_item(item: str, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append(item)
    return items
```

#### Return Consistent Types

```python
# ❌ BAD: Returns different types
def find_user(user_id: int):
    user = db.get(user_id)
    if user:
        return user  # Returns User
    return "Not found"  # Returns str!

# ✅ GOOD: Consistent return type
def find_user(user_id: int) -> User | None:
    return db.get(user_id)

# Or use exceptions for exceptional cases
def get_user(user_id: int) -> User:
    user = db.get(user_id)
    if user is None:
        raise UserNotFoundError(user_id)
    return user
```

### Pythonic Idioms

#### List Comprehensions vs Loops

```python
# ❌ Verbose
squares = []
for n in numbers:
    squares.append(n ** 2)

# ✅ Pythonic
squares = [n ** 2 for n in numbers]

# ✅ With condition
even_squares = [n ** 2 for n in numbers if n % 2 == 0]

# ⚠️ Too complex — use loop instead
# ❌ BAD: Nested comprehension is hard to read
result = [[cell ** 2 for cell in row if cell > 0] 
          for row in matrix if sum(row) > 10]
```

#### Generators for Large Data

```python
# ❌ BAD: Loads everything into memory
def get_all_users() -> list[User]:
    return [User(row) for row in db.query("SELECT * FROM users")]

# ✅ GOOD: Generator yields one at a time
def get_all_users() -> Iterator[User]:
    for row in db.query("SELECT * FROM users"):
        yield User(row)

# Usage remains the same:
for user in get_all_users():
    process(user)
```

#### Context Managers

```python
# ❌ BAD: Manual resource management
file = open("data.txt")
try:
    content = file.read()
finally:
    file.close()

# ✅ GOOD: Context manager
with open("data.txt") as file:
    content = file.read()

# Creating custom context managers
from contextlib import contextmanager

@contextmanager
def database_transaction():
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
```
