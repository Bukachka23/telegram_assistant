# Task Type Adaptations

SDD adapts to different task types by adjusting emphasis across the pipeline phases. This reference provides concrete guidance and mini-examples for each type.

---

## Create — Building Something New

**When:** "Build a…", "Create a…", "Set up a…", "New project for…"

**Spec emphasis:** Goals and scenarios drive the design. Non-goals are critical to prevent scope explosion.

**Plan emphasis:** Full architecture — stack, data model, project structure, quality gates.

**Tasks emphasis:** Incremental build — scaffolding first, data layer, business logic, integration, polish.

### Mini-Example: REST API for Task Management

**Spec fragment:**
```
Goals: 1) CRUD operations for tasks. 2) Filter by status and assignee. 3) Due date reminders.
Non-goals: Real-time sync, file attachments, team management.
S1: User creates a task with title, description, due date.
S2: User lists tasks filtered by status=pending.
Acceptance: Integration test creates, lists, and deletes a task.
```

**Tasks fragment:**
```
T1: FastAPI scaffolding + healthcheck
T2: Task model + Alembic migration
T3: CRUD endpoints (create, read, update, delete)
T4: Filtering and sorting (status, assignee, due date)
T5: Due date reminder logic + tests
T6: README + API docs + final linting
```

---

## Add — Extending Existing Systems

**When:** "Add a feature…", "I need to also support…", "Extend this with…"

**Spec emphasis:** What changes vs. what stays the same. Backwards compatibility is a business rule.

**Plan emphasis:** Integration points — how the new feature connects without breaking existing code.

**Tasks emphasis:** Non-destructive increments. Run existing tests after EVERY task.

### Mini-Example: Add Email Notifications to an Order System

**Spec fragment:**
```
Context: Existing order system handles creation and status changes. 
         Need to notify customers via email on status changes.
Goals: 1) Send email when order status changes. 2) Email includes order ID, new status, ETA.
Non-goals: SMS notifications, email template editor, notification preferences.
Business rules: Email failures must not block order status changes.
Acceptance: Existing order tests pass + email sent on status change + email failure doesn't crash.
```

**Tasks fragment:**
```
T1: Email service interface + mock implementation
T2: Hook email trigger into order status change flow
T3: Email template (order ID, status, ETA)
T4: Error handling (email failure doesn't block orders)
T5: Integration test + verify existing tests pass
```

---

## Fix — Resolving Bugs and Issues

**When:** "There's a bug…", "This doesn't work…", "Fix the issue where…", "Error when…"

**Spec emphasis:** Reproduction steps are the spec. What happens vs. what should happen.

**Plan emphasis:** Root cause analysis, fix strategy, regression prevention.

**Tasks emphasis:** Reproduce → diagnose → fix → prevent. Minimal changes only.

### Mini-Example: Cart Total Calculation Bug

**Spec fragment:**
```
Context: Cart shows $0.00 total when quantity > 99 for any item.
Goals: 1) Fix total calculation for all quantities. 2) Add regression test.
S1: Reproduce: Add item, set qty=100, observe total shows $0.00.
S2: Expected: Total correctly shows item_price × 100.
Business rules: Total must use Decimal, not float. Max quantity is 9999.
Acceptance: Test with qty=100 passes. Test with qty=9999 passes. Existing cart tests pass.
```

**Tasks fragment:**
```
T1: Write failing test reproducing the bug (qty=100 → $0.00)
T2: Trace root cause (integer overflow? type conversion? DB field size?)
T3: Fix the calculation (minimal change)
T4: Add edge case tests (qty=1, qty=99, qty=100, qty=9999)
T5: Run full test suite, verify no regressions
```

---

## Refactor — Improving Without Changing Behavior

**When:** "Clean up…", "Refactor…", "This code is messy…", "Reduce complexity…", "Make maintainable…"

**Spec emphasis:** Current problems (metrics if possible) and desired state. Behavior must NOT change.

**Plan emphasis:** Refactoring strategy, safety net (tests), transformation steps.

**Tasks emphasis:** Each task is one transformation. Tests pass after every single task.

### Mini-Example: Decompose a 200-Line Order Processing Function

**Spec fragment:**
```
Context: process_order() is 200 lines with validation, pricing, DB ops, and notifications mixed.
Goals: 1) Split into ≤20-line functions. 2) Eliminate code duplication. 3) Add type hints.
Non-goals: No new features. No behavior changes. No DB schema changes.
Business rules: All existing tests must pass after every step. Return values identical.
Acceptance: No function >25 lines. All existing tests pass. Type hints on all public functions.
```

**Tasks fragment:**
```
T1: Add test coverage for current behavior (if insufficient)
T2: Extract validation functions (validate_items, validate_customer)
T3: Extract pricing functions (calculate_subtotal, apply_discounts, calculate_total)
T4: Extract I/O functions (save_order, send_confirmation)
T5: Add type hints to all extracted functions
T6: Verify all tests pass, run linter, update docstrings
```

---

## Review — Audit and Analysis

**When:** "Review this code…", "Audit the…", "Check for…", "Analyze the…", "What's wrong with…"

**Spec emphasis:** Review scope, criteria, and standards. What questions the review answers.

**Plan emphasis:** Review methodology — what tools, what checklist, what severity levels.

**Tasks emphasis:** One area per task. Final task synthesizes into actionable report.

### Mini-Example: Security Review of a FastAPI Application

**Spec fragment:**
```
Context: FastAPI app handling user data, needs security review before launch.
Goals: 1) Identify injection vulnerabilities. 2) Check auth implementation. 3) Audit data exposure.
Non-goals: Performance review, code style review, infrastructure security.
S1: Review all user input handling for injection risks.
S2: Review auth middleware and token handling.
S3: Review API responses for excessive data exposure.
Acceptance: All in-scope areas reviewed. Findings documented with severity. Fix recommendations provided.
```

**Tasks fragment:**
```
T1: Set up review checklist (OWASP Top 10 relevant items)
T2: Review input validation and SQL injection surface
T3: Review auth (token generation, validation, expiry, middleware)
T4: Review API responses (data exposure, error message leakage)
T5: Synthesize findings into report (severity: critical/high/medium/low)
```

---

## Migrate — Moving Between Systems or Versions

**When:** "Migrate from…", "Upgrade to…", "Move to…", "Port from…"

**Spec emphasis:** Source → target mapping. What must be preserved, what can be dropped.

**Plan emphasis:** Migration strategy, rollback plan, data validation approach.

**Tasks emphasis:** Phased migration — analyze, prepare, migrate, validate, rollback-test.

### Mini-Example: Migrate from SQLite to PostgreSQL

**Spec fragment:**
```
Context: App uses SQLite for development, moving to PostgreSQL for production.
Goals: 1) All data migrates correctly. 2) All queries work on PostgreSQL. 3) Rollback is possible.
Non-goals: Schema optimization, query performance tuning, connection pooling (later phase).
Business rules: Zero data loss. All foreign key relationships preserved.
Acceptance: Data counts match. Sample record comparison passes. All app tests pass on PostgreSQL.
```

**Tasks fragment:**
```
T1: Audit SQLite schema and data (tables, types, constraints, row counts)
T2: Create PostgreSQL schema (type mapping, constraints, sequences)
T3: Data migration script (export → transform → import)
T4: Dry run on staging + data validation (counts, samples, FKs)
T5: Update application config and connection handling
T6: Run full test suite on PostgreSQL + rollback test
```

---

## Integrate — Connecting Systems

**When:** "Connect to…", "Integrate with…", "Hook up…", "Sync data between…"

**Spec emphasis:** API contracts, data flow direction, error scenarios.

**Plan emphasis:** Auth, sync strategy, error handling, rate limits.

**Tasks emphasis:** Connection first, then mapping, then error handling, then end-to-end test.

### Mini-Example: Integrate with Stripe for Payments

**Spec fragment:**
```
Context: E-commerce app needs payment processing via Stripe.
Goals: 1) Create payment intent on checkout. 2) Handle success/failure webhooks. 3) Store payment status.
Non-goals: Subscriptions, refunds, multi-currency (later phases).
Business rules: Never store card numbers. Idempotent webhook handling. Failed payments don't create orders.
Acceptance: Test payment succeeds end-to-end. Webhook handles duplicate events. Failed payment returns user to cart.
```

**Tasks fragment:**
```
T1: Stripe SDK setup + API key config (env-based)
T2: Payment intent creation on checkout endpoint
T3: Webhook handler (payment_intent.succeeded, payment_intent.payment_failed)
T4: Order status update on webhook receipt (idempotent)
T5: Error handling (network failures, invalid webhooks, duplicates)
T6: End-to-end test with Stripe test mode
```

---

## Automate — Building Workflows and Pipelines

**When:** "Automate the process of…", "Build a pipeline for…", "Set up CI/CD…", "Create a workflow…"

**Spec emphasis:** Manual process documentation, triggers, expected outputs.

**Plan emphasis:** Tool selection, scheduling, failure handling, idempotency.

**Tasks emphasis:** Document manual process → scaffold → automate step by step → error handling → validate.

### Mini-Example: Automate Daily Sales Report Generation

**Spec fragment:**
```
Context: Sales team manually exports data from DB, formats in Excel, emails to leadership daily.
Goals: 1) Auto-generate report at 7 AM. 2) Include yesterday's sales, top products, comparison to last week.
         3) Email as PDF attachment.
Non-goals: Real-time dashboard, custom report builder, historical archive.
Business rules: Report must match manual format exactly. If data is unavailable, send "data unavailable" email.
Acceptance: Report matches manual version for 3 sample days. Runs on schedule. Handles DB downtime gracefully.
```

**Tasks fragment:**
```
T1: Document current manual process step by step
T2: SQL queries for report data (yesterday's sales, top products, week comparison)
T3: Report formatting (match existing Excel template → PDF)
T4: Email delivery setup
T5: Scheduling (cron / task scheduler) + failure handling
T6: Validate against 3 days of manual reports
```

---

## Quick Reference Matrix

| Type | First Task | Critical Business Rule | Last Task |
|------|-----------|----------------------|-----------|
| Create | Scaffolding | Non-goals set boundaries | Docs + cleanup |
| Add | Map integration points | Backwards compatibility | Verify existing tests |
| Fix | Reproduce bug | Minimal change only | Regression test |
| Refactor | Ensure test coverage | No behavior change | Verify all tests |
| Review | Define checklist | Cover all in-scope areas | Synthesize report |
| Migrate | Audit source | Zero data loss | Rollback test |
| Integrate | Define API contract | Error handling | End-to-end test |
| Automate | Document manual process | Match manual output | Validate vs. manual |