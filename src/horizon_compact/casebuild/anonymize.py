"""One section's text through names, places, dates and scaling (IMPLEMENTATION §4.8), in that order.

The order matters: postal abbreviations first ("Dayton, OH" needs its capitalized town to be recognized), then
names (so a town on the term list is never mistaken for a state), then state and province names, then the
single pass over dates and numbers (``transform.py``). Whatever is still unsettled afterwards is a flag,
and a term from the list still present in the output is a flag too.

**What this cannot do, and says so in its record:** anything the term list misses is the human review's and
the recognition probe's to catch. The builder makes the first pass mechanical; it does not certify the result.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from horizon_compact.casebuild.dates import FiscalCalendar
from horizon_compact.casebuild.terms import (
    CaseTerm,
    replace_abbreviations,
    replace_place_names,
    replace_terms,
    residual,
)
from horizon_compact.casebuild.transform import Flag, Transformed, transform

LIMIT_NOTE = (
    "Names are replaced only from the case's term list. Anything the list misses, and any description "
    "distinctive enough to identify the company, is for the human review and the recognition probe."
)


@dataclass
class AnonymizedSection:
    text: str
    names_replaced: dict[str, int]
    flags: list[Flag] = field(default_factory=list)
    transformed: Transformed | None = None

    def record(self) -> dict[str, object]:
        assert self.transformed is not None
        return {
            "names_replaced": dict(sorted(self.names_replaced.items())),
            **self.transformed.record(),
            "flags": [{"kind": f.kind, "line": f.line, "text": f.text} for f in self.flags],
            "note": LIMIT_NOTE,
        }


def anonymize_and_scale(
    text: str, *, terms: Sequence[CaseTerm], calendar: FiscalCalendar, factor: float
) -> AnonymizedSection:
    text = replace_abbreviations(text)
    text, replaced = replace_terms(text, terms)
    text, city_flags = replace_place_names(text)
    moved = transform(text, calendar=calendar, factor=factor)
    flags = [
        Flag("a state word followed by City: add the town to the term list", line, name)
        for name, line in city_flags
    ]
    flags.extend(moved.flags)
    flags.extend(
        Flag("a term from the list is still present", line, name)
        for name, line in residual(moved.text, terms)
    )
    return AnonymizedSection(
        text=moved.text, names_replaced=replaced, flags=flags, transformed=moved
    )
