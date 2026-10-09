"""Cost of an attempt and the running cap (Phase 1 IMPLEMENTATION doc section 6.5, planning/09 A3).

``spend`` is written for Anthropic-style usage, where ``inputTokens`` excludes cache reads and writes, so
the four counts are priced separately. Whether Converse reports it that way is checked on the first Sonnet
attempt with a cache hit (section 19); a test is added the day it is seen.
"""

from __future__ import annotations

from horizon_compact.model_config import Prices
from horizon_compact.providers.base import ToolSpec, Usage

# Phase 0.5 measured 716 tokens of tool overhead for a short prompt.
TOOL_OVERHEAD_TOKENS = 700
CHARS_PER_TOKEN = 3.5
DEVELOPMENT_CAP_USD = 5.0


def attempt_cost_usd(usage: Usage, prices: Prices) -> float:
    total = (
        usage.input_tokens * prices.input
        + usage.output_tokens * prices.output
        + usage.cache_read_tokens * prices.cache_read
        + usage.cache_write_tokens * prices.cache_write_5m
    )
    return round(total / 1_000_000, 6)


def estimate_input_tokens(system: str, user: str, tool: ToolSpec) -> int:
    """Rendered characters over 3.5, plus the tool overhead; deliberately generous, with no caching
    assumed."""
    chars = len(system) + len(user) + len(tool.description) + len(str(dict(tool.input_schema)))
    return round(chars / CHARS_PER_TOKEN) + TOOL_OVERHEAD_TOKENS


def worst_case_attempt_usd(input_tokens: int, max_tokens: int, prices: Prices) -> float:
    """One attempt at full price: the estimated input at no caching, and the whole output allowance."""
    return round((input_tokens * prices.input + max_tokens * prices.output) / 1_000_000, 6)


class SpendCap:
    """A per-sweep cap, across sessions: ``spent_usd`` starts from what the sweep's stored attempts already
    cost."""

    def __init__(self, cap_usd: float, spent_usd: float = 0.0) -> None:
        self.cap_usd = cap_usd
        self.spent_usd = spent_usd

    def allows(self, worst_case_usd: float) -> bool:
        return self.spent_usd + worst_case_usd <= self.cap_usd

    def record(self, cost_usd: float) -> None:
        self.spent_usd = round(self.spent_usd + cost_usd, 6)
