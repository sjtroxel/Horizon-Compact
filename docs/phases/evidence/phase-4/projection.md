# Projection and re-plan check (Phase 4 runs half §6.3)

Written by Claude, 2026-10-13 about 9 PM CDT, after both pilots and before any grid. **Committed and pushed before
the first grid launch:** that commit's time is the record that the run set and the caps were fixed before any
official result existed (scope decision 2). Inputs: the two pilot reports in this folder, §6.1's thinking-on
measurement (`run-log.md`), and the readings of §6.0 step 3. No record of a decision was read.

## The fixed run set

| Sweep | Model | Runs | Sweep id | Seed |
|---|---|---|---|---|
| grid | `haiku-5-5` | 990 (S1 20, S2 6, S3 20, S4 20) | `grid-haiku-5-5-0b99fabb` | 541789037 |
| grid | `gpt-oss-openrouter` | 1,200 (20 everywhere) | `grid-gpt-oss-openrouter-fe599ad2` | 2451021948 |
| thinking | `haiku-5-5` | 100 (S1 x 5 x `w2` x 20) | `thinking-haiku-5-5-418caa9c` | 3422206995 |
| awareness | `haiku-5-5` | 15 | `awareness-haiku-5-5-0ce6ad12` | 1394052595 |
| awareness | `gpt-oss-openrouter` | 15 | `awareness-gpt-oss-openrouter-6a05acef` | 3046959125 |

The grid and thinking ids and bounds were computed offline by Claude from the harness's own `build_plan` and
`preflight_bound_usd` (no call, no record read); the launch dry runs must print the same ids.

## Measured rates (from the pilots)

| Model | Cost an attempt | Attempts a run | Cost a run |
|---|---|---|---|
| `haiku-5-5` | $0.1314 / 94 = $0.00140 | 94 / 80 = 1.175 | $0.00164 |
| `gpt-oss-openrouter` | $0.0368 / 95 = $0.00039 | 95 / 80 = 1.19 | $0.00046 |
| `haiku-5-5`, thinking on | about $0.0035 a run on S1 (§6.1's output, about 5,400 tokens, plus S1's longer input) | | |

## Expected cost, and each sweep's cap

Expected = runs x measured cost a run, plus 20% for retries. Cap = the preflight bound (every run at three attempts
at the full output allowance) rounded up, as the launch requires.

| Sweep | Expected | Preflight bound | Cap | Pot |
|---|---|---|---|---|
| grid, `haiku-5-5` | $1.63 + 20% = **$1.95** | $6.47 | **$7** (`--allow-over-cap`) | Anthropic credit |
| thinking, `haiku-5-5` | $0.35 + 20% = **$0.42** | $2.58 | **$3** | Anthropic credit |
| awareness, `haiku-5-5` | about **$0.03** | under $1 | **$1** | Anthropic credit |
| grid, `gpt-oss-openrouter` | $0.55 + 20% = $0.66, + 5.5% fee = **$0.70** | $2.73 | **$3** | his OpenRouter cash |
| awareness, `gpt-oss-openrouter` | about **$0.01** | under $1 | **$1** | his OpenRouter cash |
| Fargate and S3 | about **$0.40** | | | AWS credit |

**Phase 4 still to spend, expected:** about **$2.40 of the Anthropic credit**, about **$0.71 of his OpenRouter cash**,
about $0.40 of AWS credit. **Phase 5's estimate** (Phase 3.5 §23.4): real cases about $1.20 on Haiku and $0.35 on
`gpt-oss-120b`, extraction about $0.50.

## The four lines

1. **$60 re-plan point and $80 ceiling** (all spend, every pot). Even counting every caps' worst case (Anthropic $11,
   OpenRouter the whole $5 cap), all $24.03 of AWS credit used to date as if it were this project's alone (it is
   shared with Musical Mycelium), and Phase 5 at its estimate, the total stays under about $45. **Pass.**
2. **The Anthropic credit and the workspace's $10 a month.** The credit: about $17.90 left after the pilots (the
   $18.06 reading less §6.1's $0.03 and the pilot's $0.13), against $11 of caps and about $2.40 expected. **Pass.**
   The workspace: about $0.34 spent this month, so $9.66 of room; the grid's $7 cap fits. The thinking sub-study's
   $3 cap is checked against the room left after the grid's measured spend (expected about $7.70), not now; if
   a call were ever refused by the workspace limit, the session stops cleanly and resumes. **Pass, in launch order.**
3. **His OpenRouter cap, $5 in all since 2026-10-09.** Spent against it, from the logs: Phase 1 step 9 $0.0033, the
   failure proxy $0.0218, the pin check $0.0012, the protocol review $0.358, §6.1 $0.0035, the pilot $0.0368: about
   **$0.42** (about $0.45 with the fee). Caps still to come: $3 + $1 = $4, so at worst about $4.67 with the fee.
   **Pass, with about $0.33 left at worst; about $3.8 left at the expected spend.** Phase 5's $0.35 is checked
   against measured spend before Phase 5 runs. *His reading of the key's usage on OpenRouter replaces this tally if it
   differs.*
4. **AWS credit:** $135.97 remaining against about $0.40. **Pass.**

**Result: the re-plan check passes. No cut, no raise of any cap.**

## Time

Both pilots were complete when first checked, about 80 minutes after launch; their exact durations are in the
records. §6.4's limits stand: `--max-minutes` 300 for Haiku's grid, 720 for `gpt-oss-120b`'s. A session that stops is
resumed with the same command.
