"""The matcher's calibration (Phase 3 IMPLEMENTATION doc sections 13.3 and 14.2).

Each trial builds one synthetic case (``matcher_cases.build_case``) and runs the analysis's own
``match_case`` on it with no threshold (``d_star`` infinite, ``k_star`` 1), so the record holds what the
thresholds are then set from: the nearest objective's distance, whether the generating objective was nearest
or tied with the nearest, and the label without thresholds (match or tie). The thresholds and the labels
under them follow from these records alone:

- ``D*`` per scenario shape: the 95th percentile of the true-match cases' nearest distance at the largest
  spread, so a true match is called "no good match" at most 5% of the time there: the smallest observed
  distance with at most 5% of the trials strictly above it;
- ``k*`` per shape: the smallest number of observable dimensions at which the generating objective is
  nearest or tied with the nearest in at least 80% of sparse trials at the design spread;
- each case type's label rates at every spread, with ``D*`` and ``k*`` applied.

The gap's interval uses ``MATCH_RESAMPLES`` (10,000) here, not the analysis's 100,000: it is a 95% interval,
so 10,000 leaves about 250 resamples beyond each end, and the full count would multiply the run time by six.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from horizon_compact.analysis.intervals import comparison_seed
from horizon_compact.analysis.matcher import MatcherError, match_case
from horizon_compact.experiment import load_experiment
from horizon_compact.simulation.matcher_cases import OBJECTIVES, CaseKind, build_case

MATCH_RESAMPLES = 10_000
NO_THRESHOLD = 1e9
SPREADS = (0.05, 0.10, 0.20)
DESIGN_SPREAD = 0.10
REPEATS = 10
TRUE_MATCH_QUANTILE = 0.95
IDENTIFICATION_TARGET = 0.80
OPPOSITE_TARGET = 0.95


def trial_seed(shape: str, kind: str, sigma: float, k: int | None, trial: int) -> int:
    return comparison_seed("phase-3-matcher", f"{shape}:{kind}:{sigma}:{k}:{trial}")


def run_trials(
    shape: str, kind: CaseKind, sigma: float, k: int | None, trials: range
) -> dict[str, list[Any]]:
    """Per trial: the nearest distance, the generating objective's distance, whether it was identified
    (nearest, or tied with the nearest), the label without thresholds, and the case's dimensions."""
    scenario = load_experiment("company").get_scenario(shape)
    out: dict[str, list[Any]] = {
        "nearest": [],
        "generating": [],
        "identified": [],
        "tie": [],
        "dimensions": [],
        "unmatchable": [],
    }
    for t in trials:
        case = build_case(
            scenario,
            kind,
            seed=trial_seed(shape, kind, sigma, k, t),
            sigma=sigma,
            repeats=REPEATS,
            k=k,
        )
        out["dimensions"].append(case.decision.dimensions)
        try:
            reading = match_case(
                scenario,
                case.rows,
                [case.decision],
                case_id=f"{shape}:{kind}:{t}",
                objectives=OBJECTIVES,
                d_star=NO_THRESHOLD,
                k_star=1,
                resamples=MATCH_RESAMPLES,
            ).readings[0]
        except MatcherError:
            # Matcher finding (b): an objective with no distanceable run in some wording. Counted, and
            # never identified.
            out["unmatchable"].append(True)
            out["nearest"].append(math.nan)
            out["generating"].append(math.nan)
            out["identified"].append(False)
            out["tie"].append(False)
            continue
        out["unmatchable"].append(False)
        distances = {d.objective_id: d.distance for d in reading.distances}
        out["nearest"].append(min(distances.values()))
        out["generating"].append(distances[case.generating])
        out["identified"].append(case.generating in (reading.nearest, reading.tied_with))
        out["tie"].append(reading.label == "tie")
    return out


def d_star(nearest: list[float]) -> float:
    """The smallest observed nearest distance with at most 5% of the true-match trials strictly above it:
    the ``ceil(0.95 n)``-th smallest. From the matched trials only (an unmatchable trial has none)."""
    a = np.sort(np.asarray(nearest))
    a = a[~np.isnan(a)]
    return float(a[math.ceil(TRUE_MATCH_QUANTILE * a.size) - 1])


def k_star(identification: dict[int, float]) -> int | None:
    """The smallest k whose identification rate reaches the target; ``None`` when none does."""
    for k in sorted(identification):
        if identification[k] >= IDENTIFICATION_TARGET:
            return k
    return None


def labels(records: dict[str, list[Any]], d: float, k: int) -> dict[str, int]:
    """Label counts with the thresholds applied, in the matcher's order; ``unmatchable`` where the matcher
    refused the case."""
    out = {"not_enough_disclosed": 0, "unmatchable": 0, "no_good_match": 0, "tie": 0, "match": 0}
    for nearest, tie, dims, refused in zip(
        records["nearest"],
        records["tie"],
        records["dimensions"],
        records["unmatchable"],
        strict=True,
    ):
        if dims < k:
            out["not_enough_disclosed"] += 1
        elif refused:
            out["unmatchable"] += 1
        elif nearest > d + 1e-9:
            out["no_good_match"] += 1
        elif tie:
            out["tie"] += 1
        else:
            out["match"] += 1
    return out


def summary(values: list[float]) -> dict[str, float] | None:
    """Of the matched trials; ``None`` when none was matched."""
    a = np.asarray(values)
    a = a[~np.isnan(a)]
    if a.size == 0:
        return None
    q = np.quantile(a, [0.05, 0.5, 0.95])
    return {
        "p05": float(q[0]),
        "median": float(q[1]),
        "p95": float(q[2]),
        "max": float(a.max()),
    }
