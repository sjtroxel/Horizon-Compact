"""Prepare and assemble a case's dossier (IMPLEMENTATION §4.10, §7 step 6).

Two calls, because a person reads the flags between them and a model's reply is not repeatable:

``prepare_case`` runs the pipeline once, in order: the section inputs for the scenario shape, extraction,
sections 4 and 5's figures, section 7's options, then ``anonymize_and_scale`` on every section with **one**
factor (one seed from ``scale.new_seed``, never chosen, recorded) and **one** fiscal calendar (from the
latest year end of the figures). It writes, each once: ``sections.json`` (the anonymized text), the flags
template and ``build.json`` (last). It writes no dossier.

``assemble_case`` reads those back, checks the sections against the hash in ``build.json``, refuses unless
every flag has a current decision in ``reviewed-flags.json`` (``review.py``), applies the decisions, checks
that no term on the list has come back, and writes ``dossier.toml`` in the frozen format (``title`` and
``text``, as ``experiment/company/dossier.toml``) and ``assembly.json``.

A prepare that stops part-way leaves its files behind, which the write-once appendix will not overwrite: the
case directory is cleared by hand before a second try. That is the cost of "written once".

Nothing here fetches anything. Writing ``sources.json`` is ``documents.write_sources``, called by whoever
built the document set.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from horizon_compact.casebuild import extract, scale
from horizon_compact.casebuild.anonymize import anonymize_and_scale
from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.dates import FiscalCalendar
from horizon_compact.casebuild.documents import DocumentSet
from horizon_compact.casebuild.figures import render_section
from horizon_compact.casebuild.options import OptionFigure, build_options_section
from horizon_compact.casebuild.review import (
    FLAGS_VERSION,
    FlagRef,
    ReviewError,
    apply_decisions,
    flag_refs,
    match_reviews,
    parse_reviewed,
    template_text,
)
from horizon_compact.casebuild.sections import SHAPE_SECTIONS, HandBoundaries, build_section_inputs
from horizon_compact.casebuild.terms import CaseTerm, residual
from horizon_compact.casebuild.transform import Flag
from horizon_compact.providers.base import ModelRoute, TextProvider

BUILD_VERSION = 1
TITLE = "The Company: background for the decision"
HEADINGS = {
    1: "SECTION ONE: THE COMPANY",
    2: "SECTION TWO: SEGMENTS AND FACILITIES",
    3: "SECTION THREE: THE WORKFORCE",
    4: "SECTION FOUR: FINANCIAL POSITION",
    5: "SECTION FIVE: CAPITAL ALLOCATION",
    6: "SECTION SIX: THE SITUATION NOW",
    7: "SECTION SEVEN: THE OPTIONS",
}
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


class BuildError(Exception):
    """The pipeline cannot produce a dossier, or assembly was asked for something it must refuse."""


@dataclass(frozen=True)
class PreparedCase:
    label: str
    shape: str
    seed: int
    factor: float
    sections: dict[int, str]
    flags: list[FlagRef]
    record: dict[str, Any]


@dataclass(frozen=True)
class AssembledCase:
    dossier_sha256: str
    sections: dict[int, str]
    record: dict[str, Any]


def _sha256(data: bytes | str) -> str:
    raw = data.encode("utf-8") if isinstance(data, str) else data
    return hashlib.sha256(raw).hexdigest()


def _dump(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def _clean(text: str) -> tuple[str, int]:
    """Line endings made ``\\n`` and other control characters made spaces (a TOML literal string holds none).
    Returns the text and how many characters were replaced, for the record."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return _CONTROL.subn(" ", text)


def terms_sha256(terms: Sequence[CaseTerm]) -> str:
    """The term list as used: each term's text, its case rule and its role, in order. Recorded at prepare and
    checked at assembly, so the list that anonymized a case is the list its final check runs on."""
    canonical = [[t.term.text, t.term.ignore_case, t.role] for t in terms]
    return _sha256(json.dumps(canonical, ensure_ascii=False, separators=(",", ":")))


def _failed_pay_flags(checks: Sequence[Any]) -> list[Flag]:
    return [Flag(check.note, check.line, "") for check in checks if not check.passed]


def prepare_case(
    case: CaseAppendix,
    docset: DocumentSet,
    *,
    shape: str,
    terms: Sequence[CaseTerm],
    provider: TextProvider,
    route: ModelRoute,
    option_figures: Mapping[str, Sequence[OptionFigure]] | None = None,
    hand: HandBoundaries | None = None,
    new_seed: Callable[[], int] = scale.new_seed,
) -> PreparedCase:
    inputs = build_section_inputs(docset, shape=shape, hand=hand)
    requests = extract.build_requests(inputs)
    extracted = extract.run_extraction(provider, route, requests)
    if not inputs.figures.year_ends:
        raise BuildError(
            "no fiscal year has an admitted figure, so there is no calendar to date the case by"
        )
    calendar = FiscalCalendar(inputs.figures.year_ends[0])
    options = build_options_section(shape, option_figures or {}, docset.cutoff)

    raw: dict[int, str] = {}
    for number in SHAPE_SECTIONS[shape]:
        if number == 7:
            raw[number] = options.text
        elif number == 4:
            raw[number] = render_section(inputs.figures, 4)
        elif number == 5:
            pieces = [render_section(inputs.figures, 5)]
            if 5 in extracted:
                pieces.append(extracted[5].text)
            raw[number] = "\n\n".join(piece for piece in pieces if piece)
        elif number in extracted:
            raw[number] = extracted[number].text
        else:
            raise BuildError(f"section {number} has no text")
        if not raw[number].strip():
            raise BuildError(f"section {number} is empty: the filings gave nothing for it")

    seed = new_seed()
    factor = scale.draw_factor(seed)
    sections: dict[int, str] = {}
    flags: dict[int, list[Flag]] = {}
    section_records: dict[str, Any] = {}
    controls = 0
    for number, text in raw.items():
        text, replaced = _clean(text)
        controls += replaced
        done = anonymize_and_scale(text, terms=terms, calendar=calendar, factor=factor)
        assert done.transformed is not None
        sections[number] = done.text
        flags[number] = [*done.flags, *_failed_pay_flags(done.transformed.pay_checks)]
        section_records[str(number)] = {**done.record(), "sha256": _sha256(done.text)}
    refs = flag_refs(sections, flags)

    sections_bytes = _dump({str(n): sections[n] for n in sorted(sections)})
    record: dict[str, Any] = {
        "build_version": BUILD_VERSION,
        "label": case.label,
        "shape": shape,
        "terms_sha256": terms_sha256(terms),
        "seed": seed,
        "factor": factor,
        "fiscal_year_end": inputs.figures.year_ends[0].isoformat(),
        "cutoff": docset.cutoff.isoformat(),
        "control_characters_replaced": controls,
        "sections_sha256": _sha256(sections_bytes),
        "sections": section_records,
        "section_inputs": inputs.record,
        "extraction": {
            **extract.request_record(requests),
            "replies": {
                str(n): {
                    "model_id": e.model_id,
                    "prompt_sha256": e.prompt_sha256,
                    "usage": dataclasses.asdict(e.usage),
                }
                for n, e in sorted(extracted.items())
            },
        },
        "options": options.record,
        "flags": [ref.record() for ref in refs],
    }
    case.write_once(case.sections_path, sections_bytes)
    case.write_once(case.flags_template_path, template_text(refs).encode("utf-8"))
    case.write_once(case.build_path, _dump(record))
    return PreparedCase(case.label, shape, seed, factor, sections, refs, record)


def dossier_toml(sections: Mapping[int, str]) -> str:
    """The frozen format: ``title`` and ``text``. Sections in their fixed order under fixed headings."""
    body = "\n\n".join(f"{HEADINGS[n]}\n\n{sections[n].strip()}" for n in sorted(sections))
    text = f"\n{body}\n"
    if "'''" in text:
        raise BuildError("the dossier holds ''', which a TOML literal string cannot")
    if _CONTROL.search(text):
        raise BuildError(
            "the dossier holds a control character, which a TOML literal string cannot"
        )
    return f"title = {json.dumps(TITLE)}\ntext = '''{text}'''\n"


def _read_json(path: Any) -> Any:
    try:
        return json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read {path.name}: {exc}") from exc


def assemble_case(case: CaseAppendix, *, terms: Sequence[CaseTerm]) -> AssembledCase:
    """Refuse unless every flag has a current decision; else write ``dossier.toml`` and ``assembly.json``."""
    build = _read_json(case.build_path)
    if build.get("terms_sha256") != terms_sha256(terms):
        raise BuildError(
            "the term list is not the one the case was prepared with (its hash differs from build.json's)"
        )
    try:
        sections_bytes = case.sections_path.read_bytes()
    except OSError as exc:
        raise BuildError(f"cannot read {case.sections_path.name}: {exc}") from exc
    if _sha256(sections_bytes) != build.get("sections_sha256"):
        raise BuildError("sections.json does not hash to build.json: the prepared text has changed")
    sections = {int(k): v for k, v in json.loads(sections_bytes).items()}

    flag_list = build["flags"]
    by_section: dict[int, list[Flag]] = {}
    for item in flag_list:
        by_section.setdefault(item["section"], []).append(
            Flag(item["kind"], item["line"], item["text"])
        )
    refs = flag_refs(sections, by_section)
    if [ref.record() for ref in refs] != flag_list:
        raise BuildError("build.json's flags do not match the prepared sections")

    try:
        reviewed = parse_reviewed(_reviewed_text(case, refs), case.reviewed_flags_path.name)
        entries = match_reviews(refs, reviewed)
        final = apply_decisions(sections, entries)
    except ReviewError as exc:
        raise BuildError(str(exc)) from exc

    for number, text in final.items():
        back = residual(text, terms)
        if back:
            raise BuildError(
                f"section {number}: a listed term is present after the decisions were applied "
                f"(line {back[0][1]})"
            )
    dossier = dossier_toml(final)
    digest = _sha256(dossier)
    record: dict[str, Any] = {
        "build_sha256": _sha256(case.build_path.read_bytes()),
        "decisions": [
            {
                "section": e.section,
                "line": e.line,
                "kind": e.kind,
                "text_sha256": e.text_sha256,
                "decision": e.decision,
                "reason": e.reason,
            }
            for e in entries
        ],
        "sections_sha256": {str(n): _sha256(final[n]) for n in sorted(final)},
        "dossier_sha256": digest,
    }
    case.write_once(case.dossier_path, dossier.encode("utf-8"))
    case.write_once(case.assembly_path, _dump(record))
    return AssembledCase(digest, final, record)


def _reviewed_text(case: CaseAppendix, refs: Sequence[FlagRef]) -> str:
    path = case.reviewed_flags_path
    if path.is_file():
        return path.read_text(encoding="utf-8")
    if refs:
        raise ReviewError(
            f"{len(refs)} flag(s) have no decision: {path.name} does not exist. Fill in "
            f"{case.flags_template_path.name} and save it as {path.name}."
        )
    return json.dumps({"flags_version": FLAGS_VERSION, "entries": []})
