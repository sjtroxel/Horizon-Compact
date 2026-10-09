"""Pacing, backoff and spend (Phase 1 IMPLEMENTATION doc sections 6.4 and 6.5)."""

from __future__ import annotations

import random
from itertools import pairwise

import pytest

from horizon_compact.model_config import Prices
from horizon_compact.providers.base import ToolSpec, Usage
from horizon_compact.sweep.pacing import (
    Pacer,
    backoff_cap_seconds,
    backoff_seconds,
    interval_seconds,
)
from horizon_compact.sweep.spend import (
    SpendCap,
    attempt_cost_usd,
    estimate_input_tokens,
    worst_case_attempt_usd,
)
from sweep_helpers import FakeClock

SONNET = Prices(input=3.30, output=16.50, cache_read=0.33, cache_write_5m=4.125)


def test_sonnet_46_is_paced_to_one_start_every_7_5_seconds() -> None:
    assert interval_seconds(10, 0.8) == pytest.approx(7.5)


def test_call_starts_are_never_closer_than_the_interval() -> None:
    clock = FakeClock()
    pacer = Pacer(10, 0.8, clock.monotonic, clock.sleep)
    starts = []
    for _ in range(5):
        pacer.wait()
        starts.append(clock.monotonic())
        clock.t += 1.0  # the call itself takes a second
    gaps = [b - a for a, b in pairwise(starts)]
    assert all(gap >= 7.5 - 1e-9 for gap in gaps)
    assert clock.sleeps[0] == pytest.approx(6.5)  # 7.5 minus the 1s the call already took


def test_the_first_call_never_waits() -> None:
    clock = FakeClock()
    Pacer(10, 0.8, clock.monotonic, clock.sleep).wait()
    assert clock.sleeps == []


def test_a_slow_call_means_no_extra_wait() -> None:
    clock = FakeClock()
    pacer = Pacer(10, 0.8, clock.monotonic, clock.sleep)
    pacer.wait()
    clock.t += 30.0
    pacer.wait()
    assert clock.sleeps == []


def test_the_backoff_cap_doubles_from_four_and_stops_at_sixty_four() -> None:
    assert [backoff_cap_seconds(k) for k in range(7)] == [4, 8, 16, 32, 64, 64, 64]


def test_the_backoff_is_full_jitter_inside_its_cap() -> None:
    rng = random.Random(0)
    for k in range(8):
        draws = [backoff_seconds(k, rng) for _ in range(200)]
        assert all(0 <= d <= backoff_cap_seconds(k) for d in draws)
        assert max(draws) > backoff_cap_seconds(k) * 0.8  # it really uses the range
        assert min(draws) < backoff_cap_seconds(k) * 0.2


def test_cost_prices_all_four_token_counts_per_million() -> None:
    usage = Usage(
        input_tokens=1000, output_tokens=500, cache_read_tokens=2000, cache_write_tokens=1000
    )
    expected = (1000 * 3.30 + 500 * 16.50 + 2000 * 0.33 + 1000 * 4.125) / 1_000_000
    assert attempt_cost_usd(usage, SONNET) == pytest.approx(expected, abs=1e-6)
    assert attempt_cost_usd(Usage(), SONNET) == 0


def test_the_worst_case_is_input_at_full_price_plus_the_whole_output_allowance() -> None:
    assert worst_case_attempt_usd(2000, 2048, SONNET) == pytest.approx(
        (2000 * 3.30 + 2048 * 16.50) / 1e6, abs=1e-6
    )


def test_the_input_estimate_is_characters_over_3_5_plus_seven_hundred() -> None:
    tool = ToolSpec("t", "", {})
    assert estimate_input_tokens("a" * 350, "b" * 350, tool) == round((700 + len("{}")) / 3.5) + 700


def test_the_running_cap_stops_before_the_attempt_that_would_pass_it() -> None:
    cap = SpendCap(1.0, spent_usd=0.90)
    assert cap.allows(0.10)
    assert not cap.allows(0.11)
    cap.record(0.05)
    assert cap.spent_usd == pytest.approx(0.95)
    assert not cap.allows(0.10)
