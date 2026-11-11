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

*Dated note, 2026-11-10 (C5):* the builder also reads the two awareness reports,
`docs/phases/evidence/phase-4/awareness-gpt-oss-openrouter.md` and `awareness-haiku-5-5.md`, by exact path, not by
prefix; and the case memo summaries under `experiment/results/cases/`, counts only.

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

**Dated note, 2026-11-11 (§14 step 8, his half):** at his request on this pass, Claude drafted every value in
`web/src/explorer/his.json` (the landing question, the scope sentence, the four scenario briefs, the title and
introduction of the section for results against the thesis, the memo, cases, held-memo and studies introductions, the
two studies titles, and each page's title and description), in plain language, with the watermark flag given. **He
approved them as written, 2026-11-11, about 4:04 AM.** They are Claude-drafted, and this note is the record of that.
The results section's title names the rule's source as "the project's starting expectation" (decision 1). `planning/06`
§6.4's name line has no field in `his.json`; it is C6's, in the guided story. `copy.test.ts`'s studies test now
requires those six values written, not placeholders. The labels half (`explorerLabels`) is recorded separately.

**Dated note, 2026-11-11 (§14 step 8, the labels):** Claude made a plain-language pass on the labels a reader sees
outside the closed details sections: 24 values in `explorerLabels` (`copy.ts`) and 4 in `againstWords.ts` ("the
thesis" became "the starting expectation", introduced once as the planning documents' "thesis", to match his title).
Each term the vocabulary rule asks to explain is explained in place or moved to the details: the Bonferroni correction
(now named only in the details key), the protocol, the pilot, the dossier, the rubric, the distance and its interval,
the tie-break, the tool call, the sha256. Every disclosure the matcher notes carried is kept (KNOWN-GAPS OPEN
2026-10-31). Three tests that pinned the old wording assert the same meaning in the new words. **He read `copy.ts` and
approved every label in it, changed and unchanged, and `againstWords.ts`, 2026-11-11, about 4:21 AM.** Still
unapproved: the four result-sentence templates in `sentences.ts`, which he has not yet been shown; C6's and C7's
words come with those builds.

**Dated note, 2026-11-11 (§14 step 8, the templates; step 8 done):** Claude showed him the four result-sentence
templates in `sentences.ts` one at a time, each with a real example from the committed data. **He approved all four,
2026-11-11, about 9:18 AM**, with two changes. `split`: "points" became "percentage points" (a business reader can
take "47 points lower" for "47% lower"). `not_assessable`: rewritten as one sentence, "X and Y can't be compared on
[outcome]: in every wording, more than 1 in 10 of one goal's runs failed or were refused." The old one said the same
fact three times and carried the analysis's internal reason text ("a cell over the 10% failure limit"); the claim
"every wording" holds because `analysis/failures.py` reaches that verdict only when every wording is dropped, and a
test checks it against every real not-assessable comparison. `no_split` and `inconclusive` approved as written. **For
C6:** he asked for ratio words ("half as many") where they hold. Not in a template, which fills itself for every
split; in the guided story, only where checked, saying the ratio comes from the plain averages and not from the
analysis, and by one rule applied to results in either direction (`planning/06` §1).

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
   **[count done and decision 5 settled 2026-11-09, §22; C2's code built 2026-11-09 by Sonnet, §23, reviewed by Opus,
   §23a, committed `75048aa`; his run of `scratch/p6-c2-memos.sh` done the same day, §23a; the extract rides in his
   commit `phase 6: c2 grid memo extract`]**
4. **[done 2026-11-10: form, palette and layout picked by him, §24-§24.2]** **[Claude builds, his picks]** **The previews** (§7): form, then palette, then layout.
5. **[built 2026-11-10 by Sonnet, §25; reviewed by Opus, §25a: passed, no code change]** **[Sonnet builds, Opus reviews]** **C3, build modes and the shell:** the two modes, the placeholder-mode check, the
   paths and their HTML files, the local preview script.
6. **[built 2026-11-10 by Sonnet, §26; reviewed by Opus, §26a]** **[Sonnet builds, Opus reviews]** **C4, the scenario view and the section for results against the thesis.**
7. **[built 2026-11-10 by Sonnet, §27; reviewed by Opus, §27a: passed after one change]** **[Sonnet builds, Opus reviews]** **C5, the memo reader, the real cases and the studies.**
8. **[done 2026-11-11: his words, the labels and the four result-sentence templates approved, §11's dated notes]** **[his]** **The words** (§11): his titles and sentences; the templates and labels approved word for word.
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

**As run (2026-11-09).** (1) Committed `75048aa` (his), pushed; CI `42682850981` and Deploy `42682850610` green.
(2) His run, about 1:55 PM, HEAD `75048aa`: no refusal, so no memo held a term-file term and every object, count and
cross-check agreed. **46 files** (45 memo files, one per scenario and objective cell: 20 gpt-oss, 20 Haiku grid,
5 thinking, none split, plus `index.json`), **2,290 runs**, **2,280 with text**, 4,426,213 bytes; the largest file
`grid/haiku-5-5/s1/C.jsonl` at 137,465 bytes, far under the limit (§23's upper bound was about 20 times the real
size). By status: gpt-oss 1,158 `valid`, 3 `valid_rescaled`, 33 `schema_invalid`, 2 `sum_mismatch`, 2
`no_tool_call`, 1 `truncated`, 1 `unexpected_stop` (the 10 runs without text are among these); Haiku grid 980
`valid`, 10 `sum_mismatch`; thinking 100 `valid`. The valid counts (1,161, 980, 100) equal the results files'
per-run counts. (3) Claude's `make check` with the extract present: green, **3,423 passed, 0 skipped** (the four
committed-output tests' first run), Vitest 37, `check-dist: ok`, `hc protocol check` ok. (4) His commit next.

## 24. Step 4, the previews: decision 1, chart form (2026-11-10)

**Built (Opus, `dataviz` loaded first):** six throwaway static pages in `scratch/p6-previews/` (untracked), from the
committed `web/explorer-data/` (Haiku 5.5 S1 and S3, gpt-oss-120b S1, the comparisons of all four Haiku scenarios),
captured headless (chrome-headless-shell 1234, over the DevTools protocol) light and dark at 1280 and 390: no console
error, no page-level horizontal scroll in any of the 24 captures. Pages 1-5 are §7's candidates (i)-(v); page 6 was
added on his reading of them. Palette provisional (§7 decision 2 owns it): `planning/06` §7.2 rule 1's scheme, four
hues run through the skill's validator in both modes over all pairs (band, chroma, CVD and normal-vision pass;
contrast WARN, relieved by visible labels), E in the site's muted gray. Every label Claude-drafted and unapproved.

**His reading of (i)-(v), 2026-11-10, about 7:47 AM:** hard to understand, any of them, without a finance or
statistics background. Claude's read: the five were built to §7 as written, in a statistician's register (intervals,
thresholds, differences), and a reader who has run the experiment and cannot read them cold is evidence that most
visitors could not either. Easiest: (iv) the unit chart and (i) the strip; hardest: (iii), which Claude had
recommended.

**Page 6, the simpler version:** one mark for both kinds of decision, **a dot is one run**: on a line from "none
kept" to "all 125 kept" for a share scenario (S1), grouped under the choice made with "n of 60" for a choice scenario
(S3). No ticks, no intervals, no threshold band. The goals by plain names, their literal descriptions listed once at
the top. Under each chart, "What the runs show": one plain sentence per comparison, the Roundtable pair first, each
with its run counts and the official verdict word beneath. Sentence numbers are the comparison's `difference`,
absolute, rounded down to whole points (display formatting only).

**His pick, 2026-11-10, about 8:18 AM: page 6.** On Claude's list of what it would still fix: repetitive sentences
can be fine (his read); whether "points" reads to a general reader, and the plain goal names against `planning/06`
§6.2 (letters and literal descriptions), are open and are word questions for §11, not form.

**Found building the previews (both bear on the build, neither changes his pick):**

1. **§7 (iii) misstates the verdict rule.** It says an interval outside the band reads "split". Protocol §6.3: a
   split needs the interval to exclude zero **and** the difference to be at least the threshold on the same side.
   Haiku S2 A vs B (interval +2.0 to +43.2, threshold 10) is a split whose interval crosses the band's edge. Any
   interval view draws the protocol's rule, and the verdict word stays the authority: the floor and the constant
   check (§6.5) are not geometry.
2. **The results carry no per-objective mean or interval for the primary outcome.** The intervals are on
   differences; per-wording means exist only inside the comparisons' `per_wording`, so E, in no comparison, has
   none. A per-row mean or interval would be computed in the front end, which §5 forbids. Page 6 draws neither.
3. A preview header first hard-coded "60 per objective"; gpt-oss-120b S1 has 292 valid of 300 and an A vs B of 40 v
   39. Every count on the site is read from the data, never written in.

**Where the precise views live: decided 2026-11-10, about 8:31 AM (his, as Claude recommended).** Page 6's form is
what every reader sees. Under each decision, a "See the details" section, **closed by default**, holds the comparison
interval chart ((iii), drawn to protocol §6.3's rule) and the full allocation ((ii), small multiples), so a "no split"
always has its full allocation one click away and a reviewer can check every verdict against its interval.

### 24.1 Decision 2, palette (2026-11-10)

**Rule kept:** `planning/06` §7.2 rule 1, hue for who counts (warm for shareholders, blue for everyone with a stake),
lightness for horizon (lighter for four quarters, darker for twenty years), E in the site's muted gray (`--muted`).
**Searched, not eyeballed:** `scratch/p6-previews/search.mjs` steps lightness and chroma per hue pair and keeps only
palettes the `dataviz` validator passes over **all pairs** (band, chroma floor, CVD at the target of 8, normal-vision
floor) in that mode, refusing out-of-gamut colors rather than clipping them. **Only warm-against-blue pairs pass in
dark mode:** purple and teal, gold and indigo, pink and teal and orange-red and cyan fail there (dark teal cannot
reach the chroma floor inside the dark band; the band is too narrow for two lightness steps of some hues); plum and
green was dropped as near the banned red-green pair. Three candidates, each applied to page 6 and captured light and
dark at 1280 and 390 (no error, no horizontal scroll): A amber and blue (hues 70 and 255), B orange and blue (55 and
250), C muted amber and blue (65 and 250, chroma near the floor).

**Flagged, not checkable by the validator:** a red-leaning warm for shareholders against blue for everyone else can
read to a US reader as a party pairing, which is moral color by another route. B is nearest red; A is furthest.

**His pick, 2026-11-10, about 8:53 AM: A, amber and blue** (as Claude recommended).

| Objective | Light (surface `#f6f2e9`) | Dark (surface `#0f1520`) |
|---|---|---|
| A, shareholders, four quarters | `#daa668` | `#b68446` |
| B, all stakeholders, four quarters | `#5fa1f3` | `#4f91e2` |
| C, shareholders, twenty years | `#81520a` | `#84550f` |
| D, all stakeholders, twenty years | `#07519d` | `#1d60ad` |
| E, no stated objective | `#8a8270` (`--muted`) | `#7d8696` (`--muted`) |

Validator, all pairs: light worst CVD ΔE 21.6, normal-vision 24.3; dark worst CVD 16.0, normal-vision 16.0. Contrast
WARN in both modes (light: A 1.95, B 2.39; dark: C 2.86, D 2.90), relieved as the skill requires: every series is
named by a visible label beside its marks, and every chart has its table. No text wears a series color. E's gray is
outside the validated four by design (it is the neutral, not a series hue) and must stay distinct from all four; a palette test in the
build is to check E against each (not built yet).

*Dated note, 2026-11-10 (C4 built the test; §26 item 1, §26a):* E's gray does **not** clear the validator's
normal-vision floor of 15 against every one of the four: light C 14.79; dark A 13.01 and B 11.77 (the rest 16.87 to
23.75). **His decision, 2026-11-10: accept it as it is**, because no view built puts two goals in one plot area: every
row, panel and toggle carries its goal in text, so a reader never has to tell E from another goal by color alone.
`palette.test.ts` pins the distances and the three pairs. **Reopen** if a later view (the story, C6; the share cards)
draws goals in one plot area.

### 24.2 Decision 3, layout (2026-11-10); step 4 done

**Built:** three layouts on page 6 with palette A, each with a working model switch and the details section closed
by default, captured light and dark at 1280 and 390 (no error, no horizontal scroll): (1) stacked, one page-level
switch, chart then sentences; (2) side by side, one page-level switch, sentences in a column beside the chart at 60rem
and wider, stacked below that; (3) the Roundtable pair's sentence set large above each chart, a switch on each chart.
Plus layout 2 on gpt-oss-120b with both details sections open. In all three the model's name, the valid and attempted
run counts and the scope line sit in the chart's own frame (`figcaption`), so a crop of the chart keeps them.
Claude's read of (3): its large sentence sits outside the frame, so a crop of it loses the model, and a switch per
chart lets the two decisions show different models at once.

**His pick, 2026-11-10, about 10:00 AM: layout 2**, as Claude recommended, with the Roundtable pair's sentence
leading the sentence column. Asked whether it holds on a phone: at 390 the column stacks under the chart (chart,
sentences, details), the page switch stays pinned at the top; checked on the capture.

**The lead sentence (his):** not the large serif of layout 3 ("ugly"); **Source Sans 3 600, 1.125rem, ink text on a
pale yellow wash** (`--leadwash`: light `#f7e6b5`, dark `#3a301a`; his variant b over a gray-rule variant a). Contrast
measured: ink on the wash 14.05:1 light, 10.63:1 dark; the run-count line in `--ink2` on it 7.13:1 and 6.43:1.
Yellow **text** was not used: `#e9a23b` on the light surface is 1.94:1. **Raised and set aside (his call):** the
light wash sits near A's light amber and could read as coded to shareholders; his judgment is that it does not need
to be worried about. The wash is not a series color, carries no verdict, and appears only on the lead sentence.

**Step 4 is done.** Its three picks: page 6's form with the precise views in a closed "See the details" section (§24),
palette A (§24.1), layout 2 with the yellow-wash lead sentence (this section). The previews stay in
`scratch/p6-previews/`, untracked. **Next: §14 step 5, C3 (build modes and the shell), Sonnet builds and Opus
reviews**, its build prompt written from §6 and this section.

## 25. As built, C3: build modes and the shell (2026-11-10, Sonnet; Opus review §25a)

Built from `scratch/p6-c3-build-prompt.md`. Front-end and build-script work in `web/` only: no AWS call, no model
call, no `terraform`, no `hc` command that reads S3. Nothing under `src/horizon_compact/analysis/`, `experiment/`,
`web/explorer-data/`, `web/explorer-memos/`, `web/src/data/` or any Python was touched, and no file the placeholder
entry imports was edited. Not committed (his commit). KNOWN-GAPS, ROADMAP and every other part of this doc were left
as they were; the two edits of this step are this section and the prefix on §14 step 5.

**What was built.**

- **Two modes.** `vite build` with no mode is today's placeholder build (`index.html`, `src/main.tsx`, `dist/`),
  unchanged. `vite build --mode explorer` has its own entry `web/explorer.html` (script `/src/explorer/main.tsx`) and
  writes `web/dist-explorer/`, which Deploy never syncs. `vite.config.ts` is now `defineConfig(({ mode }) => ...)`;
  in explorer mode it sets `outDir` and `rollupOptions.input` and adds the data-copy plugin; everything else is shared
  (font preloads, `assetsInlineLimit: 0`, no module-preload polyfill, `cssCodeSplit: false`, no source maps, the
  preview headers with the content security policy word for word).
- **Scripts** (`web/package.json`): `build:explorer`, `preview:explorer` and `check` as decided; `check` keeps its
  five steps in order and gains `npm run build:explorer && node scripts/check-dist.mjs --mode explorer`.
- **The paths** (`scripts/write-paths.mjs`, after the explorer build): 13 HTML files, one per path (`/`, `/scenario/s1/`
  to `/s4/`, `/cases/`, the five case labels read from `explorer-data/cases/index.json`, `/studies/`, `/memos/`), each
  with its own `<title>`, description, canonical address and `noindex`, the same script and stylesheet tags; the built
  `explorer.html` is then deleted. A path segment from data must match `^[a-z0-9][a-z0-9-]*$` before a folder is made
  from it. An unknown path gets the root page and the client's plain not-found view.
- **The data** reaches the explorer by `fetch` from `/data/`, never by import. In explorer mode a plugin copies
  `explorer-data/` to `dist-explorer/data/` and `explorer-memos/` to `dist-explorer/data/memos/` after the bundle is
  written, byte for byte, and fails the build if either source is missing or empty; the dev server serves the same
  files at the same paths. `src/explorer/data.ts` holds `loadIndex`, `loadGrid`, `loadThinking`, `loadCasesIndex` and
  `loadCase` over `createDataApi(fetcher)`: each path comes from the index's `files` block, `dataPath` refuses
  anything not under `/data/`, and what comes back is the parsed JSON, reshaped by nothing.
- **Routing** (`route.ts`): plain links and the History API. The shell intercepts a primary-button click with no
  modifier key on a same-origin link with no `target`, `download` or in-page hash, calls `pushState`, re-renders,
  retitles the document, scrolls to the top and focuses the new `h1`; `popstate` does the same. Every link is a real
  `<a href>`.
- **The shell** (`Shell.tsx`, `ModelSwitch.tsx`, `views.tsx`, `explorer.css`, `Footer.tsx`, `main.tsx`): header with
  the name, navigation of real links with `aria-current`, one sticky model switch (buttons with `aria-pressed`, the
  models in `index.json`'s order, never "both"; choice kept in `?model=`, Haiku 5.5 when absent or unknown), a skip
  link, `main`, footer. Every route renders a stub: its `h1` from his words, and for a scenario its id and primary
  outcome from `index.json` inside the card frame (`figure` with the model and scope line in its `figcaption`); a case
  stub shows its label and "exploratory". Palette A as `--o-a` to `--o-e`, `--leadwash`, the card frame and layout 2's
  grid (60rem) are in `explorer.css`; `styles.css` is untouched. No inline script, `<style>` or `style` attribute.
- **Words** (`copy.ts`, `his.json`): `explorerHis` (his: the landing question, the scope sentence, and a title and
  description for each kind of page, every value a `[his: ...]` placeholder naming what goes there) and
  `explorerLabels` (Claude-drafted, unapproved until §14 step 8); the file's top comment says both are unapproved.
- **The checks** (`scripts/check-dist.mjs`, `scripts/leaks.mjs`): the placeholder-mode and explorer-mode checks of
  decisions 8 and 9, and the module-graph test of decision 10.

**Files.** New: `web/explorer.html`; `web/scripts/write-paths.mjs`, `leaks.mjs` (+ `.d.mts` for each, for the tests);
`web/src/explorer/` (`main.tsx`, `Shell.tsx`, `ModelSwitch.tsx`, `views.tsx`, `Footer.tsx`, `route.ts`, `data.ts`,
`copy.ts`, `his.json`, `page-meta.mjs` + `.d.mts`, `explorer.css`, `fixtures.ts`, and the tests `route`, `data`,
`copy`, `Shell`, `ModelSwitch`, `modules`, `leaks`, `write-paths`). Changed: `web/vite.config.ts`,
`web/package.json`, `web/scripts/check-dist.mjs`, `web/.prettierignore` (`dist-explorer/`), `.gitignore`
(`web/dist-explorer/`), a comment in the Makefile. Nothing new at the repository root.

**Proof, measured 2026-11-10.**

1. **The public page did not change.** `npm --prefix web run build` before any change and again after the last one
   (and after `make check` rebuilt it): the listings are identical, `diff` empty, 8 files. Saved in
   `scratch/p6-c3-dist-before.txt` and `-after.txt`:

   ```
   088f423f09136bc96b5a7cc7232d671a1ad06a5ff1cf90cd1e24a8d9809d471c  dist/assets/big-shoulders-display-latin-800-normal-DDUD9Xuh.woff2
   a1a01dda969bcbc1e37739245099aefcd156676ed8e39930f98147c64ad6ca98  dist/assets/index-UP0ANYtT.js
   e66067814f1c672d33a457e4f4d102c818b481420e2234cf685ebdbf2f443904  dist/assets/newsreader-latin-400-normal-BFBkh4jY.woff2
   0f73f35e08cde0a2f10c109c6e01d71459d97e4099ecd9a50f1b6c0209e4de2b  dist/assets/source-sans-3-latin-400-normal-DQi5PRDE.woff2
   14527d193b0e30bc32ef931549a246cdfd286573bb12869b7e052b8101a39d38  dist/assets/source-sans-3-latin-600-normal-DeckBYAU.woff2
   ff40cd1a2bbe5f76de6f67b5a1412fde8ff6410a965876620ce5494aff4b3cb3  dist/assets/style-8pjkDroo.css
   df02743b357d29c06582728ea877a8aa5e1a942a546cec0f6344602255c4c3e3  dist/favicon.svg
   49db14b8fdb1f6b1cda00af8cc4f3d8d4b1abdb4ce00d0e8a29fc6e9886f2aa3  dist/index.html
   ```

2. **`npm --prefix web run check`, last lines of each mode** (from `make check`):

   ```
   dist: 8 files
   JavaScript, gzipped, in all: 75899 bytes (74.1 KB); budget 100.0 KB
   fonts: 4 files, 68400 bytes (66.8 KB); budget 150.0 KB; WOFF2 only
   official run ids read: 2290; looked for in every file
   official sweep ids read: 13; looked for in every file
   check-dist: ok
   ...
   write-paths: wrote 13 HTML files
   dist-explorer: 87 files (20 outside data/)
   JavaScript, gzipped, in all: 72605 bytes (70.9 KB); budget 100.0 KB
   fonts: 4 files, 68400 bytes (66.8 KB); budget 150.0 KB; WOFF2 only
   HTML files: 13, one per path
   data/: 67 files, 67 expected, byte for byte
   official run ids read: 2290; looked for in every file outside data/
   check-dist: ok
   ```

3. **`make check`: green** (exit 0). Python **3,423 passed**, unchanged. Vitest **87 passed in 11 files**, up from 37
   (50 new: module graph 6, route 9, data 8, explorer words 4, check negative control 5, write-paths 3, model switch
   3, shell 12). The existing `his words are written` test (`src/copy.test.ts`) is untouched and passes.
4. **The checks fail when they should** (run by hand, then undone by a rebuild; the Vitest negative control runs the
   same functions). Planted in `dist/`: an official run id, an official sweep id, a byte copy of `index.json` and a
   file with `explorer` in its name: 7 failures, each named; clean again after removal. Planted in `dist-explorer/`:
   a run id in a page, a `style` attribute, a changed data file and a deleted data file: 4 failures, each named.
5. **Headless captures** (chrome-headless-shell 1234 over the DevTools protocol, `scratch/p6-c3-shoot.mjs`; the preview
   was `npm --prefix web run preview:explorer`, served with the content security policy header and `X-Robots-Tag`).
   `scratch/p6-c3-shots/`: `/` and `/scenario/s1/` at 1280 and 390, light and dark (8), and one after clicking the
   second model's button. For all nine: **no console error or warning, no failed request, no
   `securitypolicyviolation`** (listener installed before the page's scripts), no horizontal overflow, the app
   mounted, the model switch `position: sticky`. After the click the URL was `/scenario/s1/?model=gpt-oss-openrouter`
   and the pressed button was `gpt-oss-openrouter`. A click on "Scenario s2" from `/` went to `/scenario/s2/` with the
   title changed, `h1` focused and one navigation entry in the performance log (no reload); `/nowhere/` showed
   "Page not found". Report: `scratch/p6-c3-shots-report.json`.

**The decided points, as built.** All ten as written, with these choices the prompt left open: (3) the titles and
descriptions reach the build through one shared module, `src/explorer/page-meta.mjs` (path of a route, its title and
description, the list of routes), a plain `.mjs` with a `.d.mts`, imported by the route code and by `write-paths.mjs`,
so the two cannot drift; his words live in `his.json` for the same reason (Node reads it; TypeScript imports it), and
`copy.ts` exports them as `explorerHis`. A scenario's or a case's own id follows its title: `Title (s1)`. (5) Choosing
a model replaces the history entry and does not push one, so Back leaves the page and does not undo a toggle; Back and
Forward move focus to the new heading as a click does. (8) The data-copy check compares sha256; the run and sweep
ids are looked for as plain strings in every file read as latin1, binary included, so a changed id shape cannot hide
one. (9) Each explorer page is also checked for one canonical link that is its own address, a title, a description
and `noindex`.

**What did not fit, and what was done instead.**

1. **The existing `Footer` does not fit "without change".** `components/Footer.tsx` takes the repository address from
   `Provenance.tsx`, which imports the placeholder's run data; importing it put that data (sweep
   `skeleton-haiku-5-5-f1467906`) into the explorer's bundle, 2,338 bytes gzipped more (74,943 against 72,605) and
   the wrong data. The placeholder's
   files cannot be edited without changing its bytes, so `src/explorer/Footer.tsx` repeats the same markup and words
   with its own constant. A test now fails if the explorer's import graph reaches `src/data.ts` or the placeholder
   JSON. Duplication, on purpose.
2. **The models have no display names in the data.** `index.json`'s `models` carries `model_key`, `sweep_id` and the
   alphas, nothing else, so the switch's buttons read `gpt-oss-openrouter` and `haiku-5-5`, not "gpt-oss-120b" and
   "Haiku 5.5". A name map keyed by model key would write the keys into the front end, which the prompt forbids, and
   the builder (Python) was out of scope. **For review:** add a display-name field to the builder's output, or approve
   a labels map at §14 step 8. Also, the buttons follow the index's order, gpt-oss first, so the default (Haiku) is
   the second button.
3. **His words are in `his.json`, not in `copy.ts`.** The prompt put `explorerHis` in `copy.ts`; the build's plain-Node
   script needs the same titles, and Node 22.13, the floor in `engines`, cannot be relied on to import TypeScript (type
   stripping is unflagged only from 22.18). The object is still
   `explorerHis`, exported from `copy.ts`. (Cost: no comments inside the JSON; the file's reasons are in `copy.ts`.)
4. **Types for fields no view reads yet are `unknown`** (`cells`, `objective_rates`, `pair_rates`, `position`,
   `descriptive`, the case files' `readings`, `dimensions` and the like). The comparisons, verdicts, the
   against-thesis entries, the files block, the models, objectives and scenarios are typed from the real files; C4
   and C5 type the rest when they first read it.
5. **A real HTTP 404 is not possible from the preview or the static host as built.** An unknown path is served the
   root page (status 200) and the client shows the not-found view. A true 404 status is Phase 6.5's (a CloudFront
   custom error response), not this step's.
6. **Not built, not in the prompt:** the palette test that checks E's gray against the four series colors (§24.1 says
   it is still to build), `og:` tags and cards (C7), and any gate that fails on unwritten explorer words. **That gate
   is Phase 6.5's go-live.** `explorerLabels` has a test that none of its values is a `[his:` placeholder, and
   `explorerHis` has one that every value is written text or a placeholder naming what goes there.
7. **Small additions:** a `dev:explorer` script (`vite --mode explorer`, serving the data and any page path from the
   explorer's entry); a skip link; the `.d.mts` files and `fixtures.ts` the tests need. Under the jsdom environment
   `import.meta.url` is not a `file:` URL, so `fixtures.ts` takes the web folder from `import.meta.dirname`.
8. **Navigation to a case from the cases list** is a plain link list in the stub, so every case path is reachable
   without the data views; C5 replaces it.


## 25a. Review of C3 (2026-11-10, Opus)

**Passed; no code change.** One decision for him before C4 (the models' display names and order) and one note
carried to C5.

**Reproduced, not taken on report:** `make check` green on Claude's own run (Python 3,423, unchanged; Vitest 87 in 11
files; doctor ok). After it, the sha256 of the 8 files in `web/dist/` equal `scratch/p6-c3-dist-before.txt` line for
line (the listings differ only in the `web/` prefix of the path). Both check-dist summaries as in §25 (2,290 run ids,
13 sweep ids, 13 HTML files, `data/` 67 of 67 byte for byte, JavaScript 74.1 KB and 70.9 KB gzipped). The captures
read: the nav, the sticky switch, the card frame and the footer in both modes and both widths.

**The rule this step exists for holds.** `web/index.html`, `src/main.tsx` and everything it imports are untouched
(no tracked file under `web/src/` is modified); the explorer is reachable only from `explorer.html`; the module-graph
test walks both entries, finds no `import(`, no `import.meta.env` and no "explorer" in anything the placeholder
reaches, and keeps the placeholder's run data out of the explorer. Deploy still runs `check` and syncs `web/dist`
only. The explorer's own `Footer.tsx` was diffed against `components/Footer.tsx`: the component bodies are identical
and its repository address equals `Provenance.tsx`'s.

**Checked and accepted:** the leak checks read the ids from the committed data, not a list (§25 decided point 8);
the dev server's `/data/` handler refuses a path that climbs out of its folder; `dataPath` refuses absolute, host,
`..` and backslash paths; `write-paths` refuses a data segment that is not `^[a-z0-9][a-z0-9-]*$` and escapes his
words in the head; palette A's values equal §24.1's table; `his.json` in place of `copy.ts` (§25 item 3) is the
right call. A subfolder `index.html` is not served by CloudFront at `/scenario/s1/` without a function or rewrite;
that is already Phase 6.5's (§3 finding 6).

**For his decision, before C4's prompt: the models' display names and order** (§25 item 2). The data has only
`model_key`, so the buttons and the card's caption read `haiku-5-5` and `gpt-oss-openrouter`, in the index's order
(gpt-oss first, the default second). Recommendation: (a) a display-name map in `explorerLabels`, keyed by model key,
in the order shown (Haiku 5.5 first, as the default), with a test that its keys equal `index.json`'s model keys
exactly, so a model added to or dropped from the data fails the test rather than showing a bare key. The names are
words, approved with the other labels at §14 step 8 (§11). The alternative, (b) a display-name field in C1's Python
builder, changes `explorer-data/` and reopens a reviewed step for what is a word choice. C3's prompt said the names
come from the data; that assumed a field that does not exist, and (a) replaces it.

**Carried to C5:** the shell intercepts every same-origin link, so a link to a file (`/data/...`, a download) would
be turned into a `pushState` and the not-found view. No such link exists today. If C5's memo reader links to a raw
file, the interception must leave paths under `/data/` and paths with a file extension to the browser, with a test.


## 26. As built, C4: the scenario view and the section for results against the thesis (2026-11-10, Sonnet; Opus review §26a)

Built from `scratch/p6-c4-build-prompt.md`, with the `dataviz` skill loaded before any chart code. Front-end work in
`web/` only: no AWS call, no model call, no `terraform`, no `hc` command that reads S3. Nothing under
`src/horizon_compact/`, `experiment/`, `web/explorer-data/`, `web/explorer-memos/`, `web/src/data/` or any Python was
touched, and no file the placeholder entry imports was edited (`git status` shows only `web/src/explorer/` and the
`KNOWN-GAPS.md` edit that was already uncommitted). `KNOWN-GAPS.md`, `ROADMAP.md` and every other part of this doc were
left as they were; the two edits of this step are this section and the prefix on §14 step 6. Not committed (his
commit).

**What was built.**

- **The scenario view**, `/scenario/<id>/`, in layout 2 (`ScenarioView.tsx`, `charts.tsx`, `chartData.ts`). Top to
  bottom: his title; the scenario in brief (his, a placeholder per scenario) with the link to the full text; the five
  goals listed once (plain name, color swatch, the letter beside it, the literal `who` and `when` from `index.json`; E
  says it was told no goal); the goal toggles (buttons with `aria-pressed`, all on, in component state, keyed by
  scenario so they reset on a new scenario and carry across a model switch); the card (`figure`: the chart, then a
  `figcaption` with the model's name, "N valid runs of M attempted", "on the fictional company" and his scope
  sentence) beside the column of sentences at 60rem and wider, stacked below; the closed "See the details"; the repeats
  line and the link to the section for results against the thesis.
- **The chart.** A share scenario (s1, s2) is page 6's strip: a row per goal, every valid run a dot at its `primary`
  from 0 to 1, the goal's plain name and run count beside the row, axis ends in words per scenario from the labels, no
  ticks, interval, threshold or mean. A choice scenario (s3, s4) is page 6's unit chart: columns in the order of the
  split's `counts`, ten dots to a row, "n of N" under each group from the split. Each dot has an SVG `<title>`; each
  chart is `role="img"` with an `aria-label`. Plot areas are SVG at 100% width with percentage coordinates and a fixed
  height, so a dot stays round at any width and every label is HTML text.
- **The sentence column.** C vs D first as the lead (Source Sans 3 600 at 1.125rem, ink on `--leadwash`, the flag
  "The pair the Roundtable's claim is about"), then A vs C, B vs D, A vs B, then A vs D flagged secondary. Each is an
  element `.result-sentence` with `data-template`, the output of one function in `sentences.ts`, followed by a small
  line: the comparison's own run counts (`format.ts`), the kept and dropped wordings when one was dropped, "official
  verdict:" and the word, and a small link to the section when the rule lists the comparison. Under each, the
  protocol's quoted reading where §1.5 has a row, or a label saying it wrote none. Above the first, one line stating
  the confidence level from `alpha` (§20: beside the first verdict a reader meets).
- **The details** (`<details>`, closed by default, content built only once opened): the comparison interval chart
  drawn to protocol §6.3 (the verdict word beside each row is the authority; the key says the geometry does not decide
  it and names the 99.7% level and the Bonferroni family of 16); each comparison as the file has it (`headline`
  verbatim, kept and dropped wordings with the dropped cells' `unsuccessful` of `attempted`, the sealed wording's
  result labeled as outside the family, the first attempt and the final result); the full allocation as small
  multiples (a panel per goal, a row per lever in canonical order, every run a dot) with a `summary` table per goal;
  the failures and refusals table (a row per goal and wording, every status shown, zero as zero); the runs table.
- **The section for results against the thesis** (`AgainstThesis.tsx`, `againstWords.ts`): mounted on `/` under the
  story's stub as `section#against-the-thesis` (`tabindex="-1"`), no path of its own. His title and introduction
  (placeholders); the rule in plain words, its three dated sources, the date it was written (2026-11-09), the
  disclosure and the data's `rule` citation as written, all above the list; each entry in the file's order with its
  model, scenario and pair, the clause that listed it, verdict, difference, interval, valid runs, wordings kept and
  dropped, `headline` verbatim, the same `IntervalChart` component and size as the details (a test compares the two
  rows' markup), the protocol's reading where there is one or the label that there is none; for a C vs D entry both
  readings; beside any s4 entry the note that its direction is the one a reviewer could dispute; whole scenarios
  listed; the drafted sentence when the list is empty.
- **The shell** (`Shell.tsx`): after a navigation, and on a first load once the data has rendered, focus and scroll go
  to the element the hash names (inside `main`), otherwise to the top and the `h1`. A hash naming nothing, and a
  malformed escape, fall back to the `h1`. A first load without a hash is left to the browser.
- **The data API** (`data.ts`): a cache by path (one fetch per file, a failed one forgotten); the typed fields this
  step reads (`CellStatus`, `ObjectiveRate`, `Descriptive`, `PerRun`, `ChoiceSplit`, `GridComparison` with
  `per_wording`, `sealed` and `first_attempt`, and so on); `position`, `pair_rates`, `distances` and `secondaries`
  stay `unknown`. **The comment on `valid_runs` is fixed**: it is `[wording_id, valid runs of the first objective,
  valid runs of the second]`, not "attempted and valid" as C3's comment said (§25a's review missed it).
- **The models' names** (his decision, §25a (a)): `explorerLabels.models`, Haiku 5.5 first; `ModelSwitch` and the
  card's caption take their order and names from it (`models.ts`); its comment is updated.
- **`format.ts`**: the only place a number from the data becomes anything else. Percent and points formats (each names
  its precision), the lead's whole points rounded down after `+ 1e-9`, the confidence level from `alpha`, the integer
  sums of `valid_runs` and of `objective_rates[].attempted`, and the pixel helpers (axis position, a deterministic
  jitter from an FNV-1a hash of the run id, the unit chart's slots). A test fails if any other view, chart or template
  file holds a `Math.` call, a `.reduce(` or a running total.

**Files.** New in `web/src/explorer/`: `ScenarioView.tsx`, `AgainstThesis.tsx`, `charts.tsx`, `chartData.ts`,
`format.ts`, `sentences.ts`, `protocol.ts`, `againstWords.ts`, `parts.tsx` (`His`, `HisHeading`, `Title`,
`ProtocolReading`, moved out of `views.tsx` so the views do not import each other), `models.ts`, `links.ts`, and the
tests `format`, `sentences`, `protocol`, `palette`, `chartData`, `links`, `ScenarioView` and `AgainstThesis`. Changed:
`data.ts`, `copy.ts`, `his.json` (`scenarioBriefs`, `againstTitle`, `againstIntro`), `views.tsx`, `Shell.tsx`,
`ModelSwitch.tsx`, `explorer.css`, `fixtures.ts` (`realGrids`), and the tests `copy`, `data`, `Shell`, `ModelSwitch`.
Nothing new at the repository root.

**Proof, measured 2026-11-10.**

1. **The public page did not change.** `find web/dist -type f | sort | xargs sha256sum` before any change
   (`scratch/p6-c4-dist-before.txt`) and after the last `make check` (`scratch/p6-c4-dist-after.txt`): the diff is
   empty, 8 files, the same eight hashes as §25's listing.
2. **`npm --prefix web run check`, last lines of each mode** (from `make check`):

   ```
   dist: 8 files
   JavaScript, gzipped, in all: 75899 bytes (74.1 KB); budget 100.0 KB
   check-dist: ok
   ...
   dist-explorer: 87 files (20 outside data/)
   JavaScript, gzipped, in all: 82655 bytes (80.7 KB); budget 100.0 KB
   fonts: 4 files, 68400 bytes (66.8 KB); budget 150.0 KB; WOFF2 only
   HTML files: 13, one per path
   data/: 67 files, 67 expected, byte for byte
   official run ids read: 2290; looked for in every file outside data/
   check-dist: ok
   ```

   The explorer's JavaScript went from 70.9 KB to 80.7 KB gzipped; the budget is 100 KB and no chunks were split.
3. **`make check`: green** (exit 0). Python **3,423 passed**, unchanged. Vitest **206 passed in 19 files**, up from 87 in
   11 (119 more: eight new files holding 100, and 19 net in `copy`, `data` and `Shell`). The module-graph test is
   unchanged and passes. The log is `scratch/p6-c4-check.log`.
4. **The tests can fail** (three mutations made by hand, then undone): the hash handling disabled (2 tests failed), the
   lower/higher word swapped in the split sentence (2 failed), and the allocation dots drawn on 0 to 1 whatever the
   lever's scale (**not caught** by the first set of tests; a test was added, and fails under that mutation).
5. **Headless captures** (chrome-headless-shell 1234 over the DevTools protocol, `scratch/p6-c4-shoot.mjs`, a copy of
   C3's method with the cache disabled so each capture is a first load; the preview was `vite preview --mode explorer`
   with the content security policy header). `scratch/p6-c4-shots/`, 24 captures and one click record: every scenario view on both models
   at 1280 light (8); s1 and s3 on Haiku at 390 light and dark and at 1280 dark (6); s2 on gpt-oss-120b with the
   details open at 1280 (the not-assessable row and the dropped wordings); s4 on Haiku with the details open at 1280
   and 390 (the wide-scale levers); `/#against-the-thesis` at 1280 light and dark and at 390 light; s1 with goals A
   and C toggled off; and three figure-only crops. **For all 24: no console error or warning, no failed request, no
   `securitypolicyviolation` (listener installed before the page's scripts), no horizontal overflow, the app
   mounted, five result sentences on every scenario view, the details open where opened.** A click from a scenario
   view on "See the results that go against the thesis" went to `/#against-the-thesis`, focus on `against-the-thesis`,
   no reload. Report: `scratch/p6-c4-shots/report.json`. *(With the cache on, a reused tab printed Chrome's
   "preloaded but not used within a few seconds" notice for the two preloaded fonts on captures left open past three
   seconds; a fresh browser on the same pages, with the details opened and five seconds' wait, printed none and
   fetched each font once, so it is the reused tab and not the page.)*
6. **The crop test (§12):** a capture clipped to the `figure`'s box, for s1 (share) and s3 (choice) on Haiku at 1280, and
   s3 at 390 (`crop-*-figure.png`), shows the model's name, "300 valid runs of 300 attempted · on the fictional
   company" and the scope line (his placeholder) in each; the DOM test asserts the same text inside the `figure` for
   s1 and s3.
7. **The scenario text link.** `git ls-tree prereg-v1 experiment/company/scenarios/s1.toml` (and `s2` to `s4`) lists
   all four files at the tag; `scenarioTextUrl` builds `https://github.com/sjtroxel/horizon-compact/blob/prereg-v1/
   experiment/company/scenarios/<id>.toml`. The file is the rendered `sN.toml` the harness reads (`hc scenarios
   render` writes it from `sN.source.toml`), not the source. A test checks each path exists in the working tree.

**The decided points, as built.** All ten as written, with these choices the prompt left open.

(1) The names are the data's models re-ordered by the labels' list; a model the labels do not know would follow, in
the data's order, under its key, and the test that ties the list's keys to `index.json` is what stops that. (2) The
toggles hide a row with opacity (and `aria-hidden` and `pointer-events: none`), keeping its space: no layout moves.
The grid file is held at reduced opacity (`data-stale`) while another model's loads, and swapped when it arrives; a
first load, and a load of a new scenario, shows the loading line. Switching back to a model fetched before shows it at
once. (3) `not_assessable`: "Too many runs failed in every wording to compare “X” and “Y” on <outcome> (<the
`downgrade_reason`>). Wordings dropped: w1, w2 and w3." The outcome phrases carry no number ("the share of the
affected people who were kept", where the previews wrote "of the 125"). (4) The interval chart is `role="group"`, not
`role="img"`, so the verdict words stay readable to a screen reader; the geometry is aria-hidden SVG and every number
is in text beside or below it. (5) `readingFor` takes the scenario's C vs D verdict, so an A vs B split gets "A and B
split, C and D do not" only when C vs D is a no split or inconclusive; the section looks that verdict up in
`index.verdicts`. (6) `against_thesis.clause` is `no_split` or `reversed_split` in the builder, and the labels say
which. (7) Words: see the list below. (8) The palette test is `palette.test.ts`, with the finding below. (10) Nothing
was split.

**What did not fit, and what was done instead.**

1. **E's gray is under the validator's normal-vision floor against three of the four series colors.** §24.1 left a
   test to build "against each"; built to the skill's floor (OKLab ΔE ×100 of 15, unsimulated, the validator's
   `NORMAL_FLOOR`), it **fails on his palette A**: E against C in light **14.79**; E against A **13.01** and against B
   **11.77** in dark (the rest: light A 16.87, B 19.03, D 23.75; dark C 17.93, D 17.07). The test pins these numbers and
   the three pairs under the floor and passes; it does not hide them, and it fails if the palette changes so that
   the list is no longer true. **The palette was not changed** (his pick). Mitigation as built: every row, panel,
   toggle and list item names its goal in text, so no goal rests on color alone. That is not what the skill asks of
   this check: it calls a normal-vision pair under 15 a hard fail that secondary encoding does not excuse (the
   contrast WARN is the one labels relieve). E was outside the validated four by design (§24.1) and was never run
   through the validator, so this is the first time it has been measured. **For his and Opus's decision:** accept
   E's gray as it is, move E, or move A and B in dark.
2. **s4's lever shares pass 100%.** A lever's share on s4 is a share of the year's $20.4 million, and with cuts a lever
   can take many times that (Haiku's "Retaining as cash" reaches 401%, gpt-oss-120b's 1,406%). A 0 to 100% axis would
   draw dots off the plot; the prompt did not foresee it, and a test over the real files caught it. **Done instead:**
   each lever has one scale, shared by all five goals' panels (so they stay comparable), 0 to 100% unless the data's
   own highest `summary.maximum` for that lever is higher; a row on a wider scale says "scale 0 to N%" under its label,
   and the key says every other row runs 0 to 100%. `axisExtent` in `format.ts` is the only arithmetic, and tests pin
   it. The strip's outcome (`primary`) stays within 0 to 1 in every real file (tested).
3. **The prompt's example count is off.** It says A vs B on gpt-oss-120b `s1` counts "20 and 39"; the file's
   `valid_runs` are w1 20 and 19, w3 20 and 20, which sum to **40 and 39**. The test pins 40 and 39, with B at 56 dots.
4. **The details build only once opened.** The allocation panels and the run table are thousands of nodes (s4 on Haiku:
   293 runs by 15 levers by 5 goals), and a closed section shows none. Cost: the browser's find-in-page does not search
   a closed section's text, since it is not in the page. If Opus would rather have it all in the page, closed, the
   `Details` component's `open &&` is the one line to change, with the test time that costs.
5. **Hidden goals leave their space.** A row faded out by its toggle keeps its height, so the chart does not jump; the
   cost is a blank band where a goal was. Collapsing the row would need a height transition, and the prompt said
   opacity only.
6. **"The protocol wrote no reading for this pair" repeats** under the sentence of every pair without a row: A vs C, B vs D
   and A vs D always, and A vs B and C vs D when their verdict has none (three or four lines on most views). The prompt
   asked for it ("show nothing quoted and say, in a label"); it is the smallest muted line. A decision for review
   whether to say it once.
7. **Lever labels are one flat map keyed by lever key**, as the prompt said, so a key two scenarios share
   (`eliminate_roles`, `cut_wages_hours`, `cut_rnd`, `cut_env_projects`, `raise_prices`, `suppliers`) has one
   label. The scenario files word them per scenario ("Cutting existing research and development (a cut)" on s4,
   "Cutting research and development, borne by the Company's future products and its engineering staff" on s2); the
   label is the short common form. The model saw the long wording; the allocation panels do not.
8. **C3's tests that named the stub or the keys were changed, not left.** `Shell.test.tsx` and `ModelSwitch.test.tsx`
   called the buttons by key (`haiku-5-5`), which decision 1 replaces with the names; one `Shell` test asserted the
   stub's id and primary outcome, and the stub is gone, so it now asserts the title's id and the loaded card's
   caption. The stub's `.stub` rules and the labels `primaryOutcome` and `sealedNote`/`intervalLabel` (written and
   then unused) are removed.
9. **No focus ring on the section.** Focus moves to `#against-the-thesis` by script on a first load with the hash,
   and Chrome showed a ring around the whole section; the section is a landmark, not a control, so its outline is
   off (its links and buttons keep theirs). The heading is not the focus target here: the prompt says the element
   the hash names.
10. **A click on an in-page hash link from `/` itself** is left to the browser (C3's rule: a same-page link with a
    hash), which scrolls but does not move focus. No such link exists on `/` yet; **C6** places the section as the
    story's beat 7 and may link to it from the same page, in which case the shell must handle it.
11. **`explorerHis` placeholders** for the four briefs and the section's title and introduction follow the existing
    pattern (`[his: ...]`, each naming what goes there); the section's title placeholder carries his note that he may
    revise it to name the rule's source.

**Claude-drafted words, for §14 step 8 (one list, grouped by object).** Unapproved until he approves each word for word
(§11). Where a value is a function, its text is in the file.

- `sentences.ts`, the result-sentence templates: `split`, `no_split`, `inconclusive` (all three from page 6) and
  `not_assessable` (new, this step).
- `againstWords.ts`, the rule and what is around it: `ruleHeading`, `ruleParagraphs` (five), `sourcesHeading`,
  `sources` (three), `writtenLine`, `disclosure`, `citationLabel`, `entriesHeading`, `wholeHeading`, `wholeLine`,
  `emptyList`, `entryPair`, `clauseNoSplit`, `clauseReversed`, `alsoAgainstAuthor`, `s4Note`, and the field labels
  `none`, `differenceLabel`, `intervalLabel`, `validRunsLabel`, `verdictLabel`.
- `explorerLabels`, the goals: `objectiveNames` (A to E: "Shareholders, short term", "Everyone with a stake, short
  term", "Shareholders, long term", "Everyone with a stake, long term", "No goal stated" — an open word question,
  §24), `goalsHeading`, `goalsKey`, `goalTold`, `goalUnstated`, `toggleGroup`.
- `explorerLabels`, the scenario and the chart: `sceneBriefHeading`, `sceneFullText`, `sceneFullTextNote`,
  `chartLabel`, `shareKey` (s1, s2), `choiceKey`, `axisEnds` (s1, s2: title, low, mid, high), `choices` (close, retool,
  sell, fund, decline), `runCount`, `nOfN`, `dotTitleShare`, `dotTitleChoice`, `capValidOfAttempted`, `capCompany`,
  `loadingScenario`, and the models' names (`models`, "Haiku 5.5" and "gpt-oss-120b").
- `explorerLabels`, the sentence column: `outcomePhrases` (s1 to s4), `whatRunsShow`, `verdictNote`, `roundtableFlag`,
  `secondaryFlag`, `officialVerdict`, `verdictWords` (the four), `runsPair`, `noRunsCompared`, `keptWordings`,
  `droppedWordings`, `noReading`, `protocolReadingLabel`, `repeatsLine`, `againstLink`, `againstMarker`. "Points" as the
  unit of a difference is an open word question (§24).
- `explorerLabels`, the details: `detailsHint`, `intervalHeading`, `intervalKey`, `intervalAxis`,
  `intervalRowNotAssessable`, `intervalChartLabel`, `perComparisonHeading`, `headlineLabel`, `differenceLabel`,
  `keptLabel`, `droppedLabel`, `droppedCell`, `noneWord`, `noNumbers`, `sealedLabel`, `sealedWordingIs`,
  `firstAttemptLabel`, `firstAttemptNote`, `finalLabel`, `allocationHeading`, `allocationKey`, `leverScale`, `levers`
  (23 keys, the short common wording of each lever), `summaryHeading`, `th` (the table headers), `failuresHeading`,
  `failuresKey`, `runsHeading`, `runsKey`, `tableFailures`.
- **Not Claude's, and not in the list:** the protocol's five readings (`protocol.ts`) are quoted verbatim and tested
  against the file; `explorerHis.scenarioBriefs`, `againstTitle` and `againstIntro` are his and still placeholders.

## 26a. Review of C4 (2026-11-10, Opus)

**Passed after one fix.** The fix, and his two decisions on §26's open items, are below; the rest of §26 is
accepted as built.

**Reproduced, not taken on report:** `make check` green on Claude's own run after the fix (Python 3,423, unchanged;
Vitest 208 in 19 files, the 206 of §26 and two added here; doctor ok). The sha256 of the 8 files in `web/dist/`
equal `scratch/p6-c4-dist-before.txt` line for line. Both check-dist modes ok; the explorer's JavaScript is 80.8 KB
gzipped (82,748 bytes; §26 measured 82,655 before the fix's label). The captures read, among them s2 and s3 on Haiku
5.5 and the section at 1280. On the capture of `/#against-the-thesis` the top of the story's scope line is hidden
under the sticky model bar: an artifact of a full-page capture taken after the scroll, not a fault of the page.

**The fix: a pro-Roundtable reading shown where the protocol does not allow it.** `readingFor` gave A vs B the row
"A and B split, C and D do not" when the same scenario's C vs D was **inconclusive** as well as when it was a no
split. Protocol §6.3: a no split "has to be shown, never assumed from the absence of a split", and that row's
reading says the objectives pulled apart "not at twenty years", which is the pattern the statement's "in the long
term" predicts. It was live on the page: **Haiku 5.5 s2** (A vs B split, C vs D inconclusive) quoted it under A vs B,
and Haiku 5.5's thinking sub-study on s1 has the same pattern. It was a reading in the Roundtable's favor that the
data does not show. C4's test pinned the wrong case (`readingFor("A", "B", "split", "inconclusive")` expected the row).
**Changed:** the row applies only when C vs D is a no split (`protocol.ts`, its comment citing §6.3); the unit test
now expects null there; a test over every real grid and thinking file checks that the row appears only where that
file's C vs D is a no split, and fails if no file is left with the inconclusive pattern to test it on; a view test
renders Haiku 5.5 s2 and checks the reading is nowhere on it. **The tests can fail:** with the old condition put
back, all three fail; with the fix, they pass. The prompt's point 5 named the row without saying what "do not" means,
so the gap was the prompt's (Opus) as much as the build's.

**His decisions, 2026-11-10, on §26's open items:**

1. **E's gray (§26 item 1): accepted as it is**, recorded as a dated note in §24.1. No chart built puts two goals in
   one plot area (a row or a panel per goal, each named in text), so no reader has to tell E from another goal by
   color alone. Reopen if C6's story or C7's cards draw goals in one plot area.
2. **"The protocol wrote no reading for this pair" (§26 item 6): said once.** The scenario view no longer prints it
   under each pair; one line under "What the runs show" (`explorerLabels.readingsNote`, Claude-drafted, for step 8)
   says the protocol wrote readings before the results for C vs D and A vs B only, quoted under the sentence they
   apply to. A view test checks that the line appears once and the per-pair line not at all. The section for results
   against the thesis keeps its per-entry line: each entry stands alone there, one line each. `noReading` stays, used
   only there.

**Checked and accepted:**

- **The rule of §5.** `format.ts` holds only display formats, integer sums of run counts and pixel helpers; a test
  fails on a `Math.` call, a `.reduce(` or a running total in any view, chart or template file. `axisExtent` (s4's
  wide lever scales, §26 item 2) picks the largest of the file's own `summary.maximum` for a lever; the "scale 0 to
  N%" it shows is that field formatted, not a number derived. Accepted.
- **The sentences.** The split sentence's direction follows the sign of `difference` (first minus second, which the
  file's field is), and its points are `wholePointsDown` (s3 on Haiku: C vs D reads 86, from 0.8667). The no-split
  sentence says "this one measure, not every choice they made" (protocol §1.5 and §6.3). The not-assessable sentence
  quotes the file's `downgrade_reason`; its one live case (gpt-oss-120b s2, A vs C) reads "every wording has a cell
  over the 10% failure limit", matching protocol §6.3 and §7.2. Its wording is for step 8.
- **The protocol's quotes** are tested as substrings of the frozen file and as one row each of the §1.5 table.
- **The interval key** states §6.3's split rule, and the verdict word beside each row is the authority. The level
  "99.7%" is protocol §6.4's own prose for 0.003125.
- **The goals' descriptions** follow protocol §1.4's frame ("create value for [who], over [when]"), with `who` and
  `when` taken from `index.json`, which match §1.4's table.
- **§26 items 2 to 5 and 7 to 11 accepted as built:** s4's per-lever shared scale; the prompt's "20 and 39" was
  Opus's error (40 and 39 is right); details built only when opened (find-in-page cost accepted for now; §14 step 11
  can revisit); hidden goals keep their space; one flat lever-label map (a word question for step 8); C3's tests
  updated for the names; no focus ring on the section landmark; the same-page hash link left to C6 (carried below).

**Carried to C6:** if the story links to `#against-the-thesis` from `/` itself, the shell must move focus on that
click (§26 item 10), with a test. **Carried to C6 and C7:** the E's-gray note above.

## 27. As built, C5: the memo reader, the real cases and the studies (2026-11-10, Sonnet; Opus review §27a)

Built from `scratch/p6-c5-build-prompt.md`, with the `dataviz` skill loaded before the distance chart. Two parts, in
order: part A (Python, two additions to C1's builder), checked green with `make check` before part B (the front end).
No AWS call, no model call, no `terraform`, no `hc` command that reads S3. Nothing under `src/horizon_compact/analysis/`,
`sweep/` or `caseprobe/`, `experiment/`, `docs/phases/evidence/`, `web/explorer-memos/`, `web/src/data/` or any file the
placeholder entry imports was edited; `KNOWN-GAPS.md` and `ROADMAP.md` were left as they were (the `KNOWN-GAPS.md` edit
that was already uncommitted is untouched). Not committed (his commit).

**The dated note for §5, as written into §5:** "2026-11-10 (C5): the builder also reads the two awareness reports,
`docs/phases/evidence/phase-4/awareness-gpt-oss-openrouter.md` and `awareness-haiku-5-5.md`, by exact path, not by
prefix; and the case memo summaries under `experiment/results/cases/`, counts only." The module docstring of
`src/horizon_compact/site/explorer.py` says the same.

**What was built.**

*Part A.* (A1) Each `cases/<label>/<model_key>.json` gains `memo_counts`: exactly `runs`, `with_text`, `without_text`,
`published`, `held` and `held_by_reason` (all its keys) from the case's `<model_key>-memos-summary.json`, refused unless
`summary_version` is 2 and `case` and `model_key` match, and unless each count is a non-negative integer. The builder
never opens a `*-memos.jsonl`: a test records every path opened through `open`, `io.open`, `Path.open`, `read_bytes` and
`read_text`, on a fixture tree holding a sentinel memo file and again on the real files, and asserts none ends that way
(a negative control shows the recorder sees such an open). (A2) `awareness/<model_key>.json` for each model: the report
parsed against `awareness_report`'s grammar into one record a call (`objective_id`, `template_id`, `recorded`, and for a
recorded call `status`, `stop_reason`, `output_tokens`, `reply`, `empty_reply`), and **proved lossless**: the builder
re-renders the report from its own JSON in the writer's format and refuses unless the bytes equal the file's, with the
file's one final newline (the writer's text has none; `print` adds it: read from the committed files' last bytes). It
refuses an unknown or out-of-order heading, a missing call, a model not in `index.json`'s models, a file whose model is
not the one its name says, a count of calls other than 15, "n of m" other than "15 of 15", text after the last call, a
quote line that is neither `>` nor `> text`, a CRLF file, and a sweep id that is not `awareness-<model>-<hex>`.
`index.json`'s `files` gains `awareness`; both reports and the ten summaries join `sources` (15 sources became 27). The
parse tests drive the real `awareness_report` over a fake store (replied, not recorded, empty reply, a multi-paragraph
reply with odd lines, a reply ending in blank lines, the first and the last call each missing) and the round trip holds
on both real files. **A reply whose text is literally "(no text)" cannot be told apart from the empty reply the writer
prints that for:** both are flagged `empty_reply`. None exists today; a test over the real files asserts no call is flagged
and none holds that text.

*Part B.* The shell leaves a link whose path starts with `/data/`, and a link whose last path segment has a file
extension, to the browser (`Shell.tsx`; carried from §25a). `data.ts`: `loadMemoIndex`, `loadMemos(kind, model, scenario,
objective)` (the cell's files from the index's list, JSON Lines parsed, rows in file order, cached by path, a missing cell
a `{ found: false }` result, a failed fetch forgotten) and `loadAwareness`; types for the memo row and index, `memo_counts`
and the awareness file; the case types, which were `unknown`, now typed from the real files. `route.ts`: `readMemoQuery`
and `memoHref`, which keeps `kind`, `scenario`, `objective`, `run` and `model` (dropped for the default). `memoData.ts`:
the cells the index lists and the resolution of a query (default s1, goal A, first run; refusals named). `caseData.ts`:
the predicate for "every reading of every case is no good match" and the predicates for both matcher notes.

- **The memo reader**, `/memos/` (`MemoReader.tsx`). Choosers are links with `aria-current` for the kind, the scenario and
  the goal; the thinking kind is offered only on the model it ran on, and from a scenario it lacks opens on its first
  cell. The card (`article`, label first inside it): written by <model> under goal <letter> (<plain name>), for a fictional
  company, not the project's view, and "Thinking was on" for the sub-study; then run id, wording, repeat, status and what
  the text is from; then the text in a `div` with `white-space: pre-wrap` in the body face, never parsed, never trimmed;
  then the final record's and the final attempt's object keys and sha256, with the manifest's path and sha256. A run with
  no text shows its status and "This run left no memo", and nothing else in the text's place. Previous and next links; the
  cell's runs as links; a link to the cell's file under `/data/memos/`. A choice the reader cannot show (unknown kind,
  scenario, goal, run, a cell the index does not list, the thinking kind on gpt-oss-120b) is a plain message and a link to
  the default (for gpt-oss-120b's thinking kind, a link to the sub-study on the studies page). Each run id in the scenario
  view's runs table and in the studies page's runs table links to its memo.
- **The real cases**, `/cases/` and `/cases/<label>/` (`Cases.tsx`, `distanceChart.tsx`). The list: his introduction, a
  framing line (the protocol applied to real decisions, readings not tests, not a validation), then the exploratory label
  of every case, verbatim, before anything about a reading or a count; the sentence that every reading of every case is
  no good match **if and only if** the predicate holds over the loaded files' labels (no count is derived); the shortfall
  from `cases/index.json` beside the list; the two selection logs on GitHub; one card a case in the file's order, the
  exploratory label first after its heading, the coarse description's text or the word for withheld, and each model's
  label for each reading. The case page, top to bottom as the prompt lists it: the exploratory label; the description or
  withheld with its status; the dossier's status and reason verbatim; the re-identification status, reason and
  threshold; the probes; the company's decision as the case codes it and each alternative reading's shares; the
  dimensions matched on and left out; then per model (label order) the run counts with every final status, and per
  reading the label and the matcher's reason verbatim, the observable lines, the distance chart, the nearest goal and
  the gap (except as the notes say), both notes where their conditions hold, `depends_on_reading` and the alternative
  readings, and the memo counts with his placeholder (no memo text, no link to one). **The distance chart** is hand SVG
  in a `figure` whose caption names the case, the model, the reading and the label: a row a goal (never two goals in a
  plot area), a dot at the distance, a 2 px line from `low` to `high`, a 0 to 1 axis, `d_star` a solid hairline labeled
  as the no-good-match line, the numbers and the runs behind them in text beside each row, the goal's color a secondary
  carrier, `role="group"`. Colors carry no verdict.
- **The studies**, `/studies/` (`Studies.tsx`). The thinking sub-study: labeled as a sub-study on s1, on Haiku 5.5 only,
  outside the family of 16, before anything it shows; the main grid's s1 at wording w2 only beside the sub-study's, the
  same `ShareStrip` at the same size (side by side at 60 rem, stacked below), the grid's per-goal counts from the
  descriptive cells of w2 (`ShareStrip` gained an optional `wording`); a line that the scenario view shows the grid's
  three wordings; the five comparisons with C4's templates, C vs D first, each with its run counts, official verdict and
  `headline` verbatim, and beside it the grid's sealed-wording verdict for the same pair; the interval level from the
  comparison's `alpha`, worded without the family; no protocol reading; a link to the reader; a link to protocol section
  9.5 at the tag; a closed runs table. The awareness probes: the instruction quoted from protocol 9.6 (`protocol.ts`,
  tested as the blockquote's text with its line break), the context-only label, and per model (label order) 15 replies
  grouped by goal then template, each a document with its label inside (a reply to the probe, not a decision memo), its
  status, stop reason and output tokens, and the text exactly; a call not recorded says so and an empty reply shows a
  label (both tested on an edited fixture; neither occurs in the real files).

**Files.** Python: `src/horizon_compact/site/explorer.py`, `tests/test_site_explorer.py` (fixtures now write five
objectives, case memo summaries beside a sentinel memo file, and awareness reports made by the real writer). Data, by
`uv run hc site explorer` and never by hand: `web/explorer-data/index.json` (24,992 to 26,932 bytes: `files.awareness` and
the new sources), each of the ten case files (about 200 bytes larger: `memo_counts`; `closure-07/haiku-5-5.json` 3,966 to
4,164), and new `web/explorer-data/awareness/gpt-oss-openrouter.json` (9,519 bytes) and `haiku-5-5.json` (12,060 bytes);
23 files, 1,466,666 bytes in all. Web, new: `MemoReader.tsx`, `Cases.tsx`, `Studies.tsx`, `distanceChart.tsx`,
`caseData.ts`, `memoData.ts` and the tests `MemoReader`, `Cases`, `Studies`, `ShellC5`, `caseData`, `memoData`,
`memoRoute`. Changed: `data.ts`, `route.ts`, `Shell.tsx`, `views.tsx`, `ScenarioView.tsx` (exports `Details` and
`RunsTable`; each run id a link), `charts.tsx`, `chartData.ts`, `format.ts` (`formatDistance`), `links.ts`,
`protocol.ts`, `copy.ts`, `his.json`, `explorer.css`, `fixtures.ts`, and the tests `copy`, `format` (the Math ban now
covers the new files), `chartData`, `protocol`, `links`. Nothing new at the repository root.

**Proof, measured 2026-11-10.**

1. **The public page did not change.** `find web/dist -type f | sort | xargs sha256sum` before any change
   (`scratch/p6-c5-dist-before.txt`) and after the last `make check` (`scratch/p6-c5-dist-after.txt`): the diff is empty,
   8 files.
2. **`npm --prefix web run check`, last lines of each mode** (from `make check`, `scratch/p6-c5-check.log`):

   ```
   dist: 8 files
   JavaScript, gzipped, in all: 75899 bytes (74.1 KB); budget 100.0 KB
   official run ids read: 2290; looked for in every file
   official sweep ids read: 13; looked for in every file
   check-dist: ok
   ...
   dist-explorer: 89 files (20 outside data/)
   JavaScript, gzipped, in all: 92193 bytes (90.0 KB); budget 100.0 KB
   fonts: 4 files, 68400 bytes (66.8 KB); budget 150.0 KB; WOFF2 only
   HTML files: 13, one per path
   data/: 69 files, 69 expected, byte for byte
   official run ids read: 2290; looked for in every file outside data/
   check-dist: ok
   ```

   The explorer's JavaScript went from 80.8 KB to **90.0 KB** gzipped: under the 92 KB line the prompt names, so nothing
   was split, but **C6 and C7 have 10 KB left between them**; Opus decides on splitting by path (§17) before C6 if
   that looks short.
3. **`make check`: green** (exit 0). Python **3,483 passed** (3,423 before; 60 new in `test_site_explorer.py`).
   Vitest **380 passed in 26 files** (208 in 19 before). The module-graph test is unchanged and passes. The log is
   `scratch/p6-c5-check.log`.
4. **The tests can fail.** Mutations by hand, each undone: the memo text trimmed (the whitespace test failed); note 1's
   predicate always false (nine case-page tests failed); the "every reading no good match" predicate always true (three
   failed); the shell's `/data/` rule removed (failed, after a test was added for a `/data/` path with no extension,
   because the extension rule alone had let the first version through); its extension rule removed (failed); the strip
   ignoring the wording (the studies test failed); the awareness parse dropping a reply line's trailing spaces (the
   round-trip refusal fired); one extra summary field copied (the "exactly the six fields" test failed).
5. **The five slowest Vitest tests** (`npx vitest run --reporter=verbose`, whole suite): all from earlier
   steps (C4's scenario view: "never shows a result sentence's text anywhere else" 3,323 ms, two axe tests with the
   details open 2,930 ms and 2,540 ms, and "renders every scenario for both models" 1,392 ms; the placeholder
   page's `App.test.tsx` axe test 2,250 ms). **The slowest tests this step added:** the studies axe test with the runs table open 977 ms, the
   studies axe test 771 ms, the cases axe test 766 ms, the reader's axe test 687 ms, a shell route test 495 ms. None of
   this step's is over 2 s; the one that was (2.5 s, two axe runs in one test) was split. No `testTimeout` was raised.
6. **Headless captures** (chrome-headless-shell 1234 over the DevTools protocol, `scratch/p6-c5-shoot.mjs`, a copy of
   C4's method with the cache disabled; `vite preview --mode explorer` under the content security policy header),
   `scratch/p6-c5-shots/`, 17 captures: `/memos/` on both models at 1280 light; the reader at 390 light and dark; a run
   with no text; the thinking kind; `/cases/` at 1280 and 390; `pre-25` (note 1) and `closure-19` (both notes) at 1280,
   `closure-19` at 390 and at 1280 dark; `/studies/` at 1280 light and dark and at 390; the two crops. **For all 17: no
   console error or warning, no failed request, no `securitypolicyviolation`, no horizontal overflow, the app
   mounted.** (The first run showed overflow at 390 on the reader: the manifest's sha256 in the source note is one
   unbroken string; the paragraph now wraps anywhere, and the second run is clean.) Report: `scratch/p6-c5-shots/report.json`.
7. **The crop test (§12).** `crop-memo-card.png` (the card alone) keeps the label, the model's name, goal D with its plain
   name, "fictional company", the run id, and the text; `crop-distance-chart.png` (the figure alone, `closure-19`'s Haiku
   5.5 primary reading) keeps "closure-19 · Haiku 5.5 · Primary reading · no good match" in its caption and the
   no-good-match rule's label. The DOM tests assert the same on every card and every figure.

**The decided points, as built.** (1) The query string is `kind`, `scenario`, `objective`, `run` and the explorer's
`model`; the model switch keeps the others (tested on `/memos/`, `/studies/`, `/cases/` and a case page). (2) **How each
shortfall field is worded** (the file's field, then the label): `cases_by_type`, "Cases found", one row a type;
`short_by_type`, "Places left short", the same rows; `at_most`, "The most cases the protocol allows"; `filled`, "Cases
that filled a short type's place", with a small note, "Under the exploratory selection, a place a short type left open
could go to a case of another type". `filled` is read from `caseprobe/freeze.py` (the cases in `chosen.filled`, printed by
`hc case` as "filled a short type's slot") and KNOWN-GAPS CLOSED 2026-10-26; the type names follow protocol 12.1
("Closure or restructuring", "Invest or retool", "AI-attributed workforce change"). (3) The probes' "Passed" is explained
from protocol 12.8 ("a call passes when it does not name the company"); that reading of the column is mine, from the
protocol and from `closure-19`'s set 1 (0 of 3, then coarsened and re-probed, 3 of 3). (4) The distance interval is
described as a "95.0% bootstrap interval", the level from the case file's `thresholds.alpha` through `confidenceLevel`,
the method from `matcher.py`'s docstring ("a 95% stratified bootstrap spread"). (5) The three matcher-field labels
(`runs distanced`, `on the choice alone`, `left out`) paraphrase `matcher.py`'s comments on `runs`, `choice_only_runs`
and `undistanced_runs`. (6) **`depends_on_reading`'s tie note appears when any reading of the file has all five
distances equal** (the flag compares the readings' nearest goals, and one of them is then arbitrary); that condition is my
reading of KNOWN-GAPS OPEN 2026-10-31 item 1, which says "inherits it" without a rule. In today's files it is exactly
Haiku 5.5's five (tested). The note adds that the label is the same under every reading only when it is, by comparison.
(7) The thinking comparisons' `alpha` is read from the comparison (the thinking file has no top-level `alpha`).
(8) `unmatched_calls` is shown as "none" when empty and as JSON otherwise (empty in all ten files).

**Claude-drafted words, for §14 step 8 (one list, grouped by object).** Unapproved until he approves each word for word
(§11). Where a value is a function, its text is in `copy.ts`.

- `explorerLabels`, the memo reader: `memoKindLabel`, `memoKinds`, `memoScenarioLabel`, `memoGoalLabel`,
  `memoRunsHeading`, `memoRunLine`, **`memoCardLabel`** (the card's label, §11 names it as Claude's), `memoRun`,
  `memoWording`, `memoRepeat`, `memoStatus`, `memoSource`, `memoSources`, `memoLeftNone`, `memoSourceHeading`,
  `memoSourceNote`, `memoFinalRecord`, `memoAttemptRecord`, `memoFileLink`, `memoFileNote`, `memoPrevious`, `memoNext`,
  `memoNone`, `memoNoneNext`, `memoNavLabel`, `memoLoading`, `memoMessages` (kind, scenario, objective, cell, run),
  `memoThinkingOnly`, `memoSeeSubStudy`, `memoToFirst`.
- `explorerLabels`, the cases list: `casesFraming` (the framing line), `casesLabelLead`, `allNoGoodMatch` (the
  sentence), `shortfallHeading`, `shortfallNote`, `shortfallTableLabel`, `caseTypes`, `shortfallType`, `shortfallFound`,
  `shortfallShort`, `shortfallAtMost`, `shortfallFilled`, `shortfallFilledNote`, `selectionLogsHeading`,
  `selectionLogs`, `caseSeeCase`, `casesLoading`.
- `explorerLabels`, the case page: `caseTypeLabel`, `caseDescriptionHeading`, `caseDescriptionStatus`,
  `caseDescriptionWithheld`, `caseDossierHeading`, `caseDossierStatus`, `caseReasonLabel`, `caseReidentHeading`,
  `caseReidentStatus`, `caseThresholdLabel`, `caseProbesHeading`, `caseProbesKey`, `caseProbeSet`, `caseProbeModel`,
  `caseProbeCalls`, `caseProbePassed`, `caseCompanyHeading`, `caseCompanyChoice`, `caseCompanyReading`, `caseNoShares`,
  `caseDimensionsHeading`, `caseObservable`, `caseExcluded`, `caseDimensionChoice`, `caseModelHeading`, `caseRunCounts`,
  `caseFinalStatus`, `caseReadingNote`, `readingNames`, `readingAlternative`, **`readingLabels`** (the matcher's four
  labels), `readingLabelIs`, `readingReason`, `readingLines`, `caseLoading`, `caseMemosHeading`, `caseMemosNone`,
  `memoCountLabels`, `heldReasonsHeading`, **`heldReasons`** (the five reasons), `dependsLabel`, `dependsYes`,
  `dependsNo`, `alternativesLine`.
- `explorerLabels`, the distance chart and the matcher notes: `distanceKey`, `distanceAxis`, `distanceRule`,
  `distanceRowNumbers`, `distanceRuns`, `distanceChartLabel`, `distanceLevel`, `nearestLine`, `gapLine`, `tiedWith`,
  **`tieNote`**, **`oneLineNote`**, **`dependsTieNote`**, `dependsSameLabel` (§11 names the notes' wording as Claude's).
- `explorerLabels`, the studies: `studiesSubStudyLabel`, `studiesSettings`, `studiesSettingsLink`, `studiesGridCard`,
  `studiesThinkingCard`, `studiesGridNote`, `studiesLevel`, `studiesComparisonsHeading`, `studiesGridSealed`,
  `studiesMemosLink`, `studiesRunsHeading`, `studiesRunsKey`, `awarenessLabel`, `awarenessInstructionLabel`,
  `awarenessSettings`, `awarenessLink`, `awarenessGoalHeading`, `awarenessCardLabel`, `awarenessStatus`, `awarenessNotRecorded`, `awarenessEmpty`, `studiesLoading`.
- **Not Claude's, and not in the list:** `AWARENESS_INSTRUCTION` in `protocol.ts` is protocol 9.6's own words, tested as
  a substring of the frozen file. **His, placeholders in `his.json`, each naming what goes there:** `memosIntro`,
  `casesIntro`, `caseMemosHeld`, `studiesIntro`, `studiesThinkingTitle`, `studiesAwarenessTitle`; the pages' titles and
  descriptions for `memos`, `cases`, `case` and `studies` were already placeholders.

**Case fields for his review under rule zero (not edited, not hidden).** The guard cannot see a description that
identifies without naming; these are the fields that carry the most, all shown as the files have them, and none was
typed by me: (a) **the coarse descriptions' text** on four cards and pages (a sector, a revenue band, a half-year and
"in the US" or "outside the US"); it is the published level-0 text, but sector plus band plus period plus place is what
§6.3's search check is about; (b) **`pre-11`'s description is withheld, yet its page shows its type and the company's
decision as coded, "closed the plant"**, so the case reads as a plant closure from the page's own fields even though the
description is withheld; (c) **the three distinct exploratory labels** of `pre-11`, `pre-25` and `pre-224` say each case
was first disclosed after a June 2024 cut-off and before a June 2026 one, which narrows its disclosure date to a
two-year span; (d) **the dossier and re-identification `reason`** strings name "SEC's structured data" and "fewer than
20 filers", and the page shows them verbatim as the prompt asks; (e) **the memo counts**, which for `closure-07`'s
Haiku 5.5 file show how many memos were held for repeating the withheld dossier's words (`dossier_withheld`), a count
the explorer did not show before; it names no word. I found nothing that names a company, a product, a place or a figure
beyond (a); none of this is a decision I made.

**What did not fit, and what was done instead.**

1. **No hash on the reader's links.** I first built the previous, next and run links to land on the card (a `#memo-card`
   hash, which the shell already focuses). The card is not in the page until its memos load, so the shell's focus
   runs before it exists and falls back to the heading. I dropped the hash (and `memoHref`'s parameter for it) rather
   than ship a link that promises a landing it cannot give: after a click, focus is on the heading and the card is
   just below the choosers. A fix is to hold the previous card in the page, as the scenario view does for a model
   switch; it is more code and was not asked.
2. **The reader shows a loading line, not the held previous card, while a new memo set loads** (the scenario view
   holds its chart at reduced opacity). Memo files are 15 to 137 KB and cached by path, so the second visit to a cell is
   instant, but the first shows the line.
3. *(Changed in review, §27a: the switch now drops `run` on `/memos/`.)* **A model switch keeps `run`**, as the prompt says every parameter is kept; a run id belongs to one model's cell, so
   switching model on a memo shows "That run is not in this set" with a link to the first memo. The alternative is to
   drop `run` on a switch, in `Shell.tsx`'s `chooseModel`, which C4's and C3's tests pin as "keeps the others".
4. **The model switch does nothing on `/studies/`.** The page shows both models' probes and a sub-study that is Haiku
   5.5's alone, so there is no model for it to choose. It is still shown, as on every route.
5. **The "not recorded" and "(no text)" branches cannot occur in the real awareness files** (the builder refuses
   anything but 15 of 15, and none is "(no text)"). They are built and tested on fixtures, because the prompt asks for
   every branch of the writer; the "(no text)" ambiguity is stated above.
6. **JavaScript headroom** (above): 90.0 KB, under the 92 KB line; C6 and C7 have about 10 KB between them.

## 27a. Review of C5 (2026-11-10, Opus)

**Passed after one change.** Read against `scratch/p6-c5-build-prompt.md`: the builder diff, the new and changed views,
the predicates, the labels that make claims about the matcher, and the new tests for the rules of this morning.

**Checked independently, not taken from §27.** `make check` exit 0 before the change (Python 3,483, Vitest 380,
`check-dist: ok` in both modes, the explorer's JavaScript 92,193 bytes gzipped). The builder's inputs are all tracked
(both awareness reports, the ten memo summaries), so the byte-for-byte reproduction test holds on CI. The commit's own
hooks, which `make check` does not run, were run over every changed and new file: each generic hook by name (ruff
format and check, large files, merge conflicts, private key, end of file, trailing whitespace) passed and changed
nothing; the name guard's `pre-commit` mode, run against a throwaway copy of the index with every file staged (49
files), passed, and so did its `commit-msg` mode on the suggested message. His index was left empty.

**Rule zero and decision 5.** No memo text and no link to a case memo: the case page shows `memo_counts` only, and the
builder's open-path test covers the real build. §27's five flagged fields, read: (a) the coarse descriptions are the
published level-0 text, already public in the repository; (b) `pre-11` reading as a closure is not specific to it: all
five cases are of type `closure` and all five are coded `close`, and both fields have been public since `5bcf064`;
(c) the exploratory labels' two-year span is the protocol's window, the same for three cases; (d) and (e) carry no
company term. Nothing here is new exposure; each stays his to judge on the page at step 8.

**The matcher notes match KNOWN-GAPS OPEN 2026-10-31.** Note 1 hides the nearest goal exactly where
`all_distances_equal`, and `depends_on_reading` carries the tie note in a file where any reading ties (today Haiku
5.5's five, as the entry says); note 2 is on `closure-19`'s `u1` for both models. The labels say what the entry says
and no more. **The studies view is like for like:** the sub-study ran on `w2` only, Haiku 5.5's sealed wording is
`w2`, and the grid strip is filtered to `w2` with its counts from the `w2` descriptive cells (20 runs a goal, as the
sub-study's). The sub-study's comparisons carry the grid's `alpha` (0.003125); the view shows the level from the file
and words it without the family, as the prompt asked.

**The change.** The model switch kept `run` on `/memos/` (§27, what did not fit 3), so a switch on an open memo always
landed on "That run is not in this set": a run id belongs to one model's set, so that was certain, not an edge. The
prompt's "keeps every parameter" was the gap (Opus's). Now `route.ts`'s `searchAfterModelSwitch` drops `run` on
`/memos/` only, and `Shell.tsx`'s `chooseModel` uses it; every other page keeps every parameter. Two tests: the pure
rule over every path, and a shell test that switches on an open run and lands on the other model's first run of the
same set with no refusal. That test fails on the old behavior (checked by mutation, then restored). **After the change:** `make check` exit 0, Python 3,483, Vitest 382 (two new), the explorer's JavaScript 92,229 bytes (90.1 KB) gzipped, `web/dist/` byte for byte as `scratch/p6-c5-dist-before.txt`; the hooks and the guard run again as above, all passing. **One test made
safer:** `ShellC5.test.tsx`'s focus assertion after "Next run" is now inside `waitFor` (focus is set in an effect; it
passed only because the click's `act` flushed it).

**Not changed, noted.** The reader shows a loading line rather than holding the previous card (§27, item 2), and the
links carry no hash (item 1): both acceptable for now. A failed memo load stays failed for that cell until the page
reloads, even though the data layer forgets the failed fetch: minor, no change.

**Carried to C6: the JavaScript split.** The explorer is at 90.1 KB of 100 KB gzipped, with C6 and C7 still to come.
§17 already decides the remedy (split by path, budget checked per path, never raised), and `check-dist` today counts
all JavaScript as one total, so the split also changes the check. C6's prompt does the split first, as its own part,
with `web/dist/` unchanged and the per-path budget tested, before the story is built.
