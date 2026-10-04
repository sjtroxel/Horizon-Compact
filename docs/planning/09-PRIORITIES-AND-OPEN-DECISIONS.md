# Horizon Compact — Priorities, the Patch List, and What Remains Before the Repo

- **Status:** WRITTEN 2026-10-03. **The last numbered planning doc.** **Patch pass DONE the same afternoon** (P1-P34
  applied to `00`-`07`, §8). **All five of his decisions in §6 made 2026-10-03, as recommended.** Nothing is open.
  *Patched 2026-10-04 (his):* A1 done in Phase 0.5 (`docs/phases/phase-0.5-aws-foundation-IMPLEMENTATION.md` §19).
- **Read after:** `08-REVIEW`. **Read before:** the repo's Phase 0 scope doc.
- **What this doc is:** the forward-looking half of the review. `08` found what is wrong; this doc says **in what
  order it gets fixed, where each fix lands, and what stands between now and the first commit.** No new analysis.
- **What it is not:** the fixes themselves. The text patches in §3 were applied in their own pass (§8, step 1, done
  2026-10-03), so that `00`-`07` are consistent before they are copied into the repo.

---

## 1. Where planning ends

`00`-`07` set the design; `08` reviewed it and he approved all seven of its decisions (2026-10-03). After this doc,
**planning is closed.** No `10` follows. From here on, a change to the design is made one of two ways:

- **A dated patch** to the planning doc it belongs in, noted in that doc's status line, for anything decided before
  the repo exists or anything that changes the design itself.
- **A phase doc** (scope, then IMPLEMENTATION, `05` §5), for everything that is building work.

The planning folder stays canonical for every design decision (`00`, header) and travels into the repo as
`docs/planning/`.

---

## 2. The priority stack, stated once

When two pieces of work compete for a session, this is the order:

1. **The credibility of the measurement.** The one-way doors in `05` §3.1, above all: nothing official is seen before
   the protocol is committed. A late infrastructure mistake costs a week; a peek costs the result (`05` §2).
2. **A working skeleton on the real path.** One placeholder scenario, end to end, on the public URL (`05` Phase 1).
   Every later phase thickens it.
3. **The full experiment, then the explorer's polish.** Scenarios, wordings, repeats, the second model, real cases,
   then the views.

Under pressure, priority 3 gives first, by the cut list in `05` §5.1. Priority 1 never gives: the pre-registration,
the baseline, the published results against the thesis, three real cases including an invest or retool case, and
provenance are not on any cut list.

---

## 3. The text patches to `00`-`07` (apply before the repo)

Every finding in `08` that changes a sentence in `00`-`07`, in the order to apply them. The design-changing patches
come first because later patches refer to them. **Done when** every row is applied and each changed doc's status line
says "amended by `08` (2026-10-03)."

### 3.1 The objectives and the claims (from `08` §3.1-3.2)

| # | Doc and section | The patch | From |
|---|---|---|---|
| P1 | `00` §5.1 | Objectives rewritten in **one sentence frame**: *"Create value for [shareholders \| all of the company's stakeholders: customers, employees, suppliers, the communities in which it operates (including their environment), and shareholders], over [the next four quarters \| twenty years]."* E unchanged. Remove "finding about the model's built-in values"; say "the model's default in this role." | `08` §3.1, §3.2 |
| P2 | `01` §1.2-1.3 | The same frame; delete the claim that C's wording isolates who counts and replace it with the reason the frame does; note that "maximize total shareholder return" was dropped from A for parallel wording, as a known cost in realism. | `08` §3.1 |
| P3 | `07` §6.1 | "What it isolates" column made true under P1 (every primary pair now differs in one factor). Add: **"No split" means no split on the named outcome, for that scenario and model.** | `08` §3.1, §3.2 |
| P4 | `07` §7.1 | The three wordings are **three templates, each applied to all five objectives.** "Primary wording" is defined as the sealed one. Claims are "over these three wordings." | `08` §3.1, §3.4f, §5 |
| P5 | `06` §1, §5 | The interpretation table and the sample sentence rewritten to describe the model's behavior under the Roundtable's words ("under the Roundtable's wording, the model…"), never "the claim holds." The frame itself stays (`06` §10.1). | `08` §3.2 |
| P6 | `00` §5.4 | "Reads the company's revealed objective" becomes "shows which objective's runs the company's decision most resembled." Real cases are **illustrations of the protocol, not validation.** | `08` §3.2, §4.6 |

### 3.2 The decision shape (from `08` §3.3)

| # | Doc and section | The patch | From |
|---|---|---|---|
| P7 | `00` §5.2, `07` §3.1 | The menu gains a **supplier source** (pressing suppliers on price or payment terms), offered in S2 at minimum; Phase 2 decides whether it is offered elsewhere. `00` §5.2 stops saying every scenario uses the same dollar menu and says S3 departs from it (P8). | `08` §3.3 |
| P8 | `07` §3.2 | **S1:** the dossier must state the redeployment opportunity in numbers (the work, the retraining cost, the time to pay back). **S2:** restated as **who bears the shortfall**; shareholders bear it on one line (lower profit), with payout policy held fixed and stated. **S3:** stated as a discrete choice plus a workforce split, outside the dollar menu; every option equally fundable; the workforce outcome of every option stated, or of none. **S4:** the company has $B a year of uncommitted cash; fund the program with it or allocate it elsewhere; funding partly from cuts elsewhere is an explicit option. | `08` §3.3 |
| P9 | `07` §2.4 | Validation adds **lever caps**: no source may exceed the maximum the dossier states for it. | `08` §3.3 |
| P10 | `07` §9 | Two checklist items added: **the options offered are symmetric** (no group gets an option the others lack without a stated reason); **uncertainty is treated alike** (if one option's outcome is uncertain, every option's is stated with its uncertainty). | `08` §3.3 |

### 3.3 The statistics and the matcher (from `08` §3.4-3.6)

| # | Doc and section | The patch | From |
|---|---|---|---|
| P11 | `07` §3.2 | **S3's primary outcome is the close rate**; the full three-way split is descriptive. The family stays at 16. | `08` §3.4d |
| P12 | `07` §6.2-6.3 | Thresholds stay (10 points for shares, 20 for choice rates), each with one sentence on what it means in dollars or in runs. **Choice rates use Newcombe's interval** for a difference of proportions; shares keep the bootstrap, **at least 10,000 resamples**, stated. | `08` §3.4b, c, f |
| P13 | `07` §8 | The repeat rule is powered at **1.5 times the threshold** under the actual split rule. **Choice rates go to the cap** (spread assumed at its maximum, not estimated from the pilot). **Shares** are sized from the spread **pooled** across a scenario's cells. The "no split cannot be reached on a choice rate" sentence is corrected (reachable near 0% or 100%; not near 50% at the cap). | `08` §3.4a, b, e |
| P14 | `07` §3.3 | The summary groups are **for display only**; the matcher does not use them. | `08` §3.5 |
| P15 | `07` §10.4 | Distance computed **per run** on the lever-level vector over the observable dimensions, then averaged; a stated rule for dimensions not observed, with a minimum-evidence floor. **Tie:** the gap between the two nearest objectives lies inside its own bootstrap spread. **No good match:** a threshold set by synthetic tests in Phase 3 (A5), before any real case runs. The 0.05 and 0.50 are withdrawn. | `08` §3.5 |
| P16 | `07` §10 (new §10.0) | **Case selection by a mechanical rule**, committed in Phase 3: the first *k* candidates per case type, by date of first disclosure inside the window, from the named channels, that pass `01` §4.1. Every candidate considered is logged with the reason it was accepted or rejected. | `08` §3.6 |
| P17 | `07` §15 | Decisions 3, 4, 7 and 8 marked "amended by `08` §8 (2026-10-03)," each pointing to its patch. | `08` §8 |

### 3.4 Runs, storage and spend (from `08` §4.1-4.5)

| # | Doc and section | The patch | From |
|---|---|---|---|
| P18 | `07` §5 | A retry is a **fresh, identical request** (same prompt and menu order, no repair message). First-attempt results are published beside final ones. Results are labeled "among valid runs." For primary outcomes, a worst-case bound for the failed runs; no split is called if that bound overturns it. | `08` §4.1 |
| P19 | `02` §2.8, `05` §4.2 | Raw results written **one object per run** (or per small batch), write-once, so an interrupted sweep resumes. | `08` §4.2 |
| P20 | `02` §2.1, `03` §6 | The harness tracks **cumulative spend as it runs** and stops at the sweep's cap, in addition to the preflight estimate. `07` §13 notes that its totals exclude retries. | `08` §4.3 |
| P21 | `03` §4 | Development line no longer says "some Haiku/Sonnet"; it names the development model chosen in Phase 0 (A1). | `08` §4.4 |
| P22 | `07` §6 (new §6.5) | **Pre-registered descriptive analyses**, with no verdicts: the full allocation by objective, every lever's mean and spread, the summary groups, and E's distance to each objective under a defined metric (the per-run distance from P15). | `08` §4.5 |

### 3.5 Real cases, privacy and publishing (from `08` §4.6-4.9)

| # | Doc and section | The patch | From |
|---|---|---|---|
| P23 | `01` §4.3, `04` §2.2 | "Affected in discovery only, not in measurement" corrected: cases differ in which dimensions are observable, and each case's observed and excluded dimensions are shown beside its result. | `08` §4.6 |
| P24 | `01` §4.6 | Anonymization **scales headcounts by the same factor** as dollars (rounded), so pay per head and revenue per head are preserved. | `08` §4.7 |
| P25 | `04` §2.6, §7 item 1; `05` Phase 0 | The name check runs in a **local pre-commit hook** that reads the longlist on the laptop. CI checks that nothing under `methods-appendix/` is tracked. Tested with a made-up canary name, never a real one. | `08` §4.8 |
| P26 | `07` §12, `06` §6.1 | Every real-case memo is scanned for company names before publishing and held back if it names one. Real-case memos get their own label (not "for a fictional company"). | `08` §4.9 |
| P27 | `00` §8, `05` Phase 6 | "A hostile reader can re-run the experiment" becomes "re-run it from the published inputs, including the anonymized dossiers"; the methods page says reconstructing the cases from sources is not possible, and why. | `08` §5 |

### 3.6 Contradictions and small corrections (from `08` §5-6)

| # | Doc and section | The patch | From |
|---|---|---|---|
| P28 | `04` §1.2, §7 item 4 | "`07` committed as the pre-registration" becomes "the pre-registration, built from `07` in Phase 3 (`05`)." | `08` §5 |
| P29 | `05` §5.1, `04` §6.1 | Cutting wordings on the official model keeps the **sealed** wording, recomputes repeats, and drops the wording-robustness claim, stated on the methods page. | `08` §5 |
| P30 | `07` §7.3 | "About $3" becomes "about $5," matching §13. | `08` §5 |
| P31 | `01` §4.2, §4.3 | "Near-complete list" becomes "the main machine-searchable source"; "fully measurable" becomes "measurable in aggregate." | `08` §6 |
| P32 | `07` §2.1 | The Sonnet 5.5 row marked "per Anthropic's API; unverified on Bedrock." | `08` §6 |
| P33 | `02` §2.12 | "Filtered to this project's models" gains "if the filter works (`04` §3.3)." | `08` §6 |
| P34 | `00` status line, §9 | Points to `08` and `09` as the review and the patch list. | — |

**Thirty-four patches.** All are text. None needs a run, a purchase or an AWS change. **All applied 2026-10-03**
(§8). The pass also fixed the stale "JSONL per shard" wording in `02` §1 and `05` §3.2, §4.3, and found one more
issue, now item 5 in §6.

---

## 4. Building assignments (work done in a phase, not a text patch)

These cannot be applied to the planning docs because they are work. Each is assigned to the phase that does it, and
goes into that phase's IMPLEMENTATION doc.

| # | Phase | Assignment | From |
|---|---|---|---|
| A1 | **0** | **Name the development model** for Phase 2 runs: local (Ollama, once reachable from WSL) or a cheap Bedrock model that is neither an official model (Sonnet 4.6, Nova Pro) nor on a billing line Musical Mycelium already uses. Check that billing line first (*unverified* which Nova models Musical Mycelium spends on). *Done 2026-10-04 (his):* **Ollama `qwen3.5:4b` for volume, Nova Lite for the Bedrock path.** Musical Mycelium's bill shows Haiku 4.5, Nova Pro and Nova Micro, not Nova Lite; Nova Lite and the local model each made valid single tool calls in the Phase 0.5 smoke tests. | `08` §4.4 |
| A2 | **0** | The pre-commit name hook, the CI tracked-path check, and the canary test (P25). | `08` §4.8 |
| A3 | **1** | Per-run write-once storage (P19), the running spend cap (P20), and the account-wide rate limiter (`04` §3.1). | `08` §4.2-4.3 |
| A4 | **2** | Write the sentence frame and the **three wording templates** (P1, P4); the supplier source (P7); the four scenarios in their patched shapes (P8), including S1's redeployment numbers; a maximum for every source in the dossier (P9); the neutrality review with the two new items (P10). | `08` §3.1, §3.3 |
| A5 | **3** | On synthetic data, before the tag: **simulate the verdict rule** (power at 1.5 times the threshold, the false-split rate, behavior when every run agrees); **calibrate the matcher** on synthetic cases (identical, opposite, same choice with opposite money, sparse) and set its no-match threshold; commit the case-selection rule (P16) and the descriptive list (P22). | `08` §3.4-3.6, §4.5 |
| A6 | **5** | Headcount scaling in anonymization (P24); observed and excluded dimensions per case (P23); the selection log (P16). | `08` §3.6, §4.6-4.7 |
| A7 | **6** | The memo name scan and the real-case memo label (P26); the reproducibility wording on the methods page (P27). | `08` §4.9, §5 |

---

## 5. Open checks, gathered in one place

Every *unverified* item still open across `00`-`08`, with the phase that closes it. Checks are Claude's and use live
sources only (`00` §10). None blocks the patch pass or the repo's creation.

| Check | From | Closes in |
|---|---|---|
| Ollama's install location and reachability from WSL (7 GB of RAM visible there) | `00` §9.7, `04` §6.3 | Phase 0 |
| Whether AWS Budgets can filter on Horizon Compact's per-model billing lines; whether added budgets cost money; whether application inference profiles could tag spend | `04` §3.3 | Phase 0 (Terraform) |
| Converse: one tool with `auto` choice on Sonnet 4.6; how thinking settings are passed and recorded | `07` §14.1 | Phase 0 smoke call |
| Nova Pro: default temperature, availability, knowledge cutoff | `07` §14.2, `01` §7.5 | Phase 0 |
| Claude's default temperature value, for the methods page | `07` §14.3 | Phase 0 |
| How a refusal surfaces through Converse on Sonnet 4.6 | `07` §14.4 | Phase 0 |
| Whether a newer non-Anthropic model than Nova Pro is available to the account | `03` §7.4 | before the Phase 3 model set is fixed |
| Census AIES and BLS tables; Damodaran's terms of use; whether the SEC Financial Statement Data Sets are current | `01` §7.1-7.3, `04` §4.1 | Phase 2, before the dossier |
| Bootstrap, Newcombe intervals and the power rule implemented and tested on synthetic data | `07` §14.5, A5 | Phase 3 |
| Measured tokens and cost replace every estimate in `03` | `03` §7.5 | Phase 4 (pilot and first sweep) |
| Each real-case candidate: first-disclosure date, public status, recognition | `01` §7.6 | Phase 5 |
| Bedrock fine-tuning and custom-model serving costs | `00` §9.6 | before any fine-tuning phase (post-v1) |

**Waiting on AWS, nothing to do:** the Sonnet 5.5 quota requests (US: Support case 179097554500679; Global: pending).
If access arrives **before** the Phase 3 tag, the choice of main model reopens as his decision (`05` §5.2); after it,
Sonnet 5.5 is its own sweep.

**Closed by decision, recorded so they are not re-opened:** `02` §5 checks 4 and 5 (Nova Pro is the v1 second model;
dossier embeddings are local, `03` §5).

---

## 6. Decisions for him

Five, **all decided 2026-10-03 (his), as recommended.**

1. **DECIDED 2026-10-03 (his): public from the first commit**, with the `.gitignore` and the name hook in that
   commit. *Was:* public from the first commit, or private until a later phase? Recommended: public from the first commit.
   Musical Mycelium did the same; the planning folder is written to be publishable (`00`, header); and a public
   pre-registration commit is stronger evidence than a private one, because anyone can see its timestamp. What makes
   it safe: the `.gitignore` and the name hook (P25) are in the first commit, before anything private exists in the
   folder.
2. **DECIDED 2026-10-03 (his): $5 development, $25 official** (applied to `03` §6, `07` §13). *Was:* per-sweep
   spending caps. `03` §6 proposed $5 for development sweeps and $20 for official ones, never decided.
   `07` §13 puts the full fictional grid at about $19 before retries, which a $20 cap would likely refuse.
   **Recommended: $5 development, $25 official,** with the cumulative $60 re-plan point and the $80 ceiling unchanged
   (`04` §3.4).
3. **DECIDED (his): `~/horizon-compact`, joined to the shared memory store.** *Was:* the local folder and the
   shared memory. **Recommended:** clone to `/home/sjtroxel/horizon-compact` and join it
   to the shared memory store by symlink, as with the other active repos, so decisions made in either place are
   visible in both.
4. **DECIDED (his): copy `08a` and `08b` in.** *Was:* the 08a and 08b records in the public repo. **Recommended: copy them in** with the rest of `docs/planning/`.
   They show exactly how the independent review was made, which is the kind of evidence the project's method rests
   on. Neither contains anything private (checked: the brief describes the project; the reply discusses only the
   docs).

5. **DECIDED (his): add rule (b); `07` §8 updated.** *Was:* the reachability rule, found during the patch pass (`07` §8, rule (b)). The repeat rule `08` approved sizes
   repeats for power to find a split. It does not make sure "no split" can be reached: with a spread of 0.15 it gives
   10 repeats, the interval is then about ±11.5 points, wider than the 10-point threshold, so the C vs D share
   comparison (the Roundtable test) could end in "split" or "inconclusive" but never "no split." That would quietly
   undo `06` §1's promise that a result in the Roundtable's favor is as publishable as one against it. **Recommended:
   add rule (b):** repeats are also at least enough to keep the interval's half-width within 0.8 times the
   threshold, capped at 20 as now. Worst-case cost is unchanged (it is already priced at the cap, `07` §13); the
   likely cost rises toward it.

**Already decided, but owed in his words:** the one line in `docs/planning/README` saying the planning docs were
drafted with Claude from his interviews and decisions (`06` §10.4, §8).

---

## 7. Repo bootstrap checklist (mechanical; once the patches are applied)

In order. The first two items exist to stop the one mistake that cannot be undone: a real company's name in a public
commit (`04` §2.6).

1. **Create `Horizon-Compact` on GitHub** (his account; **public**, §6.1). He runs the commands.
2. **First commit, before anything else is copied in:** `.gitignore` containing `methods-appendix/`, `.env`,
   Terraform state and local caches; the pre-commit name hook (P25) and its canary test.
3. **Copy the planning folder to `docs/planning/`, excluding `methods-appendix/`.** That folder stays in
   `job-search-headquarters`, which is private and is its backup (`01` §4.8). Check the copy with `git status`
   before committing: nothing under `methods-appendix/` may appear.
4. **`CLAUDE.md`** from `00` §10's working rules, plus: planning is closed (§1 here); patches are dated in the doc's
   status line; nothing official runs before the `prereg-v1` tag (`05` §2).
5. **`docs/planning/README`**: the read order (`00` through `09`, with `08a` and `08b` as records), and his one-line
   disclosure (§6).
6. **The shared memory symlink** for the new local path (§6.3).
7. **Claim `horizon-compact.vercel.app`** early (`02` §2.9), as a placeholder.
8. Then **Phase 0's scope doc and IMPLEMENTATION doc** (`05` §5), written and approved before any code. A1 and A2 go
   in it, with the Phase 0 checks from §5.

---

## 8. The sequence from here

**Patch pass (§3, done) → his decisions (§6, done) → repo creation and bootstrap (§7) → Phase 0 scope and IMPLEMENTATION
docs → Phase 0 build.**

- **Step 1, the patch pass: DONE 2026-10-03.** P1-P34 applied to the planning folder in this repo; each changed
  doc's status line notes it; a final sweep found no remaining sentence in `00`-`07` that contradicts `08` §8 (old
  wordings survive only where marked as corrected, as the record of what changed).
- **Step 2 and after:** the repo. From that point the planning folder lives in `docs/planning/`, and its copy here is
  frozen as the record of how the project was planned.

---

## 9. Bottom line

- **Planning is closed with this doc.** Ten documents, `00` through `09`, plus the two review records.
- **Thirty-four text patches** make `00`-`07` agree with `08`. **Applied 2026-10-03;** the patched folder is what
  gets copied into the repo.
- **Seven building assignments** carry `08`'s fixes into the phases that do them; the largest is Phase 3's synthetic
  tests, which set the matcher's threshold and prove the verdict rule before anything real is run.
- **Five small decisions, all made** (public repo; caps $5 and $25; `~/horizon-compact` on the shared memory;
  `08a`/`08b` copied in; the reachability rule). Nothing stands between the patched folder and the first commit.
- **Nothing has been run, so nothing has been seen.** Every fix in `08` lands before the protocol is frozen, which is
  the only time it is free.
