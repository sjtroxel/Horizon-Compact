"""One section through names, places, dates and scaling (Phase 5 code half, build step 5, §4.8)."""

from __future__ import annotations

from datetime import date

from horizon_compact.casebuild.anonymize import LIMIT_NOTE, anonymize_and_scale
from horizon_compact.casebuild.dates import FiscalCalendar
from horizon_compact.casebuild.terms import parse_case_terms

TERMS = parse_case_terms(
    "term: Fernwick Canary Holdings => the Company\n"
    "term: Fernwick => the Company\n"
    "term: Dayton => a town\n"
    "term: Marlow Quill => the chief executive\n"
)
CALENDAR = FiscalCalendar(date(2025, 12, 31))


def run(text: str):  # type: ignore[no-untyped-def]
    return anonymize_and_scale(text, terms=TERMS, calendar=CALENDAR, factor=1.2)


def test_a_section_goes_through_every_step_in_order() -> None:
    result = run(
        "Fernwick Canary Holdings, led by Marlow Quill, makes cages in Dayton, Ohio. "
        "In the fiscal year ended December 31, 2025 it had revenue of $1,500.0 million."
    )
    assert result.text == (
        "the Company, led by the chief executive, makes cages in a town, the East North Central region. "
        "In fiscal year N it had revenue of $1,800 million."
    )
    assert result.flags == []
    assert result.names_replaced == {"Fernwick Canary Holdings": 1, "Marlow Quill": 1, "Dayton": 1}


def test_a_town_on_the_list_is_replaced_before_places_so_it_is_not_taken_for_a_state() -> None:
    terms = parse_case_terms("term: Kansas City => a town")
    result = anonymize_and_scale(
        "Sites in Kansas City and Kansas.", terms=terms, calendar=CALENDAR, factor=1.2
    )
    assert result.text == "Sites in a town and the West North Central region."
    assert result.flags == []


def test_an_unlisted_state_city_is_flagged_for_the_list() -> None:
    result = run("A site in Oklahoma City.")
    assert result.text == "A site in Oklahoma City."
    assert [f.kind for f in result.flags] == [
        "a state word followed by City: add the town to the term list"
    ]


def test_a_term_the_roles_bring_back_is_flagged() -> None:
    terms = parse_case_terms("term: Canary Cage => Canary Cage Works")
    result = anonymize_and_scale("Canary Cage grew.", terms=terms, calendar=CALENDAR, factor=1.2)
    assert [f.kind for f in result.flags] == ["a term from the list is still present"]


def test_the_record_says_what_the_term_list_cannot_catch() -> None:
    record = run("Fernwick makes cages. Payroll was $70.0 million for 1,240 employees.").record()
    assert record["note"] == LIMIT_NOTE
    assert "Anything the list misses" in LIMIT_NOTE
    assert record["names_replaced"] == {"Fernwick": 1}
    assert record["counts"] == {"dollar": 1, "headcount": 1}
    assert len(record["pay_checks"]) == 1
    assert record["flags"] == []


def test_the_same_factor_scales_a_dollar_total_and_its_headcount_together() -> None:
    first = run("Payroll was $70.0 million for 1,240 employees.")
    assert first.transformed is not None and first.transformed.pay_checks[0].passed


def test_a_state_abbreviation_after_a_listed_town_is_replaced_not_left() -> None:
    """Abbreviations go before names: "a town, OH" would otherwise keep the state (Opus review)."""
    terms = parse_case_terms("term: Dayton => a town\nterm: Kansas City => a town")
    result = anonymize_and_scale(
        "Plants in Dayton, OH and Kansas City, MO.", terms=terms, calendar=CALENDAR, factor=1.2
    )
    assert result.text == (
        "Plants in a town, the East North Central region and a town, the West North Central region."
    )
    assert result.flags == []
