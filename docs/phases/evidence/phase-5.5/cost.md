# Measured cost (Phase 5.5 §6.8)

Written by Claude, 2026-11-03 about 7:40 AM CST, from his readings of the three bills that morning (the Anthropic
Console's billing page, OpenRouter's credits page, AWS's billing home, credits page, cost allocation tags and Cost
Explorer) and the run log's recorded totals. Set against Phase 5's measured cost (`../phase-5/cost.md`, 2026-10-26),
the $60 re-plan point and the $80 ceiling (`planning/04` §3.4).

## The balances

Phase 5's reading (2026-10-26 about 5:57 PM CDT) is the start. No model call was made between it and §6.0's reading
(2026-10-29), which found the same two model balances, so K1-K5 cost nothing.

| Pot | 2026-10-26 | Added since | 2026-11-03 | Drawn |
|---|---|---|---|---|
| Anthropic prepaid credit | $11.96 | none | $11.00 | **$0.96** |
| OpenRouter, his cash | $3.70 | none | $3.46 | **$0.24** |
| AWS (shared with Musical Mycelium) | October to date $0.44 for the whole account | | October in full $0.60; November to date $0.01 | **at most $0.17** |

The AWS figure is the whole account's, so it overstates this project's draw. AWS credits remaining: $135.38
(estimated $135.37), expiring 2027-07-30. No AWS cash.

## Against the records

| Pot | Recorded | Bill | Difference |
|---|---|---|---|
| Anthropic | $0.8518 (five Haiku sweeps, `hc sweep status --case`) + $0.0817 (the memo scan's Haiku pass, §6.5) = $0.9335 | $0.96 | about $0.03 more on the bill, **not traced** (the Console's daily cost page was not read) |
| OpenRouter | $0.2155 (five `gpt-oss-120b` sweeps) + $0.0247 (the reader's four memo reads, §6.5) = $0.2402 | $0.24 | none to the cent |
| AWS Fargate | (tasks record no dollars) | $0.08 under `Project` = `horizon-compact` (2026-10-29 $0.05, 2026-10-30 $0.03, nothing after) | |

## The cost tag

Read the same morning. `Project` is **Active** as a resource cost-allocation tag (activated 2026-10-04, 17:19
UTC-05:00); the IAM-principal `Project` tag is inactive and not needed. Cost Explorer, 2026-10-29 to 2026-11-02 daily,
grouped by tag `Project`, filtered to Elastic Container Service, charge type Credit excluded, unblended: **one row,
`horizon-compact`, $0.08**, and no "No tag key" row. **The case sweeps' Fargate cost is under `horizon-compact`**,
which closes the cost-tag CARRIED entry (KNOWN-GAPS, was OPEN 2026-10-15). Refund was not excluded; at these amounts
it changes nothing.

## Against the projection

| | Projected (Phase 5's `cost.md`, the IMPLEMENTATION doc §12, K4) | Measured |
|---|---|---|
| Case runs, Anthropic credit | about $2.40 | $0.85 |
| Case runs, his OpenRouter cash | about $0.70 | $0.22 |
| Memo scan, Haiku pass | about $0.20 to $0.30 | $0.08 |
| Memo scan, the reader (his cash) | $1 to $6 (K4) | $0.02 (4 reads; every other flagged memo already held with its dossier) |
| Fargate (AWS credit) | under $1 | $0.08 (at most $0.17 for the whole account) |
| **Phase 5.5** | **about $3.10, worst $4.50, plus the memo scan** | **about $1.28, at most $1.37** |

## The checks

- **Cumulative project spend:** at most about $45 to 2026-10-26 (`../phase-5/cost.md`), plus at most $1.37: **at most
  about $46.** Under the **$60 re-plan point** and the **$80 ceiling.** Passes. It overstates: it counts the shared
  AWS account's whole use.
- **What is left for Phases 6 to 7** (the ROADMAP estimates under $2 and $0): Anthropic $11.00, his OpenRouter $3.46,
  AWS credits $135.38. No cut by `planning/05` §5.1 is needed.
