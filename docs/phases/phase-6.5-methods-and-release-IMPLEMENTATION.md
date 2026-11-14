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

### 5.4 The cold-read test (Delivers 4; DoD row 4)

- **Claude in Chrome, in his browser,** on the local preview (his machine serves it; checked live before the brief
  is written, §0 item 7). No context beyond the address.
- **The brief:** read the site as a visitor would and report what it concludes, in its own words: what was tested,
  what was found, what it means. Nothing about what a right answer is.
- **Scored by Claude, against `planning/06` §4:** each conclusion is allowed, or a misreading. A misreading is fixed in
  the site and re-tested with a fresh agent. The record goes to `docs/phases/evidence/phase-6.5/`.

### 5.5 The public checks (Delivers 6, 7; DoD row 6)

`planning/06` §9's seven checks on every surface (the explorer's pages, the methods page, the share cards, the story,
the video and its captions), each recorded with its result; the four readers' notes (§5); the search check re-run on
the four published case descriptions (§6.3; the record notes it is a second run, on another day); the memo name scan
confirmed by construction on what is deployed (the explorer holds real-case memo text); the vocabulary recheck, its
sources re-read live and the result dated on the page (M10).

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

## 8. The steps and the commit order

Sonnet builds code steps and Opus reviews each diff, as in every phase since 3; Opus builds the infrastructure, as in
Phase 1.5's C4. Every commit is his, after `make check` and the hooks' dry run.

| Step | What | Who | Commit |
|---|---|---|---|
| 0 | **[done 2026-11-14]** This doc approved; the scope doc amended (one dated header note pointing to §0; dated notes on Delivers 3, DoD row 8's duplicate number, and Delivers 6's memo scan) | him; Opus | C0 |
| 1 | **[done 2026-11-14]** `hc site raw-pull` and `hc site raw-verify` (§5.1), on fakes | Opus (his choice) | C1 |
| 2 | His pull; Claude's verify; the packed size and the guard's time measured | him; Claude | C2 (the raw text) |
| 3 | The re-scoring test, and its failure shown once (§5.2) | Sonnet; Opus reviews | C3 |
| 4 | The methods page: the route, its data, its sections with placeholders for his titles (§3, decision E) | Sonnet; Opus reviews | C4 |
| 5 | Its words: Claude drafts the technical descriptions, each flagged; his titles and project sentences; every ledger line placed, checked by script | him and Claude | C5 |
| 6 | Serving in `main` (§7 item 2) | Opus; his apply | C6 |
| 7 | The prompt-reconstruction check (§5.3) and any fixes | him (the fresh session); Claude | C7 |
| 8 | The cold-read test (§5.4) and any fixes | him (Chrome); Claude | C8 |
| 9 | The video (§6): pack, generation, check, captions, the file | him and Claude | C9 |
| 10 | The public checks (§5.5) | Claude; him for the four readers | C10 |
| 11 | Go-live (§7 items 3-8), the teardown test | Opus; his apply and deploy | C11 |
| 12 | The close: DoD audit, version `0.6.5`, cost | Opus | C12 |

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
