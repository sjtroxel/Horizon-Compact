"""The versioned results object for one model's sweep (Phase 3 IMPLEMENTATION doc sections 2, 4 and 8.3,
decision 1).

The engine is a library that returns this object; Phase 1.5's scorer serializes it, so every field here is
a number, a string, a boolean, ``None`` or a tuple of those (or of frozen dataclasses of those).
``RESULTS_VERSION`` (in ``analysis/__init__``) changes when a field or its meaning does, and a test pins the
field names so that cannot happen without someone noticing.

**Nothing in it is published prose.** The structured fields are the result; ``ComparisonResult.headline`` is a
diagnostic one-liner for people reading a run of the code, built from the same fields. The words on any page,
and the vocabulary a business reader sees ("robust" here means only that the direction holds under every
wording), are written by the site's author when Phase 1.5 is built.

``build_results`` refuses a ``RunSet`` with unfinished runs: the failure rules count finished runs only, so a
half-finished sweep would understate every cell's attempts.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from horizon_compact.analysis import RESULTS_VERSION
from horizon_compact.analysis.descriptive import ScenarioDescriptive, describe_scenario
from horizon_compact.analysis.failures import (
    AssessedComparison,
    CellRate,
    FinalVerdict,
    ObjectiveRates,
    PairRates,
    assess_scenario,
)
from horizon_compact.analysis.intervals import ALPHA, DESCRIPTIVE_ALPHA, RESAMPLES, Method
from horizon_compact.analysis.outcomes import ScenarioOutcomes, outcomes_for
from horizon_compact.analysis.records import RunSet
from horizon_compact.analysis.robustness import (
    PositionEffects,
    RobustComparison,
    SealedRelation,
    SealedResult,
    WordingDifference,
    WordingLabel,
    robustness_scenario,
    sealed_wording_of,
)
from horizon_compact.analysis.verdict import Role, Verdict, one_value
from horizon_compact.experiment import Experiment


@dataclass(frozen=True)
class CellCount:
    objective_id: str
    unsuccessful: int  # failures and refusals
    attempted: int


@dataclass(frozen=True)
class DroppedResult:
    """A wording dropped from both sides of a comparison, and the cell or cells that dropped it."""

    wording_id: str
    cells: tuple[CellCount, ...]


@dataclass(frozen=True)
class BoundResult:
    """One recomputation of the verdict with the failed runs in the kept wordings set to 0 or 1."""

    label: str
    first_value: float
    second_value: float
    set_first: int
    set_second: int
    difference: float
    low: float
    high: float
    verdict: Verdict
    overturned: bool


@dataclass(frozen=True)
class SealedSummary:
    label: str
    sealed_wording: str
    final_verdict: FinalVerdict
    difference: float | None
    low: float | None
    high: float | None
    relation: SealedRelation
    relation_reason: str


@dataclass(frozen=True)
class FirstAttemptSummary:
    """The same assessment on first attempts only (descriptive)."""

    final_verdict: FinalVerdict
    difference: float | None
    low: float | None
    high: float | None
    kept_wordings: tuple[str, ...]
    dropped_wordings: tuple[str, ...]


@dataclass(frozen=True)
class ComparisonResult:
    """One comparison, flat. ``final_verdict`` is after the failure rules and the worst-case bound; the
    wording check never changes it, so ``wording_label`` is a separate field a reader must not drop.
    ``headline`` is a diagnostic string, not published text."""

    scenario_id: str
    first: str
    second: str
    role: Role
    label: str
    outcome: str
    kind: str
    threshold: float
    method: Method | None
    alpha: float
    resamples: int | None
    seed: int | None
    difference: float | None
    low: float | None
    high: float | None
    verdict_among_valid: Verdict | None
    degenerate_interval: bool | None
    kept_wordings: tuple[str, ...]
    dropped_wordings: tuple[DroppedResult, ...]
    valid_runs: tuple[tuple[str, int, int], ...]  # (wording, first's runs, second's)
    failed_first: int
    failed_second: int
    bound: tuple[BoundResult, ...]
    worst_case_verdict: Verdict | None
    wording_label: WordingLabel | None
    per_wording: tuple[WordingDifference, ...]
    reversed_wordings: tuple[str, ...]  # a difference opposite to the pooled one
    zero_wordings: tuple[str, ...]  # a difference of zero
    final_verdict: FinalVerdict
    downgrade_reason: str | None
    sealed: SealedSummary
    first_attempt: FirstAttemptSummary
    headline: str


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    primary_outcome: str
    kind: str
    threshold: float
    comparisons: tuple[ComparisonResult, ...]  # A-C, A-B, C-D, B-D, then A-D
    cells: tuple[CellRate, ...]
    objective_rates: tuple[ObjectiveRates, ...]
    pair_rates: tuple[PairRates, ...]
    position: PositionEffects
    descriptive: ScenarioDescriptive


@dataclass(frozen=True)
class ModelResults:
    results_version: int
    experiment: str
    sweep_id: str
    model_key: str
    alpha: float
    descriptive_alpha: float
    resamples: int
    sealed_wording: str
    refusal_calls: tuple[tuple[str, str], ...]  # (run id, reason), sorted
    scenarios: tuple[ScenarioResult, ...]
    scenarios_without_runs: tuple[
        str, ...
    ]  # in the experiment, no run in the data: absence stays visible

    @property
    def family(self) -> tuple[ComparisonResult, ...]:
        """The primary comparisons: 4 per scenario, 16 for a full sweep of one model."""
        return tuple(c for s in self.scenarios for c in s.comparisons if c.role == "primary")


def _interval(assessed: AssessedComparison) -> tuple[float | None, float | None, float | None]:
    valid = assessed.among_valid
    return (
        (None, None, None)
        if valid is None
        else (valid.difference, valid.interval.low, valid.interval.high)
    )


def _first_attempt(assessed: AssessedComparison) -> FirstAttemptSummary:
    difference, low, high = _interval(assessed)
    return FirstAttemptSummary(
        assessed.final_verdict,
        difference,
        low,
        high,
        assessed.kept_wordings,
        tuple(d.wording_id for d in assessed.dropped),
    )


def _sealed(sealed: SealedResult) -> SealedSummary:
    difference, low, high = _interval(sealed.assessed)
    return SealedSummary(
        sealed.label,
        sealed.sealed_wording,
        sealed.assessed.final_verdict,
        difference,
        low,
        high,
        sealed.relation,
        sealed.relation_reason,
    )


def comparison_result(
    outcomes: ScenarioOutcomes,
    robust: RobustComparison,
    sealed: SealedResult,
    first_attempt: AssessedComparison,
    *,
    alpha: float,
) -> ComparisonResult:
    """Flatten one comparison's assessment, wording check, sealed rerun and first-attempt view. The outcome,
    its threshold and the alpha come from the scenario and the run settings, so a comparison that is not
    assessable still carries true values for them."""
    assessed = robust.assessed
    valid = assessed.among_valid
    interval = valid.interval if valid else None
    wording = robust.wording
    return ComparisonResult(
        scenario_id=assessed.scenario_id,
        first=assessed.first,
        second=assessed.second,
        role=assessed.role,
        label=assessed.label,
        outcome=outcomes.primary_name,
        kind=outcomes.kind,
        threshold=outcomes.threshold,
        method=interval.method if interval else None,
        alpha=alpha,
        resamples=interval.resamples if interval else None,
        seed=interval.seed if interval else None,
        difference=interval.estimate if interval else None,
        low=interval.low if interval else None,
        high=interval.high if interval else None,
        verdict_among_valid=valid.verdict if valid else None,
        degenerate_interval=valid.degenerate_interval if valid else None,
        kept_wordings=assessed.kept_wordings,
        dropped_wordings=tuple(
            DroppedResult(
                d.wording_id,
                tuple(CellCount(c.objective_id, c.unsuccessful, c.attempted) for c in d.cells),
            )
            for d in assessed.dropped
        ),
        valid_runs=valid.valid_runs if valid else (),
        failed_first=assessed.failed_first,
        failed_second=assessed.failed_second,
        bound=tuple(
            BoundResult(
                b.label,
                b.first_value,
                b.second_value,
                b.set_first,
                b.set_second,
                b.comparison.difference,
                b.comparison.interval.low,
                b.comparison.interval.high,
                b.comparison.verdict,
                b.overturned,
            )
            for b in assessed.bound
        ),
        worst_case_verdict=assessed.worst_case_verdict,
        wording_label=wording.label if wording else None,
        per_wording=wording.differences if wording else (),
        reversed_wordings=tuple(
            d.wording_id for d in wording.differences if d.direction == "opposite"
        )
        if wording
        else (),
        zero_wordings=tuple(d.wording_id for d in wording.differences if d.direction == "zero")
        if wording
        else (),
        final_verdict=assessed.final_verdict,
        downgrade_reason=assessed.downgrade_reason,
        sealed=_sealed(sealed),
        first_attempt=_first_attempt(first_attempt),
        headline=robust.headline,
    )


def build_results(
    experiment: Experiment,
    runset: RunSet,
    *,
    calls: Mapping[str, str] | None = None,
    alpha: float = ALPHA,
    descriptive_alpha: float = DESCRIPTIVE_ALPHA,
    resamples: int = RESAMPLES,
) -> ModelResults:
    """Every analysis for one finished sweep of one model. Refuses unfinished runs, runs from a scenario the
    experiment does not have, and calls that name no run."""
    if runset.unfinished:
        raise ValueError(
            f"{len(runset.unfinished)} run(s) are unfinished (first: {runset.unfinished[0]}); the failure "
            "rules count finished runs only, so the sweep must finish before it is analysed"
        )
    sealed_wording = sealed_wording_of(experiment)
    rows = list(runset.rows)
    if not rows:
        raise ValueError("no runs to analyse")
    sweep_id = one_value(rows, "sweep_id")
    model_key = one_value(rows, "model_key")
    unknown = sorted({r.scenario_id for r in rows} - set(experiment.scenarios))
    if unknown:
        raise ValueError(f"runs on scenario(s) {unknown}, which {experiment.name!r} does not have")

    scenarios: list[ScenarioResult] = []
    for scenario_id in sorted(experiment.scenarios):
        if not any(r.scenario_id == scenario_id for r in rows):
            continue
        outcomes = outcomes_for(experiment.get_scenario(scenario_id))
        assessment = assess_scenario(
            outcomes,
            rows,
            calls=calls,
            alpha=alpha,
            descriptive_alpha=descriptive_alpha,
            resamples=resamples,
        )
        robustness = robustness_scenario(
            outcomes,
            rows,
            assessment,
            sealed_wording,
            calls=calls,
            alpha=alpha,
            descriptive_alpha=descriptive_alpha,
            resamples=resamples,
        )
        scenarios.append(
            ScenarioResult(
                scenario_id=scenario_id,
                primary_outcome=outcomes.primary_name,
                kind=outcomes.kind,
                threshold=outcomes.threshold,
                comparisons=tuple(
                    comparison_result(outcomes, robust, sealed, first, alpha=alpha)
                    for robust, sealed, first in zip(
                        robustness.comparisons,
                        robustness.sealed,
                        assessment.first_attempt,
                        strict=True,
                    )
                ),
                cells=assessment.cells,
                objective_rates=assessment.objective_rates,
                pair_rates=assessment.pair_rates,
                position=robustness.position,
                descriptive=describe_scenario(outcomes, rows),
            )
        )
    return ModelResults(
        results_version=RESULTS_VERSION,
        experiment=experiment.name,
        sweep_id=sweep_id,
        model_key=model_key,
        alpha=alpha,
        descriptive_alpha=descriptive_alpha,
        resamples=resamples,
        sealed_wording=sealed_wording,
        refusal_calls=tuple(sorted((calls or {}).items())),
        scenarios=tuple(scenarios),
        scenarios_without_runs=tuple(
            s for s in sorted(experiment.scenarios) if s not in {x.scenario_id for x in scenarios}
        ),
    )
