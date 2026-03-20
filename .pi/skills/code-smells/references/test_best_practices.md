## 11. Testing Best Practices

### Test Structure — Arrange-Act-Assert

```python
def test_user_creation():
    # Arrange — set up test data
    user_data = UserCreate(email="test@example.com", name="Test User")
    repository = InMemoryUserRepository()
    service = UserService(repository)
    
    # Act — perform the action
    user = service.create_user(user_data)
    
    # Assert — verify results
    assert user.id is not None
    assert user.email == "test@example.com"
    assert repository.get_by_id(user.id) == user
```

### Pytest Fixtures

```python
import pytest
from typing import Generator

@pytest.fixture
def user() -> User:
    """Simple fixture returning a user."""
    return User(id=1, email="test@example.com", name="Test")

@pytest.fixture
def repository() -> InMemoryUserRepository:
    """Repository fixture."""
    return InMemoryUserRepository()

@pytest.fixture
def service(repository: InMemoryUserRepository) -> UserService:
    """Service with injected repository."""
    return UserService(repository)

# Fixtures with cleanup
@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    session = create_session()
    yield session
    session.rollback()
    session.close()

# Parametrized fixtures
@pytest.fixture(params=["sqlite", "postgres"])
def database(request) -> Database:
    if request.param == "sqlite":
        return SQLiteDatabase()
    return PostgresDatabase()
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("email,is_valid", [
    ("valid@example.com", True),
    ("also.valid@example.co.uk", True),
    ("invalid", False),
    ("@invalid.com", False),
    ("invalid@", False),
    ("", False),
])
def test_email_validation(email: str, is_valid: bool):
    result = validate_email(email)
    assert result == is_valid

@pytest.mark.parametrize("a,b,expected", [
    (2, 3, 5),
    (0, 0, 0),
    (-1, 1, 0),
    (100, -50, 50),
])
def test_addition(a: int, b: int, expected: int):
    assert add(a, b) == expected
```

### Mocking with pytest-mock

```python
import pytest
from unittest.mock import Mock, patch

# Using pytest-mock's mocker fixture
def test_send_email(mocker):
    # Patch the email sending
    mock_send = mocker.patch("myapp.email.send_email")
    
    # Act
    service = NotificationService()
    service.notify_user(user_id=1, message="Hello")
    
    # Assert the mock was called correctly
    mock_send.assert_called_once_with(
        to="user@example.com",
        subject="Notification",
        body="Hello"
    )

# Mocking with return values
def test_api_client(mocker):
    mock_response = Mock()
    mock_response.json.return_value = {"status": "success"}
    mock_response.status_code = 200
    
    mocker.patch("requests.get", return_value=mock_response)
    
    client = APIClient()
    result = client.get_data()
    
    assert result == {"status": "success"}

# Using autospec for safety
def test_with_autospec(mocker):
    # autospec ensures mock has same signature as real object
    mock_repo = mocker.Mock(spec=UserRepository)
    mock_repo.get_by_id.return_value = User(id=1, name="Test")
    
    service = UserService(mock_repo)
    user = service.get_user(1)
    
    mock_repo.get_by_id.assert_called_once_with(1)
```

### Test Organization

```
tests/
├── conftest.py           # Shared fixtures
├── unit/                 # Unit tests (fast, isolated)
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/          # Integration tests (slower, with DB)
│   ├── test_api.py
│   └── test_repositories.py
└── e2e/                  # End-to-end tests
    └── test_workflows.py
```

### Best Practices Checklist

- ✅ **One assertion concept per test** (not necessarily one assert statement)
- ✅ **Use descriptive test names**: `test_user_creation_with_invalid_email_raises_validation_error`
- ✅ **Keep tests independent** — no shared state between tests
- ✅ **Use fixtures for setup** — avoid duplicating setup code
- ✅ **Mock external dependencies** — database, APIs, file system
- ✅ **Test edge cases** — empty inputs, boundary values, errors
- ✅ **Use `pytest.raises` for exceptions**:

```python
def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_validation_error_message():
    with pytest.raises(ValidationError) as exc_info:
        User(email="invalid")
    assert "email" in str(exc_info.value)
```
