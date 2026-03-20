---
name: unit-test-writer
description: Generate comprehensive unit tests for new code. Use when user creates functions/classes/modules, asks for tests, mentions "test", "coverage", "TDD", "pytest", "unittest", "spec", or implements features needing verification. Also triggers after refactoring or adding new methods.
---

# Unit Test Writer

Generate maintainable unit tests following project conventions.

## Workflow

### Step 0: Detect Project Conventions (ALWAYS FIRST)

Before writing ANY test:

```bash
# Check for existing tests - MATCH THEIR STYLE
ls tests/ test/ *_test.py test_*.py **/*.spec.ts **/*.test.ts 2>/dev/null

# Check framework config
cat pyproject.toml pytest.ini setup.cfg package.json 2>/dev/null | head -50
```

If existing tests found → **match their patterns exactly** (imports, fixtures, naming, structure).

### Step 1: Analyze Implementation

1. Read the source file completely
2. Identify: inputs, outputs, exceptions, dependencies
3. List test scenarios:
   - ✅ Happy path (valid inputs → expected output)
   - ⚠️ Edge cases (empty, None, boundaries, zero, max)
   - ❌ Error cases (invalid types, missing required, exceptions)
   - 🔗 Dependencies (mock external calls)

### Step 2: Detect Framework

| File/Config | Framework |
|-------------|-----------|
| `pytest.ini`, `[tool.pytest]` in pyproject.toml | pytest |
| `unittest` imports in existing tests | unittest |
| `jest.config.*`, `"jest"` in package.json | Jest |
| `vitest.config.*` | Vitest |
| `*.spec.ts` files | Usually Jest/Vitest |

### Step 3: Generate Tests

Use **AAA pattern** (Arrange-Act-Assert):

```python
def test_validate_email_returns_normalized_for_valid_input():
    # Arrange
    raw_email = "  User@Example.COM  "
    
    # Act
    result = validate_email(raw_email)
    
    # Assert
    assert result == "user@example.com"
```

For complex scenarios, see `references/testing-patterns.md`.

## Test Structure Template

```python
"""Tests for {module_name}."""
import pytest
from unittest.mock import Mock, patch

from {module_path} import {TargetClass}


class Test{TargetClass}:
    """Tests for {TargetClass}."""

    @pytest.fixture
    def instance(self):
        """Create test instance."""
        return {TargetClass}()

    # === Happy Path ===
    def test_{method}_returns_expected_for_valid_input(self, instance):
        result = instance.{method}("valid")
        assert result == "expected"

    # === Edge Cases ===
    def test_{method}_handles_empty_input(self, instance):
        result = instance.{method}("")
        assert result is None

    @pytest.mark.parametrize("input,expected", [
        (None, None),
        ("", None),
        ("   ", None),
    ])
    def test_{method}_handles_falsy_values(self, instance, input, expected):
        assert instance.{method}(input) == expected

    # === Error Cases ===
    def test_{method}_raises_type_error_for_invalid_type(self, instance):
        with pytest.raises(TypeError):
            instance.{method}(123)

    # === Mocked Dependencies ===
    @patch("{module}.external_api")
    def test_{method}_calls_api_correctly(self, mock_api, instance):
        mock_api.return_value = {"status": "ok"}
        instance.{method}_with_api()
        mock_api.assert_called_once()
```

## Naming Convention

`test_{method}_{scenario}_{expected_outcome}`

```python
# ✅ Good - descriptive
test_calculate_total_returns_zero_when_cart_empty
test_validate_password_raises_error_for_short_input
test_send_email_retries_on_timeout

# ❌ Bad - vague
test_calculate
test_validation
test_1
```

## Mocking Rules

| Mock | Don't Mock |
|------|------------|
| External APIs | Pure functions |
| Database calls | Simple transformations |
| File I/O | The code under test |
| Time/random | Value objects |
| Third-party services | Internal helpers (usually) |

## After Writing

```bash
# Run tests
pytest tests/test_{module}.py -v

# Check coverage
pytest --cov={src_module} --cov-report=term-missing
```

## Quick Reference

For detailed patterns (Given-When-Then, Four-Phase, FIRST principles) → read `references/testing-patterns.md`