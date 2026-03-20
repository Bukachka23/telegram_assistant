---
name: function-decomposer
description: Refactor large or overhead functions into smaller, focused methods. Use when user adds new code with functions over 20 lines, mentions "refactor", "decompose", "extract method", "clean up", "simplify", or when detecting functions with multiple responsibilities, deeply nested logic, or repeated patterns.
---

# Function Decomposer

Automatically refactor large functions into smaller, single-responsibility methods while preserving original logic.

## When to Trigger

- Function exceeds 20-25 lines of code
- Function has multiple distinct operations (validation, transformation, I/O)
- Code comments indicate separate logical sections ("# Validate...", "# Process...", "# Send...")
- Deeply nested conditionals (3+ levels)
- Repeated patterns that can be extracted
- User explicitly asks to refactor, clean up, or simplify

## Refactoring Workflow

### Step 1: Analyze the Function

Identify decomposition candidates:

```
□ Multiple responsibilities (validation + processing + I/O)
□ Repeated code blocks
□ Distinct logical sections marked by comments
□ Deep nesting (if/for/while > 3 levels)
□ Multiple return paths with similar setup
□ Inline imports that could be module-level
```

### Step 2: Identify Extraction Boundaries

Look for natural breakpoints:

| Pattern | Extract As |
|---------|-----------|
| Validation logic | `validate_<entity>()` |
| Data transformation | `transform_<entity>()` or `create_<entity>()` |
| External I/O (API, DB, file) | `fetch_<entity>()`, `save_<entity>()` |
| Calculations | `calculate_<metric>()` |
| Formatting/serialization | `format_<entity>()` |
| Notifications/side effects | `send_<notification>()`, `notify_<event>()` |

### Step 3: Extract Functions

Follow this order (dependencies first):

1. **Pure functions first** - No side effects, easiest to extract
2. **Validation functions** - Input checking, return validated data or raise
3. **Transformation functions** - Data creation/modification
4. **I/O functions last** - External interactions

### Step 4: Refactor

Apply these rules:

```python
# BEFORE: Large function with mixed concerns
def process_order(order_data):
    # Validate items (10 lines)
    # Calculate totals (8 lines)
    # Apply discounts (12 lines)
    # Save to database (5 lines)
    # Send confirmation (6 lines)
    pass

# AFTER: Orchestrator + focused functions
def validate_order_items(items):
    """Validate order items exist and have stock."""
    # 10 lines of validation logic
    return validated_items

def calculate_order_total(items):
    """Calculate subtotal, tax, and total."""
    # 8 lines of calculation
    return {"subtotal": ..., "tax": ..., "total": ...}

def apply_discounts(totals, discount_code):
    """Apply discount code to order totals."""
    # 12 lines of discount logic
    return adjusted_totals

def save_order(order):
    """Persist order to database."""
    # 5 lines of DB logic
    return order_id

def send_order_confirmation(email, order_id):
    """Send confirmation email to customer."""
    # 6 lines of email logic
    pass

def process_order(order_data):
    """Orchestrate order processing."""
    items = validate_order_items(order_data["items"])
    totals = calculate_order_total(items)
    final_totals = apply_discounts(totals, order_data.get("discount_code"))
    
    order = {**order_data, "items": items, **final_totals}
    order_id = save_order(order)
    send_order_confirmation(order_data["email"], order_id)
    
    return order_id
```

## Extraction Rules

### Naming Conventions

```python
# Validation: validate_<what>
validate_email(email) -> str
validate_password(password) -> str
validate_user_input(data) -> dict

# Creation: create_<what> or build_<what>
create_user_profile(email, name) -> dict
build_response(data, status) -> Response

# Transformation: transform_<what> or convert_<what>
transform_to_dto(entity) -> dict
convert_currency(amount, from_cur, to_cur) -> float

# I/O: <action>_<what>
fetch_user(user_id) -> User
save_order(order) -> int
send_notification(user, message) -> None

# Calculations: calculate_<what> or compute_<what>
calculate_total(items) -> float
compute_hash(password, salt) -> str
```

### Function Signatures

```python
# Return validated/transformed data (not just bool)
def validate_email(email: str) -> str:  # Returns normalized email
    email = email.strip().lower()
    if not email:
        raise ValueError("Email is required")
    return email

# Single responsibility - do ONE thing
def hash_password(password: str, salt: str) -> str:
    """Hash password. Does NOT validate."""
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

# Keep extracted functions near the orchestrator
# Or move to dedicated module if reused across files
```

### Imports

```python
# BEFORE: Inline imports inside function
def create_profile():
    from datetime import datetime  # Bad: hidden dependency
    return {"created_at": datetime.now()}

# AFTER: Module-level imports
from datetime import datetime

def create_profile():
    return {"created_at": datetime.now()}
```

## Placement Strategy

```
# Same file - for tightly coupled helpers
src/
  user_service.py      # Contains process_registration + validate_* helpers

# Separate module - for reusable utilities
src/
  user_service.py      # Contains process_registration
  validators/
    user_validators.py # Contains validate_email, validate_password
  utils/
    hashing.py         # Contains hash_password
```

Decision matrix:
| Reused elsewhere? | Complex enough? | Action |
|-------------------|-----------------|--------|
| No | No | Keep in same file, above main function |
| No | Yes | Same file, consider future extraction |
| Yes | Any | Move to shared module |

## Preserve Logic Checklist

Before completing refactoring, verify:

```
□ All original functionality preserved
□ Same exceptions raised for same conditions
□ Same return values/types
□ Side effects occur in same order
□ No new dependencies introduced
□ Original function now acts as orchestrator (5-15 lines)
```

## Anti-Patterns to Avoid

```python
# ❌ Don't extract single-line operations
def get_email(data):
    return data.get("email", "")  # Too trivial

# ❌ Don't create functions that just wrap another
def validate(x):
    return do_validate(x)  # Pointless wrapper

# ❌ Don't break logical units
def validate_email_part1(email):  # Artificial split
    ...
def validate_email_part2(email):
    ...

# ❌ Don't extract if it requires passing 5+ parameters
def process(a, b, c, d, e, f):  # Consider a class instead
    ...

# ✅ DO extract when there's a clear single responsibility
# ✅ DO extract repeated patterns (3+ occurrences)
# ✅ DO extract when unit testing would be easier
```

## TypeScript/JavaScript Variant

```typescript
// BEFORE
async function processUserRegistration(userData: UserInput): Promise<User> {
  // 50+ lines of validation, hashing, DB, email...
}

// AFTER
const validateEmail = (email: string): string => {
  const normalized = email.trim().toLowerCase();
  if (!normalized || !normalized.includes('@')) {
    throw new ValidationError('Invalid email');
  }
  return normalized;
};

const validatePassword = (password: string): string => {
  if (password.length < 8) {
    throw new ValidationError('Password too short');
  }
  return password;
};

const hashPassword = async (password: string): Promise<string> => {
  return bcrypt.hash(password, 10);
};

const createUserProfile = (
  email: string, 
  username: string, 
  passwordHash: string
): UserProfile => ({
  email,
  username,
  passwordHash,
  createdAt: new Date().toISOString(),
  isActive: true,
  preferences: DEFAULT_PREFERENCES,
});

async function processUserRegistration(userData: UserInput): Promise<User> {
  const email = validateEmail(userData.email);
  const password = validatePassword(userData.password);
  const username = validateUsername(userData.username);

  const passwordHash = await hashPassword(password);
  const profile = createUserProfile(email, username, passwordHash);
  
  await saveUser(profile);
  await sendWelcomeEmail(email, username);

  return profile;
}
```

## After Refactoring

1. **Verify** - Run existing tests to ensure no regression
2. **Add tests** - New small functions are now easily unit-testable
3. **Document** - Add docstrings to extracted functions
4. **Review** - Main function should now be 5-15 lines, reading like documentation