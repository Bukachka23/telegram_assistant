## TIPS FOR REFACTORING ##

## TIPS

1. Keep the Code Modular

- Break down our code into smaller, reusable functions and classes.
- Each function or class should have a single responsibility.

## Example

```python
# Bad
def process_data(data):
    # Load data
    # Clean data
    # Analyze data
    # Save results

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

2. DRY (Don't Repeat Yourself)

- Avoid writing the same code multiple times.
- Use functions and classes to encapsulate code that can be reused.

## Example

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

3. Leverage Python’s Built-in Functions and Libraries
Python’s standard library is vast, and it’s often better to use built-in functions rather than writing custom code.
For example, instead of writing your own function to find the maximum of a list, use Python’s built-in max() function.

## Example

```python
# Bad
def find_max(lst):
    max_val = lst[0]
    for num in lst:
        if num > max_val:
            max_val = num
    return max_val

# Good
max_val = max(lst)
```

4. List Comprehension
Use list comprehensions to create new lists from existing lists.
For example, instead of writing a for loop to create a new list, use a list comprehension.

## Example 1

```python
numbers = [1, 2, 3, 4, 5]

# The "old way"
squares = []
for number in numbers:
    squares.append(number * number)

# Output: [1, 4, 9, 16, 25]


numbers = [1, 2, 3, 4, 5]
squares = [number * number for number in numbers]
print(squares)

# Output: [1, 4, 9, 16, 25]
```

## Example 2

```python

numbers = [1, 2, 3, 4, 5]
even_squares = []
for number in numbers:
    if number % 2 == 0:
        even_squares.append(number * number)

# Output: [4, 16]

numbers = [1, 2, 3, 4, 5]
even_squares = [number * number for number in numbers if number % 2 == 0]
print(list(even_squares))
```

5. Generators Expression

Use generators to create iterators that lazily yield values.
For example, instead of writing a for loop to iterate over a list, use a generator.
Tip: A generator is like a disposable camera. Once you have looped through it completely, it's exhausted. You cannot loop over it a second time.

## Example

```python
numbers = [1, 2, 3, 4, 5, 6]
even_squares_generator = (number * number for number in numbers if number % 2 == 0)

print(list(even_squares_generator))

# Output: [4, 16, 36]

6. Write Descriptive and Concise Variable Names
Choose variable names that are descriptive yet concise.

Avoid single-letter variables except in cases like loop counters.

## Example:

```python
# Bad
a = 10

# Good
number_of_users = 10
```

7. Return Statements

Return Statements
As a function grows in complexity, it becomes susceptible to having multiple return statements inside the function’s body.
However, in order to keep a clear intent and a sustained readability level, it is preferable to avoid returning meaningful values at multiple output points in the function body.

For instance, take a look at the example below (explained by the inline comments) on how to avoid adding multiple output points and raise exceptions instead:

## Example

```python
# Bad practice

def complex_function(a, b, c):
  if not a:
    return None
  if not b:
    return None
  # Some complex code trying to compute x from a, b and c
  if x:
    return x
  if not x:
    # Some Plan-B computation of x
    return x

# Best practice

def complex_function(a, b, c):
  if not a or not b or not c:
  raise ValueError("The args can't be None")

  # Raising an exception is better

  # Some complex code trying to compute x from a, b and c
  # Resist temptation to return x if succeeded
  if not x:
  # Some Plan-B computation of x

  return x # One single exit point for the returned value x will help when maintaining the code.
```

8. Model Data Explicity. Don't Pass Around Dicts

Instead of this:

```python
def process_user(user_dict):
    if user_dict['status'] == 'active':  # What if 'status' is missing?
        send_email(user_dict['email'])   # What if it's 'mail' in some places?

        # Is it 'name', 'full_name', or 'username'? Who knows!
        log_activity(f"Processed {user_dict['name']}")
```

This code is not robust because it assumes dictionary keys exist without validation.
It offers no protection against typos or missing keys, which will cause KeyError exceptions at runtime.
There's also no documentation of what fields are expected.

DO this

```python
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
    if user.status == 'active':
        send_email(user.email)
        log_activity(f"Processed {user.full_name}")
```

Python's @dataclass decorator gives you a clean, explicit structure with minimal boilerplate. Your IDE can now provide autocomplete for attributes, and you'll get immediate errors if required fields are missing.

For more complex validation, consider Pydantic:

```python
from pydantic import BaseModel, EmailStr, validator

class User(BaseModel):
    id: int
    email: EmailStr  # Validates email format
    full_name: str
    status: str

    @validator('status')
    def status_must_be_valid(cls, v):
        if v not in {'active', 'inactive', 'pending'}:
            raise ValueError('Must be active, inactive or pending')
        return v
```

9. Use Enums for Known Choices

String literals are prone to typos and provide no IDE autocomplete.
The validation only happens at runtime.

Instead of this:

```python
def process_order(order, status):
    if status == 'pending':
        # process logic
    elif status == 'shipped':
        # different logic
    elif status == 'delivered':
        # more logic
    else:
        raise ValueError(f"Invalid status: {status}")

# Later in your code...
process_order(order, 'shiped')  # Typo! But no IDE warning
```

Do this:

```python
from enum import Enum, auto

class OrderStatus(Enum):
    PENDING = 'pending'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'

def process_order(order, status: OrderStatus):
    if status == OrderStatus.PENDING:
        # process logic
    elif status == OrderStatus.SHIPPED:
        # different logic
    elif status == OrderStatus.DELIVERED:
        # more logic

# Later in your code...
process_order(order, OrderStatus.SHIPPED)  # IDE autocomplete helps!
```

When you're dealing with a fixed set of options, an Enum makes your code more robust and self-documenting.

With enums:

- Your IDE provides autocomplete suggestions
- Typos become (almost) impossible
- You can iterate through all possible values when needed
- Enum creates a set of named constants. The type hint status: OrderStatus documents the expected parameter type.
Using OrderStatus.SHIPPED instead of a string literal allows IDE autocomplete and catches typos at development time.

10. Use Keyword-Only Arguments for Clarity

Python's flexible argument system is powerful, but it can lead to confusion when function calls have multiple optional parameters.

Instead of this:

```python
def create_user(name, email, admin=False, notify=True, temporary=False):
    # Implementation

# Later in code...
create_user("John Smith", "john@example.com", True, False)
```

Wait, what do those booleans mean again? When called with positional arguments,
it's unclear what the boolean values represent without checking the function definition.
Is True for admin, notify, or something else?

Do this:

```python
def create_user(name, email, *, admin=False, notify=True, temporary=False):
    # Implementation

# Now you must use keywords for optional args
create_user("John Smith", "john@example.com", admin=True, notify=False)
```

The *, syntax forces all arguments after it to be specified by keyword.
This makes your function calls self-documenting and prevents the "mystery boolean" problem where readers can't tell what True or False refers to without reading the function definition.
This pattern is especially useful in API calls and the like, where you want to ensure clarity at the call site.

11. Use Pathlib Over os.path

Python's os.path module is functional but clunky. The newer pathlib module provides an object-oriented approach that's more intuitive and less error-prone.

Instead of this:

```python
import os

data_dir = os.path.join('data', 'processed')
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

filepath = os.path.join(data_dir, 'output.csv')
with open(filepath, 'w') as f:
    f.write('results\n')

# Check if we have a JSON file with the same name
json_path = os.path.splitext(filepath)[0] + '.json'
if os.path.exists(json_path):
    with open(json_path) as f:
        data = json.load(f)

```

This uses string manipulation with os.path.join() and os.path.splitext() for path handling. Path operations are scattered across different functions. The code is verbose and less intuitive.

Do this:

```python
from pathlib import Path

data_dir = Path('data') / 'processed'
data_dir.mkdir(parents=True, exist_ok=True)

filepath = data_dir / 'output.csv'
filepath.write_text('results\n')

# Check if we have a JSON file with the same name
json_path = filepath.with_suffix('.json')
if json_path.exists():
    data = json.loads(json_path.read_text())
```

Why pathlib is better:

- Path joining with / is more intuitive
- Methods like mkdir(), exists(), and read_text() are attached to the path object
- Operations like changing extensions (with_suffix) are more semantic
- Pathlib handles the subtleties of path manipulation across different operating systems. This makes your code more portable and robust.


12. Fail Fast with Guard Clauses

Deeply nested if-statements are often hard to understand and maintain. Using early returns — guard clauses — leads to more readable code.

Instead of this:

```python
def process_payment(order, user):
    if order.is_valid:
        if user.has_payment_method:
            payment_method = user.get_payment_method()
            if payment_method.has_sufficient_funds(order.total):
                try:
                    payment_method.charge(order.total)
                    order.mark_as_paid()
                    send_receipt(user, order)
                    return True
                except PaymentError as e:
                    log_error(e)
                    return False
            else:
                log_error("Insufficient funds")
                return False
        else:
            log_error("No payment method")
            return False
    else:
        log_error("Invalid order")
        return False
```

Deep nesting is hard to follow. Each conditional block requires tracking multiple branches simultaneously.

Do this:

```python
def process_payment(order, user):
    # Guard clauses: check preconditions first
    if not order.is_valid:
        log_error("Invalid order")
        return False

    if not user.has_payment_method:
        log_error("No payment method")
        return False

    payment_method = user.get_payment_method()
    if not payment_method.has_sufficient_funds(order.total):
        log_error("Insufficient funds")
        return False

    # Main logic comes after all validations
    try:
        payment_method.charge(order.total)
        order.mark_as_paid()
        send_receipt(user, order)
        return True
    except PaymentError as e:
        log_error(e)
        return False
```

Guard clauses handle error cases up front, reducing indentation levels.
Each condition is checked sequentially, making the flow easier to follow.
The main logic comes at the end, clearly separated from error handling.
This approach scales much better as your logic grows in complexity.

13. Don't Overuse List Comprehensions

List comprehensions are one of Python's most elegant features, but they become unreadable when overloaded with complex conditions or transformations.

Instead of this:

```python
# Hard to parse at a glance
active_premium_emails = [user['email'] for user in users_list
                         if user['status'] == 'active' and
                         user['subscription'] == 'premium' and
                         user['email_verified'] and
                         not user['email'] in blacklisted_domains]
```

This list comprehension packs too much logic into one line. It's hard to read and debug. Multiple conditions are chained together, making it difficult to understand the filter criteria.

Do this:
Here are better alternatives.

Option 1: Function with a descriptive name
Extracts the complex condition into a named function with a descriptive name. The list comprehension is now much clearer, focusing on what it's doing (extracting emails) rather than how it's filtering.

```python
def is_valid_premium_user(user):
    return (user['status'] == 'active' and
            user['subscription'] == 'premium' and
            user['email_verified'] and
            not user['email'] in blacklisted_domains)

active_premium_emails = [user['email'] for user in users_list if is_valid_premium_user(user)]
```

Option 2: Traditional loop when logic is complex
Uses a traditional loop with early continues for clarity. Each condition is checked separately, making it easy to debug which condition might be failing. The transformation logic is also clearly separated.

```python
active_premium_emails = []
for user in users_list:
    # Complex filtering logic
    if user['status'] != 'active':
        continue
    if user['subscription'] != 'premium':
        continue
    if not user['email_verified']:
        continue
    if user['email'] in blacklisted_domains:
        continue

    # Complex transformation logic
    email = user['email'].lower().strip()
    active_premium_emails.append(email)
```

List comprehensions should make your code more readable, not less. When the logic gets complex:

- Break complex conditions into named functions
- Consider using a regular loop with early continues
- Split complex operations into multiple steps
- Remember, the goal is readability.

14. Write Reusable Pure Functions

A function is a pure function if it produces the same output for the same inputs always.
Also, it has no side effects.

Instead of this:

```python
total_price = 0  # Global state

def add_item_price(item_name, quantity):
    global total_price
    # Look up price from global inventory
    price = inventory.get_item_price(item_name)
    # Apply discount
    if settings.discount_enabled:
        price *= 0.9
    # Update global state
    total_price += price * quantity

# Later in code...
add_item_price('widget', 5)
add_item_price('gadget', 3)
print(f"Total: ${total_price:.2f}")
```

This uses global state (total_price) which makes testing difficult.

The function has side effects (modifying global state) and depends on external state (inventory and settings).
This makes it unpredictable and hard to reuse.

Do this:

```python
def calculate_item_price(item, price, quantity, discount=0):
    """Calculate final price for a quantity of items with optional discount.

    Args:
        item: Item identifier (for logging)
        price: Base unit price
        quantity: Number of items
        discount: Discount as decimal

    Returns:
        Final price after discounts
    """
    discounted_price = price * (1 - discount)
    return discounted_price * quantity

def calculate_order_total(items, discount=0):
    """Calculate total price for a collection of items.

    Args:
        items: List of (item_name, price, quantity) tuples
        discount: Order-level discount

    Returns:
        Total price after all discounts
    """
    return sum(
        calculate_item_price(item, price, quantity, discount)
        for item, price, quantity in items
    )

# Later in code...
order_items = [
    ('widget', inventory.get_item_price('widget'), 5),
    ('gadget', inventory.get_item_price('gadget'), 3),
]

total = calculate_order_total(order_items,
                             discount=0.1 if settings.discount_enabled else 0)
print(f"Total: ${total:.2f}")
```

The following version uses pure functions that take all dependencies as parameters.

15. Write Docstrings for Public Functions and Classes

Documentation isn't (and shouldn't be) an afterthought.
It's a core part of maintainable code. Good docstrings explain not just what functions do,
but why they exist and how to use them correctly.

Instead of this:

```python
def celsius_to_fahrenheit(celsius):
    """Convert Celsius to Fahrenheit."""
    return celsius * 9/5 + 32
```

This is a minimal docstring that only repeats the function name. Provides no information about parameters, return values, or edge cases.
Do this:

```python
def celsius_to_fahrenheit(celsius):
	"""
	Convert temperature from Celsius to Fahrenheit.
	The formula used is: F = C × (9/5) + 32
	Args:
    	celsius: Temperature in degrees Celsius (can be float or int)
	Returns:
    	Temperature converted to degrees Fahrenheit
	Example:
    	>>> celsius_to_fahrenheit(0)
    	32.0
    	>>> celsius_to_fahrenheit(100)
    	212.0
    	>>> celsius_to_fahrenheit(-40)
    	-40.0
	"""
	return celsius * 9/5 + 32
```

A good docstring:

Documents parameters and return values
Notes any exceptions that might be raised
Provides usage examples
Your docstrings serve as executable documentation that stays in sync with your code.

16. Avoid Catch-All except

Generic exception handlers hide bugs and make debugging difficult.
They catch everything, including syntax errors, memory errors, and keyboard interrupts.

Instead of this:

```python
try:
    user_data = get_user_from_api(user_id)
    process_user_data(user_data)
    save_to_database(user_data)
except:
    # What failed? We'll never know!
    logger.error("Something went wrong")
```

This uses a bare exception to handle:

- Programming errors (like syntax errors)
- System errors (like MemoryError)
- Keyboard interrupts (Ctrl+C)
- Expected errors (like network timeouts)
- This makes debugging extremely difficult, as all errors are treated the same.

Do this:

```python
try:
    user_data = get_user_from_api(user_id)
    process_user_data(user_data)
    save_to_database(user_data)
except ConnectionError as e:
    logger.error(f"API connection failed: {e}")
    # Handle API connection issues
except ValueError as e:
    logger.error(f"Invalid user data received: {e}")
    # Handle validation issues
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    # Handle database issues
except Exception as e:
    # Last resort for unexpected errors
    logger.critical(f"Unexpected error processing user {user_id}: {e}",
                  exc_info=True)
    # Possibly re-raise or handle generically
    raise
```

Catches specific exceptions that can be expected and handled appropriately.
Each exception type has its own error message and handling strategy.

The final except Exception catches unexpected errors, logs them with full traceback (exc_info=True),
and re-raises them to avoid silently ignoring serious issues.

If you do need a catch-all handler for some reason, use except Exception as e: rather than a bare except:,
and always log the full exception details with exc_info=True.

17. Choose the Right Tool for Iteration: `for` vs. `map`/`filter`

- While functional tools like `map` and `filter` can be elegant, the traditional `for` loop is often a more readable, practical, and superior choice in many real-world scenarios.
- The goal should be clarity and maintainability, not just writing "clever" functional code.

### The Pythonic Way: List Comprehension

For simple filtering and transformation, a list comprehension is often the fastest and most readable choice. It combines the best of both worlds.

## Example

```python
users = [
    {"name": "Alice", "age": 28},
    {"name": "Bob", "age": 17},
    {"name": "Carol", "age": 35},
]

# Bad (Verbose for a simple task)
adult_names = []
for user in users:
    if user["age"] >= 18:
        adult_names.append(user["name"].upper())

# Good (Concise and readable)
adult_names = [user["name"].upper() for user in users if user["age"] >= 18]
```

### The Imperative Workhorse: `for` Loop

When your logic becomes too complex for a single line, a `for` loop is your best friend. It's explicit, easy to debug, and handles complex flow control gracefully.

## Example

```python
# Good: Use a for loop for complex logic like exception handling
def parse_numbers(user_inputs: list[str]) -> list[int]:
    valid_numbers = []
    for value in user_inputs:
        try:
            number = int(value)
            valid_numbers.append(number)
        except ValueError:
            # It's easy to handle errors and log them
            print(f"Invalid input skipped: {value}")
    return valid_numbers
```

### The Functional Duo: `map` and `filter`

These functions are declarative and use lazy evaluation, making them efficient for data pipelines. However, they can quickly become unreadable when combined with complex `lambda` functions.

## Example

```python
# Bad: Overly complex for this task
def parse_numbers_functional(user_inputs: list[str]):
    def safe_convert(value: str):
        try:
            return int(value)
        except ValueError:
            print(f"Invalid input skipped: {value}")
            return None # Awkwardly returning None on failure

    # Requires mapping, then filtering out the Nones
    return list(filter(lambda x: x is not None, map(safe_convert, user_inputs)))
```

### When to Use a `for` Loop

A `for` loop is almost always the better choice in these four cases:

1.  **Complex Logic:** When you have nested conditions, multiple steps, or default values.
2.  **Exception Handling:** When you need to gracefully handle errors with `try...except`.
3.  **Side Effects:** When your loop needs to do more than just return a value, like printing, logging, or writing to a file.
4.  **Early Exits:** When you need to stop the loop early (`break`) or skip an iteration (`continue`).


18. Use Exceptions for Control Flow

- Problem: Using try...except blocks to handle expected, non-exceptional program flow, such as an API timeout. This makes the code harder to read, can have performance implications, and leads to messy, nested logic.
- Solution: Instead of raising exceptions for predictable failures, return a status object (e.g., a dictionary with a 'status' key). The calling function can then use a simple if statement to check the status and decide the next step, making the control flow explicit and clean.

Bad:

Problem (Before): Using try...except for expected API timeouts.

```python
# BAD: Using exceptions for expected control flow
def get_weather_forecast(city: str) -> dict[str, str]:
    try:
        return fetch_from_primary_api(city)
    except TimeoutError:
        try:
            return fetch_from_backup_api(city)
        except TimeoutError:
            return {"status": "error", "message": "Both APIs timed out."}

# Helper functions that raise exceptions
def fetch_from_primary_api(city: str) -> dict[str, str]:
    if simulate_timeout():
        raise TimeoutError("Primary API timed out.")
    return {"status": "success", "data": f"Weather in {city} is sunny."}

def fetch_from_backup_api(city: str) -> dict[str, str]:
    if simulate_timeout():
        raise TimeoutError("Backup API timed out.")
    return {"status": "success", "data": f"Backup: Weather in {city} is cloudy."}
```

Good:

Solution (After): Returning a status and checking it with if statements.

```python
# GOOD: Using return values for control flow
def get_weather_forecast(city: str) -> dict[str, str]:
    result = fetch_from_primary_api(city)
    if result["status"] == "error":
        result = fetch_from_backup_api(city)
    return result

# Helper functions that return a status
def fetch_from_primary_api(city: str) -> dict[str, str]:
    if simulate_timeout():
        return {"status": "error", "message": "Primary API timed out."}
    return {"status": "success", "data": f"Weather in {city} is sunny."}

def fetch_from_backup_api(city: str) -> dict[str, str]:
    if simulate_timeout():
        return {"status": "error", "message": "Backup API timed out."}
    return {"status": "success", "data": f"Backup: Weather in {city} is cloudy."}
```

19. Use Classes with Static Methods Instead of Modules

- Problem: Creating a class that only contains @staticmethod methods, often as a way to group related utility functions. This is an unnecessary layer of indirection in Python.
- Solution: Use a Python module (.py file) as a namespace. Define the related functions at the top level of the file. This is more idiomatic in Python and allows for direct, cleaner imports and usage.

Bad:

Problem (Before): A class used only as a namespace for static methods.

```python
# BAD: A class with only static methods
class DataPreprocessingUtils:
    @staticmethod
    def fill_missing_values(df: pd.DataFrame) -> pd.DataFrame:
        # ... implementation ...
        return df.fillna(df.median(numeric_only=True))

    @staticmethod
    def normalize_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
        # ... implementation ...
        return df

# Usage
df = DataPreprocessingUtils.fill_missing_values(df)
```

Good:

Solution (After): Using a module with top-level functions.

```python
# In a file named data_processing.py
def fill_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    # ... implementation ...
    return df.fillna(df.median(numeric_only=True))

def normalize_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    # ... implementation ...
    return df

# In another file (e.g., main.py)
from data_processing import fill_missing_values, normalize_columns

df = fill_missing_values(df)
```

20. Override Dunder Methods in Surprising Ways

- Problem: Overriding dunder (double underscore) methods like new to implement "magic" behavior, such as returning an instance of a different class based on an argument. This violates the principle of least astonishment and makes the code unpredictable and hard to debug.
- Solution: Be explicit. Use a separate, clearly named factory function or a dictionary to handle the creation of different object types. This makes the logic transparent and predictable.

Bad:

Problem (Before): Overriding __new__ to act as a factory, which is unexpected.

```python
# BAD: Overriding __new__ to return different types
class Payment:
    def __new__(cls, payment_type: str):
        if payment_type == "paypal":
            return object.__new__(PaypalPayment)
        elif payment_type == "card":
            return object.__new__(StripePayment)
        else:
            raise ValueError(f"Unsupported payment type: {payment_type}")

# Usage
my_payment = Payment("card") # Returns a StripePayment instance, not a Payment instance
```

Good:

Solution (After): Using an explicit factory function or a dictionary.

```python
# GOOD: Using a clear factory function
def get_payment_method(payment_type: str) -> Callable[[int], None]:
    if payment_type == "paypal":
        return pay_paypal
    elif payment_type == "card":
        return pay_stripe
    else:
        raise ValueError(f"Unsupported payment type: {payment_type}")

# Usage
payment_fn = get_payment_method("card")
payment_fn(100)```

21. Using Hardcoded Values

- Problem: Scattering hardcoded strings and other constant values (like URLs, UI text, or column names) directly throughout the codebase. This makes maintenance difficult and localization nearly impossible.
- Solution: Centralize constants and configuration. Define constants at the top of your module. For UI text and translations, use a dedicated localization service (like the video's sponsor, Lokalise) to manage all strings in one place and fetch them programmatically.

Problem (Before): UI strings are hardcoded directly in the code.

```python
# BAD: Hardcoded strings make changes and localization difficult
st.title("Uber pickups in NYC")
data_load_state = st.text("Loading data...")
# ...
st.subheader("Raw data")
```

Solution (After): Centralizing strings and fetching them via a key.

```python
# GOOD: Strings are managed externally and fetched by a key
translator = LokaliseTranslator(LANGUAGE) # Or any other translation system

st.title(translator("dashboard_title"))
data_load_state = st.text(translator("loading_data"))
# ...
st.subheader(translator("raw_data"))```

22. Design Pattern Overengineering

- Problem: Forcing complex, classic software design patterns (like the Abstract Factory pattern) into a simple problem where they are not needed. Python's dynamic nature often provides simpler, more direct solutions.
- Solution: Prioritize simplicity. Instead of building elaborate class hierarchies and factories, a simple dictionary mapping keys to functions can often achieve the same result with much less code and complexity.

Problem (Before): Using the complex Abstract Factory pattern for a simple task.

```python
# BAD: Over-engineered factory pattern
class Exporter(ABC):
    @abstractmethod
    def export(self, filename: str, report: Report) -> None:
        pass

class CSVExporter(Exporter):
    # ... implementation ...

class JSONExporter(Exporter):
    # ... implementation ...

class ExporterFactory:
    @staticmethod
    def get_exporter(format: str) -> Exporter:
        if format == "csv":
            return CSVExporter()
        elif format == "json":
            return JSONExporter()
        # ...

# Usage
exporter = ExporterFactory.get_exporter("json")
exporter.export("report.json", report)
```

Solution (After): Using a simple dictionary to map formats to functions.

```python
# GOOD: A simple dictionary mapping formats to functions
EXPORTERS = {
    "csv": export_to_csv,
    "json": export_to_json,
}

def get_exporter(format: str) -> ExportFn:
    if format in EXPORTERS:
        return EXPORTERS[format]
    raise ValueError("Unsupported export format")

# Usage
export_fn = get_exporter("json")
export_fn("report.json", report)```

23. Inappropriate Intimacy

- Problem: When one part of the code (e.g., an exporter function) knows too much about the internal structure of another object (e.g., a Report class). This tight coupling means that if the object's structure changes, all dependent functions must also be updated.
- Solution: Encapsulate the logic. The object should be responsible for its own data representations. Add methods to the object itself (e.g., to_csv(), to_json()) to handle the conversion, decoupling the external functions from its internal details.

Problem (Before): The exporter function knows the internal structure of the Report object.

Bad:

```python
# BAD: The exporter knows about 'report.title' and 'report.content'
def export_to_csv(filename: str, report: Report) -> None:
    csv_data = f"{report.title},{report.content}\n"
    with open(filename, "w") as f:
        f.write(csv_data)
```

Solution (After): The Report object knows how to represent itself as CSV.

Good:

```python
# GOOD: The Report class handles its own CSV conversion
@dataclass
class Report:
    title: str
    content: str

    def to_csv(self) -> str:
        return f"{self.title},{self.content}\n"

def export_to_csv(filename: str, report: Report) -> None:
    csv_data = report.to_csv()
    with open(filename, "w") as f:
        f.write(csv_data)```

24. Too Much Direct Coupling

- Problem: Functions are too tightly coupled to specific concrete classes (e.g., an export function that is type-hinted to only accept a Report object). This limits the reusability of the function for other types of objects that might also be exportable.
- Solution: Use a Protocol to define an interface (a form of structural subtyping, or "duck typing"). The function can then accept any object that conforms to that protocol, making it more generic, reusable, and decoupled.

Problem (Before): The export function is tied to the concrete Report class.

Bad:

```python
# BAD: The function only works with the 'Report' class
def export_to_csv(filename: str, report: Report) -> None:
    csv_data = report.to_csv()
    # ...
```

Good:

```python
# GOOD: The function works with any 'Exportable' object
class Exportable(Protocol):
    def to_csv(self) -> str: ...
    def to_json(self) -> str: ...

def export_to_csv(filename: str, report: Exportable) -> None:
    csv_data = report.to_csv()
    # ...

# Now, both Report and Budget classes can be exported if they have a to_csv method
@dataclass
class Budget:
    title: str
    amount: float
    def to_csv(self) -> str: ...```


25. Using Wildcard Imports

- Problem: Using from module import *. This pollutes the current namespace, makes it difficult to track where functions and classes come from, can lead to name conflicts, and hinders static analysis tools.
- Solution: Use explicit imports. Either import the module and use its namespace (e.g., import os; os.walk()) or import only the specific names you need (e.g., from os import walk).

Problem (Before): Importing everything from a module with *.

Bad:

```python
# BAD: Wildcard import pollutes the namespace and hides dependencies
from dataclasses import *

@dataclass
class Report:
    # ...
```

Solution (After): Importing only what is needed.

Good:

```python
# GOOD: Explicit import is clear and safe
from dataclasses import dataclass

@dataclass
class Report:
    # ...```

26. Not Using Built-in Tools and Libraries

- Problem: Reinventing the wheel by writing custom code for common tasks that are already solved efficiently by Python's standard library or mature third-party libraries.
- Solution: Leverage the rich Python ecosystem. Before writing a utility function, always check if a solution already exists in the standard library (e.g., os.walk, json module) or in a popular, well-maintained third-party package.

Problem (Before): Manually implementing functionality that already exists.

Bad:

```python
# BAD: Manually parsing a simple JSON string (conceptual example)
def parse_json_manually(json_string: str) -> dict:
    # Complex, error-prone logic to parse the string
    # ...
    return data
```

Solution (After): Using the robust, built-in json module.

Good:

```python
# GOOD: Using the standard library
import json

def parse_with_builtin(json_string: str) -> dict:
    return json.loads(json_string)
```


27. Move Method

The "Move Method" tip addresses a common code smell in object-oriented programming where a method is more closely associated with another class than the one it's currently in. This often happens when the method accesses data or behavior from the other class more frequently, leading to poor encapsulation and increased coupling.

Key Problem
A method is called or utilized more often by instances of another class than by its own class.

This can result in duplicated code, harder maintenance, and violations of the single responsibility principle.

Suggested Solution
- Identify the class that uses the method most.
- Create a new method in that target class, copying the relevant logic from the original method.
- Update the original method to delegate to the new one, or remove it if it's no longer needed.
- This improves code organization, reduces dependencies, and enhances readability.


Problem (Before): In this initial setup, ClassA has a method calculate_discount that's primarily called from ClassB, accessing ClassB's data more than its own.
Bad:

```python
class ClassA:
    def __init__(self, base_price):
        self.base_price = base_price

    def calculate_discount(self, customer_loyalty, seasonal_factor):
        # Logic that relies heavily on ClassB's data (passed in)
        discount = self.base_price * (customer_loyalty / 100) * seasonal_factor
        return discount

class ClassB:
    def __init__(self, loyalty_points, season):
        self.loyalty_points = loyalty_points
        self.season = season
        self.item = ClassA(100)  # Example base price

    def apply_discount(self):
        seasonal_factor = 1.0 if self.season == 'summer' else 0.8
        return self.item.calculate_discount(self.loyalty_points, seasonal_factor)

# Usage
customer = ClassB(50, 'winter')
print(customer.apply_discount())  # Output: 40.0
```

Solution (After): We move the method to ClassB, where it's used most. The original method in ClassA now delegates to the new one, but since it's rarely used in ClassA, we could eventually remove it.

Good:

```python
class ClassA:
    def __init__(self, base_price):
        self.base_price = base_price

    def calculate_discount(self, customer_loyalty, seasonal_factor):
        # Delegate to ClassB's method if needed, but ideally remove this
        # For demonstration, we'll keep a reference
        return self.base_price * (customer_loyalty / 100) * seasonal_factor  # Temporary delegation

class ClassB:
    def __init__(self, loyalty_points, season, item):
        self.loyalty_points = loyalty_points
        self.season = season
        self.item = item  # Reference to ClassA instance

    def calculate_discount(self):
        seasonal_factor = 1.0 if self.season == 'summer' else 0.8
        discount = self.item.base_price * (self.loyalty_points / 100) * seasonal_factor
        return discount

    def apply_discount(self):
        return self.calculate_discount()

# Usage
item = ClassA(100)
customer = ClassB(50, 'winter', item)
print(customer.apply_discount())  # Output: 40.0
```

28. Move Field

The "Move Field" tip targets a code smell in object-oriented design where a field (such as an attribute or variable) is more frequently accessed or modified by methods in another class than in its own. This misalignment can lead to tight coupling, reduced cohesion, and maintenance challenges, as the field doesn't belong where it's most relevant.

## Key Problem
- A field is accessed or used more often by another class, often requiring frequent passing of data between classes.
- This violates principles like encapsulation and single responsibility, potentially causing duplicated logic or unnecessary dependencies.

## Suggested Solution
- Identify the class that interacts most with the field.
- Create the field in that target class (which could be new or existing), and update all references to access it there, possibly via getter/setter methods.
- Redirect users of the old field to the new location, and remove the original if it's no longer needed.
- This enhances class cohesion by placing data closer to the behavior that uses it.

Problem (Before): Here, ClassA holds discount_rate, but ClassB frequently accesses it for customer-related calculations, passing data back and forth.

Bad:

```python
class ClassA:
    def __init__(self, base_price, discount_rate):
        self.base_price = base_price
        self.discount_rate = discount_rate  # Field mostly used in ClassB

class ClassB:
    def __init__(self, loyalty_points, season):
        self.loyalty_points = loyalty_points
        self.season = season
        self.item = ClassA(100, 0.1)  # Example base price and discount rate

    def calculate_discounted_price(self):
        seasonal_factor = 1.0 if self.season == 'summer' else 0.8
        # Accessing discount_rate from ClassA, but logic is tied to ClassB data
        discounted = self.item.base_price - (self.item.base_price * self.item.discount_rate * seasonal_factor)
        discounted -= (self.loyalty_points * 0.01)  # Additional logic using ClassB data
        return discounted

# Usage
customer = ClassB(50, 'winter')
print(customer.calculate_discounted_price())  # Output: 92.0
```


Solution (After): We move discount_rate to ClassB, where it's used most. References in ClassA are removed, and access is now direct within ClassB.

Good:

```python
class ClassA:
    def __init__(self, base_price):
        self.base_price = base_price  # discount_rate moved out

class ClassB:
    def __init__(self, loyalty_points, season, item):
        self.loyalty_points = loyalty_points
        self.season = season
        self.item = item  # Reference to ClassA instance
        self.discount_rate = 0.1  # Field now in ClassB

    def calculate_discounted_price(self):
        seasonal_factor = 1.0 if self.season == 'summer' else 0.8
        # Now uses local discount_rate, closer to related data
        discounted = self.item.base_price - (self.item.base_price * self.discount_rate * seasonal_factor)
        discounted -= (self.loyalty_points * 0.01)
        return discounted

# Usage
item = ClassA(100)
customer = ClassB(50, 'winter', item)
print(customer.calculate_discounted_price())  # Output: 92.0

```

29. Extract Class

The "Extract Class" tip focuses on a code smell in object-oriented programming where a single class takes on multiple responsibilities, violating the Single Responsibility Principle. This leads to bloated classes that are hard to understand, maintain, and extend, as unrelated functionalities become intertwined.

## Key Problem
- One class handles the work of multiple logical entities, resulting in low cohesion and increased complexity.
- This can cause issues like duplicated code, difficulty in testing, and challenges when modifying one aspect without affecting others.

## Suggested Solution
- Identify distinct responsibilities within the class.
- Create a new class to encapsulate one set of related fields and methods.
- Move the relevant fields and methods to the new class, establishing a relationship (e.g., composition) between the original and new classes.
- Update references accordingly to delegate to the new class.

Problem (Before): Here, the Order class handles everything, leading to a mix of item pricing and customer-specific logic.

Bad:

```python
class Order:
    def __init__(self, base_price, loyalty_points, season):
        self.base_price = base_price
        self.loyalty_points = loyalty_points
        self.season = season

    def calculate_discounted_price(self):
        seasonal_factor = 1.0 if self.season == 'summer' else 0.8
        discount = self.base_price * (self.loyalty_points / 100) * seasonal_factor
        return self.base_price - discount

# Usage
order = Order(100, 50, 'winter')
print(order.calculate_discounted_price())  # Output: 60.0

```

Solution (After): We extract customer-related fields and logic into a new Customer class. The Order class now composes a Customer instance and delegates accordingly.

Good:

```python
class Customer:
    def __init__(self, loyalty_points, season):
        self.loyalty_points = loyalty_points
        self.season = season

    def get_discount_factor(self):
        seasonal_factor = 1.0 if self.season == 'summer' else 0.8
        return (self.loyalty_points / 100) * seasonal_factor

class Order:
    def __init__(self, base_price, customer):
        self.base_price = base_price
        self.customer = customer  # Reference to Customer instance

    def calculate_discounted_price(self):
        discount = self.base_price * self.customer.get_discount_factor()
        return self.base_price - discount

# Usage
customer = Customer(50, 'winter')
order = Order(100, customer)
print(order.calculate_discounted_price())  # Output: 60.0
```

30. Inline Class

The "Inline Class" tip addresses a code smell in object-oriented design where a class has minimal functionality, lacks significant responsibilities, and isn't expected to grow. This often occurs after other refactorings, like extracting features, leave a class underutilized, resulting in unnecessary complexity and overhead.

## Key Problem
- A class performs little to no meaningful work, with its fields and methods rarely used or easily absorbable elsewhere.
- This leads to bloated codebases, increased cognitive load, and wasted resources, violating principles of simplicity and efficiency.

## Suggested Solution
- Identify a more appropriate class to absorb the trivial class's features.
- Move all fields and methods from the trivial class to the target class, updating references accordingly.
- Delete the original class once it's empty and all usages are redirected.
- This reduces indirection and simplifies the structure.

Problem (Before): Here, the Discount class is minimal, merely storing a rate and providing a simple calculation, but it's not responsible for much and could be integrated into Order.

Bad:

```python
class Discount:
    def __init__(self, rate):
        self.rate = rate  # Trivial field

    def apply(self, price):
        return price * self.rate  # Basic method, no real responsibility

class Order:
    def __init__(self, base_price, discount):
        self.base_price = base_price
        self.discount = discount  # Reference to trivial Discount class

    def final_price(self):
        return self.base_price - self.discount.apply(self.base_price)

# Usage
discount = Discount(0.1)
order = Order(100, discount)
print(order.final_price())  # Output: 90.0
```

Solution (After): We move the rate field and apply method into Order, eliminating the Discount class entirely and updating references.

Good:

```python
class Order:
    def __init__(self, base_price, rate):
        self.base_price = base_price
        self.rate = rate  # Field moved from Discount

    def apply_discount(self):  # Method moved and renamed for clarity
        return self.base_price * self.rate

    def final_price(self):
        return self.base_price - self.apply_discount()

# Usage
order = Order(100, 0.1)
print(order.final_price())  # Output: 90.0
```

31. Hide Delegate

The "Hide Delegate" tip addresses a code smell in object-oriented design where client code directly accesses and interacts with a delegate object (object B) through a server object (object A), leading to tight coupling and exposure of internal structures. This can make the system harder to maintain, as changes to the delegate affect all clients.

## Key Problem
- Client code must know about the internal relationships between classes, such as navigating from object A to object B to call methods on B.
- This increases coupling, violates encapsulation, and makes refactoring riskier since clients depend on the delegate's interface.

##Suggested Solution
- Add delegating methods to class A that forward calls to class B, hiding the delegate from the client.
- Update client code to use these new methods on class A, reducing direct dependencies.
- If no clients need direct access to class B, remove the accessor method in class A that exposes it.
- In Python, this is straightforward with dynamic typing, but use properties or methods to control access and maintain encapsulation.

Problem (Before): Here, the client must know about Department and call its method, exposing the internal structure.

Bad:

```python
class Department:
    def __init__(self, manager_name):
        self.manager_name = manager_name

    def get_manager(self):
        return self.manager_name

class Employee:
    def __init__(self, name, department):
        self.name = name
        self.department = department  # Exposes delegate

# Client code
employee = Employee("Alice", Department("Bob"))
manager = employee.department.get_manager()  # Direct access to delegate
print(manager)  # Output: Bob
```

Solution (After): We add a get_manager method to Employee that delegates to Department, and remove direct access to the department attribute for better hiding.
Good:

```python
class Department:
    def __init__(self, manager_name):
        self.manager_name = manager_name

    def get_manager(self):
        return self.manager_name

class Employee:
    def __init__(self, name, department):
        self.name = name
        self._department = department  # Hidden with underscore

    def get_manager(self):
        return self._department.get_manager()  # Delegates the call

# Client code
employee = Employee("Alice", Department("Bob"))
manager = employee.get_manager()  # Calls delegating method
print(manager)  # Output: Bob

```

32. Remove Middle Man

The "Remove Middle Man" tip tackles a code smell in object-oriented design where a class acts excessively as a middleman, providing numerous delegating methods that simply forward calls to another object. This often arises after applying other refactorings like Hide Delegate, leading to unnecessary indirection and complexity without adding value.

## Key Problem
- A class is cluttered with methods that do nothing but delegate to methods on a composed or associated object.
- This increases indirection, making code harder to follow, and hides the true structure, potentially violating the Law of Demeter by encouraging indirect access.

## Suggested Solution
- Expose the delegate object (or relevant parts) to the client via a getter if needed.
- Remove the unnecessary delegating methods from the middleman class.
- Update client code to call the delegate's methods directly, simplifying the interface.
- In Python, this is efficient with dynamic attributes, but balance it with encapsulation—only expose what's necessary to avoid tight coupling.

Problem (Before): Here, Employee has several methods that merely delegate to Department, adding unnecessary layers without real functionality.

Bad:

```python
class Department:
    def __init__(self, manager_name, location):
        self.manager_name = manager_name
        self.location = location

    def get_manager(self):
        return self.manager_name

    def get_location(self):
        return self.location

    def set_location(self, new_location):
        self.location = new_location

class Employee:
    def __init__(self, name, department):
        self.name = name
        self._department = department  # Hidden delegate

    # Delegating methods
    def get_manager(self):
        return self._department.get_manager()

    def get_department_location(self):
        return self._department.get_location()

    def set_department_location(self, new_location):
        self._department.set_location(new_location)

# Client code
employee = Employee("Alice", Department("Bob", "New York"))
print(employee.get_manager())  # Output: Bob
print(employee.get_department_location())  # Output: New York
employee.set_department_location("San Francisco")
print(employee.get_department_location())  # Output: San Francisco
```

Solution (After): We remove the delegating methods from Employee and provide a getter for the department, allowing the client to call methods directly on it.

Good:

```python
class Department:
    def __init__(self, manager_name, location):
        self.manager_name = manager_name
        self.location = location

    def get_manager(self):
        return self.manager_name

    def get_location(self):
        return self.location

    def set_location(self, new_location):
        self.location = new_location

class Employee:
    def __init__(self, name, department):
        self.name = name
        self._department = department

    def get_department(self):
        return self._department  # Expose delegate for direct access

# Client code
employee = Employee("Alice", Department("Bob", "New York"))
department = employee.get_department()
print(department.get_manager())  # Output: Bob
print(department.get_location())  # Output: New York
department.set_location("San Francisco")
print(department.get_location())  # Output: San Francisco
```

33. Introduce Foreign Method

The "Introduce Foreign Method" tip handles a situation in object-oriented programming where you need additional functionality from a utility or server class, but you can't modify it directly—often because it's part of a library, built-in, or external code. This refactoring adds the missing method to a client class instead, passing the utility object as an argument to make it work, acting as a temporary workaround until the utility class can be extended or wrapped.

## Key Problem
- A utility class lacks a required method, and you can't alter it, forcing awkward or duplicated code in clients to compensate.
- This leads to scattered logic, reduced readability, and potential duplication across multiple client classes.

## Suggested Solution
- Create the new method in the client class, with the utility object as a parameter (or accessed via self if available).
- Extract the relevant logic into this method and replace original code with calls to it.
- Mark the method with a comment noting it's a foreign method that ideally belongs in the utility class for future reference.
- In Python, this is useful for built-ins like datetime, where you can't add methods directly, promoting cohesion without violating encapsulation.

Problem (Before): Here, the Billing class has inline logic to compute the next week's date from a given previous_date, duplicating what could be a reusable method on datetime.

Bad:

```python
from datetime import datetime, timedelta

class Billing:
    def __init__(self, previous_date):
        self.previous_date = previous_date

    def get_next_billing_date(self):
        # Inline logic to get date one week later
        next_date = self.previous_date + timedelta(days=7)
        return next_date

# Usage
previous = datetime(2025, 7, 1)
billing = Billing(previous)
print(billing.get_next_billing_date())  # Output: 2025-07-08 00:00:00
```

Solution (After): We introduce a foreign method next_week in Billing that takes a datetime object as an argument, encapsulating the logic. The original method now calls this foreign method.

Good:

```python
from datetime import datetime, timedelta

class Billing:
    def __init__(self, previous_date):
        self.previous_date = previous_date

    def get_next_billing_date(self):
        return self.next_week(self.previous_date)

    # Foreign method: Should ideally be in datetime if modifiable
    def next_week(self, date):
        return date + timedelta(days=7)

# Usage
previous = datetime(2025, 7, 1)
billing = Billing(previous)
print(billing.get_next_billing_date())  # Output: 2025-07-08 00:00:00
```

34. Introduce Local Extension

The "Introduce Local Extension" tip addresses a limitation in object-oriented programming when a utility or third-party class lacks necessary methods, and direct modification isn't possible (e.g., due to it being a library or built-in class). This refactoring creates a local extension to add the required functionality without altering the original class, promoting better code organization and reusability.

## Key Problem
- A utility class is missing methods needed for specific tasks, leading to duplicated or scattered logic in client code.
- You can't modify the utility class, which forces workarounds like inline code or foreign methods, increasing complexity and maintenance issues.

## Suggested Solution
- Create a new extension class that either subclasses the utility class (inheriting its behavior) or acts as a wrapper (delegating to an instance of the utility class).
- Add the missing methods to this extension class.
- Use the extension class in place of the original where the new functionality is needed, possibly with a converting constructor for easy substitution.
- In Python, subclassing is often simpler for built-in classes like datetime, but wrappers are useful if subclassing is restricted; this approach avoids polluting client classes with unrelated methods.

Problem (Before): Here, the Billing class contains inline logic for adding a week to a date, which could lead to duplication if similar operations are needed elsewhere.

Bad:

```python
from datetime import datetime, timedelta

class Billing:
    def __init__(self, previous_date):
        self.previous_date = previous_date

    def get_next_billing_date(self):
        # Inline logic to add one week
        next_date = self.previous_date + timedelta(days=7)
        return next_date

# Usage
previous = datetime(2025, 7, 1)
billing = Billing(previous)
print(billing.get_next_billing_date())  # Output: 2025-07-08 00:00:00
```

Solution (After): We create an ExtendedDate subclass of datetime to add the next_week method. The Billing class now uses ExtendedDate for the calculation, keeping logic centralized.

Good:

```python
from datetime import datetime, timedelta

class ExtendedDate(datetime):
    # Subclass of datetime to add local extensions
    def next_week(self):
        return self + timedelta(days=7)

    @classmethod
    def from_datetime(cls, dt):
        # Converting constructor for easy substitution
        return cls(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

class Billing:
    def __init__(self, previous_date):
        self.previous_date = ExtendedDate.from_datetime(previous_date)

    def get_next_billing_date(self):
        return self.previous_date.next_week()

# Usage
previous = datetime(2025, 7, 1)
billing = Billing(previous)
print(billing.get_next_billing_date())  # Output: 2025-07-08 00:00:00
```

35. Self Encapsulate Field

The "Self Encapsulate Field" tip addresses a code smell in object-oriented programming where even within the same class, private fields are accessed directly, bypassing potential validation, computation, or future-proofing. This can make it harder to add logic around field access later, such as lazy loading or constraints, and reduces flexibility for subclasses.

##Key Problem
- Direct access to fields inside the class skips encapsulation, making changes (like adding validation) require updates in multiple places.
- This can lead to brittle code, especially in inheritance hierarchies where subclasses might need to override access behavior.

## Suggested Solution
- Introduce getter and setter methods (or properties in Python) for the field.
- Replace all direct accesses within the class with calls to these methods.
- This centralizes access logic, enabling easier modifications and better adherence to encapsulation principles.
- In Python, using the @property decorator for getters and @field.setter for setters is idiomatic, providing a clean way to encapsulate without changing the external interface.

Problem (Before): Here, the Product class directly reads and writes to _price in its methods, which could complicate adding price validation or discounts later.

Bad:

```python
class Product:
    def __init__(self, name, price):
        self.name = name
        self._price = price  # Private field

    def apply_discount(self, discount):
        # Direct access to _price
        self._price -= self._price * discount
        return self._price

    def get_total(self, quantity):
        # Direct access to _price
        return self._price * quantity

# Usage
product = Product("Laptop", 1000)
product.apply_discount(0.1)
print(product.get_total(2))  # Output: 1800.0
```

Solution (After): We introduce property-based getter and setter for _price, replacing direct accesses with calls to these. This allows potential future logic in the accessors.

Good:

```python
class Product:
    def __init__(self, name, price):
        self.name = name
        self._price = price  # Still private

    @property
    def price(self):
        return self._price  # Getter

    @price.setter
    def price(self, value):
        self._price = value  # Setter, can add validation here if needed

    def apply_discount(self, discount):
        # Use getter and setter
        self.price -= self.price * discount
        return self.price

    def get_total(self, quantity):
        # Use getter
        return self.price * quantity

# Usage
product = Product("Laptop", 1000)
product.apply_discount(0.1)
print(product.get_total(2))  # Output: 1800.0
```

36. Replace Data Value with Object

The "Replace Data Value with Object" tip targets a code smell in object-oriented design where a simple data field (like a primitive type or basic structure) starts accumulating associated behavior and data, but remains a mere value without its own encapsulation. This can lead to duplicated logic across classes, poor organization, and difficulty in extending or maintaining the related functionality.

## Key Problem
- A data field has implicit behavior (e.g., validation, formatting, or calculations) tied to it, scattered throughout the class or multiple classes.
- Using primitives limits reusability and violates encapsulation, as the field doesn't manage its own state and operations, potentially causing errors or redundancy.

## Suggested Solution
- Create a new class to represent the data value as an object, moving the field and all related behavior (methods) into it.
- Replace the original field with an instance of this new class in the containing class(es).
- Update any code that used the old field to interact with the new object's methods, improving cohesion and allowing the object to handle its own concerns.
- In Python, this is effective for turning primitives like strings or numbers into rich objects, especially when the data grows in complexity.

Problem (Before): Here, customer_address is a plain string, but the Order class contains methods that manipulate it, mixing concerns and potentially leading to duplication if address logic is needed elsewhere.

Bad:

```python
class Order:
    def __init__(self, item, customer_address):
        self.item = item
        self.customer_address = customer_address  # Simple string field

    def format_shipping_label(self):
        # Behavior tied to the address field
        if not self.customer_address:
            raise ValueError("Address cannot be empty")
        formatted = self.customer_address.upper()  # Example formatting
        return f"Ship to: {formatted}"

    def is_valid_address(self):
        # More behavior: basic validation
        return len(self.customer_address) > 5 and ',' in self.customer_address

# Usage
order = Order("Laptop", "123 Main St, City, State")
print(order.format_shipping_label())  # Output: Ship to: 123 MAIN ST, CITY, STATE
print(order.is_valid_address())  # Output: True
```

Solution (After): We create an Address class to hold the data and its behavior. The Order class now stores an Address instance and delegates to it, cleaning up the structure.

Good:

```python
class Address:
    def __init__(self, value):
        self.value = value  # The original field, now encapsulated

    def format_for_shipping(self):
        if not self.value:
            raise ValueError("Address cannot be empty")
        return self.value.upper()  # Formatting logic moved here

    def is_valid(self):
        # Validation logic moved here
        return len(self.value) > 5 and ',' in self.value

class Order:
    def __init__(self, item, customer_address):
        self.item = item
        self.customer_address = Address(customer_address)  # Now an object

    def format_shipping_label(self):
        formatted = self.customer_address.format_for_shipping()
        return f"Ship to: {formatted}"

    def is_valid_address(self):
        return self.customer_address.is_valid()

# Usage
order = Order("Laptop", "123 Main St, City, State")
print(order.format_shipping_label())  # Output: Ship to: 123 MAIN ST, CITY, STATE
print(order.is_valid_address())  # Output: True
```

37. Change Value to Reference

- Core Idea: This refactoring tip addresses scenarios where you have multiple identical instances of a class (often treated as "value objects" with equality based on their data, like strings or integers in Python). If these instances are immutable and frequently duplicated, it can lead to inefficiencies in memory, performance, or consistency (e.g., modifying one instance doesn't affect others when it should). The solution is to replace them with a single shared "reference object" (e.g., using a factory pattern, singleton-like behavior, or a registry/cache to ensure only one instance exists per unique identity).
- When to Apply: Use this when objects are logically the same (e.g., all "USD" currency objects) and should behave as shared references rather than independent values. This promotes the Flyweight pattern, reduces memory usage, and ensures consistency (e.g., changes to the shared object are reflected everywhere).

## Python-Specific Style Suggestions

- Pros: Python's garbage collection and dynamic typing make this easy to implement with dictionaries (for caching) or class methods (as factories). It aligns with Python's "duck typing" and immutability best practices (e.g., using __hash__ and __eq__ for equality).
- Cons/Risks: Overusing references can lead to unintended side effects if the object is mutable. Ensure the reference object is immutable or carefully managed.
- Style Guidelines: Follow PEP 8 for naming/class structure. Use descriptive names, docstrings, and type hints (via typing) for clarity. Avoid global state if possible; prefer class-level caches.
- Benefits in Python: Improves performance in large-scale apps (e.g., web servers handling repeated data like currencies or colors).

Problem (Before): Here, every time you create a Currency, you get a new instance—even if the data (code and symbol) is identical. This leads to duplication, higher memory use, and inconsistency if you ever need to update shared properties.

Bad:

```python
# before.py
class Currency:
    def __init__(self, code: str, symbol: str):
        self.code = code
        self.symbol = symbol

    def __eq__(self, other):
        if isinstance(other, Currency):
            return self.code == other.code and self.symbol == other.symbol
        return False

    def __hash__(self):
        return hash((self.code, self.symbol))

    def __repr__(self):
        return f"Currency(code='{self.code}', symbol='{self.symbol}')"

# Usage: Creating multiple identical instances
usd1 = Currency("USD", "$")
usd2 = Currency("USD", "$")
eur = Currency("EUR", "€")

print(usd1)  # Currency(code='USD', symbol='$')
print(usd2)  # Currency(code='USD', symbol='$')
print(usd1 == usd2)  # True (equal values, but different objects)
print(usd1 is usd2)  # False (different references)
print(f"Memory addresses: {id(usd1)} vs {id(usd2)}")  # Different IDs, wasting memory
```

Solution (After): We introduce a class-level cache (a dictionary) and a factory method (get_currency) to ensure only one instance per unique code exists. Now, identical requests return the same reference object.

Good:

```python
# after.py
from typing import Dict

class Currency:
    _cache: Dict[str, 'Currency'] = {}  # Class-level cache for references

    def __init__(self, code: str, symbol: str):
        self.code = code
        self.symbol = symbol

    @classmethod
    def get_currency(cls, code: str, symbol: str) -> 'Currency':
        """Factory method to get or create a shared Currency reference."""
        key = code.upper()  # Normalize for uniqueness
        if key not in cls._cache:
            instance = cls(key, symbol)
            cls._cache[key] = instance
        return cls._cache[key]

    def __eq__(self, other):
        if isinstance(other, Currency):
            return self.code == other.code and self.symbol == other.symbol
        return False

    def __hash__(self):
        return hash((self.code, self.symbol))

    def __repr__(self):
        return f"Currency(code='{self.code}', symbol='{self.symbol}')"

# Usage: Now uses shared references
usd1 = Currency.get_currency("USD", "$")
usd2 = Currency.get_currency("usd", "$")  # Same as above, case-insensitive
eur = Currency.get_currency("EUR", "€")

print(usd1)  # Currency(code='USD', symbol='$')
print(usd2)  # Currency(code='USD', symbol='$')
print(usd1 == usd2)  # True (equal values)
print(usd1 is usd2)  # True (same reference!)
print(f"Memory addresses: {id(usd1)} vs {id(usd2)}")  # Same ID, efficient

# Demonstrate sharing: Add a mutable property and update
usd1.exchange_rate = 1.0  # Hypothetical mutable property
print(usd2.exchange_rate)  # 1.0 (reflected in shared reference)
```

38. Change Reference to Value

- Core Idea: This refactoring tip is the inverse of "Change Value to Reference." It applies when you have a shared reference object (e.g., managed via a factory or cache for uniqueness) that is small, immutable, and rarely modified. Managing its life cycle (e.g., ensuring a single instance) becomes unnecessary overhead. The solution is to convert it into a value object: create independent, immutable instances where equality is based on data (not identity), similar to Python's built-in types like strings or tuples.
- When to Apply: Use this when the object doesn't need shared state or life cycle management (e.g., no frequent updates that must propagate). It's ideal for small, stable data like colors, dates, or units where immutability prevents side effects and simplifies usage.

##Python-Specific Style Suggestions

- Pros: Python's emphasis on immutability (e.g., via frozen dataclasses or namedtuples) makes value objects natural and efficient. They align with hashability for use in sets/dicts and support equality checks via __eq__ and __hash__.
- Cons/Risks: If the object later needs mutable shared state, this could introduce bugs. Avoid if frequent changes are anticipated.
- Style Guidelines: Follow PEP 8 for clarity, use dataclasses (with frozen=True) or collections.namedtuple for immutability, and include type hints. Ensure objects are hashable for collections.
- Benefits in Python: Reduces complexity by eliminating caches/factories, improves performance in scenarios with many instances (no shared state overhead), and enhances thread safety due to immutability.

Problem (Before): Here, Currency uses a factory and cache to ensure a single shared instance per code. This manages life cycle but adds unnecessary complexity for a small, static object like currency (which rarely changes).

Bad:

```python
# before.py
# before.py
from typing import Dict

class Currency:
    _cache: Dict[str, 'Currency'] = {}  # Class-level cache for shared references

    def __init__(self, code: str, symbol: str):
        self.code = code
        self.symbol = symbol

    @classmethod
    def get_currency(cls, code: str, symbol: str) -> 'Currency':
        """Factory method to get or create a shared Currency reference."""
        key = code.upper()  # Normalize for uniqueness
        if key not in cls._cache:
            instance = cls(key, symbol)
            cls._cache[key] = instance
        return cls._cache[key]

    def __eq__(self, other):
        if isinstance(other, Currency):
            return self.code == other.code and self.symbol == other.symbol
        return False

    def __hash__(self):
        return hash((self.code, self.symbol))

    def __repr__(self):
        return f"Currency(code='{self.code}', symbol='{self.symbol}')"

# Usage: Shared references via factory
usd1 = Currency.get_currency("USD", "$")
usd2 = Currency.get_currency("usd", "$")  # Same reference
eur = Currency.get_currency("EUR", "€")

print(usd1)  # Currency(code='USD', symbol='$')
print(usd2)  # Currency(code='USD', symbol='$')
print(usd1 == usd2)  # True (equal values)
print(usd1 is usd2)  # True (same reference)
print(f"Memory addresses: {id(usd1)} vs {id(usd2)}")  # Same ID
```

Solution (After): We remove the cache and factory, making Currency an immutable value object (using dataclasses with frozen=True). Each creation yields a new instance, with equality based on values. This simplifies the code while preserving behavior for static data.

Good:

```python
# after.py
from dataclasses import dataclass

@dataclass(frozen=True)  # Immutable value object
class Currency:
    code: str
    symbol: str

    def __post_init__(self):
        # Normalize code for consistency (optional, but keeps robustness)
        object.__setattr__(self, 'code', self.code.upper())

    def __repr__(self):
        return f"Currency(code='{self.code}', symbol='{self.symbol}')"

# Usage: Create independent value objects directly
usd1 = Currency("USD", "$")
usd2 = Currency("usd", "$")  # New instance, but equal in value
eur = Currency("EUR", "€")

print(usd1)  # Currency(code='USD', symbol='$')
print(usd2)  # Currency(code='USD', symbol='$')
print(usd1 == usd2)  # True (equal values, via dataclass __eq__)
print(usd1 is usd2)  # False (different references, as values)
print(f"Memory addresses: {id(usd1)} vs {id(usd2)}")  # Different IDs, no sharing needed
```

39. Replace Array with Object

- Core Idea: This refactoring addresses arrays (or lists in Python) that store heterogeneous data in fixed positions, like using indices to represent different attributes (e.g., index 0 for a name, index 1 for a score). This can lead to brittle code, as changing the array structure breaks assumptions. The solution is to replace the array with a dedicated object (e.g., a class) where each piece of data becomes a named field, improving clarity and maintainability.
- When to Apply: Use this when an array acts like a "record" with mixed types but lacks self-documenting structure, especially in growing codebases where data is accessed repeatedly. It's a special case of replacing primitive data values with objects, promoting better encapsulation.

## Python-Specific Style Suggestions

- Pros: Python's classes, dataclasses (from Python 3.7+), or namedtuples make this straightforward and readable. It aligns with Python's emphasis on explicit, self-documenting code and reduces index-related errors.
- Cons/Risks: If the data is truly a simple, uniform collection (e.g., all integers), an object might add unnecessary overhead. Ensure the new class is immutable if the data shouldn't change.
- Style Guidelines: Follow PEP 8 for naming and structure; use descriptive field names, type hints, and docstrings. Prefer dataclasses for simplicity or collections.namedtuple for lightweight, hashable objects.
- Benefits in Python: Enhances readability (no magic indices), enables adding methods (e.g., for validation), and supports better type checking with tools like mypy.

Problem (Before): Here, data is crammed into a list with fixed indices, making access unclear and prone to off-by-one errors or type mismatches.

Bad:

```python
# before.py
# Example data: [team_name, wins]
team = ["Liverpool", 15]

# Usage: Accessing via magic indices
team_name = team[0]  # Assumes index 0 is name (str)
wins = int(team[1])  # Assumes index 1 is wins (needs casting if not int)

print(f"Team: {team_name}, Wins: {wins}")  # Team: Liverpool, Wins: 15

# Processing multiple teams (error-prone if structure changes)
teams = [["Liverpool", 15], ["Manchester", 12]]
for t in teams:
    print(f"Team: {t[0]}, Wins: {int(t[1])}")
```

Solution (After): We create a TeamPerformance class using dataclasses for conciseness. Each data element becomes a typed, named field, eliminating indices.

Good:

```python
# after.py
from dataclasses import dataclass

@dataclass
class TeamPerformance:
    """Represents a team's performance with named fields."""
    name: str
    wins: int

# Usage: Direct instantiation and access
team = TeamPerformance("Liverpool", 15)

print(f"Team: {team.name}, Wins: {team.wins}")  # Team: Liverpool, Wins: 15

# Processing multiple teams (clear and extensible)
teams = [TeamPerformance("Liverpool", 15), TeamPerformance("Manchester", 12)]
for t in teams:
    print(f"Team: {t.name}, Wins: {t.wins}")

# Easy to extend: Add methods or fields (e.g., for validation)
@dataclass
class TeamPerformance:
    name: str
    wins: int

    def __post_init__(self):
        if self.wins < 0:
            raise ValueError("Wins cannot be negative")
```

40. Comments as a Code Smell

- When a comment explains *what* a block of code does, it's a sign that block should be extracted into a named method.
- A comment describing a section is the method name waiting to be extracted.
- Comments explaining *why* something is done are valuable and should be kept.
- Rule: "If you feel the need to comment a block, extract it and name it instead."

## Example

```python
# Bad: each comment is a disguised method name
def process_order(order):
    # Validate order items
    for item in order.items:
        if item.quantity <= 0:
            raise ValueError(f"Invalid quantity: {item.quantity}")
        if item.price < 0:
            raise ValueError(f"Invalid price: {item.price}")

    # Calculate subtotal with tax
    subtotal = sum(item.price * item.quantity for item in order.items)
    tax = subtotal * 0.2
    total = subtotal + tax

    # Apply loyalty discount if eligible
    if order.customer.loyalty_points > 100:
        total *= 0.95

    return total


# Good: comment text becomes the method name — intent is self-documenting
def process_order(order):
    validate_order_items(order.items)
    total = calculate_total_with_tax(order.items)
    return apply_loyalty_discount(total, order.customer)


def validate_order_items(items: list) -> None:
    for item in items:
        if item.quantity <= 0:
            raise ValueError(f"Invalid quantity: {item.quantity}")
        if item.price < 0:
            raise ValueError(f"Invalid price: {item.price}")


def calculate_total_with_tax(items: list, tax_rate: float = 0.2) -> float:
    subtotal = sum(item.price * item.quantity for item in items)
    return subtotal * (1 + tax_rate)


def apply_loyalty_discount(total: float, customer, threshold: int = 100) -> float:
    if customer.loyalty_points > threshold:
        return total * 0.95
    return total
```

When to keep comments:
- Explaining *why* a non-obvious approach was chosen
- Documenting complex algorithms where all simplification options are exhausted
- Public API docstrings (always valuable)

41. Separate Query from Modifier (Command-Query Separation)

- Problem: A method both returns a value AND changes the state of an object. This violates the Command-Query Separation (CQS) principle.
- Solution: Split the method into two — one that queries (returns a value, no side effects) and one that modifies (changes state, returns nothing).
- Rule: A method should either answer a question about the world, or change the world — but never both.

## Key Problem
- When a method returns a result while also modifying state, callers cannot safely call it multiple times.
- Side effects hidden inside a "query" method cause surprising bugs that are hard to trace.
- The intent of calling the method is ambiguous: are you fetching data, or triggering an action?

## Suggested Solution
- Create a pure query method that returns the value without side effects.
- Create a separate modifier method that changes state and returns nothing.
- Have callers invoke the modifier first, then the query if they need the result.

Problem (Before): get_next_available_seat does two things — it finds a seat AND marks it as taken.

Bad:

```python
class Theater:
    def __init__(self, seats: list[str]):
        self._seats = {seat: True for seat in seats}  # True = available

    def get_next_available_seat(self) -> str | None:
        for seat, available in self._seats.items():
            if available:
                self._seats[seat] = False  # SIDE EFFECT: marks seat as taken!
                return seat
        return None

# Calling it twice produces different results — confusing!
theater = Theater(["A1", "A2", "A3"])
seat1 = theater.get_next_available_seat()  # Returns "A1", marks it taken
seat2 = theater.get_next_available_seat()  # Returns "A2", not "A1" again
```

Solution (After): Split into find_next_available_seat (pure query) and reserve_seat (modifier).

Good:

```python
class Theater:
    def __init__(self, seats: list[str]):
        self._seats = {seat: True for seat in seats}

    def find_next_available_seat(self) -> str | None:
        """Pure query — no side effects. Safe to call multiple times."""
        for seat, available in self._seats.items():
            if available:
                return seat
        return None

    def reserve_seat(self, seat: str) -> None:
        """Modifier — changes state, returns nothing."""
        if seat not in self._seats:
            raise ValueError(f"Unknown seat: {seat}")
        if not self._seats[seat]:
            raise ValueError(f"Seat {seat} is already taken")
        self._seats[seat] = False

# Usage: explicit, predictable, composable
theater = Theater(["A1", "A2", "A3"])
seat = theater.find_next_available_seat()
if seat:
    theater.reserve_seat(seat)
```

42. Introduce Parameter Object

- Problem: A repeating group of parameters travels together across multiple method signatures. Every time you add a field to this group, you must update every signature.
- Solution: Bundle the group into a single @dataclass or NamedTuple. This eliminates the scattered duplication and creates a natural home for related behavior and validation.
- Complements Tip #10 (Keyword-Only Arguments). Use parameter objects when the same group appears in multiple places.

## Key Problem
- The same parameters (e.g., start_date, end_date, granularity) appear in 3+ method signatures — this is a Data Clump.
- Adding or changing one parameter means updating every method and every call site.
- Related validation (end must be after start) is duplicated or missing.

## Suggested Solution
- Create a @dataclass to hold the related parameters.
- Add validation and helper methods to the dataclass.
- Replace the parameter group across all methods with the new object.

Problem (Before): date range parameters repeat across every reporting function.

Bad:

```python
from datetime import date

def generate_sales_report(start_date: date, end_date: date, granularity: str):
    ...

def fetch_analytics(start_date: date, end_date: date, granularity: str):
    ...

def export_csv(data, start_date: date, end_date: date, granularity: str, filename: str):
    ...

# Every call site repeats the same 3 args
report = generate_sales_report(date(2025, 1, 1), date(2025, 3, 31), "monthly")
data = fetch_analytics(date(2025, 1, 1), date(2025, 3, 31), "monthly")
export_csv(data, date(2025, 1, 1), date(2025, 3, 31), "monthly", "q1.csv")
```

Solution (After): DateRange is a self-contained object with its own validation and helpers.

Good:

```python
from dataclasses import dataclass
from datetime import date

@dataclass
class DateRange:
    start: date
    end: date
    granularity: str = "monthly"

    def __post_init__(self):
        if self.end < self.start:
            raise ValueError("end must be after start")

    def duration_days(self) -> int:
        return (self.end - self.start).days


def generate_sales_report(date_range: DateRange):
    ...

def fetch_analytics(date_range: DateRange):
    ...

def export_csv(data, date_range: DateRange, filename: str):
    ...

# Clean, single object at every call site
q1 = DateRange(date(2025, 1, 1), date(2025, 3, 31))
report = generate_sales_report(q1)
data = fetch_analytics(q1)
export_csv(data, q1, "q1.csv")
```

43. Preserve Whole Object

- Problem: Multiple values are extracted from an object and then passed as separate parameters to a method. The method knows too much about the caller's internal structure.
- Solution: Pass the whole object instead of its individually extracted values. This reduces the parameter list and isolates the method from structural changes in the source object.
- Warning: This creates a dependency on the object type. Don't apply it if the method should remain generic and work with many different types.

## Key Problem
- Extracting values and passing them separately spreads knowledge of an object's structure to every call site.
- When the source object gains new fields the method needs, you must update every caller.

## Suggested Solution
- Refactor the method to accept the whole source object as a parameter.
- Remove the individually extracted parameters.
- Let the method access only what it needs from the object directly.

Problem (Before): Three fields are extracted from room and passed to is_within_plan separately.

Bad:

```python
@dataclass
class Room:
    min_temp: float
    max_temp: float
    humidity: float

class HeatingPlan:
    def __init__(self, low: float, high: float):
        self._low = low
        self._high = high

    def is_within_plan(self, min_temp: float, max_temp: float) -> bool:
        return min_temp >= self._low and max_temp <= self._high

# Caller must extract fields and pass them individually — fragile
room = Room(min_temp=15.0, max_temp=22.0, humidity=55.0)
plan = HeatingPlan(low=18.0, high=24.0)
within = plan.is_within_plan(room.min_temp, room.max_temp)
```

Solution (After): Pass the whole Room — adding Room fields later doesn't change the caller.

Good:

```python
@dataclass
class Room:
    min_temp: float
    max_temp: float
    humidity: float

class HeatingPlan:
    def __init__(self, low: float, high: float):
        self._low = low
        self._high = high

    def is_within_plan(self, room: Room) -> bool:
        return room.min_temp >= self._low and room.max_temp <= self._high

# Clean call site — the method decides what it needs from the object
room = Room(min_temp=15.0, max_temp=22.0, humidity=55.0)
plan = HeatingPlan(low=18.0, high=24.0)
within = plan.is_within_plan(room)
```

44. Replace Temp with Query

- A local variable that stores a computed result can often be replaced with a method that computes it on demand.
- This enables Extract Method on code that would otherwise be blocked by the temporary variable.
- It also makes the computation reusable in other methods of the same class.

## Example

```python
class Order:
    def __init__(self, quantity: int, item_price: float):
        self.quantity = quantity
        self.item_price = item_price

    # Bad: base_price is a temp variable blocking method extraction
    def calculate_total(self) -> float:
        base_price = self.quantity * self.item_price
        if base_price > 1000:
            return base_price * 0.95
        return base_price * 0.98

    # Good: extracted to a method — now reusable across the entire class
    def base_price(self) -> float:
        return self.quantity * self.item_price

    def calculate_total(self) -> float:
        if self.base_price() > 1000:
            return self.base_price() * 0.95
        return self.base_price() * 0.98

    def is_bulk_order(self) -> bool:
        return self.base_price() > 1000  # Reuses the same query — no duplication
```

Performance note: For expensive computations called multiple times, cache with @functools.cached_property instead.

45. Introduce Null Object

- Problem: None checks (if x is None) are scattered across the codebase before every method call on an object.
- Solution: Create a NullX class that implements the same interface as X but with safe, default behavior. Return it instead of None.
- Client code no longer needs to check for None — the Null Object handles the "nothing" case via polymorphism.

## Key Problem
- Scattered None checks are repetitive, easy to miss, and make code noisy.
- Adding a new "default when None" behavior requires updating every check site.
- Forgetting one None check causes an AttributeError crash.

## Suggested Solution
- Create a NullX subclass (or Protocol-compatible class) with safe defaults.
- Replace None returns with NullX() returns at the source.
- Remove the None checks in client code — the Null Object handles the absent case.

Problem (Before): every call site must check if customer is None before using it.

Bad:

```python
class Customer:
    def __init__(self, name: str, discount_rate: float):
        self.name = name
        self.discount_rate = discount_rate

    def get_discount(self) -> float:
        return self.discount_rate

    def get_name(self) -> str:
        return self.name


def apply_discount(order, customer: Customer | None) -> float:
    if customer is None:
        discount = 0.0
    else:
        discount = customer.get_discount()
    return order.total * (1 - discount)


def greet_customer(customer: Customer | None) -> str:
    if customer is None:
        return "Hello, Guest!"
    return f"Hello, {customer.get_name()}!"
```

Solution (After): NullCustomer handles all absent-customer cases — client code stays clean.

Good:

```python
class Customer:
    def __init__(self, name: str, discount_rate: float):
        self.name = name
        self.discount_rate = discount_rate

    def get_discount(self) -> float:
        return self.discount_rate

    def get_name(self) -> str:
        return self.name


class NullCustomer(Customer):
    """Represents the absence of a customer with safe, do-nothing defaults."""
    def __init__(self):
        super().__init__(name="Guest", discount_rate=0.0)

    def get_discount(self) -> float:
        return 0.0

    def get_name(self) -> str:
        return "Guest"


def resolve_customer(order) -> Customer:
    return order.customer if order.customer is not None else NullCustomer()


# No None checks needed anywhere in client code
def apply_discount(order) -> float:
    customer = resolve_customer(order)
    return order.total * (1 - customer.get_discount())


def greet_customer(order) -> str:
    customer = resolve_customer(order)
    return f"Hello, {customer.get_name()}!"
```

46. Encapsulate Collection

- Problem: A class exposes a mutable collection directly via a getter. External code can add, remove, or replace elements without the class being aware — breaking its invariants.
- Solution: Return a read-only snapshot of the collection. Provide explicit add_X() and remove_X() methods for controlled mutation.
- This keeps the owner class in full control of its own data.

## Key Problem
- When a class returns its internal list/set/dict directly, any caller can mutate it freely.
- Validation, logging, or events triggered on mutation can never be enforced.
- A setter that replaces the entire collection silently discards all previous state.

## Suggested Solution
- The getter returns a read-only snapshot (tuple, frozenset, or a copy).
- Add dedicated add_X() and remove_X() methods for safe, validated mutation.
- Move any invariant-checking logic into these methods.

Problem (Before): _courses list is exposed directly — callers mutate it without the class knowing.

Bad:

```python
class Student:
    def __init__(self, name: str):
        self.name = name
        self._courses: list[str] = []

    def get_courses(self) -> list[str]:
        return self._courses  # Returns direct reference — caller can mutate!

    def set_courses(self, courses: list[str]) -> None:
        self._courses = courses  # Silently replaces all courses


student = Student("Alice")
student.get_courses().append("Math")      # Mutates internal list directly!
student.set_courses(["Physics"])          # Silently discards "Math"
```

Solution (After): The class controls all mutations; the getter returns an immutable snapshot.

Good:

```python
class Student:
    def __init__(self, name: str):
        self.name = name
        self._courses: list[str] = []

    @property
    def courses(self) -> tuple[str, ...]:
        """Read-only snapshot — caller cannot mutate internal state."""
        return tuple(self._courses)

    def add_course(self, course: str) -> None:
        if course in self._courses:
            raise ValueError(f"Already enrolled in: {course}")
        self._courses.append(course)

    def remove_course(self, course: str) -> None:
        if course not in self._courses:
            raise ValueError(f"Not enrolled in: {course}")
        self._courses.remove(course)


student = Student("Alice")
student.add_course("Math")
student.add_course("History")
print(student.courses)           # ('Math', 'History') — immutable snapshot
# student.courses.append("X")   # TypeError: 'tuple' object has no attribute 'append'
```

47. Temporary Field

- Problem: A class has fields that are only set and used during one specific algorithm — they're None or undefined the rest of the time. An object's fields should always mean something; fields that are "sometimes None" are confusing.
- Solution: Extract the algorithm and its temporary fields into a dedicated class. The temporary fields become proper, always-meaningful fields of the new class.

## Key Problem
- Reading a class with conditional fields is confusing: you see attributes, assume they always have meaningful values, but they don't.
- The algorithm relying on them is hard to test in isolation.

## Suggested Solution
- Create a new "Method Object" class for the algorithm.
- Move the temporary fields into the new class's constructor.
- Move the algorithm into the new class's compute() method.
- The original class instantiates and delegates to the new class when needed.

Problem (Before): Three fields exist only for the price() calculation — they're None everywhere else.

Bad:

```python
class Order:
    def __init__(self, base_price: float, quantity: int, discount: float):
        self.base_price = base_price
        self.quantity = quantity
        self.discount = discount
        # Temporary fields — only meaningful inside price()
        self._primary_base: float | None = None
        self._secondary_base: float | None = None
        self._final_price: float | None = None

    def price(self) -> float:
        self._primary_base = self.base_price * self.quantity
        self._secondary_base = self._primary_base * (1 - self.discount)
        self._final_price = (
            self._secondary_base * 0.95
            if self._primary_base > 1000
            else self._secondary_base
        )
        return self._final_price
```

Solution (After): PriceCalculator holds the intermediate values — every field always has meaning.

Good:

```python
class Order:
    def __init__(self, base_price: float, quantity: int, discount: float):
        self.base_price = base_price
        self.quantity = quantity
        self.discount = discount

    def price(self) -> float:
        return PriceCalculator(self).compute()


class PriceCalculator:
    """Encapsulates the pricing algorithm — all fields are meaningful from construction."""
    def __init__(self, order: Order):
        self._primary = order.base_price * order.quantity
        self._secondary = self._primary * (1 - order.discount)

    def compute(self) -> float:
        return self._secondary * 0.95 if self._primary > 1000 else self._secondary
```

48. Replace Method with Method Object

- Problem: A long method has so many intertwined local variables that you cannot apply Extract Method — extracting anything would require passing a dozen variables as parameters, making things worse.
- Solution: Move the entire method into a new class. The local variables become fields of the class. Once there, the computation can be freely decomposed into smaller sub-methods without any parameter overhead.

## Key Problem
- Some methods grow complex enough that their local variables all reference each other, making Extract Method impossible without a massive parameter list.
- The method is too large to understand as a single block, but can't be split in place.

## Suggested Solution
- Create a new class named after what the method computes (e.g., PriceCalculator, ReportBuilder).
- The original object and each local variable become constructor parameters stored as fields.
- The main computation becomes a compute() method.
- Sub-steps become private helper methods on the new class.

Problem (Before): price() method with intertwined intermediate values that can't be extracted.

Bad:

```python
class Order:
    def __init__(self, quantity: int, item_price: float, is_premium: bool):
        self.quantity = quantity
        self.item_price = item_price
        self.is_premium = is_premium

    def price(self) -> float:
        primary_base = self.quantity * self.item_price
        secondary_base = primary_base * (0.9 if self.is_premium else 1.0)
        bulk_deduction = primary_base * 0.05 if primary_base > 1000 else 0
        tertiary_base = secondary_base - bulk_deduction
        discount = 0.02 if self.quantity > 50 else 0
        return tertiary_base * (1 - discount)
```

Solution (After): Each step is a named method on the calculator — no parameter clutter.

Good:

```python
class Order:
    def __init__(self, quantity: int, item_price: float, is_premium: bool):
        self.quantity = quantity
        self.item_price = item_price
        self.is_premium = is_premium

    def price(self) -> float:
        return PriceCalculator(self).compute()


class PriceCalculator:
    def __init__(self, order: Order):
        self._quantity = order.quantity
        self._item_price = order.item_price
        self._is_premium = order.is_premium

    def compute(self) -> float:
        return self._tertiary_base() * (1 - self._bulk_discount())

    def _primary_base(self) -> float:
        return self._quantity * self._item_price

    def _secondary_base(self) -> float:
        return self._primary_base() * (0.9 if self._is_premium else 1.0)

    def _tertiary_base(self) -> float:
        deduction = self._primary_base() * 0.05 if self._primary_base() > 1000 else 0
        return self._secondary_base() - deduction

    def _bulk_discount(self) -> float:
        return 0.02 if self._quantity > 50 else 0
```

49. Replace Conditional with Polymorphism

- Problem: An if/elif chain (or match block) dispatches different behavior based on the type or state of an object. Every time a new type is added, every switch site must be found and updated.
- Solution: Create subclasses for each branch. Move each branch's logic into an overridden method. Replace the conditional with a polymorphic call — the right behavior is selected automatically.
- This follows the Open/Closed Principle: adding a new type = adding a new class, not modifying existing ones.

## Key Problem
- Type-based conditionals scattered in multiple methods create "shotgun surgery" — one new type requires changes in many places.
- The conditional grows with every new case, becoming harder to read and test.

## Suggested Solution
- Extract the conditional to the correct class using Extract Method + Move Method.
- Create a subclass for each branch.
- Move each branch's code into the subclass's overridden method.
- Delete the conditional — polymorphism handles dispatch automatically.

Problem (Before): get_speed() uses if/elif on self.type — adding a new bird type requires editing this method.

Bad:

```python
from enum import Enum

class BirdType(Enum):
    EUROPEAN = "european"
    AFRICAN = "african"
    NORWEGIAN_BLUE = "norwegian_blue"

class Bird:
    def __init__(self, bird_type: BirdType, num_coconuts: int = 0,
                 voltage: float = 1.0, is_nailed: bool = False):
        self.type = bird_type
        self.num_coconuts = num_coconuts
        self.voltage = voltage
        self.is_nailed = is_nailed

    def get_speed(self) -> float:
        if self.type == BirdType.EUROPEAN:
            return self._base_speed()
        elif self.type == BirdType.AFRICAN:
            return self._base_speed() - 0.5 * self.num_coconuts
        elif self.type == BirdType.NORWEGIAN_BLUE:
            return 0.0 if self.is_nailed else self._base_speed(self.voltage)
        raise ValueError(f"Unknown bird type: {self.type}")

    def _base_speed(self, voltage: float = 1.0) -> float:
        return 10.0 * voltage
```

Solution (After): Each bird is its own class — adding a new species requires zero changes to existing code.

Good:

```python
from abc import ABC, abstractmethod

class Bird(ABC):
    def _base_speed(self, voltage: float = 1.0) -> float:
        return 10.0 * voltage

    @abstractmethod
    def get_speed(self) -> float: ...


class EuropeanBird(Bird):
    def get_speed(self) -> float:
        return self._base_speed()


class AfricanBird(Bird):
    def __init__(self, num_coconuts: int):
        self.num_coconuts = num_coconuts

    def get_speed(self) -> float:
        return self._base_speed() - 0.5 * self.num_coconuts


class NorwegianBlueBird(Bird):
    def __init__(self, voltage: float, is_nailed: bool):
        self.voltage = voltage
        self.is_nailed = is_nailed

    def get_speed(self) -> float:
        return 0.0 if self.is_nailed else self._base_speed(self.voltage)


# Client code — no conditional, works for any future bird type automatically
def total_speed(birds: list[Bird]) -> float:
    return sum(bird.get_speed() for bird in birds)
```

50. Dead Code

- Dead code is any variable, parameter, field, method, or class that is no longer used.
- It accumulates when requirements change and nobody cleans up the old code.
- Dead code increases reading time, creates confusion ("is this still needed?"), and wastes future maintenance effort.
- Rule: delete unused code immediately. Version control is your history — you don't need it in the source.

## Detection Tools

```bash
# ruff: detect unused imports, variables, redefined names
ruff check --select F401,F811,ERA001 .

# vulture: detect unused functions, classes, and variables
pip install vulture
vulture src/
```

## Example

```python
# Bad: unused imports, obsolete function, commented-out code
import json
import xml.etree.ElementTree as ET   # Never used anywhere
from datetime import datetime         # Never used anywhere

LEGACY_MAX_RETRIES = 5               # Replaced by config.MAX_RETRIES — never read

def process_data(items: list) -> list:
    # result = []                    # Old approach, left commented out
    # for item in items:
    #     result.append(item)
    return [item for item in items if item]

def _format_date_legacy(date_str: str) -> str:
    """Obsolete — replaced by format_iso_date() six months ago."""
    return date_str.replace("-", "/")   # Nothing calls this function


# Good: only what's actually used, no noise
import json

def process_data(items: list) -> list:
    return [item for item in items if item]
```

Rule of thumb: if you're not sure whether to delete it — delete it. If you're wrong, git restores it in seconds.

51. Speculative Generality (YAGNI)

- Problem: Classes, methods, parameters, or abstraction layers were added "just in case" for future requirements that never arrived. The code is harder to understand because of flexibility nobody is using.
- Solution: Delete it. YAGNI — You Aren't Gonna Need It. Build abstractions when you have two concrete cases that need them, not before.
- Signs: ABC with only one concrete subclass, parameters always passed as None, hook methods with empty bodies, interfaces with a single implementation.

## Example

```python
# Bad: speculative abstraction for a system that only ever has one storage type
from abc import ABC, abstractmethod

class DataRepository(ABC):
    """Abstract base added for 'future multi-backend support' (that never came)."""
    @abstractmethod
    def save(self, data: dict) -> None: ...

    @abstractmethod
    def load(self, key: str) -> dict: ...

    def on_save_hook(self, data: dict) -> None:
        pass  # Empty hook for "future audit logging" — never overridden

class FileRepository(DataRepository):
    def save(self, data: dict) -> None:
        Path("data.json").write_text(json.dumps(data))

    def load(self, key: str) -> dict:
        return json.loads(Path("data.json").read_text())


# Good: simple, direct — extract the ABC when you actually have a second backend
import json
from pathlib import Path

class FileRepository:
    def save(self, data: dict) -> None:
        Path("data.json").write_text(json.dumps(data))

    def load(self, key: str) -> dict:
        return json.loads(Path("data.json").read_text())
```

Rule: create the abstraction when you have the second concrete case. Not before.

52. Introduce Assertion

- When code relies on an implicit assumption (e.g., "this value must never be None", "this list must be non-empty"), make that assumption explicit with an assert statement.
- An assertion acts as live documentation and fails loudly the moment an assumption is violated, catching bugs at their source.
- Rule: use assert for internal programmer invariants. Use raise ValueError/TypeError for user-facing or API input validation.

## Example

```python
# Bad: implicit assumption — code crashes with a confusing AttributeError if the
# assumption is violated (either expense_limit or primary_project must be set)
class Employee:
    NULL_EXPENSE = -1.0

    def __init__(self, expense_limit: float = -1.0, primary_project=None):
        self.expense_limit = expense_limit
        self.primary_project = primary_project

    def get_expense_limit(self) -> float:
        # Assumes: at least one of the two is always set
        # But nothing enforces this — silent crash if both are missing
        return (
            self.expense_limit
            if self.expense_limit != self.NULL_EXPENSE
            else self.primary_project.get_member_expense_limit()
        )


# Good: assumption is explicit — fails immediately with a clear message if violated
class Employee:
    NULL_EXPENSE = -1.0

    def __init__(self, expense_limit: float = -1.0, primary_project=None):
        self.expense_limit = expense_limit
        self.primary_project = primary_project

    def get_expense_limit(self) -> float:
        assert (
            self.expense_limit != self.NULL_EXPENSE or self.primary_project is not None
        ), "Employee must have either an expense_limit or a primary_project set"

        return (
            self.expense_limit
            if self.expense_limit != self.NULL_EXPENSE
            else self.primary_project.get_member_expense_limit()
        )
```

When to use assert vs raise:
- `assert condition, "message"` — programmer invariants (should never be False in correct code)
- `raise ValueError(...)` — user or API input that is wrong but valid to receive

53. Remove Assignments to Parameters

- Problem: A method reassigns a value to one of its parameters inside its body. The parameter no longer represents what was passed in, which makes the code hard to trace.
- Solution: Introduce a local variable initialized from the parameter. Work with the local variable instead.
- In Python this matters especially with mutable objects — reassigning the parameter name doesn't affect the caller, but mutating a mutable argument does.

## Example

```python
# Bad: input_val is reassigned — confusing, especially with mutable types
def calculate_discount(input_val: float, quantity: int) -> float:
    if quantity > 50:
        input_val -= 2.0   # input_val now means something different from what was passed in
    if input_val > 100:
        input_val *= 0.9   # input_val has a third meaning now
    return input_val


# Good: use a local variable — parameter preserves its original meaning throughout
def calculate_discount(input_val: float, quantity: int) -> float:
    result = input_val       # Local variable carries the working value

    if quantity > 50:
        result -= 2.0
    if result > 100:
        result *= 0.9

    return result
```

Mutable argument warning — reassigning vs mutating:

```python
# REASSIGNING the parameter name: does NOT affect the caller's object
def bad_clear(items: list) -> None:
    items = []               # Only rebinds the local name — caller's list is unchanged!

# MUTATING through the reference: DOES affect the caller's object
def also_bad(items: list) -> None:
    items.clear()            # Mutates the caller's actual list in place!

# Safe: always work on a copy when you need an independent result
def good_transform(items: list[str]) -> list[str]:
    result = list(items)     # Independent copy
    result.append("extra")
    return result
```

54. Divergent Change

- Problem: A single class has multiple unrelated reasons to change. When adding a new feature, you find yourself editing the same class for several different concerns at once (data access, pricing logic, AND display formatting all in one class).
- This is a Single Responsibility Principle violation — the class description can no longer fit in one sentence.
- Solution: Apply Extract Class to split the class by its axes of change. Each resulting class should have exactly one reason to change.

## Key Problem
- Every time a different part of the system evolves, the same class gets touched.
- Teams working on unrelated features create conflicts in the same file.
- Tests for one concern are coupled to completely unrelated code.

## Suggested Solution
- Identify which methods change together for the same reason — those form a new class.
- Extract those methods and their related fields into a focused, single-purpose class.
- Have the original class compose the new one, or delete it if empty.

Problem (Before): ProductService changes when the database changes, when pricing rules change, AND when the display format changes — three unrelated axes of change in one class.

Bad:

```python
class ProductService:
    def __init__(self, db_conn, tax_rate: float, currency: str):
        self._db = db_conn
        self._tax_rate = tax_rate
        self._currency = currency

    # Changes when the data source changes
    def fetch_product(self, product_id: int) -> dict:
        return self._db.query(f"SELECT * FROM products WHERE id={product_id}")

    def save_product(self, product: dict) -> None:
        self._db.execute("INSERT INTO products ...", product)

    # Changes when tax/pricing rules change
    def calculate_price_with_tax(self, base_price: float) -> float:
        return base_price * (1 + self._tax_rate)

    def apply_discount(self, price: float, discount_pct: float) -> float:
        return price * (1 - discount_pct / 100)

    # Changes when display/export format changes
    def format_price(self, price: float) -> str:
        return f"{self._currency} {price:.2f}"

    def format_product_label(self, product: dict) -> str:
        return f"[{product['sku']}] {product['name']}"
```

Solution (After): Three focused classes, each with exactly one reason to change.

Good:

```python
class ProductRepository:
    """Changes only when the data source or query logic changes."""
    def __init__(self, db_conn):
        self._db = db_conn

    def fetch(self, product_id: int) -> dict:
        return self._db.query(f"SELECT * FROM products WHERE id={product_id}")

    def save(self, product: dict) -> None:
        self._db.execute("INSERT INTO products ...", product)


class PricingService:
    """Changes only when tax rules or discount logic changes."""
    def __init__(self, tax_rate: float):
        self._tax_rate = tax_rate

    def with_tax(self, base_price: float) -> float:
        return base_price * (1 + self._tax_rate)

    def with_discount(self, price: float, discount_pct: float) -> float:
        return price * (1 - discount_pct / 100)


class ProductFormatter:
    """Changes only when the display or export format changes."""
    def __init__(self, currency: str):
        self._currency = currency

    def price(self, amount: float) -> str:
        return f"{self._currency} {amount:.2f}"

    def label(self, product: dict) -> str:
        return f"[{product['sku']}] {product['name']}"
```