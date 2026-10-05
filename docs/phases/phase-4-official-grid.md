# Phase 4 — The Official Grid (v0.4)

> **Scope doc.** Written 2026-10-04 from `planning/05` §2, §3.1, §5 (Phase 4's row), §5.1 and §5.2, `planning/07`
> §5, §7, §8, §11, §12 and §13, `planning/04` §1.2, §1.5, §1.9, §3.1 and §3.4, `planning/03` §6, and `planning/09`
> §6 item 2. **APPROVED 2026-10-04 (his)**, with all six decisions at the end taken as recommended.
>
> Written before Phases 0.5 through 3.5 are built. **Lines marked *(rests on N)* depend on what Phase N builds,
> measures or decides.** Phase 0.5's pre-build checks were run 2026-10-04 (`KNOWN-GAPS.md`); the ones this doc rests
> on are the quota, the price and the refusal mapping, which the build measures.

## What this phase is for

**The experiment runs for the first time.** Everything before this phase was built so that this one can be boring:
the protocol is frozen and tagged, the gate checks it, the harness paces, caps, stores and resumes, and the analysis
code is frozen with it. This phase runs the pilot, uses it to set the repeat count by the committed rule, then runs
the full grid on Sonnet 4.6, the pre-registered robustness studies, and the grid on Nova Pro, and measures what it all
cost.

**Almost nothing is built.** The work is conduct: who sees what, when, and in what order. After the tag, the only
choices left are operational ones (when to stop, what to cut, how to fix a broken run). Each one can still be bent by
what has been seen. This doc exists to take those choices away, or to make them before anything is seen.

**The test of a good Phase 4:** a stranger can check, from the public record, that every official result came from the
tagged protocol, that the run set was fixed before any official result existed, and that no decision made during the
phase could have been steered by a result.

## What scoping found

1. **The $25 official cap does not fit "one sweep per model" as written.** `planning/07` §11 says one official sweep
   per model per protocol version. If that sweep holds the grid (about $19 at the repeat cap, before retries), the
   thinking sub-study (about $5) and the awareness probe, it trips the $25 cap (`planning/09` §6 item 2) before it ends.
   §11's intent is that nothing is run twice and nothing outside the protocol is merged, not that every study shares
   one budget. Decision 4.
2. **The order of runs is unspecified, and it matters.** Run cell by cell, a sweep stopped by its cap or a fault
   leaves some scenarios complete and others empty, and each objective is tied to a stretch of time on the model's
   servers, which can drift over a two-hour sweep. Decision 3.
3. **The $60 re-plan point would arrive after official results are seen.** `planning/04` §3.4 has him stop at $60
   of cumulative spend and decide what to cut. `planning/05` §5 expects it during Phase 5, if at all, after the grid's
   verdicts exist. A cut chosen then (drop Nova Pro, drop a wording) is chosen by someone who knows the answers. The pilot
   measures cost per decision and sets the repeat count, which together project the rest of v1's spend before the
   grid runs. Decision 2.
4. **The pilot runs the real scenarios on the official model, and nothing says who reads what.** The rule needs one
   number per scenario from it: the pooled spread of the primary outcome. Read in full, it also shows which way each
   objective pushes, on two wordings, before the official grid. Nothing in the protocol can change after the tag, but
   run code can (Phase 3.5 decision 1), and so can the cut list. Decision 1.
5. **The official grid is the first time the sealed template reaches any model** (`planning/07` §7.1). That can be
   shown from the record rather than asserted: no earlier object in the results bucket carries the sealed template's
   hash.

## Delivers

In order. Each step starts only when the one before it is done.

1. **The pilot** (`planning/07` §8): all four scenarios, five objectives, the two development wordings only, 2
   repeats per cell, 80 decisions on Sonnet 4.6, through the gate against the tagged content, labeled pilot and stored
   under its own prefix, **excluded from every result**. Its report shows only what decision 1 allows.
2. **The repeat count, recomputed by the gate** from the pilot's raw results with the committed rule (Phase 3.5,
   Delivers 4): pooled spread per share scenario, rules (a) and (b), floor 6, cap 20, choice rates to the cap. The
   achieved precision is recorded wherever the cap binds.
3. **The projection and the re-plan check** (decision 2): measured cost per decision from the pilot, times the run
   set now fixed, plus Phase 5's estimate, against the $60 re-plan point, the $80 ceiling, **and the credit balance
   he reads from the console that day** (Billing, Credits; free to view). The credits are shared with Musical
   Mycelium (`planning/03` §1), so the balance, not the ceiling, is the line past which spend becomes cash. If the
   projection crosses $60, or would leave less than Musical Mycelium's reserve in the pot, he decides what to cut by the pre-registered order (`planning/05` §5.1) **now, before the grid**. The decision and its
   numbers are committed.
4. **The official grid on Sonnet 4.6:** four scenarios, five objectives, three wordings (the sealed one included),
   the computed repeats, thinking off (`planning/07` §7.3), in one shuffled order (decision 3). Container run by image
   digest, under the official prefix, its own sweep and manifest (decision 4).
5. **The thinking sub-study** (`planning/07` §7.3): S1, the sealed wording, five objectives, adaptive thinking at
   effort `high`, the grid's repeat count for S1, thinking tokens recorded per run. Its own sweep.
6. **The awareness probe** (`planning/07` §7.5): 15 calls per model, after the grid. Its own sweep.
7. **The grid and the probe on Nova Pro**, unless decision 2's check cut it: the same run set at its own default
   temperature (`planning/07` §2.3), analyzed separately. Nova Pro's quota is separate (25 a minute), so it may run
   beside a Sonnet sweep *(rests on 0.5 for its availability on the account)*.
8. **The analysis, run once per model with the frozen code** (Phase 3.5 decision 1): the verdicts, intervals,
   robustness results, descriptive analyses and failure tables, written to the published JSON (decision 5).
9. **The measured cost**, from the sweep manifests and then from the bill, replacing `planning/03`'s and
   `planning/07` §13's estimates by a dated patch; the ROADMAP's cost column updated.
10. **The record checks:** every official object traces to the tagged commit's content hashes and to one image
    digest; no object before the grid carries the sealed template's hash (scoping finding 5); every run-code change
    made after the tag is in the log with its effect stated.

## The rules this phase must not break

- **Nothing outside the protocol is official.** A sweep the gate refuses is not run under another label. A study not
  in the protocol is exploratory, stored under its own prefix, and never merged (`planning/07` §11).
- **The run set is fixed before the first official run** (Delivers 2 and 3) and never changed by what the runs show.
  A cap stop or a fault changes *when* runs happen, never *which*; resuming fills missing `run_id`s and re-runs
  nothing that has a final result.
- **A model's failures are outcomes.** A high refusal or failure rate never stops, restarts or re-runs a sweep. Only an
  infrastructure fault stops one (throttling past backoff, a crash, a broken credential), and the fix is resumption.
- **Run-code fixes are logged with their effect** (Phase 3.5 decision 1). Analysis code is not touched: a change there
  is `prereg-v2`, reported beside v1.
- **No model ID changes mid-grid** (`planning/04` §1.9). If the model is withdrawn mid-sweep, the partial sweep is
  reported as partial, never completed on another model.
- **Every result is published, whichever way it falls** (`planning/06` §1). A "no split" on C vs D, the result in the
  Roundtable's favor, is published with the same prominence as a split.
- **Rule zero holds.** No real company appears in any prompt, memo or record of this phase; the content is the
  fictional company's.

## Explicitly not in this phase

- **Real cases, their search, rubrics and runs.** Phase 5, by the rule frozen in Phase 3.5.
- **The explorer's views of the results and the methods page.** Phase 6. This phase produces the data they show.
- **Any public prose about the results** (a post, a README section, a thread). Phase 7, in his words. Decision 5 is
  about publishing data, not commentary.
- **Sonnet 5.5.** Not awaited after 2026-10-05 (Phase 3.5 decision 5, closed).
- **Re-running anything** that has a final result, for any reason.

## Definition of done

1. **The pilot has run and is excluded:** its objects sit under the pilot prefix, and no published number uses them.
2. **The repeat count was computed by the gate from the pilot's raw results,** and the projection and re-plan check
   were committed before the grid's first run (decision 2).
3. **The full grid has run under the protocol on Sonnet 4.6,** with run counts, failure and refusal rates per cell,
   and first-attempt beside final results recorded (`planning/07` §5.2, §12).
4. **The thinking sub-study and the awareness probe have run,** or were cut by decision 2's check with the reason
   recorded.
5. **Nova Pro's grid has run,** or was cut by the same check with the reason recorded.
6. **The frozen analysis has produced every verdict,** and the published JSON is committed (decision 5).
7. **The record checks pass** (Delivers 10).
8. **Measured cost replaces the estimates,** from the manifests and confirmed against the bill, and the $60 re-plan
   point has been checked against measured spend.
9. **`make check` and CI are green.**

## Prerequisites

- **Phase 3.5 complete:** the tag, the gate proven both ways, the model set fixed.
- *(rests on 1)* The rate limiter, the two-part spend cap with his override flag, the official prefix, write-once
  storage and resumption, proven on the placeholder.
- *(rests on 1.5)* The scorer and the published JSON schema; *(rests on 3)* the verdict engine and the repeat rule as
  code.
- *(rests on 0.5)* Sonnet 4.6's requests-per-minute quota, re-read live (10 a minute on 2026-10-03, `planning/04`
  §3.1); the refusal stop reason's Converse form (`content_filtered`, provisionally, per `KNOWN-GAPS.md`); the price
  file, checked against the AWS Price List.

## Cost

**About $20-30**, most of it on Sonnet 4.6 (`planning/07` §13; ROADMAP). At the repeat cap: the pilot about $1.50,
the grid about $19 before retries, the thinking sub-study about $5, the probes under $1, Nova Pro's grid about $5. At
10 repeats, the grid and the sub-study fall by about half.

**Where cumulative spend stands:** the $80 ceiling counts AWS spend; OpenRouter review calls are recorded in the cost
ledger beside it (Phase 2 scope doc, Cost). The scope docs for Phases 0.5 to 3.5 put their AWS spend at a few dollars
in all (Phase 2.5's development runs revised `planning/05`'s "$5-10" down). So this phase ends near $25-35, and Phase
5's $20-25 and Phase 6's under $2 take v1 to about $45-60. **Whether the projection in Delivers 3 crosses $60 depends
mostly on the repeat count and the retry rate,** which is why it is made from the pilot's measurements and not from
these estimates.

**Time:** at 10 requests a minute, the Sonnet grid takes at least about 2 hours at the cap; the pilot about 8 minutes;
the sub-study about 10. Nova Pro at 25 a minute takes under an hour.

## The main model

**Sonnet 4.6, fixed 2026-10-05 (his)**, and named in the protocol. Not reopened here.

## Known risks

- **The quota or throttling makes the grid slow** (`planning/04` §3.1). Mitigation: one task per model, pacing below
  quota, backoff; a two-to-four-hour sweep is acceptable for v1.
- **The cap stops a sweep partway.** Mitigation: decision 4 sizes each sweep under $25 with room for retries, and
  decision 3's order means a stopped sweep is a balanced subset, not a lopsided one. Continuing past the cap takes his
  override flag, recorded in the manifest.
- **A harness bug surfaces only on real content.** The placeholder and development runs exercised every path, but the
  sealed wording and the official model meet for the first time here. Mitigation: run code may be fixed and logged;
  runs already completed are kept; a run whose result the bug changed is reported, never silently re-run.
- **The model is updated or withdrawn mid-grid** (`planning/04` §1.9). Mitigation: the model ID is pinned per sweep;
  the run dates are published; a partial sweep is reported as partial.
- **A result tempts a change.** That is the risk the whole design is built around. Mitigation: decisions 1 and 2 put
  every remaining choice before the result, and the analysis code is frozen.

## Decisions for him

All six taken 2026-10-04 (his), as recommended. Each keeps its original framing under *Was:* as the record.

1. **DECIDED 2026-10-04 (his): (a), blind to objective.** *Was:*
   **What the pilot and running sweeps show before the grid is complete.**
   - (a) **Recommended: only what the rules need, blind to objective.** The pilot report shows, per scenario, the
     pooled spread, the repeat count, failure and refusal counts pooled across objectives, and the cost. `hc sweep
     status` shows counts by status, never allocations. Nobody reads an allocation by objective until the grid is
     complete and the frozen analysis runs. This is Phase 2.5's blind development loop (decisions 1-2) carried
     forward: the pilot answers "how noisy is it" without answering "which way does it go." The raw objects stay in
     S3, unhidden, and are published with everything else; the rule is about what the reports display, not about
     destroying anything.
   - (b) Show the pilot in full. Simpler, and nothing frozen can change. But run-code fixes and the cut list can, and
     both would then be chosen by someone who has seen the direction.
2. **DECIDED 2026-10-04 (his): (a), projected from the pilot, before the grid.** `planning/04` §3.4 patched. *Was:*
   **When the $60 re-plan point is checked.**
   - (a) **Recommended: projected from the pilot, before the grid.** Measured cost per decision times the fixed run set,
     plus Phase 5's estimate. If the projection crosses $60, he decides what to cut, in the pre-registered order
     (`planning/05` §5.1: Nova Pro first), before any official result exists, and the decision is committed. The
     measured check at $60 still happens when actual spend reaches it, against the projection. Cost: one decision made
     on an estimate rather than on the bill.
   - (b) As `planning/04` §3.4 has it: when measured spend reaches $60, probably in Phase 5, after the grid's verdicts
     are known.
3. **DECIDED 2026-10-04 (his): (a), one shuffled order from a recorded seed.** `planning/07` §11 patched. *Was:*
   **The order of runs within a sweep.**
   - (a) **Recommended: one shuffled order across every cell, from a seed recorded in the manifest.** A sweep stopped
     early is a balanced subset of the grid, and server-side drift over a two-hour sweep spreads across objectives
     instead of landing on one. The order is fixed with the run set (Delivers 2), so it cannot be chosen after a
     result.
   - (b) Cell by cell, scenario by scenario. Easier to follow in a log; a stop leaves gaps in whole cells.
4. **DECIDED 2026-10-04 (his): (a), one sweep per pre-registered study per model.** `planning/07` §11 patched.
   *Was:* **What one official sweep is.**
   - (a) **Recommended: one sweep per pre-registered study per model:** the grid, the thinking sub-study and the
     awareness probe are each their own sweep, with their own manifest and their own $25 cap. `planning/07` §11's
     rule keeps its meaning: each is run once per protocol version, nothing is re-run, and nothing outside the
     protocol is merged. Needs a dated patch to `planning/07` §11's wording, made before the tag (Phase 3.5 assembles
     the protocol from it).
   - (b) One sweep per model holding all three, as §11 reads literally, with its cap raised to fit by his override
     flag each time.
5. **DECIDED 2026-10-04 (his): (a), committed as data at the end of this phase.** *Was:*
   **When the results are published.**
   - (a) **Recommended: committed to the public repo at the end of this phase,** as data with no commentary: the
     published JSON (verdicts, intervals, per-run values) and the run counts, before Phase 5 starts. A result
     timestamped on the record before the real cases run cannot later be quietly reshaped, and it closes the option of
     not publishing (`planning/06` §1). The raw responses follow `planning/07` §12. His prose comes in Phase 7.
   - (b) Held until Phase 6 or 7 and published with the explorer and the write-up. One reveal, but a stretch of
     weeks in which the results exist privately.
6. **DECIDED 2026-10-04 (his): (a), one phase.** *Was:*
   **One phase or two.**
   - (a) **Recommended: one phase.** Unlike Phases 1-3, nothing new is built: the pilot, the grid, the studies and
     Nova Pro are the same harness with different run sets, and the IMPLEMENTATION doc is mostly an ordered runbook.
     Nova Pro, first on the cut list, is cut by decision 2's check, not by a phase boundary.
   - (b) Split into **4** (Sonnet 4.6: pilot, grid, sub-study, probe) and **4.5** (Nova Pro), so the second model
     family has its own scope and done-when.

## Left for the IMPLEMENTATION doc

The runbook, step by step, with the exact commands he types and what to look for after each. The pilot report's
fields, field by field. The projection's arithmetic and where it is committed. The shuffled order's seed source. Each
sweep's cap estimate with its retry allowance. Whether Nova Pro runs beside a Sonnet sweep or after it. The abort
conditions for an infrastructure fault, by name. The published JSON's location and the raw responses' publication
form (`planning/07` §12). The run-code change log's format. The record checks as commands. The dated patches to
`planning/03` and `planning/07` §13 with measured cost.
