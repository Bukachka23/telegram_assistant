# Testing Patterns Reference

## Core Patterns

### AAA (Arrange-Act-Assert) — DEFAULT PATTERN

```python
def test_get_customer_name():
    # Arrange - setup inputs and expected
    customer_id = 123
    database = {123: "John Smith"}
    
    # Act - call the function
    result = get_customer_name(customer_id, database)
    
    # Assert - verify result
    assert result == "John Smith"
```

### Given-When-Then (BDD Style)

Use for behavior-focused tests or when documenting user stories:

```python
def test_customer_receives_discount_on_birthday():
    # Given a customer with a birthday today
    customer = Customer(birthday=date.today())
    order = Order(total=100.0)
    
    # When they place an order
    result = apply_discounts(order, customer)
    
    # Then they receive 10% birthday discount
    assert result.total == 90.0
    assert result.discounts == ["birthday_10%"]
```

### Four-Phase Test (with cleanup)

Use when test requires resource cleanup:

```python
def test_file_processing():
    # Setup
    temp_file = Path("/tmp/test.txt")
    temp_file.write_text("test data")
    processor = FileProcessor()
    
    # Exercise
    result = processor.process(temp_file)
    
    # Verify
    assert result.lines == 1
    assert result.words == 2
    
    # Teardown
    temp_file.unlink()
```

With pytest fixtures (preferred):

```python
@pytest.fixture
def temp_file(tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("test data")
    yield file
    # Cleanup automatic with tmp_path

def test_file_processing(temp_file):
    result = FileProcessor().process(temp_file)
    assert result.lines == 1
```

## F.I.R.S.T. Principles

Every test should be:

| Principle | Meaning | How to Achieve |
|-----------|---------|----------------|
| **Fast** | Runs in milliseconds | Mock I/O, avoid sleep() |
| **Independent** | No test order dependency | Fresh fixtures, no shared state |
| **Repeatable** | Same result every run | No randomness, mock time/dates |
| **Self-validating** | Clear pass/fail | Meaningful assertions |
| **Timely** | Written with the code | TDD or immediately after |

## Test Isolation Patterns

### One Concept Per Test

```python
# ✅ Good - isolated concepts
def test_validates_email_format():
    assert validate_email("bad") is False

def test_validates_email_domain():
    assert validate_email("user@") is False

def test_accepts_valid_email():
    assert validate_email("user@example.com") is True

# ❌ Bad - multiple concepts
def test_email_validation():
    assert validate_email("bad") is False
    assert validate_email("user@") is False
    assert validate_email("user@example.com") is True
```

### Parameterized for Similar Cases

```python
# ✅ Good - grouped similar inputs
@pytest.mark.parametrize("invalid_email", [
    "",
    "no-at-sign",
    "@no-username.com",
    "no-domain@",
    "spaces in@email.com",
])
def test_rejects_invalid_emails(invalid_email):
    with pytest.raises(ValueError):
        validate_email(invalid_email)
```

## Async Testing

```python
@pytest.mark.asyncio
async def test_async_fetch():
    # Arrange
    client = AsyncClient()
    
    # Act
    result = await client.fetch("/api/data")
    
    # Assert
    assert result.status == 200
```

## Exception Testing

```python
# Basic
def test_raises_on_invalid():
    with pytest.raises(ValueError):
        validate("")

# With message check
def test_raises_with_message():
    with pytest.raises(ValueError, match="cannot be empty"):
        validate("")

# Capture exception for inspection
def test_exception_details():
    with pytest.raises(ValidationError) as exc_info:
        validate(bad_data)
    assert exc_info.value.field == "email"
    assert "required" in str(exc_info.value)
```

## Mocking Patterns

```python
# Dependency injection (preferred)
def test_service_with_mock_repo():
    mock_repo = Mock(spec=UserRepository)
    mock_repo.find.return_value = User(id=1, name="Test")
    
    service = UserService(repository=mock_repo)
    result = service.get_user(1)
    
    assert result.name == "Test"
    mock_repo.find.assert_called_once_with(1)

# Patch decorator (when DI not available)
@patch("myapp.services.external_api")
def test_calls_external_api(mock_api):
    mock_api.post.return_value = {"id": 123}
    
    result = create_order(order_data)
    
    assert result.external_id == 123
    mock_api.post.assert_called_once()

# Context manager (for specific scope)
def test_time_dependent():
    with patch("myapp.utils.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2024, 1, 1, 12, 0)
        result = get_greeting()
    assert result == "Good afternoon"
```