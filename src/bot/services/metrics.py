"""Metrics aggregation and /stats formatting."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bot.infrastructure.storage.metrics_storage import MetricsStore

_TOKENS_K_THRESHOLD = 1000


class MetricsService:
    """Aggregates stored metrics and formats them for display."""

    def __init__(self, store: MetricsStore) -> None:
        self._store = store

    async def build_stats(self, days: int = 7) -> str:
        """Build the /stats output text."""
        rows = await self._store.query(days=days)
        if not rows:
            return self._empty_message(days)

        total_requests = sum(r["requests"] for r in rows)
        header = f"📊 **Stats ({self._window_label(days)})** — {total_requests} requests\n"

        model_sections = [self._format_model(r) for r in rows]

        tool_names = await self._store.query_tool_names(days=days)
        tool_section = self._format_tools(tool_names)

        parts = [header, *model_sections]
        if tool_section:
            parts.append(tool_section)
        return "\n".join(parts)

    @staticmethod
    def _window_label(days: int) -> str:
        if days == 0:
            return "all time"
        if days == 1:
            return "today"
        return f"last {days} days"

    @staticmethod
    def _empty_message(days: int) -> str:
        if days == 0:
            return "📊 No requests recorded yet."
        if days == 1:
            return "📊 No requests recorded today."
        return f"📊 No requests recorded in the last {days} days."

    @classmethod
    def _format_model(cls, row: Any) -> str:
        """Format a single model's aggregated stats."""
        model = row["model"]
        requests = row["requests"]
        avg_in = cls._format_tokens(int(row["avg_tokens_in"]))
        avg_out = cls._format_tokens(int(row["avg_tokens_out"]))
        latency = cls._format_latency_ms(row["avg_latency_ms"])
        ttfb = cls._format_latency_ms(row["avg_ttfb_ms"])
        cost = row["total_cost"]
        errors = int(row["error_count"])

        cost_text = f"${cost:.2f}" if cost is not None else "n/a"
        error_pct = f" ({errors / requests * 100:.1f}%)" if errors and requests else ""

        return (
            f"\n🤖 **{model}** — {requests} req\n"
            f"  📝 Tokens: {avg_in} in / {avg_out} out avg\n"
            f"  ⏱ Latency: {latency} avg · TTFB {ttfb}\n"
            f"  💰 Cost: {cost_text}\n"
            f"  ❌ Errors: {errors}{error_pct}"
        )

    @staticmethod
    def _format_tokens(count: int) -> str:
        """Format token count: 500 → '500', 1200 → '1.2K'."""
        if count < _TOKENS_K_THRESHOLD:
            return str(count)
        return f"{count / 1000:.1f}K"

    @staticmethod
    def _format_latency_ms(ms: float) -> str:
        """Format milliseconds as seconds: 3200 → '3.2s'."""
        return f"{ms / 1000:.1f}s"

    @staticmethod
    def _format_tools(tool_names_list: list[str]) -> str:
        """Count tool usage across all rows and format."""
        if not tool_names_list:
            return ""
        counter: Counter[str] = Counter()
        for names in tool_names_list:
            for name in names.split(","):
                stripped = name.strip()
                if stripped:
                    counter[stripped] += 1
        if not counter:
            return ""
        parts = [f"{name} ×{count}" for name, count in counter.most_common()]
        return f"\n🔧 Tools: {' · '.join(parts)}"
