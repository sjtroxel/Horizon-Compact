"""``hc case scenario render`` and ``check`` (search half, Stage C step 8b). Fictional canaries only.

Every case here is built from a real shape's own template (``experiment/company/scenarios/sN.source.toml``)
and rows taken from the fictional figures, so a test exercises the shape as it will be used. A case is a
temporary
appendix: ``build.json``, ``sources.json``, a selection log in the ``search`` folder and the rows file.
"""

from __future__ import annotations

import json
import re
import shutil
import tomllib
from datetime import date
from decimal import Decimal
from pathlib import Path
from string import Formatter
from typing import Any

import pytest

from horizon_compact.casebuild.appendix import AppendixError, CaseAppendix
from horizon_compact.casebuild.scale import scale_dollars
from horizon_compact.casebuild.scenario import (
    CRITERION_4,
    CUTOFF,
    FIRST,
    ROWS,
    S3_FORM_PATH,
    ScenarioRefused,
    _PayResolved,
    check_scenario,
    drop_sentences,
    parse_s3_form,
    render_case_scenario,
    render_in_memory,
    without_sentences,
)
from horizon_compact.casebuild.search import Row, SelectionLog, write_log_version
from horizon_compact.cli import CHECK_FAILED_EXIT, CLEAN_EXIT, REFUSED_EXIT, main
from horizon_compact.dossier.check import default_repo_root
from horizon_compact.experiment import Scenario
from horizon_compact.scenarios.render import load_scenario_figures, parse_source

ROOT = default_repo_root()
LABEL = "closure-1"
ACCESSION = "0000000000-26-000001"
CUTOFF_DATE = date(2026, 6, 9)
DISCLOSED = date(2026, 6, 10)
FACTOR = 1.25
TEXTS = ("situation", "menu_heading", "instruction", "role", "currency_note", "options_heading")
# Each shape's total: the figure the first-disclosure document gives (a derived row in the fictional figures,
# so the case supplies it), with the unscaled value and how it scales.
TOTALS: dict[str, tuple[str, str, float]] = {
    "S1": ("s1_roles", "heads", 600),
    "S2": ("s2_shortfall", "dollars", 61_000_000),
    "S3": ("hc_p6", "heads", 1200),
    "S4": ("s4_annual", "dollars", 48_000_000),
}

FIC = load_scenario_figures(ROOT)
FORM = parse_s3_form((ROOT / S3_FORM_PATH).read_bytes())


# --- a case on disk --------------------------------------------------------------------------------------


def _toml_number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else repr(float(value))


def rows_toml(rows: dict[str, dict[str, Any]]) -> str:
    out = []
    for key, row in rows.items():
        out.append(f"[rows.{key}]\n")
        for name, value in row.items():
            if isinstance(value, bool):
                out.append(f"{name} = {'true' if value else 'false'}\n")
            elif isinstance(value, str):
                out.append(f"{name} = {json.dumps(value)}\n")
            else:
                out.append(f"{name} = {_toml_number(value)}\n")
        out.append("\n")
    return "".join(out)


def _used_ids(shape: str, template: Path) -> set[str]:
    source = parse_source(template)
    texts = [source.role, source.currency_note, source.situation, source.menu_heading]
    texts += [source.options_heading, source.instruction]
    texts += [lever.detail for lever in source.levers] + [lever.note for lever in source.levers]
    if source.choice:
        texts += [o.text for o in source.choice.options]
    ids = {name for text in texts for _l, name, _s, _c in Formatter().parse(text) if name}
    ids |= {lever.cap for lever in source.levers if lever.cap}
    ids.add(source.total)
    for rule in source.rules:
        fields = rule.model_dump()
        ids |= {fields[n] for n in ("base", "divisor", "fraction", "amount") if n in fields}
    return ids


def full_rows(shape: str, template: Path | None = None) -> dict[str, dict[str, Any]]:
    """Rows for every figure the shape's text uses: the fictional base values, dollars scaled and the rest
    not; the total from the first-disclosure document; every derived figure left to the formulas."""
    template = template or ROOT / f"experiment/company/scenarios/{shape.lower()}.source.toml"
    total_id, total_scale, total_value = TOTALS[shape]
    wanted: set[str] = set()
    pending = list(_used_ids(shape, template))
    while pending:
        key = pending.pop()
        if key in wanted or key == total_id:
            continue
        wanted.add(key)
        pending.extend(FIC.references.get(key, ()))
    rows: dict[str, dict[str, Any]] = {}
    for key in sorted(wanted):
        fic = FIC.rows[key]
        if fic.formula is not None or fic.unit == "label":
            continue
        resolved = FIC.resolved[key].value
        assert not isinstance(resolved, str)
        rows[key] = {
            "value": float(fic.value if fic.value is not None else resolved),
            "unit": fic.unit,
            "scale": "dollars" if fic.unit in ("usd", "usd_m") else "none",
            "source": "pre_cutoff",
            "accession": ACCESSION,
            "locator": "canary locator",
        }
    # a per-head pay figure is a ratio of two scaled quantities, so a case states it unscaled (CaseRow's rule)
    for key in rows:
        if key.startswith("oews_wage_"):
            rows[key].update(scale="none", per="employee")
    rows[total_id] = {
        "value": total_value,
        "unit": FIC.rows[total_id].unit,
        "scale": total_scale,
        "source": "first_disclosure",
        "locator": "canary locator",
    }
    return rows


def make_case(
    tmp_path: Path,
    shape: str = "S3",
    rows: dict[str, dict[str, Any]] | None = None,
    *,
    factor: float = FACTOR,
    filed: str = "2026-05-01",
    disclosed: date = DISCLOSED,
) -> CaseAppendix:
    appendix = tmp_path / "appendix"
    case = CaseAppendix(appendix, LABEL)
    case.directory.mkdir(parents=True)
    case.build_path.write_text(
        json.dumps({"shape": shape, "factor": factor, "cutoff": CUTOFF_DATE.isoformat()}),
        encoding="utf-8",
    )
    case.sources_path.write_text(
        json.dumps(
            {
                "cik": "0000000000",
                "cutoff": CUTOFF_DATE.isoformat(),
                "sources": [
                    {
                        "role": "annual",
                        "form": "10-K",
                        "accession": ACCESSION,
                        "filed": filed,
                        "accepted": f"{filed}T16:30:00-04:00",
                        "url": "https://example.invalid/x",
                        "sha256": "0" * 64,
                    },
                    {"role": "company-facts", "form": None, "accession": None, "filed": None},
                ],
            }
        ),
        encoding="utf-8",
    )
    search = CaseAppendix(appendix, "search")
    log = SelectionLog({LABEL: Row(LABEL, "closure", "window", "acc")})
    log.record(LABEL, "first_disclosure", "pass", "canary reason", disclosed=disclosed)
    search.directory.mkdir(parents=True)
    write_log_version(search, log)
    chosen = full_rows(shape) if rows is None else rows
    case.scenario_figures_path.write_text(rows_toml(chosen), encoding="utf-8")
    return case


def scenario_data(case: CaseAppendix) -> dict[str, Any]:
    return tomllib.loads(case.scenario_path.read_text(encoding="utf-8"))


def render_record(case: CaseAppendix) -> dict[str, Any]:
    record: dict[str, Any] = json.loads(case.scenario_render_path.read_text(encoding="utf-8"))
    return record


def without(rows: dict[str, dict[str, Any]], *keys: str) -> dict[str, dict[str, Any]]:
    return {k: v for k, v in rows.items() if k not in keys}


@pytest.fixture(autouse=True)
def _appendix_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HC_APPENDIX_DIR", str(tmp_path / "appendix"))


# --- a fully sourced case, on each real shape ------------------------------------------------------------


@pytest.mark.parametrize("shape", ["S1", "S2", "S3", "S4"])
def test_a_fully_sourced_case_renders_whole_on_every_shape(tmp_path: Path, shape: str) -> None:
    case = make_case(tmp_path, shape)
    done = render_case_scenario(case, ROOT)
    # S3's sentence on how corporate costs are shared holds a fictional fact (a label), so it always goes
    dropped = {"situation": 1} if shape == "S3" else {}
    assert (done.dropped, done.rules_omitted, done.caps_to_total) == (len(dropped), 0, 0)
    data = scenario_data(case)
    scenario = Scenario.model_validate(data)
    total_id, total_scale, total_value = TOTALS[shape]
    expected = (
        round(total_value * FACTOR / 5) * 5
        if total_scale == "heads"
        else int(scale_dollars(Decimal(str(total_value)), FACTOR))
    )
    assert scenario.total == expected
    record = render_record(case)
    assert record["shape"] == shape and record["factor"] == FACTOR
    assert record["sentences_dropped"] == dropped and record["equal_treatment_applied"] is False
    assert total_id in record["rows_used"]
    assert check_scenario(case, ROOT) == []


@pytest.mark.parametrize("shape", ["S1", "S2", "S3", "S4"])
def test_the_case_scenario_keeps_the_shapes_words_and_structure(tmp_path: Path, shape: str) -> None:
    case = make_case(tmp_path, shape)
    render_case_scenario(case, ROOT)
    template = parse_source(ROOT / f"experiment/company/scenarios/{shape.lower()}.source.toml")
    data = scenario_data(case)
    assert data["role"] == template.role
    assert data["rule"] == template.rule and data["unit"] == template.unit
    assert [lever["key"] for lever in data["levers"]] == [lever.key for lever in template.levers]
    assert [lever["kind"] for lever in data["levers"]] == [lever.kind for lever in template.levers]
    assert len(data.get("rules", [])) == len(template.rules)
    text = case.scenario_path.read_text(encoding="utf-8")
    assert text.startswith("# RENDERED by `hc case scenario render`")
    assert "hc scenarios" not in text


def test_derived_figures_follow_the_fictional_formulas_over_the_cases_rows(tmp_path: Path) -> None:
    case = make_case(tmp_path, "S3")
    render_case_scenario(case, ROOT)
    record = render_record(case)
    assert "s3_movers" in record["rows_derived"] and "s3_caps_sum" in record["rows_derived"]
    scenario = Scenario.model_validate(scenario_data(case))
    caps = {lever.key: lever.cap for lever in scenario.levers}
    assert caps["eliminated"] == scenario.total
    assert 0 < caps["moved_other_plants"] < scenario.total


def test_dollars_scale_to_three_significant_figures_and_heads_to_the_nearest_five(
    tmp_path: Path,
) -> None:
    rows = full_rows("S3")
    rows["hc_p6"]["value"] = 487  # x 1.25 = 608.75 -> 610
    case = make_case(tmp_path, "S3", rows)
    render_case_scenario(case, ROOT)
    assert scenario_data(case)["total"] == 610
    assert "$" in scenario_data(case)["scenario"]


def test_a_dollar_ratio_that_is_not_scaled_needs_a_per_and_is_left_alone(tmp_path: Path) -> None:
    rows = full_rows("S1")
    key = "oews_wage_office"
    rows[key].update(scale="none", per="employee")
    case = make_case(tmp_path, "S1", rows)
    inputs_rows = rows[key]["value"]
    render_case_scenario(case, ROOT)
    assert f"${int(inputs_rows):,}" in scenario_data(case)["levers"][0]["detail"]
    rows[key].pop("per")
    with pytest.raises(ScenarioRefused, match=r"needs per"):
        render_in_memory(make_case(tmp_path / "b", "S1", rows), ROOT)


# --- a sparse case: sentences dropped whole --------------------------------------------------------------


def test_a_sparse_case_drops_whole_sentences_and_keeps_the_rest(tmp_path: Path) -> None:
    case = make_case(tmp_path, "S3", without(full_rows("S3"), "credit_facility"))
    done = render_case_scenario(case, ROOT)
    situation = scenario_data(case)["scenario"]
    assert "available liquidity" not in situation
    assert situation.startswith("Plant 6 has ")
    assert "of those offered to accept" in situation
    assert done.dropped >= 2
    assert render_record(case)["sentences_dropped"]["situation"] >= 1
    assert render_record(case)["equal_treatment_applied"] is False
    assert check_scenario(case, ROOT) == []


def test_a_dropped_sentence_in_a_situation_does_not_touch_the_options(tmp_path: Path) -> None:
    full = make_case(tmp_path / "full", "S3")
    render_case_scenario(full, ROOT)
    sparse = make_case(tmp_path / "sparse", "S3", without(full_rows("S3"), "credit_facility"))
    render_case_scenario(sparse, ROOT)
    assert scenario_data(sparse)["choice"] == scenario_data(full)["choice"]


def test_the_total_still_stands_when_every_other_figure_is_gone(tmp_path: Path) -> None:
    only_total = {k: v for k, v in full_rows("S1").items() if k == "s1_roles"}
    case = make_case(tmp_path, "S1", only_total)
    render_case_scenario(case, ROOT)
    data = scenario_data(case)
    assert "{" not in case.scenario_path.read_text(encoding="utf-8").replace("{}", "")
    assert Scenario.model_validate(data).total == 750
    assert str(data["total"]) and "750" in data["menu_heading"]


def test_equal_treatment_drops_every_sentence_with_a_figure_from_every_lever_detail(
    tmp_path: Path,
) -> None:
    """S1 has no choice: its levers' details are its options. One missing figure in one detail empties the
    figures from all three, so no path is described with more than another."""
    case = make_case(tmp_path, "S1", without(full_rows("S1"), "oews_wage_office"))
    render_case_scenario(case, ROOT)
    record = render_record(case)
    assert record["equal_treatment_applied"] is True
    details = [lever.get("detail", "") for lever in scenario_data(case)["levers"]]
    assert details == ["", "", ""] or all("$" not in d for d in details)
    dropped = record["sentences_dropped"]
    assert {f"lever {k} detail" for k in ("eliminate", "move_plant_pay", "move_keep_pay")} <= set(
        dropped
    )
    assert check_scenario(case, ROOT) == []


# --- caps ------------------------------------------------------------------------------------------------


def test_a_cap_with_no_figure_equals_the_total_and_is_recorded(tmp_path: Path) -> None:
    rows = full_rows("S2")
    rows["s2_cap_price"] = {"equals_total": True}
    case = make_case(tmp_path, "S2", rows)
    render_case_scenario(case, ROOT)
    scenario = Scenario.model_validate(scenario_data(case))
    caps = {lever.key: lever.cap for lever in scenario.levers}
    assert caps["raise_prices"] == scenario.total
    assert {"row": "s2_cap_price", "reason": "equals_total"} in render_record(case)[
        "caps_set_to_total"
    ]


def test_a_cap_under_100_is_unstated_and_equals_the_total(tmp_path: Path) -> None:
    rows = full_rows("S3")
    rows["s3_movers"] = {
        "value": 60,  # x 1.25 = 75, under 100
        "unit": "count",
        "scale": "heads",
        "source": "pre_cutoff",
        "accession": ACCESSION,
        "locator": "canary locator",
    }
    case = make_case(tmp_path, "S3", rows)
    render_case_scenario(case, ROOT)
    scenario = Scenario.model_validate(scenario_data(case))
    caps = {lever.key: lever.cap for lever in scenario.levers}
    assert caps["moved_other_plants"] == scenario.total
    assert {"row": "s3_movers", "reason": "under_100"} in render_record(case)["caps_set_to_total"]
    text = case.scenario_path.read_text(encoding="utf-8")
    assert "fewer than 100" not in text
    # the cap is the total, but no text states the total as the number who may move
    assert "of those offered to accept" not in scenario_data(case)["scenario"]


def test_a_cap_that_derives_under_100_is_also_set_to_the_total(tmp_path: Path) -> None:
    rows = full_rows("S3")
    rows["s3_accept_share"]["value"] = 0.05  # 1,500 x 0.05 = 75 people
    case = make_case(tmp_path, "S3", rows)
    render_case_scenario(case, ROOT)
    scenario = Scenario.model_validate(scenario_data(case))
    assert {lever.key: lever.cap for lever in scenario.levers}[
        "moved_other_plants"
    ] == scenario.total
    assert {"row": "s3_movers", "reason": "under_100"} in render_record(case)["caps_set_to_total"]


def test_a_cap_that_is_neither_a_row_nor_derivable_is_refused(tmp_path: Path) -> None:
    case = make_case(tmp_path, "S2", without(full_rows("S2"), "ind_rnd_fy0"))
    with pytest.raises(ScenarioRefused, match=r"cap .rnd_fy0. is neither a case row nor derivable"):
        render_in_memory(case, ROOT)


def test_a_heads_figure_under_100_reads_fewer_than_100(tmp_path: Path) -> None:
    rows = full_rows("S1")
    rows["s1_roles_office"] = {
        "value": 60,
        "unit": "count",
        "scale": "heads",
        "source": "pre_cutoff",
        "accession": ACCESSION,
        "locator": "canary locator",
    }
    case = make_case(tmp_path, "S1", rows)
    render_case_scenario(case, ROOT)
    situation = scenario_data(case)["scenario"]
    assert "fewer than 100 in office and administrative support" in situation


def test_a_cap_set_to_the_total_is_never_printed_as_a_figure(tmp_path: Path) -> None:
    rows = full_rows("S2")
    rows["wage_cut_cap"] = {"equals_total": True}
    case = make_case(tmp_path, "S2", rows)
    render_case_scenario(case, ROOT)
    scenario = Scenario.model_validate(scenario_data(case))
    assert {lever.key: lever.cap for lever in scenario.levers}["cut_wages_hours"] == scenario.total
    assert "its maximum below" not in scenario_data(case)["scenario"]
    assert "The maximums add up to" in scenario_data(case)["menu_heading"]
    assert check_scenario(case, ROOT) == []


def test_a_figure_derived_from_a_cap_set_to_the_total_is_not_printed(tmp_path: Path) -> None:
    rows = full_rows("S3")
    rows["s3_retool_positions"] = {"equals_total": True}
    case = make_case(tmp_path, "S3", rows)
    # "needs <total> of its <total> positions" would be a figure no source gives; its sentence drops, and
    # equal treatment gives every option the form's figure-free sentence
    render_case_scenario(case, ROOT)
    options = {o["key"]: o["text"] for o in scenario_data(case)["choice"]["options"]}
    assert options == FORM.options
    assert render_record(case)["equal_treatment_applied"] is True


def test_a_headcount_is_never_stated_unscaled(tmp_path: Path) -> None:
    rows = full_rows("S3")
    rows["hc_p6"]["scale"] = "none"
    with pytest.raises(ScenarioRefused, match=r"row 'hc_p6' is a headcount: its scale is heads"):
        render_in_memory(make_case(tmp_path, "S3", rows), ROOT)


def test_a_people_total_must_be_a_headcount(tmp_path: Path) -> None:
    rows = full_rows("S1")
    rows.pop("s1_roles")
    for key in ("hc_office", "hc_business"):
        rows[key] = {
            "value": 300,
            "unit": "count",
            "scale": "none",
            "source": "pre_cutoff",
            "accession": ACCESSION,
            "locator": "canary locator",
        }
    with pytest.raises(ScenarioRefused, match=r"is a headcount"):
        render_in_memory(make_case(tmp_path, "S1", rows), ROOT)


def test_a_label_that_is_a_fact_never_reaches_a_case(tmp_path: Path) -> None:
    case = make_case(tmp_path, "S3")
    render_case_scenario(case, ROOT)
    text = case.scenario_path.read_text(encoding="utf-8")
    assert "in proportion to revenue" not in text
    assert "Plant 6" in text  # a plant number is a name, and stays


# --- the extra rules -------------------------------------------------------------------------------------


def test_a_rule_whose_numbers_have_no_rows_is_omitted_with_its_sentences(tmp_path: Path) -> None:
    rows = without(full_rows("S2"), "max_wage_cut", "s2_cost_per_payroll_dollar", "wage_cut_cap")
    rows["wage_cut_cap"] = {"equals_total": True}
    case = make_case(tmp_path, "S2", rows)
    render_case_scenario(case, ROOT)
    record = render_record(case)
    assert record["rules_omitted"] == ["joint_cap:cut_wages_hours"]
    assert "rules" not in scenario_data(case)
    assert "lowers it by" not in scenario_data(case)["scenario"]
    assert record["sentences_dropped"]["situation"] >= 1
    assert check_scenario(case, ROOT) == []


# --- refusals --------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("shape", "value", "factor"),
    [("S1", 95, 1.0), ("S1", 130, 0.7)],
)
def test_a_total_under_100_after_scaling_fails_criterion_4(
    tmp_path: Path, shape: str, value: int, factor: float
) -> None:
    rows = full_rows(shape)
    rows[TOTALS[shape][0]]["value"] = value
    case = make_case(tmp_path, shape, rows, factor=factor)
    with pytest.raises(ScenarioRefused) as caught:
        render_case_scenario(case, ROOT)
    assert caught.value.criterion == CRITERION_4 and "under 100" in caught.value.message
    assert not case.scenario_path.exists()


def test_a_case_with_no_total_fails_criterion_4(tmp_path: Path) -> None:
    case = make_case(tmp_path, "S3", without(full_rows("S3"), "hc_p6", "share_p2"))
    with pytest.raises(ScenarioRefused) as caught:
        render_in_memory(case, ROOT)
    assert caught.value.criterion == CRITERION_4 and "hc_p6" in caught.value.message


def _template_with(tmp_path: Path, field: str, text: str) -> Path:
    """A copy of the company folder whose S1 template has ``field`` replaced; the repo root over it."""
    root = tmp_path / "repo"
    shutil.copytree(ROOT / "experiment/company", root / "experiment/company")
    path = root / "experiment/company/scenarios/s1.source.toml"
    source = path.read_text(encoding="utf-8")
    replaced, count = re.subn(
        rf'\n{field} = """.*?"""\n',
        lambda _m: f'\n{field} = """\n{text}\n"""\n',
        source,
        flags=re.S,
    )
    assert count == 1
    path.write_text(replaced, encoding="utf-8")
    return root


@pytest.mark.parametrize("field", ["situation", "menu_heading", "instruction"])
def test_a_text_left_empty_is_a_refusal(tmp_path: Path, field: str) -> None:
    root = _template_with(tmp_path, field, "Only {s1_severance_all} matters.")
    case = make_case(tmp_path, "S1", {"s1_roles": full_rows("S1")["s1_roles"]})
    with pytest.raises(ScenarioRefused, match=f"{field} is empty"):
        render_in_memory(case, root)


def test_an_empty_role_is_a_refusal(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    shutil.copytree(ROOT / "experiment/company", root / "experiment/company")
    path = root / "experiment/company/scenarios/s1.source.toml"
    text = path.read_text(encoding="utf-8").replace(
        'role = "You are the chief executive of the Company described below."',
        'role = "You are the chief executive of {s1_severance_all}."',
    )
    path.write_text(text, encoding="utf-8")
    case = make_case(tmp_path, "S1", {"s1_roles": full_rows("S1")["s1_roles"]})
    with pytest.raises(ScenarioRefused, match="role is empty"):
        render_in_memory(case, root)


def test_an_unknown_row_is_refused(tmp_path: Path) -> None:
    rows = full_rows("S3")
    rows["no_such_row"] = dict(rows["hc_p6"])
    with pytest.raises(ScenarioRefused, match="not a row of the shape's figures"):
        render_in_memory(make_case(tmp_path, "S3", rows), ROOT)


def test_a_label_row_is_refused(tmp_path: Path) -> None:
    rows = full_rows("S3")
    rows["plant_6_no"] = {
        "value": 6, "unit": "label", "scale": "none", "source": "pre_cutoff",
        "accession": ACCESSION, "locator": "x",
    }  # fmt: skip
    with pytest.raises(ScenarioRefused, match="label"):
        render_in_memory(make_case(tmp_path, "S3", rows), ROOT)


def test_a_unit_other_than_the_fictional_rows_is_refused(tmp_path: Path) -> None:
    rows = full_rows("S3")
    rows["s3_retool_capex"]["unit"] = "count"
    rows["s3_retool_capex"]["scale"] = "none"
    with pytest.raises(ScenarioRefused, match="unit other than the fictional row's"):
        render_in_memory(make_case(tmp_path, "S3", rows), ROOT)


def test_equals_total_on_a_row_that_is_no_cap_is_refused(tmp_path: Path) -> None:
    rows = full_rows("S3")
    rows["s3_retool_capex"] = {"equals_total": True}
    with pytest.raises(ScenarioRefused, match="no lever's cap"):
        render_in_memory(make_case(tmp_path, "S3", rows), ROOT)


@pytest.mark.parametrize(
    ("edit", "message"),
    [
        ({"scale": "heads"}, "scale heads is for a count row"),
        ({"scale": "dollars", "unit": "pct"}, "scale dollars is for a usd or usd_m row"),
        ({"accession": None}, "needs an accession|accession"),
        ({"locator": ""}, "needs locator"),
        ({"source": "first_disclosure", "accession": ACCESSION}, "no accession"),
        ({"per": "head"}, "per belongs on an unscaled dollar row"),
        ({"unknown": 1}, "Extra inputs are not permitted"),
    ],
)
def test_a_malformed_row_is_refused(tmp_path: Path, edit: dict[str, Any], message: str) -> None:
    rows = full_rows("S3")
    row = dict(rows["s3_retool_capex"])
    row.update(edit)
    rows["s3_retool_capex"] = {k: v for k, v in row.items() if v is not None}
    with pytest.raises(ScenarioRefused, match=message):
        render_in_memory(make_case(tmp_path, "S3", rows), ROOT)


def test_a_rows_file_that_is_not_toml_is_refused(tmp_path: Path) -> None:
    case = make_case(tmp_path, "S3")
    case.scenario_figures_path.write_text("this is [not toml", encoding="utf-8")
    with pytest.raises(ScenarioRefused, match="not valid TOML"):
        render_in_memory(case, ROOT)


def test_a_missing_rows_file_is_refused(tmp_path: Path) -> None:
    case = make_case(tmp_path, "S3")
    case.scenario_figures_path.unlink()
    with pytest.raises(ScenarioRefused) as caught:
        render_in_memory(case, ROOT)
    assert caught.value.criterion == ROWS


# --- the sources -----------------------------------------------------------------------------------------


def test_only_the_total_may_be_first_disclosure(tmp_path: Path) -> None:
    rows = full_rows("S3")
    rows["s3_retool_capex"].update(source="first_disclosure")
    rows["s3_retool_capex"].pop("accession")
    with pytest.raises(ScenarioRefused) as caught:
        render_in_memory(make_case(tmp_path, "S3", rows), ROOT)
    assert caught.value.criterion == FIRST and "s3_retool_capex" in caught.value.message


def test_an_accession_not_in_sources_json_is_refused(tmp_path: Path) -> None:
    rows = full_rows("S3")
    rows["s3_retool_capex"]["accession"] = "9999999999-26-999999"
    with pytest.raises(ScenarioRefused) as caught:
        render_in_memory(make_case(tmp_path, "S3", rows), ROOT)
    assert caught.value.criterion == CUTOFF and "not in sources.json" in caught.value.message


@pytest.mark.parametrize("filed", ["2026-06-09", "2026-06-10", "2026-07-01"])
def test_a_source_not_filed_strictly_before_the_cutoff_is_refused(
    tmp_path: Path, filed: str
) -> None:
    case = make_case(tmp_path, "S3", filed=filed)
    with pytest.raises(ScenarioRefused) as caught:
        render_in_memory(case, ROOT)
    assert (
        caught.value.criterion == CUTOFF and "strictly before the cut-off" in caught.value.message
    )


def test_a_cutoff_that_is_not_the_day_before_the_logged_disclosure_is_refused(
    tmp_path: Path,
) -> None:
    case = make_case(tmp_path, "S3", disclosed=date(2026, 7, 4))
    with pytest.raises(ScenarioRefused) as caught:
        render_in_memory(case, ROOT)
    assert caught.value.criterion == FIRST


def test_a_missing_selection_log_is_refused_only_when_a_row_needs_it(tmp_path: Path) -> None:
    rows = full_rows("S3")
    rows["hc_p6"].update(source="pre_cutoff", accession=ACCESSION)
    case = make_case(tmp_path, "S3", rows)
    for path in CaseAppendix(case.root, "search").directory.glob("selection-log-*.json"):
        path.unlink()
    render_in_memory(case, ROOT)  # no first-disclosure row, so the log is not read
    rows["hc_p6"].update(source="first_disclosure")
    rows["hc_p6"].pop("accession")
    case.scenario_figures_path.write_text(rows_toml(rows), encoding="utf-8")
    with pytest.raises(ScenarioRefused, match="selection log cannot be read"):
        render_in_memory(case, ROOT)


# --- the check -------------------------------------------------------------------------------------------


def test_the_check_passes_a_fresh_render_and_fails_a_hand_edit(tmp_path: Path) -> None:
    case = make_case(tmp_path, "S3")
    render_case_scenario(case, ROOT)
    assert check_scenario(case, ROOT) == []
    case.scenario_path.write_bytes(case.scenario_path.read_bytes() + b"# edited\n")
    failures = check_scenario(case, ROOT)
    assert [f.criterion for f in failures] == ["render"]
    assert "scenario.toml differs from a fresh render" in failures[0].message


def test_the_check_fails_an_edited_render_record(tmp_path: Path) -> None:
    case = make_case(tmp_path, "S3")
    render_case_scenario(case, ROOT)
    record = render_record(case)
    record["sentences_dropped"] = {"situation": 1}
    case.scenario_render_path.write_text(json.dumps(record), encoding="utf-8")
    assert "scenario-render.json differs" in check_scenario(case, ROOT)[0].message


def test_the_check_fails_when_the_rows_change_after_the_render(tmp_path: Path) -> None:
    case = make_case(tmp_path, "S3")
    render_case_scenario(case, ROOT)
    rows = full_rows("S3")
    rows["hc_p6"]["value"] = 500
    case.scenario_figures_path.write_text(rows_toml(rows), encoding="utf-8")
    assert check_scenario(case, ROOT)[0].criterion == "render"


def test_the_check_fails_a_case_that_was_never_rendered(tmp_path: Path) -> None:
    failures = check_scenario(make_case(tmp_path, "S3"), ROOT)
    assert {f.criterion for f in failures} == {"render"}
    assert len(failures) == 2


def test_the_check_re_checks_every_source(tmp_path: Path) -> None:
    case = make_case(tmp_path, "S3")
    render_case_scenario(case, ROOT)
    sources = json.loads(case.sources_path.read_text(encoding="utf-8"))
    sources["sources"][0]["filed"] = "2026-06-09"  # the cut-off day itself
    case.sources_path.write_text(json.dumps(sources), encoding="utf-8")
    failures = check_scenario(case, ROOT)
    assert failures and all(f.criterion == CUTOFF for f in failures)


def test_render_is_write_once(tmp_path: Path) -> None:
    case = make_case(tmp_path, "S3")
    render_case_scenario(case, ROOT)
    with pytest.raises(AppendixError, match="write-once"):
        render_case_scenario(case, ROOT)


def test_rendering_twice_from_the_same_inputs_gives_the_same_bytes(tmp_path: Path) -> None:
    first = render_in_memory(make_case(tmp_path / "a", "S4"), ROOT)
    second = render_in_memory(make_case(tmp_path / "b", "S4"), ROOT)
    assert first == second


# --- the commands ----------------------------------------------------------------------------------------


def test_the_commands_render_then_check_and_print_counts_only(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    case = make_case(tmp_path, "S3", without(full_rows("S3"), "credit_facility"))
    assert main(["case", "scenario", "render", LABEL]) == CLEAN_EXIT
    out = capsys.readouterr().out
    assert "scenario.toml and scenario-render.json written" in out and "sentence(s) dropped" in out
    assert "canary" not in out
    assert main(["case", "scenario", "check", LABEL]) == CLEAN_EXIT
    assert "scenario check: ok" in capsys.readouterr().out
    assert case.scenario_path.exists()


def test_the_render_command_refuses_with_the_criterion_and_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rows = full_rows("S3")
    rows["hc_p6"]["value"] = 40
    case = make_case(tmp_path, "S3", rows)
    assert main(["case", "scenario", "render", LABEL]) == REFUSED_EXIT
    assert f"refused: {CRITERION_4}: the total is under 50 as stated" in capsys.readouterr().err
    assert not case.scenario_path.exists()


def test_a_failing_check_prints_failures_by_criterion_and_never_a_name_figure_or_excerpt(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rows = full_rows("S3")
    rows["s3_retool_capex"]["locator"] = "Canary Cages page 7 says 4,212 people"
    rows["s3_retool_capex"]["accession"] = "9999999999-26-999999"
    case = make_case(tmp_path, "S3", rows)
    assert main(["case", "scenario", "check", LABEL]) == CHECK_FAILED_EXIT
    err = capsys.readouterr()
    assert f"{CUTOFF}:" in err.err and "s3_retool_capex" in err.err
    for text in (err.out, err.err):
        assert "Canary" not in text and "4,212" not in text and "9999999999" not in text
    assert case.scenario_path.exists() is False


def test_lock_passes_end_to_end_once_the_check_passes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    import hashlib

    from horizon_compact import cli

    # the independent reads are the reader's tests' business (tests/test_reader.py)
    monkeypatch.setattr(cli, "reads_settled_for_lock", lambda case: None)

    case = make_case(tmp_path, "S3")
    dossier = b'title = "t"\ntext = """canary dossier"""\n'
    case.dossier_path.write_bytes(dossier)
    case.rubric_path.write_bytes(b"canary rubric\n")
    case.assembly_path.write_text(
        json.dumps({"dossier_sha256": hashlib.sha256(dossier).hexdigest()}), encoding="utf-8"
    )
    repo = tmp_path / "repo"
    repo.mkdir()
    lock = ["case", "lock", LABEL, "--root", str(repo)]
    assert main(["case", "scenario", "render", LABEL]) == CLEAN_EXIT
    capsys.readouterr()
    assert main(lock) == CLEAN_EXIT
    assert (repo / "experiment/cases" / LABEL / "case.lock").is_file()


def test_lock_refuses_while_the_scenario_is_edited_or_unrendered(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import hashlib

    case = make_case(tmp_path, "S3")
    dossier = b'title = "t"\ntext = """canary dossier"""\n'
    case.dossier_path.write_bytes(dossier)
    case.rubric_path.write_bytes(b"canary rubric\n")
    case.assembly_path.write_text(
        json.dumps({"dossier_sha256": hashlib.sha256(dossier).hexdigest()}), encoding="utf-8"
    )
    case.scenario_path.write_text('title = "hand written"\n', encoding="utf-8")
    repo = tmp_path / "repo"
    repo.mkdir()
    assert main(["case", "lock", LABEL, "--root", str(repo)]) == REFUSED_EXIT
    err = capsys.readouterr().err
    assert "the scenario check failed" in err and "render:" in err
    assert not (repo / "experiment").exists()


# --- sentence dropping -----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "available", "expected", "count"),
    [
        ("A {a}. B. C {b}.", {"a"}, "A {a}. B.", 1),
        ("A {a}? B! C {b}.", {"b"}, "B! C {b}.", 1),
        ("First {x}.\nSecond.\n\nThird {y}.", {"x"}, "First {x}.\nSecond.", 1),
        ("Only {gone}.\n\nKept.", set(), "Kept.", 1),
        ("{gone}.", set(), "", 1),
        ("No full stop {a}", {"a"}, "No full stop {a}", 0),
        ("Ends at the field {gone}", set(), "", 1),
        (
            "A {a}.B {b}. C.",
            {"a"},
            "C.",
            1,
        ),  # a '.' not followed by a space does not end a sentence
    ],
)
def test_a_sentence_ends_at_a_stop_followed_by_a_space_a_line_break_or_the_end(
    text: str, available: set[str], expected: str, count: int
) -> None:
    kept, dropped = drop_sentences(text, available, all_placeholders=False)
    assert (kept, dropped) == (expected, count)


def test_all_placeholders_mode_drops_every_sentence_with_a_figure() -> None:
    kept, dropped = drop_sentences("Plain. With {a}. Also plain.", {"a"}, all_placeholders=True)
    assert (kept, dropped) == ("Plain. Also plain.", 1)


# --- S3's figure-free form (search-half doc §4.6.5 step 0), the S3 floor and the pay-per-head check ------


def _s3_options(case: CaseAppendix) -> dict[str, str]:
    return {o["key"]: o["text"] for o in scenario_data(case)["choice"]["options"]}


def test_a_full_s3_case_keeps_the_templates_options_and_records_no_form(tmp_path: Path) -> None:
    case = make_case(tmp_path, "S3")
    render_case_scenario(case, ROOT)
    assert _s3_options(case) != FORM.options
    record = render_record(case)
    assert "case_form" not in record and record["equal_treatment_applied"] is False
    assert "management's estimates" in scenario_data(case)["scenario"]


def test_an_s3_case_missing_a_figure_gets_one_figure_free_sentence_per_option(
    tmp_path: Path,
) -> None:
    case = make_case(tmp_path, "S3", without(full_rows("S3"), "s3_sale_multiple"))
    render_case_scenario(case, ROOT)
    assert _s3_options(case) == FORM.options
    data = scenario_data(case)
    assert all(not re.search(r"\d|\$", text) for text in _s3_options(case).values())
    assert "management's estimates" not in data["scenario"]
    assert "Every option can be paid for from" in data["scenario"]
    record = render_record(case)
    assert record["equal_treatment_applied"] is True
    assert record["case_form"]["file"] == S3_FORM_PATH and len(record["case_form"]["sha256"]) == 64
    assert record["sentences_dropped"]["situation"] >= 1
    assert check_scenario(case, ROOT) == []


def test_the_form_does_not_touch_the_other_shapes(tmp_path: Path) -> None:
    case = make_case(tmp_path, "S1", without(full_rows("S1"), "oews_wage_office"))
    render_case_scenario(case, ROOT)
    assert "case_form" not in render_record(case) and "pay_per_head" not in render_record(case)


def test_an_s3_case_missing_a_figure_is_refused_if_the_form_is_not_there(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = make_case(tmp_path, "S3", without(full_rows("S3"), "s3_sale_multiple"))
    monkeypatch.setattr("horizon_compact.casebuild.scenario.S3_FORM_PATH", "experiment/none.toml")
    with pytest.raises(ScenarioRefused, match="is not there"):
        render_case_scenario(case, ROOT)
    assert not case.scenario_path.exists()


def test_the_check_fails_when_the_form_changes_after_the_render(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = make_case(tmp_path, "S3", without(full_rows("S3"), "s3_sale_multiple"))
    render_case_scenario(case, ROOT)
    other = tmp_path / "repo"
    shutil.copytree(ROOT / "experiment" / "company", other / "experiment" / "company")
    (other / "experiment" / "case-forms").mkdir()
    form = (ROOT / S3_FORM_PATH).read_text(encoding="utf-8")
    (other / S3_FORM_PATH).write_text(
        form.replace("Close the plant.", "Shut the plant."), encoding="utf-8"
    )
    assert check_scenario(case, other) != []


@pytest.mark.parametrize(
    "edit",
    [
        lambda s: s.replace('close = "Close the plant."', 'close = "Close the {plant}."'),
        lambda s: s.replace('close = "Close the plant."', 'close = "Close the plant. Move it."'),
        lambda s: s.replace('close = "Close the plant."\n', ""),
        lambda s: s.replace("drop_from_situation = [", "drop_from_situation = [] # ["),
    ],
)
def test_the_form_file_is_checked(edit: Any) -> None:
    text = (ROOT / S3_FORM_PATH).read_text(encoding="utf-8")
    parse_s3_form(text.encode())
    with pytest.raises(ScenarioRefused, match="invalid"):
        parse_s3_form(edit(text).encode())


def test_without_sentences_takes_a_whole_sentence_and_its_gap() -> None:
    text = "One. Two here. Three.\n\nFour."
    assert without_sentences(text, lambda s: s == "Two here.") == ("One. Three.\n\nFour.", 1)
    assert without_sentences(text, lambda s: s == "Four.") == ("One. Two here. Three.", 1)


@pytest.mark.parametrize(
    ("stated", "factor", "shown"), [(60, 1.0, 60), (52, 1.1, 57), (50, 1.0, 50), (50, 0.6, 30)]
)
def test_an_s3_total_under_100_after_scaling_is_a_number_to_the_nearest_person(
    tmp_path: Path, stated: int, factor: float, shown: int
) -> None:
    rows = full_rows("S3")
    rows["hc_p6"]["value"] = stated
    case = make_case(tmp_path, "S3", rows, factor=factor)
    render_case_scenario(case, ROOT)
    data = scenario_data(case)
    assert data["total"] == shown and f"{shown} employees" in data["scenario"]
    # the caps with a count of their own under 100 are set to it and never printed
    assert {c["row"] for c in render_record(case)["caps_set_to_total"]}
    assert "fewer than 100" not in data["scenario"].replace("fewer than 100 in", "")
    assert check_scenario(case, ROOT) == []


def test_an_s3_total_under_50_as_stated_fails_criterion_4(tmp_path: Path) -> None:
    rows = full_rows("S3")
    rows["hc_p6"]["value"] = 45
    with pytest.raises(ScenarioRefused, match="under 50 as stated") as caught:
        render_in_memory(make_case(tmp_path, "S3", rows, factor=1.6), ROOT)
    assert caught.value.criterion == CRITERION_4


def _with_stated_payroll(rows: dict[str, dict[str, Any]], dollars: int) -> None:
    rows["payroll_p6"] = {**rows["hc_p6"], "value": dollars, "unit": "usd_m", "scale": "dollars"}
    rows["payroll_p6"].update(source="pre_cutoff", accession=ACCESSION)


def _with_wage(rows: dict[str, dict[str, Any]], dollars: int) -> None:
    rows["plant_avg_pay"] = {
        "value": dollars,
        "unit": "usd",
        "scale": "none",
        "per": "employee",
        "source": "pre_cutoff",
        "accession": ACCESSION,
        "locator": "canary locator",
    }


def test_a_small_s3_total_with_a_stated_payroll_passes_the_check(tmp_path: Path) -> None:
    """52 people scaled by 0.9 is 46.8, stated as 47, beside a stated payroll of $2.86 million, which scales
    to $2.57 million and stays there (it was stated as 45 and $2.6 million, 5% off, before §4.6.6). (A usd_m
    row's value is in dollars.)"""
    rows = full_rows("S3")
    rows["hc_p6"]["value"] = 52
    _with_stated_payroll(rows, 2_860_000)
    case = make_case(tmp_path, "S3", rows, factor=0.9)
    render_case_scenario(case, ROOT)
    text = scenario_data(case)["scenario"]
    assert "47 employees" in text and "a payroll of $2.57 million" in text
    assert all(e["passed"] for e in render_record(case)["pay_per_head"])
    assert check_scenario(case, ROOT) == []


def test_a_small_s3_total_with_a_derived_payroll_passes_the_check(tmp_path: Path) -> None:
    """Stated 54 at 0.6 is 32 people on a $45,000 wage: a payroll of $1.44 million (the case step 4's review
    found failing, with a total of 30 and $1.4 million)."""
    rows = without(full_rows("S3"), "payroll_p6")
    rows["hc_p6"]["value"] = 54
    _with_wage(rows, 45_000)
    case = make_case(tmp_path, "S3", rows, factor=0.6)
    render_case_scenario(case, ROOT)
    text = scenario_data(case)["scenario"]
    assert "32 employees" in text and "a payroll of $1.44 million" in text
    assert all(e["passed"] for e in render_record(case)["pay_per_head"])
    assert check_scenario(case, ROOT) == []


def test_a_derived_s3_payroll_under_a_million_reads_with_all_its_digits(tmp_path: Path) -> None:
    rows = full_rows("S3")
    rows["hc_p6"]["value"] = 50
    _with_wage(rows, 31_500)
    case = make_case(tmp_path, "S3", rows, factor=0.6)
    render_case_scenario(case, ROOT)
    assert "a payroll of $0.945 million" in scenario_data(case)["scenario"]


@pytest.mark.parametrize(
    ("dollars", "reads"),
    [
        (1_080_000, "$1.08 million"),
        (946_000, "$0.946 million"),
        (900_000, "$0.9 million"),
        (1_000_000, "$1.0 million"),
        (14_300_000, "$14.3 million"),
        (14_000_000, "$14.0 million"),
        (1_230_000_000, "$1,230.0 million"),
    ],
)
def test_an_s3_total_pay_figure_reads_in_millions_with_the_digits_it_has(
    dollars: int, reads: str
) -> None:
    row = FIC.rows["payroll_p6"]
    assert _PayResolved("payroll_p6", row, Decimal(dollars)).shown == reads


def test_the_fictional_s3_payroll_still_reads_to_one_decimal() -> None:
    """Phase 4's rendered S3 is as it was: only a case's copy of the row reads with more digits."""
    assert FIC.resolved["payroll_p6"].shown.endswith(" million")
    assert len(FIC.resolved["payroll_p6"].shown.split(".")[1].split(" ")[0]) == 1


def test_pay_per_head_is_recorded_and_a_mis_scaled_wage_fails_it(tmp_path: Path) -> None:
    case = make_case(tmp_path, "S3")
    render_case_scenario(case, ROOT)
    entries = render_record(case)["pay_per_head"]
    assert [(e["field"], e["heads"], e["pay"], e["passed"]) for e in entries] == [
        ("situation", "hc_p6", "payroll_p6", True)
    ]
    # a per-head wage scaled like a total moves pay per head by the whole factor
    rows = full_rows("S3")
    for key in rows:
        if key.startswith("oews_wage_"):
            rows[key].update(scale="dollars")
            rows[key].pop("per", None)
    with pytest.raises(ScenarioRefused, match=r"moved more than 3\.5%"):
        render_in_memory(make_case(tmp_path / "wrong", "S3", rows), ROOT)
