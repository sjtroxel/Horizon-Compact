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
| **0.5** `aws-foundation` | v0.0.5 | Terraform bootstrap (OIDC looked up), filtered budgets, one tool call per Bedrock model, Ollama check, the development model named, the AWS checks in `planning/09` §5 | A recorded, provenance-stamped call from each Bedrock model; bootstrap applied with nothing shared created | under $1 | **closed 2026-10-08**, $0.02 measured |
| **1** `walking-skeleton` | v0.1 | The run path on **placeholder content, off the subject** (scenario, objectives, menu): Fargate, rate limiter, spend cap, official gate (closed), Bedrock, per-run write-once S3 | Container-run results in S3, each traceable to its image digest and input hashes; resume and cap shown | about $1 with 1.5 | **building since 2026-10-05**; steps 3, 9, 11, 12 wait on Bedrock quotas (`KNOWN-GAPS.md`) |
| **1.5** `publish-path` | v0.1.5 | Scorer, committed static JSON, one page live at `horizon-compact.vercel.app` through CloudFront and Vercel | The placeholder sweep on the public URL, traceable; destroy and re-apply of `main` tested, raw results intact | cents | not started |
| **2** `experiment-content` (split 2026-10-04: **2** `company-dossier`, **2.5** `scenarios-and-wordings`) | v0.2, v0.2.5 | The cited fictional dossier, the four scenarios, the sentence frame and three wording templates, the supplier source, lever caps, the neutrality review; development runs for format and clarity only, every change logged | Every dossier number sourced or marked as an assumption; every scenario passes the neutrality checklist; development runs parse under all five objectives | about $5-10 | **2 `company-dossier`: BUILT AND CLOSED 2026-10-06, out of order** (steps 1-9; `pyproject.toml` stays at Phase 1's version until Phases 1 and 1.5 close, Phase 2 decision 4); 2.5 not started |
| **3** `preregistration-and-scoring` (split 2026-10-04: **3** `scoring-and-simulation`, **3.5** `preregistration`) | v0.3, v0.3.5 | The protocol tagged `prereg-v1`; scoring tested on synthetic data only, including the verdict-rule simulation and the matcher calibration | Tag exists; the harness refuses an official sweep whose protocol hash does not match it; simulation results recorded in the protocol | $0 | not started |
| **4** `official-grid` | v0.4 | Pilot (excluded), then the full grid on Sonnet 4.6, then Nova Pro; robustness checks; first measured cost | Full grid run under the protocol on at least Sonnet 4.6; the $60 re-plan point checked | about $20-30 | not started |
| **5** `real-cases` (split 2026-10-04: **5** `case-building`, **5.5** `case-runs`) | v0.5, v0.5.5 | Cases by the pre-registered selection rule, dossiers, foreshadowing check, recognition probe, a rubric committed before each case runs | At least three cases run and matched, including an invest or retool case; selection log complete | about $20-25 | not started |
| **6** `explorer-and-methods` (split 2026-10-04: **6** `explorer`, **6.5** `methods-and-release`) | v0.6, v0.6.5 | The full site and the methods page | A hostile reader could re-run the experiment from the published inputs; every real-case memo passed the name scan | under $2 | not started |
| **7** `writeup-and-launch` | v1.0 | README and launch post (his prose), the plain-English write-up, a definition-of-done audit against `planning/00` §8 | Every DoD item checked with evidence, partial passes marked partial | $0 | not started |

**Total, about $50-70** (`planning/07` §13 puts the worst case at about $71). Ceiling **$80**, re-plan point at
**$60** of cumulative project spend (`planning/04` §3.4). Sweep caps: **$5** development, **$25** official
(`planning/09` §6.2).

**Phase 0 was split in two on 2026-10-03** (his; Phase 0 scope doc, decision 6): the local half stays Phase 0,
the AWS half becomes Phase 0.5, so its IMPLEMENTATION doc is written after Phase 0 lands. `planning/05`'s
status line records the split.

**Phase 1 was split in two on 2026-10-04** (his; Phase 1 scope doc, decision 1): the run path stays Phase 1, the
scorer, the page and the teardown test become Phase 1.5, both before Phase 2.

**The main model is Sonnet 4.6, fixed for v1** (his, 2026-10-05). Until then it was a slot held open for Sonnet
5.5. AWS answered the quota case on 2026-10-05: the newest models are held until an account has several billing
cycles of Bedrock use, so Sonnet 5.5 is no longer awaited (`planning/05` §5.2, patched). Model IDs, prices and
quotas stay config, never code (Phase 1 scope doc).

**Phase 2 was split in two on 2026-10-04** (his; Phase 2 scope doc, decision 1): the cited company dossier is Phase
2, the scenarios, wordings, neutrality review and blind development runs are Phase 2.5.

**Phase 3 was split in two on 2026-10-04** (his; Phase 3 scope doc, decision 1): the statistics, proven on synthetic
data, are Phase 3; the protocol, its independent review, the freeze and the `prereg-v1` tag are Phase 3.5.

**Every phase slug is now fixed by its scope doc.** Each one is fixed when its scope doc is written.

### Phase doc status

Two layers per phase, as in Musical Mycelium: a short **scope doc** first, then an **IMPLEMENTATION doc**
written and approved immediately before the build, then a plain-English write-up written during the phase, not
after it. Both live in `docs/phases/`. Superseded docs move to `docs/archive/`; they are never deleted.

| Phase | Scope doc | IMPLEMENTATION doc |
|---|---|---|
| 0 | **APPROVED 2026-10-03** | **APPROVED 2026-10-03; built; DoD audit §11a** |
| 0.5 `aws-foundation` | **APPROVED 2026-10-04**, all eight decisions as recommended | **APPROVED 2026-10-04**, its four decisions (A-D) as recommended; **built 2026-10-04** (`b9c9aaf`, `52aa3fd`, `ac2fbe0`); **closed 2026-10-08**, DoD audit §21 |
| 1 `walking-skeleton` | **APPROVED 2026-10-04**, all five decisions as recommended; split into 1 and 1.5 | **APPROVED 2026-10-04**, its four decisions as recommended; not yet built |
| 1.5 `publish-path` | **APPROVED 2026-10-04**, with Phase 1 | not written; immediately before its build |
| 2 `company-dossier` | **APPROVED 2026-10-04**, all five decisions as recommended; split into 2 and 2.5 | **APPROVED 2026-10-06**, its five decisions as recommended; **built and closed 2026-10-06**, DoD audit in §14 |
| 2.5 `scenarios-and-wordings` | **APPROVED 2026-10-04**, all six decisions as recommended | **APPROVED 2026-10-07**, its seven decisions as recommended (8 and 9 added and decided in the build); **built and closed 2026-10-07**, DoD audit in §22 |
| 3 `scoring-and-simulation` | **APPROVED 2026-10-04**, both decisions as recommended; split into 3 and 3.5 | **APPROVED 2026-10-08 (his)**, its ten decisions as recommended; not yet built |
| 3.5 `preregistration` | **APPROVED 2026-10-04**, all six decisions as recommended (5 is decided in the phase, from evidence) | not written; immediately before its build |
| 4 `official-grid` | **APPROVED 2026-10-04**, all six decisions as recommended; not split | not written; immediately before its build |
| 5 `case-building` | **APPROVED 2026-10-04**, all six decisions as recommended; split into 5 and 5.5 | not written; immediately before its build |
| 5.5 `case-runs` | **APPROVED 2026-10-04**, with Phase 5 | not written; immediately before its build |
| 6 `explorer` | **APPROVED 2026-10-04**, all six decisions as recommended (6 amended by him); split into 6 and 6.5 | not written; immediately before its build |
| 6.5 `methods-and-release` | **APPROVED 2026-10-04**, with Phase 6 | not written; immediately before its build |
| 7 `writeup-and-launch` | **APPROVED 2026-10-04**, all six decisions as recommended; not split; written to be re-scoped when the phase starts | not written; immediately before its build |

**As in Musical Mycelium, every scope doc is written up front, one at a time through the whole roadmap, before
implementation begins** (his convention). Each phase then starts by writing its IMPLEMENTATION doc immediately
before its build. When a later finding changes a scope doc (Phase 2 can change the decision schema,
`planning/05` §7), the scope doc gets a dated amendment, as Musical Mycelium's did.

**The one exception, his decision 2026-10-03: Phase 0 is built first**, before the other scope docs, so the name
guard exists as soon as possible. After Phase 0, the scope docs for Phases 0.5 through 7 are written in order,
then Phase 0.5's IMPLEMENTATION doc.

### Where the build actually is — 2026-10-07, evening

**Measured 2026-10-07, evening:** `make check` green, **723 tests passed**, root 13 of 16.

- **Phase 2.5 `scenarios-and-wordings` is built and closed** (out of order, as Phase 2 was): four scenarios as data,
  three wording templates, **`w2` sealed** by a draw from the review commit; a neutrality checklist and a blind
  reader (`google/gemini-3.1-pro-preview`), 14 logged changes to the text; probes and format runs pass on the
  development model `gpt-oss-openrouter`. DoD audit in its IMPLEMENTATION doc §22. About $0.59 of his OpenRouter
  balance, no AWS spend, no official model.
- **Next: Phase 3 `scoring-and-simulation`**, its IMPLEMENTATION doc first (Opus). It needs no AWS and no model.
- **Before Phase 3.5's tag:** the Nova Lite probes and format runs (`KNOWN-GAPS.md`, OPEN). Phase 1 steps 3, 9, 11,
  12, Phase 1.5 and Phase 0.5's close-out still wait on AWS.

### Where the build actually was — 2026-10-06, evening *(superseded by the block above; kept as the day's record)*

**Measured 2026-10-06, evening:** `make check` green, **442 tests passed**, root 13 of 16. `origin/main` at `6262c82`;
the Phase 2 close-out (steps 8 and 9) is one commit he runs.

- **Phase 2 `company-dossier` is built and closed** (out of order, his): 218 figure rows, 31 assumptions, a rendered
  pack of about 2,100 words, DoD audit in its IMPLEMENTATION doc §13 step 9 (DoD 4 marked partial: his review was an
  acceptance by deferral). One outside call, $0.50, no AWS spend and no official model. `pyproject.toml` unchanged.
- **Next: Phase 2.5 `scenarios-and-wordings`**, its IMPLEMENTATION doc first (Opus), unless AWS restores Bedrock
  first (`KNOWN-GAPS.md`, START HERE, "TOMORROW"). **Bedrock** still throttled at 2:31 PM CDT, $0.
- **Phase 0.5 still open** on billing data (`KNOWN-GAPS.md`, WAITING); Phase 1 steps 3, 9, 11, 12 still wait on Bedrock.

### Where the build actually was — 2026-10-06, morning *(superseded by the block above; kept as the day's record)*

- **Phase 2 `company-dossier` started out of order (his):** everything ahead of it waits on AWS (`KNOWN-GAPS.md`,
  START HERE, "WAITING ON AWS"). Its IMPLEMENTATION doc is approved (his, 2026-10-06, all five decisions as recommended)
  (`docs/phases/phase-2-company-dossier-IMPLEMENTATION.md`). Phase 2 calls no official model and nothing on AWS.
- **The Bedrock quota case** has his restricted-list follow-up (2026-10-06 08:04 CDT); both models still throttled
  at 13:03 UTC, $0.
- Nothing else changed since the block below.

### Where the build actually was — 2026-10-05, 1:20 PM *(superseded by the block above; kept as the day's record)*

**Measured 2026-10-05, 1:20 PM:** `make check` green, **353 tests passed**, both Terraform roots (`bootstrap`, `main`)
validate, root 13 of 16. `origin/main` at `ab76636`.

- **Phase 1 build (Sonnet), steps 0-2, 4-8 and 10 done:** C1 `70a4c4e` (harness and tests), `b89b270` (stop on quota
  errors), C2+C3 folded into `927036f` (container; results bucket, ECR, boundary and deploy policy, applied), C4
  `ab76636` (`main` root, deploy and permission-check workflows). **First deploy green on its first run** (run
  `37352790960`, 16 resources); permission check passed (run `37353579140`); an official launch refused.
- **Bedrock is blocked account-wide as far as can be read** (`KNOWN-GAPS.md`, BLOCKED): steps 3 and 9, and so 11 and 12,
  wait for AWS. No model has seen experiment content; no task has run.
- **Phase 0.5 still open** on billing data (`KNOWN-GAPS.md`, WAITING).

### Where the build actually was — 2026-10-04, 7 PM *(superseded by the block above; kept as the day's record)*

**Measured 2026-10-04, 7 PM:** `make check` green, **178 tests passed**, Terraform `validate` clean, root 13 of 16
(12 tracked, plus the untracked `experiment/` that Phase 1's C1 adds). The dated lines below are a record of the
day; a count inside one is that moment's count.

- **Phase 0 is complete.** Four commits on `main`, all pushed: `f214280` (planning, pushed before the guard
  existed, confirmed clean by the guard's history scan), `9c382b8` (the name guard, hooks, toolchain, CI),
  `f45770b` (roadmap, known gaps, Phase 0 docs), `4405412` (`CLAUDE.md`, the guard explainer, the planning
  README). **CI run `37160410815`: green on the first push**, same numbers as local.
- **`planning/09` §7, the bootstrap checklist:** steps 1-6 and 8 **done**. Step 7 (claim the Vercel name) is his.
- **2026-10-04: scope docs for Phases 0.5, 1, 1.5, 2, 2.5, 3 and 3.5 written and APPROVED** (his), all decisions
  as recommended. Phases 1, 2 and 3 were each split in two. Planning `01`, `02`, `05` and `07` carry dated patches
  from those decisions. No code was written; `make check` unchanged (123 tests passing).
- **2026-10-04 morning: Phase 0.5's pre-build checks run** (his call, before Phase 4): four of seven closed, two
  partly, one waits for the build (`KNOWN-GAPS.md`). Four `planning/07` patches proposed from them, not yet approved (*made later the same day*).
- **2026-10-04: the Phase 4 `official-grid` scope doc written and APPROVED** (his), all six decisions as recommended:
  the pilot blind to objective, the re-plan check projected from the pilot before the grid (and against the credit
  balance), one shuffled run order, one sweep per study, results committed as data at the phase's end, one phase.
  `planning/04` §3.4 and `planning/07` §11 patched.
- **2026-10-04: the Phase 5 scope doc written and APPROVED, and split** (his), all six decisions as recommended:
  Phase 5 `case-building` and Phase 5.5 `case-runs`, every case built and frozen before any runs; the real-case
  rules frozen in the protocol (Phase 3.5 scope doc amended); a minimal dossier builder; a required independent
  reader; dossiers published only after a re-identification check; the search date set by rule. `planning/01`,
  `02`, `04`, `05` and `07` patched.
- **2026-10-04: the Phase 6 scope doc written and APPROVED, and split** (his), all six decisions as recommended,
  decision 6 amended by him: Phase 6 `explorer` and Phase 6.5 `methods-and-release`; results on the public site only
  at go-live; the gray zone of who writes the site's words settled; re-scoring in CI plus prompt reconstruction; no
  visitor tracking; an impressive layer (guided story, share cards, cold-read test, narrated video, ElevenLabs
  available). `planning/02`, `05` and `06` patched.
- **2026-10-04: the four `planning/07` patches from Phase 0.5's checks made** (his approval), and `planning/06` §11's
  one citation whose URL named companies shortened to its domain.
- **2026-10-04: the Phase 7 `writeup-and-launch` scope doc written and APPROVED** (his), all six decisions as
  recommended; written to be re-scoped when the phase starts (its own section lists what will change). **Every scope
  doc, Phases 0 through 7, is now written and approved.**
- **2026-10-04: Phase 0.5's IMPLEMENTATION doc written and APPROVED** (his),
  `docs/phases/phase-0.5-aws-foundation-IMPLEMENTATION.md`, decisions A-D as recommended; the dev IAM policy drafted
  with it.
- **2026-10-04 evening: Phase 0.5 built** (Sonnet), reviewed (Opus): bootstrap applied with nothing shared created,
  deploy-role trust proven, eight smoke records committed, the development model named (his: Ollama `qwen3.5:4b` +
  Nova Lite). `planning/03`, `07` and `09` patched from the findings.
- **2026-10-04 evening: Phase 1's IMPLEMENTATION doc written (Opus) and APPROVED** (his), its four decisions as
  recommended; the placeholder drafted alongside it in `experiment/` (untracked until Phase 1's C1).
- **Next: Phase 1's build (Sonnet), from that doc's §16, step 0. Phase 0.5's close-out** runs alongside it once
  billing data posts (`KNOWN-GAPS.md`, WAITING entry); Phase 1's first Sonnet sweep (its step 9) waits for it.
- **Development calls only.** The smoke prompt is a unit conversion, off the subject entirely. Nothing official has
  been seen, and no model has seen any experiment content.

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
| `web/` site | Phase 1.5's one page; full explorer in Phase 6. Initialized **inside** `web/`, never at the root |
| Experiment content (scenarios, objectives, wordings, lever menu, dossier) as versioned data | Phase 2 |
| The protocol file and the `prereg-v1` tag | Phase 3.5 (split from Phase 3, 2026-10-04). Nothing official runs before it |
| Scorer and aggregation | Phase 1.5, descriptive only; verdicts, intervals and the matcher in Phase 3, tested on synthetic results only |
| Real-case dossiers, rubrics, the selection log | Phase 5 |
| Memo company-name scan before publishing | Phase 6 (`planning/09` A7) |

### Local prerequisites

Checked 2026-10-03 on WSL2: `uv` 0.12.0, Terraform 1.15.8, Docker 29.6.2, AWS CLI 2.36.14, `gh` 2.45.0, Node
22.20.0, GNU Make 4.3, system Python 3.12.3. **`pre-commit` is not installed**; Phase 0 brings it in as a
development dependency through `uv`. **Ollama is not on the WSL path**, which is not proof it is absent
(`planning/04` §6.3); Phase 0 checks it. *Updated 2026-10-04:* the check moved to Phase 0.5; a read-only look found
Ollama installed on the Windows side; whether WSL can reach it is still unchecked.

## 4. Decision history

Newest first. Each entry names who decided and where the reasoning lives. Decisions made during planning are
recorded in the planning docs themselves and are only indexed here.

- **2026-10-07 — Phase 2.5 `scenarios-and-wordings` built and closed** (his; out of order, AWS still blocked). The
  IMPLEMENTATION doc's seven decisions approved as recommended; decision 8 (S1 as three priced paths) and decision 9
  (`gpt-oss-openrouter` as the development model, amended to cover every Phase 2.5 run) added in the build. A
  ten-item neutrality checklist (Opus) and a blind reader (`google/gemini-3.1-pro-preview`, $0.28), whose point R5
  found that S4's cuts spared payouts, prices and the environment, which the checklist had missed; all of both
  accepted by him. Fourteen logged changes to the text, one of them (S2's wage limit) from the format runs. **The
  sealed template is `w2`,** drawn once from the review commit `67cfac6`. Phase 2.5 closed on the development model
  by decision 7; the Nova Lite runs are a prerequisite of Phase 3.5's tag. `planning/07` §3.2 patched (S4's cuts).
  **Cost: about $0.59 of his OpenRouter balance; no AWS spend and no official model call.**

- **2026-10-06 — Phase 2 `company-dossier` built and closed, started out of order** (his; Phases 1, 1.5 and every
  Bedrock run were waiting on AWS, and Phase 2 needs neither AWS nor a model). The IMPLEMENTATION doc and its five
  decisions were approved as recommended. Built and closed in one day: the four source checks (`planning/01`
  patched), 218 figure rows with 31 assumptions, a rendered 2,113-word board pack and its cited public version,
  his review by deferral (disclosed), a two-sided neutrality read (one wording changed, `planning/07` L9 patched;
  S3's missing community consequence logged for Phase 3), and a realism read by `openai/gpt-6-astra` (13 points
  verified, 8 acted on, 5 declined or logged). **Cost: $0.50, one OpenRouter call from his balance, outside the $80
  AWS ceiling; no AWS spend and no official model call.** The version in `pyproject.toml` is unchanged.
  Reasoning and the as-built record: `docs/phases/phase-2-company-dossier-IMPLEMENTATION.md`.
- **2026-10-05 — Sonnet 4.6 fixed as the v1 main model; Sonnet 5.5 no longer awaited** (his), after AWS held
  the newest models until the account has several billing cycles of Bedrock use. The main-model slot is closed;
  nothing is spent to qualify. `planning/02`-`05`, `07`, `09` and eight scope docs patched (`KNOWN-GAPS.md`).
- **2026-10-04 — Phase 7 scope doc approved** (his), all six decisions as recommended, not split: public prose
  decided by piece (README and release notes may be Claude-drafted on his grant; the post and card his by default);
  the launch post last; README numbers tied to data by a test and claims tied to the audit; the audit re-verified by
  a fresh session; a hosting plan so nothing bills cash after the credits expire 2027-07-30; two launch posts planned.
  Scoping is complete.
- **2026-10-04 — the four `planning/07` patches from Phase 0.5's checks made** (his approval); `planning/06` §11's
  company-naming citation shortened.
- **2026-10-04 — Phase 6 and 6.5 scope docs approved** (his), all six decisions as recommended, decision 6 amended
  by him: split into Phase 6 `explorer` and Phase 6.5 `methods-and-release`; results reach the public site only at
  go-live, complete (`planning/06` §6.1 patched); Claude drafts the result-sentence templates and he approves them
  word for word, the landing question, scope sentence and titles his (`planning/06` §8 patched); "re-run" shown by
  CI re-scoring and byte-for-byte prompt reconstruction (`planning/05` patched); no visitor tracking; the impressive
  layer, with the video a full piece and ElevenLabs available at a cost named first (`planning/06` §7.3, `planning/02`
  §2.9 patched).
- **2026-10-04 — Phase 5 and 5.5 scope docs approved** (his), all six decisions as recommended: split into Phase 5
  `case-building` and Phase 5.5 `case-runs`, every case frozen before any runs; the real-case build rules, the
  gate's case mode and the search date (by rule: the day after Phase 4's results are committed) frozen in the
  protocol (Phase 3.5 scope doc amended; `planning/07` §10.0-10.4 patched); a minimal dossier builder without
  retrieval or reranking (`planning/02` §2.7 patched); a required independent reader on judgment rejections and
  every rubric (`planning/04` §2.4, `planning/01` §4.1 patched); dossiers published only after a
  re-identification check (`planning/05` Phase 6 done-when patched); scaling factor drawn and option figures
  pre-cut-off only (`planning/01` §4.6 patched).
- **2026-10-04 — Phase 4 scope doc approved** (his), all six decisions as recommended, not split: the pilot and
  running sweeps blind to objective; the re-plan check projected from the pilot before the grid, against the credit
  balance too (`planning/04` §3.4 patched); one shuffled run order and one sweep per study (`planning/07` §11
  patched); results committed as data at the phase's end.
- **2026-10-04 — Phase 0.5's pre-build checks run** (his call, before Phase 4): four of seven closed, two partly,
  one waits for the build (`KNOWN-GAPS.md`). Four `planning/07` patches proposed from them, not yet approved (*made later the same day*).
- **2026-10-04 — Phase 3 and 3.5 scope docs approved** (his), all eight decisions as recommended. Phase 3: split;
  established library implementations for the intervals, tested against published examples. Phase 3.5: the tag
  freezes content, protocol and analysis code (`planning/05` §3.1 patched); tag protection, an independent public
  archive and a release; an independent review of the protocol before the tag; real-case types and *k*
  (`planning/07` §10.0 patched); errata allowed for changes that alter no computation (`planning/07` patched); the
  main model chosen in Phase 3.5 from Phase 0.5's measurements if Sonnet 5.5 has arrived.
- **2026-10-04 — Phase 2 and 2.5 scope docs approved** (his), all eleven decisions as recommended. Phase 2: split;
  Claude drafts the instrument and he reviews every line, disclosed; industry-level sources only, no peer companies
  (`planning/01` §2.2 patched); the company unnamed; one shared dossier. Phase 2.5: the development loop blind to
  outcomes, and a degenerate scenario is a result, not a defect (`planning/05` §2 patched); discrete options
  shuffled per run (`planning/07` §4, §7.2 patched); the sealed template drawn at random (`planning/07` §7.1
  patched); S1's retraining cost stated separately (`planning/07` §3.2 patched); the blind reader from another
  vendor through OpenRouter.
- **2026-10-04 — Phase 1 scope doc approved** (his), all five decisions as recommended: split into Phase 1
  `walking-skeleton` and Phase 1.5 `publish-path`; the placeholder off the subject in scenario, objectives and menu
  (`planning/05` §1-2 patched); the skeleton runs on the main model; the raw results bucket in `bootstrap`, and
  inputs built into the image with the published JSON committed (`planning/02` §1, §2.8, §2.10 patched). Also his:
  every scope doc leaves room for Sonnet 5.5 as the main model; Phase 0.5 amended to smoke-test it if access arrives.
- **2026-10-04 — Phase 1 IMPLEMENTATION doc approved** (his), its four decisions as recommended: ECR in `bootstrap`
  (Phase 1 scope doc and `planning/02` §2.10 patched); the dev key kept through Phase 1 (Phase 0.5 decision A
  amended); deploy on push for code, experiment and infrastructure paths, plus manual; 15 skeleton runs and 5
  development runs. Also from writing it: the tool schema identical on every run so caching works; write-once enforced
  by the results bucket's policy; IAM policies as JSON files so tests can parse them.
- **2026-10-04 — Phase 0.5 built; development model named** (his): Ollama `qwen3.5:4b` for volume, Nova Lite for the
  Bedrock path (`planning/09` A1 and `planning/03` §4 patched). From the smoke calls: a `ModelErrorException` is a
  model outcome, `malformed_tool_use`, not an API error, and text beside one tool call is not `no_tool_call`
  (`planning/07` §5.1 patched); Converse reports no separate thinking-token count (`planning/07` §7.3 patched); a
  tool-use input overhead of a few hundred tokens per call (`planning/03` §3.1 patched). The Sonnet-line budget waits
  for Sonnet's Service name to appear in the Budgets list, which happens only after it is billed.
- **2026-10-04 — Phase 0.5 IMPLEMENTATION doc approved** (his), its four decisions as recommended: (A) a scoped IAM
  user `horizon-compact-dev` with a managed policy that explicitly denies changes to the OIDC provider and to other
  budgets, and invocation of Musical Mycelium's models, its key deleted at phase end; (B) Nova Lite and gpt-oss-120b
  as the Bedrock development-model candidates, beside Ollama `qwen3.5:4b`; (C) Sonnet 4.6 and Nova Pro each called by
  both routes; (D) the deploy role's ARN as a GitHub secret. Also from writing it: the `.claude/settings.json` deny
  rules gain the `terraform -chdir=*` forms; `*.tfvars` gitignored; budgets on one CUSTOM period; the identity
  check masks the account ID in public logs.
- **2026-10-04 — Phase 0.5 scope doc approved** (his), all eight decisions as recommended: deploy role with no
  permissions, proven by one workflow run; budgets in `bootstrap` (`planning/02` §2.10 patched); the Nova Pro
  billing line settled by checking tagged inference profiles first; the real provider seam for the smoke calls;
  smoke records committed; he runs every AWS-authenticated command; Nova Pro at its own default temperature
  (`planning/07` §2.3 patched); the development model chosen at the end of the phase.
- **2026-10-03 — Phase 0 complete** (CI run `37160410815`;
  `docs/phases/phase-0-scaffold-and-guardrails-IMPLEMENTATION.md` §11a).
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

*2026-10-05:* a Sonnet 5.5 sweep is no longer planned (`planning/05` §5.2). If access ever arrives, it is a new
decision of his, run as its own sweep and never merged.
