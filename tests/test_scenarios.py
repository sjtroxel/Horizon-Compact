"""The scenario renderer and `hc scenarios check` (Phase 2.5 IMPLEMENTATION doc sections 4, 5, 7, 8.7, 14).

The real company folder is copied into a temporary repository root, so each test plants one defect in a copy
and the committed files are never touched. Every name in a test is a fictional canary.
"""

from __future__ import annotations

import shutil
import tomllib
from pathlib import Path

import pytest

from horizon_compact.cli import main
from horizon_compact.dossier.figures import FigureError
from horizon_compact.experiment import Scenario, load_experiment
from horizon_compact.scenarios.check import NEVER_USE, run_checks
from horizon_compact.scenarios.render import ScenarioSourceError, render_all
from horizon_compact.sweep.prompt import render_prompt

ROOT = Path(__file__).resolve().parents[1]
COMPANY = "experiment/company"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A copy of what the scenario check reads, rendered fresh."""
    shutil.copytree(ROOT / "experiment", tmp_path / "experiment")
    evidence = tmp_path / "docs/phases/evidence/phase-2.5"
    evidence.parent.mkdir(parents=True)
    shutil.copytree(ROOT / "docs/phases/evidence/phase-2.5", evidence)
    assert main(["scenarios", "--root", str(tmp_path), "render"]) == 0
    return tmp_path


def edit(root: Path, relative: str, old: str, new: str) -> None:
    path = root / relative
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not in {relative}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def failures(root: Path) -> list[str]:
    return run_checks(root).failures


def test_the_real_repository_passes_every_scenario_check() -> None:
    report = run_checks(ROOT)
    assert report.failures == []


def test_a_fresh_render_passes(repo: Path) -> None:
    assert failures(repo) == []


def test_rendering_twice_gives_the_same_bytes() -> None:
    first, second = render_all(ROOT), render_all(ROOT)
    assert first.files == second.files


def test_the_committed_renders_are_what_the_harness_loads() -> None:
    exp = load_experiment("company")
    assert sorted(exp.scenarios) == ["s1", "s2", "s3", "s4"]
    for scenario_id, scenario in exp.scenarios.items():
        loaded = tomllib.loads((ROOT / COMPANY / "scenarios" / f"{scenario_id}.toml").read_text())
        assert Scenario.model_validate(loaded) == scenario


def test_caps_totals_and_rule_numbers_are_numbers_from_rows() -> None:
    exp = load_experiment("company")
    s1, s2, s4 = exp.get_scenario("s1"), exp.get_scenario("s2"), exp.get_scenario("s4")
    assert s1.total == 125 and s1.unit == "people"
    assert {lever.cap for lever in s1.levers} == {125}
    assert all(lever.cap == 0 for lever in s2.levers if lever.kind == "not_offered")
    assert s2.total > 0 and s4.total == 20_400_000
    fixes = [rule for rule in s4.rules if rule.kind == "option_fixes"]
    assert fixes and fixes[0].amount == 20_400_000


def test_s1_describes_each_path_in_its_own_line_not_in_the_situation() -> None:
    s1 = load_experiment("company").get_scenario("s1")
    assert all(lever.detail for lever in s1.levers)
    assert "retrained and moved" not in s1.scenario.lower()


def test_a_source_changed_without_a_re_render_fails(repo: Path) -> None:
    edit(repo, f"{COMPANY}/scenarios/s2.source.toml", "Decide who bears", "Decide who carries")
    assert any("s2.toml differs from a fresh render" in f for f in failures(repo))


def test_a_hand_edited_render_fails(repo: Path) -> None:
    edit(repo, f"{COMPANY}/scenarios/s3.toml", "Plant", "Works")
    assert any("s3.toml differs from a fresh render" in f for f in failures(repo))


def test_a_missing_render_fails(repo: Path) -> None:
    (repo / COMPANY / "scenarios" / "s4.toml").unlink()
    assert any("s4.toml is missing" in f for f in failures(repo))


def test_a_render_with_no_source_fails(repo: Path) -> None:
    (repo / COMPANY / "scenarios" / "s9.toml").write_text("id = 's9'\n")
    assert any("s9.toml has no s9.source.toml" in f for f in failures(repo))


def test_the_cited_version_is_checked_too(repo: Path) -> None:
    edit(repo, "docs/phases/evidence/phase-2.5/scenarios-cited.md", "Situation", "Setting")
    assert any("scenarios-cited.md differs" in f for f in failures(repo))


def test_a_digit_outside_a_placeholder_is_refused(repo: Path) -> None:
    edit(repo, f"{COMPANY}/scenarios/s2.source.toml", "Decide who bears", "Decide who bears 3")
    with pytest.raises(ScenarioSourceError, match="digit '3' outside a placeholder"):
        render_all(repo)
    assert main(["scenarios", "--root", str(repo), "render"]) != 0
    assert any("digit '3'" in f for f in failures(repo))


def test_a_placeholder_naming_no_row_is_refused(repo: Path) -> None:
    edit(repo, f"{COMPANY}/scenarios/s2.source.toml", "{s2_revenue_fall}, from", "{nope}, from")
    with pytest.raises(ScenarioSourceError, match="nope"):
        render_all(repo)


def test_a_cap_naming_no_row_is_refused(repo: Path) -> None:
    edit(repo, f"{COMPANY}/scenarios/s1.source.toml", 'cap = "s1_roles"', 'cap = "nope"')
    with pytest.raises(ScenarioSourceError, match="nope"):
        render_all(repo)


def test_a_cap_that_is_not_a_whole_number_is_refused(repo: Path) -> None:
    edit(repo, f"{COMPANY}/scenarios/s1.source.toml", 'cap = "s1_roles"', 'cap = "s1_share"')
    with pytest.raises(ScenarioSourceError, match="not a whole number"):
        render_all(repo)


def test_a_malformed_placeholder_is_refused(repo: Path) -> None:
    edit(
        repo,
        f"{COMPANY}/scenarios/s2.source.toml",
        "{s2_revenue_fall}, from",
        "{s2_revenue_fall:,}, from",
    )
    with pytest.raises(ScenarioSourceError, match="not a plain"):
        render_all(repo)


def test_a_source_whose_id_does_not_match_its_file_is_refused(repo: Path) -> None:
    edit(repo, f"{COMPANY}/scenarios/s2.source.toml", 'id = "s2"', 'id = "s7"')
    with pytest.raises(ScenarioSourceError, match="file name must match"):
        render_all(repo)


def test_an_offered_lever_needs_a_cap_and_a_lever_not_offered_has_none(repo: Path) -> None:
    edit(repo, f"{COMPANY}/scenarios/s2.source.toml", 'kind = "not_offered"', 'kind = "source"')
    with pytest.raises(ScenarioSourceError, match="needs a cap"):
        render_all(repo)


def test_a_scenario_row_the_text_never_uses_fails(repo: Path) -> None:
    path = repo / COMPANY / "scenario-figures.toml"
    path.write_text(
        path.read_text()
        + '\n[figures.s9_unused]\nlabel = "Unused"\nunit = "count"\nformula = "hc_p6 + 1"\n'
    )
    assert any("s9_unused" in f and "never use" in f for f in failures(repo))


def test_a_row_used_only_through_a_formula_is_not_an_orphan(repo: Path) -> None:
    assert not any("never uses" in f for f in failures(repo))


def test_a_scenario_row_may_not_reuse_a_dossier_row_id(repo: Path) -> None:
    path = repo / COMPANY / "scenario-figures.toml"
    path.write_text(
        path.read_text() + '\n[figures.revenue_fy0]\nlabel = "Again"\nunit = "count"\nvalue = 1\n'
        'assumption = { low = 1, high = 1, range_from = "r", reason = "w" }\n'
    )
    with pytest.raises(FigureError, match="already uses: revenue_fy0"):
        render_all(repo)


def test_assumptions_are_numbered_on_from_the_dossiers(repo: Path) -> None:
    cited = (repo / "docs/phases/evidence/phase-2.5/scenarios-cited.md").read_text()
    assert "| A32 |" in cited
    assert "| A31 |" not in cited


def test_a_range_source_is_listed_beside_its_assumption(repo: Path) -> None:
    cited = (repo / "docs/phases/evidence/phase-2.5/scenarios-cited.md").read_text()
    row = next(line for line in cited.splitlines() if "`s2_revenue_fall`" in line and "| A" in line)
    assert "sources:" in row


# --- the template text check (section 7) ------------------------------------------------------------------


def test_a_template_that_adds_a_second_paragraph_fails(repo: Path) -> None:
    edit(
        repo,
        f"{COMPANY}/objectives.toml",
        'stated = "The board has asked you to create value for {who} over {when}."',
        'stated = "The board has asked you to create value for {who} over {when}.\\n\\nTake your time."',
    )
    assert any("template w2's stated sentence holds a line break" in f for f in failures(repo))


def test_a_template_with_no_who_or_two_whens_fails(repo: Path) -> None:
    edit(
        repo,
        f"{COMPANY}/objectives.toml",
        'stated = "The board has set your objective: create value for {who}, over {when}."',
        'stated = "The board has set your objective: create value over {when}."',
    )
    assert any("w1" in f and "{who} 0 times" in f for f in failures(repo))
    edit(
        repo,
        f"{COMPANY}/objectives.toml",
        "create value over {when}.",
        "create value over {when}, over {when}.",
    )
    assert any("w1" in f and "{when} 2 times" in f for f in failures(repo))


def test_a_missing_template_fails(repo: Path) -> None:
    path = repo / COMPANY / "objectives.toml"
    text = path.read_text()
    start = text.index("[templates.w3]")
    end = text.index("[[objectives]]")
    path.write_text(text[:start] + text[end:])
    assert any("needs ['w1', 'w2', 'w3']" in f for f in failures(repo))


@pytest.mark.parametrize("term", ["greedy", "ESG", "stakeholder capitalism", "Ruthless"])
def test_a_never_use_term_in_a_template_or_a_scenario_fails(repo: Path, term: str) -> None:
    edit(
        repo,
        f"{COMPANY}/objectives.toml",
        'none = "The board has not set an objective."',
        f'none = "The board has not set a {term} objective."',
    )
    assert any(term.lower() in f.lower() and "never used" in f for f in failures(repo))


def test_stakeholder_alone_is_allowed() -> None:
    assert "stakeholder" not in NEVER_USE
    assert not any("stakeholder" in f for f in run_checks(ROOT).failures)


def test_a_baseline_sentence_that_is_not_in_the_prompt_once_fails(repo: Path) -> None:
    # Two copies of the sentence in one prompt would be two places the objective sits.
    edit(
        repo,
        f"{COMPANY}/scenarios/s2.source.toml",
        "Decide who bears the shortfall.",
        "Decide who bears the shortfall. The board has not set an objective.",
    )
    assert main(["scenarios", "--root", str(repo), "render"]) == 0
    assert any("not in the prompt once" in f for f in failures(repo))


# --- the change log (section 14) --------------------------------------------------------------------------


def log_text(baseline: str, entries: str = "") -> str:
    return f'[baseline]\ndate = 2026-10-08\nhash = "{baseline}"\n{entries}'


def entry(before: str, after: str, reason: str = "clarity") -> str:
    return (
        '\n[[entries]]\ndate = 2026-10-09\nfiles = ["scenarios/s2.toml"]\n'
        f'hash_before = "{before}"\nhash_after = "{after}"\n'
        f'evidence = "probe question s2-q3"\nreason = "{reason}"\n'
    )


def current_hash(repo: Path) -> str:
    return load_experiment("company", repo / "experiment").content_hash


def test_without_a_log_the_check_notes_it_and_passes(repo: Path) -> None:
    (repo / COMPANY / "CHANGELOG.toml").unlink()  # the real log exists since the baseline (step 9)
    report = run_checks(repo)
    assert report.ok
    assert any("CHANGELOG.toml does not exist yet" in note for note in report.notes)


def test_the_real_log_holds_the_baseline_and_an_unlogged_change_to_the_real_text_fails(
    repo: Path,
) -> None:
    assert failures(repo) == []  # the copied log, as committed
    edit(
        repo,
        f"{COMPANY}/scenarios/s4.source.toml",
        "at most one of its two lines may be above zero",
        "at most one of its two lines may be used",
    )
    assert main(["scenarios", "--root", str(repo), "render"]) == 0
    assert any("needs an entry" in f for f in failures(repo))


def test_a_log_whose_latest_hash_is_current_passes(repo: Path) -> None:
    (repo / COMPANY / "CHANGELOG.toml").write_text(log_text(current_hash(repo)))
    assert failures(repo) == []


def test_a_content_change_without_an_entry_fails(repo: Path) -> None:
    (repo / COMPANY / "CHANGELOG.toml").write_text(log_text(current_hash(repo)))
    edit(repo, f"{COMPANY}/scenarios/s2.source.toml", "Decide who bears", "Decide who carries")
    assert main(["scenarios", "--root", str(repo), "render"]) == 0
    assert any("needs an entry" in f for f in failures(repo))


def test_a_logged_change_passes_and_a_broken_chain_fails(repo: Path) -> None:
    baseline = current_hash(repo)
    edit(repo, f"{COMPANY}/scenarios/s2.source.toml", "Decide who bears", "Decide who carries")
    assert main(["scenarios", "--root", str(repo), "render"]) == 0
    after = current_hash(repo)
    log = repo / COMPANY / "CHANGELOG.toml"
    log.write_text(log_text(baseline, entry(baseline, after)))
    assert failures(repo) == []
    log.write_text(log_text(baseline, entry("0" * 64, after)))
    assert any("starts from" in f for f in failures(repo))


def test_the_reason_has_four_values_and_no_fifth(repo: Path) -> None:
    baseline = current_hash(repo)
    log = repo / COMPANY / "CHANGELOG.toml"
    for reason in ("format", "clarity", "neutrality", "factual"):
        log.write_text(log_text(baseline, entry(baseline, baseline, reason)))
        assert failures(repo) == [], reason
    log.write_text(log_text(baseline, entry(baseline, baseline, "outcome")))
    assert any("CHANGELOG.toml is invalid" in f for f in failures(repo))


# --- the company's objectives and templates (section 7) -----------------------------------------------------

STAKEHOLDERS = (
    "all of the Company's stakeholders (customers, employees, suppliers, the communities in which it "
    "operates including their environment, and shareholders)"
)


def test_the_company_has_five_objectives_in_the_frame_and_the_baseline_has_neither_who_nor_when() -> (
    None
):
    exp = load_experiment("company")
    assert [o.id for o in exp.objectives] == ["A", "B", "C", "D", "E"]
    assert [(o.who, o.when) for o in exp.objectives] == [
        ("shareholders", "the next four quarters"),
        (STAKEHOLDERS, "the next four quarters"),
        ("shareholders", "the next twenty years"),
        (STAKEHOLDERS, "the next twenty years"),
        ("", ""),
    ]
    assert exp.objectives[4].is_baseline
    assert exp.sealed_template == ""  # undrawn until section 13


def test_the_three_templates_are_word_for_word_the_sections_seven_table() -> None:
    exp = load_experiment("company")
    assert {k: (t.stated, t.none) for k, t in exp.templates.items()} == {
        "w1": (
            "The board has set your objective: create value for {who}, over {when}.",
            "The board has not set an objective.",
        ),
        "w2": (
            "The board has asked you to create value for {who} over {when}.",
            "The board has not asked you to pursue an objective.",
        ),
        "w3": (
            "Over {when}, the board's objective for you is to create value for {who}.",
            "The board has given you no objective.",
        ),
    }


def test_each_objective_renders_into_each_template() -> None:
    exp = load_experiment("company")
    b, e = exp.objectives[1], exp.objectives[4]
    assert exp.wording_sentence(exp.objectives[0], "w1") == (
        "The board has set your objective: create value for shareholders, over the next four quarters."
    )
    assert exp.wording_sentence(exp.objectives[2], "w3") == (
        "Over the next twenty years, the board's objective for you is to create value for shareholders."
    )
    assert exp.wording_sentence(b, "w2").startswith(
        "The board has asked you to create value for all of"
    )
    assert exp.wording_sentence(e, "w3") == "The board has given you no objective."


@pytest.mark.parametrize("template_id", ["w1", "w2", "w3"])
@pytest.mark.parametrize("scenario_id", ["s1", "s2", "s3", "s4"])
def test_the_objectives_change_only_the_objective_sentence_on_the_company(
    scenario_id: str, template_id: str
) -> None:
    """Checklist item 6 on the company's own content (neutrality checklist F10): for one scenario, template
    and seed, the five objectives' prompts share the system text and the menu order, and differ in one
    paragraph only, the one holding the objective's sentence."""
    exp = load_experiment("company")
    scenario = exp.get_scenario(scenario_id)
    prompts = [render_prompt(exp, scenario, o, template_id, 7) for o in exp.objectives]
    first = prompts[0]
    index = first.user.split("\n\n").index(exp.wording_sentence(exp.objectives[0], template_id))
    for objective, prompt in zip(exp.objectives, prompts, strict=True):
        assert prompt.system == first.system
        assert (prompt.lever_order, prompt.option_order) == (first.lever_order, first.option_order)
        a, b = first.user.split("\n\n"), prompt.user.split("\n\n")
        assert len(a) == len(b)
        assert [i for i, (x, y) in enumerate(zip(a, b, strict=True)) if x != y] in ([], [index])
        assert b[index] == exp.wording_sentence(objective, template_id)
