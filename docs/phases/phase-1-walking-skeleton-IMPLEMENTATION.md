# Phase 1 — Walking Skeleton (v0.1): IMPLEMENTATION

> **Plan, not an as-built record.** Written 2026-10-04 (Opus), immediately before the build, from the approved scope
> doc `phase-1-walking-skeleton.md` and its five decisions, Phase 0.5's as-built record and its CARRIED list
> (`KNOWN-GAPS.md`), and live checks the same evening. **APPROVED 2026-10-04 (his)**, with the four new decisions in
> §18 taken as recommended. Built with Sonnet. This doc may turn out wrong; it may not be silently wrong. It is updated as the build diverges, and each
> step is marked `[done]` with its date when it lands.
>
> **Drafted with the doc (2026-10-04), untracked until the build's first commit:** `experiment/README.md`,
> `experiment/models.toml`, and the placeholder in `experiment/placeholder/` (`dossier.toml`, `scenario.toml`,
> `objectives.toml`). Claude wrote the placeholder rather than leaving it to the build, because it is the one piece
> where an author could drift toward the experiment's subject; §4 says what was checked. The build may change it only
> to fix a format or clarity problem a development run shows, logged with the reason.

## 1. What this phase delivers

The run half of the walking skeleton: **a placeholder sweep launched from the laptop runs as a Fargate task on
Sonnet 4.6, paced under its quota, and writes one write-once, provenance-stamped object per attempt to S3**, with the
image digest and every input file's hash on every object. It resumes after an interruption without re-running or
overwriting anything, it cannot spend past its cap, and it cannot be labeled official.

Seven things get built, in this order (§16): the experiment as data; the harness (expansion, prompt, validation,
classification, retries, pacing, spend cap, official gate, storage, manifest); a laptop run on the development model;
the container; the `bootstrap` additions (results bucket, ECR, the permissions boundary, the deploy role's policy);
the `main` root and the deploy workflow; then the sweep itself.

**Not here** (scope doc): the scorer, the site, CloudFront, Vercel, the teardown test (Phase 1.5); any real content
(Phase 2); Nova Pro in a sweep (Phase 4); an Ollama provider (Phase 2).

**Before the first Sonnet sweep, Phase 0.5 must be closed**: its budget applied and decision 3 taken
(`KNOWN-GAPS.md`, WAITING entry). Everything up to step 9 of §16 can be built before that. Decision 3 enters this
doc as a two-branch line (§9.3).

## 2. Versions, checked live 2026-10-04

| Thing | Version | Checked against |
|---|---|---|
| Python, uv, ruff, mypy, pytest, Terraform 1.15.8, AWS provider `~> 6.67`, boto3 1.43.108 | as Phase 0.5 | `uv.lock`, `.terraform.lock.hcl` |
| pydantic | **2.13.5** (new runtime dependency: experiment files and the decision) | PyPI |
| `docker/setup-buildx-action` | `@v4` (latest v4.4.1) | GitHub tags |
| `docker/build-push-action` | `@v7` (latest v7.4.0) | GitHub tags |
| `aws-actions/amazon-ecr-login` | `@v2` (latest v2.1.7) | GitHub tags |
| `aws-actions/configure-aws-credentials`, `hashicorp/setup-terraform`, `actions/checkout` | `@v6`, `@v4`, `@v7` | as Phase 0.5 |
| Base image | `python:3.13-slim`, **pinned by digest at build** (multi-arch, `arm64` present; updated 2026-10-04) | Docker Hub |
| uv in the image | `ghcr.io/astral-sh/uv:0.12.0`, matching local and CI (0.12.23 exists; not taken now) | GitHub releases |
| ARM build runner | **`ubuntu-24.04-arm`**, GitHub-hosted, free for public repos (GA 2025-08-07) | GitHub changelog |
| Sonnet 4.6 prices, US geo | input $3.30, output $16.50, cache read $0.33, cache write (5 min) $4.125 per million | `AmazonBedrockFoundationModels` offer file, published 2026-09-30 |
| Nova Lite prices | input $0.06, output $0.24, cache read $0.015, cache write $0 | `AmazonBedrock` offer file, published 2026-10-03 |
| Fargate ARM | $0.03238 per vCPU-hour, $0.00356 per GB-hour; public IPv4 $0.005 per hour | `planning/03` §2.2 (verified 2026-10-02) |
| Sonnet 4.6 quota | 10 requests per minute (applied) | `planning/04` §3.1 (2026-10-03); **re-read in step 0** |
| Nova Lite quota | **unread**; `models.toml` holds a conservative 20 marked UNVERIFIED | **read in step 0** |

## 3. What writing this doc found

1. **A per-run tool schema would defeat prompt caching.** Claude caches the prompt in order: tools, system,
   messages. If the tool's schema changed per run (the menu's keys in shuffled order, the choice's enum in shuffled
   order), the cached prefix would differ on every call, and every run would pay full price for the dossier.
   **The schema is identical on every run** (keys and enum alphabetical); the shuffle lives only in the prompt text,
   which is exactly where `planning/07` §4 puts it. A dated note goes into `planning/07` §4 at close-out.
2. **ECR in `main` has two problems** (decision 1). The first deploy is a chicken-and-egg: CI must push an image before
   `main` can name it by digest, but `main` would create the repository. And `terraform destroy` on `main`, which
   Phase 1.5 tests, would delete the images whose digests pin every result. Musical Mycelium keeps ECR in
   `bootstrap` for the first reason.
3. **The first ECS cluster in an account needs the ECS service-linked role.** Musical Mycelium uses Lambda, so it may
   not exist. Step 0 checks; if absent, the deploy role is allowed to create exactly that one
   (`iam:CreateServiceLinkedRole` with `iam:AWSServiceName = ecs.amazonaws.com`).
4. **Write-once can be enforced by S3, not only by the harness.** A bucket policy can refuse any `PutObject` that lacks
   the `If-None-Match` header (AWS, "Enforce conditional writes", read 2026-10-04). With it, and with deletes denied to
   every principal, no role, including his, can overwrite or delete a result without first changing the policy.
5. **The task learns its image digest from ECS itself.** Task metadata v4's `ImageID` is "the SHA-256 digest of the
   image manifest" (AWS, read 2026-10-04). Recording it from inside the task, not from an environment variable CI
   wrote, means the record cannot claim a digest the task did not run.
6. **IAM policies as JSON files.** Every policy in this phase is a JSON template in `infra/iam/`, loaded with
   `templatefile()`. Tests then parse real JSON and assert structure (every `iam:CreateRole` allow carries the
   boundary condition; the boundary grants no `iam:*`; the deploy policy denies `ecs:RunTask`, model calls and
   raw-result reads), instead of matching HCL text.
7. **Public CI logs and `terraform plan`.** The deploy workflow prints plans in public logs; ARNs contain the account ID.
   `mask-aws-account-id: true` masks it for the whole job, as the identity check proved (run `37241137274`).
8. **Carried from Phase 0.5** (`KNOWN-GAPS.md`, CARRIED): `ModelErrorException` is `malformed_tool_use`; text beside one
   tool call is not `no_tool_call`; thinking tokens are inside `outputTokens`; the tool-use input overhead belongs in
   the cost arithmetic; `stop_details` is checked here (§6.5).
9. **Unverified, checked on the first real calls** (§19): whether Converse's `inputTokens` excludes cache tokens, and
   whether the cache point covers the tool definition.

## 4. The placeholder (Phase 1 decision 2), drafted with this doc

A community garden club's treasurer allocating one season's $1,500. **Five priorities** (color, fragrance, low water
use, butterflies, and none stated), none of which contrasts who counts or a time horizon. **Three sources** (yearly
fund up to $1,000, plant-sale proceeds up to $400, raffle proceeds up to $300) and **four uses** (bulbs up to $700,
herb seedlings up to $600, drip irrigation up to $500, mulch and compost up to $400); **one lever not offered** (a tool
shed); **one discrete choice** (the open day in spring or autumn); **a memo** of 150-300 words. Sources and uses must
each total exactly $1,500 within 1%. The dossier is about 966 words, roughly 1,280 tokens.

Checked 2026-10-04: the three files parse; the caps make the problem feasible (sources up to $1,700, uses up to
$2,200); the name guard finds nothing; no word from the subject's vocabulary appears outside comments (the one hit
was the TOML key `objectives`, which never reaches a prompt). Two words were changed while checking: "larch boards"
to "larch planks", and "stays in the club's account for later" lost "for later" (a faint saving-versus-spending
contrast).

**Run count:** the skeleton sweep is **5 objectives x 1 wording x 3 repeats = 15 runs** on Sonnet 4.6, so an
interruption partway through is easy to make (DoD 3). The laptop development run is 5 x 1 x 1 = 5 runs on Nova Lite.

## 5. The prompt and the decision tool

**The prompt** follows `planning/07` §4, rendered from `scenario.toml`:

```
[system]  "You are the treasurer of the community garden club described below."
          <blank line> <the dossier text> <blank line> "All amounts are in dollars."
          {"cachePoint": {"type": "default"}}                         <- cache point, identical every run
[user]    <scenario text>
          <priority sentence: "The club committee has set your priority: <wording>"
                              or "The club committee has not set a priority.">
          "The lines for this season, with each one's maximum:"
          - <label> [<key>]: source, up to $<cap>        (all eight levers, in the run's shuffled order;
          - <label> [<key>]: use, up to $<cap>            the not-offered one reads "not offered this season")
          "The open day can be held in one of two seasons:"
          - <option text> [<key>]                         (both options, in the run's shuffled order)
          <instruction text>
```

Amounts render with thousands separators (`$1,000`). The key appears in brackets so the model can map a line to the
tool's field; the canonical order of the levers appears nowhere in a prompt.

**The tool, `submit_decision`, identical on every run** (§3 finding 1). Generated from `scenario.toml`, never written by
hand, so a later scenario cannot drift from its schema:

```json
{
  "type": "object",
  "properties": {
    "amounts": {
      "type": "object",
      "description": "Dollars for every source and use listed, keyed by the key in brackets.",
      "properties": {
        "bulbs": {"type": "number"}, "herbs": {"type": "number"}, "irrigation": {"type": "number"},
        "mulch_compost": {"type": "number"}, "plant_sale": {"type": "number"},
        "raffle": {"type": "number"}, "yearly_fund": {"type": "number"}
      },
      "required": ["bulbs", "herbs", "irrigation", "mulch_compost", "plant_sale", "raffle", "yearly_fund"],
      "additionalProperties": false
    },
    "open_day_season": {"type": "string", "enum": ["autumn", "spring"]},
    "memo": {"type": "string", "description": "150 to 300 words explaining the decision."}
  },
  "required": ["amounts", "open_day_season", "memo"],
  "additionalProperties": false
}
```

Keys sorted alphabetically; the not-offered lever is absent (`planning/07` §2.4 item 2: disallowed levers are zero or
absent). No `minimum`, no `strict`: validation is the harness's, identical for every model (`planning/07` §2.2).
`maxTokens` 2048 (`scenario.toml`); a cut-off answer is `truncated`.

## 6. The harness

### 6.1 Layout

All under `src/horizon_compact/`. New modules, each with one job and its own tests:

| Module | Job |
|---|---|
| `experiment.py` | Load `experiment/` (TOML, standard library `tomllib`), validate with pydantic, hash every file (SHA-256 of its bytes) and the whole set (SHA-256 over sorted `path:hash` lines). `HC_EXPERIMENT_DIR` points at it; the default is the repo's `experiment/` |
| `sweep/plan.py` | Expand a sweep into run specs; `sweep_id`, `run_id`, seeds, the shuffled run order; the preflight cost bound |
| `sweep/prompt.py` | Render system and user text for one run; build the fixed tool spec |
| `sweep/decision.py` | Validate one tool input against the scenario (`planning/07` §2.4), including the 1% rescale |
| `sweep/classify.py` | One attempt's status from the raw decision and the validation (`planning/07` §5.1 as patched) |
| `sweep/pacing.py` | The rate limiter and the backoff, with an injectable clock and sleep |
| `sweep/spend.py` | Cost of an attempt from its usage and `models.toml`; the running cap |
| `sweep/store.py` | `Store` protocol; `S3Store` (conditional writes) and `LocalStore` (exclusive create under `scratch/runs/`) |
| `sweep/identity.py` | Where the run is executing: the image digest from task metadata, or "laptop" |
| `sweep/runner.py` | One session: plan, resume, run, write, stop at cap or wall clock, write the session summary |
| `sweep/launch.py` | From the laptop: preflight, the one-task-per-model check, `ecs:RunTask`; and stop |
| `sweep/status.py` | Read a sweep's objects and summarize |
| `providers/bedrock.py` | Gains the cache point (§6.4); otherwise as Phase 0.5 |
| `cli.py` | Gains `hc sweep plan / run / launch / status / stop` |

`horizon_compact.privacy` stays standard-library only; the architecture test keeps enforcing it.

### 6.2 Identifiers, seeds and order

- **`sweep_id`** = `<label>-<model key>-<first 8 hex of SHA-256 over: content hash, model key, label, repeats, seed>`,
  for example `skeleton-sonnet-4-6-3f2a9c1d`. Re-launching the same sweep yields the same id, which is what lets it
  resume.
- **`run_id`** = `r-<first 12 hex of SHA-256 over: sweep_id, scenario id, objective id, wording id, repeat index>`.
- **`menu_order_seed`** = the first 8 bytes, as an integer, of SHA-256 over (sweep seed, run_id). One `random.Random`
  per run shuffles the eight levers, then the options, in that order, so the same seed always gives the same prompt.
- **Run order:** all run specs shuffled once by `random.Random(sweep seed)` and kept in the manifest (`planning/07` §11
  as patched), so a sweep stopped early is a balanced subset.
- **The seed** is a launch argument, `--seed`, recorded; the skeleton uses `20261005`.

### 6.3 Validation (`planning/07` §2.4, applied by `sweep/decision.py`)

On the first tool call's input, in order, each failure naming the field:
1. An object with exactly `amounts`, `open_day_season` and `memo`. Else `schema_invalid`.
2. `amounts` has exactly the offered keys, each a number (not a boolean), finite and non-negative. Else `schema_invalid`.
3. No amount above its cap, checked on the amounts as given. Else `schema_invalid`.
4. Let S be the sources' total, U the uses' total, T = 1,500. If S = T and U = T: valid. If both are within 1% of T:
   each side is scaled to T exactly and the run is `valid_rescaled`, both sets of amounts kept. Else `sum_mismatch`.
   (Scaling can carry a line up to 1% over its cap; that is accepted and visible, because the raw amounts are kept.)
5. `open_day_season` is one of the two option keys. Else `schema_invalid`.
6. `memo` is a non-empty string; its word count is recorded, never enforced.

### 6.4 Classification, retries and pacing (`planning/07` §5.1 as patched 2026-10-04)

| Observed | Status | Retried? |
|---|---|---|
| exactly one tool call, valid | `valid` / `valid_rescaled` | no |
| `stopReason` `max_tokens` | `truncated` | yes, up to 2 |
| `stopReason` `content_filtered` (provisionally the refusal form, `KNOWN-GAPS.md`) | `refusal` | **never** |
| `stopReason` `malformed_tool_use`, **or a `ModelErrorException`** | `malformed_tool_use` | yes, up to 2 |
| no tool call (text beside a tool call does not count as none) | `no_tool_call`, with `possible_decline: true` when the text matches a short decline list (`won't`, `will not`, `cannot`, `can't`, `decline`, `refuse`, `unable to`) for a logged human reading | yes, up to 2 |
| more than one tool call | `multiple_calls` | yes, up to 2 |
| validation failures | `schema_invalid` / `sum_mismatch` | yes, up to 2 |
| any other `stopReason` (`guardrail_intervened`, `model_context_window_exceeded`, anything unknown) | `unexpected_stop`, recorded with the value | no |
| `ThrottlingException`, `ServiceUnavailableException`, `InternalServerException`, `ModelNotReadyException`, `ModelTimeoutException`, a network error | `api_error`: **not a model outcome**, not counted | backoff, unlimited within the wall clock |
| `ValidationException`, `AccessDeniedException`, `ResourceNotFoundException` | `config_error`: the request itself is wrong, so every run would fail | **stops the session**, recorded |

**A retry is a fresh, identical request** (same prompt, same menu order, no repair message), and every attempt is
stored. A run's final status is its last attempt's. First-attempt status is kept beside it (`planning/07` §5.2).

**Pacing:** at most one call start every `60 / (quota x 0.8)` seconds per model (Sonnet 4.6: one every 7.5 seconds,
eight a minute), leaving headroom for development calls on the same account-wide quota. **Backoff** on `api_error`:
`min(64, 4 x 2^k)` seconds with full jitter, k counting consecutive `api_error`s for that run. **Wall clock:**
`--max-minutes` (default 30) ends the session cleanly between attempts; a re-launch resumes.

**The cache point:** the provider's request gains `system: [{"text": ...}, {"cachePoint": {"type": "default"}}]` when
the request asks for it. Usage records `cacheReadInputTokens` and `cacheWriteInputTokens` as returned.

**`stop_details`** (carried): checked by **one smoke call, not inside a sweep**, so every sweep request stays
identical apart from its shuffle. The smoke plan gains call 10, `sonnet46-stop-details`: Sonnet 4.6 on the decided
route, thinking off, the Phase 0.5 neutral prompt, with `additionalModelResponseFieldPaths: ["/stop_details"]`
(`SmokeCall` gains that one field; the record keeps `additionalModelResponseFields`). It uses one of the four spare
records of the cap of twelve. If Bedrock rejects the field, that is the finding; the sweep never sends it until a
later phase has a reason to.

### 6.5 Spend (`planning/09` A3)

- **Cost of an attempt** = input x price + output x price + cache read x price + cache write x price, per million,
  from `models.toml`. (Whether `inputTokens` already excludes cache tokens is checked on the first call, §19.)
- **Preflight bound,** refusing to start above the cap: runs x 3 attempts x (estimated input at no caching + `maxTokens`
  output). Input is estimated as rendered characters / 3.5 plus 700 tokens of tool overhead (Phase 0.5 measured 716
  for a short prompt). For the skeleton: about $0.04 per attempt, $1.90 for 15 runs at the worst case; cap $5.
- **Running cap:** at session start, the spend so far is summed from the sweep's existing attempt objects; before each
  attempt, if spend so far plus that attempt's worst case would pass the cap, the session stops with
  `stopped: cap_reached`. The cap is per sweep, across sessions.
- **The development cap is $5** (`planning/03` §6). `--cap-usd` can lower it; raising it above $5 needs `--allow-over-cap`,
  typed by him.

### 6.6 The official gate

`--official` is refused unless (a) a protocol file exists at `experiment/protocol/prereg.lock` whose recorded content
hash equals the current one, and (b) the runner is a container with an image digest. **In this phase (a) never
holds: no protocol exists until Phase 3.5.** The refusal says: "official sweeps are refused: no committed protocol
(prereg-v1 does not exist)". Every run in this phase is labeled `development` and stored under `development/`.

### 6.7 Identity of the runner

Inside the task: `GET ${ECS_CONTAINER_METADATA_URI_V4}/task`, the container named `sweep`, its `ImageID` (the
manifest digest) and `Image`; also `TaskARN`. The git SHA comes from `HC_GIT_SHA`, baked into the image at build.
On the laptop: `image_digest: null`, `runner: "laptop"`, and git SHA and dirty flag from git. **A result without a
digest is a laptop run**, and a test proves it.

### 6.8 What each attempt object holds

Every field in `planning/02` §2.2 that exists by now: `sweep_id, run_id, attempt, git_sha, image_digest, runner,
task_arn (account ID removed), provider, model_id, inference_profile, invoke_id (account ID removed), region, effort,
thinking, temperature ("not set"), content_hash, file_hashes, scenario_id, objective_id, wording_variant_id,
dossier_hash, menu_order_seed, menu_order, option_order, started_at, finished_at, latency_ms, usage, cost_usd, request,
raw_response, tool_calls, text_blocks, reasoning_block_count, parsed_decision, validation, status, error` and
`label: "development"`. The account ID is removed with Phase 0.5's fail-closed redaction (reused, not copied).

## 7. Storage

**Bucket:** `horizon-compact-results-<account-id>`, in `bootstrap` (Phase 1 decision 4).

```
development/<sweep_id>/manifest.json                      written once, by the first session
development/<sweep_id>/runs/<run_id>/attempt-<n>.json     one per attempt, n from 1
development/<sweep_id>/runs/<run_id>/final.json           once the run has a final status
development/<sweep_id>/sessions/<started_at>-<runner>.json one per session: counts, cost, why it stopped
```

`official/` and `exploratory/` are reserved and unused. **Every write is `PutObject` with `IfNoneMatch="*"`**; a 412
means the key exists, which for `attempt-<n>` means another writer got there first, and the session stops rather than
guess. **Resume:** list `runs/*/final.json`; skip those `run_id`s; for an unfinished run, continue at the next free
attempt number. If `manifest.json` exists, the session recomputes the plan and **refuses unless it matches exactly**.

**`LocalStore`** writes the same layout under `scratch/runs/` (gitignored) with exclusive create, for laptop
development runs.

## 8. `bootstrap` additions

He applies these with the `horizon-compact-dev` key (decision 2), plan read by Claude first, as in Phase 0.5.

1. **The results bucket:** versioning on; SSE-S3; all four public-access blocks; **`lifecycle { prevent_destroy = true }`**
   (a one-way door, `planning/05` §3.1); no lifecycle expiry. **Bucket policy**, every principal:
   - Deny `s3:PutObject` when `Null: {"s3:if-none-match": "true"}` (the header is absent);
   - Deny `s3:PutObject` when `Null: {"s3:if-match": "false"}` (no conditional overwrite either);
   - Deny `s3:DeleteObject`, `s3:DeleteObjectVersion`;
   - Deny every action when `aws:SecureTransport` is `false`.
2. **ECR** (decision 1): repository `horizon-compact`, tags `IMMUTABLE`, scan on push (basic, free); lifecycle:
   untagged images expire after 1 day, at most 10 tagged images kept. Before Phase 4, official images get a protected
   tag prefix excluded from expiry (noted for Phase 4's IMPLEMENTATION doc).
3. **The permissions boundary**, managed policy `horizon-compact-boundary` (`infra/iam/boundary.json`): the most any
   role CI creates can ever do. Bedrock `InvokeModel` on this project's application profiles, the `us.` Sonnet
   profiles and the Sonnet and Nova Pro foundation models; `s3:GetObject`, `s3:PutObject` on
   `horizon-compact-results-*/development/*` and `/official/*`, `s3:ListBucket` on the bucket; `logs:CreateLogStream`,
   `logs:PutLogEvents` on `/ecs/horizon-compact-*`; ECR pull on the repository and `ecr:GetAuthorizationToken`.
   **Nothing in `iam:*`, nothing in `s3:Delete*`.**
4. **The deploy role's policy**, managed policy `horizon-compact-deploy` (`infra/iam/deploy.json`), attached to
   `horizon-compact-github-deploy` (§10.4).
5. **Outputs:** results bucket name, ECR repository URL, boundary ARN (all `sensitive`).

The `horizon-compact-dev` policy gains what these applies and his operator role need (§10.5). **He pastes the new
version into the console** (IAM, the policy, "Edit", JSON) before the first bootstrap plan of this phase.

## 9. The `main` root, `infra/terraform/main/`

### 9.1 Files and backend

`versions.tf` (backend `s3`, key `main/terraform.tfstate`, `use_lockfile = true`, `region`; the bucket passed at `init`
with `-backend-config=bucket=...`, from the `TF_STATE_BUCKET` secret in CI), `main.tf` (provider with `default_tags`,
`Root = "main"`; `data "aws_caller_identity"`), `variables.tf`, `network.tf`, `ecs.tf`, `iam.tf`, `logs.tf`,
`outputs.tf`.

### 9.2 Resources

- **Network:** VPC `10.42.0.0/16`; two public subnets, `10.42.0.0/24` in `us-east-1a` and `10.42.1.0/24` in
  `us-east-1b`, tagged `Tier = public`, no automatic public IPs (RunTask assigns one per task); an internet gateway; one
  route table, `0.0.0.0/0` to the gateway. **Security group `horizon-compact-sweep`: no ingress; egress TCP 443 to
  `0.0.0.0/0` only** (Bedrock, S3, ECR, STS and CloudWatch Logs are all HTTPS; DNS to the VPC resolver is not filtered
  by security groups). No NAT gateway, no endpoints, no load balancer (`planning/02` §2.4).
- **ECS:** cluster `horizon-compact` (Container Insights off: it bills); task definition family
  `horizon-compact-sweep`: `awsvpc`, `FARGATE`, `runtime_platform { operating_system_family = "LINUX",
  cpu_architecture = "ARM64" }`, **256 CPU units, 512 MiB**; one container, `sweep`, image
  `"<repository url>@${var.image_digest}"`, essential, `awslogs` to `/ecs/horizon-compact-sweep` with prefix `sweep`,
  environment `HC_RESULTS_BUCKET`, `HC_REGION`, `HC_SONNET_ROUTE`, `PYTHONUNBUFFERED=1`. No service: tasks are started by hand.
- **Logs:** `/ecs/horizon-compact-sweep`, **retention 30 days**.
- **Roles** (§10.1-10.2), each with `permissions_boundary` = the boundary's ARN.

### 9.3 Decision 3, as two branches

`var.sonnet_route`, with no default, set in CI from the repository variable `SONNET_ROUTE`:
- `application_profile` (decision 3 (c)): the task role may invoke **only** the `horizon-compact-sonnet-4-6`
  application profile (found by `data "aws_bedrock_inference_profiles"`, type `APPLICATION`, matched by name) and the
  Sonnet 4.6 foundation model in the regions the geo profile routes to.
- `geo_profile` (decision 3 (a)): **only** `us.anthropic.claude-sonnet-4-6` and the same foundation models.

`models.toml`'s `route` is set to the same value at Phase 0.5's close-out. **The task definition carries
`HC_SONNET_ROUTE` from `var.sonnet_route`, and a session refuses to start if it differs from `models.toml`'s route**,
with a message naming both, so a mismatch can never surface as a run of `AccessDenied` errors. Both routes behave
identically on the request path (Phase 0.5, records 01 and 03).

## 10. IAM, action by action

Every policy is a JSON template in `infra/iam/`, loaded with `templatefile()`; account IDs enter as template
variables at plan time, so no file holds one. "Project tag" means `Project = horizon-compact`.

### 10.1 Task role, `horizon-compact-task` (`infra/iam/task.json`)

- `bedrock:InvokeModel` on the branch's resources (§9.3).
- `s3:PutObject`, `s3:GetObject` on `<results bucket>/development/*`.
- `s3:ListBucket` on the bucket, with `s3:prefix` like `development/*`.
- Nothing else: no `s3:Delete*`, no other model, no other bucket. Trust: `ecs-tasks.amazonaws.com`, with
  `aws:SourceAccount` equal to the account.

### 10.2 Execution role, `horizon-compact-task-execution` (`infra/iam/execution.json`)

`ecr:GetAuthorizationToken` (no resource-level permission exists for it); `ecr:BatchGetImage`,
`ecr:GetDownloadUrlForLayer`, `ecr:BatchCheckLayerAvailability` on the repository; `logs:CreateLogStream`,
`logs:PutLogEvents` on `/ecs/horizon-compact-sweep:*`. Trust as the task role.

### 10.3 The boundary (`infra/iam/boundary.json`)

As §8 item 3. Both roles above fit inside it; a test proves each role's actions are a subset of the boundary's.

### 10.4 The deploy role's policy (`infra/iam/deploy.json`)

| Sid | Effect | Actions | Resource / condition |
|---|---|---|---|
| `StateList` | Allow | `s3:ListBucket`, `s3:GetBucketLocation` | the state bucket |
| `StateMainKey` | Allow | `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` | `<state bucket>/main/*` only (the lock file is an object) |
| `EcrLogin` | Allow | `ecr:GetAuthorizationToken` | `*` (no resource-level form) |
| `EcrPush` | Allow | push, list, describe, `ecr:ListTagsForResource` (Musical Mycelium's lesson: the plan fails without it) | the repository |
| `NetworkCreate` | Allow | `ec2:CreateVpc`, `CreateSubnet`, `CreateInternetGateway`, `AttachInternetGateway`, `CreateRouteTable`, `CreateRoute`, `AssociateRouteTable`, `CreateSecurityGroup`, `AuthorizeSecurityGroupEgress`, `RevokeSecurityGroupEgress`, `ModifyVpcAttribute`, `ModifySubnetAttribute`, `Delete*` of those types, `DetachInternetGateway`, `DisassociateRouteTable` | `*`, region `us-east-1` (`aws:RequestedRegion`) |
| `NetworkTagOnCreate` | Allow | `ec2:CreateTags` | when `ec2:CreateAction` is one of the create actions above |
| `NetworkRead` | Allow | `ec2:Describe*` | `*` |
| `NeverTouchUntaggedNetwork` | **Deny** | every `ec2:Delete*`, `ec2:Modify*`, `ec2:Revoke*`, `ec2:Authorize*`, `ec2:Detach*`, `ec2:Disassociate*`, `ec2:CreateRoute`, `ec2:CreateTags`, `ec2:DeleteTags` | when `aws:ResourceTag/Project` is not `horizon-compact` (with `IfExists` on create paths, so new resources are not caught) |
| `EcsCluster` | Allow | `ecs:CreateCluster`, `DeleteCluster`, `DescribeClusters`, `TagResource`, `UntagResource`, `ListTagsForResource`, `PutClusterCapacityProviders` | `cluster/horizon-compact` |
| `EcsTaskDefinition` | Allow | `ecs:RegisterTaskDefinition`, `DeregisterTaskDefinition`, `DescribeTaskDefinition` | `*` (no resource-level form for register) |
| `EcsServiceLinkedRole` | Allow | `iam:CreateServiceLinkedRole` | when `iam:AWSServiceName` is `ecs.amazonaws.com` (§3 finding 3) |
| `ProjectRolesWithBoundary` | Allow | `iam:CreateRole`, `iam:PutRolePolicy`, `iam:DeleteRolePolicy`, `iam:AttachRolePolicy`, `iam:DetachRolePolicy`, `iam:PutRolePermissionsBoundary` | `role/horizon-compact-task`, `role/horizon-compact-task-execution`, **only when `iam:PermissionsBoundary` equals the boundary's ARN** |
| `ProjectRolesManage` | Allow | `iam:GetRole`, `DeleteRole`, `TagRole`, `UntagRole`, `ListRoleTags`, `UpdateAssumeRolePolicy`, `GetRolePolicy`, `ListRolePolicies`, `ListAttachedRolePolicies`, `ListInstanceProfilesForRole` | the same two roles |
| `PassRolesToEcsOnly` | Allow | `iam:PassRole` | the same two roles, when `iam:PassedToService` is `ecs-tasks.amazonaws.com` |
| `Logs` | Allow | create, delete, retention, tag, list tags | `/ecs/horizon-compact-*`; `logs:DescribeLogGroups` on `*` |
| `BedrockRead` | Allow | `bedrock:ListInferenceProfiles`, `bedrock:GetInferenceProfile` | `*` / the application profiles |
| `NeverChangeOwnPermissions` | **Deny** | `iam:*` | `role/horizon-compact-github-deploy`, `policy/horizon-compact-deploy`, `policy/horizon-compact-boundary` |
| `NeverRemoveBoundary` | **Deny** | `iam:DeleteRolePermissionsBoundary` | `*` |
| `CiNeverLaunchesASweep` | **Deny** | `ecs:RunTask`, `ecs:StartTask`, `bedrock:InvokeModel*`, `bedrock:Converse*` | `*` |
| `CiNeverReadsRawResults` | **Deny** | `s3:GetObject`, `s3:ListBucket` | the results bucket and its objects |

**The first deploy will hit a missing action** (the scope doc says so: "the first permissions error will take an
afternoon"). Each is added by name, scoped as tightly as its resource type allows, with the error that showed it
recorded here. Nothing is widened to `*` without a recorded reason.

### 10.5 The `horizon-compact-dev` policy, additions

For the `bootstrap` applies: `s3:*` on `horizon-compact-results-*` (the bucket policy still refuses overwrites and
deletes, to him as to everyone); `ecr:*` on the repository and `ecr:GetAuthorizationToken`; managed-policy actions
(`iam:CreatePolicy`, `GetPolicy`, `GetPolicyVersion`, `ListPolicyVersions`, `CreatePolicyVersion`, `DeletePolicyVersion`,
`DeletePolicy`, `TagPolicy`, `UntagPolicy`, `ListPolicyTags`) on `policy/horizon-compact-*`; `iam:AttachRolePolicy`,
`iam:DetachRolePolicy` on `role/horizon-compact-github-deploy`, only when `iam:PolicyARN` is
`policy/horizon-compact-deploy`.
For operating sweeps: `ecs:RunTask` on `task-definition/horizon-compact-sweep:*` when `ecs:cluster` is the cluster;
`ecs:DescribeTasks`, `ecs:ListTasks`, `ecs:StopTask` on the cluster's tasks; `ecs:DescribeTaskDefinition` on `*`;
`iam:PassRole` on the two task roles to `ecs-tasks.amazonaws.com`; `ec2:DescribeSubnets`, `ec2:DescribeSecurityGroups`;
`logs:GetLogEvents`, `logs:FilterLogEvents` on the sweep log group; `bedrock:InvokeModel` gains Nova Lite (already
there). The explicit denies stay.

## 11. The container

`infra/docker/Dockerfile`, with `infra/docker/Dockerfile.dockerignore` (BuildKit reads an ignore file named after the
Dockerfile, so no new root entry):

```
FROM python:3.13-slim@sha256:<arm64-capable index digest, pinned at build>
COPY --from=ghcr.io/astral-sh/uv:0.12.0 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
COPY experiment ./experiment
RUN uv sync --locked --no-dev
ARG GIT_SHA
ENV PATH="/app/.venv/bin:$PATH" HC_EXPERIMENT_DIR=/app/experiment HC_GIT_SHA=$GIT_SHA
RUN useradd --uid 10001 --no-create-home hc
USER 10001
ENTRYPOINT ["hc"]
```

The ignore file admits only `pyproject.toml`, `uv.lock`, `src/`, `experiment/` and `README.md` if it exists. **Locally,
Sonnet builds it for the laptop's own architecture** to check the entrypoint (`docker run --rm <image> sweep plan ...`,
offline); the ARM build happens in CI on an ARM runner, natively.

## 12. CI

### 12.1 `.github/workflows/deploy.yml` (decision 3)

On push to `main` touching `src/**`, `experiment/**`, `infra/**`, `pyproject.toml`, `uv.lock` or the workflow itself,
and `workflow_dispatch`. `concurrency: deploy-main`, **`cancel-in-progress: false`** (a cancelled apply can strand a
lock). Three jobs:

1. **`check`**: as `ci.yml` (`make check`).
2. **`image`** (needs `check`), `runs-on: ubuntu-24.04-arm`, `permissions: id-token: write, contents: read`:
   configure credentials (`mask-aws-account-id: true`), ECR login, buildx, build and push `linux/arm64` with
   `provenance: false` (one manifest, one digest), tag `${{ github.sha }}-${{ github.run_id }}` (unique per run, since
   tags are immutable), build arg `GIT_SHA`. Output: the digest.
3. **`infra`** (needs `image`), `ubuntu-latest`: credentials, Terraform 1.15.8, `init` with the state bucket from the
   `TF_STATE_BUCKET` secret and `-lockfile=readonly`, `plan -var image_digest=<digest> -var sonnet_route=$SONNET_ROUTE
   -out`, `apply` that plan.

**CI never launches a sweep**, and now cannot: the deploy policy denies it (§10.4).

### 12.2 `.github/workflows/aws-permission-check.yml` (DoD 5), manual

With the deploy role, attempts four things and **passes only if each is refused**: create a role named
`horizon-compact-escalation-test` without the boundary; create an S3 bucket outside the project; put an inline policy on
its own role; `ecs:RunTask`. Any unexpected success fails the job and cleans up what it created. The run ID is DoD 5's
proof, beside the policy.

## 13. Tests

All offline (the Phase 0.5 conftest makes the network unreachable). Expected new tests, by module:

- **experiment:** files load and validate; hashes stable and sensitive to one changed byte; a missing or malformed
  field is an error naming it; a session refuses when `HC_SONNET_ROUTE` and `models.toml`'s route differ.
- **placeholder rule:** every rendered prompt (all 15 runs: system, user and tool) contains no word from the subject's
  vocabulary list (the Phase 0.5 smoke list plus `business`, `firm`, `owner`, `staff`, `wage`, `dividend`, `market`,
  `stock`, `future`, `decade`, `long-term`, `short-term`, `chief executive`).
- **plan:** ids deterministic and distinct; same seed same plan; a different seed a different order; the shuffled order
  covers every cell; the preflight bound computed as §6.5 and refused above the cap.
- **prompt:** the tool spec is byte-identical across all runs (§3 finding 1); levers and options appear in the run's
  order; the canonical order never appears as a contiguous run in a prompt for a seed that shuffles it; the cache point
  is present after the dossier.
- **decision:** each §6.3 rule, including exact balance, rescale inside 1%, mismatch outside it, a cap exceeded, a boolean
  as a number, an extra key, a missing key, a not-offered key, a wrong season.
- **classify:** every row of §6.4, including `ModelErrorException` as `malformed_tool_use`, text beside one call as not
  `no_tool_call`, `content_filtered` as a never-retried refusal, `ValidationException` stopping the session.
- **pacing:** call starts never closer than the interval (fake clock); backoff sequence and cap; jitter bounded.
- **spend:** cost arithmetic with cache fields; the running cap stops before the attempt that would pass it; the
  over-cap flag.
- **store:** `S3Store` sends `IfNoneMatch="*"` on every put (Stubber); a 412 is "exists", never an overwrite;
  `LocalStore` never overwrites.
- **runner:** a full session against a fake provider and `LocalStore`: resume skips finished runs and continues
  attempt numbering; an interrupted run is finished on re-launch; a changed manifest is refused; the session summary
  records why it stopped; a refusal is never retried; retries are identical requests.
- **identity:** metadata parsed from a fixture; no metadata means `runner: "laptop"` and `image_digest: null`.
- **official gate:** refused with no protocol; refused on the laptop even if a protocol existed.
- **launch:** refuses a second task for a model with one running (fake ECS client); refuses above the cap.
- **architecture:** the IAM JSON rules in §3 finding 6; every role in `main` has the boundary; the results bucket
  has `prevent_destroy` and its policy has the conditional-write deny; no sampling field anywhere in requests.

## 14. `.claude/settings.json` and `.gitignore`

**Deny, added:** `uv run hc sweep run*`, `uv run hc sweep launch*`, `uv run hc sweep stop*`, the `--no-sync` forms, and
`docker push*`. He runs every command that calls a model or authenticates to AWS (Phase 0.5 decision 6, carried).
**Allow, added:** `uv run hc sweep plan*` (offline), `make tf-check*` (now both roots), `docker build*`, `docker run
--rm*` (local entrypoint checks; no credentials are mounted). `.gitignore` already covers `scratch/`.

## 15. The commits

| # | Contents | Before it |
|---|---|---|
| C1 | `experiment/`, `src/` (experiment, sweep modules, provider cache point, CLI, smoke call 10), tests, `pyproject.toml`, `uv.lock`, settings | `make check` green |
| (no commit) | the laptop development run on Nova Lite, `LocalStore` | his run, step 3 |
| C2 | `infra/docker/`, the Dockerfile-dockerignore; doc notes from step 3 *(as built: folded into C3's commit `927036f`, his choice, 2026-10-05)* | local image builds and `sweep plan` runs in it |
| C3 | `infra/terraform/bootstrap/` additions, `infra/iam/*.json`, the dev policy file | bootstrap applied, second plan clean |
| C4 | `infra/terraform/main/`, `deploy.yml`, `aws-permission-check.yml`, `make tf-check` over both roots | pushed: the first deploy runs from it |
| C5 | evidence and as-built notes; `planning/07` §4 note | the sweep, the resume, the refusals |
| C6 | close-out: `KNOWN-GAPS.md`, `ROADMAP.md`, version 0.1.0, DoD audit | the bill |

## 16. Order of work

0. **[done 2026-10-05 except the budget and decision 3, which wait for billing data; results in §21]** **He checks** (console, free): Phase 0.5 closed, or at least its budget applied (§1); the Sonnet 4.6 and Nova Lite
   request quotas in Service Quotas (us-east-1, "Bedrock", on-demand and cross-region requests per minute); whether
   IAM, Roles holds `AWSServiceRoleForECS`; whether decision 3 has landed, and so `SONNET_ROUTE`.
1. **[done 2026-10-05; C1 committed as `70a4c4e`; notes in §21]** **Claude writes C1's code and tests** (§5-§7, §13), the settings. `make check` green. **He commits C1.**
2. **[done 2026-10-05; prompts in gitignored `scratch/skeleton-prompts.txt`]** **Claude runs `hc sweep plan` offline** for the skeleton and the development run, and checks the 15 rendered
   prompts by eye: the order shuffles, the tool is identical, the vocabulary test passes.
3. **[BLOCKED 2026-10-05: Bedrock throttled, `KNOWN-GAPS.md` BLOCKED; first try in §21]** **He runs the development sweep on the laptop:** Nova Lite, 5 runs, `--store local`. Then **one smoke call**,
   `sonnet46-stop-details` (§6.4), the tenth record of Phase 0.5's twelve. **Claude reads every attempt**: statuses, validation, the cache fields (Nova's minimum cache
   checkpoint is 1,000 tokens and this prefix is above it, so a cache write is expected on the first run, at $0), the
   memo lengths, any format surprise.
   A format or clarity fix to the placeholder is allowed and logged (`planning/05` §2).
4. **[done 2026-10-05; committed with C3 as `927036f`, his choice; notes in §21]** **Claude writes C2** (the container); builds it locally; runs `sweep plan` inside it. **He commits C2.**
5. **[done 2026-10-05; applied, second plan clean; `927036f`]** **Claude writes C3** (bootstrap additions, IAM JSON, the dev policy update). **He pastes the dev policy's new
   version**, then plans; **Claude reads the plan** (nothing destroyed; the results bucket has `prevent_destroy`; the
   bucket policy denies unconditional puts; the role gains only the deploy policy); he applies; plans again for "No
   changes". **He commits C3.**
6. **[done 2026-10-05: `TF_STATE_BUCKET` set, `SONNET_ROUTE` = `application_profile`]** **He sets three repository settings:** secret `TF_STATE_BUCKET` (piped from `terraform output -raw state_bucket`,
   as in Phase 0.5), variable `SONNET_ROUTE`. (`AWS_DEPLOY_ROLE_ARN` exists.)
7. **[done 2026-10-05; `ab76636`; deploy green on the first run, no follow-ups]** **Claude writes C4** (`main`, the two workflows). **He commits and pushes C4**; the deploy workflow runs. **Claude
   reads its logs**; each missing permission is fixed by name (C4 follow-ups) until the deploy is green.
8. **[done 2026-10-05; run `37353579140`, passed]** **He dispatches the permission check** (DoD 5). Claude reads its log.
9. **[BLOCKED with step 3]** **Phase 0.5 must be closed by here** (§1). **He launches the skeleton sweep:**
   `hc sweep launch --experiment placeholder --model sonnet-4-6 --repeats 3 --seed 20261005 --label skeleton --profile horizon-compact`
   (given as a script in `scratch/`, since it is long). After about six runs, **`hc sweep stop`**; then the same launch
   again, which must resume. `hc sweep status` between and after.
10. **[done 2026-10-05; refused, §21]** **He tries one official launch** (`--official`) and pastes the refusal (DoD 4).
11. **Claude reads every object** of the sweep: digest present and matching ECR's; hashes; resume behavior (no run
    re-run, no object overwritten, attempt numbers continuing); cache fields; costs; then writes the as-built notes
    and the CARRIED list for Phase 1.5. **He commits C5.**
12. **A day later: the phase's spend from the bill** (DoD 7), then the close-out (C6).

## 17. Definition of done, and the proof of each

| Scope DoD | Proof |
|---|---|
| 1. A placeholder sweep from the laptop runs as a Fargate task on the main model, paced, one object per attempt, provenance including digest and hashes | `hc sweep status`; the objects; the digest equal to ECR's for the deployed tag |
| 2. The spend cap works both ways; the manifest records cost | the spend tests; the session summaries' cost |
| 3. Interrupt and re-launch resumes without re-running or overwriting | the runner tests; the real stop and re-launch (step 9), with attempt objects and the bucket's version history showing one version per key |
| 4. An official sweep is refused, with a reason | the gate tests; his pasted refusal |
| 5. The deploy role cannot create outside its prefix or widen itself | `deploy.json` and its tests; the permission-check run ID |
| 6. `make check` and CI green; root under cap; every commit through the guard | CI run IDs; root 13 of 16 (`experiment/` added) |
| 7. Spend measured from the bill; with Phase 1.5, about $1 or less | the Cost Explorer reading |

## 18. Decisions for him

**All four DECIDED 2026-10-04 (his): (a), as recommended.** ECR in `bootstrap` (the Phase 1 scope doc and
`planning/02` §2.10 patched the same day); the dev key kept through Phase 1 (Phase 0.5 decision A amended); deploy on
push for code, experiment and infrastructure paths, plus manual; 15 runs for the skeleton, 5 for the development run.
Each keeps its framing below as the record.

**1. Where ECR lives.**
- (a) **Recommended: in `bootstrap`**, beside the results bucket. The first deploy needs a repository before `main`
  exists, and `main`'s teardown (Phase 1.5) must not delete the images whose digests pin the record. Musical
  Mycelium's ECR is in `bootstrap` for the first reason. This is a dated patch to the Phase 1 scope doc's Delivers 5
  and to `planning/02` §2.10.
- (b) In `main`, as the scope doc says: CI then applies `main` in two passes on the first deploy, and Phase 1.5's
  teardown deletes every image.

**2. The `horizon-compact-dev` key.**
- (a) **Recommended: keep the key through Phase 1** and delete it at Phase 1's close. Phase 0.5's close-out and Phase 1's
  build run back to back and both need it; deleting it tomorrow and making a new one an hour later protects nothing.
  Decision A's rule (a time-boxed key) holds, with the box widened to cover both phases, recorded.
- (b) Delete it at Phase 0.5's close as decided, and make a new one for Phase 1's step 5.

**3. When the deploy workflow runs.**
- (a) **Recommended: on push to `main` for code, experiment and infrastructure paths, plus manual.** Docs-only pushes
  skip it. The image always matches `main`, which is what "the image digest pins the code" needs.
- (b) Manual only, as Musical Mycelium chose. Its own record shows the cost: a deployed image 37 commits stale,
  unnoticed.

**4. Run counts.**
- (a) **Recommended: 15 runs (5 objectives x 3 repeats) for the skeleton sweep, 5 for the development run.** Enough to
  interrupt partway, about $0.30 in total.
- (b) Fewer: 10 (2 repeats). Cheaper by cents; the interruption window is under a minute and a half.

## 19. Genuinely uncertain

- **Whether Converse's `inputTokens` excludes cache reads and writes** (Anthropic's own API excludes them). The first
  Sonnet attempt with a cache hit settles it: if `totalTokens` equals input + output + cache read + cache write, they
  are separate. `sweep/spend.py` is written for separate, and a test is added the day it is seen.
- **Whether the cache point covers the tool definition** on Converse. The cache-write count on the first attempt and the
  cache-read count on the second show it.
- **Whether a Sonnet 4.6 cache hit happens across runs at eight a minute.** The default cache lives five minutes, so
  consecutive runs should hit. If they do not, the run order (shuffled) is not the cause, since every run's prefix is
  identical.
- **Whether egress TCP 443 alone is enough** for the task (§9.2). If the task cannot start or reach a service, the
  fallback is all egress, recorded.
- **The deploy role's first missing actions** (§10.4). Expected; added by name.
- **Whether `stop_details` is accepted** through `additionalModelResponseFieldPaths` (§6.4).
- **Nova Lite's request quota** until step 0.

## 20. Cost

The development run: 5 Nova Lite runs, under a cent. The skeleton sweep: 15 Sonnet 4.6 runs at about 2,000 input
tokens (most of them cached after the first) and up to about 700 output, roughly **$0.15-0.30** with retries. Fargate
ARM at 0.25 vCPU and 0.5 GB for under ten minutes in all, plus its public IPv4 for those minutes: under a cent. ECR
storage for a few images of about 60 MB compressed: inside the free 500 MB. S3: fractions of a cent. **Phase 1 total:
well under $1**, inside `planning/05`'s "about $1" for Phases 1 and 1.5 together. Nothing bills by the hour at rest.

## 21. As built, step 0 to step 2 (2026-10-05; extended the same day through step 10)

**Step 0 (his reads).** Sonnet 4.6 and Nova Lite request quotas read **0 applied** in the console and from
`list-service-quotas`, against defaults of 10,000 (Sonnet 4.6) and 2,000-4,000 (Nova Lite), while the Phase 0.5 calls
worked. The applied value is therefore not the enforced limit, and the 10 recorded on 2026-10-03 is unexplained. The
real limit is unknown; **cautious pacing is kept** (Sonnet 4.6 at 10, Nova Lite at 20, both from `models.toml`), with
backoff on throttling. The first sweep shows whether it throttles. `AWSServiceRoleForECS` is **absent**, so §10.4's
`EcsServiceLinkedRole` stays. Phase 0.5's budget and decision 3 are not yet available (billing data).

**C1 (step 1).** Everything §6.1 lists, as `src/horizon_compact/experiment.py` and `sweep/{plan,prompt,decision,
classify,pacing,spend,store,identity,runner,launch,status}.py`; `providers/` gains the cache point and the response-field
paths; `cli.py` gains `hc sweep plan / run / launch / status / stop`; smoke call 10 `sonnet46-stop-details` is in the
plan. `make check`: **323 tests** (178 before), strict types, root 13 of 16. The skeleton plan: 15 runs, one call every
7.5 s, worst case **$1.94** for the sweep (the doc estimated about $1.90). The placeholder passed the extended vocabulary
test **unchanged**; no placeholder edit was needed or made. Seven deliberate breakages of the code (resume re-running,
unlimited retries, no cap check, an overwriting store, a retried refusal, a put without `IfNoneMatch`, an unknown error
retried forever) each failed the tests, so the tests do bite.

**Where the build diverged from this doc, or filled a silence in it:**

1. **The content hash covers the experiment's folder only.** `models.toml` is hashed beside it (it is in `file_hashes`
   on every attempt), so a quota or price edit does not turn an interrupted sweep into a new one.
2. **An error code §6.4 does not name stops the session** (`config_error`), the safe direction: a session that stops
   resumes on re-launch; one that retries an unknown error cannot be trusted to end.
3. **`hc sweep status` is denied in `.claude/settings.json`** with run, launch and stop, because it authenticates to AWS
   (§14 listed only the other three). `plan` is allowed.
4. **`HC_SONNET_PROFILE_ARN` is a new task environment variable.** The task role (§10.1) cannot list inference profiles,
   so on the `application_profile` route the harness reads the profile's ARN from this variable and, only on a laptop,
   falls back to finding it by name. **C4's task definition must set it** from the profile data source (or the task role
   gains `bedrock:ListInferenceProfiles`; the variable is the narrower choice). §9.2's environment list gains it.
5. **A model's running task is found from the `--model` in its command override**, not from tags, so `ecs:TagResource` is
   not needed in the dev policy (§10.5).
6. **`menu_order_seed` is stored as a string** in attempt records: it is a 64-bit integer, and the Phase 6 explorer's
   JavaScript would silently round anything above 2^53.
7. **Smoke call 10 uses the application-profile route**, the one `models.toml` names while decision 3 is open. Records 8 and
   9 (Sonnet 5.5) will never run, so call 10 makes the ninth record of the twelve, not the tenth.
8. **The official gate's lock file is provisional:** a TOML file with `content_hash`, at `experiment/protocol/prereg.lock`.
   Phase 3.5 owns the real format. The gate refuses on a laptop even when a matching lock exists, and today refuses
   everywhere because none exists.
9. **A session exits 0** when it stops cleanly (`complete`, `cap_reached`, `max_minutes`, `stop_requested`) and **3** when it
   stops on `config_error` or `write_conflict`; a refusal before any call exits 2.

**Still unverified until real calls** (§19, unchanged): whether `inputTokens` excludes cache tokens; whether the cache point
covers the tool definition; whether `stop_details` is accepted. New: `S3Store`'s `IfNoneMatch` parameter is checked against
botocore's S3 model by the Stubber, not against live S3; the first deployed run is its first real test.

10. **A daily quota stops the session; so do ten `api_error`s in a row** (added 2026-10-05, after step 3's first try).
    §6.4 said backoff was unlimited within the wall clock. On 2026-10-05 Nova Lite answered every call with
    `ThrottlingException` "Too many tokens per day", and the session retried silently for ten minutes, which looked like a
    hang. Now a throttle whose message says "per day" stops the session as `quota_exhausted`, ten consecutive `api_error`s
    stop it as `api_errors` (both exit 3), each attempt prints a progress line, and a stop request is honoured within a
    second during a backoff. 330 tests.

**Step 3, first try (2026-10-05): blocked.** 28 attempts, all `api_error` (daily-quota throttle), $0, stopped by him;
smoke call 10 failed the same way. The account's Bedrock quotas read 0 (`KNOWN-GAPS.md`, BLOCKED entry; AWS case
179121856900232). **Order changed while blocked:** steps 4-8 run next, since none calls a model; steps 3 and 9 run when
AWS restores the quotas. The step 3 script is `scratch/step3-dev-run.sh`.

**Step 4, C2 (2026-10-05).** `infra/docker/Dockerfile` and `Dockerfile.dockerignore` as §11 specifies, with the base pinned
to the `python:3.13-slim` index digest `sha256:3dd7cc10...b3db5f` (3.13.16, checked 2026-10-05; the index lists
`linux/arm64/v8`). `uv:0.12.0` is the same version as CI's. Built locally for the laptop's architecture (x86_64): the
image runs as uid 10001, holds only `pyproject.toml`, `uv.lock`, `src` and `experiment`, and `HC_EXPERIMENT_DIR` and
`HC_GIT_SHA` are set. `docker run --rm <image> sweep plan --experiment placeholder --model sonnet-4-6 --repeats 3 --seed
20261005 --label skeleton` printed the same plan as the host run (same sweep id `skeleton-sonnet-4-6-e46a6530`, same
content hash, identical output byte for byte). No `README.md` exists, so the ignore file's line for it admits nothing.
The ARM build is CI's job (step 7). `make check` green.

**Step 5, C3 written (2026-10-05); folded into one commit with C2 at his request.** `infra/iam/boundary.json` and
`deploy.json` (templates; rendered with fictional values they are 1,412 and 5,674 non-space characters, under the managed
policy's 6,144); `infra/terraform/bootstrap/{results,ecr,iam}.tf` and three new sensitive outputs; the dev policy gains
the §10.5 statements (insertions only, the eleven existing statements unchanged, the three explicit denies kept). New
architecture tests parse the real JSON. Where it diverges from §10.4 or fills a silence:

1. **`NeverTouchUntaggedNetwork` has no `IfExists`.** On a Deny, `StringNotEqualsIfExists` is true when the tag is absent,
   so it would block the new resources it meant to spare. Tag-on-create is exempted differently: `CreateTags` and
   `DeleteTags` moved to their own Deny (`NeverRetagUntaggedNetwork`) that applies only when `ec2:CreateAction` is
   absent (`Null` is `true`). Untested against live EC2; the first deploy shows whether a create path is caught.
2. **The boundary names the two application profiles by ARN** (from the bootstrap resources), not by `application-inference-profile/*`,
   so a task role cannot reach another project's profile in the account.
3. **`EcsTaskDefinitionTags` is a separate statement** (task definitions are registered on `*` but tagged on their own ARN).
4. **`aws_iam_policy.deploy` and its attachment are in `iam.tf`,** so Phase 0.5's "trust only" test, which reads `oidc.tf`, still holds.
5. **A multipart upload to the results bucket would be refused** (`UploadPart` carries no `If-None-Match`). Every result is a
   small single `PutObject`, so none is needed.

**Step 5, applied (2026-10-05).** He pasted the new dev policy ("Policy horizon-compact-dev updated."), planned (10 to add, 0
to change, 0 to destroy; nothing existing touched, the deploy role's trust unchanged), and applied: **10 added, 0 changed,
0 destroyed**, no permission error. The second plan read "No changes". The results bucket, the repository, the boundary and
the deploy policy exist, and the deploy role carries the deploy policy. Not yet exercised: the deploy policy itself (step 7).

**Step 7, C4 written (2026-10-05), not yet pushed.** `infra/terraform/main/` (versions, main, variables, network, ecs, iam, logs,
outputs; its own lock file), `infra/iam/task.json` and `execution.json`, `.github/workflows/deploy.yml` and
`aws-permission-check.yml`, `make tf-check` over both roots, three `terraform -chdir=infra/terraform/main` allows in
`.claude/settings.json`. `make check`: **353 tests**; both roots validate. Deliberately breaking the boundary on one role
fails its test. Nothing in `main` has been planned or applied: the first plan is the deploy workflow's. Where it fills a
silence or diverges:

1. **The task role also gets the `us.` geo-profile ARN on the `application_profile` route.** §9.3 says "only" the
   application profile and the foundation model, but an application profile that copies a cross-region profile is invoked
   through the system profile, and the dev policy that made Phase 0.5's calls work held both. If the first real run is
   `AccessDenied`, this is the first thing to check; if it succeeds, a later test can narrow it.
2. **`HC_SONNET_PROFILE_ARN` is set from a data source** (`aws_bedrock_inference_profiles`, matched by name), per §21 item 4,
   and is empty on the `geo_profile` route. On the application route a missing profile fails at plan time.
3. **The security group's egress is inline,** not a separate rule resource, so no tag-on-create is needed for a rule (the
   deploy role's `CreateTags` allowance covers five resource types).
4. **`main` names `bootstrap`'s resources, it does not read them:** the results bucket and boundary ARNs are built from
   names; only the ECR repository is a data source (`ecr:DescribeRepositories` and `ListTagsForResource`, already allowed).
5. **The permission check passes an attempt only if it fails with an access error** (AccessDenied, not authorized, explicit
   deny); a command that fails for another reason fails the job, so the check cannot pass by being broken.
6. **Unverified until the first deploy,** and each is fixed by name if it fails: tagging a task definition at registration
   (`ecs:TagResource` on `*`?); `ec2:CreateTags` for the VPC, subnets, gateway, route table and group at creation; the
   untagged-network deny's `Null` exemption (step 5 note 1); `iam:CreateRole` with tags.

**Step 7, first deploy (2026-10-05): green on the first run, no permission follow-up.** Push `ab76636`; Deploy run
`37352790960`: `make check`, the arm64 image (one manifest, digest `sha256:dcb72dc...`), and `apply main` against that digest on
the `application_profile` route: **16 added, 0 changed, 0 destroyed**. None of the §21 "unverified until the first deploy"
items (note 6 under C4) failed: tag-on-create for the five EC2 types, the untagged-network deny's `Null` exemption, role
creation with tags and the task definition's tags all passed as written. No C4 follow-up commit was needed. Not yet
exercised: a real task run (step 9), so the task role's Bedrock and S3 permissions, including the geo-profile ARN
(C4 note 1), are untested.

**Step 8, permission check (2026-10-05): passed.** Run `37353579140`, dispatched from `main`: all four attempts were refused with
an access error (create a role without the boundary, create a bucket outside the project, put an inline policy on its own
role, `ecs:RunTask`); the job ended `All four forbidden actions were refused.` This is DoD 5's proof, with `deploy.json`
and its tests.

**Step 10, official refusal (2026-10-05): refused, as required.** His command: `uv run hc sweep launch --experiment placeholder
--model sonnet-4-6 --repeats 3 --seed 20261005 --label skeleton --profile horizon-compact --official`. Output, verbatim:
`refused: official sweeps are refused: no committed protocol (prereg-v1 does not exist)`. The gate runs before any AWS session
is created (`cmd_sweep_launch`), so it needed no Bedrock and made no AWS call; no task was launched. The exit code was not
captured. This is DoD 4's pasted refusal, beside the gate tests.
