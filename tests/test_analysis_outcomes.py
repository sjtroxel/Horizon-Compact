"""Outcomes per scenario, on hand-built runs and on runs the runner wrote (Phase 3 doc 6, step 2)."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from analysis_helpers import decision, relocate, run_company
from horizon_compact.analysis.outcomes import (
    CHOICE_THRESHOLD,
    SHARE_THRESHOLD,
    OutcomeError,
    outcomes_for,
)
from horizon_compact.analysis.records import RunRow, read_runs
from horizon_compact.experiment import Scenario, load_experiment

EXP = load_experiment("company")


def row(
    scenario_id: str, amounts: Mapping[str, float] | None, choice: str | None = None, **kw: Any
) -> RunRow:
    """A hand-built run: the fields the outcomes read, the rest filler."""
    base: dict[str, Any] = {
        "run_id": "r-000000000000",
        "sweep_id": "s",
        "model_key": "m",
        "scenario_id": scenario_id,
        "objective_id": "A",
        "wording_id": "w1",
        "repeat": 0,
        "status": "valid" if amounts is not None else "sum_mismatch",
        "first_attempt_status": "valid" if amounts is not None else "sum_mismatch",
        "attempts": 1,
        "possible_decline": False,
        "menu_order": (),
        "option_order": (),
        "amounts": amounts,
        "choice": choice,
        "first_amounts": amounts,
        "first_choice": choice,
    }
    base.update(kw)
    return RunRow(**base)


# --- what is read from the files -------------------------------------------------------------------------


def test_kinds_and_thresholds() -> None:
    got = {sid: (o.kind, o.threshold) for sid, o in _all().items()}
    assert got == {
        "s1": ("share", SHARE_THRESHOLD),
        "s2": ("share", SHARE_THRESHOLD),
        "s3": ("choice_rate", CHOICE_THRESHOLD),
        "s4": ("choice_rate", CHOICE_THRESHOLD),
    }
    assert (SHARE_THRESHOLD, CHOICE_THRESHOLD) == (0.10, 0.20)


def _all() -> dict[str, Any]:
    return {sid: outcomes_for(EXP.get_scenario(sid)) for sid in ("s1", "s2", "s3", "s4")}


def test_totals_come_from_the_scenario_files_not_the_analysis() -> None:
    """Change a total in the loaded scenario and the share changes with it."""
    s1 = EXP.get_scenario("s1")
    half = replace_total(s1, 250)
    run = row("s1", {"eliminate": 125, "move_plant_pay": 0, "move_keep_pay": 0})
    assert outcomes_for(s1).score(run).primary == 0.0
    amounts = {"eliminate": 50.0, "move_plant_pay": 50.0, "move_keep_pay": 25.0}
    assert outcomes_for(s1).score_amounts(amounts, None).primary == pytest.approx(75 / 125)
    assert outcomes_for(half).score_amounts(amounts, None).primary == pytest.approx(75 / 250)


def replace_total(scenario: Scenario, total: int) -> Scenario:
    return scenario.model_copy(update={"total": total})


def test_a_renamed_line_fails_loudly_not_silently() -> None:
    s1 = EXP.get_scenario("s1")
    renamed = s1.model_copy(
        update={
            "levers": [
                lever.model_copy(update={"key": "keeps_current_pay"})
                if lever.key == "move_keep_pay"
                else lever
                for lever in s1.levers
            ]
        }
    )
    with pytest.raises(OutcomeError, match="move_keep_pay"):
        outcomes_for(renamed)
    s3 = EXP.get_scenario("s3")
    assert s3.choice is not None
    no_close = s3.model_copy(
        update={
            "choice": s3.choice.model_copy(
                update={"options": [o for o in s3.choice.options if o.key != "close"]}
            ),
            "rules": [],
        }
    )
    with pytest.raises(OutcomeError, match="close"):
        outcomes_for(no_close)


def test_an_unknown_scenario_has_no_outcomes() -> None:
    other = EXP.get_scenario("s1").model_copy(update={"id": "s9"})
    with pytest.raises(OutcomeError, match="s9"):
        outcomes_for(other)


def test_only_valid_runs_of_the_right_scenario_are_scored() -> None:
    s1 = outcomes_for(EXP.get_scenario("s1"))
    with pytest.raises(OutcomeError, match="only valid runs"):
        s1.score(row("s1", None))
    with pytest.raises(OutcomeError, match="not s1"):
        s1.score(row("s2", {"eliminate": 1}))
    with pytest.raises(OutcomeError, match="first attempt"):
        s1.score_first_attempt(
            row(
                "s1",
                {"eliminate": 125, "move_plant_pay": 0, "move_keep_pay": 0},
                first_amounts=None,
                first_attempt_status="sum_mismatch",
            )
        )
    with pytest.raises(OutcomeError, match="amounts name"):
        s1.score_amounts({"eliminate": 125.0}, None)


# --- S1 ------------------------------------------------------------------------------------------------


def s1_run(eliminate: int, plant: int, keep: int) -> RunRow:
    return row("s1", {"eliminate": eliminate, "move_plant_pay": plant, "move_keep_pay": keep})


def test_s1_share_kept_and_the_share_of_movers_who_keep_pay() -> None:
    s1 = outcomes_for(EXP.get_scenario("s1"))
    got = s1.score(s1_run(50, 25, 50))
    assert got.primary == pytest.approx(0.6)
    assert got.secondary == {"keep_pay_share_of_moved": pytest.approx(50 / 75)}
    assert got.vector == {"eliminate": 0.4, "move_plant_pay": 0.2, "move_keep_pay": 0.4}
    assert got.choice is None


def test_s1_secondary_is_undefined_when_no_one_moved_and_the_count_says_so() -> None:
    s1 = outcomes_for(EXP.get_scenario("s1"))
    nobody = s1.score(s1_run(125, 0, 0))
    assert nobody.primary == 0.0 and nobody.secondary == {"keep_pay_share_of_moved": None}
    runs = [s1_run(125, 0, 0), s1_run(100, 10, 15), s1_run(0, 0, 125), s1_run(125, 0, 0)]
    summary = s1.summarize_secondary("keep_pay_share_of_moved", runs)
    assert (summary.n_defined, summary.n_runs) == (2, 4)
    assert summary.mean == pytest.approx((0.6 + 1.0) / 2)
    none_moved = s1.summarize_secondary("keep_pay_share_of_moved", [s1_run(125, 0, 0)])
    assert none_moved.mean is None and (none_moved.n_defined, none_moved.n_runs) == (0, 1)


def test_s1_kept_everyone_and_the_vector_sums_to_one() -> None:
    s1 = outcomes_for(EXP.get_scenario("s1"))
    got = s1.score(s1_run(0, 0, 125))
    assert got.primary == 1.0 and got.secondary["keep_pay_share_of_moved"] == 1.0
    assert got.vector is not None and sum(got.vector.values()) == pytest.approx(1.0)


# --- S2 ------------------------------------------------------------------------------------------------

S2_ZERO = {
    "eliminate_roles": 0, "cut_wages_hours": 0, "cut_rnd": 0, "cut_env_projects": 0,
    "raise_prices": 0, "suppliers": 0, "lower_profit": 0,
}  # fmt: skip


def s2(**amounts: float) -> RunRow:
    return row("s2", {**S2_ZERO, **amounts})


def test_s2_workforce_share_counts_roles_and_wages_only() -> None:
    o = outcomes_for(EXP.get_scenario("s2"))
    total = EXP.get_scenario("s2").total
    assert total == 112_100_000
    got = o.score(s2(eliminate_roles=20_000_000, cut_wages_hours=10_000_000, cut_rnd=10_000_000,
                     raise_prices=30_000_000, lower_profit=42_100_000))  # fmt: skip
    assert got.primary == pytest.approx(30_000_000 / total)
    assert got.vector is not None and set(got.vector) == set(S2_ZERO)  # seven bearers
    assert got.vector["lower_profit"] == pytest.approx(42_100_000 / total)
    assert sum(got.vector.values()) == pytest.approx(1.0)
    assert got.secondary == {}


def test_s2_all_on_profit_and_all_on_jobs() -> None:
    o = outcomes_for(EXP.get_scenario("s2"))
    assert o.score(s2(lower_profit=112_100_000)).primary == 0.0
    assert o.score(s2(eliminate_roles=112_100_000)).primary == 1.0


def test_s2_vector_leaves_out_the_lines_not_offered() -> None:
    o = outcomes_for(EXP.get_scenario("s2"))
    assert "payouts" not in o.line_keys and "keep_people" not in o.line_keys
    assert len(o.line_keys) == 7


# --- S3 ------------------------------------------------------------------------------------------------


def s3(choice: str, eliminated: int, moved: int, kept: int, sold: int) -> RunRow:
    amounts = {"eliminated": eliminated, "moved_other_plants": moved, "kept_at_plant": kept,
               "transferred_to_buyer": sold}  # fmt: skip
    return row("s3", amounts, choice)


def test_s3_close_rate_is_the_choice_and_retained_is_everything_but_eliminated() -> None:
    o = outcomes_for(EXP.get_scenario("s3"))
    closed = o.score(s3("close", 161, 29, 0, 0))
    assert closed.primary == 1.0 and closed.choice == "close"
    assert closed.secondary == {"retained_share": pytest.approx(29 / 190)}
    assert closed.vector is not None and closed.vector["eliminated"] == pytest.approx(161 / 190)
    retool = o.score(s3("retool", 0, 29, 161, 0))
    assert retool.primary == 0.0 and retool.secondary["retained_share"] == 1.0
    sell = o.score(s3("sell", 19, 0, 0, 171))
    assert sell.primary == 0.0 and sell.secondary["retained_share"] == pytest.approx(171 / 190)
    assert sum(sell.vector.values()) == pytest.approx(1.0)  # type: ignore[union-attr]


def test_s3_a_valid_run_without_a_choice_is_an_error() -> None:
    o = outcomes_for(EXP.get_scenario("s3"))
    with pytest.raises(OutcomeError, match="choice"):
        o.score(
            row(
                "s3",
                {
                    "eliminated": 190,
                    "moved_other_plants": 0,
                    "kept_at_plant": 0,
                    "transferred_to_buyer": 0,
                },
            )
        )


# --- S4 ------------------------------------------------------------------------------------------------

S4_ZERO = {k.key: 0 for k in EXP.get_scenario("s4").offered()}


def s4(choice: str, **amounts: float) -> RunRow:
    return row("s4", {**S4_ZERO, **amounts}, choice)


def test_s4_fund_rate_and_the_vector_of_uses_and_sources_together() -> None:
    o = outcomes_for(EXP.get_scenario("s4"))
    assert len(o.line_keys) == 15  # eight uses (the program and seven others) and seven sources
    funded = o.score(
        s4("fund", program=20_400_000, training=6_000_000, cut_rnd=5_000_000, suppliers=1_000_000)
    )
    assert funded.primary == 1.0
    everything = 20_400_000 + 6_000_000 + 5_000_000 + 1_000_000
    assert funded.vector is not None
    assert funded.vector["program"] == pytest.approx(20_400_000 / everything)
    assert funded.vector["cut_rnd"] == pytest.approx(
        5_000_000 / everything
    )  # sources are in the vector
    assert sum(funded.vector.values()) == pytest.approx(1.0)
    assert funded.secondary == {"any_cuts": 1.0}


def test_s4_without_cuts_and_a_declined_program_with_cuts() -> None:
    o = outcomes_for(EXP.get_scenario("s4"))
    clean = o.score(s4("fund", program=20_400_000))
    assert clean.secondary == {"any_cuts": 0.0} and clean.vector is not None
    assert clean.vector["program"] == 1.0
    declined = o.score(s4("decline", retain_cash=23_400_000, cut_payouts=3_000_000))
    assert declined.primary == 0.0 and declined.secondary == {"any_cuts": 1.0}
    assert declined.vector is not None and declined.vector["program"] == 0.0
    assert declined.vector["retain_cash"] == pytest.approx(23_400_000 / 26_400_000)
    assert declined.vector["cut_payouts"] == pytest.approx(3_000_000 / 26_400_000)
    mean_cuts = o.summarize_secondary(
        "any_cuts",
        [
            s4("fund", program=20_400_000),
            s4("decline", retain_cash=23_400_000, cut_payouts=3_000_000),
        ],
    )
    assert mean_cuts.mean == 0.5 and mean_cuts.n_runs == 2


def test_s4_a_vector_with_nothing_in_it_is_undefined_not_a_division_by_zero() -> None:
    o = outcomes_for(EXP.get_scenario("s4"))
    assert o.score_amounts(dict(S4_ZERO), "decline").vector is None


# --- first attempt beside final --------------------------------------------------------------------------


def test_the_first_attempt_is_scored_on_its_own_amounts() -> None:
    o = outcomes_for(EXP.get_scenario("s1"))
    final = {"eliminate": 0, "move_plant_pay": 0, "move_keep_pay": 125}
    first = {"eliminate": 125, "move_plant_pay": 0, "move_keep_pay": 0}
    retried = row("s1", final, first_amounts=first, first_attempt_status="valid")
    assert o.score(retried).primary == 1.0 and o.score_first_attempt(retried).primary == 0.0


# --- runs the runner wrote -------------------------------------------------------------------------------


def _scored(tmp_path: Path, sid: str, inputs: list[dict[str, Any]]) -> list[Any]:
    _exp, plan, store = run_company(tmp_path, sid, inputs)
    found = read_runs(store, relocate(store, plan))
    assert [r.status for r in found.rows] == ["valid"] * len(inputs)
    o = outcomes_for(EXP.get_scenario(sid))
    return sorted(o.score(r).primary for r in found.rows)


def test_s1_runs_the_runner_wrote_are_scored_as_hand_built_ones(tmp_path: Path) -> None:
    inputs = [decision({"eliminate": e, "move_plant_pay": p, "move_keep_pay": k})
              for e, p, k in [(125, 0, 0), (50, 25, 50), (0, 0, 125), (25, 100, 0), (100, 10, 15)]]  # fmt: skip
    assert _scored(tmp_path, "s1", inputs) == pytest.approx(sorted([0.0, 0.6, 1.0, 0.8, 0.2]))


def test_s2_runs_the_runner_wrote(tmp_path: Path) -> None:
    def bear(**kw: int) -> dict[str, Any]:
        return decision({**S2_ZERO, **kw})

    inputs = [
        bear(lower_profit=112_100_000),
        bear(
            eliminate_roles=20_000_000,
            cut_wages_hours=10_000_000,
            cut_rnd=10_000_000,
            raise_prices=30_000_000,
            lower_profit=42_100_000,
        ),
        bear(eliminate_roles=112_100_000),
        bear(cut_wages_hours=22_000_000, suppliers=7_700_000, lower_profit=82_400_000),
        bear(
            eliminate_roles=50_000_000,
            cut_wages_hours=5_000_000,
            suppliers=7_700_000,
            cut_env_projects=4_500_000,
            cut_rnd=30_000_000,
            lower_profit=14_900_000,
        ),
    ]
    total = 112_100_000
    expected = [0.0, 30e6 / total, 1.0, 22e6 / total, 55e6 / total]
    assert _scored(tmp_path, "s2", inputs) == pytest.approx(sorted(expected))


def test_s3_runs_the_runner_wrote(tmp_path: Path) -> None:
    def people(choice: str, e: int, m: int, k: int, t: int) -> dict[str, Any]:
        return decision(
            {
                "eliminated": e,
                "moved_other_plants": m,
                "kept_at_plant": k,
                "transferred_to_buyer": t,
            },
            plant_decision=choice,
        )

    inputs = [
        people("close", 161, 29, 0, 0),
        people("close", 190, 0, 0, 0),
        people("retool", 0, 29, 161, 0),
        people("sell", 19, 0, 0, 171),
        people("close", 161, 29, 0, 0),
    ]
    assert _scored(tmp_path, "s3", inputs) == [0.0, 0.0, 1.0, 1.0, 1.0]


def test_s4_runs_the_runner_wrote(tmp_path: Path) -> None:
    def program(choice: str, **kw: int) -> dict[str, Any]:
        return decision({**S4_ZERO, **kw}, program_decision=choice)

    inputs = [
        program("fund", program=20_400_000),
        program(
            "fund", program=20_400_000, training=6_000_000, cut_rnd=5_000_000, suppliers=1_000_000
        ),
        program("decline", retain_cash=20_400_000),
        program("decline", retain_cash=23_400_000, cut_payouts=3_000_000),
        program("fund", program=20_400_000),
    ]
    assert _scored(tmp_path, "s4", inputs) == [0.0, 0.0, 1.0, 1.0, 1.0]
