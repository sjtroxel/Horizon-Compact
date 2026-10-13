# Phase 4 — The Official Grid, runs half: IMPLEMENTATION (v0.4)

> **IMPLEMENTATION doc, runs half. APPROVED 2026-10-13, about 5:10 PM (his), all four decisions in §8 as
> recommended, (a).** Written by Opus the day `prereg-v1`
> was tagged, immediately before the runs, as the scope doc's split by code and runs requires (his, 2026-10-10).
> Sources: the Phase 4 scope doc (`docs/phases/phase-4-official-grid.md`, its six decisions as recorded), the code
> half's IMPLEMENTATION doc (all of it built), the protocol as tagged (`experiment/protocol/protocol-v1.md`, sections
> 4.7, 5, 7, 8, 9, 13 and 14), the Phase 3.5 IMPLEMENTATION doc sections 23-26, `KNOWN-GAPS.md`'s START HERE and its
> four OPEN entries that name Phase 4 or bear on it, `docs/phases/evidence/phase-3.5/model-facts.md` and
> `failure-proxy.md`, and the harness as built at `2eb818a` (`cli.py`, `protocol/gate.py`, `sweep/runner.py`,
> `sweep/plan.py`, `sweep/spend.py`, `sweep/awareness.py`, `sweep/status.py`, `providers/anthropic.py`,
> `analysis/records.py`, `analysis/results.py`, `analysis/repeats.py`, `.claude/settings.json`,
> `.github/workflows/deploy.yml`). **Decisions: §8, all four DECIDED (his).**
>
> **What this doc is.** Mostly a runbook: who runs what, in what order, what is read and by whom, and what stops a
> sweep. Four small run-code items come first (§5), because the runs cannot be done blind or complete without them.
> **Nothing frozen changes.** Every item is run code, docs or config; the lock's three sets and the protocol are
> untouched, and `hc protocol check` proves it on every commit.
>
> **Vocabulary.** A *sweep* is one pre-registered study on one model, with its own manifest and cost cap (protocol
> 13.2). The *reveal* is the moment any person first reads a decision by objective. A *session* is one container
> task working through a sweep; a sweep can take several sessions, each resuming where the last stopped.

## 1. Where things stand on 2026-10-13

- **`prereg-v1` is tagged** on `P` = `649e8b9b8f1dde0e3698be0d279b62fef07ad70b`; Phase 3.5 closed with `R`
  (`8e6be96`, CI `38358554814` green). The protocol, the content, the instrument and the analysis are frozen; the
  gate refuses an official sweep whose files differ from the lock.
- **The code half is built** (K1-K6): per-scenario repeats, the pilot and official prefixes, the pilot path and
  `repeats.json`, the official launch, the awareness sweep, the blind refusal calls, `hc analyze`, and the OpenRouter
  and Anthropic routes from the container. The name guard's push hook was fixed today (`2eb818a`, CI
  `38472714245` green).
- **The model set is the fallback set** (Phase 3.5 §23, protocol 5.1): **Haiku 5.5** (`haiku-5-5`, main, Anthropic's
  API, the prepaid credit) and **`gpt-oss-120b`** (`gpt-oss-openrouter`, second family, OpenRouter pinned to
  DeepInfra `bf16`, his cash). Sonnet 4.6 and Nova Pro are not in v1. The scope doc still names them; §10 step 1
  adds its dated note.
- **Nothing official exists.** No object under `official/` or `pilot/` (tag record §8). Haiku 5.5 has never been
  given the company's content.

## 2. What the runs half delivers

The scope doc's Delivers 1-10, for the fallback set:

1. **The pilot on each model** (protocol 8.1): 80 decisions, two development wordings, excluded from every result.
2. **The repeat count per model**, computed by the gate from its pilot (protocol 8.2-8.3), written once.
3. **The projection and the re-plan check**, committed before any grid run (scope decision 2).
4. **The grid on each model:** 4 scenarios, 5 objectives, 3 wordings (the sealed `w2` included), the computed
   repeats, one shuffled order from a recorded seed. Haiku with thinking off; `gpt-oss-120b` at its pinned reasoning
   level, `medium`, the only setting it has (protocol 5.3).
5. **The thinking sub-study** on Haiku 5.5 (protocol 9.5): S1, `w2`, five objectives, S1's grid count, the request
   §9.5 states.
6. **The awareness probe on each model** (protocol 9.6): 15 calls, after that model's grid.
7. **The blind refusal calls** for every sweep with a `no_tool_call` run, by him (code half decision 2).
8. **The record checks** (scope Delivers 10), as one command whose output is committed.
9. **The analysis, once per official sweep, from a checkout of the tag** (protocol 14), and the results files
   committed (scope decision 5).
10. **The measured cost**, from the records and then the three bills, replacing the estimates by dated patches.

**Not in this half:** the real cases (Phase 5 and 5.5); the explorer (Phase 6); any prose about the results (Phase 7,
his words); a model outside the lock; re-running anything that has a final result.

## 3. What writing this doc found

1. **The thinking sub-study cannot run as built.** The harness has no way to send §9.5's request (Phase 3.5 §3 item
   9). Worse, `check_repeats` refuses any plan that runs fewer scenarios than `repeats.json` names ("the pilot sets
   repeats for scenario(s) ... that this plan does not run", `gate.py:522`), and the sub-study runs S1 only. Its
   worst-case cost is also computed from the scenario's 3,072 output tokens, not the 16,000 it sends. §5.2.
2. **The official analysis runs from a checkout of the tag** (protocol 14: "with the tag's locked library
   versions"). So a run-code change to `hc analyze` made after the tag never reaches the official analysis. The OPEN
   entry asking `hc analyze` to check a sweep's model against the lock is therefore met in the record checks, run
   from `main` (§5.3), not in `hc analyze`. The tag's `hc analyze` takes `--root`, so its results file can be
   written into the main checkout.
3. **The run log names each run's objective** (OPEN 2026-10-11): `run 3/80 A attempt 1: no_tool_call`, in the task's
   CloudWatch log. The pilot is the first official-model run on the company's content, so this must be fixed before
   it, not before the grid. §5.1.
4. **`gpt-oss-120b`'s host is slow, and its pin is locked.** Valid calls took a median of 74 s, and 37 of 100
   attempts were HTTP 429 (`failure-proxy.md`). The runner makes one call at a time, so the grid is about a day of
   task time against a 30-minute default session. **The pin (`deepinfra/bf16`) is in the lock's model identity**, so
   changing host is `prereg-v2`, not a run-code fix. Time limits are the only lever: §6.4.
5. **A push that touches code rebuilds the image.** `deploy.yml` builds on any push to `main` that touches `src/`,
   `experiment/`, `infra/`, `pyproject.toml` or `uv.lock`. A re-launch after such a push runs a different image
   digest. So while any sweep is unfinished, nothing that triggers a deploy is pushed unless it is a logged run-code
   fix (§7). Committing the results files (under `experiment/results/`) also deploys; it comes
   after every run.
6. **The second family's placeholder check (Phase 3.5 §25.3), listed in START HERE as still to do, was done**
   on 2026-10-12 (§25.5: DeepInfra accepted `reasoning: {effort: medium}` on 5 of 5 calls). What is not yet shown
   is §5's changes and §9.5's request on the image the official sweeps will use. Decision 4.
7. **The commands that read pilot and official records are not denied to Claude.** `.claude/settings.json` denies
   `hc sweep run`, `launch`, `status`, `stop` and `aws`, but not `hc analyze`, `hc sweep report`, `hc sweep
   awareness`, `hc sweep refusals` or `hc protocol repeats`. §5.4 closes that, so Claude's blindness is mechanical
   as well as promised.
8. **The protocol still reads "DRAFT".** Its status line says "1 reviewed, 2 to 15 awaiting his review", and section
   2's and 4's bracket notes say "wait for build steps 7 and 8" and "written on tag day". All stale since the tag;
   all frozen. Protocol 14 allows exactly this kind of fix as an erratum in `errata-v1.md`, which no lock hashes.
   §10 step 2, before anything is published.
9. **Haiku's grid needs his over-cap flag.** Its preflight bound (every run at three attempts and full output) is
   $5.88 at 10 repeats and $7.84 at 20, above the $5 default, so the launch takes `--cap-usd` and `--allow-over-cap`,
   recorded in the manifest. Still far under the $25 official cap.
10. **`--repeats-file` reads a local file; `repeats.json` lives in S3.** One `aws s3 cp` per model, run by him. No
    build needed: the official launch and the task both check the plan against the S3 copy anyway.

## 4. The run set, fixed now

| Sweep | Model | What | Runs | Label | Seed |
|---|---|---|---|---|---|
| pilot | `haiku-5-5` | 4 scenarios x 5 objectives x `w1`, `w3` x 2 | 80 | `pilot` | 4096323239 |
| pilot | `gpt-oss-openrouter` | the same | 80 | `pilot` | 2323363371 |
| grid | `haiku-5-5` | 4 x 5 x `w1`, `w2`, `w3` x its repeats | 900-1,200 | `grid` | 541789037 |
| grid | `gpt-oss-openrouter` | the same, its own repeats | 900-1,200 | `grid` | 2451021948 |
| thinking | `haiku-5-5` | S1 x 5 x `w2` x S1's grid count | 30-100 | `thinking` | 3422206995 |
| awareness | `haiku-5-5` | S1 x 5 x 3, one call each, no tool | 15 | `awareness` | 1394052595 |
| awareness | `gpt-oss-openrouter` | the same | 15 | `awareness` | 3046959125 |

**Run counts.** S3 and S4 go to the cap, 20 (protocol 8.2). S1 and S2 take 6 to 20 from the pilot, so a grid is
15 x (n1 + n2 + 40) runs: 900 at 10 and 10, 1,200 at the cap.

**The seeds, drawn, not chosen** (scope decision 3; the same way as the sealed template, protocol 4.3). Each is the
first eight hex digits of sha256 over `P`'s full id, the model key and the sweep's label, read as an integer:
`python3 -c "import hashlib; print(int(hashlib.sha256(b'649e8b9b8f1dde0e3698be0d279b62fef07ad70b|haiku-5-5|grid').hexdigest()[:8], 16))"`
prints 541789037. `P` existed before this doc, so no seed could be tried out against a result. The seed fixes the
run order and every run's line order (protocol 4.4); the grid's sweep id also depends on the repeats, so it is
known only after the pilot.

**No other official sweep runs in v1 on the fictional company.** A sweep the gate refuses is not run under another
label (scope rules); §5.2 makes "one sweep per study per model" a check, as the code half did for pilots.

## 5. What is built before the first pilot

Four items, all run code or config. **Sonnet builds; Opus reviews each diff before he commits.** No model call and no
AWS call in any test. `make check` green after each.

### 5.1 The run log stops naming the objective (closes OPEN 2026-10-11)

- On a `pilot` or `official` session, the runner's progress line drops the objective id and keeps the run's position
  and status: `run 3/80 attempt 1: no_tool_call`. Development sessions keep today's line.
- The awareness sweep's line keeps its objective and wording: it runs after its model's grid, and its replies are
  quoted in full anyway.
- **Tests:** a pilot and an official session's progress lines contain no objective id (checked against every
  objective in the fixture); a development session's still do.

### 5.2 The thinking sub-study, and one sweep per study

The request protocol 9.5 states, sent only by a sweep labeled `thinking`. **The label is the switch**, so a resumed
session cannot quietly drop it: the label is in the sweep id and the manifest, and the manifest check refuses a
resume whose plan differs.

- **The request** (Anthropic route only): the grid's body with `thinking: {"type": "disabled"}` replaced by
  `thinking: {"type": "adaptive", "display": "summarized"}`, `output_config: {"effort": "high"}` added, and
  `max_tokens` 16,000. Held as constants, with a test that each appears word for word in `protocol-v1.md` §9.5. The
  pinned SDK (1.13.0) accepts all three as typed parameters (`ThinkingConfigAdaptiveParam` with `display`,
  `OutputConfigParam` with `effort`), checked 2026-10-13; nothing goes through `extra_body`.
- **Provenance:** `thinking` reads `adaptive, display summarized: sent`, `effort` reads `high`, and `max_tokens`
  16,000, on every attempt. The provider already counts thinking blocks (`reasoning_block_count`) and keeps them in
  the raw response; the frozen classifier reads only the stop reason, the tool calls and the text blocks, so it
  needs no change.
- **The plan:** an official plan labeled `thinking` must be `haiku-5-5` (the lock's `main` role), scenario `s1`
  only, template `w2` only, all five objectives. Anything else is refused, naming what differs.
- **The repeats:** `check_repeats` gains a sub-study mode. For a `thinking` plan, S1's count must equal the pilot's
  S1 count, and the other scenarios in `repeats.json` are not compared. Every other check stays.
- **The cap:** the preflight bound and the in-sweep worst case use the request's `max_tokens` (16,000 here), not the
  scenario's.
- **Storage:** under `official/company/<sweep_id>/`, like the grid, so the tag's `hc analyze` can read it; its own
  sweep id and label keep it from being merged with anything.
- **A development path for one test:** a `thinking` plan is also allowed on the `placeholder` experiment (off the
  subject; its one scenario, `garden`, and its one template, `w1`), never on the company's content outside the
  official sweep. That is how decision 4 tests the request.
- **One sweep per study per model:** an official launch or run refuses when the bucket already holds an official
  manifest with the same model and label under another sweep id (a resume of the same id is allowed). Labels for an
  official sweep are `grid`, `thinking` and `awareness`; `pilot` is the pilot's, as now.
- **`hc sweep tokens --sweep <grid> --vs <thinking>`:** for the report of §9.5's thinking cost. Per S1 `w2` cell,
  the mean output tokens of each sweep and their difference, and the share of sub-study runs with a thinking block.
  Reads token counts and block counts only, never a decision. Run at the reveal (§6.8), not before.
- **Tests, all on fakes:** the body has exactly the fields above and none of the never-sent ones; the constants
  match the protocol file; a `thinking` plan on another model, scenario or template is refused; S1-only repeats pass
  and a wrong S1 count is refused; the bound uses 16,000; a second official `grid` sweep on one model is refused and
  its resume is not; `hc sweep tokens` reads no `validation`, `tool_calls` or `text_blocks` field.

### 5.3 The record checks (scope Delivers 10; closes OPEN 2026-10-13)

`hc protocol records --store s3`, read-only, run by him from `main`. It writes
`docs/phases/evidence/phase-4/record-checks.md`, which holds counts, ids, hashes and dates, and no decision. It
reads manifests, session records and each attempt's provenance fields only, never `validation`, `tool_calls`,
`text_blocks` or `raw_response`.

| Check | Passes when |
|---|---|
| Content | every pilot and official manifest has the lock's experiment and content hash |
| **Model** | every pilot and official manifest's model is one of the lock's (**the OPEN entry's check**) |
| Labels | pilots are `pilot`; official sweeps are `grid`, `thinking` or `awareness`; at most one per model and label |
| Container | every pilot and official session ran on `fargate`, with an image digest and a clean git tree |
| Image | the digests used, per sweep, listed; **more than one digest in a sweep is reported** with its sessions |
| Request | grid attempts carry the locked `thinking` value; sub-study attempts carry §5.2's; `gpt-oss-120b` attempts were served by DeepInfra |
| Complete | every manifest run has a `final.json`; none unfinished |
| **The sealed template first** | no development or pilot manifest lists `w2`, and the earliest attempt carrying `w2` belongs to an official sweep (scope finding 5) |
| After the tag | every pilot and official object was written after the tag's Software Heritage visit, 2026-10-13T06:24:52Z |
| Frozen files | `hc protocol check` passes on the tree that ran the check |

Run counts per sweep, published for every sweep (protocol 13.2), come from the same pass: runs, finished, attempts
by status, sessions, cost by the records' own fields.

- **Tests, on a fake store:** each check fails on a fixture built to break it, naming the sweep; nothing in the
  output comes from a decision field (the fixture puts canary values there and the test looks for them).

### 5.4 Claude cannot read the records (config)

`.claude/settings.json` gains deny entries, in both the `uv run hc` and `uv run --no-sync hc` forms, for: `hc
analyze`, `hc sweep report`, `hc sweep awareness`, `hc sweep refusals`, `hc protocol repeats` and `hc protocol
records`. Then every command that reads a pilot or official record is his to run, and Claude sees only what he
pastes. **It does not stop** a Python snippet that calls boto3 directly. That remains covered by the honor statement
(§6.10), as in Phase 2.5.

### 5.5 As built (2026-10-13)

**[done] §5.1-5.4.** Sonnet built; Opus reviewed the whole diff. `make check` green, **2127 tests**; `hc protocol
check` passes (nothing in the lock's three sets changed). Each guarded line was mutated once (11 mutations across
5.1-5.3) and a test failed every time; every file was restored byte-identical.

- **5.1** `sweep/runner.py`: a pilot or official progress line carries no objective id; a development line does.
- **5.2** The constants live in `providers/base.py`, held word for word to protocol 9.5 by a test that reads
  `protocol-v1.md`. The Anthropic route alone builds the request; Bedrock, OpenRouter and the local runtime refuse
  it. `build_plan` refuses a `thinking` plan off the Anthropic route, and on the company's content unless it is
  official, on the `main` model, S1 and the sealed template only; the placeholder may run it as development.
  `check_repeats` compares S1 only for a `thinking` plan. One official sweep per study per model is
  `check_one_sweep_per_study`, on official `run` and `launch` (labels `grid` and `thinking`; the probe has its own
  command and is caught afterwards by the record checks). `hc sweep tokens` is `sweep/tokens.py`; it counts each
  run's final model attempt, failed runs included, so a truncated sub-study run counts at its full output.
- **5.3** `hc protocol records` is `protocol/recordcheck.py`. Two choices beyond the table: the image check is
  *reported*, never failed (more than one digest lists its sessions); "after the tag" reads each record's own
  `started_at`, since the store gives no write time. **Two faults found in review and fixed before commit:** the
  request check compared calls with the lock's wording, which OpenRouter's records word differently (`reasoning
  {effort: medium} sent` against `reasoning effort medium sent`), so every `gpt-oss-120b` call would have failed
  it; it now expects each provider's own text, from one function the provider also uses, and a test runs both
  providers to prove it. And a reply the DeepInfra pin refused (stored as `config_error`, never a result) no
  longer fails the host check.
- **5.4** The deny entries were added by him (`scratch/p4-deny.py`): Claude's auto mode refused to edit its own
  permission file, which is the right default. **One beyond the doc:** `hc sweep tokens` is denied too (token
  counts by objective are a view of the results). `tests/test_claude_settings.py` holds both forms of all seven.
  Denying `hc sweep awareness` means §6.0 step 4's awareness dry run is his to run.

## 6. The runbook

**His commands, one at a time.** Anything longer than one line goes in a `scratch/` script, as on tag day, with the
string to look for named. Claude reads only what he pastes. Each step starts when the one before it is done. Both
models run side by side from step 6.3 on: separate tasks, separate sweeps, nothing read across them. The second
family is the long pole either way.

### 6.0 The day before the first pilot (no model call)

1. §5's four items committed and pushed; **CI and Deploy green on that commit**. Its Deploy run's image digest is
   written into `docs/phases/evidence/phase-4/run-log.md`, which starts here (§7).
2. **Live checks, Claude's, from the vendors' pages:** Haiku 5.5 still served as `claude-haiku-5-5` at $0.10 and
   $0.50; its output limit at least 16,000; `gpt-oss-120b`'s `deepinfra/bf16` endpoint listed, at $0.037 and $0.17,
   with no reported fault. A price change changes cost only (prices are not in the lock). A missing model or host
   stops the plan for his decision.
3. **His readings, free:** the Anthropic Console (the credit balance; the `horizon-compact` workspace's spend this
   month against its $10 limit); OpenRouter (this project's spend to date against his $5 cap); AWS Billing (the
   credit balance). Claude writes them into `run-log.md`.
4. **Dry runs, local, nothing called:** `hc sweep run --dry-run --pilot` for each pilot, and `hc sweep awareness
   --dry-run` for each model. Expect `every check passes`.

### 6.1 The placeholder check on the final image (decision 4)

On `placeholder` (off the subject), as development sweeps, under the $5 development cap:

The placeholder is one scenario, five objectives and one template, so `--repeats 3` is 15 runs, the skeleton's shape.

- `haiku-5-5`, `--repeats 3`, label `final`: 15 runs, about $0.015 of the credit, a few minutes;
- `haiku-5-5`, label `thinking`, `--repeats 1`: 5 runs, up to about $0.04 of the credit (thinking output);
- `gpt-oss-openrouter`, `--repeats 3`, label `final`: 15 runs, about $0.004 of his cash, about 20 minutes.

**What Claude reads** (placeholder records may be read in full; they carry nothing about the subject): the progress
lines (no objective on a development run is expected; §5.1 is shown on the pilot's log instead); the `thinking`
runs' request bodies, stop reasons, `reasoning_block_count`, output tokens and cost; that a tool call was made with
thinking on; the image digest. **If the API refuses the thinking request,** the sub-study stops here for his
decision, before anything official runs; the grid is not affected.

### 6.2 The pilots

Two launches (scripts `scratch/p4-pilot-<model>.sh`):

`hc sweep launch --experiment company --model <key> --repeats 2 --seed <seed> --label pilot --template w1 --template w3 --pilot --cap-usd 1 --max-minutes <m>`

- `--max-minutes` 60 for Haiku (80 calls at about 7-10 s); 300 for `gpt-oss-120b` (80 calls at about 75 s, plus
  429s).
- **Watched with** `hc sweep status --role pilot --sweep-id <id>`: counts by status, attempts, cost. No allocation
  and no objective (scope decision 1).
- **Then, for each:** `hc protocol repeats --pilot <id> --store s3`. It prints, per scenario, the pooled spread, the
  count and the rule that set it, and writes `repeats.json` once. He pastes the output; Claude writes
  `docs/phases/evidence/phase-4/pilot-<model>.md` from it and from the status output. That file holds the pilot
  report's whole content: per scenario, spread, repeats, binding rule and precision at the cap; pooled over
  objectives, the final statuses, the first-attempt statuses and the cost. Nothing else from the pilot is read,
  ever, until the reveal.

### 6.3 The projection and the re-plan check (scope decision 2)

Claude computes, and writes `docs/phases/evidence/phase-4/projection.md`:

- **Measured cost per attempt and attempts per run**, from each pilot's status (cost over attempts, attempts over
  runs).
- **The fixed run set** (§4, with the counts now known) at those rates, plus 20% for retries, per sweep. For the
  sub-study, at Haiku's thinking-on cost from §6.1's check.
- **Phase 5's estimate** (Phase 3.5 §23.4: real cases about $1.20 on Haiku and about $0.35 on `gpt-oss-120b`,
  extraction about $0.50).
- **Against four lines:** the $60 re-plan point and the $80 ceiling (all spend, every pot, summed); the credit's
  balance and the workspace's $10 a month; his OpenRouter cap ($5 in all, so what is left of it); the AWS credit
  balance, for Fargate and S3.
- **Each sweep's cap:** set at its preflight bound rounded up, which the launch requires, and checked to fit under
  each pot's remaining room. If the OpenRouter caps cannot fit what is left of his $5, he decides before the grid:
  raise his cap, or cut by the pre-registered order (the second family first, `planning/05` §5.1).

**Expected, from the measurements so far:** Haiku about $0.0013 a call (about 6,000 input and 1,300 output tokens),
so the pilot about $0.11, the grid $1.25-1.70, the sub-study $0.10-0.50, the probe $0.01: **about $1.5-2.3 of the
credit**. `gpt-oss-120b` about $0.0005 a call: **about $0.50-0.70 of his cash** with OpenRouter's 5.5% fee. Fargate:
about 40 task-hours at about a cent an hour, **about $0.40 of AWS credit**. So v1's total stays far under $60, and the
check is expected to pass. It is still made and committed, because the scope decision is about when it is made, not
about what it is expected to find.

**He commits `projection.md` and pushes it** (docs only: no deploy) **before the first grid launch.** That commit's
time is the record that the run set and the caps were fixed before any official result existed.

### 6.4 The grids

For each model: `aws s3 cp` its `repeats.json` to `scratch/repeats-<model>.json`; a dry run; then the launch:

`hc sweep launch --experiment company --model <key> --repeats-file scratch/repeats-<model>.json --seed <seed> --label grid --official --pilot-sweep <pilot id> --cap-usd <cap> [--allow-over-cap] --max-minutes <m>`

- **Haiku:** cap from §6.3 (about $8-9, so `--allow-over-cap`); `--max-minutes` 300. About 2.5-3.5 hours.
- **`gpt-oss-120b`:** cap from §6.3 (about $3); `--max-minutes` 720. About a day of task time; expect two or three
  sessions, each resumed by the same command.
- **Watched** with `hc sweep status --role official --sweep-id <id>`, a few times a day. A session that stops is
  re-launched with the same command; it resumes by run id and re-runs nothing that has a final result (protocol
  13.2). Each stop and re-launch is a line in `run-log.md`.

### 6.5 After each model's grid: the sub-study and the probes

- **The thinking sub-study** (Haiku, after Haiku's grid is complete):
  `hc sweep launch --experiment company --model haiku-5-5 --scenario s1 --template w2 --repeats <S1's count> --seed 3422206995 --label thinking --official --pilot-sweep <Haiku's pilot id> --cap-usd <cap> --max-minutes 180`.
- **The awareness probe** (each model, after its own grid): `hc sweep awareness --experiment company --model <key>
  --seed <seed> --launch --cap-usd 1 --max-minutes <m>` (60 for Haiku, 120 for `gpt-oss-120b`). Its report is not
  read until the reveal.

### 6.6 The refusal calls (protocol 4.7; code half decision 2, his)

For each finished official sweep with a `no_tool_call` run (the grids and the sub-study; status shows the count):
`hc sweep refusals --experiment company --sweep <id> --made-by sjtroxel`. Cases come shuffled and masked, with the
reply's text only. He answers each, and the file is written once. If a sweep has no `no_tool_call` run, there is
nothing to call and no file, and `hc analyze` allows that. Claude does not see the screen. The calls are made
before any record check or analysis, and before the reveal.

### 6.7 The record checks

`hc protocol records --store s3` (§5.3), after every sweep in §4 is complete and every refusal file written. **Any
failed check stops the phase before the reveal**, for diagnosis. A failure found now is found before anyone knows
what the results say.

### 6.8 The reveal: the analysis from the tag

From a detached worktree of `prereg-v1` with its own environment (`uv sync --frozen`), as on tag day (tag record
§7), so the code and libraries that compute every verdict are the tag's (protocol 14):

`uv run hc analyze --experiment company --sweep <id> --store s3 --root <the main checkout>`

once for each grid and once for the sub-study. Each writes
`experiment/results/prereg-v1/<model>/<sweep id>.json` in the main checkout, never overwritten. Then, from `main`:
`hc sweep awareness --report` for each model, into `docs/phases/evidence/phase-4/awareness-<model>.md`, and `hc
sweep tokens` (§5.2) for the sub-study's thinking cost. **This is the first time anyone reads a decision by
objective** (decision 1). He commits the results files and the evidence. The results files deploy an image, which
is harmless now.

### 6.9 The measured cost

From the record checks' per-sweep totals; then the bills: the Console's usage for the workspace, OpenRouter's
activity for the key, and AWS Cost Explorer (credits included and excluded). Dated patches to `planning/03` and
`planning/07` §13, and the ROADMAP's cost column. The $60 point is checked against measured spend (scope DoD 8).

### 6.10 The close

The DoD audit (§11), the honor statements (his in his words, Claude's in Claude's: no decision read before §6.8,
and anything seen by accident disclosed), KNOWN-GAPS and START HERE, and the ROADMAP row. `pyproject.toml`'s version stays `0.0.5` until Phases 1 and 1.5
close (Phase 2 decision 4); it is in every record as `harness_version`, so it must not change mid-run anyway.

## 7. During the runs

**The push freeze: one image per sweep.** A session runs whatever image the latest deploy built, and a push to
`main` that touches `src/`, `experiment/`, `infra/`, `pyproject.toml` or `uv.lock` builds a new one. So **while any
pilot or official sweep is unfinished**, no such push is made, except a run-code fix for an infrastructure fault,
logged below. That keeps every sweep on one image digest, which the record checks confirm.

- **What it does not block:** commits on the laptop; pushes that touch only `docs/` (no deploy), which is most of
  what this phase pushes (the run log, the pilot reports, the projection); and code pushes **between** sweeps, when
  none is unfinished, logged in the run log with the new digest. In this plan the second family's sweeps overlap
  Haiku's, so the only such gap is between the pilots and the grids.
- **How long it lasts:** from the first pilot launch to the end of the last awareness probe, about two days in this
  plan, most of it `gpt-oss-120b`'s grid. It never covers §5's build, which comes before the first pilot, nor the
  results commit at the reveal, which comes after the last session.

**The run log** (`docs/phases/evidence/phase-4/run-log.md`): every launch, stop, re-launch and fix, with time, sweep
id, session, image digest, and what was seen (statuses and costs only). **Run-code fixes** get a row each: the
commit, the file, the cause, and the effect on runs ("none", or which runs ran before and after it). A fix is made
only for an infrastructure fault, never because of what a model answered. Instrument and analysis code are never
touched; a change there is `prereg-v2`.

**What stops a sweep, by name** (the runner's own stop reasons), and what follows:

| Stop | Meaning | What he does |
|---|---|---|
| `complete` | every run has a final result | next step |
| `max_minutes` | the session's time limit | re-launch, same command |
| `stop_requested` | `hc sweep stop` | re-launch when ready |
| `api_errors` | 10 API errors in a row (the host's 429s, a network fault) | wait about 30 minutes, re-launch |
| `cap_reached` | the next attempt's worst case would pass the cap | stop; Claude checks the spend against the projection; raising the cap is his flag, recorded |
| `config_error` | 401 or 403, a malformed request, an unknown error | stop; diagnose; fix if run code (logged); re-launch |
| `SpendLimitReached` (a `config_error`) | the workspace's $10 a month, or the credit, is used up | stop; read the Console; raising the workspace limit is his decision |
| `ProviderMismatch` (a `config_error`) | a reply from a host other than DeepInfra | stop; nothing from that reply counts; resume only once DeepInfra serves the pin |
| `write_conflict` | an object exists that should not | stop; diagnose before anything else (two tasks on one sweep is the likely cause) |
| `crashed` | the task ended without a clean stop | read the log; re-launch; it resumes |

**What never stops a sweep:** a model's failures or refusals, at any rate (scope rules: failures are outcomes).
**What ends a sweep as partial:** the model or the pinned host withdrawn (protocol 5.1; the pin is locked). It is
reported as partial, never finished on another model or host. **If the repeat rule cannot be applied** (a share
scenario's pilot cells have no two valid runs, `RepeatRuleError`), that model's grid does not run in v1, and the
finding is reported.

## 8. Decisions for him

Each has a recommendation and a reason. What is not here is settled by the scope doc, the protocol or the code half.
**All four DECIDED 2026-10-13, about 5:10 PM (his): (a), as recommended.**

1. **DECIDED (his): (a). When results are first read.**
   - (a) **Recommended: one reveal, after every sweep in §4 has finished, every refusal call is made and the record
     checks pass.** Until then nobody reads anything by objective: not an allocation, a choice, a memo, an awareness
     reply or a results file. The reason: Haiku's grid finishes about a day before `gpt-oss-120b`'s. If Haiku's
     results were read in that gap, every remaining operational choice on the second family (a fix, a stop, a cap,
     a cut) would be made by someone who knows the main model's answers. The cost is about a day of waiting.
   - (b) Per model, as each finishes. Haiku's results a day sooner; the second family's run is then conducted by
     someone who has seen the main result.
2. **DECIDED (his): (a). How the raw responses are published** (protocol 13.1: "every raw response on the fictional company is
   published in full"; it sets no date).
   - (a) **Recommended: at this phase's close, commit a manifest of every pilot and official object** (key, bytes,
     sha256), and publish the full text with the publish path (Phase 1.5, or 6.5 at the latest), scanned by the name
     guard as text. The manifest timestamps the raw record publicly now, and the bucket is write-once with
     versioning. Full text is about 100 MB (about 35 KB an attempt, the prompt included), too large to put in git
     well. A model's memo could also name a real company, and the guard scans text, not archives.
   - (b) Commit every raw response now, as text, under `experiment/results/`. Complete at once, but it adds about 100
     MB to the repository for good.
3. **DECIDED (his): (a). How the thinking sub-study is reported** (protocol 9.5 asks "does thinking change what an objective does?"
   and states no test).
   - (a) **Recommended: with the frozen code only.** `hc analyze` on its sweep gives S1's verdicts with thinking on.
     They are reported beside the grid's own "sealed wording only" result for S1 (protocol 9.2), which is the same
     scenario, wording and repeats with thinking off, comparison by comparison, plus `hc sweep tokens`'s thinking
     cost. No new test, so nothing is computed that the protocol did not fix.
   - (b) Add a test of thinking on against off. It would be new analysis after the tag, so it is exploratory, labeled
     so, and can never stand beside the pre-registered results as one of them.
4. **DECIDED (his): (a). The placeholder check on the final image** (§6.1).
   - (a) **Recommended: run it.** About $0.055 of the credit and $0.004 of his cash. It is the only place §9.5's
     request meets the real API before the official sub-study, and it shows the final image end to end on both
     routes. If the thinking request fails there, it fails on garden text, with nothing official spent.
   - (b) Skip it, and let the official sub-study be the first real thinking call. If the request is refused then, the
     sub-study is stopped with a refusal in its record.

## 9. Rules this half must not break

The scope doc's rules hold as written. In particular: nothing outside the protocol is official; the run set is fixed
before the first official run (§4, §6.3) and never changed by what the runs show; a model's failures are outcomes;
no model, host or reasoning level changes mid-grid (all are in the lock); every result is published, whichever way it
falls; rule zero holds (the content is the fictional company's; a memo that names a real company is held back from
any publication and counted). And from this doc: Claude runs no command that reads a pilot or official record
(§5.4); nobody reads a decision by objective before the reveal (decision 1); the analysis runs from the tag (§6.8).

## 10. Order of work

1. **[done] [Opus] This doc**, approved by him (2026-10-13); with it, the scope doc's dated note (the fallback set's models, run set and
   cost), `KNOWN-GAPS.md` START HERE (with `R`'s CI run id, `38358554814`), and the ROADMAP row. One commit:
   `phase 4: runs-half implementation doc`.
2. **[done, `ccbfcaa`] [Opus] `errata-v1.md`** (finding 8): the status line and the stale bracket notes, each with what it should say;
   no computation, content or rule changed. Reviewed by him; committed before the first pilot.
3. **[done 2026-10-13, built and reviewed; his commit, push and digest next] [Sonnet] §5.1-5.4** (§5.5), one commit each or together; Opus reviews each diff. `make check` green; he commits and
   pushes; Deploy green; the digest recorded (§6.0).
4. **[him, Claude reading] §6.0-6.10**, in order.

**Model choice:** Sonnet for step 3; Opus to review it and for the reveal's reading. The runs themselves need little
of either, since Claude only reads pasted status lines.

## 11. Definition of done, and the proof of each

The scope doc's DoD, for the fallback set:

1. **The pilots ran and are excluded:** under `pilot/`; no results file reads them (`hc analyze` has no pilot role).
2. **The repeats came from the pilots by the gate, and the projection was committed before the first grid run:**
   each `repeats.json`; `projection.md`'s commit time against the grid's first session.
3. **The grid ran on Haiku 5.5 under the protocol:** the record checks; run counts, failure and refusal rates per
   cell, and first attempt beside final, in its results file.
4. **The thinking sub-study and both awareness probes ran,** or the reason one did not is recorded (decision 4's
   failure case).
5. **`gpt-oss-120b`'s grid ran,** or is reported as partial or cut, with the reason.
6. **The frozen analysis produced every verdict:** three results files from the tag's worktree, committed.
7. **The record checks pass** (§5.3), committed.
8. **Measured cost replaces the estimates,** confirmed against the three bills; the $60 point checked.
9. **`make check` and CI green.**

## 12. Cost

**Building §5: $0.** **The runs: about $1.5-2.3 of the prepaid Anthropic credit, about $0.50-0.70 of his OpenRouter
cash, and about $0.40 of AWS credit**, plus decision 4's $0.06. Measured, not estimated, at §6.3, and committed
before the grid.

**Time:** about a day of build and review for §5; then about two days of run time, set by `gpt-oss-120b`'s grid,
watched a few times a day; the reveal and close about half a day.
