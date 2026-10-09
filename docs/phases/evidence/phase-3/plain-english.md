# The statistics in plain English (Phase 3)

**Finished at step 11 (2026-10-08) from notes kept since step 3** (IMPLEMENTATION doc §18; `planning/04` §6.2: the
statistics must be explainable, not only computed). Plain words first, formulas last. This is the record the
methods page draws on; the methods page itself is his to write. **Updated at step 12 (2026-10-09):** the share
interval, the all-agree rules, the repeat rule's quantile, the matcher's dimension count and reading rule, and the
simulations re-run on the rule as adopted (IMPLEMENTATION doc §20b).

## 1. What is being compared

The same model makes the same decision many times: under five objectives (A to E), three wordings of each, and
several repeats of each. A **run** is one decision. A **cell** is one objective under one wording. Each scenario has
one **primary outcome**:

- **Shares** (S1, S2): a number between 0 and 1. S1, the share of the 125 people who keep a job; S2, the share of a
  $112.1 million gap the workforce bears.
- **Choice rates** (S3, S4): yes or no per run. S3, did the model close the plant; S4, did it fund the program. The
  rate is the share of runs that did.

There are 16 primary comparisons per model (four pairs of objectives on four scenarios). Each asks one thing: do
these two objectives lead the model to decisions that differ by enough to matter?

## 2. The intervals (step 3)

**What an interval is for.** The runs are a sample: ask again and the numbers move a little. The interval is the
range of differences the data cannot rule out.

**Why 99.7% and not 95%.** At 95%, about one comparison in twenty crosses the line by chance alone, so across 16 a
false finding is likely. Dividing the 5% by 16 keeps the chance of even one false split across all 16 near 5%. Each
interval leaves out 0.05 / 16 = 0.3125%, so it covers 99.6875%: "99.7%" in prose.

**Choice rates.** Newcombe's method builds a range for each objective's rate, then combines the two. Its useful
property: even when every run in both groups made the same choice, it still says "not certain," rather than claiming
a difference of exactly zero with no doubt.

**Shares** (changed at step 12). These are amounts, not yes or no. Each objective's value is the average of its three
wordings' averages, so every wording counts the same even if one lost runs to failures. The interval is the
difference plus or minus a margin built from how much the runs vary inside each wording (Welch's t-interval): the
more the runs within a wording disagree, and the fewer there are, the wider the margin. Variation between wordings
does not count as noise, since the wordings are fixed, not a sample.

**Why it changed.** The plan was to resample the runs: treat them as the whole world, draw new samples 100,000 times,
and see how much the difference moves. The simulations (section 9) showed that interval is too narrow at these sample
sizes, so it would call a split by mistake up to seven times as often as the stated level. Welch's interval held the
stated level on the same made-up data, and it needs no random draws, so there is no seed and no draw-to-draw wobble.
The resampling interval stays for the matcher, which is a 95% reading, not a verdict; its random sequence is fixed by
a rule (from the sweep's id and the reading's name), so nobody picks it.

## 3. The verdicts (step 4)

**Three answers, never two.** A comparison ends as **split**, **no split**, or **inconclusive**.

- **Split** needs two things at once: the interval sits entirely on one side of zero (the difference is not noise),
  and the difference is at least the threshold (10 points for a share, 20 for a choice rate: big enough to matter).
- **No split** needs the whole interval inside plus or minus the threshold: the data rule out any difference that
  would matter.
- Everything else is **inconclusive**, and is published as that, not as a lean either way.

**A real but small difference is a no split.** An interval of 1 to 5 points means the difference is probably real
and too small to matter by the rule fixed in advance. "No split" means no difference of a size that counts, not
"identical decisions."

**When the runs agree (two extra rules for shares).** If nearly every run lands on the same number, the margin above
shrinks toward nothing and the interval can claim "no split" with confidence it has not earned. Two rules stop that.
**(a)** An interval narrower than one person out of 125 can never support "no split." **(b)** When every run under
one objective gave the same answer, the comparison is also made the way a yes-or-no rate is (how many runs landed on
that answer under each objective, by Newcombe), and if the two ways disagree the result is inconclusive. Both rules
can only make a verdict less certain, never more. In the simulations they took the worst false "no split" on runs
that nearly all agree from about 15 in 100 down to about 3 in 1,000.

**Edges go to the weaker answer.** An interval that ends exactly at zero does not exclude zero; one that ends
exactly at the threshold is not inside it. A difference of exactly the threshold does reach it ("at least").
Computer arithmetic can land a hair off (57/60 minus 45/60 gives 0.19999999999999996), so every edge allows a margin
of one billionth, far smaller than the smallest step an outcome can take (1/125).

## 4. Failed runs (step 5)

Some runs fail: the model answers in the wrong format, the numbers do not add up, or it declines.

- **Failures are counted, never filled in.** A failed run has no outcome, and none is invented for it.
- **A cell that fails more than 10% of the time is dropped,** and its wording is dropped from both sides of every
  comparison it is in, so the two objectives are always compared over the same wordings. The verdict says which
  wordings it is over.
- **The worst-case check.** Before a verdict stands, the failed runs are set to the most damaging values (0 or 1)
  and the whole verdict is recomputed. A split that the worst case could erase, or a no split it could break in
  either direction, becomes inconclusive. Failures can make a result less certain; they can never manufacture one.
- **First attempt beside final.** A run that failed and was retried is also scored on its first attempt, to show
  whether retrying changed anything.

**What the simulations found:** the check is correct (an independent rebuild agreed on every replicate), and it is
expensive. A real 15-point difference is found 93.5% of the time with no failures, 40% at 5% failures, 6% at 10%. A
model that fails often cannot support strong conclusions, so reliability matters as much as price when choosing it.

## 5. The wordings and the order of the menu (step 6)

**The wording check.** Every objective is asked three ways. A split counts as **robust** only if each wording, on its
own, points the same way; if any wording reverses it or shows no difference, the split is labelled
**wording-sensitive**. The verdict stays "split"; the label travels with it. In the simulations a real reversal was
flagged 87-100% of the time and a consistent split almost never (0.5% at most).

**The sealed wording.** One wording (`w2`) was never used during development, so it cannot have been tuned. Its
runs alone are compared too, outside the 16, as a check.

**Menu order.** Each run shows the options in a shuffled order, and the analysis checks whether position on the menu
moved the answer (a 95% reading, not a test).

## 6. The descriptive analyses (step 7)

Beside the 16 verdicts, the full picture without verdicts: every line of every allocation, by objective and wording,
with its spread; the choices; the secondary outcomes; and how far E (no stated objective, the model's default) sits
from each objective, beside how far each objective sits from itself, so a large distance is not mistaken for noise.
Every run's values are kept, so the spread can always be drawn.

## 7. How many repeats (step 8)

A small pilot (two repeats, the two development wordings) measures how much runs vary within a cell. From that
spread, the number of repeats per cell is chosen so the interval is narrow enough for "no split" to be reachable
(its half-width at most 0.8 of the threshold), between 6 and 20. The margin uses the same t value as the share
interval, so the rule and the verdict agree on what "narrow enough" means. Choice rates always get 20, the cap. **The
repeat count carries no direction:** it is computed from spread alone, so setting it reveals nothing about which way
any comparison leans. At the cap, the share interval is about plus or minus 8 points at a spread of 0.15, and the
choice-rate interval about plus or minus 25 points near 50% and 16 near 5%.

## 8. The matcher (step 9)

**What it asks.** For a real case, which objective's runs came closest to what the company actually did. A reading,
not a test: no verdict, 95% intervals.

**Only what was disclosed.** A filing shows some of what a company did and not the rest. Runs and company are
compared on the disclosed lines only, rescaled so each side's disclosed money adds to 1, and on the choice if known.

**Distance per run, then averaged.** Each run is compared with the company on its own (half the sum of the
differences in proportions, 0 to 1; plus 0 or 1 for the choice; averaged when both exist). An objective's distance is
the average over its runs. Averaging the runs first would invent a decision: half the runs all in on one thing and
half on another average to a split no run made.

**Four answers, never forced.** *Not enough disclosed* when too few things are known to tell objectives apart.
Counting what is known: the choice counts one; disclosed money lines count one fewer than there are, because once
each side is rescaled to add to 1, the last line is fixed by the others (a single line alone tells nothing).
*No good match* when even the nearest objective is far. *Tie* when the gap between the two nearest could be zero.
Otherwise *match*. The cut-offs are set from synthetic cases with known answers before any real case runs.

**More than one reading.** Where the rubric is unsure what the company did, each reading is matched. The case
"depends on reading" only when the readings point to different objectives with nothing in common: a tie between B
and D under one reading and B alone under another is the same answer, not a change.

**Known limits.** With five objectives, one usually lands near any decision, so "no good match" will be rare (section
9). The matcher does tell an objective from its opposite: in the simulations, the objective that generated a case
almost always sits far from that case's opposite.

## 9. The simulations (step 10)

**What they are for.** Before any model's decisions are seen, the rules are run on made-up decisions whose true
answer is known: objectives that truly do not differ, that differ by exactly the threshold, or by more. Counting how
often the rules get those wrong shows what the rules can and cannot claim.

**How they were run.** Millions of made-up comparisons, each judged by the same rules the real data will be.
At step 10 the share interval was the resampling one, and since re-drawing 100,000 times for each of millions of
comparisons would take about ten days of computing, every possible re-draw was counted at once, exactly (the fast
Fourier transform). At step 12 the share interval became Welch's, which needs no re-drawing, so the whole set ran in
about twelve minutes. To be sure the simulation's fast version of the rules is the rule itself, 21,200 made-up
comparisons were also run through the real analysis code: the same answer every time. Choice rates needed no
simulation: their verdict depends only on two counts, so every pair of counts was weighed by its exact probability.

**What they found.**
- When two objectives truly do not differ, the share rule should say "split" by mistake at most about 3 times in
  1,000. The resampling interval did so up to about 22 times in 1,000 when models go all in on one answer, which
  they often do. That was fixed before anything was pre-registered: with Welch's interval and the two rules for
  runs that agree, the worst rate is about 4 in 1,000 and the typical one about 1 in 1,000. A handful of the most
  scattered settings still sit a little above 3 in 1,000, so the methods page states the level as held
  approximately, with the measured worst case.
- When nearly every run agrees, the first rule could call two objectives the same with a confidence it had not
  earned: up to 15 in 100 times where the true difference was the threshold. The two rules bring that to about 3 in
  1,000.
- The fix costs some power where runs are few: a real difference of 15 points is found less often at 6 repeats than
  it was, though much of the old interval's apparent power was the same narrowness that broke its error rate.
- Failed runs cost more than expected (section 4).
- The matcher tells an objective from its opposite (the generating objective sat beyond the no-match line in 99.8%
  to 100% of opposite cases), but "no good match" will be rare. A single disclosed line identified the right
  objective about 40% of the time, which is chance among five with ties, confirming it tells nothing.
- The numbers the plan stated in advance: the choice-rate power figures held (63% and 80% stated; 62.9% and 81.9%
  measured); the share interval at the cap is about 8 points as stated (8.3 measured); 80% power for a 15-point share
  difference at about 10 repeats is 76.5% at exactly 10 (the rule asks for 11 there).

**Why this matters for the claim.** Had the first rule gone into the pre-registration unchanged, a "split" on a share
would have been less certain than the published level said. Finding that before any real result exists is the point
of simulating first.

## 10. Questions an interviewer is likely to ask, with short answers

- **"Why three verdicts instead of significant or not?"** Because "not significant" mixes two different things: the
  data show no difference that matters, and the data are too thin to tell. The study needs to say which, since "no
  split" is the claim the Roundtable statement implies.
- **"Why divide by 16?"** Sixteen comparisons per model; at 95% each, one false split across the set would be likely.
  Bonferroni is blunt but simple, and conservative is the right direction for this claim.
- **"Why Welch for shares and Newcombe for choices?"** Choices are yes or no, where Newcombe is the standard and does
  not collapse when every run agrees. For shares the plan was a bootstrap, since shares have odd shapes (often all in
  at 0 or 1). The simulations showed it too narrow at these sample sizes; nine candidates were then tested on the same
  made-up data, and Welch's t-interval, with two rules for runs that agree, held the stated error rate. The choice
  was made on that evidence, before any real result existed.
- **"How do you know your code is right?"** Known answers built without the engine; published worked examples for
  Newcombe; scipy's own Welch test and a hand-worked example for the share interval; independent rebuilds of the
  failure and wording checks and of the share rule itself, checked against the analysis replicate by replicate; and
  mutation checks: bugs planted on purpose, one at a time, to confirm the tests catch them.
- **"What did the simulations change?"** The share interval (bootstrap to Welch), the all-agree rule (widened to near
  agreement and to any value), and the known cost of failures, all before pre-registration.

## Formulas

- **Wilson**, one rate p = x / n at z: centre (p + z²/2n) / (1 + z²/n); half-width
  z / (1 + z²/n) · √(p(1 − p)/n + z²/4n²); giving (l, u).
- **Newcombe**, d = p1 − p2: from d − √((p1 − l1)² + (u2 − p2)²) to d + √((p2 − l2)² + (u1 − p1)²) (Fagerland,
  Lydersen and Laake 2011, equation 7). z = 2.9552 at the family level (alpha = 0.05 / 16).
- **Stratified Welch t-interval** (shares): d = the difference of the two objectives' means of wording means;
  SE² = Σ over every cell of both objectives of s² / (W² n), with s² the cell's sample variance, n its runs and W the
  wordings; df = SE⁴ / Σ (term² / (n − 1)); the interval is d ± t(1 − 0.003125 / 2, df) · SE. With no spread in any
  cell it is [d, d], which rules (a) and (b) then decide.
- **Rule (a)**: a share interval narrower than 1/125 is never a no split. **Rule (b)**: when every run of either
  objective holds one value v, Newcombe on (runs at v) / (runs) for each objective, at the share threshold; the less
  certain of the two verdicts is kept.
- **Repeats**: the smallest n with t · sd · √(2 / (3n)) ≤ 0.8 T, t taken on 6 (n − 1) degrees of freedom, between 6
  and 20; the interval's half-width at n is t · sd · √(2 / (3n)).
- **Stratified percentile bootstrap** (the matcher only, 95%): per wording, resample the cell's runs with replacement,
  as many as it holds; average; average the wordings; the interval is the 2.5% and 97.5% points of 100,000 draws.
- **Matcher distance**: ½ Σ |a_i − b_i| over the disclosed lines, each side rescaled to sum to 1; plus 1 if the
  choices differ; averaged when both exist.
