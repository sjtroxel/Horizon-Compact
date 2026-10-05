# Phase 2.5 — Scenarios and Wordings (v0.2.5)

> **Scope doc.** Written 2026-10-04 from `planning/05` §2, §5 (Phase 2's row) and §7, `planning/00` §5.1-5.2,
> `planning/01` §1, `planning/04` §1.2, §1.4, §1.6 and §1.7, `planning/06` §3, `planning/07` §2.4, §3, §4, §5,
> §7.1-7.2 and §9, `planning/08` §3.1 and §3.3, and `planning/09` A1 and A4. **APPROVED 2026-10-04 (his)**, with all
> six decisions at the end taken as recommended.
>
> **Split out of Phase 2 on 2026-10-04** (his, Phase 2 decision 1).
>
> Written before Phases 0.5 through 2 are built. **Lines marked *(rests on 0.5)*, *(rests on 1)* or *(rests on 2)*
> depend on what those phases measure or build.**

## What this phase is for

**The rest of the instrument:** the four scenarios set in Phase 2's company, the five objectives in three wordings
each, and the proof that a model can read and answer them, made **without anyone learning which way the objectives
push.**

This is where the experiment's credibility is most exposed before the protocol exists. It is the one phase in which
real content meets a model. `planning/05` §2 allows development runs on non-official models, with the rule that
afterwards a wording or scenario may change **only** to fix a format, clarity or neutrality failure, and every change
is logged. This scope doc turns that rule into mechanisms. A rule that depends on not looking needs a design that
does not show.

**The test of a good Phase 2.5:** at the end, the content is ready to freeze; every change since the dossier was
fixed has a logged reason that is not an outcome; and nobody, him or Claude, can say how any objective allocated on
any real scenario, because nobody was shown.

## What scoping found

1. **Checking format does not require seeing allocations, and checking clarity does not require seeing decisions.**
   Whether a run parses is a status. Whether a scenario is clear can be tested by asking the development model
   questions about it with known answers (what is the total, which levers are sources, what does retooling cost),
   with no decision asked for. So the development loop can be built **blind to outcomes** (decision 1). Without that,
   the change-log rule depends on discipline alone.
2. **The obvious reason to tune a scenario is the one the rule forbids.** `planning/07` §3.2 warns that a dossier
   that makes every objective cut, or every objective keep, decides the result by itself. The tempting fix is to
   adjust numbers until the objectives spread out. That is tuning toward a result. `planning/00` §5.1 already names
   "everything cuts" as **the result against the thesis, and published.** Decision 2.
3. **The discrete options have an order, and nothing shuffles it.** `planning/07` §4 shuffles the lever menu from a
   recorded seed. The closure scenario's close, retool or sell, and the R&D scenario's fund or decline, are listed in
   some order too, with their economics described in paragraphs. A model can favor the first or last option. Nothing
   in `planning/07` covers it. Decision 3.
4. **The sealed template is chosen by its author.** `planning/07` §7.1 seals one of the three wording templates.
   If the author picks which one, the choice can carry a preference. Decision 4.
5. **The sealed template is never run, so it is never tested as a prompt.** That is its purpose. The risk is a format
   problem that surfaces first in the official sweep. The mitigation is structural: all three templates differ only
   inside the one objective sentence, in a fixed position (`planning/07` §4), and a text check confirms that.

## Delivers

In build order.

1. **The four scenarios as data**, in `planning/07` §3.2's shapes as patched by `planning/08` §3.3: S1 an allocation
   of AI-released capacity; S2 who bears a shortfall, with payout held fixed; S3 a closure choice plus a workforce
   split, outside the dollar menu, every option equally fundable and every option's workforce outcome stated; S4 a
   fund-or-allocate choice from uncommitted cash. For each scenario: the event text, each option's economics, every
   lever marked source, use or not offered with the reason stated in the prompt, its caps from the dossier, and its
   primary outcome. **Every number is derived from a dossier row** *(rests on 2)* or is a sourced figure or marked
   assumption in the same table format (the 30% automatable share, the 15% revenue fall and the R&D program's odds
   are the likeliest assumptions). The supplier lever is offered in S2 and S4 as `planning/07` §3.2 has it; it is not
   offered in S1, which has only uses, or in S3, which is outside the dollar menu. That closes `planning/09` P7's
   "Phase 2 decides whether it is offered elsewhere."
2. **The objective wordings:** the sentence frame of `planning/00` §5.1 and three templates, each applied to all five
   objectives (A-E), so wording *k* of every objective shares its structure (`planning/07` §7.1). No template adds an
   adjective the frame lacks (`planning/01` §1.4). Then **the sealed template is drawn at random** (decision 4).
3. **The harness extended to the real shapes** *(rests on 1)*: the decision schema for each scenario as data;
   validation per scenario, including caps, S3's workforce split, and S4's optional cuts to fund; the discrete
   options' order shuffled from the run's seed (decision 3); and **a refusal to put the sealed template in any
   decision prompt** before an official sweep, enforced in code, not by memory.
4. **The development model's provider** *(rests on 0.5, decision 8)*: an Ollama provider if Ollama was chosen, or a
   config line if it was a Bedrock model. Development runs use **only** the development model.
5. **Comprehension probes** (decision 1): for each scenario, a set of questions with answer keys about its facts
   and rules, asked of the development model with the scenario and dossier and **no objective and no decision
   requested.** A wrong answer is a clarity finding about the text. Probes are scored automatically against the key.
6. **Format runs:** every scenario, all five objectives, the two development templates, a few repeats each, on the
   development model. **The report shows status counts and failure types only** (decision 1). The text of failed runs
   (no tool call, malformed call, truncation) may be read, because fixing format needs it.
7. **The neutrality review:** `planning/07` §9's ten items, completed for every scenario and every wording (the
   sealed template included, as text), by Claude and then by him; then **a blind second reader**, another vendor's
   model through OpenRouter, as `planning/08` was made, given the scenarios and wordings as text only and asked what
   in them leads. The brief and raw reply are committed as records. Every point is marked confirmed, partly right or
   rejected.
8. **The change log**, committed: one entry per change to any content file after the dossier was fixed, with the
   date, the content hashes before and after, the evidence that prompted it (a probe question, a failure type, a
   checklist item, a reviewer's point), and its reason, which must be **format, clarity, neutrality or a factual
   correction.** "Because of what a run decided" is never a reason, and no entry can cite one, because no report
   shows one.
9. **Planning patches,** applied 2026-10-04 when the decisions were made: `planning/07` §3.2 (S1's retraining cost,
   decision 5), §4 and §7.2 (option order, decision 3), §7.1 (how the sealed template is chosen, decision 4);
   `planning/05` §2 (the development loop built blind, and no change for an outcome reason, decisions 1 and 2). Any
   later finding in this phase that changes `planning/07` gets its own dated patch.

## The rules this phase must not break

- **No official model sees real content in any form before `prereg-v1`.** Not Sonnet 4.6, not Nova Pro, whether as a decision, a probe or a review. Every model call in this phase is to the
  development model or, for the text review, to a non-official reader.
- **Nobody aggregates or reads allocations by objective** (decision 1): not him, not Claude, not a script whose output
  either of them sees. Raw development results are still kept, write-once, under the development prefix
  (`planning/05` §3.1). Whether they are published after the official results is a Phase 6 question.
- **No change for an outcome reason** (decision 2). Numbers come from the dossier and its sources.
- **The sealed template never appears in a decision prompt** until the official sweep. Text review is allowed; a
  run is not, and the harness refuses one.
- **The development cap is $5 per sweep** (`planning/09` §6).
- **Rule zero holds in every scenario:** no real company, ticker, plant location or recognizable event.

## Explicitly not in this phase

- **The protocol, thresholds, repeat counts and the tag.** Phase 3.
- **Any run on an official model**, including the pilot. Phase 4, after the tag.
- **The verdict rule and the matcher's tests.** Phase 3, on synthetic data.
- **The thinking sub-study.** Phase 4.

## Definition of done

1. **The four scenarios exist as data**, and every number in them traces to a dossier row or to a sourced or marked
   assumption.
2. **Three templates are written for all five objectives**, none adds an adjective, a text check shows they differ
   only inside the objective sentence, and **the sealed one was drawn at random**, with the draw recorded.
3. **The comprehension probes pass** for every scenario at a rate set in the IMPLEMENTATION doc, or each failing
   question is traced to a text change in the change log, or to a recorded limit of the development model.
4. **Format runs parse under all five objectives** (`planning/05`) in every scenario on the two development
   templates. Every failure type seen is either fixed by a logged format change or recorded as a limit of the
   development model.
5. **The neutrality checklist is complete** for every scenario and wording, the blind second reader's review is done,
   and both are committed.
6. **The change log is complete,** with a statement, made by him and by Claude, that no allocation by objective was
   seen. That statement can only be honor-based, and it says so. The blind reports are what make it credible.
7. **The harness refuses the sealed template in a decision prompt,** shown by a test.
8. **No official model was called.** `make check` and CI are green, and the phase's spend is measured.

## Prerequisites

- **Phase 2 complete:** the dossier fixed and reviewed.
- *(rests on 0.5)* **The development model named** (Phase 0.5 decision 8), and its tool-call behavior known.
- *(rests on 1)* **The harness from Phase 1:** schema and validation as data, seeded shuffling, per-run storage.
- **His OpenRouter balance** for the blind reader.

## Cost

**A few dollars at most.** If the development model is local, the probes and format runs cost nothing. A cheap
Bedrock model costs cents for a few hundred short calls. The blind reader is one OpenRouter call, about $1.
`planning/05`'s "$5-10" was written before the development model was known and is likely high.

## The main model

The content does not depend on which model is main (Sonnet 4.6, fixed 2026-10-05; Sonnet 5.5 is no longer
awaited). No official model runs in this phase.

## Known risks

- **The development model is weaker than the official ones**, so its format failures and comprehension errors may
  not predict theirs. Mitigation: the Phase 4 pilot measures the official models' format before the grid, and
  `planning/07` §5.2 excludes unreliable cells by a rule fixed in advance.
- **The blind rule leaks a little.** A failed run's text or a probe answer can hint at direction. Accepted: it is
  small, and the change log records what was read.
- **Writing four scenarios at once invites asymmetry**, such as one option described at more length or with more
  uncertainty. Mitigation: checklist items 3, 9 and 10, and the blind reader.
- **A scenario cannot be expressed in its shape without distortion.** That is what `planning/07` §3.3 sends to this
  phase to find out. If found, the shape changes here, with dated patches to `planning/07` and a Phase 1 harness
  amendment, before the freeze (`planning/05` §7).
- **Assumed scenario numbers** (the 30%, the 15%, the R&D odds) draw the "toy" attack. Mitigation: the same
  assumptions table as the dossier, with ranges and reasons.

## Decisions for him

All six taken 2026-10-04 (his), as recommended. Each keeps its original framing under *Was:* as the record.

1. **DECIDED 2026-10-04 (his): (a), blind to outcomes.** `planning/05` §2 patched. *Was:*
   **How the development loop sees results.**
   - (a) **Recommended: blind to outcomes.** Format is judged from status counts; clarity from comprehension probes
     with answer keys; neutrality from the checklist and the blind reader. Nobody aggregates or reads allocations by
     objective, and the reports are built so they cannot show them. The text of failed runs may be read. This turns
     `planning/05` §2's rule from a promise into a design.
   - (b) Full development reports, including allocations, relying on the change-log rule alone. More information for
     clarity work, but every later wording change then has to be defended against "you saw which way it went."
2. **DECIDED 2026-10-04 (his): (a), a degenerate scenario is a result, not a defect.** `planning/05` §2 patched.
   *Was:*
   **What happens if a scenario looks degenerate**, for example every objective cutting.
   - (a) **Recommended: nothing. That is a result, not a defect.** Numbers come from the dossier and its sources,
     and are never changed for their effect on decisions. `planning/00` §5.1 names "everything cuts" as the result
     against the thesis, to be published. Under decision 1 (a) it would not even be visible before the official
     sweep.
   - (b) Allow a change when development runs pooled across all objectives sit at a bound, judged without a
     per-objective breakdown and logged. It protects sensitivity, but it is tuning on outcomes, on a model that is not
     the official one.
3. **DECIDED 2026-10-04 (his): (a), shuffled per run from the seed.** `planning/07` §4 and §7.2 patched. *Was:*
   **The discrete options' order.**
   - (a) **Recommended: shuffled per run from the recorded seed**, both the list of choices and the paragraphs that
     describe each option's economics, so the order cannot favor an option and any run can be reproduced exactly.
     Position is recorded and reported, as for levers (`planning/07` §7.2). Needs dated patches to `planning/07` §4
     and §7.2.
   - (b) A fixed order, stated on the methods page.
4. **DECIDED 2026-10-04 (his): (a), drawn at random after the neutrality review.** `planning/07` §7.1 patched.
   *Was:*
   **Which template is sealed.**
   - (a) **Recommended: drawn at random** after all three are written and have passed the neutrality review, using a
     seed fixed before the draw (for example, the hash of the commit that holds all three). The draw is recorded, so
     no one chose the template that would never be seen.
   - (b) Chosen by him.
5. **DECIDED 2026-10-04 (his): (a), stated separately as a one-time cost from cash, with its payback.**
   `planning/07` §3.2 patched. *Was:*
   **The retraining cost in S1** (`planning/07` §3.2 leaves it to Phase 2).
   - (a) **Recommended: stated separately,** as a one-time cost paid from existing cash, with its payback period, so
     S1's table stays in annual payroll dollars and the share kept stays a clean ratio. The cost is a fact in the
     scenario, stated in numbers like every other option's economics.
   - (b) Drawn from the freed amount, so keeping people costs part of what keeping them frees. It puts the cost inside
     the decision, but mixes a one-time cost into an annual table.
6. **DECIDED 2026-10-04 (his): (a), another vendor's model through OpenRouter,** chosen live. *Was:*
   **The blind second reader.**
   - (a) **Recommended: another vendor's model through OpenRouter**, the method `planning/08` used, with the brief
     and raw reply kept as records. Chosen live, for being current and from a vendor that makes none of the models
     under test.
   - (b) Claude in a fresh session. Cheaper, but it is the same model family as the author and the main subject.

## Left for the IMPLEMENTATION doc

Each scenario's text and numbers, and its decision schema. The three templates, word for word. The text check on
templates. The probe questions and answer keys, and the pass rate. The number of format runs. The report formats,
built so they cannot show allocations by objective. The change log's format. The reader's model and brief. The
seed and method for the sealed draw. The harness changes, file by file. The order of the commits.
