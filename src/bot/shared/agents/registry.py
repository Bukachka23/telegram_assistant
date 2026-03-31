from bot.domain.models import AgentProfile
from bot.shared.agents.configs import AGENTS, COMMAND_TO_AGENT, DEFAULT_AGENT_NAME


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
