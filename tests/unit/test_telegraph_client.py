"""Tests for Telegraph API client."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from bot.domain.exceptions import TelegraphError
from bot.infrastructure.telegraph.client import TelegraphClient


def _mock_response(status_code: int, json_data: dict) -> httpx.Response:
    """Build a fake httpx.Response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_data
    response.text = json.dumps(json_data)
    return response


class TestTelegraphClientInit:
    @pytest.mark.asyncio
    async def test_init_creates_account_and_stores_token(self):
        client = TelegraphClient(author_name="Test Bot")
        mock_response = _mock_response(200, {
            "ok": True,
            "result": {"access_token": "test-token-123", "short_name": "TestBot"},
        })

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response):
            await client.init()

        assert client._access_token == "test-token-123"

    @pytest.mark.asyncio
    async def test_init_raises_on_api_error(self):
        client = TelegraphClient(author_name="Test Bot")
        mock_response = _mock_response(200, {"ok": False, "error": "Bad request"})

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(TelegraphError, match="account creation failed"):
                await client.init()

    @pytest.mark.asyncio
    async def test_init_raises_on_http_error(self):
        client = TelegraphClient(author_name="Test Bot")

        with patch.object(
            client._client, "post", new_callable=AsyncMock, side_effect=httpx.HTTPError("timeout")
        ):
            with pytest.raises(TelegraphError, match="request failed"):
                await client.init()


class TestTelegraphClientCreatePage:
    @pytest.mark.asyncio
    async def test_create_page_returns_url(self):
        client = TelegraphClient(author_name="Test Bot")
        client._access_token = "test-token"

        mock_response = _mock_response(200, {
            "ok": True,
            "result": {"url": "https://telegra.ph/Test-Page-04-04"},
        })

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
            url = await client.create_page(
                title="Test Page",
                content=[{"tag": "p", "children": ["Hello"]}],
            )

        assert url == "https://telegra.ph/Test-Page-04-04"
        call_kwargs = mock_post.call_args
        body = call_kwargs[1]["json"]
        assert body["title"] == "Test Page"
        assert body["access_token"] == "test-token"

    @pytest.mark.asyncio
    async def test_create_page_raises_without_init(self):
        client = TelegraphClient(author_name="Test Bot")

        with pytest.raises(TelegraphError, match="not initialized"):
            await client.create_page(title="Test", content=[])

    @pytest.mark.asyncio
    async def test_create_page_raises_on_api_error(self):
        client = TelegraphClient(author_name="Test Bot")
        client._access_token = "test-token"
        mock_response = _mock_response(200, {"ok": False, "error": "CONTENT_TOO_BIG"})

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(TelegraphError, match="page creation failed"):
                await client.create_page(title="Test", content=[])

    @pytest.mark.asyncio
    async def test_create_page_raises_on_http_error(self):
        client = TelegraphClient(author_name="Test Bot")
        client._access_token = "test-token"

        with patch.object(
            client._client, "post", new_callable=AsyncMock, side_effect=httpx.HTTPError("connection error")
        ):
            with pytest.raises(TelegraphError, match="request failed"):
                await client.create_page(title="Test", content=[])

    @pytest.mark.asyncio
    async def test_create_page_truncates_long_title(self):
        client = TelegraphClient(author_name="Test Bot")
        client._access_token = "test-token"

        mock_response = _mock_response(200, {
            "ok": True,
            "result": {"url": "https://telegra.ph/Long-Title-04-04"},
        })

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
            long_title = "x" * 300
            await client.create_page(title=long_title, content=[])

        body = mock_post.call_args[1]["json"]
        assert len(body["title"]) <= 256


class TestTelegraphClientClose:
    @pytest.mark.asyncio
    async def test_close_closes_http_client(self):
        client = TelegraphClient(author_name="Test Bot")

        with patch.object(client._client, "aclose", new_callable=AsyncMock) as mock_close:
            await client.close()

        mock_close.assert_called_once()
