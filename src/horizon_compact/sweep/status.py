"""Read a sweep's objects and summarize them (Phase 1 IMPLEMENTATION doc section 6.1). Read-only."""

from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any

from horizon_compact.sweep.runner import Role, sweep_prefix
from horizon_compact.sweep.store import Store

_ATTEMPT = re.compile(r"runs/r-[0-9a-f]{12}/attempt-\d+\.json$")
_FINAL = re.compile(r"runs/r-[0-9a-f]{12}/final\.json$")


def summarize(
    store: Store, experiment_name: str, sweep_id: str, role: Role = "development"
) -> dict[str, Any] | None:
    prefix = sweep_prefix(experiment_name, sweep_id, role)
    manifest_text = store.get(f"{prefix}manifest.json")
    if manifest_text is None:
        return None
    manifest = json.loads(manifest_text)
    keys = store.list_keys(prefix)
    finals = [json.loads(store.get(k) or "{}") for k in keys if _FINAL.search(k)]
    attempts = [json.loads(store.get(k) or "{}") for k in keys if _ATTEMPT.search(k)]
    sessions = [json.loads(store.get(k) or "{}") for k in keys if "/sessions/" in k]
    return {
        "sweep_id": sweep_id,
        "runs_total": len(manifest["runs"]),
        "runs_finished": len(finals),
        "final_statuses": dict(sorted(Counter(f["status"] for f in finals).items())),
        "attempts": len(attempts),
        "attempt_statuses": dict(sorted(Counter(a["status"] for a in attempts).items())),
        "cost_usd": round(sum(float(a.get("cost_usd", 0.0)) for a in attempts), 6),
        "sessions": [
            {
                "started_at": s.get("started_at"),
                "runner": s.get("runner"),
                "stopped": s.get("stopped"),
                "attempts": s.get("attempts_this_session"),
                "cost_usd": s.get("cost_usd_this_session"),
            }
            for s in sessions
        ],
    }
