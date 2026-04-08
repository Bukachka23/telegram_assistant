from bot.domain.models import AgentProfile
from bot.prompts.explanatory_prompt import EXPLANATORY_PROMPT
from bot.prompts.math_tutor_prompt import MATH_TUTOR_PROMPT
from bot.prompts.researcher_prompt import RESEARCHER_PROMPT
from bot.prompts.system_prompt import SYSTEM_PROMPT

DEFAULT_AGENT_NAME = "default"

ALL_TOOL_NAMES = [
    "search_vault",
    "read_note",
    "list_vault_folders",
    "list_notes",
    "create_note",
    "append_note",
    "fetch_messages",
    "search_channel",
    "web_search",
    "save_memory",
    "recall_memory",
    "schedule",
    "list_schedules",
    "remove_schedule",
]

AGENTS = {
    DEFAULT_AGENT_NAME: AgentProfile(
        name=DEFAULT_AGENT_NAME,
        command="assistant",
        display_name="Default Assistant",
        prompt=SYSTEM_PROMPT,
        temperature=0.7,
        max_tokens=4096,
        allowed_tools=list(ALL_TOOL_NAMES),
    ),
    "explanatory": AgentProfile(
        name="explanatory",
        command="explanatory",
        display_name="Explanatory",
        prompt=EXPLANATORY_PROMPT,
        temperature=0.4,
        max_tokens=4096,
        allowed_tools=list(ALL_TOOL_NAMES),
    ),
    "math_tutor": AgentProfile(
        name="math_tutor",
        command="math_tutor",
        display_name="Math Tutor",
        prompt=MATH_TUTOR_PROMPT,
        temperature=0.2,
        max_tokens=4096,
        allowed_tools=[],
    ),
    "researcher": AgentProfile(
        name="researcher",
        command="researcher",
        display_name="Researcher",
        prompt=RESEARCHER_PROMPT,
        temperature=0.3,
        max_tokens=4096,
        allowed_tools=list(ALL_TOOL_NAMES),
    ),
}

COMMAND_TO_AGENT = {profile.command: profile for profile in AGENTS.values()}


def get_default_agent() -> AgentProfile:
    """Return the default assistant profile."""
    return AGENTS[DEFAULT_AGENT_NAME]


def get_agent(name: str) -> AgentProfile | None:
    """Return an agent profile by internal name."""
    return AGENTS.get(name)


def get_agent_by_command(command: str) -> AgentProfile | None:
    """Return an agent profile by slash-command name without the slash."""
    return COMMAND_TO_AGENT.get(command.lstrip("/"))


def list_agents() -> list[AgentProfile]:
    """Return all built-in agent profiles."""
    return list(AGENTS.values())


__all__ = [
    "AGENTS",
    "ALL_TOOL_NAMES",
    "COMMAND_TO_AGENT",
    "DEFAULT_AGENT_NAME",
    "get_agent",
    "get_agent_by_command",
    "get_default_agent",
    "list_agents",
]
