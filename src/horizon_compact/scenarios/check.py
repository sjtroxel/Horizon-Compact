"""``hc scenarios check``, run by ``make check`` and CI (Phase 2.5 IMPLEMENTATION doc sections 7, 8.7 and 14).

Failures make the check fail; notes never do. Nothing here calls a model or reads a run's record.

1. Every source renders to its committed ``sN.toml`` and the cited public version exactly, and no rendered
   scenario is left without a source.
2. No digit outside a placeholder in any source text (the renderer refuses it), every placeholder, cap, total
   and rule number is a row, and every scenario row is used, directly or through a formula.
3. The template text check (section 7): the three templates each hold ``{who}`` and ``{when}`` once, the
   baseline sentence holds neither, no term from ``planning/06`` section 3.1's never-use list appears in a
   template, an objective or a scenario, and for every scenario, objective and template the rendered prompts
   differ only in the objective sentence, which is in one place.
4. The comprehension probes (section 10): one file per scenario, every key resolvable.
5. The change log (section 14), once ``CHANGELOG.toml`` exists: the current content hash is the latest entry's
   "after" hash, and the entries chain.
"""

from __future__ import annotations

import re
import tomllib
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from horizon_compact.dossier.check import Report
from horizon_compact.dossier.figures import FigureError
from horizon_compact.dossier.render import COMPANY_DIR
from horizon_compact.experiment import (
    SOURCE_SUFFIX,
    TEMPLATE_IDS,
    Experiment,
    ExperimentError,
    load_experiment,
)
from horizon_compact.probes.questions import ProbeError
from horizon_compact.probes.run import load_probe_sets
from horizon_compact.scenarios.render import (
    SCENARIO_FIGURES_FILE,
    SCENARIOS_DIR,
    ScenarioSourceError,
    load_scenario_figures,
    render_all,
    scenario_row_ids,
)
from horizon_compact.sweep.plan import SweepRefusal
from horizon_compact.sweep.prompt import render_prompt

COMPANY_EXPERIMENT = "company"
CHANGELOG_PATH = f"{COMPANY_DIR}/CHANGELOG.toml"
# planning/06 section 3.1, "Never in public": words the instrument's own text must not use. "Stakeholder"
# alone is allowed (the Roundtable's word, in objectives B and D); only "stakeholder capitalism" is not.
NEVER_USE = (
    "greed",
    "greedy",
    "oligarch",
    "oligarchs",
    "the elite",
    "esg",
    "stakeholder capitalism",
    "corporate greed",
    "evil",
    "villain",
    "ruthless",
)
_NEVER_USE = re.compile(
    r"\b(?:" + "|".join(re.escape(term) for term in NEVER_USE) + r")\b", re.IGNORECASE
)
OBJECTIVE_MARK = "\0"
CHECK_SEED = 1


# --- the change log (section 14) -------------------------------------------------------------------------


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Baseline(_Strict):
    """The commit that first holds all four scenarios and three templates, before any model has seen them."""

    date: date
    hash: str


class LogEntry(_Strict):
    date: date
    files: list[str]
    hash_before: str
    hash_after: str
    evidence: str
    # Four values and no fifth (section 9): a change made for an outcome is not a change this log records.
    reason: Literal["format", "clarity", "neutrality", "factual"]


class ChangeLog(_Strict):
    baseline: Baseline
    entries: list[LogEntry] = []


def check_change_log(root: Path, content_hash: str) -> tuple[list[str], list[str]]:
    """``(failures, notes)``. A missing log is a note: the baseline is step 9."""
    path = root / CHANGELOG_PATH
    if not path.is_file():
        return [], [f"{CHANGELOG_PATH} does not exist yet (the baseline commit makes it)"]
    try:
        log = ChangeLog.model_validate(tomllib.loads(path.read_text(encoding="utf-8")))
    except (OSError, tomllib.TOMLDecodeError, ValidationError) as exc:
        return [f"{CHANGELOG_PATH} is invalid: {exc}"], []
    failures: list[str] = []
    previous = log.baseline.hash
    for number, entry in enumerate(log.entries, start=1):
        if entry.hash_before != previous:
            failures.append(
                f"{CHANGELOG_PATH}: entry {number} starts from {entry.hash_before[:12]}, "
                f"but the one before it ended at {previous[:12]}"
            )
        previous = entry.hash_after
    if content_hash != previous:
        failures.append(
            f"the instrument's content hash {content_hash[:12]} is not the log's latest "
            f"{previous[:12]}: a content change needs an entry in {CHANGELOG_PATH}"
        )
    return failures, []


# --- the template text check (section 7) -----------------------------------------------------------------


def _vocabulary_failures(exp: Experiment) -> list[str]:
    texts: dict[str, str] = {}
    for template_id, template in exp.templates.items():
        texts[f"template {template_id} (stated)"] = template.stated
        texts[f"template {template_id} (none)"] = template.none
    for objective in exp.objectives:
        texts[f"objective {objective.id} (who)"] = objective.who
        texts[f"objective {objective.id} (when)"] = objective.when
    for scenario in exp.scenarios.values():
        texts[f"{scenario.id} (scenario)"] = scenario.scenario
        texts[f"{scenario.id} (menu_heading)"] = scenario.menu_heading
        texts[f"{scenario.id} (instruction)"] = scenario.instruction
        for lever in scenario.levers:
            texts[f"{scenario.id} lever {lever.key}"] = f"{lever.label} {lever.note} {lever.detail}"
        if scenario.choice is not None:
            for option in scenario.choice.options:
                texts[f"{scenario.id} option {option.key}"] = option.text
    return [
        f"{where} holds {match.group(0)!r}, a term planning/06 section 3.1 says is never used"
        for where, text in texts.items()
        if (match := _NEVER_USE.search(text))
    ]


def template_failures(exp: Experiment) -> list[str]:
    failures: list[str] = []
    if tuple(sorted(exp.templates)) != TEMPLATE_IDS:
        failures.append(
            f"objectives.toml has templates {sorted(exp.templates)}; the company needs {list(TEMPLATE_IDS)}"
        )
    for template_id, template in exp.templates.items():
        for kind, sentence in (("stated", template.stated), ("none", template.none)):
            if "\n" in sentence:
                failures.append(
                    f"template {template_id}'s {kind} sentence holds a line break; "
                    "the objective is one paragraph"
                )
        for name in ("who", "when"):
            count = template.stated.count("{" + name + "}")
            if count != 1:
                failures.append(
                    f"template {template_id}'s stated sentence holds {{{name}}} {count} times, not once"
                )
        if "{" in template.none or "}" in template.none:
            failures.append(f"template {template_id}'s none sentence holds a placeholder")
    failures.extend(_vocabulary_failures(exp))
    failures.extend(_prompt_difference_failures(exp))
    return failures


def _prompt_difference_failures(exp: Experiment) -> list[str]:
    """For each scenario, every objective under every template renders the same prompt once the objective
    sentence is taken out, and the sentence is in the prompt once: the prompts differ only in that sentence,
    at the same position."""
    failures: list[str] = []
    for scenario in exp.scenarios.values():
        reference: tuple[str, str] | None = None
        for objective in exp.objectives:
            for template_id in exp.templates:
                sentence = exp.wording_sentence(objective, template_id)
                rendered = render_prompt(exp, scenario, objective, template_id, CHECK_SEED)
                where = f"{scenario.id}, objective {objective.id}, template {template_id}"
                if rendered.user.count(sentence) != 1:
                    failures.append(f"{where}: the objective sentence is not in the prompt once")
                    continue
                masked = (rendered.system, rendered.user.replace(sentence, OBJECTIVE_MARK))
                if reference is None:
                    reference = masked
                elif masked != reference:
                    failures.append(
                        f"{where}: the prompt differs from the others outside the objective"
                    )
    return failures


# --- the probes (section 10) ------------------------------------------------------------------------------


def _probe_failures(root: Path, exp: Experiment) -> list[str]:
    """Every scenario has a probe file whose questions parse, whose choices are the scenario's own keys and
    whose numeric keys resolve from the rows. The probes are not part of the content hash; a broken key would
    still make a probe report wrong."""
    try:
        load_probe_sets(exp, load_scenario_figures(root), None)
    except (ProbeError, SweepRefusal, FigureError) as exc:
        return [f"probes: {exc}"]
    return []


# --- everything ------------------------------------------------------------------------------------------


def _scenario_file_failures(root: Path, expected: set[str]) -> list[str]:
    folder = root / SCENARIOS_DIR
    present = {
        path.name
        for path in folder.glob("*.toml")
        if folder.is_dir() and not path.name.endswith(SOURCE_SUFFIX)
    }
    return [
        f"{SCENARIOS_DIR}/{name} has no {name.removesuffix('.toml')}{SOURCE_SUFFIX}; "
        "a rendered scenario without a source cannot be checked"
        for name in sorted(present - {Path(path).name for path in expected})
    ]


def run_checks(root: Path) -> Report:
    report = Report()
    try:
        outputs = render_all(root)
    except (FigureError, ScenarioSourceError) as exc:
        report.failures.append(str(exc))
        return report
    for path, expected in outputs.files.items():
        target = root / path
        try:
            actual = target.read_text(encoding="utf-8")
        except OSError:
            report.failures.append(f"{path} is missing; run `hc scenarios render`")
            continue
        if actual != expected:
            report.failures.append(f"{path} differs from a fresh render; run `hc scenarios render`")
    report.failures.extend(_scenario_file_failures(root, set(outputs.files)))
    orphans = [row for row in scenario_row_ids(root) if row not in outputs.used]
    if orphans:
        report.failures.append(
            f"{SCENARIO_FIGURES_FILE}: rows the scenarios never use, directly or by formula: "
            f"{', '.join(orphans)}"
        )
    try:
        exp = load_experiment(COMPANY_EXPERIMENT, root / "experiment")
    except ExperimentError as exc:
        report.failures.append(str(exc))
        return report
    report.failures.extend(template_failures(exp))
    report.failures.extend(_probe_failures(root, exp))
    failures, notes = check_change_log(root, exp.content_hash)
    report.failures.extend(failures)
    report.notes.extend(notes)
    report.notes.append(
        f"instrument content hash {exp.content_hash[:12]}; sealed_template "
        f"{exp.sealed_template!r}; scenarios {', '.join(exp.scenarios)}"
    )
    return report
