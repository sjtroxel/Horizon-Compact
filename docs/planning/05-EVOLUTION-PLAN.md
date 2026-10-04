# Horizon Compact — Evolution Plan

- **Status:** APPROVED 2026-10-03 (his five decisions in §8). Sets the phase order, what each phase delivers, and
  what grows after v1.0. **Amended by `08` (2026-10-03):** §3.1 the name check, §4.2 per-run storage, Phases 0, 3
  and 6, §5.1 the wording cut (patches P19, P25, P27, P29 and assignments A1-A7 in `09` §3-4).
  **Patched 2026-10-03 (his):** §5's Phase 0 is split. The local half (repo, guardrails, toolchain, CI) stays
  Phase 0; the AWS half (Terraform bootstrap, budgets, smoke calls, Ollama, the development model, the `09` §5
  checks) becomes Phase 0.5 `aws-foundation`. Reason and record: `docs/phases/phase-0-scaffold-and-guardrails.md`,
  decision 6. The table below is unchanged as the record of the plan.
  **Patched 2026-10-04 (his), from `docs/phases/phase-1-walking-skeleton.md`:** §5's Phase 1 is split into Phase 1
  `walking-skeleton` (the run path: results land in S3) and Phase 1.5 `publish-path` (the scorer, the page, the
  teardown test), both done before Phase 2 (decision 1). §1 and §2: the skeleton's placeholder is **off the
  experiment's subject entirely**, in scenario, objectives and menu, not only in scenario (decision 2).
  **Patched 2026-10-04 (his), from `docs/phases/phase-2-company-dossier.md` and
  `docs/phases/phase-2.5-scenarios-and-wordings.md`:** §5's Phase 2 is split into Phase 2 `company-dossier` and Phase
  2.5 `scenarios-and-wordings`. §2: the development loop is built blind to outcomes, and no scenario changes for an
  outcome reason (Phase 2.5 decisions 1 and 2).
  **Patched 2026-10-04 (his), from `docs/phases/phase-3-scoring-and-simulation.md` and
  `docs/phases/phase-3.5-preregistration.md`:** §5's Phase 3 is split into Phase 3 `scoring-and-simulation` (the
  statistics, proven on synthetic data) and Phase 3.5 `preregistration` (the protocol, its review, the freeze and the
  tag). §3.1: the tag freezes the analysis code as well as the content and the protocol (Phase 3.5 decision 1).
- **Read after:** `04-RISK-REGISTER`. **Read before:** `06`.
- **Answers two questions:** in what order does v1 get built so that nothing built early has to be thrown away; and
  in what order does the experiment get *run* so that nothing seen early can bend the result.

The first question is the one Musical Mycelium's evolution plan answered, and its answer carries over unchanged:
**build a walking skeleton, thin in depth and correct in shape** (§1). The second question is new. Musical Mycelium
answered questions; this project runs an experiment, and an experiment has an order of operations that a product does
not (§2).

---

## 1. Walking skeleton, not prototype (carried over)

A **prototype** answers a question and is thrown away. A **walking skeleton** performs a tiny end-to-end slice of
real function on the real architecture: every component present and connected, each doing the least interesting
version of its job. It grows by thickening in place. Musical Mycelium was built this way from v0.1 to v1.1 without a
rewrite.

*Patched 2026-10-04 (his; Phase 1 decision 2):* the scenario, the five objectives and the menu below are all
**placeholders off the experiment's subject** (no company, workers or owners; no contrast of who counts or of time
horizon), with the same shape as the real ones. A placeholder scenario alone would still run the real objectives
on the official model and show which way they push (§2).

For Horizon Compact, the skeleton is: **one scenario, five objectives, a handful of runs, launched as a Fargate task,
calling Bedrock through the real provider interface, writing provenance-stamped results to S3, aggregated by the real
scorer, shown on one page of the real site through the real CloudFront and Vercel path.** Every later phase adds
content (scenarios, wordings, repeats, models, cases) or surface (views), not structure.

---

## 2. The experiment's own order of operations (new)

**The rule:** nobody, including the author, sees the official model's decisions on a pre-registered scenario before
the pre-registration is committed (`04` §1.2). That one rule decides most of the phase order, because three things a
normal build would do early all count as looking:

| Something a build normally does early | Why it counts as looking | How the plan handles it |
|---|---|---|
| A walking skeleton that runs the real scenario | It shows which way the objectives push, before anything is fixed | **The skeleton runs a placeholder scenario** that is not one of the four and never becomes one (§4, Phase 1). *Patched 2026-10-04:* its objectives and menu are placeholders too, off the subject entirely (§1) |
| Development runs of every wording on cheap or local models (`00` §5.5) | Different models, but they show a direction, and wording edits made after seeing it are the forking paths `04` §1.2 warns about | **Allowed, with a written rule:** after a development run, a wording or scenario may change only to fix a format, clarity or neutrality failure, and every change is logged with its reason. The pre-registration says plainly that development runs on other models were seen (Phase 2). *Patched 2026-10-04:* the loop is **built blind to outcomes**: format from status counts, clarity from comprehension questions with answer keys, neutrality from the checklist and a blind reader; nobody reads allocations by objective. A scenario where every objective lands the same way is a result, never a reason to change numbers (Phase 2.5, decisions 1-2) |
| A pilot to measure noise and set the number of repeats (`04` §1.5) | It is a run of the real scenarios on the official model | **The pre-registration comes before the pilot.** It states the rule that turns the pilot's measured spread into a repeat count, and pilot runs are excluded from the results (Phase 4) |

**Why this matters more than any infrastructure choice:** a late infrastructure mistake costs a week. A peek before
the protocol is fixed costs the result's credibility, and that cannot be fixed afterwards, because nobody can unsee a
result. Everything else in this plan is a two-way door; this is the one that only opens one way.

---

## 3. One-way and two-way doors

### 3.1 One-way doors: right from the first commit

| Decision | Why it locks | What "right" means from the start |
|---|---|---|
| **Pre-registration before any official run** (§2) | A result seen before the protocol is fixed cannot be unseen | The protocol commit is a phase gate (Phase 3); the harness refuses to run an official sweep unless the protocol hash in its config matches a committed protocol. *Patched 2026-10-04 (his):* the tag freezes the content, the protocol **and the analysis code** (verdicts, intervals, matching); a change to any of them after the tag is a new protocol version. Run code may be fixed, each fix logged with its effect (Phase 3.5 decision 1) |
| **Provenance on every model call** (`02` §2.2) | A result without its model, prompt hash and seed cannot be defended or re-run; retrofitting means re-running everything | Recorded from the first skeleton call, including the placeholder runs |
| **Raw responses kept, write-once** (`02` §2.8) | If only parsed numbers are kept, a scoring bug found later means paying for every run again | The raw response is stored next to the parsed decision; results are never overwritten |
| **Official and development results kept apart** (`02` §2.2) | A laptop or local-model run mixed into the official set is Musical Mycelium's false-finding lesson | Official = container run, identified by image digest, under a committed protocol. Everything else is labeled development and stored under a different prefix |
| **One way to capture a decision across all models** (`04` §1.8) | Two capture methods add a difference between models that is not about the models | One tool, `auto` choice, an explicit instruction and identical validation for every model, from the first provider (corrected 2026-10-03 from forced tool use, which Sonnet 5.5 rejects; `07` §2) |
| **Experiment content as versioned data, hashed** (`02` §2.1) | Prompts edited in code drift silently between runs | Scenarios, objectives, wordings, lever menu and dossier live in versioned files; every run records their hash |
| **The public/private boundary** (`04` §2.6) | A company name pushed to a public repo is public for good | `.gitignore` for `methods-appendix/`, the local pre-commit name hook and the CI tracked-path check in the first commit; the repo is public from that commit (his decision, `09` §6) |
| **Everything in Terraform, the shared OIDC provider looked up** (`04` §3.5) | Console-made resources and a second OIDC provider break teardown and the other project's deploys | Terraform from the first resource; the provider is a data source, never a resource |
| **The model set for v1 fixed before real cases are accepted** (`04` §2.3) | Adding a model with a later cutoff after cases are accepted can disqualify them | Named in the pre-registration |

**Nine.** Musical Mycelium also had nine. That list is short on purpose; everything not on it is cheap to change.

### 3.2 Two-way doors: decide late, change freely

| Decision | Why it stays cheap |
|---|---|
| Which models run, and how many | A config value behind the provider interface (§4.1); a new model is a new sweep, never a code change |
| Repeats, number of wordings, which cells get thinking | Sweep parameters; set by the pre-registration's rules, not by code |
| Number of scenarios and company types | Data files; the harness does not know how many exist |
| Whether real-case dossiers are built by the retrieval pipeline or by hand | Both produce the same frozen dossier format (§4.4); the CEOs cannot tell |
| Charting library and visual design | The site reads static JSON (§4.3); it can be rebuilt without touching the experiment |
| DuckDB versus anything else for aggregation | Raw results are plain JSON in S3, one object per run (`02` §2.8); any reader works |
| Step Functions, more parallelism | Orchestration sits outside the harness; one task per model is enough at v1's quota (`04` §3.1) |
| A live "write your own objective" mode | A new endpoint beside a static site; the precomputed explorer does not change |

---

## 4. The seams

Four interfaces carry the structure. Each exists in the skeleton with the simplest possible implementation behind it.

### 4.1 The provider interface (harness to any model)

```python
class Provider(Protocol):
    name: str                       # "bedrock", "ollama"
    def decide(self, request: DecisionRequest) -> RawDecision: ...

@dataclass
class RawDecision:
    raw_response: dict              # exactly what came back, kept forever
    tool_input: dict | None         # the tool call's arguments, unvalidated; None if the model did not call it
    usage: Usage                    # input, output, cache-read, cache-write tokens
    provenance: Provenance          # model_id, inference_profile, region, effort, temperature, started_at
```

Adding Nova Pro, Sonnet 5.5 or a local model is a new implementation or a config line, never a change to the sweep
loop. Validation (pydantic, `02` §2.1) happens after this seam, in one place for every model, so every model is held
to the same rules.

### 4.2 The experiment definition (data to runs)

A sweep is fully described by committed files plus a seed: scenarios, objectives and wordings, the lever menu with its
meaning per scenario (`04` §1.4), the dossier, run counts, and the protocol hash. The harness expands that into a list
of run specifications, each with a deterministic `run_id`. Runs are idempotent: a `run_id` that already has a result
is skipped, so an interrupted sweep resumes rather than restarts. That works because each run's result is its own
write-once object (`02` §2.8, corrected 2026-10-03).

### 4.3 Results to the site (the static data contract)

```
S3 raw JSON, per run (write-once) ──> scorer (pure function, deterministic) ──> static JSON (versioned schema) ──> site
```

The scorer is a pure function of raw results, so a scoring change re-scores everything for free. The site reads only
the static JSON, whose schema is versioned, so the site and the experiment can each change without breaking the other.
The same contract is what makes the "official versus development" split visible to readers: development results never
reach the published JSON.

### 4.4 The frozen dossier (build-time tools to the experiment)

Every company the CEOs see, fictional or real, arrives as one **frozen dossier**: a fixed template per case type
(`04` §2.1), its source list with accession numbers, and a content hash recorded on every run. How it was produced
(the retrieval-and-rerank pipeline, `02` §2.7, or by hand) is invisible downstream. That is what makes the pipeline
safe to cut from v1 if it runs long (`04` §6.1) and safe to add back for the frequency study.

---

## 5. The phases to v1.0

**Each phase follows Musical Mycelium's convention:** a short scope doc, then an IMPLEMENTATION doc written and
approved before any code, then a plain-English write-up of what the phase did, written during the phase, not after.
Phase scope docs are written when the repo is created; this table is their outline. Costs are from `03` §4 and are
estimates until Phase 4 measures them.

| Phase | Version | Delivers | Done when | Est. cost |
|---|---|---|---|---|
| **0. Scaffold and guardrails** | v0.0 | Repo (public from the first commit), `CLAUDE.md` (`00` §10), planning docs copied in **without** `methods-appendix/`, `.gitignore`, the local pre-commit name hook and the CI tracked-path check (`04` §2.6), Terraform bootstrap (OIDC looked up), Horizon Compact's filtered budgets (`04` §3.3), one tool call (`auto` choice, `07` §2) to Sonnet 4.6 and Nova Pro from the laptop, Ollama reachability confirmed, **the development model named** (`09` A1), the Phase 0 checks in `09` §5 | CI green; a recorded, provenance-stamped call from each Bedrock model; a commit containing a made-up canary name is refused by the hook, and a tracked file under `methods-appendix/` fails CI | under $1 |
| **1. Walking skeleton** | v0.1 | The whole path from §1 on a **placeholder scenario**: Fargate task, rate limiter, Bedrock, S3, scorer, one page live at `horizon-compact.vercel.app` | A container-run sweep's results are visible on the public URL, each traceable to its image digest; `terraform destroy` and re-apply tested | about $1 |
| **2. The experiment's content** | v0.2 | The cited fictional-company dossier (`01` §2), the four scenarios with each lever's meaning per scenario (`04` §1.4), objectives with about three wordings each, the neutrality review (`04` §1.6); development runs on local and cheap models for format and clarity only, every change logged | Every number in the dossier has a source or is marked as an assumption; every scenario passes the neutrality checklist; development runs parse cleanly under all five objectives | about $5-10, mostly development |
| **3. Pre-registration and scoring** | v0.3 | The protocol committed and tagged (`prereg-v1`): content hashes, comparisons and thresholds, the repeat rule, refusal and retry handling, the descriptive analyses, the real-case selection rule, the v1 model set (`07`). Scoring and aggregation code written and tested **on synthetic results only**, including the verdict-rule simulation and the matcher calibration that sets its no-match threshold (`09` A5) | Tag exists; the harness refuses an official sweep whose protocol hash does not match it; the scorer passes its tests on synthetic data; the simulation's power and false-split rates are recorded in the protocol | $0 |
| **4. The official grid** | v0.4 | Pilot (excluded from results) sets repeats by the committed rule; then the full grid on Sonnet 4.6, then on Nova Pro; robustness checks (wordings, shuffled order); first measured cost replaces `03`'s estimates | The full grid has run under the protocol on at least Sonnet 4.6, with spread, refusal rates and run counts recorded; the $60 re-plan point checked (`04` §3.4) | about $20-30 |
| **5. Real cases** | v0.5 | Case selection by the pre-registered mechanical rule (`07` §10.0; model set already fixed), every candidate logged, dossiers (pipeline or by hand, §4.4), the foreshadowing check (`04` §2.1), headcounts scaled with dollars (`01` §4.6), the recognition probe, each case's rubric committed before it runs with its observed and excluded dimensions, the runs, the "most closely matched" view | At least three cases run and matched, including the invest or retool case; every rubric's commit predates its case's first run; the selection log is complete | about $20-25 |
| **6. The explorer and methods page** | v0.6 | The full site from `00` §6: scenario picker, five CEOs side by side, memo reader, real cases by type (coarse descriptions, `04` §2.5), the fixed place for results against the thesis, the methods page | A hostile reader could re-run the experiment from the published inputs, including the anonymized dossiers, using the methods page alone (reconstructing cases from their sources is not possible, and the page says so); each public case description fails to identify its company in a search; every published real-case memo has passed the company-name scan (`07` §12) | under $2 |
| **7. Write-up and launch** | v1.0 | README and launch post (his prose; `00` §10), the plain-English write-up, a definition-of-done audit against `00` §8 | Every DoD item checked with evidence; the audit is published in the repo, with partial passes marked as partial | $0 |

**Total, about $50-70** (`07` §13, written later the same day, puts the worst case at about $71)**,** inside the $80 ceiling and consistent with `03` §4's no-thinking column. The $60 re-plan
point most likely arrives during Phase 5.

**Why real cases come after the official grid, not before:** the harness is proven on the fictional company first, so
a real-case problem is a case problem rather than a harness problem; and every week of waiting adds post-cutoff
decisions to the candidate pool (`04` §2.3). The model set, which sets the case window, is already fixed in Phase 3.

**Why the explorer is mostly built late:** a page exists from Phase 1, so the deploy path is never untested. The full
explorer waits for real data because views designed around imagined results get redesigned.

### 5.1 If v1 runs long: the cut list (from `04` §6.1)

In this order, each cut stated on the methods page:

1. **The second model family** (Nova Pro). The result becomes "on one model," which is weaker but honest.
2. **Wording variants on the official model** (they still run on cheap models; the official model runs the
   **sealed** wording only, repeats are recomputed for one wording, and the wording-robustness claim is dropped and
   said so on the methods page; `08` §5).
3. **The fifth real case**, then **the fourth**.
4. **The retrieval-and-rerank pipeline**, replaced by hand-built dossiers in the same frozen format (§4.4). Moves to
   the frequency study, where it is needed.

**Never cut:** the pre-registration, the baseline objective (E), the published results against the thesis, at least
three real cases including one invest or retool case, and provenance.

### 5.2 If Sonnet 5.5 access arrives

- **Before the Phase 3 commit:** choosing the main model is reopened, as his decision. Sonnet 5.5 is about a third
  cheaper (`03` §2.1) and newer; Sonnet 4.6 is already proven on the account.
- **After the Phase 3 commit:** v1 stays on the models it pre-registered. Sonnet 5.5 runs as its **own complete
  sweep** under the same protocol, reported beside v1, never merged (`04` §1.9). Its June 2026 cutoff fits the real
  cases, because the case window was already set to the strictest cutoff (`04` §2.3).

---

## 6. After v1.0

**Every phase after v1.0 needs its own budget.** The $80 ceiling covers v1 only, and the rest of the shared credits
belong to Musical Mycelium and contingencies (`03` §7). Each later phase gets a cost check and a spending decision
from him before its scope doc is written; credits expire 2027-07-30, and anything beyond them is billed to the card.

Each later phase reuses the v1 protocol where it can and writes a **new pre-registration** for anything it adds.

| Phase | What it adds | Which seam absorbs it | Order |
|---|---|---|---|
| **More company types** (software, healthcare, others) | New dossiers, scenarios adapted per type | Experiment definition (§4.2), frozen dossier (§4.4) | **Committed: first after v1.0** (his decision, `00` §6.1) |
| **Sonnet 5.5 sweep** | The same grid on a newer model | Provider config (§4.1) | Whenever access arrives (§5.2) |
| **Horizon sweep** | Objective D at 10, 20 and 50 years | New objective variants (§4.2) | Second: small and cheap |
| **Small-model contestant** | A small open model as a sixth CEO, on Bedrock or local (`02` §2.6) | Provider (§4.1) | Third |
| **Memo analysis** | A secondary, labeled LLM-judge pass over the memos (`02` §2.8) | A new scorer over kept raw responses (§4.3) | Fourth |
| **"Write your own objective"** | A live mode, rate-limited and budget-capped (`00` §6) | A new endpoint beside the static site; **the first always-on component**, so it needs its own risk pass | Fifth |
| **The frequency study** | Money flows from XBRL financial statements across hundreds of companies (`00` §6.1, `01` §4.3) | Dossier pipeline (§4.4); likely Step Functions; possibly Bedrock batch for volume (`03` §5) | Sixth: the largest |
| **Fine-tuned or distilled CEO** | A small trained model against a frontier one | Provider (§4.1) | Hopeful: after a cost check (`00` §9 check 6) |

---

## 7. What is honestly still at risk of rework

- **Lever meanings per scenario** (`04` §1.4). If Phase 2 finds that one menu cannot mean the same thing in all four
  scenarios, the decision schema changes. That is why the schema is versioned, raw responses are kept, and Phase 2
  finishes before the protocol is committed. It is the one item worth being slow about.
- **First contact with ECS, Fargate and hand-written IAM.** The plan is right; the first permissions error will still
  take an afternoon. Phase 1 is small so that the afternoon is spent on a skeleton.
- **Nova Pro and the tool call.** If its rate of failed tool calls is high, that is published as a finding
  (`04` §1.7), but it may also push it down the cut list.
- **Whether Budgets can filter on per-model billing lines** (`04` §3.3), found in Phase 0.
- **Prompt and dossier wording.** Continuous churn in Phase 2 by nature, and frozen in Phase 3 by design.

**The aim is bounded rework, not none.** A skeleton whose bones are right can have any amount of muscle rearranged.
What it cannot have is a result that was seen before its protocol was written, which is why §2 exists.

---

## 8. Decisions for him

**All five decided 2026-10-03, his, as recommended:**
1. **The skeleton runs a placeholder scenario, not one of the four** (§2, Phase 1), so every real result stays
   unseen until the protocol is committed.
2. **The pre-registration comes before the pilot;** pilot runs set the repeat count by a committed rule and are
   excluded from results (§2, Phases 3-4). `07` specifies the rule.
3. **Development runs on other models are allowed, with the change-log rule** (§2).
4. **The order after v1.0** (§6): company types first (already committed), then horizon sweep, small-model
   contestant, memo analysis, live mode, frequency study; the Sonnet 5.5 sweep whenever access arrives. Each
   phase still needs its own budget decision first.
5. **How Sonnet 5.5 enters** (§5.2): the main-model choice reopens if access arrives before the Phase 3 commit;
   after it, a separate sweep.

**Still his:** nothing open in this plan.

## 9. Bottom line

- Build a **walking skeleton**: thin in depth, correct in shape. Musical Mycelium's rule, unchanged.
- **Nine one-way doors** (§3.1). The new one, and the one that matters most, is the **order of operations**:
  nothing official is seen before the protocol is committed (§2).
- **Four seams** (§4): the provider interface, the experiment definition, results to the site, and the frozen
  dossier.
- **Eight phases to v1.0** (§5), about $50-70, with a cut list that never touches the pre-registration, the baseline
  or the results against the thesis.
- **Everything after v1.0** lands in a seam that already exists, and each phase brings its own budget.
