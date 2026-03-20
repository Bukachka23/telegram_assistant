# Specification Template

Use this template to draft `specification.md` for any SDD task. Adapt sections to the task type — not every section applies to every task, but the structure should remain consistent.

---

## Template

```markdown
# [Project/Feature/Task Name]

## 1. Context

[One paragraph: Why does this exist? What problem does it solve? Who is it for?]

## 2. Goals

[Numbered list of what the system/feature/deliverable must do. Each goal is a concrete, testable statement.]

1) [Goal 1 — user-facing behavior or deliverable]
2) [Goal 2]
3) [Goal N]

## 3. Non-Goals

[Explicit list of what will NOT be done. This is the "negative prompt" — it constrains scope and prevents the generation of unnecessary work.]

- [Thing that might seem in scope but is not]
- [Feature that will be deferred to a later phase]
- [Integration or complexity that is out of MVP scope]

## 4. User Scenarios (or Workflow Steps)

[For user-facing work: concrete scenarios describing user interactions.
For non-user-facing work: workflow steps describing the process.]

S1. [Scenario name]: [Description of what the user does and what happens]
S2. [Scenario name]: [Description]
S3. [Scenario name]: [Description]

## 5. Business Rules (or Constraints)

[Invariants, edge cases, constraints that must be respected.]

- [Rule 1: e.g., "Price is fixed at the time of order creation"]
- [Rule 2: e.g., "Personal data must not appear in logs"]
- [Rule 3: e.g., "All API responses must return within 500ms"]

## 6. Acceptance Criteria

[How we know it's done. Each criterion is binary: pass or fail. Must be testable.]

- [ ] [Criterion 1 — maps to Goal 1 and/or Scenario S1]
- [ ] [Criterion 2 — maps to Goal 2 and/or Scenario S2]
- [ ] [Criterion N]
- [ ] [Quality criterion: e.g., "CI passes (linter + tests)"]
- [ ] [Documentation criterion: e.g., "README describes API and data structure"]
```

---

## Guidance by Task Type

### Create (new project/feature)
- **Goals**: Focus on user-facing behaviors
- **Scenarios**: Full user journeys (S1: Browse → S2: Select → S3: Purchase)
- **Business rules**: Data invariants, security constraints
- **Acceptance**: UI reproducibility + integration tests + CI

### Add (feature to existing code)
- **Context**: Reference the existing system and what's being extended
- **Goals**: What the new feature adds (not what already exists)
- **Non-goals**: Explicitly state what existing functionality is NOT being changed
- **Business rules**: Backwards compatibility constraints
- **Acceptance**: New behavior works + existing tests still pass

### Fix (bug/issue)
- **Context**: Describe the bug — what happens vs. what should happen
- **Goals**: 1) Fix the specific bug. 2) Add regression test.
- **Scenarios**: S1: Reproduction steps. S2: Expected behavior after fix.
- **Business rules**: Edge cases related to the bug
- **Acceptance**: Bug no longer reproducible + regression test passes + no new failures

### Refactor (improve existing code)
- **Context**: What's wrong with the current state (tech debt, performance, readability)
- **Goals**: Measurable improvements (e.g., "reduce function size to <20 lines", "eliminate code duplication")
- **Non-goals**: No new features. No behavior changes.
- **Business rules**: Behavior must remain identical
- **Acceptance**: All existing tests pass + new quality metrics met + no behavior change

### Review (audit/analysis)
- **Context**: What is being reviewed and why
- **Goals**: What the review should produce (findings, recommendations, report)
- **Non-goals**: What the review will NOT fix (just identify)
- **Scenarios**: Review workflow (S1: Scan structure → S2: Deep-dive modules → S3: Generate report)
- **Acceptance**: All scope areas covered + findings documented + recommendations prioritized

### Migrate (move/upgrade)
- **Context**: Source system/version → target system/version
- **Goals**: What must be migrated and what must work after migration
- **Non-goals**: What can be left behind or done in a later phase
- **Business rules**: Data integrity constraints, rollback requirements
- **Acceptance**: All data migrated + functionality verified + rollback tested

### Integrate (connect systems)
- **Context**: System A ↔ System B, what data flows between them
- **Goals**: What data/events must flow and in which direction
- **Non-goals**: Which integrations are out of scope
- **Business rules**: API contracts, auth requirements, rate limits, error handling
- **Acceptance**: Data flows correctly + errors handled gracefully + auth works

### Automate (workflow/pipeline)
- **Context**: What manual process is being automated
- **Goals**: What the automation must do (triggers, actions, outputs)
- **Non-goals**: Edge cases that will still be handled manually
- **Business rules**: Timing constraints, retry policies, failure handling
- **Acceptance**: Automation runs end-to-end + handles failures + produces correct output

---

## Spec Quality Checklist

Before presenting the spec to the user:

```
□ Context is one paragraph (not a novel)
□ Goals are numbered and testable
□ Non-goals exist and are meaningful (not filler)
□ Every scenario has concrete actions and outcomes
□ Business rules cover edge cases, not just happy path
□ Every goal maps to at least one acceptance criterion
□ Acceptance criteria are binary (pass/fail, not "good enough")
□ Total length is under 2 pages
□ No implementation details leaked into the spec
```