from bot.domain.models import AgentProfile
from bot.shared.prompt.explanatory_prompt import EXPLANATORY_PROMPT
from bot.shared.prompt.math_tutor_prompt import MATH_TUTOR_PROMPT
from bot.shared.prompt.researcher_prompt import RESEARCHER_PROMPT
from bot.shared.prompt.system_prompt import SYSTEM_PROMPT

DEFAULT_AGENT_NAME = "default"

ALL_TOOL_NAMES = [
    "search_vault",
    "read_note",
    "list_notes",
    "create_note",
    "append_note",
    "fetch_messages",
    "search_channel",
    "web_search",
    "save_memory",
    "recall_memory",
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
