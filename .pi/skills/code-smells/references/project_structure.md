The recommended project structure follows the src layout pattern:

```commandline
my-project/
├── pyproject.toml          # Project configuration (REQUIRED)
├── README.md               # Project documentation
├── LICENSE
├── .gitignore
├── src/
│   └── my_project/         # Package directory (underscore, not dash)
│       ├── __init__.py
│       ├── main.py         # Entry point
│       ├── config.py       # Configuration
│       ├── domain/         # Business logic (entities, value objects)
│       │   ├── __init__.py
│       │   ├── models.py
│       │   └── exceptions.py
│       ├── application/    # Use cases, services
│       │   ├── __init__.py
│       │   └── services.py
│       ├── infrastructure/ # External systems (DB, APIs)
│       │   ├── __init__.py
│       │   ├── repositories.py
│       │   └── adapters.py
│       └── interfaces/     # Controllers, CLI, API routes
│           ├── __init__.py
│           └── api.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Shared fixtures
│   ├── unit/
│   │   └── test_services.py
│   └── integration/
│       └── test_api.py
└── docs/
    └── architecture.md
```