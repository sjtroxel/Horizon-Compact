# Phase 5.5 run log

Every launch, stop, re-launch and fix of the Phase 5.5 case runs, with the time, sweep id, session, image digest and
what was seen (statuses and costs only, never a decision). IMPLEMENTATION doc §6. Newest last. A run-code fix gets its
own row: the commit, the file, the cause, and the effect on runs. Times are UTC unless marked CDT.

## The image (§6.0 step 1)

| When | Commit | CI | Deploy | Image digest |
|---|---|---|---|---|
| 2026-10-28 22:19 UTC (5:19 PM CDT) | `101e2df` (`phase 5.5: k5 re-identification check`) | `40778513125` green | `40778513089` green | `sha256:ef0588f95b3fbf6fc5960a863dec11ac775a4fca23a2a49734736baa809baec7` |

The digest is the pushed image's (`containerimage.digest` in the Deploy run's build job, read 2026-10-29 from the
job's log), and the Deploy's `apply main` job planned and applied the task definition with the same
`image_digest` (Plan: 1 to add, 1 to destroy; Apply complete). It replaces `sha256:3fd3831a...`, the image of the
previous commit. Local `main` and `origin/main` were both at `101e2df` with a clean working tree when this was
written. Every case sweep should run on this digest; the record checks (§6.3) list what each sweep ran on. A code
push before §6.1 adds a row here.

## Live checks (§6.0 step 2), Claude's, 2026-10-29 about 8 AM CDT

| Model | Read from | Seen | Verdict |
|---|---|---|---|
| Haiku 5.5 | platform.claude.com, Models overview | API id `claude-haiku-5-5`; "From $0.10 / input MTok, From $0.50 / output MTok" (the "from" is the under-100K-token tier `models.toml` uses); max output 128K tokens; thinking "Adaptive", default effort `medium`; retirement "Not sooner than October 7, 2027" | **pass** |
| `gpt-oss-120b` | OpenRouter's endpoints API for `openai/gpt-oss-120b` | 25 endpoints listed; DeepInfra tag `deepinfra/bf16`, quantization `bf16`, $0.000000037 prompt and $0.00000017 completion per token ($0.037 and $0.17 per million), status 0, uptime 100% over 5 and 30 minutes and 98.75% over a day, max completion tokens 117,964 | **pass** |

Neither price changed since 2026-10-13 (`phase-4/run-log.md`), so `cost.md`'s rates stand. Haiku 5.5 has been served
at the same id and price on every reading to date.

## Readings before the first case run (§6.0 step 3)

His readings, 2026-10-29 about 7:50 AM CDT, set against `docs/phases/evidence/phase-5/cost.md` (2026-10-26) and
the IMPLEMENTATION doc §12 (case runs about $3.10, worst $4.50: Anthropic credit about $2.40, OpenRouter about
$0.70; Fargate under $1 of AWS credit):

| Pot | Reading | Phase 5.5's share | Note |
|---|---|---|---|
| Anthropic prepaid credit | **$11.96** | about $2.40 for the runs, plus about $0.20-0.30 for the memo scan's Haiku pass | Covers it about four times over. The monthly limit ($20, resets 2026-11-01) was $13.71 from its limit on 2026-10-26 (October spend $6.29); no model call has been made since, so that figure stands unless the Console says otherwise. **To confirm from the Console.** |
| OpenRouter (his cash) | **$3.70**; no top-up possible until next week at the earliest | about $0.70 for the five `gpt-oss-120b` sweeps | Covers the runs about five times over. See the warning below. |
| AWS (shared with Musical Mycelium) | Billing home, 2026-10-29 about 7:58 AM CDT: month-to-date **$0.45** for the whole account, forecast **$0.89** for October (September in full was $17.77); 5 budgets OK, no cost anomalies | Fargate under $1 | $0.44 on 2026-10-26, so about a cent since. The credits balance is not on that page and was not read; the 2026-10-13 reading was $135.97 of credits remaining, expiring 2027-07-30. The whole month is forecast under the share's own bound, so nothing here limits the runs. |

Both reported balances equal the 2026-10-26 readings to the cent, which fits: nothing in §5 called a model.

**OpenRouter warning, for §6.5 not §6.0.** After the five sweeps about $3.00 is left. The memo scan's independent
reader reads (a few cents each, Gemini 3.1 Pro on OpenRouter) are estimated at $1-6 in all (IMPLEMENTATION doc §5.4's
dated note), so they may not all fit before the top-up. The number of memos flagged is known from Haiku's pass
(Anthropic credit) before any reader read is paid, so §6.5 decides then: read what fits, or wait for the top-up. His
decision. No OpenRouter spend outside the five `gpt-oss-120b` sweeps until then.

The cut order if a pot ever cannot cover its share (`planning/05` §5.1) is the fifth case, then the fourth, where
fifth is the last in `freeze.json`'s order: `closure-07`, `closure-19`, `pre-11`, `pre-25`, `pre-224`. No cut is
needed on these readings.

## Dry runs (§6.0 step 4)

His, 2026-10-29 about 8:10 AM CDT, `scratch/p55-dryruns.sh` (output kept in `scratch/p55-dryruns.txt`), on the
laptop at `101e2df` with the `horizon-compact` profile: every gate check against the lock and the freeze, nothing
written, nothing called. **10 of 10 passed**, each `order: admitted`, scenario `s3` x 5 objectives x 3 templates
(`w1`, `w2`, `w3`) x 10 repeats, 150 runs, "not in the container (dry run)" as expected. **5 of 5 rubrics
checked:** each shape `s3`, observable dimension `choice`, primary reading 1 of 1 needed, `u1` reading enough (1 of 1
for `closure-19`, 4 of 1 for the other four).

| Case | Model | Seed | Sweep id | Worst case (3 attempts per run) |
|---|---|---|---|---|
| closure-07 | `haiku-5-5` | 4142789090 | `case-haiku-5-5-9119a8cd` | $0.95 |
| closure-07 | `gpt-oss-openrouter` | 2401484987 | `case-gpt-oss-openrouter-90dc7f0d` | $0.33 |
| closure-19 | `haiku-5-5` | 916347355 | `case-haiku-5-5-3d85ff31` | $0.89 |
| closure-19 | `gpt-oss-openrouter` | 537881194 | `case-gpt-oss-openrouter-1e058732` | $0.31 |
| pre-11 | `haiku-5-5` | 3510822617 | `case-haiku-5-5-13fab9d7` | $1.00 |
| pre-11 | `gpt-oss-openrouter` | 218789764 | `case-gpt-oss-openrouter-e3ccf78f` | $0.35 |
| pre-25 | `haiku-5-5` | 1933638959 | `case-haiku-5-5-30276496` | $0.98 |
| pre-25 | `gpt-oss-openrouter` | 1259122587 | `case-gpt-oss-openrouter-eb1036dc` | $0.34 |
| pre-224 | `haiku-5-5` | 4141966721 | `case-haiku-5-5-a7525775` | $0.94 |
| pre-224 | `gpt-oss-openrouter` | 1744604528 | `case-gpt-oss-openrouter-2b24bdc9` | $0.33 |

The sweep ids are derived from the lock, model, case and seed, so the real launches carry these same ids. The worst
cases sum to **$4.76 for Haiku** (against $11.96 of credit) and **$1.66 for `gpt-oss-120b`** (against $3.70 of
OpenRouter cash, leaving at least $2.04 if every attempt of every run were used), **$6.42 in all**. That is above
`cost.md`'s "worst $4.50" for the case runs; the expected spend there ($3.10) is a different, lower figure and is
not changed by this. Cumulative at the worst case: at most about $45 (`cost.md`) + $6.42 + Fargate under $1, about
$52, under the $60 re-plan point.

Note for the doc: step 4 named `hc sweep launch --case ... --dry-run`, but `launch` has no `--dry-run` (it is on
`hc sweep run` only, `cli.py`), and `cmd_case_sweep_launch` would write `order.json` and start a task. The script
used `hc sweep run --case ... --dry-run`. The doc's step 4 carries a dated correction.

## The caps (§6.0 step 5)

To be set with him from the worst cases above; see the next entry.

## Sessions

| When | Sweep | Model | Session | Stopped | Runs finished | Cost (USD) | Note |
|---|---|---|---|---|---|---|---|
