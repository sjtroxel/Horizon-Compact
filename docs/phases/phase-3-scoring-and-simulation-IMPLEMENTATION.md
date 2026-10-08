# Phase 3 — Scoring and Simulation: IMPLEMENTATION (v0.3)

> **IMPLEMENTATION doc.** Written 2026-10-08 (Opus) from the approved scope doc
> (`docs/phases/phase-3-scoring-and-simulation.md`, both decisions as recommended), `planning/07` (all of it, as
> patched through 2026-10-07), `planning/08` §3.4-3.5 and §4.5, `planning/09` A5, `planning/05` §4.3 and §5,
> `planning/04` §1.2, §1.5 and §6.2, the Phase 1.5, 3.5, 4 and 5.5 scope docs (what they expect from this phase), the
> Phase 2.5 IMPLEMENTATION doc §22 (its close-out), the harness as built (`experiment.py`, `sweep/decision.py`,
> `sweep/classify.py`, `sweep/runner.py`, `sweep/plan.py`) and the four rendered scenarios under
> `experiment/company/scenarios/`. **APPROVED 2026-10-08 (his), all ten decisions in §17 as recommended.**
>
> **Built out of order**, like Phases 2 and 2.5: Phase 1 (steps 3, 9, 11, 12) and Phase 1.5 wait on AWS. This phase
> needs no AWS and calls no model. One of its prerequisites, Phase 1.5's scorer, does not exist; §3 item 1 and
> decision 1 deal with that.

## 1. Where things stand on 2026-10-08, before this phase

What was done, what was not, and what is still waiting, so this doc starts from the record and not from memory.

**Done and committed.** Phase 2.5 closed 2026-10-07; its close-out commit `6c8240f` is pushed and green (CI
`37714513948`, Deploy `37714513935`). That run id is the one Phase 2.5's DoD 8 row was waiting for; it goes into that
doc with this doc's commit (§15, C1). The sealed template is `w2`. The four scenarios, the objectives and the three
templates are final unless Phase 3.5's review or the Nova Lite runs reopen them (both go through the change log).

**Not done, because of AWS** (the BLOCKED entry in `KNOWN-GAPS.md`):
- **Bedrock is still throttled.** One call each, 2026-10-08 13:55 UTC (`scratch/throttle-check.py`): Nova Lite and
  Sonnet 4.6 both `ThrottlingException`, "Too many tokens per day" (request ids `9b94c7e7-2ba2-45f4-a07a-2c4a9b06b833`
  and `75959270-171d-4285-aeda-22909f50e8e6`), $0. Case 179121856900232: no reply. He will not buy paid support.
- **Phase 1:** steps 3 (the Nova Lite development run) and 9 (the skeleton sweep), then 11 and 12, so Phase 1's close
  and the first test of the task role's Bedrock and S3 permissions.
- **Phase 1.5, all of it:** it needs Phase 1's sweep results in S3. Its scorer, which this phase was to extend, is
  unbuilt.
- **The Nova Lite probes and format runs**, a prerequisite of Phase 3.5's tag (the OPEN entry, 2026-10-07).
- **Probably Musical Mycelium's Bedrock calls** too; still unchecked.

**Not done, and not blocked by the quota:** **Phase 0.5's billing close-out** (the WAITING entry, 2026-10-04): about
15 minutes of his console, the tag measurement, the Sonnet 4.6 budget's service name, the phase's spend read from the
bill, then one `terraform apply` and its DoD audit. It needs posted billing data, which has existed since 2026-10-06.
It can run any day, alongside this phase; it is his console, so it is his call when.

**What this phase does not need from any of that:** nothing. No AWS, no model, no run record from any sweep.

## 2. What this phase delivers

The analysis that turns runs into verdicts, written once, tested on synthetic data with known answers, and the
simulations whose numbers Phase 3.5's protocol quotes. In build order:

1. **The run reader:** run records (the attempt and final objects `sweep/runner.py` writes) into typed rows, one per
   run, from any `Store`. Refuses development records on real content (decision 8).
2. **The outcomes:** each scenario's primary outcome, secondaries and lever-level vector, from the rendered scenario
   files, never hard-coded amounts (§6).
3. **The intervals:** Newcombe's interval from statsmodels; the stratified bootstrap as a short routine on numpy
   (decision 2 of the scope doc; §7).
4. **The verdict engine:** for each comparison, the difference, its interval, and one of split, no split or
   inconclusive (§8).
5. **The failure rules:** rates per cell, the 10% exclusion, first-attempt beside final, the worst-case bound (§9).
6. **The robustness rules:** the per-wording direction check, the sealed-wording result, position effects (§10).
7. **The descriptive analyses** of `planning/07` §6.5, fixed in code (§11).
8. **The repeat rule:** from a pilot's runs to repeats per scenario, showing no direction (§12).
9. **The matcher:** per-run distance, the tie rule, minimum evidence, the no-match threshold (§13).
10. **The simulations**, seeded, with a results file and a summary the protocol quotes (§14).
11. **A plain-English account of the statistics** (`planning/04` §6.2), written as each part is built.

**Not delivered here, moved by decision 1:** the static JSON and its schema version (scope doc Delivers 8). This
phase delivers a versioned results object; Phase 1.5's scorer serializes it.

## 3. What writing this doc found

1. **Phase 1.5's scorer does not exist.** The scope doc's Delivers 8 ("the scorer extended ... under a new schema
   version") and its prerequisite *(rests on 1.5)* assumed Phase 1.5 would be built first. AWS has blocked it, and
   `grep` finds no scorer, no DuckDB and no JSON schema in `src/`. Decision 1: the engine is a library with a versioned
   results object, and the JSON stays Phase 1.5's.
2. **The worst-case bound protects one verdict and not the other.** `planning/07` §5.2 sets failed runs to the
   extremes "in the direction that most narrows the difference" and downgrades a **split** if that overturns it.
   Nothing does the same for **no split**: a "no split" with failed runs is never checked against the direction
   that would widen the difference. "No split" on C vs D is the verdict in the Roundtable's favor, so the rule as
   written guards against a false finding on one side only. The project tests a claim and does not argue for one
   (`planning/06` §1), so this is a fairness gap, not a detail. Decision 3.
3. **The simulations as scoped measure false splits but not false "no splits."** The scope doc asks for power, the
   false-split rate and whether "no split" is reachable. It does not ask how often the rule says "no split" when a
   real difference of the threshold's size exists. With a bootstrap that runs narrow at small samples, that error is
   the likelier one. Decision 4 adds it, with the same target as the false-split rate.
4. **The bootstrap has the same all-agree failure as the one Newcombe fixed, now on a share.** `planning/07` §6.3
   moved choice rates to Newcombe because a bootstrap gives a zero-width interval when every run agrees. **S1's share
   is now a count of people out of 125** (decision 8 of Phase 2.5), and a model that keeps all 125 on every run, or
   eliminates all 125, gives every run the same share. Under two objectives that both do it, the bootstrap returns
   [0, 0] and declares "no split" with false certainty: the exact failure `planning/08` §3.4c found, on the scenario
   that carries the Roundtable test. The simulations test it (the scope doc already lists the all-agree case for
   both methods); decision 10 agrees now how the fix is chosen, so it is not chosen later.
5. **S1's secondary outcome can be undefined.** The share of moved people who keep their pay divides by the people
   moved; a run that moves nobody has no value. It is reported among runs that moved anyone, with that count beside
   it (§6.1).
6. **An excluded cell breaks like-with-like.** A cell is one objective under one wording. If A's `w3` cell passes 10%
   failures and is excluded, A vs C would compare A on two wordings against C on three, which `planning/07` §7.1
   exists to prevent. Decision 6.
7. **"99.7%" needs to be one exact number.** `planning/07` §6.3 says "0.05 / 16 ≈ 0.003," and §8 uses 2.96. Bonferroni
   over 16 is exactly 0.003125, a 99.6875% interval (z = 2.955); 0.003 is 99.7% (z = 2.968). The difference is small
   but the code must freeze one. Decision 7.
8. **How each objective's mean is formed is unstated.** With no failures, the mean of all runs and the mean of the
   three per-wording means are the same number. With failures they differ, and the second keeps every wording's
   weight equal, as "wordings are treated as fixed" (§6.3) implies. Decision 5.
9. **Analysis must never touch the Phase 2.5 runs.** `scratch/runs/development/company/` holds the format runs, by
   objective. Both honor statements (Phase 2.5 §22.3) say no allocation by objective was seen; running this engine
   on those records would show exactly that. A rule in memory is not enough. Decision 8 makes it a refusal in code.
10. **Phase 3.5 freezes the analysis code by hash** (its decision 1). So the analysis lives in one package, with
    nothing it needs outside it except the scenario loader, and the library versions are pinned by `uv.lock`. A
    seeded numpy generator's output can change between numpy versions, so "re-run from the committed code and seeds"
    means with the locked versions (§16).
11. **The run records already carry what robustness needs.** Each attempt stores `menu_order`, `option_order`,
    `validation.amounts`, `validation.scaled_amounts`, `validation.choice`, `status` and `possible_decline`; each final
    stores `status` and `first_attempt_status`. No run-code change is needed for analysis. One gap is noted for
    Phase 4, not fixed here: the planner takes one repeat count for the whole sweep, and the repeat rule gives one per
    scenario (§12).
12. **The `possible_decline` flag matches S4's own option name.** Phase 2.5 §22.4 recorded that the flag fires on the
    word "decline." For analysis it matters little: a refusal and a failure count the same toward exclusion and the
    worst-case bound, and differ only in which column of the published table they sit in. A run is counted as a
    refusal only when its final status is `refusal` or a logged human call says so (§9.1). The flag itself is run
    code; it gets an OPEN entry for Phase 4, not a change here.

## 3a. Checks run while writing this doc (live, 2026-10-08)

- **Library versions, from PyPI:** numpy 2.5.3 (2026-09-06), scipy 1.18.1 (2026-08-21), statsmodels 0.15.0
  (2026-08-27), pandas 3.0.6 (2026-09-17, a statsmodels dependency), patsy 1.0.3 (2026-08-29). Each supports Python
  3.13 and is more than two weeks old. The build pins them by `uv.lock`; versions are re-read on the build day.
- **statsmodels' Newcombe interval:** `statsmodels.stats.proportion.confint_proportions_2indep(..., method="newcomb",
  compare="diff", correction=False)` exists in 0.15.0. Run in a throwaway environment at 95% on eight two-sample
  examples, it agreed with the values Opus recalled from Newcombe (1998), Table II, on seven of eight
  (56/70 − 48/80: 0.0524 to 0.3339; 9/10 − 3/10: 0.1705 to 0.8090; 0/10 − 0/20: −0.1611 to 0.2775; and so on). On
  6/7 − 2/7 it gave 0.0582 to 0.8062 against a recalled 0.0381 to 0.8384. **Recall is not a source:** step 3 reads the
  published table from a live copy before any test is written against it (§18).
- **scipy's bootstrap** has no stratified mode (`scipy.stats.bootstrap` takes `data`, `n_resamples`, `paired`,
  `method`, `rng`, and so on). So the stratified bootstrap is a short routine, cross-checked against scipy's
  percentile method on unstratified data (§7.2).
- **uv 0.12.0** has `--no-default-groups` and `--group`, which decision 2 relies on.

## 4. Layout

```
src/horizon_compact/analysis/          the frozen analysis code (Phase 3.5 hashes this folder)
    __init__.py                        the version of the results object (RESULTS_VERSION)
    records.py                         run records -> RunRow; the refusal of development records on real content
    outcomes.py                        per-scenario primary outcomes, secondaries, lever-level vectors
    intervals.py                       Newcombe (statsmodels) and the stratified bootstrap
    verdict.py                         the comparisons, the three verdicts, the estimand
    failures.py                        rates, exclusion, first attempt beside final, the worst-case bound
    robustness.py                      wording direction, sealed wording, position effects
    descriptive.py                     planning/07 section 6.5
    repeats.py                         the repeat rule from a pilot's runs
    matcher.py                         per-run distance, tie, minimum evidence, no match
    results.py                         the results object for one model's sweep
src/horizon_compact/simulation/        generators and the simulation runner (not frozen; it produces evidence)
tests/test_analysis_*.py               known-answer tests, one file per module
docs/phases/evidence/phase-3/
    simulation-results.json            every simulated number, with its seed and replicate count
    simulation-summary.md              the same, in tables the protocol quotes
    matcher-calibration.md             the matcher's synthetic cases and the thresholds set from them
    worked-examples.md                 the published examples the interval tests use, with their sources
    plain-english.md                   the statistics explained without formulas, then with them
```

The `simulation` package is outside `analysis` on purpose: it may change after the tag without changing a verdict,
and Phase 3.5 can hash `analysis/` alone. Simulations import the analysis; the analysis never imports the simulation.
A test enforces the direction (as `tests/test_architecture.py` already enforces other boundaries).

**CLI:** `hc simulate run [--quick]` and `hc simulate report`. There is **no** `hc analyze` command in this phase:
the only way to point the engine at real records arrives with Phase 4's IMPLEMENTATION doc, under decision 8's refusal.

## 5. The dependencies (decision 2)

- **numpy, scipy, statsmodels** (pandas and patsy come with statsmodels) in a new dependency group, **`analysis`**,
  added to `[tool.uv] default-groups` so `make install`, `make check` and CI get it with no workflow change.
- **The container image does not get it.** On both of the Dockerfile's `uv sync` lines, `--no-dev` becomes
  `--no-default-groups` (which leaves out `dev` and `analysis` alike); the image runs sweeps and never analysis (`planning/02` §2.11: aggregation
  is on the laptop). This is a Dockerfile change, so the image digest changes on the next deploy. Tested by building
  the image locally and checking that `import numpy` fails inside it.
- **mypy strict:** numpy and scipy ship types; statsmodels does not. One `[[tool.mypy.overrides]]` entry,
  `ignore_missing_imports` for `statsmodels.*` only, and the one call to it wrapped in a typed function in
  `intervals.py`.
- **`pyproject.toml`'s comment** ("each runtime dependency arrives with its subject") gains a line: the analysis
  group arrives with Phase 3.

## 6. The outcomes, scenario by scenario

All amounts are read from `validation.scaled_amounts` when the run is `valid_rescaled`, otherwise from
`validation.amounts` (`planning/07` §2.4 item 3: within 1% the table is scaled to balance, and the scaled table is the
decision). Every key and total below comes from the rendered scenario file through `experiment.py`, never typed into
the analysis. Analysis runs on `valid` and `valid_rescaled` runs only; everything else is a failure (§9).

### 6.1 S1 (125 people; `split_equals_headcount`)

- **Primary: share kept** = (`move_plant_pay` + `move_keep_pay`) / 125. A share outcome, threshold 10 points, by
  bootstrap. Values lie on a grid of 1/125.
- **Secondary (descriptive): share of moved people who keep their pay** = `move_keep_pay` / (`move_plant_pay` +
  `move_keep_pay`), among runs that moved anyone; the count of such runs is reported beside it.
- **Lever-level vector:** the three paths, each divided by 125.

### 6.2 S2 ($112.1 million; `bearers_equal_total`)

- **Primary: share borne by the workforce** = (`eliminate_roles` + `cut_wages_hours`) / total. A share outcome,
  threshold 10 points, by bootstrap.
- **Lever-level vector:** the seven offered bearers, each divided by the total. The two not offered (`payouts`,
  `keep_people`) are not in it.

### 6.3 S3 (190 people; a choice plus `split_equals_headcount`)

- **Primary: the close rate**, the share of runs whose `plant_decision` is `close`. A choice rate, threshold 20 points,
  by Newcombe.
- **Descriptive:** the three-way choice split; the people split (`eliminated`, `moved_other_plants`, `kept_at_plant`,
  `transferred_to_buyer`) by choice; the share retained (everything but `eliminated`, over 190).
- **Lever-level vector:** the four people lines, each divided by 190, plus the choice (for the matcher, §13).

### 6.4 S4 ($20.4 million; a choice plus `uses_equal_total_plus_sources`)

- **Primary: the fund rate**, the share of runs whose `program_decision` is `fund`. A choice rate, threshold 20 points,
  by Newcombe.
- **Secondary (descriptive):** where the money went (each use); whether funding came with cuts (any source above zero,
  among `fund` runs) and from whom (each source); the same for `decline` runs, since the cuts are offered under both.
- **Lever-level vector:** every offered line, uses and sources together, each divided by the run's sum of all offered
  lines. Uses alone would miss the cuts; sources alone would miss the program. Decision 9.

### 6.5 The canonical levers

Each scenario line carries its `lever` (L1-L9) in the scenario file. The descriptive analyses group by it (and by
`planning/07` §3.3's display groups); the matcher never does (§3.3: the groups overlap).

## 7. The intervals

### 7.1 Newcombe, for choice rates

statsmodels' `confint_proportions_2indep(count1, nobs1, count2, nobs2, method="newcomb", compare="diff",
alpha=ALPHA, correction=False)`, on counts pooled across wordings (decision 5). Wrapped in one typed function. Tested
three ways: against the published worked examples at 95% (read live, §3a), against a hand-written version of the
same formula (Wilson score intervals for each proportion, combined as Newcombe's method 10) at 95% and at `ALPHA`, and
at the edges (0 of n, n of n, both groups at 0%, both at 100%), where it must give a non-zero width.

### 7.2 The stratified bootstrap, for shares

For a comparison of objectives X and Y on one scenario:
1. Within each objective, within each wording, draw that cell's valid runs with replacement, the same number as the
   cell holds.
2. Compute the estimand (decision 5: the mean of the per-wording means) for X and for Y, and their difference.
3. Repeat `B` times (decision 7); the interval is the `ALPHA / 2` and `1 − ALPHA / 2` quantiles of the differences
   (the percentile method, which can be explained in one sentence).

Vectorized on numpy, one `numpy.random.Generator` (PCG64) per comparison, seeded from the sweep id and the comparison's
name (decision 7), so no one chooses a seed. Tested: against `scipy.stats.bootstrap(method="percentile")` on
unstratified data with matching seeds where the APIs allow, otherwise within Monte Carlo error; on a hand-checkable
case (two objectives, one wording, three runs each); and the resample count's own Monte Carlo error at the interval's
ends, measured at `B` = 10,000 and 100,000 (§14.3).

### 7.3 Where each method applies

Shares (S1, S2, and every secondary share): bootstrap. Choice rates (S3, S4): Newcombe. The degenerate share case
(decision 10) is the one place this may change, by a dated patch to `planning/07` §6.3 with the simulation's evidence.

## 8. The verdict engine

### 8.1 The comparisons

Per model and scenario: **A vs C, A vs B, C vs D, B vs D** (primary, 4 × 4 = 16 per model); **A vs D** (secondary,
labeled as the expected comparison, the same computation, not in the family); **E vs each** (descriptive distance,
§11). The sign convention is fixed: difference = first named minus second named (A − C, A − B, C − D, B − D, A − D).

### 8.2 The three verdicts (`planning/07` §6.2)

With `T` the threshold (0.10 for shares, 0.20 for choice rates), `d` the observed difference and `[lo, hi]` its
interval:
- **Split:** `lo > 0` or `hi < 0`, **and** `|d| ≥ T`.
- **No split:** `−T < lo` and `hi < T` (the whole interval strictly inside ±T).
- **Inconclusive:** anything else.

A boundary value counts against the stronger verdict (an interval end exactly at ±T is not inside; exactly at 0 does
not exclude it). Written as one function over (`d`, `lo`, `hi`, `T`), tested on every boundary.

### 8.3 What the engine returns per comparison

The difference, the interval, the method, `ALPHA`, `B` and seed (for the bootstrap), the valid run count on each side
by wording, the verdict among valid runs, the worst-case-bound verdict (§9.4), the wording-direction label (§10.1),
the final verdict after both, and the reason for any downgrade. Every field is in the results object, so a reader
sees why a verdict is what it is.

## 9. The failure rules (`planning/07` §5.2)

### 9.1 Counting

From each run's final record: `valid` and `valid_rescaled` are valid; `refusal` is a refusal; every other model status
is a failure by type. `api_error` and `config_error` are never a final status (the runner's rule). **A refusal is
also a run whose final status is `no_tool_call` and which a human call, logged in a file beside the sweep, judges an
explicit decline** (`planning/07` §5.1: "applied by code where possible and by a logged human call otherwise"). The
`possible_decline` flag only lists candidates for that call; it never decides one.

### 9.2 Rates and the 10% exclusion

Per cell (model × scenario × objective × wording): runs attempted, valid, rescaled, failed by type, refused, and the
final failure rate including refusals. A cell above 10% is **unreliable**: reported, and excluded from the primary
comparisons with its reason. By decision 6, its wording is dropped from **both** sides of every comparison it is in,
and the verdict says "over wordings w1 and w3" (for example). A comparison left with no wording is "not assessable."

### 9.3 First attempt beside final

Every outcome is computed twice: on final results, and on first attempts only (runs whose first attempt was valid,
using that attempt's amounts). The first-attempt verdicts are descriptive, beside the final ones.

### 9.4 The worst-case bound (decision 3)

For each comparison with failed or refused runs on either side: set each failed run's outcome to 0 or 1, in the
direction that most narrows the difference, and recompute the **whole verdict** (interval included). If a split
becomes anything else, the comparison is **inconclusive**, with the reason. Under decision 3 (a), also the direction
that most widens it: if a no split becomes anything else, the comparison is **inconclusive**. A comparison with no
failed runs is untouched. For choice rates, 0 and 1 mean the run did not or did make the choice; for shares, the
share's own extremes.

### 9.5 Whether failures differ by objective

A descriptive table per scenario: each objective's failure and refusal rate, pooled over wordings, with a Newcombe
interval for each pair. No verdict (`planning/04` §1.7 asks for it reported, not tested).

## 10. The robustness rules

### 10.1 Wording (`planning/07` §7.1)

For a split: the difference under each wording separately, same sign convention. **Robust** if every per-wording
difference has the pooled difference's sign and is not zero; otherwise **wording-sensitive**, with each wording's
difference shown. For S3 and S4 the direction is the close or fund rate's. "No split" and "inconclusive" carry the
per-wording differences too, descriptively.

### 10.2 The sealed wording

The whole verdict computation repeated on the sealed template's runs alone (`w2`, read from `objectives.toml`, never
typed), labeled "sealed wording only," outside the family of 16.

### 10.3 Position effects (`planning/07` §7.2)

Each attempt records `menu_order` and `option_order`. Per scenario, descriptive only:
- **levers:** each line's mean share of its scenario's total by its position in the menu (1 to k), and the slope of a
  least-squares line through the run-level points, with the run count;
- **options (S3, S4):** each option's choice rate when it was listed first, against when it was not, with a Newcombe
  interval.
No verdict. If a position effect is visible, it is published; shuffling already spreads it across objectives.

## 11. The descriptive analyses (`planning/07` §6.5)

Fixed in code before any result exists, outside the family:
1. **The full allocation:** every offered line's mean, standard deviation, median and range, per scenario, per
   objective, per wording and pooled; with per-run values kept in the results object, so spread can always be drawn
   (`planning/06` §7.3).
2. **The display groups** (`planning/07` §3.3), summed per run, labeled as overlapping.
3. **Where the money went:** the same as 1 for S2's bearers and S4's uses and sources, with S4 split by choice.
4. **S3's three-way split** of choices and its people lines by choice; **S4's funding sources** among `fund` runs and
   among `decline` runs.
5. **E's distance to each objective:** the mean over all pairs (one E run, one run of the other objective) of the
   matcher's per-run distance (§13.1) on the full lever-level vector, **reported beside each objective's own
   distance to itself** (the mean over pairs of its own distinct runs). Without that reference, a large distance could
   be only spread.
6. **Position effects** (§10.3) and **first attempt beside final** (§9.3).
7. **S1's and S4's secondaries** (§6.1, §6.4).

## 12. The repeat rule (`planning/07` §8)

Input: a pilot's runs (Phase 4: two development wordings, two repeats, every scenario and objective). Output, per
scenario, and nothing else:
- **Shares (S1, S2):** the pooled standard deviation of the primary outcome over the scenario's cells (sum of squared
  deviations from each cell's mean, over the sum of each cell's runs minus one; a cell with one valid run adds
  nothing), its degrees of freedom, then n from (a) and (b), each rounded up, the larger, clamped to [6, 20], and
  **the achieved precision** (the interval half-width at that n) when the cap binds.
- **Choice rates (S3, S4):** 20, the cap, with the achieved precision at rates of 50% and 5%.

The output carries no mean, no difference and no objective label, so computing the repeats shows no direction
(Phase 4 decision 1's concern). Tested against `planning/07` §8's worked example (sd 0.15 gives 10 and 21, so 20;
sd 0.10 gives 5 and 10, so 10), with the `z` that decision 7 fixes. **For Phase 4, noted in `KNOWN-GAPS.md`:** the
planner takes one repeat count; the grid needs one per scenario.

## 13. The matcher (`planning/07` §10.4)

### 13.1 The per-run distance

Between one run and the company's actual decision, on the case's **observable** dimensions only:
- the lever-level vector (§6), restricted to the observable lines and renormalized to sum to 1 on each side; the
  **total variation distance** (half the sum of absolute differences, 0 to 1). If either side's observable lines sum to
  zero, that side's money dimension is undefined and the run is distanced on the choice alone (recorded);
- the choice, where there is one and it is observable: 0 if the run made the company's choice, 1 if not;
- where both exist, their mean with equal weight.

An objective's distance is the mean of its runs' distances (§10.4 item 3). Five distances per case per model, each
with a bootstrap spread (runs resampled within wording, as §7.2).

### 13.2 Tie (decision 9)

Between the two nearest objectives: the gap's bootstrap distribution (both objectives' runs resampled together, so
the gap is computed on the same resample). **Tie** if its central 95% interval includes zero. 95% and not 99.7%: a
match is a reading, not a test (`planning/07` §6.4).

### 13.3 No good match, and minimum evidence (set by simulation, §14.2)

- **No good match:** the nearest objective's distance is above a threshold `D*`. `D*` is set from synthetic cases
  where the company's decision is drawn from the same distribution as one objective's runs (a true match): `D*` is
  the 95th percentile of the nearest distance across those cases at the largest simulated spread, so a true match is
  called "no good match" at most 5% of the time at the worst spread. Then checked: "opposite" cases must exceed `D*`
  in at least 95% of trials, and the result recorded either way.
- **Minimum evidence:** a case is "not enough disclosed to match" when its observable dimensions are fewer than `k*`,
  the smallest number at which, in synthetic cases, the generating objective is nearest (or tied with the nearest)
  in at least 80% of trials at the design spread. The choice counts as one dimension; each observable line counts as
  one.
- **Alternative readings** (`planning/07` §10.4 item 6): the matcher takes the rubric's uncertain calls as alternative
  company decisions and runs once per reading; "depends on reading" when the nearest objective changes. Tested on a
  synthetic rubric.

### 13.4 The synthetic cases

The four the planning names, plus the true match above. Built per scenario shape, from **randomly drawn objective
profiles** (each objective's runs drawn around a Dirichlet-drawn mean allocation, with a choice rate drawn uniformly),
never from a guess at how any objective behaves:
1. **Identical:** the company's decision equals one objective's mean allocation and modal choice.
2. **Opposite:** the company puts its money where that objective puts least, and makes the other choice.
3. **Same choice, opposite money:** the choice matches; the allocation is opposite.
4. **Sparse disclosure:** the identical case with only 1, 2, 3 ... observable dimensions (this sets `k*`).
5. **True match:** the company's decision is one more draw from one objective's run distribution (this sets `D*`).

Every case, its seed and the matcher's output go into `matcher-calibration.md`.

## 14. The simulations

### 14.1 The verdict rule

Synthetic runs for two objectives, three wordings each, with stated distributions and seeds. **No parameter is
taken from any run, the dossier or a guess at the answer** (scope doc finding 2); the ranges span the plausible.

- **Shares.** Per-run outcome in [0, 1] from a Beta distribution with mean `μ` and standard deviation `σ`, mixed with
  point masses at 0 and 1 (weight `π`), since a model often goes all in. S1's runs are rounded to the 1/125 grid.
  `μ` ∈ {0.1, 0.3, 0.5, 0.7, 0.9}; `σ` ∈ {0.02, 0.05, 0.10, 0.15, 0.20, 0.25}; `π` ∈ {0, 0.2, 0.5}; true difference ∈
  {0, 0.05, 0.10, 0.15, 0.20, 0.30}; repeats per wording ∈ {6, 10, 15, 20}; a wording shift ∈ {0, ±0.03, ±0.05},
  shared by both objectives or reversed between them (to test §10.1).
- **Choice rates.** Bernoulli with rate `p` ∈ {0, 0.05, 0.2, 0.5, 0.8, 0.95, 1}; true difference ∈ {0, 0.10, 0.20,
  0.30, 0.35}; repeats per wording ∈ {6, 10, 15, 20}.
- **Failures.** Failure rate per cell ∈ {0, 2%, 5%, 10%, 15%}, at random and, separately, only under one objective,
  so the exclusion and the worst-case bound are exercised.
- **Replicates.** 2,000 per grid point; 20,000 at every point with a true difference of 0 or exactly `T`, where the
  rates are small (a 0.3% rate at 20,000 replicates has a Monte Carlo standard error of about 0.04 points). The
  build's first act is a timing run (`--quick`); if the full grid would take more than about an hour on the laptop,
  the grid is thinned, never the null and threshold points.

**What is measured, each against a target written now:**

| Measure | Where | Target | If missed |
|---|---|---|---|
| False split | true difference 0 | at most 0.05 / 16 per comparison (family-wise at most 5%) | dated patch to `planning/07` §6 |
| False no split (decision 4) | true difference exactly `T` | at most 0.05 / 16 per comparison | dated patch to `planning/07` §6 |
| Power | true difference 1.5 `T`, at the repeat rule's n | reported; at least 80% for shares where rule (a) sets n | stated in the protocol |
| No split reachable | true difference 0, at rule (b)'s n | about 54% (the rule puts the half-width at 0.8 `T`, so "no split" needs the observed difference within 0.2 `T`, about 0.74 standard errors) | dated patch to rule (b) |
| All agree | every run identical in both objectives, both methods | no "no split" from a zero-width interval | decision 10 |
| Worst-case bound | each failure pattern | a verdict is never kept that the bound overturns | a bug, fixed before the tag |
| Wording rule | reversed wording shift | flagged wording-sensitive | a bug |

**`planning/07` §8's and `planning/08` §3.4's stated numbers, each checked and kept or corrected by a dated patch:**
the share interval of about ±8 points at sd 0.15 and the cap; the choice-rate interval of about ±27 points near 50%
and about ±12 points near 5% at the cap; a 30-point difference near 50% declared a split about 63% of the time, a
35-point one about 80%; and 80% power for a 15-point share difference at sd 0.15 and about 10 per wording.

### 14.2 The matcher

The five synthetic cases of §13.4 per scenario shape, 2,000 trials each, at spreads `σ` ∈ {0.05, 0.10, 0.20} and 10
repeats per wording (`planning/07` §10.4 item 1). Output: `D*`, `k*`, the rate at which each case type is labeled
match, tie, no good match and not enough disclosed. Recorded in `matcher-calibration.md`.

### 14.3 The resample count

At two typical points (a share split near its boundary and a no split near its boundary), the verdict recomputed on
200 seeds at `B` = 10,000 and at `B` = 100,000: the share of seeds on which the verdict differs from the majority.
Recorded; it is the evidence for decision 7.

### 14.4 Where results go

`docs/phases/evidence/phase-3/simulation-results.json` (every number, its grid point, seed and replicate count; the
git sha and the locked library versions) and `simulation-summary.md` (tables, each row pointing at the JSON). **Both
are produced by code** (`hc simulate run`, then `hc simulate report`), and re-running from the same commit gives
byte-identical files. A test checks the committed summary against the committed JSON.

## 15. Commits

He runs each one; short one-line messages, no attribution.

- **C1** `phase 3: implementation doc` — this doc, after approval, with: `ROADMAP.md`'s Phase 3 row; START HERE; the
  Phase 2.5 doc's DoD 8 CI id (`37714513948`); the `KNOWN-GAPS.md` OPEN entries (Phase 4: per-scenario repeats, the
  `possible_decline` flag); the dated scope-doc notes decision 1 needs (Phase 3 Delivers 8 and DoD, Phase 1.5).
- **C2** `phase 3: analysis group, run reader, outcomes` — steps 1-2.
- **C3** `phase 3: intervals and verdict engine` — steps 3-4.
- **C4** `phase 3: failure, robustness, descriptive` — steps 5-7.
- **C5** `phase 3: repeat rule and matcher` — steps 8-9.
- **C6** `phase 3: simulations` — steps 10-11, with the evidence files.
- **C7** `phase 3: planning/07 patches and close-out` — step 12, and step 13's audit.

## 16. Rules this build must not break

- **No model is called.** Not official, not development. `tests/test_network_guard.py` stays green.
- **No run record from any sweep is read.** Not `scratch/runs/`, not S3. Every test record is built by code.
- **Synthetic data encodes no expected answer** (§14.1, §13.4).
- **Every number is reproducible** from committed code, committed seeds and the locked library versions.
- **The rules implemented are `planning/07`'s,** as patched. Where the build shows one cannot work as written, the fix
  is a dated patch to `planning/07` with the evidence, made in this phase, before Phase 3.5. A better method found
  along the way is noted for a later protocol version, not swapped in (the scope doc's risk on scope creep).
- **No content change.** Nothing under `experiment/company/` changes; if one ever must, it goes through the change log.
- **`make check` before every commit; CI green.**

## 17. Decisions for him

Ten. Each has a recommendation. Decisions 3, 4, 6 and 10 change `planning/07` by dated patches once decided.

**ALL TEN DECIDED 2026-10-08 (his), each (a), as recommended:** 1, 3, 4, 7, 8 and 10 at 9:10 AM; 2, 5, 6 and 9 at
9:17 AM. The options stay as the record.

1. **The missing Phase 1.5 scorer** (§3 item 1).
   - (a) **Recommended:** the engine is a **library** that returns a **versioned results object** (`RESULTS_VERSION`).
     The static JSON, its schema and the site stay Phase 1.5's; when Phase 1.5 is built, its scorer serializes this
     object. Dated notes amend the Phase 3 scope doc (Delivers 8 and the *(rests on 1.5)* prerequisite) and the Phase
     1.5 scope doc (its scorer reads the run rows through `analysis/records.py`; whether DuckDB still earns its place
     is its IMPLEMENTATION doc's question).
   - (b) Build Phase 1.5's descriptive scorer and JSON here, without the site. More scope, designed before the page
     it feeds exists.
2. **Where the statistics libraries live** (§5).
   - (a) **Recommended:** a separate **`analysis`** dependency group, installed locally and in CI by default, kept out
     of the container image (`--no-default-groups`). The image runs sweeps and never analysis.
   - (b) Ordinary runtime dependencies. Simpler; the image grows by numpy, scipy, pandas and statsmodels, none of
     which it uses.
3. **The worst-case bound, both ways** (§3 item 2, §9.4).
   - (a) **Recommended:** apply it to **"no split" as well as "split"**: a "no split" that failed runs could overturn
     is inconclusive. The cost: with failures, "no split" becomes harder to earn, by up to the failure rate (a 2%
     failure rate can move a share difference by about 2 points). The simulation measures the cost at 0-15% failure.
     Patch: `planning/07` §5.2.
   - (b) As written: only "split" is protected. "No split," the verdict in the Roundtable's favor, would then be the
     one verdict failures could quietly produce.
4. **A false "no split" target** (§3 item 3).
   - (a) **Recommended:** simulate how often the rule says "no split" when the true difference is exactly the
     threshold, with the same target as false splits (at most 0.05 / 16 per comparison). Added to DoD 3; a miss is a
     dated patch before the tag.
   - (b) Measure it and report it, with no target.
5. **How each objective's value is formed** (§3 item 8).
   - (a) **Recommended:** shares use **the mean of the three per-wording means**, so each wording counts equally
     even when failures leave them unequal; choice rates use counts pooled across wordings, which Newcombe's method
     needs. With no failures the two are the same. Stated in the protocol.
   - (b) The mean of all valid runs, pooled, for both. A wording with more failures then counts less.
6. **An excluded cell** (§3 item 6, §9.2).
   - (a) **Recommended:** **drop that wording from both sides** of every comparison it is in, and say so in the
     verdict ("over w1 and w3"). Like with like, as `planning/07` §7.1 requires. Patch: `planning/07` §5.2.
   - (b) Drop only the cell, so one side has fewer wordings than the other.
7. **The interval's fine print** (§3 item 7, §7.2).
   - (a) **Recommended:** `ALPHA` = **0.05 / 16 = 0.003125** exactly (z = 2.955), called "99.7%" in prose; the
     **percentile** bootstrap with **100,000** resamples (the floor is 10,000; a 99.7% interval reads about 15
     resamples in each tail at 10,000, and 156 at 100,000; §14.3 measures what that buys); each comparison's seed
     derived from the sweep id and the comparison's name, so no one picks it. Patch: `planning/07` §6.3 and §8, to
     carry the exact number.
   - (b) 0.003 and 2.968, as `planning/07` §8's arithmetic has it; 10,000 resamples; a seed written into the protocol.
8. **Keeping the engine away from the Phase 2.5 runs** (§3 item 9).
   - (a) **Recommended:** the run reader **refuses any record under `development/` whose experiment is not the
     placeholder**, with a message saying why. Official, pilot and placeholder records are read; nothing else. Tested.
     Phase 4's prefixes must then fit it, which its IMPLEMENTATION doc confirms.
   - (b) A rule in the docs only.
9. **The matcher's open choices** (§6.4, §13.2).
   - (a) **Recommended:** S4's vector holds **uses and sources together**, normalized by their combined sum; a **tie**
     is a gap whose central **95%** bootstrap interval includes zero; `D*` from the 95th percentile of true-match
     distances at the largest spread; `k*` from 80% identification at the design spread (§13.3).
   - (b) S4 on uses only; a tie at the same 99.7% as the verdicts (more ties, fewer matches).
10. **The all-agree share case** (§3 item 4). Not decidable before the evidence exists; agreed here as a procedure,
    like Phase 3.5's decision 5.
    - (a) **Recommended:** the simulation measures the bootstrap's behavior when every run in both objectives is
      identical or nearly so (all-in mixtures with `π` up to 0.5, S1's grid). **If it gives a "no split" from a
      zero-width or near-zero-width interval, Opus brings him a fix with the evidence before C7**, and a dated patch
      to `planning/07` §6.3 records the choice. The leading candidate, stated now so it is not invented after: when
      the runs of both objectives sit at one boundary value, the share outcome is also tested as a choice rate (the
      share of runs at that value) by Newcombe, and the comparison takes the less certain of the two verdicts.
    - (b) Accept the bootstrap's answer in that case, and say so on the methods page.

## 18. Order of work

Each step ends green under `make check`. Model choice in brackets (`CLAUDE.md`: Opus for design and review, Sonnet
for routine code; he switches with `/model`).

0. **C1** (him): this doc and the housekeeping in §15, after approval.
1. **[done 2026-10-08, Sonnet] The analysis group and the run reader.** `pyproject.toml` group and `default-groups`; the Dockerfile
   change and a local image check; the mypy override; `records.py` with `RunRow` (run id, scenario, objective,
   wording, repeat, final status, first-attempt status, the amounts used, the choice, `menu_order`, `option_order`,
   the first attempt's amounts and choice); decision 8's refusal; tests on records **written by test code in the
   runner's exact format** (built by calling the runner's own record functions on fake providers where possible, so
   the format cannot drift).
   *As built.* Versions re-read on PyPI the same day: numpy 2.5.3, scipy 1.18.1, statsmodels 0.15.0, pandas 3.0.6,
   patsy 1.0.3, all at least two weeks old. **One transitive pin:** `formulaic` (statsmodels) pulled `wrapt` 2.5.0,
   released 2026-09-27 (11 days), so `uv.lock` holds `wrapt` 2.4.1 (2026-09-10); a bare `uv lock --upgrade` will move
   it, so re-check the age of anything new in the lock then. `[tool.uv] default-groups = ["dev", "analysis"]`; both
   Dockerfile `uv sync` lines say `--no-default-groups`. **Image checked locally** (built, then removed): `import
   numpy`, `scipy` and `statsmodels` each fail inside it with `ModuleNotFoundError`, `pydantic` and `boto3` import.
   mypy override for `statsmodels.*` only. `records.py` reads from anything with `get` and `list_keys` (its own small
   protocol, since `sweep/store.py` imports botocore and the analysis may not), refuses by key, **on every key a
   listing returns** and not only on the prefix asked for, so a wide prefix (`""`, `development/`) that reaches
   `development/company/` is refused; the message says why. Integrity refusals beyond the brief: a `final.json` that
   disagrees with its last model attempt, a run not in the manifest, no manifest. Unfinished runs (a manifest entry
   with no `final.json`) are listed in `RunSet.unfinished`, not analysed. `repeat` comes from `manifest.json`, since
   the attempt records do not carry it. The status sets are copied into `records.py` (it may not import
   `sweep.classify`) and a test compares them with the runner's. Tests: `tests/test_analysis_records.py` (13), the
   records built by `run_session` on a scripted provider, and `tests/analysis_helpers.py`, which runs the real
   company scenario files through the runner and copies the objects to a `pilot-test/` prefix the reader accepts.
2. **[done 2026-10-08, Sonnet] The outcomes** (§6), every key read from the scenario files; tests on hand-built runs for each
   scenario, including S1's undefined secondary and S4's vector of uses and sources together.
   *As built.* `analysis/outcomes.py`: `outcomes_for(scenario)` returns kind, threshold (0.10 / 0.20), line keys and
   `score_amounts` / `score` / `score_first_attempt` (the same computation on the counted decision or the first
   attempt's) / `summarize_secondary` (mean over runs where defined, with `n_defined` beside `n_runs`). Totals, caps,
   lines and the offered set come from the loaded scenario; lines are found by lever code (L1 for the eliminated
   people in S1 and S3, L1 and L4 for S2's workforce). **Three names a lever cannot give are in one table
   (`_ROLES`) and checked against the file on construction:** S1's `move_keep_pay` and `move_plant_pay`, S3's `close`,
   S4's `fund`. A rename fails loudly, and a test proves it. Secondaries per run: S1 `keep_pay_share_of_moved` (None when
   no one moved), S3 `retained_share`, S4 `any_cuts`; S2 has none. S4's vector is all fifteen offered lines over
   their sum, and is None (not a division by zero) if every line is zero. The descriptive roll-ups of §11 stay step 7.
   Tests: `tests/test_analysis_outcomes.py` (21), hand-built runs for each scenario plus the same shapes written by the
   runner and read back through the reader.
   *Architecture tests added* (`tests/test_architecture.py`): `analysis` never imports `simulation`; `analysis` imports
   only itself, `horizon_compact.experiment`, the standard library and numpy, scipy, statsmodels; nothing outside
   `analysis` and `simulation` imports those three (the image has none of them); `default-groups` and both Dockerfile
   lines are as above. *Opus review, same day:* the import reader skipped relative imports, so `from ..simulation
   import x` would have passed; it now resolves them against the file's package, with a test that proves it.
3. **[done 2026-10-08, Opus] The intervals.** First, read Newcombe (1998) Table II, or a published reproduction of it, from a live
   copy, and write `worked-examples.md` with the source; then `intervals.py` and its tests (§7); the bootstrap's
   cross-check against scipy.
   *As built.* **Newcombe's Table II was not readable in full** (publisher paywall; ResearchGate 403). Read instead:
   three of its columns, (a), (b) and (h), as reproduced with a page-877 citation in the `pairwiseCI` R documentation,
   and Fagerland, Lydersen and Laake (2011), whose equation 7 gives the formula and whose Table 3 gives a worked
   example. statsmodels matches all four published values, and matches a hand-written equation 7 to 1e-15 on all
   eight Table II columns at 95% and at `ALPHA`. **§3a's disagreement was my recall, not statsmodels:** the recalled
   0.0381 is column (d)'s lower bound. Sources, both tables and what is and is not a published check:
   `evidence/phase-3/worked-examples.md`. `analysis/intervals.py`: `ALPHA` = 0.05 / 16 exactly, `Z` = 2.9552 (computed,
   not typed), `RESAMPLES` = 100,000; `newcombe_difference` (the one statsmodels call, typed); `mean_of_wording_means`
   (decision 5); `comparison_seed(sweep_id, name)` (sha256, first 128 bits, into PCG64; decision 7);
   `stratified_bootstrap_difference`, which refuses two sides with different wordings (like with like; the caller drops
   an excluded wording from both, decision 6), empty cells and non-finite values. Quantiles use numpy's default
   (linear), the same as scipy's percentile method. Tests: `tests/test_analysis_intervals.py` (48): published values,
   the formula, the edges (never zero width), an exact enumeration of a three-run bootstrap, scipy within Monte Carlo
   error, stratification, seeds, refusals, and **the all-agree [0, 0] kept as a visible test for decision 10.**
   **§5 was wrong about scipy:** it ships no types. `scipy-stubs` 1.18.1.1 (2026-09-20) joins the `dev` group, so mypy
   stays strict with no new override; its dependency `optype` is held at 0.18.0 (2026-06-07) in `uv.lock`, because
   0.19.0 was 6 days old. The plain-English notes began: `evidence/phase-3/plain-english.md`.

4. **[done 2026-10-08, Opus] The verdict engine** (§8), with known-answer sets built **independently of the engine** (a split, a no
   split, an inconclusive, each for shares and for choice rates, and the all-agree case for each method), every
   boundary of §8.2 tested.
   *As built.* `analysis/verdict.py`: `decide(d, lo, hi, T)` returns the verdict and a sentence saying why;
   `compare(outcomes, rows, first, second)` gives one `Comparison` (scenario, pair, role and label, outcome, kind,
   threshold, the wordings it is "over", valid runs per wording per side, the `Interval`, the decision, and a
   `degenerate_interval` flag); `compare_scenario` gives A-C, A-B, C-D, B-D, then A-D as "secondary: the expected
   comparison". Only valid runs are read; runs from two sweeps or two models are refused; **a wording with no valid
   run on one side is refused, never dropped quietly** (dropping is decision 6, the failure rules' call, made by
   passing `wordings`). The bootstrap's seed name is `<scenario>:<first>-<second>`; the sealed-wording rerun (step 6)
   passes its own name, e.g. `s1:A-C:sealed`. Tests: `tests/test_analysis_verdict.py` (54). **Known answers built
   without the engine:** share cases whose interval is bounded by the data's range alone (every resampled mean lies
   between a cell's smallest and largest value), and choice-rate cases checked against the test's own Newcombe.
   **Mutation check:** twelve deliberate bugs planted in the boundary logic, one at a time; eleven failed the tests,
   and the twelfth (dropping the same-side condition) is logically equivalent to the code, as noted below.
   **Four findings, for step 12's `planning/07` patch list (his review), none changing a rule's intent:**
   (a) **floating point at the threshold:** 57/60 − 45/60 is 0.19999999999999996, and its interval excludes zero, so
   a plain `>=` would call an exact 20-point difference inconclusive. Every boundary is compared with a tolerance of
   1e-9 (the finest outcome grid is 1/125 = 0.008); a value within it counts as on the boundary, which then goes
   against the stronger verdict, except that "at least T" includes T, as `planning/07` §6.2 says.
   (b) **a guard the planning does not state:** the difference must lie inside its own interval, or the verdict is
   inconclusive. A percentile interval can, rarely, exclude its own estimate, and without the guard an interval
   could satisfy split and no split at once. It can only weaken a verdict, and it makes §8.2's "|d| ≥ T" directional
   (a split's difference is on the side of zero its interval is on).
   (c) **decision 10 is already triggered, without waiting for the simulations:** when every run under both
   objectives gives the same share, the bootstrap returns [0, 0] and the rule as written says **no split**. That
   follows from arithmetic, and a test now holds it. The engine flags it (`degenerate_interval`) and does not hide
   it. What the simulations still have to show is how often *nearly* identical runs give a near-zero width; the fix
   (the leading candidate is in decision 10) comes to him before C7, as agreed.
   (d) §8.3's remaining fields (the worst-case verdict, the wording label, the final verdict and the downgrade
   reason) belong to steps 5 and 6, which extend `Comparison`; this step returns the verdict among valid runs only.

5. **[done 2026-10-08, Sonnet] The failure rules** (§9), including decision 3's bound both ways and decision 6's exclusion.
   *As built.* `analysis/failures.py`. **Refactor first:** `verdict.compare()` is now `gather_cells()` (the valid
   runs' outcomes by objective and wording, a `CellSet`) then `compare_cells()` (interval and decision); `compare()`
   calls both, so its behavior is unchanged and the 54 step-4 tests pass unedited. `verdict.one_value` and
   `verdict.label_for` became public for `failures.py`. **Counting:** `classify_run` gives valid, valid_rescaled,
   refusal or failure; a `no_tool_call` is a refusal only through `refusal-calls.json` beside the sweep, an object of
   run id to a non-empty reason (`parse_refusal_calls`, `read_refusal_calls`); a call naming an unknown run, or a
   run whose final status is not `no_tool_call`, is a `RefusalCallError`, checked against every run given so a typo
   cannot pass; `decline_candidates` lists flagged runs and decides nothing. **Cells:** `cell_rates` (attempted,
   valid, rescaled, refused, failures by type); `exceeds_limit` compares integers, strictly greater than 1/10 (3 of
   30 kept, 4 of 30 dropped). **Decision 6:** `assess_comparison` drops a wording from both sides when either side's
   cell is over the limit, says which and why (`scope`), and returns `not_assessable` when none is left; a wording
   with no run at all on one side is refused, not dropped. **Decision 3:** one `BoundCheck` per setting, each a full
   recompute through `compare_cells` (interval included) with its own seed name (`<name>:bound:<label>`); a split
   gets the narrowing setting (the sign of the difference picks the direction), a no split gets both widening
   signs; the first overturning check sets `worst_case_verdict`, and the final verdict is inconclusive with the
   reason spelled out. Failed runs in a dropped wording are not imputed; no failed run, or an already inconclusive
   verdict, means no bound. **9.3:** `first_attempt_rows` re-reads each run as its first attempt (status, amounts,
   choice) and the same assessment runs on that view, exclusion and bound included, under seed names ending
   `:first-attempt`; a test shows the view scores exactly as `outcomes.score_first_attempt` does. **9.5:**
   `objective_rates` and `pair_rates` (failure, refusal and either, as first minus second, each by Newcombe).
   `assess_scenario` returns all of it for one scenario. Tests: `tests/test_analysis_failures.py` (53; 917 tests in all), hand-built
   runs only, expected intervals from the test's own Newcombe; every boundary named in the brief is a test (exactly
   10%; a narrowed difference of exactly 0.20 kept as a split, one run short overturned; a no split overturned only
   by the negative sign, and separately only by the positive; a no split the bound turns into a split; failures in a
   dropped wording). `tests/analysis_helpers.py` now holds `run`, `s1_runs`, `s3_runs`, `hand_newcombe`, `failed`
   and `s3_cell`. **Mutation check:** 24 deliberate bugs planted in `failures.py`, one at a time (limit `>=`, a
   float limit, refusals left out, calls ignored, the flag deciding, either-side and both-side exclusion, inverted
   narrowing, one widening sign only, no split not bounded, only "inconclusive" counting as overturned, the final
   verdict not downgraded, failures counted from dropped wordings, imputed values swapped, each first-attempt field
   left at its final value, a shared seed, and more); all 24 failed the tests; the file was restored.
   **Findings, for step 12's list and his review (none changes a rule's intent):**
   (a) **Decision 3's two signs is an interpretation, implemented as asked:** a no split's difference can sit near
   zero, so raising it and lowering it are different tests and either one overturning downgrades. Without the
   second sign, a one-sided design (failures only on the second objective, both rates 0) passes the raising check
   and is overturned only by the lowering one; a test holds each case.
   (b) **The bound also reaches decision 10's case:** the all-agree share "no split" ([0, 0]) is downgraded
   whenever failed runs exist in the kept wordings (C at 1.0, D's failures at 0 gives a 0.10 difference). It is
   kept only when nothing failed. That narrows decision 10 to the failure-free all-agree case.
   (c) **At small cells a single failure excludes a wording:** 1 of 6 is 16.7%, over the limit; 1 of 10 is exactly
   10% and kept. `planning/07` §8's repeat floor is 6 per wording, so at 6 to 9 repeats one failure drops that
   wording from every comparison its cell is in. The rule is pre-registered as written; the simulations (step 10)
   should measure how often it bites at the repeat counts the rule produces.
   (d) **`planning/07` §5.1 names a "logged human call" and no format.** The format is now `refusal-calls.json`,
   beside the sweep; Phase 4's IMPLEMENTATION doc must say who writes it and when (before any official analysis).
   (e) **9.5's interval level is not stated in the planning.** Built first at the family `ALPHA`; **changed after
   Opus's review (his, 2026-10-08) to `DESCRIPTIVE_ALPHA` = 0.05**, see below.
   (f) **Unfinished runs are invisible to the rates:** `RunSet.unfinished` is not in the rows, so a cell's
   "attempted" counts finished runs only. Phase 4 should refuse analysis while anything is unfinished.
   (g) **The first-attempt view ignores human calls** (they are about a final status); a first-attempt
   `no_tool_call` stays a failure by type, which counts the same toward every rule.
   *Opus review, same day (his decisions):* (a) kept: "worst case" is the worse of the two settings, and near zero the
   difference's sign is noise. **`DESCRIPTIVE_ALPHA` = 0.05** in `intervals.py`, for every descriptive interval (9.5
   now, §10.3 next): as decision 9, a reading not a test, and here the narrower interval is the cautious one, since
   9.5 exists to show a failure difference by objective that could bias the comparison. `assess_scenario` takes it
   as its own `descriptive_alpha`, so the family `alpha` cannot leak into the table (a test holds it). **Renamed
   away from "imputed"** (`set_first`, `set_second`, `_set_failed`): `planning/07` §5.2 says "no imputation", and
   the bound is a sensitivity bound whose field names reach the results object. **For the methods page:** the
   bound is the worst case for the *difference* (§5.2's words); splitting failed runs between 0 and 1 can widen an
   interval more without moving the mean, which the rule does not check, and need not. **For Phase 4's OPEN
   list:** refusal calls made with the objective hidden and written once before analysis; analysis refused while
   any run is unfinished (finding f). **For step 12:** finding (a)'s two signs, `DESCRIPTIVE_ALPHA`, and finding
   (c), to be judged on step 10's evidence.
6. **[done 2026-10-08, Sonnet] The robustness rules** (§10).
   *As built.* `analysis/robustness.py`. **10.1:** `wording_direction` reads the per-wording difference (first minus
   second, among valid runs; the mean share, or the choice rate) over the wordings `assess_comparison` **kept**, so a
   dropped wording can neither support nor break a split; each difference is `same`, `opposite` or `zero` against the
   pooled sign (`zero` is within `BOUNDARY_TOLERANCE`, which a test shows catches a -1.4e-17 float residue), or
   `undefined` when the pooled difference has no sign. A split that survived the bound is `robust` only if every
   wording is `same`, otherwise `wording_sensitive`; any other final verdict has the differences and no label.
   `RobustComparison` wraps the `AssessedComparison` and adds `headline`, the claim as published ("split, robust: ..."
   / "split, wording-sensitive: w3 reverses (-0.600), over wordings ..."). **10.2:** `sealed_wording_of(experiment)`
   reads the id from the loaded experiment (a test reads `objectives.toml` itself), and `sealed_result` reruns the
   whole assessment, bound included, on that wording's runs under seed name `<scenario>:<first>-<second>:sealed`,
   labeled "sealed wording only; outside the family of 16", with the pooled final verdict and whether they agree.
   **10.3:** `position_effects`: per offered line, mean share of the total at each menu position and the
   least-squares slope; per option of S3 and S4, the choice rate when listed first against not first with a
   Newcombe interval at `DESCRIPTIVE_ALPHA` (`None`, not invented, when a group is empty). `robustness_scenario`
   returns all of it for one scenario's assessment. Tests: `tests/test_analysis_robustness.py` (26), hand-built runs,
   expected intervals from the test's own Newcombe, the position cases worked out by hand in the comments. The
   `s3_design` and `with_failures` helpers moved to `tests/analysis_helpers.py`. **Mutation check:** 25 deliberate bugs
   (zero not recognised or counted as agreement, the sign test inverted, any-agrees instead of all, a label on a
   non-split or from the pre-bound verdict, dropped wordings read, the difference reversed, a wording-sensitive split
   downgraded, a sealed rerun that shares the pooled seed, reads every wording, hard-codes the id, drops the pair's
   role or always agrees, 0-based positions, a share not over the total, the slope's sign, a slope for a constant
   position, the first-listed test, the family alpha in the option interval, an invented interval for an empty group,
   failed runs read); 23 failed the tests on the first pass and two survived, which showed two real gaps (the pair's
   role was never checked in the rerun, and the sealed id was always `w2`, so a typed `"w2"` was invisible); both
   are now tested and caught, 25 of 25.
   **To flag to him (the rule I was asked to decide and state):** *a wording-sensitive split keeps its verdict,
   `split`, and carries the label.* The planning words are "reported as wording-sensitive" (`planning/07` 7.1) and
   "marks a split as wording-sensitive" (scope doc); making it inconclusive would be a new rule. The cost is that
   the headline, not the verdict field, carries the qualification, so the results page must show the headline.
   **Findings for step 12 and step 10:**
   (a) **"Robust" is demanding at small cells.** Per-wording differences rest on 6 to 20 runs a side; a real split
   can show a zero or opposite difference in one wording by chance. Step 10 should measure how often a true split
   is labeled wording-sensitive at the repeat counts the rule produces (its table has the reversed-shift case, not
   this false-alarm rate).
   (b) **A split over one kept wording is labeled robust trivially.** Its scope says "over wording w1"; the results
   page should not show "robust" without the scope.
   (c) **The sealed rerun uses the family `ALPHA` and one third of the runs.** It repeats "the whole verdict
   computation" as asked, so it is the same test on less data: an inconclusive sealed result beside a pooled split
   usually means power, not disagreement. `agrees_with_pooled` was strict (identical final verdicts); **replaced in step 7 by a relation** after Opus's
   review (see step 7). Whether the sealed result should be judged at 95% is for step 12; Opus advised keeping the
   family level, since 95% would make the sealed wording easier to pass than the pooled test.
   (d) **Position effects:** positions are those shown, including lines not offered; the pooling crosses objectives
   and wordings (shuffling is independent of both); the slope has no interval, as §10.3 says. A standard error or an
   interval at `DESCRIPTIVE_ALPHA` on the slope is a small addition if he wants one.
   (e) **§8.3's "final verdict after both":** the wording check never downgrades, so it equals the failure rules'
   final verdict; the wording label is a separate field.
7. **[done 2026-10-08, Sonnet] The descriptive analyses** (§11) and `results.py`, the versioned object.
   *First, Opus's step 6 review (his decision):* `SealedResult.agrees_with_pooled` is replaced by a **relation**
   (`robustness.relate`), because the sealed rerun is the same test on about a third of the data and a real result
   can come back less certain without any wording disagreeing. Four values, not three: **`same_verdict`** (same
   verdict; two splits must also share a sign), **`same_direction_less_certain`** (sealed inconclusive, and either the
   pooled split's sign with a nonzero difference, or a pooled no split with the sealed point estimate strictly inside
   the band, `|d| < T - eps`), **`different`** (everything else, including a sealed difference of zero beside a
   pooled split and a sealed estimate at or past T beside a pooled no split), and **`not_comparable`** (either side
   not assessable). *The fourth is my addition to Opus's three:* a sealed cell over the failure limit is "nothing to
   compare", not a disagreement. Defined exactly in the module docstring; 29 boundary cases plus integration tests;
   mutation check 14 of 14 (two gaps first: the integration tests never had the sealed difference pointing the other
   way or the threshold in play). *As built, §11:* `analysis/descriptive.py`: per scenario, valid runs only, every
   offered line's share of the total (count, mean, sample sd, median, range) per objective x wording and pooled over
   wordings, and by choice (pooled over wordings) for S3 and S4; the display groups (`planning/07` §3.3, overlapping;
   uses and sources summed apart in S4; S4's program, which has no canonical lever, in none); the choice split per
   objective and wording with zeros kept; the secondaries (S1 with `n_defined` beside `n_runs`, S3's retained share,
   S4's any-cuts) per cell and by choice; **E's distance to each objective beside each objective's own distance**
   (`run_distance`: total variation on the lever-level vector, plus a 0/1 choice term where the scenario has a
   choice, the mean of the two when both exist; an undefined vector (S4, all zero) distances on the choice alone and
   the pair is counted as choice-only); and every valid run's values kept whole (`per_run`) so spread can be drawn.
   `results.py`: `build_results(experiment, runset, ...)` returns **`ModelResults`**: the version, sweep, model,
   alphas, resamples, the sealed wording (read from the experiment), the refusal calls with their reasons, and per
   scenario the flat **`ComparisonResult`** for each pair (method, difference, interval, seed, verdict among valid,
   kept and dropped wordings with the cells that dropped them, runs per wording, failed runs per side, **the bound's
   settings and recomputed verdicts**, the worst-case verdict, **the wording label as its own field**, the
   per-wording differences, **reversed and zero wordings as separate fields**, the final verdict and the downgrade
   reason, the sealed summary with its relation, the first-attempt summary, and `headline`), the failure-rule cells
   and pair rates, position effects and the descriptive output. `headline` is documented in the class docstring as a
   **diagnostic string, not published text**; the site's wording is written when Phase 1.5 is built. Everything in the
   object is numbers, strings, booleans, `None` and tuples of frozen dataclasses of those, and a test walks it with
   `dataclasses.asdict` and `json.dumps`. **`RESULTS_VERSION` stays 1:** the object did not exist before this step and
   nothing has serialized an earlier shape; a test pins every field name of the result types, so any later change
   fails it until the version is bumped. **`build_results` refuses an unfinished sweep** (the `RunSet` carries
   `unfinished`), runs on a scenario the experiment does not have, an experiment with no sealed template, and calls
   that name no run (checked once, downstream, by the failure rules). A scenario in the experiment with no runs is
   listed in `scenarios_without_runs`, not dropped silently. Tests: `tests/test_analysis_descriptive.py` (19; every
   expected number worked out by hand in its comment), `tests/test_analysis_results.py` (17), and 32 more in
   `tests/test_analysis_robustness.py`. **Mutation checks:** descriptive 23 of 23, results 23 of 23 non-equivalent
   (one planted bug, removing the calls check from `build_results`, was equivalent because `assess_scenario` checks
   the same calls, so the redundant line was deleted). Gaps the mutation checks showed, now tested: a median equal to
   the mean in every sample, a choice-less scenario that happened to give the same distance from the vector and
   the choice, and result tests whose designs were all symmetric (equal failures per side), all default alphas, or
   with first attempts equal to finals.
   **For step 9 (Opus), flagged:** `run_distance` is defined here, on the full vector, because §11 item 5 needs it
   now and §13.1 defines it; the matcher restricts the vector to observable lines and renormalizes before calling
   the same function. If step 9 prefers the definition to live in `matcher.py`, it moves; its tests are here.
   **Findings for step 12 and the site, none changing a rule:**
   (a) **Position-effect slopes are pooled across objectives** (step 6 note (d)); a per-cell fit would be tighter,
   noted for a later protocol version (§16).
   (b) **E's distance pools all wordings.** The mean is over every (E run, other-objective run) pair, as §11 item 5
   says; a like-with-like version (the same wording only) is a one-line change if he prefers it.
   (c) **The allocation summaries use the share of the scenario's total**, S4's uses and sources each against
   $20.4 million (not against their own sum, as the matcher's vector does).
   (d) **`build_results` needs `menu_order` and `option_order` on every valid run** (position effects refuse
   otherwise). The runner always writes them; a hand-built or old record without them is refused loudly, not
   skipped.
   *Opus review, same day, before C4:* one fix. A comparison that was not assessable got made-up values in the
   object (`outcome` and `kind` empty, `threshold` and `alpha` 0.0); they now come from the scenario and the run
   settings, which are known either way, and only what depends on valid runs is `None` (a test holds it). No field
   name changed, so `RESULTS_VERSION` stays 1. Sonnet's fourth sealed relation, `not_comparable`, is right and kept.
8. **[done 2026-10-08, Sonnet] The repeat rule** (§12), tested on `planning/07` §8's worked example.
   *As built.* `analysis/repeats.py`. `repeats_for_scenario(outcomes, rows)` returns a `ShareRepeats` (S1, S2:
   `scenario_id`, `pooled_sd`, `degrees_of_freedom`, `n_power`, `n_both_reachable`, `repeats`, `cap_binds`,
   `achieved_half_width`, set only when the cap binds) or a `ChoiceRepeats` (S3, S4: `scenario_id`, `repeats` = 20,
   `half_width_at_50`, `half_width_at_5`); `repeats_for_pilot` gives one per scenario in the order asked. Cells are
   one objective under one wording; valid runs only; a cell of one run adds neither squares nor degrees of freedom;
   no cell with two runs is a `RepeatRuleError`, as are no runs and (via the verdict engine's own check) runs of two
   sweeps or two models. Rules (a) and (b) use `Z` from `intervals.py`, the threshold from the scenario's outcomes
   and `WORDINGS` = 3; `0.84` is the planning's number as written. Counts are rounded up with a 1e-9 guard so a
   value that is a whole number to rounding error is not pushed to the next (`round_up`, tested). The cap binds
   only when the larger count is *over* 20 (exactly 20 does not). Achieved precision is `Z sd sqrt(2 / (3 n))` at
   n = 20; for choice rates it is half of Newcombe's interval width at the family level for equal rates of 30 of 60
   and 3 of 60 a side. **No direction in the output:** a test pins the field names for both types, checks none
   contains a direction word (mean, diff, objective, label, first, second, winner, split, verdict), and shows the
   output is identical when an objective's runs are shifted up or down by 0.4 or the objectives are relabelled.
   Tests: `tests/test_analysis_repeats.py` (47): the worked example, every clamp edge (0, 5, 6, 7, 19, 20 and just
   over 20), sd 0, a one-run cell, cells keyed by objective and wording, the frozen Z against rounding edges,
   by-hand pooled sd. **Mutation check:** 66 deliberate bugs planted one at a time (a typed 2.96 in each rule and in
   the half-width, 0.8416 for 0.84, floor and cap off by one, min for max, either rule alone, the cap test `>=`,
   rounding down, to nearest or with no guard, wrong multiples, wordings or threshold typed or not passed down,
   df off, cells keyed wrongly, failed runs counted, other scenarios' runs read, choice rates, widths and
   wordings changed, and more); 62 failed the tests and four are equivalent (rule (b) alone, the clamp applied in
   the other order, `half_width` at the clamped n instead of 20, and counting a one-run cell, which adds 0 and 0).
   Three gaps showed first and are tested: rule (a) was never near a rounding edge, so a typed 2.96 or 0.8416 there
   survived; and `wordings` was never passed through the scenario or pilot functions. **The worked example holds
   with the frozen Z: no rounding changed** (sd 0.15 gives 10 and 21, so 20; sd 0.10 gives 5 and 10, so 10; the
   unrounded values with Z and with 2.96 are in a test comment).
   **Findings, for step 12's patch list (none changes a rule):**
   (a) **`planning/07` §8's choice-rate precision figures do not match the method it names.** It says about ±27
   points at 50% and about ±12 at 5% (60 runs a side). Those are the Wald figures (2.96 sqrt(2 p (1-p) / 60) gives
   0.270 and 0.118). Newcombe, the method §6.3 chose, gives **±25.2 and ±15.9**, hand-checked against Fagerland's
   equation 7. The code reports Newcombe; the planning text and the methods page should say 25 and 16. At 5% the
   gap matters most: "no split" is somewhat harder to reach there than §8 says.
   (b) **Rule (a) can never set the count:** the ratio (a)/(b) is (Z + 0.84)² / Z² / (1.5/0.8)² = 0.47 whatever the
   spread, so rule (b) always decides. Rule (a) stays in the output, as the planning wrote it, but it is dead
   weight in the rule as amended; the patch can say so.
   (c) `0.84` is a rounded 0.8416; kept as written. At rule (a)'s rounding edges the two differ, but (a) never sets
   the count (finding b), so the repeats cannot move.
   (d) **For Phase 4 (already noted at the top of §12):** the planner takes one repeat count and the grid needs one
   per scenario. Also, the rule reads a pilot of **two development wordings** but divides by **three**, the study's
   wordings (the spread is per cell and the third wording is sealed); a pilot with a different shape should
   pass `wordings` explicitly.
   *Opus review, same day, before step 9:* no bug. The formulas, the clamp, the pooled sd and the no-direction tests
   were read against `planning/07` §8; the Newcombe half-widths (0.2520, 0.1586) and the (a)/(b) ratio (0.469) were
   recomputed by hand. Three `# type: ignore` comments in the test file became real annotations. **One consequence
   of finding (b), for step 10:** §14.1's power row ("at least 80% for shares where rule (a) sets n") is vacuous,
   because rule (a) never sets n. At rule (b)'s n, power at 1.5 T is above 80% unless the cap binds. Step 10 should
   report power at the n rule (b) gives and at the cap, and the row should be reworded in step 12.
9. **[done 2026-10-08, Opus] The matcher** (§13) and its synthetic cases.
   *As built.* **One definition of the distance:** `descriptive.distance(vector_a, vector_b, choice_a, choice_b)`
   (total variation where both vectors exist, 0/1 on the choice where both are given, their mean when both, `None`
   when neither); step 7's `run_distance` now calls it, its tests unchanged, so step 7's flag closes with the
   definition staying in `descriptive.py`. **`analysis/matcher.py`:** `CompanyDecision(reading, amounts, choice)`
   is one reading from the rubric, observable lines only, in any unit; `match_case(scenario, rows, readings, *,
   case_id, objectives, d_star, k_star)` returns a `CaseMatch` with one `ReadingMatch` per reading (the primary
   first). Each reading carries its observable lines (file order), whether the choice is observable, its
   dimension count, the company side's basis, the label and why, the nearest, the tied objective, the `Gap` (second
   minus nearest, with its 95% interval and seed) and every objective's `ObjectiveDistance` (distance, 95% spread,
   seed, runs distanced, choice-only runs, undistanced runs). The matcher takes a `Scenario`, not
   `ScenarioOutcomes`, because a real case's scenario will have its own id and `outcomes_for` accepts only S1-S4.
   **The label, in order:** not enough disclosed (dimensions below `k_star`, or nothing to distance on); no good
   match (nearest strictly above `d_star`; equal to it within `BOUNDARY_TOLERANCE` is not above, which is what makes
   "a true match is called no good match at most 5% of the time" true when `d_star` is a 95th percentile, since
   distances on a choice are discrete); tie (the gap's 95% interval includes zero); match. The nearest is the
   smallest distance, an exact equality broken by objective id (the tie rule then says tie). **`D_STAR` and `K_STAR`
   are `None` until step 10,** and the matcher refuses to label without them. An objective's distance is the mean of
   its per-wording means, with a 95% stratified bootstrap spread; `intervals.stratified_bootstrap_value` was added
   for it (one side, same resampling as the difference), tested by exact enumeration. Seeds come from the sweep id
   and `match:<case>:<reading>:<objective>` (the gap: `...:<nearest>-<second>`). Refused: an uncalibrated call, no
   reading, repeated reading names, fewer than two distinct objectives, an objective with no valid run, runs of two
   sweeps or two models, a line, option or choice the scenario lacks, a negative or missing amount, objectives whose
   distanced runs cover different wordings, and an objective none of whose runs can be distanced.
   **`simulation/matcher_cases.py`** (a new package outside the frozen folder; the architecture test already
   forbids the analysis importing it): `build_case(scenario, kind, *, seed, sigma, repeats, k)` gives one synthetic
   case fixed by its seed, of the five kinds in §13.4. Profiles are flat Dirichlet draws (mean allocation over the
   offered lines; choice probabilities over the options, which for two options is a uniform rate); runs are
   Dirichlet draws around the mean, with a concentration that gives a line at share 1/K the standard deviation
   `sigma`, floored at 0.05; three wordings, five objectives; the generating objective is drawn among the five.
   Opposite: all the money on the line the objective funds least, and its least likely choice. Sparse: the
   identical case on `k` of its dimensions drawn without replacement, the choice being one. True match: one more
   draw from the objective's runs. Tests: `tests/test_analysis_matcher.py` (37), `tests/test_simulation_matcher_cases.py`
   (19), and 4 more in `tests/test_analysis_intervals.py`; 1119 tests in all, `make check` green.
   **Mutation checks:** matcher and the shared distance, 63 planted; 60 caught, 3 equivalent (each changes one side
   of a choice comparison whose other side is `None`; planted on both sides at once, it is caught). The cases, 20
   planted, 20 caught. `stratified_bootstrap_value`, 4 planted, 4 caught. **Gaps the checks showed first, now
   tested:** lines given out of file order; a non-valid run carrying amounts; the spread's level (the first test's
   data had the same quantiles at 95% and 99.7%); a tie with a positive gap estimate; the generating objective
   never shown to vary; a true match equal to the mean passing whenever its choice differed; the bootstrap's seed.
   **Findings, for step 12 and for him (none changes a rule as written):**
   (a) **A lone observable line carries no information.** Renormalized over one line, every run that puts anything
   there is identical to the company (distance 0). `planning/07` §10.4 counts each observable line as a dimension,
   so one line plus the choice counts as 2 but tells only as much as the choice. A test holds the behavior. The
   options for step 12: count a line toward `k_star` only when at least two lines are observable, or let step 10's
   `k*` absorb it (its sparse cases draw one-line subsets, so the measured `k*` will already show the cost).
   (b) **A run with nothing on the observable lines and no observable choice has no distance.** The planning says
   such a run is distanced "on the choice alone" and is silent when there is no choice. Built as: left out and
   counted (`undistanced_runs`), and an objective with no distanceable run is refused. The alternative, a distance
   of 1 when exactly one side put nothing on the observable lines, would score the objective that did nothing there
   as far from a company that did, which is arguably the honest reading; it is his call.
   (c) **An objective's distance is the mean of its per-wording means** (decision 5 by analogy); `planning/07` §10.4
   says "the average of its runs' distances". The two are the same unless runs failed.
   (d) **"Depends on reading" follows the planning literally:** set when the nearest objective changes. When two
   objectives tie, which one is nearest can flip between readings by noise, so a tie can produce "depends on
   reading" without any real change. Comparing the matched sets (one objective, or the tied pair) would avoid it.
   (e) **The failure rules do not reach the matcher.** `planning/07` says nothing of a cell's 10% exclusion for real
   cases; failed runs are simply not distanced. Phase 5's IMPLEMENTATION doc should say whether that is enough.
   (f) **The synthetic choice is drawn independently of the allocation.** In the real scenarios the two are coupled
   (S3's lines follow the plant decision); the generator says so in its docstring.
   (g) **For step 10, from a 30-seed smoke run (not a calibration):** at `sigma` 0.2 on S3 and S4, an opposite
   case's nearest distance (median about 0.53-0.58) overlaps a true match's largest (about 0.62), so "opposite
   exceeds `D*` in at least 95% of trials" may fail at the largest spread, which §20 anticipated. Part of the cause
   is the design: "opposite" is opposite to the generating objective only, and with five random profiles another
   objective can sit near it. Step 10 should report the opposite case's distance to the generating objective
   beside its nearest distance. **Cost:** one match runs six bootstraps at 100,000 resamples. `D*` needs only the
   point distances; `k*` needs the tie, so step 10 should time it and set `resamples` for the simulation openly.
   (h) **The rubric's format is Phase 5's.** The matcher takes `CompanyDecision`; Phase 5's IMPLEMENTATION doc writes
   the loader from the committed rubric to it, uncertain calls to alternative readings included.
10. **[done 2026-10-08, Opus] The simulations** (§14): the timing run, then the full run, then the report. Opus reads every number
    against its target and writes the findings into this doc's §20.
    *As built.* **The findings are §20a (ten, for him and step 12); this entry is how they were produced.**
    **The timing run decided the method.** One engine comparison costs about 50 ms; §14.1's grid is about 17.3 million
    replicates (20,000 at every null and threshold point), so the engine itself would need about 240 core-hours, and the
    null and threshold points that may never be thinned are 14.4 million of them. So **the no-failure share grid uses the
    exact bootstrap** (`simulation/exact.py`): on a lattice the engine's resampling distribution is a convolution,
    computed by FFT, whose percentile ends are the engine's ends with infinitely many resamples. It equals a brute-force
    enumeration of every resample (a test, three alphas); the engine at 1,000,000 resamples lands within 0.0013 of it;
    and in the run itself 954 of 960 verdicts agree with the engine at 100,000 (the six others sit at a boundary within
    the engine's own Monte Carlo error). Every verdict is `verdict.decide`. **Choice rates are exact** (binomial sums over
    the analysis's own Newcombe and `decide`). **The engine itself, end to end on run rows,** carries failures and the
    bound (162 settings, with an independent rebuild of the bound on every replicate), the wording rule (36 settings,
    label recomputed independently), the resample count (§14.3) and the matcher (the analysis's `match_case`, 10,000
    resamples for its 95% gap interval, recorded). Throughput was bounded by memory bandwidth (about 2,300 replicates a
    second at any worker count above 8), so the exact routine sizes each transform to the cells' own ranges and works
    in chunks of 4: about 6,500 a second. **The full grid ran unthinned in 68 minutes on 10 workers**; thinning the
    only points §14.1 allows to be thinned would have saved about 4 minutes, so the "about an hour" guide was exceeded
    by choice, recorded here.
    **Added to §14.1's families, each saying why in the summary:** the repeat rule's own n (power at 1.5 T, "no split
    reachable" at 0); a near-all-agree family with decision 10's candidate and a wider reading, plus an interior
    all-agree case; a finer lattice (1/1000) beside S1's; a 0.10 wording shift (the planning's 0.03 and 0.05 never
    reverse a split-sized difference); a count of interval ends near a boundary (how many verdicts the seed can move).
    The share distributions are exact on the lattice: the Beta part's mean is solved so the mixture's mean is the
    stated one, so two sides differ by exactly the stated difference.
    **Outputs, all by code:** `hc simulate run` writes `evidence/phase-3/simulation-results.json` (2.6 MB; every point,
    its seeds, its counts); `hc simulate report` writes `simulation-summary.md` and `matcher-calibration.md`; a test holds
    both equal to what the report makes of the committed JSON. **Reproducibility:** each task's seed is derived from its
    name, so the file does not depend on worker count or finish order (the quick run is byte-identical at 10 and 3
    workers). The file records a **sha256 of the code and data it depends on** (the analysis package, the simulation
    package except its report, the company experiment, `uv.lock`) instead of a git sha, since a file cannot name the
    commit that contains it; checked equal to the code as committed after the run and after the mutation check.
    **`D*` and `k*` live in `analysis/matcher_thresholds.toml`**, per shape, read by `match_case` (a `shape` argument,
    default the scenario's id), because writing them into code would change the hash the results record; Phase 3.5's
    folder hash still freezes them, and a test holds the file equal to the report's rendering of the results.
    `hc simulate` imports the simulation inside its command (a new architecture test), since the container image has
    no numpy and `hc` is its entry point. **Progress lines are block-buffered** when the run's output goes to a file;
    set `PYTHONUNBUFFERED=1` to watch them.
    **The results file is 2.6 MB, over the 1,024 KB large-file hook** (1.8 MB even compact; compressing it would make a
    binary the name guard cannot scan). With his approval (2026-10-08), `.pre-commit-config.yaml` excludes that one path
    from `check-added-large-files`; checked that it passes while any other file over the limit is still refused.
    **Mutation checks:** simulation code, 43 planted, 42 caught, one equivalent (the transforms' scale, which the
    quantile search divides out); the first pass caught 33 and showed ten gaps, now tested with cases built so the
    outcome is forced (point masses that make the bound overturn, a wording whose difference is exactly zero beside a
    negative split, the candidates' threshold where 0.1 and 0.2 differ, and more). The thresholds loader, 8 planted,
    8 caught after one gap (`d_star = 0.0`). Tests: `tests/test_simulation_exact.py`, `test_simulation_verdicts.py`,
    `test_simulation_report.py`; 1176 in all.
    **Step 9's flags, resolved:** `run_distance` stays in `descriptive.py`; `D*`/`k*` are set; the matcher's refusal of
    an objective with nothing to distance (finding (b)) occurs in 90 of 270,000 synthetic trials.
11. **[Opus] `plain-english.md`**, finished from the notes kept since step 3.
12. **[Opus, then him] The patches:** decisions 3, 4, 6 and 7, plus anything step 10 found (decision 10 included),
    as dated patches to `planning/07`, each shown to him before it is applied.
13. **[Sonnet] Close-out:** the DoD audit (§19), `ROADMAP.md`, START HERE, `KNOWN-GAPS.md`.

## 19. Definition of done, and the proof of each

| DoD (scope doc) | Proof |
|---|---|
| 1. Each interval method agrees with published worked examples, and with its library | `worked-examples.md` with live sources; the tests in CI |
| 2. The verdict engine returns the known answer, shares and choice rates, the all-agree case included | the known-answer tests, built independently of the engine |
| 3. The simulations are recorded; a miss is patched before Phase 3.5 | `simulation-summary.md` and `simulation-results.json`; every target in §14.1 met, or its dated patch |
| 4. The matcher's no-match threshold and minimum-evidence rule are set | `matcher-calibration.md`, with `D*` and `k*` |
| 5. The failure rules, robustness rules and descriptive analyses each have tests | the test files, green |
| 6. No model was called; `make check` and CI green | the network guard test; the CI run ids |

**Amended by decision 1:** the scope doc's Delivers 8 (the JSON under a new schema version) is replaced by the
versioned results object; the JSON moves to Phase 1.5. **Amended by decision 4:** DoD 3 includes the false "no
split" target.

## 20. Genuinely uncertain

- **How narrow the bootstrap runs at these sizes.** At 30-60 runs per objective and a 99.7% interval, the percentile
  bootstrap is known to cover less than it claims. If it does here, the false-split and false-no-split targets will
  show it, and the fix (a wider method, or a correction) is a dated patch. This is the most likely finding.
- **The simulation's run time.** Estimated at well under an hour vectorized; the timing run says.
- **Newcombe's published table.** One of eight recalled values disagreed with statsmodels (§3a). Step 3 settles it
  from a live source.
- **Whether `D*` and `k*` come out usable.** If the true-match and opposite cases overlap at the largest spread, no
  threshold separates them; then "no good match" is defined at the design spread only, and the methods page says so.

**Settled by step 10 (2026-10-08, Opus), each in a line; the evidence is in `evidence/phase-3/simulation-summary.md`
and `matcher-calibration.md`, every number from `simulation-results.json`:**
- *How narrow the bootstrap runs:* **narrower than it claims, as predicted.** Finding 1 below.
- *Run time:* the engine itself on §14.1's grid would take about 240 hours on one core; the exact bootstrap (step 10
  as built) ran the full grid, unthinned, in 68 minutes. The estimate "well under an hour" was wrong by two orders of
  magnitude for the engine and about right for the method used.
- *Newcombe's table:* settled in step 3.
- *`D*` and `k*`:* both come out, per shape; `D*` does not separate opposite cases from true matches. Finding 6.

### 20a. Step 10's findings, for him and for step 12

Targets are per comparison, 0.05 / 16 = 0.3125%. "Clearly missed" means the 95% Wilson interval's lower end is over
the target. Each finding names what step 12 should decide; none is decided here.

1. **False split, shares: clearly missed across most of the grid.** At a true difference of 0, the share rule says
   "split" more often than 0.3125% at 272 of 360 points (267 clearly); median 0.59%, worst 2.22%. By pi (the share of
   all-in runs): pi = 0, 50 of 120 points over, median 0.10%, and **within target everywhere sigma <= 0.10** (worst
   0.28%); pi = 0.2, 102 of 120, median 0.62%; pi = 0.5, all 120, median 0.76%. By repeats per wording: worst 2.22%
   at 6, 1.49% at 10, 0.98% at 15, 0.67% at 20, so even the cap does not reach the target once runs go all in, which
   models often do. A finer lattice (1/1000) gives the same rates, and a wording shift shared by both objectives
   changes nothing, so this is the percentile bootstrap's known narrowness in the tails at small samples, not the
   lattice or the design. **Consequence:** the family-wise false-split rate for the eight share comparisons is not
   held at the 5% the design claims; at the worst points it could be several times that. **For step 12:** a dated patch
   to `planning/07` §6.3 replacing or correcting the share interval, evaluated by re-running this grid. Candidates,
   all standard and all pre-registrable: a studentized (bootstrap-t) interval; the "expanded" percentile interval
   (Hesterberg's small-sample correction); BCa; or an alpha calibrated on this grid so the worst point meets the
   target. The cost of each in power must be measured beside its false-split rate. **Opus's recommendation: evaluate
   the studentized and expanded intervals first**; a calibrated alpha is simplest but fits the correction to this grid.
2. **False no split, shares (decision 4): missed at some points, mostly mildly.** At a true difference of exactly T,
   "no split" more often than target at 49 of 360 points (34 clearly); median 0.015%, worst 1.29%. The misses sit at
   small spreads with rare all-in runs (worst: mu 0.1, sigma 0.02, pi 0.2, 20 per wording), where a sample with few
   runs at 1 gives a narrow interval. Finding 1's fix should be judged on this target too, and finding 3's.
3. **Decision 10 is triggered, and the candidate as written is not enough.** Near-all-agree runs (one objective all in
   at 1 always, the other 90% of the time; a true difference of exactly T) give a false "no split" 15.5% of the time
   at 6 per wording, every one from a zero-width interval; 4.1% at 10. **The candidate as written (c1: every run of
   both objectives at one boundary value, then Newcombe on the share at that value, less certain verdict kept)** fixes
   the exactly-identical cases only: near-identical ones still give up to 3.55% false "no split" (mixture, 1 vs 0.8,
   6 per wording), and it never fires when every run sits at the same interior value (all keep 100 of 125), which
   gives the same [0, 0] and up to 3.5% false "no split" at a true difference of T. **A wider reading (c2: every run of
   either objective at one boundary value)** removes nearly all of the false "no splits" but costs power where the
   runs go all in (a 45% split rate falls to 7% in one setting). On the main grid both are nearly free (c1 changes 17
   of 17.28 million verdicts; c2 1,377, of which 852 splits). **For him, before C7 (as agreed in decision 10):** the
   evidence says the fix must cover near-identical runs and interior values, not only exact boundary agreement. Opus's
   recommendation: let finding 1's corrected interval carry most of it, and add a degenerate-interval rule for what
   remains (a share comparison whose interval is narrower than the outcome's own grid step, 1/125 for S1, is never a
   "no split"), re-run on this family. Detail: summary section 4.
4. **Failures cost far more than the planning assumed (decisions 3 and 6, measured).** The rules are correct: in 162
   failure settings run through the engine, **no verdict was kept that the bound overturns, and the engine agreed with
   an independent rebuild of the bound on every replicate.** But at 20 per wording a true 15-point difference is a
   split 93.5% of the time with no failures, 74% at 2% random failures, 40% at 5%, 6% at 10%; at 6 per wording any
   one failure drops its wording, so at 10% failures over a third of comparisons are "not assessable". Decision 3
   priced the bound at "up to the failure rate"; the measured cost is several times that, because the bound widens the
   interval as well as moving the difference, and the 10% exclusion bites early in small cells (step 5 finding (c)).
   **For step 12 and Phase 3.5's model choice:** a model's failure rate is a first-order factor in what the study
   can conclude. Whether to soften the bound (for example, applying it only when failures exceed a stated rate) is a
   design question for him; the planning's intent (failures must not manufacture a verdict) holds as built.
5. **The wording rule works; the planning's shifts never test a reversal.** No false alarm above 0.5% of splits with
   no shift; a true reversal in one wording flagged in 87-100% of splits; 0 labels differing from an independent
   recomputation. But §14.1's shifts (0.03 and 0.05) cannot reverse a split-sized difference in any wording; step 10
   added a 0.10 shift to test it. The summary says so; step 12 can widen §14.1's grid or note it.
6. **The matcher: `D*` and `k*` set; "opposite" is missed, and "no good match" is weak.** `D*` (from the true matches
   at sigma 0.20): S1 0.348, S2 0.679, S3 0.546, S4 0.656. `k*` (80% identification at sigma 0.10): S1 2, S2 3, S3 2,
   S4 3. **The opposite check (95% of opposite cases beyond `D*`) is missed on every shape: 15-65%.** Yet 99.8-100% of
   opposite cases are beyond `D*` from their *own* objective: with five random profiles, another objective usually
   sits near the "opposite" decision. So the matcher separates an objective from its opposite, and "no good match"
   rarely fires because the nearest of five is usually close enough. Ties are common (true matches at sigma 0.20: tie
   45-59%). In S4, identification peaks near 92% at 8 dimensions and falls slightly with more (more lines, more
   noise). Unmatchable cases (step 9 finding (b)): 90 of 270,000 trials, all with a single dimension. **For step 12:**
   (a) whether the opposite check should be judged against the generating objective's distance, as it now reads,
   or kept and reported as missed; (b) whether `D*` should come from the spread the official grid actually shows (its
   runs are known before any real case runs, and nothing about the cases), which would make "no good match" mean
   something at realistic spreads. The thresholds are set as computed (`analysis/matcher_thresholds.toml`).
7. **Choice rates: Newcombe slightly over at 50%.** False split 0.417% at p = 0.5, 15 per wording, and 0.394% at 6:
   2 of 28 points, both just over; exact, not sampled. False no split met everywhere (worst 0.094%). The repeat rule
   sends choice rates to 20, where the 50% point is 0.28%, inside. Step 12 can note it; no change is needed at the cap.
8. **The repeat rule's stated numbers.** About +-8 points at sd 0.15 and the cap: **7.9**. Choice +-27 and +-12:
   **25.2 and 15.9** (step 8). A 30-point choice difference near 50% a split 63%: **62.9%**; 35 points, 80%: **81.9%**.
   80% power for 15 points at sd 0.15 and 10 per wording: **84.4%**. "No split reachable about 54%" at rule (b)'s n:
   **48.6% at worst** where the cap does not bind (higher where the floor of 6 binds); where the cap binds it falls to
   0.4% (median), so for wide or all-in spreads "no split" is unreachable at 20 per wording. Power at 1.5 T where the
   cap does not bind: 96.8-100%; where it binds: median 61%, worst 22%.
9. **Decision 7 is supported.** Near a boundary, a verdict flips with the engine's seed on 33% (no split) and 16%
   (split) of 200 seeds at 10,000 resamples, and on 13.5% and 0% at 100,000. Across the grid, 1.70% of replicates had
   an interval end within 0.001 of a boundary and 4.98% within 0.003, so at most a few percent of verdicts can depend
   on the seed, and the seed is fixed by rule. The exact bootstrap and the engine agreed on 954 of 960 validation
   verdicts; all six disagreements sit at a boundary within the engine's Monte Carlo error.
10. **For the methods page:** the share rule as pre-registered would have had a false-split rate above its stated
    level; the simulation found it before any real result existed, which is what the simulation is for.

## 21. Cost

**$0.** No model call, no AWS resource. Simulations run on the laptop. One throwaway download of the libraries was
made while writing this doc (§3a), outside the project.
