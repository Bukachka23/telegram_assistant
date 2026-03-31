# Refactoring Strategy

Strategic guidance on *when*, *why*, and *how* to refactor — and what technical debt really means.

Cross-reference: `code_smells_catalog.md` to identify smells | `refactoring_techniques_catalog.md` to select techniques.

---

## What Is Clean Code?

Refactoring's goal is clean code. Clean code has these properties:

| Property | What it means |
|----------|--------------|
| **Obvious** | Any developer can read it and understand what it does — no magic numbers, no bloated methods, no cryptic names |
| **No duplication** | Every change is made in one place only; no cognitive overhead tracking "all the copies" |
| **Minimal** | Fewest classes, moving parts, and lines of code that still solve the problem correctly |
| **Fully tested** | 0% test coverage is not clean code — it's a minefield. Passing all tests is non-negotiable |

> *"Code is liability. Keep it short and simple."*
>
> *"A method should do one thing, do it well, and do it only."*

---

## Technical Debt

Technical debt is the future cost you pay for shortcuts taken today. Like financial debt, it accrues **interest** — slowing development every day until the debt is paid off. Enough accumulated debt makes full repayment impossible.

**Example:** Skipping tests on new features temporarily speeds up delivery, but slows every day that follows — until tests are written (paying off the principal + interest).

### Causes of Technical Debt

| Cause | Description |
|-------|-------------|
| **Business pressure** | Features shipped before they're complete; patches and kludges hide unfinished parts |
| **Misunderstood consequences** | Management doesn't see that accumulating debt slows future development; refactoring is deprioritized |
| **Component coupling (monolith)** | The codebase resembles one big monolith; any change ripples everywhere; team isolation is impossible |
| **Lack of tests** | No feedback loop encourages risky workarounds; changes go directly to production with no safety net |
| **Lack of documentation** | New team members take weeks to onboard; key knowledge is lost when people leave |
| **Siloed teams** | People work with outdated understanding; no shared knowledge base; junior devs trained poorly |
| **Long-lived feature branches** | Parallel isolation accumulates debt; merging long branches multiplies it |
| **Delayed refactoring** | As requirements evolve, old design accumulates; the longer you wait, the more dependent code must be reworked |
| **No compliance monitoring** | Everyone writes code their own way; no shared standards enforced |
| **Incompetence** | Developer doesn't know how to write clean code |

---

## When to Refactor

### The Rule of Three

1. **First time** — Just do it. Get it done.
2. **Second time** — Notice the repetition, but do it anyway.
3. **Third time** — Stop. Refactor.

This rule prevents premature abstraction (too early) while catching duplication before it spreads (not too late).

### When Adding a Feature

- Refactor the code you need to touch **before** adding the feature
- Clean code is much easier to extend than messy code
- Refactoring is an investment: clean now = faster development every day after
- **Do not mix** refactoring commits with feature commits — keep them separate

### When Fixing a Bug

- Bugs live in dirty code. Cleaning the area around a bug often reveals it
- Proactive refactoring while bug-fixing prevents the same bug class from returning
- Managers appreciate it: fewer special "refactoring sprints" needed later

### During a Code Review

- Code review is the last opportunity to clean up before code goes public
- Best done as a pair review with the author: small issues fixed immediately, larger ones scoped
- Reviewing clean code takes minutes; reviewing dirty code takes hours

---

## How to Refactor

### Core Principles

**1. Refactoring must make the code cleaner.**

If code is just as messy after refactoring — you've wasted time. Common cause: trying to do too much in a single session. Mix of many refactorings in one big change makes it easy to lose track. When this happens, revert and restart with smaller, focused steps.

**2. Never add new functionality during refactoring.**

Mixing refactoring with feature development creates confusion, risk, and untestable changes. Separate them at commit level:
```
git commit -m "refactor: extract OrderProcessor class"
git commit -m "feat: add discount calculation to OrderProcessor"
```

**3. All existing tests must pass after every refactoring step.**

Two cases when tests break:
- **You made an error** → fix it before continuing
- **Tests were too low-level** (e.g., testing private methods) → refactor the tests, or write higher-level tests

No tests? Write them before starting refactoring. Refactoring without a test suite is dangerous.

### The Small-Steps Rule

Refactoring must be done as **a series of small, safe changes** — each one leaving the code in a working state. Never make a refactoring that requires the entire change to be "done" before tests pass.

```
Identify smell → Choose ONE technique → Apply → Run tests → ✅ Commit → Repeat
```

**Wrong approach:**
```
1. Rename 12 methods + move 3 classes + extract 2 modules (all in one session with no intermediate commits)
→ Tests fail → Hard to know what broke
```

**Right approach:**
```
1. Rename one method → tests pass → commit
2. Extract one class → tests pass → commit
3. Move one module → tests pass → commit
```

### Refactoring vs Rewriting

When code is so messy that incremental refactoring can't make progress:

1. Write tests first (or verify they exist and cover the behavior)
2. Consider a targeted rewrite of that specific module only
3. **Never rewrite without tests** — they are the safety net that defines "correct behavior"
4. Rewrite in a separate branch; compare behavior test-by-test

---

## Practical Checklist

### Before Starting

- [ ] Tests exist and pass (if not, write them first)
- [ ] The smell is identified (see `code_smells_catalog.md`)
- [ ] The technique is chosen (see `refactoring_techniques_catalog.md`)
- [ ] No new features will be mixed in
- [ ] Scope is clearly defined (one file, one class, one method)

### During Refactoring

- [ ] Making one change at a time
- [ ] Running tests after each change
- [ ] Committing small, descriptive changes
- [ ] Not introducing new behavior

### After Refactoring

- [ ] All tests pass
- [ ] Code is visibly cleaner (simpler names, shorter methods, less nesting)
- [ ] No new functionality was added
- [ ] The commit message describes the smell fixed, not just "refactor"

---

## Refactoring Smell → Timing Guide

| When you notice this | Best time to refactor |
|---------------------|----------------------|
| You need to add a feature nearby | **Now** — before adding the feature |
| You're fixing a bug in this area | **Now** — cleaning reveals bugs |
| You see it in a code review | **Now** — before merge |
| You're reading code to understand it | **Now** — cleaning aids comprehension |
| You're under a deadline | **Later** — schedule it; leave a `# TODO: refactor - Long Method` marker |
| It's in code you're not touching | **Later** — don't touch code that isn't in your current scope |
| It's in a third-party library | **Never** — use Introduce Foreign Method or Introduce Local Extension instead |

---

## Common Mistakes to Avoid

| Mistake | Why it's wrong | Better approach |
|---------|---------------|-----------------|
| Refactoring everything at once | Creates merge conflicts, hard to test, hard to review | Small steps, one smell at a time |
| Mixing refactoring with features | Untestable; obscures what changed | Separate commits always |
| Refactoring without tests | No safety net; behavior can silently change | Write tests first |
| Refactoring "just to refactor" | No clear payoff; wastes time | Refactor when it helps a specific task |
| Over-engineering while refactoring | Speculative Generality — adding flexibility for imagined future needs | YAGNI: refactor toward simplicity, not complexity |
| Renaming things and calling it done | Renaming is the lowest-impact refactoring | Address structural smells first (Long Method, Large Class) |
