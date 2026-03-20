## 3. Module Organization

### Import Guidelines

```python
# ❌ BAD: Star imports make dependencies unclear
from module import *

# ❌ BAD: Importing implementation details
from module.internal._private import something

# ✅ GOOD: Explicit imports
from module import specific_function, SpecificClass

# ✅ GOOD: Aliased imports for clarity
import very.deep.module as mod
```

### `__init__.py` Philosophy

**Empty `__init__.py` is often correct.** Only add exports when you want to define a public API:

```python
# src/my_project/domain/__init__.py
# Keep empty if modules are imported directly

# OR define public API explicitly:
from .models import User, Order
from .exceptions import DomainError

__all__ = ["User", "Order", "DomainError"]
```

### Module Responsibilities

Each module should have a **single, clear purpose**:

```python
# ❌ BAD: Mixed responsibilities
# utils.py (the "junk drawer" anti-pattern)
def send_email(): ...
def calculate_tax(): ...
def format_date(): ...
def connect_to_db(): ...

# ✅ GOOD: Focused modules
# email/sender.py
def send_email(): ...

# finance/tax.py
def calculate_tax(): ...

# formatting/dates.py
def format_date(): ...
```

### Circular Import Prevention

```python
# ❌ Causes circular import
# module_a.py
from module_b import func_b
# module_b.py
from module_a import func_a

# ✅ Solution 1: Import inside function
def my_function():
    from module_b import func_b
    return func_b()

# ✅ Solution 2: Use dependency injection
def my_function(dependency):
    return dependency()

# ✅ Solution 3: Create interface module
# interfaces.py contains abstract definitions
# Both modules depend on interfaces, not each other
```