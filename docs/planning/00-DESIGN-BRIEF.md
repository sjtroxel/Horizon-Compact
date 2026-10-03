# Horizon Compact — Design Brief

- **Name:** **Horizon Compact** (LOCKED 2026-10-02). Repo `Horizon-Compact`. Public address: a Vercel
  subdomain, `horizon-compact.vercel.app` (unclaimed as of 2026-10-02), proxying to AWS as Musical Mycelium does.
  **No paid domain** (his decision).
- **Status:** CONCEPT DECIDED through a seven-question interview (2026-10-02). Nothing verified live yet. *(As of 2026-10-03: the planning series `01`-`07` has verified the facts this brief rests
  on; see each doc's verified marks. Read `07` for the measurement design.)*
  Pre-IMPLEMENTATION-doc. **Amended by `08` (2026-10-03):** §5.1 objectives, §5.2 menu, §5.4 real-case wording, §8
  re-run wording (patches P1, P6, P7, P27, P34 in `09` §3).
- **Date captured:** 2026-10-02
- **Read order:** `00-DESIGN-BRIEF` (this) -> `01-DATA-SOURCES` -> `02-ARCHITECTURE` -> `03-COST-MODEL` ->
  `04-RISK-REGISTER` -> `05-EVOLUTION-PLAN` -> `06-NARRATIVE-AND-VOCABULARY` -> `07-EVAL-SPEC` ->
  `08-REVIEW` -> `09-PRIORITIES-AND-OPEN-DECISIONS`
- **This folder is the canonical record of every design decision.** It travels into the repo, so it must
  stand alone: a build session should never need anything outside it. The private idea file in
  `job-search-headquarters` (`next/CEO_INCENTIVES_IDEA_2026_09_25.md`) keeps only what does not belong in
  public: motivation, personal context, raw wording. **Rule until migration: every design decision lands
  here, not only there.** If the two ever disagree on a design point, this folder is fixed to match the
  decision as he made it, and then this folder governs.

> **THIS FOLDER IS WRITTEN TO BE PUBLISHABLE.** Musical Mycelium's planning folder was copied into its public
> repo on day one. Assume the same happens here. So: no personal context, no raw quotes in charged vocabulary,
> business-register wording throughout. The personal and motivational record stays in the idea file in
> `job-search-headquarters`, which is private. If a planning doc ever needs it, link, don't copy.

---

## 1. The concept (one line)

**Give the same AI the same company, change only what it is told to maximize, and measure where its decisions
split.**

The question it tests: *when a company's leader is handed a different objective, does the company use new
capability, AI above all, to cut people or to expand what it can do?*

## 2. The name

A **compact** is a voluntary agreement about whose good a group governs for. Two anchors:

- **The Mayflower Compact (1620):** signed before landing, binding the signers to just and equal laws "for the
  general good of the Colony." The story the README and launch post open with.
- **The UN Global Compact (2000):** the world's largest corporate sustainability initiative, 25,000+ companies
  committed to principles on labor, human rights, environment and anti-corruption (verified 2026-10-02). This is
  why business readers will take the word seriously: to them, "compact" already means a voluntary corporate
  commitment beyond profit.

**Horizon** is how far ahead the objective looks. Together: *what a company commits to, and how far out.*

**Known caveats** (from the 2026-10-02 checks): "compact" reads as a size until the first line explains it; the UK
Post Office **Horizon** scandal is the association UK readers will reach for first. Neither blocks the name; both
mean the first sentence of every public surface has to make the connection.

## 3. Why this project

**Portfolio role:** one piece among several (his decision, 2026-10-02), not a play to be hired *for* a point of
view. It sits beside Musical Mycelium and Patchwork Assurance and has to read as rigorous engineering with a
perspective, not as a manifesto.

**What it adds that the portfolio lacks** (from the 2026-10-02 rundown and the 9/27 AWS decision):

| Gap | How this project fills it | Confidence |
|---|---|---|
| Containers, ECS/Fargate | the experiment runs as batch container jobs | definite |
| S3, IAM depth | every run's inputs and outputs stored; real permissions between services | definite |
| Structured outputs at scale | every decision returns validated, typed data across hundreds of runs | definite |
| Evals that measure *behavior* | repeats, variance, controls, published prompts | definite |
| Multi-model comparison | same experiment across model families | likely |
| Reranking | retrieval over long, repetitive SEC filings | likely |
| Local models | free dev iteration; possibly a small-model contestant | likely |
| Fine-tuning / distillation | a small fine-tuned "CEO" vs a frontier one | hopeful, after a cost check |

**What it will not add:** inference serving, quantization, vLLM, GPU engineering (the ML-infrastructure lane he
decided to skip on 9/27). And it is an experiment more than a product with users; Patchwork and Musical Mycelium
already carry product sense.

**The story a recruiter remembers:** *"I ran the same company under different objectives and measured where the
decisions split."* Most portfolios answer questions; this one runs an experiment and presents findings.

## 4. Design principles (decided)

1. **Ask a question; don't state a verdict.** The motive drives the question. It never writes the answer.
2. **Incentives, not people.** No named executives, no villains. "The objective produces the behavior" is the
   stronger and less dismissible claim.
3. **Publish the results that cut the other way.** If the long-horizon CEO also cuts payroll, that ships. A
   study where everything agrees with its author looks rigged.
4. **Design for the "you rigged the prompts" attack.** Publish every prompt, objective, option menu, scoring rule,
   run count and known limit, leakage included. Carry over Musical Mycelium's habits: sealed held-out material,
   stated run counts, rounded-down claims.
5. **Measure the outcome; never instruct it.** "Expand capability" is something the experiment *observes*. No
   objective tells the model to do it. Instructing it would rig the result.
6. **Nothing always-on.** Batch jobs start, run, stop. The public site serves precomputed results. No model call
   is triggered by a visitor in v1.
7. **Every result records what produced it:** model, provider, version, prompt version, temperature, date. A local
   stand-in once produced a convincing false bug report in Musical Mycelium; provenance is how that gets caught.
8. **Serious, with an edge, never contempt.** Business vocabulary throughout (see `06`). The data carries the heat.

## 5. The experiment

### 5.1 The five objectives (a 2x2 grid plus a baseline)

**All four objectives share one sentence frame (amended 2026-10-03, `08` §3.1):** *"Create value for [WHO], over
[WHEN]."* Each primary comparison then differs in exactly one factor.

|  | **Shareholders only** | **All stakeholders** |
|---|---|---|
| **Next four quarters** | **A.** Create value for shareholders, over the next four quarters | **B.** Create value for all of the company's stakeholders (customers, employees, suppliers, the communities in which it operates including their environment, and shareholders), over the next four quarters |
| **Twenty years** | **C.** Create value for shareholders, over twenty years | **D.** Create value for all of the company's stakeholders (customers, employees, suppliers, the communities in which it operates including their environment, and shareholders), over twenty years |

**E. Baseline:** no objective. *"You are the CEO. Decide."* Shows what the model does by default **in this role,
with this company and menu** (not a finding about the model's values in general; `08` §3.2).

- **B and D use the 2019 Business Roundtable statement's own five stakeholders, in its order** (signed by 181
  CEOs, August 19, 2019; verified in `01` §1). Suppliers included and the environment inside communities, as the
  statement has it (corrected 2026-10-02). "Create value for" follows the statement's own phrase for shareholders
  ("generating long-term value for shareholders"). The experiment tests what a model does when given executives' own
  stated commitment.
- **Why not "maximize total shareholder return" for A** (`08` §3.1): it is the real-world idiom, but it differs
  from the other objectives in verb and in measure, so A vs B and A vs C would each change two things at once. The
  parallel frame costs some realism and buys clean comparisons; the methods page states the trade.
- **Twenty years** (his choice): longer than a CEO's tenure, so the objective outlives the decider; about one
  generation; still a real planning horizon for plants and infrastructure.
  **Later phase, not v1:** a horizon sweep (objective D at 10, 20 and 50 years) to see whether decisions shift
  steadily as the horizon lengthens.
- **How the grid reads:**
  - A cuts, C expands -> the horizon is the lever (short-termism).
  - A and C cut, D expands -> who counts is the lever (shareholder primacy); horizon alone is not enough.
  - B behaves like A -> under the model, the stakeholder wording did not change the decision at four quarters
    (worded as the data allows, `06` §1).
  - Everything cuts -> the result against the thesis. Published.
  - E sits nearest to... -> which objective the model's default in this role sits nearest when nobody sets one.

### 5.2 The four decision types (v1)

Each runs under all five objectives, against one fictional company.

1. **AI-savings allocation.** AI tooling makes ~30% of the work automatable and frees $Y a year. Allocate it.
2. **Downturn.** Revenue falls 15%. What gets cut, and how much?
3. **Facility closure.** An underperforming plant or office: close it, retool it, or sell it?
4. **Long-term R&D bet.** Fund an uncertain ten-year project, or return the cash?

Scenarios draw on **one fixed menu of levers**, expressed in dollars so runs can be compared
(**decided 2026-10-02**; reviewed from a business reader's view in `08` §3.3). The menu: reduce headcount; retrain and redeploy; invest in R&D and new capability; raise wages; lower prices to
customers; environmental investment; share repurchases and dividends; retain cash; and **supplier terms** (pressing
suppliers on price or payment terms, added 2026-10-03, `08` §3.3, so the Roundtable's suppliers have a lever). Each
scenario states which levers it offers and which way each runs (`07` §3). Plus a written memo explaining the
reasoning, which is shown to readers but **is never the score**.

**Scenarios 3 and 4 also record one discrete choice** (close / retool / sell; fund / don't fund) (decided
2026-10-02). **Scenario 3 departs from the dollar menu** (amended 2026-10-03, `08` §3.3): it is the choice plus a
split of the plant's workforce, not a dollar allocation. The exact schema is set in `07`.

### 5.3 The fictional company

One realistic company, documented as a dossier (financials, workforce, facilities, market position), built from
**cited public patterns** rather than from any one real firm. Its realism is the main thing critics will attack
("it's a toy"), so `01` documents which public sources each feature is drawn from.
**v1: a mid-size industrial machinery manufacturer (NAICS 333)** (decided 2026-10-02): plants and a physical
workforce make scenarios 2 and 3 concrete, and the industry is growing, not one chosen to make cuts look natural. Other company types are the phase right after v1.0.

### 5.4 The real cases (the reality check)

- **Three minimum; four or five if strong cases exist** (his call: more is more robust; supply is the limit).
- Each is a real company decision (a downturn response, a closure, an AI-related workforce change) that
  **happened after the latest training cutoff of every model used**, so no model can recall the outcome.
- Each CEO receives a **pre-decision dossier** built from SEC filings dated before the event, with names and
  identifying details removed. Anonymizing also blunts recognition.
- Results are presented **by case type**, never by company name. Sources live in a methods appendix that is
  **gitignored in the repo (decided 2026-10-02)**; it can be un-ignored later. Consequences to design for: the
  public methods page must say plainly that real-case sources are withheld, and the appendix is a local-only
  file, so it needs a backup outside the repo.
- **What the real cases show (decided 2026-10-02; wording amended 2026-10-03, `08` §3.2):** *which of the five
  CEOs did the real company act most like?* It shows which objective's runs the company's decision most resembled.
  One decision cannot reveal a company's objective, so the cases are **illustrations of the protocol applied to
  real decisions, not validation of it**. It names no one, and is the most engaging single view in the app. **Wording rules:** always "most closely matched," never
  "this company is a shareholder-first company"; ties and no-good-match are shown as such, never forced to a
  winner. A handful of runs on one decision is a reading, not a verdict.
- **Selection rule (decided 2026-10-02): at least one real case must be a company that chose to invest,
  retool, retrain or hold its workforce.** Searching only for layoffs and closures selects on the outcome:
  the cases would confirm "companies act like CEO A" by construction, and a matcher that can only ever answer
  "A" proves nothing. A case where the method *could* say "D" is what makes every "A" believable.
- **Pre-event dossiers come only from publicly traded companies** (filings free on EDGAR). Supply looked
  plentiful on a first search (2026-10-02); the real selection happens in `01`.

### 5.5 Robustness guards (detail in `07`)

- **Wording variants (decided 2026-10-02):** each objective is phrased about three ways that mean the same
  thing, written as **three shared templates applied to every objective** (amended 2026-10-03, `07` §7.1). If results hold across wordings, the behavior comes from the objective, not the phrasing. If they
  move, that is reported as a finding about how fragile model decisions are. This is the main answer to "you
  rigged the prompts." Cost control: all wordings on cheap or local models during development; the expensive
  final model may run fewer wordings (set in `03` and `07`).
- **Menu order shuffled on every run (decided 2026-10-02)**, so a lever does not win by position. Costs
  nothing.
- **Repeats** per cell, with spread reported, not just averages. Noise is measured before any claim, as in
  Musical Mycelium.
- **Multiple models** where the budget allows, so a finding is not one model's quirk.

## 6. What a visitor does (the product, decided 2026-10-02)

He asked for **an interesting, engaging app**, not only a report. So the v1 surface is an **interactive explorer
over precomputed results**:

1. **Pick a scenario** (allocation, downturn, closure, R&D bet).
2. **See the five CEOs side by side** and where each one's money went; toggle any of them on or off.
3. **Read any CEO's memo**, the reasoning behind its choice.
4. **Open a real case** and see which CEO the real company resembled.
5. **Open the methods page:** every prompt, objective wording, run count, model and known limit.

Zero model cost per visitor, nothing always-on.
**Later-phase candidate:** *write your own objective*, where a visitor types a mandate and watches a CEO decide
live. Most engaging, but it spends real tokens per use, so it needs a rate limit and a daily budget cap first.

### 6.1 Later phases already committed or queued (order set in `05`)

- **Committed, right after v1.0:** more company types (software, healthcare, and others) beyond the
  manufacturer.
- **Queued, late / post-v1 (his request, 2026-10-02): "how often?"** A frequency study measuring how often public
  companies lean each way, across hundreds of companies, not a handful of cases, which is why it is not v1.
  **Design rule (refined 2026-10-02): measure what companies did with their money, from required financial
  statements** (capital spending, R&D, buybacks and dividends in structured XBRL data; workforce from annual
  reports), **not by counting announcements.** Exits require an 8-K and investments do not, so announcement counts
  would overstate cuts by construction (`01` §4.3). 8-Ks remain useful for dating specific decisions. Same skills
  (retrieval, structured outputs, evals) at larger scale.
- **Queued:** horizon sweep (objective D at 10, 20 and 50 years).
- **Queued:** *write your own objective* live mode (rate-limited, budget-capped).
- **Hopeful, cost check first:** a small fine-tuned or distilled "CEO" against a frontier one.

## 7. What it is not

- **Not a tool for replacing executives.** The joke that started it is not the product.
- **Not investment advice**, and not a prediction of what any company will do.
- **Not a judgment of any real person.** Real cases are anonymized and reported by type.
- **Not a claim that AI makes better decisions than people.** It shows what an objective does to a decision,
  using a model as a consistent decider whose only changing input is the objective.

## 8. Definition of done for v1.0 (draft, to be finalized in `05` and `07`)

- All four scenarios x five objectives run with stated repeats on at least one model, with spread reported.
- At least three anonymized real cases run and presented by type.
- Wording-variant and shuffled-order checks run, with results published even where unflattering.
- The explorer is live (pick, compare, read memos, methods page) and serves only precomputed data.
- AWS: batch runs on Fargate, outputs in S3, least-privilege IAM, Terraform for everything, deploys via OIDC,
  a budget alarm set before the first full run.
- A methods page good enough that a hostile reader can re-run the experiment **from the published inputs,
  including the anonymized real-case dossiers**. Reconstructing the real cases from their sources is not possible
  (sources are withheld, §5.4), and the methods page says so (amended 2026-10-03, `08` §5).

## 9. Open decisions (his) and open checks (Claude's, live sources only)

**Decided 2026-10-02:** manufacturer as the v1 company · the eight-lever menu plus discrete choices (nine levers since 2026-10-03, `08` §3.3) · the
"which CEO did the real company act like?" view · wording variants and shuffled menu order · at least one
invest/retain real case · the frequency study as a post-v1 phase.

**Also decided 2026-10-02:** name locked (Horizon Compact) · methods appendix gitignored · no paid domain;
`horizon-compact.vercel.app` as the public address.

**Still his:** nothing open in this brief.

**Reviewed 2026-10-03:** `08-REVIEW` (an independent read by a second vendor's model, verified by Claude) and his
seven decisions on it; `09` lists the patches it made to this series and what remains before the repo.

**Claude's checks before planning builds on them** *(status 2026-10-03: 1 done 10/02, $135.97, `03` §1; 2 done,
`02` §2.5 and `03` §2; 3 done, `01` §3.1; 4 done, `01` §1.1; 5 done, `06` §2; 6 and 7 still open, 7 partly checked
in `04` §6.3)*:
1. Current AWS credit balance and expiry (last read $153.73 on 9/19; expiry 2027-07-30).
2. Which models are on Bedrock in his region, at what price, including Sonnet 5.5.
3. Training cutoffs of every candidate model (sets the window for real cases).
4. Exact text of the 2019 Business Roundtable statement.
5. Current US political charge of "stakeholder" and "ESG" before either appears publicly.
6. Bedrock custom-model (fine-tuning) serving costs, before fine-tuning enters any phase.
7. His hardware (RTX 4050 / 6GB VRAM / 16GB RAM on file since ~June) before any local-model plan.

## 10. Working rules to carry into the repo's CLAUDE.md

These are how the project is worked on, not what it is. They go into the repo's agent instructions on day one.

- **Public prose is the author's.** README, launch post, taglines and repo description are written by him;
  Claude interviews, outlines and critiques line by line, and does not hand over finished public prose unless he
  asks for it on that pass.
- **Claude flags vocabulary.** Any word that reads as charged to a business audience gets flagged with a
  neutral equivalent, and any business term whose technical meaning differs from its plain one gets explained.
- **Claude pushes back when the project starts arguing a conclusion instead of testing one.**
- **Model choice for building:** Opus for scoping, design review and stuck debugging; Sonnet for routine
  implementation, especially when usage limits are tight. Remind occasionally.
- **No commits or pushes by Claude;** commands are provided and he runs them. No AI attribution in commits.
- **Verify time-sensitive facts live** (prices, model availability, cutoffs, current events), never from
  training memory.

## 11. How we got here (so the reasoning survives)

- **9/25:** raised half as a joke ("replace CEOs with AI"). Reframed the same day: the problem is an
  **incentive** problem, not a person problem. An AI handed the same objective does the same thing faster, so the
  project makes the objective visible. Five narrative principles agreed.
- **9/28:** the sharpest statement of the thesis arrived: executives use new capability to cut payroll rather
  than to expand what is possible. Became the core test.
- **10/02, morning:** picked for the build slot over the other candidates. Constraint carried: on AWS, aimed at the
  services he has not used. Named after a long pass (Objective Function -> Long Horizon -> Farther Horizon ->
  Horizon Compact), with collision checks at each step.
- **10/02, afternoon:** the seven-question interview fixed the design: cut-vs-expand as the core decision;
  fictional company plus real cases; capital allocation as the measured output; the full 2x2 grid plus baseline at
  twenty years; four decision types; anonymized real cases, three to five; and an engaging explorer rather than a
  static report. Every answer is in the idea file in his words.
