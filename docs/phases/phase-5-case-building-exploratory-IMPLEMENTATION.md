# Phase 5 — Case Building, exploratory part: IMPLEMENTATION (v0.5)

> **IMPLEMENTATION doc, exploratory part. Written 2026-10-19 (Opus, about 1:00 PM CDT), immediately after the
> search-half doc's §4.6.5 was adopted (his, about 12:50 PM, after the independent reader's read). APPROVED 2026-10-20
> (his, about 8:35 AM), all three decisions in §6 as recommended.** This doc is the build plan for §4.6.5; the rules themselves are in
> §4.6.5 and are pointed to here, not restated. Sources: the search-half doc (`phase-5-case-building-search-IMPLEMENTATION.md`)
> §4.1, §4.3, §4.6 to §4.6.5, §4.8, §4.9 and Stage D; the code as read 2026-10-19 (`casebuild/search.py`,
> `casebuild/scenario.py`, `reader/material.py`, `cli.py`, `analysis/matcher.py`); `KNOWN-GAPS.md`'s OPEN entries of
> 2026-10-16.
>
> **Rule zero.** This doc names no company, no candidate and no identifier, and neither does anything this part
> commits. Every case is called by its neutral label everywhere outside the private appendix.

## Read this first: the plan on one page

| Stage | Steps | What happens | Who | Costs his cash? | Status |
|---|---|---|---|---|---|
| **1. The code** | 1-6 | the exploratory log and its command, the S3 case form, the brief, the new channel | Sonnet builds, Opus reviews; his commit | no | **done 2026-10-20** |
| **2. Step 2's rows** | 7-9 | the ten pre-registered S3 rows re-read; the new channel run and checked; a count | Opus with him | a few cents (rejection reads) | **done 2026-10-21: 2 rows pass** |
| **3. Each passing row to a case** | 10 | build, scenario, rubric, lock, probe, as every case | Opus with him | yes, about 10 cents a read: **the one top-up comes due here** | not started |
| **4. The reserve** | 11-13 | the pre-cut-off pool and the knowledge probe; the pool extended; a second search on 2027-01-04 | as stage 1, then 2 and 3 | cents | **opened 2026-10-21** (decision 2(a)): step 3 first |
| **5. The freeze** | 14 | the cases frozen with their labels | Opus with him; his commit | no | not started |

**Where to look:** this doc is the plan, and each step gets a `[done]` marker and an as-built note (§9) as it is
built. The rules are §4.6.5 of the search-half doc. Where things stand today is `KNOWN-GAPS.md`'s START HERE.

## 1. Where things stand on 2026-10-19

- **The pre-registered selection is complete with no case** in any type (`selection-log-633.json`; shortfalls 2, 2
  and 1). It stays as recorded and is reported first.
- **§4.6.5 is adopted:** an exploratory record, the figure-free S3 form (step 0), looser S3 rules (step 1), the ten
  pre-registered S3 rows re-read and one new in-window channel (step 2), and a reserve (steps 3 to 5).
- **Nothing of it is built.** Last commit `2b4549f` (pushed); `make check` green, 2532 tests.
- **Money:** his OpenRouter balance was under $1 on 2026-10-19; the Anthropic prepaid credit was about $15.95 at its
  last reading (2026-10-15); AWS runs on credits. §4 says what draws on each.

## 2. What this part delivers

1. **The exploratory record:** its own write-once log, its command, its public view carrying each case's step and
   label (§4.6.5 B).
2. **The S3 case form and the S3 rules in code and in the reader's brief** (§4.6.5 step 0 and step 1).
3. **Step 2 done:** the ten rows re-read at criterion 4 and the new channel's rows checked through criterion 4.
4. **Each passing candidate taken to a frozen case** by the search half's §4.1 steps 2 to 9, unchanged.
5. **The reserve built only when opened** (steps 3 to 5).
6. **Up to five cases, each labeled exploratory, or a shortfall reported** after every opened step.

## 3. The steps

### Stage 1: the code (Sonnet builds, Opus reviews each diff; no model call, no cash)

1. **[done 2026-10-20, Sonnet built, Opus reviewed, two fixes applied] The exploratory log** (`casebuild/exploratory.py`, new, reusing `search.py`'s `Row`, `Result` and `Read`;
   `search.py`'s pre-registered log unchanged). Rows carried from `selection-log-633.json` by id, each with that file's
   name and sha256 (§4.6.5 B.2); criteria per row (a carried or in-window row: §12.4's, as now; a pool row: `not_known`
   added after `maps_to_shape`); **one order across types** (D.1); per type the first k that pass, the fill of a short
   type's slots (D.3), the selection held open while an earlier row is unfinished (D.4), and the stop at five (D.5).
   Written once per version as `search/exploratory-log-<n>.json`, with `exploratory-public-<n>.json`, whose rows carry
   their step and §4.6.5 B.3's label. **Tests:** a carried row keeps its results and refuses an edit of them; the
   order across types; the fill; the stop; a hand-edited file refused, as `SelectionLog.from_text` refuses one.
2. **[done 2026-10-20, Sonnet built, Opus reviewed, three fixes applied] `hc case xlog`** (`cli.py`): `show`, `carry <id>`, `record <id> <criterion> pass|fail --reason ...`,
   `read <id> <criterion>` and `public`, in the shape of `hc case log`. **Tests** as for `hc case log`.
3. **[done 2026-10-20, Sonnet built, Opus reviewed, two fixes applied] One answer to "which row is this label's"** (B.4): `hc case documents`, `build`, `scenario render` and `check`,
   `reader`, `lock`, `probe` and `probe-verdict` read the exploratory row when the exploratory log has one for the
   label, else the pre-registered row, and read a candidate's details from `candidates.json` or the new channel's
   candidate file. **Tests:** each command finds an exploratory row; a carried row is never read from the old log once
   it is carried.
4. **[done 2026-10-20, Sonnet built, Opus reviewed, three fixes applied] The S3 case form** (step 0): `experiment/case-forms/s3.toml` holds the three option sentences and the situation
   sentence to drop; `casebuild/scenario.py` uses it when equal treatment applies to an S3 case; the pay-per-head
   check on each kept sentence that states a heads row and a total-pay row (step 0 item 3); a scaled exploratory S3
   total under 100 stated as a number (step 1 item 2). **Tests:** `hc scenarios check` still passes, so Phase 4's S3
   is unchanged byte for byte; a case with no option figures renders the three sentences; the situation sentence is
   dropped; a scaled total of 60 reads 60; the pay-per-head check passes and fails as it should.
5. **[done 2026-10-20, Sonnet built, Opus reviewed, two fixes applied] The brief and the reader's material** (step 1 item 7): the four changes to `experiment/readers/rejection.txt`;
   `reader/material.py` sends, with an S3 total rejection, the public report saved as `total-report.txt` (the report's
   text under a line naming its source and date, saved by rule before the result is recorded, as `total-search.txt`
   is). **Tests:** the brief's text; the material with and without a report. Logged in the search-half doc's §11 as a
   change to the instrument.
6. **[done 2026-10-20, Sonnet built, Opus reviewed, one rule added] The new channel** (step 2 item 2): its ten phrases as data, each its own query (`Query(4, ...)`, `items` 7.01 or
   8.01, `sics` 2000-3999); `hc case search --channel press`, run once, writing `search/press-candidates.json`
   (write-once; ids `press-01` on, `press-f01` on for the fallback month), leaving out any filing already a
   candidate; rows typed at criterion 4. **Tests** on fake replies, as for the search.

**His, to close stage 1:** `make check`, then one commit (`phase 5: exploratory record, S3 case form, press
channel`) and a push. *(2026-10-20: steps 1 to 4 were committed as they were reviewed, so the closing commit holds
steps 5 and 6 only: `phase 5: reader brief, press channel`.)* The reader's inputs change, so they are pushed before the next read.

### Stage 2: step 2's rows (Opus with him; reads cost a few cents)

7. **[done 2026-10-21, 07 passes, 19 passes on the reader's dispute, eight rejected] Carry the ten rows** (`hc case xlog carry` for closure-04, 05, 07, 09, 16, 19, 24, 27, 29 and f01) and record each
   one's criterion 4 under step 1. Where the filings give no headcount at the facility, the public-report search
   comes first (a WARN notice for a site in the United States, the company's later releases, news reports that
   attribute the number to the company, a union or a government office; dated up to 60 days after first disclosure),
   and the report is saved in the case's private folder before the result is recorded. A rejection goes to the reader
   (1 to 3 cents a read).
8. **[done 2026-10-21, nine rows, all fail criterion 1] Run the channel** (his one command, `hc case search --channel press`) and take its rows through criteria 1 to 4
   in order, by the search half's §4.3 and Stage D methods. *(2026-10-20)* At criterion 1, a row the command lists
   under `same_filer_as` is read against those earlier candidates: the same decision fails as "already a candidate:
   <id>" (search-half doc §11, 2026-10-20).
9. **[done 2026-10-21: two, so decision 2(a) opens stage 4] Count the rows that pass criterion 4.** Five or more: stage 4 stays closed. Fewer: decision 2.

### Stage 3: each passing row to a case (as many sessions as it takes)

*Before step 10 (2026-10-21):* **the pay-per-head fix,** the search-half doc's §4.6.6 (drafted by Opus, adopted by him
2026-10-21, no independent read): a scaled S3 total under 100 to the nearest whole person, and an S3 total-pay figure to three
significant digits with no $100,000 step. A Sonnet build (in the drafting session, his choice) and a fresh Opus chat's review (§4.6.6 F), his commit and
push, then step 10.

10. **For each passing row, in §4.6.5 D.1's order,** the search half's §4.1 steps 2 to 9, unchanged: his identifiers
    into the term file; `hc case build` (the Anthropic credit, about $0.32 a build); his flag review; the scenario
    render and check; the rubric and its read; the foreshadowing and neutrality checks; `hc case lock`, his commit and
    push; the upload; the probe; the verdict. **The first scenario read and rubric read are where his OpenRouter
    balance needs its one top-up** (§4). A probe failure needs the coarsened dossier's home settled first
    (`KNOWN-GAPS.md`, OPEN 2026-10-16), before any second probe set.

### Stage 4: the reserve (only when §4.6.5 D.6 opens it)

11. **Step 3, the pre-cut-off pool:** `hc case search --pool pre` (filing dates 2025-07-01 to 2026-06-30, channel 1
    and the press channel, newest first, write-once `search/pre-candidates.json`), with closure-f04 and closure-18
    joined as step 3 item 6 says; `hc case knowledge-probe <label>` (on the laptop; three calls each to `haiku-5-5`,
    `gpt-oss-openrouter` and `sonnet-5-5-extraction`; step 3 item 4's message word for word; write-once records;
    refused unless the row stands at `not_known`); his read of every answer that is not "unknown"; the reader on every
    failure, with a new brief committed before its first read. Built by Sonnet and reviewed by Opus, like stage 1;
    then stages 2 and 3 for its rows.
12. **Step 4:** the same search over 2024-07-01 to 2025-06-30.
13. **Step 5:** on 2027-01-04, the three channels of §12.3 and the press channel over 2026-10-16 to 2027-01-03.

### Stage 5: the freeze

14. **The search half's Stage E, for the exploratory record:** its `problems()` empty and its selection closed; the
    freeze commit lists every case with its step and label; the measured cost against §4; the DoD audit (§7);
    ROADMAP and START HERE.

## 4. Money

| Pot | What draws on it | Expected, from here to the end of Phase 5.5 |
|---|---|---|
| **OpenRouter, his cash** (under $1 on 2026-10-19) | rejection reads (1 to 3 cents each); each case's scenario and rubric reads (about 10 cents each, about $1 for five cases); `gpt-oss-120b`'s probes (pennies) and its Phase 5.5 runs (about 70 cents); if stage 4 opens, the knowledge probe's `gpt-oss-120b` calls and its reads (cents) | **about $2 to $2.50 in all: one top-up, OpenRouter's $5 minimum (about $5.80 with the card fee, per third-party sources), at the first scenario read** |
| **Anthropic prepaid credit** (about $15.95 at the 2026-10-15 reading) | builds (about $0.32 each); Haiku 5.5's probes and Phase 5.5 runs (about $2.40); the knowledge probe's Sonnet and Haiku calls (about a cent a candidate) | about $4 to $5 |
| **AWS credits** | Fargate for the probes and the runs | under $1 |

**The rule for paid calls** (his, 2026-10-19): after every batch of paid calls, the measured cost is totaled from the
reply files and said against his last known balance, and any step that would need more than the balance is named
before it runs. The reader's candidate reads cost $3.92 through 2026-10-19, four times the search half's projection,
which no one compared against his cap at the time; this rule is why.

## 5. Rules this part must not break

- **Rule zero**, in every file, commit, branch, message and chat summary; labels only.
- **The pre-registered selection log is never written again.**
- **No case's decision runs** (that is Phase 5.5's), and the rubric precedes the model: `case.lock` committed and
  pushed before a case's first probe.
- **The frozen files are not touched:** the protocol, `experiment/company/`, `sweep/prompt.py`, `decision.py`,
  `classify.py`, `analysis/`, `experiment.py`, a locked model's identity in `models.toml`. The S3 case form lives
  outside `experiment/company/` for this reason.
- **Selection follows §4.6.5 D:** one order, the first k, the fill, the stop; nothing is picked by hand.
- **`make check` before every commit; CI green.** He runs every commit, push, Terraform and AWS-authenticated command.

## 6. Decisions for him

1. **The command for the exploratory log.**
   - (a) **Recommended: `hc case xlog`**, a command of its own, so the pre-registered log cannot be written to by
     mistake.
   - (b) A flag on `hc case log`: one command to learn, at the risk of a slip writing to the wrong log.
2. **If fewer than five rows pass criterion 4 in stage 2.**
   - (a) **Recommended: open step 3 early** (§4.6.5 D.6), so the pool's search and knowledge probes run while stage 3
     builds the rows already passed. The search is free and the probe costs cents, and the order decides which
     candidates are cases, so building ahead changes nothing about selection.
   - (b) Wait until every stage 2 candidate is finished, as D.6 has it by default: no work on a pool that may not be
     needed, at the cost of days.
3. **The model for the build.**
   - (a) **Recommended: Sonnet builds stage 1 (and stage 4 if it opens) and Opus reviews each diff,** the repo's rule
     for routine implementation, at medium effort; Opus does the judgment steps of stages 2 and 3 with him.
   - (b) Opus throughout: more careful on routine code, and much heavier on his usage limits.

**Decided 2026-10-20 (his): 1(a), 2(a), 3(a).** §11's 2026-10-18 entries stay as written (his, the same morning);
past commits are public either way.

## 7. Definition of done

| # | Done when | Proof |
|---|---|---|
| 1 | The exploratory record enforces §4.6.5's carry, order, fill and stop | its tests; `hc case xlog show` |
| 2 | The S3 case form renders, and Phase 4's S3 is unchanged | `hc scenarios check`; the render tests |
| 3 | Step 2's rows re-read and the press channel run and checked | the exploratory log |
| 4 | Up to five cases frozen, each labeled, or a shortfall reported after every opened step | the freeze commit; the public view |
| 5 | Every judgment rejection read; every paid batch totaled against his balance | the log's reads; the search half's §11 |
| 6 | `make check` and CI green at every commit | CI run IDs |

## 8. Genuinely uncertain

- **Whether public reports give the step 2 rows' plant headcounts.** Five of the ten depend on them, and the main
  route depends on those five.
- **The first real build.** The splitter and the extraction have never run on a real filing; a split it refuses is
  done by hand (search half §4.5).
- **The recognition probe on large companies,** and the coarsening procedure, which is not yet designed (OPEN
  2026-10-16).
- **Whether three cases are reached without stage 4.** Not measured; §4.6.5 G says what is expected.

## 9. As built

**Step 1 (2026-10-20, Sonnet built; Opus reviewed, high effort).** `casebuild/exploratory.py` and `tests/test_casebuild_exploratory.py`
(30 tests after the review; `make check` green, 2562). `search.py` changed by two read-only properties on `Row` (`criteria`,
`read_required`) that the new row type overrides; the pre-registered log behaves as before. Choices the plan did not
fix, for the review: (1) the file is an **event list** replayed through the code that took each change, with the
step's `not_known` criterion only on step 3 and 4 rows; (2) a **carried row stores no results**, only the source log's
name and sha256, and the replay reads them from that file (a changed source is refused); (3) **the list a row is on is
settled at `maps_to_shape`** (`case_type` on that record), and a disputed `maps_to_shape` read that names a type sets it
(there is no list to fail on in this record, so the selection log's "a pass of another type agrees" does not apply);
(4) **selection** holds a type open at its first unfinished row before its k-th case, fills a short type's slots from
the first passing unselected rows in order, and waits at the first unfinished row if any type is open or the fill meets
one; (5) **checking stops** by refusing a result for a row ordered after the fifth case, so a step 3 row checked ahead
is allowed until five exist. Not built: any way to `add` rows from a candidate file (press, pool, late), which needs
step 6 and stage 4's files; step 2 (`hc case xlog`) is next.

*The review (Opus) found two faults, both fixed, with tests:* (a) **a complete selection could change.** An unfinished
row held open only its provisional type, but its list is settled only at `maps_to_shape`, so a row added as closure
that turned out a retool could displace a retool case already reported complete (reproduced, D.4). Now a row whose
list is not settled holds every type not yet full; once settled, only its own. A consequence, which D.3 already says:
a type is not short while any unchecked row could still be of it, so opening step 3 early (decision 2) delays the
fill until its rows are checked, without changing which rows are cases. (b) **A carried read could be changed** in the
new log (a disputed rejection turned into one that stands); a read of a carried criterion is now refused. *Open, for
stage 4:* step 3 item 6's rows (closure-f04, and closure-18 if its date falls inside), which failed the first-disclosure
check and join the pool "as if filed on that date", fit neither `carry` (it needs every criterion before criterion 4
met) nor the pool's order (by id); they need their own event when stage 4 is built.

**Step 2 (2026-10-20, Sonnet built; Opus reviewed, high effort).** `hc case xlog` with `show`, `carry <id>`,
`record <id> <criterion> pass|fail --reason [--public-reason] [--disclosed] [--list]`, `read <id> <criterion>
[--resolution]` and `public`, in `cli.py`; 12 tests in `tests/test_case_cli.py` (`make check` green, 2574). Choices the
plan did not fix: (1) **no type argument**, since the log runs across types; the list a row goes on is `--list` on its
`maps_to_shape` record; (2) **`carry` reads the highest-numbered `selection-log-<n>.json`**, the pre-registered
record's last version, and names it in the event; (3) `read` offers `real_decision`, `maps_to_shape` and
`not_recognizable` only: the `not_known` read is stage 4's (it needs a reader brief and material that do not exist),
though `record` accepts `not_known`; (4) `_log_status` now takes a row's own criteria (the same text for every
pre-registered row); (5) the verdict line says "agrees" for any reading but "pass", as the exploratory log decides it.
Not built, as in step 1: adding rows from a candidate file.

*The review (Opus) found two faults, both reproduced by a failing test first and fixed:* (a) **`xlog read` would log
the pre-registered record's read as the read of the new rejection.** Every step 2 row was rejected at criterion 4 and
read under the old rules, and that reply is still the newest one in its folder. A carried row now keeps the names of
every reply the old record logged for it, and none of them is accepted as a read here. (b) **`hc case log` could still
write the pre-registered log:** a criterion 4 read can be replaced while no later criterion is recorded, so a read meant
for the exploratory log, sent through `hc case log` by mistake, would have rewritten the old one. `hc case log record`
and `read` now refuse once any `exploratory-log-<n>.json` exists (§4.6.5 A.1); `show` and `public` still work. Also:
`ordered()` made public, since the CLI calls it. *For later steps:* step 3 must make `hc case reader` find an
exploratory rejection (today it reads the pre-registered log, so no new read can be made yet); step 6 must widen the
public-reason check to the press channel's candidate names (today it checks `candidates.json` only).

**Step 3 (2026-10-20, Sonnet built; Opus reviewed, high effort).** `row_for(search, label)` and `candidate_records(search)` in
`casebuild/exploratory.py`; `make check` green, 2585 tests (8 new, in `tests/test_case_cli.py`). The exploratory log's
row is the row of record when it has the label, else the pre-registered log's; a carried row is never read from the old
log. Callers moved: `hc case documents` and `build` (`_candidate_cik_and_row`, which now checks `row.criteria`, so a
pool row's `not_known` is required before the build and `not_recognizable` stays the probe's), the scenario check's
first-disclosure date (`_disclosure_failures`), and the reader's `rejection_ready` and `probe_read_ready`. Candidate
details come from `candidates.json` and, when it exists, `press-candidates.json` (assumed the same `{"list": [...]}`
shape; step 6 fixes it); the public-reason check in `hc case log` and `xlog` reads both, which closes the step 2
note about widening it. `reader`'s hint lines and `probe-verdict`'s now say `hc case xlog` for an exploratory label
(`_log_command`). `scenario render`, `lock`, `probe` and `upload` never read the log, so they needed no change.
*Not done:* the `not_known` read (stage 4); the `xlog read` of a probe failure's reply is as step 2 left it.

*The review (Opus) found two faults, both reproduced by a failing test first and fixed:* (a) **`hc case reader` would
pay for a read that could never be logged.** For a label the exploratory log lacks, `row_for` gives the pre-registered
row, and `rejection_ready` and `probe_read_ready` accepted its unread rejection, though `hc case log read` refuses
once the old log is closed. Both now refuse a pre-registered row once an exploratory log exists, and say to carry it
first (`exploratory_started`, which `hc case log` now uses too). (b) **`candidate_records` let an id in both
candidate lists take the press channel's record silently**, so the CIK the build fetches could come from the wrong
file; an id in both is now refused. *Tests added for what the step claimed but did not test:* a pool row is refused
at the build until `not_known` is recorded, and the scenario check finds a row that only the exploratory log holds
(the earlier test used a carried row, whose date is the old log's, so it would have passed on the old code). 2589
tests. *Left as is:* §4.6.5 B.4 names `lock` and `probe`, but neither reads a row today, so there was nothing to
move; whether `probe` should check that a label has passed criterion 4 is a question for stage 3, not this step.

**Step 4 (2026-10-20, Sonnet built, Opus reviewed).** `experiment/case-forms/s3.toml` (the three option
sentences as the search-half doc gives them, and the one situation sentence to drop), read by `casebuild/scenario.py`
(`S3Form`, `parse_s3_form`); `make check` green, 2611 tests (22 new). `experiment/company/` is untouched, so `hc
scenarios check` and the tag's hash are as they were. What it does: (1) **the form applies when any S3 option sentence
names a figure the case lacks** (the same trigger as equal treatment), replaces all three option texts, and takes "The
figures for every option are management's estimates." out of the situation; the render refuses if the file is missing
or a sentence to drop is not in the template. A full S3 case renders as before. (2) **The S3 floor and a small total:**
an S3 total is stated as a number to the nearest 5 even under 100 (`scale.scale_total_heads`; a derived total keeps its
row's step), and the render refuses a total under 50 as stated, unscaled (`_unscaled`, a case row's value or its
formula over case values). Other shapes keep "under 100 after scaling". (3) **The pay-per-head check**
(`_pay_per_head`): on each kept S3 sentence holding exactly one headcount and one total-pay row, it runs
`scale.check_pay_per_head` and records the result as `pay_per_head` in `scenario-render.json`; a failure refuses the
render and writes nothing, naming rows and never a value. `scenario-render.json` gains `pay_per_head` for S3 and
`case_form` (file and sha256) only when the form was used, so no other shape's record changes.

*Choices the plan did not fix:* the total-pay rows are an explicit S3 set (`payroll_p6`, `s3_retool_payroll`,
`s3_sell_payroll`), not a pattern; a sentence holding more than one headcount or more than one pay row refuses (no
fixed S3 sentence does); `drop_sentences` is now built on a public `without_sentences(text, predicate)`; the shared
test fixture states the `oews_wage_*` rows unscaled with `per` (a per-head wage is a ratio, `CaseRow`'s own rule), or
every S3 render would fail the new check.

*Two things for the review and for him:* (a) a payroll derived from the headcount was said never to fail the check;
**the review found it can** (below). (b) **Rounding to the nearest 5 alone moves a headcount by more than 3.5% under
about 70 people**, so a small S3 case that states its own payroll can fail the check on rounding, not on any fault;
the plan says a failure is a build error, so it refuses. *Tests for "a scaled total of 60 reads 60"* run at 60
(factor 1.0), 52 (1.1, reads 55) and 50 (1.0); the cap rows under 100 are set to the total by the existing rule,
unchanged.

*Opus review (2026-10-20, high effort), three fixes applied:* (1) **the reader was sent an unscaled value:**
`pay_per_head` holds pay per head before scaling, and `reader/material.py` passed every render-record field but the
factor and the hashes; it is now private as they are (test extended). (2) **The stated-payroll test failed for the
wrong reason:** it gave `payroll_p6` as 2.86 in a `usd_m` row, whose values are in dollars, so the scaled payroll
rounded to zero and pay per head moved 100%; now $2,860,000, which fails at about 5%. (3) **The refusal said "his to
decide"**; protocol §12.6 makes a failure a build error (fixed in the builder and the case rebuilt with the factor
unchanged, or, if none is found, criterion 4 fails), and the message now says so. *Found, not changed (his call):*
**a correct build can now fail the check, derived payroll or stated.** A derived payroll is the rounded headcount
times the wage, then rounded to a `usd_m` row's $100,000 step, which moves a payroll under about $1.43 million by more
than 3.5%; a sweep found it at a stated total of 54, factor 0.6 (stated 30) and a $45,000 wage. It needs a small
plant, a low factor and a low wage together (5 of 1,470 renders over totals 50 to 119, factors 0.6 to 1.1 and wages
$36,000 to $45,000; none at the fixture's wages). §12.6's premise that a correct build always passes was argued for
headcounts of 100 or more; step 1 item 2 states smaller ones. The recommendation is to leave the code: the refusal is
loud, and if it fires, §12.6's own path (fix the builder, rebuild, factor unchanged) recovers the case. *Left as is:*
when the form replaces the options, their dropped sentences are not counted in `sentences_dropped` (the record's
`case_form` says the options were replaced); the floor's refusal says "under 50 as stated" also when the total
cannot be stated unscaled at all, which no S3 row set reaches today.

**Step 5 (2026-10-20, Sonnet built, Opus reviewed).** `experiment/readers/rejection.txt`: the four changes of
§4.6.5 step 1 item 7, in the `maps_to_shape` paragraph and nowhere else, word for word as the item gives them (the
product-making facility sentence after the S3 shape rule; the S3 total "as a source states it", with jobs cut and
several facilities excluded; "For S1 the total must be 167 or more; for S3, 50 or more"; the public report added to
the total's material). `CaseAppendix.total_report_path` (`total-report.txt`, hand-placed, private) and
`material.rejection_material`: a `maps_to_shape` read is sent it as a third block, "Public report of the facility's
headcount", after the search of earlier filings, when the file exists; no other read is sent it; an empty or over-long
file is refused, not dropped; its hash goes into `material_sha256` with the other parts. `make check` green, 2614 tests
(3 new, 1 changed), `hc protocol check` ok. No read was made. **Not enforced in code, as for the search and the
excerpt:** that the report was saved before the result was recorded, and that its first line names its source and date
(his or Opus's, per stage 2 step 7). **The brief's sha256 changes**, so it is pushed before the next read (the stage 1
commit says so); the search-half doc's §11 logs the change to the instrument.

*Opus review (2026-10-20), two fixes:* (1) **A carried row could not be read again.** Each of the ten rows stage 2
carries already has the pre-registered record's `maps_to_shape` read in its folder, and a rejection's once-only rule
counted every attempt there, so `hc case reader` refused the read B.2 asks for ("was read already"); and the reply
lookup returned the oldest reply, which the exploratory log rightly refuses. Now the replies the carried row's
pre-registered reads name (`prior_replies`, `read.earlier_record_replies`) are passed over by both; the new read's
number follows theirs (`-2`), so their files are never written again. A test makes the old read, carries the row,
rejects it again, makes the new read and checks it alone is logged and made once. (2) **The report's block was named
"Public report of the facility's headcount"**, which tells the reader the thing the brief asks it to judge (whether
the report's number is the plant's headcount, step 1 item 4). It is now "Public report", the brief's own words.
`make check` green after both.

**Step 6 (2026-10-20, Sonnet built; Opus review pending).** `casebuild/search.py`: `PRESS_PHRASES` (the ten, in
§4.6.5's order, as data) and `PRESS_QUERIES` (`Query(4, "closure", ...)`, `items` 7.01 or 8.01, `sics` 2000-3999); they
are **not** in `QUERIES`, so protocol §12.3's table and the test that compares it are untouched. `run_search` gained
`id_prefix` (ids `press-01`, `press-f01` for the fallback month; refused for queries of more than one type) and
`exclude` (accession numbers already candidates, left out and counted as "already a candidate" in the query's
`dropped`); with neither, it behaves as before (a test says so). `write_candidates` takes the file's name.
`cli.py`: `hc case search --channel press --date <today>`, run once. It refuses without `candidates.json` (it leaves
out those filings), a second run, a `--deviation`, and a day that is not today; it uses the search's own dates
(2026-07-01 to 2026-10-15, the fallback month held apart). It writes `search/press-candidates.json` (write-once,
`channel` and `step` in its record) and **adds each hit to the exploratory log as a step 2 row, typed `closure`**,
as the next `exploratory-log-<n>.json`, so no separate "add" command is needed; the list is settled at criterion 4
as for every row. Counts only are printed. With no hits it writes its file and no log version. `make check` green,
2626 tests (11 new). **Not decided here:** the press rows' initial type is `closure`, the list the
phrases point at; a row that reads as a retool is moved at criterion 4 by `hc case xlog record ... --list retool`.
**His, stage 2 step 8:** one command, `hc case search --channel press --date <that day>`, after the commit and push
that close stage 1. The channel reads the SEC, never a model: no cash.

*Opus review (2026-10-20), no fault in the code; one gap, closed by a rule (his):* **"one decision is one case" was
checked by filing only.** The channel leaves out a filing already a candidate by accession number, and the log's
duplicate check compares accession numbers, so a decision announced in two separate filings would come in twice
when the press filing is the earlier one. Now `press-candidates.json` records each row's earlier candidates from the
same filer (`same_filer_as`, by CIK; private) and the command prints how many; at criterion 1 a row that is the same
decision fails as "already a candidate: <id>" (search-half doc §11, 2026-10-20; stage 2 step 8). It flags, it does
not leave out: a different decision of the same company is an ordinary row. One test added. Both of Sonnet's choices
stand: rows start as `closure`, which is safe because a row whose list is not settled holds every open type (step 1's
review); and every SEC request finishes before either file is written, so only a local write can split the candidate
file from the log version.

**Stage 2 (2026-10-21, Opus with him; about $0.16 of his OpenRouter credit).** *Step 7.* The ten rows carried
(`exploratory-log-1` to `-10`) and each one's criterion 4 recorded under step 1 (`-11` to `-20`), after a
public-report search for every row whose filings gave no plant headcount. Each report used was saved as the row's
`total-report.txt` before its result was recorded (07, 16, 19, 29; for 07 also the notice itself, privately).
**closure-07 passes:** its filings give only an upper bound of positions eliminated (item 4), but the WARN notice the
company filed with a US state on the first-disclosure day states the number as "all individuals employed by the
Company at the Plant": 65, as a source states it, 50 or more. A government notice of the closing, inside the 60 days
(item 3). **Eight rejections stand** after the reader's reads (`-21` to `-28`): 04 (a laboratory, step 0 item 4), 05
and 24 (more than one facility, item 5), 09, 27 and f01 (no report in the 60 days states a headcount at the
facility; several say the company gave none), 29 (the company's number is its employees in the country, including
roles outside the plant), and 16 (only "positions affected", recorded as a fail by the letter of item 4, his
decision, so that the reader judged it; the reader agreed). **closure-19 passes on the reader's dispute** (`-29`):
the rejection rested on item 3's attribution rule (the only site number, about 150 in the plant's production, is from
a chemical park's profile, relayed by a trade portal, not from the company, a union or a government office); the
reader judged, as its brief asks, whether the number is the plant's headcount, and read it so. Under protocol §12.4
a disputed rejection does not stand; his resolution is logged with it. **Found: the brief does not carry item 3's
attribution condition** (step 1 item 7 changed only what the reader is told to judge). Open, his: whether the brief
gains it before stage 4's reads (a change to the instrument, logged as such; 19 is settled either way). The
write-up labels 19's headcount as from a third-party site profile.

*Step 8.* His one command, `hc case search --channel press --date 2026-10-21`: 8 rows in the window and 1 in the
fallback month (`-30`); one (press-08) shares a filer with two earlier candidates. **All nine fail criterion 1**
(`-31` to `-39`; no read is due on criterion 1): six match only accounting definitions, contract boilerplate or cost
lines of a restructuring announced earlier (one of them in 2024); press-02 and press-03 refer to closures the
filing itself calls announced before; press-08 completes a plan its own 8-K says was first disclosed before the
window (a different decision from the two earlier candidates of its filer, so not "already a candidate").

*Step 9.* **Two rows pass criterion 4 (closure-07 and closure-19), both closure, both S3.** Fewer than five, so by
decision 2(a) stage 4 opens now (step 3: the pre-cut-off pool and the knowledge probe, built by Sonnet and reviewed
by Opus) while stage 3 takes the two rows to cases. **The pay-per-head check needs a fix before either build** (step
4's "found, not changed", his decision 2026-10-21): a correct build can fail it at a small total, and protocol §12.6
drops a case whose failure has no error to fix, so §12.6's fix-and-rebuild path does not recover it, contrary to the
2026-10-20 recommendation. 07's total is 65 and 19's about 150 (90 at a factor of 0.6), both in the range where the
sweep found failures. A dated patch and a small Sonnet build, before stage 3's first `hc case build`.

*Paid calls:* nine reads, attempt 2 each, about $0.0086 to $0.0250 each, **about $0.16 in all**; his OpenRouter balance
about $10.56 after them (his reading; $10.72 before, after a $10 top-up that morning). A first run of the batch sent
nothing (the key was mistyped and refused before any call). Reader spend over every case in the appendix: about
$4.08.

**The pay-per-head fix (2026-10-21, Sonnet built in the drafting session at medium effort; reviewed by Opus in a
fresh chat the same day, high effort: no code fault).** The search-half doc's §4.6.6 F, as written. `casebuild/scale.py`: `scale_total_heads` rounds a scaled
total under 100 to the nearest whole person (from 100 up, to 5 as before); docstrings restate the bound.
`casebuild/scenario.py`: an S3 total-pay figure (`payroll_p6`, `s3_retool_payroll`, `s3_sell_payroll`), stated or
derived, is rounded to three significant digits and not then to the fictional row's step, and a case-side
`_PayResolved` (a subclass of `Resolved`, so `format_value` and the fictional rows are untouched) reads it in
millions with the digits it has, trailing zeros dropped to one decimal. `make check` green, 2642 tests (15 new);
`hc scenarios check` unchanged (content hash `a31d1f1184a5`). *Tests:* the sweep of §4.6.6 C as a test on a coarse
grid (fails on the old code); both payroll routes through the real render (a stated payroll at a total of 52, factor
0.9; a derived one at a total of 54, factor 0.6, wage $45,000, step 4's found failure); the reading of seven payroll
values; a derived payroll under a million; the fictional S3 payroll still reading to one decimal; the old tests at
52 and 50 updated (52 at 1.1 reads 57). The mis-scaled-wage test still refuses. *Left as is, for the review:* a total
*derived* from a formula (not a case row) under 100 keeps its row's step (hc_p6's is 10), so it reads in tens; no
S3 case row set reaches it today, since the total is a case row from the first-disclosure document. *Review:* agreed
to leave; the same row step also applies from 100 up, so §4.6.6 C's bound holds for a total that is a case row,
which step 1 item 3 requires (the total is taken from a document).

**Stage 4 step 3, part 3a: the pool search (2026-10-21, Sonnet built at medium effort; reviewed by Opus in a fresh chat,
high effort).** Step 11 is built in three parts, each reviewed before the next: 3a the pool and the item 6 join (this
note), 3b `hc case knowledge-probe` and its records, 3c the verdict (his read, the reader's new brief, the log's
`not_known` result). `hc case search --pool pre --date <today> [--join ID=YYYY-MM-DD ...]`: channel 1 and step 2's
channel over 2025-07-01 to 2026-06-30 (`PRE_QUERIES`; the protocol's table and `PRESS_PHRASES` untouched), a filing
found by two queries is one candidate, ids `pre-NN` newest filing first then accession number, every hit typed
`closure` and settled at criterion 4, written once to `pre-candidates.json` (with `same_filer_as`, as the press
channel's) and added to the exploratory log as step 3 rows in pool `pre`. `candidate_records` reads the new file, so
`hc case build` finds a `pre-NN` row's CIK. **Item 6 is by argument, not by guess:** the log keeps a failed row's
date only inside its reason text, so `--join` takes his reading of the earlier mention's date; the row must have
failed the first-disclosure check in the pre-registered log, and a date outside the pool's range is refused before
any request. A joined row is counted on that date for the order, with `joined_from` and `actual_file_date` in its
record. Not built, on purpose: step 4's search (2024-07-01 to 2025-06-30, ids continuing) is `run_pool_search` with
other dates and `first_number`, with no command yet (step 12). `make check` green, 2650 tests (8 new).
*Review:* one fault, fixed: a joined row carries its source row's own filing, so `same_filer_as` named that row
as its earlier candidate, which under the rule of 2026-10-20 would point criterion 1 at failing the row on itself;
the source row is now left out. Also fixed: the summary counts the list as `closure/pre` (was `pre/pre`), and
`--join` refuses a row not on the closure list (item 6). The rule for a joined row and a pool row that are one
decision is the search-half doc's §11 entry of this date. `make check` green.

**Stage 4 step 3, part 3a: the pool searched (2026-10-21, once, by him).** `hc case search --pool pre --date
2026-10-21 --join closure-f04=2026-05-12 --join closure-18=2026-05-12`. The dates are the earlier mentions that
failed each row, read from the pre-registered log's reasons with him: closure-f04's, the company's public statement
of 2026-05-12; closure-18's, the first-quarter results 8-K of the same day, which reported its restructuring in
aggregate (its 8-K names several sites, so step 1 item 5 may leave it no S3 total; criterion 1 or 4 judges it).
**Result, counts only:** 172 candidates, `pre-01` to `pre-172` (2026-06-29 back to 2025-07-01, 7 to 23 a month):
129 from channel 1 (5 of them also found by a press phrase), 41 by press phrases alone, and the 2 joined, `pre-18`
(closure-18) and `pre-20` (closure-f04). 30 share a filer with an earlier candidate; neither joined row is flagged
against its own source (the review's fix), and no pool row is the 2026-05-12 mention of either, so §11's rule (b)
is not needed. Channel 1's 129 is below §4.6.5 E's sizing count of 142, made before the patch with its own
filters; every query was read to its last page, so the recorded run is the pool. Written: `pre-candidates.json`,
`exploratory-log-40.json`.

**Stage 4 step 3, part 3b: the knowledge probe built (2026-10-21, Sonnet at medium effort, in the same chat as
3a's review; Opus review pending in a fresh chat).** `hc case knowledge-probe <label> [--yes]`, in
`caseprobe/knowledge.py` (not `casebuild/`: `tests/test_architecture` keeps probe answers out of the case builder).
Refused, before any byte leaves the machine, unless the label's row is a step 3 or 4 row that met every
criterion before `not_known` and has no result on it; then the inputs file, no earlier probe record, and the
models; then the spend question; then the keys; then, for each of nine calls, the request record, the call and
the reply record. **The message is filled from `knowledge-inputs.toml`, placed by hand in the case's folder**
(`shape`, `company`, and for S3 `facility` and `place`, in the first-disclosure document's own words): no name is
typed on a command line or printed, so a pasted session cannot carry one. S1 and S2 take the month and year from
the row's first-disclosure date; S4 has no message in item 4 and is not offered. **Models** are chosen by role,
exactly one `main` and one `second_family` plus the extraction model: `haiku-5-5`, `gpt-oss-openrouter`,
`sonnet-5-5-extraction` today; a models.toml that changes the set is refused. Three calls each, no system text,
4,000 tokens, the one message word for word (a test compares both templates with this doc's own text). **A reply
is never retried, whatever its status** (truncated, empty and filtered replies are recorded as such); an API error
is kept as its own record and retried with backoff, five at most per call, a fatal code stops. Records, write-once,
in the label's folder: `knowledge-probe-<model>-<n>-request.json`, `-reply.json`, `-error-<k>.json`, each with the
entry's and the prompt's sha256, the inputs file's sha256, the git commit and whether `src` or `experiment` had
uncommitted changes (recorded, not refused). A second run for the label is refused, including after a run that
stopped part-way. The command prints counts only (per model, how many answers were exactly "unknown") and logs
nothing: 3c holds his read of every other answer, the reader's brief and the log's `not_known` result.
**For the reviewer:** (1) the part-way rule, a stopped run is never resumed (the case probe resumes; item 5 says a
second run is refused, and a resume could shop for replies); (2) a dirty `src` is recorded, not refused, unlike the
reader's frozen-inputs check; (3) no pacing beyond the API-error backoff (nine calls). `make check` green, 2697
tests (47 new).

**Part 3b reviewed (2026-10-21, a fresh Opus chat, high effort).** One fault, fixed: the probe sent its "no system
text" as an empty one (`"system": ""` to Anthropic, an empty system message to OpenRouter), a request shape no call
had sent before; a 400 on it would have stopped the first run at its first call, and a stopped run is never resumed.
Both providers' text bodies now leave out an empty system text (the decision bodies are unchanged, and every
earlier text call sends one); two provider tests. `make check` green, 2699. **The three questions:** (1) the
part-way rule stands as built. A later rule to continue a stopped run (never repeat a call with a reply; make again
a call with none, as an API error is) could be adopted even after partial replies are seen, because one failed call
fails the candidate: continuing can add failures but never remove one, so it cannot shop. Decided only if a run
stops. (2) a dirty `src` recorded, not refused: accepted, since the request record holds the message and the whole
body sent. (3) no pacing: accepted. **For 3c, his:** (a) `gpt-oss-120b`'s reasoning cannot be turned off and its
text is kept in each reply's `raw_response`: does reasoning that states or guesses the decision fail the call,
when the answer is "unknown"? Recommended yes (a dated patch to item 4), which means reading its reasoning on all
three calls; (b) the probe's shape comes from the inputs file and the build's from `--shape`, with nothing tying
them: recommended, a probed row's build refused when its shape differs from the shape in its probe records.
**Both adopted (his, about 3:45 PM) and built the same chat (Opus):** the search-half doc's item 4 has a dated
note and §11 an entry. (a) each call's result records whether its reply carried reasoning, and the command counts
those among "for him to read"; 3c reads the reasoning from `raw_response`. (b) `check_build_shape` in
`caseprobe/knowledge.py`, called by `hc case build` after its log check and before any fetch or key, compares the
question asked (S1 and S2 share one, so a slip between them in the inputs file costs nothing; S4 is refused).
`make check` green.

**Part 3c: what it builds (2026-10-21, Opus, for the Sonnet build; nothing built yet).** From the search-half doc's
step 3 item 4 and its three dated notes of this date. **First, the change to 3b that note (c) needs:** the
knowledge probe's token allowance 16,000 (its own constant, not the container probe's `PROBE_MAX_TOKENS`); a reply
with no answer text and no reasoning gets a replacement call at once, recorded beside it (`-replacement-<k>`
files with the same provenance), at most two per call, the replacement's reply standing for the call; after
three empty replies the call fails, and 3c's read counts it so with nothing to
ask him. **Then 3c:** (1) **his read**, a command on the
model of `hc case probe-verdict`'s first step: every reply that is not exactly "unknown" or that carries reasoning
is shown with its status and its reasoning (taken from `raw_response`), he answers y or n to whether it states or
guesses the decision or gives a figure of it, and the reads are saved write-once (`knowledge-reads.json`, with each
reply's sha256), so a re-run never asks again; no failure means the command prints the `hc case xlog record <id>
not_known pass` to run, a failure writes the flagged replies (`knowledge-flagged.json`) and prints the `record ...
fail` and the reader command; (2) **the reader**, `hc case reader <id> rejection --criterion not_known`, with a
new brief used for that criterion only (the three existing briefs unchanged), committed and pushed before its first
read; the reader is shown item 4's failure definition for the probed shape, the question that was asked, and the
flagged replies with their reasoning, never the dossier and never which model answered; (3) **the log**:
`rejection_reply_on_record` and `hc case xlog read` accept `not_known`, so a reader's "pass" disputes the failure
and his written resolution clears it, as for criterion 5. Nothing printed holds a name, an answer or a reasoning.
Sonnet builds at medium effort; a fresh Opus chat at high effort reviews, reading the new brief word for word.

**Part 3c built (2026-10-21, Sonnet at medium effort; Opus review pending in a fresh chat).** *(Reviewed and changed
the same day: see the review note and the decisions note below; EMPTY replies no longer reach the reader.)* From the note above
and the search-half doc's item 4 with its three dated notes. **The change to 3b (note (c)):** `knowledge.py` has its
own `MAX_TOKENS = 16_000` (it no longer takes the container probe's constant); a reply with no answer text and no
reasoning (`holds_nothing`) is replaced at once, at most twice per call, as `knowledge-probe-<model>-<n>-replacement-<k>-
request.json` / `-reply.json` (and `-error-<j>`), each carrying `replacement` in its fields; the last reply stands for
the call; a call empty three times has `CallResult.empty` and `to_read` False. The cost of a call adds its
replacements; the command prints replacements and empty-three-times calls. **His read:** `hc case knowledge-verdict
<label>` (`caseprobe/knowledge_read.py`): the standing reply of each of nine calls; an empty call fails with no read;
exactly "unknown" with no reasoning passes with no read; every other reply is shown on his terminal (question,
definition, answer, reasoning from `raw_response`) and he answers y or n, one stray word asked again up to three
times, then nothing saved; reads saved write-once in `knowledge-reads.json` with each reply's sha256 (a re-run asks
nothing; changed replies are refused); no failing call prints the `xlog record ... pass` to run; otherwise it writes
`knowledge-flagged.json` (shape, the question, the failing replies with their reasoning, empty ones marked) and
prints `xlog record ... fail`, the reader command and `xlog read`. Refused unless the row stands at `not_known`
with no result. **The reader:** `hc case reader <id> rejection --criterion not_known`; new brief
`experiment/readers/knowledge.txt`, loaded for that criterion only (`load_brief(root, kind, criterion)`; the three
existing briefs untouched); material `Definition` (item 4's failure definition for the probed shape, with note (a)'s
reasoning clause), `Question asked`, `Flagged replies` (numbered, no model named, EMPTY marked, a cut-off reply
marked); reply format as criterion 5's (shape and type null). **The log:** `rejection_reply_on_record` takes
`not_known` (it is in `READ_CRITERIA`) and `hc case xlog read` offers it, so a reader's "pass" disputes the failure
and needs his resolution, as for criterion 5. `make check` green, 2741 tests (34 new). **Before its first read** the
brief and `reader/` must be committed and pushed (the frozen-inputs check refuses otherwise). **For the reviewer:**
(1) read `knowledge.txt` word for word: does it let the reader judge "states or guesses" without being told the
decision, and is its handling of EMPTY and of a cut-off reply right? (2) an EMPTY-only failure goes to the reader
marked, who reads "pass", which disputes it and so needs his written resolution: is that the right way to let him
decide a call that returned nothing, or should an empty failure never be disputable? (3) the `Question asked`
block shows the reader the company's name and the facility (as criterion 3 and 4 excerpts already do); the reader
never sees which model answered or the dossier. (4) his terminal shows the full reasoning of a reply (up to
16,000 tokens of gpt-oss); is that readable enough? (5) `knowledge_verdict` writes `knowledge-reads.json` before
any failing set is flagged, so a crash between them is finished by a re-run.

**Part 3c reviewed (2026-10-21, a fresh Opus chat at high effort; the brief read word for word).** Two faults,
fixed: (1) a run stopped by API errors in the last call's replacement left every call with a reply, so the
verdict took the empty first reply as the call's and failed it as empty three times; `load_replies` now refuses any
request with no reply (one test). (2) The spend warning's ceiling counted nine calls, not their replacements;
it now counts both (about $0.51 before, about $1.54 now, nearly all of it Sonnet; one test). `make check` green,
2743 tests. **The five questions:** (3) the company and facility in `Question asked`: as built, the reader already
sees names in criteria 3 to 5. (4) the full reasoning on his terminal: as built; a reasoning model's reply to this
question is short in practice, and the ceiling is the allowance. (5) the write order: as built, a re-run after a
crash between the two files writes the flagged one from the saved reads. **Open, his, before the first read:**
(a) for S1 or S2 the question itself says a reduction was announced, so a reply or a reasoning that only repeats
the question "states that the reduction happened" on the definition's words; (b) a call empty three times goes to
the reader, whose brief tells it to read "pass", so every such failure is a dispute that his written resolution
decides, with nothing in the reply to decide on; (c) the brief's closing sentence names a workforce reduction for
every shape, wider than the S3 definition. Recommendations are in START HERE.

**Part 3c's three decisions, built (2026-10-21, his at about 5:00 PM, all as recommended; Opus, the review's chat).**
Item 4's dated notes (d) and (e). (a) `KNOWLEDGE_DEFINITIONS["reduction"]` carries note (d)'s words, and the brief
says that what the question itself says is not something a reply states. (b) A call empty three times fails by
rule: `hc case knowledge-verdict` ends at `failed_empty` and writes no `knowledge-flagged.json` (an empty call beside
a read failure included); the flagged file and the material no longer hold an empty reply; `hc case xlog record <id>
not_known fail --empty` logs it, refused unless his saved reads count an empty call, and a fail without `--empty`
is refused when they do; the row's `not_known` then leaves `read_required`, so it awaits no read, and both `hc case
reader` and the log refuse one. (c) The brief's closing sentence says "the decision the definition names", and its
EMPTY sentences are gone. `make check` green.

**Stage 3, step 10, closure-07's first build (2026-10-22, Opus with him; his decision to fix in this chat, no
Sonnet build or separate review, as the fixes are three patterns).** Step 2: the case's term list written in the
appendix (74 terms; tested on the eleven cached filings, nothing identifying left inside an item); six identifiers
added by him to the guard's term file. Step 3: the splitter refused the quarterly report (a table of contents with
each heading, title and page on its own line reads as body text), so Part I Item 2 was cut by hand
(`hand-boundaries.json`, checked by him). The build then ran: 13 sources, 5 extraction requests, about $0.12 of
Anthropic credit (the projection was $0.32), 21 flags. **Read in full before the flag review, the dossier had three
faults the flags do not reach, and the review file can change only flagged text, so the build is redone:** (1) a
per-share figure written "per diluted share" was not recognized, so it was scaled as dollars and not flagged
(scaled earnings over it give the real share count); `_PER_SHARE_AFTER` now takes basic, diluted, common and
ordinary. (2) A 52/53-week filer's quarter can end a day past the month-based boundary, so "the second quarter
ended <date>" was labeled the third; a year or quarter end is now placed by `FiscalCalendar.locate_period_end`
(half a quarter earlier), and a stated quarter its date contradicts is flagged. (3) "the first quarter ended
<date>" left "first" in front of the label; the stated ordinal is now part of `ENDED`, which also takes "ending".
The term list also gained two possessive forms it missed. Tests for each; `make check` green, 2768 tests. **Not
fixable by rule, noted for the checks and the probe:** the extraction's region list in section 2 double-lists two
regions (its total is right); "the a town facility" reads oddly; and section 1 carries the company's own
description of its market position, which no term list removes: the recognition probe decides it, and the
coarsening procedure (OPEN 2026-10-16) applies only if it fails. **Next:** his commit and push, the three build
outputs deleted by hand (the folder rule for starting over), the build run again (a new seed), then the flag review.

**closure-07's second build (2026-10-22, after `e5c557e`).** About $0.12, 21 flags; the three fixes hold (the
diluted figure flagged and unscaled, the second quarter's results labeled the second quarter, no stray ordinal).
**One new leak of the same kind:** this extraction wrote a prior-year per-share figure as "$19.7 million ($1.01)",
with no "per share" after it, so it was scaled. Matching phrases cannot keep up with the extraction's wording, so
the rule is now structural: a dollar figure under $100 with no unit is flagged and left unscaled (per share, or
kept by him). Tests; `make check` green. The term list's roles were also lettered (subsidiaries A and B, towns A
to M) so the text no longer reads "the a town facility". **Next:** his commit and push, the outputs deleted, a
third build, then the flag review.

**closure-07, third build to the scenario (2026-10-22).** Third build (after `7b501b6`): about $0.12, 20 flags, no
unflagged per-share figure. His flag review (Claude drafted, his reasons as worded): 13 fiscal-year flags kept (the
filer's year ends in late September, so the assumption holds), 7 per-share figures removed (§4.8 of the code half);
`hc case assemble` wrote the dossier. **Scenario (step 4):** rows for the total (the state notice filed on the
first-disclosure date, the one first-disclosure row), cash and undrawn credit (the last quarterly report before the
cut-off), and the three caps equal to the total; every other S3 figure has no source. Rendered (nine sentences
dropped; the figure-free S3 form) and `hc case scenario check` passes. **A known gap, logged before any read:** the
dropped first situation sentence was the only one introducing the plant, so the scenario never says which of the
dossier's facilities "Plant 6" is (§4.6.1's "what this costs" foresaw the loss of context). His question (does
leaving it risk the case?), answered from the code: a scenario read can only return "neutral" or "concerns", and
"concerns" means fix and re-read or his written resolution, never a rejection; naming the plant's product line and
region would instead raise the recognition risk at criterion 5, the step that can lose the case. Left as rendered;
if the reader raises it, the fix is a clarity fix with the reader's concern as its logged reason.

**closure-07, the reads (2026-10-22).** Scenario read 1 ("concerns", two figure-source concerns, about $0.02): the
rows' locators quoted the unscaled values, so the reader set the scaled total and liquidity against unscaled sources.
The material is built to show neither the unscaled values nor the factor (protocol §12.6); the locators defeated
that. Fixed in the case's rows (a locator names where a figure is, never its value), rendered again (scenario.toml
unchanged byte for byte), check passes. Read 2 ("concerns", about $0.04): the figure-free options are thin and the
sell sentence says more than the close one. Those sentences are the shared S3 case form (§4.6.5 step 0), read when
adopted, and close is short at that reader's own request; his written resolution keeps them. The Plant 6 gap above
was not raised. Rubric read 1: "agrees", five lines, none disagreeing (about $0.02). **A fault found in the
resolution:** `hc case resolve` and the lock's check took the *oldest* read of the scenario as it stands, so with
two reads of a byte-identical scenario his resolution was filed against read 1's reply, and a neutral re-read would
not have superseded an earlier "concerns". Fixed in `reader/read.py` (the newest read of the current scenario or
rubric counts), with a test that fails on the old code. The misfiled resolution is removed from the case folder and
recorded again against read 2.

**closure-07 passes criterion 5 (2026-10-22).** `case.lock` committed (`0142a0a`), the content uploaded, one probe
task per model (worst cases about $0.007 and $0.003). His read of the six answers: none names the company (one model
declined three times, saying the profile may match a real company; the other named a different company three times).
Recorded in the exploratory log (`-41`): **closure-07 finished, passed all**, the first exploratory case.

**closure-19, stage 3 to the lock (2026-10-22).** Term list drafted from the 10-K's Items 1, 2 and 7, the 10-Q's Item
2 and the current reports (some 300 terms: the company, its listed partnership, subsidiaries, acquired businesses,
brands, executives, the founding family and directors, former employers, competitors, towns, an address and a phone
number). First build (about $0.30): two names from current reports the first scan missed, a newly appointed
executive and a litigant company, unflagged; the term list gained them and a fuller sweep of the remaining
capitalized words (more brands, first names, the phone number, the street), and the outputs were deleted. Second
build (about $0.31): 27 flags, no name. His flag review (Claude drafted): 12 kept (counts, physical capacities, one
month-and-day twice on its line), 11 edited (two small dollar figures and two euro amounts the scaler leaves raw,
replaced by scaled values; the headcount split, scaled to sum to the scaled total; five month-and-day dates to their
fiscal quarter), 4 per-share figures removed. Scenario rows: the total from the 60-day public report accepted at
criterion 4 (§4.6.5 step 1 item 3), cash and undrawn credit from the last quarterly report, three caps equal to the
total; rendered and checked. **Scenario read 1** ("concerns", three, about $0.05): the figure-free option sentences,
the dropped estimates sentence, and the total's post-disclosure source. All three follow adopted rules the reader's
brief does not describe; his written resolution keeps the scenario. **Found: the scenario brief does not describe
the figure-free S3 form or the 60-day source for the total.** Open, his: whether the brief gains them before the next
case's read (a change to the instrument, logged as such). **Rubric read 1:** "agrees", five lines (about $0.03).
Foreshadowing: 12 hits, each justified (the company's earlier closures, a general labor fact, the shape's wording);
neutrality checklist passed. `hc case lock` written. Recognition risk noted before the probe: the dossier keeps the
company's own claim to be among the world's largest producers in its industry, its capacity and its antitrust suits.

**closure-19 fails probe set 1; coarsened once for set 2 (2026-10-22).** The content uploaded and one probe task per
model (worst cases about $0.008 and $0.003). His read: **6 of 6 answers name the company**, both models, three times
each. One model gave its reasons: the two segment names and their abbreviations, the company's self-description
(nearly word for word from its annual report), its product chain and its headquarters region. The segment names are
as identifying as a brand and should have been on the term list at build time; for later cases the term list takes
the segment names and any self-description. The reader's read of the failure (about $0.01): agrees, the rejection
stands. **His decision: coarsen once, as hard as the procedure allows.** The coarsening of §12.8 was not yet built
(`KNOWN-GAPS.md`, OPEN 2026-10-16, now closed): the coarsened dossier is `set-2/dossier.toml` in the case's appendix
folder, beside its record `set-2/coarsening.md` (each change, by the four rules of §12.8); the assembled
`dossier.toml` stays as set 1 was probed on. `hc case lock --probe-set 2` reads the set-2 dossier and refuses without
the record; `hc case upload` and `hc case hashes` read the dossier of the set they are given. Done by hand by Claude,
all four rules applied, and two things beyond them, **an exploratory deviation logged here:** the product lines and
the self-description generalized to "chemicals and plastics, and finished goods made partly from them" (they are
none of the rule's four kinds, but they were what the answers cited), and the company's size claims, its capacity
and its feedstock partnership dropped. The scenario and the rubric are unchanged, so no new read. Checks on the set-2
dossier: no case term, no place name, the name guard clean, and the outcome-term hits the same kinds as set 1's,
each already justified. **A second failure drops the case** (protocol §12.8).

**closure-19 passes criterion 5 on set 2 (2026-10-22).** Set 2 locked and pushed, the Deploy run green, the content
uploaded as set 2, one probe task per model (worst cases about $0.007 and $0.002). His read: **no answer names the
company**, all six "unknown". The set-1 failure's verdicts were written before set 2 (six), and the exploratory log
took one result for the criterion, after set 2: `exploratory-log-42`, **closure-19 finished, passed all**, the second
exploratory case. Found on the way: `hc case probe-verdict` and `hc case reader ... rejection` print "log it: hc case
xlog read ..." after a set-1 failure, but the log refuses a read with no failure recorded, and recording one would
end the row (nothing follows a failure); the verdict's own closing line says it right (log the failure only if set 2
fails too). **Lesson for every later case, his to adopt:** the term list takes the company's segment names and their
abbreviations, its self-description sentence and any rank or size claim at build time, since those are what set 1's
answers cited; the full coarsening stays the fallback after a failure. Two closure cases now fill closure's k = 2;
by §4.6.5 D.1 and D.3, stage 4's pool rows come next in the order, and a third closure is a case only if retool or
ai is short.

**Stage 4 step 3: pool rows pre-01 to pre-11 (2026-10-23, Opus with him).** Checked in the order of §4.6.5 D.1 by
the search half's §4.3 method (EDGAR full-text on the filer, a web search, the filing's own text), each rejection on
criteria 3 to 5 read (about 9 cents in all, every read "agrees" but pre-11's). **pre-01** (a research site, no
product: §4.6.5 step 1 item 4, the closure-04 precedent) and **pre-02** (S2, no stated operating-income fall: a
company with no product revenue) fail criterion 4. **Batch 1, pre-03 to pre-10:** pre-03 fails criterion 3 (a cut
inside a bankruptcy whose aim is the sale of substantially all assets: a forced wind-down); pre-07 and pre-08 fail
criterion 1 (press-channel hits on "plant closure" as a past-charges line item and a non-GAAP definition, stated
before the pool; the press-05 precedent); pre-04, 05, 06, 09 and 10 are S2 and fail its total (no stated
operating-income fall in the first-disclosure document or the pre-cut-off filings searched, `total-search.txt`).
**A scan of all 172 rows' text** (Item 2.05 and press releases, for retool, AI and closure wording; no record, no
cost, and the order still binds, D.4): no ai row with an AI-attributed cut and a stated count; one possible retool row
(pre-72, production moved to a recently opened plant: whether that is capacity "the company is building" is
his, when the row is reached); about ten S3 closures.

**pre-11, passed all (2026-10-23).** Criterion 4: S3 closure; the filings give no headcount, and the two public
reports each miss one rule (the company's release: a number of employees *affected*, item 4; a trade report the
same day: the same number *working* at the site, no source named, item 3). His decision (a): record the fail by the letter
and keep the rejection brief unchanged, so every S3 row of this record is read by one brief, as closure-19 was; the
reader disputed (log -97), the rejection does not stand, and the write-up labels the headcount as press-stated,
matching the company's affected count. Knowledge probe: nine replies, none "unknown", none stating or guessing the
decision (log -98). **An exploratory deviation, his decision (the closure-19 lesson applied before set 1):** the term
list (370 terms) takes, at build time, the company's self-description and rank claims, its product line
(generalized), the countries of its plants (to regions), its activist investors and lenders, and the
dossier's plant counts (to "several", in the flag review); the one coarsening of §12.8 stays in reserve. Three builds
(about $0.56): the first read in full showed a fiscal-year label the date code does not read ("FY25", a real-year
leak) and customer categories that point to the product; the second, country adjectives the term list lacked; both
fixed in the term list. Not fixable in the review file, noted: one report near a fiscal year's end is headed one quarter
late (the build's calendar takes the prior year's month and day). Flag review 33 kept, 9
edited, 5 removed. Scenario: the total scaled, liquidity from the last quarterly report, three caps equal to the
total; read 1 "concerns" (the figure-free option sentences, as closure-19's), kept by his written resolution; rubric
read "agrees" (choice close, observable; the four lines not). Foreshadowing: 17 hits, each justified. Lock committed
and pushed; recognition probe set 1: **six of six answers do not name the company** (one names a private competitor;
log -99). **pre-11 is finished, passed all; it fills a slot by D.3 only when every step 3 row is finished and retool
or ai is short.**

**Stage 4 step 3: batch 2, pool rows pre-12 to pre-72 (2026-10-24, Opus with him).** Sixty-one rows, checked as
batch 1 was, in two scripts of his (criteria 1 to 3 and the documents; then criterion 4 and the reads), and three
more for the reads that needed more. **15 fail criterion 1:** each match is a cost line, a footnote, contract wording
or a risk factor for a decision stated before the pool, or (pre-55) the same decision as an earlier row (the rule of
one decision judged once, (b)). **pre-43 fails criterion 3** (the exit of a business whose products a new law will
prohibit: compelled). **43 fail criterion 4:** 30 are S2 with no stated operating-income fall in the first-disclosure
document or the pre-cut-off filings searched (`total-search.txt`), among them pre-66 (the release names AI as a means
of the program, not the cause of the cut: S2, not S1, his call, the ai-07 precedent); 5 name more than one facility
(item 5); 3 name one facility and no source states its headcount; 4 name one facility whose only number is of jobs cut
or employees affected (item 4, his decision (a)), among them pre-72, the scan's one retool lead, on the closure list
(its production goes to a plant already open, not to capacity being built: closure by §12.1, his call); pre-24
matches no shape. **The reads:** 48 in all, about $0.97, 45 "agrees". **Three disputes, each logged with his
resolution; under protocol §12.4 none of the three rejections stands:** pre-20 and pre-25 (S3 closures failed at
criterion 4 by the letter: a headcount reported with no attribution item 3 accepts; a number of employees the closure
may affect, item 4; the pre-11 pattern, the brief unchanged) and pre-28 (criterion 3). **Found at pre-28, Claude's
fault:** the rejection rested on a statement in the same announcement but outside the excerpt the reader is given
(the whole Item 2.05). A criterion 3 rejection should rest only on what the reader is shown. pre-28 then fails
criterion 4 (S2, no total; "agrees"). **pre-69's first read was refused**, its `total-search.txt` over the length
limit: the subject term was the product's name, which matched nearly every paragraph. It was re-cut with the action's
own words, as the S2 subject rule says (no operating-income paragraph in either cut; the first cut kept beside it in
the appendix), and read after one throttled attempt that produced no reading and cost nothing: "agrees". **Knowledge
probes** (about a cent and a quarter each): **pre-20 fails**, on two gpt-oss replies (the same answer) that state a
closure of the plant was announced in an earlier year and reversed, their reasoning stating it too; his read, by the
letter of item 4 and its note on reasoning; the reader agrees. **pre-25 passes**, nine of nine. **pre-25 goes on to
stage 3** (the build and the recognition probe), as pre-11 did. **After batch 2, no retool or ai row has been found in
pre-01 to pre-72;** pre-73 to pre-172 remain.

**pre-25, stage 3 to the lock (2026-10-24, Opus with him).** Term list (about 1,100 terms) drafted from the 10-K's
Items 1, 2 and 7, the 10-Q's Part I Item 2 and the current reports with their exhibits, taking at build time, by his
pre-11 decision applied again (an exploratory deviation): the self-description and rank claims, the two segment names
(to "Polymers" and "Chemicals"), the product lines (the chemicals and polymers to lettered names; the closing site's
product and its end use generalized), the founding history, the plant countries (to regions), the competitors,
partners, lenders and advisers, and, generated, a "the" form of every name whose replacement carries an article. The
10-Q's Part I Item 2 cut by hand, as pre-11's was. **Three builds (about $1.37; the filings come to about 200,000
tokens a build):** build 1, read in full, showed the notes' exact coupons, the dividend cut's exact size, the acquired
business's description and doubled articles; build 2, the product's chemical name in the extraction's own words
(beside the generalized product, it names it) and the dividend cut written in words; each fixed in the term list.
Build 3 kept; noted, not fixable in the review file: the feedstock's short name left beside the generalized product.
Flag review 26 kept, 20 edited (ten regional headcounts left unscaled under a scaled total, three euro amounts, seven
month-and-day dates), 8 removed (per-share figures). Scenario: the total from the public report accepted at criterion
4 on the reader's dispute (the company's count of the permanent employees the closure may affect; the temporary
workers named beside them left out), liquidity from the last quarterly report, three caps equal to the total. Scenario
read 1 "concerns" (the sell option's "with its product family", the case form's fixed sentence), kept by his written
resolution. **Rubric read 1 "disagrees", Claude's fault:** every line agreed, but one line's note carried the
company's stated reason for the closure, and a rubric records actions only; the reason was removed from the note and
two excerpts, and read 2 "agrees" (choice close, observable; the four lines not). Foreshadowing: 7 hits, each
justified (the company's earlier closures and exits of other sites, the shape's wording); neutrality checklist
passed. Reads about $0.10. `hc case lock` written; next his commit and push, then the upload and probe set 1.

**pre-25 passes probe set 1 (2026-10-24).** The lock committed and pushed, the Deploy run green, the content uploaded
and one probe task per model: six of six answers do not name the company (gpt-oss "unknown" three times, recorded by
the tool; Haiku three answers, his read, each saying the text names no company and fits many). Logged
(`exploratory-log-394`): **pre-25 finished, passed all**, the second closure fill candidate beside pre-11.

**Stage 4 step 3: batch 3, pool rows pre-73 to pre-172 (2026-10-24, Opus with him). Step 3 is finished.** One hundred
rows, checked as batches 1 and 2 were, in four scripts of his. **26 fail criterion 1:** cost lines and prior-year
comparisons for closures stated before the pool (10), merger-agreement representations and loan wording (8), filings
that name no decision (3), three repeats of decisions already judged (the 2026-10-21 rule: the lower id stands, pre-25
and pre-27), and two decisions stated before the pool (a plant exit whose consultation began in February 2025, and a
company-wide cut announced to employees in a memo reported in June 2025). **2 fail criterion 2** (a filer with no
stock on a US exchange; a stock moved from its exchange to the OTC market before the decision). **pre-111 fails
criterion 3** (a cut compelled by a lender's foreclosure; "agrees"). **70 fail criterion 4:** 52 S2 with no stated
operating-income fall in the first-disclosure document or the pre-cut-off filings searched (one by hand, two CIKs);
10 name more than one facility (item 5); 3 name one facility and no source states its headcount; one names one
facility whose only number is of people the closure affects (a state WARN notice, item 4; the reader agrees, unlike
pre-11 and pre-25); one moves a research operation (the pre-01 precedent); two match no shape; and **pre-90, the
pool's only ai lead:** its Item 2.05 frames the whole plan, cuts included, as AI adoption, so S1 by rule 1 (unlike
pre-66, whose Item 2.05 named no AI; his call), and its total fails: the document states no number of roles whose
work AI takes over, and S1 is not relaxed (his decision of 2026-10-19); the reader agrees. **pre-124 passed criterion
4**, an S3 closure whose headcount the company stated in its last quarterly report before the cut-off, and **failed
the knowledge probe**: one of the three extraction-model replies stated that the closure was decided (its date wrong,
the pre-20 precedent), his read; the reader agrees. He asked whether a coarsening could let it pass: no (coarsening
works on the dossier, after the build; the knowledge probe asks about the real names before any dossier exists), and
leaving the extraction model out of the probe is a relaxation already rejected. **One dispute: pre-75**, a cut
rejected at criterion 3 as made inside a bankruptcy whose aim was the sale of its businesses. **Claude's fault, the
pre-28 lesson missed again:** the bankruptcy is named only in the filing's forward-looking statements, outside the
Item 2.05 excerpt the reader is given, and the reader read the excerpt as a plain cost cut. Logged with his
resolution, the rejection does not stand (§12.4); pre-75 then fails criterion 4 (S2, no total; "agrees"). **The
reads:** 73, about $1.15, 72 "agrees". Every result was recorded through `hc case xlog`. **After step 3, no retool or
ai row passes.** By D.6, with two cases and step 3 finished, **step 4 opens**: the same pool rules over filing dates
2024-07-01 to 2025-06-30, whose search is not yet built (`hc case search --pool` knows step 3's range only). pre-11
and pre-25 come before every step 4 row in D.1's order, so they fill two of the three short slots if retool and ai
stay short.

**Stage 4 step 4: the second pool (plan step 12), built 2026-10-25 (Sonnet, high effort); the Opus review is next, in
a fresh chat.** `hc case search --pool pre --step 4 --date <today>` (`--step 3` or `4` is now required with `--pool`;
`--step 3` is the old command): channel 1 and step 2's channel over 2024-07-01 to 2025-06-30 (`STEP4_START`,
`STEP4_END`), once, written to `pre-step4-candidates.json` (read by `candidate_records` with the others). Its ids
continue step 3's: the first number is one more than the highest `pre-NN` in the lists, read, never assumed. Every
earlier candidate's accession number is left out and `same_filer_as` is checked against every earlier list. Rows go in
the exploratory log as step `"4"`, pool `pre`, and sort after step 3's. **Step 4 opens by D.6, all checked before any
request:** step 3's file exists; no row of the log is unfinished (a rejection awaiting its read counts); `problems()`
is empty; fewer than five cases, **each type's own only**; and step 5's search is not yet recorded. `--join` is refused
for step 4 (item 6's two rows joined step 3).

**The held fill (his decision, 2026-10-25; the dated note under D.3 in the search-half doc).** `ExploratoryLog.selection()`
no longer fills a short type's slots until step 5's search is recorded: the log has a new event, `searched` (step `"5"`
only, once, refused if a step 5 row is added after it), written by `ExploratoryLog.mark_searched()`, **which step 13's
search must call and which is not built**, so the selection stays incomplete, and pre-11 and pre-25 stay pending, until
then. `ExploratorySelection` has a `pending` field (rows that passed, took no own slot, wait for the fill), shown by
`hc case xlog show` ("passed all, pending the fill") and the public view. A selection with five own cases needs no
step 5 search. The open item is in `KNOWN-GAPS.md` (2026-10-25). **Behavior that changed, for the reviewer:** every
test that asserted a fill or `complete` without a step 5 search now calls `mark_searched()` first (seven in
`test_casebuild_exploratory.py`, and the public view's), and the step 3 pool tests now pass `--step 3`.

`make check` green, 2787 tests (15 new). **Not done:** step 13 (the search of 2027-01-04 and its `mark_searched` call);
the START HERE block of 2026-10-24 said pre-11 and pre-25 fill "only if no retool or ai row passes in step 4"; rewritten
after the Opus review (2026-10-25, no code fix).
