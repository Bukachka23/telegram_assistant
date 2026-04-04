"""Tests for conversation manager."""

from datetime import UTC, datetime, timedelta

from bot.domain.models import Message, Role
from bot.services.conversation import ConversationManager
from bot.shared.agents.registry import DEFAULT_AGENT_NAME, get_default_agent


def _make_manager(
    *,
    default_model: str = "test-model",
    session_timeout_minutes: int = 30,
    max_history: int = 50,
) -> ConversationManager:
    return ConversationManager(
        default_model=default_model,
        session_timeout_minutes=session_timeout_minutes,
        max_history=max_history,
    )


def test_new_session_has_default_system_prompt_and_agent() -> None:
    manager = _make_manager()

    session = manager.get_or_create(user_id=1)

    assert len(session.messages) == 1
    assert session.messages[0].role == Role.SYSTEM
    assert session.messages[0].content == get_default_agent().prompt
    assert session.model == "test-model"
    assert session.active_agent == DEFAULT_AGENT_NAME


def test_get_existing_session() -> None:
    manager = _make_manager()

    first = manager.get_or_create(user_id=1)
    second = manager.get_or_create(user_id=1)

    assert first is second


def test_expired_session_resets_to_default_agent() -> None:
    manager = _make_manager(session_timeout_minutes=1)
    session = manager.get_or_create(user_id=1)
    manager.add_message(1, Message(role=Role.USER, content="old"))
    manager.set_active_agent(1, "researcher")

    session.last_active = datetime.now(UTC) - timedelta(minutes=5)

    new_session = manager.get_or_create(user_id=1)

    assert len(new_session.messages) == 1
    assert new_session is not session
    assert new_session.active_agent == DEFAULT_AGENT_NAME


def test_add_message() -> None:
    manager = _make_manager()

    manager.add_message(1, Message(role=Role.USER, content="hello"))
    session = manager.get_or_create(1)

    assert len(session.messages) == 2


def test_messages_for_api_format() -> None:
    manager = _make_manager()

    manager.add_message(1, Message(role=Role.USER, content="hi"))
    messages = manager.get_messages_for_api(1)

    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "hi"


def test_messages_for_api_can_override_system_prompt() -> None:
    manager = _make_manager()
    manager.add_message(1, Message(role=Role.USER, content="hi"))

    messages = manager.get_messages_for_api(1, system_prompt="OVERRIDE")
    session = manager.get_or_create(1)

    assert messages[0]["content"] == "OVERRIDE"
    assert session.messages[0].content == get_default_agent().prompt


def test_model_switching() -> None:
    manager = _make_manager()

    manager.get_or_create(1)
    manager.set_model(1, "new-model")

    assert manager.get_model(1) == "new-model"


def test_active_agent_switching_is_per_user() -> None:
    manager = _make_manager()

    manager.set_active_agent(1, "researcher")
    manager.get_or_create(2)

    assert manager.get_active_agent(1) == "researcher"
    assert manager.get_active_agent(2) == DEFAULT_AGENT_NAME


def test_clear_session_resets_active_agent() -> None:
    manager = _make_manager()

    manager.add_message(1, Message(role=Role.USER, content="hi"))
    manager.set_active_agent(1, "researcher")
    manager.clear(1)
    session = manager.get_or_create(1)

    assert len(session.messages) == 1
    assert session.active_agent == DEFAULT_AGENT_NAME


def test_trim_respects_max_history() -> None:
    manager = _make_manager(max_history=5)

    for index in range(20):
        manager.add_message(1, Message(role=Role.USER, content=f"msg {index}"))
    session = manager.get_or_create(1)

    assert len(session.messages) == 5


def test_tool_message_format() -> None:
    manager = _make_manager()

    manager.add_message(
        1,
        Message(role=Role.TOOL, content="result", tool_call_id="call_1"),
    )
    messages = manager.get_messages_for_api(1)
    tool_message = messages[-1]

    assert tool_message["tool_call_id"] == "call_1"
    assert tool_message["role"] == "tool"
