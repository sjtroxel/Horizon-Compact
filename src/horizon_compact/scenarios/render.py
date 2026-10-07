"""``hc scenarios render``: each ``sN.source.toml`` becomes the ``sN.toml`` the harness reads, and the cited
public version is written beside the evidence (Phase 2.5 IMPLEMENTATION doc sections 4, 5 and 8.7).

A source is the scenario as written: every text field holds ``{row_id}`` placeholders and **no digit outside
one**, and every cap, total and rule number names a row. Rows come from ``figures.toml`` and
``scenario-figures.toml`` resolved as one set, so a scenario may cite a dossier row and a dossier correction
flows through. The rendered file carries the numbers; ``hc scenarios check`` re-renders and compares byte for
byte, so nobody edits an output by hand.
"""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from string import Formatter
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from horizon_compact.dossier.figures import (
    FIGURES_FILE,
    SOURCES_FILE,
    FigureError,
    FigureSet,
    format_value,
    parse_rows,
    parse_sources,
    resolve,
)
from horizon_compact.dossier.render import (
    COMPANY_DIR,
    TEMPLATE_PATH,
    labels,
    parse_template,
    source_line,
    sources_behind,
    table,
)
from horizon_compact.experiment import SOURCE_SUFFIX, BalanceRule, Scenario

SCENARIO_FIGURES_FILE = "scenario-figures.toml"
SCENARIOS_DIR = f"{COMPANY_DIR}/scenarios"
EVIDENCE_DIR = "docs/phases/evidence/phase-2.5"
CITED_PATH = f"{EVIDENCE_DIR}/scenarios-cited.md"

_ID = re.compile(r"[a-z][a-z0-9_]*")
_RENDERED_HEADER = (
    "# RENDERED by `hc scenarios render` from {source} and the figures. Do not edit by hand:\n"
    "# `hc scenarios check` fails if this file differs from a fresh render.\n\n"
)


class ScenarioSourceError(Exception):
    """A scenario source, or a figure it names, is invalid. The message names the file and the problem."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceLever(_Strict):
    key: str
    lever: str = ""
    label: str
    kind: Literal["source", "use", "not_offered"]
    cap: str | None = None  # a row id; a lever not offered has none (its cap renders as 0)
    note: str = ""
    detail: str = ""

    @model_validator(mode="after")
    def _cap_belongs_to_offered_levers(self) -> SourceLever:
        if self.kind == "not_offered" and self.cap is not None:
            raise ValueError(f"lever {self.key!r} is not offered, so it has no cap")
        if self.kind != "not_offered" and self.cap is None:
            raise ValueError(f"lever {self.key!r} is offered, so it needs a cap (a row id)")
        return self


class SourceOption(_Strict):
    key: str
    text: str


class SourceChoice(_Strict):
    key: str
    label: str
    options: list[SourceOption]


class SourceJointCap(_Strict):
    kind: Literal["joint_cap"]
    key: str
    against: str
    base: str
    divisor: str
    fraction: str


class SourceOptionRequires(_Strict):
    kind: Literal["option_requires"]
    key: str
    options: list[str]


class SourceOptionFixes(_Strict):
    kind: Literal["option_fixes"]
    key: str
    option: str
    amount: str


class SourceNotBoth(_Strict):
    kind: Literal["not_both"]
    keys: list[str]


SourceRule = Annotated[
    SourceJointCap | SourceOptionRequires | SourceOptionFixes | SourceNotBoth,
    Field(discriminator="kind"),
]
# The fields of a rule that are row ids in the source and numbers in the rendered file.
_RULE_ROW_FIELDS = ("base", "divisor", "fraction", "amount")


class ScenarioSource(_Strict):
    id: str
    role: str
    currency_note: str
    rule: BalanceRule
    unit: Literal["usd", "people"] = "usd"
    total: str
    tolerance_fraction: float
    max_tokens: int
    situation: str
    menu_heading: str
    options_heading: str = ""
    instruction: str
    levers: list[SourceLever]
    choice: SourceChoice | None = None
    rules: list[SourceRule] = Field(default_factory=list)


# --- reading ---------------------------------------------------------------------------------------------


def load_scenario_figures(root: Path) -> FigureSet:
    """``figures.toml`` and ``scenario-figures.toml`` resolved as one set. A scenario row may not reuse a
    dossier row's id (Phase 2.5 IMPLEMENTATION doc section 5)."""
    company = root / COMPANY_DIR
    sources = parse_sources(_read(company / SOURCES_FILE))
    dossier_rows = parse_rows(_read(company / FIGURES_FILE))
    scenario_rows = parse_rows(_read(company / SCENARIO_FIGURES_FILE))
    clash = sorted(dossier_rows.keys() & scenario_rows.keys())
    if clash:
        raise FigureError(
            f"{SCENARIO_FIGURES_FILE}: row ids that the dossier's {FIGURES_FILE} already uses: "
            f"{', '.join(clash)}"
        )
    return resolve({**dossier_rows, **scenario_rows}, sources)


def scenario_row_ids(root: Path) -> list[str]:
    """The ids in ``scenario-figures.toml``, in file order."""
    return list(parse_rows(_read(root / COMPANY_DIR / SCENARIO_FIGURES_FILE)))


def source_paths(root: Path) -> list[Path]:
    folder = root / SCENARIOS_DIR
    return sorted(folder.glob(f"*{SOURCE_SUFFIX}")) if folder.is_dir() else []


def parse_source(path: Path) -> ScenarioSource:
    text = _read(path)
    try:
        source = ScenarioSource.model_validate(tomllib.loads(text))
    except tomllib.TOMLDecodeError as exc:
        raise ScenarioSourceError(f"{path.name} is not valid TOML: {exc}") from exc
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(str(part) for part in err['loc']) or '(file)'}: {err['msg']}"
            for err in exc.errors()
        )
        raise ScenarioSourceError(f"{path.name} is invalid: {problems}") from exc
    expected = path.name.removesuffix(SOURCE_SUFFIX)
    if source.id != expected:
        raise ScenarioSourceError(f"{path.name} has id {source.id!r}; the file name must match")
    return source


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ScenarioSourceError(f"cannot read {path}: {exc.strerror or exc}") from exc


# --- filling ---------------------------------------------------------------------------------------------


@dataclass
class Filler:
    """Fills ``{row_id}`` placeholders from the resolved rows and records every row it touches. With
    ``refs`` (a label for each row) it writes the cited version: a bracketed label after each number."""

    fs: FigureSet
    refs: dict[str, str] | None = None
    used: set[str] = field(default_factory=set)

    def text(self, text: str, where: str) -> str:
        try:
            parsed = list(Formatter().parse(text))
        except ValueError as exc:
            raise ScenarioSourceError(f"{where}: {exc}") from exc
        parts: list[str] = []
        for literal, name, spec, conversion in parsed:
            for ch in literal:
                if ch.isnumeric():
                    raise ScenarioSourceError(
                        f"{where}: the text holds the digit {ch!r} outside a placeholder; "
                        "every number comes from a row"
                    )
            parts.append(literal)
            if name is None:
                continue
            if spec or conversion or not _ID.fullmatch(name):
                raise ScenarioSourceError(
                    f"{where}: {{{name}}} is not a plain {{row_id}} placeholder"
                )
            resolved = self.fs.resolved.get(name)
            if resolved is None:
                raise ScenarioSourceError(f"{where}: {{{name}}} is not a row in the figures")
            self.used.add(name)
            parts.append(resolved.shown)
            if self.refs is not None and resolved.row.unit != "label":
                parts.append(f" [{self.refs[name]}]")
        return "".join(parts).strip()

    def number(self, row_id: str, where: str) -> Decimal:
        resolved = self.fs.resolved.get(row_id)
        if resolved is None:
            raise ScenarioSourceError(f"{where}: {row_id!r} is not a row in the figures")
        if isinstance(resolved.value, str):
            raise ScenarioSourceError(f"{where}: {row_id!r} is a label, not a number")
        self.used.add(row_id)
        return resolved.value

    def whole(self, row_id: str, where: str) -> int:
        value = self.number(row_id, where)
        if value != value.to_integral_value():
            raise ScenarioSourceError(f"{where}: {row_id!r} is {value}, not a whole number")
        return int(value)


@dataclass(frozen=True)
class RenderedScenario:
    """One scenario with every row filled, as the ``Scenario`` model's data and as the cited version."""

    data: dict[str, Any]
    numbers: tuple[
        tuple[str, str, str], ...
    ]  # (where, row id, shown) for caps, total and rule numbers
    used: frozenset[str]


def fill_scenario(
    source: ScenarioSource, fs: FigureSet, refs: dict[str, str] | None
) -> RenderedScenario:
    f = Filler(fs, refs)
    sid = source.id
    numbers: list[tuple[str, str, str]] = []

    def counted(where: str, row_id: str) -> int:
        value = f.whole(row_id, f"{sid}.{where}")
        numbers.append((where, row_id, fs.resolved[row_id].shown))
        return value

    data: dict[str, Any] = {
        "id": sid,
        "role": f.text(source.role, f"{sid}.role"),
        "currency_note": f.text(source.currency_note, f"{sid}.currency_note"),
        "rule": source.rule,
        "unit": source.unit,
        "total": counted("total", source.total),
        "tolerance_fraction": source.tolerance_fraction,
        "max_tokens": source.max_tokens,
        "scenario": f.text(source.situation, f"{sid}.situation"),
        "menu_heading": f.text(source.menu_heading, f"{sid}.menu_heading"),
        "instruction": f.text(source.instruction, f"{sid}.instruction"),
    }
    if source.options_heading:
        data["options_heading"] = f.text(source.options_heading, f"{sid}.options_heading")
    levers: list[dict[str, Any]] = []
    for lever in source.levers:
        where = f"lever {lever.key}"
        item: dict[str, Any] = {"key": lever.key}
        if lever.lever:
            item["lever"] = lever.lever
        item["label"] = f.text(lever.label, f"{sid}.{where}.label")
        item["kind"] = lever.kind
        item["cap"] = counted(f"{where} cap", lever.cap) if lever.cap else 0
        if lever.note:
            item["note"] = f.text(lever.note, f"{sid}.{where}.note")
        if lever.detail:
            item["detail"] = f.text(lever.detail, f"{sid}.{where}.detail")
        levers.append(item)
    data["levers"] = levers
    if source.choice is not None:
        data["choice"] = {
            "key": source.choice.key,
            "label": f.text(source.choice.label, f"{sid}.choice.label"),
            "options": [
                {"key": o.key, "text": f.text(o.text, f"{sid}.option {o.key}")}
                for o in source.choice.options
            ],
        }
    rules: list[dict[str, Any]] = []
    for rule in source.rules:
        item = rule.model_dump()
        for name in _RULE_ROW_FIELDS:
            if name in item:
                where = f"rule {rule.kind} {name}"
                item[name] = float(f.number(item[name], f"{sid}.{where}"))
                numbers.append(
                    (where, rule.model_dump()[name], _shown(fs, rule.model_dump()[name]))
                )
        rules.append(item)
    if rules:
        data["rules"] = rules
    try:
        Scenario.model_validate(data)
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(str(part) for part in err['loc']) or '(file)'}: {err['msg']}"
            for err in exc.errors()
        )
        raise ScenarioSourceError(f"{sid}: the rendered scenario is invalid: {problems}") from exc
    return RenderedScenario(data=data, numbers=tuple(numbers), used=frozenset(f.used))


def _shown(fs: FigureSet, row_id: str) -> str:
    return fs.resolved[row_id].shown


# --- the rendered TOML -----------------------------------------------------------------------------------


def _string(text: str) -> str:
    """A TOML string: a literal block for text with line breaks, a basic string otherwise."""
    if "\n" not in text:
        return json.dumps(text, ensure_ascii=False)
    if "'''" in text:
        raise ScenarioSourceError("a text holds ''', which a TOML literal string cannot")
    return f"'''\n{text}'''"


def _value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        return _string(value)
    if isinstance(value, list):
        return "[" + ", ".join(_value(item) for item in value) + "]"
    raise TypeError(f"cannot write {type(value).__name__} as TOML")


def _pairs(item: dict[str, Any]) -> str:
    return "".join(f"{key} = {_value(value)}\n" for key, value in item.items())


def toml_text(data: dict[str, Any], source_name: str) -> str:
    """The rendered file. Scalars first, then the tables, in a fixed order so the bytes are reproducible."""
    scalars = {k: v for k, v in data.items() if k not in ("levers", "choice", "rules")}
    out = [_RENDERED_HEADER.format(source=source_name), _pairs(scalars)]
    for lever in data["levers"]:
        out.append(f"\n[[levers]]\n{_pairs(lever)}")
    choice = data.get("choice")
    if choice is not None:
        out.append(
            f"\n[choice]\nkey = {_value(choice['key'])}\nlabel = {_value(choice['label'])}\n"
        )
        for option in choice["options"]:
            out.append(f"\n[[choice.options]]\n{_pairs(option)}")
    for rule in data.get("rules", []):
        out.append(f"\n[[rules]]\n{_pairs(rule)}")
    return "".join(out)


# --- the cited version -----------------------------------------------------------------------------------


def scenario_labels(fs: FigureSet, dossier_ids: set[str], root: Path) -> dict[str, str]:
    """A reference label for every row. A dossier row keeps the label the cited dossier gives it; a scenario
    row's assumption number continues from the dossier's last (A32, ...) and its derived number from the
    dossier's last (D#), both in file order. A sourced row's label is its source's."""
    dossier_fs = FigureSet(
        sources=fs.sources,
        rows={k: v for k, v in fs.rows.items() if k in dossier_ids},
        resolved={k: v for k, v in fs.resolved.items() if k in dossier_ids},
        references={k: v for k, v in fs.references.items() if k in dossier_ids},
    )
    template = parse_template(_read(root / TEMPLATE_PATH))
    out = labels(dossier_fs, template)
    counts = {
        "assumption": sum(1 for r in dossier_fs.rows.values() if r.kind == "assumption"),
        "derived": sum(1 for r in dossier_fs.rows.values() if r.kind == "derived"),
    }
    for key, row in fs.rows.items():
        if key in dossier_ids:
            continue
        if row.kind == "sourced":
            assert row.source is not None
            out[key] = fs.sources[row.source].short
        else:
            counts[row.kind] += 1
            prefix = "assumption A" if row.kind == "assumption" else "derived D"
            out[key] = f"{prefix}{counts[row.kind]}"
    return out


def cited_markdown(
    rendered: list[RenderedScenario],
    cited: list[RenderedScenario],
    fs: FigureSet,
    scenario_ids: list[str],
    refs: dict[str, str],
    own_rows: list[str],
) -> str:
    """The public version: each scenario's text with a bracketed label after every number, the numbers that
    sit in caps, totals and rules, then the scenario rows' figures and assumptions and the sources."""
    parts = [
        "# The scenarios (cited version)\n\n"
        "The text of each scenario is as the model reads it, with a bracketed label after each number. A source "
        "name points to the list at the end; `assumption A#` rows are in the assumptions table below with "
        "their ranges and reasons, and `derived D#` rows are in the figures table with their formulas. "
        "Assumption and derived numbers continue from the dossier's (`dossier-cited.md`). The order of the "
        "lines and of the options is shuffled for each run; here they are in the file's order.\n"
    ]
    for item in cited:
        data = item.data
        parts.append(f"\n---\n\n## {data['id']}\n")
        parts.append(f"\n**Situation**\n\n{data['scenario']}\n")
        parts.append(f"\n**Menu heading**\n\n{data['menu_heading']}\n")
        parts.append("\n**Lines**\n")
        for lever in data["levers"]:
            line = f"- `{lever['key']}`: {lever['label']}"
            if lever["kind"] == "not_offered":
                line += f" (not offered: {lever.get('note', 'not offered')})"
            else:
                line += f" ({lever['kind']})"
            parts.append(line + "\n")
            if lever.get("detail"):
                parts.append(f"  - {lever['detail']}\n")
        choice = data.get("choice")
        if choice is not None:
            parts.append(f"\n**{data['options_heading']}**\n\n")
            parts.extend(f"- `{o['key']}`: {o['text']}\n" for o in choice["options"])
        parts.append(f"\n**Instruction**\n\n{data['instruction']}\n")
    # What sits outside the text: totals, caps and rule numbers, each with its row.
    rows: list[list[str]] = []
    for sid, item in zip(scenario_ids, rendered, strict=True):
        for where, row_id, shown in item.numbers:
            rows.append([sid, where, f"`{row_id}`", shown, refs[row_id]])
    parts.append(
        "\n---\n\n## Numbers outside the text\n\nThe total, each line's maximum and the numbers in the "
        "checking rules.\n\n" + table(["Scenario", "Where", "Row", "As shown", "Basis"], rows)
    )
    parts.append("\n## Figures\n\n" + _figures_table(fs, own_rows, refs))
    parts.append("\n## Assumptions\n\n" + _assumptions_table(fs, own_rows, refs))
    parts.append("\n## Sources\n\n" + _sources_list(fs, own_rows) + "\n")
    return "".join(parts)


def _figures_table(fs: FigureSet, ids: list[str], refs: dict[str, str]) -> str:
    rows: list[list[str]] = []
    for key in ids:
        row, resolved = fs.rows[key], fs.resolved[key]
        if row.kind == "sourced":
            assert row.source is not None
            read = f"{row.value:,}" if isinstance(row.value, int) else row.value
            basis = f"{fs.sources[row.source].short}: {row.locator}; read as {read}"
        elif row.kind == "assumption":
            basis = f"{refs[key]}: see the assumptions table"
        else:
            basis = f"{refs[key]}: {row.formula}"
        if row.note:
            basis += f". Note: {row.note}"
        rows.append([f"`{key}`", row.label, resolved.shown, row.kind, basis])
    return (
        "Every row behind the scenarios. `As shown` is the value after rounding, which is the value later "
        "formulas use.\n\n" + table(["ID", "Figure", "As shown", "Kind", "Basis"], rows)
    )


def _assumptions_table(fs: FigureSet, ids: list[str], refs: dict[str, str]) -> str:
    rows: list[list[str]] = []
    for key in ids:
        row, resolved = fs.rows[key], fs.resolved[key]
        assumption = row.assumption
        if assumption is None:
            continue
        if assumption.low is None or assumption.high is None:
            span = "none (a name, not a quantity)"
        else:
            low = format_value(row.unit, Decimal(str(assumption.low)))
            high = format_value(row.unit, Decimal(str(assumption.high)))
            span = f"{low} to {high}"
        where = assumption.range_from
        if assumption.range_sources:
            shorts = ", ".join(fs.sources[name].short for name in assumption.range_sources)
            where += f" (sources: {shorts})"
        rows.append(
            [
                refs[key].removeprefix("assumption "),
                f"{row.label} (`{key}`)",
                resolved.shown,
                span,
                where,
                assumption.reason,
                assumption.review or "",
            ]
        )
    return table(
        [
            "ID",
            "Figure",
            "Value",
            "Range",
            "Where the range comes from",
            "Why this point",
            "His review",
        ],
        rows,
    )


def _sources_list(fs: FigureSet, ids: list[str]) -> str:
    used: dict[str, None] = {}
    for key in ids:
        row = fs.rows[key]
        for dependency in sources_behind(fs, key):
            used.setdefault(dependency)
        if row.source:
            used.setdefault(row.source)
        if row.assumption and row.assumption.range_sources:
            for name in row.assumption.range_sources:
                used.setdefault(name)
    return "\n".join(source_line(fs.sources[name]) for name in used)


# --- everything ------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Outputs:
    files: dict[str, str]  # path relative to the repository root -> content
    used: frozenset[str]  # every row a text, cap, total, rule number or formula touches


def render_all(root: Path) -> Outputs:
    """Every rendered file. Raises ``FigureError`` or ``ScenarioSourceError`` on the first problem."""
    fs = load_scenario_figures(root)
    paths = source_paths(root)
    if not paths:
        raise ScenarioSourceError(f"{SCENARIOS_DIR} holds no {SOURCE_SUFFIX} file")
    sources = [parse_source(path) for path in paths]
    dossier_ids = set(parse_rows(_read(root / COMPANY_DIR / FIGURES_FILE)))
    refs = scenario_labels(fs, dossier_ids, root)

    plain = [fill_scenario(source, fs, None) for source in sources]
    cited = [fill_scenario(source, fs, refs) for source in sources]
    files: dict[str, str] = {}
    for source, item in zip(sources, plain, strict=True):
        files[f"{SCENARIOS_DIR}/{source.id}.toml"] = toml_text(
            item.data, f"{source.id}{SOURCE_SUFFIX}"
        )
    scenario_ids = [source.id for source in sources]
    scenario_only = [k for k in fs.rows if k not in dossier_ids]
    files[CITED_PATH] = cited_markdown(plain, cited, fs, scenario_ids, refs, scenario_only)

    used: set[str] = set()
    for item in plain:
        used |= item.used
    return Outputs(files=files, used=frozenset(_with_formula_inputs(used, fs)))


def _with_formula_inputs(used: set[str], fs: FigureSet) -> set[str]:
    """Rows used directly, plus every row a used row's formula reads, however deep."""
    found: set[str] = set()
    pending = list(used)
    while pending:
        key = pending.pop()
        if key in found:
            continue
        found.add(key)
        pending.extend(fs.references.get(key, ()))
    return found
