"""The extraction request on a fake provider (Phase 5 code half, build step 5, §4.7)."""

from __future__ import annotations

import dataclasses
import json
from datetime import date
from pathlib import Path

import pytest

from edgar_helpers import CANARY_CIK, FACTS_URL, accession, annual, facts_file, world
from horizon_compact.casebuild import extract
from horizon_compact.casebuild.documents import build_document_set
from horizon_compact.casebuild.extract import (
    COMMON,
    SECTION_INSTRUCTIONS,
    ExtractionError,
    ExtractionRequest,
    build_requests,
    instructions_sha256,
    request_record,
    run_extraction,
    to_text_request,
)
from horizon_compact.casebuild.figures import extract_figures, render_section
from horizon_compact.casebuild.sections import SectionInputs, TextPart, build_section_inputs
from horizon_compact.providers.base import (
    ModelRoute,
    Provenance,
    RawDecision,
    TextRequest,
    Usage,
    text_prompt_sha256,
)

ROUTE = ModelRoute(key="fake", model_id="fake-model", route_kind="in_region")
FACTS = json.dumps(
    facts_file(
        {
            "Revenues": [
                annual(2024, 800_000_000, "2024-03-04"),
                annual(2025, 900_000_000, "2025-03-03"),
                annual(2026, 1_000_000_000, "2026-03-02"),
            ],
            "PaymentsToAcquirePropertyPlantAndEquipment": [annual(2026, 50_000_000, "2026-03-02")],
        }
    )
).encode()
PROVENANCE = Provenance(
    provider="fake", api="fake", model_id="fake-model", invoke_id="", route_kind="in_region",
    inference_profile=None, region="none", thinking="off", effort="", temperature="default", max_tokens=1,
    prompt_sha256="", started_at="t", finished_at="t", latency_ms=1,
)  # fmt: skip


class FakeTextProvider:
    """Serves scripted replies; records every request so a test can read exactly what was sent."""

    name = "fake"

    def __init__(self, reply: RawDecision | None = None) -> None:
        self.requests: list[TextRequest] = []
        self._reply = reply

    def text_request_body(self, request: TextRequest) -> dict[str, object]:
        return {}

    def decide_text(self, request: TextRequest) -> RawDecision:
        self.requests.append(request)
        if self._reply is not None:
            return self._reply
        return ok(f"summary of section {len(self.requests)}")


def ok(*blocks: str, stop: str = "end_turn") -> RawDecision:
    return RawDecision(
        status="ok", provenance=PROVENANCE, text_blocks=list(blocks), stop_reason=stop,
        usage=Usage(input_tokens=10, output_tokens=5),
    )  # fmt: skip


def _inputs(tmp_path: Path, shape: str = "S3") -> SectionInputs:
    client, _ = world(tmp_path, {FACTS_URL: FACTS})
    return build_section_inputs(
        build_document_set(client, CANARY_CIK, date(2026, 6, 15)), shape=shape
    )


def test_the_request_has_two_inputs_and_a_section_number_and_no_other_field() -> None:
    assert [f.name for f in dataclasses.fields(ExtractionRequest)] == [
        "section",
        "instruction",
        "text",
    ]


def test_one_request_per_model_read_section_the_shape_needs(tmp_path: Path) -> None:
    assert [r.section for r in build_requests(_inputs(tmp_path, "S3"))] == [1, 2, 3, 5, 6]
    assert [r.section for r in build_requests(_inputs(tmp_path / "s4", "S4"))] == [
        1,
        5,
        6,
    ]  # 4 is figures only


def test_a_request_carries_the_fixed_instruction_and_only_the_admitted_text(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    request = next(r for r in build_requests(inputs) if r.section == 2)
    assert request.instruction == f"{COMMON}\n\n{SECTION_INSTRUCTIONS[2]}"
    assert "One plant in the Midwest" in request.text
    assert "Cages revenue was 900" in request.text  # the segment note
    assert "Demand for cages softened" not in request.text  # Item 7 is not section 2's
    assert request.text == "\n\n".join(f"[{p.label}]\n{p.text}" for p in inputs.parts[2])


def test_section_6_carries_the_current_reports_and_nothing_after_the_cutoff(tmp_path: Path) -> None:
    request = next(r for r in build_requests(_inputs(tmp_path)) if r.section == 6)
    assert "Quarterly demand fell" in request.text
    assert "report 4" in request.text and "closure release" in request.text
    assert (
        accession(7) not in request.text and accession(8) not in request.text
    )  # cut-off day and after


def test_the_instruction_does_not_name_an_outcome_a_case_or_a_selection_reason() -> None:
    words = " ".join([COMMON, *SECTION_INSTRUCTIONS.values()]).lower()
    for forbidden in (
        "clos",
        "layoff",
        "rubric",
        "outcome",
        "later",
        "subsequent",
        "after the",
        "chose",
        "decided",
    ):
        assert forbidden not in words, forbidden


def test_the_text_request_sent_to_the_provider_is_exactly_system_and_user() -> None:
    request = ExtractionRequest(section=1, instruction="I", text="T")
    sent = to_text_request(request, ROUTE, max_tokens=99)
    assert (sent.system, sent.user, sent.max_tokens, sent.route) == ("I", "T", 99, ROUTE)


def test_running_it_on_a_fake_provider_returns_each_sections_text_and_provenance(
    tmp_path: Path,
) -> None:
    requests = build_requests(_inputs(tmp_path))
    provider = FakeTextProvider()
    done = run_extraction(provider, ROUTE, requests)
    assert sorted(done) == [r.section for r in requests]
    assert done[1].text == "summary of section 1"
    assert done[1].model_id == "fake-model"
    assert done[1].prompt_sha256 == text_prompt_sha256(provider.requests[0])
    assert [r.system for r in provider.requests] == [r.instruction for r in requests]


def test_a_failed_call_stops_the_run_and_nothing_is_filled_in(tmp_path: Path) -> None:
    bad = RawDecision(
        status="api_error", provenance=PROVENANCE, error={"type": "Throttle", "message": "x"}
    )
    provider = FakeTextProvider(bad)
    with pytest.raises(ExtractionError, match="call failed"):
        run_extraction(provider, ROUTE, build_requests(_inputs(tmp_path)))
    assert len(provider.requests) == 1  # no retry, no next section


def test_a_reply_cut_off_at_the_token_limit_is_refused() -> None:
    with pytest.raises(ExtractionError, match="cut off"):
        run_extraction(
            FakeTextProvider(ok("partial", stop="max_tokens")),
            ROUTE,
            [ExtractionRequest(1, "I", "T")],
        )


def test_an_empty_reply_is_refused() -> None:
    with pytest.raises(ExtractionError, match="no text"):
        run_extraction(FakeTextProvider(ok("  ", "")), ROUTE, [ExtractionRequest(1, "I", "T")])


def test_the_instructions_hash_is_recorded_and_moves_when_the_wording_does(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = instructions_sha256()
    assert len(before) == 64
    record = request_record(build_requests(_inputs(tmp_path)))
    assert record["instructions_sha256"] == before
    assert record["sections"] == [1, 2, 3, 5, 6]
    monkeypatch.setitem(extract.SECTION_INSTRUCTIONS, 1, "changed")
    assert instructions_sha256() != before


# --- section 4 and 5's figures, by code -------------------------------------------------------------------


def test_section_4_is_rendered_from_the_figures_with_years_named_relative_to_the_latest() -> None:
    table = extract_figures(json.loads(FACTS), date(2026, 6, 15))
    text = render_section(table, 4)
    assert text == (
        "Revenue\n"
        "  fiscal year N: $1,000.0 million\n"
        "  fiscal year N-1: $900.0 million\n"
        "  fiscal year N-2: $800.0 million"
    )


def test_section_5_lists_only_its_own_lines_and_marks_a_missing_year() -> None:
    table = extract_figures(json.loads(FACTS), date(2026, 6, 15))
    text = render_section(table, 5)
    assert text.startswith(
        "Capital spending\n  fiscal year N: $50.0 million\n  fiscal year N-1: not available"
    )
    assert "Revenue" not in text


def test_text_parts_are_labelled_by_their_source() -> None:
    inputs = SectionInputs(
        shape="S1",
        parts={1: [TextPart("annual report A, Item 1", "text one")]},
        figures=extract_figures(json.loads(FACTS), date(2026, 6, 15)),
    )
    assert build_requests(inputs)[0].text == "[annual report A, Item 1]\ntext one"
