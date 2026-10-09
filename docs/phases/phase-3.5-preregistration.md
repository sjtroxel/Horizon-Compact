# Phase 3.5 — Pre-registration (v0.3.5)

> **Scope doc.** Written 2026-10-04 from `planning/05` §2, §3.1, §5 (Phase 3's row) and §5.2, `planning/07` (all of
> it: this phase freezes it), `planning/04` §1.2, §1.9 and §2.3, `planning/01` §3, `planning/08` §3.6, and
> `planning/09` §5. **APPROVED 2026-10-04 (his)**, with all six decisions at the end taken as recommended.
>
> **Split out of Phase 3 on 2026-10-04** (his, Phase 3 decision 1).
>
> **Amended 2026-10-05 (his):** Sonnet 4.6 is the v1 main model, fixed; Sonnet 5.5 is no longer awaited
> (`KNOWN-GAPS.md`). Decision 5 is closed, "The main model" names Sonnet 4.6, and constraint 3 has no fallback.
>
> **Amended 2026-10-04 (his), from `docs/phases/phase-5-case-building.md` decisions 2 and 6:** the protocol also
> freezes the real-case rules that Phase 5 would otherwise write after the tag (Delivers 2, last items), the gate gains
> a case mode (Delivers 4, DoD 4), and the real-case search date is set by rule, not chosen.
>
> Written before Phases 0.5 through 3 are built. **Lines marked *(rests on N)* depend on what Phase N builds,
> measures or decides.**

## What this phase is for

**The experiment's one-way door, walked through on purpose.** Everything decided in `planning/07`, as filled in by
Phases 2 to 3, is written into one protocol, reviewed by a reader who did not write it, frozen, committed and tagged
`prereg-v1`. From that moment, the harness accepts an official sweep only when it matches the protocol, and anything
changed later is a new version, reported beside the first and never merged into it (`planning/04` §1.2).

**Nothing official has been seen when this phase ends,** and the record has to prove it to a stranger, not only state
it. That is the job: not only to freeze the design, but to freeze it in a way a hostile reader can verify.

**The test of a good Phase 3.5:** a reader who has never met him can check, from public evidence alone, that the
protocol existed in this exact form before any official run, and that every official result was produced under it.

## What scoping found

1. **The tag must freeze the analysis code, not only the content.** The planning docs freeze the content (dossier,
   scenarios, wordings) and the rules. But if the code that computes verdicts can still change after official results
   are seen, a "bug fix" to scoring is a path to a different answer, and it would leave no trace in the content
   hashes. Run code (calling models, retrying, storing) can need real fixes after the tag; scoring code must not
   change silently. Decision 1.
2. **A git tag on its own is weak evidence.** A tag is a pointer, and it can be deleted and re-created on a different
   commit; the public repo would not obviously show it. The commit timestamp can also be set by its author. What makes
   a pre-registration credible is a timestamp the author cannot change. Decision 2.
3. **Sonnet 4.6's end of life is not sooner than 2027-02-17** (`planning/02` §2.5). The model set is fixed here and
   real cases are run in Phase 5 on that set. If the main model retires before Phase 5 finishes, the real cases
   cannot run on it. That is a schedule constraint, and a consideration in the main-model choice (decision 5).
   *2026-10-05:* with Sonnet 5.5 not awaited, there is no successor to choose; the schedule has to fit Sonnet
   4.6's life.
4. **The protocol is the last design document a second reader can still change for free.** `planning/08`'s
   independent review changed thirty-four things. After the tag, a flaw becomes a new protocol version. Decision 3.
5. **The pilot's repeat count is computed after the tag,** from the pilot's results (`planning/07` §8). The gate must
   accept it without trusting a number typed in. The harness can recompute it from the pilot's raw results with the
   committed rule, so the gate checks the arithmetic instead of the input.

## Delivers

In build order.

1. **The model set fixed** (`planning/05` §3.1, `planning/04` §2.3): the main model (decision 5) and the second model
   family, each with its exact ID, inference profile, region, settings (thinking, sampling defaults recorded), price
   and end-of-life date as known on the day. Before it is fixed, the open check runs: whether a newer non-Anthropic
   model than Nova Pro is available to the account (`planning/09` §5) *(rests on 0.5 for Nova Pro's facts)*. The
   real-case window follows from the set's latest cutoff, and stays at the strict window (first disclosed after June
   2026, preferably from August 1) whatever the set, so a later model can run the same cases (`planning/01` §3.2).
2. **The protocol**, one human-readable document plus one machine-readable file, together holding:
   - the content hashes of the dossier, the four scenarios, all three wording templates (the sealed one included),
     the decision schemas and the prompt structure *(rests on 2 and 2.5)*;
   - how the sealed template was chosen (drawn at random, with the draw's record; Phase 2.5 decision 4) and the
     shuffling of lever and discrete-option order from each run's seed (Phase 2.5 decision 3);
   - the model set and every sampling and thinking setting, including the thinking sub-study's (`planning/07` §7.3);
   - the 16 primary comparisons per model, the thresholds, the interval methods, the three verdicts;
   - the failure and retry rules, the cell exclusion rule, the worst-case bound;
   - the repeat rule and the pilot procedure (development wordings only, two repeats, excluded from results);
   - the robustness rules (wording, positions, the second model, the thinking sub-study, the awareness probe);
   - the descriptive analyses;
   - the simulation results from Phase 3, quoted, with what they mean for each verdict;
   - the real-case procedure: the selection rule with its parameters (decision 4), the channels, the window, the
     search date, the log, the rubric-before-run rule, the foreshadowing check, the recognition probe, and the
     matcher with its threshold and minimum-evidence rule from Phase 3;
   - what is published (`planning/07` §12);
   - **what was seen before the tag**, stated plainly: Phase 0.5's smoke calls on a neutral prompt, Phase 1's
     placeholder sweeps, and Phase 2.5's development runs on the development model, with their change log and their
     reports, which by design showed no allocation by objective (Phase 2.5 decisions 1 and 2) *(rests on 2.5 for the
     record itself)*;
   - **who drafted the instrument:** Claude drafted the dossier, scenarios and wordings from cited sources, and he
     reviewed every line; the main model is from the same family, which the independent reviews and the second model
     family answer (Phase 2 decision 2);
   - the change policy after the tag (decision 6);
   - *(added 2026-10-04, Phase 5 decision 2)* **the real-case build rules:** the dossier template per case type; the
     scenario shape each case type uses (a closure on S3; an AI-attributed workforce change on S1; an invest or retool
     case on S3 with retool or on S4 for a funded program; a restructuring without a facility on S2), chosen by a
     stated rule from the first-disclosure document; the option-economics rule (option figures only from pre-cut-off
     documents, and where an option has none, every option described without figures alike); the replacement rule
     (a case dropped by the recognition probe is replaced by the next eligible candidate of its type, in disclosure
     order); the scaling-factor rule (drawn from a stated range with a private recorded seed, never chosen); the
     uncertain-call rule (each case also matched under every uncertain call's alternative reading, and a match that
     changes reported as "depends on reading"); and the independent reader's role (Phase 5 decision 4);
   - *(added 2026-10-04, Phase 5 decision 6)* **the real-case search date, by rule:** the day after Phase 4's results
     are committed, with the window closing the day before.
3. **The independent review of the protocol** (decision 3), by another vendor's model, with the brief and the raw
   reply kept as records, and each point marked confirmed, partly right or rejected. Changes are made before the tag.
4. **The freeze:** the analysis code's hash recorded in the protocol (decision 1); the gate configured to check the
   content hashes, the protocol file and the analysis code against the tagged commit, and to recompute the repeat count
   from the pilot's raw results when Phase 4 supplies them. *Added 2026-10-04 (Phase 5 decision 2):* **a case mode**,
   which admits a real-case sweep only when that case's dossier, scenario text and rubric hashes sit in a commit that
   predates the sweep and its recognition probe passed, since case content does not exist at the tag.
5. **The tag**, created by him (Claude never runs `git tag`), on the commit that holds the protocol, then made hard to
   move and timestamped from outside (decision 2).
6. **The gate proven both ways** without a model call: a dry run of an official sweep against the tagged content
   passes; the same dry run with one byte of content changed, or with an edited scoring file, is refused with a
   message that names what differs.

## The rules this phase must not break

- **No official model sees real content before the tag.** This phase is the last one in which that rule is absolute.
- **Nothing in the protocol is chosen by looking at a result.** There are no results to look at: only the
  simulations, which are synthetic.
- **Rule zero holds in the protocol.** The real-case procedure names channels, criteria and parameters, never a
  company. Every candidate stays in the private longlist.
- **The protocol does not argue.** It states what is measured, how, and what each verdict would mean, including the
  ones in the Roundtable's favor (`planning/06` §1). A result on either side is publishable.

## Explicitly not in this phase

- **The pilot.** Phase 4, after the tag.
- **Any real-case search or candidate decision.** Phase 5, by the rule fixed here.
- **Public prose about the pre-registration** (a post, a README section). Phase 7, in his words.

## Definition of done

1. **The protocol is complete** against the list in Delivers 2, and he has approved it.
2. **The independent review is done and committed,** and every point is resolved before the tag.
3. **The tag `prereg-v1` exists** on the commit that holds the protocol, is protected from being moved or deleted,
   and has an outside timestamp that matches (decision 2).
4. **The gate passes the tagged content and refuses changed content or changed scoring code**, shown by dry runs that
   call no model. *Added 2026-10-04:* **its case mode is proven both ways** on a synthetic case: admitted with a prior
   rubric commit and a passed probe record; refused without either.
5. **No official result exists anywhere:** the results bucket holds no object under an official prefix, and every
   model call made so far is accounted for by its phase and label.
6. **`make check` and CI are green.**

## Prerequisites

- **Phases 2, 2.5 and 3 complete:** the content final, the change log closed, the engine and simulations done.
- *(rests on 0.5)* **The measured facts about each model** (Sonnet 4.6 and Nova Pro).
- **His OpenRouter balance** for the review.

## Cost

**About $1-2, none of it on AWS.** No model is called on Bedrock. The independent review is one OpenRouter call; the
`planning/08` review of a longer set cost $1.34. The outside timestamp, under decision 2's recommendation, is free.

## The main model

**Sonnet 4.6, fixed 2026-10-05 (his); no choice is made here.** Sonnet 5.5 is no longer awaited. *Was:*
**This is where the choice is made.** If Sonnet 5.5 access has arrived by now, choosing the main model reopens as his
decision (`planning/05` §5.2), with Phase 0.5's measurements of it in hand. If access arrives after the tag, Sonnet 5.5
is its own complete sweep under the same protocol, never merged (`planning/04` §1.9). The considerations are
in decision 5.

## Known risks

- **The tag is created on the wrong commit,** or before a last change lands. Mitigation: the dry-run gate test (DoD 4)
  runs against the tag itself, and the outside timestamp records the commit hash it covers.
- **A flaw is found after the tag.** That is what the change policy is for (decision 6). A new version is honest; a
  quiet edit is the failure this whole phase exists to prevent.
- **The review asks for changes that reopen Phase 2.5's content.** Possible, and acceptable before the tag. Any
  content change goes through Phase 2.5's change log with its reason, then the hashes are recomputed.
- **The schedule meets the model's retirement** (scoping finding 3). Mitigation: the protocol records each model's
  end-of-life date, and Phase 5 is planned against it.

## Decisions for him

All six taken 2026-10-04 (his), as recommended. Five are decided outright; 5 is an agreed procedure, decided in this
phase from the evidence. Each keeps its original framing under *Was:* as the record.

1. **DECIDED 2026-10-04 (his): (a), content, protocol and analysis code.** Run-code fixes after the tag are logged
   with their effect. `planning/05` §3.1 patched. *Was:*
   **What the tag freezes.**
   - (a) **Recommended: the content, the protocol and the analysis code.** A change to the code that computes verdicts,
     intervals or matches after the tag is a new protocol version, and the first version's results are still
     reported. Run code (model calls, retries, storage) can be fixed after the tag, with each change logged and its
     effect on runs stated, because those fixes cannot choose an answer: what was measured is in the raw responses,
     which are kept.
   - (b) The content and the protocol only. Simpler, but a scoring change after results are seen would leave no mark
     in the hashes.
   - (c) The whole repository. Strongest, but any harness bug fix becomes a new protocol version, which would make
     the versioning meaningless.
2. **DECIDED 2026-10-04 (his): (a), tag protection, an independent public archive, and a release.** Checked live in
   the IMPLEMENTATION doc. *Was:*
   **How the tag is made verifiable.**
   - (a) **Recommended:** a **tag protection rule** on GitHub, so `prereg-*` tags cannot be moved or deleted, plus an
     **outside, timestamped copy** of the repository at that commit, made by an independent public archive of source
     code, plus a GitHub release pointing at the tag. The archive and the protection settings are checked live in the
     IMPLEMENTATION doc. Free, no prose to write beyond a release title, and checkable by a stranger without trusting
     him or GitHub alone.
   - (b) Also register the protocol with a research pre-registration service. It is the form researchers recognize,
     but it means an account, forms to fill, and text typed outside the guard's reach.
   - (c) The tag only.
3. **DECIDED 2026-10-04 (his): (a), yes,** by another vendor's model before the tag. *Was:*
   **An independent review of the protocol before the tag.**
   - (a) **Recommended: yes,** by another vendor's model, as `planning/08` was made, given the protocol and the
     simulation results, asked to find what would let a result be bent or a claim overstated. About $1-2.
   - (b) His review and Claude's only.
4. **DECIDED 2026-10-04 (his): (a).** Closure or restructuring *k* = 2, AI-attributed workforce change *k* = 1,
   invest or retool *k* = 2; at most five, at least three, at least one invest or retool; shortfalls reported, never
   filled. `planning/07` §10.0 patched. *Was:*
   **The real-case selection parameters** (`planning/07` §10.0 leaves *k* and the case types to this phase).
   - (a) **Recommended:** three case types: **closure or restructuring** (*k* = 2), **an AI-attributed workforce
     change** (*k* = 1; may be outside manufacturing, labeled, `planning/01` §4.5), and **invest or retool** (*k* =
     2, with the closure-plus-new-facility fallback counting as retool, `planning/01` §4.3). At most five cases, at
     least three, and at least one invest or retool case. A type that yields fewer than *k* is reported as a
     shortfall, never filled by judgment. The search runs once, on a date fixed in the protocol, and candidates are
     taken in order of first disclosure. This matches `planning/07` §13's budget of five cases.
   - (b) Different *k* or types, his choice, before the tag.
5. **CLOSED 2026-10-05 (his): Sonnet 4.6 is the main model; Sonnet 5.5 is not awaited.** *Was:*
   **AGREED 2026-10-04 (his), as a procedure:** if Sonnet 5.5 access has arrived, the main model is chosen in this
   phase from Phase 0.5's measurements, weighing the considerations below. No choice is made before that evidence
   exists. *Was:*
   **The main model, if Sonnet 5.5 access has arrived** (decided here, with Phase 0.5's measurements). No
   recommendation now; the evidence does not exist yet. The considerations, recorded so they are not rediscovered:
   - **For Sonnet 5.5:** newer; about a third cheaper per token (`planning/03` §2.1); a later end of life, which
     protects Phase 5; a June 2026 cutoff, which the strict case window already allows for.
   - **For Sonnet 4.6:** proven on the account; thinking can be turned fully off, which is the official setting
     (`planning/07` §7.3). On Sonnet 5.5 it cannot, so its sweep would use `between_tools`, and the protocol would say
     so.
   - **Both, pre-registered as separate sweeps:** possible, at roughly $13-19 more for the fictional grid alone
     (`planning/07` §13, the lower figure at Sonnet 5.5's price) and more with real cases, which the $60 re-plan point
     would then have to absorb. The cut list (`planning/05` §5.1) still applies.
6. **DECIDED 2026-10-04 (his): (a), errata for changes that alter no computation and no content; everything else is
   `prereg-v2`.** `planning/07` status line patched. *Was:*
   **The change policy after the tag.**
   - (a) **Recommended:** a correction that changes no computation and no content (a typo, a broken link, a clearer
     sentence) is an erratum: allowed, dated, and listed in the protocol's errata section. Anything that changes a
     computation, a hash or a rule is a new version (`prereg-v2`), labeled exploratory where results already exist,
     reported beside v1 and never merged.
   - (b) No errata: every change, however small, is a new version.

## Left for the IMPLEMENTATION doc

*Note 2026-10-09 (his approval of the IMPLEMENTATION doc, all ten decisions as recommended):* decision 1's freeze
extends to the instrument code (prompt, validation, classification) and `experiment.py`; the protocol also freezes the
real-case search queries (decision 6), the scaling factor's range and the coarsening rule (decision 7, §9.3); the
model set is decided by a procedure at build step 9 (decision 2: Sonnet 4.6 main, Haiku 5.5 a third official model if
Bedrock serves it, Nova Pro second family), **with a fallback set if Bedrock is not answering by 2026-10-16 (tentative)** (Haiku
5.5 and `gpt-oss-120b` through OpenRouter from the container, inside his $5 cap; decision 5 as decided). That reopens
"The main model" above under its stated conditions. Cost: $0 cash on the Bedrock path.

The protocol's outline and its machine-readable format. Which files count as analysis code. The gate's checks, one by
one. The archive and the GitHub protection settings, checked live. The reviewer's model and brief. The release's
wording (a title, his). The real-case build rules' exact text (Delivers 2) and the case mode's checks. The order of the commits and of the steps on tag day.
