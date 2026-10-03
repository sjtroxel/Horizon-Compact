# Phase 0 — Scaffold and Guardrails (v0.0)

> **Scope doc.** Written 2026-10-03, before any code, from `planning/05` §5 (Phase 0's row), `planning/09` §4-5
> and §7, and `planning/04` §2.6. **APPROVED 2026-10-03 (his).** The IMPLEMENTATION doc is approved before
> step 1 is built. All six decisions at the end were made 2026-10-03.
>
> **Split 2026-10-03 (his, decision 6):** `planning/05`'s Phase 0 is now two phases. This doc covers the local
> half (repo, guardrails, toolchain, CI; $0). The AWS half (Terraform bootstrap, budgets, smoke calls, the
> development model, the Ollama check) is **Phase 0.5 `aws-foundation`**, with its own scope and IMPLEMENTATION
> docs. Its scope doc is written after Phase 0 is built, first of the remaining scope docs (0.5 through 7), which
> are all written before any further implementation.
>
> **This is the one phase built before the full set of scope docs exists** (his exception, 2026-10-03), so the
> name guard is in place as early as possible.

## What this phase is for

A repo that can be built in without stopping to retrofit guardrails, with the one irreversible mistake made
mechanically hard before anything more is committed.

**The irreversible mistake** is a real company's name in a public commit (`planning/04` §2.6). A name pushed
to a public repo can be found in its history even after removal, and anyone who saw it can keep it. Everything
else in this phase is ordinary setup, and can be redone.

**The test of a good Phase 0 is negative:** after it, no later phase pauses to add a lint config, CI, a dev
runner, a guardrail, or a doc convention.

## Delivers

In build order. Nothing here touches AWS or spends money.

1. **The name guard** (`planning/09` A2, P25): a local check that refuses a commit, or a push, containing a
   name from a private term list; the CI check that fails if any path under `methods-appendix/` is tracked; and
   tests that prove both with a made-up canary name, plus a mode that scans **every commit already in the
   history**.
2. **The guard commit** (his): the name guard and its tests, the pre-commit config, the CI workflow, and the
   minimum Python toolchain needed to run the tests. Nothing else. *(Amended 2026-10-03: this was "the first
   commit," with `.gitignore` in it. `f214280`, holding `.gitignore` and `docs/planning/`, was committed and
   pushed first; `KNOWN-GAPS.md`, 2026-10-03.)*
3. **The history scan, then the docs commit** (his): the installed guard scans every commit already pushed,
   `f214280` included, against the real term list, and the result is recorded. Then `docs/ROADMAP.md`,
   `docs/KNOWN-GAPS.md` and `docs/phases/` are committed through the guard.
4. **`CLAUDE.md`** from `planning/00` §10's working rules, plus: planning is closed; patches are dated in the
   doc's status line; nothing official runs before `prereg-v1`; no real company name in any tracked file, any
   commit message or any GitHub text. **`docs/planning/README.md`** with the read order and **his** one-line
   disclosure.
5. **The toolchain and dev runner:** `pyproject.toml` as the only tool config (ruff, mypy, pytest), `uv.lock`
   committed, a `Makefile` whose `make check` is what CI runs, `make setup` that installs the hooks. The package
   skeleton `src/horizon_compact/` with docstrings and no logic. The repo-root cap, enforced in CI. **`make
   check` runs exactly what CI runs**, except the one check CI skips by name (decision 5), so a green local
   check predicts a green GitHub check.

**Moved to Phase 0.5 `aws-foundation`** (decision 6), recorded here so nothing is lost: the Terraform bootstrap
(state bucket and lock, a deploy role trusting only this repo's `main`, the shared OIDC provider looked up as a
data source and never created, `planning/04` §3.5); this project's budgets filtered to its model billing lines,
or the recorded reason they cannot be (`planning/04` §3.3); one `auto`-choice tool call to Sonnet 4.6 and to
Nova Pro on a neutral prompt that is never one of the four scenarios, provenance-stamped and labeled
development, closing the Converse checks in `planning/09` §5; the development model named (`planning/09` A1)
after checking Musical Mycelium's billing lines; Ollama's reachability from WSL (`planning/04` §6.3).

**And from him, in parallel:** claiming `horizon-compact.vercel.app` as a placeholder. (The public
`Horizon-Compact` repo exists as of 2026-10-03.)

## The name guard, in more detail

Because it is the one part of this phase that cannot be fixed afterwards, its requirements are written here
rather than left to the IMPLEMENTATION doc.

**What it reads.** A private term list that lives outside this repo, next to the longlist, in the private
job-search-headquarters repo. Its location reaches the guard through local configuration that git never
tracks (see decision 2). **The path is never written into a tracked file**, including this doc's successors,
`CLAUDE.md`, the Makefile and the hook config.

**What it scans,** each with the staged or pushed content, not the working tree:
- the **content** of every added or modified file;
- every **path** being added or renamed (a file name can carry a name too);
- the **commit message**;
- at **push**, every commit being pushed, which catches a commit made with `--no-verify` and anything the
  commit-time scan missed.

It also refuses any staged path under `methods-appendix/` by itself, so the local check and the CI check
overlap.

**How it fails.** **Closed.** If the configuration is missing, the term file cannot be read, it holds no terms,
or the longlist has changed since the term file was written (decision 1), the commit is refused with a message that says which. A guard
that passes silently when its list is missing is worse than no guard, because it looks like protection. The
message names the file and line that matched, and **never prints the matched term in CI output**; locally it
may show it, since the terminal is private.

**What CI does.** CI cannot read the private list (`planning/08` §4.8), so CI **does not run the name scan**. It
runs (a) the tracked-path check, (b) the guard's own tests, which use made-up canary names only, and
(c) `make check`. The CI configuration skips the name hook by name, explicitly, so the skip is visible.

**How it is proven.** Automated tests, with fictional names only, that show: a canary in content, in a path,
and in a commit message is refused; the same text without the canary passes; an allowed phrase passes; each
fail-closed condition refuses; the push-time scan catches a canary committed with `--no-verify`. Then once, by
hand, before the guard commit: the installed hook refuses a real staged file containing the canary. **No real
name is ever used in a test.** (`planning/04` §2.6.)

**What it cannot catch,** stated so nobody relies on it for these: text typed into GitHub itself (issue and
pull-request text, the repo description, release notes); a name spelled in a way the term list does not
contain; a description detailed enough to identify a company without naming it (`planning/04` §2.5, handled in
Phase 5 and 6). `CLAUDE.md` carries the human rule for these.

## Explicitly not in this phase

- **Anything that touches the AWS account**, including Terraform and any model call. Phase 0.5.
- **Any Fargate task, ECR repository, Docker image, S3 results bucket, CloudFront distribution or site.**
  Phase 1.
- **Any experiment content**: scenarios, objectives, wordings, the dossier. Phase 2.
- **Any change to the Musical Mycelium repo.**

## Definition of done

1. **The name guard refuses** a canary in staged content, a staged path and a commit message, and at push;
   **passes** clean content and allowed phrases; **fails closed** on each missing-list condition. Shown by
   automated tests, and once by hand against the installed hook before the guard commit.
2. **The guard's history scan passes over every commit already pushed** (`f214280` and anything after it) with
   the real term list, and the docs commit passes the guard. No term was removed from the list to make either
   pass. Any allowed phrase added for them is recorded in the private list with its reason. **If the history scan
   finds a case reference, the phase stops** and the response is his decision, made before anything else is
   pushed.
3. **CI is green on the first push**, and the CI tracked-path check is shown to fail on a tracked
   `methods-appendix/` path. *Shown how:* by the check's own test and by running CI's exact command against a
   throwaway local repo, **not** by pushing such a path to the public repo.
4. **`make check` passes locally**, the root is under its cap, and `make setup` installs every hook type.
5. **`CLAUDE.md` and `docs/planning/README.md` exist**; the README's disclosure line is his.
6. **Nothing in the AWS account was created, changed or called** by this phase.

## Prerequisites

- **Local tools:** checked 2026-10-03 (`ROADMAP.md` §3). `pre-commit` arrives as a development dependency.
- **His:** nothing before the guard commit. The GitHub repo and its remote exist.

## Cost

**$0.** No AWS resource, no model call. (`planning/05`'s "under $1" for Phase 0 now belongs to Phase 0.5.)

## Known risks

- **False positives push toward `--no-verify`.** A guard that blocks ordinary prose gets bypassed. That is why
  the matching rule (decision 3) is precise and why the push-time scan exists as a backstop.
- **The term list goes stale.** The longlist will grow in Phase 5. Decision 1's freshness check exists for this.
- **A fresh clone has no hooks.** Hooks are not cloned. `make setup` installs them, `CLAUDE.md` says so, and
  `make check` fails if they are not installed (decision 5).

## Decisions for him

All six decided 2026-10-03. Each keeps its original framing under *Was:* as the record.

1. **DECIDED 2026-10-03 (his): (b), with a content fingerprint instead of a date.** The term file records a
   hash of the longlist's contents; the guard refuses to run if the longlist's current hash differs, so only a
   real edit trips it. Claude drafts and maintains the term file; he reviews it. He preferred (a) as less work
   and chose (b) because (a)'s failure is silent. *Was:*
   **Where the guard gets its terms.** The longlist is written for a person, not a parser (`KNOWN-GAPS.md`,
   2026-10-03): names sit in table cells, comma lists and sentences, with tickers and plant locations beside
   them.
   - (a) Parse the longlist directly. No second file, but any prose the parser misreads is a **silent** miss.
   - (b) **Recommended:** a separate private **term file** beside the longlist, one term per line, written from
     the longlist by hand (Claude drafts it, he checks it). The guard **refuses to run if the longlist has
     changed since the term file was last updated**, so a new candidate cannot be added to the longlist without
     the term file being revisited. The cost is one more private file to maintain.
2. **DECIDED 2026-10-03 (his): (b)**, the path in this repo's local git config, an environment variable allowed
   to override it, `make setup` prompting for it once. *Was:*
   **How the guard finds the private file.**
   - (a) An environment variable. Easy, but it has to be set in every shell, and it is easy to forget.
   - (b) **Recommended:** a value in this repo's local git config (`.git/config`), with an environment variable
     allowed to override it. Git never tracks its own config, so the path cannot be committed by mistake, and
     it survives across shells. `make setup` prompts for it once.
   - (c) A gitignored file in the repo. Works, but adds a root file and relies on an ignore rule, which is the
     mechanism `planning/04` §2.6 says can fail.
3. **DECIDED 2026-10-03 (his): the three-part rule below, as recommended.** Possessives ("Name's") match;
   plurals and longer words do not. *Was:*
   **The matching rule.**
   - **Recommended:** whole-word matching, **case-sensitive by default** (company names are proper nouns, and
     several longlist names are also ordinary English words); a per-term flag for case-insensitive matching
     where a name is unusual enough to be safe; and **allowed phrases**, kept in the same private file, that
     are removed before matching. Allowed phrases are needed: one longlist term already appears 9 times in the
     planning docs, each time inside a product name the project uses, never as a case.
4. **DECIDED 2026-10-03 (his): all four groups as recommended.** Company names including rejected and excluded
   candidates; tickers of three or more letters; each shorter ticker only if it matches nothing in the repo
   (checked when the term file is drafted, any match brought to him); plant and site locations. Out on purpose:
   industry codes, the cited research sources, and the unnamed descriptions. *Was:*
   **What counts as a term.**
   - **Recommended:** every company name on the longlist, **including rejected and excluded candidates**
     (blocking them is cheap; a rejected candidate can come back); every ticker of three or more letters,
     case-sensitive; shorter tickers only if they match nothing in the repo; and **the plant and site locations
     named for candidates**, because for a single-plant closure the town identifies the company as surely as
     the name does. Locations are the part most likely to be needed in the public dossier's coarse description,
     so if one is ever needed, it is moved to the allowed phrases on purpose, with a reason.
5. **DECIDED 2026-10-03 (his): as recommended.** `make check` fails locally if the hooks or the term-file path
   are missing; CI skips that one check by name. His reason: catch failures before they reach GitHub, never
   after. *Was:* **Hooks not installed.** **Recommended:** `make check` fails if the hooks are not installed, so a fresh clone
   cannot quietly commit without them.
6. **DECIDED 2026-10-03 (his): split into Phase 0 (local) and Phase 0.5 `aws-foundation`.** Claude first
   recommended one phase with a stop; he preferred half-phases for pacing, and on reflection the split is
   better on the merits too: the AWS half's IMPLEMENTATION doc should be written immediately before its build,
   after Phase 0 lands, because its four open checks (Budgets filtering, Converse behavior, Ollama, the
   development model) can change it. *Was:* **Phase 0 in one phase or two.** `planning/05` puts the
   guardrails and the AWS checks in one phase. One phase with a stop, or two phases.

## Left for the IMPLEMENTATION doc

The term file's exact format; the guard's language and where it lives (the recommendation will be a
standard-library Python script outside the package, so it runs before the toolchain exists); the hook framework
configuration for the commit, message and push stages; the fictional canary names; the exact CI workflow and
pinned action versions, each checked against the live registry; the root cap's number; the order of commits,
with the exact files in each.
