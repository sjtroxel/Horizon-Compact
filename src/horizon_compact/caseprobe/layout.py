"""Where a real case's content and probe records live in the results bucket (search-half doc §4.8).

Everything is under ``cases/``, which the publish path never reads and no manifest lists; the task role is
granted ``cases/*`` and nothing wider. Objects are write-once.

* content: ``cases/<label>/set-<n>/{dossier,scenario,rubric}.toml``
* a probe call: ``cases/<label>/probes/set-<n>/<model>/call-<i>.json``
* its verdict:  ``cases/<label>/probes/set-<n>/<model>/call-<i>.verdict.json``
* a call that failed with an API error: ``.../<model>/errors/call-<i>-<k>.json`` (a call made, no answer)
* a case sweep: ``cases/<label>/runs/<sweep_id>/`` (manifest, ``order.json``, runs, sessions). Private like
  the rest: every attempt record holds the request, which holds the dossier.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from horizon_compact.protocol.cases import PROBE_CALLS

CASES_PREFIX = "cases"
# Protocol §12.8, word for word: the user message of every recognition-probe call. A test compares it with
# the protocol's own text.
PROBE_MESSAGE = "Which company is this? If you are not sure, say unknown."
# The models a case's recognition probe may name (the experiment's own set, protocol §12.8), by role.
PROBE_ROLES = ("main", "second_family")
# Room for an answer, a reasoning model's reasoning included. One word is the usual answer.
PROBE_MAX_TOKENS = 4000
CONTENT_FILES = ("dossier.toml", "scenario.toml", "rubric.toml")

__all__ = [
    "CALL_KEY",
    "CASES_PREFIX",
    "CONTENT_FILES",
    "PROBE_CALLS",
    "PROBE_MAX_TOKENS",
    "PROBE_MESSAGE",
    "PROBE_ROLES",
    "CallKey",
    "call_key",
    "content_key",
    "error_key",
    "parse_call_key",
    "probes_prefix",
    "runs_prefix",
    "verdict_key",
]

_LABEL = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
_MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_SWEEP = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
CALL_KEY = re.compile(
    rf"{CASES_PREFIX}/(?P<label>[^/]+)/probes/set-(?P<set>\d+)/(?P<model>[^/]+)/call-(?P<call>\d+)\.json"
)


def _label(label: str) -> str:
    if not _LABEL.fullmatch(label):
        raise ValueError(f"{label!r} is not a case label")
    return label


def _model(model_key: str) -> str:
    if not _MODEL.fullmatch(model_key):
        raise ValueError(f"{model_key!r} is not a model key")
    return model_key


def _sweep(sweep_id: str) -> str:
    if not _SWEEP.fullmatch(sweep_id):
        raise ValueError(f"{sweep_id!r} is not a sweep id")
    return sweep_id


def content_key(label: str, probe_set: int, filename: str) -> str:
    if filename not in CONTENT_FILES:
        raise ValueError(f"{filename!r} is not one of {', '.join(CONTENT_FILES)}")
    return f"{CASES_PREFIX}/{_label(label)}/set-{probe_set}/{filename}"


def probes_prefix(label: str, probe_set: int | None = None) -> str:
    base = f"{CASES_PREFIX}/{_label(label)}/probes/"
    return base if probe_set is None else f"{base}set-{probe_set}/"


def runs_prefix(label: str, sweep_id: str | None = None) -> str:
    """Where a case's sweeps live; with ``sweep_id``, where one sweep does."""
    base = f"{CASES_PREFIX}/{_label(label)}/runs/"
    return base if sweep_id is None else f"{base}{_sweep(sweep_id)}/"


def call_key(label: str, probe_set: int, model_key: str, call: int) -> str:
    return f"{probes_prefix(label, probe_set)}{_model(model_key)}/call-{call}.json"


def verdict_key(label: str, probe_set: int, model_key: str, call: int) -> str:
    return f"{probes_prefix(label, probe_set)}{_model(model_key)}/call-{call}.verdict.json"


def error_key(label: str, probe_set: int, model_key: str, call: int, n: int) -> str:
    return f"{probes_prefix(label, probe_set)}{_model(model_key)}/errors/call-{call}-{n}.json"


@dataclass(frozen=True)
class CallKey:
    label: str
    probe_set: int
    model_key: str
    call: int


def parse_call_key(key: str) -> CallKey | None:
    """A call object's key as its parts, or None for any other key (a verdict, an error, content)."""
    match = CALL_KEY.fullmatch(key)
    if match is None:
        return None
    return CallKey(match["label"], int(match["set"]), match["model"], int(match["call"]))
