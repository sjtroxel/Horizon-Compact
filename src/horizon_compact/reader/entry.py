"""The reader's entry in ``models.toml`` and the route that reaches it (search-half doc §4.9, decision 3).

``hc case reader`` is the only reader of the entry. ``ModelsFile`` keeps it out of ``models``, so a sweep,
probe, awareness check, lock or gate cannot reach it; this module reads the file itself.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import ValidationError

from horizon_compact.casebuild.extraction_model import entry_sha256
from horizon_compact.experiment import MODELS_FILE, default_experiment_dir
from horizon_compact.model_config import ModelConfig, ModelsFile
from horizon_compact.providers.base import ModelRoute

__all__ = ["ReaderModelError", "entry_sha256", "load_reader_model", "reader_route"]


class ReaderModelError(Exception):
    """models.toml cannot be read, or has no usable reader entry."""


def load_reader_model(root: Path | None = None) -> tuple[str, ModelConfig]:
    """The reader's key and entry, from ``<root>/models.toml`` (``experiment/`` by default)."""
    path = (root or default_experiment_dir()) / MODELS_FILE
    try:
        models = ModelsFile.model_validate(tomllib.loads(path.read_text(encoding="utf-8")))
        return models.reader()
    except (
        OSError,
        UnicodeDecodeError,
        tomllib.TOMLDecodeError,
        ValidationError,
        ValueError,
    ) as exc:
        raise ReaderModelError(f"{MODELS_FILE}: {type(exc).__name__}: {exc}") from exc


def reader_route(key: str, config: ModelConfig) -> ModelRoute:
    """Unpinned: the stored reply names the host that served the call."""
    return ModelRoute(
        key,
        config.model_id,
        "openrouter",
        invoke_id=config.model_id,
        pinned_provider=config.openrouter_provider,
        reasoning_effort=config.reasoning_effort,
    )
