# AGENTS.md - AI Coding Agent Guide

This document provides essential information for AI coding agents working on this project.

## Project Overview

**Single Address Notifier** (also known as `signer-service`) is a Django-based blockchain transaction processing service for EVM-compatible chains. It monitors blockchain addresses, processes deposits/withdrawals, manages token balances, and handles fund sweeping operations between hot and cold wallets.

The service integrates with:
- An exchange platform (via REST API)
- A private key manager service for transaction signing
- PostgreSQL for data persistence
- Redis for Celery task queuing

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | Django 4.2 |
| API Framework | Django REST Framework |
| Task Queue | Celery 5.3.4 + django-celery-beat |
| Message Broker | Redis |
| Database | PostgreSQL |
| Blockchain | Web3.py 5.31.3 |
| Python Version | 3.12.4 |
| WSGI Server | Gunicorn |
| Testing | pytest + pytest-django |
| Linting/Formatting | Ruff |

## Architecture Overview

### Core Modules

The project follows Django's app-based architecture with 6 main modules:

```
scanner_core/         # Django project configuration
├── settings/         # Environment-specific settings
├── celery.py         # Celery configuration and periodic tasks
├── urls.py           # URL routing
├── wsgi.py           # WSGI entry point

balance_management/   # Deposit/withdrawal processing
├── models.py         # Transaction models (Deposit, Withdraw, Address)
├── tasks.py          # Celery tasks for withdrawals
├── views.py          # API endpoints
└── db.py             # Database operations

exchange_notifier/    # Exchange integration
├── tasks.py          # Notification and confirmation tasks
├── business.py       # Core business logic
└── models.py         # DynamicOptions model

sweeps/               # Fund sweeping operations
├── models.py         # SweepTransaction, GasTransaction models
├── tasks.py          # Sweep periodic tasks
├── business.py       # Sweep logic
└── enums.py          # Transaction status enums

token_management/     # ERC-20 token handling
├── models.py         # Token model with contract info
└── tasks.py          # Token balance update tasks

app_events/           # Application event logging
├── models.py         # Event storage
└── tasks.py          # Event processing tasks

common/               # Shared utilities
├── utils.py          # Helper functions
├── validators.py     # Input validation
├── decorators.py     # Custom decorators
├── logger.py         # Application logging
└── crypto/           # Encryption/decryption middleware
```

### Data Flow

1. **Deposits**: External scanner → Redis → exchange_notifier detects → balance_management stores → notifies exchange
2. **Withdrawals**: Exchange API → balance_management creates tx → private key manager signs → blockchain
3. **Sweeps**: Periodic Celery tasks scan balances → sweep to hot/cold wallets based on thresholds

## Configuration

### Environment Variables

Key required environment variables (see `env/env_example`):

```bash
# Blockchain
ETH_NODE_CREDENTIALS=    # RPC endpoint
CHAIN_ID=               # Network chain ID
TICKER=                 # Currency symbol (ETH, BNB, etc.)
DECIMALS=               # Token decimals
CONFIRMATIONS=          # Block confirmations required

# Wallets
MASTER_ADDRESS=         # Master wallet address
COLD_ADDRESS=           # Cold storage address
DEEP_COLD_WALLETS=      # Additional cold wallets

# External Services
PRIVATE_KEY_MANAGER_URL=  # Signing service URL
EXCHANGE_URL=             # Exchange API URL
EXCHANGE_REQUEST_TOKEN=   # API authentication token

# Database
DB_HOST=, DB_NAME=, DB_USER=, DB_PASSWORD=, DB_PORT=

# Redis
REDIS_HOST=, REDIS_PORT=

# Security
SECRET_KEY=             # Django secret key
OTP_TOKEN=              # 2FA token for sensitive operations

# Gas Settings
MAX_GASPRICE=, MIN_GASPRICE=, GAS_LIMIT=
ETH_GAS_PRICE_PERCENT=  # Gas price multiplier
```

### Settings Structure

- `scanner_core/settings/base.py` - Common settings, loads from environment
- `scanner_core/settings/dev.py` - Local development
- `scanner_core/settings/production.py` - Production environment
- `scanner_core/settings/test.py` - Unit tests (SQLite, no migrations)
- `scanner_core/settings/test_integration.py` - Integration tests (PostgreSQL)

## Build and Test Commands

### Setup

```bash
# Install dependencies
make install

# Run migrations
make migrate
```

### Running the Application

```bash
# Production mode
make run           # Starts gunicorn server

# Celery worker
make celery        # Starts Celery worker with beat scheduler

# Local development
make local_run     # Starts with debug configuration
make local_celery  # Starts Celery in debug mode
```

### Testing

```bash
# Run all unit tests
make test

# Run with coverage
make test-cov

# Run specific module tests
make test-sweeps
make test-balance
make test-common
make test-exchange
make test-tokens
make test-scanner

# Run tests matching keyword
make test-k K=test_name_pattern

# Run single test file
make test-file F=tests/unit/sweeps/test_models.py

# Docker-based testing
make test-unit-docker       # Unit tests in container
make test-integration-docker # Integration tests with real services
```

### Docker Operations

```bash
# Production build/push
make prod_build
make prod_push
make prod_release  # Tags git release

# Development
make dev_build
make dev_push
```

## Code Style Guidelines

### Linting with Ruff

The project uses Ruff with extensive rule configuration in `pyproject.toml`:

```bash
# Run linter
ruff check .

# Run formatter
ruff format .

# Auto-fix issues
ruff check . --fix
```

### Key Style Rules

- **Line length**: 120 characters
- **Quotes**: Double quotes for strings
- **Indentation**: 4 spaces
- **Import style**: Sorted with `isort` rules via Ruff

### Ignored Rules (Intentional)

- `D10x` - Missing docstrings (modules, classes, functions)
- `COM812` - Trailing comma requirements
- `ANN002/003` - `*args`/`**kwargs` annotations not required
- `G004` - f-strings in logging allowed
- `PLR0913` - Multiple function arguments allowed

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Testing Instructions

### Test Organization

```
tests/
├── unit/              # Fast tests, no external dependencies
│   ├── conftest.py    # Shared fixtures
│   ├── test_*.py      # Test modules mirroring src structure
├── integration/       # Tests requiring DB, Redis, external APIs
│   ├── fixtures.py    # Integration test fixtures
│   └── test_*.py      # Integration tests
```

### Writing Tests

```python
# Use pytest markers
@pytest.mark.unit           # Fast, isolated tests (default)
@pytest.mark.integration    # Requires external services
@pytest.mark.slow          # Long-running tests

# Mock external services - NEVER make real network calls in unit tests
from unittest.mock import MagicMock, patch

# Use fixtures from conftest.py
@pytest.fixture
def mock_token():
    token = MagicMock(spec=Token)
    token.symbol = "TEST"
    return token
```

### Critical Testing Rules

1. **Never make real network calls in unit tests** - Always mock Web3 clients, HTTP requests
2. **Database**: Unit tests use SQLite in-memory; integration tests use PostgreSQL
3. **Migrations**: Disabled in unit tests for speed (`MIGRATION_MODULES = DisableMigrations()`)
4. **Rate limiting**: Disabled in tests (`WEB3_RATE_LIMIT_ENABLED = False`)

### Coverage Requirements

```bash
# Generate HTML coverage report
make test-cov-html
# Opens at htmlcov/index.html
```

## Security Considerations

### Critical Security Points

1. **Private Keys**: NEVER stored in this service. All signing goes to `PRIVATE_KEY_MANAGER_URL`
2. **API Authentication**: 
   - `EXCHANGE_REQUEST_TOKEN` for exchange API
   - `OTP_TOKEN` for sensitive operations
3. **Encryption**: `DecryptAllPayloadMiddleware` decrypts incoming requests
4. **Cold Wallets**: Multiple cold wallet types supported (DEFAULT, BINANCE, DEEP_COLD)

### Environment Security

- Never commit `.env` files
- Use strong `SECRET_KEY` in production
- Restrict access to private key manager service

### Transaction Security

- Gas price limits (`MIN_GASPRICE`, `MAX_GASPRICE`)
- Rate limiting on Web3 requests to prevent credit exhaustion
- Transaction confirmation requirements (`CONFIRMATIONS`)

## Deployment Process

### GitLab CI/CD Pipeline

```yaml
Stages: test → build → deploy → release

1. build-web-image    # Docker image build
2. deploy-web-to-ecr  # Push to AWS ECR
3. release-web-and-celery-on-vps  # SSH deployment
```

### Manual Deployment

```bash
# Update version
export IMAGE_VERSION=x.x.x

# Build and push
make prod_build
make prod_push

# Tag release
make prod_release
```

### Docker Compose Services

- `db` - PostgreSQL 15.3
- `redis` - Redis for Celery
- `web` - Django application (gunicorn)
- `celery` - Celery worker + beat scheduler

## Key Business Logic

### Sweep Operations

Sweeps move funds from user addresses to hot/cold wallets:

1. **Sweep to Hot**: Periodic task moves funds from deposit addresses to hot wallet
2. **Sweep to Cold**: Moves excess funds from hot to cold storage
3. **Token Sweeps**: ERC-20 token transfers with allowance handling

### Transaction Status Flow (GasTransaction)

- `Created (0)` → `Success (1)` or `Pending (2)`
- On error: `ReceiptNotFound (3)`, `InvalidReceiptStatus (4)`, `UnhandledError (5)`

### Confirmation Logic

Deposits require `CONFIRMATIONS` blocks before being marked confirmed and notified to exchange.

## Common Tasks

### Adding a New Celery Task

1. Define task in `<app>/tasks.py`
2. Add to `scanner_core/celery.py` beat_schedule:
```python
app.conf.beat_schedule = {
    "task_name": {
        "task": "app_name.tasks.task_function",
        "schedule": 30,  # seconds or crontab()
    },
}
```

### Adding a New Model

1. Define model in `<app>/models.py`
2. Create migration: `python manage.py makemigrations`
3. Apply: `python manage.py migrate`
4. Add to admin if needed: `<app>/admin.py`

### Adding API Endpoints

1. Define views in `<app>/views.py` or `<app>/api_handlers.py`
2. Add URL patterns in `<app>/urls.py`
3. Include in `scanner_core/urls.py`

## Troubleshooting

### Common Issues

1. **Celery not processing tasks**: Check Redis connection, verify task routing
2. **Database locked**: PostgreSQL connection limits, check `max_connections`
3. **Web3 rate limiting**: Check `WEB3_RATE_LIMIT_ENABLED` and adjust thresholds
4. **Migration errors**: Ensure `django_celery_beat` migrations applied

### Logs

```bash
# Django logs
python manage.py runserver  # Debug mode

# Celery logs
celery -A scanner_core worker -l debug

# Gunicorn logs
gunicorn -c gunicorn.conf.py --log-level debug
```

## Important Notes

1. **Language**: Codebase primarily uses English for code/comments. Documentation may include Russian.
2. **No Alembic**: Uses Django migrations, not Alembic (excluded from Ruff checks).
3. **Rate Limiting**: Web3 requests are rate-limited by default to prevent API credit exhaustion.
4. **Decimal Precision**: Always use `Decimal` for monetary calculations (max_digits=100, decimal_places=18).
5. **Address Checksumming**: All addresses are converted to checksum format via Web3.py.
