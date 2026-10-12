"""The model set as configuration: which models, by which route, at what price and pace.

Run code, not content: ``experiment.py`` reads ``models.toml`` through these classes, but nothing under
``analysis/`` imports this module, so a later field here never touches the frozen analysis set (Phase 3.5
IMPLEMENTATION doc section 5.1). A test pins that.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    # decision C). Left out, the model runs at its own default. Refused for any other route.
    thinking: Literal["off"] | None = None

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
        return self


class ModelsFile(_Strict):
    pace_fraction: float = Field(gt=0, le=1)
    models: dict[str, ModelConfig]
