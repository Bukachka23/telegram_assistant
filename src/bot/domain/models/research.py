from dataclasses import dataclass, field


@dataclass
class ResearchState:
    """Mutable state for a single deep research session."""

    query: str
    max_cycles: int
    cycle: int = 0
    scratchpad: list[str] = field(default_factory=list)
    cycle_summaries: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class JudgeDecision:
    """Structured decision returned by the judge step."""

    should_stop: bool
    reason: str
