"""The simulations that run the analysis engine itself, end to end, at its frozen settings (``ALPHA``):
failures and the worst-case bound, the wording rule, and the validation of the share family's vectorized
engine against the analysis. Each replicate is a set of S1 runs built as ``RunRow`` objects, read by the same
functions a real sweep's runs are.

Every check here recomputes what it checks *independently* where it can: the bound's settings and verdicts
are rebuilt from the replicate's own values with this module's own Welch interval and decision 10's rules,
the wording label from the per-wording means, and the share engine's verdicts from ``verdicts.py``, so a
passing check is not the code agreeing with itself. (Step 10's resample-count family served the bootstrap
verdict; it went at step 12, and its numbers stay in the IMPLEMENTATION doc, section 20a, finding 9.)
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from functools import cache
from typing import Any

import numpy as np
from scipy import stats

from horizon_compact.analysis.failures import assess_comparison
from horizon_compact.analysis.intervals import ALPHA
from horizon_compact.analysis.outcomes import SHARE_THRESHOLD, ScenarioOutcomes, outcomes_for
from horizon_compact.analysis.records import RunRow
from horizon_compact.analysis.robustness import wording_direction
from horizon_compact.analysis.verdict import BOUNDARY_TOLERANCE, SHARE_FLOOR, compare, decide
from horizon_compact.experiment import load_experiment
from horizon_compact.simulation.exact import S1_GRID, draw
from horizon_compact.simulation.verdicts import less_certain, newcombe_verdict, share_verdicts

W3 = ("w1", "w2", "w3")
FIRST, SECOND = "A", "B"
MODEL = "simulation"


@cache
def s1_outcomes() -> ScenarioOutcomes:
    return outcomes_for(load_experiment("company").get_scenario("s1"))


def _row(sweep: str, objective: str, wording: str, repeat: int, kept: int | None) -> RunRow:
    amounts = (
        None
        if kept is None
        else {"eliminate": S1_GRID - kept, "move_plant_pay": kept, "move_keep_pay": 0}
    )
    status = "valid" if kept is not None else "sum_mismatch"
    return RunRow(
        run_id=f"{sweep}:{objective}:{wording}:{repeat}",
        sweep_id=sweep,
        model_key=MODEL,
        scenario_id="s1",
        objective_id=objective,
        wording_id=wording,
        repeat=repeat,
        status=status,
        first_attempt_status=status,
        attempts=1,
        possible_decline=False,
        menu_order=(),
        option_order=(),
        amounts=amounts,
        choice=None,
        first_amounts=amounts,
        first_choice=None,
    )


def build_rows(
    sweep: str,
    first: np.ndarray,
    second: np.ndarray,
    failed_first: np.ndarray,
    failed_second: np.ndarray,
) -> list[RunRow]:
    """S1 runs from lattice values of shape (wordings, n); a failed run is a format failure, no amounts."""
    rows = []
    for objective, values, failed in (
        (FIRST, first, failed_first),
        (SECOND, second, failed_second),
    ):
        for w, wording in enumerate(W3):
            for i in range(values.shape[1]):
                kept = None if failed[w, i] else int(values[w, i])
                rows.append(_row(sweep, objective, wording, i, kept))
    return rows


def _cells(
    values: np.ndarray, failed: np.ndarray, wordings: Sequence[str]
) -> dict[str, list[float]]:
    index = {w: i for i, w in enumerate(W3)}
    return {
        w: [v / S1_GRID for v, f in zip(values[index[w]], failed[index[w]], strict=True) if not f]
        for w in wordings
    }


def rebuild_verdict(
    cells_first: dict[str, list[float]],
    cells_second: dict[str, list[float]],
    threshold: float = SHARE_THRESHOLD,
) -> str:
    """The adopted share rule, written again for the bound's independent rebuild: Welch over unequal cells,
    then the floor and the constant check. Values are S1 shares, so on the lattice in 125ths."""
    wordings = len(cells_first)
    sides = [
        [np.rint(np.asarray(cells[w]) * S1_GRID).astype(np.int64) for w in sorted(cells)]
        for cells in (cells_first, cells_second)
    ]
    means = [np.mean([cell.mean() for cell in side]) / S1_GRID for side in sides]
    d = float(means[0] - means[1])
    terms, sizes = [], []
    for side in sides:
        for cell in side:
            n = cell.size
            numerator = n * int((cell * cell).sum()) - int(cell.sum()) ** 2  # exact
            terms.append(numerator / (n * (n - 1) * S1_GRID**2) / (wordings**2 * n))
            sizes.append(n)
    se2 = sum(terms)
    if se2 > 0:
        df = se2**2 / sum(t * t / (n - 1) for t, n in zip(terms, sizes, strict=True))
        half = float(stats.t.ppf(1 - ALPHA / 2, df)) * se2**0.5
    else:
        half = 0.0
    verdict: str = decide(d, d - half, d + half, threshold).verdict
    if verdict == "no_split" and 2 * half < SHARE_FLOOR + BOUNDARY_TOLERANCE:
        verdict = "inconclusive"
    for side in sides:
        values = np.concatenate(side)
        if np.all(values == values[0]):
            value = int(values[0])
            counts = [int((np.concatenate(x) == value).sum()) for x in sides]
            totals = [sum(c.size for c in x) for x in sides]
            verdict = less_certain(
                verdict, newcombe_verdict(counts[0], totals[0], counts[1], totals[1], threshold)
            )
            break
    return verdict


def _bound_settings(verdict: str, difference: float) -> list[tuple[str, float, float]]:
    if verdict == "split":
        return [("narrowing", 0.0, 1.0)] if difference > 0 else [("narrowing", 1.0, 0.0)]
    return [("widening: difference raised", 1.0, 0.0), ("widening: difference lowered", 0.0, 1.0)]


def failure_point(
    pmf_first: np.ndarray,
    pmf_second: np.ndarray,
    *,
    n: int,
    rate: float,
    pattern: str,
    reps: int,
    seed: int,
    key: str,
) -> dict[str, Any]:
    """Failures at ``rate`` per run, "random" (either objective) or "one_objective" (the first only)."""
    if pattern not in ("random", "one_objective"):
        raise ValueError(pattern)
    rng = np.random.Generator(np.random.PCG64(seed))
    outcomes = s1_outcomes()
    final: Counter[str] = Counter()
    among: Counter[str] = Counter()
    dropped_any = downgraded = violations = mismatches = bound_applied = 0
    kept_total = 0
    for r in range(reps):
        first, second = draw(pmf_first, (3, n), rng), draw(pmf_second, (3, n), rng)
        fail_first = rng.random((3, n)) < rate
        fail_second = (
            rng.random((3, n)) < rate if pattern == "random" else np.zeros((3, n), dtype=bool)
        )
        sweep = f"failsim:{key}:{r}"
        assessed = assess_comparison(
            outcomes, build_rows(sweep, first, second, fail_first, fail_second), FIRST, SECOND
        )
        final[assessed.final_verdict] += 1
        dropped_any += bool(assessed.dropped)
        kept_total += len(assessed.kept_wordings)
        if assessed.among_valid is None:
            continue
        valid = assessed.among_valid
        among[valid.verdict] += 1
        if (
            any(check.overturned for check in assessed.bound)
            and assessed.final_verdict != "inconclusive"
        ):
            violations += 1
        if assessed.final_verdict != valid.verdict:
            downgraded += 1
        # The independent rebuild: the kept wordings' valid values and failure counts, set to the extremes.
        kept = assessed.kept_wordings
        index = {w: i for i, w in enumerate(W3)}
        n_failed = sum(int(fail_first[index[w]].sum() + fail_second[index[w]].sum()) for w in kept)
        expected = valid.verdict
        if n_failed and valid.verdict in ("split", "no_split"):
            bound_applied += 1
            base_first, base_second = (
                _cells(first, fail_first, kept),
                _cells(second, fail_second, kept),
            )
            for _label, v_first, v_second in _bound_settings(valid.verdict, valid.difference):
                cells_first = {
                    w: base_first[w] + [v_first] * int(fail_first[index[w]].sum()) for w in kept
                }
                cells_second = {
                    w: base_second[w] + [v_second] * int(fail_second[index[w]].sum()) for w in kept
                }
                if rebuild_verdict(cells_first, cells_second) != valid.verdict:
                    expected = "inconclusive"
        if expected != assessed.final_verdict:
            mismatches += 1
    return {
        "reps": reps,
        "seed": str(seed),
        "final": dict(sorted(final.items())),
        "among_valid": dict(sorted(among.items())),
        "replicates_with_a_dropped_wording": dropped_any,
        "mean_kept_wordings": kept_total / reps,
        "bound_applied": bound_applied,
        "downgraded_by_bound": downgraded,
        "kept_verdict_the_bound_overturns": violations,
        "independent_rebuild_mismatches": mismatches,
    }


def wording_point(
    pmfs_first: Sequence[np.ndarray],
    pmfs_second: Sequence[np.ndarray],
    *,
    n: int,
    reps: int,
    seed: int,
    key: str,
) -> dict[str, Any]:
    """The wording rule (section 10.1) under per-wording means, through the analysis end to end, with the
    label recomputed independently from the per-wording means."""
    rng = np.random.Generator(np.random.PCG64(seed))
    outcomes = s1_outcomes()
    none = np.zeros((3, n), dtype=bool)
    final: Counter[str] = Counter()
    labels: Counter[str] = Counter()
    mismatches = 0
    for r in range(reps):
        first = np.stack([draw(p, (n,), rng) for p in pmfs_first])
        second = np.stack([draw(p, (n,), rng) for p in pmfs_second])
        rows = build_rows(f"wordsim:{key}:{r}", first, second, none, none)
        assessed = assess_comparison(outcomes, rows, FIRST, SECOND)
        direction = wording_direction(outcomes, rows, assessed)
        final[assessed.final_verdict] += 1
        label = direction.label if direction is not None else None
        if label is not None:
            labels[label] += 1
        expected = None
        if assessed.final_verdict == "split":
            pooled = (first.sum() - second.sum()) / (3 * n * S1_GRID)
            broken = False
            for w in range(3):
                diff = (first[w].sum() - second[w].sum()) / (n * S1_GRID)
                if abs(diff) <= BOUNDARY_TOLERANCE or (diff > 0) != (pooled > 0):
                    broken = True
            expected = "wording_sensitive" if broken else "robust"
        if expected != label:
            mismatches += 1
    return {
        "reps": reps,
        "seed": str(seed),
        "final": dict(sorted(final.items())),
        "labels": dict(sorted(labels.items())),
        "independent_label_mismatches": mismatches,
    }


def validation_point(
    pmf_first: np.ndarray, pmf_second: np.ndarray, *, n: int, reps: int, seed: int, key: str
) -> dict[str, Any]:
    """The share family's engine (``verdicts.share_verdicts``) against the analysis's own ``compare`` on the
    same replicates, built as run rows. The verdicts must agree exactly, and so must the rules that fired;
    the interval ends agree to floating-point error."""
    rng = np.random.Generator(np.random.PCG64(seed))
    first, second = draw(pmf_first, (reps, 3, n), rng), draw(pmf_second, (reps, 3, n), rng)
    engine = share_verdicts(first, second, grid=S1_GRID)
    none = np.zeros((3, n), dtype=bool)
    outcomes = s1_outcomes()
    agree = 0
    diffs: list[float] = []
    disagreements = []
    for r in range(reps):
        rows = build_rows(f"validate:{key}:{r}", first[r], second[r], none, none)
        got = compare(outcomes, rows, FIRST, SECOND)
        same = (
            got.verdict == engine.final[r]
            and got.floor_applied == engine.floor_fired[r]
            and (got.constant_value is not None) == (engine.constant[r] >= 0)
        )
        agree += same
        diffs += [abs(got.interval.low - engine.low[r]), abs(got.interval.high - engine.high[r])]
        if not same:
            disagreements.append(
                {
                    "replicate": r,
                    "analysis": got.verdict,
                    "engine": engine.final[r],
                    "estimate": float(engine.estimate[r]),
                    "analysis_interval": [got.interval.low, got.interval.high],
                    "engine_interval": [float(engine.low[r]), float(engine.high[r])],
                }
            )
    return {
        "reps": reps,
        "seed": str(seed),
        "verdicts_agree": agree,
        "constant_fired": int(sum(v >= 0 for v in engine.constant)),
        "floor_fired": int(sum(engine.floor_fired)),
        "max_abs_endpoint_difference": float(max(diffs)),
        "disagreements": disagreements,
    }
