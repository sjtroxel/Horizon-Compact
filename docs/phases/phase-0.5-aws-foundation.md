# Phase 0.5 — AWS Foundation (v0.0.5)

> **Scope doc.** Written 2026-10-04 from the Phase 0 scope doc's "Moved to Phase 0.5" paragraph (decision 6),
> `planning/05` §5 (the AWS half of Phase 0's row), `planning/09` A1 and §5, `planning/04` §3.1, §3.3, §3.5 and
> §6.3, `planning/02` §2.2 and §2.10-2.12, and `planning/07` §2 and §14.1-14.4. **APPROVED 2026-10-04 (his)**, with all
> eight decisions at the end taken as recommended.
>
> **Amended 2026-10-04 (his):** if Sonnet 5.5 access has arrived when this phase is built, it gets the same smoke
> calls (Delivers 4), so the main-model choice can reopen on measured facts (`planning/05` §5.2).
>
> The first of the scope docs for Phases 0.5 through 7, which are written in order before any further
> implementation. This phase's IMPLEMENTATION doc is written immediately before it is built, after the other scope
> docs exist.
>
> **Three read-only pre-checks were run while scoping** (2026-10-04; no AWS call, no model call). Two of them change
> the design. They are in "What scoping already found" below.

## What this phase is for

Make the AWS account safe to build on, and replace the design's assumptions about the models with measured facts,
before Phase 1 puts a container in front of either.

It has two halves:

1. **The guardrails on the account.** A Terraform bootstrap that creates the state bucket and the deploy role and
   **creates nothing shared**, plus budgets that watch this project's own spend.
2. **First contact with the models.** One tool call to each Bedrock model from the laptop, provenance-stamped and
   labeled development, which closes the seven open checks (`KNOWN-GAPS.md`, "Phase 0.5 checks") and gives him what
   he needs to name the development model.

**The one mistake in this phase that cannot be cleanly undone** is touching something Musical Mycelium owns. The
GitHub OIDC provider is one per account and is managed by Musical Mycelium's Terraform. If this project creates it,
the apply fails. If this project ever owns it and is torn down, Musical Mycelium's deploys break (`planning/04`
§3.5). Everything else here can be destroyed and re-applied.

**The test of a good Phase 0.5:** Phase 1 starts with no open question about the account. It knows where state
lives, how CI authenticates, what an alarm covers, and what a Converse tool call returns on each model.

## What scoping already found (pre-checks, 2026-10-04)

1. **Nova Pro's billing line is shared with Musical Mycelium.** Musical Mycelium uses `amazon.nova-pro-v1:0` as its
   eval judge (its `DEFAULT_JUDGE_MODEL_ID`; judge results on file from 2026-08-20 to 2026-09-10), and Haiku 4.5 for
   its agent. `planning/04` §3.3 assumed it spends only on Haiku 4.5, so a budget filtered to Sonnet 4.6 and Nova
   Pro would measure this project alone. That still holds for Sonnet 4.6 as far as the code shows. **It does not
   hold for Nova Pro.** Its judge runs are small (one 30-item run was estimated at about $0.10 in its own
   records), so the error is small, but it is not zero, and it grows if its eval cadence does. Decision 3 settles
   how this project's budgets handle it.
   It also narrows A1: the development model can be neither Haiku 4.5 nor Nova Pro.
   *What this check is not:* it read Musical Mycelium's code, not its bill. The billing check below confirms it.
2. **This repo's OIDC subject claim is the immutable form.** GitHub's API (2026-10-04) returns
   `use_immutable_subject: true` and the prefix `repo:sjtroxel@183318591/Horizon-Compact@1403629566`, because the
   repo was created after GitHub's 2026-07-15 change. Musical Mycelium's first deploy failed on 2026-08-05 because
   its trust policy used the older name-only form. Here, the deploy role uses the prefix exactly as the API
   returns it.
3. **Ollama is installed on the Windows side**, under his Windows user profile, and is not on the WSL path. WSL
   sees 7 GB of RAM. **Whether WSL can reach its server is still unchecked.**

## Delivers

In build order. **Claude writes; he runs everything that authenticates to AWS** (decision 6).

1. **The Terraform bootstrap root, `infra/terraform/bootstrap/`**, with local state, gitignored, the same as
   Musical Mycelium's. It holds:
   - **the state bucket** for Phase 1's `main` root: versioned, encrypted, public access blocked, old versions
     expiring, locked with S3's native lock file (no DynamoDB table);
   - **the shared GitHub OIDC provider, looked up as a data source and never declared as a resource**;
   - **the deploy role**, whose trust is pinned to this repo's `main` branch by the immutable subject claim (its
     permissions are decision 1);
   - **this project's budgets** (where they live is decision 2; how they treat Nova Pro is decision 3).

   Every name starts with `horizon-compact-`, every resource is tagged `Project = horizon-compact`, and the region is
   `us-east-1`.
2. **Terraform in `make check` and CI:** `terraform fmt -check` and `terraform validate` (neither needs credentials),
   so a green local check still predicts a green GitHub check.
3. **The provider seam, at minimum size** (decision 4): `Provider`, `RawDecision` and `Provenance` from
   `planning/05` §4.1, and a Bedrock implementation through the Converse API with exactly one tool and `auto`
   choice (`planning/07` §2.2). It is tested against a stubbed client. Tests and CI never call the network.
4. **The smoke calls, run by him.** Every call uses the same neutral prompt (see "The smoke calls" below):
   - Sonnet 4.6 with thinking off, the official setting (`planning/07` §7.3);
   - Sonnet 4.6 with adaptive thinking, to see how thinking settings are passed and recorded, ahead of the
     thinking sub-study (`planning/07` §14.1);
   - Nova Pro;
   - each Bedrock candidate for the development model;
   - **Sonnet 5.5, if access has arrived by then** (amended 2026-10-04): one call with its default thinking and one
     with `between_tools`. That checks on Bedrock's Converse API what `planning/07` §2.1 records only from Anthropic's
     API, and it is the evidence for reopening the main-model choice before `prereg-v1` (`planning/05` §5.2).

   Every call is provenance-stamped and labeled development, and its record is kept (decision 5).
5. **The Ollama check:** whether WSL can reach the server on the Windows side; if it can, which small model fits in
   6 GB of VRAM, and whether that model calls one tool under `auto` choice reliably enough for format checks.
6. **The seven checks closed**, each with its source and date, as set out in the table below.
7. **His decision on the development model, made from the evidence** (`planning/09` A1; decision 8), and Nova
   Pro's default temperature recorded under the rule already decided (`planning/07` §2.3; decision 7).

## The bootstrap, in more detail

**State.** The bootstrap root keeps its own state locally and gitignored. It exists to create the bucket that holds
`main`'s state, so it cannot keep its state there from the start. Losing the local file costs a few `terraform
import` commands, because the names are stable. Musical Mycelium accepted the same risk and documents moving the
state later; that option stays open here.

**The account ID stays out of the repo.** The state bucket's name contains the account ID, because bucket names
are global. `main`'s backend will take the bucket name at `init` time, not from a tracked file (Musical Mycelium's
partial backend configuration, for the same reason). The account ID is not secret, but a public repo is permanent,
and leaving it out is free.

**The OIDC provider.** It is a data source. The plan read before every apply must show it read, never created.
Its ARN and creation date are read before the apply and after it, and they must match. `planning/04` §3.5 also
asks for a comment in both repos recording the dependency. The comment in this repo is written here. The comment
in Musical Mycelium is a change to that repo, which this project does not make; it is his to add during a Musical
Mycelium session, if he wants it.

**The deploy role.** Its trust allows only `sts:AssumeRoleWithWebIdentity` from the looked-up provider, with
audience `sts.amazonaws.com` and subject exactly `<the prefix>:ref:refs/heads/main`. With that subject, a pull
request, including one from a fork, cannot obtain credentials.

**The budgets.** They measure actual spend with credits excluded (`IncludeCredit: false`, as Musical Mycelium's
already do). They have **no forecast notifications**: on 2026-10-02 a forecast alert projected $9.17 against $0.001
of actual spend (`planning/04` §3.3). Their thresholds are tied to the $80 ceiling, for example $40, $60 and $75,
and $60 is the re-plan point. The notification address is supplied through an untracked variable, never a tracked
file. **Musical Mycelium's three budgets are read before and after the apply, and must be unchanged.**

## The smoke calls, in more detail

**The prompt is neutral and outside the experiment's subject entirely.** It is not one of the four scenarios, not
Phase 1's placeholder scenario, and not about capital allocation. An example would be a tool that records the
answer to a unit conversion. The reason is `planning/05` §2: a smoke call must show nothing about how any objective
pushes a decision. A call that tests the plumbing has no reason to be about the subject.

**What each call proves:** the request shape that Converse accepts for one tool under `auto` choice on that model;
whether the model called the tool, called it once, and passed arguments matching the schema; the stop reason; the
token usage fields returned; and, for the thinking call, where the thinking setting goes in the request and how it
shows in the response. Every one of these is recorded, including failures. **If Nova Pro answers in text instead of
calling the tool, that is a finding**, and it may move Nova Pro down the cut list (`planning/05` §7). It is not
something to retry until it passes.

**Provenance** follows `planning/02` §2.2, limited to the fields that exist before there is a sweep: no `sweep_id`,
no `image_digest`, `provider` and `model_id` and `inference_profile` and `region`, the effort and temperature as
sent (or "not set"), the prompt's hash, `started_at`, the token counts, the raw response, the tool input, and a
development label. If an inference profile's ARN contains the account ID, the account ID is removed before anything
is stored in the repo.

**Bounded by count, not by a dollar cap.** The running dollar cap is Phase 1's (`planning/09` A3). The smoke command
makes a fixed, small number of calls and refuses to make more, and the IMPLEMENTATION doc states the number.

## The checks, and how each closes

| Check | How it closes | Who |
|---|---|---|
| Ollama's install location and whether WSL can reach it | Located 2026-10-04 (Windows side). Reachability: one request from WSL to the Windows server | him runs, Claude reads |
| Whether Budgets can filter on this project's per-model billing lines; whether added budgets cost money; whether application inference profiles could tag spend | AWS documentation, live; then the plan and apply | Claude reads, him applies |
| Which Bedrock billing lines Musical Mycelium spends on (`planning/09` A1) | Its code, read 2026-10-04 (Haiku 4.5, Nova Pro); then its bill, grouped by usage type, in the Cost Explorer console (the API charges per request) | him |
| Converse: one tool with `auto` choice on Sonnet 4.6; how thinking settings are passed and recorded | The two Sonnet 4.6 smoke calls | him runs, Claude reads |
| Nova Pro: default temperature, availability, knowledge cutoff | AWS model card, live; the Nova Pro smoke call | Claude, him |
| Claude's default temperature, for the methods page | Anthropic's documentation, live | Claude |
| How a refusal comes back through Converse on Sonnet 4.6 | **Documentation only, on purpose:** Converse's stop-reason values and Anthropic's refusal documentation. A refusal is not provoked. Provoking one would mean writing a prompt designed to be refused, and the harness already records any unexpected stop reason as a failure rather than dropping it (`planning/07` §5). Recorded as "documented, not observed" | Claude |

Each check closes in `KNOWN-GAPS.md` with its source and date, or is carried forward with a stated reason. Where a
result changes a planning doc (`planning/07` §2.3 and §14, `planning/04` §3.3, `planning/02` §2.10), that doc gets a
dated patch noted in its status line.

## Explicitly not in this phase

- **The `main` root and everything in it:** VPC, ECR, the ECS cluster and task definition, the results bucket,
  CloudFront, log groups. Phase 1.
- **The deploy workflow**, apart from the single identity check in decision 1. Phase 1.
- **The rate limiter, per-run storage and the running spend cap** (`planning/09` A3). Phase 1.
- **Prompt caching.** Phase 1 onward.
- **Any experiment content**, including the placeholder scenario. Phases 1 and 2.
- **An Ollama provider in the harness.** Phase 2, and only if Ollama is chosen.
- **Sonnet 5.5.** Still waiting on AWS (`KNOWN-GAPS.md`).
- **Any change to Musical Mycelium:** its budgets, Terraform, OIDC provider or code. Reading it is allowed.

## Definition of done

1. **The bootstrap is applied and creates nothing shared.** The plan read before the apply shows the OIDC provider
   read, not created, and nothing named outside `horizon-compact-`. A second plan after the apply shows no changes.
   The provider's ARN and creation date match before and after.
2. **The deploy role trusts this repo's `main` only**, by the immutable subject claim. One manual workflow run on
   `main` assumes it and prints its identity, and the role has no permission policy (decision 1).
3. **This project's budgets exist** on actual spend, credits excluded, filtered as decision 3 settles, with no
   forecast notifications. Alternatively, the reason a filter cannot work is recorded and the fallback is stated.
   **Musical Mycelium's three budgets are unchanged**, read before and after.
4. **There is a recorded, provenance-stamped, development-labeled tool call** from Sonnet 4.6 with thinking off,
   from Sonnet 4.6 with thinking on, and from Nova Pro (and from Sonnet 5.5, if access arrived; amended 2026-10-04).
   Each shows the tool called once under `auto` choice, or the
   failure recorded as found.
5. **All seven checks are closed in `KNOWN-GAPS.md`** with their sources and dates, or carried forward with a reason.
   Every planning doc that a result changes has its dated patch.
6. **The development model is named** (his) **and Nova Pro's default temperature is recorded** with its source.
7. **`make check` and CI are green**, including the Terraform checks. No account ID and no email address is in any
   tracked file. Every commit passed the guard.
8. **The phase's spend is measured, not estimated:** read from the bill by usage type, credits excluded, a day after
   the last call. It is under $1.
9. **Nothing always-on was created, and nothing of Musical Mycelium's was changed.**

## Prerequisites

- **Phase 0 complete** (2026-10-03).
- **Local tools:** Terraform 1.15.8 and AWS CLI 2.36.14, checked 2026-10-03 (`ROADMAP.md` §3). The AWS provider's
  version is checked live in the IMPLEMENTATION doc.
- **His AWS credentials on the laptop.** Which profile, and whether this project gets its own, is settled in the
  IMPLEMENTATION doc.
- **Model access:** Sonnet 4.6 and Nova Pro worked on 2026-10-02 (`planning/02` §2.5). Access for each
  development-model candidate is checked before its call.

## Cost

**Under $1** (`planning/05`, the AWS half of Phase 0). The smoke calls are a few dozen at most, which is cents at
Sonnet 4.6's price (`planning/03` §2.1). The state bucket costs fractions of a cent. IAM roles and data sources are
free. **Whether added budgets cost money is unverified**, and is checked before any are added. Application
inference profiles, if decision 3 uses them, are checked for cost the same way.

## Known risks

- **Touching a shared resource by accident:** the OIDC provider, a budget, a tag. Mitigation: the data source, the
  prefix, a plan read before every apply, and before-and-after reads of Musical Mycelium's resources.
- **A trust policy in the wrong form fails closed with no explanation**, as Musical Mycelium's did on 2026-08-05.
  Mitigation: use the API's prefix verbatim, and the identity check in decision 1.
- **Budgets cannot filter on Marketplace lines.** Then the fallback in `planning/04` §3.3 applies: Musical
  Mycelium's account-wide net plus the harness caps, with the per-sweep record as the authoritative number.
- **A smoke call counted as a look at the result.** Mitigation: the prompt is outside the experiment's subject.
- **Losing the local bootstrap state.** A few imports; accepted, as in Musical Mycelium.
- **First contact with Converse may surprise**, for example a model that answers in text, or usage fields that
  differ by model. Every surprise is recorded. A surprise is a reason for this phase to be small, not a reason to
  widen it.

## Decisions for him

All eight taken 2026-10-04 (his), as recommended. Six are decided outright; 3 is an agreed procedure whose
outcome waits for its check; 8 is decided at the end of the phase by design. Each keeps its original framing under
*Was:* as the record.

1. **DECIDED 2026-10-04 (his): (a).** The role is created with no permission policy, and its trust is proven by one
   manual workflow run on `main`. *Was:*
   **The deploy role's scope in this phase.**
   - (a) **Recommended:** create the role now with **no permission policy**, and prove its trust with one manual
     workflow run on `main` that assumes it and prints its identity (no permission is needed for that). The
     lookup of the shared provider only means something once a role uses it, and the trust policy is the part
     Musical Mycelium got wrong the first time. Proving it with zero permissions costs nothing and risks nothing.
     Phase 1 attaches permissions once the resources exist. The cost is one small workflow added now.
   - (b) Create the role without the proof; Phase 1's first deploy tests it.
   - (c) Leave the role to Phase 1 entirely; this phase only looks the provider up.
2. **DECIDED 2026-10-04 (his): (a), in the bootstrap root.** `planning/02` §2.10 patched the same day. *Was:*
   **Where the budgets live.**
   - (a) **Recommended:** in the bootstrap root. They must exist before the first model call, and they must survive
     Phase 1's teardown test of `main` (`planning/05` Phase 1: destroy and re-apply). In `main`, they would vanish at
     exactly the moment the project tests turning things off. This needs a dated patch to `planning/02` §2.10, which
     lists the budget alarm under `main`.
   - (b) In `main`, as `planning/02` §2.10 says, which means no budgets until Phase 1.
3. **AGREED 2026-10-04 (his), as a procedure:** check (c) in this phase, take it if all three conditions hold,
   otherwise (a). The choice itself is his once the check is in. *Was:*
   **Nova Pro's shared billing line** (pre-check 1).
   - (a) A budget on the Sonnet 4.6 line only. Nova Pro is covered by the harness caps and by Musical Mycelium's
     account-wide budgets. Simple; Sonnet 4.6 is the larger of the two official models' lines (`planning/03` §4).
   - (b) Budgets on both lines, accepting that the Nova Pro figure includes Musical Mycelium's judge spend, and
     saying so in the budget's description.
   - (c) Send this project's calls through **application inference profiles** tagged `Project = horizon-compact`,
     and filter the budgets by that tag. This works only if the checks show that both models support them, that
     Budgets can filter by the tag on both billing lines, and that they cost nothing. It gives the cleanest
     attribution. It also changes the `inference_profile` recorded on every call, so it must be settled before
     `prereg-v1`, and this phase comes before it.
   - **Recommended:** check (c) in this phase and take it if all three conditions hold; otherwise (a). He decides
     once the check is in.
4. **DECIDED 2026-10-04 (his): the real provider seam.** *Was:*
   **The smoke calls go through the real provider seam** (recommended) **or a throwaway script.** Provenance on
   every call is a one-way door (`planning/05` §3.1), and a seam built now is thickened by Phase 1 rather than
   replaced. The cost is a little more code now, with its tests.
5. **DECIDED 2026-10-04 (his): committed**, in an evidence folder under `docs/phases/`, account ID removed. *Was:*
   **The smoke records are committed** (recommended: in an evidence folder under `docs/phases/`, account ID
   removed; public evidence that the checks ran, on a prompt that reveals nothing) **or kept local only.**
6. **DECIDED 2026-10-04 (his): (a).** He runs every command that authenticates to AWS; `.claude/settings.json` stays
   as it is. *Was:*
   **Who touches the account.**
   - (a) **Recommended:** he runs every command that authenticates to AWS, one at a time, with Claude saying what
     to look for. Claude runs `terraform fmt` and `validate` and the stubbed tests. This matches
     `.claude/settings.json`, which denies Claude `aws` and `terraform apply` and `destroy`. `terraform plan` is not
     denied, but it authenticates, so under (a) Claude does not run it either.
   - (b) Allow Claude a short allowlist of read-only `aws` commands (describing budgets, the OIDC provider and the
     quotas). Faster, but it widens what Claude can reach on a shared account.
7. **DECIDED 2026-10-04 (his): (a), Nova Pro at its own default.** `planning/07` §2.3 patched the same day. The
   default's value is still recorded in this phase, for the methods page. *Was:*
   **Nova Pro's temperature** (`planning/07` §2.3; can be decided now).
   - (a) **Recommended:** its own default, the same rule as for Claude, so that each model runs at its default. The
     same number does not mean the same thing on two different models, so matching it does not match their
     behavior. It does add a difference between the models that the methods page has to state.
   - (b) Set to Claude's default value. It looks like a match, but it is a setting Nova Pro would not otherwise
     run at.
8. **AGREED 2026-10-04 (his): decided at the end of this phase, by the criteria below.** *Was:*
   **The development model** (`planning/09` A1), decided at the end of this phase from the evidence. The criteria:
   not an official model (Sonnet 4.6, Nova Pro); not on Musical Mycelium's lines (Haiku 4.5, Nova Pro); calls one
   tool under `auto` choice reliably on the neutral prompt; cheap; and available through Phase 2. The candidates are
   a small local model through Ollama, if WSL can reach it and one fits in 6 GB, and a cheaper Bedrock model,
   priced live. It could be both: Ollama for volume, and a Bedrock model to show format failures closer to the
   official ones.

## Left for the IMPLEMENTATION doc

The AWS provider version, checked live. The budgets' exact amounts and time unit (monthly, or a custom period, since
the ceiling is cumulative). The neutral prompt and the tool schema, word for word. The provenance fields as built.
The smoke command's call limit. The credentials and profile. The identity-check workflow (decision 1).
The `make` targets. Additions to `.claude/settings.json`. The evidence folder's path. The order of the commits,
with the exact files in each.
