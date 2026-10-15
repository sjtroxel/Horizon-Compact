# Phase 4 run log

Every launch, stop, re-launch and fix of the Phase 4 runs, with the time, sweep id, session, image digest and what
was seen (statuses and costs only, never a decision). Runs-half IMPLEMENTATION doc §6 and §7. Newest last. A run-code
fix gets its own row: the commit, the file, the cause, and the effect on runs. Times are UTC unless marked CDT.

## The image

| When | Commit | CI | Deploy | Image digest |
|---|---|---|---|---|
| 2026-10-13 23:02 UTC (6:02 PM CDT) | `50f6f21` (`phase 4: runs-half section 5 build`) | `38481435281` green | `38481435305` green | `sha256:ff978703e4b6ae30fd6d4b2cd7a65670a2754a6b6623a1dfc5f1683229436723` |

The digest is the pushed image's (`containerimage.digest` in the Deploy run's build step), the one the task
definition names. Every pilot and official sweep should run on it; the record checks' "image" row lists what each
sweep actually ran on. A later code push before the first pilot (a fault found by §6.1) adds a row here, and the
pilots then run on that one.

## Live checks (§6.0 step 2), Claude's, 2026-10-13 about 6:20 PM CDT

| Model | Read from | Seen | Verdict |
|---|---|---|---|
| Haiku 5.5 | platform.claude.com, Models overview | API id `claude-haiku-5-5`; "From $0.10 / input MTok, From $0.50 / output MTok" (the "from" is the under-100K-token tier `models.toml` uses); max output 128K tokens (at least 16,000: yes); thinking "Adaptive", default effort `medium`; retirement "not sooner than October 7, 2027" | **pass** |
| `gpt-oss-120b` | OpenRouter's endpoints API for `openai/gpt-oss-120b` | DeepInfra endpoint tag `deepinfra/bf16`, quantization `bf16`, $0.000000037 prompt and $0.00000017 completion per token ($0.037 and $0.17 per million), status 0, uptime 100% over 30 minutes and 99.6% over a day, max completion tokens 117,964 | **pass** |

No price changed, so the projection's rates stand. Whether Haiku 5.5 accepts the sub-study's exact request is
§6.1's question, on the placeholder, not a page reading.

## Readings before the first pilot (§6.0 step 3)

His readings, 2026-10-13 about 6:30 PM CDT, before §6.1's first call:

| Pot | Reading | Note |
|---|---|---|
| Anthropic prepaid credit | **$18.06** remaining; the `horizon-compact` workspace has spent **$0.18** this month against its $10 limit | Phase 4's Haiku estimate is about $1.5-2.3 |
| OpenRouter (his cash) | **$5.95** of credit available on his account; the key itself has no limit | the project's own spend to date was not read separately; `gpt-oss-120b`'s estimate is about $0.50-0.70 |
| AWS credits (shared with Musical Mycelium) | **$135.97** remaining, $24.03 used (estimated: $135.88 and $24.12); four active credits, all expiring 2027-07-30 | Fargate and S3 for Phase 4 are about $0.40 |

Every pot has room for the whole phase several times over. §6.3's projection checks each sweep's cap against these.

## Dry runs (§6.0 step 4), his, 2026-10-13 about 6:21 PM CDT

`scratch/p4-dryruns.sh`, on the laptop at `50f6f21`: every gate check against the lock, nothing written, nothing
called. **4 of 4 passed.** Each noted "not in the container (dry run)", as expected; the container check runs in
the task.

| Dry run | Seed | Sweep id | Runs | Result |
|---|---|---|---|---|
| pilot, `haiku-5-5` | 4096323239 | `pilot-haiku-5-5-0b9d9e79` | 80 | every check passes |
| pilot, `gpt-oss-openrouter` | 2323363371 | `pilot-gpt-oss-openrouter-1f75b653` | 80 | every check passes |
| awareness, `haiku-5-5` | 1394052595 | `awareness-haiku-5-5-0ce6ad12` | 15 | every check passes |
| awareness, `gpt-oss-openrouter` | 3046959125 | `awareness-gpt-oss-openrouter-6a05acef` | 15 | every check passes |

The four sweep ids are derived from the lock's content hash, the model, the label, the repeats and the seed, so the
real launches will carry these same ids.

## Sessions

| When | Sweep | Model | Session | Stopped | Runs finished | Cost (USD) | Note |
|---|---|---|---|---|---|---|---|
| 2026-10-13 23:30:35 UTC | `final-haiku-5-5-dde5ae24` (development, placeholder) | `haiku-5-5` | task `4fcab40e35204fd1a283105d41239996` | complete | 15 of 15, all `valid`, 15 attempts | 0.0147 | §6.1 |
| 2026-10-13 23:31:11 UTC | `final-gpt-oss-openrouter-82194bbe` (development, placeholder) | `gpt-oss-openrouter` | task `0ed7798f382744cb86763c549455c0e2` | complete | 15 of 15, all `valid`, 15 attempts | 0.0035 | §6.1 |
| 2026-10-14 00:05:02 UTC | `thinking-haiku-5-5-fd5e6f49` (development, placeholder) | `haiku-5-5` | task `9658ab03fed94e4985640b98f8123bae` | complete | 5 of 5, all `valid`, 5 attempts | 0.0150 | §6.1, the sub-study's request |
| 2026-10-14 00:28:29 UTC | `pilot-haiku-5-5-0b9d9e79` (pilot) | `haiku-5-5` | fargate | complete | 80 of 80: 79 `valid`, 1 `schema_invalid`; 94 attempts (79 `valid`, 10 `sum_mismatch`, 5 `schema_invalid`) | 0.1314 | §6.2, cap $1 |
| 2026-10-14 00:28:26 UTC | `pilot-gpt-oss-openrouter-1f75b653` (pilot) | `gpt-oss-openrouter` | fargate | complete | 80 of 80: 76 `valid`, 4 `schema_invalid`; 95 attempts (76 `valid`, 15 `schema_invalid`, 1 `sum_mismatch`, 3 `api_error`) | 0.0368 | §6.2, cap $1 |
| 2026-10-14 about 09:50 UTC (4:50 AM CDT) | `grid-haiku-5-5-0b99fabb` (official) | `haiku-5-5` | task `42cc50d429c14c71923f7621ceb5a671` (session 09:52:25 UTC) | complete | 990 of 990: 980 `valid`, 10 `sum_mismatch`; 1,128 attempts (980 `valid`, 134 `sum_mismatch`, 14 `schema_invalid`) | 1.5750 | §6.4, launched after `8eb3d43` (projection) was pushed; dry run passed; cap $7, max 300 min; read 8:02 AM CDT |
| 2026-10-14 about 09:50 UTC (4:50 AM CDT) | `grid-gpt-oss-openrouter-fe599ad2` (official) | `gpt-oss-openrouter` | task `038bd3d2804c4b82864b9f88bae2f14e` (session 09:52:27 UTC) | **crashed** (its summary says `complete`: fault 2 below) | 490 of 1,200 by the end; 551 attempts | 0.2208 | §6.4, the same; cap $3, max 720 min. Unhandled `IncompleteRead` (fault 1 below) |
| 2026-10-14 about 13:03 UTC (8:03 AM CDT) | `thinking-haiku-5-5-418caa9c` (official) | `haiku-5-5` | task `aff26f26744c453ca064c99ada37a79b` (session 13:03:48 UTC) | complete | 100 of 100, all `valid`, 100 attempts (none `truncated`) | 0.3688 | §6.5, after Haiku's grid completed; dry run passed; cap $3, max 180 min. The awareness probe's launch in the same script was refused by the one-task-per-model check (nothing written; its dry run passed); it waits for this one |
| 2026-10-14 about 14:02 UTC (9:02 AM CDT) | `awareness-haiku-5-5-0ce6ad12` (official) | `haiku-5-5` | task `38da4f1ca85d442dac1b132add90b6b3` | | 15 calls | | §6.5, after the sub-study completed; dry run passed; cap $1, max 60 min. Its replies are not read until the reveal |
| 2026-10-14 about 15:47 UTC (10:47 AM CDT) | `grid-gpt-oss-openrouter-fe599ad2` (official) | `gpt-oss-openrouter` | task `94e6ce3cff9544d6ba84317e21aec883` (session 15:47:45 UTC) | complete | 1,200 of 1,200 (782 attempts this session): 1,158 `valid`, 3 `valid_rescaled`, 33 `schema_invalid`, 2 `no_tool_call`, 2 `sum_mismatch`, 1 `truncated`, 1 `unexpected_stop`; 1,333 attempts over both sessions | 0.5422 (sweep total) | §6.4, resume after the crash (`scratch/p4-gptoss-resume.sh`); dry run passed; cap $3, max 720 min |
| 2026-10-15 00:04 UTC (7:04 PM CDT) | `awareness-gpt-oss-openrouter-6a05acef` (official) | `gpt-oss-openrouter` | task `6664dcab3434470eb2c16e2900d75407` | | 15 calls | | §6.5, after gpt-oss's grid completed; dry run passed; cap $1, max 120 min. Its replies are not read until the reveal |
| 2026-10-15 about 00:10 UTC (7:10 PM CDT) | `grid-gpt-oss-openrouter-fe599ad2` refusal calls | | his, on the laptop | written | 2 cases, **0 called refusals** | | §6.6, `refusal-calls.json` and `.meta.json`, write-once. Haiku's grid and sub-study had no `no_tool_call` run, so no file |

## §6.1 the placeholder check on the final image (decision 4): passed

Read by Claude from the 76 synced objects (`scratch/p4-check-sync.sh`; garden content only, read in full).

- **One image, clean, in the container:** all 35 attempts and all 3 sessions on
  `sha256:ff978703…436723`, runner `fargate`, git `50f6f21`, clean tree.
- **The grid's request on both routes:** Haiku `off: thinking {type: disabled} sent`, 0 thinking blocks;
  `gpt-oss-120b` `reasoning effort medium sent`, served by `DeepInfra` on all 15, one reasoning block each. Every
  attempt `tool_use` with one tool call; 30 of 30 `valid` on the first attempt.
- **The thinking sub-study's request is accepted by the API.** All 5 request bodies are exactly protocol 9.5's:
  `thinking {type: adaptive, display: summarized}`, `output_config {effort: high}`, `max_tokens` 16000, tool choice
  `auto`, nothing else added. Provenance on all 5: `adaptive, display summarized: sent`, effort `high`, max tokens
  16000. Every reply is a `thinking` block (a summary of 2,357-10,026 characters) then a `tool_use`; stop reason
  `tool_use`; 5 of 5 `valid`. **A tool call is made with thinking on.**
- **What thinking costs here:** output tokens 3,092-10,221 (mean about 5,400) against 1,025-1,773 with thinking off;
  $0.0030 a run against $0.0010. **One finding for §6.3:** the longest run used 10,221 of the 16,000 allowed on the
  short garden prompt; on S1's longer content a sub-study run could reach the limit and end `truncated`, a counted
  failure (protocol 9.5 says so). The 16,000 is locked; nothing changes. The projection uses this cost.
- **The record checks' wording, confirmed live:** the strings the providers wrote are the ones `hc protocol
  records` now expects (the fault fixed in review would have failed every `gpt-oss-120b` call).
- **Cost:** $0.0147 + $0.0035 + $0.0150 = **$0.0332** ($0.0297 of the Anthropic credit, $0.0035 of his cash), under
  decision 4's $0.06.

**Pilots' caps checked** (Claude, from the plans, no records read): preflight bounds $0.52 (`haiku-5-5`) and $0.18
(`gpt-oss-openrouter`), both under the $1 cap §6.2 sets.

## Faults found during the runs (not fixed until the last sweep ends: the push freeze)

**2026-10-14, `grid-gpt-oss-openrouter-fe599ad2`, first session (task `038bd3d2…`), crashed at 490 of 1,200.** Read
from the task's last 40 log lines (status and traceback only).

1. **Cause: an unhandled `http.client.IncompleteRead`.** OpenRouter's connection dropped part way through a reply's
   body (231 bytes read). `providers/openrouter.py` `_post` reads the body with `response.read()`; the caller turns
   `urllib.error` and `OSError` into an `api_error` record, but `IncompleteRead` is an `http.client.HTTPException`,
   neither of those, so it escaped the session. A transient network fault, not tied to a run: a resume is safe. The
   in-flight attempt left no record (it may still have been billed by OpenRouter, a fraction of a cent, which the
   §6.9 bill reconciliation will show as a small gap). It can happen again; each time, the same resume.
2. **The session's summary says `stopped: complete`, not `crashed`.** `sweep/runner.py` `run_session` sets
   `stopped = "complete"` before the loop over runs rather than after it, so an exception that leaves the loop is
   recorded as complete. The run records are unaffected (each attempt is written as it finishes); only the session
   summary's label is wrong. The record checks (§6.7) will show a `complete` session with 490 runs finished; this
   entry explains it.

Both are fixed after the last sweep, with tests, as a code commit of their own (no image change mid-run).
