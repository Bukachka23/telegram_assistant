"""Tests for conversation manager."""

from datetime import datetime, timedelta
from unittest.mock import patch

from bot.domain.models import Message, Role
from bot.services.conversation import ConversationManager


class TestConversationManager:
    def _make_manager(self, **kwargs) -> ConversationManager:
        defaults = {
            "default_model": "test-model",
            "session_timeout_minutes": 30,
            "max_history": 50,
        }
        return ConversationManager(**{**defaults, **kwargs})

    def test_new_session_has_system_prompt(self):
        mgr = self._make_manager()
        session = mgr.get_or_create(user_id=1)
        assert len(session.messages) == 1
        assert session.messages[0].role == Role.SYSTEM
        assert session.model == "test-model"

    def test_get_existing_session(self):
        mgr = self._make_manager()
        s1 = mgr.get_or_create(user_id=1)
        s2 = mgr.get_or_create(user_id=1)
        assert s1 is s2

    def test_expired_session_resets(self):
        mgr = self._make_manager(session_timeout_minutes=1)
        session = mgr.get_or_create(user_id=1)
        mgr.add_message(1, Message(role=Role.USER, content="old"))

        # Simulate expiry
        session.last_active = datetime.now() - timedelta(minutes=5)

        new_session = mgr.get_or_create(user_id=1)
        assert len(new_session.messages) == 1  # Only system prompt
        assert new_session is not session

    def test_add_message(self):
        mgr = self._make_manager()
        mgr.add_message(1, Message(role=Role.USER, content="hello"))
        session = mgr.get_or_create(1)
        assert len(session.messages) == 2  # system + user

    def test_messages_for_api_format(self):
        mgr = self._make_manager()
        mgr.add_message(1, Message(role=Role.USER, content="hi"))
        msgs = mgr.get_messages_for_api(1)
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"
        assert msgs[1]["content"] == "hi"

    def test_model_switching(self):
        mgr = self._make_manager()
        mgr.get_or_create(1)
        mgr.set_model(1, "new-model")
        assert mgr.get_model(1) == "new-model"

    def test_clear_session(self):
        mgr = self._make_manager()
        mgr.add_message(1, Message(role=Role.USER, content="hi"))
        mgr.clear(1)
        session = mgr.get_or_create(1)
        assert len(session.messages) == 1  # Fresh system prompt

    def test_trim_respects_max_history(self):
        mgr = self._make_manager(max_history=5)
        for i in range(20):
            mgr.add_message(1, Message(role=Role.USER, content=f"msg {i}"))
        session = mgr.get_or_create(1)
        assert len(session.messages) == 5

    def test_tool_message_format(self):
        mgr = self._make_manager()
        mgr.add_message(
            1,
            Message(role=Role.TOOL, content="result", tool_call_id="call_1"),
        )
        msgs = mgr.get_messages_for_api(1)
        tool_msg = msgs[-1]
        assert tool_msg["tool_call_id"] == "call_1"
        assert tool_msg["role"] == "tool"
