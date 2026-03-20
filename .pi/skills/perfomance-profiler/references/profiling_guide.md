# Python Profiling Guide

## Table of Contents

1. [CPU Profiling](#cpu-profiling)
2. [Memory Profiling](#memory-profiling)
3. [I/O and Network Profiling](#io-and-network-profiling)
4. [Database Query Profiling](#database-query-profiling)
5. [Async Profiling](#async-profiling)
6. [Import and Startup Profiling](#import-and-startup-profiling)
7. [Statistical Benchmarking](#statistical-benchmarking)
8. [Interpreting Results](#interpreting-results)
9. [Profiling in Production](#profiling-in-production)

---

## CPU Profiling

### cProfile (stdlib — deterministic profiler)

**When:** First-pass profiling to identify which functions are slowest.

```python
# Method 1: Command line
# python -m cProfile -s cumulative script.py

# Method 2: Programmatic
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# ... code to profile ...

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(30)  # Top 30 functions

# Save for visualization
stats.dump_stats('output.prof')
```

**Reading cProfile output:**

```
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
   1000    0.523    0.001    2.150    0.002 processor.py:45(process_item)
   50000   1.200    0.000    1.200    0.000 utils.py:12(validate)
   1       0.001    0.001    5.340    5.340 main.py:10(run_pipeline)
```

- **ncalls**: Number of times the function was called
- **tottime**: Total time IN the function (excluding sub-calls)
- **cumtime**: Cumulative time IN the function (including sub-calls)
- **percall**: Per-call average

**Key insight:** If `tottime` is high, the function itself is slow. If `cumtime` is high but `tottime` is low, the function calls slow sub-functions.

### Visualization with snakeviz

```bash
pip install snakeviz
python -m cProfile -o output.prof script.py
snakeviz output.prof
# Opens browser with interactive flame chart
```

### py-spy (sampling profiler — zero overhead)

**When:** Profiling running processes, production profiling, or when cProfile overhead is too high.

```bash
pip install py-spy

# Record a flame graph
py-spy record -o profile.svg -- python script.py

# Attach to running process
py-spy record -o profile.svg --pid 12345

# Top-like live view
py-spy top --pid 12345

# Wall-clock time (includes I/O wait)
py-spy record --idle -o profile.svg -- python script.py
```

**py-spy vs cProfile:**
- py-spy: No code changes, low overhead, works on running processes, no Python API
- cProfile: More precise counts, programmatic control, stdlib, higher overhead

### line_profiler (line-by-line profiling)

**When:** You've identified a slow function and need to know which LINES are slow.

```bash
pip install line_profiler
```

```python
# Decorate the function to profile
@profile  # This decorator is added by kernprof
def slow_function(data):
    result = []                          # Line 1
    for item in data:                    # Line 2
        processed = transform(item)      # Line 3 — maybe this is slow?
        if validate(processed):          # Line 4 — or this?
            result.append(processed)     # Line 5
    return result                        # Line 6
```

```bash
kernprof -l -v script.py
```

**Output:**
```
Line #  Hits    Time    Per Hit  % Time  Line Contents
    3   10000   45000   4.5      85.2    processed = transform(item)
    4   10000   7000    0.7      13.2    if validate(processed):
    5   8500    800     0.1      1.5     result.append(processed)
```

### Scalene (CPU + Memory + GPU profiler)

**When:** Need both CPU and memory profiling in one pass.

```bash
pip install scalene
scalene script.py
# or
scalene --cpu --memory --html --- script.py
```

Scalene provides:
- CPU time split between Python and C/native code
- Memory allocation and deallocation per line
- GPU time (if applicable)
- Copy volume (data movement)

---

## Memory Profiling

### tracemalloc (stdlib — allocation tracker)

**When:** Finding where memory is being allocated.

```python
import tracemalloc

tracemalloc.start(25)  # Store 25 frames of traceback

# ... code to profile ...

snapshot = tracemalloc.take_snapshot()

# Top allocations by line
top_stats = snapshot.statistics('lineno')
print("Top 15 allocations:")
for stat in top_stats[:15]:
    print(f"  {stat}")

# Top allocations by file
top_stats = snapshot.statistics('filename')
for stat in top_stats[:10]:
    print(f"  {stat}")

# Compare two snapshots (find memory leaks)
snapshot1 = tracemalloc.take_snapshot()
# ... run more code ...
snapshot2 = tracemalloc.take_snapshot()

top_stats = snapshot2.compare_to(snapshot1, 'lineno')
print("Memory growth:")
for stat in top_stats[:10]:
    print(f"  {stat}")
```

### memory_profiler (line-by-line memory)

**When:** Need to see memory usage per line of a function.

```bash
pip install memory_profiler
```

```python
from memory_profiler import profile

@profile
def memory_heavy_function():
    big_list = [i ** 2 for i in range(1000000)]  # +38 MiB
    filtered = [x for x in big_list if x % 2 == 0]  # +19 MiB
    del big_list  # -38 MiB
    return sum(filtered)
```

```bash
python -m memory_profiler script.py
```

**Output:**
```
Line #  Mem usage    Increment  Occurrences   Line Contents
    4   45.2 MiB    38.0 MiB     1           big_list = [...]
    5   64.1 MiB    18.9 MiB     1           filtered = [...]
    6   26.2 MiB   -37.9 MiB     1           del big_list
```

### objgraph (object reference graphs)

**When:** Debugging memory leaks, understanding object relationships.

```bash
pip install objgraph
```

```python
import objgraph

# Show most common types
objgraph.show_most_common_types(limit=15)

# Show growth between two points
objgraph.show_growth(limit=10)
# ... run code ...
objgraph.show_growth(limit=10)  # Shows new objects

# Find what's referencing an object (why it's not GC'd)
objgraph.show_backrefs(
    objgraph.by_type('MyClass')[0],
    max_depth=5,
    filename='refs.png'
)
```

### sys.getsizeof and pympler

**When:** Measuring the size of specific objects.

```python
import sys

# Basic size (doesn't include referenced objects!)
sys.getsizeof([1, 2, 3])  # Size of list object itself

# Deep size with pympler
from pympler import asizeof
asizeof.asizeof({'key': [1, 2, 3, {'nested': 'dict'}]})  # Full deep size
```

---

## I/O and Network Profiling

### Timing I/O Operations

```python
import time
import contextlib

@contextlib.contextmanager
def io_timer(operation_name):
    """Context manager to time I/O operations."""
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    print(f"[I/O] {operation_name}: {elapsed:.4f}s")

# Usage
with io_timer("read large file"):
    data = open("huge_file.csv").read()

with io_timer("API call"):
    response = requests.get("https://api.example.com/data")

with io_timer("DB query"):
    results = db.execute("SELECT * FROM users").fetchall()
```

### Identifying I/O Bottlenecks with py-spy

```bash
# Wall-clock mode captures I/O wait time
py-spy record --idle -o profile.svg -- python script.py

# Compare with CPU-only mode
py-spy record -o profile_cpu.svg -- python script.py
```

If wall-clock profile shows much more time than CPU profile, the bottleneck is I/O.

### Network Request Profiling

```python
import requests
import time

class ProfilingSession(requests.Session):
    """Session that logs timing for all requests."""

    def request(self, method, url, **kwargs):
        start = time.perf_counter()
        response = super().request(method, url, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"[HTTP] {method} {url} → {response.status_code} ({elapsed:.3f}s)")
        return response

# Usage
session = ProfilingSession()
session.get("https://api.example.com/data")
```

---

## Database Query Profiling

### SQLAlchemy Query Logging

```python
import logging
import time
from sqlalchemy import event

# Enable SQL logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Detailed timing with events
@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.perf_counter())

@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.perf_counter() - conn.info["query_start_time"].pop()
    if total > 0.1:  # Log slow queries (>100ms)
        print(f"[SLOW QUERY] {total:.3f}s: {statement[:200]}")
```

### Detecting N+1 Queries

```python
class QueryCounter:
    """Context manager to count and detect N+1 queries."""

    def __init__(self, engine, threshold=10):
        self.engine = engine
        self.threshold = threshold
        self.queries = []

    def __enter__(self):
        @event.listens_for(self.engine, "before_cursor_execute")
        def receive_before(conn, cursor, statement, params, context, executemany):
            self.queries.append(statement)
        self._listener = receive_before
        return self

    def __exit__(self, *args):
        event.remove(self.engine, "before_cursor_execute", self._listener)
        if len(self.queries) > self.threshold:
            print(f"⚠️  N+1 DETECTED: {len(self.queries)} queries executed")
            # Group by pattern
            from collections import Counter
            patterns = Counter(q.split('WHERE')[0].strip() for q in self.queries)
            for pattern, count in patterns.most_common(5):
                print(f"  {count}x: {pattern[:100]}")

# Usage
with QueryCounter(engine) as qc:
    users = session.query(User).all()
    for user in users:
        print(user.orders)  # N+1 if not eagerly loaded
```

### PostgreSQL EXPLAIN ANALYZE

```python
def explain_query(session, query):
    """Run EXPLAIN ANALYZE on a query."""
    explain_sql = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {query}"
    result = session.execute(explain_sql)
    for row in result:
        print(row[0])
```

Key things to look for in EXPLAIN output:
- **Seq Scan** on large tables → needs an index
- **Nested Loop** with high row counts → consider JOIN optimization
- **Sort** with high memory → needs index for ORDER BY
- **Hash Join** with large hash tables → memory pressure

---

## Async Profiling

### asyncio Debug Mode

```python
import asyncio
import logging

# Enable asyncio debug mode
logging.basicConfig(level=logging.DEBUG)
asyncio.get_event_loop().set_debug(True)

# Warns about:
# - Coroutines that were never awaited
# - Callbacks taking too long (>100ms by default)
# - Blocking the event loop
```

### Profiling Async Functions

```python
import asyncio
import time

def async_timer(func):
    """Decorator to time async functions."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"[ASYNC] {func.__name__}: {elapsed:.4f}s")
        return result
    return wrapper

# Detect event loop blocking
class EventLoopMonitor:
    """Detect when the event loop is blocked."""

    def __init__(self, loop, threshold=0.1):
        self.loop = loop
        self.threshold = threshold
        self._last_check = time.monotonic()

    async def monitor(self):
        while True:
            await asyncio.sleep(0.05)
            now = time.monotonic()
            delta = now - self._last_check
            if delta > self.threshold:
                print(f"⚠️  Event loop blocked for {delta:.3f}s")
            self._last_check = now
```

### Identifying Concurrency Issues

```python
async def profile_gather(*coros):
    """Profile concurrent execution to find serialization issues."""
    total_start = time.perf_counter()
    
    async def timed_coro(name, coro):
        start = time.perf_counter()
        result = await coro
        elapsed = time.perf_counter() - start
        return name, elapsed, result

    results = await asyncio.gather(
        *[timed_coro(f"task_{i}", c) for i, c in enumerate(coros)]
    )

    total_elapsed = time.perf_counter() - total_start
    sum_individual = sum(r[1] for r in results)

    print(f"Total wall time: {total_elapsed:.3f}s")
    print(f"Sum of individual times: {sum_individual:.3f}s")
    print(f"Concurrency efficiency: {sum_individual / total_elapsed:.1f}x")

    for name, elapsed, _ in sorted(results, key=lambda r: -r[1]):
        print(f"  {name}: {elapsed:.3f}s")
```

---

## Import and Startup Profiling

### python -X importtime

```bash
# Show import times for all modules
python -X importtime script.py 2>&1 | sort -t: -k2 -n | tail -20

# Typical output:
# import time: self [us] | cumulative | imported package
# import time:      2145 |       8923 | numpy
# import time:       312 |       5120 | pandas
```

### Lazy Imports

```python
# BEFORE: Slow startup due to heavy imports at module level
import pandas as pd          # ~150ms
import numpy as np           # ~80ms
import matplotlib.pyplot as plt  # ~200ms

def rarely_used_function(data):
    return pd.DataFrame(data).plot()

# AFTER: Lazy import — only loaded when needed
def rarely_used_function(data):
    import pandas as pd
    import matplotlib.pyplot as plt
    return pd.DataFrame(data).plot()

# Or use importlib for more control
import importlib

def get_pandas():
    return importlib.import_module('pandas')
```

### Startup Profiling Script

```python
import time
import importlib

MODULES_TO_CHECK = [
    'numpy', 'pandas', 'requests', 'sqlalchemy',
    'flask', 'django', 'fastapi', 'pydantic',
]

for mod_name in MODULES_TO_CHECK:
    try:
        start = time.perf_counter()
        importlib.import_module(mod_name)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"  {mod_name}: {elapsed:.1f}ms")
    except ImportError:
        pass
```

---

## Statistical Benchmarking

### Proper Benchmarking Methodology

```python
import timeit
import statistics
import math

def benchmark(func, args=(), kwargs=None, min_rounds=5, min_time=1.0):
    """
    Statistically sound benchmarking.

    Runs enough iterations to get stable results,
    reports mean, median, stddev, and confidence interval.
    """
    kwargs = kwargs or {}

    # Warm-up phase (JIT, caches, etc.)
    for _ in range(3):
        func(*args, **kwargs)

    # Calibration: find how many iterations to fill min_time
    single = timeit.timeit(lambda: func(*args, **kwargs), number=1)
    number = max(1, int(min_time / single))

    # Collect samples
    times = []
    for _ in range(max(min_rounds, 5)):
        t = timeit.timeit(lambda: func(*args, **kwargs), number=number)
        times.append(t / number)

    mean = statistics.mean(times)
    median = statistics.median(times)
    stdev = statistics.stdev(times) if len(times) > 1 else 0
    ci95 = 1.96 * stdev / math.sqrt(len(times))

    return {
        'mean': mean,
        'median': median,
        'stdev': stdev,
        'ci95': ci95,
        'min': min(times),
        'max': max(times),
        'rounds': len(times),
        'iterations_per_round': number,
    }

def compare_benchmarks(implementations: dict, **kwargs):
    """Compare multiple implementations with statistical rigor."""
    results = {}
    for name, (func, args) in implementations.items():
        results[name] = benchmark(func, args=args, **kwargs)

    # Sort by median time
    sorted_results = sorted(results.items(), key=lambda x: x[1]['median'])
    baseline_median = sorted_results[0][1]['median']

    print(f"\n{'Name':<25} {'Median':>10} {'Mean':>10} {'StdDev':>10} {'CI95':>10} {'Speedup':>8}")
    print("-" * 78)
    for name, r in sorted_results:
        speedup = baseline_median / r['median'] if r['median'] > 0 else float('inf')
        print(f"{name:<25} {r['median']:.6f} {r['mean']:.6f} {r['stdev']:.6f} ±{r['ci95']:.6f} {speedup:.2f}x")

    return results
```

### Benchmarking Best Practices

1. **Warm up** — Run the function a few times before measuring to prime caches and JIT
2. **Multiple rounds** — Single measurements are noisy; run at least 5 rounds
3. **Report median** — Mean is skewed by outliers (GC pauses, OS scheduling)
4. **Report confidence interval** — Shows measurement reliability
5. **Control variables** — Same data, same machine, same load
6. **Disable GC for microbenchmarks** — `gc.disable()` during timing, re-enable after
7. **Use `time.perf_counter()`** — Highest resolution timer, includes sleep time
8. **Use `time.process_time()`** — CPU time only, excludes sleep/wait

---

## Interpreting Results

### Reading Flame Graphs

Flame graphs (from py-spy, Scalene) show:
- **X-axis**: Proportion of total time (NOT chronological)
- **Y-axis**: Call stack depth (bottom = entry point, top = leaf functions)
- **Width of bar**: Time spent in that function
- **Color**: Usually arbitrary, but can encode CPU vs I/O

**What to look for:**
- **Wide bars at the top** → Leaf functions consuming lots of time (optimize these)
- **Wide bars at the bottom** → Framework overhead (may need architectural changes)
- **Tall narrow stacks** → Deep call chains (consider flattening)
- **Flat tops ("plateaus")** → Time spread across many sub-calls

### Common Bottleneck Patterns

| Pattern | Symptom | Typical Cause |
|---------|---------|---------------|
| **One hot function** | Single function takes >50% time | Inefficient algorithm, missing cache |
| **Death by 1000 cuts** | Many functions each take 1-5% | Usually acceptable, look elsewhere |
| **I/O domination** | Wall-clock >> CPU time | Network/disk waits, needs async/batching |
| **Memory thrashing** | Frequent GC pauses | Too many small allocations, need pooling |
| **Serialization tax** | JSON/pickle in hot path | Use faster serializers (orjson, msgpack) |
| **Import-time cost** | Slow startup, fast runtime | Lazy imports, lighter dependencies |
| **N+1 queries** | Linear DB calls growth | Eager loading, batch queries |
| **GIL contention** | Multi-threaded but no speedup | Use multiprocessing or async I/O |

### Red Flags in Profiling Data

- Function called **millions of times** → Can it be batched or vectorized?
- **String concatenation in loop** → Use `''.join()` or `io.StringIO`
- **`isinstance()` in tight loop** → Consider polymorphism or dictionary dispatch
- **`json.loads/dumps`** in hot path → Use `orjson` or `msgspec`
- **`re.compile`** called repeatedly → Compile once, reuse pattern
- **Global variable lookup** in tight loop → Assign to local variable
- **`.append()` in loop building list** → List comprehension
- **`in` on a `list`** → Convert to `set` for O(1) lookup
- **Excessive logging** in hot path → Check log level before formatting

---

## Profiling in Production

### Lightweight Production Profiling

```python
import cProfile
import signal
import threading

class OnDemandProfiler:
    """
    Enable profiling in production by sending SIGUSR1.
    Send SIGUSR1 to start, SIGUSR2 to stop and dump.
    """

    def __init__(self, output_dir="/tmp/profiles"):
        self.profiler = None
        self.output_dir = output_dir
        signal.signal(signal.SIGUSR1, self._start)
        signal.signal(signal.SIGUSR2, self._stop)

    def _start(self, signum, frame):
        self.profiler = cProfile.Profile()
        self.profiler.enable()
        print("Profiling started")

    def _stop(self, signum, frame):
        if self.profiler:
            self.profiler.disable()
            import datetime
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"{self.output_dir}/profile_{ts}.prof"
            self.profiler.dump_stats(path)
            print(f"Profile saved to {path}")
            self.profiler = None
```

### Sampling-Based Production Monitoring

```python
import threading
import traceback
import time
from collections import Counter

class StackSampler:
    """Lightweight stack sampler for production."""

    def __init__(self, interval=0.01):
        self.interval = interval
        self.samples = Counter()
        self._running = False

    def start(self):
        self._running = True
        thread = threading.Thread(target=self._sample_loop, daemon=True)
        thread.start()

    def stop(self):
        self._running = False

    def _sample_loop(self):
        import sys
        while self._running:
            for thread_id, frame in sys._current_frames().items():
                stack = ''.join(traceback.format_stack(frame))
                # Hash just the function names for grouping
                key = tuple(
                    f"{f.f_code.co_filename}:{f.f_code.co_name}"
                    for f in self._iter_frames(frame)
                )
                self.samples[key] += 1
            time.sleep(self.interval)

    @staticmethod
    def _iter_frames(frame):
        while frame:
            yield frame
            frame = frame.f_back

    def report(self, top_n=20):
        total = sum(self.samples.values())
        for stack, count in self.samples.most_common(top_n):
            pct = count / total * 100
            print(f"{pct:5.1f}% ({count:6d}) {' → '.join(stack[-3:])}")
```

### Metrics to Track in Production

```python
import time
import functools
from contextlib import contextmanager

# Use with Prometheus, StatsD, Datadog, etc.
class PerfMetrics:
    """Simple performance metrics collector."""

    def __init__(self):
        self.timings = {}
        self.counters = {}

    def timer(self, name):
        """Decorator to time a function."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    return func(*args, **kwargs)
                finally:
                    elapsed = time.perf_counter() - start
                    self.timings.setdefault(name, []).append(elapsed)
            return wrapper
        return decorator

    @contextmanager
    def time_block(self, name):
        """Context manager to time a block."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self.timings.setdefault(name, []).append(elapsed)

    def report(self):
        """Print summary of all recorded metrics."""
        for name, times in sorted(self.timings.items()):
            import statistics
            print(f"{name}:")
            print(f"  count={len(times)}, mean={statistics.mean(times):.4f}s, "
                  f"p50={statistics.median(times):.4f}s, "
                  f"p99={sorted(times)[int(len(times)*0.99)]:.4f}s")
```