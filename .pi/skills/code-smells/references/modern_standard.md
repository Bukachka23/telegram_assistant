Modern Standard

pyproject.toml
```commandline
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-project"
version = "0.1.0"
description = "A well-structured Python project"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
authors = [
    {name = "Your Name", email = "your@email.com"}
]
dependencies = [
    "pydantic>=2.0",
    "httpx>=0.24",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "ruff>=0.1",
    "mypy>=1.0",
]

[project.scripts]
my-project = "my_project.main:main"

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "UP", "B"]

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --cov=src"
```

Package Management Tools
Tool       Use Case        Key Feature
Poetry     Most projects   Lock files, dependency resolution
uv         Fast installs   Rust-based, extremely fast
pip-tools  Simple projects Requirements compilation
PDM        PEP compliance  Standards-focused