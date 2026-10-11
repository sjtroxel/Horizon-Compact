# Phase 5 — Case Building, code half: IMPLEMENTATION (v0.5)

> **IMPLEMENTATION doc, code half. Written 2026-10-11 (Opus). APPROVED 2026-10-11 (his), all four decisions in §6 as
> recommended, (a). Not yet built.** Written after
> Phase 5 was split by code and search (his, 2026-10-10; the scope doc's dated note; ROADMAP decision history).
> Sources: the Phase 5 scope doc (`docs/phases/phase-5-case-building.md`, its six decisions as recorded), the protocol
> draft (`experiment/protocol/protocol-v1.md` §12, all of it), `planning/01` §4.6, §4.8 and §5, `planning/02` §2.7 as
> patched, `planning/04` §2.1, and the code as built (`protocol/cases.py`, `protocol/sets.py`, `dossier/render.py`,
> `experiment/company/dossier.toml`). SEC access rules checked live 2026-10-11 (§4.2).
>
> **Everything here is built and tested on synthetic filings, with no model call, no AWS call and no request to the
> SEC.** One step at the end is a single read-only request he runs, to confirm field names (§7 step 1).
>
> **Rule zero.** This doc names no company, no candidate and no identifier, and neither does anything this half
> commits. Every filing in a test is a fictional canary's.
>
> **Vocabulary.** A **10-K** is a company's annual report to the SEC; a **10-Q** its quarterly report; an **8-K** a
> "current report" filed within four business days of a significant event, sorted into numbered **items** (Item 2.05
> is "costs associated with exit or disposal activities", the usual closure filing). **EDGAR** is the SEC's filing
> system. **XBRL** is the machine-readable tagging of a filing's financial figures; the SEC publishes every tagged
> figure a company has filed, each with the date it was filed. An **accession number** is a filing's permanent ID.

## 1. Where things stand on 2026-10-11

- **The protocol already fixes what a dossier holds** (§12.6): seven sections in a fixed order, which sections each
  scenario shape needs, the option-economics rule, anonymization, and the scaling draw. It does not fix how a builder
  gets from filings to those sections. That is this half.
- **The case record and its gate exist** (`protocol/cases.py`, Phase 3.5 step 6): `experiment/cases/<label>/case.lock`
  holds the sha256 of a case's dossier, scenario text and rubric, and the content arrives at run time. The builder's
  output must hash the way `check_case_content` reads it.
- **The fictional dossier's format is the target** (`planning/05` §5.1 item 4: hand-built dossiers in the same frozen
  format): a TOML file with `title` and `text`, as `experiment/company/dossier.toml`.
- **The builder is run code, not frozen** (`protocol/sets.py`: only the prompt, validation, classification and
  `analysis/` are). So this half has no tag deadline. **But four of its rules belong in the protocol** (§3, findings
  1-4), and the protocol is frozen at the tag, so those four protocol edits do have the tag as their deadline.
- **Nothing has fetched a filing.** `planning/01` §5's endpoints were checked on 2026-10-02 with one live query.

## 2. What this half delivers

1. **The EDGAR client** (§4.2): User-Agent from local config, throttled under the SEC's limit, every response cached
   write-once in the private appendix, a fake transport for tests.
2. **The cut-off filter** (§4.3): the one function every document and every figure passes through; nothing reaches
   extraction without it.
3. **The document set** (§4.4): for a filer and a cut-off, the most recent 10-K, the most recent 10-Q, and the 8-Ks
   the rule admits, with the source list (accession numbers, dates, hashes).
4. **The section map and splitter** (§4.5): which filing items feed which dossier section; splitting a filing into
   items, with a refusal when it cannot.
5. **Figures from XBRL** (§4.6): sections 4 and 5 built from tagged figures filtered by their filing date, no model in
   the number path.
6. **The extraction step's request** (§4.7): the prompt and its shape, run against a fake provider. The model is
   chosen in the search half.
7. **Anonymize and scale** (§4.8): name replacement from the case's private term list, states to regions, dates to
   relative, the scaling draw exactly as §12.6, the rounding and the pay-per-head check.
8. **Options and the equal-treatment rule** (§4.9).
9. **Assemble, check, record** (§4.10): the dossier in the frozen format, the foreshadowing check as a tool, and the
   hashes for `case.lock`.
10. **If decision 1 is (a): the search runner and the selection log** (§4.11), on fakes.

**Not in this half:** any real fetch beyond step 1's one request; the extraction model's choice; the recognition
probe's runs; the independent reader; the rubric (written by a person, after the dossier, in the search half); every
case. All of it is the search half, written immediately before the search.

## 3. What writing this doc found

1. **"Earlier current reports a chief executive would know" is a judgment** (protocol §12.6, from `planning/01` §4.6),
   made on case day by someone who knows the grid's results and the company's outcome. Which 8-Ks go in is exactly the
   kind of selection hindsight bends. It needs a mechanical rule, in the protocol, before the tag. Decision 2.
2. **"Dated before the cut-off" has two readings.** The cut-off is the day before first disclosure. "Before" it can mean
   filed on or before that day, or strictly before it. Both exclude the disclosing filing; they differ by one day.
   Decision 3.
3. **The pay-per-head "realistic band" has no number.** Scaling dollars and headcounts by one factor keeps pay per head
   exactly; only the rounding moves it (dollars to three significant digits, heads to the nearest 5). A small headcount
   can move a lot: 12 people round to 10, a 17% change, and 2 round to 0. Decision 4.
4. **The section map is unfixed.** The protocol fixes the dossier's sections, not which part of a 10-K feeds each.
   Written on case day, it is a selection made with hindsight. It is generic (no case in it), so it can be fixed now.
   It belongs beside decision 2's rule.
5. **XBRL gives figures dated by filing, which is what the cut-off needs.** Each tagged figure carries the date of the
   filing it came from, so a figure later restated in a post-cut-off filing is seen as it stood before the cut-off.
   Taking sections 4 and 5 from XBRL keeps a model out of the numbers and makes the cut-off exact. **Two limits:**
   the company-facts file holds only whole-company figures, not segments, so section 2's segment figures come from the
   filing's text; and companies tag the same thing under different names (several revenue tags are in use), so the
   builder takes a fixed fallback list per line and reports which tag it used. *(Field names checked at build, §7
   step 1.)*
6. **Splitting a real 10-K into items is the fragile part.** Filings are HTML with a table of contents that repeats
   every heading. Synthetic filings can test the splitter's rules but cannot prove it on real ones. The splitter
   therefore refuses rather than guesses (no item found once, an item found out of order), and on case day a refused
   split is done by hand with the boundaries recorded. Stated as uncertain in §10.
7. **"Never told the outcome" can be made structural, not just a promise.** If the builder's modules cannot import the
   rubric's types, and the extraction request is built only from a section's text and the template's fixed
   instructions, no code path carries the outcome to the model. A test checks the imports.
8. **The scaling draw from a union of two ranges needs one more sentence.** "Log-uniformly from [0.6, 0.9] ∪ [1.1,
   1.6]" is well defined only once the two pieces are weighted by their log-lengths (ln 1.5 ≈ 0.405 and ln(16/11) ≈
   0.375). That is the natural reading; the code does it and the protocol should say it. Folded into decision 4's
   protocol edit.

## 4. The design

### 4.1 Where things live

New package `src/horizon_compact/casebuild/`, run code. **Its output never enters the repository.** The builder finds
the private appendix the way the name guard finds its term file: local git config `hc.appendixDir`, or the environment
variable `HC_APPENDIX_DIR`; no default, and no path written in any tracked file. **Before writing anything it asks git
whether the target would be tracked** (`git check-ignore`) and refuses if so. Inside the appendix, per case:
`<label>/cache/` (raw responses), `<label>/sources.json`, `<label>/build.json` (the factor, its seed, every rounding),
`<label>/dossier.toml`, `<label>/scenario.toml`. Labels are neutral (`closure-1`, `retool-2`); the scheme is fixed in
the search half.

### 4.2 The EDGAR client

Checked live 2026-10-11 on the SEC's "Accessing EDGAR Data" page (last updated 2024-06-26): **at most 10 requests a
second**, and a declared User-Agent in the form "Sample Company Name AdminContact@<domain>.com". The client:

- reads the User-Agent from local config (`hc.secUserAgent` or `HC_SEC_USER_AGENT`), his choice of name and address
  (scope doc, Prerequisites), and refuses to run without it;
- spaces requests at least 0.25 s apart (4 a second, well under 10), and on a 403 or 429 stops rather than retries;
- caches every response under the case's `cache/`, write-once, keyed by URL, with its sha256 and fetch time; a cached
  URL is never fetched again (filings do not change);
- takes a transport object, so tests use a fake that serves synthetic files and fails the test on any unexpected URL.

### 4.3 The cut-off filter

One function, `admit(document_or_fact, cutoff)`, used by everything below; nothing reaches extraction or the figures
without passing it. **The rule is decision 3's.** It reads the filing date, never the period a filing covers, so a
10-K/A filed after the cut-off is out even though it amends an earlier year. The acceptance time is not a second rule (a
filing accepted after the day's close is dated the next business day, so the filing date already excludes it); the
filter only checks the two agree (acceptance date, in US Eastern, on or before the filing date) and refuses a filing
where they do not. *(Amended 2026-10-11, Opus review: the earlier "acceptance after the cut-off is out" clause was
redundant.)* Tests put a document on each side of every
boundary.

### 4.4 The document set

For a filer and a cut-off: **the most recent 10-K and the most recent 10-Q** admitted by §4.3, and **the 8-Ks (and
8-K/As) decision 2's rule admits**. For each 8-K: the main document and its press-release exhibits (EX-99). The source
list records, per document: form, accession number, filing date, acceptance time, URL, sha256. This is the
"builder's source list" of the scope doc's DoD 3.

### 4.5 The section map and the splitter

| Dossier section (protocol §12.6) | From |
|---|---|
| (1) overview | 10-K Item 1 (Business) |
| (2) segments and facilities | 10-K Item 2 (Properties); segment figures from the segment note in Item 8 or Item 7 |
| (3) workforce | 10-K Item 1, the human capital part |
| (4) financial position, three years | XBRL (§4.6) |
| (5) capital allocation history, three years | XBRL (§4.6); acquisitions also from Item 7 |
| (6) the situation at the cut-off | the later of the 10-Q's Part I Item 2 and the 10-K's Item 7 (MD&A); every admitted 8-K |
| (7) the options plausibly open | §4.9 |

The splitter finds item headings, skips the table of contents (the first run of headings with no body between them),
and refuses when an item is missing, found twice in the body, or out of order. **The map goes into the protocol with
decision 2** (finding 4).

### 4.6 Figures from XBRL

From the company-facts file, admitted by §4.3 on each figure's filing date; for each line of sections 4 and 5, a fixed
list of tags tried in order, the first present used and recorded. Three fiscal years ending at the latest admitted
annual figure. **Where two admitted filings give different values for the same period, the later admitted one wins**
(a restatement known before the cut-off). A line with no admitted figure is left out and listed in `build.json`, never
filled from text by a model.

### 4.7 The extraction request

Per section, one request: the template's fixed instruction for that section, and the admitted text the map assigns it,
nothing else. The output is plain text in the template's section. **The request type has no field for anything outside
those two inputs, and `casebuild/` cannot import the rubric or any case-outcome type** (a test reads the imports).
In this half it runs only against a fake provider. The model, its route and the cost are the search half's.

### 4.8 Anonymize and scale

- **Names:** every term on the case's private term list (company, former names, brands, products, executives, towns),
  matched as the guard matches, replaced by a neutral role ("the Company", "a product line", "the chief executive").
  States and provinces become census regions by a fixed table. Anything the list misses is the human review's and the
  recognition probe's to catch; the builder says so in its output.
- **Dates** in text become relative to the cut-off's fiscal year ("fiscal year N-1, third quarter") by a fixed set of
  patterns; a date in a form the patterns do not know is flagged for the human, never left silently.
- **Scaling,** exactly as protocol §12.6: one factor per case, **drawn log-uniformly from [0.6, 0.9] ∪ [1.1, 1.6], each
  piece weighted by its log-length** (finding 8), from a seed made by `secrets` (never chosen) and recorded in
  `build.json`. Every dollar figure and headcount is scaled; dollars rounded to three significant digits, headcounts to
  the nearest 5. Percentages and ratios are not scaled, **including a dollar figure stated per employee or per
  hour**. **Per-share figures and share counts are left out** of the dossier: they would need their own rule, they
  identify a company, and no section needs them.
- **The pay-per-head check** is decision 4's rule, run on every line that has both pay and heads.

### 4.9 Options and the equal-treatment rule

Section 7 lists the options of the case's scenario shape (protocol §12.5: S1, S2, S3 or S4), in the shape's fixed
order. Each option takes figures only from admitted documents. **If any option has no admitted figure, the builder
strips figures from every option** (protocol §12.6), and records that it did. What each option is called comes from
the shape, never from the filings.

### 4.10 Assemble, check, record

- **Assemble** the sections the shape needs (protocol §12.6: S1 sections 1, 3, 4, 6, 7; S2 1, 3, 4, 5, 6, 7; S3 all;
  S4 1, 4, 5, 6, 7) into `dossier.toml` in the fixed format.
- **The foreshadowing check** (`hc case foreshadow`): given a term list and the dossier and scenario text, every hit
  with its line, written to the appendix for a justification or a removal. The terms come from the rubric, which the
  builder never reads; the check is a separate command run after the build.
- **Record:** `hc case hashes` prints the three sha256 values in the form `case.lock` needs, computed by the same
  function `check_case_content` uses (shared, not copied; a test checks they agree).

### 4.11 The search runner and the selection log (decision 1 (a) only)

The queries of protocol §12.3 as data, run as written: each query separately, every page read, hits unioned by
accession number, the filters on `items`, `sics` and `file_date` applied in code, the fallback month's hits held apart.
The output is the candidate list in disclosure order, for the person who applies the criteria. **The selection log**
is a fixed format (one row per candidate, each criterion's result and reason), with a public view by case type that
the code writes without names. Tested on fake search responses only. The first real run is the search, on the rule
date.

## 5. Rules this half must not break

- **No model call, no AWS call, no SEC request in any test.** Every transport and provider is a fake that fails on an
  unexpected call.
- **Rule zero.** Fixtures are fictional canaries. No path into the private appendix is written into a tracked file.
  The builder refuses to write where git would track.
- **Hindsight never reaches a dossier.** Every document and figure passes §4.3; the extraction request carries only a
  section's text and the template's instruction; the builder cannot import the rubric.
- **The frozen files are not touched.** Nothing here changes `sweep/prompt.py`, `sweep/decision.py`,
  `sweep/classify.py`, `analysis/` or `experiment.py`.
- **`make check` before every commit; CI green.** He runs `git commit` and `git push`.

## 6. Decisions for him

Each has my recommendation and the reason. **All four DECIDED 2026-10-11 (his): (a), as recommended.**

1. **What this half builds.**
   - (a) **Recommended: the builder and the search runner with the selection log**, on fakes. The search runs on the
     day after Phase 4's results are committed; the point of the split was that run day means typing commands, not
     writing code (the Phase 4 code half's reasoning). The queries are already frozen in protocol §12.3, so the code
     is mechanical. This widens the 2026-10-10 scope note, which named the builder only; that note gets a dated line.
   - (b) The builder only, as the 2026-10-10 note says. Smaller; the search code is written on search day.
2. **Which 8-Ks go in, and the section map** (findings 1 and 4). A protocol edit before the tag.
   - (a) **Recommended: every 8-K filed after the most recent admitted 10-K and before the cut-off**, its main document
     and press-release exhibits, plus §4.5's map. Mechanical, about one year of reports, the same span as the 10-K's
     own view. A busy filer gives a long section 6; that is the extraction step's job.
   - (b) Every 8-K in the twelve months before the cut-off. Also mechanical; can reach back before the annual report
     and repeat what it already says.
   - (c) Leave it to judgment on case day, as written. Not recommended: a selection made with hindsight.
3. **The cut-off comparison** (finding 2).
   - (a) **Recommended: strictly before the cut-off date**, as the protocol is written: a document filed on the
     cut-off day itself is out. It costs at most one day of filings and needs no protocol change.
   - (b) On or before the cut-off date. One day more; a protocol edit to say so.
4. **The pay-per-head band, and the draw's weighting** (findings 3 and 8). A protocol edit before the tag.
   - (a) **Recommended: after rounding, pay per head within 3% of its unscaled value; a scaled headcount under 100
     is not rounded to 5 but stated as "fewer than 100"**, and the draw's two pieces weighted by log-length. The
     numbers fit together: rounding to 5 moves a headcount of 100 or more by at most 2.5%, and three significant
     digits move a dollar figure by at most 0.5%, so the check fails only on something unexpected. The small-group
     case is generalized the way §12.6 already generalizes distinctive facts.
     *Corrected 2026-10-11 (his, on Opus's review): 3.5%, not 3%; "fit together" was wrong by 0.08 points. See §7
     step 2.*
   - (b) A 5% band and rounding kept as written. Simpler, but a small group can still round to 0 and fail.

**Not a decision now:** the extraction model, its route and its cost; the independent reader's model. Both are chosen
in the search half, from what is available on credits that day.

## 7. Order of work

**Sonnet builds; Opus reviews each commit's diff before he commits.**

1. **[done 2026-10-11; results in §11]** **He runs one read-only request** (a script in `scratch/`, his User-Agent, a
   filer not on the longlist, named only in the session) for one submissions file and one company-facts file. Claude
   reads the field names and records them here; the synthetic fixtures are written to match. No spend.
2. **[done 2026-10-11]** **The protocol edits** for decisions 2 and 4 (and 3 if (b)), with the Phase 3.5 doc's note;
   before the tag. Landed in `protocol-v1.md` §12.6 (the 8-K rule, strict cut-off, the section map, the scaling
   weights, "fewer than 100", the 3% band) and §22 of the Phase 3.5 doc. **Corrected the same day (Opus review,
   his):** the band is **3.5%, not 3%**: rounding a headcount down 2.5% raises pay per head 2.6%, so the two
   roundings together reach 3.08%, and a 3% check could fail a correct build. At 3.5% a failure means an error,
   never a redraw. Also added: a per-employee or per-hour dollar figure is a ratio and is not scaled; 8-K/As count with 8-Ks; section 6
   reads the later of the quarterly and annual reports; the acceptance-time clause dropped as redundant. §12.6 is
   still among the sections awaiting his review of the draft.
3. **[done 2026-10-11; Sonnet built, Opus reviewed, fixes applied]** §4.1-4.3: the package, the appendix config and
   its refusal, the client on a fake transport, the cut-off filter. `casebuild/{config,appendix,edgar,cutoff}.py`;
   67 new tests, 1607 in all, `make check` green. As built: the git check runs on every write, not once per case;
   the cache is a `.body` file plus a `.json` record per URL, the record written second; a 403 or 429 halts every
   later uncached request; `edgar.UrllibTransport` is tested only against a loopback stand-in; the architecture test
   that `casebuild/` cannot import the rubric is step 5's, when there is an extraction request to guard. **Review
   fixes:** a submissions row with no acceptance time is refused, not admitted unchecked; the real transport never
   follows a redirect (a 3xx is an error), so the SEC-host check cannot be stepped around; the git calls drop every
   inherited `GIT_*` variable and force English messages. **Kept as written (his):** an appendix inside any git
   repository, a private one included, is refused.
4. **[done 2026-10-11; Sonnet built, Opus reviewed, fixes applied]** §4.4-4.6: the document set and source list,
   the map and splitter, figures from XBRL. `casebuild/{documents,figures,splitter,sections}.py`; 89 new tests,
   1696 in all, `make check` green; one commit (B4). **Choices, reviewed and kept:** (a) only plain `10-K` and
   `10-Q` are picked as the periodic reports, an amendment never is, and an 8-K/A counts as an 8-K; (b) "after
   the annual report" compares filing dates strictly, so an 8-K filed the same day as the 10-K is out; (c) older
   submissions pages are followed only until both an admitted 10-K and 10-Q are in hand; (d) a figure line uses
   the first listed tag that has an admitted value for the latest fiscal year, and years that tag lacks are
   listed, never filled from another tag; (e) an annual period is 355 to 375 days and fiscal years chain 350 to
   380 days apart; (f) two same-day filings that disagree leave the year out, listed; (g) section 5 also carries
   the annual report's Item 7 for acquisitions. **Review fixes:** only rows of the four forms used (10-K, 10-Q,
   8-K, 8-K/A) are parsed, so a malformed row of another form cannot stop a build, while a malformed row of one
   of the four still refuses the table; the segment note needs a heading shaped like one, so a table row such as
   "Total segment revenue" is no longer taken for it (it was, tested); `build_section_inputs` takes the case's
   scenario shape and builds and requires only that shape's sections (protocol §12.6), so an S4 case is never
   refused over Item 2 or the workforce part; Item 1's human-capital part can be cut by hand alone
   (`HUMAN_CAPITAL` in the hand boundaries) while the items still split automatically; a hand boundary key must
   be an item; exhibits sort by number (`ex99-2` before `ex99-10`). **Not verified on any real filing:** the
   splitter and the human-capital and segment-note finders (§10); the shape of an older submissions page
   (`filings.files[].name`, the table at the page's top level) and of a filing's `index.json`
   (`directory.item[].name`), which step 1 did not fetch, and the exhibit-name pattern built on it; every figure
   tag not listed in §11. The first real case is the check; the cheap one to run sooner is one `index.json` and
   one older page for a filer, by script, his User-Agent.
5. §4.7-4.9: the extraction request on a fake provider, anonymize and scale, options.
6. §4.10: assemble, `hc case foreshadow`, `hc case hashes`.
7. §4.11 if decision 1 is (a).

About two days of build with tests; the splitter and the date patterns are most of it.

## 8. Commits

He runs each one; short one-line messages, no attribution.

- **B1** `phase 5: code-half implementation doc` — this doc, approved, with the ROADMAP row and START HERE.
- **B2** `phase 5: protocol edits for the builder` — step 2.
- **B3** `phase 5: edgar client and cut-off` — step 3.
- **B4** `phase 5: documents, sections, figures` — step 4.
- **B5** `phase 5: extract, anonymize, scale` — step 5.
- **B6** `phase 5: assemble and case commands` — step 6.
- **B7** `phase 5: search runner and selection log` — step 7, if built.

## 9. Cost

**Nothing.** No model call, no AWS, no SEC request but step 1's one. The extraction, the probes and the reader cost is
the search half's, estimated there from Phase 4's measured cost per call.

## 10. Genuinely uncertain

- **Whether the splitter works on real 10-Ks.** Synthetic filings test its rules, not real filers' HTML. The refusal
  and the hand split are the fallback; the first real case will show how often it is needed.
- **Whether the fixed tag lists cover the filers that turn up.** A missing line is listed, never filled by a model;
  the search half may add a tag, logged.
- **Whether name replacement plus human review is enough before the probe.** The recognition probe is the measured
  check; this half only makes the first pass mechanical.
- **The field names** until step 1. *(Settled by step 1, §11.)*
- **Unit volumes** (tons, units shipped) are neither dollars nor heads, so they are not scaled, and a per-unit price
  beside them would then be inconsistent with scaled revenue. Not decided: the build reports any case where both
  appear, and the search half decides (generalize the volume, or leave it out).

## 11. As built: step 1, the field names (2026-10-11)

His request, two files for one public filer chosen by him, not on the guard's term file, named nowhere in the repo:
`submissions` (158 KB) and `companyfacts` (3.8 MB), one second apart, the User-Agent from his environment. Read here
from the files, not from SEC documentation, which does not list the fields (the API page, checked the same day, names
none). **The builder's fixtures must match these shapes.**

**Submissions (`data.sec.gov/submissions/CIK##########.json`).** Top level has `name`, `tickers`, `sic`, `formerNames`,
`fiscalYearEnd` and `filings`. `filings.recent` is a table of parallel lists, one entry per filing, with
`accessionNumber`, `filingDate`, `reportDate`, `acceptanceDateTime`, `form`, `items`, `primaryDocument`, `size`,
`isXBRL`. Findings that change the design:

1. **`items` is one comma-separated string** (`"2.02,9.01"`), and empty for forms with none. The channel filters of
   protocol §12.3 must split it.
2. **`acceptanceDateTime` is UTC** (`2026-08-20T14:59:01.000Z`); `filingDate` is a plain date. §4.3 compares the date
   rule on `filingDate` (decision 3) and uses acceptance only as a consistency check against the filing date, converted
   to US Eastern first, so a late-evening acceptance is not read a day late.
3. **`recent` is not the whole history.** It held 1,004 rows, filing dates 2023-06-02 to 2026-10-08, and only 3
   10-Ks; older filings are in the pages listed under `filings.files` (two here, with their date ranges). §4.4 must
   follow those pages whenever `recent`'s earliest date is later than a lookback needs, and the cache keys them like
   any other URL.

**Company facts (`data.sec.gov/api/xbrl/companyfacts/CIK##########.json`).** `facts` has the taxonomies `dei`,
`us-gaap` (478 tags here), `ecd`, `ffd`, `invest`. A tag holds `units`, and under `USD` a list of facts with `start`,
`end`, `val`, `accn`, `fy`, `fp`, `form`, `filed` and sometimes `frame`; a point-in-time figure (a balance) has no
`start`. The tags §4.6 tries first were all present (`Revenues`,
`RevenueFromContractWithCustomerExcludingAssessedTax`, `SalesRevenueNet`, `OperatingIncomeLoss`,
`NetCashProvidedByUsedInOperatingActivities`, `LongTermDebt`, `PaymentsToAcquirePropertyPlantAndEquipment`). Findings:

4. **Repetition is the norm, so the "latest admitted wins" rule is required, not a nicety:** 99 of 111 periods of one
   tag appeared in more than one filing (a quarter reported again as a comparative a year later).
5. **`fy` and `fp` describe the filing, not the figure.** One annual period appears with `fy` 2025 in the filing that
   reported it and `fy` 2026 in the next year's filing, where it is a comparative. **The builder keys every figure by
   `start` and `end`, never by `fy`**, and dates a fiscal year by its `end`. (This filer's year also ends in January,
   so `fy` runs ahead of the calendar.)
6. **`frame` is a label added after the fact** (the same period had none on the earlier filing and one on the later).
   The cut-off logic never reads it.
7. **`form` in the facts is only `10-K`, `10-Q` and `10-Q/A`** here, and a 10-K's annual rows span 364 or 365 days,
   which is how an annual figure is told from a quarterly one in the same tag.

**Left for the build:** the splitter has still seen no real filing's HTML (§10); this step read structured data only.
