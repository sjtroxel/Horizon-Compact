# Known gaps

Open items, newest first. **This file narrows the phase docs:** if it and an older phase doc disagree, this file
governs until the phase doc is amended. Closed items stay, marked closed with the date, so the record shows how
they closed.

**Never write a real company's name in this file, or in anything else under version control.** Refer to a real
case by its type and a neutral label. The names live only in the private longlist outside this repo.

> ## START HERE — where things stand, 2026-10-07, morning
>
> **PHASE 2.5 `scenarios-and-wordings`: IMPLEMENTATION doc WRITTEN (Opus) and APPROVED 2026-10-07 (his, all seven
> §19 decisions as recommended)**: `docs/phases/phase-2.5-scenarios-and-wordings-IMPLEMENTATION.md`. Planning
> patches applied the same day: `planning/00` §5.1 ("over the next twenty years"), `planning/07` §3.2 (employment
> cost for L1 and L2; S4's cuts under both choices). The OPEN entry on S3's community consequence is CLOSED by
> decision 5 (below). **Decision 7:** if Bedrock is still blocked at its step 16, Phase 2.5 closes on Ollama alone,
> and **the Nova Lite probes and format runs become a prerequisite of Phase 3.5's tag** (they add to the Ollama
> runs; nothing is re-run).
> **BUILD, §17 STEPS 1-3 DONE 2026-10-07 (Sonnet) AND COMMITTED: `3039526`, pushed, CI run `37640121903` green.**
> Loader and layout (`scenarios/*.toml`, `objectives.toml` with who/when and the templates `w1`-`w3`,
> `sealed_template`), the five balancing rules and four extra rules, the planner across scenarios x objectives x
> templates x repeats, records under `development/<experiment>/<sweep_id>/`, and the three refusals. **The
> placeholder is byte for byte what it was** (`tests/golden/placeholder_prompts.json`, digests taken before the
> change). Deviations and one open point for step 6 (rescaling and a pinned line) are in the doc's §17. Phase 2's
> DoD 7 row is closed with run `37534188137`.
> **STEP 4, THE OLLAMA PROVIDER, DONE 2026-10-07 (Sonnet; reviewed by Opus); `make check` green, 550 tests;
> COMMITTED: `b5ae8fb` "phase 2.5: ollama provider, prompt diagnosis" (his), pushed, CI run `37655035891` green.** Live checks first (Ollama 0.35.1; `qwen3.5:4b` digest `2a654d98e6fb...`, maximum context
> 262,144, thinking off with `"think": false`, its own sampling defaults temperature 1 / top_k 20 / top_p 0.95 /
> presence_penalty 1.5; `num_ctx` 16,384 uses 3,379 MiB, all in VRAM), then `providers/ollama.py`, the `local` route,
> `qwen-local` in `models.toml`, and a CLI path with no AWS session at all. **The placeholder sweep ran (his,
> 11:00 AM): the path works, and 0 of 5 runs ended valid** (13 `sum_mismatch`, 1 `truncated`, 1 `schema_invalid`).
> **DIAGNOSED BY OPUS (11:30 AM, placeholder variants only, $0): mostly the prompt, not the model.** At temperature 0
> both `qwen3.5:4b` and `qwen3:8b` set every line to its maximum ("up to $1,000" read as "$1,000"); one neutral
> sentence ("each maximum is a limit, not a target", with the maximums' sum against the total) made a one-sided
> table balance **4 of 4 (4B) and 2 of 2 (8B)**. The placeholder's two-sided rule is harder than any real scenario
> and still fails on the 4B. **So DoD 4 and decision 7(a) stand;** the table is in the doc's §17 step 4. **He ran
> the diagnostic himself (11:44 AM) and saw the same result, then APPROVED both of Opus's recommendations (11:45 AM):**
> the drafting rule in §6 (every menu says the maximums are limits, not targets, and states their sum), and S4's
> shape test, now §17 step 6a, before the baseline.
> **STEP 6a, 2026-10-07 afternoon: the local models cannot do S2-S4.** The S4 shape test failed (0 of 5), and four
> diagnostic rounds on garden copies found the cause: the 4B balances 3-4 lines (S1's shape 4 of 4) but not 7, the
> 8B about half of S2, the 14B does not fit the card. **Through OpenRouter (his runs): Nova Lite failed the same
> way; `gpt-oss-120b` did S1-S3 and half of S4 for half a cent; Sonnet 4.6, on garden content only, did 10 of 10.
> The format is sound; the weak models were the problem.** `gpt-oss-120b`'s S4 failures all broke the "not both"
> rule, so step 7 looks at S4's matching sentence. **DECISION 9 (his, amended 3:44 PM): `gpt-oss-120b` through
> OpenRouter for Phase 2.5's development runs, until Bedrock answers; $3 cap** (his key; about $0.24 spent today).
> **The official runs are NOT covered:** if Bedrock is still blocked at Phase 3.5's pilot, that is its own decision.
> Step 8 adds an OpenRouter provider and `models.toml` entry (Sonnet).
> **STEP 7 DONE 3:50 PM (his, accepted all on Opus's review packet, `evidence/phase-2.5/step7-review.md`):** five
> text fixes applied (two were quiet leans: S2's research line now says it includes engineering pay; S1's
> severance for salaried staff moved to the middle of its range, 1.5 weeks); T3 (S1 always describes elimination
> first) waits for step 8's per-line `detail`. 73 rows, 20 assumptions.
> **Committed and pushed: `de95e16` "phase 2.5: step 6a diagnostics, dec'n 9, step 7 rev." (CI run
> `37685407688` green; Deploy `37685407768` green).**
> **STEP 8, ITEMS 1-10, BUILT 2026-10-07 (Sonnet), UNCOMMITTED: `make check` green, 648 tests, the placeholder's golden
> test untouched.** Objectives and templates, `hc scenarios render` and `check` (in `make check`), the loader, lever-line,
> tool and per-line `detail` changes, pinned lines out of rescaling, `range_sources`, and the OpenRouter provider with
> `gpt-oss-openrouter` (price re-checked live: $0.037 / $0.17 per million). **Item 11 is his run** (garden content,
> under a cent; the doc's §17 step 8 gives the command). **Opus, 4:20 PM, on his delegation:** fixed two S1
> sentences that pointed at a path by position or by "the same" (the paths are shuffled now), and accepted Sonnet's
> change log format, with one gap for step 14 (the sealed draw moves the content hash). Detail in §17 step 8 and §14.
> **Committed and pushed: `5f02092`, CI `37688590949` green (Deploy `37688590950`). Item 11 DONE (his, 4:21 PM): the
> OpenRouter provider ran `s4shape` 5 of 5 valid, first attempts, $0.0017; no key in any record.**
> **STEP 9, THE BASELINE, DONE 2026-10-07 (Opus), for his commit: `experiment/company/CHANGELOG.toml`, baseline hash
> `caa1e5398d5c...` (the content of `5f02092`). FROM HERE, EVERY CHANGE TO WHAT A MODEL READS NEEDS A LOG ENTRY** (date,
> files, hash before and after, evidence, reason: format, clarity, neutrality or factual); `make check` fails otherwise.
> **STEP 10, PROBES, BUILT 2026-10-07 (Opus), uncommitted: forty questions (ten per scenario, keys checked by hand),
> `hc probes run` and `report`, probe files checked in `make check`; 686 tests. **Decision 9 AMENDED 4:45 PM (his):
> `gpt-oss-openrouter` for the probes and every Phase 2.5 development run from here, not the 4B.** Counts are scored
> exactly; model failures are not retried. **PROBES RUN (his, 4:55 PM): all 40 questions pass (34 at
> 5 of 5, six at 4 of 5), $0.0062; DoD 3 met.** The six misses are two replies giving money in millions, every value
> right: the answer's unit, not the text; no change, no log entry. **NEXT: commit (his); then the spend warning before
> the key prompt (his request, Sonnet); then step 11, the neutrality checklist (Opus).** Detail in §17 step 10.
> **STEP 5 COMMITTED: `490a94e` "phase 2.5: scenario rows and sources", pushed, CI run `37663609137` green (Deploy
> `37663608886` green).** **DECISION 8 DECIDED 1:11 PM (his):** S1 is a split of the 125 people into three priced
> paths (eliminated; moved at plant pay; moved keeping current pay), and the $11.4M saving is stated as the same on
> every path; `planning/07` §3.2 patched. **STEP 6 DRAFTED (Opus):** `scenarios/s1.source.toml` to `s4.source.toml`,
> review copy `docs/phases/evidence/phase-2.5/scenarios-step6-draft.md`; 72 rows, 19 assumptions (new: S3's
> transfer acceptance, 15%, at most 29 people move). Step 8 owes five code changes found by rendering (§17 step 6).
> **STEP 6a PREPARED:** `experiment/s4shape/`; he ran it (results above). *(Superseded: the NEXT SESSION line above governs.)* **Was: 6a (his run), then 7 (his review of A32-A50 and
> the four texts; look hardest at `s4_payoff_mid` and `s3_accept_share`), then 8 (Sonnet).**
> *Earlier the same day:* **STEP 5, THE SCENARIO ROWS, DONE 2026-10-07 (Opus), except S1's redeployment rows:**
> `experiment/company/scenario-figures.toml` (54 rows, 18 assumptions), six sources added to `sources.toml` with
> extracts under `docs/phases/evidence/phase-2.5/sources/`; the doc's §17 step 5 has the table. **He accepted the
> recommendations generally (12:31 PM), so these are decided:** S1's share is 25% from a public source, not 30%
> (Y $11.4M); S2's G counts only materials, parts and energy as variable ($112.1M, not $84.4M: the draft would have
> cut about 285 plant roles before the decision); S3's product family moves to the other plants if it closes;
> `planning/00` §5.2 and `planning/07` §3.2 patched. **OPEN, decision 8 (§19):** S1's table charges a kept person
> full employment cost, but the dossier's plant vacancies make keeping cost at most $2.6M a year, not $11.4M.
> **NEXT: Opus designs decision 8's option (a) and shows him; meanwhile step 6 can draft S2-S4,** then 6a (S4's shape
> test, run by him) and 7 (his review of A32-A49; look hardest at S4's payoff, `s4_payoff_mid`).
> **Bedrock at 8:51 AM CDT on 2026-10-07 (`scratch/throttle-check.py`, run once):** Nova Lite and Sonnet 4.6 both
> still `ThrottlingException`, "Too many tokens per day", $0. No AWS reply on case 179121856900232. He will not buy
> paid support (his, 2026-10-07).
>
> *Phase 2's close-out, kept as the record (2026-10-06):*
> **PHASE 2 `company-dossier` IS BUILT AND CLOSED (2026-10-06)**, committed and pushed in full (`fe82c3f`, `891ee3c`,
> `6262c82`, `4250ea3`). **DoD audit: all seven met except DoD 4, marked partial** (an acceptance by deferral). The
> manual rule-zero read found nothing; `ROADMAP.md` marks Phase 2 closed; `pyproject.toml` is unchanged (decision 4).
> The step 7 and 8 details follow.
> **STEP 8 (the realism read) DONE 2026-10-06, Opus.** `experiment/company/figures.toml` (218 rows, 31 assumptions),
> `dossier.template.txt`, the rendered `dossier.toml` and the public files under `docs/phases/evidence/phase-2/`;
> about 2,113 words (estimated 2,850 tokens). **Step 7:** DoD 4 is an acceptance by deferral (he accepted A1-A31 and
> the text on Opus's recommendations, choosing not to weigh in item by item); the environmental limit kept as
> drafted; a two-sided neutrality read changed "pressing suppliers" to "negotiating lower prices with suppliers"
> here and in `planning/07` L9, and logged S3's missing community consequence (OPEN entry below). **Step 8:**
> `openai/gpt-6-astra`, one call, $0.50 (his OpenRouter balance, outside the AWS ceiling); 13 points, each verified
> and decided (his: all as recommended); the table is in the IMPLEMENTATION doc §13 step 8. Fixed: the retraining
> cost's definition (wages excluded, value kept), A12's range and a new check on range bounds, roles not places in
> section five, compounded growth, the overlaps and annual basis in section eleven, a balancing line, prior-year
> net income built like the current year's. Two left and logged (RECORDED entry below). **Nothing scenario-facing
> moved.** **Step 9 (Sonnet):** the manual rule-zero read (nothing found), the DoD audit, `ROADMAP.md`, this block.
> Nothing in Phase 2 called Bedrock or any official model.
> **Bedrock at 2:31 PM CDT on 2026-10-06 (`scratch/throttle-check.py`, run once, not acted on):** Nova Lite and
> Sonnet 4.6 both still `ThrottlingException`, "Too many tokens per day", $0 (12:00 PM: same).
>
> **WAITING ON AWS, the full list (2026-10-06):**
> - **Bedrock quotas restored** (case 179121856900232, BLOCKED entry). Behind it: Phase 1 steps 3 and 9, then 11 and
>   12, so Phase 1's close and the first test of the task role's Bedrock and S3 permissions; Phase 1.5, which needs
>   Phase 1's sweep results in S3; Phase 2.5's Nova Lite development runs (its Ollama runs do not wait); Phase 3.5's
>   pilot and everything after it. Probably Musical Mycelium's Bedrock calls too (unchecked).
> - **Phase 0.5 close-out on billing data** (WAITING entry). Not the quota block: the data should have posted by the
>   morning of 2026-10-06, so it can run now, about 15 minutes of his console. The Sonnet 4.6 budget needs Sonnet's
>   charges to have posted.
> - **If AWS never restores the quotas,** the fallbacks are another provider's credits or a free route; none is
>   researched or decided (his decision, when it comes to that).
>
> *Everything below this line is as of 2026-10-05, 1:20 PM, and still true unless the list above says otherwise.*
>
> **PHASE 0 is complete** (2026-10-03; CI run `37160410815`). **Every scope doc, Phases 0 through 7, is approved.**
> **PHASE 0.5 `aws-foundation` is BUILT and its smoke calls are done; it is NOT closed.** Three commits on `main`, all
> pushed, CI green: `b9c9aaf` (bootstrap Terraform, identity check, the settings deny fix), `52aa3fd` (provider seam,
> smoke command), `ac2fbe0` (eight smoke records and findings). The bootstrap is applied with nothing shared created;
> the deploy role's trust is proven (run `37241137274`); Sonnet 4.6 (thinking off and on), Nova Pro, Nova Lite and
> gpt-oss-120b each made a recorded tool call. The development model is named (his): **Ollama `qwen3.5:4b` + Nova
> Lite.** The as-built record is `docs/phases/phase-0.5-aws-foundation-IMPLEMENTATION.md` §15 and §19.
>
> **What keeps it open is billing data, which AWS posts up to about a day late** (the entry just below): the tag
> measurement for decision 3, the Sonnet 4.6 budget (its Service name appears in the Budgets list only once Sonnet's
> charges post), and the phase's spend read from the bill. That close-out is about 15 minutes of his console and one
> `terraform apply`, then the DoD audit; it runs **as soon as the data posts** (evening of 2026-10-05 at the earliest),
> alongside Phase 1's build.
>
> **Phase 1's IMPLEMENTATION doc is APPROVED (his, 2026-10-04 evening):**
> `docs/phases/phase-1-walking-skeleton-IMPLEMENTATION.md`, its four decisions as recommended (ECR in `bootstrap`; keep
> the dev key through Phase 1; deploy on push for code paths; 15 runs). **BUILD STARTED 2026-10-05 (Sonnet): steps 0-2,
> 4-8 and 10 are DONE** (C1-C4 committed and pushed; first deploy green, run `37352790960`; permission check passed, run
> `37353579140`; official launch refused). **BEDROCK IS BLOCKED (entry below): steps 3 and 9 wait for AWS, and 11 and 12
> follow them** (IMPLEMENTATION doc §16, §21). No task has run yet, so the task role's Bedrock and S3 permissions are
> untested. `experiment/` (`models.toml` and the garden-club placeholder) is tracked since C1. Decision 3 enters as two
> branches (§9.3); `SONNET_ROUTE` is set to `application_profile`, matching `models.toml`, until it closes. Its build can start
> before Phase 0.5 closes; **its first Sonnet sweep cannot** (§1).
>
> **The `horizon-compact-dev` access key stays through Phase 1** (decision A, amended 2026-10-04 by Phase 1's
> decision 2); he deletes it at Phase 1's close. **Sonnet 4.6 is the main model for v1, fixed (his, 2026-10-05).** Sonnet 5.5 is no longer awaited;
> its two smoke calls will not run (the closed Sonnet 5.5 entry below).
>
> **`horizon-compact.vercel.app` is claimed** (his, 2026-10-05; entry below), so Phase 1.5's prerequisite is met.
>
> **Each session, alongside Phase 2.5:** check case 179121856900232 (restricted-list follow-up added 2026-10-06; BLOCKED
> entry). If Bedrock answers again (`scratch/throttle-check.py`), run step 3 (`scratch/step3-dev-run.sh`), then step 9.
> Phase 0.5's billing close-out (WAITING entry) can run the same day.

---

## OPEN — for Phase 4: `hc sweep launch --official` does not pass `--official` to the task, 2026-10-07

Found in Opus's review of Phase 2.5 steps 1-3. `cmd_sweep_launch` checks the protocol lock on the laptop when
`--official` is given, but the container command it builds (`sweep run ...`) has no `--official`, so the task runs
a development session. Before Phase 2.5 that only mislabeled the run; since steps 1-3, the task's plan is also
refused (the sealed template, and Sonnet 4.6 on real content). Harmless until Phase 4, since nothing official runs
before `prereg-v1`. **For Phase 4's IMPLEMENTATION doc:** forward `--official` in the launch command, with a test
that the command carries it, before the first official launch.

---

## RECORDED — dossier simplifications kept after the realism read, 2026-10-06

The Phase 2 realism read (`openai/gpt-6-astra`, IMPLEMENTATION doc §13 step 8) raised two points he chose to leave
as they are. They go to Phase 2.5's checklist and the methods page as known simplifications, not defects to fix
silently:

- **Every plant has the same revenue per employee** (plant headcount is split by revenue share). The text says
  Plant 6 is subscale, which would usually mean fewer sales per employee. Changing it moves Plant 6's loss and
  payroll, which every closure scenario uses, so it is a scenario-design question, not a dossier edit.
- **No orders, backlog or outlook.** A machinery maker's board pack would usually have them. There is no keyless
  public source (the Census M3 survey needs a key), and an outlook invites the model to forecast.

---

## CLOSED 2026-10-07 — S3 states no community consequence (was OPEN, 2026-10-06)

**Closed by the Phase 2.5 IMPLEMENTATION doc's decision 5 (his, 2026-10-07):** every S3 option states the plant's
local payroll after the option, derived from existing dossier rows, with no multiplier and no new source.

The original entry:

Found in Phase 2 step 7's two-sided neutrality read (his decision to log it, 2026-10-06). The Roundtable names
communities as a stakeholder, and objectives B and D direct the model to weigh them. `planning/07` §3 S3 (facility
closure) states every option's **workforce** outcome in numbers, but nothing about the community the plant is in,
and the dossier has no community figure (communities share L6 with environmental spending, §3.3). Checklist item 1
(`planning/07` §9) asks for consequences "for every affected group, or for none"; on a closure the local community
is an affected group, so S3 as written may fail its own checklist.

**For Phase 3, when S3's text is written:** either S3 gives the closure's local consequence a number (an assumption
with a range and reason, like the dossier's, and the same for every option: close, retool, sell), or the committed
checklist record says why no group's community consequence is stated. Not a dossier change: adding a local-economy
figure now would be designing S3 early. Step 8's realism reader may comment on it; that is input, not the decision.

---

## CLOSED — Phase 2 source checks, 2026-10-06

The four checks the Phase 2 scope doc owed (`planning/01` §7 items 1-3, and the SEC currency question). The IMPLEMENTATION
doc §2 ran them in the morning; build step 1 re-read the files themselves in the afternoon and recorded them here.
`planning/01` §2.2, §2.3, §6 and §7 are patched with dated notes. Every source and its file hash is in
`experiment/company/sources.toml`; the extracts of the rows used are under `docs/phases/evidence/phase-2/sources/`.

- **Census AIES: closed.** 2024 is the current release (full data 2026-09-03; the file was last modified 2026-09-08).
  Table `AIES31BASIC01`, U.S. by industry. NAICS 333 read from the file: revenue $473,891,483 thousand; employees
  1,046,464; annual payroll $84,347,756 thousand; fringe benefits $22,566,734 thousand; cost of materials
  $237,904,461 thousand; value added $236,158,343 thousand. **All six match the IMPLEMENTATION doc §2.** Derived:
  revenue per employee $452,850 (the doc's §5 example row said 452851; the file gives 452,850.2, so the real row says
  452850); payroll 17.8% of revenue; fringe benefits 26.8% of payroll; materials 50.2% of revenue; production workers
  64.5% of employees. **`AIES31BASIC03` holds sector-level rows only (U.S. and states, NAICS 31-33), no NAICS 333**, so
  the materials share comes from `BASIC01`, which has it. Capital spending is not in these files; it comes from
  Damodaran, so no Census API key is needed.
- **BLS OEWS: closed.** May 2025 is current (released 2026-05-15). File `nat3d_M2025_dl.xlsx` inside `oesm25in4.zip`
  (the file list calls it "National, 3-digit NAICS, cross-ownership estimates"), NAICS 333000, 535 rows. **Every
  occupation the workforce table needs is published at the 333000 level**, so none comes from the all-industries
  table (IMPLEMENTATION doc §16, second uncertainty, answered). BLS refuses HEAD requests (403) but serves the
  GET, so the edition is recorded by file name and hash. OEWS counts 1,092,170 jobs in NAICS 333000 against AIES's
  1,046,464 employees: different surveys and reference dates, so the dossier uses AIES for ratios and OEWS for pay and
  does not mix their counts.
- **Damodaran: closed.** US industry Machinery, 105 firms, in each of the eight files used (margin, capex, divfund,
  divfcfe, dbtfund, debtdetails, wcdata, taxrate). **The margin row matches the doc's §2 to the digit** (pre-tax
  unadjusted operating margin 15.86%, net 10.58%, R&D 2.03%, SG&A 19.65%, EBITDA 19.62%, gross 37.47%). **The files'
  own "date updated" cell reads 2026-01-05; the 2026-01-09 date is his post announcing the update** ("Data Update 1 for
  2026", header date Friday, January 9, 2026, read live). Both are recorded; `sources.toml` uses 2026-01-09 as the
  release and names the 01-05 cell. His public-domain statement was re-read live and is quoted in `planning/01` §6.
  **His `Employee` file is not used:** its Machinery row says revenue per employee is $34 thousand against AIES's
  $453 thousand, because its market-cap and revenue columns cover a different set of firms than its employee column
  (a market cap of $49 billion there against $605 billion in `divfund`). Only the AIES ratio is used.
- **SEC Financial Statement Data Sets: closed, moot here.** Current: the 2026 Q2 quarterly set exists (last modified
  2026-08-19) and Q3 does not yet; the 2026-10-02 worry (releases only through 2023) was wrong. Not used for the
  fictional company (scope decision 3); recorded for Phase 5.
- **Reading the downloads.** Each download went in its own new folder, read with `python -I`; the `.xlsx` files with the
  standard library, the legacy `.xls` files with `xlrd` run from a throwaway `uv --no-project --with xlrd` environment
  (not a project dependency). The extract script is `scratch/phase2-extract-sources.py` (gitignored); to add a row
  or an occupation later, add it to the script's lists and re-run it on a fresh download. **Damodaran's values are
  written to 8 significant digits** in the extracts: the `.xls` cells carry binary-float noise
  (6927.635999999998), and a 12-digit fraction trips `tests/test_architecture.py`'s account-id pattern; the test was
  left as it is.

---

## BLOCKED — every Bedrock call throttled, quotas reset to 0, 2026-10-05

**What happened.** On 2026-10-05 every Bedrock call on the account returns `ThrottlingException`, HTTP 429, "Too many
tokens per day, please wait before trying again": Nova Lite (the step 3 development run, 28 attempts, $0) and Sonnet 4.6
(smoke call 10, recorded as `10-sonnet46-stop-details.json`, an `api_error`). Service Quotas shows **0 applied** for
Sonnet 4.6 cross-region requests and tokens per minute and for Nova Lite, including Nova Lite's tokens per day; on
2026-10-03 Sonnet 4.6 read 10 requests a minute applied. Every call worked on 2026-10-04 (22:54-23:02 UTC).

**Likely cause, unconfirmed by AWS.** AWS answered the Sonnet 5.5 Global case at 05:31 UTC on 2026-10-05 after
"reaching out to the service team" (new models need several billing cycles of usage and spend). The quotas went to 0
between that review and the morning. The same message on new or low-spend accounts is widely reported, and the
reported fix is a support case asking AWS to restore the default quotas. **It is account-wide**, so Musical Mycelium's
Bedrock calls (Haiku 4.5, Nova Pro) are probably failing too; unchecked.

**Action taken.** Account-and-billing case **179121856900232**, opened 2026-10-05 11:42 CDT (Service Quotas, General;
web), asking for the default quotas back and naming the two request ids. Nothing is spent to qualify (no cash; credits
only).

**Follow-up added 2026-10-06 08:04 CDT (his).** The restricted-list argument below, with fresh request ids: one call each
at 13:03 UTC, both `ThrottlingException`, $0. Service Quotas read the same morning: Sonnet 4.6 and Nova Lite rate
quotas still 0 applied; several Nova Lite ones are "Not adjustable", so the case is the only route. Case still
Unassigned. One-call check: `scratch/throttle-check.py` (gitignored).

**AWS's own answer contradicts the block (read again 2026-10-05 13:18 CDT).** The Sonnet 5.5 case's reply lists the models
that need "a consistent usage and spend history ... for few billing cycle": Opus 4.7 and 4.8, Fable 5, Sonnet 5 and 5.5,
Haiku 4.5, Mythos 5, Grok 4.3, GPT 5.4 and 5.5. **Sonnet 4.6 and Nova Lite are not on it**, and the reply says "the other
models should have their default quota available." Both read 0 and are throttled. That is the argument for case
179121856900232; he adds it to the case in his own words. Haiku 4.5 is on the list, so Musical Mycelium's Haiku calls are
probably restricted too (unchecked).

**US West (Oregon), read 2026-10-05 13:15 CDT (console, free, no call):** every rate quota reads **0 applied** against a
non-zero default, the same as us-east-1: Sonnet 4.6 cross-region and global cross-region requests and tokens per minute;
Nova Lite cross-region requests and tokens per minute and max tokens per day. Batch-job limits read their defaults.
**Inconclusive:** us-east-1 also read 0 applied on the morning of 2026-10-05 while the 2026-10-04 calls had worked (Phase 1
IMPLEMENTATION doc §21, step 0), so an applied 0 is not proof of a block. Only a call in Oregon would tell, and moving
regions to get around a limit while the case is open is **not** being done (his decision, 2026-10-05). The case is the
path.

**What it blocks.** Phase 1 steps 3 (the development run) and 9 (the skeleton sweep), and Phase 0.5's tag measurement
only if it needs a new call (it does not: it reads the 2026-10-04 bill). **What it does not block:** steps 4-8 (container,
`bootstrap` additions, `main`, deploy, permission check), which call no model.

**If AWS says no** (discussed 2026-10-05, nothing decided): ask again or escalate; another region; a free local open
model (Ollama `qwen3.5:4b`) as the subject, a smaller but real version of the experiment; another cloud's new-account
credits, if they cover the models (unverified). Each is his decision.

**The harness change it caused** (IMPLEMENTATION doc §21, item 10): a daily-quota throttle now stops the session at once
(`quota_exhausted`), and ten `api_error`s in a row stop it (`api_errors`), instead of retrying silently until the
30-minute clock ends.

---

## WAITING — Phase 0.5 close-out, on billing data, 2026-10-04

The smoke calls ran 17:54-18:01 CDT on 2026-10-04; `Project` was activated as a cost allocation tag at 17:19 CDT.
Cost Explorer and Budgets post usage up to about a day late, so these wait until **the evening of 2026-10-05 at the
earliest; the morning of 2026-10-06 is safer.** All reads are in the console (free; the Cost Explorer API charges).

1. **The tag measurement (decision 3).** Cost Explorer, 2026-10-04, daily, credits excluded (Charge type: exclude
   Credit), filter Tag `Project` = `horizon-compact`, group by Service, then by Usage type. **(c) holds only if both a
   Sonnet 4.6 row and a Nova Pro row appear under the tag**, from smoke calls 1, 2 and 4. A day with no rows waits one
   more day; if still none, try the page's **Backfill tags** before calling it a no. Then he decides (c) or (a).
2. **The Sonnet-line budget (DoD 3).** Budgets console, Create budget, Customize, Cost, Budget scope, filter
   Service: copy the exact Sonnet 4.6 string (Haiku's reads `Claude Haiku 4.5 ( Bedrock Edition)`, with that space).
   Abandon the form. Add `sonnet_service_name = "<string>"` to the untracked `terraform.tfvars`; plan (Claude reads
   it: one budget, CUSTOM period, $80, ACTUAL at 40/60/75, credits excluded), apply, plan again for "No changes". If
   (c) was taken, the tag budget is added in the same apply. **If the apply refuses `CUSTOM`**, the fallback is
   `ANNUALLY` from 2026-10-01 (§6 of the IMPLEMENTATION doc).
3. **The phase's spend (DoD 8).** Cost Explorer, 2026-10-04 to the day of the read, credits excluded, grouped by usage
   type, every line this phase touched (Sonnet 4.6, Nova Pro, Nova Lite, gpt-oss, S3). Estimates sum to $0.019;
   must be under $1. Also whether the errored Nova Pro call (record 05) was charged.
4. Then: the DoD audit (§16, provisional table in §20), version 0.0.5, `ROADMAP.md`. The dev access key is **not**
   deleted here; it is kept through Phase 1 (decision A, amended).

---

## CARRIED — from Phase 0.5 to Phase 1, 2026-10-04

Found by the smoke calls (`docs/phases/phase-0.5-aws-foundation-IMPLEMENTATION.md` §19); each lands in Phase 1's
IMPLEMENTATION doc.
- **`ModelErrorException` is `malformed_tool_use`, a model outcome**, not `api_error` (`planning/07` §5.1, patched
  2026-10-04). The classifier and its tests must say so, with the error's HTTP status and request ID recorded.
- **Text beside one tool call is not `no_tool_call`** (`planning/07` §5.1, patched). Nova's `<thinking>` text tag is
  visible text, not a thinking setting.
- **Thinking tokens are inside `outputTokens`** (`planning/07` §7.3, patched); Phase 4's sub-study reads them that way.
- **The refusal `stop_details` question** (refusals entry below) is still unchecked; it needs
  `additionalModelResponseFieldPaths`, which is Phase 1's request shape.
- **The tool-use input overhead** (a few hundred tokens per call, `planning/03` §3.1 patched) belongs in Phase 1's
  price-and-cap arithmetic, and whether the cache point covers it is checked there.
- **The deploy role gets its permissions in Phase 1**, with a permissions boundary; the identity workflow is the
  pattern for its first run.
- **Model routes:** both the tagged application profile and the `us.` geo profile behave identically for Sonnet 4.6;
  which one the task role is granted is decision 3's outcome.

---

## REMINDER — hosting before the credits expire, set 2026-10-04 (Phase 7 decision 5)

**Act by 2027-06-30.** The AWS credits expire **2027-07-30** (`planning/03` §1); after that, anything AWS still
bills is charged in cash, and the project's budget rule is that it never is. From launch, the idle monthly bill is
measured. By 2027-06-30, either the static site moves to a free static host and the published record stays in the
public repo, with AWS hosting torn down and the raw results archived where they cost nothing; or he decides, before
the date, to keep AWS hosting on a stated cash budget. Free hosts and their terms are checked live at the time.
Musical Mycelium shares the same credits and the same date. **Owner:** Phase 7 records the plan; he decides.

---

## FINDING — Nova Pro's billing line is shared with Musical Mycelium, 2026-10-04

Found while scoping Phase 0.5, by reading Musical Mycelium's code (read-only). It uses `amazon.nova-pro-v1:0` as
its **eval judge** (its `DEFAULT_JUDGE_MODEL_ID`; judge result files from 2026-08-20 to 2026-09-10), and Haiku 4.5
for its agent. `planning/04` §3.3 and `planning/02` §2.12 assumed Musical Mycelium spends only on Haiku 4.5, so a
budget filtered to Sonnet 4.6 and Nova Pro would measure Horizon Compact alone. **For Nova Pro it would not.** The
error is small (one 30-item judge run was estimated at about $0.10 in Musical Mycelium's own records) but not zero.

**What this check is not:** it read code, not the bill. A grep of one repo's source is not proof of what was billed.
The billing check (Cost Explorer by usage type) is in Phase 0.5's checks.

**What it changes:** how this project's budgets treat Nova Pro is Phase 0.5 decision 3. It also narrows
`planning/09` A1: the development model can be neither Haiku 4.5 nor Nova Pro. `planning/04` §3.3 gets a dated
patch once decision 3 is made.

**Also found while scoping, recorded in the scope doc:** this repo's OIDC subject claim is the immutable form
(GitHub API, 2026-10-04); Ollama is installed on the Windows side, and whether WSL can reach it is still unchecked.

---

## FINDING — the first commit went public before the name guard, and it is clean, 2026-10-03

`f214280` ("first commit new project", 15:56 CDT) holds `.gitignore` and the 12 files of `docs/planning/` (13
files in all; `docs/planning/README.md` was not in it, and was added later in `4405412`), and was pushed to
`github.com/sjtroxel/Horizon-Compact` (public, confirmed through the GitHub API). `planning/09` §7
put the guard in the first commit, before anything was copied in. That order was not followed.

**The push was his, deliberate.** Another session scanned the same 12 planning files against the longlist
**before** he committed and found nothing (his account, 2026-10-03; that scan's method is not recorded here).

**Checked again the same afternoon, after the push:** every company name, ticker and plant location on the private
longlist was searched for, whole-word and ignoring case, across every file in `f214280` and in its message.
**No reference to any case or candidate.** One longlist term matches 9 times, each one inside a cloud product
name the project uses. No path under `methods-appendix/` is tracked.

**What this check is not:** it was a one-off search over a term list typed by hand from the longlist, run before
the guard or its term file existed. **It is not the guard.** Phase 0 DoD 2 has the guard scan the full history,
`f214280` included, once it is installed. That scan is the check that counts.

**CLOSED 2026-10-03, by the guard itself.** After C1 (`9c382b8`), `make guard-history` scanned both commits with
the real term file (61 terms, 11 allowed phrases, fingerprint matching): **"history clean, 2 commit(s)
scanned."** `f214280` is confirmed clean by the check that counts.

**What it changes:** the scope doc's "first commit" becomes "the guard commit," and the planning commit becomes
a scan of the history that already exists. No rewrite of history is needed or recommended. Rewriting a public
commit that holds nothing private would add risk and protect nothing.

---

## CLOSED — the private longlist is prose, not a term list, 2026-10-03

**Closed the same day by Phase 0 decisions 1-4 (his):** a separate private term file with a longlist
fingerprint, whole-word case-sensitive matching with per-term flags and allowed phrases, and names, tickers and
plant locations all counted. Built and live; the record below is kept as the finding that led there.

Found while scoping Phase 0's name hook. The longlist was written for a person: candidates appear in table cells,
in comma-separated lists inside sentences, with tickers, plant locations and SIC codes beside them. Three
consequences:

1. **A hook that pulls names out of the longlist automatically will miss some.** Any parser of free-form prose
   has gaps, and a gap here is silent. Missing a name is the costly error.
2. **Using every word as written would over-block.** Measured on 2026-10-03: one longlist term already matches
   **9 places in the planning docs**, none of them a reference to a case. Several other longlist names are also
   ordinary English words or short tickers, and would match common words in this project's prose.
3. **Plant locations are as identifying as company names** for a single-plant closure, and the longlist holds
   them. Whether the hook blocks them is a policy decision, not a mechanical one.

**What follows:** the hook needs an explicit term list, kept private next to the longlist, with a stated
matching rule, and a way to notice when the longlist changes and the term list does not. Options and a
recommendation are in the Phase 0 scope doc. **His decision.**

---

## OPEN — Phase 0.5 checks, from `planning/09` §5, 2026-10-03

`planning/09` calls these the Phase 0 checks; they moved to Phase 0.5 with the AWS half (2026-10-03, his).
Each is Claude's, using live sources only. None blocks Phase 0.

| Check | Source |
|---|---|
| ~~Ollama's install location and whether WSL can reach it (7 GB RAM visible in WSL)~~ **CLOSED 2026-10-04**, below | `planning/00` §9.7, `planning/04` §6.3 |
| Whether AWS Budgets can filter on this project's per-model billing lines; whether added budgets cost money; whether application inference profiles could tag spend **PARTLY CLOSED 2026-10-04**, below; the tag half waits for a measurement. *Update 2026-10-04 evening:* the tagged profiles exist, `Project` is active (17:19 CDT), and calls 1, 2 and 4 went through them; the reading waits for billing data (WAITING entry above). Found: the Budgets Service list offers only services already billed | `planning/04` §3.3 |
| ~~Converse: one tool with `auto` choice on Sonnet 4.6; how thinking settings are passed and recorded~~ **CLOSED 2026-10-04** by smoke calls 1, 3 and 4 (IMPLEMENTATION doc §19; `planning/07` §14.1 and §7.3 patched) | `planning/07` §14.1 |
| ~~Nova Pro: default temperature, availability, knowledge cutoff~~ **CLOSED 2026-10-04**: the documented values below, and availability by smoke calls 2 and 5.2 (one `ModelErrorException` in three calls, recorded) | `planning/07` §14.2, `planning/01` §7.5 |
| ~~Claude's default temperature value, for the methods page~~ **CLOSED 2026-10-04**, below | `planning/07` §14.3 |
| ~~How a refusal comes back through Converse on Sonnet 4.6~~ **CLOSED 2026-10-04 as documented, not observed**, below | `planning/07` §14.4 |
| ~~Which Bedrock billing lines Musical Mycelium already spends on, before the development model is named (`planning/09` A1)~~ **CLOSED 2026-10-04**, below | `planning/09` A1 |

**CLOSED 2026-10-04 — Musical Mycelium's billing lines.** Read by him in the Cost Explorer console (free; the API
charges per request), 2026-07-01 to 2026-10-04, monthly, credits excluded so the figures are gross:
- **Grouped by service:** "Claude Haiku 4.5 (Bedrock Edition)" $23.68 (Aug $6.05, Sep $17.63); "Bedrock" $0.30
  (Aug $0.22, Sep $0.08); everything else a few cents. **No Sonnet 4.6 row and no other Claude row**, so a budget
  on Sonnet 4.6's line measures this project alone, as `planning/04` §3.3 assumed. Holds for this window only.
- **"Bedrock" grouped by usage type:** `USE1-NovaPro-input-tokens` $0.27, `USE1-NovaPro-output-tokens` $0.03,
  `USE1-NovaMicro-input-tokens` and `-output-tokens` under $0.01 (August only). **Nova Pro is confirmed on the bill**
  (pre-check 1 read it from code). **Nova Micro is new:** the code read did not find it.
- **What it changes:** the A1 development model can be none of Haiku 4.5, Nova Pro or Nova Micro if it is to sit on
  a line of its own. Ollama (`qwen3.5:4b`, Ollama check above) is now a reachable alternative. Decision 3 is
  unchanged: Nova Pro's line is shared, as found.
- **Not taken from this view:** the exact service names for Terraform's budget filters. The console table appears to
  abbreviate them ("Bedrock", "( Bedrock Edition)"); the IMPLEMENTATION doc takes them from the filter's own value
  list.

**CLOSED 2026-10-04 — Ollama.** Measured from WSL by Claude, no AWS call:
- **Reachable.** `http://localhost:11434/api/version` answers from WSL (Ollama 0.35.1, Windows side). No
  `.wslconfig` exists; whatever WSL networking mode makes `localhost` work is the default here, so a WSL update that
  changes it would break this.
- **Fits in 6 GB of VRAM:** `qwen3.5:4b` (Q4_K_M, 3.4 GB on disk), already installed. `qwen3:8b` does not fit
  whole: loaded, it took 6.0 GB with 4.2 GB on the GPU (RTX 4050 Laptop, 6141 MiB), spilled to CPU, and ran 30-60 s
  a call against 6-16 s for `qwen3.5:4b`. `qwen3:14b` was not tried.
- **One tool under `auto`:** Ollama's chat API has no tool-choice setting; the model may answer in text, which is
  the `auto` case. On a throwaway two-option prompt with one tool, both models made exactly one valid call in 5 of
  5 runs. **Five runs on a trivial prompt is enough for format and retry-path testing, which is all `planning/04`
  §6.3 asks of a local model, and is not evidence about longer prompts.**

**PARTLY CLOSED 2026-10-04 — Budgets and application inference profiles.** AWS documentation, read live by Claude;
nothing measured on the account yet.
- **Added budgets cost nothing.** AWS Budgets pricing page: monitoring and notifications are free; only
  action-enabled budgets past the first two ($0.10 a day each) and delivered reports ($0.01 each) cost money. This
  project's budgets are notification-only. **Closed.**
- **Budgets can filter on both billing lines, as documented.** The Sonnet 4.6 model card: it is "offered and billed
  through AWS Marketplace", and its charges appear "under the model provider (not under Amazon Bedrock)"; Budgets'
  Service filter, with Billing entity, "can filter costs by specific AWS Marketplace purchases". Nova Pro is billed
  under Amazon Bedrock and is separated by the Usage type filter. **Documented, not observed:** the exact Service
  name and usage-type strings are read from Cost Explorer in the Musical Mycelium billing check.
- **Application inference profiles: supported for both models, at no extra cost, as documented.** A profile can wrap
  a cross-region profile (`us.anthropic.claude-sonnet-4-6`, which `planning/02` already uses: Sonnet 4.6 has no
  in-region endpoint in any US region) or an in-region model (Nova Pro is in-region in us-east-1, and has no global
  profile). Bedrock's docs: the price is the model's price; tags must be activated as cost allocation tags
  (`user:` prefix in Budgets), and secondary sources put the lag at 24-48 hours.
- **OPEN, the one that decides decision 3: whether a profile's tag lands on Marketplace-billed Claude charges.**
  Bedrock's docs say tags track on-demand invocation costs and do not distinguish Marketplace-billed models; no
  source found, AWS or other (Feb, Apr and Aug 2026 articles read), shows it either way. **It closes only by
  measurement:** the Sonnet 4.6 smoke call made through a tagged profile, the tag activated, then Cost Explorer
  filtered by the tag 24-48 hours later. Until then decision 3's second condition is unmet, and the procedure's
  fallback is (a).

**PARTLY CLOSED 2026-10-04 — Nova Pro.** AWS documentation, read live by Claude:
- **Default temperature 0.7** (valid range 0.00001 to 1), with `topP` 0.9 and `topK` unused by default (Amazon Nova
  user guide, "Complete request schema"). Under decision 7 Nova Pro runs at this default; the value goes into the
  pre-registration and the methods page.
- **Knowledge cutoff Oct 2024; lifecycle Active**, EOL "no sooner than" December 2025 (the card says both Dec 4 and Dec 5), which has passed without a date
  being set (Bedrock model card). In-region in us-east-1, with a `us.` geo profile and no global one.
- **Open until its smoke call:** that it is enabled and answers on this account.
- **Conflicts with `planning/07` §2.1** *(patched 2026-10-04, his approval; was "not yet patched")*: that table said Nova Pro has no thinking. The Nova guide
  documents a `reasoningConfig` for "Amazon Nova Pro and Amazon Nova Lite only", **disabled by default**. Leaving it
  unset keeps it off, so runs are unaffected; the table's cell was wrong. Patch made (below).

**CLOSED 2026-10-04 — Claude's default temperature: 1.0.** Bedrock's Anthropic request page: default 1, range 0 to
1. Anthropic's API reference now marks `temperature` deprecated: "Models released after Claude Opus 4.6 do not
support setting temperature. A value of 1.0 will be accepted for backwards compatibility." Either way the default is
1.0, and `planning/07` §2.3 never sets it, so runs are unaffected.
- **Conflicts with `planning/07` §2.1** *(patched 2026-10-04, his approval; was "not yet patched")*: that table said temperature is "allowed with thinking off"
  on Sonnet 4.6. Sonnet 4.6 launched 2026-02-17, Opus 4.6 on 2026-02-05 (Bedrock model cards), so Anthropic's
  sentence, read literally, covers Sonnet 4.6 too. Whether it does is **unverified**; it does not matter while the
  harness never sets temperature, and the Sonnet 4.6 smoke call does not need to settle it.

**CLOSED 2026-10-04 — refusals through Converse, as documented, not observed** (a refusal is not provoked, by
design):
- **Converse has no `refusal` stop reason.** Its valid values (Converse API reference): `end_turn`, `tool_use`,
  `max_tokens`, `stop_sequence`, `guardrail_intervened`, `content_filtered`, `malformed_model_output`,
  `malformed_tool_use`, `model_context_window_exceeded`.
- **Claude's own response does have one.** Bedrock's Anthropic response page (InvokeModel): `stop_reason: "refusal"`,
  with an optional `stop_details` (category, explanation) that "may be null even on a refusal", and possibly partial
  content.
- **How the one becomes the other, on Converse:** one third-party report (a GitHub issue, 2026-09-24, on Claude Fable
  5.1, citing no AWS source) says Converse returns `content_filtered`. **No AWS source states the mapping, and nothing
  shows it for Sonnet 4.6.**
- **What it means for `planning/07` §5's classifier:** "the API's refusal stop reason" is, on Converse,
  **`content_filtered`, provisionally**. `guardrail_intervened` cannot occur, since no guardrail is configured. The
  written rule for an explicit decline in text still applies alongside it. Any stop reason the harness does not
  expect is already recorded as a failure, not dropped (`planning/07` §5), so a wrong guess shows up as a failure
  rather than vanishing. Whether `additionalModelResponseFieldPaths` can also return `/stop_details` is unchecked,
  and left to the IMPLEMENTATION doc.

**MADE 2026-10-04 (his approval): the four `planning/07` patches below,** dated in `planning/07`'s status line.
*Were proposed as:* §2.1's Nova Pro thinking cell ("none" becomes "a
reasoning setting exists, off by default; never set"); §2.1's Sonnet 4.6 temperature cell (adds "possibly rejected
for non-1.0 values; never set, so moot"); §5's refusal row (names `content_filtered` as the Converse form,
provisionally); §14 items 2-4 marked closed with a pointer here.

---

## OPEN — owed by him, 2026-10-03

- ~~**Create the empty public GitHub repo `Horizon-Compact`**~~ **Done 2026-10-03**, with `f214280` pushed to it.
- ~~**The one-line disclosure in `docs/planning/README.md`**~~ **Done 2026-10-03**, his words, in `4405412`.
- ~~**Commit the private term file in job-search-headquarters**~~ **Done 2026-10-03** (`ca8f316`).
- ~~**Claim `horizon-compact.vercel.app`**~~ **Done 2026-10-05 (his)**, as a placeholder (`planning/09` §7 step 7): Vercel
  project `horizon-compact`, deployed with the CLI from a folder outside this repo (not linked to GitHub, so pushes do
  not deploy it). The page holds only the name and `noindex`. The production URL answers 200 to the public; Deployment
  Protection covers only the generated deployment URLs. Phase 1.5 replaces it with the rewrite to CloudFront.

---

## CLOSED 2026-10-05 — Sonnet 5.5 access (was WAITING, 2026-10-03)

**Decided 2026-10-05 (his)**: **Sonnet 4.6 is the main model for v1, fixed. Sonnet 5.5 is no longer awaited.** AWS answered
the Global quota case on 2026-10-05: the newest models, Sonnet 5.5 among them, are held until an account has
several billing cycles of Bedrock usage and spend, with automatic re-evaluation or a new request after the next
cycle. The US case (179097554500679) asked for the same model; AWS closed it on 2026-10-06 as a duplicate of
179097558200946 (taken to be the Global case). Case 179121856900232, the quota restore, is separate. The
main-model slot is closed, no phase plans around Sonnet 5.5, and nothing is spent to qualify for it. If access
ever arrives, using it is a new decision of his, not something the plan assumes. Patched the same day:
`planning/02`, `03`, `04`, `05`, `07` and `09` (status lines), `ROADMAP.md` §2, §4 and §5, and the scope docs for
Phases 0.5, 1, 1.5, 2, 2.5, 3.5, 4 and 7. The Phase 0.5 smoke code keeps its two inert Sonnet 5.5 entries
(built and tested; never run).

*The entry as it stood before closing:*

Quota requests open (US: AWS Support case 179097554500679; Global: pending). If access arrives **before** the
`prereg-v1` tag, the main-model choice reopens as his decision. After the tag, Sonnet 5.5 is its own sweep
(`planning/05` §5.2).

**Room left for it, 2026-10-04 (his):** the scope docs treat the main model as a slot (Phase 1, "The main model is
a slot"; `ROADMAP.md` §2). Phase 0.5 smoke-tests Sonnet 5.5 if access has arrived, which gives the measured facts
for the decision. Every later scope doc says which of its lines would change if 5.5 became the main model.

---

## RECORDED — later-phase checks, so they are not lost, 2026-10-03

From `planning/09` §5. Not Phase 0's.

- A newer non-Anthropic model than Nova Pro on the account: before the Phase 3 model set is fixed.
- Census AIES and BLS tables; Damodaran's terms of use; whether the SEC Financial Statement Data Sets are
  current: Phase 2, before the dossier.
- Bootstrap, Newcombe intervals and the power rule implemented and tested on synthetic data: Phase 3.
- Measured tokens and cost replacing every estimate in `planning/03`: Phase 4.
- Each real-case candidate's first-disclosure date, public status and recognition: Phase 5.
- Bedrock fine-tuning and custom-model serving costs: before any fine-tuning phase, after v1.
