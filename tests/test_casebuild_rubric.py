"""The rubric reader (Phase 5.5 IMPLEMENTATION doc §5.2, K2), on invented rubrics in the committed layout.

Every sentence, name and figure here is a canary: the real rubrics are private, and the reader was fitted to
their layout (key names and types) only.
"""

from __future__ import annotations

import dataclasses

import pytest

from horizon_compact.casebuild.rubric import (
    NOT_OBSERVABLE,
    Rubric,
    RubricError,
    UncertainCall,
    check_rubric_against,
    parse_alternatives,
    parse_rubric,
)

LINES = ("eliminated", "moved_other_plants", "kept_at_plant", "transferred_to_buyer")
CANARIES = (
    "CANARY-EXCERPT-TEXT",
    "CANARY-SOURCE",
    "CANARY-NOTE",
    "CANARY-ABOUT",
    "CANARY-READING",
    "CANARY-ALTERNATIVE",
    "CANARY-TERM",
    "CANARY-LABEL",
)


def line(reading: str) -> str:
    return (
        f'label = "CANARY-LABEL"\nreading = {reading}\nexcerpt_ids = ["e1"]\nnote = "CANARY-NOTE"\n'
    )


def rubric_text(
    *,
    observed: dict[str, float] | None = None,
    choice: str | None = "close",
    uncertain: int = 1,
    extra: str = "",
    drop: str = "",
) -> str:
    """A rubric in the committed layout. ``observed`` gives lines a numeric reading; the rest are "not
    observable". ``choice`` None makes the choice unobservable."""
    observed = observed or {}
    parts = [
        'case = "pre-90"',
        'shape = "S3"',
        'cutoff = "2024-01-01"',
        "scenario_total = 190",
        "",
        "[choice]",
        'key = "plant_decision"',
        f'company_choice = "{choice if choice is not None else NOT_OBSERVABLE}"',
        f"observable = {'true' if choice is not None else 'false'}",
        'excerpt_ids = ["e1", "e2"]',
        'note = "CANARY-NOTE"',
        "",
    ]
    for key in LINES:
        parts += [
            f"[lines.{key}]",
            line(str(observed[key]) if key in observed else '"not observable"'),
        ]
    seen = [k for k in LINES if k in observed]
    gone = [k for k in LINES if k not in observed]
    parts += [
        "[dimensions]",
        "observable = [" + ", ".join(f'"{k}"' for k in (["choice"] if choice else []) + seen) + "]",
        "excluded = [" + ", ".join(f'"{k}"' for k in ([] if choice else ["choice"]) + gone) + "]",
        "",
    ]
    for n in range(1, uncertain + 1):
        parts += [
            "[[uncertain]]",
            f'id = "u{n}"',
            'about = "CANARY-ABOUT"',
            'reading = "CANARY-READING"',
            'alternative = "CANARY-ALTERNATIVE (kept_at_plant = 12)"',
            'excerpt_ids = ["e1"]',
            "",
        ]
    parts += [
        "[foreshadowing]",
        'outcome_terms = ["close", "CANARY-TERM"]',
        "",
        "[[excerpts]]",
        'id = "e1"',
        'source = "CANARY-SOURCE"',
        'text = "CANARY-EXCERPT-TEXT"',
        "",
        "[[excerpts]]",
        'id = "e2"',
        'source = "CANARY-SOURCE"',
        'text = "CANARY-EXCERPT-TEXT"',
        "",
        extra,
    ]
    text = "\n".join(parts)
    return text.replace(drop, "") if drop else text


def parse(text: str) -> Rubric:
    return parse_rubric(text.encode("utf-8"))


def refusal(text: str) -> str:
    with pytest.raises(RubricError) as caught:
        parse(text)
    return str(caught.value)


# --- the three forms ---------------------------------------------------------------------------------------


def test_the_committed_layout_choice_only_with_one_uncertain_call() -> None:
    rubric = parse(rubric_text())
    assert rubric.case == "pre-90" and rubric.shape == "S3" and rubric.scenario_total == 190
    assert rubric.choice_key == "plant_decision" and rubric.company_choice == "close"
    assert rubric.amounts == {}
    assert dict(rubric.lines) == dict.fromkeys(LINES)
    assert rubric.observable == ("choice",) and rubric.excluded == LINES
    assert rubric.uncertain == (UncertainCall("u1"),)


def test_a_choice_and_observable_lines() -> None:
    rubric = parse(rubric_text(observed={"eliminated": 120, "kept_at_plant": 70.5}))
    assert rubric.amounts == {"eliminated": 120.0, "kept_at_plant": 70.5}
    assert rubric.observable == ("choice", "eliminated", "kept_at_plant")
    assert rubric.excluded == ("moved_other_plants", "transferred_to_buyer")
    assert list(rubric.lines) == list(LINES)  # the rubric's order


def test_an_unobservable_choice_is_none_and_excluded() -> None:
    rubric = parse(rubric_text(choice=None, observed={"eliminated": 10}))
    assert rubric.company_choice is None
    assert "choice" in rubric.excluded and "choice" not in rubric.observable


def test_a_rubric_with_no_uncertain_call_has_none() -> None:
    assert parse(rubric_text(uncertain=0)).uncertain == ()


def test_each_uncertain_call_is_kept_by_id_in_the_rubrics_order() -> None:
    assert parse(rubric_text(uncertain=3)).uncertain == tuple(
        UncertainCall(f"u{n}") for n in (1, 2, 3)
    )


def test_excerpts_terms_and_prose_are_dropped() -> None:
    rubric = parse(rubric_text(observed={"eliminated": 5}))
    shown = repr(rubric) + repr(dataclasses.asdict(rubric))
    for canary in CANARIES:
        assert canary not in shown
    assert "kept_at_plant = 12" not in shown  # the alternative's prose, whatever it holds


# --- refusals ----------------------------------------------------------------------------------------------


def test_invalid_toml_and_bytes_that_are_not_text_are_refused() -> None:
    assert "not valid TOML" in refusal("case = ")
    with pytest.raises(RubricError, match="not valid TOML"):
        parse_rubric(b"\xff\xfe")


def test_an_unknown_or_missing_key_is_refused_at_every_level() -> None:
    assert "keys this form does not: ['surprise']" in refusal(rubric_text(extra="surprise = 1\n"))
    assert "lacks keys: ['cutoff']" in refusal(rubric_text(drop='cutoff = "2024-01-01"'))
    assert "uncertain[0] lacks keys: ['alternative']" in refusal(
        rubric_text(drop='alternative = "CANARY-ALTERNATIVE (kept_at_plant = 12)"')
    )
    assert "choice has keys this form does not" in refusal(
        rubric_text().replace(
            'note = "CANARY-NOTE"\n\n[lines', 'note = "CANARY-NOTE"\nextra = 1\n\n[lines', 1
        )
    )


def test_a_line_reading_must_be_not_observable_or_a_non_negative_number() -> None:
    assert "lines.eliminated.reading is neither" in refusal(
        rubric_text().replace('reading = "not observable"', 'reading = "unknown"', 1)
    )
    assert "negative or not finite" in refusal(rubric_text(observed={"eliminated": -1}))
    assert "negative or not finite" in refusal(rubric_text(observed={"eliminated": float("inf")}))
    assert "is neither" in refusal(
        rubric_text(observed={"eliminated": 1}).replace("reading = 1", "reading = true", 1)
    )


def test_the_choice_must_agree_with_its_observable_flag() -> None:
    flipped = rubric_text().replace("observable = true", "observable = false", 1)
    assert "observable is false but company_choice is not 'not observable'" in refusal(flipped)
    said = rubric_text(choice=None).replace("observable = false", "observable = true", 1)
    assert "observable is true but company_choice is 'not observable'" in refusal(said)
    assert "choice.observable is not true or false" in refusal(
        rubric_text().replace("observable = true", 'observable = "yes"', 1)
    )


def test_the_dimension_lists_must_match_what_is_observable() -> None:
    wrong = rubric_text().replace(
        'observable = ["choice"]', 'observable = ["choice", "eliminated"]', 1
    )
    assert "dimensions.observable and dimensions.excluded do not match" in refusal(wrong)
    assert "dimensions.excluded repeats a name" in refusal(
        rubric_text().replace('"kept_at_plant", "transferred', '"eliminated", "transferred', 1)
    )


def test_excerpts_must_be_unique_and_every_citation_must_exist() -> None:
    assert "two excerpts share an id" in refusal(rubric_text().replace('id = "e2"', 'id = "e1"', 1))
    assert "cites excerpts the rubric does not hold: ['e9']" in refusal(
        rubric_text().replace('excerpt_ids = ["e1", "e2"]', 'excerpt_ids = ["e9"]', 1)
    )
    assert "cites no excerpt" in refusal(
        rubric_text().replace('excerpt_ids = ["e1", "e2"]', "excerpt_ids = []", 1)
    )


def test_an_uncertain_call_needs_an_id_prose_and_a_unique_id() -> None:
    assert "uncertain[0].alternative is not a non-empty string" in refusal(
        rubric_text().replace(
            'alternative = "CANARY-ALTERNATIVE (kept_at_plant = 12)"', 'alternative = ""', 1
        )
    )
    assert "two uncertain calls share an id" in refusal(
        rubric_text(uncertain=2).replace('id = "u2"', 'id = "u1"', 1)
    )


def test_the_totals_and_terms_are_checked() -> None:
    assert "scenario_total is not a positive whole number" in refusal(
        rubric_text().replace("scenario_total = 190", "scenario_total = 190.5", 1)
    )
    assert "scenario_total is not a positive whole number" in refusal(
        rubric_text().replace("scenario_total = 190", "scenario_total = true", 1)
    )
    assert "outcome_terms holds something that is not a non-empty string" in refusal(
        rubric_text().replace('outcome_terms = ["close"', 'outcome_terms = [1, "close"', 1)
    )


def test_every_reason_is_named_at_once_and_none_carries_a_value() -> None:
    message = refusal(
        rubric_text(extra="surprise = 1\n").replace('cutoff = "2024-01-01"', "cutoff = 3", 1)
    )
    assert "keys this form does not" in message and "cutoff is not a non-empty string" in message
    for canary in CANARIES:
        assert canary not in message


# --- the rubric against its scenario ------------------------------------------------------------------------


def fits(rubric: Rubric, **changes: object) -> list[str]:
    arguments: dict[str, object] = {
        "label": "pre-90",
        "scenario_id": "s3",
        "scenario_total": 190,
        "choice_key": "plant_decision",
        "options": ["close", "retool", "sell"],
        "lines": list(LINES),
    }
    arguments.update(changes)
    return check_rubric_against(rubric, **arguments)  # type: ignore[arg-type]


def test_a_rubric_that_fits_its_scenario_has_no_reason() -> None:
    assert fits(parse(rubric_text())) == []


def test_each_difference_from_the_scenario_is_named() -> None:
    rubric = parse(rubric_text())
    assert fits(rubric, label="pre-91") == ["the rubric is for another case than the one asked for"]
    assert fits(rubric, scenario_id="s2") == ["the rubric's shape is not the scenario's (s2)"]
    assert fits(rubric, scenario_total=191) == [
        "the rubric's scenario_total is not the scenario's (191)"
    ]
    assert fits(rubric, choice_key="other") == ["the rubric's choice key is not the scenario's"]
    assert fits(rubric, choice_key=None) == ["the rubric's choice key is not the scenario's"]
    assert "not one of the scenario's options" in fits(rubric, options=["retool", "sell"])[0]
    assert "the rubric's lines are not the scenario's" in fits(rubric, lines=list(LINES[:3]))[0]


# --- alternatives.toml: the uncertain calls' alternatives, transcribed into numbers -------------------------


def alternatives(*entries: str, case: str = "pre-90") -> bytes:
    return (f'case = "{case}"\n' + "".join(entries)).encode("utf-8")


def entry(call: str = "u1", lines: str = "eliminated = 150, moved_other_plants = 0") -> str:
    return f'\n[[alternative]]\ncall = "{call}"\nlines = {{ {lines} }}\n'


def test_a_transcribed_alternative_reads_as_its_call_and_its_lines() -> None:
    [found] = parse_alternatives(alternatives(entry()), parse(rubric_text()))
    assert found.call == "u1"
    assert found.amounts == {"eliminated": 150.0, "moved_other_plants": 0.0}


def test_two_calls_each_transcribed_once_read_in_order() -> None:
    rubric = parse(rubric_text(uncertain=2))
    found = parse_alternatives(alternatives(entry("u2"), entry("u1")), rubric)
    assert [a.call for a in found] == ["u2", "u1"]


def test_an_alternatives_file_that_does_not_fit_its_rubric_is_refused_with_every_reason() -> None:
    data = alternatives(
        entry("u9"),
        entry("u1", 'eliminated = -3, nowhere = 1, kept_at_plant = "not observable"'),
        entry("u1", "kept_at_plant = 2"),
        '\n[[alternative]]\ncall = "u1"\nlines = {}\nnote = "CANARY-NOTE"\n',
        case="pre-91",
    )
    with pytest.raises(RubricError) as caught:
        parse_alternatives(data, parse(rubric_text()))
    message = str(caught.value)
    for reason in (
        "for another case than the rubric",
        "alternative[0] names a call the rubric does not hold",
        "alternative[1].lines.eliminated is negative or not finite",
        "alternative[1].lines names a line the rubric does not list",
        "alternative[1].lines.kept_at_plant is not a number",
        "alternative[2] repeats a call",
        "alternative[3] has keys this form does not: ['note']",
        "alternative[3] makes no line observable",
    ):
        assert reason in message
    assert "CANARY" not in message


def test_an_alternatives_file_with_no_alternative_is_refused() -> None:
    with pytest.raises(RubricError, match="transcribes no alternative"):
        parse_alternatives(alternatives(), parse(rubric_text()))
