<!-- raw reply from openai/gpt-6-astra via OpenRouter, 2026-10-03; finish_reason=stop; usage={"prompt_tokens": 55020, "completion_tokens": 12984, "total_tokens": 68004, "cost": 1.3369425, "is_byok": false, "prompt_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 55017, "audio_tokens": 0, "video_tokens": 0}, "cost_details": {"upstream_inference_cost": 1.3369425, "upstream_inference_prompt_cost": 0.6877425, "upstream_inference_completions_cost": 0.6492}, "completion_tokens_details": {"reasoning_tokens": 7250, "image_tokens": 0, "audio_tokens": 0}} -->

# 1. Verdict

**Not yet ready to become the build plan, although the project itself is viable.** The infrastructure and experiment-ordering work are substantially ahead of the measurement design. The biggest risk is presenting differences between a model’s allocations as evidence that executives’ stakeholder commitments do—or do not—work. The experiment measures interpretations of objective instructions, not economic outcomes or executives’ incentives. That narrower experiment is worth building. Before implementation locks in the scorer and schema, the plan needs corrections to the financial accounting, statistical decision rule, and real-case distance metric. Pre-registration will prevent changing an answer after seeing it; it will not make an invalid measurement valid.

# 2. Findings, ranked most severe first

## 1. The comparisons answer a useful model question, but not the advertised Roundtable test

**Severity: HIGH**  
**Docs:** `04` §1.1; `07` §3.2, §6.1–6.2; `06` §1, §4–5; `00` §5.1, §5.4.

### What is wrong

The tautology objection is **partly wrong**: maximizing shareholder return does not logically prescribe buybacks, layoffs, or any particular allocation. Investing or retaining employees might maximize it. Therefore, observing which allocations a model selects—and how those change across horizons—is a genuine empirical question.

But `07` does not move beyond **model interpretation of instructions**. There are no measured shareholder returns, stakeholder outcomes, or subsequent company performance. Changing “twenty-year shareholder value” to “value for all stakeholders” can reveal different learned associations without establishing that the underlying interests actually conflict.

Several public claims cross that boundary:

- `06` §1: **“The claim holds”** if C and D make the same decisions. Matching allocations cannot establish that stakeholder interests are inseparable.
- `06` §1: **“The stakeholder commitment does not survive”** if B resembles A. Both might have chosen an allocation beneficial to all stakeholders.
- `06` §5: **“I tested whether executives’ own stated commitment holds up.”** The study tests model responses to an operationalization of that commitment.
- `00` §5.4: the matcher **“reads the company’s revealed objective.”** One decision generally cannot identify an objective; different preferences, information and constraints can produce the same action.

Even the narrower allocation-convergence claim exceeds the primary tests. S1 compares retention share, not the allocation vector. C and D could both retain 40% of affected payroll while allocating the remaining 60% entirely differently. That would be “no split” on the primary outcome, not convergence of decisions.

Finally, A versus C changes both horizon **and financial terminology**: “total shareholder return” versus “long-term shareholder value.” The claim that this isolates horizon is stronger than the prompt design warrants. B and D are adaptations of the Roundtable statement, not its literal wording or a uniquely specified stakeholder objective.

### Concrete failure scenario

C and D both retain 40% of affected workers. C puts the released cash into distributions; D puts it into environmental investment. The primary test earns “no split,” and the landing page says the Roundtable’s convergence claim holds—even though the models’ other allocations sharply disagree and no stakeholder outcomes were evaluated.

### Specific fix

The approved framing needs narrowing, not abandonment:

- Keep the Roundtable as the **motivation and source of stakeholder categories**. Describe the experiment as testing how models translate those mandates into allocations.
- Reserve “no split” for **the named outcome, scenario, model and equivalence margin**.
- Remove claims about proving economic alignment, identifying real companies’ objectives, or discovering a model’s “built-in values.” E is a CEO-role baseline under this dossier and menu, not an unprompted value system.
- Use parallel shareholder-objective wording across A and C, or explicitly acknowledge the terminology confound.
- Report allocation-vector differences descriptively alongside the primary endpoint; do not silently expand the confirmatory test family.

**No change to the grid:** its comparisons are useful once their interpretation is bounded correctly.

---

## 2. “Sources and uses” has not resolved the accounting problem—and some answers are encoded in the menu

**Severity: HIGH**  
**Docs:** `07` §2.4, §3–4, §9; `04` §1.4, §1.6; `01` §2.3.

### What is wrong

A CFO would recognize the label, but not accept the current tables as balanced financial plans. They mix labor capacity, annual expenses, profit, financing flows and balance-sheet stocks.

| Scenario | Problem | Concrete failure |
|---|---|---|
| **S1: AI savings** | Automatable work is treated as an immediately realizable payroll saving. L2 represents retained payroll, whereas other uses represent spending financed by removing it. Transition costs, implementation costs and realizability are unspecified. | A model eliminates roles and puts all released money into R&D. It has expanded capability, yet the primary endpoint records zero “kept with people.” Conversely, retaining payroll counts positively without evidence that useful redeployment exists. |
| **S2: Downturn** | Cutting dividends or drawing cash does **not repair an operating-profit shortfall**. It can finance a cash shortfall. “Accepting lower profit” is neither the same transaction as drawing cash nor an operating improvement. | A model covers the entire $60M operating-profit gap by reducing distributions by $60M. The table balances, but operating profit remains $60M lower. |
| **S3: Closure** | The example is a workforce disposition table, not a sources-and-uses table. The model chooses retooling without demonstrating funding for the capital cost. “Transferred with sale” is also outside the eight-lever schema. | A valid response chooses retooling that the company cannot finance. The validator checks the payroll split but never catches the liquidity failure. |
| **S4: R&D bet** | Funding requires finding $B from sources, but declining the project apparently creates $B available for other uses. That is not necessarily the same feasible budget. | A company would need $20M of cash and $10M of distribution cuts to fund the project. It declines, then allocates $30M to wage increases without identifying those sources. |

`07` §2.4 also lacks the constraints that make an allocation financially feasible: existing spending limits, accessible cash, minimum liquidity, transition costs, and consistency between a discrete choice and its allocations. A balanced table can still cut more R&D than exists.

The neutrality problem is consequently structural, not just adjectival:

- “A downturn frees no capacity to redeploy” excludes a plausible response. Lower demand can leave employees available for maintenance, training or other work.
- S3 explicitly makes the buyer’s workforce intentions uncertain, without requiring comparable uncertainty for retooling or redeployment.
- S1 makes cash-funded expansion require payroll elimination while treating retaining affected payroll as redeployment. That builds part of the cut-versus-expand relationship into the instrument.
- Suppliers are named as essential in B/D but have no explicit decision channel. A common menu is not a complete operationalization of all five stakeholder commitments.

The final scenario text is not supplied, so its neutrality cannot yet be certified. The examples already show what the review checklist misses: **asymmetric feasibility, uncertainty and opportunity sets**. Numbers without adjectives can still lead the witness.

### Specific fix

Before writing the production schema, produce a one-page accounting specification for each scenario:

1. Define the budget basis and period: annual operating effect, cash flow, or labor-capacity value.
2. Keep operating effects separate from financing and cash movements.
3. Make funding available on the same basis across discrete choices.
4. Specify lever caps, unavoidable costs, minimum liquidity and choice/allocation consistency.
5. Distinguish retained payroll from incremental training cost and from cash available for investment.
6. Explain omitted choices—debt repayment, working capital, maintenance investment, supplier terms—as fixed constraints or deliberate exclusions.

Keep the eight-lever taxonomy if desired; it need not pretend that every scenario has an identical financial transaction underneath it.

Add neutrality checks for **which options exist, which have uncertain outcomes, and which consequences receive numbers**. Sourced industry figures help realism, but individually sourced figures do not establish a coherent company or a feasible plan.

---

## 3. The repeat rule does not deliver the power claimed, and the categorical test is undefined

**Severity: HIGH**  
**Docs:** `07` §6–8, §14–15.

### What is wrong

There are four connected defects.

#### A. The power formula targets a different decision rule

The formula estimates power to reject a zero difference when the true difference equals the practical threshold. But “split” additionally requires the **observed estimate** to meet that threshold.

Using the document’s share example:

- Within-cell SD = 0.10.
- Ten repeats × three wordings = 30 observations per objective.
- Standard error of the difference:

\[
SE=\sqrt{\frac{2(0.10)^2}{30}}\approx0.0258.
\]

- The corrected interval excludes zero when the estimate exceeds approximately:

\[
2.96(0.0258)=0.0764.
\]

But a positive “split” requires an estimate of at least **0.10**. If the true difference is exactly 0.10, approximately half the estimates exceed 0.10. Thus the specified rule has roughly **50% power to declare that split**, not 80%.

#### B. “No split cannot be reached on a choice rate” is false

The ±27-point calculation is a **maximum-variance approximation**, not a universal interval width.

At 60 observations per objective and rates near 0.50:

\[
2.96\sqrt{\frac{2(0.5)(0.5)}{60}}\approx0.270.
\]

That calculation is correct.

At rates near 0.05, the same approximation gives:

\[
2.96\sqrt{\frac{2(0.05)(0.95)}{60}}\approx0.118.
\]

An interval centered near zero can then fit inside ±0.20. “No split” is therefore reachable near sufficiently concentrated choice distributions.

More seriously, an ordinary empirical bootstrap gives a difference interval of **[0, 0]** when both objectives always select the same choice in the observed sample. That would readily produce “no split,” potentially with badly overstated certainty.

#### C. S3 has no defined statistical outcome

Close/retool/sell is a three-category variable. The plan does not specify:

- a particular choice probability;
- a multinomial omnibus comparison; or
- another defined distributional statistic.

There is no natural signed “direction” for this outcome, either, so the wording-robustness rule is also incomplete.

If all three choice rates are tested separately, the primary family becomes:

\[
3\text{ other scenarios}\times4
+3\text{ S3 rates}\times4
=24,
\]

not 16. A single properly defined omnibus comparison could preserve 16, but none is specified.

#### D. Two pilot observations do not provide a stable variance estimate

For a binary outcome, a two-observation sample SD is either **0** or approximately **0.707**. Taking the largest across cells mostly chooses between the repeat floor and cap; it does not reliably estimate the underlying choice-rate variance.

Bonferroni itself is defensible. Independence is not required. But its familywise guarantee depends on valid component intervals; sparse-data bootstrap intervals do not acquire coverage merely because the confidence level is raised.

### Concrete failure scenario

The pilot happens to contain identical choices within every cell, so the rule selects six repeats per wording. The final samples again contain identical choices. The bootstrap reports zero-width intervals and “no split”—precisely the verdict the document says is impossible at even its largest sample size.

### Specific fix

- Define S3’s estimand and its equivalence criterion before implementing the scorer.
- Calibrate power against the **actual three-verdict rule**, preferably through simulation. State a design alternative above the practical boundary if retaining the point-estimate threshold.
- Use an interval method appropriate to sparse categorical outcomes; validate coverage, equivalence decisions and false-split rates on synthetic boundary cases.
- Replace the two-run binary variance estimate with a conservative prespecified variance assumption or a more stable estimation rule.
- Keep the cap, but describe underpowered comparisons honestly.
- Specify the bootstrap method and replication count; a 99.7% interval depends on very extreme resampling quantiles.

The **10-point and 20-point margins can be defensible conventions**, but “choice rates are noisier” is not a justification for practical importance. In the illustrative budgets, 10 points means $4M in S1 and $6M in S2. Explain why those differences matter. Separately explain that 20 points means one additional choice in five—not merely an easier threshold to detect.

---

## 4. The real-case matcher can declare a good match despite completely opposite allocations

**Severity: HIGH**  
**Docs:** `07` §3.3, §10.2–10.4; `00` §5.4.

### What is wrong

The distance lacks a fully defined mathematical domain, and its no-match threshold has an unintended consequence.

**Total variation requires probability vectors over the same mutually exclusive categories.** The display groups do not qualify:

- L2 appears in both workforce and future capability.
- L1 is a source and L2 a use.
- Workforce sums together eliminating roles, retaining them and changing wages.

Using S1’s worked example, normalized display groups sum to **2**, not 1:

- Workforce: \(0.60+0.40+0.05=1.05\)
- Future capability: \(0.20+0.40=0.60\)
- Environment: 0.05
- Shareholders: 0.25
- Cash: 0.05

`07` §3.3 says these groups are used by the matcher; §10.4 does not resolve this.

Excluding unobserved components creates another problem. Leaving them unnormalized changes the meaning and scale of the distance; renormalizing answers a different, conditional question. With only one observed component, renormalization can make every nonzero allocation identical.

**The 0.50 no-match threshold fails a simple extreme test.** For cases with both shares and a discrete choice:

\[
d=\frac{TV+\text{choice disagreement}}{2}.
\]

If an objective always makes the real company’s discrete choice, disagreement is zero. Even completely opposite allocations then give:

\[
d=\frac{1+0}{2}=0.50.
\]

Because no-match requires **greater than** 0.50, that objective cannot fail the no-match test. If any objective always selects the observed discrete choice, the case cannot receive “no good match,” regardless of its allocation mismatch.

The **0.05 tie threshold** is also not stable across evidence types. On a discrete-only case it means five percentage points of choice probability; in the equally weighted hybrid it means ten points if the share distance is unchanged.

With 30 runs per objective, two choice rates near 0.50 have an approximate difference SE of:

\[
\sqrt{0.25/30+0.25/30}\approx0.129.
\]

A five-point nearest-neighbor gap is much smaller than that sampling uncertainty.

Finally, matching the **mean allocation** can match behavior that no run exhibited: half the runs allocating everything to X and half everything to Y average to a 50/50 allocation.

### Concrete failure scenario

The company funds a project entirely from cash. Every run under one objective funds it entirely through layoffs. The discrete choice matches perfectly, the financing shares are maximally different, and the matcher still cannot call that objective a bad match.

### Specific fix

- Define a disjoint, direction-consistent matching vector for each scenario, separate from overlapping display groups.
- Specify exactly how partial observability changes the metric, including a minimum-evidence rule.
- Identify the result as nearest **mean allocation** if that remains the target; do not imply that typical runs resemble the company.
- Calibrate the two thresholds against synthetic cases: identical, opposite, same discrete choice/opposite financing, sparse observations and uninformed choice probabilities.
- Report uncertainty in the **distance gaps or ranking**, not only separate spreads.
- Define tie/no-match precedence and treatment of more than two tied objectives.

Neither 0.05 nor 0.50 is presently justified by the metric’s behavior. Freeze replacement rules only after those tests—not after seeing real-case matches.

---

## 5. Real-case disclosure asymmetry affects measurement, not just discovery

**Severity: HIGH**  
**Docs:** `01` §4.3–4.6; `04` §2.1–2.4; `05` Phase 5; `07` §10.

### What is wrong

The repeated claim that asymmetry affects **“discovery only, not measurement”** conflicts with the later admission that many allocation dimensions are unobservable and excluded.

A closure may disclose affected employees and estimated savings. An investment may disclose capital cost but not the number of jobs that otherwise would have disappeared. Neither necessarily discloses where the marginal savings came from or went. These cases can consequently be matched on different—and outcome-dependent—subsets of behavior.

Required financial statements do not, by themselves, solve attribution. Aggregate capex, R&D or distributions do not identify which spending was financed by a particular decision.

The hindsight safeguards are useful but incomplete:

- Pre-event documents prevent direct inclusion of later filings.
- They do not prevent selecting pre-event facts because they explain the known outcome.
- “Options plausibly open” is particularly vulnerable: public filings rarely establish the actual rejected alternatives and their economics.
- Cases are selected after the fictional grid has revealed which objectives tend toward which actions. A rubric committed before that case’s runs is not necessarily blind to the model’s known tendencies.

The outcome-keyword check can even remove genuine pre-event information merely because it was predictive. Predictive facts are not leakage when they were actually available; selective reconstruction is the problem.

Anonymization also needs an economic check. Multiplying dollars while leaving employees unchanged alters implied payroll per employee and revenue per employee. It preserves financial ratios, not every decision-relevant ratio.

### Concrete failure scenario

A closure is matched using its choice and workforce reduction; an investment is matched using only “fund.” The app presents both as comparable readings of objectives. Their different winners are driven partly by what disclosures happen to reveal, not by different company priorities.

### Specific fix

- Show each case’s **observable dimensions and excluded dimensions** beside its result.
- Separate reported facts from analyst-supplied alternatives, forecasts and assumptions.
- Freeze the case-construction and acceptance rules before examining the fictional grid; log accepted and rejected candidates with reasons.
- Add an outcome-blind review of whether the dossier fairly summarizes the permitted source pack. Do not remove legitimate adverse facts simply because they foreshadow the outcome.
- Audit anonymization for operational as well as financial consistency.
- Treat the three to five cases as **illustrations of applying the protocol**, not validation of inferred executive objectives or evidence of frequency.

**No change to the private-appendix decision or minimum case count.** The consequence is that readers can inspect and rerun the anonymized exercise, but cannot independently audit its reconstruction from original sources. The reproducibility claim must say so.

---

## 6. Recording failures does not remove the selection bias they create

**Severity: MEDIUM**  
**Docs:** `02` §2.1; `04` §1.7; `07` §1, §5, §11.

### What is wrong

Publishing failure rates is necessary, but valid-only comparisons still estimate behavior **conditional on successful completion**. Excluding cells above 10% failure does not solve bias below that threshold.

For example, suppose two accepted cells each have exactly 10% failures, with valid-response means of 0.60 and 0.50. With an outcome bounded between zero and one, their hypothetical all-run means are bounded by:

- First cell: \([0.54,0.64]\)
- Second cell: \([0.45,0.55]\)

The difference can range from **−0.01 to 0.19**, despite a valid-only difference of 0.10. The missingness can therefore change the practical conclusion.

Retries add an unspecified intervention. A repair prompt explaining a validation error may change an allocation; a fresh retry selects among stochastic responses. The plan records attempts but never defines the retry prompt or the resulting estimand.

### Concrete failure scenario

One objective disproportionately produces malformed, strongly workforce-protective allocations. The remaining valid runs appear less protective. The failure rate stays at 10%, so the cell remains eligible and produces a misleading split.

### Specific fix

- Freeze retry instructions and whether retries are fresh calls or continuations.
- Distinguish one **run with attempts** from one model call in the schema and accounting.
- Label allocation estimates as conditional on valid completion.
- Publish first-attempt results alongside repaired results.
- For bounded primary outcomes, add a missing-outcome sensitivity bound; withhold an unconditional split claim when plausible missing outcomes overturn it.

No imputation is required. The fix is to show what the observed data do and do not identify.

# 3. Contradictions between docs

| Doc A says | Doc B says | Which should win |
|---|---|---|
| `06` §1 says matching C/D decisions means the Roundtable claim holds. | `04` §1.3 and `06` §4 limit inference to model behavior. | The scope restriction. Rewrite the interpretation table. |
| `01` §4.3 and `04` §2.2 say disclosure asymmetry affects discovery, not measurement. | `07` §10.2 excludes unobservable dimensions from matching. | `07`’s admission. Measurement coverage must be reported and its consequences acknowledged. |
| `00` §5.2 describes a common dollar-allocation menu across all scenarios. | `07` §3.2 makes S3 chiefly a choice and workforce split, including transfers outside that menu. | A corrected scenario-specific schema. Patch the brief rather than claiming the original common-budget design survives unchanged. |
| `05` §5.1 permits cutting official-model wordings to one. | `07` §8 divides required repeats by three; §7.1 depends on a sealed wording. | The frozen protocol. Any reduced-wording design needs recalculated precision and an explicit status—not an unchanged analysis with fewer observations. |
| `00` §8 and `05` Phase 6 promise that a hostile reader can rerun the experiment from the methods page. | `01` §4.8 withholds source identities, links and scaling factors. | Keep the approved privacy boundary; distinguish rerunning supplied inputs from independently reconstructing and auditing real cases. |
| `03` §4 includes Haiku in development spending. | `04` §3.3 explicitly prohibits Horizon Compact development on Haiku for spend attribution. | The later explicit restriction in `04`. |
| `04` §7 says commit `07` as the pre-registration. | `07` explicitly says it is not the pre-registration; `05` Phase 3 freezes completed content and hashes. | `05`/`07`. The planning document alone is not the registered experiment. |
| `04` §2.6 describes CI checking a deny-list read locally and never committed. | `05` Phase 0 requires this check to operate in CI. | The privacy requirement. Specify a secure delivery mechanism or make the name check local/pre-push, with CI checking tracked paths. Use a dummy canary—not a real case identity—to test rejection. |

**Implementation decisions still missing from the canonical record:** the S3 estimand; partial-observability normalization; retry instructions; choice/allocation feasibility checks; and the atomic result/checkpoint format. In particular, “one write-once JSONL object per shard” does not yet explain how completed individual runs survive a shard interruption.

Also, `07`’s **“worst case ~$71”** is a repeat-count scenario, not a spending ceiling: it omits worst-case validation retries. The $33 estimated main-model grid/case cost alone could become about $99 at three attempts per run. Keep the $80 decision, but enforce cumulative spend and bounded retry execution in the harness rather than relying only on a preflight estimate and delayed alarms.

# 4. Facts I could not verify

I have not independently verified the dated model, AWS or filing facts. I am not replacing them with older training-memory claims. These particular assertions need checking because their scope or evidence is unclear:

- **Item 2.05 as a near-complete list of cut-side decisions — `01` §4.2.**  
  **I cannot verify this; check it.** The universal language depends on the form’s triggering conditions, materiality and disclosure requirements. Finding 64 mentions establishes search results, not coverage of all qualifying workforce decisions.

- **Every company’s investment measures being fully available in required structured data — `01` §4.3.**  
  **I cannot verify this; check it.** API availability does not establish uniform disclosure, comparable tagging or complete measurement of training, retention and investment. Missing fields must not silently become zeros.

- **Sonnet 5.5’s universal tool-choice and thinking restrictions on Bedrock — `07` §2.1.**  
  **I cannot verify this; check it.** The account lacks access, and part of the cited support is an API reference cached before the stated Bedrock launch. Provider API documentation and actual Converse behavior need not be interchangeable.

- **Nova Pro’s eligibility under the training-cutoff rule — `03` §7; `07` §14.**  
  **I cannot verify this; check it.** The record cites a knowledge cutoff, whereas case eligibility is defined using training exposure. Those are distinguished elsewhere in the documents and should not be silently equated here.

- **Per-model AWS Budgets filtering — `04` §3.3.**  
  **I cannot verify this; check it.** This is already marked unverified, but later architecture prose treats the filtered alarms as settled. Resolve it before relying on them for project attribution.

# 5. What I deliberately did not recommend

- **No new name, cloud, company type or wholesale project redesign.** None fixes the measurement problems.
- **No mandatory larger study or higher spending cap.** A small experiment with honest inconclusive results is defensible.
- **No removal of Bonferroni merely to obtain more findings.** The correction is understandable; the estimands and interval coverage need repair.
- **No forced publication of the private appendix.** Keep the decision and narrow the auditability claim.
- **No dropping real cases altogether.** They can be engaging applications of the protocol without identifying corporate motives.
- **No claim that wording variants, another vendor, or an awareness probe solve construct validity.** They test useful sensitivities, but several models can share the same economic simplifications and prompt associations.