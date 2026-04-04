from dataclasses import dataclass


@dataclass(frozen=True)
class RequestMetric:
    """A single user-message-level metric record."""

    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float | None
    latency_ms: int
    ttfb_ms: int
    tool_names: str  # comma-separated: "web_search,recall_memory"
    is_error: bool = False
    error_text: str = ""
