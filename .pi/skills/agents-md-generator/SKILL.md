---
name: agents-md-generator
description: Analyzes a Python (Django/FastAPI) codebase from a local path and generates a comprehensive AGENTS.md file for the pi coding agent CLI. Use this skill whenever the user wants to generate, create, or write an AGENTS.md for their project, or when they mention pi agent, pi coding agent, or want to set up project context for an AI agent. Also trigger when the user says things like "analyze my codebase", "create agent instructions", "set up pi for my project", or "generate project docs for AI".
---

# AGENTS.md Generator for Pi Coding Agent

Generates a well-structured `AGENTS.md` file for the [pi coding agent CLI](https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent) by thoroughly analyzing a Python project codebase.

## What is AGENTS.md?

Pi loads `AGENTS.md` at startup from `~/.pi/agent/`, parent directories, and the current project directory. It's a briefing document that gives the AI agent persistent, project-specific instructions so it can work effectively without being told the same things every session. Good `AGENTS.md` files are specific, actionable, and avoid vague generalities.

---

## Workflow

### Step 1 — Get the path

Ask the user for the absolute path to their project root if not already provided. Example:
> "What's the absolute path to your project? (e.g. `/home/user/myproject`)"

### Step 2 — Explore the project structure

Run the following bash commands to understand the codebase. Adapt based on what you find.

```bash
# Top-level overview
find <PATH> -maxdepth 3 -not -path '*/.*' -not -path '*/node_modules/*' \
  -not -path '*/__pycache__/*' -not -path '*/venv/*' -not -path '*/.venv/*' \
  -not -path '*/migrations/*' | sort

# Key config & dependency files
cat <PATH>/pyproject.toml 2>/dev/null || cat <PATH>/setup.py 2>/dev/null || cat <PATH>/requirements.txt 2>/dev/null
cat <PATH>/requirements*.txt 2>/dev/null
cat <PATH>/.env.example 2>/dev/null || cat <PATH>/.env.sample 2>/dev/null
cat <PATH>/docker-compose*.yml 2>/dev/null
cat <PATH>/Makefile 2>/dev/null
cat <PATH>/README.md 2>/dev/null

# Django-specific
cat <PATH>/manage.py 2>/dev/null
find <PATH> -name "settings*.py" | head -5 | xargs cat 2>/dev/null
find <PATH> -name "urls.py" | head -5 | xargs cat 2>/dev/null

# FastAPI-specific
find <PATH> -name "main.py" -o -name "app.py" | head -3 | xargs cat 2>/dev/null
find <PATH> -name "routers" -type d | head -3
find <PATH> -name "*.py" -path "*/api/*" | head -10

# Architecture / app structure
find <PATH> -name "models.py" -o -name "models" -type d | head -10
find <PATH> -name "services.py" -o -name "services" -type d | head -10
find <PATH> -name "repositories.py" -o -name "repositories" -type d | head -10
find <PATH> -name "schemas.py" -o -name "schemas" -type d | head -10

# Tests
find <PATH> -name "pytest.ini" -o -name "pyproject.toml" | xargs grep -l "pytest" 2>/dev/null | head -3 | xargs cat 2>/dev/null
find <PATH> -name "conftest.py" | head -3 | xargs cat 2>/dev/null
find <PATH> -name "test_*.py" | head -5 | xargs cat 2>/dev/null

# Linting / formatting config
cat <PATH>/.flake8 2>/dev/null
cat <PATH>/setup.cfg 2>/dev/null
grep -A5 "\[tool.ruff\]\|\\[tool.black\]\|\\[tool.isort\]" <PATH>/pyproject.toml 2>/dev/null

# Git config
cat <PATH>/.gitignore | head -30 2>/dev/null
git -C <PATH> log --oneline -10 2>/dev/null
git -C <PATH> branch 2>/dev/null

# CI/CD
find <PATH> -name "*.yml" -path "*/.github/workflows/*" | xargs cat 2>/dev/null
cat <PATH>/.gitlab-ci.yml 2>/dev/null
```

Read source files from core modules to understand patterns, naming conventions, and architecture. Focus on:
- Entry points (main.py, app.py, manage.py, wsgi.py, asgi.py)
- Core domain files (models, services, repositories)
- A few representative view/router files
- Base classes or mixins that are widely used

### Step 3 — Assess complexity and depth

Determine how comprehensive the AGENTS.md should be:

| Signal | Depth |
|--------|-------|
| Single-app, <20 files | **Concise** — key rules + commands only |
| Multi-module, 20–100 files | **Standard** — full sections, moderate detail |
| Monorepo / large app / DDD | **Comprehensive** — architecture map, domain rules, all workflows |

### Step 4 — Generate AGENTS.md

Write the file to `<PATH>/AGENTS.md`. Use the template below as a guide, but **adapt section depth based on complexity**. Skip sections that don't apply. Add sections that are specific to the project.

---

## AGENTS.md Template

````markdown
# AGENTS.md — <Project Name>

> Project instructions for the pi coding agent. Loaded automatically at startup.

## Project Overview

<1–3 sentences: what the project does, who uses it, what problem it solves>

**Framework:** Django X.X / FastAPI X.X  
**Python:** X.X  
**Database:** PostgreSQL / SQLite / etc.  
**Key integrations:** <Celery, Redis, S3, etc.>

---

## Repository Structure

```
<condensed tree of top-level dirs with one-line descriptions>
```

<For complex projects, explain each major module or app.>

---

## Architecture & Patterns

<Describe the architecture. Examples:>

- Clean Architecture: domain → application → infrastructure → api layers
- Django MTV with service layer between views and models
- DDD with aggregates in `domain/`, use cases in `application/`
- FastAPI with dependency injection via `Depends()`

**Key conventions:**
- <e.g. "Business logic lives in services/, never in views or serializers">
- <e.g. "All DB access goes through repositories, never query directly in services">
- <e.g. "Pydantic schemas in schemas/ for validation, separate from ORM models">

---

## How to Run

```bash
# Install dependencies
<command>

# Run development server
<command>

# Run with Docker
<command if applicable>
```

**Environment:** Copy `.env.example` to `.env` and fill in required values.

---

## How to Test

```bash
# Run all tests
<pytest command with flags>

# Run specific test file
<command>

# Run with coverage
<command>
```

<Note any test fixtures, factories, or conftest.py conventions>

---

## Code Style & Linting

```bash
# Format
<black/ruff format command>

# Lint
<ruff/flake8 command>

# Type check (if applicable)
<mypy command>
```

**Rules:**
- <e.g. "Max line length: 88 (Black default)">
- <e.g. "Use ruff for linting — run before every commit">
- <e.g. "Type hints required on all public functions">

---

## Git Workflow

- **Branch naming:** `<pattern, e.g. feature/short-description, fix/issue-id>`
- **Commit style:** `<e.g. conventional commits: feat:, fix:, refactor:>`
- **PRs:** `<any PR rules — squash, review required, etc.>`

**Critical git rules:**
- NEVER use `git add -A` or `git add .`
- Always `git add <specific files>` you modified
- Run lint + tests before committing

---

## Coding Conventions

### Naming
- <e.g. "Models: PascalCase nouns — `UserProfile`, not `user_profile_model`">
- <e.g. "Services: verb-noun — `CreateUserService`, `SendEmailService`">
- <e.g. "URL names: kebab-case — `user-profile`, not `user_profile`">

### Django-Specific (if applicable)
- <e.g. "Use `select_related`/`prefetch_related` — never cause N+1 queries">
- <e.g. "Migrations: always run `makemigrations` after model changes">
- <e.g. "Use Django signals sparingly — prefer explicit service calls">

### FastAPI-Specific (if applicable)
- <e.g. "All endpoints return Pydantic response models — never raw dicts">
- <e.g. "Use `Depends()` for auth, DB sessions, and shared logic">
- <e.g. "Async endpoints only — use `async def` everywhere">

---

## Critical Rules

> These are non-negotiable. Follow them on every task.

- <Rule 1 — e.g. "NEVER read a file without reading it completely before editing">
- <Rule 2 — e.g. "ALWAYS run tests after any logic change">
- <Rule 3 — e.g. "NEVER commit secrets or .env files">
- <Rule 4 — e.g. "ALWAYS check for existing abstractions before creating new ones">

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `<path>` | <what it does> |
| `<path>` | <what it does> |
| `<path>` | <what it does> |

---

## Known Gotchas

<Optional section — add project-specific traps, quirks, or things that often go wrong>

- <e.g. "Celery tasks in tasks.py must be registered in CELERY_TASK_ROUTES">
- <e.g. "The `User` model is extended via `UserProfile` — never use `User` directly for profile data">
````

---

## Writing Guidelines

- **Be specific.** "Use `ruff check .`" beats "run the linter."
- **Use exact commands.** Don't say "run tests" — give the full pytest command.
- **Keep critical rules short and imperative.** "NEVER use git add -A" not "It would be better to avoid..."
- **Skip sections that don't apply.** An empty section is worse than no section.
- **Don't pad.** Pi reads this every session — waste no tokens on obvious things.
- **Add project-specific gotchas.** The most valuable content is what isn't obvious.

---

## Final Step

After writing the file, report to the user:
1. The path where `AGENTS.md` was saved
2. A brief summary of what was detected (framework, architecture, depth chosen)
3. Any sections where you had to make assumptions (so they can review and adjust)