"""Tests for command handlers."""

from types import SimpleNamespace

import pytest

from bot.handlers.commands import setup_commands
from bot.services.conversation import ConversationManager
from bot.shared.agents.registry import DEFAULT_AGENT_NAME


class FakeMessage:
    """Minimal async message stub for command handler tests."""

    def __init__(self, text: str, user_id: int = 1, forward_origin=None) -> None:
        self.text = text
        self.from_user = SimpleNamespace(id=user_id)
        self.forward_origin = forward_origin
        self.answers: list[tuple[str, dict]] = []

    async def answer(self, text: str, **kwargs) -> None:
        self.answers.append((text, kwargs))


class FakeMonitor:
    def __init__(
        self,
        *,
        chat_id: int,
        title: str,
        username: str = "",
        keywords: list[str] | None = None,
    ) -> None:
        self.chat_id = chat_id
        self.title = title
        self.username = username
        self.keywords = keywords or []


class FakeMonitorService:
    def __init__(self) -> None:
        self.monitors: list[FakeMonitor] = []
        self.pending: dict[int, list[str]] = {}
        self.public_error: str | None = None

    async def list_monitors(self, owner_user_id: int) -> list[FakeMonitor]:
        del owner_user_id
        return list(self.monitors)

    def begin_pending_add(self, owner_user_id: int, keywords: list[str]) -> None:
        self.pending[owner_user_id] = keywords

    def has_pending_add(self, owner_user_id: int) -> bool:
        return owner_user_id in self.pending

    async def add_public_monitor(
        self,
        *,
        owner_user_id: int,
        channel_ref: str,
        keywords: list[str],
    ) -> FakeMonitor:
        del owner_user_id
        if self.public_error:
            raise ValueError(self.public_error)
        monitor = FakeMonitor(
            chat_id=1001,
            title="Public Channel",
            username=channel_ref,
            keywords=keywords,
        )
        self.monitors.append(monitor)
        return monitor

    async def add_forwarded_monitor(self, *, owner_user_id: int, forwarded_chat) -> FakeMonitor:
        keywords = self.pending[owner_user_id]
        monitor = FakeMonitor(
            chat_id=forwarded_chat.id,
            title=forwarded_chat.title,
            username=getattr(forwarded_chat, "username", "") or "",
            keywords=keywords,
        )
        self.monitors.append(monitor)
        self.pending.pop(owner_user_id, None)
        return monitor

    async def remove_monitor(self, owner_user_id: int, identifier: str) -> bool:
        del owner_user_id
        before = len(self.monitors)
        normalized = identifier.lstrip("@")
        self.monitors = [
            monitor
            for monitor in self.monitors
            if monitor.username.lstrip("@") != normalized and str(monitor.chat_id) != identifier
        ]
        return len(self.monitors) < before


@pytest.fixture
def conversations() -> ConversationManager:
    return ConversationManager(default_model="test-model")


@pytest.fixture
def monitor_service() -> FakeMonitorService:
    return FakeMonitorService()


def _get_handler(router, name: str):
    for handler in router.message.handlers:
        if handler.callback.__name__ == name:
            return handler.callback
    msg = f"Handler {name} not found"
    raise AssertionError(msg)


@pytest.mark.asyncio
async def test_start_command_mentions_agent_modes(
    conversations: ConversationManager,
    monitor_service: FakeMonitorService,
) -> None:
    router = setup_commands(conversations, monitor_service)
    handler = _get_handler(router, "cmd_start")
    message = FakeMessage("/start")

    await handler(message)

    text, kwargs = message.answers[0]
    assert "`/agent` — show current agent" in text
    assert "`/explanatory`" in text
    assert kwargs["parse_mode"] == "Markdown"


@pytest.mark.asyncio
async def test_agent_command_switches_active_agent(
    conversations: ConversationManager,
    monitor_service: FakeMonitorService,
) -> None:
    router = setup_commands(conversations, monitor_service)
    handler = _get_handler(router, "cmd_agent_switch")
    message = FakeMessage("/explanatory")

    await handler(message)

    assert conversations.get_active_agent(1) == "explanatory"
    assert message.answers[0][0] == "🤖 Active agent: `Explanatory`"


@pytest.mark.asyncio
async def test_second_agent_command_replaces_previous_agent(
    conversations: ConversationManager,
    monitor_service: FakeMonitorService,
) -> None:
    router = setup_commands(conversations, monitor_service)
    handler = _get_handler(router, "cmd_agent_switch")

    await handler(FakeMessage("/researcher"))
    await handler(FakeMessage("/math_tutor"))

    assert conversations.get_active_agent(1) == "math_tutor"


@pytest.mark.asyncio
async def test_agent_status_command_shows_current_and_available_agents(
    conversations: ConversationManager,
    monitor_service: FakeMonitorService,
) -> None:
    router = setup_commands(conversations, monitor_service)
    handler = _get_handler(router, "cmd_agent")
    message = FakeMessage("/agent")

    await handler(message)

    text, kwargs = message.answers[0]
    assert "Current agent: `Default Assistant`" in text
    assert "Use `/agent <mode>`" in text
    assert "/assistant" in text
    assert "/explanatory" in text
    assert "/math_tutor" in text
    assert "/researcher" in text
    assert kwargs["parse_mode"] == "Markdown"
    assert conversations.get_active_agent(1) == DEFAULT_AGENT_NAME


@pytest.mark.asyncio
async def test_agent_command_with_argument_switches_active_agent(
    conversations: ConversationManager,
    monitor_service: FakeMonitorService,
) -> None:
    router = setup_commands(conversations, monitor_service)
    handler = _get_handler(router, "cmd_agent")
    message = FakeMessage("/agent researcher")

    await handler(message)

    assert conversations.get_active_agent(1) == "researcher"
    assert message.answers[0][0] == "🤖 Active agent: `Researcher`"


@pytest.mark.asyncio
async def test_agent_command_with_unknown_agent_returns_help(
    conversations: ConversationManager,
    monitor_service: FakeMonitorService,
) -> None:
    router = setup_commands(conversations, monitor_service)
    handler = _get_handler(router, "cmd_agent")
    message = FakeMessage("/agent unknown_mode")

    await handler(message)

    text, kwargs = message.answers[0]
    assert "Unknown command" in text
    assert "unknown_mode" in text
    assert "Use `/agent`" in text
    assert kwargs["parse_mode"] == "Markdown"


@pytest.mark.asyncio
async def test_clear_command_resets_active_agent_to_default(
    conversations: ConversationManager,
    monitor_service: FakeMonitorService,
) -> None:
    conversations.set_active_agent(1, "researcher")
    router = setup_commands(conversations, monitor_service)
    handler = _get_handler(router, "cmd_clear")
    message = FakeMessage("/clear")

    await handler(message)

    assert message.answers[0][0] == "🗑 Conversation cleared."
    assert conversations.get_active_agent(1) == DEFAULT_AGENT_NAME


@pytest.mark.asyncio
async def test_monitor_command_lists_persisted_monitors(
    conversations: ConversationManager,
    monitor_service: FakeMonitorService,
) -> None:
    monitor_service.monitors.append(
        FakeMonitor(chat_id=-10055, title="Private Channel", keywords=["gym"])
    )
    router = setup_commands(conversations, monitor_service)
    handler = _get_handler(router, "cmd_monitor")
    message = FakeMessage("/monitor")

    await handler(message)

    text, kwargs = message.answers[0]
    assert "Active monitors" in text
    assert "Private Channel" in text
    assert "id:-10055" in text
    assert kwargs["parse_mode"] == "Markdown"


@pytest.mark.asyncio
async def test_monitor_add_without_channel_enters_pending_forward_mode(
    conversations: ConversationManager,
    monitor_service: FakeMonitorService,
) -> None:
    router = setup_commands(conversations, monitor_service)
    handler = _get_handler(router, "cmd_monitor")
    message = FakeMessage("/monitor add")

    await handler(message)

    assert monitor_service.has_pending_add(1) is True
    assert "Forward me a message from the private channel" in message.answers[0][0]


@pytest.mark.asyncio
async def test_monitor_add_public_channel_persists_immediately(
    conversations: ConversationManager,
    monitor_service: FakeMonitorService,
) -> None:
    router = setup_commands(conversations, monitor_service)
    handler = _get_handler(router, "cmd_monitor")
    message = FakeMessage("/monitor add @publicchan ai, ml")

    await handler(message)

    assert monitor_service.monitors[0].username == "@publicchan"
    assert monitor_service.monitors[0].keywords == ["ai", "ml"]
    assert "Monitoring Public Channel" in message.answers[0][0]


@pytest.mark.asyncio
async def test_forwarded_channel_message_completes_pending_setup(
    conversations: ConversationManager,
    monitor_service: FakeMonitorService,
) -> None:
    monitor_service.begin_pending_add(1, ["gym"])
    router = setup_commands(conversations, monitor_service)
    handler = _get_handler(router, "cmd_monitor_forward")
    message = FakeMessage(
        "forwarded",
        forward_origin=SimpleNamespace(
            chat=SimpleNamespace(id=-10055, title="Private Channel", username=None)
        ),
    )

    await handler(message)

    assert monitor_service.has_pending_add(1) is False
    assert monitor_service.monitors[0].chat_id == -10055
    assert "Monitoring Private Channel" in message.answers[0][0]


@pytest.mark.asyncio
async def test_monitor_remove_deletes_persisted_monitor(
    conversations: ConversationManager,
    monitor_service: FakeMonitorService,
) -> None:
    monitor_service.monitors.append(
        FakeMonitor(chat_id=-10055, title="Private Channel", keywords=["gym"])
    )
    router = setup_commands(conversations, monitor_service)
    handler = _get_handler(router, "cmd_monitor")
    message = FakeMessage("/monitor remove -10055")

    await handler(message)

    assert monitor_service.monitors == []
    assert message.answers[0][0] == "✅ Removed -10055"


@pytest.mark.asyncio
async def test_unknown_slash_command_returns_help(
    conversations: ConversationManager,
    monitor_service: FakeMonitorService,
) -> None:
    router = setup_commands(conversations, monitor_service)
    handler = _get_handler(router, "cmd_unknown")
    message = FakeMessage("/unknownagent")

    await handler(message)

    text, kwargs = message.answers[0]
    assert "Unknown command" in text
    assert "/unknownagent" in text
    assert kwargs["parse_mode"] == "Markdown"
