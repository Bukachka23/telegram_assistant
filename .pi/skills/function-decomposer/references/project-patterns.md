# Project-Specific Refactoring Patterns

## Thresholds

| Metric | Trigger Refactoring |
|--------|---------------------|
| Lines of code | > 25 lines |
| Cyclomatic complexity | > 10 |
| Parameters | > 4 parameters |
| Nesting depth | > 3 levels |
| Responsibilities | > 2 distinct operations |

## Module Structure

```
src/
├── services/           # Business logic orchestrators
│   └── user_service.py
├── validators/         # Input validation functions
│   └── user_validators.py
├── utils/              # Pure utility functions
│   ├── hashing.py
│   └── formatting.py
├── repositories/       # Data access layer
│   └── user_repository.py
└── notifications/      # External communication
    └── email_sender.py
```

## Naming Patterns (Customize for your project)

```python
# Validators - always raise or return validated data
validate_<entity>()      # validate_user_input()
check_<condition>()      # check_permissions()
ensure_<state>()         # ensure_authenticated()

# Creators/Builders
create_<entity>()        # create_user_profile()
build_<structure>()      # build_response()
make_<thing>()           # make_request()

# Transformers
to_<format>()            # to_dict(), to_json()
from_<source>()          # from_request()
convert_<what>()         # convert_currency()
parse_<input>()          # parse_date()

# I/O Operations
fetch_<entity>()         # fetch_user()
save_<entity>()          # save_order()
send_<message>()         # send_email()
load_<resource>()        # load_config()

# Computations
calculate_<metric>()     # calculate_total()
compute_<value>()        # compute_hash()
get_<derived>()          # get_age_from_birthdate()
```

## Common Extraction Patterns

### FastAPI/Flask Endpoints

```python
# BEFORE: Fat endpoint
@router.post("/users")
async def create_user(request: UserCreate):
    # 50 lines of validation, business logic, DB calls...

# AFTER: Thin endpoint + service layer
@router.post("/users")
async def create_user(request: UserCreate):
    validated = validate_user_create(request)
    user = await user_service.register(validated)
    return UserResponse.from_entity(user)
```

### Repository Pattern

```python
# Extract DB operations
class UserRepository:
    def save(self, user: User) -> int: ...
    def find_by_email(self, email: str) -> User | None: ...
    def exists(self, email: str) -> bool: ...
```

### Domain Services

```python
# Business logic orchestration
class RegistrationService:
    def __init__(self, repo: UserRepository, emailer: EmailSender):
        self.repo = repo
        self.emailer = emailer
    
    def register(self, data: UserCreate) -> User:
        # Orchestrate: validate -> create -> save -> notify
        pass
```

## When to Use Classes vs Functions

| Scenario | Prefer |
|----------|--------|
| Stateless operations | Functions |
| Shared dependencies | Class with DI |
| Multiple related operations | Class grouping |
| Single operation, no state | Standalone function |
| Complex initialization | Class with __init__ |

## Project-Specific Rules

Add your custom rules here:

```python
# Example: Always extract API calls
# Example: Validation functions go in validators/ module
# Example: Use async for all I/O operations
# Example: Maximum function length: 20 lines
```