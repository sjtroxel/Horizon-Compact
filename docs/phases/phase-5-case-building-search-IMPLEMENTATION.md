# Phase 5 — Case Building, search half: IMPLEMENTATION (v0.5)

> **IMPLEMENTATION doc, search half. Written 2026-10-15 (Opus), immediately before the search. APPROVED 2026-10-15 (his,
> about 3:50 PM CDT), all seven decisions in §8 as recommended, (a).** **Stage A built 2026-10-15; Stage B, the search, run 2026-10-16 on the rule date with no deviation (§11).** **Patched 2026-10-16 (his): §4.6.1, the case scenario
> is rendered from the shape's template and checked by re-render; Stage C step 8 split into 8a and 8b.** **Patched
> 2026-10-17 (his), after the independent reader's read: §4.6.2, the total in criterion 4 and a search hit
> that announces no decision.** **Patched 2026-10-17 (his), after the reader's read: §4.6.3, the headcount floor at criterion 4 is 167 as stated.** **Patched 2026-10-17 (his), after the reader's read: §4.6.4, a candidate's type is decided by §12.1 at criterion 4, with no move between lists.** **Patched 2026-10-19 (his), after the reader's read: §4.6.5, exploratory cases after the pre-registered rule found none; their build is planned in `phase-5-case-building-exploratory-IMPLEMENTATION.md`.** Sources: the Phase 5 scope doc (`docs/phases/phase-5-case-building.md`, its
> six decisions and dated notes), the code-half doc (`phase-5-case-building-code-IMPLEMENTATION.md`, all of it, as
> built), the Phase 5.5 scope doc, the protocol as tagged (`experiment/protocol/protocol-v1.md` §12, all of it, §14),
> `planning/07` §10, Phase 3.5 IMPLEMENTATION doc §16 step 6 and §24.2, the Phase 4 run log §6.9, `KNOWN-GAPS.md`'s
> OPEN entry "for Phase 5: the case mode's readers and wiring", and the code (`casebuild/`, `protocol/cases.py`,
> `providers/anthropic.py`, `infra/iam/`). Facts checked live 2026-10-15 are marked *(live 2026-10-15)*.
>
> **Rule zero.** This doc names no company, no candidate and no identifier, and neither does anything this half
> commits. Every case is called by its neutral label (§4.2) everywhere outside the private appendix, including chat
> summaries, handoffs and memory.
>
> **Vocabulary**, as in the code half: an **8-K** is a "current report" filed within four business days of a
> significant event, sorted into numbered **items**; **EDGAR full-text search** (EFTS) is the SEC's search over
> filing text; an **accession number** is a filing's permanent ID; a **10-K** is the annual report, a **10-Q** the
> quarterly one. A **cut-off** is the day before a decision's first public disclosure.

## 1. Where things stand on 2026-10-15

- **Phase 4 is closed.** Its results files were committed in `6d1ef6a` on **2026-10-15** (09:17 CDT), the reveal,
  and the close followed in `fe5c546` the same day.
- **So the search date is 2026-10-16, by rule.** Protocol §12.2: "the search runs once, on the day after the
  official grid's results are committed." The window is **2026-08-01 through 2026-10-15**; the fallback month is
  **2026-07-01 through 2026-07-31**, held apart (§12.2). *No document recorded this date until this one* (a grep of
  `docs/` and the protocol for "rule date", "search date" and "day after" found only the rule, not the date). The
  date is not a choice, and this doc does not treat it as one. What is a choice is what happens if the search cannot
  run tomorrow (decision 1).
- **The code half is built** (`4cd6559` to `8271785`, 2026-10-11): the EDGAR client, the cut-off filter, the document
  set, the splitter, figures from XBRL, the extraction request on a fake provider, anonymize and scale, options,
  assemble, `hc case foreshadow`, `hc case hashes`, and the search runner with the selection log. **Not built, by
  design:** `hc case search` and `hc case build` (they need the rule date and a model route), the case scenario
  file, the case record writer, the recognition-probe runner, the gate's real readers, the independent reader.
- **The model set is fixed** (`prereg-v1`): **Haiku 5.5** (`main`, Anthropic's API) and **`gpt-oss-120b`**
  (`second_family`, OpenRouter, pinned to DeepInfra). The scope docs' "Sonnet 4.6" and "Nova Pro" lines are stale
  (ROADMAP decision history, 2026-10-11).
- **Spend to date:** at most about **$28** cumulative, every pot (Phase 4 run log §6.9). The Anthropic prepaid credit
  read **$15.95** on 2026-10-15; his OpenRouter balance **$5.36**; no AWS cash ever.

## 2. What this half delivers

The scope doc's Delivers 1-9, for every case, before any case's decision runs (that is Phase 5.5):

1. **The projection check** (Delivers 1), before any case work: §6.
2. **The search, once, on 2026-10-16** (Delivers 2), through the three channels of protocol §12.3, by
   `hc case search`.
3. **The selection log** (Delivers 3), every candidate and criterion, with the independent reader on every
   rejection under criterion 3, 4 or 5.
4. **Identifiers into the guard** before any work on a case (Delivers 4).
5. **Each case's dossier** (Delivers 5-6), by `hc case build` from pre-cut-off documents only.
6. **Each case's scenario file** by the case scenario rule (§4.6, decision 4), with the foreshadowing check and the
   neutrality checklist on both texts.
7. **Each case's rubric** (Delivers 7), read by the independent reader, committed as a hash in `case.lock` and pushed
   before the case's first probe.
8. **The recognition probe** (Delivers 8): three calls per model per case, as Fargate tasks, coarsened and re-probed
   once on a failure.
9. **The freeze commit** (Delivers 9).

**Not in this half:** any case's decision runs, the matching, the memo name scan, the re-identification check and
publication (Phase 5.5); wiring the case mode into `hc sweep launch` (Phase 5.5: the gate's readers are built here
and proved on the probes, the launch wiring there).

## 3. What writing this doc found

1. **The search date is tomorrow, and nothing had said so** (§1). Everything in Stage A (§5) is either done tonight or
   done tomorrow morning before the search. The search itself takes minutes; the work after it takes days, and none
   of that work has a date by rule.
2. **A case has no scenario file, and the protocol does not say where its facts come from.** The harness decides on a
   scenario file (`experiment/company/scenarios/s3.toml` is the model: a total, lever caps, the option texts with
   their economics). Protocol §12.6's heading covers "the dossier and the scenario text", and its first bullet's
   source rule ("only documents dated before the cut-off") is written about the dossier's documents. **A real
   closure's facility headcount, the size of an AI-attributed cut and the cost of a funded program usually first
   appear in the very document that discloses the decision**, after the cut-off by definition. Read strictly, most
   cases cannot be posed at all; read loosely, the person writing the scenario (who knows the outcome and the grid's
   results) decides which facts go in. **This is the largest judgment left in the phase.** It is settled here, before
   any candidate is seen, by a mechanical rule (decision 4). Written today it is a rule chosen without knowing a
   single candidate; written on case day it would be a choice made per case.
3. **The fictional scenarios' lever caps are realism assumptions** (29 movers at most, a buyer keeping 171). A real
   filing rarely states such a limit before the decision. A cap invented for a case would be a figure the writer
   chose; a cap copied from the fictional company would import its assumptions. Decision 4 proposes: **a cap with no
   pre-cut-off figure equals the scenario's total** (a limit no one stated is not imposed).
4. **The extraction model's training data must end before the window.** A model that learned of a case's decision in
   training could write the outcome into a summary of pre-cut-off text, which no cut-off filter can catch. Protocol
   §12.6 bars only the official models. **Claude Sonnet 5.5's training data cutoff is June 2026** *(live 2026-10-15,
   Anthropic's models overview)*, before the fallback month and the window. Some newer models fail this test (an
   OpenAI model released 2026-09-29 is the newest on OpenRouter *(live 2026-10-15)*, its cutoff unstated). Decision 2.
5. **The probe cannot run on the laptop without breaking a deliberate rule.** Haiku 5.5's key exists only in SSM
   (Phase 1 §21a: "no laptop copy of the key exists"), so the probe runs as a Fargate task. The task role reads and
   writes only `development/`, `pilot/` and `official/` (`infra/iam/task.json`), so a private `cases/` prefix needs
   a Terraform change, and the case content needs a way into it. The gate's order check reads the first probe
   object's `LastModified` from S3, so S3 is where the probe records must be anyway. Decision 5.
6. **Probe records hold the models' answers, which can contain real company names.** They are private forever: never
   under a prefix the publish path reads, never in a committed manifest. §4.8 fixes the prefix.
7. **A probe answer's pass or fail is a laptop judgment.** It needs the private term list and one human read
   (§12.8), neither of which belongs in the container. So the container writes each call's answer; a separate verdict
   object, written once from the laptop, carries `passed`. `ProbeRecord.last_modified` is the call object's time,
   which is the one the order check needs (the first time a model saw the case).
8. **The selection log is run from Python, not a command.** `SelectionLog` enforces order, reasons and reads, but
   nothing records a result from the terminal. A small `hc case log` command is needed, or every result is typed
   into a scratch script.
9. **His $5 OpenRouter cap** (Phase 3.5 decision, 2026-10-09: "OpenRouter capped at $5 in aggregate for every
   remaining use") has about $1 used (the 2026-10-09 to 10-12 tally, about $0.38, and Phase 4's $0.59). This half
   and Phase 5.5 together project about $2.10-3.10 more (§6), inside it. The cap stays his.
10. **Phase 3.5 §24.2 carried the probe runner to Phase 5.5**, but the scope doc puts the probe in Phase 5 (Delivers
    8), before the freeze. The scope doc governs; §24.2 gets a dated note.
11. **The EFTS reply's shape has never been seen** (code half §7 step 7). One read-only request settles it before the
    search. **It must not use dates inside July to October 2026**, so that no one sees a candidate before the
    search; a week in 2025 serves.
12. **`prepare_case` takes its seed function as a parameter for tests** (code half §7 step 6): `hc case build` must
    not expose it, or "never chosen" is a promise rather than code.

## 4. The design

### 4.1 The run order, one case at a time within a type

Selection is by disclosure order, and criterion 5 (the probe) needs a built dossier, so a type's candidates are
worked in order: the first that passes criteria 1-4 is built and probed; if it fails, the next. **Building ahead
is allowed** (a second candidate's dossier while the first is being probed) because it changes nothing: whichever
passes first in order is the case. **A built candidate that is not selected is logged as passed and not a case**,
and its files stay in the appendix.

For one candidate, in this order and no other:

1. Criteria 1-4 in the selection log (§4.3); a rejection on 3 or 4 goes to the reader before the next candidate.
2. **His:** the candidate's identifiers into the private term file; Claude writes the case's term list in the
   appendix (the same names, with roles, for `anonymize`).
3. `hc case build`: documents, extraction, prepare; his flag review; `assemble_case`.
4. The scenario file by the case scenario rule; `hc case scenario check`.
5. The rubric, from post-event filings; the reader reads its mapping; disagreements to him.
6. The foreshadowing check on dossier and scenario, from the rubric's outcome terms; the neutrality checklist on the
   scenario; every hit removed or justified in writing.
7. `hc case lock`: `experiment/cases/<label>/case.lock` (hashes only); **his commit and push**; CI's run on that
   commit is the time the gate reads.
8. Content to the private S3 prefix; the probe as a Fargate task per model; his read; verdicts.
9. Pass on every model: criterion 5 passes, and the case is selected if it is within its type's first k. Fail: the
   coarsening procedure of §12.8, a new `case.lock` with `probe_set = 2`, commit, push, re-probe once. A second fail:
   criterion 5 fails, and the next candidate starts at step 1.

### 4.2 Labels

**A case's label is its candidate id** from the search (`closure-01`, `retool-03`, `ai-02`; a fallback candidate
`closure-f01`): already neutral, already unique, already in the private candidate list, so there is no second
mapping to keep. It is used everywhere outside the appendix. The search's own files live under the appendix label
`search`.

### 4.3 The selection log, from the terminal

`hc case log <type> show | record <id> <criterion> pass|fail --reason ... [--disclosed YYYY-MM-DD] |
read <id> <criterion> agree|disagree [--resolution ...] | public`. *(Amended 2026-10-16, the step 9 review,
decision 7: `read <id> <criterion> [--resolution ...]`, the verdict taken from the reader's reply file; §11.)* Each
call loads the newest `selection-log-<n>.json`, applies one `record` or `record_read` (which enforce the order, the reasons and the
fallback rule), and writes the next version with its public view. The log holds names, so it lives only in the
appendix; `public` prints the view without them.

**The first-disclosure check (criterion 1 in the code, §12.2's check before §12.4's five)** is done the same way for
every candidate, and the log's reason lists what was searched: (a) EDGAR full-text search on the filer's CIK for the
facility, program or workforce action, from 2025-01-01 to the candidate's filing date; (b) a web search for the
company and the action, for news, a press release or an earnings-call report; (c) the candidate filing's own text,
for "previously announced" or a reference to an earlier date. The earliest dated mention is the disclosure date. A
mention before the window fails (before the fallback month, for a fallback candidate).

### 4.4 `hc case search`

`hc case search --date 2026-10-16`: refuses any other date unless `--deviation "<reason>"` is given (decision 1),
refuses to run twice (the appendix's `search/candidates.json` is write-once), runs `run_search` with the EDGAR
client and his User-Agent, writes `candidates.json`, the first `selection-log-1.json` and its public view, and prints
counts per type and pool only. The window's end is **2026-10-15** however the date flag reads (decision 1 (a)).

### 4.5 `hc case build`

`hc case build <label> --cutoff YYYY-MM-DD --shape S1|S2|S3|S4`. The CIK comes from `search/candidates.json`, never
the command line. In order: `build_document_set` and `write_sources`; `build_section_inputs` for the shape; the
extraction on the fixed model (decision 2) through `run_extraction`; `prepare_case` with `scale.new_seed`, which the
command cannot replace. `hc case assemble <label>` runs `assemble_case` once the reviewed-flags file exists.

**The extraction model gets its own entry in `models.toml`**, role `extraction`, which every sweep, probe and
official path refuses (a new tripwire test: no `extraction` model may be planned, probed or locked), and which
`hc case build` requires. Its settings (route, thinking off, `max_tokens`) are fixed in that entry. **That entry,
`extract.COMMON`, `SECTION_INSTRUCTIONS` and their hash are committed before the first real document is fetched**
(§12.6); each case's `build.json` records that commit and the hash.

**A split the splitter refuses** is done by hand (code half §3 finding 6): Claude proposes the item boundaries from
the HTML, he checks them, and they are recorded in the case's hand-boundaries file, which `build.json` hashes.

### 4.6 The case scenario rule (decision 4 (a))

The case's `scenario.toml` is written in the fictional scenario's own format and **keeps everything of its shape's
fictional scenario except the facts**: the role line, the rule, the unit, the lever keys, labels and kinds, the
choice keys, the extra rules, the instruction and headings, word for word. The facts come only from these places:

1. **The decision's subject and size may come from the first-disclosure document:** which kind of thing is decided
   (a facility, a program, a part of the workforce), at the level of a product category and a census region, and its
   size as the scenario's total (the facility's headcount, the roles affected, the program's annual cost). Scaled by
   the case's factor and anonymized like the dossier. **Nothing else from that document:** not which option was
   taken, not a charge, a timing, a severance figure or any other economics.
2. **Every other figure, including every option's economics, comes only from pre-cut-off documents.** Where any
   option has none, every option is described without figures alike (§12.6, already the builder's rule for section
   7).
3. **A lever's cap with no pre-cut-off figure equals the total.** A stated cap is used only where a pre-cut-off
   document gives it.
4. **A total that neither the disclosure nor a pre-cut-off document gives** fails criterion 4 ("maps onto a scenario
   shape"), and that rejection goes to the reader like any other.
5. **The option texts** use the fictional shape's sentences with the case's figures, or, where the case has none,
   the same sentences with the figures removed and nothing added.

~~`hc case scenario check <label>` checks the file against its shape: same keys, kinds, labels, rules and wording
outside the facts; every cap either equal to the total or listed with its source in `build.json`; no digit outside a
figure; and no figure absent from the case's figure sources.~~ *Superseded by the patch below: `build.json` is written
once by `prepare_case` and cannot take a later list, nothing recorded the scenario's figure sources, and rule 5
cannot be applied clause by clause (taking a figure out of "about $4,566 a person" leaves broken text).* **The reader
reads every case's scenario file for neutrality** (decision 4), given the shape and the sources, not the rubric.

#### 4.6.1 Patch 2026-10-16 (his, about 12:46 PM CDT): the scenario is rendered, not written

Found while building step 8 (Sonnet stopped on it; Opus reviewed). The case scenario is made **the way the fictional
ones are: the shape's own template, rows, a render, and a check that re-renders and compares byte for byte**
(`scenarios/render.py`, `hc scenarios check`). Rules 1-5 above stand; this says how they are carried out.

1. **The template is the shape's `experiment/company/scenarios/sN.source.toml`, unchanged.** Every word of the case
   scenario comes from it; nothing is written per case except rows.
2. **The rows: `scenario-figures.toml` in the case's appendix folder,** written by Claude (Opus) with him at Stage D.
   One row per placeholder the case can fill, keyed by the template's row id: the **unscaled** value, the fictional
   row's unit, a `scale` of `dollars`, `heads` or `none`, and a source. A source is `pre_cutoff` (an accession number
   in the case's `sources.json`, admitted by `cutoff.admit`, and a locator) or `first_disclosure` (a locator; its date
   is the selection log's `disclosed` date), **and only the total may be `first_disclosure`** (rule 1). A cap row may
   instead say `equals_total = true` (rule 3). `scale = "none"` on a dollar row needs `per` (a head, an hour): only a
   ratio of two scaled quantities escapes scaling (protocol §12.6).
3. **Label rows** (`plant_6_no` and the like) take the fictional value. They are names in the wording, not facts.
4. **Derived rows** use the fictional row's formula from `scenario-figures.toml`, and are filled only when every row
   the formula names is a case row. The menu heading's sum of caps is always derivable, since every cap is a row.
5. **Scaling** by `build.json`'s factor with `scale.py`'s functions, as the dossier: dollars to three significant
   figures, heads to the nearest 5. **A heads figure under 100 reads "fewer than 100" in the text. A total under 100
   fails criterion 4** (the protocol forbids stating it, and the decision needs a whole number), and the rejection goes
   to the reader. **A cap under 100 is treated as unstated and equals the total** (rule 3's reasoning: a limit that
   cannot be stated is not imposed), recorded.
6. **Rule 5, mechanically: a sentence holding a placeholder with no row is dropped whole.** A sentence ends at `.`,
   `?` or `!` followed by a space, a line break or the end of the field. A paragraph left empty is dropped. A lever's
   `detail` or `note` left empty is omitted. **If any option text drops a sentence, every sentence with a placeholder
   is dropped from every option text** (protocol §12.6's equal treatment); for a shape with no choice (S1), the
   levers' `detail`s are its options and the same holds across them. An option text, the role, the menu heading or
   the instruction left empty is a render refusal.
7. **A rule whose numbers have no rows** (S2's joint cap) is omitted with the sentences that describe it, by 6, and
   recorded: a limit no one stated is not imposed.
8. **`hc case scenario render <label>`** writes `scenario.toml` (the harness's format, the fictional header replaced by
   a case one) and `scenario-render.json` (rows used, sentences dropped by field, rules omitted, caps set to the
   total, the factor and `build.json`'s sha256), each once. The rendered data must pass the `Scenario` model.
9. **`hc case scenario check <label>`** re-renders in memory and compares with `scenario.toml` byte for byte, and
   re-checks every source (admitted, in `sources.json`, the total alone first-disclosure). It prints failures by
   criterion and never a name, a figure or an excerpt. A pass is what `hc case lock` requires.

**What this costs:** a dropped sentence can take context with it (S3's first sentence holds both the headcount and
the payroll). The total still stands in the menu heading and the instruction, and the reader's neutrality read of
every scenario is the backstop. **The alternative,** figure-free wordings of every sentence written for all four
shapes now, was declined: it is prose chosen after the candidate list exists.

#### 4.6.2 Patch 2026-10-17 (his, about 4:54 AM CDT; drafted by Opus): the total in criterion 4, and a search hit that announces no decision

*ADOPTED 2026-10-17 (his), after the independent reader's read (below) and with its two changes to B answered.* Found at Stage D step 11 (`KNOWN-GAPS.md`, both OPEN 2026-10-17 entries on rules),
before any criterion 4 result and before any retool or ai row was recorded. Each rule is judged on its own terms,
not by which candidates it admits.

**A. The total is part of criterion 4, and every rejection on criterion 4 is still read.** The fault: §4.6 rule 4
and §4.6.1 item 5 fail criterion 4 on a missing or too-small total, but the reader's brief defines `maps_to_shape`
by shape alone, so the reader disputes, the rejection does not stand (§12.4), and the render refuses a case the log
says passed.

1. **Criterion 4 is checked in two parts, in order,** recorded as one result whose reason says which part failed:
   **(i) the shape**, by §12.5's rule on the first-disclosure document; **(ii) the total**: the figure the shape's
   template names as its `total` (S1 `s1_roles`, S2 `s2_shortfall`, S3 `hc_p6`, S4 `s4_annual`), stated for the case
   under §4.6 rule 1 or 2, or derived from case rows by the template's own formulas (§4.6.1 item 4), and, for a
   headcount, 100 or more after scaling (§4.6.1 item 5).
2. **Each total is the quantity the template's text says it is, and nothing near it:**
   - **S1:** the number of roles whose work the document says AI or automation software takes over.
   - **S3:** the number of employees at the facility named.
   - **S4:** the program's stated annual cost.
   - **S2:** **the fall in operating income the company expected before acting, from lower revenue,** as a dollar
     figure, in operating income as reported (the measure `op_income_fy0` is). The template says so in sentences
     with no placeholder, so they are in every S2 scenario: "A downturn in the industries the Company's customers
     work in is cutting orders", and "Before any decision, operating income would therefore fall by" the total.
     **Not** a savings or cost-reduction target: that is the size of the company's response, which rule 1 keeps
     out, and as the total it would build the company's choice into the problem (the line "accepting lower
     operating income" would be zero for the company by construction, and the scenario would state a fall no
     source states). **Not** a charge (rule 1), an adjusted measure, a percentage, or an expected fall in revenue
     alone, unless the template's formulas derive the total from it with case rows.
   A figure that is not the template's quantity is not the total, however close.
3. **Where it is looked for, by rule:** the first-disclosure document first; if it is not there, **every document
   of the §12.6 set for the case's cut-off**, fetched before criterion 4 is recorded by a fetch with no extraction
   and no key (`hc case documents <id>`, new, refused until the criteria before 4 are met; it writes `sources.json`
   exactly as the build would, so the build reuses it). In each document, every paragraph holding the subject as
   the first-disclosure document names it (the facility's name or place; the program's name; for S1 and S2, the
   action's own words), and, for S2, every paragraph holding "operating income" together with "expect",
   "anticipate", "outlook", "guidance" or "forecast".
4. **A rejection on either part goes to the reader** (§12.4 unchanged). Its material is the first-disclosure excerpt
   as now, and, for a rejection on the total, **`total-search.txt`**: every paragraph item 3's search found, each
   under a line naming its document by form and filing date, then the list of every document searched and the
   terms used. Both are placed by rule and saved before the result is recorded. A rejection for a stated total
   under 100 after scaling is read the same way: the material says so, and the reader judges only whether that
   figure is the total (the arithmetic is not a judgment).
5. **The brief's `maps_to_shape` gains the total** (the text below). A "pass" quotes, in its reason, the sentence
   that states the total. A pass disputes the rejection (§12.4): the candidate goes on, the quoted figure becomes
   the total row with its source, and his resolution is logged beside it.
6. **What no one reads:** a total in a part of a document no search term reached. The limit is stated on the
   methods page with the terms.

**The brief's new `maps_to_shape` text** (replacing the present paragraph; the other two criteria unchanged):

> maps_to_shape: Two parts, and both must be met. First, the shape: the excerpt maps onto one of four decision
> shapes. Apply them in this order; the first that matches wins. 1. S1: a workforce change the document attributes
> to AI or automation software. 2. S3: a facility named for closure or sale, with or without new capacity elsewhere
> (on retool when new or converted capacity is named). 3. S4: a multi-year program of stated annual cost, funded or
> declined. 4. S2: a restructuring with workforce or cost reductions and no facility named. An excerpt that matches
> none of the four fails this criterion. Second, the total: the material states, for that shape, the one figure the
> decision is about. S1: the number of roles whose work the document says AI or automation software takes over. S3:
> the number of employees at the facility named. S4: the program's annual cost. S2: the fall in operating income the
> company expected before acting, from lower revenue, as a dollar figure; a savings or cost-reduction target, a
> charge, an adjusted measure, a percentage or an expected fall in revenue alone is not it. The material for the
> total is the excerpt and, if you are given one, a search of the company's earlier filings. If the material says a
> stated total was rejected as too small after the study's scaling, judge only whether that figure is the total.
> "pass" means both parts are met: give the shape, and quote in your reason the sentence that states the total.
> "fail" means either part is not met; say which.

**B. A search hit that announces no decision** (a risk factor, forward-looking boilerplate, capital-spending
commentary, a contract's covenant, another company's plans) **is recorded like any candidate and fails criterion 3,
read.**

1. **The first-disclosure check is done as §4.3 says, on the passage's subject** (what the matched passage is
   about, in its own words, whether or not it reads as a decision), so that the date stands if the reader later
   disputes criterion 3. An earlier mention before the window fails it, as now (this is where "previously
   announced" falls). With none, the earliest dated mention is the filing itself, and its date is the disclosure
   date, **exactly as for any candidate whose own filing is its earliest mention** (§12.2 dates by first public
   disclosure; it does not say a first disclosure cannot fall on a filing date). The reason says the passage
   announces no decision in Claude's reading, which criterion 3 then records.
2. **Criteria 1 and 2 as now; criterion 3 fails,** "no decision announced", and is read like any criterion 3
   rejection. **The brief is unchanged:** `real_decision` already requires that "the excerpt describes a real
   decision with real alternatives, made by the company".
3. **The excerpt is Stage D step 11's unit:** the whole item of the current report, or the whole exhibit, that holds
   the matched phrase, never a paragraph picked from it. Over the 200,000-character limit, it is cut at paragraph
   boundaries, in rings: every paragraph that holds the matched phrase; then, for every match at once, the one
   paragraph before and the one after; then the second before and after; and so on, stopping before the first ring
   that would pass the limit (a ring is added whole or not at all). Kept paragraphs are sent in document order, a
   line `[...]` marking each gap.

*The independent read (2026-10-17, Gemini 3.1 Pro, $0.126; `evidence/phase-5/patch-4.6.2-review-raw.md`):* **A,
adopt as written. B, adopt with two changes, both answered:** (1) "dated by the filing date" read as contradicting
§12.2's "never its filing date": answered by rewording B.1, not by a deviation, since the date is the first-disclosure
check's result like any other and that check now runs on the passage's subject; (2) the cut rule at the limit was
not mechanical with several matches: replaced by the ring rule in B.3.

*Declined:* for A, recording the total as a lookup the reader does not read (`KNOWN-GAPS.md`'s option (a)): it
narrows §12.4's "every rejection on criterion 3, 4 or 5 is read", a sentence of the tagged protocol, so it would be
a reported deviation, and the part that decides most cases (whether a stated figure is the total) is a judgment.
Leaving it (option (c)) logs criterion 4 as passed for cases that cannot be rendered. For B, failing the hit at the
first-disclosure check: a judgment that removes most of a type's list would never reach the reader.

**What it costs.** A: an S2 case needs a stated expected fall in operating income, which many restructurings do not
give; the closure type may fall short, and a shortfall is reported (§12.1), never filled. A total rejection's read
carries more material (likely a few cents). B: one read per no-decision hit, likely tens across retool and ai, at
about $0.006 each. **Build work before criterion 4** (Stage D step 11a): the brief's paragraph; `total-search.txt`
in `material.py` for `maps_to_shape`; `hc case documents`; tests. **The brief changes after its first read**
(closure type, `real_decision`; that text is untouched): logged in §11 as a change to the instrument, with this
reason.

#### 4.6.3 Patch 2026-10-17 (his, about 11:55 AM CDT; drafted by Opus): the headcount floor at criterion 4 is fixed

*ADOPTED 2026-10-17 (his, about 12:15 PM CDT), after the independent reader's read (below): its changes 2 to 4
taken; change 1 answered as a stated interpretation, his decision.* *Dated note, 2026-10-19: in the exploratory record
only, §4.6.5 step 1 sets the S3 floor at 50, states a scaled S3 total under 100 as a number, and takes an S3 total
only as the plant's headcount; the pre-registered record keeps this patch as written.* Found in the Opus review of step 11a (§11), before any S1 or S3 total was looked for (`KNOWN-GAPS.md`, OPEN
2026-10-17, the headcount floor). Judged on its own terms, not by which candidates it admits: no headcount total of
any candidate has been read.

**The fault.** §4.6.1 item 5 and §4.6.2 A.1 fail criterion 4 on a heads total "under 100 after scaling". The factor
is drawn by `hc case build`, which refuses until criterion 4 is met, so for a stated total from 63 to 166 the result
depends on a draw that has not happened, and criterion 4 cannot be recorded in the log's order.

**The rule.**

1. **Part (ii) of criterion 4, for a headcount total (S1 `s1_roles`, S3 `hc_p6`), passes at 167 or more, as stated
   or derived (§4.6.2 A.1), unscaled.** 167 is the least whole number that every factor in protocol §12.6's range
   scales to 100 or more: the range's low end is 0.6, the render compares the scaled value before rounding
   (`scale.py`), and 167 x 0.6 = 100.2 while 166 x 0.6 = 99.6. If that range were ever changed, the floor is 100
   divided by its low end, rounded up; it is not changed for any other reason.
2. **This replaces "100 or more after scaling" in §4.6.2 A.1 and "a total under 100 fails criterion 4" in §4.6.1 item
   5, for criterion 4.** The rest of item 5 stands: any heads figure under 100 after scaling reads "fewer than 100",
   and a cap under 100 after scaling equals the total. The render's refusal of a total under 100 after scaling stays
   as a backstop; with the floor, it cannot fire on a case that passed criterion 4.
3. **How a stated total is read, for every shape** (it was open for all four): a figure given as "about",
   "approximately", "roughly", "more than", "over" or "at least" a number is that number; **a range is taken at its
   low end** (a figure the source states, and the one the floor is safe on); a figure given only as an upper bound
   ("up to", "as many as", "fewer than") states no total. The number so read is the total row's unscaled value.
4. **The reader is told the floor, and nothing about the rejection.** The rejection read starts blind (§4.9;
   `material.py` sends no reason and no result), so the floor goes in the brief, where it applies to every read
   alike, and the reader applies it. **`total-search.txt` carries no note of why the case was rejected**; the 11a
   "too-small note" (A.4, §11) is dropped. §4.6.2 A.4's last sentence ("A rejection for a stated total under 100
   after scaling is read the same way ...") is replaced by this item.
5. **The brief's `maps_to_shape` paragraph changes in three places** (the rest as §4.6.2 adopted it):
   - after "S3: the number of employees at the facility named.", add: **"For S1 and S3 the total must be 167 or
     more."**
   - after "... or an expected fall in revenue alone is not it.", add: **"A figure given as about, approximately,
     more than or at least a number is that number; a range is taken at its low end; a figure given only as up to
     or fewer than a number states no total."**
   - **remove** "If the material says a stated total was rejected as too small after the study's scaling, judge
     only whether that figure is the total."
   - "quote in your reason the sentence that states the total" becomes **"quote in your reason the sentence that
     states the total or, if the total is worked out from several figures, the sentences that state them"**.
   Logged in §11 as a change to the instrument. No read has used the changed sentences: closure-02's read was on
   criterion 3, and no criterion 4 read has been made.

**Why not the others.** *Drawing the factor at `hc case documents`* keeps §4.6.1's words, but makes a case's admission
depend on a random draw. The factor exists to keep a case from being identified by its figures, not to choose cases;
under it, two candidates with the same stated total could be admitted and rejected by chance. It also moves the draw
out of the build, whose code says nothing before it can supply one. *Recording part (ii) on the stated figure and
leaving the floor to the render* logs criterion 4 as passed for a case the render then refuses, the fault §4.6.2 A
was made to remove.

**The protocol, read (the reader's change 1, answered; his decision 2026-10-17).** Protocol §12.4 says "Each case's size
beside the fictional company's (revenue and headcount, scaled) is reported, and never used to choose." The reader
reads the floor as using size to choose, and asks that the patch be reported as a deviation. **Answered as a stated
interpretation, not a deviation:** that sentence is about the company's size (its revenue and headcount, set beside
the fictional company's), and it forbids choosing cases by how big the company is. The floor is on the decision's
total, the figure the scenario is about, and it follows from §12.6's own rule that a scaled headcount under 100 is
stated as "fewer than 100": a scenario whose decision is a number of people needs that number, and the template
states it as one. The floor was already in force (§4.6.1 item 5, which the reader saw in the §4.6.2 read without
raising this); this patch only moves it to the figure as stated. The interpretation, the reader's objection in its
words and this answer are given on the methods page beside the rule, so a reader of the results can judge it.

*The independent read (2026-10-17, Gemini 3.1 Pro, $0.170; `evidence/phase-5/patch-4.6.3-review-raw.md`):* **adopt
with four changes.** It confirmed 167 against the range and the code, and the reasons for declining the alternatives.
(1) Report the floor as a deviation from §12.4's "never used to choose": answered above as a stated interpretation (his). (2)
The brief's "judge only whether that figure is the total" steers the reader and does not tell it the floor, so a
reader finding 150 would pass and wrongly dispute: taken (items 4 and 5). (3) A derived total has no one sentence to
quote: taken (item 5). (4) Ranges and approximations: taken (item 3).

**What it costs.** Totals from 100 to 166 are rejected even where a high draw would have scaled them past 100 (and
totals from 63 to 99 that only a high draw would have admitted). A total given only as an upper bound is rejected on
every shape. No code: the brief's paragraph and its test change; `scenario.py`, `scale.py` and `material.py` are
untouched.

#### 4.6.4 Patch 2026-10-17 (his, about 4:55 PM CDT; drafted by Opus): a candidate's type is decided by §12.1, not by the search that found it

*ADOPTED 2026-10-17 (his, about 5:15 PM CDT), after the independent reader's read (below): its changes 1 to 4 taken;
the draft's move of a candidate to another list is dropped.* *Dated note, 2026-10-19: in the exploratory record only,
§4.6.5 step 1 item 1 sets item 2 below aside (one list per type); the pre-registered record keeps it.* Found at Stage D step 11, at closure-16: the first
closure candidate whose first-disclosure document names a facility for closure **and** moves its production to a
facility the company is building. **Written after closure-16's criterion 4 total was seen** (it would pass on the
closure list): the rule was chosen knowing what it does to that one candidate, which is why it was read before
adoption and judged on its own terms. It rejects that candidate; no other recorded row is changed by it (below).

**The gap.** Protocol §12.1 defines the types: "a closure with production moved to a new facility the company is
building counts as retool", and the ai type is "an AI-attributed workforce change". §12.3 finds candidates by three
query channels, one per type, and the selection log gives each candidate the type of the channel that found it. No
rule said what happens when the two disagree. §12.5's S3 line says the same from the other side ("on retool when new
or converted capacity is named").

**The rule.**

1. **§12.1's definitions decide a candidate's type, on its first-disclosure document; a candidate whose type is not
   its list's fails criterion 4 on that list** (part (i), with the shape, read off the same document). A stated
   interpretation of §12.1 and §12.5, not a deviation: the channels of §12.3 are how candidates are found, the
   definitions are what the types are. The type of each shape:
   - **S1** (a workforce change the document attributes to AI or automation software): **ai**;
   - **S3**: **retool** when the named facility's production moves to capacity the company is building or
     converting; **closure** otherwise (a closure or sale whose production stops, or moves to capacity that is
     neither new nor converted);
   - **S2**: **closure**;
   - **S4**: no type is read; it keeps its list's.
2. **No candidate moves to another list.** It fails on its own and is finished there. Each list stays what its own
   channel returned, so no list's candidates depend on how far another list's checking went (the reader's change 1:
   a candidate checked only because the candidates before it on its first list failed would otherwise enter a second
   list by that accident, and a late arrival with an earlier date could displace a case already built).
3. **The read stays blind** (§4.9): the material does not name the list. The reader gives, with a `maps_to_shape`
   pass or cannot_tell on S1, S2 or S3, the type the excerpt shows (`"type"` in its reply); the log compares it
   with the row's type. **A pass whose type is not the row's agrees with the rejection** (the candidate fails on
   that list either way); any other reading counts as before. A reply saved before this patch carries no type and
   is read as it was.
4. **The brief's `maps_to_shape` paragraph gains, after "An excerpt that matches none of the four fails this
   criterion.":** "With the shape, give the type of decision the excerpt describes: "ai" for S1; for S3, "retool"
   when the facility's production moves to capacity the company is building or converting, and "closure"
   otherwise; "closure" for S2; null for S4." The reply format gains `"type"`. Logged in §11 as a change to the
   instrument. No read so far is affected: no earlier criterion 4 rejection rested on type.

**Rows already recorded.** Every closure row checked before this patch was read again for the test (closure-01 to 15
and closure-29): none moves production to capacity being built or converted, and none attributes a workforce change
to AI; every one is S2 or S3 closure. The two S3 rows concentrate production at existing plants or transfer
equipment. No recorded result changes. No retool or ai row has been recorded. On the ai list, an S2 (a workforce cut
not attributed to AI) now fails as closure: that follows from the same definition and is stated here so it is not
found later.

**Why not the others** (his choice of three, 2026-10-17, then the reader's change 1). *Moving the candidate to its
type's list* (the draft) breaks §12.4's order, as item 2 says. *Keeping it on the closure list* reads §12.5's "with
or without new capacity elsewhere" over §12.1's plain words, and is the reading that admits the one candidate already
seen to pass.

*The independent read (2026-10-17, Gemini 3.1 Pro, $0.188; `evidence/phase-5/patch-4.6.4-review-raw.md`):* **adopt
with changes.** It judged §12.1 deciding the type a stated interpretation, the extensions to ai and to closure
justified by §12.1 and §12.5, and criterion 4 part (i) the right place. (1) Drop the move, which breaks §12.4's
order: taken (item 2). (2) Do not tell the reader the type: taken (item 3). (3) Have the reader give the type and
the code compare it: taken (items 3 and 4). (4) "Building or converting", not the draft's "under construction or
planned": taken (item 1). (5) The move's pool date: moot.

**What it costs.** A candidate the protocol places on another type is lost to both lists unless that list's own
channel found it. Code: the reply's `type` (checked against the shape), the log's agreement for a typed pass, the
saved read's `type`; the brief's paragraph and its test. The reader's inputs change, so they are committed and pushed
before the next read.

#### 4.6.5 Patch 2026-10-19 (his, about 12:50 PM CDT, after the independent reader's read; drafted by Opus): exploratory cases, after the pre-registered rule found none

*ADOPTED 2026-10-19 (his, about 12:50 PM CDT), after the independent reader's read (below): its changes 1 to 5 and 8
taken, 6, 7, 9 and 10 answered. His decision in principle came first (about 12:05 PM: adopt, steps 3 and 4 included,
with the window's protection replaced by the knowledge probe for those steps, and with every further relaxation that
holds up), and he took the read's changes on the condition that they help reach a legitimate five cases or close to
it. **The build is planned step by step in `phase-5-case-building-exploratory-IMPLEMENTATION.md`.*** The
pre-registered rule found no case in any type (§11, 2026-10-18 and 2026-10-19). His decision (2026-10-18, about 4:14
PM; confirmed 2026-10-19): do not close v1 on the shortfall; relax the rule in logged steps until v1 has three to five
cases, each labeled exploratory. **This patch is written after the record of every rejected candidate was seen**, so
steps 1 and 2 are written knowing which candidates they admit, as §4.6.4 was; step 3's pool was sized, by counts only,
before its rule was written (E). It is judged as an exploratory rule, not as a reading of the protocol.

**A. What does not change.**

1. **The pre-registered selection stands as recorded:** `selection-log-633.json` (sha256 `ae329e10...`), "selection
   complete" for every type, shortfalls 2 (closure), 2 (retool), 1 (ai). No row of it is edited or written again, and
   it is reported first, as the rule's result (§12.1: a shortfall is "reported, never filled by judgment").
2. **Phase 4 stays the headline result.** The cases are readings (§12), never in the family of 16.
3. **His conditions (2026-10-18), kept:** every step logged with what changed, why and what it let in; the
   recognition probe (§12.8); the rule that a scenario never states the company's choice; the exploratory label.
   **The fourth, the window's protection against training data, is kept in steps 1, 2 and 5 and replaced in steps 3
   and 4 by a knowledge probe (step 3 item 4): his decision, 2026-10-19.**
4. **Everything after criterion 4 is unchanged** for every case: the build and his flag review, the scenario check,
   the rubric and its read, the foreshadowing and neutrality checks, `case.lock` pushed before the first probe, the
   probe and its coarsening, the gate (§12.10).

**B. The exploratory record.**

1. **A separate log:** `search/exploratory-log-<n>.json` and its public view, written once per version as the
   selection log is (§4.3), by the same code with each step's criteria and lists.
2. **A pre-registered row that step 2 re-reads is carried:** its results before criterion 4, with the log version and
   sha256 they came from; criterion 4 is recorded again under the exploratory rules, with its reason, and read if it
   fails. Its label stays its candidate id (§4.2).
3. **The label, everywhere a case appears** (the public selection view, the freeze's case list, Phase 5.5's report,
   the explorer, the methods page): "exploratory: selected by §4.6.5 step N, after the pre-registered rule found
   none". Steps 3 and 4 add: "first disclosed before the main model's training cut-off (Haiku 5.5, June 2026) and
   after the second family's (gpt-oss-120b, June 2024); admitted after a knowledge probe of both official models and
   the extraction model found no recall". `case.lock` is unchanged (hashes only); the label lives in the log and the
   freeze's list.
4. **Every command that reads the selection log for a label** (`hc case documents`, `build`, `scenario check`,
   `reader`, `lock`, `probe`) reads the exploratory log for an exploratory row.

**C. The steps, in order.**

**Step 0 (a prerequisite, not a relaxation of selection): the figure-free S3 form.** The fault (`KNOWN-GAPS.md`, OPEN
2026-10-16, "S3 renders only with every option's figures"): by §4.6.1 item 6, an S3 case without a pre-cut-off figure
for every option drops every option sentence that holds one; the retool and sell texts are made only of such
sentences, so they are left empty and the render refuses. **No S3 case can render today, and every candidate the
steps below admit is S3 or S1.** Protocol §12.6 provides for exactly this case: "Where an option has no pre-cut-off
figures, every option is described without figures alike."

1. **When equal treatment applies to an S3 case, each option's text is one figure-free sentence**, from a new file,
   `experiment/case-forms/s3.toml`, outside `experiment/company/`, so the tag's content hash and Phase 4's rendered S3
   are unchanged and `hc scenarios check` still passes:
   - close: "Close the plant." (the template's first sentence without "and move its product family to the other
     plants", which a real company that drops the product would make false; the reader's change 2);
   - retool: "Retool the plant and keep running it." (new: the template's "automating welding and material handling
     as at the larger plants" describes the fictional plant only);
   - sell: "Sell the plant, with its product family, to a buyer that will keep running it." (the template's first
     sentence without its figure clause).
2. In that form the situation's "The figures for every option are management's estimates." is dropped, since it
   would be false, and so are the close text's other sentences, so that each option is one sentence.
3. **The pay-per-head check** (`KNOWN-GAPS.md`, OPEN 2026-10-16): where a kept sentence states both a heads row and a
   total-pay row, the render runs `scale.check_pay_per_head` on the pair and records the result in
   `scenario-render.json`. A failure is a build error under §12.6.
4. **S3's text is about a plant that makes a product family**, so in this record a decision about a facility that
   makes no product (a laboratory, an office, a store, or a warehouse or distribution center on its own) fails
   criterion 4 part (i): the text would misdescribe it.

*Cost:* three sentences of shape-level text, cut from the template's own or, for retool, new, written before any step
3 candidate is read; the reader reads them with this patch and again in every case's scenario read (§4.9). A
figure-free scenario can leave a case "not enough disclosed" at the matcher (§12.7). That is a reading's outcome, and
it is reported.

**Step 1: the S3 rules of this record.** They apply to every S3 candidate of steps 2 to 5.

1. **The type, with no list restriction.** One list per type; a candidate goes on the list of the type that §12.1 and
   §4.6.4 item 1 give it at criterion 4. §4.6.4 item 2 ("no candidate moves") does not apply here, because neither of
   its concerns can arise: every pre-registered row was checked, so none reaches a second list by the accident of how
   far its first list was checked, and every row of step 2 is recorded at criterion 4 before any exploratory case is
   built, so no later arrival can displace one.
2. **The floor: an S3 total of 50 or more, as stated, unscaled**, replacing §4.6.3's 167 for S3. S1 keeps 167 (his
   decision, 2026-10-19: S1 is not relaxed). A scaled S3 total under 100 is stated as a number to the nearest 5, with
   the caps set equal to it; every other heads figure under 100 still reads "fewer than 100". His reason: a smaller
   site can be a perfectly good decision. 50 is below every S3 number in the pre-registered record and was chosen
   knowing them. **A reported deviation from §12.6's "fewer than 100":** that rule guards against a small site being
   identified by its exact headcount; the scaled, rounded figure is not the real one, and the recognition probe and
   §12.11's re-identification check guard the same risk.
3. **Where the total may come from, the first of these that gives one:** the first-disclosure document; the
   pre-cut-off documents (§4.6.2 A.3); then, new, **a public report dated from the first disclosure to 60 days after
   it:** a government notice of the layoffs or the closing for the facility (a WARN notice, in the United States),
   the company's own later release or filing, or a news report that attributes the number to the company, a union or
   a government office, the earliest such report found. The search is the first-disclosure check's web search (§4.3
   (b)) on the facility's name or place, and the source is logged in the private appendix. **A reported deviation
   from §12.6** ("only documents dated before the cut-off"), extending §4.6 rule 1, which already takes the
   decision's size from the first-disclosure document: a report dated after the cut-off may supply the plant's
   headcount, and nothing else (the reader's change 4).
4. **The total is the number of employees at the facility, as a source states it.** A number of jobs or positions
   cut, eliminated or affected is not the total, and neither is a number given only as an upper bound ("up to"):
   each is the size of the company's own choice, and as the plant's size it would build that choice into the scenario
   (the reader's change 3). "About" a number is that number and a range is its low end (§4.6.3 item 3).
5. **A decision that names more than one facility has no S3 total:** S3's scenario is one plant, and a sum would put
   the company's chosen set of plants into it as one (the reader's change 3).
6. **Lines are read only where post-event filings state them** (§12.7, as for every case). A case with none observable
   is read on its choice alone, which S3's k* of 1 allows: the frozen matcher counts the choice as one dimension and n
   observable lines as max(n - 1, 0) (`analysis/matcher.py`), so a choice-only reading has one.
7. **The brief's `maps_to_shape` paragraph, for this record,** changes in four places, logged in §11 as a change to
   the instrument (no pending read uses the old text):
   - after the S3 shape rule, add: "Here the facility must be one that makes products; a decision about a
     laboratory, an office, a store, or a warehouse or distribution center on its own matches no shape."
   - "S3: the number of employees at the facility named." becomes "S3: the number of employees at the facility named,
     as a source states it; a number of jobs or positions cut, eliminated or affected is not it, and a decision that
     names more than one facility has no S3 total."
   - "For S1 and S3 the total must be 167 or more." becomes "For S1 the total must be 167 or more; for S3, 50 or
     more."
   - "The material for the total is the excerpt and, if you are given one, a search of the company's earlier
     filings." gains, before its full stop: "and, for S3, any public report you are given (a government notice, the
     company's later release or a news report); judge from the whole report whether its number is the number of
     employees at the facility named" (the reader's change 5).

*Cost:* an S3 case may now rest on a plant's headcount from a report dated after the cut-off, a declared deviation,
and a case with no observable lines is read on its choice alone.

**Step 2: the pre-registered S3 rows, re-read, and one new in-window channel.**

1. **Every pre-registered row read as S3 at criterion 4 is carried** (B.2), and its criterion 4 is recorded again
   under steps 0 and 1, on the list of its type: closure-04, 05, 07, 09, 16, 19, 24 and 29, closure-f01, and
   closure-27 (S3 by §11's correction of 2026-10-18). What the record already shows: closure-16's first-disclosure
   document states the number of roles at the facility, and its type is retool by §12.1; closure-19's number is a
   workforce reduction and closure-07's an upper bound of positions eliminated, so neither is the plant's headcount
   (item 4), and both, with closure-09, closure-29 and closure-f01, depend on item 3's reports for one; closure-05 and
   closure-24 each name two facilities (item 5); closure-04's facility makes no product (step 0 item 4); closure-27's
   facility is read by rule. *Not re-read:* the S2 rows on any list (S2's text states a downturn and an expected fall
   that no source gives, F) and the S1 rows (S1 is not relaxed).
2. **A new in-window channel, for plant closures announced outside Item 2.05:** 8-K, `items` with 7.01 or 8.01,
   `sics` 2000-3999, the search's filing dates (2026-07-01 to 2026-10-15, the fallback month held apart as §12.2
   holds it), not already a candidate, with any of these phrases, each its own query: "close the facility",
   "closure of the facility", "close its facility", "plant closure", "close the plant", "closure of the plant",
   "cease production", "consolidate production", "closing the facility", "closure of its". Every hit is a new row,
   checked from the first criterion, on the list of its type at criterion 4. Over the window it returns 8 filings
   (counts only, E); the fallback month was not run.

*Cost:* rows the order rule excluded come in after their results were known, which is what the label is for; the
channel was written after the pre-registered ones found nothing.

**Step 3: a pre-cut-off pool, admitted through a knowledge probe.**

1. **The pool:** channel 1 of §12.3 as written (`"Item 2.05"`, 8-K, `items` with 2.05, `sics` 2000-3999) and step 2's
   channel, filing dates **2025-07-01 to 2026-06-30**, the twelve months before the fallback month. One search,
   recorded as §4.4's was (`search/pre-candidates.json`, write-once). Channels 2 and 3 are not run: in the window, 47
   of 62 retool candidates failed the first-disclosure check on text repeated from earlier filings, and no ai
   candidate had a usable S1. Their checking costs the most and yielded nothing.
2. **One list per type, typed at criterion 4** (step 1 item 1). Ids `pre-01` on, in order of **filing date, newest
   first**, then accession number. A decision near the models' cut-off is the least likely to be in their training
   data, and the order is mechanical, so no one picks it. Candidates are dated when reached; §12.4's order of first
   disclosure would need all of them dated first.
3. **The criteria, in order:** first disclosure (an earlier mention before 2025-07-01 fails; the date found sets the
   cut-off, §12.6), publicly traded, inside the pool, real decision, maps to shape (§4.6.2 to §4.6.4, with steps 0
   and 1), **not known** (item 4), not recognizable (§12.8). Every rejection on the last four is read (§12.4).
4. **The knowledge probe** (`not_known`, after criterion 4 and before the build). Each of v1's two official models,
   `haiku-5-5` (main) and `gpt-oss-openrouter` (second family), and the extraction model `sonnet-5-5-extraction`,
   gets three calls, with no system text, a reply never retried (an API error is), and this message, word for word:
   - S3: "What do you know about {company}'s {facility} in {place}? If you know nothing about it, say unknown."
   - S1 or S2: "What do you know about the workforce reduction {company} announced in {month} {year}? If you know
     nothing about it, say unknown."

   {company} is the filer's name as the first-disclosure document gives it; {facility} and {place} are that
   document's own words for the facility and its town; {month} {year} is the first-disclosure date. **An answer fails
   if it states, or guesses, that the facility was or would be closed or sold or its production moved, or that the
   reduction happened, or if it gives a figure of the decision.** "unknown", or an answer about the company or the
   facility that does not state the decision, passes. The candidate fails if any call fails. He reads every answer
   that is not "unknown"; the reader reads every failure (with a brief like criterion 5's: the definition and the
   flagged answers, never the dossier), and a dispute is settled as for criterion 5 (§4.9). **The extraction model is
   probed because it writes the dossier:** a model that knows the outcome could carry it into the text in ways the
   foreshadowing check does not catch.
5. **Where it runs:** on the laptop, `hc case knowledge-probe <label>`, refused unless the label's row stands at
   `not_known`. The request and every reply are written once in the case's appendix folder with the usual provenance,
   and a second run for the label is refused. It is the only path that sends an official model a real company's name
   outside the container, and only with this message. *Why not the container:* that would need a deploy and a
   committed, salted hash per batch, for a screen whose failures only remove candidates.
6. **The closure list's rows that failed only the first-disclosure check**, where the earlier mention that failed
   them is dated inside the pool's range, join the pool's list as if filed on that date: closure-f04, and closure-18
   if its earlier mention falls inside.

**Step 4: the pool extended.** The pool extends to filing dates **2024-07-01 to 2025-06-30**, under step 3's rules,
with ids continuing and newest first. 2024-07-01 is the day after the earlier of the two official models' training
cut-offs (gpt-oss-120b's, 2024-06-30, OpenRouter's model listing, *live 2026-10-19*), so every case it admits is still
outside one official model's training data. Nothing earlier is admitted.

**Step 5: a second search, with the window's protection kept.** The three channels of §12.3 and step 2's channel,
run once by rule on **2027-01-04** over filing dates 2026-10-16 to 2027-01-03, every candidate under steps 0 and 1. No
knowledge probe: every decision in it falls after every model's cut-off. Ids `late-01` on, by first disclosure. It
comes last because it cannot run before January, not because it is weaker.

**D. The order, the counts and the stop.**

1. **One order for every exploratory candidate, across types** (the reader's change 8): step 2's rows by first
   disclosure, the window's before the fallback month's (§12.2); then step 3's list in its order; then step 4's; then
   step 5's by first disclosure.
2. **Per type, the cases are the first k in that order that pass every criterion** (closure 2, retool 2, ai 1).
3. **A type that cannot reach k is short, and its slots go to the next candidates in the same order that pass, of any
   type.** This fills a shortfall by a rule fixed here, never by judgment. §12.1's "at least one invest or retool"
   either holds or is reported.
4. **The order binds the checking too:** a candidate is not selected while one before it in the order is unfinished,
   as the selection log's `waiting` already holds a type's selection open, so the pace at which candidates are worked
   cannot choose a case.
5. **At most five. Checking stops when five cases are selected;** later candidates are never checked. Building ahead
   is allowed, as §4.1 says.
6. **Steps 3, 4 and 5 open in turn,** each when every candidate of the steps before it is finished and fewer than five
   cases exist. He may open step 3 early, to build ahead; that changes nothing about which candidates are cases, since
   item 1's order decides.

**E. What was seen before this was written.**

- Every pre-registered candidate's record, names included.
- For the options not taken (F): XBRL figures for the 25 closure-list S2 candidates; the Item 2.05 text of the 24
  non-manufacturing Item 2.05 filings in the window.
- For step 2's channel: its count over the window (8 filings) and a mechanical scan of their text (6 hold a closure
  phrase near a facility word; the only headcounts in them are company-wide). No filing was read and no name seen.
- For step 3: the pool's size by month (142 channel 1 filings, 6 to 17 a month) and the same scan (32 hold a closure
  phrase; 13 of those state 167 or more people; about 6 of the 13 plausibly a site's headcount, the rest company-wide
  totals). Counts only: no filing of the pool was read and no name seen. Step 3's twelve months were chosen with that
  count known.
- No public report (step 1 item 3) has been looked up for any candidate, so no number from one is known.

**F. Considered and not taken.**

- **A count of jobs cut, an upper bound, or a sum over facilities as the S3 total** (in this patch's first form,
  removed at the reader's change 3): each makes the scenario's plant the size of the company's chosen cut or chosen
  set of plants, which builds part of the company's choice into the scenario.
- **Any change to the S2 total, a realized fall in operating income included** (the reader's change 9 asked for the
  realized fall; declined). S2's fixed text says that "a downturn ... is cutting orders" and that management
  *expects* revenue and operating income to fall. Nearly every real S2 candidate cut costs while revenue held or grew
  (about 11 of the 25 had no product revenue at all), so no rule about the total can make that text true. The best a
  realized fall could admit is one filer (closure-12 and closure-20 are two of its decisions), whose decision, ending a
  product line, maps onto S2's lines too thinly to be read: S2 needs two observable dimensions (k* = 2, protocol
  §11.4).
- **A stated total program cost as the S4 total** (retool-34 and retool-42). S4's fixed first sentence says the
  engineering center designed a program to develop a new family of machines for customers the Company does not serve,
  which would then be stated for a plant expansion, and a multi-year total would be offered as one year's money. An S4
  case also needs two observable dimensions (k* = 2), which a plant expansion's filings rarely give beyond its choice.
  Making S4 fit is a new shape: new prose, written after the candidates were seen.
- **An S1 relaxation.** His decision, 2026-10-19. S1's text says that AI tools can take over the work of the roles in
  question, which a cut only partly credited to AI would make false.
- **The non-manufacturing Item 2.05 filings** (24 in the window): S3's text is about a plant, and their workforce cuts
  have no S2 total.
- **A second coarsening after a second probe failure:** it relaxes §12.8's "a second failure drops the case", and a
  dossier coarsened twice keeps little of the company it describes.
- **Leaving the extraction model out of the knowledge probe:** the dossier would then be written by a model that may
  know the ending.
- **Letting a guess pass the knowledge probe:** a correct guess and a memory cannot be told apart.
- **Admitting forced wind-downs (criterion 3):** a decision with no alternative cannot be matched to an objective.
- **Cases from the private longlist:** selection by hand, which D exists to exclude.

**G. What it costs.**

- **Build:** planned step by step in `phase-5-case-building-exploratory-IMPLEMENTATION.md` (Sonnet building, Opus
  reviewing): stage 1, the code (about a day); stage 2, step 2's rows (about a day, then each passing row's build,
  rubric and probe); stage 3, the pool and the knowledge probe, built only when step 3 opens. The coarsened dossier's
  home (`KNOWN-GAPS.md`, OPEN 2026-10-16) must still be settled before any second probe set.
- **Money:** the reader's candidate reads cost $3.92 measured through 2026-10-19 and this patch's read $0.24; his
  OpenRouter balance was under $1 that day. A criterion 4 rejection read on a short excerpt costs 1 to 3 cents; the
  first cash that the balance does not cover is the first case's scenario and rubric reads (about 10 cents each), and
  from here to the end of Phase 5.5 about $2 to $2.50 of OpenRouter in all, one top-up. Builds, Haiku 5.5's probes
  and runs, and the knowledge probe's Sonnet calls draw on the prepaid Anthropic credit (about $15.95 at the last
  reading); Fargate on AWS credits. The projection (§6) is updated before the first exploratory build.
- **Validity, by step:** step 0 is the protocol's own rule with three sentences of new or shortened text; step 1 lowers
  the S3 floor (a reported anonymity deviation) and takes a plant's headcount from public reports (a reported
  deviation from §12.6); step 2 brings back rows the order rule excluded and adds a channel written late; steps 3 and
  4 trade the window's guarantee for a probe that can miss partial knowledge; step 5 costs only time. Each is labeled.
- **Expected yield, not measured:** step 2 holds one row expected to pass criterion 4 on the record's own figures
  (closure-16) and up to five more if public reports give their plants' headcounts (closure-07, 09, 19, 29 and f01),
  plus the channel's rows. Each can still fail the build (never yet run on a real filing), the scenario check or the
  recognition probe. **Three from step 2 alone depends on those reports; five is likely to need step 3. Neither is
  measured.**
- **What the cases can show, a limit to report:** every S3 candidate in the record is a decision in which the company
  closed a plant, and many will be read on their choice alone. The readings will ask, case by case, which objectives
  choose to close; none will show a decision to invest. The write-up says so.

*The independent read (2026-10-19, Gemini 3.1 Pro, $0.241; `evidence/phase-5/patch-4.6.5-review-raw.md`):* **adopt
with ten changes.** (1) Name the models in the label and say whose cut-off bounds the pool: taken (B.3). (2) The close
text says the product family moves, which a real closure may not do: taken (step 0, "Close the plant."). (3) A count of
jobs cut, an upper bound or a sum over facilities as the plant's size builds the company's choice into the scenario:
taken in the stronger form, removed rather than stated (step 1 items 4 and 5; F). (4) The post-cut-off report is a
deviation from §12.6: taken (step 1 item 3). (5) "From which only the number is taken" steers the reader: taken,
reworded so the reader judges from the whole report (step 1 item 7). (6) and (7) Probe every official model and bound
the pool by the earliest official cut-off: answered, not changed in substance; v1's official set is two models, both
probed, and step 4's boundary is already the earlier of their cut-offs, which the text now says. (8) One order across
types: taken (D). (9) The realized fall for S2: declined (F). (10) A choice-only S3 reading has no dimension under
§12.7: declined; the frozen matcher counts it as one (step 1 item 6). The read's other points (step 2's rules were
written knowing what they admit; zero-shot recall can miss associative knowledge; a laptop run is less verifiable than
the container) are limits the patch and the label state, not changed.

### 4.7 The rubric

Written by Claude with him, from filings dated after the cut-off, in a fixed TOML form in the appendix
(`rubric.toml`): the company's choice (an option key, or "not observable"); each lever line it observably used,
scaled like the scenario, or "not observable"; the observable and excluded dimensions; every uncertain call with its
alternative reading; the outcome terms for the foreshadowing check; the source excerpt for every line. **Actions only,
never stated reasons** (`planning/06` §2.1). Its sha256 goes in `case.lock`; the file itself stays private until
Phase 5.5 publishes what §12.11 allows. The reader reads the mapping with the excerpts (§4.9).

### 4.8 The probe

- **Content in:** `hc case upload <label>` (laptop, dev user, which already holds `s3:*` on the results bucket) puts
  the dossier, scenario and rubric under `cases/<label>/set-<n>/`, write-once, after checking them against the
  committed `case.lock`.
- **The call:** `hc case probe <label> --model haiku-5-5|gpt-oss-openrouter`, launched as a Fargate task like a
  sweep. In the container it reads the content, refuses unless it hashes to `case.lock` in the image (so the image
  must carry the record: the commit is pushed and deployed first), sends §12.8's message word for word with the
  dossier as the system text, three calls, and writes each answer to
  `cases/<label>/probes/set-<n>/<model>/call-<i>.json`, write-once, with the usual provenance. **Its own model
  rule:** only models with role `main` or `second_family`, only on a `cases/` label (not `check_probe_model`'s
  development-only rule, Phase 3.5 §24.2).
- **The verdict:** `hc case probe-verdict <label> --set <n>` (laptop) shows each answer once, checks it against the
  case's term list, asks him to confirm or overrule any answer that is not "unknown", and writes one
  `verdict.json` per call beside it, write-once, with `passed`. The gate's S3 reader builds `ProbeRecord` from the
  call object's `LastModified` and the verdict's `passed`.
- *(Amended 2026-10-16, his decision on criterion 5; built in 10a, §11.)* **The verdict is two steps when an answer
  names the company.** A verdict object is write-once and carries the final `passed`, so it is written only once the
  set is settled: his read of each answer is saved in the appendix (`probe-reads-set-<n>.json`), the flagged answers
  go to the independent reader, and the verdicts are written after the reader's reply is on record, from that reply.
  The verdict key is `call-<i>.verdict.json` beside `call-<i>.json`. It holds the original verdict, the reply's file
  name and sha256, his resolution on a dispute and the final `passed`.
- **The prefix is private forever:** `cases/` is not read by the publish path (Phase 1.5), not listed in any manifest
  Phase 4's decision 2 commits, and the task role's new statement grants `cases/*` and nothing wider.
- **Infrastructure (his apply):** `task.json` gains `s3:GetObject` and `s3:PutObject` on `cases/*` and the list
  prefix; the bucket policy's write-once rule already applies to every key. The deploy carries the new command.

### 4.9 The independent reader

One command, `hc case reader <label|id> rejection|scenario|rubric`, sends the fixed brief for that kind with only what
§12.9 allows (the criteria and the candidate's first-disclosure excerpt; or the shape and the scenario with its
sources; or the rubric with its excerpts), never the grid's results, and writes the request and reply to the
appendix, write-once. The briefs are committed before the first read. The reader's model is decision 3. Each read's
outcome goes into the selection log (`hc case log ... read`) or the case's rubric record; a disagreement is his to
resolve, logged with both readings.

*(Added 2026-10-16, his decision on criterion 5.)* The reader also reads a criterion 5 rejection, a probe failure:
`hc case reader <id> rejection --criterion not_recognizable [--set n]`. It is shown only §12.8's definition of
"names the company", the answers flagged as naming it, and the case's private term list; never the dossier, never
a result. Its reply is recorded like any other, per probe set, and a "pass" (the flagged answers do not name the
company) disputes the failure: the verdict records carry the final result (§4.8), so the log and the gate agree.

### 4.10 The gate's readers, proved on the probes

Built here, wired into `hc sweep launch` in Phase 5.5: the **GitHub reader** (each Actions run's `created_at` and the
record at its head commit, `gh api` and `git show`; first checked: whether an expired or deleted run disappears from
the listing, which would fail closed) and the **S3 probe reader** (§4.8). Proof for this half: `check_case_order` and
`check_case_probes` run on every frozen case from the laptop, and their findings are committed with the freeze.

### 4.11 The freeze

One commit: every case's `case.lock`; `docs/phases/evidence/phase-5/` with the public selection log, each case's
probe results by model (passed or not, by set, no answer text), the reader's outcomes by kind (counts, no text), the
order findings, the projection and the measured cost; and the list of cases Phase 5.5 runs. Nothing in it names a
company, and nothing in it is an answer text, a figure or an excerpt.

## 5. Order of work

**Sonnet builds; Opus reviews each diff before he commits; Opus does the judgment steps (criteria, rubrics,
scenario facts) with him.** One terminal command at a time, with the line to look for.

### Stage A: tonight and tomorrow morning, before the search

1. **His approval of this doc**, decisions in §8. His commit: `phase 5: search-half implementation doc`, with the
   stale-doc fixes made the same day.
2. **The reply-shape check** (finding 11): one EFTS request by script, his User-Agent, query `"Item 2.05"`, forms
   8-K, a week in January 2025. Claude reads the field names against `search.py`'s and records them in §11. If they
   differ, the parser is fixed (run code) and tested before the search.
3. **`hc case search`** (§4.4) built and reviewed, with a test on a fake reply that has the shape step 2 found. His
   commit.
4. **The projection** (§6) into `docs/phases/evidence/phase-5/projection.md`, with his three balance readings (the
   Console, OpenRouter, AWS Billing), before the search. Committed with the search's record or before it.

### Stage B: 2026-10-16, the search

5. **His one command:** `hc case search --date 2026-10-16`. Claude reads the printed counts and the per-query records
   (any short read or `MAX_RESULTS` hit is a deviation to report). Nothing else is decided that day by rule.

### Stage C: the case code (Sonnet, about two days; may start the same day)

6. `hc case log` (§4.3).
7. The extraction entry in `models.toml` with its tripwire tests; `hc case build` and `hc case assemble` (§4.5).
   **Committed and pushed before the first real document is fetched.**
8. *(Split 2026-10-16, his.)* **8a.** `hc case lock` (writes `case.lock` from `content_hashes`), refusing until the
   scenario check passes. **8b.** `hc case scenario render` and `hc case scenario check` by the §4.6.1 patch.
9. The reader command and its three briefs (§4.9), committed before the first read.
10. The probe: `upload`, the container command, `probe-verdict`, `task.json` (his Terraform plan and apply, Claude
    reading the plan), the S3 and GitHub readers (§4.8, §4.10).
    *(Split 2026-10-16, his.)* **10a.** Everything that runs on fakes: `upload`, the container's probe command,
    `probe-verdict`, the S3 and GitHub readers, and the criterion 5 read (as built, §11). No `task.json` or
    Terraform change, no AWS call, no real probe. **10b.** `task.json` (his Terraform plan and apply, Claude reading
    the plan), launching the task, and the first real probe.
    *(Dated note, 2026-10-16, about 5:10 PM.)* **The first real probe moves to Stage D,** as the first case's own
    probe: a probe needs a locked, uploaded case, and no case exists before Stage D. 10b is the grant (`task.json`
    and `boundary.json` gain `cases/*`) and `hc case probe --launch`. With his apply and push, Stage C is done.

### Stage D: the cases (as many sessions as it takes)

11. Criteria 1-4 down each type's list, in order (§4.1 step 1). Reader on each 3-4 rejection. *(Added 2026-10-16,
    the step 9 review, point 3.)* **The reader's excerpt is taken by rule, and saved before the result it is read
    against is recorded:** the whole part of the first-disclosure document that announces the decision (the item of
    a current report, or the body of the release it files), not paragraphs picked from it, cut only to fit the
    200,000-character limit, at a paragraph boundary. Then `hc case reader <id> rejection --criterion ...`, then
    `hc case log <type> read <id> <criterion>`, which takes the verdict from the reply file.
12. For each candidate that passes them: §4.1 steps 2-9. The first real document fetch is the first real test of
    the splitter and the date patterns (code half §10).
13. A type that runs out of window candidates opens its fallback pool (§12.2), in the same way.

### Stage E: the freeze

14. The selection log complete (`problems()` empty, `selection()` closed for every type), the order checks pass, the
    freeze commit (§4.11), the measured cost against the projection, the DoD audit (§9), ROADMAP and START HERE.

## 6. The projection (Delivers 1, scope DoD 8)

Measured per run in Phase 4 (run log §6.9): Haiku 5.5 **$0.0016**, `gpt-oss-120b` **$0.00045**. A case prompt is
assumed up to twice the fictional one, so both are doubled below.

| Item | Pot | Estimate | Worst |
|---|---|---|---|
| Extraction, Sonnet 5.5 at $2 / $10 per million *(live 2026-10-15)*: about 120,000 input and 8,000 output tokens a build, up to 8 builds | Anthropic credit | $2.60 | $5 |
| Probes: 3 calls per model per set, up to 8 builds and 2 sets | credit and his cash | $0.10 | $0.30 |
| Reader, Gemini 3.1 Pro at $2 / $12 per million *(live 2026-10-15)*: about 30 reads | his cash | $1 | $2 |
| Phase 5.5's runs: 5 cases x 150 runs per model | credit $2.40, his cash $0.70 | $3.10 | $4.50 |
| Fargate for the probes and Phase 5.5 | AWS credit | $0.40 | $1 |
| **Phases 5 and 5.5** | | **about $7** | **about $13** |

**Cumulative after both: about $35, at worst about $41,** against the $60 re-plan point and the $80 ceiling. Passes.
The Anthropic credit ($15.95) stays above $8 at worst; its workspace limit ($10 a month, resets 2026-11-01) holds at
October's projected draw of about $5. His OpenRouter cash stays inside his $5 cap (finding 9). **No cut** by
`planning/05` §5.1 is needed. Re-read on the day with his balances (§5 step 4).

## 7. Rules this half must not break

- **Rule zero**, in every file, commit, branch, message and chat summary; labels only; identifiers in the term file
  before a case's first commit.
- **No case's decision runs.** The only model calls on a case are the extraction (pre-cut-off text, never the outcome)
  and the probe (after the rubric is pushed).
- **The rubric precedes the model:** `case.lock` committed and pushed, CI run created, before the first probe object.
- **The frozen files are not touched**: the protocol, the content, `sweep/prompt.py`, `decision.py`, `classify.py`,
  `analysis/`, `experiment.py`, a locked model's identity in `models.toml`. Adding the extraction entry changes no
  locked identity; `hc protocol check` proves it after step 7.
- **Selection is by the rule**, and a shortfall is reported, never filled.
- **`make check` before every commit; CI green.** He runs every commit, push, Terraform command and AWS-authenticated
  command.

## 8. Decisions for him

**All seven DECIDED 2026-10-15 (his): (a), as recommended.** Each keeps its options as the record.

1. **If the search cannot run on 2026-10-16.**
   - (a) **Recommended: the window ends 2026-10-15 whatever day the search runs**, and a later run is reported as a
     deviation with its reason. The rule's purpose is that nobody picks the window knowing the candidates; fixing the
     end today keeps that even if tomorrow is lost, and costs nothing if it is not.
   - (b) Read §12.2 literally: the window ends the day before whatever day the search runs. A slip then moves the
     window by a choice made later.
2. **The extraction model.**
   - (a) **Recommended: Claude Sonnet 5.5 through Anthropic's API, on the prepaid credit, thinking off.** Its training
     data ends June 2026 *(live)*, before the fallback month (finding 4); it is not an official model; it runs on the
     route K6 built and costs no new money (about $2.60 of the credit). The cost: it is the main model's vendor, so a
     Claude model summarizes for a Claude model. The probe and the foreshadowing check are the measured guards, and
     the methods page says so.
   - (b) Gemini 3.1 Pro through OpenRouter: another vendor, about $2.60 of his cash (half his remaining cap); a
     preview model, so it may be withdrawn mid-phase, which forces a rebuild of every case (§12.6).
3. **The independent reader.**
   - (a) **Recommended: Gemini 3.1 Pro through OpenRouter**, his cash, about $1 (worst $2). Another vendor than the
     drafter (Claude) and the main model; already used as the protocol's reviewer, which is not a conflict (it read
     the protocol, never a result); training data well before the window.
   - (b) An OpenAI model released after September 2026: its cutoff is not stated and may postdate the window.
4. **The case scenario rule** (findings 2-3).
   - (a) **Recommended: §4.6 as written:** the subject and size from the first-disclosure document, every other figure
     pre-cut-off, a cap with no pre-cut-off figure equal to the total, the fictional shape's wording kept, and the
     reader's neutrality read of every scenario. Fixed tonight, before any candidate exists; recorded in the
     selection log's public view and on the methods page as a rule set after the tag and before the search, since the
     protocol does not state it.
   - (b) Every scenario fact pre-cut-off only. Most closures and AI-attributed cuts then fail criterion 4, since the
     size first appears in the disclosure; expect shortfalls in every type.
   - (c) Leave it to judgment per case. Not recommended: it is the one choice in the phase made knowing both the
     outcome and the grid's results.
5. **Where the probe runs** (finding 5).
   - (a) **Recommended: as a Fargate task, with a private `cases/` prefix** (one `task.json` statement, his apply).
     Keeps "no laptop copy of the key"; the probe records land where the gate reads them.
   - (b) A temporary laptop copy of the Anthropic key, deleted after the probes. Less to build; breaks a rule set on
     purpose on 2026-10-12, and the records would need copying into S3 for the gate.
6. **The reader also reads scenario files** (§4.6, §4.9).
   - (a) **Recommended: yes.** §12.9 requires the reader on rejections and rubrics; the scenario file is the other
     text written by someone who knows the outcome. About $0.10 a case.
   - (b) No: the neutrality checklist alone, by Claude and him.
7. **The appendix and its backup.**
   - (a) **Recommended: the appendix at a folder outside every git repository on the laptop** (its path set by `git
     config hc.appendixDir`, never written in a tracked file), **backed up after each stage as one archive file
     committed to the private job-search-headquarters repo** by him. The code refuses an appendix inside any git
     repository (kept, code half step 3), so the backup is a copy, not the working folder.
   - (b) No backup beyond the laptop. A disk loss would lose the raw filings and every seed.

**Not a decision:** the search date (by rule); the labels (§4.2); the first-disclosure method (§4.3), which is the
protocol's check done the same way each time.

## 9. Definition of done (the scope doc's, with the proof of each)

| Scope DoD | Proof |
|---|---|
| 1. At least three cases, one invest or retool, or a shortfall by type | the public selection log; the freeze commit's case list |
| 2. The selection log complete, every judgment rejection read | `selection()` closed and `problems()` empty for every type |
| 3. Foreshadowing and neutrality passed; pre-cut-off sources only | `foreshadow-<n>.json` with every hit resolved; the checklist record; each `sources.json` |
| 4. Every rubric committed and read; its commit before the first probe | `case.lock`; the reader's record; `check_case_order` findings |
| 5. Every case passed the probe on every model, or coarsened, re-probed, or dropped and replaced | the verdicts by set; `check_case_probes` |
| 6. The freeze commit exists; no case decision has run | the commit; no object under any case sweep prefix |
| 7. Identifiers in the term file before each case's first commit; the guard on every commit; CI green | his confirmation per case, dated; CI run IDs |
| 8. Measured cost recorded; the $60 point checked before case work | `projection.md` committed before the search; the bills at the freeze |

## 10. Genuinely uncertain

- **How many candidates the channels return.** The invest-or-retool queries are broad phrases; channel 3's "AI"
  query may return many. Every page is read either way; more than 10,000 hits is a deviation.
- **Whether real 10-Ks split** (code half §10). The hand split is the fallback, recorded.
- **How many flags a real dossier raises.** Each needs his decision; a long list is slow, not wrong.
- **Whether the probe fails often.** Two failures in a row drop a candidate; a type could run out.
- **Whether the first-disclosure check finds earlier mentions consistently.** It is a search by a person, and a missed
  earlier mention lets a candidate in that the rule would have kept out. The method is the same for every candidate
  (§4.3) and its sources are logged.

## 11. As built

**Stage A step 2, the reply's shape (2026-10-15, about 3:58 PM CDT).** Three read-only requests by him
(`scratch/sec-efts-shape.sh`, `scratch/sec-efts-paging.sh`, his User-Agent now in local git config
`hc.secUserAgent`), query `"Item 2.05"`, forms 8-K, dates in the first half of **2025** only, so no candidate was
seen. Read by Claude from the printed structure, no name printed:
- **HTTP 200.** Top level `took`, `timed_out`, `_shards`, `hits`, `aggregations`, `query`. `hits.total` is
  `{value, relation}` with `relation` `eq`; `hits.hits` a list. Each hit has `_id` (`<accession>:<file>`),
  `_index`, `_score`, `_source`.
- `_source` holds every field `search.py` reads: `adsh` (text), `form` (text), `file_date` (`YYYY-MM-DD`), `items`
  (**a list of text**, `['2.05', '7.01']`), `sics` (**a list of text**, `['5311']`), `ciks` and `display_names`
  (lists). Also present, unread: `biz_locations`, `biz_states`, `inc_states`, `file_num`, `film_num`,
  `file_description`, `file_type`, `period_ending`, `root_forms`, `sequence`, `xsl`.
- **Paging works:** 160 hits for the half-year; `from=0` returned 100, `from=100` returned 60; no id on both pages;
  100 distinct accession numbers on the first page. **A page is 100 hits.**
- **A search for forms 8-K also returns 8-K/A.** `filter_reason` drops them ("form is 8-K/A, not 8-K"), the literal
  reading of protocol §12.3's Forms column; an amendment's original 8-K is found by the same query. Kept as built,
  and the drop is counted in each query's record.

**Nothing in `search.py` needed changing.**

**Stage A step 3, `hc case search` (2026-10-15, Opus built and reviewed; for his commit).** `RULE_DATE`
(2026-10-16) in `casebuild/search.py`; `cmd_case_search` in `cli.py`. It refuses: a `--date` that is not today's
local date; any day before the rule date; a later day without `--deviation "<reason>"`; a second run
(`search/candidates.json` exists). It always searches through 2026-10-15 (decision 1), records `run_on` and the
deviation in `candidates.json`, writes `selection-log-1.json` and its public view, and prints per-query counts, the
filter drops and the candidates per type and pool, never a name or an accession number. A run stopped part-way (a
403, a network fault) writes no candidate list; its fetched pages stay in the search folder's cache, and the same
command finishes it. Five tests in `tests/test_case_cli.py` on fake replies of the real shape; 2135 tests,
`make check` green.

**Stage A step 4, the projection (2026-10-15, about 4:25 PM CDT).** From his readings of 10:30 AM the same day
(nothing paid has run since): `docs/phases/evidence/phase-5/projection.md`. **Passes:** about $35 cumulative after
Phases 5 and 5.5, at worst about $41; inside the Anthropic workspace limit and his $5 OpenRouter cap. Committed with
step 3, before the search.

**Stage B step 5, the search (2026-10-16, about 8:55 AM CDT, his command).** `hc case search --date 2026-10-16`, run
on the rule date: `run_on` 2026-10-16, `deviation` null, window 2026-08-01 to 2026-10-15, fallback month from
2026-07-01. Written to the appendix's `search/` folder: `candidates.json`, `selection-log-1.json`,
`selection-public-1.json`, and the page cache. Read by Claude from the printed counts and the per-query records in
`candidates.json`, no name printed. **No short read and no `MAX_RESULTS` hit:** every query's `documents_read`
equals its `total`; the largest is 132 (two pages).

| channel | query | hits | pages | filings kept | documents dropped |
|---|---|---|---|---|---|
| 1 | `"Item 2.05"` | 71 | 1 | 36 | 4 form 8-K/A, 31 SIC outside 2000-3999 |
| 2 | `"new manufacturing facility"` | 3 | 1 | 2 | 1 items lack 7.01 or 8.01 |
| 2 | `"new production facility"` | 2 | 1 | 1 | 1 SIC |
| 2 | `"expand production"` | 21 | 1 | 10 | 7 items, 3 SIC |
| 2 | `"expansion of our manufacturing"` | 5 | 1 | 2 | 3 items |
| 2 | `"capacity expansion"` | 132 | 2 | 49 | 2 form 8-K/A, 53 items, 23 SIC |
| 2 | `"retool"` | 6 | 1 | 1 | 1 items, 4 SIC |
| 3 | `"artificial intelligence" "reduction in force"` | 48 | 1 | 46 | 1 form 8-K/A |
| 3 | `"artificial intelligence" "workforce reduction"` | 17 | 1 | 17 | none |
| 3 | `"artificial intelligence" "reduce our workforce"` | 0 | 0 | 0 | none |
| 3 | `"AI" "reduction in force"` | 50 | 1 | 48 | 2 form 8-K/A |
| 3 | `"automation" "workforce reduction"` | 5 | 1 | 5 | none |

`filings kept` counts distinct accession numbers; a drop counts documents, so a query's kept plus dropped can fall
short of its hits by the extra documents (exhibits) of filings already kept. **Candidates per type, after the union
by accession number within a type:** closure 29 window and 7 fallback (36, the same as channel 1's kept); retool 44
and 18 (62, from 65 kept: three filings found by two queries); ai 50 and 26 (76, from 116 kept). Each type's window
pool is many times its k (2, 2, 1). One query returned no hits; that is a result, not a deviation. Nothing else was
decided that day, by rule. Next: Stage C.

**Stage C step 6, `hc case log` (2026-10-16, Sonnet built; for Opus's review, then his commit).**
`cmd_case_log` in `cli.py`; `load_newest_log` in `casebuild/search.py`. `hc case log <type> show | record <id>
<criterion> pass|fail --reason ... [--public-reason ...] [--disclosed YYYY-MM-DD] | read <id> <criterion>
agree|disagree [--resolution ...] | public`. Each call loads the newest `selection-log-<n>.json` (by number, so 10
follows 9), rebuilt through `from_text`; `record` and `read` apply exactly one change and write the next numbered pair
with `write_log_version`; `show` and `public` write nothing; a `LogError` prints `refused: ...` and writes nothing.
An id of another type than the one named is refused. Three things for the review:
- **§4.3 says the log holds names; the code's log does not.** A row holds the id, type, pool and accession number;
  the names are in `candidates.json`. So `show` joins the two (id, pool, filing date, accession number, names, and
  each criterion's state, the next criterion, the read's state, the type's selection and open problems), and is for
  his terminal only. `public` prints `public_view()` only.
- **`--public-reason` was added** (§4.3's command line did not list it). Without it a `public_reason` could never be
  set from the terminal, and the public view's `reason` would always be empty. Left off, it is empty, never the
  private `--reason`; tested both ways. Its help text says no name, date, figure or place that identifies.
- **`show` omits the reasons** (they can name the company and can be long); they are in the log file.
Nine tests in `tests/test_case_cli.py` on a fake search run (canary names only): a new version and the earlier one
untouched, newest-by-number, seven refusals writing nothing, the other-type refusal, the disagreement needing a
resolution, `public` showing no name and writing nothing, `show`, and a log before the search. 2144 tests,
`make check` green.

**Step 6 reviewed (2026-10-16, Opus); fixes applied.** The three points above accepted: `show` reads
`candidates.json` (names on his terminal only), `--public-reason` kept (protocol §12.4 publishes the log "with each
criterion passed or failed and why", so the public view needs a written reason), `show` without reasons. Found and
fixed:
- **A public reason could name a rejected candidate and pass the name guard on commit:** only a case's
  identifiers go into the term file (§4.1 step 2), so most candidates' names never do. `_check_public_reason` now
  refuses, before anything is written, a public reason holding a name-guard term, any candidate's display name
  (without parentheses and legal form, any case; a name under three letters in its own case), ticker, CIK (with or
  without leading zeros) or accession number (`candidate_terms` in `search.py`), or a date; it fails closed without
  the term file or the candidate list, and says which kind of match, never the match. Checked on the real list by
  counts only: every one of the 174 candidates yields a name term, and thirteen ordinary reasons ("an earlier public
  mention", "not publicly traded" and so on) pass.
- **`public` printed every type's view** under one type's name; it now prints the named type only.
- **A `show` test assertion was vacuous** (no other type in the fake search); replaced.
Ten tests added (seven refusals, the missing term file, `candidate_terms` including a short name); every test sets
`HC_NAME_GUARD_TERMS` to a fictional file, so none reads the real one through git config. 2153 tests, `make check`
green.

**Stage C step 7, the extraction entry, `hc case build` and `hc case assemble` (2026-10-16, Sonnet built; for Opus's
review in a fresh chat, then his commit and push).** Nothing was fetched and no model was called: every test uses a
fake SEC and a fake provider. 2214 tests, `make check` green, `hc protocol check: ok` (no locked identity moved).
- **The entry:** `[models.sonnet-5-5-extraction]` in `experiment/models.toml`: `claude-sonnet-5-5`, route `anthropic`,
  `thinking = "off"`, `max_tokens = 4096`, role `extraction`; $2 input, $10 output, $2.50 cache write, $0.10 cache
  read per million tokens, one rate across the whole context *(live 2026-10-16, Anthropic's models overview and
  pricing pages; training data ends June 2026, same page)*. `ModelConfig` gained `max_tokens` (extraction role only;
  that role needs route `anthropic`, thinking off and a `max_tokens`).
- **The tripwire is structural, not a list of checks.** `experiment.py` is frozen at `prereg-v1`, so `Experiment.model`
  could not be edited. Instead `ModelsFile` keeps the entry **out of `models`** (in `extraction_models`), so every
  sweep plan, run, probe, awareness check, cost estimate, lock and gate sees it as an unknown model, and a future
  path cannot forget a check. `tests/test_extraction_model.py` proves each: every experiment's `model()`,
  `build_plan` (every experiment, official or not), the thinking sub-study on the off-subject placeholder,
  `check_probe_model`, `build_lock`, the gate's `check_model`, and `hc sweep plan` and `run`. Only
  `casebuild/extraction_model.py` reads the entry; at most one is allowed.
- **`hc case build <label> --cutoff D --shape S`:** refusals first, none needing the network or the key, in this
  order: the CIK from `candidates.json` by label (exactly one; not on the command line); the selection log (criteria
  1-4 passed, and `--cutoff` equal to the day before the logged first-disclosure date, protocol §12.6); the case's
  `terms.txt`; `hand-boundaries.json` if present; the extraction entry; **the committed-and-pushed proof**
  (`casebuild/frozen.py`: `extract.py` and `models.toml` clean, and the commit that last changed them on a remote
  branch, else refused); an already-prepared folder. Then the filings (cached), a dry run of `build_section_inputs`
  (a `SplitRefused` prints "needs hand boundaries" and stops before `sources.json` and before the key), then
  `write_sources`, the key, and `prepare_case`, which draws the seed itself (the command has no seed argument and does
  not pass one; a test spies on it). `build.json` gains `provenance` (that commit, the instructions hash, the entry's
  key and hash, the hand file's hash) and `extraction.max_tokens`. It prints counts, tokens and about what the credit
  paid, never a name.
- **`hc case assemble <label>`** reads `terms.txt` and runs `assemble_case`.
- **Points for review:**
  1. `write_sources` now accepts an identical second call as a no-op (so a rerun after a hand-split stop or a failed
     extraction, read from the cache, does not trip write-once); a different list is still refused. The existing test
     was updated to say so.
  2. `prepare_case` gained `max_tokens` and `provenance` parameters (defaults keep every earlier call as it was).
  3. **The cut-off check against the log is added to §4.5** (not stated there): the cut-off must equal the logged
     first-disclosure date minus one day. It guards a typo from admitting a filing on or after disclosure.
  4. **Not built, not in §4.5:** option figures for section 7 (the command passes none, so every option is described
     without figures alike, protocol §12.6's default), and a command to print a filing's extracted text for choosing
     hand-boundary offsets. Either may be needed on the first real case.
  5. **Unverified until the first call:** that `claude-sonnet-5-5` accepts `thinking: {type: disabled}` (its page lists
     thinking as adaptive; Haiku 5.5 accepts it). A 400 would be an `ExtractionError` with no sections written.
  6. `requests_per_minute = 30` in the entry is unused by the builder (calls run one at a time); the file requires it.
  7. The term list is `terms.txt` and the hand file `hand-boundaries.json` in the case's folder (new `CaseAppendix`
     paths); `hand-boundaries.json` is `{accession: {item key: [start, end]}}`, validated strictly in `handfile.py`.

**Stage C step 7, the Opus review (2026-10-16, about 11:45 AM).** Read the whole diff against §4.1, §4.5, protocol
§12.4 and §12.6. The tripwire, the order of refusals, `frozen_inputs` and the seed hold as built: `ModelsFile` is
the only reader of `models.toml`'s entries (the lock and gate drop its file hash and compare identities only), so
the extraction entry is unknown to every experiment path; every refusal in `cmd_case_build` runs before the
`EdgarClient` is made and before the key is read; `frozen_inputs` checks both files clean and their last commit on
a remote-tracking branch; and `prepare_case` gets no seed. Points 1, 2, 3, 6 and 7 accepted as built. Fixed:
1. **The build's criteria check skipped criterion 4.** It required `CRITERIA[:4]` (the first-disclosure check and
   §12.4's criteria 1-3), so a candidate that had not passed `maps_to_shape` could be built. It now requires every
   criterion but the probe (`CRITERIA[:-1]`), as §4.1 step 1 says; the test setup and refusal cases follow.
2. **Point 5 is settled, and the entry as built would have failed its first call.** Anthropic's Sonnet 5.5
   migration guide (read live 2026-10-16): `thinking: {type: "disabled"}` returns a 400 on this model; thinking off
   is `{type: "between_tools"}` (no extended thinking, a text-only reply when no tool is offered, accepted at the
   default effort). The entry now says `thinking = "between_tools"`; `ModelRoute` gained `thinking_between_tools`;
   the Anthropic provider sends it and records `off: thinking {type: between_tools} sent`; a route with both
   settings is refused; `"between_tools"` is refused on every role but extraction, so no locked identity and no
   official request changes (Haiku 5.5's `disabled` body is byte-identical; `hc protocol check: ok`). Decision 2
   (thinking off) is kept as decided. The prices were re-read on the live pricing page and are right ($0.10 cache
   read; the bundled reference's $0.20 is stale).
3. A candidate missing from the log was a `KeyError` traceback; now a refusal.
4. An extraction call that fails now names the error's code and message (scrubbed of the key by the provider),
   so a first-call rejection says why.
5. Two comments claimed `Experiment.model` and `build_lock` refuse the role; they now say `ModelsFile` keeps it out.

**Found outside step 7, for him (KNOWN-GAPS OPEN 2026-10-16):** `SelectionLog.record` refuses anything after a
failure, and `record_read` with `agrees=False` only stores the resolution, so a rejection the reader disputes
still stands. Protocol §12.4 says the opposite ("a rejection the reader disputes does not stand: the candidate goes
on to the next criterion"). Harmless until the first rejection on criterion 3, 4 or 5; fix before then.

Four tests added and the affected ones updated (2218 tests), `make check` green, `hc protocol check: ok`.

**The disputed-rejection fix (2026-10-16, Sonnet built; for Opus's review in this chat, then his commit and push).**
Closes the KNOWN-GAPS OPEN of 2026-10-16. Protocol §12.4: a rejection the independent reader disputes does not
stand, and the candidate goes on to the next criterion with both reasons logged. 2229 tests (up from 2218),
`make check` green, `hc protocol check: ok`. All in `casebuild/search.py`, plus `cli.py` (status line and the
build's criteria check) and tests. No model called, nothing fetched.
- **`Row.disputed(c)` and `Row.met(c)`** are the one place the rule lives: a fail with a read that does not agree is
  disputed; a criterion is met if passed or disputed. `Row.failed` is the first fail that is not disputed, and
  `Row.passed` is every criterion met, so `record` (which stops at a standing failure), `finished`, `selection`,
  `problems` and `_window_short` all read it without change. A disputed fail on the last criterion
  (`not_recognizable`) counts as passing it.
- **Nothing is rewritten.** The fail, its reason and the read with his resolution stay in the saved log. The public
  view marks the criterion `"disputed": true` (only where it is), carries no resolution text, and is otherwise
  unchanged. The log version stays 1: an older file without disputes loads and saves identically.
- **`record_read`** now checks that the criterion's recorded result is a fail (it used to check `row.failed`, which
  no longer names a disputed one). **Point for review (added by me, not in the spec):** a read cannot flip once a
  later criterion is recorded, because that would leave results after a standing failure. A read may still change
  while the rejected criterion is the last one recorded.
- **`from_text` applies each read right after its own result**, so the results that follow a disputed rejection
  load; a read for a criterion with no recorded fail is still refused.
- **`hc case build`'s check** uses `row.met`, so a disputed rejection on 3 or 4 counts as passed there; a rejection
  the reader agreed with still refuses. **`hc case log` status** shows the read for any rejection on 3, 4 or 5
  ("FAIL (disputed, does not stand)", "read: DISAGREES").
- **Tests:** dispute then continue, agree then stand, a standing fail after a disputed one, the last criterion,
  the order by disclosure date, a read that cannot flip, the round trip and two hand-edits, the public view; and
  `hc case build` accepting a disputed rejection on 3 or 4 and refusing one that stands.

**The disputed-rejection fix, the Opus review (2026-10-16, about 12:05 PM, in the same chat).** `Row.disputed` and
`Row.met` carry the rule in one place; the reload order in `from_text`, the unchanged log version, the public view
(no resolution text) and the build's check are right. **The flip rule is accepted:** a read that changed after
later criteria were recorded would leave results after a standing failure. Fixed:
1. **An unread rejection on 3, 4 or 5 counted as finished.** Before the fix that was harmless, because a read changed
   nothing. Now a dispute reopens the candidate, so `selection` could call a type complete, and `_window_short`
   could open the fallback month, while a read that could still change the order was missing. `Row.awaiting_read`
   names such a rejection, and `Row.finished` is false until the read is in; the selection's `waiting` line says
   which read it waits for. This is §4.1 step 1 ("a rejection on 3 or 4 goes to the reader before the next
   candidate") made structural. One test added; two of the new tests that asserted the old behavior were corrected.
2. The status line's loop had been split over three lines by the formatter around a long comment; the comment moved.

**For him, not built (KNOWN-GAPS OPEN 2026-10-16, criterion 5):** a dispute on criterion 5 now lets the log count the
probe as passed, but protocol §12.10's gate check (3) needs "every recognition probe in the set that counts passed on
every model", read from the probe records. So a disputed probe failure would pass the log and still be refused at
the gate. Which governs is his call at step 10 (`probe-verdict`); nothing reaches it before a probe has run.

2230 tests, `make check` green, `hc protocol check: ok`.

**Stage C step 8a, `hc case lock` (2026-10-16, about 1:15 PM, Sonnet built; awaiting an Opus review).** Step 8b (scenario
render and check, §4.6.1) is not built.
- **Where it lives.** `protocol/caselock.py` (`lock_case`, `scenario_check_passes`, `CaseLockError`) and `cmd_case_lock`
  in `cli.py`. **It is not in `casebuild/`:** `test_architecture` bars that package from importing
  `protocol.cases`, and the lock reads the rubric, so the guard was kept and the module put beside `cases.py`.
  `CaseAppendix` gains `rubric_path` (`rubric.toml`) and `scenario_render_path` (`scenario-render.json`).
- **What it does.** Hashes the appendix's `dossier.toml`, `scenario.toml` and `rubric.toml` with `content_hashes`, text
  by `case_lock_text`, written to `experiment/cases/<label>/case.lock` in the repo by a temporary file replaced into
  place. A test proves `hc case lock` and `hc case hashes` produce the same text, and that the gate's
  `check_case_content` accepts it. Hashes only; the label is checked by the appendix's label pattern and `case_path`.
- **Refusals, all before the write:** a bad label; any of the three files missing; probe set 1 with a lock already
  there (write-once); probe set 2 with no lock, an unreadable lock, a lock already at set 2, a changed rubric, or the
  same dossier; a probe set that is not 1 or 2; a scenario check that does not pass.
- **`scenario_check_passes(case)` always refuses** ("the scenario check is not built (step 8b)") until 8b replaces its
  body. The lock takes it as a parameter, so tests inject a passing one. **Until 8b, no real `case.lock` can be
  written.**
- **Tests (17, `tests/test_protocol_caselock.py`), fictional canaries only.** 2247 tests, `make check` green,
  `hc protocol check: ok`.

**Points for review:**
1. **That set 1 actually failed is not checked** for `--probe-set 2`; the probe records do not exist until step 10.
   The gate's `check_case_probes` refuses a re-probe whose first set passed, so the failure is caught late, not
   missed. A step-10 hook (the lock reading the probe verdicts) would close it; not built.
2. **The label is not checked against the search's candidate list** (the doc says "the neutral candidate id"; only the
   label's shape is checked). `hc case build` does check it. Adding it here would need the search file at lock time.
3. **The lock does not check that the dossier and scenario came from the same build** (no `assembly.json` or
   `scenario-render.json` hash check). 8b's render record is where that belongs.
4. **A set 2 may change the scenario file as well as the dossier;** only the rubric must be unchanged. The doc and the
   gate say the same; noted in case a coarsening should leave the scenario alone.
5. **The move out of `casebuild/`** was forced by the architecture test, not chosen; check it is the right home.

**Stage C step 8a, the Opus review (2026-10-16, about 1:30 PM, in the same chat).** The core is right: the lock is
written by the gate's own `content_hashes` and `case_lock_text`, every refusal precedes the write, and the set-2 rules
match `check_case_order`'s. Checked beyond the tests (which use a temporary repo): `experiment/cases/` lies in no frozen
set (`protocol/sets.py`'s patterns cover only `sweep/` and `analysis/` code), so a committed lock leaves `hc protocol
check` ok; and the image copies all of `experiment/` (`infra/docker/Dockerfile`), so the container gate finds it. The
move to `protocol/` (point 5) is right: the architecture test's guard is the design, and `protocol/` is where the case
record lives. Fixed:
1. **A hand-edited dossier would have been locked.** Set 1 now requires `assembly.json` and its `dossier_sha256` to
   match, so the locked dossier is the one that passed the flag review and the term check. This also answers point 2:
   `assembly.json` exists only for a candidate `hc case build` accepted. Two tests.
2. **Set 1 was not truly write-once:** `exists()` then `replace()` would overwrite a lock written in between. Set 1 now
   links the temporary file into place (as the appendix's `write_once` does); set 2 still replaces. One test.

Points 1 and 4 accepted as written (the gate's `check_case_probes` catches a re-probe after a passing set; whether a
coarsening may touch the scenario belongs to the coarsening design). **Logged, not fixed:** the set-2 branch reads the
write-once `dossier.toml`, so it is reachable today only by a hand replacement (KNOWN-GAPS OPEN 2026-10-16, "where a
coarsened dossier lives"). 2250 tests, `make check` green, `hc protocol check: ok`.

**Stage C step 8b, `hc case scenario render` and `check` (2026-10-16, about 1:45 PM, Sonnet built; reviewed below).** Built by §4.6.1, items 1 to 9. Steps 9 and 10, coarsening and the real rows files are not touched.
- **Where it lives.** `casebuild/scenario.py` (the rows file's model, `render_in_memory`, `render_case_scenario`,
  `check_scenario`, `drop_sentences`); `cmd_case_scenario` and the `case scenario render|check <label>` parsers in
  `cli.py`; `CaseAppendix.scenario_figures_path`; `toml_text` in `scenarios/render.py` gained an optional `header`
  argument (its default is the old header, so `hc scenarios check` is byte-for-byte unchanged). **No architecture
  rule blocked an import:** `casebuild/` imports `scenarios.render`, `dossier.figures` and `experiment`, none of
  which the rule bars, and `protocol/caselock.py` imports `casebuild/scenario.py`. `scenario_check_passes` in
  `protocol/caselock.py` now calls `check_scenario` and raises `CaseLockError` with the failures by criterion.
- **How the fill is reused.** The sentence drops are made on the template (a copy of the parsed `ScenarioSource`
  with the dropped sentences removed, the rules without rows removed, the lever details emptied), and then the
  existing `fill_scenario` runs over a `FigureSet` of the case's values: its `Filler`, caps, total, rules and
  `Scenario` validation are the fictional render's own. The case's values are `Resolved` objects over the
  fictional rows (so units and formatting are the fictional ones), built by scaling each file row with
  `scale.py` and filling derived rows with `evaluate_formula` over the fictional formulas.
- **The rows file** is `scenario-figures.toml` in the appendix, `[rows.<row_id>]` tables with `value` (unscaled),
  `unit` (must equal the fictional row's), `scale` (`dollars`, `heads`, `none`), `per` (required on an unscaled
  dollar row, refused elsewhere), `source` (`pre_cutoff` with an `accession`, or `first_disclosure`) and `locator`;
  or `equals_total = true` and nothing else, on a lever's cap. Refused: an id that is not a fictional row, a label
  row, `equals_total` on a row that is no cap, `first_disclosure` on any row but the total.
- **The check** (`check_scenario`) loads the same inputs, re-checks every source (an accession in `sources.json`
  that `cutoff.admit` accepts against `build.json`'s cut-off, which must equal `sources.json`'s; the total alone
  first-disclosure, its date the newest selection log's `disclosed`, one day after the cut-off), then re-renders in
  memory and compares **both** `scenario.toml` and `scenario-render.json` byte for byte. It prints failures grouped
  by criterion (`rows file`, `cut-off rule`, `first-disclosure rule`, `criterion 4 (maps_to_shape)`, `render`) with
  row ids, lever keys and counts only; a test proves a name, a figure and an accession typed into the rows file
  never reach the output. The selection log is read only when a row is `first_disclosure`.
- **Tests (71 new, `tests/test_casebuild_scenario.py`), fictional canaries only,** run against the real S1 to S4
  templates with rows generated from each shape's own fictional figures: a fully sourced case on all four, the
  shape's words and structure kept, a sparse case with dropped sentences, equal treatment across S1's lever details,
  equal treatment emptying an S3 option text (refused), caps equal to the total (explicit, under 100 stated, under
  100 derived), a total under 100 refused (three scalings), an omitted S2 joint-cap rule, every row and source
  refusal, a hand-edited `scenario.toml` and an edited record failing the check, the rows changing after the
  render, `hc case lock` passing end to end after the render and refusing before it. 2321 tests, `make check`
  green, `hc protocol check: ok`.

**Points for review** (each is a reading of §4.6.1 where it was silent or could be read two ways; none was a fork I
stopped on, but each is his or Opus's to overrule):
1. **A count derived from a headcount is a headcount.** A derived row of unit `count` whose formula reads a
   `heads` row (or another such row) is treated as a heads figure: under 100 it reads "fewer than 100", which blocks
   the formulas that use it. §4.6.1 item 5 speaks of "a heads figure"; the protocol says "a scaled headcount".
   Reading it narrowly (file rows only) would print, for example, S3's "29 people may accept" at a small plant.
   A cap that is under 100 by either route equals the total (the same rule, item 5).
2. **A cap with no row, no formula and no `equals_total` is refused,** not defaulted to the total. Item 2 says a cap
   row "may" say `equals_total` and item 4 says "every cap is a row"; the strict reading makes the rows file say it.
   **This bites S4:** `s4_use_cap` is derived from the seven cut caps and `s4_annual`, so a case that lacks any of
   them must write `s4_use_cap = { equals_total = true }` (23 of 37 single-row removals refuse for this reason).
3. **A file row overrides a fictional derived row of the same id.** Needed because every shape's total is derived in
   the fictional figures (`s1_roles`, `s2_shortfall`, `hc_p6`); it also lets a case state any other derived figure
   directly. A file row for a derived id is not range-checked.
4. **A scaled value is rounded to the fictional row's step** (`resolve`'s rule) after the three-figure or nearest-5
   rounding, so the text and the formulas see the same number. For a `usd_m` row below $10 million this rounds the
   three figures to one decimal of a million.
5. **An emptied situation or currency note is refused** along with the four fields item 6 names. Neither can be
   emptied by the real templates (the total is always present); the check is for a changed template.
6. **S3 and S4 are whole or refused, by the rule as written.** Sweeping every base row out of a fully sourced case
   one at a time: S1 renders in all 34 (in 23 of them equal treatment empties the lever details, which item 6 allows); S3 renders
   only when the missing figure sits in the situation text (11 of 41), because any dropped sentence in an option text
   takes every figure out of all three and the retool and sell texts are made only of sentences with figures, so the
   retool text empties and the render refuses; S4's fund text is one sentence holding `s4_annual` and `s4_years`, so a
   case without `s4_years` from a pre-cut-off document refuses (rule 1 forbids taking it from the disclosure). This
   is what item 6 and "What this costs" imply; it is stated here so it is not a surprise at Stage D.
7. **`scenario-render.json` is compared byte for byte too,** which item 9 does not ask. It holds no figure; the
   comparison keeps the record honest (it is the record of what was dropped).
8. **The render writes `scenario.toml` first and the record second.** If the second write is refused, the first
   stands and the case needs its folder cleared by hand (as `hc case build` does for its three files).

**Stage C step 8b, the Opus review (2026-10-16, about 2:30 PM).** Read against §4.6 and §4.6.1 with the four real
templates and the fictional rows. **Three faults found and fixed; the eight points accepted.** 2326 tests (five new,
two changed), `make check` green, `hc protocol check: ok`.
- **Fixed: a headcount could be stated unscaled.** Nothing stopped a rows file giving a plant's headcount, or any
  other count of people, with `scale = "none"`: it printed rounded only to the fictional step (a probe: 1,234 people
  rendered as "1,230 employees"), escaping both the factor and "fewer than 100". Now a case row for any count the
  fictional figures derive (every one is a number of people: `hc_*`, `s1_roles*`, `s3_movers`, the positions, the
  plants' hires) must be `heads`, and in a shape whose unit is people the total and every stated cap must be a
  headcount. Count rows the fictional figures give as values (months, weeks, industry statistics) may stay unscaled.
- **Fixed: a cap set to the total was printed as a figure.** A cap at `equals_total`, or set to the total because it
  is under 100, holds the total so the lever works, and the text then printed that value wherever the cap's row
  appears: S3's "at most {s3_movers} people" read as the whole plant, "the retooled plant needs {total} of its {total}
  positions", S2's wage-cut maximum stated as the whole shortfall. No source gives those numbers (§4.6 rule 2), and
  rule 3 speaks of caps, not text. Now such a cap, and every row derived from it, is a **stand-in**: the menu heading
  may print it (its sum of caps is the sum of what the model is given), and every other text drops its sentence by
  item 6. Consequence for S3: an `equals_total` on `s3_retool_positions` or `s3_buyer_positions` now refuses the
  render (KNOWN-GAPS OPEN 2026-10-16, "S3 renders only with every option's figures").
- **Fixed: a fictional fact reached the case through a label.** Item 3 lets label rows take the fictional value as
  "names in the wording, not facts". Six of the seven labels are plant numbers; the seventh, `s3_alloc_basis` ("in
  proportion to revenue"), is how the fictional company shares corporate costs, which §4.6 keeps out ("everything of
  its shape except the facts"). Only the `plant_<n>_no` labels now take the fictional value; any other label has no
  case value and its sentence drops (S3 loses one situation sentence in every case).
- **Points 1 to 8:** accepted as Sonnet read them. 1 is the protective reading the protocol's "a scaled headcount"
  supports. 2 (strict caps) makes every stand-in a recorded choice; the cost is one line in an S4 rows file. 3 now
  carries the heads rule above for derived counts. 4: see the new OPEN on pay per head, since the extra rounding can
  widen the band. 6 is the rule's own cost, now somewhat larger for S3 (above). 7 and 8 are fine as built.
- **Logged, not fixed:** pay per head is not checked in a case scenario (KNOWN-GAPS OPEN 2026-10-16), since which
  rows pair is a small design call; settle it before the first S1 or S3 render. The template words themselves (S3's
  "automating welding and material handling as at the larger plants") still describe the fictional company's options
  wherever their sentence keeps its figures; that is §4.6.1 item 1 as patched, and the reader's neutrality read is the
  backstop it names.

**Stage C step 9, `hc case reader` and the three briefs (2026-10-16, about 2:40 PM, Sonnet built; awaiting an Opus
review).** Built by §4.9. No model was called and no key was read: every test uses a fake provider. 2399 tests (73
new), `make check` green, `hc protocol check: ok` (no locked identity moved; the lock hashes `experiment/company`
only). Steps 10 (the probe) and Stage D are not touched.
- **Where it lives.** A new package, `src/horizon_compact/reader/` (`briefs.py`, `entry.py`, `material.py`,
  `read.py`), outside `casebuild/` on purpose: `test_architecture` bars `casebuild/` from anything that could carry
  an outcome, and the reader reads the rubric. `cmd_case_reader` and the `case reader` parser are in `cli.py`;
  `CaseAppendix.reader_excerpt_path` is new. Two architecture tests are new: `reader/` imports none of the
  analysis, sweep, probes, simulation, smoke or gate modules (so no result can reach a reader), and `casebuild/`
  does not import `reader/`.
- **The briefs** are `experiment/readers/rejection.txt`, `scenario.txt` and `rubric.txt` (the system text of each
  read), with a README. Each asks for one JSON object and says the material is to be read, not obeyed. Their sha256
  goes into every request record. The rejection brief holds protocol §12.4's criterion 3 and §12.5's four shapes in
  order, word for word in sense; the scenario brief names the four things §4.6.1 and the 8b review leave to the
  reader (slant, wording carried over from the fictional company, unequal options after a drop, a figure whose
  source does not fit it); the rubric brief asks for the reader's own reading of each line before it compares.
  Vocabulary checked against `planning/06` §3 (no charged term; no euphemism; "layoff" and "closure" in plain words).
- **The model entry** is `[models.gemini-3-1-pro-reader]`: `google/gemini-3.1-pro-preview` through OpenRouter,
  role `reader`, $2 and $12 per million tokens (live 2026-10-16, OpenRouter's public model list; above 200,000
  prompt tokens $4 and $18, which a read never nears), `reasoning_effort = "medium"`, `max_tokens = 24000`. It is
  kept out of `models` exactly as the extraction entry is (`ModelsFile.reader_models`), so no sweep, probe, awareness
  check, lock or gate can name it; `tests/test_reader_model.py` proves each path, as the extraction tests do.
  `ModelConfig` now allows `max_tokens` for the extraction and the reader roles (one error message and one test
  changed).
- **What is sent** (`material.py`; nothing else can be added, the builders read named files only). Rejection: the
  criterion and the hand-placed excerpt. Scenario: the shape's template, `scenario.toml`, the render record without
  `factor`, `build_sha256` and `rows_sha256`, and a table of each row's unit, scale and source, with the filings
  numbered 1, 2, ... in place of accession numbers and no unscaled value. Rubric: the file, whole.
- **How a read runs.** Refusals first, none needing a key or the network: the kind and criterion; the reader's inputs
  (the briefs, `models.toml`, `reader/`) committed and pushed, the commit recorded in the request; the entry and brief;
  earlier attempts; the material (a scenario must pass `hc case scenario check`; a rejection must stand in the log
  with no read yet); then the spend warning (the most the read can cost, from his own OpenRouter credit; `--yes`
  skips the question); then the key, then the one call. It writes `reader-<kind>[-<criterion>]-<n>-request.json`
  and `-reply.json` into the case's folder, write-once, and prints the reading, token counts, the estimated cost
  and, for a rejection, the `hc case log ... read` command to run. It never writes the log.

**Points for review** (each a reading where the docs were silent or could go two ways; each his or Opus's to overrule):
1. **Scenario and rubric reads have no recording path beyond the reply file.** §4.9 says an outcome goes "into the
   selection log (`hc case log ... read`) or the case's rubric record". The log is keyed by criteria 1 to 6 and has
   no place for a scenario read; no rubric record exists in code (only `rubric.toml`, whose form is not coded). I did
   not invent either. A rejection read is logged by the existing command, run by him. The scenario and rubric
   outcomes live in the numbered reply files until he decides where a disagreement is logged "with both readings"
   (protocol §12.9). This is the one thing to settle before Stage D's first scenario read.
2. **The rejection read covers criteria 3 and 4 only** (`real_decision`, `maps_to_shape`). §12.4 also has the reader
   read criterion 5's rejection, but that rejection is a probe failure, and §12.9 gives the reader "only the criteria
   or the rubric with its source excerpts", not a probe answer. It belongs to step 10 and to KNOWN-GAPS OPEN
   2026-10-16, criterion 5.
3. **The excerpt is a hand-placed file** (`first-disclosure-excerpt.txt` in the candidate's folder); nothing stores
   one before the first real fetch. The command checks that it is present, not empty and under 200,000 characters.
   Which part of the first-disclosure document it holds is a Stage D choice, and an excerpt that leans is the same
   neutrality risk the scenario rule has: worth one line in the Stage D procedure.
4. **A rejection read starts blind.** The drafter's reason and the recorded result are not sent (§12.9 lists
   neither). The command still requires the log to hold a standing fail on that criterion with no read, which keeps
   one read per rejection and in the right order.
5. **The scenario table hides what the reader does not need and could use to recognize the company:** unscaled
   values, the scaling factor (private, protocol §12.6), the build and rows checksums, accession numbers. The reader
   cannot check a figure against filing text it is not given; the brief says so and asks only whether the source
   listed could give the figure and whether anything but the total is sourced to the first disclosure.
6. **The rubric is sent whole, and its blind-first reading is asked of the reader, not enforced.** Enforcing it
   would need the rubric's schema, which is not coded. The reply is by "line", as the file names its lines.
7. **A read is made once.** Every attempt leaves a numbered request and reply record, so nothing is overwritten and
   a failed call or a cut-off reply is on record. A later attempt is allowed only when every earlier one produced no
   usable reading (a failed call, a reply stopped at the token limit, or a reply not in the brief's format); after a
   usable reply, or three unusable attempts, the command refuses. This stops a reader being asked again until it
   says what is wanted, and cannot be used to shop for a reading. It is a rule I added; §4.9 says only "write-once".
8. **A reply's format is strict about contradictions.** "neutral" with a concern listed, "concerns" with none, and a
   rubric "agrees" with a disagreeing line or a stated reason are not readings. An unknown extra field is ignored.
9. **The model entry's choices are mine:** unpinned (the stored reply names the host; a pin would fail closed where
   OpenRouter's slug and host name differ, as `Google` and `google-vertex` do); reasoning `medium`, sent and recorded
   because the level cannot be turned off; `max_tokens = 24000` with reasoning counted in it. The most one read can
   cost is about $0.29 for the output plus its input (about $0.06 per 30,000 tokens); fifteen reads at the worst
   would be about $5, his cap. Decision 3's "about $1" is the likely cost, not the bound.
10. **Decision 3's "training data well before the window" rests on the release date, not a stated cutoff.**
    OpenRouter lists `knowledge_cutoff: null` for this model. It was released 2026-02-19, so it cannot have seen
    events from August to October 2026; that is what the decision needs, and it is stated here as inferred.
    It is also a preview id: a retirement would fail the first read with a named error, and the entry would change
    (a logged change to the instrument).
11. **Unverified until the first live call:** that this model's reply puts its text in `message.content` with the
    reasoning kept apart (the provider handles the OpenRouter shape, and tests use a fake), and that
    `reasoning_effort` is accepted as sent (the model's `supported_parameters` list it). A failure is a recorded
    attempt with a named error code and costs nothing but the call.
12. **The reader's inputs are frozen like the extraction's:** the briefs, `models.toml` and `reader/` must be
    committed and pushed before a read, and each request records the commit. A later edit to a brief or to
    `reader/` therefore needs a commit and push before the next read, and is a change to the instrument (logged
    here with its reason).

**Stage C step 9, the Opus review (2026-10-16, about 3:50 PM; fixes and decisions applied the same session).** 2423
tests (24 new), `make check` green, `hc protocol check: ok`. No model was called and no key was read. His decisions
6-8 below were taken as recommended. Sonnet's twelve points: 2, 4, 5, 9, 10, 11 and 12 accepted as built; 1, 3, 6
and 7 settled below.
- **Fix 1, the request record is written before the call.** It was written after the call returned, so an
  interrupt or crash during a call left no record, money spent, and the next attempt took the same number:
  the once-only rule could be stepped around without a trace, and the "request with no reply" refusal could
  not fire. Now the key is read, then the request is written, then the call; a call that never returns leaves a
  request with no reply, and the next attempt is refused until he has looked. A key that cannot be read leaves
  no record.
- **Fix 2 (point 7 amended), a scenario or rubric is read once as it stands.** The once-only rule counted
  attempts by kind, so a scenario fixed after a "concerns" reading could never be read again and the lock would
  have locked content no reader saw. Now a rejection is read once whatever its excerpt (a changed excerpt after a
  reading is how one would be shopped for); a scenario or rubric is read once per material (the request's part
  hashes), every earlier read kept on record. Three unusable attempts on the same material still end it.
- **Fix 3 (point 8 tightened), a rejection reply's shape must fit.** `real_decision` gives no shape;
  `maps_to_shape` gives S1-S4 on a pass, "none" on a fail, either on cannot_tell. The brief now says so.
- **Fix 4, a rubric reply holds at least one line.** A "disagrees" with no lines was a usable reading and
  spent the one read on nothing. The brief now says so.
- **Fix 5, a cap the render set to the total is marked in the sources table** whether it was `equals_total` or
  a stated cap under 100; before, the second showed its original source while the scenario printed the total,
  inviting a false figure_source concern.
- **Decision 6 (point 1 settled), `hc case lock` refuses until the reads are settled:** the scenario and the
  rubric, exactly as locked (by sha256 against the read's material), each have a usable read, and each
  "concerns" or "disagrees" reading has his written resolution, `hc case resolve <id> scenario|rubric
  --resolution "..."` (new; write-once `reader-<kind>-<n>-resolution.json` beside the reply, with that reply's
  sha256). This is how DoD 4's "every rubric read" is proved rather than asserted. Both readings stay on record:
  the reader's in the reply, his in the resolution (protocol §12.9).
- **Decision 7, the log's read is taken from the reply.** `hc case log <type> read <id> <criterion>` lost its
  agree/disagree word: it finds the usable reply in the candidate's folder (refused if none, so a read never made
  cannot be logged), takes the verdict from its reading, and stores the reply's file name, sha256 and reading
  beside the verdict. `record_read` takes a `ReaderReply`, and a saved log whose verdict differs from its reading,
  or whose read names no reply, is refused on load. **Criterion 5's read** has no reader reply yet: it is refused
  here and belongs to step 10 (OPEN 2026-10-16, criterion 5), which must give it a reply record of the same form.
- **Decision 8, "cannot_tell" is not a dispute: the rejection stands,** logged with the reader's reading
  ("could not tell (stands)" in the status). The protocol's word is "disputes"; counting a non-answer as one would
  add to it, and deciding it per case after reading the excerpt is the judgment decision 4 ruled out.
- **Point 3, the excerpt:** a rule in Stage D step 11 (above), fixed before any excerpt exists.
- **Point 6, the rubric's blind-first reading** is asked, not enforced: in one call the reader always sees the
  mapping beside the excerpts. A two-call read (excerpts alone, then the mapping) needs the rubric's coded form;
  it is to be weighed when that form is written. For his methods page: "asked, not enforced".
- **The running total.** The spend question now prints the reader's estimated spend so far across every case
  in the appendix (the sum of each reply record's `estimated_usd`; a record whose cost cannot be read is counted
  and named, never taken as zero) and the total with this read at its worst. It does not refuse: no reader cap
  was set. Note that the projection (§6) bounds the reader at $2 for about 30 reads, while one read's worst is
  about $0.35; the likely cost stands, the bound does not, and the running total is the check.

**Stage C step 10a, the probe code on fakes (2026-10-16, about 4:20 PM; Sonnet built; for an Opus review).**
2493 tests (70 new), `make check` green, `hc protocol check: ok` (no locked identity moved). No model was called, no key was
read, no AWS call was made, and no `task.json` or Terraform file changed. What 10a is and is not is in §5, step 10.

**His decision, criterion 5 (closes KNOWN-GAPS OPEN 2026-10-16, "a disputed probe failure"; recorded there too).** A
reader's dispute CAN turn a probe failure into a pass, and the probe's verdict record carries the result, so the
selection log and the gate's check (3) always agree. The reader is shown only §12.8's definition of "names the
company", the flagged answers and the case's private term list. The verdict record holds the original verdict, the
reply's file name and sha256, his resolution on a dispute and the final `passed`; the gate reads only `passed`. A
disputed failure is not coarsened. Proof: `test_the_readers_reading_decides_the_final_passed_and_the_log_always_agrees`
takes the reader's three readings through the reply, the verdict, the log row and the gate's `check_case_probes`.

- **Where it lives.** A new package, `src/horizon_compact/caseprobe/`: `layout.py` (the S3 keys, §12.8's message),
  `upload.py`, `run.py` (the container's three calls), `verdict.py`, `s3reader.py`, `github.py`. Not in `probes/`
  (the Phase 2.5 comprehension probes), and not in `casebuild/` or `reader/`, which the architecture tests bar from
  anything holding a result or a probe answer. `horizon_compact.caseprobe` is added to the reader's barred modules, and
  a new test bars `casebuild/` from importing it. **The one channel from a probe answer to the reader is a file** the
  reader's material builder reads (`probe-flagged-set-<n>.json`), never an import.
- **The reader, extended.** `reader/material.py`: `PROBE_CRITERION`, `NAMES_THE_COMPANY` (§12.8's sentence, checked
  against the protocol text by a test), `probe_rejection_material` (three parts: Definition, Term list, Flagged
  answers; nothing else can be added). `reader/read.py`: a per-set stem (`reader-rejection-not_recognizable-set<n>`),
  `probe_set` on `run_read`, `probe_read_ready`, `probe_reply_on_record`, and `rejection_reply_on_record` accepting
  `not_recognizable`. `experiment/readers/rejection.txt` gained the third criterion (its sha256 changed; no read has
  yet been made with any brief, so this is not a change to the instrument after use).
- **`hc case upload <label> [--set n] --profile p [--bucket b]`** (laptop). Refuses unless `case.lock` is committed and
  on a remote branch with the working copy unchanged, is for that probe set, and the three files hash to it; then
  three exclusive puts to `cases/<label>/set-<n>/`. A re-run passes where the stored object equals the file; one that
  differs stops the run before any put.
- **`hc case probe <label> --model m [--set n] [--cap-usd c]`** (the container's command). Refuses before any call
  outside a container; for a model whose role is not `main` or `second_family`, or whose route is not Anthropic or
  OpenRouter, or an unpinned OpenRouter model; for a `case.lock` in the image that is missing or for another set; for
  content in storage that does not hash to it; for a worst case above the cap. Then three calls: the dossier as the
  system text, §12.8's message word for word, no tool, `max_tokens` 4000. A reply is never retried; an API error is
  retried with backoff and kept under `errors/`; a call with a record is skipped. Each answer is one write-once
  object with the usual provenance, image digest included.
- **`hc case probe-verdict <label> [--set n] [--resolution "..."] --profile p`** (laptop). Step 1: every answer that
  is not exactly "unknown" is shown with a term-list hint and he answers whether it names the company; everything is
  saved (`probe-reads-set-<n>.json`, write-once), so a re-run never asks again. If none names it, every call passes
  and the verdict objects are written. Otherwise the flagged answers go to `probe-flagged-set-<n>.json` and the
  command stops and says to run `hc case reader <label> rejection --criterion not_recognizable --set n`. Step 2 (the
  same command again): with the reply on record, "fail" and "cannot_tell" leave the flagged calls failed, "pass" passes
  them and needs his `--resolution`. The reply must have been given exactly the flagged answers now on record (the
  request's part hash is compared).
- **The S3 probe reader** (`read_probe_records`): one `ProbeRecord` per call object, `LastModified` from the listing,
  `passed` from the verdict. **Fails closed:** a call with no verdict, a verdict naming another call, or a `passed` that
  is not literally `true` is not passed. **The GitHub reader** (`read_ci_runs`): one `CiRun` per Actions run from `gh
  api --paginate ... --jq` (one JSON object per line) and the record at its head commit from `git show`, `None` where
  the commit holds none; both programs are injected. Both feed `check_case_probes` and `check_case_order` in tests.

**Points for review** (each a reading where the docs were silent or could go two ways; each his or Opus's to overrule):
1. **One reading covers every flagged answer of a set.** The reply has one `reading`; "pass" means no flagged answer
   names the company and disputes all of that set's flagged calls, "fail" means at least one does. A per-answer reading
   would let a dispute clear one call and not another; I did not build it because the rejection reply's form is one
   reading per criterion and the log holds one. If two flagged answers differ in kind, the reader says "fail".
2. **Only the answers he flagged go to the reader.** A term-list hit he overruled is not flagged, so the reader does not
   see it. The reader therefore disputes his reads of answers he thought named the company; it never second-guesses an
   answer he passed. The alternative (send every non-"unknown" answer) enlarges what leaves the laptop and widens the
   reader's task to the whole probe.
3. **The term list, with its names, is sent to OpenRouter and the reader model's vendor.** The decision asks for it. It
   is the one place a real company name leaves the laptop in Phase 5 outside the SEC; the dossier never does. The request
   record in the private appendix holds it, as it holds an excerpt.
4. **The read is per probe set and made once per set** (`-set1`, `-set2` in the file names). `--set` defaults to the set
   the committed `case.lock` is for. The log's criterion 5 holds the candidate's final probe outcome, so `hc case log
   ... read` takes the newest set with a usable reply. A first-set failure that stands is coarsened, not rejected, so it is
   not logged unless set 2 also fails; the verdict command prints which of the two next steps applies.
5. **A criterion 5 read does not need a standing fail in the log** (criteria 3 and 4 do). A first-set failure is not yet a
   rejection. It does refuse if the log already holds a criterion 5 read. His order on a failure: `probe-verdict`,
   `hc case reader`, `probe-verdict` again; then, if the rejection goes on to stand or is disputed, `hc case log ...
   record ... not_recognizable fail` and `read`.
6. **"cannot_tell" is not a dispute** (decision 8 carried over): the flagged calls fail and a `--resolution` is refused.
7. **The verdict is written only when the set is settled**, because the S3 write-once rule would otherwise forbid
   updating a verdict after the reader's reply. The cost is that nothing is in S3 between his read and the reader; his
   reads live in the private appendix until then. A run that stops part-way writing verdicts is finished by the same
   command (a stored verdict equal to the one it would write is skipped; one that differs stops it).
8. **Key names.** The spec said "one `verdict.json` per call beside" the call object; the verdict is
   `call-<i>.verdict.json` beside `call-<i>.json`, so a listing tells them apart and the reader pairs them by name.
9. **"Unknown" is the exact word**, ignoring case, punctuation and whitespace (`Unknown.`, `**UNKNOWN**`); anything
   longer, an empty answer, or a call whose status is not "replied" (truncated, no text) goes to his read.
10. **`max_tokens` is 4000 for every probe call and the default cap is $2.** §12.8 fixes neither. A reasoning model's
    reasoning counts toward the 4000; a truncated answer is stored with status `truncated` and goes to his read. The cap
    check uses the same worst-case estimate as a sweep. Measured from `models.toml`'s prices: the worst case for three
    calls is about $0.015 (Haiku 5.5) and $0.005 (gpt-oss) on a 30,000-token dossier, and $0.036 and $0.013 on a
    100,000-token one, so $2 never binds; it is a tripwire against a wrong file.
11. **The container is the only place a case probe runs.** There is no laptop path (the sweeps have one for development);
    the probe is official-only, so a laptop run is refused before any key is read. Bedrock and local routes are refused.
12. **`upload` requires the lock pushed, not only committed.** Stricter than §4.8's wording; the container needs the pushed,
    deployed image anyway, and the gate's order check compares the CI run's time with the first probe's.
13. **The verdict covers whatever models have calls in the set** (each must have exactly calls 1 to 3). It does not check
    that both official models are present: the gate does, from `lock.models`.
14. **What is NOT built, on purpose (10b or later):** `task.json` (`s3:GetObject` and `s3:PutObject` on `cases/*`);
    launching the task (`--launch`, like the awareness probe's); any command that runs `check_case_order` and
    `check_case_probes` from the laptop on a frozen case (Stage E's proof, and Phase 5.5's wiring into `hc sweep
    launch`); a check at `hc case lock --probe-set 2` that set 1 actually failed, which the probe records can now answer.
15. **Unverified until the first live use:** that `gh api --paginate` with this `--jq` prints one object per line across
    pages and fills `{owner}/{repo}` from the clone; what GitHub's run listing holds once a run is expired or deleted (a
    missing run is absent, so the order check refuses: fails closed); that `LastModified` from `list_objects_v2` is the
    time the write-once object was written (it is S3's own); and that OpenRouter's pinned route answers a no-tool
    request with the text in `message.content` (the same unverified assumption as the reader's, point 11 of step 9).
16. **The reader's frozen inputs changed** (`reader/`, `experiment/readers/rejection.txt`), so `hc case reader` refuses
    until this step is committed and pushed, by design.

**Stage C step 10a, the Opus review (2026-10-16, about 4:50 PM).** Points 1, 6-9, 11 and 12 stand as built. Four
fixes applied, and his decision on a fifth; 2496 tests, `make check` green.
- **His read takes only a plain yes or no.** It took exactly `y` as "names it" and anything else (Enter, `yes`, the
  end of input) as "does not", and the read is saved write-once, so a stray Enter passed an answer that named the
  company with no way back. Now y/yes/n/no only, asked again up to three times, then refused; the end of input is
  refused. Nothing is saved until every answer is read.
- **The brief no longer tells the reader the answers were flagged.** "Each answer was set aside because a check
  flagged it as naming the company" contradicted the brief's own "you have not been told what anyone else
  concluded"; criteria 3 and 4 are not told a rejection was made either. Removed.
- **Only the term list's directives leave the laptop** (amends point 3). The raw file was sent, comments included,
  and the list also holds people, products and places; the brief described it as names, tickers and brands only.
  Now only the `term:` and `term-i:` lines are sent (the list must parse), and the brief says what the roles may be
  and that a person or a place alone does not name the company.
- **The log takes the reply of the newest set with flagged answers** (amends point 4). It took the newest set with
  any reply, so after a coarsened set 2 was flagged and before its read, `hc case log ... read` would log set 1's
  reply. It now refuses until that set is read.
- **His decision: the brief's reading of §12.8's definition stands** (point 3 of this review, 2026-10-16). The
  material gives §12.8's sentence word for word; the brief adds that a name counts "written in full or in a form a
  reader would take for it", and that a listed term used only as an ordinary word does not. Both kept, as a stated
  interpretation of the pre-registered definition, made before any read. **For his methods page** (his to write).

**Stage C step 10b, the grant and the launch (2026-10-16, about 5:10 PM; Opus built).** 2497 tests, `make check`
green. No AWS call was made from here; the apply is his.
- **The grant.** `infra/iam/task.json` and `infra/iam/boundary.json` each gain `cases/*` on `ResultsObjects`
  (`s3:GetObject`, `s3:PutObject`) and on `ResultsList`'s `s3:prefix`, nothing wider; the architecture test now
  pins the four prefixes. The boundary is the `bootstrap` root (his plan and apply); the task role is `main`, which
  the deploy applies on push. The list grant also means a missing verdict reads as missing, not AccessDenied.
- **`hc case probe <label> --model m --launch --profile p`** (laptop). Before any task starts, the container's
  checks are made again on the laptop (`check_probe_launch`): the model's role and route, `case.lock` committed and
  on a remote branch, the stored content hashing to it for this set, the worst case under the cap, and a set not
  already complete for this model. Then one Fargate task running `hc case probe <label> --model m --set n
  --cap-usd c`, which checks everything again. One task per model at a time (the sweep launcher's rule: tasks share
  the model's request quota).
- **Not proved until the first case:** the task role's grant in use, `LastModified` on a `cases/` call object, and
  the three unverified points of 10a point 15. All are the first case's probe, Stage D.

**Stage D step 11a, the build for §4.6.2 (2026-10-17, about 5:10 AM CDT; Sonnet built; for Opus's review in a fresh
chat, then his commit and push).** No document was fetched and no read was made: every test uses a fake SEC and fake
replies. 2508 tests (11 added), `make check` green, `hc protocol check: ok`.
- **The brief changed, and it is a change to the instrument.** `experiment/readers/rejection.txt`: the
  `maps_to_shape` paragraph is replaced by §4.6.2's text (two parts, the shape and the total, the S2 definition,
  the quoted sentence on a pass, the too-small note). The shape list, the order, the `real_decision` and
  `not_recognizable` paragraphs and the reply format are untouched. **Reason:** the brief judged the shape alone, so
  a reader would dispute a rejection for a missing total (§4.6.2). The only read made before it, closure-02's on
  `real_decision`, used text that did not change; no read of `maps_to_shape` exists. The brief's sha256 in every
  later request record is the new one.
- **`total-search.txt`** (`CaseAppendix.total_search_path`; `material.rejection_material`): sent as a second block,
  "Search of the company's earlier filings", on a `maps_to_shape` read when the file exists, and on no other read.
  An empty or over-long file is refused, not dropped. It is hand-placed, as the excerpt is, and its hash goes into
  the request record's `material_sha256`, so a changed search is a changed material (the existing one-read-per-
  material rule). **Not enforced in code:** that it was saved before the result was recorded (the same as the
  excerpt; the order of work in §4.6.2 A.4 and Stage D step 11). The too-small note (A.4) is a line he or Opus
  writes at the top of the file; it must carry no figure and no factor.
- **`hc case documents <id>`:** fetches the candidate's §12.6 document set and writes `sources.json`, with no key
  and no extraction. The CIK comes from the search's list and the cut-off from the log (the day before the recorded
  first disclosure), neither typed. Refused, before any fetch, until `first_disclosure`, `public_and_filing`,
  `inside_window` and `real_decision` are met (a disputed rejection counts as met, as in `hc case build`). It prints
  counts only. `sources.json` is the builder's own list: a later `hc case build` rewrites nothing (tested). The
  shared lookup is `_candidate_cik_and_row`; `hc case build`'s checks are unchanged.
- **Not built, by §4.6.2:** the paragraph search itself stays by hand from the cache, by the rule in A.3; nothing
  in code finds the paragraphs. **For the review:** (1) the brief's reply format still says a `maps_to_shape` "fail"
  gives shape "none", and `_shape_problem` enforces it, so a failure on the total alone reads as "none" with its
  reason saying which part; (2) B.3's ring rule for the excerpt cut is not built (nothing cuts an excerpt in code,
  and none will exceed the limit until a very long filing does); (3) nothing in code checks that a pass quotes the
  total's sentence.

**Stage D step 11a, the Opus review (2026-10-17, about 5:25 AM CDT).** Read against §4.6.2 as adopted, not
against the 11a notes. **No code changed:** the build matches the patch. 2508 tests, `make check` green, `hc
protocol check: ok`.
- **Checked:** the brief's new `maps_to_shape` paragraph equals §4.6.2's text word for word (compared with the
  line breaks removed), and nothing else in the brief changed. `rejection_material` adds the search block only to
  a `maps_to_shape` read, and its hash goes into `material_sha256`. `hc case documents` refuses, before any fetch,
  until the four checks before criterion 4 are met (a disputed rejection counts, as in the build); it takes the CIK
  from the search's list and the cut-off from the log, writes `sources.json` with `write_sources` (an identical
  list is a no-op, a different one is refused), and makes no model call. `hc case build`'s gate is unchanged. `hc
  case lock` checks the scenario and rubric reads only, so the brief's new sha256 does not touch closure-02's
  `real_decision` read.
- **The three open points, answered.** (1) A `maps_to_shape` "fail" giving shape "none" is kept: §4.6.2 replaced
  the criterion's paragraph only, the reply format was not part of what the reader read, and a fail agrees with
  the rejection, so its shape is never used; the reason says which part failed. A reply that names a shape on a
  fail is unusable and costs an attempt, as before. (2) The ring rule is applied by hand when an excerpt is cut, as
  the excerpt is placed by hand; code refuses any part over 200,000 characters, which is the backstop. The same
  limit applies to `total-search.txt`, for which §4.6.2 gives no cut rule; none is expected to come near it. (3) A
  pass's quoted sentence is checked by him when he logs the resolution (A.5), not by code.
- **Found, not fixed (a rule, his): the headcount floor cannot be checked when criterion 4 is recorded.** §4.6.1
  item 5 and §4.6.2 A.1 fail a heads total under 100 *after scaling*, but the factor is drawn by `hc case build`,
  which refuses until criterion 4 is met. With the factor in [0.6, 0.9] or [1.1, 1.6], a stated total of 167 or
  more always scales to 100 or more and one of 62 or fewer never does; between, criterion 4 cannot be decided in
  the order the log requires. It touches S1 and S3 only (S2 and S4 totals are dollars). The independent read did
  not raise it. Logged as an OPEN in `KNOWN-GAPS.md`, to settle before the total search of any S1 or S3
  candidate. The 11a note that the too-small line "must carry no figure and no factor" waits on that decision.

**Stage D, §4.6.3 adopted (2026-10-17, about 12:15 PM CDT; Opus drafted, his decision).** The headcount floor OPEN
from the 11a review is settled by option (a): a heads total passes criterion 4 part (ii) at 167 or more as stated.
The independent read (Gemini 3.1 Pro, $0.170, `evidence/phase-5/patch-4.6.3-review-raw.md`) asked for four changes;
2 to 4 are taken and 1 is answered as a stated interpretation (§4.6.3). **A change to the instrument:** the reader's
brief (`experiment/readers/rejection.txt`, `maps_to_shape`) gains the floor and the rule for approximate figures,
ranges and upper bounds, loses the "judge only whether that figure is the total" sentence, and lets a derived total
be quoted from several sentences. No read has used the changed text. The 11a too-small note is dropped:
`total-search.txt` carries no note of why a case was rejected, as the read is blind (§4.9). Its test changed with it;
no other code changed. The commit's whitespace hook stripped trailing spaces from five lines of the raw file's prose
copy of the reply; no word changed, and the full response as returned (its JSON block) is byte-exact.

**Stage D step 11, a fault in the cut-off check (2026-10-17, about 12:55 PM CDT; Opus fixed, his decision).**
`hc case documents` refused closure-09 because one filing a decade before the cut-off had an acceptance date (US
Eastern) a day after its filing date; the SEC's data shows it, and the SEC grants filing-date adjustments, so it is
real. `cutoff.check_consistent` refused any such disagreement, in any filing of the company's history, even one
that could not change admission (a test asserted it). **Fixed, his decision:** a disagreement is refused only when
the filing and acceptance dates fall on opposite sides of the cut-off; otherwise the filing date decides, as for
any filing. `cutoff.py` and three tests changed (one replaced, two added). No earlier case is affected: every
earlier fetch passed the old check, so none held a disagreeing filing. The S2 and S3 pattern so far (closure-01 to
09, every one rejected on the total) is the cost §4.6.2 named; no rule changed for it.

**Stage D step 11, closure-10 to 15 and §4.6.4 adopted (2026-10-17, about 5:20 PM CDT; Opus drafted and built,
his decisions).** closure-10 to 13 and 15 fail criterion 4 on the S2 total, every one read and agreed. closure-14:
its shares trade only over the counter after a delisting, and criterion 1's "publicly traded" is read to include
that (his decision, so the rejection that follows is read); it fails criterion 3 on an insolvency proceeding stated
in another item of the same report than the one the excerpt rule sends, so the reader, given that item alone,
disputed, the rejection does not stand (as closure-02's did, on the same cause), and it fails criterion 4 (S2, no
figure). **The excerpt unit (§4.6.2 B.3) can keep a criterion 3 reason out of the reader's sight** when the reason
is in another item of the report; it has changed no outcome so far, and is noted for the methods page. closure-16
raised the type rule: **§4.6.4, adopted after the reader's read** (Gemini 3.1 Pro, $0.188,
`evidence/phase-5/patch-4.6.4-review-raw.md`); the draft's move between lists was dropped at the reader's change 1.
**A change to the instrument:** the brief's `maps_to_shape` paragraph and reply format gain the decision's type; no
read has used them. Code: `RejectionReply.type` checked against the shape (`read.py`), `read_agrees` and the saved
read's `type` (`search.py`), the reader's printout (`cli.py`); tests added for each. A hand check of the S2 search
(alternate wordings of operating income, by grep) was found to have covered one document of nine for closure-13,
from an output file truncated by each call; redone over every document for closure-13 and 15, it found nothing that
counts, and the A.3 search itself (its own parser) was not affected. Two trailing spaces in the prose copy of the
§4.6.4 reply were stripped before the commit, for the whitespace hook; the JSON block is byte-exact.

**Stage D step 11, the closure window finished, and the fail-shape rule changed (2026-10-18, about 12:35 PM CDT;
Opus, his decisions).** closure-14 and 16's `maps_to_shape` reads logged, both agreeing (closure-14 on its third
attempt: the first named a type on a fail, the second was a call refused for a mistyped key). closure-17 and 19 to
28 taken through criteria 2 to 4: every one fails criterion 4, every read agrees. S2 on the total (17, 20, 21, 22,
23, 25, 26, 28); S3 under the floor or with no figure (19, about 120; 24, about 85 across two sites; 27, no
headcount at the facility named). closure-28's shares trade over the counter (EDGAR's submissions record), read as
publicly traded as closure-14 was; its criterion 3 pass is a judgment (the lessors' taking back of the aircraft was
forced, the reduction in force that followed was chosen, and the excerpt shows the alternative of retraining).
**The closure window yields no case (0 of k = 2); the fallback pool opens next (§12.2).**

**Three slips, on record because the log is write-once.** (1) The excerpts of closure-17 and 19 to 28 were saved
after their criterion 3 and 4 results were recorded, not before, as Stage D step 11 requires. Each is the whole
Item 2.05, cut by rule at the next item heading (at a period-led heading run into a paragraph, for 17 and 25) or
at an unnumbered heading (forward-looking statements, signature); none was chosen, so the order could not shape
it, but the order was broken. (2) closure-27's recorded reason calls it S2: the tool used to read the filings
matched "Item" case-sensitively and missed the filer's "ITEM 2.05", so the release alone was read. Item 2.05 names
a facility to be exited at its lease's end, so it is S3 (closure); the A.3 search was redone for the facility's
name, which no earlier filing holds, so it fails on the total either way, and the reader read it on the right
excerpt and search. (3) closure-17's recorded reason counts nine 8-Ks and seven EX-99; there are ten and six (18
documents, as stated).

**A change to the instrument, his decision after closure-22's second unusable reply.** The reply format said a
`maps_to_shape` fail gives shape "none", kept at the step 11a review at the cost of an attempt per slip. Four of
the day's sixteen `maps_to_shape` replies named the matching shape on a fail on the total alone (closure-14's
first, closure-22's first two, closure-23's first), each with the right reading, and closure-22 was one unusable
reply from the three-attempt limit, after which nothing logs its read. **Now a fail gives the shape that matches,
or "none"**, its type fitting the shape (§4.6.4): the brief's reply-format sentence and `_shape_problem`
(`read.py`), with tests. No outcome can change: a fail agrees with the rejection whatever its shape. Replies
already on record keep the verdict they were given; closure-22's third attempt is read under the change. Also
fixed: `hc case log ... read` printed "(disputes)" over a §4.6.4 read that agrees (the record was right; only the
label used the old rule), with a test.

**Stage D step 11, the closure fallback pool, and the closure selection complete (2026-10-18, about 12:55 PM CDT;
Opus, his reads).** The seven fallback candidates (closure-f01 to f07) were checked, **each excerpt saved before
any result was recorded**. f04 fails criterion 1: an S3 closure of one named plant (about 1,750 job reductions,
which would have passed the total), but the company publicly said on 2026-05-12, before the fallback month, that
it was in discussions to close the facility; the earlier plan at the same plant (about 300 job reductions, Q4
2025) was judged a different decision. f01 passes criterion 1 (its "previously discussed" call names three other
footprint projects and no plant in Mexico; the transcript was read) and fails criterion 4 as S3 with no headcount
at the site. f02, f03, f05, f06 and f07 fail criterion 4 on the S2 total. f02 is quoted over the counter now, but
its 8-K cover of the decision date lists it on an exchange, and criterion 2 is read as of the decision. Every read
agrees, each on its first attempt (no format failure under the changed rule). **The log reports "selection
complete; shortfall 2": the closure type has no case** (§12.1: a shortfall is reported, never filled).

**What decided it.** Of 36 closure candidates, every S2 that reached criterion 4 failed on the total: no filing
stated the fall in operating income the company expected before acting, as a dollar figure (§4.6.2 A); the S3
candidates failed on a headcount at the site under 167 or absent. The one candidate with a usable total (f04)
was disclosed before the fallback month. This is a property of the rule against real filings, reported as such;
nothing here changes it.

**The excerpt cut, made mechanical.** The rule (the whole Item 2.05, ended at the next item heading or an
unnumbered heading) is applied by a scratch script (`scratch/c4/excerpt.py`, not tracked) that also breaks before
a heading run into the paragraph before it, strips table-cell marks and treats a thin space as a space. Re-run
over the eleven window excerpts saved earlier the same day, it reproduces each in content (two differ only in a
thin space and a page-number cell's marks); the saved files were not changed.

**Stage D step 11, the retool window finished (2026-10-18, about 2:40 PM CDT; Opus, his reads and decisions).**
All 44 window candidates (retool-01 to 44) were dated first. **32 fail the first-disclosure check:** the matched
passage's subject was public before the window, almost always as the same forward-looking list, capital-spending
sentence or project announcement in an earlier filing, found by EDGAR full-text search on the passage's own words
and read in context (§4.6.2 B.1). His three calls (2026-10-18, on Claude's recommendation): fail those 32 unread at
the first-disclosure check, as B.1 provides; date retool-09 at its own presentation and retool-21 at the
customer's board approval it refers to, each with the alternative reading in its reason; and record retool-40, a
later filing of retool-34's decision, as dated with retool-34 (KNOWN-GAPS OPEN 2026-10-18). **The 12 that pass**
were taken through criteria 1 to 4: four are real decisions to expand existing plants (19, 34, 40, 42) and fail
criterion 4 part (i), no shape (no facility of the company's named for closure or sale, no annual program cost
stated); eight were rejected on criterion 3 as passages announcing no decision (09, 10, 15, 17, 20, 21, 33, 36).
**The reader disputed all eight** on the whole excerpt, which in each shows some real decision (a merger, an
acquisition, an offering, a machine purchase, a ten-year investment total, a listing restructuring, technology
choices); his resolution for each: the rejection judged only the matched passage's subject, so per §12.4 it does
not stand and the candidate went on to criterion 4. All eight then failed criterion 4 part (i), no shape, and
every one of those reads agrees, each on its first attempt (retool-20's reason records the reading of a total over
ten years as an annual cost, rejected because S4 requires a stated one). Reader spend for the window's 21 reads,
about $0.53. **The retool window yields no case (0 of k = 2); the fallback pool (retool-f01 to f18) opens next
(§12.2).**

**Two slips, on record because the log is write-once.** (1) The first-disclosure results of the 12 passing
candidates were recorded before their excerpts were saved, not after, as Stage D step 11 requires. Each excerpt was
then cut by rule before any criterion 1 to 4 result (below); none was chosen, so the order could not shape it, but
it was broken. (2) The eight criterion 3 rejections rested on a reading of B (criterion 3 judged on the matched
passage's subject) that the brief does not hold: the brief judges the whole excerpt. Every one was disputed and
none stood, so no outcome rests on the slip; on the fallback pool, criterion 3 is judged on the whole excerpt, as
the brief does.

**The excerpt for a hit outside Item 2.05, made mechanical** (`scratch/c4/excerpt_doc.py`, not tracked): B.3's
unit, the whole exhibit or the whole item of the current report that holds the matched phrase, parsed as the Item
2.05 script parses; where more than one document of the filing holds it (retool-34), **the first in the filing's
own order**; over 200,000 characters (retool-10, a merger agreement), B.3's rings around every paragraph holding
the phrase, each ring whole, `[...]` marking each gap.

**Stage D step 11, the retool fallback pool, and the retool selection complete (2026-10-18, about 3:25 PM CDT;
Opus, his reads).** The 18 fallback candidates (retool-f01 to f18) were checked, **each excerpt saved before any
result was recorded**, and criterion 3 judged on the whole excerpt, as the brief does. **15 fail the first-disclosure
check**, the passage's subject public before July 2026 (forward-looking lists and slides repeated from earlier
filings; capacity work announced earlier in the year; a new plant in filings since 2025). retool-f07 and f08 are one
deck filed by both parties to a combination (the gap of KNOWN-GAPS OPEN 2026-10-18); both fail on the expansion
work announced in February, so the gap did not arise. **Three pass** (f10, an acquisition; f13, a capital raise
reported with quarterly results; f14, the company's agreement to be sold, after a strategic review announced in
April, judged an earlier, different step as at closure-13), and all three fail criterion 4 part (i), no shape.
Every read agrees, each on its first attempt (three reads, about $0.05). **The log reports "selection complete;
shortfall 2": the retool type has no case** (§12.1).

**What decided it.** Of 62 retool candidates, 47 failed the first-disclosure check: the channel's phrases ("capacity
expansion", "expand production") match boilerplate and running commentary far more often than an announcement, and
that text is repeated from filing to filing. Of the 15 that reached criterion 4, none named a facility of the
company's for closure or sale with production moving to new or converted capacity (S3 on retool), and none stated a
program's annual cost (S4); the real decisions found were expansions of existing plants, acquisitions, sales and
financings. This is a property of the rule and the channel against real filings, reported as such; nothing here
changes either. Two of the three types now have no case (closure, retool); with ai at k = 1, v1 has at most one
case, below §12.1's "at least three, at least one invest or retool". The definition of done here (§9, DoD 1: "or a
shortfall by type") and the Phase 5.5 scope doc ("unless Phase 5 reported" one) already provide for that outcome;
what it means for Phase 5.5 and the write-up is his (KNOWN-GAPS OPEN 2026-10-18).

**Stage D step 11, the ai type, and the ai selection complete (2026-10-19, about 3:45 AM CDT; Sonnet, his reads).**
All 76 candidates (50 window, 26 fallback) were checked under the rules as they stood, **every excerpt saved before
any result was recorded** (the retool slip not repeated), criterion 3 judged on the whole excerpt, full-text search
only for the contract-wording matches and a web search for every filing that announces an action. **The log
reports "selection complete; shortfall 1": the ai type has no case** (§12.1), so **no type has a case under the
pre-registered rule**. This is the record the exploratory relaxation (KNOWN-GAPS START HERE, 2026-10-19) rests on.

**The window (50).** 21 fail the first-disclosure check (forward-looking lists, non-GAAP definitions and covenants
repeated from earlier filings; one AI-framed workforce cut disclosed in July, before the window).
The 29 that pass are 20 transaction agreements whose workforce wording is a covenant, representation or definition,
and nine filings that announce a cost or workforce action. Every one fails criterion 4 part (i): no filing
attributes a workforce change to AI or automation software with a usable total. One (ai-39, a product-data
release naming a cut announced the day before only in its forward-looking statements) was rejected at criterion 3;
**the reader disputed it and his decision (2026-10-19) was that the rejection does not stand**, as at retool-09 and
retool-21, so it went on to criterion 4, where the reader agreed it fails. All other reads agree. The closest
candidates: ai-07 and ai-20 (one decision filed twice), a cut whose sibling exhibit credits AI-assisted tooling but
whose Item 2.05 excerpt does not, and which is under the 167 floor; and ai-41, a cut at a company whose product is
AI, not attributed to it.

**The fallback pool (26).** 12 fail the first-disclosure check; three (f06 to f08, student-loan trust notices)
fail criterion 2, no publicly traded stock; the 11 that pass criteria 1 to 3 (ten transaction agreements or deal
slides and one 2% reduction in force inside a cost program) fail criterion 4 part (i), every read agreeing. One
automation-linked cut (f17) fails first disclosure: announced in January 2026.

**Slips.** (1) The first run of the recording script was refused at the first fallback (the log requires every
window read before a fallback), so the window rows were written and the fallbacks later; nothing was lost. (2)
Two fallback reads failed with AccessDeniedException (0 tokens, no cost) and were retried, both succeeded. (3) The
fallback reads were estimated at about $0.30 and cost about $0.9: the agreement excerpts, cut to 200,000
characters, cost about $0.09 each, not the $0.02 of the short ones. The reader's spend, every case in the
appendix, is about $3.83 (about $2.7 of it the ai type).

**Boundary of the web check.** The web search was run for the 14 filings that announce an action; for the contract
wording the full-text search alone was used, so the first-disclosure date of those is the filing or the signing
date, not a searched date. It cannot change an outcome (each is inside the window or fails criterion 4 anyway).

**§4.6.5, drafted, read and adopted (2026-10-19, Opus at max effort; his decisions).** Drafted from about 11:40 AM
CDT, after the measurements §4.6.5 E lists (XBRL figures for the 25 closure-list S2 candidates; the Item 2.05 text of
the window's 24 non-manufacturing filings; counts and a mechanical scan of the pre-cut-off pool, 142 filings, and of
the new channel, 8 filings, no filing read; gpt-oss-120b's training cut-off from OpenRouter's listing, live). His
decision in principle about 12:05 PM asked for every further relaxation that holds up, so step 1's S3 rules, step 2's
re-read and channel, and step 5 were added before the read; the reader read that version (Gemini 3.1 Pro, $0.241,
`evidence/phase-5/patch-4.6.5-review-raw.md`) and asked for ten changes, answered as §4.6.5's read paragraph says. He
adopted it about 12:50 PM, on the condition that the changes help reach a legitimate five cases or close to it. Its
build is planned in `phase-5-case-building-exploratory-IMPLEMENTATION.md`, written the same day.

**Three slips, on record.** (1) An early draft was stamped "about 1:00 PM" though written before noon; fixed before
any commit. (2) **The reader's spend passed his $5 OpenRouter cap without being flagged:** the candidate reads total
**$3.92**, measured from the 139 reply files in the appendix (104 billed), against the projection's $1 (worst $2), most
of it the ai type's agreement excerpts at about $0.09 each; with the patch reads, about $4.65 since 2026-10-15. The
2026-10-19 entry above estimated $3.83. He has removed the cap and watches the balance; the exploratory plan's §4 now
has the spend totaled after every batch of paid calls and said against his balance. (3) Four trailing spaces were
stripped from the prose copy of the read's reply, for the whitespace hook; the JSON block is byte-exact.

**The brief changed again, a change to the instrument (2026-10-20, Sonnet built the exploratory part's step 5; for
Opus's review).** `experiment/readers/rejection.txt`, the `maps_to_shape` paragraph, the four changes §4.6.5 step 1
item 7 lists, nothing else. **Reason:** the S3 rules of the exploratory record (a product-making facility, the
plant's headcount as a source states it, a floor of 50, a public report as material). **No pending read uses the old
text** (no `maps_to_shape` read is pending). The brief's sha256 in every later request record is the new one.
`total-report.txt` (`CaseAppendix.total_report_path`; `material.rejection_material`) is sent as a third block on a
`maps_to_shape` read when the file exists, and on no other read. Opus's review renamed that block "Public report" (it had
said "of the facility's headcount", which is the reader's to judge), and let a carried row's rejection be read again
past the pre-registered read in its folder (the exploratory plan's §9, step 5).

**A rule for the press channel's rows, one decision judged once (2026-10-20, his, on Opus's review of the
exploratory part's step 6).** The channel leaves out a filing already a candidate by its accession number, and the
log's "one decision is one case" check compares accession numbers too. A decision announced in two filings (a press
release under Item 7.01 or 8.01, then an Item 2.05 8-K, filed apart) would come in twice. A later press filing fails
criterion 1 on the earlier one already; an earlier one would not. **Rule:** a press row that is the same decision as a
candidate already listed fails criterion 1, with the reason "already a candidate: <id>"; the decision is judged once,
on the earlier row. A different decision of the same company is checked as any row. To make the reading possible,
`press-candidates.json` records, privately, each press row's earlier candidates from the same filer
(`same_filer_as`, by CIK), and the command prints only how many there are. **His condition:** nothing here may cost
a case the record could otherwise have. It does not: the decision is judged either way, on the same facts, and what
the rule removes is the second count of it, which would not be a second case.
