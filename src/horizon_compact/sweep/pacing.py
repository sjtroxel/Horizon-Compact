"""The rate limiter and the backoff (Phase 1 IMPLEMENTATION doc section 6.4), with an injectable clock and
sleep.

At most one call start every ``60 / (quota x pace_fraction)`` seconds per model, leaving headroom for
development calls on the same account-wide quota. Backoff on an ``api_error`` is ``min(64, 4 x 2^k)``
seconds with full jitter, k counting consecutive ``api_error`` results for the run.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable

BACKOFF_BASE_SECONDS = 4
BACKOFF_CAP_SECONDS = 64


def interval_seconds(requests_per_minute: int, pace_fraction: float) -> float:
    return 60 / (requests_per_minute * pace_fraction)


def backoff_cap_seconds(k: int) -> float:
    return float(min(BACKOFF_CAP_SECONDS, BACKOFF_BASE_SECONDS * 2**k))


def backoff_seconds(k: int, rng: random.Random) -> float:
    """Full jitter: uniform between zero and the cap, so concurrent retries do not align."""
    return rng.uniform(0, backoff_cap_seconds(k))


class Pacer:
    def __init__(
        self,
        requests_per_minute: int,
        pace_fraction: float,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.interval = interval_seconds(requests_per_minute, pace_fraction)
        self._monotonic = monotonic
        self._sleep = sleep
        self._last_start: float | None = None

    def wait(self) -> None:
        """Block until a call may start, then mark it started."""
        if self._last_start is not None:
            remaining = self._last_start + self.interval - self._monotonic()
            if remaining > 0:
                self._sleep(remaining)
        self._last_start = self._monotonic()
