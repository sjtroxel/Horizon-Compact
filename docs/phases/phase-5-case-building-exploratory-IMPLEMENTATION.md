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
| **1. The code** | 1-6 | the exploratory log and its command, the S3 case form, the brief, the new channel | Sonnet builds, Opus reviews; his commit | no | not started |
| **2. Step 2's rows** | 7-9 | the ten pre-registered S3 rows re-read; the new channel run and checked; a count | Opus with him | a few cents (rejection reads) | not started |
| **3. Each passing row to a case** | 10 | build, scenario, rubric, lock, probe, as every case | Opus with him | yes, about 10 cents a read: **the one top-up comes due here** | not started |
| **4. The reserve** | 11-13 | the pre-cut-off pool and the knowledge probe; the pool extended; a second search on 2027-01-04 | as stage 1, then 2 and 3 | cents | **opens only if needed** (§4.6.5 D.6) |
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
5. **The brief and the reader's material** (step 1 item 7): the four changes to `experiment/readers/rejection.txt`;
   `reader/material.py` sends, with an S3 total rejection, the public report saved as `total-report.txt` (the report's
   text under a line naming its source and date, saved by rule before the result is recorded, as `total-search.txt`
   is). **Tests:** the brief's text; the material with and without a report. Logged in the search-half doc's §11 as a
   change to the instrument.
6. **The new channel** (step 2 item 2): its ten phrases as data, each its own query (`Query(4, ...)`, `items` 7.01 or
   8.01, `sics` 2000-3999); `hc case search --channel press`, run once, writing `search/press-candidates.json`
   (write-once; ids `press-01` on, `press-f01` on for the fallback month), leaving out any filing already a
   candidate; rows typed at criterion 4. **Tests** on fake replies, as for the search.

**His, to close stage 1:** `make check`, then one commit (`phase 5: exploratory record, S3 case form, press
channel`) and a push. The reader's inputs change, so they are pushed before the next read.

### Stage 2: step 2's rows (Opus with him; reads cost a few cents)

7. **Carry the ten rows** (`hc case xlog carry` for closure-04, 05, 07, 09, 16, 19, 24, 27, 29 and f01) and record each
   one's criterion 4 under step 1. Where the filings give no headcount at the facility, the public-report search
   comes first (a WARN notice for a site in the United States, the company's later releases, news reports that
   attribute the number to the company, a union or a government office; dated up to 60 days after first disclosure),
   and the report is saved in the case's private folder before the result is recorded. A rejection goes to the reader
   (1 to 3 cents a read).
8. **Run the channel** (his one command, `hc case search --channel press`) and take its rows through criteria 1 to 4
   in order, by the search half's §4.3 and Stage D methods.
9. **Count the rows that pass criterion 4.** Five or more: stage 4 stays closed. Fewer: decision 2.

### Stage 3: each passing row to a case (as many sessions as it takes)

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
