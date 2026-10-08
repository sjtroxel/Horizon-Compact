# Worked examples for the interval tests (Phase 3, step 3)

Read 2026-10-08 (Opus), for `tests/test_analysis_intervals.py`. The IMPLEMENTATION doc (§18 step 3) asked for
Newcombe (1998) Table II read from a live copy before any test was written against it.

## What could and could not be read

- **Newcombe (1998) itself** (Statistics in Medicine 17(8), 873-890): **not read.** The publisher's copy is
  paywalled, and the ResearchGate copy returned 403. The table was read through two reproductions instead.
- **Three Table II columns, as reproduced in the `pairwiseCI` R package's documentation**, which cites "Newcombe
  (1998), Table II, page 877, 10. Score, noCC" beside each value:
  <https://search.r-project.org/CRAN/refmans/pairwiseCI/html/pairwiseCImethodsProp.html>
- **Fagerland, Lydersen and Laake (2011)**, "Recommended confidence intervals for two independent binomial
  proportions", Statistical Methods in Medical Research. **Its equation 7** gives the hybrid score interval in
  closed form, and **its Table 3** gives a worked example. Read from
  <https://www.ms.uky.edu/~mai/sta635/FagerlandLydersenLaake2011---RecommendedCIsForTwoIndependent....pdf>, with text
  extracted locally (a throwaway `pypdf` run in the session's scratchpad, outside the project).

## The published values the tests hold

| Case | Source | Published 95% interval | statsmodels 0.15.0 |
|---|---|---|---|
| 56/70 − 48/80, Table II (a) | `pairwiseCI`, citing Newcombe p. 877 | 0.0524 to 0.3339 | 0.0524 to 0.3339 |
| 9/10 − 3/10, Table II (b) | same | 0.1705 to 0.8090 | 0.1705 to 0.8090 |
| 10/10 − 0/10, Table II (h) | same | 0.6075 to 1.000 | 0.6075 to 1.0000 |
| 7/34 − 1/34, estimate 0.18 | Fagerland et al. 2011, Table 3 | 0.019 to 0.34 | 0.0189 to 0.3404 |

## Every Table II column, at 95% and at the family level

Columns (c) to (g) were **not** read from a published copy. Their values come from statsmodels and from a
hand-written version of Fagerland's equation 7 (in the test file), which agree to within 1e-15 on every case at
both levels. That is agreement between two implementations of one formula, not a published check.

| Column | Counts | 95% | ALPHA = 0.003125 |
|---|---|---|---|
| (a) | 56/70 − 48/80 | 0.0524 to 0.3339 | −0.0233 to 0.3941 |
| (b) | 9/10 − 3/10 | 0.1705 to 0.8090 | −0.0253 to 0.8502 |
| (c) | 6/7 − 2/7 | 0.0582 to 0.8062 | −0.1377 to 0.8423 |
| (d) | 5/56 − 0/29 | −0.0381 to 0.1926 | −0.1506 to 0.2632 |
| (e) | 0/10 − 0/20 | −0.1611 to 0.2775 | −0.3039 to 0.4662 |
| (f) | 0/10 − 0/10 | −0.2775 to 0.2775 | −0.4662 to 0.4662 |
| (g) | 10/10 − 0/20 | 0.6791 to 1.0000 | 0.4435 to 1.0000 |
| (h) | 10/10 − 0/10 | 0.6075 to 1.0000 | 0.3407 to 1.0000 |

## The disagreement in the IMPLEMENTATION doc §3a, settled

§3a recorded that, on 6/7 − 2/7, statsmodels gave 0.0582 to 0.8062 against a recalled 0.0381 to 0.8384. **The
recall was wrong, not statsmodels:** −0.0381 is column (d)'s lower bound (5/56 − 0/29), misremembered onto
column (c). Column (c) from the formula is 0.0582 to 0.8062, matching statsmodels. Recall was not a source, as §3a
said; this is why the step began by reading.

## The bootstrap's checks (no published table exists for them)

- **Exact enumeration:** one wording, three runs a side (0, 0.5, 1 against 0, 0, 1). All 27 × 27 equally likely
  resamples are enumerated, and the 95% percentile interval at 100,000 resamples equals the exact quantiles, with a
  test that the cumulative probability is not within Monte Carlo error of the cut.
- **scipy:** `scipy.stats.bootstrap(method="percentile")` on one wording (unstratified), 100,000 resamples. Different
  generators draw differently, so the two agree within Monte Carlo error (0.006 at 95%, 0.012 at the family level),
  not exactly.
- **All agree:** identical runs on both sides give [0, 0]. Kept as a test on purpose; decision 10 settles what the
  engine does about it, from the simulations.
