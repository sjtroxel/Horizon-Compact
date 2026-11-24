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

## The items (batch 3 of 3)

ITEM C14. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/07-EVAL-SPEC.md#L602, section 10.0): real cases chosen by a mechanical rule; a shortfall is reported, never filled by judgment.
1. The rule ran on its set date, 2026-10-16, and found no case in any type, with shortfalls closure 2, retool 2, ai 1: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/phase-5-case-building-search-IMPLEMENTATION.md#L510, part A item 1, and https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/ROADMAP.md, the Phase 5 row.
2. The five cases came from a later exploratory rule, adopted on 2026-10-19 after every rejected candidate's record had been seen: the same section's opening paragraphs.
3. Every case carries an exploratory label saying it was selected after the pre-registered rule found none: https://horizon-compact.vercel.app/cases/ and https://github.com/sjtroxel/horizon-compact/blob/4911440/experiment/results/cases/cases.json (`exploratory_label`).

ITEM C15. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/07-EVAL-SPEC.md#L622, sections 10.1 to 10.3): a pre-event dossier, a rubric committed before any model sees the case, and a recognition probe.
1. The case-building audit records each case's lock pushed before its first probe, five rubric reads, and the probe results (four cases six of six on the first set; one on a second set after coarsening): https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/phase-5-case-building-exploratory-IMPLEMENTATION.md#L1116, its rows 3 to 5.
2. For cases from the exploratory rule's steps 3 and 4, a knowledge probe of both official models replaced the date window's protection against training data: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/phase-5-case-building-search-IMPLEMENTATION.md#L510, part A item 3.
3. Three cases carry a label saying so: https://horizon-compact.vercel.app/cases/

ITEM C16. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/07-EVAL-SPEC.md#L668, section 10.4): "most closely matched", the matcher.
1. The matcher is frozen at the tag: https://github.com/sjtroxel/horizon-compact/blob/4911440/experiment/protocol/protocol-v1.md#L951
2. All 20 readings came out "no good match": https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/phase-5.5-case-runs-IMPLEMENTATION.md#L922, row 2.
3. The methods page discloses two behaviors of the matcher: https://horizon-compact.vercel.app/methods/#real-cases

ITEM D1. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/05-EVOLUTION-PLAN.md#L94, the first row of the table): pre-registration before any official run; the harness refuses an official sweep whose protocol hash does not match.
1. The tag `prereg-v1` points to commit 649e8b9 and is dated 2026-10-13: https://github.com/sjtroxel/horizon-compact/releases/tag/prereg-v1 and https://github.com/sjtroxel/horizon-compact/tags
2. The first official grid sessions started on 2026-10-14 at 09:52 UTC: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/phase-4-official-grid-runs-IMPLEMENTATION.md#L515, row 2.
3. On tag day, dry runs refused changed content, instrument, analysis, document and model identity: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/evidence/phase-3.5/tag-record.md (section 7).
4. The protocol discloses what was seen before the tag, including the second family's development runs, with no amount, choice or memo read: https://github.com/sjtroxel/horizon-compact/blob/4911440/experiment/protocol/protocol-v1.md#L182 and #L260

ITEM D2. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/05-EVOLUTION-PLAN.md#L95): provenance on every model call.
1. https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/evidence/phase-4/record-checks.md: the "content", "model" and "request" checks pass.
2. A test checks a provider's provenance record: https://github.com/sjtroxel/horizon-compact/blob/4911440/tests/test_anthropic_provider.py#L231

ITEM D3. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/05-EVOLUTION-PLAN.md#L96): raw responses kept, write-once.
1. Every write sends `IfNoneMatch="*"`, so an existing object is never replaced: https://github.com/sjtroxel/horizon-compact/blob/4911440/src/horizon_compact/sweep/store.py#L70
2. A test checks the results bucket is write-once and cannot be destroyed: https://github.com/sjtroxel/horizon-compact/blob/4911440/tests/test_architecture.py#L341

ITEM D5. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/05-EVOLUTION-PLAN.md#L98): one way to capture a decision across all models.
1. Both providers send one tool with `tool_choice` set to auto: https://github.com/sjtroxel/horizon-compact/blob/4911440/src/horizon_compact/providers/anthropic.py#L236 and https://github.com/sjtroxel/horizon-compact/blob/4911440/src/horizon_compact/providers/openrouter.py#L220

ITEM D6. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/05-EVOLUTION-PLAN.md#L99): experiment content as versioned data, hashed.
1. The content is in data files: https://github.com/sjtroxel/horizon-compact/blob/4911440/experiment/company
2. A lock file hashes it: https://github.com/sjtroxel/horizon-compact/blob/4911440/experiment/protocol/prereg.lock
3. The "content" record check passes: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/evidence/phase-4/record-checks.md

ITEM D7. Promise (https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/planning/05-EVOLUTION-PLAN.md#L100): the public/private boundary (no real company name in the public repo).
1. Name-guard hooks run on commits and commit messages: https://github.com/sjtroxel/horizon-compact/blob/4911440/.pre-commit-config.yaml#L21 and #L31
2. `methods-appendix/` is ignored: https://github.com/sjtroxel/horizon-compact/blob/4911440/.gitignore
3. A history scan found nothing over 177 commits, and the surfaces the guard cannot read were read by hand: https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/phases/evidence/phase-7/rule-zero.md

ITEM E6. Claim: an entry carried from the AWS foundation phase to the walking-skeleton phase is still headed CARRIED, and its items either landed or concerned Bedrock only.
1. https://github.com/sjtroxel/horizon-compact/blob/4911440/docs/KNOWN-GAPS.md has an entry headed "CARRIED", from Phase 0.5 to Phase 1, dated 2026-10-04 (search the page for "CARRIED").
2. A malformed tool call is classed as a model outcome: https://github.com/sjtroxel/horizon-compact/blob/4911440/src/horizon_compact/sweep/classify.py#L75
3. The deploy role has a permissions boundary: https://github.com/sjtroxel/horizon-compact/blob/4911440/infra/terraform/bootstrap/iam.tf#L1
