"""``hc simulate run``: every simulation of Phase 3 step 10, seeded, in parallel, into one results file.

Each task is fixed by its family, its grid point and its chunk, and its seed is derived from those names
(``comparison_seed``), so no one picks a seed and the results do not depend on how many workers run them or
in what order they finish: tasks are merged by key and chunk, in sorted order. Re-running from the same code
gives a byte-identical file. The file records a hash of the code and data it was produced from (the analysis
package, the simulation package except its report, the company experiment and ``uv.lock``) rather than a git
sha, because a file cannot name the commit that contains it; the hash is the same before and after that
commit.

``--quick`` runs a small slice of every family, for timing and for checking the pipeline, and writes to
``scratch/`` (never to the evidence folder).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
from collections import defaultdict
from collections.abc import Callable, Iterable
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

import numpy as np

from horizon_compact.analysis import RESULTS_VERSION
from horizon_compact.analysis.intervals import ALPHA, RESAMPLES, Z, comparison_seed
from horizon_compact.analysis.outcomes import CHOICE_THRESHOLD, SHARE_THRESHOLD
from horizon_compact.analysis.repeats import share_repeats
from horizon_compact.analysis.verdict import decide
from horizon_compact.simulation import matcher_sim, real, verdicts
from horizon_compact.simulation.exact import (
    FINE_GRID,
    S1_GRID,
    draw,
    exact_intervals,
    pmf_mean_sd,
    share_pmf,
)

SIMULATION_VERSION = 1
SEED_ROOT = "phase-3-simulation"
T = SHARE_THRESHOLD


@dataclass(frozen=True)
class Plan:
    """The grids of one mode. ``full`` is section 14.1 and 14.2 as written, plus the families the build
    added (each says why in the summary); ``quick`` is a small slice of each."""

    mode: str
    share_mu: tuple[float, ...]
    share_sigma: tuple[float, ...]
    share_pi: tuple[float, ...]
    share_d: tuple[float, ...]
    repeats: tuple[int, ...]
    share_reps: int
    share_reps_null_threshold: int
    chunk: int
    rule_reps: int
    agree_reps: int
    agree_repeats: tuple[int, ...]
    choice_p: tuple[float, ...]
    choice_d: tuple[float, ...]
    fine_reps: int
    shift_reps: int
    failure_sigma: tuple[float, ...]
    failure_repeats: tuple[int, ...]
    failure_rates: tuple[float, ...]
    failure_reps: int
    wording_repeats: tuple[int, ...]
    wording_reps: int
    validation_every: int
    validation_reps: int
    resample_seeds: int
    matcher_trials: int
    matcher_spreads: tuple[float, ...]
    matcher_chunk: int


FULL = Plan(
    mode="full",
    share_mu=(0.1, 0.3, 0.5, 0.7, 0.9),
    share_sigma=(0.02, 0.05, 0.10, 0.15, 0.20, 0.25),
    share_pi=(0.0, 0.2, 0.5),
    share_d=(0.0, 0.05, 0.10, 0.15, 0.20, 0.30),
    repeats=(6, 10, 15, 20),
    share_reps=2_000,
    share_reps_null_threshold=20_000,
    chunk=2_000,
    rule_reps=4_000,
    agree_reps=20_000,
    agree_repeats=(6, 10, 15, 20),
    choice_p=(0.0, 0.05, 0.2, 0.5, 0.8, 0.95, 1.0),
    choice_d=(0.0, 0.10, 0.20, 0.30, 0.35),
    fine_reps=4_000,
    shift_reps=20_000,
    failure_sigma=(0.10, 0.20),
    failure_repeats=(6, 10, 20),
    failure_rates=(0.02, 0.05, 0.10, 0.15),
    failure_reps=300,
    wording_repeats=(10, 20),
    wording_reps=400,
    validation_every=3,
    validation_reps=40,
    resample_seeds=200,
    matcher_trials=2_000,
    matcher_spreads=matcher_sim.SPREADS,
    matcher_chunk=250,
)

QUICK = Plan(
    mode="quick",
    share_mu=(0.5,),
    share_sigma=(0.15,),
    share_pi=(0.0, 0.5),
    share_d=(0.0, 0.10, 0.15),
    repeats=(6, 20),
    share_reps=200,
    share_reps_null_threshold=1_000,
    chunk=500,
    rule_reps=200,
    agree_reps=500,
    agree_repeats=(6,),
    choice_p=(0.05, 0.5),
    choice_d=(0.0, 0.20, 0.30),
    fine_reps=100,
    shift_reps=500,
    failure_sigma=(0.10,),
    failure_repeats=(10,),
    failure_rates=(0.05, 0.15),
    failure_reps=10,
    wording_repeats=(10,),
    wording_reps=10,
    validation_every=24,
    validation_reps=5,
    resample_seeds=5,
    matcher_trials=20,
    matcher_spreads=(0.10, 0.20),
    matcher_chunk=10,
)


# --- the tasks ----------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Task:
    family: str
    key: str
    chunk: int
    params: tuple[tuple[str, Any], ...]

    @property
    def seed(self) -> int:
        return comparison_seed(SEED_ROOT, f"{self.family}|{self.key}|{self.chunk}")

    def get(self, name: str) -> Any:
        return dict(self.params)[name]


def _task(family: str, key: str, chunk: int = 0, **params: Any) -> Task:
    return Task(family, key, chunk, tuple(sorted(params.items())))


@cache
def pmf(mean: float, sigma: float, pi: float, grid: int = S1_GRID) -> np.ndarray | None:
    return share_pmf(round(mean, 10), sigma, pi, grid)


def pair(
    mu: float, d: float, sigma: float, pi: float, grid: int = S1_GRID
) -> tuple[float, float] | None:
    """The two sides' means for base ``mu`` and difference ``d``: (mu + d, mu) when both exist, else
    (mu, mu - d); the first is the higher."""
    for high, low in ((mu + d, mu), (mu, mu - d)):
        high, low = round(high, 10), round(low, 10)
        if pmf(high, sigma, pi, grid) is not None and pmf(low, sigma, pi, grid) is not None:
            return high, low
    return None


def _chunks(total: int, size: int) -> list[int]:
    return [min(size, total - start) for start in range(0, total, size)]


def _share_key(mu: float, sigma: float, pi: float, d: float, n: int) -> str:
    return f"mu={mu:g}|sigma={sigma:g}|pi={pi:g}|d={d:g}|n={n}"


AGREE_CONFIGS: tuple[tuple[str, str, float, float], ...] = (
    # (name, kind, first's rate at the boundary or interior value, second's)
    ("bernoulli a=1 vs 1", "bernoulli", 1.0, 1.0),
    ("bernoulli a=0.98 vs 0.98", "bernoulli", 0.98, 0.98),
    ("bernoulli a=0.95 vs 0.95", "bernoulli", 0.95, 0.95),
    ("bernoulli a=0.9 vs 0.9", "bernoulli", 0.9, 0.9),
    ("bernoulli a=0.8 vs 0.8", "bernoulli", 0.8, 0.8),
    ("bernoulli a=1 vs 0.9", "bernoulli", 1.0, 0.9),
    ("bernoulli a=0.98 vs 0.88", "bernoulli", 0.98, 0.88),
    ("bernoulli a=0.95 vs 0.85", "bernoulli", 0.95, 0.85),
    ("bernoulli a=0.9 vs 0.8", "bernoulli", 0.9, 0.8),
    ("mixture a=1 vs 1", "mixture", 1.0, 1.0),
    ("mixture a=0.95 vs 0.95", "mixture", 0.95, 0.95),
    ("mixture a=0.9 vs 0.9", "mixture", 0.9, 0.9),
    ("mixture a=1 vs 0.8", "mixture", 1.0, 0.8),
    ("mixture a=0.95 vs 0.75", "mixture", 0.95, 0.75),
    ("mixture a=0.9 vs 0.7", "mixture", 0.9, 0.7),
    ("interior a=1 vs 1", "interior", 1.0, 1.0),
    ("interior a=1 vs 5/6", "interior", 1.0, 5 / 6),
)


def agree_pmf(kind: str, a: float) -> np.ndarray:
    """Near-all-agree distributions on S1's lattice. ``bernoulli``: 1 with probability ``a``, else 0.
    ``mixture``: 1 with probability ``a``, else a rounded Beta with mean 0.5 and sd 0.15. ``interior``: 100
    of 125 (0.8) with probability ``a``, else 25 of 125 (0.2): an all-agree away from the boundary."""
    out = np.zeros(S1_GRID + 1)
    if kind == "bernoulli":
        out[S1_GRID], out[0] = a, 1 - a
    elif kind == "mixture":
        beta = pmf(0.5, 0.15, 0.0)
        assert beta is not None
        out = (1 - a) * beta
        out[S1_GRID] += a
    elif kind == "interior":
        out[100], out[25] = a, 1 - a
    else:
        raise ValueError(kind)
    result: np.ndarray = out / out.sum()
    return result


WORDING_CONFIGS = (
    ("none", 0.0),
    ("shared", 0.03),
    ("shared", 0.05),
    ("reversed", 0.03),
    ("reversed", 0.05),
    ("reversed", 0.10),
)


def wording_means(m: float, mode: str, s: float, side: int) -> tuple[float, float, float]:
    """Per-wording means: ``shared`` shifts both objectives by (-s, 0, +s); ``reversed`` shifts the first
    by (-s, 0, +s) and the second by (+s, 0, -s)."""
    sign = -1 if (mode == "reversed" and side == 1) else 1
    return tuple(round(m + sign * k * s, 10) for k in (-1, 0, 1))  # type: ignore[return-value]


def build_tasks(plan: Plan) -> list[Task]:
    tasks: list[Task] = []
    # 1. the share grid, exact bootstrap, S1's lattice
    for mu in plan.share_mu:
        for sigma in plan.share_sigma:
            for pi in plan.share_pi:
                for d in plan.share_d:
                    for n in plan.repeats:
                        reps = plan.share_reps_null_threshold if d in (0.0, T) else plan.share_reps
                        key = _share_key(mu, sigma, pi, d, n)
                        for i, size in enumerate(_chunks(reps, plan.chunk)):
                            tasks.append(
                                _task(
                                    "share_grid",
                                    key,
                                    i,
                                    mu=mu,
                                    sigma=sigma,
                                    pi=pi,
                                    d=d,
                                    n=n,
                                    reps=size,
                                )
                            )
    # 2. the repeat rule's n: power at 1.5 T and "no split reachable" at 0
    for mu in plan.share_mu:
        for sigma in plan.share_sigma:
            for pi in plan.share_pi:
                for target in ("power", "reachable"):
                    key = f"mu={mu:g}|sigma={sigma:g}|pi={pi:g}|{target}"
                    tasks.append(
                        _task(
                            "rule_n",
                            key,
                            mu=mu,
                            sigma=sigma,
                            pi=pi,
                            target=target,
                            reps=plan.rule_reps,
                        )
                    )
    # 3. near-all-agree (decision 10), with the candidates
    configs = AGREE_CONFIGS if plan.mode == "full" else (AGREE_CONFIGS[0], AGREE_CONFIGS[5])
    for name, kind, a1, a2 in configs:
        for n in plan.agree_repeats:
            key = f"{name}|n={n}"
            for i, size in enumerate(_chunks(plan.agree_reps, plan.chunk)):
                tasks.append(_task("all_agree", key, i, kind=kind, a1=a1, a2=a2, n=n, reps=size))
    # 4. choice rates, exact
    for p in plan.choice_p:
        for d in plan.choice_d:
            for n in plan.repeats:
                high, low = (p + d, p) if p + d <= 1 + 1e-12 else (p, p - d)
                key = f"p={p:g}|d={d:g}|n={n}"
                tasks.append(
                    _task("choice_grid", key, high=round(high, 10), low=round(low, 10), n=n)
                )
    for high, low in ((0.65, 0.35), (0.675, 0.325)):
        tasks.append(_task("choice_stated", f"{high:g} vs {low:g}|n=20", high=high, low=low, n=20))
    # 5. the stated share power point (planning/07 section 8): 15 points at sd 0.15, about 10 per wording
    for i, size in enumerate(_chunks(plan.share_reps_null_threshold, plan.chunk)):
        tasks.append(
            _task(
                "share_stated",
                "0.575 vs 0.425|sigma=0.15|pi=0|n=10",
                i,
                high=0.575,
                low=0.425,
                sigma=0.15,
                pi=0.0,
                n=10,
                reps=size,
            )
        )
    # 6. a finer lattice (1/1000, standing in for S2's continuous share) at a slice of the grid
    full = plan.mode == "full"
    for mu in (0.3, 0.5) if full else (0.5,):
        for sigma in (0.05, 0.15, 0.25) if full else (0.15,):
            for pi in (0.0, 0.5) if full else (0.0,):
                for d in (0.0, T) if full else (0.0,):
                    for n in (6, 20) if full else (6,):
                        key = _share_key(mu, sigma, pi, d, n)
                        for i, size in enumerate(_chunks(plan.fine_reps, plan.chunk)):
                            tasks.append(
                                _task(
                                    "share_fine",
                                    key,
                                    i,
                                    mu=mu,
                                    sigma=sigma,
                                    pi=pi,
                                    d=d,
                                    n=n,
                                    reps=size,
                                )
                            )
    # 7. a wording shift shared by both objectives (exact)
    for d in (0.0, T):
        for n in (10, 20) if plan.mode == "full" else (10,):
            for s in (0.03, 0.05) if plan.mode == "full" else (0.05,):
                key = f"d={d:g}|n={n}|shared s={s:g}"
                for i, size in enumerate(_chunks(plan.shift_reps, plan.chunk)):
                    tasks.append(_task("shift_shared", key, i, d=d, n=n, s=s, reps=size))
    # 8. failures and the worst-case bound (the engine itself)
    for sigma in plan.failure_sigma:
        for d in (0.0, T, 1.5 * T):
            for n in plan.failure_repeats:
                settings = [(0.0, "random")] + [
                    (rate, pattern)
                    for rate in plan.failure_rates
                    for pattern in ("random", "one_objective")
                ]
                for rate, pattern in settings:
                    key = f"sigma={sigma:g}|d={d:g}|n={n}|rate={rate:g}|{pattern}"
                    for i, size in enumerate(_chunks(plan.failure_reps, 100)):
                        tasks.append(
                            _task(
                                "failures",
                                key,
                                i,
                                sigma=sigma,
                                d=d,
                                n=n,
                                rate=rate,
                                pattern=pattern,
                                reps=size,
                            )
                        )
    # 9. the wording rule (the engine itself)
    configs_w = WORDING_CONFIGS if plan.mode == "full" else (WORDING_CONFIGS[0], WORDING_CONFIGS[5])
    for d in (0.10, 0.15, 0.20):
        for mode, s in configs_w:
            for n in plan.wording_repeats:
                key = f"d={d:g}|{mode} s={s:g}|n={n}"
                for i, size in enumerate(_chunks(plan.wording_reps, 100)):
                    tasks.append(_task("wording", key, i, d=d, mode=mode, s=s, n=n, reps=size))
    # 10. the exact bootstrap against the engine
    points = [
        (mu, sigma, pi, d, n)
        for mu in (0.1, 0.5, 0.9)
        for sigma in (0.02, 0.15, 0.25)
        for pi in (0.0, 0.5)
        for d in (0.0, T)
        for n in (6, 20)
    ][:: plan.validation_every]
    for mu, sigma, pi, d, n in points:
        tasks.append(
            _task(
                "validation",
                _share_key(mu, sigma, pi, d, n),
                mu=mu,
                sigma=sigma,
                pi=pi,
                d=d,
                n=n,
                reps=plan.validation_reps,
            )
        )
    # 11. the resample count (section 14.3)
    for which in ("split near its boundary", "no split near its boundary"):
        tasks.append(_task("resamples", which, which=which, seeds=plan.resample_seeds))
    # 12. the matcher
    tasks += matcher_tasks(plan)
    return tasks


def matcher_tasks(plan: Plan) -> list[Task]:
    from horizon_compact.experiment import load_experiment

    exp = load_experiment("company")
    tasks = []
    for shape in ("s1", "s2", "s3", "s4"):
        scenario = exp.get_scenario(shape)
        dims = len(scenario.offered()) + (1 if scenario.choice else 0)
        kinds = ["identical", "opposite", "true_match"]
        if scenario.choice:
            kinds.insert(2, "same_choice_opposite_money")
        cells: list[tuple[str, int | None]] = [(kind, None) for kind in kinds]
        ks = range(1, dims + 1) if plan.mode == "full" else (1, dims)
        cells += [("sparse", k) for k in ks]
        for sigma in plan.matcher_spreads:
            for kind, k in cells:
                key = f"{shape}|{kind}|sigma={sigma:g}|k={k}"
                for i, start in enumerate(range(0, plan.matcher_trials, plan.matcher_chunk)):
                    stop = min(plan.matcher_trials, start + plan.matcher_chunk)
                    tasks.append(
                        _task(
                            "matcher",
                            key,
                            i,
                            shape=shape,
                            kind=kind,
                            sigma=sigma,
                            k=k,
                            start=start,
                            stop=stop,
                        )
                    )
    return tasks


# --- running one task ---------------------------------------------------------------------------------------


def _uniform(p: np.ndarray) -> list[np.ndarray]:
    return [p, p, p]


def _required(p: np.ndarray | None) -> np.ndarray:
    if p is None:
        raise ValueError("no distribution for this point")
    return p


def _resample_dataset(
    which: str,
) -> tuple[dict[str, list[float]], dict[str, list[float]], dict[str, Any]]:
    """The fixed data set for section 14.3: from 2,000 replicates at a typical point, the one at the 5th
    percentile of its verdict's margin (close to the boundary, not the closest)."""
    sigma, n = 0.15, 10
    high, low = (0.55, 0.45) if which.startswith("split") else (0.5, 0.5)
    rng = np.random.Generator(
        np.random.PCG64(comparison_seed(SEED_ROOT, f"resamples|{which}|data"))
    )
    first = draw(_required(pmf(high, sigma, 0.0)), (2000, 3, n), rng)
    second = draw(_required(pmf(low, sigma, 0.0)), (2000, 3, n), rng)
    ex = exact_intervals(first, second, grid=S1_GRID, alpha=ALPHA)
    margins = []
    for r in range(2000):
        verdict = decide(float(ex.estimate[r]), float(ex.low[r]), float(ex.high[r]), T).verdict
        if which.startswith("split") and verdict == "split" and ex.estimate[r] > 0:
            margins.append((float(ex.low[r]), r))
        if which.startswith("no split") and verdict == "no_split":
            margins.append((min(T - float(ex.high[r]), float(ex.low[r]) + T), r))
    margins.sort()
    margin, r = margins[max(0, math.ceil(0.05 * len(margins)) - 1)]
    cells_first = {w: [float(v) / S1_GRID for v in first[r, i]] for i, w in enumerate(real.W3)}
    cells_second = {w: [float(v) / S1_GRID for v in second[r, i]] for i, w in enumerate(real.W3)}
    meta = {
        "point": f"{high:g} vs {low:g}|sigma={sigma:g}|pi=0|n={n}",
        "replicate": r,
        "candidates": len(margins),
        "exact_margin": margin,
        "exact_interval": [float(ex.low[r]), float(ex.high[r])],
        "estimate": float(ex.estimate[r]),
        "values_first": {w: [int(v) for v in first[r, i]] for i, w in enumerate(real.W3)},
        "values_second": {w: [int(v) for v in second[r, i]] for i, w in enumerate(real.W3)},
    }
    return cells_first, cells_second, meta


def run_task(task: Task) -> tuple[str, str, int, dict[str, Any]]:
    g = task.get
    family = task.family
    if family in ("share_grid", "share_fine"):
        grid = S1_GRID if family == "share_grid" else FINE_GRID
        sides = pair(g("mu"), g("d"), g("sigma"), g("pi"), grid)
        if sides is None:
            return (
                family,
                task.key,
                task.chunk,
                {"skipped": "no distribution has these means and spread"},
            )
        high, low = sides
        result = verdicts.share_point(
            _uniform(_required(pmf(high, g("sigma"), g("pi"), grid))),
            _uniform(_required(pmf(low, g("sigma"), g("pi"), grid))),
            n=g("n"),
            reps=g("reps"),
            seed=task.seed,
            grid=grid,
        )
        result["means"] = [high, low]
    elif family == "share_stated":
        result = verdicts.share_point(
            _uniform(_required(pmf(g("high"), g("sigma"), g("pi")))),
            _uniform(_required(pmf(g("low"), g("sigma"), g("pi")))),
            n=g("n"),
            reps=g("reps"),
            seed=task.seed,
            grid=S1_GRID,
        )
    elif family == "rule_n":
        result = _rule_n(task)
    elif family == "all_agree":
        result = verdicts.share_point(
            _uniform(agree_pmf(g("kind"), g("a1"))),
            _uniform(agree_pmf(g("kind"), g("a2"))),
            n=g("n"),
            reps=g("reps"),
            seed=task.seed,
            grid=S1_GRID,
        )
        result["means"] = [pmf_mean_sd(agree_pmf(g("kind"), a))[0] for a in (g("a1"), g("a2"))]
    elif family in ("choice_grid", "choice_stated"):
        result = verdicts.choice_point(g("high"), g("low"), n=g("n"))
        result["rates"] = [g("high"), g("low")]
    elif family == "shift_shared":
        high, low = (0.55, 0.45) if g("d") else (0.5, 0.5)
        means = [wording_means(m, "shared", g("s"), side) for side, m in enumerate((high, low))]
        result = verdicts.share_point(
            [_required(pmf(m, 0.15, 0.0)) for m in means[0]],
            [_required(pmf(m, 0.15, 0.0)) for m in means[1]],
            n=g("n"),
            reps=g("reps"),
            seed=task.seed,
            grid=S1_GRID,
        )
        result["wording_means"] = means
    elif family == "failures":
        d = g("d")
        high, low = round(0.5 + d / 2, 10), round(0.5 - d / 2, 10)
        result = real.failure_point(
            _required(pmf(high, g("sigma"), 0.0)),
            _required(pmf(low, g("sigma"), 0.0)),
            n=g("n"),
            rate=g("rate"),
            pattern=g("pattern"),
            reps=g("reps"),
            seed=task.seed,
            key=f"{task.key}|{task.chunk}",
        )
    elif family == "wording":
        d = g("d")
        high, low = round(0.5 + d / 2, 10), round(0.5 - d / 2, 10)
        means = [wording_means(m, g("mode"), g("s"), side) for side, m in enumerate((high, low))]
        result = real.wording_point(
            [_required(pmf(m, 0.10, 0.0)) for m in means[0]],
            [_required(pmf(m, 0.10, 0.0)) for m in means[1]],
            n=g("n"),
            reps=g("reps"),
            seed=task.seed,
            key=f"{task.key}|{task.chunk}",
        )
        result["wording_means"] = means
        result["true_wording_differences"] = [
            round(a - b, 10) for a, b in zip(means[0], means[1], strict=True)
        ]
    elif family == "validation":
        sides = pair(g("mu"), g("d"), g("sigma"), g("pi"))
        if sides is None:
            return (
                family,
                task.key,
                task.chunk,
                {"skipped": "no distribution has these means and spread"},
            )
        result = real.validation_point(
            _required(pmf(sides[0], g("sigma"), g("pi"))),
            _required(pmf(sides[1], g("sigma"), g("pi"))),
            n=g("n"),
            reps=g("reps"),
            seed=task.seed,
            key=task.key,
        )
    elif family == "resamples":
        cells_first, cells_second, meta = _resample_dataset(g("which"))
        result = {
            **meta,
            "by_resamples": real.resample_point(
                cells_first,
                cells_second,
                seeds=g("seeds"),
                resamples=(10_000, RESAMPLES),
                key=task.key,
            ),
        }
    elif family == "matcher":
        result = matcher_sim.run_trials(
            g("shape"), g("kind"), g("sigma"), g("k"), range(g("start"), g("stop"))
        )
    else:  # pragma: no cover
        raise ValueError(family)
    return family, task.key, task.chunk, result


def _rule_n(task: Task) -> dict[str, Any]:
    g = task.get
    mu, sigma, pi = g("mu"), g("sigma"), g("pi")
    if g("target") == "power":
        sides = pair(mu, 1.5 * T, sigma, pi)
    else:
        sides = (mu, mu) if pmf(mu, sigma, pi) is not None else None
    if sides is None:
        return {"skipped": "no distribution has these means and spread"}
    high, low = sides
    p_high, p_low = _required(pmf(high, sigma, pi)), _required(pmf(low, sigma, pi))
    sd = math.sqrt((pmf_mean_sd(p_high)[1] ** 2 + pmf_mean_sd(p_low)[1] ** 2) / 2)
    rule = share_repeats("s1", sd, 0, T)
    result = verdicts.share_point(
        _uniform(p_high),
        _uniform(p_low),
        n=rule.repeats,
        reps=g("reps"),
        seed=task.seed,
        grid=S1_GRID,
    )
    result.update(
        means=[high, low],
        pooled_sd=sd,
        n=rule.repeats,
        n_power=rule.n_power,
        n_both_reachable=rule.n_both_reachable,
        cap_binds=rule.cap_binds,
    )
    return result


# --- merging, and the file ----------------------------------------------------------------------------------


def _merge_share(parts: list[dict[str, Any]]) -> dict[str, Any]:
    """Chunks of one share point, in chunk order: counts added, the mean half-width weighted by replicates."""
    if "skipped" in parts[0]:
        return parts[0]
    out = {k: v for k, v in parts[0].items() if k not in ("seed",)}
    out["seeds"] = [p["seed"] for p in parts]
    out["reps"] = sum(p["reps"] for p in parts)
    for name in ("verdicts", "c1_rule", "c1_combined", "c2_rule", "c2_combined"):
        out[name] = {v: sum(p[name][v] for p in parts) for v in verdicts.VERDICTS}
    for name in ("split_wrong_sign", "no_split_degenerate", "no_split_narrow"):
        out[name] = sum(p[name] for p in parts)
    out["mean_half_width"] = sum(p["mean_half_width"] * p["reps"] for p in parts) / out["reps"]
    out["end_near_a_boundary"] = {
        k: sum(p["end_near_a_boundary"][k] for p in parts) for k in parts[0]["end_near_a_boundary"]
    }
    return out


def _merge_counts(parts: list[dict[str, Any]]) -> dict[str, Any]:
    """Chunks of an engine family: every count added, mean kept wordings weighted by replicates."""
    out: dict[str, Any] = {
        "reps": sum(p["reps"] for p in parts),
        "seeds": [p["seed"] for p in parts],
    }
    for name, value in parts[0].items():
        if name in ("reps", "seed"):
            continue
        if isinstance(value, dict):
            keys = sorted({k for p in parts for k in p[name]})
            out[name] = {k: sum(p[name].get(k, 0) for p in parts) for k in keys}
        elif name == "mean_kept_wordings":
            out[name] = sum(p[name] * p["reps"] for p in parts) / out["reps"]
        elif isinstance(value, int) and not isinstance(value, bool):
            out[name] = sum(p[name] for p in parts)
        else:
            out[name] = value
    return out


def _matcher_summary(records: dict[str, dict[str, list[Any]]], plan: Plan) -> dict[str, Any]:
    by_shape: dict[str, Any] = {}
    for shape in ("s1", "s2", "s3", "s4"):
        mine = {k: v for k, v in records.items() if k.startswith(f"{shape}|")}
        widest = max(plan.matcher_spreads)
        design = (
            matcher_sim.DESIGN_SPREAD
            if matcher_sim.DESIGN_SPREAD in plan.matcher_spreads
            else widest
        )
        true_widest = mine[f"{shape}|true_match|sigma={widest:g}|k=None"]["nearest"]
        d = matcher_sim.d_star(true_widest)
        identification = {
            int(key.split("|k=")[1]): float(np.mean(v["identified"]))
            for key, v in mine.items()
            if "|sparse|" in key and f"sigma={design:g}|" in key
        }
        k = matcher_sim.k_star(identification)
        k_applied = k if k is not None else max(identification) + 1
        cells = {}
        for key in sorted(mine):
            v = mine[key]
            _, kind, sigma_part, k_part = key.split("|")
            cells[key] = {
                "kind": kind,
                "sigma": float(sigma_part.split("=")[1]),
                "k": None if k_part == "k=None" else int(k_part.split("=")[1]),
                "trials": len(v["nearest"]),
                "identified": int(sum(v["identified"])),
                "labels": matcher_sim.labels(v, d, k_applied),
                "nearest": matcher_sim.summary(v["nearest"]),
                "generating": matcher_sim.summary(v["generating"]),
                "unmatchable": int(sum(v["unmatchable"])),
                "nearest_above_d_star": int(sum(1 for x in v["nearest"] if x > d + 1e-9)),
                "generating_above_d_star": int(sum(1 for x in v["generating"] if x > d + 1e-9)),
            }
        by_shape[shape] = {
            "d_star": d,
            "d_star_from": f"{shape}|true_match|sigma={widest:g}|k=None",
            "k_star": k,
            "identification_by_k_at_design_spread": {
                str(kk): identification[kk] for kk in sorted(identification)
            },
            "design_spread": design,
            "cells": cells,
        }
    return by_shape


def code_hash(root: Path) -> tuple[str, int]:
    """sha256 over what the results depend on: the analysis package, the simulation package except its
    report (which only formats the results), the company experiment and uv.lock."""
    files = sorted(
        [
            *root.glob("src/horizon_compact/analysis/*.py"),
            *(p for p in root.glob("src/horizon_compact/simulation/*.py") if p.name != "report.py"),
            *(p for p in root.glob("experiment/company/**/*") if p.is_file()),
            root / "uv.lock",
        ]
    )
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest(), len(files)


def run(
    plan: Plan,
    out: Path,
    *,
    root: Path,
    workers: int,
    log: Callable[[str], None] = print,
) -> dict[str, Any]:
    import scipy
    import statsmodels

    tasks = build_tasks(plan)
    log(f"{len(tasks)} tasks, {workers} workers, mode {plan.mode}")
    started = time.perf_counter()
    results: dict[str, dict[str, dict[int, dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    elapsed: dict[str, float] = defaultdict(float)
    done = 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_timed, task): task for task in tasks}
        for future in as_completed(futures):
            (family, key, chunk, result), seconds = future.result()
            results[family][key][chunk] = result
            elapsed[family] += seconds
            done += 1
            if done % max(1, len(tasks) // 20) == 0 or done == len(tasks):
                log(f"  {done}/{len(tasks)} tasks, {time.perf_counter() - started:.0f} s")
    wall = time.perf_counter() - started
    log(f"done in {wall:.0f} s wall; CPU seconds by family:")
    for family in sorted(elapsed):
        log(f"  {family:15s} {elapsed[family]:9.0f}")

    def merged(
        family: str, merge: Callable[[list[dict[str, Any]]], dict[str, Any]]
    ) -> dict[str, Any]:
        return {
            key: merge([chunks[i] for i in sorted(chunks)])
            for key, chunks in sorted(results[family].items())
        }

    def single(family: str) -> dict[str, Any]:
        return {key: chunks[0] for key, chunks in sorted(results[family].items())}

    matcher_records: dict[str, dict[str, list[Any]]] = {}
    for key, chunks in sorted(results["matcher"].items()):
        matcher_records[key] = {
            name: [x for i in sorted(chunks) for x in chunks[i][name]] for name in chunks[0]
        }
    sha, count = code_hash(root)
    document = {
        "simulation_version": SIMULATION_VERSION,
        "results_version": RESULTS_VERSION,
        "mode": plan.mode,
        "code_sha256": sha,
        "code_files": count,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        "libraries": {
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "statsmodels": statsmodels.__version__,
        },
        "constants": {
            "alpha": ALPHA,
            "z": Z,
            "resamples": RESAMPLES,
            "share_threshold": SHARE_THRESHOLD,
            "choice_threshold": CHOICE_THRESHOLD,
            "match_resamples": matcher_sim.MATCH_RESAMPLES,
            "seed_root": SEED_ROOT,
        },
        "families": {
            "share_grid": merged("share_grid", _merge_share),
            "rule_n": single("rule_n"),
            "all_agree": merged("all_agree", _merge_share),
            "choice_grid": single("choice_grid"),
            "choice_stated": single("choice_stated"),
            "share_stated": merged("share_stated", _merge_share),
            "share_fine": merged("share_fine", _merge_share),
            "shift_shared": merged("shift_shared", _merge_share),
            "failures": merged("failures", _merge_counts),
            "wording": merged("wording", _merge_counts),
            "validation": single("validation"),
            "resamples": single("resamples"),
        },
        "matcher": _matcher_summary(matcher_records, plan),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(document, indent=1) + "\n", encoding="utf-8")
    log(f"wrote {out}")
    return document


def _timed(task: Task) -> tuple[tuple[str, str, int, dict[str, Any]], float]:
    started = time.perf_counter()
    result = run_task(task)
    return result, time.perf_counter() - started


def default_workers() -> int:
    return max(1, min(12, (os.cpu_count() or 2) - 2))


def count_by_family(tasks: Iterable[Task]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for task in tasks:
        counts[task.family] += 1
    return dict(sorted(counts.items()))
