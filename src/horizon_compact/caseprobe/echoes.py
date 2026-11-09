"""``hc case echoes``: how many published real-case memos repeat something distinctive from their withheld
case text (Phase 6 IMPLEMENTATION doc section 22, decision 5 as widened 2026-11-09).

**Why it exists.** Phase 5.5's memo scan (``caseprobe/memos.py``) looked for company **names** and held a memo
whose flagged words all came from a withheld dossier. It did not look at unflagged words or at figures, so a
published memo can repeat a product line, a program name or a scale-free figure that the model read in its
withheld dossier. This counts how many do, so the explorer's choice for real-case memos (decision 5) rests on
counts, not on one sample. **It changes nothing it reads**, holds back nothing, and calls no model and no AWS.

**What it reads.** ``cases.json`` and each case's ``case.lock``; the case's dossier and scenario from the
private appendix, refused unless each hashes to ``case.lock`` (so the text compared is the text the model was
given); every ``<model>-memos.jsonl`` in the case's results folder (a ``"held"`` line is skipped: it was
never published); and, as the reference text, every ``.toml``, ``.txt`` and ``.md`` file under
``experiment/`` outside ``results/`` and ``cases/`` (the fictional company, the protocol, the reader briefs).

**The rule, mechanical and fixed here.** The *withheld text* of a case is every string and number in its
dossier and scenario files. Three kinds of token are taken from a text after the memo scan's own ``fold``:

- a **word**: three or more letters, no digit;
- a **percentage**: a number written with ``%`` or "percent";
- a **figure**: any other number of two or more digits, unless it is written with ``$`` or followed by
  million, billion, thousand or trillion (dollar amounts are scaled by a hidden factor, protocol section 12.6,
  so they do not point at the company).

A token is **distinctive** for a case when it is in the case's withheld text and in none of: the reference
text; the case's published description, if it has one; and, for words only, the published memos of every
other case (a word that memos about other companies also use is ordinary business English). A published memo
is **counted** for a kind when it holds at least one distinctive token of that kind.

**It is an upper bound, and says so.** A distinctive word can still be an ordinary one the reference text
happens to lack; the counts include those. It cannot see a term the model knew from training and the dossier
lacks. The private report lists every token counted, so he can judge which, if any, point toward a company.

**What is public, what is private, what is printed.** The public file
(``docs/phases/evidence/phase-6/memo-echoes.json``) holds counts, labels, model keys and hashes only: no
token, no memo text, by construction. The private report (``memo-echoes.json`` in each case's appendix
folder) holds the tokens with the run ids that carry them. The command prints counts only.
"""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.caseprobe.memos import HELD, fold

METHOD_VERSION = 1
SCHEMA = "horizon-compact/memo-echoes"
PUBLIC_PATH = Path("docs") / "phases" / "evidence" / "phase-6" / "memo-echoes.json"
PRIVATE_NAME = "memo-echoes.json"
CASES_FILE = Path("experiment") / "results" / "cases" / "cases.json"
RESULTS_CASES = Path("experiment") / "results" / "cases"
LOCKS = Path("experiment") / "cases"
EXPERIMENT = Path("experiment")
REFERENCE_SUFFIXES = (".toml", ".txt", ".md")
REFERENCE_SKIP = ("results", "cases")
MEMOS_SUFFIX = "-memos.jsonl"
KINDS = ("word", "percent", "figure")

_PLAIN = re.compile(r"[a-z0-9][a-z0-9-]*")
_WORD = re.compile(r"[^\W\d_]{3,}")
# A number, with what is written around it: a dollar sign before, a percent sign or a scale word after.
_NUMBER = re.compile(
    r"(?<![\w.,])(?P<dollar>\$\s?)?(?P<num>\d{1,3}(?:,\d{3})+|\d+)(?P<dec>\.\d+)?(?![\w])"
    r"(?P<pct>\s?%|\s?percent\b|\s?per cent\b)?"
    r"(?P<scale>\s?(?:million|billion|thousand|trillion)\b)?"
)


class EchoRefusal(Exception):
    """The count cannot be made without asserting something that is not true. The message names a file and a
    kind of failure, never a token or a memo's text."""


# --- tokens ------------------------------------------------------------------------------------------------


def _number(whole: str, decimals: str | None) -> str:
    text = whole.replace(",", "") + (decimals or "")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text.lstrip("0") or "0"


def tokens(text: str) -> dict[str, set[str]]:
    """The three kinds of token in ``text``, after the memo scan's ``fold``."""
    folded = fold(text)
    found: dict[str, set[str]] = {kind: set() for kind in KINDS}
    found["word"] = set(_WORD.findall(folded))
    for match in _NUMBER.finditer(folded):
        value = _number(match["num"], match["dec"])
        if match["pct"]:
            found["percent"].add(value)
        elif match["dollar"] or match["scale"]:
            continue  # a dollar amount: scaled, protocol section 12.6
        elif sum(ch.isdigit() for ch in value) >= 2:
            found["figure"].add(value)
    return found


def _merge(into: dict[str, set[str]], more: Mapping[str, set[str]]) -> None:
    for kind in KINDS:
        into[kind] |= more[kind]


def _empty() -> dict[str, set[str]]:
    return {kind: set() for kind in KINDS}


def _strings(value: Any) -> Iterable[str]:
    """Every string and number in a parsed TOML document, as text."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, bool):
        return
    elif isinstance(value, int | float):
        yield str(value)
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


# --- reading -----------------------------------------------------------------------------------------------


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reference_files(root: Path) -> list[Path]:
    base = root / EXPERIMENT
    return sorted(
        path
        for path in base.rglob("*")
        if path.is_file()
        and path.suffix in REFERENCE_SUFFIXES
        and path.relative_to(base).parts[0] not in REFERENCE_SKIP
    )


@dataclass(frozen=True)
class Memo:
    run_id: str
    text: str


@dataclass
class CaseInput:
    label: str
    description: str | None
    dossier_sha256: str
    scenario_sha256: str
    withheld: dict[str, set[str]]
    memos: dict[str, list[Memo]] = field(default_factory=dict)
    held: dict[str, int] = field(default_factory=dict)
    memo_sha256: dict[str, str] = field(default_factory=dict)


def _read_toml(path: Path, shown: str, expected: str) -> dict[str, Any]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise EchoRefusal(f"{shown} cannot be read ({type(exc).__name__})") from exc
    if _sha256(data) != expected:
        raise EchoRefusal(f"{shown} does not hash to case.lock: not the text the model was given")
    try:
        return tomllib.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise EchoRefusal(f"{shown} is not valid TOML") from exc


def _read_memos(path: Path, shown: str) -> tuple[list[Memo], int, str]:
    data = path.read_bytes()
    memos: list[Memo] = []
    held = 0
    for number, line in enumerate(data.decode("utf-8").splitlines(), start=1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EchoRefusal(f"{shown} line {number} is not JSON") from exc
        memo, run_id = row.get("memo"), row.get("run_id")
        if not isinstance(memo, str) or not isinstance(run_id, str):
            raise EchoRefusal(f"{shown} line {number} has no memo or run_id")
        if memo == HELD:
            held += 1
        else:
            memos.append(Memo(run_id, memo))
    return memos, held, _sha256(data)


def read_cases(root: Path, appendix: Path) -> list[CaseInput]:
    try:
        index = json.loads((root / CASES_FILE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EchoRefusal(f"{CASES_FILE.as_posix()} cannot be read") from exc
    cases: list[CaseInput] = []
    for case in index.get("cases", []):
        label = case.get("label")
        if not isinstance(label, str) or not _PLAIN.fullmatch(label):
            raise EchoRefusal(f"{CASES_FILE.as_posix()}: a case label that is not plain")
        lock_path = root / LOCKS / label / "case.lock"
        try:
            lock = tomllib.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise EchoRefusal(f"experiment/cases/{label}/case.lock cannot be read") from exc
        if lock.get("probe_set") != case.get("probe_set"):
            raise EchoRefusal(f"{label}: case.lock and cases.json disagree on the probe set")
        folder = CaseAppendix(appendix, label)
        withheld = _empty()
        for path, key, name in (
            (folder.dossier_path_for(int(lock["probe_set"])), "dossier_sha256", "dossier"),
            (folder.scenario_path, "scenario_sha256", "scenario"),
        ):
            parsed = _read_toml(path, f"{label}'s {name} in the appendix", str(lock[key]))
            for text in _strings(parsed):
                _merge(withheld, tokens(text))
        description = case.get("description") or {}
        published = description.get("status") == "published"
        item = CaseInput(
            label=label,
            description=str(description.get("text")) if published else None,
            dossier_sha256=str(lock["dossier_sha256"]),
            scenario_sha256=str(lock["scenario_sha256"]),
            withheld=withheld,
        )
        memo_files = sorted((root / RESULTS_CASES / label).glob(f"*{MEMOS_SUFFIX}"))
        if not memo_files:
            raise EchoRefusal(f"experiment/results/cases/{label} holds no memo file")
        for path in memo_files:
            model_key = path.name.removesuffix(MEMOS_SUFFIX)
            shown = f"experiment/results/cases/{label}/{path.name}"
            item.memos[model_key], item.held[model_key], item.memo_sha256[model_key] = _read_memos(
                path, shown
            )
        cases.append(item)
    if not cases:
        raise EchoRefusal(f"{CASES_FILE.as_posix()} lists no case")
    return cases


# --- the count ---------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class EchoResult:
    public: dict[str, Any]
    private: dict[str, dict[str, Any]]  # label -> the private report


def count_echoes(
    cases: Sequence[CaseInput], reference: Sequence[tuple[str, str]], head: str
) -> EchoResult:
    """``reference`` is (repo-relative path, text) for each reference file."""
    reference_tokens = _empty()
    for _path, text in reference:
        _merge(reference_tokens, tokens(text))
    memo_words = {
        case.label: set().union(
            *(tokens(m.text)["word"] for memos in case.memos.values() for m in memos)
        )
        for case in cases
    }
    rows: list[dict[str, Any]] = []
    case_rows: list[dict[str, Any]] = []
    private: dict[str, dict[str, Any]] = {}
    for case in cases:
        described = tokens(case.description) if case.description else _empty()
        others = set().union(*(memo_words[c.label] for c in cases if c.label != case.label))
        distinctive = {
            kind: case.withheld[kind] - reference_tokens[kind] - described[kind] for kind in KINDS
        }
        distinctive["word"] -= others
        report: dict[str, Any] = {
            "label": case.label,
            "method_version": METHOD_VERSION,
            "models": {},
        }
        for model_key in sorted(case.memos):
            hits: dict[str, dict[str, list[str]]] = {kind: {} for kind in KINDS}
            with_kind = dict.fromkeys(KINDS, 0)
            with_any = 0
            for memo in case.memos[model_key]:
                found = tokens(memo.text)
                matched = False
                for kind in KINDS:
                    shared = found[kind] & distinctive[kind]
                    if shared:
                        with_kind[kind] += 1
                        matched = True
                    for token in shared:
                        hits[kind].setdefault(token, []).append(memo.run_id)
                with_any += matched
            rows.append(
                {
                    "label": case.label,
                    "model_key": model_key,
                    "published": len(case.memos[model_key]),
                    "held": case.held[model_key],
                    "with_word": with_kind["word"],
                    "with_percent": with_kind["percent"],
                    "with_figure": with_kind["figure"],
                    "with_any": with_any,
                    "distinct_words": len(hits["word"]),
                    "distinct_percents": len(hits["percent"]),
                    "distinct_figures": len(hits["figure"]),
                    "memos_sha256": case.memo_sha256[model_key],
                }
            )
            report["models"][model_key] = {
                kind: [
                    {"token": token, "memos": len(runs), "run_ids": sorted(runs)}
                    for token, runs in sorted(
                        hits[kind].items(), key=lambda item: (-len(item[1]), item[0])
                    )
                ]
                for kind in KINDS
            }
        case_rows.append(
            {
                "label": case.label,
                "description_published": case.description is not None,
                "dossier_sha256": case.dossier_sha256,
                "scenario_sha256": case.scenario_sha256,
            }
        )
        private[case.label] = report
    reference_digest = _sha256(
        "".join(f"{path}\t{_sha256(text.encode('utf-8'))}\n" for path, text in reference).encode(
            "utf-8"
        )
    )
    public = {
        "schema": SCHEMA,
        "method_version": METHOD_VERSION,
        "rule": "Phase 6 IMPLEMENTATION doc §22, 2026-11-09",
        "head": head,
        "reference": {"files": len(reference), "sha256": reference_digest},
        "cases": case_rows,
        "counts": rows,
    }
    return EchoResult(public, private)


# --- writing -----------------------------------------------------------------------------------------------

_HEX = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
_PUBLIC_STRINGS = frozenset({SCHEMA, "Phase 6 IMPLEMENTATION doc §22, 2026-11-09"})


def check_public(public: Mapping[str, Any], cases: Sequence[CaseInput]) -> None:
    """Every string in the public file is a key, a label, a model key, the schema, the rule's name or a hash:
    never a token or a memo's text. Checked on the value written, not assumed from the code."""
    allowed = set(_PUBLIC_STRINGS) | {c.label for c in cases}
    allowed |= {m for c in cases for m in c.memos}

    def walk(value: Any, where: str) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                walk(item, f"{where}/{key}")
        elif isinstance(value, list):
            for i, item in enumerate(value):
                walk(item, f"{where}/{i}")
        elif isinstance(value, str) and value not in allowed and not _HEX.fullmatch(value):
            raise EchoRefusal(f"the public file would hold a string at {where} that is not allowed")

    walk(public, "")


def _text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def write_public(root: Path, public: Mapping[str, Any]) -> tuple[Path, bool]:
    """Written once. The same bytes again is a no-op; different bytes are refused (delete it on purpose)."""
    path = root / PUBLIC_PATH
    text = _text(public)
    if path.exists():
        if path.read_text(encoding="utf-8") == text:
            return path, False
        raise EchoRefusal(
            f"{PUBLIC_PATH.as_posix()} exists with other counts: delete it on purpose to count again"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path, True


def write_private(appendix: Path, private: Mapping[str, Mapping[str, Any]]) -> list[Path]:
    written = []
    for label, report in private.items():
        path = CaseAppendix(appendix, label).directory / PRIVATE_NAME
        path.write_text(_text(report), encoding="utf-8", newline="\n")
        written.append(path)
    return written


def run_echo_count(root: Path, appendix: Path, head: str) -> tuple[EchoResult, Path, bool]:
    cases = read_cases(root, appendix)
    reference = [
        (p.relative_to(root).as_posix(), p.read_text(encoding="utf-8"))
        for p in reference_files(root)
    ]
    if not reference:
        raise EchoRefusal("no reference text under experiment/")
    result = count_echoes(cases, reference, head)
    check_public(result.public, cases)
    write_private(appendix, result.private)
    path, wrote = write_public(root, result.public)
    return result, path, wrote
