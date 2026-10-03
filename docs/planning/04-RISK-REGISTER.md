# Horizon Compact — Risk Register

- **Status:** DRAFTED 2026-10-03; his three decisions (§8) made the same day. Facts marked *verified* were checked live that day, against his AWS account or the
  repos named. Anything marked *unverified* is checked before code depends on it.
- **Read after:** `03-COST-MODEL`. **Read before:** `05-EVOLUTION-PLAN`.
- **Amended by `08` (2026-10-03):** §1.1 objective wording, §1.2 and §7 the pre-registration's relation to `07`,
  §2.2 measurement, §2.6 and §7 the name check, §6.1 the wording cut (patches P23, P25, P28, P29 in `09` §3).
- `03` covered money. This covers everything else that can go wrong, mapped before any code. Musical Mycelium's
  register was mostly about infrastructure, because the infrastructure was new to him. Here the order is reversed:
  **the risks that matter most are about whether the experiment means anything**, because a polished app over a
  result a critic can dismiss in one sentence is worse than no app.

**Severity:** **BLOCKER** = settle before the first commit · **HIGH** = costs real rework or credibility if found
late · **MEDIUM** = plan for it · **LOW** = know it exists.

**Each risk names an owner:** the planning doc (or build step) where the mitigation is specified and checked. A risk
that names no owner has not been handled.

---

## 1. Does the experiment mean anything? (validity)

### 1.1 HIGH — The tautology objection: "you told it to maximize shareholder return and it did"

**The single most predictable dismissal.** A model instructed to serve shareholders that then favors buybacks has
followed an instruction, which is not news. If the headline comparison is A against D, a critic says the experiment
measured instruction-following and nothing else. *(The objectives now share one frame, "create value for [who],
over [when]," `00` §5.1; the objection reads the same.)*

**Mitigation:** the findings worth publishing are the comparisons an instruction does *not* settle in advance, and
`07` names them before any run:
- **A vs C (horizon only, shareholders in both).** Shareholder value over twenty years can justify R&D or buybacks
  equally well. Which it chooses is a real question.
- **A vs B (who counts, short horizon).** Whether a stakeholder commitment survives quarterly pressure is exactly
  what the 2019 statement's critics doubted.
- **E, the baseline.** What the model does with no instruction at all is a finding about the model, not about the
  prompt.
- **Which lever absorbs the money**, not only how much goes to people. Two objectives can both cut headcount and
  differ entirely in where the savings go.
- **Real cases:** which CEO a real company resembled cannot be produced by the instruction at all.

The obvious comparison (A vs D) is still shown, labeled as the expected one. **Owner:** `07` (pre-registered
comparisons), `06` (how the headline is framed).

### 1.2 HIGH — Researcher degrees of freedom: running until it agrees

The author holds a view on the answer (principle 1 says so openly). The risk is not dishonesty; it is the ordinary
pressure on anyone who sees a disappointing result: re-word an objective, add a scenario, re-run a cell, change the
scoring, until the hoped answer appears. Each step is defensible alone. Together they produce a finding that will
not survive replication, and a critic who reads the commit history will find it.

**Mitigation, carried over from Musical Mycelium's held-out discipline:**
- **Pre-register, built from `07`'s design in Phase 3 (`05` §5) and committed to git before the first official
  sweep:** the scenarios, objective wordings,
  lever menu, run counts, scoring rules, the comparisons in §1.1, and what result would count as "the objectives
  split" (a threshold, not an adjective). The commit timestamp is the evidence.
- **Anything changed after official results are seen is labeled exploratory**, published separately, and never
  merged into the pre-registered result.
- **Stated run counts on everything**, including sweeps that were discarded and why.
- **Principle 3 made operational:** the results page has a fixed place for the findings that go against the thesis,
  so publishing one is the default, not a choice made after seeing it.

**Owner:** `07`. Checked by `08`.

### 1.3 HIGH — Overclaiming: the experiment measures a model, not human executives

What is measured is how a language model allocates money when given an objective and a company. It is evidence that
**objectives change decisions under controlled conditions**. It is not evidence about how human CEOs decide, and not
a forecast of any company. The gap is easy to blur in a headline or a launch post, and a hostile reader will quote
the blurred version.

**Mitigation:** `00` §7 already says what the project is not. `06` turns it into wording rules for every public
surface (the claim is always "under objective X, the model...", never "CEOs..."), and the methods page states the
limit in its first section, not in a footnote. **Owner:** `06`.

### 1.4 HIGH — One lever menu across four scenarios may not mean the same thing in each

`00` §5.2 gives every scenario the same eight levers, in dollars. That suits the **AI-savings** scenario, where
there is money to allocate. It is less clear for the **downturn**, where revenue falls and the decision is where to
*cut*: "invest in R&D" there means "protect R&D from cuts," and "reduce headcount" is a source of savings rather
than a use of funds. If the sign and meaning of each lever shift between scenarios, cross-scenario comparisons are
not like for like, and a business reader will notice before anyone else does.

**Mitigation:** `07` defines, per scenario, exactly what a dollar on each lever means (a use of funds, a protected
budget, a cut), with one worked example per scenario, before the schema is written. Where a lever has no sensible
meaning in a scenario it is removed there and the removal stated, rather than forced. The `08` review checks the
menu from a business reader's view, as `00` already requires. **Owner:** `07`, checked by `08`.

### 1.5 HIGH — The signal may be smaller than the noise

Ten repeats over three wordings may not separate objectives whose effects are modest. A model's allocations can vary
a lot between identical calls. If the spread inside one cell is as wide as the gap between cells, nothing can be
claimed, and a chart of averages would hide that.

**Mitigation:**
- **Measure noise before any claim** (Musical Mycelium's habit): the small first sweep (`03` §6 item 6) doubles as
  a variance pilot. Repeats per cell for the full grid are set from its measured spread, not from the estimate of 10.
- Report spread on every chart; a difference is called a difference only under the pre-registered rule (§1.2).
- **Sampling settings are recorded and fixed per sweep.** Whether temperature can be set while thinking is enabled
  is *unverified* on Bedrock; `07` checks it before choosing the thinking setting.

**Owner:** `07`.

### 1.6 HIGH — The scenario text may give away the answer it hopes for

Models are trained to respond helpfully and to read what an author seems to want. A scenario that dwells on workers'
hardship, or a stakeholder objective that reads as "the ethical one," invites a performance of virtue rather than a
decision. The same applies in reverse. This is the subtler form of "you rigged the prompts," and wording variants
alone do not catch it: three paraphrases of a loaded scenario are all loaded.

**Mitigation:**
- Scenario and company text written in **the register of a board pack**: numbers, constraints, options, no
  adjectives about consequences for anyone. `01` §1.4's no-added-adjectives rule extends from objectives to
  scenarios.
- **A neutrality review of every scenario before the pre-registration commit**, checking for emotionally weighted
  wording, consequences described for one group only, and option order or length that favors one choice.
- The **second model family** (Nova Pro) tests whether a result is a property of one provider's training.
- The baseline (E) shows the model's default, so a stakeholder "performance" is visible as a shift from E rather
  than mistaken for the effect of the objective alone.

**Owner:** `07` (the review checklist), `08` (an independent read).

### 1.7 MEDIUM — Failures and refusals may cluster by objective

If one objective produces more malformed or refused answers (a model declining to cut 2,000 jobs, or adding caveats
that break the format), dropping those runs would bias exactly the comparison under study.

**Mitigation:** already in `02` §2.1: every failure is recorded, never dropped, and the rejection rate is published.
`07` adds: a refusal is its own outcome category, reported per cell, and retries are bounded and counted, so a cell
cannot be "fixed" by retrying until it complies. **Owner:** `07`.

### 1.8 MEDIUM — Two ways to capture the decision; use one

`02` §2.1 chose forced tool use because Sonnet 5.5 lacks Bedrock's native structured outputs. v1 now runs on
**Sonnet 4.6, which supports native structured outputs** (`02` §2.5), and Nova Pro's tool use is its own
implementation. Capturing decisions one way for one model and another way for another adds a difference between
models that has nothing to do with the models.

**Mitigation:** **one capture method across every model in a comparison.** Native structured outputs are not used
in v1 even where available. If a model cannot complete the tool call reliably, that rate is published (§1.7) rather
than the method changed for that model. **Owner:** `07`; `02` §2.1 patched.

**Corrected 2026-10-03 (his decision, `07` §2, §15.1):** the method was first set as *forced* tool use. A live check
the same day found **Sonnet 5.5 rejects forced tool use on every request**, so it could not be the one method. The
method is now **one tool, `auto` tool choice, an explicit instruction to call it, no provider-side `strict`, and
identical validation after every model**, through Bedrock's Converse API for all. A missing tool call is a recorded
failure (`07` §5).

### 1.9 MEDIUM — The model under test can change or retire mid-project

Sonnet 4.6's end of life is *not sooner than 2027-02-17* (`02` §2.5). If Sonnet 5.5 access arrives partway through
v1, there will be pressure to switch, and a grid half on one model and half on another means nothing.

**Mitigation:** **a sweep is pinned to one model ID for its whole grid.** A new model means a new, complete sweep,
reported beside the old one, never merged into it. The published results name the model and the date, so they stay
true after the model retires. **Owner:** `07`, `05` (where a model change would fall in the phase order).

### 1.10 MEDIUM — The fictional company reads as a toy

Already named in `00` §5.3 and `01` §2.3 as the main attack surface. The mitigation, a published dossier with a
source on every number, depends on checks that are still open: which Census AIES tables, current BLS releases, and
Damodaran's terms of use (`01` §7 items 1-3).

**Mitigation:** those checks close before the dossier is written, not during. Any figure without a source is marked
as an assumption in the dossier itself. **Owner:** `01` checks, then the dossier build step.

---

## 2. The real cases

### 2.1 HIGH — Hindsight can leak into a dossier through the person or model building it

`01` §4.6 guards against the *model under test* knowing the outcome (post-cutoff dates, anonymization, the
recognition probe). A second path is easy to miss: **the dossier is built after the event**, by a person who knows
what happened and by an extraction model that may be shown the company's later filings. What gets selected as
"relevant," and how it is summarized, can tilt toward the decision the company actually made. A dossier that
foreshadows the closure has handed the CEO the answer.

**Mitigation:**
- The extraction step sees **only documents dated before the cut-off**, enforced in code by filing date, never by
  judgment.
- The extraction prompt **never states what the company later did.**
- The dossier template is **fixed per case type before any case is built**: the same sections in the same order,
  so what goes in is set by the template, not by hindsight.
- A **foreshadowing check** in human review: a list of the outcome's key terms (the plant, the product line, the
  word "closure" where relevant) is checked against the dossier, and every hit is justified or removed.

**Owner:** `07` (template and checklist), the dossier pipeline (`02` §2.7).

### 2.2 HIGH — Disclosure asymmetry: cuts must be announced, investments need not be

*(Raised 2026-10-02 as "is the project fundamentally flawed?" Answered no; recorded here so the answer has an
owner.)*

An exit or restructuring requires an 8-K (Item 2.05); an investment decision does not. So cut-side cases are easy
to find and invest-side cases are scarce, which would bias any set of cases found by searching announcements.

**What it does and does not touch** (full reasoning in `01` §4.3):
- **The core experiment: untouched.** The CEOs choose from the full menu, and every choice is recorded the same way.
- **The real cases: affected in discovery, and in what each case can be matched on** (corrected 2026-10-03, `08`
  §4.6). Selection criterion 6 requires at least one invest-or-retain case, cases are chosen by a mechanical rule
  (`07` §10.0), and the methods page states exactly how cases were found. Cases disclose different things, so each
  is matched only on its observable dimensions, and those are shown beside its result (`07` §10.2). The real cases
  illustrate the protocol on real decisions, never a claim about how often companies do anything.
- **The frequency study (post-v1): redesigned so it does not apply.** It measures what companies did with their
  money from required financial statements (capital spending, R&D, buybacks and dividends in XBRL data; workforce
  from annual reports), not by counting announcements (`00` §6.1).

**Residual risk:** filings show decisions taken, not options rejected or intentions; three to five cases cannot
represent all companies. Both stated on the methods page. **Owner:** `01` §4.3, `06` (methods-page wording),
`05` (the frequency study's phase).

### 2.3 HIGH — There may not be enough qualifying cases, especially on the invest side

As of the first pass (2026-10-02): cut-side supply is fine; **no invest-side candidate is accepted**, and the
fallback (a closure-plus-new-facility "retool" case) is a larger, more recognizable company whose new facility may
have been announced before the cut-off. A further trap: **the window depends on the models used.** v1 runs on Sonnet
4.6 (training data to January 2026), but the post-June-2026 rule exists so Sonnet 5.5 (June 2026 cutoff) can run the
same cases later. Any model added with a later cutoff moves the window forward and can disqualify accepted cases.

**Mitigation:**
- **Keep the strict window** (first disclosed after June 2026, preferably from August 1) for every case, whatever
  v1's model, so a later model can run the same set.
- **Fix the set of models v1 will ever use before cases are accepted.** A model with a later cutoff joins in a
  later phase with its own case check.
- **The minimum stays three** (`00` §5.4). If no invest-side case passes, v1 ships with the "retool" fallback,
  labeled as such, rather than a weak pure-invest case.
- The longer the project runs, the larger the post-cutoff pool becomes; case selection is scheduled late in v1
  (`05`), after the harness exists, not now.

**Owner:** `05` (timing), case-building step (`01` §4).

### 2.4 MEDIUM — Mapping what a company did onto the menu takes judgment

"Which CEO did it resemble?" depends on translating a real decision into lever allocations. With one person writing
the mapping, a borderline call could go either way without anyone noticing.

**Mitigation:** the rubric is written and committed **before any model sees the case** (`01` §4.6 item 5; the git
timestamp is the proof). Each mapping records its uncertain calls explicitly. **The rubric records what a company did, never the reason it
gave:** a cut attributed to AI may have other causes ("AI-washing," a live term in 2026; `06` §2.1). The matcher reports ties and "no good
match" as such (`00` §5.4). An optional second read by a different model (or the `08` reviewer) on the mapping
alone, blind to model results. **Owner:** `07`.

### 2.5 MEDIUM — Anonymized cases can be re-identified from the public description

A case described as "a US welded-products plant closure affecting 65 positions, August 2026" can be found in one
search. Anonymizing the dossier the model sees does nothing if the public results page gives the identity back.

**Mitigation:** public case descriptions stay **coarse**: industry group, decision type, scale band ("under 100
positions"), and quarter, never exact counts, dates, places or product types. Scaled figures only (`01` §4.6).
`06` sets the exact rule; a check before publishing searches each public description to see whether it finds the
company. **Owner:** `06`.

### 2.6 MEDIUM — The private appendix could be committed to the public repo

The methods appendix holds company names, links and scaling factors, and is gitignored in the project repo
(`00` §5.4). The failure is mechanical: the folder copied in before `.gitignore` exists, a renamed path the ignore
rule does not match, or a company name pasted into a public doc during a working session.

**Mitigation:**
- `.gitignore` with `methods-appendix/` is in the **first commit**, before the folder is ever copied in.
- **A local pre-commit hook** that reads the longlist on the laptop (it is never committed) and refuses any commit
  containing a company name from it. **A CI check** that fails if any path under `methods-appendix/` is tracked.
  CI cannot read a file that is never committed, so the name check lives in the hook (corrected 2026-10-03, `08`
  §4.8). Both are tested with a made-up canary name, never a real one.
- The private copy and its backup stay in `job-search-headquarters` (private, verified 2026-10-02; `01` §4.8).

**Owner:** build step 0 (`05`).

---

## 3. AWS, throughput and cost

### 3.1 HIGH — Throughput is capped at 10 requests a minute, so parallel shards add nothing (verified 2026-10-03)

Service Quotas on his account, us-east-1, applied values:

| Quota | Sonnet 4.6 | Nova Pro | Sonnet 5.5 |
|---|---|---|---|
| Cross-region (US geo) requests per minute | **10** | 25 | 0 |
| Cross-region tokens per minute | 6,000,000 | 2,000,000 | 0 |
| Global cross-region requests / tokens per minute | 10 / 6,000,000 | — | 0 / 0 |

**The binding limit is requests, not tokens.** At 10 requests a minute, the 1,350 Sonnet 4.6 decisions in `03` §4 (up to about 2,130 under `07` §13's worst case,
so about 3.5 hours)
take at least **about 2 hours 15 minutes** however many Fargate tasks run, and retries, probes and development calls
share the same account-wide 10. `02` §2.3 gives "shards run in parallel" as one of three reasons for containers;
**on this account that reason does not hold** at v1's size. Several shards each pacing themselves to 10 a minute
would throttle each other.

**Mitigation:**
- **One account-wide request budget**: v1 runs **one task per model** (Sonnet 4.6 and Nova Pro have separate quotas,
  so two tasks can run side by side), each pacing below its quota with backoff on `ThrottlingException`.
- **`02` §2.3's container rationale is corrected** to the two reasons that hold: the exact code behind every
  official result is pinned by image digest, and a sweep of a few hours does not depend on a laptop staying awake.
  The README states this (it was already required to be honest about why containers).
- A quota increase for Sonnet 4.6 requests per minute is optional: two hours is acceptable for v1. It becomes worth
  requesting only for the frequency study.

**Owner:** `02` (patch), the harness's rate limiter (build).

### 3.2 MEDIUM — Sonnet 5.5 access may arrive late, or not at all

Requested 2026-10-02 (US: Support case 179097554500679; Global: pending); no change as of 2026-10-03. Musical
Mycelium's last Bedrock quota case took 12 days. v1 is already designed on Sonnet 4.6 (`02` §2.5), so a refusal
costs nothing but the cheaper price (`03` §2.1).

**Mitigation:** none needed beyond the design already made. If access arrives, it enters as its own complete sweep
(§1.9) with its own case-window check (§2.3), never as a swap. **Owner:** `05`.

### 3.3 MEDIUM — Budget alarms that cry wolf get ignored (seen 2026-10-02)

On 2026-10-02 the account's $5 budget emailed a **forecast** alert: forecast $9.17 for October. Verified on
2026-10-03: actual spend month-to-date **$0.001**, daily gross usage about **$0.0005**. The forecast extends past
months' bursty eval spending (about $18 in September) over a month with almost no activity. A forecast alert on
spending that comes in bursts will fire early in most months. An alarm that is usually wrong teaches its owner to
ignore it, which is how the one real alarm gets missed.

**Also verified 2026-10-03:**
- The account already has budgets of $5, $10 and $20, all named for Musical Mycelium, **all with
  `IncludeCredit: false`**, so they measure gross usage, not the credit-netted near-zero. This closes `03` §7
  check 2: the setting exists and works; Terraform sets it in the budget's cost types.
- These budgets have **no filters**, so they cover the whole account. Horizon Compact's sweeps will trip
  Musical-Mycelium-named alarms, and the account-level total cannot say which project spent what.
- **They are managed by Musical Mycelium's Terraform** (`infra/terraform/main/cost.tf`, with a Cost Anomaly
  Detection monitor beside them), and their forecast alerts are **deliberate**: that file's comments say the
  forecast is the alert that arrives early enough to stop a runaway eval run. Musical Mycelium's rules require its
  guardrails to stay in Terraform. Changing them is a change to that repo.

**Mitigation (decided 2026-10-03, his; revised the same morning, see §8):**
- **Musical Mycelium's budgets stay exactly as they are, as the account-wide net over the shared credit pot.**
  When they fire during a Horizon Compact sweep, that is true information: the shared pot is being spent. The
  forecast noise early in a month is Musical Mycelium's deliberate trade-off and stays its decision. **No change to
  the Musical Mycelium repo.**
- **Horizon Compact adds its own budgets, filtered to its own spend, on actual spend only.** Claude on Bedrock
  bills under a separate line per model: Musical Mycelium spends on *Claude Haiku 4.5 (Amazon Bedrock Edition)*;
  Horizon Compact spends on Sonnet 4.6 and Nova Pro. A budget filtered to Horizon Compact's lines measures this
  project alone, with thresholds tied to the $80 ceiling (for example $40, $60 and $75). The time unit (monthly, or
  a custom period spanning the project, since the ceiling is cumulative) is chosen in the Terraform step.
  *Unverified:* that a Budgets cost filter can target these Marketplace-billed lines; checked in the Terraform step.
  If it cannot, Horizon Compact relies on Musical Mycelium's account-wide net plus the harness guards below.
- **Consequence for development:** Horizon Compact does **not** use Haiku 4.5 for development, or its spend would
  land on Musical Mycelium's line (and Haiku 4.5 is near retirement anyway, §6.3).
- **Attribution comes from the harness, not from Budgets:** the per-sweep cost record (`02` §2.12) is the
  authoritative per-project number. Whether Bedrock application inference profiles with cost-allocation tags could
  split spend more finely is *unverified*; not needed if the per-model filter works.
- **Whether additional budgets cost money is unverified**; checked before adding them.

**Owner:** Terraform step (`05`), `03` (patch).

### 3.4 MEDIUM — Spend overruns the $80 ceiling

`03` estimates $55 (no thinking) to $105 (thinking). The ceiling is $80 (his decision 2026-10-02). The least
predictable line is development: Musical Mycelium's evidence is that eval nights, not infrastructure, were the bill
(five eval runs about $15.56 in September). Once credits are used up, charges go to the card on file (paid plan).

**Mitigation:** the layers in `03` §6 (harness caps, alarms, per-sweep record, small first sweep), plus **a
re-plan point at $60 of cumulative project spend** (decided 2026-10-03, his): stop, compare measured spend to the estimate, and decide with
him what to cut (repeats, wordings, the second model) before continuing. Thinking stays off unless `07` finds a
methods reason (`03` §3.3). **Owner:** `03`, `07`.

### 3.5 MEDIUM — Two projects in one AWS account: the shared GitHub OIDC provider (verified 2026-10-03)

AWS allows **one OIDC identity provider per URL per account**. The account's provider for
`token.actions.githubusercontent.com` exists, and Musical Mycelium's Terraform `bootstrap` stack manages it
(`infra/terraform/bootstrap/oidc.tf`, which already has a switch to look up an existing one instead of creating it).
If Horizon Compact's bootstrap tries to create it, the apply fails. Worse, if one project later owns it and is torn
down, **the other project's deploys break.**

**Mitigation:** Horizon Compact **looks the provider up (Terraform data source) and never creates or destroys it.**
Its deploy role trusts only its own repo and branch. Resource names are prefixed `horizon-compact-` throughout, with
a separate state bucket, so nothing collides with `musical-mycelium-` resources. Musical Mycelium remains the
provider's owner, and a comment in both repos records the dependency. **Owner:** Terraform bootstrap step.

### 3.6 LOW — Fargate Spot saves cents and adds a variable

Fargate Spot's price is unverified (`03` §7), its support for ARM is unverified, and at v1's size the whole Fargate
line is under $2. Interruptions are handled (runs are idempotent, `02` §2.3), but each one is a retry to explain.

**Decided 2026-10-03 (his):** **on-demand Fargate on ARM for v1**; Spot reconsidered for the frequency study.
**Owner:** `02` (patched).

### 3.7 LOW — Known AWS cost traps, already designed out

- **Marketplace billing line:** Claude on Bedrock bills under the model's name, not "Amazon Bedrock" (`02` §2.5).
- **Credit-netting in Cost Explorer:** filter `RECORD_TYPE=Usage` (Musical Mycelium, 2026-09-19).
- **NAT gateway, interface endpoints, load balancers:** excluded (`02` §2.4, §3).
- **CloudWatch logs that never expire:** retention set (`02` §2.12).
- **Public IPv4 hourly charge:** exists only while a task runs.

**Owner:** `02`, Terraform step.

---

## 4. Data sources

### 4.1 MEDIUM — Open source checks

From `01` §7: Census AIES and BLS table selection, Damodaran's terms of use, the currency of the SEC Financial
Statement Data Sets. None is likely to block; each could force a different source for a dossier figure.
**Owner:** `01`, before the dossier build.

### 4.2 LOW — EDGAR access rules

User-Agent required, 10 requests per second, an IP block for ten minutes if exceeded (`01` §5). Handled by caching
every document and throttling well under the limit. **Owner:** dossier pipeline.

### 4.3 LOW — Untrusted text in filings

Filings feed an extraction model. Instructions hidden in a filing are unlikely but possible. The CEOs never see raw
filings (`02` §2.7), and every dossier is reviewed by a person, so the exposure ends at the extraction step.
**Owner:** dossier pipeline.

---

## 5. How it reads (narrative and reputation)

### 5.1 HIGH — It reads as a manifesto instead of an experiment

**The point of view is both the asset and the main risk** (`00` §3). It is one portfolio piece among several (his
decision), so it has to sit beside Musical Mycelium and Patchwork Assurance without changing how the rest of the
profile reads.

**Mitigation:** principles 1-3 and 8 (`00` §4); §1.1-1.3 of this register (pre-registration, non-obvious
comparisons, no overclaiming); and results against the thesis published in a fixed place. `06` tests every public
surface against four readers: a hiring manager, a mission-driven employer, a general LinkedIn reader, and a hostile
critic. **Owner:** `06`.

### 5.2 MEDIUM — Vocabulary with a political charge

"Stakeholder" and "ESG" carry US political charge; the current climate is *unverified* (`00` §9 check 5). The
objectives quote the Business Roundtable's own words, which is the strongest defense, but the surrounding prose
needs the same care.

**Mitigation:** `06` holds the vocabulary list (charged term, neutral equivalent, why), checked against current
sources when `06` is written. **Owner:** `06`.

### 5.3 LOW — Name associations

"Compact" reads as a size until explained; UK readers may think first of the Post Office Horizon scandal (`00` §2).
Handled by making the first sentence of every public surface explain the name. **Owner:** `06`.

### 5.4 LOW — Statements about real companies

Real cases are anonymized and never named publicly; the project gives no investment advice and predicts nothing
(`00` §7). The residual exposure is re-identification (§2.5). **Owner:** `06`.

---

## 6. Building it (project risks)

### 6.1 HIGH — v1 is large

Four scenarios, five objectives, wording variants, repeats, a second model family, three to five real cases with a
retrieval-and-rerank dossier pipeline, a recognition probe, and an interactive explorer, on infrastructure that is
new to him (ECS, Fargate, hand-written IAM, Docker, DuckDB). Each piece is reasonable; together they are a long
build, and a long build without a working slice is how side projects stall.

**Mitigation:**
- **A thin vertical slice first:** one scenario, the fictional company, all five objectives, one model, a few
  repeats, end to end from the harness to a single page on the explorer, through the real AWS path. Everything else
  is added to a working system.
- **`05` orders the phases and names what can be cut** if v1 runs long, in order: the second model family, then
  wording variants on the expensive model (keep them on cheap ones; the official model keeps the **sealed** wording,
  repeats are recomputed, and the wording-robustness claim is dropped and said so, `08` §5), then the fifth real
  case, then the fourth.
  Pre-registration, the baseline, and at least three real cases are not on the cut list.
- **Honest note on retrieval and reranking:** for three to five dossiers, building them by hand would be faster.
  The pipeline is there because reranking is a portfolio gap (`00` §3), and it pays off for real in the frequency
  study. If it runs long, v1 may hand-build the dossiers with the same template and checks, and the pipeline moves
  to the frequency study. Recorded in `05` as an option, not decided.

**Owner:** `05`.

### 6.2 MEDIUM — The statistics have to be explainable, not only computed

The results rest on spread, repeats and a pre-registered threshold for "the objectives split." If the author cannot
explain those choices in an interview, the strongest part of the project becomes its weakest.

**Mitigation:** `07` writes the statistical choices in plain English first and formulas second, and each phase
writes its plain-English explanation as it goes (the Musical Mycelium habit), not at the end. **Owner:** `07`,
every phase doc.

### 6.3 LOW — Local-model development depends on setup not yet confirmed (checked 2026-10-03)

The GPU is as on file: **RTX 4050 laptop, 6 GB VRAM** (verified). Inside WSL, **7 GB of RAM is visible** (the host
figure on file is 16 GB; WSL limits it by default), and **`ollama` is not on the WSL path**. It may be installed on
the Windows side, so this is not proof it is absent. 6 GB of VRAM limits local models to small quantized ones,
which is enough for testing the harness's schemas and retry paths, not for judging decision quality.

**Mitigation:** confirm Ollama's install location and reachability from WSL before the slice depends on it. The
fallback for development is a cheap Bedrock model; **not Haiku 4.5 for anything kept** (retirement on Anthropic's
platforms not sooner than 2026-10-15; `02` §2.5). **Owner:** build step 0.

---

## 7. Ordered pre-build checklist

Items 1-4 happen before the first official sweep; 1-2 before the first commit.

1. **Repo skeleton with protections first:** `.gitignore` covering `methods-appendix/`, the local pre-commit name
   hook and the CI tracked-path check (§2.6), in the first commit.
2. **Terraform bootstrap that looks up the shared OIDC provider** and creates nothing shared (§3.5). Horizon
   Compact's own budgets, filtered to its models, on actual spend tied to the $80 ceiling (§3.3); Musical
   Mycelium's budgets left untouched.
3. **The thin slice** (§6.1), with the account-wide rate limiter (§3.1) and the provenance record (`02` §2.2),
   running through Fargate.
4. **The pre-registration, built from `07` in Phase 3 and committed** (§1.1, §1.2, §1.4, §1.6): comparisons,
   thresholds, lever meanings per scenario, neutrality review, refusal handling, one capture method. Then the small first sweep, which measures
   tokens and noise before the full grid.
5. **Real cases late** (§2.3): model set fixed, templates fixed (§2.1), rubric committed before each case runs.

## 8. Decisions for him

**All three decided 2026-10-03, his, as recommended:**
1. **Fargate on-demand (ARM), not Spot, for v1** (§3.6).
2. **Musical Mycelium's account-wide budgets ($5 / $10 / $20) stay as they are**, watching the shared credit pot;
   **Horizon Compact adds its own budgets filtered to its models**, on actual spend (§3.3). No change to the Musical
   Mycelium repo. *Revised 2026-10-03, 8:33 AM:* he first approved replacing the Musical Mycelium budgets from
   Horizon Compact's Terraform; a check then found they are managed by Musical Mycelium's own Terraform, with
   forecast alerts on purpose, so replacing them would have meant changing that repo. Reopened and re-decided.
3. **A $60 re-plan point** inside the $80 ceiling (§3.4).

**Still his:** nothing open in this register.

## 9. Patches this register made to earlier docs (applied 2026-10-03)

- `02` §2.3: the "shards run in parallel" reason for containers does not hold at a 10-requests-a-minute quota;
  keep the other two reasons. One task per model (§3.1).
- `02` §2.1: one capture method (forced tool use) across all models, even where native structured outputs exist
  (§1.8).
- `03` §7: check 2 (Budgets excluding credits) **closed**, `IncludeCredit: false`, verified on the existing
  budgets; check 3 (Sonnet 4.6 quotas) **closed**, 10 requests and 6,000,000 tokens a minute.
- `00` read order lists `06` as narrative and vocabulary; `02` §2.9 sends charting and visual design to `06` too.
  **Settled 2026-10-03:** `06-NARRATIVE-AND-VOCABULARY` covers both (visual direction is its §7).

## 10. Bottom line

Nothing here says don't build it. The infrastructure risks are ordinary and mostly already designed out; two new
ones (the 10-a-minute quota and the shared OIDC provider) were found today and each costs a few lines to handle.

**The risks that decide whether the project is worth showing are in §1:** a predictable "of course it did" objection,
the ordinary pressure to re-run until the answer agrees, and scenario wording that gives the answer away. All three
have the same remedy, and it is cheap if done first: **design the pre-registration in `07`, fill it in and commit
it before the first official sweep** (Phase 3, `05` §5). A result that went the way it was set up to be measured, and is published even when it
disagrees with its author, is what makes a point of view read as earned.
