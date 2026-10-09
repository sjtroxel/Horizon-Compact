"""The repeat rule (Phase 3 IMPLEMENTATION doc section 12, `planning/07` section 8).

Input: a pilot's runs. Output, per scenario, and nothing else. It carries no mean, no difference and no
objective label, so computing the repeats cannot show which way any comparison leans (Phase 4 decision
1's concern); a test pins the field names and shows the output does not move when an objective's values
are shifted or relabelled.

**Shares (S1, S2):** the pooled standard deviation of the primary outcome over the scenario's cells (a
cell is one objective under one wording): the sum of squared deviations from each cell's mean, over the
sum of each cell's valid runs minus one, so a cell with one valid run adds nothing. Then two repeat
counts per cell, each the smallest ``n`` (at least 2, the fewest runs a cell's variance needs) for which:

- (a) power: 80% power to declare a split at 1.5 times the threshold,
  ``(t_n + 0.84) sd sqrt(2 / (W n)) <= 1.5 T``;
- (b) both verdicts reachable: the interval's half-width at most 0.8 times the threshold,
  ``t_n sd sqrt(2 / (W n)) <= 0.8 T``;

with ``W`` wordings (three), ``T`` the scenario's threshold and ``t_n`` the ``1 - ALPHA / 2`` quantile of
t on ``2 W (n - 1)`` degrees of freedom: the Welch interval's quantile when both objectives share one spread
(step 12, section 20b item 5; the rule was first written with the normal quantile, for the bootstrap). The
repeats are the larger of the two, clamped to [6, 20]. When the cap binds, the achieved precision is the
interval's half-width at 20 repeats, ``t_20 sd sqrt(2 / (W n))``: the same expression rule (b) inverts.

**Choice rates (S3, S4):** a pilot cannot measure them, so they go to the cap, 20, with the achieved
precision at true rates of 50% and 5% (Newcombe's interval on 60 runs a side with equal rates, so the
half-width is symmetric).

``0.84`` is the planning's number, taken as written (the 80th percentile of the normal is 0.8416).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from scipy.stats import t as t_distribution

from horizon_compact.analysis.intervals import ALPHA, newcombe_difference
from horizon_compact.analysis.outcomes import ScenarioOutcomes
from horizon_compact.analysis.records import RunRow
from horizon_compact.analysis.verdict import one_value

FLOOR = 6
CAP = 20
WORDINGS = 3  # the study's wordings: two development, one sealed (planning/07 section 8)
POWER_Z = 0.84  # 80% power, as the planning writes it
DESIGN_MULTIPLE = 1.5  # rule (a): the true difference the power is stated at, in thresholds
PRECISION_MULTIPLE = 0.8  # rule (b): the largest half-width, in thresholds
CHOICE_RATES = (0.5, 0.05)  # the rates the achieved precision is stated at (section 8)

_EPSILON = 1e-9  # a half-width within rounding error of its limit meets it
_SEARCH_LIMIT = 100_000  # far past any share's need: sd is at most 0.5 and T at least 0.10


class RepeatRuleError(Exception):
    """The repeats cannot be set from these runs. The message says why."""


@dataclass(frozen=True)
class ShareRepeats:
    """S1 or S2. ``achieved_half_width`` is set only when the cap binds; it is in share units."""

    scenario_id: str
    pooled_sd: float
    degrees_of_freedom: int
    n_power: int  # rule (a), rounded up
    n_both_reachable: int  # rule (b), rounded up
    repeats: int  # the larger, clamped to [FLOOR, CAP]
    cap_binds: bool
    achieved_half_width: float | None


@dataclass(frozen=True)
class ChoiceRepeats:
    """S3 or S4: the cap, and the half-width of the interval at it for true rates of 50% and 5%."""

    scenario_id: str
    repeats: int
    half_width_at_50: float
    half_width_at_5: float


def pooled_sd(cells: Sequence[Sequence[float]]) -> tuple[float, int]:
    """The pooled standard deviation and its degrees of freedom. A cell of one run adds neither."""
    squares = 0.0
    df = 0
    for cell in cells:
        if len(cell) < 2:
            continue
        centre = math.fsum(cell) / len(cell)
        squares += math.fsum((v - centre) ** 2 for v in cell)
        df += len(cell) - 1
    if df == 0:
        raise RepeatRuleError(
            "no cell has two valid runs, so there is no within-cell spread to pool; the pilot cannot set "
            "the repeats"
        )
    return math.sqrt(squares / df), df


def t_quantile(repeats: int, *, wordings: int = WORDINGS) -> float:
    """The family quantile of t on the degrees of freedom of ``repeats`` runs in each of ``wordings`` cells a
    side, both sides sharing one spread: ``2 W (n - 1)``."""
    if repeats < 2:
        raise ValueError(f"a cell's variance needs two runs; got {repeats}")
    return float(t_distribution.ppf(1 - ALPHA / 2, 2 * wordings * (repeats - 1)))


def _smallest(fits: Callable[[int], bool]) -> int:
    for n in range(2, _SEARCH_LIMIT):
        if fits(n):
            return n
    raise RepeatRuleError(
        f"no repeat count up to {_SEARCH_LIMIT:,} meets the rule"
    )  # pragma: no cover


def power_repeats(sd: float, threshold: float, *, wordings: int = WORDINGS) -> int:
    """Rule (a): the fewest repeats with 80% power to declare a split at 1.5 times the threshold."""
    design = DESIGN_MULTIPLE * threshold
    return _smallest(
        lambda n: (
            (t_quantile(n, wordings=wordings) + POWER_Z) * sd * math.sqrt(2 / (wordings * n))
            <= design + _EPSILON
        )
    )


def both_verdicts_repeats(sd: float, threshold: float, *, wordings: int = WORDINGS) -> int:
    """Rule (b): the fewest repeats whose half-width is at most 0.8 times the threshold."""
    reach = PRECISION_MULTIPLE * threshold
    return _smallest(lambda n: share_half_width(sd, n, wordings=wordings) <= reach + _EPSILON)


def share_half_width(sd: float, repeats: int, *, wordings: int = WORDINGS) -> float:
    """The interval's half-width on a difference of two objectives' shares, at ``repeats`` per cell."""
    return t_quantile(repeats, wordings=wordings) * sd * math.sqrt(2 / (wordings * repeats))


def share_repeats(
    scenario_id: str, sd: float, df: int, threshold: float, *, wordings: int = WORDINGS
) -> ShareRepeats:
    """The rule from a pooled sd: both counts, the clamp, and the precision when the cap binds."""
    n_power = power_repeats(sd, threshold, wordings=wordings)
    n_both = both_verdicts_repeats(sd, threshold, wordings=wordings)
    wanted = max(n_power, n_both)
    binds = wanted > CAP
    return ShareRepeats(
        scenario_id=scenario_id,
        pooled_sd=sd,
        degrees_of_freedom=df,
        n_power=n_power,
        n_both_reachable=n_both,
        repeats=min(CAP, max(FLOOR, wanted)),
        cap_binds=binds,
        achieved_half_width=share_half_width(sd, CAP, wordings=wordings) if binds else None,
    )


def choice_half_width(rate: float, repeats: int = CAP, *, wordings: int = WORDINGS) -> float:
    """The half-width of Newcombe's interval, at the family level, for two objectives with the same true rate,
    ``repeats`` runs in each of ``wordings`` wordings a side. Equal rates make the interval symmetric."""
    runs = repeats * wordings
    count = round(rate * runs)
    if abs(count / runs - rate) > _EPSILON:
        raise ValueError(f"a rate of {rate} is not a whole number of {runs} runs")
    interval = newcombe_difference(count, runs, count, runs)
    return interval.width / 2


def choice_repeats(scenario_id: str, *, wordings: int = WORDINGS) -> ChoiceRepeats:
    high, low = CHOICE_RATES
    return ChoiceRepeats(
        scenario_id,
        CAP,
        choice_half_width(high, wordings=wordings),
        choice_half_width(low, wordings=wordings),
    )


def repeats_for_scenario(
    outcomes: ScenarioOutcomes, rows: Sequence[RunRow], *, wordings: int = WORDINGS
) -> ShareRepeats | ChoiceRepeats:
    """The repeats for one scenario from a pilot's runs. Choice rates read no run (they go to the cap); shares
    pool the valid runs' primary outcome over every (objective, wording) cell."""
    scenario_id = outcomes.scenario.id
    if outcomes.kind == "choice_rate":
        return choice_repeats(scenario_id, wordings=wordings)
    scoped = [r for r in rows if r.scenario_id == scenario_id]
    if not scoped:
        raise RepeatRuleError(f"{scenario_id}: no runs in the pilot")
    one_value(scoped, "sweep_id")
    one_value(scoped, "model_key")
    cells: dict[tuple[str, str], list[float]] = {}
    for row in scoped:
        if row.valid:
            cells.setdefault((row.objective_id, row.wording_id), []).append(
                outcomes.score(row).primary
            )
    sd, df = pooled_sd(list(cells.values()))
    return share_repeats(scenario_id, sd, df, outcomes.threshold, wordings=wordings)


def repeats_for_pilot(
    outcomes: Sequence[ScenarioOutcomes], rows: Sequence[RunRow], *, wordings: int = WORDINGS
) -> tuple[ShareRepeats | ChoiceRepeats, ...]:
    """One result per scenario, in the order given."""
    return tuple(repeats_for_scenario(o, rows, wordings=wordings) for o in outcomes)
