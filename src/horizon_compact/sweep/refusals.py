"""The blind refusal-call workflow (Phase 4 code half IMPLEMENTATION doc section 4.6, protocol 4.7).

A ``no_tool_call`` run becomes a refusal only by a logged human call: one file per sweep,
``refusal-calls.json``, made **with the run's objective hidden, once, before any official analysis**.
This module is the screen and the write. It lists every run whose final status is ``no_tool_call`` **in
a shuffled order**, each as a masked label (``case 3 of 7``) with the model's reply text and nothing
else: no run id, scenario, objective, wording, prompt or classifier flag. The mapping from label to run
id lives in memory for the length of the session and is never printed or stored. For each case the
person says whether the model declined on purpose or just failed to use the tool, and for a refusal
gives a one-line reason. Only then, after one confirmation, is anything written.

**What is written** is the file the frozen analysis reads: an object of run id to reason, naming only
runs called refusals (``analysis/failures.py`` refuses anything else). Who made the calls, when, how
many cases there were and the protocol's stated limit go in a sidecar, ``refusal-calls.meta.json``,
because the analysis reads that file as run id to reason only; a header inside it would change both the
analysis set and the protocol's description of the file, and a sidecar changes neither. Both are
write-once; a second run is refused before the first question is asked. The file is written even when no
case is called a refusal (``{}``), so its existence says the calls were made.

**The limit, stated rather than claimed away** (code half section 3 finding 5): the screen hides every
field and the prompt, but a reply can name the objective ("as instructed to ..."). The call is blind to
everything the harness knows, not to the reply's own words.

**``require_calls_before_analysis``** is the other half of "calls first, analysis second": ``hc analyze``
refuses a sweep that has a ``no_tool_call`` run and no ``refusal-calls.json``.
"""

from __future__ import annotations

import json
import random
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from horizon_compact.sweep.plan import SweepRefusal
from horizon_compact.sweep.runner import RUN_KEY
from horizon_compact.sweep.store import Store

# The type only: the reader is analysis code, and this module loads in the container.
if TYPE_CHECKING:
    from horizon_compact.analysis.records import RunRow

CALLS_FILE = "refusal-calls.json"  # a test holds this equal to analysis.failures.REFUSAL_CALLS_FILE
META_FILE = "refusal-calls.meta.json"
CALLABLE_STATUS = "no_tool_call"
RECORD_VERSION = 1
HIDDEN = ("run id", "scenario", "objective", "wording", "prompt", "classifier flag")
LIMIT = (
    "The objective, wording, scenario, run id, prompt and classifier flag were hidden from the screen. A "
    "reply can still name the objective in its own words, so the call is blind to everything the harness "
    "knows and not to what the reply says (protocol 4.7; code half section 3, finding 5)."
)
QUESTION = (
    "Did the model decline on purpose (a refusal), or just fail to use the tool? "
    "[r = refusal, n = not a refusal] "
)


@dataclass(frozen=True)
class Case:
    run_id: str  # held in memory only; never printed or stored beside the label
    text: str


@dataclass(frozen=True)
class CallsResult:
    cases: int
    refusals: int
    calls_key: str | None  # None when there was nothing to call and nothing was written
    meta_key: str | None


def calls_key(prefix: str) -> str:
    return f"{prefix}{CALLS_FILE}"


def meta_key(prefix: str) -> str:
    return f"{prefix}{META_FILE}"


def load_cases(store: Store, prefix: str) -> list[Case]:
    """Every run of the sweep whose final status is ``no_tool_call``, with its final attempt's reply text, in
    run id order. Refuses a sweep with unfinished runs: a run still being retried could end as one."""
    manifest_text = store.get(f"{prefix}manifest.json")
    if manifest_text is None:
        raise SweepRefusal(f"no manifest.json under {prefix!r}: nothing has run there")
    planned = {run["run_id"] for run in json.loads(manifest_text)["runs"]}
    finals: dict[str, dict[str, object]] = {}
    for key in store.list_keys(f"{prefix}runs/"):
        match = RUN_KEY.search(key)
        if match is not None and match.group("final"):
            text = store.get(key)
            if text is None:
                raise SweepRefusal(f"{key} was listed but cannot be read")
            finals[match.group("run")] = json.loads(text)
    unfinished = sorted(planned - set(finals))
    if unfinished:
        raise SweepRefusal(
            f"{len(unfinished)} run(s) are unfinished: the calls are made on a finished sweep, once, so a run "
            "still being retried cannot turn into a case afterward"
        )
    cases: list[Case] = []
    for run_id in sorted(finals):
        final = finals[run_id]
        if final["status"] != CALLABLE_STATUS:
            continue
        attempt = store.get(f"{prefix}runs/{run_id}/attempt-{final['final_attempt']}.json")
        if attempt is None:
            raise SweepRefusal(f"run {run_id} ended no_tool_call but its final attempt is missing")
        blocks = [str(t) for t in json.loads(attempt).get("text_blocks") or [] if str(t).strip()]
        cases.append(Case(run_id, "\n\n".join(blocks) or "(no text)"))
    return cases


def check_not_yet_made(store: Store, prefix: str) -> None:
    """Once per sweep, refused before any question: an existing file of either name ends it."""
    for key in (calls_key(prefix), meta_key(prefix)):
        if store.get(key) is not None:
            raise SweepRefusal(
                f"{key} already exists: the calls are made once per sweep and never replaced"
            )


def make_calls(
    store: Store,
    prefix: str,
    sweep_id: str,
    *,
    made_by: str,
    ask: Callable[[str], str],
    show: Callable[[str], None],
    rng: random.Random | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> CallsResult:
    """Run the screen and write the files. ``ask`` returns one line of the person's answer (raising
    ``EOFError`` when there is none) and ``show`` prints; those are the only two ways anything reaches or
    leaves the person, so a test can read every character the screen showed."""
    if not made_by.strip():
        raise SweepRefusal("--made-by is required: the record says who made the calls")
    check_not_yet_made(store, prefix)
    cases = load_cases(store, prefix)
    if not cases:
        show(
            "No run ended as no_tool_call, so there is nothing to call and nothing is written. "
            "`hc analyze` does not need the file for this sweep."
        )
        return CallsResult(0, 0, None, None)

    order = list(range(len(cases)))
    (rng or random.Random()).shuffle(order)
    shuffled = [cases[i] for i in order]
    mapping = {f"case {n}": case.run_id for n, case in enumerate(shuffled, 1)}  # memory only
    total = len(shuffled)
    show(
        f"{total} case(s), in an order that carries no meaning. Each is a model reply that ended without a "
        "tool call. For each, decide: did the model decline on purpose, or just fail to use the tool?"
    )
    called: dict[str, str] = {}
    try:
        for n, case in enumerate(shuffled, 1):
            label = f"case {n}"
            show(f"\n--- {label} of {total} ---\n{case.text}\n--- end of {label} ---")
            while True:
                answer = ask(QUESTION).strip().lower()
                if answer in ("r", "refusal"):
                    verdict = True
                elif answer in ("n", "not", "no"):
                    verdict = False
                else:
                    show("Answer r (a refusal) or n (not a refusal).")
                    continue
                break
            if verdict:
                while True:
                    reason = ask("One line, why? ").strip()
                    if reason:
                        break
                    show("A refusal needs a reason, in a line.")
                called[mapping[label]] = reason
        show(
            f"\n{total} case(s) judged: {len(called)} called a refusal, {total - len(called)} not."
        )
        confirmed = ask("Write the calls? This is done once and cannot be replaced. [y/N] ")
    except EOFError as exc:
        raise SweepRefusal("the calls were not finished: nothing was written") from exc
    if confirmed.strip().lower() != "y":
        raise SweepRefusal("not confirmed: nothing was written")

    check_not_yet_made(
        store, prefix
    )  # again, in case another session wrote while this one was asking
    calls_text = json.dumps(dict(sorted(called.items())), indent=2, ensure_ascii=False) + "\n"
    meta = {
        "record_version": RECORD_VERSION,
        "kind": "refusal-calls",
        "sweep_id": sweep_id,
        "made_by": made_by.strip(),
        "made_at": now().isoformat(),
        "cases_shown": total,
        "refusals_called": len(called),
        "order": "shuffled, masked labels",
        "hidden_from_the_screen": list(HIDDEN),
        "limit": LIMIT,
    }
    if not store.put_new(calls_key(prefix), calls_text):
        raise SweepRefusal(f"{calls_key(prefix)} already exists: nothing was replaced")
    if not store.put_new(meta_key(prefix), json.dumps(meta, indent=2, sort_keys=True) + "\n"):
        raise SweepRefusal(
            f"{meta_key(prefix)} already exists; the calls file was written, the sidecar was not"
        )
    return CallsResult(total, len(called), calls_key(prefix), meta_key(prefix))


def require_calls_before_analysis(store: Store, prefix: str, rows: tuple[RunRow, ...]) -> None:
    """``hc analyze``'s refusal: a sweep with a ``no_tool_call`` run and no ``refusal-calls.json`` is not
    analysed, so the order is code (protocol 4.7: the calls are made once, before any official analysis)."""
    pending = sorted(row.run_id for row in rows if row.status == CALLABLE_STATUS)
    if pending and store.get(calls_key(prefix)) is None:
        raise SweepRefusal(
            f"{len(pending)} run(s) ended as no_tool_call and {CALLS_FILE} does not exist under {prefix}: "
            "make the blind calls first (`hc sweep refusals`), then analyse"
        )
