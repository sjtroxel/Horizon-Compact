"""The seam's types: a request, a raw result and the provenance stamped on it.

Sized to what exists before there is a sweep (Phase 0.5 IMPLEMENTATION doc section 10). There is
deliberately no sampling field on ``DecisionRequest``: sampling parameters are never set, so none can be sent
(planning/07 2.3). Validation of a decision is not here; it happens after this seam, in one place for every
model (Phase 1).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

RouteKind = Literal["in_region", "geo_profile", "application_profile"]


@dataclass(frozen=True)
class ToolSpec:
    """The one tool a request offers. Its input schema is the decision."""

    name: str
    description: str
    input_schema: Mapping[str, Any]


@dataclass(frozen=True)
class ModelRoute:
    """How a model is reached. ``invoke_id`` is the ``modelId`` sent.

    For an application profile ``invoke_id`` is empty until the profile's ARN (which contains the account id)
    is resolved by name at call time, so no ARN lives in a file.
    """

    key: str
    model_id: str
    route_kind: RouteKind
    invoke_id: str = ""
    inference_profile: str | None = None


@dataclass(frozen=True)
class DecisionRequest:
    route: ModelRoute
    system: str
    user: str
    tool: ToolSpec
    max_tokens: int
    additional_fields: Mapping[str, Any] | None = None
    # A cache point after the system text (Phase 1 section 6.4). Off unless the request asks for it.
    cache_system: bool = False
    # Extra response fields to ask for, e.g. "/stop_details" (a smoke call only; a sweep never sends it).
    additional_response_fields: Sequence[str] | None = None


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0


@dataclass(frozen=True)
class Provenance:
    """What produced a result. Fields that need a sweep (sweep_id, image_digest) do not exist yet."""

    provider: str
    api: str
    model_id: str
    invoke_id: str
    route_kind: str
    inference_profile: str | None
    region: str
    thinking: str
    effort: str
    temperature: str
    max_tokens: int
    prompt_sha256: str
    started_at: str
    finished_at: str
    latency_ms: int


@dataclass(frozen=True)
class RawDecision:
    """Exactly what came back, unvalidated. An API error is a record, not an exception (planning/07 5)."""

    status: Literal["ok", "api_error"]
    provenance: Provenance
    raw_response: dict[str, Any] | None = None
    error: dict[str, str] | None = None
    stop_reason: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    text_blocks: list[str] = field(default_factory=list)
    reasoning_block_count: int = 0
    usage: Usage = field(default_factory=Usage)

    @property
    def tool_call_count(self) -> int:
        return len(self.tool_calls)

    @property
    def tool_input(self) -> dict[str, Any] | None:
        """The first tool call's arguments; None if the model did not call the tool."""
        return self.tool_calls[0]["input"] if self.tool_calls else None


class Provider(Protocol):
    name: str

    def decide(self, request: DecisionRequest) -> RawDecision: ...
