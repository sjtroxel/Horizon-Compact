# ROADMAP — Horizon Compact

This file has the version spine, the scaffolding ledger and the decision history. The design itself lives in
`docs/planning/` (`00` through `09`), which stays the authority for every design decision. This file says where
the build is against that design. Open items live in `docs/KNOWN-GAPS.md`, not here.

**Started 2026-10-03.** Planning closed the same day (`planning/09` §1). From here, a design change is either a
dated patch to the planning doc it belongs in (noted in that doc's status line) or a phase doc.

## 1. The priority stack

Stated once, from `planning/09` §2, because it settles arguments when two pieces of work compete for a session:

1. **The credibility of the measurement.** Above all: nobody sees an official result before the protocol is
   committed (`planning/05` §2). A late infrastructure mistake costs a week; an early look costs the result.
2. **A working skeleton on the real path.** One placeholder scenario, end to end, on the public URL. Every later
   phase thickens it.
3. **The full experiment, then the explorer's polish.**

Under pressure, priority 3 gives first, by the cut list in `planning/05` §5.1. Priority 1 never gives. These are
not on any cut list: the pre-registration, the baseline objective (E), the published results against the thesis,
three real cases including an invest or retool case, and provenance.

## 2. The version spine

From `planning/05` §5. The "Done when" column is a summary; the phase's scope doc holds the definition of done
that counts. Costs are `planning/03` estimates until Phase 4 measures them.

| Phase | Version | Delivers | Done when (summary) | Est. cost | Status |
|---|---|---|---|---|---|
| **0** `scaffold-and-guardrails` | v0.0 | Repo, the name guard (commit, message and push scans, history scan), the CI path check, toolchain, `make check`, CI, `CLAUDE.md`, the planning README | A canary name refused by the guard; the history scan clean; a tracked file under `methods-appendix/` fails the CI check; CI green | $0 | **COMPLETE 2026-10-03**, CI run `37160410815` green on first push |
| **0.5** `aws-foundation` | v0.0.5 | Terraform bootstrap (OIDC looked up), filtered budgets, one tool call per Bedrock model, Ollama check, the development model named, the AWS checks in `planning/09` §5 | A recorded, provenance-stamped call from each Bedrock model; bootstrap applied with nothing shared created | under $1 | not started |
| **1** `walking-skeleton` | v0.1 | The whole path on a **placeholder scenario**: Fargate, rate limiter, Bedrock, S3, scorer, one page live at `horizon-compact.vercel.app` | Container-run results on the public URL, each traceable to its image digest; destroy and re-apply tested | about $1 | not started |
| **2** `experiment-content` | v0.2 | The cited fictional dossier, the four scenarios, the sentence frame and three wording templates, the supplier source, lever caps, the neutrality review; development runs for format and clarity only, every change logged | Every dossier number sourced or marked as an assumption; every scenario passes the neutrality checklist; development runs parse under all five objectives | about $5-10 | not started |
| **3** `preregistration-and-scoring` | v0.3 | The protocol tagged `prereg-v1`; scoring tested on synthetic data only, including the verdict-rule simulation and the matcher calibration | Tag exists; the harness refuses an official sweep whose protocol hash does not match it; simulation results recorded in the protocol | $0 | not started |
| **4** `official-grid` | v0.4 | Pilot (excluded), then the full grid on Sonnet 4.6, then Nova Pro; robustness checks; first measured cost | Full grid run under the protocol on at least Sonnet 4.6; the $60 re-plan point checked | about $20-30 | not started |
| **5** `real-cases` | v0.5 | Cases by the pre-registered selection rule, dossiers, foreshadowing check, recognition probe, a rubric committed before each case runs | At least three cases run and matched, including an invest or retool case; selection log complete | about $20-25 | not started |
| **6** `explorer-and-methods` | v0.6 | The full site and the methods page | A hostile reader could re-run the experiment from the published inputs; every real-case memo passed the name scan | under $2 | not started |
| **7** `writeup-and-launch` | v1.0 | README and launch post (his prose), the plain-English write-up, a definition-of-done audit against `planning/00` §8 | Every DoD item checked with evidence, partial passes marked partial | $0 | not started |

**Total, about $50-70** (`planning/07` §13 puts the worst case at about $71). Ceiling **$80**, re-plan point at
**$60** of cumulative project spend (`planning/04` §3.4). Sweep caps: **$5** development, **$25** official
(`planning/09` §6.2).

**Phase 0 was split in two on 2026-10-03** (his; Phase 0 scope doc, decision 6): the local half stays Phase 0,
the AWS half becomes Phase 0.5, so its IMPLEMENTATION doc is written after Phase 0 lands. `planning/05`'s
status line records the split.

**The phase slugs other than Phase 0's are provisional.** Each one is fixed when its scope doc is written.

### Phase doc status

Two layers per phase, as in Musical Mycelium: a short **scope doc** first, then an **IMPLEMENTATION doc**
written and approved immediately before the build, then a plain-English write-up written during the phase, not
after it. Both live in `docs/phases/`. Superseded docs move to `docs/archive/`; they are never deleted.

| Phase | Scope doc | IMPLEMENTATION doc |
|---|---|---|
| 0 | **APPROVED 2026-10-03** | **APPROVED 2026-10-03; built; DoD audit §11a** |
| 0.5-7 | not written; written in order after Phase 0 is built | not written; each immediately before its build |

**As in Musical Mycelium, every scope doc is written up front, one at a time through the whole roadmap, before
implementation begins** (his convention). Each phase then starts by writing its IMPLEMENTATION doc immediately
before its build. When a later finding changes a scope doc (Phase 2 can change the decision schema,
`planning/05` §7), the scope doc gets a dated amendment, as Musical Mycelium's did.

**The one exception, his decision 2026-10-03: Phase 0 is built first**, before the other scope docs, so the name
guard exists as soon as possible. After Phase 0, the scope docs for Phases 0.5 through 7 are written in order,
then Phase 0.5's IMPLEMENTATION doc.

### Where the build actually is — 2026-10-03, evening

- **Phase 0 is complete.** Four commits on `main`, all pushed: `f214280` (planning, pushed before the guard
  existed, confirmed clean by the guard's history scan), `9c382b8` (the name guard, hooks, toolchain, CI),
  `f45770b` (roadmap, known gaps, Phase 0 docs), `4405412` (`CLAUDE.md`, the guard explainer, the planning
  README). **CI run `37160410815`: green on the first push**, same numbers as local.
- **`planning/09` §7, the bootstrap checklist:** steps 1-6 and 8 **done**. Step 7 (claim the Vercel name) is his.
- **Next: the scope docs for Phases 0.5 through 7**, in order, before any further implementation.
- **Nothing has been run against any model by this repo.** Nothing official has been seen.

## 3. Scaffolding ledger

Musical Mycelium's rule: **structure now, content when its subject exists.** This ledger keeps deferred items
from being forgotten without building them early.

### In place as of 2026-10-03

| Item | Where |
|---|---|
| Ignore rules for `methods-appendix/`, secrets, Terraform state, local caches | `.gitignore` (committed in `f214280`) |
| Public GitHub repo | `github.com/sjtroxel/Horizon-Compact` |
| The design, patched and closed | `docs/planning/00`-`09`, `08a`, `08b` |
| Phase spine, ledger, decision history | `docs/ROADMAP.md` (this file) |
| Open items, newest first | `docs/KNOWN-GAPS.md` |
| Shared memory store | `~/.claude/projects/-home-sjtroxel-horizon-compact/memory`, a symlink to the job-search-headquarters store |

### Arrived in Phase 0 (2026-10-03)

| Item | Where |
|---|---|
| The name guard: commit, message and push scans, history scan, fail closed | `src/horizon_compact/privacy/`, `.pre-commit-config.yaml` |
| CI: `make check` on every push, the tracked-path check | `.github/workflows/ci.yml` |
| Python 3.13 toolchain, single config file, lockfile | `pyproject.toml`, `uv.lock` |
| Single-command entry point; `make check` equals CI | `Makefile` |
| Agent operating manual, rule zero on names | `CLAUDE.md` |
| Commit, push, tag, Terraform and AWS denied to Claude | `.claude/settings.json` |
| The guard, explained | `docs/name-guard-explained.md` |
| Planning read order and his disclosure line | `docs/planning/README.md` |

### Arrives in Phase 0.5

The Terraform bootstrap and budgets, the smoke calls, the development model, Ollama's reachability.

### Arrives with its subject, not before

| Item | Trigger |
|---|---|
| Dockerfile, ECR, ECS task definition | Phase 1: there is a harness to package |
| Deploy workflow with OIDC (role trusts this repo only; provider looked up, never created) | Phase 1: there is something to deploy |
| `web/` site | Phase 1's one page; full explorer in Phase 6. Initialized **inside** `web/`, never at the root |
| Experiment content (scenarios, objectives, wordings, lever menu, dossier) as versioned data | Phase 2 |
| The protocol file and the `prereg-v1` tag | Phase 3. Nothing official runs before it |
| Scorer and aggregation | Phase 3, tested on synthetic results only |
| Real-case dossiers, rubrics, the selection log | Phase 5 |
| Memo company-name scan before publishing | Phase 6 (`planning/09` A7) |

### Local prerequisites

Checked 2026-10-03 on WSL2: `uv` 0.12.0, Terraform 1.15.8, Docker 29.6.2, AWS CLI 2.36.14, `gh` 2.45.0, Node
22.20.0, GNU Make 4.3, system Python 3.12.3. **`pre-commit` is not installed**; Phase 0 brings it in as a
development dependency through `uv`. **Ollama is not on the WSL path**, which is not proof it is absent
(`planning/04` §6.3); Phase 0 checks it.

## 4. Decision history

Newest first. Each entry names who decided and where the reasoning lives. Decisions made during planning are
recorded in the planning docs themselves and are only indexed here.

- **2026-10-03 — Phase 0 complete** (CI run `37160410815`; `docs/phases/phase-0-scaffold-and-guardrails-IMPLEMENTATION.md` §11a).
- **2026-10-03 — All scope docs up front, Phase 0 excepted** (his). Phase 0 is built first so the name guard
  exists early; then the scope docs for 0.5 through 7, in order, before any further implementation.
- **2026-10-03 — Phase 0 decisions 1-6 made** (his; Phase 0 scope doc): a private term file with a longlist
  fingerprint; its path in local git config; whole-word, case-sensitive matching with per-term flags and
  allowed phrases; names, tickers and plant locations all counted; `make check` fails without the hooks; Phase 0
  split, AWS half to Phase 0.5.
- **2026-10-03 — No further commit or push until the guard is installed and has passed its canary test** (his).
- **2026-10-03 15:56 — First commit `f214280` pushed, before the name guard** (his, deliberate). `.gitignore` and
  the 12 planning files, scanned against the longlist by another session before the commit and again after the
  push; no case reference found either time (`KNOWN-GAPS.md`, 2026-10-03).
- **2026-10-03 — Planning closed** (`planning/09` §1). Every decision through `planning/09` §6 is made, his, as
  recommended: public from the first commit; sweep caps $5 and $25; `~/horizon-compact` on the shared memory;
  `08a` and `08b` copied in; reachability rule (b) in `planning/07` §8.
- **2026-10-03 — The repo follows Musical Mycelium's doc convention** (his): `ROADMAP.md`, then `KNOWN-GAPS.md`,
  then the Phase 0 scope doc, then its IMPLEMENTATION doc, before any code.
- **2026-10-03 — The name list stays outside the repo** (his). The longlist lives only in the private
  job-search-headquarters repo. Its path is never written into a tracked file; the hook reads it from an
  environment variable or a gitignored local config.
- **2026-10-03 — Nothing is committed until he says so** (his). Claude never runs `git commit` or `git push`.
- **2026-10-02 — Horizon Compact picked as the build**, name locked (his). `planning/00`.

## 5. After v1.0

From `planning/05` §6, in his decided order. **Each needs its own budget decision before its scope doc**; the $80
ceiling covers v1 only. Credits expire 2027-07-30.

1. More company types (committed first).
2. The horizon sweep.
3. A small-model contestant.
4. Memo analysis (a labeled LLM-judge pass).
5. A live "write your own objective" mode, the first always-on component.
6. The frequency study.
7. A fine-tuned or distilled CEO, after a cost check.

The Sonnet 5.5 sweep runs whenever access arrives (`planning/05` §5.2). Before the `prereg-v1` tag, its arrival
reopens the main-model choice as his decision; after the tag, it is its own sweep, never merged.
