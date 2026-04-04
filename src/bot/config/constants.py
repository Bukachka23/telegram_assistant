from pathlib import Path
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

# System
MAX_ATTEMPTS: int = 3
BASE_DELAY_SECONDS: float = 1.0
BACKOFF_MULTIPLIER: float = 2.0

# Messages
LIMIT_MESSAGES: int = 20
LIMIT_CHANNELS: int = 20
DAYS: int = 7

# Channel configs
CHANNEL_REQUEST_TIMEOUT_SECONDS = 15.0
CHANNEL_REQUEST_MAX_ATTEMPTS = 3
CHANNEL_REQUEST_BASE_DELAY_SECONDS = 0.5
CHANNEL_MAX_LENGTH_MESSAGE: int = 300

# Conversation Manager
SESSION_TIMEOUT_MINUTES: int = 30
MAX_HISTORY: int = 50

# LLM Configs
MAX_TOOL_ROUNDS = 10
ASYNC_TOOL_PREFIX = "ASYNC_TOOL:"
MAX_TOKENS: int = 4096
TEMPERATURE: float = 0.7
DEEP_RESEARCH_MAX_CYCLES: int = 3

# Vault Configs
MAX_RESULTS: int = 10
CONTEXT: int = 200

# Openrouter
BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_TEMPERATURE: float = 0.7
OPENROUTER_MAX_TOKENS: int = 4096
TIMEOUT: float = 120.0

# Commands Config
MODEL_COMMAND_MIN_PARTS = 2
MONITOR_COMMAND_MIN_PARTS = 3
VAULT_COMMAND_MIN_PARTS = 3

# Telegram Messages
MAX_TG_TEXT = 4096

# Path Configs
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CWD = Path.cwd()

# Brave Search Config
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
DEFAULT_MAX_RESULTS = 5
REQUEST_TIMEOUT = 15.0

# Deep Research
SUMMARY_LIMIT = 220
JUDGE_MAX_TOKENS = 120
SUMMARY_PREVIEW_LIMIT = 1200

# Time
SECONDS_PER_MINUTE: int = 60

# Arxiv
MAX_ARXIV_AUTHORS: int = 4

# Scheduler Configs
TZ_OFFSET_HOURS: int = 0
TICK_SECONDS: float = 10.0
TIMEOUT_BACK_LOOP: float = 5.0
CRON_TYPES = frozenset({"cron", "once_cron"})
JOB = dict[str, Any]

# Github Configs
GITHUB_API_BASE = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "telegram-assistant-bot",
}
GITHUB_KEYWORDS = frozenset([
    "github", "github.com", "repo", "repository", "open source",
    "open-source", "star", "fork",
])

# HF Configs
HF_API_BASE = "https://huggingface.co/api"
HUGGINGFACE_KEYWORDS = frozenset([
    "huggingface", "hugging face", "hf model", "hf models",
    "transformers model", "gguf", "safetensors",
])

STACKOVERFLOW_KEYWORDS = frozenset([
    "stackoverflow", "stack overflow", "how to", "error",
    "exception", "traceback", "debug", "fix bug",
])

# Stack Overflow Configs
STACKOVERFLOW_API = "https://api.stackexchange.com/2.3"

# Arxiv Configs
ARXIV_API = "http://export.arxiv.org/api/query"
ARXIV_KEYWORDS = frozenset([
    "arxiv", "paper", "research paper", "study", "journal",
    "preprint", "publication", "academic",
])

# Reddit Configs
REDDIT_API_BASE = "https://www.reddit.com"
REDDIT_USER_AGENT = (
    "TelegramAssistantBot/1.0 "
    "(https://github.com/telegram-assistant; bot@telegram-assistant.local) "
    "python-httpx"
)
REDDIT_KEYWORDS = frozenset([
    "reddit", "r/", "subreddit", "upvote", "downvote", "ama", "thread",
])
REDDIT_CACHE_TTL_SECONDS: float = 300.0   # 5 min — Reddit allows ~100 req per 6 min
REDDIT_RATE_LIMIT_STATUS: int = 429

# Wikipedia Configs
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
# Wikipedia blocks generic UA strings (e.g. python-httpx/x.y). Per
# https://meta.wikimedia.org/wiki/User-Agent_policy the UA must identify
# the application and provide a contact / URL.
WIKIPEDIA_USER_AGENT = (
    "TelegramAssistantBot/1.0 "
    "(https://github.com/telegram-assistant; bot@telegram-assistant.local) "
    "python-httpx"
)
WIKIPEDIA_KEYWORDS = frozenset([
    "wikipedia", "wiki", "definition", "what is",
    "who is", "history of", "meaning of",
])

VALID_SOURCES = ("auto", "web", "github", "huggingface", "stackoverflow", "arxiv", "wikipedia", "reddit")


# Database queries
SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fact TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
USING fts5(fact, category, content=memories, content_rowid=id);

CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
    INSERT INTO memories_fts(rowid, fact, category)
    VALUES (new.id, new.fact, new.category);
END;

CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, fact, category)
    VALUES ('delete', old.id, old.fact, old.category);
END;

CREATE TABLE IF NOT EXISTS channel_monitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL UNIQUE,
    username TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL,
    keywords_json TEXT NOT NULL DEFAULT '[]',
    source_type TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_channel_monitors_owner_user_id
ON channel_monitors(owner_user_id);
"""
