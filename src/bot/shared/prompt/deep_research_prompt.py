"""Prompt builders for multi-cycle deep research."""

from collections.abc import Sequence

SUMMARY_PREVIEW_LIMIT = 1200

DEEP_RESEARCH_CYCLE_SYSTEM_PROMPT = """\
You are an autonomous deep-research agent.

You work in cycles. In each cycle, review what is already known, identify the
most important gap, use tools when needed, and return a concise research memo.
You are not writing the final user-facing answer yet.

Rules:
- Use tools deliberately and only when they reduce uncertainty.
- Prefer evidence over speculation.
- Distinguish facts, interpretations, and open questions.
- Avoid repeating the same search unless you are explicitly verifying a claim.
- End with the most important next step if more work is needed.
"""

DEEP_RESEARCH_JUDGE_SYSTEM_PROMPT = """\
You judge whether a deep-research session is complete enough to answer the
user well.

Reply in exactly one line using one of these formats:
- YES: <brief reason>
- NO: <brief reason>

Say YES only when the current findings are sufficient for a useful, honest,
well-supported answer.
"""

DEEP_RESEARCH_SYNTHESIS_SYSTEM_PROMPT = """\
You are preparing the final answer for the user from a completed deep-research
session.

Write a concise, well-structured answer that:
- leads with the direct conclusion
- clearly separates strong evidence from weaker signals
- mentions uncertainty or missing evidence when relevant
- stays readable on mobile
"""


def _format_scratchpad(entries: Sequence[str]) -> str:
    if not entries:
        return "No prior findings yet."

    formatted_entries = []
    for index, entry in enumerate(entries, start=1):
        preview = entry.strip()
        if len(preview) > SUMMARY_PREVIEW_LIMIT:
            preview = preview[: SUMMARY_PREVIEW_LIMIT - 1].rstrip() + "…"
        formatted_entries.append(f"Cycle {index} findings:\n{preview}")
    return "\n\n".join(formatted_entries)


def build_cycle_prompt(*, query: str, cycle: int, max_cycles: int, scratchpad: Sequence[str]) -> str:
    """Build the user prompt for a single research cycle."""
    prior_findings = _format_scratchpad(scratchpad)
    return f"""\
Research question:
{query}

Current cycle: {cycle} of {max_cycles}

What is already known:
{prior_findings}

Your task for this cycle:
1. Identify the biggest remaining uncertainty or gap.
2. Use available tools if they help resolve that gap.
3. Return a compact research memo with these sections:
   - Findings
   - Evidence quality
   - Open questions
   - Recommended next step

Do not write the final answer yet.
"""


def build_judge_prompt(*, query: str, scratchpad: Sequence[str]) -> str:
    """Build the judge prompt that decides whether more cycles are needed."""
    findings = _format_scratchpad(scratchpad)
    return f"""\
Research question:
{query}

Accumulated findings:
{findings}

Is the research complete enough to answer the user well?
Reply with exactly one line in the required YES/NO format.
"""


def build_synthesis_prompt(*, query: str, scratchpad: Sequence[str]) -> str:
    """Build the final synthesis prompt from accumulated findings."""
    findings = _format_scratchpad(scratchpad)
    return f"""\
Research question:
{query}

Accumulated findings:
{findings}

Write the final answer for the user now.
"""
