"""The extraction model's entry in ``models.toml`` and the route that reaches it (search-half doc §4.5).

``hc case build`` is the only reader. ``ModelsFile`` keeps the entry out of ``models``, so a sweep, probe,
awareness check, lock or gate cannot reach it (``tests/test_extraction_model.py`` proves each). This module
reads the file itself, because ``Experiment.model`` is the door the entry is deliberately not behind.
"""

from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

from pydantic import ValidationError

from horizon_compact.experiment import MODELS_FILE, default_experiment_dir
from horizon_compact.model_config import ModelConfig, ModelsFile
from horizon_compact.providers.base import ModelRoute


class ExtractionModelError(Exception):
    """models.toml cannot be read, or has no usable extraction entry."""


def load_extraction_model(root: Path | None = None) -> tuple[str, ModelConfig]:
    """The extraction model's key and entry, from ``<root>/models.toml`` (``experiment/`` by default)."""
    path = (root or default_experiment_dir()) / MODELS_FILE
    try:
        models = ModelsFile.model_validate(tomllib.loads(path.read_text(encoding="utf-8")))
        return models.extraction()
    except (
        OSError,
        UnicodeDecodeError,
        tomllib.TOMLDecodeError,
        ValidationError,
        ValueError,
    ) as exc:
        raise ExtractionModelError(f"{MODELS_FILE}: {type(exc).__name__}: {exc}") from exc


def extraction_route(key: str, config: ModelConfig) -> ModelRoute:
    return ModelRoute(
        key,
        config.model_id,
        "anthropic",
        invoke_id=config.model_id,
        thinking_off=config.thinking == "off",
        thinking_between_tools=config.thinking == "between_tools",
    )


def entry_sha256(key: str, config: ModelConfig) -> str:
    """The entry as used, for ``build.json``: its key and every field, in a fixed order."""
    canonical = json.dumps(
        {"key": key, **config.model_dump(mode="json")}, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
