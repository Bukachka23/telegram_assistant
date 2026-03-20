# Task Decomposition Template

Use this template to draft `tasks.md`. Tasks are the executable units of the plan — small enough to review in one pass, ordered by dependency, and each producing a testable result.

---

## Template

```markdown
# Tasks

## Overview

[One-line summary of what these tasks deliver, referencing the spec.]

Total tasks: [N]
Estimated effort: [rough estimate if applicable]

## Task List

### T1: [Short descriptive title]
- **Delivers**: [What artifact, behavior, or state this task produces]
- **Depends on**: [T0 / nothing / "clean environment"]
- **Spec mapping**: [Which goals (G1, G2) and scenarios (S1, S2) this covers]
- **Acceptance**:
  - [ ] [Testable criterion 1]
  - [ ] [Testable criterion 2]
- **Notes**: [Any implementation hints, gotchas, or constraints]

### T2: [Short descriptive title]
- **Delivers**: [...]
- **Depends on**: T1
- **Spec mapping**: [...]
- **Acceptance**:
  - [ ] [...]
- **Notes**: [...]

### T3–TN: [...]

## Dependency Graph

[Visual or textual representation of task dependencies]

T1 → T2 → T3
            ↘
       T4 → T5 → T6
            ↗
       T3 →

## Parallel Opportunities

[Tasks that can run in parallel if resources allow]

- T3 and T4 are independent after T2
- T6 depends on both T3 and T5
```

---

## Task Sizing Rules

### The Right Size

A well-sized task:
- Produces ONE reviewable artifact or behavior change
- Can be described in 1-3 sentences
- Has 1-3 clear acceptance criteria
- Doesn't require "and then also..." in its description
- Can be verified independently

### Too Big — Split It

Signs a task is too big:
- Description has multiple paragraphs
- Uses "and" to connect unrelated actions
- Has 5+ acceptance criteria
- Would require reviewing multiple files or systems
- Takes multiple tool-use sessions to complete

**How to split:** Find the "and" — each clause becomes its own task.

```
# TOO BIG:
T3: Build catalog API and product search and filtering

# SPLIT:
T3: Catalog API — list products and categories
T4: Product search by name
T5: Category-based filtering and price sorting
```

### Too Small — Merge It

Signs a task is too small:
- It's a single line change
- It has no meaningful acceptance criteria
- It's just a setup step for another task
- It can't be verified independently

**How to merge:** Combine with the adjacent task it supports.

```
# TOO SMALL:
T2: Create empty models file
T3: Add Product model
T4: Add Category model

# MERGED:
T2: Database models (Product, Category) + Alembic migration
```

---

## Task Ordering Patterns

### Standard Pattern (most projects)

```
T1: Scaffolding / Setup        ← Foundation: project init, config, healthcheck
T2: Core Data / Structure      ← Models, schemas, base classes
T3–Tn-2: Feature tasks         ← Business logic, one per feature area
Tn-1: Integration / Wiring     ← Connect components, end-to-end flow
Tn: Polish / Documentation     ← README, cleanup, final quality checks
```

### Fix Pattern

```
T1: Reproduce the bug           ← Write a failing test or reproduction script
T2: Identify root cause          ← Trace the issue, document findings
T3: Implement the fix            ← Minimal change to fix the root cause
T4: Regression test              ← Test that prevents recurrence
T5: Verify no side effects       ← Run full test suite, check related areas
```

### Refactor Pattern

```
T1: Establish safety net         ← Ensure test coverage of current behavior
T2–Tn-1: Incremental transforms ← One refactoring step each, tests pass after each
Tn: Verify and document          ← Final quality check, update docs
```

### Review Pattern

```
T1: Setup review framework       ← Define criteria, create checklist, gather tools
T2–Tn-1: Section reviews         ← One section/module/area per task
Tn: Synthesize and report        ← Compile findings, prioritize, write report
```

### Migration Pattern

```
T1: Analyze source               ← Map current structure and data
T2: Set up target                 ← Prepare destination environment
T3: Build migration scripts       ← Transformation logic
T4: Dry run                       ← Migrate to staging, validate
T5: Execute migration             ← Run against production/target
T6: Verify and rollback test      ← Confirm integrity, test rollback
```

### Integration Pattern

```
T1: API contract definition       ← Define interfaces between systems
T2: Auth / connection setup       ← Establish secure connection
T3: Data mapping                  ← Map fields between systems
T4: Happy path implementation     ← Core integration flow
T5: Error handling                ← Retry, fallback, alerting
T6: End-to-end test               ← Full flow validation
```

### Automation Pattern

```
T1: Manual process documentation  ← Document current workflow step by step
T2: Pipeline scaffolding          ← Set up automation tool/framework
T3–Tn-2: Step automation          ← Automate one manual step per task
Tn-1: Error handling and recovery ← Handle failures, retries, alerts
Tn: End-to-end validation         ← Run full pipeline, compare with manual result
```

---

## Guidance by Task Type

### Create
- Start with scaffolding (project init, config, healthcheck)
- Data layer before business logic
- Business logic before presentation
- Tests alongside implementation (not as a separate final task)

### Add
- First task: understand integration points in existing code
- Add database migrations early if needed
- Ensure backwards compatibility at every step
- Run existing tests after every task

### Fix
- First task is ALWAYS reproduction (failing test or script)
- Keep the fix minimal — don't refactor while fixing
- Regression test is a separate task, not part of the fix

### Refactor
- First task is ALWAYS establishing test coverage (safety net)
- Each task is one transformation, tests pass after each
- Never combine "refactor" and "add feature" in one task

### Review
- One task per review area/module (don't review everything at once)
- Final task synthesizes findings into actionable report
- Keep findings factual — separate observations from recommendations

---

## Task Quality Checklist

Before presenting tasks to the user:

```
□ First task is scaffolding/setup/reproduction (depending on type)
□ Last task is documentation/cleanup/report
□ Each task has 1-3 acceptance criteria
□ Each task maps to spec goals/scenarios
□ Dependencies are explicit and form a valid DAG
□ No task has "and" connecting unrelated actions
□ Parallel opportunities are identified
□ Total task count feels right (3-8 for small projects, 6-15 for medium)
□ No implementation details in task descriptions (that's for the implementation phase)
```