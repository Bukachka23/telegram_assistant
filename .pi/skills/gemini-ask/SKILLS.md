# Quick Gemini Query

Send a quick question to Gemini about the codebase and get a response.

## Arguments

- `question`: The question to ask Gemini (required)
- `context`: Optional files for context (comma-separated)

## Instructions

1. Run Gemini with the question:

```bash
# With context files:
gemini -p "@{context} {question}" --approval-mode plan -o text

# Without context (uses project context):
gemini -p "{question}" --approval-mode plan -o text
```

2. Return Gemini's response directly to the user with minimal processing.

3. If the user wants Claude's perspective, they can ask as a follow-up.

## Example Usage

- `/gemini-ask question:"What testing framework is used in this project?"`
- `/gemini-ask question:"How does the authentication flow work?" context:"src/auth/"`
