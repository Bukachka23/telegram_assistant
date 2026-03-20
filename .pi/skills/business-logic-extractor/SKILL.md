---
name: business-logic-extractor
description: Extract and analyze core business logic from Python codebases by identifying domain concepts, workflows, decision points, and data flows while filtering out infrastructure, framework, and technical concerns. Use when analyzing Python projects to understand business rules, document domain logic, plan refactoring, or audit systems before migrations. Triggers include "extract business logic", "understand the domain logic", "analyze core functionality", "document business rules", or when examining Python files (.py) for domain understanding.
---

# Python Business Logic Extractor

## Overview

This skill guides systematic extraction of business logic from Python codebases. It helps identify domain concepts, business rules, workflows, and decision points while separating them from infrastructure code (HTTP handlers, database ORM, serialization, framework boilerplate).

## When to Use This Skill

Use this skill when:
- Analyzing unfamiliar Python codebases to understand core functionality
- Documenting business logic before refactoring or migrating systems
- Auditing domain logic for compliance, security, or architectural reviews
- Identifying coupling between business rules and infrastructure
- Creating technical documentation focused on "what the system does" vs "how it's built"

## Extraction Workflow

### Step 1: Scope Definition

Determine the extraction scope based on the user's request:

**Full codebase analysis**: Identify all business logic across the entire project
**Module/package focus**: Extract logic from specific modules (e.g., "analyze the payment processing module")
**Feature-specific**: Target particular business capabilities (e.g., "extract deposit flow logic")
**Comparative**: Compare logic across implementations (e.g., "how do old vs new systems handle reconciliation?")

**Output**: Confirm scope with user before proceeding. For large codebases (>50 files), recommend starting with high-value modules.

### Step 2: Codebase Discovery

Scan the codebase to understand structure and identify business logic hotspots:

```bash
# Get project structure
find /path/to/code -name "*.py" -type f | head -50

# Identify key directories (common patterns)
ls -la  # Look for: services/, domain/, business/, core/, models/, handlers/, workflows/

# Get file statistics
find /path/to/code -name "*.py" -exec wc -l {} + | sort -rn | head -20
```

**What to look for**:
- Service/domain/business/core directories (high likelihood of business logic)
- Model definitions (domain entities and relationships)
- Files with "handler", "processor", "manager", "service" naming
- Large files (>300 lines) often contain business logic mixed with infrastructure

**Output**: List of 5-10 highest-priority files to analyze first.

### Step 3: Pattern Recognition

Load `references/patterns.md` to understand common Python patterns for business logic:

```bash
view references/patterns.md
```

This reference provides examples of:
- Service layer patterns (business logic orchestration)
- Domain model patterns (entities, value objects, aggregates)
- Repository patterns (data access abstraction)
- Strategy patterns (pluggable business rules)
- Workflow/state machine patterns
- Decorator-based business logic
- Async business operations

### Step 4: File-by-File Analysis

For each high-priority file, perform systematic extraction:

**4a. Read the file**
```bash
view /path/to/file.py
```

**4b. Categorize each function/class/method**:
- **Core Business Logic**: Domain rules, calculations, validations, workflows
- **Infrastructure**: HTTP handlers, database queries, serialization, framework integration
- **Hybrid**: Functions mixing business logic and infrastructure (flag for refactoring)
- **Utilities**: Generic helpers with no business context

**4c. Extract business logic signatures**:
For each business logic component, document:
- Function/method name and signature
- Purpose (what business rule/capability it implements)
- Key decision points (if/else, match/case, business rule branches)
- Data transformations (what goes in, what comes out)
- Dependencies on other business logic components
- Any coupling to infrastructure (database, HTTP, external services)

**4d. Identify patterns**:
Note which patterns from `patterns.md` appear (e.g., "This is a service layer class orchestrating multiple domain operations")

### Step 5: Cross-File Analysis

After analyzing individual files, identify cross-cutting concerns:

**Domain concepts**: Extract entity names, relationships, and lifecycle
**Workflows**: Trace multi-step business processes across files
**Business rules**: List validation rules, calculation formulas, state transitions
**Decision points**: Document conditional logic that represents business choices
**Data flows**: Track how domain data moves through the system

**Use grep/ripgrep for tracking**:
```bash
# Find all references to a business concept
rg "class Order" /path/to/code
rg "def calculate_" /path/to/code
rg "if.*status.*==" /path/to/code  # Status-based business logic
```

### Step 6: Documentation

Use `references/analysis-template.md` to structure findings:

```bash
view references/analysis-template.md
```

Create a comprehensive markdown document with:
- Executive summary of business capabilities
- Domain model (entities and relationships)
- Business logic inventory (categorized by capability)
- Key workflows with sequence descriptions
- Business rules catalog
- Decision points and branching logic
- Infrastructure coupling analysis
- Recommendations for refactoring

**Output location**: Create in `/mnt/user-data/outputs/business-logic-analysis.md`

## Tips for Effective Extraction

**Separate "what" from "how"**: Business logic is "what the system does for users", infrastructure is "how it's technically implemented"

**Look for domain language**: Variable names, function names, and comments using business terminology (not technical jargon) indicate business logic

**Follow the data transformations**: Business logic often appears as data transformation chains. Track: raw input → validation → business rules application → domain model update → output

**Identify decision trees**: Nested if/else, match/case, or strategy patterns often encode business rules

**Watch for coupling red flags**:
- Business calculations directly in HTTP handlers
- Domain logic inside ORM model methods
- Business rules in database queries
- State transitions coupled to API responses

**Use type hints as clues**: Functions accepting/returning domain model types likely contain business logic

**Check for decorator-based logic**: `@validate_`, `@authorize_`, `@transactional` decorators may wrap business logic

## Common Python Patterns to Recognize

**Service layer pattern**:
```python
class PaymentService:
    def process_payment(self, order_id, payment_method):
        # Business logic orchestration
```

**Domain model with business methods**:
```python
class Order:
    def calculate_total(self) -> Decimal:
        # Business calculation
    
    def can_be_cancelled(self) -> bool:
        # Business rule
```

**Strategy pattern for business rules**:
```python
class DiscountStrategy(ABC):
    @abstractmethod
    def calculate_discount(self, order: Order) -> Decimal:
        pass
```

For comprehensive pattern examples, see `references/patterns.md`.

## Output Format

Deliver findings as a structured markdown document with:
- Clear hierarchy (H1: domain, H2: capability, H3: specific logic)
- Code snippets showing extracted business logic
- Flow diagrams for complex workflows (use mermaid)
- Actionable insights (coupling issues, refactoring opportunities)

Present the analysis file using the present_files tool.