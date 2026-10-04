# Phase 5.5 — Case Runs (v0.5.5)

> **Scope doc.** Written 2026-10-04 from `planning/00` §5.4, `planning/06` §2.1, §6.1 and §6.3, `planning/07`
> §6.4, §10.3-10.4 and §12, and the Phase 4 and Phase 5 scope docs. **APPROVED 2026-10-04 (his)** with Phase 5: its
> rules come from Phase 5's decisions 1, 2 and 5 and Phase 4's decisions 1 and 3-5, all approved that day. It adds
> no decision of its own.
>
> **Split out of Phase 5 on 2026-10-04** (his, Phase 5 decision 1). Phase 5's scoping findings cover this half too
> (`docs/phases/phase-5-case-building.md`).
>
> Written before Phases 0.5 through 5 are built. **Lines marked *(rests on N)* depend on what Phase N builds,
> measures or decides.**
>
> **Rule zero governs every line of this phase**, as in Phase 5: no company, candidate or identifier, anywhere public.

## What this phase is for

**The frozen cases, run and matched.** Phase 5 built every case and froze it: dossier, scenario text, rubric, probe.
This phase runs each case under the five objectives, three wordings and the fixed model set, matches each company's
decision to the objective whose runs it most closely resembled, and publishes the results by case type.

**Little new code is built.** The harness, the gate, the matcher and the scorer exist. This phase's IMPLEMENTATION doc
is mostly the ordered steps and commands, as Phase 4's is. Its scope is conduct: nothing seen while the cases run can
change a case, a rubric or a rule, and nothing published identifies a company.

**The test of a good Phase 5.5:** every published match traces to a case frozen before its first run, through the gate,
by the frozen matcher; every public word about a case is coarse enough that a search does not find the company.

## Delivers

In order.

1. **The credit check before the runs:** the balance read from the console that day, against the projection Phase 5
   made (Phase 5, Delivers 1). If the measured spend since has drifted past the projection, he decides before any
   run, in the pre-registered cut order (`planning/05` §5.1: the fifth case, then the fourth).
2. **The case runs:** each case its own sweep per model (Phase 4 decision 4), five objectives, three wordings, 10
   repeats (`planning/07` §10.4), in one shuffled order (Phase 4 decision 3), thinking off, through the **gate's case
   mode** (Phase 5 decision 2): admitted only when the case's dossier, scenario text and rubric hashes sit in a commit
   that predates the sweep and its recognition probe passed *(rests on 3.5)*. Sweep status shows counts by status,
   never allocations, until every case's sweeps are complete (Phase 4 decision 1).
3. **The matching, by the frozen matcher** (`planning/07` §10.4): for each case and model, all five distances with
   their spreads, the nearest objective, ties and "no good match" as such, "not enough disclosed to match" where the
   minimum-evidence rule applies, and **the match under each uncertain call's alternative reading**, with "depends on
   reading" where it changes (Phase 5 decision 2) *(rests on 3)*.
4. **The name scan on every real-case memo** (`planning/07` §12): the private term file, which holds each case's
   identifiers since Phase 5, plus a general check for any company name. A memo that names one is held back and
   counted, never edited.
5. **The re-identification check on each anonymized dossier** (Phase 5 decision 5): its distinctive figures and
   description searched against public sources, including the structured financial data it was built from. Pass:
   publishable. Fail: withheld, with the reason recorded for the methods page.
6. **The coarse public descriptions** (`planning/06` §6.3): sector, decision type, scale band, half-year, no place
   finer than the country; each searched as written, with variations, before it is published.
7. **Publication as data** (Phase 4 decision 5, Phase 5 decision 5), committed at the end of this phase: each case's
   results by case type, its observed and excluded dimensions (`planning/07` §10.2), its probe results, the dossiers
   that passed decision 5's check, the memos that passed the name scan, and the public selection log. No commentary.
8. **Measured cost**, from the manifests and the bill, recorded against the projection.

## The rules this phase must not break

- **A frozen case is not changed by what its runs show.** A case changes only by the protocol's own rules, all of
  which act before its first run.
- **A model's failures are outcomes** (Phase 4): a refusal or format failure never stops or re-runs a case sweep. Only
  an infrastructure fault stops one, and the fix is resumption.
- **"Most closely matched,"** always; ties and "no good match" shown as such, never forced to a winner
  (`planning/00` §5.4). The cases never join the sixteen comparisons (`planning/07` §6.4).
- **Nothing about a company's motives.** Matches describe what a company did against what runs did, never why
  (`planning/06` §2.1).
- **Rule zero:** no identifier in any tracked file, commit, published memo, description or dossier. A check that
  fails holds the item back; it is never "fixed" by guessing.

## Explicitly not in this phase

- **Building, coarsening or replacing a case** after its first run. Phase 5's rules, before the freeze.
- **The explorer's real-case view and the methods page.** Phase 6.
- **Public prose about any case.** Phase 7, in his words.
- **Running a case on a model outside the fixed set.** A later phase, with its own window check (`planning/04` §2.3).

## Definition of done

1. **Every frozen case has run on every model in the set** through the gate's case mode, or was cut by Delivers 1's
   check with the reason recorded; at least three cases, including an invest or retool case, unless Phase 5 reported
   a shortfall.
2. **Every case is matched,** with its distances, spreads, the alternative-reading matches and its observed and
   excluded dimensions recorded.
3. **Every real-case memo passed the name scan** or was held back and counted.
4. **Every dossier passed the re-identification check or is withheld with its reason;** every public description
   passed the search check.
5. **The results are committed as data** (Delivers 7), and the guard passed every commit.
6. **Measured cost is recorded.** `make check` and CI are green.

## Prerequisites

- **Phase 5 complete:** the freeze commit, with every case's hashes, rubric, probe records and independent reads.
- *(rests on 3.5)* The gate's case mode, proven both ways before the tag.
- *(rests on 3)* The matcher, its threshold and its minimum-evidence rule.

## Cost

**About $18-20**, nearly all of `planning/05`'s "$20-25" for Phase 5: about $14 for 750 decisions on Sonnet 4.6
(five cases, five objectives, three wordings, 10 repeats) and about $3-4 on Nova Pro. Four cases cost about
four-fifths of that, three about three-fifths. Each case sweep is a few dollars, well under the $25 official cap.

**Time:** 150 decisions per case per model; at 10 requests a minute, about 15 minutes per case on Sonnet 4.6, about
6 on Nova Pro.

## The main model

**Fixed in Phase 3.5.** The same set as the grid.

## Known risks

- **A memo names the company, or another real one.** Mitigation: the name scan; the memo is held back and counted.
- **A dossier fails the re-identification check after its runs.** Mitigation: the result is still published, by type
  and coarsely described; only the dossier is withheld, and the methods page says that case cannot be re-run from
  published inputs.
- **A match reads as a verdict on a company.** Mitigation: the wording rules, the coarse descriptions, and the
  "illustration, not validation" framing (`planning/00` §5.4) on every surface Phase 6 builds.

## Left for the IMPLEMENTATION doc

The steps and commands, in order, with what to look for after each. The re-identification check's method, exactly.
The general company-name check in the memo scan. The published files' layout. The order of the commits.
