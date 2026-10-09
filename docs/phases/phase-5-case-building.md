# Phase 5 — Case Building (v0.5)

> **Scope doc.** Written 2026-10-04 from `planning/00` §5.4, `planning/01` §3.2 and §4 (all of it), `planning/02`
> §2.7, `planning/04` §2.1-2.6, `planning/05` §4.4, §5 (Phase 5's row) and §5.1, `planning/06` §2.1, §6.1 and §6.3,
> `planning/07` §10 and §12-13, and `planning/09` A6. **APPROVED 2026-10-04 (his)**, with all six decisions at the
> end taken as recommended.
>
> **Split 2026-10-04 (his, decision 1):** `planning/05`'s Phase 5 is now two phases. This doc covers **building every
> case** (the search, the log, the dossiers, the rubrics, the probes), frozen before any case runs. **Phase 5.5
> `case-runs`** (`docs/phases/phase-5.5-case-runs.md`) runs them, matches them and publishes the results. The six
> decisions were made on this doc, before the split, and are recorded here; findings 1-7 cover both halves.
>
> Written before Phases 0.5 through 4 are built. **Lines marked *(rests on N)* depend on what Phase N builds,
> measures or decides.**
>
> **Rule zero governs every line of this phase.** This doc names no company, no candidate and no identifier, and
> neither does anything this phase commits. Candidates live only in the private longlist and the private appendix.

## What this phase is for

**The protocol, applied to real decisions.** A few companies made a real capital-allocation decision after every
model's training cutoff. Each is rebuilt as an anonymized dossier from filings dated before the decision, run under the
same five objectives, three wordings and models as the fictional grid, and shown beside the objective whose runs it
most closely matched. The cases are **illustrations of the protocol, never validation of it** (`planning/00` §5.4),
and never a claim about how often companies do anything (`planning/01` §4.3).

**This is the phase with the most judgment in it, made by people who already know the grid's results.** The grid ran
in Phase 4 and its results are public. Everyone building a case knows which objective tends toward which action. The
design's answer is to make every judgment either mechanical, fixed before the tag, or checked by a reader who has not
seen the results. This doc finds the judgments that are none of those yet.

**The test of a good Phase 5:** for every case, a stranger can see from the public record that the case was chosen
by the rule, that its rubric was committed before any model saw it, that its dossier could not have told the model the
outcome, and that nothing public identifies the company.

## What scoping found

1. **The selection rule is only as mechanical as its criteria.** "The first *k* per case type, by date of first
   disclosure" (`planning/07` §10.0) is mechanical. But criteria 3 ("a real decision with real alternatives"), 4 ("maps
   onto the lever menu") and 5 ("not instantly recognizable") in `planning/01` §4.1 are judgments, and the person
   applying them can predict which objective a candidate would match. Rejecting a candidate as "does not map" is the
   one door the rule leaves open. Decision 4.
2. **The option economics can carry hindsight.** The fictional closure scenario states every option's economics with
   the same treatment (`planning/07` §3.2, §9 items 9-10). For a real closure, the costs of the option the company
   chose often first appear in the filing that announced it, after the cut-off, and the options it rejected may never
   have been costed in public. Using the post-decision numbers would leak the outcome and describe one option better
   than the others. Decision 2.
3. **The rubric is written by someone who has seen the grid's results.** `planning/04` §2.4 makes a second reader of
   the mapping optional. After Phase 4 it should not be: a borderline call (does a severance-funded relocation count
   as retool or close?) decides which objective a case matches, and the person making it knows the matcher's
   tendencies. Decision 4.
4. **Several rules this phase needs are in no frozen document.** The tag freezes the selection rule, the matcher and
   the probe (Phase 3.5, Delivers 2). It does not yet freeze: the dossier template per case type (`planning/07` §10.1
   says "fixed per case type before any case is built", but not where), **which of the four scenario shapes each case
   type uses**, the option-economics rule (finding 2), what replaces a case that fails the recognition probe, how the
   scaling factor is chosen, how uncertain rubric calls are reported, and how the gate admits a case sweep whose
   content did not exist at the tag. Written after the tag, by someone who knows the results, each is a place to bend
   the outcome. Decision 2. *(Resolved the same day: the Phase 3.5 scope doc was amended so the protocol freezes
   all of these.)*
5. **A published anonymized dossier can identify its company without naming it.** Anonymization keeps ratios,
   margins and trends on purpose (`planning/01` §4.6), and those are what a determined reader can match against public
   structured financial data. `planning/05`'s Phase 6 done-when publishes the dossiers so the experiment can be re-run.
   `CLAUDE.md` names "a description detailed enough to identify a company without naming it" as exactly what the
   guard cannot catch. Publishing a result about an identifiable company is a statement about that company, which
   the project does not make (`planning/06` §2.1). Decision 5.
6. **Building cases one at a time lets each case's result shape the next.** If case 1 is built, run and matched
   before case 2's rubric is written, case 2's borderline calls are made by someone who has just watched the matcher
   work on a real decision. Decision 1.
7. **The name guard knows the longlist's names, not each case's other identifiers.** An accepted case brings a
   filer number, a ticker, plant locations, product names and executives' names. The guard catches only what its
   private term file holds.

## Delivers

In order. All of it is done for **every** case before any case's decision runs, which is Phase 5.5 (decision 1).

1. **The projection check, repeated** (Phase 4 decision 2): measured cost per decision from Phase 4, times the case
   runs, against the $60 re-plan point, the $80 ceiling and the credit balance read that day. Any cut, in the
   pre-registered order (`planning/05` §5.1: the fifth case, then the fourth), is decided and committed here.
2. **The search, run once on the protocol's date** (Phase 3.5 decision 4), through the named channels (`planning/01`
   §4.2, §4.3, §4.7), with candidates taken in order of first disclosure inside the window (first disclosed after
   June 2026, preferably from August 1; `planning/01` §3.2). Each candidate's first-disclosure date is checked for the
   "previously announced" trap (`planning/01` §4.4) before any other criterion.
3. **The selection log:** every candidate considered, with each criterion passed or failed and why, in the private
   appendix; by case type and without names, in public. Every rejection on a judgment criterion is checked by the
   independent reader (decision 4).
4. **Identifiers into the guard, before any work on a case:** each accepted case's filer number, ticker, plant
   locations, product and brand names and executives' names are added to the private term file, so the guard refuses
   them from the moment the case exists (scoping finding 7). Every case gets a neutral label (by type and number),
   used everywhere outside the private appendix, including session notes and memory.
5. **The dossier builder** (decision 3), with the date filter enforced in code (`planning/04` §2.1): it can read only
   documents dated before the case's cut-off, the day before first disclosure. Filings are cached and fetched under
   the SEC's rate limit and User-Agent rule (`planning/01` §5) *(checked live in the IMPLEMENTATION doc)*. Raw filings
   and all identifying material stay in the private appendix.
6. **Each case's dossier and scenario text:** the template for its type (decision 2), anonymized, with dollars and
   headcounts scaled by one factor drawn by the protocol's rule (`planning/01` §4.6); then the **foreshadowing check**
   on the dossier *and* the scenario text (`planning/07` §10.1); then the **neutrality checklist** (`planning/07` §9) on
   the scenario text, since its options are now real. Frozen with a hash.
7. **Each case's rubric** (`planning/07` §10.2): what the company did, from post-decision filings, mapped onto the
   scenario's table and choice; actions only, never stated reasons (`planning/06` §2.1); observable and excluded
   dimensions; every uncertain call with its alternative reading. Read by the independent reader (decision 4).
   **Committed before any model sees the case**, and the commit predates the case's first model call.
8. **The recognition probe** (`planning/07` §10.3): three calls per model on the frozen dossier. A failure is
   coarsened and re-probed once; a second failure drops the case, which is replaced by the protocol's rule (decision
   2) and logged.
9. **The freeze:** every accepted case's dossier, scenario text and rubric hashes, its probe records, its
   independent reads and the selection log, committed together with the list of cases Phase 5.5 will run. From this
   commit on, a case is changed only by the protocol's rules (coarsening after a failed probe, replacement), and
   every change is logged.

## The rules this phase must not break

- **Rule zero.** No company name, ticker, filer number, brand, product, executive or plant location in any tracked
  file, commit message, branch, tag, prompt log that is published, or anything typed into GitHub. The guard is the
  backstop, not the method; neutral labels are the method.
- **Hindsight never reaches a dossier.** The builder reads only pre-cut-off documents, enforced in code; the
  extraction step is never told what the company did; option economics come only from pre-cut-off documents
  (decision 2).
- **The rubric precedes the model.** No model sees a case before its rubric is committed. The git timestamp is the
  proof, and the gate checks it.
- **Selection is by the rule.** A candidate is never chosen or skipped for the result it might give. A type that
  yields fewer than *k* is a reported shortfall, never filled by judgment (Phase 3.5 decision 4).
- **What the company said is not what it did.** The rubric records actions; no public surface says or implies any
  case was "AI-washing" or anything else about a company's motives (`planning/06` §2.1).
- **No case's decision runs in this phase.** The only model calls on a case are the recognition probe, which comes
  after its rubric, and the extraction step, which sees only pre-cut-off documents and never the outcome.

## Explicitly not in this phase

- **The case runs, the matching, the memo name scan and publication.** Phase 5.5.
- **The explorer's real-case view and the methods page.** Phase 6.
- **Public prose about any case.** Phase 7, in his words, under the same coarse-description rule.
- **The frequency study** ("how often do companies do X"), which counts from financial statements, not
  announcements. Post-v1 (`planning/00` §6.1).
- **Retrieval and reranking over filings,** unless decision 3 chooses it. They return in the frequency study either
  way (`planning/05` §5.1 item 4).
- **A model not fixed in Phase 3.5.** A later model runs the same cases in a later phase with its own window check
  (`planning/04` §2.3).

## Definition of done

1. **At least three cases are built, including at least one invest or retool case** (`planning/05` §5.1's never-cut
   list), or a shortfall is reported by type with the selection log that produced it.
2. **The selection log is complete:** every candidate considered, every criterion, every reason, and every rejection
   on a judgment criterion checked by the independent reader.
3. **Every case's dossier and scenario text passed the foreshadowing check and the neutrality checklist,** with the
   records committed, and every dossier was built only from pre-cut-off documents, shown by the builder's source list.
4. **Every case's rubric is committed and independently read,** and its commit predates the case's first model call
   (the probe).
5. **Every case passed the recognition probe** on every model, or was coarsened, re-probed, or dropped and replaced by
   the rule, all logged.
6. **The freeze commit exists** (Delivers 9), and no case decision has been run.
7. **Each case's identifiers were in the term file before its first commit,** every commit passed the guard, and
   `make check` and CI are green.
8. **Measured cost is recorded,** and the $60 re-plan point was checked before any case work (Delivers 1).

## Prerequisites

- **Phase 4 complete,** with its measured cost and its results committed (the search date follows from that
  commit, decision 6).
- **Phase 3.5's protocol holds what this phase needs frozen** (decision 2) *(rests on 3.5)*.
- *(rests on 3)* The matcher, its no-match threshold and its minimum-evidence rule.
- **The private appendix and the term file in place** on the laptop, with the private repo as their backup
  (`planning/01` §4.8).
- **A contact for the SEC's User-Agent rule,** his choice of name and address (`planning/01` §5).

## Cost

**A few dollars.** The dossier builder's extraction calls cost cents to about a dollar a case (decision 3); the
recognition probes are three calls per case per model, well under a dollar in all; the independent reader is a
handful of calls (decision 4). The case runs, about $18-20 of `planning/05`'s "$20-25", are Phase 5.5's. **The
projection in Delivers 1 covers both halves and runs before any of it.**

The independent reader runs on Bedrock under the credits where a suitable other-vendor model is available there, so
it costs no cash *(checked live in the IMPLEMENTATION doc)*; otherwise through OpenRouter, about $1-3, which is his
prepaid balance, not AWS.

## The main model

**Fixed in Phase 3.5.** The cases run on the same model set as the grid, with the strict window either way, so a later
model can run the same cases (`planning/04` §2.3). Sonnet 4.6's end of life is not sooner than 2027-02-17; the
protocol records each model's date, and this phase is scheduled against it.

## Known risks

- **Too few qualifying cases**, especially invest or retool (`planning/04` §2.3). Mitigation: the strict window
  grows with time, so the search date is set late enough to give it room; the retool fallback; a shortfall reported,
  never filled.
- **A decision first mentioned only on an earnings call.** Transcripts are out of scope (`planning/01` intro), so a
  call-only mention before the window can be missed. Mitigation: the earnings release on EDGAR is checked; the
  residual risk is stated on the methods page.
- **Re-identification** through the dossier or the public description (scoping finding 5, `planning/04` §2.5).
  Mitigation: decision 5 and the search check.
- **A name slips into a tracked file** while working with raw filings (`planning/04` §2.6). Mitigation: identifiers
  into the term file before work (Delivers 4), neutral labels, raw material only in the private appendix.
- **The extraction step summarizes toward the outcome.** Mitigation: the code-enforced date filter, a template that
  fixes the sections, an extraction prompt that never states the outcome, and the foreshadowing check.
- **Building takes long enough that a case's window or the model's end of life presses.** Mitigation: the
  projection and the schedule are checked in Delivers 1; Sonnet 4.6's end of life is not sooner than 2027-02-17.
- **The pipeline grows into a project of its own.** Mitigation: decision 3 keeps v1's builder minimal; `planning/05`
  §5.1 item 4 already allows hand-built dossiers in the same frozen format.

## Decisions for him

All six taken 2026-10-04 (his), as recommended. Each keeps its original framing under *Was:* as the record.

1. **DECIDED 2026-10-04 (his): (a), build every case first, split into Phase 5 `case-building` and Phase 5.5
   `case-runs`.** `planning/05` status line patched. *Was:*
   **Build every case before running any, and split the phase.**
   - (a) **Recommended: yes, as two phases.** **Phase 5 `case-building`** (v0.5): the projection, the search and log,
     the identifiers, the builder, every dossier, scenario text, rubric and probe, all frozen and committed. **Phase
     5.5 `case-runs`** (v0.5.5): the runs, the matching, the name scan and publication. No rubric is written after any
     case result exists (scoping finding 6). Phase 5 builds new code (the dossier builder) and deserves its own
     IMPLEMENTATION doc; Phase 5.5 is a runbook, like Phase 4.
   - (b) One phase, each case built and run in turn. Faster to a first case, but later rubrics are written after
     earlier results.
2. **DECIDED 2026-10-04 (his): (a), in the protocol.** Phase 3.5 scope doc amended; `planning/07` §10.0-10.4
   patched. *Was:*
   **Freeze the missing rules in the protocol, before the tag.**
   - (a) **Recommended:** a dated amendment to the Phase 3.5 scope doc, so the protocol also holds: the dossier
     template per case type; **the scenario shape each case type uses** (a closure on S3's close, retool or sell; an
     AI-attributed workforce change on S1; an invest or retool case on S3 with retool or on S4 for a funded program; a
     restructuring without a facility on S2), chosen by a stated rule from the first-disclosure document; **the
     option-economics rule** (option figures only from pre-cut-off documents; where an option has none, every option
     is described without figures alike, `planning/07` §9 items 1 and 10); **the replacement rule** (a case dropped by
     the probe is replaced by the next eligible candidate of its type, in disclosure order); **the scaling-factor
     rule** (drawn from a stated range with a private recorded seed, never chosen); **the uncertain-call rule** (each
     case is also matched under every uncertain call's alternative reading, and a match that changes is reported as
     "depends on reading"); and **the gate's case mode** (a case sweep is admitted only when its dossier, scenario
     text and rubric hashes are in a commit that predates the sweep and its probe passed). `planning/07` §10.1-10.4 get
     the matching dated patches.
   - (b) Write them in this phase, committed before the search runs, outside the protocol. Simpler, but written after
     the grid's results by someone who knows them.
3. **DECIDED 2026-10-04 (his): (a), a minimal builder.** `planning/02` §2.7 patched. *Was:*
   **How dossiers are built.**
   - (a) **Recommended: a minimal builder.** Fetch filings by date with the cut-off enforced in code; select sections
     by the template's fixed list of sections, not by a search query; extract each section into the template with a
     model that sees only those pre-cut-off sections and is never told the outcome; anonymize and scale; human review;
     freeze. No embeddings and no reranker in v1: a retrieval query is written by someone who knows the outcome, and
     a fixed section list is easier for a stranger to audit. What it gives up: the retrieval-and-rerank pipeline as a
     piece of AI engineering to show, which moves to the frequency study, where it is needed (`planning/05` §4.4).
   - (b) The full retrieval-and-rerank pipeline of `planning/02` §2.7. Stronger as engineering to show; more to build
     and test, and a query shaped by hindsight to guard against.
   - (c) By hand, with Claude extracting in a working session. Least code, but the extractor knows the outcome, and the
     date filter becomes a discipline instead of a check.
4. **DECIDED 2026-10-04 (his): (a), required, on judgment rejections and every rubric.** `planning/04` §2.4
   patched. *Was:*
   **An independent reader where judgment remains.**
   - (a) **Recommended: required, on two things.** Every candidate rejected on a judgment criterion (`planning/01`
     §4.1 items 3-5), and every rubric's mapping. The reader is another vendor's model, given the criteria or the
     rubric with its source excerpts, never the grid's results; a disagreement is resolved by him and logged with the
     reason. On Bedrock under the credits where possible, otherwise OpenRouter.
   - (b) Optional, as `planning/04` §2.4 has it.
5. **DECIDED 2026-10-04 (his): (a), dossiers only after a re-identification check.** Carried out in Phase 5.5.
   `planning/05` Phase 6 done-when patched. *Was:*
   **What real-case material is published.**
   - (a) **Recommended:** the case results as data, by case type, committed at the end of the case runs (as Phase 4
     decision 5), with coarse descriptions and name-scanned memos. **Each anonymized dossier is published only after a
     re-identification check passes**: its distinctive figures and description are searched against public sources,
     including the structured financial data it was built from. A dossier that fails is withheld, the reason stated,
     and the methods page says which cases can be re-run from published inputs. `planning/05`'s Phase 6 done-when gets
     a dated patch from "including the anonymized dossiers" to "including every anonymized dossier that passed the
     re-identification check."
   - (b) Publish every dossier, as `planning/05` has it.
   - (c) Publish no dossier. Safest, but no case can be re-run by a stranger.
6. **DECIDED 2026-10-04 (his): (a), the day after Phase 4's results are committed.** Phase 3.5 scope doc amended;
   `planning/07` §10.0 patched. *Was:*
   **When the search runs.**
   - (a) **Recommended: fixed by a rule in the protocol, not by a choice:** the search runs on **the day after
     Phase 4's results are committed** (Phase 4 decision 5), with the window closing the day before. It is as late as
     the schedule naturally allows, and every week adds candidates inside the window, which matters most on the
     scarce invest side (`planning/04` §2.3). A rule matters because a chosen date is a lever: the private longlist
     already exists, so someone who knows its candidates and the grid's results could time a search to take in or
     leave out a particular one. Phase 3.5 left the date to its IMPLEMENTATION doc; this sets the rule it uses.
   - (b) A calendar date chosen at the tag. Equally mechanical, but it has to guess when Phase 5 will start, and a
     guess that is too early wastes weeks of candidates.

## Left for the IMPLEMENTATION doc

*Note 2026-10-09 (Phase 3.5 IMPLEMENTATION doc §3 items 10-11, decisions 6 and 7, his):* **the search queries per
channel, the template per case type section by section, and the scaling factor's range are frozen in the protocol**,
not written here; the Phase 3.5 scope doc's amendment (from this doc's own decision 2) governs. This doc's
IMPLEMENTATION doc runs them as written and reports any deviation.

The search queries per channel, exactly. The template per case type, section by section. The extraction model and its
prompt. The scaling factor's range. The independent reader's model and brief. The SEC User-Agent and
rate handling, checked live. Where the private appendix's cache lives and how it is backed up. The neutral labeling
scheme. What the freeze commit holds, file by file. The order of the commits, with which ones touch the private repo
instead of this one.
