# Projection and re-plan check (Phase 5 search half §6; scope Delivers 1 and DoD 8)

Written by Claude, 2026-10-15 about 4:25 PM CDT, **before the search** (2026-10-16, by rule) and before any case
work. Committed before the search, so its time is the record that the check came first.

## The balances

His readings of **2026-10-15, about 10:30 AM CDT** (Phase 4 run log §6.9). **Nothing that costs money has run
since:** no model call and no sweep after the reveal; the SEC requests of the afternoon (search-half doc §11) are
free.

| Pot | Balance | Use in this projection |
|---|---|---|
| Anthropic prepaid credit | **$15.95** | extraction (Sonnet 5.5), Haiku 5.5's probes and case runs |
| OpenRouter, his cash | **$5.36** | the reader (Gemini 3.1 Pro), `gpt-oss-120b`'s probes and case runs |
| AWS credits (shared with Musical Mycelium) | about **$24.43** used since 2026-07-30 | Fargate for the probes and the case runs |

## The projection

Rates measured in Phase 4 (run log §6.9): Haiku 5.5 **$0.0016** a run, `gpt-oss-120b` **$0.00045** a run. A case
prompt is assumed to be up to twice the fictional one, so both are doubled. Prices read live 2026-10-15: Sonnet 5.5
$2 / $10 per million input / output tokens (Anthropic's models overview), Gemini 3.1 Pro $2 / $12 (OpenRouter's
models API).

| Item | Pot | Expected | Worst |
|---|---|---|---|
| Extraction: about 120,000 input and 8,000 output tokens a build, up to 8 builds | Anthropic credit | $2.60 | $5.00 |
| Recognition probes: 3 calls per model per set, up to 8 builds and 2 sets | credit and his cash | $0.10 | $0.30 |
| Independent reader: about 30 reads | his cash | $1.00 | $2.00 |
| Phase 5.5's case runs: 5 cases x 150 runs per model | credit $2.40, his cash $0.70 | $3.10 | $4.50 |
| Fargate for the probes and the case runs | AWS credit | $0.40 | $1.00 |
| **Phases 5 and 5.5** | | **about $7** | **about $13** |

## The checks

- **The $60 re-plan point and the $80 ceiling** (`planning/04` §3.4): cumulative spend to date is at most about
  **$28** (run log §6.9, every pot, overstated by Musical Mycelium's AWS use). After both phases: **about $35, at
  worst about $41.** **Passes.** No cut by `planning/05` §5.1 (the fifth case, then the fourth) is needed.
- **The Anthropic credit:** $15.95 less at most about $7.70 leaves at least about **$8.25**. Its workspace limit is
  $10 a month (resets 2026-11-01); October's draw so far is about $2.24 and this projection adds at most about $5 in
  October, so the limit holds.
- **His OpenRouter cash and his $5 cap** (Phase 3.5, 2026-10-09: OpenRouter capped at $5 in aggregate for every
  remaining use): about **$1** used since the cap was set; this projection adds at most about **$2.40**
  (reader, `gpt-oss-120b`'s probes and runs), about $3.40 in all. **Inside the cap**, and inside the $5.36 balance.
- **AWS:** inside the credits; no cash. The sweep-task cost tag (KNOWN-GAPS OPEN 2026-10-15) is proved at the first
  probe launch.

**Re-read before Phase 5.5's runs** (its Delivers 1), against that day's balances.
