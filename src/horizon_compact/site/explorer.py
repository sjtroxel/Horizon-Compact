"""The explorer-data builder: the committed results files to the explorer's split JSON (Phase 6 IMPLEMENTATION
doc section 5, with the rule of section 19; the decided points of ``scratch/p6-c1-build-prompt.md``).

It reads only committed files: under ``experiment/results/`` the three official files under ``prereg-v1/``,
the case results under ``cases/`` and, per case and model, the memo summary beside them (**counts only**);
``experiment/company/objectives.toml``; and the two awareness reports,
``docs/phases/evidence/phase-4/awareness-<model_key>.md``, each by its exact path and never by a prefix
(Phase 6 IMPLEMENTATION doc section 5's dated note of 2026-11-10, C5); and, for the methods data (below),
the three official sweeps' records under ``experiment/raw/`` and ``raw-manifest.json``. It calls nothing and
writes nothing but its own output directory. Run code under ``protocol/sets.py``'s rules. Standard library
only.

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

**The run dates (Phase 7 step 2, 2026-11-23).** The index gains a ``runs`` block: for the grids and the
thinking sub-study, the earliest session start and the latest session finish of the sweep's raw session
records (the methods data's ``sessions``); for each awareness probe, the earliest start and latest finish of
its 15 raw call records (``experiment/raw/official/company/awareness/``: the manifest and every
``runs/r-*.json``, of which only the two timestamps are picked, never the reply); for each case and model,
the dates of the sessions in the **Sessions table of ``docs/phases/evidence/phase-5.5/run-log.md``**, read
by its exact path (the case sweeps' raw text is not published and no results file carries a date). Every
date is the UTC calendar date of a copied timestamp, the one thing computed from it; the case dates are
**session start dates**, because the log records no finish time. A model's retirement date comes from
``experiment/retirements.toml`` (empty in v1; ``None`` in the output while it is). This amends the line
below for the awareness runs: their records are opened for two timestamps and nothing else.

**What it does not read:** any ``*-memos.jsonl`` (a real case's memo text: decision 5 holds it off the site;
a test records every path the builder opens), ``reident.json`` (named, not listed), and no memo text of any
kind. Grid memos come from ``hc site memos``, a different step.

**The methods data (Phase 6.5 step 4, 2026-11-17).** ``methods.json`` is built from the published raw text
(``experiment/raw/``, beside the results root) for the three official sweeps that have a results file, and for
no other: per sweep its ``manifest.json``, every ``sessions/*.json`` and every ``runs/*/attempt-*.json``, and
once ``docs/phases/evidence/phase-4/raw-manifest.json``. Fields are picked by name and never copied whole; no
memo, prompt, model text, request id, task or image reference is ever copied. The request-side settings are
copied from the attempts and **refused unless every attempt of a sweep has the same value** (a check, not a
computation). The things this adds to "derives", each a count of copied values: the number of entries in a
manifest's ``runs`` list, and, for the two response-side fields ``served_by`` and ``served_model``, how many
attempts had each distinct value (the one new computed value: the page must say that 11 of one model's
attempts did not report which provider served them, and the number has to trace to a file, not be typed).
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tomllib
from collections import Counter
from collections.abc import Mapping
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

# Unchanged by the methods data (2026-11-17): a new file and a new key of ``files`` are additions, no existing
# field changes shape, and nothing reads this number (the explorer's loaders take every path from ``files``).
EXPLORER_DATA_VERSION = 1
OUT_NAME = "explorer-data"
RESULTS_PREFIX = "experiment/results"
OBJECTIVES_SOURCE = "experiment/company/objectives.toml"

# The published raw text (Phase 6.5 step 4): where it is, and the manifest that hashes every object in it.
RAW_FOLDER = "experiment/raw"
RAW_MANIFEST_SOURCE = "docs/phases/evidence/phase-4/raw-manifest.json"
METHODS_PATH = "methods.json"
_OFFICIAL_SWEEPS = "official/company"

# The run dates (Phase 7 IMPLEMENTATION doc step 2). Four kinds of date, each from the one place that holds
# it: the grids and the thinking sub-study from the raw session records (the methods data already has them),
# the awareness probes from their raw call records, and the case runs from the Phase 5.5 run log's Sessions
# table, because the case sweeps' raw text is not published and no results file carries a date.
RUN_LOG_SOURCE = "docs/phases/evidence/phase-5.5/run-log.md"
RETIREMENTS_SOURCE = "experiment/retirements.toml"
_AWARENESS_SWEEPS = "official/company/awareness"
_CALL_FIELDS = ("started_at", "finished_at")
_CASE_SWEEP_ID = re.compile(r"case-[a-z0-9-]+-[0-9a-f]{8}")
_RUN_LOG_WHEN = re.compile(r"([0-9]{4}-[0-9]{2}-[0-9]{2}) (?:about )?[0-9]{2}:[0-9]{2} UTC")
_RUN_LOG_SESSION_DATE = re.compile(r"session started ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9:]+ UTC")
_RUN_LOG_CELLS = 8  # When, Sweep, Model, Session, Stopped, Runs finished, Cost, Note

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
    re.compile(r"methods\.json"),
)

# The methods data. Each tuple is a list of fields picked by name from a raw record, never the record whole.
#
# The sweep's own plan, from its manifest.json.
_SWEEP_FIELDS = ("seed", "repeats", "templates", "scenarios")
# The request-side fields of an attempt: each must be a single value across every attempt of a sweep.
_SETTINGS_FIELDS = (
    "api",
    "provider",
    "route_kind",
    "model_id",
    "invoke_id",
    "max_tokens",
    "temperature",
    "effort",
    "thinking",
    "region",
    "inference_profile",
    "harness_version",
    "image_digest",
    "git_sha",
    "git_dirty",
    "runner",
    "label",
)
# The response-side fields (inside ``provider_details``) that may differ between attempts, and are counted.
_SERVED_FIELDS = ("served_by", "served_model")
# A session record's fields (a session is one launch of the sweep's task).
_SESSION_FIELDS = (
    "started_at",
    "finished_at",
    "stopped",
    "runs_total",
    "runs_finished_this_session",
    "status_counts_this_session",
    "cost_usd_sweep_total",
    "cap_usd",
)
_RAW_MANIFEST_FIELDS = ("object_count", "total_bytes", "hash")

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


# --- the methods data (Phase 6.5 step 4) -------------------------------------------------------------------


def _same_value(a: Any, b: Any) -> bool:
    return type(a) is type(b) and a == b


def _read_sweep_raw(raw_root: Path, grid: _Grid) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """One official sweep's methods record and its sources (path and sha256 of its manifest and sessions).

    Opens exactly three kinds of file under the sweep's folder: ``manifest.json``, ``sessions/*.json`` and
    ``runs/*/attempt-*.json``. Never ``final.json``, never another sweep, never a pilot or an awareness
    run."""
    sweep = grid.sweep_id
    base = raw_root / _OFFICIAL_SWEEPS / sweep
    shown_base = f"{RAW_FOLDER}/{_OFFICIAL_SWEEPS}/{sweep}"
    sources: list[dict[str, str]] = []

    shown_manifest = f"{shown_base}/manifest.json"
    manifest, manifest_sha = _load(base / "manifest.json", shown_manifest)
    sources.append({"path": shown_manifest, "sha256": manifest_sha})
    for key, expected in (("sweep_id", sweep), ("model_key", grid.model_key), ("label", grid.kind)):
        if manifest.get(key) != expected:
            raise ExplorerDataRefusal(
                f"{shown_manifest} has {key} {manifest.get(key)!r}, not {expected!r}"
            )
    planned = manifest.get("runs")
    if not isinstance(planned, list):
        raise ExplorerDataRefusal(f"{shown_manifest} has no runs list")
    record: dict[str, Any] = {"sweep_id": sweep, "model_key": grid.model_key, "kind": grid.kind}
    record.update(_pick(manifest, _SWEEP_FIELDS, shown_manifest))
    record["runs_in_manifest"] = len(planned)

    sessions: list[dict[str, Any]] = []
    for path in sorted((base / "sessions").glob("*.json")):
        shown = f"{shown_base}/sessions/{path.name}"
        data, sha = _load(path, shown)
        sources.append({"path": shown, "sha256": sha})
        sessions.append(_pick(data, _SESSION_FIELDS, shown))
    if not sessions:
        raise ExplorerDataRefusal(f"{shown_base}/sessions holds no session record")
    sessions.sort(key=lambda s: str(s["started_at"]))

    settings: dict[str, Any] | None = None
    first_id = ""
    attempts = 0
    seen = {field: Counter[str]() for field in _SERVED_FIELDS}
    lacking: dict[str, str] = {}
    for path in sorted((base / "runs").glob("*/attempt-*.json")):
        attempt_id = f"{path.parent.name}/{path.stem}"
        data, _sha = _load(path, f"{shown_base}/runs/{attempt_id}.json")
        here = _pick(data, _SETTINGS_FIELDS, f"{shown_base}/runs/{attempt_id}.json")
        attempts += 1
        if settings is None:
            settings, first_id = here, attempt_id
        else:
            for field in _SETTINGS_FIELDS:
                if not _same_value(settings[field], here[field]):
                    raise ExplorerDataRefusal(
                        f"{shown_base}: the request-side field {field} is {settings[field]!r} on "
                        f"{first_id} and {here[field]!r} on {attempt_id}; a sweep's settings must be "
                        "identical on every attempt"
                    )
        details = data.get("provider_details")
        if not isinstance(details, dict):
            raise ExplorerDataRefusal(
                f"{shown_base}/runs/{attempt_id}.json has no provider_details block"
            )
        for field in _SERVED_FIELDS:
            if field not in details:
                lacking.setdefault(field, attempt_id)
                continue
            value = details[field]
            if not isinstance(value, str) or not value:
                raise ExplorerDataRefusal(
                    f"{shown_base}/runs/{attempt_id}.json: {field} is not a plain value ({value!r})"
                )
            seen[field][value] += 1
    if settings is None:
        raise ExplorerDataRefusal(f"{shown_base}/runs holds no attempt record")

    served: dict[str, list[dict[str, Any]]] = {}
    for field in _SERVED_FIELDS:
        counted = seen[field]
        if not counted:
            continue  # no attempt of this sweep reports the field: it is left out, not invented
        if field in lacking:
            raise ExplorerDataRefusal(
                f"{shown_base}: {field} is reported on some attempts and not on {lacking[field]}"
            )
        served[field] = [{"value": v, "attempts": counted[v]} for v in sorted(counted)]
    record["settings"] = settings
    record["served"] = served
    record["sessions"] = sessions
    return record, sources


def _read_methods(
    results_root: Path, raw_root: Path, grids: list[_Grid], thinking: _Grid
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """The methods document and its sources: the two grids then the thinking sub-study, and the raw manifest's
    totals. Reads the raw text of those three sweeps and of no other."""
    manifest_path = results_root.parent.parent / RAW_MANIFEST_SOURCE
    manifest, manifest_sha = _load(manifest_path, RAW_MANIFEST_SOURCE)
    totals = _pick(manifest, _RAW_MANIFEST_FIELDS, RAW_MANIFEST_SOURCE)
    for key in ("object_count", "total_bytes"):
        if not _is_count(totals[key]):
            raise ExplorerDataRefusal(
                f"{RAW_MANIFEST_SOURCE}: {key} is not a count ({totals[key]!r})"
            )
    sweeps: list[dict[str, Any]] = []
    sources: list[dict[str, str]] = [{"path": RAW_MANIFEST_SOURCE, "sha256": manifest_sha}]
    for grid in [*grids, thinking]:
        record, more = _read_sweep_raw(raw_root, grid)
        sweeps.append(record)
        sources.extend(more)
    document = {
        "raw_text": {"folder": RAW_FOLDER, "manifest": RAW_MANIFEST_SOURCE, **totals},
        "sweeps": sweeps,
    }
    return document, sources


# --- the run dates -----------------------------------------------------------------------------------------


def _utc(stamp: Any, shown: str) -> datetime:
    """A timestamp the raw records wrote. It must say it is UTC: a date read off local time would be wrong."""
    if not isinstance(stamp, str):
        raise ExplorerDataRefusal(f"{shown} has no timestamp where one is needed ({stamp!r})")
    try:
        moment = datetime.fromisoformat(stamp)
    except ValueError as exc:
        raise ExplorerDataRefusal(
            f"{shown} has a timestamp that is not ISO 8601 ({stamp!r})"
        ) from exc
    if moment.tzinfo is None or moment.utcoffset() != timedelta(0):
        raise ExplorerDataRefusal(f"{shown} has a timestamp that is not in UTC ({stamp!r})")
    return moment


def _span(first: str, last: str, basis: str) -> dict[str, str]:
    """The UTC calendar dates of a run's first start and last finish (the one thing computed from a timestamp:
    its date). ``basis`` says which record they were read from."""
    return {"from": first, "to": last, "basis": basis}


def _sweep_span(record: Mapping[str, Any], shown: str) -> dict[str, str]:
    """One official sweep's dates from its sessions (already copied into the methods data): the earliest
    start and the latest finish, as UTC dates."""
    sessions = record["sessions"]
    starts = [_utc(s["started_at"], f"{shown}, a session's started_at") for s in sessions]
    ends = [_utc(s["finished_at"], f"{shown}, a session's finished_at") for s in sessions]
    first, last = min(starts), max(ends)
    if last < first:
        raise ExplorerDataRefusal(f"{shown} finishes before it starts")
    return _span(first.date().isoformat(), last.date().isoformat(), "sessions")


def _awareness_span(
    raw_root: Path, model_key: str, sweep_id: str
) -> tuple[dict[str, str], dict[str, str]]:
    """One awareness probe's dates from its 15 raw call records, and its manifest as a source. Opens the
    sweep's ``manifest.json`` and every ``runs/r-*.json``, and picks only the two timestamps of a call: the
    reply text in those files is never copied."""
    base = raw_root / _AWARENESS_SWEEPS / sweep_id
    shown_base = f"{RAW_FOLDER}/{_AWARENESS_SWEEPS}/{sweep_id}"
    shown_manifest = f"{shown_base}/manifest.json"
    manifest, manifest_sha = _load(base / "manifest.json", shown_manifest)
    for key, expected in (("sweep_id", sweep_id), ("model_key", model_key)):
        if manifest.get(key) != expected:
            raise ExplorerDataRefusal(
                f"{shown_manifest} has {key} {manifest.get(key)!r}, not {expected!r}"
            )
    paths = sorted((base / "runs").glob("r-*.json"))
    if len(paths) != AWARENESS_CALLS:
        raise ExplorerDataRefusal(
            f"{shown_base}/runs holds {len(paths)} call records, not {AWARENESS_CALLS}"
        )
    starts: list[datetime] = []
    ends: list[datetime] = []
    for path in paths:
        shown = f"{shown_base}/runs/{path.name}"
        data, _sha = _load(path, shown)
        if data.get("model_key") != model_key:
            raise ExplorerDataRefusal(f"{shown} is not a {model_key} record")
        stamps = _pick(data, _CALL_FIELDS, shown)
        starts.append(_utc(stamps["started_at"], shown))
        ends.append(_utc(stamps["finished_at"], shown))
    first, last = min(starts), max(ends)
    span = _span(first.date().isoformat(), last.date().isoformat(), "calls")
    return span, {"path": shown_manifest, "sha256": manifest_sha}


def _read_case_run_dates(
    root: Path, expected: Mapping[str, tuple[str, str]]
) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    """The case runs' dates from the Sessions table of the Phase 5.5 run log, by its exact path.

    ``expected`` maps each case sweep id (from the case results) to its (case label, model key). A row
    is a session when its Session cell does not start with ``(`` (the table also records stops, which
    are not sessions). Each session row must say its time is UTC, name a sweep the results have, and
    agree with that sweep's case label and model; a ``session started <date>`` in the Session or Stopped
    cell must give the same date as the When cell. The dates are **session start dates**: the log
    records no finish time, so a case's ``to`` is the date its last session started. Every case sweep
    must have at least one session row.
    """
    shown = RUN_LOG_SOURCE
    path = root.parent.parent / RUN_LOG_SOURCE
    try:
        raw = path.read_bytes()
        lines = raw.decode("utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise ExplorerDataRefusal(f"{shown} cannot be read: {exc}") from exc
    if "## Sessions" not in lines:
        raise ExplorerDataRefusal(f"{shown} has no '## Sessions' section")
    start = lines.index("## Sessions")
    found: dict[str, list[str]] = {}
    in_table = False
    for number, line in enumerate(lines[start + 1 :], start + 2):
        if line.startswith("## "):
            break
        if not line.startswith("|"):
            if in_table:
                break
            continue
        in_table = True
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells[0] == "When" or set(line) <= set("|- "):
            continue
        if len(cells) != _RUN_LOG_CELLS:
            raise ExplorerDataRefusal(
                f"{shown}, line {number}: {len(cells)} cells, not {_RUN_LOG_CELLS}"
            )
        when, sweep_cell, model_cell, session_cell, stopped_cell = cells[:5]
        if session_cell.startswith("("):
            continue  # a stop that was read, not a session
        ticked = re.findall(r"`([^`]+)`", sweep_cell)
        if len(ticked) < 2 or not _CASE_SWEEP_ID.fullmatch(ticked[0]):
            raise ExplorerDataRefusal(
                f"{shown}, line {number}: the Sweep cell does not hold a case sweep id and a case label"
            )
        sweep_id, label = ticked[0], ticked[1]
        if sweep_id not in expected:
            raise ExplorerDataRefusal(
                f"{shown}, line {number}: sweep {sweep_id} is not a case sweep the results hold"
            )
        want_label, want_model = expected[sweep_id]
        if label != want_label or model_cell.strip("`") != want_model:
            raise ExplorerDataRefusal(
                f"{shown}, line {number}: sweep {sweep_id} is {want_label} on {want_model} in the "
                f"results, not {label} on {model_cell.strip('`')}"
            )
        when_match = _RUN_LOG_WHEN.match(when)
        if when_match is None:
            raise ExplorerDataRefusal(
                f"{shown}, line {number}: the When cell does not give a UTC date and time"
            )
        day = when_match.group(1)
        try:
            date.fromisoformat(day)
        except ValueError as exc:
            raise ExplorerDataRefusal(f"{shown}, line {number}: {day} is not a date") from exc
        in_cell = _RUN_LOG_SESSION_DATE.search(f"{session_cell} {stopped_cell}")
        if in_cell is not None and in_cell.group(1) != day:
            raise ExplorerDataRefusal(
                f"{shown}, line {number}: the When cell says {day} and the Session cell says "
                f"{in_cell.group(1)}"
            )
        found.setdefault(sweep_id, []).append(day)
    missing = sorted(set(expected) - set(found))
    if missing:
        raise ExplorerDataRefusal(f"{shown} has no session row for {', '.join(missing)}")
    spans = {sid: _span(min(days), max(days), "run_log") for sid, days in found.items()}
    return spans, {"path": shown, "sha256": hashlib.sha256(raw).hexdigest()}


def _read_retirements(
    root: Path, model_keys: list[str]
) -> tuple[dict[str, str | None], dict[str, str]]:
    """Each model's retirement date, ``None`` while it is still served (every model, in v1). The source is a
    small TOML list, ``[[retired]]`` entries of ``model_key`` and ``date``; filling one is a data change with
    an M12 entry. Anything else in the file is refused."""
    path = root.parent / "retirements.toml"
    shown = RETIREMENTS_SOURCE
    try:
        raw = path.read_bytes()
        loaded = tomllib.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ExplorerDataRefusal(f"{shown} cannot be read: {exc}") from exc
    if set(loaded) - {"retired"}:
        raise ExplorerDataRefusal(f"{shown} holds a key other than 'retired'")
    items = loaded.get("retired", [])
    if not isinstance(items, list):
        raise ExplorerDataRefusal(f"{shown}: 'retired' must be a list of [[retired]] tables")
    retired: dict[str, str | None] = dict.fromkeys(model_keys)
    for item in items:
        if not isinstance(item, dict) or set(item) != {"model_key", "date"}:
            raise ExplorerDataRefusal(f"{shown}: each [[retired]] holds exactly model_key and date")
        key, day = item["model_key"], item["date"]
        if key not in retired:
            raise ExplorerDataRefusal(f"{shown} names {key!r}, which is not an official model")
        if retired[key] is not None:
            raise ExplorerDataRefusal(f"{shown} names {key!r} twice")
        if not isinstance(day, str) or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", day) is None:
            raise ExplorerDataRefusal(f"{shown}: the date for {key} is not YYYY-MM-DD ({day!r})")
        try:
            date.fromisoformat(day)
        except ValueError as exc:
            raise ExplorerDataRefusal(f"{shown}: {day} is not a date") from exc
        retired[key] = day
    return retired, {"path": shown, "sha256": hashlib.sha256(raw).hexdigest()}


def _read_runs(
    root: Path,
    raw_root: Path,
    methods: Mapping[str, Any],
    awareness: list[tuple[str, str, dict[str, Any], str]],
    case_results: list[tuple[str, str, str, dict[str, Any], str]],
    model_keys: list[str],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """The ``runs`` block of the index: when each kind of run happened, and each model's retirement date."""
    sources: list[dict[str, str]] = []
    grid: dict[str, Any] = {}
    thinking: dict[str, Any] = {}
    for record in methods["sweeps"]:
        shown = f"the methods data for {record['sweep_id']}"
        target = grid if record["kind"] == "grid" else thinking
        target[record["model_key"]] = _sweep_span(record, shown)
    aware: dict[str, Any] = {}
    for model_key, _shown, doc, _sha in awareness:
        span, source = _awareness_span(raw_root, model_key, str(doc["sweep_id"]))
        aware[model_key] = span
        sources.append(source)
    expected = {
        str(data["sweep_id"]): (label, model_key)
        for label, model_key, _shown, data, _sha in case_results
    }
    by_sweep, log_source = _read_case_run_dates(root, expected)
    sources.append(log_source)
    cases: dict[str, dict[str, Any]] = {}
    for label, model_key, _shown, data, _sha in case_results:
        cases.setdefault(label, {})[model_key] = by_sweep[str(data["sweep_id"])]
    retired, retired_source = _read_retirements(root, model_keys)
    sources.append(retired_source)
    runs = {
        "grid": grid,
        "thinking": thinking,
        "awareness": aware,
        "cases": cases,
        "retired_on": retired,
    }
    return runs, sources


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


def build_explorer_data(results_root: Path, raw_root: Path | None = None) -> dict[str, str]:
    """Published relative path to the file's exact text, each ending in one newline. ``raw_root`` is the
    published raw text (default: ``raw`` beside the results root); only the methods data reads it."""
    raw_root = results_root.parent / "raw" if raw_root is None else raw_root
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
    methods, methods_sources = _read_methods(results_root, raw_root, grids, thinking)
    runs, runs_sources = _read_runs(
        results_root, raw_root, methods, awareness, case_results, model_keys
    )

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
        "methods": METHODS_PATH,
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
    out[METHODS_PATH] = _text(methods, METHODS_PATH)

    sources = (
        [{"path": g.shown, "sha256": g.sha} for g in [*grids, thinking]]
        + [
            {"path": f"{RESULTS_PREFIX}/cases/cases.json", "sha256": case_index_sha},
            {"path": OBJECTIVES_SOURCE, "sha256": objectives_sha},
        ]
        + [{"path": shown, "sha256": sha} for _l, _m, shown, _d, sha in case_results]
        + [{"path": shown, "sha256": sha} for _c, shown, sha in memo_counts.values()]
        + [{"path": shown, "sha256": sha} for _m, shown, _d, sha in awareness]
        + methods_sources
        + runs_sources
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
        "runs": runs,
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
