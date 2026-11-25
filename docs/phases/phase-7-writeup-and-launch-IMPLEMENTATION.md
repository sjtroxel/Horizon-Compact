# Phase 7 — Write-up and Launch: IMPLEMENTATION (v1.0)

> **IMPLEMENTATION doc. APPROVED 2026-11-22, about 10:27 AM (his).** Drafted by Claude (Opus) the same morning, from
> about 9:10 AM, while he was out. **Decisions A-D DECIDED about 10:12 AM (his, §2):** A, B and C as leaned; D, one
> Short, Gemini first, which amends the re-scope's R-A (the scope doc's header note of 2026-11-22). Drafted the morning the scope doc was re-scoped and approved (its
> section "Re-scoped 2026-11-22", approved about 8:51 AM). Sections: §0 the review; §1 facts checked live; §2 decisions
> A-D; §3 the steps; §4 the README's outline; §5 the marker scheme and its tests; §6 the audit; §7 the Short; §8 the
> commit order; §9 the definition of done; §10 cost; §11 risks to the build.
>
> Sources: the scope doc as re-scoped (`docs/phases/phase-7-writeup-and-launch.md`); the Phase 6.5 IMPLEMENTATION doc
> (§3, the methods page; §6, the video; §11.2, what Phase 7 inherits); `planning/00` §2, §8 and §10; `planning/02`
> §2.3; `planning/05` §5-§6; `planning/06` §1, §4-§6, §8, §9 and §11; `planning/07` (the eval spec Phase 7 audits
> against); `ROADMAP.md` §2 and §5; `KNOWN-GAPS.md` (START HERE, the OPEN, REMINDER and BLOCKED entries); the two
> official grids; `web/explorer-data/index.json`; `web/src/explorer/methods.json`; `.github/workflows/deploy.yml`;
> `evidence/phase-5.5/cost.md`; Musical Mycelium's `tests/test_published_numbers.py`, read only, for the marker
> pattern.
>
> **The scope doc is amended at this approval:** one dated line in its header pointing here, and a dated note on
> R-A, the one line a decision here changes.
>
> **Rule zero governs every line.** Real cases appear only by label and type. No memo text from a real case is quoted.
> Every surface this phase creates is public by design, so every step ends with the guard, and the surfaces the guard
> cannot read (text typed into GitHub, LinkedIn, images, video) get a named human or Claude read.

## 0. The review: what the re-scope settled, and what this doc found besides

The re-scope (scope doc, "Re-scoped 2026-11-22") settled the results row, the cuts, the models, the card, the
hosting, the cost pots, the vocabulary clock, the Short and the carried items. This doc builds on it and adds:

1. **Delivers 0 is done.** He set the corrected card line and the website field on 2026-11-22, before 9:08 AM
   (Claude-drafted at his request, the name guard's message check passed first); `gh repo view --json
   description,homepageUrl` returned both as set. Recorded in §3 step 0.
2. **No license.** The repository has no `LICENSE` file, and no planning or phase doc decides one (grep of
   `docs/planning`, `docs/phases` and `ROADMAP.md` for "licen", 2026-11-22: only font and data-source licences). A
   public repo with no license reserves every right by default, so a reader may look and may not lawfully reuse the
   code, the data or the results, which sits badly with a project that asks a hostile reader to re-run it. Decision C.
   Root count: 14 of 16 now; `README.md` and `LICENSE` make 16, exactly the cap.
3. **The results views may not carry run dates.** Delivers 7 puts "the model, the run dates" on every results
   surface. A grep of the scenario view, the story, the run details and the footer (`web/src/explorer/*.tsx`) and of
   the copy file found no date; the methods page (M3) names the models, and his `metaLine` dates the plan
   (2026-10-13), not the runs. **A grep miss is not proof:** step 2 checks the built pages first, and only adds what
   is missing. The share cards are out of this item on purpose: they state no result and hold no digit beyond the
   models' names, by test (`cards.test.ts`).
4. **The idle bill can be measured during this phase, not after it.** "After launch" in Delivers 6 means after the
   site went live (2026-11-21, about 10:15 AM), not after the post. No sweep or task runs in this phase; the Deploys
   it starts build images in GitHub's runners and add at most about a cent a month of ECR storage each (Phase 1.5
   IMPLEMENTATION doc §26), which is part of what the idle bill is. So a measured window inside the phase lets DoD 4
   close without waiting a month, provided every Deploy in the window is listed beside the figure. Decision B.
5. **Two ROADMAP lines are stale and the README must not inherit them:** §2's "The main model is Sonnet 4.6, fixed
   for v1 (his, 2026-10-05)", superseded when Bedrock was blocked and the protocol took Haiku 5.5 and `gpt-oss-120b`;
   and §5's "a Sonnet 5.5 sweep is no longer planned ... If access ever arrives", since Anthropic's API now reaches
   Sonnet 5.5 without Bedrock. Neither is a plan change: both get dated notes at Delivers 10, and any Sonnet 5.5 sweep
   stays a new decision with its own budget (`planning/05` §6).
6. **The official run dates, from the run log** (`evidence/phase-4/run-log.md`): Haiku 5.5's grid and thinking
   sub-study and `gpt-oss-120b`'s grid all ran on 2026-10-14 (UTC; the `gpt-oss-120b` grid in two sessions after a
   crash, resumed the same day); the awareness probes on 2026-10-14 and 2026-10-15 UTC. The case runs are Phase 5.5's,
   dated in its run log. These are the dates step 2 and the README use, read from the records by code, not typed.
7. **A LinkedIn post may not carry both a video and an image.** Not verified; checked live at step 13. If it cannot,
   the Short carries the chart (it is built from the site's charts either way, §7), which keeps `planning/06` §6.1's
   "one chart".

## 1. Facts checked live, 2026-11-22

| Fact | Read | Source |
|---|---|---|
| Haiku 5.5's retirement | "Not sooner than October 7, 2027"; active, not deprecated; Anthropic gives "at least 60 days' notice before model retirement for publicly released models" | Anthropic's model deprecations page (platform.claude.com), read about 8:12 AM |
| Sonnet 4.6's retirement (not an official model; for the record only) | "Not sooner than February 17, 2027" | the same page |
| Gemini Notebook's short video format | a vertical format of about 60 seconds, named "Short" in the Gemini Notebook help center and "Brief" in the older NotebookLM one (a mid-rebrand mismatch); English only by Google's documentation, one secondary source disagreeing; **whether a free account can generate it is reported both ways**. His own notebook listed "Short" among its formats on 2026-11-20 (`evidence/phase-6.5/video/README.md`), so the format exists in his account; whether it renders on his plan is found by trying, at step 10 | web search, secondary sources plus Google's help pages as reported; not read first-hand today |
| LinkedIn's organic video limits | 3 seconds to 15 minutes from desktop; aspect ratio 1:2.4 to 2.4:1 (so 9:16 and 4:5 are both inside); videos play muted by default, so captions are burned in or uploaded as a caption file; third-party guides disagree on recommended vertical sizes | LinkedIn's help pages as reported by search (video sharing troubleshooting; captions); re-read first-hand at step 10 before the cut is rendered |
| Tools like Gemini Notebook | several vendors offer document-to-video tools; every comparison found is vendor-written; no independent review, price or tracking terms verified | web search; not used: decision D, one Short, Gemini first |

**Still to read at the step that needs it:** Gemini Notebook's plan access (step 10, by trying); LinkedIn's video and
caption help pages first-hand (step 10); whether a LinkedIn post carries both a video and an image (step 13); the
vocabulary recheck if the post goes out after 2026-12-12 (step 13); free static hosts' terms (not this phase: the
hosting plan's own date, 2027-06-30).

## 2. Decisions for him

Claude's lean first in each, with the reason. **All four DECIDED 2026-11-22, about 10:12 AM (his).** The options are
kept as the record.

- **A. Who re-verifies the audit's sample (scope decision 4). DECIDED: (a), Claude in Chrome.** His condition: at step
  7, Claude gives him the setup step by step (open the extension, start a new conversation, check the model, paste the
  brief), since the arrangement is easy to forget between uses.
  - (a) **Claude's lean: Claude in Chrome, in his browser, with no context but the public repo and site URLs,** as
    the cold read ran (Phase 6.5 §5.4): Sonnet 5.5 at the panel's default effort, a brief listing the sample's items
    and their stated evidence, nothing about the expected answer. It has no working history, no memory store and no
    repo checkout, so it can only check what a public reader can. Free on his plan.
  - (b) A fresh Claude Code session on a fresh clone in a scratch directory. It can run `make check` and the
    re-scoring test itself, which a browser cannot, but it loads his global `CLAUDE.md`, which describes this
    project, so it is less cold.
  - (c) Both: (a) for the sample, (b) for the three items that need code run (the re-scoring check, the README
    numbers test, `hc protocol check`).
- **B. The window for the idle monthly bill (Delivers 6, DoD 4). DECIDED: (a), seven measured days scaled to a
  month.**
  - (a) **Claude's lean: seven days, measured, then scaled,** from his Cost Explorer reading (tag `Project`, daily,
    charge type Credit excluded, as Phase 5.5 read it): seven consecutive whole days after C2's Deploy, with no task
    run and every Deploy in the window listed beside the figure. Stated as "measured over seven days, about $X a month at that rate", and the first full calendar
    month after close added as a dated note on M8 and in M12. It closes the phase without waiting, and it says what
    it is.
  - **Amended 2026-11-25 (his, about 3:51 AM: "i'd like to be done and not have to wait").** The window is 2026-11-14
    to 2026-11-20 UTC, before go-live, in place of seven days after C2's Deploy: the first such window (11/24 to 11/30)
    cannot be read before 12/01. The nine Deploys in it are listed beside the figure. **The December note is dropped**
    (his, about 4:12 AM: it would not affect the project's outcome); M8 makes no promise of it.
    Step 9's As built note and `evidence/phase-7/cost.md` hold the detail.
  - (b) A full calendar month (December 2026) before the close. Exact, but it holds the phase until early January,
    past the dev key's 2027-01-02 date.
- **C. The license (§0 item 2). DECIDED: (a), MIT for the code, CC BY 4.0 for the rest.**
  - (a) **Claude's lean: MIT for the code; CC BY 4.0 for everything else** (docs, experiment content, results, raw
    text, site words), stated in one `LICENSE` file at the root and one line in the README. Reuse with credit is what
    a re-runnable experiment wants. The fonts keep their own OFL licences (`web/fonts-ttf/`). The raw text holds model
    outputs: whether they need their own line is read from Anthropic's and OpenAI's current terms at step 4, live,
    not assumed; until then the README's line claims only the project's own work.
  - (b) MIT for everything. Simpler; a poorer fit for prose and data.
  - (c) No license, kept as now. Viewable, not reusable; the README would have to say so.
- **D. A third candidate in the Short bake-off. DECIDED: neither option; one Short, made well.** His words: "I'd rather
  focus on making one really good short than try and make yet another one too ... hopefully Gemini does a fine job
  for us." So: **no third tool, and no second candidate made in parallel.** The Gemini Short is made first, under the
  three-attempt cap; the cut from the site's renders (§7.3) is made **only if** no Gemini attempt passes the check or
  he does not want the one that does. This amends the re-scope's R-A (the bake-off) to Gemini first, with the built
  cut as the fallback (a dated note on the scope doc at this doc's approval).
  - (a) **Claude's lean: two candidates only** (the Gemini Short and the cut built from renders), unless one tool
    passes a pre-check first: free or under $5, no tracking on the output, accepts a fixed script, exports an MP4,
    states how it labels AI output. Claude runs the pre-check on vendor pages at step 10 and names the tool to him
    before anything is uploaded; nothing from the project goes to a new service without his yes.
  - (b) Three candidates from the start: Claude picks the best-reviewed tool.

## 3. The steps

Each step names its Delivers item, who does it, the model, and what "done" is. `[done]` markers and "As built" notes
go under each as the phase runs. **Model choice:** Opus for steps 1, 6, 7, 8, 13 (reads and judgement); Sonnet for
the code in steps 2 and 3; Opus to review that code.

### Step 0. The card corrected (Delivers 0; decision R-B) [done 2026-11-22]

His line, Claude-drafted at his request, set with `gh repo edit` before 9:08 AM, with `homepageUrl`
`https://horizon-compact.vercel.app`; his `gh repo view` showed both. Re-read at step 8 against the finished README.

### Step 1. The rule-zero sweep, first pass (Delivers 1) [done]

Claude, Opus. Read-only.

1. `make guard-history` over every commit, branch and tag; `make paths-check`; `make doctor`. Recorded with their
   output lines.
2. **The surfaces the guard cannot read,** each read in full by Claude against the term file's spirit, not its list:
   the repo description and website (step 0); every release and its notes (`gh release list`, `gh release view` for
   each); every issue and pull request, open or closed (`gh issue list --state all`, `gh pr list --state all`); the
   tag messages, which `make guard-history` scans, read once more by eye (Claude's settings deny `git tag`, so he runs
   `git tag -l -n99` and pastes the output);
   the 14 live paths (fetched, text extracted); the video's captions (59 cues) and its frames' text (from step 9 of
   Phase 6.5's check record); the README images, once made (step 4, read as images).
3. **The two private cross-appearances** from Phase 6.5's search check (not hits): Claude reminds him; his call
   whether to coarsen further. If he coarsens, it is a site change (an M12 entry) and the search check re-runs on the
   changed description only.
4. Recorded in `docs/phases/evidence/phase-7/rule-zero.md`: each command, each surface, what was read, the result.
   Rule zero for the record itself: no term, no private path, no description beyond the coarse ones already public.

**Done:** every item clean, or a finding fixed and the item re-read. **A second, shorter pass** runs before the tag
(step 12) and before the post (step 13): `make guard-history`, the new surfaces (README, write-up, audit, release
notes, the Short, the post draft and its image).

**As built, step 1 (2026-11-23).** Every item clean, nothing to fix; record `docs/phases/evidence/phase-7/rule-zero.md`.
Beyond the list: the built site's 104 text files and the captions run through the guard's own matcher (0 findings), the
14 link-preview cards, the poster and one Phase 1.5 screenshot read as images. His call on the two cross-appearances: no
further coarsening. The README images move to the second pass.

### Step 2. The model and run dates on the results surfaces (Delivers 7) [done]

Claude reads, Sonnet builds, Opus reviews. A site change: M12 entry, Deploy.

1. **Measure first:** on a local preview of the current build, list every results surface (the landing story, each
   scenario view, the section for results against the thesis, the studies, the cases, the memo reader) and record
   which show the model and which show run dates. Only what is missing is added.
2. **Where dates come from:** the results files and the raw manifest, by the explorer-data builder, never typed. Per
   model: the official grid's run date (2026-10-14 UTC for both; §0 item 6), the sub-study's, the case runs'. The
   builder writes them into `web/explorer-data/`; a test fails if a date on the page is not the data's.
3. **The words:** a template line, in substance "Runs: [model], [dates]", drafted by Claude from `planning/06` §4 and
   approved by him word for word (`planning/06` §8's gray zone), flagged as Claude-drafted.
4. **The retirement line is prepared, not shown:** a data field, empty in v1, that renders a dated line ("[model] was
   retired on [date]; these results describe it as it was") when filled. Filling it later is a data change with an
   M12 entry. Its reminder goes in KNOWN-GAPS (step 11).

**Done:** every results surface names its model and run dates from data; tests for both and for the empty retirement
field rendering nothing; `make check` green; Deploy green; an M12 entry ("presentation"); his approval of the words.

**As built, step 2 (2026-11-23).** Record: `docs/phases/evidence/phase-7/run-dates.md`. **Measured first:** the model was
already named on every results surface; run dates were on none except the methods page, so six surfaces gained a line
and none gained a model name. **Where the dates come from:** a new `runs` block in `index.json`, built by
`site/explorer.py`: the grids and the thinking sub-study from the raw session records, each awareness probe from its 15
raw call records (two timestamps picked, never the reply), and the case runs from the Sessions table of the Phase 5.5
run log, read by its exact path. **Two departures from the step's text, both his decisions of 2026-11-23 (1a and 2a):**
the awareness raw is now opened, for two timestamps (a dated note in the builder's docstring amends its "never an
awareness run"); and the case dates are not "from the results files and the raw manifest", because no results file
carries a date and the case raw is not published, so they are **session start dates** from the run log, checked
against each case result's sweep id, label and model, and the lines say "started". The retirement field is
`experiment/retirements.toml` (empty; outside the hashed `experiment/company/`), rendered only when it names a date.
**The words:** the four strings of the record's section 3, Claude-drafted and approved by him word for word; lines on
the scenario view, the story (first decision and second-model section), the section against the thesis, Studies, the
cases list and each case page, and the memo reader; none on the story's case cards or its other-scenarios section (his
"yes" to that placement). **M12:** the entry dated November 23, 2026 ("presentation", no published number changed).
**A bug the tests found:** the run-log date cross-check read the wrong cell and never ran; fixed, with a test. **Opus's
review (2026-11-23):** no code change; the M12 entry reworded with his approval, because its first version said the
pages newly named their model, which none did. **Still open:** Deploy green (it rides in C2); if C2 is committed on another day, the M12 entry's date is
Claude's to change before the Deploy that publishes it.

### Step 3. The README machinery (Delivers 2; scope decision 3; §5) [done]

Sonnet builds, Opus reviews. Before any README prose, so the first sentence with a number is already under test.

**Done:** §5's generator, markers and tests exist and pass on a README skeleton holding one marked figure of each
kind; each of the three tests fails on a planted fault (a changed digit, an unknown key, a removed marker) and the
digit census fails on an unmarked number; `make readme` rewrites marked figures; `make check` runs the tests.

**As built, step 3 (2026-11-24).** **Three choices of his, made 2026-11-24 before the build:** (1) the skeleton is a
test fixture, `tests/fixtures/readme-skeleton.md`, and not a `README.md` in the root, which would have shown on the
public repo page until step 4; (2) §5.2's test 5 (the scope sentence) and §5.3's audit-ID test are deferred; (3) no
cost key until step 9. **Built:** `src/horizon_compact/site/readme_figures.py` (the generator, the marker helpers
and the `make readme` entry point, standard library only, no network, AWS client or clock; a test reads its imports),
`tests/test_readme_figures.py`, the fixture, and a `readme` target in the Makefile
(`python -m horizon_compact.site.readme_figures`, with a help line; no change to `cli.py`). `make check`: 3,667 Python
tests passed and 1 skipped (the real-files test of §5.2 test 3, which has nothing to read until step 4), 697 frontend
tests.

**The keys and their sources.** Every figure is read from `web/explorer-data/` (`index.json` and the files it lists),
the data the site reads and `test_site_explorer` already holds equal to a fresh build from the official results
files and the case results. The table `KEYS` in the module names each key's source and the `format.ts` function it
mirrors, and a test holds the table and the generator to the same keys. For the lead, Haiku 5.5 on s1, C against D:
`haiku_cd_s1_difference` (the difference in points, `formatPoints`), `haiku_cd_s1_points_down` (whole points,
`wholePointsDown`, as the site's sentences use it), `haiku_cd_s1_interval` (the two ends, joined as
`AgainstThesis.tsx` does), `haiku_cd_s1_confidence` (`confidenceLevel` of the model's `alpha`),
`haiku_cd_s1_runs_c` and `haiku_cd_s1_runs_d` (valid runs per side, `comparisonRuns`). Run counts per model:
`grid_runs_haiku` and `grid_runs_gpt_oss`, the attempted runs summed over the four scenarios (`attemptedRuns`; attempted,
not valid). Against the thesis: `against_thesis_count`, the length of the section's entries. The cases:
`cases_exploratory_closures`, `cases_leakage_disclosed`, `cases_readings` and `cases_readings_no_good_match`. **The
lead scenario and pair are in the module's constants** (`LEAD_SCENARIO`, `LEAD_PAIR`) and are his choice at step 4
(the re-scope's R.1); a figure for another comparison is one more entry in the module and one more marker. The
rounding is the site's: a test pins that an exact tie rounds up as JavaScript's `toFixed` does and Python's `format`
does not.

**The tests** (all in `tests/test_readme_figures.py`; §5.2's tests 1 to 4): each runs on the fixture always and on
`README.md` and `docs/plain-english.md` whenever they exist. The census blanks, in order, text that is not prose
(fenced code, comments, tags, link targets, URLs, a code span that is a path or file name), then dates, section and
planning references (`§`, `planning/NN`, `protocol N.N`, `Phase N`, `step N`), versions (only after `v` or the word
"version", never a bare decimal), the names (Haiku 5.5, `gpt-oss-120b`, `prereg-v1`, `sha256` and the five case
labels from the data), the years (1620, 2019, 2024 and the run years from the data's `runs` block, today 2026),
scenario and wording ids (`s1`, `w3`, lower case) and list markers; whatever digit is left fails, with its line. The
explicit allowlist holds one entry, `S3` (the storage service's name), with its reason; an entry is added with the
step that needs it. **The planted-fault tests** write a faulty copy of the rendered skeleton to `tmp_path` and assert
the check reports it: a changed digit (test 1), an unknown key (test 2), a removed marker (test 3, and the retyped
number also fails the census), an unclosed marker, and an unmarked number in prose (the census). They stay in the
suite.

**Departures from the step's text and choices to review.** (a) **The skeleton's marked values are placeholders**
(`0`), by design: test 1 renders the fixture from the data before it compares, so a change in the data never needs a
fixture edit; on the real files test 1 compares the committed text as it stands. Tests 2 to 4 read the fixture as
committed. (b) **Test 3 on the real files is across `README.md` and `docs/plain-english.md` together:** the plain-English
write-up need not carry every figure, the pair must. On the fixture alone every key must be marked. (c) **There is no
structured field for "three with a leakage disclosure".** `cases_leakage_disclosed` counts the cases whose
`exploratory_label` holds the phrase "first disclosed before the main model's training cut-off" (constant
`LEAKAGE_PHRASE`); the label is the disclosure the site shows beside each case, but a reworded label would count 0.
The alarm for that is the pin (`test_the_figures_hold_what_the_sources_hold`, "3"), not the stale-figure test, which
would fail only until `make readme` wrote the 0 in (Opus's review corrected this sentence). (d) **A claim test the outline's "all 20 readings"
needs:** a test fails if `cases_readings` and `cases_readings_no_good_match` ever differ, because the word "all" is
not a number the markers protect. (e) **Not in this step, as decided:** §5.2 test 5, the scope sentence, waits for his
wording at step 4; §5.3's audit-ID test waits for `docs/v1-audit.md` and its format at step 6. (f) No change to
`web/explorer-data/`, the site, `experiment/` or any planning doc; the root holds 14 of its 16 entries. **Still
open:** C3 is not yet committed.

**Opus's review of step 3 (2026-11-24).** The generator's values, sources and formatting were checked against the data
and `format.ts` (each twin is the same expression; `toFixed`'s tie rule is right); no change to the generator. **Four
holes in the census, each a number that passed unmarked, fixed in the test file:** (1) the path-in-code pattern also
matched the prose *between* two code spans when that prose held a "/" or an "e.g.", so its digits were blanked; code
spans are now found left to right and only a path-like one is blanked; (2) and (3) the list-marker pattern blanked any
line starting "990." or "20. All", which a hard-wrapped sentence can produce; a marker is now blanked only where
Markdown renders a list (after a blank line or another list line); (4) the long-date pattern took any four digits after
"October 14, " as its year; the year is now left to the year pass, so only an allowed year passes. One false positive
went with it ("June 2026" had failed on "26"). Each is a failing case in the suite. **One claim test added,** beside
step 3's "all 20 readings" test: the lead comparison's `final_verdict` is still "split". **Left as designed:** an
allowed year (1620, 2019, 2024, 2026) passes anywhere, so a count equal to one would pass unmarked; no figure today is
one.

### Step 4. The README (Delivers 2; §4) [done]

His words, or Claude's draft on his grant made on this pass (scope decision 1). Claude interviews and outlines first
either way (§4 is the outline). Every result sentence from `planning/06` §4's allowed column with run counts.

1. **His choice on this pass:** his words (Claude critiques line by line) or a Claude draft (flagged once with the
   watermark, he edits). Also his: which scenario and chart lead (the re-scope's R.1).
2. **Images:** real renders of the site, captured headless (chrome-headless-shell over the DevTools protocol, the
   method of Phase 6's captures), light and dark, at a width that reads on GitHub; shown with `<picture>` and
   `prefers-color-scheme` sources so each reader sees their theme. Stored under `docs/readme/` (no new root entry).
   Read as images by Claude for rule zero (step 1's second pass). No emoji, no stock art.
3. **The four readers** (`planning/06` §5): Claude reads it as each and writes one note per reader; he reads it once.
4. **`planning/06` §9's seven checks**, each recorded.

**Done:** the README is in the repo; the §5 tests pass; §9's checks recorded; his approval.

**As built, step 4 (2026-11-24). APPROVED by him, 2026-11-24, about 11:13 AM** ("Yes the README is approved"), as pushed in C3. **His choice on this pass:** a Claude draft ("just
have you write the readme.md now"), so flagged once for the watermark; he asked for it to be the most striking README
he has. The lead and its chart were left at the defaults (Haiku 5.5, s1, C against D; the site's s1 dot chart) for
him to confirm. **Built:** `README.md` (twelve sections, the outline's order, with "How it works" moved below the lead so
one chart and one sentence come first), `docs/readme/` (the two images), `LICENSE` (decision C; the root now holds
16 of its 16 entries), and an extended generator (81 keys: every C against D split in numbers, both results against
the thesis, the 40-cell verdict grid) with a claim test for each sentence a marker cannot protect. `make check` green,
3,691 Python tests passed and none skipped (the real-files test now runs), 697 frontend. **Record:**
`docs/phases/evidence/phase-7/readme.md` (what reuses his approved words, the images, the four readers, §9's seven
checks, rule zero). **Still open:** decision C's live read of the providers' terms
on model outputs (until then the license line claims only the project's own work); the cost line waits for step 9.
This step and step 3 can ride in one commit (C3 and C4 merged), or C3 first, at his choice.

### Step 5. The plain-English write-up (Delivers 3) [done]

Claude drafts, he reviews (scope decision 1), at `docs/plain-english.md`: what was asked, what was done, what was
found, what it does not show, for a reader who will not open the methods page. Every result sentence from §4's
allowed column; its numbers marked and tested like the README's (§5 covers both files). Flagged as Claude-drafted;
it says so in one line at its top, in his words.

**Done:** in the repo, tests passing, his review recorded.

**As built, step 5 (2026-11-24). APPROVED by him, 2026-11-24, about 11:13 AM, without the top line** (his decision: "I don't see the need for a top line at all"; this departs from the step's text, which asked for a line in his words saying Claude drafted it; the page's maintainer comment records the drafting instead). `docs/plain-english.md`, Claude-drafted: what was asked,
what was done, five findings, six limits, where to go next, with no term left undefined (an interval is "the range
the true difference most likely lies in"; inconclusive is "the runs could not tell"). Its figures use the README's
keys; no new key. **Two tests added:** over one year, Haiku 5.5's A against B is a split on every decision (the
write-up says so in words); and no governed file holds a `[his:` placeholder. The second is kept, though no placeholder is left: it guards the governed files against one being left later. The name guard is clean on a throwaway index; the vocabulary scan finds "stakeholder" only
inside the Roundtable's quoted words. **His question on this pass, answered:** the write-up's reader (one who will not open the methods page) is unlikely to open a docs file either; Claude's read was that the site and the README already serve that reader and recommended a cut; he chose to keep it, since it was finished.

### Step 6. The audit (Delivers 5; scope decision 4; §6) [done]

Claude, Opus. At `docs/v1-audit.md`.

**Done:** every item in §6's five parts marked met, partial, not met or waived (his, with the date), each with
evidence a reader can follow (a commit, a file and line, a run ID, a URL); partials stated as partial; every item the
README leans on flagged.

**As built, step 6 (2026-11-24, Opus; drafted, awaiting his read).** `docs/v1-audit.md`: 56 scored rows across
Parts A to D, plus 12 listed in Part E. **Nothing is not met.** Weakest rows: A 7 met, 5 partial; B 9 met, 3 partial,
1 waived (Phase 1's DoD 7, his); C 18 met, 3 partial; D 9 met, 1 partial. Each ID is a stable token (`A3b`, `B65`,
`C19c`), ready for §5.3's markers at step 8. Every run ID cited was read with `gh run view` that day; the live paths
fetched; `hc site raw-verify` run ("ok: 5247 objects"); one item per phase re-checked (Part B's last column).
**Two partials this doc's §6 did not expect:** the menu-order results are published as data but on no page (A3b, C9;
one of ten option intervals excludes zero, Haiku 5.5 s3 `sell`), and the budget alarm was blind to the first full
run's spend (A5f: the model calls were off AWS, and the tasks carried no cost tag). Two more read stricter than the
expected list: Terraform for everything (A5d, D8b: the operator's IAM user is console-made, by decision A of Phase
0.5) and tokens per sweep (C19c). **His calls, open:** E12 (a methods-page line for the menu-order results and the
token totals, or leave both as partial). **Two notes for step 8's read, not audit rows:** the README's "A full
teardown and re-apply was tested before launch" is true of the post, but the explorer's teardown test ran after the
site went live (2026-11-21); and "a substitution the protocol provides for" rests on protocol §5.1 and Phase 3.5
decision 5. `make check` green: 3,697 Python tests, 697 frontend. The name guard is clean on a throwaway index.
*Dated note, 2026-11-24, about 12:02 PM:* **E12 decided (his), as leaned:** a methods-page line for the menu-order
results, with an M12 entry, built after step 7; the tokens per sweep stay partial. *Dated note, 2026-11-24, after
step 7:* the counts above moved: B 8 met, 4 partial, 1 waived (B65 re-marked); C 17 met, 4 partial (C6 re-marked);
E 13 entries (E13 added). The audit's own summary is the authority.

### Step 7. The audit's sample, re-verified cold (scope decision 4; decision A) [done]

Per decision A. **The sample:** every item flagged "README leans on it", plus enough others to reach at least ten,
chosen across the five parts, including at least one partial. The brief lists the items and their evidence and asks
the agent to check each and report what it found; it does not say which are expected to pass. Claude scores each
report: agrees, disagrees with reason, could not check. A disagreement is fixed in the audit (or the item re-marked)
and re-checked by a fresh agent. Record: `docs/phases/evidence/phase-7/audit-sample/` (the brief, the reports
verbatim, the scoring).

**Done:** every sampled item agrees, or was corrected and re-checked.

**As built, step 7 (2026-11-24, about 12:15 to 1:30 PM; Claude scored, he ran each batch).** Record:
`docs/phases/evidence/phase-7/audit-sample/README.md`, with the four briefs and the four reports verbatim. 28 rows in
three batches (every README row, after the flags were pruned from 36 to 25 as duplicates; A3b and A5f; E6), a new
conversation each, Sonnet 5.5 at the panel's default, no status in any brief. **First pass:** 24 of 27 scored rows
agree; 3 disagree (A2 kept partial with its reason written in; B65 and C6 re-marked partial, the agent's way); 8 rows'
evidence corrected. **The re-check,** six rows to a fresh agent with the corrected claims: six of six agree. **Found
by it and public:** the README and the methods page call both deleted images official, and only one was (audit E13;
the README at step 8, the methods page with E12's change). Also corrected: the tag's time is 01:19 CDT (the tag
object), not the commit's 01:14.

### Step 8. The README read against the audit; the card re-read (Delivers 4; scope decision 3) [done]

Claude, Opus. Each README claim that is not a number cites an audit item (§5.3); Claude reads each claim against its
item and records any mismatch, which is fixed in the README. Then the card (step 0's line) is read against the
finished README and the results; any change is his.

**Done:** no claim beyond its item; his yes or his new line for the card.

**As built, step 8 (2026-11-24, Opus).** Record: `docs/phases/evidence/phase-7/readme-against-audit.md`. **E12 first**
(his decision, approved word for word about 1:38 PM): the methods page reports the menu-order check ("What the order
did", in the goals-and-wordings section), corrects the deleted-images sentence in three places (E13), and adds an M12
entry dated November 24, 2026 (Claude's to change before the Deploy that publishes it, if C5 lands on another day);
A3b and C9 re-marked met. **Then §5.3:** 40 `<!-- audit:ID -->` markers in `README.md`, citing 26 rows, exactly the
rows the audit flags README (A3b added to the flags, a row step 7 sampled); the test in `tests/test_readme_figures.py`
with three planted faults. **The read:** five README claims went beyond their rows and were reworded (the goal as the
only change; "Terraform for everything", twice; the teardown "before launch"; "a substitution the protocol provides
for"; the two official images, twice), and one sentence in `docs/plain-english.md`. **His, 2026-11-24, about 1:55 PM:**
every rewording approved ("the rewordings I all approve"), and the card changed by him, "decision" to "decisions"
("I'm not thrilled about the repo card but it is what it is").

### Step 9. The final cost record (Delivers 6; decision B)

His readings, Claude's record, as at every close.

1. **His readings** of the three pots: the Anthropic Console's billing page, OpenRouter's credits page, AWS's
   billing home, credits page and Cost Explorer (tag `Project`, daily, credits excluded), for the period since
   `evidence/phase-5.5/cost.md`'s 2026-11-03 reading.
2. **Claude's record** at `docs/phases/evidence/phase-7/cost.md`: each pot's draw since 2026-11-03; the cumulative
   total, still an overstatement on AWS because the account is shared, against the $60 re-plan point and the $80
   ceiling; **his OpenRouter spend stated as cash** (R.3 item 5); the AWS credit left, which is Musical Mycelium's too,
   and its 2027-07-30 expiry; the idle bill per decision B.
3. **M8 updated** (its "The final figure ... comes with the write-up" sentence replaced by the figure), the trace test's
   sources extended to the new record; an M12 entry ("a published number: the cost"). Site change, Deploy.

**Done:** the record committed; M8 live with the final figure; the idle bill measured per decision B.

**As built, step 9 (2026-11-25, Opus).** Record: `docs/phases/evidence/phase-7/cost.md`, from his readings about 3:45
to 3:51 AM. **Drawn since 2026-11-03 by this project:** Anthropic none (the $0.11 the credit fell is another project's
key, a game of his, by the Console's API keys page), OpenRouter none, AWS $0.12 under the tag and at most $0.16 for
the shared account. **Cumulative: at most about $46**, under $60 and $80. **His OpenRouter cash** since 2026-10-15:
$12.70 with the card fee. **AWS credit left** $135.38, expiring 2027-07-30. **The idle bill:** about $0.17 a month, from
$0.04 over 2026-11-14 to 2026-11-20, decision B as amended the same morning (the window before go-live, his choice
not to hold the phase); the charge type filter was not set, and the figure is positive, so no credit was netted.
**M8** now gives the final figure and the idle bill, sourced to the new record, and an **M12 entry** is dated
November 25, 2026 (Claude's to change before the Deploy that publishes it, if C6 lands on another day). The trace and
digit tests pass, 655 of 655 explorer tests. **The December note is dropped** (his, about 4:12 AM).
**The M8 and M12 wording is Claude's draft, approved by him (about 4:21 AM: "fine, approved").**

### Step 10. The Short, Gemini first (Delivers 12; decision R-A as amended by D; §7)

Him and Claude. Before the post. §7 holds the detail.

**Done:** one Short he wants, its check record committed, the scope sentence on it.

**As built, step 10 (2026-11-25, Opus).** Record: `docs/phases/evidence/phase-7/short/README.md`. **Attempt 1 of 3 kept**
(his, about 5:02 AM): a Gemini Notebook Short, 720 by 1280, from the live methods and story pages, steered by Claude's
topic as he revised it (the narration ends on the result; the scope on an end card). **His gate, about 4:40 AM:** the
presentation first, with a floor (a wrong number or direction, the people presented as real, a claim about real
companies, executives or AI in general, a missing scope); it passed. **Two ffmpeg edits:** the label "Stakeholders"
restored over the bar from the video's own frame (his catch), and a six-second end card in his words with the scope
sentence, the second model's split and the AI-generated label. **Commit order:** steps 9 and 10 go in one commit
(his, 2026-11-25), C6's step 9 with C7; step 11 follows in its own commit.

### Step 11. The hosting plan, the dated reminders, the after-v1 list (Delivers 10; scope decision 5)

Claude records, he decides the plan's content. In KNOWN-GAPS, the REMINDER entry of 2026-10-04 rewritten as a dated
checklist (the re-scope's R.3 item 4):

- **By 2027-06-30:** serve the built site from the free host directly (Vercel today; its terms read live then), then
  tear down the CloudFront distribution, the bucket and the ECR repository with the teardown workflow's knowledge of
  what `main` holds; the raw text is already in the repo. Or his decision, before that date, to keep AWS on a stated
  cash budget. **Extend the budgets past 2027-10-01** if AWS stays.
- **Monthly from close:** his Cost Explorer reading of the idle bill, one line each, until the plan is carried out.
- **2027-01-02:** the dev key's date, if step 15 has not deleted it.
- **From 2027-08-08 (60 days before 2027-10-07):** watch for Anthropic's retirement notice for Haiku 5.5; on retirement,
  fill step 2's retirement field. For `gpt-oss-120b`, the line is filled if its pinned host stops serving it.
- **A calendar entry** for 2027-06-01 (a month's margin), if he wants one: he makes it, or Claude makes it through his
  calendar connector with his explicit yes for that one entry.

**The after-v1 list** (`ROADMAP.md` §5): confirmed item by item; the two stale lines (§0 item 5) get dated notes.

**Done:** the checklist in KNOWN-GAPS with its dates; the ROADMAP notes; his yes on the plan.

### Step 12. Version 1.0.0, the tag and the release (Delivers 8)

1. **Claude:** `1.0.0` in `pyproject.toml`, `src/horizon_compact/__init__.py` and `uv.lock` (`uv lock --check`
   agrees); `make check` green. This commit starts Deploy's image build and `main` apply, as at Phase 6.5's close.
2. **The release notes:** Claude drafts on his grant (scope decision 1), flagged with the watermark; passed through
   the name guard's message check (`python -m horizon_compact.privacy.guard commit-msg <file>`) and read for rule
   zero.
3. **His, after Deploy is green:** an annotated tag `v1.0` (Musical Mycelium's convention, `v1.1`) with a message
   that names no company; `git push origin v1.0` (the pre-push guard reads tags); `gh release create v1.0 --title
   "..." --notes-file ...`. Claude gives each command one at a time, with the output to look for.

**Done:** the tag and release exist (`gh release view v1.0`); Deploy green on the version commit.

### Step 13. The launch post (Delivers 9; scope decisions 1, 2, 6)

His words: Claude interviews, outlines and critiques line by line, never drafts unless he asks on that pass.

1. **The outline** (`planning/06` §6.1): it opens with the question or the Mayflower line, not a finding stated as a
   verdict; one chart (or the Short, which carries it; §0 item 7); one sentence from §4's allowed column with its run
   count; the link to the site. **His standing decision of 2026-10-05:** a section "The hardest part" on AWS, the
   quotas set to zero and the support case, and how the build continued (the move to Anthropic's API and OpenRouter,
   2026-10-11). Claude offers the facts, from KNOWN-GAPS BLOCKED 2026-10-05; the tone is his. The real-case result, if
   mentioned, in R.1's order (the pre-registered rule found none first).
2. **The checks:** `planning/06` §9's seven, on the post and its image or video; the vocabulary recheck if the post
   date is after 2026-12-12; step 1's second rule-zero pass; LinkedIn's Post Inspector on the link (it matched at
   Phase 6.5's go-live; re-run if the landing page's card changed).
3. **His date,** set against the week (Thanksgiving is 2026-11-26). DoD 6 is met when it is published or when he
   has set its date.

**Done:** the post published, or its date set by him, after every check.

### Step 14. The second post, planned (scope decision 6)

An outline only, with him: the method post, a week or two after the first, on the pre-registration, the sealed
wording, and what went against the thesis (the two B vs D entries). His words, his date. Recorded in the close.

### Step 15. The close

1. **The dev access key deleted** (Delivers 11): his, in the IAM console (`horizon-compact-dev`), after every step
   that needs a laptop read of AWS (none is planned in this phase; the cost readings are consoles). Claude confirms
   by `aws sts get-caller-identity --profile horizon-compact` failing with an invalid-key error, which he runs.
2. **The phase's DoD audit** (§9) in this doc, with evidence; the ROADMAP's Phase 7 row closed with version `1.0.0`;
   START HERE rewritten for a project at v1.0.
3. **The public-prose record:** a list of every public piece and who wrote it (his words, his edit of a Claude draft,
   or Claude's draft at his request), so the watermark question has a factual answer later.

## 4. The README's outline

The order is `planning/06` §6.1's, with the scope's Delivers 2. **Who writes:** per step 4. **Every number** is a
marked figure (§5); **every non-number claim** cites an audit item (§5.3).

1. **The name and the question, in the first two sentences:** the Mayflower Compact as an agreement "for the general
   good" and the UN Global Compact as the modern corporate meaning (`planning/06` §6.4: one idea, an agreement about
   whose good a group governs for; the colony is not celebrated). Then the question.
2. **The Roundtable frame** (`planning/06` §1): the 2019 statement and the 2024 retrospective's "in the long term"
   words; what the grid tests, in its narrow form.
3. **The scope sentence,** in substance, before any result: a model under objectives, not executives.
4. **The lead result** (R.1): the "C and D split" row, in §4's allowed wording, the scenario and chart his choice, with
   run counts and intervals; the inconclusive cells said as inconclusive; one image (light and dark).
5. **The results against the thesis** (`planning/06` §9 item 7): the two Haiku 5.5 B vs D "no split" entries, stated
   as plainly as the lead, above the end of the page, linking the site's section.
6. **The real cases, in R.1's order:** the pre-registered rule found no case; five exploratory closures, three with a
   leakage disclosure; all 20 readings "no good match"; no case can be re-run from published inputs.
7. **What was built:** Python on Fargate, S3 write-once records, Terraform for everything, OIDC deploys, the name
   guard, the `prereg-v1` tag, the static explorer; the models through Anthropic's API and OpenRouter after Bedrock
   was blocked (a substitution, not a cut). **The honest note on containers** (`planning/02` §2.3): the workload is API
   calls a laptop could run; the container pins the code behind every official result by image digest and keeps a
   sweep of hours off a laptop.
8. **Check it yourself:** the site, the methods page, the pre-registration tag and release, the raw text and its
   manifest, the re-scoring check in CI, the audit, `make setup` then `make check`.
9. **Limits,** linking M9; **cost,** the final figure (step 9) with its overstatement stated; **the models' dates**
   and Haiku 5.5's tentative retirement.
10. **License** (decision C) and **layout** (one short table).

**Not in the README:** a verdict on any company or executive; "ESG", "stakeholder capitalism", or "stakeholder"
unattributed (`planning/06` §3.1); personas for the objectives (§6.2); the planning docs' Claude-drafting line, which
lives in `docs/planning/README` (`planning/06` §10 item 4).

## 5. The marker scheme and its tests

Musical Mycelium's pattern (`tests/test_published_numbers.py`), extended with the methods page's digit census
(`web/src/explorer/methods.test.ts`, "holds no digit in its words that is not a figure, a name or a protocol
section").

### 5.1 The markers and the generator

- **A marked figure:** `<!-- n:key -->value<!-- /n -->`, invisible on GitHub. Keys are stable names
  (`haiku_cd_s1_difference`, `grid_runs_haiku`, `cost_cumulative`).
- **The generator,** `src/horizon_compact/site/readme_figures.py` (beside the explorer-data builder): computes every
  key from the committed sources only (the three official results files, `web/explorer-data/`, the case results, the
  phase 7 cost record), formats each as the README shows it (the same rounding as the site), and returns a mapping.
  No network, no AWS client.
- **`make readme`** rewrites the values between markers in `README.md` and `docs/plain-english.md`, and nothing else.

### 5.2 The tests (in `tests/`, run by `make check` and CI)

1. **Every marked figure matches its source.** Fails with the stale keys and "run `make readme`".
2. **Every marker names a key the generator computes.** A typo would leave a number looking protected.
3. **Every key the generator computes is still marked.** Deleting a marker and typing the number by hand fails here.
4. **The digit census.** Outside markers, every digit in either file belongs to an allowed class: a date, a year
   (1620, 2019, 2024 and the run years), a model name (Haiku 5.5, `gpt-oss-120b`), a protocol or planning section
   reference, a version, or an entry in a short explicit allowlist with a reason per entry. Anything else fails.
5. **The scope sentence is present** in substance in both files (a fixed phrase test, his wording once approved).

### 5.3 Claims tied to the audit

Each claim that is not a number carries an invisible `<!-- audit:ID -->` after it. A test checks every cited ID
exists in `docs/v1-audit.md`, and that no README claim cites an item marked "not met". It cannot check that the claim
matches the item; step 8's read does, and **the audit is re-read against the README at every later change** (a line in
the README's own maintainer note, and in CLAUDE.md's how-the-work-is-done list at the close).

## 6. The audit

At `docs/v1-audit.md`. One table per part; each row: ID, the promise (quoted, with its source), status (met / partial
/ not met / waived, his, dated), evidence, and "README" if the README leans on it. **Partial is said as partial.** The
expected partials below are Claude's reading before the audit runs; the audit decides.

- **Part A, `planning/00` §8 (v1.0's definition of done), six items.** Expected: the grid on at least one model, met
  (two models); **at least three real cases, partial** (five ran and are presented by type, but all are exploratory
  and all closures; Phase 5's done-when "including an invest or retool case" is not met); the wording and
  shuffled-order checks, to be read (the wording result is in the results files; the position-effects analysis is in
  `analysis/robustness.py`, and whether its output is published on a public surface is checked); the explorer live,
  met; the AWS list, to be read item by item (budget alarm before the first full run, OIDC, least privilege, Terraform
  for everything); **the hostile re-run, partial** (the grids, yes, by the re-scoring check and the raw text; the
  cases, no: no dossier is published, which the methods page says).
- **Part B, every phase's definition of done** (0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 5, 5.5, 6, 6.5): each phase's own
  DoD audit is cited, not redone; its status is carried (Phase 1's DoD 7 is **waived**, his; Phase 6.5's rows 5 and 6
  carry their departures and qualifications). Claude spot-checks one item per phase against its evidence.
- **Part C, `planning/07`, the eval spec "Phase 7 audits against":** its commitments section by section (the verdict
  rules, the family correction, the wording and sealed-wording rules, position effects, failures and refusals,
  thinking, the matcher, the real-case rules, publishing every raw response), each pointed at where it was honoured
  or where it changed (errata, the dated patches).
- **Part D, the one-way doors** (`planning/05` §3.1; `CLAUDE.md`): provenance on every call; raw responses kept
  write-once; official and development results apart; one capture method; content as hashed data; the public/private
  boundary; Terraform for everything with the OIDC provider looked up; the v1 model set fixed before real cases.
- **Part E, what is still open:** every KNOWN-GAPS entry still OPEN, BLOCKED or REMINDER, listed with one line on why
  it does not block v1 (Musical Mycelium's deploy role, its to fix; the hidden key prompt; the pinned-host matcher;
  Bedrock; the hosting reminder).

## 7. The Short, Gemini first (decision R-A, as amended by decision D)

**One Short, made well** (decision D): §7.2 first; §7.3 only if §7.2 gives nothing that passes, or nothing he wants.

### 7.1 What the Short must be

About a minute; vertical (9:16 or 4:5, chosen at the step from LinkedIn's help page read then);
captions burned in, since the feed plays muted; **the scope sentence in substance** (an end card is enough); every
figure on screen and in the narration on the site; no result past §4's allowed column; no company; the AI-generated
label where any part is generated. **Narration that speaks for him in his post is his words** (the re-scope's R.6).

### 7.2 Candidate 1, the Gemini Short

His notebook (memory off, the "Chats from Gemini" entries unticked, as in Phase 6.5 §6 item 2), sources narrowed to
the methods page and the story (attempt 3's narrowing of Phase 6.5's step 9), rebuilt from the live site if any page
changed since the pack was printed. Claude writes the steering prompt; he generates. **Capped at three attempts.** Its
words are the tool's, so the post labels it AI-generated. If steering alone does not hold the facts and a script is
needed (as the Explainer's attempt 4 needed one), the script is his words, Claude outlining and checking; a
Claude-written script would repeat Phase 6.5's departure, and only he can choose that, on that pass.

### 7.3 The fallback, cut from the site's own renders (only if §7.2 gives nothing he wants)

- **Pictures:** the real pages and charts, captured headless (light theme, or dark if he prefers), at the vertical
  size; motion by pan, zoom and cross-fade in ffmpeg, and a highlight drawn over the bar being described. No
  generated imagery.
- **Words:** his script, about 130 to 150 words for a minute; Claude interviews, outlines from R.1 and critiques, and
  checks every figure.
- **Voice:** his, recorded on his phone or laptop, or on-screen text only, his choice. No synthetic voice unless he
  asks (then ElevenLabs, its cost and licence terms read first, as in Phase 6.5 §1's table).
- **Tools:** ffmpeg (version recorded), the headless browser already used, libass for burned captions. All local, all
  free; scripts in `scratch/`, never shipped.

### 7.4 The check, whichever is made

Phase 6.5 §6 item 4's check, reused: frames every two seconds, every frame's text read against the data and §4;
narration transcribed locally (`faster-whisper`, the version recorded at install; `scratch/p65-s9-check.sh` as the
starting point) and read line by line; **he watches each once** for tone and pronunciation. A failure in the Gemini
Short is fixed by steering and regenerating; in the fallback, by editing, since its pictures are the site's.

### 7.5 The choice and the record

He decides which attempt ships. `docs/phases/evidence/phase-7/short/README.md`: every attempt's check record, the
steering prompts, his script (if one was used), the tools and versions, the chosen file's sha256 and length. **The MP4 is not
tracked** (a binary the guard cannot read; it lives on LinkedIn and in his files); the record is. If he wants it on the
site too, that is a site change with M11 and M12 entries, the media budget checked, and a step added here first.

## 8. The commit order

His commits, each after `make check` and the guard; Claude provides each command, one at a time.

| # | Message | Holds | Starts |
|---|---|---|---|
| C1 | `phase 7: re-scope and implementation doc` | Phase 6.5's held START HERE and row 1 note; the re-scope; this doc, approved; the scope doc's header line | CI only |
| C2 | `phase 7: c2 rule-zero sweep and dates` | step 1's record; step 2's code, data and M12 entry | CI, Deploy (image, apply and site) |
| C3 | `phase 7: c3 readme machinery` | step 3 | CI, Deploy (image and apply, since `src/` changes; no task) |
| C4 | `phase 7: c4 readme, write-up and license` | steps 4 and 5; `LICENSE` (decision C) | CI |
| C5 | `phase 7: c5 audit` | steps 6, 7 and 8 | CI |
| C6 | `phase 7: c6 cost and hosting plan` | steps 9 and 11; M8 and M12 | CI, Deploy (site) |
| C7 | `phase 7: c7 the short` | step 10's record | CI |
| C8 | `phase 7: close, version 1.0.0` | step 12's version; step 15's audit, ROADMAP and START HERE | CI, Deploy (image, apply) |

Then his tag and release (step 12 item 3), then the post (step 13). A finding that changes an earlier commit's file
goes in the next commit with a dated note, not an amend. C7 may land earlier: the Short can run alongside steps 2 to 9.

## 9. Definition of done

The scope doc's eight, plus the re-scope's two, each with the proof that will show it.

| DoD | Proof |
|---|---|
| 1. The rule-zero sweep clean | `evidence/phase-7/rule-zero.md`, both passes |
| 2. The README in the repo, numbers tested by `make check`, claims checked against the audit | §5's tests in CI; step 8's record |
| 3. The audit published, every item marked with evidence | `docs/v1-audit.md`; step 7's record |
| 4. The final cost record on the methods page, the idle bill measured | `evidence/phase-7/cost.md`; M8 live; decision B's window |
| 5. The `v1.0` tag and release exist (his) | `gh release view v1.0` |
| 6. The launch post published, or its date set (his), after `planning/06` §9's checks | step 13's record |
| 7. The hosting plan recorded with its dated reminder | KNOWN-GAPS checklist (step 11) |
| 8. `make check` and CI green; every commit through the guard | C1-C8's CI runs and Deploys |
| 9. The dev access key deleted (or on 2027-01-02 if the phase runs past it) | step 15 item 1 |
| 10. The chosen Short passed the check and carries the scope sentence | `evidence/phase-7/short/README.md` |
| *Added:* 11. Every results surface names its model and run dates from data (Delivers 7) | step 2's tests and M12 entry |

## 10. Cost

**No model call for the experiment, and no paid model call planned.** The cold agents (step 7) and the web reads run
on his Claude plan; the Gemini Short on his Google account (its plan access found by trying); the fallback cut, if needed, on local
free tools. AWS: the Deploys this phase starts (image builds and `main` applies at C2, C3 and C8, no task run; site syncs at C2 and C6) and the idle site,
inside the rounding of the cumulative figure (at most about $46 at Phase 6.5's close). **A cost appears only if** he
chooses ElevenLabs for the Short's voice (read first) or a third tool under decision D's $5 ceiling.

## 11. Risks to the build

- **The Short becomes a second four-attempt grind.** Mitigation: the three-attempt cap on the Gemini Short, then the
  fallback, whose pictures cannot invent anything.
- **The README is finished before its numbers are under test.** Mitigation: step 3 comes before step 4, and the digit
  census fails on any number typed by hand.
- **The audit is graded by the hand that built the project.** Mitigation: the cold sample (step 7), partials stated
  as partial, and Part B citing each phase's own audit rather than restating it.
- **A Deploy in the idle window blurs decision B's measurement.** Mitigation: the window starts after C2's Deploy;
  any Deploy inside it (C3 likely) is listed beside the figure, and its ECR cost is small and part of the idle bill
  anyway. No task runs in the phase.
- **Thanksgiving week.** The post's date is his; nothing in steps 1 to 12 depends on it.
- **Something identifying in an image or the Short.** Mitigation: both are read as images and frames by Claude at step
  1's second pass; the Short's frames are already read by §7.4.
