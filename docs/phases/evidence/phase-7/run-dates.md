# Phase 7 step 2: the model and run dates on the results surfaces

Step 2 built: 2026-11-23. Read by Claude (Sonnet) from about 9:20 AM CST, with his approval of every word and both
data decisions (his "yes" of 9:46 AM, on the strings as listed). Opus reviews in a separate chat. A site change: M12
entry, Deploy. The words below are Claude-drafted and approved by him word for word (`planning/06` section 8, the gray
zone).

## 1. What was measured first (a local preview of the current build, 2026-11-23, before anything was built)

Every route rendered in headless Chromium from `npm run build:explorer` (the preview served `dist-explorer`), the text
read, the model switch (which puts both model names on every page) set aside.

| Surface | Names its model | Run dates before this step |
|---|---|---|
| The story | yes: "main model, Claude Haiku 5.5", the second-model section, every caption | none (its dates are the plan's, the reveal's and the rule's) |
| Results against the thesis (a section of the story) | yes: "Haiku 5.5 · Scenario s1 · B vs D" on each entry | none |
| Scenario views s1-s4, each model | yes: the chart card's caption, and the switch | none |
| Studies | yes | none |
| Cases list, the five case pages | yes | none (its "June 2026" and "June 2024" are the models' training cutoffs, not run dates) |
| Memo reader | yes: "Written by Haiku 5.5 under goal A..." | none |
| Methods, "The models, the dates and the runs" | yes | yes: first session started and last finished (UTC), per sweep |

So no model name was added; run dates were missing on six surfaces.

## 2. Where each date comes from (decisions 1a and 2a, his)

The index gains a `runs` block (`web/explorer-data/index.json`); every other committed data file is byte-identical.
Each date is the UTC calendar date of a copied timestamp (the one thing computed from it).

| Run | Source | Basis in the data |
|---|---|---|
| Both official grids, the thinking sub-study | each sweep's raw session records (the earliest `started_at`, the latest `finished_at`), via the methods data | `sessions` |
| Each awareness probe | its 15 raw call records (`experiment/raw/official/company/awareness/`): the manifest and `runs/r-*.json`, of which only the two timestamps are picked, never the reply | `calls` |
| Each case and model (ten) | the Sessions table of `docs/phases/evidence/phase-5.5/run-log.md`, read by its exact path; the case sweeps' raw text is not published and no results file carries a date | `run_log` (session start dates: the log records no finish time) |
| Each model's retirement | `experiment/retirements.toml`, empty in v1; kept outside `experiment/company/`, which is hashed into the protocol lock (`hc protocol check` passes) | `retired_on`, null for both models |

What the real data holds: both grids and the sub-study, 2026-10-14; the Haiku 5.5 probe 2026-10-14; the gpt-oss-120b
probe 2026-10-15 UTC (it started at 7:04 PM CDT on the 14th); the case runs 2026-10-29, and 2026-10-29 to 2026-10-30
for one gpt-oss-120b case, a sweep resumed after two stops.

The run-log reader refuses: no Sessions section; a row of other than eight cells; a time not marked UTC; an impossible
date; a sweep id the results do not hold, or one whose case label or model disagrees with the results; a When cell and
a "session started" date that disagree; a case sweep with no session row; a sweep id used by two results files. A
stop row (its Session cell starts with "(") is not a session. **A bug found by a test during the build:** the
"session started" date sits in the Stopped cell in the real log, not the Session cell, so the first version of the
When-versus-Session cross-check never ran; it now reads both cells.

## 3. The words (Claude-drafted, approved by him)

- `Runs: {model}, {date} (UTC).` and, over two days, `Runs: {model}, {from} to {to} (UTC).`
- For a case's runs: `Runs: {model}, started {date} (UTC).` / `... started {from} to {to} (UTC).`
- `{model} was retired on {date}; these results describe it as it was.` (rendered only when the data names a date)
- The M12 entry (dated November 23, 2026).

Dates read "October 14, 2026". Two days of one year read "October 29 to October 30, 2026" (the year said once, as in
the example he approved); different years are each in full. "(UTC)" is deliberate: the probe above.

## 4. Where the lines are

The scenario view (title band, the selected model's grid dates); the story's first decision (Haiku 5.5) and under each
model's heading in the second-model section; the section against the thesis (one line per model, under its
introduction); Studies (the sub-study, and the awareness probe of the model shown); the cases list (two lines on each
card) and each case page (under each model's heading); the memo reader (the kind shown: grid or thinking, only when
memos are shown). The retirement line, when the data names a date, follows the model's dates in each of those places.
**Not added, by his "yes" to the placement as listed:** the story's five case cards (they only summarize and link to the
case pages) and its other-scenarios section, whose models' dates are stated just above it.

## 5. Tests

- Python (`tests/test_site_explorer.py`): the `runs` block and its basis for each kind; UTC enforced; midnight
  crossings; every refusal above; the retirement file filled, empty and malformed; the new inputs in `sources` with
  their real sha256; the two "opens only" tests now exact for the awareness records; each real date recomputed from the
  raw files and the log's text by a separate route. `make check` is green: 3,620 Python tests, 697 web tests.
- Web (`runs.test.ts`, `runDates.test.tsx`, `format.test.ts`): the selectors return the index's own values and nothing
  else; each surface's lines equal, exactly and in order, the lines built from the index by the browser's own calendar
  (not by `format.ts`), so a wrong date, a missing line and an extra line each fail; the approved words pinned as
  strings; a changed index changes the page; no dates in the data means no line; the retirement line appears after the
  dates only for the retired model, and nowhere while the data holds none; each surface reads its own kind of run even
  when the dates differ (the real grid and sub-study share a date, so a separate test makes them differ).
- Negative controls, done by hand and reverted: changing "Runs:" to "Run:" failed 18 tests; the memo reader reading
  the wrong kind failed the kind test (and, before that test existed, passed everything, which is why it was added).

## 6. Budgets

The story's JavaScript: 96.1 KB of the 100 KB budget (was 95.6); the others unchanged to within 0.6 KB.
