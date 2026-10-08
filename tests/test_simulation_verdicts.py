"""The verdict-rule simulations: choice rates exact, decision 10's candidates, the engine families and the
runner's grid (Phase 3 doc 14, step 10)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest
from scipy import stats

from analysis_helpers import hand_newcombe
from horizon_compact.analysis.intervals import comparison_seed
from horizon_compact.analysis.verdict import decide
from horizon_compact.simulation import real
from horizon_compact.simulation.exact import S1_GRID, share_pmf
from horizon_compact.simulation.matcher_sim import d_star, k_star, labels
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
    candidate_verdicts,
    choice_point,
    less_certain,
    newcombe_verdict,
    share_point,
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


# --- decision 10's candidates -------------------------------------------------------------------------------


def test_less_certain() -> None:
    assert less_certain("split", "split") == "split"
    assert less_certain("no_split", "no_split") == "no_split"
    assert less_certain("split", "no_split") == "inconclusive"
    assert less_certain("no_split", "inconclusive") == "inconclusive"


def test_every_run_at_one_boundary_value_on_both_sides() -> None:
    # The rule says no split from [0, 0]; both candidates fire on every replicate and test 18 of 18 against
    # 18 of 18 by Newcombe at the share threshold, whose interval is far wider than 0.1: inconclusive.
    one = point_mass(S1_GRID)
    got = share_point([one] * 3, [one] * 3, n=6, reps=50, seed=1, grid=S1_GRID)
    assert got["verdicts"] == {"split": 0, "no_split": 50, "inconclusive": 0}
    assert got["no_split_degenerate"] == 50
    assert newcombe_verdict(18, 18, 18, 18, 0.1) == "inconclusive"
    for name in ("c1", "c2"):
        assert got[f"{name}_rule"]["no_split"] == 50
        assert candidate_verdicts(got, name) == {"split": 0, "no_split": 0, "inconclusive": 50}


def test_an_interior_all_agree_fires_neither_candidate() -> None:
    # Every run keeps 100 of 125: still [0, 0] and no split, but no run is at a boundary value.
    eighty = point_mass(100)
    got = share_point([eighty] * 3, [eighty] * 3, n=6, reps=20, seed=2, grid=S1_GRID)
    assert got["verdicts"]["no_split"] == 20 and got["no_split_degenerate"] == 20
    assert sum(got["c1_rule"].values()) == sum(got["c2_rule"].values()) == 0
    assert candidate_verdicts(got, "c1") == got["verdicts"]


def test_one_side_at_a_boundary_fires_only_the_wider_candidate() -> None:
    one, zero = point_mass(S1_GRID), point_mass(0)
    mixed = 0.5 * one + 0.5 * zero
    got = share_point([one] * 3, [mixed] * 3, n=6, reps=40, seed=3, grid=S1_GRID)
    assert sum(got["c1_rule"].values()) == 0
    assert sum(got["c2_rule"].values()) == 40


def test_candidate_verdicts_replace_only_the_triggered_replicates() -> None:
    point = {
        "verdicts": {"split": 10, "no_split": 5, "inconclusive": 85},
        "c1_rule": {"split": 0, "no_split": 4, "inconclusive": 0},
        "c1_combined": {"split": 0, "no_split": 0, "inconclusive": 4},
    }
    assert candidate_verdicts(point, "c1") == {"split": 10, "no_split": 1, "inconclusive": 89}


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


def test_the_candidates_test_at_the_share_threshold_not_the_choice_threshold() -> None:
    # 60 of 60 against 60 of 60: Newcombe's half-width is about 0.127, inside 0.2 but not inside 0.1. At the
    # share threshold the candidate must make it inconclusive; at 0.2 it would stay a no split.
    assert newcombe_verdict(60, 60, 60, 60, 0.1) == "inconclusive"
    assert newcombe_verdict(60, 60, 60, 60, 0.2) == "no_split"
    one = point_mass(S1_GRID)
    got = share_point([one] * 3, [one] * 3, n=20, reps=5, seed=1, grid=S1_GRID)
    assert candidate_verdicts(got, "c1") == {"split": 0, "no_split": 0, "inconclusive": 5}


def test_a_no_split_with_width_is_not_counted_degenerate() -> None:
    p = share_pmf(0.5, 0.05, 0.0, S1_GRID)
    assert p is not None
    got = share_point([p] * 3, [p] * 3, n=20, reps=200, seed=2, grid=S1_GRID)
    assert got["verdicts"]["no_split"] > 150
    assert got["no_split_degenerate"] == 0


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
    # Every valid run of both keeps 62 of 125: a no split from [0, 0]. Widening sets A's failures to 1 and B's
    # to 0 (and the reverse); with both sides' failures counted the difference reaches about 0.1 and
    # overturns it, which a rebuild that dropped B's failures would miss.
    got = real.failure_point(
        point_mass(62), point_mass(62), n=20, rate=0.1, pattern="random", reps=12, seed=5, key="n"
    )
    assert got["bound_applied"] > 0 and got["downgraded_by_bound"] > 0
    assert got["independent_rebuild_mismatches"] == 0


def test_a_wording_with_no_difference_breaks_a_negative_split() -> None:
    # w1 identical on both sides (difference exactly 0); w2 and w3 put A far below B: a negative split whose
    # w1 is "zero", so the label must be wording-sensitive.
    same, low, high = point_mass(60), point_mass(10), point_mass(115)
    got = real.wording_point([same, low, low], [same, high, high], n=10, reps=3, seed=6, key="z")
    assert got["final"] == {"split": 3}
    assert got["labels"] == {"wording_sensitive": 3}
    assert got["independent_label_mismatches"] == 0
