"""The matcher's synthetic cases (Phase 3 doc 13.4, step 9): each case type built as the doc defines it."""

from __future__ import annotations

import math
from collections import Counter

import numpy as np
import pytest

from horizon_compact.analysis.matcher import CompanyDecision, match_case
from horizon_compact.experiment import load_experiment
from horizon_compact.simulation.matcher_cases import (
    CASE_KINDS,
    CHOICE_DIMENSION,
    OBJECTIVES,
    CaseKind,
    build_case,
    concentration,
    draw_profiles,
    draw_runs,
    sparse_decision,
)

EXP = load_experiment("company")
S2 = EXP.get_scenario("s2")
S3 = EXP.get_scenario("s3")
S4 = EXP.get_scenario("s4")


def shares(decision: CompanyDecision, total: float) -> list[float]:
    return [v / total for v in decision.amounts.values()]


def test_concentration_by_hand() -> None:
    # K = 4, sigma 0.1: (1/4)(3/4) / 0.01 - 1 = 17.75;  K = 15, sigma 0.2: (1/15)(14/15) / 0.04 - 1 = 0.5556
    assert concentration(0.1, 4) == pytest.approx(17.75)
    assert concentration(0.2, 15) == pytest.approx(14 / 225 / 0.04 - 1)
    assert concentration(0.5, 2) == 0.05  # (1/2)(1/2) / 0.25 - 1 = 0: floored
    with pytest.raises(ValueError):
        concentration(0.0, 4)


def test_runs_have_the_stated_spread_around_the_mean() -> None:
    # K = 4 lines (S3), sigma 0.1. A line whose mean is m has variance m(1 - m) / (c + 1); at m = 1/4 that is
    # 0.1^2. Checked on the line nearest 1/4 over 6,000 draws, against its own formula.
    rng = np.random.Generator(np.random.PCG64(7))
    profiles = draw_profiles(S3, rng, ["A"])
    rows = draw_runs(S3, profiles, 0.1, 2000, rng)
    keys = [lever.key for lever in S3.offered()]
    mean = profiles[0].mean
    for i, key in enumerate(keys):
        values = np.array([r.amounts[key] / 190 for r in rows if r.amounts is not None])
        assert values.mean() == pytest.approx(mean[i], abs=0.01)
        expected_sd = math.sqrt(mean[i] * (1 - mean[i]) / (concentration(0.1, 4) + 1))
        assert values.std(ddof=1) == pytest.approx(expected_sd, rel=0.06)


def test_choices_follow_the_profile() -> None:
    rng = np.random.Generator(np.random.PCG64(3))
    profiles = draw_profiles(S3, rng, ["A"])
    rows = draw_runs(S3, profiles, 0.1, 3000, rng)
    counts = Counter(r.choice for r in rows)
    for option, p in zip(["close", "retool", "sell"], profiles[0].choice_probs, strict=True):
        assert counts[option] / len(rows) == pytest.approx(p, abs=0.02)


def test_the_grid_of_runs() -> None:
    case = build_case(S3, "identical", seed=1, sigma=0.1, repeats=10)
    assert len(case.rows) == 5 * 3 * 10
    assert len({r.run_id for r in case.rows}) == len(case.rows)
    cells = Counter((r.objective_id, r.wording_id) for r in case.rows)
    assert set(cells.values()) == {10} and len(cells) == 15
    for r in case.rows:
        assert r.valid and r.amounts is not None
        assert sum(r.amounts.values()) == pytest.approx(190)
    assert case.generating in OBJECTIVES


def test_a_scenario_without_a_choice_has_no_choice_anywhere() -> None:
    for kind in ("identical", "opposite", "same_choice_opposite_money", "true_match"):
        case = build_case(S2, kind, seed=2, sigma=0.1, repeats=2)
        assert case.decision.choice is None
        assert all(r.choice is None for r in case.rows)


def test_identical_is_the_mean_and_the_modal_choice() -> None:
    case = build_case(S3, "identical", seed=5, sigma=0.1, repeats=2)
    profile = next(p for p in case.profiles if p.objective_id == case.generating)
    assert shares(case.decision, 190) == pytest.approx(list(profile.mean))
    assert case.decision.choice == ["close", "retool", "sell"][int(np.argmax(profile.choice_probs))]


def test_opposite_is_everything_on_the_least_funded_line_and_the_least_likely_choice() -> None:
    case = build_case(S3, "opposite", seed=5, sigma=0.1, repeats=2)
    profile = next(p for p in case.profiles if p.objective_id == case.generating)
    least = int(np.argmin(profile.mean))
    assert shares(case.decision, 190) == [1.0 if i == least else 0.0 for i in range(4)]
    assert case.decision.choice == ["close", "retool", "sell"][int(np.argmin(profile.choice_probs))]


def test_same_choice_opposite_money() -> None:
    opposite = build_case(S4, "opposite", seed=9, sigma=0.1, repeats=2)
    same = build_case(S4, "same_choice_opposite_money", seed=9, sigma=0.1, repeats=2)
    identical = build_case(S4, "identical", seed=9, sigma=0.1, repeats=2)
    assert same.decision.amounts == opposite.decision.amounts
    assert same.decision.choice == identical.decision.choice
    assert same.generating == identical.generating == opposite.generating  # same seed, same draws


def test_sparse_keeps_k_dimensions_of_the_identical_case() -> None:
    identical = build_case(S3, "identical", seed=4, sigma=0.1, repeats=2)
    for k in range(1, 6):
        case = build_case(S3, "sparse", seed=4, sigma=0.1, repeats=2, k=k)
        assert case.decision.dimensions == k
        for key, value in case.decision.amounts.items():
            assert value == identical.decision.amounts[key]
        if case.decision.choice is not None:
            assert case.decision.choice == identical.decision.choice


def test_sparse_draws_the_choice_as_one_dimension_among_the_lines() -> None:
    full = CompanyDecision("primary", {"a": 1.0, "b": 2.0}, "close")
    rng = np.random.Generator(np.random.PCG64(0))
    seen: Counter[str] = Counter()
    for _ in range(600):
        got = sparse_decision(S3, full, 1, rng)
        seen[CHOICE_DIMENSION if got.choice is not None else next(iter(got.amounts))] += 1
    assert set(seen) == {"a", "b", CHOICE_DIMENSION}
    assert all(150 < n < 250 for n in seen.values())  # about a third each
    with pytest.raises(ValueError):
        sparse_decision(S3, full, 4, rng)
    with pytest.raises(ValueError):
        sparse_decision(S3, full, 0, rng)


def test_k_only_for_a_sparse_case() -> None:
    with pytest.raises(ValueError):
        build_case(S3, "sparse", seed=1, sigma=0.1, repeats=2)
    with pytest.raises(ValueError):
        build_case(S3, "identical", seed=1, sigma=0.1, repeats=2, k=2)


def test_true_match_is_a_new_draw_from_the_generating_objective() -> None:
    a = build_case(S3, "true_match", seed=11, sigma=0.05, repeats=2)
    b = build_case(S3, "identical", seed=11, sigma=0.05, repeats=2)
    assert a.rows == b.rows and a.generating == b.generating
    assert a.decision.amounts != b.decision.amounts  # a draw, not the mean
    profile = next(p for p in a.profiles if p.objective_id == a.generating)
    assert shares(a.decision, 190) == pytest.approx(list(profile.mean), abs=0.25)


@pytest.mark.parametrize("kind", CASE_KINDS)
def test_a_case_is_fixed_by_its_seed(kind: CaseKind) -> None:
    k = 2 if kind == "sparse" else None
    one = build_case(S4, kind, seed=21, sigma=0.1, repeats=2, k=k)
    two = build_case(S4, kind, seed=21, sigma=0.1, repeats=2, k=k)
    other = build_case(S4, kind, seed=22, sigma=0.1, repeats=2, k=k)
    assert one == two
    assert one != other


def test_the_matcher_finds_the_generating_objective_of_an_identical_case_at_a_tight_spread() -> (
    None
):
    # Not a calibration (step 10 does that): a check that the cases and the matcher fit together.
    found = 0
    for seed in range(20):
        case = build_case(S2, "identical", seed=seed, sigma=0.05, repeats=10)
        m = match_case(
            S2,
            case.rows,
            [case.decision],
            case_id=f"sim-{seed}",
            objectives=OBJECTIVES,
            d_star=1.0,
            k_star=1,
            resamples=500,
        )
        found += m.readings[0].nearest == case.generating
    assert found >= 19


def test_the_generating_objective_is_drawn_among_all_five() -> None:
    drawn = {
        build_case(S2, "identical", seed=s, sigma=0.1, repeats=1).generating for s in range(60)
    }
    assert drawn == set(OBJECTIVES)
