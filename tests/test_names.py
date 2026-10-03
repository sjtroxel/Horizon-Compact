"""Tests for the term-file parser and matcher.

Every name here is a fictional canary (Phase 0 IMPLEMENTATION doc §7). No real company name may ever appear
in a test: this file is itself committed through the guard.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from horizon_compact.privacy.names import (
    Match,
    TermFile,
    TermFileError,
    find_terms,
    load_term_file,
    parse_term_file,
    sha256_of,
)

DIGEST = "0" * 64
CANARY_TERMS = f"""\
# fictional canaries only
longlist: /nonexistent/longlist.md
longlist-sha256: {DIGEST}
term: Quillmere Fastening
term-i: Zarnothic
term: QXZW
term: Fenwick Hollow
term: Brask-Ollen & Vey
allow: Quillmere Fastening Cloud Suite
"""


@pytest.fixture
def canaries() -> TermFile:
    return parse_term_file(CANARY_TERMS)


def terms_in(text: str, term_file: TermFile) -> list[str]:
    return [m.term for m in find_terms(text, term_file)]


# --- matching ----------------------------------------------------------------


def test_whole_word_match(canaries: TermFile) -> None:
    assert terms_in("A plant run by Quillmere Fastening closed.", canaries) == [
        "Quillmere Fastening"
    ]


def test_case_sensitive_term_misses_other_capitalization(canaries: TermFile) -> None:
    assert terms_in("quillmere fastening, QUILLMERE FASTENING", canaries) == []


@pytest.mark.parametrize("text", ["Zarnothic", "zarnothic", "ZARNOTHIC", "zArNoThIc"])
def test_ignore_case_term_matches_any_capitalization(canaries: TermFile, text: str) -> None:
    assert terms_in(f"see {text} here", canaries) == ["Zarnothic"]


def test_possessive_matches(canaries: TermFile) -> None:
    assert terms_in("Fenwick Hollow's plant", canaries) == ["Fenwick Hollow"]


def test_curly_possessive_matches(canaries: TermFile) -> None:
    text = "Fenwick Hollow\N{RIGHT SINGLE QUOTATION MARK}s plant"
    assert terms_in(text, canaries) == ["Fenwick Hollow"]


@pytest.mark.parametrize("text", ["Zarnothics", "preZarnothic", "Zarnothic2", "QXZWA", "AQXZW"])
def test_plural_substring_and_digit_neighbours_miss(canaries: TermFile, text: str) -> None:
    assert terms_in(text, canaries) == []


@pytest.mark.parametrize(
    "text",
    [
        "(QXZW)",
        "QXZW,",
        "QXZW.",
        "`QXZW`",
        "**QXZW**",
        "QXZW\n",
        "notes/QXZW/x",
        "a_QXZW_b",
        "a-QXZW-b",
    ],
)
def test_punctuation_underscore_and_hyphen_are_separators(canaries: TermFile, text: str) -> None:
    assert terms_in(text, canaries) == ["QXZW"]


def test_snake_case_file_name_is_caught(canaries: TermFile) -> None:
    assert terms_in("docs/cases/zarnothic_plant_closure.md", canaries) == ["Zarnothic"]


def test_multi_word_term_across_a_line_break(canaries: TermFile) -> None:
    text = "the closure announced by Quillmere\nFastening in August"
    assert find_terms(text, canaries) == [Match(term="Quillmere Fastening", line=1, column=26)]


def test_multi_word_term_with_extra_spaces(canaries: TermFile) -> None:
    assert terms_in("Fenwick   Hollow", canaries) == ["Fenwick Hollow"]


def test_multi_word_term_does_not_match_a_single_word(canaries: TermFile) -> None:
    assert terms_in("Fenwick alone, Hollow alone", canaries) == []


def test_punctuation_inside_a_term(canaries: TermFile) -> None:
    assert terms_in("acquired by Brask-Ollen & Vey.", canaries) == ["Brask-Ollen & Vey"]


def test_allowed_phrase_is_blanked(canaries: TermFile) -> None:
    assert terms_in("We deploy on Quillmere Fastening Cloud Suite.", canaries) == []


def test_allowed_phrase_across_a_line_break_is_blanked(canaries: TermFile) -> None:
    assert terms_in("on Quillmere Fastening\nCloud Suite today", canaries) == []


def test_term_next_to_an_allowed_phrase_is_still_caught(canaries: TermFile) -> None:
    text = "Quillmere Fastening Cloud Suite is fine; Quillmere Fastening the company is not."
    assert terms_in(text, canaries) == ["Quillmere Fastening"]


def test_blanking_keeps_line_numbers(canaries: TermFile) -> None:
    text = "Quillmere Fastening\nCloud Suite\nthen QXZW"
    assert find_terms(text, canaries) == [Match(term="QXZW", line=3, column=6)]


def test_every_match_is_reported_in_order(canaries: TermFile) -> None:
    text = "QXZW first\nthen zarnothic\nand Fenwick Hollow and QXZW again"
    assert find_terms(text, canaries) == [
        Match(term="QXZW", line=1, column=1),
        Match(term="Zarnothic", line=2, column=6),
        Match(term="Fenwick Hollow", line=3, column=5),
        Match(term="QXZW", line=3, column=24),
    ]


def test_clean_text_has_no_matches(canaries: TermFile) -> None:
    assert find_terms("A fictional company closes a plant in a Midwest town.", canaries) == []


def test_regex_metacharacters_in_terms_are_literal() -> None:
    term_file = parse_term_file(
        f"longlist: /x\nlonglist-sha256: {DIGEST}\nterm: Vey (Holdings)\nterm: A.B.\n"
    )
    assert terms_in("Vey (Holdings) and A.B. and AxB.", term_file) == ["Vey (Holdings)", "A.B."]


# --- parsing: every malformed line is an error, never a silent skip -----------


@pytest.mark.parametrize(
    ("text", "message"),
    [
        (f"longlist-sha256: {DIGEST}\nterm: X\n", "no 'longlist' line"),
        ("longlist: /x\nterm: X\n", "no 'longlist-sha256' line"),
        (f"longlist: /x\nlonglist-sha256: {DIGEST}\n", "no terms"),
        (f"longlist: /x\nlonglist-sha256: {DIGEST}\nallow: Y\n", "no terms"),
        (f"longlist: /x\nlonglist-sha256: {DIGEST}\nterm X\n", "line 3: not a known directive"),
        (f"longlist: /x\nlonglist-sha256: {DIGEST}\nterms: X\n", "line 3: not a known directive"),
        (f"longlist: /x\nlonglist-sha256: {DIGEST}\nterm:\n", "line 3: 'term' has no value"),
        (f"longlist: /x\nlonglist-sha256: {DIGEST}\nterm:   \n", "line 3: 'term' has no value"),
        ("longlist: /x\nlonglist-sha256: abc\nterm: X\n", "not 64 hex digits"),
        (f"longlist: /x\nlonglist-sha256: {DIGEST.upper()}A\nterm: X\n", "not 64 hex digits"),
        (f"longlist: /x\nlonglist: /y\nlonglist-sha256: {DIGEST}\nterm: X\n", "second 'longlist'"),
        (
            f"longlist: /x\nlonglist-sha256: {DIGEST}\nlonglist-sha256: {DIGEST}\nterm: X\n",
            "second 'longlist-sha256'",
        ),
    ],
)
def test_malformed_term_file_is_an_error(text: str, message: str) -> None:
    with pytest.raises(TermFileError, match=message):
        parse_term_file(text)


def test_parse_errors_never_echo_the_line(canaries: TermFile) -> None:
    """An error message may reach a log; it names the line number, never the line's content."""
    with pytest.raises(TermFileError) as exc:
        parse_term_file(f"longlist: /x\nlonglist-sha256: {DIGEST}\nQuillmere Fastening\n")
    assert "Quillmere" not in str(exc.value)


def test_comments_and_blank_lines_are_ignored() -> None:
    term_file = parse_term_file(
        f"\n# a comment\n   # indented comment\nlonglist: /x\n\nlonglist-sha256: {DIGEST}\nterm: QXZW\n"
    )
    assert [t.text for t in term_file.terms] == ["QXZW"]


def test_a_hash_inside_a_term_is_part_of_the_term() -> None:
    term_file = parse_term_file(f"longlist: /x\nlonglist-sha256: {DIGEST}\nterm: Vey #2\n")
    assert [t.text for t in term_file.terms] == ["Vey #2"]


# --- loading: the longlist fingerprint ----------------------------------------


def write_pair(tmp_path: Path, longlist_text: str, digest: str | None = None) -> Path:
    longlist = tmp_path / "longlist.md"
    longlist.write_text(longlist_text, encoding="utf-8")
    digest = digest or hashlib.sha256(longlist.read_bytes()).hexdigest()
    terms = tmp_path / "terms.txt"
    terms.write_text(
        f"longlist: {longlist}\nlonglist-sha256: {digest}\nterm: QXZW\n", encoding="utf-8"
    )
    return terms


def test_load_succeeds_when_the_fingerprint_matches(tmp_path: Path) -> None:
    term_file = load_term_file(write_pair(tmp_path, "a fictional longlist\n"))
    assert [t.text for t in term_file.terms] == ["QXZW"]


def test_load_fails_closed_when_the_longlist_changed(tmp_path: Path) -> None:
    terms = write_pair(tmp_path, "a fictional longlist\n")
    (tmp_path / "longlist.md").write_text(
        "a fictional longlist, plus one candidate\n", encoding="utf-8"
    )
    with pytest.raises(TermFileError, match="longlist has changed"):
        load_term_file(terms)


def test_resaving_the_longlist_unchanged_does_not_trip_the_fingerprint(tmp_path: Path) -> None:
    terms = write_pair(tmp_path, "a fictional longlist\n")
    (tmp_path / "longlist.md").write_text("a fictional longlist\n", encoding="utf-8")
    load_term_file(terms)


def test_load_fails_closed_when_the_longlist_is_missing(tmp_path: Path) -> None:
    terms = write_pair(tmp_path, "x\n")
    (tmp_path / "longlist.md").unlink()
    with pytest.raises(TermFileError, match="cannot read the longlist"):
        load_term_file(terms)


def test_load_fails_closed_when_the_term_file_is_missing(tmp_path: Path) -> None:
    with pytest.raises(TermFileError, match="cannot read the term file"):
        load_term_file(tmp_path / "absent.txt")


def test_load_fails_closed_when_the_term_file_is_not_utf8(tmp_path: Path) -> None:
    path = tmp_path / "terms.txt"
    path.write_bytes(b"\xff\xfe\x00bad")
    with pytest.raises(TermFileError, match="cannot read the term file"):
        load_term_file(path)


def test_sha256_of_matches_hashlib(tmp_path: Path) -> None:
    path = tmp_path / "f"
    path.write_bytes(b"abc")
    assert sha256_of(path) == hashlib.sha256(b"abc").hexdigest()
