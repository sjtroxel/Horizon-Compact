# Known gaps

Open items, newest first. **This file narrows the phase docs:** if it and an older phase doc disagree, this file
governs until the phase doc is amended. Closed items stay, marked closed with the date, so the record shows how
they closed.

**Never write a real company's name in this file, or in anything else under version control.** Refer to a real
case by its type and a neutral label. The names live only in the private longlist outside this repo.

> ## START HERE — where things stand, 2026-10-04, 7 PM (main-model line amended 2026-10-05)
>
> **PHASE 0 is complete** (2026-10-03; CI run `37160410815`). **Every scope doc, Phases 0 through 7, is approved.**
> **PHASE 0.5 `aws-foundation` is BUILT and its smoke calls are done; it is NOT closed.** Three commits on `main`, all
> pushed, CI green: `b9c9aaf` (bootstrap Terraform, identity check, the settings deny fix), `52aa3fd` (provider seam,
> smoke command), `ac2fbe0` (eight smoke records and findings). The bootstrap is applied with nothing shared created;
> the deploy role's trust is proven (run `37241137274`); Sonnet 4.6 (thinking off and on), Nova Pro, Nova Lite and
> gpt-oss-120b each made a recorded tool call. The development model is named (his): **Ollama `qwen3.5:4b` + Nova
> Lite.** The as-built record is `docs/phases/phase-0.5-aws-foundation-IMPLEMENTATION.md` §15 and §19.
>
> **What keeps it open is billing data, which AWS posts up to about a day late** (the entry just below): the tag
> measurement for decision 3, the Sonnet 4.6 budget (its Service name appears in the Budgets list only once Sonnet's
> charges post), and the phase's spend read from the bill. That close-out is about 15 minutes of his console and one
> `terraform apply`, then the DoD audit; it runs **as soon as the data posts** (evening of 2026-10-05 at the earliest),
> alongside Phase 1's build.
>
> **Phase 1's IMPLEMENTATION doc is APPROVED (his, 2026-10-04 evening):**
> `docs/phases/phase-1-walking-skeleton-IMPLEMENTATION.md`, its four decisions as recommended (ECR in `bootstrap`; keep
> the dev key through Phase 1; deploy on push for code paths; 15 runs). **BUILD STARTED 2026-10-05 (Sonnet): steps 0-2
> done, C1 committed (`70a4c4e`). BEDROCK IS BLOCKED (entry below): steps 3 and 9 wait for AWS; NEXT: steps 4-8, which
> call no model (IMPLEMENTATION doc §16, §21).** Drafted with it and untracked: `experiment/`
> (`models.toml` and the garden-club placeholder). Decision 3 enters it as two branches (§9.3). Its build can start
> before Phase 0.5 closes; **its first Sonnet sweep cannot** (§1).
>
> **The `horizon-compact-dev` access key stays through Phase 1** (decision A, amended 2026-10-04 by Phase 1's
> decision 2); he deletes it at Phase 1's close. **Sonnet 4.6 is the main model for v1, fixed (his, 2026-10-05).** Sonnet 5.5 is no longer awaited;
> its two smoke calls will not run (the closed Sonnet 5.5 entry below).
>
> **Owed by him:** claim `horizon-compact.vercel.app` (entry below). A prerequisite for Phase 1.5.

---

## BLOCKED — every Bedrock call throttled, quotas reset to 0, 2026-10-05

**What happened.** On 2026-10-05 every Bedrock call on the account returns `ThrottlingException`, HTTP 429, "Too many
tokens per day, please wait before trying again": Nova Lite (the step 3 development run, 28 attempts, $0) and Sonnet 4.6
(smoke call 10, recorded as `10-sonnet46-stop-details.json`, an `api_error`). Service Quotas shows **0 applied** for
Sonnet 4.6 cross-region requests and tokens per minute and for Nova Lite, including Nova Lite's tokens per day; on
2026-10-03 Sonnet 4.6 read 10 requests a minute applied. Every call worked on 2026-10-04 (22:54-23:02 UTC).

**Likely cause, unconfirmed by AWS.** AWS answered the Sonnet 5.5 Global case at 05:31 UTC on 2026-10-05 after
"reaching out to the service team" (new models need several billing cycles of usage and spend). The quotas went to 0
between that review and the morning. The same message on new or low-spend accounts is widely reported, and the
reported fix is a support case asking AWS to restore the default quotas. **It is account-wide**, so Musical Mycelium's
Bedrock calls (Haiku 4.5, Nova Pro) are probably failing too; unchecked.

**Action taken.** Account-and-billing case **179121856900232**, opened 2026-10-05 11:42 CDT (Service Quotas, General;
web), asking for the default quotas back and naming the two request ids. Nothing is spent to qualify (no cash; credits
only). Not tried yet: whether US West (Oregon) has non-zero applied quotas (limits are per region); using it would be a
design change and his decision.

**What it blocks.** Phase 1 steps 3 (the development run) and 9 (the skeleton sweep), and Phase 0.5's tag measurement
only if it needs a new call (it does not: it reads the 2026-10-04 bill). **What it does not block:** steps 4-8 (container,
`bootstrap` additions, `main`, deploy, permission check), which call no model.

**If AWS says no** (discussed 2026-10-05, nothing decided): ask again or escalate; another region; a free local open
model (Ollama `qwen3.5:4b`) as the subject, a smaller but real version of the experiment; another cloud's new-account
credits, if they cover the models (unverified). Each is his decision.

**The harness change it caused** (IMPLEMENTATION doc §21, item 10): a daily-quota throttle now stops the session at once
(`quota_exhausted`), and ten `api_error`s in a row stop it (`api_errors`), instead of retrying silently until the
30-minute clock ends.

---

## WAITING — Phase 0.5 close-out, on billing data, 2026-10-04

The smoke calls ran 17:54-18:01 CDT on 2026-10-04; `Project` was activated as a cost allocation tag at 17:19 CDT.
Cost Explorer and Budgets post usage up to about a day late, so these wait until **the evening of 2026-10-05 at the
earliest; the morning of 2026-10-06 is safer.** All reads are in the console (free; the Cost Explorer API charges).

1. **The tag measurement (decision 3).** Cost Explorer, 2026-10-04, daily, credits excluded (Charge type: exclude
   Credit), filter Tag `Project` = `horizon-compact`, group by Service, then by Usage type. **(c) holds only if both a
   Sonnet 4.6 row and a Nova Pro row appear under the tag**, from smoke calls 1, 2 and 4. A day with no rows waits one
   more day; if still none, try the page's **Backfill tags** before calling it a no. Then he decides (c) or (a).
2. **The Sonnet-line budget (DoD 3).** Budgets console, Create budget, Customize, Cost, Budget scope, filter
   Service: copy the exact Sonnet 4.6 string (Haiku's reads `Claude Haiku 4.5 ( Bedrock Edition)`, with that space).
   Abandon the form. Add `sonnet_service_name = "<string>"` to the untracked `terraform.tfvars`; plan (Claude reads
   it: one budget, CUSTOM period, $80, ACTUAL at 40/60/75, credits excluded), apply, plan again for "No changes". If
   (c) was taken, the tag budget is added in the same apply. **If the apply refuses `CUSTOM`**, the fallback is
   `ANNUALLY` from 2026-10-01 (§6 of the IMPLEMENTATION doc).
3. **The phase's spend (DoD 8).** Cost Explorer, 2026-10-04 to the day of the read, credits excluded, grouped by usage
   type, every line this phase touched (Sonnet 4.6, Nova Pro, Nova Lite, gpt-oss, S3). Estimates sum to $0.019;
   must be under $1. Also whether the errored Nova Pro call (record 05) was charged.
4. Then: the DoD audit (§16, provisional table in §20), version 0.0.5, `ROADMAP.md`. The dev access key is **not**
   deleted here; it is kept through Phase 1 (decision A, amended).

---

## CARRIED — from Phase 0.5 to Phase 1, 2026-10-04

Found by the smoke calls (`docs/phases/phase-0.5-aws-foundation-IMPLEMENTATION.md` §19); each lands in Phase 1's
IMPLEMENTATION doc.
- **`ModelErrorException` is `malformed_tool_use`, a model outcome**, not `api_error` (`planning/07` §5.1, patched
  2026-10-04). The classifier and its tests must say so, with the error's HTTP status and request ID recorded.
- **Text beside one tool call is not `no_tool_call`** (`planning/07` §5.1, patched). Nova's `<thinking>` text tag is
  visible text, not a thinking setting.
- **Thinking tokens are inside `outputTokens`** (`planning/07` §7.3, patched); Phase 4's sub-study reads them that way.
- **The refusal `stop_details` question** (refusals entry below) is still unchecked; it needs
  `additionalModelResponseFieldPaths`, which is Phase 1's request shape.
- **The tool-use input overhead** (a few hundred tokens per call, `planning/03` §3.1 patched) belongs in Phase 1's
  price-and-cap arithmetic, and whether the cache point covers it is checked there.
- **The deploy role gets its permissions in Phase 1**, with a permissions boundary; the identity workflow is the
  pattern for its first run.
- **Model routes:** both the tagged application profile and the `us.` geo profile behave identically for Sonnet 4.6;
  which one the task role is granted is decision 3's outcome.

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
| Whether AWS Budgets can filter on this project's per-model billing lines; whether added budgets cost money; whether application inference profiles could tag spend **PARTLY CLOSED 2026-10-04**, below; the tag half waits for a measurement. *Update 2026-10-04 evening:* the tagged profiles exist, `Project` is active (17:19 CDT), and calls 1, 2 and 4 went through them; the reading waits for billing data (WAITING entry above). Found: the Budgets Service list offers only services already billed | `planning/04` §3.3 |
| ~~Converse: one tool with `auto` choice on Sonnet 4.6; how thinking settings are passed and recorded~~ **CLOSED 2026-10-04** by smoke calls 1, 3 and 4 (IMPLEMENTATION doc §19; `planning/07` §14.1 and §7.3 patched) | `planning/07` §14.1 |
| ~~Nova Pro: default temperature, availability, knowledge cutoff~~ **CLOSED 2026-10-04**: the documented values below, and availability by smoke calls 2 and 5.2 (one `ModelErrorException` in three calls, recorded) | `planning/07` §14.2, `planning/01` §7.5 |
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

## CLOSED 2026-10-05 — Sonnet 5.5 access (was WAITING, 2026-10-03)

**Decided 2026-10-05 (his)**: **Sonnet 4.6 is the main model for v1, fixed. Sonnet 5.5 is no longer awaited.** AWS answered
the Global quota case on 2026-10-05: the newest models, Sonnet 5.5 among them, are held until an account has
several billing cycles of Bedrock usage and spend, with automatic re-evaluation or a new request after the next
cycle. The US case (179097554500679) asks for the same model and is expected to get the same answer. The
main-model slot is closed, no phase plans around Sonnet 5.5, and nothing is spent to qualify for it. If access
ever arrives, using it is a new decision of his, not something the plan assumes. Patched the same day:
`planning/02`, `03`, `04`, `05`, `07` and `09` (status lines), `ROADMAP.md` §2, §4 and §5, and the scope docs for
Phases 0.5, 1, 1.5, 2, 2.5, 3.5, 4 and 7. The Phase 0.5 smoke code keeps its two inert Sonnet 5.5 entries
(built and tested; never run).

*The entry as it stood before closing:*

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
