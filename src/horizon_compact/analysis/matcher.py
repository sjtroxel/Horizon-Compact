"""The matcher: which objective's runs came closest to what a company actually did (Phase 3 IMPLEMENTATION doc
section 13, `planning/07` section 10.4). A reading, not a test: no verdict, no family, 95% spreads.

**The per-run distance** (13.1) is `descriptive.distance`, the one definition, on the case's observable
dimensions only. The lever-level vector is restricted to the lines the rubric marks observable and
renormalized to sum to 1 on each side; the choice counts only when the company's choice is observable. If
the company's observable lines sum to zero, its money dimension is undefined and every run is distanced
on the choice alone; if one run's do, that run is (``choice_only_runs`` counts them). A run with neither
(no observable choice and nothing on the observable lines) has no distance: it is left out and counted in
``undistanced_runs``, never given a made-up value.

**An objective's distance** is the mean of its runs' distances (10.4 item 3), formed as the mean of its
per-wording means (decision 5, the same as a plain mean when no run failed), with a 95% stratified bootstrap
spread (runs resampled within wording, as section 7.2).

**The label**, in this order:
1. ``not_enough_disclosed``: fewer observable dimensions than ``k_star`` (the choice counts one, each
   observable line one), or nothing to distance on at all;
2. ``no_good_match``: the nearest objective's distance is above ``d_star`` (strictly: a distance equal to
   ``d_star``, to ``BOUNDARY_TOLERANCE``, is not above it, which is what makes "a true match is called no good
   match at most 5% of the time" true when ``d_star`` is a 95th percentile);
3. ``tie``: the 95% bootstrap interval of the gap between the two nearest (second minus nearest, both
   resampled on the same generator) includes zero (decision 9);
4. ``match``: the nearest objective.

The nearest is the smallest distance; an exact equality is broken by objective id, and the tie rule then
says "tie". All five distances and their spreads are returned whatever the label.

**Readings** (10.4 item 6): the rubric's primary reading and each uncertain call's alternative are matched
separately. ``depends_on_reading`` is set when the nearest objective is not the same across every reading
that was matched (a reading labelled ``not_enough_disclosed`` has no nearest and does not count).

``d_star`` and ``k_star`` are set by the simulations (step 10, section 14.2), one pair per scenario shape, and
kept as data in ``matcher_thresholds.toml`` beside this file (frozen with the folder). They are data, not
code, so that writing them does not change the code the simulations' results record a hash of. A shape with no
entry is not calibrated, and the matcher refuses to label it unless both are passed.
"""

from __future__ import annotations

import math
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from horizon_compact.analysis.descriptive import distance
from horizon_compact.analysis.intervals import (
    DESCRIPTIVE_ALPHA,
    RESAMPLES,
    comparison_seed,
    stratified_bootstrap_difference,
    stratified_bootstrap_value,
)
from horizon_compact.analysis.records import RunRow
from horizon_compact.analysis.verdict import BOUNDARY_TOLERANCE, one_value
from horizon_compact.experiment import Scenario

THRESHOLDS_FILE = Path(__file__).with_name("matcher_thresholds.toml")

PRIMARY_READING = "primary"

Label = Literal["match", "tie", "no_good_match", "not_enough_disclosed"]
Basis = Literal["vector", "choice", "both"]


class MatcherError(Exception):
    """The case cannot be matched as given. The message says why."""


@dataclass(frozen=True)
class CompanyDecision:
    """One reading of what the company did, from the rubric: the observable lines only (any unit; the
    vector is renormalized) and the choice, or ``None`` when the choice is unobservable or there is none."""

    reading: str
    amounts: Mapping[str, float]
    choice: str | None

    @property
    def dimensions(self) -> int:
        return len(self.amounts) + (1 if self.choice is not None else 0)


@dataclass(frozen=True)
class ObjectiveDistance:
    objective_id: str
    distance: float  # the mean of its per-wording mean run distances
    low: float  # the 95% stratified bootstrap spread
    high: float
    seed: int
    runs: int  # runs distanced
    choice_only_runs: (
        int  # of those, distanced on the choice alone (the run's observable lines sum to 0)
    )
    undistanced_runs: int  # left out: nothing observable to distance on


@dataclass(frozen=True)
class Gap:
    """Second nearest minus nearest, with its 95% interval."""

    nearest: str
    second: str
    estimate: float
    low: float
    high: float
    seed: int


@dataclass(frozen=True)
class ReadingMatch:
    reading: str
    observable_lines: tuple[str, ...]
    choice_observable: bool
    dimensions: int
    company_basis: Basis | None  # what the company side offers; None when nothing
    label: Label
    reason: str
    nearest: str | None  # None only when not enough is disclosed
    tied_with: str | None
    gap: Gap | None
    distances: tuple[
        ObjectiveDistance, ...
    ]  # in objective order; empty when not enough is disclosed


@dataclass(frozen=True)
class CaseMatch:
    case_id: str
    scenario_id: str
    sweep_id: str
    model_key: str
    d_star: float
    k_star: int
    alpha: float
    resamples: int
    readings: tuple[ReadingMatch, ...]  # the primary first, then the alternatives as given
    depends_on_reading: bool


@dataclass(frozen=True)
class Thresholds:
    d_star: float
    k_star: int


def load_thresholds(path: Path = THRESHOLDS_FILE) -> dict[str, Thresholds]:
    """The calibrated thresholds by scenario shape; empty when the file does not exist yet."""
    if not path.is_file():
        return {}
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    out = {}
    for shape, entry in data.get("shapes", {}).items():
        d, k = entry["d_star"], entry["k_star"]
        if not (isinstance(d, float) and d > 0 and isinstance(k, int) and k >= 1):
            raise MatcherError(
                f"{path.name}: {shape} needs a positive d_star and an integer k_star >= 1"
            )
        out[shape] = Thresholds(d, k)
    return out


def observable_vector(
    amounts: Mapping[str, float], lines: Sequence[str]
) -> dict[str, float] | None:
    """``amounts`` restricted to ``lines`` and renormalized to sum to 1; ``None`` when they sum to zero."""
    total = math.fsum(float(amounts[k]) for k in lines)
    if total <= 0:
        return None
    return {k: float(amounts[k]) / total for k in lines}


def check_decision(scenario: Scenario, decision: CompanyDecision) -> None:
    """Refuse a reading that names a line or option the scenario does not offer, or a negative amount."""
    offered = {lever.key for lever in scenario.offered()}
    unknown = sorted(set(decision.amounts) - offered)
    if unknown:
        raise MatcherError(
            f"reading {decision.reading!r} names lines {unknown} that {scenario.id} does not offer"
        )
    negative = sorted(k for k, v in decision.amounts.items() if not v >= 0)
    if negative:
        raise MatcherError(
            f"reading {decision.reading!r} has negative or missing amounts on {negative}"
        )
    if decision.choice is not None:
        if scenario.choice is None:
            raise MatcherError(
                f"reading {decision.reading!r} names a choice; {scenario.id} has none"
            )
        options = {option.key for option in scenario.choice.options}
        if decision.choice not in options:
            raise MatcherError(
                f"reading {decision.reading!r} chose {decision.choice!r}; {scenario.id} offers {sorted(options)}"
            )


@dataclass(frozen=True)
class _Distanced:
    cells: dict[str, list[float]]  # wording -> run distances
    choice_only: int
    undistanced: int


def _distance_runs(
    rows: Sequence[RunRow],
    lines: Sequence[str],
    company_vector: dict[str, float] | None,
    choice: str | None,
) -> _Distanced:
    cells: dict[str, list[float]] = {}
    choice_only = undistanced = 0
    for row in rows:
        assert row.amounts is not None  # valid runs only
        run_vector = observable_vector(row.amounts, lines) if company_vector is not None else None
        got = distance(
            run_vector, company_vector, row.choice if choice is not None else None, choice
        )
        if got is None:
            undistanced += 1
            continue
        if company_vector is not None and got.basis == "choice":
            choice_only += 1
        cells.setdefault(row.wording_id, []).append(got.value)
    return _Distanced(cells, choice_only, undistanced)


def _not_enough(
    decision: CompanyDecision, lines: tuple[str, ...], basis: Basis | None, reason: str
) -> ReadingMatch:
    return ReadingMatch(
        reading=decision.reading,
        observable_lines=lines,
        choice_observable=decision.choice is not None,
        dimensions=decision.dimensions,
        company_basis=basis,
        label="not_enough_disclosed",
        reason=reason,
        nearest=None,
        tied_with=None,
        gap=None,
        distances=(),
    )


def match_reading(
    scenario: Scenario,
    rows: Sequence[RunRow],
    decision: CompanyDecision,
    *,
    case_id: str,
    objectives: Sequence[str],
    d_star: float,
    k_star: int,
    alpha: float = DESCRIPTIVE_ALPHA,
    resamples: int = RESAMPLES,
) -> ReadingMatch:
    """One reading of one case: the five distances, their spreads and the label. ``rows`` are the case's
    runs (one sweep of one model); only valid runs are read."""
    check_decision(scenario, decision)
    lines = tuple(lever.key for lever in scenario.offered() if lever.key in decision.amounts)
    company_vector = observable_vector(decision.amounts, lines) if lines else None
    has_choice = decision.choice is not None
    basis: Basis | None = (
        "both"
        if company_vector is not None and has_choice
        else "vector"
        if company_vector is not None
        else "choice"
        if has_choice
        else None
    )
    if decision.dimensions < k_star:
        return _not_enough(
            decision,
            lines,
            basis,
            f"{decision.dimensions} observable dimension(s), fewer than the {k_star} needed to separate objectives",
        )
    if basis is None:
        return _not_enough(
            decision, lines, basis, "the observable lines sum to zero and no choice is observable"
        )

    sweep_id = one_value(rows, "sweep_id")
    valid = [r for r in rows if r.valid and r.scenario_id == scenario.id]
    distanced: dict[str, _Distanced] = {}
    for objective in objectives:
        own = [r for r in valid if r.objective_id == objective]
        if not own:
            raise MatcherError(f"{case_id}: objective {objective} has no valid run")
        got = _distance_runs(own, lines, company_vector, decision.choice)
        if not got.cells:
            raise MatcherError(
                f"{case_id} ({decision.reading}): no run of objective {objective} can be distanced on "
                "the observable dimensions"
            )
        distanced[objective] = got
    wordings = {objective: set(d.cells) for objective, d in distanced.items()}
    if len({frozenset(w) for w in wordings.values()}) != 1:
        raise MatcherError(
            f"{case_id} ({decision.reading}): objectives hold different wordings of distanced runs: "
            f"{ {o: sorted(w) for o, w in wordings.items()} }"
        )

    prefix = f"match:{case_id}:{decision.reading}"
    results = []
    for objective in objectives:
        d = distanced[objective]
        seed = comparison_seed(sweep_id, f"{prefix}:{objective}")
        spread = stratified_bootstrap_value(d.cells, seed=seed, alpha=alpha, resamples=resamples)
        results.append(
            ObjectiveDistance(
                objective_id=objective,
                distance=spread.estimate,
                low=spread.low,
                high=spread.high,
                seed=seed,
                runs=sum(len(v) for v in d.cells.values()),
                choice_only_runs=d.choice_only,
                undistanced_runs=d.undistanced,
            )
        )

    ranked = sorted(results, key=lambda r: (r.distance, r.objective_id))
    nearest, second = ranked[0], ranked[1]
    gap_seed = comparison_seed(sweep_id, f"{prefix}:{nearest.objective_id}-{second.objective_id}")
    gap_interval = stratified_bootstrap_difference(
        distanced[second.objective_id].cells,
        distanced[nearest.objective_id].cells,
        seed=gap_seed,
        alpha=alpha,
        resamples=resamples,
    )
    gap = Gap(
        nearest.objective_id,
        second.objective_id,
        gap_interval.estimate,
        gap_interval.low,
        gap_interval.high,
        gap_seed,
    )
    eps = BOUNDARY_TOLERANCE
    tied_with: str | None = None
    label: Label
    if nearest.distance > d_star + eps:
        label = "no_good_match"
        reason = f"the nearest distance {nearest.distance:.4f} is above {d_star:.4f}"
    elif gap.low <= eps and gap.high >= -eps:
        label = "tie"
        tied_with = second.objective_id
        reason = (
            f"the gap to {second.objective_id} ({gap.estimate:.4f}) has a 95% interval "
            f"[{gap.low:.4f}, {gap.high:.4f}] that includes zero"
        )
    else:
        label = "match"
        reason = (
            f"nearest by {gap.estimate:.4f}, interval [{gap.low:.4f}, {gap.high:.4f}] above zero"
        )
    return ReadingMatch(
        reading=decision.reading,
        observable_lines=lines,
        choice_observable=has_choice,
        dimensions=decision.dimensions,
        company_basis=basis,
        label=label,
        reason=reason,
        nearest=nearest.objective_id,
        tied_with=tied_with,
        gap=gap,
        distances=tuple(results),
    )


def match_case(
    scenario: Scenario,
    rows: Sequence[RunRow],
    readings: Sequence[CompanyDecision],
    *,
    case_id: str,
    objectives: Sequence[str],
    d_star: float | None = None,
    k_star: int | None = None,
    shape: str | None = None,
    alpha: float = DESCRIPTIVE_ALPHA,
    resamples: int = RESAMPLES,
) -> CaseMatch:
    """Every reading of one case. ``readings[0]`` is the primary; the rest are the uncertain calls'
    alternatives. ``d_star`` and ``k_star`` default to the calibrated pair for ``shape`` (default: the
    scenario's id) in ``matcher_thresholds.toml``; both are given, or neither."""
    if (d_star is None) != (k_star is None):
        raise MatcherError("pass both d_star and k_star, or neither")
    if d_star is not None and k_star is not None:
        d, k = d_star, k_star
    else:
        key = shape or scenario.id
        calibrated = load_thresholds(THRESHOLDS_FILE).get(key)
        if calibrated is None:
            raise MatcherError(
                f"the matcher is not calibrated for shape {key!r}: matcher_thresholds.toml has no entry"
            )
        d, k = calibrated.d_star, calibrated.k_star
    if not readings:
        raise MatcherError(f"{case_id}: no reading to match")
    names = [r.reading for r in readings]
    if len(set(names)) != len(names):
        raise MatcherError(f"{case_id}: reading names repeat: {names}")
    if len(set(objectives)) != len(objectives) or len(objectives) < 2:
        raise MatcherError(
            f"{case_id}: the matcher needs at least two distinct objectives, not {list(objectives)}"
        )
    scoped = [r for r in rows if r.scenario_id == scenario.id]
    if not scoped:
        raise MatcherError(f"{case_id}: no runs on {scenario.id}")
    sweep_id = one_value(scoped, "sweep_id")
    model_key = one_value(scoped, "model_key")
    matched = tuple(
        match_reading(
            scenario,
            scoped,
            reading,
            case_id=case_id,
            objectives=objectives,
            d_star=d,
            k_star=k,
            alpha=alpha,
            resamples=resamples,
        )
        for reading in readings
    )
    nearest = {m.nearest for m in matched if m.nearest is not None}
    return CaseMatch(
        case_id=case_id,
        scenario_id=scenario.id,
        sweep_id=sweep_id,
        model_key=model_key,
        d_star=d,
        k_star=k,
        alpha=alpha,
        resamples=resamples,
        readings=matched,
        depends_on_reading=len(nearest) > 1,
    )
