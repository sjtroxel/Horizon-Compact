"""The template and the renderer (Phase 2 IMPLEMENTATION doc section 6).

``dossier.template.txt`` is the board pack with ``{row_id}`` placeholders and **no digit characters** outside
them, so every digit in the rendered text came from a row. Two kinds of marker line start with ``@``: one
``@title`` and any number of ``@group`` lines, which tag the text that follows with a stakeholder group for
the balance report. Marker lines are never rendered.

From one template and one set of figures this module renders the model's version (no citations, decision 1),
the cited public version, and the figures and assumptions tables. ``hc dossier check`` re-renders and compares
byte for byte, so nobody edits an output by hand.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal
from string import Formatter

from horizon_compact.dossier.figures import FigureSet, Source, format_value

COMPANY_DIR = "experiment/company"
EVIDENCE_DIR = "docs/phases/evidence/phase-2"
TEMPLATE_PATH = f"{COMPANY_DIR}/dossier.template.txt"
DOSSIER_PATH = f"{COMPANY_DIR}/dossier.toml"
CITED_PATH = f"{EVIDENCE_DIR}/dossier-cited.md"
FIGURES_TABLE_PATH = f"{EVIDENCE_DIR}/figures-table.md"
ASSUMPTIONS_TABLE_PATH = f"{EVIDENCE_DIR}/assumptions-table.md"

# The stakeholder groups of the balance report (IMPLEMENTATION doc section 7, check 5). ``general`` is text
# that belongs to none of them.
GROUPS = ("general", "workforce", "customers", "suppliers", "shareholders", "environment")
TOKENS_PER_WORD = 1.35

_ID = re.compile(r"[a-z][a-z0-9_]*")


class TemplateError(Exception):
    """The template has a problem the renderer cannot get past."""


@dataclass(frozen=True)
class Piece:
    literal: str
    field: str | None = None


@dataclass(frozen=True)
class Line:
    group: str
    pieces: tuple[Piece, ...]


@dataclass(frozen=True)
class Template:
    title: str
    lines: tuple[Line, ...]

    def references(self) -> list[str]:
        """Every row id the template uses, in order of first appearance."""
        seen: dict[str, None] = {}
        for line in self.lines:
            for piece in line.pieces:
                if piece.field is not None:
                    seen.setdefault(piece.field)
        return list(seen)


def _digit_problem(text: str, line_no: int, what: str) -> str | None:
    for ch in text:
        if ch.isnumeric():
            return (
                f"line {line_no}: the {what} holds the digit {ch!r}; every number comes from a row"
            )
    return None


def scan_template(text: str) -> tuple[Template | None, list[str]]:
    """Parse the template and collect every problem (not only the first). The template is returned only if
    there are none."""
    problems: list[str] = []
    title: str | None = None
    group = "general"
    lines: list[Line] = []
    for line_no, raw in enumerate(text.splitlines(), start=1):
        if raw.startswith("@"):
            command, _, argument = raw[1:].partition(" ")
            argument = argument.strip()
            if command == "title":
                if title is not None:
                    problems.append(f"line {line_no}: a second @title")
                elif any(
                    piece.literal.strip() or piece.field for ln in lines for piece in ln.pieces
                ):
                    problems.append(f"line {line_no}: @title must come before the text")
                elif not argument or "{" in argument or "}" in argument:
                    problems.append(f"line {line_no}: @title needs plain text, no braces")
                else:
                    title = argument
                    problem = _digit_problem(argument, line_no, "title")
                    if problem:
                        problems.append(problem)
            elif command == "group":
                if argument in GROUPS:
                    group = argument
                else:
                    problems.append(
                        f"line {line_no}: unknown group {argument!r}; use one of {GROUPS}"
                    )
            else:
                problems.append(f"line {line_no}: unknown marker @{command}")
            continue
        try:
            parsed = list(Formatter().parse(raw))
        except ValueError as exc:
            problems.append(f"line {line_no}: {exc}")
            continue
        pieces: list[Piece] = []
        for literal, field, spec, conversion in parsed:
            problem = _digit_problem(literal, line_no, "text")
            if problem:
                problems.append(problem)
            if field is not None and (spec or conversion or not _ID.fullmatch(field)):
                problems.append(
                    f"line {line_no}: {{{field}}} is not a plain {{row_id}} placeholder"
                )
                field = None
            pieces.append(Piece(literal, field))
        lines.append(Line(group, tuple(pieces)))
    if title is None:
        problems.append("no @title line")
    if problems or title is None:
        return None, problems
    return Template(title, tuple(lines)), problems


def parse_template(text: str) -> Template:
    template, problems = scan_template(text)
    if template is None:
        raise TemplateError("; ".join(problems))
    return template


# --- numbering ---------------------------------------------------------------------------------------------


def labels(fs: FigureSet, template: Template) -> dict[str, str]:
    """The reference label for every row: assumptions are A1, A2, ... and derived rows D1, D2, ... in order of
    first appearance in the template, then the rest in file order. A sourced row's label is its source's."""
    order = [*template.references(), *fs.rows]
    out: dict[str, str] = {}
    counts = {"assumption": 0, "derived": 0}
    for key in dict.fromkeys(order):
        row = fs.rows.get(key)
        if row is None:
            continue
        if row.kind == "sourced":
            assert row.source is not None
            out[key] = fs.sources[row.source].short
        else:
            counts[row.kind] += 1
            prefix = "assumption A" if row.kind == "assumption" else "derived D"
            out[key] = f"{prefix}{counts[row.kind]}"
    return out


def _ordered_ids(fs: FigureSet, template: Template) -> list[str]:
    return [key for key in dict.fromkeys([*template.references(), *fs.rows]) if key in fs.rows]


# --- the text -----------------------------------------------------------------------------------------------


def _line_text(line: Line, fs: FigureSet, ref: dict[str, str] | None) -> str:
    parts: list[str] = []
    for piece in line.pieces:
        parts.append(piece.literal)
        if piece.field is not None:
            resolved = fs.resolved.get(piece.field)
            if resolved is None:
                raise TemplateError(
                    f"the template uses {piece.field!r}, which is not a row in figures.toml"
                )
            parts.append(resolved.shown)
            if ref is not None and resolved.row.unit != "label":
                parts.append(f" [{ref[piece.field]}]")
    return "".join(parts)


def render_text(template: Template, fs: FigureSet, *, cited: bool) -> str:
    ref = labels(fs, template) if cited else None
    out: list[str] = []
    for line in template.lines:
        text = _line_text(line, fs, ref)
        if text == "" and out and out[-1] == "":
            continue
        out.append(text)
    return "\n".join(out).strip("\n") + "\n"


def balance_report(template: Template, fs: FigureSet) -> dict[str, int]:
    """Words of rendered text per stakeholder group."""
    words = dict.fromkeys(GROUPS, 0)
    for line in template.lines:
        words[line.group] += len(_line_text(line, fs, None).split())
    return words


def estimated_tokens(words: int) -> int:
    """No Claude tokenizer without calling an official model, which this phase forbids: words x 1.35."""
    return round(words * TOKENS_PER_WORD)


# --- the outputs --------------------------------------------------------------------------------------------


def _toml_dossier(template: Template, text: str) -> str:
    if "'''" in text:
        raise TemplateError("the rendered text holds ''', which a TOML literal string cannot")
    return (
        "# RENDERED by `hc dossier render` from experiment/company/figures.toml and dossier.template.txt.\n"
        "# Do not edit by hand: `hc dossier check` fails if this file differs from a fresh render.\n\n"
        f"title = {json.dumps(template.title, ensure_ascii=False)}\n"
        f"text = '''\n{text}'''\n"
    )


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(_cell(cell) for cell in row) + " |" for row in rows]
    return "\n".join(lines) + "\n"


def _source_line(source: Source) -> str:
    return (
        f"- **{source.short}**: {source.publisher}, {source.title}. {source.edition}. Released "
        f"{source.released.isoformat()}, retrieved {source.retrieved.isoformat()}. {source.url} "
        f"Population: {source.population}. Terms: {source.terms}. Rows used: `{source.extract}`."
    )


def _cited_markdown(template: Template, fs: FigureSet) -> str:
    used: dict[str, None] = {}
    for key in template.references():
        row = fs.rows[key]
        for dependency in _sources_behind(fs, key):
            used.setdefault(dependency)
        if row.source:
            used.setdefault(row.source)
    sources = "\n".join(_source_line(fs.sources[name]) for name in used)
    return (
        f"# {template.title} (cited version)\n\n"
        "The text between the rules is the board pack the model reads, with a bracketed label after each "
        "number. A source name points to the list below; `assumption A#` rows are in "
        "`assumptions-table.md` with their ranges and reasons, and `derived D#` rows are in "
        "`figures-table.md` with their formulas.\n\n---\n\n"
        f"{render_text(template, fs, cited=True)}\n---\n\n## Sources\n\n{sources}\n"
    )


def _sources_behind(fs: FigureSet, key: str) -> list[str]:
    """Sources of every sourced row a derived row ultimately rests on."""
    found: list[str] = []
    for dependency in fs.references.get(key, frozenset()):
        row = fs.rows[dependency]
        if row.source:
            found.append(row.source)
        found += _sources_behind(fs, dependency)
    return found


def _figures_markdown(template: Template, fs: FigureSet, ref: dict[str, str]) -> str:
    rows: list[list[str]] = []
    for key in _ordered_ids(fs, template):
        row, resolved = fs.rows[key], fs.resolved[key]
        if row.kind == "sourced":
            assert row.source is not None
            basis = f"{fs.sources[row.source].short}: {row.locator}; read as {row.value}"
        elif row.kind == "assumption":
            basis = f"{ref[key]}: see assumptions-table.md"
        else:
            basis = f"{ref[key]}: {row.formula}"
        rows.append([f"`{key}`", row.label, resolved.shown, row.kind, basis])
    return (
        "# Figures\n\nEvery row behind the dossier. `As shown` is the value after rounding, which is the "
        "value later formulas use.\n\n"
        + _table(["ID", "Figure", "As shown", "Kind", "Basis"], rows)
    )


def _assumptions_markdown(template: Template, fs: FigureSet, ref: dict[str, str]) -> str:
    rows: list[list[str]] = []
    for key in _ordered_ids(fs, template):
        row, resolved = fs.rows[key], fs.resolved[key]
        assumption = row.assumption
        if assumption is None:
            continue
        if assumption.low is None or assumption.high is None:
            span = "none (a name, not a quantity)"
        else:
            low = format_value(row.unit, _decimal(assumption.low))
            high = format_value(row.unit, _decimal(assumption.high))
            span = f"{low} to {high}"
        rows.append(
            [
                ref[key].removeprefix("assumption "),
                f"{row.label} (`{key}`)",
                resolved.shown,
                span,
                assumption.range_from,
                assumption.reason,
                assumption.review or "",
            ]
        )
    return (
        "# Assumptions\n\nEvery figure that is a chosen value, not a source's. His review is recorded in "
        "`figures.toml` (the `review` line of each assumption) and rendered here; a changed value is changed "
        "there and re-rendered, never in this table.\n\n"
        + _table(
            [
                "ID",
                "Figure",
                "Value",
                "Range",
                "Where the range comes from",
                "Why this point",
                "His review",
            ],
            rows,
        )
    )


def _decimal(value: float) -> Decimal:
    return Decimal(str(value))


def render_outputs(template: Template, fs: FigureSet) -> dict[str, str]:
    """Every rendered file, keyed by its path relative to the repository root."""
    ref = labels(fs, template)
    return {
        DOSSIER_PATH: _toml_dossier(template, render_text(template, fs, cited=False)),
        CITED_PATH: _cited_markdown(template, fs),
        FIGURES_TABLE_PATH: _figures_markdown(template, fs, ref),
        ASSUMPTIONS_TABLE_PATH: _assumptions_markdown(template, fs, ref),
    }
