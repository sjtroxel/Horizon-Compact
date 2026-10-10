"""Plans: ids, seeds, order and the preflight bound (Phase 1 IMPLEMENTATION doc sections 6.2 and 6.5)."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

from horizon_compact.experiment import OFF_SUBJECT_EXPERIMENTS, Experiment, load_experiment
from horizon_compact.sweep.plan import (
    MANIFEST_VERSION,
    SweepPlan,
    SweepRefusal,
    build_plan,
    check_preflight,
    manifest_repeats,
    normalize_repeats,
    preflight_bound_usd,
    repeats_from_json,
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


def test_the_off_subject_experiments_are_the_placeholder_and_the_garden_shapes_only() -> None:
    """Phase 3.5 decision 3: the garden shapes run on the official candidates before the tag. Any other
    experiment, the Phase 2.5 S4 shape test included, stays on the development model."""
    assert OFF_SUBJECT_EXPERIMENTS == ("placeholder", "shapes")
    shapes = load_experiment("shapes")
    plan = build_plan(shapes, model_key="sonnet-4-6", label="proxy", repeats=3, seed=1)
    assert len(plan.runs) == 4 * 5 * 3
    with pytest.raises(SweepRefusal, match="s4shape is not off the subject"):
        build_plan(load_experiment("s4shape"), model_key="sonnet-4-6", label="t", repeats=1, seed=1)


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


def test_the_local_model_may_run_real_content_because_it_is_the_development_model(
    tmp_path: Path,
) -> None:
    exp = company_like(tmp_path, sealed="w3")
    plan = build_plan(exp, model_key="qwen-local", label="t", repeats=1, seed=1, templates=["w1"])
    assert plan.runs
    assert preflight_bound_usd(exp, plan) == 0.0


# --- Phase 4 code half, section 4.1: a count for each scenario -------------------------------------------


def _per_scenario(exp: Experiment, repeats: int | dict[str, int]) -> SweepPlan:
    return build_plan(
        exp, model_key="nova-lite", label="t", repeats=repeats, seed=1, templates=["w1"]
    )


def test_a_mapping_expands_to_the_right_number_of_runs_per_scenario(tmp_path: Path) -> None:
    plan = _per_scenario(company_like(tmp_path, sealed="w3"), {"s1": 3, "s2": 1})
    assert len(plan.runs) == 3 * 3 + 1 * 3  # 3 objectives each
    by_scenario: dict[str, set[int]] = {}
    for run in plan.runs:
        by_scenario.setdefault(run.scenario_id, set()).add(run.repeat)
    assert by_scenario == {"s1": {0, 1, 2}, "s2": {0}}
    assert dict(plan.repeats) == {"s1": 3, "s2": 1}
    assert plan.repeats_text() == "s1=3, s2=1"


def test_an_int_and_a_uniform_mapping_are_the_same_plan(tmp_path: Path) -> None:
    exp = company_like(tmp_path, sealed="w3")
    as_int = _per_scenario(exp, 2)
    as_map = _per_scenario(exp, {"s1": 2, "s2": 2})
    assert as_int == as_map
    assert as_int.repeats_text() == "2"


def test_a_sweep_that_has_one_count_everywhere_keeps_the_id_it_had_before() -> None:
    """The id's repeats part was ``str(repeats)``; it still is, so a stored development sweep resumes."""
    exp, plan = make_plan(repeats=3, seed=11)
    legacy = hashlib.sha256(
        "|".join(
            [exp.content_hash, "nova-lite", "t", "3", "11", "garden", ",".join(plan.templates)]
        ).encode("utf-8")
    ).hexdigest()
    assert plan.sweep_id == f"t-nova-lite-{legacy[:8]}"


def test_two_plans_that_differ_in_one_scenarios_count_are_two_sweeps(tmp_path: Path) -> None:
    exp = company_like(tmp_path, sealed="w3")
    a = _per_scenario(exp, {"s1": 3, "s2": 1})
    assert a.sweep_id == _per_scenario(exp, {"s1": 3, "s2": 1}).sweep_id
    assert a.sweep_id != _per_scenario(exp, {"s1": 3, "s2": 2}).sweep_id
    assert a.sweep_id != _per_scenario(exp, 3).sweep_id


def test_the_manifest_holds_the_mapping_at_version_three(tmp_path: Path) -> None:
    exp = company_like(tmp_path, sealed="w3")
    manifest = _per_scenario(exp, {"s1": 3, "s2": 1}).manifest()
    assert MANIFEST_VERSION == 3
    assert manifest["manifest_version"] == 3
    assert manifest["repeats"] == {"s1": 3, "s2": 1}


def test_a_mapping_that_misses_or_adds_a_scenario_is_refused_naming_it(tmp_path: Path) -> None:
    exp = company_like(tmp_path, sealed="w3")
    kw = {"model_key": "nova-lite", "label": "t", "seed": 1, "templates": ["w1"]}
    with pytest.raises(SweepRefusal, match=r"no count for scenario\(s\) \['s2'\]"):
        build_plan(exp, repeats={"s1": 3}, **kw)  # type: ignore[arg-type]
    with pytest.raises(SweepRefusal, match=r"scenario\(s\) \['s9'\]"):
        build_plan(exp, repeats={"s1": 3, "s2": 1, "s9": 1}, **kw)  # type: ignore[arg-type]
    with pytest.raises(SweepRefusal, match=r"scenario\(s\) \['s2'\]"):  # a subset needs a subset
        build_plan(exp, repeats={"s1": 3, "s2": 1}, scenarios=["s1"], **kw)  # type: ignore[arg-type]


def test_a_count_below_one_or_not_a_whole_number_is_refused(tmp_path: Path) -> None:
    exp = company_like(tmp_path, sealed="w3")
    kw = {"model_key": "nova-lite", "label": "t", "seed": 1, "templates": ["w1"]}
    bad_counts: list[object] = [0, -1, 2.5, True, "3"]
    for bad in bad_counts:
        with pytest.raises(ValueError, match="repeats for s2"):
            build_plan(exp, repeats={"s1": 3, "s2": bad}, **kw)  # type: ignore[arg-type,dict-item]
    with pytest.raises(ValueError, match="at least 1"):
        normalize_repeats(True, ("s1",))


def test_a_version_two_manifest_is_read_as_the_same_count_everywhere() -> None:
    v2 = {"manifest_version": 2, "repeats": 4, "scenarios": ["s1", "s2"], "runs": []}
    assert manifest_repeats(v2) == {"s1": 4, "s2": 4}
    v1ish = {"repeats": 2, "runs": [{"scenario_id": "garden"}, {"scenario_id": "garden"}]}
    assert manifest_repeats(v1ish) == {"garden": 2}
    assert manifest_repeats({"repeats": {"s1": 3, "s2": 1}, "runs": []}) == {"s1": 3, "s2": 1}


def test_a_repeats_file_may_be_a_pilots_record_or_a_plain_mapping() -> None:
    record = {
        "protocol": "prereg-v1",
        "scenarios": [
            {"kind": "ShareRepeats", "scenario_id": "s1", "repeats": 20},
            {"kind": "ChoiceRepeats", "scenario_id": "s3", "repeats": 10},
        ],
    }
    assert repeats_from_json(record) == {"s1": 20, "s3": 10}
    assert repeats_from_json({"s1": 20, "s3": 10}) == {"s1": 20, "s3": 10}
    refused: list[object] = [
        [],
        {},
        "x",
        {"s1": "20"},
        {"s1": 20.7},
        {"s1": True},
        {"scenarios": [{"scenario_id": "s1"}]},
        {"scenarios": [{"scenario_id": "s1", "repeats": 20.7}]},
        {"scenarios": [{"scenario_id": "s1", "repeats": "20"}]},
        {"scenarios": [{"scenario_id": "s1", "repeats": True}]},
        {"scenarios": [{"scenario_id": "s1", "repeats": 2}, {"scenario_id": "s1", "repeats": 3}]},
        {"scenarios": [{"scenario_id": 1, "repeats": 2}]},
    ]
    for bad in refused:
        with pytest.raises(SweepRefusal):
            repeats_from_json(bad)
