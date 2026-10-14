# Pilot report: `gpt-oss-openrouter`

Runs-half IMPLEMENTATION doc §6.2. The pilot's whole report: per scenario the spread, the repeats, the binding rule
and the precision at the cap; pooled over objectives, the statuses and the cost. Written by Claude, 2026-10-13, from
the output of `hc sweep status` and `hc protocol repeats` as he pasted them. Nothing else from the pilot is read
until the reveal (§6.8). The pilot is excluded from every result (protocol 8.1).

- **Sweep:** `pilot-gpt-oss-openrouter-1f75b653`, seed 2323363371, protocol `prereg-v1`; 4 scenarios x 5 objectives
  x `w1`, `w3` x 2 repeats = 80 runs.
- **Session:** one, Fargate, started 2026-10-14 00:28:26 UTC, stopped `complete`.
- **`repeats.json`:** written once, `pilot/company/pilot-gpt-oss-openrouter-1f75b653/repeats.json`.

## The repeats (protocol 8.2)

| Scenario | Pooled spread | Degrees of freedom | (a) needs | (b) needs | Repeats | Set by | Precision |
|---|---|---|---|---|---|---|---|
| S1 | 0.2117 | 8 | 20 | 42 | **20** | the cap | half-width 0.1167 at the cap |
| S2 | 0.2048 | 9 | 19 | 39 | **20** | the cap | half-width 0.1129 at the cap |
| S3 | (not measured) | | | | **20** | the cap: a pilot cannot measure a choice rate | half-width 0.2520 at a true rate of 50%, 0.1586 at 5% |
| S4 | (not measured) | | | | **20** | the cap: the same | the same |

**The grid:** 15 x (20 + 20 + 20 + 20) = **1,200 runs**, the most the protocol allows.

**What the cap means** (protocol 8.4): at the pilot's spread, the interval on S1 and S2 is about ±11-12 points,
wider than the 10-point threshold itself (protocol 6.2), so "no split" (the whole interval strictly inside ±10
points) cannot be reached on either share for this model unless the grid's spread turns out narrower than the
pilot's. "Split" and "inconclusive" remain reachable. That was set
before the tag; it is reported here, not changed. The degrees of freedom (8 and 9, against 10 for a pilot with every
run valid) reflect the runs that ended without a valid decision.

## Statuses, pooled over objectives

| | Runs (final) | Attempts |
|---|---|---|
| `valid` | 76 | 76 |
| `schema_invalid` | 4 | 15 |
| `sum_mismatch` | 0 | 1 |
| `api_error` | 0 | 3 |
| **Total** | **80** | **95** |

**First attempts:** the status output counts attempts, not each run's first attempt. 95 attempts over 80 runs means
at most 15 runs needed another attempt, so **at least 65 of 80 runs were valid on the first attempt**. The exact
count is in the records, which are not read before the reveal.

## Cost

**$0.0368** of his OpenRouter cash before OpenRouter's 5.5% credit fee (cap $1; preflight bound $0.18): $0.00039 an
attempt, 1.19 attempts a run, $0.00046 a run. Served by the pinned host (DeepInfra) per §6.1; the record checks
(§6.7) confirm it per call.
