"""The blind refusal-call workflow and ``hc analyze`` (Phase 4 code half IMPLEMENTATION doc sections 4.6 and
4.7). The sweeps are real ``run_session`` output on the company's S1, scripted: nothing here calls a model."""

from __future__ import annotations

import json
import random
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from analysis_helpers import DEVELOPMENT_MODEL, decision
from horizon_compact import cli
from horizon_compact.analysis.failures import (
    REFUSAL_CALLS_FILE,
    check_refusal_calls,
    parse_refusal_calls,
)
from horizon_compact.analysis.records import read_runs
from horizon_compact.experiment import Experiment, load_experiment
from horizon_compact.protocol.gate import GateResult
from horizon_compact.sweep.plan import SweepPlan, SweepRefusal, build_plan
from horizon_compact.sweep.prompt import render_prompt
from horizon_compact.sweep.refusals import (
    CALLS_FILE,
    META_FILE,
    calls_key,
    load_cases,
    make_calls,
    meta_key,
    require_calls_before_analysis,
)
from horizon_compact.sweep.runner import Role, sweep_prefix
from horizon_compact.sweep.store import LocalStore
from sweep_helpers import ScriptedProvider, raw_ok, session

SWEEP_ARGS = ["--experiment", "company", "--made-by", "a tester"]
REPLIES = [
    "I would rather not pick between these people, so I will not submit a split.",
    "Here is my thinking in prose; the split is about half and half.",
    "I cannot in good conscience make this call.",
    "Probably most should stay on, so I would keep them.",
]


@pytest.fixture(scope="module")
def company() -> Experiment:
    return load_experiment("company")


def s1_input(k: int) -> dict[str, Any]:
    return decision({"eliminate": 125 - k, "move_plant_pay": k, "move_keep_pay": 0})


def build(company: Experiment) -> SweepPlan:
    """S1 under all three wordings (the analysis wants the sealed one), two repeats: 30 runs, since a
    cell's variance needs two valid runs."""
    return build_plan(
        company,
        model_key=DEVELOPMENT_MODEL,
        label="refusals-test",
        repeats=2,
        seed=52,  # every run's prompt is different under this seed (play() checks); found for nova-lite
        scenarios=["s1"],
        templates=["w1", "w2", "w3"],
        official=True,
    )


def play(
    company: Experiment,
    plan: SweepPlan,
    store: LocalStore,
    no_tool: dict[int, str],
    *,
    role: Role = "official",
    stop_after: int | None = None,
) -> None:
    """Run the sweep. The runs at the indexes in ``no_tool`` answer in text, always (so each ends no_tool_call
    after its three attempts); every other run answers validly."""
    objectives = {o.id: o for o in company.objectives}
    scenario = company.get_scenario("s1")
    reply_for: dict[str, str] = {}
    seen_users: set[str] = set()
    for index, spec in enumerate(plan.runs):
        user = render_prompt(
            company,
            scenario,
            objectives[spec.objective_id],
            spec.wording_id,
            spec.menu_order_seed,
        ).user
        assert user not in seen_users, "two runs share a prompt: pick another seed"
        seen_users.add(user)
        if index in no_tool:
            reply_for[user] = no_tool[index]

    def script(n: int, request: Any) -> Any:
        text = reply_for.get(request.user)
        if text is not None:
            return raw_ok(request, calls=[], text=[text], stop="end_turn")
        return raw_ok(request, tool_input=s1_input(40 + n % 40))

    provider = ScriptedProvider(script)
    session(
        company,
        plan,
        provider,
        store,
        role=role,
        should_stop=(lambda: len(provider.requests) >= stop_after)
        if stop_after
        else (lambda: False),
    )


class Screen:
    """Scripted answers, and a record of every character shown or asked."""

    def __init__(self, answers: Callable[[str, int], str]) -> None:
        self._answers = answers
        self.shown: list[str] = []
        self.asked: list[str] = []
        self.texts_in_order: list[str] = []

    def show(self, text: str) -> None:
        self.shown.append(text)

    def ask(self, prompt: str) -> str:
        self.asked.append(prompt)
        return self._answers(prompt, len(self.asked))

    @property
    def everything(self) -> str:
        return "\n".join([*self.shown, *self.asked])


def answers_for(refusals: set[str], reason: str = "it wrote that it would not decide") -> Screen:
    """Answer r to a case whose shown text is in ``refusals`` and n to the rest, then y to the write."""
    screen = Screen(lambda prompt, n: "")

    def answer(prompt: str, n: int) -> str:
        if prompt.startswith("Write the calls"):
            return "y"
        if prompt.startswith("One line"):
            return reason
        case = screen.shown[-1] if screen.shown else ""
        return "r" if any(text in case for text in refusals) else "n"

    screen._answers = answer
    return screen


def made(
    store: LocalStore, plan: SweepPlan, screen: Screen, *, seed: int = 1, role: Role = "official"
) -> Any:
    return make_calls(
        store,
        sweep_prefix(plan.experiment, plan.sweep_id, role),
        plan.sweep_id,
        made_by="a tester",
        ask=screen.ask,
        show=screen.show,
        rng=random.Random(seed),
    )


@pytest.fixture
def finished(company: Experiment, tmp_path: Path) -> Iterator[tuple[SweepPlan, LocalStore]]:
    """A finished sweep of thirty runs; four of them (index 0, 3, 5, 8) end as no_tool_call."""
    plan = build(company)
    store = LocalStore(tmp_path)
    play(company, plan, store, dict(zip((0, 3, 5, 8), REPLIES, strict=True)))
    yield plan, store


# --- the screen is blind ----------------------------------------------------------------------------


def test_the_calls_file_name_is_the_one_the_frozen_analysis_reads() -> None:
    assert CALLS_FILE == REFUSAL_CALLS_FILE


def test_the_screen_shows_no_run_objective_wording_scenario_or_flag(
    company: Experiment, finished: tuple[SweepPlan, LocalStore]
) -> None:
    plan, store = finished
    screen = answers_for(set())
    made(store, plan, screen)
    seen = screen.everything
    forbidden = {spec.run_id for spec in plan.runs}
    for objective in company.objectives:
        forbidden.update(v for v in (objective.who, objective.when) if v)
    for value in forbidden:
        assert value not in seen, value
    for pattern in (
        r"\bs1\b",
        r"\bw[123]\b",
        r"possible_decline",
        r"\bflag",
        r"\br-[0-9a-f]{12}\b",
    ):
        assert re.search(pattern, seen) is None, pattern
    # what it does show: a masked label and the reply, in full
    for reply in REPLIES:
        assert reply in seen
    assert "case 1 of 4" in seen and "case 4 of 4" in seen


def test_only_the_final_no_tool_call_replies_are_cases(
    finished: tuple[SweepPlan, LocalStore],
) -> None:
    plan, store = finished
    cases = load_cases(store, sweep_prefix(plan.experiment, plan.sweep_id, "official"))
    assert sorted(c.text for c in cases) == sorted(REPLIES)
    assert len({c.run_id for c in cases}) == 4


def test_the_order_is_shuffled_and_not_the_run_id_order(
    finished: tuple[SweepPlan, LocalStore],
) -> None:
    plan, store = finished
    prefix = sweep_prefix(plan.experiment, plan.sweep_id, "official")
    by_run_id = [c.text for c in load_cases(store, prefix)]
    orders = set()
    for seed in range(12):
        screen = answers_for(set())
        shown = _case_order(screen, store, plan, seed)
        orders.add(tuple(shown))
        assert sorted(shown) == sorted(by_run_id)
    assert len(orders) > 1  # the order depends on the shuffle, not on the data


def _case_order(screen: Screen, store: LocalStore, plan: SweepPlan, seed: int) -> list[str]:
    # A fresh copy of the sweep each time, since a calls file is written once.
    copy = LocalStore(store.root.parent / f"copy-{seed}")
    prefix = sweep_prefix(plan.experiment, plan.sweep_id, "official")
    for key in store.list_keys(prefix):
        text = store.get(key)
        assert text is not None and copy.put_new(key, text)
    made(copy, plan, screen, seed=seed)
    order = []
    for block in screen.shown:
        for reply in REPLIES:
            if reply in block and block.startswith("\n--- case"):
                order.append(reply)
    return order


# --- what is written --------------------------------------------------------------------------------


def test_the_file_names_only_the_runs_called_refusals_and_the_reasons(
    company: Experiment, finished: tuple[SweepPlan, LocalStore]
) -> None:
    plan, store = finished
    prefix = sweep_prefix(plan.experiment, plan.sweep_id, "official")
    cases = {c.text: c.run_id for c in load_cases(store, prefix)}
    screen = answers_for({REPLIES[0], REPLIES[2]}, reason="it declined in its own words")
    result = made(store, plan, screen)
    assert (result.cases, result.refusals) == (4, 2)
    written = json.loads(store.get(calls_key(prefix)) or "")
    assert written == {
        cases[REPLIES[0]]: "it declined in its own words",
        cases[REPLIES[2]]: "it declined in its own words",
    }
    # the frozen analysis accepts it as it is, and it names only no_tool_call runs
    calls = parse_refusal_calls(store.get(calls_key(prefix)) or "")
    check_refusal_calls(read_runs(store, prefix).rows, calls)


def test_the_label_answered_is_the_run_called(
    company: Experiment, finished: tuple[SweepPlan, LocalStore]
) -> None:
    """The memory-only mapping from a masked label to a run id points at the right run for every shuffle."""
    plan, store = finished
    prefix = sweep_prefix(plan.experiment, plan.sweep_id, "official")
    cases = {c.text: c.run_id for c in load_cases(store, prefix)}
    for seed in range(6):
        copy = LocalStore(store.root.parent / f"mapping-{seed}")
        for key in store.list_keys(prefix):
            text = store.get(key)
            assert text is not None and copy.put_new(key, text)
        screen = answers_for({REPLIES[1]})
        made(copy, plan, screen, seed=seed)
        written = json.loads(copy.get(calls_key(prefix)) or "")
        assert list(written) == [cases[REPLIES[1]]]


def test_no_refusal_called_still_writes_an_empty_file_so_the_calls_are_on_record(
    finished: tuple[SweepPlan, LocalStore],
) -> None:
    plan, store = finished
    prefix = sweep_prefix(plan.experiment, plan.sweep_id, "official")
    made(store, plan, answers_for(set()))
    assert json.loads(store.get(calls_key(prefix)) or "") == {}
    require_calls_before_analysis(store, prefix, read_runs(store, prefix).rows)  # now allowed


def test_the_sidecar_says_who_when_how_many_and_the_limit_and_names_no_run(
    finished: tuple[SweepPlan, LocalStore],
) -> None:
    plan, store = finished
    prefix = sweep_prefix(plan.experiment, plan.sweep_id, "official")
    made(store, plan, answers_for({REPLIES[0]}))
    text = store.get(meta_key(prefix)) or ""
    meta = json.loads(text)
    assert meta["made_by"] == "a tester" and meta["sweep_id"] == plan.sweep_id
    assert (meta["cases_shown"], meta["refusals_called"]) == (4, 1)
    assert "A reply can still name the objective" in meta["limit"]
    assert "T" in meta["made_at"] and meta["order"].startswith("shuffled")
    assert not re.search(r"r-[0-9a-f]{12}", text)
    assert META_FILE == "refusal-calls.meta.json"


def test_a_second_run_is_refused_before_the_first_question(
    finished: tuple[SweepPlan, LocalStore],
) -> None:
    plan, store = finished
    made(store, plan, answers_for(set()))
    again = answers_for(set())
    with pytest.raises(SweepRefusal, match="already exists"):
        made(store, plan, again)
    assert again.asked == [] and again.shown == []


def test_a_sweep_with_an_unfinished_run_is_refused(company: Experiment, tmp_path: Path) -> None:
    plan = build(company)
    store = LocalStore(tmp_path)
    play(company, plan, store, {0: REPLIES[0]}, stop_after=2)
    screen = answers_for(set())
    with pytest.raises(SweepRefusal, match="unfinished"):
        made(store, plan, screen)
    assert screen.asked == []


def test_a_sweep_with_no_no_tool_call_run_writes_nothing(
    company: Experiment, tmp_path: Path
) -> None:
    plan = build(company)
    store = LocalStore(tmp_path)
    play(company, plan, store, {})
    screen = answers_for(set())
    result = made(store, plan, screen)
    assert (result.cases, result.calls_key) == (0, None)
    assert store.get(calls_key(sweep_prefix(plan.experiment, plan.sweep_id, "official"))) is None
    assert "nothing to call" in screen.everything


def test_no_manifest_is_refused(tmp_path: Path, company: Experiment) -> None:
    with pytest.raises(SweepRefusal, match="no manifest"):
        make_calls(
            LocalStore(tmp_path),
            "official/company/none/",
            "none",
            made_by="a tester",
            ask=lambda p: "",
            show=lambda t: None,
        )


def test_made_by_is_required(finished: tuple[SweepPlan, LocalStore]) -> None:
    plan, store = finished
    with pytest.raises(SweepRefusal, match="made-by"):
        make_calls(
            store,
            sweep_prefix(plan.experiment, plan.sweep_id, "official"),
            plan.sweep_id,
            made_by="  ",
            ask=lambda p: "",
            show=lambda t: None,
        )


def test_running_out_of_input_or_declining_to_confirm_writes_nothing(
    finished: tuple[SweepPlan, LocalStore],
) -> None:
    plan, store = finished
    prefix = sweep_prefix(plan.experiment, plan.sweep_id, "official")

    def eof(prompt: str, n: int) -> str:
        if n > 2:
            raise EOFError
        return "n"

    with pytest.raises(SweepRefusal, match="not finished"):
        made(store, plan, Screen(eof))
    assert store.get(calls_key(prefix)) is None

    screen = answers_for(set())
    screen._answers = lambda prompt, n: "" if prompt.startswith("Write") else "n"
    with pytest.raises(SweepRefusal, match="not confirmed"):
        made(store, plan, screen)
    assert store.get(calls_key(prefix)) is None and store.get(meta_key(prefix)) is None


def test_a_bad_answer_or_an_empty_reason_is_asked_again(
    finished: tuple[SweepPlan, LocalStore],
) -> None:
    plan, store = finished
    prefix = sweep_prefix(plan.experiment, plan.sweep_id, "official")
    script = iter(["maybe", "r", "", "  ", "because it said no", "n", "n", "n", "y"])
    screen = Screen(lambda prompt, n: next(script))
    made(store, plan, screen)
    assert len(json.loads(store.get(calls_key(prefix)) or "")) == 1
    assert any("Answer r" in s for s in screen.shown) and any(
        "needs a reason" in s for s in screen.shown
    )


# --- analysis comes second --------------------------------------------------------------------------


def test_analysis_is_refused_until_the_calls_exist(
    finished: tuple[SweepPlan, LocalStore],
) -> None:
    plan, store = finished
    prefix = sweep_prefix(plan.experiment, plan.sweep_id, "official")
    rows = read_runs(store, prefix).rows
    with pytest.raises(SweepRefusal, match="make the blind calls first"):
        require_calls_before_analysis(store, prefix, rows)
    made(store, plan, answers_for(set()))
    require_calls_before_analysis(store, prefix, rows)


def test_a_sweep_with_no_no_tool_call_needs_no_file(company: Experiment, tmp_path: Path) -> None:
    plan = build(company)
    store = LocalStore(tmp_path)
    play(company, plan, store, {})
    prefix = sweep_prefix(plan.experiment, plan.sweep_id, "official")
    require_calls_before_analysis(store, prefix, read_runs(store, prefix).rows)


# --- the commands -----------------------------------------------------------------------------------


@pytest.fixture
def local(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> LocalStore:
    """The command's store, and its analysis gate passed: no lock exists before the tag. The gate itself is
    tested in test_protocol_gate.py, and its refusal here below."""
    store = LocalStore(tmp_path / "bucket")
    monkeypatch.setattr(cli, "_store", lambda args, session: store)
    monkeypatch.setattr(cli, "run_analysis_gate", lambda experiment: GateResult())
    return store


def analyze_args(plan: SweepPlan, tmp_path: Path, *extra: str) -> list[str]:
    root = tmp_path / "repo"
    root.mkdir(exist_ok=True)
    return [
        "analyze", "--experiment", "company", "--sweep", plan.sweep_id, "--store", "local",
        "--protocol", "prereg-test", "--root", str(root), *extra,
    ]  # fmt: skip


def test_hc_analyze_refuses_a_sweep_that_has_no_tool_calls_and_no_calls_file(
    company: Experiment, local: LocalStore, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    plan = build(company)
    play(company, plan, local, {0: REPLIES[0]})
    assert cli.main(analyze_args(plan, tmp_path)) == 2
    assert "make the blind calls first" in capsys.readouterr().err
    assert not (tmp_path / "repo" / "experiment").exists()


def test_hc_analyze_refuses_an_official_sweep_unless_the_analysis_is_the_locked_one(
    company: Experiment,
    local: LocalStore,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plan = build(company)
    play(company, plan, local, {})
    monkeypatch.undo()  # the real gate, on this repository, which has no lock before the tag
    monkeypatch.setattr(cli, "_store", lambda args, session: local)
    assert cli.main(analyze_args(plan, tmp_path)) == 2
    err = capsys.readouterr().err
    assert "official analysis refused" in err and "no committed protocol" in err
    assert not (tmp_path / "repo" / "experiment").exists()
    # a placeholder development sweep is not official, so the gate does not apply to it


def test_hc_analyze_refuses_a_half_finished_sweep_through_the_runset(
    company: Experiment, local: LocalStore, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    plan = build(company)
    play(company, plan, local, {}, stop_after=3)
    assert cli.main(analyze_args(plan, tmp_path)) == 2
    assert "unfinished" in capsys.readouterr().err
    assert not (tmp_path / "repo" / "experiment").exists()


def test_hc_analyze_refuses_development_records_on_real_content(
    company: Experiment, local: LocalStore, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    plan = build(company)
    play(company, plan, local, {}, role="development")
    assert cli.main(analyze_args(plan, tmp_path, "--role", "development")) == 2
    assert "refusing to read" in capsys.readouterr().err


def test_hc_analyze_writes_one_results_file_and_the_same_bytes_again(
    company: Experiment, local: LocalStore, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    plan = build(company)
    play(company, plan, local, {0: REPLIES[0], 3: REPLIES[1]})
    made(local, plan, answers_for({REPLIES[0]}))
    assert cli.main(analyze_args(plan, tmp_path)) == 0
    out = capsys.readouterr().out
    path = tmp_path / "repo" / "experiment" / "results" / "prereg-test" / DEVELOPMENT_MODEL
    written = path / f"{plan.sweep_id}.json"
    assert f"wrote {written.relative_to(tmp_path / 'repo')}" in out and "1 refusal calls" in out
    first = written.read_bytes()
    record = json.loads(first)
    assert record["sweep_id"] == plan.sweep_id and len(record["refusal_calls"]) == 1
    assert cli.main(analyze_args(plan, tmp_path)) == 0  # the same input, the same bytes, no error
    assert written.read_bytes() == first
    assert sorted(p.name for p in path.iterdir()) == [written.name]


def test_hc_analyze_takes_the_protocol_name_from_the_lock_when_not_given(
    company: Experiment,
    local: LocalStore,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plan = build(company)
    play(company, plan, local, {})
    args = [a for a in analyze_args(plan, tmp_path) if a not in ("--protocol", "prereg-test")]
    assert cli.main(args) == 2  # no lock in the empty root
    assert "no --protocol given" in capsys.readouterr().err
    monkeypatch.setattr(cli, "read_lock", lambda path: SimpleNamespace(protocol="prereg-v1"))
    assert cli.main(args) == 0
    results = tmp_path / "repo" / "experiment" / "results" / "prereg-v1"
    assert (results / DEVELOPMENT_MODEL / f"{plan.sweep_id}.json").is_file()


def test_hc_sweep_refusals_asks_in_the_terminal_and_writes_once(
    company: Experiment,
    local: LocalStore,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plan = build(company)
    play(company, plan, local, {1: REPLIES[0], 4: REPLIES[2]})
    typed = iter(["r", "it said it would not", "n", "y"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(typed))
    args = ["sweep", "refusals", *SWEEP_ARGS, "--sweep", plan.sweep_id, "--store", "local"]
    assert cli.main(args) == 0
    out = capsys.readouterr().out
    assert "wrote" in out and "1 of 2 called refusals" in out
    prefix = sweep_prefix("company", plan.sweep_id, "official")
    assert len(json.loads(local.get(calls_key(prefix)) or "")) == 1
    assert cli.main(args) == 2  # once only
    assert "already exists" in capsys.readouterr().err
