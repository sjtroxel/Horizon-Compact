# Phase 1 — Walking Skeleton (v0.1)

> **Scope doc.** Written 2026-10-04 from `planning/05` §1, §2, §3.1, §4 and §5 (Phase 1's row), `planning/02` §2.1-2.4
> and §2.8-2.12, `planning/04` §3.1 and §6.1, `planning/07` §1, §2, §4, §5 and §11, and `planning/09` A3.
> **APPROVED 2026-10-04 (his)**, with all five decisions at the end taken as recommended.
>
> **Amended 2026-10-04 (his, IMPLEMENTATION doc decision 1):** ECR moves from `main` to `bootstrap` (Delivers 5), so
> the first deploy can push an image before `main` exists, and `main`'s teardown never deletes the images whose
> digests pin the record (`docs/phases/phase-1-walking-skeleton-IMPLEMENTATION.md` §3 finding 2, §18).
>
> **Split 2026-10-04 (his, decision 1):** `planning/05`'s Phase 1 is now two phases. This doc covers the **run path**
> (a sweep from the laptop to results in S3). The **publish path** (the scorer, the page, the teardown test) is
> **Phase 1.5 `publish-path`**, `docs/phases/phase-1.5-publish-path.md`. Both are done before Phase 2 starts. The
> five decisions were made on this doc, before the split, and are recorded here.
>
> Written before Phase 0.5 is built. **Lines marked *(rests on 0.5)* depend on a Phase 0.5 check that has not been
> measured yet;** if that check comes back different, they are the lines to amend.

## What this phase is for

The run half of the walking skeleton, on the real architecture, carrying content that cannot mislead anyone. A
sweep is launched from the laptop, runs as a Fargate task, calls Bedrock through the provider seam, and writes one
provenance-stamped object per run to S3 (`planning/05` §1). Phase 1.5 then scores it and puts it on the public URL.

**Every component on the run path is present and connected, and each does the least interesting version of its
job.** Later phases add content (scenarios, wordings, repeats, models, cases), not structure. If Phase 2 has to add
a component to the run path, this phase missed one.

**The test of a good Phase 1:** a result in S3 can be traced, by its image digest and its run ID, back to the exact
code, the exact input files and the exact raw response that produced it; an interrupted sweep resumes without
re-running or overwriting anything; and no sweep can spend past its cap or be labeled official.

## The main model is a slot, not a fixed name

> **Amended 2026-10-05 (his): the slot is closed. Sonnet 4.6 is the v1 main model, fixed;** Sonnet 5.5 is no
> longer awaited (`KNOWN-GAPS.md`). Model IDs, prices and quotas still live in config, never in code. The
> section as it stood:

This doc says **Sonnet 4.6** because it is the model the account can call today (`planning/02` §2.5). **If Sonnet
5.5 access arrives before `prereg-v1`, choosing the main model reopens as his decision** (`planning/05` §5.2), and
wherever this doc says Sonnet 4.6, it means the main model.

The design already fits Sonnet 5.5's recorded differences (`planning/07` §2.1-2.3; documented for Anthropic's API,
*unverified on Bedrock* until Phase 0.5 calls it): one tool with `auto` choice (5.5 rejects forced tool use);
sampling parameters never set (5.5 rejects non-default values); the US geo inference profile (5.5 has no in-region
endpoint); a placeholder prefix above 1,024 tokens, which clears both models' caching minimums. What would change:
the price (lower, `planning/03` §2.1), the quota (its own, read live), and thinking, which cannot be fully turned off
on 5.5 (`planning/07` §7.3). **Model IDs, inference profiles, prices and quotas live in config and data files, never
in code**, so the switch is a config change plus the checks that go with it.

## What scoping found

1. **A placeholder scenario alone does not keep the skeleton from showing a result.** `planning/05` §2 has the
   skeleton run a placeholder scenario, so that no pre-registered scenario is seen. But the plan as written still
   ran **the real five objectives and the real lever menu, on the official model**, on a placeholder capital
   decision. That shows which way the objectives push, the thing §2 exists to prevent, and Phase 1.5 would put it on
   the public URL before any protocol exists, where a screenshot can be quoted as a finding. Decision 2;
   `planning/05` §1-2 patched 2026-10-04.
2. **The teardown test would have erased the raw results.** `planning/02` §2.10 put the S3 buckets in `main`, and the
   skeleton's done-when includes destroying and re-applying `main`. Raw responses are kept and written once, a
   one-way door (`planning/05` §3.1). Musical Mycelium hit the same problem and kept its record bucket in
   `bootstrap`. Decision 4; `planning/02` §2.10 patched 2026-10-04.
3. **The Vercel rewrite points at the CloudFront domain**, which changes when the distribution is re-created. That
   belongs to Phase 1.5's teardown test and is planned there.

## Delivers

In build order.

1. **The placeholder experiment as versioned data** (decision 2): one scenario, five objectives, a small lever menu
   with caps, one discrete choice, a memo, and a placeholder dossier of at least 1,024 tokens. That is Sonnet 4.6's
   minimum cacheable prefix (`planning/07` §4), so the cache-write and cache-read token fields show up in the cost
   arithmetic on real numbers. Every file is hashed, and every run records the hashes. The files carry a comment
   stating decision 2's rule.
2. **The harness, at minimum size,** on top of Phase 0.5's provider seam:
   - **expansion into runs**, each with a deterministic `run_id` and a seeded menu order (`planning/05` §4.2);
   - **the prompt in `planning/07` §4's fixed structure**, with the cache point after the dossier;
   - **validation** generic over the menu data: non-negative amounts, levers allowed, caps, sources equal to uses
     within 1%, the discrete choice, a memo present (`planning/07` §2.4);
   - **failure classification and retries** as `planning/07` §5 sets them: a fresh, identical request, every attempt
     stored, a refusal never retried, throttling retried with backoff and not counted as a model outcome *(the
     refusal stop reason rests on 0.5)*;
   - **the rate limiter**: one task per model, paced below that model's quota, with backoff on throttling
     (`planning/04` §3.1). The launch command refuses to start a second task for a model that already has one
     running;
   - **the spend cap in two parts** (`planning/09` A3): a preflight estimate that refuses to start above the cap, and
     a running total from each call's token counts that stops the sweep when it reaches the cap. Prices come from a
     data file checked against the AWS Price List, with cache-read and cache-write prices included. The development
     cap is $5;
   - **the official gate, built now and always closed in this phase:** an official sweep is refused unless the
     protocol hash matches a committed protocol. No protocol exists until Phase 3, so in this phase every official
     sweep is refused. The gate is in place before anything could get through it (`planning/05` §3.1);
   - **a sweep manifest:** run counts by status, tokens, and the dollar cost (`planning/02` §2.12).
3. **Per-run, write-once storage:** one S3 object per run attempt under a development prefix, in the raw results
   bucket in `bootstrap` (decision 4). The harness never overwrites, the task role cannot delete, and bucket
   versioning is on. An interrupted sweep resumes by skipping `run_id`s that already have a final result
   (`planning/02` §2.8).
4. **The container:** one ARM image built in CI, with the experiment's input files built into it (decision 5), and
   pushed to ECR with immutable tags. The task definition names the image **by digest**, and the harness records that
   digest on every result. That record is what will make a run eligible to be official later (`planning/02` §2.2). A
   result without a digest is labeled a laptop run.
5. **`main`, the Terraform root:** a minimal VPC with public subnets only and a security group that allows outbound
   traffic and nothing inbound; ~~ECR~~ (*moved to `bootstrap`, amended 2026-10-04*); the ECS cluster and task definition (Fargate, ARM, on-demand); the task role and
   execution role, written by hand one action at a time (`planning/02` §2.11); log groups with retention set. No NAT
   gateway, no endpoints, no load balancer (`planning/02` §2.4). `main`'s state goes in the bucket Phase 0.5 created.
   The task role can invoke only the inference profiles named in config *(which profiles rests on 0.5, decision 3)*.
6. **CI, the image and infrastructure half of deploying:** on `main`, build and push the image, then apply `main`,
   through the deploy role from Phase 0.5, which now gets its permissions. They can create only `horizon-compact-`
   resources, and any IAM role CI creates carries a permissions boundary, so the deploy role cannot grant itself
   more. **CI never launches a sweep** (`planning/02` §2.10).
7. **`hc sweep launch` and `hc sweep status`:** he launches a placeholder sweep from the laptop on the main model
   (decision 3), and its results land in S3.

## The rules this phase must not break

- **Nothing official runs.** Every run in this phase is labeled development and stored under the development prefix.
  The official gate refuses everything.
- **The placeholder stays off the subject** (decision 2), so nothing produced here shows which way the real
  objectives push.
- **Provenance on every call,** from the first container run, with every field in `planning/02` §2.2 that exists by
  then.
- **No account ID and no email address in a tracked file** (carried from Phase 0.5).
- **Nothing always-on.** At rest, this phase leaves buckets, an ECR repository and an idle ECS cluster, none of which
  bills by the hour. Idle cost target: under $1 a month (`planning/03` §6).
- **Musical Mycelium is untouched.** It uses Haiku 4.5 and Nova Pro, which have their own quotas, and this phase
  calls only the main model.

## Explicitly not in this phase

- **The scorer, the static JSON, the site, CloudFront, Vercel and the teardown test.** Phase 1.5.
- **Any real experiment content:** the dossier, the four scenarios, the sentence frame, the wordings, the real lever
  menu. Phase 2.
- **Verdicts, intervals, the bootstrap, the repeat rule, the protocol file.** Phase 3. The official gate exists but
  has nothing to open it.
- **Nova Pro in a sweep.** The launch command takes a list of models, so adding it is a config line. Its first sweep
  is in Phase 4.
- **The development model in the harness,** and an Ollama provider. Phase 2.
- **The thinking sub-study and prompt-caching tuning.** Phase 4.
- **Step Functions, Fargate Spot, more than one task per model.** Out of v1 (`planning/02` §3, `planning/04` §3.6).

## Definition of done

1. **A placeholder sweep launched from the laptop runs as a Fargate task** on the main model, paced under its quota,
   and writes one object per run attempt to S3. Every object carries its provenance, including the image digest and
   the input files' hashes.
2. **The spend cap works both ways:** shown by tests, a preflight estimate above the cap refuses to start, and a
   running total that reaches the cap stops the sweep. The sweep's manifest records its measured cost.
3. **Interrupting a sweep and re-launching it resumes without re-running** any run that has a final result, and
   without overwriting any object. Shown by test, and once for real.
4. **An official sweep is refused**, with a message that says why.
5. **The deploy role can create nothing outside its prefix and cannot widen its own permissions**, shown by its
   policy and by one denied attempt.
6. **`make check` and CI are green,** the root stays under its cap, and every commit passed the guard.
7. **The phase's spend is measured from the bill**, and with Phase 1.5's it is about $1 or less (`planning/05`).

## Prerequisites

- **Phase 0.5 complete:** the state bucket, the deploy role and its proven trust, the budgets, and the provider seam.
  *(rests on 0.5)* The Converse behavior of one `auto` tool call on the main model, and Phase 0.5 decision 3's
  outcome. If decision 3 takes application inference profiles, the task role is granted those profiles and the
  provenance records them.
- **Local tools:** Docker 29.6.2, checked 2026-10-03 (`ROADMAP.md` §3). Versions of the actions, the AWS provider and
  the Python packages are checked live in the IMPLEMENTATION doc.

## Cost

**Well under $1.** The placeholder sweep is a handful of main-model calls with a prefix of about 1,000 tokens: cents
to tens of cents. Fargate on ARM for minutes is cents, and public IPv4 bills only while a task runs. ECR storage is
cents a month with a lifecycle rule. S3 at this size is fractions of a cent. The deploy workflow's Terraform runs cost
nothing in AWS. `planning/05`'s "about $1" covers this phase and Phase 1.5 together.

## Known risks

- **First contact with ECS, Fargate and hand-written IAM** (`planning/05` §7). The first permissions error will take
  an afternoon. That is why the content is a placeholder and the phase is split: the afternoon is spent on the
  plumbing, not on content.
- **A deploy role that can create IAM roles can try to escalate.** Mitigation: the permissions boundary and the
  prefix condition, plus one denied attempt as proof (DoD 5).
- **The image digest is not recorded, or is recorded from the wrong place,** and official runs later have nothing to
  pin them. Mitigation: the task definition names the digest, and a test checks that a result without one is labeled
  a laptop run.
- **Laptop and container runs on the same model at once** would share its quota. Mitigation: backoff, and the launch
  command's refusal while a task for that model is running.
- **The placeholder drifts toward the subject.** A placeholder that slowly gains employees, shareholders or a time
  horizon becomes a look at the result. Mitigation: decision 2's rule is written into the data files.

## Decisions for him

All five taken 2026-10-04 (his), as recommended. Each keeps its original framing under *Was:* as the record.

1. **DECIDED 2026-10-04 (his): (a), split.** This doc is Phase 1; the publish path is Phase 1.5 `publish-path`.
   `planning/05` status line patched. *Was:* **One phase or two.**
   - (a) **Recommended:** split into **Phase 1 `walking-skeleton`** (v0.1: results land in S3) and **Phase 1.5
     `publish-path`** (v0.1.5: the scorer, the page and the teardown test). Both are done before Phase 2 starts, so
     the skeleton still walks end to end before any content goes on it. Phase 1 is first contact with ECS, Fargate
     and IAM; Phase 1.5 is first contact with this project's site. Each deserves an IMPLEMENTATION doc written right
     before it, from what the previous half taught.
   - (b) One phase, as `planning/05` has it.
2. **DECIDED 2026-10-04 (his): (a), off the subject entirely.** `planning/05` §1 and §2 patched. *Was:* **What the
   placeholder is.**
   - (a) **Recommended:** **off the experiment's subject entirely**, in scenario, objectives and menu, with the same
     *shape* as the real thing: five objectives, an allocation with caps that must balance, one discrete choice, a
     memo. The rule, written into the data files: no company, no workers, no shareholders or owners, no contrast of
     who counts, no contrast of time horizon. An example would be a fictional club allocating a yearly budget across
     a few lines under five priorities unrelated to the project's question. It keeps `planning/05` §2's promise
     fully: nothing seen on the official model shows which way the real objectives push, and nothing on the public
     page can be quoted as a finding. It also proves the harness does not depend on the content, which
     `planning/05` §3.2 relies on. What it gives up: the skeleton does not exercise the real menu's wording. Phase
     2's development runs do that, on the development model.
   - (b) A placeholder scenario with the real objectives and menu, as `planning/05` §1 reads literally.
3. **DECIDED 2026-10-04 (his): (a), the main model** (Sonnet 4.6 today; see "The main model is a slot"). *Was:*
   **Which model the skeleton runs on.**
   - (a) **Recommended:** **Sonnet 4.6**, a handful of runs. The skeleton's job is to prove the official path: the
     cross-region profile, its 10-a-minute quota and throttling, its billing line, the cache-token arithmetic. Only
     the official model proves those. With decision 2 (a), what it is shown is harmless.
   - (b) The development model chosen in Phase 0.5. Cheaper by cents, but it leaves the official path unproven until
     Phase 4's pilot.
4. **DECIDED 2026-10-04 (his): (a), in `bootstrap`.** `planning/02` §2.10 patched. *Was:* **Where the raw results
   bucket lives.**
   - (a) **Recommended:** in **`bootstrap`**, beside the state bucket and the budgets, so `main`'s destroy is a real
     off-switch for compute and the site but never deletes the record. Musical Mycelium kept its record bucket in
     `bootstrap` for the same reason. This needs a second dated patch to `planning/02` §2.10.
   - (b) In `main`, as `planning/02` §2.10 had it, and copy results somewhere else before every teardown.
5. **DECIDED 2026-10-04 (his): (a).** `planning/02` §1 and §2.8 patched. *Was:* **Inputs and outputs.**
   - (a) **Recommended:** the experiment's input files are **built into the image**, so the image digest pins the
     code and the content together, and no inputs bucket or read permission is needed. The **published JSON is
     committed to the repo** after he runs the aggregation, so every change to what the site shows is a reviewable
     diff, and CI never needs to read raw results. This changes `planning/02` §1's picture, which shows an inputs
     bucket and aggregation "on the laptop or in CI." That needs a dated patch.
   - (b) An inputs bucket and aggregation in CI, as `planning/02` §1 shows. That needs a read grant on raw results
     for CI, which `planning/02` §2.11 forbids.

## Left for the IMPLEMENTATION doc

The placeholder content, word for word, and its run count. The decision schema as data. The prompt text. The price
file's values, checked live. The task size. Retry and backoff numbers. The S3 key layout and the write-once
mechanism (whether S3's conditional writes are used, checked live). How the task learns its image digest. ARM image
builds on GitHub's runners (checked live). The IAM policies, action by action, and the permissions boundary. Log
retention. Versions of every action and package, checked live. The order of the commits.
