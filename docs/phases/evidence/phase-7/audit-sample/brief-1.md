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

## The items (batch 1 of 3)

ITEM A1. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/00-DESIGN-BRIEF.md#L242): "All four scenarios x five objectives run with stated repeats on at least one model, with spread reported."
1. https://github.com/sjtroxel/horizon-compact/blob/4911440/web/explorer-data/methods.json lists two grid sweeps: `grid-haiku-5-5-0b99fabb` with repeats s1 20, s2 6, s3 20, s4 20 and 990 runs in its manifest, and `grid-gpt-oss-openrouter-fe599ad2` with 20 on every scenario and 1,200.
2. The same file shows each grid covering four scenarios (s1 to s4) and three wordings (`templates` w1, w2, w3).
3. The repeats were set from the pilots by a rule before the grid ran: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/phase-4-official-grid-runs-IMPLEMENTATION.md#L515, row 2 of the table there.
4. Each comparison reports an interval: in https://github.com/sjtroxel/horizon-compact/blob/4911440/web/explorer-data/grid/haiku-5-5/s1.json, every entry of `comparisons` has `low` and `high`.
5. The site shows every run and five goals (A to E): https://horizon-compact.vercel.app/scenario/s1/

ITEM A2. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/00-DESIGN-BRIEF.md#L243): "At least three anonymized real cases run and presented by type."
1. https://github.com/sjtroxel/horizon-compact/blob/4911440/experiment/results/cases/cases.json holds five cases, each with `type` "closure" and `exploratory` true, and its `shortfall` reads short by type: retool 2, ai 1.
2. None of the five was chosen by the pre-registered selection rule, which found no case: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/phase-5-case-building-search-IMPLEMENTATION.md#L510, part A item 1 of that section.
3. The project's own plan for this phase asked for "at least three cases run and matched, including an invest or retool case", and the invest-or-retool part is recorded as not met: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/ROADMAP.md, the Phase 5 row of the first table.
4. The cases page presents them by type, each with an exploratory label: https://horizon-compact.vercel.app/cases/

ITEM A3a. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/00-DESIGN-BRIEF.md#L244): "Wording-variant and shuffled-order checks run, with results published even where unflattering." This item covers the wording half only.
1. Each goal is given in three wordings, and one, sealed in advance, is also reported alone: https://github.com/sjtroxel/horizon-compact/blob/4911440/experiment/protocol/protocol-v1.md#L659 (sections 9.1 and 9.2).
2. In https://github.com/sjtroxel/horizon-compact/blob/4911440/web/explorer-data/grid/haiku-5-5/s1.json each comparison carries `per_wording`, `kept_wordings` and `sealed` fields.
3. A scenario page shows the sealed wording's result beside each comparison: https://horizon-compact.vercel.app/scenario/s1/ (open the details of a comparison if needed).

ITEM A3b. Promise: the same sentence as A3a; this item covers the shuffled-order half. Also https://github.com/sjtroxel/horizon-compact/blob/4911440/experiment/protocol/protocol-v1.md#L675 (section 9.3): "a position effect found is published".
1. https://github.com/sjtroxel/horizon-compact/blob/4911440/web/explorer-data/grid/haiku-5-5/s3.json has a `position` block; for each option it gives the times chosen when listed first and otherwise, with a 95% interval.
2. In that block, option `sell` was chosen 8 times in 106 runs where it was listed first and 3 times in 194 otherwise, with an interval of about +0.013 to +0.127.
3. Of the ten option intervals in the `position` blocks of s3.json and s4.json, for both models (the same files under `web/explorer-data/grid/gpt-oss-openrouter/`), that is the only one that excludes zero.
4. No page of the site shows these position results or says what they found: look at https://horizon-compact.vercel.app/scenario/s3/ and https://horizon-compact.vercel.app/methods/

ITEM A4. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/00-DESIGN-BRIEF.md#L245): "The explorer is live (pick, compare, read memos, methods page) and serves only precomputed data."
1. These load: https://horizon-compact.vercel.app/ , https://horizon-compact.vercel.app/methods/ , https://horizon-compact.vercel.app/cases/ , https://horizon-compact.vercel.app/scenario/s1/ , https://horizon-compact.vercel.app/memos/ ; and https://horizon-compact.vercel.app/nope-404/ shows a not-found page.
2. On a scenario page you can pick a model and compare goals; the memos page shows the models' memos on the made-up company.
3. The site reads only committed data, and computes no result: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/phase-6-explorer-IMPLEMENTATION.md#L3445, row 1.

ITEM A5a. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/00-DESIGN-BRIEF.md#L246): "AWS: batch runs on Fargate ..."
1. https://github.com/sjtroxel/horizon-compact/blob/4911440/infra/terraform/main/ecs.tf#L15 sets `requires_compatibilities = ["FARGATE"]`.
2. https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/evidence/phase-4/record-checks.md: the "container" check passes, and one image digest is listed for all seven sweeps.

ITEM A5b. Promise: "AWS: ... outputs in S3 ..."
1. https://github.com/sjtroxel/horizon-compact/blob/4911440/src/horizon_compact/sweep/store.py#L1 (its opening docstring): the store writes one S3 object per attempt and never overwrites one.

ITEM A5d. Promise: "AWS: ... Terraform for everything ..."
1. The project's AWS resources are defined under https://github.com/sjtroxel/horizon-compact/blob/4911440/infra/terraform/bootstrap and https://github.com/sjtroxel/horizon-compact/blob/4911440/infra/terraform/main
2. Not in Terraform: the IAM user `horizon-compact-dev` and its policy, created by hand in the AWS console with the policy pasted from a tracked file: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/phase-0.5-aws-foundation-IMPLEMENTATION.md#L88
3. A full destroy and re-apply of the `main` configuration passed: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/phase-6.5-methods-and-release-IMPLEMENTATION.md#L897, row 11.

ITEM A5e. Promise: "AWS: ... deploys via OIDC ..."
1. https://github.com/sjtroxel/horizon-compact/blob/4911440/.github/workflows/deploy.yml#L120 grants `id-token: write`, and #L132 assumes a role from a secret (`role-to-assume`), with no AWS access key in the workflow.
2. The GitHub OIDC provider is looked up, not created: https://github.com/sjtroxel/horizon-compact/blob/4911440/infra/terraform/bootstrap/oidc.tf#L14 is a `data` source.
