# Phase 6 — Explorer: IMPLEMENTATION (v0.6)

> **IMPLEMENTATION doc. APPROVED 2026-11-09, about 8:30 AM (his): all nine decisions in §13 as recommended, with
> decision 2 changed to a local preview after his question (no second Vercel site; §13).** Drafted the same morning (Opus). Written the morning after Phase 1.5
> closed (`2227a26`), immediately before this phase is built, and five weeks after its scope doc. Sources: the scope
> doc (`docs/phases/phase-6-explorer.md`) and Phase 6.5's (`phase-6.5-methods-and-release.md`); `planning/00` §4-§6,
> `planning/04` §1.2-§1.3 and §2.5, `planning/06` §4-§9 (all of it binds this phase), `planning/07` §1, §7, §10 and
> §12; the protocol (`experiment/protocol/protocol-v1.md` §1.4-§1.6); the Phase 1.5 IMPLEMENTATION doc (§0, §7, §8,
> §9, §17-§26); the Phase 4 runs doc (§5.4, §6.8, §13) and the Phase 5.5 doc (§5.4, §6.4-§6.7); `KNOWN-GAPS.md` (START
> HERE, OPEN 2026-10-31); the committed results under `experiment/results/` (read for shape on 2026-11-09, after the
> reveal of 2026-10-15); `web/` at `2227a26`; and live checks the same morning (§2). The `dataviz` skill was loaded
> before §7 named any chart form.
>
> **What this doc is.** The scope doc was written on 2026-10-04, before any result existed. §0 is the scope review,
> as Phase 1.5's was; §3 holds what writing this doc found, four findings of which need his decision before anything
> is built (§13, decisions 1, 2, 4 and 5). The rest is the build plan.
>
> **Rule zero governs every line.** Real cases appear only by label, type and their published coarse description. No
> memo text from a real case is quoted in this doc, and none will be quoted in any phase doc.

## 0. The scope review: what changed since 2026-10-04

Read the scope doc with these changes. Each is measured or cited; none lowers a rule.

1. **The model set is the fallback set** (Phase 3.5 §23, 2026-10-11): **Haiku 5.5** (main, Anthropic's API) and
   **gpt-oss-120b** (second family, OpenRouter). The scope doc's "the second model" robustness study is therefore a
   full official grid of its own, shown beside the main model's at the same size and never pooled (`planning/07` §1).
   The site takes every model's name from the records, as Phase 1.5's does.
2. **The results exist, and their shape is known.** Three results files from the frozen analysis
   (`experiment/results/prereg-v1/`, `RESULTS_VERSION` 2, written 2026-10-15): Haiku's grid (990 runs), gpt-oss's
   grid (1,200 runs) and Haiku's thinking sub-study (100 runs, scenario `s1` only). Each scenario carries five
   comparisons (four primary, one secondary) with their verdict, interval, per-wording detail, first attempt and the
   analysis's own `headline` string; 15 to 20 cells with attempted, valid, refused and failures by type; and a
   descriptive block with **per-run values** (`per_run`, one row a run: objective, wording, repeat, primary value,
   shares, choice). `planning/06` §7.3's ask that the JSON carry per-run values is met. Per-cell repeats differ by
   scenario and model (Haiku's `s2` ran 6 a cell, 87 valid runs in all, where its other scenarios ran 20), so every
   number carries its own count and no layout may assume a fixed n.
3. **Verdicts come in four kinds, not three:** split, no split, inconclusive, and **not assessable** (one gpt-oss
   comparison, `s2` A vs C, where every wording has a cell over the 10% failure limit). Several verdicts rest on fewer
   wordings than three, because a wording is dropped from both sides when either cell fails over 10%; the `headline`
   string says which. Every view shows the verdict with its wordings and its drops; none hides a drop.
4. **The real cases are exploratory, five of them, and none can be re-run from published inputs.** No candidate met
   the pre-registered selection rule; the five (`closure-07`, `closure-19`, `pre-11`, `pre-25`, `pre-224`) were
   selected under the search-half doc's §4.6.5 after it found none, and each carries its `exploratory_label`
   (`experiment/results/cases/cases.json`). **Every surface that shows a case shows that label** (his condition,
   2026-10-18). All five dossiers were withheld by the re-identification check; four coarse descriptions are
   published and `pre-11`'s is withheld, so that case appears by type only. Every reading in all ten case results is
   **no good match** (Phase 5.5 §6.4).
5. **Two behaviors of the frozen matcher must be stated wherever the case results are shown** (KNOWN-GAPS OPEN
   2026-10-31, which closes when Phases 6 and 6.5 carry both notes): a five-way exact tie yields an arbitrary nearest
   objective that `depends_on_reading` inherits, and a one-line reading (`closure-19`'s `u1`) averages a structural
   zero into its distance. This doc makes both a DoD row (§15, row 8).
6. **The site exists, and its rules carry over.** React 19 and TypeScript on Vite, hand-drawn SVG with no chart
   library, self-hosted fonts, a content security policy that forbids every other host, `noindex`, and a build check
   (`web/scripts/check-dist.mjs`) holding a JavaScript budget of 100 KB gzipped (about 74 KB used today) and a font
   budget of 150 KB. The look Phase 1.5 chose (Big Shoulders Display for the name, Source Sans 3 for headings,
   Newsreader for prose, the ink-and-paper colors, his footer) is the explorer's starting point; the previews (§7)
   decide the chart form, palette and layout on real data, as `planning/06` §7.3 says.
7. **The deploy path publishes every `web/` change.** Deploy's site half builds `web/` on any push under `web/` and
   syncs it to the distribution behind `horizon-compact.vercel.app`. So scope decision 2 (results reach the public URL
   only at go-live) is not held by where the explorer is previewed; it has to be held in the build (§3 finding 3,
   decision 3).
8. **The data path changes.** Phase 1.5's site-data builder reads S3 and refuses everything but
   `development/placeholder/`; that rule stays, for that builder. The explorer's data comes from the **committed**
   results files, which need no AWS access, by a second builder (§5). Grid memos are the exception: they are only in
   the raw records in S3 (§3 finding 4).
9. **Phase 1.5's §8 standard ("polished, with no sign of generated filler") applies here,** and his ask of 2026-11-04
   reaches this phase in full. §12 carries it forward.
10. **Prerequisites:** all met. Phase 5.5 closed 2026-11-03; Phase 1.5 closed 2026-11-08; the JSON schema is
    `RESULTS_VERSION` 2 (Phase 3, frozen at `prereg-v1`).

## 1. Where things stand on 2026-11-09

- **Every phase through 5.5 is closed**; version `0.5.5`. Phase 1.5's close (`2227a26`) is pushed, CI and Deploy green.
- **The public URL** shows Phase 1.5's placeholder page, through the Vercel rewrite to `d10219migxiagd.cloudfront.net`.
- **Committed results:** the three Phase 4 files (5.8 MB in all under `experiment/results/`, with the cases); per case,
  two results files, two memo files and two memo summaries (1,237 of 1,500 memos published, 263 held), `reident.json`,
  and `cases.json`.
- **In S3 only:** every raw record, grid memos included. Phase 4's raw-object manifest is committed
  (`docs/phases/evidence/phase-4/raw-manifest.json`, 5,247 objects); their full text is Phase 6.5's DoD row 8.
- **Spend:** cumulative at most about $46 (`evidence/phase-5.5/cost.md`); Phase 1.5 about $0.01. This phase makes no
  model call.

## 2. Versions and facts, checked live 2026-11-09

| Item | Today | Choice and why |
|---|---|---|
| Vite | 8.3.7 (published this morning); 8.3.6 (2026-11-05); pinned 8.3.5 | **stay 8.3.5**; nothing in this phase needs a bump |
| `@vitejs/plugin-react` | 6.3.0 (this morning); pinned 6.1.2 | stay |
| React; TypeScript | 19.3.1; 7.0.2 | as pinned |
| Vitest | 5.1.0 (2026-11-02, seven days old); pinned 4.1.12 | stay on 4.1.x (the 14-day rule) |
| jsdom | 31.0.0 (2026-11-05, a new major); pinned 29.1.1 | stay |
| `axe-core` | 4.14.0 | as pinned |
| `@resvg/resvg-js` | 2.6.2 (2024-03-26) | the share-card rasterizer if decision 6 is (a); build-time only, never shipped to the browser |
| `satori` | 0.63.2 (2026-10-20) | not needed if decision 6 is (a) |
| Vercel Deployment Protection | read on Vercel's docs today | **"All Deployments" with Vercel Authentication is available on every plan, Hobby included, and needs no paid add-on**; Password Protection is not available on Hobby. So a preview project can be closed to everyone but his Vercel account (decision 2) |

Versions are rechecked at each install, as in Phase 1.5 (exact pins, `npm ci`, the 14-day rule).

## 3. What writing this doc found

1. **The section for results against the thesis has no fill rule.** His title is "Results that go against what I
   expected", and its sentence promises that every finding that goes against what he expected will be listed, by a
   rule planned before the experiment ran. **No such rule was written.** What exists from before the results: the
   protocol's table of what each pattern would mean (§1.5, tagged `prereg-v1` 2026-10-13), and `planning/00` §4
   principle 3 and §5.1's "how the grid reads" (2026-10-02 and 2026-10-03), which say that if the long-horizon
   objective also cuts, that ships, and that "everything cuts" is the result against the thesis. His own expectation,
   comparison by comparison, was never recorded, and it cannot be recorded now: the reveal was on 2026-10-15. So the
   section can be filled honestly only by a mechanical rule taken from those dated documents and stated on the page
   beside the list. Decision 1. This is the finding most likely to be attacked by a hostile reader if it is left to
   judgment, so it is settled before any view is built.
2. **The preview needs a host that is not the public URL.** Scope decision 2 keeps the public URL on the placeholder
   until go-live; Delivers 8 wants the explorer "deployed somewhere he can open it." Vercel's Hobby plan can close a
   whole project behind Vercel's own login (§2). Decision 2. *(Decided 2026-11-09: local only. A protected preview
   cannot be fetched by a social platform's crawler either, so it would not have tested link previews, its one real
   advantage.)*
3. **The build, not the host, has to keep results off the public URL.** Deploy builds whatever `web/` holds on every
   `web/` push (§0 item 7). If the explorer's code and data land in `web/` with no guard, the next push puts results on
   the public page with none of the methods page beside them, which is what scope decision 2 forbids. Decision 3
   proposes two build modes, with Deploy pinned to the placeholder mode until Phase 6.5 changes it, and a check that
   fails the placeholder build if any official run id or results file reaches `dist/`.
4. **Grid memos are not in any committed file.** The memo reader needs them; they live only in the raw records in
   S3, which Claude's deny list keeps from Claude (Phase 4 doc §5.4), so extracting them is his run. 2,290 memos
   (both grids and the sub-study), all on the fictional company, so rule zero is not engaged; the extract is tied to
   the raw-object manifest by sha256 so a reader can check it against Phase 6.5's full-text publication. Decision 4.
5. **Published real-case memos repeat figures from their withheld dossiers.** Phase 5.5's memo scan (its §5.4, §6.5)
   looked for names and held a memo whose flagged words all came from a withheld dossier. It did not look at numbers.
   A sample read today shows a published memo restating the case's figures. **The dollar figures are scaled**
   (Phase 5's case build multiplies them by a hidden factor, protocol §12.6), so they do not point at the company;
   **percentages, growth rates and other scale-free figures are not scaled**, and the dossiers were withheld precisely
   because their scale-free figures narrow the field to fewer than 20 filers. One or two repeated ratios are far
   weaker than a whole dossier, and these memos have been in the public repository since 2026-11-01, so nothing done
   now takes them back. **What is still open is whether the explorer amplifies them.** Decision 5 proposes a
   count before deciding: how many published memos repeat a scale-free figure from their withheld dossier. Claude
   writes it; he runs it, since the dossiers are private; only counts reach the repository.
6. **Per-view link previews need per-view URLs that serve distinct HTML.** A crawler reads `og:` tags from the HTML
   and runs no JavaScript, so each view needs its own small HTML file carrying its title, description and card image.
   On CloudFront with an S3 origin behind an access control, a path such as `/scenario/s1/` does not resolve to its
   `index.html` by itself; that is a serving detail for Phase 6.5's go-live (a CloudFront Function or a rewrite rule),
   noted here so the path shape chosen now works for both. The preview (decision 2) is served by Vercel, which
   resolves such paths. Decision 6.
7. **The guided story walks one scenario, and which one cannot be chosen by its result.** Decision 7 proposes `s1`,
   the first scenario in protocol order, fixed here before any design work, with the second model's result on the
   same comparisons shown beside the main model's at the same size.
8. **The frozen analysis already writes a sentence per comparison** (`headline`, e.g. "split, robust: the direction
   holds under every wording, over wordings w1, w2 and w3"). It is the analysis's output and is not reworded by the
   front end. The result-sentence templates (scope decision 3) are rendered from the structured fields beside it
   (verdict, difference, interval, valid runs, wordings kept and dropped), so the site never recomputes a number and
   never says more than the file.

## 4. What this phase delivers

As the scope doc's Delivers 1-8, read through §0, plus:

- **The explorer-data builder** (§5), run code in Python, from the committed results files to the site's split JSON;
  a second build byte-identical; its output committed.
- **The grid memo extract** (§5.3; decision 4), his S3 run.
- **The real-case figure count** (decision 5), his run, counts only.
- **Two build modes** (decision 3) and the placeholder-mode check.
- **The local preview** (decision 2): `npm run preview:explorer` builds explorer mode and serves it on `localhost`,
  which his Windows browser reaches from WSL; Claude's headless captures at 1280 and 390 stand in for a phone, as in
  Phase 1.5's review.

## 5. The explorer-data builder (run code; Sonnet builds, Opus reviews)

**Command:** `hc site explorer` (no AWS, no flags beyond `--out`), reading only `experiment/results/prereg-v1/**` and
`experiment/results/cases/**`, writing `web/explorer-data/`. Standard library only, as Phase 1.5's builder.

**It reshapes and never computes.** Every number in its output is copied from a results file field by field: no
mean, interval, rounding or verdict is computed in the builder or the front end (scope rule: "the numbers on the
site are the frozen analysis's output"). The one exception allowed is formatting at display time (a share shown as a
percentage to the precision the file carries), and a test pins each format to its source value.

**Split, so each view loads only what it needs** (scope Delivers 2):

- `index.json`: models, scenarios, objective letters and descriptions (from `experiment/company/objectives.toml`),
  the comparisons with their verdicts for every model and scenario, and file names for the rest. Small enough to load
  with the page.
- `grid/<model>/<scenario>.json`: one scenario's cells, comparisons in full (per-wording, first attempt, drops) and
  per-run rows. Loaded when the scenario is opened.
- `thinking/haiku-5-5/s1.json`: the sub-study, same shape.
- `cases/index.json` and `cases/<label>/<model>.json`: from `cases.json` and the case results files; the exploratory
  label, the coarse description (or "withheld"), the dossier status, every reading's distances and intervals, the
  matcher notes (§0 item 5) as fields the view must render.
- `memos/<model>/<scenario>/<objective>.jsonl` and `cases/<label>/memos-<model>.jsonl`: loaded on demand; real-case
  memos only as published by Phase 5.5 (a held memo appears as "held", with the reason), and subject to decision 5.

**It refuses:** any file outside the two prefixes; a results file whose `results_version` is not 2; a case whose
`exploratory` is true without its label; a real-case memo marked held; any string matching the account-id and bucket
checks Phase 1.5's builders use.

**Tests:** a second build byte-identical; every number in the output found, unchanged, at its source path (a
property test over all fields); each refusal; the matcher-note fields present wherever their condition holds (every
distance in a reading equal; a one-line reading).

**Where its output lives:** `web/explorer-data/`, outside `web/public/`, so the placeholder build cannot copy it by
accident (decision 3). Committed, so its diff is reviewable, and CI re-runs the builder and fails on any difference: a
first, narrow form of Phase 6.5's re-scoring check, reading only committed files.

### 5.3 The grid memo extract (decision 4)

*Amended 2026-11-09 (his, §21a item 6):* the extract is written to **`web/explorer-memos/`**, a sibling of
`web/explorer-data/`, not inside it: it comes from his S3 run, so CI cannot rebuild it, and the folder CI reproduces
stays exact. Read `web/explorer-data/memos/` below as `web/explorer-memos/`.

`hc site memos --store s3` (his run; on the deny list, since it reads official records): for each official run of the
two grids and the sub-study, the run id, model, scenario, objective, wording, repeat, status and memo text, written to
`web/explorer-data/memos/`, plus a line per source object with its key and sha256 from
`raw-manifest.json`, so every memo traces to an object a reader can fetch once Phase 6.5 publishes them. A run with no
valid memo appears with its status and no text. **No memo is edited, trimmed or summarized** (`planning/06` §6.1).

## 6. Site structure

**Two build modes** (decision 3): `placeholder` (today's page, unchanged, the mode Deploy builds until Phase 6.5) and
`explorer`. The mode is a Vite build option; the explorer's entry and data are imported only in explorer mode.
`check-dist.mjs` in placeholder mode fails if `dist/` holds any file from `web/explorer-data/`, any of the 2,290 official
run ids, or any official sweep id (the three in `experiment/results/prereg-v1/` and the ten case sweeps). A Vitest
test asserts the same on the module graph.

**Paths** (decision 6): `/` (the guided story), `/scenario/<id>/` (one per scenario), `/cases/` and
`/cases/<label>/`, `/studies/` (the thinking sub-study and the awareness probes), `/memos/` (the reader, with the
scenario, model and objective in the query string). Each path has its own small HTML file written after the build,
with its own title, description, canonical URL and card image; all share one bundle. **Routing is plain links and
the History API**, no router package.

**Budgets stay:** JavaScript 100 KB gzipped, fonts 150 KB; data files are not counted as JavaScript and are loaded with
`fetch` from the site's own origin, which the content security policy already allows (`connect-src 'self'`).

## 7. The previews (scope Delivers 1; the `dataviz` skill loaded)

Three decisions, in a fixed order, three to six throwaway previews each, built by Claude as static pages in `scratch/`
from the real data, captured headless in light and dark at 1280 and 390 (the 2026-11-06 method), and compared side by
side by him. His picks are recorded in this doc, with the previews kept in `scratch/`, untracked.

**1. Chart form.** The candidates, each judged against `planning/06` §7.2 and the skill's anti-patterns:

- **(i) Per-run strip with interval.** One row per objective, every valid run a dot on the primary outcome's axis, the
  mean and the analysis's interval drawn over them. Spread is the mark itself, n is visible as the dots.
- **(ii) Small multiples of the full allocation.** One panel per objective, levers in canonical order, per-run dots
  and a range per lever. The scope doc's form for the full allocation (`planning/06` §7.2 rule 3).
- **(iii) Comparison interval chart.** One row per comparison, the difference and its interval against the
  threshold band (`threshold` in each comparison): an interval inside the band reads "no split", one outside reads
  "split", one across its edge reads "inconclusive". The verdict becomes visible geometry, which also makes a
  verdict hard to crop away from its evidence.
- **(iv) Unit chart for choice scenarios** (`s3`, `s4`): each run a square, grouped by objective and choice, so a
  rate is seen as counted runs.
- **(v) A table-first view** with inline range bars, as the accessible fallback every chart needs anyway.

The likely outcome is a combination (iii for the verdicts, i or iv for the primary outcome, ii for the full
allocation), but that is his pick on real data, not this doc's.

**2. Palette.** `planning/06` §7.2 rule 1 as the starting proposal (hue for who counts, lightness for horizon, a
neutral gray for E), run through the skill's validator in light and dark against the site's two surfaces, plus up to
three alternatives the validator passes. No red-green pair, no status color for a verdict, and the verdicts carried by
words and geometry, never by color.

**3. Layout.** The scenario view's arrangement at both widths: where the verdicts sit relative to the allocation, how
the model switch works, where the scope sentence and run counts sit so a crop keeps them.

## 8. The views, component by component

Each view carries the scope sentence (his wording), its run counts on every number, and the model's name from the
records. No result is colored as a win or a loss.

- **Scenario view** (`/scenario/<id>/`): the scenario in brief (from the scenario file, the same text the model saw,
  linked in full); a model switch (Haiku 5.5, gpt-oss-120b) that never shows the two pooled; the five comparisons
  with verdict, interval, valid runs, wordings kept and dropped, the sealed wording's verdict separately, first
  attempt beside final; the primary outcome per objective (preview form); the full allocation (small multiples); cell
  failure and refusal rates, every status shown even at zero (Phase 1.5's rule); any objective toggled on or off,
  with a transition only.
- **The section for results against the thesis**, his title, filled by decision 1's rule, the same chart styles and
  sizes as everything else (`planning/06` §7.2 rule 4), reachable from the story and from every scenario view.
- **Memo reader** (`/memos/`): memos set as documents with the label inside the card (`planning/06` §6.1): written by
  the model under objective X, for a fictional company (or an anonymized real decision), not the project's view; run
  id, wording and status on the card; never edited.
- **Real cases** (`/cases/`): the exploratory label first on every card; the coarse description or "withheld"; the
  dossier's status and why; both models' readings, all five distances with their intervals, the label ("no good
  match" in every reading today); the matcher notes where their condition holds; observed and excluded dimensions
  (`planning/07` §10.2). Framed as the protocol applied to real decisions, not as validation.
- **Studies** (`/studies/`): the thinking sub-study (Haiku 5.5, `s1`, 100 runs), labeled as a sub-study and shown
  beside the main grid's `s1` at the same size; the awareness probes (both models, 15 replies each), labeled as what
  they are.
- **Guided story** (`/`): §9.
- **Share cards**: §10.

## 9. The guided story (scope Delivers 4)

**Beats** (structure only; every sentence in it is his or a template he approved word for word):

1. The question, his words. The name explained in the opening (`planning/06` §6.4).
2. The setup in one screen: one fictional company, one model, five objectives (letters and literal descriptions,
   `planning/06` §6.2), the same decision. The scope sentence here.
3. `s1` on the main model (decision 7): the primary outcome by objective, every run visible.
4. The comparisons on `s1`, one at a time, each with its verdict and interval; C vs D named as the test of the
   Roundtable's claim (protocol §1.5), with the protocol's pre-registered reading of its result quoted as written.
5. The same comparisons on the second model, beside the first, at the same size.
6. The other three scenarios in one compact view, every verdict shown, inconclusive and not assessable included.
7. The section for results against the thesis, at full size.
8. The real cases, exploratory label first.
9. The path to the methods page (a link to Phase 6.5's page; until then, to the protocol in the repository).

Scroll moves the reader through the beats with transitions only (`planning/06` §7.2 rule 7); under
`prefers-reduced-motion`, or without JavaScript's observer, the same beats are a plain page. No scroll library:
`IntersectionObserver`, which every current browser has.

## 10. Share cards (scope Delivers 5; decision 6)

One PNG per path, 1200 by 630, generated in the build from the same data files the view reads: the view's title (his),
the model, the run count, the scope line, and for a scenario its comparisons' verdicts as words. The image is drawn as
SVG by a small template in the build script and rasterized by `@resvg/resvg-js` with TTF copies of the three fonts
(OFL, the same families, committed under `web/fonts-ttf/` for the build only). A test reads each card's SVG and checks
that every number in it is in the view's data file, and that the scope line and run count are present.

## 11. Words

**His** (scope decision 3): the landing question, the scope sentence's public wording, every section and view title,
every introductory sentence, and any revision of the results section's title or sentence that decision 1 calls for.
Claude interviews and critiques; it does not draft these unless he asks on that pass.

**Claude drafts, he approves word for word, each flagged as Claude-drafted when handed over:** the result-sentence
templates (from `planning/06` §4's allowed column, filled from the structured fields of §3 finding 8), the memo-card
label, chart labels and axis text, the matcher notes' wording, and the share cards' fixed text. Recorded in this doc
as Phase 1.5 §20 recorded its labels.

## 12. What "polished" means here, as checks

Phase 1.5 §8 carries over in full (type scale, spacing, focus states, both modes, both widths, no layout shift, no
console error, `axe-core` clean, nothing generic). Added for this phase:

- every chart passes the `dataviz` anti-patterns list and the palette validator in both modes;
- every number traces to the data file (scope DoD 5), checked on a sample per view by a script, not by eye;
- a crop test: for each view, a screenshot cropped to the chart alone still shows the model, the run count and the
  scope line;
- the story read with reduced motion and at 390 wide, beat by beat;
- every result sentence on every view is an approved template, checked by a test that rejects any rendered result
  sentence not produced by a template.

## 13. Decisions for him

My recommendation is (a) in each, for the reason given.

1. **DECIDED 2026-11-09 (his): (a); the rule is §19, written as if a skeptical AI reviewer will audit it (his
   instruction), with §20 listing what such a reviewer would dig for.** *Was:* **How the section for results against
   the thesis is filled.**
   - (a) **Recommended: a mechanical rule, taken only from documents dated before the results**, written into this
     doc for his approval, applied by code, and stated on the page beside the list with its sources and dates. The
     draft rule, from `planning/00` §4 principle 3 and §5.1 and the protocol's §1.5: *a primary comparison belongs in
     the section if, on that scenario's primary outcome, it shows "no split" between a pair that differs in horizon or
     in who counts, or a split in which the longer-horizon or all-stakeholder objective of the pair cuts more than the
     other; and a scenario belongs if every objective's runs cut.* "Cuts" is defined per scenario from the scenario
     files' own wording of each outcome, fixed in this doc before the rule is run. Inconclusive and not assessable
     verdicts are not "against" anything and are shown at full size in the scenario views and the story, not here.
     Because his title promises "what I expected", and that expectation was never written per comparison, he may want
     to revise the title or sentence so they name the rule's source; those words stay his.
   - (b) List every primary verdict in the section, so no selection is made. Safe, but it turns the section into a
     copy of the results and drops what `planning/04` §1.2 wanted from it.
   - (c) He writes his expectation now and the section follows it. Not recommended: written after the reveal, it
     cannot be shown to be what he expected before.
2. **DECIDED 2026-11-09 (his question, Claude's revised recommendation): local only.** He asked whether a second
   Vercel site was needed, or a hidden path on the existing one. A hidden path on the public site is unlisted, not
   unreachable: anyone with the link sees the full explorer on the real domain, and it would put results on the
   public deploy path that decision 3 keeps them off. A protected preview cannot be read by a social platform's
   crawler, so it would not have tested link previews either. Local serving does everything else: his browser, Claude's
   headless captures at both widths, and (to be rechecked in Phase 6.5) the cold-read agent in his Chrome. *Fallback,
   if a real phone check turns out to matter:* a non-production deploy in the **existing** Vercel project, whose
   generated preview URL Standard Protection keeps behind his login, never with `--prod`. *Was:* **Where the preview
   lives.**
   - (a) *Was recommended:* a separate Vercel project, `horizon-compact-preview`,** static files deployed by him with the
     CLI (as Phase 1.5 C5), Deployment Protection set to All Deployments with Vercel Authentication, `noindex`. Free
     (§2); only his Vercel account can open it; a phone can open it after his login; Phase 6.5's cold-read agent runs
     in his signed-in Chrome.
   - (b) **Chosen:** local only (`vite preview`). Nothing deployed at all, but no
     link-preview testing and harder phone checks.
3. **DECIDED 2026-11-09 (his): (a).** *Was:* **How the public URL keeps the placeholder while `web/` becomes the explorer.**
   - (a) **Recommended: two build modes,** Deploy pinned to `placeholder` until Phase 6.5's go-live commit changes one
     line, the explorer data outside `web/public/`, and the placeholder-mode check in `check-dist.mjs` and Vitest (§6).
     A teardown re-apply in between still rebuilds the placeholder.
   - (b) Turn Deploy's site half off until go-live. Simpler, but the public page then cannot be redeployed (after a
     teardown, for one) without the explorer.
4. **DECIDED 2026-11-09 (his): (a).** *Was:* **Grid memos.**
   - (a) **Recommended: his S3 run of `hc site memos` in this phase** (§5.3), the extract committed and tied to the
     manifest by sha256. The memo reader is built on real memos, and Phase 6.5's full-text publication later lets
     anyone check the extract.
   - (b) Wait for Phase 6.5's full-text publication and build the memo reader from it. One source fewer, but the
     memo reader waits for the next phase.
5. **DECIDED 2026-11-09 (his): (a).** *Was:* **Real-case memos that repeat scale-free figures from a withheld dossier.**
   *Widened 2026-11-09 (his, §22):* the count also covers distinctive **words** shared with the withheld text,
   after a published memo was found repeating a product line and a program name; (c) is the expected choice.
   - (a) **Recommended: count first, then decide.** A local script (Claude writes, he runs; it reads the private
     dossiers) counts, per case and model, the published memos that contain a percentage, rate or other unscaled
     figure that also appears in the case's withheld dossier, and writes only the counts to the repository. With the
     counts in hand he chooses, in this doc, between showing the memos as Phase 5.5 published them and holding those
     memos from the site (they stay in the repository, which cannot be undone).
   - (b) Show them as published; Phase 5.5's scan stands. The exposure is weak and already public.
   - (c) Hold every real-case memo from the site. The safest, and it loses the memo reader for the cases entirely.
6. **DECIDED 2026-11-09 (his): (a).** *Was:* **Per-view link previews and share cards.**
   - (a) **Recommended: a small HTML file per path, written after the build, each with its own `og:` tags, and a card
     per path drawn as SVG and rasterized by `@resvg/resvg-js` in the build** (§10). No new runtime dependency; the
     cards are generated from data, never committed as images.
   - (b) The same, with `satori` drawing the cards from JSX. More flexible layouts, one more dependency.
   - (c) One card for the whole site. Simplest, but a scenario view's link would travel without its own numbers.
7. **DECIDED 2026-11-09 (his): (a).** *Was:* **Which scenario the guided story walks.**
   - (a) **Recommended: `s1`, the first in protocol order,** fixed now, before any design work and without regard to
     its result; the main model in the walk, the second model beside it at the same size; the other three scenarios
     in beat 6.
   - (b) All four scenarios walked in turn. Even-handed, but four times as long.
8. **DECIDED 2026-11-09 (his): (a).** *Was:* **The explorer-data output.**
   - (a) **Recommended: committed, and CI re-runs the builder and fails on any difference** (§5).
   - (b) Generated in the build only. Less in the repository, but no reviewable diff when a view's data changes.
9. **DECIDED 2026-11-09 (his): (a).** *Was:* **The version at the close.**
   - (a) **Recommended: `0.6.0`**, as Phase 2 decision 4's rule now runs in order.

## 14. Order of work

1. **[done 2026-11-09: the doc approved (his); the scope doc's dated note; ROADMAP and KNOWN-GAPS]** **[Claude]** Step 0: this doc approved; the scope doc's dated note pointing to §0; KNOWN-GAPS.
2. **[built 2026-11-09 by Sonnet, §21; reviewed by Opus, §21a]** **C1, the explorer-data builder** (§5) with tests and its committed output; the CI
   re-run check.
3. **[his runs]** **The grid memo extract** (decision 4; `web/explorer-memos/`, §5.3's note) and **the real-case
   count** (decision 5, widened: `hc case echoes`, §22); his choice on decision 5 recorded. **C2** commits both.
   **[count done and decision 5 settled 2026-11-09, §22; C2's code built 2026-11-09 by Sonnet, §23; Opus review and
   his run of `scratch/p6-c2-memos.sh` pending]**
4. **[Claude builds, his picks]** **The previews** (§7): form, then palette, then layout.
5. **[Sonnet builds, Opus reviews]** **C3, build modes and the shell:** the two modes, the placeholder-mode check, the
   paths and their HTML files, the local preview script.
6. **[Sonnet builds, Opus reviews]** **C4, the scenario view and the section for results against the thesis.**
7. **[Sonnet builds, Opus reviews]** **C5, the memo reader, the real cases and the studies.**
8. **[his]** **The words** (§11): his titles and sentences; the templates and labels approved word for word.
9. **[Sonnet builds, Opus reviews]** **C6, the guided story.**
10. **[Sonnet builds, Opus reviews]** **C7, the share cards.**
11. **[his, Claude reading]** **The review against §12** on the preview, both widths, both modes; the number-trace
    script per view; fixes before the close.
12. **[Claude]** **C8, the close:** the DoD audit, the version (decision 9), `ROADMAP.md`, `KNOWN-GAPS.md`.

## 15. Definition of done, and the proof of each

| Scope DoD (as read through §0) | Proof |
|---|---|
| 1. Every view, the guided story and the share cards built and running on the preview, reading only precomputed data | the local explorer build; the module graph test (no fetch outside the site's origin) |
| 2. The public URL still shows Phase 1.5's placeholder | the placeholder-mode check; the public page on the close day, byte-identical to `2227a26`'s build |
| 3. The palette passed the validator in both modes; nothing by color alone; the story works with reduced motion and at phone width | the validator's output; `axe-core`; the review notes, step 11 |
| 4. Every template and label approved word for word; his words for the landing question, the scope sentence and the titles in place | this doc's words section; `copy.ts` |
| 5. Every number on the preview traces to the published JSON, on a sample per view | the number-trace script's output |
| 6. `make check` and CI green; every commit through the guard | CI and Deploy run ids |
| *Added:* 7. The explorer data is reproduced byte for byte by the builder from the committed results files | the CI re-run check |
| *Added:* 8. Every case surface carries its exploratory label and both matcher notes where their condition holds (closes KNOWN-GAPS OPEN 2026-10-31 for this phase's half) | the builder's tests; the cases view |
| *Added:* 9. The section for results against the thesis is filled by decision 1's rule, stated on the page | the rule's test; the section |
| *Added:* 10. Decision 5's counts are recorded and his choice applied | the counts file; the cases view |

## 16. Cost

**No model call.** AWS: the memo extract reads about 2,290 objects from S3 once (well under a cent); the explorer is
not deployed to AWS in this phase. **Vercel:** nothing new (decision 2). **GitHub Actions:**
free for a public repository.

## 17. Genuinely uncertain

- **The JavaScript budget.** React is most of today's 74 KB; the explorer's views and story may push past 100 KB
  gzipped. If they do, the views split by path (one chunk each), and the budget is checked per path, not raised.
- **Whether decision 1's rule reads cleanly on every scenario.** Settled in §19: each scenario's direction is taken
  from the protocol's definition of its outcome; S4's is the one a reviewer could dispute, and the page says so.
- **How long the previews take.** Three decisions, three to six previews each, capped, in a fixed order (the scope
  doc's own mitigation).

## 18. Rules this phase must not break

The scope doc's list, unchanged, and: no number computed outside the frozen analysis; no official data in the
placeholder build; no real-case memo text in any tracked doc; the exploratory label on every case surface; Claude
never reads an official record directly (the memo extract is his run); nothing at the public URL changes in this
phase.

## 19. The rule for the section of results against the thesis (decision 1)

Written 2026-11-09 by Claude (Opus), at his instruction to write it **as if a skeptical AI reviewer will audit it**.
Approved with this doc; applied by the explorer-data builder (§5), never by hand.

**Disclosed first, because a reviewer will ask:** the rule was written after the reveal of 2026-10-15, and Claude
printed every grid verdict on 2026-11-09 while drafting this doc, before writing the rule. Its *inputs* are all dated
before the results; its *wording* is not. Two things limit what that could buy: every term below is taken from a
pre-results document and cited, and **no alternative rule was tried against the data**. The list is whatever this
rule yields, empty included, and the builder applies it for the first time after this doc is committed.

**The thesis, as written before the results.** `planning/00` §4 principle 3 (2026-10-02): "If the long-horizon CEO
also cuts payroll, that ships." Its §5.1 "how the grid reads" (2026-10-03): a longer horizon or a wider set of people
who count is expected to make the model cut less, and "everything cuts" is "the result against the thesis." Its
origin record (9/28): "executives use new capability to cut payroll rather than to expand what is possible."

**What the rule reads:** each **primary** comparison's `final_verdict` and `difference` in the two **official grids**
(`experiment/results/prereg-v1/<model>/grid-*.json`), model by model, never pooled. The secondary comparison (A vs D)
and the thinking sub-study are not read: the protocol names A vs D secondary (§1.5), and the sub-study is not the grid.

**In each primary pair the second objective is the one the thesis expects to cut less** (protocol §1.4-§1.5; the
difference is "the first named minus the second"):

| Pair | What changes | Expected to cut less |
|---|---|---|
| A vs C | the horizon, shareholders only | C (twenty years) |
| A vs B | who counts, four quarters | B (all stakeholders) |
| C vs D | who counts, twenty years | D (all stakeholders) |
| B vs D | the horizon, all stakeholders | D (twenty years) |

**"Cuts more," scenario by scenario,** from each primary outcome as the protocol defines it (§4's table):

| Scenario | Primary outcome (protocol) | Cuts more means | So the second objective cut more when the difference is |
|---|---|---|---|
| S1 | share kept: people on either retraining path, over 125 | a lower share kept | **above zero** |
| S2 | share borne by the workforce: roles eliminated plus wages or hours cut, over the shortfall | a higher share | **below zero** |
| S3 | close rate: the share of runs that choose close | a higher rate | **below zero** |
| S4 | fund rate: the share of runs that fund the ten-year program | a lower rate (declining to expand) | **above zero** |

**S4 is the one reading a reviewer could dispute,** because S4 offers a cut and an expansion rather than a cut alone.
It reads the origin record's "rather than to expand what is possible" and §5.1's "A cuts, C expands"; the page says so
beside any S4 entry.

**A comparison is listed when:**

1. its verdict is **no split**: changing the horizon or who counts did not change the decision on that outcome, by
   the protocol's own threshold; or
2. its verdict is **split** and the difference has the sign in the last column: the objective expected to cut less
   cut more.

**Not listed, and shown at full size elsewhere** (the scenario views and the story): a split in the expected
direction, and every **inconclusive** or **not assessable** verdict, which are not against anything (protocol §1.5:
inconclusive "is reported as a result, not omitted"). "Everything cuts" is not given an absolute threshold, because
none was written before the results and one chosen now would be chosen after them; a scenario on which every primary
comparison is "no split" is listed whole, which is the nearest reading that needs no new number.

**What each entry shows:** the model, scenario and pair; the verdict with its difference, 99.7% interval, valid runs,
wordings kept and dropped; which clause of the rule listed it; and the protocol's pre-registered sentence for that
pattern, quoted as written. **For C vs D** the entry also quotes the protocol's other reading, since a "no split"
there is against the project author's thesis and "consistent with the statement's claim" (the Roundtable's) at once,
and the page says both.

**On the page,** above the list: the rule in plain words, its sources with their dates, the date the rule was written,
and the disclosure above. The words around it are his (§11); the rule's own text is Claude-drafted and approved by him
word for word, like the templates.

**Tests:** fixtures for each clause and each scenario's sign; an inconclusive and a not-assessable verdict never
listed; a secondary comparison never read; the two models never merged; the builder's list for the real files written
once, committed with C4, and reproduced byte for byte by the CI re-run.

## 20. What a skeptical reviewer would dig for, and where the site answers it

His instruction (2026-11-09): prepare as if a reviewer sends an AI such as GPT-6 Astra to do a skeptical review. This is
the list such a review would most likely produce, from the repository as it stands, with where each is answered. Items
marked **6.5** are the methods page's; the explorer links to them.

| What it would find | Where it is answered |
|---|---|
| The section of results against the thesis was filled by a rule written after the results | §19 on the page: sources dated, the disclosure, no alternative rule tried, and the list whatever it yields |
| The real cases were selected after the pre-registered rule found none, with the criteria relaxed step by step | the exploratory label on every case surface; the public selection logs (`evidence/phase-5/selection-public.json`, `exploratory-public.json`); **6.5** tells the story in order |
| All five cases are plant closures: no retool and no AI-workforce case, though `ROADMAP.md` §1 lists "three real cases including an invest or retool case" among what is never cut | the cases view states the shortfall from `cases.json` (`short_by_type`: retool 2, ai 1) beside the cases; **6.5** gives the history (KNOWN-GAPS CLOSED 2026-10-27, "two of three types short") |
| Every case reading is "no good match", so the cases add no evidence | the cases view says so first, and frames the cases as the protocol applied, never as validation |
| The matcher's five-way tie and the one-line reading (KNOWN-GAPS OPEN 2026-10-31) | both notes on the cases view (DoD row 8) and **6.5** |
| No case dossier is published, so no case can be re-run | the cases view; **6.5**'s re-run section; `cases.json` gives each reason |
| Published real-case memos repeat unscaled ratios from withheld dossiers | decision 5's counts and his choice, recorded here and on **6.5** |
| Repeats per cell differ (Haiku's `s2` ran 6 a cell, its other scenarios 20) | every number shows its own n; the scenario view says repeats were set by protocol §8.2 from each model's pilot, before the grid |
| Several verdicts rest on one or two wordings, after drops for failures over 10% | the verdict line names its wordings and its drops (the analysis's own `headline`); failure rates per cell on every scenario view |
| One gpt-oss comparison is not assessable | shown in place, at full size, never hidden |
| Sixteen comparisons per model invite false positives | the interval is Bonferroni over the family (99.7%), stated beside the first verdict a reader meets and on **6.5** |
| The model set changed from the plan (Bedrock was blocked) | **6.5**: the fallback set was fixed on 2026-10-11, before the tag on 2026-10-13 |
| The harness was built with Claude and the main model is Anthropic's | **6.5** says so plainly; the second family is not Anthropic's and is shown at the same size |
| The images that ran Phase 4 have expired from ECR, so a run cannot be repeated on identical bytes | **6.5**, from KNOWN-GAPS (closed 2026-11-04): the records keep every digest; the code is pinned by the tag and the archive |
| A case first disclosed before the main model's training cut-off | the case's own exploratory label states it, and the knowledge probe's result |
| The thinking sub-study covers `s1` only | labeled as a sub-study on `s1` wherever it appears |
| The planning and phase docs were drafted by Claude | `docs/planning/README` says so (his words); **6.5** repeats it |
| A number on the site differs from the frozen output | none can by construction (§5); the CI re-run and Phase 6.5's re-scoring check prove it |

**An actual skeptical review is possible, and cheap.** The `08` design review used a non-Anthropic model through
OpenRouter for $1.34 of his cash (2026-10-03). The same kind of read on the finished site and the methods page fits
**Phase 6.5**, before go-live, as a check on this list; its cost and the model's availability are rechecked live then,
and it is his call, from his cash.

## 21. As built, C1: the explorer-data builder (2026-11-09, Sonnet; Opus review §21a)

Built from `scratch/p6-c1-build-prompt.md`. No AWS call, no S3 read, no model call; it reads only committed files.
Not committed (his commit).

**What was built.**

- `src/horizon_compact/site/explorer.py` (new, run code): `build_explorer_data(results_root) -> dict[str, str]`,
  `write_explorer_data(files, out) -> Path`, `explorer_data_matches(files, out) -> bool` (a read-only helper the
  command uses to say "unchanged"), and `ExplorerDataRefusal`. Standard library only (`tomllib` for
  `objectives.toml`). Compact JSON, `ensure_ascii=False`, `allow_nan=False`, key order as built, one newline.
  Integers above 2**53 - 1 are written as decimal strings (only the case files' 39-digit bootstrap seeds are).
- `hc site explorer [--results <dir>] [--out <dir>]` in `cli.py`, defaulting to `experiment/results` and
  `web/explorer-data`. Prints each file with its byte count, the file count, the total, and `unchanged` when the bytes
  were the same (in that case each line starts `kept`, not `wrote`). A refusal prints `refused: ...` and exits
  `REFUSED_EXIT`. It is not on the deny list.
- `tests/test_site_explorer.py` (new, 98 tests): fixtures for each refusal, each clause of §19 on each scenario's sign
  and each pair, the notes true and false, the writer, the command, and the real-data group below.
- `web/explorer-data/` (new, committed output, 21 files) and `web/.prettierignore` (`explorer-data/`, with its reason).
- Nothing in `experiment/`, `infra/`, `.github/` or `web/src/` changed; no frozen file was touched.
  `hc protocol check`: ok.

**Output, measured 2026-11-09** (bytes; 21 files, **1,441,167 in all**; the largest, 292,118, is far under the large-file hook's 1,024 KB):

| Files | Bytes |
|---|---|
| `index.json` | 24,992 |
| `grid/haiku-5-5/` s1, s2, s3, s4 | 102,458; 97,977; 139,133; 281,038 |
| `grid/gpt-oss-openrouter/` s1, s2, s3, s4 | 101,804; 169,978; 141,087; 292,118 |
| `thinking/haiku-5-5/s1.json` | 42,200 |
| `cases/index.json` | 5,838 |
| `cases/<label>/<model>.json`, ten files | 3,909 to 4,570 |

**Real-data facts the tests assert** (all against the real output): every case's Haiku `primary` reading has
`all_distances_equal` true; `closure-19`'s `u1` reading has `one_observable_line` true for both models (one line);
every case result is exploratory with its label; all ten case files hold their seeds as strings and no other number
above 2**53 - 1; the three sources' sha256 values in `index.json` match the files; the output holds no memo, no `arn:`
and no `horizon-compact-results-`. The committed `web/explorer-data/` is reproduced byte for byte by a fresh build,
and holds no other file (§15 row 7; it runs inside `pytest`, so CI needs no change). A second build is
byte-identical. A walk over every leaf (measured 2026-11-09: 81,870 in the grid and thinking files, 1,528 in the ten case files, 926 in the verdicts) finds each value in the
grid files, the case files, the verdicts and the entries equal to its source value, with the one allowed change.
A separate, plainer recomputation of §19's list from the source files agrees with the builder's.

**`against_thesis`, counts only** (rule `Phase 6 IMPLEMENTATION doc §19, 2026-11-09`):

| Model | `no_split` entries | `reversed_split` entries | scenarios listed whole |
|---|---|---|---|
| `haiku-5-5` | 2 | 0 | 0 |
| `gpt-oss-openrouter` | 0 | 0 | 0 |

**Checks:** `make check` green: Python 3,347 tests (3,249 before this step, +98), Vitest 37, strict mypy, root cap,
paths-check, doctor. `uv run hc site explorer` run once (wrote 21 files) and again (`unchanged`).

**What did not fit, and what was done instead.**

1. **A case result's `sweep_id` cannot equal its filename** (the files are `<model_key>.json`, the sweep id is
   `case-<model_key>-<hex>`). The check is: `model_key` equals the filename, `sweep_id` matches
   `case-<model_key>-<hex>`, and `case` equals the label. The grid and thinking files do check `sweep_id` against
   the filename stem.
2. **Refusals added beyond the list** (all pass on the real data; each has a test): a case result that disagrees
   with `cases.json` on `exploratory` or its label; a scenario whose outcome, kind or threshold differs between
   official files; a reading without five distances; an unknown verdict value; a "split" with no difference at
   all (as well as zero); exactly one thinking file (not "at most one"); a symbolic link in a `prereg-v1/` folder
   or in the output folder.
3. **Objective E** is carried as `{"id": "E", "who": null, "when": null}`, not with the keys left out, so the front
   end reads one shape.
4. **`verdicts` is a list** of `{model_key, sweep_id, scenario_id, comparisons}`, grids only. The thinking
   sub-study's comparisons are in its own file, so no view can mix it with a grid by accident.
5. **`cases/index.json` leaves out** `probe_set` and `content_sha256`, which the prompt's list did not name.
6. **A hazard for C2, which was not decided here.** §5.3 puts the grid memo extract in `web/explorer-data/memos/`
   (`.jsonl`). The writer replaces `explorer-data/` whole and refuses an existing folder that holds anything but
   `.json` files in its layout, as decided; so once `memos/` is there, `hc site explorer` will **refuse** (nothing is
   deleted), and the reproduction test, which says the folder holds no other file, will fail. C2 has to choose:
   put the memos in a sibling folder (such as `web/explorer-memos/`, with its own builder and `.prettierignore`
   line), or extend the layout and the test to include `memos/`. Recommended: the sibling folder, since the writer's
   "replace whole" is exactly what keeps stale files out of the results files.
7. **The tests count the real leaves as a floor** (more than 20,000 in grid and thinking, 500 in the case files,
   600 in the verdicts; well under the measured counts above), so a change that silently stopped walking would fail.

## 21a. Opus review of C1 (2026-11-09)

**Passed, with one test added; no change to the builder or its output.**

**Reproduced, not taken on report:** `make check` green on Claude's own run (Python 3,347 before the added test and
3,348 with it, Vitest 37, strict mypy, root cap, paths-check, doctor); `hc protocol check` ok; `uv run hc site explorer` prints
`unchanged` (21 files, 1,441,167 bytes). The name guard, run by hand over the 26 new and changed files (nothing
staged), finds nothing.

**The rule, checked against the frozen analysis, not the prompt.** `difference` is the first named minus the second
(`analysis/intervals.py`: `welch_difference` and `newcombe_difference` estimate first minus second;
`analysis/verdict.py` passes `cells[first], cells[second]`). S3 counts `close` and S4 counts `fund`
(`analysis/outcomes.py`), so §19's four signs (s1 +1, s2 -1, s3 -1, s4 +1) read correctly. **A separate recount from
the two grid files, written without the builder's code, gives the same list:** Haiku `s1` B vs D and `s3` B vs D, both
`no_split`; no reversed split in either model (every split goes the way the thesis expects); no scenario whole.
Counts only, as §19 says; what they mean is the page's, in his approved words.

**Nothing new is exposed.** Every input is already tracked in the public repo; the output carries no memo text (the
longest string is the exploratory label) and no field that is not in a tracked results file.

**The one change: a test.** The leaf walk covered the grid, thinking and case files, the verdicts and the entries, but
not `index.json`'s `models`, `scenarios` and `objectives` blocks or `cases/index.json`, which carry numbers too
(`alpha`, `threshold`, the shortfall counts). §5 asks for every number at its source path, so
`test_every_leaf_in_the_index_blocks_and_the_cases_index_is_the_source_value` walks them against the grid files,
`objectives.toml` and `cases.json`. Four mutations (a shortfall count, a model's alpha, a threshold, an objective's
`when`) each fail it.

**On §21's "what did not fit":** items 1 to 5 and 7 are accepted as built. **Item 6, the memo folder: decided (his,
2026-11-09), the sibling folder.** As recommended: the sibling folder (`web/explorer-memos/`) and a dated note on §5 and §5.3 when C2's
prompt is written, for a reason beyond §21's: the memo extract comes from his S3 run, so CI can never rebuild it, and
keeping it out of the folder CI reproduces keeps that check exact. C2 then also extends §6's placeholder-mode check
to the new folder and adds its `.prettierignore` line.

**Carried forward, not a C1 change:** `objectives` carries `who` and `when` but not the three wording templates or
the sealed one (`w2`). If a view shows the sentence the model read, the templates come from `objectives.toml` in a
later step, copied, not composed by hand.

## 22. Decision 5 widened: published real-case memos and their withheld dossiers (2026-11-09)

**What was found.** Writing step 3's scripts, Claude read the first published memo of closure-07 and found it
repeats terms from the case's withheld dossier: a product line, its abbreviation, a product category and a named
employee program, none of them in the case's published 98-character description. Counted on public files only, 140
of closure-07's 198 published memos hold at least one of the four (Haiku 50 of 74, gpt-oss 90 of 124). The terms
are not written in this repository. Phase 5.5's scan looked for names and held memos whose flagged words came from a
withheld dossier; these words were never flagged, so they passed. Finding 5 (§3) expected scale-free figures to be
the exposure; words are the larger one. KNOWN-GAPS (OPEN, then CLOSED 2026-11-09) tracks it.

**His decisions (2026-11-09), on Claude's recommendations:** (1) widen decision 5's count from figures to words,
percentages and other unscaled figures; (2) for the explorer, the expected choice is (c), holding real-case memos
from the site, at least for every case whose dossier is withheld (all five), with the counts and the reason shown in
their place; it is final once the counts are in; (3) the copies already in the repository: decided after the
counts. The grid memos (decision 4) are not affected: every one is about the fictional company.

**The count: `hc case echoes`** (`src/horizon_compact/caseprobe/echoes.py`; his to run, on the deny list, since it
reads the private dossiers). No model call, no AWS, no network. For each case it reads the dossier and scenario
from the appendix and refuses unless each hashes to the case's `case.lock`, so the text compared is the text the
model was given. It takes three kinds of token, after the memo scan's own `fold`: **words** (three or more letters),
**percentages**, and **other figures** of two or more digits (a figure written with `$` or followed by million,
billion, thousand or trillion is skipped, since dollar amounts are scaled, protocol §12.6). A token is
**distinctive** for a case when it is in the case's withheld text and in none of: the reference text (every
`.toml`, `.txt` and `.md` under `experiment/` outside `results/` and `cases/`: the fictional company, the protocol,
the reader briefs); the case's published description; and, for words only, every other case's published memos (a
word memos about other companies also use is ordinary business English). A published memo is counted for a kind
when it holds at least one distinctive token of it.

**It is an upper bound.** An ordinary word the reference text happens to lack is counted too; and a term the model
knew from training, but the dossier lacks, is not seen. The private report beside each case's dossier lists every
token with the runs that carry it, most frequent first, so he can judge which, if any, point toward the company.

**What is public:** `docs/phases/evidence/phase-6/memo-echoes.json`, written once: per case and model, the memos
published and held, how many carry a distinctive word, percentage or figure, how many carry any, and how many
distinct tokens of each kind; with the HEAD that counted, each dossier's and scenario's sha256 from `case.lock`,
each memo file's sha256 and the reference text's digest. A check refuses the file if it would hold any string that
is not a key, a label, a model key, the rule's name or a hash. The command prints counts only.

**His steps.** (1) Commit the code (the command refuses to run on uncommitted `src/`, so the HEAD it records is the
code that counted). (2) `uv run hc case echoes`. (3) Paste the printed table; Claude reads only that. (4) Open the
private report in each case's appendix folder and look at the top of each list: does any word, alone or with the
published description, point toward the company? (5) His choice on (2) and (3) above, recorded here. The counts file
rides in C2.

**The counts, his run (2026-11-09, about 11:35 AM, HEAD `705ea98`;
`docs/phases/evidence/phase-6/memo-echoes.json`).** Of **1,237** published real-case memos, **845** hold at least one
distinctive token (an upper bound; 263 more were already held by Phase 5.5's scan). Per case and model:

| Case | Model | Published | Held | With a word | With a percentage | With a figure | With any | Distinct words / percentages / figures |
|---|---|---|---|---|---|---|---|---|
| closure-07 | gpt-oss | 124 | 26 | 112 | 0 | 89 | 118 | 17 / 0 / 2 |
| closure-07 | haiku | 74 | 76 | 72 | 33 | 55 | 74 | 25 / 6 / 1 |
| closure-19 | gpt-oss | 150 | 0 | 4 | 0 | 0 | 4 | 4 / 0 / 0 |
| closure-19 | haiku | 147 | 3 | 91 | 17 | 0 | 94 | 17 / 2 / 0 |
| pre-11 | gpt-oss | 132 | 18 | 32 | 0 | 76 | 90 | 7 / 0 / 2 |
| pre-11 | haiku | 108 | 42 | 108 | 8 | 82 | 108 | 19 / 2 / 1 |
| pre-25 | gpt-oss | 136 | 14 | 109 | 0 | 71 | 122 | 16 / 0 / 2 |
| pre-25 | haiku | 145 | 5 | 141 | 1 | 101 | 145 | 22 / 1 / 1 |
| pre-224 | gpt-oss | 143 | 7 | 26 | 2 | 1 | 29 | 6 / 1 / 1 |
| pre-224 | haiku | 78 | 72 | 45 | 34 | 2 | 61 | 11 / 6 / 1 |

The distinct tokens are few (4 to 25 words, at most 6 percentages and 2 figures per case and model), so his read of
the private reports (step 4) covers every token, not a sample.

**His read and his choices (2026-11-09, about 12:05 PM).** He read all five private reports and found nothing that
points toward a specific company or plant. This is his judgment against the private longlist; Claude did not
check it, since checking would be the identification itself. On Claude's recommendations he chose:

- **The site: hold** (option (c)). The explorer shows no real-case memo text. The cases view shows, per case and
  model, the published and held counts from this file and the reason, in his approved words. His read rules out an
  obvious pointer, not a combined one: 68% of published memos echo dossiers withheld because their figures narrow
  the field to fewer than 20 filers, and the site would put them in front of readers. The memo reader keeps every
  grid memo.
- **The repository copies: leave them** as Phase 5.5 published them. They are write-once results; removing them
  from the current tree would not remove them from history; and this section, the counts file and KNOWN-GAPS
  (CLOSED 2026-11-09) disclose the finding.

Decision 5 is settled. C5 (the real cases) builds the cases view without memo text.

## 23. As built, C2 code: the grid memo extract, `hc site memos` (2026-11-09, Sonnet; Opus review pending)

Built from `scratch/p6-c2-build-prompt.md`. **No AWS call, no S3 read, no `terraform` command and no model call
was made**, and `hc site memos` and his script were not run. Not committed (his commit). The command reads official
records, so it is his to run and it is on the deny list.

**What was built.**

- `src/horizon_compact/site/memos.py` (new, run code): `build_memo_extract(reader, results_root, manifest_path,
  term_file, head, progress) -> dict[str, str]`, `write_memo_extract(files, out)`, `memo_extract_matches(files,
  out)`, and `MemoExtractRefusal`. The reader it is handed needs only `read(key, version_id)`; `S3RawReader`
  (Phase 1.5) has that and no write call. The file rules for which results files name the official sweeps are
  C1's: it imports `_read_prereg` and `_Grid` from `site/explorer.py` (private names, imported and not edited), so
  there is one rule for what an official results file is. `final_text` is imported from `caseprobe/memos.py` and a
  comment in the module says the two must read the same field.
- `hc site memos [--profile P] [--bucket B] [--out DIR]` in `cli.py`, with two hidden options (`--results`,
  `--manifest`) that only the tests use, as C1 has `--results`. Default `--out` is `web/explorer-memos`. It refuses
  uncommitted `src/`, `pyproject.toml` or `uv.lock` first (as `cmd_case_reident` does), then loads the term file
  (failing closed), and only then makes an S3 client. It prints the file count, runs, runs with text, total bytes
  and the largest file with its size, never a memo's text. A refusal prints `refused: ...` and exits `REFUSED_EXIT`.
- `.claude/settings.json` and `tests/test_claude_settings.py`: `hc site memos` denied in both forms, added to
  `READERS`, with a comment. `web/.prettierignore`: `explorer-memos/`, with its reason.
- `scratch/p6-c2-memos.sh` (his run, in the shape of `scratch/p15-step3-s3.sh`; `scratch/` is untracked).
- `tests/test_site_memos.py` (new, 54 tests, 4 of them skipped until `web/explorer-memos/` exists): see below.
- Nothing under `experiment/`, `analysis/`, `site/explorer.py`, `caseprobe/` or `web/explorer-data/` changed, and
  `docs/phases/evidence/phase-6/memo-echoes.json` is untouched (it rides in C2's second commit). `hc protocol check`: ok.

**What it reads, as decided.** The three sweeps the committed results files name (`grid-gpt-oss-openrouter-fe599ad2`,
`grid-haiku-5-5-0b99fabb`, `thinking-haiku-5-5-418caa9c`), prefix `official/company/<sweep_id>/`. Every manifest
entry under those prefixes is read once **by its recorded version id, as bytes** and refused unless its byte count
and sha256 are the manifest's: 4,860 objects, 97,159,462 bytes (the group totals in `raw-manifest.json`), about as
many reads as Phase 1.5's manifest run. Objects the frozen reader does not need (the sweep summaries, the
refusal-call files) are verified and then dropped; the manifest, every `final.json` and every `attempt-N.json` are
served to `read_runs` through an in-memory `RecordSource`, so one sweep's needed bytes (about 40 to 52 MB) are held
at a time. A pilot, awareness or case prefix is never listed, and a test records every key the fake reader was asked
for and compares the set with the manifest's three prefixes.

**The cross-checks** (each a refusal, each tested): the run count equals the manifest group's `final_objects`; per
scenario, objective and wording, the runs with a valid status equal that cell's `valid` in the results file (in
both directions, so a cell on either side alone is caught); every `descriptive.per_run` run is in the extract with
a valid status. **Added beyond the prompt:** the per-run entry's objective, wording and repeat must equal the run's,
and each cell must carry its scenario's id. These compare fields the frozen analysis copied from the same records,
so a refusal on the real data would be a finding and not a mismatch of representation.

**The output** is the prompt's: `<kind>/<model_key>/<scenario_id>/<objective_id>.jsonl` and `index.json`, one line
per run ordered by wording, repeat and run id, compact JSON with the key order the prompt gives. `files` in the index
is the sorted list of memo files. The writer is C1's (sibling folder, swap, refusal of any other name or any foreign
file, same bytes a no-op, the old folder put back if the swap fails).

**Size estimate (item 6).** The manifest gives each object's whole size, and an attempt record holds the request
and the raw response as well as the memo, so it cannot say how large a memo file will be; it gives only an upper
bound. Summing every attempt of the valid runs in a scenario-objective cell: the largest cell is 2,934.7 KB for
gpt-oss, 3,260.0 KB for the Haiku grid and 1,085.2 KB for the thinking sub-study, against the hook's 1,024 KB. By
that bound a file could pass the limit, so the split is built in, and **it applies on the real size, not on the
estimate**: a cell file over `MAX_FILE_BYTES` (1,000,000, under the hook's 1,048,576) is written as one file per
wording, `<objective_id>-<wording_id>.jsonl`, and a wording's file still over it is refused. Which cells, if any, are
split is therefore known only after his run (the command prints the largest file, and the index's `files` lists what
was written). The committed-output test fails if any file in `web/explorer-memos/` is over the limit. The hook's
limit is not raised and no exclusion was added to `.pre-commit-config.yaml`.

**What did not fit, and what was done instead.**

1. *A fixed layout.* The prompt's item 6 splits "that file" if one could pass. Since the estimate cannot say which,
   the split is conditional on the actual size (above). A consumer (C5) must read the paths from `index.json`'s
   `files`, not build them from the cell's name.
2. *The `arn:` test as a bare substring.* A bare `arn:` also matches "learn:" and "warn:", which a memo can
   contain, and a refusal there could not be worked around. The test is `arn:` with no letter or digit before it;
   `horizon-compact-results-` is still a bare substring. Tested both ways. The prompt's other leak test (a bare run
   of twelve digits) is not made, as instructed.
3. *`ensure_ascii=False` with nothing else changed.* U+0085, U+2028 and U+2029 are written as `\u0085`, `\u2028` and
   `\u2029`. They parse back to the same character, so no memo is changed; written raw, they cut a line in two for
   any reader that splits on them (Python's `splitlines`, among others). Tested: a memo holding all three
   round-trips and the file holds none of them raw.
4. *Reply-text and refused runs.* They are in the extract with their status and the text of their final attempt
   (`source` `reply_text`), as the prompt says, and the tests cover both.

**Tests** (`tests/test_site_memos.py`, fictional canary sweeps, runs and memos, a fake in-memory reader): each
refusal (hash, size, a missing manifest entry, group or version, a cross-check, a name-guard term, an `arn:`, the
bucket prefix, an object that is not UTF-8, an unexpected results file); that the read goes by the recorded
version (the fake serves other bytes for any other version id, and a reader that asks for another is refused); a
run with no text; a reply-text run; a run whose final attempt is the second; the ordering (and that the fixture is
not already sorted); the split and its refusal; the writer's swap, no-op, stale file, foreign file, leftover and
failed swap; the term-file refusal with a canary term (the message names the run and not the term, and the command
prints neither the term nor a memo); and the command end to end. **Four tests skip until `web/explorer-memos/`
exists** and then run in CI: every line's `final` and `attempt` key and sha256 are in `raw-manifest.json`; the
per-cell valid counts and the run counts equal the committed results files; no file is over the limit; no `arn:`
or bucket name. Two of the tests were checked by breaking the code (the hash check removed; the read made by another
version id): each failed as it should.

**`make check`: green, 3,417 passed and 4 skipped** (the 4 are this file's committed-output tests), the web tests
37 passed, `check-dist: ok`, `doctor` ok. `hc protocol check`: ok.

**His steps.** (1) Opus reviews this section and the code. (2) Commit the code (`phase 6: c2 memo extract builder`).
(3) `scratch/p6-c2-memos.sh` (about 4,860 reads, about 97 MB; paste the printed counts and the largest file). (4)
Commit `web/explorer-memos/` with `docs/phases/evidence/phase-6/memo-echoes.json`. If the run refuses, the message
names the object or the run and never a memo or a term; a refusal on a cross-check is a finding to report, not
something to code around. *(Steps amended by §23a: the counts file moves into step 2's commit.)*

## 23a. Review of C2's code (2026-11-09, Opus)

**Passed. One test added and one docstring; the builder's behavior and its output are unchanged.** Read: the module,
the command, the tests, the deny-list lines, the run script, and this section against the build prompt's eight points.
`make check` re-run before the additions: green, 3,417 passed and 4 skipped, Vitest 37.

**Checked against the real committed files, not only the fixtures** (the fixtures cannot show these):

- The three official prefixes do not overlap the awareness groups, which sit under `official/company/awareness/`.
  The manifest's `final_objects` are 1,200 (gpt-oss grid), 990 (Haiku grid, S2 at 6 repeats) and 100 (thinking),
  and each results file's `attempted` totals agree. The frozen `build_results` refuses unfinished runs as this
  extract does, so a sweep the analysis read cannot be refused here for that.
- Every `descriptive.per_run` entry in the three results files carries `objective_id`, `wording_id` and an integer
  `repeat` (2,241 entries), so §23's added cross-check compares fields that exist; per scenario, the per-run count
  equals the cells' `valid` sum. The committed-output tests' valid statuses equal `VALID_STATUSES`.
- `_NEEDED` keeps exactly the keys the frozen reader's `_RUN_KEY` and its `manifest.json` read use.
- The three escaped separators are the only line breaks `str.splitlines` knows that `json.dumps` writes raw; the
  others are control characters, which it already escapes.

**Added: the scan's reason, pinned by a test.** The commit guard reads a file as written, where a line break in a
memo is backslash and `n`. A term just after a break then has a letter before it, and a two-word term split by a
break is no longer split by whitespace, so the guard misses both. The extract's scan of the decoded memo catches
both, so for these files it is the protection that counts, not the hook. A docstring on `_scan_names` says so, and
`test_the_scan_reads_the_memo_because_the_commit_guard_cannot_see_past_an_escape` (two cases) shows the guard
finding nothing in the written line and the extract refusing. Checked by breaking the scan: both cases failed, and
passed again on restore.

**Accepted as departures:** the conditional split (C5 reads paths from `index.json`'s `files`), the `arn:` edge
rule, the escaped separators, and the extra cross-check, each for §23's reason.

**Noted, no change:**

1. The scan uses the term file only. A model naming some other real company as an analogy in a grid memo would be
   published, as Phase 5.5 published case memos that passed its scan. The term file is the rule-zero mechanism.
2. `site/memos.py` imports C1's private `_read_prereg` and `_Grid`, so there is one rule for what an official results
   file is. Acceptable inside the package; a rename in `explorer.py` breaks this at import, loudly.
3. The command checks that `src/`, `pyproject.toml` and `uv.lock` are committed, not the results files or the raw
   manifest it reads. The committed-output tests compare the index's manifest sha256 and every count with the
   committed files, so a local edit to either would fail `make check` before the extract could be committed.
4. The four committed-output tests have only run on nothing. `make check` after his run and before the extract's
   commit is their first run, so a fault in them shows locally, not as a red check.
5. The extract's commit changes `web/`, so Deploy runs its site half. `web/explorer-memos/` is not in Vite's input and
   is not in `dist/`, so the sync should be the same 8 placeholder files.

**His steps, amended.** (1) Commit the code with the counts file, which nothing in the build depends on (`phase 6:
c2 memo extract builder`); push. (2) `scratch/p6-c2-memos.sh`; paste what it prints. (3) `make check`. (4) Commit
`web/explorer-memos/`.
