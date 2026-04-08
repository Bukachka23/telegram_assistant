"""Tests for multi-source web search router."""

import pytest

from bot.services.web_search_router import WebSearchRouter


class FakeTavily:
    async def search(self, query: str, *, max_results: int = 5) -> str:
        return f"Tavily: {query} ({max_results})"

    async def close(self) -> None:
        pass


class FakeGitHub:
    async def search(self, query: str, *, max_results: int = 5) -> str:
        return f"GitHub: {query} ({max_results})"

    async def close(self) -> None:
        pass


class FakeHuggingFace:
    async def search(self, query: str, *, max_results: int = 5) -> str:
        return f"HuggingFace: {query} ({max_results})"

    async def close(self) -> None:
        pass


class FakeStackOverflow:
    async def search(self, query: str, *, max_results: int = 5) -> str:
        return f"StackOverflow: {query} ({max_results})"

    async def close(self) -> None:
        pass


class FakeArxiv:
    async def search(self, query: str, *, max_results: int = 5) -> str:
        return f"arXiv: {query} ({max_results})"

    async def close(self) -> None:
        pass


class FakeWikipedia:
    async def search(self, query: str, *, max_results: int = 5) -> str:
        return f"Wikipedia: {query} ({max_results})"

    async def close(self) -> None:
        pass


@pytest.fixture
def router() -> WebSearchRouter:
    return WebSearchRouter(
        tavily=FakeTavily(),
        github=FakeGitHub(),
        huggingface=FakeHuggingFace(),
        stackoverflow=FakeStackOverflow(),
        arxiv=FakeArxiv(),
        wikipedia=FakeWikipedia(),
    )


class TestExplicitSource:
    @pytest.mark.asyncio
    async def test_explicit_web_uses_tavily(self, router):
        result = await router.search("python async", source="web")
        assert result.startswith("Tavily:")

    @pytest.mark.asyncio
    async def test_explicit_github(self, router):
        result = await router.search("fastapi", source="github")
        assert result.startswith("GitHub:")

    @pytest.mark.asyncio
    async def test_explicit_huggingface(self, router):
        result = await router.search("llama 3", source="huggingface")
        assert result.startswith("HuggingFace:")

    @pytest.mark.asyncio
    async def test_max_results_forwarded(self, router):
        result = await router.search("test", source="web", max_results=10)
        assert "(10)" in result


class TestAutoRouting:
    @pytest.mark.asyncio
    async def test_github_keyword_routes_to_github(self, router):
        result = await router.search("best open source LLM frameworks")
        assert result.startswith("GitHub:")

    @pytest.mark.asyncio
    async def test_repo_keyword_routes_to_github(self, router):
        result = await router.search("aiogram repo examples")
        assert result.startswith("GitHub:")

    @pytest.mark.asyncio
    async def test_huggingface_keyword_routes_to_hf(self, router):
        result = await router.search("huggingface text generation models")
        assert result.startswith("HuggingFace:")

    @pytest.mark.asyncio
    async def test_gguf_keyword_routes_to_hf(self, router):
        result = await router.search("llama 3 gguf quantized")
        assert result.startswith("HuggingFace:")

    @pytest.mark.asyncio
    async def test_error_keyword_routes_to_stackoverflow(self, router):
        result = await router.search("TypeError cannot unpack non-iterable NoneType")
        assert result.startswith("StackOverflow:")

    @pytest.mark.asyncio
    async def test_how_to_keyword_routes_to_stackoverflow(self, router):
        result = await router.search("how to parse JSON in Python")
        assert result.startswith("StackOverflow:")

    @pytest.mark.asyncio
    async def test_paper_keyword_routes_to_arxiv(self, router):
        result = await router.search("attention is all you need paper")
        assert result.startswith("arXiv:")

    @pytest.mark.asyncio
    async def test_research_paper_keyword_routes_to_arxiv(self, router):
        result = await router.search("latest research paper on RLHF")
        assert result.startswith("arXiv:")

    @pytest.mark.asyncio
    async def test_what_is_keyword_routes_to_wikipedia(self, router):
        result = await router.search("what is transformer architecture")
        assert result.startswith("Wikipedia:")

    @pytest.mark.asyncio
    async def test_wiki_keyword_routes_to_wikipedia(self, router):
        result = await router.search("wiki neural networks")
        assert result.startswith("Wikipedia:")

    @pytest.mark.asyncio
    async def test_generic_query_routes_to_tavily(self, router):
        result = await router.search("weather in Kyiv tomorrow")
        assert result.startswith("Tavily:")


class TestMissingClients:
    @pytest.mark.asyncio
    async def test_missing_tavily_returns_message(self):
        router = WebSearchRouter(tavily=None, github=FakeGitHub())
        result = await router.search("test query", source="web")
        assert "not configured" in result

    @pytest.mark.asyncio
    async def test_missing_github_returns_message(self):
        router = WebSearchRouter(tavily=FakeTavily(), github=None)
        result = await router.search("test", source="github")
        assert "not available" in result

    @pytest.mark.asyncio
    async def test_missing_huggingface_returns_message(self):
        router = WebSearchRouter(tavily=FakeTavily(), huggingface=None)
        result = await router.search("llama", source="huggingface")
        assert "not available" in result

    @pytest.mark.asyncio
    async def test_missing_stackoverflow_returns_message(self):
        router = WebSearchRouter(tavily=FakeTavily(), stackoverflow=None)
        result = await router.search("test", source="stackoverflow")
        assert "not available" in result

    @pytest.mark.asyncio
    async def test_missing_arxiv_returns_message(self):
        router = WebSearchRouter(tavily=FakeTavily(), arxiv=None)
        result = await router.search("test", source="arxiv")
        assert "not available" in result

    @pytest.mark.asyncio
    async def test_missing_wikipedia_returns_message(self):
        router = WebSearchRouter(tavily=FakeTavily(), wikipedia=None)
        result = await router.search("test", source="wikipedia")
        assert "not available" in result
