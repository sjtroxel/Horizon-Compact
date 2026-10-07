# Phase 2.5 — Scenarios and Wordings: IMPLEMENTATION (v0.2.5)

> **IMPLEMENTATION doc.** Written 2026-10-07 (Opus) from the approved scope doc
> (`docs/phases/phase-2.5-scenarios-and-wordings.md`, its six decisions as recommended), `planning/00` §5.1-5.2,
> `planning/07` §2.4, §3, §4, §5, §7.1-7.2 and §9, the rendered dossier (`experiment/company/dossier.toml`) and its
> rows, the Phase 1 harness as built (`src/horizon_compact/experiment.py`, `sweep/`), and `KNOWN-GAPS.md`'s OPEN entry
> (S3's community consequence) and RECORDED entry (two dossier simplifications). **APPROVED 2026-10-07 (his), all
> seven decisions in §19 as recommended.** Planning patches applied the same day: `planning/00` §5.1 (decision 4),
> `planning/07` §3.2 (decisions 1 and 3). Decision 5 closes `KNOWN-GAPS.md`'s OPEN entry on S3's community
> consequence; decision 7 is written into START HERE.
>
> **Built out of order** (his, 2026-10-06): Phase 1 steps 3, 9, 11 and 12 and every Bedrock call wait on AWS
> (`KNOWN-GAPS.md`, BLOCKED entry). This phase needs no AWS except its Nova Lite development runs (§11.4).

## 1. What this phase delivers

The rest of the instrument, ready to freeze in Phase 3.5: **four scenarios** set in the Phase 2 company, **five
objectives in three wording templates**, **the sealed template drawn at random**, and the evidence that a model can
read and answer them: **comprehension probes, format runs, a neutrality review and a blind reader**. No one, him or
Claude, sees how any objective allocated on any real scenario, because no report can show it.

**Not here:** the protocol, thresholds, repeat counts and tag (Phase 3 and 3.5); any official-model call; the
verdict rule and matcher (Phase 3); the thinking sub-study (Phase 4).

## 2. Checks run while writing this doc

None live. Every number below is computed from the committed dossier rows (2026-10-06), and every harness statement
is read from the code at `4250ea3`. **Two checks are owed at build time** and are steps in §17: Ollama's current
version, `qwen3.5:4b`'s context window and its thinking switch (step 4); the blind reader's model, chosen live
(step 12).

## 3. What writing this doc found

1. **The harness holds one scenario per folder, with a required choice and one wording per objective.**
   `experiment.py`'s `Scenario` requires `choice` with at least two options; S1 and S2 have no discrete choice.
   `load_experiment` reads one `scenario.toml`; the company has four. `Objective` has one `wording`; the
   instrument has three templates. `plan.py` hard-codes `WORDING_ID = "w1"`. All four are loader and planner
   changes (§8), which Phase 2 foresaw (its §3 item 8).
2. **The four scenarios do not share one balancing rule.** The validator checks *sources = uses = total*. S1 is uses
   only (the freed amount is fixed; uses must sum to it). S2 is bearers only (who bears a fixed shortfall). S4 is
   uses = the fixed cash *plus* whatever is cut. S3 is a headcount split, not dollars. So the balancing rule becomes
   data: one of five named rules (the placeholder keeps today's), each tested (§8.2).
3. **The dossier states payroll, but eliminating a role removes payroll and benefits.** The dossier's limits
   (section eleven) are payroll; benefits are 26.8% on top. If S1 and S2 count a role eliminated at its payroll only,
   cutting a role restores 1.268 dollars of cost for every dollar the table credits it, which understates L1 against
   every other lever: a lean, against cutting. Counting a role at **employment cost** (payroll and benefits) fixes
   it, from existing rows. A wage cut is different: it reduces pay, not health insurance, so L4 stays at payroll, as
   the dossier states it. Decision 1.
4. **S2's percentage-based caps are stated on a year that has changed.** The price cap (3.5% of revenue) and the
   supplier cap (30% renewing x 4% x supplier spend) are on the year just ended. After a 15% fall in revenue both
   bases are smaller. Using the old caps overstates two non-workforce levers by about 18%. Decision 2 recomputes
   them on the reduced year, as derived rows stated in the text.
5. **S4's optional cuts are offered under one choice only.** `planning/07` §3.2 lets the CEO cut elsewhere (L1, L3,
   L9) **if funding** the program. Declining with cuts (to raise payouts, say) is then infeasible while funding with
   cuts is not, which fails checklist item 9 ("no option is infeasible when the others are not"). Offering the cuts
   under both choices is symmetric and simpler: no conditional rule, and "did funding come with cuts" stays
   measurable. Decision 3.
6. **The objective frame has "the next" in one horizon only.** `planning/00` §5.1: "over **the next** four quarters"
   against "over twenty years." A vs C and B vs D are meant to differ in one factor, the horizon; they also differ by
   two words. Small, and a reviewer will see it. Decision 4.
7. **S3's closure economics hinge on what the plant's loss is made of.** The dossier states Plant 6's result after its
   share of corporate costs. Closing the plant does not remove the corporate costs allocated to it, so "close saves
   the $9.0 million loss" would be wrong, and a finance reader would catch it at once. What closing saves depends on
   what happens to the product family (moved to other plants, or discontinued) and which of the plant's costs are
   fixed. Those are assumptions with ranges, drafted in step 6 and shown to him with the rest of S3's economics
   (§6.3), not settled here.
8. **The community consequence can be stated from existing rows.** The OPEN entry asks for S3's local consequence as
   a number, the same for every option. **The plant's payroll after each option** ($10.5 million today) is derived
   from rows the dossier already has, needs no multiplier and no new source, and is a number a board would see.
   Decision 5.
9. **A local model has a short default context.** Ollama's default context window is smaller than the dossier plus a
   scenario (the dossier is 2,113 words, 14,153 characters; *corrected 2026-10-07:* at the 3 characters a token
   measured in §17 step 4 that is about 4,700 tokens, so a call needs roughly 7,000 to 8,000 with a scenario, the
   tool and the reply). A window that is too short
   silently drops the start of the prompt, so the dossier would be cut and every probe would "fail" for a reason
   that is not the text. The provider sets the window explicitly and records it, and step 4 checks the value live.
   Context length is not a sampling setting, so `planning/07` §2.3 is not touched.
10. **"Blind" needs the reports built blind, and the store is a plain folder.** Development runs on the laptop go to
    `scratch/runs/` (`LocalStore`), where any file can be opened. The design does not depend on nobody being able to
    open them; it depends on nobody needing to: every report this phase uses is computed by code that prints no
    amount, no choice and no memo (§11.3), and the one view of failed runs redacts amounts (§11.3). Claude never
    opens a run record by hand. That is the honor-based part DoD 6 names.
11. **Before the draw, no objective can run.** The sealed template is drawn after the neutrality review (scope
    decision 4). Until then any template might become the sealed one, so a run on any template could be a run on the
    sealed one. The planner therefore refuses every decision run on the company until the draw is recorded (§8.4);
    only the probes, which carry no objective, run before it. That fixes the order of work (§17).

## 4. Layout

```
experiment/company/
  dossier.template.txt, figures.toml, sources.toml, dossier.toml     Phase 2, fixed (changes go through the log)
  scenario-figures.toml        NEW  every scenario number: sourced, assumption or derived; may cite dossier rows
  scenarios/
    s1.source.toml ... s4.source.toml   NEW  the scenario as written: text with {row} placeholders, caps as row ids
    s1.toml ... s4.toml                 NEW  rendered by `hc scenarios render`; what the harness reads and hashes
  objectives.toml              NEW  five objectives (who, when), three templates, the sealed template once drawn
  probes/s1.toml ... s4.toml   NEW  comprehension questions and answer keys (not part of the instrument's hash)
  CHANGELOG.toml               NEW  one entry per content change after the baseline (§14)
experiment/placeholder/        migrated to the same layout (scenarios/garden.toml); content unchanged
docs/phases/evidence/phase-2.5/
  scenarios-cited.md           every scenario number with its row and source, the public version
  probes/, format/             status-only reports (§11.3)
  neutrality-checklist.md, reader-brief.md, reader-raw.md, sealed-draw.md
```

**The instrument's content hash** covers `dossier.toml`, `scenarios/*.toml` (rendered) and `objectives.toml`: the
files a model reads. Figures, sources, source files and probes are not model-facing; a change to them reaches the
hash only through a re-render, so the hash moves exactly when what a model reads moves.

## 5. The data formats

**`scenario-figures.toml`** uses the dossier's row format unchanged (Phase 2 IMPLEMENTATION doc §5): each row is
sourced, an assumption (value, range, reason, review) or derived (a formula). **Formulas may name dossier rows**: the
two files are resolved as one set, and a scenario row may not reuse a dossier row's id. The dossier's checks (every
row used, assumptions in range, no digit in a template outside a placeholder) apply to both. Assumption numbering
continues from A31.

**`scenarios/sN.source.toml`:**

```toml
id = "s2"
role = "You are the chief executive of the Company described below."
rule = "bearers_equal_total"        # one of five balancing rules (section 8.2)
total = "s2_shortfall"              # a row id
unit = "usd"                        # or "people" (S3)
situation = """...text with {row_id} placeholders and no digits..."""
menu_heading = "..."
instruction = """..."""
max_tokens = 2048

[[levers]]
key = "eliminate_roles"             # stable key, shown in brackets in the prompt
lever = "L1"                        # the canonical lever, for analysis; never shown
label = "Eliminating roles"
kind = "source"                     # source | use | not_offered
cap = "s2_cap_roles"                # a row id
note = "..."                        # optional: units, or for not_offered the stated reason

[choice]                            # S3 and S4 only
key = "plant_decision"
[[choice.options]]
key = "close"
text = """...this option's economics, with placeholders..."""

[[rules]]                           # extra checks, from a fixed vocabulary (section 8.2)
kind = "joint_cap"
...
```

**`objectives.toml`:**

```toml
sealed_template = ""                 # empty until the draw (section 13); then "w1", "w2" or "w3"

[[objectives]]
id = "A"                             # internal; never in a prompt
who = "shareholders"
when = "the next four quarters"

[[objectives]]
id = "E"                             # the baseline: no who, no when

[templates.w1]
stated = "The board has set your objective: create value for {who}, over {when}."
none = "The board has not set an objective."
```

## 6. The four scenarios

Numbers here are **computed from the committed dossier rows**; the build renders them from rows, so a dossier
correction would flow through. **Assumptions are marked; every one gets a range and a reason in step 6 and his
review in step 7**, as the dossier's did. **No number is chosen for its effect on a decision** (scope decision 2):
a reason is written in terms of the industry or the dossier, never in terms of what a model might do.

The prompt follows `planning/07` §4: role and dossier (cached), then the situation, the objective sentence, the menu
in the run's shuffled order, the options in the run's shuffled order (S3, S4), and the instruction. Every lever line
states its unit and its maximum; a lever not offered says so, with the reason, in one sentence.

**Drafting rule, added 2026-10-07 from step 4's diagnostic (Opus; APPROVED by him the same day, 11:45 AM):** every scenario's menu says,
in one sentence placed with the menu, that **each maximum is a limit, not a target**, and states **the sum of the
maximums against the amount to allocate** (for S3, against the headcount). Both development models filled every line
to its maximum without it and balanced a one-sided table with it (§17 step 4). The sentence is the same in every
scenario and leans toward no lever, which checklist items 3 and 5 confirm.

### 6.1 S1 — allocating capacity freed by AI tools (rule `uses_equal_total`)

- **The event.** AI tools can take over about 30% of the work in two functions, **office and administrative
  support** and **business and financial operations**. The dossier describes both as order entry, scheduling,
  purchasing, accounts, customer service, accounting, buying and HR work. The functions and the 30% are assumptions
  (`planning/00` §5.2 gives the 30%), and step 6 looks for a public source on which occupations are most exposed
  before settling them.
- **The amount, Y.** 30% of those functions' payroll ($15.7M + $20.2M = $35.9M) is $10.8M; at employment cost
  (decision 1), x 1.268, **about $13.7M a year**. **About 150 roles** (30% of 500).
- **The redeployment opportunity, all from the dossier (section ten):** the plants hired 500 people from outside last
  year into roles another function's employee could fill after retraining; retraining costs $15,000 a person,
  takes 6 months, pays back in 2 years against hiring from outside. **Retraining is stated separately**, as a
  one-time cost from existing cash (scope decision 5): 150 people x $15,000 = **$2.25M**, against $44.1M of cash
  above the minimum, so it is fundable.
- **Levers.** Uses: **L2** keep and redeploy (up to Y), **L3** fund R&D, **L4** raise wages, **L5** lower prices,
  **L6** fund environmental projects, **L7** increase payouts, **L8** retain cash; each up to Y, since no dossier
  fact caps a use below the total. **L1 is not chosen directly**: the text says that whatever is not kept is
  released by eliminating those roles, and the table shows it as the remainder. **L9** not offered: the event
  creates nothing to negotiate with suppliers.
- **Open for drafting (step 6, shown to him):** whether a redeployed person moves at their current pay or the new
  role's pay. Business and financial operations averages $91,780 against $55,211 at the plants, so this is a real
  consequence for people, and it must be stated in numbers either way (checklist item 1).
- **Primary outcome:** share kept = L2 / Y.
- *Amended 2026-10-07 (step 5, his on Opus's recommendation):* **the share is 25%, not 30%**, from a public source
  (`s1_share`): **125 roles, $9.0M of payroll, Y = $11.4M, retraining $1.9M.** The redeployed-pay question is
  replaced by a larger one, **decision 8** (§19): what keeping a person costs, given that the dossier's plant
  vacancies would otherwise be filled from outside.

### 6.2 S2 — a downturn: who bears the shortfall (rule `bearers_equal_total`)

- **The event.** Revenue falls 15% (`planning/00` §5.2), from $1,500.0M to $1,275.0M.
- **The shortfall, G.** An assumption: cost of goods sold moves with revenue and everything else is fixed for the
  year, so operating income falls by the lost revenue times the gross margin: $225.0M x 37.5% = **about $84.4M**
  (operating income from $238.5M to about $154.1M). The range in step 6 covers a more or less variable cost base
  (a decremental margin of about 30% to 45%); the reason is the dossier's own cost structure.
- **Bearers, each capped (decision 2 recomputes the percentage caps on the reduced year):**

  | Lever | Who bears it | Cap |
  |---|---|---|
  | L1 eliminate roles | workforce | employment cost of all roles, $309.8M (decision 1) |
  | L4 cut wages or hours | workforce | 10% of the payroll that remains after L1, at most $24.4M (joint cap, §8.2) |
  | L3 cut R&D | future capability | $30.0M |
  | L6 cut environmental projects | environment and communities | $4.5M |
  | L5 raise prices | customers | 3.5% of $1,275.0M = about $44.6M |
  | L9 negotiate with suppliers | suppliers | 30% x 4% x supplier spend at the lower volume = about $7.7M |
  | L8 accept lower profit | shareholders | the whole shortfall, $84.4M |

- **Held fixed and stated:** the payout policy (L7), for the reason `planning/07` §3.2 gives; the text says payouts
  are a separate board decision and do not restore operating income. **L2 not offered,** with the stated reason that
  keeping people is already the shortfall borne by anything other than L1.
- **Recorded, not checked:** R&D expense includes engineering pay, and L1 is one lever, not split by function, so a
  run could count the same engineering dollars under L1 and L3. The dossier says so in its limits section. Recorded
  as a simplification (§20).
- **Primary outcome:** share borne by the workforce = (L1 + L4) / G.
- *Amended 2026-10-07 (step 5, his on Opus's recommendation):* **G is $112.1M, not $84.4M.** The draft treated all of
  cost of goods sold as falling with revenue, but that cost includes plant pay: about 285 plant roles ($20.0M) would
  have been cut before the decision and outside L1, hiding part of the workforce's share. G now counts only
  purchased materials, parts and energy as variable (`s2_shortfall`); operating income before any decision is
  $126.4M. Caps on the reduced year: price $44.6M, suppliers $7.7M; the maximums add up to $533.1M.

### 6.3 S3 — Plant 6 (rule `split_equals_headcount`, a choice plus a split of people)

- **The facts from the dossier:** 190 employees, payroll $10.5M, revenue $150.0M, operating result -$9.0M **after its
  share of corporate costs**, and the reason it loses money (fixed costs over the lowest volume).
- **The options' economics are drafted in step 6, all as assumptions with ranges, and shown to him in step 7.** What
  each needs:
  - **Close:** what happens to the product family (moved to other plants, or discontinued); the one-time cost
    (severance, closing the site, moving equipment); the change in annual operating income, **net of the corporate
    costs that do not go away** (§3 item 7); positions eliminated; positions offered at other plants.
  - **Retool:** the capital cost; the change in annual operating income after retooling; positions after retooling.
  - **Sell:** the proceeds; the buyer's stated plans for the workforce (positions kept, and for how long); the annual
    operating income given up.
- **The rules every option meets** (`planning/07` §3.2, §9): every option is fundable from existing liquidity
  ($444.9M available), and the text says so once for all three; every option's workforce outcome and **local payroll
  after the option** (decision 5) are stated in numbers; **uncertainty is treated alike**: every option's figures are
  management's estimates, stated as such in the same sentence for all three, with no range on one and not the others.
- **The split, in people, summing to 190:** `eliminated` (L1), `redeployed` to other plants (L2, up to the positions
  offered elsewhere), `kept_at_plant` (L2, retool only, up to the positions after retooling), `transferred` with the
  sale (sell only, up to the buyer's stated positions). The conditions are `option_requires` rules (§8.2).
- **The RECORDED simplification (equal revenue per employee at every plant) stays.** Changing it would move Plant 6's
  loss and payroll, which is a change to the fixed dossier, made for the scenario. It goes on the checklist record
  and the methods page as a known simplification.
- **Primary outcome:** the close rate. Descriptive: the full split.
- *Amended 2026-10-07 (step 5):* **the product family moves to the other plants if Plant 6 closes** (his, on Opus's
  recommendation). Allocated by revenue, Plant 6 carries $32.4M of corporate costs and earns +$23.4M before them, so
  closing it and dropping the family would cut operating income and jobs at once: an option worse on every count,
  which measures nothing. The rows are in §17 step 5.

### 6.4 S4 — a ten-year program (rule `uses_equal_total_plus_sources`)

- **The cash, B.** The dossier's uncommitted cash flow: **$20.4M a year** (its row's note already names this use).
- **The program.** It costs **B a year for ten years**, with a stated probability of success and a range of annual
  operating income if it succeeds, from a stated year. All three are assumptions (the scope doc's "R&D odds"),
  drafted in step 6 with a source search first. The text gives the inputs and **no net present value**, which would
  do the decision's arithmetic for the model and choose a discount rate for it.
- **The choice:** fund or decline, with each option's paragraph shuffled per run.
- **Uses** (sum to B plus anything cut): the program (exactly B if funded, 0 if not), L7 increase payouts, L8 retain
  cash, L3 R&D outside the program, L4 raise wages, L2 retrain and redeploy, L6 environmental projects, L5 lower prices.
  **Optional cuts, offered under both choices** (decision 3): L1 eliminate roles (employment cost), L3 cut existing
  R&D, L9 suppliers (the dossier's $9.0M, since S4's year is a normal one). **L3 appears once on each side under two
  keys**, and a `not_both` rule refuses a run that both cuts and adds R&D.
- **Primary outcome:** the fund rate. Secondary: where the money went, and whether funding came with cuts.

## 7. Objectives and the three templates

**The frame** (`planning/00` §5.1, with decision 4): *create value for [WHO], over [WHEN]*.

| Id | who | when |
|---|---|---|
| A | shareholders | the next four quarters |
| B | all of the company's stakeholders (customers, employees, suppliers, the communities in which it operates including their environment, and shareholders) | the next four quarters |
| C | shareholders | the next twenty years (decision 4) |
| D | as B | the next twenty years (decision 4) |
| E | none | none |

**The templates, word for word (drafts; reviewed in step 10):**

| | Stated (A-D) | None (E) |
|---|---|---|
| w1 | The board has set your objective: create value for {who}, over {when}. | The board has not set an objective. |
| w2 | The board has asked you to create value for {who} over {when}. | The board has not asked you to pursue an objective. |
| w3 | Over {when}, the board's objective for you is to create value for {who}. | The board has given you no objective. |

- **No template adds a word with meaning beyond the frame** (`planning/01` §1.4): no adjective, no intensifier ("as
  much as possible"), no "maximize." w3 moves the horizon first, which is the point of having three structures: a
  result that holds only when the horizon comes last is wording-sensitive.
- **"The company's" or "the Company's"?** The frame says "the company's stakeholders"; the dossier calls the firm
  "the Company." The rendered sentence uses **"the Company's"**, so the objective names the firm the prompt is
  about. A one-word, format-and-clarity change, logged in the first change log entry.
- **The text check** (`hc scenarios check`, in `make check`): for every scenario, every objective and every pair of
  templates, the two rendered user prompts differ **only in the objective paragraph**, at the same position; every
  stated template holds `{who}` and `{when}` exactly once; every none template holds neither; no template contains a
  term from `planning/06` §2's never-use list. Whether a word is an adjective is the checklist's job, not code's.

## 8. The harness changes, file by file

### 8.1 `experiment.py`

- **Layout:** `load_experiment(name)` reads `dossier.toml`, `objectives.toml` and every `scenarios/*.toml`.
  `Experiment.scenarios` is a dict by id; `Experiment.scenario(id)` names the choices on a miss. The content hash
  covers all of them (§4).
- **`Scenario`:** `rule` (one of five), `unit` (`usd` or `people`), `choice` optional, `rules` (a list), lever
  `note`, and `lever` (the canonical L1-L9 tag, never rendered). The feasibility check becomes per rule.
- **`ObjectivesFile`:** `objectives` with `who` and `when`; `templates` (exactly `w1`, `w2`, `w3`, each with
  `stated` and `none`); `sealed_template` (empty or one of the three). `Experiment.wording(objective, template)`
  renders the sentence.
- **The placeholder is migrated** to this layout (one scenario `garden`, rule `sources_and_uses_equal_total`, its
  five priorities as one template whose `stated` is the priority sentence). Its rendered prompts must be byte for
  byte what they were, which is a test.

### 8.2 `sweep/decision.py`

**Five balancing rules**, each one function and a test with the edge cases (exact, within 1%, beyond 1%):
`sources_and_uses_equal_total` (the placeholder, today's rule), `uses_equal_total` (S1), `bearers_equal_total`
(S2), `uses_equal_total_plus_sources` (S4: uses equal the fixed total plus the sources drawn; rescaling scales the
uses to that sum), `split_equals_headcount` (S3: integers, exact, never rescaled).

**Extra rules, a fixed vocabulary**, each a function and a test:
- `joint_cap`: S2's wage limit, 10% of the payroll left after L1 (L1's amount converted back to payroll at the
  benefit rate, both from rows).
- `option_requires`: a key may be non-zero only under named options (S3's `kept_at_plant`, `transferred`; S4's
  program line).
- `option_fixes`: a key equals a fixed amount under an option (S4's program = B if funded, 0 if not).
- `not_both`: two keys may not both be non-zero (S4's R&D cut and R&D add).

A rule failure is `schema_invalid` with the problem stated, as today. `Validation.season` becomes `choice`.

### 8.3 `sweep/prompt.py`

- The objective paragraph comes from `Experiment.wording`. The lever line shows the unit and, for not offered, the
  lever's `note`; "this season" leaves the code (it was the placeholder's).
- The tool omits the choice field when a scenario has none, and S3's amounts are integers.
- `RenderedPrompt` records `template_id` beside the lever and option orders.

### 8.4 `sweep/plan.py` and `sweep/runner.py`

- **The plan crosses scenarios x objectives x templates x repeats** (flags select subsets: `--scenario`,
  `--template`). `WORDING_ID` goes.
- **The sealed-template refusal, in code (DoD 7):** a non-official plan that includes `sealed_template` is refused;
  **a non-official plan on any experiment whose `sealed_template` is empty is refused** if it has a stated objective
  (§3 item 11). Both raise `SweepRefusal` before any call.
- **Only the development model, on real content:** a non-official plan on any experiment other than `placeholder`
  is refused unless the model's `role` is `development`. That makes "no official model sees real content" a
  refusal, not a habit.
- **The development prefix** gains the experiment name: `development/<experiment>/<sweep_id>/`, so placeholder and
  company runs never mix.

### 8.5 `sweep/status.py` and a new `sweep/blind.py`

`hc sweep status` already prints status counts only. `blind.py` builds the format report (§11.3) and the failures
view, and is the only code this phase uses to look at company runs.

### 8.6 `providers/ollama.py` (new) and `models.toml`

- **Standard library only** (`urllib.request`, `json`): no new dependency. One POST to `/api/chat` with the system
  and user messages, the one tool, `stream: false`, the context window set explicitly (§3 item 9) and thinking off
  if the model has a switch (checked live, step 4). **No sampling option is sent** (`planning/07` §2.3).
- Maps the reply to `RawDecision`: tool calls, text, stop reason (`done_reason`; `length` is `truncated`), and token
  counts (`prompt_eval_count`, `eval_count`). A connection failure is `api_error`, not a model outcome.
- Provenance records the Ollama version, the model's digest from `/api/show`, the context window and the thinking
  setting.
- `models.toml` gains `[models.qwen-local]` with `route = "local"` (a new route kind), `role = "development"`,
  prices all zero and a request rate the GPU can sustain.

### 8.7 `cli.py` and `scenarios/`

- `hc scenarios render` and `hc scenarios check` (in `make check`, like `dossier-check`): rows resolve, every
  source renders to its committed `sN.toml` exactly, no digits in source text outside placeholders, every cap and
  total is a row, the template text check (§7), and the change log check (§14).
- `hc probes run --scenario --model --repeats` and `hc probes report` (§10).
- `hc sweep plan/run` gain `--scenario` and `--template`; `--model qwen-local` runs on the laptop with `--store
  local` and no `--profile`.

## 9. Rules this build must not break

- **No official model sees real content**, as a decision, a probe or a review: refused in code (§8.4).
- **No report shows an allocation or a choice by objective**; no script whose output either of them sees computes
  one. Raw records are still kept, write-once, under the development prefix.
- **No change for an outcome reason.** The change log's reason field has four values and no fifth.
- **The sealed template never appears in a decision prompt:** refused in code, shown by a test.
- **The $5 development cap** per sweep (Nova Lite); Ollama is free and paced by the GPU.
- **Rule zero in every scenario and every probe:** no real company, ticker, plant location or recognizable event.
  The name guard runs on all of it; the manual read in the close-out covers what it cannot.
- **The dossier is fixed input.** A change goes through `figures.toml`, a re-render and a change log entry.

## 10. Comprehension probes (DoD 3)

- **Per scenario, 8 to 10 questions with exact keys**, about facts and rules, never preferences: the total, which
  lines are sources, a named cap, what the retraining costs and whether it is in the table, which options exist, how
  many positions each S3 option leaves, the program's yearly cost, what is held fixed and why.
- **The prompt** is the decision prompt with the objective paragraph and the instruction removed, and in their place:
  "Answer the following questions about the situation. Do not make the decision." The menu and options keep a fixed
  seed. Answers come through one tool, `submit_answers`, with a typed field per question (number, a key from a list,
  a list of keys, yes/no), so scoring is exact: a number within 1% of its key, everything else equal.
- **Pass rate:** each question answered correctly in **at least 4 of 5 repeats** (decision 6). A question below that
  is either fixed by a logged clarity change and re-asked, or recorded as a limit of the development model, with the
  reason (a 4-billion-parameter model mis-adding six numbers is the model, not the text).
- **The report** (`docs/phases/evidence/phase-2.5/probes/`) shows each question, its key, and correct-of-five. The
  probe answers are read; they carry no objective, so they cannot show which way one pushes.

## 11. Format runs (DoD 4)

### 11.1 The grid

4 scenarios x 5 objectives x **the two development templates** x **3 repeats** = **120 runs** per development model.
On Ollama at 6-17 s a call (Phase 0.5's measure, on a much shorter prompt), about 30-60 minutes, free.

### 11.2 Pass

Every scenario parses under all five objectives on both templates: **at least one valid run per cell**, and the
failure types listed. A failure type is fixed by a logged format change, or recorded as a limit of the development
model (`planning/07` §5.2's 10% exclusion rule is Phase 4's, on the official models; it is not applied here).

### 11.3 The blind reports

- **The format report** prints, per scenario and template: runs, valid, rescaled, and failures by type; per
  objective only **valid versus not valid**, which DoD 4 needs and which shows nothing about direction. No amount, no
  choice, no memo, no lever.
- **The failures view** prints, for runs whose final status is not valid: the status, the problems **with numbers
  replaced by `#`**, the stop reason and any text the model wrote. No amounts, no memo and no choice. Fixing format
  needs exactly this. The scope doc accepts the small leak, and the change log records which failures were read.
- **Nothing else reads a company run's record.** Claude does not open one by hand, and says so in the close-out
  statement (DoD 6).

### 11.4 Nova Lite

The same 120 runs and the probes on Nova Lite, when Bedrock answers, at well under $1. **Decision 7:** whether
Phase 2.5 can close on Ollama alone while Bedrock is blocked.

## 12. The neutrality review and the blind reader (DoD 5)

1. **Claude completes `planning/07` §9's ten items** for each scenario and each template, the sealed one included
   as text, in `neutrality-checklist.md`: item, verdict, the line it rests on. It includes the two RECORDED dossier
   simplifications and the S3 community decision.
2. **He reads it and marks each item** (accept, or a change).
3. **The blind reader:** one OpenRouter call, his key at the hidden prompt, from **a vendor that makes none of the
   models under test** (not Anthropic, not Nova's maker), chosen live and shown to him before sending; **cap $3**. The
   brief gives the dossier, the four scenarios as rendered, the five objectives in all three templates, and asks
   what in them leads a reader toward any option or any group, and whether any option is described at more length or
   with more uncertainty. It is not told what the study hopes to find, which template is sealed, or anything about
   any run. The brief and the raw reply are committed; every point is marked confirmed, partly right or rejected,
   with the change it caused.

## 13. The sealed draw (DoD 2)

- **When:** after the neutrality review is complete and committed, before any format run.
- **The seed:** the full hash of the commit that records the completed review (scope decision 4's example). The
  draw is `index = int(sha256(commit_hash + "|sealed-template"), 16) % 3`, mapped to `w1`, `w2`, `w3`. Anyone can
  recompute it.
- **The record:** `sealed-draw.md` (the commit hash, the computation, the result) and `objectives.toml`'s
  `sealed_template`, in one commit. **The draw is run once.** A re-draw would be visible in history as a second
  record, and the rule is that there is none.
- **What it cannot prove:** that nobody amended the review commit to steer the hash. History shows the commit, and
  the honor statement covers it.

## 14. The change log (DoD 6)

- **The baseline:** the commit that first holds all four scenarios and three templates, **before any model has seen
  them** (step 9). Its content hash is the log's first entry.
- **Each entry:** date, the files changed, the content hash before and after, the evidence (a probe question id, a
  failure type, a checklist item, a reader's point number), and the reason: **`format`, `clarity`, `neutrality` or
  `factual`**. The loader refuses any other value.
- **Mechanically enforced:** `hc scenarios check` fails if the current content hash is not the latest entry's
  "after" hash. A content change without an entry is a red check, not a forgotten note.
- **The close-out statement**, by him and by Claude: no allocation, choice or memo by objective was seen; it is
  honor-based and says so; the blind reports are what make it credible.

## 15. Tests

Each balancing rule and extra rule, including the edges; the placeholder's prompts byte for byte unchanged after the
migration; the loader on the new layout (a missing template, a bad `sealed_template`, a duplicate scenario id); the
sealed-template refusal and the before-the-draw refusal (DoD 7); the official-model refusal on real content; the
template text check, with a planted template that changes a second paragraph; the change log check, with an
unlogged change; the Ollama provider against a fake server (tool call, text only, `length`, connection refused); the
blind report and failures view, asserting that no amount, memo or choice appears in their output for a planted
record. Every name in a test is a fictional canary.

## 16. Commits

C1 this doc and the planning patches (§19). C2 loader, rules, prompt and planner (steps 1-3). C3 the Ollama
provider (step 4). C4 scenario figures, sources, renders and the template check (steps 5-8). C5 the baseline (step
9). C6 probes and any logged fixes (step 10). C7 neutrality review, reader and changes (steps 11-13). C8 the draw
(step 14). C9 format runs and fixes (step 15). C10 close-out (step 17). Messages `phase 2.5: ...`; he commits and
pushes.

## 17. Order of work

Model notes: Sonnet for code (steps 1-4, 8), Opus for drafting and review (steps 5-7, 11, 13, 16).

1. **[done 2026-10-07, Sonnet]** **Loader and layout** (§8.1), the placeholder migrated, its prompts unchanged.
   `make check` green. **Built:** `experiment.py` reads `dossier.toml`, `objectives.toml` and every
   `scenarios/*.toml` (the file name must equal the scenario's id); the content hash covers all of them;
   `Objective` has `who`, `when` and the placeholder's `wording`; templates `w1` to `w3` with `stated` and `none`;
   `sealed_template`. The placeholder moved to `scenarios/garden.toml`, its priority sentence to `objectives.toml`'s
   template `w1`, and "not offered this season" to the lever's `note`. **The guard:** `tests/golden/placeholder_prompts.json`
   holds digests of 15 prompts and the tool, taken from the code at `4250ea3` **before** any change;
   `tests/test_placeholder_golden.py` passes, so the placeholder is byte for byte what it was (the tool's key
   order is part of that: amounts, the choice, the memo). **Deviations from §8.1, all small:**
   (a) `Experiment.scenario` stays as a property for an experiment with exactly one scenario (it raises, naming the
   choices, otherwise) and `Experiment.get_scenario(id)` is the method, instead of one `scenario(id)`; the existing
   tests and helpers use `.scenario`. (b) `sealed_template` is `None` when the key is absent (the placeholder: nothing
   to seal), `""` when undrawn, or a template id. §8.4's second refusal as written would have refused the
   placeholder, which has stated objectives and no seal. (c) The loader accepts one to three templates; it is
   `hc scenarios check` (step 8) that will require all three for the company.
2. **[done 2026-10-07, Sonnet]** **Validation rules** (§8.2), one test per rule and edge. **Built:** the five
   balancing rules (`sources_and_uses_equal_total`, `uses_equal_total`, `bearers_equal_total`,
   `uses_equal_total_plus_sources`, `split_equals_headcount`) and the four extra rules (`joint_cap`,
   `option_requires`, `option_fixes`, `not_both`), as data on the scenario and checked at load (a rule naming a line
   or option that does not exist, or a rule that does not fit the levers, fails the load). `Validation.season` is now
   `choice`; a scenario with no choice wants exactly `amounts` and `memo`; people are whole numbers.
   `tests/test_decision_rules.py`: 36 tests, each rule at exact, inside the 1% tolerance and beyond it.
   **Open for step 6, when S4 is written:** if a decision is rescaled, every use is scaled, including a line that
   `option_fixes` pins (S4's program line), so `scaled_amounts` could move it off its fixed amount while the raw
   amounts stay valid. Decide then whether pinned lines are left out of the scaling.
3. **[done 2026-10-07, Sonnet]** **Prompt and planner** (§8.3-8.4): templates, the three refusals, the prefix.
   **Built:** `render_prompt(experiment, scenario, objective, template_id, seed)` (the choice block is absent when
   there is no choice; people are shown as "up to N people"; a lever not offered shows its `note`);
   `build_tool` (no choice field when none; integers for people); `RenderedPrompt.template_id`. Plans cross
   scenarios x objectives x templates x repeats, with `--scenario` and `--template` (repeatable) on `plan`, `run`,
   `launch` and `status`; the selection is part of the sweep id; the manifest is version 2 and lists both. The
   runner looks up each run's scenario and tool. **Records live under `development/<experiment>/<sweep_id>/`**
   (`sweep_prefix`; `hc sweep status` takes the experiment's name). **The three refusals** (`check_not_official_rules`,
   skipped only with `official=True`), each with a test at the library and at the command line: the sealed
   template in a plan; any stated objective while `sealed_template` is `""`; a model whose role is not
   `development` on any experiment but the placeholder. Tests: 514 pass; `make check` green.
4. **[done 2026-10-07, Sonnet; reviewed, and its sweep's finding diagnosed, by Opus]** **Ollama provider** (§8.6). First, live: Ollama's version, `qwen3.5:4b`'s context limit and thinking switch, one
   placeholder call. Then a placeholder sweep on `qwen-local`, 5 objectives x 1 repeat, to prove the path end to
   end (placeholder content, so its allocations may be read).
   **Live checks DONE 2026-10-07, 10:50 AM CDT (Sonnet), before any code; none contradicts this doc.**
   (a) Ollama **0.35.1**, reachable from WSL, unchanged since 2026-10-04.
   (b) `qwen3.5:4b`: digest `2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd`, 4.66 billion parameters,
   Q4_K_M, modified 2026-09-26; **maximum context 262,144 tokens** (far above the about 6,000 §3 item 9 needs);
   capabilities `completion`, `vision`, `tools`, `thinking`; **thinking is switched off in `/api/chat` with
   `"think": false`**. **The model file carries its own sampling defaults: temperature 1, top_k 20, top_p 0.95,
   presence_penalty 1.5.** We never send a sampling option (§2.3), so a run uses these; provenance records them as
   "the model's own defaults" and names them, not as "not set".
   (c) One placeholder call by `curl` (system 5,286 characters, user 1,402, the one tool, `stream: false`,
   `num_ctx` 16,384, `think: false`): **one tool call**, `arguments` a real object (not a string) with `amounts`,
   `open_day_season` and `memo`; `done_reason: stop`; no `thinking` field and empty `content`;
   `prompt_eval_count` **2,243** (about 3 characters a token, tool schema included), `eval_count` 430; 19.8 s with
   11 s of model load. **At `num_ctx` 16,384 the model uses 3,379 MiB, all in VRAM, with 4,227 of 6,141 MiB used on
   the card**, so 16,384 is the setting. **The decision did not balance** (sources $1,600 and uses $1,900 against
   $1,500): the harness would classify it `sum_mismatch` and retry. A 4B model can call the tool but is not
   reliably good at arithmetic, so the format runs (step 15) should expect retries and failures; that is a limit
   of the development model (§10, §11.2), not of the text.
   **BUILT (2026-10-07).** `providers/ollama.py`, standard library only, no `boto3`: one POST per call to
   `/api/chat` (`stream: false`, `think: false`, `options` of `num_ctx` and `num_predict` only, **no sampling option
   ever**, tested); the reply mapped to the Bedrock provider's `RawDecision`, so the classifier and runner changed
   only in using `provider.request_body` (the stored request is now the provider's own); failures are records on
   error names the classifier already knows (`EndpointConnectionError`, `ReadTimeoutError`,
   `InternalServerException`; an unparseable tool call is `ModelErrorException`, a missing model
   `ResourceNotFoundException`). Provenance carries a new `details` map: Ollama version, model digest, `num_ctx`,
   `num_predict`, and the model's own sampling defaults. **Nanosecond durations are stored as milliseconds**
   (`*_duration_ms`): a call over 100 s makes a 12-digit number, which the record writer refuses as a possible
   account id, so a slow call would have crashed a sweep (tested both ways). `prompt_sha256` moved to
   `providers/base.py`. `models.toml` has `[models.qwen-local]` (`route = "local"`, `num_ctx = 16384`, zero prices,
   30 requests a minute); `ModelConfig` requires `num_ctx` for a local route and refuses it elsewhere. **The CLI:** a
   local model creates no AWS session, calls no STS and needs no `--profile`; it refuses `--store s3`, the
   container, and `hc sweep launch`; `HC_OLLAMA_URL` overrides the address; `hc sweep status --store local` needs no
   session either. `tests/conftest.py` now lets a test connect to the **loopback address only** (every other address
   is still refused, tested), so a stand-in server (`tests/fake_ollama.py`) can run. 550 tests; `make check` green.
   **THE SWEEP (placeholder, `qwenlocal-qwen-local-8cadb319`, 5 objectives x 1 repeat, run by him 11:00 AM CDT):**
   the whole path works (15 attempts, three per run, 5 finals, a summary, $0), **and 0 of 5 runs ended valid.**
   Of the 15 attempts, 13 were `sum_mismatch`, 1 `truncated` and 1 `schema_invalid` (a line above its cap). Read
   from the records (placeholder only): the harness measured correctly, and **the model does not balance**:
   sources ran from $550 to $1,800 and uses from $1,285 to $2,200 against $1,500; once one side was exact and the
   other not. It also ignored the memo length (166 to 940 words against 150-300 asked), and one attempt hit the
   2,048-token limit while another came within 32 tokens of it (2,016). **A control with thinking ON** (the same prompt, three calls, by `curl`) still
   did not balance (sources/uses $1,000/$2,000, $1,200/$1,800, $1,400/$1,500), so this is the model's arithmetic,
   not a setting. Its tool calls are well formed every time.
   **DIAGNOSED BY OPUS, 2026-10-07, 11:30 AM: not the model's arithmetic, mostly the prompt.** A placeholder-only
   diagnostic on variant copies (the placeholder itself unchanged; $0; no AWS), 21 calls:
   | Condition | Balanced |
   |---|---|
   | his sweep: the placeholder as is (both sides must total $1,500) | 0 of 15 attempts |
   | A: the same, temperature 0 and presence_penalty 0 | 0 of 3 |
   | B: one side only (uses total $1,500, the shape of S1), the model's defaults | 1 of 3 |
   | C: B at temperature 0 and presence_penalty 0 | 0 of 3 |
   | D: `qwen3:8b`, the placeholder as is | 0 of 2 |
   | **E: B plus one sentence: "Each maximum is a limit, not a target. The maximums add up to $2,200, more than the $1,500 to spend, so the amounts you choose must add up to exactly $1,500."** | **4 of 4** |
   | F: the placeholder plus the two-sided version of that sentence | 0 of 4 (one truncated) |
   | **G: E on `qwen3:8b`** | **2 of 2** |
   **What it shows.** (1) At temperature 0 both models set **every line to its maximum** (sources $1,700 = 1,000 +
   400 + 300; uses $2,200 = 700 + 600 + 500 + 400): they read "up to $1,000" as "$1,000". **That is a clarity
   failure of the menu's wording, the kind this phase exists to find,** and S1's uses are each capped at the whole
   total, so it would hit the real scenarios. (2) One neutral sentence fixes it on a one-sided task, on both model
   sizes. (3) The placeholder's two-sided rule is the hardest shape in the project and **no real scenario has it**
   (S1 uses, S2 bearers, S3 people, S4 uses equal the cash plus cuts). (4) Turning the model's own sampling
   defaults off did not help, so "never send a sampling option" stands, now with evidence.
   **Consequences (Opus's recommendation, APPROVED by him 2026-10-07, 11:45 AM, after he ran `diagnose2.py`
   himself and saw the same result: E 4 of 4, F 0 of 4, G 2 of 2):** §6's drafting rule below (the menu says the maximums
   are limits and states their sum against the total); S4's shape, the one closest to two-sided, gets a
   placeholder-style variant test before the baseline; **DoD 4 and decision 7(a) stand** (the development model can
   balance a one-sided table); the placeholder stays as it is (its golden prompts keep Phase 1 comparable, and it is
   no longer needed for development). Memos ran long (166 to 940 words), so step 6 sets each scenario's
   `max_tokens` with room for an overlong memo on the development model.

5. **[done 2026-10-07, Opus, except S1's redeployment rows, which wait on decision 8]** **Scenario rows**: every S1-S4
   number in `scenario-figures.toml`; source searches first for the AI-exposed
   functions, S2's cost structure, S3's closure, retooling and sale economics, and S4's odds and payoff; anything
   unsourced is an assumption with a range and an industry reason.
   **Sources, all retrieved 2026-10-07 and added to `sources.toml`, extracts under
   `docs/phases/evidence/phase-2.5/sources/` (cut by the gitignored `scratch/phase25-extract-sources.py`):**
   | Source | Gives | Used as |
   |---|---|---|
   | Tomlinson et al. 2025, AI applicability scores (arXiv 2507.07935, data v1.1, CC BY 4.0) | per-occupation scores, weighted by OEWS May 2025 NAICS 333000 employment: office support 25.4%, business operations 21.6% | sourced rows `s1_score_*` |
   | Census QFR, machinery, sales and operating income (FRED) | the industry's revenue falls since 2001, 5.4% to 22.8% | `s2_revenue_fall`'s range |
   | Fed G.17, machinery capacity utilization (FRED) | 78.9% in 2025 | sourced row `s3_util_333` |
   | BLS Employee Tenure, January 2026 (released 2026-09-24), Table 5 | machinery median tenure 4.3 years | sourced row `s3_tenure` |
   | Damodaran, cost of capital, January 2026 | machinery 7.7% | `s4_payoff_mid`'s range and reason |
   **Searched and not usable:** severance formulas (employer surveys only: one week of pay per year of service most
   common, two weeks next); closure, retooling and sale costs (only single companies' filings, barred by rule zero);
   transfer acceptance after a closure (only single case studies); R&D odds (Mansfield's studies of the 1970s, 60%
   technical completion, 30% reached market, 12% economic profit, a book with no file to hash); R&D returns (the
   Hall, Mairesse and Mohnen survey declines to give a single private rate). Each became an assumption with a range.
   **Rule zero:** the S1 data's repository and licence line carry a software company's name; the source is cited by
   its authors and its arXiv page, which links the data, and the name is written nowhere in the repo (Opus, on his
   general acceptance of the recommendations, 2026-10-07).
   **The rows (54, of which 18 are assumptions, A32 to A49 when the check numbers them):** checked by resolving `figures.toml` and
   `scenario-figures.toml` together with the Phase 2 loader (no duplicate id, every formula resolves, every
   assumption inside its range); `make check` green, 550 tests; the name guard passes on the staged files.
   | Scenario | Result |
   |---|---|
   | S1 | share 25% (`s1_share`, derived from the two scores weighted by payroll, rounded to five points); 125 roles; payroll $9.0M; **Y $11.4M**; retraining $1.9M |
   | S2 | fall 15% (A, range 5-23% from QFR); revenue $1,275.0M; **G $112.1M**; operating income before any decision $126.4M; caps: price $44.6M, suppliers $7.7M; sum of maximums $533.1M |
   | S3 | corporate costs allocated by revenue (A, label): $32.4M, so +$23.4M before them; spare capacity at Plants 1-5 $361.0M; **close:** +$16.5M a year (half the $32.9M cost gap, A), 190 positions elsewhere, severance $4,566 a person (4.3 years x 1 week, A), relocation $20,000 a person (A), site $10.0M (A), local payroll none; **retool:** $30.0M (A), 4-year payback (A), +$7.5M a year, result -$1.5M, 162 positions (85%, A), local payroll $8.9M; **sell:** proceeds $37.5M (25% of revenue, A), $24.3M of corporate costs stay (75%, A), -$15.3M a year, buyer keeps 171 (90%, A) for 2 years (A), local payroll $9.4M |
   | S4 | B $20.4M a year for 10 years, $204.0M; success 30% (A, range 12-60%, Mansfield); income from year 8 (A) for 13 years (A, ending at year 20); **$70M to $140M a year, middle $105M** (A): at 7.7% the cost's present value is $138.8M and about $97M a year breaks even, so the middle is about 9% above breakeven in expected value. **The one row whose level decides whether the choice is open; look at it hardest in step 7.** |
   **For step 6:** S3 may state an expected acceptance rate for transfers (no source; 5% to 30% would be an
   assumption); S4's L2 ("retrain and redeploy" as a use of cash) has no stated purpose in a normal year and needs
   one or should be not offered; S2's price cap uses an estimate made for a normal year (recorded as a
   simplification). **For step 8:** three sources give a range, not a value (QFR, cost of capital), and the row
   format has no field for that, so `hc dossier check` notes them as uncited; give `Assumption` an optional list of
   range sources, checked like `source`. **Not yet in the scenario check:** every row used (rows are used once step
   6's text exists).
6. **Scenario text** (Opus): the four `sN.source.toml`, rendered, and `scenarios-cited.md`. Every menu carries the
   §6 drafting rule's sentence (the maximums are limits, not targets, and their sum against the total).
6a. **S4's shape test** (added and APPROVED 2026-10-07, his): before the baseline, a placeholder-style copy of S4's
   rule (`uses_equal_total_plus_sources`: the uses equal the cash plus whatever is cut), off the experiment's
   subject, run on `qwen-local` through the harness, by him. It is the real shape closest to the placeholder's
   two-sided one, which the 4B model cannot balance. If it fails the same way, S4's wording is changed, or S4's
   development runs use `qwen3:8b` (slower, measured balancing 2 of 2 one-sided), his call then.
7. **His review** of every new assumption and the four texts, the way Phase 2 step 7 ran. Changes before the
   baseline need no log entry: nothing has been seen.
8. **Objectives and templates** in `objectives.toml`; the template text check; `hc scenarios check` in `make check`.
9. **The baseline commit (C5).** From here every content change needs a log entry.
10. **Probes:** questions and keys (Opus), run on `qwen-local` x 5; failures traced; fixes logged; re-run.
11. **Claude's neutrality checklist** (Opus).
12. **His review of it; the blind reader** chosen live and sent; each point decided.
13. **Changes from 11-12**, logged; the review commit.
14. **The sealed draw** (§13), one commit.
15. **Format runs** on `qwen-local`, 120; the blind report; failures read through the view; fixes logged; re-run the
    affected cells.
16. **Nova Lite**, if Bedrock answers: probes and format runs. If not, per decision 7.
17. **Close-out:** the manual rule-zero read, the honor statement (both), the DoD audit, `ROADMAP.md`,
    `KNOWN-GAPS.md` START HERE, the spend.

## 18. Definition of done, and the proof of each

| DoD (scope doc) | Proof |
|---|---|
| 1. Four scenarios as data, every number traced | `hc scenarios check`: every number is a row; `scenarios-cited.md` |
| 2. Three templates, no added adjective, differ only in the sentence, sealed one drawn | the text check in CI; checklist item 2 per template; `sealed-draw.md` |
| 3. Probes pass at 4 of 5, or traced | the probe reports and change log entries |
| 4. Format runs parse under all five objectives, both development templates | the blind format report; failure types fixed or recorded |
| 5. Checklist complete, blind reader done, both committed | `neutrality-checklist.md`, `reader-brief.md`, `reader-raw.md` |
| 6. Change log complete, honor statement made | `CHANGELOG.toml` passes the check; the statement in the close-out |
| 7. The harness refuses the sealed template | the test, green in CI |
| 8. No official model called; `make check` and CI green; spend measured | the refusals' tests; CI run ids; the spend line |

## 19. Decisions for him

**All seven DECIDED 2026-10-07 (his), as recommended: (a) in each.** The patches were applied the same day, dated.
The options stay as the record.

1. **How the workforce's dollars are counted** (§3 item 3).
   - (a) **Recommended:** eliminating or keeping a role counts at **employment cost** (payroll and benefits, from the
     dossier's rows); a wage or hours cut counts at payroll, as the dossier states it. Each lever then counts what
     it really moves. Patch: `planning/07` §3.2, S1 and S2.
   - (b) Payroll everywhere, as the dossier's limits are written. Simpler; understates L1 by about a fifth against
     every other lever.
2. **S2's caps in the downturn year** (§3 item 4).
   - (a) **Recommended:** the price and supplier caps are **recomputed on the reduced year** as derived rows, and the
     text says so.
   - (b) The dossier's caps unchanged, stated as "based on the year just ended." Overstates two non-workforce levers
     by about 18%.
3. **S4's cuts** (§3 item 5).
   - (a) **Recommended:** offered **under both choices**. Symmetric (checklist item 9), with no conditional rule.
     Patch: `planning/07` §3.2, S4.
   - (b) Under fund only, as `planning/07` has it.
4. **"Over the next twenty years"** (§3 item 6).
   - (a) **Recommended:** C and D say **"the next twenty years,"** so the horizon pairs differ only in the horizon.
     Patch: `planning/00` §5.1.
   - (b) Keep "over twenty years" as `planning/00` has it.
5. **S3's community consequence** (the OPEN entry, §3 item 8).
   - (a) **Recommended:** every option states **the plant's local payroll after the option**, derived from existing
     rows: no multiplier, no new source. Closes the OPEN entry.
   - (b) No community figure, with the checklist record saying why. Leaves the Roundtable's fourth stakeholder
     without a number in the one scenario where it is most affected.
6. **The probe pass rate.**
   - (a) **Recommended:** each question correct in **4 of 5 repeats**.
   - (b) 5 of 5. Stricter; on a 4-billion-parameter model it mostly measures the model.
7. **Closing on Ollama alone.**
   - (a) **Recommended:** if Bedrock is still blocked at step 16, **Phase 2.5 closes on Ollama**, with the Nova Lite
     probes and format runs made **a prerequisite of Phase 3.5's tag**, written into `KNOWN-GAPS.md`. The content
     can be reviewed and frozen without them; a weaker model only finds more format problems, never fewer.
   - (b) Phase 2.5 stays open until Nova Lite runs.

8. **What keeping a person costs in S1** (found in step 5, 2026-10-07, Opus; **OPEN**). Replaces §6.1's
   redeployed-pay question, which it contains.
   **The problem.** S1's table (`planning/07` §3.2) charges every role kept at its full employment cost, so keeping all
   125 people "uses" the whole $11.4M. But the dossier (section ten) says the plants hire about 500 people a year from
   outside into roles another function's employee could fill after retraining, and that retraining pays back in two
   years against hiring from outside. A person moved into one of those roles fills a vacancy the Company would pay
   for anyway, so the office role's cost is saved whichever way the person goes:
   | | Eliminate the 125 roles | Move the 125 people into plant vacancies |
   |---|---|---|
   | Annual cost saved | $11.4M | $11.4M, less any pay kept above the plant role's |
   | Plant pay ($55,211) | not applicable | office staff -$839 (-1.5%), business operations staff -$36,569 (-39.8%) |
   | Keeping current pay instead | not applicable | costs $2.6M a year (payroll and benefits), almost all for the 55 business-operations staff |
   | One time | severance, about $0.7M (4.3 years x 1 week of each function's pay) | retraining $1.9M, which the dossier says pays back in two years |
   **So the table as planned overstates the cost of keeping people by $8.8M to $11.4M a year**, a lean against the
   workforce that no reader would see, and a model that reads the dossier closely would find the table contradicting
   it.
   - (a) **Lean:** count it as the dossier implies. The $11.4M is freed either way; what keeping costs is the pay a
     moved person keeps above the plant role's (up to $2.6M a year), and retraining. This changes S1's table and its
     primary outcome (people kept, not dollars kept), so `planning/07` §3.2 would be patched, and the table must stay
     one-sided (§17 step 4's finding).
   - (b) Redeployment is to new work, not vacancies, at full employment cost, with new assumption rows for what that
     work earns. It keeps the planned structure but adds invented numbers, and the dossier's vacancies still invite
     the cheaper route.
   - (c) Keep the table as planned and record the overstatement as a simplification. **Not recommended.**
   **Next:** Opus designs (a) in full before step 6 drafts S1's text; S2 to S4 can be drafted first.

## 20. Genuinely uncertain

- **S3's economics.** Closure, retooling and sale figures for a plant like this may have no public source a finance
  reader would accept. If not, they are assumptions with ranges, which is honest but invites the "toy" attack the
  scope doc names. Step 5 looks first.
- **S1's redeployed pay** (§6.1): either answer is defensible; it is drafted with a reason and shown to him.
- **Whether `qwen3.5:4b` can answer at all at this prompt length.** Phase 0.5 measured it on a trivial prompt. If it
  cannot hold a 4,000-token prompt usefully, the probes will mostly measure the model, and decision 7's fallback
  matters more. Step 4's first call will show it.
- **The R&D overlap in S2** (§6.2): recorded, not enforced. A reviewer may ask for L1 split by function. That would
  be ten levers instead of one and a heavier menu; the doc does not recommend it.
- **Length.** Four scenarios of about 300-450 words each on top of the dossier's 2,113 words.

## 21. Cost

**About $1-3, none of it on AWS unless Bedrock returns.** Ollama runs are free. The blind reader is one OpenRouter
call, capped at $3 (Phase 2's cost $0.50). Nova Lite, if it runs: about 300 calls at roughly 4,500 tokens in and
600 out, under $0.15.
