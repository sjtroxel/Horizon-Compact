# Phase 3 — Scoring and Simulation (v0.3)

> **Scope doc.** Written 2026-10-04 from `planning/05` §2, §3.1 and §5 (Phase 3's row), `planning/07` §5.2, §6,
> §7.1, §8, §10.4, §12 and §14.5-14.6, `planning/08` §3.4-3.5 and §4.5, `planning/04` §1.2 and §1.5, and
> `planning/09` A5. **APPROVED 2026-10-04 (his)**, with both decisions at the end taken as recommended.
>
> **Split 2026-10-04 (his, decision 1):** `planning/05`'s Phase 3 is now two phases. This doc covers **the
> statistics, built and proven on synthetic data**. **Phase 3.5 `preregistration`**
> (`docs/phases/phase-3.5-preregistration.md`) assembles the protocol from it, has it reviewed, freezes it and tags
> it.
>
> Written before Phases 0.5 through 2.5 are built. **Lines marked *(rests on N)* depend on what Phase N builds or
> decides.** Phase 2 and 2.5's decisions were made 2026-10-04 (his), after this doc was first drafted; it was
> adjusted to them the same day.

## What this phase is for

**The machinery that turns runs into verdicts, proven before it ever sees a real run.** The scorer from Phase 1.5
becomes the full analysis that `planning/07` specifies: the three verdicts, their intervals, the robustness rules,
the failure handling, the descriptive analyses, and the real-case matcher. **Every part is tested on synthetic data
with a known answer, and nothing else.** No model is called.

Its other output is numbers that the protocol needs and that can only come from simulation: how often the verdict rule
finds a real difference at the design size, how often it invents one, whether "no split" can actually be earned, and
where the matcher's no-match threshold sits. `planning/09` A5 assigns all of this to the time before the tag, because
it is the last time a fix costs nothing.

**The test of a good Phase 3:** given synthetic results where the truth is known, the analysis says the truth at the
rates the simulation reports, and someone else can re-run every number from the committed code and seeds.

## What scoping found

1. **The simulations feed the protocol, so they come first.** The power at 1.5 times the threshold, the false-split
   rate, the reachability of "no split" (`planning/07` §8 (b)) and the matcher's no-match threshold and
   minimum-evidence rule (`planning/07` §10.4) are all *outputs* of this phase and *inputs* to the protocol. That is
   the reason for the split (decision 1).
2. **"Synthetic" has to mean what it says.** The synthetic data is generated from stated distributions with seeds.
   It never borrows from a development run, a Phase 1 placeholder sweep, or the dossier's numbers in a way that
   encodes an expected result. Its parameters span the plausible range (spreads from small to `planning/07` §8's
   worst case, true differences from zero to well above the threshold) rather than guessing where the real answer
   lies.
3. **The all-agree case is likely, not rare.** `planning/08` §3.4c: models at default settings often repeat the same
   discrete choice. The tests treat "every run under both objectives made the same choice" as a main case, with the
   Newcombe interval checked to stay honest there.
4. **The interval methods should be standard and verifiable,** not hand-written. A reader who doubts the result
   should be able to point at a well-known implementation, and the tests should check it against published worked
   examples. Decision 2.

## Delivers

In build order.

1. **The verdict engine:** for each primary comparison (`planning/07` §6.1), the difference, its 99.7% interval
   (Bonferroni over 16 per model, §6.3), and exactly one of split, no split or inconclusive (§6.2). Shares use a
   stratified bootstrap by wording with at least 10,000 resamples; choice rates use Newcombe's score interval
   (decision 2).
2. **The failure rules as code** (`planning/07` §5.2): per-cell failure and refusal rates; the 10% exclusion of
   unreliable cells; first-attempt beside final results; the worst-case bound that turns a split inconclusive when
   failed runs could overturn it; "among valid runs" labeling.
3. **The robustness rules:** the per-wording direction check that marks a split as wording-sensitive (§7.1); the
   sealed-wording result reported separately; position effects for levers and for the discrete options in S3
   and S4, whose order is shuffled per run (Phase 2.5 decision 3; `planning/07` §4 and §7.2).
4. **The descriptive analyses** (`planning/07` §6.5): the full allocation by objective, every lever's mean and spread,
   the summary groups, where the money went, S3's three-way split and S4's funding sources, E's distance to each
   objective. Fixed in code, so they cannot be chosen after the results are seen.
5. **The repeat rule as code** (`planning/07` §8): pooled spread for shares, the cap for choice rates, floor 6, cap 20,
   both (a) and (b), and the achieved precision reported when the cap binds. Phase 4's pilot feeds it.
6. **The matcher** (`planning/07` §10.4): per-run distance on the lever-level vector over observable dimensions, then
   averaged; the tie rule from the gap's own bootstrap spread; the minimum-evidence rule; and the no-match threshold,
   **set from synthetic cases** (identical, opposite, same choice with opposite money, sparse disclosures).
7. **The simulations,** with seeds committed and results written to a file the protocol will quote:
   - power to declare a split at 1.5 times the threshold, across spreads and repeat counts;
   - the false-split rate when the true difference is zero, which must stay near the 5% family-wise target;
   - "no split" earned at the rate rule (b) promises when the true difference is near zero;
   - the all-agree case, for both interval methods;
   - the matcher's behavior on the synthetic cases, and the threshold that separates "matched" from "no good match."
8. **The scorer extended,** so Phase 1.5's static JSON gains the verdicts, intervals and descriptive results, still
   with per-run values, under a new schema version *(rests on 1.5)*.

## The rules this phase must not break

- **No model is called.** Not the official models, not the development model. Everything runs on synthetic data.
- **Synthetic data encodes no expected answer** (scoping finding 2).
- **Every number is reproducible** from committed code and seeds.
- **The rules being implemented are `planning/07`'s.** Where implementation shows a rule cannot work as written, the
  fix is a dated patch to `planning/07` with the evidence, made here, before the tag. Never after.

## Explicitly not in this phase

- **The protocol document, its review, the freeze and the tag.** Phase 3.5.
- **The pilot and every official run.** Phase 4.
- **Real cases, rubrics and the selection log.** Phase 5. The matcher is built and calibrated here on synthetic cases
  only.
- **The explorer's views of the verdicts.** Phase 6.

## Definition of done

1. **Each interval method agrees with published worked examples** to stated precision, and with the library it comes
   from (decision 2).
2. **The verdict engine returns the known answer** on synthetic sets built to be a split, a no split and an
   inconclusive, for shares and for choice rates, including the all-agree case.
3. **The simulations are recorded:** power at 1.5 times the threshold, the false-split rate, the reachability of "no
   split," each across the stated range of spreads and repeat counts. **If the false-split rate exceeds the target, or
   "no split" cannot be reached where rule (b) says it can, the rule is fixed by a dated patch to `planning/07` before
   Phase 3.5 begins.**
4. **The matcher's no-match threshold and minimum-evidence rule are set** from the synthetic cases, with the evidence
   recorded.
5. **The failure rules, the robustness rules and the descriptive analyses each have tests.**
6. **No model was called.** `make check` and CI are green.

## Prerequisites

- *(rests on 1.5)* **The scorer and the static JSON schema** from Phase 1.5.
- *(rests on 2.5)* **The final shapes of the four scenarios' decisions**, so the engine reads the real schema. The
  synthetic data follows those shapes without using their content.
- **Nothing from AWS.**

## Cost

**$0.** No model call, no AWS resource. Simulations run on the laptop.

## The main model

Nothing here depends on which model is main. The engine is per model, and analysis is always per model, never pooled
(`planning/07` §1).

## Known risks

- **The simulation shows the design is weaker than hoped**, for example that choice rates near 50% rarely reach a
  verdict at the cap. That is the purpose of running it now. The response is stated in the protocol (the achieved
  precision on the methods page, `planning/07` §8), or a dated patch to the rule, before the tag.
- **A subtle bug makes the engine agree with itself and not with the truth.** Mitigation: known-answer tests built
  independently of the engine, published worked examples for the intervals, and the library cross-check.
- **Scope creep into "better statistics."** `planning/07` §6.3 chose Bonferroni on purpose: it can be explained in
  one sentence. A more powerful method found here is noted for a later protocol version, not swapped in.

## Decisions for him

Both taken 2026-10-04 (his), as recommended. Each keeps its original framing under *Was:* as the record.

1. **DECIDED 2026-10-04 (his): (a), split.** This doc is Phase 3; Phase 3.5 is `preregistration`. `planning/05`
   status line patched. *Was:*
   **One phase or two.**
   - (a) **Recommended:** split into **Phase 3 `scoring-and-simulation`** (v0.3, this doc) and **Phase 3.5
     `preregistration`** (v0.3.5). The simulations produce numbers the protocol must quote, and the tag is the
     experiment's one-way door, which deserves its own IMPLEMENTATION doc written with those numbers in hand.
   - (b) One phase, as `planning/05` has it.
2. **DECIDED 2026-10-04 (his): (a), established library implementations,** each tested against published worked
   examples. *Was:*
   **Where the interval methods come from.**
   - (a) **Recommended: established library implementations**, each tested against published worked examples:
     Newcombe's interval from a widely used statistics package, and the bootstrap from the scientific Python stack
     or a short, tested routine where the stratified design needs it. The libraries and their versions are checked
     live in the IMPLEMENTATION doc. A doubting reader can then check the method, not only this project's code.
   - (b) Written by hand from the papers, with the same tests. No dependency, but every line is this project's to
     defend.

## Left for the IMPLEMENTATION doc

The synthetic generators and their parameter ranges. The libraries and versions, checked live, and the worked
examples they are tested against. The number of simulation replicates. The matcher's synthetic case set, case by case.
The file the simulation results are written to. The JSON schema's new version. The order of the commits.
