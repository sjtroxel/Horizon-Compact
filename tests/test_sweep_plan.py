"""Plans: ids, seeds, order and the preflight bound (Phase 1 IMPLEMENTATION doc sections 6.2 and 6.5)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from horizon_compact.sweep.plan import (
    SweepRefusal,
    build_plan,
    check_preflight,
    preflight_bound_usd,
    worst_case_per_attempt_usd,
)
from sweep_helpers import company_like, experiment, make_plan


def test_the_skeleton_is_fifteen_runs_with_derived_ids() -> None:
    exp = experiment()
    plan = build_plan(exp, model_key="sonnet-4-6", label="skeleton", repeats=3, seed=20261005)
    assert len(plan.runs) == 15
    assert re.fullmatch(r"skeleton-sonnet-4-6-[0-9a-f]{8}", plan.sweep_id)
    assert all(re.fullmatch(r"r-[0-9a-f]{12}", run.run_id) for run in plan.runs)
    assert len({run.run_id for run in plan.runs}) == 15
    assert len({run.menu_order_seed for run in plan.runs}) == 15


def test_the_same_inputs_give_the_same_plan() -> None:
    assert make_plan(seed=3)[1] == make_plan(seed=3)[1]
    assert make_plan(seed=3)[1].manifest() == make_plan(seed=3)[1].manifest()


def test_a_different_seed_gives_a_different_sweep_and_order() -> None:
    a, b = make_plan(repeats=3, seed=1)[1], make_plan(repeats=3, seed=2)[1]
    assert a.sweep_id != b.sweep_id
    assert [r.run_id for r in a.runs] != [r.run_id for r in b.runs]


def test_the_model_label_and_repeats_are_part_of_the_sweep_id() -> None:
    exp = experiment()
    base = build_plan(exp, model_key="nova-lite", label="t", repeats=1, seed=1)
    assert (
        build_plan(exp, model_key="sonnet-4-6", label="t", repeats=1, seed=1).sweep_id
        != base.sweep_id
    )
    assert (
        build_plan(exp, model_key="nova-lite", label="u", repeats=1, seed=1).sweep_id
        != base.sweep_id
    )
    assert (
        build_plan(exp, model_key="nova-lite", label="t", repeats=2, seed=1).sweep_id
        != base.sweep_id
    )


def test_the_shuffled_order_covers_every_cell_exactly_once() -> None:
    exp, plan = make_plan(repeats=3)
    cells = [(r.objective_id, r.repeat) for r in plan.runs]
    expected = {(o.id, n) for o in exp.objectives for n in range(3)}
    assert len(cells) == len(set(cells)) == 15
    assert set(cells) == expected
    canonical = [(o.id, n) for o in exp.objectives for n in range(3)]
    assert cells != canonical, "the run order should be shuffled"


def test_an_unknown_model_or_zero_repeats_is_refused() -> None:
    exp = experiment()
    with pytest.raises(Exception, match="unknown model"):
        build_plan(exp, model_key="nope", label="t", repeats=1, seed=1)
    with pytest.raises(ValueError, match="repeats"):
        build_plan(exp, model_key="nova-lite", label="t", repeats=0, seed=1)


def test_the_preflight_bound_is_runs_times_three_attempts_times_the_worst_attempt() -> None:
    exp, plan = make_plan("sonnet-4-6", repeats=3)
    per_attempt = worst_case_per_attempt_usd(exp, plan)
    assert 0.03 < per_attempt < 0.06  # doc: about $0.04
    assert preflight_bound_usd(exp, plan) == pytest.approx(15 * 3 * per_attempt, abs=1e-3)
    assert 1.5 < preflight_bound_usd(exp, plan) < 2.5  # doc: about $1.90


def test_a_sweep_whose_worst_case_passes_the_cap_is_refused() -> None:
    exp, plan = make_plan("sonnet-4-6", repeats=3)
    assert check_preflight(exp, plan, 5.0) == preflight_bound_usd(exp, plan)
    with pytest.raises(SweepRefusal, match="above the cap"):
        check_preflight(exp, plan, 1.0)


# --- Phase 2.5: scenarios x objectives x templates x repeats, and the refusals --------------------


def test_a_plan_crosses_scenarios_objectives_templates_and_repeats(tmp_path: Path) -> None:
    exp = company_like(tmp_path, sealed="w3")
    plan = build_plan(
        exp, model_key="nova-lite", label="t", repeats=2, seed=1, templates=["w1", "w2"]
    )
    cells = {(r.scenario_id, r.objective_id, r.wording_id, r.repeat) for r in plan.runs}
    assert len(plan.runs) == len(cells) == 2 * 3 * 2 * 2
    assert plan.scenarios == ("s1", "s2")
    assert plan.templates == ("w1", "w2")
    assert plan.manifest()["templates"] == ["w1", "w2"]
    assert len({r.run_id for r in plan.runs}) == len(plan.runs)


def test_the_scenario_and_template_flags_select_and_unknown_names_are_refused(
    tmp_path: Path,
) -> None:
    exp = company_like(tmp_path, sealed="w3")
    one = build_plan(
        exp, model_key="nova-lite", label="t", repeats=1, seed=1, scenarios=["s2"], templates=["w1"]
    )
    assert {r.scenario_id for r in one.runs} == {"s2"}
    assert len(one.runs) == 3
    with pytest.raises(SweepRefusal, match=r"unknown scenario \['s9'\]; the choices are: s1, s2"):
        build_plan(exp, model_key="nova-lite", label="t", repeats=1, seed=1, scenarios=["s9"])
    with pytest.raises(SweepRefusal, match=r"unknown template \['w9'\]"):
        build_plan(exp, model_key="nova-lite", label="t", repeats=1, seed=1, templates=["w9"])
    with pytest.raises(SweepRefusal, match="named twice"):
        build_plan(exp, model_key="nova-lite", label="t", repeats=1, seed=1, templates=["w1", "w1"])


def test_the_selection_is_part_of_the_sweep_id(tmp_path: Path) -> None:
    exp = company_like(tmp_path, sealed="w3")
    ids = {
        build_plan(
            exp, model_key="nova-lite", label="t", repeats=1, seed=1, scenarios=s, templates=w
        ).sweep_id
        for s, w in [(["s1"], ["w1"]), (["s2"], ["w1"]), (["s1"], ["w2"]), (None, ["w1"])]
    }
    assert len(ids) == 4


def test_the_sealed_template_is_never_part_of_a_development_plan(tmp_path: Path) -> None:
    exp = company_like(tmp_path, sealed="w2")
    with pytest.raises(
        SweepRefusal, match=r"sealed template \(w2\) is never part of a decision prompt"
    ):
        build_plan(exp, model_key="nova-lite", label="t", repeats=1, seed=1, templates=["w1", "w2"])
    with pytest.raises(SweepRefusal, match="sealed template"):
        build_plan(
            exp, model_key="nova-lite", label="t", repeats=1, seed=1
        )  # every template, w2 too
    allowed = build_plan(
        exp, model_key="nova-lite", label="t", repeats=1, seed=1, templates=["w1", "w3"]
    )
    assert {r.wording_id for r in allowed.runs} == {"w1", "w3"}


def test_an_official_plan_may_include_the_sealed_template(tmp_path: Path) -> None:
    """The refusal is for development. The official path has its own gate (the protocol lock)."""
    exp = company_like(tmp_path, sealed="w2")
    plan = build_plan(
        exp, model_key="sonnet-4-6", label="t", repeats=1, seed=1, templates=["w2"], official=True
    )
    assert {r.wording_id for r in plan.runs} == {"w2"}


def test_no_decision_runs_until_the_sealed_template_is_drawn(tmp_path: Path) -> None:
    exp = company_like(tmp_path, sealed="")
    with pytest.raises(SweepRefusal, match="sealed template is not drawn yet"):
        build_plan(exp, model_key="nova-lite", label="t", repeats=1, seed=1)


def test_the_placeholder_has_no_sealed_template_so_it_runs_freely() -> None:
    exp = experiment()
    assert exp.sealed_template is None
    assert build_plan(exp, model_key="nova-lite", label="t", repeats=1, seed=1).runs


def test_real_content_runs_only_on_the_development_model(tmp_path: Path) -> None:
    exp = company_like(tmp_path, sealed="w3")
    assert build_plan(
        exp, model_key="nova-lite", label="t", repeats=1, seed=1, templates=["w1"]
    ).runs
    with pytest.raises(SweepRefusal, match="sonnet-4-6 is not the development model"):
        build_plan(exp, model_key="sonnet-4-6", label="t", repeats=1, seed=1, templates=["w1"])


def test_the_placeholder_may_run_on_any_model() -> None:
    assert build_plan(experiment(), model_key="sonnet-4-6", label="t", repeats=1, seed=1).runs


def test_the_preflight_bound_covers_every_scenario_in_the_plan(tmp_path: Path) -> None:
    exp = company_like(tmp_path, sealed="w3")
    one = build_plan(
        exp, model_key="nova-lite", label="t", repeats=1, seed=1, scenarios=["s1"], templates=["w1"]
    )
    both = build_plan(exp, model_key="nova-lite", label="t", repeats=1, seed=1, templates=["w1"])
    assert preflight_bound_usd(exp, both) == pytest.approx(
        2 * preflight_bound_usd(exp, one), abs=1e-3
    )
