"""Tests for built-in agent registry."""

from bot.prompts import EXPLANATORY_PROMPT, MATH_TUTOR_PROMPT, RESEARCHER_PROMPT, SYSTEM_PROMPT
from bot.config.agents import (
    DEFAULT_AGENT_NAME,
    get_agent,
    get_agent_by_command,
    get_default_agent,
    list_agents,
)


def test_get_default_agent() -> None:
    agent = get_default_agent()

    assert agent.name == DEFAULT_AGENT_NAME
    assert agent.display_name == "Default Assistant"
    assert agent.prompt == SYSTEM_PROMPT
    assert "search_vault" in agent.allowed_tools


def test_get_agent_by_name() -> None:
    agent = get_agent("explanatory")

    assert agent is not None
    assert agent.command == "explanatory"
    assert agent.prompt == EXPLANATORY_PROMPT


def test_get_agent_by_command_supports_optional_slash() -> None:
    direct = get_agent_by_command("math_tutor")
    with_slash = get_agent_by_command("/math_tutor")

    assert direct is not None
    assert with_slash is not None
    assert direct.name == "math_tutor"
    assert with_slash.name == "math_tutor"
    assert direct.prompt == MATH_TUTOR_PROMPT


def test_list_agents_returns_all_built_ins() -> None:
    agents = list_agents()
    names = {agent.name for agent in agents}

    assert names == {
        DEFAULT_AGENT_NAME,
        "explanatory",
        "math_tutor",
        "researcher",
    }


def test_researcher_profile_uses_own_prompt() -> None:
    agent = get_agent("researcher")

    assert agent is not None
    assert agent.prompt == RESEARCHER_PROMPT


def test_get_unknown_agent_returns_none() -> None:
    assert get_agent("missing") is None
    assert get_agent_by_command("missing") is None
