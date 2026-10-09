"""The robustness rules (Phase 3 IMPLEMENTATION doc section 10, `planning/07` sections 7.1 and 7.2).

**Wording direction** (10.1). For each comparison, the difference under each kept wording separately,
first named minus second named, among valid runs. A split is **robust** if every wording's difference
has the pooled difference's sign and is not zero; otherwise **wording-sensitive**. Only wordings the
failure rules kept are read, so a dropped wording can neither support nor break a split. "No split" and
"inconclusive" carry the per-wording differences too, descriptively, and have no label; neither has a
split that the worst-case bound already overturned. **The label never changes the verdict.**
`planning/07` 7.1 says a split that reverses under one wording "is reported as wording-sensitive", and
the Phase 3 scope doc says the rule "marks a split as wording-sensitive": the verdict stays a split and
the published claim says which kind (``headline``). Making it inconclusive would be a new rule the
planning does not have. A split over one kept wording is labeled robust trivially; its ``scope`` already
says it is over that wording alone.

**The sealed wording** (10.2). The whole assessment, bound included, repeated on the sealed template's
runs alone, labeled "sealed wording only", outside the family of 16. Which template is sealed is read
from ``objectives.toml`` through the loaded experiment, never typed here. Its verdict is reported beside
the pooled one with a **relation**, because the sealed rerun is the same test on about a third of the
data at the same 99.7% level, so a real result can come back less certain without any wording
disagreeing. With ``P`` the pooled final verdict, ``S`` the sealed one, ``d_P`` and ``d_S`` their
observed differences, ``T`` the threshold and ``eps`` the verdict engine's boundary tolerance:

- ``not_comparable``: either result is ``not_assessable`` (nothing to compare; this is not a
  disagreement);
- ``same_verdict``: ``P`` and ``S`` are the same verdict, and if both are splits their differences
  have the same sign (two splits in opposite directions are ``different``);
- ``same_direction_less_certain``: ``S`` is inconclusive and either ``P`` is a split and ``d_S`` has
  the sign of ``d_P`` and is not zero (``abs(d_S) > eps``), or ``P`` is a no split and ``abs(d_S)``
  is below ``T - eps`` (the point estimate sits inside the band, though its interval is too wide to
  say so);
- ``different``: everything else, including a sealed difference of exactly zero beside a pooled
  split, a sealed point estimate at or past ``T`` beside a pooled no split, and any sealed split or
  no split beside a pooled inconclusive.

**Position effects** (10.3). Descriptive, per scenario, pooled over every objective and wording of one
sweep of one model, valid runs only. For each offered line, its mean share of the scenario's total at
each menu position (positions are those shown, including lines not offered, which sit in the menu too),
and the least-squares slope of share on position through the run-level points. For each option of S3 and
S4, its choice rate when it was listed first against when it was not, with a Newcombe interval at
``DESCRIPTIVE_ALPHA``. No verdict.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from horizon_compact.analysis.failures import (
    AssessedComparison,
    FinalVerdict,
    ScenarioAssessment,
    assess_comparison,
    check_refusal_calls,
)
from horizon_compact.analysis.intervals import (
    ALPHA,
    DESCRIPTIVE_ALPHA,
    Interval,
    newcombe_difference,
)
from horizon_compact.analysis.outcomes import ScenarioOutcomes
from horizon_compact.analysis.records import RunRow
from horizon_compact.analysis.verdict import BOUNDARY_TOLERANCE, gather_cells, one_value
from horizon_compact.experiment import Experiment

SEALED_LABEL = "sealed wording only; outside the family of 16"

WordingLabel = Literal["robust", "wording_sensitive"]
Direction = Literal["same", "opposite", "zero", "undefined"]


# --- 10.1 wording direction --------------------------------------------------------------------------------


@dataclass(frozen=True)
class WordingDifference:
    wording_id: str
    first_value: (
        float  # the first objective's outcome under this wording: mean share, or choice rate
    )
    second_value: float
    n_first: int  # valid runs
    n_second: int
    difference: float  # first minus second
    # Against the pooled difference: its sign, "zero" (within BOUNDARY_TOLERANCE), or "undefined" when the
    # pooled difference has no sign to agree with.
    direction: Direction


@dataclass(frozen=True)
class WordingDirection:
    pooled_difference: float
    differences: tuple[WordingDifference, ...]  # over the kept wordings, in order
    label: WordingLabel | None  # only for a split that survived the bound

    @property
    def reversed_wordings(self) -> tuple[str, ...]:
        """Wordings whose difference is opposite to the pooled one or zero: the ones that break robustness."""
        return tuple(d.wording_id for d in self.differences if d.direction in ("opposite", "zero"))


def _direction(difference: float, pooled: float) -> Direction:
    eps = BOUNDARY_TOLERANCE
    if abs(difference) <= eps:
        return "zero"
    if abs(pooled) <= eps:
        return "undefined"
    return "same" if (difference > 0) == (pooled > 0) else "opposite"


def wording_direction(
    outcomes: ScenarioOutcomes, rows: Sequence[RunRow], assessed: AssessedComparison
) -> WordingDirection | None:
    """The per-wording differences behind one assessed comparison; ``None`` when it was not assessable."""
    if assessed.among_valid is None:
        return None
    cellset = gather_cells(
        outcomes, rows, assessed.first, assessed.second, wordings=assessed.kept_wordings
    )
    pooled = assessed.among_valid.difference
    differences = []
    for wording in cellset.wordings:
        a, b = cellset.cells[assessed.first][wording], cellset.cells[assessed.second][wording]
        first_value, second_value = sum(a) / len(a), sum(b) / len(b)
        difference = first_value - second_value
        differences.append(
            WordingDifference(
                wording, first_value, second_value, len(a), len(b), difference,
                _direction(difference, pooled),
            )
        )  # fmt: skip
    label: WordingLabel | None = None
    if assessed.final_verdict == "split":
        label = "robust" if all(d.direction == "same" for d in differences) else "wording_sensitive"
    return WordingDirection(pooled, tuple(differences), label)


@dataclass(frozen=True)
class RobustComparison:
    """An assessed comparison with its wording direction. ``final_verdict`` is the failure rules' final
    verdict: the wording label qualifies a split and never changes it."""

    assessed: AssessedComparison
    wording: WordingDirection | None

    @property
    def final_verdict(self) -> FinalVerdict:
        return self.assessed.final_verdict

    @property
    def downgrade_reason(self) -> str | None:
        return self.assessed.downgrade_reason

    @property
    def headline(self) -> str:
        """The claim as published: the verdict, qualified for a split, and what it is over."""
        scope = self.assessed.scope
        verdict = self.assessed.final_verdict
        if verdict == "not_assessable":
            return scope
        if verdict != "split" or self.wording is None:
            return f"{verdict.replace('_', ' ')}, {scope}"
        if self.wording.label == "robust":
            return f"split, robust: the direction holds under every wording, {scope}"
        broken = ", ".join(
            f"{d.wording_id} {d.direction if d.direction == 'zero' else 'reverses'} ({d.difference:+.3f})"
            for d in self.wording.differences
            if d.direction in ("opposite", "zero")
        )
        return f"split, wording-sensitive: {broken}, {scope}"


# --- 10.2 the sealed wording -----------------------------------------------------------------------------


def sealed_wording_of(experiment: Experiment) -> str:
    """The sealed template's id, from ``objectives.toml``. An experiment with none (the placeholder) has no
    sealed wording to analyse."""
    if not experiment.sealed_template:
        raise ValueError(f"experiment {experiment.name!r} has no sealed template")
    return experiment.sealed_template


SealedRelation = Literal[
    "same_verdict", "same_direction_less_certain", "different", "not_comparable"
]


def relate(
    pooled_verdict: FinalVerdict,
    pooled_difference: float | None,
    sealed_verdict: FinalVerdict,
    sealed_difference: float | None,
    threshold: float,
) -> tuple[SealedRelation, str]:
    """How the sealed wording's result relates to the pooled one, and why (see the module docstring)."""
    eps = BOUNDARY_TOLERANCE
    if pooled_verdict == "not_assessable" or sealed_verdict == "not_assessable":
        return "not_comparable", "one of the two results is not assessable"
    if pooled_difference is None or sealed_difference is None:
        raise ValueError("an assessable result has a difference")
    if pooled_verdict == sealed_verdict:
        if pooled_verdict == "split" and (pooled_difference > 0) != (sealed_difference > 0):
            return "different", "both are splits, in opposite directions"
        return "same_verdict", f"both are {pooled_verdict.replace('_', ' ')}"
    if sealed_verdict == "inconclusive" and pooled_verdict == "split":
        if abs(sealed_difference) > eps and (sealed_difference > 0) == (pooled_difference > 0):
            return (
                "same_direction_less_certain",
                "the pooled split's direction, but the sealed interval is too wide",
            )
        return "different", "the sealed difference is zero or points the other way"
    if sealed_verdict == "inconclusive" and pooled_verdict == "no_split":
        if abs(sealed_difference) < threshold - eps:
            return (
                "same_direction_less_certain",
                "the point estimate is inside the band, but the interval is too wide",
            )
        return "different", "the sealed difference reaches the threshold"
    return (
        "different",
        f"pooled {pooled_verdict.replace('_', ' ')}, sealed {sealed_verdict.replace('_', ' ')}",
    )


@dataclass(frozen=True)
class SealedResult:
    label: str
    sealed_wording: str
    assessed: AssessedComparison  # over the sealed wording alone, bound included
    pooled_verdict: FinalVerdict
    relation: SealedRelation
    relation_reason: str


def sealed_result(
    outcomes: ScenarioOutcomes,
    rows: Sequence[RunRow],
    pooled: AssessedComparison,
    sealed_wording: str,
    *,
    calls: Mapping[str, str] | None = None,
    alpha: float = ALPHA,
) -> SealedResult:
    """One comparison repeated on the sealed wording's runs alone."""
    check_refusal_calls(rows, calls or {})  # against every run, before the rows are narrowed
    sealed_rows = [r for r in rows if r.wording_id == sealed_wording]
    if not any(r.scenario_id == outcomes.scenario.id for r in sealed_rows):
        raise ValueError(
            f"{outcomes.scenario.id}: no run under the sealed wording {sealed_wording}, so there is no "
            "sealed-wording result to report"
        )
    kept = {r.run_id for r in sealed_rows}
    assessed = assess_comparison(
        outcomes,
        sealed_rows,
        pooled.first,
        pooled.second,
        role=pooled.role,
        calls={k: v for k, v in (calls or {}).items() if k in kept},
        alpha=alpha,
    )
    relation, reason = relate(
        pooled.final_verdict,
        pooled.among_valid.difference if pooled.among_valid else None,
        assessed.final_verdict,
        assessed.among_valid.difference if assessed.among_valid else None,
        outcomes.threshold,
    )
    return SealedResult(
        SEALED_LABEL, sealed_wording, assessed, pooled.final_verdict, relation, reason
    )


# --- 10.3 position effects -------------------------------------------------------------------------------


@dataclass(frozen=True)
class PositionBucket:
    position: int  # 1 is the top of the menu
    runs: int
    mean_share: float


@dataclass(frozen=True)
class LeverPosition:
    key: str
    runs: int
    by_position: tuple[PositionBucket, ...]
    slope: (
        float | None
    )  # share per step down the menu; None when every run had the line at one position


@dataclass(frozen=True)
class OptionPosition:
    option: str
    chosen_first: int  # runs that chose it among the runs that listed it first
    runs_first: int
    chosen_not_first: int
    runs_not_first: int
    interval: (
        Interval | None
    )  # first-listed rate minus not-first rate; None if either group is empty


@dataclass(frozen=True)
class PositionEffects:
    scenario_id: str
    runs: int  # valid runs read
    menu_size: int  # lines shown in the menu, not-offered ones included
    levers: tuple[LeverPosition, ...]
    options: tuple[OptionPosition, ...]  # empty for a scenario with no choice
    alpha: float


def _slope(points: Sequence[tuple[int, float]]) -> float | None:
    xs = [x for x, _ in points]
    mean_x = sum(xs) / len(xs)
    sxx = sum((x - mean_x) ** 2 for x in xs)
    if len(points) < 2 or sxx == 0:
        return None
    mean_y = sum(y for _, y in points) / len(points)
    return sum((x - mean_x) * (y - mean_y) for x, y in points) / sxx


def position_effects(
    outcomes: ScenarioOutcomes, rows: Sequence[RunRow], *, alpha: float = DESCRIPTIVE_ALPHA
) -> PositionEffects:
    """Position effects on one scenario: every objective and wording of one sweep, valid runs."""
    scenario = outcomes.scenario
    scoped = [r for r in rows if r.scenario_id == scenario.id]
    if not scoped:
        raise ValueError(f"no runs on {scenario.id}")
    one_value(scoped, "sweep_id")
    one_value(scoped, "model_key")
    valid = [r for r in scoped if r.valid and r.amounts is not None]
    if not valid:
        raise ValueError(f"{scenario.id}: no valid run, so no position to read")

    total = float(scenario.total)
    keys = outcomes.line_keys
    sizes = {len(r.menu_order) for r in valid}
    if len(sizes) != 1:
        raise ValueError(f"{scenario.id}: runs recorded menus of different sizes {sorted(sizes)}")
    points: dict[str, list[tuple[int, float]]] = {key: [] for key in keys}
    for row in valid:
        assert row.amounts is not None
        missing = [k for k in keys if k not in row.menu_order]
        if missing:
            raise ValueError(
                f"run {row.run_id}: menu_order lacks {missing}; position cannot be read"
            )
        for key in keys:
            points[key].append((row.menu_order.index(key) + 1, float(row.amounts[key]) / total))

    levers = []
    for key in keys:
        buckets = []
        for position in sorted({x for x, _ in points[key]}):
            shares = [y for x, y in points[key] if x == position]
            buckets.append(PositionBucket(position, len(shares), sum(shares) / len(shares)))
        levers.append(LeverPosition(key, len(points[key]), tuple(buckets), _slope(points[key])))

    options: list[OptionPosition] = []
    if scenario.choice is not None:
        for option in scenario.choice.options:
            first = [r for r in valid if r.option_order[:1] == (option.key,)]
            rest = [r for r in valid if r.option_order[:1] != (option.key,)]
            if any(option.key not in r.option_order for r in valid):
                raise ValueError(
                    f"{scenario.id}: option_order lacks {option.key}; cannot read position"
                )
            c1, c2 = (sum(1 for r in g if r.choice == option.key) for g in (first, rest))
            interval = (
                newcombe_difference(c1, len(first), c2, len(rest), alpha=alpha)
                if first and rest
                else None
            )
            options.append(OptionPosition(option.key, c1, len(first), c2, len(rest), interval))
    return PositionEffects(
        scenario.id, len(valid), next(iter(sizes)), tuple(levers), tuple(options), alpha
    )


# --- one scenario ------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ScenarioRobustness:
    scenario_id: str
    comparisons: tuple[RobustComparison, ...]  # in the assessment's order
    sealed: tuple[SealedResult, ...]  # the same order
    position: PositionEffects


def robustness_scenario(
    outcomes: ScenarioOutcomes,
    rows: Sequence[RunRow],
    assessment: ScenarioAssessment,
    sealed_wording: str,
    *,
    calls: Mapping[str, str] | None = None,
    alpha: float = ALPHA,
    descriptive_alpha: float = DESCRIPTIVE_ALPHA,
) -> ScenarioRobustness:
    """Wording direction, the sealed wording and position effects for one scenario's assessment. ``alpha``
    should be the one the assessment was made with."""
    return ScenarioRobustness(
        scenario_id=assessment.scenario_id,
        comparisons=tuple(
            RobustComparison(a, wording_direction(outcomes, rows, a))
            for a in assessment.comparisons
        ),
        sealed=tuple(
            sealed_result(outcomes, rows, a, sealed_wording, calls=calls, alpha=alpha)
            for a in assessment.comparisons
        ),
        position=position_effects(outcomes, rows, alpha=descriptive_alpha),
    )
