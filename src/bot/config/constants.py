from pathlib import Path
from typing import Any

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

# Search Config
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

# Search Configs
REDDIT_CACHE_TTL_SECONDS: float = 300.0
REDDIT_RATE_LIMIT_STATUS: int = 429
VALID_SOURCES = ("auto", "web", "github", "huggingface", "stackoverflow", "arxiv", "wikipedia", "reddit")
