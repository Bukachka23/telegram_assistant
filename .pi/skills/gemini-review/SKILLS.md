# Gemini Code Review

Get a second opinion from Gemini on code changes or specific files.

## Arguments

- `files`: Files to review (required, comma-separated, e.g., "src/app.ts,src/utils.ts")
- `focus`: Review focus area - "quality", "security", "performance", "all" (default: "all")

## Instructions

1. Build the review prompt based on focus:
   - **quality**: Code quality, maintainability, best practices, SOLID principles
   - **security**: Security vulnerabilities, input validation, auth issues
   - **performance**: Performance bottlenecks, optimization opportunities
   - **all**: Comprehensive review covering all areas

2. Run Gemini CLI:

```bash
gemini -p "@{files} Please review this code focusing on {focus}. Structure your response with: 1) Summary 2) Issues Found (severity: critical/high/medium/low) 3) Specific Recommendations with code examples" --approval-mode plan -o text
```

3. After receiving Gemini's review:
   - Read the actual files using Claude's tools to verify findings
   - Validate each issue Gemini found
   - Check for any issues Gemini might have missed
   - Assess the severity ratings

4. Produce a combined review report:
   - **Validated Issues**: Issues both AIs confirm
   - **Gemini-Only Findings**: Issues only Gemini found (with your assessment)
   - **Additional Findings**: Issues you found that Gemini missed
   - **Priority Action Items**: Ranked list of what to fix first
