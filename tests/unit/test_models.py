"""Tests for domain models."""

from bot.domain.models import (
    ChannelFilter,
    Conversation,
    Message,
    Note,
    Role,
    ToolCall,
    ToolResult,
)


class TestMessage:
    def test_create_user_message(self):
        msg = Message(role=Role.USER, content="hello")
        assert msg.role == Role.USER
        assert msg.content == "hello"
        assert msg.tool_call_id is None

    def test_frozen(self):
        msg = Message(role=Role.USER, content="hello")
        try:
            msg.content = "changed"  # type: ignore
            raise AssertionError("Should be frozen")
        except AttributeError:
            pass


class TestConversation:
    def test_add_message(self):
        conv = Conversation(user_id=123, model="test")
        conv.add(Message(role=Role.USER, content="hi"))
        assert len(conv.messages) == 1

    def test_trim_preserves_system(self):
        conv = Conversation(user_id=123, model="test")
        conv.add(Message(role=Role.SYSTEM, content="system prompts"))
        for i in range(10):
            conv.add(Message(role=Role.USER, content=f"msg {i}"))

        conv.trim(max_messages=4)
        assert conv.messages[0].role == Role.SYSTEM
        assert len(conv.messages) == 4

    def test_trim_noop_when_under_limit(self):
        conv = Conversation(user_id=123, model="test")
        conv.add(Message(role=Role.USER, content="hi"))
        conv.trim(max_messages=10)
        assert len(conv.messages) == 1


class TestNote:
    def test_name_from_path(self):
        note = Note(path="folder/my-note.md", content="# Title")
        assert note.name == "my-note.md"

    def test_explicit_name(self):
        note = Note(path="folder/file.md", content="", name="custom")
        assert note.name == "custom"


class TestChannelFilter:
    def test_matches_keyword(self):
        f = ChannelFilter(username="@test", keywords=["python", "asyncio"])
        assert f.matches("New Python release today!")
        assert not f.matches("Rust is great")

    def test_empty_keywords_matches_all(self):
        f = ChannelFilter(username="@test", keywords=[])
        assert f.matches("anything")

    def test_case_insensitive(self):
        f = ChannelFilter(username="@test", keywords=["Python"])
        assert f.matches("PYTHON is great")


class TestToolCall:
    def test_create(self):
        tc = ToolCall(id="call_1", name="search_vault", arguments='{"query":"test"}')
        assert tc.name == "search_vault"


class TestToolResult:
    def test_create(self):
        tr = ToolResult(tool_call_id="call_1", content="result")
        assert not tr.is_error

    def test_error_result(self):
        tr = ToolResult(tool_call_id="call_1", content="failed", is_error=True)
        assert tr.is_error
