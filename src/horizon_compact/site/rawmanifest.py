"""Phase 4's manifest of raw objects (Phase 1.5 IMPLEMENTATION doc section 12 step 3, decision 8 (a)).

Phase 4's runs-half decision 2 (a), his: at the phase's close, commit a manifest of every pilot and official
object (key, bytes, sha256). It was not done then; this is it. The manifest timestamps the raw record in
public, and it says something the bucket alone does not: that every object is the only version of its key, so
the record was write-once in fact and not only by policy.

Run code under ``protocol/sets.py``'s rules. Standard library only: the S3 reader is handed in, and the one
concrete reader takes a boto3 client it does not create. The reader has **no write call**, so the builder
cannot change the bucket by construction. It reads **bytes**: the sha256 is taken over the stored bytes, chunk
by chunk, and nothing is decoded (``Store.get`` decodes to text, which is why it is not used here).

**What it refuses** (each is a finding for him, never something to code around): a bucket whose versioning is
not ``Enabled``; an empty prefix; a delete marker, a second version of a key, or a version that is not the
latest; a key outside the listed experiments, with a character outside ``[A-Za-z0-9._/-]``, ending in ``/``,
or with an empty or dot segment; a read whose byte count differs from the listing's ``Size``; and an output
that holds ``arn:``, the bucket name or the account id taken from it. It does **not** scan for a bare run of
twelve digits, as ``site/data.py`` does: this file holds thousands of run ids and sha256 values, a few of
which hold twelve decimal digits in a row by chance, and that pattern would refuse almost every real build.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from horizon_compact.experiment import EXPERIMENT_FILES
from horizon_compact.protocol.recordcheck import SWEEP_MANIFEST

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

SCHEMA = "horizon-compact/raw-manifest"
SCHEMA_VERSION = 1
KIND = "raw-object-manifest"
HASH = "sha256"
PREFIXES: tuple[str, ...] = ("official/", "pilot/")
VERSIONING_ENABLED = "Enabled"
CHUNK_BYTES = 1 << 20
PROGRESS_EVERY = 500

_KEY_CHARACTERS = re.compile(r"^[A-Za-z0-9._/-]+$")
# The record-check module keeps these three private; the shapes are copied here (a drift would show in the
# attempt counts, which the review checks against the Phase 4 record checks). A call is what ``_read_sweep``
# counts as one: an attempt, an awareness reply, or an awareness API error kept under ``errors/``.
_FINAL = re.compile(r"/runs/r-[0-9a-f]{12}/final\.json$")
_ATTEMPT = re.compile(r"/runs/r-[0-9a-f]{12}/attempt-\d+\.json$")
_PROBE_CALL = re.compile(r"/runs/r-[0-9a-f]{12}\.json$")


class RawManifestRefusal(Exception):
    """The manifest cannot be built, or written, without asserting something that is not true."""


@dataclass(frozen=True)
class ObjectVersion:
    """One entry of a bucket's version listing. A delete marker has no size."""

    key: str
    version_id: str
    size: int
    last_modified: datetime
    is_latest: bool
    is_delete_marker: bool = False


class RawReader(Protocol):
    """What the builder may do: read. There is no put, copy or delete here."""

    def versioning(self) -> str: ...

    def list_versions(self, prefix: str) -> list[ObjectVersion]: ...

    def read(self, key: str, version_id: str) -> Iterator[bytes]: ...


class S3RawReader:
    def __init__(self, client: S3Client, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    def versioning(self) -> str:
        reply = self._client.get_bucket_versioning(Bucket=self._bucket)
        return str(reply.get("Status", "Unversioned"))

    def list_versions(self, prefix: str) -> list[ObjectVersion]:
        found: list[ObjectVersion] = []
        for page in self._client.get_paginator("list_object_versions").paginate(
            Bucket=self._bucket, Prefix=prefix
        ):
            for entry in page.get("Versions", []):
                found.append(
                    ObjectVersion(
                        key=entry["Key"],
                        version_id=entry["VersionId"],
                        size=entry["Size"],
                        last_modified=entry["LastModified"],
                        is_latest=entry["IsLatest"],
                    )
                )
            for marker in page.get("DeleteMarkers", []):
                found.append(
                    ObjectVersion(
                        key=marker["Key"],
                        version_id=marker["VersionId"],
                        size=0,
                        last_modified=marker["LastModified"],
                        is_latest=marker["IsLatest"],
                        is_delete_marker=True,
                    )
                )
        return found

    def read(self, key: str, version_id: str) -> Iterator[bytes]:
        reply = self._client.get_object(Bucket=self._bucket, Key=key, VersionId=version_id)
        yield from reply["Body"].iter_chunks(chunk_size=CHUNK_BYTES)


def repository_experiments(root: Path) -> frozenset[str]:
    """The repository's own experiment folders (a folder holding both experiment files). A local copy of the
    freeze check's helper, which is private to its module."""
    base = root / "experiment"
    if not base.is_dir():
        return frozenset()
    return frozenset(
        p.name for p in base.iterdir() if all((p / f).is_file() for f in EXPERIMENT_FILES)
    )


def account_id(bucket: str) -> str:
    """The account id a bucket name ends with (``<project>-results-<account>``). A bucket without one leaves
    the leak check nothing to look for, so no manifest is built."""
    tail = bucket.rsplit("-", 1)[-1]
    if not tail.isdigit():
        raise RawManifestRefusal(
            "the bucket name does not end in an account id, so the output cannot be checked for one"
        )
    return tail


def _check_key(key: str, experiments: frozenset[str]) -> str:
    """The role and experiment of a key, or a refusal."""
    if not _KEY_CHARACTERS.match(key) or key.endswith("/"):
        raise RawManifestRefusal(f"a key with an unexpected shape: {key!r}")
    parts = key.split("/")
    if len(parts) < 3 or any(part in ("", ".", "..") for part in parts):
        raise RawManifestRefusal(f"a key with an unexpected shape: {key!r}")
    if parts[1] not in experiments:
        raise RawManifestRefusal(
            f"{key} is under an experiment that is not one of this repository's ({parts[1]})"
        )
    return f"{parts[0]}/{parts[1]}/"


def _listing(reader: RawReader, experiments: frozenset[str]) -> list[ObjectVersion]:
    found: list[ObjectVersion] = []
    for prefix in PREFIXES:
        versions = reader.list_versions(prefix)
        if not versions:
            raise RawManifestRefusal(f"nothing is stored under {prefix}")
        found.extend(versions)
    seen: set[str] = set()
    for version in found:
        if version.is_delete_marker:
            raise RawManifestRefusal(f"a delete marker on {version.key}")
        if version.key in seen:
            raise RawManifestRefusal(f"more than one version of {version.key}")
        seen.add(version.key)
        if not version.is_latest:
            raise RawManifestRefusal(f"{version.key} has a version that is not the latest")
        _check_key(version.key, experiments)
    return sorted(found, key=lambda v: v.key)


def _hash(reader: RawReader, version: ObjectVersion) -> str:
    digest = hashlib.sha256()
    size = 0
    for chunk in reader.read(version.key, version.version_id):
        digest.update(chunk)
        size += len(chunk)
    if size != version.size:
        raise RawManifestRefusal(
            f"{version.key}: read {size} bytes, the listing said {version.size}"
        )
    return digest.hexdigest()


def _moment(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _groups(entries: Iterable[dict[str, Any]], experiments: frozenset[str]) -> list[dict[str, Any]]:
    """One group per sweep (the directory of its ``manifest.json``, the longest one above a key), and one per
    ``<role>/<experiment>/`` for a key under no sweep."""
    keys = [entry["key"] for entry in entries]
    sweeps = sorted(
        key[: -len("manifest.json")] for key in keys if SWEEP_MANIFEST.match(key) is not None
    )
    groups: dict[str, dict[str, Any]] = {}
    for entry in entries:
        key = entry["key"]
        above = [prefix for prefix in sweeps if key.startswith(prefix)]
        prefix = max(above, key=len) if above else _check_key(key, experiments)
        group = groups.setdefault(
            prefix,
            {"prefix": prefix, "objects": 0, "bytes": 0, "attempt_objects": 0, "final_objects": 0},
        )
        group["objects"] += 1
        group["bytes"] += entry["bytes"]
        if _ATTEMPT.search(key) or _PROBE_CALL.search(key) or "/errors/" in key:
            group["attempt_objects"] += 1
        if _FINAL.search(key):
            group["final_objects"] += 1
    return [groups[prefix] for prefix in sorted(groups)]


def _text(head: dict[str, Any], entries: list[dict[str, Any]]) -> str:
    """The header and groups indented; each object on one line, so several thousand stay small and diff by
    line."""
    body = json.dumps(head, indent=2, ensure_ascii=False, allow_nan=False)
    lines = ",\n".join(f"    {json.dumps(entry, ensure_ascii=False)}" for entry in entries)
    return f'{body[:-2]},\n  "objects": [\n{lines}\n  ]\n}}\n'


def build_raw_manifest(
    reader: RawReader,
    experiments: frozenset[str],
    bucket: str,
    progress: Callable[[int, int], None] | None = None,
) -> str:
    """The manifest's exact text, ending in one newline. ``bucket`` is used for the leak check only and is
    never written. ``progress`` is told (objects read, objects in all) every 500 objects."""
    account = account_id(bucket)
    status = reader.versioning()
    if status != VERSIONING_ENABLED:
        raise RawManifestRefusal(
            f"the bucket's versioning is {status}, so write-once cannot be shown from its versions"
        )
    versions = _listing(reader, experiments)
    entries: list[dict[str, Any]] = []
    for number, version in enumerate(versions, start=1):
        entries.append(
            {
                "key": version.key,
                "bytes": version.size,
                "sha256": _hash(reader, version),
                "version_id": version.version_id,
                "last_modified": _moment(version.last_modified),
            }
        )
        if progress is not None and number % PROGRESS_EVERY == 0:
            progress(number, len(versions))
    groups = _groups(entries, experiments)
    head: dict[str, Any] = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "kind": KIND,
        "hash": HASH,
        "prefixes": list(PREFIXES),
        "versioning": status,
        "object_count": len(entries),
        "total_bytes": sum(entry["bytes"] for entry in entries),
        "groups": groups,
    }
    text = _text(head, entries)
    for needle, what in (
        ("arn:", "an ARN"),
        (bucket, "the bucket name"),
        (account, "the account id"),
    ):
        if needle in text:
            raise RawManifestRefusal(f"the output would hold {what}")
    return text


def write_raw_manifest(text: str, path: Path) -> Path:
    """Write the file once. The same bytes again is a no-op; different bytes are refused, never overwritten
    (replacing the file means deleting it on purpose first)."""
    data = text.encode("utf-8")
    if path.exists():
        if path.read_bytes() == data:
            return path
        raise RawManifestRefusal(
            f"{path} already holds different data; delete it on purpose to replace it"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)
    return path
