"""The reviewed-flags file (Phase 5 code half, build step 6)."""

from __future__ import annotations

import json

import pytest

from horizon_compact.casebuild.review import (
    FLAGS_VERSION,
    ReviewError,
    apply_decisions,
    flag_refs,
    match_reviews,
    parse_reviewed,
    template_text,
)
from horizon_compact.casebuild.transform import Flag

SECTIONS = {
    1: "It has 35 countries and 12 plants.\nNothing else here.",
    3: "Staff of 40 in 2 teams.",
}
FLAGS = {
    1: [Flag("unclassified number", 1, "35"), Flag("unclassified number", 1, "12")],
    3: [Flag("pay per head not checked: several figures on one line", 1, "")],
}


def entries(**changes: object) -> list[dict[str, object]]:
    done = []
    for ref in flag_refs(SECTIONS, FLAGS):
        entry: dict[str, object] = {
            **ref.record(),
            "decision": "keep",
            "reason": "a count of places, left as written",
            "replacement": None,
        }
        done.append(entry)
    return done


def reviewed(items: list[dict[str, object]]):  # type: ignore[no-untyped-def]
    return parse_reviewed(json.dumps({"flags_version": FLAGS_VERSION, "entries": items}))


def test_every_distinct_flag_becomes_one_reference_in_section_and_line_order() -> None:
    refs = flag_refs(SECTIONS, FLAGS)
    assert [(r.section, r.line, r.text) for r in refs] == [(1, 1, "12"), (1, 1, "35"), (3, 1, "")]
    twice = {1: [Flag("k", 1, "35"), Flag("k", 1, "35")]}
    assert len(flag_refs(SECTIONS, twice)) == 1


def test_a_flag_on_a_line_the_section_lacks_is_an_error() -> None:
    with pytest.raises(ReviewError, match="line 9"):
        flag_refs(SECTIONS, {1: [Flag("k", 9, "x")]})


def test_the_template_lists_every_flag_with_the_decision_blank_and_cannot_be_used_as_is() -> None:
    template = json.loads(template_text(flag_refs(SECTIONS, FLAGS)))
    assert len(template["entries"]) == 3
    assert all(e["decision"] == "" and e["reason"] == "" for e in template["entries"])
    with pytest.raises(ReviewError, match="malformed"):
        parse_reviewed(json.dumps(template))


def test_a_decision_for_every_flag_passes_and_comes_back_in_flag_order() -> None:
    refs = flag_refs(SECTIONS, FLAGS)
    matched = match_reviews(refs, reviewed(list(reversed(entries()))))
    assert [e.key for e in matched] == [r.key for r in refs]


def test_a_flag_with_no_entry_is_refused_and_named() -> None:
    refs = flag_refs(SECTIONS, FLAGS)
    with pytest.raises(ReviewError, match=r"no decision for section 1, line 1.*'35'"):
        match_reviews(refs, reviewed(entries()[:1] + entries()[2:]))


def test_an_entry_for_a_flag_that_is_gone_is_stale() -> None:
    refs = flag_refs(SECTIONS, {1: FLAGS[1]})
    with pytest.raises(ReviewError, match="stale entry"):
        match_reviews(refs, reviewed(entries()))


def test_an_entry_does_not_survive_a_change_to_its_line() -> None:
    old = entries()
    changed = {**SECTIONS, 1: "It has 35 countries and 12 sites.\nNothing else here."}
    with pytest.raises(ReviewError) as caught:
        match_reviews(flag_refs(changed, FLAGS), reviewed(old))
    assert "stale entry" in str(caught.value) and "no decision" in str(caught.value)


def test_two_entries_for_one_flag_are_refused() -> None:
    refs = flag_refs(SECTIONS, FLAGS)
    with pytest.raises(ReviewError, match="2 entries for one flag"):
        match_reviews(refs, reviewed(entries() + entries()[:1]))


def test_an_entry_whose_text_was_altered_is_refused() -> None:
    items = entries()
    items[0]["text"] = "13"
    with pytest.raises(ReviewError, match="does not match its text_sha256"):
        match_reviews(flag_refs(SECTIONS, FLAGS), reviewed(items))


def test_an_edit_needs_a_one_line_replacement_and_only_an_edit_takes_one() -> None:
    refs = flag_refs(SECTIONS, FLAGS)
    items = entries()
    items[0]["decision"] = "edit"
    with pytest.raises(ReviewError, match="edit needs a one-line replacement"):
        match_reviews(refs, reviewed(items))
    items[0]["replacement"] = "a\nb"
    with pytest.raises(ReviewError, match="edit needs a one-line replacement"):
        match_reviews(refs, reviewed(items))
    items = entries()
    items[0]["replacement"] = "x"
    with pytest.raises(ReviewError, match="only an edit takes a replacement"):
        match_reviews(refs, reviewed(items))


def test_a_flag_with_no_text_can_only_be_kept() -> None:
    items = entries()
    items[2]["decision"] = "remove"
    with pytest.raises(ReviewError, match="no flagged text can only be kept"):
        match_reviews(flag_refs(SECTIONS, FLAGS), reviewed(items))


def test_a_reason_is_required_and_every_problem_is_listed_at_once() -> None:
    items = entries()
    items[0]["reason"] = ""
    with pytest.raises(ReviewError, match="reason"):
        reviewed(items)
    refs = flag_refs(SECTIONS, FLAGS)
    with pytest.raises(ReviewError, match="2 problem"):
        match_reviews(refs, reviewed(entries()[:1]))


def test_edit_and_remove_change_only_the_flagged_text_on_its_line() -> None:
    refs = flag_refs(SECTIONS, FLAGS)
    items = entries()
    for item in items:
        if item["text"] == "12":
            item.update(decision="edit", replacement="a dozen")
        if item["text"] == "35":
            item.update(decision="remove")
    final = apply_decisions(SECTIONS, match_reviews(refs, reviewed(items)))
    assert final[1] == "It has  countries and a dozen plants.\nNothing else here."
    assert final[3] == SECTIONS[3]


def test_a_flagged_text_that_is_not_once_on_its_line_cannot_be_edited() -> None:
    sections = {1: "Twelve 12 and 12 again."}
    flags = {1: [Flag("k", 1, "12")]}
    items = [
        {
            **flag_refs(sections, flags)[0].record(),
            "decision": "remove",
            "reason": "r",
            "replacement": None,
        }
    ]
    with pytest.raises(ReviewError, match="occurs 2 times"):
        apply_decisions(sections, match_reviews(flag_refs(sections, flags), reviewed(items)))


def test_a_flag_whose_text_the_transform_rewrote_can_only_be_kept_and_the_error_says_so() -> None:
    """Opus review of step 6: "fiscal 2025" is flagged, then rewritten, so edit and remove find nothing."""
    sections = {1: "It grew in fiscal year N-1."}
    flags = {1: [Flag("fiscal-year convention assumed", 1, "fiscal 2025")]}
    refs = flag_refs(sections, flags)
    for decision in ("remove", "edit"):
        item = {
            **refs[0].record(),
            "decision": decision,
            "reason": "r",
            "replacement": "x" if decision == "edit" else None,
        }
        with pytest.raises(ReviewError, match=r"transform rewrote it.*only be kept"):
            apply_decisions(sections, match_reviews(refs, reviewed([item])))
    kept = {**refs[0].record(), "decision": "keep", "reason": "r", "replacement": None}
    assert apply_decisions(sections, match_reviews(refs, reviewed([kept]))) == sections


def test_a_wrong_version_or_broken_file_is_refused() -> None:
    with pytest.raises(ReviewError, match="flags_version"):
        parse_reviewed(json.dumps({"flags_version": 99, "entries": []}))
    with pytest.raises(ReviewError, match="not valid JSON"):
        parse_reviewed("{")
