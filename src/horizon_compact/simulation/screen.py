"""Step 12's screening of the share interval (Phase 3 IMPLEMENTATION doc §20a findings 1-3).

Step 10 found the percentile bootstrap too narrow: false splits up to 2.2% against a 0.3125% target. This
screens candidate replacements on the same distributions, on every null, threshold and power point of
§14.1's share grid and on the near-all-agree family, so the choice is made on evidence and before any result
exists. Each candidate's verdict is the analysis's own ``verdict.decide`` on the candidate's interval; one
draw of replicates is shared by all candidates, so they are compared on identical data.

The candidates, for three wordings of ``n`` runs per cell and both objectives:

- ``percentile``: the rule as written (the exact bootstrap at ``ALPHA``).
- ``expanded``: the percentile interval at a wider level (Hesterberg's small-sample correction): the level
  whose normal quantile is ``sqrt(n / (n - 1)) * t(1 - ALPHA / 2, df)``, with ``df`` the within-cell degrees
  of freedom of both objectives, ``6 (n - 1)``. It corrects the bootstrap's two known small-sample faults:
  resampling shrinks a cell's variance by ``(n - 1) / n``, and a normal quantile is used where a t quantile
  belongs.
- ``welch``: the difference plus or minus ``t(1 - ALPHA / 2, df) * SE``, with ``SE`` from the cells' sample
  variances (``SE^2 = sum over cells of s^2 / (9 n)``) and Welch-Satterthwaite degrees of freedom.
- each of the above with ``+floor``: decision 10's rule, a comparison whose interval is narrower than one
  step of the outcome's lattice (1/125 for S1) is never a "no split" (it becomes inconclusive);
- and with ``+floor+const``: also, when every run of either objective sits at one value, the share of runs
  at that value is tested by Newcombe at the share threshold and the less certain of the two verdicts is
  kept (decision 10's candidate, widened from boundary values to any value and from both objectives to
  either)."""

from __future__ import annotations

import json
import math
from collections import Counter
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from horizon_compact.analysis.intervals import ALPHA, comparison_seed
from horizon_compact.analysis.outcomes import SHARE_THRESHOLD
from horizon_compact.analysis.verdict import decide
from horizon_compact.simulation.exact import S1_GRID, draw, exact_intervals_at
from horizon_compact.simulation.runner import AGREE_CONFIGS, FULL, agree_pmf, pair, pmf
from horizon_compact.simulation.verdicts import less_certain, newcombe_verdict

SEED_ROOT = "phase-3-step-12-screen"
T = SHARE_THRESHOLD
FLOOR = 1 / S1_GRID
BASES = ("percentile", "expanded", "welch")
CANDIDATES = tuple(f"{b}{s}" for b in BASES for s in ("", "+floor", "+floor+const"))
VERDICTS = ("split", "no_split", "inconclusive")


def expanded_alpha(n: int, alpha: float = ALPHA, wordings: int = 3) -> float:
    """The level at which the percentile interval is read for the expanded interval."""
    df = 2 * wordings * (n - 1)
    z = math.sqrt(n / (n - 1)) * float(stats.t.ppf(1 - alpha / 2, df))
    return float(2 * stats.norm.sf(z))


def welch_intervals(
    first: np.ndarray, second: np.ndarray, grid: int, alpha: float = ALPHA
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per replicate: the difference of the mean of wording means, and the Welch interval's ends."""
    _, wordings, n = first.shape
    a, b = first / grid, second / grid
    d = a.mean(axis=2).mean(axis=1) - b.mean(axis=2).mean(axis=1)
    parts = np.concatenate([a.var(axis=2, ddof=1), b.var(axis=2, ddof=1)], axis=1) / (
        wordings**2 * n
    )
    se2 = parts.sum(axis=1)
    denom = (parts**2 / (n - 1)).sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        df = np.where(denom > 0, se2**2 / denom, 2 * wordings * (n - 1))
    half = stats.t.ppf(1 - alpha / 2, np.maximum(df, 1.0)) * np.sqrt(se2)
    return d, d - half, d + half


def _constant_value(first: np.ndarray, second: np.ndarray) -> int | None:
    """The value every run of one objective sits at (the first objective's, if both are constant), or None."""
    for side in (first, second):
        if np.all(side == side.flat[0]):
            return int(side.flat[0])
    return None


def screen_point(
    first_pmfs: list[np.ndarray], second_pmfs: list[np.ndarray], n: int, reps: int, seed: int
) -> dict[str, Any]:
    rng = np.random.Generator(np.random.PCG64(seed))
    first = np.stack([draw(p, (reps, n), rng) for p in first_pmfs], axis=1)
    second = np.stack([draw(p, (reps, n), rng) for p in second_pmfs], axis=1)
    a_exp = expanded_alpha(n)
    exact = exact_intervals_at(first, second, grid=S1_GRID, alphas=(ALPHA, a_exp))
    welch = welch_intervals(first, second, S1_GRID)
    ends: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {
        "percentile": (exact[ALPHA].estimate, exact[ALPHA].low, exact[ALPHA].high),
        "expanded": (exact[a_exp].estimate, exact[a_exp].low, exact[a_exp].high),
        "welch": welch,
    }
    counts: dict[str, Counter[str]] = {c: Counter() for c in CANDIDATES}
    big_n = 3 * n
    constant = [_constant_value(first[r], second[r]) for r in range(reps)]
    for base, (d, lo, hi) in ends.items():
        for r in range(reps):
            verdict = decide(float(d[r]), float(lo[r]), float(hi[r]), T).verdict
            counts[base][verdict] += 1
            floored: str = (
                "inconclusive" if verdict == "no_split" and hi[r] - lo[r] < FLOOR else verdict
            )
            counts[f"{base}+floor"][floored] += 1
            value = constant[r]
            if value is not None:
                k1, k2 = int((first[r] == value).sum()), int((second[r] == value).sum())
                floored = less_certain(floored, newcombe_verdict(k1, big_n, k2, big_n, T))
            counts[f"{base}+floor+const"][floored] += 1
    return {
        "reps": reps,
        "seed": str(seed),
        "expanded_alpha": a_exp,
        "verdicts": {c: {v: counts[c][v] for v in VERDICTS} for c in CANDIDATES},
    }


def _task(spec: tuple[str, str, dict[str, Any]]) -> tuple[str, str, dict[str, Any]]:
    family, key, p = spec
    seed = comparison_seed(SEED_ROOT, f"{family}|{key}")
    if family == "grid":
        sides = pair(p["mu"], p["d"], p["sigma"], p["pi"])
        if sides is None:
            return family, key, {"skipped": True}
        a, b = pmf(sides[0], p["sigma"], p["pi"]), pmf(sides[1], p["sigma"], p["pi"])
        assert a is not None and b is not None
        return family, key, screen_point([a] * 3, [b] * 3, p["n"], p["reps"], seed)
    a, b = agree_pmf(p["kind"], p["a1"]), agree_pmf(p["kind"], p["a2"])
    return family, key, screen_point([a] * 3, [b] * 3, p["n"], p["reps"], seed)


def specs(reps_null: int = 4000, reps_power: int = 2000) -> list[tuple[str, str, dict[str, Any]]]:
    out: list[tuple[str, str, dict[str, Any]]] = []
    for mu in FULL.share_mu:
        for sigma in FULL.share_sigma:
            for pi in FULL.share_pi:
                for d in (0.0, T, 1.5 * T):
                    for n in FULL.repeats:
                        key = f"mu={mu:g}|sigma={sigma:g}|pi={pi:g}|d={d:g}|n={n}"
                        reps = reps_power if d > T else reps_null
                        out.append(
                            (
                                "grid",
                                key,
                                {"mu": mu, "sigma": sigma, "pi": pi, "d": d, "n": n, "reps": reps},
                            )
                        )
    for name, kind, a1, a2 in AGREE_CONFIGS:
        for n in FULL.agree_repeats:
            out.append(
                (
                    "agree",
                    f"{name}|n={n}",
                    {"kind": kind, "a1": a1, "a2": a2, "n": n, "reps": reps_null},
                )
            )
    return out


def summary(doc: dict[str, Any]) -> str:
    """``interval-screening.md``: each candidate against both targets, its power, and the near-all-agree
    family."""
    from horizon_compact.simulation.report import table, wilson

    target = 0.05 / 16

    def key(k: str) -> dict[str, str]:
        return dict(x.split("=", 1) for x in k.split("|") if "=" in x)

    grid = {k: p for k, p in doc["grid"].items() if "skipped" not in p}
    rows = []
    for c in doc["candidates"]:
        cells = []
        for d, verdict in (("0", "split"), ("0.1", "no_split")):
            points = [p for k, p in grid.items() if key(k)["d"] == d]
            rates = [p["verdicts"][c][verdict] / p["reps"] for p in points]
            clear = sum(wilson(p["verdicts"][c][verdict], p["reps"])[0] > target for p in points)
            cells.append(
                f"{sum(r > target for r in rates)} ({clear}); worst {100 * max(rates):.2f}%"
            )
        power = {
            n: sorted(
                p["verdicts"][c]["split"] / p["reps"]
                for k, p in grid.items()
                if key(k)["d"] == "0.15" and key(k)["n"] == n
            )
            for n in ("6", "10", "15", "20")
        }
        medians = ", ".join(f"{100 * v[len(v) // 2]:.0f}%" for v in power.values())
        same = [
            p["verdicts"][c]["split"] / p["reps"]
            for k, p in doc["agree"].items()
            if k.split("|")[0].split(" vs ")[0].split("=")[1] == k.split("|")[0].split(" vs ")[1]
        ]
        differ = [
            p["verdicts"][c]["no_split"] / p["reps"]
            for k, p in doc["agree"].items()
            if k.split("|")[0].split(" vs ")[0].split("=")[1] != k.split("|")[0].split(" vs ")[1]
        ]
        rows.append(
            [f"`{c}`", *cells, medians, f"{100 * max(differ):.2f}%", f"{100 * max(same):.2f}%"]
        )
    lines = [
        "# Phase 3 step 12: screening the share interval",
        "",
        "> Generated by `horizon_compact.simulation.screen` from `interval-screening.json`. Do not edit by hand.",
        "",
        "Every null (d = 0), threshold (d = T) and power (d = 1.5 T) point of section 14.1's share grid, 4,000",
        "replicates at the first two and 2,000 at the third, and the near-all-agree family at 4,000, each judged",
        f'by every candidate on the same draws. Target {100 * target:.4f}% per comparison; "clearly" means the',
        "95% Wilson interval's lower end is over it. With 360 points per row, about 9 would read clearly over",
        "by chance even at the target.",
        "",
        *table(
            [
                "Candidate",
                "False split at 0: points over (clearly)",
                "False no split at T: over (clearly)",
                "Power at 1.5 T, median at 6 / 10 / 15 / 20 per wording",
                "Near-all-agree: worst false no split at T",
                "Near-all-agree: worst false split at 0",
            ],
            rows,
        ),
        "",
    ]
    return "\n".join(lines)


def run(out: Path, workers: int = 10, log: Callable[[str], None] = print) -> dict[str, Any]:
    tasks = specs()
    log(f"{len(tasks)} screening points, {workers} workers")
    results: dict[str, dict[str, Any]] = {"grid": {}, "agree": {}}
    with ProcessPoolExecutor(workers) as pool:
        for family, key, result in pool.map(_task, tasks, chunksize=4):
            results[family][key] = result
    doc = {
        "alpha": ALPHA,
        "threshold": T,
        "floor": FLOOR,
        "candidates": list(CANDIDATES),
        "grid": dict(sorted(results["grid"].items())),
        "agree": dict(sorted(results["agree"].items())),
    }
    out.write_text(json.dumps(doc, separators=(",", ":")) + "\n", encoding="utf-8")
    out.with_suffix(".md").write_text(summary(doc), encoding="utf-8")
    log(f"wrote {out} and its summary")
    return doc


if __name__ == "__main__":  # pragma: no cover
    import sys

    if sys.argv[1] == "--summary":
        source = Path(sys.argv[2])
        source.with_suffix(".md").write_text(
            summary(json.loads(source.read_text(encoding="utf-8"))), encoding="utf-8"
        )
    else:
        run(Path(sys.argv[1]), workers=int(sys.argv[2]) if len(sys.argv) > 2 else 10)
