# Python Optimization Patterns

## Table of Contents

1. [Algorithmic Optimizations](#1-algorithmic-optimizations)
2. [Data Structure Selection](#2-data-structure-selection)
3. [Caching and Memoization](#3-caching-and-memoization)
4. [I/O Optimization](#4-io-optimization)
5. [Database Optimization](#5-database-optimization)
6. [Concurrency and Parallelism](#6-concurrency-and-parallelism)
7. [Python-Specific Performance Idioms](#7-python-specific-performance-idioms)
8. [Memory Optimization](#8-memory-optimization)
9. [Serialization Optimization](#9-serialization-optimization)
10. [Numerical and Data Processing](#10-numerical-and-data-processing)

---

## 1. Algorithmic Optimizations

### Pattern 1.1: Eliminate Redundant Computation

**Problem:** Same computation repeated multiple times.

```python
# SLOW: Recomputes len(data) and processes duplicates
def process_items(data):
    results = []
    for i in range(len(data)):
        for j in range(len(data)):
            if data[i] + data[j] == target:
                results.append((data[i], data[j]))
    return results  # O(n²)

# FAST: Use a set for O(1) lookup
def process_items(data):
    seen = set(data)
    return [(x, target - x) for x in data if (target - x) in seen]  # O(n)
```

### Pattern 1.2: Reduce Algorithmic Complexity

**Problem:** O(n²) or worse when O(n) or O(n log n) is possible.

```python
# SLOW: O(n²) — checking every pair
def find_duplicates(items):
    duplicates = []
    for i, item in enumerate(items):
        for j, other in enumerate(items):
            if i != j and item == other and item not in duplicates:
                duplicates.append(item)
    return duplicates

# FAST: O(n) — count occurrences
from collections import Counter

def find_duplicates(items):
    return [item for item, count in Counter(items).items() if count > 1]
```

### Pattern 1.3: Early Termination

**Problem:** Processing continues after the answer is found.

```python
# SLOW: Always processes entire list
def has_negative(numbers):
    return len([n for n in numbers if n < 0]) > 0

# FAST: Stops at first negative
def has_negative(numbers):
    return any(n < 0 for n in numbers)
```

### Pattern 1.4: Precomputation and Lookup Tables

**Problem:** Repeated expensive computation with limited input space.

```python
# SLOW: Recomputes on every call
def get_day_name(day_num):
    import calendar
    return calendar.day_name[day_num]

# FAST: Precomputed lookup
DAY_NAMES = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')

def get_day_name(day_num):
    return DAY_NAMES[day_num]
```

### Pattern 1.5: Batch Processing

**Problem:** Processing items one at a time when batching is possible.

```python
# SLOW: One DB insert per item
def save_users(users):
    for user in users:
        db.execute("INSERT INTO users (name) VALUES (%s)", (user.name,))
        db.commit()

# FAST: Batch insert
def save_users(users):
    db.executemany(
        "INSERT INTO users (name) VALUES (%s)",
        [(u.name,) for u in users]
    )
    db.commit()
```

---

## 2. Data Structure Selection

### Pattern 2.1: Set for Membership Testing

```python
# SLOW: O(n) per lookup
allowed = ['admin', 'editor', 'viewer', 'moderator']
if role in allowed:  # Scans entire list
    ...

# FAST: O(1) per lookup
allowed = {'admin', 'editor', 'viewer', 'moderator'}
if role in allowed:  # Hash lookup
    ...
```

**Rule of thumb:** If you check membership more than once, convert to a `set`.

### Pattern 2.2: dict for Key-Value Lookups

```python
# SLOW: Linear search through list of tuples
config_pairs = [('host', 'localhost'), ('port', 8080), ('debug', True)]

def get_config(key):
    for k, v in config_pairs:
        if k == key:
            return v  # O(n)

# FAST: Dictionary lookup
config = {'host': 'localhost', 'port': 8080, 'debug': True}

def get_config(key):
    return config.get(key)  # O(1)
```

### Pattern 2.3: deque for Queue/Stack Operations

```python
from collections import deque

# SLOW: list.pop(0) is O(n) — shifts all elements
queue = [1, 2, 3, 4, 5]
item = queue.pop(0)  # O(n)

# FAST: deque.popleft() is O(1)
queue = deque([1, 2, 3, 4, 5])
item = queue.popleft()  # O(1)
```

### Pattern 2.4: defaultdict and Counter for Aggregation

```python
from collections import defaultdict, Counter

# SLOW: Manual checking
word_count = {}
for word in words:
    if word in word_count:
        word_count[word] += 1
    else:
        word_count[word] = 1

# FAST: Counter
word_count = Counter(words)

# SLOW: Manual group-by
groups = {}
for item in items:
    key = item.category
    if key not in groups:
        groups[key] = []
    groups[key].append(item)

# FAST: defaultdict
groups = defaultdict(list)
for item in items:
    groups[item.category].append(item)
```

### Pattern 2.5: heapq for Top-N Problems

```python
import heapq

# SLOW: Sort entire list to get top 10
top_10 = sorted(huge_list, key=lambda x: x.score, reverse=True)[:10]  # O(n log n)

# FAST: Heap-based selection
top_10 = heapq.nlargest(10, huge_list, key=lambda x: x.score)  # O(n log k)
```

### Pattern 2.6: bisect for Sorted Insertion/Search

```python
import bisect

# SLOW: Search + insert in sorted list
def insert_sorted(sorted_list, item):
    for i, existing in enumerate(sorted_list):
        if item <= existing:
            sorted_list.insert(i, item)
            return
    sorted_list.append(item)  # O(n)

# FAST: Binary search insertion
def insert_sorted(sorted_list, item):
    bisect.insort(sorted_list, item)  # O(log n) search + O(n) insert
```

---

## 3. Caching and Memoization

### Pattern 3.1: functools.lru_cache

```python
from functools import lru_cache

# SLOW: Recomputes for same inputs
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)  # O(2^n)

# FAST: Cached — each value computed once
@lru_cache(maxsize=None)
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)  # O(n)
```

### Pattern 3.2: functools.cache (Python 3.9+)

```python
from functools import cache

@cache  # Simpler than lru_cache(maxsize=None)
def expensive_computation(x, y):
    # Complex math...
    return result
```

### Pattern 3.3: Manual Cache with TTL

```python
import time

class TTLCache:
    """Simple cache with time-to-live expiration."""

    def __init__(self, ttl_seconds=300):
        self.ttl = ttl_seconds
        self._cache = {}

    def get(self, key):
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.monotonic() - timestamp < self.ttl:
                return value
            del self._cache[key]
        return None

    def set(self, key, value):
        self._cache[key] = (value, time.monotonic())

# Usage
cache = TTLCache(ttl_seconds=60)

def get_user(user_id):
    cached = cache.get(f"user:{user_id}")
    if cached is not None:
        return cached
    user = db.query(User).get(user_id)  # Expensive
    cache.set(f"user:{user_id}", user)
    return user
```

### Pattern 3.4: Property Caching

```python
# SLOW: Recomputes every access
class Report:
    @property
    def summary(self):
        return self._compute_expensive_summary()

# FAST: Compute once, cache on instance
from functools import cached_property

class Report:
    @cached_property
    def summary(self):
        return self._compute_expensive_summary()
```

### Pattern 3.5: Application-Level Caching (Redis)

```python
import json
import redis
import hashlib

r = redis.Redis()

def cached(ttl=300):
    """Decorator for Redis-based caching."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{hashlib.md5(json.dumps((args, kwargs), sort_keys=True, default=str).encode()).hexdigest()}"
            cached_result = r.get(key)
            if cached_result:
                return json.loads(cached_result)
            result = func(*args, **kwargs)
            r.setex(key, ttl, json.dumps(result, default=str))
            return result
        return wrapper
    return decorator

@cached(ttl=60)
def get_expensive_report(user_id, date_range):
    ...
```

---

## 4. I/O Optimization

### Pattern 4.1: Buffered I/O

```python
# SLOW: Many small writes
with open('output.txt', 'w') as f:
    for line in million_lines:
        f.write(line + '\n')

# FAST: Batch writes
with open('output.txt', 'w', buffering=8192) as f:
    f.writelines(line + '\n' for line in million_lines)

# FASTEST: Single write
with open('output.txt', 'w') as f:
    f.write('\n'.join(million_lines))
```

### Pattern 4.2: Memory-Mapped Files

```python
import mmap

# SLOW: Read entire large file into memory
with open('huge_file.bin', 'rb') as f:
    data = f.read()
    # Process data...

# FAST: Memory-mapped — only loads pages on access
with open('huge_file.bin', 'rb') as f:
    with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        # Access like bytes, but only loads needed pages
        chunk = mm[1000:2000]
        position = mm.find(b'pattern')
```

### Pattern 4.3: Streaming Large Files

```python
# SLOW: Load entire CSV into memory
import csv

with open('huge.csv') as f:
    data = list(csv.reader(f))  # Everything in memory
    for row in data:
        process(row)

# FAST: Stream row by row
with open('huge.csv') as f:
    reader = csv.reader(f)
    for row in reader:  # One row in memory at a time
        process(row)
```

### Pattern 4.4: Connection Pooling

```python
# SLOW: New connection per request
def get_data(url):
    response = requests.get(url)  # TCP handshake every time
    return response.json()

# FAST: Reuse connections via session
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20,
)
session.mount('https://', adapter)

def get_data(url):
    response = session.get(url)  # Reuses TCP connection
    return response.json()
```

### Pattern 4.5: Async I/O for Concurrent Requests

```python
import aiohttp
import asyncio

# SLOW: Sequential requests
def fetch_all(urls):
    return [requests.get(url).json() for url in urls]  # N * latency

# FAST: Concurrent async requests
async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [session.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)  # ~1 * latency
        return [await r.json() for r in responses]
```

---

## 5. Database Optimization

### Pattern 5.1: Eager Loading (Prevent N+1)

```python
# SLOW: N+1 queries
users = session.query(User).all()
for user in users:
    print(user.orders)  # Each access = 1 query

# FAST: Eager load relationships
from sqlalchemy.orm import joinedload

users = session.query(User).options(joinedload(User.orders)).all()
for user in users:
    print(user.orders)  # Already loaded, no extra queries
```

### Pattern 5.2: Select Only Needed Columns

```python
# SLOW: Fetches all columns
users = session.query(User).all()
names = [u.name for u in users]

# FAST: Fetch only what's needed
names = session.query(User.name).all()
# Returns lightweight tuples, not full ORM objects
```

### Pattern 5.3: Bulk Operations

```python
# SLOW: Individual inserts with ORM overhead
for data in big_data_list:
    session.add(User(**data))
session.commit()

# FAST: Bulk insert
session.bulk_insert_mappings(User, big_data_list)
session.commit()

# FASTEST: Raw SQL with executemany
session.execute(
    User.__table__.insert(),
    big_data_list
)
session.commit()
```

### Pattern 5.4: Pagination for Large Result Sets

```python
# SLOW: Load all results
all_users = session.query(User).all()  # Millions of rows in memory

# FAST: Server-side pagination
def iter_users(session, batch_size=1000):
    offset = 0
    while True:
        batch = session.query(User).offset(offset).limit(batch_size).all()
        if not batch:
            break
        yield from batch
        offset += batch_size

# FASTER: Keyset pagination (no OFFSET penalty)
def iter_users_keyset(session, batch_size=1000):
    last_id = 0
    while True:
        batch = (session.query(User)
                 .filter(User.id > last_id)
                 .order_by(User.id)
                 .limit(batch_size)
                 .all())
        if not batch:
            break
        yield from batch
        last_id = batch[-1].id
```

### Pattern 5.5: Indexing Strategy

```python
# Add indexes for frequently queried columns
from sqlalchemy import Index

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)  # Single-column index
    status = Column(String)
    created_at = Column(DateTime)

    # Composite index for common query patterns
    __table_args__ = (
        Index('idx_status_created', 'status', 'created_at'),
    )
```

---

## 6. Concurrency and Parallelism

### Pattern 6.1: ThreadPoolExecutor for I/O-Bound Work

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

# SLOW: Sequential I/O
results = [fetch(url) for url in urls]

# FAST: Concurrent I/O
with ThreadPoolExecutor(max_workers=20) as executor:
    futures = {executor.submit(fetch, url): url for url in urls}
    results = {}
    for future in as_completed(futures):
        url = futures[future]
        results[url] = future.result()
```

### Pattern 6.2: ProcessPoolExecutor for CPU-Bound Work

```python
from concurrent.futures import ProcessPoolExecutor

# SLOW: Sequential CPU work (GIL bottleneck with threads)
results = [heavy_computation(item) for item in big_data]

# FAST: Parallel across CPU cores
with ProcessPoolExecutor() as executor:
    results = list(executor.map(heavy_computation, big_data))
```

### Pattern 6.3: asyncio for High-Concurrency I/O

```python
import asyncio
import aiohttp

async def fetch_all(urls, max_concurrent=50):
    """Fetch many URLs concurrently with rate limiting."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_one(session, url):
        async with semaphore:
            async with session.get(url) as resp:
                return await resp.json()

    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(
            *[fetch_one(session, url) for url in urls]
        )
```

### Pattern 6.4: Chunked Parallel Processing

```python
from concurrent.futures import ProcessPoolExecutor
import itertools

def chunk(iterable, size):
    """Split iterable into chunks of given size."""
    it = iter(iterable)
    while batch := list(itertools.islice(it, size)):
        yield batch

def process_chunk(items):
    """Process a chunk of items (runs in subprocess)."""
    return [heavy_computation(item) for item in items]

# Process large dataset in parallel chunks
with ProcessPoolExecutor() as executor:
    chunks = list(chunk(huge_dataset, 1000))
    results = []
    for chunk_result in executor.map(process_chunk, chunks):
        results.extend(chunk_result)
```

---

## 7. Python-Specific Performance Idioms

### Pattern 7.1: Local Variable Access

```python
# SLOW: Global/attribute lookup in tight loop
import math

def compute(data):
    return [math.sqrt(x) for x in data]

# FAST: Local variable binding
def compute(data):
    sqrt = math.sqrt  # Bind to local
    return [sqrt(x) for x in data]

# ~15-20% faster for tight loops due to LOAD_FAST vs LOAD_GLOBAL
```

### Pattern 7.2: str.join() vs Concatenation

```python
# SLOW: O(n²) — creates new string each iteration
result = ""
for chunk in chunks:
    result += chunk

# FAST: O(n) — single allocation
result = ''.join(chunks)

# For building complex strings
from io import StringIO
buffer = StringIO()
for chunk in chunks:
    buffer.write(chunk)
result = buffer.getvalue()
```

### Pattern 7.3: List Comprehension vs Loop

```python
# SLOW: append in loop
result = []
for x in data:
    if x > 0:
        result.append(x ** 2)

# FAST: List comprehension (~30% faster)
result = [x ** 2 for x in data if x > 0]

# FASTEST for large data: Generator (lazy, memory-efficient)
result = (x ** 2 for x in data if x > 0)  # No list created
```

### Pattern 7.4: dict.get() vs try/except vs if/in

```python
# Context-dependent — choose based on expected hit rate

# FAST when key usually exists (EAFP)
try:
    value = d[key]
except KeyError:
    value = default

# FAST when key often missing (LBYL)
value = d.get(key, default)

# For frequent access patterns:
# If >90% hit rate: try/except is fastest
# If <50% hit rate: dict.get() is fastest
```

### Pattern 7.5: __slots__ for Memory and Speed

```python
# SLOW: Regular class (each instance has __dict__)
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
# ~100-200 bytes per instance

# FAST: Slotted class (~40-60% less memory, faster attribute access)
class Point:
    __slots__ = ('x', 'y')
    def __init__(self, x, y):
        self.x = x
        self.y = y
# ~50-70 bytes per instance
```

### Pattern 7.6: Avoid Repeated Attribute Access

```python
# SLOW: Multiple dot lookups per iteration
for item in data:
    self.container.items.append(item.process())

# FAST: Cache the references
container_items = self.container.items
append = container_items.append
for item in data:
    append(item.process())
```

### Pattern 7.7: Use Built-in Functions

```python
# SLOW: Manual implementation
total = 0
for x in data:
    total += x

# FAST: C-implemented built-in
total = sum(data)

# Other fast built-ins:
max(data), min(data)       # vs manual loop
sorted(data)               # Timsort, C implementation
map(func, data)            # C-speed iteration
filter(pred, data)         # C-speed filtering
any(pred(x) for x in data) # Short-circuit
all(pred(x) for x in data) # Short-circuit
```

### Pattern 7.8: Precompile Regular Expressions

```python
import re

# SLOW: Recompiles on every call
def find_emails(text):
    return re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)

# FAST: Compile once
EMAIL_PATTERN = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')

def find_emails(text):
    return EMAIL_PATTERN.findall(text)
```

---

## 8. Memory Optimization

### Pattern 8.1: Generators Instead of Lists

```python
# SLOW: Creates full list in memory
def get_squares(n):
    return [i ** 2 for i in range(n)]  # Stores all n items

# FAST: Generates one at a time
def get_squares(n):
    return (i ** 2 for i in range(n))  # Stores 1 item at a time

# For file processing:
def process_lines(filename):
    with open(filename) as f:
        for line in f:  # Generator — one line at a time
            yield process(line)
```

### Pattern 8.2: itertools for Memory-Efficient Operations

```python
import itertools

# Memory-efficient chaining
combined = itertools.chain(list1, list2, list3)  # No new list created

# Memory-efficient slicing
first_100 = itertools.islice(huge_generator, 100)  # No list created

# Memory-efficient grouping
for key, group in itertools.groupby(sorted_data, key=lambda x: x.category):
    process_group(key, group)

# Memory-efficient product (vs nested loops)
for a, b, c in itertools.product(range(100), repeat=3):
    ...
```

### Pattern 8.3: __slots__ and namedtuple for Object Collections

```python
# For millions of simple objects:

# Option 1: namedtuple (immutable, memory-efficient)
from collections import namedtuple
Point = namedtuple('Point', ['x', 'y', 'z'])

# Option 2: __slots__ class (mutable, memory-efficient)
class Point:
    __slots__ = ('x', 'y', 'z')
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

# Option 3: dataclass with slots (Python 3.10+)
from dataclasses import dataclass

@dataclass(slots=True)
class Point:
    x: float
    y: float
    z: float
```

### Pattern 8.4: Weak References for Caches

```python
import weakref

# PROBLEM: Cache prevents garbage collection
cache = {}

def get_resource(key):
    if key not in cache:
        cache[key] = create_expensive_resource(key)
    return cache[key]  # Resource never freed!

# SOLUTION: Weak references allow GC
cache = weakref.WeakValueDictionary()

def get_resource(key):
    resource = cache.get(key)
    if resource is None:
        resource = create_expensive_resource(key)
        cache[key] = resource  # Will be GC'd when no other refs
    return resource
```

### Pattern 8.5: Array Module for Typed Arrays

```python
import array

# SLOW: List of ints (each int is a full Python object ~28 bytes)
numbers = [0] * 1_000_000  # ~28 MB

# FAST: Typed array (4 bytes per int)
numbers = array.array('i', [0] * 1_000_000)  # ~4 MB

# FASTEST: numpy array
import numpy as np
numbers = np.zeros(1_000_000, dtype=np.int32)  # ~4 MB + vectorized ops
```

---

## 9. Serialization Optimization

### Pattern 9.1: Fast JSON Libraries

```python
# SLOW: stdlib json
import json
data = json.dumps(obj)
obj = json.loads(data)

# FAST: orjson (3-10x faster)
import orjson
data = orjson.dumps(obj)  # Returns bytes
obj = orjson.loads(data)

# FAST: ujson (2-5x faster, more compatible)
import ujson
data = ujson.dumps(obj)
obj = ujson.loads(data)

# FAST: msgspec (type-safe, very fast)
import msgspec

class User(msgspec.Struct):
    name: str
    age: int

encoder = msgspec.json.Encoder()
decoder = msgspec.json.Decoder(User)
data = encoder.encode(user)
user = decoder.decode(data)
```

### Pattern 9.2: Binary Serialization

```python
# For internal data (not human-readable):

# MessagePack (compact, fast)
import msgpack
data = msgpack.packb(obj)
obj = msgpack.unpackb(data)

# Protocol Buffers (schema-defined, very compact)
# Requires .proto file and code generation

# pickle (Python-specific, fast for complex objects)
import pickle
data = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
obj = pickle.loads(data)
```

### Pattern 9.3: Streaming Serialization

```python
import json

# SLOW: Build entire JSON string in memory
output = json.dumps(huge_list)

# FAST: Stream to file
with open('output.json', 'w') as f:
    f.write('[\n')
    for i, item in enumerate(huge_list):
        if i > 0:
            f.write(',\n')
        json.dump(item, f)
    f.write('\n]')
```

---

## 10. Numerical and Data Processing

### Pattern 10.1: NumPy Vectorization

```python
import numpy as np

# SLOW: Python loop
def normalize(data):
    result = []
    mean = sum(data) / len(data)
    std = (sum((x - mean) ** 2 for x in data) / len(data)) ** 0.5
    for x in data:
        result.append((x - mean) / std)
    return result

# FAST: NumPy vectorized (10-100x faster)
def normalize(data):
    arr = np.asarray(data)
    return (arr - arr.mean()) / arr.std()
```

### Pattern 10.2: Avoid pandas .apply() and .iterrows()

```python
import pandas as pd

# SLOW: iterrows — Python-speed iteration
for idx, row in df.iterrows():
    df.at[idx, 'result'] = row['a'] + row['b']

# SLOW: apply — slightly better but still Python-speed
df['result'] = df.apply(lambda row: row['a'] + row['b'], axis=1)

# FAST: Vectorized operation (C-speed)
df['result'] = df['a'] + df['b']

# For complex logic, use np.where or np.select
df['category'] = np.where(df['value'] > 100, 'high', 'low')

conditions = [
    df['value'] > 100,
    df['value'] > 50,
    df['value'] > 0,
]
choices = ['high', 'medium', 'low']
df['category'] = np.select(conditions, choices, default='zero')
```

### Pattern 10.3: Chunked DataFrame Processing

```python
# SLOW: Load entire CSV (may OOM)
df = pd.read_csv('huge_file.csv')

# FAST: Process in chunks
chunks = pd.read_csv('huge_file.csv', chunksize=10000)
results = []
for chunk in chunks:
    processed = process_chunk(chunk)
    results.append(processed)
final = pd.concat(results)

# FASTER: Use Polars for large data
import polars as pl
df = pl.scan_csv('huge_file.csv')  # Lazy — builds query plan
result = (
    df.filter(pl.col('value') > 100)
    .group_by('category')
    .agg(pl.col('amount').sum())
    .collect()  # Executes optimized query
)
```

### Pattern 10.4: Use Appropriate dtypes

```python
import pandas as pd
import numpy as np

# SLOW: Default dtypes waste memory
df = pd.read_csv('data.csv')
# int64 for small numbers, object for categories

# FAST: Optimized dtypes
df = pd.read_csv('data.csv', dtype={
    'id': np.int32,           # Instead of int64
    'count': np.int16,        # If max < 32767
    'category': 'category',   # Instead of object (huge savings for repeated strings)
    'flag': bool,             # Instead of int64
    'amount': np.float32,     # Instead of float64 (if precision allows)
})

# Auto-optimize existing DataFrame
def optimize_dtypes(df):
    for col in df.select_dtypes(include=['int']):
        df[col] = pd.to_numeric(df[col], downcast='integer')
    for col in df.select_dtypes(include=['float']):
        df[col] = pd.to_numeric(df[col], downcast='float')
    for col in df.select_dtypes(include=['object']):
        if df[col].nunique() / len(df) < 0.5:
            df[col] = df[col].astype('category')
    return df
```

---

## Quick Reference: Optimization Decision Tree

```
Is the code slow?
├── Profile first! (cProfile, py-spy)
├── CPU-bound?
│   ├── Bad algorithm? → Fix algorithm (Section 1)
│   ├── Wrong data structure? → Switch (Section 2)
│   ├── Repeated work? → Cache it (Section 3)
│   ├── Python loop over data? → Vectorize with numpy (Section 10)
│   ├── Single-threaded CPU? → multiprocessing (Section 6)
│   └── Tight loop? → Python idioms (Section 7)
├── I/O-bound?
│   ├── Sequential requests? → async or threads (Section 4, 6)
│   ├── DB queries? → Optimize queries (Section 5)
│   ├── File I/O? → Buffering, streaming (Section 4)
│   └── Serialization? → Faster library (Section 9)
└── Memory-bound?
    ├── Large collections? → Generators (Section 8)
    ├── Many objects? → __slots__, namedtuple (Section 8)
    ├── Large DataFrames? → Optimize dtypes, chunk (Section 10)
    └── Memory leak? → objgraph, tracemalloc (profiling_guide.md)
```