# Phase 0.5 — AWS Foundation (v0.0.5): IMPLEMENTATION

> **Plan, not an as-built record.** Written 2026-10-04, immediately before the build, from the approved scope doc
> `phase-0.5-aws-foundation.md`, its eight decisions and its ordering constraint, and from the Phase 0.5 pre-build
> checks already closed in `KNOWN-GAPS.md`. **APPROVED 2026-10-04 (his)**, with the four new decisions in §17
> taken as recommended. Written with Opus; built with Sonnet; reviewed with Opus. **BUILT 2026-10-04; NOT CLOSED:**
> the close-out waits on billing data (§20). This doc may turn out wrong; it may not be silently
> wrong. It is updated as the build diverges, and each step is marked `[done]` with its date when it lands.
>
> **Drafted with the doc, before the build (2026-10-04):** `infra/iam/horizon-compact-dev-policy.json`, the §4
> policy in full (valid JSON; 3,294 characters without whitespace, inside the 6,144 managed-policy limit and over
> the 2,048 inline limit, hence a managed policy). It was untracked until C1 (*committed in C1, `b9c9aaf`*), and the build may amend it only by
> adding a named action the first apply proves missing (§4).

## 1. What this phase delivers

The account made safe to build on, and the design's assumptions about the models replaced by measured ones:

- **The Terraform bootstrap root**, applied: the state bucket for `main`, the shared GitHub OIDC provider **looked
  up, never created**, the deploy role with no permission policy and its trust proven by one workflow run, this
  project's budgets, and two tagged application inference profiles.
- **Terraform in `make check` and CI** (`fmt -check`, `validate`), with no credentials.
- **The provider seam at minimum size** (`Provider`, `RawDecision`, `Provenance`, a Bedrock Converse
  implementation), tested against a stubbed client, plus a smoke command bounded by count.
- **The smoke calls**, run by him, each kept as a committed, provenance-stamped, development-labeled record.
- **The open checks closed** in `KNOWN-GAPS.md`, decision 3 settled from a measurement, the development model named
  by him.

**Spend: under $1, worst case bounded at about $0.85 by the call cap (§11.5).** The definition of done is the scope
doc's nine items; §16 maps each to its proof.

## 2. Versions, checked live 2026-10-04

| Thing | Version | Checked against |
|---|---|---|
| Terraform (local) | **1.15.8**; CI pins the same. 1.16.5 is the newest release; staying on 1.15.8 keeps local and CI identical, and nothing here needs 1.16 | `terraform version`; HashiCorp checkpoint API |
| `required_version` | `>= 1.10` (S3 native lock file, `use_lockfile`, needs it; Musical Mycelium's floor) | Terraform docs |
| AWS provider | **`~> 6.67`** (6.67.0, published 2026-09-30) | Terraform Registry API |
| `hashicorp/setup-terraform` | **`@v4`** (floating major tag exists; latest v4.0.1); `terraform_wrapper: false` | GitHub tags, its `action.yml` at v4.0.1 |
| `aws-actions/configure-aws-credentials` | **`@v6`** (floating major tag exists; latest v6.3.0); `mask-aws-account-id` is an input and **defaults to not masking** | GitHub tags, its `action.yml` at v6.3.0 |
| boto3 / botocore | 1.43.108 | PyPI |
| `boto3-stubs[bedrock-runtime,bedrock,sts]` | 1.43.108 (dev group; strict mypy needs typed clients) | PyPI |
| Bedrock prices | AWS Price List, publication 2026-10-03 (§11.4) | `pricing.us-east-1.amazonaws.com` bulk offer file, read 2026-10-04 |

`uv.lock` fixes the Python versions; `.terraform.lock.hcl` fixes the provider and is committed. CI runs
`terraform init -lockfile=readonly`, so a lock file that disagrees with the config fails the build instead of
resolving something new.

## 3. What writing this doc found

1. **The deny rule for Terraform has a hole.** `.claude/settings.json` denies `terraform apply*` and
   `terraform destroy*`, which match the start of the command. `terraform -chdir=infra/terraform/bootstrap apply`
   starts with `terraform -chdir`, so neither pattern matches it. The same is true of `plan`, which decision 6 keeps
   from Claude. Fixed in §13 before any Terraform file exists.
2. **`*.tfvars` is not gitignored.** The budgets' notification address arrives through a variable (scope doc), and
   the easy place for it is `terraform.tfvars`, which the current `.gitignore` would let through. Fixed in §13. The
   name guard would not catch an email address; it only knows company names.
3. **Public Actions logs would print the account ID.** `configure-aws-credentials` does not mask it by default, and
   `aws sts get-caller-identity` prints it. This repo's workflow logs are public. The identity check (§8) masks it
   and also redacts it in its own output.
4. **AWS Budgets has a CUSTOM period (since 2025-09).** One period from a start date to an end date, no reset,
   end within three years of the start. It fits a ceiling that is cumulative. The API now marks `CostFilters` and
   `CostTypes` deprecated in favour of `FilterExpression` and `Metrics`, but the provider still supports them, and
   `IncludeCredit: false` is only expressible through `CostTypes`. §6 uses `cost_filter` and `cost_types`, as
   Musical Mycelium's working budgets do.
5. **Thinking, confirmed against Anthropic's Sonnet 5.5 migration guide and Bedrock's adaptive thinking page
   (2026-10-04).** Sonnet 4.6: no thinking unless asked; `thinking: {"type": "adaptive"}` with `output_config:
   {"effort": ...}` as a separate object, both inside Converse's `additionalModelRequestFields`; thinking text is
   returned summarized by default. Sonnet 5.5: thinking is on without a `thinking` field; `between_tools` is the
   lowest setting; **`disabled` returns a 400** on 5.5 (it works on Sonnet 5, which is easy to confuse). This agrees
   with `planning/07` §2.1; no patch needed.
6. **Anthropic models need a one-time Marketplace subscription,** made by the first invocation from an identity
   holding `aws-marketplace:Subscribe` (Musical Mycelium's record, 2026-08-11). Sonnet 4.6 was called from his
   console on 2026-10-02, so it is subscribed. **Sonnet 5.5 is not**, if access arrives: its first call has to come
   from his console, and the smoke identity is never given Marketplace permissions (§4).
7. **Musical Mycelium's Terraform never activates a cost allocation tag,** although it tags everything `Project`.
   Whether `Project` is already active on the account was set by hand, if at all, and is checked in step 2.
8. **gpt-oss-120b's model card lists client-side tool calling for the `bedrock-mantle` endpoint, not for
   `bedrock-runtime`** (it lists Converse as supported). Whether Converse tool use works on it is exactly what its
   smoke call shows.

## 4. The laptop identity (decision A)

`~/.aws/config` has one profile, `default`. Which identity it is has not been read (Claude does not run `aws`).
Musical Mycelium's rule is a scoped IAM user whose key is time-boxed and deleted after use. That user is scoped to
`musical-mycelium-` resources, so if `default` is that user, it cannot create anything here.

**Recommended (decision A):** a new IAM user **`horizon-compact-dev`**, created by him in the console, with a
customer managed policy **`horizon-compact-dev`** pasted from the tracked file `infra/iam/horizon-compact-dev-policy.json`,
and an access key in a profile named **`horizon-compact`**. **The key is deleted when this phase closes** (*amended 2026-10-04: kept through Phase 1 and deleted at Phase 1's close; §17 decision A*), and a new
one is made when Phase 1 needs one (two minutes in the console). The policy uses `*` where an account ID would go, so
the tracked file holds none. It is a managed policy, not an inline one, because an inline user policy is capped at
2,048 characters and this one is longer.

This is the one resource the phase creates by hand, and it is an exception to "Terraform for everything" for the
same reason as Musical Mycelium's: it is the identity that runs Terraform.

**What the policy allows, and what it refuses outright** (the file is the authority; this is its outline):

| Statement | Effect | Actions | Resources |
|---|---|---|---|
| `StateBucket` | Allow | `s3:*` | `horizon-compact-tfstate-*` and its objects (scoped by resource, as Musical Mycelium's SPA bucket is: the provider's read path calls a dozen `Get*` actions) |
| `ProjectRoles` | Allow | create, read, update, tag, delete roles; inline role policies; list role policies and instance profiles | `role/horizon-compact-*` |
| `ReadOidcProviders` | Allow | `iam:GetOpenIDConnectProvider`, `iam:ListOpenIDConnectProviders` | `*` |
| `NeverChangeOidcProviders` | **Deny** | every create, delete, update, tag and client-ID action on OIDC providers | `*` |
| `ProjectBudgets` | Allow | `budgets:ViewBudget`, `ModifyBudget`, `ListTagsForResource`, `TagResource`, `UntagResource` | `budget/horizon-compact-*` |
| `ReadAllBudgets` | Allow | `budgets:ViewBudget` | `*` (so the before-and-after read of Musical Mycelium's budgets uses this profile) |
| `NeverChangeOtherBudgets` | **Deny** | `budgets:ModifyBudget`, `TagResource`, `UntagResource` | `NotResource: budget/horizon-compact-*` |
| `ProjectInferenceProfiles` | Allow | create, get, delete, tag, untag, list tags | application profiles in us-east-1, plus the two sources they copy from |
| `ListModels` | Allow | `bedrock:ListInferenceProfiles`, `ListFoundationModels`, `GetFoundationModel` | `*` |
| `InvokeProjectModels` | Allow | `bedrock:InvokeModel` (Converse uses it) | the application profiles; `us.anthropic.claude-sonnet-4-6` and `us.anthropic.claude-sonnet-5-5`; the Sonnet 4.6 and 5.5 foundation models in every region (a geo profile routes across regions); Nova Pro, Nova Lite and gpt-oss-120b in us-east-1 |
| `NeverInvokeMusicalMyceliumModels` | **Deny** | `bedrock:InvokeModel`, `InvokeModelWithResponseStream` | Haiku 4.5 and Nova Micro, foundation models and profiles |

No `aws-marketplace:*`, no `ce:*`, no `iam:CreateUser`, no `iam:PassRole`. The explicit denies are there as proof,
not only as defaults: an identity that is refused even if a later allow is added by mistake. **The first apply may
still hit a missing read action.** Each one found is added by name and recorded here with the error that showed it,
never widened to `*`, as Musical Mycelium did.

**Not offered:** root access keys. Root is used only in the console, for creating the user, activating the cost
allocation tag and, if needed, Sonnet 5.5's Marketplace subscription.

## 5. The bootstrap root, `infra/terraform/bootstrap/`

**Local state, gitignored** (`*.tfstate` is already ignored), as in Musical Mycelium. No `backend` block.

| File | Holds |
|---|---|
| `versions.tf` | `required_version >= 1.10`; AWS provider `~> 6.67`; the comment explaining local state |
| `main.tf` | provider `us-east-1` with `default_tags` `Project = horizon-compact`, `ManagedBy = terraform`, `Root = bootstrap`; `data "aws_caller_identity"`; locals for names |
| `variables.tf` | `region`, `project` (default `horizon-compact`), `github_repo` (default the immutable prefix), `github_branch` (`main`), `alert_email` (no default, `sensitive = true`), `sonnet_service_name` (the Budgets Service value, read in step 2) |
| `state.tf` | the state bucket |
| `oidc.tf` | the provider data source and the deploy role |
| `budgets.tf` | the budgets (§6) |
| `bedrock.tf` | the two application inference profiles (§7) |
| `outputs.tf` | state bucket name, deploy role ARN, profile ARNs, the provider ARN read. **Every output that contains the account ID is marked `sensitive`**, so a pasted `terraform output` cannot leak it by accident |
| `terraform.tfvars.example` | tracked; placeholder values only |

**The state bucket:** `horizon-compact-tfstate-<account-id>` (the account ID is the global disambiguator, computed at
plan time, never written in a file). Versioning on; SSE-S3 (`AES256`); all four public-access blocks; lifecycle
rule expiring noncurrent versions after 30 days and aborting incomplete multipart uploads after 7, with
`depends_on` the versioning resource (the race Musical Mycelium recorded). `force_destroy = true`, with Musical
Mycelium's argument and its rule written in the comment: destroy `main` first, then `bootstrap`. `main` will use
`use_lockfile = true`, so no DynamoDB table exists.

**The OIDC provider:** `data "aws_iam_openid_connect_provider" "github" { url = "https://token.actions.githubusercontent.com" }`.
**No `resource "aws_iam_openid_connect_provider"` appears in the repo, in any form, including behind a `count`
switch.** Musical Mycelium has that switch because it owns the provider; this project never will. The comment
records the dependency (`planning/04` §3.5): Musical Mycelium's `infra/terraform/bootstrap/oidc.tf` owns it, and
destroying that stack would break this project's deploys. A test (§12) fails if the resource type ever appears
under `infra/`.

**The deploy role, `horizon-compact-github-deploy`:** trust allows only `sts:AssumeRoleWithWebIdentity` from the
looked-up provider, with `StringEquals` on `token.actions.githubusercontent.com:aud` = `sts.amazonaws.com` and on
`token.actions.githubusercontent.com:sub` = `repo:sjtroxel@183318591/Horizon-Compact@1403629566:ref:refs/heads/main`.
That prefix was read from `gh api repos/sjtroxel/Horizon-Compact/actions/oidc/customization/sub` on 2026-10-04
(`use_immutable_subject: true`) and is used verbatim; the comment explains why it carries numbers. `max_session_duration
= 3600`. **No permission policy, inline or attached** (decision 1). Phase 1 adds one with a permissions boundary.

## 6. The budgets

**Period:** `time_unit = "CUSTOM"`, `time_period_start = "2026-10-01_00:00"`, `time_period_end =
"2029-09-30_00:00"`. One period covering the whole project, because the $80 ceiling is cumulative; a monthly budget
would reset and never see it. The end date is inside the three-year limit and well past the credits' expiry
(2027-07-30), since after that date the alarms matter more, not less. **Uncertain until `terraform validate`
runs:** the provider's documentation lists four time units without `CUSTOM`, though its validation is generated from
the SDK's enum, which has it. If validate or apply refuses `CUSTOM`, the fallback is `ANNUALLY` with the same start
date, and that change is recorded here.

**Amounts:** `limit_amount = "80"`, with three notifications, all `ACTUAL`, all `ABSOLUTE_VALUE`: **$40, $60 (the
re-plan point) and $75.** **No `FORECASTED` notification** (`planning/04` §3.3). `cost_types { include_credit =
false }`, so they read gross spend while credits drain. The address comes from `var.alert_email`, set in an
untracked `terraform.tfvars` or `TF_VAR_alert_email`, never a tracked file.

**Which budgets (decision 3's procedure):**

| Budget | Filter | When |
|---|---|---|
| `horizon-compact-sonnet-line` | `cost_filter { name = "Service", values = [var.sonnet_service_name] }` | **first apply**, so a budget exists before the first model call. Kept even if (c) is taken: it is free, and a second watch on the largest line costs nothing |
| `horizon-compact-project-tag` | `cost_filter { name = "TagKeyValue", values = ["user:Project$horizon-compact"] }` | **only if decision 3 lands on (c)**, added at step 10 |

If (c) fails its conditions, the procedure's fallback (a) is already in place: the Sonnet-line budget, with Nova
Pro covered by the harness caps and Musical Mycelium's account-wide budgets. The exact `Service` string is
read from the Budgets console's own filter list in step 2, because the Cost Explorer table abbreviates it
(`KNOWN-GAPS.md`, Musical Mycelium billing check). **Added budgets cost nothing** (closed 2026-10-04: notification-only
budgets are free).

## 7. The application inference profiles and the tag test

Two `aws_bedrock_inference_profile` resources, free (Bedrock documentation: the price is the model's price), in
bootstrap so they exist before the first call and survive `main`'s teardown:

| Name | `copy_from` | Tags |
|---|---|---|
| `horizon-compact-sonnet-4-6` | `arn:aws:bedrock:us-east-1:<account-id>:inference-profile/us.anthropic.claude-sonnet-4-6` (built from `data.aws_caller_identity`) | default tags, so `Project = horizon-compact` |
| `horizon-compact-nova-pro` | `arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0` | the same |

**The question only a measurement answers** (`KNOWN-GAPS.md`): does the profile's tag land on Marketplace-billed
Claude charges in Cost Explorer? Nova Pro is billed under Bedrock, where tags are documented to work; it is
measured too, because decision 3's condition is "on both billing lines," and documented is not observed.

**The sequence, placed as early as the phase allows** (§15 steps 3-7):
1. The first apply creates the profiles and tagged resources.
2. He looks for `Project` under Billing, Cost allocation tags. A user-defined tag key appears there only after a
   tagged resource exists, which can take up to 24 hours. **If it is already listed and active** (§3 finding 7), the
   wait shrinks to the data lag alone. He activates it the moment it is listed.
3. Smoke calls 1 and 2 run through the profiles, **after activation**, so the measurement does not depend on
   backfill.
4. 24-48 hours later, he opens Cost Explorer (the console is free; the API is not), filters by tag
   `Project = horizon-compact`, groups by service, then by usage type, for the day of the calls, credits excluded.
   **Condition 2 holds only if both the Sonnet 4.6 line and the Nova Pro line appear under the tag.** A day with no
   rows waits one more day before it counts as a no.

**What (c) changes if it is taken:** every official call goes through an application profile, so `inference_profile`
in provenance is the profile (account ID removed), and the task role in Phase 1 is granted the profiles. That is
settled now, before `prereg-v1`.

## 8. The identity check (decision 1)

`.github/workflows/aws-identity.yml`, **manual only** (`workflow_dispatch`), `permissions: id-token: write,
contents: read`, one job:
1. `aws-actions/configure-aws-credentials@v6` with `role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}`,
   `aws-region: us-east-1`, **`mask-aws-account-id: true`**.
2. `aws sts get-caller-identity --query Arn --output text | sed -E 's/[0-9]{12}/<account-id>/g'`.

**Pass:** the log shows `arn:aws:sts::<account-id>:assumed-role/horizon-compact-github-deploy/...`. No permission is
needed for `GetCallerIdentity`, so a role with no policy proves the trust and nothing else. **Dispatched from
`main` only**: a run from a tag or another branch presents a different `sub` and is refused by design (Musical
Mycelium's 2026-09-06 lesson). The role ARN is a repository **secret** (decision D), so it is masked in every log.
Never on push: CI never touches AWS in this phase (`ci.yml` keeps `contents: read` only).

## 9. Terraform in `make check` and CI

**`Makefile`** gains `TF_BOOTSTRAP := infra/terraform/bootstrap` and:
- `tf-fmt`: `terraform -chdir=$(TF_BOOTSTRAP) fmt -recursive` (rewrites; for Claude and him).
- `tf-check`: `fmt -check -recursive`, then `init -backend=false -input=false -lockfile=readonly`, then
  `validate`. No credentials, no AWS call. `init` downloads the provider (cached locally in `.terraform/`, ignored).
- `check` gains `tf-check`, so local and CI stay identical.

**No `make` target runs `plan`, `apply`, `import` or `destroy`.** He types those, one at a time, so nothing that
authenticates hides behind a target name.

**`ci.yml`** gains, before `make check`: `hashicorp/setup-terraform@v4` with `terraform_version: "1.15.8"` and
`terraform_wrapper: false`. Still `permissions: contents: read`, still no AWS.

**Root:** `infra/` is the twelfth entry of 16, as `planning/02` §4 planned.

## 10. The provider seam

**Location:** `src/horizon_compact/providers/`. **boto3 becomes the first runtime dependency** (`pyproject.toml`'s
comment already says it arrives with the provider interface). pydantic does not arrive yet: validation of a decision
is Phase 1's (§11.6 does the smoke check by hand).

- `base.py`: frozen dataclasses and the protocol, from `planning/05` §4.1, sized to what exists before a sweep.
  - `ToolSpec(name, description, input_schema)`.
  - `ModelRoute(key, provider, model_id, invoke_id, route_kind)`. `route_kind` is `in_region` (a foundation model
    ID), `geo_profile` (`us.` system profile) or `application_profile` (resolved by name at call time, §11.3).
  - `DecisionRequest(route, system, user, tool, max_tokens, additional_fields)`. One tool, always; `toolChoice` is
    always `auto`; **no sampling field exists on the type**, so none can be sent (`planning/07` §2.3).
  - `Usage(input_tokens, output_tokens, cache_read_tokens, cache_write_tokens)`.
  - `Provenance`: the fields in §11.7 that the seam knows.
  - `RawDecision(raw_response, tool_input, tool_call_count, stop_reason, text_blocks, reasoning_block_count, usage,
    provenance)`.
  - `class Provider(Protocol): name: str; def decide(self, request: DecisionRequest) -> RawDecision: ...`
- `bedrock.py`: `BedrockConverseProvider`, taking an injected `bedrock-runtime` client. Builds the Converse request
  (`modelId`, `system`, `messages`, `toolConfig` with exactly one `toolSpec` and `toolChoice: {"auto": {}}`,
  `inferenceConfig: {"maxTokens": N}`, `additionalModelRequestFields` only when given). Parses `output.message.content`
  into `toolUse`, `text` and `reasoningContent` blocks, counts tool calls, and keeps the whole response. **An API
  error is returned as a record, not raised away:** its code and message are kept (`planning/07` §5: nothing is
  dropped). The client is built with `retries={"max_attempts": 1}`, so botocore never re-sends silently; every
  attempt is visible.

Validation and the failure taxonomy of `planning/07` §5 come in Phase 1, on top of this.

## 11. The smoke command

### 11.1 The command

`hc` becomes a console script (`[project.scripts] hc = "horizon_compact.cli:main"`). Two subcommands, in
`src/horizon_compact/smoke/`:

- **`uv run hc smoke list`**: prints the call plan, which records already exist, and how many calls remain under
  the cap. **No network.** Claude may run it.
- **`uv run hc smoke run <name> --profile horizon-compact`**: makes **exactly one** call, writes its record, prints
  a summary. `--profile` is required and has no default, so a call can never fall through to `default`.
  **He runs it; Claude never does.**

**Refusals, before any network call:** an unknown name; a call marked conditional whose condition he has not
confirmed (`--confirm-access` for Sonnet 5.5); **a name whose record already exists**, unless `--again "<reason>"` is
given, which writes a new numbered record and keeps the old one; **12 records already in the evidence folder**.

### 11.2 The prompt and the tool, word for word

Off the experiment's subject entirely (`planning/05` §2): a unit conversion with an exact answer.

- **System:** `You are a careful assistant completing a short arithmetic task.`
- **User:** `A walking trail is 12 miles long. Convert its length to kilometers, using 1 mile = 1.609344 kilometers,
  and round to two decimal places. Record your answer by calling the record_conversion tool exactly once. Do not
  give the answer in text.`
- **Tool:** `record_conversion`, description `Records the result of a unit conversion.`, input schema:

```json
{
  "type": "object",
  "properties": {
    "kilometers": {
      "type": "number",
      "description": "The converted length in kilometers, rounded to two decimal places."
    },
    "unit_system": {
      "type": "string",
      "enum": ["metric", "imperial"],
      "description": "The unit system of the converted value."
    },
    "note": {
      "type": "string",
      "description": "One sentence describing how the conversion was done."
    }
  },
  "required": ["kilometers", "unit_system", "note"],
  "additionalProperties": false
}
```

The three fields mirror the three kinds in the real decision (an amount, a discrete choice, a memo) without any of
its content. **Expected:** `kilometers` 19.31 (12 × 1.609344 = 19.312128), `unit_system` `metric`. Correctness is
recorded, not required: these calls test plumbing. A test (§12) fails if the prompt or tool text ever contains a word
from the subject's vocabulary (company, shareholder, stakeholder, employee, worker, invest, capital, objective,
profit, budget, allocate, quarter, horizon, board).

### 11.3 The call plan

| # | Name | Route (`modelId` sent) | Thinking as sent | `maxTokens` | Runs at |
|---|---|---|---|---|---|
| 1 | `sonnet46-profile-off` | application profile `horizon-compact-sonnet-4-6` | not set (off) | 1024 | step 6, the tag test |
| 2 | `novapro-profile` | application profile `horizon-compact-nova-pro` | not set | 1024 | step 6, the tag test |
| 3 | `sonnet46-geo-off` | `us.anthropic.claude-sonnet-4-6` | not set (off) | 1024 | step 8 |
| 4 | `sonnet46-profile-adaptive` | application profile `horizon-compact-sonnet-4-6` | `{"thinking": {"type": "adaptive"}, "output_config": {"effort": "high"}}` (the sub-study's setting, `planning/07` §7.3) | 4096 | step 8 |
| 5 | `novapro-direct` | `amazon.nova-pro-v1:0` | not set (its `reasoningConfig` stays off) | 1024 | step 8 |
| 6 | `novalite` | `amazon.nova-lite-v1:0` | not set | 1024 | step 8 |
| 7 | `gptoss120b` | `openai.gpt-oss-120b-1:0` | not set (its own default) | 2048 | step 8 |
| 8 | `sonnet55-default` | `us.anthropic.claude-sonnet-5-5` | not set (adaptive by default on 5.5) | 4096 | step 8, **only if access arrived** |
| 9 | `sonnet55-between-tools` | `us.anthropic.claude-sonnet-5-5` | `{"thinking": {"type": "between_tools"}}` | 4096 | step 8, **only if access arrived** |

**Why both routes for Sonnet 4.6 and Nova Pro** (decision C): whichever way decision 3 lands, the official route has
been called once. Calls 1 and 3 differ only in route, so any difference in response shape is the route's.

**An application profile is resolved by name** through `bedrock:ListInferenceProfiles` (`typeEquals=APPLICATION`),
so its ARN, which contains the account ID, lives in no file.

**No sampling parameter is sent on any call** (`planning/07` §2.3, decision 7). `maxTokens` is a length limit, not a
sampling setting. Every call is one attempt, no retry.

### 11.4 Prices used for the summary's estimate

AWS Price List, publication 2026-10-03, us-east-1, standard tier, per million tokens, input / output: Sonnet 4.6 on
the US geo route **$3.30 / $16.50**; Sonnet 5.5, US geo, **$2.20 / $11.00** (`planning/03` §2.1); Nova Pro **$0.80 /
$3.20**; Nova Lite **$0.06 / $0.24**; gpt-oss-120b **$0.15 / $0.60**. The bill, not this table, is the phase's
spend (DoD 8).

### 11.5 The cap

**Twelve records, ever, in this phase:** nine planned, three spare for an `--again` after a harness bug or a
throttle. **Worst case, all twelve at the largest `maxTokens` (4,096) and Sonnet 4.6's output price:** $0.068 each,
about **$0.81 in output**, plus under $0.03 in input (the prompt is about 300 tokens), so **about $0.84, under $1 by
construction**. That is what lets this phase be bounded by count rather than by Phase 1's dollar cap. Expected spend
is a few cents.

### 11.6 The check on each tool call (by hand, not pydantic)

`tool_call_count` (0, 1 or more); for exactly one call: name is `record_conversion`; input is an object with
exactly the three keys; `kilometers` is a number and not a boolean, and non-negative; `unit_system` is one of the two
values; `note` is a non-empty string. Problems are listed, not raised. `answer_correct` is `abs(kilometers - 19.31)
<= 0.01`. **A text answer with no tool call is recorded as found** (scope doc: a finding, not a retry).

### 11.7 The record

One JSON file per call, **write-once** (opened with exclusive create), at
`docs/phases/evidence/phase-0.5/smoke/NN-<name>.json` (decision 5). Fields:

`record_version, label ("development"), call_name, again_reason, git_sha, git_dirty, harness_version,
botocore_version, provider ("bedrock"), api ("converse"), model_id (the foundation model), invoke_id (as sent,
redacted), route_kind, inference_profile (name, or null), region, thinking (as sent, or "not set"), effort (as sent,
or "not set"), temperature ("not set"), max_tokens, prompt_sha256 (of the canonical system, user and tool JSON),
request (the full request as sent, redacted), started_at, finished_at, latency_ms, status ("ok" | "api_error"),
error (code and message, or null), stop_reason, usage (input, output, cache read, cache write), tool_call_count,
tool_input, tool_input_check, text_blocks, reasoning_block_count, raw_response (redacted), est_cost_usd,
price_source`.

No `sweep_id`, `run_id` or `image_digest`: none exists before a sweep (scope doc). Phase 1 adds them.

**Account ID removal, fail closed:** the command reads the account ID once with `sts:GetCallerIdentity` (no
permission needed), replaces every occurrence in the serialized record with `<account-id>`, then checks the string is
gone and that no `@` email address is present. **If either check fails, nothing is written** and the command exits
non-zero. The caller's ARN is never recorded. Response metadata (request ID, HTTP status, headers) is kept: it holds
no account ID and it is what AWS Support asks for.

### 11.8 What he pastes back

The summary, per call: name, status, stop reason, tool calls, schema problems, answer correct, tokens, estimated
cost, record path. Claude reads the record file itself for anything more.

## 12. Tests

All offline. **A `conftest.py` makes the network unreachable from tests:** autouse fixtures set fake AWS credentials
and region, point `AWS_CONFIG_FILE` and `AWS_SHARED_CREDENTIALS_FILE` at missing files, unset `AWS_PROFILE`, and patch
`socket.socket.connect` to raise. A test that tries to reach AWS fails instead of using his credentials. (The guard
tests' `git` subprocesses are unaffected.)

- `tests/test_bedrock_provider.py`, with `botocore.stub.Stubber` on a real client: the request shape (one tool,
  `auto`, no sampling field, `additionalModelRequestFields` only when given, the route's `modelId`); parsing one tool
  call; text only (zero calls); two tool calls; a reasoning block before a tool call; `max_tokens` stop; a
  `ValidationException` and a `ThrottlingException` each returned as a record with code and message; usage fields,
  including absent cache fields read as zero.
- `tests/test_smoke.py`: the plan's names are unique and its routes are well formed; `run` refuses an unknown name,
  an existing record, a missing `--profile`, a conditional call without confirmation, and a thirteenth record; `--again`
  writes a new record and keeps the old one; **redaction** (a fake account ID in an ARN and in the response is
  replaced; a record that would still contain it, or an email address, is not written); the tool-input check on
  good, wrong-type, extra-key, boolean-as-number and missing-key inputs; the prompt contains none of the subject's
  vocabulary.
- `tests/test_architecture.py` gains: no `aws_iam_openid_connect_provider` resource anywhere under `infra/`; no
  `FORECASTED` notification in any budget; every budget has `include_credit = false`; no 12-digit number and no
  email address in any tracked file under `infra/` or `docs/phases/evidence/`; `horizon_compact.privacy` still imports
  only the standard library.

## 13. `.claude/settings.json` and `.gitignore`

**[done 2026-10-04, with the doc, in C0]** Both changes below are made; `git check-ignore` shows
`terraform.tfvars` ignored, and `terraform.tfvars.example` and `.terraform.lock.hcl` not ignored.

**Deny, added** (the `-chdir` hole, §3 finding 1; decision 6): `terraform plan*`, `terraform import*`, `terraform
state*`, `terraform output*`, and every `terraform -chdir=* <verb>*` form of `apply`, `destroy`, `plan`, `import`,
`state` and `output`; `uv run hc smoke run*` and `uv run --no-sync hc smoke run*`. `output` is denied because the
bootstrap's outputs carry the account ID.

**Allow, added:** `make tf-check*`, `make tf-fmt*`, `terraform -chdir=infra/terraform/bootstrap fmt*`, `terraform
-chdir=infra/terraform/bootstrap validate*`, `terraform -chdir=infra/terraform/bootstrap init -backend=false*`, `uv
run hc smoke list*`.

**`.gitignore` gains:** `*.tfvars` with `!*.tfvars.example`, and `.terraform.lock.hcl` is confirmed **not** ignored
(it is committed). Checked with `git check-ignore` before C1.

## 14. The commits

He runs every `git commit` and `git push`; Claude gives the commands one at a time.

| # | Contents | Before it |
|---|---|---|
| C0 | this doc, approved; `ROADMAP.md` and `KNOWN-GAPS.md` status lines; **`.claude/settings.json` and `.gitignore` (§13), done with the doc** so the `-chdir` hole is closed before the build session starts | his approval |
| C1, the bootstrap commit | `infra/terraform/bootstrap/` (with `.terraform.lock.hcl`, without state), `infra/iam/horizon-compact-dev-policy.json`, `.github/workflows/aws-identity.yml`, `ci.yml` and `Makefile` changes, the new architecture tests | `make check` green, Terraform included; **pushed**, so the identity workflow exists on `main` |
| C2, the seam commit | `pyproject.toml`, `uv.lock`, `src/horizon_compact/providers/`, `src/horizon_compact/smoke/`, `src/horizon_compact/cli.py`, `tests/conftest.py`, the new tests | `make check` green |
| C3, the evidence commit | `docs/phases/evidence/phase-0.5/smoke/*.json`, this doc's as-built notes; `budgets.tf` if (c) adds the tag budget | the smoke calls; every record scanned by the guard as it is committed |
| C4, close-out | `KNOWN-GAPS.md`, `ROADMAP.md`, the dated planning patches, version 0.0.5 in `pyproject.toml` and `__init__.py`, the DoD audit | the bill read; his development-model decision |

## 15. Order of work

Each step says who, and what to look for. **Steps 3 to 7 are front-loaded for the 24-48 hour tag wait.**

0. **He reads, before anything is written that touches AWS** (all free, all console or read-only):
   - `aws sts get-caller-identity --query Arn --output text` on the `default` profile: tells Claude only the part
     after `:user/` or `:assumed-role/`, or that it says `:root`. This settles decision A's starting point.
   - Whether Sonnet 5.5 access has arrived (support case 179097554500679).
1. **[files written 2026-10-04; commit and push pending]** **Claude writes C1's files** (§5-§9, §13). Runs `make tf-fmt`, `make tf-check`, `make check`. Nothing touches
   AWS. **He commits C1 and pushes**; CI watched to green.
   *As built (Sonnet, 2026-10-04):* `infra/terraform/bootstrap/` (nine files plus the committed
   `.terraform.lock.hcl`, AWS provider 6.67.0), `.github/workflows/aws-identity.yml`, `ci.yml` (setup-terraform
   `@v4`, 1.15.8, wrapper off), the `Makefile` (`tf-fmt`, `tf-check`, `check` runs `tf-check`), and seven
   architecture tests. `terraform validate` accepted `time_unit = "CUSTOM"` (§6), which is **evidence, not proof**:
   only the apply proves it. `CI=true make check`: 130 passed, root 12 of 16, doctor skipped by name. Each new test
   was checked for teeth (a planted OIDC resource, a `FORECASTED` notification, a budget without `include_credit`
   and a 12-digit number each failed the matching test; the plants were removed). The guard found 0 names in the
   15 files scanned. **C0 was not committed separately; it is folded into C1** (his call), so C1 also carries the
   approved doc, `ROADMAP.md`, `KNOWN-GAPS.md`, `.claude/settings.json` and `.gitignore`.
   *Deviations from this doc:* (1) **`sonnet_service_name` has no default and is not in `variables.tf`'s
   committed values**; it is set in the untracked `terraform.tfvars` at step 2 (a guessed default would create a
   budget that watches nothing; the variable fails validation if empty). (2) The `terraform.tfvars.example`
   placeholder for the email is not email-shaped, because the new account-id-and-email test correctly flagged
   `you@example.com`. (3) The budget thresholds, limit and period are variables with the §6 values as defaults.
2. **He prepares the account** (console unless stated):
   - Creates `horizon-compact-dev` and its managed policy from the file, and an access key in profile
     `horizon-compact` (decision A).
   - Reads under Billing, Cost allocation tags, whether `Project` is listed, and if so whether it is active.
   - Reads the exact `Service` value for Claude Sonnet 4.6 from the Budgets console filter list (starting to create
     a budget and abandoning it at the filter step costs nothing). Claude puts it in `variables.tf`.
   - **Before-reads**, profile `horizon-compact`: `aws iam list-open-id-connect-providers`, then `aws iam
     get-open-id-connect-provider` on its ARN, noting **CreateDate** (the ARN's account ID is not pasted); `aws
     budgets describe-budgets --account-id <id>` for Musical Mycelium's three, noting names, limits and
     notification types. Recorded in this doc, account ID removed.
   *As built, 2026-10-04 (step 2 partly done):*
   - **Identity (step 0):** `default` is `mycelium-dev`, Musical Mycelium's scoped user, as suspected. Decision A
     stands. `horizon-compact-dev` and the managed policy `horizon-compact-dev` were created in the console
     (the policy was accepted as written); profile `horizon-compact` verified by `sts get-caller-identity`.
   - **Before-reads, taken (account ID removed):** the OIDC provider, **CreateDate 2026-08-03T23:55:11 UTC**, client
     ID `sts.amazonaws.com`, tags `Root=bootstrap` and `Project=...`; exactly one provider in the account.
     Musical Mycelium's budgets: `musical-mycelium-monthly-5`, `-10`, `-20`; MONTHLY; `IncludeCredit: false`; no
     filters; start 2026-08-31 19:00 -05:00, end 2087-06-14. Notifications were not read (the dev policy denies
     changing them). Their `LastUpdatedTime` values (this morning) are not treated as a signal.
   - **`Project` cost allocation tag:** already listed (Resource type, last used October 2026), **activated
     2026-10-04 17:19 CDT.** That is the start of the tag-test clock; AWS says activation can take up to 24 hours.
   - **The Sonnet Service string cannot be read yet** (finding below). *Deviation 4:* the Sonnet-line budget is
     created only when `sonnet_service_name` is set (default empty), so the first apply creates no Sonnet-line
     budget. The smoke cap ($0.84 worst case) and Musical Mycelium's account-wide budgets are the guard until then;
     the string is set and the budget applied after the first Sonnet call has charges.
   - *Found:* the Budgets console's Service filter lists only services already billed. On 2026-10-04 it held 13,
     including `Claude Haiku 4.5 ( Bedrock Edition)` (space after the parenthesis, as Haiku is written) and no
     Sonnet. Why Sonnet 4.6, called on 2026-10-02, is absent is unknown (billing lag, a charge too small to list,
     or another reason); not guessed.
3. **He runs `terraform -chdir=infra/terraform/bootstrap init`, then `plan`, and pastes the plan.** **Claude reads it
   before any apply** and checks: the OIDC provider appears only as a data source read; nothing is to be created
   whose name lacks `horizon-compact-`; nothing is to be changed or destroyed; the budget has no `FORECASTED`
   notification. **If any check fails, stop.**
4. **He applies.** Then a second `plan`: **"No changes."** After-reads: the OIDC provider's ARN and CreateDate
   match step 2; Musical Mycelium's three budgets match step 2.
   *As built, 2026-10-04 (steps 3 and 4 done):* init clean (provider 6.67.0 from the lock file, no backend). The
   plan was read by Claude before any apply: **8 to add, 0 to change, 0 to destroy** (the bucket and its four
   settings, the role, the two profiles; this doc's earlier "11" was a miscount); the OIDC provider appeared only as
   `Read complete`; every created name began `horizon-compact-`; the role's trust read `aud` `sts.amazonaws.com`
   and `sub` exactly the immutable prefix plus `:ref:refs/heads/main`; no budget was planned (deviation 4) and no
   `FORECASTED` notification exists. Applied from the saved plan with **no permission errors**: the dev policy
   needed no added action. **A second plan: "No changes."** After-reads (`scratch/after-reads.sh`, gitignored,
   read-only): the OIDC provider's `CreateDate` **2026-08-03T23:55:11.048000+00:00**, client and count (1)
   **identical** to the before-read; Musical Mycelium's three budgets **identical** (names, limits, MONTHLY,
   `IncludeCredit` false, no filters). The inference profiles were created 17:29-17:30 CDT, after `Project` was
   activated at 17:19. **DoD 3 is NOT yet met:** there is no budget until the Sonnet Service string exists.
5. **He activates `Project`** as a cost allocation tag the moment it is listed (immediately, if step 2 found it).
   **Meanwhile, Claude writes C2** (§10-§12): `make check` green. **He commits C2.**
   **Also meanwhile:** he adds the `AWS_DEPLOY_ROLE_ARN` secret (`gh secret set AWS_DEPLOY_ROLE_ARN`, pasting the
   ARN from `terraform output -raw github_deploy_role_arn`) and dispatches the identity workflow from `main`.
   **Pass:** the log shows the assumed role, account ID masked. That is DoD 2.
   *As built, 2026-10-04 (step 5's identity check done):* **C1 is `b9c9aaf`, CI run `37240755349` green** (Terraform
   1.15.8 installed on the runner; `fmt -check`, locked `init` and `validate` passed with no credentials). The
   secret `AWS_DEPLOY_ROLE_ARN` was set by piping `terraform output -raw` into `gh secret set` (the ARN never
   displayed). **Identity run `37241137274`, dispatched from `main`: success.** Its log shows the role assumed and
   `arn:aws:sts::<account-id>:assumed-role/horizon-compact-github-deploy/GitHubActions`; the role ARN appears as
   `***`; the log holds zero unmasked 12-digit numbers. **DoD 2 met.** Found along the way: the account-id test
   scanned gitignored local state and `terraform.tfvars`, which legitimately hold the ID and an email; it now
   asks git for the files that could be tracked (teeth re-checked).
   *C2 built meanwhile (Sonnet, 2026-10-04; commit pending):* `src/horizon_compact/providers/` (`base.py`,
   `bedrock.py`), `src/horizon_compact/smoke/` (`plan.py`, `record.py`, `runner.py`), `cli.py` (`hc smoke list` and
   `hc smoke run`), `tests/conftest.py` (network unreachable, no real AWS identity), 48 new tests; boto3 1.43.108 as
   the first runtime dependency, `boto3-stubs` as a dev dependency. `make check`: **178 passed**, strict mypy and
   ruff clean. Teeth checked by deliberate breaks (account redaction removed, a sampling parameter sent, forced
   tool choice, an overwritable record, a refusal made after the AWS call, the email check removed): every one
   failed a test. *Harness caveat found:* a same-size edit reverted within one second left stale compiled
   bytecode, which once made a green test look red and a broken change look green; the fix is to clear
   `__pycache__` between mutations. The network block was probed: an unmocked client is stopped with "a test tried
   to open a network connection". *Deviation 5:* `hc smoke run` checks every refusal from the filesystem **before**
   creating an AWS session (the doc's order would have called STS first). *Deviation 6:* the account-id test's
   pattern now excludes digit runs inside hyphenated IDs, so a UUID's last group cannot trip it (about 0.35% per
   UUID otherwise).
6. **[done 2026-10-04, 17:54 CDT; results in section 19]** **Once `Project` is active: smoke calls 1 and 2,** `uv run hc smoke run sonnet46-profile-off --profile
   horizon-compact`, then `novapro-profile`, one at a time. The clock for the tag measurement starts here.
7. **Claude reads both records:** did each call the tool once under `auto`; stop reason; usage fields; the
   profile recorded with the account ID removed.
8. **[done 2026-10-04 except the Sonnet 5.5 pair, whose access had not arrived; Ollama done]** **The remaining smoke calls,** 3 to 7, one at a time, Claude reading each record before the next. If Sonnet 5.5
   access has arrived: **he first makes one call to it in the Bedrock console playground** (the Marketplace
   subscription, §3 finding 6), using the same neutral prompt, noted here; then calls 8 and 9 with
   `--confirm-access`.
   **Also:** Claude runs the same prompt and tool five times on Ollama `qwen3.5:4b` by `curl` (local, free, no AWS),
   so the development-model decision compares like with like. Results noted here, not committed as records.
9. **Records committed (C3, part 1)** if he wants them public before the wait ends; otherwise with step 10.
10. **24-48 hours after step 6: the tag measurement** (§7). Claude writes decision 3's evidence; **he decides (c) or
    (a).** If (c): Claude adds `horizon-compact-project-tag` to `budgets.tf`; he plans (Claude reads), applies,
    plans again for "No changes."
11. **A day after the last call: the phase's spend,** from Cost Explorer in the console, by usage type, credits
    excluded, every line this phase touched. **Must be under $1** (DoD 8).
12. **[done 2026-10-04, except the decision 3 patches, which wait for the tag reading]** **Checks closed** in `KNOWN-GAPS.md` with sources and dates; dated patches where a result changes a planning doc
    (likely `planning/04` §3.3 and `planning/02` §2.12 for decision 3; `planning/07` §14 item 1; `planning/09` A1).
    The refusal `stop_details` question (`KNOWN-GAPS.md`, refusals) is **carried forward to Phase 1** with this
    reason: testing it means adding `additionalModelResponseFieldPaths` to a request, which is Phase 1's request
    shape, and an unexpected stop reason is already recorded as a failure.
13. **[decision made 2026-10-04: Ollama `qwen3.5:4b` + Nova Lite; the key deletion moves to Phase 1's close, per decision A as amended]** **His decision on the development model** (decision 8), from §11 records, the Ollama runs and prices. Then
    **he deletes the `horizon-compact-dev` access key** (decision A). C3 and C4 committed; pushed; CI green.

## 16. Definition of done, and the proof of each

| Scope DoD | Proof |
|---|---|
| 1. Bootstrap applied, nothing shared created; second plan clean; provider unchanged | the pre-apply plan as read by Claude (step 3); "No changes" (step 4); ARN and CreateDate before and after; the architecture test that bans the resource type |
| 2. Deploy role trusts `main` only, by the immutable claim; no permission policy | the identity workflow's run ID and its masked output; the role's Terraform; the absence of any policy resource on it |
| 3. Budgets on actual spend, credits excluded, filtered, no forecast; Musical Mycelium's unchanged | the applied budgets; the architecture tests; the before-and-after budget reads |
| 4. A recorded tool call from Sonnet 4.6 off, Sonnet 4.6 on, Nova Pro (and Sonnet 5.5 if access) | records 1-5 (and 8-9) in the evidence folder |
| 5. Checks closed or carried with a reason; planning patches made | `KNOWN-GAPS.md` entries; the patched docs' status lines |
| 6. Development model named; Nova Pro's default temperature recorded with its source | his decision recorded; 0.7, Amazon Nova user guide (already closed 2026-10-04) |
| 7. `make check` and CI green with Terraform; no account ID or email tracked; every commit through the guard | CI run IDs; the architecture tests; the hooks |
| 8. Phase spend measured from the bill, under $1 | the Cost Explorer reading, recorded in step 11 |
| 9. Nothing always-on; nothing of Musical Mycelium's changed | the plan (bucket, role, budgets, profiles: none bills by the hour); the before-and-after reads; the explicit denies in the dev policy |

## 17. Decisions for him

New in this doc. The scope doc's eight stand as decided. **All four DECIDED 2026-10-04 (his): (a), as
recommended.** Each keeps its framing below as the record.

**A. The laptop identity.** *Amended 2026-10-04 (his; Phase 1 IMPLEMENTATION decision 2):* the key is kept through
Phase 1 and deleted at Phase 1's close, not this phase's; the two phases run back to back and both need it. The
time-box stands, widened to cover both, and Phase 1's policy additions (its §10.5) extend the same user.
- (a) **Recommended:** a new IAM user `horizon-compact-dev` with the managed policy in §4, its own profile
  `horizon-compact`, the key deleted at the end of the phase. It is least privilege on a shared account, its denies
  make touching Musical Mycelium's budgets, its models or the OIDC provider impossible rather than merely unlikely,
  and writing it by hand is the IAM depth the project wants to show. Cost: about 15 minutes in the console, and one
  or two "missing action" errors on the first apply, each fixed by name.
- (b) Use `default`, if step 0 shows it is an identity broad enough to create these resources. Faster, but nothing
  stops a typo from reaching Musical Mycelium's resources, and if `default` is Musical Mycelium's scoped user it
  cannot do this phase at all.

**B. The Bedrock development-model candidates** (decision 8 picks among them at the end).
- (a) **Recommended:** **Nova Lite** ($0.06 / $0.24; in-region; Converse and client-side tool use documented;
  billed under Bedrock on its own usage type, which Musical Mycelium's bill did not show on 2026-10-04) and
  **gpt-oss-120b** ($0.15 / $0.60; a different family; Converse supported, tool use on that endpoint not
  documented, so its call is informative either way), with Ollama `qwen3.5:4b` already measured.
- (b) Name others. Cheaper rows exist (Gemma 3 4B at $0.04 / $0.08, Ministral 3B at $0.10 / $0.10), but tool use on
  Converse is less documented for them; any added candidate is one more call against the cap of twelve.

**C. Both routes for Sonnet 4.6 and Nova Pro** (calls 3 and 5).
- (a) **Recommended:** yes. Two calls, cents, and whichever way decision 3 lands the official route has been
  exercised before Phase 1 depends on it.
- (b) Profiles only. Saves two calls; if decision 3 falls back to (a), the `us.` route's first call is in Phase 1.

**D. The role ARN in GitHub.**
- (a) **Recommended:** a repository **secret**, so it is masked in public logs along with the account ID inside it.
- (b) A repository variable, as Musical Mycelium does. Visible in logs unless masked separately.

## 18. Genuinely uncertain

- **Whether `CUSTOM` passes `terraform validate` and the apply** (§6). Fallback stated.
- **Whether the first apply needs read actions the policy lacks** (§4). Expected; each one added by name.
- **Whether `CreateInferenceProfile` needs permission on the source it copies from, in every region the geo
  profile covers.** The policy grants the source in us-east-1 and the foundation model everywhere; a refusal will
  name what is missing.
- **Whether the `Project` tag lands on Marketplace-billed Claude charges.** The point of the tag test; no source
  found either way (`KNOWN-GAPS.md`).
- **Whether gpt-oss-120b calls a tool through Converse on `bedrock-runtime`** (§3 finding 8).
- **How Nova models report cache fields** when no cache point is set (absent, or zero). The parser reads absent as
  zero and the record keeps the raw response, so either is visible.

## 19. Smoke results (as built, 2026-10-04, steps 6-8)

Eight records in `docs/phases/evidence/phase-0.5/smoke/` (cap 12; Sonnet 5.5 access had **not** arrived, so calls 8
and 9 did not run). All `development`, thinking and temperature as recorded, no sampling parameter sent. Estimates
sum to about **$0.019**; the bill is the authority (DoD 8). First call 17:54 CDT, after `Project` was activated at
17:19, which starts the tag clock; the earliest useful Cost Explorer look is the evening of 2026-10-05.

| Record | Route | Result | Tokens in/out | ms |
|---|---|---|---|---|
| 01 `sonnet46-profile-off` | tagged profile | 1 tool call, valid, correct | 716 / 175 | 2,637 |
| 02 `novapro-profile` | tagged profile | 1 tool call, valid, correct (`unit_system` wrongly `imperial`) | 559 / 120 | 1,470 |
| 03 `sonnet46-geo-off` | `us.` geo profile | identical shape to 01 | 716 / 173 | 2,669 |
| 04 `sonnet46-profile-adaptive` | tagged profile | thinking block, text, 1 tool call | 716 / 239 | 3,295 |
| 05 `novapro-direct` | in-region | **`ModelErrorException`**, no usage returned | 0 / 0 | 8,125 |
| 05.2 `novapro-direct` (`--again`) | in-region | 1 tool call, valid, correct | 559 / 119 | 1,553 |
| 06 `novalite` | in-region | 1 tool call, valid, correct | 559 / 89 | 1,342 |
| 07 `gptoss120b` | in-region | 1 tool call, valid, correct (reasoning block) | 235 / 169 | 1,050 |

Local, not an evidence record: Ollama `qwen3.5:4b`, the same prompt and tool, **5 of 5** valid correct calls, 5-17 s.

**Findings, each carried to step 12 where it changes a doc:**
1. **Thinking on Converse** (`planning/07` 14.1, 7.3). Sent as `additionalModelRequestFields` `thinking` and
   `output_config.effort`; returned as a `reasoningContent` block ahead of text and tool use; **no separate
   thinking-token count**, the tokens are inside `outputTokens` (239 vs 175 for the same call without it). 7.3's
   "thinking tokens recorded per run" must be read from the reasoning text or a paired non-thinking run. Patch 7.3.
2. **`ModelErrorException` is a model failure delivered as an API error** (`planning/07` 5.1). Nova Pro, one in three
   calls, same prompt that passed twice. `api_error` is "retried unlimited, not a model outcome", which would hide it.
   It must classify as a `malformed_tool_use` model outcome. Patch 5.1; carried to Phase 1's classifier.
3. **Text beside a tool call is normal under `auto`.** Sonnet 4.6 narrated a sentence and then made one call, in
   spite of "do not give the answer in text". Nova models write a `<thinking>` tag in visible text with
   `reasoning_block_count` 0. Neither is `no_tool_call`.
4. **Tool-use input overhead is about 400-450 tokens on Claude and Nova** (716 and 559 input for a roughly 100-token
   prompt); gpt-oss showed 235. `planning/03`'s per-decision token estimates need it; Phase 4 measures it.
5. **Valid is not sensible:** Nova Pro filled `unit_system: imperial` for a metric value. The schema allows it.
6. **Cache fields:** Sonnet returns explicit zeros; Nova and gpt-oss omit them. Absent reads as zero, as built.
7. **Profile and plain `us.` route behave identically** on Sonnet 4.6 (calls 1 and 3). Decision 3 is therefore only
   about billing attribution; nothing in the request or response depends on the route.
8. **Nova Pro is enabled and answering on this account** (closes the availability half of the Nova Pro check).
9. **gpt-oss-120b supports Converse tool use on `bedrock-runtime`**, though its model card lists tool calling only
   for the other endpoint.
10. **Provenance honesty:** `git_dirty` read `True` from record 02 because earlier evidence was uncommitted, not
    because code differed; records from 05.2 on also carry the uncommitted error-capture change (error path only).
    The flag now ignores the evidence folder.
11. **Error records now carry `http_status` and `request_id`.** Record 05 predates that and has code and message only.
12. **The estimate for an errored call is $0.00 by assumption;** the bill shows whether input tokens were charged.

**Development-model evidence so far (decision 8, his, at the end):** Nova Lite $0.000055 per call, 1 of 1 valid,
correct unit; gpt-oss-120b $0.000137, 1 of 1 valid, reasoning on by default; Ollama `qwen3.5:4b` free, 5 of 5 valid,
local, slower. One call each on Bedrock is not a failure rate; a handful of repeats would be cheap if he wants more
before deciding (a few cents, counted against the cap of 12; 4 records remain).

## 20. Review and close-out state (Opus, 2026-10-04 evening)

**Review of the build.** Every file Sonnet produced was read. The Terraform matches §5-§7; the plan was read before the
apply; the provider sends one tool, `auto`, no sampling field; records are write-once and fail closed; refusals happen
before any AWS contact; tests were checked for teeth and the build's own gaps (`git_dirty`, error capture, the account-id
test's scope) were found and fixed in the open. **One weak test found and fixed:**
`test_a_call_with_a_record_is_refused_without_again` built a fake client it never passed in, so its "no call was made"
assertion could not fail. It now injects the client; moving the refusal after the model call makes it fail ("a refused
call reached the model"), checked and restored. `make check`: 178 passed.

**Done tonight (step 12, the parts that do not wait on billing data):** `planning/07` §5.1 (`ModelErrorException` is
`malformed_tool_use`; text beside one tool call is not `no_tool_call`), §7.3 (no separate thinking-token count), §14
item 1 closed; `planning/03` §3.1 (tool-use input overhead) and §4 (development model named); `planning/09` A1 done;
`KNOWN-GAPS.md` (checks table, a WAITING entry for the close-out, a CARRIED entry for Phase 1); `ROADMAP.md`.

**Waits on billing data** (`KNOWN-GAPS.md`, WAITING entry): the tag reading and decision 3, with the `planning/04`
§3.3 and `planning/02` §2.12 patches it settles; the Sonnet-line budget; the phase's spend; then version 0.0.5 and
the key deletion.

**DoD audit, provisional (final at close-out):**

| Scope DoD | Verdict now | Evidence |
|---|---|---|
| 1. Bootstrap applied, nothing shared created, second plan clean, provider unchanged | **PASS** | §15 steps 3-4: plan read before apply, 8 added, "No changes", CreateDate and count identical |
| 2. Deploy role trusts `main` only, no permission policy | **PASS** | run `37241137274`; the architecture test that bans policy resources on it |
| 3. Budgets on actual spend, credits excluded, filtered, no forecast; Musical Mycelium's unchanged | **OPEN** | Musical Mycelium's half PASS (read before and after); this project's budget waits for the Service name |
| 4. Recorded calls: Sonnet 4.6 off, Sonnet 4.6 on, Nova Pro | **PASS** | records 01, 03, 04, 02, 05, 05.2 (§19) |
| 5. Checks closed or carried; planning patches | **PARTIAL** | all closed or carried except the tag half of the Budgets check; its patches wait for it |
| 6. Development model named; Nova Pro's default temperature recorded | **PASS** | his decision 2026-10-04; 0.7, Amazon Nova user guide |
| 7. `make check` and CI green with Terraform; no account ID or email tracked; guard on every commit | **PASS so far** | CI runs `37240755349`, `37241581113`, `37242580418`; the architecture test; re-checked at close-out |
| 8. Spend measured from the bill, under $1 | **OPEN** | estimates $0.019; the bill is read at close-out |
| 9. Nothing always-on; nothing of Musical Mycelium's changed | **PASS** | the plan (a bucket, a role, two profiles; none bills by the hour); the before-and-after reads; the dev policy's denies |
