# Phase 4 — The Official Grid, code half: IMPLEMENTATION (v0.4)

> **IMPLEMENTATION doc, code half.** Written 2026-10-10 (Opus) after Phase 4 was split by code and runs (his,
> 2026-10-10; ROADMAP decision history; the scope doc's dated note). Sources: the Phase 4 scope doc
> (`docs/phases/phase-4-official-grid.md`, its six decisions as recorded), `KNOWN-GAPS.md` START HERE and the four
> OPEN entries that name Phase 4, the protocol draft (`experiment/protocol/protocol-v1.md` §4.7, §7, §8, §9.5, §9.6,
> §13), the Phase 3.5 IMPLEMENTATION doc §5 (the frozen sets), §15 decision 5 (the fallback set) and §16, the
> Phase 1 IMPLEMENTATION doc §16 (what is built and what waits), and the harness as built (`sweep/plan.py`,
> `sweep/launch.py`, `sweep/runner.py`, `sweep/prompt.py`, `protocol/gate.py`, `protocol/sets.py`,
> `analysis/records.py`, `analysis/results.py`, `analysis/failures.py`, `providers/base.py`,
> `providers/openrouter.py`, `cli.py`, `infra/iam/task.json`, `infra/iam/boundary.json`). **APPROVED 2026-10-10 (his),
> all five decisions in §6 as recommended, (a).**
>
> **Everything here is built and tested on fakes, with no model call and no AWS call.** Two items end in a
> Terraform change he applies (§4.2, §4.8). Those touch IAM and SSM only, never Bedrock, and cost nothing.
>
> **Vocabulary.** A *pilot* is a small trial run whose only job is to measure how noisy the answers are, so the main
> run's size can be set by rule; it is never part of a result. A *refusal call* is a person reading a reply in which
> the model did not submit a decision and judging whether it declined on purpose.

## 1. Where things stand on 2026-10-10

- **Phase 3.5's no-AWS work is done** (`183421f`); the protocol's six drafting choices were decided 2026-10-10. Its
  remaining steps and the tag wait on Bedrock, with a fallback set if Bedrock is still dark on 2026-10-16
  (tentative, his).
- **The harness runs development sweeps only.** `sweep_prefix` writes under `development/` and nowhere else; every
  final record says `"label": "development"`; `hc sweep launch --official` runs the gate's checks 1-7 and then refuses
  ("not wired yet"); the plan takes one repeat count for the whole sweep; nothing reads a whole sweep into the
  analysis engine from a command; nothing writes `repeats.json` or `refusal-calls.json`.
- **No Fargate task has ever run.** The `main` stack is deployed and its permission check passed (Phase 1 step 8),
  but step 9, the first real task, waits on Bedrock. `launch` refuses an OpenRouter model outright.

## 2. What this half delivers

The run code the scope doc's runbook needs, so that on run day the work is typing commands, not writing code:

1. **Per-scenario repeats** in the plan, the manifest and the command line (§4.1).
2. **The pilot and official prefixes and labels** in the store and the records, with the IAM change (§4.2).
3. **The pilot path:** `--pilot` through `run` and `launch`, the gate's pilot mode, and `hc protocol repeats`, which
   writes `repeats.json` once (§4.3).
4. **The official launch:** `--official` (and `--pilot`) forwarded to the task, and the launch refused unless the
   plan's repeats equal `repeats.json`'s (§4.4).
5. **The awareness probe** as its own sweep kind: the prompt variant, a request with no tool, its records (§4.5).
6. **The blind refusal-call workflow** (§4.6).
7. **`hc analyze`:** a whole finished sweep into the frozen engine and out as a versioned results file (§4.7).
8. **OpenRouter from the container,** the fallback set's route, built now so it is ready either way (§4.8;
   decision 4).

**Not in this half:** the thinking sub-study's request fields (decision 5); every model call; the projection and
re-plan check (arithmetic done on run day from the pilot); the record checks of Delivers 10 (they read real
objects).

## 3. What writing this doc found

1. **Half of this work touches files frozen at the tag, so it must land before the tag.** The awareness probe's
   prompt variant belongs in `sweep/prompt.py` (instrument), and the results file's writer in `analysis/`
   (analysis). Both sets are hashed into the lock at `prereg-v1`; a change after it is `prereg-v2`. Everything else
   here is run code and could come later, but building it all now keeps it in one piece. **This half's deadline is
   therefore the tag, not the grid.**
2. **The task role can write only under `development/`** (`infra/iam/task.json`), and the permissions boundary allows
   `development/` and `official/` but not a pilot prefix. Official and pilot sweeps from the container need an IAM
   change, applied by him before the first pilot (decision 1).
3. **Nothing serializes the results object.** `build_results` returns a `ModelResults` dataclass with
   `RESULTS_VERSION 2`; Phase 4 decision 5 commits "the published JSON", and Phase 1.5 owns the publish path. The
   writer has to be frozen with the analysis, so it is built here; Phase 1.5 then reads the file this writes
   (decision 3).
4. **The awareness probe cannot use today's request type.** `DecisionRequest` requires a tool, and both providers
   always send one. The probe offers none (protocol §9.6), so the seam needs a request that carries no tool. This is
   run code (`providers/` is run), but the prompt it sends is instrument.
5. **A blind refusal call is only partly blind.** The objective can be hidden from the reader's screen, but a reply
   can name it ("as instructed to maximize shareholder value..."). The workflow hides every field and the prompt,
   and the protocol's limit is stated in the record rather than claimed away.
6. **Building the container's OpenRouter route also unblocks Phase 1 step 9.** With it, a placeholder sweep on the
   development model can run as a real Fargate task for about a cent of his OpenRouter balance, and prove the
   container end to end (digest, write-once, resume) before anything official depends on it. Today that proof waits
   on Bedrock.

## 4. The items

### 4.1 Per-scenario repeats

- `SweepPlan.repeats` becomes a mapping, scenario id to count (`build_plan(..., repeats: int | Mapping[str, int])`;
  an int means the same count everywhere, so every development command keeps working unchanged).
- `MANIFEST_VERSION` 3: `repeats` is written as the mapping. The sweep id hashes the mapping in scenario order, so two
  plans that differ in one scenario's count are two sweeps. A version-2 manifest is still read (the runner's resume
  check and `records.read_runs`), with its int read as the same count everywhere.
- `--repeats-file <path>` on `plan`, `run` and `launch` reads a `repeats.json`'s mapping; `--repeats N` stays; both
  given is an error.
- **Tests:** the mapping expands to the right run count per scenario; ids are stable; the old manifest still resumes;
  a missing scenario in the mapping is refused naming it.

### 4.2 Pilot and official prefixes and labels

- `sweep_prefix(experiment, sweep_id, role)` with role `development`, `pilot` or `official`:
  `development/<exp>/<id>/`, `pilot/<exp>/<id>/`, `official/<exp>/<id>/`. The final record's `label` is the role,
  not the constant `"development"`.
- **Terraform, his to apply:** `task.json` and `boundary.json` gain `pilot/*` and `official/*` on the same actions as
  `development/*`. No Bedrock permission changes.
- **Tests:** each role writes only under its prefix; the reader refuses nothing new (it already refuses only
  non-placeholder `development/`); a policy test that the JSON grants exactly the three prefixes.

### 4.3 The pilot path

- `--pilot` on `hc sweep run` and `launch`: the plan's label must be `pilot`, the gate runs with `pilot=True`
  (already built), and the session writes under `pilot/`.
- `hc protocol repeats --pilot <sweep_id>`: reads the pilot's records, calls `required_repeats` (built), and writes
  `RepeatDecision.as_record()` to `pilot/<exp>/<id>/repeats.json` with write-once (`put_new`). A second write is
  refused, never overwritten. It prints per scenario only what the record holds: the pooled spread, the count, the
  binding rule. No mean, no objective (scope decision 1).
- **Tests:** a fake finished pilot gives the worked example's counts (protocol §8.2: sd 0.15 gives 20, sd 0.10 gives
  10); an unfinished pilot is refused; a second write is refused; the printout has no objective id in it.

### 4.4 The official launch

- `cmd_sweep_launch` stops refusing after the laptop's gate checks. The container command carries `--official` or
  `--pilot`, and `--repeats-file`'s mapping as `--repeats-json '<json>'` (the task has no copy of the laptop's file).
- An official launch reads `repeats.json` from the pilot's prefix and **refuses unless the plan's repeats equal it**
  (protocol §8.3). An official run in the container (`hc sweep run --official`) checks the same, so a hand-typed
  task command cannot skip it.
- **Tests:** the built command contains `--official`, with a test that fails if it is dropped (the OPEN entry's
  test); a plan whose repeats differ from the file by one scenario is refused naming it; a missing file is refused.

### 4.5 The awareness probe

Protocol §9.6: S1, every objective under every template, one call each, 15 per model, after the grid; no tool; the
instruction replaced by the frozen question.

- **Instrument (before the tag):** `prompt.render_awareness_prompt(...)`, which is `render_prompt` with the
  scenario's instruction replaced by the protocol's text, word for word, held as a constant with a test that it
  matches the protocol file.
- **Run code:** a `TextRequest` (system, user, max tokens; no tool) and `decide_text` on both providers; Bedrock's
  Converse call without `toolConfig`, OpenRouter's body without `tools`.
- `hc sweep awareness --model <key> --seed <n>`: its own sweep id and manifest (scope decision 4), under
  `official/<exp>/awareness/<id>/`, write-once records holding the reply text, resume like a sweep, no retry of a
  model reply (a reply is the measurement), an API error retried with backoff. Its report quotes every reply in full,
  by objective and template, since it runs after the grid and filters nothing.
- **Tests:** the prompt equals the grid prompt except the instruction; no tool is sent by either provider (body
  inspected); 15 runs planned; resume skips finished calls.

### 4.6 The blind refusal-call workflow

Protocol §4.7: one file per sweep, made with the objective hidden, once, before any official analysis.

- `hc sweep refusals --sweep <id>` lists every run whose final status is `no_tool_call`, **in a shuffled order**,
  each with a short masked label (`case 1`, `case 2`...) and its reply text only: no run id, objective, wording,
  prompt or classifier flag on screen. A private mapping from label to run id is held in memory only.
- It asks for each case: refusal or not, and a one-line reason. Then it writes `refusal-calls.json` beside the sweep,
  write-once, naming only the runs called refusals, with a header recording who made the calls, when, and the
  stated limit (finding 5). A second write is refused.
- `hc analyze` (§4.7) refuses to run on an official sweep that has `no_tool_call` runs and no `refusal-calls.json`,
  so the order "calls first, analysis second" is code.
- **Who makes the calls** is decision 2.
- **Tests:** the screen output holds no objective id, wording id or run id (checked against every fixture value);
  the file names only `no_tool_call` runs; a second write is refused; analysis is refused without the file.

### 4.7 `hc analyze`

- `hc analyze --sweep <id> [--store s3|local]`: `read_runs` gives the `RunSet`; `read_refusal_calls` gives the calls;
  **`build_results(experiment, runset, calls=...)` is passed the `RunSet` itself**, so its unfinished-runs refusal
  cannot be skipped (the OPEN entry). A test calls the command on a half-finished fake sweep and expects the refusal.
- **Analysis (before the tag):** `results.to_record(ModelResults) -> dict`, stable key order, floats as written,
  `results_version` first, and `results.write_results(...)`. One file per model per sweep, written to
  `experiment/results/<protocol>/<model>/<sweep_id>.json` in the repo (inside an existing folder, so the root cap is
  untouched), to be committed by him (scope decision 5).
- **Tests:** round trip of a fake sweep's results through the record; the same input gives byte-identical output;
  development prefixes on real content are refused, as today.

### 4.8 OpenRouter from the container (the fallback route)

Phase 3.5 decision 5's design change, built now.

- **The key:** an SSM Parameter Store `SecureString` named `/horizon-compact/openrouter-key` (standard tier, free;
  the AWS-managed key, free). He creates its value by hand in the console, so the key never passes through a file,
  a command line or Terraform state. Terraform creates the task role's permission to read that one parameter, and
  only that, and the boundary gains the same. *Checked at build, not assumed here:* whether reading a
  `SecureString` under the AWS-managed key needs an explicit `kms:Decrypt` grant, from AWS's documentation on the
  day.
- **The provider:** `read_key` gains a third source, SSM, used only in the container. **Provider pinning:** the body
  sends `provider: {order: [<named provider>], allow_fallbacks: false}` from `models.toml`, so OpenRouter can never
  silently serve the call from a different backend; the serving provider from the reply is recorded per call, and a
  reply from any other provider is a recorded `api_error`, never a result.
- **`launch`** allows an OpenRouter model once its config names a pinned provider.
- **Tests:** the body carries the pin; a reply from another provider is refused; the key never appears in a stored
  body, an error or a log (the existing scrub tests extended to the SSM path); IAM grants read on exactly one
  parameter.
- **Then, his choice, about a cent of his OpenRouter balance:** Phase 1 step 9 on the placeholder as a real Fargate
  task with the development model, which proves the container end to end (finding 6).

## 5. Rules this half must not break

- **No model call and no AWS call in any test.** Every provider, store and AWS client is a fake.
- **No real content on an official model.** Nothing here runs a sweep; the refusals in `check_not_official_rules`
  are unchanged.
- **The frozen-set files change only before the tag**, and each change lands with its test.
- **Rule zero.** Fixtures use the placeholder and canary names only.
- **`make check` before every commit; CI green.** He runs `git commit`, `git push` and `terraform apply`.

## 6. Decisions for him

Each has my recommendation and why. **All five DECIDED 2026-10-10 (his): (a), as recommended.**

1. **Where pilot records live.**
   - (a) **Recommended: a top-level `pilot/` prefix**, with the IAM change in §4.2. Pilot records can never be mixed
     into official results by a careless prefix, which is what scope decision 1 asks for. Costs one small Terraform
     change, applied by him.
   - (b) Under `official/<exp>/pilot/`. No change to the boundary, but one wrong path and the pilot sits beside the
     grid.
2. **Who makes the refusal calls.**
   - (a) **Recommended: him, through the blind screen** (§4.6). The protocol says "a person", the question is plain
     ("did the model decline on purpose, or just fail to use the tool?"), and needs no finance knowledge. Likely a
     handful of cases, or none; about ten minutes.
   - (b) Claude, in a session given only the blind screen's output. Faster for him, but the protocol's "human call"
     would then need a wording change before the tag, and a reviewer may read an AI call as less independent.
3. **The results file's writer.**
   - (a) **Recommended: built here, in `analysis/`, before the tag**, since it must be frozen with the analysis.
     Phase 1.5 reads the file.
   - (b) Left to Phase 1.5. Then it is built after the tag, outside the frozen set, and "the published numbers came
     from the frozen code" has one unfrozen step in it.
4. **Build the container's OpenRouter route now.**
   - (a) **Recommended: yes**, at $0 to build. It is the fallback set's only way to run officially, it unblocks the
     first real Fargate task, and it is ready if 2026-10-16 arrives with Bedrock still dark. If Bedrock answers, it is
     unused but costs nothing to keep.
   - (b) Wait until the fallback date decides it. Saves about half a day if Bedrock answers; costs that half day
     under deadline pressure if it does not.
5. **The thinking sub-study's request fields.**
   - (a) **Recommended: not built now.** The sub-study is cut under the fallback set, its exact request fields wait
     on build step 9's live reading, and its code is run code that can be added after the tag. Building it now risks
     code for a study that does not run.
   - (b) Build the plumbing now with placeholder fields.

## 7. Order of work

Items that touch frozen files first, so the tag is never waiting on them. **Sonnet builds; Opus reviews each
commit's diff before he commits** (the arrangement he called "exactly what we wanted", 2026-10-09).

1. **[done 2026-10-10, `24b40c5`]** §4.5's instrument part (`render_awareness_prompt`) and §4.7's analysis part
   (`to_record`, `write_results`): the frozen files, first.
2. **[done 2026-10-10, K3]** §4.1 per-scenario repeats.
3. **[done 2026-10-10, K3; boundary applied by him]** §4.2 prefixes and labels; the IAM JSON change (he applies).
4. **[done 2026-10-10, K3]** §4.3 the pilot path; §4.4 the official launch.
5. §4.5's run part (the text request, `hc sweep awareness`).
6. §4.6 the refusal workflow; §4.7's command.
7. §4.8 the container's OpenRouter route (if decision 4 is (a)); the SSM parameter he creates; then, his choice,
   Phase 1 step 9 on the placeholder.

About a day of build with tests, in line with START HERE's estimate; §4.8 about half a day of it.

**As built, 2026-10-10 (steps 1-4; Sonnet built, Opus reviewed each).** `make check` green at 1457 tests.

- **Step 1.** `AWARENESS_INSTRUCTION` is held equal to protocol §9.6's block quote by a test that reads the protocol
  file. `write_results` writes with `\n` line endings, refuses NaN, infinity and any type JSON cannot hold, and never
  overwrites a different result (an identical rewrite is a no-op). The protocol name is an argument: `analysis/` may
  not import `protocol/`.
- **Step 2.** One count everywhere hashes into the sweep id exactly as before, so stored development sweeps keep their
  ids; a version-2 manifest resumes. A repeats file that misses a scenario, names one the plan does not run, or holds
  a count that is not a plain whole number is refused (Opus's review removed a silent `int()` conversion). Added
  beyond the doc: `--repeats-json`, how `launch` hands a mapping to the task.
- **Step 3.** `sweep_prefix(..., role)`; every record's `label` is the role. `hc sweep run --official` now writes under
  `official/`. `status` and `report` take `--role`. **Moved, by design:** the task role can now write `official/`,
  so the only guard on an official write is the code gate, no longer IAM.
- **Step 4.** Added beyond the doc: **`--pilot-sweep <id>`**, required with `--official`, names the pilot whose
  `repeats.json` must match (the doc did not say how the pilot is found). A pilot builds its plan as official (else
  `build_plan` refuses the official model on real content); the gate's pilot checks still apply. The check also
  requires the record's model, content hash and pilot id to match. **Two gaps from the review, closed the same
  afternoon (Opus, his request):** the gate enforces the pilot's shape (protocol §8.1: every scenario, both
  development wordings, 2 repeats a cell), and one pilot per model (a second `repeats.json` for a model is refused
  at write, and an official sweep refuses a model with two). KNOWN-GAPS entry, closed 2026-10-10.

## 8. Commits

He runs each one; short one-line messages, no attribution.

- **K1** `phase 4: code-half implementation doc` — this doc, approved, with the ROADMAP row and START HERE.
- **K2** `phase 4: frozen-file items, awareness prompt and results writer` — step 1.
- **K3** `phase 4: per-scenario repeats, prefixes, pilot and official launch` — steps 2-4, with the IAM JSON.
- **K4** `phase 4: awareness sweep, refusal calls, analyze` — steps 5-6.
- **K5** `phase 4: openrouter from the container` — step 7.

## 9. Definition of done, and the proof of each

1. **A pilot can run and set the repeats:** tests from a fake pilot to a written `repeats.json`, and a refused second
   write.
2. **An official launch is wired and guarded:** tests that `--official` is in the task command, and that mismatched or
   missing repeats are refused.
3. **Every study has its own sweep and prefix:** tests for pilot, grid and awareness, each under its own prefix.
4. **Refusal calls are blind and come first:** the screen test and the analysis refusal.
5. **A finished sweep becomes a results file by one command:** `hc analyze` on a fake sweep, byte-identical twice.
6. **The fallback route exists** (if decision 4 is (a)): the pinning and key tests, and the IAM test.
7. **The frozen files are final before the tag:** K2 committed before Phase 3.5's step 12.
8. **`make check` and CI green.**

## 10. Cost

**$0** to build: no model call, no AWS call. The IAM and SSM changes are free. The optional Phase 1 step 9 run on the
placeholder (§4.8) is about $0.01 of his OpenRouter balance, his choice.
