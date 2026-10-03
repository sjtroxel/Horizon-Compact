"""Parse the private term file and find its terms in text.

Pure functions over strings, plus the two file reads the term file itself requires (the term file, and the
longlist whose fingerprint it records). No git, no environment, no output: ``guard`` owns all of that, so
Phase 6's memo scan can import this module unchanged.

The term file format (Phase 0 IMPLEMENTATION doc §3), one directive per line::

    # comments on their own line only; a "#" inside a term is part of the term
    longlist: /absolute/path/to/the/longlist.md
    longlist-sha256: <64 hex characters>
    term: Exact Name
    term-i: Distinctive Name
    allow: Some Product Name

The matching rule (decision 3, made precise in the IMPLEMENTATION doc §4):

- allowed phrases are blanked out first, keeping line breaks so line numbers survive;
- a term matches only as a whole word: not preceded or followed by a letter or digit. Underscores and
  hyphens are separators, so a term inside ``a_name_here.md`` is still found;
- a space inside a term matches any run of whitespace, including a line break;
- ``term`` is case-sensitive, ``term-i`` is not.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

# A letter or digit: a word character that is not an underscore. Unicode-aware for str patterns.
_ALNUM = r"[^\W_]"
_SHA256 = re.compile(r"[0-9a-f]{64}")
_DIRECTIVES = frozenset({"longlist", "longlist-sha256", "term", "term-i", "allow"})


class TermFileError(Exception):
    """The term file, or the longlist it points to, cannot be trusted. The guard fails closed on this."""


@dataclass(frozen=True)
class Term:
    text: str
    ignore_case: bool
    pattern: re.Pattern[str]


@dataclass(frozen=True)
class TermFile:
    terms: tuple[Term, ...]
    allows: tuple[re.Pattern[str], ...]
    longlist: Path
    longlist_sha256: str


@dataclass(frozen=True)
class Match:
    term: str
    line: int
    column: int


def _phrase(text: str) -> str:
    """The regex for a phrase: each word escaped, any run of whitespace between words."""
    return r"\s+".join(re.escape(word) for word in text.split())


def compile_term(text: str, *, ignore_case: bool) -> Term:
    pattern = re.compile(
        rf"(?<!{_ALNUM}){_phrase(text)}(?!{_ALNUM})", re.IGNORECASE if ignore_case else 0
    )
    return Term(text=text, ignore_case=ignore_case, pattern=pattern)


def parse_term_file(text: str) -> TermFile:
    """Parse the term file's text. Every malformed line is an error; nothing is skipped silently."""
    terms: list[Term] = []
    allows: list[re.Pattern[str]] = []
    longlist: str | None = None
    digest: str | None = None

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if not sep or key not in _DIRECTIVES:
            raise TermFileError(f"term file line {lineno}: not a known directive")
        if not value:
            raise TermFileError(f"term file line {lineno}: '{key}' has no value")
        if key == "longlist":
            if longlist is not None:
                raise TermFileError(f"term file line {lineno}: a second 'longlist' line")
            longlist = value
        elif key == "longlist-sha256":
            if digest is not None:
                raise TermFileError(f"term file line {lineno}: a second 'longlist-sha256' line")
            if not _SHA256.fullmatch(value):
                raise TermFileError(
                    f"term file line {lineno}: 'longlist-sha256' is not 64 hex digits"
                )
            digest = value
        elif key == "allow":
            allows.append(re.compile(_phrase(value)))
        else:
            terms.append(compile_term(value, ignore_case=key == "term-i"))

    if longlist is None:
        raise TermFileError("term file has no 'longlist' line")
    if digest is None:
        raise TermFileError("term file has no 'longlist-sha256' line")
    if not terms:
        raise TermFileError("term file has no terms")
    return TermFile(
        terms=tuple(terms), allows=tuple(allows), longlist=Path(longlist), longlist_sha256=digest
    )


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_term_file(path: Path) -> TermFile:
    """Read and parse the term file, then check the longlist has not changed since it was written."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise TermFileError(f"cannot read the term file: {type(exc).__name__}") from exc
    term_file = parse_term_file(text)
    try:
        current = sha256_of(term_file.longlist)
    except OSError as exc:
        raise TermFileError(f"cannot read the longlist: {type(exc).__name__}") from exc
    if current != term_file.longlist_sha256:
        raise TermFileError(
            "the longlist has changed since the term file was written: revisit the term file, then "
            "update its longlist-sha256 line (print it with the guard's 'fingerprint' mode)"
        )
    return term_file


def _blank(match: re.Match[str]) -> str:
    return "".join("\n" if ch == "\n" else " " for ch in match.group())


def find_terms(text: str, term_file: TermFile) -> list[Match]:
    """Every term found in ``text`` after allowed phrases are blanked, in order of position."""
    for allow in term_file.allows:
        text = allow.sub(_blank, text)
    found: list[tuple[int, str]] = []
    for term in term_file.terms:
        found.extend((m.start(), term.text) for m in term.pattern.finditer(text))
    found.sort()
    matches = []
    for start, term_text in found:
        line_start = text.rfind("\n", 0, start) + 1
        matches.append(
            Match(
                term=term_text, line=text.count("\n", 0, start) + 1, column=start - line_start + 1
            )
        )
    return matches
