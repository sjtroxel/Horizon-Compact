"""The scaling factor, the rounding and the pay-per-head check (IMPLEMENTATION §4.8; protocol §12.6).

**The draw.** One factor per case, drawn log-uniformly from [0.6, 0.9] union [1.1, 1.6], the two pieces
weighted by their log-lengths (ln 1.5 and ln(16/11)), from a seed made by ``secrets`` and never chosen. The
seed is recorded in ``build.json`` so the draw can be re-run, and the factor is never redrawn.

**The rounding.** Dollars to three significant digits (half up). Headcounts to the nearest 5, except that a
scaled headcount under 100 is stated as "fewer than 100", not rounded.

**The check.** Wherever a total pay figure and a headcount are both stated, pay per head after rounding stays
within 3.5% of its unscaled value. A failure is a reported deviation for him to decide; the factor is not
redrawn. (Rounding a headcount of 100 or more down by 2.5% raises pay per head by 2.6%, three significant
digits move a dollar figure by at most 0.5%: together at most 3.1%, so a correct build always passes.)
"""

from __future__ import annotations

import math
import random
import secrets
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

LOW_PIECE = (0.6, 0.9)
HIGH_PIECE = (1.1, 1.6)
PAY_PER_HEAD_BAND = Decimal("0.035")
SMALL_GROUP = 100
FEWER_THAN = "fewer than 100"


def new_seed() -> int:
    """A seed nobody chose."""
    return secrets.randbits(64)


def draw_factor(seed: int) -> float:
    """The case's scaling factor for ``seed``: log-uniform over the two pieces, weighted by log-length."""
    low = math.log(LOW_PIECE[1]) - math.log(LOW_PIECE[0])
    high = math.log(HIGH_PIECE[1]) - math.log(HIGH_PIECE[0])
    point = random.Random(seed).random() * (low + high)
    if point < low:
        return math.exp(math.log(LOW_PIECE[0]) + point)
    return math.exp(math.log(HIGH_PIECE[0]) + (point - low))


def round_significant(value: Decimal, digits: int = 3) -> Decimal:
    """``value`` to ``digits`` significant digits, half up."""
    if value == 0:
        return Decimal(0)
    exponent = value.adjusted() - (digits - 1)
    rounded = value.quantize(Decimal(1).scaleb(exponent), rounding=ROUND_HALF_UP)
    if rounded.adjusted() > value.adjusted():  # 999.6 rounded up to 1000: re-round at the new size
        rounded = rounded.quantize(
            Decimal(1).scaleb(rounded.adjusted() - (digits - 1)), rounding=ROUND_HALF_UP
        )
    return rounded


def format_number(value: Decimal) -> str:
    """A number with thousands separators and only the decimals it has."""
    exponent = value.as_tuple().exponent
    assert isinstance(exponent, int)
    if exponent >= 0:
        return f"{int(value):,}"
    return f"{value:,.{-exponent}f}"


def scale_dollars(amount: Decimal, factor: float) -> Decimal:
    """``amount`` (in whatever unit it is stated) times the factor, to three significant digits."""
    return round_significant(amount * Decimal(repr(factor)))


@dataclass(frozen=True)
class ScaledHeads:
    text: str  # "1,725" or "fewer than 100"
    value: int | None  # the rounded headcount; None when stated as "fewer than 100"


def scale_heads(heads: int, factor: float) -> ScaledHeads:
    scaled = Decimal(heads) * Decimal(repr(factor))
    if scaled < SMALL_GROUP:
        return ScaledHeads(text=FEWER_THAN, value=None)
    nearest_five = int((scaled / 5).to_integral_value(rounding=ROUND_HALF_UP)) * 5
    return ScaledHeads(text=f"{nearest_five:,}", value=nearest_five)


def scale_total_heads(heads: int, factor: float) -> int:
    """An S3 case's total headcount, scaled to the nearest 5 and stated as a number even under 100
    (search-half doc §4.6.5 step 1 item 2). From 100 up it is ``scale_heads``'s; below, ``scale_heads`` says
    "fewer than 100" and this does not."""
    scaled = Decimal(heads) * Decimal(repr(factor))
    return int((scaled / 5).to_integral_value(rounding=ROUND_HALF_UP)) * 5


@dataclass(frozen=True)
class PayFigure:
    """A total pay figure and a headcount stated on one line, before and after scaling."""

    line: int
    pay_before: Decimal
    pay_after: Decimal
    heads_before: int
    heads_after: int | None  # None: stated as "fewer than 100"


@dataclass(frozen=True)
class PayCheck:
    line: int
    per_head_before: Decimal | None
    per_head_after: Decimal | None
    change: Decimal | None
    passed: bool
    note: str

    def record(self) -> dict[str, object]:
        return {
            "line": self.line,
            "per_head_before": str(self.per_head_before)
            if self.per_head_before is not None
            else None,
            "per_head_after": str(self.per_head_after) if self.per_head_after is not None else None,
            "change": str(self.change) if self.change is not None else None,
            "passed": self.passed,
            "note": self.note,
        }


def check_pay_per_head(figure: PayFigure) -> PayCheck:
    """Pay per head after rounding within 3.5% of its unscaled value. "Fewer than 100" cannot be checked."""
    if figure.heads_after is None:
        return PayCheck(
            figure.line, None, None, None, True, "headcount stated as fewer than 100; not checked"
        )
    before = figure.pay_before / Decimal(figure.heads_before)
    after = figure.pay_after / Decimal(figure.heads_after)
    change = abs(after / before - 1)
    passed = change <= PAY_PER_HEAD_BAND
    note = "" if passed else "pay per head moved more than 3.5%: a reported deviation, not a redraw"
    return PayCheck(figure.line, before, after, change, passed, note)
