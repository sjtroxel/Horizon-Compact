"""The page's two links to the rest of the repository (Phase 1.5 IMPLEMENTATION doc sections 0 and 20).

Nothing under ``web/src`` may import from outside ``web/``: the page reads only its own data file,
which is how "results reach the public URL only at go-live" holds while the official results sit in
the same repository. And the page's list of call statuses is the one ``sweep/classify.py`` defines,
in the same order.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import get_args

from horizon_compact.sweep.classify import Status

WEB = Path(__file__).resolve().parents[1] / "web"
SRC = WEB / "src"

# Static imports and re-exports, side-effect imports, dynamic import(), and CSS url() / @import.
_FROM = re.compile(r"""\b(?:import|export)\b[^"'`;]*?\bfrom\s*["']([^"']+)["']""")
_SIDE_EFFECT = re.compile(r"""\bimport\s*["']([^"']+)["']""")
_DYNAMIC = re.compile(r"""\bimport\s*\(\s*["']([^"']+)["']\s*\)""")
_URL = re.compile(r"""\burl\(\s*["']?([^"')]+)["']?\s*\)""")
_NEW_URL = re.compile(r"""new\s+URL\(\s*["']([^"']+)["']""")


def _specifiers(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    found = (
        _FROM.findall(text)
        + _SIDE_EFFECT.findall(text)
        + _DYNAMIC.findall(text)
        + _NEW_URL.findall(text)
    )
    if path.suffix == ".css":
        found += _URL.findall(text)
    return found


def _source_files() -> list[Path]:
    # Everything but the generated data file, which holds no imports (and is the one file the page reads).
    return sorted(
        p for p in SRC.rglob("*") if p.is_file() and p.suffix in {".ts", ".tsx", ".css", ".mjs"}
    )


def test_web_has_source_files() -> None:
    assert (SRC / "App.tsx").is_file()
    assert (SRC / "data" / "placeholder.json").is_file()
    assert len(_source_files()) >= 8


def test_nothing_under_web_src_imports_from_outside_web() -> None:
    escapes: list[str] = []
    for path in _source_files():
        for spec in _specifiers(path):
            if re.match(r"^[a-z][a-z0-9+.-]*:", spec, re.IGNORECASE) and not spec.startswith(
                "node:"
            ):
                escapes.append(f"{path.relative_to(WEB)}: {spec} (a URL or a drive path)")
                continue
            if spec.startswith("//"):
                escapes.append(f"{path.relative_to(WEB)}: {spec} (a host)")
            elif spec.startswith("/"):
                escapes.append(f"{path.relative_to(WEB)}: {spec} (an absolute path)")
            elif spec.startswith("."):
                target = (path.parent / spec.split("?")[0]).resolve()
                if WEB.resolve() not in (target, *target.parents):
                    escapes.append(f"{path.relative_to(WEB)}: {spec} (resolves outside web/)")
    assert escapes == []


def test_the_boundary_check_catches_an_escape(tmp_path: Path) -> None:
    # The check's own regexes must see each shape of import; a fixture holds one of each.
    sample = tmp_path / "x.ts"
    sample.write_text(
        'import a from "../../experiment/x";\n'
        'export { b } from "../../src/y";\n'
        'import "../../z.css";\n'
        'const c = await import("../../w");\n'
        'const u = new URL("../../v.json", import.meta.url);\n',
        encoding="utf-8",
    )
    assert _specifiers(sample) == [
        "../../experiment/x",
        "../../src/y",
        "../../z.css",
        "../../w",
        "../../v.json",
    ]


def test_the_page_lists_the_same_statuses_as_the_classifier() -> None:
    text = (SRC / "data.ts").read_text(encoding="utf-8")
    block = re.search(r"export const STATUSES = \[(.*?)\] as const;", text, re.DOTALL)
    assert block is not None
    listed = re.findall(r'"([a-z_]+)"', block.group(1))
    assert listed == list(get_args(Status))
