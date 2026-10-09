"""The verdict-rule simulations: choice rates exact, the share engine under the rule adopted at step 12 (Welch
and decision 10's two rules), the engine families and the runner's grid (Phase 3 doc 14, steps 10 and 12)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest
from scipy import stats

from analysis_helpers import hand_newcombe, hand_welch
from horizon_compact.analysis.intervals import comparison_seed
from horizon_compact.analysis.verdict import compare, decide
from horizon_compact.simulation import real
from horizon_compact.simulation.exact import S1_GRID, share_pmf
from horizon_compact.simulation.matcher_sim import (
    d_star,
    identification_by_dimensions,
    k_star,
    labels,
)
from horizon_compact.simulation.runner import (
    AGREE_CONFIGS,
    FULL,
    QUICK,
    SEED_ROOT,
    Task,
    agree_pmf,
    build_tasks,
    pair,
    wording_means,
)
from horizon_compact.simulation.verdicts import (
    VERDICTS,
    choice_point,
    less_certain,
    newcombe_verdict,
    share_point,
    share_verdicts,
    welch_arrays,
)


def point_mass(k: int) -> np.ndarray:
    out = np.zeros(S1_GRID + 1)
    out[k] = 1.0
    return out


# --- choice rates, exact ------------------------------------------------------------------------------------


def test_choice_probabilities_by_brute_force_with_the_tests_own_newcombe() -> None:
    # Three wordings of 2 runs a side, N = 6: every pair of counts weighed by hand.
    p1, p2, n_side = 0.7, 0.3, 6
    expected = dict.fromkeys(VERDICTS, 0.0)
    for c1 in range(n_side + 1):
        for c2 in range(n_side + 1):
            w = stats.binom.pmf(c1, n_side, p1) * stats.binom.pmf(c2, n_side, p2)
            lo, hi = hand_newcombe(c1, n_side, c2, n_side)
            expected[decide(c1 / n_side - c2 / n_side, lo, hi, 0.2).verdict] += w
    got = choice_point(p1, p2, n=2)
    for v in VERDICTS:
        assert got["probability"][v] == pytest.approx(expected[v], abs=1e-12)
    assert sum(got["probability"].values()) == pytest.approx(1.0, abs=1e-12)


def test_choice_rates_at_0_and_1_are_point_masses() -> None:
    got = choice_point(1.0, 1.0, n=20)  # 60 of 60 on both sides, always
    assert got["probability"][newcombe_verdict(60, 60, 60, 60, 0.2)] == pytest.approx(1.0)


def test_the_stated_choice_powers() -> None:
    # planning/07 section 8: about 63% for 30 points near 50%, about 80% for 35. Exact here.
    assert choice_point(0.65, 0.35, n=20)["probability"]["split"] == pytest.approx(0.629, abs=0.001)
    assert choice_point(0.675, 0.325, n=20)["probability"]["split"] == pytest.approx(
        0.819, abs=0.001
    )


# --- the share engine: Welch and decision 10's two rules (step 12) ----------------------------------------


def test_less_certain() -> None:
    assert less_certain("split", "split") == "split"
    assert less_certain("no_split", "no_split") == "no_split"
    assert less_certain("split", "no_split") == "inconclusive"
    assert less_certain("no_split", "inconclusive") == "inconclusive"


def test_the_vectorized_welch_matches_the_tests_own_on_every_replicate() -> None:
    rng = np.random.Generator(np.random.PCG64(11))
    first = rng.integers(0, S1_GRID + 1, size=(40, 3, 5))
    second = rng.integers(0, S1_GRID + 1, size=(40, 3, 5))
    first[0] = 100  # one replicate with no spread on the first side
    d, lo, hi = welch_arrays(first, second, S1_GRID)
    for r in range(40):
        one, two = (
            {w: list(x[r, i] / S1_GRID) for i, w in enumerate("abc")} for x in (first, second)
        )
        hd, hlo, hhi, _ = hand_welch(one, two)
        assert (d[r], lo[r], hi[r]) == pytest.approx((hd, hlo, hhi), abs=1e-12)


def test_every_run_at_one_boundary_value_on_both_sides_is_inconclusive_by_both_rules() -> None:
    # Welch alone says no split from [0, 0]. The floor makes it inconclusive, and the constant check tests
    # 18 of 18 against 18 of 18 by Newcombe at the share threshold, far wider than 0.1: inconclusive too.
    one = point_mass(S1_GRID)
    got = share_point([one] * 3, [one] * 3, n=6, reps=50, seed=1, grid=S1_GRID)
    assert got["interval_alone"] == {"split": 0, "no_split": 50, "inconclusive": 0}
    assert got["interval_alone_no_split_degenerate"] == 50
    assert got["verdicts"] == {"split": 0, "no_split": 0, "inconclusive": 50}
    assert got["floor_fired"] == got["constant_fired"] == 50
    assert got["constant_changed"] == 0  # the floor had already made it inconclusive
    assert newcombe_verdict(18, 18, 18, 18, 0.1) == "inconclusive"


def test_an_interior_all_agree_is_caught_too() -> None:
    # Every run keeps 100 of 125: away from 0 and 1, which decision 10's first candidate missed.
    eighty = point_mass(100)
    got = share_point([eighty] * 3, [eighty] * 3, n=6, reps=20, seed=2, grid=S1_GRID)
    assert got["interval_alone"]["no_split"] == 20
    assert got["verdicts"]["no_split"] == 0 and got["constant_fired"] == 20


def test_one_constant_side_fires_the_constant_check_on_every_replicate() -> None:
    one, zero = point_mass(S1_GRID), point_mass(0)
    mixed = 0.5 * one + 0.5 * zero
    got = share_point([one] * 3, [mixed] * 3, n=6, reps=40, seed=3, grid=S1_GRID)
    assert got["constant_fired"] == 40


def test_the_floor_alone_fires_on_a_narrow_interval_with_no_constant_side() -> None:
    narrow = 0.5 * point_mass(62) + 0.5 * point_mass(63)
    got = share_point([narrow] * 3, [narrow] * 3, n=20, reps=30, seed=9, grid=S1_GRID)
    assert got["constant_fired"] == 0
    assert got["floor_fired"] == got["interval_alone"]["no_split"] > 0
    assert got["verdicts"]["no_split"] == 0


def test_the_engine_reads_the_first_sides_value_when_both_are_constant() -> None:
    first, second = np.full((1, 3, 6), 125), np.full((1, 3, 6), 0)
    got = share_verdicts(first, second, grid=S1_GRID)
    assert got.constant == [125] and got.final == ["split"]
    got = share_verdicts(second, first, grid=S1_GRID)
    assert got.constant == [0] and got.final == ["split"]  # a split the other way


def test_a_share_point_is_fixed_by_its_seed_and_counts_every_replicate() -> None:
    p = share_pmf(0.5, 0.15, 0.2, S1_GRID)
    assert p is not None
    one = share_point([p] * 3, [p] * 3, n=6, reps=300, seed=7, grid=S1_GRID)
    assert one == share_point([p] * 3, [p] * 3, n=6, reps=300, seed=7, grid=S1_GRID)
    assert one != share_point([p] * 3, [p] * 3, n=6, reps=300, seed=8, grid=S1_GRID)
    assert sum(one["verdicts"].values()) == 300


def test_a_wrong_sign_split_is_counted_apart() -> None:
    # The first side always lower: every split is in the wrong direction.
    low, high = point_mass(10), point_mass(115)
    got = share_point([low] * 3, [high] * 3, n=6, reps=10, seed=4, grid=S1_GRID)
    assert got["verdicts"]["split"] == got["split_wrong_sign"] == 10


# --- the engine families ------------------------------------------------------------------------------------


def test_failures_through_the_engine_never_keep_an_overturned_verdict() -> None:
    a, b = share_pmf(0.55, 0.15, 0.0, S1_GRID), share_pmf(0.45, 0.15, 0.0, S1_GRID)
    assert a is not None and b is not None
    for rate, pattern in ((0.1, "random"), (0.15, "one_objective")):
        got = real.failure_point(a, b, n=10, rate=rate, pattern=pattern, reps=6, seed=3, key="t")
        assert got["kept_verdict_the_bound_overturns"] == 0
        assert got["independent_rebuild_mismatches"] == 0
        assert sum(got["final"].values()) == 6


def test_a_failure_rate_of_one_leaves_nothing_assessable() -> None:
    a = share_pmf(0.5, 0.15, 0.0, S1_GRID)
    assert a is not None
    got = real.failure_point(a, a, n=6, rate=1.0, pattern="random", reps=2, seed=1, key="all")
    assert got["final"] == {"not_assessable": 2}


def test_the_wording_label_is_recomputed_independently() -> None:
    def mk(m: float) -> np.ndarray:
        p = share_pmf(m, 0.1, 0.0, S1_GRID)
        assert p is not None
        return p

    first = [mk(m) for m in wording_means(0.575, "reversed", 0.10, 0)]
    second = [mk(m) for m in wording_means(0.425, "reversed", 0.10, 1)]
    got = real.wording_point(first, second, n=10, reps=8, seed=5, key="t")
    assert got["independent_label_mismatches"] == 0


def test_wording_means() -> None:
    assert wording_means(0.5, "shared", 0.05, 0) == (0.45, 0.5, 0.55)
    assert wording_means(0.5, "shared", 0.05, 1) == (0.45, 0.5, 0.55)
    assert wording_means(0.5, "reversed", 0.05, 1) == (0.55, 0.5, 0.45)


# --- the runner's grid --------------------------------------------------------------------------------------


def test_the_full_grid_is_section_14_1s() -> None:
    tasks = build_tasks(FULL)
    reps: dict[str, int] = {}
    for t in tasks:
        if t.family == "share_grid":
            reps[t.key] = reps.get(t.key, 0) + t.get("reps")
    assert len(reps) == 5 * 6 * 3 * 6 * 4
    for key, total in reps.items():
        d = key.split("|d=")[1].split("|")[0]
        assert total == (20_000 if d in ("0", "0.1") else 2_000), key


def test_every_task_has_its_own_seed() -> None:
    tasks = build_tasks(FULL)
    seeds = [t.seed for t in tasks]
    assert len(set(seeds)) == len(seeds)
    t = tasks[0]
    assert t.seed == comparison_seed(SEED_ROOT, f"{t.family}|{t.key}|{t.chunk}")


def test_quick_is_a_slice_of_every_family() -> None:
    assert {t.family for t in build_tasks(QUICK)} == {t.family for t in build_tasks(FULL)}


def test_pair_keeps_the_difference_and_the_first_higher() -> None:
    assert pair(0.5, 0.1, 0.15, 0.0) == (0.6, 0.5)
    assert pair(0.9, 0.1, 0.15, 0.0) == (0.9, 0.8)  # 1.0 has no Beta
    assert pair(0.9, 0.05, 0.25, 0.0) == (0.9, 0.85)  # 0.95 has none at this spread
    assert pair(0.1, 0.0, 0.3, 0.0) is None


def test_the_all_agree_settings_have_the_differences_they_claim() -> None:
    for name, kind, a1, a2 in AGREE_CONFIGS:
        m1 = float(agree_pmf(kind, a1) @ (np.arange(S1_GRID + 1) / S1_GRID))
        m2 = float(agree_pmf(kind, a2) @ (np.arange(S1_GRID + 1) / S1_GRID))
        assert m1 - m2 == pytest.approx(0.0 if a1 == a2 else 0.1, abs=1e-12), name


def test_a_task_reads_its_params() -> None:
    t = Task("x", "k", 0, (("a", 1), ("b", 2)))
    assert (t.get("a"), t.get("b")) == (1, 2)


# --- the matcher's thresholds -------------------------------------------------------------------------------


def test_d_star_is_an_observed_95th_percentile_ignoring_unmatchable_trials() -> None:
    values = [i / 100 for i in range(1, 101)] + [math.nan] * 7
    assert d_star(values) == 0.95  # 5 of 100 lie strictly above it; 0.94 would leave 6
    assert d_star([0.3] * 20) == 0.3  # ties: none above


def test_identification_is_grouped_by_the_dimensions_each_case_has() -> None:
    # Two sparse cells: trials are pooled by their own dimension count, not by the cell they came from.
    one: dict[str, list[Any]] = {
        "dimensions": [0, 1, 1, 2],
        "identified": [False, True, False, True],
    }
    two: dict[str, list[Any]] = {"dimensions": [1, 2, 2], "identified": [True, True, False]}
    assert identification_by_dimensions([one, two]) == {0: 0.0, 1: 2 / 3, 2: 2 / 3}


def test_k_star_is_the_smallest_k_reaching_80_percent() -> None:
    assert k_star({1: 0.5, 2: 0.79, 3: 0.8, 4: 0.95}) == 3
    assert k_star({1: 0.5, 2: 0.7}) is None
    assert k_star({1: 0.85, 2: 0.7}) == 1  # the smallest, even if a larger k dips


def test_labels_in_the_matchers_order() -> None:
    records: dict[str, list[Any]] = {
        "nearest": [0.1, 0.5, 0.2, math.nan, 0.1],
        "tie": [False, False, True, False, False],
        "dimensions": [5, 5, 5, 5, 1],
        "unmatchable": [False, False, False, True, False],
    }
    assert labels(records, 0.3, 2) == {
        "not_enough_disclosed": 1,
        "unmatchable": 1,
        "no_good_match": 1,
        "tie": 1,
        "match": 1,
    }


# --- cases built so the outcome is forced (gaps the mutation check showed) ----------------------------------


def test_the_constant_check_tests_at_the_share_threshold_not_the_choice_threshold() -> None:
    # 60 of 60 against 60 of 60: Newcombe's half-width is about 0.127, inside 0.2 but not inside 0.1. A
    # constant check at the choice threshold would let a no split through where the floor did not fire.
    assert newcombe_verdict(60, 60, 60, 60, 0.1) == "inconclusive"
    assert newcombe_verdict(60, 60, 60, 60, 0.2) == "no_split"
    first = np.full((1, 3, 20), 125)
    second = np.full((1, 3, 20), 125)
    second[0, :2, 0] = 100  # one run at 0.8 in two wordings: real width, and 58 of 60 still at 125
    assert newcombe_verdict(60, 60, 58, 60, 0.1) == "inconclusive"
    assert newcombe_verdict(60, 60, 58, 60, 0.2) == "no_split"
    got = share_verdicts(first, second, grid=S1_GRID)
    assert got.interval_verdict == ["no_split"] and got.floor_fired == [False]
    assert got.constant == [125] and got.final == ["inconclusive"]


def test_a_no_split_with_width_is_not_counted_degenerate_and_stands() -> None:
    p = share_pmf(0.5, 0.05, 0.0, S1_GRID)
    assert p is not None
    got = share_point([p] * 3, [p] * 3, n=20, reps=200, seed=2, grid=S1_GRID)
    assert got["verdicts"]["no_split"] > 150
    assert got["interval_alone_no_split_degenerate"] == 0 and got["floor_fired"] == 0


def test_a_choice_split_in_the_wrong_direction_is_counted() -> None:
    got = choice_point(0.2, 0.8, n=20)  # the first objective lower: every split is the wrong way
    assert got["split_wrong_sign"] == pytest.approx(got["probability"]["split"], abs=1e-12)
    assert got["probability"]["split"] > 0.99
    assert choice_point(0.8, 0.2, n=20)["split_wrong_sign"] == pytest.approx(0.0, abs=1e-12)


def test_a_tie_above_d_star_is_no_good_match_and_k_star_itself_is_enough() -> None:
    records: dict[str, list[Any]] = {
        "nearest": [0.5, 0.1],
        "tie": [True, False],
        "dimensions": [3, 2],
        "unmatchable": [False, False],
    }
    assert labels(records, 0.3, 2) == {
        "not_enough_disclosed": 0,
        "unmatchable": 0,
        "no_good_match": 1,
        "tie": 0,
        "match": 1,
    }


def test_wording_means_reverse_only_the_second_objective() -> None:
    assert wording_means(0.5, "reversed", 0.05, 0) == (0.45, 0.5, 0.55)


def test_the_bound_rebuild_agrees_when_the_bound_must_overturn_a_split() -> None:
    # Every valid run of A keeps 100 of 125 (0.8) and of B 75 (0.6): a split of exactly 0.2 with a [0.2, 0.2]
    # interval. With about two failures per cell of 20, narrowing (A's failures to 0, B's to 1) brings the
    # difference near 0.08 and must overturn it; the wrong direction would not. The engine and the
    # independent rebuild must agree on every replicate.
    got = real.failure_point(
        point_mass(100), point_mass(75), n=20, rate=0.1, pattern="random", reps=12, seed=4, key="b"
    )
    assert got["bound_applied"] > 0 and got["downgraded_by_bound"] > 0
    assert got["independent_rebuild_mismatches"] == 0
    assert got["kept_verdict_the_bound_overturns"] == 0


def test_the_bound_rebuild_agrees_when_the_bound_must_overturn_a_no_split() -> None:
    # Both objectives near 0.5 with a spread of 0.05: a no split with real width. Widening sets A's failures
    # to 1 and B's to 0 (and the reverse); with both sides' failures counted the difference reaches about
    # 0.1 and overturns it, which a rebuild that dropped B's failures would miss.
    p = share_pmf(0.5, 0.05, 0.0, S1_GRID)
    assert p is not None
    got = real.failure_point(p, p, n=20, rate=0.1, pattern="random", reps=12, seed=5, key="n")
    assert got["bound_applied"] > 0 and got["downgraded_by_bound"] > 0
    assert got["independent_rebuild_mismatches"] == 0


def test_the_rebuild_is_the_adopted_rule_on_unequal_cells() -> None:
    # Against the analysis's own compare on the same cells, with a cell short of runs and a constant side.
    cases = [
        ({"w1": [0.8, 0.6, 0.72], "w2": [0.4, 0.96]}, {"w1": [0.2, 0.16], "w2": [0.0, 0.08, 0.4]}),
        ({"w1": [1.0] * 4, "w2": [1.0] * 3}, {"w1": [1.0, 0.92, 1.0], "w2": [1.0] * 5}),
        (
            {"w1": [0.496, 0.504] * 5, "w2": [0.504] * 6},
            {"w1": [0.496] * 6, "w2": [0.504, 0.496] * 4},
        ),
        # Welch says no split; the constant check (42 of 42 against 40 of 42) makes it inconclusive.
        (
            {"w1": [1.0] * 20, "w2": [1.0] * 22},
            {"w1": [1.0] * 19 + [0.8], "w2": [1.0] * 21 + [0.8]},
        ),
    ]
    outcomes = real.s1_outcomes()
    for first, second in cases:
        rows = []
        for objective, cells in ((real.FIRST, first), (real.SECOND, second)):
            for w, values in cells.items():
                for i, v in enumerate(values):
                    rows.append(real._row("rebuild", objective, w, i, round(v * S1_GRID)))
        got = compare(outcomes, rows, real.FIRST, real.SECOND)
        assert real.rebuild_verdict(first, second) == got.verdict
    assert got.interval.width > 0.008 and got.constant_check is not None
    assert decide(got.difference, got.interval.low, got.interval.high, 0.1).verdict == "no_split"
    assert got.verdict == "inconclusive"  # the last case is decided by the constant check


def test_the_validation_family_agrees_with_the_analysis_where_the_rules_fire() -> None:
    a, b = agree_pmf("mixture", 1.0), agree_pmf("mixture", 0.8)
    got = real.validation_point(a, b, n=6, reps=40, seed=2, key="t")
    assert got["verdicts_agree"] == 40 and got["disagreements"] == []
    assert got["constant_fired"] > 0 and got["max_abs_endpoint_difference"] < 1e-12


def test_a_wording_with_no_difference_breaks_a_negative_split() -> None:
    # w1 identical on both sides (difference exactly 0); w2 and w3 put A far below B: a negative split whose
    # w1 is "zero", so the label must be wording-sensitive.
    same, low, high = point_mass(60), point_mass(10), point_mass(115)
    got = real.wording_point([same, low, low], [same, high, high], n=10, reps=3, seed=6, key="z")
    assert got["final"] == {"split": 3}
    assert got["labels"] == {"wording_sensitive": 3}
    assert got["independent_label_mismatches"] == 0
