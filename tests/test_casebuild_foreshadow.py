"""The foreshadowing check (Phase 5 code half, build step 6)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.foreshadow import (
    ForeshadowError,
    find_hits,
    format_hits,
    parse_terms,
    write_hits,
)

TERMS = "# the outcome's key terms\nclosure\nLay Off\n\n"


def test_terms_are_one_per_line_and_comments_and_blank_lines_are_skipped() -> None:
    assert [t.text for t in parse_terms(TERMS)] == ["closure", "Lay Off"]
    with pytest.raises(ForeshadowError):
        parse_terms("# nothing\n\n")


def test_a_hit_is_a_whole_word_in_any_case_with_its_line() -> None:
    texts = {
        "dossier": "Plans.\nA Closure was not discussed.\nEnclosure is a noun.",
        "scenario": "lay  off",
    }
    hits = find_hits(texts, parse_terms(TERMS))
    assert [(h.source, h.line, h.term) for h in hits] == [
        ("dossier", 2, "closure"),
        ("scenario", 1, "Lay Off"),
    ]
    assert "A Closure was not discussed." in format_hits(hits)


def test_a_term_that_wraps_across_a_line_break_is_found_at_the_line_it_starts() -> None:
    """Opus review of step 6: a line-by-line search passed this text with no hit."""
    hits = find_hits(
        {"scenario": "Intro.\nthe plant\nclosure was\nnot named"}, parse_terms("plant closure\n")
    )
    assert [(h.line, h.term, h.text) for h in hits] == [
        (2, "plant closure", "the plant closure was")
    ]


def test_a_term_twice_on_one_line_is_one_hit_and_each_line_is_its_own() -> None:
    hits = find_hits({"dossier": "closure, closure\nclosure"}, parse_terms("closure\n"))
    assert [h.line for h in hits] == [1, 2]


def test_no_hits_is_an_empty_list() -> None:
    assert find_hits({"dossier": "Nothing here."}, parse_terms(TERMS)) == []


def test_each_run_writes_a_new_numbered_file_with_hashes_and_the_terms_found(
    tmp_path: Path,
) -> None:
    case = CaseAppendix(root=tmp_path, label="closure-1")
    texts = {"dossier": "a closure", "scenario": "b"}
    hits = find_hits(texts, parse_terms(TERMS))
    assert write_hits(case, hits, terms_text=TERMS, texts=texts) == "foreshadow-1.json"
    assert write_hits(case, [], terms_text=TERMS, texts=texts) == "foreshadow-2.json"
    first = (case.directory / "foreshadow-1.json").read_text(encoding="utf-8")
    record = json.loads(first)
    assert len(record["hits"]) == 1 and len(record["terms_sha256"]) == 64
    assert record["hits"][0]["term"] == "closure"
    assert "Lay Off" not in first  # a term with no hit is recorded only through the list's hash
