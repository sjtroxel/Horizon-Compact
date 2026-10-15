# Phase 5 — Case Building, search half: IMPLEMENTATION (v0.5)

> **IMPLEMENTATION doc, search half. Written 2026-10-15 (Opus), immediately before the search. APPROVED 2026-10-15 (his,
> about 3:50 PM CDT), all seven decisions in §8 as recommended, (a).** Sources: the Phase 5 scope doc (`docs/phases/phase-5-case-building.md`, its
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
read <id> <criterion> agree|disagree [--resolution ...] | public`. Each call loads the newest
`selection-log-<n>.json`, applies one `record` or `record_read` (which enforce the order, the reasons and the
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

`hc case scenario check <label>` checks the file against its shape: same keys, kinds, labels, rules and wording
outside the facts; every cap either equal to the total or listed with its source in `build.json`; no digit outside a
figure; and no figure absent from the case's figure sources. **The reader reads every case's scenario file for
neutrality** (decision 4), given the shape and the sources, not the rubric.

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
8. `hc case scenario check` (§4.6) and `hc case lock` (writes `case.lock` from `content_hashes`).
9. The reader command and its three briefs (§4.9), committed before the first read.
10. The probe: `upload`, the container command, `probe-verdict`, `task.json` (his Terraform plan and apply, Claude
    reading the plan), the S3 and GitHub readers (§4.8, §4.10).

### Stage D: the cases (as many sessions as it takes)

11. Criteria 1-4 down each type's list, in order (§4.1 step 1). Reader on each 3-4 rejection.
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
