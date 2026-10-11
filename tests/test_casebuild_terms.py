"""Name replacement from a case's term list, and places to regions (Phase 5 code half, build step 5, §4.8)."""

from __future__ import annotations

import pytest

from horizon_compact.casebuild.terms import (
    CaseTermsError,
    parse_case_terms,
    replace_places,
    replace_terms,
    residual,
)
from horizon_compact.privacy.names import compile_term

TERMS = """
# a case's private list (these are canaries)
term: Fernwick Canary Holdings => the Company
term: Fernwick => the Company
term-i: Perchmaster => a product line
term: Marlow Quill => the chief executive
"""


def test_the_list_is_parsed_into_terms_with_roles() -> None:
    terms = parse_case_terms(TERMS)
    assert [t.term.text for t in terms] == [
        "Fernwick Canary Holdings",
        "Fernwick",
        "Perchmaster",
        "Marlow Quill",
    ]
    assert terms[2].term.ignore_case and not terms[0].term.ignore_case


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "# only a comment",
        "term: Name",
        "term: => the Company",
        "name: X => y",
        "term Fernwick => y",
        "term: X =>",
    ],
)
def test_a_malformed_list_is_an_error(bad: str) -> None:
    with pytest.raises(CaseTermsError):
        parse_case_terms(bad)


def test_the_longest_term_is_replaced_first() -> None:
    terms = parse_case_terms(TERMS)
    text, counts = replace_terms(
        "Fernwick Canary Holdings, or Fernwick for short, sells Perchmaster.", terms
    )
    assert text == "the Company, or the Company for short, sells a product line."
    assert counts == {"Fernwick Canary Holdings": 1, "Fernwick": 1, "Perchmaster": 1}


def test_possessives_whole_words_and_case_follow_the_guards_rules() -> None:
    terms = parse_case_terms(TERMS)
    text, _ = replace_terms(
        "Fernwick's plants; Fernwickian ones stay; PERCHMASTER and perchmaster; fernwick.", terms
    )
    assert (
        text
        == "the Company's plants; Fernwickian ones stay; a product line and a product line; fernwick."
    )


def test_a_space_matches_a_line_break_and_an_underscore_is_a_separator() -> None:
    """The guard's rules, which the replacement shares: a break between the words is a space; "_" is not."""
    terms = parse_case_terms(TERMS)
    text, _ = replace_terms("see Marlow\nQuill and x_Marlow Quill_y and Marlow_Quill", terms)
    assert text == "see the chief executive and x_the chief executive_y and Marlow_Quill"


def test_the_replacement_uses_the_guards_own_matcher() -> None:
    """One pattern, not two: the term compiled by the guard's function is the term replaced."""
    case_term = parse_case_terms("term: Fernwick => the Company")[0]
    assert (
        case_term.term.pattern.pattern
        == compile_term("Fernwick", ignore_case=False).pattern.pattern
    )


def test_residual_finds_a_term_the_roles_brought_back() -> None:
    terms = parse_case_terms("term: Canary Cage => Canary Cage Works")
    text, _ = replace_terms("We make Canary Cage products.", terms)
    assert residual(text, terms) == [("Canary Cage", 1)]
    clean = parse_case_terms("term: Canary Cage => the Company")
    text, _ = replace_terms("We make Canary Cage products.", clean)
    assert residual(text, clean) == []


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("a plant in Ohio", "a plant in the East North Central region"),
        (
            "offices in Texas and California",
            "offices in the West South Central region and the Pacific region",
        ),
        ("a site in Ontario", "a site in Canada"),
        ("Dayton, OH is the largest", "Dayton, the East North Central region is the largest"),
        ("Tulsa, OK", "Tulsa, the West South Central region"),
        ("New Hampshire and Hampshire", "the New England region and Hampshire"),
        ("West Virginia and Virginia", "the South Atlantic region and the South Atlantic region"),
        ("Washington", "the Pacific region"),
    ],
)
def test_states_provinces_and_abbreviations_become_regions(text: str, expected: str) -> None:
    assert replace_places(text)[0] == expected


def test_a_bare_abbreviation_that_is_also_a_word_is_left_alone() -> None:
    text = "IN the OR case, OH my: is it 'or' in Ohioan? Not Dayton OH either."
    assert replace_places(text)[0] == text


def test_a_state_word_before_city_is_flagged_not_replaced() -> None:
    text, flagged = replace_places("sites in Kansas City and Oklahoma City, and Kansas")
    assert text == "sites in Kansas City and Oklahoma City, and the West North Central region"
    assert flagged == [("Kansas City", 1), ("Oklahoma City", 1)]


def test_flagged_places_carry_their_line() -> None:
    _, flagged = replace_places("one\ntwo\nNew York City")
    assert flagged == [("New York City", 3)]


def test_the_two_place_passes_can_run_apart_with_names_between_them() -> None:
    from horizon_compact.casebuild.terms import replace_abbreviations, replace_place_names

    assert replace_abbreviations("Dayton, OH") == "Dayton, the East North Central region"
    assert replace_place_names("a town in Ohio")[0] == "a town in the East North Central region"
