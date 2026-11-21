# Phase 6.5 step 10: the public checks (doc section 5.5)

Run 2026-11-21 from about 4:20 AM CST, by Claude (Opus), on the explorer build at `8457a84` (C9) served by the local
preview. The four readers' read (check 4) is his. **Status: done, 2026-11-21, about 5:10 AM.** His decisions on the findings were taken the same morning (each below).

## How the surfaces were read

- **The pages:** `scratch/p65-s10/dump.mjs` (adapted from `video/source-pack.mjs`) loaded each of the 14 explorer
  paths in headless Chrome, light scheme, reduced motion, every `<details>` open, and wrote the page's title, its
  description, its card's alternative text, every chart's alternative text and the whole visible text. Those dumps
  were read, and searched by script for the word lists.
- **The share cards:** the 14 PNGs in `web/dist-explorer/cards/`, read as images (story, scenario s3, case `pre-224`
  in full; the rest by their shared template, built and tested in Phase 6 C7).
- **The video and its captions:** `video/final-transcript.txt`, `video/narration-script.txt` and the page's spoken
  words (held equal to the captions by `methods.test.ts`), against the explorer's grid data.

## planning/06 section 9, surface by surface

| Check | Pages | Cards | Video and captions |
|---|---|---|---|
| 1. Result sentences fit section 4; run counts; spread | pass after one fix (`/studies/`, below) | pass | two lines broader than the site, disclosed on M11 (below); spread not shown |
| 2. No section 3.1 word; no section 3.3 euphemism in the project's voice | pass | pass | pass |
| 3. Scope sentence where results are | pass (13 of 14 paths; `/memos/` shows no result) | pass (all 14) | pass (the end card) |
| 4. The four readers | his read: fine (below) | his read: fine | his read: fine |
| 5. Real-case descriptions pass the search check | pass (second run) | pass (same text) | no description |
| 6. The name explained in the opening | pass, on `/` (below) | not on any card; accepted (below) | not explained; accepted (below) |
| 7. A result against the thesis visible | pass | pass (s1, s3) | pass ("twice, for Haiku, it didn't") |

### Check 1

- **The main pages.** Every result sentence is one of C4's four templates ("came out different ... about N
  percentage points lower/higher under ...", "came out about the same on ... That is about this one measure, not every
  choice they made", "The runs can't tell whether ...", not assessable). Each states its run counts beside it, and each
  scenario's chart shows every difference with its 99.7% interval; the case pages show every distance with its
  bootstrap interval. "About N" is the difference rounded toward zero (`format.ts`, `Math.floor` on the absolute
  value), checked against every figure: 19.1 to 19, 39.8 to 39, 56.9 to 56, 58.9 to 58, 86.7 to 86, 70.0 to 70, 41.6
  to 41, 31.9 to 31, 36.3 to 36, 22.6 to 22, 100.0 to 100.
- **`/studies/`, the miss, and its fix.** The thinking sub-study's five comparisons gave a verdict, run counts and the
  analysis's headline, and every run is drawn as a dot, but no comparison showed its difference or its interval, where
  every main page does. *Correction, the same morning:* this record first said two of the five had intervals of real
  width; the data shows all five have none, because every run of each goal held one value (A kept no one; B, C and D
  kept everyone). C vs D and B vs D are inconclusive by protocol section 6.5's floor; all five carry its constant check.
  **Fixed (his decision, 2026-11-21):** each comparison's closed section now gives "Difference: ..." from the file's
  `difference`, `low` and `high`, as the scenario view's details do, and, where the analysis applied them, one line for
  each of section 6.5's rules (`floor_applied`, `constant_value` and `constant_check`), so an interval of no width is
  never left unexplained. The two lines' words are Claude-drafted, his to approve (`copy.ts`, `studiesFloorNote`,
  `studiesConstantNote`). `Studies.test.tsx` holds both, and removing the floor line fails it (mutation checked).
- **The video.** Every figure is right with its run count (step 9). Two lines say more than the site does:
  - "For the following orders, neither model's runs could settle on a clear pattern." In the script it sat inside the
    long-term pair's paragraph (C vs D, inconclusive for both models), and the video keeps that order, but heard alone
    it covers the whole decision, and Haiku's A vs B on falling orders is a split (+22.6 points, 12 and 12 runs).
  - "Looking after everyone over one year or over 20, it made about the exact same call." The site's no-split sentence
    adds "about this one measure, not every choice they made" (`planning/06` section 4, `07` section 6.1); the video
    does not. The script said "about the same call"; "exact" is the narrator's.
  - Spread: the video gives differences without intervals. The page under it (M11) links the views that show them.
  - **His decision (2026-11-21): disclosed on M11, not regenerated.** M11's "Where it differs from this site" now says
    the video's results are for the two long-term goals, that on falling orders Haiku's two short-term goals did split,
    and that "about the exact same call" is about each decision's main measure, not every choice. Claude-drafted, his to
    approve. Step 9's record (`video/README.md`) lists four differences; M11 now lists six.
- **Pass, noted:** "much more often" for Plant 6 under the shareholder goal (Haiku +86.7, gpt-oss-120b +38.3 points,
  both split, 60 and 60 runs) is the narrator's word; the script said "more often". Tone is his call (step 9's gate).

### Check 2

A script search of all 14 pages for every section 3.1 and 3.3 term found two, both mentions rather than uses: M10's
own sentence that the site never uses "ESG" or "stakeholder capitalism", and the story's quotation of planning doc 00
("If the long-horizon CEO also cuts payroll, that ships."), the source of the against-thesis rule. Every "stakeholder"
is the objectives' own wording for B and D, M10's sentence, or a model's reply on `/studies/`. The cards and the video
use none. (Section 3.4, noted: the video says AI tools "can efficiently do the work"; plain sense, not the filing term.)

### Check 6

The name is explained once, on `/`, in the opening (`his.json` `storyName`, the Mayflower Compact and the UN Global
Compact). No other page, no card and not the video explains it. **His decision (2026-11-21), on Claude's recommendation:**
the site is one surface whose opening is `/` (Phase 6 placed the line there, its IMPLEMENTATION doc §9 item 1), so the other
pages pass through it. A card or the video, seen alone in a feed, is a first contact that does not explain the name;
that is accepted for v1 and recorded here: the README and the launch post, which are his words, are where a feed
reader meets the name.

### Check 5: the search check, second run

**Run 2026-11-21, about 4:55 to 5:05 AM CST, by Claude at his instruction** (his go-ahead after the session's permission
check first refused the read; Claude then read the four companies from the private appendix, and they were written only
there). Phase 5.5 section 6.6's method, unchanged: Claude Code's web search, standard mode, about ten links and the
tool's summary per query standing in for a first page; a hit is the case's own company on its own description's page.
Each published description at the level it is published at, as written and with the same two variations (the sector's
plain-English synonym; the half-year as a quarter). 12 searches; each search, its result and the detail are in the
private appendix only. **This is the second run, on another day (the first was 2026-11-02); results change over time.**

| Case | Published at | As written / var 1 / var 2 | Outcome |
|---|---|---|---|
| `closure-07` | level 0 | no hit / no hit / no hit | passes |
| `closure-19` | level 0 | no hit / no hit / no hit | passes |
| `pre-25` | level 0 | no hit / no hit / no hit | passes |
| `pre-224` | level 1 | no hit / no hit / no hit | passes |

`pre-11` is withheld and was not searched. Twice a case's company appeared on another case's page, as in the first run;
neither is a hit under the rule, and both are recorded privately, never here, since pairing a company with a case would
itself identify it. **Pass.**

## The memo name scan, by construction

The explorer holds real-case memo text (Phase 6 decision 5). Confirmed on the build: `data/memos/` holds only the two
grid sweeps and the thinking sub-study (no case sweep id); `data/cases/` holds no memo text (its only text fields are
the four published descriptions); and none of 7,415 sentence openings (the first 60 characters of every sentence of
60 or more) taken from the 1,237 published case memos in `experiment/results/cases/` appears anywhere in
`web/dist-explorer/` (JSON, HTML, JavaScript, captions). Pass.

## The vocabulary recheck (M10), 2026-11-21

`planning/06` section 11's sources, re-read live by a fetch agent; section 11's "re-check before launch" topics searched
(Claude Code's web search, standard mode).

| Source (section 11) | Read 2026-11-21 | What it says now |
|---|---|---|
| Business Roundtable, "Five Years On" (2024-08-16) | loaded | unchanged; links no newer purpose statement |
| Business Roundtable, all statements | loaded | no 2025 or 2026 item on corporate purpose or the 2019 statement |
| ESG Dive, greenhushing (2026-01-22) | loaded | "ESG" used less because polarizing (25% of S&P 100 reports in 2024, from 40%) |
| Conference Board / Barron's | loaded (text truncated; dated 2023-09-21 by summary) | the backlash "real and likely to increase" |
| Ballotpedia, 14 ESG-related bills (2026-08-24) | loaded | fewest since 2021, still mostly limiting ESG |
| Ballotpedia, ESG proposals down 47% (2026-04-24) | loaded | unchanged |
| Sierra Club, Texas anti-ESG law (2026-02) | empty response | not read |
| Springer, "Stakeholder Capitalism and Ideology" | login redirect | not read |
| CorpGov.net, "Shareholder Primacy" (2026-02-09) | loaded | argues against "stakeholderism" |
| Fortune, AI-attributed layoffs (2026-05-31) | not fetched (its path names companies) | replaced by the searches below |
| Wikipedia, "AI washing" (edited 2026-11-01) | loaded | 2026 accusations of layoffs blamed on AI |

Searches: no new Business Roundtable statement on corporate purpose; "stakeholder capitalism" still argued over in 2026
(commentary from both sides, an ECGI working paper dated November 2026); "AI washing" still the press's term for
layoffs attributed to AI. **Result: the word list stands, unchanged.** "ESG" and "stakeholder capitalism" stay out; the
real-case vocabulary needs nothing new, since no AI-attributed case was found.

## Check 4, the four readers, and his read of the words

**His read, 2026-11-21, about 5:05 AM:** he looked the preview over and found it "fine for now". It was one pass, not
four separate reads with notes per reader, so this record holds no note of what would lose each reader; that is
recorded as it happened, not upgraded. The same read approved the Claude-drafted words of this step and step 9: M10's
dated line, the two `/studies/` notes (`studiesFloorNote`, `studiesConstantNote`), M11's two new disclosures, and M11's
label, player strings and paragraphs from step 9.

## Not done here

- The search re-run's cross-appearances (a case's company on another case's page, twice) are recorded privately; under
  the rule they are not hits, and coarsening further stays his call, as in Phase 5.5.
- Go-live (step 11) makes `check-dist` refuse any placeholder in `dist-explorer/`, now that none is left.
