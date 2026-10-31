# Phase 5.5 — Case Runs: IMPLEMENTATION (v0.5.5)

> **IMPLEMENTATION doc. APPROVED 2026-10-27, about 11:45 AM (his): decisions 1-3 in §8 as recommended, (a);
> decision 4 (d), an option added on his question (he preferred a model to make the reads). Patched 2026-10-27 after
> K1's review (his decisions): `hc sweep status --case` goes into K3 (§5.3), and §6.2 runs one sweep at a time per
> model (its dated note). Patched 2026-10-28 after K4's review (his decision): a ticker on SEC's list counts only
> where the text marks it as a ticker (§5.4's dated note).** Written the day
> Phase 5 closed (`5f794ee`), immediately before this phase is built. Sources: the Phase 5.5 scope doc
> (`docs/phases/phase-5.5-case-runs.md`), the Phase 4 runs-half IMPLEMENTATION doc (its runbook is this one's model),
> the search-half doc §4.6.5 and §4.7-4.11, the exploratory doc §3.1 and §9, protocol sections 12, 13.2 and 14,
> `docs/phases/evidence/phase-5/freeze.json` and `cost.md`, `KNOWN-GAPS.md`'s START HERE and its four CARRIED entries
> for Phase 5.5, and the code at `5f794ee` (`protocol/cases.py`, `caseprobe/run.py`, `caseprobe/layout.py`,
> `experiment.py`, `sweep/plan.py`, `sweep/runner.py`, `sweep/prompt.py`, `analysis/records.py`,
> `analysis/matcher.py`, `cli.py`, `.pre-commit-config.yaml`).
>
> **What this doc is.** As the scope doc says, mostly a runbook. Unlike the scope doc, it finds that the case path
> is not built yet. The gate's case checks exist and are proven, but nothing runs a case: no session reads a case's
> content, and no command matches it (§3). So five run-code items come first (§5). **Nothing frozen changes.** The
> matcher, the records reader, the experiment loader and the instrument are used as tagged, and `hc protocol check`
> proves it on every commit.
>
> **Rule zero governs every line.** No company, candidate or identifier appears in this doc, in any file this phase
> commits, or in anything typed into GitHub. Cases are named by their neutral labels only.

## 0. The dated note for exploratory cases (closes CARRIED 2026-10-18 when this doc is approved)

The scope doc was written on 2026-10-04 for cases selected by the pre-registered rule. That rule found none in any
type (search-half doc §11; `selection-log-633.json`, shortfalls closure 2, retool 2, ai 1). **The cases this phase
runs are the five exploratory cases** selected under search-half doc §4.6.5 (his decision, 2026-10-19) and frozen
on 2026-10-27 (`freeze.json`): `closure-07`, `closure-19`, `pre-11`, `pre-25`, `pre-224`. All five are closures.
Retool is short 2 and ai is short 1, and §12.1's "at least one invest or retool" is not held. Each case carries its
exploratory label from `freeze.json` wherever it appears, in this phase's files and every later surface. The
pre-registered result (no case) is reported first.

Read the scope doc with these changes:

1. **Delivers 1:** the projection this checks against is `docs/phases/evidence/phase-5/cost.md` (case runs about
   $3.10, worst $4.50), not the scope doc's $18-20.
2. **Delivers 2 and the Cost section:** the model set is the fallback set (Phase 4 scope doc, amended 2026-10-13).
   Read every "Sonnet 4.6" as Haiku 5.5 and every "Nova Pro" as `gpt-oss-120b`.
3. **DoD 1:** "at least three cases, including an invest or retool case, unless Phase 5 reported a shortfall".
   Phase 5 reported one, so DoD 1 is met by five closure cases with the shortfall stated.
4. **Every result is a reading of an exploratory case.** It is never pooled with, or reported as, a result of the
   pre-registered rule. Phase 4 stays the headline (§4.6.5 A.2).
5. **What the cases can show is limited** (§4.6.5 G): every case is a closure, and some will be read on their
   choice alone. No case shows an investment decision. The results file and every later surface say so.

## 1. Where things stand on 2026-10-27

- **Phase 5 is closed** (`5f794ee`, pushed, CI and Deploy green). Five cases are frozen. Each has a `case.lock`
  (dossier, scenario and rubric hashes), every recognition probe passed in the set that counts (closure-19 in set
  2, after coarsening; the rest in set 1), and the order check admitted all five from the laptop (`freeze.json`,
  `order`).
- **The model set** is Haiku 5.5 (`haiku-5-5`, main, Anthropic's API, prepaid credit) and `gpt-oss-120b`
  (`gpt-oss-openrouter`, second family, OpenRouter pinned to DeepInfra `bf16`, his cash), as in the lock.
- **Nothing has been run on a case** beyond the recognition probes, the knowledge probes and the extraction.
  No official model has seen a case's scenario.
- **Spend:** at most about $45 cumulative (`cost.md`), under the $60 re-plan point. The balances on 2026-10-26 were
  Anthropic credit $11.96 (monthly limit $20, resets 2026-11-01), OpenRouter $3.70, and AWS inside the credits.
- **The frozen files are unchanged since the tag:** `git diff prereg-v1 HEAD` over the analysis set,
  `experiment.py`, the instrument and `uv.lock` is empty (checked 2026-10-27).

## 2. What this phase delivers

The scope doc's Delivers 1-8 for five exploratory closure cases on the fallback set:

1. **The credit check** against `cost.md`'s projection, from that day's three balances, before any run.
2. **Ten case sweeps**: five cases × two models, each 5 objectives × 3 wordings × 10 repeats = 150 runs, so 1,500
   runs in all. Each sweep is admitted by the gate's case mode (protocol §12.10) in the container.
3. **The matching**: for each case and model, `match_case` (frozen) on the rubric's primary reading and each
   uncertain call's alternative. The output is all five distances with spreads, the label, and "depends on
   reading" where it applies.
4. **The memo scan** on every model-written text of every case run (§5.4).
5. **The re-identification check** on each dossier (§5.5, decision 3).
6. **The coarse descriptions**, each searched before publication (§6.6).
7. **Publication as data** under `experiment/results/cases/` (§6.7). The public selection logs were already
   committed by Phase 5 (`selection-public.json`, `exploratory-public.json`).
8. **Measured cost**, from the records and then the bills.

**Not in this phase:** building, coarsening or replacing a case; the explorer and the methods page (Phase 6, 6.5);
any prose about a case (Phase 7, his words); a model outside the lock; Phases 1 and 1.5's open close-outs
(KNOWN-GAPS OPEN 2026-10-15, Phase 6's prerequisite, not this phase's).

## 3. What writing this doc found

1. **No session runs a case.** `run_case_gate` and `check_case_official` (`protocol/cases.py`) are built and tested
   on fakes, but nothing calls them. `hc sweep run` and `launch` load an experiment folder from the image, and a
   case's content lives only in `cases/<label>/set-<n>/` in the bucket, never in the image or the repo. The launch's
   order check (writing `OrderFinding.as_record()` into the manifest) and the container session that supplies case
   content are the CARRIED entry of 2026-10-09. Both are §5.1.
2. **The case's content fits the frozen loader.** The case's `dossier.toml` is in the frozen `title`/`text` format
   (`casebuild/assemble.py`), and its `scenario.toml` is a rendered scenario. A folder holding those two files, the
   tag's `company/objectives.toml` and a copy of `models.toml` loads through `load_experiment` unchanged. So the
   prompt, the tool and the classifier are the grid's, as tagged.
3. **The matcher has no driver, and nothing parses a rubric.** `match_case` (frozen) takes a `Scenario`,
   `RunRow`s and `CompanyDecision` readings. `rubric.toml` was written by hand in §4.7's form. Until now it has only
   been hashed and quoted to the reader (`reader/material.py`). §5.2 builds the parser and the command. **The
   parser is fitted to the five rubrics as committed. A rubric is never edited to fit the parser**: its hash is in
   `case.lock`, and the gate would refuse a changed one.
4. **The tag's code has no case command, so protocol 14 cannot be met to the letter.** Protocol 14 says the
   official analysis runs from a checkout of the tag. Phase 4 did that, because the tag's `hc analyze` was
   complete. The tag has no case matcher driver, and a driver added now is not in it. Decision 2.
5. **Case run records must stay private.** Every attempt record holds the request, so it holds the anonymized
   dossier, which is published only if §5.5's check passes. So case sweeps write under
   `cases/<label>/runs/<sweep_id>/`, which is never published and is already in the task role's grant
   (search-half doc §4.8). No infrastructure change is needed. The frozen `read_runs` reads any prefix outside
   `development/`, so it reads these unchanged.
6. **The record checks cannot see case sweeps.** `hc protocol records` (`protocol/recordcheck.py`) lists only
   `development/`, `pilot/` and `official/`. §5.3.
7. **Claude's deny list does not cover the new commands** that read case run records. §5.3, his edit as in Phase 4
   (Claude's auto mode will not edit its own permission file).
8. **The memo scan's "general check for any company name" does not exist.** The name guard and `casebuild/terms.py`
   match a term list only. Decision 4.
9. **Scaling hides sizes, not shapes.** One factor multiplies every dollar figure and headcount, so every ratio
   between two of them survives to rounding: revenue growth, margins, cash flow against revenue. Per-employee
   figures are not scaled at all (§12.6). Three years of such ratios, at three significant digits, may be close to
   a fingerprint against SEC's structured data, which is exactly the source §12.11 names. Decision 3.
10. **The recognition probe sent the dossier file, not the decision prompt's system text.** `caseprobe/run.py` sends
    `dossier.toml`'s bytes (its `title` line and the `text` block in TOML quoting). The decision prompt's system
    text is the scenario's role sentence, the dossier's `text` and the currency note (`sweep/prompt.py`). The
    dossier's words are the same in both. Recorded for the methods page. No action: the probe asked about the
    dossier, and it was shown the dossier.
11. **No refusal calls are needed.** The grid's blind refusal calls feed its refusal-rate table (protocol 4.7, 13.1).
    Protocol 12 asks for no refusal rate for a case. The matcher reads valid runs only, and a `no_tool_call` run is
    left out and counted either way. Status counts are published per case sweep.
12. **`gpt-oss-120b` is the long pole.** In Phase 4 its valid calls took a median of 74 s, and 37% of attempts were
    HTTP 429s. Its 750 case runs take about 15 hours as one task at a time. §6.2 runs its five sweeps side by side
    and falls back to fewer if `api_errors` stops repeat.
13. **The results-file hook already admits** `experiment/results/<a>/<b>/<c>.json` (`.pre-commit-config.yaml`), so
    `experiment/results/cases/<label>/<model>.json` passes. A memo file is `.jsonl`, which the pattern does not
    cover; §5.4 extends it.

## 4. The run set, fixed now

| Case | Model | Sweep | Runs | Seed |
|---|---|---|---|---|
| closure-07 | `haiku-5-5` | `case` | 150 | 4142789090 |
| closure-19 | `haiku-5-5` | `case` | 150 | 916347355 |
| pre-11 | `haiku-5-5` | `case` | 150 | 3510822617 |
| pre-25 | `haiku-5-5` | `case` | 150 | 1933638959 |
| pre-224 | `haiku-5-5` | `case` | 150 | 4141966721 |
| closure-07 | `gpt-oss-openrouter` | `case` | 150 | 2401484987 |
| closure-19 | `gpt-oss-openrouter` | `case` | 150 | 537881194 |
| pre-11 | `gpt-oss-openrouter` | `case` | 150 | 218789764 |
| pre-25 | `gpt-oss-openrouter` | `case` | 150 | 1259122587 |
| pre-224 | `gpt-oss-openrouter` | `case` | 150 | 1744604528 |

- **Each sweep:** the case's one scenario, all five objectives, all three wordings (`w1`, `w2`, `w3`), 10 repeats
  (protocol §12.7), in one shuffled order. The request is the grid's: Haiku with thinking off, `gpt-oss-120b` at
  `reasoning {effort: medium}`, the scenario's own `max_tokens`. **No pilot**: the repeat count is fixed by §12.7,
  not computed.
- **The seeds were drawn, not chosen**, as in Phase 4 §4. Each is the first eight hex digits of sha256 over `P`'s
  full id, the model key and `case-<label>`, read as an integer:
  `python3 -c "import hashlib; print(int(hashlib.sha256(b'649e8b9b8f1dde0e3698be0d279b62fef07ad70b|haiku-5-5|case-closure-07').hexdigest()[:8], 16))"`
  prints 4142789090. `P` predates every case.
- **One sweep per case per model.** A sweep the gate refuses is never run under another label.
- **The scenario's shape is read from the case's `scenario.toml`** at the dry run. Every case is expected to be S3,
  since the exploratory steps admitted closures on S3 only. If a case's shape is not S3, the dry run shows that before
  any run, and the matcher uses that shape's calibrated pair.

## 5. What is built before the first case run

Five items, all run code, config or new commands. None touches the lock's sets. **Sonnet builds; Opus reviews each
diff before he commits.** No model call and no AWS call in any test. `make check` green after each.

### 5.1 The case session (K1; closes CARRIED 2026-10-09)

`hc sweep launch --case <label> --model <key> --seed <seed> --cap-usd <cap> --max-minutes <m>` on the laptop, and
`hc sweep run --case <label> ...` in the container.

- **Only a frozen case:** the label must be in `freeze.json`'s `cases`. The probe set is that entry's, and it must
  equal `case.lock`'s.
- **The laptop:** reads `case.lock` and runs `check_case_order` with the GitHub and S3 readers Phase 5 built (the
  ones `hc case freeze` used). It writes `OrderFinding.as_record()` as `order.json` beside the manifest, write-once,
  before the first task starts. *Not inside `manifest.json`:* the manifest is recomputed by every session and must
  match exactly (`sweep/plan.py`), and the container cannot recompute the finding (no GitHub access). A resume
  recomputes the finding on the laptop and refuses unless it equals the stored one. It then runs the laptop half of
  the gate (`run_case_gate`, container not required), the preflight bound and a dry-run print, all before any task
  starts.
- **The container:** reads `case.lock` from the image and the three content files from
  `cases/<label>/set-<n>/`, and calls `check_case_official`. That checks the content hashes, `order.json`'s order
  finding, the probes from S3, and the grid's checks 2 and 5-8 in the container. Any failure refuses before any call.
- **The assembled experiment:** in a temporary folder, `models.toml` from the image, and under `case-<label>/`: the
  case's `dossier.toml`, the image's `experiment/company/objectives.toml` (its sha256 checked against the lock's
  `content.files` entry, refused if different), and `scenarios/<id>.toml` from the case's `scenario.toml`. Then
  `load_experiment("case-<label>", root=<tmp>)`, unchanged.
- **The plan:** experiment `case-<label>`, label `case`, the official model given, the one scenario, templates
  `w1`-`w3`, repeats exactly 10, five objectives. Anything else is refused, naming what differs.
  `check_not_official_rules` does not apply (this is an official run). The thinking sub-study's plan is refused
  for a case.
- **Where it writes:** `cases/<label>/runs/<sweep_id>/`, with the record label `case`. `sweep_prefix` gains the
  `case` role, and a case sweep can write nowhere else.
- **One sweep per case per model:** a launch or run is refused when the bucket already holds a case manifest for
  that case and model under another sweep id. A resume of the same id is allowed.
- **Progress lines carry no objective**, as for official sessions (Phase 4 §5.1).
- **Tests, on fakes:** a label not in the freeze is refused; a probe-set mismatch is refused; content that does not
  hash to `case.lock` is refused; a missing or not-admitted order finding is refused in the container; a changed
  `objectives.toml` is refused; a plan with 9 repeats, two scenarios, or two templates is refused; the assembled
  experiment's prompt for a fixed seed equals one built by hand from the same files; records land under the case
  prefix only; a second sweep for the same case and model is refused and its resume is not; no progress line holds
  an objective id.

**[done] K1, as built (2026-10-27; Sonnet built; Opus reviewed about 12:40 PM, no code fix, `make check` rerun
green at 2899).** `make check` green, **2899 tests** (42 new, in
`tests/test_case_session.py`); `hc protocol check` passes (nothing in the lock's three sets changed). No model, AWS or
GitHub call in any test. The new code is `caseprobe/session.py` (`prepare_case_sweep`, `check_case_plan`,
`check_one_sweep_per_case`, `write_order`, the assembly); `caseprobe/layout.py` gains `runs_prefix`; `sweep/runner.py`
gains the `case` role; `cli.py` gains `--case` on `sweep run` and `sweep launch`. What did not fit §5.1's text, and
what was done instead:

- **`order.json`, not the manifest, in the code's own words.** `check_order_finding`'s messages and the docstrings in
  `protocol/cases.py` said "the manifest"; they now say `order.json`. The tests' substrings still hold.
- **The container cannot read `freeze.json`** (the image holds `src/` and `experiment/`, not `docs/`), so "the label
  must be in `freeze.json`" is the laptop's check (launch, dry run). In the container the same guarantee is
  `order.json`, which only a launch that passed it writes; a hand-typed container command for another label finds
  none and is refused.
- **`_checked_content` is probe-shaped** (it also proves a probe call's worst case against a cap), so K1 reuses
  `load_content` and `check_case_content` from it and not the function itself.
- **`--case` and the plan flags.** `--experiment`, `--label` and the repeats are no longer required by the parser on
  `run` and `launch`; `main` requires them unless `--case` is given (same message shape, same exit 2). With `--case`:
  `--official`, `--pilot`, `--pilot-sweep`, `--experiment-dir`, `--repeats-file` and `--repeats-json` are refused by
  name; `--experiment` must be `case-<label>`; `--label`, `--repeats`, `--scenario` and `--template` are accepted only
  to be checked, so `--repeats 9` or `--label thinking` is refused naming what differs.
- **Order of a launch:** every check (including the preflight bound and the one-sweep rule), then `order.json`
  (`put_new`, or equal to the stored one on a resume), then the task. A launch the checks refuse writes nothing.
- **The dry run reads the network** (the bucket, `gh`, `git`) where the grid's dry run reads none, because check 2 needs
  them. It needs `--profile` and the bucket, as `hc case freeze` does.
- **A run on a laptop** (not `--dry-run`) is refused first, before anything is read; a container run needs `--store s3`.
- **`Role` gains `"case"`; `ROLES` does not.** `ROLES` stays the grid's three, so `--role` choices and the freeze's scan
  of `development/`, `pilot/` and `official/` are unchanged. `sweep_prefix(..., "case")` needs an experiment named
  `case-<label>` and returns `cases/<label>/runs/<sweep_id>/`.
- **`_run_and_report`** was cut out of the end of `cmd_sweep_run` (stop flag, the session, the summary lines) so the
  grid and the case path share it. No behavior change.
- **`hc sweep status` does not read a case sweep.** Its `--role` choices are unchanged; reading a case's progress is
  K3's (the deny list names `hc sweep status` for case sweeps). §6.1's "watch it with `hc sweep status`" is therefore
  not yet possible. **Decided 2026-10-27 (his, as recommended): K3 adds `--case` to `hc sweep status`** (§5.3).
- **One task per model blocks §6.2's parallel launches.** `launch_task` (`sweep/launch.py`) refuses a second running
  task for the same model, because tasks share a model's request quota. §6.2 launched Haiku's other four, and
  `gpt-oss-120b`'s five, together. **Decided 2026-10-27 (his, as recommended): the rule stays; each model's sweeps
  run one after another** (§6.2's dated note).
- **Review notes (Opus), no fix needed.** The assembled `Experiment`'s `root` is the temporary folder, gone once it
  is read; nothing on the case path reads it, and a later reader would fail loudly, not silently. The one-sweep rule
  counts manifests, so an `order.json` left by a container that refused before its manifest does not block a launch
  under another seed; no run exists then, so no seed can be chosen by its results. K3's "exactly one sweep per case
  and model" counts manifests for the same reason.

### 5.2 The matcher's driver and the rubric reader (K2)

- **`casebuild/rubric.py`**: a strict reader for `rubric.toml` in §4.7's form, giving the company's choice (or
  "not observable"), the observable lines, the observable and excluded dimensions, and each uncertain call's
  alternative reading. Its output is `CompanyDecision` readings, primary first. Excerpts and outcome terms are read
  and dropped. **Fitted to the five committed rubrics**: a test per rubric shape, using fictional values only.
- **`hc case match <label> --model <key> --sweep <id>`** (laptop, his to run). It reads the rubric from
  `cases/<label>/set-<n>/rubric.toml` and refuses unless it hashes to `case.lock`. It reads the runs with the frozen
  `read_runs` on the case prefix and refuses any unfinished run (as `results.build_results` does). It loads the
  scenario through the same assembly as §5.1 and calls the frozen `match_case` with the calibrated pair for the
  scenario's shape.
  - **It writes** `experiment/results/cases/<label>/<model>.json`, once, never overwritten. The file holds: the
    exploratory label text; run counts by final status; per reading, the label, nearest, tie, gap, all five
    distances with spreads, the basis and the undistanced count; `depends_on_reading`; the observable and excluded
    dimensions; and the company's reading as the matcher used it (the renormalized observable shares and the
    choice; no amount and no excerpt). It also records provenance: HEAD's commit, `hc protocol check`'s result,
    and the analysis files' combined sha256 from the lock.
- **`hc case match <label> --check-rubric`**: parses the rubric and prints only its dimension names, its reading
  names and the shape. No run is read. It is run at §6.0 on all five, so a rubric the reader cannot take is found
  before any sweep.
- **Tests:** a rubric fixture per form (choice only, choice and lines, an uncertain call); a hash mismatch refused;
  an unfinished run refused; the file refused if it already exists; the results file holds no excerpt, amount or
  outcome term (canary values in the fixture).

**[done] K2, as built (2026-10-27; Sonnet built; awaiting Opus's review).** `make check` green, **2941 tests** (42
new: `tests/test_casebuild_rubric.py`, `tests/test_case_match.py`); `hc protocol check` passes (no frozen file
touched). No model, AWS or GitHub call in any test. The new code is `casebuild/rubric.py` (the strict reader),
`caseprobe/match.py` (the driver) and `cmd_case_match` with the `match` subparser in `cli.py`. What did not fit
§5.2's text, and what was done instead:

- **The reader returns plain dataclasses, not `CompanyDecision`s.** `tests/test_architecture.py` bars `casebuild/`
  from importing `analysis`, so `rubric.py` is standard library only and returns a `Rubric`. The driver builds the
  `CompanyDecision` (`caseprobe/match.py`). The driver sits in `caseprobe/` and `cli.py` imports it inside its
  command only (it needs scipy, which the image leaves out); `MatchRefused` is a `SweepRefusal` so the command line
  catches it without that import.
- **The five committed rubrics share one layout.** Read from `scratch/k2-rubric-shapes.txt` (key names and types
  only): only the choice is observable, all four lines are `not observable`, and each rubric has one uncertain call
  (`u1`) whose `alternative` is a sentence. *As built, Sonnet's diagnostic looked only for option words, concluded
  that no alternative could be read into numbers, and left every call unmatched; Opus's review found otherwise
  (below).*
- **Two small mismatches between the rubrics and §4.7's words.** `shape` is written in upper case (`S3`) where the
  scenario's id is `s3`; the reader compares it lower-cased. An observable line's `reading` is read as a
  non-negative number (the only form §4.7 allows); **none of the five has an observable line, so that branch is
  tested but not fitted to evidence.**
- **Checks beyond §5.2's list, all refusals:** the rubric's `case` is the label, `scenario_total` is the scenario's
  total, `choice.key` and the company's choice are the scenario's, the rubric's lines are exactly the scenario's, and
  `dimensions` agree with which readings are observable; the sweep's manifest also runs the case's one scenario.
  If one of these were wrong for a committed rubric, `--check-rubric` shows it at §6.0, before any sweep.
- **`--check-rubric` also says whether the primary reading has enough dimensions** for the shape (`k_star` is public
  data). It names no choice, amount, run or result.
- **Provenance proves the frozen code, not that the driver was committed.** The file records HEAD, `hc protocol
  check`'s result, the analysis files' combined sha256, `uv.lock`'s hash, the rubric's hash and the sweep id. HEAD
  identifies the driver only if it is committed before the first `hc case match` run. A dirty-tree refusal would
  block the second of the ten runs (the first leaves a results file), so none was added.
- **Written once by a link, not a rename:** the file is written beside itself and `os.link`ed into place, so a
  concurrent or repeated command is refused and never replaces it.

**Opus's review of K2 (2026-10-27), and his decision on the alternatives.** `make check` green, **2952 tests**.

- **The alternatives can be matched.** Each `u1` alternative states its lines as `line = number`: four of the five
  make every line observable (all of the scenario's total on `eliminated`, the rest 0), and closure-19's makes
  `eliminated` alone observable. pre-224's sentence also gives a second alternative that leaves every line not
  observable with the same choice: that is the primary reading, so it is not matched separately. Leaving them
  unmatched would have reported "depends on reading" (`planning/07` §10.4 item 6) as not evaluated for every case.
- **Dated note, 2026-10-27, his decision (a), before any case run:** each alternative is transcribed into numbers in
  a private `alternatives.toml` beside the rubric in the appendix (`CaseAppendix.alternatives_path`); the choice
  stays the primary reading's, as no sentence changes it. **The rubric is not changed.** The transcription is legitimate
  only because no case run exists: the rubric's lock guards against fitting the company to results, and there are
  none. **The check is mechanical, not his line by line** (his request): a script compared every number in each file
  with its sentence (each `line = N`, the "observable as" list in the rubric's line order, and "(all)" against
  `scenario_total`) and all five agreed. Their sha256s are committed in `docs/phases/evidence/phase-5.5/alternatives.json`,
  which must be in a commit before the first case sweep.
- **What the code does with them:** `rubric.parse_alternatives` reads the file strictly against the rubric (its case,
  a known call once each, known lines, non-negative numbers). The driver refuses a file that does not hash to the
  committed sha256, a file with no committed hash and a hash with no file, runs each alternative through the frozen
  `check_decision`, and passes it to `match_case` after the primary. The results file adds `company_alternatives` (each
  reading's choice and renormalized shares, never an amount) and `provenance.alternatives_sha256`. A call with no
  transcription is still reported unmatched, with `depends_on_reading` null. `--check-rubric` lists every reading and
  each one's dimensions against `k_star`.
- **Two fixes:** the manifest's own `sweep_id` is now checked against the sweep asked for (`read_runs` takes the
  rows' sweep id from the manifest, so a manifest naming another sweep was accepted); and `hc case match` refuses
  when `src`, `pyproject.toml` or `uv.lock` differ from HEAD, so the HEAD in the file is the code that computed it.
  Scoped to the code, it does not block the second of the ten runs. Each has a test.

### 5.3 The record checks for case sweeps, and the deny list (K3)

- **`hc protocol records --cases`** writes `docs/phases/evidence/phase-5.5/record-checks.md`. It reads manifests,
  session records and provenance fields only, never `validation`, `tool_calls`, `text_blocks` or `raw_response`.
  It checks:
  - every case manifest's content hashes equal its `case.lock`;
  - its model is the lock's, with the lock's request (`thinking` value; DeepInfra for `gpt-oss-120b`);
  - its seed equals §4's drawn value;
  - its plan is §4's (one scenario, three templates, 10 repeats, five objectives);
  - its order finding is admitted;
  - every session ran in the container with a digest and a clean tree, and the digests are listed;
  - every run has a `final.json`;
  - there is exactly one sweep per case and model (counted by manifest, not by `order.json`: §5.1's review notes);
  - every session started after the freeze commit's CI run;
  - `hc protocol check` passes.

  Run counts, attempts by status and cost come from the same pass.
- **Deny entries** (his edit, from a `scratch/` script, as Phase 4 §5.4), both `uv run hc` and `uv run --no-sync hc`
  forms: `hc case match`, `hc case memos`, `hc protocol records`, and `hc sweep status` when it reads a case
  sweep. `tests/test_claude_settings.py` holds them. Claude reads what he pastes.
- **`hc sweep status --case <label> --sweep-id <id>`** (added 2026-10-27, his decision on K1's finding): reads
  `cases/<label>/runs/<sweep_id>/` through `sweep_prefix(..., "case")`, as `sweep/status.py` already can. The same
  lines as the grid's status: counts by status, attempts, cost and sessions, never an allocation or an objective.
  Tests on fakes: it reads a case sweep's records; it prints no objective id; without `--case` it is unchanged.

**[done] K3, as built (2026-10-28; Sonnet built; Opus reviewed about 9:10 AM, one fix).** `make check` stops at the tests: **3,015
tests, 3,011 pass, 4 fail by design** (`tests/test_claude_settings.py`, `case match` and `case memos` in both forms,
until he runs `scratch/k3-deny.py`). Format, lint and strict types are clean; `make root-check`, `make paths-check`
and `hc protocol check` pass. 63 new tests (`tests/test_case_record_checks.py`, plus the settings parameters and one
assertion in `tests/test_case_session.py`). No model, AWS or GitHub call in any test; nothing was run for real.

- **Reused from the grid's pass, unchanged:** `check_model`, `check_container`, `check_image`, `check_request`,
  `check_complete`, `check_frozen`, and the time test, now `_check_not_before` (with `check_after_tag` calling it, same
  output). `_graded` includes the `case` role. **New, case-only:** `cases`, `one sweep`, `case plan`, `seed`,
  `case content`, `order`, `after the freeze`. `Attempt` gains `dossier_hash` and `file_hashes`; `Sweep` gains the
  case label, seed, scenarios, repeats and the order record. The grid's checks, report and file are unchanged.
- **`hc protocol records --cases`** writes `docs/phases/evidence/phase-5.5/record-checks.md`, from the five labels in
  `freeze.json` and their `case.lock`s (`frozen_case_records`; a freeze or lock that cannot be read fails the
  `cases` check, never an empty set). Before any case run all ten pairs are missing and it exits 1, as intended.
- **P is a constant, `PREREG_COMMIT`**, in `protocol/recordcheck.py`: the code held it nowhere else (only these docs
  and the tag record do). A test checks it against `phase-3.5/tag-record.md`, and another reproduces §4's ten seeds
  from `case_seed`, which computes them.
- **What did not fit §5.3's text, and what was done instead:**
  - *"Content hashes equal `case.lock`."* The run records carry the dossier hash and the per-file hashes (dossier,
    objectives, scenario), so the check reads those, and recomputes the manifest's content hash from them. **The
    rubric's hash is in no run record**, and reading it from the bucket would read the rubric, so this pass does not.
    The gate checks it before every call and `hc case match` before every reading.
  - *"Five objectives."* Checked as 150 runs = 1 scenario x 5 x 3 templates x 10 repeats, not by counting objective
    ids (the module's source test forbids naming that field).
  - *`cases` check:* any key under `cases/` for a label that is not one of the five fails, as asked. If the bucket
    holds objects for an earlier, unfrozen candidate, the first real run will say so; that is his to look at, not to
    silence in code.
- **`hc sweep status --case <label> --sweep-id <id>`** reads `cases/<label>/runs/<sweep_id>/` through
  `sweep_prefix(..., "case")`. It refuses a label outside `freeze.json`, a missing `--sweep-id`, and any explicit
  `--role` or `--experiment`. To allow that, `--role` defaults to none (read as development) and `--model` and
  `--seed` are no longer required by the parser for `status`; `main` requires them without `--case`, same message
  shape, exit 2. K1's launch message now names this command.
- **Deny list.** `hc protocol records*` and `hc sweep status*` are already denied in both forms, so they cover
  `--cases` and `--case`; nothing added for them. `hc case match` and `hc case memos` are new, in both forms,
  through `scratch/k3-deny.py` (his to run: `python3 scratch/k3-deny.py`, looking for `added 4 deny entries`).

**Opus's review of K3 (2026-10-28).** One fix; the rest checked against the code it relies on. `make check` before
the deny script: **3,017 tests, 3,013 pass, the same 4 fail by design.**

- **Fix: `hc sweep status --case` refuses every plan flag**, as its docstring said. It refused `--role` and
  `--experiment` only and silently ignored `--model`, `--seed`, `--label`, the repeats, `--scenario`, `--template` and
  `--experiment-dir`. Harmless (the sweep id picks the sweep), but not what the code claimed, and K1's `--case` path
  refuses or checks the same flags. Two test cases added.
- **Checked, no change:** `FREEZE_CI_DONE` is CI run 40487345520's `updatedAt` on `5f794ee` (completed, success),
  read from GitHub. The manifest's content hash is recomputed exactly as `load_experiment` makes it (every content
  file but `models.toml`, through `combine_hashes`), and the runner writes `file_hashes` and `dossier_hash` on every
  attempt record, so the case-content check reads real fields. The rubric's hash is checked by K1's gate before any
  call (`protocol/cases.py`'s content check covers it), so leaving it out of this pass loses nothing. The deny
  script changes four lines and nothing else; `hc sweep status*` and `hc protocol records*` already cover the new
  flags (the review's own attempt to run `hc sweep status` was refused by the deny list).
- **To know before the first record-check run:** the `cases` check fails on any label under `cases/` in the bucket
  that is not one of the five. Every candidate that reached the recognition probe was frozen, so none is expected,
  but an earlier development upload would show up there. Fail-closed is right; if it happens, it is his call then.

### 5.4 The memo scan (K4; decision 4)

`hc case memos <label> --model <key> --sweep <id>` (laptop, his to run). It runs after the reveal.

- **Every model-written text of every run** is scanned: the tool call's `memo`, and the text blocks of a reply with no
  tool call (also of a failed attempt that is the run's final). Reasoning is not published and not scanned.
- **Two nets (decision 4 (d)):**
  - **The list:** the private term file (every case's terms, found through `hc.nameGuardTerms`), and SEC's list of
    filer names and tickers (`company_tickers.json`, fetched once per scan, its sha256 recorded), with corporate
    suffixes stripped and names shorter than four characters dropped except as tickers in capitals. Matches are
    case-sensitive and whole-word.
    **Dated note, 2026-10-28 (his decision, after K4's review, before any memo exists): a ticker counts only where
    the text marks it as one** (after an exchange, "NYSE: X" or "Nasdaq X"; after a dollar sign, "$X"; after the
    word ticker, "ticker symbol X"). Bare tickers are left to the model net, whose brief asks for them. The reason,
    measured on SEC's list of that day (10,430 tickers) over the repo's own business prose in memo-sized chunks:
    as written, the rule flagged 42% of the scenario prose's chunks and 85% of the planning docs', nearly all on
    one- and two-letter tickers that are ordinary words in capitals ("A", "D", "C", "AI"); with tickers marked,
    1% and about 2%. Every flag is a paid read by the independent reader, so the rule as written would have sent
    most of the 1,500 memos to it (an estimated $6-25 of his OpenRouter cash, against $1-6 now). Names are
    unchanged.
  - **The model:** Haiku 5.5 reads every memo, in batches of up to 25, with a fixed brief committed before the
    first scan (`experiment/readers/memo-names.txt`): "list every name of a real company, brand or ticker that
    appears in each memo, quoted exactly, or none". The brief carries no objective, and the order is shuffled.
    Requests and replies are written once in the case's appendix folder. A reply that does not account for every
    memo in its batch is re-asked once for that batch; a second failure flags every memo in the batch.
- **The judgment, by the independent reader:** every memo flagged by either net goes to the reader (`hc case reader
  ... memo`, a new brief kind, `experiment/readers/memo.txt`). It is shown the memo, the flagged words and §12.11's
  rule, never the dossier or a result, and answers per flag whether it names a real company. **A memo with a
  confirmed name is held back and counted, never edited.** A memo the reader clears is published. He may read any
  flag and overrule the reader toward holding, never toward publishing, and an overrule is logged with his reason.
- **The key:** the Haiku pass is a laptop model call, so it takes the Anthropic key in the environment for the one
  command (the CARRIED key-prompt workaround, §10).
- **Writes** `experiment/results/cases/<label>/<model>-memos.jsonl`, once: one line per run, with run id, objective,
  wording, final status, and the memo text or `"held"`. The counts held, by reason, also go into the results file's
  summary. `.pre-commit-config.yaml`'s results exclusion is widened to `.jsonl` under `experiment/results/cases/`.
- **The name guard runs on the commit as well**, a second layer for the term file.
- **Tests, on fakes:** a canary term in a memo is flagged by the list; a fake model reply naming a canary flags its
  memo; a batch reply missing a memo is re-asked once, then flags the batch; a memo the fake reader confirms is
  held, and one it clears is published; an overrule toward publishing is refused; a held memo's text appears nowhere
  in the output; whole-word matching (a term inside a longer word is not a hit); no brief or request holds an
  objective id; the file is refused if it exists.

**[done] K4, as built (2026-10-28; Sonnet built; Opus reviewed about 11:00 AM, three fixes below).** `make check` green, **3,069 tests** (52 new,
`tests/test_case_memos.py`; K3's four deny-list tests now pass, the script having been run); `hc protocol check` passes
(no frozen file touched). No model, AWS, SEC or GitHub call in any test; nothing was run for real. The new code is
`caseprobe/memos.py` (the scan), `reader/memo.py` (the two message builders and reply parsers, pure), two drafts of briefs
(`experiment/readers/memo-names.txt` and `memo.txt`) and `cmd_case_memos` with the `memos` subparser in `cli.py`;
`reader/briefs.py` gains `MEMO_KINDS`, `casebuild/appendix.py` gains `memo_overrules_path`, `.pre-commit-config.yaml`
and `experiment/readers/README.md` are widened. What did not fit §5.4's text, and what was done instead:

- **One command, not `hc case reader ... memo` per flag.** `hc case memos <label> --model <key> --sweep <id>` runs both
  nets, the reader on every flagged memo, then writes. The `memo` brief sits beside the reader's kinds as a second tuple,
  `MEMO_KINDS = ("memo-names", "memo")`, not in `KINDS`: `load_brief` takes either, `run_read` and `hc case reader`
  still take only `KINDS` (a test holds that `hc case reader ... memo` is refused). Both briefs are under
  `experiment/readers/`, so `frozen_reader_inputs` covers them, and every request record holds the brief's sha256.
- **The held counts are not in the results file.** `hc case match`'s file is write-once, so the counts go to
  `<model>-memos-summary.json` beside it (counts by reason, provenance as K2's file has it, both brief hashes, the SEC
  list's hash, the reader-inputs commit), written once by a link. The memo file is `<model>-memos.jsonl`: one line per
  run with run id, objective, wording, final status, `source` (`memo`, `reply_text` or null) and `memo` (the text,
  `"held"`, or null for a run whose final attempt wrote no text). A reply with no tool call publishes its text blocks.
- **Resumable, which §5.4 did not say.** His overrule needs a second pass after he has read the flags, and the records
  are write-once. So every paid call is recorded (request before the call) and a rerun reads the records instead of
  calling: he deletes the two uncommitted public files, adds `memo-overrules-<model>.toml` to the case's folder and runs
  the command again, at no cost and with no question asked. A request with no reply is refused until he looks; a rerun
  whose lists, flags or stored requests differ from the first run's is refused. The overrule file has `[[overrule]]`
  entries of `run_id` and `reason` (optional `action`, which may only be `hold`); an entry that would publish, one for a
  run with no text or no run, a repeat, or one without a reason stops the command before any spend. Each overrule is
  logged with its reason in the appendix and counted.
- **Order of the refusals.** Before any byte leaves: the results file for the model must exist (the reveal), the two
  public files must not, `hc protocol check`, the reader's inputs committed and pushed, the models and briefs, the
  case, the sweep (all of K2's checks, through `load_material` and `read_sweep`), the overrule file and the private term
  file; the CLI also refuses when `src`, `pyproject.toml` or `uv.lock` differ from HEAD. Then SEC's list (free), then the
  first question (Haiku), then the second (the reader), each asked only if it has a call left to make, the keys last.
- **`read_runs` gives no texts.** The frozen reader returns rows, so `collect_texts` reads each run's `final.json` and its
  final attempt's record by named fields only: `tool_calls[0].input.memo`, else `text_blocks`. Reasoning is never read.
- **The reader's reply.** Per flagged word `yes`/`no`/`cannot_tell`, and once for the memo as a whole (so a name that no
  net flagged can still be caught, and a memo flagged by a failed batch, with no word, can be judged). Any `yes` holds the
  memo (`name_confirmed`); no `yes` and any `cannot_tell` holds it too (`reader_unclear`: neither cleared nor confirmed,
  so fail closed); three unusable replies hold it (`reader_no_reply`). Only a full set of `no` publishes. His overrule is a
  fourth reason (`overruled`).
- **A call that fails at the API is not an attempt.** It is recorded and stops the run (a spent credit is not a model
  failure, and treating it as an unaccounted batch would flag every memo); the rerun goes on from the records. A reply
  that arrives but does not account for its batch counts as an attempt: two such flag every memo of the batch.
- **The lists.** The term file is the name guard's (`hc.nameGuardTerms`, matched by `find_terms`, so its `allow:` lines
  apply); the per-case `terms.txt` are not read. SEC's names and tickers are matched on whole-word tokens, which is the
  guard's rule in effect, case-sensitively; a name is its title with a state tag (`/DE/`) and a legal form (Inc, Corp,
  Co, Ltd, LLC, PLC, ...) stripped, dropped under four characters, and an all-capitals title is also matched
  capitalized (SEC's casing is not a writer's). Tickers are kept at any length, in capitals only, as written. *(As
  first built, a ticker counted bare, so a one- or two-letter ticker that is also a word in capitals flagged most
  memos; the review measured it, and since the dated note of 2026-10-28 a ticker counts only where marked.)* The
  first question prints how many memos the lists flagged, and the second prints the reader's worst case, so he sees
  the size before spending. SEC's file is fetched through the one
  EDGAR client and cached in the case's own folder, so the second model's scan of the same case reads the same file.
- **The model net's shuffle is seeded** from the label, model and sweep, so a rerun asks the same questions; batch ids are
  `m1`, `m2`, ... by position. Nothing sent holds a run id, an objective or a wording. Request records hold no
  objective (they hold the run id of a reader's memo, privately).
- **Haiku's allowance is a constant** (`NAMES_MAX_TOKENS = 4096`, in the record), since the model's `models.toml` entry has
  none; its id, route and prices are the `haiku-5-5` entry's.
- **The briefs are drafts for his approval.** `memo-names.txt` and `memo.txt` must be read and approved by him, then
  committed and pushed before the first scan; until then `frozen_reader_inputs` refuses.

**Opus's review of K4 (2026-10-28).** Three fixes, one of them his decision; the rest checked against the code it
relies on. `make check` green before and after.

- **Fix (his decision): a ticker counts only where marked** (the dated note above). `ListNet.words_in` matches SEC's
  names as before and tickers through `_MARKED_TICKER`; the fixture memo now marks its ticker, and the list test
  holds that a bare ticker, short or long, is not a flag and a marked one is (exchange, dollar sign, the word ticker),
  in capitals and whole only.
- **Fix: the reader's brief contradicted its task.** `memo.txt` said "Do not use anything you may remember about any
  company, plant or news", a line carried from `rejection.txt` and `knowledge.txt`, where it belongs. Here the
  reader cannot know whether a word is a real company without what it remembers. It now says to use what it knows to
  recognize a name, and not to work out which company the memo is about. `memo-names.txt`'s "Use only the memos"
  says the same: list only names written in the memos, recognized with what the model knows.
- **Fix: an edit to the term file no longer blocks his overrules.** The flags record held the term file's hash and
  a rerun compared it, so any edit between a scan and its overrule rerun (a term for another case) refused the rerun
  for good. The rerun now compares every memo's flags and not the lists' hashes; a change that flags something new
  is still refused. One test added (it fails without the fix).
- **Checked, no change:** SEC's list is cached in the case's folder by the one EDGAR client, so a rerun sees the same
  list. The name guard scans `.jsonl` on commit (only binary files are skipped). Reader calls are sequential and,
  with reasoning, well under the entry's 10 a minute; a refusal at the API stops the run and the rerun goes on from
  the records. Nothing printed or refused holds a flagged word or a memo. Every test §5.4 names is there.
- **To know before the first scan:** the second question's worst case assumes the reader's full 24,000-token
  allowance on every read (about $0.29 a read), so it prints far above the expected cost; and places do not count
  under §12.11, so a real plant location in a memo is caught only by the commit's name guard, if the term file holds
  it.

### 5.5 The re-identification check (K5; decision 3)

As recommended in decision 3 (a): **`hc case reident <label>`** (laptop, his to run, no model call).

- **The figure half:** from the dossier's financial section, the ratios scaling cannot change. These are each
  year-on-year revenue change, operating margin each year, and operating cash flow over revenue each year, plus
  every unscaled per-employee figure. Each is compared, within its rounding tolerance, against SEC's XBRL frames for
  the same periods across every filer. The real periods are known from the private appendix: an attacker who knows
  the half-year from the public description gets them nearly free. The output is the number of filers that match
  every ratio, and whether the case's own filer is among them (taken from the appendix, never printed).
- **Fails if the company is among fewer than 20 matching filers.** The threshold is fixed here, before any case
  is checked. The output, written to the appendix and summarized publicly, is "passed" or "withheld: its scale-free
  figures match fewer than 20 filers in SEC's structured data". No count that narrows the case further is published.
- **The description half**, only for a dossier that passed the figure half: he searches the overview's first
  sentence and up to three distinctive phrases of the situation section as written, each in a web search engine,
  and logs the queries and whether the company appears on the first page. If it appears, the dossier is withheld,
  with the reason.
- **A withheld dossier changes nothing else:** the case's results are still published by type and coarse
  description, and the methods page says that this case cannot be re-run from published inputs (scope doc, Known
  risks).
- **Tests:** the ratios from a fictional dossier; the tolerance from three significant digits; a fixture frame in
  which the target is unique (fail) and one in which it hides among 25 (pass); nothing the command prints holds a
  name or a CIK.

**[done] K5, as built (2026-10-28; Sonnet built; awaiting Opus's review).** `make check` green, **3,115 tests** (45
new, `tests/test_case_reident.py`); `hc protocol check` passes (no frozen file touched). No SEC, AWS, GitHub or model
call in any test, and nothing was run for real; the private appendix was never opened. The new code is
`caseprobe/reident.py` and `cmd_case_reident` with the `reident` subparser in `cli.py`; `casebuild/edgar.py` gains
`EdgarNotFound` (a subclass of `EdgarError`, raised on a 404, so a frame SEC does not have is told from a failure; the
old message and its test are unchanged). The module imports nothing that needs scipy (a test imports it and `cli` in a
fresh interpreter and checks `scipy` is absent). **No AWS:** the case is loaded from the repository (`case.lock`,
`freeze.json`, through `read_case` and `check_frozen`) and the private appendix (the dossier of the lock's probe set,
hashed against `case.lock`; `build.json`; the CIK from `sources.json`); no bucket is read. It needs
`HC_SEC_USER_AGENT` (or `hc.secUserAgent`) and the appendix setting, and fetches about 18 frames (three years, four
revenue tags, income and cash flow) at 0.25 s apart, cached in the case's folder. What did not fit §5.5's text, and what
was done instead:

- **The figures are rebuilt from `build.json`, not read from the dossier's prose.** The raw XBRL value is rendered as
  `figures.py` renders it (to $0.1 million, or whole dollars under $1 million), then scaled by `scale_dollars`, the
  transform's own function, with the case's factor. *Departure from the brief's words: the interval is wider than half a
  unit of the third digit.* The text was rendered to $0.1 million before it was scaled, so the true scaled value can sit
  up to 0.05 million times the factor beyond the stated one; without that, the case's own figures could fall outside
  their own intervals and withhold a case spuriously. The width is the third digit's half unit plus that rendering
  half unit times the factor (`stated_interval`). It errs toward more matches, not fewer, the opposite of the other
  assumptions, so it is the first thing for Opus to confirm or strike.
- **Per-employee figures are not compared:** SEC has no headcount frame (`dei/EntityNumberOfEmployees` is a 404). Recorded
  in the private record and here as a limit of the check; no substitute was invented.
- **Every ratio is exact.** Intervals and filers' ratios are `Fraction`s, so "a value at the interval's edge matches" is
  exact; a ratio whose denominator interval holds zero is dropped and recorded; a revenue interval is never assumed
  positive. At most eight ratios (two growths, three margins, three cash-flow ratios); a line or year `build.json` lacks
  drops the ratios that need it.
- **Which frame, and what a filer's row is.** For each fiscal year the own filer's revenue tag (as `build.json` records
  it, refused if it is not one `figures.LINES` lists) is asked for in the calendar-year frames of the year itself, the
  year before and the year after, in that order and only as needed, until the own CIK appears there with
  `end` equal to the fiscal year end. The other tags' frames are then taken at that year. A filer's revenue is the first
  tag, in `figures.LINES`' order, with a row for it. A filer matches only if every ratio can be computed from its rows
  and falls in the interval; its income or cash-flow row must end the day its revenue row ends, or the ratio is not
  formed.
- **The verdict, fail closed.** The own filer not found in a frame for a year a ratio needs, found but outside its own
  intervals, or **no ratio at all** (a `build.json` that gives none) is "withheld: ... could not confirm"; fewer than 20
  matching, own included, is the fewer-than-20 reason; the threshold test is exactly 20 passes, 19 withholds. When the
  own filer is not found, no year after that is compared (so there is no matching count and the output says "not
  compared").
- **The description half.** The template holds the overview's first sentence (cut at the first full stop that is not an
  abbreviation or an initial) and three empty slots. *Departure: query 1 need only be the start of the overview, not
  equal to the first sentence the code cut*, so a wrong cut can be fixed by hand; each slot's phrase must appear in the
  situation section, whitespace aside, and the dossier hash in the file must be the case's. An entry with an engine, a date
  and `company_on_first_page` is answered; any `true` withholds even beside unanswered entries; query 1 and every filled
  slot answered `false` passes; anything else is pending and nothing public is written. The template is written
  only after a passed figure half.
- **A coarsened case (probe set 2) is checked at `build.json`'s three-digit figures, not at its coarsened ones.** The
  hand-coarsened dossier's figures (rounded to two significant digits, protocol §12.8) are not in `build.json`, and the
  appendix was not opened. Three-digit intervals are the narrower test, so any count is a lower bound on what an attacker
  of the coarsened dossier would match: it errs toward withholding. Recorded in the private record. `closure-19` is the
  case in `freeze.json` this applies to. *Changed at Opus's review (his decision (a), below): a coarsened case is now
  checked at its two-digit figures.*
- **What is written.** Private, once: `reident-record.json` (ratios and intervals, every frame with URL, sha256 and fetch
  time, whether each frame exists, the year found for each fiscal year, the matching CIKs, what was dropped, the
  assumptions) and `reident-search.toml`. A rerun recomputes the record from the cached frames and refuses if it differs;
  a frame SEC 404s is asked again (it is never cached), and a change there also refuses. Public, once, by a link,
  `experiment/results/cases/<label>/reident.json`: `reident_version`, the label, `exploratory`, `status`, `reason` (one of the
  three fixed strings or null), the threshold, and provenance by hash: HEAD, `build.json`, the dossier, the private record
  and, *added to the brief's list so a pass can be traced to the answers it rested on*, `search_sha256` (the filled
  template's, null when the figure half withheld it). No count, CIK, name, year, period or URL. Refused up front if the
  file exists, with nothing fetched; the command also refuses when `src`, `pyproject.toml` or `uv.lock` differ from HEAD.
- **What it prints** is the status and a note, the ratios used, the matching count (the case's own filer included) and
  whether the own filer was found and matching; never a name, CIK, ticker or URL. A pending run says which file to
  fill in (by its name in the case's folder) and writes nothing else.
- **No deny entry**, as decided: it makes no model call and reads no result.

**Opus's review of K5 (2026-10-28), and his decision on the coarsened case.** One change, his decision (a); the rest
checked against the code it relies on. `make check` green before and after.

- **Confirmed: the rendering's extra width stays.** `figures._dollars` renders to $0.1 million, and `transform._dollar`
  scales that rendered number in its stated unit to three digits (`scale_dollars`), so the true scaled value sits up
  to 0.05 million times the factor beyond the stated one. For a figure under about $10 million that term is the
  larger part of the interval; without it a case's own small operating income would miss its own interval and the
  case would be withheld for no real reason.
- **Change (his decision (a)): a coarsened case is checked at its two-digit figures.** At three digits a pass was
  conclusive but a "fewer than 20" was not, and the public file is write-once. For probe set 2 each figure is now
  the three-digit figure rounded to two (protocol §12.8, done by hand from the three-digit dossier), and its interval
  is centred there and widened by both roundings' half-units plus the rendering's: a rounding of a rounding can land
  more than one half-unit away (1,545 goes to 1,550, then 1,600). `stated_interval(..., coarsened=True)`,
  `build_ratios(..., coarsened=...)`, `COARSENED` reworded. One test added (that example, exact), and the coarsened
  case's test now holds that its own filer matches and that every wide interval contains the plain one.
- **Checked, no change:** the CIK is read where `documents.write_sources` writes it (`sources.json`'s ten-digit
  string); the dossier's sections are read from its `text` key under `assemble.HEADINGS`; a cached frame keeps its
  first `fetched_at`, so a rerun's record is stable; `ReidentRefused` is a `SweepRefusal` and `EdgarError` is caught
  by `cmd_case`; nothing refused or printed holds a URL, a CIK or a name; every CIK and name in the tests is a
  fictional canary.
- **To know before the first run:** SEC's API page (read live 2026-10-28) says a frame holds, per filer, the fact
  **last filed** for the period. A case whose earlier years were recast in a later 10-K (discontinued operations
  after a closure are common) will not match its own intervals and is withheld with the "could not confirm" reason.
  That is the fail-closed outcome chosen, not a fault; the output then says the own filer was found but not matching.
  Not built (offered, not taken): the private record does not say which of the own filer's ratios missed.

## 6. The runbook

**His commands, one at a time.** Anything longer than one line goes in a `scratch/` script, with the string to look
for named. Claude reads only what he pastes. The run log `docs/phases/evidence/phase-5.5/run-log.md` starts at §6.0.

### 6.0 Before the first case run (no model call)

1. §5's five items are committed and pushed, with **CI and Deploy green on that commit**. Its image digest goes into
   `run-log.md`.
2. **Live checks, Claude's, from the vendors' pages:** Haiku 5.5 is still served as `claude-haiku-5-5` at its price;
   `gpt-oss-120b`'s `deepinfra/bf16` endpoint is listed. A missing model or host stops the phase for his decision.
3. **The credit check (Delivers 1), his readings:** the Anthropic credit and the month's spend against its limit
   (the limit resets 2026-11-01); OpenRouter's balance; AWS Billing. Claude sets them against `cost.md` (case runs
   about $3.10, worst $4.50). If a pot cannot cover its share, he decides before any run: top up, or cut in the
   pre-registered order (`planning/05` §5.1: the fifth case, then the fourth, where "fifth" is the last in
   `freeze.json`'s order).
4. **Dry runs:** `hc sweep launch --case <label> --model <key> --seed <seed> --dry-run` for all ten. Expect `every
   check passes`, the order finding `admitted`, the scenario's shape, 150 runs and the preflight bound. Then
   `hc case match <label> --check-rubric` for all five. **Dated correction, 2026-10-29 (found at §6.0):** the
   dry run is `hc sweep run --case <label> --model <key> --seed <seed> --profile horizon-compact --dry-run`.
   `hc sweep launch` takes no `--dry-run`, and its case path writes `order.json` and starts the task, so the command
   as first written must not be used. `scratch/p55-dryruns.sh` runs the ten and the five.
5. **The caps:** each sweep's cap is its preflight bound rounded up to the next dollar, about $1-2 for Haiku and
   under $1 for `gpt-oss-120b`. All are under the $25 official cap, so no over-cap flag is expected.

### 6.1 The first sweep alone

`haiku-5-5` on `closure-07` first, alone. It is watched with `hc sweep status --case closure-07` (K3) until about
20 runs have a final result: counts by status only, never an allocation or an objective. This is the live proof of K1 (the assembly,
the gate in the container, the case prefix) at a cost of a few cents. **It also closes the cost-tag item's launch
half again**: the task starts, so `propagateTags` was accepted. If anything fails here, the fault is diagnosed and
fixed (logged run code), and nothing else has launched.

### 6.2 The other nine

- **Haiku's other four** launch together once §6.1 looks right. Each takes about 20-30 minutes.
- **`gpt-oss-120b`'s five** launch together, with `--max-minutes` 720. A session that stops on `api_errors` is
  re-launched after about 30 minutes. If two such stops come within an hour, the remaining sweeps run two at a time.
  Expect about a day, as in Phase 4.
- **Dated note, 2026-10-27 (his decision on K1's finding, before any case run): one sweep at a time per model.**
  `launch_task` refuses a second running task for the same model (tasks share its request quota), and the rule
  stays. So the two bullets above run as two chains side by side: Haiku's other four one after another, and
  `gpt-oss-120b`'s five one after another, each launched when the one before is complete. From Phase 4's run log
  (Haiku about 990 runs in 3 hours; `gpt-oss-120b` about 1,270 in 11 over two sessions), about 2.5 hours for Haiku's
  chain and 7-8 for `gpt-oss-120b`'s, plus any re-launch: still about a day. The "two at a time" fallback above is moot.
- Every launch, stop, re-launch and fix is a line in `run-log.md`. **Phase 4 §7's stop table applies as written.**
  One more refusal is possible: the case gate. A case-gate refusal is diagnosed and never worked around.

### 6.3 The record checks

`hc protocol records --cases`, once all ten sweeps are complete. **Any failed check stops the phase before the
reveal.**

### 6.4 The reveal (decision 1)

`hc case match` for each case and model (`scratch/p55-match.sh`, ten lines), from `main`, under decision 2's rule.
The ten results files are written. **This is the first time anyone reads a case result.** Claude reads them in full
from here on.

**[done] 2026-10-31, at `cbd6cb0` (his run).** Ten files written, each 150 of 150 `valid` and `protocol_check: ok`;
all 20 readings are no good match (`run-log.md`, §6.4). Two behaviors of the frozen matcher to disclose: KNOWN-GAPS,
OPEN 2026-10-31.

### 6.5 The memo scan

`hc case memos` for each case and model, with the Anthropic key in the environment for the command, then `hc case
reader ... memo` on the flagged memos (decision 4 (d)). He reads any flag he chooses. The counts held go into the run log.

### 6.6 The re-identification check and the coarse descriptions

- `hc case reident` for each case (decision 3).
- **The coarse descriptions (Delivers 6), fixed here:** for each case, the SIC major group's name (two digits,
  SEC's list), "plant closure", a revenue band on the unscaled latest annual revenue (under $1 billion, $1-10
  billion, over $10 billion), the half-year of first disclosure, and the country. **He searches each as written and
  with two variations** (the sector's plain-English synonym; the half-year as a quarter). If the company appears on
  a first page, the description is coarsened once: the sector goes to SEC's division ("Manufacturing"), then the
  half-year to the year. It is searched again. A second hit means the description is withheld, and the case is
  published by type only.

### 6.7 Publication

**One commit, after the last session**: the ten results files, the ten memo files, `experiment/results/cases/cases.json`
(per case: label, exploratory label text, type, shape, coarse description, probe results from `freeze.json`, the
re-identification outcome, and the dossier as published or "withheld" with its reason), each dossier that passed as
`experiment/results/cases/<label>/dossier.txt`, and `record-checks.md`. The commit deploys an image, which is
harmless after the last session. The guard checks it. **No commentary**: prose is Phase 7's, in his words.

**Dated note, 2026-10-31 (his decision, at §6.4):** the ten results files are committed with §6.4's docs, not held
for this commit, so they are tracked rather than only on the laptop. They hold no name, amount or excerpt, are
written once, and nothing after §6.4 recomputes them; the sessions are over, so the image the commit deploys is
harmless. `record-checks.md` was already committed at §6.3 (`cbd6cb0`). This commit carries the rest: the memo
files, `cases.json` and the dossiers that pass.

### 6.8 The measured cost

From the record checks' per-sweep totals, then the bills: the Console, OpenRouter's activity, and AWS Cost Explorer.
**The Cost Explorer reading also closes the cost-tag CARRIED entry** if the case sweeps' Fargate cost shows under
`horizon-compact`. If the `Project` tag was never activated as a cost-allocation tag, that is found here, activated
by him, and the item closes on the next reading. Dated patches go to `planning/03` and `planning/07` §13, and to the
ROADMAP's cost column. The $60 point is checked against measured spend.

### 6.9 The close

The DoD audit (§11), the honor statements (his in his words; Claude's: no case result read before §6.4, anything
seen by accident disclosed), KNOWN-GAPS and START HERE, and the ROADMAP row.

## 7. During the runs

**The push freeze, one image for all ten sweeps**, as Phase 4 §7: from §6.1's launch to the last session's end, no
push that touches `src/`, `experiment/`, `infra/`, `pyproject.toml` or `uv.lock`, except a logged run-code fix for an
infrastructure fault. Docs-only pushes (the run log) are fine. A fix is made only for an infrastructure fault, never
because of what a model answered. **The case content, the rubrics and the lock are never touched.**

**What never stops a sweep:** a model's failures or refusals, at any rate. **A sweep ends partial** only if the model
or its pinned host is withdrawn. It is reported as partial and never finished elsewhere.

## 8. Decisions for him

Each has a recommendation and a reason. What is not here is settled by the scope doc, the protocol, §4.6.5 or
Phase 4's decisions.

1. **DECIDED (his): (a). When case results are first read.**
   - (a) **Recommended: one reveal, after all ten sweeps are complete and the record checks pass**, as Phase 4's
     decision 1. Until then nobody reads anything by objective: no allocation, choice or memo. The reason: Haiku's
     sweeps finish about a day before `gpt-oss-120b`'s. A choice made in that gap (a fix, a stop, a cut) would
     otherwise be made by someone who knows the main model's readings. The cost is about a day.
   - (b) Per model as each finishes. Haiku's readings a day sooner, and the second family's sweeps are then
     conducted by someone who has seen them.
2. **DECIDED (his): (a). Where the matching runs** (finding 4).
   - (a) **Recommended: from `main`, with the frozen code proven unchanged.** The driver (§5.2) is new run code; the
     computation is the tag's `match_case`, `read_runs`, `descriptive.distance`, intervals and thresholds. `hc
     protocol check` proves these byte-identical to the lock, with `uv.lock` unchanged. Each results file records
     HEAD, that check's result and the analysis hash, and the record checks re-run it. This keeps protocol 14's
     purpose (the code that computes is the tag's), not its letter, and the methods page says so.
   - (b) From a worktree of the tag with the driver and rubric reader copied in. Closer to the letter, but the tree
     that runs is then neither the tag nor `main`, and nothing records which copy ran. It proves less than (a).
3. **DECIDED (his): (a). The re-identification check's method** (finding 9).
   - (a) **Recommended: the figure half against SEC's XBRL frames, then the description half (§5.5)**, with
     withholding if either fails, at the threshold of 20 fixed now. It is measured rather than assumed, it uses the
     source §12.11 names, and it costs no money (SEC's API is free). **Expect most or all dossiers to be withheld:**
     three years of ratios at three significant digits are close to a fingerprint. That is a finding to report, and
     it does not change any case's result.
   - (b) Withhold every dossier without the check, the reason stated. It saves about half a day of build, but rests
     on an unmeasured claim, and §12.11 says "published only after a re-identification check passes", which (b)
     never tries.
   - (c) The description search only. It misses the structured-data route that §12.11 names.
4. **DECIDED (his): (d). The memo scan's general list** (finding 8).
   - (d) **Recommended, added 2026-10-27 on his question, and taken: both nets, and a model judges what they
     catch** (§5.4). (a)'s list runs as written; Haiku 5.5 also reads every memo for company names (about $0.20-0.30
     of the credit); anything either flags goes to the independent reader, which decides whether it names a real
     company. He reads nothing unless he chooses to. His reason: he preferred to delegate the reads to a model. The
     list keeps a fixed, free net under the model's, so a model miss is not the only check.
   - (a) SEC's public list of filer names and tickers** (`company_tickers.json`, fetched once at the
     scan and its sha256 recorded), with corporate suffixes stripped and names shorter than four characters dropped
     except as tickers in capitals. Every hit is read by him. It is mechanical, fixed and repeatable, and it covers
     every listed company, which is where a name in a memo is most likely to come from.
   - (b) A model reads every memo for any company name. It reaches private and foreign names, but adds about 1,500
     calls, a model's judgment, and a cost.
   - (c) The private term file only. That is not the "general check for any company name" §12.11 asks for.

## 9. Rules this phase must not break

The scope doc's rules hold as written. A frozen case is not changed by what its runs show, and a model's failures
are outcomes. "Most closely matched" is always the wording, and ties and "no good match" are shown as such. No word
about a company's motives. Rule zero. And from this doc:

- Nothing reads a case result before §6.4 (decision 1). Claude runs no command that reads case run records (§5.3).
- The rubric and the case content are never edited. The parser fits them.
- Every case surface carries its exploratory label, and the pre-registered result (no case) comes first.

## 10. Order of work

1. **[Opus] This doc**, approved by him. With it go the scope doc's amendment (§0, already in this change), KNOWN-GAPS
   START HERE (the 4:50 AM block corrected: Phase 5 is committed as `5f794ee`, not "uncommitted") with the CARRIED
   entry of 2026-10-18 closed, and the ROADMAP row. One commit: `phase 5.5: implementation doc`.
2. **[Sonnet builds, Opus reviews each] §5.1-5.5**, one commit each or together. `make check` green; he commits and
   pushes; Deploy green; the digest is recorded. The deny entries are his.
3. **[him, Claude reading pasted output] §6.0-6.9**, in order.

**Model choice:** Sonnet for step 2; Opus to review it, and for the reveal's reading and the close.

**The four CARRIED entries, and how each is taken:**

| Entry | Taken by | Closes when |
|---|---|---|
| 2026-10-18, exploratory cases (two of three types short) | §0 | this doc is approved |
| 2026-10-09, the launch's order check and the container session | §5.1 | the first case sweep is admitted in the container (§6.1) |
| 2026-10-15, the cost tag | §6.1 and §6.8 | Cost Explorer shows the case sweeps' Fargate under `horizon-compact` |
| 2026-10-17, the hidden key prompt | the workaround, at §6.5 | **Not fixed; not blocking.** The runs read SSM in the container. The one laptop call that takes a key is the memo scan (§5.4, decision 4 (d)); it uses the workaround, the key in the environment for the one command. The `getpass` cause stays open. |

## 11. Definition of done, and the proof of each

1. **Every frozen case ran on both models** through the case gate, or was cut at §6.0 with the reason; the shortfall
   is stated. *Proof:* `record-checks.md`, ten sweeps complete; `run-log.md`.
2. **Every case is matched,** with distances, spreads, alternative readings, and observed and excluded dimensions.
   *Proof:* ten results files.
3. **Every memo passed the scan or was held back and counted.** *Proof:* the memo files and their counts.
4. **Every dossier passed the re-identification check or is withheld with its reason; every public description
   passed its search.** *Proof:* `cases.json`, with each check's record in the appendix.
5. **The results are committed as data, and the guard passed every commit.** *Proof:* §6.7's commit, with CI green.
6. **Measured cost recorded; `make check` and CI green.** *Proof:* `run-log.md`'s cost section; the close commit's CI.

## 12. Cost

**Building §5: $0. The runs: about $3.10, worst $4.50** (`cost.md`). About $2.40 is Anthropic credit and about $0.70
his OpenRouter cash. Fargate is under $1 of AWS credit. **Little money for the checks:** SEC's API and web searches are
free. The memo scan's Haiku pass is about $0.20-0.30 of the credit, and the reader's reads of flagged memos a few
cents each of his cash (decision 4 (d)); *(2026-10-28, K4's review: about $1-6 in all, an estimate that turns on how
many memos Haiku flags; §5.4's dated note)*. Cumulative after this phase: about $49, worst about $51, under the $60
re-plan point.

**Time:** about two days of build and review for §5. Then about a day of run time, set by `gpt-oss-120b`. Then about
a day for the reveal, the scans, the checks and the close.

## 13. Genuinely uncertain

- **Whether every rubric reads cleanly into the matcher's terms.** They were written for the reader, in a form the
  code never parsed. If one holds a dimension the scenario has no line for, `check_decision` (frozen) refuses it at
  the reveal. §6.0's `--check-rubric` exists to find that first. If it happens, the case is reported as not
  matchable as written, and the rubric is not changed.
- **How many cases come out "not enough disclosed".** A choice-only S3 reading has one dimension, which S3's k* of 1
  allows; any case whose choice is unobservable falls below it.
- **Whether five `gpt-oss-120b` tasks at once draw more 429s than one.** §6.2's fallback covers it, at the cost of
  time.
