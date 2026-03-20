# Implementation Plan Template

Use this template to draft `plan.md`. The plan locks in architectural and technical decisions so the implementation phase is predictable. It bridges the WHAT (spec) and the HOW (tasks).

---

## Template

```markdown
# Implementation Plan

## 1. Components / Stack

[List the tools, libraries, frameworks, services that will be used. For non-code tasks, list the tools and formats.]

- [Component 1]: [role in the system]
- [Component 2]: [role]
- [Component N]: [role]

## 2. Structure

[For code: data model with entities, fields, and relationships.
For documents: section outline.
For reviews: review categories and methodology.
For migrations: source-to-target mapping.]

### [Appropriate heading for task type]

[Describe the structure — entities, sections, categories, mappings, etc.]

## 3. Key Decisions

[Architectural choices that constrain implementation. Each decision has a one-line rationale.]

| Decision | Rationale |
|----------|-----------|
| [Decision 1] | [Why this choice was made] |
| [Decision 2] | [Why] |
| [Decision N] | [Why] |

## 4. File / Directory Layout

[Where things will live. For code: project structure. For docs: file organization. For automation: pipeline layout.]

```
[project-root]/
├── [dir/file]     # [purpose]
├── [dir/file]     # [purpose]
└── [dir/file]     # [purpose]
```

## 5. Quality Strategy

[What checks, tests, and gates will be applied.]

- [Check 1: e.g., "Linter: ruff / black"]
- [Check 2: e.g., "Unit tests for business rules"]
- [Check 3: e.g., "Integration test for critical path"]
- [Check 4: e.g., "Security: no PII in logs"]

## 6. Dependencies & Prerequisites

[External services, packages, APIs, data, or access needed before implementation can start.]

- [Dependency 1]
- [Dependency 2]
```

---

## Guidance by Task Type

### Create (new project)
- **Components**: Full stack listing (framework, DB, ORM, test runner, etc.)
- **Structure**: Complete data model with entities and relationships
- **Key decisions**: Architecture style (monolith vs. service), auth approach, storage strategy
- **Layout**: Full project directory tree
- **Quality**: Linter + unit tests + integration tests + CI

### Add (feature to existing)
- **Components**: Only NEW dependencies (reference existing ones briefly)
- **Structure**: New entities or changes to existing ones (highlight diffs)
- **Key decisions**: How the feature integrates without breaking existing code
- **Layout**: Where new files go within the existing structure
- **Quality**: Existing test suite + new tests for the feature

### Fix (bug)
- **Components**: Usually none new (unless the fix requires a library)
- **Structure**: Affected data flow or state (what goes wrong and where)
- **Key decisions**: Fix approach (patch vs. deeper refactor), regression prevention
- **Layout**: Which files will be modified
- **Quality**: Regression test + existing test suite

### Refactor
- **Components**: Same as current (unless swapping a dependency)
- **Structure**: Before/after comparison of the affected area
- **Key decisions**: Refactoring strategy (incremental vs. big-bang), safety net
- **Layout**: Files affected, any new files or moved files
- **Quality**: All existing tests must pass at every step

### Review / Audit
- **Components**: Review tools (linters, analyzers, checklists)
- **Structure**: Review categories (security, performance, architecture, code quality)
- **Key decisions**: Review methodology, scoring criteria, severity levels
- **Layout**: Report structure and format
- **Quality**: Coverage — every in-scope area reviewed

### Migrate
- **Components**: Source system, target system, migration tools
- **Structure**: Data mapping (source fields → target fields), transformation rules
- **Key decisions**: Migration strategy (big-bang vs. phased), rollback plan, data validation
- **Layout**: Migration scripts location, staging environment
- **Quality**: Data integrity checks, rollback test, comparison validation

### Integrate
- **Components**: Both systems, middleware/adapter, auth mechanism
- **Structure**: API contracts, data flow diagrams, event schemas
- **Key decisions**: Sync vs. async, error handling strategy, retry policy, auth flow
- **Layout**: Integration layer location, config management
- **Quality**: Contract tests, error scenario tests, load limits

### Automate
- **Components**: Automation platform, triggers, connectors, storage
- **Structure**: Pipeline stages, data transformations, trigger conditions
- **Key decisions**: Scheduling strategy, failure handling, idempotency, alerting
- **Layout**: Workflow files, config, scripts
- **Quality**: End-to-end test, failure recovery test, output validation

---

## Plan Quality Checklist

Before presenting the plan to the user:

```
□ Every component has a stated role
□ Structure is concrete (entities, fields, sections — not vague)
□ Key decisions have rationale (not just "we'll use X")
□ Layout matches the structure (no orphan files or missing directories)
□ Quality strategy is specific (named tools, named test types)
□ Dependencies are listed (nothing assumed to "just be there")
□ Plan references the spec (maps to goals and scenarios)
□ No implementation code in the plan (that's for the tasks phase)
□ Plan is under 2 pages
```