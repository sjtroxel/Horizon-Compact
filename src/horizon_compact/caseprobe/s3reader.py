"""The gate's S3 probe reader (protocol §12.10 check (3); search-half doc §4.8, §4.10).

Builds one ``ProbeRecord`` per recognition-probe call object under ``cases/<label>/probes/``: its model, its
set, the object's ``LastModified`` (results objects are write-once, so that is when it was written, a time
neither author can set) and the **final** ``passed`` of its verdict record. **Fails closed:** a call with no
verdict, a verdict that does not name this call object, or a ``passed`` that is not literally true counts as
not passed, so an unjudged call can never admit a case.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from horizon_compact.caseprobe.layout import parse_call_key, probes_prefix, verdict_key
from horizon_compact.protocol.cases import ProbeRecord

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


def _verdict_passed(client: S3Client, bucket: str, key: str, verdict: str) -> bool:
    try:
        body = client.get_object(Bucket=bucket, Key=verdict)["Body"].read()
    except client.exceptions.NoSuchKey:
        return False
    try:
        record: Any = json.loads(bytes(body).decode("utf-8"))
    except ValueError:
        return False
    return (
        isinstance(record, dict) and record.get("call_key") == key and record.get("passed") is True
    )


def read_probe_records(client: S3Client, bucket: str, label: str) -> list[ProbeRecord]:
    prefix = probes_prefix(label)
    found: list[ProbeRecord] = []
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj.get("Key", "")
            where = parse_call_key(key)
            if where is None or where.label != label:
                continue
            modified: datetime = obj["LastModified"]
            found.append(
                ProbeRecord(
                    key=key,
                    model_key=where.model_key,
                    probe_set=where.probe_set,
                    passed=_verdict_passed(
                        client,
                        bucket,
                        key,
                        verdict_key(label, where.probe_set, where.model_key, where.call),
                    ),
                    last_modified=modified,
                )
            )
    return sorted(found, key=lambda p: (p.probe_set, p.model_key, p.key))
