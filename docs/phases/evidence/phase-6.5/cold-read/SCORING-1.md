# Scoring of the first cold-read report (Phase 6.5 step 8, doc §5.4)

Scored by Claude (Opus 5.5), 2026-11-19, against `planning/06` §4 (the claim rules, the four habits and the scope
sentence). Each figure the report states was checked against the explorer's data files (`data/index.json`,
`data/grid/`, `data/cases/`) and the rendered text of each page it read (a headless dump of the same preview).

**Why Sonnet, medium:** no doc names the agent's model. The panel's default was kept because the test asks whether the
site explains itself, and a stronger reader is better at supplying what a page leaves unsaid; the re-test after any
fix uses the same model and setting, so a pass cannot come from a change of reader.

## Result

**No conclusion is a misreading under §4. One detail is misread, and the site caused it; it is fixed (below) and
re-tested with a fresh agent.** Two sentences sit at the edge of the claim rules and are recorded, not fixed.

## Conclusions, one by one

| # | The report's conclusion | Checked against | Score |
|---|---|---|---|
| 1 | What was tested: five goals (A-E as the site defines them), four decisions, two models, about 60 runs a goal and 6 a wording on Haiku's s2, pre-registered on 2026-10-13, the 10 and 20 point thresholds, the 99.7% interval | home, methods, `index.json` | allowed; every figure right |
| 2 | Five real cases, all closures, exploratory, not part of the main comparisons | `cases/index.json` (`cases_by_type.closure` 5), cases page | allowed |
| 3 | s1, Haiku: C vs D about 19 points lower under C; A vs C about 39; A vs B about 57; B vs D no split, −2.0 (−7.2 to +3.2) | `index.json` verdicts: −19.1, −39.8, −56.9, −2.0 (−7.2, 3.2) | allowed; one rounding slip (below) |
| 4 | s3, Haiku: closed 50, 8, 60, 8, 60 of 60 under A-E; C vs D about 86 points; A vs C cannot tell; B vs D no split | scenario s3 page; verdicts 86.7, inconclusive, no split | allowed |
| 5 | s2: mostly inconclusive; the one split is Haiku A vs B, about 22 points more on the workforce; 6 runs a wording; gpt-oss has one comparison not assessable | verdicts: Haiku A vs B 22.6 split; gpt-oss A vs C not assessable | allowed |
| 6 | s4: Haiku funded about 41 points less under C than D; the models disagree on the other splits | verdicts −41.6; gpt-oss splits A vs C and B vs D, Haiku A vs B | allowed |
| 7 | s1, gpt-oss: C vs D −45; both short-versus-long pairs inconclusive | verdicts −45.4; A vs C and B vs D inconclusive | allowed |
| 8 | Against the starting expectation: the two Haiku "no split" pairs, s1 and s3 B vs D | `against_thesis.entries` (two) | allowed |
| 9 | Real cases: all 20 readings no good match; the method is not claimed to work on real decisions | cases page ("readings, not tests, and they do not prove the study's method right") | allowed |
| 10 | Awareness probe: in the sampled replies Haiku often named weighing workers against shareholders; no summary conclusion shown | studies page ("Context only... none is used") | allowed; the site gives no summary by design, and the report says its read was a sample |
| 11 | Scope: how two models respond to goal wording, not how executives behave | the scope sentence, on every results surface | allowed; the scope sentence was carried |
| 12 | "Who counts moves Haiku's decisions more reliably than how far ahead it looks" | Haiku's primary verdicts: the who-counts pairs (A vs B, C vs D) split in 7 of 8; the horizon pairs (A vs C, B vs D) in 1 of 8 | **allowed, at the edge** (below) |
| 13 | The Roundtable's claim "did not hold for Haiku on three scenarios" | Haiku C vs D split on s1, s3, s4; s2 inconclusive | **allowed, at the edge** (below) |
| 14 | The disclosed limits: the against-expectation rule written after the reveal, Claude drafted the test text, two program images deleted | methods, home | allowed |

## The two at the edge (recorded, not fixed)

- **#12** is the report's own summary across scenarios; the site does not make it. It fits the verdict tables and is
  scoped to Haiku, which is what `planning/06` §4's "A and C differed mainly in..." allows. Stated as counts it would
  sit squarely inside the rules; "more reliably" is the reader's word, not the data's.
- **#13** turns a split on the named pair into a verdict on the claim. The site's own logic supports the direction (it
  calls C vs D "the pair the Roundtable's claim is about", and says a "no split" there "is consistent with the
  Roundtable's claim"), and the report puts its scope limit in the sentence before. It says nothing about any
  company. The report's next sentence names only s1 and s3 of the three; its own s4 line gives the third.

## Slips that are the agent's, not the site's

- A vs B on s1, "about 57": the page says "about 56" (−56.9, rounded down, as `planning/06` §4 asks).
- "A company's decision shouldn't depend on a goal wording alone": no page says this; the home page asks whether the
  goal changes the decision. The agent's own framing.
- Memos: "no visible way to browse others": the reader has "Next run" and a grid of every run in the set. The agent
  says it did not read the selectors.

## The misread detail, and its cause (fixed)

The report says closure-07's Haiku primary reading shows "distance 1.000 and '0 runs compared'", and that it could
not tell why nothing matched. The page says "30 runs compared, 0 on the choice alone". Two things on the page caused
the misreading:

1. **The counter contradicts the reading above it.** Above it, the page says "Only the choice is coded in this
   reading; it gives no shares", so every run in that reading is compared on its choice alone. But the line shows the
   matcher's `choice_only_runs`, which counts something else: runs that fall back to the choice because their own
   shares are undefined while the company's are given (`analysis/matcher.py`, `_distance_runs`). In a reading with no
   company shares, that count is 0 by construction.
2. **Nothing says what a distance means when only the choice is compared.** By `descriptive.distance`, each run then
   counts 0 if it chose as the company did and 1 if it did not, so a goal's distance is the share of its runs that did
   not make the company's choice. A distance of 1.000 means that none of the goal's 30 runs closed the plant.
   (Haiku closes Plant 6 in most runs, but those runs are a different decision on the made-up company's figures.)

## The fix (2026-11-19, about 8:05 AM; words Claude-drafted, approved by him in-session, all three)

- **(a)** In a reading whose `company_basis` is `choice` (today, every primary reading of all ten case files, and no
  alternative one), each row says "30 runs compared, each on its choice alone; 0 had nothing to compare". A reading
  with company shares keeps the old line (`copy.ts` `distanceRunsChoiceBasis`; `distanceChart.tsx`).
- **(b)** Under such a reading's chart, before the tie note: "In this reading a run counts 0 if it made the company's
  choice and 1 if it did not, so a goal's distance is the share of its runs that chose otherwise; 1.000 means none of
  them made the company's choice." (`copy.ts` `choiceBasisNote`; `caseData.ts` `hasChoiceBasisNote`; `Cases.tsx`).
- **(c)** The cases page's introduction gains: "Each case's runs gave the model that case's own background file in
  place of the made-up company's, so a goal's result on Plant 6 does not carry over to a case." (`his.json`
  `casesIntro`).
- **Tests** (`Cases.test.tsx`): the per-case note loop now checks the choice-basis note and each row's line on every
  reading of all five cases; a new block pins that the choice basis is exactly the primary readings with a choice-only
  count of 0, the closure-07 Haiku primary reading's new words and their order, and the cases page's new sentence.
  Mutation-checked twice (the row's condition forced false; the note's predicate forced false): 6 tests fail each time.
- **Checks:** the Python suite 3,581 passed and lint clean (no Python changed); `npm run check` green after one
  Prettier fix to the test file, every page under its JavaScript budget (largest `/` 95.3 KB, case pages 92.5 KB);
  root cap, paths-check and doctor clean; the hooks' dry run clean. Browser pass (`scratch/p65-s5-shoot.mjs`): 56
  loads with no problem, CLS 0.001, 0 figures missing a part, number trace 0 untraced on every page but `/methods/`,
  whose 1 untraced ("1,237") is the script quirk recorded at step 5.

## The re-test

Recorded in `REPORT-2.md` and `SCORING-2.md`: the same brief, a new Claude in Chrome conversation, Sonnet 5.5 medium,
on the fixed preview.
