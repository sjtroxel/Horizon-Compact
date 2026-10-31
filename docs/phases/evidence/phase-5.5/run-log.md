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

His decision, 2026-10-29 about 9:20 AM CDT, as recommended. Each sweep's cap against its worst case above:

| Model | Cap per sweep | Worst cases | Why |
|---|---|---|---|
| `haiku-5-5` | **$2.00** | $0.89 to $1.00 | The doc's rule (bound rounded up to the next dollar) gives $1, but `pre-11`'s bound is $1.00 to the cent; $2 leaves room. |
| `gpt-oss-openrouter` | **$0.50** | $0.31 to $0.35 | The doc says "under $1". His OpenRouter cash is $3.70 with no top-up until next week at the earliest; five sweeps at $0.50 cannot take more than $2.50. |

All are under the $5 development cap and the $25 official cap; no `--allow-over-cap` is used and no over-cap flag is
expected. Commit `73f2cdf` (`phase 5.5: section 6.0 readiness`) is pushed with CI green; Deploy did not run (it is
path-filtered and the commit touched only docs), so the digest above is still the task definition's image.

**§6.0 closed 2026-10-29. §6.1 next.**

## Totals so far
**The Haiku chain is complete, 2026-10-29:** five sweeps, 750 of 750 runs `valid`, 758 attempts (8 `schema_invalid`, all retried), $0.8518 in all against $4.76 of worst cases. Counts by status only.

**The `gpt-oss-120b` chain is complete, 2026-10-30:** `closure-07`, `closure-19`, `pre-11` (2026-10-29), `pre-25`, `pre-224` (2026-10-30); 750 of 750 runs `valid`, $0.2155 in all ($0.0426 + $0.0381 + $0.0482 + $0.0446 + $0.0420) against caps of $0.50 each. Counts by status only.

**§6.2 is complete, 2026-10-30:** all ten case sweeps, 1,500 of 1,500 runs `valid`, $1.0673 in all ($0.8518 Haiku + $0.2155 `gpt-oss-120b`), as read by him with `hc sweep status --case`. §6.3 next.

**§6.3, the record checks, 2026-10-30 about 17:20 UTC (12:20 PM CDT):** `hc protocol records --cases`, run by him; every check passes (`record-checks.md`). The image check is reported, not judged: all ten sweeps ran on one digest, `sha256:ef0588f9...`, the one §6.0 recorded. The per-sweep counts match the session rows below. The file's tree reads `fecd23dffb1f plus uncommitted changes`: the uncommitted changes were this log, `KNOWN-GAPS.md` and `ROADMAP.md` only (no code), committed with it (his choice, over a re-run on a clean tree). **§6.3 closed. §6.4, the reveal, next.**

**§6.4, the reveal, 2026-10-31 about 8:07 to 8:12 AM CDT:** `scratch/p55-match.sh` (ten `hc case match` lines, in
freeze order), run by him from `main` at `cbd6cb0`. Ten results files written under `experiment/results/cases/`, each
with `protocol_check: ok`, one `analysis_sha256` (`0cabbfd9...`) and one `uv_lock_sha256` (`d9cdf7fc...`) across all
ten; the two files of each case share that case's `rubric_sha256`. Every file reads 150 of 150 runs `valid`, and every
uncertain call's alternative was matched (no unmatched call). Against the S3 pair (`d_star` 0.5457, `k_star` 1):

| Case | Model | `primary` | `u1` | `depends_on_reading` |
|---|---|---|---|---|
| `closure-07` | `haiku-5-5` | no good match | no good match | true (see KNOWN-GAPS, OPEN 2026-10-31, item 1) |
| `closure-07` | `gpt-oss-openrouter` | no good match | no good match | false |
| `closure-19` | `haiku-5-5` | no good match | no good match | true (item 1) |
| `closure-19` | `gpt-oss-openrouter` | no good match | no good match | false |
| `pre-11` | `haiku-5-5` | no good match | no good match | true (item 1) |
| `pre-11` | `gpt-oss-openrouter` | no good match | no good match | false |
| `pre-25` | `haiku-5-5` | no good match | no good match | false |
| `pre-25` | `gpt-oss-openrouter` | no good match | no good match | false |
| `pre-224` | `haiku-5-5` | no good match | no good match | false |
| `pre-224` | `gpt-oss-openrouter` | no good match | no good match | false |

**All 20 readings are no good match.** The distances and spreads are in the files; nothing here interprets them.
Claude read all ten in full after they were written (a Sonnet session, then Opus checked every figure against the files
and the frozen `matcher.py` and `descriptive.distance`). Two behaviors of the frozen matcher show in these files and are
disclosure items for Phase 6 and 6.5, not changes: KNOWN-GAPS, OPEN 2026-10-31. **Honor statement (Claude's):** no case
result was read before the files were written. **§6.4 closed. §6.5, the memo scan, next.**

## Sessions

| When | Sweep | Model | Session | Stopped | Runs finished | Cost (USD) | Note |
|---|---|---|---|---|---|---|---|
| 2026-10-29 about 14:24 UTC (9:24 AM CDT) | `case-haiku-5-5-9119a8cd` (`closure-07`, seed 4142789090, cap $2) | `haiku-5-5` | task `6092876d891847a1b0e623c9bffb4965` | complete (session started 2026-10-29 14:24:41 UTC) | 150 of 150, all `valid`; 151 attempts (1 `schema_invalid`, retried, then `valid`) | 0.1667 | §6.1, launched alone by him at `73f2cdf`; sweep id matches the dry run. Read by him at about 11:07 AM CDT with `hc sweep status --case`. Counts by status only. Against the $0.95 worst case and the $2 cap. No fault: the case path (assembly, gate in the container, case prefix) ran end to end, and the task started, so `propagateTags` was accepted |
| 2026-10-29 about 16:08 UTC (11:08 AM CDT) | `case-gpt-oss-openrouter-90dc7f0d` (`closure-07`, seed 2401484987, cap $0.50, `--max-minutes 720`) | `gpt-oss-openrouter` | task `c125a241f1b94d2ca393e5255a9a8c68` | complete (session started 16:08:57 UTC) | 150 of 150, all `valid`; 150 attempts, no retry | 0.0426 | §6.2, `gpt-oss-120b` chain, 1 of 5; launched by him; sweep id matches the dry run |
| 2026-10-29 about 16:36 UTC (11:36 AM CDT) | `case-haiku-5-5-3d85ff31` (`closure-19`, seed 916347355, cap $2) | `haiku-5-5` | task `3ff7ac4e08614f54b3e189427686865b` | complete (session started 16:36:48 UTC) | 150 of 150, all `valid`; 151 attempts (1 `schema_invalid`, retried) | 0.1459 | §6.2, Haiku chain, 2 of 5 (`closure-07` was §6.1); launched by him while the `gpt-oss-120b` `closure-07` sweep runs; sweep id matches the dry run |
| 2026-10-29 about 17:05 UTC (12:05 PM CDT) | `case-haiku-5-5-13fab9d7` (`pre-11`, seed 3510822617, cap $2) | `haiku-5-5` | task `199714da1c0b4d8aa064350f5632587e` | complete (session started 17:05:34 UTC) | 150 of 150, all `valid`; 151 attempts (1 `schema_invalid`, retried) | 0.1861 | §6.2, Haiku chain, 3 of 5; launched by him after `closure-19` completed; sweep id matches the dry run |
| 2026-10-29 about 17:14 UTC (12:14 PM CDT) | `case-gpt-oss-openrouter-1e058732` (`closure-19`, seed 537881194, cap $0.50, `--max-minutes 720`) | `gpt-oss-openrouter` | task `034eab78d68b484ebd6ec97447a044e8` | complete (session started 17:14:49 UTC) | 150 of 150, all `valid`; 156 attempts (6 `api_error`, each retried; the session did not stop) | 0.0381 | §6.2, `gpt-oss-120b` chain, 2 of 5; launched by him after `closure-07` completed; sweep id matches the dry run |
| 2026-10-29 about 17:27 UTC (12:27 PM CDT) | `case-haiku-5-5-30276496` (`pre-25`, seed 1933638959, cap $2) | `haiku-5-5` | task `ebb335ba68fb49769a235b09b1582a0b` | complete (session started 17:27:48 UTC) | 150 of 150, all `valid`; 154 attempts (4 `schema_invalid`, each retried; the most of any sweep so far, still inside 3 attempts per run) | 0.1871 | §6.2, Haiku chain, 4 of 5; launched by him after `pre-11` completed; sweep id matches the dry run |
| 2026-10-29 about 18:18 UTC (1:18 PM CDT) | `case-haiku-5-5-a7525775` (`pre-224`, seed 4141966721, cap $2) | `haiku-5-5` | task `714f218ed7754054a8207d2f9349e784` | complete (session started 18:19:07 UTC) | 150 of 150, all `valid`; 151 attempts (1 `schema_invalid`, retried) | 0.1660 | §6.2, Haiku chain, 5 of 5; launched by him after `pre-25` completed; sweep id matches the dry run |
| 2026-10-29 about 21:14 UTC (4:14 PM CDT) | `case-gpt-oss-openrouter-e3ccf78f` (`pre-11`, seed 218789764, cap $0.50, `--max-minutes 720`) | `gpt-oss-openrouter` | task `ef8c155b957e42a298d25a9fdb058023` | **stopped: `api_errors`** (session started 21:15:00 UTC) | 19 of 150, all `valid`; 96 attempts (73 `api_error`, 4 `no_tool_call`, 19 `valid`) | 0.0060 | §6.2, `gpt-oss-120b` chain, 3 of 5; launched by him after `closure-19` completed (he was away about three hours between); sweep id matches the dry run |
| 2026-10-29 about 22:00 UTC (5:00 PM CDT) | `case-gpt-oss-openrouter-e3ccf78f` | `gpt-oss-openrouter` | (stop, read by him) | | | | Phase 4 §7's stop table, `api_errors` row: wait about 30 minutes, re-launch. Cause read by Claude from OpenRouter's endpoints API at about 5:00 PM CDT: the pinned `deepinfra/bf16` endpoint at status -5, uptime 33% over 30 minutes and 80% over 5 (96% over a day). The pin is the protocol's and is not changed. A re-launch with the same seed resumes the same sweep id (`write_order` refuses unless the stored finding matches). |
| 2026-10-29 about 22:37 UTC (5:37 PM CDT) | `case-gpt-oss-openrouter-e3ccf78f` (`pre-11`, re-launch, same seed and cap) | `gpt-oss-openrouter` | task `f3d252d76db04c14bda90acad62c3d2d` | **stopped: `api_errors`** (session started 22:37:43 UTC; stop time not read) | sweep at 68 of 150, all `valid`; 239 attempts in all (164 `api_error`, 7 `no_tool_call`, 68 `valid`); this session 143 attempts | 0.0218 (sweep) | Re-launch after the `api_errors` stop, about 37 minutes later; same sweep id, so a resume. DeepInfra read at about 5:36 PM CDT: status 0, uptime 87% over 30 minutes, 20% over 5, 96% over a day |
| 2026-10-29 about 00:53 UTC 10/30 (7:53 PM CDT) | `case-gpt-oss-openrouter-e3ccf78f` | `gpt-oss-openrouter` | (second stop, read by him) | | | | Second `api_errors` stop, more than an hour after the first. DeepInfra read by Claude at about 7:54 PM CDT: status -2, uptime 20% over 5 minutes, 70% over 30, 93% over a day. |
| 2026-10-30 00:55 UTC (7:55 PM CDT 10/29) | `case-gpt-oss-openrouter-e3ccf78f` (`pre-11`, second re-launch, same seed and cap) | `gpt-oss-openrouter` | session started 00:55:02 UTC (task id not pasted) | complete | **150 of 150, all `valid`**; sweep in all 321 attempts (164 `api_error`, 7 `no_tool_call`, 150 `valid`); this session 82 attempts, no `api_error` | 0.0482 (sweep) | Resume after the second stop; DeepInfra had recovered. Three sessions in all; the `no_tool_call` attempts were retried and no run finished on one |
| 2026-10-30 about 12:54 UTC (7:54 AM CDT) | `case-gpt-oss-openrouter-eb1036dc` (`pre-25`, seed 1259122587, cap $0.50, `--max-minutes 720`) | `gpt-oss-openrouter` | task `b344b373c62947bc818a356797869b4d` | complete (session started 12:54:33 UTC) | 150 of 150, all `valid`; 213 attempts (63 `api_error`, each retried; the session did not stop) | 0.0446 | §6.2, `gpt-oss-120b` chain, 4 of 5; launched by him; sweep id matches the dry run. Two refusals came first, both from a command Claude gave without `--profile`, then without `--bucket` (the laptop's case path needs both; `HC_RESULTS_BUCKET` was not set in his shell). Both refuse before `order.json` is written. DeepInfra not read before the launch. Read by him at about 9:15 AM CDT with `hc sweep status --case`. Counts by status only |
| 2026-10-30 about 14:16 UTC (9:16 AM CDT) | `case-gpt-oss-openrouter-2b24bdc9` (`pre-224`, seed 1744604528, cap $0.50, `--max-minutes 720`) | `gpt-oss-openrouter` | task `4e172f454954487db54fa6b412064bd6` | complete (session started 14:16:19 UTC) | 150 of 150, all `valid`; 244 attempts (94 `api_error`, each retried; the session did not stop) | 0.0420 | §6.2, `gpt-oss-120b` chain, 5 of 5; launched by him after `pre-25` completed; sweep id matches the dry run. Read by him at about 12:15 PM CDT with `hc sweep status --case`. Counts by status only |
