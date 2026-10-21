"""``hc case scenario render`` and ``check``: a case's ``scenario.toml`` is rendered from its shape's own
template and the case's rows, and checked by re-rendering (search-half doc §4.6.1; protocol §12.5 and §12.6).

The template is the shape's ``sN.source.toml``, unchanged: every word of the case scenario is the fictional
scenario's. What a case adds is **rows** (``scenario-figures.toml`` in its appendix folder): the unscaled
value of each figure the case can state, with a scale and a source. The render

* scales each row by ``build.json``'s factor with ``scale.py`` (dollars to three significant figures, heads to
  the nearest 5), then rounds it to the fictional row's step as the fictional figures do;
* fills a derived row by the fictional row's formula only when every row the formula names is a case row;
* drops a sentence whole when it holds a placeholder with no row, and, if any option text (or, for S1, any
  lever's detail) drops one, drops every sentence with a placeholder from all of them (equal treatment);
* states a heads figure under 100 as "fewer than 100", refuses a total under 100 (criterion 4), and gives a
  cap under 100 the value of the total (an S3 total is the exception: a number, to the nearest whole person
  under 100, and an S3 total-pay figure is rounded to three significant digits and no further, §4.6.6);
* never prints a cap set to the total, or a figure derived from one, outside the menu heading's sum of caps:
  no source states it, so its sentences are dropped like any other with no row;
* takes the fictional value only for the label rows that are names (the plant numbers);
* omits an extra rule whose numbers have no rows;
* refuses when an option text, the role, the menu heading, the instruction or the situation is left empty.

The fill itself is ``scenarios.render.fill_scenario``, run on the template with the dropped sentences removed
and over the case's values, so the harness's own ``Scenario`` model validates the result.

``check_scenario`` re-renders in memory and compares byte for byte, and re-checks every source. It reports
failures by criterion with row ids and counts, never a name, a figure or an excerpt.
"""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from string import Formatter
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, StrictBool, ValidationError, model_validator

from horizon_compact.casebuild import scale
from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.cutoff import (
    CutoffError,
    FilingStamp,
    admit,
    parse_acceptance,
    parse_date,
)
from horizon_compact.casebuild.exploratory import row_for
from horizon_compact.casebuild.search import LogError
from horizon_compact.dossier.figures import (
    FigureError,
    FigureRow,
    FigureSet,
    Number,
    Resolved,
    Unit,
    evaluate_formula,
    round_half_up,
    step_for,
)
from horizon_compact.experiment import SOURCE_SUFFIX
from horizon_compact.scenarios.render import (
    SCENARIOS_DIR,
    ScenarioSource,
    ScenarioSourceError,
    SourceChoice,
    SourceLever,
    fill_scenario,
    load_scenario_figures,
    parse_source,
    toml_text,
)

RENDER_VERSION = 1
SEARCH_LABEL = "search"
SMALL = Decimal(scale.SMALL_GROUP)
# The figure-free form of S3 (search-half doc §4.6.5 step 0), outside experiment/company/ so Phase 4's S3 and
# the tag's content hash are unchanged; the S3 floor of this record (step 1 item 2), as stated and unscaled;
# and the S3 rows that are a total pay figure, which the pay-per-head check (step 0 item 3) pairs with a
# headcount.
S3_FORM_PATH = "experiment/case-forms/s3.toml"
S3_FLOOR = Decimal(50)
S3_TOTAL_PAY = frozenset({"payroll_p6", "s3_retool_payroll", "s3_sell_payroll"})
_MILLION = Decimal(1_000_000)

CRITERION_4 = "criterion 4 (maps_to_shape)"
ROWS = "rows file"
CUTOFF = "cut-off rule (protocol 12.6)"
FIRST = "first-disclosure rule (4.6 rule 1)"
RENDER = "render"

_ID = re.compile(r"[a-z][a-z0-9_]*")
# The label rows that are names in the wording (§4.6.1 item 3): the plant numbers. Any other label (S3's
# ``s3_alloc_basis``, how corporate costs are shared) is a fact about the fictional company, so a case has no
# value for it and its sentence is dropped (§4.6: everything of the shape is kept except the facts).
_NAME_LABEL = re.compile(r"plant_[0-9]+_no")
_HEADER = (
    "# RENDERED by `hc case scenario render` from {source} and the case's rows. Do not edit by hand:\n"
    "# `hc case scenario check` fails if this file differs from a fresh render.\n\n"
)
_RULE_NUMBERS = ("base", "divisor", "fraction", "amount")


class ScenarioRefused(Exception):
    """The scenario cannot be rendered. The message holds row ids, field names and counts, never a value."""

    def __init__(self, criterion: str, message: str) -> None:
        super().__init__(f"{criterion}: {message}")
        self.criterion = criterion
        self.message = message


@dataclass(frozen=True)
class Failure:
    criterion: str
    message: str


# --- the rows file ---------------------------------------------------------------------------------------


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CaseRow(_Strict):
    """One figure the case can state. ``value`` is unscaled; ``unit`` is the fictional row's. A cap with no
    figure of its own says ``equals_total`` and nothing else."""

    value: Number | None = None
    unit: Unit | None = None
    scale: Literal["dollars", "heads", "none"] | None = None
    per: str | None = None
    source: Literal["pre_cutoff", "first_disclosure"] | None = None
    accession: str | None = None
    locator: str | None = None
    equals_total: StrictBool = False

    @model_validator(mode="after")
    def _a_row_is_whole(self) -> CaseRow:
        if self.equals_total:
            extra = [
                name
                for name in ("value", "unit", "scale", "per", "source", "accession", "locator")
                if getattr(self, name) is not None
            ]
            if extra:
                raise ValueError(f"a row with equals_total says nothing else ({', '.join(extra)})")
            return self
        missing = [
            name
            for name in ("value", "unit", "scale", "source", "locator")
            if getattr(self, name) in (None, "")
        ]
        if missing:
            raise ValueError(f"needs {', '.join(missing)}")
        assert self.value is not None
        if self.unit == "label":
            raise ValueError("a label row takes the fictional value and has no case row")
        money = self.unit in ("usd", "usd_m")
        if self.scale == "dollars" and not money:
            raise ValueError("scale dollars is for a usd or usd_m row")
        if self.scale == "heads":
            if self.unit != "count":
                raise ValueError("scale heads is for a count row")
            if Decimal(str(self.value)) != Decimal(str(self.value)).to_integral_value():
                raise ValueError("a heads row is a whole number")
            if self.value <= 0:
                raise ValueError("a heads row is above zero")
        if self.scale == "none" and money and not self.per:
            raise ValueError(
                "an unscaled dollar row needs per: only a ratio of two scaled quantities escapes scaling"
            )
        if self.per is not None and not (self.scale == "none" and money):
            raise ValueError("per belongs on an unscaled dollar row")
        if self.source == "pre_cutoff" and not self.accession:
            raise ValueError("a pre_cutoff row needs an accession")
        if self.source == "first_disclosure" and self.accession is not None:
            raise ValueError(
                "a first_disclosure row has no accession: its date is the selection log's"
            )
        return self


class RowsFile(_Strict):
    rows: dict[str, CaseRow]


def parse_rows(data: bytes) -> dict[str, CaseRow]:
    try:
        parsed = RowsFile.model_validate(tomllib.loads(data.decode("utf-8")))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise ScenarioRefused(
            ROWS, f"scenario-figures.toml is not valid TOML ({type(exc).__name__})"
        ) from exc
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(str(part) for part in err['loc']) or '(file)'}: {err['msg']}"
            for err in exc.errors()
        )
        raise ScenarioRefused(ROWS, f"scenario-figures.toml is invalid: {problems}") from exc
    for key in parsed.rows:
        if not _ID.fullmatch(key):
            raise ScenarioRefused(ROWS, f"row id {key!r} must be lowercase letters, digits and _")
    return dict(parsed.rows)


class S3Form(_Strict):
    """``experiment/case-forms/s3.toml``: one figure-free sentence per option, and the situation sentences
    that would be false without the figures (§4.6.5 step 0 items 1 and 2)."""

    drop_from_situation: tuple[str, ...]
    options: dict[str, str]

    @model_validator(mode="after")
    def _whole(self) -> S3Form:
        if set(self.options) != {"close", "retool", "sell"}:
            raise ValueError("options are close, retool and sell, each once")
        for key, text in self.options.items():
            if "{" in text or "}" in text:
                raise ValueError(f"option {key} holds a placeholder: the form states no figure")
            if len(re.split(r"(?<=[.?!])\s+", text.strip())) != 1:
                raise ValueError(f"option {key} is not one sentence")
        if not self.drop_from_situation:
            raise ValueError("drop_from_situation names at least one sentence")
        return self


def parse_s3_form(data: bytes) -> S3Form:
    try:
        return S3Form.model_validate(tomllib.loads(data.decode("utf-8")))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError, ValidationError) as exc:
        raise ScenarioRefused(
            RENDER, f"{S3_FORM_PATH} is invalid ({type(exc).__name__}): {exc}"
        ) from exc


# --- everything the render and the check read ------------------------------------------------------------


@dataclass(frozen=True)
class Inputs:
    label: str
    shape: str
    factor: float
    cutoff: date
    build_sha256: str
    rows_sha256: str
    rows: dict[str, CaseRow]
    sources: dict[str, Any]  # sources.json
    source: ScenarioSource
    fictional: FigureSet
    form: S3Form | None = None  # S3 only, and only if the file is there
    form_sha256: str | None = None


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ScenarioRefused(RENDER, f"{path.name} cannot be read ({type(exc).__name__})") from exc


def _read_json(path: Path, what: str, criterion: str) -> tuple[Any, bytes]:
    try:
        data = path.read_bytes()
        return json.loads(data), data
    except OSError as exc:
        raise ScenarioRefused(
            criterion, f"{what} cannot be read: {path.name} ({type(exc).__name__})"
        ) from exc
    except ValueError as exc:
        raise ScenarioRefused(criterion, f"{what} is not valid JSON: {path.name}") from exc


def load_inputs(case: CaseAppendix, repo_root: Path) -> Inputs:
    build, build_bytes = _read_json(case.build_path, "the build record", RENDER)
    try:
        shape = str(build["shape"])
        factor = float(build["factor"])
        cutoff = parse_date(build["cutoff"], what="build.json's cutoff")
    except (KeyError, TypeError, ValueError, CutoffError) as exc:
        raise ScenarioRefused(RENDER, "build.json lacks a shape, a factor or a cutoff") from exc
    if shape not in ("S1", "S2", "S3", "S4"):
        raise ScenarioRefused(RENDER, "build.json names no scenario shape")
    sources, _ = _read_json(case.sources_path, "the source list", CUTOFF)
    try:
        rows_bytes = case.scenario_figures_path.read_bytes()
    except OSError as exc:
        raise ScenarioRefused(
            ROWS,
            f"{case.scenario_figures_path.name} cannot be read ({type(exc).__name__}): write the case's rows first",
        ) from exc
    rows = parse_rows(rows_bytes)
    template = repo_root / SCENARIOS_DIR / f"{shape.lower()}{SOURCE_SUFFIX}"
    try:
        source = parse_source(template)
        fictional = load_scenario_figures(repo_root)
    except (ScenarioSourceError, FigureError) as exc:
        raise ScenarioRefused(
            RENDER, f"the shape's template or figures cannot be read: {exc}"
        ) from exc
    form: S3Form | None = None
    form_sha256: str | None = None
    form_path = repo_root / S3_FORM_PATH
    if shape == "S3" and form_path.exists():
        form_bytes = _read_bytes(form_path)
        form, form_sha256 = parse_s3_form(form_bytes), _sha256(form_bytes)
    inputs = Inputs(
        label=case.label,
        shape=shape,
        factor=factor,
        cutoff=cutoff,
        build_sha256=_sha256(build_bytes),
        rows_sha256=_sha256(rows_bytes),
        rows=rows,
        sources=sources if isinstance(sources, dict) else {},
        source=source,
        fictional=fictional,
        form=form,
        form_sha256=form_sha256,
    )
    _check_rows_against_shape(inputs)
    return inputs


def _cap_ids(source: ScenarioSource) -> set[str]:
    return {lever.cap for lever in source.levers if lever.cap}


def _check_rows_against_shape(inputs: Inputs) -> None:
    caps = _cap_ids(inputs.source)
    for key, row in inputs.rows.items():
        fictional = inputs.fictional.rows.get(key)
        if fictional is None:
            raise ScenarioRefused(ROWS, f"row {key!r} is not a row of the shape's figures")
        if fictional.unit == "label":
            raise ScenarioRefused(ROWS, f"row {key!r} is a label: it takes the fictional value")
        if row.equals_total:
            if key not in caps:
                raise ScenarioRefused(ROWS, f"row {key!r} says equals_total but is no lever's cap")
            continue
        if row.unit != fictional.unit:
            raise ScenarioRefused(ROWS, f"row {key!r} has a unit other than the fictional row's")
        # Every derived count in the fictional figures is a number of people (a plant's headcount, the roles
        # affected, positions kept): a case states it scaled to the nearest 5, never unscaled.
        if fictional.unit == "count" and fictional.formula is not None and row.scale != "heads":
            raise ScenarioRefused(ROWS, f"row {key!r} is a headcount: its scale is heads")


# --- the sources -----------------------------------------------------------------------------------------


def source_failures(inputs: Inputs, case: CaseAppendix) -> list[Failure]:
    """Every row's source: a pre-cut-off one is an accession in ``sources.json`` that ``admit`` accepts; only
    the total may be first-disclosure, and its date is the selection log's."""
    failures: list[Failure] = []
    stated = inputs.sources.get("cutoff")
    try:
        if parse_date(stated, what="sources.json's cutoff") != inputs.cutoff:
            failures.append(Failure(CUTOFF, "sources.json and build.json disagree on the cut-off"))
    except CutoffError as exc:
        failures.append(Failure(CUTOFF, str(exc)))
    records = {
        str(r["accession"]): r
        for r in inputs.sources.get("sources", [])
        if isinstance(r, dict) and r.get("accession")
    }
    first_disclosure: list[str] = []
    for key, row in inputs.rows.items():
        if row.equals_total:
            continue
        if row.source == "first_disclosure":
            first_disclosure.append(key)
            continue
        record = records.get(row.accession or "")
        if record is None:
            failures.append(Failure(CUTOFF, f"row {key}: its accession is not in sources.json"))
            continue
        try:
            accepted = record.get("accepted")
            stamp = FilingStamp(
                filed=parse_date(record.get("filed"), what=f"row {key}'s source filing date"),
                accepted=parse_acceptance(accepted) if accepted else None,
                label=str(row.accession),
            )
            if not admit(stamp, inputs.cutoff):
                failures.append(
                    Failure(
                        CUTOFF, f"row {key}: its source was not filed strictly before the cut-off"
                    )
                )
        except CutoffError as exc:
            failures.append(Failure(CUTOFF, f"row {key}: {exc}"))
    for key in first_disclosure:
        if key != inputs.source.total:
            failures.append(
                Failure(
                    FIRST,
                    f"row {key} is first_disclosure but is not the total; only the total may be",
                )
            )
    if first_disclosure:
        failures.extend(_disclosure_failures(inputs, case))
    return failures


def _disclosure_failures(inputs: Inputs, case: CaseAppendix) -> list[Failure]:
    try:
        row = row_for(CaseAppendix(case.root, SEARCH_LABEL), case.label)
    except LogError as exc:
        return [Failure(FIRST, f"the selection log cannot be read: {exc}")]
    if row is None or row.disclosed is None:
        return [Failure(FIRST, "the selection log has no first-disclosure date for the case")]
    if row.disclosed - timedelta(days=1) != inputs.cutoff:
        return [Failure(FIRST, "the cut-off is not the day before the log's first-disclosure date")]
    return []


# --- the values ------------------------------------------------------------------------------------------


@dataclass
class _Values:
    resolved: dict[str, Resolved] = field(default_factory=dict)
    heads: set[str] = field(default_factory=set)
    derived: list[str] = field(default_factory=list)
    caps_to_total: list[dict[str, str]] = field(default_factory=list)
    # Caps set to the total, and every row derived from one: numbers the levers need, but no source states
    # them, so no text but the menu heading's sum of caps may print them (§4.6 rules 2, 3 and 5).
    stand_ins: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class _PayResolved(Resolved):
    """An S3 total-pay figure (§4.6.6 B.2): its value is rounded to three significant digits and no further,
    so it reads in millions with the digits it has ("$1.08 million", "$0.946 million", "$14.3 million"), at
    least one decimal. Only the case's copy reads this way; ``format_value`` and the fictional rows are
    untouched."""

    @property
    def shown(self) -> str:
        assert isinstance(self.value, Decimal)
        millions = format(abs(self.value) / _MILLION, ",f")
        whole, _, decimals = millions.partition(".")
        sign = "-" if self.value < 0 else ""
        return f"{sign}${whole}.{decimals.rstrip('0') or '0'} million"


def _is_s3_pay(inputs: Inputs, key: str) -> bool:
    return inputs.shape == "S3" and key in S3_TOTAL_PAY


def _resolved(inputs: Inputs, key: str, row: FigureRow, shown: Decimal | str) -> Resolved:
    if _is_s3_pay(inputs, key) and isinstance(shown, Decimal):
        return _PayResolved(key, row, shown)
    return Resolved(key, row, shown)


def _scaled(
    row: CaseRow,
    fictional: FigureRow,
    factor: float,
    *,
    as_number: bool = False,
    to_step: bool = True,
) -> Decimal | str:
    """``as_number``: an S3 case's total, stated as a number even under 100: to the nearest whole person
    there (§4.6.5 step 1 item 2, §4.6.6 B.1). ``to_step`` false: a dollar figure stops at three significant
    digits instead of going on to the fictional row's step (an S3 total-pay figure, §4.6.6 B.2)."""
    assert row.value is not None
    value = Decimal(str(row.value))
    if row.scale == "heads" and as_number:
        return Decimal(scale.scale_total_heads(int(value), factor))
    if row.scale == "heads":
        heads = scale.scale_heads(int(value), factor)
        return Decimal(heads.value) if heads.value is not None else scale.FEWER_THAN
    if row.scale == "dollars":
        value = scale.scale_dollars(value, factor)
        if not to_step:
            return value
    step = step_for(fictional)
    assert step is not None
    return round_half_up(value, step)


def _number(values: _Values, key: str) -> Decimal | None:
    resolved = values.resolved.get(key)
    return resolved.value if resolved is not None and isinstance(resolved.value, Decimal) else None


def _derive(inputs: Inputs, values: _Values, skip: set[str]) -> None:
    """Fill every derived row whose formula names only rows the case has, until nothing more can be filled.
    A count derived from a headcount is a headcount, so under 100 it reads "fewer than 100"."""
    fictional = inputs.fictional
    pending = [
        key
        for key, row in fictional.rows.items()
        if row.formula is not None and key not in values.resolved and key not in skip
    ]
    changed = True
    while changed:
        changed = False
        for key in list(pending):
            refs = fictional.references[key]
            if any(_number(values, ref) is None for ref in refs):
                continue
            row = fictional.rows[key]
            assert row.formula is not None
            pending.remove(key)
            changed = True
            try:
                value = evaluate_formula(row.formula, lambda ref: _required(_number(values, ref)))
            except FigureError:
                continue  # a division by zero on the case's numbers: the row cannot be filled
            step = step_for(row)
            assert step is not None
            if _is_s3_pay(inputs, key):  # three significant digits and no step (§4.6.6 B.2)
                value = scale.round_significant(value)
            else:
                value = round_half_up(value, step)
            if row.unit == "count" and refs & values.heads:
                values.heads.add(key)
                # an S3 total under 100 is a number (its step is a multiple of 5): §4.6.5 step 1 item 2
                small = value < SMALL and not _is_s3_total(inputs, key)
                shown: Decimal | str = scale.FEWER_THAN if small else value
            else:
                shown = value
            values.resolved[key] = _resolved(inputs, key, row, shown)
            values.derived.append(key)


def _is_s3_total(inputs: Inputs, key: str) -> bool:
    return inputs.shape == "S3" and key == inputs.source.total


def _unscaled(inputs: Inputs, key: str) -> Decimal | None:
    """The figure as the case states it, before scaling and rounding: a case row's value, or a derived row's
    formula over those; None if the case has no way to state it."""
    row = inputs.rows.get(key)
    if row is not None and not row.equals_total:
        return Decimal(str(row.value))
    formula = inputs.fictional.rows[key].formula if key in inputs.fictional.rows else None
    if row is not None or formula is None:
        return None
    refs = inputs.fictional.references[key]
    found = {ref: _unscaled(inputs, ref) for ref in refs}
    if any(value is None for value in found.values()):
        return None
    try:
        return evaluate_formula(formula, lambda ref: _required(found[ref]))
    except FigureError:
        return None


def _required(value: Decimal | None) -> Decimal:
    assert value is not None
    return value


def case_values(inputs: Inputs) -> _Values:
    fictional, source = inputs.fictional, inputs.source
    values = _Values()
    for key, resolved in fictional.resolved.items():
        if resolved.row.unit == "label" and _NAME_LABEL.fullmatch(key):
            values.resolved[key] = resolved
    equals_total: set[str] = set()
    for key, row in inputs.rows.items():
        if row.equals_total:
            equals_total.add(key)
            continue
        fic = fictional.rows[key]
        try:
            shown = _scaled(
                row,
                fic,
                inputs.factor,
                as_number=_is_s3_total(inputs, key),
                to_step=not _is_s3_pay(inputs, key),
            )
        except FigureError as exc:
            raise ScenarioRefused(ROWS, f"row {key}: {exc}") from exc
        values.resolved[key] = _resolved(inputs, key, fic, shown)
        if row.scale == "heads":
            values.heads.add(key)
    _derive(inputs, values, equals_total)

    total = values.resolved.get(source.total)
    if total is None:
        raise ScenarioRefused(
            CRITERION_4,
            f"the total ({source.total}) is neither a case row nor derivable from case rows",
        )
    if isinstance(total.value, str):
        raise ScenarioRefused(CRITERION_4, "the total is under 100 after scaling")
    if inputs.shape == "S3":
        # §4.6.5 step 1 item 2: the floor is 50 as stated, and a smaller scaled total is a number
        stated = _unscaled(inputs, source.total)
        if stated is None or stated < S3_FLOOR:
            raise ScenarioRefused(CRITERION_4, f"the total is under {S3_FLOOR} as stated")
    elif source.unit == "people" and total.value < SMALL:
        raise ScenarioRefused(CRITERION_4, "the total is under 100 after scaling")
    if source.unit == "people" and source.total not in values.heads:
        raise ScenarioRefused(ROWS, f"the total ({source.total}) is not stated as a headcount")

    for key in sorted(equals_total):
        values.resolved[key] = Resolved(key, fictional.rows[key], total.value)
        values.caps_to_total.append({"row": key, "reason": "equals_total"})
    for lever in source.levers:
        if lever.cap is None:
            continue
        held = values.resolved.get(lever.cap)
        if held is not None and isinstance(held.value, str) and lever.cap not in equals_total:
            values.resolved[lever.cap] = Resolved(lever.cap, held.row, total.value)
            values.caps_to_total.append({"row": lever.cap, "reason": "under_100"})
    values.stand_ins = {cap["row"] for cap in values.caps_to_total}
    _derive(inputs, values, set())
    changed = True
    while changed:
        changed = False
        for key in values.derived:
            if key not in values.stand_ins and inputs.fictional.references[key] & values.stand_ins:
                values.stand_ins.add(key)
                changed = True
    for lever in source.levers:
        if lever.cap is not None and _number(values, lever.cap) is None:
            raise ScenarioRefused(
                CRITERION_4,
                f"lever {lever.key}: its cap ({lever.cap}) is neither a case row nor derivable, "
                "and is not marked equals_total",
            )
        if (
            lever.cap is not None
            and source.unit == "people"
            and lever.cap not in values.heads
            and lever.cap not in values.stand_ins
        ):
            raise ScenarioRefused(ROWS, f"lever {lever.key}: its cap is not stated as a headcount")
    # fill_scenario names the value of a figure that is not whole; the refusal here names the row only
    for key in [source.total, *(lever.cap for lever in source.levers if lever.cap)]:
        value = _required(_number(values, key))
        if value != value.to_integral_value():
            raise ScenarioRefused(RENDER, f"{key} is not a whole number after scaling")
    return values


# --- sentences -------------------------------------------------------------------------------------------


def _placeholders(sentence: str) -> set[str]:
    try:
        return {name for _lit, name, _spec, _conv in Formatter().parse(sentence) if name}
    except ValueError:
        return set()  # a malformed placeholder: the fill refuses it, naming the field


def _sentences(text: str) -> list[list[tuple[str, str]]]:
    """``text`` as paragraphs of (sentence, the gap after it). A sentence ends at ``.``, ``?`` or ``!``
    followed by a space, a line break or the end of the field."""
    out = []
    for paragraph in re.split(r"\n[ \t]*\n", text.strip()):
        parts = re.split(r"(?<=[.?!])(\s+)", paragraph.strip())
        out.append(
            [
                (parts[i], parts[i + 1] if i + 1 < len(parts) else "")
                for i in range(0, len(parts), 2)
            ]
        )
    return out


def without_sentences(text: str, drop: Callable[[str], bool]) -> tuple[str, int]:
    """``text`` without the sentences ``drop`` picks; a paragraph left empty goes with its sentences. Returns
    the kept text and the number dropped."""
    dropped = 0
    paragraphs: list[str] = []
    for sentences in _sentences(text):
        kept = ""
        for sentence, gap in sentences:
            if drop(sentence):
                dropped += 1
                continue
            kept += sentence + gap
        if kept.strip():
            paragraphs.append(kept.strip())
    return "\n\n".join(paragraphs), dropped


def drop_sentences(text: str, available: set[str], *, all_placeholders: bool) -> tuple[str, int]:
    """``text`` without the sentences that name a row the case lacks (or, with ``all_placeholders``, any row
    at all). Returns the kept text and the number dropped."""

    def drop(sentence: str) -> bool:
        names = _placeholders(sentence)
        return bool(names) and (all_placeholders or not names <= available)

    return without_sentences(text, drop)


@dataclass
class _Drops:
    by_field: dict[str, int] = field(default_factory=dict)
    equal_treatment: bool = False
    case_form: bool = False  # S3's figure-free form took the place of the options' sentences

    def add(self, where: str, count: int) -> None:
        if count:
            self.by_field[where] = self.by_field.get(where, 0) + count


def _text(
    drops: _Drops, where: str, text: str, available: set[str], *, all_placeholders: bool = False
) -> str:
    kept, count = drop_sentences(text, available, all_placeholders=all_placeholders)
    drops.add(where, count)
    return kept


def _group(texts: list[tuple[str, str]], available: set[str], drops: _Drops) -> dict[str, str]:
    """The option texts (or S1's lever details) together: if any drops a sentence, every one drops every
    sentence with a placeholder (protocol §12.6's equal treatment)."""
    first = {
        where: drop_sentences(text, available, all_placeholders=False) for where, text in texts
    }
    if any(count for _kept, count in first.values()):
        drops.equal_treatment = True
        out: dict[str, str] = {}
        for where, text in texts:
            kept, count = drop_sentences(text, available, all_placeholders=True)
            drops.add(where, count)
            out[where] = kept
        return out
    return {where: kept for where, (kept, _count) in first.items()}


def _dropped_source(
    source: ScenarioSource, values: _Values, inputs: Inputs
) -> tuple[ScenarioSource, _Drops, list[str]]:
    available = set(values.resolved) - values.stand_ins
    drops = _Drops()
    sid = source.id

    def single(name: str, text: str, names: set[str] = available) -> str:
        return _text(drops, name, text, names) if text else ""

    update: dict[str, Any] = {
        "role": single("role", source.role),
        "currency_note": single("currency_note", source.currency_note),
        "situation": single("situation", source.situation),
        # The menu heading states the sum of the caps the model is given, stand-ins included.
        "menu_heading": single("menu_heading", source.menu_heading, set(values.resolved)),
        "options_heading": single("options_heading", source.options_heading),
        "instruction": single("instruction", source.instruction),
    }
    for name, text in update.items():
        if not text and name != "options_heading":
            raise ScenarioRefused(
                RENDER, f"{sid}: {name} is empty after the sentences with no row were dropped"
            )

    choice: SourceChoice | None = source.choice
    levers = list(source.levers)
    if choice is not None:
        texts = [(f"option {o.key}", o.text) for o in choice.options]
        if inputs.shape == "S3" and any(
            drop_sentences(text, available, all_placeholders=False)[1] for _where, text in texts
        ):
            kept = _form_options(inputs, update, drops, [o.key for o in choice.options])
        else:
            kept = _group(texts, available, drops)
        options = []
        for option in choice.options:
            text = kept[f"option {option.key}"]
            if not text:
                raise ScenarioRefused(
                    RENDER, f"{sid}: the text of option {option.key} is empty after dropping"
                )
            options.append(option.model_copy(update={"text": text}))
        choice = choice.model_copy(update={"options": options})
        levers = [_with_note(lever, drops, available) for lever in levers]
    else:
        kept = _group(
            [(f"lever {lever.key} detail", lever.detail) for lever in levers if lever.detail],
            available,
            drops,
        )
        levers = [
            _with_note(
                lever.model_copy(update={"detail": kept.get(f"lever {lever.key} detail", "")}),
                drops,
                available,
            )
            for lever in levers
        ]
    rules_omitted: list[str] = []
    rules = []
    for rule in source.rules:
        fields = rule.model_dump()
        numbers = [fields[name] for name in _RULE_NUMBERS if name in fields]
        if all(_number(values, ref) is not None for ref in numbers):
            rules.append(rule)
        else:
            rules_omitted.append(f"{rule.kind}:{fields.get('key', '')}")
    return (
        source.model_copy(update={**update, "choice": choice, "levers": levers, "rules": rules}),
        drops,
        rules_omitted,
    )


def _form_options(
    inputs: Inputs, update: dict[str, Any], drops: _Drops, keys: list[str]
) -> dict[str, str]:
    """Equal treatment on an S3 case (§4.6.5 step 0): each option is the form's one figure-free sentence, and
    the form's sentences leave the situation (``update['situation']``, changed in place)."""
    form = inputs.form
    if form is None:
        raise ScenarioRefused(
            RENDER, f"{S3_FORM_PATH} is not there: an S3 case with missing figures needs it"
        )
    if set(keys) != set(form.options):
        raise ScenarioRefused(RENDER, "the S3 template's options are not the form's")
    gone = set(form.drop_from_situation)
    update["situation"], count = without_sentences(update["situation"], lambda s: s in gone)
    if count != len(gone):
        raise ScenarioRefused(RENDER, "a sentence the S3 form drops is not in the situation")
    drops.add("situation", count)
    drops.equal_treatment = True
    drops.case_form = True
    return {f"option {key}": text for key, text in form.options.items()}


def _with_note(lever: SourceLever, drops: _Drops, available: set[str]) -> SourceLever:
    if not lever.note:
        return lever
    return lever.model_copy(
        update={"note": _text(drops, f"lever {lever.key} note", lever.note, available)}
    )


# --- the render ------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Rendered:
    scenario_text: str
    record_text: str
    dropped: int
    rules_omitted: int
    caps_to_total: int


def _kept_texts(source: ScenarioSource) -> list[tuple[str, str]]:
    """Every text the scenario prints, by field, after the drops."""
    texts = [
        ("role", source.role),
        ("currency_note", source.currency_note),
        ("situation", source.situation),
        ("menu_heading", source.menu_heading),
        ("options_heading", source.options_heading),
        ("instruction", source.instruction),
    ]
    if source.choice is not None:
        texts += [(f"option {o.key}", o.text) for o in source.choice.options]
    for lever in source.levers:
        texts += [
            (f"lever {lever.key} detail", lever.detail),
            (f"lever {lever.key} note", lever.note),
        ]
    return [(where, text) for where, text in texts if text]


def _pay_per_head(
    inputs: Inputs, values: _Values, source: ScenarioSource
) -> list[dict[str, object]]:
    """§12.6 and §4.6.5 step 0 item 3: on each kept sentence of an S3 scenario that states a headcount and a
    total pay figure, pay per head after scaling and rounding stays within 3.5% of its unscaled value.
    One of each to a sentence, as the dossier's line is; a failure is a build error, which names rows and
    never a value."""
    shown = set(values.resolved) - values.stand_ins
    records: list[dict[str, object]] = []
    for where, text in _kept_texts(source):
        for sentences in _sentences(text):
            for sentence, _gap in sentences:
                names = _placeholders(sentence) & shown
                pay, heads = sorted(names & S3_TOTAL_PAY), sorted(names & values.heads)
                if not pay or not heads:
                    continue
                if len(pay) != 1 or len(heads) != 1:
                    raise ScenarioRefused(
                        RENDER,
                        f"{where}: a sentence states {len(heads)} headcounts and {len(pay)} total pay "
                        "figures; the pay-per-head check needs one of each",
                    )
                pay_row, heads_row = pay[0], heads[0]
                pay_before, heads_before = _unscaled(inputs, pay_row), _unscaled(inputs, heads_row)
                pay_after, heads_after = _number(values, pay_row), _number(values, heads_row)
                if (
                    pay_before is None
                    or pay_after is None
                    or heads_before is None
                    or heads_before < 1
                ):
                    raise ScenarioRefused(
                        RENDER,
                        f"{where}: pay per head cannot be checked for {pay_row} and {heads_row}",
                    )
                check = scale.check_pay_per_head(
                    scale.PayFigure(
                        line=len(records) + 1,
                        pay_before=pay_before,
                        pay_after=pay_after,
                        heads_before=int(heads_before.to_integral_value()),
                        heads_after=int(heads_after) if heads_after is not None else None,
                    )
                )
                if not check.passed:
                    raise ScenarioRefused(
                        RENDER,
                        f"{where}: pay per head for {pay_row} and {heads_row} moved more than 3.5%: "
                        "a build error (protocol §12.6), fixed in the builder and the case rebuilt with "
                        "the factor unchanged; if none is found, the case fails criterion 4",
                    )
                records.append(
                    {"field": where, "heads": heads_row, "pay": pay_row, **check.record()}
                )
    return records


def _closure(used: set[str], references: Mapping[str, frozenset[str]]) -> set[str]:
    found: set[str] = set()
    pending = list(used)
    while pending:
        key = pending.pop()
        if key not in found:
            found.add(key)
            pending.extend(references.get(key, ()))
    return found


def render_in_memory(case: CaseAppendix, repo_root: Path) -> Rendered:
    inputs = load_inputs(case, repo_root)
    failures = source_failures(inputs, case)
    if failures:
        first = failures[0]
        raise ScenarioRefused(first.criterion, first.message)
    values = case_values(inputs)
    source, drops, rules_omitted = _dropped_source(inputs.source, values, inputs)
    fs = FigureSet(
        sources={},
        rows=inputs.fictional.rows,
        resolved=values.resolved,
        references=inputs.fictional.references,
    )
    try:
        rendered = fill_scenario(source, fs, None)
    except ScenarioSourceError as exc:
        raise ScenarioRefused(RENDER, str(exc)) from exc
    reached = _closure(set(rendered.used), inputs.fictional.references)
    record = {
        "render_version": RENDER_VERSION,
        "shape": inputs.shape,
        "factor": inputs.factor,
        "build_sha256": inputs.build_sha256,
        "rows_sha256": inputs.rows_sha256,
        "rows_used": sorted(k for k in inputs.rows if k in reached),
        "rows_unused": sorted(k for k in inputs.rows if k not in reached),
        "rows_derived": sorted(k for k in values.derived if k in reached),
        "sentences_dropped": dict(sorted(drops.by_field.items())),
        "equal_treatment_applied": drops.equal_treatment,
        "rules_omitted": rules_omitted,
        "caps_set_to_total": sorted(values.caps_to_total, key=lambda c: c["row"]),
    }
    if (
        inputs.shape == "S3"
    ):  # keys only an S3 case's record has, so no other shape's record changes
        record["pay_per_head"] = _pay_per_head(inputs, values, source)
        if drops.case_form:
            record["case_form"] = {"file": S3_FORM_PATH, "sha256": inputs.form_sha256}
    return Rendered(
        scenario_text=toml_text(
            rendered.data, f"{inputs.shape.lower()}{SOURCE_SUFFIX}", header=_HEADER
        ),
        record_text=json.dumps(record, indent=2, sort_keys=True) + "\n",
        dropped=sum(drops.by_field.values()),
        rules_omitted=len(rules_omitted),
        caps_to_total=len(values.caps_to_total),
    )


def render_case_scenario(case: CaseAppendix, repo_root: Path) -> Rendered:
    """Write ``scenario.toml`` and ``scenario-render.json``, each once; nothing if the render refuses."""
    rendered = render_in_memory(case, repo_root)
    case.write_once(case.scenario_path, rendered.scenario_text.encode("utf-8"))
    case.write_once(case.scenario_render_path, rendered.record_text.encode("utf-8"))
    return rendered


def check_scenario(case: CaseAppendix, repo_root: Path) -> list[Failure]:
    """Empty when the scenario passes: every source re-checked, and ``scenario.toml`` and its record equal a
    fresh render byte for byte."""
    failures: list[Failure] = []
    try:
        inputs = load_inputs(case, repo_root)
    except ScenarioRefused as exc:
        return [Failure(exc.criterion, exc.message)]
    failures.extend(source_failures(inputs, case))
    if failures:
        return failures
    try:
        fresh = render_in_memory(case, repo_root)
    except ScenarioRefused as exc:
        return [Failure(exc.criterion, exc.message)]
    for path, expected in (
        (case.scenario_path, fresh.scenario_text),
        (case.scenario_render_path, fresh.record_text),
    ):
        try:
            found = path.read_bytes()
        except OSError:
            failures.append(
                Failure(RENDER, f"{path.name} does not exist: run `hc case scenario render`")
            )
            continue
        if found != expected.encode("utf-8"):
            failures.append(
                Failure(
                    RENDER,
                    f"{path.name} differs from a fresh render (edited, or the rows or build changed)",
                )
            )
    return failures


def format_failures(failures: list[Failure]) -> list[str]:
    """One line per failure, grouped by criterion."""
    lines: list[str] = []
    for criterion in dict.fromkeys(f.criterion for f in failures):
        lines.append(f"{criterion}:")
        lines.extend(f"  {f.message}" for f in failures if f.criterion == criterion)
    return lines
