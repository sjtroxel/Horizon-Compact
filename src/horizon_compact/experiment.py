"""The experiment as versioned, hashed data (planning/05 section 3.1, Phase 1 IMPLEMENTATION doc section 6.1).

Everything an experiment says lives in TOML under ``experiment/``: ``models.toml`` (how each model is
reached, its quota and prices) and one folder per experiment: ``dossier.toml``, ``objectives.toml`` (the
objectives, the wording templates and, once drawn, the sealed template) and one file per scenario under
``scenarios/`` (Phase 2.5 IMPLEMENTATION doc sections 4, 5 and 8.1). Nothing here is hard-coded in the
harness. Every file is hashed by the SHA-256 of its bytes. The **content hash** covers the experiment's own
folder only, so a price or quota change in ``models.toml`` does not make an interrupted sweep unresumable;
``models.toml`` is hashed beside it and recorded as a file hash on every attempt.
"""

from __future__ import annotations

import hashlib
import os
import string
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from horizon_compact.model_config import ModelConfig, ModelsFile

EXPERIMENT_DIR_ENV = "HC_EXPERIMENT_DIR"
MODELS_FILE = "models.toml"
EXPERIMENT_FILES = ("dossier.toml", "objectives.toml")
SCENARIOS_DIR = "scenarios"
# A scenario as written (text with {row} placeholders); `hc scenarios render` turns it into the file the
# harness reads. The loader never reads it (Phase 2.5 IMPLEMENTATION doc section 4).
SOURCE_SUFFIX = ".source.toml"
# The placeholder: the walking skeleton's experiment, and the only one whose development records the analysis
# engine reads (analysis/records.py).
PLACEHOLDER_EXPERIMENT = "placeholder"
# The experiments that may run on any model, official ones included: they have none of the real content, and
# the placeholder rule's subject-vocabulary test covers every file in them (tests/test_sweep_prompt.py). The
# garden shapes measure each official candidate's format failures before the tag (Phase 3.5 decision 3).
OFF_SUBJECT_EXPERIMENTS = (PLACEHOLDER_EXPERIMENT, "shapes")
TEMPLATE_IDS = ("w1", "w2", "w3")
WORDING_FIELDS = ("who", "when", "wording")


class ExperimentError(Exception):
    """A file is missing, unreadable or invalid. The message names the file and the field."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Lever(_Strict):
    key: str
    label: str
    kind: Literal["source", "use", "not_offered"]
    cap: int = Field(ge=0)
    # For a lever not offered, the sentence the prompt shows after its label (the reason). Never used for
    # an offered lever.
    note: str = ""
    # The canonical lever (L1-L9, planning/07 section 3.1), for analysis. Never shown in a prompt.
    lever: str = ""
    # For an offered lever, optional text shown on the line below it and shuffled with it (Phase 2.5
    # IMPLEMENTATION doc section 17 step 8, item 7): a description that must not be first on every run.
    detail: str = ""

    @model_validator(mode="after")
    def _detail_is_for_an_offered_lever(self) -> Lever:
        if self.detail and self.kind == "not_offered":
            raise ValueError("detail is for an offered lever; a lever not offered has a note")
        return self


class Option(_Strict):
    key: str
    text: str


class Choice(_Strict):
    key: str
    label: str
    options: list[Option] = Field(min_length=2)


class JointCap(_Strict):
    """``key`` may not exceed ``fraction`` of what is left of ``base`` after ``against`` is removed, with
    ``against`` converted back at ``divisor`` (S2: a wage cut applies to the payroll that remains after roles
    are eliminated, and roles are counted at employment cost)."""

    kind: Literal["joint_cap"]
    key: str
    against: str
    base: float = Field(gt=0)
    divisor: float = Field(gt=0)
    fraction: float = Field(gt=0, le=1)


class OptionRequires(_Strict):
    """``key`` may be non-zero only when the choice is one of ``options``."""

    kind: Literal["option_requires"]
    key: str
    options: list[str] = Field(min_length=1)


class OptionFixes(_Strict):
    """``key`` equals ``amount`` when the choice is ``option`` and zero otherwise."""

    kind: Literal["option_fixes"]
    key: str
    option: str
    amount: float = Field(ge=0)


class NotBoth(_Strict):
    """Two lines that may not both be non-zero."""

    kind: Literal["not_both"]
    keys: list[str] = Field(min_length=2, max_length=2)


ExtraRule = Annotated[
    JointCap | OptionRequires | OptionFixes | NotBoth, Field(discriminator="kind")
]
BalanceRule = Literal[
    "sources_and_uses_equal_total",
    "uses_equal_total",
    "bearers_equal_total",
    "uses_equal_total_plus_sources",
    "split_equals_headcount",
]


class Scenario(_Strict):
    id: str
    role: str
    currency_note: str
    total: int = Field(gt=0)
    tolerance_fraction: float = Field(gt=0, lt=0.1)
    scenario: str
    menu_heading: str
    options_heading: str = ""
    instruction: str
    max_tokens: int = Field(gt=0)
    rule: BalanceRule
    unit: Literal["usd", "people"] = "usd"
    levers: list[Lever]
    choice: Choice | None = None
    rules: list[ExtraRule] = Field(default_factory=list)

    @model_validator(mode="after")
    def _levers_make_a_feasible_problem(self) -> Scenario:
        keys = [lever.key for lever in self.levers]
        if len(set(keys)) != len(keys):
            raise ValueError("lever keys must be unique")
        if self.choice is not None:
            if self.choice.key in keys:
                raise ValueError("the choice key must not be a lever key")
            option_keys = [option.key for option in self.choice.options]
            if len(set(option_keys)) != len(option_keys):
                raise ValueError("option keys must be unique")
            if not self.options_heading:
                raise ValueError("a scenario with a choice needs options_heading")
        elif self.options_heading:
            raise ValueError("options_heading is for a scenario with a choice")
        self._check_the_rule_fits_the_levers()
        self._check_the_extra_rules_name_real_keys()
        return self

    def _check_the_rule_fits_the_levers(self) -> None:
        sources = sum(lever.cap for lever in self.offered("source"))
        uses = sum(lever.cap for lever in self.offered("use"))
        has_sources, has_uses = bool(self.offered("source")), bool(self.offered("use"))
        if self.rule == "sources_and_uses_equal_total":
            if sources < self.total:
                raise ValueError("the sources' caps cannot reach the total")
            if uses < self.total:
                raise ValueError("the uses' caps cannot reach the total")
        elif self.rule in ("uses_equal_total", "uses_equal_total_plus_sources"):
            if has_sources and self.rule == "uses_equal_total":
                raise ValueError(f"{self.rule} takes uses only")
            if uses < self.total:
                raise ValueError("the uses' caps cannot reach the total")
        elif self.rule == "bearers_equal_total":
            if has_uses:
                raise ValueError("bearers_equal_total takes sources only")
            if sources < self.total:
                raise ValueError("the sources' caps cannot reach the total")
        else:  # split_equals_headcount
            if self.unit != "people":
                raise ValueError("split_equals_headcount counts people")
            if has_sources:
                raise ValueError("split_equals_headcount takes uses only")
            if uses < self.total:
                raise ValueError("the caps cannot reach the headcount")

    def _check_the_extra_rules_name_real_keys(self) -> None:
        offered = {lever.key for lever in self.offered()}
        options = {o.key for o in self.choice.options} if self.choice else set()
        for rule in self.rules:
            named = rule.keys if isinstance(rule, NotBoth) else [rule.key]
            if isinstance(rule, JointCap):
                named = [rule.key, rule.against]
            for key in named:
                if key not in offered:
                    raise ValueError(
                        f"rule {rule.kind} names {key!r}, which is not an offered line"
                    )
            if isinstance(rule, OptionRequires | OptionFixes):
                if self.choice is None:
                    raise ValueError(f"rule {rule.kind} needs a scenario with a choice")
                wanted = rule.options if isinstance(rule, OptionRequires) else [rule.option]
                for option in wanted:
                    if option not in options:
                        raise ValueError(
                            f"rule {rule.kind} names option {option!r}, which is not offered"
                        )

    def offered(self, kind: Literal["source", "use"] | None = None) -> list[Lever]:
        """The levers a decision must fill, in canonical (file) order. ``not_offered`` levers are never
        here."""
        return [
            lever
            for lever in self.levers
            if lever.kind != "not_offered" and (kind is None or lever.kind == kind)
        ]


class Objective(_Strict):
    """One objective. ``who`` and ``when`` fill a template's placeholders (the real experiment); ``wording``
    fills the placeholder's. The baseline has none of the three."""

    id: str
    who: str = ""
    when: str = ""
    wording: str = ""

    @property
    def is_baseline(self) -> bool:
        return not (self.who or self.when or self.wording)


class WordingTemplate(_Strict):
    """``stated`` is the objective sentence for an objective that has one, with ``{who}``, ``{when}`` or
    ``{wording}`` placeholders; ``none`` is the sentence for the baseline, and has no placeholder."""

    stated: str
    none: str


def _placeholders(text: str) -> set[str]:
    return {name for _lit, name, _spec, _conv in string.Formatter().parse(text) if name}


class ObjectivesFile(_Strict):
    # ``None`` (the key absent): this experiment has no sealed template (the placeholder). ``""``: it has
    # one that has not been drawn yet. Otherwise the drawn template's id (Phase 2.5 IMPLEMENTATION doc
    # section 13).
    sealed_template: str | None = None
    templates: dict[str, WordingTemplate] = Field(min_length=1)
    objectives: list[Objective] = Field(min_length=1)

    @model_validator(mode="after")
    def _the_file_is_consistent(self) -> ObjectivesFile:
        ids = [objective.id for objective in self.objectives]
        if len(set(ids)) != len(ids):
            raise ValueError("objective ids must be unique")
        for template_id, template in self.templates.items():
            if template_id not in TEMPLATE_IDS:
                raise ValueError(
                    f"template ids are {', '.join(TEMPLATE_IDS)}; found {template_id!r}"
                )
            unknown = _placeholders(template.stated) - set(WORDING_FIELDS)
            if unknown:
                raise ValueError(
                    f"template {template_id} has unknown placeholders {sorted(unknown)}"
                )
            if _placeholders(template.none):
                raise ValueError(f"template {template_id}'s `none` sentence takes no placeholder")
            for objective in self.objectives:
                if objective.is_baseline:
                    continue
                for name in _placeholders(template.stated):
                    if not getattr(objective, name):
                        raise ValueError(
                            f"objective {objective.id!r} has no {name!r}, which template {template_id} needs"
                        )
        if self.sealed_template and self.sealed_template not in self.templates:
            raise ValueError(
                f"sealed_template {self.sealed_template!r} is not one of the templates"
            )
        return self


class Dossier(_Strict):
    title: str
    text: str


@dataclass(frozen=True)
class Experiment:
    name: str
    scenarios: dict[str, Scenario]
    dossier: Dossier
    objectives: tuple[Objective, ...]
    templates: dict[str, WordingTemplate]
    sealed_template: str | None
    models: ModelsFile
    file_hashes: dict[str, str]
    content_hash: str
    root: Path

    @property
    def scenario(self) -> Scenario:
        """The one scenario, for an experiment that has exactly one (the placeholder). Several: name one."""
        if len(self.scenarios) != 1:
            raise ExperimentError(
                f"{self.name} has {len(self.scenarios)} scenarios; name one with get_scenario "
                f"({', '.join(self.scenarios)})"
            )
        return next(iter(self.scenarios.values()))

    def get_scenario(self, scenario_id: str) -> Scenario:
        try:
            return self.scenarios[scenario_id]
        except KeyError:
            raise ExperimentError(
                f"unknown scenario {scenario_id!r}; {self.name} has: {', '.join(self.scenarios)}"
            ) from None

    def wording_sentence(self, objective: Objective, template_id: str) -> str:
        """The objective's sentence under one template: the same position in every prompt (planning/07 4)."""
        try:
            template = self.templates[template_id]
        except KeyError:
            raise ExperimentError(
                f"unknown template {template_id!r}; {self.name} has: {', '.join(self.templates)}"
            ) from None
        if objective.is_baseline:
            return template.none
        sentence = template.stated
        for name in WORDING_FIELDS:
            sentence = sentence.replace("{" + name + "}", getattr(objective, name))
        return sentence

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


def _scenario_paths(folder: Path) -> list[Path]:
    paths = (
        sorted(
            path
            for path in (folder / SCENARIOS_DIR).glob("*.toml")
            if not path.name.endswith(SOURCE_SUFFIX)
        )
        if (folder / SCENARIOS_DIR).is_dir()
        else []
    )
    if not paths:
        raise ExperimentError(f"no scenarios: {folder / SCENARIOS_DIR} holds no .toml file")
    return paths


def load_experiment(name: str, root: Path | None = None) -> Experiment:
    """Load, validate and hash ``<root>/<name>/`` and ``<root>/models.toml``."""
    base = root or default_experiment_dir()
    folder = base / name
    if not folder.is_dir():
        raise ExperimentError(f"no experiment folder {folder}")
    raw = {filename: _read(folder / filename) for filename in EXPERIMENT_FILES}
    scenario_paths = _scenario_paths(folder)
    raw_scenarios = {f"{SCENARIOS_DIR}/{path.name}": _read(path) for path in scenario_paths}
    models_raw = _read(base / MODELS_FILE)

    scenarios: dict[str, Scenario] = {}
    for path in scenario_paths:
        scenario = _parse(Scenario, path, raw_scenarios[f"{SCENARIOS_DIR}/{path.name}"])
        if scenario.id != path.stem:
            raise ExperimentError(f"{path.name} has id {scenario.id!r}; the file name must match")
        scenarios[scenario.id] = scenario
    dossier = _parse(Dossier, folder / "dossier.toml", raw["dossier.toml"])
    objectives = _parse(ObjectivesFile, folder / "objectives.toml", raw["objectives.toml"])
    models = _parse(ModelsFile, base / MODELS_FILE, models_raw)

    content = {
        f"{name}/{filename}": sha256_bytes(data)
        for filename, data in {**raw, **raw_scenarios}.items()
    }
    return Experiment(
        name=name,
        scenarios=scenarios,
        dossier=dossier,
        objectives=tuple(objectives.objectives),
        templates=dict(objectives.templates),
        sealed_template=objectives.sealed_template,
        models=models,
        file_hashes={**content, MODELS_FILE: sha256_bytes(models_raw)},
        content_hash=combine_hashes(content),
        root=base,
    )
