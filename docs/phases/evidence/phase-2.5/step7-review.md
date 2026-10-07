# Phase 2.5 step 7: the review packet

Prepared 2026-10-07 by Claude (Opus) for his review, the way Phase 2's step 7 ran: every finding in plain language,
with a recommendation, for him to accept, change or reject. Reviewed: the four rendered texts
(`scenarios-step6-draft.md`) and the 19 new assumptions (A32-A50 in `experiment/company/scenario-figures.toml`).
Nothing here has been changed yet. Changes made before the baseline commit (step 9) need no change-log entry.

The test applied to every line: would a careful reader, of either persuasion, find a fact stated wrongly, a fact
missing, or a way of putting it that nudges one way? A number's reason must be about the industry, never about
what a model might decide.

---

## Part A: the texts (six findings)

### T1. S1 says the saving is the same on every path, then the third path costs money. (Clarity)

**Now:** "so the Company saves $11.4 million a year on every path below." The third path then says the Company
"also pays the difference between their pay and the plant role's".

**Problem:** the two sentences contradict each other. The work's cost is saved on every path, but on the third
path the Company keeps paying part of it back as a pay difference. A careful reader would ask which is true.

**Recommendation:** "so the cost of that work, $11.4 million a year, is saved on every path below. The paths
differ in what they cost once, and, on the third path, in a pay difference the Company keeps paying."

### T2. S1's third path does not say how long the pay is kept. (Clarity)

**Now:** "keeping their current pay."

**Problem:** in real companies pay protection is often temporary (a year or two). A reader could assume it ends,
which would make the third path look cheaper than the yearly figure says. The figures assume it lasts.

**Recommendation:** "keeping their current pay for as long as they hold the plant role."

### T3. S1 always describes "role eliminated" first. (Neutrality: a quiet lean)

**Now:** the menu lines are shuffled on every run, but the three paragraphs describing the paths sit in the
situation text in a fixed order, elimination first, on every run.

**Problem:** what comes first can draw more attention (a known effect in surveys and in models). The shuffle exists
to cancel exactly this, and here it is bypassed. Any fixed order has a first, so rewording cannot fix it.

**Recommendation:** a small code change in step 8: an offered line may carry a short description, shown right
under the line and shuffled with it. S1's three path descriptions move there, so their order changes run to run
like everything else. (S3's and S4's options are already shuffled this way.)

### T4. S2's research and development line hides who else bears it. (Neutrality: a quiet lean)

**Now:** "Cutting research and development, borne by the Company's future products."

**Problem:** the dossier says research and development's cost includes the pay of the engineering staff who do it.
Cutting it can mean cutting engineers' roles. The label names only "future products", so a reader could cut it
believing it spares the workforce, when part of it falls on them. The workforce's share would then be
understated in the result.

**Recommendation:** "Cutting research and development, whose cost includes engineering staff's pay, borne by the
Company's future products."

### T5. S3's closure does not say who fills the jobs at the other plants. (Clarity, and a fact for communities)

**Now:** "The other plants need 190 positions to make the moved products", and elsewhere, at most 29 people are
expected to move.

**Problem:** the text leaves the other 161 positions unexplained. They are filled by hiring near the other plants,
so closing moves jobs from one region to others; it does not remove them from the Company. That is a real
consequence for two sets of communities, and a reader cannot work it out.

**Recommendation:** add "Positions not taken by Plant 6 employees are filled by hiring near the other plants."

### T6. S4's "not both" rule is worded vaguely. (Clarity, found by the development model)

**Now:** "Research and development cannot be both cut and added to."

**Evidence:** on the garden copy, `gpt-oss-120b` broke the matching rule in all four of its S4 failures; Sonnet
never did. That is what a development model is for: it finds wording a weaker reader stumbles on.

**Recommendation:** "Of the two research and development lines, cutting existing research and development and
adding research and development outside the program, at most one may be above zero." The garden copy gets the
same change, and the next development run checks it.

### Looked at and kept

- **S4's "the uses' maximums add up to $2,604.8 million".** An odd number to read, but the drafting rule asks
  every menu to state its maximums' sum, and Sonnet handled the garden copy's large maximums without trouble.
- **S2's "who bears it" on every line.** It is how `planning/07` frames S2, and it is applied to every line alike.
- **S3's buyer keeping 171 positions "for at least 2 years"** while retooling's 162 positions are open-ended.
  Asymmetric, but that is what a buyer's stated plan looks like; the text says plainly it is the buyer's plan.

---

## Part B: the 19 assumptions

Each is a number no public source gives, so it was chosen inside a range with an industry reason. The column
"what it moves" says which way a higher value pushes the scenario's economics, so a lean can be seen; it is not
a reason for the value.

| # | Row | Value (range) | In plain words | What it moves | Verdict |
|---|---|---|---|---|---|
| A32 | `s2_revenue_fall` | 15% (5-23%) | how far sales drop in the downturn | a bigger drop, a bigger shortfall | **keep**: the design's figure, inside the industry's own downturns |
| A33 | `s3_alloc_basis` | by revenue | how head-office costs are shared out to plants | sets Plant 6's share at $32.4M | **keep**: the usual basis |
| A34 | `s3_close_recovery` | 50% (30-70%) | how much of Plant 6's extra cost disappears if its work moves | higher makes closing pay more | **keep**, middle of the range |
| A35 | `s3_accept_share` | 15% (5-30%) | how many offered a job at a distant plant take it | higher makes closing kinder to workers | **keep**; look at it (see below) |
| A36 | `shared_severance_weeks` | 1 week (1-2) | severance per year of service | higher makes eliminating roles cost more | **change for S1** (see below) |
| A37 | `s3_relocation_pp` | $20,000 ($10-50k) | moving help per person | higher makes moving people cost more | **keep** |
| A38 | `s3_site_close_cost` | $10.0M ($5-20M) | closing the site and moving equipment | higher makes closing cost more | **keep** |
| A39 | `s3_retool_capex` | $30.0M ($15-45M) | the cost of retooling | higher makes retooling cost more | **keep** |
| A40 | `s3_retool_payback` | 4 years (3-6) | how fast retooling pays back | shorter makes retooling pay more | **keep** |
| A41 | `s3_retool_share_kept` | 85% (70-95%) | jobs kept after automating | higher keeps more jobs | **keep** |
| A42 | `s3_avoidable_share` | 25% (10-40%) | head-office costs that leave with a sold plant | higher makes selling cost less | **keep** |
| A43 | `s3_sale_multiple` | 25% of revenue (10-40%) | the sale price | higher makes selling pay more | **keep** |
| A44 | `s3_buyer_share` | 90% (70-100%) | jobs the buyer promises to keep | higher makes selling kinder to workers | **keep** |
| A45 | `s3_buyer_years` | 2 years (1-3) | how long the buyer's promise lasts | longer makes selling kinder to workers | **keep** |
| A46 | `s4_years` | 10 (fixed) | the program's length | | **keep**: fixed by the design |
| A47 | `s4_p_success` | 30% (12-60%) | the program's chance of success | higher makes funding look better | **keep** |
| A48 | `s4_payoff_start` | year 8 (5-10) | when income starts if it succeeds | earlier makes funding look better | **keep** |
| A49 | `s4_payoff_years` | 13 (10-15) | how long the income lasts | longer makes funding look better | **keep** |
| A50 | `s4_payoff_mid` | $105M a year ($75-140M) | the income if it succeeds | higher makes funding look better | **keep**; look at it (see below) |

### A36: severance, one change recommended

One severance figure serves S1 and S3. Its reason, "the most common formula" (one week of pay per year of service),
fits S3's plant staff, who are paid by the hour. S1's people are salaried office staff, for whom employer practice
is not the same (that it runs higher is general knowledge, not something a source in this repo shows).
The value sits at the very bottom of its range, and in S1 a low severance makes eliminating roles look cheaper
against retraining in the first year: about $0.7M for all 125 against $1.9M of retraining.

**Recommendation:** a separate S1 row at **1.5 weeks**, the middle of the same range, with the reason that the
"most common" figure describes hourly staff best; S3 keeps 1 week. S1's severance becomes about $8,900 a person
on average, $1.1M for all 125. Retraining still costs more in year one, and still pays back in two years.

### A35 and A50: the two that decide the most

**A35, transfer acceptance (15%, at most 29 of 190 people move):** the only thing stopping "close and move
everyone", which no real closure achieves. It has no public source; case studies run from about one in twenty to
about one in five. 15% is near the middle. **Keep.**

**A50, the program's payoff ($105M a year in the middle, $70-140M as the text states it):** set so that, at the
industry's cost of capital (7.7%) and the stated 30% odds, the program is about 9% better than breaking even in
expected value: the modest margin a proposal brought to a board usually shows. Much higher and funding would be an
easy call; much lower and declining would be. The text gives no cost of capital and no net present value, so a
reader must weigh it. **Keep.** This is the row a critic would attack first; its reasoning is written out in its
range and note.

---

## Part C: what this adds to step 8 (code, Sonnet)

- An optional short description on an offered line, shown under it and shuffled with it (T3). The placeholder has
  none, so its golden prompts stay the same.

## His decisions

**2026-10-07, 3:50 PM: accepted all as recommended**, after skimming this packet; like Phase 2's step 7, an
acceptance on the recommendations rather than an item-by-item weighing, and recorded as such. He noted that the
expert's eye he does not have comes from step 12's outside reader. Applied the same afternoon: T1, T2, T4, T5, T6
(S4 and its garden copy), and A36 split into `s1_severance_weeks` (1.5, salaried office staff) and
`s3_severance_weeks` (1, plant staff); S1's severance is now $8,902 a person, $1.1M for all 125. **T3 waits for
step 8's code** (a short description per line, shuffled with it); S1's three path paragraphs move there then.
