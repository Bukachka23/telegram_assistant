# Python Code Condensation Patterns

This reference contains practical patterns for reducing Lines of Code (LOC) in Python while preserving functionality and readability.

## Table of Contents

1. [Boolean and Conditional Simplification](#1-boolean-and-conditional-simplification)
2. [Collection Operations and Comprehensions](#2-collection-operations-and-comprehensions)
3. [Dictionary and Mapping Operations](#3-dictionary-and-mapping-operations)
4. [Function Composition and Chaining](#4-function-composition-and-chaining)
5. [Context Managers and Resource Handling](#5-context-managers-and-resource-handling)
6. [String Operations and Formatting](#6-string-operations-and-formatting)
7. [Exception Handling](#7-exception-handling)
8. [Iterator and Generator Patterns](#8-iterator-and-generator-patterns)
9. [Import and Module Organization](#9-import-and-module-organization)
10. [Class and Method Condensation](#10-class-and-method-condensation)

---

## 1. Boolean and Conditional Simplification

### Pattern 1.1: Direct Boolean Return

**Before (4 lines):**
```python
def is_valid(value):
    if value > 0 and value < 100:
        return True
    return False
```

**After (2 lines):**
```python
def is_valid(value):
    return 0 < value < 100
```

**LOC Saved:** 2 lines (50% reduction)  
**When to use:** Any time returning boolean result of a condition  
**When NOT to use:** Complex conditions that benefit from intermediate variables for clarity

---

### Pattern 1.2: Ternary Operator for Simple Conditionals

**Before (4 lines):**
```python
if condition:
    value = 'yes'
else:
    value = 'no'
```

**After (1 line):**
```python
value = 'yes' if condition else 'no'
```

**LOC Saved:** 3 lines (75% reduction)  
**When to use:** Simple binary assignments  
**When NOT to use:** Complex expressions in branches, nested ternaries

---

### Pattern 1.3: Boolean Short-Circuit for Default Values

**Before (3 lines):**
```python
if name is None or name == '':
    name = 'Unknown'
```

**After (1 line):**
```python
name = name or 'Unknown'
```

**LOC Saved:** 2 lines (67% reduction)  
**When to use:** Setting defaults for falsy values  
**When NOT to use:** When you need to distinguish between None, empty string, 0, etc.

---

### Pattern 1.4: Dictionary Dispatch Instead of If-Elif-Else

**Before (10 lines):**
```python
def get_handler(action):
    if action == 'create':
        return create_handler
    elif action == 'update':
        return update_handler
    elif action == 'delete':
        return delete_handler
    else:
        return default_handler
```

**After (4 lines):**
```python
def get_handler(action):
    handlers = {'create': create_handler, 'update': update_handler, 'delete': delete_handler}
    return handlers.get(action, default_handler)
```

**LOC Saved:** 6 lines (60% reduction)  
**When to use:** Multiple equality checks against constant values  
**When NOT to use:** Complex conditions, range checks, or when conditions have side effects

---

### Pattern 1.5: Match/Case for Multiple Conditions (Python 3.10+)

**Before (12 lines):**
```python
def process_status(status):
    if status == 'pending':
        return 'Waiting...'
    elif status == 'processing':
        return 'Working...'
    elif status in ['completed', 'done']:
        return 'Finished!'
    else:
        return 'Unknown'
```

**After (5 lines):**
```python
def process_status(status):
    match status:
        case 'pending': return 'Waiting...'
        case 'processing': return 'Working...'
        case 'completed' | 'done': return 'Finished!'
        case _: return 'Unknown'
```

**LOC Saved:** 7 lines (58% reduction)  
**When to use:** Python 3.10+, pattern matching scenarios  
**When NOT to use:** Python < 3.10, simple if-else that's clearer

---

## 2. Collection Operations and Comprehensions

### Pattern 2.1: List Comprehensions Instead of Loops

**Before (4 lines):**
```python
result = []
for item in items:
    if item.active:
        result.append(item.name)
```

**After (1 line):**
```python
result = [item.name for item in items if item.active]
```

**LOC Saved:** 3 lines (75% reduction)  
**When to use:** Building lists with filtering or transformation  
**When NOT to use:** Complex logic in loop body, side effects, nested comprehensions that hurt readability

---

### Pattern 2.2: Set and Dict Comprehensions

**Before (4 lines):**
```python
unique_values = set()
for item in items:
    unique_values.add(item.category)
```

**After (1 line):**
```python
unique_values = {item.category for item in items}
```

**LOC Saved:** 3 lines (75% reduction)

**Dict Comprehension:**
```python
# Before (4 lines)
mapping = {}
for key, value in pairs:
    mapping[key] = value.upper()

# After (1 line)
mapping = {k: v.upper() for k, v in pairs}
```

**When to use:** Building sets or dicts from iterables  
**When NOT to use:** Complex transformations better as explicit loops

---

### Pattern 2.3: Built-in Functions (map, filter, sum, any, all)

**Before (4 lines):**
```python
total = 0
for item in items:
    total += item.price
```

**After (1 line):**
```python
total = sum(item.price for item in items)
```

**More Examples:**
```python
# Check if any item is valid
has_valid = any(item.is_valid() for item in items)

# Check if all items are valid
all_valid = all(item.is_valid() for item in items)

# Filter items
active = filter(lambda x: x.active, items)

# Transform items
names = map(lambda x: x.name, items)
```

**LOC Saved:** 3 lines (75% reduction)  
**When to use:** Simple aggregations, checks, transformations  
**When NOT to use:** Complex logic requiring multiple statements

---

### Pattern 2.4: Flatten Nested Lists

**Before (4 lines):**
```python
flat = []
for sublist in nested:
    for item in sublist:
        flat.append(item)
```

**After (1 line):**
```python
flat = [item for sublist in nested for item in sublist]
```

**Alternative (more readable):**
```python
from itertools import chain
flat = list(chain.from_iterable(nested))
```

**LOC Saved:** 3 lines (75% reduction)  
**When to use:** Flattening one level of nesting  
**When NOT to use:** Deep nesting (use recursion or itertools), conditional flattening

---

### Pattern 2.5: Unpacking and Multiple Assignment

**Before (3 lines):**
```python
first = items[0]
second = items[1]
rest = items[2:]
```

**After (1 line):**
```python
first, second, *rest = items
```

**LOC Saved:** 2 lines (67% reduction)  
**When to use:** Extracting values from sequences  
**When NOT to use:** When you need bounds checking or defaults

---

## 3. Dictionary and Mapping Operations

### Pattern 3.1: Dict.get() with Default

**Before (3 lines):**
```python
if key in config:
    value = config[key]
else:
    value = 'default'
```

**After (1 line):**
```python
value = config.get(key, 'default')
```

**LOC Saved:** 2 lines (67% reduction)

---

### Pattern 3.2: Dict.setdefault() for Accumulation

**Before (4 lines):**
```python
if key not in counts:
    counts[key] = []
counts[key].append(item)
```

**After (1 line):**
```python
counts.setdefault(key, []).append(item)
```

**Alternative with defaultdict:**
```python
from collections import defaultdict
counts = defaultdict(list)
counts[key].append(item)  # No need for setdefault
```

**LOC Saved:** 3 lines (75% reduction)

---

### Pattern 3.3: Dictionary Merging (Python 3.9+)

**Before (3 lines):**
```python
result = defaults.copy()
result.update(config)
result.update(overrides)
```

**After (1 line):**
```python
result = defaults | config | overrides
```

**Alternative (Python 3.5+):**
```python
result = {**defaults, **config, **overrides}
```

**LOC Saved:** 2 lines (67% reduction)

---

### Pattern 3.4: Counter for Frequency Counting

**Before (5 lines):**
```python
counts = {}
for item in items:
    if item not in counts:
        counts[item] = 0
    counts[item] += 1
```

**After (2 lines):**
```python
from collections import Counter
counts = Counter(items)
```

**LOC Saved:** 3 lines (60% reduction)

---

## 4. Function Composition and Chaining

### Pattern 4.1: Method Chaining

**Before (4 lines):**
```python
text = text.strip()
text = text.lower()
text = text.replace(' ', '_')
```

**After (1 line):**
```python
text = text.strip().lower().replace(' ', '_')
```

**LOC Saved:** 3 lines (75% reduction)  
**When to use:** Sequential transformations on same object  
**When NOT to use:** Long chains that hurt readability (>3-4 methods)

---

### Pattern 4.2: functools.reduce for Accumulation

**Before (4 lines):**
```python
result = initial
for item in items:
    result = combine(result, item)
```

**After (2 lines):**
```python
from functools import reduce
result = reduce(combine, items, initial)
```

**LOC Saved:** 2 lines (50% reduction)

---

### Pattern 4.3: operator Module for Common Operations

**Before (1 line):**
```python
sorted_items = sorted(items, key=lambda x: x.score)
```

**After (2 lines - but more efficient):**
```python
from operator import attrgetter
sorted_items = sorted(items, key=attrgetter('score'))
```

**More examples:**
```python
from operator import itemgetter, methodcaller

# Instead of: lambda x: x[1]
key_func = itemgetter(1)

# Instead of: lambda x: x.upper()
upper_func = methodcaller('upper')
```

**When to use:** Performance-critical sorting, mapping operations  
**When NOT to use:** One-time use cases where lambda is clearer

---

## 5. Context Managers and Resource Handling

### Pattern 5.1: Context Manager for File Operations

**Before (4 lines):**
```python
f = open('file.txt')
data = f.read()
f.close()
```

**After (2 lines):**
```python
with open('file.txt') as f:
    data = f.read()
```

**LOC Saved:** 2 lines (50% reduction)

---

### Pattern 5.2: Multiple Context Managers

**Before (6 lines):**
```python
with open('input.txt') as infile:
    data = infile.read()
    with open('output.txt', 'w') as outfile:
        outfile.write(process(data))
```

**After (3 lines):**
```python
with open('input.txt') as infile, open('output.txt', 'w') as outfile:
    data = infile.read()
    outfile.write(process(data))
```

**LOC Saved:** 3 lines (50% reduction)

---

### Pattern 5.3: contextlib.suppress for Ignoring Exceptions

**Before (4 lines):**
```python
try:
    os.remove(temp_file)
except FileNotFoundError:
    pass
```

**After (2 lines):**
```python
from contextlib import suppress
with suppress(FileNotFoundError): os.remove(temp_file)
```

**LOC Saved:** 2 lines (50% reduction)  
**When to use:** Ignoring specific expected exceptions  
**When NOT to use:** When you need to log or handle the exception

---

## 6. String Operations and Formatting

### Pattern 6.1: f-strings Instead of format() or %

**Before:**
```python
message = "Hello, {}! You have {} messages.".format(name, count)
```

**After:**
```python
message = f"Hello, {name}! You have {count} messages."
```

**LOC Saved:** Same lines but more concise and readable

---

### Pattern 6.2: join() Instead of Concatenation

**Before (3 lines):**
```python
result = ''
for item in items:
    result += str(item) + ', '
```

**After (1 line):**
```python
result = ', '.join(str(item) for item in items)
```

**LOC Saved:** 2 lines (67% reduction)

---

### Pattern 6.3: str.translate() for Multiple Replacements

**Before (4 lines):**
```python
text = text.replace('a', 'A')
text = text.replace('e', 'E')
text = text.replace('i', 'I')
```

**After (2 lines):**
```python
trans = str.maketrans('aei', 'AEI')
text = text.translate(trans)
```

**LOC Saved:** 2 lines (50% reduction)

---

## 7. Exception Handling

### Pattern 7.1: EAFP (Easier to Ask Forgiveness than Permission)

**Before (4 lines):**
```python
if key in data:
    value = data[key]
else:
    value = default
```

**After (3 lines):**
```python
try:
    value = data[key]
except KeyError:
    value = default
```

**Or even better (1 line):**
```python
value = data.get(key, default)
```

**When to use:** When the happy path is the common case  
**When NOT to use:** When exceptions are frequent (use LBYL)

---

### Pattern 7.2: Consolidate Exception Handling

**Before (6 lines):**
```python
try:
    return int(value)
except ValueError:
    return None
except TypeError:
    return None
```

**After (3 lines):**
```python
try:
    return int(value)
except (ValueError, TypeError):
    return None
```

**LOC Saved:** 3 lines (50% reduction)

---

## 8. Iterator and Generator Patterns

### Pattern 8.1: Generator Expressions for Large Data

**Before (4 lines):**
```python
result = []
for item in large_dataset:
    if expensive_check(item):
        result.append(transform(item))
```

**After (1 line):**
```python
result = (transform(item) for item in large_dataset if expensive_check(item))
```

**LOC Saved:** 3 lines (75% reduction)  
**Benefit:** Memory efficient for large datasets

---

### Pattern 8.2: itertools for Complex Iteration

**Common patterns:**
```python
from itertools import islice, chain, groupby, zip_longest

# Take first N items
first_ten = list(islice(items, 10))

# Flatten multiple iterables
all_items = chain(items1, items2, items3)

# Group by key
grouped = groupby(sorted_items, key=lambda x: x.category)

# Zip with padding
paired = zip_longest(list1, list2, fillvalue=None)
```

**When to use:** Complex iteration patterns  
**Benefit:** Often replaces 3-5 lines of manual iteration

---

### Pattern 8.3: yield from for Delegation

**Before (3 lines):**
```python
def flatten(nested):
    for item in nested:
        for sub in item:
            yield sub
```

**After (2 lines):**
```python
def flatten(nested):
    for item in nested:
        yield from item
```

**LOC Saved:** 1 line (33% reduction)

---

## 9. Import and Module Organization

### Pattern 9.1: Combine Related Imports

**Before (3 lines):**
```python
from os import path
from os import environ
from os import makedirs
```

**After (1 line):**
```python
from os import path, environ, makedirs
```

**LOC Saved:** 2 lines (67% reduction)

---

### Pattern 9.2: Import Common Combinations

**Common patterns:**
```python
# Instead of multiple typing imports
from typing import Dict, List, Optional, Union, Any

# Instead of multiple pathlib imports
from pathlib import Path

# Instead of datetime parts
from datetime import datetime, timedelta, date
```

---

## 10. Class and Method Condensation

### Pattern 10.1: dataclasses Instead of Manual __init__

**Before (10 lines):**
```python
class User:
    def __init__(self, name, email, age):
        self.name = name
        self.email = email
        self.age = age
    
    def __repr__(self):
        return f"User(name={self.name}, email={self.email}, age={self.age})"
```

**After (4 lines):**
```python
from dataclasses import dataclass

@dataclass
class User:
    name: str
    email: str
    age: int
```

**LOC Saved:** 6 lines (60% reduction)  
**Benefits:** Auto-generates __init__, __repr__, __eq__, etc.

---

### Pattern 10.2: Properties Instead of Getter/Setter

**Before (8 lines):**
```python
class Product:
    def __init__(self):
        self._price = 0
    
    def get_price(self):
        return self._price
    
    def set_price(self, value):
        self._price = max(0, value)
```

**After (5 lines):**
```python
class Product:
    def __init__(self):
        self._price = 0
    
    @property
    def price(self):
        return self._price
    
    @price.setter
    def price(self, value):
        self._price = max(0, value)
```

**LOC Saved:** 3 lines (37% reduction) + Pythonic interface

---

### Pattern 10.3: __slots__ for Memory Efficiency

**Before:**
```python
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
```

**After (with slots):**
```python
class Point:
    __slots__ = ('x', 'y')
    def __init__(self, x, y):
        self.x = x
        self.y = y
```

**Same LOC but:** 50% memory reduction for instances

---

### Pattern 10.4: Enum for Constants

**Before (5 lines):**
```python
STATUS_PENDING = 'pending'
STATUS_ACTIVE = 'active'
STATUS_COMPLETE = 'complete'
STATUS_FAILED = 'failed'
```

**After (4 lines):**
```python
from enum import Enum

class Status(Enum):
    PENDING = 'pending'
    ACTIVE = 'active'
    COMPLETE = 'complete'
    FAILED = 'failed'
```

**Benefits:** Type safety, auto-complete, grouping

---

## Advanced Patterns

### Pattern A.1: Walrus Operator (:=) Python 3.8+

**Before (3 lines):**
```python
match = pattern.search(text)
if match:
    return match.group(1)
```

**After (2 lines):**
```python
if match := pattern.search(text):
    return match.group(1)
```

**LOC Saved:** 1 line (33% reduction)

---

### Pattern A.2: Structural Pattern Matching (Python 3.10+)

**Complex data extraction:**
```python
# Before (8 lines)
if isinstance(data, dict):
    if 'user' in data:
        user = data['user']
        if 'name' in user:
            name = user['name']
            print(f"Hello, {name}")

# After (3 lines)
match data:
    case {'user': {'name': name}}:
        print(f"Hello, {name}")
```

**LOC Saved:** 5 lines (63% reduction)

---

## Measuring Impact

After applying patterns, calculate:

```
LOC Saved = Original LOC - Condensed LOC
Reduction % = (LOC Saved / Original LOC) * 100
```

**Example:**
- Original: 150 lines
- Condensed: 90 lines
- Saved: 60 lines (40% reduction)

## Readability vs. Conciseness Trade-offs

**Keep it verbose when:**
- Complex business logic needs clarity
- Debugging will be difficult with condensed code
- Team unfamiliar with advanced Python features
- Condensation creates maintenance burden

**Condense when:**
- Pattern is idiomatic Python (comprehensions, context managers)
- Removes boilerplate without obscuring intent
- Team is comfortable with the feature
- Improves readability (removes clutter)

## Summary

Focus on these high-impact areas:
1. **List/dict comprehensions** → 3-4 line savings each
2. **Context managers** → 2-3 line savings
3. **Dictionary dispatch** → 5-8 line savings
4. **Built-in functions** (sum, any, all) → 3-4 line savings
5. **f-strings and join()** → 1-2 line savings
6. **dataclasses** → 6-10 line savings per class

Typical condensation achieves **30-50% LOC reduction** while maintaining readability.