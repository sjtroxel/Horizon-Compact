"""``hc dossier check``: the checks of Phase 2 IMPLEMENTATION doc section 7, run by ``make check`` and CI.

Failures make the check fail. Notes (the balance report, the length estimate, anything skipped) never do.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from horizon_compact.dossier.figures import (
    FIGURES_FILE,
    SOURCES_FILE,
    FigureError,
    FigureSet,
    parse_rows,
    parse_sources,
    resolve,
)
from horizon_compact.dossier.render import (
    COMPANY_DIR,
    TEMPLATE_PATH,
    Template,
    TemplateError,
    balance_report,
    estimated_tokens,
    render_outputs,
    render_text,
    scan_template,
)

LENGTH_WARNING_TOKENS = 7_000


@dataclass
class Report:
    failures: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def reachable(fs: FigureSet, template: Template) -> set[str]:
    """Rows the template uses, directly or through a formula."""
    found: set[str] = set()
    pending = [key for key in template.references() if key in fs.rows]
    while pending:
        key = pending.pop()
        if key in found:
            continue
        found.add(key)
        pending.extend(fs.references.get(key, ()))
    return found


def run_checks(root: Path) -> Report:
    report = Report()
    company = root / COMPANY_DIR
    sources_text = _read(company / SOURCES_FILE)
    if sources_text is None:
        report.failures.append(f"{COMPANY_DIR}/{SOURCES_FILE} is missing")
        return report
    try:
        sources = parse_sources(sources_text)
    except FigureError as exc:
        report.failures.append(str(exc))
        return report
    for name, source in sources.items():
        if not (root / source.extract).is_file():
            report.failures.append(
                f"{SOURCES_FILE}: {name}: the extract {source.extract} does not exist"
            )

    # No skip: the figures and the template must exist (the not-built-yet skip of steps 2-4 was removed in
    # step 6, when they landed). A missing rendered file is reported by the freshness check below.
    figures_text = _read(company / FIGURES_FILE)
    template_text = _read(root / TEMPLATE_PATH)
    if figures_text is None or template_text is None:
        missing = [
            name
            for name, text in (
                (FIGURES_FILE, figures_text),
                ("dossier.template.txt", template_text),
            )
            if text is None
        ]
        report.failures.append(f"{COMPANY_DIR} is missing: {', '.join(missing)}")
        return report

    try:
        fs = resolve(parse_rows(figures_text), sources)
    except FigureError as exc:
        report.failures.append(str(exc))
        return report
    template, problems = scan_template(template_text)
    report.failures.extend(f"dossier.template.txt: {problem}" for problem in problems)
    if template is None:
        return report

    unknown = sorted(set(template.references()) - fs.rows.keys())
    if unknown:
        report.failures.append(
            f"dossier.template.txt uses rows that do not exist: {', '.join(unknown)}"
        )
        return report
    orphans = sorted(fs.rows.keys() - reachable(fs, template))
    if orphans:
        report.failures.append(
            f"{FIGURES_FILE}: rows the text never uses, directly or by formula: {', '.join(orphans)}"
        )

    try:
        outputs = render_outputs(template, fs)
    except TemplateError as exc:
        report.failures.append(str(exc))
        return report
    for path, expected in outputs.items():
        actual = _read(root / path)
        if actual is None:
            report.failures.append(f"{path} is missing; run `hc dossier render`")
        elif actual != expected:
            report.failures.append(f"{path} differs from a fresh render; run `hc dossier render`")

    _add_notes(report, template, fs)
    return report


def _add_notes(report: Report, template: Template, fs: FigureSet) -> None:
    words = balance_report(template, fs)
    total = sum(words.values())
    shares = ", ".join(f"{group} {count}" for group, count in words.items())
    report.notes.append(f"balance, words per group: {shares} (total {total})")
    tokens = estimated_tokens(len(render_text(template, fs, cited=False).split()))
    report.notes.append(f"estimated length: about {tokens:,} tokens (words x 1.35, an estimate)")
    if tokens > LENGTH_WARNING_TOKENS:
        report.notes.append(
            f"WARNING: above {LENGTH_WARNING_TOKENS:,} tokens; say so before trimming anything"
        )
    unused = sorted(set(fs.sources) - {row.source for row in fs.rows.values() if row.source})
    if unused:
        report.notes.append(f"sources no row cites: {', '.join(unused)}")
