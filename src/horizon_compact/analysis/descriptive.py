"""The descriptive analyses (Phase 3 IMPLEMENTATION doc section 11, `planning/07` section 6.5).

Fixed in code before any result exists, outside the family of 16, no verdicts. One scenario of one sweep
of one model at a time, valid runs only (failures are counted by the failure rules, not here).

1. **The full allocation.** Every offered line's share of the scenario's total: count, mean, standard
   deviation (sample, ``n - 1``; ``None`` for one run), median and range, per objective, per wording and
   pooled over the wordings. The per-run values are kept in ``per_run`` so spread can always be drawn
   (`planning/06` 7.3).
2. **The display groups** (`planning/07` 3.3), each run's lines summed. The groups overlap (L2 is in
   two) and exist for display only. A scenario with both uses and sources (S4) sums them apart. A line
   with no canonical lever (S4's program) is in no group.
3. **Where the money went.** The same cells for S2's bearers and S4's uses and sources, with the choice
   scenarios also split by the choice made (S4 by fund and decline).
4. **The choices.** S3's three-way split and S4's two-way, as counts per objective and wording; the
   lines by choice are cells 1 and 3 with a choice named, so S3's people lines and S4's funding sources
   among funding runs and among declining runs are there.
5. **E's distance to each objective** beside each objective's distance to itself, so a large distance
   cannot be read as spread alone (see `run_distance`).
6. **The secondaries** (section 6): S1's keep-pay share of those moved (with how many runs it is defined
   for), S3's retained share, S4's any-cuts, per objective and wording, and by choice where there is
   one.

Position effects (10.3) are in `robustness.py` and first attempt beside final (9.3) in `failures.py`.
"""

from __future__ import annotations

import statistics
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import combinations

from horizon_compact.analysis.outcomes import RunOutcome, ScenarioOutcomes
from horizon_compact.analysis.records import RunRow
from horizon_compact.analysis.verdict import one_value

BASELINE_OBJECTIVE = "E"  # the model's default, with no stated objective (`planning/07` 6.1)

DISPLAY_GROUPS = (
    "workforce",
    "customers",
    "suppliers",
    "future_capability",
    "environment_communities",
    "shareholders",
    "balance_sheet",
)


def groups_of(scenario_id: str, lever: str) -> tuple[str, ...]:
    """The display groups a canonical lever belongs to (`planning/07` 3.3). L8 is the shareholders' lower
    profit in S2 and the balance sheet elsewhere. A line with no lever is in none."""
    table = {
        "L1": ("workforce",),
        "L2": ("workforce", "future_capability"),
        "L3": ("future_capability",),
        "L4": ("workforce",),
        "L5": ("customers",),
        "L6": ("environment_communities",),
        "L7": ("shareholders",),
        "L8": ("shareholders",) if scenario_id == "s2" else ("balance_sheet",),
        "L9": ("suppliers",),
    }
    return table.get(lever, ())


@dataclass(frozen=True)
class Summary:
    n: int
    mean: float
    sd: float | None  # sample standard deviation; None for one run
    median: float
    minimum: float
    maximum: float


def summarize(values: Sequence[float]) -> Summary:
    if not values:
        raise ValueError("nothing to summarize")
    return Summary(
        n=len(values),
        mean=statistics.fmean(values),
        sd=statistics.stdev(values) if len(values) > 1 else None,
        median=float(statistics.median(values)),
        minimum=min(values),
        maximum=max(values),
    )


@dataclass(frozen=True)
class LineSummary:
    key: str
    kind: str  # "use" or "source", from the scenario file
    summary: Summary  # of the line's share of the scenario's total


@dataclass(frozen=True)
class GroupSummary:
    group: str
    kind: str
    summary: Summary  # of each run's summed shares; the groups overlap


@dataclass(frozen=True)
class AllocationCell:
    """One cell of section 11 items 1-4: an objective, a wording (``None``: pooled over wordings) and a
    choice (``None``: every run)."""

    objective_id: str
    wording_id: str | None
    choice: str | None
    runs: int
    lines: tuple[LineSummary, ...]
    groups: tuple[GroupSummary, ...]


@dataclass(frozen=True)
class ChoiceSplit:
    objective_id: str
    wording_id: str | None
    runs: int
    counts: tuple[tuple[str, int], ...]  # every option in file order, zeros included


@dataclass(frozen=True)
class SecondaryRow:
    objective_id: str
    wording_id: str | None
    choice: str | None
    name: str
    mean: float | None  # over the runs where it is defined
    n_defined: int
    n_runs: int


@dataclass(frozen=True)
class RunValues:
    """One valid run's outcome, kept whole so spread can be drawn."""

    run_id: str
    objective_id: str
    wording_id: str
    repeat: int
    choice: str | None
    primary: float
    shares: tuple[tuple[str, float], ...]  # every offered line's share of the total
    secondary: tuple[tuple[str, float | None], ...]


@dataclass(frozen=True)
class RunDistance:
    value: float
    basis: str  # "both", "vector" or "choice"


def total_variation(a: dict[str, float], b: dict[str, float]) -> float:
    """Half the sum of absolute differences of two vectors that each sum to 1: 0 (same) to 1 (disjoint)."""
    if set(a) != set(b):
        raise ValueError("two vectors to compare must name the same lines")
    return 0.5 * sum(abs(a[k] - b[k]) for k in a)


def distance(
    vector_a: Mapping[str, float] | None,
    vector_b: Mapping[str, float] | None,
    choice_a: str | None,
    choice_b: str | None,
) -> RunDistance | None:
    """The one definition of the per-run distance (`planning/07` 10.4, doc 13.1): the total variation
    distance of the two vectors where both are defined; 0 if the two choices are the same and 1 if not,
    where both are given; the mean of the two when both exist. ``basis`` records which. ``None`` when
    there is neither. ``run_distance`` (section 11) and the matcher (section 13) both call it."""
    parts: list[float] = []
    basis = []
    if vector_a is not None and vector_b is not None:
        parts.append(total_variation(dict(vector_a), dict(vector_b)))
        basis.append("vector")
    if choice_a is not None and choice_b is not None:
        parts.append(0.0 if choice_a == choice_b else 1.0)
        basis.append("choice")
    if not parts:
        return None
    return RunDistance(sum(parts) / len(parts), "both" if len(parts) == 2 else basis[0])


def run_distance(a: RunOutcome, b: RunOutcome, *, has_choice: bool) -> RunDistance:
    """The per-run distance between two runs on the full lever-level vector (`distance`). A vector that
    is undefined (S4, every line zero) leaves the choice alone, and ``basis`` records it."""
    got = distance(
        a.vector,
        b.vector,
        a.choice if has_choice else None,
        b.choice if has_choice else None,
    )
    if got is None:
        raise ValueError("these runs have neither a vector nor a choice to distance")
    return got


@dataclass(frozen=True)
class DistanceRow:
    """E's mean distance to one objective's runs beside that objective's mean distance to itself."""

    objective_id: str
    e_to_objective: float | None  # mean over every (E run, this objective's run) pair
    e_pairs: int
    e_choice_only_pairs: int  # pairs distanced on the choice alone because a vector was undefined
    self_distance: float | None  # mean over its own distinct pairs of runs; None below two runs
    self_pairs: int
    self_choice_only_pairs: int


@dataclass(frozen=True)
class ScenarioDescriptive:
    scenario_id: str
    runs: int  # valid runs read
    cells: tuple[AllocationCell, ...]
    choice_splits: tuple[ChoiceSplit, ...]
    secondaries: tuple[SecondaryRow, ...]
    distances: tuple[DistanceRow, ...]  # empty when there is no E run
    per_run: tuple[RunValues, ...]  # sorted by run id


def _mean_distance(
    pairs: Sequence[tuple[RunOutcome, RunOutcome]], has_choice: bool
) -> tuple[float | None, int, int]:
    distances = [run_distance(a, b, has_choice=has_choice) for a, b in pairs]
    if not distances:
        return None, 0, 0
    return (
        statistics.fmean(d.value for d in distances),
        len(distances),
        sum(1 for d in distances if d.basis == "choice"),
    )


def _shares(row: RunRow, keys: Sequence[str], total: float) -> dict[str, float]:
    assert row.amounts is not None  # a valid run
    return {k: float(row.amounts[k]) / total for k in keys}


def describe_scenario(outcomes: ScenarioOutcomes, rows: Sequence[RunRow]) -> ScenarioDescriptive:
    scenario = outcomes.scenario
    scoped = [r for r in rows if r.scenario_id == scenario.id]
    if not scoped:
        raise ValueError(f"no runs on {scenario.id}")
    one_value(scoped, "sweep_id")
    one_value(scoped, "model_key")
    valid = sorted((r for r in scoped if r.valid), key=lambda r: r.run_id)
    if not valid:
        raise ValueError(f"{scenario.id}: no valid run to describe")

    total = float(scenario.total)
    offered = scenario.offered()
    kinds = {lever.key: lever.kind for lever in offered}
    group_lines: dict[tuple[str, str], list[str]] = {}
    for lever in offered:
        for group in groups_of(scenario.id, lever.lever):
            group_lines.setdefault((group, lever.kind), []).append(lever.key)
    group_order = [
        (g, k) for g in DISPLAY_GROUPS for k in ("use", "source") if (g, k) in group_lines
    ]
    scored = {r.run_id: outcomes.score(r) for r in valid}
    shares = {r.run_id: _shares(r, outcomes.line_keys, total) for r in valid}

    def cell(objective: str, wording: str | None, choice: str | None) -> AllocationCell | None:
        members = [
            r
            for r in valid
            if r.objective_id == objective
            and (wording is None or r.wording_id == wording)
            and (choice is None or r.choice == choice)
        ]
        if not members:
            return None
        lines = tuple(
            LineSummary(key, kinds[key], summarize([shares[r.run_id][key] for r in members]))
            for key in outcomes.line_keys
        )
        groups = tuple(
            GroupSummary(
                group,
                kind,
                summarize(
                    [sum(shares[r.run_id][k] for k in group_lines[(group, kind)]) for r in members]
                ),
            )
            for group, kind in group_order
        )
        return AllocationCell(objective, wording, choice, len(members), lines, groups)

    objectives = sorted({r.objective_id for r in valid})
    options = [o.key for o in scenario.choice.options] if scenario.choice else []
    cells: list[AllocationCell] = []
    splits: list[ChoiceSplit] = []
    secondary_rows: list[SecondaryRow] = []
    for objective in objectives:
        wordings = sorted({r.wording_id for r in valid if r.objective_id == objective})
        for wording in [None, *wordings]:
            for choice in [None, *(options if wording is None else [])]:
                got = cell(objective, wording, choice)
                if got is None:
                    continue
                cells.append(got)
                members = [
                    r
                    for r in valid
                    if r.objective_id == objective
                    and (wording is None or r.wording_id == wording)
                    and (choice is None or r.choice == choice)
                ]
                names = list(scored[members[0].run_id].secondary)
                for name in names:
                    summary = outcomes.summarize_secondary(name, members)
                    secondary_rows.append(
                        SecondaryRow(
                            objective,
                            wording,
                            choice,
                            name,
                            summary.mean,
                            summary.n_defined,
                            summary.n_runs,
                        )
                    )
            if options:
                members = [
                    r
                    for r in valid
                    if r.objective_id == objective and (wording is None or r.wording_id == wording)
                ]
                counted = Counter(r.choice for r in members)
                splits.append(
                    ChoiceSplit(
                        objective, wording, len(members), tuple((o, counted[o]) for o in options)
                    )
                )

    distances: list[DistanceRow] = []
    by_objective = {o: [scored[r.run_id] for r in valid if r.objective_id == o] for o in objectives}
    has_choice = scenario.choice is not None
    if by_objective.get(BASELINE_OBJECTIVE):
        e_runs = by_objective[BASELINE_OBJECTIVE]
        for objective in objectives:
            runs = by_objective[objective]
            to_e = (
                _mean_distance([(e, x) for e in e_runs for x in runs], has_choice)
                if objective != BASELINE_OBJECTIVE
                else (None, 0, 0)
            )
            own = _mean_distance(list(combinations(runs, 2)), has_choice)
            distances.append(
                DistanceRow(objective, to_e[0], to_e[1], to_e[2], own[0], own[1], own[2])
            )

    per_run = tuple(
        RunValues(
            r.run_id,
            r.objective_id,
            r.wording_id,
            r.repeat,
            r.choice,
            scored[r.run_id].primary,
            tuple((k, shares[r.run_id][k]) for k in outcomes.line_keys),
            tuple(scored[r.run_id].secondary.items()),
        )
        for r in valid
    )
    return ScenarioDescriptive(
        scenario.id,
        len(valid),
        tuple(cells),
        tuple(splits),
        tuple(secondary_rows),
        tuple(distances),
        per_run,
    )
