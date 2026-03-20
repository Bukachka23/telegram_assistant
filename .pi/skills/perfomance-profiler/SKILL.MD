---
name: python-performance-profiler
description: Profile and optimize Python project performance. Use when the user wants to find bottlenecks, measure execution time, reduce memory usage, optimize slow code, or improve throughput. Triggers include requests to "profile", "benchmark", "optimize performance", "find bottlenecks", "speed up", "reduce memory", "why is this slow", or when working with code that has known performance issues. Covers CPU profiling, memory profiling, I/O analysis, async performance, database query optimization, and algorithmic complexity improvements.
---

# Python Performance Profiler & Optimizer

## Mission

Systematically identify and eliminate performance bottlenecks in Python projects using data-driven profiling, while preserving correctness and code quality.

**Core Principle:** _Measure first, optimize second._ Never optimize based on assumptions — always profile to identify the actual bottleneck before changing code.

## When to Use This Skill

Use this skill when:
- User reports slow code or asks "why is this slow?"
- User wants to profile or benchmark Python code
- User asks to "speed up", "optimize", or "improve performance"
- Working with code that processes large datasets, handles high traffic, or has latency requirements
- User mentions memory issues, OOM errors, or high memory usage
- User needs to compare performance of different implementations
- Code review reveals potential performance concerns (N+1 queries, nested loops over large data, etc.)

## Profiling & Optimization Workflow

### Phase 1: Understand the Context

Before profiling, gather critical context:
- **What is slow?** — Specific function, endpoint, pipeline, or the whole system?
- **How slow is it?** — Current numbers (latency, throughput, memory usage)
- **What is acceptable?** — Target performance requirements
- **What scale?** — Data size, request volume, concurrency
- **Environment?** — Python version, key libraries, deployment (local, Docker, cloud)

### Phase 2: Profile to Find Bottlenecks

**Choose the right profiler for the problem:**

| Symptom | Profiler | Tool |
|---------|----------|------|
| Slow execution | CPU profiler | `cProfile`, `py-spy`, `line_profiler` |
| High memory usage | Memory profiler | `tracemalloc`, `memory_profiler`, `objgraph` |
| Slow I/O operations | I/O profiler | `strace`, `py-spy` wall-clock mode |
| Slow DB queries | Query analyzer | `EXPLAIN ANALYZE`, Django debug toolbar |
| Async bottlenecks | Async profiler | `py-spy`, `asyncio` debug mode |
| Startup time | Import profiler | `python -X importtime` |

Read the comprehensive profiling guide:
```bash
view references/profiling_guide.md
```

### Phase 3: Analyze Results

Interpret profiling data following these principles:

1. **Focus on the hot path** — The top 3-5 functions consuming the most time/memory
2. **Look for disproportionate costs** — Functions called millions of times, or single calls taking seconds
3. **Distinguish CPU-bound vs I/O-bound** — Different problems need different solutions
4. **Check algorithmic complexity** — Is the bottleneck O(n²) when O(n) is possible?
5. **Identify low-hanging fruit** — Quick fixes that yield large improvements

### Phase 4: Optimize Strategically

Apply optimizations from highest to lowest impact:

```
1. Algorithmic improvements     (10x-1000x gains)
2. Data structure changes       (2x-100x gains)
3. Caching / memoization        (2x-100x gains for repeated work)
4. I/O optimization             (2x-50x gains)
5. Concurrency / parallelism    (2x-Nx gains, N = cores)
6. Python-specific idioms       (1.2x-5x gains)
7. C extensions / Cython        (2x-100x gains for compute-heavy)
```

Read the comprehensive optimization patterns:
```bash
view references/optimization_patterns.md
```

### Phase 5: Validate Improvements

After optimization:
1. **Re-profile** — Verify the bottleneck is actually resolved
2. **Benchmark comparison** — Quantify improvement with before/after numbers
3. **Regression test** — Ensure correctness is preserved
4. **Check for new bottlenecks** — Optimization can shift bottlenecks elsewhere
5. **Document** — Record what was changed and why

## Quick-Start Profiling Scripts

### CPU Profiling (cProfile)

```python
import cProfile
import pstats
from io import StringIO

def profile_function(func, *args, **kwargs):
    """Profile a function and print top bottlenecks."""
    profiler = cProfile.Profile()
    profiler.enable()
    result = func(*args, **kwargs)
    profiler.disable()

    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
    print(stream.getvalue())
    return result
```

### Memory Profiling (tracemalloc)

```python
import tracemalloc

def profile_memory(func, *args, **kwargs):
    """Profile memory allocation of a function."""
    tracemalloc.start()
    result = func(*args, **kwargs)
    snapshot = tracemalloc.take_snapshot()

    top_stats = snapshot.statistics('lineno')
    print("Top 10 memory allocations:")
    for stat in top_stats[:10]:
        print(f"  {stat}")

    current, peak = tracemalloc.get_traced_memory()
    print(f"\nCurrent: {current / 1024:.1f} KB, Peak: {peak / 1024:.1f} KB")
    tracemalloc.stop()
    return result
```

### Timing Decorator

```python
import time
import functools

def timer(func):
    """Decorator to measure function execution time."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__}: {elapsed:.4f}s")
        return result
    return wrapper
```

### Benchmark Comparison

```python
import timeit
import statistics

def compare_implementations(implementations: dict, setup="", number=1000, repeat=5):
    """Compare performance of multiple implementations."""
    results = {}
    for name, code in implementations.items():
        times = timeit.repeat(code, setup=setup, number=number, repeat=repeat)
        results[name] = {
            'mean': statistics.mean(times) / number,
            'median': statistics.median(times) / number,
            'stdev': statistics.stdev(times) / number,
            'min': min(times) / number,
        }

    # Print comparison table
    print(f"{'Implementation':<30} {'Mean':>12} {'Median':>12} {'StdDev':>12}")
    print("-" * 68)
    baseline_mean = None
    for name, stats_data in sorted(results.items(), key=lambda x: x[1]['mean']):
        if baseline_mean is None:
            baseline_mean = stats_data['mean']
        speedup = baseline_mean / stats_data['mean'] if stats_data['mean'] > 0 else float('inf')
        print(f"{name:<30} {stats_data['mean']:.6f}s {stats_data['median']:.6f}s {stats_data['stdev']:.6f}s")

    return results
```

## Common Performance Scenarios

### Scenario 1: Slow API Endpoint

**Diagnostic approach:**
1. Profile the endpoint handler with `cProfile`
2. Check for N+1 database queries
3. Look for synchronous I/O in async context
4. Check serialization overhead
5. Review middleware chain

### Scenario 2: High Memory Usage

**Diagnostic approach:**
1. Use `tracemalloc` to find top allocators
2. Check for large data structures held in memory
3. Look for memory leaks (growing collections, circular refs)
4. Review generator vs list usage
5. Check for large string concatenation

### Scenario 3: Slow Data Processing Pipeline

**Diagnostic approach:**
1. Profile each stage of the pipeline separately
2. Check algorithmic complexity of each stage
3. Look for redundant data transformations
4. Evaluate parallelization opportunities
5. Consider chunked/streaming processing

### Scenario 4: Slow Startup Time

**Diagnostic approach:**
1. Run `python -X importtime` to check import costs
2. Look for heavy imports done at module level
3. Check for expensive module-level computation
4. Consider lazy imports for optional dependencies

## Profiling Workflow for Different Project Types

### Web Applications (FastAPI, Django, Flask)

```bash
# 1. Profile endpoint with py-spy
py-spy record -o profile.svg -- python -m uvicorn app:app

# 2. Check DB queries
# Django: use django-debug-toolbar or django-silk
# SQLAlchemy: enable echo=True or use event listeners

# 3. Load test
locust -f locustfile.py --headless -u 100 -r 10 --run-time 60s
```

### Data Processing (pandas, numpy)

```bash
# 1. Profile with line_profiler for hot functions
kernprof -l -v script.py

# 2. Check vectorization opportunities
# Look for .apply(), iterrows(), Python loops over DataFrames

# 3. Memory profile large dataset operations
python -m memory_profiler script.py
```

### CLI Tools / Scripts

```bash
# 1. Full CPU profile
python -m cProfile -o output.prof script.py
snakeviz output.prof  # Visualize

# 2. Quick timing
time python script.py

# 3. Import time analysis
python -X importtime script.py 2>&1 | head -30
```

## Output Format

After profiling and optimization, provide:

1. **Profiling Summary**
   - Tool(s) used
   - Top bottlenecks identified (ranked by impact)
   - CPU-bound vs I/O-bound classification

2. **Optimization Plan**
   - Ranked list of optimizations by expected impact
   - Estimated effort for each
   - Risk assessment (correctness, maintainability)

3. **Implementation**
   - Optimized code with clear comments explaining changes
   - Before/after benchmark numbers
   - Any trade-offs made

4. **Validation**
   - Benchmark comparison (before vs after)
   - Correctness verification approach
   - Remaining bottlenecks (if any)

## Relationship to Other Skills

**Use python-performance-profiler when:**
- Primary goal is improving execution speed or reducing memory usage
- Code is functionally correct but too slow or memory-hungry
- Need to find and fix specific bottlenecks
- Comparing performance of alternative implementations

**Use python-refactoring-guide when:**
- Goal is improving code quality, readability, and maintainability
- Code has structural issues (not performance issues)
- Need to apply design patterns

**Use python-code-condensation when:**
- Goal is reducing lines of code while preserving logic
- Code is verbose but not necessarily slow

**Use together when:**
- Code needs both structural improvement AND performance optimization
- Refactoring first can reveal optimization opportunities
- Performance optimization should maintain code quality

## Resources

### references/profiling_guide.md
Comprehensive guide to Python profiling tools and techniques:
- CPU profiling (cProfile, py-spy, line_profiler, scalene)
- Memory profiling (tracemalloc, memory_profiler, objgraph)
- I/O and async profiling
- Database query profiling
- Interpreting profiling output
- Statistical benchmarking methodology

### references/optimization_patterns.md
25+ optimization patterns organized by category:
- Algorithmic optimizations
- Data structure selection
- Caching and memoization
- I/O and database optimization
- Concurrency and parallelism
- Python-specific performance idioms
- Memory optimization techniques
- Serialization and data format optimization