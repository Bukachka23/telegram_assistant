"""Tests for the default Telegram assistant system prompt."""

from bot.prompts.system_prompt import (
    PROMPT_AMBIGUITY,
    PROMPT_COMMUNICATION,
    PROMPT_IDENTITY,
    PROMPT_LIMITS,
    PROMPT_MEMORY,
    PROMPT_SOURCE_AWARENESS,
    PROMPT_TOOL_POLICY,
    PROMPT_WEB_SEARCH,
    SYSTEM_PROMPT,
)


def test_system_prompt_is_composed_from_named_sections() -> None:
    expected = (
        f"{PROMPT_IDENTITY}\n\n"
        f"{PROMPT_COMMUNICATION}\n\n"
        f"{PROMPT_AMBIGUITY}\n\n"
        f"{PROMPT_TOOL_POLICY}\n\n"
        f"{PROMPT_WEB_SEARCH}\n\n"
        f"{PROMPT_MEMORY}\n\n"
        f"{PROMPT_SOURCE_AWARENESS}\n\n"
        f"{PROMPT_LIMITS}"
    )

    assert expected == SYSTEM_PROMPT


def test_system_prompt_sections_are_non_empty() -> None:
    sections = [
        PROMPT_IDENTITY,
        PROMPT_COMMUNICATION,
        PROMPT_AMBIGUITY,
        PROMPT_TOOL_POLICY,
        PROMPT_WEB_SEARCH,
        PROMPT_MEMORY,
        PROMPT_SOURCE_AWARENESS,
        PROMPT_LIMITS,
    ]

    assert all(section.strip() for section in sections)
