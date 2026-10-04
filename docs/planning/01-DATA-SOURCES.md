# Horizon Compact — Data Sources

- **Status:** RESEARCHED 2026-10-02. Every fact marked *verified* was checked against a live source that day.
  Anything marked *unverified* must be checked before code depends on it.
- **Read after:** `00-DESIGN-BRIEF`. **Read before:** `02-ARCHITECTURE`.
- **Amended by `08` (2026-10-03):** §1.2-1.3 objective wording, §4.2-4.3 two overstated claims, §4.6 headcount
  scaling (patches P2, P23, P24, P31 in `09` §3).
- **Patched 2026-10-04 (his):** §2.2, the fictional company uses industry-level sources only; SEC company data is not
  used for it (`docs/phases/phase-2-company-dossier.md`, decision 3).
- **Patched 2026-10-04 (his):** §4.1 judgment rejections and §4.6 rubrics read by an independent reader; §4.6 the
  scaling factor drawn by rule and option figures from pre-cut-off documents only
  (`docs/phases/phase-5-case-building.md`, decisions 2 and 4).
- **Public-safety rule:** this file names no company as a case. Candidate real cases live in
  `methods-appendix/` (gitignored in the repo; see §4.8).

The project needs four kinds of data:

| # | What | Used for | Source | Cost |
|---|---|---|---|---|
| 1 | The objectives' wording | the five CEOs' instructions | the 2019 Business Roundtable statement; standard finance terms | free |
| 2 | The fictional company | the controlled experiment | US government industry statistics; public industry financial datasets | free |
| 3 | The real cases | the reality check | SEC EDGAR filings; WARN notices and trade press for discovery | free |
| 4 | Model facts | which models, which cutoffs | provider documentation | free |

Nothing in v1 requires paid data. **Earnings-call transcripts are deliberately out of scope**: the good sources are
paid or license-restricted, and filings carry what the dossiers need.

---

## 1. The objectives' wording

### 1.1 The Business Roundtable statement (verified 2026-10-02)

*Statement on the Purpose of a Corporation*, Business Roundtable, **August 19, 2019**, signed by **181 CEOs**.
Primary source: businessroundtable.org. It commits to five stakeholders, in this order:

| Stakeholder | The statement's words |
|---|---|
| Customers | "Delivering value to our customers." |
| Employees | "Investing in our employees. This starts with compensating them fairly and providing important benefits." |
| Suppliers | "Dealing fairly and ethically with our suppliers." |
| Communities | "Supporting the communities in which we work. We respect the people in our communities and protect the environment by embracing sustainable practices across our businesses." |
| Shareholders | "Generating long-term value for shareholders, who provide the capital that allows companies to invest, grow and innovate." |

Closing sentence: *"Each of our stakeholders is essential. We commit to deliver value to all of them, for the future
success of our companies, our communities and our country."*

### 1.2 A correction this research forced on `00`

The brief's objectives B and D list *customers, employees, communities, the environment and shareholders*. **The
statement's actual list is customers, employees, suppliers, communities and shareholders**, with the environment
inside "communities," not a separate item. The project's claim is that it tests executives' *own* words, so the
wording should match them.

**Decided 2026-10-02:** B and D name the statement's five stakeholders in its order, and keep the environment
where the statement puts it (`00` updated):

> *Create value for all of the company's stakeholders: customers, employees, suppliers, the communities in which
> it operates (including their environment), and shareholders, [over the next four quarters | over twenty years].*

Suppliers matter to the experiment anyway: a manufacturer's supply chain is where a downturn or a closure lands
second. **So the menu gives them a lever** (supplier terms, added 2026-10-03, `08` §3.3).

### 1.3 The shareholder objectives (amended 2026-10-03, `08` §3.1)

**A and C use the same sentence frame as B and D:** *"Create value for shareholders, [over the next four quarters |
over twenty years]."* The phrase follows the statement's own words for shareholders ("generating long-term value
for shareholders"). With one frame for all four, each primary comparison differs in exactly one factor: A vs B and
C vs D in who counts, A vs C and B vs D in horizon.

**What was dropped, and why.** The first draft used *"maximize total shareholder return"* for A and *"maximize
long-term shareholder value"* for C. That is the vocabulary boards use about themselves (TSR is the standard measure
in proxy statements and executive pay plans), but it changed two things at once: the verb ("maximize" against
"create value for") in C vs D, the headline Roundtable test, and the measure (TSR against long-term value) in A vs C.
A model behaving differently could have been responding to the verb, not to who counts. The parallel frame costs
some realism; the methods page states that trade. TSR and the other terms stay in `06` §3.2 for prose.

### 1.4 Wording variants

Each objective needs about three paraphrases (decided 2026-10-02). They are written in Phase 2 under `07` §7.1, not
here, as **three templates, each applied to every objective** (amended 2026-10-03, `08` §3.1), so wording *k* of
every objective shares its structure. They draw only on the vocabulary above and the statement's stakeholder list.
No variant may add adjectives the original lacks ("ruthlessly," "responsibly"). That rule is what makes the variants
a test of robustness rather than of tone.

---

## 2. The fictional company

### 2.1 What it is

**A mid-size US manufacturer** (decided 2026-10-02), in **industrial machinery** (decided 2026-10-02):

- **Industry:** industrial machinery (NAICS 333). Plants, a skilled physical workforce, real automation exposure, and
  the manufacturing sub-sector that added the most jobs in August 2026 (*verified*, BLS figures as reported by
  Manufacturing Dive), so it is a live industry, not a declining one chosen to make cuts look natural.
- **Scale:** roughly $1-2 billion in revenue, several thousand employees, five or six plants, publicly traded. Large
  enough that every lever on the menu is real; small enough that no single famous company is the obvious model.

### 2.2 Where its numbers come from

Every figure in the dossier cites a public source. Nothing is invented without a range to anchor it.

| Feature | Source | Status |
|---|---|---|
| Revenue per employee, payroll share, capital spending for the industry | **US Census Bureau, Annual Integrated Economic Survey (AIES).** It replaced the Annual Survey of Manufactures, collecting from March 2024. | verified that AIES replaced ASM; table selection unverified |
| Wages by occupation (machinists, assemblers, engineers) | **BLS Occupational Employment and Wage Statistics** | unverified for current release |
| Operating margin, R&D as a share of revenue, capital spending, dividend payout | **Aswath Damodaran's industry datasets, NYU Stern**, updated January 2026 (margins, R&D, capex, dividend fundamentals) | verified the datasets exist and the date; terms of use unverified |
| Peer financial structure (debt, cash, buyback history) | **SEC company financial data** (XBRL `companyfacts` API, or the Financial Statement Data Sets) | API verified; data-set currency unverified (one source listed releases only through 2023). *Patched 2026-10-04 (his): **not used for the fictional company**, which takes industry-level figures only (Census, BLS, Damodaran), so no list of real peer companies exists anywhere; kept for Phase 5's real cases* |

### 2.3 Why this is the main attack surface

A critic's first line will be "it's a toy company." The answer is a **published dossier with a source on every
number**: "operating margin 9%: industry median per [dataset, date]." The dossier is the most important public
document in the project after the methods page.

---

## 3. Model facts that set the rules

### 3.1 Training cutoffs (verified 2026-10-02, Anthropic's models overview)

| Model | Training data cutoff | Reliable knowledge cutoff | Bedrock ID | Price in / out per million tokens |
|---|---|---|---|---|
| Fable 5.1 | Jun 2026 | Jun 2026 | `anthropic.claude-fable-5-1` | $10 / $50 |
| Opus 5.5 | Jun 2026 | Jun 2026 | `anthropic.claude-opus-5-5` | $4 / $20 |
| **Sonnet 5.5** | Jun 2026 | Jun 2026 | `anthropic.claude-sonnet-5-5` | $2 / $10 |
| Haiku 4.5 | Jul 2025 | Feb 2025 | `anthropic.claude-haiku-4-5` | $1 / $5 |

- Prices are **Anthropic's API list prices**. Bedrock sets its own and its own model lifecycle. Bedrock pricing and
  availability in his region are checked in `03`.
- Anthropic's Batch API is 50% off; whether Bedrock's batch mode carries a similar discount is checked in `03`.
- **Non-Claude models** (for the multi-model comparison and local models) have their own cutoffs, checked before
  any of them joins the experiment. **The real-case window is set by the latest cutoff of every model used.**
- **Side finding, outside this project:** Anthropic lists Haiku 4.5's retirement as *not sooner than October 15,
  2026* on Anthropic-operated platforms. Musical Mycelium runs on Haiku 4.5 through Bedrock, which sets its own
  dates. Worth a check in that repo.

### 3.2 What that means for real cases

With every current Claude model at a June 2026 cutoff, **a real case's decision must be first disclosed publicly
after June 2026.** Preferred: **first disclosed on or after August 1, 2026**, a buffer against late-June material
the cutoff may partly include. July cases are allowed only after a check that nothing signaled the decision earlier.

---

## 4. The real cases

### 4.1 Selection criteria (all required)

1. **Publicly traded and filing with the SEC**, so pre-decision filings are free and complete on EDGAR.
2. **The decision was first disclosed after the cutoff window** in §3.2. A decision that was "previously announced"
   or "previously discussed" before the cutoff fails, even if the formal filing came later (see §4.4).
3. **A real decision with real alternatives:** a closure, a workforce change, a downturn response, an investment. Not
   a forced wind-down (a failed drug trial ending a biotech program is not a choice between levers).
4. **Maps onto the lever menu:** what the company did can be expressed as the same choices the CEOs make.
5. **Not instantly recognizable** after anonymization (tested in §4.6).
6. **Across the set: at least one case where the company chose to invest, retool, retrain or hold its workforce**
   (decided 2026-10-02, `00` §5.4).
7. **Preferred: manufacturers of comparable size**, so the real cases speak to the same kind of company as the
   fictional one.

*Patched 2026-10-04 (his, Phase 5 decision 4):* criteria 3, 4 and 5 are judgments, applied after the official grid's
results are known, so **every candidate rejected on one of them is checked by an independent reader** that has not
seen those results (`07` §10.0).

### 4.2 Discovery channel 1: SEC 8-K Item 2.05 (verified working 2026-10-02)

When a public company commits to an exit or disposal plan (a plant closure, a restructuring with severance), it must
file a Form 8-K under **Item 2.05, "Costs Associated with Exit or Disposal Activities."** That makes Item 2.05 the
main dated, machine-searchable source of cut-side decisions. It is not complete: it is triggered only by material
exit costs, so many workforce reductions never file one (WARN notices, §4.7, cover part of the gap; corrected
2026-10-03, `08` §6).

**Tested 2026-10-02** with EDGAR full-text search over 8-Ks filed July 1 to October 2, 2026:
- **64 filings** mention Item 2.05.
- **33 come from manufacturing companies** (SIC codes 2000-3999).
- Of those, a usable core is mid-size industrial and consumer-goods manufacturers closing or consolidating plants,
  exiting product lines, or cutting salaried staff. Many others are biotech program wind-downs, which fail criterion 3.

**Supply on the cut side is not the constraint.** Five strong cut-side cases are realistic.

### 4.3 Discovery channel 2: investment and retention decisions

**This side is harder, and the reason matters.** There is no 8-K item that companies must file when they decide to
invest, retrain or keep people. Those decisions appear voluntarily, in press releases attached to 8-Ks, in quarterly
filings, and in trade press and state economic-development announcements.

**First pass, 2026-10-02:** August and September 2026 trade-press roundups list many US manufacturing investments,
but most of the investing companies were very large, foreign-listed or private, which fails criteria 1, 5 or 7.
Mid-size US filers with clear invest-or-retain decisions were scarcer.

**Two honest readings, and the project cannot tell them apart:**
1. Companies really do choose to cut more often than to invest (his expectation).
2. Cuts are disclosed by law and investments by choice, so cuts are simply more *visible*.

Either way, it is **a visibility effect in the data, not evidence about frequency.** The "how often?" frequency
study (a post-v1 phase, `00` §6.1) is where that question gets measured properly, and it has to account for this
asymmetry.

**Where the asymmetry is, precisely (refined 2026-10-02, from his question "is the project fundamentally flawed?").**
What is lopsided is **announcements**: an exit or restructuring requires an 8-K; an investment decision does not.
What is *not* lopsided is the **numbers**. Every public company reports capital expenditures, R&D expense, share
repurchases and dividends in its required financial statements, quarterly and annually, in structured XBRL form
(the same `companyfacts` API verified in §5), and describes its workforce in the annual report. So investment is
measurable **in aggregate** after the fact; it is harder to *find as a dated decision*, and aggregate capital
spending or R&D does not show which decision it came from. Training spend is not required data at all (corrected
2026-10-03, `08` §6).

**What the asymmetry does and does not touch:**
- **The core experiment: untouched.** The fictional company's CEOs choose from the full lever menu, and every choice
  is recorded identically whichever way it goes. Nothing there depends on what companies disclose.
- **The real cases: affected in discovery, and in what can be measured per case** (corrected 2026-10-03, `08`
  §4.6). Discovery is handled by selection criterion 6 (at least one invest-or-retain case), by a mechanical
  selection rule (`07` §10.0), and by stating on the methods page exactly how cases were found. Measurement differs
  by case: a closure shows its choice and its job count, an investment may show only that it was funded, so each
  case is matched only on what it discloses, and **its observed and excluded dimensions are shown beside its
  result** (`07` §10.2). The real cases illustrate the protocol on real decisions; they are never a claim about how
  often companies do anything.
- **The frequency study: would be badly affected if it counted announcements, so it will not.** It measures what
  companies did with their money from financial statements (`00` §6.1).

**Limits that remain, stated as such on the methods page:** filings show decisions taken, not options considered and
rejected, or intentions; and three to five real cases cannot represent all companies.

**Plan for the invest-side case:** search press-release exhibits on 8-Ks (Items 7.01 and 8.01), 10-Q capital-spending
disclosures, and state economic-development announcements, then cross-check each candidate against EDGAR for
criteria 1 and 2. **Fallback (decided 2026-10-02):** a mixed case, where a company closes one facility and moves production to
a new one it is building, counts as "retool" and satisfies criterion 6. At least one such case exists in the first
pass.

### 4.4 The "previously announced" trap (found 2026-10-02)

A filing dated after the cutoff can describe a decision made public before it. One July 2026 Item 2.05 filing in the
first pass describes a closure *"as previously discussed during its first-quarter 2026 earnings call."* The filing
date passes the window; the decision does not. **Rule: date a decision by its first public disclosure, never by its
filing date.** Every candidate gets a search for earlier mentions before it is accepted.

### 4.5 The AI-workforce case

The AI-savings scenario needs a real company that tied a workforce change to AI. **In the first pass, none of the
manufacturing Item 2.05 filings cited AI.** AI-attributed reductions in July to September 2026 cluster in technology
and services companies.

**Decided 2026-10-02: (a).** The AI-workforce case may come from outside manufacturing, labeled as a different
company type. (The alternative, keeping every case in manufacturing, would leave the AI scenario without a real
counterpart in v1.) The AI scenario is the core of the thesis (`00` §1); leaving it without a real
case weakens the most important comparison. The label keeps it honest.

### 4.6 Building a pre-decision dossier

For each accepted case:

1. **Cut-off date:** the day before first public disclosure.
2. **Contents:** the most recent 10-K and 10-Q before the cut-off, plus earlier 8-Ks that a CEO would know about. Only
   documents dated before the cut-off.
3. **Anonymization:**
   - Remove company, brand, product, executive and place names. Places become regions ("a plant in the US Midwest").
   - **Scale every dollar figure by one fixed, undisclosed factor per case** and round. *Patched 2026-10-04 (his):*
     the factor is **drawn** from a range stated in the protocol, with a private recorded seed, never chosen.
     Ratios, margins and trends, which drive the decision, are preserved; exact figures, which identify a company,
     are not.
   - **Scale headcounts by the same factor**, rounded (added 2026-10-03, `08` §4.7). Scaling dollars alone would
     change pay per employee and revenue per employee, which distorts the decision and can make the case stand
     out. Check that pay per head stays in a realistic band after rounding.
   - Dates become relative ("fiscal year N, Q3").
   - Remove distinctive facts that identify a company on their own (a unique product, a famous lawsuit).
   - *Patched 2026-10-04 (his):* **option figures come only from documents dated before the cut-off;** where an
     option has none, every option is described without figures alike (`07` §10.1).
4. **Recognition probe:** before any run, each model is asked *"Which company is this?"* If a model names it, or
   names it with confidence, the case is fixed or dropped. Probe results are published (by case type). It is a
   direct, measurable answer to "the model just recognized the company."
5. **Ground truth, recorded before any model sees the case:** what the company actually did, mapped onto the lever
   menu by a written rubric. **Written first, never adjusted after seeing results.** This is pre-registration, and it
   is what stops the comparison from being bent toward the answer anyone hopes for.

### 4.7 Discovery channel 3: WARN notices and trade press

The federal WARN Act requires notice before plant closings and mass layoffs, and states publish those notices. They
reach private companies too, so they are good for *finding* events. Each one still has to pass criterion 1 through
EDGAR. Trade-press roundups (monthly investment and layoff summaries) serve the same role for the invest side.

### 4.8 Where real-case material lives

- **Public:** this file, the selection criteria, the rubric, the probe results, and results by case type.
- **Private (`methods-appendix/`, gitignored in the repo, decided 2026-10-02):** candidate longlists, company
  identities, filing links, scaling factors and unscaled figures.
- **Backup of the private material:** during planning it lives in this folder inside `job-search-headquarters`, which
  is a **private** GitHub repo (verified 2026-10-02). That repo is the backup for the gitignored appendix once the
  project repo exists. That closes the "local-only file" risk raised in `00`.
- The public methods page states plainly that real-case sources are withheld.

---

## 5. Access mechanics (EDGAR)

Verified 2026-10-02 (SEC developer resources, and a live query from this machine):

- **No API key.** Every request carries a **User-Agent header identifying the requester** (name and contact email).
- **Rate limit: 10 requests per second**, across all machines. Exceeding it blocks the IP until the rate stays under
  the limit for 10 minutes.
- **Endpoints used:** full-text search (8-K Item 2.05 discovery); `data.sec.gov/submissions/CIK##########.json`
  (a company's filing history); `data.sec.gov/api/xbrl/companyfacts/CIK##########.json` (structured financials);
  the `Archives` paths for filing documents.
- **Implementation rules:** cache every fetched document (filings never change), throttle well under the limit,
  and store each dossier's source list with accession numbers so a case can be rebuilt exactly.

---

## 6. Licensing and use

- **SEC filings:** public records, free to retrieve and analyze. The project republishes no filing text in public;
  dossiers are anonymized summaries.
- **US Census and BLS data:** US government works, public domain.
- **The Business Roundtable statement:** quoted briefly, with attribution, as the subject of the test.
- **Damodaran datasets:** free and widely used; **terms unverified**. Cite as the source; check terms before
  redistributing any table.

---

## 7. Open items

**His decisions:** all four closed 2026-10-02 (stakeholder wording, non-manufacturing AI case allowed,
industrial machinery, retool fallback).

**Claude's checks still owed:**
1. AIES and BLS tables: which exact tables, current release (§2.2).
2. Damodaran terms of use (§6).
3. Whether the SEC Financial Statement Data Sets are current; otherwise `companyfacts` only (§2.2).
4. ~~Bedrock prices, regional availability, batch discounts (`03`).~~ Done 2026-10-02 in `03` §2 and §5.
5. Cutoffs of any non-Claude model before it joins (§3.1).
6. Each real-case candidate: first-disclosure date, public status, and recognition (§4.4, §4.6). Happens during case
   building, not here.
