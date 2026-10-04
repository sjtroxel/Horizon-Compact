# Horizon Compact — Architecture

- **Status:** PROPOSED 2026-10-02. Facts marked *verified* were checked live that day. Costs are estimated in `03`.
  **Amended by `08` (2026-10-03):** §2.1 retries and a running spend cap, §2.8 per-run storage, §2.12 the Budgets
  filter's status (patches P18, P19, P20, P33 in `09` §3).
  **Patched 2026-10-04 (his):** §2.10, the budgets move from `main` to `bootstrap`, so they exist before the first
  model call and survive `main`'s teardown (`docs/phases/phase-0.5-aws-foundation.md`, decision 2).
  **Patched 2026-10-04 (his):** §1, §2.8 and §2.10, from Phase 1's decisions 4 and 5
  (`docs/phases/phase-1-walking-skeleton.md`): the raw results bucket lives in `bootstrap`; experiment inputs are
  built into the image (no inputs bucket); aggregation runs on the laptop and the published JSON is committed.
  **Patched 2026-10-04 (his):** §2.7, v1 builds real-case dossiers with a minimal builder, without retrieval or
  reranking (`docs/phases/phase-5-case-building.md`, decision 3).
  **Patched 2026-10-04 (his):** §2.9, a preview build off the public URL until go-live, share cards built at deploy
  time, a CI job that re-scores the published raw responses, and no visitor tracking
  (`docs/phases/phase-6-explorer.md`, decisions 2, 4, 5 and 6).
  **Patched 2026-10-04 (his):** §2.10, ECR moves from `main` to `bootstrap` (`docs/phases/phase-1-walking-skeleton-IMPLEMENTATION.md`, decision 1).
- **Read after:** `01-DATA-SOURCES`. **Read before:** `03-COST-MODEL`.
- **Inherits from Musical Mycelium** wherever a pattern already worked there: Python 3.13 + uv, Terraform with
  separate `bootstrap` and `main` stacks, GitHub Actions deploying through OIDC with no long-lived keys, a React +
  TypeScript SPA on S3 + CloudFront behind a free Vercel rewrite, region `us-east-1`, Bedrock through boto3.

---

## 1. The shape in one picture

```
 OFFLINE, BUILD TIME (laptop)                     EXPERIMENT (AWS, runs only when started)
 ───────────────────────────────                  ─────────────────────────────────────────
 public data (Census, BLS, Damodaran) ─┐
 SEC EDGAR filings ── retrieve/rerank ─┼─> dossiers ──> S3 (inputs, versioned)
 human review of every dossier ────────┘                     │
                                                             v
 hc CLI ── "launch sweep" ──> ECS RunTask (Fargate, 1 task/model) ─> Bedrock (Converse API)
                                                             │
                                                             v
                                         S3 (raw results, 1 object/run, write-once)
                                                             │
 PUBLISH (laptop or CI)                                       v
 ──────────────────────                    aggregate (DuckDB over S3) ──> static JSON
                                                             │
                                                             v
 visitor ──> horizon-compact.vercel.app ──> CloudFront ──> S3 (SPA + precomputed JSON)
```

*Patched 2026-10-04 (his; Phase 1 decisions 4 and 5):* the picture above is kept as the record. As built, the
experiment's inputs are **built into the container image** rather than read from an S3 inputs bucket, so the image
digest pins the code and the content together; aggregation runs **on the laptop only**, and the static JSON is
**committed to the repo** before CI deploys it, so CI never reads raw results (§2.11). The raw results bucket lives
in the `bootstrap` root (§2.10).

**Three stages that never overlap:** build inputs (offline, reviewed by a human), run the experiment (batch, then
it stops), publish results (static files). A visitor never triggers a model call in v1.

---

## 2. Components

### 2.1 The harness (Python 3.13, uv)

One Python package, `horizon_compact`, with a CLI (`hc`). The same code runs on the laptop and inside the container.

- **Experiment definition as data.** Scenarios, objectives and their wording variants, the lever menu, the company
  dossier and run counts live in versioned files (YAML or JSON), not in code. A sweep is fully described by those
  files plus a seed. Changing a prompt changes a version hash, never silently.
- **Provider interface.** One small interface (`decide(prompt) -> raw response + usage`) with implementations for
  **Bedrock** and **local models (Ollama)**. Every result records which implementation produced it.
- **Structured output by one tool call, `auto` choice (corrected 2026-10-03, `07` §2).** *Verified 2026-10-02:*
  Bedrock's native "structured outputs" feature is not supported for Claude Sonnet 5.5. *Verified 2026-10-03:*
  Sonnet 5.5 also **rejects forced tool use** on every request. **One capture method across every model** (`04`
  §1.8): one tool, `tool_choice: auto`, an explicit instruction to call it, no provider-side `strict`, through the
  Converse API, even for Sonnet 4.6 (which supports native structured outputs and forced tool use). A response
  without the tool call is a recorded failure. So each decision is returned by the model calling one tool whose
  input schema *is* the decision (lever allocations in dollars, the discrete choice where a scenario has one, the
  memo). The harness then validates with pydantic: amounts non-negative, allocations sum to the stated budget
  within a tolerance, the discrete choice is one of the allowed values, no lever above its cap (`07` §2.4). A failed
  validation is retried a bounded number of times as a **fresh, identical request** (no repair message; `07` §5),
  and **every failure is recorded, never silently dropped**. The rejection rate is itself
  published (a model that cannot follow the format under some objective is a finding).
- **Menu order shuffled** per run from a recorded seed, so any run can be reproduced exactly.
- **Budget guard, in two parts.** Before a sweep starts, the harness estimates its token cost from the run count and
  prompt sizes and **refuses to start above a configured cap**. While it runs, it **adds up the actual cost from
  each call's token counts and stops at the cap** (added 2026-10-03, `08` §4.3), because the preflight estimate does
  not include retries and AWS Budgets alarms arrive hours late. Musical Mycelium's hard token cap, extended to a
  whole sweep. Caps: `03` §6.

### 2.2 The provenance record (every model call)

Written next to the result, so no number in the app is separable from what produced it:

`sweep_id, run_id, git_sha, image_digest, provider, model_id, inference_profile, region, effort,
temperature (if settable), prompt_version_hash, objective_id, wording_variant_id, scenario_id, dossier_hash,
menu_order_seed, started_at, input_tokens, output_tokens, raw_response, parsed_decision, validation_status,
retry_count`

**Official results come only from container runs**, identified by image digest. Laptop runs (local models,
development) are labeled as such and kept separate. This is the Musical Mycelium lesson about a local stand-in
producing a false finding, built into the data model.

### 2.3 Compute: ECS on Fargate, launched on demand

- **One container image** (in ECR), built in CI. A sweep is split into shards; the CLI launches one **ECS RunTask**
  per shard on **Fargate**. Each task runs its shard, writes results to S3, and exits. Nothing stays running.
- **On-demand Fargate on ARM, not Spot, for v1** (decided 2026-10-03, `04` §3.6): the whole Fargate line is under
  $2, so Spot would save cents and add interruptions to explain. Runs are still idempotent (keyed by `run_id`; an
  existing result is skipped), so any interrupted task is simply re-run. Spot reconsidered for the frequency study.
- **One task per model, not many shards (corrected 2026-10-03, `04` §3.1).** *Verified:* the account's Sonnet 4.6
  quota is **10 requests per minute**, account-wide. Extra tasks add no throughput and would throttle each other.
  Each model's task paces itself below that model's quota, with backoff on throttling. Sonnet 4.6 and Nova Pro have
  separate quotas, so their tasks can run side by side.
- **Honest note on why containers here.** The workload is API calls, not heavy computation, and a laptop *could* run
  it. The container earns its place for two real reasons: the exact code behind every official result is pinned
  by image digest, and a sweep of a few hours does not depend on a laptop staying awake. (A third reason given on
  2026-10-02, parallel shards, does not hold at this account's quota; `04` §3.1.) It is also the ECS/Fargate
  experience the 9/27 decision was aiming for. **The README should say this plainly** rather than imply the workload
  needed a cluster.
- **Orchestration: the CLI, not a workflow service, in v1.** `hc sweep launch` starts one task per model; `hc sweep status`
  reads results from S3. AWS Step Functions would add a dependency for little gain at this size. Logged as a
  possible later step if sweeps grow (the frequency study, `00` §6.1, might justify it).

### 2.4 Networking: no NAT gateway, by design

- A minimal VPC with **public subnets only**. Tasks get a public IP and a security group that **allows outbound
  traffic and no inbound traffic**. Nothing listens; tasks only call out to Bedrock, S3 and ECR.
- **Ruled out, with reasons:** a NAT gateway (bills hourly whether used or not; the classic surprise bill); VPC
  interface endpoints (also hourly, per endpoint, per availability zone); a load balancer (nothing to balance).
- AWS charges for public IPv4 addresses by the hour they exist; a task's address exists only while the task runs.
  Rate checked in `03`.

### 2.5 Models on Bedrock (verified 2026-10-02, AWS model card)

> **ACCESS FINDING, 2026-10-02 (his console):** Sonnet 5.5, Opus 5.5 and Sonnet 5 all return
> `AccessDeniedException: ... is not available for this account`; his applied quota for Sonnet 5.5 is **0**
> (AWS default 6,000,000 tokens/min). A known pattern for accounts with limited Bedrock history. **Sonnet 4.6,
> Haiku 4.5 and Amazon Nova Pro all work.** A quota increase for Sonnet 5.5 is being requested. **v1 is designed
> on Sonnet 4.6**; the Sonnet 5.5 notes below apply if and when access arrives.
>
> **Claude Sonnet 4.6 on Bedrock (verified, AWS model card):** launched 2026-02-17; **EOL not sooner than
> 2027-02-17**; knowledge cutoff Aug 2025 (Anthropic lists training data through **Jan 2026**); `us.` geo profile
> `us.anthropic.claude-sonnet-4-6`; **native structured outputs SUPPORTED** (unlike 5.5); prompt caching (min
> 1,024 tokens per checkpoint); no batch tier listed; Anthropic list price $3 / $15 per million tokens (Bedrock
> price checked in `03`).

**Claude Sonnet 5.5 on Bedrock:** launched **2026-09-28**; knowledge cutoff June 2026; Converse, Invoke and Messages
APIs on `bedrock-runtime`; **no in-region endpoint in us-east-1**, so calls go through an inference profile:

- **`us.anthropic.claude-sonnet-5-5`** (US geo: keeps data in US and Canada regions) **(decided 2026-10-02)**,
  not `global.anthropic.claude-sonnet-5-5` (routes worldwide).

Other facts that shape the design:
- **Batch inference: not supported** for Sonnet 5.5. No 50% batch discount; sweeps use standard on-demand calls,
  throttled to the account's quota. Flex and Priority tiers also not supported.
- **Prompt caching: supported** (explicit, minimum 512 tokens per checkpoint, 5-minute or 1-hour TTL). The company
  dossier is identical across thousands of runs, so caching it is the single largest cost lever. Quantified in `03`.
- **Adaptive thinking is on by default (effort `high`).** Effort is configurable. Thinking tokens cost money and
  affect variability, so **effort is set explicitly and recorded** on every call; the value is chosen in `07`.
- **Billed through AWS Marketplace, under the model provider, not under "Amazon Bedrock"** in Cost Explorer. This is
  exactly the trap measured in Musical Mycelium on 2026-09-19 (reading the obvious "Amazon Bedrock" line was wrong
  by about 200x). The cost dashboards must filter for it from day one.
- Default quotas apply; a sweep's request rate is set below them. Quota numbers checked in `03`.

**Model roles in v1** (final choice in `03` after pricing):

| Role | Model | Where |
|---|---|---|
| Main "CEO" for official results | **Claude Sonnet 4.6** (works on his account, verified 2026-10-02); Sonnet 5.5 added if AWS grants access | Bedrock, Fargate |
| Development, harness testing, all wording variants | a local model (Ollama) and/or a cheap Bedrock model | laptop |
| Second model family (multi-model check) | a non-Anthropic model on Bedrock, if its cutoff fits | Bedrock, Fargate |
| Small-model contestant (later phase) | a small open model | see §2.6 |

**Avoid Claude Haiku 4.5 for anything long-lived.** Anthropic lists its retirement as not sooner than 2026-10-15 on
its own platforms (Bedrock sets its own dates). Fine for throwaway development, not for official results.

### 2.6 Local models

- **Development:** the harness's Ollama provider runs every scenario, schema and retry path for free on the laptop.
  Hardware on file: RTX 4050, 6GB VRAM, 16GB RAM (to be confirmed before relying on it). Small models only.
- **Small-model contestant (later phase), two options, decided when that phase is scoped:**
  - run the small model **locally**: free, but the results are laptop runs and are labeled that way; or
  - run a comparable **small open model on Bedrock**: costs a little, but runs in the same container with the same
    provenance as every other official result. Cleaner evidence.
- **Not in Fargate:** Fargate has no GPUs, and the project does not need them.

### 2.7 Building real-case dossiers (retrieval and reranking)

- An offline pipeline: fetch filings from EDGAR (cached, throttled; `01` §5) -> split into sections -> **retrieve**
  the sections that matter for the decision (operations, segments, liquidity, workforce, capital allocation,
  restructuring history) -> **rerank** them (filings are long and repetitive, which is exactly where reranking pays
  off) -> extract into the dossier template -> anonymize and scale (`01` §4.6) -> **human review** -> freeze with a
  hash.
- **The CEOs never see retrieval.** They see only the finished, reviewed dossier. Retrieval is a build-time tool, so a
  retrieval error can never silently change a result: it can only change a dossier, which a human reviews first.
- Embeddings and reranker: local or Bedrock-hosted, chosen in `03` on cost and quality. No vector database: a few
  hundred sections per case fit in memory.
- *Patched 2026-10-04 (his, Phase 5 decision 3):* **v1 uses a minimal builder instead:** fetch by date with the
  cut-off enforced in code, select sections by the template's fixed list, extract with a model that sees only those
  sections and is never told the outcome, anonymize and scale, human review, freeze. No embeddings and no reranker:
  a retrieval query is written by someone who knows the outcome, and a fixed section list is easier to audit. The
  retrieve-and-rerank design above moves to the frequency study, where it is needed (`05` §4.4).

### 2.8 Results and aggregation (no database)

- **Raw results:** JSON in S3, **one object per run** (or per small batch), **write-once** (bucket versioning on;
  the harness never overwrites). Raw responses are kept, so any score can be recomputed later. *Corrected
  2026-10-03 (`08` §4.2):* the first draft wrote one object per shard, but with one task per model (§2.3) a shard is
  the whole sweep, so an interrupted task would have lost everything; per-run objects let it resume by `run_id`.
- **Aggregation with DuckDB**, reading straight from S3, on the laptop (*patched 2026-10-04:* laptop only; the
  output JSON is committed to the repo, and CI never reads raw results, §2.11): per-cell means, spread, rejection
  rates, wording-variant comparisons, real-case matching. Output: small static JSON files for the site.
- **Scoring is deterministic.** The main measure (where the money goes, what was chosen) comes straight from
  validated structured output. **No model grades the main result.** An LLM judge may later analyze the *memos*
  (does a memo mention workers? communities?), but that is secondary and labeled as such.
- No database: the data is append-only and small, and DuckDB over files answers every question v1 asks.

### 2.9 The public site

- **React + TypeScript SPA**, static, on **S3 + CloudFront**, behind a **Vercel rewrite** at
  `horizon-compact.vercel.app` (unclaimed as of 2026-10-02; claim it early). Same pattern as Musical Mycelium.
- Reads only the precomputed JSON. **No backend, no model calls, nothing to scale.**
- Views (from `00` §6): scenario picker; the five CEOs side by side; memo reader; real cases by type; methods page.
- Charting library and visual design: `06`.
- *Patched 2026-10-04 (his, Phase 6 decisions 2, 4, 5 and 6):* the explorer is built and checked on **a preview build
  off the public URL**, and replaces the placeholder in one deploy at go-live. **Share cards** (link-preview images)
  are generated at deploy time from the data. **A CI job re-scores** the published JSON from the published raw
  responses and fails on any difference; it reads published files only, never S3 (§2.11). **No visitor tracking:** no
  cookies, analytics scripts or third-party requests.

### 2.10 Infrastructure as code and deployment

- **Terraform** for every resource. `bootstrap` (state bucket, lock, OIDC provider, deploy role, budget alarms, the
  raw results bucket) and `main` (VPC, ECR, ECS cluster and task definition, the site bucket, CloudFront, IAM, log
  groups). *Patched 2026-10-04 (his; Phase 1 decision 4):* the raw results bucket moved to `bootstrap`, so
  destroying `main` never deletes the write-once record (`05` §3.1). *Patched 2026-10-04
  (his):* the budget alarms moved from `main` to `bootstrap`, so they exist before the first model call and are not
  removed when `main` is destroyed. *Patched 2026-10-04 (his; Phase 1 IMPLEMENTATION decision 1):* ECR moved from
  `main` to `bootstrap`, so the first deploy can push before `main` exists and a teardown never deletes the images
  whose digests pin the results. The OIDC provider is looked up, never created (`04` §3.5).
- **GitHub Actions with OIDC:** test on every push; build and push the image; deploy infrastructure and the site on
  merge to main. **CI never launches a sweep.** Sweeps cost money and are started by a person, on purpose.

### 2.11 Permissions (IAM, least privilege)

| Role | May do | May not do |
|---|---|---|
| Task role (the running shard) | invoke the specific Bedrock inference profiles in config; read its own sweep's inputs; write results under its own sweep's prefix | delete or overwrite results; read anything else; any other model |
| Task execution role | pull the image from ECR; write its log stream | anything else |
| CI deploy role (OIDC, scoped to this repo's main branch) | apply Terraform; push images; sync the site | invoke models; read raw results |
| Operator (him, from the laptop) | launch and read sweeps; run aggregation | — |

Writing these by hand, one action and one resource at a time, is the "IAM depth" the 9/27 decision named.

### 2.12 Observability and cost safety

- **CloudWatch Logs with a retention period set** (log groups never expire by default, which is a slow-growing
  cost).
- **Per-sweep cost record:** token counts per call summed into a sweep manifest with an estimated dollar cost, so the
  project can publish what each result cost.
- **AWS Budgets alarms in Terraform, on actual spend, filtered to this project's models** (decided 2026-10-03,
  `04` §3.3): Sonnet 4.6 and Nova Pro billing lines, thresholds tied to the $80 ceiling, **if a Budgets filter
  can target those lines** (*unverified*, checked in the Terraform step, `04` §3.3). Musical Mycelium's
  account-wide budgets stay as they are, as the net over the shared credit pot. Set before the first full sweep
  (`00` §8). The per-sweep cost record, not Budgets, is the authoritative per-project number.
- **Cost dashboards filter by the Marketplace provider line** (§2.5).

---

## 3. Explicitly out (decided unless he reopens them)

- **Kubernetes:** always-on cost; wrong tool at this size.
- **A NAT gateway, VPC interface endpoints, a load balancer:** hourly charges for nothing (§2.4).
- **A database (RDS, DynamoDB, a vector database):** append-only files and DuckDB cover v1 (§2.8).
- **Bedrock Agents, Knowledge Bases, Flows:** they hide the engineering that makes the project worth showing.
- **Any live model call from the public site in v1** (`00` §6).
- **Step Functions in v1** (§2.3); reconsidered for the frequency study.

## 4. Repository layout (proposed)

```
horizon-compact/
  CLAUDE.md                     # working rules (00 §10)
  docs/planning/                # this series, copied in
  docs/phases/                  # one IMPLEMENTATION doc per phase
  experiment/                   # scenarios, objectives, variants, lever menu, company dossier (versioned data)
  src/horizon_compact/          # harness, providers, schemas, scoring, CLI
  pipelines/dossiers/           # EDGAR fetch, retrieve, rerank, extract, anonymize
  web/                          # React + TypeScript SPA
  infra/terraform/{bootstrap,main}
  infra/docker/
  infra/vercel/
  tests/
  methods-appendix/             # GITIGNORED: real-case identities, links, scaling factors
```

## 5. Open decisions

**His, all decided 2026-10-02:**
1. **Inference profile: US geo** (`us.anthropic.claude-sonnet-5-5`; data stays in US and Canada regions).
2. **Containers accepted, honestly framed:** the README states the real reasons (§2.3).
3. **Orchestration: a simple CLI command** (`hc sweep launch`) in v1; Step Functions only if the frequency study
   needs it.

**Claude's checks, for `03`** *(status 2026-10-03: 1 done in `03` §2 and `04` §3.1; 2 done in `03` §2.2, Spot now
moot, not used in v1; 3 done, `03` §1; 4 and 5 open: Nova Pro is the v1 second model, `03` §5 chose local
embeddings)*:
1. Bedrock price for Sonnet 5.5 and every candidate model (via the AWS Price List, since the pricing page does not
   render per-model rates for automated reading), prompt-cache prices, and default quotas.
2. Fargate Spot and public IPv4 rates (third-party figures found 2026-10-02: Fargate on-demand ~$0.0405 per
   vCPU-hour and ~$0.0044 per GB-hour in us-east-1; Spot roughly 70% less; unverified against AWS).
3. Whether the account has Marketplace access to Sonnet 5.5 enabled, and the current credit balance.
4. Whether a non-Anthropic Bedrock model with a post-June-2026 cutoff exists for the multi-model check.
5. Embedding and reranking options on Bedrock vs local, with prices.
