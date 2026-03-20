# Initialize Gemini Project Context

Use Gemini's `/init` command to analyze the project and create a GEMINI.md file, then review it with Claude.

## Instructions

1. Run Gemini's init command to generate project analysis:

```bash
gemini -p "/init" -y -o text
```

2. After Gemini creates the GEMINI.md file, read it:

```bash
cat GEMINI.md 2>/dev/null || cat .gemini/GEMINI.md 2>/dev/null
```

3. Review the generated GEMINI.md:
   - Assess accuracy of project description
   - Verify identified technologies and dependencies
   - Check if key architectural decisions are captured
   - Identify any missing important context

4. Provide feedback:
   - **Accuracy Assessment**: How well Gemini understood the project
   - **Missing Context**: Important aspects not captured
   - **Suggestions**: Improvements to add to GEMINI.md

5. Optionally, help the user enhance the GEMINI.md with missing information.
