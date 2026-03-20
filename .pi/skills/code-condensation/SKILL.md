---
name: code-condensation
description: Optimize and reduce Python code size without changing logic. Use when the user wants to make code more concise, reduce LOC (Lines of Code), eliminate verbosity, or make code more "Pythonic" while STRICTLY preserving original business logic, input data, and output results. Triggers include requests to "condense", "shorten", "optimize size", "reduce lines", "make more concise", "remove boilerplate", or "make more Pythonic" without adding new features.
---

# Python Code Condensation

## Mission

Reduce Lines of Code (LOC) while STRICTLY preserving:
- ✅ Original business logic and algorithms
- ✅ Input data contracts and validation
- ✅ Output results and return values
- ✅ Error handling behavior
- ✅ Side effects and state changes

## Core Principle

**Every line removed must be justified.** Code condensation is about removing unnecessary verbosity, not removing necessary clarity. The goal is Pythonic conciseness, not code golf.

## Condensation Strategy

### 1. Quick Assessment

Scan the code for high-impact opportunities:
- **Verbose patterns** → Can be replaced with Python idioms
- **Redundant code** → Can be consolidated
- **Unnecessary abstractions** → Can be inlined
- **Explicit loops** → Can use comprehensions or built-ins
- **Boilerplate** → Can leverage standard library

### 2. Apply Condensation Patterns

Use the comprehensive patterns in `references/condensation_patterns.md`:

```bash
view references/condensation_patterns.md
```

The reference contains 25+ condensation patterns organized by category:
- Boolean and conditional simplification
- Collection operations and comprehensions
- Function composition and chaining
- Context managers and resource handling
- Dictionary and data structure operations
- Import and module organization
- String operations and formatting
- Exception handling
- Iterator and generator patterns
- Class and method condensation

### 3. Measure Impact

Track the condensation:
- **Before LOC**: Count original lines
- **After LOC**: Count condensed lines
- **LOC Saved**: Calculate reduction
- **Logic Preserved**: Verify behavior unchanged

### 4. Verify Preservation

Critical verification checklist:
- [ ] Same inputs produce same outputs
- [ ] Same exceptions raised in same conditions
- [ ] Same side effects (file writes, API calls, state changes)
- [ ] Same performance characteristics (no algorithmic changes)
- [ ] Tests still pass (if available)

## Condensation Workflow

### Step 1: Understand the Code

Before condensing, ensure full understanding:
- What does this code do?
- What are the inputs and outputs?
- What are the edge cases and error conditions?
- What are the performance requirements?

### Step 2: Identify Condensation Opportunities

Scan for common verbose patterns:

**High-Impact Targets:**
- Loops that build collections → comprehensions
- Multiple if-elif-else → dictionary dispatch or match/case
- Explicit boolean comparisons → direct boolean operations
- Redundant intermediate variables → inline expressions
- Verbose exception handling → contextlib utilities
- Explicit file operations → context managers

**Medium-Impact Targets:**
- Multiple similar operations → map/filter/reduce
- Repeated code blocks → helper functions
- Verbose string formatting → f-strings
- Manual iteration → itertools functions

**Low-Impact Targets:**
- Minor variable naming → use shorter but clear names
- Import organization → combine similar imports
- Docstring condensation → more concise documentation

### Step 3: Apply Patterns from Reference

Read the relevant sections of `references/condensation_patterns.md` and apply appropriate patterns. Each pattern includes:
- Before/after examples
- When to apply
- When NOT to apply (readability concerns)
- LOC impact estimation

### Step 4: Test and Validate

After condensation:
1. Run existing tests (if available)
2. Manually verify outputs match for sample inputs
3. Check edge cases and error conditions
4. Review for readability - did you go too far?

## Anti-Patterns: When NOT to Condense

**Don't sacrifice readability:**
```python
# TOO CONDENSED - hard to understand
result = [y for x in data if x > 0 for y in process(x) if validate(y)]

# BETTER - clear intent
filtered = [x for x in data if x > 0]
processed = [process(x) for x in filtered]
result = [y for y in processed if validate(y)]
```

**Don't remove necessary error handling:**
```python
# BAD - removed important error context
try: data = json.loads(text)
except: data = {}

# GOOD - preserved error handling
try:
    data = json.loads(text)
except json.JSONDecodeError as e:
    logger.error(f"Failed to parse JSON: {e}")
    data = {}
```

**Don't inline complex logic:**
```python
# BAD - too complex in one line
return {k: v for k, v in ((compute_key(x), process_value(x)) for x in data) if v is not None}

# GOOD - readable steps
items = ((compute_key(x), process_value(x)) for x in data)
return {k: v for k, v in items if v is not None}
```

## Common Condensation Scenarios

### Scenario 1: Verbose Function with Explicit Loops

**Before (15 lines):**
```python
def get_active_users(users):
    active = []
    for user in users:
        if user.status == 'active':
            if user.last_login:
                if (datetime.now() - user.last_login).days < 30:
                    active.append(user)
    return active
```

**After (3 lines):**
```python
def get_active_users(users):
    cutoff = datetime.now() - timedelta(days=30)
    return [u for u in users if u.status == 'active' and u.last_login and u.last_login > cutoff]
```

**LOC Saved: 12 lines (80% reduction)**

### Scenario 2: Dictionary Building with Explicit Loops

**Before (8 lines):**
```python
def build_lookup(items):
    result = {}
    for item in items:
        if item.active:
            result[item.id] = item.name
    return result
```

**After (2 lines):**
```python
def build_lookup(items):
    return {item.id: item.name for item in items if item.active}
```

**LOC Saved: 6 lines (75% reduction)**

### Scenario 3: Multiple Conditional Checks

**Before (12 lines):**
```python
def get_status(value):
    if value >= 90:
        return 'excellent'
    elif value >= 70:
        return 'good'
    elif value >= 50:
        return 'fair'
    else:
        return 'poor'
```

**After (2 lines):**
```python
def get_status(value):
    return next((s for t, s in [(90, 'excellent'), (70, 'good'), (50, 'fair')] if value >= t), 'poor')
```

**Alternative (4 lines - more readable):**
```python
def get_status(value):
    thresholds = [(90, 'excellent'), (70, 'good'), (50, 'fair'), (0, 'poor')]
    return next(status for threshold, status in thresholds if value >= threshold)
```

## Output Format

After condensation, provide:

1. **Summary**
   - Original LOC: X
   - Condensed LOC: Y
   - LOC Saved: Z (P% reduction)

2. **Key Changes**
   - List major condensation techniques applied
   - Note any trade-offs in readability

3. **Verification**
   - Confirm logic preservation
   - List any assumptions or caveats

4. **Condensed Code**
   - Present the optimized code
   - Add comments where condensation might reduce clarity

## Important Reminders

- **Never change business logic** - only change how it's expressed
- **Never remove necessary error handling** - preserve all error cases
- **Never sacrifice maintainability** - if condensed code is cryptic, keep it verbose
- **Never assume** - if unsure about behavior, ask before condensing
- **Always test** - verify behavior is preserved after condensation

## When to Use This Skill vs. python-refactoring-guide

**Use python-code-condensation when:**
- Primary goal is reducing LOC
- Code is verbose but functionally correct
- User explicitly wants more concise/Pythonic code
- No new features or logic changes needed

**Use python-refactoring-guide when:**
- Goal is improving overall code quality
- Code has structural issues (poor organization, coupling)
- Need to apply design patterns
- Working with class hierarchies and architecture

**Use both together when:**
- Code needs both structural improvement AND size reduction
- Comprehensive code cleanup is requested