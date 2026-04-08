from __future__ import annotations

import re
from typing import TYPE_CHECKING

from bot.config.constants import DEEP_RESEARCH_MAX_CYCLES, JUDGE_MAX_TOKENS, SUMMARY_LIMIT
from bot.domain.models import JudgeDecision, ResearchState
from bot.domain.protocols import DeepResearchServiceProtocol, ProgressCallback
from bot.prompts import (
    DEEP_RESEARCH_CYCLE_SYSTEM_PROMPT,
    DEEP_RESEARCH_JUDGE_SYSTEM_PROMPT,
    DEEP_RESEARCH_SYNTHESIS_SYSTEM_PROMPT,
    build_cycle_prompt,
    build_judge_prompt,
    build_synthesis_prompt,
)
from bot.config.agents import get_agent, get_default_agent

if TYPE_CHECKING:
    from bot.domain.protocols import LLMServiceProtocol

_RE_WHITESPACE = re.compile(r"\s+")


class DeepResearchService(DeepResearchServiceProtocol):
    """Runs an auto research-style multi-cycle research loop."""

    def __init__(self, llm: LLMServiceProtocol) -> None:
        self._llm = llm
        self._researcher = get_agent("researcher") or get_default_agent()

    async def run(
        self,
        *,
        query: str,
        model: str,
        on_progress: ProgressCallback | None = None,
        max_cycles: int = DEEP_RESEARCH_MAX_CYCLES,
    ) -> str:
        """Execute deep research and return the final synthesized answer."""
        state = ResearchState(query=query.strip(), max_cycles=max_cycles)
        await self._emit(on_progress, f"🔬 Starting deep research (up to {max_cycles} cycles)...")

        completed_cycles = 0
        for cycle in range(1, max_cycles + 1):
            state.cycle = cycle
            completed_cycles = cycle
            await self._emit(on_progress, self._cycle_status_text(state))

            findings = await self._run_cycle(state=state, model=model)
            state.scratchpad.append(findings)

            summary = self._build_cycle_summary(findings)
            state.cycle_summaries.append(summary)
            await self._emit(on_progress, f"📝 Cycle {cycle} summary: {summary}")

            if cycle >= max_cycles:
                break

            decision = await self._judge_complete(state=state, model=model)
            if decision.should_stop:
                break

        await self._emit(on_progress, self._completion_text(completed_cycles))
        return await self._synthesize_final(state=state, model=model)

    async def _run_cycle(self, *, state: ResearchState, model: str) -> str:
        messages = [
            {"role": "system", "content": DEEP_RESEARCH_CYCLE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_cycle_prompt(
                    query=state.query,
                    cycle=state.cycle,
                    max_cycles=state.max_cycles,
                    scratchpad=state.scratchpad,
                ),
            },
        ]
        return await self._llm.complete_side_context(
            messages=messages,
            model=model,
            allowed_tools=self._researcher.allowed_tools,
            temperature=self._researcher.temperature,
            max_tokens=self._researcher.max_tokens,
        )

    async def _judge_complete(self, *, state: ResearchState, model: str) -> JudgeDecision:
        response = await self._llm.complete_side_context(
            messages=[
                {"role": "system", "content": DEEP_RESEARCH_JUDGE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_judge_prompt(
                        query=state.query,
                        scratchpad=state.scratchpad,
                    ),
                },
            ],
            model=model,
            allowed_tools=None,
            temperature=0.0,
            max_tokens=JUDGE_MAX_TOKENS,
        )
        return self._parse_judge_response(response)

    async def _synthesize_final(self, *, state: ResearchState, model: str) -> str:
        return await self._llm.complete_side_context(
            messages=[
                {"role": "system", "content": DEEP_RESEARCH_SYNTHESIS_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_synthesis_prompt(
                        query=state.query,
                        scratchpad=state.scratchpad,
                    ),
                },
            ],
            model=model,
            allowed_tools=None,
            temperature=self._researcher.temperature,
            max_tokens=self._researcher.max_tokens,
        )

    @staticmethod
    async def _emit(on_progress: ProgressCallback | None, text: str) -> None:
        if on_progress is not None:
            await on_progress(text)

    @staticmethod
    def _build_cycle_summary(findings: str) -> str:
        cleaned = _RE_WHITESPACE.sub(" ", findings).strip()
        if not cleaned:
            return "No material findings returned in this cycle."
        if len(cleaned) <= SUMMARY_LIMIT:
            return cleaned
        return cleaned[: SUMMARY_LIMIT - 1].rstrip() + "…"

    @staticmethod
    def _parse_judge_response(response: str) -> JudgeDecision:
        verdict_line = response.strip().splitlines()[0] if response.strip() else "NO: Empty judge response"
        normalized = verdict_line.upper()
        if normalized.startswith("YES:"):
            return JudgeDecision(should_stop=True, reason=verdict_line[4:].strip())
        if normalized.startswith("NO:"):
            return JudgeDecision(should_stop=False, reason=verdict_line[3:].strip())
        return JudgeDecision(should_stop=False, reason=verdict_line)

    @staticmethod
    def _cycle_status_text(state: ResearchState) -> str:
        if state.cycle == 1:
            phase = "exploring the question"
        elif state.cycle == state.max_cycles:
            phase = "synthesizing remaining gaps"
        else:
            phase = "verifying and cross-checking"
        return f"🔄 Cycle {state.cycle}/{state.max_cycles} — {phase}"

    @staticmethod
    def _completion_text(completed_cycles: int) -> str:
        suffix = "" if completed_cycles == 1 else "s"
        return f"✅ Research complete after {completed_cycles} cycle{suffix}."
