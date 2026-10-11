"""The reviewed-flags file: one decision per flag, or no dossier is assembled (IMPLEMENTATION §7 step 6).

On real text nearly every count ("twelve plants", "thirty-five countries") is a flag, and assembly refuses
while any flag stands. This file is how a person clears them, one line each, reading the flags and not the
dossier.

Where it lives: ``reviewed-flags.json`` in the case's appendix directory. ``prepare_case`` writes
``reviewed-flags.template.json`` beside it, one entry per flag with the decision and reason blank; he fills
those in and saves the copy under the real name.

An entry names its flag by four things, and all four must still match, so **an entry cannot outlive a change
to the text it was written about**: the section, the flag's kind, the line, the sha256 of the flagged text
and the sha256 of the whole line. Assembly passes only when every flag has exactly one entry and no entry is
left over.

Decisions: ``keep`` (the flagged text stays as written), ``edit`` (the flagged text, which must occur once
on its line, becomes ``replacement``) and ``remove`` (it is deleted). A flag with no flagged text (the
several-figures pay note) can only be kept. Each decision carries a reason in his words.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from horizon_compact.casebuild.transform import Flag

FLAGS_VERSION = 1
Key = tuple[int, str, int, str, str]


class ReviewError(Exception):
    """The reviewed-flags file is missing, malformed, stale or incomplete. The message lists every problem."""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FlagRef:
    """A flag, located in its section and tied to the text it was raised about."""

    section: int
    kind: str
    line: int
    text: str
    text_sha256: str
    line_sha256: str

    @property
    def key(self) -> Key:
        return (self.section, self.kind, self.line, self.text_sha256, self.line_sha256)

    def record(self) -> dict[str, object]:
        return {
            "section": self.section,
            "kind": self.kind,
            "line": self.line,
            "text": self.text,
            "text_sha256": self.text_sha256,
            "line_sha256": self.line_sha256,
        }


def flag_refs(sections: Mapping[int, str], flags: Mapping[int, Sequence[Flag]]) -> list[FlagRef]:
    """Every distinct flag, in section then line order. Two flags that agree on all five parts are one."""
    refs: dict[Key, FlagRef] = {}
    for section in sorted(flags):
        lines = sections[section].split("\n")
        for flag in sorted(flags[section], key=lambda f: (f.line, f.kind, f.text)):
            if not 1 <= flag.line <= len(lines):
                raise ReviewError(
                    f"section {section}: a flag names line {flag.line}, but the section has {len(lines)}"
                )
            ref = FlagRef(
                section=section,
                kind=flag.kind,
                line=flag.line,
                text=flag.text,
                text_sha256=_sha256(flag.text),
                line_sha256=_sha256(lines[flag.line - 1]),
            )
            refs.setdefault(ref.key, ref)
    return list(refs.values())


class ReviewEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    section: int
    kind: str
    line: int = Field(ge=1)
    text: str
    text_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    line_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    decision: Literal["keep", "edit", "remove"]
    reason: str = Field(min_length=1)
    replacement: str | None = None

    @property
    def key(self) -> Key:
        return (self.section, self.kind, self.line, self.text_sha256, self.line_sha256)


class ReviewedFlags(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    flags_version: int
    entries: list[ReviewEntry]


def template_text(refs: Sequence[FlagRef]) -> str:
    """The file a person fills in: every flag, ``decision`` and ``reason`` blank."""
    entries = [{**ref.record(), "decision": "", "reason": "", "replacement": None} for ref in refs]
    return json.dumps({"flags_version": FLAGS_VERSION, "entries": entries}, indent=2) + "\n"


def parse_reviewed(text: str, name: str = "reviewed-flags.json") -> ReviewedFlags:
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ReviewError(f"{name} is not valid JSON: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("flags_version") != FLAGS_VERSION:
        version = raw.get("flags_version") if isinstance(raw, dict) else None
        raise ReviewError(
            f"{name} has flags_version {version!r}; this reader knows {FLAGS_VERSION}"
        )
    try:
        return ReviewedFlags.model_validate(raw)
    except ValidationError as exc:
        fields = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )
        raise ReviewError(f"{name} is malformed: {fields}") from exc


def _describe(ref: FlagRef | ReviewEntry) -> str:
    return f"section {ref.section}, line {ref.line}, {ref.kind!r}, text {ref.text!r}"


def match_reviews(refs: Sequence[FlagRef], reviewed: ReviewedFlags) -> list[ReviewEntry]:
    """The entries, in flag order, once every flag has exactly one current entry. Raises with all problems."""
    problems: list[str] = []
    by_key: dict[Key, list[ReviewEntry]] = {}
    for entry in reviewed.entries:
        by_key.setdefault(entry.key, []).append(entry)
    current = {ref.key for ref in refs}
    for entry in reviewed.entries:
        if entry.key not in current:
            problems.append(f"stale entry, no such flag now: {_describe(entry)}")
        if _sha256(entry.text) != entry.text_sha256:
            problems.append(f"entry's text does not match its text_sha256: {_describe(entry)}")
        if entry.decision == "edit":
            if entry.replacement is None or "\n" in entry.replacement:
                problems.append(f"an edit needs a one-line replacement: {_describe(entry)}")
        elif entry.replacement is not None:
            problems.append(f"only an edit takes a replacement: {_describe(entry)}")
        if entry.decision != "keep" and not entry.text:
            problems.append(f"a flag with no flagged text can only be kept: {_describe(entry)}")
    ordered: list[ReviewEntry] = []
    for ref in refs:
        found = by_key.get(ref.key, [])
        if not found:
            problems.append(f"no decision for {_describe(ref)}")
        elif len(found) > 1:
            problems.append(f"{len(found)} entries for one flag: {_describe(ref)}")
        else:
            ordered.append(found[0])
    if problems:
        raise ReviewError(
            f"{len(problems)} problem(s) with the reviewed flags:\n  " + "\n  ".join(problems)
        )
    return ordered


def apply_decisions(sections: Mapping[int, str], entries: Sequence[ReviewEntry]) -> dict[int, str]:
    """The sections after every edit and removal. The flagged text must occur exactly once on its line."""
    lines = {section: text.split("\n") for section, text in sections.items()}
    problems: list[str] = []
    for entry in entries:
        if entry.decision == "keep":
            continue
        line = lines[entry.section][entry.line - 1]
        found = line.count(entry.text)
        if found == 0:
            # The transform rewrote what it flagged ("fiscal 2025" became "fiscal year N-1"), so there is
            # nothing left to edit or remove: the flag records an assumption, and it can only be kept.
            problems.append(
                "the flagged text is no longer on its line (the transform rewrote it), so this flag can "
                f"only be kept: {_describe(entry)}"
            )
            continue
        if found > 1:
            problems.append(
                f"the flagged text occurs {found} times on its line, not once: {_describe(entry)}"
            )
            continue
        lines[entry.section][entry.line - 1] = line.replace(
            entry.text,
            entry.replacement if entry.decision == "edit" and entry.replacement else "",
            1,
        )
    if problems:
        raise ReviewError("\n".join(problems))
    return {section: "\n".join(parts) for section, parts in lines.items()}
