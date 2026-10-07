"""The experiment loads, validates and hashes (Phase 1 IMPLEMENTATION doc section 13, "experiment")."""

from __future__ import annotations

from pathlib import Path

import pytest

from horizon_compact.experiment import ExperimentError, load_experiment
from sweep_helpers import company_like, copy_experiment


def test_the_placeholder_loads_with_its_five_objectives_and_eight_levers() -> None:
    exp = load_experiment("placeholder")
    assert len(exp.objectives) == 5
    assert len(exp.scenario.levers) == 8
    assert [lever.key for lever in exp.scenario.offered()] == [
        "yearly_fund",
        "plant_sale",
        "raffle",
        "bulbs",
        "herbs",
        "irrigation",
        "mulch_compost",
    ]
    assert exp.model("sonnet-4-6").requests_per_minute == 10


def test_hashes_are_stable_across_loads() -> None:
    first, second = load_experiment("placeholder"), load_experiment("placeholder")
    assert first.content_hash == second.content_hash
    assert first.file_hashes == second.file_hashes
    assert set(first.file_hashes) == {
        "placeholder/dossier.toml",
        "placeholder/scenarios/garden.toml",
        "placeholder/objectives.toml",
        "models.toml",
    }


def test_one_changed_byte_changes_the_file_hash_and_the_content_hash(tmp_path: Path) -> None:
    root = copy_experiment(tmp_path)
    before = load_experiment("placeholder", root)
    path = root / "placeholder" / "objectives.toml"
    path.write_bytes(path.read_bytes() + b" ")
    after = load_experiment("placeholder", root)
    assert (
        after.file_hashes["placeholder/objectives.toml"]
        != before.file_hashes["placeholder/objectives.toml"]
    )
    assert after.content_hash != before.content_hash


def test_a_price_change_does_not_change_the_content_hash(tmp_path: Path) -> None:
    """models.toml is config: a quota or price edit must not make an interrupted sweep unresumable."""
    root = copy_experiment(tmp_path)
    before = load_experiment("placeholder", root)
    models = root / "models.toml"
    models.write_text(
        models.read_text().replace("requests_per_minute = 20", "requests_per_minute = 30")
    )
    after = load_experiment("placeholder", root)
    assert after.content_hash == before.content_hash
    assert after.file_hashes["models.toml"] != before.file_hashes["models.toml"]


def test_a_missing_field_is_an_error_naming_the_file_and_the_field(tmp_path: Path) -> None:
    root = copy_experiment(tmp_path)
    path = root / "placeholder" / "scenarios" / "garden.toml"
    path.write_text(path.read_text().replace('id = "garden"\n', ""))
    with pytest.raises(ExperimentError, match=r"garden\.toml.*id"):
        load_experiment("placeholder", root)


def test_malformed_toml_is_an_error_naming_the_file(tmp_path: Path) -> None:
    root = copy_experiment(tmp_path)
    (root / "placeholder" / "dossier.toml").write_text("title = ")
    with pytest.raises(ExperimentError, match=r"dossier\.toml is not valid TOML"):
        load_experiment("placeholder", root)


def test_an_unknown_model_names_the_known_ones() -> None:
    with pytest.raises(ExperimentError, match="nova-lite"):
        load_experiment("placeholder").model("nope")


def test_a_missing_folder_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(ExperimentError, match="no experiment folder"):
        load_experiment("nope", copy_experiment(tmp_path))


def test_caps_that_cannot_reach_the_total_are_rejected(tmp_path: Path) -> None:
    root = copy_experiment(tmp_path)
    path = root / "placeholder" / "scenarios" / "garden.toml"
    path.write_text(path.read_text().replace("cap = 1000", "cap = 10"))
    with pytest.raises(ExperimentError, match="sources' caps cannot reach the total"):
        load_experiment("placeholder", root)


def test_an_application_profile_route_needs_its_profile_name(tmp_path: Path) -> None:
    root = copy_experiment(tmp_path)
    models = root / "models.toml"
    models.write_text(
        models.read_text().replace('inference_profile = "horizon-compact-sonnet-4-6"\n', "")
    )
    with pytest.raises(ExperimentError, match="needs inference_profile"):
        load_experiment("placeholder", root)


# --- Phase 2.5: several scenarios, templates and the sealed template ------------------------------


def test_a_folder_with_two_scenarios_loads_both_and_the_single_scenario_shortcut_refuses_to_guess(
    tmp_path: Path,
) -> None:
    exp = company_like(tmp_path, sealed="")
    assert list(exp.scenarios) == ["s1", "s2"]
    assert exp.get_scenario("s2").id == "s2"
    with pytest.raises(
        ExperimentError, match=r"has 2 scenarios; name one with get_scenario \(s1, s2\)"
    ):
        _ = exp.scenario
    with pytest.raises(ExperimentError, match="unknown scenario 'nope'; company has: s1, s2"):
        exp.get_scenario("nope")


def test_a_scenario_file_whose_id_differs_from_its_name_is_refused(tmp_path: Path) -> None:
    root = copy_experiment(tmp_path)
    path = root / "placeholder" / "scenarios" / "garden.toml"
    path.rename(path.with_name("lawn.toml"))
    with pytest.raises(
        ExperimentError, match=r"lawn\.toml has id 'garden'; the file name must match"
    ):
        load_experiment("placeholder", root)


def test_a_folder_with_no_scenarios_is_refused(tmp_path: Path) -> None:
    root = copy_experiment(tmp_path)
    (root / "placeholder" / "scenarios" / "garden.toml").unlink()
    with pytest.raises(ExperimentError, match="no scenarios"):
        load_experiment("placeholder", root)


def test_every_scenario_file_is_in_the_content_hash(tmp_path: Path) -> None:
    exp = company_like(tmp_path, sealed="")
    assert {"company/scenarios/s1.toml", "company/scenarios/s2.toml"} <= set(exp.file_hashes)
    path = exp.root / "company" / "scenarios" / "s2.toml"
    path.write_text(path.read_text() + "\n# a changed byte\n")
    assert load_experiment("company", exp.root).content_hash != exp.content_hash


def test_the_objective_sentence_comes_from_the_template_and_the_baseline_has_its_own(
    tmp_path: Path,
) -> None:
    exp = company_like(tmp_path, sealed="")
    a, e = exp.objectives[0], exp.objectives[2]
    assert (
        exp.wording_sentence(a, "w1")
        == "The panel has set your aim: create value for members, over this year."
    )
    assert (
        exp.wording_sentence(a, "w3")
        == "Over this year, the panel's aim for you is to create value for members."
    )
    assert exp.wording_sentence(e, "w2") == "The panel has not asked you to pursue an aim."
    with pytest.raises(ExperimentError, match="unknown template 'w9'"):
        exp.wording_sentence(a, "w9")


def _objectives_text(tmp_path: Path) -> tuple[Path, str]:
    exp = company_like(tmp_path, sealed="")
    path = exp.root / "company" / "objectives.toml"
    return exp.root, path.read_text()


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("{when}", "{wen}", "unknown placeholders"),
        ("The panel has set no aim.", "The panel has set {who}.", "takes no placeholder"),
        ("[templates.w3]", "[templates.w4]", "template ids are w1, w2, w3; found 'w4'"),
        (
            'sealed_template = ""',
            'sealed_template = "w7"',
            "sealed_template 'w7' is not one of the templates",
        ),
        ('who = "members"\nwhen = "this year"', 'who = "members"', "has no 'when'"),
        ('id = "B"', 'id = "A"', "objective ids must be unique"),
    ],
)
def test_an_inconsistent_objectives_file_is_refused(
    tmp_path: Path, old: str, new: str, message: str
) -> None:
    root, text = _objectives_text(tmp_path)
    assert old in text
    (root / "company" / "objectives.toml").write_text(text.replace(old, new, 1))
    with pytest.raises(ExperimentError, match=message):
        load_experiment("company", root)


def test_the_sealed_template_is_none_when_the_key_is_absent_and_empty_when_undrawn(
    tmp_path: Path,
) -> None:
    assert load_experiment("placeholder").sealed_template is None
    assert company_like(tmp_path / "a", sealed="").sealed_template == ""
    assert company_like(tmp_path / "b", sealed="w2").sealed_template == "w2"


# --- Phase 2.5 step 4: the local route ------------------------------------------------------------


def test_a_local_route_needs_its_context_window(tmp_path: Path) -> None:
    root = copy_experiment(tmp_path)
    models = root / "models.toml"
    models.write_text(models.read_text().replace("num_ctx = 16384\n", ""))
    with pytest.raises(ExperimentError, match="a local route needs num_ctx"):
        load_experiment("placeholder", root)


def test_a_context_window_on_a_route_that_is_not_local_is_refused(tmp_path: Path) -> None:
    root = copy_experiment(tmp_path)
    models = root / "models.toml"
    models.write_text(
        models.read_text().replace(
            'route = "in_region"\n', 'route = "in_region"\nnum_ctx = 4096\n', 1
        )
    )
    with pytest.raises(ExperimentError, match="num_ctx is for a local route"):
        load_experiment("placeholder", root)


def test_the_local_model_is_a_development_model_with_zero_prices() -> None:
    config = load_experiment("placeholder").model("qwen-local")
    assert (config.model_id, config.route, config.role) == ("qwen3.5:4b", "local", "development")
    assert (config.num_ctx, config.requests_per_minute) == (16384, 30)
    assert config.prices.input == config.prices.output == 0.0
