---
name: spec-development-driven
description: >
  Use Spec Development Driven (SDD) methodology for any task that benefits from structured planning
  before implementation. Triggers include: requests to "build", "create", "add", "fix", "refactor",
  "review", "migrate", "integrate", or "automate" anything non-trivial. Also use when the user says
  "plan this out", "let's do this properly", "SDD", "spec-driven", or when a task has multiple moving
  parts, unclear requirements, or risk of scope creep. Do NOT use for one-liner fixes, simple lookups,
  quick questions, or tasks the user explicitly wants done immediately without planning.
---

# Spec Development Driven (SDD)

A universal methodology for turning ideas into predictable, reviewable, high-quality results.
SDD ensures that every non-trivial task follows the pipeline:

```
idea → specification → implementation plan → task decomposition → implementation → verification
```

## Core Principle

**Never start implementing before the spec is approved.** The spec is the contract. The plan is the architecture. The tasks are the execution units. Implementation is just filling in the blanks.

---

## When to Use SDD

| Signal | Action |
|--------|--------|
| Task has 2+ components or steps | Use SDD |
| Requirements are ambiguous or incomplete | Use SDD (spec forces clarity) |
| Task involves data models, APIs, or integrations | Use SDD |
| User says "build", "create", "add feature", "migrate" | Use SDD |
| Risk of scope creep is high | Use SDD (non-goals are critical) |
| Simple bug fix with clear cause | Skip SDD, just fix it |
| One-liner change, formatting, typo | Skip SDD |
| User says "just do it" or "quick fix" | Skip SDD unless it's clearly complex |

## When NOT to Use SDD

- Answering questions or explaining concepts
- Single-file edits with obvious scope
- Tasks the user explicitly wants done fast without ceremony
- Exploratory/prototyping work (unless user asks for structure)

---

## The SDD Pipeline

### Phase 0: Intake — Understand the Idea

Before writing anything, clarify:

1. **What** does the user want? (the deliverable)
2. **Why** do they want it? (the goal behind the request)
3. **What's out of scope?** (the negative prompt — this prevents generation of unnecessary work)
4. **What are the constraints?** (tech stack, timeline, existing code, conventions)

If the user's request is vague, ask targeted questions. Do not assume. A 30-second clarification saves hours of rework.

### Phase 1: Specification — `specification.md`

The spec is the **single source of truth** for what will be built. It must be formal enough to serve as an acceptance document and short enough to maintain.

Read `references/specification-template.md` for the full template.

**Key sections:**
- **Context**: Why this exists, one paragraph
- **Goals**: Numbered list of what the system/feature must do
- **Non-goals**: Explicit list of what will NOT be done (the negative prompt)
- **User scenarios**: Concrete S1, S2, S3… descriptions of user interactions
- **Business rules**: Invariants, constraints, edge cases
- **Acceptance criteria**: How we know it's done — testable, binary conditions

**Rules for specs:**
- Max 2 pages. If longer, the scope is too big — decompose into multiple specs
- Every goal must have at least one acceptance criterion
- Non-goals are NOT optional. They prevent scope creep and guide the model
- Scenarios use concrete examples, not abstract descriptions

**Output:** `specification.md` → Present to user for review → Get explicit approval before proceeding.

### Phase 2: Implementation Plan — `plan.md`

The plan locks in architectural decisions so the implementation doesn't "grow on its own."

Read `references/plan-template.md` for the full template.

**Key sections:**
- **Components/Stack**: What tools, libraries, frameworks will be used
- **Data model**: Entities, relationships, key fields (for data-driven tasks)
- **Key decisions**: Architectural choices with brief rationale
- **File/directory structure**: Where things will live
- **Quality strategy**: What tests, linting, checks will be applied
- **Dependencies**: External services, APIs, packages needed

**Rules for plans:**
- The plan references the spec (e.g., "Implements S1-S3 via REST endpoints")
- Every key decision has a one-line rationale
- The plan does NOT contain implementation details — it's about WHAT and WHERE, not HOW
- For non-code tasks (documents, reviews, configs), adapt: "Components" becomes "Sections", "Data model" becomes "Structure", etc.

**Output:** `plan.md` → Present to user for review → Get explicit approval before proceeding.

### Phase 3: Task Decomposition — `tasks.md`

Decomposition turns the plan into executable work units. Each task is small enough to review in one pass and independent enough to test in isolation.

Read `references/tasks-template.md` for the full template.

**Task sizing rules:**
- Each task produces a reviewable, testable increment
- A task should take 1 tool-use "session" (roughly: one focused block of work)
- If a task description needs more than 3 sentences, it's too big — split it
- Tasks are ordered by dependency: foundations first, features second, polish last

**Task format:**
```
T1: [Short title]
    Delivers: [What artifact or behavior this produces]
    Depends on: [T0 / nothing]
    Acceptance: [How to verify it's done]

T2: [Short title]
    ...
```

**Rules:**
- First task is always scaffolding/setup (project init, base structure, healthcheck)
- Last task is always documentation/cleanup (README, final linting, CI config)
- Each task maps to spec goals and plan components
- Mark tasks that can run in parallel vs. those that are sequential

**Output:** `tasks.md` → Present to user → Begin implementation upon approval.

### Phase 4: Implementation

Execute tasks sequentially: T1 → review → T2 → review → … → Tn.

**Per-task workflow:**
1. Announce which task you're starting and what it delivers
2. Implement the task
3. Self-check against the task's acceptance criteria
4. Present the result for review
5. If the user approves, move to the next task
6. If not, iterate on the current task before moving on

**Implementation rules:**
- Never skip ahead. Complete T(n) before starting T(n+1)
- If implementation reveals a spec/plan gap, STOP and propose an update
- If behavior changes, the specification must be updated
- Follow the tech stack and conventions from the plan
- Apply quality checks from the plan (linting, tests) as you go

### Phase 5: Verification

After all tasks are complete:

1. Walk through each acceptance criterion from the spec
2. Confirm each scenario (S1, S2…) is covered
3. Run quality checks (tests, linting, etc.)
4. Verify non-goals were respected (nothing extra was built)
5. Produce a summary: what was built, what was deferred, any known limitations

---

## Adapting SDD to Task Types

SDD is not just for building new projects. The pipeline adapts to different task types by adjusting what each phase emphasizes.

Read `references/task-type-adaptations.md` for detailed guidance on:

| Task Type | Spec Focus | Plan Focus | Tasks Focus |
|-----------|-----------|-----------|------------|
| **Create** (new project/feature) | Goals, scenarios, data model | Architecture, stack, structure | Build incrementally |
| **Add** (feature to existing) | What changes, what doesn't | Integration points, migrations | Backwards-compatible steps |
| **Fix** (bug/issue) | Reproduction steps, root cause | Fix strategy, regression risk | Fix → test → verify |
| **Refactor** (improve existing) | Current problems, desired state | Refactoring strategy, safety net | Incremental transformations |
| **Review** (audit/analysis) | Review scope, criteria, standards | Review methodology, checklist | Section-by-section review |
| **Migrate** (move/upgrade) | Source/target, data mapping | Migration strategy, rollback plan | Phased migration steps |
| **Integrate** (connect systems) | API contracts, data flow | Auth, error handling, sync strategy | Connection → mapping → testing |
| **Automate** (workflow/pipeline) | Triggers, actions, edge cases | Tool selection, scheduling | Build pipeline incrementally |

---

## Quality Assurance

Every SDD project includes these baseline checks:

```
□ Linter/formatter passes (language-appropriate)
□ Key business rules have unit tests
□ At least one integration/end-to-end test for the happy path
□ Dependencies are minimal and justified
□ Sensitive data (PII, secrets) handling is specified upfront
□ If behavior changed, the spec was updated
□ README/docs describe the API/structure/usage
```

---

## Working with the User

SDD distributes responsibility clearly:

| Role | Responsibility |
|------|---------------|
| **User** | Approves spec, approves plan, reviews task results, makes product/architecture decisions |
| **Claude** | Drafts spec, drafts plan, decomposes tasks, implements, runs quality checks |
| **CI/Tests** | Catches regressions, enforces quality gates |

**Communication rules:**
- Present each phase's output and wait for approval before proceeding
- If uncertain about a requirement, ask — don't assume
- If a task reveals something unexpected, pause and discuss
- Keep the user informed of progress: "Starting T3 of 6: Order processing API"

---

## File Structure

SDD produces these artifacts in the working directory:

```
project-root/
├── sdd/
│   ├── specification.md    # Phase 1: What we're building
│   ├── plan.md             # Phase 2: How we'll build it
│   └── tasks.md            # Phase 3: Step-by-step execution plan
├── [project files]         # Phase 4: Implementation
└── README.md               # Phase 5: Documentation
```

For non-code tasks, adapt the structure:
```
task-root/
├── sdd/
│   ├── specification.md
│   ├── plan.md
│   └── tasks.md
└── [deliverables]
```

---

## Anti-Patterns

| Anti-Pattern | Why It Fails | SDD Fix |
|-------------|-------------|---------|
| Jumping to code without spec | Scope creep, rework, wrong assumptions | Spec forces alignment first |
| Spec without non-goals | Model generates everything it can think of | Non-goals set boundaries |
| Giant tasks (T1: "Build the backend") | Unreviewable, untestable, risky | Decompose until each task is atomic |
| Skipping verification | "It works on my machine" syndrome | Acceptance criteria are binary checks |
| Updating code but not spec | Spec and reality drift apart | Rule: behavior change = spec update |
| Over-engineering the spec | 10-page spec for a CRUD endpoint | 2-page max; if longer, split the scope |

---

## Quick Start

For any new task:

1. **Read** `references/specification-template.md`
2. **Draft** `specification.md` based on user's request
3. **Present** for approval
4. **Read** `references/plan-template.md`
5. **Draft** `plan.md`
6. **Present** for approval
7. **Read** `references/tasks-template.md`
8. **Draft** `tasks.md`
9. **Present** for approval
10. **Execute** tasks sequentially with per-task review
11. **Verify** against acceptance criteria
12. **Deliver** final result with summary