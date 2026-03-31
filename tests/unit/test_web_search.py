"""Tests for Tavily Search client and web tools."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from bot.domain.exceptions import WebSearchError
from bot.infrastructure.websearch_engine.tavily_search import TavilySearchClient
from bot.tools.registry import ToolRegistry
from bot.tools.web_tools import register_web_tools

TAVILY_RESPONSE = {
    "results": [
        {
            "title": "Python 3.14 Released",
            "url": "https://python.org/news",
            "content": "Python 3.14 is now available.",
        },
        {
            "title": "Python Guide",
            "url": "https://realpython.com",
            "content": "Learn Python basics.",
        },
    ]
}

EMPTY_RESPONSE = {"results": []}


@pytest.fixture
def registry() -> ToolRegistry:
    reg = ToolRegistry()
    register_web_tools(reg)
    return reg


class TestWebToolRegistration:
    def test_tool_registered(self, registry: ToolRegistry):
        assert "web_search" in registry.names

    def test_schema_has_required_query(self, registry: ToolRegistry):
        tool = registry.get("web_search")
        assert tool is not None
        assert "query" in tool.parameters["properties"]
        assert "query" in tool.parameters["required"]

    def test_placeholder_returns_async_prefix(self, registry: ToolRegistry):
        result = registry.execute("web_search", {"query": "test"})
        assert result.startswith("ASYNC_TOOL:")

    def test_openrouter_schema(self, registry: ToolRegistry):
        schema = registry.to_openrouter_schema()
        assert len(schema) == 1
        assert schema[0]["function"]["name"] == "web_search"


class TestTavilySearchClient:
    @pytest.fixture
    def client(self) -> TavilySearchClient:
        return TavilySearchClient(api_key="test-key")

    async def test_search_returns_formatted_results(self, client: TavilySearchClient):
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = TAVILY_RESPONSE
        mock_response.raise_for_status = lambda: None

        with patch.object(client._client, "post", return_value=mock_response):
            result = await client.search("python 3.14")

        assert "Python 3.14 Released" in result
        assert "https://python.org/news" in result
        assert "Python Guide" in result
        assert "Web results for 'python 3.14':" in result

    async def test_search_no_results(self, client: TavilySearchClient):
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = EMPTY_RESPONSE
        mock_response.raise_for_status = lambda: None

        with patch.object(client._client, "post", return_value=mock_response):
            result = await client.search("xyznonexistent123")

        assert "No web results found" in result

    async def test_search_http_error_raises(self, client: TavilySearchClient):
        with (
            patch.object(
                client._client,
                "post",
                side_effect=httpx.HTTPStatusError(
                    "429", request=httpx.Request("POST", "https://api.tavily.com"), response=httpx.Response(429)
                ),
            ),
            pytest.raises(WebSearchError, match="Tavily Search request failed"),
        ):
            await client.search("test")

    async def test_search_passes_correct_payload(self, client: TavilySearchClient):
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = EMPTY_RESPONSE
        mock_response.raise_for_status = lambda: None

        with patch.object(client._client, "post", return_value=mock_response) as mock_post:
            await client.search("bitcoin price", max_results=3)

        mock_post.assert_called_once_with(
            "https://api.tavily.com/search",
            json={
                "api_key": "test-key",
                "query": "bitcoin price",
                "max_results": 3,
                "search_depth": "basic",
            },
        )

    async def test_close(self, client: TavilySearchClient):
        with patch.object(client._client, "aclose", new_callable=AsyncMock) as mock_close:
            await client.close()
        mock_close.assert_called_once()
