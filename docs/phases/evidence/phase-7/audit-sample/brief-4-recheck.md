You are checking part of an audit of a public research repository. Work only from the public pages linked below and pages you reach from them by following links. Do not use anything you may remember about this project, and do not guess. If a page will not load, is too large to read, or does not hold what you need, say "could not check" and why.

- Repository (public): https://github.com/sjtroxel/horizon-compact
- Every file link is pinned to commit 4911440. For a raw copy of any file, use https://raw.githubusercontent.com/sjtroxel/horizon-compact/4911440/ followed by its path.
- The live site: https://horizon-compact.vercel.app

Each item below gives a promise the project made and the claims the audit makes about it. For each claim, open its source and say whether it is Confirmed, Contradicted, or Could not check, with what you saw (a short quote, a number or a line). Then give the item your own status: met (done as promised), partial (some of it not done: say which part), or not met. Base the status on what you found against the promise, not on the claims' wording.

Reply in exactly this form, one block per item, and nothing else:

ITEM <ID>
- claim 1: Confirmed | Contradicted | Could not check: <what you saw>
- claim 2: ...
- status: met | partial | not met: <one sentence>

Do not change anything anywhere, do not sign in to anything, and do not submit any form.

## The items (re-check batch)

ITEM A2. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/00-DESIGN-BRIEF.md#L243): "At least three anonymized real cases run and presented by type." The section holding that line is headed "Definition of done for v1.0 (draft, to be finalized in `05` and `07`)" (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/00-DESIGN-BRIEF.md#L240).
1. https://github.com/sjtroxel/horizon-compact/blob/4911440/experiment/results/cases/cases.json holds five cases, each with `type` "closure" and `exploratory` true; `shortfall` reads short by type: retool 2, ai 1.
2. The cases are anonymized: each is named by a neutral label only; every dossier is withheld because a re-identification check could not clear it (each case's `reidentification.status` is "withheld", with its reason); four short descriptions are published after a search found no company, and one (pre-11) is withheld. See cases.json and https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/phase-5.5-case-runs-IMPLEMENTATION.md#L922, row 4.
3. The done-when for the case phase, as finalized in the project's plan, reads "At least three cases run and matched, including an invest or retool case", and that part is recorded as not met: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/ROADMAP.md, the Phase 5 row of the first table, and https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/05-EVOLUTION-PLAN.md#L186 (the phases table, where it reads "including the invest or retool case").
4. None of the five was chosen by the pre-registered selection rule, which found no case: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/phase-5-case-building-search-IMPLEMENTATION.md#L510, part A item 1.

ITEM A5b. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/00-DESIGN-BRIEF.md#L246): "AWS: ... outputs in S3 ..."
1. Every write to S3 is exclusive (`IfNoneMatch="*"`): https://github.com/sjtroxel/horizon-compact/blob/4911440/src/horizon_compact/sweep/store.py#L1 and #L70.
2. The rule "one object per attempt" is the protocol's: https://github.com/sjtroxel/horizon-compact/blob/4911440/experiment/protocol/protocol-v1.md#L1036
3. The record checks find every run complete: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/evidence/phase-4/record-checks.md ("complete").

ITEM A6. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/00-DESIGN-BRIEF.md#L248): "A methods page good enough that a hostile reader can re-run the experiment from the published inputs, including the anonymized real-case dossiers. Reconstructing the real cases from their sources is not possible ..., and the methods page says so."
1. The made-up company's raw responses are published with a manifest of 5,247 objects (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/evidence/phase-4/raw-manifest.json), and a test re-runs the frozen analysis over them with no AWS client (https://github.com/sjtroxel/horizon-compact/blob/4911440/tests/test_analysis_rescoring.py).
2. Every case dossier is withheld (cases.json, each `dossier.published` false), so no real case can be re-run, and the methods page says so: https://horizon-compact.vercel.app/methods/
3. Two image digests expired from the image registry: `sha256:ff978703...`, the one image of every Phase 4 sweep (the grids, the side studies and the pilots), and `sha256:ef2582ed...`, an earlier skeleton test image that ran no official sweep. The case runs' image, `sha256:ef0588f9...`, still exists. So no Phase 4 run can be repeated in its identical image. Sources: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/KNOWN-GAPS.md (search for "ten-image") and https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/evidence/phase-4/record-checks.md (the image section).

ITEM B65. Promise: the methods-and-release phase's definition of done: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/phase-6.5-methods-and-release-IMPLEMENTATION.md#L861 (section 9) and its audit at #L897 (section 11.1).
1. Its audit marks all eleven rows "yes".
2. Row 5 (the video) carries two logged departures in how the video was made; the row's outcome (the frame and narration checks passed, captioned and labeled) is recorded as met.
3. Row 6 promises "every section 9 check on every surface", but check 6 is accepted as absent on the cards and the video by his decision, and check 4 was one read rather than the reads it described.

ITEM C6. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/07-EVAL-SPEC.md#L398, section 6.3, with its targets in section 8): the interval method, and the error rates it is chosen to hold.
1. The method was changed before the tag (2026-10-13), after simulations found the first method's false-split rate too high (worst 2.22%): https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/phase-3-scoring-and-simulation-IMPLEMENTATION.md#L1067, row 3.
2. What remains: the per-comparison false-split target of 0.3125% is held approximately (worst 0.43% for shares, 0.417% for choice rates), and no-split reachability is 49.7% at its worst point against about 54% stated. Sources: the same row, and https://horizon-compact.vercel.app/methods/ (the statistics section and the known limits).

ITEM E6. Claim: an entry carried from the AWS foundation phase to the walking-skeleton phase is still headed CARRIED, and of its items, some landed and some concerned only a model service the project stopped using.
1. https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/KNOWN-GAPS.md has an entry headed "CARRIED", from Phase 0.5 to Phase 1, dated 2026-10-04 (search the page for "CARRIED").
2. A malformed tool call is classed as a model outcome: https://github.com/sjtroxel/horizon-compact/blob/4911440/src/horizon_compact/sweep/classify.py#L75
3. A permissions boundary exists for every role the deploy role creates (https://github.com/sjtroxel/horizon-compact/blob/4911440/infra/terraform/bootstrap/iam.tf#L23), and the deploy role itself carries none (https://github.com/sjtroxel/horizon-compact/blob/4911440/infra/terraform/bootstrap/oidc.tf).
