"""The exploratory record of search-half doc §4.6.5 (build plan:
``phase-5-case-building-exploratory-IMPLEMENTATION.md``, stage 1 step 1).

A separate log, written once per version as ``exploratory-log-<n>.json`` with
``exploratory-public-<n>.json``; ``selection-log-<n>.json`` is never written to. The file is a list of
events (a row added, a pre-registered row carried, a criterion recorded, a read recorded), and
``from_text`` replays them through the same code that took them, so a hand-edited file cannot step
around the rules, as with the selection log. A carried row's results are not stored: the event names the
pre-registered log file and its sha256, and the replay reads them from that file, so a carried result
cannot be edited here and a changed source is refused.

What differs from the selection log: one order across the three types (D.1), the cases the first k per
type that pass with a short type's slots filled by the next passing candidates of any type (D.2, D.3),
the selection held open while an earlier candidate is unfinished (D.4), at most five cases and no
checking after the fifth (D.5), and, for the pool of steps 3 and 4, a ``not_known`` criterion after
``maps_to_shape``.

The fill is held until step 5's search has been recorded (his decision, 2026-10-25, dated note under D.3): a
type is short only when no step left can give it a row. Until then a passed row that no type's own slots
took is ``pending``, not a case, and the selection is not complete while a short type's slots are open.
His decision of 2026-10-26 (second dated note under D.3) lifts the hold: a ``released`` event, with its date
and his reason, lets the fill run without step 5, and step 5 then brings no row and is never recorded as run.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.search import (
    CRITERIA,
    PRE_CANDIDATES,
    PRESS_CANDIDATES,
    READ_REQUIRED,
    READINGS,
    STEP4_CANDIDATES,
    TYPES,
    K,
    LogError,
    Read,
    ReaderReply,
    Result,
    Row,
    SelectionLog,
    load_newest_log,
)

EXPLORATORY_VERSION = 1
AT_MOST = 5  # §4.6.5 D.5
# the knowledge probe (step 3 item 4): after maps_to_shape, before not_recognizable
KNOWLEDGE = "not_known"
POOL_CRITERIA = (*CRITERIA[:5], KNOWLEDGE, CRITERIA[5])
POOL_READ_REQUIRED = (*READ_REQUIRED[:2], KNOWLEDGE, READ_REQUIRED[2])
CARRIED = CRITERIA[
    : CRITERIA.index("maps_to_shape")
]  # what a carried row brings; criterion 4 is recorded again
PROBED_STEPS = ("3", "4")
STEP_POOLS = {"2": ("window", "fallback"), "3": ("pre",), "4": ("pre",), "5": ("late",)}
STEP_RANK = {"2": 0, "3": 1, "4": 2, "5": 3}  # §4.6.5 D.1
SOURCE_LOG = re.compile(r"selection-log-\d+\.json")
HELD_FILL = (
    "a short type's slots are held until step 5's search has run (his decision, 2026-10-25): "
    "a type is short only when no step left can give it a row"
)

LABEL = "exploratory: selected by §4.6.5 step {step}, after the pre-registered rule found none"
PROBE_LABEL = (
    "first disclosed before the main model's training cut-off (Haiku 5.5, June 2026) and after the second "
    "family's (gpt-oss-120b, June 2024); admitted after a knowledge probe of both official models and the "
    "extraction model found no recall"
)  # §4.6.5 B.3


@dataclass
class ExploratoryRow(Row):
    """A row of the exploratory record: ``step`` is the §4.6.5 step that brought it in, ``source`` the
    pre-registered log (file name, sha256) a carried row came from. ``type`` is the list the row is on,
    set when it is added or carried and settled at ``maps_to_shape`` (§4.6.5 step 1 item 1)."""

    step: str = "2"
    source: tuple[str, str] | None = None
    # the reply files the pre-registered record logged reads from for this row: never a read here
    prior_replies: frozenset[str] = frozenset()
    # a not_known failure on a call empty three times: it fails by rule, so it is never read and never
    # disputed (search-half doc step 3 item 4, dated note (e))
    empty_fail: bool = False

    @property
    def probed(self) -> bool:
        return self.step in PROBED_STEPS

    @property
    def criteria(self) -> tuple[str, ...]:
        return POOL_CRITERIA if self.probed else CRITERIA

    @property
    def read_required(self) -> tuple[str, ...]:
        if not self.probed:
            return READ_REQUIRED
        return tuple(c for c in POOL_READ_REQUIRED if not (self.empty_fail and c == KNOWLEDGE))

    @property
    def label(self) -> str:
        text = LABEL.format(step=self.step)
        return f"{text}; {PROBE_LABEL}" if self.probed else text


@dataclass(frozen=True)
class ExploratorySelection:
    """The cases so far, in the order of D.1. ``filled`` are those that took a short type's slot (D.3);
    ``short_types`` is each type's slots left after its own candidates, before the fill; ``waiting``
    names what must be finished before the selection can be read; ``pending`` are the rows that passed
    every criterion, took no own slot and are held for the fill (empty once the fill has run)."""

    cases: tuple[str, ...]
    filled: tuple[str, ...]
    short_types: Mapping[str, int]
    waiting: tuple[str, ...]
    pending: tuple[str, ...] = ()

    @property
    def complete(self) -> bool:
        return not self.waiting

    @property
    def shortfall(self) -> int:
        return AT_MOST - len(self.cases) if self.complete else 0


@dataclass
class ExploratoryLog:
    rows: dict[str, ExploratoryRow] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    # step 5's search is recorded: no step can give a short type a row now
    step5_searched: bool = False
    # the hold on the fill is lifted (his decision, 2026-10-26): the fill runs without step 5
    fill_released: bool = False

    @property
    def fill_open(self) -> bool:
        return self.step5_searched or self.fill_released

    # --- the order -----------------------------------------------------------------------------------------

    def _key(self, row: ExploratoryRow) -> tuple[int, int, date, int, str]:
        """D.1: step 2 by first disclosure, the window's before the fallback month's; step 3's list, then
        step 4's, by id (their ids run on, newest filing first); step 5 by first disclosure. A row whose
        first-disclosure check is not done sorts first in its group, so the selection stops there; one that
        failed it has no date and sorts last."""
        rank = STEP_RANK[row.step]
        if row.step in PROBED_STEPS:
            tail = re.search(r"(\d+)$", row.id)
            return (rank, 0, date.min, int(tail.group(1)) if tail else 0, row.id)
        pool = STEP_POOLS[row.step].index(row.pool)
        if "first_disclosure" not in row.results:
            return (rank, pool, date.min, 0, row.id)
        return (rank, pool, row.disclosed or date.max, 0, row.id)

    def ordered(self) -> list[ExploratoryRow]:
        return sorted(self.rows.values(), key=self._key)

    @staticmethod
    def _why(row: ExploratoryRow) -> str:
        if "first_disclosure" not in row.results and row.step not in PROBED_STEPS:
            return f"{row.id}: no first-disclosure result, so its place in the order is unknown"
        if row.awaiting_read:
            return (
                f"{row.id}: its rejection on {row.awaiting_read} awaits the independent read, "
                "and it comes before any later case"
            )
        return f"{row.id}: not finished, and it comes before any later case"

    # --- the selection -------------------------------------------------------------------------------------

    def selection(self) -> ExploratorySelection:
        """D.2: per type the first k that pass, in order. D.3: slots of a type that cannot reach k go to the
        next candidates in the same order that pass, of any type. D.4: nothing is selected while an earlier
        candidate that could take the place is unfinished. D.5: five at most, which the slots add up to."""
        ordered = self.ordered()
        own: dict[str, list[str]] = {t: [] for t in TYPES}
        held: dict[str, str] = {}
        for row in ordered:
            if row.finished:
                if row.passed and row.type not in held and len(own[row.type]) < K[row.type]:
                    own[row.type].append(row.id)
                continue
            # a row whose list is not settled yet (maps_to_shape not met) may land on any list
            for t in (row.type,) if row.met("maps_to_shape") else TYPES:
                if len(own[t]) < K[t]:
                    held.setdefault(t, self._why(row))
        short = {t: K[t] - len(own[t]) for t in TYPES if len(own[t]) < K[t]}
        waiting = list(held.values())
        taken = {i for ids in own.values() for i in ids}
        filled: list[str] = []
        slots = sum(short.values())
        if slots and held:
            waiting.append(
                "a short type's slots go to the next candidates, and a type is still open"
            )
        elif slots and not self.fill_open:
            waiting.append(HELD_FILL)
        elif slots:
            for row in ordered:
                if row.id in taken:
                    continue
                if not row.finished:
                    waiting.append(self._why(row))
                    break
                if row.passed:
                    filled.append(row.id)
                    if len(filled) == slots:
                        break
        chosen = taken | set(filled)
        held_fill = bool(slots) and (bool(held) or not self.fill_open)
        pending = tuple(
            r.id for r in ordered if held_fill and r.finished and r.passed and r.id not in chosen
        )
        return ExploratorySelection(
            tuple(r.id for r in ordered if r.id in chosen),
            tuple(r.id for r in ordered if r.id in filled),
            short,
            tuple(waiting),
            pending,
        )

    def _after_the_fifth(self, row: ExploratoryRow) -> bool:
        """D.5: checking stops when five cases are selected; a candidate after the fifth is never checked."""
        chosen = self.selection().cases
        if len(chosen) < AT_MOST or row.id in chosen:
            return False
        return self._key(row) > max(self._key(self.rows[c]) for c in chosen)

    def problems(self) -> list[str]:
        """What stops the log being complete: a rejection that must be read and has not been, and one filing
        taken as a case twice (one decision is one case; §12.5 decides its shape)."""
        lines = [
            f"{row.id}: its rejection on {row.failed} has not been read by the independent reader"
            for row in self.rows.values()
            if row.failed in row.read_required and row.failed not in row.reads
        ]
        taken: dict[str, list[str]] = {}
        for case_id in self.selection().cases:
            taken.setdefault(self.rows[case_id].accession, []).append(case_id)
        lines.extend(
            f"one filing is a case twice ({', '.join(ids)}): one decision is one case"
            for ids in taken.values()
            if len(ids) > 1
        )
        return lines

    # --- the changes: each is an event, applied once here and again when a saved file is replayed -----------

    def add(self, row_id: str, case_type: str, step: str, pool: str, accession: str) -> None:
        """A candidate that is not carried: step 2's new channel, the pool of steps 3 and 4, step 5's
        search."""
        event = {"event": "add", "id": row_id, "type": case_type, "step": step}
        self._take({**event, "pool": pool, "accession": accession})

    def carry(self, row_id: str, source_text: str, source_name: str) -> None:
        """A pre-registered row, with its results before criterion 4 (§4.6.5 B.2), from ``source_text``,
        the text of ``source_name``. Its criterion 4 is recorded again here."""
        digest = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
        self._take(
            {"event": "carry", "id": row_id, "log": source_name, "log_sha256": digest},
            {source_name: source_text},
        )

    def mark_searched(self) -> None:
        """Step 5's search has run, with rows or none: no step is left to give a short type a row, so the fill
        (D.3) may run. Recorded once, and after every row the search brings in has been added."""
        self._take({"event": "searched", "step": "5"})

    def release_fill(self, on: date, reason: str) -> None:
        """His decision, 2026-10-26: the hold on the fill is lifted, so a short type's slots go to the pending
        rows now (D.3 as written) and step 5 does not run. Recorded once, with its date and his reason, and
        never after step 5's search, when the fill runs anyway."""
        self._take({"event": "released", "on": on.isoformat(), "reason": reason})

    def record(
        self,
        row_id: str,
        criterion: str,
        result: str,
        reason: str,
        *,
        public_reason: str | None = None,
        disclosed: date | None = None,
        case_type: str | None = None,
        empty: bool = False,
    ) -> None:
        """The next criterion for a row, as the selection log takes it. ``case_type`` is allowed on
        ``maps_to_shape`` only: the list the row is on is settled there. ``empty`` is allowed on a pool row's
        ``not_known`` failure only, when a call came back empty three times: that failure is never read."""
        event: dict[str, Any] = {
            "event": "result",
            "id": row_id,
            "criterion": criterion,
            "result": result,
            "reason": reason,
            "public_reason": public_reason,
            "disclosed": disclosed.isoformat() if disclosed else None,
            "case_type": case_type,
        }
        self._take({**event, "empty": True} if empty else event)

    def record_read(
        self,
        row_id: str,
        criterion: str,
        *,
        reply: ReaderReply,
        resolution: str | None = None,
    ) -> None:
        """The independent reader's read of a rejection, logged from its reply as the selection log
        does. The verdict is the reply's reading alone: "pass" disputes, anything else lets the
        rejection stand. There is no list to fail on here (§4.6.5 step 1 item 1), so a type the reader
        names on a disputed ``maps_to_shape`` read is the list the row goes on."""
        self._take(
            {
                "event": "read",
                "id": row_id,
                "criterion": criterion,
                "reply": reply.reply,
                "reply_sha256": reply.reply_sha256,
                "reading": reply.reading,
                "reply_type": reply.type,
                "resolution": resolution,
            }
        )

    def _take(self, event: dict[str, Any], sources: Mapping[str, str] | None = None) -> None:
        self._apply(event, sources or {})
        self.events.append(event)

    def _row(self, row_id: str) -> ExploratoryRow:
        if row_id not in self.rows:
            raise LogError(f"no candidate {row_id!r} in the log")
        return self.rows[row_id]

    def _apply(self, event: dict[str, Any], sources: Mapping[str, str]) -> None:
        kind = event["event"]
        if kind == "add":
            self._apply_add(event)
        elif kind == "carry":
            self._apply_carry(event, sources)
        elif kind == "result":
            self._apply_result(event)
        elif kind == "read":
            self._apply_read(event)
        elif kind == "searched":
            self._apply_searched(event)
        elif kind == "released":
            self._apply_released(event)
        else:
            raise LogError(f"{kind!r} is not an event of the exploratory log")

    def _apply_searched(self, event: dict[str, Any]) -> None:
        if event["step"] != "5":
            raise LogError(
                "only step 5's search is recorded as run: the others are known from their lists"
            )
        if self.step5_searched:
            raise LogError("step 5's search is already recorded")
        if self.fill_released:
            raise LogError("the hold on the fill is lifted: step 5 does not run")
        self.step5_searched = True

    def _apply_released(self, event: dict[str, Any]) -> None:
        date.fromisoformat(event["on"])
        if not str(event["reason"]).strip():
            raise LogError("lifting the hold on the fill has its reason")
        if self.fill_released:
            raise LogError("the hold on the fill is already lifted")
        if self.step5_searched:
            raise LogError(
                "step 5's search is recorded: the fill runs, and there is no hold to lift"
            )
        self.fill_released = True

    def _apply_add(self, event: dict[str, Any]) -> None:
        row_id, case_type, step = str(event["id"]), event["type"], event["step"]
        if row_id in self.rows:
            raise LogError(f"{row_id} is already in the log")
        if case_type not in TYPES:
            raise LogError(f"a type is one of {', '.join(TYPES)}")
        if step not in STEP_POOLS or event["pool"] not in STEP_POOLS[step]:
            raise LogError(f"step {step!r} with pool {event['pool']!r} is not one of §4.6.5's")
        if step == "5" and self.step5_searched:
            raise LogError(f"{row_id}: step 5's search is recorded, so it brings no row after that")
        if step == "5" and self.fill_released:
            raise LogError(f"{row_id}: the hold on the fill is lifted, so step 5 does not run")
        if not str(event["accession"]).strip():
            raise LogError("a candidate has its accession number")
        self.rows[row_id] = ExploratoryRow(
            row_id, case_type, event["pool"], str(event["accession"]), step=step
        )

    def _apply_carry(self, event: dict[str, Any], sources: Mapping[str, str]) -> None:
        row_id, name = str(event["id"]), str(event["log"])
        if row_id in self.rows:
            raise LogError(f"{row_id} is already in the log")
        if not SOURCE_LOG.fullmatch(name):
            raise LogError("a row is carried from a selection-log-<n>.json")
        text = sources.get(name)
        if text is None:
            raise LogError(f"{name} is needed to read the carried rows and is not there")
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != event["log_sha256"]:
            raise LogError(f"{name} is not the file {row_id} was carried from: its sha256 differs")
        old = SelectionLog.from_text(text).rows.get(row_id)
        if old is None:
            raise LogError(f"no candidate {row_id!r} in {name}")
        if not all(old.met(c) for c in CARRIED):
            raise LogError(f"{row_id} did not meet every criterion before maps_to_shape in {name}")
        self.rows[row_id] = ExploratoryRow(
            row_id,
            old.type,
            old.pool,
            old.accession,
            results={c: copy.copy(old.results[c]) for c in CARRIED},
            reads={c: copy.copy(old.reads[c]) for c in CARRIED if c in old.reads},
            step="2",
            source=(name, str(event["log_sha256"])),
            prior_replies=frozenset(r.reply for r in old.reads.values() if r.reply),
        )

    def _apply_result(self, event: dict[str, Any]) -> None:
        row = self._row(str(event["id"]))
        criterion, result, reason = event["criterion"], event["result"], event["reason"]
        disclosed = date.fromisoformat(event["disclosed"]) if event["disclosed"] else None
        if criterion not in row.criteria:
            raise LogError(f"{criterion!r} is not a criterion: {', '.join(row.criteria)}")
        if result not in ("pass", "fail"):
            raise LogError("a result is 'pass' or 'fail'")
        if not str(reason).strip():
            raise LogError("every result needs its reason")
        if row.failed is not None:
            raise LogError(f"{row.id} already failed {row.failed}; nothing follows a failure")
        expected = next((c for c in row.criteria if c not in row.results), None)
        if criterion != expected:
            raise LogError(
                f"{row.id}: the next criterion is {expected}, not {criterion} "
                "(they are checked in order, none skipped)"
            )
        if (criterion == "first_disclosure" and result == "pass") != (disclosed is not None):
            raise LogError(
                "a passed first-disclosure check carries its date (the order the cases are taken in), "
                "and no other result does"
            )
        case_type = event["case_type"]
        if case_type is not None and (criterion != "maps_to_shape" or case_type not in TYPES):
            raise LogError(f"a list is one of {', '.join(TYPES)}, and is settled at maps_to_shape")
        empty = bool(event.get("empty"))
        if empty and not (row.probed and criterion == KNOWLEDGE and result == "fail"):
            raise LogError(
                f"only a pool row's {KNOWLEDGE} failure is recorded as a call empty three times"
            )
        if self._after_the_fifth(row):
            raise LogError(
                f"{row.id} comes after the fifth case: checking stops at five (§4.6.5 D.5)"
            )
        row.empty_fail = empty
        row.results[criterion] = Result(
            result, reason, event["public_reason"], disclosed.isoformat() if disclosed else None
        )
        if case_type is not None:
            row.type = case_type

    def _apply_read(self, event: dict[str, Any]) -> None:
        row = self._row(str(event["id"]))
        criterion, reading, reply_type = event["criterion"], event["reading"], event["reply_type"]
        if criterion not in row.read_required:
            raise LogError(f"only a rejection on {', '.join(row.read_required)} is read")
        if reading not in READINGS:
            raise LogError(f"a read's reading is one of {', '.join(READINGS)}")
        if not (
            str(event["reply"]).strip() and re.fullmatch(r"[0-9a-f]{64}", event["reply_sha256"])
        ):
            raise LogError("a read names the reader's reply file and its sha256")
        if reply_type is not None and (criterion != "maps_to_shape" or reply_type not in TYPES):
            raise LogError(f"a read of {criterion} carries no type, and a type is one of the lists")
        if event["reply"] in row.prior_replies:
            raise LogError(
                f"{event['reply']} is the pre-registered record's read of an earlier rejection; "
                f"this rejection needs its own read"
            )
        if row.source is not None and criterion in CARRIED:
            raise LogError(
                f"{row.id}'s {criterion} is carried from {row.source[0]}; it is not read here"
            )
        result = row.results.get(criterion)
        if result is None or result.result != "fail":
            raise LogError(f"{row.id} did not fail {criterion}")
        agrees = reading != "pass"
        resolution = event["resolution"]
        if not agrees and not (resolution and str(resolution).strip()):
            raise LogError("a disagreement is resolved by him and logged with the reason")
        later = row.criteria[row.criteria.index(criterion) + 1 :]
        previous = row.reads.get(criterion)
        if (
            previous is not None
            and previous.agrees != agrees
            and any(c in row.results for c in later)
        ):
            raise LogError(
                f"{row.id}: {criterion} was read as "
                f"{'agreed' if previous.agrees else 'disputed'} and later criteria are recorded; "
                "a read cannot change now"
            )
        row.reads[criterion] = Read(
            agrees, resolution, event["reply"], event["reply_sha256"], reading, reply_type
        )
        if not agrees and reply_type is not None:
            row.type = reply_type

    # --- saving and the public view ------------------------------------------------------------------------

    def to_text(self) -> str:
        return (
            json.dumps(
                {"exploratory_version": EXPLORATORY_VERSION, "events": self.events},
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )

    @staticmethod
    def source_names(text: str) -> list[str]:
        """The pre-registered log files a saved log carries rows from, so the caller can read them."""
        try:
            names = {e["log"] for e in json.loads(text)["events"] if e["event"] == "carry"}
        except (ValueError, KeyError, TypeError) as exc:
            raise LogError(f"the exploratory log cannot be read: {type(exc).__name__}") from exc
        return sorted(str(n) for n in names)

    @classmethod
    def from_text(cls, text: str, sources: Mapping[str, str] | None = None) -> ExploratoryLog:
        """A saved log, rebuilt event by event through the code that took each, so a hand-edited file cannot
        step around the rules. ``sources`` holds the text of each selection-log file the log carries rows from
        (``source_names``); a carried row's results come from there and from nowhere else."""
        try:
            raw = json.loads(text)
            if raw["exploratory_version"] != EXPLORATORY_VERSION:
                raise LogError(
                    f"the log has version {raw['exploratory_version']!r}; "
                    f"this reader knows {EXPLORATORY_VERSION}"
                )
            log = cls()
            for event in raw["events"]:
                log._take(dict(event), sources or {})
            return log
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise LogError(f"the exploratory log cannot be read: {type(exc).__name__}") from exc

    def public_view(self) -> dict[str, Any]:
        """No name, accession number, date or industry code. A row is its neutral id, its step and each
        criterion's result; a reason appears only where a ``public_reason`` was written. Every case carries
        its label (§4.6.5 B.3)."""
        chosen = self.selection()
        cases = [self.rows[c] for c in chosen.cases]
        return {
            "at_most": AT_MOST,
            "cases": list(chosen.cases),
            "filled": list(chosen.filled),
            "pending": list(chosen.pending),
            "fill_released": self.fill_released,
            "complete": chosen.complete,
            "shortfall": chosen.shortfall,
            "short_types": dict(chosen.short_types),
            "types": {t: {"k": K[t], "cases": sum(1 for r in cases if r.type == t)} for t in TYPES},
            "rows": [
                {
                    "id": r.id,
                    "step": r.step,
                    "type": r.type,
                    "carried": r.source is not None,
                    "passed": r.passed,
                    "case": r.id in chosen.cases,
                    **({"label": r.label} if r.id in chosen.cases else {}),
                    "criteria": {
                        c: {
                            "result": r.results[c].result,
                            "reason": r.results[c].public_reason,
                            **({"disputed": True} if r.disputed(c) else {}),
                        }
                        for c in r.criteria
                        if c in r.results
                    },
                    "independent_read": {
                        c: {"agrees": read.agrees} for c, read in sorted(r.reads.items())
                    },
                }
                for r in self.ordered()
                if r.results
            ],
        }


def load_newest_exploratory(case: CaseAppendix) -> ExploratoryLog:
    """The log in the highest-numbered ``exploratory-log-<n>.json`` (numerically), replayed with the selection
    logs it carries rows from, read from the same folder; an empty log if none has been written."""
    numbers = [
        int(m.group(1))
        for path in case.directory.glob("exploratory-log-*.json")
        if (m := re.fullmatch(r"exploratory-log-(\d+)\.json", path.name))
    ]
    if not numbers:
        return ExploratoryLog()
    name = f"exploratory-log-{max(numbers)}.json"
    try:
        text = (case.directory / name).read_text(encoding="utf-8")
        sources = {
            source: (case.directory / source).read_text(encoding="utf-8")
            for source in ExploratoryLog.source_names(text)
            if SOURCE_LOG.fullmatch(source)
        }
    except OSError as exc:
        raise LogError(
            f"cannot read {name} or its sources: {exc.strerror or type(exc).__name__}"
        ) from exc
    return ExploratoryLog.from_text(text, sources)


# the search's list, step 2's channel, then the pools of steps 3 and 4
CANDIDATE_FILES = ("candidates.json", PRESS_CANDIDATES, PRE_CANDIDATES, STEP4_CANDIDATES)


def exploratory_started(case: CaseAppendix) -> bool:
    """An exploratory log has been written, so the pre-registered log is closed (§4.6.5 A.1)."""
    return any(case.directory.glob("exploratory-log-*.json"))


def row_for(search: CaseAppendix, label: str) -> Row | None:
    """The one answer to "which row is this label's" (§4.6.5 B.4): the exploratory log's row when it has one,
    else the pre-registered log's. A carried row is therefore never read from the old log."""
    row = load_newest_exploratory(search).rows.get(label)
    if row is not None:
        return row
    return load_newest_log(search).rows.get(label)


def candidate_records(search: CaseAppendix) -> dict[str, dict[str, Any]] | None:
    """Every candidate's private record by id, from the search's list, the press channel's list and step 3's
    pool when they exist; None if no candidate file is there. An id is in one file only."""
    found: dict[str, dict[str, Any]] = {}
    present = False
    for name in CANDIDATE_FILES:
        path = search.directory / name
        if not path.exists():
            continue
        present = True
        try:
            records = {c["id"]: c for c in json.loads(path.read_text(encoding="utf-8"))["list"]}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise LogError(f"{name} cannot be read: {type(exc).__name__}") from exc
        both = sorted(found.keys() & records.keys())
        if both:
            raise LogError(f"{', '.join(both)} is in more than one candidate list")
        found.update(records)
    return found if present else None


def newest_selection_log_name(case: CaseAppendix) -> str:
    """The name of the highest-numbered ``selection-log-<n>.json``: the pre-registered record's last version,
    which a row is carried from (§4.6.5 B.2)."""
    numbers = [
        int(m.group(1))
        for path in case.directory.glob("selection-log-*.json")
        if (m := re.fullmatch(r"selection-log-(\d+)\.json", path.name))
    ]
    if not numbers:
        raise LogError("there is no selection log yet: the search has not run")
    return f"selection-log-{max(numbers)}.json"


def read_source_log(case: CaseAppendix, name: str) -> str:
    """A pre-registered selection log's text, for ``carry``. Only a ``selection-log-<n>.json`` in the
    folder."""
    if not SOURCE_LOG.fullmatch(name):
        raise LogError("a row is carried from a selection-log-<n>.json")
    try:
        return (case.directory / name).read_text(encoding="utf-8")
    except OSError as exc:
        raise LogError(f"cannot read {name}: {exc.strerror or type(exc).__name__}") from exc


def write_exploratory_version(case: CaseAppendix, log: ExploratoryLog) -> str:
    """The next ``exploratory-log-<n>.json`` and ``exploratory-public-<n>.json``, never overwriting an earlier
    one. Returns the private log's file name."""
    number = 1
    while (case.directory / f"exploratory-log-{number}.json").exists():
        number += 1
    name = f"exploratory-log-{number}.json"
    case.write_once(case.directory / name, log.to_text().encode("utf-8"))
    public = json.dumps(log.public_view(), indent=2, ensure_ascii=False) + "\n"
    case.write_once(case.directory / f"exploratory-public-{number}.json", public.encode("utf-8"))
    return name
