"""What the reader is shown, and nothing else (protocol §12.9; search-half doc §4.9).

Each builder returns the user message of one kind of read and the hash of every part in it. The fixed brief is
the system text. There is no parameter by which a result, a probe answer, a selection reason, a log entry or a
case's name could be added: a builder reads named files of the case's folder and the shape's template, and
this module imports nothing that holds a result (``tests/test_architecture.py`` checks the imports).

* ``rejection``: the criterion and the candidate's first-disclosure excerpt, placed by hand in the case's
  folder. Not the drafter's reason, not the recorded result: an independent read starts blind.
* ``scenario``: the shape's template, the rendered scenario, what the render dropped and set, and a table of
  where each figure came from. Not the unscaled values, the scaling factor or an accession number (the table
  numbers the filings 1, 2, ... in order of first use); the factor and the hashes are removed from the render
  record.
  A scenario that does not pass ``hc case scenario check`` is not sent.
* ``rubric``: the rubric file, whole, with its excerpts.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.scenario import (
    CaseRow,
    ScenarioRefused,
    check_scenario,
    format_failures,
    parse_rows,
)
from horizon_compact.experiment import SOURCE_SUFFIX
from horizon_compact.scenarios.render import SCENARIOS_DIR

MAX_PART_CHARS = 200_000
# The render record's fields that are private (the scaling factor, protocol §12.6) or only a checksum.
_PRIVATE_RECORD_FIELDS = ("factor", "build_sha256", "rows_sha256")
REJECTION_CRITERIA = ("real_decision", "maps_to_shape")


class MaterialError(Exception):
    """What a read needs is missing or not fit to send. The message names a file or a rule, never a value."""


@dataclass(frozen=True)
class Material:
    kind: str
    criterion: str | None
    user: str
    parts: dict[str, str]  # part name -> sha256 of the text sent


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_text(path: Path, what: str) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise MaterialError(f"{what} cannot be read: {path.name} ({type(exc).__name__})") from exc
    if not text.strip():
        raise MaterialError(f"{what} is empty: {path.name}")
    if len(text) > MAX_PART_CHARS:
        raise MaterialError(f"{what} is too long to send ({path.name}): cut it down first")
    return text


def _block(name: str, text: str) -> str:
    return f"[{name}]\n{text.strip()}\n[end of {name}]"


def _assemble(kind: str, criterion: str | None, blocks: list[tuple[str, str]]) -> Material:
    head = f"Criterion to read: {criterion}\n\n" if criterion else ""
    user = head + "\n\n".join(_block(name, text) for name, text in blocks)
    return Material(kind, criterion, user, {name: _sha256(text) for name, text in blocks})


def rejection_material(case: CaseAppendix, criterion: str) -> Material:
    if criterion not in REJECTION_CRITERIA:
        raise MaterialError(
            f"{criterion!r} is not a criterion the reader reads from an excerpt: "
            f"{', '.join(REJECTION_CRITERIA)} (a probe failure is read at the probe step)"
        )
    excerpt = _read_text(case.reader_excerpt_path, "the first-disclosure excerpt")
    return _assemble("rejection", criterion, [("Excerpt", excerpt)])


def _provenance_table(rows: dict[str, CaseRow], set_to_total: set[str]) -> str:
    """One line per row. A cap the render set to the total (``equals_total``, or a stated cap under 100,
    treated as unstated) is marked so, since the scenario prints the total, not that row's figure."""
    filings: dict[str, int] = {}
    lines = ["row | unit | scale | source"]
    for key, row in rows.items():
        if row.equals_total or key in set_to_total:
            lines.append(f"{key} | - | - | set equal to the total: no source states it")
            continue
        scale = f"{row.scale}" + (f" (per {row.per})" if row.per else "")
        if row.source == "first_disclosure":
            source = f"the first-disclosure document, {row.locator}"
        else:
            number = filings.setdefault(str(row.accession), len(filings) + 1)
            source = f"a filing dated before the first disclosure (filing {number}), {row.locator}"
        lines.append(f"{key} | {row.unit} | {scale} | {source}")
    return "\n".join(lines)


def _render_record(case: CaseAppendix) -> dict[str, object]:
    raw = _read_text(case.scenario_render_path, "the render record")
    try:
        record = json.loads(raw)
    except ValueError as exc:
        raise MaterialError(
            f"the render record is not valid JSON: {case.scenario_render_path.name}"
        ) from exc
    if not isinstance(record, dict):
        raise MaterialError("the render record is not a JSON object")
    return record


def _public_render_record(record: dict[str, object]) -> str:
    public = {k: v for k, v in record.items() if k not in _PRIVATE_RECORD_FIELDS}
    return json.dumps(public, indent=2, sort_keys=True)


def _caps_set_to_total(record: dict[str, object]) -> set[str]:
    caps = record.get("caps_set_to_total", [])
    if not isinstance(caps, list) or not all(isinstance(c, dict) and "row" in c for c in caps):
        raise MaterialError("the render record's caps_set_to_total cannot be read")
    return {str(c["row"]) for c in caps}


def scenario_material(case: CaseAppendix, repo_root: Path) -> Material:
    failures = check_scenario(case, repo_root)
    if failures:
        raise MaterialError(
            "the scenario does not pass `hc case scenario check`, so it is not sent: "
            + "; ".join(format_failures(failures))
        )
    try:
        build = json.loads(_read_text(case.build_path, "the build record"))
        shape = str(build["shape"]).lower()
        rows = parse_rows(case.scenario_figures_path.read_bytes())
    except (ValueError, KeyError, TypeError, OSError, ScenarioRefused) as exc:
        raise MaterialError(f"the shape or the rows cannot be read ({type(exc).__name__})") from exc
    template = _read_text(
        repo_root / SCENARIOS_DIR / f"{shape}{SOURCE_SUFFIX}", "the shape's template"
    )
    record = _render_record(case)
    return _assemble(
        "scenario",
        None,
        [
            ("Template", template),
            ("Scenario", _read_text(case.scenario_path, "the scenario")),
            ("Render record", _public_render_record(record)),
            ("Figure sources", _provenance_table(rows, _caps_set_to_total(record))),
        ],
    )


def rubric_material(case: CaseAppendix) -> Material:
    return _assemble("rubric", None, [("Rubric", _read_text(case.rubric_path, "the rubric"))])
