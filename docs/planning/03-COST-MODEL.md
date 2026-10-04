# Horizon Compact — Cost Model

- **Status:** ESTIMATED 2026-10-02 from **AWS's own Price List files** (machine-readable, us-east-1; Bedrock
  foundation-model file published 2026-09-30, Bedrock file 2026-09-30, ECS file 2026-09-11) and his account checks
  the same day. Token volumes are estimates until the first real sweep measures them.
- **Read after:** `02-ARCHITECTURE`. **Read before:** `04-RISK-REGISTER`.
- *(2026-10-03: `07` §13 replaces §4's run-count assumptions; worst case about $71, about $57 at 10 repeats.)*
- **Amended by `08` (2026-10-03):** §4 development line, §6 a running spend cap and the per-sweep caps decided
  (patches P20, P21 in `09` §3; caps decided by him, `09` §6).
- **Patched 2026-10-04 (his), from Phase 0.5's smoke calls (`docs/phases/phase-0.5-aws-foundation-IMPLEMENTATION.md` §19):** §3.1 the tool-use input overhead, measured;
  §4 the development model named.
- **The one-line answer:** v1 should cost **roughly $50-110 in total**, almost all of it model tokens, inside the
  **$135.97** of credits he has left, which expire **2027-07-30** and are **shared with Musical Mycelium**. The
  biggest swing factor is whether the model "thinks" before answering (§3.3).

---

## 1. What the account has (his console, 2026-10-02)

| Item | Value |
|---|---|
| Credits remaining | **$135.97** of $160.00 issued ($24.03 used) |
| Credit expiry | **2027-07-30** (all four credits) |
| Plan | Paid plan |
| Models that work | **Claude Sonnet 4.6, Claude Haiku 4.5, Amazon Nova Pro** |
| Models denied | Claude Sonnet 5.5, Opus 5.5, Sonnet 5 (`AccessDeniedException`; applied quota 0) |
| Pending | Sonnet 5.5 quota requests (US cross-region: Support case opened; Global: pending). Musical Mycelium's last Bedrock quota case took 12 days. |

**The credits are one shared pot.** Musical Mycelium's eval runs draw on it too (about $15 for five eval episodes in
September). Every Horizon Compact dollar is a dollar Musical Mycelium cannot spend before July 2027.

## 2. Verified prices (AWS Price List, us-east-1)

### 2.1 Models, per million tokens

| Model | Route | Input | Output | Cache read | Cache write (5 min / 1 hr) | Batch in / out |
|---|---|---|---|---|---|---|
| **Claude Sonnet 4.6** | **US geo** (`us.`) | **$3.30** | **$16.50** | $0.33 | $4.125 / $6.60 | $1.65 / $8.25 |
| Claude Sonnet 4.6 | global | $3.00 | $15.00 | $0.30 | $3.75 / $6.00 | $1.50 / $7.50 |
| Claude Sonnet 5.5 *(if granted)* | US geo | $2.20 | $11.00 | $0.22 | $2.75 / $4.40 | not offered |
| Claude Sonnet 5.5 *(if granted)* | global | $2.00 | $10.00 | $0.20 | $2.50 / $4.00 | not offered |
| **Amazon Nova Pro** | standard | **$0.80** | **$3.20** | $0.20 | $0 | $0.40 / $1.60 |

Three things this table shows:
- **The US route costs 10% more than global** for Claude ($3.30 vs $3.00 input). He chose US for data residency;
  over v1 that premium is a few dollars. Worth knowing, not worth reversing.
- **Sonnet 5.5, if access arrives, is about a third cheaper than Sonnet 4.6.** Access would *save* money.
- **Nova Pro is about a quarter of Sonnet's price,** which makes it cheap to run as the second model family.
- **Claude on Bedrock is billed through AWS Marketplace,** listed under the model, not under "Amazon Bedrock."
  (Musical Mycelium's cost check was wrong by about 200x on 2026-09-19 for exactly this reason.)

### 2.2 Compute and network

| Item | Price | Source |
|---|---|---|
| Fargate, x86 | $0.04048 per vCPU-hour, $0.004445 per GB-hour | AWS Price List (ECS), verified |
| **Fargate, ARM (Graviton)** | **$0.03238 per vCPU-hour, $0.00356 per GB-hour** (about 20% less) | AWS Price List (ECS), verified |
| Fargate Spot | about 70% below on-demand | third-party figure, unverified; **not used in v1** (2026-10-03, `04` §3.6) |
| Public IPv4 address | **$0.005 per hour**, in use or idle | AWS Price List (VPC), verified |

**Use ARM.** The harness is pure Python with no native dependencies that need x86, and ARM is cheaper.

## 3. Token estimates per decision

### 3.1 What one decision contains

| Part | Tokens (estimate) | Cached? |
|---|---|---|
| Fictional company dossier | ~6,000 | **yes**, identical across every run |
| Real-case dossier | ~15,000 | **yes**, identical across that case's runs |
| Scenario, objective wording, shuffled lever menu, instructions | ~800 | no (varies per run) |
| Output: the decision form | ~300 | — |
| Output: the memo | ~400 | — |
| Output: thinking, if enabled | 0 to ~2,000 | — |
| *Added 2026-10-04:* tool-use input the API adds to every call | a few hundred (measured, below) | part of the prefix; *unverified* whether a cache point covers it on Converse |

*Measured 2026-10-04 (Phase 0.5):* the same short prompt and one-tool schema counted **716** input tokens on Sonnet 4.6,
**559** on Nova Pro and Nova Lite, and **235** on gpt-oss-120b. Tokenizers differ, so the difference is approximate,
but a fixed overhead of a few hundred input tokens per call exists on both official models and is not in the rows
above. Phase 4's measured tokens replace this whole table.

Caching is the reason the dossier costs little: after the first call, each re-read costs $0.33 per million tokens
instead of $3.30. Cache writes recur when the cache expires; a sweep that keeps calling within the window pays few
of them. The 1-hour cache option costs more to write but suits sweeps that pause.

### 3.2 Cost per decision on Sonnet 4.6 (US route)

| Case | No thinking (~700 output tokens) | With thinking (~2,700 output tokens) |
|---|---|---|
| Fictional company | about **$0.016** | about **$0.049** |
| Real case | about **$0.019** | about **$0.052** |

**Output tokens are most of the cost**, at five times the input price. That is why thinking matters so much.

### 3.3 The thinking decision (belongs to `07`, priced here)

**Decided 2026-10-03 (`07` §7.3):** thinking **off** for official runs, plus a thinking sub-study on one scenario
(about $5). `07` §13 also replaces §4's run-count assumptions: worst case about $71, which triggers the $60 re-plan.

Thinking can change *what the model decides*, not only what it costs, so it is a methods decision first.
Options for `07`:
- **Thinking off** for official runs: cheapest, and the memo already carries the reasoning readers see.
- **Thinking on at a fixed, recorded effort:** about three times the cost; possibly more considered decisions.
- **Both, as a finding:** run one grid cell both ways and publish whether thinking changes decisions. Cheap if kept
  to a subset.

## 4. The v1 budget

Assumptions, all adjustable in `07`: 4 scenarios x 5 objectives x 3 wordings x **10 repeats** = **600 decisions**
on the fictional company; **5** real cases x 5 objectives x 3 wordings x 10 repeats = **750 decisions**.

| Line | No thinking | With thinking |
|---|---|---|
| Fictional grid, Sonnet 4.6 (600) | ~$10 | ~$29 |
| Real cases, Sonnet 4.6 (750) | ~$14 | ~$39 |
| Second model family, Nova Pro, same 1,350 decisions | ~$10 | ~$10 |
| Recognition probes (every case x every model) | under $1 | under $1 |
| Dossier building (extraction from retrieved filing sections) | ~$5 | ~$5 |
| Development: harness testing, failed runs, re-runs (the development model named in Phase 0: local, or a cheap Bedrock model that is neither an official model nor on Musical Mycelium's billing lines; `09` A1. Not Haiku 4.5, `04` §3.3). *Named 2026-10-04 (his):* Ollama `qwen3.5:4b` (free) for volume, **Nova Lite** ($0.06 / $0.24 per million) for the Bedrock path | ~$15 | ~$20 |
| Fargate, IPv4, S3, ECR, CloudFront, logs | under $2 | under $2 |
| **Total, v1** | **about $55** | **about $105** |

The total sits **inside the $135.97**, but at the "with thinking" end it uses most of it, leaving little for Musical
Mycelium and nothing for later phases. **So the plan defaults to the low column** unless `07` finds a methods
reason for thinking, and the "both, as a finding" option is run on a subset only.

**If Sonnet 5.5 access arrives:** the Claude lines drop by about a third.

## 5. Options considered and rejected for v1

- **Bedrock batch inference (50% off for Sonnet 4.6).** *Verified 2026-10-02 in the AWS batch docs:* batch
  inference **does not support tool calling or structured output.** The decision form would have to come back as
  plain text and be parsed, a different measuring instrument from the on-demand runs. Mixing the two would add a
  confound between results; switching everything to batch would make decisions less reliable to capture. Savings
  of roughly $12-34 are not worth either. Reconsidered for the frequency study, where volume is far higher.
- **Global routing for the 10% discount:** his data-residency decision stands (2026-10-02).
- **Provisioned throughput or reserved capacity:** hourly charges (Nova Pro provisioned: $55-60 per hour). Never.
- **Bedrock-hosted embeddings and reranking for dossier building:** local models do this for free on his laptop; the
  dossiers are small. Revisited only if local quality is poor.

## 6. Cost safety, in layers

1. **The harness budget guard** (`02` §2.1): every sweep estimates its cost first and refuses to start above a cap,
   and **stops mid-sweep when its running cost reaches the cap** (added 2026-10-03, `08` §4.3). **Caps (decided
   2026-10-03, his, `09` §6): $5 per sweep during development, $25 per sweep for official runs**, overridable only
   by an explicit flag he types. Raised from the proposed $20 because `07` §13 puts the full fictional grid at about
   $19 before retries, which a $20 cap would likely refuse.
2. **AWS Budgets alarms in Terraform, on actual spend, filtered to this project's models** (revised 2026-10-03,
   `04` §3.3): the Sonnet 4.6 and Nova Pro billing lines, with thresholds tied to the $80 ceiling. **No forecast
   alerts on these:** on 2026-10-02 a forecast alert projected $9.17 for October while actual spend was $0.001,
   because the forecast extends past months' bursty eval spending. **Musical Mycelium's three account-wide budgets
   stay as they are** (his decision), as the net over the shared credit pot. **It must measure gross
   usage with credits excluded**, or it will read near $0 while credits silently drain (the Musical Mycelium
   2026-09-19 trap). *Verified 2026-10-03:* the setting is `IncludeCredit: false` in the budget's cost types, and the
   existing budgets already use it.
3. **A per-sweep cost record** in each sweep's manifest (`02` §2.12), so actual spend is measured, not assumed, and
   the published results can state what they cost.
4. **Nothing always-on** (`02` §3). Idle cost target: under $1 a month.
5. **A re-plan point at $60** of cumulative project spend (decided 2026-10-03, `04` §3.4): stop, compare measured
   spend to this document, and decide what to cut before continuing.
6. **The first official sweep is small on purpose:** one scenario, all five objectives, a few repeats. Its *measured*
   tokens replace every estimate in this document before the full grid runs.

## 7. Open items

**Decided 2026-10-03:** on-demand Fargate (no Spot); Horizon Compact's own actual-spend alarms filtered to its
models, Musical Mycelium's budgets untouched; a $60
re-plan point (`04` §8). Later the same day: per-sweep caps $5 development, $25 official (`09` §6).

**Decided 2026-10-02:** Horizon Compact spends **no more than $80** of the $135.97 in credits, keeping about
$55 for Musical Mycelium and contingencies. The harness caps and the Budgets alarm are set to respect it.

**Claude's checks still owed:**
1. ~~Fargate Spot price~~ moot: Spot is not used in v1 (2026-10-03).
2. ~~The AWS Budgets option that excludes credits~~ **closed 2026-10-03:** `IncludeCredit: false`, in use on the
   existing budgets.
3. ~~Sonnet 4.6 quotas~~ **closed 2026-10-03:** 10 requests and 6,000,000 tokens per minute (US geo and global);
   Nova Pro 25 requests and 2,000,000 tokens per minute cross-region. Requests are the binding limit (`04` §3.1).
4. Whether a newer non-Anthropic model than Nova Pro is available to his account (Nova Pro's published knowledge
   cutoff is October 2024; fine for the experiment, but dated).
5. Replace every estimate in §3-4 with measured numbers after the first small sweep.
