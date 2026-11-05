"""Phase 4's raw-object manifest and ``hc site raw-manifest`` (Phase 1.5 IMPLEMENTATION doc, sections 12, 19).

Every key, run id and body is a fictional canary in the real key shapes. The bucket is a fake whose name ends
in a fake account id. Nothing here touches a network.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, cast

import pytest

from horizon_compact import cli
from horizon_compact.cli import CLEAN_EXIT, REFUSED_EXIT, main
from horizon_compact.site.rawmanifest import (
    RawManifestRefusal,
    S3RawReader,
    account_id,
    build_raw_manifest,
    repository_experiments,
    write_raw_manifest,
)

ACCOUNT = "111122223333"
BUCKET = f"horizon-compact-results-{ACCOUNT}"
EXPERIMENTS = frozenset({"company", "placeholder"})
MEMO = b"ZEBRA-MEMO-the-distinctive-words-a-model-wrote-about-its-reasons"
NOT_UTF8 = b"\xff\xfe\x00 not utf-8 \x80\x81"
MOMENT = datetime(2026, 10, 14, 7, 0, 0, tzinfo=timezone(timedelta(hours=-5)))  # 12:00:00Z

PILOT = "pilot/company/pilot-canary-a-0a1b2c3d/"
GRID = "official/company/grid-canary-b-1b2c3d4e/"
AWARE = "official/company/awareness/awareness-canary-c-2c3d4e5f/"


def _digit_body() -> bytes:
    """A body whose sha256 holds twelve decimal digits in a row, as about one digest in five does."""
    for n in range(500):
        body = f"canary-{n}".encode()
        if re.search(r"[0-9]{12}", hashlib.sha256(body).hexdigest()):
            return body
    raise AssertionError("no such body in 500 tries")  # pragma: no cover


DIGIT_BODY = _digit_body()

BODIES: dict[str, bytes] = {
    PILOT + "manifest.json": NOT_UTF8,
    PILOT + "runs/r-a00000000001/attempt-1.json": b'{"attempt": 1}\n',
    PILOT + "runs/r-a00000000001/attempt-2.json": MEMO,
    PILOT + "runs/r-a00000000001/final.json": b'{"final": 2}\n',
    "pilot/company/repeats.json": b'{"repeats": 3}\n',
    GRID + "manifest.json": b'{"grid": true}\n',
    GRID + "runs/r-100000000001/attempt-1.json": b"one\n",
    GRID + "runs/r-100000000001/final.json": b"two\n",
    GRID + "runs/r-b00000000002/attempt-1.json": b"three\n",
    GRID + "runs/r-b00000000002/final.json": b"four\n",
    GRID + "runs/r-b00000000003/attempt-1.json": DIGIT_BODY,
    GRID + "sessions/s-1.json": b"session\n",
    AWARE + "manifest.json": b'{"awareness": true}\n',
    AWARE + "runs/r-c00000000001.json": b"reply one\n",
    AWARE + "runs/r-c00000000002.json": b"reply two\n",
    AWARE + "errors/r-c00000000002-1.json": b"an api error, then the reply\n",
}


@dataclass
class Version:
    key: str
    body: bytes
    version_id: str = ""
    latest: bool = True
    size: int | None = None

    def __post_init__(self) -> None:
        if not self.version_id:
            self.version_id = "v" + hashlib.md5(self.key.encode()).hexdigest()[:10]


class FakeBody:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def iter_chunks(self, chunk_size: int = 1024) -> Iterator[bytes]:
        step = min(chunk_size, 3)  # several chunks, so the streaming is exercised
        for start in range(0, len(self._data), step):
            yield self._data[start : start + step]


class FakeS3:
    """Just enough of a boto3 S3 client for ``S3RawReader``: versioning, a paginated version listing with
    delete markers, and get_object by version. Every call is recorded."""

    def __init__(
        self,
        versions: list[Version],
        markers: tuple[str, ...] = (),
        status: str | None = "Enabled",
    ) -> None:
        self.versions, self.markers, self.status = versions, markers, status
        self.calls: list[str] = []
        self.bucket = BUCKET

    def get_bucket_versioning(self, *, Bucket: str) -> dict[str, Any]:
        assert Bucket == self.bucket
        self.calls.append("get_bucket_versioning")
        return {} if self.status is None else {"Status": self.status}

    def get_paginator(self, name: str) -> FakeS3:
        assert name == "list_object_versions"
        self.calls.append("get_paginator")
        return self

    def paginate(self, *, Bucket: str, Prefix: str) -> Iterator[dict[str, Any]]:
        assert Bucket == self.bucket
        found = sorted((v for v in self.versions if v.key.startswith(Prefix)), key=lambda v: v.key)
        marks = [
            {"Key": k, "VersionId": "dm-" + k[-6:], "IsLatest": True, "LastModified": MOMENT}
            for k in self.markers
            if k.startswith(Prefix)
        ]
        for start in range(0, max(len(found), 1), 4):  # several pages
            yield {
                "Versions": [
                    {
                        "Key": v.key,
                        "VersionId": v.version_id,
                        "IsLatest": v.latest,
                        "Size": len(v.body) if v.size is None else v.size,
                        "LastModified": MOMENT,
                        "ETag": '"never-copied"',
                    }
                    for v in found[start : start + 4]
                ],
                "DeleteMarkers": marks if start == 0 else [],
            }

    def get_object(self, *, Bucket: str, Key: str, VersionId: str) -> dict[str, Any]:
        assert Bucket == self.bucket
        self.calls.append("get_object")
        for v in self.versions:
            if v.key == Key and v.version_id == VersionId:
                return {"Body": FakeBody(v.body)}
        raise AssertionError(f"no such version {Key} {VersionId}")  # pragma: no cover


def fake(extra: tuple[Version, ...] = (), **kwargs: Any) -> FakeS3:
    return FakeS3([*(Version(k, b) for k, b in BODIES.items()), *extra], **kwargs)


def reader(client: FakeS3) -> S3RawReader:
    return S3RawReader(cast("Any", client), BUCKET)


def built(client: FakeS3 | None = None, **kwargs: Any) -> str:
    return build_raw_manifest(reader(client or fake()), EXPERIMENTS, BUCKET, **kwargs)


def objects_of(text: str) -> list[dict[str, Any]]:
    return cast("list[dict[str, Any]]", json.loads(text)["objects"])


# --- the file's bytes ------------------------------------------------------------------------------


def test_a_second_build_is_byte_identical() -> None:
    assert built() == built()
    assert built().endswith("}\n") and not built().endswith("\n\n")


def test_key_order_is_pinned_at_every_level() -> None:
    data = json.loads(built())
    assert list(data) == [
        "schema",
        "schema_version",
        "kind",
        "hash",
        "prefixes",
        "versioning",
        "object_count",
        "total_bytes",
        "groups",
        "objects",
    ]
    assert (data["schema"], data["schema_version"]) == ("horizon-compact/raw-manifest", 1)
    assert (data["kind"], data["hash"], data["versioning"]) == (
        "raw-object-manifest",
        "sha256",
        "Enabled",
    )
    assert data["prefixes"] == ["official/", "pilot/"]
    assert list(data["groups"][0]) == [
        "prefix",
        "objects",
        "bytes",
        "attempt_objects",
        "final_objects",
    ]
    assert list(data["objects"][0]) == ["key", "bytes", "sha256", "version_id", "last_modified"]


def test_each_object_is_one_line_and_the_whole_parses() -> None:
    text = built()
    lines = text.splitlines()
    start = lines.index('  "objects": [')
    body = lines[start + 1 : -2]
    assert lines[-2:] == ["  ]", "}"]
    assert len(body) == len(BODIES)
    for number, line in enumerate(body):
        assert line.startswith("    {") and line.rstrip(",").endswith("}")
        assert line.endswith(",") == (number < len(body) - 1)
        json.loads(line.rstrip(","))
    assert len(objects_of(text)) == len(BODIES)


def test_objects_are_sorted_by_key_and_hashed_over_bytes() -> None:
    entries = objects_of(built())
    assert [e["key"] for e in entries] == sorted(BODIES)
    by_key = {e["key"]: e for e in entries}
    for key, body in BODIES.items():
        assert by_key[key]["bytes"] == len(body)
        assert by_key[key]["sha256"] == hashlib.sha256(body).hexdigest()
    # A body that is not valid UTF-8 was hashed as it is: nothing is decoded.
    with pytest.raises(UnicodeDecodeError):
        NOT_UTF8.decode("utf-8")
    assert by_key[PILOT + "manifest.json"]["sha256"] == hashlib.sha256(NOT_UTF8).hexdigest()


def test_the_time_is_utc_with_a_z_and_the_version_id_is_the_listing_s() -> None:
    client = fake()
    entries = {e["key"]: e for e in objects_of(built(client))}
    first = entries["pilot/company/repeats.json"]
    assert first["last_modified"] == "2026-10-14T12:00:00Z"
    expected = next(v.version_id for v in client.versions if v.key == "pilot/company/repeats.json")
    assert first["version_id"] == expected


def test_the_totals_and_the_groups_by_hand() -> None:
    data = json.loads(built())
    assert data["object_count"] == 16
    assert data["total_bytes"] == sum(len(b) for b in BODIES.values())
    groups = {g["prefix"]: g for g in data["groups"]}
    assert list(groups) == [AWARE, GRID, "pilot/company/", PILOT]  # sorted by prefix
    assert groups[PILOT] == {
        "prefix": PILOT,
        "objects": 4,
        "bytes": sum(len(b) for k, b in BODIES.items() if k.startswith(PILOT)),
        "attempt_objects": 2,
        "final_objects": 1,
    }
    assert (groups[GRID]["objects"], groups[GRID]["attempt_objects"]) == (7, 3)
    assert groups[GRID]["final_objects"] == 2  # the session summary is counted in objects only
    # An awareness sweep lives one level deeper; its replies are the probe-call shape, and an API error kept
    # under errors/ is a call too, as the record checks count it.
    assert (groups[AWARE]["objects"], groups[AWARE]["attempt_objects"]) == (4, 3)
    assert groups[AWARE]["final_objects"] == 0
    # A key under no sweep goes in its experiment's group.
    assert groups["pilot/company/"]["objects"] == 1
    assert sum(g["objects"] for g in groups.values()) == data["object_count"]


def test_a_run_id_of_twelve_digits_and_a_digest_holding_twelve_digits_are_not_refused() -> None:
    text = built()
    assert "r-100000000001" in text
    assert re.search(r"[0-9]{12}", hashlib.sha256(DIGIT_BODY).hexdigest())
    assert hashlib.sha256(DIGIT_BODY).hexdigest() in text


def test_nothing_of_the_bodies_the_bucket_or_the_listing_s_extras_is_written() -> None:
    text = built()
    assert MEMO.decode() not in text
    assert BUCKET not in text and ACCOUNT not in text and "arn:" not in text
    assert "never-copied" not in text and "ETag" not in text


def test_the_reader_only_reads() -> None:
    client = fake()
    built(client)
    assert set(client.calls) == {"get_bucket_versioning", "get_paginator", "get_object"}
    assert client.calls.count("get_object") == len(BODIES)  # one GET per object
    assert not any(hasattr(S3RawReader, name) for name in ("put", "write", "delete", "copy"))


def test_progress_is_told_every_five_hundred_objects() -> None:
    many = [Version(f"pilot/company/loose-{i:04d}.json", b"x") for i in range(1001)]
    told: list[tuple[int, int]] = []
    built(
        FakeS3([*many, Version("official/company/only.json", b"y")]),
        progress=lambda a, b: told.append((a, b)),
    )
    assert told == [(500, 1002), (1000, 1002)]


# --- what it refuses -------------------------------------------------------------------------------


@pytest.mark.parametrize("status", ["Suspended", None])
def test_it_refuses_a_bucket_that_is_not_versioned(status: str | None) -> None:
    with pytest.raises(RawManifestRefusal, match="versioning is"):
        built(fake(status=status))


def test_it_refuses_an_empty_prefix() -> None:
    only_official = FakeS3([Version(k, b) for k, b in BODIES.items() if k.startswith("official/")])
    with pytest.raises(RawManifestRefusal, match="nothing is stored under pilot/"):
        built(only_official)


def test_it_refuses_a_delete_marker() -> None:
    with pytest.raises(RawManifestRefusal, match="delete marker"):
        built(fake(markers=("pilot/company/repeats.json",)))


def test_it_refuses_a_second_version_of_a_key() -> None:
    twin = Version("pilot/company/repeats.json", b"changed", version_id="vtwo", latest=False)
    with pytest.raises(RawManifestRefusal, match="more than one version"):
        built(fake((twin,)))


def test_it_refuses_a_version_that_is_not_the_latest() -> None:
    client = FakeS3([Version(k, b) for k, b in BODIES.items()])
    client.versions[0].latest = False
    with pytest.raises(RawManifestRefusal, match="not the latest"):
        built(client)


def test_it_refuses_a_key_under_an_experiment_the_repository_lacks() -> None:
    with pytest.raises(RawManifestRefusal, match="not one of this repository's"):
        built(fake((Version("official/elsewhere/x.json", b"z"),)))


@pytest.mark.parametrize(
    "key",
    [
        "pilot/company/a b.json",  # a space
        "pilot/company/café.json",  # outside ASCII
        "pilot/company/folder/",  # ends in a slash
        "pilot/company/../x.json",  # a dot segment
        "pilot/company//x.json",  # an empty segment
        "pilot/x.json",  # too shallow to name an experiment
    ],
)
def test_it_refuses_a_key_of_an_unexpected_shape(key: str) -> None:
    with pytest.raises(RawManifestRefusal, match="unexpected shape"):
        built(fake((Version(key, b"z"),)))


def test_it_refuses_a_read_whose_byte_count_differs_from_the_listing() -> None:
    with pytest.raises(RawManifestRefusal, match="the listing said 99"):
        built(fake((Version("pilot/company/short.json", b"abc", size=99),)))


def test_it_refuses_an_output_holding_the_account_id_the_bucket_name_or_an_arn() -> None:
    with pytest.raises(RawManifestRefusal, match="the account id"):
        built(fake((Version(f"pilot/company/x-{ACCOUNT}.json", b"z"),)))
    with pytest.raises(RawManifestRefusal, match="the bucket name"):
        built(fake((Version("pilot/company/y.json", b"z", version_id=BUCKET),)))
    with pytest.raises(RawManifestRefusal, match="an ARN"):
        built(fake((Version("pilot/company/y.json", b"z", version_id="arn:aws:s3:::x"),)))


def test_it_refuses_a_bucket_name_with_no_account_id() -> None:
    with pytest.raises(RawManifestRefusal, match="does not end in an account id"):
        build_raw_manifest(reader(fake()), EXPERIMENTS, "horizon-compact-results")
    assert account_id(BUCKET) == ACCOUNT


# --- the writer ------------------------------------------------------------------------------------


def test_the_writer_is_a_no_op_for_the_same_bytes_and_refuses_different_ones(
    tmp_path: Path,
) -> None:
    text = built()
    out = tmp_path / "evidence" / "raw-manifest.json"
    assert write_raw_manifest(text, out) == out
    assert out.read_bytes() == text.encode("utf-8")
    assert b"\r" not in out.read_bytes() and out.read_bytes().endswith(b"}\n")
    assert write_raw_manifest(text, out) == out  # the same bytes again
    with pytest.raises(RawManifestRefusal, match="already holds different data"):
        write_raw_manifest(text + " ", out)
    assert out.read_bytes() == text.encode("utf-8")
    assert not any(p.name.endswith(".tmp") for p in out.parent.iterdir())


def test_the_repository_s_experiment_folders_are_the_ones_with_both_files(tmp_path: Path) -> None:
    for name, files in (("a", ("dossier.toml", "objectives.toml")), ("b", ("dossier.toml",))):
        (tmp_path / "experiment" / name).mkdir(parents=True)
        for f in files:
            (tmp_path / "experiment" / name / f).write_text("", encoding="utf-8")
    assert repository_experiments(tmp_path) == frozenset({"a"})
    assert repository_experiments(tmp_path / "nowhere") == frozenset()


# --- the command -----------------------------------------------------------------------------------


@pytest.fixture
def aws(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> FakeS3:
    config = tmp_path / "aws-config"
    config.write_text("[profile test]\nregion = us-east-1\n", encoding="utf-8")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(config))
    monkeypatch.delenv("HC_RESULTS_BUCKET", raising=False)
    client = fake()
    monkeypatch.setattr(cli, "_raw_s3_client", lambda session: client)
    return client


def _argv(tmp_path: Path, *extra: str) -> list[str]:
    return ["site", "raw-manifest", "--out", str(tmp_path / "out" / "raw.json"), *extra]


def test_the_command_end_to_end(
    aws: FakeS3, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = _argv(tmp_path, "--profile", "test", "--bucket", BUCKET)
    assert main(argv) == CLEAN_EXIT
    out = tmp_path / "out" / "raw.json"
    assert capsys.readouterr().out.splitlines() == [
        f"wrote {out}",
        f"objects: {len(BODIES)}",
        f"bytes:   {sum(len(b) for b in BODIES.values())}",
        "groups:  4",
    ]
    assert out.read_text(encoding="utf-8") == built(aws)
    assert main(argv) == CLEAN_EXIT  # the same bytes again, a no-op
    out.write_text("{}\n", encoding="utf-8")  # different bytes: refused, and left alone
    assert main(argv) == REFUSED_EXIT
    assert "already holds different data" in capsys.readouterr().err
    assert out.read_text(encoding="utf-8") == "{}\n"


def test_the_bucket_can_come_from_the_environment(
    aws: FakeS3, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HC_RESULTS_BUCKET", BUCKET)
    assert main(_argv(tmp_path, "--profile", "test")) == CLEAN_EXIT


def test_the_command_refuses_and_writes_nothing_when_the_build_does(
    aws: FakeS3, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    aws.status = "Suspended"
    assert main(_argv(tmp_path, "--profile", "test", "--bucket", BUCKET)) == REFUSED_EXIT
    assert capsys.readouterr().err.startswith("refused: ")
    assert not (tmp_path / "out").exists()


def test_the_command_needs_a_profile_and_a_bucket(
    aws: FakeS3, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(_argv(tmp_path, "--bucket", BUCKET)) == REFUSED_EXIT
    assert "--profile is required" in capsys.readouterr().err
    assert main(_argv(tmp_path, "--profile", "test")) == REFUSED_EXIT
    assert "needs --bucket" in capsys.readouterr().err
    assert aws.calls == []  # nothing was read
