"""The grid memo extract: every official run's memo, read from the raw objects the public manifest names, into
the explorer's memo files (Phase 6 IMPLEMENTATION doc section 5.3 with its 2026-11-09 note, decision 4; the
decided points of ``scratch/p6-c2-build-prompt.md``).

**His to run, never Claude's.** It reads official records from S3, so ``hc site memos`` is on the deny list.
This module makes no call itself: the one thing it is handed is a reader with a ``read`` method (the S3 byte
reader of ``rawmanifest.py`` has one, and no write call). Run code under ``protocol/sets.py``'s rules.

**What it reads, and only that.** The three official sweeps the committed results files name (each grid, and
the thinking sub-study): the prefix is ``official/company/<sweep_id>/``, never a pilot prefix and never a case
prefix. The objects read are exactly the entries of ``docs/phases/evidence/phase-4/raw-manifest.json`` under
those prefixes, each **by its recorded version id and as bytes**, and each refused unless its sha256 and byte
count equal the manifest's. So every memo comes from the object the public manifest names, and a later write
to a key could not change what is extracted.

**The runs are the frozen analysis's.** The verified objects are served to ``read_runs`` through an in-memory
record source, so a run's scenario, objective, wording, repeat and final status are not re-derived here. The
memo is ``final_text`` of the run's final attempt (``final.json``'s ``final_attempt``), imported from
``caseprobe/memos.py``: **that function and this one must read the same field**, so a memo here is the text
the case scan and the reader would see. A run whose final attempt wrote no text has ``source`` and ``memo``
null. **No memo is edited, trimmed or summarized** (``planning/06`` section 6.1); the one change of
representation is that U+0085, U+2028 and U+2029 are written as JSON escapes, which parse back to the same
character and keep a line-splitting reader from breaking a line in the middle of a memo.

**It ties the extract to the frozen output** (each a refusal, so a reviewer can trust the files without S3):
per sweep, the runs equal the manifest group's ``final_objects``; per scenario, objective and wording, the
runs with a valid status equal that cell's ``valid`` in the committed results file; every run in
``descriptive.per_run`` is in the extract, valid, with the same objective, wording and repeat.

**What it refuses** (one exception class, the message says why and never holds a memo's text or a term):
a manifest entry, version, sha256 or size that does not agree; a cross-check failure; a memo holding a
name-guard term (the message names the run id, never the term); an output holding ``arn:`` or the results
bucket's name prefix. It does **not** scan for a bare run of twelve digits (``explorer.py`` says why: run
ids are ``r-`` and twelve hex digits, and some are all digits). The ``arn:`` test needs a character that is
not a letter or digit before it, because a memo may say "learn:" or "warn:".

**The writer** is C1's: build in a sibling folder and swap it in; refuse an ``out`` not named
``explorer-memos``, or an existing one holding anything outside this layout; the same bytes is a no-op.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections import Counter
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from horizon_compact.analysis.records import RecordRefusal, RunRow, read_runs
from horizon_compact.caseprobe.memos import final_text
from horizon_compact.privacy.names import TermFile, find_terms
from horizon_compact.site.explorer import ExplorerDataRefusal, _Grid, _read_prereg

EXPLORER_MEMOS_VERSION = 1
OUT_NAME = "explorer-memos"
OFFICIAL_PREFIX = "official/company/"
RAW_MANIFEST_RELATIVE = "docs/phases/evidence/phase-4/raw-manifest.json"
CHUNK_PROGRESS_EVERY = 500

# The large-file hook's limit is 1,024 KB (.pre-commit-config.yaml). A file this builder writes stays under
# this many bytes: a (kind, model, scenario, objective) file over it is split by wording, and a wording's file
# over it is refused. The limit in the hook is never raised.
MAX_FILE_BYTES = 1_000_000

_PLAIN = r"[a-z0-9][a-z0-9-]*"
_ID = r"[A-Za-z0-9]+"
_LAYOUT = (
    re.compile(r"index\.json"),
    re.compile(rf"(?:grid|thinking)/{_PLAIN}/s[0-9]+/{_ID}(?:-[a-z0-9]+)?\.jsonl"),
)
_HEX64 = re.compile(r"[0-9a-f]{64}")
_HEAD = re.compile(r"[0-9a-f]{40}")
_SCENARIO = re.compile(r"s[0-9]+")
_WORDING = re.compile(r"[a-z0-9]+")
# The objects read_runs needs; every other object under a prefix is verified and then dropped.
_NEEDED = re.compile(r"/(?:manifest\.json|runs/r-[0-9a-f]{12}/(?:final|attempt-[0-9]+)\.json)$")
# "arn:" only where an ARN could start: after a character that is not a letter or digit.
_ARN = re.compile(r"(?<![A-Za-z0-9])arn:")
_BUCKET_PREFIX = "horizon-compact-results-"
# Written as escapes so a reader that splits a file into lines on these characters cannot cut a line.
_LINE_SEPARATORS = str.maketrans(
    {
        "\N{NEXT LINE}": "\\u0085",
        "\N{LINE SEPARATOR}": "\\u2028",
        "\N{PARAGRAPH SEPARATOR}": "\\u2029",
    }
)


class MemoExtractRefusal(Exception):
    """The extract or its writer will not produce this output. The message says why."""


class ByteReader(Protocol):
    """What the extract may do: read one version of one key, as bytes. No list, put or delete is here."""

    def read(self, key: str, version_id: str) -> Iterator[bytes]: ...


@dataclass(frozen=True)
class RawEntry:
    key: str
    size: int
    sha256: str
    version_id: str


@dataclass(frozen=True)
class RawManifest:
    sha256: str
    entries: dict[str, RawEntry]
    final_objects: dict[str, int]  # group prefix -> the group's count of final.json objects


# --- the official sweeps -----------------------------------------------------------------------------------


def official_sweeps(results_root: Path) -> list[_Grid]:
    """The sweeps the committed results files name: each grid in model-key order, then the thinking file. The
    file rules (which files are read, the version, the model key and sweep id) are C1's own."""
    try:
        grids, thinking = _read_prereg(results_root)
    except ExplorerDataRefusal as exc:
        raise MemoExtractRefusal(str(exc)) from exc
    sweeps = [*grids, thinking]
    for sweep in sweeps:
        if not re.fullmatch(_PLAIN, sweep.sweep_id) or not re.fullmatch(_PLAIN, sweep.model_key):
            raise MemoExtractRefusal(f"{sweep.shown} has an id that is not plain")
    return sweeps


def prefix_of(sweep: _Grid) -> str:
    return f"{OFFICIAL_PREFIX}{sweep.sweep_id}/"


# --- the raw-object manifest ------------------------------------------------------------------------------


def load_raw_manifest(path: Path) -> RawManifest:
    """The committed manifest, its sha256 and its entries by key, or a refusal."""
    try:
        data = path.read_bytes()
        loaded = json.loads(data.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MemoExtractRefusal(f"{path.name} cannot be read as JSON: {exc}") from exc
    if not isinstance(loaded, dict):
        raise MemoExtractRefusal(f"{path.name} is not a JSON object")
    entries: dict[str, RawEntry] = {}
    objects = loaded.get("objects")
    if not isinstance(objects, list) or not objects:
        raise MemoExtractRefusal(f"{path.name} lists no objects")
    for item in objects:
        key = item.get("key") if isinstance(item, dict) else None
        size = item.get("bytes") if isinstance(item, dict) else None
        sha = item.get("sha256") if isinstance(item, dict) else None
        version = item.get("version_id") if isinstance(item, dict) else None
        if (
            not isinstance(key, str)
            or not isinstance(size, int)
            or isinstance(size, bool)
            or not isinstance(sha, str)
            or not _HEX64.fullmatch(sha)
            or not isinstance(version, str)
            or not version
        ):
            raise MemoExtractRefusal(
                f"{path.name} has an entry without a key, size, sha256 or version"
            )
        if key in entries:
            raise MemoExtractRefusal(f"{path.name} lists {key} twice")
        entries[key] = RawEntry(key, size, sha, version)
    finals: dict[str, int] = {}
    groups = loaded.get("groups")
    if not isinstance(groups, list):
        raise MemoExtractRefusal(f"{path.name} has no groups")
    for group in groups:
        prefix = group.get("prefix") if isinstance(group, dict) else None
        count = group.get("final_objects") if isinstance(group, dict) else None
        if not isinstance(prefix, str) or not isinstance(count, int) or isinstance(count, bool):
            raise MemoExtractRefusal(f"{path.name} has a group without a prefix or final_objects")
        finals[prefix] = count
    return RawManifest(hashlib.sha256(data).hexdigest(), entries, finals)


# --- reading and verifying --------------------------------------------------------------------------------


class VerifiedSource:
    """The verified objects of one sweep, as the frozen reader's ``RecordSource`` (``get``, ``list_keys``)."""

    def __init__(self, objects: Mapping[str, bytes]) -> None:
        self._objects = dict(objects)

    def get(self, key: str) -> str | None:
        data = self._objects.get(key)
        if data is None:
            return None
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise MemoExtractRefusal(f"{key} is not valid UTF-8") from exc

    def list_keys(self, prefix: str) -> list[str]:
        return sorted(key for key in self._objects if key.startswith(prefix))


def _read_verified(reader: ByteReader, entry: RawEntry) -> bytes:
    """One version of one key, by the version id the manifest records, refused unless it is the manifest's
    bytes."""
    digest = hashlib.sha256()
    chunks: list[bytes] = []
    for chunk in reader.read(entry.key, entry.version_id):
        digest.update(chunk)
        chunks.append(chunk)
    data = b"".join(chunks)
    if len(data) != entry.size:
        raise MemoExtractRefusal(
            f"{entry.key}: read {len(data)} bytes, the manifest says {entry.size}"
        )
    if digest.hexdigest() != entry.sha256:
        raise MemoExtractRefusal(f"{entry.key}: the sha256 of what was read is not the manifest's")
    return data


def _fetch_sweep(
    reader: ByteReader,
    manifest: RawManifest,
    prefix: str,
    progress: Callable[[int], None] | None,
    counted: list[int],
) -> dict[str, bytes]:
    """Every manifest entry under ``prefix``, verified; the ones read_runs needs are kept."""
    entries = sorted(
        (e for key, e in manifest.entries.items() if key.startswith(prefix)), key=lambda e: e.key
    )
    if not entries:
        raise MemoExtractRefusal(f"the manifest has no object under {prefix}")
    kept: dict[str, bytes] = {}
    for entry in entries:
        data = _read_verified(reader, entry)
        if _NEEDED.search(entry.key):
            kept[entry.key] = data
        counted[0] += 1
        if progress is not None and counted[0] % CHUNK_PROGRESS_EVERY == 0:
            progress(counted[0])
    return kept


# --- the runs ---------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class MemoRun:
    row: RunRow
    source: str | None
    memo: str | None
    final_key: str
    final_sha256: str
    attempt_key: str
    attempt_sha256: str


def _json_object(source: VerifiedSource, key: str) -> dict[str, Any]:
    text = source.get(key)
    if text is None:
        raise MemoExtractRefusal(f"{key} was not read")
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MemoExtractRefusal(f"{key} is not valid JSON") from exc
    if not isinstance(loaded, dict):
        raise MemoExtractRefusal(f"{key} is not a JSON object")
    return loaded


def _runs_of(
    source: VerifiedSource, manifest: RawManifest, prefix: str, shown: str
) -> list[MemoRun]:
    try:
        run_set = read_runs(source, prefix)
    except (RecordRefusal, KeyError, ValueError, TypeError) as exc:
        raise MemoExtractRefusal(
            f"the frozen reader refused the records of {shown}: {type(exc).__name__}: {exc}"
        ) from exc
    if run_set.unfinished:
        raise MemoExtractRefusal(
            f"{shown}: {len(run_set.unfinished)} planned runs have no final.json"
        )
    runs: list[MemoRun] = []
    for row in run_set.rows:
        base = f"{prefix}runs/{row.run_id}/"
        final_key = f"{base}final.json"
        number = _json_object(source, final_key).get("final_attempt")
        if not isinstance(number, int) or isinstance(number, bool):
            raise MemoExtractRefusal(f"{final_key} names no final attempt")
        attempt_key = f"{base}attempt-{number}.json"
        attempt = _json_object(source, attempt_key)
        found, memo = final_text(attempt)
        runs.append(
            MemoRun(
                row=row,
                source=found,
                memo=memo,
                final_key=final_key,
                final_sha256=manifest.entries[final_key].sha256,
                attempt_key=attempt_key,
                attempt_sha256=manifest.entries[attempt_key].sha256,
            )
        )
    return runs


# --- the cross-checks against the committed results file ----------------------------------------------------


def _cross_check(sweep: _Grid, runs: list[MemoRun], final_objects: int) -> None:
    shown = sweep.shown
    if len(runs) != final_objects:
        raise MemoExtractRefusal(
            f"{shown}: {len(runs)} runs read, and the manifest's group holds {final_objects} final.json "
            "objects"
        )
    actual: Counter[tuple[str, str, str]] = Counter()
    by_id: dict[str, RunRow] = {}
    for run in runs:
        by_id[run.row.run_id] = run.row
        if run.row.valid:
            actual[(run.row.scenario_id, run.row.objective_id, run.row.wording_id)] += 1
    expected: Counter[tuple[str, str, str]] = Counter()
    for scenario in sweep.scenarios:
        sid = scenario.get("scenario_id")
        for cell in scenario.get("cells") or []:
            if not isinstance(cell, dict) or cell.get("scenario_id") != sid:
                raise MemoExtractRefusal(f"{shown}: a cell of scenario {sid!r} that is not its own")
            valid = cell.get("valid")
            if not isinstance(valid, int) or isinstance(valid, bool):
                raise MemoExtractRefusal(
                    f"{shown}: a cell of scenario {sid!r} without a valid count"
                )
            expected[(str(sid), str(cell.get("objective_id")), str(cell.get("wording_id")))] += (
                valid
            )
    for cell_key in sorted(set(expected) | set(actual)):
        if expected[cell_key] != actual[cell_key]:
            raise MemoExtractRefusal(
                f"{shown}: scenario {cell_key[0]}, objective {cell_key[1]}, wording {cell_key[2]} has "
                f"{actual[cell_key]} valid runs in the records and {expected[cell_key]} in the results file"
            )
    for scenario in sweep.scenarios:
        descriptive = scenario.get("descriptive")
        per_run = descriptive.get("per_run") if isinstance(descriptive, dict) else None
        for item in per_run or []:
            run_id = item.get("run_id") if isinstance(item, dict) else None
            row = by_id.get(str(run_id))
            if row is None or not row.valid:
                raise MemoExtractRefusal(
                    f"{shown}: {run_id} is in the results file's per-run list, and is not a valid run "
                    "in the extract"
                )
            if (
                item.get("objective_id") != row.objective_id
                or item.get("wording_id") != row.wording_id
                or item.get("repeat") != row.repeat
                or scenario.get("scenario_id") != row.scenario_id
            ):
                raise MemoExtractRefusal(
                    f"{shown}: {run_id} has a different scenario, objective, wording or repeat in the "
                    "results file"
                )


# --- the files --------------------------------------------------------------------------------------------


def _dump(value: Any, shown: str) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    except ValueError as exc:
        raise MemoExtractRefusal(f"{shown} holds a value JSON cannot carry: {exc}") from exc
    return text.translate(_LINE_SEPARATORS) + "\n"


def _line(run: MemoRun) -> dict[str, Any]:
    row = run.row
    return {
        "run_id": row.run_id,
        "wording_id": row.wording_id,
        "repeat": row.repeat,
        "status": row.status,
        "source": run.source,
        "memo": run.memo,
        "final": {"key": run.final_key, "sha256": run.final_sha256},
        "attempt": {"key": run.attempt_key, "sha256": run.attempt_sha256},
    }


def _check_ids(sweep: _Grid, run: MemoRun) -> None:
    row = run.row
    if not _SCENARIO.fullmatch(row.scenario_id) or not re.fullmatch(_ID, row.objective_id):
        raise MemoExtractRefusal(
            f"{sweep.shown}: {row.run_id} has a scenario or objective id that is not plain"
        )
    if not _WORDING.fullmatch(row.wording_id):
        raise MemoExtractRefusal(f"{sweep.shown}: {row.run_id} has a wording id that is not plain")


def _memo_files(sweep: _Grid, runs: list[MemoRun]) -> dict[str, str]:
    """One file per scenario and objective; one per wording too when a file would pass ``MAX_FILE_BYTES``."""
    cells: dict[tuple[str, str], list[MemoRun]] = {}
    for run in runs:
        _check_ids(sweep, run)
        cells.setdefault((run.row.scenario_id, run.row.objective_id), []).append(run)
    files: dict[str, str] = {}
    for (scenario_id, objective_id), members in sorted(cells.items()):
        ordered = sorted(members, key=lambda r: (r.row.wording_id, r.row.repeat, r.row.run_id))
        folder = f"{sweep.kind}/{sweep.model_key}/{scenario_id}"
        path = f"{folder}/{objective_id}.jsonl"
        text = "".join(_dump(_line(r), path) for r in ordered)
        if len(text.encode("utf-8")) <= MAX_FILE_BYTES:
            files[path] = text
            continue
        for wording in sorted({r.row.wording_id for r in ordered}):
            split_path = f"{folder}/{objective_id}-{wording}.jsonl"
            part = "".join(
                _dump(_line(r), split_path) for r in ordered if r.row.wording_id == wording
            )
            if len(part.encode("utf-8")) > MAX_FILE_BYTES:
                raise MemoExtractRefusal(
                    f"{split_path} would be {len(part.encode('utf-8'))} bytes, over the "
                    f"{MAX_FILE_BYTES}-byte limit even split by wording"
                )
            files[split_path] = part
    return files


def _scan_names(runs: list[MemoRun], term_file: TermFile) -> list[str]:
    """The ids of the runs whose memo holds a name-guard term. Never the term.

    This scan is the one that counts for these files, not the commit guard's. The guard reads the file as
    written, where a line break in a memo is backslash and ``n``: a term just after a break has a letter
    before it, and a phrase split by a break is not split by whitespace, so the guard misses both. The
    decoded memo has neither problem (review, Phase 6 IMPLEMENTATION doc section 23a)."""
    return [
        run.row.run_id for run in runs if run.memo is not None and find_terms(run.memo, term_file)
    ]


# --- the build --------------------------------------------------------------------------------------------


def build_memo_extract(
    reader: ByteReader,
    results_root: Path,
    manifest_path: Path,
    term_file: TermFile,
    head: str,
    progress: Callable[[int], None] | None = None,
) -> dict[str, str]:
    """Published relative path to the file's exact text, each ending in one newline. ``head`` is the commit
    whose code ran. Reads (through ``reader``) every manifest object under the three official prefixes."""
    if not _HEAD.fullmatch(head):
        raise MemoExtractRefusal("head is not a 40-character commit id")
    sweeps = official_sweeps(results_root)
    manifest = load_raw_manifest(manifest_path)
    prefixes = [prefix_of(s) for s in sweeps]
    if len(set(prefixes)) != len(prefixes):
        raise MemoExtractRefusal("two results files name the same sweep")
    for prefix in prefixes:
        if prefix not in manifest.final_objects:
            raise MemoExtractRefusal(f"the manifest has no group for {prefix}")

    counted = [0]
    files: dict[str, str] = {}
    summaries: list[dict[str, Any]] = []
    flagged: list[tuple[str, str]] = []
    for sweep, prefix in zip(sweeps, prefixes, strict=True):
        source = VerifiedSource(_fetch_sweep(reader, manifest, prefix, progress, counted))
        runs = _runs_of(source, manifest, prefix, sweep.shown)
        _cross_check(sweep, runs, manifest.final_objects[prefix])
        flagged.extend((sweep.sweep_id, run_id) for run_id in _scan_names(runs, term_file))
        for path, text in _memo_files(sweep, runs).items():
            if path in files:
                raise MemoExtractRefusal(f"{path} would be written twice")
            files[path] = text
        summaries.append(
            {
                "kind": sweep.kind,
                "model_key": sweep.model_key,
                "sweep_id": sweep.sweep_id,
                "prefix": prefix,
                "runs": len(runs),
                "with_text": sum(1 for r in runs if r.memo is not None),
                "by_status": dict(sorted(Counter(r.row.status for r in runs).items())),
            }
        )
    if flagged:
        shown = ", ".join(f"{run_id} ({sweep_id})" for sweep_id, run_id in flagged[:10])
        more = f" and {len(flagged) - 10} more" if len(flagged) > 10 else ""
        raise MemoExtractRefusal(
            f"{len(flagged)} memos hold a term of the name guard's term file: {shown}{more}. The term is "
            "not printed; nothing was written"
        )

    files = dict(sorted(files.items()))
    index = {
        "explorer_memos_version": EXPLORER_MEMOS_VERSION,
        "head": head,
        "raw_manifest": {"path": RAW_MANIFEST_RELATIVE, "sha256": manifest.sha256},
        "sweeps": summaries,
        "files": list(files),
    }
    out = {"index.json": _dump(index, "index.json"), **files}
    for path, text in out.items():
        if _ARN.search(text) or _BUCKET_PREFIX in text:
            raise MemoExtractRefusal(
                f"{path} looks like it holds an ARN or the results bucket's name; it was not produced"
            )
    return out


# --- the writer -------------------------------------------------------------------------------------------


def _in_layout(relative: str) -> bool:
    return any(p.fullmatch(relative) for p in _LAYOUT)


def _existing(out: Path) -> dict[str, bytes]:
    """What an existing output directory holds, or a refusal if it holds anything else."""
    if out.is_symlink() or not out.is_dir():
        raise MemoExtractRefusal(f"{out} exists and is not a directory")
    found: dict[str, bytes] = {}
    for path in sorted(out.rglob("*")):
        relative = path.relative_to(out).as_posix()
        if path.is_symlink():
            raise MemoExtractRefusal(f"{out} holds a symbolic link ({relative}); not replacing it")
        if path.is_dir():
            continue
        if not _in_layout(relative):
            raise MemoExtractRefusal(
                f"{out} holds {relative}, which is not a file this command writes; not replacing the "
                "directory"
            )
        found[relative] = path.read_bytes()
    return found


def memo_extract_matches(files: Mapping[str, str], out: Path) -> bool:
    """True when ``out`` already holds exactly these files, byte for byte."""
    if not out.exists():
        return False
    return _existing(out) == {k: v.encode("utf-8") for k, v in files.items()}


def write_memo_extract(files: Mapping[str, str], out: Path) -> Path:
    """Replace ``out`` whole: built in a sibling directory, then swapped in, so a stale file cannot linger.
    The same bytes again is a no-op. Returns ``out``; committing is the author's."""
    if out.name != OUT_NAME:
        raise MemoExtractRefusal(f"the output directory must be named {OUT_NAME}, not {out.name!r}")
    for relative, text in files.items():
        if not _in_layout(relative):
            raise MemoExtractRefusal(f"{relative} is not in the expected layout")
        if not text.endswith("\n"):
            raise MemoExtractRefusal(f"{relative} does not end in a newline")
    if out.exists() and _existing(out) == {k: v.encode("utf-8") for k, v in files.items()}:
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    fresh = out.with_name(f".{OUT_NAME}.new")
    old = out.with_name(f".{OUT_NAME}.old")
    for leftover in (fresh, old):
        if leftover.exists() or leftover.is_symlink():
            raise MemoExtractRefusal(
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
