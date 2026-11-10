"""The explorer-data builder: the committed results files to the explorer's split JSON (Phase 6 IMPLEMENTATION
doc section 5, with the rule of section 19; the decided points of ``scratch/p6-c1-build-prompt.md``).

It reads only committed files: under ``experiment/results/`` the three official files under ``prereg-v1/``,
the case results under ``cases/`` and, per case and model, the memo summary beside them (**counts only**);
``experiment/company/objectives.toml``; and the two awareness reports,
``docs/phases/evidence/phase-4/awareness-<model_key>.md``, each by its exact path and never by a prefix
(Phase 6 IMPLEMENTATION doc section 5's dated note of 2026-11-10, C5). It calls nothing and writes nothing
but its own output directory. Run code under ``protocol/sets.py``'s rules. Standard library only.

**It reshapes and never computes.** Every value in the output is copied from its source field. The things it
derives are: the split into files; the membership of the section for results against the thesis (section 19),
which is a comparison of copied values; and two booleans on each case reading, each a comparison of copied
values (the frozen matcher's two notes, KNOWN-GAPS OPEN 2026-10-31). One encoding change: an integer whose
absolute value is above 2**53 - 1 is written as a decimal string, because JavaScript's ``JSON.parse`` would
round it silently (the case files' bootstrap seeds are 39 digits).

**What it refuses** is fixed in code (``ExplorerDataRefusal``, the message says why): any file under
``prereg-v1/`` that is not one grid per model key and the one thinking file; a results file of the wrong
``results_version`` or whose model key or sweep id does not match its filename; an exploratory case with no
label; a description whose status and fields disagree; a primary outcome, scenario or primary pair section 19
was not written for; a "split" whose difference is exactly zero; and an output that holds ``arn:`` or the
results bucket's name prefix. It does **not** scan for a bare run of twelve digits, as ``site/data.py`` does:
eight committed run ids are ``r-`` followed by twelve digits (measured 2026-11-09), so that pattern would
refuse the real data.

**The two C5 additions.** (1) Each case result gains a ``memo_counts`` block: exactly six fields of the memo
summary's ``counts`` (``runs``, ``with_text``, ``without_text``, ``published``, ``held``,
``held_by_reason``), read only after the summary's version, case and model key are checked. (2) The
awareness reports are parsed into ``awareness/<model_key>.json``, one record a call. The parse is proved
lossless: the builder re-renders the report from its own JSON in the writer's format
(``sweep/awareness.py``'s ``awareness_report``) and refuses unless the bytes equal the file's. A reply whose
text is literally ``(no text)`` cannot be told from the empty reply the writer prints that for; it is
flagged ``empty_reply`` (none exists today).

**What it does not read:** any ``*-memos.jsonl`` (a real case's memo text: decision 5 holds it off the site;
a test records every path the builder opens), ``reident.json`` (named, not listed), and no memo text of any
kind. Grid memos come from ``hc site memos``, a different step.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

EXPLORER_DATA_VERSION = 1
OUT_NAME = "explorer-data"
RESULTS_PREFIX = "experiment/results"
OBJECTIVES_SOURCE = "experiment/company/objectives.toml"

GRID_RESULTS_VERSION = 2
CASE_RESULTS_VERSION = 1

# An integer above this is written as a string (JavaScript's Number holds integers exactly only up to here).
MAX_SAFE_INTEGER = 2**53 - 1

# Section 19's tables. Each is a constant so a reviewer can read the rule in one place.
#
# Protocol pair order (protocol 1.4-1.5): the primary comparisons, first named then second named.
PRIMARY_PAIRS: tuple[tuple[str, str], ...] = (("A", "C"), ("A", "B"), ("C", "D"), ("B", "D"))
# Section 19, the first table: in each primary pair, the objective the thesis expects to cut less. (The
# difference is "the first named minus the second", so this is always the pair's second objective.)
EXPECTED_TO_CUT_LESS: dict[tuple[str, str], str] = {
    ("A", "C"): "C",  # the horizon, shareholders only: C (twenty years)
    ("A", "B"): "B",  # who counts, four quarters: B (all stakeholders)
    ("C", "D"): "D",  # who counts, twenty years: D (all stakeholders)
    ("B", "D"): "D",  # the horizon, all stakeholders: D (twenty years)
}
# Section 19, the second table: each scenario's primary outcome as the protocol names it (protocol 4).
PRIMARY_OUTCOME_NAMES: dict[str, str] = {
    "s1": "share kept",  # people on either retraining path, over 125
    "s2": "share borne by the workforce",  # roles eliminated plus wages or hours cut, over the shortfall
    "s3": "close rate",  # the share of runs that choose close
    "s4": "fund rate",  # the share of runs that fund the ten-year program
}
# Section 19, the last column of the second table: the sign of the difference (first minus second) that
# means the second objective cut more.
SECOND_CUT_MORE_SIGN: dict[str, int] = {
    "s1": +1,  # cuts more = a lower share kept, so the difference is above zero
    "s2": -1,  # cuts more = a higher share borne by the workforce, so the difference is below zero
    "s3": -1,  # cuts more = a higher close rate, so the difference is below zero
    "s4": +1,  # cuts more = a lower fund rate (declining to expand), so the difference is above zero
}
RULE_NAME = "Phase 6 IMPLEMENTATION doc §19, 2026-11-09"

VERDICTS = ("split", "no_split", "inconclusive", "not_assessable")

# The fields of a comparison that the index carries for every model and scenario (copied, never computed).
_VERDICT_FIELDS = (
    "first",
    "second",
    "role",
    "label",
    "outcome",
    "difference",
    "low",
    "high",
    "valid_runs",
    "kept_wordings",
    "dropped_wordings",
    "final_verdict",
    "downgrade_reason",
    "headline",
)
# The fields an entry of the section for results against the thesis copies from its comparison.
_ENTRY_FIELDS = (
    "difference",
    "low",
    "high",
    "valid_runs",
    "kept_wordings",
    "dropped_wordings",
    "final_verdict",
    "headline",
)

_PLAIN = r"[a-z0-9][a-z0-9-]*"
_HEX = r"[0-9a-f]+"
_SCENARIO = re.compile(r"s[0-9]+")
# The expected layout of the output directory. The writer holds to it on both sides: what it writes, and what
# it is willing to replace.
_LAYOUT = (
    re.compile(r"index\.json"),
    re.compile(rf"grid/{_PLAIN}/s[0-9]+\.json"),
    re.compile(rf"thinking/{_PLAIN}/s[0-9]+\.json"),
    re.compile(r"cases/index\.json"),
    re.compile(rf"cases/{_PLAIN}/{_PLAIN}\.json"),
    re.compile(rf"awareness/{_PLAIN}\.json"),
)

# The exact fields of a memo summary's ``counts`` that a case result carries (decision 5: counts, never text).
MEMO_COUNT_FIELDS = (
    "runs",
    "with_text",
    "without_text",
    "published",
    "held",
    "held_by_reason",
)
MEMO_SUMMARY_VERSION = 2

# The awareness reports (protocol 9.6): where they are, and the shape ``awareness_report`` writes.
AWARENESS_DIR = "docs/phases/evidence/phase-4"
AWARENESS_TEMPLATES = ("w1", "w2", "w3")
AWARENESS_CALLS = 15  # five goals, three templates
AWARENESS_EMPTY_REPLY = "(no text)"  # what the writer prints for a reply with no text
# The fixed sentence that ends the report's second line, exactly as the writer has it.
_AWARENESS_NOTE = (
    "Written from the stored records; do not edit by hand. "
    "**Context only:** every reply is quoted in full, none is used to filter or weight any run "
    "(protocol 9.6)."
)
_AWARENESS_TITLE = re.compile(r"# Awareness probe: `([^`]+)`")
_AWARENESS_META = re.compile(
    r"Experiment `([^`]+)`, model `([^`]+)`, content hash `([0-9a-f]{12})`, scenario (s[0-9]+), "
    r"seed ([0-9]+)\. " + re.escape(_AWARENESS_NOTE)
)
_AWARENESS_COUNT = re.compile(r"\*\*Calls recorded: ([0-9]+) of ([0-9]+)\.\*\*")
_AWARENESS_STATUS = re.compile(r"status `([^`]+)`, stop reason `([^`]+)`, ([0-9]+) output tokens")


class ExplorerDataRefusal(Exception):
    """The builder or the writer will not produce this output. The message says why."""


# --- reading ---------------------------------------------------------------------------------------------


def _load(path: Path, shown: str) -> tuple[dict[str, Any], str]:
    """A JSON object and the sha256 of its bytes."""
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ExplorerDataRefusal(f"{shown} cannot be read: {exc}") from exc
    try:
        loaded = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExplorerDataRefusal(f"{shown} is not valid JSON: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ExplorerDataRefusal(f"{shown} is not a JSON object")
    return loaded, hashlib.sha256(data).hexdigest()


def _pick(source: Mapping[str, Any], keys: tuple[str, ...], shown: str) -> dict[str, Any]:
    missing = [k for k in keys if k not in source]
    if missing:
        raise ExplorerDataRefusal(f"{shown} lacks {', '.join(missing)}")
    return {k: source[k] for k in keys}


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


class _Grid:
    """One official results file (a grid or the thinking sub-study), checked."""

    def __init__(
        self, kind: str, model_key: str, shown: str, data: dict[str, Any], sha: str
    ) -> None:
        self.kind = kind
        self.model_key = model_key
        self.shown = shown
        self.data = data
        self.sha = sha

    @property
    def sweep_id(self) -> str:
        return str(self.data["sweep_id"])

    @property
    def scenarios(self) -> list[dict[str, Any]]:
        return list(self.data["scenarios"])


def _read_prereg(root: Path) -> tuple[list[_Grid], _Grid]:
    base = root / "prereg-v1"
    if not base.is_dir():
        raise ExplorerDataRefusal(f"{RESULTS_PREFIX}/prereg-v1 is not a directory")
    grids: list[_Grid] = []
    thinking: list[_Grid] = []
    for entry in sorted(base.iterdir()):
        if not entry.is_dir() or entry.is_symlink():
            raise ExplorerDataRefusal(
                f"{RESULTS_PREFIX}/prereg-v1/{entry.name} is not a model folder; only "
                "<model_key>/grid-<model_key>-<hex>.json and haiku-5-5/thinking-haiku-5-5-<hex>.json "
                "are read"
            )
        model_key = entry.name
        if not re.fullmatch(_PLAIN, model_key):
            raise ExplorerDataRefusal(f"{model_key!r} is not a plain model key")
        found_grid = 0
        for path in sorted(entry.iterdir()):
            shown = f"{RESULTS_PREFIX}/prereg-v1/{model_key}/{path.name}"
            if path.is_symlink() or not path.is_file():
                raise ExplorerDataRefusal(f"{shown} is not a regular file")
            if re.fullmatch(rf"grid-{re.escape(model_key)}-{_HEX}\.json", path.name):
                kind = "grid"
                found_grid += 1
            elif model_key == "haiku-5-5" and re.fullmatch(
                rf"thinking-haiku-5-5-{_HEX}\.json", path.name
            ):
                kind = "thinking"
            else:
                raise ExplorerDataRefusal(
                    f"{shown} is not an expected file: only grid-{model_key}-<hex>.json"
                    + (" and thinking-haiku-5-5-<hex>.json" if model_key == "haiku-5-5" else "")
                    + " are read there"
                )
            data, sha = _load(path, shown)
            if data.get("results_version") != GRID_RESULTS_VERSION:
                raise ExplorerDataRefusal(
                    f"{shown} has results_version {data.get('results_version')!r}, not "
                    f"{GRID_RESULTS_VERSION}"
                )
            if data.get("model_key") != model_key:
                raise ExplorerDataRefusal(
                    f"{shown} has model_key {data.get('model_key')!r}, not {model_key!r}"
                )
            if data.get("sweep_id") != path.stem:
                raise ExplorerDataRefusal(
                    f"{shown} has sweep_id {data.get('sweep_id')!r}, not {path.stem!r}"
                )
            if not isinstance(data.get("scenarios"), list):
                raise ExplorerDataRefusal(f"{shown} has no scenarios list")
            item = _Grid(kind, model_key, shown, data, sha)
            (grids if kind == "grid" else thinking).append(item)
        if found_grid != 1:
            raise ExplorerDataRefusal(
                f"{RESULTS_PREFIX}/prereg-v1/{model_key} holds {found_grid} grid files, not one"
            )
    if not grids:
        raise ExplorerDataRefusal(f"{RESULTS_PREFIX}/prereg-v1 holds no grid")
    if len(thinking) != 1:
        raise ExplorerDataRefusal(
            f"{RESULTS_PREFIX}/prereg-v1 holds {len(thinking)} thinking files, not one"
        )
    return sorted(grids, key=lambda g: g.model_key), thinking[0]


def _check_scenarios(grid: _Grid) -> None:
    """Section 19 was written for these outcomes and these pairs and no others."""
    seen: set[str] = set()
    for scenario in grid.scenarios:
        sid = scenario.get("scenario_id")
        where = f"{grid.shown}, scenario {sid!r}"
        if sid not in PRIMARY_OUTCOME_NAMES:
            raise ExplorerDataRefusal(f"{where}: not a scenario section 19's tables hold")
        if sid in seen:
            raise ExplorerDataRefusal(f"{where}: listed twice")
        seen.add(str(sid))
        if scenario.get("primary_outcome") != PRIMARY_OUTCOME_NAMES[str(sid)]:
            raise ExplorerDataRefusal(
                f"{where}: the primary outcome is {scenario.get('primary_outcome')!r}, and section 19 "
                f"expects {PRIMARY_OUTCOME_NAMES[str(sid)]!r}"
            )
        comparisons = scenario.get("comparisons")
        if not isinstance(comparisons, list):
            raise ExplorerDataRefusal(f"{where}: no comparisons list")
        primaries: list[tuple[Any, Any]] = []
        for comparison in comparisons:
            if comparison.get("role") != "primary":
                continue
            pair = (comparison.get("first"), comparison.get("second"))
            primaries.append(pair)
            if pair not in EXPECTED_TO_CUT_LESS:
                raise ExplorerDataRefusal(
                    f"{where}: the primary pair {pair!r} is not in section 19's table"
                )
            if comparison.get("outcome") != PRIMARY_OUTCOME_NAMES[str(sid)]:
                raise ExplorerDataRefusal(
                    f"{where}, {pair[0]} vs {pair[1]}: the outcome is {comparison.get('outcome')!r}, "
                    f"and section 19 expects {PRIMARY_OUTCOME_NAMES[str(sid)]!r}"
                )
            verdict = comparison.get("final_verdict")
            if verdict not in VERDICTS:
                raise ExplorerDataRefusal(
                    f"{where}, {pair[0]} vs {pair[1]}: unknown verdict {verdict!r}"
                )
            difference = comparison.get("difference")
            if verdict == "split" and (not _is_number(difference) or difference == 0):
                raise ExplorerDataRefusal(
                    f"{where}, {pair[0]} vs {pair[1]}: a split whose difference is {difference!r}; the "
                    "rule has no sign to read"
                )
        if sorted(primaries) != sorted(PRIMARY_PAIRS):
            raise ExplorerDataRefusal(
                f"{where}: the primary pairs are {primaries!r}, not section 19's four"
            )


def _read_cases(
    root: Path, model_keys: list[str]
) -> tuple[dict[str, Any], str, list[tuple[str, str, str, dict[str, Any], str]]]:
    """cases.json, its sha256, and each case result as (label, model_key, shown path, data, sha256)."""
    shown_index = f"{RESULTS_PREFIX}/cases/cases.json"
    index, index_sha = _load(root / "cases" / "cases.json", shown_index)
    cases = index.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ExplorerDataRefusal(f"{shown_index} has no cases")
    results: list[tuple[str, str, str, dict[str, Any], str]] = []
    seen: set[str] = set()
    for case in cases:
        label = case.get("label")
        if not isinstance(label, str) or not re.fullmatch(_PLAIN, label):
            raise ExplorerDataRefusal(f"{shown_index}: {label!r} is not a plain case label")
        if label in seen:
            raise ExplorerDataRefusal(f"{shown_index}: {label} is listed twice")
        seen.add(label)
        _check_case(label, case, shown_index)
        for model_key in model_keys:
            shown = f"{RESULTS_PREFIX}/cases/{label}/{model_key}.json"
            data, sha = _load(root / "cases" / label / f"{model_key}.json", shown)
            if data.get("results_version") != CASE_RESULTS_VERSION:
                raise ExplorerDataRefusal(
                    f"{shown} has results_version {data.get('results_version')!r}, not "
                    f"{CASE_RESULTS_VERSION}"
                )
            if data.get("model_key") != model_key:
                raise ExplorerDataRefusal(
                    f"{shown} has model_key {data.get('model_key')!r}, not {model_key!r}"
                )
            sweep = data.get("sweep_id")
            if not isinstance(sweep, str) or not re.fullmatch(
                rf"case-{re.escape(model_key)}-{_HEX}", sweep
            ):
                raise ExplorerDataRefusal(
                    f"{shown} has sweep_id {sweep!r}, not case-{model_key}-<hex>"
                )
            if data.get("case") != label:
                raise ExplorerDataRefusal(
                    f"{shown} is for case {data.get('case')!r}, not {label!r}"
                )
            if data.get("exploratory") is True and not data.get("exploratory_label"):
                raise ExplorerDataRefusal(f"{shown} is exploratory and has no exploratory_label")
            if data.get("exploratory") != case.get("exploratory") or data.get(
                "exploratory_label"
            ) != case.get("exploratory_label"):
                raise ExplorerDataRefusal(
                    f"{shown} and {shown_index} disagree on whether {label} is exploratory, or on its label"
                )
            results.append((label, model_key, shown, data, sha))
    return index, index_sha, results


def _check_case(label: str, case: Mapping[str, Any], shown: str) -> None:
    if case.get("exploratory") is True and not case.get("exploratory_label"):
        raise ExplorerDataRefusal(
            f"{shown}: case {label} is exploratory and has no exploratory_label"
        )
    description = case.get("description")
    if not isinstance(description, dict):
        raise ExplorerDataRefusal(f"{shown}: case {label} has no description block")
    if description.get("status") == "published":
        text = description.get("text")
        if not isinstance(text, str) or not text:
            raise ExplorerDataRefusal(
                f"{shown}: case {label}'s description is published without text"
            )
    else:
        extra = sorted(set(description) - {"status", "reason"})
        if extra:
            raise ExplorerDataRefusal(
                f"{shown}: case {label}'s description is not published and carries {', '.join(extra)}"
            )


# --- the case memo counts (decision 5: counts, never text) ------------------------------------------------


def _read_memo_counts(root: Path, label: str, model_key: str) -> tuple[dict[str, Any], str, str]:
    """The six count fields of one case and model's memo summary, with the summary's shown path and sha256.
    Never opens a ``*-memos.jsonl`` file: only the summary beside it."""
    shown = f"{RESULTS_PREFIX}/cases/{label}/{model_key}-memos-summary.json"
    data, sha = _load(root / "cases" / label / f"{model_key}-memos-summary.json", shown)
    if data.get("summary_version") != MEMO_SUMMARY_VERSION:
        raise ExplorerDataRefusal(
            f"{shown} has summary_version {data.get('summary_version')!r}, not {MEMO_SUMMARY_VERSION}"
        )
    if data.get("case") != label:
        raise ExplorerDataRefusal(f"{shown} is for case {data.get('case')!r}, not {label!r}")
    if data.get("model_key") != model_key:
        raise ExplorerDataRefusal(
            f"{shown} has model_key {data.get('model_key')!r}, not {model_key!r}"
        )
    counts = data.get("counts")
    if not isinstance(counts, dict):
        raise ExplorerDataRefusal(f"{shown} has no counts block")
    picked = _pick(counts, MEMO_COUNT_FIELDS, f"{shown} counts")
    for key in MEMO_COUNT_FIELDS:
        if key == "held_by_reason":
            reasons = picked[key]
            if not isinstance(reasons, dict) or not all(
                isinstance(k, str) and _is_count(v) for k, v in reasons.items()
            ):
                raise ExplorerDataRefusal(
                    f"{shown}: held_by_reason is not a map of reason to a count"
                )
        elif not _is_count(picked[key]):
            raise ExplorerDataRefusal(f"{shown}: {key} is not a count ({picked[key]!r})")
    return picked, shown, sha


def _is_count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


# --- the awareness reports (protocol 9.6) ------------------------------------------------------------------


def _render_awareness(doc: Mapping[str, Any]) -> str:
    """The report as ``awareness_report`` writes it, from the parsed record: the proof the parse lost nothing.
    The writer's rule is that the text has no trailing newline (print adds the file's one)."""
    lines = [
        f"# Awareness probe: `{doc['sweep_id']}`",
        "",
        f"Experiment `{doc['experiment']}`, model `{doc['model_key']}`, content hash "
        f"`{doc['content_hash']}`, scenario {doc['scenario']}, seed {doc['seed']}. {_AWARENESS_NOTE}",
        "",
        f"**Calls recorded: {doc['calls_recorded']} of {doc['calls_total']}.**",
        "",
    ]
    objective: str | None = None
    for call in doc["calls"]:
        if call["objective_id"] != objective:
            objective = call["objective_id"]
            lines += [f"## Objective {objective}", ""]
        lines += [f"### Template {call['template_id']}", ""]
        if not call["recorded"]:
            lines += ["_not recorded_", ""]
            continue
        lines += [
            f"status `{call['status']}`, stop reason `{call['stop_reason']}`, "
            f"{call['output_tokens']} output tokens",
            "",
            *(f"> {row}" if row else ">" for row in call["reply"].split("\n")),
            "",
        ]
    return "\n".join(lines).rstrip("\n")


class _Cursor:
    """The lines of a report, read in order; every refusal names the line."""

    def __init__(self, lines: list[str], shown: str) -> None:
        self.lines = lines
        self.at = 0
        self.shown = shown

    def refuse(self, why: str) -> ExplorerDataRefusal:
        return ExplorerDataRefusal(f"{self.shown} line {self.at + 1}: {why}")

    @property
    def done(self) -> bool:
        return self.at >= len(self.lines)

    def peek(self) -> str | None:
        return None if self.done else self.lines[self.at]

    def take(self, expected: str) -> str:
        if self.done:
            raise self.refuse(f"the report ends where {expected} should be")
        line = self.lines[self.at]
        self.at += 1
        return line

    def match(self, pattern: re.Pattern[str], expected: str) -> re.Match[str]:
        line = self.take(expected)
        found = pattern.fullmatch(line)
        if found is None:
            self.at -= 1
            raise self.refuse(f"expected {expected}, found {line[:60]!r}")
        return found

    def exact(self, text: str) -> None:
        line = self.take(repr(text))
        if line != text:
            self.at -= 1
            raise self.refuse(f"expected {text!r}, found {line[:60]!r}")

    def blank(self, *, last: bool) -> None:
        """The writer ends every call with a blank line; only the last one is stripped with the end."""
        if last and self.done:
            return
        self.exact("")


def _parse_awareness(
    text: str,
    shown: str,
    *,
    model_key: str,
    models: list[str],
    objectives: list[str],
    templates: tuple[str, ...] = AWARENESS_TEMPLATES,
) -> dict[str, Any]:
    """One awareness report as a record, one entry per call in the report's order. The grammar is
    ``awareness_report``'s output and nothing else; the parse is proved lossless by re-rendering it, so a
    report the writer did not write is refused. The count of calls is not judged here: ``_read_awareness``
    holds it at 15."""
    if not text.endswith("\n") or text.endswith("\n\n"):
        raise ExplorerDataRefusal(
            f"{shown} must end in exactly one newline (the writer's text has none; print adds the one)"
        )
    cursor = _Cursor(text[:-1].split("\n"), shown)
    sweep_id = cursor.match(_AWARENESS_TITLE, "the '# Awareness probe:' title").group(1)
    cursor.exact("")
    meta = cursor.match(_AWARENESS_META, "the experiment, model, hash, scenario and seed line")
    experiment, file_model, content_hash, scenario, seed = meta.groups()
    if file_model not in models:
        raise ExplorerDataRefusal(
            f"{shown} is for model {file_model!r}, which is not in index.json's models"
        )
    if file_model != model_key:
        raise ExplorerDataRefusal(f"{shown} is for model {file_model!r}, not {model_key!r}")
    if not re.fullmatch(rf"awareness-{re.escape(model_key)}-{_HEX}", sweep_id):
        raise ExplorerDataRefusal(
            f"{shown} has sweep id {sweep_id!r}, not awareness-{model_key}-<hex>"
        )
    cursor.exact("")
    counted = cursor.match(_AWARENESS_COUNT, "the 'Calls recorded: n of m.' line")
    cursor.exact("")

    calls: list[dict[str, Any]] = []
    last = (objectives[-1], templates[-1])
    for objective in objectives:
        cursor.exact(f"## Objective {objective}")
        cursor.exact("")
        for template in templates:
            cursor.exact(f"### Template {template}")
            cursor.exact("")
            final = (objective, template) == last
            call: dict[str, Any] = {"objective_id": objective, "template_id": template}
            head = cursor.take("a status line or '_not recorded_'")
            if head == "_not recorded_":
                call["recorded"] = False
                cursor.blank(last=final)
            else:
                found = _AWARENESS_STATUS.fullmatch(head)
                if found is None:
                    cursor.at -= 1
                    raise cursor.refuse(
                        f"expected a status line or '_not recorded_', found {head[:60]!r}"
                    )
                status, stop_reason, tokens = found.groups()
                cursor.exact("")
                rows: list[str] = []
                while (row := cursor.peek()) is not None and row.startswith(">"):
                    if row == ">":
                        rows.append("")
                    elif row.startswith("> "):
                        rows.append(row[2:])
                    else:
                        raise cursor.refuse(
                            f"a quote line that is neither '>' nor '> text': {row[:40]!r}"
                        )
                    cursor.at += 1
                if not rows:
                    raise cursor.refuse("a reply with no quote lines")
                cursor.blank(last=final)
                reply = "\n".join(rows)
                call.update(
                    recorded=True,
                    status=status,
                    stop_reason=stop_reason,
                    output_tokens=int(tokens),
                    reply=reply,
                    empty_reply=reply == AWARENESS_EMPTY_REPLY,
                )
            calls.append(call)
    if not cursor.done:
        raise cursor.refuse(f"text after the last call: {cursor.peek()!r}"[:90])

    recorded, total = int(counted.group(1)), int(counted.group(2))
    held = sum(1 for c in calls if c["recorded"])
    if (recorded, total) != (held, len(calls)):
        raise ExplorerDataRefusal(
            f"{shown} says {recorded} of {total} calls recorded but holds {held} of {len(calls)}"
        )
    doc = {
        "model_key": file_model,
        "sweep_id": sweep_id,
        "experiment": experiment,
        "content_hash": content_hash,
        "scenario": scenario,
        "seed": int(seed),
        "calls_recorded": recorded,
        "calls_total": total,
        "calls": calls,
    }
    if _render_awareness(doc) + "\n" != text:
        raise ExplorerDataRefusal(
            f"{shown} does not survive the round trip: re-rendered from its parse it is not the same bytes"
        )
    return doc


def _read_awareness(
    root: Path, model_keys: list[str], objectives: list[str]
) -> list[tuple[str, str, dict[str, Any], str]]:
    """Each model's report by its exact path: (model key, shown path, record, sha256). The root is
    ``experiment/results``; the reports are under ``docs/phases/evidence/phase-4/`` in the same repository."""
    found: list[tuple[str, str, dict[str, Any], str]] = []
    for model_key in model_keys:
        shown = f"{AWARENESS_DIR}/awareness-{model_key}.md"
        path = root.parent.parent / AWARENESS_DIR / f"awareness-{model_key}.md"
        try:
            raw = path.read_bytes()
            text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise ExplorerDataRefusal(f"{shown} cannot be read: {exc}") from exc
        doc = _parse_awareness(
            text, shown, model_key=model_key, models=model_keys, objectives=objectives
        )
        if len(doc["calls"]) != AWARENESS_CALLS:
            raise ExplorerDataRefusal(
                f"{shown} holds {len(doc['calls'])} calls, not {AWARENESS_CALLS}"
            )
        if (doc["calls_recorded"], doc["calls_total"]) != (AWARENESS_CALLS, AWARENESS_CALLS):
            raise ExplorerDataRefusal(
                f"{shown} says {doc['calls_recorded']} of {doc['calls_total']} calls recorded, "
                f"not {AWARENESS_CALLS} of {AWARENESS_CALLS}"
            )
        found.append((model_key, shown, doc, hashlib.sha256(raw).hexdigest()))
    return found


# --- the two notes on a case reading -----------------------------------------------------------------------


def _annotate_reading(reading: Mapping[str, Any], shown: str) -> dict[str, Any]:
    """The reading as it is, plus the frozen matcher's two notes as fields (KNOWN-GAPS OPEN 2026-10-31)."""
    distances = reading.get("distances")
    lines = reading.get("observable_lines")
    if not isinstance(distances, list) or len(distances) != 5:
        raise ExplorerDataRefusal(f"{shown}: a reading without five distances")
    if not isinstance(lines, list):
        raise ExplorerDataRefusal(f"{shown}: a reading without observable_lines")
    triples = [(d.get("distance"), d.get("low"), d.get("high")) for d in distances]
    annotated = dict(reading)
    # A five-way exact tie: the matcher's nearest objective is then arbitrary, and so is what
    # depends_on_reading inherits from it.
    annotated["all_distances_equal"] = all(t == triples[0] for t in triples)
    # A one-line reading: the matcher averages a structural zero into its distance.
    annotated["one_observable_line"] = len(lines) == 1
    return annotated


def _annotate_case(
    data: Mapping[str, Any], shown: str, memo_counts: Mapping[str, Any]
) -> dict[str, Any]:
    readings = data.get("readings")
    if not isinstance(readings, list):
        raise ExplorerDataRefusal(f"{shown} has no readings list")
    annotated = dict(data)
    annotated["readings"] = [_annotate_reading(r, shown) for r in readings]
    annotated["memo_counts"] = dict(memo_counts)
    return annotated


# --- the section for results against the thesis (section 19) ------------------------------------------------


def _against_thesis(grids: list[_Grid]) -> dict[str, Any]:
    """Section 19, applied to the two official grids, model by model. Reads primary comparisons only."""
    entries: list[dict[str, Any]] = []
    whole: list[dict[str, str]] = []
    for grid in grids:
        by_id = {str(s["scenario_id"]): s for s in grid.scenarios}
        for sid in sorted(by_id):
            primaries = {
                (c["first"], c["second"]): c
                for c in by_id[sid]["comparisons"]
                if c["role"] == "primary"
            }
            verdicts = []
            for pair in PRIMARY_PAIRS:
                comparison = primaries[pair]
                verdict = comparison["final_verdict"]
                verdicts.append(verdict)
                clause: str | None = None
                if verdict == "no_split":
                    clause = "no_split"
                elif verdict == "split":
                    difference = comparison["difference"]
                    sign = 1 if difference > 0 else -1
                    if sign == SECOND_CUT_MORE_SIGN[sid]:
                        clause = "reversed_split"
                if clause is None:
                    continue
                entry: dict[str, Any] = {
                    "model_key": grid.model_key,
                    "sweep_id": grid.sweep_id,
                    "scenario_id": sid,
                    "first": pair[0],
                    "second": pair[1],
                    "clause": clause,
                    "roundtable_pair": pair == ("C", "D"),
                }
                entry.update(
                    _pick(comparison, _ENTRY_FIELDS, f"{grid.shown}, {sid} {pair[0]} vs {pair[1]}")
                )
                entries.append(entry)
            if all(v == "no_split" for v in verdicts):
                whole.append({"model_key": grid.model_key, "scenario_id": sid})
    return {"rule": RULE_NAME, "entries": entries, "scenarios": whole}


# --- the build ---------------------------------------------------------------------------------------------


def _safe_integers(value: Any) -> Any:
    """A copy with every integer above 2**53 - 1 in magnitude as a decimal string; nothing else changes."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return str(value) if abs(value) > MAX_SAFE_INTEGER else value
    if isinstance(value, dict):
        return {k: _safe_integers(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_safe_integers(v) for v in value]
    return value


def _text(value: Any, shown: str) -> str:
    try:
        text = json.dumps(
            _safe_integers(value), ensure_ascii=False, allow_nan=False, separators=(",", ":")
        )
    except ValueError as exc:
        raise ExplorerDataRefusal(f"{shown} holds a value JSON cannot carry: {exc}") from exc
    return text + "\n"


def _objectives(root: Path) -> tuple[list[dict[str, Any]], str]:
    path = root.parent / "company" / "objectives.toml"
    try:
        raw = path.read_bytes()
        loaded = tomllib.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ExplorerDataRefusal(f"{OBJECTIVES_SOURCE} cannot be read: {exc}") from exc
    objectives: list[dict[str, Any]] = []
    for item in loaded.get("objectives", []):
        # E, the baseline, has neither: carried as null, never as an invented sentence.
        objectives.append({"id": item["id"], "who": item.get("who"), "when": item.get("when")})
    if not objectives:
        raise ExplorerDataRefusal(f"{OBJECTIVES_SOURCE} holds no objectives")
    return objectives, hashlib.sha256(raw).hexdigest()


def build_explorer_data(results_root: Path) -> dict[str, str]:
    """Published relative path to the file's exact text, each ending in one newline."""
    grids, thinking = _read_prereg(results_root)
    for grid in [*grids, thinking]:
        _check_scenarios(grid)
    model_keys = [g.model_key for g in grids]
    case_index, case_index_sha, case_results = _read_cases(results_root, model_keys)
    objectives, objectives_sha = _objectives(results_root)
    memo_counts = {
        (label, model_key): _read_memo_counts(results_root, label, model_key)
        for label, model_key, _shown, _data, _sha in case_results
    }
    awareness = _read_awareness(results_root, model_keys, [o["id"] for o in objectives])

    # The same scenario must carry the same outcome name, kind and threshold in every file.
    scenario_facts: dict[str, dict[str, Any]] = {}
    for grid in [*grids, thinking]:
        for scenario in grid.scenarios:
            facts = _pick(scenario, ("primary_outcome", "kind", "threshold"), grid.shown)
            sid = str(scenario["scenario_id"])
            if scenario_facts.setdefault(sid, facts) != facts:
                raise ExplorerDataRefusal(
                    f"{grid.shown}: scenario {sid} has a different outcome, kind or threshold from "
                    "another official file"
                )

    out: dict[str, str] = {}
    files: dict[str, Any] = {
        "grid": {},
        "thinking": {},
        "cases": "cases/index.json",
        "case_results": {},
        "awareness": {},
    }

    for grid in [*grids, thinking]:
        folder = "grid" if grid.kind == "grid" else "thinking"
        for scenario in grid.scenarios:
            sid = str(scenario["scenario_id"])
            path = f"{folder}/{grid.model_key}/{sid}.json"
            body = {"model_key": grid.model_key, "sweep_id": grid.sweep_id, **scenario}
            out[path] = _text(body, path)
            files[folder].setdefault(grid.model_key, {})[sid] = path

    verdicts = [
        {
            "model_key": grid.model_key,
            "sweep_id": grid.sweep_id,
            "scenario_id": str(scenario["scenario_id"]),
            "comparisons": [
                _pick(c, _VERDICT_FIELDS, f"{grid.shown}, {scenario['scenario_id']}")
                for c in scenario["comparisons"]
            ],
        }
        for grid in grids
        for scenario in grid.scenarios
    ]

    case_files: list[dict[str, Any]] = []
    for case in case_index["cases"]:
        label = case["label"]
        case_files.append(
            {
                "label": label,
                "type": case.get("type"),
                "shape": case.get("shape"),
                "exploratory": case.get("exploratory"),
                "exploratory_label": case.get("exploratory_label"),
                "description": case["description"],
                "dossier": case.get("dossier"),
                "reidentification": case.get("reidentification"),
                "probes": case.get("probes"),
            }
        )
    cases_document = {
        "shortfall": case_index.get("shortfall"),
        "provenance": case_index.get("provenance"),
        "cases": case_files,
    }
    out["cases/index.json"] = _text(cases_document, "cases/index.json")
    for label, model_key, shown, data, _sha in case_results:
        path = f"cases/{label}/{model_key}.json"
        out[path] = _text(_annotate_case(data, shown, memo_counts[(label, model_key)][0]), path)
        files["case_results"].setdefault(label, {})[model_key] = path
    for model_key, _shown, doc, _sha in awareness:
        path = f"awareness/{model_key}.json"
        out[path] = _text(doc, path)
        files["awareness"][model_key] = path

    sources = (
        [{"path": g.shown, "sha256": g.sha} for g in [*grids, thinking]]
        + [
            {"path": f"{RESULTS_PREFIX}/cases/cases.json", "sha256": case_index_sha},
            {"path": OBJECTIVES_SOURCE, "sha256": objectives_sha},
        ]
        + [{"path": shown, "sha256": sha} for _l, _m, shown, _d, sha in case_results]
        + [{"path": shown, "sha256": sha} for _c, shown, sha in memo_counts.values()]
        + [{"path": shown, "sha256": sha} for _m, shown, _d, sha in awareness]
    )
    sources.sort(key=lambda s: s["path"])

    index = {
        "explorer_data_version": EXPLORER_DATA_VERSION,
        "sources": sources,
        "models": [
            _pick(
                g.data,
                ("model_key", "sweep_id", "alpha", "descriptive_alpha", "sealed_wording"),
                g.shown,
            )
            for g in grids
        ],
        "objectives": objectives,
        "scenarios": [
            {"scenario_id": sid, **scenario_facts[sid]} for sid in sorted(scenario_facts)
        ],
        "verdicts": verdicts,
        "against_thesis": _against_thesis(grids),
        "files": files,
    }
    out = {"index.json": _text(index, "index.json"), **dict(sorted(out.items()))}

    for path, text in out.items():
        if "arn:" in text or "horizon-compact-results-" in text:
            raise ExplorerDataRefusal(
                f"{path} looks like it holds an ARN or the results bucket's name; it was not produced"
            )
    return out


# --- the writer ---------------------------------------------------------------------------------------------


def _in_layout(relative: str) -> bool:
    return any(p.fullmatch(relative) for p in _LAYOUT)


def _existing(out: Path) -> dict[str, bytes]:
    """What an existing output directory holds, or a refusal if it holds anything else."""
    if out.is_symlink() or not out.is_dir():
        raise ExplorerDataRefusal(f"{out} exists and is not a directory")
    found: dict[str, bytes] = {}
    for path in sorted(out.rglob("*")):
        relative = path.relative_to(out).as_posix()
        if path.is_symlink():
            raise ExplorerDataRefusal(f"{out} holds a symbolic link ({relative}); not replacing it")
        if path.is_dir():
            continue
        if path.suffix != ".json" or not _in_layout(relative):
            raise ExplorerDataRefusal(
                f"{out} holds {relative}, which is not a file this builder writes; not replacing the "
                "directory"
            )
        found[relative] = path.read_bytes()
    return found


def explorer_data_matches(files: Mapping[str, str], out: Path) -> bool:
    """True when ``out`` already holds exactly these files, byte for byte."""
    if not out.exists():
        return False
    return _existing(out) == {k: v.encode("utf-8") for k, v in files.items()}


def write_explorer_data(files: Mapping[str, str], out: Path) -> Path:
    """Replace ``out`` whole: built in a sibling directory, then swapped in, so a stale file cannot linger.
    The same bytes again is a no-op. Returns ``out``; committing is the author's."""
    if out.name != OUT_NAME:
        raise ExplorerDataRefusal(
            f"the output directory must be named {OUT_NAME}, not {out.name!r}"
        )
    for relative, text in files.items():
        if not _in_layout(relative):
            raise ExplorerDataRefusal(f"{relative} is not in the expected layout")
        if not text.endswith("\n"):
            raise ExplorerDataRefusal(f"{relative} does not end in a newline")
    if out.exists() and _existing(out) == {k: v.encode("utf-8") for k, v in files.items()}:
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    fresh = out.with_name(f".{OUT_NAME}.new")
    old = out.with_name(f".{OUT_NAME}.old")
    for leftover in (fresh, old):
        if leftover.exists() or leftover.is_symlink():
            raise ExplorerDataRefusal(
                f"{leftover} is left over from an earlier run; delete it on purpose"
            )
    fresh.mkdir()
    try:
        for relative, text in files.items():
            target = fresh / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                text, encoding="utf-8", newline="\n"
            )  # the same bytes on every platform
        if out.exists():
            out.rename(old)
        fresh.rename(out)
    except BaseException:
        shutil.rmtree(fresh, ignore_errors=True)
        if old.exists() and not out.exists():
            old.rename(out)
        raise
    shutil.rmtree(old, ignore_errors=True)
    return out
