# Pilot report: `haiku-5-5`

Runs-half IMPLEMENTATION doc §6.2. The pilot's whole report: per scenario the spread, the repeats, the binding rule
and the precision at the cap; pooled over objectives, the statuses and the cost. Written by Claude, 2026-10-13, from
the output of `hc sweep status` and `hc protocol repeats` as he pasted them. Nothing else from the pilot is read
until the reveal (§6.8). The pilot is excluded from every result (protocol 8.1).

- **Sweep:** `pilot-haiku-5-5-0b9d9e79`, seed 4096323239, protocol `prereg-v1`; 4 scenarios x 5 objectives x `w1`,
  `w3` x 2 repeats = 80 runs.
- **Session:** one, Fargate, started 2026-10-14 00:28:29 UTC, stopped `complete`.
- **`repeats.json`:** written once, `pilot/company/pilot-haiku-5-5-0b9d9e79/repeats.json`.

## The repeats (protocol 8.2)

| Scenario | Pooled spread | Degrees of freedom | (a) needs | (b) needs | Repeats | Set by | Precision |
|---|---|---|---|---|---|---|---|
| S1 | 0.1585 | 10 | 12 | 24 | **20** | the cap | half-width 0.0874 at the cap |
| S2 | 0.0619 | 10 | 3 | 5 | **6** | the floor | (cap not reached) |
| S3 | (not measured) | | | | **20** | the cap: a pilot cannot measure a choice rate | half-width 0.2520 at a true rate of 50%, 0.1586 at 5% |
| S4 | (not measured) | | | | **20** | the cap: the same | the same |

**The grid:** 15 x (20 + 6 + 20 + 20) = **990 runs.** The thinking sub-study takes S1's count: **100 runs**
(S1 x 5 objectives x `w2` x 20).

**What the cap means for S1** (protocol 8.4): at the pilot's spread, an interval of about ±8.7 points against the
10-point threshold (protocol 6.2), so "no split" on S1 is reachable only when the observed difference is within
about 1.3 points of zero. That was set before the tag; it is reported here, not
changed.

## Statuses, pooled over objectives

| | Runs (final) | Attempts |
|---|---|---|
| `valid` | 79 | 79 |
| `sum_mismatch` | 0 | 10 |
| `schema_invalid` | 1 | 5 |
| **Total** | **80** | **94** |

**First attempts:** the status output counts attempts, not each run's first attempt. 94 attempts over 80 runs means
at most 14 runs needed a retry, so **at least 66 of 80 runs were valid on the first attempt**. The exact count is
in the records, which are not read before the reveal.

## Cost

**$0.1314** of the prepaid Anthropic credit (cap $1; preflight bound $0.52): $0.0014 an attempt, 1.175 attempts a
run, $0.0016 a run.
