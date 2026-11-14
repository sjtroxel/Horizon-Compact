# Phase 6.5 — Methods and Release: IMPLEMENTATION (v0.6.5)

> **IMPLEMENTATION doc. DRAFT, NOT APPROVED.** Started 2026-11-14, about 2:20 AM (Opus), the day after Phase 6 closed
> (`21262a6`). **Written so far:** §0 (the scope review), §1 (the disclosure ledger, two passes), §2 (the decisions
> it raises; none taken), §3 (the methods page's outline) and §4 (facts checked live, the video first). **Not yet
> written:** the other facts checked live, each decision's options and recommendation (C's are listed), the checks'
> build, the video plan, the go-live checklist, the steps, the commit order and the definition of done. Those follow
> once he has seen §0 to §4.
>
> Sources so far: the scope doc (`docs/phases/phase-6.5-methods-and-release.md`, 2026-10-04); the Phase 6 scope doc and
> IMPLEMENTATION doc (§0 and §34.3, what Phase 6 hands on); `KNOWN-GAPS.md`; `docs/phases/evidence/phase-4/raw-manifest.json`;
> `git log` over `infra/`; and every line under `docs/` and `experiment/` (archive excluded) that says "methods page",
> read in its context (§1).
>
> **The scope doc is amended when this doc is approved,** as Phase 6's was (its header note of 2026-11-09): one dated
> note in its header pointing here, and a dated note on each line that a finding here, or a decision of his, changes.
> Until then the scope doc stands as written and is read through §0.
>
> **Rule zero governs every line.** Real cases appear only by label and type. No memo text from a real case is quoted.

## 0. The scope review: what changed since 2026-10-04

Read the scope doc with these changes. Each is measured or cited; none lowers a rule.

1. **The raw text to publish is about 105 MB.** Delivers 2 and DoD row 8 publish the full text of Phase 4's pilot and
   official objects: 5,247 objects, 104,785,272 bytes by the manifest's own sum (measured 2026-11-14). The repository's
   `.git` is about 50 MB today, so committing them would roughly triple it. Where they are published (the repository,
   a GitHub release asset, or a path on the site) decides what the CI re-scoring job reads. Decision A (§2).
   **Not yet seen by Claude:** what the objects hold beyond the prompt, the reply and the provenance. Claude's deny
   list keeps it out of S3 (Phase 4 runs doc §5.4), so before anything is published, his read-only pull and a scan for
   anything that must not be public (an account number, a key, a request header) come first.
2. **No real case can be re-scored or rebuilt from published inputs.** All five dossiers were withheld by the
   re-identification check (Phase 5.5 §6.6), and every raw case record carries its dossier. So Delivers 3's sample
   "one real case whose dossier was published" cannot exist; the re-scoring check and the prompt-reconstruction check
   cover the fictional company's grids and the thinking sub-study only. The scope doc already provides for it (DoD 3:
   "Where a dossier was withheld, the page says that case cannot be re-run, and why"). A dated note, not a decision.
3. **The planning's reproducibility promise, as patched, cannot be kept for the cases.** `planning/00` §8 (amended
   2026-10-03, patch P27, `planning/09`) says a hostile reader can re-run the experiment "from the published inputs,
   including the anonymized dossiers." No anonymized dossier is published. The methods page has to say this in those
   terms, near the top of its cases section, not only in the known limits. The grids keep the promise in full.
4. **"No good match will be rare," said before the results; all 20 case readings are no good match.** Phase 3's
   matcher calibration (`evidence/phase-3/matcher-calibration.md`, and the IMPLEMENTATION doc's finding 6) wrote that
   "no good match" would be rare and that the methods page must say so. Phase 5.5's reveal (its §6.4) found every one
   of the 20 readings across the ten case results to be no good match. A hostile reader will set the two side by side.
   The methods page states both, with their dates, and what is and is not known about why. Claude has not checked why,
   and no explanation goes on the page that a measurement does not support.
5. **The teardown test probably does not re-run.** Delivers 8 re-runs it "if `main` changed since Phase 1.5." The only
   commit under `infra/` since the Phase 1.5 teardown (`f49d530`) is its own evidence commit (`cf1fb71`). That holds
   unless go-live adds infrastructure: Phase 6 left a true 404 status (a CloudFront Function, or a rule in the Vercel
   rewrite) to this phase (Phase 6 IMPLEMENTATION doc, C3 notes). Decision B.
6. **The video is a deliverable to make work** (his, 2026-11-14: videos make the project digestible for casual
   readers, "as valuable as ever"). Scope DoD 5 still allows not publishing it, with the reason; that is his last
   resort, not a fallback this doc plans around. Open: the tool the scope doc calls "Gemini Notebook" (what it is
   called today, whether it makes video, whether it is still free), checked live; narration (the tool's, or
   ElevenLabs at a named cost); and hosting with **no visitor tracking** (scope rule) under the site's content
   security policy and its size budgets. Decision C.
7. **The cold-read test meets a local-only preview.** Phase 6 decision 2 kept the preview off every public host. The
   scope doc's agent is Claude in Chrome, which runs in his own browser, so it should be able to open a preview served
   on his machine; checked live before the brief is written (the Phase 6 IMPLEMENTATION doc §13 decision 2 left it so).
8. **Phase 6 hands on five items** (its §34.3): the go-live commit that switches Deploy from the `placeholder` build to
   the explorer; the grid memos' full-text publication; the methods page's half of KNOWN-GAPS OPEN 2026-10-31 (both
   matcher notes); the share cards' link previews, testable only once public; and the cold-read agent. Two serving
   details also wait for go-live: Deploy must not sync `dist-explorer/.vite/` (Phase 6 IMPLEMENTATION doc, C3 notes),
   and the `noindex` header and meta tag come off in the go-live deploy (Phase 1.5 decision on `noindex`).
9. **The models are the fallback set,** not the scope doc's: Haiku 5.5 through Anthropic's API (main) and
   gpt-oss-120b through OpenRouter, after Bedrock was blocked (Phase 3.5 §23, 2026-10-11). The methods page's
   "models, dates" section and its cut list carry that change and its reason; Nova Pro's planned role, and its default
   temperature recorded in Phase 0.5, become history on the page, not a description of what ran.
10. **Small faults in the scope doc:** DoD has two rows numbered 8; Delivers 6's "memo name scan confirmed on what is
    actually deployed" is now met by construction, since the explorer holds every real-case memo's text (Phase 6
    decision 5, KNOWN-GAPS CLOSED 2026-11-09), while the repository copies stay as published.

## 1. The disclosure ledger (two passes, 2026-11-14)

Forty-odd places in the record say something is "for the methods page." They were written over six weeks, in eleven
phases, and nothing gathers them. This ledger does. Each line: what the page must say, and where the obligation was
written. **Status** is one of: *stated* (the fact is settled and only needs writing), *his* (the record names it as his
to write, or a sentence that speaks for the project), or *check* (a number or claim to re-verify before it is written).
The page's section order is `planning/06` §6.1's, as the scope doc's Delivers 1 lists it.

**How it was made, and what it can still miss.** First pass: a search for "methods page" across `docs/` and
`experiment/`, the archive excluded, each hit read in context (140 hits, about 45 of them obligations, the rest
mentions). Second pass: the same tree for "stated as a limit", "known limit", "known simplification", "residual
risk", "to disclose", "stated on the page", "reproducibility gap" and "for the write-up" without the words "methods
page" (17 hits), and both KNOWN-GAPS RECORDED entries read in full. The second pass added lines 20a, 20b and 40, and
settled three *check* lines from the record (13, 18, 21); the reads after it settled the other five (14, 17, 31, 38, 39); 14 from Phase 3's simulation summary, which had measured both power figures under the Newcombe rule. **No line is left at *check*.** **What it can still miss:** an obligation in words none of
these searches uses. A grep miss is not proof of absence; the four readers' pass on the drafted page (scope Delivers
6) is the backstop.

### 1.1 What is measured and what is not (first, `planning/04` §1.3)

| # | The page must say | Source | Status |
|---|---|---|---|
| 1 | The claim is always "under objective X, the model ...", never about executives; the limit is in the first section, not a footnote | `planning/04` §1 (risk on overreach, mitigation) | stated |
| 2 | Re-asking a model gives a new sample, not the same numbers | scope doc Delivers 1; `planning/05` Phase 6 row | stated |
| 3 | Stated reasons in filings are not verified; no case is called AI-washing | `planning/06` §2.1 | stated |

### 1.2 The objectives, the scenarios and the lever menu

| # | The page must say | Source | Status |
|---|---|---|---|
| 4 | The parallel objective frame ("Create value for [who], over [when]") costs some realism and buys clean comparisons | `planning/00` §5; `planning/01` §2 | stated, his words for the trade |
| 5 | Claude drafted the instrument's text (dossier, scenarios, wording templates) and he reviewed every line; the same-family question and its two answers (another vendor's review) | Phase 2 scope decision 2 | stated |
| 6 | Known simplifications of the fictional company: the same revenue per employee at every plant; no orders, backlog or outlook | KNOWN-GAPS RECORDED 2026-10-06; Phase 2.5 neutrality checklist; Phase 2 IMPLEMENTATION doc | stated |
| 7 | The wording order is shuffled per run from the seed (Phase 2.5 decision 3 (a); a fixed order was option (b), not taken) | Phase 2.5 scope doc, decision 3; `planning/07` §4 and §7.2 | stated |

### 1.3 Models, dates, run counts

| # | The page must say | Source | Status |
|---|---|---|---|
| 8 | Sampling is never set; each model runs at its default, recorded; the same number would not mean the same on two models | protocol `prereg-v1` §5.3; `planning/07` (the sampling rule); Phase 0.5 decision 7 | stated; defaults to be re-read from the provenance |
| 9 | What the fallback set gives up: reach (a small current model and an open-weights model, not the larger models companies would use) | Phase 3.5 IMPLEMENTATION doc §23.6 | stated |
| 10 | Two official images are no longer in the registry (Phase 4's and Phase 1's skeleton); the records keep each digest, the code is pinned by the tag, the archive and each record's `git_sha`; a run cannot be repeated on the identical image | KNOWN-GAPS (ECR lifecycle entry, measured 2026-11-04); Phase 1.5 IMPLEMENTATION doc §3 and §17 | stated |
| 11 | Case runs: the code that computes is the tag's (`hc protocol check` byte-identical), run from `main` with the case driver; protocol 14's purpose kept, not its letter | Phase 5.5 IMPLEMENTATION doc decision on the run tree | stated |

### 1.4 The pre-registration, the statistics and what changed after the tag

| # | The page must say | Source | Status |
|---|---|---|---|
| 12 | The share rule's measured worst false-split rate, 0.43% against the nominal 0.3125%, found by simulation before any result existed; held approximately (his decision 2026-10-09) | Phase 3 IMPLEMENTATION doc §20c finding A; `evidence/phase-3/plain-english.md` | stated |
| 13 | Choice-rate precision by Newcombe: about ±25 points at 50% and ±16 at 5% (not `planning/07` §8's Wald figures, ±27 and ±12) | Phase 3 IMPLEMENTATION doc §18, finding (a); `planning/07` §8 already patched to ±25 and ±16 | stated |
| 14 | Power on a choice rate at the cap (20 runs a wording): a true 30-point difference near 50% is called a split about 63% of the time, a 35-point one about 80%. **Measured** under the rule that ran (the exact binomial sum through the analysis's own Newcombe interval and verdict): 62.9% (0.65 against 0.35) and 81.9% (0.675 against 0.325) | `planning/07` §8; `evidence/phase-3/simulation-summary.md` §3 (rows `choice_stated`; code and data hash `705078047b9ec370`) | stated: the page gives the measured figures |
| 14a | Reachability of "no split": 49.7% at worst, against about 54% stated where the cap does not bind (a stated residual, written into `planning/07` §8) | Phase 3 IMPLEMENTATION doc §19a, DoD 3 | stated |
| 15 | The failed-run bound is the worst case for the difference, not for the interval's width | Phase 3 IMPLEMENTATION doc (step on the sensitivity bound) | stated |
| 16 | "No good match" was expected to be rare; all 20 case readings are no good match (§0 item 4) | `evidence/phase-3/matcher-calibration.md`; Phase 3 IMPLEMENTATION doc finding 6; Phase 5.5 §6.4 | stated, both with dates |
| 17 | Failures, measured, beside the planning's warning that a model failing more than about 2% supports few firm verdicts: Haiku 10 of 990 grid runs (1.0%), gpt-oss 39 of 1,200 (3.25%), the thinking sub-study 0 of 100; gpt-oss `s2` 27 of 300 (9.0%), with 4 cells over the 10% limit, which is why one of its comparisons is not assessable; Haiku `s2` runs 6 a cell, where one failure (3 cells) already drops a wording (protocol §7.4, pre-registered) | Phase 3 IMPLEMENTATION doc (open items at step 10); protocol `prereg-v1` §7.4; the three results files, counted 2026-11-14 from `cells` (attempted minus valid) | stated; recount by the page's own build, not by hand |
| 18 | The run-code change log from Phase 4, the errata, and whether any `prereg-v2` exists | scope doc Delivers 1; `experiment/protocol/errata-v1.md` (41 lines); Phase 4 runs doc (the run-code change and errata steps) | stated; no `prereg-v2` exists |

### 1.5 The real cases: how they were found, and what cannot be re-run

| # | The page must say | Source | Status |
|---|---|---|---|
| 19 | The disclosure asymmetry and exactly how cases were found; filings show decisions taken, not options rejected or intentions; five cases cannot represent all companies | `planning/01` §4.3 and §4.8; `planning/04` §2 | stated |
| 20 | No candidate met the pre-registered rule; the five are exploratory, selected under §4.6.5 after it found none, each with its label | search-half doc §4.6.5; `cases.json` | stated, the label verbatim |
| 20a | The pre-registered result first: the rule found no case, shortfalls 2 (closure), 2 (retool) and 1 (ai), reported and never filled; the five exploratory cases are all closures, so retool and ai have no case at all | search-half doc §4.6.5 A.1; `cases.json` | stated, before any case result |
| 20b | **Leakage.** Three of the five (`pre-11`, `pre-25`, `pre-224`, §4.6.5 steps 3 and 4) were first disclosed before Haiku 5.5's training cut-off (June 2026), so they may be in its training data; the window's protection was replaced for them by a knowledge probe that found no recall in either official model or the extraction model (his decision 2026-10-19). Every relaxation step is logged with what changed, why and what it let in | search-half doc §4.6.5 A.3 and B.3; `cases.json` labels; `planning/00` §4 principle 4 ("every ... known limit, leakage included") | stated; a probe that finds no recall is not proof of absence, and the page says so |
| 21 | The public selection log, by case type, without names | `planning/07` §10.0; published as `docs/phases/evidence/phase-5/selection-public.json` and `exploratory-public.json` | stated; the page links both |
| 22 | Rules set after the tag and before the search (the subject and size from the first-disclosure document, every other figure pre-cut-off, §4.6) | search-half doc §4 decision on scenario facts | stated |
| 23 | §4.6.3's headcount floor (167 as stated): the interpretation, the reader's objection in its words, and the answer, beside the rule | search-half doc §4.6.3 | stated |
| 24 | What no one reads: a total in a part of a document no search term reached, with the terms | search-half doc §4.6.2 | stated |
| 25 | The excerpt unit can keep a criterion 3 reason out of the reader's sight (another item of the same report); it changed no outcome | search-half doc Stage D notes; KNOWN-GAPS (closure window) | stated |
| 26 | The reader's rubric: blind-first reading asked, not enforced; its training cutoff inferred from its release date, not stated by the vendor | search-half doc Stage C notes; KNOWN-GAPS | his |
| 27 | The brief's reading of the name definition (§12.8): a name counts written in full or in a form a reader would take for it | search-half doc step 10a, his decision | his |
| 28 | The summarizer is the main model's vendor (a Claude model summarizes for a Claude model); the probe and the foreshadowing check are the measured guards | search-half doc decision on the summarizer | stated |
| 29 | A decision mentioned first only on an earnings call can be missed (transcripts out of scope) | Phase 5 scope doc, known risks | stated |
| 30 | One decision filed twice as two candidates: no rule was written, and the case did not recur | KNOWN-GAPS CLOSED 2026-10-27 | stated |
| 31 | Criterion 4 is checked in two parts, the shape then the total (§4.6.2, his decision 2026-10-17, set after the tag and before any criterion 4 read); every rejection on criterion 4 is still read, a failed total included (the reader judges only whether the figure is the total) | search-half doc §4.6.2 A and items 4-5; KNOWN-GAPS CLOSED 2026-10-17 | stated |
| 32 | The recognition probe sent the dossier file, not the decision prompt's system text; the words are the same | Phase 5.5 IMPLEMENTATION doc §3 item 10 | stated |
| 33 | No dossier is published, so no case can be re-run from published inputs; the planning's promise (§0 item 3) is not kept for the cases | Phase 5 decision 5; `planning/00` §8 (P27); Phase 5.5 scope doc | stated, plainly |
| 34 | The 263 held memos were held because they repeat their case's text while every dossier is withheld, not because any named a company; the rule cannot tell a placeholder label from a product term | `evidence/phase-5.5/run-log.md` §6.5 | stated |
| 35 | The search check on the descriptions ran once, on one engine, on one day; results change over time | `evidence/phase-5.5/run-log.md` §6.6 | stated; the scope doc re-runs it (Delivers 6) |
| 36 | Both matcher behaviors: a five-way exact tie yields an arbitrary nearest objective that `depends_on_reading` inherits; a one-line reading averages a structural zero into its distance | KNOWN-GAPS OPEN 2026-10-31 | stated; closes that entry |
| 37 | Published real-case memos repeat distinctive terms from their withheld dossiers (845 of 1,237, an upper bound); the explorer holds real-case memo text; the repository copies stay | KNOWN-GAPS CLOSED 2026-11-09; Phase 6 IMPLEMENTATION doc §22 | his: how much the page says is his call, and the terms themselves never appear |

### 1.6 Cost, the cut list and known limits

| # | The page must say | Source | Status |
|---|---|---|---|
| 38 | **The cut list was not applied:** nothing in `planning/05` §5.1 was cut (Phase 5.5's cost check: "No cut ... is needed"). The second family changed from Nova Pro to gpt-oss-120b because Bedrock was blocked, a substitution under protocol 5.1 and Phase 3.5 §23, not a cut; the page says which, so a reader does not take it for one. Five cases ran, all exploratory (line 20) | `planning/05` §5.1; `evidence/phase-5.5/cost.md`; Phase 3.5 IMPLEMENTATION doc §23 | stated |
| 39 | Cost, measured: at most about $46 through Phase 5.5, an overstatement since it counts the shared AWS account's whole use, under the $60 re-plan point and the $80 ceiling; Phase 1.5 about $0.01, Phase 6 no model call. The final record, with the idle monthly bill, is Phase 7's (its DoD 4) | `evidence/phase-5.5/cost.md` (2026-11-03); Phase 1.5 IMPLEMENTATION doc §26; Phase 6 IMPLEMENTATION doc §34.3 | stated; this phase's own spend added at its close |
| 40 | The rule that fills the section for results against the thesis, with its dated sources (already on `/`); the methods page links it | Phase 6 IMPLEMENTATION doc §19, decision 1 | stated |

## 2. Decisions this raises (listed, none taken)

Each gets options and a recommendation when the doc's later sections are written; none is decided here, and none is
for tonight.

- **A. Where the raw text is published** (§0 item 1): the repository, a GitHub release asset, or a path on the site.
  What the re-scoring job reads follows from it, and so does the size of every future clone.
- **B. A true 404 status at go-live** (§0 item 5): add it (and so re-run the teardown test), or keep today's
  status-200 not-found view and say so.
- **C. The video** (§0 item 6, §4): how, not whether. Options as they stand after §4, none taken:
  - (a) **Claude's lean:** an **Explainer** for the site, **served from the site** (`media-src 'self'` added to
    `bootstrap`, with decision B in the same apply); narration from the tool, with ElevenLabs only if the tool's
    narration fails the line-by-line check (replacing narration means re-cutting the video to it, real work). And a
    **Short** made from the same sources for Phase 7's post, where a vertical clip is the form a casual reader meets.
  - (b) The Explainer uploaded to a video host and **linked, not embedded**: no infrastructure change; the host tracks
    a viewer only after a deliberate click; a host's page is also easier to share. The scope rule (no tracking) allows
    a link, not an embedded player.
  - (c) Both: served from the site, and the same file also on a host for sharing.
  Each option keeps the label (every tool named), the frame-by-frame check, and the rule that nothing in the video is
  the only place a fact appears.
- **D. How much the methods page says about the memo echoes** (ledger 37): his call, since it is a judgment about a
  public file that cannot be taken back.
- **E. Where the methods page lives, and where its numbers come from** (§3). Recommended, to be argued when the
  options are written: a route in the explorer's build (`/methods/`), so it inherits the security policy, fonts and
  number trace; numbers that sit in a results file are read from it by the build, and figures from evidence files are
  quoted with their source linked.

Ledger lines marked *check* are not decisions; they are reads to make before the page is drafted.

## 3. The methods page, section by section (outline)

**What this is.** The page's order, `planning/06` §6.1's with the scope doc's additions (Delivers 1, 5, 7 and 10), and
for each section what it holds, which ledger lines (§1) it carries, where its facts come from, and who writes it.
**Every ledger line lands in exactly one section** (two, for line 17, split as marked); that is checked when the page
is drafted, line by line, and is a row of this phase's definition of done.

**Who writes what** (`planning/06` §8, Phase 6 decision 3). **His:** the page's title, every section title, and any
sentence that speaks for the project. **Claude drafts, he approves:** the technical descriptions, each flagged as
Claude-drafted when handed over. **Already his and in place:** the scope sentence (`web/src/explorer/his.json`,
`scopeSentence`). **Every result sentence** fits `planning/06` §4's allowed column, with its run count.

**Where the page lives, and where its numbers come from:** decision E (§2). Recommended there: a route in the
explorer's own build, so the page inherits its content security policy, fonts, `noindex` handling and number trace.

| § | Section (working name; the title is his) | What it holds | Ledger | Sources |
|---|---|---|---|---|
| M0 | Opening | The scope sentence, first; that the claim is always about the model under an objective, never about executives; stated reasons are not verified; re-asking a model gives a new sample, not the same numbers; a link to the video (M11) | 1, 2, 3 | `his.json`; `planning/04` §1.3; `planning/06` §2.1 |
| M1 | The objectives | The five objectives in full, word for word from the hashed content; the shared frame and what it trades away; the three wordings and their order, shuffled per run from the seed; who drafted the instrument and how it was reviewed | 4, 5, 7 | `experiment/` content files at `prereg-v1`; Phase 2 decision 2; Phase 2.5 decision 3 |
| M2 | The company and the four scenarios | The fictional company and its sources; each scenario and its lever menu, with each lever's meaning in that scenario; its known simplifications | 6 | the dossier and scenario files at `prereg-v1`; KNOWN-GAPS RECORDED 2026-10-06 |
| M3 | Models, dates and run counts | The fallback set and why (Bedrock blocked); what it gives up in reach; each model's default settings, from the provenance; run dates; attempted, valid and failed runs per scenario, from the results files; the two expired images | 8, 9, 10, 17 (counts) | the three results files; Phase 3.5 §23 and §23.6; KNOWN-GAPS (images) |
| M4 | The pre-registration, and what changed after it | The tag `prereg-v1`, its outside timestamp and archive, the release; `errata-v1.md`, and that no `prereg-v2` exists; every rule set after the tag and before the case search, each with its date and reason; how the case runs used the tag's code | 11, 18, 22, 23, 31 | the tag day record (Phase 3.5 §26); `errata-v1.md`; search-half doc §4.6-§4.6.3 |
| M5 | What the statistics can and cannot show | Precision (Newcombe ±25 and ±16; shares about ±8.3); power, measured (62.9%, 81.9%); "no split" reachability, with its worst point; the measured false-split worst case; the failure bound's form; what failures cost, with gpt-oss `s2`'s not-assessable comparison and Haiku `s2`'s 6-a-cell rule; the matcher: "no good match" expected rare, then 20 of 20; the rule that fills the results-against-the-thesis section | 12, 13, 14, 14a, 15, 16, 17 (consequence), 40 | `evidence/phase-3/simulation-summary.md` and `plain-english.md`; protocol §7.4; Phase 6 IMPLEMENTATION doc §19 |
| M6 | The real cases | In this order: the pre-registered result (no case; the shortfalls); the five exploratory cases, all closures, each with its label; leakage (three first disclosed before Haiku's cut-off, the knowledge probe in the window's place); how cases were found, the disclosure asymmetry and what filings cannot show; the reader, its brief and its limits; the recognition probe; the selection logs, linked; why no case can be re-run, and the planning promise this breaks; the held memos and why; the search check's limits; both matcher behaviors; the memo echoes, as far as his decision D says | 19, 20, 20a, 20b, 21, 24-30, 32-37 | search-half doc §4.6.5; `cases.json`; `selection-public.json`, `exploratory-public.json`; Phase 5.5 run log; KNOWN-GAPS OPEN 2026-10-31 and CLOSED 2026-11-09 |
| M7 | Checking it yourself | Where the raw responses are (decision A) and how to tie each to the manifest by sha256; the re-scoring check in CI, what it reads and its last passing run; the prompt-reconstruction check, its samples and result; what can and cannot be re-run | (scope Delivers 2, 3; DoD 2, 3, 8) | `raw-manifest.json`; the CI job; the reconstruction record |
| M8 | Cost, and the cut list | Measured spend to date, and that it overstates; the cut list not applied, and the second family's change named as a substitution | 38, 39 | `evidence/phase-5.5/cost.md`; Phase 1.5 §26; Phase 6 §34.3 |
| M9 | Known limits, together | One list, each item a sentence and a link up to where the page explains it; nothing here that is not stated above | (gathers) | the sections above |
| M10 | The words this project uses | The vocabulary recheck, dated; the terms avoided and why, in brief | (scope Delivers 7) | `planning/06` §2-§3 and §11, re-read live |
| M11 | The video | The AI-generated label, with every tool named; that every fact in it is also on this page or the explorer; the transcript | (scope Delivers 5) | decision C |
| M12 | Changes to this site | The dated changelog from go-live, each entry saying whether it is presentation or a published number, and for a number, by which protocol rule | (scope Delivers 10) | the go-live record onward |

**What the outline leaves open:** each section's length, and how much of M6 sits on the page against linked records.
Both are settled on the draft, read as the four readers (`planning/06` §5); the hostile reader decides M5 and M6, the
LinkedIn reader decides M0.

## 4. Facts checked live, 2026-11-14 (the video first)

The video's tools were tested in his ten-session tool sprint (Gemini Notebook 2026-09-23; ElevenLabs 2026-09-25); those
notes are private and are cited here by date only. What follows is that record, rechecked live this morning, with each
fact's source and its confidence.

| Item | Today | Source and confidence |
|---|---|---|
| The tool's name | **Gemini Notebook**, renamed from NotebookLM in July 2026; the help pages still sit under `support.google.com/notebooklm` | sprint record; Google's help page (live) |
| Video formats | **Cinematic** ("rich, immersive"; English only; 18+), **Explainer** ("structured, comprehensive"; no length stated), **Short** ("~60 second videos", vertical) | Google's help page, read live; no update date shown |
| Steering | an optional **steering prompt** (a topic); **producer notes** reviewed and refined before rendering; a visual style, including a custom one (not for Cinematic or Short) | Google's help page, live |
| Download | yes ("select Download") | Google's help page, live |
| Accuracy | the page itself: "may contain inaccuracies or audio glitches" | Google's help page, live |
| Free limits | **not stated by Google.** Third-party figures disagree (3 a day; a quota every five hours under a weekly cap). In the sprint, one Short moved the free account's usage bar about 20% by his eye, with no number shown | secondary sources, low confidence; sprint record |
| Generation time | about 7 minutes for a Short in the sprint; Google: "sometimes, more than 30 minutes" | sprint record; help page |
| Marking | a visible Gemini Notebook mark sat in the frame corners of the sprint's Short; Google's page says nothing about watermarks | sprint record (one video) |
| ElevenLabs | Text to Speech "1 credit per character" (confirmed 1:1 only for the Multilingual v2 models). Free: 10k credits a month, no commercial licence listed; Starter $6 a month (first month $1), 30k credits, "Commercial License" | elevenlabs.io/pricing, live |
| His ElevenLabs account | an existing balance, read in the sprint, would cover a script of about 2,500 characters (about three minutes); its plan and its licence terms are his to read before he chooses it | sprint record; **today's balance not read** (his account) |

**What the sprint's video showed, which this phase plans around** (one Short, on a different corpus): made-up text on
screen (a "legal notice" of word-shaped nonsense); editorial framing the sources did not state; and, in the chat beside
it, outside material mixed in unmarked. The notebook also **added its own chats to its sources by default**, and they
then shaped its summary. So the scope doc's frame-by-frame and line-by-line check is the gate, not a formality: every
frame's on-screen text read, every narrated sentence held to `planning/06` §4 and to the data; the source list checked
to hold only the methods page and published results before generating, its chats unticked.

**A finding about hosting (measured in the repository):** the site's content security policy is set in CloudFront, at
`infra/terraform/bootstrap/site.tf` line 22: `default-src 'none'`, with no `media-src`. **A video served from the site
is blocked until `media-src 'self'` is added**, which is a change to `bootstrap`, applied by him, so the teardown test
re-runs (Delivers 8). A link to a video hosted elsewhere needs no change: a link is navigation, which the policy does not
govern. This ties decision C to decision B: if both change `bootstrap`, they go in one apply and one teardown test.

**Not yet checked live:** Gemini Notebook's terms for publishing what it generates; the site's own size limits for a
video file (the build check, `web/scripts/check-dist.mjs`, has a JavaScript and a font budget and nothing for media);
package and action versions (rechecked at each install, the 14-day rule, as in Phase 6).
