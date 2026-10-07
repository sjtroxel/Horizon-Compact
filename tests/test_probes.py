"""Comprehension probes (Phase 2.5 IMPLEMENTATION doc section 10): the question files, the keys, the probe
prompt and tool, the scoring, the runner and the report. Nothing here calls a model: the provider is
scripted."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from horizon_compact import cli
from horizon_compact.experiment import Experiment, load_experiment
from horizon_compact.probes.questions import (
    PROBE_INTRO,
    PROBE_MENU_SEED,
    TOOL_NAME,
    Key,
    ProbeError,
    Question,
    build_probe_tool,
    load_probe_file,
    render_probe,
    resolve_keys,
    score,
)
from horizon_compact.probes.run import (
    ProbeSet,
    check_probe_model,
    load_probe_sets,
    probe_report,
    run_probes,
)
from horizon_compact.providers.base import DecisionRequest, ModelRoute, RawDecision
from horizon_compact.scenarios.render import load_scenario_figures
from horizon_compact.sweep.plan import SweepRefusal
from horizon_compact.sweep.prompt import render_prompt
from horizon_compact.sweep.store import LocalStore
from sweep_helpers import LAPTOP, FakeClock, ScriptedProvider, raw_error, raw_ok

ROOT = Path(__file__).resolve().parents[1]
ROUTE = ModelRoute("qwen-local", "qwen-test:1b", "local", invoke_id="qwen-test:1b")


@pytest.fixture(scope="module")
def company() -> Experiment:
    return load_experiment("company")


@pytest.fixture(scope="module")
def sets(company: Experiment) -> list[ProbeSet]:
    return load_probe_sets(company, load_scenario_figures(ROOT), None)


def right_answers(probe_set: ProbeSet) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in probe_set.keys:
        out[key.question.id] = list(key.value) if isinstance(key.value, tuple) else key.value
    return out


def answering(
    probe_sets: list[ProbeSet], answers: dict[str, Any] | None = None
) -> ScriptedProvider:
    """A provider that answers every probe correctly, or with ``answers`` when given."""

    def script(n: int, request: DecisionRequest) -> RawDecision:
        probe_set = next(
            s for s in probe_sets if all(k.question.text in request.user for k in s.keys)
        )
        given = answers if answers is not None else right_answers(probe_set)
        return raw_ok(request, calls=[{"name": TOOL_NAME, "input": given}])

    return ScriptedProvider(script)


def run(
    company: Experiment,
    sets: list[ProbeSet],
    provider: ScriptedProvider,
    store: LocalStore,
    *,
    repeats: int = 2,
    model: str = "qwen-local",
    cap_usd: float = 5.0,
) -> Any:
    clock = FakeClock()
    return run_probes(
        experiment=company,
        model_key=model,
        sets=sets,
        repeats=repeats,
        label="t",
        route=ROUTE,
        provider=provider,
        store=store,
        identity=LAPTOP,
        account_id="000000000000",
        cap_usd=cap_usd,
        max_minutes=30.0,
        harness_version="0.test",
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )


# --- the files and the keys -------------------------------------------------------------------------


def test_every_scenario_has_eight_to_ten_questions_with_resolvable_keys(
    sets: list[ProbeSet],
) -> None:
    assert [s.scenario_id for s in sets] == ["s1", "s2", "s3", "s4"]
    for probe_set in sets:
        assert 8 <= len(probe_set.keys) <= 10


def test_numeric_keys_are_the_values_the_text_shows(sets: list[ProbeSet]) -> None:
    keys = {(s.scenario_id, k.question.id): k.value for s in sets for k in s.keys}
    assert keys[("s1", "q1")] == 125
    assert keys[("s2", "q1")] == 112_100_000  # "$112.1 million" in the text
    assert keys[("s2", "q5")] == 10  # max_wage_cut, 10.0%, as a percentage
    assert keys[("s4", "q6")] == 25_400_000  # $20.4 million plus a $5,000,000 cut


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"type": "number", "answer": "1"}, "answer_formula only"),
        ({"type": "yes_no", "answer": "maybe"}, "yes"),
        ({"type": "key", "choices": ["a", "b"], "answer": "c"}, "one of its choices"),
        ({"type": "keys", "choices": ["a", "b"], "answer": []}, "non-empty list"),
        ({"type": "key", "choices": ["a"], "answer": "a"}, "two or more"),
        ({"type": "yes_no", "answer": "yes", "answer_formula": "x"}, "only a number"),
    ],
)
def test_a_question_whose_answer_does_not_fit_its_type_is_refused(
    fields: dict[str, Any], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        Question.model_validate({"id": "q1", "text": "t", **fields})


def test_a_choice_that_is_not_one_of_the_scenarios_keys_is_refused(
    company: Experiment, sets: list[ProbeSet]
) -> None:
    probe = sets[0].probe
    bad = probe.model_copy(
        update={
            "questions": [
                Question(
                    id="q1",
                    type="key",
                    text="t",
                    choices=["eliminate", "invented"],
                    answer="eliminate",
                ),
                *probe.questions[1:],
            ]
        }
    )
    with pytest.raises(ProbeError, match="invented"):
        resolve_keys(bad, company.get_scenario("s1"), load_scenario_figures(ROOT))


def test_an_answer_formula_naming_no_row_is_refused(
    company: Experiment, sets: list[ProbeSet]
) -> None:
    probe = sets[0].probe
    bad = probe.model_copy(
        update={
            "questions": [
                Question(id="q1", type="number", text="t", answer_formula="no_such_row * 2"),
                *probe.questions[1:],
            ]
        }
    )
    with pytest.raises(ProbeError, match="no_such_row"):
        resolve_keys(bad, company.get_scenario("s1"), load_scenario_figures(ROOT))


def test_a_probe_file_for_the_wrong_scenario_is_refused(tmp_path: Path) -> None:
    text = (ROOT / "experiment/company/probes/s1.toml").read_text()
    path = tmp_path / "s2.toml"
    path.write_text(text)
    with pytest.raises(ProbeError, match="file name must match"):
        load_probe_file(path)


# --- the prompt and the tool --------------------------------------------------------------------------


def test_a_probe_has_no_objective_and_no_instruction_and_reads_the_same_menu(
    company: Experiment, sets: list[ProbeSet]
) -> None:
    for probe_set in sets:
        scenario = company.get_scenario(probe_set.scenario_id)
        probe = render_probe(company, scenario, probe_set.probe)
        decision = render_prompt(company, scenario, company.objectives[0], "w1", PROBE_MENU_SEED)
        assert probe.system == decision.system
        assert (probe.lever_order, probe.option_order) == (
            decision.lever_order,
            decision.option_order,
        )
        for objective in company.objectives:
            for template_id in company.templates:
                assert company.wording_sentence(objective, template_id) not in probe.user
        assert scenario.instruction.strip() not in probe.user
        assert PROBE_INTRO in probe.user
        parts = decision.user.split("\n\n")
        assert parts[-2] in probe.user  # the menu, or the options when there are some, unchanged


def test_the_probe_prompt_is_the_same_on_every_call(
    company: Experiment, sets: list[ProbeSet]
) -> None:
    scenario = company.get_scenario("s4")
    assert render_probe(company, scenario, sets[3].probe) == render_probe(
        company, scenario, sets[3].probe
    )


def test_the_tool_has_one_typed_field_per_question(sets: list[ProbeSet]) -> None:
    schema = build_probe_tool(sets[1].probe).input_schema
    properties = schema["properties"]
    assert list(properties) == [f"q{n}" for n in range(1, 11)]
    assert schema["required"] == list(properties)
    assert properties["q1"]["type"] == "number"
    assert properties["q2"]["type"] == "array"
    assert properties["q6"]["enum"] == ["yes", "no"]
    assert schema["additionalProperties"] is False


# --- scoring ------------------------------------------------------------------------------------------


def key(kind: str, value: Any, choices: list[str] | None = None) -> Key:
    fields: dict[str, Any] = {"id": "q1", "type": kind, "text": "t"}
    if kind == "number":
        fields["answer_formula"] = "x"
    else:
        fields["answer"] = list(value) if isinstance(value, tuple) else value
        if choices:
            fields["choices"] = choices
    return Key(Question.model_validate(fields), value)


@pytest.mark.parametrize(
    ("given", "right"),
    [
        (112_100_000, True),
        (113_200_000, True),  # within 1%
        (113_300_000, False),  # beyond 1%
        (112.1, False),  # millions, not dollars
        ("$112,100,000", True),  # a string that is plainly the number
        ("about 112 million", False),
        (True, False),
        (None, False),
    ],
)
def test_a_number_is_right_within_one_percent(given: Any, right: bool) -> None:
    assert score([key("number", 112_100_000.0)], {"q1": given}) == {"q1": right}


def test_an_exact_question_takes_no_tolerance_and_counts_of_people_are_exact(
    sets: list[ProbeSet],
) -> None:
    exact = Key(Question(id="q1", type="number", text="t", answer_formula="x", exact=True), 125.0)
    assert score([exact], {"q1": 125}) == {"q1": True}
    assert score([exact], {"q1": 124}) == {"q1": False}  # within 1%, and still wrong
    assert next(k for k in sets[2].keys if k.question.id == "q1").question.exact  # S3's head count


def test_only_a_number_question_can_be_exact() -> None:
    with pytest.raises(ValidationError, match="only a number question can be exact"):
        Question(id="q1", type="yes_no", text="t", answer="yes", exact=True)


def test_a_zero_key_needs_exactly_zero() -> None:
    assert score([key("number", 0.0)], {"q1": 0}) == {"q1": True}
    assert score([key("number", 0.0)], {"q1": 0.001}) == {"q1": False}


def test_keys_are_compared_as_sets_and_a_key_and_a_yes_no_exactly() -> None:
    keys_key = key("keys", ("a", "b"), ["a", "b", "c"])
    assert score([keys_key], {"q1": ["b", "a"]}) == {"q1": True}
    assert score([keys_key], {"q1": ["a"]}) == {"q1": False}
    assert score([keys_key], {"q1": ["a", "b", "c"]}) == {"q1": False}
    assert score([keys_key], {"q1": ["a", "a", "b"]}) == {"q1": False}
    assert score([key("key", "b", ["a", "b"])], {"q1": "b"}) == {"q1": True}
    assert score([key("yes_no", "no")], {"q1": "No"}) == {"q1": True}
    assert score([key("yes_no", "no")], {"q1": False}) == {"q1": False}


def test_a_missing_answer_or_no_answers_at_all_is_wrong() -> None:
    keys = [key("yes_no", "yes")]
    assert score(keys, {}) == {"q1": False}
    assert score(keys, None) == {"q1": False}
    assert score(keys, "yes") == {"q1": False}


# --- refusals -----------------------------------------------------------------------------------------


def test_an_official_model_is_never_asked_about_real_content(company: Experiment) -> None:
    with pytest.raises(SweepRefusal, match="not the development model"):
        check_probe_model(company, "sonnet-4-6")
    check_probe_model(company, "qwen-local")
    check_probe_model(company, "gpt-oss-openrouter")


def test_the_cli_refuses_an_official_model_before_it_reads_anything_else(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = ["probes", "run", "--experiment", "company", "--model", "sonnet-4-6", "--label", "x"]
    assert cli.main(args) == 2
    assert "not the development model" in capsys.readouterr().err


def test_an_experiment_without_probes_is_refused(capsys: pytest.CaptureFixture[str]) -> None:
    args = ["probes", "run", "--experiment", "s4shape", "--model", "qwen-local", "--label", "x"]
    assert cli.main(args) == 2
    assert "has no probes" in capsys.readouterr().err


# --- running --------------------------------------------------------------------------------------------


def test_a_run_writes_one_record_per_repeat_with_the_keys_and_the_marks(
    tmp_path: Path, company: Experiment, sets: list[ProbeSet]
) -> None:
    store = LocalStore(tmp_path)
    result = run(company, sets, answering(sets), store)
    assert (result.stopped, result.repeats_total, result.repeats_done_now) == ("complete", 8, 8)
    keys = store.list_keys(f"development/company/probes/{result.run_id}/")
    assert len(keys) == 8
    record = json.loads(store.get(keys[0]) or "{}")
    assert record["kind"] == "probe" and record["status"] == "answered"
    assert all(record["correct"].values())
    assert record["content_hash"] == company.content_hash
    assert "objective_id" not in record


def test_a_rerun_resumes_and_repeats_nothing(
    tmp_path: Path, company: Experiment, sets: list[ProbeSet]
) -> None:
    store = LocalStore(tmp_path)
    first = run(company, sets[:1], answering(sets), store)
    provider = answering(sets)
    second = run(company, sets[:1], provider, store)
    assert first.run_id == second.run_id
    assert (second.repeats_done_before, second.repeats_done_now) == (2, 0)
    assert provider.requests == []


def test_a_model_failure_is_recorded_not_retried_and_an_api_error_is_retried(
    tmp_path: Path, company: Experiment, sets: list[ProbeSet]
) -> None:
    def script(n: int, request: DecisionRequest) -> RawDecision:
        if n == 1:
            return raw_error(request, "ThrottlingException", "slow down")
        if n == 2:
            return raw_ok(
                request, calls=[], text=["Here are my answers in prose."], stop="end_turn"
            )
        return raw_ok(request, calls=[{"name": TOOL_NAME, "input": right_answers(sets[0])}])

    provider = ScriptedProvider(script)
    store = LocalStore(tmp_path)
    result = run(company, sets[:1], provider, store)
    assert result.stopped == "complete"
    assert len(provider.requests) == 3  # the throttle once, then one call per repeat
    statuses = [
        json.loads(store.get(k) or "{}")["status"]
        for k in sorted(store.list_keys(f"development/company/probes/{result.run_id}/"))
    ]
    assert statuses == ["no_tool_call", "answered"]


def test_an_official_model_cannot_run_probes_even_when_called_directly(
    tmp_path: Path, company: Experiment, sets: list[ProbeSet]
) -> None:
    with pytest.raises(SweepRefusal):
        run(company, sets, answering(sets), LocalStore(tmp_path), model="sonnet-4-6")


def test_the_cap_stops_a_run_before_a_call_it_cannot_afford(
    tmp_path: Path, company: Experiment, sets: list[ProbeSet]
) -> None:
    provider = answering(sets)
    result = run(
        company, sets, provider, LocalStore(tmp_path), model="gpt-oss-openrouter", cap_usd=0.0
    )
    assert result.stopped == "cap_reached"
    assert provider.requests == []


# --- the report ---------------------------------------------------------------------------------------


def test_the_report_shows_each_question_its_key_and_correct_of_the_repeats(
    tmp_path: Path, company: Experiment, sets: list[ProbeSet]
) -> None:
    store = LocalStore(tmp_path)
    wrong = {**right_answers(sets[0]), "q1": 124, "q5": "eliminate"}

    def script(n: int, request: DecisionRequest) -> RawDecision:
        given = wrong if n == 1 else right_answers(sets[0])
        return raw_ok(request, calls=[{"name": TOOL_NAME, "input": given}])

    result = run(company, sets[:1], ScriptedProvider(script), store, repeats=5)
    report = probe_report(store, company, result.run_id, sets[:1], 5)
    rows = {
        line.split(" | ")[0].strip("| "): line
        for line in report.splitlines()
        if line.startswith("| q")
    }
    assert "4 of 5 | yes" in rows["q1"]  # 124 for 125 is wrong (an exact count); 4 of 5 passes
    assert "4 of 5 | yes" in rows["q5"]
    assert "124" in rows["q1"]
    assert "5 of 5 | yes" in rows["q2"]
    assert "5 of 5 repeats recorded" in report


# --- the command line, end to end, with a scripted model --------------------------------------------


def test_probes_run_then_report_from_the_command_line(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    sets: list[ProbeSet],
) -> None:
    def fake_git(*args: str) -> str:
        return str(tmp_path) if "--show-toplevel" in args else ("abc1234" if "HEAD" in args else "")

    def fast(**kwargs: Any) -> Any:
        clock = FakeClock()
        return run_probes(**kwargs, monotonic=clock.monotonic, sleep=clock.sleep)

    monkeypatch.setattr(cli, "_git", fake_git)
    monkeypatch.setattr(cli, "run_probes", fast)
    monkeypatch.setattr(cli, "OllamaProvider", lambda url, num_ctx: answering(sets))
    args = ["--experiment", "company", "--model", "qwen-local", "--label", "cli", "--repeats", "2"]
    assert cli.main(["probes", "run", *args, "--scenario", "s3"]) == 0
    out = capsys.readouterr().out
    assert "repeats done:    2 of 2" in out
    assert cli.main(["probes", "report", *args, "--scenario", "s3"]) == 0
    written = list((tmp_path / "docs/phases/evidence/phase-2.5/probes").glob("*.md"))
    assert len(written) == 1
    report = written[0].read_text()
    assert report.endswith("|\n")  # exactly one final newline: the end-of-file hook passes
    assert "## s3" in report
    assert report.count("| 2 of 2 | yes |") == 10
