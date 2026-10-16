"""The model set as configuration: which models, by which route, at what price and pace.

Run code, not content: ``experiment.py`` reads ``models.toml`` through these classes, but nothing under
``analysis/`` imports this module, so a later field here never touches the frozen analysis set (Phase 3.5
IMPLEMENTATION doc section 5.1). A test pins that.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# The role of the one model that builds a real case's dossier text (Phase 5 search half, section 4.5). It is
# not an experiment model: ``ModelsFile`` keeps it out of ``models``, so no sweep, probe, awareness check or
# lock can name it, and only ``hc case build`` reads it.
EXTRACTION_ROLE = "extraction"
# The role of the model that reads a case's rejections, scenario and rubric as the independent reader
# (protocol §12.9; search-half doc §4.9 and decision 3). Kept out of ``models`` the same way, so no sweep,
# probe or lock can name it, and only ``hc case reader`` reads it.
READER_ROLE = "reader"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Prices(_Strict):
    """USD per million tokens."""

    input: float = Field(ge=0)
    output: float = Field(ge=0)
    cache_read: float = Field(ge=0)
    cache_write_5m: float = Field(ge=0)


class ModelConfig(_Strict):
    model_id: str
    route: Literal[
        "in_region", "geo_profile", "application_profile", "local", "openrouter", "anthropic"
    ]
    role: str
    requests_per_minute: int = Field(gt=0)
    prices: Prices
    inference_profile: str | None = None
    geo_profile_id: str | None = None
    # The context window sent to a local runtime, in tokens. Required for a local route, refused for the rest.
    num_ctx: int | None = Field(default=None, gt=0)
    # An OpenRouter route's pinned provider, a slug from OpenRouter's endpoint list (``deepinfra/bf16``). The
    # request names it with fallbacks off, so OpenRouter can never serve the call from another backend
    # (Phase 4 code half section 4.8). Needed to run in the container; optional on the laptop.
    openrouter_provider: str | None = None
    # An Anthropic route's thinking setting: "off" sends ``thinking: {type: disabled}`` (Phase 3.5 section 23
    # decision C). "between_tools" sends ``thinking: {type: between_tools}``, the lowest setting on a model
    # that refuses ``disabled`` (Claude Sonnet 5.5), for the extraction model only. Left out, the model runs
    # at its own default. Refused for any other route.
    thinking: Literal["off", "between_tools"] | None = None
    # An OpenRouter route's reasoning level, sent as ``reasoning: {effort: ...}`` on every request. For a
    # model whose reasoning cannot be turned off (``gpt-oss-120b``), so the level is pre-registered rather
    # than left to OpenRouter's default (Phase 3.5 section 25). Left out, nothing is sent. Refused for any
    # other route.
    reasoning_effort: Literal["low", "medium", "high"] | None = None
    # The output allowance of every call to an extraction or reader model, fixed in its entry so it is
    # recorded with the model and not chosen at the command line. Required for those two roles, refused for
    # any other.
    # (A reader's reasoning tokens count toward it.)
    max_tokens: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _route_has_what_it_needs(self) -> ModelConfig:
        if self.route == "application_profile" and not self.inference_profile:
            raise ValueError("an application_profile route needs inference_profile")
        if self.route == "geo_profile" and not self.geo_profile_id:
            raise ValueError("a geo_profile route needs geo_profile_id")
        if self.route == "local" and self.num_ctx is None:
            raise ValueError("a local route needs num_ctx")
        if self.route != "local" and self.num_ctx is not None:
            raise ValueError("num_ctx is for a local route")
        if self.openrouter_provider is not None:
            if self.route != "openrouter":
                raise ValueError("openrouter_provider is for an openrouter route")
            if not self.openrouter_provider.strip():
                raise ValueError("openrouter_provider must name a provider")
        if self.thinking is not None and self.route != "anthropic":
            raise ValueError("thinking is for an anthropic route")
        if self.reasoning_effort is not None and self.route != "openrouter":
            raise ValueError("reasoning_effort is for an openrouter route")
        if self.role == EXTRACTION_ROLE:
            if self.route != "anthropic" or self.thinking is None or self.max_tokens is None:
                raise ValueError(
                    "an extraction model is on the anthropic route, with thinking off "
                    '("off" or "between_tools") and a max_tokens, all fixed in its entry'
                )
        elif self.role == READER_ROLE:
            if self.route != "openrouter" or self.max_tokens is None:
                raise ValueError(
                    "a reader model is on the openrouter route, with a max_tokens fixed in its entry"
                )
        elif self.max_tokens is not None:
            raise ValueError("max_tokens is for an extraction or reader model")
        elif self.thinking == "between_tools":
            raise ValueError('thinking = "between_tools" is for an extraction model')
        return self


class ModelsFile(_Strict):
    """``models.toml``. **The extraction and reader models are kept out of ``models``.** Every sweep plan,
    run, probe, awareness check, cost estimate, lock and gate reads ``models``, so an entry with role
    ``extraction`` or ``reader`` is, to all of them, an unknown model: it cannot be planned, probed or
    locked, with no per-path check to forget. Only ``extraction()`` and ``reader()`` reach them."""

    pace_fraction: float = Field(gt=0, le=1)
    models: dict[str, ModelConfig]
    extraction_models: dict[str, ModelConfig] = Field(default_factory=dict)
    reader_models: dict[str, ModelConfig] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _set_the_case_tool_models_apart(cls, data: Any) -> Any:
        if not isinstance(data, dict) or not isinstance(data.get("models"), dict):
            return data
        for field_name in ("extraction_models", "reader_models"):
            if field_name in data:
                needed = EXTRACTION_ROLE if field_name == "extraction_models" else READER_ROLE
                raise ValueError(
                    f"{field_name} is not a models.toml key; give the entry role = '{needed}'"
                )
        models: dict[str, Any] = {}
        extraction: dict[str, Any] = {}
        readers: dict[str, Any] = {}
        for key, entry in data["models"].items():
            entry_role = entry.get("role") if isinstance(entry, dict) else None
            target = {EXTRACTION_ROLE: extraction, READER_ROLE: readers}.get(
                str(entry_role), models
            )
            target[key] = entry
        return {**data, "models": models, "extraction_models": extraction, "reader_models": readers}

    @model_validator(mode="after")
    def _one_of_each_case_tool_model_at_most(self) -> ModelsFile:
        for what, found in (("extraction", self.extraction_models), ("reader", self.reader_models)):
            if len(found) > 1:
                raise ValueError(f"at most one {what} model, found {', '.join(sorted(found))}")
        return self

    def extraction(self) -> tuple[str, ModelConfig]:
        """The extraction model's key and entry."""
        for key, config in self.extraction_models.items():
            return key, config
        raise ValueError("models.toml has no extraction model")

    def reader(self) -> tuple[str, ModelConfig]:
        """The independent reader's key and entry."""
        for key, config in self.reader_models.items():
            return key, config
        raise ValueError("models.toml has no reader model")
