"""The extraction request (IMPLEMENTATION §4.7): one per section, the template's fixed instruction and the
admitted text the section map assigns it, and **nothing else**.

This is where "never told the outcome" is made structural. ``ExtractionRequest`` has no field for anything
but those two inputs, so no code path can carry the outcome, a rubric, a case label or a selection reason to
the model; and ``tests/test_architecture.py`` checks that nothing in ``casebuild/`` imports the rubric or any
case-outcome type.

The instructions below are the template's fixed wording, written for protocol §12.6's seven-section template.
They are run code, not frozen, but they decide what the model is asked, so their hash goes into ``build.json``
(``instructions_sha256``) and they are for review before the first case. Sections 4 and 5's figures come from
XBRL with no model; section 5's request is for acquisitions only. Section 7 comes from the scenario shape.

In this half the request runs only against a fake provider. The model, its route and its cost are the search
half's decision.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from horizon_compact.casebuild.sections import SectionInputs, TextPart
from horizon_compact.providers.base import (
    ModelRoute,
    TextProvider,
    TextRequest,
    Usage,
    text_prompt_sha256,
)

COMMON = (
    "You are preparing one section of a background document about a company, from the company's own public "
    "filings. Use only the text you are given. Do not add anything from memory or from any other source, and do "
    "not guess: if the text does not say something, leave it out. Report figures exactly as the text gives "
    "them. Write plain text in short paragraphs, with no headings, lists or markup. Describe; do not judge, "
    "and do not say what the company should do."
)
SECTION_INSTRUCTIONS: dict[int, str] = {
    1: "Section: overview. Say what the company makes and sells, at the level of a product category, and how "
    "it sells it.",
    2: "Section: segments and facilities. Give each segment with its revenue and operating income where the "
    "text gives them. Give facilities by region and function (for example manufacturing, distribution, "
    "offices), never by town or street.",
    3: "Section: workforce. Give headcount by function where the text gives it, pay where it gives it, and "
    "representation (for example the share of employees covered by union agreements).",
    5: "Section: capital allocation. From this text only, list the acquisitions the company made in the last "
    "three fiscal years, each by what was bought (a product category) and its price where the text gives it. "
    "Say nothing about capital spending, research and development, dividends or share repurchases.",
    6: "Section: the situation at the latest filing. Say what the text says about demand, costs, and any "
    "facility, program or restructuring it describes. Report each current report's event as that report "
    "states it, with the report's date, in date order.",
}
# Sections that are asked of a model. 4 is figures only; 5 is figures plus this request for acquisitions.
MODEL_SECTIONS = tuple(sorted(SECTION_INSTRUCTIONS))
DEFAULT_MAX_TOKENS = 4096


class ExtractionError(Exception):
    """A provider call failed, was cut short, or returned nothing."""


@dataclass(frozen=True)
class ExtractionRequest:
    """The two inputs and nothing else. A field added here is a way for hindsight to reach the model."""

    section: int
    instruction: str
    text: str


def instructions_sha256() -> str:
    canonical = json.dumps(
        {
            "common": COMMON,
            "sections": {str(k): v for k, v in sorted(SECTION_INSTRUCTIONS.items())},
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _joined(parts: Sequence[TextPart]) -> str:
    return "\n\n".join(f"[{part.label}]\n{part.text}" for part in parts)


def build_requests(inputs: SectionInputs) -> list[ExtractionRequest]:
    """One request per model-read section the shape needs, in section order."""
    requests: list[ExtractionRequest] = []
    for section in MODEL_SECTIONS:
        parts = inputs.parts.get(section)
        if not parts:
            continue
        requests.append(
            ExtractionRequest(
                section=section,
                instruction=f"{COMMON}\n\n{SECTION_INSTRUCTIONS[section]}",
                text=_joined(parts),
            )
        )
    return requests


def to_text_request(
    request: ExtractionRequest, route: ModelRoute, *, max_tokens: int = DEFAULT_MAX_TOKENS
) -> TextRequest:
    return TextRequest(
        route=route, system=request.instruction, user=request.text, max_tokens=max_tokens
    )


@dataclass(frozen=True)
class ExtractedSection:
    section: int
    text: str
    prompt_sha256: str
    model_id: str
    usage: Usage


def run_extraction(
    provider: TextProvider,
    route: ModelRoute,
    requests: Sequence[ExtractionRequest],
    *,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> dict[int, ExtractedSection]:
    """Run each request once. Any failure stops the run: nothing is retried or filled in."""
    done: dict[int, ExtractedSection] = {}
    for request in requests:
        text_request = to_text_request(request, route, max_tokens=max_tokens)
        decision = provider.decide_text(text_request)
        if decision.status != "ok":
            error = decision.error or {}
            raise ExtractionError(
                f"section {request.section}: the provider call failed "
                f"({error.get('code', 'unknown')}: {error.get('message', '')[:300]})"
            )
        if decision.stop_reason == "max_tokens":
            raise ExtractionError(
                f"section {request.section}: the reply was cut off at the token limit"
            )
        text = "\n".join(block.strip() for block in decision.text_blocks if block.strip())
        if not text:
            raise ExtractionError(f"section {request.section}: the reply had no text")
        done[request.section] = ExtractedSection(
            section=request.section,
            text=text,
            prompt_sha256=text_prompt_sha256(text_request),
            model_id=decision.provenance.model_id,
            usage=decision.usage,
        )
    return done


def request_record(requests: Sequence[ExtractionRequest]) -> Mapping[str, object]:
    return {
        "instructions_sha256": instructions_sha256(),
        "sections": [r.section for r in requests],
        "characters": {str(r.section): len(r.text) for r in requests},
    }
