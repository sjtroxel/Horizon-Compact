# Horizon Compact — Review of the Planning Series (`00`-`07`)

- **Status:** APPROVED 2026-10-03 (his seven decisions in §8, all as recommended). **Nothing in `00`-`07` has been
  changed yet;** `09` orders the patches.
- **Read after:** `07-EVAL-SPEC`. **Read before:** `09-PRIORITIES-AND-OPEN-DECISIONS`.
- **How this review was made, in two passes:**
  1. **An independent read by a different vendor's model.** `openai/gpt-6-astra`, via OpenRouter, 2026-10-03, one
     call, given `00`-`07` and the project's decision log in full (the private real-case appendix withheld). The
     prompt is `08a-REVIEW-BRIEF-gpt-6-astra.md`; the reply, unedited, is `08b-REVIEW-RAW-gpt-6-astra.md`
     (55,020 input and 12,984 output tokens, 7,250 of them reasoning; $1.34; finished normally).
  2. **A verification pass by Claude Opus 5.5** (this document). Every one of Astra's claims was checked against the
     text of `00`-`07` and its arithmetic recomputed. Each is marked **confirmed**, **partly right** or **rejected**,
     with the evidence. Catches Astra missed are added and marked as new.
- **The limit, stated plainly:** pass 2 was written by the same model family that drafted `00`-`07`, so it shares
  their blind spots. Pass 1 is the independent read. Where the two disagree, both positions are given.

---

## 1. Verdict

**The project is sound and worth building, and the infrastructure plan is ready. The measurement design is not
ready to freeze.** Astra's one-line verdict holds up under checking: the plan for *running* the experiment is ahead
of the plan for *reading* it.

None of the findings below calls for a different project, model, cloud or company. Every one is a correction to
`07` (and a few sentences in `00`, `01` and `06`), and all of them land **before Phase 3's freeze**, which is
exactly where `05` §2 says corrections are cheap. Nothing has been run, so nothing has been seen. That is the good
news, and it is real: if this review had happened after the pilot, several of these fixes would have counted as
peeking.

**The single biggest risk:** the headline comparison (C vs D, the Business Roundtable test) is currently confounded
by its own wording, measured on an outcome too narrow to support "the same decisions," and judged by a repeat rule
that delivers about half the power it claims. Each of the three is fixable in a day of design work; together they
would let a careful critic dismiss the project's main result.

---

## 2. Scorecard of Astra's findings

| # | Astra's finding | Its severity | Verdict here | Where in this doc |
|---|---|---|---|---|
| 1 | The comparisons answer a model question, not the advertised Roundtable test | HIGH | **Confirmed**, and extended: the wording confound is worse than Astra found | §3.1, §3.2 |
| 2 | Sources-and-uses does not resolve the accounting; answers are encoded in the menu | HIGH | **Mostly confirmed**; one point rejected (S2 redeployment) | §3.3 |
| 3 | The repeat rule does not deliver the claimed power; the categorical test is undefined | HIGH | **Confirmed**, every sub-claim, arithmetic rechecked | §3.4 |
| 4 | The real-case matcher can call a good match despite opposite allocations | HIGH | **Confirmed** | §3.5 |
| 5 | Disclosure asymmetry affects measurement, not just discovery | HIGH | **Partly right:** the wording point is MEDIUM; one sub-point (cases chosen after the grid is seen) is HIGH and is promoted | §3.6, §4.6 |
| 6 | Recording failures does not remove the selection bias they create | MEDIUM | **Confirmed** | §4.1 |
| — | Eight contradictions between docs | — | **All eight confirmed** | §5 |
| — | Five facts it could not verify | — | Two need wording fixes, three need no change | §6 |

Astra's work was careful. It overstated in only two places (§3.3's S2 point and a cost bound in §4.3), and its
arithmetic was right everywhere it showed it.

---

## 3. HIGH findings

### 3.1 The objective wordings confound the comparisons they are meant to isolate *(Astra #1, extended; new catch in bold)*

**Docs:** `00` §5.1; `01` §1.3; `07` §6.1, §7.1.

The four objectives, as written in `00` §5.1:

| | Verb | What is valued | Horizon |
|---|---|---|---|
| A | **Maximize** | total shareholder return | next four quarters |
| B | **Create value for** | all stakeholders (five, listed) | next four quarters |
| C | **Maximize** | long-term shareholder value | twenty years |
| D | **Create value for** | all stakeholders (five, listed) | twenty years |

- **A vs C** changes the horizon **and** the measure (TSR versus long-term value). `07` §6.1 says it isolates
  horizon. It does not. *(Astra caught this.)*
- **C vs D, the headline Roundtable test, changes who counts _and_ the verb: "maximize" versus "create value
  for."** `01` §1.3 says C's wording "isolates the one variable that differs: who counts." It does not. "Maximize"
  instructs optimization; "create value for" instructs something looser. A model that behaves differently under C
  and D may be responding to the verb, and a critic who notices will say so. The same confound sits in A vs B.
  *(New; Astra flagged only the A vs C half.)*
- **B vs D is the only clean pair** (only the horizon differs).
- **The three wordings are written per objective, not per template.** `07` §7.1 says a split is robust only if its
  direction holds under every wording, but wording 2 of C and wording 2 of D are not written to correspond. If they
  differ in structure, a wording-level reversal could come from the pair being mismatched, not from the objective.
  *(New.)*

**Fix (proposed):**
1. **Write all four objectives from one sentence frame**, varying only the two factors. One way, using the
   Roundtable's own phrase for shareholders ("generating long-term value for shareholders"):
   *"Create value for [shareholders | all of the company's stakeholders: customers, employees, suppliers, the
   communities in which it operates (including their environment), and shareholders], over [the next four
   quarters | twenty years]."* Then every primary pair differs in exactly one factor.
2. **Write the three wordings as three templates**, each applied to all four objectives (and a matching E). Wording
   *k* of every objective then shares its structure, and §7.1's direction rule compares like with like.
3. **What the fix costs:** "maximize total shareholder return" is the real-world idiom, and dropping it from A
   loses some realism. Two ways to keep it: use "maximize" in all four (*"Maximize value for all stakeholders"* is
   awkward but parallel), or keep TSR as a stated limit. **His call (§8, item 1).**

**Owner:** `07` §6.1 and §7.1; `00` §5.1 and `01` §1.2-1.3 patched to match.

### 3.2 Several public claims exceed what the design can show *(Astra #1, confirmed)*

**Docs:** `06` §1, §5; `00` §5.1, §5.4; `07` §3.2, §6.1.

`06` §4's scope sentence is right: the project measures how a model decides under different objectives. Four
sentences elsewhere break it:

| Where | What it says | Why the design cannot support it |
|---|---|---|
| `06` §1, table row 1 | If C and D make the same decisions, "the claim holds: … serving shareholders and serving everyone converge" | Identical model allocations under two instructions say nothing about whether the underlying interests converge in the world |
| `06` §5 | "I tested whether executives' own stated commitment holds up" | It tests how a model acts on that commitment's words |
| `00` §5.4 | The real-case view "reads the company's revealed objective from its behavior" | One decision cannot identify an objective; different objectives, information and constraints produce the same action |
| `00` §5.1 | E is "a finding about the model's built-in values" | E is the model's default *in a CEO role, with this dossier and menu*, not a value system |

**A narrower point, also confirmed:** "C and D make the same decisions" would be read off the **primary outcome
only** (`07` §6.1). In S1 that is the share kept with people. C and D could both keep 40% with people and send the
other 60% to entirely different places. That is "no split" on the primary outcome, not "the same decisions."

**The Roundtable frame survives; its table does not.** The honest version of the frame is still strong, and it is
the question the design actually answers: *does handing a decider the Roundtable's own words, in place of a
shareholder mandate, change what it decides?* That is testable, fair to executives, and keeps his thesis inside it.

**Fix:** rewrite `06` §1's table and §5's sample sentence in that form ("under the Roundtable's wording, the
model…"); in `00`, replace "reads the company's revealed objective" with "shows which objective's runs the
company's decision most resembled," and "built-in values" with "default in this role." State in `07` §6 that "no
split" means *no split on the named outcome, for this scenario and model*, and pre-register the full allocation
comparison as a **descriptive** secondary (§4.5), so a reader can see whether the rest of the money moved too.
**Owner:** `06`, `00`, `07`. These are wording fixes inside his approved decision (`06` §10.1); the frame stays.

### 3.3 Sources and uses is the right shape, but three of the four scenarios do not balance as finance yet *(Astra #2, mostly confirmed)*

**Docs:** `07` §2.4, §3.1-3.3, §9; `00` §5.2; `01` §1.2.

A CFO would recognize the sources-and-uses table. Read line by line, though, it mixes operating effects, cash
movements and headcount. Scenario by scenario:

- **S1 (AI savings). Partly confirmed.** The arithmetic balances. The gap is what a redeployed person *does*: if
  the dossier offers no productive work for retained people, keeping them (L2) is paying for idle capacity, and every
  objective will cut. If it offers unusually attractive work, every objective will keep them. Either way the result
  is set by the dossier, not the objective. **Fix:** the dossier states a redeployment opportunity in numbers (what
  work exists, what retraining costs, how long until it pays), the same way it states the savings.
- **S2 (downturn). Confirmed.** L7 (reduce shareholder returns) and L8 (absorb it as lower profit, or draw on cash)
  are not the same kind of thing as L1, L3, L4, L5 and L6. Cutting a dividend does not restore an operating-profit
  shortfall; it moves cash. And L8 bundles two different acts. Read honestly, S2 is a table of **who bears the
  shortfall**, not of sources and uses. **Fix:** say so, and let it be that: workforce (L1, L4), future capability
  (L3), environment (L6), customers (L5), shareholders (one line: lower profit, with payout policy stated as fixed or
  asked separately). That is clearer for a business reader, and the primary outcome (the workforce share) is
  unchanged.
  - **Rejected:** Astra's point that excluding L2 in a downturn removes "keep people idle and train them." Keeping
    people is already expressible in S2: it is the shortfall being borne by anything other than L1. No change.
- **S3 (closure). Confirmed.** It is a discrete choice plus a workforce split, not a sources-and-uses table. Retool
  has a capital cost with no stated funding, so a model can choose an option the company cannot pay for, and
  "transferred with the sale" is outside the eight levers. **Fix:** state in `07` that S3 departs from the dollar
  menu; give every option the same funding status (for example, the dossier states retooling is fundable from
  existing liquidity, so feasibility is equal); and update `00` §5.2, which still says every scenario uses the same
  dollar menu (§5, row 3).
- **S4 (R&D bet). Confirmed, as an internal inconsistency.** If funded, the CEO must find $B from sources (cash,
  cuts, lower returns). If not funded, the CEO allocates $B to uses. Those cannot both be true: either the company
  has $B of free cash (then funding needs no sources), or it does not (then declining frees nothing to allocate).
  **Fix:** pick one in Phase 2. The cleaner one: *the company has $B a year of uncommitted cash; fund the program
  with it, or allocate it elsewhere*, with "fund it partly by cutting elsewhere" as an explicit option if the
  cut-to-fund tradeoff is wanted.
- **No lever caps. Confirmed.** `07` §2.4 checks that the table balances, not that it is possible. A model could cut
  more R&D than the company spends. **Fix:** the dossier states a maximum for every source; validation enforces it.
- **No supplier lever. Confirmed, and it matters more here than Astra said.** B and D name suppliers because the
  Roundtable does, and `01` §1.2 justifies keeping them because "a manufacturer's supply chain is where a downturn
  or a closure lands second." The menu then gives the model no way to act on suppliers. **Fix, his call (§8 item
  2):** add a supplier source in S2 (pressing suppliers on price or payment terms, a lever real CFOs use), or state
  the omission as a known limit.
- **S3's sketch fails `07`'s own neutrality checklist.** "The buyer's intentions for the workforce uncertain" is a
  consequence for workers stated for one option only. Checklist item 1 says consequences are stated for every group
  or for none. **Fix:** state the workforce outcome of every option in numbers, or of none. *(Astra caught this.)*

**Owner:** `07` §2.4 and §3 (Phase 2 tests the result before the freeze, as `07` §3.3 already requires); `00` §5.2.

### 3.4 The statistics need repair before they are frozen *(Astra #3, every sub-claim confirmed)*

**Doc:** `07` §6.2, §6.3, §8.

**(a) The repeat rule cannot deliver 80% power at the threshold, at any sample size.** `07` §8 sizes the repeats
for 80% power to rule out zero when the true difference *equals* the threshold. But `07` §6.2's "split" also
requires the **observed** difference to reach the threshold. When the true difference sits exactly at the threshold,
the observed one lands above it about half the time, however many runs there are.

> Worked check, shares: sd 0.10 gives n = 10 per wording, 30 per objective. The standard error of a difference is
> √(2 × 0.10² / 30) ≈ 0.026. The interval clears zero once the estimate passes 2.96 × 0.026 ≈ 0.076, but "split"
> needs 0.10. With a true difference of 0.10, P(estimate ≥ 0.10) ≈ 50%.

**Fix:** keep the verdict rule (it is a good rule) and restate the power target as a **design difference above the
threshold**, for example 1.5 times it (15 points for shares, 30 for choice rates), solving for n under the actual
split rule. Checked: for shares at sd 0.15, a true 15-point difference reaches 80% power at about 10 per wording.
For choice rates at the cap (60 per objective), a true 30-point difference reaches only about 63%, so the cap binds
and the methods page says so. Then verify by simulation on synthetic data (already planned, `07` §14 item 5).

**(b) "'No split' cannot be reached on a choice rate" is too strong.** `07` §8's ±27 points is the worst case, at
choice rates near 50%. Near 0% or 100% the interval is much narrower (about ±12 points at 5%), and "no split" is
reachable. *(Astra's arithmetic, rechecked.)* **Fix:** correct the sentence in `07` §8 and in `07` §15 item 3,
which repeats it as part of his decision.

**(c) The bootstrap can report false certainty, and probably will.** If every run under two objectives makes the
same discrete choice, a plain bootstrap returns an interval of exactly zero width and declares "no split" with
complete confidence. Models with thinking off at default settings often do repeat the same discrete choice, so
this is a likely case, not an edge case. **Fix:** for choice rates, use a score-based interval for a difference of
proportions (Newcombe's method), which behaves sensibly at 0% and 100% and can still be explained in one sentence.
Keep the bootstrap for shares, with the number of resamples stated (a 99.7% interval reads extreme tails, so at
least 10,000).

**(d) S3 has no defined outcome.** Close / retool / sell is three categories; `07` §3.2 says only "primary outcome:
the choice." There is no single rate to compare, no direction for `07` §7.1's wording rule, and testing all three
rates would make the family 24 comparisons, not 16. **Fix:** define S3's primary outcome as the **close rate**
(the cut option, which is the thesis), with the full three-way split reported descriptively. The family stays at 16.

**(e) Two pilot runs per cell cannot estimate spread.** For a yes/no outcome, the spread of two runs is either 0 or
about 0.71. Taking the largest across cells mostly picks between the floor and the cap. **Fix:** for choice rates,
skip estimation and pre-commit to the conservative assumption (rate 0.5), which sends them to the cap; for shares,
pool the spread across all of a scenario's cells (ten cells of two runs, about 10 degrees of freedom) instead of taking the largest of
many two-run estimates.

**(f) Lower priority:** the thresholds are justified as "choice rates are noisier," which explains why they are
easier to detect, not why they matter. One sentence each in dollars fixes it (10 points of S1's illustrative budget
is $4M). And because wordings are treated as fixed (`07` §6.3), every claim is "over these three wordings," which
the methods page should say in those words.

**Owner:** `07` §6-8, §14-15. Items (a), (b) and (d) change approved decisions 3 and 7 in `07` §15 (§8 here).

### 3.5 The real-case matcher has a hole, and its two numbers are not yet justified *(Astra #4, confirmed)*

**Doc:** `07` §3.3, §10.4.

- **"No good match" can never fire on a case with a discrete choice.** The distance is (share difference + choice
  disagreement) / 2. If an objective's runs always make the company's actual choice, the most that distance can be
  is (1 + 0) / 2 = 0.50, and "no match" requires *more than* 0.50. So an objective whose allocations are the exact
  opposite of the company's still cannot be called a bad match. *(Checked.)*
- **The summary groups cannot be used for a distance.** `07` §3.3 says the groups serve "the real-case matcher,"
  but L2 is in two groups, so the groups sum to more than 1 and total variation distance is undefined on them.
  `07` §10.4 says "observable shares," which may mean levers; the two sections disagree.
- **A 0.05 tie margin is smaller than the noise.** With 30 runs per objective and choice rates near 50%, the
  standard error of the difference between two objectives' rates is about 13 points. Two objectives 5 points apart
  are indistinguishable.
- **Distance of the average is not the average distance.** Half the runs putting everything into X and half into Y
  average to a 50/50 split that no run made.

**Fix:** compute distance **per run** on a disjoint lever-level vector restricted to the case's observable
dimensions, then average over runs; state the rule for dimensions that are not observed; and set the tie and
no-match thresholds **after** testing them on synthetic cases (identical, opposite, same choice with opposite
money, sparse), never after seeing a real case. Call a tie when the gap between the two nearest objectives is
inside its own bootstrap spread, not at a fixed 0.05. **Owner:** `07` §10.4. Changes approved decision 8 in `07` §15.

### 3.6 Real cases are chosen after the main results are seen *(new emphasis; Astra raised it inside #5)*

**Docs:** `05` §5 (Phase 4 then Phase 5), `04` §2.3-2.4, `07` §10.2.

`05` deliberately runs the real cases after the official grid, for good reasons (a proven harness, a larger pool).
But that means the person choosing which cases to accept already knows which objective tends toward which action.
`07` §10.2 commits each rubric before its case runs, which protects the *mapping*; nothing protects the *selection*.
Choosing a retool case that will plainly match D, or skipping an invest case that matches A, would be invisible in
the commit history. In a design whose credibility rests on closing every such path (`04` §1.2), this is the one
left open.

**Fix:** pre-register a **mechanical selection rule** in Phase 3: for example, the first *k* candidates by date of
first disclosure inside the window, from the named search channels, that pass `01` §4.1's criteria, in each case
type. Log every candidate considered and why it was accepted or rejected. That keeps the late timing and its
benefits, and removes the choice. **Owner:** `07` §10 (new subsection); `05` Phase 3's deliverables.

---

## 4. MEDIUM findings

### 4.1 Retries are an undefined intervention, and valid-only results are conditional *(Astra #6, confirmed)*

`07` §5.1 allows up to two retries but never says what a retry *is*: the same request again, or a message
telling the model what failed. The second is a different instrument and can change the allocation. And a cell with
10% failures passes `07` §5.2's rule while its valid-run average can move by several points depending on what the
failures would have said (Astra's bound: a 10-point difference between two such cells could truly be anywhere from
-1 to 19 points).

**Fix:** a retry is a **fresh, identical request** (same prompt and menu order, no repair message), stated in the
pre-registration; publish first-attempt results beside final ones; label results as "among valid runs"; for the
primary outcomes, add a simple worst-case bound for the failed runs, and do not call a split if that bound would
overturn it. **Owner:** `07` §5.

### 4.2 Results written once per shard cannot survive an interrupted sweep *(Astra noted it; promoted here)*

`02` §2.8 stores "JSONL in S3, one object per shard, write-once." `04` §3.1 then made each model's whole sweep one
task, so a shard is now 1,200 or more runs over two to four hours. If the object is written once at the end, an
interrupted task loses everything, and `05` §4.2's resume-by-`run_id` has nothing to resume from. **Fix:** write
one object per run (or per small batch), write-once, under the sweep's prefix. **Owner:** `02` §2.8, `05` §4.2.

### 4.3 Nothing stops spending mid-sweep *(Astra, confirmed; its cost figure overstated)*

The budget guard (`02` §2.1) is a preflight estimate, and AWS Budgets alarms arrive hours late. `07` §13's ~$71
does not include retries. Astra's figure of about $99 assumes every run uses all three attempts, which is a ceiling,
not a forecast. The point stands without it: **the harness should track cumulative spend from token counts as it
goes and stop at the sweep's cap**, not only check it before starting. **Owner:** `02` §2.1, `03` §6.

### 4.4 The development model is unnamed, and two docs disagree on it *(new; extends Astra's Haiku row)*

`03` §4 budgets development on "mostly local models, some Haiku/Sonnet." `04` §3.3 bans Haiku 4.5 (its spend lands on
Musical Mycelium's billing line). `05` §2 forbids running the official model on a real scenario before the
pre-registration, which rules out Sonnet 4.6 for scenario development, and Nova Pro is also an official model. Local
models are unconfirmed (`04` §6.3: Ollama not found on the WSL path, 7 GB of RAM visible). **So no model is
currently allowed for Phase 2's development runs.** **Fix:** name the development model in `05` Phase 0, and check
that its billing line is not one Musical Mycelium already uses (*unverified* whether Musical Mycelium spends on any
Nova model; check before choosing one). **Owner:** `05` Phase 0, `03` §4 (patch).

### 4.5 The secondary analyses the risk register relies on are not pre-registered *(new)*

`04` §1.1 answers the tautology objection partly with "which lever absorbs the money" and the E baseline. `07`
pre-registers only the 16 primary comparisons and E's distance. Everything else, including the allocation
comparison that §3.2 above needs, would be chosen after the results are seen. **Fix:** list the secondary analyses in
the pre-registration as **descriptive** (full allocation by objective, every lever's mean and spread, the E distances
with a defined metric), with no verdicts, so they are fixed in advance without growing the tested family. **Owner:**
`07` §6.

### 4.6 What real cases can show differs by case, and the docs say it does not *(Astra #5, partly right)*

`01` §4.3 and `04` §2.2 say the cut/invest disclosure asymmetry affects "discovery only, not measurement." `07`
§10.2 then excludes unobservable dimensions from matching, and those differ by case type: a closure shows its choice
and its job count; an investment may show only "fund." So cases are matched on different evidence. **Fix:** correct
the "discovery only" sentence, and show each case's observed and excluded dimensions beside its result. Astra's
proposal to treat the cases as **illustrations of the protocol**, not as validation, is right and costs nothing.
**Owner:** `01` §4.3, `04` §2.2, `07` §10, `06` §6.1.

### 4.7 Scaling dollars without scaling headcount distorts the dossier *(Astra, confirmed)*

`01` §4.6 scales every dollar figure by a hidden factor and leaves headcounts as they are, so pay per employee and
revenue per employee change. A plant's machinists could appear to earn an implausible wage, which both distorts the
decision and can make the case stand out. **Fix:** scale headcounts by the same factor (rounded), or state which
ratios are preserved and check that pay per head stays in a realistic band. **Owner:** `01` §4.6.

### 4.8 The privacy check in CI cannot read a file that is never committed *(Astra, confirmed)*

`04` §2.6 has CI fail on any company name from the longlist, "read locally, never committed." CI runs on GitHub, not
the laptop, so it cannot read that file. **Fix:** a local pre-commit or pre-push hook reads the longlist (it is on
the laptop); CI checks only that nothing under `methods-appendix/` is tracked. If a CI name check is wanted too, keep
the names in a repository secret. Test it with a made-up canary name, never a real one. **Owner:** `04` §2.6, `05`
Phase 0.

### 4.9 A model's memo on a real case could name a company *(new)*

`07` §12 publishes raw responses for real cases by case type. The recognition probe (`07` §10.3) catches a model that
names the company *when asked*; nothing catches a memo that guesses a company in passing ("as a firm like X might…").
Publishing that would either re-identify the case or attach a real company's name to a decision it did not make.
**Fix:** run the deny-list check (§4.8) over every real-case memo before publishing, plus a check for any company
name at all; hold back any memo that names one. Real-case memos also need their own label (the memo label in `06`
§6.1 says "for a fictional company"). **Owner:** `07` §12, `06` §6.1.

---

## 5. Contradictions between docs (all of Astra's, each confirmed, plus three new)

| Doc A says | Doc B says | Resolution |
|---|---|---|
| `06` §1: C and D matching means "the claim holds" | `04` §1.3, `06` §4: claims are about the model only | `06` §4 wins; rewrite `06` §1 (§3.2) |
| `01` §4.3, `04` §2.2: asymmetry affects discovery, not measurement | `07` §10.2: unobservable dimensions excluded per case | `07`; correct the sentence (§4.6) |
| `00` §5.2: every scenario uses the same dollar menu | `07` §3.2: S3 is a choice plus a workforce split, with a category outside the menu | Patch `00` §5.2 to match `07` (§3.3) |
| `05` §5.1 (and `04` §6.1): cut wordings on the official model to "the primary wording" | `07` §8 divides repeats by three wordings; §7.1's robustness needs all three; "primary wording" is defined nowhere | Define it as the sealed wording; any cut recomputes repeats and drops the robustness claim, stated |
| `00` §8, `05` Phase 6: a hostile reader can re-run the experiment from the methods page | `01` §4.8: real-case sources withheld | Keep the privacy decision; say "re-run from the published inputs, including the anonymized dossiers," not "audit how the cases were built" |
| `03` §4: some development on Haiku | `04` §3.3: no Haiku for Horizon Compact development | `04` wins (§4.4) |
| `04` §1.2 and §7 item 4: "`07` committed as the pre-registration" | `07` header: `07` is the design, not the pre-registration; `05` Phase 3 creates it | `05`/`07` win; reword `04` |
| `04` §2.6: CI reads a deny-list that is never committed | `05` Phase 0: a deny-listed name must fail CI | §4.8's fix |
| **New:** `01` §1.3: C's wording isolates who counts | `00` §5.1: C says "maximize," D says "create value for" | §3.1's fix |
| **New:** `07` §7.3: the thinking sub-study costs "about $3" | `07` §13 and `03` §3.3: about $5 | §13 is the computed figure (100 × $0.049); fix §7.3 |
| **New:** `02` §2.8: one write-once object per shard | `04` §3.1: one task per model, so one shard is the whole sweep | §4.2's fix |

---

## 6. Facts Astra could not verify

| Claim | Astra's concern | Verdict |
|---|---|---|
| `01` §4.2: Item 2.05 is "a near-complete … list of cut-side decisions" | Item 2.05 is triggered only by material exit costs; many layoffs never file one | **Right. Reword** to "the main machine-searchable source"; WARN notices (`01` §4.7) already cover part of the gap. Discovery only, so LOW |
| `01` §4.3: investment is "fully measurable after the fact" in XBRL | Aggregate capex and R&D do not identify a decision; training spend is not required data | **Right. Reword** to "measurable in aggregate." Matters for the frequency study, not v1. LOW |
| `07` §2.1: Sonnet 5.5 rejects forced tool use and non-default sampling | Sourced from Anthropic's API reference, not from Bedrock's Converse API, and unverifiable without access | **Right that it is unverified on Bedrock.** No change needed: the `auto` method is sound on every model whether or not the restriction holds there. Mark the row "per Anthropic's API; unverified on Bedrock" |
| Nova Pro's cutoff under the case-window rule | The record cites a knowledge cutoff, while the rule needs training exposure | **No change.** `07` §14 item 2 already checks Nova Pro's cutoff before Phase 3, and the case window runs from mid-2026, far past any published Nova Pro date |
| `04` §3.3: Budgets can filter on per-model billing lines | Marked unverified in `04`, stated as settled in `02` §2.12 | **Right.** Add "if the filter works (`04` §3.3)" to `02` §2.12. LOW |

---

## 7. What this review deliberately does not recommend

- **No change of project, name, cloud, company type or model.** Nothing found needs one. (Astra agrees.)
- **No larger study and no higher ceiling.** An honest "inconclusive" from a small study is a publishable result;
  the fixes above make the small study honest, not bigger.
- **No dropping of Bonferroni** to find more splits. It is the explainable choice (`07` §6.3), and it stays.
- **No publishing of the private appendix.** Narrow the reproducibility claim instead (§5).
- **No dropping of the real cases.** Treated as illustrations of the protocol, chosen by a rule, they remain the most
  engaging view in the app.
- **No removal of "maximize total shareholder return" without his decision.** It is the real-world idiom, and the
  cost of parallel wording is realism (§3.1).
- **No claim that wording variants, a second model family or the awareness probe settle construct validity.** They
  test sensitivity. Astra says the same, and it is right.

---

## 8. Decisions for him

**All seven decided 2026-10-03, his, as recommended** (including "create value for" as the shared verb in item 1,
and adding the supplier source in item 2). These change or amend decisions already approved in `00`-`07`. Everything
else in this review is a correction inside a decision he already made, and goes straight into `09`'s patch list.

1. **Objective wording (§3.1):** one sentence frame for all four objectives so each primary pair differs in one
   factor, with the three wordings written as shared templates. **Recommended.** Sub-choice: the shared verb
   ("create value for" throughout, recommended, using the Roundtable's own phrase; or "maximize" throughout).
2. **Suppliers (§3.3):** add a supplier source to S2, or state the omission as a known limit. **Recommended: add it**,
   since `01` §1.2 kept suppliers in B and D for exactly this reason.
3. **The repeat rule (§3.4a, e):** power stated at 1.5 times the threshold, choice rates pre-committed to the cap,
   shares sized from a pooled spread. **Recommended.** Amends `07` §15 decision 7.
4. **Choice-rate statistics (§3.4b-d):** S3's primary outcome is the close rate; Newcombe intervals for choice
   rates; the "no split unreachable" sentence corrected. **Recommended.** Amends `07` §15 decisions 3 and 4 (the
   thresholds themselves, 10 and 20 points, stay).
5. **The matcher (§3.5):** per-run distance on lever-level vectors; tie and no-match thresholds set from synthetic
   tests before any real case. **Recommended.** Replaces `07` §15 decision 8's two numbers.
6. **Real-case selection (§3.6):** a mechanical, pre-registered selection rule. **Recommended.** New.
7. **The Roundtable frame (§3.2):** kept as the lead (`06` §10.1 stands), with its table and sample sentence
   rewritten to describe the model's behavior under the Roundtable's words. **Recommended.**

---

## 9. Bottom line

- **Build it.** Nothing here argues against the project, and the infrastructure plan needs only small patches
  (§4.2-4.4, §4.8).
- **Do not freeze `07` as it stands.** The headline comparison has a wording confound (§3.1), a narrow outcome
  (§3.2) and half its claimed power (§3.4); the matcher has a hole (§3.5); and case selection is open (§3.6). All
  are fixed on paper, before any run, at no cost but design time.
- **The second-vendor read earned its $1.34.** Of Astra's six findings, five held up in full or in substance; its
  math was right throughout; and two of this review's own catches (§3.1's verb confound, §4.4's missing development
  model) came from following its findings back into the text.
- **Next:** his decisions on §8, then `09` turns this review into an ordered patch list and the open decisions that
  remain before the repo.
