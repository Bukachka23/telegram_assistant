
# Arxiv
ARXIV_API = "http://export.arxiv.org/api/query"
ARXIV_KEYWORDS = frozenset([
    "arxiv", "paper", "research paper", "study", "journal",
    "preprint", "publication", "academic",
])

# Github
GITHUB_API_BASE = "https://api.github.com"
GITHUB_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "telegram-assistant-bot",
}
GITHUB_KEYWORDS = frozenset([
    "github", "github.com", "repo", "repository", "open source",
    "open-source", "star", "fork",
])

# HF
HF_API_BASE = "https://huggingface.co/api"
HUGGINGFACE_KEYWORDS = frozenset([
    "huggingface", "hugging face", "hf model", "hf models",
    "transformers model", "gguf", "safetensors",
])

# Reddit
REDDIT_API_BASE = "https://www.reddit.com"
REDDIT_USER_AGENT = (
    "TelegramAssistantBot/1.0 "
    "(https://github.com/telegram-assistant; bot@telegram-assistant.local) "
    "python-httpx"
)
REDDIT_KEYWORDS = frozenset([
    "reddit", "r/", "subreddit", "upvote", "downvote", "ama", "thread",
])

# Stackoverflow
STACKOVERFLOW_API = "https://api.stackexchange.com/2.3"
STACKOVERFLOW_KEYWORDS = frozenset([
    "stackoverflow", "stack overflow", "how to", "error",
    "exception", "traceback", "debug", "fix bug",
])

# Tavily
TAVILY_SEARCH_URL = "https://api.tavily.com/search"

# Wiki
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_USER_AGENT = (
    "TelegramAssistantBot/1.0 "
    "(https://github.com/telegram-assistant; bot@telegram-assistant.local) "
    "python-httpx"
)
WIKIPEDIA_KEYWORDS = frozenset([
    "wikipedia", "wiki", "definition", "what is",
    "who is", "history of", "meaning of",
])
