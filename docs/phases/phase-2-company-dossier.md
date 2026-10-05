# Phase 2 — Company Dossier (v0.2)

> **Scope doc.** Written 2026-10-04 from `planning/05` §2 and §5 (Phase 2's row), `planning/00` §5.3, `planning/01`
> §2, §6 and §7, `planning/04` §1.10, `planning/07` §2.4 (lever caps), §3 and §4, `planning/08` §3.3, and
> `planning/09` A4 and §5. **APPROVED 2026-10-04 (his)**, with all five decisions at the end taken as recommended.
>
> **Split 2026-10-04 (his, decision 1):** `planning/05`'s Phase 2 is now two phases. This doc covers **the fictional
> company**: the cited dossier every scenario is set in. **Phase 2.5 `scenarios-and-wordings`**
> (`docs/phases/phase-2.5-scenarios-and-wordings.md`) covers the four scenarios, the objective wordings, the
> neutrality review and the development runs.
>
> Written before Phases 0.5 through 1.5 are built. **Lines marked *(rests on 0.5)* or *(rests on 1)* depend on what
> those phases measure or build.**

## What this phase is for

**The one realistic company the whole fictional experiment is set in, with a source on every number.** It is the
project's main attack surface after the methods page: a critic's first line will be "it's a toy company"
(`planning/01` §2.3, `planning/04` §1.10). The answer is a published dossier in which every figure cites a public
source or is marked plainly as an assumption.

It is also the experiment's biggest fixed input. Every one of the four scenarios, all five objectives and every
repeat sees the same dossier, as the cached prefix of the prompt (`planning/07` §4). A slant in the dossier is a
slant in every run, so it is written and reviewed on its own, before any scenario is written on top of it.

**The test of a good Phase 2:** a skeptical reader with a finance background can pick any number in the dossier and
find where it came from in under a minute, and finds nothing that reads as invented to make a point.

## What scoping found

1. **Rule zero reaches into the dossier's sources.** `planning/01` §2.2 lists SEC company financial data for "peer
   financial structure." Any peer set is a list of real companies. Rule zero says no real company's name, ticker or
   plant location goes in a tracked file, and the dossier's source list is a tracked file. A source line naming
   peers would break the rule the guard exists for, and a peer name the term file lacks would get through it.
   Decision 3.
2. **The dossier is shared by all four scenarios, so it has to hold what each of them needs.** The closure scenario
   needs a plant with stated economics; the AI scenario needs payroll by function; the R&D scenario needs
   uncommitted cash; every scenario needs a cap on every source (`planning/07` §2.4). Those are company facts, so they
   are written here. Phase 2.5 adds only the event and the options. Decision 5 settles whether the dossier is one
   document or one per scenario.
3. **A company name is a variable.** A name carries associations a model may react to, and a made-up name can
   collide with a real company the term file does not list, which the guard cannot catch. Decision 4.
4. **The instrument is drafted by the same model family it tests.** The dossier and scenarios will be drafted by
   Claude, and the main model is Claude. A critic can ask whether the text is written in a register Claude finds
   natural. It is a fair question, not a fatal one. The answer is a review by another vendor's model (the method
   `planning/08` used) and Nova Pro as the second model family. Decision 2 states it, so the methods page can.

## Delivers

In build order.

1. **The four source checks closed, before any figure is written** (`planning/01` §7 items 1-3, `planning/09` §5,
   `planning/04` §1.10):
   - which **Census AIES** tables give revenue per employee, payroll share and capital spending for NAICS 333, and
     their latest release;
   - the current **BLS Occupational Employment and Wage Statistics** release for the occupations the dossier uses
     (machinists, assemblers, engineers, and the functions the AI scenario names);
   - **Damodaran's** industry datasets: the current edition and the terms of use, which decide whether a figure is
     quoted or only cited;
   - whether the **SEC Financial Statement Data Sets** are current. Under decision 3 (a) this check may become moot;
     it is closed either way, with the reason.
2. **The dossier as data, then as text.** The figures live in one versioned data file. Each figure has a value, a
   unit, a source ID, and either the derivation (for example, "industry median times revenue") or the word
   *assumption* with a reason. The board-pack text is **rendered from that file**, so every number in the text
   traces to a row, and editing a number means editing its row. The rendered text and the data file are both hashed
   and committed.
3. **What the dossier contains:** the company as a board would see it on the decision date. That means the income
   statement and balance sheet in summary; revenue, margins, R&D, capital spending and payout set from industry
   medians; the workforce by function and occupation, with pay from BLS; five or six plants, by region only, each
   with its headcount and results, one of them underperforming (for the closure scenario); the cash position,
   including the uncommitted cash the R&D scenario draws on; environmental spending; the supplier spend; and the
   payout policy, which the downturn scenario holds fixed (`planning/07` §3.2). **It states a maximum for every lever
   that can be a source** (`planning/07` §2.4a): the R&D that exists, the payroll of each function, the cash
   available, the environmental budget, the payout, and the share of supplier spend that could plausibly be
   renegotiated.
   **And the redeployment opportunity for the AI scenario, in numbers** (`planning/07` §3.2 S1): the new work that
   exists, what retraining costs and how long until it pays back, each sourced or marked as an assumption.
4. **An assumptions table**, one place listing every figure that has no direct source, with the range it was chosen
   from and why that point in the range. He reviews it line by line. It is the dossier's most important part
   for an honest reader.
5. **The register:** a board pack. Numbers, units and plain labels, with no adjective about anyone's welfare or
   hardship and no adjective about shareholders' expectations (`planning/07` §9 items 1-2). One vocabulary
   throughout, with no euphemism from `planning/06` §3.3. About 6,000 tokens (`planning/03` §3.1).
6. **The realism read, by a reader that cannot run the experiment** (decision 2): another vendor's model, through
   OpenRouter as in `planning/08`, given the rendered dossier and asked what a director or analyst would find
   implausible, missing or slanted. The brief and the raw reply are kept beside the dossier as records, as `08a`
   and `08b` are. Claude verifies each point and he decides each change. The reader is never asked what a CEO
   should do.

## The rules this phase must not break

- **No official model sees the dossier before `prereg-v1`.** No main-model call and no Nova Pro call, as a decision,
  a probe or a review. Text review is done by a non-official model only. `planning/05` §2 forbids seeing the official
  model's decisions; this goes further, because there is no reason in this phase for an official model to read the
  dossier at all.
- **No decision is run on the dossier in this phase.** Development runs are Phase 2.5's, under its rules.
- **Rule zero, on sources too** (decision 3). No real company's name, ticker or plant location in the dossier, its
  data file, its source list or any record of how it was built. Plants are described by region.
- **Numbers come from sources, never from what they might make a model do.** A figure is chosen for being true to
  the industry, not for its likely effect on a decision. If a number is found to be wrong later, it is corrected,
  and the change is logged with its source.
- **The dossier is fixed once Phase 2.5 starts.** A later change is a logged change with a reason (format, clarity,
  neutrality or a factual correction). It is never made because of what a run did (Phase 2.5's change-log rule).

## Explicitly not in this phase

- **The scenarios, the objective wordings, the neutrality checklist on scenarios, any development run.** Phase 2.5.
- **Any harness change.** The dossier is data. Phase 2.5 extends the schema to the four scenario shapes.
- **Real-case dossiers and the retrieval pipeline.** Phase 5.
- **Any other company type.** After v1.0 (`planning/00` §6.1).

## Definition of done

1. **Every number in the dossier traces to a row in the data file**, and every row has a source or is marked as an
   assumption with its range and reason. Shown by a check that fails on any number in the rendered text that has no
   row.
2. **The four source checks are closed** in `KNOWN-GAPS.md` with sources and dates, and `planning/01` §7 is patched.
3. **A maximum is stated for every lever that can be a source**, and the redeployment opportunity is in numbers.
4. **He has reviewed the assumptions table and the rendered dossier line by line.**
5. **The realism read is done,** its brief and raw reply are committed as records, and every point it raised is
   marked confirmed, partly right or rejected, with the change made or the reason not.
6. **No real company's name, ticker or plant location appears** in any file of the dossier: the guard passes, and a
   manual read covers what the guard cannot (spellings it lacks, descriptions detailed enough to identify a firm).
7. **No official model was called.** `make check` and CI are green.

## Prerequisites

- **None from Phases 0.5 to 1.5 for the writing itself.** The dossier is data and text. *(rests on 1)* Its file
  format joins the experiment files Phase 1 hashes and builds into the image, so it follows Phase 1's layout.
- **His OpenRouter balance for the realism read** (`planning/08` cost $1.34 for a much longer read).

## Cost

**About $1, none of it on AWS.** The source checks and the writing cost nothing. The realism read is one call
through OpenRouter, which is his API wallet, outside the AWS credits. No Bedrock call is made. **`planning/03`'s
$80 ceiling counts AWS spend;** whether OpenRouter review calls count toward the project's total is recorded in the
cost ledger either way, so the full cost of the project is visible.

## The main model

Nothing in this phase depends on which model is main (Sonnet 4.6, fixed 2026-10-05). The dossier's length is far
above its caching minimum.

## Known risks

- **A public source does not exist for a figure the scenarios need** (the redeployment opportunity is the likeliest).
  Then it is an assumption, in the table, with its reason. A dossier with an honest assumptions table is stronger than
  one that hides its guesses.
- **The dossier slants by what it includes.** Giving the workforce three paragraphs and the payout one line is a slant
  with no adjectives in it. Mitigation: a length and detail balance check across stakeholder groups is part of the
  realism read, and of Phase 2.5's neutrality checklist (`planning/07` §9 items 3, 9).
- **Industry medians produce a company too average to be real.** Real companies are lumpy. Mitigation: where the
  data gives a range, the dossier may sit away from the median, with the point chosen in the assumptions table and
  never chosen for its effect on a decision.
- **Sources move.** Damodaran updates each January; BLS and Census release on their own schedules. The dossier records
  the edition and date of every source, and is never silently refreshed.

## Decisions for him

All five taken 2026-10-04 (his), as recommended. Each keeps its original framing under *Was:* as the record.

1. **DECIDED 2026-10-04 (his): (a), split.** This doc is Phase 2; Phase 2.5 is `scenarios-and-wordings`.
   `planning/05` status line patched. *Was:*
   **One phase or two.**
   - (a) **Recommended:** split into **Phase 2 `company-dossier`** (v0.2, this doc) and **Phase 2.5
     `scenarios-and-wordings`** (v0.2.5). The two halves are different kinds of work: one is research and data,
     the other is writing, method and development runs. The second is written on top of the first and should start
     from a finished, reviewed dossier, so a dossier fix does not force rewriting four scenarios. Each gets an
     IMPLEMENTATION doc written right before it. `planning/05`'s status line records the split.
   - (b) One phase, as `planning/05` has it.
2. **DECIDED 2026-10-04 (his): (a).** Claude drafts from the sources; he reviews every line; the methods page
   discloses the same-family question and its two answers. *Was:*
   **Who drafts the instrument's text** (the dossier here; the scenarios and wording templates in Phase 2.5).
   - (a) **Recommended:** Claude drafts, from the sources, and he reviews every line. The methods page says so,
     together with the same-family question (scoping finding 4) and its two answers: the review by another vendor's
     model, and Nova Pro as the second model family. The dossier is an instrument, not his voice, and the rule that
     public prose is his (`planning/00` §10) covers the README, the launch post and the site's words, not the
     stimulus.
   - (b) He drafts it, and Claude critiques. This removes the same-family question for the text, at the cost of much
     more of his time on the longest document in the project.
3. **DECIDED 2026-10-04 (his): (a), industry-level sources only.** `planning/01` §2.2 patched. *Was:*
   **Where the industry figures come from.**
   - (a) **Recommended:** **industry-level sources only**: Census AIES, BLS, and Damodaran's industry tables.
     Damodaran's tables already cover debt, cash and payout at the industry level, which is what the SEC peer data
     was meant to supply. No peer set means no list of real companies anywhere, so rule zero is met without relying on
     the guard. `planning/01` §2.2's SEC row is patched to "not used for the fictional company; kept for Phase 5."
   - (b) Also use SEC data for a peer set, aggregated by a script over an industry code, with the list of firms kept
     out of the repo. More granular, but it puts a list of real companies on the laptop and in the script's inputs,
     for figures the industry tables mostly already give.
4. **DECIDED 2026-10-04 (his): (a), no name.** The dossier says "the Company"; plants by region and number. *Was:*
   **The company's name.**
   - (a) **Recommended:** **no name.** The dossier says "the Company," as a board pack does internally; plants are
     named by region and number. That removes the association variable and the risk of matching a real firm.
   - (b) A made-up name, checked against company registries and the term file. More readable, at the cost of a
     variable and a check.
5. **DECIDED 2026-10-04 (his): (a), one shared dossier.** *Was:*
   **One dossier or one per scenario.**
   - (a) **Recommended:** **one shared dossier** holding everything a board would know on the decision date, with
     each scenario adding only its event and options. It is one document to source and review, one cached prefix,
     and every scenario is set in the same company, which is what "same company, only the objective changes" means.
     What it costs: a model in the AI scenario also sees the underperforming plant, which is true of any real board
     pack.
   - (b) One variant per scenario, each with only the facts that scenario needs. Less to read in each run, but four
     documents to source and keep consistent, four cache prefixes, and a weaker claim that the company is the same.

## Left for the IMPLEMENTATION doc

The exact tables and editions, from the source checks. The data file's format and the rendering template. The
dossier's outline, section by section. The decision date the dossier is set at. The fiscal-year convention. The
assumptions table's columns. The realism reader's model, chosen live, and its brief. The check that ties every number
in the text to a row. The order of the commits.
