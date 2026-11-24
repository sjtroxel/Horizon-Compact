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

## The items (batch 2 of 3)

ITEM A5f. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/00-DESIGN-BRIEF.md#L246): "AWS: ... a budget alarm set before the first full run."
1. https://github.com/sjtroxel/horizon-compact/blob/4911440/infra/terraform/bootstrap/budgets.tf defines two budgets that notify on actual spend only (`notification_type = "ACTUAL"`) and do not net out credits (`include_credit = false`); one is filtered to the `Project` tag.
2. They were applied when the AWS foundation phase closed on 2026-10-08: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/ROADMAP.md, the Phase 0.5 row, and https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/phase-0.5-aws-foundation-IMPLEMENTATION.md#L767, row 3.
3. The first full run started on 2026-10-14: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/phase-4-official-grid-runs-IMPLEMENTATION.md#L515, row 2.
4. That run's model calls went through Anthropic's API and OpenRouter, not through AWS: https://github.com/sjtroxel/horizon-compact/blob/4911440/experiment/protocol/protocol-v1.md#L433
5. That run's AWS compute was mostly untagged, so the tag-filtered budget did not see it (/bin/bash.27 of /bin/bash.31 had no `Project` tag): https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/evidence/phase-4/run-log.md#L118

ITEM A6. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/00-DESIGN-BRIEF.md#L248): "A methods page good enough that a hostile reader can re-run the experiment from the published inputs, including the anonymized real-case dossiers. Reconstructing the real cases from their sources is not possible ..., and the methods page says so."
1. The raw responses on the made-up company are in the repo, under https://github.com/sjtroxel/horizon-compact/blob/4911440/experiment/raw , with a manifest whose `object_count` is 5247: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/evidence/phase-4/raw-manifest.json (read its first lines).
2. A test re-runs the frozen analysis over those raw records and fails if anything opens an AWS client: https://github.com/sjtroxel/horizon-compact/blob/4911440/tests/test_analysis_rescoring.py (its docstring and #L39).
3. In https://github.com/sjtroxel/horizon-compact/blob/4911440/experiment/results/cases/cases.json, every case's `dossier` has `published: false` with a reason.
4. The methods page says no real case can be re-run: https://horizon-compact.vercel.app/methods/ (the real cases section and the "checking it yourself" section).
5. Two program images used by official runs were deleted from the image registry: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/KNOWN-GAPS.md, the entry headed "CLOSED 2026-11-04, with Phase 1.5 C1's apply ... ECR's ten-image rule had expired images" (search the page for "ten-image").

ITEM B15. Promise: the publish-path phase's definition of done, row 7: "No request leaves for another host; the security headers are served." The README relies on it for "No cookies, no analytics, no third-party requests."
1. That phase's audit marks row 7 met: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/phase-1.5-publish-path-IMPLEMENTATION.md#L1551 (the table in that section).
2. The site's content security policy allows only the site's own origin: https://github.com/sjtroxel/horizon-compact/blob/4911440/infra/terraform/bootstrap/site.tf#L23

ITEM B65. Promise: the methods-and-release phase's definition of done (eleven rows).
1. Its audit marks all eleven met, row 5 with two logged departures and two disclosures, row 6 with two qualifications: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/phase-6.5-methods-and-release-IMPLEMENTATION.md#L897
2. The CI run on that phase's go-live commit succeeded: https://github.com/sjtroxel/horizon-compact/actions/runs/44922943678

ITEM C2. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/07-EVAL-SPEC.md#L293, section 5): failures and refusals are counted as outcomes, a cell rule, and a worst-case bound.
1. The protocol states the counting, the 10% cell rule and the worst-case bound: https://github.com/sjtroxel/horizon-compact/blob/4911440/experiment/protocol/protocol-v1.md#L556 (section 7).
2. One comparison is "not assessable" because of failures: gpt-oss-120b, falling orders (s2), A against C. Check https://horizon-compact.vercel.app/scenario/s2/ with the model switched to gpt-oss-120b, or https://github.com/sjtroxel/horizon-compact/blob/4911440/README.md ("Every verdict").

ITEM C4. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/07-EVAL-SPEC.md#L353, section 6.1): a family of pre-registered primary comparisons, corrected for their number.
1. The protocol names sixteen primary comparisons and the correction: https://github.com/sjtroxel/horizon-compact/blob/4911440/experiment/protocol/protocol-v1.md#L491
2. In https://github.com/sjtroxel/horizon-compact/blob/4911440/web/explorer-data/grid/haiku-5-5/s1.json the primary comparisons carry `alpha` 0.003125 (0.05 divided by 16), so their intervals are at 99.7%.

ITEM C5. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/07-EVAL-SPEC.md#L375, section 6.2): "Three verdicts, never two."
1. The protocol keeps split, no split and inconclusive, and adds a fourth label, not assessable: https://github.com/sjtroxel/horizon-compact/blob/4911440/experiment/protocol/protocol-v1.md#L504
2. The protocol was tagged before any official run (the tag `prereg-v1`, 2026-10-13): https://github.com/sjtroxel/horizon-compact/releases/tag/prereg-v1

ITEM C6. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/07-EVAL-SPEC.md#L398, section 6.3): the interval method.
1. Before the tag, simulations found the first method's false-split rate too high (worst 2.22%), and the method for shares was changed; a residual (worst 0.43%) was accepted: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/phase-3-scoring-and-simulation-IMPLEMENTATION.md#L1067, row 3.
2. The known limits say the false-split chance is held approximately: https://horizon-compact.vercel.app/methods/#known-limits

ITEM C12. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/07-EVAL-SPEC.md#L501, section 7.4): a second model family.
1. The protocol names gpt-oss-120b as the second family, taken on 2026-10-12 in place of the planned Nova Pro, because Bedrock was unavailable: https://github.com/sjtroxel/horizon-compact/blob/4911440/experiment/protocol/protocol-v1.md#L433
2. That was before the protocol's tag on 2026-10-13: https://github.com/sjtroxel/horizon-compact/releases/tag/prereg-v1
3. The protocol discloses that gpt-oss-120b had been the development model on the company's content, read only through blind reports: https://github.com/sjtroxel/horizon-compact/blob/4911440/experiment/protocol/protocol-v1.md#L182
