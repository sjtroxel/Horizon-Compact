# Known gaps

Open items, newest first. **This file narrows the phase docs:** if it and an older phase doc disagree, this file
governs until the phase doc is amended. Closed items stay, marked closed with the date, so the record shows how
they closed.

**Never write a real company's name in this file, or in anything else under version control.** Refer to a real
case by its type and a neutral label. The names live only in the private longlist outside this repo.

> ## START HERE — where things stand, 2026-10-04, noon
>
> **PHASE 0 `scaffold-and-guardrails` IS COMPLETE.** Four commits on `main`, all pushed: `f214280` (planning,
> pushed before the guard existed, since confirmed clean by the guard), `9c382b8` (the name guard, hooks,
> toolchain, CI), `f45770b` (roadmap, known gaps, Phase 0 docs), `4405412` (`CLAUDE.md`, the guard explainer,
> the planning README with his disclosure line). **CI run `37160410815`: green on the first push.** The DoD
> audit, with its one caveat: `docs/phases/phase-0-scaffold-and-guardrails-IMPLEMENTATION.md` §11a.
>
> **The name guard is live** on every commit, message and push in this clone (61 terms, 11 allowed phrases,
> fingerprint matching). The private term file is committed in job-search-headquarters (`ca8f316`). **A fresh
> clone needs `make setup`** before anything is committed; `make check` fails until it is run.
>
> **NEXT: the scope docs for Phases 0.5 through 7, written one at a time, in order, before any further
> implementation** (his convention; Phase 0 was the one exception). **2026-10-04: Phase 0.5's scope doc is
> APPROVED** (`docs/phases/phase-0.5-aws-foundation.md`), all eight decisions as recommended. **Phase 1
> `walking-skeleton` is APPROVED and split** (his, 2026-10-04): Phase 1 (`docs/phases/phase-1-walking-skeleton.md`,
> the run path) and Phase 1.5 (`docs/phases/phase-1.5-publish-path.md`, the scorer, the page, the teardown test).
> **Phase 2 is APPROVED and split** (his, 2026-10-04): `docs/phases/phase-2-company-dossier.md` and
> `docs/phases/phase-2.5-scenarios-and-wordings.md`, all eleven decisions as recommended. **Phase 3 is APPROVED and
> split** (his, 2026-10-04): `docs/phases/phase-3-scoring-and-simulation.md` and
> `docs/phases/phase-3.5-preregistration.md`, all eight decisions as recommended. **Phase 4 `official-grid` is
> APPROVED, not split** (his, 2026-10-04): `docs/phases/phase-4-official-grid.md`, all six decisions as recommended;
> `planning/04` §3.4 and `planning/07` §11 patched. **Phase 5 is APPROVED and split** (his, 2026-10-04):
> `docs/phases/phase-5-case-building.md` and `docs/phases/phase-5.5-case-runs.md`, all six decisions as recommended;
> the Phase 3.5 scope doc amended (the protocol freezes the real-case rules, the gate gains a case mode, the search
> date is set by rule); `planning/01`, `02`, `04`, `05` and `07` patched. **Phase 6 is APPROVED and split** (his,
> 2026-10-04): `docs/phases/phase-6-explorer.md` and `docs/phases/phase-6.5-methods-and-release.md`, all six
> decisions as recommended, decision 6 amended by him; `planning/02`, `05` and `06` patched. **Next: the Phase 7
> `writeup-and-launch` scope doc**, kept deliberately open (his). **Phase 7 is APPROVED, not split** (his,
> 2026-10-04): `docs/phases/phase-7-writeup-and-launch.md`, all six decisions as recommended, written to be re-scoped
> when the phase starts. **Every scope doc, Phases 0 through 7, is written and approved.** The four proposed
> `planning/07` patches are made (his approval, 2026-10-04). A later scope doc that rests on a Phase 0.5 check not yet measured
> says so in a line, so the amendments are easy to find if the check comes back different. Phase 0.5's
> IMPLEMENTATION doc is written immediately before it is built.
>
> **2026-10-04 morning: the Phase 0.5 pre-build checks were run** before Phase 4 (his call). Closed: Ollama,
> Musical Mycelium's billing lines, Claude's default temperature, refusals through Converse (documented, not
> observed). Partly closed: Budgets and profiles (the tag test is in the build, placed early for its 24-48 hour
> wait), Nova Pro (availability waits for its smoke call). Open until the build: the Sonnet 4.6 smoke calls. Details
> in "OPEN — Phase 0.5 checks" below. The four `planning/07` patches proposed from them are made.
> **2026-10-04, 5 PM: Phase 0.5's IMPLEMENTATION doc is APPROVED** (his),
> `docs/phases/phase-0.5-aws-foundation-IMPLEMENTATION.md`, its decisions A-D as recommended. The dev IAM policy
> (`infra/iam/horizon-compact-dev-policy.json`) was drafted with it and is untracked until the build's C1.
> **Next: the build, with Sonnet, from that doc's §15, starting at step 0** (he reads which identity `default` is,
> and whether Sonnet 5.5 access has arrived). Found while writing it and **already fixed** (in C0): the deny rules
> did not cover `terraform -chdir=... apply` or `plan` (§3 finding 1), and `*.tfvars` was not gitignored (finding 2).
>
> **Owed by him:** claim `horizon-compact.vercel.app` (entry below). No rush now; it is a prerequisite for Phase
> 1.5.

---

## REMINDER — hosting before the credits expire, set 2026-10-04 (Phase 7 decision 5)

**Act by 2027-06-30.** The AWS credits expire **2027-07-30** (`planning/03` §1); after that, anything AWS still
bills is charged in cash, and the project's budget rule is that it never is. From launch, the idle monthly bill is
measured. By 2027-06-30, either the static site moves to a free static host and the published record stays in the
public repo, with AWS hosting torn down and the raw results archived where they cost nothing; or he decides, before
the date, to keep AWS hosting on a stated cash budget. Free hosts and their terms are checked live at the time.
Musical Mycelium shares the same credits and the same date. **Owner:** Phase 7 records the plan; he decides.

---

## FINDING — Nova Pro's billing line is shared with Musical Mycelium, 2026-10-04

Found while scoping Phase 0.5, by reading Musical Mycelium's code (read-only). It uses `amazon.nova-pro-v1:0` as
its **eval judge** (its `DEFAULT_JUDGE_MODEL_ID`; judge result files from 2026-08-20 to 2026-09-10), and Haiku 4.5
for its agent. `planning/04` §3.3 and `planning/02` §2.12 assumed Musical Mycelium spends only on Haiku 4.5, so a
budget filtered to Sonnet 4.6 and Nova Pro would measure Horizon Compact alone. **For Nova Pro it would not.** The
error is small (one 30-item judge run was estimated at about $0.10 in Musical Mycelium's own records) but not zero.

**What this check is not:** it read code, not the bill. A grep of one repo's source is not proof of what was billed.
The billing check (Cost Explorer by usage type) is in Phase 0.5's checks.

**What it changes:** how this project's budgets treat Nova Pro is Phase 0.5 decision 3. It also narrows
`planning/09` A1: the development model can be neither Haiku 4.5 nor Nova Pro. `planning/04` §3.3 gets a dated
patch once decision 3 is made.

**Also found while scoping, recorded in the scope doc:** this repo's OIDC subject claim is the immutable form
(GitHub API, 2026-10-04); Ollama is installed on the Windows side, and whether WSL can reach it is still unchecked.

---

## FINDING — the first commit went public before the name guard, and it is clean, 2026-10-03

`f214280` ("first commit new project", 15:56 CDT) holds `.gitignore` and the 12 files of `docs/planning/` (13
files in all; `docs/planning/README.md` was not in it, and was added later in `4405412`), and was pushed to
`github.com/sjtroxel/Horizon-Compact` (public, confirmed through the GitHub API). `planning/09` §7
put the guard in the first commit, before anything was copied in. That order was not followed.

**The push was his, deliberate.** Another session scanned the same 12 planning files against the longlist
**before** he committed and found nothing (his account, 2026-10-03; that scan's method is not recorded here).

**Checked again the same afternoon, after the push:** every company name, ticker and plant location on the private
longlist was searched for, whole-word and ignoring case, across every file in `f214280` and in its message.
**No reference to any case or candidate.** One longlist term matches 9 times, each one inside a cloud product
name the project uses. No path under `methods-appendix/` is tracked.

**What this check is not:** it was a one-off search over a term list typed by hand from the longlist, run before
the guard or its term file existed. **It is not the guard.** Phase 0 DoD 2 has the guard scan the full history,
`f214280` included, once it is installed. That scan is the check that counts.

**CLOSED 2026-10-03, by the guard itself.** After C1 (`9c382b8`), `make guard-history` scanned both commits with
the real term file (61 terms, 11 allowed phrases, fingerprint matching): **"history clean, 2 commit(s)
scanned."** `f214280` is confirmed clean by the check that counts.

**What it changes:** the scope doc's "first commit" becomes "the guard commit," and the planning commit becomes
a scan of the history that already exists. No rewrite of history is needed or recommended. Rewriting a public
commit that holds nothing private would add risk and protect nothing.

---

## CLOSED — the private longlist is prose, not a term list, 2026-10-03

**Closed the same day by Phase 0 decisions 1-4 (his):** a separate private term file with a longlist
fingerprint, whole-word case-sensitive matching with per-term flags and allowed phrases, and names, tickers and
plant locations all counted. Built and live; the record below is kept as the finding that led there.

Found while scoping Phase 0's name hook. The longlist was written for a person: candidates appear in table cells,
in comma-separated lists inside sentences, with tickers, plant locations and SIC codes beside them. Three
consequences:

1. **A hook that pulls names out of the longlist automatically will miss some.** Any parser of free-form prose
   has gaps, and a gap here is silent. Missing a name is the costly error.
2. **Using every word as written would over-block.** Measured on 2026-10-03: one longlist term already matches
   **9 places in the planning docs**, none of them a reference to a case. Several other longlist names are also
   ordinary English words or short tickers, and would match common words in this project's prose.
3. **Plant locations are as identifying as company names** for a single-plant closure, and the longlist holds
   them. Whether the hook blocks them is a policy decision, not a mechanical one.

**What follows:** the hook needs an explicit term list, kept private next to the longlist, with a stated
matching rule, and a way to notice when the longlist changes and the term list does not. Options and a
recommendation are in the Phase 0 scope doc. **His decision.**

---

## OPEN — Phase 0.5 checks, from `planning/09` §5, 2026-10-03

`planning/09` calls these the Phase 0 checks; they moved to Phase 0.5 with the AWS half (2026-10-03, his).
Each is Claude's, using live sources only. None blocks Phase 0.

| Check | Source |
|---|---|
| ~~Ollama's install location and whether WSL can reach it (7 GB RAM visible in WSL)~~ **CLOSED 2026-10-04**, below | `planning/00` §9.7, `planning/04` §6.3 |
| Whether AWS Budgets can filter on this project's per-model billing lines; whether added budgets cost money; whether application inference profiles could tag spend **PARTLY CLOSED 2026-10-04**, below; the tag half waits for a measurement | `planning/04` §3.3 |
| Converse: one tool with `auto` choice on Sonnet 4.6; how thinking settings are passed and recorded | `planning/07` §14.1 |
| Nova Pro: default temperature, availability, knowledge cutoff **PARTLY CLOSED 2026-10-04**, below; availability on this account waits for its smoke call | `planning/07` §14.2, `planning/01` §7.5 |
| ~~Claude's default temperature value, for the methods page~~ **CLOSED 2026-10-04**, below | `planning/07` §14.3 |
| ~~How a refusal comes back through Converse on Sonnet 4.6~~ **CLOSED 2026-10-04 as documented, not observed**, below | `planning/07` §14.4 |
| ~~Which Bedrock billing lines Musical Mycelium already spends on, before the development model is named (`planning/09` A1)~~ **CLOSED 2026-10-04**, below | `planning/09` A1 |

**CLOSED 2026-10-04 — Musical Mycelium's billing lines.** Read by him in the Cost Explorer console (free; the API
charges per request), 2026-07-01 to 2026-10-04, monthly, credits excluded so the figures are gross:
- **Grouped by service:** "Claude Haiku 4.5 (Bedrock Edition)" $23.68 (Aug $6.05, Sep $17.63); "Bedrock" $0.30
  (Aug $0.22, Sep $0.08); everything else a few cents. **No Sonnet 4.6 row and no other Claude row**, so a budget
  on Sonnet 4.6's line measures this project alone, as `planning/04` §3.3 assumed. Holds for this window only.
- **"Bedrock" grouped by usage type:** `USE1-NovaPro-input-tokens` $0.27, `USE1-NovaPro-output-tokens` $0.03,
  `USE1-NovaMicro-input-tokens` and `-output-tokens` under $0.01 (August only). **Nova Pro is confirmed on the bill**
  (pre-check 1 read it from code). **Nova Micro is new:** the code read did not find it.
- **What it changes:** the A1 development model can be none of Haiku 4.5, Nova Pro or Nova Micro if it is to sit on
  a line of its own. Ollama (`qwen3.5:4b`, Ollama check above) is now a reachable alternative. Decision 3 is
  unchanged: Nova Pro's line is shared, as found.
- **Not taken from this view:** the exact service names for Terraform's budget filters. The console table appears to
  abbreviate them ("Bedrock", "( Bedrock Edition)"); the IMPLEMENTATION doc takes them from the filter's own value
  list.

**CLOSED 2026-10-04 — Ollama.** Measured from WSL by Claude, no AWS call:
- **Reachable.** `http://localhost:11434/api/version` answers from WSL (Ollama 0.35.1, Windows side). No
  `.wslconfig` exists; whatever WSL networking mode makes `localhost` work is the default here, so a WSL update that
  changes it would break this.
- **Fits in 6 GB of VRAM:** `qwen3.5:4b` (Q4_K_M, 3.4 GB on disk), already installed. `qwen3:8b` does not fit
  whole: loaded, it took 6.0 GB with 4.2 GB on the GPU (RTX 4050 Laptop, 6141 MiB), spilled to CPU, and ran 30-60 s
  a call against 6-16 s for `qwen3.5:4b`. `qwen3:14b` was not tried.
- **One tool under `auto`:** Ollama's chat API has no tool-choice setting; the model may answer in text, which is
  the `auto` case. On a throwaway two-option prompt with one tool, both models made exactly one valid call in 5 of
  5 runs. **Five runs on a trivial prompt is enough for format and retry-path testing, which is all `planning/04`
  §6.3 asks of a local model, and is not evidence about longer prompts.**

**PARTLY CLOSED 2026-10-04 — Budgets and application inference profiles.** AWS documentation, read live by Claude;
nothing measured on the account yet.
- **Added budgets cost nothing.** AWS Budgets pricing page: monitoring and notifications are free; only
  action-enabled budgets past the first two ($0.10 a day each) and delivered reports ($0.01 each) cost money. This
  project's budgets are notification-only. **Closed.**
- **Budgets can filter on both billing lines, as documented.** The Sonnet 4.6 model card: it is "offered and billed
  through AWS Marketplace", and its charges appear "under the model provider (not under Amazon Bedrock)"; Budgets'
  Service filter, with Billing entity, "can filter costs by specific AWS Marketplace purchases". Nova Pro is billed
  under Amazon Bedrock and is separated by the Usage type filter. **Documented, not observed:** the exact Service
  name and usage-type strings are read from Cost Explorer in the Musical Mycelium billing check.
- **Application inference profiles: supported for both models, at no extra cost, as documented.** A profile can wrap
  a cross-region profile (`us.anthropic.claude-sonnet-4-6`, which `planning/02` already uses: Sonnet 4.6 has no
  in-region endpoint in any US region) or an in-region model (Nova Pro is in-region in us-east-1, and has no global
  profile). Bedrock's docs: the price is the model's price; tags must be activated as cost allocation tags
  (`user:` prefix in Budgets), and secondary sources put the lag at 24-48 hours.
- **OPEN, the one that decides decision 3: whether a profile's tag lands on Marketplace-billed Claude charges.**
  Bedrock's docs say tags track on-demand invocation costs and do not distinguish Marketplace-billed models; no
  source found, AWS or other (Feb, Apr and Aug 2026 articles read), shows it either way. **It closes only by
  measurement:** the Sonnet 4.6 smoke call made through a tagged profile, the tag activated, then Cost Explorer
  filtered by the tag 24-48 hours later. Until then decision 3's second condition is unmet, and the procedure's
  fallback is (a).

**PARTLY CLOSED 2026-10-04 — Nova Pro.** AWS documentation, read live by Claude:
- **Default temperature 0.7** (valid range 0.00001 to 1), with `topP` 0.9 and `topK` unused by default (Amazon Nova
  user guide, "Complete request schema"). Under decision 7 Nova Pro runs at this default; the value goes into the
  pre-registration and the methods page.
- **Knowledge cutoff Oct 2024; lifecycle Active**, EOL "no sooner than" December 2025 (the card says both Dec 4 and Dec 5), which has passed without a date
  being set (Bedrock model card). In-region in us-east-1, with a `us.` geo profile and no global one.
- **Open until its smoke call:** that it is enabled and answers on this account.
- **Conflicts with `planning/07` §2.1** *(patched 2026-10-04, his approval; was "not yet patched")*: that table said Nova Pro has no thinking. The Nova guide
  documents a `reasoningConfig` for "Amazon Nova Pro and Amazon Nova Lite only", **disabled by default**. Leaving it
  unset keeps it off, so runs are unaffected; the table's cell was wrong. Patch made (below).

**CLOSED 2026-10-04 — Claude's default temperature: 1.0.** Bedrock's Anthropic request page: default 1, range 0 to
1. Anthropic's API reference now marks `temperature` deprecated: "Models released after Claude Opus 4.6 do not
support setting temperature. A value of 1.0 will be accepted for backwards compatibility." Either way the default is
1.0, and `planning/07` §2.3 never sets it, so runs are unaffected.
- **Conflicts with `planning/07` §2.1** *(patched 2026-10-04, his approval; was "not yet patched")*: that table said temperature is "allowed with thinking off"
  on Sonnet 4.6. Sonnet 4.6 launched 2026-02-17, Opus 4.6 on 2026-02-05 (Bedrock model cards), so Anthropic's
  sentence, read literally, covers Sonnet 4.6 too. Whether it does is **unverified**; it does not matter while the
  harness never sets temperature, and the Sonnet 4.6 smoke call does not need to settle it.

**CLOSED 2026-10-04 — refusals through Converse, as documented, not observed** (a refusal is not provoked, by
design):
- **Converse has no `refusal` stop reason.** Its valid values (Converse API reference): `end_turn`, `tool_use`,
  `max_tokens`, `stop_sequence`, `guardrail_intervened`, `content_filtered`, `malformed_model_output`,
  `malformed_tool_use`, `model_context_window_exceeded`.
- **Claude's own response does have one.** Bedrock's Anthropic response page (InvokeModel): `stop_reason: "refusal"`,
  with an optional `stop_details` (category, explanation) that "may be null even on a refusal", and possibly partial
  content.
- **How the one becomes the other, on Converse:** one third-party report (a GitHub issue, 2026-09-24, on Claude Fable
  5.1, citing no AWS source) says Converse returns `content_filtered`. **No AWS source states the mapping, and nothing
  shows it for Sonnet 4.6.**
- **What it means for `planning/07` §5's classifier:** "the API's refusal stop reason" is, on Converse,
  **`content_filtered`, provisionally**. `guardrail_intervened` cannot occur, since no guardrail is configured. The
  written rule for an explicit decline in text still applies alongside it. Any stop reason the harness does not
  expect is already recorded as a failure, not dropped (`planning/07` §5), so a wrong guess shows up as a failure
  rather than vanishing. Whether `additionalModelResponseFieldPaths` can also return `/stop_details` is unchecked,
  and left to the IMPLEMENTATION doc.

**MADE 2026-10-04 (his approval): the four `planning/07` patches below,** dated in `planning/07`'s status line.
*Were proposed as:* §2.1's Nova Pro thinking cell ("none" becomes "a
reasoning setting exists, off by default; never set"); §2.1's Sonnet 4.6 temperature cell (adds "possibly rejected
for non-1.0 values; never set, so moot"); §5's refusal row (names `content_filtered` as the Converse form,
provisionally); §14 items 2-4 marked closed with a pointer here.

---

## OPEN — owed by him, 2026-10-03

- ~~**Create the empty public GitHub repo `Horizon-Compact`**~~ **Done 2026-10-03**, with `f214280` pushed to it.
- ~~**The one-line disclosure in `docs/planning/README.md`**~~ **Done 2026-10-03**, his words, in `4405412`.
- ~~**Commit the private term file in job-search-headquarters**~~ **Done 2026-10-03** (`ca8f316`).
- **Claim `horizon-compact.vercel.app`** as a placeholder (`planning/09` §7 step 7). Unclaimed as of 2026-10-02;
  not re-checked since. *2026-10-04:* now a prerequisite for Phase 1.5.

---

## WAITING — Sonnet 5.5 access, no action, 2026-10-03

Quota requests open (US: AWS Support case 179097554500679; Global: pending). If access arrives **before** the
`prereg-v1` tag, the main-model choice reopens as his decision. After the tag, Sonnet 5.5 is its own sweep
(`planning/05` §5.2).

**Room left for it, 2026-10-04 (his):** the scope docs treat the main model as a slot (Phase 1, "The main model is
a slot"; `ROADMAP.md` §2). Phase 0.5 smoke-tests Sonnet 5.5 if access has arrived, which gives the measured facts
for the decision. Every later scope doc says which of its lines would change if 5.5 became the main model.

---

## RECORDED — later-phase checks, so they are not lost, 2026-10-03

From `planning/09` §5. Not Phase 0's.

- A newer non-Anthropic model than Nova Pro on the account: before the Phase 3 model set is fixed.
- Census AIES and BLS tables; Damodaran's terms of use; whether the SEC Financial Statement Data Sets are
  current: Phase 2, before the dossier.
- Bootstrap, Newcombe intervals and the power rule implemented and tested on synthetic data: Phase 3.
- Measured tokens and cost replacing every estimate in `planning/03`: Phase 4.
- Each real-case candidate's first-disclosure date, public status and recognition: Phase 5.
- Bedrock fine-tuning and custom-model serving costs: before any fine-tuning phase, after v1.
