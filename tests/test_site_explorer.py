"""The explorer-data builder and ``hc site explorer`` (Phase 6 IMPLEMENTATION doc sections 5, 15, 19).

The fixtures are fictional: two model keys, four scenarios, five objectives, two cases, written here in the
shape the frozen analysis writes, never copies of a real file. The last group of tests reads the real
``experiment/results/`` and compares the committed ``web/explorer-data/`` with a fresh build, byte for byte:
that is Phase 6's reproduction check, and CI runs it because CI runs pytest.
"""

from __future__ import annotations

import copy
import hashlib
import json
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from horizon_compact.cli import CLEAN_EXIT, REFUSED_EXIT, main
from horizon_compact.site import explorer
from horizon_compact.site.explorer import (
    EXPECTED_TO_CUT_LESS,
    MAX_SAFE_INTEGER,
    PRIMARY_OUTCOME_NAMES,
    PRIMARY_PAIRS,
    SECOND_CUT_MORE_SIGN,
    ExplorerDataRefusal,
    build_explorer_data,
    explorer_data_matches,
    write_explorer_data,
)

REPO = Path(__file__).resolve().parent.parent
REAL_RESULTS = REPO / "experiment" / "results"
REAL_OUT = REPO / "web" / "explorer-data"

MAIN_MODEL = "haiku-5-5"
OTHER_MODEL = "alpha-model"
MODELS = (OTHER_MODEL, MAIN_MODEL)  # sorted, as the builder sorts them
SCENARIOS = ("s1", "s2", "s3", "s4")
BIG_SEED = 51708200104990895674395918064214010461
OBJECTIVES = "ABCDE"

Obj = dict[str, Any]

# (final_verdict, difference) for a comparison; the key is (model_key, scenario_id, first, second).
Verdicts = dict[tuple[str, str, str, str], tuple[str, float | None]]


def _comparison(sid: str, pair: tuple[str, str], role: str, verdict: str, difference: Any) -> Obj:
    return {
        "scenario_id": sid,
        "first": pair[0],
        "second": pair[1],
        "role": role,
        "label": role,
        "outcome": PRIMARY_OUTCOME_NAMES[sid],
        "kind": "share",
        "threshold": 0.1,
        "method": "welch",
        "difference": difference,
        "low": None if difference is None else difference - 0.05,
        "high": None if difference is None else difference + 0.05,
        "valid_runs": [["w1", 20, 20], ["w2", 20, 20], ["w3", 20, 20]],
        "kept_wordings": ["w1", "w2", "w3"],
        "dropped_wordings": [],
        "final_verdict": verdict,
        "downgrade_reason": None,
        "headline": f"{verdict}, over wordings w1, w2 and w3",
        "per_wording": [{"wording_id": "w1", "first_value": 0.1 + 0.2, "n_first": 20}],
    }


def _scenario(model: str, sid: str, verdicts: Verdicts) -> Obj:
    comparisons = []
    for pair in (*PRIMARY_PAIRS, ("A", "D")):
        role = "secondary" if pair == ("A", "D") else "primary"
        verdict, difference = verdicts.get((model, sid, *pair), ("inconclusive", 0.0))
        comparisons.append(_comparison(sid, pair, role, verdict, difference))
    return {
        "scenario_id": sid,
        "primary_outcome": PRIMARY_OUTCOME_NAMES[sid],
        "kind": "share",
        "threshold": 0.1,
        "comparisons": comparisons,
        "cells": [{"objective_id": o, "wording_id": "w1", "valid": 20} for o in OBJECTIVES],
        "descriptive": {"runs": 2, "per_run": [{"run_id": "r-123456789012", "value": 1e22}]},
    }


def _results_file(model: str, sweep: str, verdicts: Verdicts, only: tuple[str, ...]) -> Obj:
    return {
        "results_version": 2,
        "experiment": "company",
        "sweep_id": sweep,
        "model_key": model,
        "alpha": 0.003125,
        "descriptive_alpha": 0.05,
        "sealed_wording": "w2",
        "refusal_calls": [],
        "scenarios": [_scenario(model, sid, verdicts) for sid in only],
        "scenarios_without_runs": [],
    }


def _distance(objective: str, distance: float, low: float, high: float) -> Obj:
    return {
        "objective_id": objective,
        "distance": distance,
        "low": low,
        "high": high,
        "seed": BIG_SEED + ord(objective),
        "runs": 30,
    }


def _reading(name: str, lines: list[str], equal: bool) -> Obj:
    distances = [
        _distance(o, 1.0 if equal else 0.5 + 0.1 * i, 1.0 if equal else 0.4, 1.0)
        for i, o in enumerate(OBJECTIVES)
    ]
    return {
        "reading": name,
        "observable_lines": lines,
        "label": "no_good_match",
        "gap": {"seed": BIG_SEED, "estimate": 0.0},
        "distances": distances,
    }


def _case_result(label: str, model: str, hexid: str) -> Obj:
    return {
        "results_version": 1,
        "case": label,
        "type": "closure",
        "exploratory": True,
        "exploratory_label": "exploratory: fixture label",
        "experiment": f"case-{label}",
        "scenario_id": "s3",
        "model_key": model,
        "sweep_id": f"case-{model}-{hexid}",
        "readings": [
            _reading("primary", [], equal=True),
            _reading("u1", ["eliminated"], equal=False),
        ],
        "depends_on_reading": True,
    }


def _cases_index() -> Obj:
    published = {
        "status": "published",
        "level": 0,
        "sector": "Fixture Sector",
        "text": "Fixture Sector; plant closure.",
    }
    withheld = {"status": "withheld", "reason": "withheld: fixture reason"}
    base = {
        "type": "closure",
        "shape": "s3",
        "exploratory": True,
        "exploratory_label": "exploratory: fixture label",
        "dossier": {"published": False, "reason": "withheld: fixture reason"},
        "reidentification": {"status": "withheld", "reason": "fixture", "threshold": 20},
        "probes": [{"set": 1, "model": MAIN_MODEL, "calls": 3, "passed": 3}],
        "probe_set": 1,
        "content_sha256": {"dossier": "0" * 64},
    }
    return {
        "cases_version": 1,
        "cases": [
            {"label": "case-one", "description": published, **base},
            {"label": "case-two", "description": withheld, **base},
        ],
        "shortfall": {"at_most": 5, "cases": 2},
        "provenance": {"head": "abc"},
    }


OBJECTIVES_TOML = """\
sealed_template = "w2"

[[objectives]]
id = "A"
who = "shareholders"
when = "the next four quarters"

[[objectives]]
id = "E"
"""


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1), encoding="utf-8")


def make_tree(tmp_path: Path, verdicts: Verdicts | None = None) -> Path:
    """A fixture ``experiment/results`` tree; returns that folder."""
    verdicts = verdicts or {}
    root = tmp_path / "experiment" / "results"
    (tmp_path / "experiment" / "company").mkdir(parents=True)
    (tmp_path / "experiment" / "company" / "objectives.toml").write_text(OBJECTIVES_TOML)
    for model, hexid in ((OTHER_MODEL, "aaaa1111"), (MAIN_MODEL, "bbbb2222")):
        sweep = f"grid-{model}-{hexid}"
        _write_json(
            root / "prereg-v1" / model / f"{sweep}.json",
            _results_file(model, sweep, verdicts, SCENARIOS),
        )
    thinking = f"thinking-{MAIN_MODEL}-cccc3333"
    # The thinking file is all "no split" on purpose: the rule must never read it.
    every_no_split: Verdicts = {
        (MAIN_MODEL, "s1", *pair): ("no_split", 0.0) for pair in PRIMARY_PAIRS
    }
    _write_json(
        root / "prereg-v1" / MAIN_MODEL / f"{thinking}.json",
        _results_file(MAIN_MODEL, thinking, every_no_split, ("s1",)),
    )
    _write_json(root / "cases" / "cases.json", _cases_index())
    for label in ("case-one", "case-two"):
        for model in MODELS:
            _write_json(
                root / "cases" / label / f"{model}.json", _case_result(label, model, "dddd4444")
            )
    return root


def _edit(path: Path, change: Callable[[Obj], None]) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(json.dumps(data, indent=1), encoding="utf-8")


def _grid_path(root: Path, model: str = MAIN_MODEL) -> Path:
    return next((root / "prereg-v1" / model).glob("grid-*.json"))


def _index(files: dict[str, str]) -> Obj:
    result: Obj = json.loads(files["index.json"])
    return result


# --- the shape of the output ------------------------------------------------------------------------------


def test_the_build_returns_compact_json_files_ending_in_one_newline(tmp_path: Path) -> None:
    files = build_explorer_data(make_tree(tmp_path))
    assert "index.json" in files and "cases/index.json" in files
    assert f"grid/{MAIN_MODEL}/s1.json" in files and f"thinking/{MAIN_MODEL}/s1.json" in files
    assert f"cases/case-one/{OTHER_MODEL}.json" in files
    assert not any("memo" in path for path in files)
    for path, text in files.items():
        assert text.endswith("}\n") and not text.endswith("\n\n"), path
        compact = json.dumps(json.loads(text), ensure_ascii=False, separators=(",", ":"))
        assert text == compact + "\n", path


def test_a_second_build_is_byte_identical(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    assert build_explorer_data(root) == build_explorer_data(root)


def test_the_index_names_models_scenarios_objectives_and_sources(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    index = _index(build_explorer_data(root))
    assert index["explorer_data_version"] == 1
    assert [m["model_key"] for m in index["models"]] == list(MODELS)
    assert index["models"][1] == {
        "model_key": MAIN_MODEL,
        "sweep_id": f"grid-{MAIN_MODEL}-bbbb2222",
        "alpha": 0.003125,
        "descriptive_alpha": 0.05,
        "sealed_wording": "w2",
    }
    assert [s["scenario_id"] for s in index["scenarios"]] == list(SCENARIOS)
    assert index["scenarios"][2]["primary_outcome"] == "close rate"
    assert index["objectives"] == [
        {"id": "A", "who": "shareholders", "when": "the next four quarters"},
        {"id": "E", "who": None, "when": None},
    ]
    grid_file = _grid_path(root)
    shown = f"experiment/results/prereg-v1/{MAIN_MODEL}/{grid_file.name}"
    sha = hashlib.sha256(grid_file.read_bytes()).hexdigest()
    assert {"path": shown, "sha256": sha} in index["sources"]
    paths = [s["path"] for s in index["sources"]]
    assert paths == sorted(paths)
    assert "experiment/company/objectives.toml" in paths
    assert not any("memos" in p or "reident" in p for p in paths)
    assert len(index["verdicts"]) == len(MODELS) * len(SCENARIOS)
    assert len(index["verdicts"][0]["comparisons"]) == 5


def test_a_grid_file_is_the_scenario_whole_plus_the_model_and_sweep(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    source = json.loads(_grid_path(root).read_text())["scenarios"][1]
    body = json.loads(build_explorer_data(root)[f"grid/{MAIN_MODEL}/s2.json"])
    assert body.pop("model_key") == MAIN_MODEL
    assert body.pop("sweep_id") == f"grid-{MAIN_MODEL}-bbbb2222"
    assert body == source


def test_the_cases_index_copies_the_listed_fields_and_not_the_rest(tmp_path: Path) -> None:
    document = json.loads(build_explorer_data(make_tree(tmp_path))["cases/index.json"])
    assert document["shortfall"] == {"at_most": 5, "cases": 2}
    assert document["provenance"] == {"head": "abc"}
    one, two = document["cases"]
    assert one["description"]["text"] == "Fixture Sector; plant closure."
    assert two["description"] == {"status": "withheld", "reason": "withheld: fixture reason"}
    assert one["exploratory_label"] == "exploratory: fixture label"
    assert "probe_set" not in one and "content_sha256" not in one


# --- one encoding change: big integers --------------------------------------------------------------------


def test_an_integer_above_two_to_the_53rd_is_written_as_a_string(tmp_path: Path) -> None:
    files = build_explorer_data(make_tree(tmp_path))
    result = json.loads(files[f"cases/case-one/{MAIN_MODEL}.json"])
    seed = result["readings"][0]["gap"]["seed"]
    assert seed == str(BIG_SEED) and isinstance(seed, str)
    assert f'"seed":"{BIG_SEED}"' in files[f"cases/case-one/{MAIN_MODEL}.json"]
    assert result["readings"][0]["distances"][0]["runs"] == 30  # a small integer stays a number


def test_the_boundary_of_the_encoding_and_what_it_leaves_alone() -> None:
    safe = explorer._safe_integers
    assert safe(MAX_SAFE_INTEGER) == MAX_SAFE_INTEGER
    assert safe(MAX_SAFE_INTEGER + 1) == str(MAX_SAFE_INTEGER + 1)
    assert safe(-MAX_SAFE_INTEGER) == -MAX_SAFE_INTEGER
    assert safe(-MAX_SAFE_INTEGER - 1) == str(-MAX_SAFE_INTEGER - 1)
    assert safe(True) is True and safe(None) is None and safe("text") == "text"
    assert safe({"a": [2**60, 1]}) == {"a": [str(2**60), 1]}


def test_no_float_is_changed_by_the_round_trip(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    floats = [0.1 + 0.2, 1e22, 5e-324, 1.7976931348623157e308, -0.0, 1.0, 0.003125]
    _edit(_grid_path(root), lambda d: d["scenarios"][0].__setitem__("floats", floats))
    body = json.loads(build_explorer_data(root)[f"grid/{MAIN_MODEL}/s1.json"])
    assert body["floats"] == floats
    assert [type(v) for v in body["floats"]] == [float] * len(floats)
    assert str(body["floats"][0]) == "0.30000000000000004"


# --- what it refuses ---------------------------------------------------------------------------------------


def _refuses(root: Path, message: str) -> None:
    with pytest.raises(ExplorerDataRefusal) as info:
        build_explorer_data(root)
    assert message in str(info.value)


def test_it_refuses_a_file_it_does_not_expect_under_a_model_folder(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    (root / "prereg-v1" / MAIN_MODEL / "notes.json").write_text("{}")
    _refuses(root, "not an expected file")


def test_it_refuses_a_loose_file_beside_the_model_folders(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    (root / "prereg-v1" / "README.md").write_text("x")
    _refuses(root, "is not a model folder")


def test_it_refuses_a_second_grid_for_one_model(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    grid = _grid_path(root)
    twin = grid.with_name(f"grid-{MAIN_MODEL}-eeee5555.json")
    twin.write_text(grid.read_text().replace("bbbb2222", "eeee5555"))
    _refuses(root, "2 grid files, not one")


def test_it_refuses_a_thinking_file_in_another_models_folder(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    src = next((root / "prereg-v1" / MAIN_MODEL).glob("thinking-*.json"))
    (root / "prereg-v1" / OTHER_MODEL / src.name).write_text(src.read_text())
    _refuses(root, "not an expected file")


def test_it_refuses_a_missing_or_doubled_thinking_file(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    src = next((root / "prereg-v1" / MAIN_MODEL).glob("thinking-*.json"))
    twin = src.with_name(f"thinking-{MAIN_MODEL}-ffff6666.json")
    twin.write_text(src.read_text().replace("cccc3333", "ffff6666"))
    _refuses(root, "2 thinking files, not one")
    twin.unlink()
    src.unlink()
    _refuses(root, "0 thinking files, not one")


@pytest.mark.parametrize("version", [1, 3, None])
def test_it_refuses_a_grid_of_the_wrong_results_version(tmp_path: Path, version: Any) -> None:
    root = make_tree(tmp_path)
    _edit(_grid_path(root), lambda d: d.__setitem__("results_version", version))
    _refuses(root, "has results_version")


def test_it_refuses_a_case_result_of_the_wrong_results_version(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    _edit(
        root / "cases" / "case-one" / f"{MAIN_MODEL}.json",
        lambda d: d.__setitem__("results_version", 2),
    )
    _refuses(root, "has results_version 2, not 1")


def test_it_refuses_a_model_key_or_sweep_id_that_does_not_match_the_filename(
    tmp_path: Path,
) -> None:
    root = make_tree(tmp_path)
    grid = _grid_path(root)
    original = grid.read_text()
    _edit(grid, lambda d: d.__setitem__("model_key", "other"))
    _refuses(root, "has model_key 'other'")
    grid.write_text(original)
    _edit(grid, lambda d: d.__setitem__("sweep_id", "grid-haiku-5-5-0000"))
    _refuses(root, "has sweep_id")
    grid.write_text(original)
    case = root / "cases" / "case-one" / f"{MAIN_MODEL}.json"
    _edit(case, lambda d: d.__setitem__("sweep_id", f"case-{OTHER_MODEL}-dddd4444"))
    _refuses(root, "has sweep_id")


def test_it_refuses_an_exploratory_case_with_no_label(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    _edit(
        root / "cases" / "cases.json",
        lambda d: d["cases"][0].pop("exploratory_label"),
    )
    _refuses(root, "is exploratory and has no exploratory_label")


def test_it_refuses_an_exploratory_case_result_with_no_label(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    for model in MODELS:
        _edit(root / "cases" / "case-one" / f"{model}.json", lambda d: d.pop("exploratory_label"))
    _edit(root / "cases" / "cases.json", lambda d: d["cases"][0].pop("exploratory_label"))
    _refuses(root, "has no exploratory_label")


def test_it_refuses_a_case_result_whose_label_differs_from_the_index(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    _edit(
        root / "cases" / "case-one" / f"{MAIN_MODEL}.json",
        lambda d: d.__setitem__("exploratory_label", "exploratory: another"),
    )
    _refuses(root, "disagree")


def test_it_refuses_a_published_description_without_text(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    _edit(root / "cases" / "cases.json", lambda d: d["cases"][0]["description"].pop("text"))
    _refuses(root, "published without text")


@pytest.mark.parametrize("field", ["text", "sector", "level"])
def test_it_refuses_a_withheld_description_that_carries_more_than_status_and_reason(
    tmp_path: Path, field: str
) -> None:
    root = make_tree(tmp_path)
    _edit(
        root / "cases" / "cases.json",
        lambda d: d["cases"][1]["description"].__setitem__(field, "x"),
    )
    _refuses(root, "is not published and carries")


def test_it_refuses_a_primary_outcome_section_19_was_not_written_for(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    _edit(_grid_path(root), lambda d: d["scenarios"][0].__setitem__("primary_outcome", "kept"))
    _refuses(root, "the primary outcome is 'kept'")


def test_it_refuses_a_comparison_outcome_section_19_was_not_written_for(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    _edit(
        _grid_path(root),
        lambda d: d["scenarios"][2]["comparisons"][0].__setitem__("outcome", "fund rate"),
    )
    _refuses(root, "section 19 expects 'close rate'")


def test_it_refuses_a_scenario_id_section_19_does_not_hold(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    _edit(_grid_path(root), lambda d: d["scenarios"][0].__setitem__("scenario_id", "s9"))
    _refuses(root, "not a scenario section 19's tables hold")


def test_it_refuses_a_primary_pair_not_in_section_19(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    _edit(
        _grid_path(root),
        lambda d: d["scenarios"][0]["comparisons"][0].__setitem__("second", "E"),
    )
    _refuses(root, "not in section 19's table")


def test_it_refuses_a_scenario_missing_one_of_the_four_primary_pairs(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    _edit(_grid_path(root), lambda d: d["scenarios"][0]["comparisons"].pop(0))
    _refuses(root, "not section 19's four")


def test_it_refuses_a_split_whose_difference_is_exactly_zero(tmp_path: Path) -> None:
    root = make_tree(tmp_path, {(MAIN_MODEL, "s1", "A", "C"): ("split", 0.0)})
    _refuses(root, "the rule has no sign to read")


def test_it_refuses_a_split_with_no_difference(tmp_path: Path) -> None:
    root = make_tree(tmp_path, {(MAIN_MODEL, "s1", "A", "C"): ("split", None)})
    _refuses(root, "the rule has no sign to read")


def test_it_refuses_a_verdict_it_does_not_know(tmp_path: Path) -> None:
    root = make_tree(tmp_path, {(MAIN_MODEL, "s1", "A", "C"): ("maybe", 0.1)})
    _refuses(root, "unknown verdict 'maybe'")


def test_it_refuses_a_scenario_whose_threshold_differs_between_files(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    _edit(_grid_path(root), lambda d: d["scenarios"][0].__setitem__("threshold", 0.2))
    _refuses(root, "different outcome, kind or threshold")


def test_it_refuses_an_output_holding_an_arn(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    _edit(
        _grid_path(root),
        lambda d: d["scenarios"][0]["comparisons"][0].__setitem__(
            "headline", "arn:aws:s3:::somewhere"
        ),
    )
    _refuses(root, "ARN or the results bucket's name")


def test_it_refuses_an_output_holding_the_results_bucket_name(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    _edit(
        root / "cases" / "case-one" / f"{MAIN_MODEL}.json",
        lambda d: d.__setitem__("note", "horizon-compact-results-123456789012"),
    )
    _refuses(root, "ARN or the results bucket's name")


def test_a_bare_twelve_digit_run_id_is_not_refused(tmp_path: Path) -> None:
    """Eight committed run ids are r- plus twelve digits; Phase 1.5's account-id regex would refuse them."""
    files = build_explorer_data(make_tree(tmp_path))
    assert "r-123456789012" in files[f"grid/{MAIN_MODEL}/s1.json"]


# --- the matcher's two notes --------------------------------------------------------------------------------


def test_each_case_reading_carries_both_notes_true_and_false(tmp_path: Path) -> None:
    files = build_explorer_data(make_tree(tmp_path))
    for model in MODELS:
        primary, u1 = json.loads(files[f"cases/case-one/{model}.json"])["readings"]
        assert primary["all_distances_equal"] is True
        assert primary["one_observable_line"] is False  # no lines at all
        assert u1["all_distances_equal"] is False
        assert u1["one_observable_line"] is True


def test_all_distances_equal_needs_the_interval_to_be_equal_too(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    path = root / "cases" / "case-one" / f"{MAIN_MODEL}.json"
    _edit(path, lambda d: d["readings"][0]["distances"][4].__setitem__("high", 0.9))
    reading = json.loads(build_explorer_data(root)[f"cases/case-one/{MAIN_MODEL}.json"])[
        "readings"
    ][0]
    assert reading["all_distances_equal"] is False


def test_one_observable_line_is_false_for_two_lines(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    path = root / "cases" / "case-one" / f"{MAIN_MODEL}.json"
    _edit(path, lambda d: d["readings"][1].__setitem__("observable_lines", ["a", "b"]))
    reading = json.loads(build_explorer_data(root)[f"cases/case-one/{MAIN_MODEL}.json"])[
        "readings"
    ][1]
    assert reading["one_observable_line"] is False


def test_it_refuses_a_reading_without_five_distances(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    path = root / "cases" / "case-one" / f"{MAIN_MODEL}.json"
    _edit(path, lambda d: d["readings"][0]["distances"].pop())
    _refuses(root, "a reading without five distances")


# --- section 19: the rule --------------------------------------------------------------------------------


def _entries(files: dict[str, str]) -> list[Obj]:
    entries: list[Obj] = _index(files)["against_thesis"]["entries"]
    return entries


def _coords(entry: Obj) -> tuple[str, str, str, str]:
    return (entry["model_key"], entry["scenario_id"], entry["first"], entry["second"])


def test_the_constants_are_section_19s_tables() -> None:
    assert PRIMARY_PAIRS == (("A", "C"), ("A", "B"), ("C", "D"), ("B", "D"))
    assert EXPECTED_TO_CUT_LESS == {
        ("A", "C"): "C",
        ("A", "B"): "B",
        ("C", "D"): "D",
        ("B", "D"): "D",
    }
    assert SECOND_CUT_MORE_SIGN == {"s1": 1, "s2": -1, "s3": -1, "s4": 1}
    assert PRIMARY_OUTCOME_NAMES == {
        "s1": "share kept",
        "s2": "share borne by the workforce",
        "s3": "close rate",
        "s4": "fund rate",
    }


def test_a_primary_no_split_is_listed_with_its_clause_and_copied_fields(tmp_path: Path) -> None:
    root = make_tree(tmp_path, {(MAIN_MODEL, "s2", "B", "D"): ("no_split", 0.01)})
    (entry,) = _entries(build_explorer_data(root))
    source = json.loads(_grid_path(root).read_text())["scenarios"][1]["comparisons"][3]
    assert entry["clause"] == "no_split"
    assert entry["roundtable_pair"] is False
    assert (entry["model_key"], entry["scenario_id"], entry["first"], entry["second"]) == (
        MAIN_MODEL,
        "s2",
        "B",
        "D",
    )
    assert entry["sweep_id"] == f"grid-{MAIN_MODEL}-bbbb2222"
    for field in explorer._ENTRY_FIELDS:
        assert entry[field] == source[field]
    assert set(entry) == {
        "model_key",
        "sweep_id",
        "scenario_id",
        "first",
        "second",
        "clause",
        "roundtable_pair",
        *explorer._ENTRY_FIELDS,
    }


def test_only_c_versus_d_is_the_roundtable_pair(tmp_path: Path) -> None:
    verdicts: Verdicts = {(MAIN_MODEL, "s1", *pair): ("no_split", 0.0) for pair in PRIMARY_PAIRS}
    entries = _entries(build_explorer_data(make_tree(tmp_path, verdicts)))
    assert {(e["first"], e["second"]): e["roundtable_pair"] for e in entries} == {
        ("A", "C"): False,
        ("A", "B"): False,
        ("C", "D"): True,
        ("B", "D"): False,
    }


@pytest.mark.parametrize("sid", SCENARIOS)
@pytest.mark.parametrize("pair", PRIMARY_PAIRS)
def test_a_split_is_listed_only_when_the_second_objective_cut_more(
    tmp_path: Path, sid: str, pair: tuple[str, str]
) -> None:
    sign = SECOND_CUT_MORE_SIGN[sid]
    listed = make_tree(tmp_path / "listed", {(MAIN_MODEL, sid, *pair): ("split", 0.3 * sign)})
    (entry,) = _entries(build_explorer_data(listed))
    assert entry["clause"] == "reversed_split"
    assert _coords(entry) == (MAIN_MODEL, sid, *pair)
    expected = make_tree(tmp_path / "expected", {(MAIN_MODEL, sid, *pair): ("split", -0.3 * sign)})
    assert _entries(build_explorer_data(expected)) == []


@pytest.mark.parametrize("verdict", ["inconclusive", "not_assessable"])
def test_an_inconclusive_or_not_assessable_verdict_is_never_listed(
    tmp_path: Path, verdict: str
) -> None:
    verdicts: Verdicts = {
        (model, sid, *pair): (verdict, None if verdict == "not_assessable" else 0.5)
        for model in MODELS
        for sid in SCENARIOS
        for pair in PRIMARY_PAIRS
    }
    index = _index(build_explorer_data(make_tree(tmp_path, verdicts)))
    assert index["against_thesis"]["entries"] == []
    assert index["against_thesis"]["scenarios"] == []


def test_the_secondary_comparison_is_never_read(tmp_path: Path) -> None:
    verdicts: Verdicts = {
        (model, sid, "A", "D"): ("no_split", 0.0) for model in MODELS for sid in SCENARIOS
    }
    assert _entries(build_explorer_data(make_tree(tmp_path, verdicts))) == []
    reversed_secondary: Verdicts = {
        (model, sid, "A", "D"): ("split", 0.4 * SECOND_CUT_MORE_SIGN[sid])
        for model in MODELS
        for sid in SCENARIOS
    }
    assert _entries(build_explorer_data(make_tree(tmp_path / "again", reversed_secondary))) == []


def test_the_thinking_file_is_never_read(tmp_path: Path) -> None:
    """make_tree's thinking file is all no_split on s1, and nothing from it reaches the rule."""
    index = _index(build_explorer_data(make_tree(tmp_path)))
    assert index["against_thesis"]["entries"] == []
    assert all("thinking" not in v["sweep_id"] for v in index["verdicts"])


def test_two_models_are_never_merged(tmp_path: Path) -> None:
    verdicts: Verdicts = {
        (OTHER_MODEL, "s3", "A", "C"): ("no_split", 0.0),
        (MAIN_MODEL, "s3", "C", "D"): ("no_split", 0.0),
    }
    index = _index(build_explorer_data(make_tree(tmp_path, verdicts)))
    assert [(_coords(e)) for e in index["against_thesis"]["entries"]] == [
        (OTHER_MODEL, "s3", "A", "C"),
        (MAIN_MODEL, "s3", "C", "D"),
    ]
    sweeps = {e["model_key"]: e["sweep_id"] for e in index["against_thesis"]["entries"]}
    assert sweeps == {
        OTHER_MODEL: f"grid-{OTHER_MODEL}-aaaa1111",
        MAIN_MODEL: f"grid-{MAIN_MODEL}-bbbb2222",
    }


def test_a_scenario_is_listed_whole_only_when_its_four_primaries_are_all_no_split(
    tmp_path: Path,
) -> None:
    whole: Verdicts = {(OTHER_MODEL, "s2", *pair): ("no_split", 0.0) for pair in PRIMARY_PAIRS}
    # Three of four on s3 for one model: not whole. Two and two across the models on s4: not whole.
    for pair in PRIMARY_PAIRS[:3]:
        whole[(MAIN_MODEL, "s3", *pair)] = ("no_split", 0.0)
    for pair in PRIMARY_PAIRS[:2]:
        whole[(OTHER_MODEL, "s4", *pair)] = ("no_split", 0.0)
    for pair in PRIMARY_PAIRS[2:]:
        whole[(MAIN_MODEL, "s4", *pair)] = ("no_split", 0.0)
    index = _index(build_explorer_data(make_tree(tmp_path, whole)))
    assert index["against_thesis"]["scenarios"] == [{"model_key": OTHER_MODEL, "scenario_id": "s2"}]
    assert len(index["against_thesis"]["entries"]) == 4 + 3 + 2 + 2


def test_a_scenario_with_a_reversed_split_among_its_no_splits_is_not_whole(tmp_path: Path) -> None:
    verdicts: Verdicts = {
        (MAIN_MODEL, "s1", *pair): ("no_split", 0.0) for pair in PRIMARY_PAIRS[:3]
    }
    verdicts[(MAIN_MODEL, "s1", "B", "D")] = (
        "split",
        0.3,
    )  # s1: above zero means the second cut more
    index = _index(build_explorer_data(make_tree(tmp_path, verdicts)))
    assert index["against_thesis"]["scenarios"] == []
    assert [e["clause"] for e in index["against_thesis"]["entries"]] == [
        "no_split",
        "no_split",
        "no_split",
        "reversed_split",
    ]


def test_entries_are_ordered_by_model_then_scenario_then_protocol_pair(tmp_path: Path) -> None:
    verdicts: Verdicts = {
        (model, sid, *pair): ("no_split", 0.0)
        for model in MODELS
        for sid in ("s3", "s1")
        for pair in PRIMARY_PAIRS
    }
    entries = _entries(build_explorer_data(make_tree(tmp_path, verdicts)))
    order = [(m, s, p) for m in MODELS for s in ("s1", "s3") for p in PRIMARY_PAIRS]
    assert [(e["model_key"], e["scenario_id"], (e["first"], e["second"])) for e in entries] == order


def test_the_rule_carries_its_name_and_no_prose(tmp_path: Path) -> None:
    block = _index(build_explorer_data(make_tree(tmp_path)))["against_thesis"]
    assert set(block) == {"rule", "entries", "scenarios"}
    assert block["rule"] == "Phase 6 IMPLEMENTATION doc §19, 2026-11-09"


# --- the writer -------------------------------------------------------------------------------------------


def _built(tmp_path: Path) -> dict[str, str]:
    return build_explorer_data(make_tree(tmp_path / "src"))


def test_the_writer_writes_the_files_and_nothing_else(tmp_path: Path) -> None:
    files = _built(tmp_path)
    out = tmp_path / "web" / "explorer-data"
    assert write_explorer_data(files, out) == out
    written = {p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()}
    assert written == set(files)
    assert all((out / k).read_text(encoding="utf-8") == v for k, v in files.items())
    assert [p.name for p in out.parent.iterdir()] == ["explorer-data"]  # no temporary left


def test_the_writer_uses_unix_newlines(tmp_path: Path) -> None:
    out = tmp_path / "explorer-data"
    write_explorer_data(_built(tmp_path), out)
    assert b"\r" not in (out / "index.json").read_bytes()


def test_the_same_bytes_again_is_a_no_op(tmp_path: Path) -> None:
    files = _built(tmp_path)
    out = tmp_path / "explorer-data"
    write_explorer_data(files, out)
    assert explorer_data_matches(files, out)
    marker = out / "index.json"
    before = (marker.stat().st_ino, marker.stat().st_mtime_ns)
    write_explorer_data(files, out)
    assert (marker.stat().st_ino, marker.stat().st_mtime_ns) == before


def test_the_writer_replaces_the_directory_whole_so_no_stale_file_lingers(tmp_path: Path) -> None:
    files = _built(tmp_path)
    out = tmp_path / "explorer-data"
    write_explorer_data(files, out)
    stale = out / "grid" / MAIN_MODEL / "s9.json"
    stale.write_text("{}\n")
    assert not explorer_data_matches(files, out)
    write_explorer_data(files, out)
    assert not stale.exists()
    assert explorer_data_matches(files, out)


def test_the_writer_replaces_different_bytes(tmp_path: Path) -> None:
    files = _built(tmp_path)
    out = tmp_path / "explorer-data"
    write_explorer_data(files, out)
    changed = {**files, "index.json": files["index.json"].replace("1", "2", 1)}
    write_explorer_data(changed, out)
    assert (out / "index.json").read_text() == changed["index.json"]


def test_the_writer_refuses_an_output_folder_with_another_name(tmp_path: Path) -> None:
    with pytest.raises(ExplorerDataRefusal, match="must be named explorer-data"):
        write_explorer_data(_built(tmp_path), tmp_path / "somewhere-else")
    assert not (tmp_path / "somewhere-else").exists()


@pytest.mark.parametrize(
    "name", ["notes.txt", "memos/m.jsonl", "grid/haiku-5-5/s1.jsonl", "extra.json", "grid/s1.json"]
)
def test_the_writer_refuses_to_replace_a_directory_holding_anything_else(
    tmp_path: Path, name: str
) -> None:
    files = _built(tmp_path)
    out = tmp_path / "explorer-data"
    write_explorer_data(files, out)
    other = out / name
    other.parent.mkdir(parents=True, exist_ok=True)
    other.write_text("keep me")
    with pytest.raises(ExplorerDataRefusal, match="not a file this builder writes"):
        write_explorer_data(files, out)
    assert other.read_text() == "keep me"  # nothing was deleted
    assert (out / "index.json").exists()


def test_the_writer_refuses_a_file_outside_the_layout_or_without_a_newline(tmp_path: Path) -> None:
    out = tmp_path / "explorer-data"
    with pytest.raises(ExplorerDataRefusal, match="not in the expected layout"):
        write_explorer_data({"../evil.json": "{}\n"}, out)
    with pytest.raises(ExplorerDataRefusal, match="not in the expected layout"):
        write_explorer_data({"memos/a.json": "{}\n"}, out)
    with pytest.raises(ExplorerDataRefusal, match="does not end in a newline"):
        write_explorer_data({"index.json": "{}"}, out)
    assert not out.exists()


def test_the_writer_refuses_when_a_temporary_is_left_over(tmp_path: Path) -> None:
    out = tmp_path / "explorer-data"
    (tmp_path / ".explorer-data.new").mkdir()
    with pytest.raises(ExplorerDataRefusal, match="left over"):
        write_explorer_data(_built(tmp_path), out)


def test_the_writer_refuses_a_symbolic_link_in_the_directory(tmp_path: Path) -> None:
    files = _built(tmp_path)
    out = tmp_path / "explorer-data"
    write_explorer_data(files, out)
    (out / "index-link.json").symlink_to(out / "index.json")
    with pytest.raises(ExplorerDataRefusal, match="symbolic link"):
        write_explorer_data(files, out)


# --- the command --------------------------------------------------------------------------------------------


def test_the_command_writes_then_reports_unchanged(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_tree(tmp_path)
    out = tmp_path / "web" / "explorer-data"
    argv = ["site", "explorer", "--results", str(root), "--out", str(out)]
    assert main(argv) == CLEAN_EXIT
    first = capsys.readouterr().out
    assert first.count("wrote ") == 1 + 1 + 8 + 1 + 4 and "unchanged" not in first
    assert "index.json" in first and "bytes" in first
    assert main(argv) == CLEAN_EXIT
    second = capsys.readouterr().out
    assert "unchanged" in second and "wrote " not in second


def test_the_command_refuses_with_the_reason(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_tree(tmp_path)
    _edit(_grid_path(root), lambda d: d.__setitem__("results_version", 1))
    argv = ["site", "explorer", "--results", str(root), "--out", str(tmp_path / "explorer-data")]
    assert main(argv) == REFUSED_EXIT
    err = capsys.readouterr().err
    assert err.startswith("refused: ") and "results_version" in err
    assert not (tmp_path / "explorer-data").exists()


# --- the real data: the committed output is reproduced ----------------------------------------------------


@pytest.fixture(scope="module")
def real() -> dict[str, str]:
    return build_explorer_data(REAL_RESULTS)


def test_the_committed_explorer_data_is_reproduced_byte_for_byte(real: dict[str, str]) -> None:
    """Phase 6 DoD 7 (IMPLEMENTATION doc section 15, row 7). If this fails, run `uv run hc site explorer`
    and read the diff: the results files or the builder changed."""
    on_disk = {
        p.relative_to(REAL_OUT).as_posix(): p.read_bytes()
        for p in REAL_OUT.rglob("*")
        if p.is_file()
    }
    assert set(on_disk) == set(real), "web/explorer-data/ holds a file the builder does not write"
    for path, text in real.items():
        assert on_disk[path] == text.encode("utf-8"), path
    assert explorer_data_matches(real, REAL_OUT)


def test_a_second_build_of_the_real_files_is_byte_identical(real: dict[str, str]) -> None:
    assert build_explorer_data(REAL_RESULTS) == real


def test_no_real_output_file_is_over_the_large_file_limit(real: dict[str, str]) -> None:
    sizes = {path: len(text.encode("utf-8")) for path, text in real.items()}
    assert max(sizes.values()) < 1024 * 1024


def test_the_real_output_holds_no_memo_and_no_account_marker(real: dict[str, str]) -> None:
    assert not any("memo" in path for path in real)
    for text in real.values():
        assert "arn:" not in text and "horizon-compact-results-" not in text


def test_the_sources_name_every_input_with_its_real_sha256(real: dict[str, str]) -> None:
    for source in _index(real)["sources"]:
        path = REPO / source["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"], source["path"]
    paths = {s["path"] for s in _index(real)["sources"]}
    assert (
        len(paths) == 3 + 1 + 1 + 10
    )  # three results files, cases.json, objectives.toml, ten cases


def _same(out: Any, src: Any, where: str, counter: list[int]) -> None:
    """The output value equals the source value, leaf by leaf; the only change allowed is a big integer
    written as its decimal string."""
    if isinstance(src, dict):
        assert isinstance(out, dict) and list(out) == list(src), where
        for key in src:
            _same(out[key], src[key], f"{where}/{key}", counter)
    elif isinstance(src, list):
        assert isinstance(out, list) and len(out) == len(src), where
        for i, (o, s) in enumerate(zip(out, src, strict=True)):
            _same(o, s, f"{where}/{i}", counter)
    elif isinstance(src, int) and not isinstance(src, bool) and abs(src) > MAX_SAFE_INTEGER:
        assert out == str(src), where
        counter[0] += 1
    else:
        assert type(out) is type(src) and out == src, where
        counter[0] += 1


def _source(path: str) -> Obj:
    result: Obj = json.loads((REAL_RESULTS / path).read_text(encoding="utf-8"))
    return result


def test_every_leaf_in_the_grid_and_thinking_files_is_the_source_value(
    real: dict[str, str],
) -> None:
    counter = [0]
    for path, text in real.items():
        folder, _, rest = path.partition("/")
        if folder not in ("grid", "thinking"):
            continue
        model, _, name = rest.partition("/")
        sid = name.removesuffix(".json")
        source_file = next(
            (REAL_RESULTS / "prereg-v1" / model).glob(
                f"{folder if folder == 'thinking' else 'grid'}-*.json"
            )
        )
        source = json.loads(source_file.read_text(encoding="utf-8"))
        scenario = next(s for s in source["scenarios"] if s["scenario_id"] == sid)
        out = json.loads(text)
        assert out.pop("model_key") == model and out.pop("sweep_id") == source["sweep_id"]
        _same(out, scenario, path, counter)
    assert counter[0] > 20_000  # the walk covered the per-run rows, not a sample


def test_every_leaf_in_the_case_files_is_the_source_value_but_the_two_added_notes(
    real: dict[str, str],
) -> None:
    counter = [0]
    seen = 0
    for path, text in real.items():
        if not path.startswith("cases/") or path == "cases/index.json":
            continue
        out = json.loads(text)
        for reading in out["readings"]:
            assert isinstance(reading.pop("all_distances_equal"), bool)
            assert isinstance(reading.pop("one_observable_line"), bool)
        _same(out, _source(path), path, counter)
        seen += 1
    assert seen == 10
    assert counter[0] > 500


def test_the_big_seeds_are_strings_and_nothing_else_in_the_case_files_is_(
    real: dict[str, str],
) -> None:
    for path, text in real.items():
        if path.startswith("cases/") and path != "cases/index.json":
            assert '"seed":"' in text, path

            def no_big_number(value: Any) -> None:
                if isinstance(value, dict):
                    for v in value.values():
                        no_big_number(v)
                elif isinstance(value, list):
                    for v in value:
                        no_big_number(v)
                elif isinstance(value, int) and not isinstance(value, bool):
                    assert abs(value) <= MAX_SAFE_INTEGER

            no_big_number(json.loads(text))


def test_every_leaf_in_the_verdicts_and_the_entries_is_the_source_value(
    real: dict[str, str],
) -> None:
    index = _index(real)
    counter = [0]
    for block in index["verdicts"]:
        source_file = next((REAL_RESULTS / "prereg-v1" / block["model_key"]).glob("grid-*.json"))
        source = json.loads(source_file.read_text(encoding="utf-8"))
        assert block["sweep_id"] == source["sweep_id"]
        scenario = next(s for s in source["scenarios"] if s["scenario_id"] == block["scenario_id"])
        assert len(block["comparisons"]) == len(scenario["comparisons"])
        for out, src in zip(block["comparisons"], scenario["comparisons"], strict=True):
            _same(out, {k: src[k] for k in explorer._VERDICT_FIELDS}, "verdicts", counter)
    assert counter[0] > 600
    for entry in index["against_thesis"]["entries"]:
        source = _source(
            f"prereg-v1/{entry['model_key']}/grid-{entry['model_key']}-{entry['sweep_id'].rsplit('-', 1)[1]}.json"
        )
        scenario = next(s for s in source["scenarios"] if s["scenario_id"] == entry["scenario_id"])
        comparison = next(
            c
            for c in scenario["comparisons"]
            if (c["first"], c["second"], c["role"]) == (entry["first"], entry["second"], "primary")
        )
        _same(
            {k: entry[k] for k in explorer._ENTRY_FIELDS},
            {k: comparison[k] for k in explorer._ENTRY_FIELDS},
            "entry",
            counter,
        )


def test_every_leaf_in_the_index_blocks_and_the_cases_index_is_the_source_value(
    real: dict[str, str],
) -> None:
    """The rest of section 5's "every number at its source path": the models, scenarios and objectives blocks
    of index.json, and cases/index.json against cases.json (Opus review, 2026-11-09)."""
    index = _index(real)
    counter = [0]
    grids = {
        p.parent.name: json.loads(p.read_text(encoding="utf-8"))
        for p in (REAL_RESULTS / "prereg-v1").glob("*/grid-*.json")
    }
    assert [m["model_key"] for m in index["models"]] == sorted(grids)
    for model in index["models"]:
        source = grids[model["model_key"]]
        _same(model, {k: source[k] for k in model}, "models", counter)
    for scenario in index["scenarios"]:
        for source in grids.values():
            src = next(
                s for s in source["scenarios"] if s["scenario_id"] == scenario["scenario_id"]
            )
            _same(scenario, {k: src[k] for k in scenario}, "scenarios", counter)
    objectives = tomllib.loads(
        (REPO / "experiment" / "company" / "objectives.toml").read_text(encoding="utf-8")
    )["objectives"]
    assert [o["id"] for o in index["objectives"]] == [o["id"] for o in objectives]
    for out, src in zip(index["objectives"], objectives, strict=True):
        assert out == {"id": src["id"], "who": src.get("who"), "when": src.get("when")}
    cases = _source("cases/cases.json")
    document = json.loads(real["cases/index.json"])
    for key in ("shortfall", "provenance"):
        _same(document[key], cases[key], f"cases/index.json/{key}", counter)
    assert [c["label"] for c in document["cases"]] == [c["label"] for c in cases["cases"]]
    for out, src in zip(document["cases"], cases["cases"], strict=True):
        _same(out, {k: src[k] for k in out}, f"cases/index.json/{src['label']}", counter)
    assert counter[0] > 50


def test_the_real_entries_follow_the_rule_and_nothing_else(real: dict[str, str]) -> None:
    """Recomputes the list from the source files by a separate, plainer reading of section 19, and compares.
    It asserts the rule's mechanics, not what the list contains."""
    expected: list[tuple[str, str, str, str, str]] = []
    for model in sorted(p.name for p in (REAL_RESULTS / "prereg-v1").iterdir()):
        source = _source(
            next((REAL_RESULTS / "prereg-v1" / model).glob("grid-*.json"))
            .relative_to(REAL_RESULTS)
            .as_posix()
        )
        for scenario in source["scenarios"]:
            sid = scenario["scenario_id"]
            by_pair = {
                (c["first"], c["second"]): c
                for c in scenario["comparisons"]
                if c["role"] == "primary"
            }
            for pair in PRIMARY_PAIRS:
                c = by_pair[pair]
                if c["final_verdict"] == "no_split":
                    expected.append((model, sid, *pair, "no_split"))
                elif c["final_verdict"] == "split":
                    positive = c["difference"] > 0
                    if positive == (SECOND_CUT_MORE_SIGN[sid] > 0):
                        expected.append((model, sid, *pair, "reversed_split"))
    actual = [(*_coords(e), e["clause"]) for e in _entries(real)]
    assert actual == expected


def test_the_matcher_facts_measured_on_2026_10_31_hold_in_the_real_output(
    real: dict[str, str],
) -> None:
    labels = [c["label"] for c in json.loads(real["cases/index.json"])["cases"]]
    assert len(labels) == 5
    for label in labels:
        haiku = json.loads(real[f"cases/{label}/haiku-5-5.json"])
        primary = next(r for r in haiku["readings"] if r["reading"] == "primary")
        assert primary["all_distances_equal"] is True, label
    for model in ("haiku-5-5", "gpt-oss-openrouter"):
        closure_19 = json.loads(real[f"cases/closure-19/{model}.json"])
        u1 = next(r for r in closure_19["readings"] if r["reading"] == "u1")
        assert u1["one_observable_line"] is True
        assert len(u1["observable_lines"]) == 1


def test_every_real_case_carries_its_exploratory_label(real: dict[str, str]) -> None:
    document = json.loads(real["cases/index.json"])
    for case in document["cases"]:
        assert case["exploratory"] is True and case["exploratory_label"]
    for path, text in real.items():
        if path.startswith("cases/") and path != "cases/index.json":
            body = json.loads(text)
            assert body["exploratory"] is True and body["exploratory_label"], path


def test_the_real_output_is_not_changed_by_deep_copying_the_inputs(real: dict[str, str]) -> None:
    """The builder must not mutate what it reads: a build after a build still matches (a cheap guard on the
    annotation step, which copies each reading before adding to it)."""
    snapshot = copy.deepcopy(real)
    build_explorer_data(REAL_RESULTS)
    assert snapshot == real
