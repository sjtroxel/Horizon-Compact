"""Prepare and assemble on synthetic filings and a fake provider (Phase 5 code half, build step 6)."""

from __future__ import annotations

import hashlib
import json
import tomllib
from datetime import date
from pathlib import Path

import pytest

from edgar_helpers import CANARY_CIK, FACTS_URL, facts_file, world
from horizon_compact.casebuild import scale
from horizon_compact.casebuild.appendix import AppendixError, CaseAppendix
from horizon_compact.casebuild.assemble import (
    HEADINGS,
    BuildError,
    PreparedCase,
    assemble_case,
    dossier_toml,
    prepare_case,
    terms_sha256,
)
from horizon_compact.casebuild.documents import DocumentSet, build_document_set
from horizon_compact.casebuild.options import OptionFigure
from horizon_compact.casebuild.terms import parse_case_terms
from test_casebuild_extract import FACTS, ROUTE, FakeTextProvider, ok

CUTOFF = date(2026, 6, 15)
TERMS = parse_case_terms("term: Fernwick Canary Holdings => the Company\n")
PLAIN = "Fernwick Canary Holdings had revenue of $100.0 million."
COUNTS = "Fernwick Canary Holdings makes cages in 35 countries and had revenue of $100.0 million."


class Scripted(FakeTextProvider):
    """Every reply is ``reply``, or ``replies[section]`` for the section whose request this is."""

    def __init__(self, reply: str, replies: dict[int, str] | None = None) -> None:
        super().__init__()
        self.reply = reply
        self.replies = replies or {}
        self.sections = [1, 2, 3, 5, 6]

    def decide_text(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return ok(self.replies.get(self.sections[len(self.requests) - 1], self.reply))


def setup(tmp_path: Path, facts: bytes = FACTS) -> tuple[CaseAppendix, DocumentSet]:
    client, _ = world(tmp_path, {FACTS_URL: facts})
    return (
        CaseAppendix(root=tmp_path, label="closure-1"),
        build_document_set(client, CANARY_CIK, CUTOFF),
    )


def prepare(
    tmp_path: Path, reply: str = PLAIN, *, shape: str = "S3", seed: int = 7, **kwargs: object
) -> tuple[CaseAppendix, PreparedCase]:
    case, docset = setup(tmp_path)
    provider = Scripted(reply, kwargs.pop("replies", None))  # type: ignore[arg-type]
    if shape != "S3":
        provider.sections = {"S4": [1, 5, 6], "S1": [1, 3, 6], "S2": [1, 3, 5, 6]}[shape]
    prepared = prepare_case(
        case,
        docset,
        shape=shape,
        terms=TERMS,
        provider=provider,
        route=ROUTE,
        new_seed=lambda: seed,
        **kwargs,  # type: ignore[arg-type]
    )
    return case, prepared


def fill_in(
    case: CaseAppendix, decision: str = "keep", changes: dict[str, dict[str, object]] | None = None
) -> None:
    template = json.loads(case.flags_template_path.read_text(encoding="utf-8"))
    for entry in template["entries"]:
        entry.update(decision=decision, reason="checked by hand")
        entry.update((changes or {}).get(entry["text"], {}))
    case.reviewed_flags_path.write_text(json.dumps(template), encoding="utf-8")


def test_prepare_writes_the_sections_the_flags_template_and_build_json_and_no_dossier(
    tmp_path: Path,
) -> None:
    case, prepared = prepare(tmp_path)
    assert case.sections_path.is_file() and case.flags_template_path.is_file()
    assert case.build_path.is_file()
    assert not case.dossier_path.exists()
    assert sorted(prepared.sections) == [1, 2, 3, 4, 5, 6, 7]
    build = json.loads(case.build_path.read_text(encoding="utf-8"))
    assert build["seed"] == 7 and build["factor"] == scale.draw_factor(7) == prepared.factor
    assert build["shape"] == "S3" and build["label"] == "closure-1"
    assert build["fiscal_year_end"] == "2026-01-31"


def test_build_json_holds_every_record_the_notes_name(tmp_path: Path) -> None:
    case, _ = prepare(tmp_path)
    build = json.loads(case.build_path.read_text(encoding="utf-8"))
    for key in ("sections", "section_inputs", "extraction", "options", "flags", "sections_sha256"):
        assert key in build, key
    assert "figures" in build["section_inputs"] and "annual_split" in build["section_inputs"]
    assert build["extraction"]["instructions_sha256"] and build["extraction"]["sections"] == [
        1,
        2,
        3,
        5,
        6,
    ]
    assert set(build["extraction"]["replies"]) == {"1", "2", "3", "5", "6"}
    assert build["options"]["shape"] == "S3"
    for record in build["sections"].values():
        assert {"names_replaced", "counts", "flags", "pay_checks", "note", "sha256"} <= set(record)


def test_one_factor_and_one_calendar_run_through_every_section(tmp_path: Path) -> None:
    reply = "Fernwick Canary Holdings had revenue of $100.0 million in the fiscal year ended January 31, 2026."
    _, prepared = prepare(tmp_path, reply)
    scaled = f"${100.0 * prepared.factor:.1f} million"
    for number in (1, 2, 3, 6):
        assert scaled in prepared.sections[number], number
        assert "in fiscal year N." in prepared.sections[number]
        assert "Fernwick" not in prepared.sections[number]
    assert scaled in prepared.sections[5]  # the acquisitions text, after the figures


def test_the_seed_is_drawn_by_the_given_function_not_chosen(tmp_path: Path) -> None:
    drawn: list[int] = []

    def seeds() -> int:
        drawn.append(scale.new_seed())
        return drawn[-1]

    case, docset = setup(tmp_path)
    prepared = prepare_case(
        case, docset, shape="S3", terms=TERMS, provider=Scripted(PLAIN), route=ROUTE, new_seed=seeds
    )
    assert len(drawn) == 1 and prepared.seed == drawn[0]
    default = prepare_case.__kwdefaults__["new_seed"]  # type: ignore[index]
    assert default is scale.new_seed


def test_build_json_is_written_once(tmp_path: Path) -> None:
    case, docset = setup(tmp_path)
    kwargs = {"shape": "S3", "terms": TERMS, "route": ROUTE}
    prepare_case(case, docset, provider=Scripted(PLAIN), **kwargs)  # type: ignore[arg-type]
    with pytest.raises(AppendixError, match="write-once"):
        prepare_case(case, docset, provider=Scripted(PLAIN), **kwargs)  # type: ignore[arg-type]


def test_a_case_with_no_flags_assembles_without_a_reviewed_file(tmp_path: Path) -> None:
    case, prepared = prepare(tmp_path)
    assert prepared.flags == []
    assembled = assemble_case(case, terms=TERMS)
    parsed = tomllib.loads(case.dossier_path.read_text(encoding="utf-8"))
    assert set(parsed) == {"title", "text"}
    positions = [parsed["text"].index(HEADINGS[n]) for n in range(1, 8)]
    assert positions == sorted(positions)
    assert hashlib.sha256(case.dossier_path.read_bytes()).hexdigest() == assembled.dossier_sha256
    record = json.loads(case.assembly_path.read_text(encoding="utf-8"))
    assert record["dossier_sha256"] == assembled.dossier_sha256 and record["decisions"] == []


def test_the_dossier_text_has_no_name_and_no_digit_in_a_heading(tmp_path: Path) -> None:
    case, _ = prepare(tmp_path)
    assemble_case(case, terms=TERMS)
    text = tomllib.loads(case.dossier_path.read_text(encoding="utf-8"))["text"]
    assert "Fernwick" not in text
    assert not any(c.isdigit() for h in HEADINGS.values() for c in h)


def test_assembly_refuses_while_a_flag_has_no_decision_and_says_where_the_template_is(
    tmp_path: Path,
) -> None:
    case, prepared = prepare(tmp_path, COUNTS)
    assert prepared.flags and all(f.text == "35" for f in prepared.flags)
    with pytest.raises(BuildError, match=r"have no decision.*reviewed-flags\.template\.json"):
        assemble_case(case, terms=TERMS)
    assert not case.dossier_path.exists() and not case.assembly_path.exists()


def test_a_reviewed_file_still_holding_the_templates_blanks_is_refused(tmp_path: Path) -> None:
    case, _ = prepare(tmp_path, COUNTS)
    case.reviewed_flags_path.write_text(
        case.flags_template_path.read_text(encoding="utf-8"), encoding="utf-8"
    )
    with pytest.raises(BuildError, match="malformed"):
        assemble_case(case, terms=TERMS)


def test_assembly_passes_once_every_flag_has_a_decision_and_records_them(tmp_path: Path) -> None:
    case, prepared = prepare(tmp_path, COUNTS)
    fill_in(case)
    assembled = assemble_case(case, terms=TERMS)
    assert "35 countries" in assembled.sections[1]  # kept as written
    record = json.loads(case.assembly_path.read_text(encoding="utf-8"))
    assert len(record["decisions"]) == len(prepared.flags)
    assert {d["decision"] for d in record["decisions"]} == {"keep"}


def test_edit_and_remove_decisions_are_applied_before_the_dossier_is_written(
    tmp_path: Path,
) -> None:
    case, prepared = prepare(tmp_path, COUNTS, replies={2: COUNTS.replace("35", "36")})
    fill_in(case, "edit", {"35": {"replacement": "many"}, "36": {"decision": "remove"}})
    assemble_case(case, terms=TERMS)
    text = tomllib.loads(case.dossier_path.read_text(encoding="utf-8"))["text"]
    assert "35" not in text and "36" not in text and "many countries" in text
    assert any(f.text == "36" for f in prepared.flags)


def test_an_edit_that_brings_a_listed_term_back_is_refused(tmp_path: Path) -> None:
    case, _ = prepare(tmp_path, COUNTS)
    fill_in(case, "edit", {"35": {"replacement": "Fernwick Canary Holdings"}})
    with pytest.raises(BuildError, match="listed term is present"):
        assemble_case(case, terms=TERMS)
    assert not case.dossier_path.exists()


def test_a_stale_entry_is_refused(tmp_path: Path) -> None:
    case, _ = prepare(tmp_path, COUNTS)
    fill_in(case)
    reviewed = json.loads(case.reviewed_flags_path.read_text(encoding="utf-8"))
    reviewed["entries"][0]["line_sha256"] = "0" * 64
    case.reviewed_flags_path.write_text(json.dumps(reviewed), encoding="utf-8")
    with pytest.raises(BuildError, match="stale entry"):
        assemble_case(case, terms=TERMS)


def test_a_file_of_entries_with_no_flags_to_match_is_refused(tmp_path: Path) -> None:
    case, _ = prepare(tmp_path)
    case.reviewed_flags_path.write_text(
        json.dumps(
            {
                "flags_version": 1,
                "entries": [
                    {
                        "section": 1,
                        "kind": "k",
                        "line": 1,
                        "text": "x",
                        "text_sha256": hashlib.sha256(b"x").hexdigest(),
                        "line_sha256": "0" * 64,
                        "decision": "keep",
                        "reason": "r",
                        "replacement": None,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(BuildError, match="stale entry"):
        assemble_case(case, terms=TERMS)


def test_assembly_refuses_a_term_list_other_than_the_one_prepare_used(tmp_path: Path) -> None:
    """Opus review of step 6: the list was not recorded, so assembly could check against another one."""
    case, prepared = prepare(tmp_path)
    assert prepared.record["terms_sha256"] == terms_sha256(TERMS)
    other = parse_case_terms(
        "term: Fernwick Canary Holdings => the Company\nterm: Quill => a person\n"
    )
    with pytest.raises(BuildError, match="not the one the case was prepared with"):
        assemble_case(case, terms=other)
    relabelled = parse_case_terms("term: Fernwick Canary Holdings => the firm\n")
    assert terms_sha256(relabelled) != terms_sha256(TERMS)
    assert not case.dossier_path.exists()


def test_changed_sections_json_is_refused(tmp_path: Path) -> None:
    case, _ = prepare(tmp_path)
    case.sections_path.write_text(
        case.sections_path.read_text(encoding="utf-8") + " ", encoding="utf-8"
    )
    with pytest.raises(BuildError, match=r"does not hash to build\.json"):
        assemble_case(case, terms=TERMS)


def test_assembling_twice_is_refused_by_the_write_once_appendix(tmp_path: Path) -> None:
    case, _ = prepare(tmp_path)
    assemble_case(case, terms=TERMS)
    with pytest.raises(AppendixError, match="write-once"):
        assemble_case(case, terms=TERMS)


def test_only_the_shapes_sections_are_built(tmp_path: Path) -> None:
    _, prepared = prepare(tmp_path / "s4", shape="S4")
    assert sorted(prepared.sections) == [1, 4, 5, 6, 7]
    _, prepared = prepare(tmp_path / "s1", shape="S1")
    assert sorted(prepared.sections) == [1, 3, 4, 6, 7]


def test_section_7_takes_part_in_scaling_and_the_equal_treatment_rule(tmp_path: Path) -> None:
    from horizon_compact.casebuild.cutoff import FilingStamp

    early = FilingStamp(filed=date(2026, 3, 2), label="0009999999-26-000001")
    figures = {
        "close": [OptionFigure("one-time cost of $20.0 million", early)],
        "retool": [OptionFigure("capital cost of $30.0 million, once", early)],
        "sell": [OptionFigure("proceeds of $12.0 million", early)],
    }
    _, prepared = prepare(tmp_path, option_figures=figures)
    assert f"${20.0 * prepared.factor:.1f} million" in prepared.sections[7]
    _, stripped = prepare(tmp_path / "x", option_figures={"close": figures["close"]})
    assert "$" not in stripped.sections[7]


def test_a_case_with_no_admitted_fiscal_year_is_refused(tmp_path: Path) -> None:
    case, docset = setup(tmp_path, json.dumps(facts_file({})).encode())
    with pytest.raises(BuildError, match="no calendar"):
        prepare_case(case, docset, shape="S3", terms=TERMS, provider=Scripted(PLAIN), route=ROUTE)
    assert not case.build_path.exists()


def test_control_characters_become_spaces_and_are_counted(tmp_path: Path) -> None:
    case, prepared = prepare(tmp_path, "Revenue was $100.0 million.\x0cMore text.\r\nNext.")
    assert "\x0c" not in prepared.sections[1] and "\r" not in prepared.sections[1]
    assert prepared.record["control_characters_replaced"] == 5
    assemble_case(case, terms=TERMS)


def test_the_dossier_format_is_title_and_text_and_refuses_what_a_literal_string_cannot_hold() -> (
    None
):
    parsed = tomllib.loads(dossier_toml({1: "One.", 4: "Four."}))
    assert set(parsed) == {"title", "text"}
    assert parsed["text"].startswith(HEADINGS[1]) and parsed["text"].endswith("Four.\n")
    with pytest.raises(BuildError, match="'''"):
        dossier_toml({1: "a ''' b"})
    with pytest.raises(BuildError, match="control character"):
        dossier_toml({1: "a\x1b b"})
