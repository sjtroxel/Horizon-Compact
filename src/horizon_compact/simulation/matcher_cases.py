"""The matcher's synthetic cases (Phase 3 IMPLEMENTATION doc section 13.4). Step 10 runs them at scale
(section 14.2) to set ``D_STAR`` and ``K_STAR``; this module only builds one case from a seed.

**Objective profiles are drawn at random, never guessed** (section 13.4): each objective's mean allocation is
a flat Dirichlet draw over the scenario's offered lines, and its choice probabilities a flat Dirichlet over
the options (for two options, a rate drawn uniformly, as the doc says). Each run's allocation is a Dirichlet
draw around the objective's mean, with a concentration chosen so that a line at the average share ``1/K``
has standard deviation ``sigma`` (``c = (1/K)(1 - 1/K) / sigma^2 - 1``, at least ``MIN_CONCENTRATION``); its
choice is drawn from the objective's probabilities, independently of the allocation (a simplification: in the
real scenarios the two are coupled, as S3's lines are by the choice).

The five case types, each built from the generating objective's profile:
1. ``identical``: the company's decision is the objective's mean allocation and modal choice;
2. ``opposite``: all the money on the line the objective funds least, and its least likely choice;
3. ``same_choice_opposite_money``: the modal choice, the opposite allocation;
4. ``sparse``: the identical case observed on only ``k`` of its dimensions, drawn at random (the choice is
   one dimension, each line one);
5. ``true_match``: one more draw from the objective's own run distribution.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np

from horizon_compact.analysis.matcher import CompanyDecision
from horizon_compact.analysis.records import RunRow
from horizon_compact.experiment import Scenario

CaseKind = Literal["identical", "opposite", "same_choice_opposite_money", "sparse", "true_match"]
CASE_KINDS: tuple[CaseKind, ...] = (
    "identical",
    "opposite",
    "same_choice_opposite_money",
    "sparse",
    "true_match",
)
OBJECTIVES = ("A", "B", "C", "D", "E")
WORDINGS = ("w1", "w2", "w3")
MIN_CONCENTRATION = 0.05
CHOICE_DIMENSION = "<choice>"
SWEEP_ID = "matcher-simulation"
MODEL_KEY = "synthetic"


@dataclass(frozen=True)
class Profile:
    objective_id: str
    mean: tuple[float, ...]  # over the offered lines, in file order; sums to 1
    choice_probs: tuple[
        float, ...
    ]  # over the options, in file order; empty when there is no choice


@dataclass(frozen=True)
class SyntheticCase:
    kind: CaseKind
    seed: int
    sigma: float
    repeats: int
    generating: str
    profiles: tuple[Profile, ...]
    rows: tuple[RunRow, ...]
    decision: CompanyDecision


def concentration(sigma: float, lines: int) -> float:
    """The Dirichlet concentration giving a line at share ``1/lines`` a standard deviation of ``sigma``."""
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    m = 1 / lines
    return max(MIN_CONCENTRATION, m * (1 - m) / sigma**2 - 1)


def _lines(scenario: Scenario) -> tuple[str, ...]:
    return tuple(lever.key for lever in scenario.offered())


def _options(scenario: Scenario) -> tuple[str, ...]:
    return tuple(option.key for option in scenario.choice.options) if scenario.choice else ()


def draw_profiles(
    scenario: Scenario, rng: np.random.Generator, objectives: Sequence[str] = OBJECTIVES
) -> tuple[Profile, ...]:
    k, options = len(_lines(scenario)), _options(scenario)
    profiles = []
    for objective in objectives:
        mean = rng.dirichlet(np.ones(k))
        probs = rng.dirichlet(np.ones(len(options))) if options else np.empty(0)
        profiles.append(
            Profile(objective, tuple(float(v) for v in mean), tuple(float(v) for v in probs))
        )
    return tuple(profiles)


def _draw_allocation(profile: Profile, sigma: float, rng: np.random.Generator) -> np.ndarray:
    c = concentration(sigma, len(profile.mean))
    alpha = np.maximum(np.asarray(profile.mean) * c, 1e-12)
    drawn: np.ndarray = rng.dirichlet(alpha)
    return drawn


def _draw_choice(scenario: Scenario, profile: Profile, rng: np.random.Generator) -> str | None:
    options = _options(scenario)
    if not options:
        return None
    return options[int(rng.choice(len(options), p=np.asarray(profile.choice_probs)))]


def draw_runs(
    scenario: Scenario,
    profiles: Sequence[Profile],
    sigma: float,
    repeats: int,
    rng: np.random.Generator,
    wordings: Sequence[str] = WORDINGS,
) -> tuple[RunRow, ...]:
    """``repeats`` valid runs per objective per wording, amounts in the scenario's units."""
    lines = _lines(scenario)
    rows = []
    n = 0
    for profile in profiles:
        for wording in wordings:
            for repeat in range(repeats):
                shares = _draw_allocation(profile, sigma, rng)
                choice = _draw_choice(scenario, profile, rng)
                amounts = {k: float(v) * scenario.total for k, v in zip(lines, shares, strict=True)}
                rows.append(
                    RunRow(
                        run_id=f"sim-{n:06d}",
                        sweep_id=SWEEP_ID,
                        model_key=MODEL_KEY,
                        scenario_id=scenario.id,
                        objective_id=profile.objective_id,
                        wording_id=wording,
                        repeat=repeat,
                        status="valid",
                        first_attempt_status="valid",
                        attempts=1,
                        possible_decline=False,
                        menu_order=(),
                        option_order=(),
                        amounts=amounts,
                        choice=choice,
                        first_amounts=amounts,
                        first_choice=choice,
                    )
                )
                n += 1
    return tuple(rows)


def _modal(scenario: Scenario, profile: Profile) -> str | None:
    options = _options(scenario)
    return options[int(np.argmax(profile.choice_probs))] if options else None


def _least_likely(scenario: Scenario, profile: Profile) -> str | None:
    options = _options(scenario)
    return options[int(np.argmin(profile.choice_probs))] if options else None


def _opposite_money(scenario: Scenario, profile: Profile) -> dict[str, float]:
    lines = _lines(scenario)
    least = int(np.argmin(profile.mean))
    return {k: (float(scenario.total) if i == least else 0.0) for i, k in enumerate(lines)}


def _mean_money(scenario: Scenario, profile: Profile) -> dict[str, float]:
    return {k: v * scenario.total for k, v in zip(_lines(scenario), profile.mean, strict=True)}


def sparse_decision(
    scenario: Scenario, full: CompanyDecision, k: int, rng: np.random.Generator
) -> CompanyDecision:
    """``full`` observed on ``k`` of its dimensions, chosen at random without replacement."""
    dims = list(full.amounts) + ([CHOICE_DIMENSION] if full.choice is not None else [])
    if not 1 <= k <= len(dims):
        raise ValueError(f"k must be between 1 and {len(dims)}, not {k}")
    kept = {dims[int(i)] for i in rng.choice(len(dims), size=k, replace=False)}
    return CompanyDecision(
        reading="primary",
        amounts={key: v for key, v in full.amounts.items() if key in kept},
        choice=full.choice if CHOICE_DIMENSION in kept else None,
    )


def build_case(
    scenario: Scenario,
    kind: CaseKind,
    *,
    seed: int,
    sigma: float,
    repeats: int,
    k: int | None = None,
    objectives: Sequence[str] = OBJECTIVES,
) -> SyntheticCase:
    """One synthetic case, fixed by its seed. The generating objective is drawn among ``objectives``."""
    if (kind == "sparse") != (k is not None):
        raise ValueError("k is given for a sparse case and only for one")
    rng = np.random.Generator(np.random.PCG64(seed))
    profiles = draw_profiles(scenario, rng, objectives)
    rows = draw_runs(scenario, profiles, sigma, repeats, rng)
    profile = profiles[int(rng.integers(len(profiles)))]
    if kind == "identical":
        decision = CompanyDecision(
            "primary", _mean_money(scenario, profile), _modal(scenario, profile)
        )
    elif kind == "opposite":
        decision = CompanyDecision(
            "primary", _opposite_money(scenario, profile), _least_likely(scenario, profile)
        )
    elif kind == "same_choice_opposite_money":
        decision = CompanyDecision(
            "primary", _opposite_money(scenario, profile), _modal(scenario, profile)
        )
    elif kind == "sparse":
        assert k is not None
        full = CompanyDecision("primary", _mean_money(scenario, profile), _modal(scenario, profile))
        decision = sparse_decision(scenario, full, k, rng)
    else:  # true_match
        shares = _draw_allocation(profile, sigma, rng)
        money = {
            k_: float(v) * scenario.total for k_, v in zip(_lines(scenario), shares, strict=True)
        }
        decision = CompanyDecision("primary", money, _draw_choice(scenario, profile, rng))
    return SyntheticCase(kind, seed, sigma, repeats, profile.objective_id, profiles, rows, decision)
