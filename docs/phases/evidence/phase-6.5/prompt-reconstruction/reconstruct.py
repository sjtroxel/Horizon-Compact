"""Phase 6.5 step 7: the prompt-reconstruction check (IMPLEMENTATION doc section 5.3, decision G (a)).

    python3 scratch/p65-s7-reconstruct.py prepare <reader-dir>   # build the reader's folder
    python3 scratch/p65-s7-reconstruct.py compare <reader-dir>   # compare what the reader rebuilt

`prepare` picks the ten samples by the fixed rule, copies the experiment's content files at
`prereg-v1` (checked against the hashes every sample's record carries), writes each sample's recorded
settings, and writes the brief. It copies no code, no raw record and no prompt.

`compare` reads `<reader-dir>/rebuilt/<sample>.json`, hashes each the way the harness hashed the prompt
it sent (canonical JSON of system, user and, for a decision, the tool), and compares it with the
record's `prompt_sha256`; for a mismatch it writes a unified diff of each part. It reads the records;
the reader never does.

The rule (section 5.3): for each scenario, the first official run by run id in Haiku 5.5's grid and in
gpt-oss-120b's grid; the first run by run id of the thinking sub-study; the first call by run id of Haiku
5.5's awareness probe (the main model's). Ten prompts. Each decision sample's prompt is its first
attempt's (a retry is the identical request).
"""

from __future__ import annotations

import difflib
import hashlib
import json
import subprocess
import sys
from pathlib import Path

# The repository: the nearest folder above this file that holds .git (the script runs from scratch/
# or from its copy in docs/phases/evidence/phase-6.5/prompt-reconstruction/).
REPO = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
RAW = REPO / "experiment" / "raw" / "official" / "company"
TAG = "prereg-v1"
GRIDS = {
    "haiku-5-5": "grid-haiku-5-5-0b99fabb",
    "gpt-oss-openrouter": "grid-gpt-oss-openrouter-fe599ad2",
}
THINKING = "thinking-haiku-5-5-418caa9c"
AWARENESS = "awareness/awareness-haiku-5-5-0ce6ad12"
NAMES = {"haiku-5-5": "Claude Haiku 5.5", "gpt-oss-openrouter": "gpt-oss-120b"}
CONTENT = [
    "company/dossier.toml",
    "company/objectives.toml",
    "company/scenarios/s1.toml",
    "company/scenarios/s2.toml",
    "company/scenarios/s3.toml",
    "company/scenarios/s4.toml",
]
SETTINGS = [
    "model_key",
    "model_id",
    "sweep_id",
    "run_id",
    "scenario_id",
    "objective_id",
    "wording_variant_id",
    "menu_order",
    "option_order",
    "menu_order_seed",
]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _decision_runs(sweep: str) -> list[tuple[str, dict]]:
    runs = []
    for folder in sorted((RAW / sweep / "runs").iterdir()):
        runs.append((folder.name, _load(folder / "attempt-1.json")))
    return runs


def samples() -> list[dict]:
    """The ten samples, by the rule. Each: its name, its kind and its record (never given to the reader)."""
    picked = []
    for model, sweep in GRIDS.items():
        runs = _decision_runs(sweep)
        for scenario in ("s1", "s2", "s3", "s4"):
            record = next(d for _, d in runs if d["scenario_id"] == scenario)
            picked.append(
                {"name": f"grid-{model}-{scenario}", "kind": "decision", "record": record}
            )
    _, record = _decision_runs(THINKING)[0]
    picked.append({"name": "thinking-haiku-5-5-s1", "kind": "decision", "record": record})
    first = sorted((RAW / AWARENESS / "runs").glob("*.json"))[0]
    picked.append({"name": "awareness-haiku-5-5", "kind": "awareness", "record": _load(first)})
    assert len(picked) == 10
    return picked


def _git_show(path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{TAG}:experiment/{path}"], cwd=REPO, check=True, capture_output=True
    ).stdout


def prepare(reader: Path) -> None:
    if reader.exists() and any(reader.iterdir()):
        sys.exit(f"{reader} is not empty; the reader's folder starts empty")
    picked = samples()
    (reader / "content" / "company" / "scenarios").mkdir(parents=True)
    (reader / "rebuilt").mkdir()
    for path in CONTENT:
        data = _git_show(path)
        digest = hashlib.sha256(data).hexdigest()
        for s in picked:
            assert s["record"]["file_hashes"][path] == digest, (path, s["name"])
        (reader / "content" / path).write_bytes(data)
    settings = []
    for s in picked:
        r = s["record"]
        entry = {"sample": s["name"], "kind": s["kind"], "model": NAMES[r["model_key"]]}
        entry.update({k: r[k] for k in SETTINGS})
        entry["sweep_kind"] = s["name"].split("-")[0]
        settings.append(entry)
    (reader / "samples.json").write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    (reader / "BRIEF.md").write_text(BRIEF, encoding="utf-8")
    print(f"prepared {reader}: {len(CONTENT)} content files, {len(settings)} samples, the brief")


def _canonical_hash(kind: str, rebuilt: dict) -> str:
    body = {"system": rebuilt.get("system"), "user": rebuilt.get("user")}
    if kind == "decision":
        tool = rebuilt.get("tool") or {}
        body["tool"] = {
            "name": tool.get("name"),
            "description": tool.get("description"),
            "input_schema": tool.get("input_schema"),
        }
    text = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _recorded_parts(kind: str, record: dict) -> dict:
    """The prompt's parts as the record holds them (route-independent, as the harness hashed them)."""
    request = record["request"]
    if record["route_kind"] == "anthropic":
        system = request["system"]
        user = request["messages"][0]["content"]
        tools = request.get("tools", [])
        tool = tools[0] if tools else None
    else:  # OpenRouter's chat completions: the system and user messages, the tool as a function
        messages = {m["role"]: m["content"] for m in request["messages"]}
        system, user = messages["system"], messages["user"]
        tools = request.get("tools", [])
        tool = None
        if tools:
            fn = tools[0]["function"]
            tool = {
                "name": fn["name"],
                "description": fn["description"],
                "input_schema": fn["parameters"],
            }
    parts = {"system": system, "user": user}
    if kind == "decision":
        parts["tool"] = tool
    return parts


def _as_text(value: object) -> list[str]:
    if isinstance(value, str):
        return value.splitlines(keepends=True)
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").splitlines(keepends=True)


def compare(reader: Path) -> None:
    report = []
    passed = 0
    for s in samples():
        name, kind, record = s["name"], s["kind"], s["record"]
        path = reader / "rebuilt" / f"{name}.json"
        if not path.exists():
            report.append(f"## {name}: MISSING (no rebuilt/{name}.json)\n")
            continue
        rebuilt = _load(path)
        recorded = _recorded_parts(kind, record)
        assert _canonical_hash(kind, recorded) == record["prompt_sha256"], (
            f"{name}: the record's own parts"
        )
        got = _canonical_hash(kind, rebuilt)
        if got == record["prompt_sha256"]:
            passed += 1
            report.append(f"## {name}: MATCH (sha256 {got[:16]})\n")
            continue
        report.append(
            f"## {name}: MISMATCH (rebuilt {got[:16]}, recorded {record['prompt_sha256'][:16]})\n"
        )
        for part, value in recorded.items():
            mine = rebuilt.get(part)
            if mine == value:
                report.append(f"- {part}: identical\n")
                continue
            diff = difflib.unified_diff(
                _as_text(value), _as_text(mine), f"recorded {part}", f"rebuilt {part}", n=2
            )
            report.append(f"- {part}: differs\n\n```diff\n{''.join(diff)}```\n")
    head = f"# Prompt-reconstruction check: {passed} of 10 match\n\n"
    out = reader / "comparison.md"
    out.write_text(head + "\n".join(report), encoding="utf-8")
    print(head.strip())
    print(f"written {out}")


BRIEF = """# Brief: rebuild ten prompts from a published methods page

You are helping test a published research write-up. The question is whether a careful stranger, with only what is
published, can rebuild the exact prompts an experiment sent to two AI models. You are that stranger.

## What you may use, and nothing else

1. **The site**, running locally at http://127.0.0.1:4173/ . Start with the methods page,
   http://127.0.0.1:4173/methods/ , and read any page of the site you like. Fetch it with curl or any tool you have.
2. **This folder:** `content/` (the experiment's content files, exactly as published), `samples.json` (each sample's
   recorded settings), and this brief.

**Do not** open, search or read any file outside this folder; do not look for the project's repository, its code or its
raw records, on this machine or on the internet; do not fetch any address but http://127.0.0.1:4173/ ; do not call any
AI model's API; do not use git. If the site links somewhere else (GitHub, for example), do not follow the link: note it
in NOTES.md as something you could not use. The test is only fair if you use only what is listed above. Nothing
enforces this; it is on your honor, and your notes should say plainly if you broke it, even by accident.

## What to produce

For each of the ten entries in `samples.json`, write `rebuilt/<sample>.json`, where `<sample>` is the entry's
`sample` field:

- for an entry whose `kind` is `decision`:
  `{"system": "<the system text>", "user": "<the user message>", "tool": {"name": "...", "description": "...",
  "input_schema": {...}}}`
- for an entry whose `kind` is `awareness`: `{"system": "<the system text>", "user": "<the user message>"}`

Each must be exactly what the model was sent: every character, every blank line, every line break, every space. The
tool's `input_schema` is a JSON object, compared as data (key order inside it does not matter); the texts are compared
byte for byte.

Then write `NOTES.md`: for each sample, what you were sure of, what you had to guess, and where on the site (or in
which content file) you found each rule you used. A guess the site does not settle is the most useful thing you can
report. Also list anything the site seemed to promise but you could not find.

You will not be told whether your rebuilds match until you are finished. Do not stop at the first doubt: make your
best rebuild of every sample, and record the doubt in NOTES.md.
"""


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("prepare", "compare"):
        sys.exit(__doc__)
    {"prepare": prepare, "compare": compare}[sys.argv[1]](Path(sys.argv[2]).expanduser())
