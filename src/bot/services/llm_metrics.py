import logging
import time

from bot.domain.models import RequestMetric, TokenUsage
from bot.infrastructure.storage.metrics_storage import MetricsStore

logger = logging.getLogger(__name__)


class LLMRequestMetricsEmitter:
    def __init__(self, store: MetricsStore | None) -> None:
        self._store = store

    async def emit(
        self,
        *,
        model: str,
        t_start: float,
        t_first_token: float | None,
        usage: TokenUsage | None,
        tool_names: list[str],
        error_text: str,
    ) -> None:
        """Record a request metric. Fire-and-forget — never breaks a response."""
        if self._store is None:
            return
        try:
            t_end = time.monotonic()
            metric = RequestMetric(
                model=model,
                tokens_in=usage.prompt_tokens if usage else 0,
                tokens_out=usage.completion_tokens if usage else 0,
                cost_usd=usage.cost if usage else None,
                latency_ms=int((t_end - t_start) * 1000),
                ttfb_ms=int((t_first_token - t_start) * 1000) if t_first_token else 0,
                tool_names=",".join(tool_names),
                is_error=bool(error_text),
                error_text=error_text,
            )
            await self._store.record(metric)
        except Exception:
            logger.warning("Failed to emit request metric", exc_info=True)
