"""Name replacement from a case's private term list (IMPLEMENTATION §4.8).

Every term on the case's list (company, former names, brands, products, executives, towns) is replaced by a
neutral role, matched exactly as the name guard matches (``privacy.names.compile_term``: whole words, spaces
match any whitespace, ``term`` case-sensitive and ``term-i`` not), so the two cannot drift apart. The longest
term is replaced first, so "Fernwick Canary Holdings" goes before "Fernwick".

The list lives in the private appendix, one directive per line::

    # a comment on its own line
    term: Fernwick Canary Holdings => the Company
    term-i: Perchmaster => a product line

**Anything the list misses is the human review's and the recognition probe's to catch.** This module says so
in its report, and ``residual`` is the one check it can make: a term still present after replacement.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from horizon_compact.privacy.names import Term, compile_term


class CaseTermsError(Exception):
    """The case's term list is malformed."""


@dataclass(frozen=True)
class CaseTerm:
    term: Term
    role: str


def parse_case_terms(text: str) -> tuple[CaseTerm, ...]:
    terms: list[CaseTerm] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, rest = line.partition(":")
        key = key.strip()
        if not sep or key not in ("term", "term-i"):
            raise CaseTermsError(f"term list line {lineno}: not a 'term' or 'term-i' directive")
        name, arrow, role = rest.partition("=>")
        name, role = name.strip(), role.strip()
        if not arrow or not name or not role:
            raise CaseTermsError(f"term list line {lineno}: expected 'term: Name => role'")
        terms.append(CaseTerm(term=compile_term(name, ignore_case=key == "term-i"), role=role))
    if not terms:
        raise CaseTermsError("the term list has no terms")
    return tuple(terms)


def _constant(value: str) -> Callable[[re.Match[str]], str]:
    return lambda _match: value


def replace_terms(text: str, terms: Iterable[CaseTerm]) -> tuple[str, dict[str, int]]:
    """The text with every term replaced by its role, and how many times each was replaced."""
    counts: dict[str, int] = {}
    for case_term in sorted(terms, key=lambda t: len(t.term.text), reverse=True):
        text, count = case_term.term.pattern.subn(_constant(case_term.role), text)
        if count:
            counts[case_term.term.text] = counts.get(case_term.term.text, 0) + count
    return text, counts


def residual(text: str, terms: Iterable[CaseTerm]) -> list[tuple[str, int]]:
    """Terms still present after replacement, with line numbers. Empty when the replacement was whole."""
    found: list[tuple[str, int]] = []
    for case_term in terms:
        for match in case_term.term.pattern.finditer(text):
            found.append((case_term.term.text, text.count("\n", 0, match.start()) + 1))
    return sorted(found, key=lambda item: item[1])


# --- places: states and provinces become census regions (a fixed table) -----------------------------------

_DIVISIONS: dict[str, tuple[str, ...]] = {
    "New England": (
        "Connecticut",
        "Maine",
        "Massachusetts",
        "New Hampshire",
        "Rhode Island",
        "Vermont",
    ),
    "Middle Atlantic": ("New Jersey", "New York", "Pennsylvania"),
    "East North Central": ("Illinois", "Indiana", "Michigan", "Ohio", "Wisconsin"),
    "West North Central": (
        "Iowa",
        "Kansas",
        "Minnesota",
        "Missouri",
        "Nebraska",
        "North Dakota",
        "South Dakota",
    ),
    "South Atlantic": (
        "Delaware",
        "District of Columbia",
        "Florida",
        "Georgia",
        "Maryland",
        "North Carolina",
        "South Carolina",
        "Virginia",
        "West Virginia",
    ),
    "East South Central": ("Alabama", "Kentucky", "Mississippi", "Tennessee"),
    "West South Central": ("Arkansas", "Louisiana", "Oklahoma", "Texas"),
    "Mountain": (
        "Arizona",
        "Colorado",
        "Idaho",
        "Montana",
        "Nevada",
        "New Mexico",
        "Utah",
        "Wyoming",
    ),
    "Pacific": ("Alaska", "California", "Hawaii", "Oregon", "Washington"),
}
CENSUS_REGIONS: dict[str, str] = {
    "New England": "Northeast",
    "Middle Atlantic": "Northeast",
    "East North Central": "Midwest",
    "West North Central": "Midwest",
    "South Atlantic": "South",
    "East South Central": "South",
    "West South Central": "South",
    "Mountain": "West",
    "Pacific": "West",
}
_ABBREVIATIONS: dict[str, str] = {
    "CT": "Connecticut", "ME": "Maine", "MA": "Massachusetts", "NH": "New Hampshire", "RI": "Rhode Island",
    "VT": "Vermont", "NJ": "New Jersey", "NY": "New York", "PA": "Pennsylvania", "IL": "Illinois",
    "IN": "Indiana", "MI": "Michigan", "OH": "Ohio", "WI": "Wisconsin", "IA": "Iowa", "KS": "Kansas",
    "MN": "Minnesota", "MO": "Missouri", "NE": "Nebraska", "ND": "North Dakota", "SD": "South Dakota",
    "DE": "Delaware", "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "MD": "Maryland",
    "NC": "North Carolina", "SC": "South Carolina", "VA": "Virginia", "WV": "West Virginia", "AL": "Alabama",
    "KY": "Kentucky", "MS": "Mississippi", "TN": "Tennessee", "AR": "Arkansas", "LA": "Louisiana",
    "OK": "Oklahoma", "TX": "Texas", "AZ": "Arizona", "CO": "Colorado", "ID": "Idaho", "MT": "Montana",
    "NV": "Nevada", "NM": "New Mexico", "UT": "Utah", "WY": "Wyoming", "AK": "Alaska", "CA": "California",
    "HI": "Hawaii", "OR": "Oregon", "WA": "Washington",
}  # fmt: skip
_PROVINCES = (
    "Alberta",
    "British Columbia",
    "Manitoba",
    "New Brunswick",
    "Newfoundland and Labrador",
    "Nova Scotia",
    "Ontario",
    "Prince Edward Island",
    "Quebec",
    "Saskatchewan",
    "Yukon",
    "Northwest Territories",
    "Nunavut",
)
PLACE_TO_DIVISION: dict[str, str] = {
    state: division for division, states in _DIVISIONS.items() for state in states
}
_NAMES = sorted([*PLACE_TO_DIVISION, *_PROVINCES], key=len, reverse=True)
_ALNUM = r"[^\W_]"
# A state or province name as a whole word; "Kansas City"-style names are left for the human (flagged).
_PLACE = re.compile(
    rf"(?<!{_ALNUM})({'|'.join(re.escape(n) for n in _NAMES)})(?!{_ALNUM})(?!\s+City\b)"
)
_PLACE_CITY = re.compile(rf"(?<!{_ALNUM})(?:{'|'.join(re.escape(n) for n in _NAMES)})\s+City\b")
# "Dayton, OH": a postal abbreviation after a capitalized word and a comma, never a bare "OH" or "IN".
_ABBREVIATION = re.compile(rf"([A-Z][A-Za-z.]*),\s+({'|'.join(_ABBREVIATIONS)})(?!{_ALNUM})")


def place_label(name: str) -> str:
    if name in PLACE_TO_DIVISION:
        return f"the {PLACE_TO_DIVISION[name]} region"
    return "Canada"


def replace_abbreviations(text: str) -> str:
    """``Dayton, OH`` becomes ``Dayton, the East North Central region``.

    Run before the term list: once a town is replaced by its role ("a town"), the capitalized word this rule
    needs is gone and ", OH" would be left in place (Opus review, 2026-10-11).
    """
    return _ABBREVIATION.sub(
        lambda m: f"{m.group(1)}, {place_label(_ABBREVIATIONS[m.group(2)])}", text
    )


def replace_place_names(text: str) -> tuple[str, list[tuple[str, int]]]:
    """State and province names become regions. Returns the text and the places flagged.

    Run after the term list, so a town such as "Kansas City" on the list is replaced first. Flagged, not
    replaced: a state word followed by "City" that the list did not hold.
    """
    flagged = [(m.group(0), text.count("\n", 0, m.start()) + 1) for m in _PLACE_CITY.finditer(text)]
    return _PLACE.sub(lambda m: place_label(m.group(1)), text), flagged


def replace_places(text: str) -> tuple[str, list[tuple[str, int]]]:
    """Both passes, abbreviations first, for text with no term list."""
    return replace_place_names(replace_abbreviations(text))
