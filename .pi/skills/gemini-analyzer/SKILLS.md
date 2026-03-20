# Gemini Project Analysis

Use Gemini CLI to analyze the current project and provide insights for Claude to review.

## Arguments

- `task`: The analysis task to perform (e.g., "analyze architecture", "review security", "explain codebase")
- `files`: Optional specific files/folders to focus on (comma-separated, e.g., "src/,package.json")
- `format`: Output format - "text" (default) or "json"

## Instructions

1. First, construct the Gemini CLI command based on the arguments:
   - Use `-p` flag for non-interactive mode
   - Use `--approval-mode plan` for read-only analysis (safe)
   - Use `-o` flag for output format
   - Use `@` prefix for file context if specific files are provided

2. Run the Gemini CLI command using Bash:

```bash
# If files are specified:
gemini -p "@{files} {task}" --approval-mode plan -o {format}

# If no files specified (whole project):
gemini -p "{task}" --approval-mode plan -o {format}
```

3. After receiving Gemini's response:
   - Parse and summarize the key findings
   - Identify any areas that need clarification or deeper analysis
   - Cross-reference with the actual codebase if needed
   - Provide your own assessment comparing/contrasting with Gemini's analysis
   - Highlight agreements and any disagreements with reasoning

4. Present a consolidated report with:
   - **Gemini's Analysis Summary**: Key points from Gemini
   - **Claude's Review**: Your assessment of Gemini's findings
   - **Consensus Points**: Where both AIs agree
   - **Divergent Points**: Where you disagree (with reasoning)
   - **Recommendations**: Combined actionable recommendations

## Example Usage

- `/gemini-analyze task:"analyze the architecture and suggest improvements"`
- `/gemini-analyze task:"review for security vulnerabilities" files:"src/api/,src/auth/"`
- `/gemini-analyze task:"explain the data flow" format:"json"`
