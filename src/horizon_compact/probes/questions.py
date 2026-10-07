"""Probe questions, their answer keys, the probe prompt, the ``submit_answers`` tool and the scoring
(Phase 2.5 IMPLEMENTATION doc section 10).

A probe asks about facts and rules, never preferences. Its prompt is the decision prompt with the objective
sentence and the instruction taken out: the situation, then "Answer the following questions about the
situation. Do not make the decision.", then the menu and options in one fixed order, then the questions.
**No probe carries an objective**, so no answer can show which way an objective pushes, and the answers may
be read.

``experiment/<name>/probes/<scenario>.toml`` holds the questions. A numeric key is a **formula over the
rows** (``answer_formula``), evaluated on the values as the text shows them, so a figure corrected later
moves its key with it; ``key``, ``keys`` and ``yes_no`` questions give ``answer`` directly. Probe files are
not part of the instrument's content hash (section 4): a model reads them only in a probe.

Scoring is exact: a number within 1% of its key (exactly equal when the question is marked ``exact``, for
counts, years and stated percentages, or when the key is zero), a key equal, a set of keys
equal as a set, yes or no equal. A reply without a usable answer to a question scores that question wrong.
"""

from __future__ import annotations

import math
import re
import tomllib
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from horizon_compact.dossier.figures import (
    FigureError,
    FigureSet,
    evaluate_formula,
    formula_references,
)
from horizon_compact.experiment import Experiment, Scenario
from horizon_compact.providers.base import ToolSpec
from horizon_compact.sweep.prompt import situation_blocks

PROBES_DIR = "probes"
TOOL_NAME = "submit_answers"
TOOL_DESCRIPTION = "Submits the answers: one for every question, keyed by the question's id."
PROBE_INTRO = "Answer the following questions about the situation. Do not make the decision."
# The menu and options keep one fixed order in every probe (section 10).
PROBE_MENU_SEED = 1
NUMBER_TOLERANCE = 0.01
MIN_QUESTIONS, MAX_QUESTIONS = 8, 10
_QUESTION_ID = re.compile(r"q[0-9]+")

QuestionType = Literal["number", "key", "keys", "yes_no"]


class ProbeError(Exception):
    """A probe file is missing, unreadable or invalid. The message names the file and the question."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Question(_Strict):
    id: str
    type: QuestionType
    text: str
    # For key and keys: the keys the answer is chosen from (shown in the prompt and enforced by the tool).
    choices: list[str] = Field(default_factory=list)
    # For number: a formula over the figures' row ids. For the others: the answer itself.
    answer_formula: str | None = None
    answer: str | list[str] | None = None
    # For number: the answer must equal the key exactly (a count of people, a number of years, a stated
    # percentage). Without it, within 1%, which allows for money rounded as the text rounds it.
    exact: bool = False
    # Why the key is what it is, for anyone checking it by hand. Never shown to a model.
    note: str = ""

    @model_validator(mode="after")
    def _the_answer_fits_the_type(self) -> Question:
        if not _QUESTION_ID.fullmatch(self.id):
            raise ValueError(f"question id {self.id!r} must be q followed by digits")
        if self.type == "number":
            if self.answer_formula is None or self.answer is not None or self.choices:
                raise ValueError(f"{self.id}: a number question has answer_formula only")
            return self
        if self.exact:
            raise ValueError(f"{self.id}: only a number question can be exact")
        if self.answer_formula is not None:
            raise ValueError(f"{self.id}: only a number question has answer_formula")
        if self.type == "yes_no":
            if self.answer not in ("yes", "no") or self.choices:
                raise ValueError(f'{self.id}: a yes_no question\'s answer is "yes" or "no"')
            return self
        if len(self.choices) < 2 or len(set(self.choices)) != len(self.choices):
            raise ValueError(
                f"{self.id}: a {self.type} question needs two or more distinct choices"
            )
        if self.type == "key":
            if not isinstance(self.answer, str) or self.answer not in self.choices:
                raise ValueError(f"{self.id}: a key question's answer is one of its choices")
        else:
            if (
                not isinstance(self.answer, list)
                or not self.answer
                or len(set(self.answer)) != len(self.answer)
                or not set(self.answer) <= set(self.choices)
            ):
                raise ValueError(
                    f"{self.id}: a keys question's answer is a non-empty list of distinct choices"
                )
        return self


class ProbeFile(_Strict):
    scenario: str
    questions: list[Question] = Field(min_length=MIN_QUESTIONS, max_length=MAX_QUESTIONS)

    @model_validator(mode="after")
    def _ids_are_unique(self) -> ProbeFile:
        ids = [q.id for q in self.questions]
        if len(set(ids)) != len(ids):
            raise ValueError("question ids must be unique")
        return self


@dataclass(frozen=True)
class Key:
    """A question with its answer key resolved: a float for a number question, else the answer as written."""

    question: Question
    value: float | str | tuple[str, ...]


def probe_path(experiment: Experiment, scenario_id: str) -> Path:
    return experiment.root / experiment.name / PROBES_DIR / f"{scenario_id}.toml"


def load_probe_file(path: Path) -> ProbeFile:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ProbeError(f"cannot read {path}: {exc.strerror or exc}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ProbeError(f"{path.name} is not valid TOML: {exc}") from exc
    try:
        probe = ProbeFile.model_validate(data)
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(str(part) for part in err['loc']) or '(file)'}: {err['msg']}"
            for err in exc.errors()
        )
        raise ProbeError(f"{path.name} is invalid: {problems}") from exc
    if probe.scenario != path.stem:
        raise ProbeError(
            f"{path.name} is for scenario {probe.scenario!r}; the file name must match"
        )
    return probe


def resolve_keys(probe: ProbeFile, scenario: Scenario, fs: FigureSet) -> list[Key]:
    """Every question with its key. A choice must be a key the scenario has (a line, an option, or a choice
    the question itself defines as a distractor is refused: only real keys, so a key is never a trick)."""
    known = {lever.key for lever in scenario.levers}
    if scenario.choice is not None:
        known |= {option.key for option in scenario.choice.options}
    keys: list[Key] = []
    for question in probe.questions:
        where = f"probes/{probe.scenario}.toml {question.id}"
        unknown = sorted(set(question.choices) - known)
        if unknown:
            raise ProbeError(f"{where}: choices that are not keys of {scenario.id}: {unknown}")
        if question.type == "number":
            assert question.answer_formula is not None
            try:
                missing = sorted(formula_references(question.answer_formula) - fs.resolved.keys())
                if missing:
                    raise ProbeError(f"{where}: the answer uses rows that do not exist: {missing}")
                value = evaluate_formula(question.answer_formula, lambda ref: _number(fs, ref))
            except FigureError as exc:
                raise ProbeError(f"{where}: {exc}") from exc
            keys.append(Key(question, float(value)))
        elif question.type == "keys":
            assert isinstance(question.answer, list)
            keys.append(Key(question, tuple(sorted(question.answer))))
        else:
            assert isinstance(question.answer, str)
            keys.append(Key(question, question.answer))
    return keys


def _number(fs: FigureSet, ref: str) -> Decimal:
    value = fs.resolved[ref].value
    if isinstance(value, str):
        raise FigureError(f"{ref} is a label, not a number")
    return value


# --- the prompt and the tool --------------------------------------------------------------------------


def _question_line(question: Question) -> str:
    if question.type == "key":
        hint = f" (one of: {', '.join(question.choices)})"
    elif question.type == "keys":
        hint = f" (any of: {', '.join(question.choices)})"
    elif question.type == "yes_no":
        hint = " (yes or no)"
    else:
        hint = " (a number)"
    return f"- [{question.id}] {question.text.strip()}{hint}"


@dataclass(frozen=True)
class ProbePrompt:
    system: str
    user: str
    lever_order: tuple[str, ...]
    option_order: tuple[str, ...]


def render_probe(experiment: Experiment, scenario: Scenario, probe: ProbeFile) -> ProbePrompt:
    blocks = situation_blocks(experiment, scenario, PROBE_MENU_SEED)
    parts = [blocks.situation, PROBE_INTRO, blocks.menu]
    if blocks.options is not None:
        parts.append(blocks.options)
    parts.append("\n".join(["The questions:", *(_question_line(q) for q in probe.questions)]))
    parts.append(
        f"Call the {TOOL_NAME} tool exactly once, with an answer to every question, keyed by the "
        "question's id in brackets. A number is a plain number, with no dollar sign, commas or words."
    )
    return ProbePrompt(
        system=blocks.system,
        user="\n\n".join(parts),
        lever_order=blocks.lever_order,
        option_order=blocks.option_order,
    )


def build_probe_tool(probe: ProbeFile) -> ToolSpec:
    properties: dict[str, Any] = {}
    for question in sorted(probe.questions, key=lambda q: int(q.id[1:])):
        spec: dict[str, Any]
        if question.type == "number":
            spec = {"type": "number"}
        elif question.type == "yes_no":
            spec = {"type": "string", "enum": ["yes", "no"]}
        elif question.type == "key":
            spec = {"type": "string", "enum": sorted(question.choices)}
        else:
            spec = {
                "type": "array",
                "items": {"type": "string", "enum": sorted(question.choices)},
                "uniqueItems": True,
            }
        spec["description"] = f"The answer to question {question.id}."
        properties[question.id] = spec
    schema = {
        "type": "object",
        "properties": properties,
        "required": sorted(properties, key=lambda k: int(k[1:])),
        "additionalProperties": False,
    }
    return ToolSpec(name=TOOL_NAME, description=TOOL_DESCRIPTION, input_schema=schema)


# --- scoring ------------------------------------------------------------------------------------------


def _as_number(given: Any) -> float | None:
    if isinstance(given, bool):
        return None
    if isinstance(given, int | float):
        return float(given) if math.isfinite(given) else None
    if isinstance(given, str):  # a model that sends "125" or "$1,500" has still said a number
        cleaned = given.replace(",", "").replace("$", "").strip()
        try:
            value = float(cleaned)
        except ValueError:
            return None
        return value if math.isfinite(value) else None
    return None


def is_correct(key: Key, given: Any) -> bool:
    kind = key.question.type
    if kind == "number":
        number = _as_number(given)
        if number is None:
            return False
        assert isinstance(key.value, float)
        if key.value == 0 or key.question.exact:
            return number == key.value
        return abs(number - key.value) <= NUMBER_TOLERANCE * abs(key.value)
    if kind == "keys":
        if not isinstance(given, list) or not all(isinstance(item, str) for item in given):
            return False
        return tuple(sorted(set(given))) == key.value and len(set(given)) == len(given)
    if not isinstance(given, str):
        return False
    return given.strip().lower() == key.value if kind == "yes_no" else given.strip() == key.value


def score(keys: list[Key], answers: Any) -> dict[str, bool]:
    """Each question id, right or wrong. Anything that is not an object of answers scores every one wrong."""
    given = answers if isinstance(answers, dict) else {}
    return {
        key.question.id: (key.question.id in given and is_correct(key, given[key.question.id]))
        for key in keys
    }
