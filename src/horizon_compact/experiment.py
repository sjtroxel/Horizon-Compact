"""The experiment as versioned, hashed data (planning/05 section 3.1, Phase 1 IMPLEMENTATION doc section 6.1).

Everything an experiment says lives in TOML under ``experiment/``: ``models.toml`` (how each model is reached,
its quota and prices) and one folder per experiment (``dossier.toml``, ``scenario.toml``,
``objectives.toml``). Nothing here is hard-coded in the harness. Every file is hashed by the SHA-256 of its
bytes. The **content hash** covers the experiment's own folder only, so a price or quota change in
``models.toml`` does not make an interrupted sweep unresumable; ``models.toml`` is hashed beside it and
recorded as a file hash on every attempt.
"""

from __future__ import annotations

import hashlib
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

EXPERIMENT_DIR_ENV = "HC_EXPERIMENT_DIR"
MODELS_FILE = "models.toml"
EXPERIMENT_FILES = ("dossier.toml", "scenario.toml", "objectives.toml")


class ExperimentError(Exception):
    """A file is missing, unreadable or invalid. The message names the file and the field."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Lever(_Strict):
    key: str
    label: str
    kind: Literal["source", "use", "not_offered"]
    cap: int = Field(ge=0)


class Option(_Strict):
    key: str
    text: str


class Choice(_Strict):
    key: str
    label: str
    options: list[Option] = Field(min_length=2)


class Scenario(_Strict):
    id: str
    role: str
    currency_note: str
    total: int = Field(gt=0)
    tolerance_fraction: float = Field(gt=0, lt=0.1)
    scenario: str
    priority_frame: str
    no_priority: str
    menu_heading: str
    options_heading: str
    instruction: str
    max_tokens: int = Field(gt=0)
    levers: list[Lever]
    choice: Choice

    @model_validator(mode="after")
    def _levers_make_a_feasible_problem(self) -> Scenario:
        keys = [lever.key for lever in self.levers]
        if len(set(keys)) != len(keys):
            raise ValueError("lever keys must be unique")
        if self.choice.key in keys:
            raise ValueError("the choice key must not be a lever key")
        option_keys = [option.key for option in self.choice.options]
        if len(set(option_keys)) != len(option_keys):
            raise ValueError("option keys must be unique")
        if sum(lever.cap for lever in self.offered("source")) < self.total:
            raise ValueError("the sources' caps cannot reach the total")
        if sum(lever.cap for lever in self.offered("use")) < self.total:
            raise ValueError("the uses' caps cannot reach the total")
        return self

    def offered(self, kind: Literal["source", "use"] | None = None) -> list[Lever]:
        """The levers a decision must fill, in canonical (file) order. ``not_offered`` levers are never
        here."""
        return [
            lever
            for lever in self.levers
            if lever.kind != "not_offered" and (kind is None or lever.kind == kind)
        ]


class Objective(_Strict):
    id: str
    wording: str


class ObjectivesFile(_Strict):
    objectives: list[Objective] = Field(min_length=1)

    @model_validator(mode="after")
    def _ids_are_unique(self) -> ObjectivesFile:
        ids = [objective.id for objective in self.objectives]
        if len(set(ids)) != len(ids):
            raise ValueError("objective ids must be unique")
        return self


class Dossier(_Strict):
    title: str
    text: str


class Prices(_Strict):
    """USD per million tokens."""

    input: float = Field(ge=0)
    output: float = Field(ge=0)
    cache_read: float = Field(ge=0)
    cache_write_5m: float = Field(ge=0)


class ModelConfig(_Strict):
    model_id: str
    route: Literal["in_region", "geo_profile", "application_profile"]
    role: str
    requests_per_minute: int = Field(gt=0)
    prices: Prices
    inference_profile: str | None = None
    geo_profile_id: str | None = None

    @model_validator(mode="after")
    def _route_has_what_it_needs(self) -> ModelConfig:
        if self.route == "application_profile" and not self.inference_profile:
            raise ValueError("an application_profile route needs inference_profile")
        if self.route == "geo_profile" and not self.geo_profile_id:
            raise ValueError("a geo_profile route needs geo_profile_id")
        return self


class ModelsFile(_Strict):
    pace_fraction: float = Field(gt=0, le=1)
    models: dict[str, ModelConfig]


@dataclass(frozen=True)
class Experiment:
    name: str
    scenario: Scenario
    dossier: Dossier
    objectives: tuple[Objective, ...]
    models: ModelsFile
    file_hashes: dict[str, str]
    content_hash: str
    root: Path

    def model(self, key: str) -> ModelConfig:
        try:
            return self.models.models[key]
        except KeyError:
            known = ", ".join(sorted(self.models.models))
            raise ExperimentError(f"unknown model {key!r}; {MODELS_FILE} has: {known}") from None


def default_experiment_dir() -> Path:
    override = os.environ.get(EXPERIMENT_DIR_ENV)
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "experiment"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def combine_hashes(file_hashes: dict[str, str]) -> str:
    """SHA-256 over the sorted ``path:hash`` lines, so the order files were read in cannot matter."""
    lines = "".join(f"{path}:{digest}\n" for path, digest in sorted(file_hashes.items()))
    return sha256_bytes(lines.encode("utf-8"))


def _read(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ExperimentError(f"cannot read {path}: {exc.strerror or exc}") from exc


def _parse[T: BaseModel](model: type[T], path: Path, data: bytes) -> T:
    try:
        return model.model_validate(tomllib.loads(data.decode("utf-8")))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise ExperimentError(f"{path.name} is not valid TOML: {exc}") from exc
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(str(part) for part in err['loc']) or '(file)'}: {err['msg']}"
            for err in exc.errors()
        )
        raise ExperimentError(f"{path.name} is invalid: {problems}") from exc


def load_experiment(name: str, root: Path | None = None) -> Experiment:
    """Load, validate and hash ``<root>/<name>/`` and ``<root>/models.toml``."""
    base = root or default_experiment_dir()
    folder = base / name
    if not folder.is_dir():
        raise ExperimentError(f"no experiment folder {folder}")
    raw = {filename: _read(folder / filename) for filename in EXPERIMENT_FILES}
    models_raw = _read(base / MODELS_FILE)

    scenario = _parse(Scenario, folder / "scenario.toml", raw["scenario.toml"])
    dossier = _parse(Dossier, folder / "dossier.toml", raw["dossier.toml"])
    objectives = _parse(ObjectivesFile, folder / "objectives.toml", raw["objectives.toml"])
    models = _parse(ModelsFile, base / MODELS_FILE, models_raw)

    content = {f"{name}/{filename}": sha256_bytes(data) for filename, data in raw.items()}
    return Experiment(
        name=name,
        scenario=scenario,
        dossier=dossier,
        objectives=tuple(objectives.objectives),
        models=models,
        file_hashes={**content, MODELS_FILE: sha256_bytes(models_raw)},
        content_hash=combine_hashes(content),
        root=base,
    )
