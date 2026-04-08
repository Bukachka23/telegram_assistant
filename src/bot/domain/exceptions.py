class BotError(Exception):
    """Base exception for all bot errors."""


class VaultError(BotError):
    """Raised when vault operations fail."""


class LLMError(BotError):
    """Raised when LLM API calls fail."""


class ChannelError(BotError):
    """Raised when channel operations fail."""


class WebSearchError(BotError):
    """Raised when web search API calls fail."""


class TelegraphError(BotError):
    """Raised when Telegraph API operations fail."""
