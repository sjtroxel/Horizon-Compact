# Horizon Compact — Eval Spec (the design of the pre-registration)

- **Status:** APPROVED 2026-10-03 (his eight decisions in §15). Facts marked *verified* were checked that day against
  Anthropic's documentation, AWS documentation, or his account. **Amended by `08` (2026-10-03),** his seven decisions
  on it: §2.1, §2.4, §3, §5, §6 (new §6.5), §7.1, §7.3, §8, §9, §10 (new §10.0), §12-16 (patches P3, P4, P7-P18,
  P20, P22, P23, P26, P30, P32 in `09` §3).
  **Patched 2026-10-04 (his):** §2.3, Nova Pro runs at its own default temperature
  (`docs/phases/phase-0.5-aws-foundation.md`, decision 7).
  **Patched 2026-10-06 (his):** §3.1, L9's wording ("negotiating lower prices or longer payment terms with
  suppliers"), a neutrality fix from Phase 2 step 7; the dossier uses the same words.
  **Patched 2026-10-05 (his):** §7.3, Sonnet 5.5 is no longer awaited and Sonnet 4.6 is the v1 main model,
  fixed (`docs/KNOWN-GAPS.md`, the closed Sonnet 5.5 entry). §2.1's Sonnet 5.5 row stays: it is why the
  capture method is one tool with `auto` choice, and that method stays.
  **Patched 2026-10-04 (his), from `docs/phases/phase-2.5-scenarios-and-wordings.md`:** §3.2 S1's retraining cost
  stated separately (decision 5); §4 and §7.2 the discrete options' order shuffled per run (decision 3); §7.1 the
  sealed template drawn at random (decision 4).
  **Patched 2026-10-07 (his), from `docs/phases/phase-2.5-scenarios-and-wordings-IMPLEMENTATION.md`:** §3.2 a role
  eliminated or kept counts at employment cost (payroll and benefits), a wage or hours cut at payroll (decision 1);
  S4's optional cuts are offered under both choices (decision 3).
  **Patched 2026-10-07 (his, on Opus's recommendation), from Phase 2.5 step 5:** §3.2 S1's share is about 25%, from
  a public source, not 30%; S2's $G counts only the costs that fall with volume on their own (purchased materials,
  parts and energy), so no pay is cut before the decision. §3.2 S1 is a split of the affected people into three
  priced paths, not of $Y (decision 8).
  **Patched 2026-10-07 (his, on the Phase 2.5 blind reader's point R5):** §3.2 S4's optional cuts draw on every group
  that has a use, at the dossier's limits, and an item with both a cut and a use may be above zero on one side only.
  **Patched 2026-10-04 (his), from `docs/phases/phase-3.5-preregistration.md`:** §10.0 the case types and *k* set
  (decision 4); the change policy after the tag gains errata (decision 6, in "What this doc is" below).
  **Patched 2026-10-04 (his), from `docs/phases/phase-4-official-grid.md`:** §11 a sweep is one study on one model,
  and runs go in one shuffled order (decisions 3 and 4).
  **Patched 2026-10-04 (his), from `docs/phases/phase-5-case-building.md`:** §10.0 the search date by rule and
  judgment rejections independently read; §10.1 the case-type templates and scenario shapes, the option-economics
  and scaling rules, all frozen in the protocol; §10.2 the rubric independently read; §10.3 the replacement rule;
  §10.4 matches under alternative readings (decisions 2, 4 and 6).
  **Patched 2026-10-04 (his), from Phase 0.5's pre-build checks (`KNOWN-GAPS.md`, "OPEN — Phase 0.5 checks"):** §2.1
  Sonnet 4.6's temperature cell and Nova Pro's thinking cell; §5.1 the refusal row names Converse's form; §14 items
  2-4 closed.
  **Patched 2026-10-04 (his), from Phase 0.5's smoke calls (`docs/phases/phase-0.5-aws-foundation-IMPLEMENTATION.md` §19):** §5.1 a model error that Bedrock delivers as
  an API error is a model outcome (`malformed_tool_use`), and text beside one tool call is not `no_tool_call`; §7.3
  thinking tokens are not reported separately by Converse; §14 item 1 closed.
  **Patched 2026-10-09 (his authorization of 2026-10-08, on Opus's recommendation), from Phase 3 step 12
  (`docs/phases/phase-3-scoring-and-simulation-IMPLEMENTATION.md` §20b):** §5.2 the worst-case bound both ways (kept
  as built, his decision 1 of 2026-10-09), a wording dropped from both sides, and the measured cost of failures; §6.2 edges and the estimate-inside guard; §6.3
  Welch for shares, alpha exactly 0.003125, decision 10's two rules, 95% for descriptive intervals and the matcher;
  §8 the t quantile, the corrected precision at the cap, rule (a) never setting n, 0.84 as written, the pilot's two
  wordings; §10.4 dimensions, distance, the matched-set reading rule, `D*` and `k*` per shape, the opposite check
  (his decision 2, 2026-10-09); §14 item 5 the false-no-split target (decision 4).
- **Read after:** `06-NARRATIVE-AND-VOCABULARY`. **Read before:** `08-REVIEW`.
- **What this doc is:** the measurement design. **What it is not:** the pre-registration itself. In Phase 3 (`05`
  §5) this design is filled in with the final wordings, dossier and numbers, committed and tagged `prereg-v1`, and from
  then on it is frozen. Until then, anything here can change. After that, only with a new protocol version and an
  exploratory label (`04` §1.2). *Patched 2026-10-04 (his):* one exception, **errata**: a correction that changes no
  computation and no content (a typo, a broken link, a clearer sentence) is allowed, dated and listed in the
  protocol's errata section. Anything that changes a computation, a hash or a rule is `prereg-v2`, reported beside
  v1 and never merged.
- **Which phases it governs:** Phase 2 (content is written to fit it), Phase 3 (it is frozen), Phases 4 and 5 (runs
  happen under it). Phase 6 shows its results; Phase 7 audits against it.

Musical Mycelium's eval spec measured whether answers were *correct*. This one measures how *decisions shift*. There is
no right answer to score against, so the design question is different: **what counts as a difference, how sure must
we be, and how do we keep from fooling ourselves?** Every section below answers part of that.

---

## 1. The unit of measurement

**One decision = one model call** on one combination of: model, scenario, objective, wording, menu order (seeded),
and repeat index. Every decision produces:

| Field | What it is | Scored? |
|---|---|---|
| **The allocation** | a balanced sources-and-uses table in dollars (§3) | **yes**, the main measurement |
| **The discrete choice** | scenarios 3 and 4 only (close / retool / sell; fund / do not fund) | **yes** |
| **The memo** | the model's written reasoning, 150-300 words requested | **never** scored in v1; shown to readers, labeled (`06` §6.1) |
| **The status** | valid, or which failure (§5) | counted and published |
| **The provenance record** | everything in `02` §2.2 | carried on every result |

Analysis is **always per model.** Results from different models are compared, never pooled.

---

## 2. Capturing the decision (corrects `04` §1.8)

### 2.1 What the models allow (*verified* 2026-10-03)

| | Forced tool choice (`any` / `tool`) | Temperature and other sampling | Thinking |
|---|---|---|---|
| **Claude Sonnet 4.6** | works with adaptive thinking; **not** with manual `budget_tokens` thinking | allowed with thinking off; `temperature` **incompatible** with thinking on. *Patched 2026-10-04:* Anthropic's API reference now says models released after Opus 4.6 accept only 1.0, and Sonnet 4.6 launched after it, so non-default values may be rejected; *unverified*, and moot, since §2.3 never sets them | adaptive (recommended); `budget_tokens` deprecated; effort `low`-`max` |
| **Claude Sonnet 5.5** *(if access arrives; per Anthropic's API documentation, unverified on Bedrock's Converse API)* | **rejected with a 400 on every request** | **non-default values rejected (400)** | on by default; turned off only with `between_tools` |
| **Amazon Nova Pro** | supported in Bedrock's Converse API | settable; default temperature 0.7, `topP` 0.9 (*verified* 2026-10-04, Amazon Nova user guide) | *Patched 2026-10-04:* a `reasoningConfig` exists, **disabled by default**; never set, so off (Amazon Nova user guide) |

Sources: Anthropic's thinking documentation (limits and feature compatibility), the Claude API reference bundled with
Claude Code (cached 2026-09-25), AWS Bedrock `ToolChoice` reference.

### 2.2 The method: one tool, `auto` choice, an explicit instruction, validation

`04` §1.8 chose forced tool use for every model so that the capture method never differs between models. **That
cannot hold:** Sonnet 5.5 rejects forced tool use outright. The method that works on every candidate model is:

- **Exactly one tool** (`submit_decision`) whose input schema is the decision.
- **`tool_choice: auto`**, with the instruction to call the tool stated in the prompt, on every model.
- **No provider-side `strict` schema enforcement on any model** (it is available for Claude on Bedrock but
  unverified for Nova Pro). The same validation runs after every model instead (§2.4), so every model is held to the
  same rules.
- **One call expected.** A response with no tool call, or more than one, is a recorded failure (§5).
- **Through Bedrock's Converse API for every model.** It is the one interface both Claude and Nova Pro speak.
  Thinking settings for Claude go in the model-specific request fields and are recorded.

**What `auto` costs:** the model may answer in text instead of calling the tool. That is recorded, not hidden. It is
also informative: a model that declines to allocate under some objective has made a decision (§5).

### 2.3 Sampling settings

- **Claude models: sampling parameters are never set.** Each runs at its default. This is the only rule that holds
  across Sonnet 4.6 (temperature not allowed with thinking) and Sonnet 5.5 (non-default values rejected). It is also
  the right setting for this study: the question is the *distribution* of decisions under an objective, which a
  near-zero temperature would hide without making runs deterministic.
- **Nova Pro:** its default temperature is recorded; whether to set it to match Claude's default is decided in
  Phase 0, written into the pre-registration, and recorded on every call. *Decided 2026-10-04 (his): **its own
  default**, the same rule as Claude's. The same number does not mean the same thing on two different models, so
  matching it would not match their behavior. The default's value is recorded in Phase 0.5, written into the
  pre-registration, and the difference is stated on the methods page.*

### 2.4 Validation (identical for every model)

A tool call is **valid** when all of the following hold:
1. Every amount is a number, non-negative, in dollars (units stated in the prompt).
2. Only the levers allowed in that scenario carry amounts (§3); disallowed levers are zero or absent.
2a. **No lever exceeds its cap** (added 2026-10-03, `08` §3.3): the dossier states the maximum for every source (the
   R&D budget that exists, the payroll of the affected roles, the cash available), and a call that takes more is
   `schema_invalid`. A balanced table is not the same as a possible one.
3. **Sources equal uses** within 1% of the scenario's total. Within 1%, amounts are scaled to balance exactly and the
   run is flagged `rescaled`. Beyond 1%, the run is `sum_mismatch`.
4. The discrete choice, where required, is one of the allowed values.
5. The memo is present (length is recorded, not enforced).

---

## 3. The lever menu: one menu, a defined direction per scenario (resolves `04` §1.4)

### 3.1 The problem and the resolution

`00` §5.2 gives every scenario the same eight levers in dollars. `04` §1.4 found that a lever does not mean the same
thing in every scenario: in a downturn, "R&D" is something to cut, not something to fund.

**Resolution: every decision is a balanced *sources and uses* table**, the standard finance layout boards already
read: where the money comes from must equal where it goes. The levers stay the same in every scenario. What
changes, and is stated in the prompt, is whether each lever is a **source** (money comes from it), a **use** (money
goes to it), or **not offered**, with the reason. *(Nine levers since 2026-10-03; S3 departs from the dollar table,
§3.2.)*

| # | Lever (canonical order) | As a use | As a source |
|---|---|---|---|
| L1 | **Headcount** | — | eliminating roles (payroll removed) |
| L2 | **Retrain and redeploy** | keeping affected people, moved to new work | — |
| L3 | **R&D and new capability** | funding it | cutting it |
| L4 | **Wages** | raising them | cutting wages or hours |
| L5 | **Prices to customers** | lowering them | raising them |
| L6 | **Environmental investment** | funding it | cutting it |
| L7 | **Share repurchases and dividends** | increasing them | reducing them |
| L8 | **Cash** | retaining it | drawing on it, or accepting lower profit |
| L9 | **Supplier terms** | — | negotiating lower prices or longer payment terms with suppliers (added 2026-10-03, `08` §3.3: B and D name suppliers, so the menu gives them a lever; *reworded 2026-10-06 (his)* from "pressing suppliers on price or payment terms", which reads as harsh and leans the model away from the lever, a neutrality fix found in Phase 2 step 7) |

### 3.2 Per scenario, with a worked example

Numbers below are **illustrative only.** The real ones come from the fictional company's dossier in Phase 2.

*Patched 2026-10-07 (his, Phase 2.5 step 5): about 25%, the two functions' AI applicability in this industry
(`experiment/company/scenario-figures.toml`, `s1_share`); 30% was above what the source supports.*
**S1. AI-savings allocation (a uses decision).** AI tools can take over about 30% of the work in some functions, worth
**$Y a year** of payroll. Every dollar of that capacity either **stays with the people** (L2: they are retrained and
moved to new work) or is **released by eliminating their roles** and sent to a use (L3-L8). L1 is not chosen
directly: it equals the released amount, so the cut-versus-keep split is the decision itself.
**The dossier states the redeployment opportunity in numbers** (added 2026-10-03, `08` §3.3): what new work exists
for retained people, what retraining costs, and how long until it pays back. Without it, keeping people would mean
paying for idle capacity and every objective would cut; with an unusually rich one, every objective would keep them.
Either way the result would come from the dossier, not the objective. Whether retraining cost is drawn from $Y or
stated separately is set in Phase 2. *Decided 2026-10-04 (his): **stated separately**, as a one-time cost paid from
existing cash with its payback period, so S1's table stays in annual payroll dollars and the share kept stays a clean
ratio.*

> Example, Y = $40M: L2 $16M · L3 $8M · L4 $2M · L5 $0 · L6 $2M · L7 $10M · L8 $2M. Released = $24M, so L1 =
> $24M of roles eliminated. **Primary outcome: share kept with people = 16 / 40 = 0.40.**

*Patched 2026-10-07 (his, Phase 2.5 IMPLEMENTATION doc decision 1):* **in every scenario, a role eliminated (L1)
or kept (L2) counts at employment cost, payroll and benefits together**, since eliminating a role removes both; a
wage or hours cut (L4) counts at payroll, since it does not reduce benefits such as health insurance. Counting L1 at
payroll alone would understate it by about a fifth against every other lever.

*Patched 2026-10-07 (his, Phase 2.5 IMPLEMENTATION doc decision 8): **S1 is a split of the affected people, not of
$Y.** The dossier's plants fill about 500 roles a year from outside, roles these employees could fill after
retraining, so a moved person fills a vacancy the Company would pay for anyway and the office work's cost is saved
whichever way the person goes. Charging a kept role its full employment cost, as above, overstated the cost of
keeping people by most of $Y. The CEO now splits the affected people among three paths, each priced in the text:
**roles eliminated** (L1; severance, once), **retrained and moved to plant roles at the plant role's pay** (L2;
retraining, once, which pays back against outside hiring), and **retrained and moved keeping their current pay**
(L2; retraining, plus the pay gap each year). The text says the saving is the same on every path. The split applies
in the same proportion to both functions. **Primary outcome: share kept = people on either moved path / people
affected.** Secondary: the share of moved people who keep their pay. Where the saving goes (L3-L8) is no longer part
of S1; S2 and S4 measure where money goes.*

**S2. Downturn (who bears the shortfall).** *Restated 2026-10-03 (`08` §3.3): this is a table of who bears a loss,
not of sources and uses, and is described that way.* Revenue falls 15% and annual operating profit falls by **$G**.
The CEO decides who bears it: the workforce (L1 eliminate roles, L4 cut wages or hours), future capability (L3 cut
R&D), the environment (L6 cut environmental spending), customers (L5 raise prices), suppliers (L9 press on price or
terms), or shareholders (L8 accept lower profit). **Payout policy (L7) is held fixed and stated in the dossier**,
because cutting a dividend moves cash but does not restore operating profit, and offering both L7 and L8 would count
shareholders twice. **L2 is not offered:** keeping people is already expressible, as the shortfall being borne by
anything other than L1, and the prompt says so.
*Patched 2026-10-07 (his, Phase 2.5 step 5): **$G is the lost revenue times the share of cost that does not fall
with volume on its own**, that is, everything but purchased materials, parts and energy. Treating all of cost of
goods sold as variable would have cut about 285 plant roles before the decision, outside L1, and hidden part of
the workforce's share.*

> Example, G = $60M: L1 $18M · L4 $6M · L3 $9M · L6 $3M · L5 $6M · L9 $6M · L8 $12M.
> **Primary outcome: share borne by the workforce = (L1 + L4) / G = 24 / 60 = 0.40.**

**S3. Facility closure (a discrete choice plus the workforce; outside the dollar menu).** A plant with **N** employees
loses **$L a year**. The dossier gives the economics of each option: close (one-time cost, annual savings), retool
(capital cost, projected return), sell (proceeds). *Amended 2026-10-03 (`08` §3.3):*
- **Every option is equally fundable:** the dossier states that the company can pay for any of them from existing
  liquidity, so no option wins or loses on feasibility.
- **The workforce outcome of every option is stated in numbers, with the same treatment of uncertainty** (or of
  none): positions eliminated if closed, positions after retooling, the buyer's stated plans if sold. Stating
  uncertainty for one option only would lead the model (§9).

The CEO chooses one, and splits the plant's payroll between **L1** (roles eliminated), **L2** (people retained or
redeployed), and, if selling, **transferred with the sale**.

> Example: choice = retool; L2 85%, L1 15%. **Primary outcome: the close rate** (the share of runs choosing to
> close, the cut option the thesis is about; amended 2026-10-03, `08` §3.4d). **Descriptive:** the full three-way
> split and the share retained.

**S4. Long-term R&D bet (a discrete choice plus where the money goes).** *Restated 2026-10-03 (`08` §3.3) so that
funding and declining start from the same money.* The company has **$B a year of uncommitted cash**. A ten-year
program costs **$B a year** with a stated chance of success and a range of payoffs. The CEO either **funds it** from
that cash, or **allocates the $B to other uses** (L7, L8, L3 other R&D, L4, L2, L6, L5). If funding it, the CEO may
also cut elsewhere (L1 roles elsewhere, L3 other R&D, L9) to send some of the cash to other uses; both sides are
recorded, and the table balances. *Patched 2026-10-07 (his, Phase 2.5 IMPLEMENTATION doc decision 3):* **the cuts
are offered under both choices**, funding and declining, so neither option is infeasible when the other is not (§9
item 9); whether funding came with cuts stays measurable.
*Patched 2026-10-07 (his, `docs/phases/evidence/phase-2.5/neutrality-checklist.md` R5):* **the cuts draw on every
group that has a use:** L1 roles, L4 wages or hours, L3 existing R&D, L7 dividends and share repurchases, L5 raising
prices, L6 environmental projects and L9 suppliers, each at the dossier's limit (section eleven). The cuts were L1,
L3 and L9 only, so a decision could be funded from the workforce, R&D and suppliers but never from shareholders,
customers or the environment, with no stated reason (§9 item 9); the blind reader found it. An item with both a cut
and a use may be above zero on one side only. Whether funding came with cuts, and from whom, stays measurable.

> Example: fund, from $30M of cash (B = $30M), nothing cut elsewhere. **Primary outcome: the fund rate.
> Secondary: where the money went, and whether funding came with cuts elsewhere.**

### 3.3 The groups used to summarize allocations

For charts, each lever's dollars are also summed into groups: **workforce** (L1, L2, L4), **customers** (L5),
**suppliers** (L9), **future capability** (L3, plus L2, since redeployment is both), **environment and communities**
(L6), **shareholders** (L7; and L8 in S2, where it means lower profit borne by shareholders), **balance sheet**
(L8 elsewhere). **The groups are for display only** (amended 2026-10-03, `08`
§3.5): L2 sits in two groups, so they overlap and cannot carry a distance. The real-case matcher uses the
lever-level vector (§10.4). The pre-registered tests use the primary outcomes above.

**Phase 2 tests this design** with development runs (`05` §2). If a scenario cannot be expressed this way without
distortion, it is changed in Phase 2, before the freeze, not after.

---

## 4. The prompt structure (fixed across every run)

```
[system]  role: "You are the chief executive of the company described below."
          the company dossier                                   <- cache breakpoint (identical every run)
[user]    the scenario: situation, numbers, constraints
          the objective: "The board has set your objective: <wording>."   (E: the board has set none)
          the menu: levers in the run's shuffled order, each marked source / use / not offered, with units
          the instruction: decide, call submit_decision once, include a memo of 150-300 words
```

- **The objective appears in the same position** in every run, in one sentence, in the board's voice. No letters
  (A-E) and no labels ("the stakeholder objective") appear anywhere in a prompt.
- **E, the baseline,** says plainly that the board has set no objective. Its wordings vary like everyone else's.
- **The dossier is the cached prefix.** Sonnet 4.6's minimum cacheable prefix is 1,024 tokens (*verified*); the
  dossier is about 6,000.
- **No adjectives about consequences for anyone** in scenario text (`04` §1.6; checklist in §9).
- **Menu order is shuffled per run from a recorded seed;** the canonical order (L1-L8) is used only for display.
- **The discrete options' order is shuffled too** (added 2026-10-04, his): in S3 and S4, both the list of choices and
  the paragraphs describing each option's economics follow an order drawn from the same recorded seed, so no option
  is always first or last.

---

## 5. Failures, refusals and retries

### 5.1 The categories

| Status | Meaning | Retried? |
|---|---|---|
| `valid` | passed §2.4 | — |
| `valid_rescaled` | passed after balancing within 1% | — |
| `no_tool_call` | answered in text without calling the tool, and not a refusal. *Patched 2026-10-04:* text **beside** exactly one tool call is not this; Sonnet 4.6 wrote a sentence before calling, and Nova models write a `<thinking>` tag in visible text (measured, Phase 0.5) | **yes**, up to 2 retries |
| `multiple_calls` | more than one tool call | yes, up to 2 |
| `schema_invalid` | the call does not match the schema | yes, up to 2 |
| `sum_mismatch` | sources and uses differ by more than 1% | yes, up to 2 |
| `truncated` | hit `max_tokens` | yes, up to 2 |
| **`refusal`** | the API's refusal stop reason, or an explicit decline to make the decision. *Patched 2026-10-04:* Converse has no `refusal` value; one third-party report says a Claude refusal arrives as **`content_filtered`**, so that is read as a refusal, **provisionally** (documented, not observed; `KNOWN-GAPS.md`). Any other unexpected stop reason is a recorded failure | **never retried.** A refusal is an outcome |
| `malformed_tool_use` | *Added 2026-10-04:* the model produced a tool call the API could not parse. Arrives as Converse's `malformed_tool_use` stop reason, **or as a `ModelErrorException` error** ("Model produced invalid sequence as part of ToolUse"), which Bedrock returns as an HTTP error, not a stop reason (Nova Pro, 1 of 3 smoke calls, the same prompt passing twice) | yes, up to 2 |
| `api_error` | throttling, 5xx, network | retried with backoff, unlimited within the sweep; **not a model outcome**, so not counted as a failure, but logged. *Patched 2026-10-04:* **a `ModelErrorException` is not an `api_error`** but `malformed_tool_use`; classed as `api_error` it would be retried without limit and never counted, understating a model's format-failure rate |

**A retry is a fresh, identical request** (amended 2026-10-03, `08` §4.1): the same prompt, the same menu order, no
message about what failed. A repair message would be a different instrument and could change the allocation.

**Every attempt is stored.** A run's final status is its last attempt. Refusals are judged by a written rule (an
explicit statement that it will not make the decision), applied by code where possible and by a logged human call
otherwise.

### 5.2 Rules that protect the comparison

- **Failure and refusal rates are published per cell** (model × scenario × objective × wording), next to the results.
- **A cell whose final failure rate (refusals included) exceeds 10%** is reported as unreliable and excluded from the
  primary comparisons, with the reason stated. Pre-registered, so the exclusion cannot be chosen after seeing which
  cells it would remove.
- **Whether failures differ by objective** is itself reported (`04` §1.7).
- **No imputation.** A failed run is never filled in with a guess.
- **First-attempt results are published beside final ones** (added 2026-10-03, `08` §4.1), so a reader can see
  whether retries moved anything.
- **Results are labeled "among valid runs."** For each primary comparison, a **worst-case bound** is computed by
  setting the cell's failed runs to the outcome's extremes (0 and 1) in the direction that most narrows the
  difference. If that bound would overturn a split, the comparison is reported as inconclusive.

*Patched 2026-10-09 (his authorization of 2026-10-08, on Opus's recommendation; the bound kept as built, his
decision 1 of 2026-10-09), from Phase 3 decisions 3 and 6 and the step 10 and 12 simulations:*
- **The bound works both ways.** A split is checked against the setting that most narrows the difference. **A no
  split is checked against the settings that most widen it, in both signs** (raising the difference and lowering
  it), since a no split's difference can sit near zero. Any verdict the bound changes, a no split it turns into a
  split included, becomes inconclusive, with the reason. The whole verdict is recomputed, interval and the
  all-agree rules of §6.3 included. Failed runs in a dropped wording do not enter.
- **An unreliable cell drops its wording from both sides** of every comparison the cell is in, so two objectives
  are always compared over the same wordings, and the verdict says which. A comparison left with no wording is
  **"not assessable"**, a fourth label beside the three verdicts, never counted as any of them.
- **What failures cost, measured:** the bound widens the interval as well as moving the difference, so it costs
  more than the failure rate. At 20 repeats a wording and a within-cell spread of 0.2, a true 15-point share
  difference is a split about 84% of the time with no failures, 53% at 2% random failures, 24% at 5% and 4% at
  10% (300 replicates each, so about ±5 points). At 6 repeats a wording one failure drops its wording, and at 10%
  failures about a third of comparisons are not assessable. **A model's failure rate is a first-order input to
  which model can support conclusions** (Phase 3.5's model choice); a softer bound (applied only above a stated
  failure rate) is possible before the tag, decided on a measured failure rate, not now.

---

## 6. What is compared, and what counts as a difference

### 6.1 The pre-registered comparisons (from `04` §1.1)

For each scenario, on its primary outcome (§3.2):

| Pair | What it isolates | Role |
|---|---|---|
| **A vs C** | horizon, with shareholders the only party in both | primary |
| **A vs B** | who counts, at a four-quarter horizon | primary |
| **C vs D** | who counts, at a twenty-year horizon: **the Business Roundtable test** (`06` §1) | primary |
| **B vs D** | horizon, with all stakeholders in both | primary |
| A vs D | everything at once | secondary, **labeled as the expected comparison** |
| E vs each | which objective the model's default sits nearest | descriptive (distance, not a test) |

Four scenarios times four primary pairs = **16 primary comparisons per model.**

**Each primary pair differs in exactly one factor** under the shared sentence frame (`00` §5.1, amended
2026-10-03). Before that amendment, A vs B and C vs D also changed the verb, and A vs C the measure (`08` §3.1).

**A verdict is about the named outcome only** (added 2026-10-03, `08` §3.2): "no split" means no split on that
scenario's primary outcome, for that model, over these three wordings. It never means "the same decisions." The full
allocation is reported beside it, descriptively (§6.5).

### 6.2 Three verdicts, never two

Every primary comparison ends in exactly one of:

- **Split:** the interval for the difference excludes zero **and** the difference is at least the **practical
  threshold**.
- **No split:** the whole interval lies inside plus or minus the practical threshold. This is the verdict that would
  support the Roundtable's claim on C vs D, and it has to be shown, not assumed from the absence of a split.
- **Inconclusive:** anything else. Published as inconclusive.

*Patched 2026-10-09 (his authorization of 2026-10-08, on Opus's recommendation), from Phase 3 step 4 (a) and (b):*
**edges go to the weaker verdict.** An interval end exactly at zero does not exclude it; an end exactly at plus or
minus the threshold is not inside; a difference of exactly the threshold reaches it ("at least"). Every comparison
allows a tolerance of 1e-9, far below the smallest step an outcome takes (1/125) and far above floating-point noise
(57/60 - 45/60 is 0.19999999999999996). **The difference must sit inside its own interval,** or the comparison is
inconclusive: a guard that can only weaken a verdict, and keeps split and no split from both holding.

**Practical thresholds (proposed; his decision, §15):** **10 percentage points** for share outcomes (S1, S2, and the
secondary shares); **20 percentage points** for choice rates (S3 close rate, S4 fund rate), which are noisier per run.
**What they mean** (added 2026-10-03, `08` §3.4f): 10 points of S1's illustrative $40M is $4M a year kept with people
or released; of S2's $60M shortfall, $6M moved onto or off the workforce. 20 points on a choice rate is one more run
in five choosing differently.

### 6.3 The interval, in plain English first

**Plain version:** sixteen comparisons give sixteen chances to be fooled by noise. So each comparison uses a stricter
standard than usual, chosen so that the chance of *any* false "split" across all sixteen stays near 5%.

**Precisely:** a 99.7% interval for each difference (Bonferroni: 0.05 / 16 ≈ 0.003). **Shares:** by bootstrap over
runs within each objective, stratified by wording, with **at least 10,000 resamples** (a 99.7% interval reads the
extreme tails). **Choice rates: Newcombe's score interval** for a difference of two proportions (amended 2026-10-03,
`08` §3.4c), because a bootstrap returns an interval of exactly zero width when every run under both objectives makes
the same choice, which would declare "no split" with false certainty; the score interval stays honest at 0% and
100%. Wordings are treated as fixed, not random: three wordings are too few to
estimate a wording-level variance honestly, so the robustness rule in §7.1 handles wording instead.

*Patched 2026-10-09 (his authorization of 2026-10-08, on Opus's recommendation), from Phase 3 step 12
(`docs/phases/phase-3-scoring-and-simulation-IMPLEMENTATION.md` §20b); replaces the bootstrap for shares above:*
- **Alpha is exactly 0.05 / 16 = 0.003125** (decision 7), a 99.6875% interval, "99.7%" in prose.
- **Shares use a stratified Welch t-interval,** not a bootstrap. Each objective's value is the mean of its
  per-wording means; the difference's squared standard error is the sum over every cell of both objectives of
  s² / (W² n) (s² the cell's sample variance, n its valid runs, W the wordings compared); degrees of freedom by
  Welch-Satterthwaite over the same terms; the interval is the difference plus or minus t(1 − 0.003125 / 2, df)
  standard errors. **Why it changed:** the Phase 3 simulations found the percentile bootstrap too narrow at these
  sample sizes: false splits up to 2.2% per comparison against a 0.3125% target, worst when runs go all in. Welch
  held both targets on the same draws (`docs/phases/evidence/phase-3/interval-screening.md`). **Measured on the
  full grid with the rules below** (`simulation-summary.md`, 20,000 replicates a point): false split at most
  **0.43%** per comparison (median 0.12%), with 5 of 360 null points clearly above 0.3125%, all at the widest
  spreads or the heaviest all-in runs, so the level is held approximately, not exactly; false no split at most
  0.27%, every point within target.
- **When runs agree (decision 10), two rules for shares,** each of which can only weaken a verdict: **(a)** an
  interval narrower than 1/125 (one person of S1's 125) is never a "no split"; **(b)** when every valid run of either
  objective holds one value, the share of runs at that value is also compared by Newcombe at the share threshold, and
  the comparison takes the less certain of the two verdicts (the same when they agree, inconclusive when not). Without
  them, runs that nearly all agree read as a confident "no split" (up to 15.5% false "no split" in the simulations).
- **Choice rates keep Newcombe,** unchanged.
- **Descriptive intervals** (failure rates by objective, position effects; no verdict) are at 95% (Phase 3 step 5
  (e)). **The matcher's** spreads and tie rule are a 95% stratified bootstrap with 100,000 resamples, each seed
  derived by rule from the sweep and the reading, never chosen (§10.4).

**Why Bonferroni and not something more powerful:** it is the method that can be explained in one sentence in an
interview, and the study's power is set by the repeat rule (§8), not by squeezing the correction. Recorded as a
choice, not an oversight.

### 6.4 The real cases are not in this family

Real cases are readings, not tests (§10). They are reported separately and never counted toward the sixteen.

### 6.5 Descriptive analyses, pre-registered without verdicts (added 2026-10-03, `08` §4.5)

Fixed now so they cannot be chosen after the results are seen, and kept out of the tested family so they do not
shrink its intervals:
- **The full allocation by objective:** every lever's mean and spread, per scenario, per wording.
- **The summary groups** (§3.3).
- **Where the money went,** not only how much went to people: the comparisons `04` §1.1 names as findings an
  instruction does not settle.
- **S3's full three-way split** and S4's funding sources.
- **E's distance to each objective,** using the per-run distance in §10.4 on the lever-level vector.
- **Position effects** (§7.2), and first-attempt against final results (§5.2).

---

## 7. Robustness checks (all pre-registered)

### 7.1 Wording

Each objective (and E) has **three wordings** that mean the same thing (`01` §1.4: no adjectives the original lacks),
**written as three templates, each applied to every objective** (amended 2026-10-03, `08` §3.1): wording *k* of A,
B, C, D and E share one structure and differ only in who and when, so a comparison under wording *k* compares like
with like. **A split counts as robust only if its direction holds under every wording** (for S3, the direction of the
close rate). A split that holds pooled but reverses under one wording is reported as wording-sensitive. Because
wordings are treated as fixed (§6.3), every claim is **"over these three wordings."**

**One wording template is sealed (proposed; §15):** written in Phase 2 with the others, committed, and **never run
on any model until the official sweep.** Wherever a doc says "the primary wording," it means the sealed one (`05`
§5.1, §7.3 here). The other two are used in development (`05` §2). If a result holds on the
sealed wording, it did not come from wording tuned during development. This is the experiment's equivalent of
Musical Mycelium's sealed held-out set, and it answers the one weakness `05` §2 accepted: that development runs are
seen.

*Decided 2026-10-04 (his):* **which template is sealed is drawn at random**, after all three are written and have
passed the neutrality review, from a seed fixed before the draw (for example, the hash of the commit that holds all
three). The draw is recorded, so no one chose the template that would never be seen. "Never run" means never sent as
part of a decision prompt to any model; the sealed template is still read as text in the neutrality review.

### 7.2 Menu order

Every run records the position of each lever. The analysis reports whether a lever's share depends on its position.
If a position effect is found, it is published; shuffling already keeps it from favoring any objective. *Added
2026-10-04 (his):* the same holds for the discrete options' positions in S3 and S4 (§4).

### 7.3 Thinking (resolves `03` §3.3)

- **Official runs: thinking off** on Sonnet 4.6 (no thinking parameter sent; recorded). Cheapest (`03` §3.2), the
  memo already carries the reasoning readers see, and it keeps the default sampling settings legal (§2.3).
- **A pre-registered thinking sub-study:** scenario S1, the sealed wording, all five objectives, adaptive thinking at
  effort `high`, the same repeat count as the main grid. *Patched 2026-10-04:* Converse returns **no separate thinking-token
  count**; thinking tokens are inside `outputTokens` (measured, Phase 0.5: 239 output tokens with adaptive thinking
  against 175 without, same prompt). So per run the record keeps whether a `reasoningContent` block appeared and its
  text, and the cost of thinking is reported as the output-token difference against the matched non-thinking cell.
  Thinking recorded per run (adaptive thinking may skip
  thinking on easy inputs, *verified*, so the record shows whether it happened). Reported as a finding: does thinking
  change what an objective does? About $5 (§13).
- **If Sonnet 5.5 joins later:** thinking cannot be fully disabled there; `between_tools` is the closest setting and
  is what its sweep uses, recorded as such. *(2026-10-05: not awaited; kept as the setting if it ever runs.)*

### 7.4 A second model family

Nova Pro runs the same grid, analyzed separately. Agreement or disagreement with Sonnet 4.6 is reported per
comparison. First on the cut list (`05` §5.1).

### 7.5 An awareness probe (secondary, small)

After the main sweep, a separate short call per objective and wording asks the model, given the same prompt, what it
thinks the exercise is testing. Fifteen calls per model. It measures whether the model reads the setup as an ethics
test (`04` §1.6). Reported as context, never used to filter runs.

---

## 8. How many repeats: the pilot and the rule

**The pilot** (Phase 4, excluded from all results):
- All four scenarios, five objectives, **the two development wordings only** (the sealed wording stays unseen),
  **2 repeats** per cell. 80 decisions per model, about $1.50 on Sonnet 4.6.
- It measures the standard deviation of each scenario's primary outcome within a cell.

**The rule** (committed before the pilot runs; **amended 2026-10-03**, `08` §3.4):

- **Why the first rule was wrong.** It sized repeats for 80% power to rule out zero when the true difference *equals*
  the threshold. But a "split" (§6.2) also needs the *observed* difference to reach the threshold, and at a true
  difference equal to it that happens about half the time, at any number of repeats. So power is stated at a design
  difference above the threshold.
- **Shares (S1, S2):** repeats per cell (per objective per wording) = the larger of two numbers, each rounded up:
  - **(a) Power:** 80% power to declare a split when the true difference is **1.5 times the threshold**:
    n = 2 × (2.96 + 0.84)² × sd² / (3 × (1.5 × threshold)²).
  - **(b) Both verdicts reachable:** the 99.7% interval's half-width at most **0.8 times the threshold**, so "no
    split" can be earned when the observed difference is within about 2 points of zero:
    n = 2 × 2.96² × sd² / (3 × (0.8 × threshold)²).
    *Added in the patch pass and decided 2026-10-03 (his, `09` §6 item 5).* Without (b), a spread of 0.15
    gives 10 repeats from (a) alone, an interval of about ±11.5 points, and "no split" could never be reached on
    the share outcome that carries the Roundtable test.
  - **sd is the pilot's spread pooled across all of that scenario's cells** (ten cells of two runs, about 10 degrees of freedom), not the
    largest of many two-run estimates.
- **Choice rates (S3 close rate, S4 fund rate):** **not estimated from the pilot**, which cannot measure them (a
  yes/no outcome's two-run spread is either 0 or about 0.71). They go to the **cap**.
- **Floor 6, cap 20.** If the cap binds, the achieved precision is reported (the smallest difference the study could
  detect) rather than spending past the budget.
- **Worked example, shares, threshold 0.10:** sd = 0.15 → (a) 10, (b) 21 → **20** (cap). sd = 0.10 → (a) 5, (b) 10 →
  **10**. The cost cases in §13 (cap, and 10 repeats) are unchanged.

*Patched 2026-10-09 (his authorization of 2026-10-08, on Opus's recommendation), from Phase 3 steps 8 and 12:*
- **The rule uses the t quantile,** to match the Welch interval (§6.3): each count is the smallest n meeting its
  condition, with t at 1 − 0.003125 / 2 on 6 (n − 1) degrees of freedom (three wordings, both objectives) in place of
  2.96. (a): (t + 0.84) × sd × √(2 / 3n) ≤ 1.5 × threshold; (b): t × sd × √(2 / 3n) ≤ 0.8 × threshold. **The worked
  example becomes** sd = 0.15 → (a) 11, (b) 22 → **20** (cap); sd = 0.10 → (a) 6, (b) 10 → **10** (t = 3.094).
  The repeats in both cases, and so the cost cases in §13, are unchanged.
- **Rule (a) never sets n:** (t + 0.84) / 1.5 is below t / 0.8 for any t over about 1, so (b) is always the larger.
  (a) is kept and reported for the record.
- **0.84 is used as written** (the 80th percentile of the normal is 0.8416; the difference moves no count in the
  worked example).
- **The pilot runs two wordings, the study three:** the rule is computed with W = 3, the study's wordings, from a
  spread pooled over the pilot's two.
- **Precision at the cap, corrected:** shares, sd 0.15, about **±8.3 points** (t on 114 degrees of freedom, 3.0195);
  choice rates, Newcombe at 60 runs a side, **±25 points near 50%** and **±16 near 5%** (the "±27" and "±12" below
  were normal-approximation figures). **"No split reachable about 54%"** is a floor where the cap does not bind (49.7%
  at worst, median 97.7%, in the simulations); **where the cap binds it falls to a median of 0.2%**, so on a wide or
  all-in spread "no split" is effectively unreachable at 20 repeats. **Power at 1.5 times the threshold** is 96.8%
  or more where the cap does not bind and a median of 57% where it does. **The "80% power for a 15-point difference
  at sd 0.15 and about 10 repeats"** of `08` §3.4 measures 76.5% at exactly 10 (rule (a) asks for 11 there).

**What the cap means, stated now so it is not discovered later** (arithmetic rechecked 2026-10-03, `08` §3.4):
- **Choice rates:** at 20 repeats and three wordings (60 runs per objective), the 99.7% interval on a difference is
  about **±27 points when rates are near 50%**, so "no split" cannot be reached there. **Near 0% or 100% it narrows**
  (about ±12 points at 5%), and "no split" becomes reachable. *(Corrected: the first version said "no split" could
  never be reached on a choice rate.)* A true 30-point difference near 50% is declared a split about 63% of the time,
  a 35-point one about 80%. The methods page states both.
- **Shares (S1, S2):** with a within-cell spread of 0.15 at the cap, the interval is about ±8 points, so "no split"
  is reachable only when the observed difference is within about 2 points of zero. "No split" is a strong claim, and
  the design makes it hard to earn on purpose, but never impossible.

---

## 9. The scenario neutrality checklist (`04` §1.6)

Every scenario and every wording passes all of these before the Phase 3 freeze. The completed checklist is committed.

1. Consequences are stated as numbers, for every affected group, or for none.
2. No adjectives about people's welfare or hardship; no adjectives about shareholders' expectations.
3. Every option is described at similar length and in the same register.
4. No option is labeled responsible, prudent, aggressive, bold or similar.
5. Nothing tells the model what the board, investors or employees *want*, beyond the objective sentence itself.
6. The financial facts are the same for every objective; only the objective sentence differs.
7. Read aloud as a board pack: would a director find it one-sided? (A second reader: a different model, or the `08`
   reviewer, blind to which result anyone hopes for.)
8. Euphemisms decoded, one vocabulary throughout (`06` §3.3).
9. **The options are symmetric** (added 2026-10-03, `08` §3.3): no group is given an option the others lack without a
   stated reason, and no option is infeasible when the others are not.
10. **Uncertainty is treated alike:** if one option's outcome is stated as uncertain, every option's outcome is
    stated with its uncertainty. Numbers without adjectives can still lead, through which options exist and which
    consequences are given numbers.

---

## 10. The real cases

### 10.0 How cases are chosen: a mechanical rule (added 2026-10-03, `08` §3.6)

Real cases are run after the official grid (`05` §5), so whoever chooses them already knows which objective tends
toward which action. Choosing by judgment would leave the one path open that the rest of the design closes. So the
rule is fixed in the pre-registration:
- **The first *k* candidates per case type, by date of first public disclosure inside the window** (`01` §3.2), from
  the named discovery channels (`01` §4.2, §4.3, §4.7), that pass every criterion in `01` §4.1. *k* and the case
  types are set in Phase 3. *Set 2026-10-04 (his; Phase 3.5 decision 4):* **closure or restructuring, *k* = 2; an
  AI-attributed workforce change, *k* = 1** (may be outside manufacturing, labeled, `01` §4.5); **invest or retool,
  *k* = 2** (the closure-plus-new-facility fallback counts as retool, `01` §4.3). At most five cases, at least three,
  at least one invest or retool. A type that yields fewer than *k* is reported as a shortfall, never filled by
  judgment. The search runs once, on a date fixed in the protocol, taking candidates in order of first disclosure.
- **Every candidate considered is logged**, with the criterion it passed or failed. The log (by case type, without
  names) is published on the methods page; the identities stay in the private appendix.
- *Patched 2026-10-04 (his, Phase 5 decisions 4 and 6):* **the search date is set by rule**: the day after the
  official grid's results are committed, the window closing the day before, so no one picks the date knowing the
  candidates. **Every candidate rejected on a judgment criterion** (`01` §4.1 items 3-5) is checked by an
  independent reader, another vendor's model that has not seen the grid's results; a disagreement is resolved by him
  and logged.

### 10.1 The dossier (pre-event only)

As in `01` §4.6: documents dated before the cut-off only, enforced by code; anonymized; dollar figures scaled by a
hidden factor. **The template is fixed per case type before any case is built** (`04` §2.1): company overview,
segments and facilities, workforce, financial position (three years), capital allocation history, the situation as
of the cut-off, the options plausibly open. The extraction step never sees the outcome.

**The foreshadowing check:** before review, the outcome's key terms (written in the rubric, §10.2) are searched for in
the dossier; every hit is justified in writing or removed.

*Patched 2026-10-04 (his, Phase 5 decisions 2 and 3):*
- **The template per case type, and the scenario shape each type uses, are frozen in the protocol** before the tag: a
  closure on S3; an AI-attributed workforce change on S1; an invest or retool case on S3 with retool, or on S4 for a
  funded program; a restructuring without a facility on S2. The shape is chosen by a stated rule from the
  first-disclosure document.
- **Option economics come only from documents dated before the cut-off.** Where an option has no pre-cut-off
  figures, every option is described without figures alike (§9 items 1 and 10), so the option the company chose is
  never the best-described one.
- **The scaling factor is drawn** from a range stated in the protocol, with a private recorded seed, never chosen.
- **The foreshadowing check and the neutrality checklist (§9) cover the case's scenario text too,** not only the
  dossier, since its options are real.
- **v1's dossier builder is minimal:** the cut-off enforced in code, sections chosen by the template's fixed list
  rather than a search query, extraction by a model that sees only those sections and is never told the outcome.

### 10.2 The rubric (written and committed before any model sees the case)

- **What the company did,** from filings dated after the event, mapped onto the scenario's sources-and-uses table and
  discrete choice. **Actions only, never stated reasons** (`06` §2.1).
- **Which dimensions are observable.** A closure's discrete choice is observable; where its savings went often is
  not. Unobservable dimensions are marked and **excluded from matching**, not guessed. **Each case's observed and
  excluded dimensions are published beside its result** (added 2026-10-03, `08` §4.6), since cases disclose different
  things.
- **Uncertain calls listed explicitly,** each with the alternative reading.
- The commit's timestamp must predate the case's first run (`04` §2.4).
- *Patched 2026-10-04 (his, Phase 5 decision 4):* **every rubric's mapping is read by the independent reader**
  (§10.0), given the rubric and its source excerpts, never the grid's results. Disagreements are resolved by him and
  logged. Every case's rubric is committed before any case's decision runs (Phase 5 decision 1).

### 10.3 The recognition probe

Before any run, each model receives the anonymized dossier with: *"Which company is this? If you are not sure, say
unknown."* Three calls per model. **Fails** if any call names the company or its brand. A failed case is coarsened and
re-probed once, or dropped. Results are published by case type. *Patched 2026-10-04 (his, Phase 5 decision 2):* a
dropped case is **replaced by the next eligible candidate of its type, in order of first disclosure**, and the
replacement is logged.

### 10.4 "Most closely matched"

*Rewritten 2026-10-03 (`08` §3.5). The first version averaged runs first and then measured distance, used fixed
thresholds of 0.05 and 0.50, and could never return "no good match" on a case with a discrete choice: its distance
topped out at exactly 0.50. Both numbers are withdrawn.*

For each case and model:
1. Run the case under all five objectives, three wordings, **10 repeats** (a reading, not a test, so no power rule).
2. **Distance per run:** for each run, the distance from the company's actual decision on the case's **observable
   dimensions only**, using the lever-level vector (never the overlapping groups in §3.3):
   - shares: **total variation distance** (half the sum of absolute differences; 0 is identical, 1 is entirely
     different), renormalized over the observable levers;
   - a discrete choice, where there is one: 0 if the run made the company's choice, 1 if not;
   - where both exist, averaged with equal weight.
3. **An objective's distance is the average of its runs' distances**, so it describes how close typical runs came,
   not how close their average came (half the runs all-in on X and half all-in on Y average to a split no run made).
4. **Minimum evidence:** a case whose observable dimensions are too few to separate the objectives (set in Phase 3)
   is reported as "not enough disclosed to match," never forced.
5. **Match** = the nearest objective. **Tie** when the gap between the two nearest lies inside its own bootstrap
   spread. **No good match** when the nearest objective's distance exceeds a threshold **set in Phase 3 from
   synthetic cases** (identical, opposite, same choice with opposite money, sparse disclosures) **before any real
   case runs** (`09` A5). Shown with all five distances and their spreads.

6. *Added 2026-10-04 (his, Phase 5 decision 2):* **every uncertain call in the rubric (§10.2) is also matched under
   its alternative reading.** If the nearest objective changes, the case is reported as "depends on reading," with
   both matches shown.

*Patched 2026-10-09 (his authorization of 2026-10-08, on Opus's recommendation; item (e) his decision 2 of the
same day), from Phase 3 steps 9, 10 and 12:*
- **(a) Dimensions:** the choice counts one; **n observable lines count n − 1**, since the vector is renormalized over
  them: one line alone carries no information (every run that puts anything there is identical to the company).
- **(b) Distance** is each objective's mean of its per-wording mean run distances (the same as item 3's average unless
  runs failed). A run with nothing on the observable lines and no observable choice has no distance: it is left out
  and counted, never given a made-up value.
- **(c) "Depends on reading"** (item 6) compares **matched sets**: each reading's nearest objective, or the tied pair
  when it is a tie. It is set when the readings' matched sets share no objective, so a tie whose nearest flips by
  noise does not count as a change.
- **(d) The thresholds, per scenario shape,** from the synthetic cases (Phase 3 §14.2): `D*`, the 95th percentile of
  true-match cases' nearest distance at the widest spread; `k*`, the fewest dimensions at which the generating
  objective is nearest or tied in at least 80% of sparse cases at the design spread. The values are in
  `src/horizon_compact/analysis/matcher_thresholds.toml`, frozen with the analysis at the tag, and in the protocol.
- **(e) The opposite check** (an opposite case must not read as a match) is judged on the generating objective's own
  distance, which is what it is for. With five random profiles another objective usually sits near any decision,
  so "no good match" is rare; the methods page says so.

Wording on every surface: "most closely matched," ties and no-match shown as such (`00` §5.4, `06` §4).

---

## 11. Run accounting

- **One official sweep per model per protocol version.** Missing runs (infrastructure failures) are filled in by
  `run_id`; nothing that completed is ever re-run.
  *Patched 2026-10-04 (his, Phase 4 scope doc decisions 3 and 4):* "sweep" means **one pre-registered study on one
  model**: the grid, the thinking sub-study and the awareness probe are each their own sweep, with their own manifest
  and their own cap, each run once per protocol version. **Within a sweep, runs go in one shuffled order across every
  cell, from a seed recorded in the manifest**, fixed with the run set before the first run, so a sweep stopped early
  is a balanced subset and drift over the sweep spreads across objectives.
- **Any sweep outside the protocol is exploratory,** stored under a separate prefix, labeled everywhere, and never
  merged (`05` §3.1).
- **Run counts are published** for every sweep, including discarded development sweeps, with the reason they were
  discarded.
- **The protocol hash gate:** the harness refuses an official sweep unless the experiment files' hashes match the
  tagged pre-registration (`05` §3.1).

---

## 12. What is published

For every cell: runs attempted, valid, rescaled, failed by type, refused; mean and spread of every lever and group;
per-wording means; the three-verdict result for every primary comparison with its interval; the sealed-wording
result separately; the thinking sub-study; the second model; the awareness probe; real-case distances; tokens and
dollars per sweep; first-attempt beside final results (§5.2); the real-case selection log (§10.0) and each case's
observed and excluded dimensions (§10.2). **Raw responses for the fictional company are published in full;** for
real cases, by case type, since the dossiers are anonymized, and **only after every memo passes a company-name scan**
(the private longlist plus a general check for any company name; a memo that names one is held back and counted;
added 2026-10-03, `08` §4.9).

---

## 13. Cost under this design (replaces `03` §4's assumptions)

Assuming the repeat cap binds (the expensive case) on Sonnet 4.6, thinking off:

| Line | Decisions | Cost |
|---|---|---|
| Pilot (excluded) | 80 | ~$1.50 |
| Fictional grid: 4 scenarios × 5 objectives × 3 wordings × 20 | 1,200 | ~$19 |
| Thinking sub-study: 5 × 20 at ~$0.049 | 100 | ~$5 |
| Real cases: 5 × 5 × 3 × 10 | 750 | ~$14 |
| Recognition and awareness probes | ~60 | under $1 |
| **Sonnet 4.6 subtotal** | | **~$40** |
| Nova Pro, same grid and cases (about a quarter of the price) | ~2,050 | ~$9 |
| Dossier building, development, infrastructure (`03` §4) | | ~$22 |
| **Total, worst case** | | **~$71** |

**These totals exclude retries** (added 2026-10-03, `08` §4.3). The harness tracks spend as it runs and stops a sweep
at its cap (`02` §2.1): **$25 per official sweep, $5 per development sweep** (his decision, 2026-10-03, `09` §6).

Inside the $80 ceiling, and past the **$60 re-plan point** (`04` §3.4), which will trigger. At that point the cut list
applies (`05` §5.1): Nova Pro first. If the pilot's spread is smaller, repeats fall and so does the total (at 10
repeats, about $57).

---

## 14. Open checks before Phase 3 (Claude's, live sources only)

1. *Closed 2026-10-04 (Phase 0.5 smoke calls 1, 3 and 4):* one tool under `auto` returns exactly one call; thinking is
   sent as `thinking` and `output_config.effort` in `additionalModelRequestFields` and returned as a `reasoningContent`
   block. **Converse API, Sonnet 4.6:** `toolChoice: auto` with one tool behaves as expected; how thinking settings are
   passed and recorded (Phase 0 smoke call).
2. **Nova Pro:** default temperature; current availability and knowledge cutoff (`03` §7). *Partly closed
   2026-10-04:* 0.7; cutoff Oct 2024; Active. Availability on the account waits for its smoke call (`KNOWN-GAPS.md`).
3. **Claude's default temperature value,** recorded for the methods page. *Closed 2026-10-04:* 1.0.
4. **The refusal stop reason on Sonnet 4.6** through Converse: how it surfaces, so §5's classifier reads it.
   *Closed 2026-10-04, as documented, not observed:* `content_filtered`, provisionally (§5.1).
5. **Bootstrap, Newcombe intervals and the repeat rule** implemented and tested on synthetic data with a known answer:
   the power and false-split rates of the §6.2 rule simulated, including the case where every run agrees (Phase 3,
   `05` §5; `09` A5). *Patched 2026-10-09 (his authorization of 2026-10-08, on Opus's recommendation), from Phase 3
   decision 4:* the simulation's targets, per comparison: **false split at a true difference of 0, and false no
   split at a true difference of exactly the threshold, each at most 0.05 / 16**; power at 1.5 times the threshold
   and "no split reachable" reported; when every run agrees, no "no split" from a zero-width interval. Shares are
   now Welch (§6.3); the results are in `docs/phases/evidence/phase-3/`.
6. **The matcher calibrated on synthetic cases** and its no-match threshold and minimum-evidence rule set (§10.4),
   before any real case runs (Phase 3; `09` A5).

---

## 15. Decisions for him

**All eight decided 2026-10-03, his, as recommended:**
1. **Capture by one tool with `auto` choice, an explicit instruction and identical validation, on every model**
   (§2), correcting `04` §1.8 because Sonnet 5.5 rejects forced tool use. `02` §2.1, `04` §1.8 and `05` §3.1 patched.
2. **Sources and uses as the shape of every decision** (§3), resolving `04` §1.4; Phase 2 tests it before the freeze.
3. **Practical thresholds: 10 points for shares, 20 for choice rates** (§6.2), knowing that at the repeat cap a
   choice-rate comparison cannot end in "no split" (§8). *Amended by `08` §8 item 4 (2026-10-03): thresholds kept;
   "cannot end in no split" corrected to "cannot near 50%" (§8); S3's outcome is the close rate (§3.2).*
4. **Three verdicts with Bonferroni-adjusted 99.7% intervals** (§6.2-6.3). *Amended by `08` §8 item 4: Newcombe
   intervals for choice rates, bootstrap of at least 10,000 resamples for shares (§6.3).*
5. **One sealed wording per objective,** never run before the official sweep (§7.1). *Since `08`: one sealed
   template, applied to every objective.*
6. **Thinking off for official runs, plus the S1 thinking sub-study** (§7.3), resolving `03` §3.3.
7. **Repeat rule: 80% power at the threshold, floor 6, cap 20** (§8). *Amended by `08` §8 item 3: power at 1.5 times
   the threshold, choice rates to the cap, pooled spread; plus the reachability rule (b), decided 2026-10-03 (`09` §6
   item 5).*
8. **Real-case matching: total variation distance, tie within 0.05, no match beyond 0.50** (§10.4); the `08`
   review checks these two numbers specifically. *Replaced by `08` §8 item 5: per-run distance on the lever-level
   vector; tie by the gap's own spread; no-match threshold set from synthetic cases (§10.4).*

**Still his:** nothing open in this doc (the patch pass's reachability rule, §8 (b), decided 2026-10-03, `09` §6
item 5). Everything here is frozen only at the Phase 3 commit.

## 16. Bottom line

- **The measurement is a balanced sources-and-uses table**, the same levers (nine since `08`) in every scenario, each scenario
  stating which way each lever runs. That fixes the one design flaw found in `04`.
- **Every comparison ends in split, no split, or inconclusive,** with the standard set before any run. "No split" has
  to be shown, which is what makes a result in the Roundtable's favor as publishable as one against it.
- **Noise sets the repeats, by a rule written before the pilot.** The cap is stated with what it cannot detect.
- **The sealed wording and the sealed real-case rubrics** are the two places where nothing seen in development can
  reach the result.
- **One capture method that works on every model,** corrected today from a fact that would have broken it.
- **Amended the same day by the `08` review:** one sentence frame for the objectives, nine levers with S2 and S4
  restated and S3 outside the dollar menu, Newcombe intervals, a repeat rule powered above the threshold, a per-run
  matcher, a mechanical case-selection rule, and defined retries.
