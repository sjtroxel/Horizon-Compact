# Phase 6.5 — Methods and Release: IMPLEMENTATION (v0.6.5)

> **IMPLEMENTATION doc. APPROVED 2026-11-14, about 8:55 AM (his): decisions A-G all as leaned** (A-E about 8:30 AM,
> §2; F and G about 8:55 AM, §6 and §5.6). Drafted 2026-11-14 from about 2:20 AM (Opus), the day after Phase 6 closed
> (`21262a6`), and finished the same morning. The scope doc is amended at this approval (its header note of
> 2026-11-14). Sections: §0 the scope review; §1 the disclosure ledger; §2 decisions A-E; §3 the methods page's
> outline; §4 facts checked live; §5 the checks; §6 the video; §7 go-live; §8 steps and commits; §9 DoD; §10 cost.
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
   official objects: 5,247 objects, 104,785,272 bytes by the manifest's own sum (measured 2026-11-14); 92 MB of it is
   first attempts (2,450 objects of about 37 KB each), since every attempt carries its whole prompt and reply. Where
   they are published (the repository, a GitHub release asset, or a path on the site) decides what the CI re-scoring
   job reads. Decision A (§2).
   **How much space they take, estimated, not measured** (*corrected the same morning: the first draft said committing
   them would "roughly triple" the 50 MB `.git`, which set raw bytes against packed ones*). On the nearest stand-in,
   355 development attempt records in `scratch/runs/` (9.7 MB, written by the same code, on the placeholder
   experiment), git's own pack came to 10% of the raw bytes, gzip 17% and xz 5%. If the official records compress
   alike, that is about 10 MB in git, 18 MB as a `.tar.gz`, 5 MB as `.tar.xz`. The real figure is measured on his pull
   before decision A is taken.
   **What a record holds** (read on the stand-in): the whole request (the prompt, the tool, the provider settings),
   the whole raw reply (the reasoning text included where a model returns it), usage and cost, and provenance (git
   sha, image digest, an ECS task ARN). **Private values are kept out at write time:** every sweep record is written
   through `serialize_safely` (`smoke/record.py`; `sweep/runner.py` calls it), which replaces the AWS account number
   with `<account-id>`, redacts e-mail addresses and refuses any record holding an API key. On the stand-in: 169 of
   355 hold the placeholder, no twelve-digit number stands alone, no key shape appears. Claude has not seen an
   official record (the deny list, Phase 4 runs doc §5.4), so the same checks run again over the real pull before
   anything is published.
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
   unless go-live adds infrastructure, and it has to (decision B). **Measured in `infra/terraform/main/site.tf`:** the
   distribution answers every missing key with `/index.html` and status 200 (a private bucket answers 403, and both
   403 and 404 map to the page). A path such as `/scenario/s1/` is not a key (the file is `scenario/s1/index.html`),
   so it gets the root page. **A person is not hurt by that** (the app routes in the browser); **a link-preview
   crawler is**, since it runs no script: every shared link would show the root page's title and card, which undoes
   Phase 6's per-view cards (its decision 6, and its §3 finding 6, which named this as go-live's to fix). And an
   unknown path returns 200, not 404.
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

## 2. Decisions this raises (all DECIDED 2026-11-14 (his), each as leaned)

Each had its options and Claude's lean; **he took all five as leaned on the morning of 2026-11-14, rested** ("all as
leaned"), and F and G (§6, §5.6) the same way at his approval of the doc. The options are kept as the record.

- **A. Where the raw text is published** (§0 item 1). **DECIDED 2026-11-14, about 8:30 AM (his): (a), as leaned.** GitHub, read live 2026-11-14: a file over 100 MiB is blocked,
  repositories "ideally less than 1 GB", release assets have no total limit.
  - (a) **Claude's lean: in the repository**, under `experiment/`, at the manifest's keys. The re-scoring job reads
    them with no network and no credential; the name guard reads every byte on the way in; GitHub shows any one of
    them to a reader with no download. About 10 MB packed, estimated (§0 item 1); a checkout carries the full 105 MB.
    Permanent once pushed, which suits write-once records on a fictional company.
  - (b) **A release asset**: one archive (about 18 MB gzipped, estimated) on a GitHub release, its sha256 committed.
    The repository stays light; the job downloads it (one more moving part); a reader must download to read one.
  - (c) **A path on the site**, served from the distribution: browsable, but CI would read the site, and Deploy
    would sync 105 MB it does not sync today.
- **B. Serving at go-live** (§0 item 5). **DECIDED 2026-11-14, about 8:30 AM (his): (a), as leaned.** Not whether, since the share cards need it; how:
  - (a) **Claude's lean: a CloudFront Function** in `main` (on each viewer request, a path ending in `/` gets
    `index.html`), with the error responses changed to serve a not-found page with status 404. One place; it works
    from the Vercel URL and the distribution's own; `main` changes, so the teardown test re-runs (Delivers 8).
  - (b) **Rules in the Vercel rewrite** (`infra/vercel/vercel.json`, his deploy) that send `/(.*)/` to
    `/$1/index.html`. Smaller, but the distribution's own URL keeps the root-page behavior, and a real 404 still needs
    a change in `main`.
  - Either way the changes to `main` (B) and to `bootstrap` (C's `media-src`, if chosen) go in one apply each, and
    one teardown test covers both.
- **C. The video** (§0 item 6, §4): how, not whether. **DECIDED 2026-11-14, about 8:30 AM (his): (a), as leaned.**
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
- **D. How much the methods page says about the memo echoes** (ledger 37). **DECIDED 2026-11-14, about 8:30 AM (his): (a), as leaned.** Never the terms themselves, under any
  option.
  - (a) **Claude's lean: a plain paragraph**: what was counted (845 of 1,237 published memos hold a distinctive token,
    an upper bound), that the explorer holds real-case memo text for that reason, that the repository copies stay as
    published, and that his read found nothing pointing to a company (his judgment, stated as his), with a link to
    `memo-echoes.json`, which is already public. A hostile reader finds the file anyway; the page saying it first is
    the stronger position.
  - (b) Only that real-case memo text is held from the site, and why, with no count.
  - (c) (a) with the per-case counts in a table.
- **E. Where the methods page lives, and where its numbers come from** (§3). **DECIDED 2026-11-14, about 8:30 AM (his): (a), as leaned.**
  - (a) **Claude's lean: a route in the explorer's build** (`/methods/`), so it inherits the security policy, fonts,
    `noindex` handling, share card and number trace. A number that sits in a results file is read from it by the
    build; a figure from an evidence file is quoted with its source linked.
  - (b) A separate static page in `web/`, outside the explorer: simpler to write, but its numbers are typed by hand
    and nothing traces them.
  - (c) A Markdown file in the repository, linked from the site: readable on GitHub, but outside the site's checks,
    and the scope doc puts the page on the site.

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

**As built, step 4 (2026-11-17, Sonnet; Opus review pending).** The frame of the page, with no sentence of its prose.
- **The data.** `hc site explorer` now also writes `methods.json` (`src/horizon_compact/site/explorer.py`, `_read_methods`;
  a hidden `--raw` option points it at other raw text, the way `--results` does). It reads, for the three official sweeps
  that have a results file and no other, each `manifest.json`, every `sessions/*.json` and every `runs/*/attempt-*.json`,
  and once `raw-manifest.json`; fields are picked by name. The seventeen request-side fields are copied and **refused
  unless identical on every attempt of a sweep** (the message names the field, the sweep and two attempt ids); on the
  real data none disagreed (1,128, 1,333 and 100 attempts). Two counts of copied values are the only things it derives,
  both stated in the module docstring: `runs_in_manifest` (the length of the manifest's `runs`) and `served` (attempts
  per distinct `served_by` and `served_model`; gpt-oss: DeepInfra 1,322, unknown 11; Haiku: one model, 1,128 and 100).
  Nothing from a record's text, request, tool calls, task, image or ids is copied. `index.json` lists the file and gains
  eight sources (the raw manifest, three sweep manifests, four session records: 27 to 35); the attempt files are covered
  by the raw manifest. Every other file in `web/explorer-data/` is byte for byte unchanged (`git diff --stat`: `index.json`
  only, `methods.json` added). **Version decision:** `EXPLORER_DATA_VERSION` stays 1: a new file and a new key of `files`
  are additions, no existing field changed shape, and nothing reads the number (every loader takes its path from `files`).
- **The route.** Kind `methods` everywhere a kind is listed (`pathOf`, `routeOfPath`, `cardSlug`, `allRoutes` after
  `memos`, `parseRoute`, `Pages`, `VIEW_MODULES` as its own chunk, `views.tsx`, `check-dist`'s `kindOfPath`); a `Methods`
  nav entry after Memos; no model switch; the story's last beat gains the link to `/methods/` first. His page title and
  description are placeholders in `his.json` (`pages.methods`); the card is drawn from them like the studies card.
- **The page.** `web/src/explorer/Methods.tsx`; its outline is `methods.json` (thirteen sections, anchor, ledger ids, `also`
  for the sections with no ledger id). Each section is a `<section id=anchor>` with an `<h2>` and the body placeholder; a
  contents list sits on the title band. The sections draw after the data loads (as the studies page does, so nothing
  shifts), and an address that names one is revealed then. M3's data part: per model (the main one first) the settings, who
  served the attempts, the first start and last finish in UTC and the session count, and the runs of each scenario
  (attempted, valid, refused, failures by type, summed from the grid files' `cells`); the thinking sweep in its own part
  labelled as the side study; nothing added across models. M7's data part: the object count, the total bytes and two links.
- **The tests.** `web/src/explorer/methods.test.ts` (the outline is M0 to M12 with safe, unique anchors; the ledger ids
  are exactly 1 to 40 plus 14a, 20a, 20b and are held equal to **this doc's §1 table**, and each section's ledger to **§3's
  Ledger column**; 17 sits in M3 and M5 only; the placeholder census pins 2 + 13 + 13 places and that his.json holds the
  one exported constant), `Methods.test.tsx` (the rendered page, both data parts against the data, no digit outside the
  two data parts), and tests added to `cards`, `route`, `Shell`, `Story`, `data`, `format`, `links` and `write-paths`;
  `tests/test_site_explorer.py` gained the builder's fakes and tests. Step 5 extends the placement test to "every ledger
  id has a block that carries it"; go-live must make `check-dist` refuse any placeholder (not added now: it would fail
  `make check`).
- **New labels for the words pass** (`explorerLabels` unless named): `navMethods` "Methods"; `storyMethodsLink` "How the
  study was done, in full"; `methodsContentsLabel`; `methodsLoading`; `methodsSettingsCaption`; `methodsSettingLabels` (the
  seventeen fields' names); `methodsSettingColumn`, `methodsValueColumn`, `methodsNone`, `methodsYes`, `methodsNo`;
  `methodsServedCaption`, `methodsServedLabels` (two), `methodsServedColumn`, `methodsAttemptsColumn`;
  `methodsDatesCaption`, `methodsFirstStarted`, `methodsLastFinished`, `methodsSessionCount`; `methodsCountsCaption`,
  `methodsScenarioColumn`, `methodsAttemptedColumn`, `methodsValidColumn`, `methodsRefusedColumn`, `methodsFailedColumn`,
  `methodsNoFailures`; `methodsSideStudy`; `methodsRawCaption`, `methodsRawObjects`, `methodsRawBytes`,
  `methodsRawFolderLink`, `methodsRawManifestLink`; and `explorerCardLabels.cardAlt.methods`. The two placeholders are the
  constant `METHODS_PLACEHOLDER` (`[his title]`, `[to be written]`).
- **Proof.** `make check` exit 0: Python 3,580 (3,545 before: +35), web 621 (585 before: +36). Mutations, each one change,
  the test failing, the file restored (hash checked): (1) the same-value comparison made always true: `DID NOT RAISE
  ExplorerDataRefusal` in the disagreement tests (all 17 fields and the type-only case); (2) `tool_calls` added to the
  settings field names: `AssertionError: ('methods.json', 'FIXTURE RAW MEMO TEXT THAT MUST NEVER REACH THE METHODS DATA')`.
  Browser pass (`scratch/p65-s4-shoot.mjs`, 14 paths): 56 loads, 0 with a problem, max layout shift 0.001, crop test 0
  missing, **number trace 0 untraced on `/methods/`** (115 numbers). The trace still allows any number found in
  `his.json`'s text; the placeholders hold no digit, so that is safe now, but step 5 needs a stricter rule for
  `methods.json`, where a quoted evidence figure must trace to its source (not built now). Dist: added `methods/index.html`,
  `cards/methods.png`, `data/methods.json`, the `Methods` chunk and a new shared `format-*.js` chunk; the other assets only
  change their content hashes. The methods path loads 86.9 KB of JavaScript gzipped, the story's 94.7 KB (budget 100 KB).
- **What did not fit, and what was done instead.** (1) The build prompt gave M7 to M12 no ledger ids; the doc's §3 gives M8
  ledger 38 and 39, so the doc was followed (the test holds methods.json to the doc). (2) No `methods.pageTitle` in
  `his.json`: the page's title is `pages.methods.title`, which the heading, the head tags and the card already read, and a
  second copy would be two places for one of his words. (3) The sections carry no `aria-labelledby`: while all thirteen
  titles are one placeholder, a labelled section is thirteen identical landmarks (axe `landmark-unique`); revisit when the
  titles are written. (4) The placement test is two files, `methods.test.ts` and `Methods.test.tsx`, since rendering needs
  JSX. (5) Two phone-width fixes the browser pass found: the run counts' last column overflowed 390 px, so those tables
  take less side padding and a failure type breaks after its underscores. (6) The card is an image, so it shows the
  placeholder text until his words replace it; the census test, not a pixel check, guards that.

**Reviewed, step 4 (2026-11-17, Opus): passed after one test addition.** Read the whole diff; re-ran `make check` (exit 0,
3,580 and 621); looked at the `/methods/` captures at 390 and 1280, light and dark, and the card. The builder picks by name,
refuses on any disagreement, and its arn and bucket refusal covers `methods.json`; the page orders the models by the labels
(Haiku 5.5 first) whatever the file's order; the placement test reads the doc's own §1 and §3 tables, so the outline cannot
drift from them. All six deviations stand: (1) was the build prompt's error, and the test it was told to write would have
failed without 38 and 39. **The addition:** the prompt asked that a case path under the fake raw root be shown never
opened, and the fake had none; it now holds a case's sweep (`official/case-alpha/...`) beside the stray, the pilot and the
awareness run. Mutation-checked: a builder that also reads every `official/*/*/manifest.json` fails
`test_the_builder_opens_only_the_three_sweeps_records_and_the_raw_manifest` at `assert allowed.fullmatch(...)`; restored,
hash checked. **For the words pass, besides the labels listed above:** (a) the served tables' "Attempts" (API calls, retries
included: Haiku 1,128) and the run tables' "Attempted" (runs: Haiku 990) are two units under one word, and read as a
contradiction; (b) the settings table shows all seventeen fields, several of which repeat for a reader (Provider and Route;
Model and Model name sent) or are internal (Runner, Kind of run); whether the page shows a shorter table with the rest in a
closed details section is his call; (c) the side study's tables are captioned "Haiku 5.5: ..." exactly as the main Haiku's
are; (d) `explorerCardLabels.cardAlt.methods` describes a page that is not written yet; (e) cosmetic, for step 5: the
two-column key and value tables (settings, dates, raw text) do not share a value column, and the contents list's two columns
sit far apart while every title is the same placeholder.

**Words pass and step 5, as drafted (2026-11-18, Opus). APPROVED 2026-11-18, about 10:06 AM (his), on his read of the preview ("it all looks legit"); committed as C5 `fc8e65e` (his), CI `44344066964` and Deploy `44344066870` green.** His instruction, about 9:23 AM: take Claude's
recommendation on every step 4 label and every review note, and have Claude draft the page's prose, the titles and the
project sentences included, for his approval ("I'm going to direct you to write the prose for me to approve"). So this
pass departs from the "his" column above at his request: every title and sentence is Claude-drafted, his to approve or
change.
- **The five notes, as recommended.** (a) The served tables' column is "API calls, retries included" and the run tables'
  "Runs attempted"; M3's last paragraph says a run is one decision and an API call one request. (b) Each sweep's settings
  show eight fields (`methodsSettingsMain`: model ID, output limit, temperature, effort, thinking, where it ran, image,
  code version); the other nine sit in a closed "The other recorded settings" part under them; none is dropped, and a test
  holds both tables to the record in its order. (c) The side study's tables are captioned "Haiku 5.5, thinking sub-study:
  ...". (d) `cardAlt.methods` describes the written page. (e) The key-and-value tables share a 15rem key column (45% at
  phone width); the contents list keeps its two columns, which read evenly now that the titles differ. Labels also
  changed: "Model ID", "Where the program ran", "Kind of sweep", the settings caption "the same on every API call".
- **The words.** `methods.json` gives each section its blocks: a paragraph, a quote, a list, three blocks drawn from data
  or his.json (his scope sentence first; the goals table from `index.json`; the scenarios from his approved briefs) and
  `pending` parts. Each block names the ledger ids it states and its source files (linked at the section's end). **Every
  figure in the prose is traced** (`methods.test.ts`): a quoted figure names a file and the words there that hold it, and
  the test finds them (markdown marks dropped, white space collapsed) and requires every digit run of the figure in them;
  a counted figure (the failure counts in M5) is recomputed from the explorer's grid files; any other digit fails, except
  model names, the tag, `sha256`, the case labels and section signs. Quotes (the three wordings, the reader's objection,
  the recognition question) are checked word for word. Mutation-checked: 62.9% changed to 63.9% fails the trace; the
  count 27 changed to 28 fails it (`expected '27' to be '28'`); $46 changed to $47 with no figure fails the digit rule.
- **Placement:** every ledger id has a block that states it, and no block claims an id its section lacks (the DoD's row 1,
  by script). Ledger 7 is written as the protocol has it (the lines' and options' order is shuffled per run; the ledger's
  "wording order" was loose). Ledger 5 says plainly that his review was mostly acceptance of Claude's recommendations
  (protocol §3), not an independent line-by-line check. The sections carry `aria-labelledby` again, since the thirteen
  titles now differ.
- **Still pending, by step:** M0's link to the video and M11 (step 9), M7's prompt-reconstruction check (step 7), M10's
  dated vocabulary recheck (step 10). The census test pins exactly these four. `check-dist`'s refusal of a placeholder is
  still for go-live.
- **Proof.** `make check` green: Python 3,580, web 631. Browser pass (`scratch/p65-s5-shoot.mjs`, a copy of step 4's whose
  trace also allows methods.json's figures, quotes and source paths): 56 loads, 0 with a problem, max layout shift 0.001;
  `/methods/` 18,542 px at 1280 and 25,881 at 390; trace 1 untraced on `/methods/`, "1,237", a script quirk (it strips
  commas before matching), traced by the unit test. A plain-text copy for his read: `scratch/p65-s5-methods-prose.md`.
  **The name guard, run on the working files before any commit, found one term** in the first draft (a cloud vendor's
  name, in M3 and M8); both places reworded to name only the service and the model, as the rest of the repo does, and a
  re-scan of every changed file found none.

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

## 5. The checks, as they will be built

### 5.1 The raw text, published (decision A; DoD row 8)

- **Where:** `experiment/raw/`, each object at its manifest key (`official/...`, `pilot/...`), 5,247 files.
- **The pull is his** (Claude's deny list keeps it out of S3): a new read-only command, `hc raw pull`, fetches each
  object **at the manifest's `version_id`**, so a later write to the same key (none is expected; the bucket is
  write-once by design) cannot change what is published. Claude writes the command; he runs it once.
- **The verify is anyone's:** `hc raw verify` reads only `experiment/raw/` and the committed manifest, and fails on any
  object missing, extra, or differing in bytes or sha256, and on any file that fails the write-time checks again (the
  account placeholder only, no standalone twelve-digit number, no e-mail address, no key shape:
  `smoke/record.py`'s `assert_clean`, reused). It runs inside `pytest`, so in `make check` and CI.
- **Measured before the commit, not estimated:** the packed size (§0 item 1), and how long the name guard takes over
  5,247 new files. `check-added-large-files` (`--maxkb=1024`) needs no exception: the largest object is 230,749 bytes.
- **Rule zero:** these are the fictional company's records only (the `official/company/` and `pilot/company/`
  prefixes); no case record is in the manifest, and `hc raw verify` refuses any key outside those two prefixes.

**As built, step 1 (2026-11-14, Opus; he chose to stay on Opus rather than switch to Sonnet for the build, so this
step had no separate reviewer).** `src/horizon_compact/site/rawtext.py`; the commands are **`hc site raw-pull`** and
**`hc site raw-verify`**, beside `hc site raw-manifest`, not the `hc raw ...` this section first named.
- The pull reads through `rawmanifest.S3RawReader` (no write call) at each entry's `version_id`; checks bytes,
  sha256 and the write-time text checks **before** writing; writes once (the same bytes again a no-op, different
  bytes refused). The account id comes from the bucket name, as the manifest builder takes it.
- The verify reads only `experiment/raw/` and the manifest: the same key set (a leftover `.tmp` counts as extra),
  each file's bytes and sha256, and the text checks without the account id.
- The text checks are `smoke/record.py`'s three patterns, copied (that file is the sweep's writer and stays
  untouched), with a test holding the copies equal to the originals.
- **Two findings, fixed in this step:** `end-of-file-fixer` and `trailing-whitespace` rewrite files on commit, which
  would change a record's bytes away from its sha256; both now exclude `^experiment/raw/`. And `experiment/.gitattributes`
  (`raw/** -text`) keeps git from converting line endings on any clone. Neither touches the root (14 of 16).
- `hc site raw-pull` is denied to Claude in `.claude/settings.json`, both forms, with its test.
- Tests: `tests/test_site_rawtext.py`, 50 cases, fictional canaries only; the committed manifest loads and every one
  of its 5,247 keys is the fictional company's. **Seven mutations** (reading the newest version instead of the pinned
  one; skipping the text checks or the sha check in the pull; letting verify pass extra files; dropping the prefix
  check; allowing an overwrite; skipping verify's text checks) **were each caught**, the file restored byte for byte.
- `make check` exit 0: Python 3,533 passed, web 585.

**As run, step 2 (2026-11-15).** His pull, `hc site raw-pull` with the project profile and the bucket from
`bootstrap`'s output: `written: 5247`, `unchanged: 0`, `bytes: 104785272`, the manifest's total. Then, measured, not
estimated:
- `hc site raw-verify`: `ok: 5247 objects, 104785272 bytes`, in about 12 seconds.
- **Packed size: 10.30 MiB** (a throwaway repository holding only `experiment/raw/` and its `.gitattributes`, after
  `git repack -ad`); 125 MB on disk. §0 item 1's estimate of about 10 MB held.
- **The name guard: about 3.5 minutes** over the 5,247 staged files (3 min 27 s and 3 min 30 s, staged into a
  throwaway index, never his). C2's commit waits on it that long, once, and its push about as long again (the push guard reads each new commit's full content); later commits touch none of these files.
- **Two false positives, found by the guard's first pass:** a short term from the private term file matched inside
  the base64 `signature` of a thinking block in two Haiku 5.5 records, between `/` and `+`, which the guard counts
  as word boundaries. The records cannot be reworded (their sha256 is in the manifest), so he added two `allow:`
  lines to the private term file, each a short span around one match, occurring exactly once in
  `experiment/raw/`. The second pass: exit 0. No text of either match is written in this repository.
- **One gap in step 1, closed here:** §5.1 says the verify runs inside `pytest`, but every `verify_raw` test ran on
  fakes. `test_the_committed_raw_text_matches_the_committed_manifest` now verifies the real `experiment/raw/` against
  the committed manifest, with no skip when the files are absent; it failed on one byte changed and on one file
  missing, each restored (sha256 checked). `tests/test_site_rawtext.py`: 51 cases.

### 5.2 The re-scoring check (Delivers 2; DoD row 2)

- **What it is:** a test that runs the frozen analysis (`hc analyze`'s own code, `--store local`, rooted at
  `experiment/raw/`) for each of the three official sweeps and compares the output with the committed results files
  **byte for byte**. Feasible as stated: the results files carry no timestamp or host value (read 2026-11-14), and
  `hc analyze` already takes a local store.
- **Published files only:** the test fails if anything opens an S3 client while it runs (`planning/02` §2.11).
- **In `pytest`,** as Phase 6's explorer-data reproduction test is, so it runs in `make check` and on every CI run. The
  chain a reader can then check end to end: raw records, to results files (this test), to the explorer's data
  (Phase 6's test), to every number on the page (the number trace).
- **Shown to fail once** (DoD 2): one number in a copy of a results file changed by hand, the test run, its failure
  recorded in this doc, the copy discarded. As Phase 6's mutation checks were.
- **Its time** is measured on the first run; if it makes `make check` slow, it gets a marker of its own that CI still
  runs, never a skip.

**As built, step 3 (2026-11-16, Sonnet; reviewed by Opus the same day, below).**
- **The option.** `hc analyze` takes `--runs-root` (`cli.py`). With `--store local` the store is a `LocalStore` on
  that folder in place of `scratch/runs`; with `--store s3` it is refused (a `SweepRefusal` naming both options,
  exit 2, before any session is opened, nothing written). Its help line is visible: "with --store local: the
  folder holding the records (default scratch/runs); experiment/raw is the published text". Nothing else in
  `cmd_analyze` changed except that the store choice is now an if/else, whose default branch calls `_store` as it
  did. A reader's own `uv run hc analyze --experiment company --sweep <id> --store local --runs-root
  experiment/raw` on a clone is itself the check: `write_results` is a no-op on the same text and refuses a
  different one.
- **The test file.** `tests/test_analysis_rescoring.py`, five tests, no skip, no marker. One per sweep
  (parametrized over `grid-haiku-5-5-0b99fabb`, `grid-gpt-oss-openrouter-fe599ad2`, `thinking-haiku-5-5-418caa9c`)
  calls `cli.main(["analyze", ..., "--store", "local", "--runs-root", <experiment/raw>, "--protocol", "prereg-v1",
  "--root", <tmp>])` with the real gate unpatched and the default official role, asserts exit 0, and compares the
  file written under the temporary root with the committed one by `read_bytes()`; nothing is written into the
  repository's own `experiment/`. One test holds that the `*.json` files under `experiment/results/prereg-v1/`
  are exactly these three. An autouse fixture makes `botocore.session.Session.create_client` (the chokepoint every
  `boto3` client and resource passes through), `boto3.client`, `boto3.resource` and `cli._session` raise one
  error class, `AwsClientOpened`; one test shows each of those doors raising it.
- **Three tests in `tests/test_sweep_refusals.py`** for the option: it reads the folder it is given (a played
  sweep under a `tmp_path` folder, with the default store made to fail if asked for; a folder with no such sweep
  is refused and writes nothing); it is refused with `--store s3` and opens no session; the default is unchanged
  (`_store` is still asked, and still means `scratch/runs`). **Eight tests added in the step.**
- **Proof.** `make check` exit 0: **3,542 Python** (3,533 at step 1, one added by step 2, eight by this step) and
  **585 web**. The new file takes **3.6 s** under `--durations` (grid-haiku 2.11 s, gpt-oss 1.32 s, thinking 0.16 s,
  the guard test 0.01 s), inside a pytest run of 202 s (the whole `make check` 3 min 49 s), so `make check` is not
  noticeably slower and the file needs no marker. The three sweeps came out identical to the committed files, as
  Opus's read-only check had found.
- **Mutations, each backed up to the scratchpad with its sha256 taken, run against the new file alone, and restored
  from the backup with the sha256 matching and `git status --short experiment/` empty.**
  1. *DoD 2.* One `estimate` of one pair-rate in `experiment/results/prereg-v1/haiku-5-5/grid-haiku-5-5-0b99fabb.json`,
     its last digit. The edit went into the tracked file, not a copy, because that is what the test reads; the backup
     is the copy it was restored from. Only the grid-haiku test failed; the other two sweeps and the rest passed.
     Failing line: `assert b'{\n  "resul...uns": []\n}\n' == b'{\n  "resul...uns": []\n}\n'` with `At index 290772
     diff: b'1' != b'2'`.
  2. *The test reads the raw text.* In `runs/r-0065d100cd6a/attempt-1.json` of the grid-haiku sweep, `validation.amounts`:
     one person moved from `kept_at_plant` to `moved_other_plants`, so the record still parses and still adds up.
     Only the grid-haiku test failed, **on the bytes, not on a parse error**: the same `assert b'...' == b'...'`
     with `At index 523036 diff: b'7' != b'0'`.
  3. *The AWS guard fires.* A throwaway edit of the test to `--store s3`, reverted: `AwsClientOpened: the re-scoring
     test opened an AWS client: it may read published files only`, raised from `cli._session`, not a credentials or
     network error.
- **`git diff --stat` of the step:** `cli.py`, `tests/test_sweep_refusals.py` and this doc modified, and
  `tests/test_analysis_rescoring.py` new; nothing under `experiment/`, `src/horizon_compact/analysis/`, `uv.lock` or
  `docs/phases/evidence/`.
- **The hooks' dry run** (`uv run pre-commit run --files` the four files above): every hook passed or had no file to
  check, the name guard included; `experiment/raw/` was not staged.
- **What did not fit, and what was done instead.** (a) Mutation 2's first attempt changed `parsed_decision.amounts`
  and **the test passed**: the frozen analysis reads each attempt's `validation` (`analysis/records.py`), not
  `parsed_decision`, so that edit was restored (sha256 checked) and redone on `validation.amounts`. The raw-verify
  test catches an edit to either field; the re-scoring test catches only what the analysis reads, which is the right
  scope for it. (b) Mutation 3 as written ("`--store s3` in place of `--store local`") would stop at the new
  `--runs-root` refusal before reaching a client, so the throwaway edit also dropped `--runs-root`, and the run reached
  `_session`. (c) The spec said the failure is shown on "a copy" of a results file; mutation 1 edited the tracked file
  (as the prompt directed) and restored it. (d) `make fmt` reported two docstring lines over the 110-column limit (W505) in the new file; they were rewrapped by hand.

**Reviewed, step 3 (2026-11-16, Opus). Passed, no change to Sonnet's code or tests; one test added on his
decision (below).**
- **Re-run, not taken on report:** the eight new tests pass; `make check` exit 0, 3,542 Python and 585 web, the counts
  above. The diff touches only `cli.py`, the two test files and this doc.
- **The option:** the refusal comes after the gate and before any session, so `--store s3 --runs-root` opens nothing;
  the default branch is the old two lines unchanged. `--runs-root` is read relative to the working directory, as
  `site data`'s is, so the reader's command in step 4 is given from the clone's top folder.
- **The guard** patches `botocore.session.Session.create_client` on the class, which every `boto3` client and
  resource reaches, so a door not named in the fixture is still closed.
- **What the test covers, stated exactly (Sonnet's finding (a), checked further).** The frozen analysis reads each
  attempt's recorded `validation`, the harness's verdict written at run time, not the model's tool call. So this test
  closes the link *recorded validation to results file*; the link *the model's tool call to the recorded validation*
  has no test. Checked read-only today (a throwaway script outside the repository): the frozen `validate_decision`, run
  again on every recorded tool call of the three sweeps (2,524 attempts carrying a validation), reproduces every recorded
  `validation` exactly, in about a second; and every recorded `tool_calls` input equals the call inside `raw_response`
  (the one apparent difference is a model's malformed `"{\n"` argument string, recorded as given and scored
  `schema_invalid`). **His decision (2026-11-16): add the re-validation as a test.**
- **Added in review (Opus, his decision):** `test_every_recorded_validation_is_the_frozen_validator_on_the_recorded_tool_call`
  in the same file, parametrized over the three sweeps: for every attempt that carries a `validation`, the locked
  `validate_decision` on the record's one tool call (on its scenario) must equal the recorded validation, and the count
  checked must be the sweep's (1,128, 1,296, 100), so a glob that finds nothing fails. Under the same AWS guard; about
  1.3 s for the three. **Mutation-checked:** in the grid-haiku record used for mutation 2, the tool call's
  `amounts` changed (one person from `kept_at_plant` to `moved_other_plants`, still valid and balanced): only the
  grid-haiku re-validation test failed (`Differing items: {'amounts': {... 'kept_at_plant': 161.0,
  'moved_other_plants': 29.0 ...}} != {... 162.0 ... 28.0 ...}`), and the byte test passed, which is the link the
  byte test could not see. Restored from a scratchpad backup, sha256 matching, `git status --short experiment/` empty. With it, `make check` exit 0: **3,545 Python** (three more) and **585 web**; the step added eleven.
  The chain a reader can check now starts at the model's tool call: tool call, to recorded validation (this test), to
  results file (the byte test). The link from the provider's `raw_response` to the recorded `tool_calls` matched on
  every record in the read-only check above but has no test; it is the harness's extraction, recorded side by side
  with its source in the same file.
- **Minor, not fixed:** `experiment/.gitattributes` keeps `raw/**` byte-exact but not `results/**`; on a Windows
  clone with `core.autocrlf` the byte comparison would fail while the reader's `hc analyze` (which compares text)
  would pass. CI and his laptop are unaffected. And on a reader's clone `hc analyze` prints "wrote ..." even when the
  file was already identical and nothing was written; step 4's page says what success looks like (exit 0, `git status`
  clean).

### 5.3 The prompt-reconstruction check (Delivers 3; DoD row 3)

- **The question it answers:** can a stranger rebuild a prompt **from the methods page and the published inputs**
  (`planning/05`'s Phase 6 row: "from the methods page alone"), without our code? If not, the methods page is missing
  something.
- **The samples, fixed by rule before the reader starts:** for each of the four scenarios, the first official run by
  run id in Haiku's grid, and one in gpt-oss's; one run from the thinking sub-study; one awareness call. Ten prompts.
  No real case (§0 item 2): the page says why.
- **What the reader gets:** the methods page and the explorer (the local preview), the experiment's content files at
  `prereg-v1` (objectives, wordings, dossier, scenarios), and, for each sample, its settings as the record states them
  (model, scenario, objective, wording, and the menu and option order with its seed). **Not** the code, and **not**
  the raw records, which hold the prompts. Decision G (below, decided as leaned) settled this list.
- **Who reads:** a fresh Claude Code session, started by him in an empty scratch directory holding only those files,
  with a brief Claude writes. Its isolation is the directory, not a guarantee; the record says so.
- **The comparison is mechanical:** a script compares each rebuilt prompt with the record's `request` and its
  `prompt_sha256`. A mismatch is a gap in the methods page, fixed there and re-checked with a new fresh session. The
  record (briefs, replies, diffs) goes to `docs/phases/evidence/phase-6.5/`.

**As prepared, step 7 (2026-11-18, Opus).** `scratch/p65-s7-reconstruct.py prepare ~/hc-reconstruct` built the
reader's folder **outside the repository** (a session started inside it would load the repo's `CLAUDE.md` and project
memory; his global `CLAUDE.md` still loads anywhere and names the repo's path, so the brief forbids leaving the folder,
and the isolation is the folder and the brief, not a guarantee). It holds the six content files at `prereg-v1`, each
checked against the hash all ten samples' records carry; `samples.json` (each sample's model, sweep, run id, scenario,
goal, wording, menu and option order and `menu_order_seed`, and no request field); `BRIEF.md`; an empty `rebuilt/`.
The samples, by the rule: the first run by run id of each scenario in Haiku 5.5's grid and in gpt-oss-120b's, the first
of the thinking sub-study, the first call of Haiku 5.5's awareness probe. `compare` hashes each rebuilt prompt as the
harness hashed what it sent (canonical JSON of system, user and, for a decision, the tool; the awareness call has no
tool) against the record's `prompt_sha256`, and diffs each part of a mismatch. Checked: every record's own parts
reproduce its hash (ten of ten), and a dry run with one blank line removed from one sample reads "9 of 10" with the diff
at that line.
- **A gap found before the reader, by inspection (his choice (b), about 4:31 PM):** the page did not say how a prompt is
  put together (the role sentence, the currency note, the user message's order, a line's format, the tool's schema), so
  the reader would have failed all ten for a reason already known. Claude drafted M7's "How each prompt is built" (six
  blocks and the awareness question, quoted from the protocol), from `sweep/prompt.py` and protocol §4.4-§4.5. **Checked
  against the records:** a script that follows only those written rules and the reader's folder (no harness code)
  rebuilt all ten, **10 of 10**. This proves the words are right; the reader tests whether a stranger can follow them.
  His approval of the new blocks rides with his read of the result.
- **A budget the new words broke, fixed:** with them, `/methods/` loaded 103.4 KB of JavaScript gzipped, over the 100
  KB budget, because the page's words were bundled into its chunk. The words are now a file of the build
  (`methods.json?url`, emitted under `assets/`), fetched by `loadMethodsWords` with the page's data; the thirteen ids and
  anchors stay in code (`methodsOutline.ts`) so the contents list draws at once, a test holds them equal to the file's,
  and the page refuses words whose sections differ (an alert, no section). `/methods/` now loads 88.0 KB.
  `make check` green, 3,581 and 638; browser pass 56 loads, 0 with a problem, layout shift 0.001.

**As run, step 7 (2026-11-18, his session about 5:00 PM; Claude's comparison about 5:35 PM): 10 of 10 match.** His
fresh Claude Code session in `~/hc-reconstruct`, a Claude Sonnet model (`/model sonnet`), rebuilt the ten prompts from
the preview and the folder, and `compare` found every one equal to the record's `prompt_sha256`. Its notes list seven
points the page left to a guess (a heading's join to its first line; which tool properties are required; whether the
choice has a description; whether a not-offered line on S4 carries a kind; whether the thinking sub-study's prompt is
the grid's; what the awareness probe keeps; whether the second model gets the same text). **Every guess was right, and
the page now states each** (M7's blocks reworded; Claude's rule-only rebuild still 10 of 10). Its honor statement: no
link off the site followed; one site data file fetched and not used. **No re-check with a new session:** §5.3 asks for
one after a mismatch, and there was none; the rewording only settles what the session guessed correctly. The record:
`docs/phases/evidence/phase-6.5/prompt-reconstruction/` (README, brief, samples, the rebuilds, its notes, the
comparison, and `reconstruct.py`, which reproduces "10 of 10" from there). M7's pending part now gives the result.
**DoD row 3 met** (the page says why no real case can be re-run: M6 and M7).

### 5.4 The cold-read test (Delivers 4; DoD row 4)

- **Claude in Chrome, in his browser,** on the local preview (his machine serves it; checked live before the brief
  is written, §0 item 7). No context beyond the address.
- **The brief:** read the site as a visitor would and report what it concludes, in its own words: what was tested,
  what was found, what it means. Nothing about what a right answer is.
- **Scored by Claude, against `planning/06` §4:** each conclusion is allowed, or a misreading. A misreading is fixed in
  the site and re-tested with a fresh agent. The record goes to `docs/phases/evidence/phase-6.5/`.

**As run, step 8 (2026-11-19, about 7:40 to 8:45 AM): no conclusion a misreading; one misread detail fixed and
re-tested.** The preview was checked live first (the served build equal, file for file, to a fresh build of `6876762`).
The brief (`BRIEF.md`) went verbatim into a new Claude in Chrome conversation in his browser, Sonnet 5.5 at medium
effort (the panel's default, kept so a stronger reader could not paper over a weak page; the re-test used the same).
Claude scored each conclusion against `planning/06` §4 with every figure checked against the data files and the
rendered pages. **First agent:** every figure right, no conclusion a misreading; one detail misread, caused by the
site: closure-07's choice-only reading said "30 runs compared, 0 on the choice alone" under "Only the choice is coded",
and nothing said what a choice-only distance means, so the agent read "0 runs compared" and could not square 1.000
with Plant 6. **Fixed** (his approval of Claude's words, all three): (a) a choice-only reading's rows say "each on its
choice alone"; (b) a note says a run counts 0 or 1 by its choice, so 1.000 means none made the company's choice; (c)
the cases introduction says a case's runs used its own background file, so Plant 6's result does not carry over.
Tests added and mutation-checked; `make check` green (3,581 and 641); browser pass clean. **Second agent (fresh):** no
misreading; it read closure-07 and stated the distance correctly (the fix confirmed). Recorded at the edge, not fixed:
both readers took the long-horizon pair's splits as the Roundtable's claim failing (the second for both models); **his
decision, about 8:42 AM: no sentence added** (Claude's lean: a fair reading of a test result, the scope sentence is on
every surface, and words at that spot risk the site arguing). The record: `docs/phases/evidence/phase-6.5/cold-read/`
(the brief, both reports verbatim, both scorings). **DoD row 4 met once C8 is committed.**

### 5.5 The public checks (Delivers 6, 7; DoD row 6)

`planning/06` §9's seven checks on every surface (the explorer's pages, the methods page, the share cards, the story,
the video and its captions), each recorded with its result; the four readers' notes (§5); the search check re-run on
the four published case descriptions (§6.3; the record notes it is a second run, on another day); the memo name scan
confirmed by construction on what is deployed (the explorer holds real-case memo text); the vocabulary recheck, its
sources re-read live and the result dated on the page (M10).

**As run, step 10 (2026-11-21, about 4:20 to 5:10 AM; record `docs/phases/evidence/phase-6.5/public-checks/README.md`).**
Claude read every surface: the 14 explorer paths as rendered (a headless dump, every details section open), the 14 cards,
and the video's transcript and script against the grid data. Checks 1-3 and 5-7 pass after three findings, each settled
by his decision on Claude's recommendation: (1) `/studies/` gave no difference or interval for the sub-study's five
comparisons; it now does, with one line for each of §6.5's rules where the analysis applied them, since all five
intervals have no width (every run of each goal held one value); (2) two video lines say more than the site does (the
falling-orders line, true of the long-term pair only, where Haiku's short-term pair split; "about the exact same call",
without "on this one measure"); disclosed on M11, not regenerated, so M11 now lists six differences, not four; (3) the
name is explained on `/` only; the site is read as one surface opening at `/`, and the cards and the video are accepted
without it for v1. **The search re-run** (Claude at his instruction, after the permission check first refused the read
of the private appendix and he allowed it): 12 searches, the four published descriptions at their published levels with
the same two variations, no hit; the detail in the private appendix. **The memo scan by construction:** no case sweep in
`data/memos/`, no memo text in `data/cases/`, and none of 7,415 sentence openings from the 1,237 published case memos
anywhere in the build. **The vocabulary recheck:** `planning/06` §11's sources re-read (7 of 10 read; one empty, one
behind a login, one not fetched by rule) and its re-check topics searched; the list stands, and M10 says so, dated
(the page's last placeholder). **Check 4:** his read, one pass, "fine for now", with no note per reader; the same read
approved the Claude-drafted words of steps 9 and 10. `make check` green, 3,581 and 647.

### 5.6 One more decision, G

- **G. What the prompt-reconstruction reader gets** (§5.3). **DECIDED 2026-11-14, about 8:55 AM (his): (a), as leaned.**
  - (a) **Claude's lean:** the site, the content files, and each sample's recorded settings, as listed in §5.3. It
    tests what a careful stranger can do; a reader who must guess a seed is not testing the methods page.
  - (b) The site and the content files only. Stricter, but no one can rebuild a seeded order without the seed, so
    every sample fails for a reason the page cannot fix.
  - (c) (a) plus the code. Then the check proves the code runs, which the re-scoring check already proves, and not
    that the page explains it.

## 6. The video (decision C)

1. **The source pack** (the scope doc: "from the methods page and the published results only"): the methods page and
   the explorer's pages, printed to PDF from the local preview by the headless browser Phase 6 used. Nothing else is
   uploaded. Rule zero holds by construction: these are the pages the site will publish.
2. **The notebook, set up as the sprint taught:** a new notebook; the source list checked to hold only the pack, every
   "Chats from Gemini" entry unticked; notebook memory off. His Google account; he generates, Claude writes the
   steering prompt and reads the producer notes against `planning/06` §4 before he renders.
3. **Two pieces:** an **Explainer** for the site, and a **Short** from the same notebook, held for Phase 7's post.
4. **The check, the gate before anything ships:**
   - **Frames:** extracted every two seconds (ffmpeg); Claude reads every frame's on-screen text against the data
     and §4. Made-up text, a number not on the site, or a claim past §4's allowed column fails the frame.
   - **Narration:** transcribed locally (a local open-source speech-to-text tool, its version checked at install, run
     in scratch, never shipped), checked line by line by Claude; he listens once through as well, since Claude cannot
     hear tone or a mispronounced name.
   - **A failure** is fixed by steering and regenerating, not by editing around it. If the narration fails and the
     pictures pass, ElevenLabs narration over the same pictures is the fallback (its cost named first).
5. **On the site** (M11): `<video>` with `preload="none"`, a poster frame, **captions** (a WebVTT file built from the
   checked transcript), the transcript as text below it, and the label: AI-generated, every tool named.
   `media-src 'self'` in `bootstrap` at go-live (§7).
6. **Decision F: where the video file lives.** **DECIDED 2026-11-14, about 8:55 AM (his): (a), as leaned.**
   - (a) **Claude's lean:** in the repository under `web/public/`, re-encoded to stay under GitHub's 50 MiB warning,
     with a media budget added to `check-dist.mjs` and a named exception in `check-added-large-files`. Every deploy,
     and the teardown test's re-apply, then brings it back with the rest of the site.
   - (b) Uploaded to the site bucket by hand, outside the repository: no binary in git, but a deploy from scratch
     loses it, which breaks "Terraform for everything" in spirit and the teardown test's "page back".
   - Either way, **a binary file is the one surface the name guard cannot read** (CLAUDE.md); the frame check is its
     rule-zero check.

**As run, step 9 (2026-11-20; record `docs/phases/evidence/phase-6.5/video/README.md`).** Four Explainers in one
notebook (memory off, Classic, producer notes reviewed by Claude before each render). Attempts 1 and 2 came from the
14-page source pack, attempt 3 from the methods and story pages only; each failed the check (a result read the wrong way
round, run counts not the study's, results the site does not list, the steering prompt read aloud). **Attempt 4 came from
a narration script Claude wrote from the site's pages at his request, every figure checked against the explorer's data:
a departure from item 1** ("nothing else is uploaded"), logged. It passed on every figure and failed on two lines at its
end: the scope was dropped, and "every response they gave on it is published" followed the real cases. **His decision
(12:17 PM): keep it with one edit, logged as a departure from item 4** ("regenerating, not editing around it"): ffmpeg
cut the last sentence and added an 8 s card of `his.json`'s scope sentence before the closing logo; the kept file was
checked again (12 distinct frames, transcript equal to attempt 4's less the cut sentence). At 11:58 AM the gate was
split, his agreement: a wrong number, a reversed direction, a claim past `planning/06` §4, invented on-screen text or a
missing scope fail; tone, agenda slides, plain titles and length are his call. Four kept wordings that differ from the
site are disclosed on M11. **Decision F as built:** the files are in `web/explorer-media/` (served at `/media/` by the
explorer build only), not `web/public/`, because both builds copy `public/` and the placeholder page must not change
before go-live; `check-dist` holds a media budget (20 MiB, `.mp4`, `.vtt`, `.jpg`, explorer only) and
`check-added-large-files` names the video. M11 shows the label (every tool named), the player (`preload="none"`, poster,
captions), how it was checked, the edit, the differences, and the spoken words below it; M0 links to it. **Until go-live
adds `media-src 'self'` (section 7), the preview's policy blocks the video and its captions:** the poster and the words
show, and `/methods/` logs two policy errors, which the browser pass will report until then. Not done: the Short for
Phase 7 (item 3). The labels and M11's words are Claude-drafted, his to approve.

## 7. The go-live checklist (decision B; Delivers 8, 9)

In order, each item checked off in this doc with its evidence:

1. **Every check in §5 has passed** (Delivers 2-7). Nothing below starts before.
2. **`main`:** the CloudFront Function (a path ending in `/` gets `index.html`) and a not-found page served with
   status 404 (decision B). Can be applied before go-live: it serves the placeholder just as well.
3. **`bootstrap`, his apply:** `media-src 'self'` added; the `X-Robots-Tag: noindex` header removed
   (`infra/terraform/bootstrap/site.tf`).
4. **The go-live commit:** Deploy builds the explorer, not the placeholder; the `noindex` meta tag removed; Deploy
   syncs the cards and the video and never `.vite/` (Phase 6 C3 note); the placeholder build kept as a mode, unused.
5. **The teardown test,** once, after 2 and 3 (`main` changed): destroy, re-apply, the rewrite updated, the page back,
   the raw results intact.
6. **The live site against the preview, view by view:** every path, both widths, the number trace and the crop check
   run on the live URL; each path's HTML fetched with no script to confirm its own title and card (what a crawler
   sees); an unknown path answers 404.
7. **Link previews on the platforms themselves,** now possible (Phase 6 decision 2): each share card checked in at
   least LinkedIn's post inspector.
8. **The changelog starts** (M12) with go-live as its first entry.

**As built, step 6 (2026-11-18, Opus; item 2).** Facts read live the same day: CloudFront Functions cost $0.10 per
million invocations after 2,000,000 free a month (always free), so at this traffic nothing; a function can be tagged,
`CreateFunction` carries its tags in the request (`aws:RequestTag`), and every function action but the create takes
`aws:ResourceTag` on an ARN that holds the function's **name** (AWS's service authorization reference and the
CreateFunction API reference); the pinned provider (6.67) gives `aws_cloudfront_function` a `tags` argument.
- **What the doc did not foresee:** `main` is applied by Deploy, as the deploy role, and that role had no function
  permission. So the change has two halves. **`bootstrap` (his apply, first):** `infra/iam/deploy-site.json` gains three
  statements: `SiteFunctionCreate` (`CreateFunction`, any resource, only with `Project=horizon-compact` in the request),
  `SiteFunctionManage` (update, publish, delete, tag, untag, on `function/horizon-compact-*` and only with that tag),
  `SiteFunctionRead` (describe, get, list tags, on `function/horizon-compact-*`, unconditioned for the reason the
  distribution's read after delete is). The retag deny already covers functions (its resource is `*`). No new
  `cloudfront:*` and no write on the two bootstrap objects; `test_architecture.py` pins all three.
- **`main` (Deploy, on his push):** `aws_cloudfront_function.site_paths` (`horizon-compact-site-paths`,
  `cloudfront-js-2.0`, published, tagged by `default_tags`), code in `infra/terraform/main/functions/site-paths.js`: a
  path ending in `/` gets its `index.html`; a page path with no slash and no file extension gets a permanent, relative
  redirect to the slash form, its query string kept; a file passes. Associated as `viewer-request`. The two error
  responses (403, 404) now serve `/404.html` with **status 404**, where they served `/index.html` with 200.
- **The not-found page, in both builds:** the placeholder's `404.html` is its own page titled "Page not found: Horizon
  Compact" (a Vite plugin, `placeholderNotFound`); the explorer's is written by `write-paths.mjs` from the explorer's
  page, with no canonical link and no share tags, and the shell shows the not-found view at any address. `check-dist`
  requires it in both (the placeholder build now holds exactly `index.html` and `404.html`) and counts its JavaScript
  as the entry alone (82.5 KB gzipped, under 100 KB).
- **Deploy's smoke test** now also requires an unknown address on the distribution to answer 404 with the not-found
  page, retried for about six minutes, since a distribution change reaches the edge after the apply.
- **Proof so far.** `make check` green: Python 3,581, web 636 (`web/src/site-paths.test.ts`, five cases, runs the file
  Terraform uploads). Mutations: the function serving `/` unchanged fails it (`expected { uri: '/' } to match object {
  uri: '/index.html' }`); a placeholder build without `404.html` fails `check-dist` ("must hold exactly two HTML files").
  **His `bootstrap` half, done 2026-11-18, about 11:57 AM:** his plan (`scratch/p65-s6-plan.sh`): **0 to add, 1 to
  change, 0 to destroy**, the one change `aws_iam_role_policy.github_deploy_site` gaining exactly the three statements
  above, the others unchanged; his apply: "Apply complete! Resources: 0 added, 1 changed, 0 destroyed.", the two site ids
  as §17 of the Phase 1.5 doc recorded them; his second plan: "No changes." **His commit C6 `954b222` and push; CI
  `44364703009` and Deploy `44364703011` green, first attempt, no permission added.** Claude's read of the Deploy log:
  the plan read "2 to add, 2 to change, 1 to destroy" (the function and the task definition replaced as on every image
  build; the distribution in place; the site bucket's policy shown only because the distribution's ARN reads as known
  after apply during an in-place update) and the apply "2 added, 1 changed, 1 destroyed", the bucket policy never
  modified; `aws_cloudfront_function.site_paths: Creation complete after 2s`. The smoke test: "an unknown address answers
  the not-found page with 404 (attempt 1)", every header ok. **On the public address** (Claude, curl, about 12:07 PM):
  `/` 200 "Horizon Compact"; `/no-such-page/` **404** "Page not found: Horizon Compact"; `/methods` **301** to
  `https://horizon-compact.vercel.app/methods/`, so the relative redirect stays on the rewrite's host; `/404.html` 200 (a
  file). Per-page HTML and cards are checked at go-live (item 6), since the placeholder has one page. **Item 2 done.**

**As built, step 11 (2026-11-21, Opus; items 3, 4 and 8; record `docs/phases/evidence/phase-6.5/go-live/README.md`).**
Begun at his go-ahead (9:43 AM). The go-live commit holds `bootstrap`'s new headers policy (`media-src 'self'`
added; the `X-Robots-Tag: noindex` header removed), which he applies before pushing, and what goes with it: the
preview's mirrored policy; the explorer's `noindex` tag taken off every page and kept on the not-found page alone
(`renderNotFound`); `check-dist` refusing a robots tag on a live page and any placeholder in his words or the shipped
methods words; Deploy syncing `web/dist-explorer` (never `.vite/`; captions as `text/vtt`, memo files as `text/plain`)
with a smoke test for the explorer's entry, the headers (retried; `media-src` present, no `x-robots-tag`), each media and
data type, `/methods/` as its own page and the manifest's absence; the architecture tests to match; M12's first entry.
**What the doc did not foresee:** the item-4 line ("Deploy builds the explorer, not the placeholder") was a sync and a
smoke test, not a build switch: `npm run check` already built both, and the smoke test was the placeholder's (its bundle
named the placeholder's sweep). Proof before the push: `make check` green (3,581 and 649); the new refusals
mutation-checked on the built files (a pending block in the methods words; a robots tag on `/methods/`); on a fresh
preview with the new policy, the video loads (ready state 4, 163.5 s) with its 59 caption cues and no console or policy
error. **Done the same day** (the record has each item's evidence): item 3, his apply (0 to add, 1 to change, 0 to
destroy); item 4, C11 `42e6284`, CI `44922943678` and Deploy `44922943677` green on the first attempt, **the site public
from about 10:15 AM**; item 6, the live site and a fresh preview give identical reports (14 paths with no script; 56
browser loads each, none with a problem); item 5, the teardown test passes (destroy `44928743719`, 21 destroyed, the
first real run of the INACTIVE-cluster check, passing; re-apply `44929157666`, 21 added, the new distribution
`E34HK7Y6ZF40HF`; the rewrite moved and deployed by him; before and after identical); item 7, LinkedIn's Post Inspector
shows the story's title, description and card (his read). The public site was down about 1 hour 45 minutes during the
teardown test.

## 8. The steps and the commit order

Sonnet builds code steps and Opus reviews each diff, as in every phase since 3; Opus builds the infrastructure, as in
Phase 1.5's C4. Every commit is his, after `make check` and the hooks' dry run.

| Step | What | Who | Commit |
|---|---|---|---|
| 0 | **[done 2026-11-14]** This doc approved; the scope doc amended (one dated header note pointing to §0; dated notes on Delivers 3, DoD row 8's duplicate number, and Delivers 6's memo scan) | him; Opus | C0 |
| 1 | **[done 2026-11-14]** `hc site raw-pull` and `hc site raw-verify` (§5.1), on fakes | Opus (his choice) | C1 |
| 2 | **[done 2026-11-15]** His pull; Claude's verify; the packed size and the guard's time measured | him; Claude | C2 (the raw text) |
| 3 | **[done 2026-11-16, §5.2; built by Sonnet, reviewed by Opus]** The re-scoring test, and its failure shown once (§5.2) | Sonnet; Opus reviews | C3 |
| 4 | **[done 2026-11-17, §3; built by Sonnet, reviewed by Opus]** The methods page: the route, its data, its sections with placeholders for his titles (§3, decision E) | Sonnet; Opus reviews | C4 |
| 5 | **[done 2026-11-18, §3; approved (his), C5 `fc8e65e`]** Its words: Claude drafts the technical descriptions, each flagged; his titles and project sentences (Claude-drafted too, his instruction of 2026-11-18); every ledger line placed, checked by script | him and Claude | C5 |
| 6 | **[done 2026-11-18, §7 "As built, step 6"; his `bootstrap` apply, C6 `954b222`, Deploy green]** Serving in `main` (§7 item 2) | Opus; his apply | C6 |
| 7 | **[done 2026-11-18, §5.3 "As run, step 7": 10 of 10]** The prompt-reconstruction check (§5.3) and any fixes | him (the fresh session); Claude | C7 |
| 8 | **[done 2026-11-19, §5.4 "As run, step 8": no misreading after one fix, re-tested]** The cold-read test (§5.4) and any fixes | him (Chrome); Claude | C8 |
| 9 | **[done 2026-11-20, §6 "As run, step 9"; attempt 4 kept with one edit, two departures logged]** The video (§6): pack, generation, check, captions, the file | him and Claude | C9 |
| 10 | **[done 2026-11-21, §5.5 "As run, step 10": three findings fixed or disclosed, the search re-run passes]** The public checks (§5.5) | Claude; him for the four readers | C10 |
| 11 | **[done 2026-11-21, §7 "As built, step 11": live from about 10:15 AM; the teardown test passes]** Go-live (§7 items 3-8), the teardown test | Opus; his apply and deploy | C11 |
| 12 | **[done 2026-11-21, §11]** The close: DoD audit, version `0.6.5`, cost | Opus | C12 |

Steps 7 and 8 come after 5 because they test the page's words; step 9 after them because the video is made from the
fixed page.

## 9. Definition of done

The scope doc's rows, renumbered (its two rows 8 become 8 and 9), with what this doc adds:

1. The methods page is complete against Delivers 1 and **every ledger line (§1) is on it**, checked by script; he has
   approved it.
2. The re-scoring check is in CI and passes; it failed once when one number was changed by hand, recorded.
3. The prompt-reconstruction check passes for all ten samples, or every gap it found is fixed and re-checked; the
   page says why no real case can be re-run.
4. The cold-read test's conclusions all fit `planning/06` §4, after fixes, with its record committed.
5. The video passed its frame and narration checks, is captioned and labeled, or he decided not to publish it, with
   the reason.
6. Every §9 check passes on every surface; every public case description fails to identify its company in a search;
   the deployed site holds no real-case memo text; the vocabulary recheck is dated.
7. The site is live at `horizon-compact.vercel.app` and matches the preview; each path serves its own HTML and card to
   a client running no script; an unknown path answers 404.
8. The full text of every Phase 4 pilot and official object is published, and `hc raw verify` passes against
   `raw-manifest.json`.
9. `make check` and CI are green, and every commit passed the guard.
10. *Added:* KNOWN-GAPS OPEN 2026-10-31 closed (both matcher notes on the methods page).
11. *Added:* the teardown test passed after the changes to `main`.

## 10. Cost

No experiment call. AWS: his S3 read of 5,247 objects (well under a cent), the CloudFront Function's invocations (at
this traffic, cents a month at most; checked on the pricing page before step 6), hosting. Outside AWS: the fresh
session and Claude in Chrome on his Claude plan; Gemini Notebook on his free Google account; ElevenLabs only as the
fallback, its cost named first. The ceiling and re-plan point stand ($80, $60); cumulative is at most about $46.

## 11. The close (C12), 2026-11-21: the DoD audit, the version, the cost

Claude (Opus), on his instruction to finish step 12 and commit once with step 11's records ("can we bypass the
gitcommit for now and wait and do it after we finish step 12 to make it a finale end of step 6.5 commit", about 2:44
PM). One commit carries step 11's teardown and live-check records, the moved rewrite (`infra/vercel/vercel.json`) and
this section.

### 11.1 The DoD audit (§9)

| DoD | Met | Proof |
|---|---|---|
| 1. The methods page complete against Delivers 1; every ledger line on it, by script; his approval | yes | `methods.test.ts`: the 43 ledger ids, each placed, against §3's table, section by section; every figure traced to its source and no digit untraced. His approval: C5 (`fc8e65e`), and his reads of the words added at steps 7 to 10 (§5.3, §5.4, §6, §5.5). **M12's first entry (step 11, Claude-drafted) awaits his read** |
| 2. The re-scoring check in CI and passing; failed once on a number changed by hand, recorded | yes | `tests/test_analysis_rescoring.py` (the three official sweeps from `experiment/raw/`, byte for byte, no AWS client) and the re-validation test in the same file, in `make check` and CI on every commit since C3 (`9dbab42`); its mutations, §5.2 "As built, step 3" |
| 3. The prompt reconstruction passes for all ten samples; the page says why no real case can be re-run | yes | §5.3 "As run, step 7": 10 of 10 equal to the recorded sha256, his fresh session, the record in `evidence/phase-6.5/prompt-reconstruction/`; M7's "Why no case can be re-run" and "What can and cannot be re-run", on the live page |
| 4. The cold read's conclusions all fit `planning/06` §4, after fixes, record committed | yes | §5.4 "As run, step 8": one misread detail caused by the site, fixed, a fresh agent re-tested, no conclusion a misreading; `evidence/phase-6.5/cold-read/`, in C8 (`c136692`) |
| 5. The video passed its frame and narration checks, captioned and labeled | **yes, with two logged departures and two disclosures** | §6 "As run, step 9": attempt 4 passed on every figure; it came from a script Claude wrote (a departure from §6 item 1) and is shown with one edit (a departure from item 4), both logged and on M11; step 10 found two lines broader than the site, disclosed on M11 (§5.5). Captions (59 cues) held equal to the page's transcript by `methods.test.ts`; on the live site the video and its captions load with no policy error (§7 "As built, step 11") |
| 6. Every §9 check on every surface; no description identifies its company; no real-case memo text deployed; the vocabulary recheck dated | **yes, with two qualifications** | §5.5 "As run, step 10" and `evidence/phase-6.5/public-checks/`: checks 1-3, 5 and 7 pass after one fix and one disclosure; **check 6** passes on `/` and is accepted as absent on the cards and the video (his decision); **check 4** is his one read ("fine for now"), not four reads with notes. The search re-run: four descriptions, 12 searches, no hit. No case memo text in the build (7,415 sentence openings, none found). M10 dated 2026-11-21 |
| 7. Live at `horizon-compact.vercel.app`, matching the preview; each path its own HTML and card with no script; an unknown path 404 | yes | `evidence/phase-6.5/go-live/` items 4 and 6: live from about 10:15 AM; 14 paths with no script, each its own title, canonical link and card; 56 browser loads on the live URL and on the preview, identical reports; again after the teardown test; 404 on an unknown path |
| 8. The full text of every Phase 4 pilot and official object published; the verify passes against `raw-manifest.json` | yes | §5.1 "As run, step 2": `hc site raw-verify`, "ok: 5247 objects, 104785272 bytes"; `tests/test_site_rawtext.py::test_the_committed_raw_text_matches_the_committed_manifest`, on the real `experiment/raw/`, in `make check` and CI. (The doc's "`hc raw verify`" is the command `hc site raw-verify`.) |
| 9. `make check` and CI green; every commit through the guard | yes | every Phase 6.5 commit, `96ab718` to `42e6284` (12, all since Phase 6's close), green: CI `43578717282`, `43609886539`, `43735395010`, `43886444310`, `44122817993`, `44344066964`, `44364703009`, `44423330851`, `44547601602`, `44795927700`, `44898505411`, `44922943678`, and every Deploy they started; the teardown run `44928743719` and the re-apply `44929157666` green. The hooks and the name guard dry-run before each commit; no bypass recorded. `make check` exit 0 on this tree (below) |
| 10. KNOWN-GAPS OPEN 2026-10-31 closed (both matcher notes on the methods page) | yes, closed with this commit | M6, "Two behaviors of the matcher" (C5), live since go-live; the explorer's half since Phase 6 (§34.2 of its doc); the entry closed today |
| 11. The teardown test passed after the changes to `main` | yes | `evidence/phase-6.5/go-live/` item 5: destroy `44928743719` (21 destroyed; the INACTIVE-cluster check's first real run, passing), re-apply `44929157666` (21 added, distribution `E34HK7Y6ZF40HF`), the rewrite moved, before and after counts identical |

### 11.2 The version, the cost, and what Phase 7 inherits

**Version `0.6.5`** in `pyproject.toml`, `src/horizon_compact/__init__.py` and `uv.lock` (`uv lock --check` agrees).
`web/package.json` stays `0.0.0`, as at every close before.

**Cost.** No experiment call and no paid model call in the phase: the fresh session (step 7), the cold-read agents (step
8) and the web searches (step 10) ran on his Claude plan; Gemini Notebook on his free Google account; ElevenLabs was not
needed. AWS: his one S3 read of 5,247 objects (step 2, well under a cent); the CloudFront Function at this traffic
(nothing, inside its free tier); the image-building Deploys, each adding about a cent a month of ECR storage at most
(Phase 1.5 doc §26). Not read from Cost Explorer: the phase has no spend item in its DoD, and the amount is inside the
rounding of the cumulative figure, **at most about $46**, against the $80 ceiling and the $60 re-plan point. If he wants
it on the record, his Cost Explorer reading for 2026-11-14 to 2026-11-21, filtered to the `Project` tag, can be added as
a dated note.

**Carried to Phase 7:** the README and the launch post (his words, `planning/06` §6.1; the README is where a feed
reader meets the name, step 10's check 6); the Short from the same notebook (§6 item 3, not made); `planning/06` §11's
re-check of the vocabulary when the launch post is written; M12's changelog, from its first entry; the search check's
two private cross-appearances, not hits, his call to coarsen further.

**`make check`:** exit 0 on this tree: Python 3,581 passed; web 649 passed; `check-dist` ok in both modes; `doctor` ok.
