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
6. The garden shapes (Phase 3.5 IMPLEMENTATION doc decision 3, step 7): ``experiment/shapes/`` loads, holds
   one ``garden_sN`` for each company ``sN`` and nothing else, each with its scenario's form (``_form``), no
   never-use term, and prompts that differ only in the objective sentence.
"""

from __future__ import annotations

import hashlib
import re
import tomllib
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from horizon_compact.dossier.check import Report
from horizon_compact.dossier.figures import FigureError
from horizon_compact.dossier.render import COMPANY_DIR
from horizon_compact.experiment import (
    SOURCE_SUFFIX,
    TEMPLATE_IDS,
    Experiment,
    ExperimentError,
    JointCap,
    NotBoth,
    OptionFixes,
    OptionRequires,
    Scenario,
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
SHAPES_EXPERIMENT = "shapes"
SHAPE_PREFIX = "garden_"
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


class SealedDraw(_Strict):
    """The sealed draw (section 13). Setting ``sealed_template`` moves the content hash and is none of the
    four reasons, so it is its own record, chained like an entry at the place ``after_entry`` names (the
    number of entries before it), with no reason field. The check recomputes the template from the commit."""

    date: date
    commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    template: str
    hash_before: str
    hash_after: str
    after_entry: int = Field(ge=0)


class ChangeLog(_Strict):
    baseline: Baseline
    entries: list[LogEntry] = []
    draw: SealedDraw | None = None


SEALED_DRAW_SUFFIX = "|sealed-template"
SEALED_DRAW_TEMPLATES = ("w1", "w2", "w3")


def sealed_draw(commit: str) -> str:
    """``int(sha256(commit + "|sealed-template"), 16) % 3``, mapped to w1, w2, w3 (section 13). Anyone can
    recompute it."""
    digest = hashlib.sha256((commit + SEALED_DRAW_SUFFIX).encode("utf-8")).hexdigest()
    return SEALED_DRAW_TEMPLATES[int(digest, 16) % len(SEALED_DRAW_TEMPLATES)]


def check_change_log(
    root: Path, content_hash: str, sealed_template: str | None = None
) -> tuple[list[str], list[str]]:
    """``(failures, notes)``. A missing log is a note: the baseline is step 9. A drawn ``sealed_template``
    needs the draw record, and the record must match it and the computation."""
    path = root / CHANGELOG_PATH
    if not path.is_file():
        return [], [f"{CHANGELOG_PATH} does not exist yet (the baseline commit makes it)"]
    try:
        log = ChangeLog.model_validate(tomllib.loads(path.read_text(encoding="utf-8")))
    except (OSError, tomllib.TOMLDecodeError, ValidationError) as exc:
        return [f"{CHANGELOG_PATH} is invalid: {exc}"], []
    failures: list[str] = []
    draw = log.draw
    if draw is not None:
        if draw.after_entry > len(log.entries):
            failures.append(
                f"{CHANGELOG_PATH}: the draw follows entry {draw.after_entry}, which does not exist"
            )
        if sealed_draw(draw.commit) != draw.template:
            failures.append(
                f"{CHANGELOG_PATH}: the draw records {draw.template}, but commit {draw.commit[:12]} draws "
                f"{sealed_draw(draw.commit)}"
            )
        if sealed_template != draw.template:
            failures.append(
                f"{CHANGELOG_PATH}: the draw records {draw.template}, but objectives.toml's sealed_template is "
                f"{sealed_template!r}"
            )
    elif sealed_template:
        failures.append(
            f"sealed_template is {sealed_template!r} but {CHANGELOG_PATH} has no draw record (section 13)"
        )
    previous = log.baseline.hash
    links: list[tuple[str, str, str]] = [
        (f"entry {n}", e.hash_before, e.hash_after) for n, e in enumerate(log.entries, start=1)
    ]
    if draw is not None and draw.after_entry <= len(log.entries):
        links.insert(draw.after_entry, ("the draw", draw.hash_before, draw.hash_after))
    for name, before, after in links:
        if before != previous:
            failures.append(
                f"{CHANGELOG_PATH}: {name} starts from {before[:12]}, "
                f"but the one before it ended at {previous[:12]}"
            )
        previous = after
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


def _form(scenario: Scenario) -> tuple[object, ...]:
    """What a garden shape copies from its company scenario: everything that can make a reply fail the format,
    none of the content. Caps and rule amounts are kept as ratios to the total, so a shape may scale the
    amounts; the order of the lines is not kept, since every run shuffles it."""

    def ratio(amount: float) -> float:
        return round(amount / scenario.total, 3)

    caps = {
        kind: sorted(ratio(lever.cap) for lever in scenario.offered(kind))
        for kind in ("source", "use")
    }
    levers = {lever.key: lever for lever in scenario.levers}

    def line(key: str) -> tuple[str, float]:
        return (levers[key].kind, ratio(levers[key].cap))

    extra = sorted(
        (
            rule.kind,
            tuple(sorted(line(key) for key in rule.keys))
            if isinstance(rule, NotBoth)
            else (line(rule.key), line(rule.against))
            if isinstance(rule, JointCap)
            else (line(rule.key),),
            (ratio(rule.base), rule.divisor, rule.fraction) if isinstance(rule, JointCap) else (),
            ratio(rule.amount) if isinstance(rule, OptionFixes) else None,
            len(rule.options) if isinstance(rule, OptionRequires) else None,
        )
        for rule in scenario.rules
    )
    return (
        scenario.rule,
        scenario.unit,
        scenario.tolerance_fraction,
        scenario.max_tokens,
        caps["source"],
        caps["use"],
        sum(lever.kind == "not_offered" for lever in scenario.levers),
        all(lever.detail for lever in scenario.offered()),
        len(scenario.choice.options) if scenario.choice else 0,
        extra,
    )


def shape_failures(company: Experiment, root: Path) -> list[str]:
    """The garden shapes (decision 3): one per company scenario, each with its form, off the never-use list,
    and prompts that differ only in the objective sentence. The placeholder rule's subject-vocabulary test is
    in tests/test_sweep_prompt.py, as it is for the placeholder."""
    try:
        shapes = load_experiment(SHAPES_EXPERIMENT, root / "experiment")
    except ExperimentError as exc:
        return [f"{SHAPES_EXPERIMENT}: {exc}"]
    expected = {SHAPE_PREFIX + scenario_id for scenario_id in company.scenarios}
    failures = [
        f"{SHAPES_EXPERIMENT}: {shape_id} has no company scenario {shape_id.removeprefix(SHAPE_PREFIX)}"
        for shape_id in sorted(set(shapes.scenarios) - expected)
    ] + [
        f"{SHAPES_EXPERIMENT}: no garden shape {shape_id} for company scenario "
        f"{shape_id.removeprefix(SHAPE_PREFIX)}"
        for shape_id in sorted(expected - set(shapes.scenarios))
    ]
    for scenario_id, scenario in company.scenarios.items():
        shape = shapes.scenarios.get(SHAPE_PREFIX + scenario_id)
        if shape is not None and _form(shape) != _form(scenario):
            failures.append(
                f"{SHAPES_EXPERIMENT}: {shape.id} does not have {scenario_id}'s form "
                f"(rule, unit, caps as ratios to the total, extra rules, choice); "
                f"{_form(shape)} against {_form(scenario)}"
            )
    failures.extend(f"{SHAPES_EXPERIMENT}: {f}" for f in _vocabulary_failures(shapes))
    failures.extend(f"{SHAPES_EXPERIMENT}: {f}" for f in _prompt_difference_failures(shapes))
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
    report.failures.extend(shape_failures(exp, root))
    report.failures.extend(_probe_failures(root, exp))
    failures, notes = check_change_log(root, exp.content_hash, exp.sealed_template)
    report.failures.extend(failures)
    report.notes.extend(notes)
    report.notes.append(
        f"instrument content hash {exp.content_hash[:12]}; sealed_template "
        f"{exp.sealed_template!r}; scenarios {', '.join(exp.scenarios)}"
    )
    return report
