"""The foreshadowing check as a tool (IMPLEMENTATION §4.10, ``planning/07`` §10).

The outcome's key terms are written in the rubric, which the builder never reads. A person copies them into
a plain file, one term per line (``#`` starts a comment), and ``hc case foreshadow`` searches the dossier
and the scenario text for each, whole words, any case. **Every hit is justified in writing or removed**:
this module lists the hits and does not judge them. The list is written to the case's appendix directory,
never overwritten (``foreshadow-1.json``, ``foreshadow-2.json`` and so on), with the hash of the term list
and of each text it read, so a later run is a new record rather than a changed one. Each hit names its term,
so the record holds every term that was found (the appendix is private).

**Each text is searched whole, not line by line**, since the guard's matcher lets a space in a term match any
whitespace: a term that wraps across a line break is still found, and reported at the line where it starts
with every line it spans (Opus review of step 6: a line-by-line search missed it).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.privacy.names import Term, compile_term


class ForeshadowError(Exception):
    """The term list is empty or a text cannot be read."""


@dataclass(frozen=True)
class Hit:
    source: str  # "dossier" or "scenario"
    line: int
    term: str
    text: str  # every line the match spans, for the justification


def parse_terms(text: str) -> tuple[Term, ...]:
    terms = tuple(
        compile_term(line.strip(), ignore_case=True)
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    )
    if not terms:
        raise ForeshadowError("the term list has no terms")
    return terms


def _lines_spanned(text: str, start: int, end: int) -> str:
    first = text.rfind("\n", 0, start) + 1
    last = text.find("\n", end)
    return " ".join(text[first : last if last != -1 else len(text)].split())


def find_hits(texts: Mapping[str, str], terms: Sequence[Term]) -> list[Hit]:
    """One hit per term per line it starts on, in source, line and term-list order."""
    hits: list[Hit] = []
    for source in sorted(texts):
        text = texts[source]
        found: dict[tuple[int, int], Hit] = {}
        for index, term in enumerate(terms):
            for match in term.pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                found.setdefault(
                    (line, index),
                    Hit(source, line, term.text, _lines_spanned(text, match.start(), match.end())),
                )
        hits.extend(found[key] for key in sorted(found))
    return hits


def format_hits(hits: Sequence[Hit]) -> str:
    return "\n".join(f"{h.source} line {h.line}: {h.term!r}: {h.text}" for h in hits)


def write_hits(
    case: CaseAppendix, hits: Sequence[Hit], *, terms_text: str, texts: Mapping[str, str]
) -> str:
    """Write the next ``foreshadow-<n>.json``; returns its name."""
    number = 1
    while (case.directory / f"foreshadow-{number}.json").exists():
        number += 1
    name = f"foreshadow-{number}.json"
    record = {
        "terms_sha256": hashlib.sha256(terms_text.encode("utf-8")).hexdigest(),
        "texts_sha256": {
            k: hashlib.sha256(v.encode("utf-8")).hexdigest() for k, v in sorted(texts.items())
        },
        "hits": [
            {"source": h.source, "line": h.line, "term": h.term, "text": h.text} for h in hits
        ],
        "justification": "each hit needs one, in writing, or the text is changed and the check run again",
    }
    case.write_once(case.directory / name, (json.dumps(record, indent=2) + "\n").encode("utf-8"))
    return name
