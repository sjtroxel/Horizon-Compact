# Phase 2 — Company Dossier (v0.2): IMPLEMENTATION

> **Plan, not an as-built record.** Written 2026-10-06 (Opus), immediately before the build, from the approved scope
> doc `phase-2-company-dossier.md` and its five decisions, `planning/01` §2 and §6-7, `planning/07` §2.4, §3, §4 and
> §9, `planning/06` §3.3, the Phase 2.5 scope doc (what it needs from the dossier), the Phase 1 code as built, and
> live source checks the same morning (§2). **APPROVED 2026-10-06 (his)**, with all five decisions in §15 taken as
> recommended.
>
> **Started out of order (his, 2026-10-06).** Phase 1 is not closed: its steps 3, 9, 11 and 12 wait on AWS
> (`KNOWN-GAPS.md`, BLOCKED entry), and Phase 1.5 waits on Phase 1. This phase needs no AWS and no official model, and
> nothing it produces depends on what those steps find (§3 finding 7).
>
> This doc may turn out wrong; it may not be silently wrong. It is updated as the build diverges, and each step is
> marked `[done]` with its date when it lands.

## 1. What this phase delivers

**One cited board pack for a fictional industrial machinery company, as data first and text second.** Every number in
the text is rendered from a row in one data file, and every row has a source or is marked as an assumption with its
range and reason. A check fails the build if any digit in the text did not come from a row.

Built in this order (§13): the source checks recorded and the planning patches made; the data format, the renderer
and the check, with tests (code, Sonnet); the figures and the template text (drafting, Opus); his line-by-line review;
the realism read by another vendor's model; close-out.

**Not here** (scope doc): the four scenarios, the objective wordings, the neutrality checklist on scenarios, any
model call on the dossier, any change to the sweep harness. Those are Phase 2.5.

## 2. The source checks, run live 2026-10-06

The scope doc's four checks (Delivers 1; `planning/01` §7 items 1-3). Closing them in `KNOWN-GAPS.md` and patching
`planning/01` §2.2 and §7 is step 1 of the build (§13), from this table.

| Source | Finding (2026-10-06) | Use in the dossier |
|---|---|---|
| **Census AIES** | **The 2024 AIES is the current release** (full data released 2026-09-03; time series 2026-09-10). Keyless bulk files at `www2.census.gov/programs-surveys/aies/data/2024/`; the manufacturing tables are `AIES31BASIC01` (U.S. by industry), `-02` (by state), `-03` (expenses and inventories). **NAICS 333, Machinery manufacturing, U.S., 2024, read from `AIES31BASIC01`:** revenue $473,891,483 thousand; employees 1,046,464; annual payroll $84,347,756 thousand; fringe benefits $22,566,734 thousand; cost of materials $237,904,461 thousand; value added $236,158,343 thousand. Detail goes down to six-digit NAICS. **Capital spending is not in these files**: it is in the `aiesmiscsector` dataset, which the Census API serves only with a key (redirects to `missing_key` without one). | Revenue per employee (about $453 thousand), payroll share of revenue (about 17.8%), fringe benefits relative to payroll (about 26.8%), materials share of revenue (about 50.2%), production-worker share. Capital spending comes from Damodaran instead, so no Census key is needed. |
| **BLS OEWS** | **May 2025 is current**, released 2026-05-15 (the national news release, read live). The industry-specific estimates cover NAICS 333000 and its four-digit industries. The BLS web pages refused automated reads, so the 333000 rows are downloaded as the industry-specific file in the build (step 1) and the exact file name and edition recorded then. | Pay by occupation for every function in the workforce table: machinists, assemblers, welders, maintenance, engineers, supervisors, sales, service technicians, office and administrative. |
| **Damodaran** | **Current edition dated 2026-01-09.** The US industry **Machinery** exists, **105 firms**. Margins file, read live: operating margin (pre-tax, unadjusted) 15.86%; net margin 10.58%; R&D/sales 2.03%; SG&A/sales 19.65%; EBITDA/sales 19.62%; gross margin 37.47%. Also available: capital expenditures, dividends and FCFE, debt details, working capital, employee statistics, cash. **Terms:** his 2026-01-09 post says "If you use my data, and acknowledge me as a source, I thank you, but you do not need to explicitly ask me for permission" and "The data is in the public domain to be used." | Margins, R&D, capital spending, payout, debt and cash ratios. **Quoted with attribution**, which his statement allows. |
| **SEC Financial Statement Data Sets** | **Current**: quarterly, with 2026 Q1 and Q2 posted. The 2026-10-02 worry (releases only through 2023) was wrong. | **Not used for the fictional company** (scope decision 3). Recorded for Phase 5. Moot here, closed with the reason. |

## 3. What writing this doc found

1. **Damodaran's figures are aggregates, not medians.** His industry ratios are computed over the industry's 105
   public firms taken together, which weights the largest firms most. `planning/01` §2.3's example ("industry median
   per [dataset, date]") and the scope doc's "set from industry medians" are both wrong about that. Every Damodaran
   row says "industry aggregate, 105 firms," and `planning/01` §2.3 gets a dated note in step 1.
2. **Two populations, said plainly.** Census AIES covers every employer firm in NAICS 333, private and small ones
   included; Damodaran covers public firms only. A board pack mixes such sources all the time, but a reader with a
   finance background will check. Each row names its population, and where the two disagree on the same quantity
   the dossier takes one and the assumptions table says why.
3. **The scale holds together.** At the AIES revenue per employee, a company with $1.5 billion of revenue has about
   3,300 employees, inside `planning/01` §2.1's "several thousand." The headcount is derived from the revenue and
   the ratio, not chosen separately.
4. **The source years differ.** AIES is 2024, OEWS is May 2025, Damodaran is data for 2025 published January 2026.
   The dossier uses **ratios** from AIES (stable year to year) and **dollar pay** from OEWS, and does not inflate
   anything, because an inflation factor is an invented number. The assumptions table records the mismatch once.
5. **A number in the text with no row is detectable mechanically.** If the template's own text contains no digit at
   all, every digit in the rendered dossier came from a row. Plant numbers become rows too (unit `label`). That is
   DoD 1's check, and it is simpler and stricter than matching numbers back to rows after rendering.
6. **The dossier will be tokenized without a Claude tokenizer.** Counting Sonnet 4.6 tokens exactly needs a call to
   an official model, which this phase forbids. The length target (about 6,000 tokens, `planning/03` §3.1) is checked
   as words times 1.35, recorded as an estimate; Phase 2.5's development runs report Nova Lite's count and Phase 4's
   pilot reports Sonnet's. Nothing depends on the exact number: the caching minimum is 1,024.
7. **Nothing Phase 1 still has to do can invalidate this phase.** The model reads the dossier as `dossier.toml`
   (`title`, `text`), the format Phase 1 built and committed (`experiment/placeholder/dossier.toml`,
   `src/horizon_compact/experiment.py`). Phase 1's open steps test calls and storage. If a provider changes, the
   dossier does not.
8. **The loader expects a whole experiment folder.** `load_experiment` reads `dossier.toml`, `scenario.toml` and
   `objectives.toml` from one folder. The dossier's folder holds no scenario until Phase 2.5, which decides how its
   four scenarios share one dossier (one loader change, there). This phase does not touch the loader (scope: no
   harness change).
9. **Where the citations go is a design choice** (decision 1). A board pack carries no footnotes. Citations in the
   model's prompt would tell it the company is built from industry averages, which is a cue that it is in a test
   (`planning/07` §7.5's awareness probe exists because of that risk). The public needs the citations. Both can come
   from the same rows.

## 4. Layout

```
experiment/company/                       the dossier, hashed into the image like all experiment content
  figures.toml                            every figure: value or formula, unit, source or assumption
  sources.toml                            every source: publisher, title, edition, release date, URL, table, terms
  dossier.template.txt                    the board-pack text, with {row_id} placeholders and NO digits
  dossier.toml                            RENDERED (title, text): what the model reads; committed, checked
src/horizon_compact/dossier/
  figures.py                              the data model (pydantic), formula evaluation
  render.py                               template + figures -> dossier.toml text; the cited public version
  check.py                                the checks of §7
docs/phases/evidence/phase-2/
  sources/                                extracts of the source rows used, one file per source (decision 3)
  dossier-cited.md                        RENDERED: the public version, with a citation on every number
  figures-table.md                        RENDERED: every row, its value, source or assumption
  assumptions-table.md                    RENDERED: the assumption rows only, his review columns
  realism-brief.md, realism-raw.md        the realism read, as `08a`/`08b` are
tests/test_dossier.py
```

`experiment/README.md` gets one line for `company/`. Nothing is added at the repo root.

## 5. The data format

**`sources.toml`**, one table per source:

```toml
[sources.aies-2024-basic01]
publisher = "US Census Bureau"
title = "Annual Integrated Economic Survey, 2024, table AIES31BASIC01"
released = 2026-09-03
retrieved = 2026-10-06
url = "https://www2.census.gov/programs-surveys/aies/data/2024/AIES31BASIC01.zip"
population = "all US employer firms, NAICS 333"
terms = "US government work, public domain"
extract = "docs/phases/evidence/phase-2/sources/aies-2024-basic01.csv"
```

**`figures.toml`**, one table per figure. A row is exactly one of three kinds:

```toml
[figures.ind_revenue_per_employee]          # SOURCED: a value read from a source
label = "Industry revenue per employee"
value = 452851
unit = "usd"
source = "aies-2024-basic01"
locator = "NAICS 333, U.S., RCPT_TOT_VAL / EMP_MAR12_NUM, x1000"

[figures.revenue_fy0]                        # ASSUMPTION: a chosen value, with its range and reason
label = "Revenue, year just ended"
value = 1_500_000_000
unit = "usd"
assumption = { low = 1_000_000_000, high = 2_000_000_000, range_from = "planning/01 section 2.1, scale decided 2026-10-02", reason = "midpoint of the decided scale" }

[figures.headcount_total]                    # DERIVED: a formula over other rows
label = "Employees"
formula = "revenue_fy0 / ind_revenue_per_employee"
unit = "count"
round = 10
```

- **Units:** `usd`, `usd_m` (rendered in millions, one decimal), `pct` (one decimal), `count`, `years`, `ratio`,
  `label` (rendered as written; for plant numbers and the like). Rounding is per row, defaulting by unit.
- **Formulas** use only row IDs, numbers, `+ - * /` and parentheses, evaluated by a small `ast` walker, never
  `eval`. A cycle or an unknown ID fails loading.
- **Every row must be used** by the template or by another row's formula; an orphan row fails the check, so the
  assumptions table never lists a figure the reader cannot find.
- **No row is chosen for its effect on a decision** (scope rule). The `reason` field says why that point in the range,
  in terms of the industry, never in terms of what a model might do.

## 6. Rendering

- **The template** is plain text with `{row_id}` placeholders, formatted with `string.Formatter` (standard library;
  no new dependency). It contains **no digit characters** outside placeholders.
- **`hc dossier render`** writes `experiment/company/dossier.toml` (the model's version) and the three rendered
  files under `docs/phases/evidence/phase-2/`. The model's version has no citations (decision 1). The cited version
  is the same text with a bracketed source label after each number, `[AIES 2024]` or `[assumption A7]`, and a
  sources list at the end.
- **The title** follows the placeholder's pattern: "the Company: board pack for the year just ended" (wording settled in
  drafting). The dossier says "the Company" throughout (scope decision 4), and the plants by region and number.

## 7. The checks (`hc dossier check`, run by `make check` and CI)

1. **No digit in the template** outside a placeholder (DoD 1).
2. **The committed `dossier.toml` and the three rendered files equal a fresh render**, byte for byte, so nobody edits
   the output by hand.
3. **Every row is sourced, an assumption with a range and reason, or derived;** every source a row names exists in
   `sources.toml`; every row is used; no formula cycles; every assumption's value lies inside its own range.
4. **Every row ID in the template exists.**
5. **A balance report** (not a failure): words per stakeholder group (workforce, customers, suppliers, shareholders,
   environment and communities), from section markers in the template. It goes to the realism read and to Phase
   2.5's neutrality checklist (`planning/07` §9 items 3 and 9, scope Known risks).
6. **The estimated length** (words times 1.35), reported, warned above 7,000.

The name guard already runs on every file. The check adds nothing for it; the manual read in step 9 covers what the
guard cannot.

## 8. What the dossier contains

The outline. Each section is drafted in step 5 with its rows, and each names the scenario that needs it, so
nothing is there for its own sake and nothing a scenario needs is missing.

| # | Section | Holds | Needed by |
|---|---|---|---|
| 1 | The Company | what it makes (industrial machinery and replacement parts, sold to manufacturers; service revenue), where it sells, its plants by region | all |
| 2 | Results, three years | revenue, gross margin, operating income, net income, for the year just ended and the two before; growth from AIES year-over-year change where it exists | all |
| 3 | Balance sheet and liquidity | cash, debt, the credit facility, minimum operating cash; **uncommitted cash** (cash above the operating minimum) | S3 (every option fundable), S4 ($B) |
| 4 | Capital allocation | capital spending, R&D (with what it funds), dividends and repurchases and **the payout policy**, which S2 holds fixed | S2, S4 |
| 5 | Workforce | headcount by function and occupation, average pay from OEWS, benefits ratio from AIES, **payroll by function** | S1, S2 |
| 6 | Plants | six plants by region and number: headcount, revenue, operating result; **one with an operating loss**, its headcount and payroll | S3 |
| 7 | Customers and pricing | customer mix, recent price changes, **the price change the market would bear**, as a maximum | L5 in S2, S4 |
| 8 | Suppliers | supplier spend (AIES materials share), payment terms, **the share that could be renegotiated** | L9 in S2, S4 |
| 9 | Environmental spending | the current budget and what it covers | L6 everywhere |
| 10 | Technology and work | where the Company already uses automation; **the redeployment opportunity in numbers**: the new work that exists, the retraining cost per person, the time until it pays back (`planning/07` §3.2, retraining stated separately, decided 2026-10-04) | S1 |
| 11 | Limits on each line | one table: **the maximum for every lever that can be a source** (R&D that exists, payroll of each function, cash available, environmental budget, payout, renegotiable supplier spend) | every scenario's caps (`planning/07` §2.4 item 2a) |

**Register:** a board pack. Numbers, units, plain labels; no adjective about anyone's welfare or hardship or about
shareholders' expectations; no euphemism from `planning/06` §3.3; one vocabulary throughout. About 4,400 words.

**Rows likely to be assumptions** (scope Known risks; each gets its range from the best source found in step 5, or
says none exists): the Company's revenue (the decided scale), the plant split and the losing plant's result, the
price change the market would bear, the renegotiable share of supplier spend, the environmental budget, the
retraining cost and payback, the new work available. **A dossier with an honest assumptions table is stronger than
one that hides its guesses.**

## 9. The assumptions table

Generated from `figures.toml` into `assumptions-table.md`. Columns: ID (A1, A2, ... in template order), figure,
value, range, where the range comes from, why this point, and **his review**: accepted, changed (to what, why), or
questioned. He fills the last column in step 7 (DoD 4). A changed value is changed in `figures.toml` and re-rendered,
never in the table.

## 10. The realism read (DoD 5)

- **The reader** is another vendor's model through OpenRouter, as `planning/08` was made. **Not Anthropic** (the
  drafter's family) and **not Nova's maker** (Nova Pro is the second official model). Chosen live at step 8 from what
  OpenRouter offers that day, with its price checked; recorded with its exact model ID.
- **The brief** (`realism-brief.md`, drafted at step 8 and shown to him before it is sent): the cited version of the
  dossier; the question "what would a director or a buy-side analyst covering industrial machinery find implausible,
  missing, internally inconsistent or slanted"; the balance report; an explicit statement that it is a fictional
  company built from industry sources. **It is never asked what the CEO should do**, and it is never shown a scenario
  or an objective.
- **The raw reply** is committed unedited (`realism-raw.md`). Claude verifies each point against the sources; each is
  marked confirmed, partly right or rejected, in a table appended to this doc; **he decides each change.**
- **Cost:** one call, expected under $1, cap $3. From his OpenRouter balance, not the AWS credits; recorded in the
  `ROADMAP.md` cost ledger as outside the $80 AWS ceiling.

## 11. Rules this build must not break

- **No official model is called, for anything.** No Sonnet 4.6, no Nova Pro: not as a decision, a probe, a token
  count or a review. In practice nothing in this phase calls Bedrock at all.
- **Rule zero, sources included.** No real company's name, ticker or plant location in any file, including source
  extracts, which are cut to the rows used (industry aggregates; Damodaran's industry rows name no firm). The extract
  step drops any column that lists firms.
- **Numbers come from sources, never from what they might make a model do.**
- **The dossier is fixed when Phase 2.5 starts**; a later change is logged with a reason (Phase 2.5's change log).

## 12. Tests (`tests/test_dossier.py`)

Every fixture is a small made-up figures file, not the real one. The cases: a sourced, an assumption and a derived row
each load; a row that is two kinds at once, or none, is refused; an unknown source, an unknown ID in a formula, a
cycle, a disallowed character in a formula, and an assumption outside its own range are each refused; a digit in the
template outside a placeholder fails; an orphan row fails; each unit renders as specified, with rounding; the cited
version puts the right label after each number; a hand-edited `dossier.toml` fails the equality check; the real
`experiment/company/` passes all checks (once it exists). `make check` runs them with everything else.

## 13. Order of work

**Model for each step:** steps 1-4 are code and records (**Sonnet**). Steps 5-6 are drafting the instrument, where
wording and neutrality matter (**Opus**). Steps 7 and 9 are his. Step 8 is Opus for the brief and the verification.

0. **Approval of this doc** and its five decisions (§15). `[done 2026-10-06]` He commits it with the session's other
   doc edits.
1. **Close the source checks.** Record §2 in `KNOWN-GAPS.md` (a CLOSED entry); patch `planning/01` §2.2 (status
   column), §2.3 (aggregates, not medians, §3 finding 1) and §7 items 1-3, each with a dated note. Download the OEWS
   May 2025 industry file and record its name and edition. Write `sources.toml` and the source extracts (decision 3).
   `[done 2026-10-06]` As built: the CLOSED entry is in `KNOWN-GAPS.md`; `planning/01` is patched in §2.2, §2.3, §6
   and §7 (§6 too, because it still said Damodaran's terms were unverified); OEWS is `nat3d_M2025_dl.xlsx` in
   `oesm25in4.zip`; ten sources (AIES, OEWS, eight Damodaran files) are in `experiment/company/sources.toml` with the
   hash of each exact file, and ten extracts are under `docs/phases/evidence/phase-2/sources/`. **Divergences from
   this doc:** (1) `sources.toml` carries three fields beyond §5's example, `edition`, `file` and `sha256`
   (plus `archive_sha256` for zips); step 2's model must accept them. (2) The §5 example row's 452851 is really
   452850, from the file. (3) The extracts hold every field of the NAICS 333 row (AIES) and 21 candidate occupations
   plus the major groups (OEWS), which is more than the final figures will use: **step 6 prunes each extract to the
   rows the figures cite** before C2. (4) The Damodaran `Employee` file is not used (bad Machinery row; CLOSED entry).
   (5) The extract script is `scratch/phase2-extract-sources.py`, untracked. (6) Damodaran's values are written to
   8 significant digits in the extracts (binary-float noise, and the account-id test, `KNOWN-GAPS.md` CLOSED entry);
   the rounding the figures use is far coarser. (7) `sources.toml` also carries a `short` label per source, which
   the cited version prints after a number.
2. **The data model and formulas** (`figures.py`) with their tests. `[done 2026-10-06]` Pydantic models for
   sources, assumptions and rows; formulas parsed with `ast` and walked, `Decimal` arithmetic. **Rules the build
   fixed that §5 and §6 left open:** (1) **rounding is one rule:** every row's value is rounded half up to its step
   (its `round`, or the unit's default: usd 1, usd_m 100,000, pct 0.001 as a fraction, count 1, years 0.1, ratio
   0.01) when resolved, and formulas and text both see the rounded value, so the page's numbers agree with each
   other; an explicit `round` must be a multiple of the unit's default. (2) **`pct` is stored as a fraction**
   (0.159, shown 15.9%); `usd_m` is stored in dollars. (3) **A `label` row (a plant number) is an assumption with
   no range** (`low` and `high` both absent), listed in the assumptions table as "none (a name, not a quantity)";
   it gets no bracket in the cited text. (4) **An assumption has an optional `review` line**, which is where his
   step 7 review is recorded, so the rendered table stays reproducible from the data (§9 said he fills the table;
   a hand-filled table could not pass the byte-for-byte check). (5) Numbers use strict types: a TOML boolean is
   refused (a lax union had quietly read `true` as 1; the test for it found that).
3. **The renderer and the checks** (`render.py`, `check.py`), the `hc dossier render` and `hc dossier check`
   commands, and `make check` running the check. Tests first where practical. **Commit C1** (code only; the real
   files do not exist yet, so the last test in §12 is skipped until they do, and says so). `[done 2026-10-06]`
   `render.py` (template parser, renderer, the three tables), `check.py`, the `hc dossier` group in `cli.py`, and
   `tests/test_dossier.py` (the §12 cases: 83 pass and one is skipped by name). **As built:** (1) **the template's
   markers are `@title <text>` (once, first) and `@group <name>` lines**, never rendered; groups are `general`,
   `workforce`, `customers`, `suppliers`, `shareholders`, `environment`. Consecutive blank lines collapse. (2)
   **The digit check rejects any Unicode numeric character**, so `2` `²` and `½` all fail. Spelled-out numbers
   ("two years ago") cannot be checked mechanically; **step 7's line-by-line read is the check for them.** (3)
   **Cited labels:** a sourced row prints its source's `short`, an assumption `assumption A#`, a derived row
   `derived D#`, numbered in order of first appearance in the template. (4) **An orphan is a row the template
   cannot reach**, directly or through formulas (stricter than §5's "used by another row's formula": a chain of
   rows feeding only each other is still an orphan). (5) **While none of `figures.toml`, the template and
   `dossier.toml` exist, `hc dossier check` validates `sources.toml` and its extracts and prints a SKIPPED note;
   once any exists, all must. Step 6 removes the skip** (it is a hole: deleting all three would pass). (6) Exit
   codes: 0 ok, 1 a check failed, 2 `render` refused. (7) The token estimate is words x 1.35 and warns above 7,000.
4. **Wire-up**: `experiment/README.md` line, `.gitignore` if needed, `make check` green. `[done 2026-10-06]` The
   README line; a `dossier-check` Makefile target in `check` (so CI runs it); `.gitignore` needed nothing. `make
   check` is green with doctor (436 tests, 1 skipped, mypy strict, ruff, both Terraform roots). The name guard,
   run on a temporary copy of the whole change set, passes. **One thing it cost:** the repo's account-id test caught
   the extracts' float noise (12-digit fractions); the Damodaran extracts were re-cut to 8 significant digits and
   the test was left alone (divergence 6, step 1).
5. **Draft the figures** (Opus), section by section in §8's order: every sourced row from the extracts, every derived
   row as a formula, every assumption with its range and reason.
   `[done 2026-10-06, drafted; uncommitted]` `experiment/company/figures.toml`: 216 rows, all resolving. **It cannot
   be committed alone:** with figures and no template, `hc dossier check` fails the folder as half built, by design,
   so it lands with step 6 in C2. **Five sources added** (15 in all): AIES 2023 (industry revenue 2023 to 2024,
   -0.5%), Damodaran's archived January 2024 and January 2025 margin editions (so each of the three years has its
   own industry margins), BLS PPI for NAICS 333 (2022-2025 annual averages: the price changes) and BLS JOLTS for
   durable goods manufacturing (2025 hires rate, 26.4%: the openings a retrained person could fill). All through
   keyless public routes; the Census M3 API wants a key and FRED refused automated reads, so neither is used.
   **How the Company is built:** revenue $1,500.0 million (the one scale assumption); every margin, the balance
   sheet ratios, capital spending, payout and repurchases from Damodaran's industry aggregates; headcount from
   AIES revenue per employee (3,310); the functions, their headcounts and pay from OEWS shares and mean wages; the
   benefits ratio and the supplier spend from AIES. The statements tie: operating income is gross profit less SG&A
   and R&D; net income is operating income less interest (debt at the industry's debt to EBITDA, at its book
   rate) less tax; payroll by function adds to the total; the plants add to operating income. **Two findings:**
   (1) OEWS pay gives payroll at 16.3% of revenue against AIES's 17.8%; OEWS is used throughout because pay by
   occupation needs it, and the row's note says so. (2) `formula_references` validated a formula by evaluating it
   with every row set to one, so `ev * r / (1 - r)` divided by zero and a valid formula was refused; it now walks
   the formula without arithmetic (a regression test added). **Code change:** an optional `note` on any row,
   shown in the figures table only, never in the model's text (tested). **Assumptions: 31**, six of them plant
   numbers; the rest are the scale, plant count, aftermarket share, unit volume, minimum cash, the credit
   facility, five plant shares and five plant margins, the price ceiling, two supplier figures, two environmental
   figures, three retraining figures and the wage-or-hours ceiling. Every one says where its range comes from,
   and most say plainly that no public industry-level source was found.
6. **Draft the template** (Opus) and render. Run the checks. Estimate the length. **Commit C2** (the dossier, its
   rendered files, the source extracts).
   `[done 2026-10-06, Opus; uncommitted until he runs C2]` `experiment/company/dossier.template.txt`, eleven
   sections in §8's order, rendered to `dossier.toml` and the three public files; `hc dossier check` green with no
   skip; `make check` green (438 tests); the name guard passes on the whole change set. **Three more rows**
   (return on equity, dividend yield, market value over net income), all derived, no new assumption: the balance
   report had the shareholder section at 54 words. **Balance now (words):** general 1,152, workforce 418,
   customers 126, suppliers 112, shareholders 98, environment 88. The workforce lead is structural (payroll by
   function is every scenario's caps); it goes to the realism read and Phase 2.5's checklist as is. **Length:
   about 1,990 words, an estimated 2,690 tokens, well under §8's 4,400 words.** Not padded: every added sentence
   is unsourced content, the caching minimum is 1,024, and a shorter prefix costs less per run. **Found and
   fixed:** (1) the cited version's source list followed a set's order, which changes per process with Python's
   string hashing, so a render could differ from the committed file; now sorted, with a test that renders under
   six hash seeds and fails without the fix. (2) The figures table printed a raw twelve-digit dollar amount
   (AIES revenue), which tripped the account-id test; integers now print with separators. (3) The skip is gone:
   a missing figures file or template fails the check. **Extracts pruned** to the rows the figures cite plus each
   file's identifying rows (the script's `KEEP` list); 170 lines across 15 files. **Unsourced statements in words**
   (no number, so no row; step 7 should read them as claims): the product range and customers' industries; the
   sales force plus distributors; list prices set once a year; that debt was held level and no principal falls
   due in the coming year; what capital spending and R&D fund; the dividend set as a share of net income and an
   annual repurchase program; what office and business functions cover; why Plant 6 loses money (smallest plant,
   lowest-volume family, fixed costs over fewer units); supplier categories and multi-year agreements; what
   compliance and environmental projects cover, and that compliance is required by permits; the automation in
   use; that the openings are positions a retrained employee could fill. **One design call for him:** the
   environmental line's limit is the projects budget only ($4.5 million); compliance ($3.0 million) is stated as
   required and not available.
7. **His review** (DoD 4): the assumptions table line by line, then the rendered model version line by line. Each
   change goes through `figures.toml` or the template and a re-render. **Commit C3** if anything changed.
   **Working method (written 2026-10-06 for the session that runs it):**
   - **He reads; Claude does not decide.** Go one assumption at a time, A1 to A31, in `assumptions-table.md`
     order (the ID is the row's place in the template, not in `figures.toml`; the table's second column gives the
     row id). For each, show him the value, range, where the range comes from and the reason, in a few lines, and
     ask: accept, change (to what, why) or question. Do not batch several into one question, and do not argue
     him toward accepting. If he asks for evidence, check the source or the extract; never answer from memory.
   - **Record his verdict in `figures.toml`**, never in the rendered table: add `review = "..."` inside that
     row's `assumption = { ... }` inline table, in his words or a faithful short form (for example
     `review = "accepted 2026-10-07"` or `review = "changed from 0.30 to 0.25, 2026-10-07: <his reason>"`). A changed
     value changes `value`, and the range and reason too if his reason changes them; the value must stay inside
     its range or the check fails.
   - **Then the rendered text, `experiment/company/dossier.toml`, section by section**, and the unsourced
     statements in words (the list in step 6 above). A wording change goes in `dossier.template.txt`: no digit
     outside a `{row_id}` placeholder (the check refuses one), plain register, no adjective about anyone's welfare
     or shareholders' expectations, no euphemism (`planning/06` §3.3), one vocabulary. A new number needs a new
     row in `figures.toml` (sourced, assumption with range and reason, or derived) and must be reachable from the
     template, or the check fails it as an orphan.
   - **After every batch of edits:** `uv run --no-sync hc dossier render`, then `uv run --no-sync hc dossier
     check`. Before the commit: `make check`. A new or changed source row must match its extract exactly
     (`docs/phases/evidence/phase-2/sources/`); if a new source row is needed, the extract script is
     `scratch/phase2-extract-sources.py` (its `KEEP` list prunes each extract) and the downloads are gone with the
     old session's scratchpad, so re-download into a new scratchpad folder and read with `python -I`.
   - **Watch the shared numbers:** many rows feed others (revenue feeds nearly everything; plant shares feed plant
     revenue, headcount and Plant 1's remainder). After a change, read the re-rendered numbers he cares about
     and tell him what moved, especially the scenario-facing ones: Plant 6's revenue, headcount, loss and payroll;
     the limits in section eleven; the uncommitted cash flow ($20.4 million); plant hires.
   - **Open design call to put to him first:** the environmental limit is the projects budget only; compliance
     is stated as required by permits and not available (step 6).
   - **Done when** every A-row has a `review` line and he has said he has read the rendered text; record his
     statement in this doc's as-built notes (DoD 4). Commit C3 with `make check` green.
   - `[done 2026-10-06, Sonnet; uncommitted until he runs C3]` **As held, and what it is.** **The environmental
     limit (the open design call): kept as drafted** (his: "Don't let the board break its permits. Make sure the
     board acts legally."): the limit is the projects budget only ($4.5 million); compliance ($3.0 million) is
     stated as required by permits and not available. **A1 to A31: every row has a `review` line, and no value,
     range or reason changed.** A1 to A3 were put one at a time; A4 to A31 were taken as one group at his
     request. **His statement for DoD 4, in his words:** he said he is "not a qualified expert in any of these"
     and does not expect to be better placed than Opus to decide the rest, and accepted Opus's recommendations for
     A1 to A31 and for "all the rest" of the rendered text. **Read this honestly:** the review is an acceptance
     of the drafted recommendations, not an independent line-by-line check: he has policy views but chose not to
     weigh in item by item, and did not judge himself qualified on the corporate facts (his, 2026-10-06); the `review` lines say "deferred to the drafted recommendation" for that
     reason. He read section one (given in full) and accepted the other ten sections on the same basis. The
     independent check on the numbers is therefore step 8's outside reader, not this step. **Checks Claude ran
     in place of a line-by-line read (2026-10-06):** (1) A1's "about $1.9 billion average revenue" re-derived from
     the extracts: $20,804.5 million net income / 10.58% net margin / 105 firms = $1.87 billion, a mean (the
     extract has no median). (2) A23's price changes (3.3% to 6.9%) and A10's prior-year volume change (-3.6%)
     re-derived from the PPI and AIES extracts. (3) The text's arithmetic: plant headcounts sum to 1,900, the
     rest to 1,410; cash above minimum $44.1 million; cash flow after payouts $20.4 million; dividend 33.4% of
     net income. (4) **A stated source is looser than it reads:** A15, A17, A19 and A21 say the plant margin is
     "within five points of the Company's operating margin excluding Plant 6" (18.3%); the ranges are the value
     plus and minus five points, which is not the same thing. The values themselves are within five points
     (15.0% to 20.0%). Left as is; the wording is for step 8 or a later patch. **Spotted in the text, left
     unchanged, for step 8 and his say:** (a) the three "price increases in the last three years" (6.9%, 3.3%,
     3.5%) are the industry's producer price changes, presented as the Company's own (the figures note says the
     Company is taken to have moved with the industry); (b) "pressing suppliers on price" (section eleven, and
     the supplier line) is the one phrase that reads as charged under `planning/06` §2; a neutral wording is
     "negotiating lower prices"; (c) "These are positions an employee from another function could fill after
     retraining" (section ten) is an unsourced sentence that makes the retraining lever look available. It is
     there on purpose (DoD 3), but a reader could take it as a lean.
     **Then a two-sided neutrality read (Opus, 2026-10-06, his request):** the text read once for framing that
     makes cutting workers, suppliers or environmental spending look easy, once for framing that makes the
     stakeholder options look easy, against `planning/07` §9; only lopsided points changed, each his decision.
     **Changed:** (b) above, in both places it lives: the dossier and `supplier_cap`'s label now say "negotiating
     lower prices with suppliers", and `planning/07` §3.1 L9 is patched to match (one vocabulary). **Logged:** S3
     states no community consequence (`KNOWN-GAPS.md` OPEN entry, for Phase 3). **Checked and left:** (a), (c),
     the dividend "policy" wording (every line in section eleven is listed as fully available, gross, with no
     consequence stated for any), Plant 6's stated cause (consistent with closing it and with adding volume), and
     the price cap's "without a loss of unit volume" (an estimate framed like purchasing's). He had asked first
     for the assumptions to be re-answered as a named politician would; declined on the project's rule that it
     tests a claim and does not argue one, and this read was done instead.
8. **The realism read** (DoD 5): pick the reader live, draft the brief, show him, send, commit the raw reply,
   verify each point, he decides each change, re-render. **Commit C4.**
9. **The manual rule-zero read** (DoD 6) of every file this phase added: spellings the term file lacks,
   descriptions detailed enough to identify a firm. Then the DoD audit (§14), `ROADMAP.md`, `KNOWN-GAPS.md` START
   HERE. **Commit C5** (close-out).

Commit messages: `phase 2: ...`, one line, his to run.

## 14. Definition of done, and the proof of each

| DoD (scope doc) | Proof |
|---|---|
| 1. Every number traces to a row; every row sourced or an assumption with range and reason | `hc dossier check` green in CI: no digit in the template, every row of a valid kind |
| 2. The four source checks closed | `KNOWN-GAPS.md` CLOSED entry and `planning/01` patches, step 1 |
| 3. A maximum for every source lever; the redeployment opportunity in numbers | §8 sections 10 and 11 present; the lever-limits table has a row per lever (a test lists the levers from `planning/07` §3.1 that can be sources) |
| 4. He reviewed the assumptions table and the rendered dossier line by line | His review column filled in `assumptions-table.md`; his statement in this doc's as-built section |
| 5. The realism read done and every point marked | `realism-brief.md`, `realism-raw.md` committed; the verification table in this doc |
| 6. No real company name, ticker or plant location | The guard passing on every commit, plus the manual read recorded in step 9 |
| 7. No official model called; `make check` and CI green | No Bedrock call in this phase (nothing to show in the provenance store); CI run IDs recorded |

## 15. Decisions for him

All five taken 2026-10-06 (his), as recommended: (1) no citations in the model's text, a cited public version from
the same rows; (2) relative year labels, no calendar date in the model's text; (3) extracts of the rows used are
committed; (4) `ROADMAP.md` marks Phase 2 closed when it closes, `pyproject.toml` steps through 0.1, 0.1.5 and 0.2 in
order once Phases 1 and 1.5 close; (5) the realism read is capped at $3. The options below stay as the record.

1. **Where the citations go.**
   - (a) **Recommended:** **the model reads a board pack with no citations; the public reads a cited version.** Both
     are rendered from the same rows, and the check proves the numbers are identical. Citations in the prompt would
     tell the model it is reading a constructed company, which is the cue `planning/07` §7.5 worries about, and a
     real board pack carries none. The methods page says exactly this.
   - (b) Citations in the model's text too. One version, simpler to explain, at the cost of the cue and about 15%
     more tokens.
2. **Calendar years, or "the year just ended."**
   - (a) **Recommended:** **relative labels** ("the year just ended," "the prior year," "two years ago") and no
     calendar date anywhere in the model's text. A named year invites the model to bring in what it knows about that
     year's rates, tariffs and markets, a variable the experiment does not control, which is the same reasoning that
     took the company's name out (scope decision 4). The cited public version gives the source editions, so the
     reader still knows when the numbers are from.
   - (b) A named fiscal year, matching the sources (the year just ended is 2025). More natural to a finance reader;
     brings in the year's associations.
3. **Commit extracts of the source rows.**
   - (a) **Recommended:** **commit small extracts of only the rows used**, one file per source, under
     `docs/phases/evidence/phase-2/sources/`. Census and BLS are public domain; Damodaran's statement allows it with
     attribution. Sources update (Damodaran each January), so without extracts a reader may not be able to find the
     number cited, which fails the scope doc's "under a minute" test.
   - (b) Cite URLs and editions only. Smaller, and dependent on the sources keeping old editions online.
4. **The version number, out of order.**
   - (a) **Recommended:** when Phase 2 closes, `ROADMAP.md` marks it **built and closed**, but **`pyproject.toml`
     stays at Phase 1's version** until Phases 1 and 1.5 close, then steps through 0.1, 0.1.5 and 0.2 in order. The
     spine stays readable, and the version never claims a phase that is not done.
   - (b) Bump to 0.2 at Phase 2's close regardless.
5. **The realism reader's cost cap.**
   - (a) **Recommended:** **$3**, one call, model chosen live at step 8 and shown to him before sending.
     `planning/08`'s much longer read cost $1.34.
   - (b) Another figure of his choosing.

## 16. Genuinely uncertain

- **Whether public sources exist** for the environmental budget, the retraining cost and payback, the price change
  the market would bear and the renegotiable supplier share. Likely assumptions; step 5 looks first.
- **Whether OEWS publishes every occupation needed** at the NAICS 333000 level, or some come from the all-industries
  table (a population difference, recorded per row).
- **Whether six plants by region** can each carry a believable headcount and result from industry ratios without
  invented detail. If not, the plant split is an assumption with its reason.
- **The length.** About 4,400 words is the target; if the outline needs much more, the drafting step says so before
  trimming anything a scenario needs.

## 17. Cost

**About $1, none of it on AWS.** The source downloads and all code and drafting are free. The realism read is one
OpenRouter call, capped at $3 (decision 5).
