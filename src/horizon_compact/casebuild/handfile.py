"""The hand-boundaries file: item boundaries for a filing the splitter refuses (search-half doc §4.5).

``hand-boundaries.json`` in the case's folder maps an accession number to its item keys, each to a
``[start, end]`` pair of character offsets in the filing's extracted text (``splitter.html_to_text``)::

    {"0009999999-26-000001": {"1": [1200, 9800], "7": [20100, 31000], "human-capital": [4000, 6100]}}

Claude proposes the boundaries from the filing; he checks them; the file's hash goes into ``build.json``. An
absent file means no filing needed one. Nothing is guessed here: a malformed file is refused whole.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from horizon_compact.casebuild.sections import HandBoundaries

_ACCESSION = re.compile(r"\d{10}-\d{2}-\d{6}")


class HandFileError(Exception):
    """The hand-boundaries file cannot be read or is malformed."""


def load_hand_boundaries(path: Path) -> tuple[HandBoundaries, str | None]:
    """The boundaries and the file's SHA-256, or ``({}, None)`` where the file does not exist."""
    if not path.is_file():
        return {}, None
    try:
        raw = path.read_bytes()
        data = json.loads(raw)
    except (OSError, ValueError) as exc:
        raise HandFileError(f"{path.name} cannot be read: {type(exc).__name__}") from exc
    if not isinstance(data, dict) or not data:
        raise HandFileError(f"{path.name} is not an object of accession numbers (or is empty)")
    bounds: dict[str, dict[str, tuple[int, int]]] = {}
    for accession, items in data.items():
        if not _ACCESSION.fullmatch(str(accession)) or not isinstance(items, dict) or not items:
            raise HandFileError(f"{path.name}: {accession!r} is not an accession number with items")
        cuts: dict[str, tuple[int, int]] = {}
        for key, pair in items.items():
            ok = (
                isinstance(pair, list)
                and len(pair) == 2
                and all(isinstance(n, int) and not isinstance(n, bool) for n in pair)
                and 0 <= pair[0] < pair[1]
            )
            if not key.strip() or not ok:
                raise HandFileError(
                    f"{path.name}: {accession} item {key!r} is not [start, end] with 0 <= start < end"
                )
            cuts[key] = (pair[0], pair[1])
        bounds[accession] = cuts
    return bounds, hashlib.sha256(raw).hexdigest()
