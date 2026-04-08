"""Tests for deep research service."""

import pytest

from bot.services.deep_research import DeepResearchService
from bot.config.agents import get_agent


class FakeLLMService:
    """Minimal LLM stub for deep research orchestration tests."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    async def complete_side_context(
        self,
        *,
        messages: list[dict],
        model: str,
        allowed_tools: list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        self.calls.append(
            {
                "messages": messages,
                "model": model,
                "allowed_tools": allowed_tools,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
        return self._responses.pop(0)


async def _capture_progress(log: list[str], text: str) -> None:
    log.append(text)


@pytest.mark.asyncio
async def test_deep_research_stops_early_when_judge_says_yes() -> None:
    llm = FakeLLMService(
        [
            "Cycle 1 findings about longevity interventions.",
            "YES: the evidence is already sufficient for a useful answer.",
            "Final synthesis with cited categories and caveats.",
        ]
    )
    service = DeepResearchService(llm=llm)
    progress: list[str] = []

    result = await service.run(
        query="Most promising longevity interventions in 2024",
        model="test-model",
        on_progress=lambda text: _capture_progress(progress, text),
    )

    assert result == "Final synthesis with cited categories and caveats."
    assert progress[0] == "🔬 Starting deep research (up to 3 cycles)..."
    assert "Cycle 1/3" in progress[1]
    assert progress[2].startswith("📝 Cycle 1 summary:")
    assert progress[3] == "✅ Research complete after 1 cycle."
    assert len(llm.calls) == 3


@pytest.mark.asyncio
async def test_deep_research_runs_full_cycle_budget_when_judge_says_no() -> None:
    llm = FakeLLMService(
        [
            "Cycle 1 findings.",
            "NO: more verification is needed.",
            "Cycle 2 findings.",
            "NO: one last synthesis pass is still needed.",
            "Cycle 3 findings.",
            "Final synthesis after all cycles.",
        ]
    )
    service = DeepResearchService(llm=llm)
    progress: list[str] = []

    result = await service.run(
        query="Best evidence-based sleep interventions",
        model="test-model",
        on_progress=lambda text: _capture_progress(progress, text),
    )

    assert result == "Final synthesis after all cycles."
    assert any("Cycle 3/3" in entry for entry in progress)
    assert progress[-1] == "✅ Research complete after 3 cycles."
    assert len(llm.calls) == 6


@pytest.mark.asyncio
async def test_deep_research_uses_researcher_toolset_for_cycle_calls_only() -> None:
    llm = FakeLLMService(
        [
            "Cycle 1 findings.",
            "YES: enough.",
            "Final synthesis.",
        ]
    )
    service = DeepResearchService(llm=llm)

    await service.run(query="AI safety updates", model="test-model")

    researcher = get_agent("researcher")
    assert researcher is not None
    assert llm.calls[0]["allowed_tools"] == researcher.allowed_tools
    assert llm.calls[1]["allowed_tools"] is None
    assert llm.calls[2]["allowed_tools"] is None
