"""The scaling draw, the rounding and the pay-per-head check (Phase 5 code half, build step 5, §4.8)."""

from __future__ import annotations

import math
import secrets
from decimal import Decimal

import pytest

from horizon_compact.casebuild.scale import (
    FEWER_THAN,
    PayFigure,
    check_pay_per_head,
    draw_factor,
    format_number,
    new_seed,
    round_significant,
    scale_dollars,
    scale_heads,
)

SEEDS = range(20_000)
LOW_LENGTH = math.log(0.9) - math.log(0.6)  # ln 1.5
HIGH_LENGTH = math.log(1.6) - math.log(1.1)  # ln(16/11)


def test_every_draw_is_in_one_of_the_two_pieces_and_never_in_the_gap() -> None:
    factors = [draw_factor(seed) for seed in SEEDS]
    assert all(0.6 <= f <= 0.9 or 1.1 <= f <= 1.6 for f in factors)
    assert not any(0.9 < f < 1.1 for f in factors)
    assert min(factors) < 0.62 and max(factors) > 1.58  # both ends are reached


def test_the_two_pieces_are_weighted_by_their_log_lengths() -> None:
    low = sum(1 for seed in SEEDS if draw_factor(seed) < 1)
    expected = LOW_LENGTH / (LOW_LENGTH + HIGH_LENGTH)  # about 0.520, not one half
    assert low / len(SEEDS) == pytest.approx(expected, abs=0.015)
    assert abs(low / len(SEEDS) - 0.5) > 0.01  # an equal-weight draw would fail this


def test_within_a_piece_the_draw_is_log_uniform() -> None:
    lows = sorted(f for f in (draw_factor(s) for s in SEEDS) if f < 1)
    highs = sorted(f for f in (draw_factor(s) for s in SEEDS) if f > 1)
    assert lows[len(lows) // 2] == pytest.approx(math.sqrt(0.6 * 0.9), abs=0.01)
    assert highs[len(highs) // 2] == pytest.approx(math.sqrt(1.1 * 1.6), abs=0.015)


def test_a_seed_gives_one_factor_and_new_seeds_come_from_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert draw_factor(12345) == draw_factor(12345)
    assert draw_factor(1) != draw_factor(2)
    monkeypatch.setattr(secrets, "randbits", lambda bits: 42)
    assert new_seed() == 42


def test_new_seeds_differ() -> None:
    assert len({new_seed() for _ in range(20)}) == 20


@pytest.mark.parametrize(
    ("value", "rounded", "text"),
    [
        ("15.618", "15.6", "15.6"),
        ("1234.5", "1.23E+3", "1,230"),
        ("999.6", "1.00E+3", "1,000"),
        ("0.04567", "0.0457", "0.0457"),
        ("76787.5", "7.68E+4", "76,800"),
        ("100", "100", "100"),
        ("0", "0", "0"),
        ("1.005", "1.01", "1.01"),
    ],
)
def test_dollars_to_three_significant_digits_half_up(value: str, rounded: str, text: str) -> None:
    result = round_significant(Decimal(value))
    assert result == Decimal(rounded)
    assert format_number(result) == text


def test_scale_dollars_multiplies_in_the_stated_unit_then_rounds() -> None:
    assert scale_dollars(Decimal("11.4"), 1.37) == Decimal("15.6")
    assert scale_dollars(Decimal("56050"), 1.37) == Decimal("7.68E+4")


@pytest.mark.parametrize(
    ("heads", "factor", "text", "value"),
    [
        (1240, 1.2, "1,490", 1490),  # 1,488 to the nearest 5
        (100, 1.0, "100", 100),
        (80, 1.2, FEWER_THAN, None),  # 96 scaled: under 100, not rounded
        (65, 1.5, FEWER_THAN, None),  # 97.5 scaled: still under 100
        (100, 0.99, FEWER_THAN, None),
        (85, 1.2, "100", 100),  # 102.0 scaled
        (1000, 1.025, "1,025", 1025),
        (3, 1.1, FEWER_THAN, None),
    ],
)
def test_headcounts_to_the_nearest_five_and_fewer_than_100_below(
    heads: int, factor: float, text: str, value: int | None
) -> None:
    scaled = scale_heads(heads, factor)
    assert (scaled.text, scaled.value) == (text, value)


def test_a_small_group_is_never_rounded_to_zero() -> None:
    assert scale_heads(2, 0.6).text == FEWER_THAN  # 12 people would have rounded to 10 and 2 to 0


def test_pay_per_head_passes_when_pay_and_heads_scaled_together() -> None:
    check = check_pay_per_head(
        PayFigure(1, Decimal("70000000"), Decimal("84000000"), 1240, 1490)  # 1.2x, rounded
    )
    assert check.passed
    assert check.change is not None and check.change < Decimal("0.01")


def test_pay_per_head_fails_when_pay_and_heads_were_scaled_apart() -> None:
    check = check_pay_per_head(PayFigure(1, Decimal("70000000"), Decimal("70000000"), 1240, 1490))
    assert not check.passed
    assert "3.5%" in check.note


def test_the_band_is_three_and_a_half_percent_not_three() -> None:
    """The worst correct build moves pay per head about 3.01%: a 3% band would fail it (the Opus review)."""
    factor = 1.02499
    heads = scale_heads(100, factor)  # 102.499 rounds down to 100
    pay_after = scale_dollars(Decimal(980_500), factor)  # 1,005,003 rounds up to 1,010,000
    assert heads.value == 100 and pay_after == Decimal("1.01E+6")
    check = check_pay_per_head(PayFigure(1, Decimal(980_500), pay_after, 100, heads.value))
    assert check.change is not None and Decimal("0.030") < check.change < Decimal("0.035")
    assert check.passed


def test_a_headcount_stated_as_fewer_than_100_is_not_checked_and_says_so() -> None:
    check = check_pay_per_head(PayFigure(3, Decimal("1000000"), Decimal("1200000"), 80, None))
    assert check.passed and check.per_head_after is None
    assert "not checked" in check.note


def test_a_correct_build_never_fails_the_check() -> None:
    """The doc's claim, tried through the real draw, rounding and scaling over many totals and headcounts."""
    failures = []
    for seed in range(3000):
        factor = draw_factor(seed)
        heads = 100 + (seed * 37) % 40_000
        pay = Decimal(1_000_000 + (seed * 7919) % 900_000_000)
        scaled_heads = scale_heads(heads, factor)
        if scaled_heads.value is None:
            continue
        scaled_pay = scale_dollars(pay, factor)
        check = check_pay_per_head(PayFigure(1, pay, scaled_pay, heads, scaled_heads.value))
        if not check.passed:
            failures.append((seed, check.change))
    assert failures == []
