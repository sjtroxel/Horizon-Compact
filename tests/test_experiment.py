"""The experiment loads, validates and hashes (Phase 1 IMPLEMENTATION doc section 13, "experiment")."""

from __future__ import annotations

from pathlib import Path

import pytest

from horizon_compact.experiment import ExperimentError, load_experiment
from sweep_helpers import copy_experiment


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
        "placeholder/scenario.toml",
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
    path = root / "placeholder" / "scenario.toml"
    path.write_text(path.read_text().replace('id = "garden"\n', ""))
    with pytest.raises(ExperimentError, match=r"scenario\.toml.*id"):
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
    path = root / "placeholder" / "scenario.toml"
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
