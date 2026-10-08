"""The blind format report and the failures view (Phase 2.5 IMPLEMENTATION doc section 11.3).

They are the only readers of a company run's records. **The format report** gives, per scenario and template,
the runs, how many were valid, rescaled or valid on the first attempt, and the failures by type; per objective
it gives only valid against not valid, which DoD 4 needs and which shows nothing about direction. **The
failures view** gives, for each run whose final status is not valid, its status, its stop reason and the
validator's problems, **with every digit replaced by `#` and every option's key by `<option>`**, and only the
shape of any text the model wrote outside the tool call: its length in words, whether it reads as a decline,
and whether it names the tool.

*Stricter than section 11.3 (Opus, 2026-10-07, found by this module's test):* the section allowed the text
itself. A model that fails by not calling the tool usually writes its decision as prose, and masking digits
and option keys does not hide "closing the plant", so the text is never printed.

Neither ever prints an amount, a choice, a memo or a parsed decision: they read only the fields named here,
and a test plants a record full of all four and checks that none of them appears in either output.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Iterable
from typing import Any

from horizon_compact.experiment import Experiment
from horizon_compact.sweep.plan import RunSpec, SweepPlan
from horizon_compact.sweep.runner import sweep_prefix
from horizon_compact.sweep.store import Store

VALID = frozenset({"valid", "valid_rescaled"})
OPTION_MASK = "<option>"
_DIGITS = re.compile(r"\d")
_NAMES_TOOL = re.compile(r"\bsubmit_decision\b|\btool\b", re.IGNORECASE)


def _finals(store: Store, plan: SweepPlan) -> dict[str, dict[str, Any]]:
    prefix = sweep_prefix(plan.experiment, plan.sweep_id)
    found: dict[str, dict[str, Any]] = {}
    for run in plan.runs:
        text = store.get(f"{prefix}runs/{run.run_id}/final.json")
        if text is not None:
            found[run.run_id] = json.loads(text)
    return found


def _counts(statuses: Iterable[str]) -> str:
    counter = Counter(statuses)
    return ", ".join(f"{name} {n}" for name, n in sorted(counter.items())) or "none"


def format_report(store: Store, experiment: Experiment, plan: SweepPlan) -> str:
    finals = _finals(store, plan)
    objectives = [o.id for o in experiment.objectives]
    lines = [
        f"# Format report: `{plan.sweep_id}`",
        "",
        f"Experiment `{plan.experiment}`, model `{plan.model_key}`, content hash `{plan.content_hash[:12]}`, "
        f"templates {', '.join(plan.templates)}, {plan.repeats} repeats. Written by `hc sweep report` from the "
        "stored records; do not edit by hand. **Blind:** no amount, choice, memo or line appears here, and per "
        "objective only valid against not valid (IMPLEMENTATION doc section 11.3). A cell passes with at least "
        "one valid run (section 11.2).",
        "",
        "| Scenario | Template | Runs | Finished | Valid | Of which rescaled | Valid on the first attempt "
        "| Not valid, by type |",
        "|---|---|---|---|---|---|---|---|",
    ]
    failing_cells: list[str] = []
    per_objective: list[str] = []
    for scenario_id in plan.scenarios:
        for template_id in plan.templates:
            runs = [
                r for r in plan.runs if (r.scenario_id, r.wording_id) == (scenario_id, template_id)
            ]
            done = [finals[r.run_id] for r in runs if r.run_id in finals]
            valid = [f for f in done if f["status"] in VALID]
            lines.append(
                f"| {scenario_id} | {template_id} | {len(runs)} | {len(done)} | {len(valid)} | "
                f"{sum(1 for f in valid if f['status'] == 'valid_rescaled')} | "
                f"{sum(1 for f in done if f['first_attempt_status'] in VALID)} | "
                f"{_counts(f['status'] for f in done if f['status'] not in VALID)} |"
            )
            cells: list[str] = []
            for objective_id in objectives:
                cell = [r for r in runs if r.objective_id == objective_id]
                cell_done = [finals[r.run_id] for r in cell if r.run_id in finals]
                ok = sum(1 for f in cell_done if f["status"] in VALID)
                cells.append(f"{ok} of {len(cell_done)}")
                if len(cell_done) == len(cell) and cell and ok == 0:
                    failing_cells.append(f"{scenario_id} {template_id} objective {objective_id}")
            per_objective.append(f"| {scenario_id} | {template_id} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Valid runs per objective",
        "",
        "| Scenario | Template | " + " | ".join(objectives) + " |",
        "|---|---|" + "---|" * len(objectives),
        *per_objective,
        "",
        f"**Runs finished: {len(finals)} of {len(plan.runs)}.** "
        + (
            "**Cells with no valid run: " + "; ".join(failing_cells) + ".**"
            if failing_cells
            else "Every finished cell has at least one valid run."
        ),
        "",
    ]
    return "\n".join(lines)


def mask(text: str, option_keys: Iterable[str]) -> str:
    """Every digit to `#`, and every option key to `<option>`, longest first so no key is half masked."""
    for key in sorted(set(option_keys), key=len, reverse=True):
        text = re.sub(rf"\b{re.escape(key)}\b", OPTION_MASK, text)
    return _DIGITS.sub("#", text)


def _option_keys(experiment: Experiment, scenario_id: str) -> list[str]:
    choice = experiment.get_scenario(scenario_id).choice
    return [o.key for o in choice.options] if choice is not None else []


def _text_shape(written: str, attempt: dict[str, Any]) -> str:
    """The shape of the model's text, never its words: a no-tool-call reply is usually the decision."""
    if not written:
        return "none"
    names_tool = _NAMES_TOOL.search(written) is not None
    return (
        f"{len(written.split())} words; reads as a decline: {'yes' if attempt.get('possible_decline') else 'no'}; "
        f"names the tool: {'yes' if names_tool else 'no'}"
    )


def failures_view(store: Store, experiment: Experiment, plan: SweepPlan) -> str:
    finals = _finals(store, plan)
    prefix = sweep_prefix(plan.experiment, plan.sweep_id)
    failed: list[tuple[RunSpec, dict[str, Any]]] = [
        (r, finals[r.run_id])
        for r in plan.runs
        if r.run_id in finals and finals[r.run_id]["status"] not in VALID
    ]
    lines = [
        f"# Failures view: `{plan.sweep_id}`",
        "",
        "Each run whose final status is not valid, from its final attempt: its status, stop reason and the "
        "validator's problems, **with every digit replaced by `#` and every option's key by `<option>`**, and the "
        "shape of any text outside the tool call, never its words. No amount, choice or memo (IMPLEMENTATION doc "
        "section 11.3, made stricter). Written by `hc sweep report`; do not edit by hand.",
        "",
        f"**{len(failed)} of {len(finals)} finished runs are not valid.**",
        "",
    ]
    for spec, final in failed:
        keys = _option_keys(experiment, spec.scenario_id)
        text = store.get(f"{prefix}runs/{spec.run_id}/attempt-{final['final_attempt']}.json")
        attempt: dict[str, Any] = json.loads(text) if text is not None else {}
        validation = attempt.get("validation") or {}
        problems = [str(p) for p in validation.get("problems") or []]
        if attempt.get("detail"):
            problems.append(str(attempt["detail"]))
        written = " ".join(str(t) for t in attempt.get("text_blocks") or [] if str(t).strip())
        lines += [
            f"## {spec.scenario_id} {spec.wording_id} objective {spec.objective_id}, `{spec.run_id}`",
            "",
            f"- status: `{final['status']}` (first attempt `{final['first_attempt_status']}`, "
            f"{final['model_attempts']} model attempts)",
            f"- stop reason: `{attempt.get('stop_reason')}`",
            "- problems: "
            + ("; ".join(mask(p, keys) for p in problems) if problems else "none recorded"),
            "- text outside the tool call: " + _text_shape(written, attempt),
            "",
        ]
    lines += [
        "## Failed attempts in runs that ended valid",
        "",
        "The same fields for every model attempt that was not valid in a run that a later attempt made valid, so "
        "a failure that a retry hides is still counted by its cause.",
        "",
    ]
    hidden = 0
    for spec in plan.runs:
        ended = finals.get(spec.run_id)
        if ended is None or ended["status"] not in VALID:
            continue
        keys = _option_keys(experiment, spec.scenario_id)
        for n in range(1, int(ended["final_attempt"])):
            text = store.get(f"{prefix}runs/{spec.run_id}/attempt-{n}.json")
            attempt = json.loads(text) if text is not None else {}
            if attempt.get("status") in VALID or attempt.get("status") in (
                "api_error",
                "config_error",
                None,
            ):
                continue
            hidden += 1
            validation = attempt.get("validation") or {}
            problems = [str(p) for p in validation.get("problems") or []]
            written = " ".join(str(t) for t in attempt.get("text_blocks") or [] if str(t).strip())
            lines.append(
                f"- {spec.scenario_id} {spec.wording_id} objective {spec.objective_id}, attempt {n}: "
                f"`{attempt.get('status')}`; problems: "
                + ("; ".join(mask(p, keys) for p in problems) if problems else "none recorded")
                + f"; text outside the tool call: {_text_shape(written, attempt)}"
            )
    lines += ["", f"**{hidden} failed attempts in runs that ended valid.**", ""]
    return "\n".join(lines)
