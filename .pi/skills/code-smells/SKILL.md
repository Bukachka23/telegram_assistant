---
name: code-smells
description: Review and refactor Python code by detecting code smells and applying best practices. Use when user mentions "code smell", "refactor", "review code", "clean code", "improve code quality", or when analyzing Python files for quality improvements. Always reviews code with suggestions before making changes.
---

# Code Smells Detection and Refactoring

## Overview

This skill systematically reviews Python code to identify code smells and provides actionable refactoring suggestions based on comprehensive reference materials. It follows a **review-first approach** - always analyzing and presenting suggestions before making any code changes.

## When to Use This Skill

Use this skill when:
- User asks to "review", "refactor", or "improve" Python code
- Detecting code smells, anti-patterns, or quality issues
- Applying clean code principles to existing codebase
- Modernizing legacy Python code
- User mentions: "code smell", "clean up", "code quality", "best practices"

## Reference Materials

This skill uses the following reference documents located in `references/`:

| Document | Purpose |
|----------|---------|
| `tips_for_refactoring.md` | Practical refactoring patterns and anti-patterns |
| `clean_arhitecture.md` | SOLID principles and layered architecture |
| `functions_and_methods.md` | Function design: size, guard clauses, returns |
| `design_patterns.md` | When and how to apply design patterns |
| `data_modeling.md` | Dataclasses, Pydantic, domain modeling |
| `type_hints_protocols.md` | Type annotations and Protocol usage |
| `when_to_use_classes.md` | Classes vs functions decision guide |
| `module_organization.md` | Package structure and imports |
| `project_structure.md` | Project layout best practices |
| `modern_standard.md` | Modern Python idioms (3.10+) |
| `test_best_practices.md` | Testing patterns and coverage |

## Workflow

### Phase 1: Discovery

1. **Identify target files**
   ```bash
   # List Python files in scope
   find <path> -name "*.py" -type f
   ```

2. **Load reference materials** (load as needed based on detected issues)
   ```
   Read: .claude/skills/code-smells/references/<relevant_doc>.md
   ```

### Phase 2: Code Review (ALWAYS DO THIS FIRST)

For each file, analyze and document:

#### 2.1 Code Smells Checklist

```markdown
## Review: <filename>

### Detected Issues

#### Modularity & Structure
- [ ] God classes (classes doing too many things)
- [ ] Long functions (>25 lines)
- [ ] Deep nesting (>3 levels)
- [ ] Multiple responsibilities in single function

#### Data & Types
- [ ] Passing raw dicts instead of dataclasses/models
- [ ] Missing type hints
- [ ] Magic numbers/strings
- [ ] Arrays used as records

#### Control Flow
- [ ] Deep nesting instead of guard clauses
- [ ] Catch-all exceptions
- [ ] Exceptions for normal control flow

#### Duplication & Reuse
- [ ] Repeated code blocks
- [ ] Custom utilities replacing built-ins
- [ ] Copy-paste patterns

#### Naming & Documentation
- [ ] Unclear variable/function names
- [ ] Missing docstrings on public APIs
- [ ] Wildcard imports

#### OOP Issues
- [ ] Feature envy (method uses another class's data)
- [ ] Inappropriate inheritance
- [ ] Static-only utility classes
```

#### 2.2 Generate Suggestions Report

For each detected issue, provide:

```markdown
### Issue: <Issue Name>

**Location**: `file.py:line_number`

**Current Code**:
```python
# problematic code snippet
```

**Problem**: Why this is a code smell

**Suggested Refactoring**:
```python
# improved code snippet
```

**Reference**: See `references/<relevant_doc>.md` - Section: <section_name>
```

### Phase 3: User Confirmation

**IMPORTANT**: Always present the review findings and ask for confirmation before proceeding:

```markdown
## Summary

I've reviewed `<files>` and found:
- X modularity issues
- Y data modeling improvements
- Z control flow optimizations

### Recommended Priority:
1. [High] <most critical issue>
2. [Medium] <next issue>
3. [Low] <minor improvement>

Would you like me to:
1. Proceed with all suggested refactorings
2. Apply specific refactorings (specify which)
3. Explain any suggestion in more detail
4. Skip refactoring for now
```

### Phase 4: Refactoring (Only After Approval)

Apply approved changes following these principles:

#### 4.1 Refactoring Order

1. **Extract/rename** - Improve naming and extract functions first
2. **Data modeling** - Replace dicts with dataclasses/models
3. **Type hints** - Add missing type annotations
4. **Control flow** - Flatten nesting, add guard clauses
5. **Remove duplication** - DRY up repeated code
6. **Organize** - Move methods, extract classes if needed

#### 4.2 Preserve Behavior

```
□ Run tests before refactoring
□ Make incremental changes
□ Run tests after each change
□ Same inputs produce same outputs
□ Same exceptions raised for same conditions
```

## Quick Reference: Common Code Smells

### Smell → Fix Mapping

| Code Smell | Reference Doc | Quick Fix |
|------------|---------------|-----------|
| Long function | `functions_and_methods.md` | Extract helper functions |
| Dict as data | `data_modeling.md` | Use dataclass or Pydantic |
| Deep nesting | `functions_and_methods.md` | Guard clauses |
| God class | `when_to_use_classes.md` | Extract class per responsibility |
| Magic numbers | `tips_for_refactoring.md` | Named constants |
| Missing types | `type_hints_protocols.md` | Add annotations |
| Repeated code | `tips_for_refactoring.md` | Extract common function |
| Wildcard import | `module_organization.md` | Explicit imports |
| Catch-all except | `tips_for_refactoring.md` | Specific exceptions |

## Example Review Output

```markdown
## Code Review: user_service.py

### 1. God Class Detected [HIGH]

**Location**: `user_service.py:15-150`

**Current**: `UserService` handles user CRUD, email sending, PDF generation, and analytics.

**Problem**: Violates Single Responsibility Principle. Changes to email logic require modifying user service.

**Suggestion**: Extract `EmailService`, `ReportService`, `AnalyticsService`

**Reference**: `clean_arhitecture.md` - Single Responsibility Principle

---

### 2. Dict Instead of Model [MEDIUM]

**Location**: `user_service.py:45`

**Current**:
```python
def create_user(self, user_dict: dict) -> dict:
    if user_dict["email"]:
        ...
```

**Problem**: No validation, no IDE support, easy to make key typos.

**Suggestion**:
```python
@dataclass
class UserData:
    email: str
    name: str

def create_user(self, data: UserData) -> User:
    ...
```

**Reference**: `data_modeling.md` - Dataclasses for Domain Models

---

### Summary

| Priority | Count | Category |
|----------|-------|----------|
| High | 1 | Architecture |
| Medium | 3 | Data Modeling |
| Low | 5 | Type Hints |

Proceed with refactoring? [Y/n/select specific]
```

## Output

After completing the review:
1. Present findings in structured markdown format
2. Wait for user approval before making changes
3. Apply changes incrementally with verification
4. Summarize what was changed
