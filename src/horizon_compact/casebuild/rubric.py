"""The rubric reader: ``rubric.toml`` in the form of search-half doc §4.7, read strictly (Phase 5.5
IMPLEMENTATION doc §5.2, K2).

A rubric records what the company did, from filings after the cut-off: its choice (an option key, or "not
observable"), each lever line it observably used (a number, or "not observable"), which dimensions are
observable and which are excluded, every uncertain call, the outcome terms for the foreshadowing check and
the source excerpt for every line. **A rubric is never edited to fit this reader**: its hash is in
``case.lock``, and the gate refuses a changed one. This reader is fitted to the five committed rubrics.

The reader is strict: an unknown key, a wrong type, a duplicate or an inconsistent dimension list is refused,
every reason at once. What it returns is only what the matcher's driver needs. **Excerpts and outcome terms
are parsed (so a malformed one is refused) and then dropped**, and so is every sentence: nothing here keeps
prose, so nothing the driver prints or writes can carry it.

**An uncertain call's alternative reading is a sentence in the committed rubrics**, which states its lines as
``line = number`` in words, not in TOML fields. The rubric reader checks that it is a non-empty string and
keeps the call's id only. The numbers come from ``alternatives.toml`` (``parse_alternatives``), a private
transcription beside the rubric, written before any case run (2026-10-27, his decision), checked number by
number against the sentence and hashed into a committed file. A call with no transcription is not matched.

Standard library only: this package cannot import the analysis (``tests/test_architecture.py``), so the driver
builds the matcher's ``CompanyDecision`` from what this returns.
"""

from __future__ import annotations

import math
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

NOT_OBSERVABLE = "not observable"
CHOICE_DIMENSION = "choice"

_TOP = frozenset(
    {
        "case",
        "shape",
        "cutoff",
        "scenario_total",
        "choice",
        "lines",
        "dimensions",
        "uncertain",
        "foreshadowing",
        "excerpts",
    }
)
_CHOICE = frozenset({"key", "company_choice", "observable", "excerpt_ids", "note"})
_LINE = frozenset({"label", "reading", "excerpt_ids", "note"})
_DIMENSIONS = frozenset({"observable", "excluded"})
_UNCERTAIN = frozenset({"id", "about", "reading", "alternative", "excerpt_ids"})
_FORESHADOWING = frozenset({"outcome_terms"})
_EXCERPT = frozenset({"id", "source", "text"})


class RubricError(Exception):
    """The rubric cannot be read as given. The message names every reason, never a value."""


@dataclass(frozen=True)
class UncertainCall:
    """An uncertain call, by id only: its prose is dropped."""

    id: str


@dataclass(frozen=True)
class Alternative:
    """An uncertain call's alternative reading as transcribed: the lines it makes observable, in the
    rubric's units. The choice is the primary reading's: no committed alternative changes it."""

    call: str
    amounts: Mapping[str, float]


@dataclass(frozen=True)
class Rubric:
    case: str
    shape: str  # as written; the scenario's id in upper or lower case
    scenario_total: int
    choice_key: str
    company_choice: str | None  # an option key, or None when the choice is not observable
    lines: Mapping[
        str, float | None
    ]  # every line the rubric lists, in its order; None = not observable
    observable: tuple[str, ...]
    excluded: tuple[str, ...]
    uncertain: tuple[UncertainCall, ...]

    @property
    def amounts(self) -> dict[str, float]:
        """The observable lines only, in the rubric's units (the matcher renormalizes them)."""
        return {key: value for key, value in self.lines.items() if value is not None}


def _keys(
    table: Mapping[str, Any],
    allowed: frozenset[str],
    where: str,
    problems: list[str],
    *,
    optional: frozenset[str] = frozenset(),
) -> None:
    extra = sorted(set(table) - allowed)
    missing = sorted(allowed - optional - set(table))
    if extra:
        problems.append(f"{where} has keys this form does not: {extra}")
    if missing:
        problems.append(f"{where} lacks keys: {missing}")


def _text(value: Any, where: str, problems: list[str]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        problems.append(f"{where} is not a non-empty string")
        return None
    return value


def _string(value: Any, where: str, problems: list[str]) -> None:
    if not isinstance(value, str):
        problems.append(f"{where} is not a string")


def _table(value: Any, where: str, problems: list[str]) -> Mapping[str, Any] | None:
    if not isinstance(value, dict):
        problems.append(f"{where} is not a table")
        return None
    return value


def _list(value: Any, where: str, problems: list[str]) -> list[Any]:
    if not isinstance(value, list):
        problems.append(f"{where} is not a list")
        return []
    return value


def _names(value: Any, where: str, problems: list[str]) -> list[str]:
    items = _list(value, where, problems)
    found = [item for item in items if isinstance(item, str) and item.strip()]
    if len(found) != len(items):
        problems.append(f"{where} holds something that is not a non-empty string")
    if len(set(found)) != len(found):
        problems.append(f"{where} repeats a name")
    return found


def _excerpt_ids(value: Any, where: str, known: set[str], problems: list[str]) -> None:
    ids = _names(value, f"{where}.excerpt_ids", problems)
    if not ids:
        problems.append(f"{where} cites no excerpt")
    unknown = sorted(set(ids) - known)
    if unknown:
        problems.append(f"{where} cites excerpts the rubric does not hold: {unknown}")


def _amount(value: Any, where: str, problems: list[str]) -> float | None:
    """A line's reading: "not observable" (None) or a finite, non-negative number."""
    if value == NOT_OBSERVABLE:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        problems.append(f"{where} is neither {NOT_OBSERVABLE!r} nor a number")
        return None
    if not math.isfinite(value) or value < 0:
        problems.append(f"{where} is negative or not finite")
        return None
    return float(value)


def parse_rubric(data: bytes) -> Rubric:
    """The rubric's bytes as stored. Refuses with every reason found."""
    try:
        raw = tomllib.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise RubricError(f"the rubric is not valid TOML ({type(exc).__name__})") from exc
    problems: list[str] = []
    _keys(raw, _TOP, "the rubric", problems, optional=frozenset({"uncertain"}))

    case = _text(raw.get("case"), "case", problems)
    shape = _text(raw.get("shape"), "shape", problems)
    _text(raw.get("cutoff"), "cutoff", problems)
    total = raw.get("scenario_total")
    if isinstance(total, bool) or not isinstance(total, int) or total <= 0:
        problems.append("scenario_total is not a positive whole number")
        total = 0

    excerpts = _list(raw.get("excerpts"), "excerpts", problems)
    known: set[str] = set()
    for i, excerpt in enumerate(excerpts):
        table = _table(excerpt, f"excerpts[{i}]", problems)
        if table is None:
            continue
        _keys(table, _EXCERPT, f"excerpts[{i}]", problems)
        excerpt_id = _text(table.get("id"), f"excerpts[{i}].id", problems)
        _string(table.get("source"), f"excerpts[{i}].source", problems)
        _string(table.get("text"), f"excerpts[{i}].text", problems)
        if excerpt_id is not None:
            if excerpt_id in known:
                problems.append("two excerpts share an id")
            known.add(excerpt_id)
    if not excerpts:
        problems.append("the rubric holds no excerpt")

    foreshadowing = _table(raw.get("foreshadowing"), "foreshadowing", problems)
    if foreshadowing is not None:
        _keys(foreshadowing, _FORESHADOWING, "foreshadowing", problems)
        _names(foreshadowing.get("outcome_terms"), "foreshadowing.outcome_terms", problems)

    choice_key: str | None = None
    company_choice: str | None = None
    choice_observable = False
    choice = _table(raw.get("choice"), "choice", problems)
    if choice is not None:
        _keys(choice, _CHOICE, "choice", problems)
        choice_key = _text(choice.get("key"), "choice.key", problems)
        observed = choice.get("observable")
        if not isinstance(observed, bool):
            problems.append("choice.observable is not true or false")
        else:
            choice_observable = observed
        said = _text(choice.get("company_choice"), "choice.company_choice", problems)
        if said is not None:
            if choice_observable and said == NOT_OBSERVABLE:
                problems.append(
                    f"choice.observable is true but company_choice is {NOT_OBSERVABLE!r}"
                )
            elif not choice_observable and said != NOT_OBSERVABLE:
                problems.append(
                    f"choice.observable is false but company_choice is not {NOT_OBSERVABLE!r}"
                )
            elif choice_observable:
                company_choice = said
        _string(choice.get("note"), "choice.note", problems)
        _excerpt_ids(choice.get("excerpt_ids"), "choice", known, problems)

    lines: dict[str, float | None] = {}
    table = _table(raw.get("lines"), "lines", problems)
    for key, entry in (table or {}).items():
        line = _table(entry, f"lines.{key}", problems)
        if line is None:
            continue
        _keys(line, _LINE, f"lines.{key}", problems)
        _string(line.get("label"), f"lines.{key}.label", problems)
        _string(line.get("note"), f"lines.{key}.note", problems)
        _excerpt_ids(line.get("excerpt_ids"), f"lines.{key}", known, problems)
        lines[key] = _amount(line.get("reading"), f"lines.{key}.reading", problems)
    if not lines:
        problems.append("the rubric lists no line")

    observable: list[str] = []
    excluded: list[str] = []
    dimensions = _table(raw.get("dimensions"), "dimensions", problems)
    if dimensions is not None:
        _keys(dimensions, _DIMENSIONS, "dimensions", problems)
        observable = _names(dimensions.get("observable"), "dimensions.observable", problems)
        excluded = _names(dimensions.get("excluded"), "dimensions.excluded", problems)
        expected_observable = {key for key, value in lines.items() if value is not None}
        expected_excluded = {key for key, value in lines.items() if value is None}
        if choice_observable:
            expected_observable.add(CHOICE_DIMENSION)
        else:
            expected_excluded.add(CHOICE_DIMENSION)
        if set(observable) != expected_observable or set(excluded) != expected_excluded:
            problems.append(
                "dimensions.observable and dimensions.excluded do not match what the choice and the "
                "lines say is observable"
            )

    calls: list[UncertainCall] = []
    uncertain = _list(raw.get("uncertain", []), "uncertain", problems)
    for i, entry in enumerate(uncertain):
        call = _table(entry, f"uncertain[{i}]", problems)
        if call is None:
            continue
        _keys(call, _UNCERTAIN, f"uncertain[{i}]", problems)
        call_id = _text(call.get("id"), f"uncertain[{i}].id", problems)
        for name in ("about", "reading", "alternative"):
            _text(call.get(name), f"uncertain[{i}].{name}", problems)
        _excerpt_ids(call.get("excerpt_ids"), f"uncertain[{i}]", known, problems)
        if call_id is not None:
            if any(c.id == call_id for c in calls):
                problems.append("two uncertain calls share an id")
            calls.append(UncertainCall(call_id))

    if problems or case is None or shape is None or choice_key is None:
        raise RubricError("; ".join(dict.fromkeys(problems)))
    return Rubric(
        case=case,
        shape=shape,
        scenario_total=total,
        choice_key=choice_key,
        company_choice=company_choice,
        lines=lines,
        observable=tuple(observable),
        excluded=tuple(excluded),
        uncertain=tuple(calls),
    )


def check_rubric_against(
    rubric: Rubric,
    *,
    label: str,
    scenario_id: str,
    scenario_total: int,
    choice_key: str | None,
    options: Sequence[str],
    lines: Sequence[str],
) -> list[str]:
    """What the rubric says against the scenario it was written for: the case label, the shape (the
    scenario's id, upper or lower case), the total, the choice key and its options, and exactly the scenario's
    lines. Every difference is named; the matcher's own checks come after these."""
    reasons: list[str] = []
    if rubric.case != label:
        reasons.append("the rubric is for another case than the one asked for")
    if rubric.shape.lower() != scenario_id:
        reasons.append(f"the rubric's shape is not the scenario's ({scenario_id})")
    if rubric.scenario_total != scenario_total:
        reasons.append(f"the rubric's scenario_total is not the scenario's ({scenario_total})")
    if choice_key is None or rubric.choice_key != choice_key:
        reasons.append("the rubric's choice key is not the scenario's")
    elif rubric.company_choice is not None and rubric.company_choice not in options:
        reasons.append(
            f"the company's choice is not one of the scenario's options ({sorted(options)})"
        )
    if set(rubric.lines) != set(lines):
        reasons.append(f"the rubric's lines are not the scenario's ({sorted(lines)})")
    return reasons


_ALTERNATIVES = frozenset({"case", "alternative"})
_ALTERNATIVE = frozenset({"call", "lines"})


def parse_alternatives(data: bytes, rubric: Rubric) -> tuple[Alternative, ...]:
    """``alternatives.toml``'s bytes, against the rubric they transcribe: each entry names one of the
    rubric's uncertain calls, once, and gives a number for each line it makes observable. Refuses with every
    reason found, never a value."""
    try:
        raw = tomllib.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise RubricError(f"alternatives.toml is not valid TOML ({type(exc).__name__})") from exc
    problems: list[str] = []
    _keys(raw, _ALTERNATIVES, "alternatives.toml", problems)
    if raw.get("case") != rubric.case:
        problems.append("alternatives.toml is for another case than the rubric")
    calls = {call.id for call in rubric.uncertain}
    found: list[Alternative] = []
    for i, entry in enumerate(_list(raw.get("alternative"), "alternative", problems)):
        where = f"alternative[{i}]"
        table = _table(entry, where, problems)
        if table is None:
            continue
        _keys(table, _ALTERNATIVE, where, problems)
        call = _text(table.get("call"), f"{where}.call", problems)
        if call is not None and call not in calls:
            problems.append(f"{where} names a call the rubric does not hold")
        if call is not None and any(a.call == call for a in found):
            problems.append(f"{where} repeats a call")
        amounts: dict[str, float] = {}
        lines = _table(table.get("lines"), f"{where}.lines", problems) or {}
        if not lines:
            problems.append(f"{where} makes no line observable")
        for key, value in lines.items():
            if key not in rubric.lines:
                problems.append(f"{where}.lines names a line the rubric does not list")
                continue
            if value == NOT_OBSERVABLE:
                problems.append(f"{where}.lines.{key} is not a number")
                continue
            amount = _amount(value, f"{where}.lines.{key}", problems)
            if amount is not None:
                amounts[key] = amount
        if call is not None:
            found.append(Alternative(call, amounts))
    if not found:
        problems.append("alternatives.toml transcribes no alternative")
    if problems:
        raise RubricError("; ".join(dict.fromkeys(problems)))
    return tuple(found)
