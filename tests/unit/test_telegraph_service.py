"""Tests for Telegraph publish service."""

import pytest

from bot.domain.exceptions import TelegraphError
from bot.services.telegraph import TelegraphPublishService, TelegraphResult


class FakeTelegraphClient:
    def __init__(self, url: str = "https://telegra.ph/Test-04-04") -> None:
        self.url = url
        self.error: Exception | None = None
        self.last_title: str | None = None
        self.last_content: list | None = None

    async def create_page(self, title: str, content: list[dict]) -> str:
        self.last_title = title
        self.last_content = content
        if self.error:
            raise self.error
        return self.url


class TestShouldPublish:
    def test_below_threshold_returns_false(self):
        service = TelegraphPublishService(client=FakeTelegraphClient(), threshold_chars=100)
        assert service.should_publish("short text") is False

    def test_above_threshold_returns_true(self):
        service = TelegraphPublishService(client=FakeTelegraphClient(), threshold_chars=10)
        assert service.should_publish("this is longer than ten chars") is True

    def test_exact_threshold_returns_false(self):
        text = "x" * 100
        service = TelegraphPublishService(client=FakeTelegraphClient(), threshold_chars=100)
        assert service.should_publish(text) is False

    def test_threshold_plus_one_returns_true(self):
        text = "x" * 101
        service = TelegraphPublishService(client=FakeTelegraphClient(), threshold_chars=100)
        assert service.should_publish(text) is True


class TestPublish:
    @pytest.mark.asyncio
    async def test_publish_returns_result_with_url_and_preview(self):
        fake_client = FakeTelegraphClient(url="https://telegra.ph/My-Page")
        service = TelegraphPublishService(client=fake_client)

        long_text = "This is a fairly long response. " * 20
        result = await service.publish(
            long_text, title="Test Question", model="claude-sonnet", agent="default",
        )

        assert isinstance(result, TelegraphResult)
        assert result.url == "https://telegra.ph/My-Page"
        assert len(result.preview) <= 310  # ~300 + "…"
        assert result.preview.endswith("…") or len(long_text) <= 300

    @pytest.mark.asyncio
    async def test_publish_short_text_preview_is_full_text(self):
        fake_client = FakeTelegraphClient()
        service = TelegraphPublishService(client=fake_client)

        result = await service.publish(
            "Short answer", title="Q", model="m", agent="a",
        )

        assert result.preview == "Short answer"

    @pytest.mark.asyncio
    async def test_publish_truncates_title_to_256(self):
        fake_client = FakeTelegraphClient()
        service = TelegraphPublishService(client=fake_client)

        long_title = "x" * 300
        await service.publish("body", title=long_title, model="m", agent="a")

        assert fake_client.last_title is not None
        assert len(fake_client.last_title) <= 256

    @pytest.mark.asyncio
    async def test_publish_passes_content_nodes_to_client(self):
        fake_client = FakeTelegraphClient()
        service = TelegraphPublishService(client=fake_client)

        await service.publish(
            "# Hello\n\nWorld", title="Test", model="claude", agent="researcher",
        )

        assert fake_client.last_content is not None
        assert len(fake_client.last_content) > 0
        # First node should be metadata
        assert fake_client.last_content[0]["tag"] == "p"

    @pytest.mark.asyncio
    async def test_publish_raises_telegraph_error_on_failure(self):
        fake_client = FakeTelegraphClient()
        fake_client.error = TelegraphError("API down")
        service = TelegraphPublishService(client=fake_client)

        with pytest.raises(TelegraphError, match="API down"):
            await service.publish("text", title="T", model="m", agent="a")


class TestPreview:
    @pytest.mark.asyncio
    async def test_preview_strips_markdown_headers(self):
        fake_client = FakeTelegraphClient()
        service = TelegraphPublishService(client=fake_client)

        text = "# Big Header\n\nActual content here that matters."
        result = await service.publish(text, title="T", model="m", agent="a")

        assert not result.preview.startswith("#")
        assert "Actual content" in result.preview

    @pytest.mark.asyncio
    async def test_preview_ends_at_word_boundary(self):
        fake_client = FakeTelegraphClient()
        service = TelegraphPublishService(client=fake_client)

        # Build text that's longer than 300 chars
        text = "word " * 100
        result = await service.publish(text, title="T", model="m", agent="a")

        # Should not cut mid-word
        assert result.preview.endswith("…")
        before_ellipsis = result.preview[:-1].rstrip()
        assert before_ellipsis.endswith("word")


class TestTelegraphResult:
    def test_frozen_dataclass(self):
        result = TelegraphResult(url="https://telegra.ph/test", preview="hello")
        assert result.url == "https://telegra.ph/test"
        assert result.preview == "hello"

        with pytest.raises(AttributeError):
            result.url = "changed"  # type: ignore[misc]
