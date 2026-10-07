"""The Company's figures: the data model, formula evaluation, rounding and formatting (Phase 2 IMPLEMENTATION
doc sections 5 and 6).

Every number in the dossier is a row in ``experiment/company/figures.toml``. A row is exactly one of three
kinds: **sourced** (a value read from a source in ``sources.toml``), an **assumption** (a chosen value with
its range and reason) or **derived** (a formula over other rows). Formulas are parsed with ``ast`` and
evaluated by a small walker, never ``eval``; arithmetic is ``Decimal`` so a number renders the same on every
machine.

Rounding is one rule with no exceptions: a row's value is rounded half up to its step (an explicit ``round``
or the unit's default) when it is resolved, and a formula downstream and the text both see the rounded value.
The page's numbers therefore agree with each other.
"""

from __future__ import annotations

import ast
import datetime
import re
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, DivisionByZero, InvalidOperation
from pathlib import Path
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    StrictFloat,
    StrictInt,
    StrictStr,
    ValidationError,
    model_validator,
)

Unit = Literal["usd", "usd_m", "pct", "count", "years", "ratio", "label"]
Kind = Literal["sourced", "assumption", "derived"]

SOURCES_FILE = "sources.toml"
FIGURES_FILE = "figures.toml"
_ID = re.compile(r"[a-z][a-z0-9_]*")
_FORMULA_CHARS = re.compile(r"[A-Za-z0-9_+\-*/(). ]+")

# The default rounding step for each unit, in the unit's stored terms: usd in dollars, usd_m in dollars (shown
# in millions to one decimal, so a step of 100,000), pct as a fraction (shown as a percent to one decimal, so
# 0.001).
DEFAULT_STEP: dict[str, Decimal] = {
    "usd": Decimal(1),
    "usd_m": Decimal(100_000),
    "pct": Decimal("0.001"),
    "count": Decimal(1),
    "years": Decimal("0.1"),
    "ratio": Decimal("0.01"),
}


class FigureError(Exception):
    """A source or figure file is invalid. The message names the file, the row and the problem."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Source(_Strict):
    short: str
    publisher: str
    title: str
    edition: str
    released: datetime.date
    retrieved: datetime.date
    url: str
    file: str
    sha256: str
    archive_sha256: str | None = None
    population: str
    terms: str
    extract: str

    @model_validator(mode="after")
    def _hashes_are_sha256(self) -> Source:
        for name in ("sha256", "archive_sha256"):
            value = getattr(self, name)
            if value is not None and not re.fullmatch(r"[0-9a-f]{64}", value):
                raise ValueError(f"{name} must be 64 lowercase hex characters")
        return self


class SourcesFile(_Strict):
    sources: dict[str, Source]


# Strict, so a TOML boolean is refused instead of quietly becoming 1.
Number = StrictInt | StrictFloat


class Assumption(_Strict):
    """A chosen value with where its range comes from and why this point. For a ``label`` row (a name, not a
    quantity) there is no range: ``low`` and ``high`` are both absent. ``review`` is his line in the
    assumptions table, recorded here so the rendered table stays reproducible from the data."""

    low: Number | None = None
    high: Number | None = None
    range_from: str
    reason: str
    review: str | None = None
    # Sources the range (not the value) comes from, by id in sources.toml, checked like a row's ``source``:
    # a range read from a public series is cited, not only described in ``range_from`` (Phase 2.5
    # IMPLEMENTATION doc section 17 step 8, item 9).
    range_sources: list[str] | None = None


class FigureRow(_Strict):
    label: str
    unit: Unit
    value: Number | StrictStr | None = None
    source: str | None = None
    locator: str | None = None
    assumption: Assumption | None = None
    formula: str | None = None
    round: Number | None = None
    # Shown in the figures table only, never in the model's text: how a row was read or why a formula is built
    # the way it is (added in step 5, when derived rows needed their reasoning recorded somewhere).
    note: str | None = None

    @property
    def kind(self) -> Kind:
        if self.formula is not None:
            return "derived"
        return "sourced" if self.source is not None else "assumption"

    @model_validator(mode="after")
    def _exactly_one_kind(self) -> FigureRow:
        is_sourced = self.source is not None or self.locator is not None
        flags = [is_sourced, self.assumption is not None, self.formula is not None]
        if sum(flags) != 1:
            raise ValueError(
                "a row is exactly one of sourced (source + locator + value), an assumption "
                "(assumption + value) or derived (formula)"
            )
        if self.formula is not None:
            if self.value is not None:
                raise ValueError("a derived row has no value of its own")
            if self.unit == "label":
                raise ValueError("a derived row cannot be a label")
        else:
            if self.value is None:
                raise ValueError("this row needs a value")
            if is_sourced and (not self.source or not self.locator):
                raise ValueError("a sourced row needs both source and locator")
        if self.value is not None:
            self._check_value_type()
        if self.assumption is not None:
            self._check_assumption(self.assumption)
        return self

    def _check_value_type(self) -> None:
        value = self.value
        if self.unit == "label":
            if not isinstance(value, str) or not value:
                raise ValueError("a label row's value is a non-empty string")
            if self.round is not None:
                raise ValueError("a label row has no rounding")
        elif isinstance(value, str) or not _finite(value):
            raise ValueError(f"a {self.unit} row's value must be a finite number")

    def _check_assumption(self, assumption: Assumption) -> None:
        if not assumption.range_from.strip() or not assumption.reason.strip():
            raise ValueError("an assumption needs range_from and reason, both non-empty")
        if assumption.range_sources is not None and (
            not assumption.range_sources
            or len(set(assumption.range_sources)) != len(assumption.range_sources)
        ):
            raise ValueError("range_sources is a non-empty list of distinct sources")
        if self.unit == "label":
            if assumption.low is not None or assumption.high is not None:
                raise ValueError("a label assumption has no range: leave low and high out")
            return
        low, high = assumption.low, assumption.high
        if low is None or high is None:
            raise ValueError("an assumption needs both low and high")
        if not (_finite(low) and _finite(high)) or low > high:
            raise ValueError("an assumption's low and high must be finite, with low <= high")
        # A bound finer than the unit can show would print rounded in the assumptions table, so the range read
        # there would not be the range stored (a count range of 0.5 to 2 printed as 1 to 2).
        unit_step = DEFAULT_STEP[self.unit]
        for bound in (low, high):
            if Decimal(str(bound)) % unit_step != 0:
                raise ValueError(
                    f"an assumption's bound {bound} cannot be shown in {self.unit} "
                    f"(it must be a multiple of {unit_step})"
                )


class FiguresFile(_Strict):
    figures: dict[str, FigureRow]


def _finite(value: Number | None) -> bool:
    return value is not None and Decimal(str(value)).is_finite()


# --- formulas ---------------------------------------------------------------------------------------------


def _walk(node: ast.AST, lookup: Callable[[str], Decimal]) -> Decimal:
    if isinstance(node, ast.Expression):
        return _walk(node.body, lookup)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, int | float):
            raise FigureError(f"only numbers are allowed in a formula, not {node.value!r}")
        return Decimal(str(node.value))
    if isinstance(node, ast.Name):
        return lookup(node.id)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.UAdd | ast.USub):
        operand = _walk(node.operand, lookup)
        return operand if isinstance(node.op, ast.UAdd) else -operand
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add | ast.Sub | ast.Mult | ast.Div):
        left, right = _walk(node.left, lookup), _walk(node.right, lookup)
        try:
            match node.op:
                case ast.Add():
                    return left + right
                case ast.Sub():
                    return left - right
                case ast.Mult():
                    return left * right
                case _:
                    return left / right
        except (DivisionByZero, InvalidOperation):
            raise FigureError("a formula divides by zero") from None
    raise FigureError(
        f"only + - * / and parentheses are allowed in a formula ({type(node).__name__})"
    )


def _parse_formula(expression: str) -> ast.Expression:
    if not _FORMULA_CHARS.fullmatch(expression):
        bad = sorted({ch for ch in expression if not _FORMULA_CHARS.fullmatch(ch)})
        raise FigureError(
            f"a formula may hold only row ids, numbers, + - * / and parentheses: {bad}"
        )
    try:
        return ast.parse(expression.strip(), mode="eval")
    except SyntaxError as exc:
        raise FigureError(f"not a formula: {exc.msg}") from None


def _names(node: ast.AST, seen: set[str]) -> None:
    """Validate a formula's structure and collect its names, with no arithmetic (a dry run that evaluated
    would divide by zero on a valid formula such as ``x / (1 - r)``)."""
    if isinstance(node, ast.Expression):
        _names(node.body, seen)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, int | float):
            raise FigureError(f"only numbers are allowed in a formula, not {node.value!r}")
    elif isinstance(node, ast.Name):
        seen.add(node.id)
    elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.UAdd | ast.USub):
        _names(node.operand, seen)
    elif isinstance(node, ast.BinOp) and isinstance(
        node.op, ast.Add | ast.Sub | ast.Mult | ast.Div
    ):
        _names(node.left, seen)
        _names(node.right, seen)
    else:
        raise FigureError(
            f"only + - * / and parentheses are allowed in a formula ({type(node).__name__})"
        )


def formula_references(expression: str) -> frozenset[str]:
    """The row ids a formula uses. Validates the whole formula (characters, syntax, allowed operations)."""
    seen: set[str] = set()
    _names(_parse_formula(expression), seen)
    return frozenset(seen)


def evaluate_formula(expression: str, lookup: Callable[[str], Decimal]) -> Decimal:
    return _walk(_parse_formula(expression), lookup)


# --- rounding and formatting ----------------------------------------------------------------------------


def step_for(row: FigureRow) -> Decimal | None:
    """The rounding step for a row: its explicit ``round``, which must be a multiple of the unit's default."""
    if row.unit == "label":
        return None
    default = DEFAULT_STEP[row.unit]
    if row.round is None:
        return default
    step = Decimal(str(row.round))
    if step <= 0 or step % default != 0:
        raise FigureError(
            f"round {row.round} must be a positive multiple of {default} ({row.unit})"
        )
    return step


def round_half_up(value: Decimal, step: Decimal) -> Decimal:
    return (value / step).to_integral_value(rounding=ROUND_HALF_UP) * step


def _quantize(value: Decimal, places: str) -> Decimal:
    return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)


def format_value(unit: str, value: Decimal | str) -> str:
    """How a resolved value reads in the text. count, years and ratio are bare numbers: the template says
    what they are."""
    if isinstance(value, str):
        return value
    sign = "-" if value < 0 else ""
    magnitude = abs(value)
    match unit:
        case "usd":
            return f"{sign}${format(_quantize(magnitude, '1'), ',f')}"
        case "usd_m":
            return (
                f"{sign}${format(_quantize(magnitude / Decimal(1_000_000), '0.1'), ',.1f')} million"
            )
        case "pct":
            return f"{sign}{format(_quantize(magnitude * 100, '0.1'), '.1f')}%"
        case "count":
            return f"{sign}{format(_quantize(magnitude, '1'), ',f')}"
        case "years":
            text = format(_quantize(magnitude, "0.1"), ".1f")
            return sign + text.removesuffix(".0")
        case "ratio":
            return f"{sign}{format(_quantize(magnitude, '0.01'), '.2f')}"
    raise FigureError(f"unknown unit {unit!r}")


# --- loading and resolving ------------------------------------------------------------------------------


@dataclass(frozen=True)
class Resolved:
    id: str
    row: FigureRow
    value: Decimal | str

    @property
    def shown(self) -> str:
        return format_value(self.row.unit, self.value)


@dataclass(frozen=True)
class FigureSet:
    sources: dict[str, Source]
    rows: dict[str, FigureRow]
    resolved: dict[str, Resolved]
    references: dict[str, frozenset[str]]  # derived row id -> the row ids its formula uses


def _parse[T: BaseModel](model: type[T], name: str, text: str) -> T:
    try:
        return model.model_validate(tomllib.loads(text))
    except tomllib.TOMLDecodeError as exc:
        raise FigureError(f"{name} is not valid TOML: {exc}") from exc
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(str(part) for part in err['loc']) or '(file)'}: {err['msg']}"
            for err in exc.errors()
        )
        raise FigureError(f"{name} is invalid: {problems}") from exc


def parse_sources(text: str) -> dict[str, Source]:
    sources = _parse(SourcesFile, SOURCES_FILE, text).sources
    for key in sources:
        if not _ID.fullmatch(key.replace("-", "_")):
            raise FigureError(
                f"{SOURCES_FILE}: source id {key!r} must be lowercase letters, digits, - and _"
            )
    shorts = [source.short for source in sources.values()]
    if len(set(shorts)) != len(shorts):
        raise FigureError(f"{SOURCES_FILE}: each source needs its own short label")
    return sources


def parse_rows(text: str) -> dict[str, FigureRow]:
    rows = _parse(FiguresFile, FIGURES_FILE, text).figures
    for key in rows:
        if not _ID.fullmatch(key):
            raise FigureError(
                f"{FIGURES_FILE}: row id {key!r} must be lowercase letters, digits and _"
            )
    return rows


def resolve(rows: dict[str, FigureRow], sources: dict[str, Source]) -> FigureSet:
    """Validate every cross-reference and compute every value. Raises ``FigureError`` on the first problem."""
    references: dict[str, frozenset[str]] = {}
    for key, row in rows.items():
        if row.source is not None and row.source not in sources:
            raise FigureError(f"{FIGURES_FILE}: {key}: unknown source {row.source!r}")
        if row.assumption is not None:
            for name in row.assumption.range_sources or ():
                if name not in sources:
                    raise FigureError(f"{FIGURES_FILE}: {key}: unknown range source {name!r}")
        if row.formula is not None:
            try:
                refs = formula_references(row.formula)
            except FigureError as exc:
                raise FigureError(f"{FIGURES_FILE}: {key}: {exc}") from None
            unknown = sorted(refs - rows.keys())
            if unknown:
                raise FigureError(
                    f"{FIGURES_FILE}: {key}: formula uses unknown row {', '.join(unknown)}"
                )
            references[key] = refs

    resolved: dict[str, Resolved] = {}
    visiting: list[str] = []

    def value_of(key: str) -> Decimal | str:
        if key in resolved:
            return resolved[key].value
        if key in visiting:
            cycle = " -> ".join([*visiting[visiting.index(key) :], key])
            raise FigureError(f"{FIGURES_FILE}: formulas form a cycle: {cycle}")
        visiting.append(key)
        row = rows[key]
        try:
            value: Decimal | str
            if row.formula is not None:
                value = _round(
                    row, evaluate_formula(row.formula, lambda ref: _number(ref, value_of(ref)))
                )
            elif isinstance(row.value, str):
                value = row.value
            else:
                value = _round(row, Decimal(str(row.value)))
            _check_in_range(row, value)
        except FigureError as exc:
            if str(exc).startswith(FIGURES_FILE):
                raise
            raise FigureError(f"{FIGURES_FILE}: {key}: {exc}") from None
        finally:
            visiting.pop()
        resolved[key] = Resolved(key, row, value)
        return value

    for key in rows:
        value_of(key)
    return FigureSet(sources=sources, rows=rows, resolved=resolved, references=references)


def _number(key: str, value: Decimal | str) -> Decimal:
    if isinstance(value, str):
        raise FigureError(f"{key} is a label, not a number, so a formula cannot use it")
    return value


def _round(row: FigureRow, value: Decimal) -> Decimal:
    step = step_for(row)
    return value if step is None else round_half_up(value, step)


def _check_in_range(row: FigureRow, value: Decimal | str) -> None:
    assumption = row.assumption
    if assumption is None or assumption.low is None or assumption.high is None:
        return
    if isinstance(value, str) or not Decimal(str(assumption.low)) <= value <= Decimal(
        str(assumption.high)
    ):
        raise FigureError(
            f"the value {format_value(row.unit, value)} lies outside its own range "
            f"{format_value(row.unit, Decimal(str(assumption.low)))} to "
            f"{format_value(row.unit, Decimal(str(assumption.high)))}"
        )


def load_figures(company_dir: Path) -> FigureSet:
    """Read ``sources.toml`` and ``figures.toml`` from ``company_dir`` and resolve them."""
    sources = parse_sources(_read(company_dir / SOURCES_FILE))
    rows = parse_rows(_read(company_dir / FIGURES_FILE))
    return resolve(rows, sources)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise FigureError(f"cannot read {path}: {exc.strerror or exc}") from exc
