---
name: code-difference
description: >
  Generate a detailed Markdown report comparing two Git branches in the current repository.
  Use this skill whenever the user types "code-difference", asks to "compare branches",
  "review changes between branches", "what changed in branch X vs Y", "diff between branches",
  or any request to understand what was implemented/changed in a feature branch compared to another.
  Also trigger when the user mentions a branch name and wants an overview of its changes.
  Always use this skill even if the user only says "code-difference" with no further context — prompt them for branch names.
---

# Code Difference Skill

Produces a detailed, file-by-file Markdown report of all changes between two Git branches.

---

## Workflow

### Step 1 – Gather inputs

If the user hasn't provided both branch names, ask for:
- **Base branch** (e.g. `develop`, `main`)
- **Feature branch** (e.g. `IN-4824-feat-new-payment`)
- **Scope** (optional): a specific directory or file path to limit the diff. If not provided, analyze the entire repo.

### Step 2 – Validate the Git repo

```bash
git rev-parse --is-inside-work-tree
git fetch --all --quiet   # ensure remote branches are up to date
git branch -a             # confirm both branches exist
```

If branches don't exist locally, try `origin/<branch>` remotes.

### Step 3 – Get the list of changed files

```bash
git diff --name-status <base_branch>...<feature_branch> [-- <scope_path>]
```

Parse the output into a list of files with their change type:
- `A` = Added
- `M` = Modified  
- `D` = Deleted
- `R` = Renamed

### Step 4 – For each changed file, generate a Python context diff

Extract both versions of the file from git, then generate a `difflib.context_diff`:

```python
import difflib
import subprocess

def get_file_content(branch: str, filepath: str) -> list[str]:
    result = subprocess.run(
        ["git", "show", f"{branch}:{filepath}"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return []  # file didn't exist on this branch
    return result.stdout.splitlines(keepends=True)

def generate_context_diff(base_branch: str, feature_branch: str, filepath: str) -> str:
    base_lines = get_file_content(base_branch, filepath)
    feature_lines = get_file_content(feature_branch, filepath)

    diff = difflib.context_diff(
        base_lines,
        feature_lines,
        fromfile=f"{base_branch}/{filepath}",
        tofile=f"{feature_branch}/{filepath}",
        n=5  # lines of context around each change
    )
    return "".join(diff)
```

Run this script per file and capture the output. Then analyze the diff and extract:
1. **What changed** — logical description of additions/deletions (not just line numbers)
2. **Intent / Why** — infer the purpose from context: function names, variable names, comments, surrounding code
3. **Potential risks / side effects** — breaking changes, removed validations, changed interfaces, DB migrations, new dependencies, performance implications
4. **The context diff output** — include the `difflib.context_diff` output in a fenced code block

### Step 5 – Build the Markdown report

Structure the report as follows:

```markdown
# Branch Diff Report: `<base>` → `<feature>`

**Generated:** <datetime>  
**Base branch:** `<base>`  
**Feature branch:** `<feature>`  
**Scope:** <path or "entire repository">  
**Total files changed:** <N> (Added: X | Modified: Y | Deleted: Z)

---

## Summary

<2–4 sentence high-level overview of what this branch implements>

---

## Changed Files

### 1. `path/to/file.py` · Modified

#### What changed
<Logical description of what was added/removed/restructured>

#### Intent / Why
<Inferred purpose of these changes>

#### Potential Risks & Side Effects
- <risk 1>
- <risk 2>
- ✅ No significant risks detected ← use this if no risks found

#### Diff (context diff)
```
*** <base_branch>/path/to/file.py
--- <feature_branch>/path/to/file.py
***************
*** 10,15 ****
  # unchanged context line
! - old line (changed)
  # unchanged context line
--- 10,15 ----
  # unchanged context line
! + new line (changed)
  # unchanged context line
```

---

### 2. `path/to/another_file.py` · Added
...
```

Repeat the per-file block for every changed file, ordered by: Modified → Added → Deleted → Renamed.

### Step 6 – Save the report

Save the report as a `.md` file:

```
code-diff-<base>-vs-<feature>-<YYYYMMDD>.md
```

Copy to `/mnt/user-data/outputs/` and present it to the user with the `present_files` tool.

---

## Tips for quality analysis

- **For Python files**: look for changed function signatures, new/removed decorators, ORM query changes, new exceptions, changed return types
- **For config/settings files**: highlight new env variables, changed defaults, removed flags
- **For migration files** (Django/Alembic): always flag as HIGH RISK and describe the schema change precisely
- **For test files**: note what new scenarios are covered or what was removed
- **For `requirements.txt` / `pyproject.toml`**: list every added/removed/version-bumped dependency
- **Deleted files**: always investigate why — could be a refactor, dead code removal, or accidental deletion

## Risk severity labels

Use these labels in the Risks section:
- 🔴 **HIGH** — breaking change, data loss risk, removed auth/validation, migration
- 🟡 **MEDIUM** — changed interface, new external dependency, altered business logic
- 🟢 **LOW** — refactor, renaming, formatting, test additions
- ✅ **None** — purely additive, no regressions expected