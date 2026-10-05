"""Stores: exclusive writes, and the conditional-write header on every S3 put (Phase 1 IMPLEMENTATION doc
section 7)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import boto3
import pytest
from botocore.stub import Stubber

from horizon_compact.sweep.store import LocalStore, S3Store

BUCKET = "horizon-compact-results-test"


def test_local_store_creates_once_and_never_overwrites(tmp_path: Path) -> None:
    store = LocalStore(tmp_path)
    assert store.put_new("development/s/manifest.json", "one") is True
    assert store.put_new("development/s/manifest.json", "two") is False
    assert store.get("development/s/manifest.json") == "one"
    assert store.get("development/s/missing.json") is None


def test_local_store_lists_keys_under_a_prefix(tmp_path: Path) -> None:
    store = LocalStore(tmp_path)
    for key in ("development/a/x.json", "development/a/runs/r/y.json", "development/b/z.json"):
        store.put_new(key, "{}")
    assert store.list_keys("development/a/") == [
        "development/a/runs/r/y.json",
        "development/a/x.json",
    ]
    assert store.list_keys("development/none/") == []


def _s3() -> tuple[S3Store, Stubber]:
    client = boto3.client("s3", region_name="us-east-1")
    stubber = Stubber(client)
    stubber.activate()
    return S3Store(cast("Any", client), BUCKET), stubber


def test_every_s3_put_sends_if_none_match_star() -> None:
    store, stubber = _s3()
    body = b'{"a": 1}'
    stubber.add_response(
        "put_object",
        {},
        {
            "Bucket": BUCKET,
            "Key": "development/s/x.json",
            "Body": body,
            "ContentType": "application/json",
            "IfNoneMatch": "*",
        },
    )
    assert store.put_new("development/s/x.json", '{"a": 1}') is True
    stubber.assert_no_pending_responses()


@pytest.mark.parametrize("code", ["PreconditionFailed", "ConditionalRequestConflict"])
def test_a_412_or_409_means_the_key_exists_never_an_overwrite(code: str) -> None:
    store, stubber = _s3()
    stubber.add_client_error("put_object", service_error_code=code, http_status_code=412)
    assert store.put_new("development/s/x.json", "{}") is False


def test_any_other_s3_error_is_raised_not_swallowed() -> None:
    from botocore.exceptions import ClientError

    store, stubber = _s3()
    stubber.add_client_error("put_object", service_error_code="AccessDenied", http_status_code=403)
    with pytest.raises(ClientError):
        store.put_new("development/s/x.json", "{}")


def test_s3_get_returns_none_for_a_missing_key() -> None:
    store, stubber = _s3()
    stubber.add_client_error("get_object", service_error_code="NoSuchKey", http_status_code=404)
    assert store.get("development/s/nope.json") is None


def test_s3_list_pages_through_every_key() -> None:
    store, stubber = _s3()
    stubber.add_response(
        "list_objects_v2",
        {
            "IsTruncated": True,
            "NextContinuationToken": "t",
            "Contents": [{"Key": "development/s/b.json"}],
        },
        {"Bucket": BUCKET, "Prefix": "development/s/"},
    )
    stubber.add_response(
        "list_objects_v2",
        {"IsTruncated": False, "Contents": [{"Key": "development/s/a.json"}]},
        {"Bucket": BUCKET, "Prefix": "development/s/", "ContinuationToken": "t"},
    )
    assert store.list_keys("development/s/") == ["development/s/a.json", "development/s/b.json"]
