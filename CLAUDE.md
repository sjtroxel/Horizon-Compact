# CLAUDE.md — Horizon Compact

Operating manual for AI coding agents in this repo. Read this first. **Then read `docs/KNOWN-GAPS.md`'s START
HERE block**, which says where the build is and what is next; it narrows every older doc. The version spine and
decision history are in `docs/ROADMAP.md`. The design is `docs/planning/00`-`09`, which is **closed**: do not
add numbered planning docs.

## What this is

An experiment, not a product. The same model is given five corporate objectives (shareholder value over four
quarters or over twenty years, all stakeholders over four quarters or over twenty years, and a baseline with no
stated objective) and asked to make the same capital-allocation decision on a cited fictional company, then on
anonymized real cases. The question is whether the objectives produce different decisions, and in particular
whether the long-horizon versions converge, as the Business Roundtable's 2019 statement claims. Python on AWS
(Bedrock, Fargate, S3), Terraform for everything, a static explorer at `horizon-compact.vercel.app`.

**The project tests a claim; it does not argue for one.** A result in the Roundtable's favor is as publishable
as one against it (`docs/planning/06` §1). Push back when the work starts arguing a conclusion.

## Rule zero: no real company name in this repository, ever

The repo is public. Real-case candidates are listed in a **private** longlist that lives outside this repo and
is never copied in. **A company name in a public commit cannot be taken back** (`docs/planning/04` §2.6).

- **Never write a real company's name, ticker, brand or plant location** into any tracked file, commit message,
  branch name, tag name or tag message, or into anything typed into GitHub (issues, pull requests, the repo
  description, releases). Refer to a real case by its type and a neutral label.
- **Never write the path of any private file** into a tracked file. The name guard finds its term file through
  local git config (`hc.nameGuardTerms`) or the `HC_NAME_GUARD_TERMS` environment variable.
- **The name guard** (`src/horizon_compact/privacy/`) runs on every commit, every commit message and every push,
  and fails closed. **Never bypass it** (`--no-verify`, `SKIP=`). **Never remove a term** to make a commit pass:
  reword, or, for a true false positive, he adds an `allow:` line with its reason to the private term file.
- **`methods-appendix/` is never tracked.** `.gitignore` excludes it; the guard refuses it locally; CI's
  `paths-check` fails on it.
- **What the guard cannot catch:** text typed into GitHub; a spelling the term file lacks; a description
  detailed enough to identify a company without naming it; binary files. Those are on you, every time.
- **A fresh clone has no hooks.** Run `make setup` first; `make check` fails until it has been run.

## The order of operations (the experiment's one-way door)

**Nobody sees an official model's decisions on a pre-registered scenario before the protocol is committed and
tagged `prereg-v1`** (`docs/planning/05` §2). A result seen early cannot be unseen.

- The walking skeleton runs a **placeholder** scenario, never one of the four.
- Development runs on other models are allowed. After one, a wording or scenario may change **only** to fix a
  format, clarity or neutrality failure, and every change is logged with its reason.
- The pilot comes **after** the pre-registration and is excluded from results.
- The harness refuses an official sweep whose protocol hash does not match the committed protocol.

## The other one-way doors (`docs/planning/05` §3.1)

Provenance on every model call. Raw responses kept, write-once, one object per run. Official and development
results kept apart (official = container run, by image digest). One way to capture a decision for every model
(one tool, `auto` choice). Experiment content as versioned, hashed data. The public/private boundary above.
Terraform for everything, with the shared GitHub OIDC provider **looked up, never created**. The v1 model set
fixed before real cases are accepted.

## How the work is done

- **Two doc layers per phase.** Scope docs for every phase, written up front, one at a time, before
  implementation (Phase 0 was the one exception, built first so the guard existed). Each phase's
  **IMPLEMENTATION doc is written and approved immediately before that phase is built**, then updated with
  `[done]` markers and as-built results. A later finding amends a scope doc with a dated note.
- **Planning is closed.** A design change is a **dated patch** to the planning doc it belongs in, noted in that
  doc's status line, or it is phase work.
- **`docs/KNOWN-GAPS.md` is newest-first and governs** when it and an older doc disagree.
- **`make check` before every commit.** It runs exactly what CI runs (format, lint, strict types, tests, root
  cap, paths-check), plus `doctor` locally. A green `make check` should mean a green check on GitHub; he hates
  red checks, so keep it that way.
- **Never run `git commit` or `git push`.** Provide the command; he runs it (`.claude/settings.json` denies
  both). Short one-line messages (`phase N: ...`), **no AI attribution, no `Co-Authored-By`**.
- **Give him one terminal command at a time**, and say exactly what output to look for.
- **Verify against the repo, not memory.** A grep miss is not proof of absence.
- **Verify time-sensitive facts live**: prices, model availability, cutoffs, action and package versions.
- **No new emoji** in code, docs or commit messages.

## Working rules (`docs/planning/00` §10)

- **Public prose is his.** README, launch post, taglines and the repo description are written by him. Claude
  interviews, outlines and critiques line by line, and does not hand over finished public prose unless he asks
  on that pass. When handing over any prose bound for something a reader would take as his, say so in one line.
- **Flag vocabulary.** Any word that reads as charged to a business audience gets flagged with a neutral
  equivalent; any business term whose technical meaning differs from its plain one gets explained.
  `docs/planning/06` §2 holds the list ("ESG" and "stakeholder capitalism" are never used).
- **Model choice:** Opus for scoping, design review and stuck debugging; Sonnet for routine implementation,
  especially when usage limits are tight. Remind him occasionally.

## Cost and safety

- **v1 ceiling $80, re-plan point at $60** of cumulative project spend. **Sweep caps: $5 development, $25
  official** (`docs/planning/09` §6.2). The harness enforces caps before and during a sweep.
- **No Haiku 4.5 for development**: its spend would land on Musical Mycelium's billing line.
- **Musical Mycelium shares the AWS account.** Its budgets, its Terraform and its OIDC provider are not changed
  from here. Every resource here is prefixed `horizon-compact-`.
- **No always-on resources**: no NAT gateway, load balancer, database or interface endpoints. CloudWatch log
  retention set explicitly. CI never launches a sweep.

## Layout

```
src/horizon_compact/privacy/   the name guard (standard library only)
tests/                         pytest; every name in a test is a fictional canary
docs/planning/                 the closed design, 00-09
docs/phases/                   scope and IMPLEMENTATION docs per phase
docs/ROADMAP.md                spine, ledger, decision history
docs/KNOWN-GAPS.md             open items, START HERE
```

Later phases add `infra/`, `experiment/`, `web/` and `pipelines/` (`docs/planning/02` §4). The root is capped
at 16 entries (`make root-check`); relocate before raising it.

This repo shares one Claude memory store with `job-search-headquarters` through a symlink.
