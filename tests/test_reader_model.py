"""The reader's entry in models.toml, and the tripwire: it is never planned, probed or locked (search-half
IMPLEMENTATION doc §4.9, decision 3). Nothing here calls a model."""

from __future__ import annotations

import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from horizon_compact.cli import REFUSED_EXIT, main
from horizon_compact.experiment import ExperimentError, load_experiment
from horizon_compact.model_config import READER_ROLE, ModelConfig, ModelsFile
from horizon_compact.probes.run import check_probe_model
from horizon_compact.protocol.gate import check_model
from horizon_compact.protocol.lock import LockError, build_lock, lock_path, read_lock
from horizon_compact.reader.entry import (
    ReaderModelError,
    entry_sha256,
    load_reader_model,
    reader_route,
)
from horizon_compact.sweep.plan import SweepRefusal, build_plan, check_thinking_plan

ROOT = Path(__file__).resolve().parents[1]
KEY = "gemini-3-1-pro-reader"
EXPERIMENTS = ("company", "placeholder", "s4shape", "shapes")


def _entry(**changes: object) -> dict[str, object]:
    entry: dict[str, object] = {
        "model_id": "google/gemini-3.1-pro-preview",
        "route": "openrouter",
        "reasoning_effort": "medium",
        "max_tokens": 24000,
        "requests_per_minute": 10,
        "role": READER_ROLE,
        "prices": {"input": 2.0, "output": 12.0, "cache_read": 2.0, "cache_write_5m": 2.0},
    }
    entry.update(changes)
    return entry


def _file(**models: dict[str, object]) -> dict[str, object]:
    return {"pace_fraction": 0.8, "models": models}


# --- the entry ---------------------------------------------------------------------------------------------


def test_the_entry_is_gemini_3_1_pro_on_openrouter_with_a_fixed_allowance_and_level() -> None:
    key, config = load_reader_model()
    assert key == KEY
    assert config.model_id == "google/gemini-3.1-pro-preview"
    assert config.route == "openrouter" and config.role == READER_ROLE
    assert config.max_tokens == 24000 and config.reasoning_effort == "medium"
    assert (config.prices.input, config.prices.output) == (2.0, 12.0)


def test_the_route_is_unpinned_and_carries_the_reasoning_level() -> None:
    key, config = load_reader_model()
    route = reader_route(key, config)
    assert (route.key, route.model_id, route.invoke_id) == (
        KEY,
        "google/gemini-3.1-pro-preview",
        "google/gemini-3.1-pro-preview",
    )
    assert route.route_kind == "openrouter" and route.pinned_provider is None
    assert route.reasoning_effort == "medium"


def test_the_entry_hash_follows_every_field() -> None:
    key, config = load_reader_model()
    other = config.model_copy(update={"max_tokens": 12000})
    assert entry_sha256(key, other) != entry_sha256(key, config)


def test_a_missing_or_unreadable_models_file_is_a_named_error(tmp_path: Path) -> None:
    with pytest.raises(ReaderModelError):
        load_reader_model(tmp_path)
    (tmp_path / "models.toml").write_text(
        'pace_fraction = 0.8\n[models.a]\nmodel_id = "x"\nroute = "local"\nnum_ctx = 1\n'
        'requests_per_minute = 1\nrole = "development"\n'
        "[models.a.prices]\ninput = 0\noutput = 0\ncache_read = 0\ncache_write_5m = 0\n",
        encoding="utf-8",
    )
    with pytest.raises(ReaderModelError):  # a valid file with no reader model
        load_reader_model(tmp_path)


# --- the entry's own rules ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "changes",
    [{"route": "anthropic"}, {"max_tokens": None}, {"max_tokens": 0}],
)
def test_a_reader_entry_needs_the_openrouter_route_and_a_max_tokens(
    changes: dict[str, object],
) -> None:
    entry = {k: v for k, v in _entry(**changes).items() if v is not None}
    with pytest.raises(ValidationError):
        ModelsFile.model_validate(_file(x=entry))


def test_max_tokens_is_refused_on_any_other_role() -> None:
    with pytest.raises(ValidationError, match="extraction or reader model"):
        ModelConfig.model_validate(_entry(role="main"))


def test_at_most_one_reader_model() -> None:
    with pytest.raises(ValidationError, match="at most one reader"):
        ModelsFile.model_validate(_file(a=_entry(), b=_entry()))


def test_the_reader_entry_is_kept_out_of_models_and_cannot_be_smuggled_in() -> None:
    parsed = ModelsFile.model_validate(_file(x=_entry()))
    assert "x" not in parsed.models and "x" in parsed.reader_models
    assert parsed.reader()[0] == "x" and not parsed.extraction_models
    with pytest.raises(ValidationError, match=r"not a models\.toml key"):
        ModelsFile.model_validate({**_file(), "reader_models": {"x": _entry()}})
    with pytest.raises(ValueError, match="no reader model"):
        ModelsFile.model_validate(_file()).reader()


# --- the tripwire, path by path ----------------------------------------------------------------------------


@pytest.mark.parametrize("name", EXPERIMENTS)
def test_no_experiment_can_see_the_reader(name: str) -> None:
    experiment = load_experiment(name)
    assert KEY not in experiment.models.models
    with pytest.raises(ExperimentError, match="unknown model"):
        experiment.model(KEY)


@pytest.mark.parametrize("official", [False, True])
@pytest.mark.parametrize("name", ["company", "placeholder"])
def test_it_cannot_be_planned_on_any_experiment_in_any_mode(name: str, official: bool) -> None:
    experiment = load_experiment(name)
    with pytest.raises(ExperimentError, match="unknown model"):
        build_plan(experiment, model_key=KEY, label="x", repeats=1, seed=1, official=official)


def test_it_cannot_run_a_thinking_sweep() -> None:
    experiment = load_experiment("placeholder")
    with pytest.raises(ExperimentError, match="unknown model"):
        check_thinking_plan(experiment, KEY, ["s1"], [], official=False)


@pytest.mark.parametrize("name", ["company", "placeholder"])
def test_it_cannot_be_probed(name: str) -> None:
    with pytest.raises(ExperimentError, match="unknown model"):
        check_probe_model(load_experiment(name), KEY)


def test_it_cannot_be_locked() -> None:
    with pytest.raises(LockError) as caught:
        build_lock(ROOT, [KEY])
    assert any(f"model {KEY!r} is not in" in reason for reason in caught.value.reasons)


def test_the_gate_refuses_it_as_not_one_of_the_locks_models() -> None:
    lock = read_lock(lock_path(ROOT))
    assert KEY not in lock.models
    plan = SimpleNamespace(model_key=KEY)
    failures = check_model(load_experiment("company"), plan, lock)  # type: ignore[arg-type]
    assert failures and "not one of" in failures[0]


@pytest.mark.parametrize("command", ["plan", "run"])
def test_the_command_line_refuses_it(command: str, capsys: pytest.CaptureFixture[str]) -> None:
    words = ["sweep", command, "--experiment", "placeholder", "--model", KEY, "--repeats", "1"]
    words += ["--seed", "1", "--label", "development"]
    try:
        code = main(words)
    except (SweepRefusal, ExperimentError) as exc:
        assert "unknown model" in str(exc)
    else:
        assert code == REFUSED_EXIT
        assert "unknown model" in capsys.readouterr().err


def test_the_real_file_parses_with_both_case_tool_entries_and_no_experiment_model_changed() -> None:
    raw = tomllib.loads((ROOT / "experiment" / "models.toml").read_text(encoding="utf-8"))
    parsed = ModelsFile.model_validate(raw)
    assert set(parsed.models) == {
        "sonnet-4-6",
        "nova-lite",
        "qwen-local",
        "gpt-oss-openrouter",
        "haiku-5-5",
    }
    assert set(parsed.extraction_models) == {"sonnet-5-5-extraction"}
    assert set(parsed.reader_models) == {KEY}
