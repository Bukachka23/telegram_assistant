from bot.prompts.deep_research_prompt import (
    DEEP_RESEARCH_CYCLE_SYSTEM_PROMPT,
    DEEP_RESEARCH_JUDGE_SYSTEM_PROMPT,
    DEEP_RESEARCH_SYNTHESIS_SYSTEM_PROMPT,
    build_cycle_prompt,
    build_judge_prompt,
    build_synthesis_prompt,
)
from bot.prompts.explanatory_prompt import EXPLANATORY_PROMPT
from bot.prompts.math_tutor_prompt import MATH_TUTOR_PROMPT
from bot.prompts.researcher_prompt import RESEARCHER_PROMPT
from bot.prompts.system_prompt import SYSTEM_PROMPT

__all__ = [
    "DEEP_RESEARCH_CYCLE_SYSTEM_PROMPT",
    "DEEP_RESEARCH_JUDGE_SYSTEM_PROMPT",
    "DEEP_RESEARCH_SYNTHESIS_SYSTEM_PROMPT",
    "EXPLANATORY_PROMPT",
    "MATH_TUTOR_PROMPT",
    "RESEARCHER_PROMPT",
    "SYSTEM_PROMPT",
    "build_cycle_prompt",
    "build_judge_prompt",
    "build_synthesis_prompt",
]
