"""The call plan, the neutral prompt and the tool (Phase 0.5 IMPLEMENTATION doc sections 11.2-11.5).

The prompt is outside the experiment's subject entirely (planning/05 section 2): a unit conversion with an
exact answer. A smoke call must show nothing about how any objective pushes a decision.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from horizon_compact.providers.base import ModelRoute, ToolSpec

SYSTEM = "You are a careful assistant completing a short arithmetic task."
USER = (
    "A walking trail is 12 miles long. Convert its length to kilometers, using 1 mile = 1.609344 "
    "kilometers, and round to two decimal places. Record your answer by calling the record_conversion "
    "tool exactly once. Do not give the answer in text."
)
TOOL = ToolSpec(
    name="record_conversion",
    description="Records the result of a unit conversion.",
    input_schema={
        "type": "object",
        "properties": {
            "kilometers": {
                "type": "number",
                "description": "The converted length in kilometers, rounded to two decimal places.",
            },
            "unit_system": {
                "type": "string",
                "enum": ["metric", "imperial"],
                "description": "The unit system of the converted value.",
            },
            "note": {
                "type": "string",
                "description": "One sentence describing how the conversion was done.",
            },
        },
        "required": ["kilometers", "unit_system", "note"],
        "additionalProperties": False,
    },
)
EXPECTED_KILOMETERS = 19.31  # 12 x 1.609344 = 19.312128
EXPECTED_TOLERANCE = 0.01

# Words from the experiment's subject. A test fails if any appears in the prompt or the tool.
SUBJECT_VOCABULARY = (
    "company",
    "shareholder",
    "stakeholder",
    "employee",
    "worker",
    "invest",
    "capital",
    "objective",
    "profit",
    "budget",
    "allocate",
    "quarter",
    "horizon",
    "board",
)

# Twelve records, ever, across Phases 0.5 and 1: nine planned in 0.5, call 10 added by Phase 1, two spare.
MAX_RECORDS = 12

ADAPTIVE_HIGH: Mapping[str, Any] = {
    "thinking": {"type": "adaptive"},
    "output_config": {"effort": "high"},
}
BETWEEN_TOOLS: Mapping[str, Any] = {"thinking": {"type": "between_tools"}}


@dataclass(frozen=True)
class SmokeCall:
    number: int
    name: str
    route: ModelRoute
    max_tokens: int
    additional_fields: Mapping[str, Any] | None = None
    conditional: bool = False
    additional_response_fields: Sequence[str] | None = None


SONNET46 = "anthropic.claude-sonnet-4-6"
SONNET55 = "anthropic.claude-sonnet-5-5"
NOVA_PRO = "amazon.nova-pro-v1:0"
NOVA_LITE = "amazon.nova-lite-v1:0"
GPT_OSS = "openai.gpt-oss-120b-1:0"

PLAN: tuple[SmokeCall, ...] = (
    SmokeCall(
        1,
        "sonnet46-profile-off",
        ModelRoute(
            "sonnet-4-6",
            SONNET46,
            "application_profile",
            inference_profile="horizon-compact-sonnet-4-6",
        ),
        1024,
    ),
    SmokeCall(
        2,
        "novapro-profile",
        ModelRoute(
            "nova-pro",
            NOVA_PRO,
            "application_profile",
            inference_profile="horizon-compact-nova-pro",
        ),
        1024,
    ),
    SmokeCall(
        3,
        "sonnet46-geo-off",
        ModelRoute(
            "sonnet-4-6", SONNET46, "geo_profile", invoke_id="us.anthropic.claude-sonnet-4-6"
        ),
        1024,
    ),
    SmokeCall(
        4,
        "sonnet46-profile-adaptive",
        ModelRoute(
            "sonnet-4-6",
            SONNET46,
            "application_profile",
            inference_profile="horizon-compact-sonnet-4-6",
        ),
        4096,
        ADAPTIVE_HIGH,
    ),
    SmokeCall(
        5, "novapro-direct", ModelRoute("nova-pro", NOVA_PRO, "in_region", invoke_id=NOVA_PRO), 1024
    ),
    SmokeCall(
        6, "novalite", ModelRoute("nova-lite", NOVA_LITE, "in_region", invoke_id=NOVA_LITE), 1024
    ),
    SmokeCall(
        7, "gptoss120b", ModelRoute("gpt-oss-120b", GPT_OSS, "in_region", invoke_id=GPT_OSS), 2048
    ),
    SmokeCall(
        8,
        "sonnet55-default",
        ModelRoute(
            "sonnet-5-5", SONNET55, "geo_profile", invoke_id="us.anthropic.claude-sonnet-5-5"
        ),
        4096,
        conditional=True,
    ),
    SmokeCall(
        9,
        "sonnet55-between-tools",
        ModelRoute(
            "sonnet-5-5", SONNET55, "geo_profile", invoke_id="us.anthropic.claude-sonnet-5-5"
        ),
        4096,
        BETWEEN_TOOLS,
        conditional=True,
    ),
    # Phase 1 section 6.4: the one place `stop_details` is asked for, so every sweep request stays identical
    # apart from its shuffle. On the route models.toml names (application profile until decision 3 says
    # otherwise), thinking off, the neutral prompt. If Bedrock rejects the field, that is the finding.
    SmokeCall(
        10,
        "sonnet46-stop-details",
        ModelRoute(
            "sonnet-4-6",
            SONNET46,
            "application_profile",
            inference_profile="horizon-compact-sonnet-4-6",
        ),
        1024,
        additional_response_fields=("/stop_details",),
    ),
)

# AWS Price List, publication 2026-10-03, us-east-1, standard tier, USD per million tokens (input, output).
# The Sonnet rows are the US geo route (planning/03 section 2.1). The bill, not this table, is the
# phase's spend.
PRICE_SOURCE = "AWS Price List publication 2026-10-03, us-east-1, standard tier"
PRICES: Mapping[str, tuple[float, float]] = {
    SONNET46: (3.30, 16.50),
    SONNET55: (2.20, 11.00),
    NOVA_PRO: (0.80, 3.20),
    NOVA_LITE: (0.06, 0.24),
    GPT_OSS: (0.15, 0.60),
}


def find_call(name: str) -> SmokeCall | None:
    return next((call for call in PLAN if call.name == name), None)
