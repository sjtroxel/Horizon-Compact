# The statistics in plain English (Phase 3)

**Notes kept as each part is built; finished at step 11** (IMPLEMENTATION doc §18). Plain words first, formulas
after. This is the record the methods page draws on later; the methods page itself is his to write.

## The intervals (step 3, 2026-10-08)

**What an interval is for.** Every comparison asks whether two objectives lead the model to different decisions.
The runs are a sample: ask again and the numbers move a little. The interval is the range of differences the data
cannot rule out. If it sits clearly away from zero and the difference is large, that is a split; if it sits
inside a small band around zero, that is no split; anything else is inconclusive.

**Why 99.7% and not 95%.** There are 16 primary comparisons per model. At 95%, about one in twenty would cross the
line by chance alone, so across 16 a false split is likely. Dividing the 5% error by 16 keeps the chance of even one
false split across all 16 at about 5%. Exactly, each interval leaves out 0.05 / 16 = 0.3125%, so it covers 99.6875%;
"99.7%" in prose.

**Choice rates (did the model close the plant, fund the program).** Each run either made the choice or did not.
Newcombe's method builds a range for each objective's rate (Wilson's), then combines the two. Its useful property
here: even when every run in both groups made the same choice, it still says "we are not certain", rather than
claiming a difference of exactly zero with no doubt.

**Shares (how many people kept, how much of the cost the workforce bore).** These are amounts, not yes or no, so
the interval comes from resampling: pretend the runs we have are the whole world, draw new samples from them many
times (100,000), and see how much the difference moves. Draws are made within each wording, so a wording that ran
a bit high cannot leak into another's. Each objective's value is the average of its three wordings' averages, so
each wording counts the same even if one lost runs to failures.

**The known weak spot.** If every run under both objectives gives the identical share, resampling can only ever
reproduce it, and the range collapses to a single point: false certainty. Decision 10 deals with it once the
simulations show how often it happens.

**Formulas.** Wilson for one rate p = x / n at z: centre (p + z²/2n) / (1 + z²/n), half-width
z / (1 + z²/n) · √(p(1 − p)/n + z²/4n²), giving (l, u). Newcombe for p1 − p2 = d: from d − √((p1 − l1)² + (u2 − p2)²)
to d + √((p2 − l2)² + (u1 − p1)²) (Fagerland, Lydersen and Laake 2011, equation 7). z = 2.9552 at the family level.
Bootstrap: the 0.15625% and 99.84375% points of 100,000 resampled differences.

## The verdicts (step 4, 2026-10-08)

**Three answers, never two.** A comparison ends as a split, no split, or inconclusive. "Split" needs two things at
once: the interval sits entirely on one side of zero (the difference is not noise), and the difference is at least
the practical threshold (10 points for a share, 20 for a choice rate: big enough to matter). "No split" needs the
whole interval inside plus or minus the threshold: the data rule out any difference that would matter. Everything
else is inconclusive, and is published as that, not as a lean either way.

**A real but small difference is a no split.** If the interval is, say, 1 to 5 points, the difference is probably
real, and too small to matter by the rule fixed in advance. That is what "no split" means: no difference of a size
that counts, not "identical decisions."

**Ties go to the weaker answer.** An interval that ends exactly at zero does not exclude zero; one that ends exactly
at the threshold is not inside it. A difference of exactly the threshold does count as reaching it ("at least").
Computer arithmetic can land a hair under 0.2 when the true answer is exactly 0.2 (57/60 minus 45/60 gives
0.19999999999999996), so every comparison allows a margin of one billionth, millions of times smaller than the
smallest step an outcome can take (1/125).

**The known weak spot, made visible.** If every run under both objectives gives the identical share, the resampling
interval has no width and the rule says "no split" with a certainty the data cannot support. The engine flags this
case on every comparison; decision 10 decides what to do about it.

## The matcher (step 9, 2026-10-08)

**What it asks.** For a real case, which objective's runs came closest to what the company actually did. It is a
reading, not a test: no verdict, and its intervals are 95%.

**Only what was disclosed.** A filing shows some of what a company did and not the rest. The matcher compares runs
and the company on the disclosed lines only, rescaled so each side's disclosed money adds to 1, and on the choice if
the choice is known. Two runs that spent the same proportions on those lines are at distance 0, whatever they did
elsewhere.

**Distance per run, then averaged.** Each run is compared with the company on its own (half the sum of the
differences in proportions, 0 to 1; plus 0 or 1 for the choice; the two averaged when both exist). An objective's
distance is the average over its runs. Averaging the runs first would invent a decision: half the runs all-in on one
thing and half all-in on another average to a split that no run made.

**Four answers, never forced.** *Not enough disclosed* when too few dimensions are known to tell objectives apart.
*No good match* when even the nearest objective is far. *Tie* when the gap between the two nearest could be zero
once the runs are resampled. Otherwise *match*. The two cut-offs (how far is "far", how few is "too few") are set
from synthetic cases with a known answer before any real case is run, so neither is chosen after seeing a result.

**A known limit, for step 12.** One disclosed line on its own carries no information: rescaled to add to 1, every
run that put anything there looks identical to the company.
