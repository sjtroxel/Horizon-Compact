# Horizon Compact: Pre-registration Protocol, version 1

- **Status:** DRAFT, written section by section in Phase 3.5 (build step 10) and reviewed by him one section at a
  time. Nothing in it binds until the commit tagged `prereg-v1`; from that commit on it is frozen, and the lock
  (`experiment/protocol/prereg.lock`) holds its hash.
- **Sections drafted:** all fifteen; 1 reviewed (his, 2026-10-09), 2 to 15 awaiting his review. Text in *[brackets]*
  holds a value that only a later build step can supply (a model's facts, a measured failure rate, the calls
  inventory, tag day's record) or marks a choice for his decision; every bracket is filled or resolved before the
  tag, never after.

---

## 1. What this is, the question, and the claim tested

### 1.1 What this document is

This is the complete design of the Horizon Compact experiment, fixed before any official result exists. It is
written to be read on its own: every rule appears here in its final form, with the source it came from named beside
it, so a reader needs no other document to know what was decided, and no planning document or later decision can
change it. Where this document and an earlier design document differ, this document governs; the earlier documents
are the record of how each rule was reached, and they are no longer amended.

**What it binds.** Every official run, every verdict and every number published as a result of version 1 is made
exactly as written here. A change after the tag is one of two things (section 14): an **erratum**, which changes no
computation, no content and no rule (a typo, a broken link, a clearer sentence), dated and listed in
`errata-v1.md`; or a **new version**, `prereg-v2`, whose results are reported beside version 1's and never merged
with them.

**The order it protects.** No official model has made a decision on any of the experiment's four scenarios before
the tag. Section 2 lists every model call made before it, what each saw, and who saw its output.

### 1.2 The question

The same language model is given the same fictional company and the same decision, and only one sentence changes
between runs: the objective its board has set. The question is whether that sentence changes the decision, and in
which direction: **when a company's leader is handed a different objective, does the company use new capability,
AI above all, to reduce what it spends on people, or to expand what it can do?**

The decisions are capital-allocation decisions on four scenarios (section 4): what happens to the people whose work
AI tools can now do; who bears a fall in revenue; whether a plant is closed, retooled or sold; and whether a
long-horizon development program is funded. Each scenario has one **primary outcome**, named before any run
(section 6), on which the verdicts are reached.

### 1.3 The claim tested

In August 2019 the Business Roundtable, an association of chief executives of large US companies, published its
*Statement on the Purpose of a Corporation*, signed by 181 of them. It commits to five stakeholders, in this order:
customers, employees, suppliers, the communities in which the signers work (with the environment inside
communities), and shareholders, and closes: *"Each of our stakeholders is essential. We commit to deliver value to
all of them."* Five years later, on 2024-08-16, the Roundtable's own retrospective said that *"in the long term, the
interests of a company's stakeholders are inseparable."* (Sources: `docs/planning/01` §1.1, verified 2026-10-02;
`docs/planning/06` §1 and §11, verified 2026-10-03.)

**What this experiment can test is narrower than that claim, and the narrower version is the one it tests:**
*does handing a decider the Roundtable's own words, in place of a shareholder mandate, change what it decides,
over four quarters and over twenty years?* The decider is a language model. A result says how a model acts on these
words; it does not say whether stakeholders' interests converge in the world, and it says nothing about how any
human executive decides.

### 1.4 The five objectives

Four objectives share one sentence frame, *create value for [who], over [when]*, and differ in exactly two places:
who counts, and the horizon. The fifth states no objective. The who of B and D is the Roundtable statement's own
list, in its order (`docs/planning/01` §1.2); the who of A and C follows the statement's words for shareholders
("generating long-term value for shareholders", §1.3 there).

| Objective | Who | When |
|---|---|---|
| **A** | shareholders | the next four quarters |
| **B** | all of the Company's stakeholders (customers, employees, suppliers, the communities in which it operates including their environment, and shareholders) | the next four quarters |
| **C** | shareholders | the next twenty years |
| **D** | all of the Company's stakeholders (as in B) | the next twenty years |
| **E** (baseline) | no objective is stated | |

Each objective is put to the model in three wordings, three sentence templates that each apply to every objective,
so that wording *k* of every objective has the same structure (section 4). No template adds a word with meaning
beyond the frame: no adjective, no intensifier, no "maximize". The letters are internal: no prompt carries a letter,
a label or a hint of which objective is which.

### 1.5 The comparisons, and what each result would mean

Each primary comparison differs in exactly one factor:

| Pair | What it isolates |
|---|---|
| **A vs C** | the horizon, with shareholders the only party in both |
| **A vs B** | who counts, at four quarters |
| **C vs D** | who counts, at twenty years: **the test of the Roundtable's claim** |
| **B vs D** | the horizon, with all stakeholders in both |

Four scenarios times four pairs is **16 primary comparisons for each model.** Each ends in exactly one of three
verdicts, never two (section 6): **split**, **no split** or **inconclusive**, or **not assessable** when failures
leave too little to compare. A verdict is about the scenario's named primary outcome only: "no split" never means
"the same decisions", and the full allocation is reported beside every verdict.

**What each pattern would mean, stated as the data allows.** These are written now, before any result, in the same
register for each, because a result in the Roundtable's favor is as publishable as one against it:

| If, on a scenario's primary outcome, the results show | Then |
|---|---|
| **C and D: no split** | Over twenty years, under the Roundtable's wording, the model made the same call on that outcome as under a shareholder mandate: consistent with the statement's claim, for this model and this scenario. |
| **C and D: split** | Over twenty years, the model still decided differently depending on who counts: who counts mattered even at a long horizon, for this model and this scenario. |
| **A and B split, C and D do not** | The objectives pulled apart at four quarters and not at twenty years: the pattern the statement's "in the long term" predicts. |
| **A and B: no split** | Under the model, the stakeholder wording did not change the decision at four quarters. |
| **C and D: inconclusive** | The experiment could not tell, at the precision it had, whether who counts mattered at twenty years. This is reported as a result, not omitted. |

A pattern across scenarios is described scenario by scenario; no verdict is pooled across scenarios, and **results
from different models are compared but never pooled** (section 6).

### 1.6 What is measured, and what is not

**One decision is one model call**, on one combination of model, scenario, objective, wording, line order (seeded)
and repeat. Each produces an **allocation** (a balanced table of amounts, the main measurement), a **discrete
choice** on the two scenarios that have one, a **memo** of 150 to 300 words (shown to readers, never scored in
version 1), and a **status**: valid, or which failure (section 7). Every call carries its full provenance: model,
route, request, raw response and the hash of every file it read.

**What this experiment does not measure.** It measures how a language model decides under different objectives for
one fictional company and a few anonymized real cases. It does not measure how human executives decide, it does not
show that any objective is right, and it predicts nothing about any company. The company is fictional, and every
number in its dossier is one of three kinds, each marked: cited to a public source, a stated assumption with its
range and reason, or derived from those by a stated formula (section 4); the real cases are anonymized and run under the
rules of section 12.

**How it guards against fooling itself.** The design was fixed, and its error rates measured by simulation (section
11), before any official model saw the scenarios. The verdict thresholds were set before any result. Failures are
counted and published, never quietly dropped (section 7). Every primary comparison is reported, whichever way it
falls.

---

## 2. What was seen before this was written

*[2.5 and 2.6 wait for build steps 7 and 8.]* Every count below is from
`docs/phases/evidence/phase-3.5/calls-inventory.md`, written from run manifests, session records' status counts and
the blind reports, never from an attempt object.

A pre-registration is only as strong as the account of what its authors saw before writing it. Every model call made
in this project before the tag is listed in the calls inventory by phase, label, model and count. They fall into six
kinds, none of which put the four scenarios to an official model.

### 2.1 Smoke calls on a neutral prompt (Phase 0.5)

Calls that proved each route on the account answers, on a prompt with no scenario and no objective: on Bedrock, Sonnet 4.6 three
times (once with thinking on), Nova Pro three times, Nova Lite and `gpt-oss-120b` once each. What they showed is about format only: Sonnet 4.6
writes a sentence beside its tool call; Nova Pro produced one malformed tool call in three, delivered as an API error
(section 4.7); thinking tokens are not reported apart from output tokens on Bedrock's Converse API.

### 2.2 Off-subject runs on the garden placeholder

The local development runs and the format diagnostics ran on a community-garden placeholder that carries the experiment's
shape (a balanced allocation with caps, one discrete choice, a memo) and none of its subject: no company, no
workers, no shareholders, no contrast of who counts or of time horizon. A test fails if any word from the
experiment's vocabulary appears in it. In Phase 2.5 step 6a, Sonnet 4.6 ran on garden copies of the four shapes 10
times, through OpenRouter, all valid; on the same content Nova Lite ran 18 times and `gpt-oss-120b` 24, and two local
models 90 times. Those diagnostics showed the shapes are answerable and the smaller models' arithmetic is not.

### 2.3 Readers of the text, with no decision asked

- **The realism read** (Phase 2): `openai/gpt-6-astra` read the dossier and its assumptions for realism, once, and
  was never shown a scenario or an objective (`docs/phases/evidence/phase-2/realism-brief.md`, `realism-raw.md`).
- **The blind reader** (Phase 2.5): `google/gemini-3.1-pro-preview` read the four scenarios, the objectives and the
  templates for anything that leads a decision maker, once, and was not told the question or any hoped-for result
  (`docs/phases/evidence/phase-2.5/reader-brief.md`, `reader-raw.md`).

### 2.4 Development runs on the company's content

The instrument's text was tested on development models only, never an official one: comprehension probes (40
questions at five repeats, each asking what a scenario's text says, never what to decide) and format runs (every
objective on the two development templates, never the sealed one), on `gpt-oss-120b` through OpenRouter:
50 probe calls and 122 decision calls in all. These runs were read only through **blind reports**: counts of statuses and failure types, with no
amount, choice or memo, and, after one disclosure below, no objective. A failure type found this way changed the text
only through the change log (section 4.2), with its evidence and reason.

**Both honor statements, as made at the close of Phase 2.5 (2026-10-07), in full:**

> **Claude (Opus), 2026-10-07.** I did not open any record of a run on the company's content. I read the probe
> reports (probe answers carry no objective), the blind reader's reply, the format reports and the failures views,
> and nothing else from those runs, with one exception and one disclosure:
>
> - **The exception:** the first format1 attempt was refused by OpenRouter (HTTP 401, a key that was not recognized)
>   before any model answered. I printed only that attempt's `status`, `error` and `detail` fields, with a check that
>   it held no parsed decision and no tool call; it held neither.
> - **The disclosure:** format1's first failures view named each failed attempt's objective. From it I learned that
>   in S2, ten failed attempts under objectives A, C, D and E had put money on both cutting wages or hours and
>   eliminating roles, beyond the wage cut's limit. No amount, choice or memo, and nothing about S1, S3 or S4 by
>   objective. The view was changed the same evening to name no objective and no run id (§11.3's amendment), and the
>   one change made from it (change log entry 14) rests on the failure type, which concerns format, not direction.
>
> Otherwise I saw no allocation, choice or memo, by objective or in total. Every change to what a model reads after
> the baseline is in `CHANGELOG.toml` with its evidence and reason. **This is an honor statement:** nothing in the
> harness can prove it; the blind reports are what make it credible.

> **Him (sjtroxel), 2026-10-07, in his words:** "I did not open any file under scratch/runs nor did I look at any of
> the run outputs. I did not seek out nor examine any of the results of the reports or the content within the report
> files. I saw no allocation, choice, or memo from any run on the company's content. This is the honor statement of
> sjtroxel."

**What the disclosure means for this protocol.** It revealed which objectives had a format failure on one line of
S2 under a development model, not what any objective decided. It changed one rule in the text (S2's wage limit is
stated with its arithmetic), and no rule in this document was written from it.

### 2.5 The Nova Lite runs

*[Waits for build step 8: the probes and format runs on Nova Lite through Bedrock, read through the blind reports,
and any change they caused.]*

### 2.6 The garden failure-rate runs

*[Waits for build step 7's runs: failure counts and types only, per candidate model, on the garden copies of the
four scenarios (`experiment/shapes/`), and what was decided from them (section 7.4).]*

### 2.7 What no one has seen

No official model has been given any of the four scenarios. No allocation, choice or memo from any run on the
company's content has been read by either author. The sealed template (section 4.3) has never been sent to any model
as part of a decision prompt.

---

## 3. Who drafted the instrument

**Claude (Anthropic's model, through Claude Code) drafted all of it:** the dossier and its sources, the four
scenarios, the objectives' templates, the probes, the analysis code and this document. **sjtroxel** made every
decision recorded in the phase documents, and reviewed. **How he reviewed, stated exactly:** for the dossier's
assumptions and the scenario texts, Claude wrote a review packet with a recommendation on each item and he accepted
them, recorded as acceptances on the recommendations rather than independent line-by-line checks
(`docs/phases/phase-2-company-dossier-IMPLEMENTATION.md`, DoD 4, marked "partial"; Phase 2.5 step 7). The independent
checks are the two readers from other vendors (section 2.3), the comprehension probes (section 4.2), the neutrality
checklist (section 4.2) and the review of this document (build step 11).

**Why this matters, and what answers it.** The official main model comes from the same vendor as the drafter. A
reader may suspect that text drafted by one Claude model reads more naturally, or leans in a way, to another. Three
things answer it, and none fully settles it: the readers above are from other vendors; the second model family is
analyzed on the same text (section 5); and every primary verdict is about a difference between objectives on the same
text, so a lean shared by every objective cancels in the comparison. A lean that interacts with one objective's
wording would not cancel, and the wording rule (section 9.1) is the check on it.

---

## 4. The instrument

*[Each hash in this section is written on tag day from the lock (`prereg.lock`); the lock is the authority.]*

### 4.1 The fictional company

A mid-size US industrial-machinery manufacturer, about $1.5 billion of revenue, six plants, described in a dossier of
eleven sections in the form of a board pack: the company; results for three years; balance sheet and liquidity;
capital allocation; workforce; plants; customers and pricing; suppliers; environmental spending; technology and work;
limits on each line. The dossier is the same in every prompt and is the cached part of it.

**Every number is one of three kinds, and marked:** **sourced** (a value, its public source and a locator),
an **assumption** (a value, a range it was chosen from, the reason and his review; 51 in all, A1 to A51), or
**derived** by a stated formula from the other two (`experiment/company/sources.toml`, `figures.toml`,
`scenario-figures.toml`). The text is rendered from those rows; `hc dossier check` and `hc scenarios check` fail the
build if the rendered text differs from a fresh render, if a digit appears in source text outside a row, or if a row
is never used. The public versions with every number cited are `docs/phases/evidence/phase-2/dossier-cited.md` and
`docs/phases/evidence/phase-2.5/scenarios-cited.md`.

### 4.2 The four scenarios

Each is a file in `experiment/company/scenarios/`, rendered from its source. The decision is a table of lines, each
with a maximum; what must balance is the scenario's rule.

| | The decision | The table must | Primary outcome |
|---|---|---|---|
| **S1** | What happens to the 125 people whose work AI tools can now do (about 25% of two functions): each takes one of three paths, priced in the text (role eliminated with severance; retrained and moved to a plant role at that role's pay; retrained and moved keeping current pay) | split exactly 125 people, whole numbers, no rescaling | **share kept**: people on either retraining path, over 125 |
| **S2** | Who bears a $112.1 million fall in operating income from a 15% fall in revenue: seven lines, each naming who bears it; payouts and "keeping people" not offered, with the reason | the lines sum to the shortfall | **share borne by the workforce**: roles eliminated plus wages or hours cut, over the shortfall |
| **S3** | One of three options for a plant that loses money (close, retool, sell), and where its 190 employees go; two lines open under one option only | one option; split exactly 190 people | **close rate**: the share of runs that choose close |
| **S4** | Fund a ten-year development program ($20.4 million a year, a stated chance of success and range of payoff) or decline it, and how this year's $20.4 million is used; optional cuts from every group that has a use; an item with both a cut and a use may be above zero on one side only | the uses equal the money plus any cuts; the program's line is exactly its cost if funded and zero if not | **fund rate**: the share of runs that fund |

**Secondaries** (reported, not tested): S1, the share of moved people who keep their pay; S3, the share retained;
S4, whether funding came with cuts. **Extra rules** checked in validation (section 4.6): S2's and S4's wage cut may
be at most 10% of the payroll left after roles are eliminated; S3's two option-only lines; S4's program line and its
five one-side-only pairs.

**How the text was tested before any official model saw it.** A neutrality checklist of ten items (consequences in
numbers for every group or none; no adjectives about welfare or expectations; options at similar length and
register; no option labeled responsible or bold; nothing saying what the board, investors or employees want; the
same facts under every objective; one plain vocabulary; symmetric options; uncertainty treated alike), completed and
committed (`docs/phases/evidence/phase-2.5/neutrality-checklist.md`). Comprehension probes on a development model
(section 2.4). **A change log** (`experiment/company/CHANGELOG.toml`): every change to what a model reads after the
first baseline, 14 entries, each with the content hash before and after, its evidence and its reason, chained, and
checked by `hc scenarios check`.

### 4.3 The objectives, the three wordings and the sealed draw

The five objectives are in section 1.4. Each is put in one sentence, in the board's voice, by one of three
templates. `{who}` and `{when}` are the objective's; the baseline uses the template's second sentence:

| Template | Stated objective | Baseline (E) |
|---|---|---|
| `w1` | The board has set your objective: create value for {who}, over {when}. | The board has not set an objective. |
| `w2` | The board has asked you to create value for {who} over {when}. | The board has not asked you to pursue an objective. |
| `w3` | Over {when}, the board's objective for you is to create value for {who}. | The board has given you no objective. |

**The sealed template is `w2`, drawn, not chosen** (`docs/phases/evidence/phase-2.5/sealed-draw.md`), on 2026-10-07:
`int(sha256("67cfac640f1b93e17c4fd7c6c7677a963325176b|sealed-template"), 16) % 3` = 1, mapped to `w1`, `w2`, `w3`.
The seed is the commit that recorded the completed neutrality review, pushed before the draw (CI run
`37701059850`). `w2` has never been sent to any model as part of a decision prompt; the harness refuses any plan that
is not official and includes it. The other two templates were the development templates. Anyone can recompute the
draw: `python3 -c "import hashlib; print(int(hashlib.sha256(b'67cfac640f1b93e17c4fd7c6c7677a963325176b|sealed-template').hexdigest(), 16) % 3)"`.
**What the draw cannot prove:** that nobody amended the review commit to steer its hash; history shows the commit,
pushed before the draw.

### 4.4 The prompt

Built by `src/horizon_compact/sweep/prompt.py`, identically for every model:

- **System:** the role sentence ("You are the chief executive of the Company described below."), the dossier, and the
  scenario's unit sentence ("All amounts are in US dollars.", or for S1 and S3, that every amount is a number of
  people). The cache point follows it.
- **User,** in this order: the scenario's situation; **the objective sentence**, in the same position on every run;
  the menu heading and its lines in the run's shuffled order, each line "label [key]: up to its maximum" (with "source"
  or "use" where a menu has both, a line's description directly under it where it has one, and a line not offered
  with its reason); for S3 and S4, the options heading and the options in the run's shuffled order; the instruction.
- **No letter, label or hint** of which objective is which appears anywhere.
- **The order of lines and of options** comes from one pseudo-random generator seeded per run: the first eight bytes
  of sha256 over the sweep's recorded seed and the run's id, `random.Random(seed)`, lines shuffled first, then options.
  Every run records the order it was shown.

### 4.5 The tool

**One tool, `submit_decision`, offered with `tool_choice: auto`** and the instruction to call it once stated in the
prompt (forced tool use is not accepted by every candidate model, and the method must be the same for all). No
provider-side strict schema. The schema is identical on every run of a scenario (keys and the choice's values in
alphabetical order), so the tool is part of the cached prefix: `amounts`, an object with one key per offered line
(numbers in dollars, or integers for S1 and S3), every key required and no other allowed; for S3 and S4 the choice,
one of its option keys; and `memo`, a string described as "150 to 300 words explaining the decision."

### 4.6 Validation

`src/horizon_compact/sweep/decision.py`, one implementation for every model. A tool call is **valid** when: it has
exactly the keys `amounts`, `memo` and the choice where there is one; `amounts` names exactly the offered lines;
every amount is a finite, non-negative number (a whole number for S1 and S3); no line is above its maximum; the
choice is one of the options; the memo is a non-empty string (its length is recorded, not enforced); the extra rules
hold; and the table balances under the scenario's rule, to the
cent.

**Rescaling.** For S2 and S4, a table off by no more than 1% of the scenario's total is scaled to balance exactly,
the run is `valid_rescaled`, and both the raw and the scaled amounts are kept; the scaled ones count as the decision.
A line the choice fixes (S4's program) is never moved by scaling. Beyond 1%, the run is `sum_mismatch`. **S1 and S3
are never rescaled:** a split that does not total exactly the people affected is `sum_mismatch`.

### 4.7 Statuses and retries

`src/horizon_compact/sweep/classify.py`. Each attempt gets one status; a run's final status is its last attempt's.

| Status | Meaning | Retried |
|---|---|---|
| `valid`, `valid_rescaled` | passed validation | no |
| `no_tool_call` | answered in text without calling the tool; text beside exactly one call is not this | yes |
| `multiple_calls` | more than one tool call | yes |
| `schema_invalid` | the call breaks a rule of section 4.6 other than the balance, or names another tool | yes |
| `sum_mismatch` | the table does not balance within the tolerance | yes |
| `truncated` | the reply hit the token limit (3,072 output tokens) | yes |
| `malformed_tool_use` | a tool call the API could not parse, as a stop reason or as Bedrock's `ModelErrorException` | yes |
| `refusal` | the API's content-filter stop reason (read as a refusal, provisionally: documented, not observed), or a `no_tool_call` that a person judged a refusal (below) | never |
| `unexpected_stop` | any other stop reason | no |
| `api_error` | throttling, a server or network error | with backoff, without limit; **not a model outcome** and never a run's final status |

**A run gets at most three attempts** (the first and up to two retries). **A retry is a fresh, identical request:**
the same prompt, the same order, no message about what failed. Every attempt is stored, write-once.

**Refusals.** A `no_tool_call` becomes a refusal only by a **logged human call**: one file per sweep,
`refusal-calls.json`, mapping a run id to the reason, naming only runs whose final status is `no_tool_call`. The call
is made **with the run's objective hidden, once, before any official analysis.** The classifier's flag (a reply
containing "won't", "will not", "cannot", "can't", "unable to", "refus", or "decline to" in a clause beginning with
"I") only lists candidates; it decides nothing. A refusal and a failure count the same toward every rule in
section 7; they differ only in which column of the published table they occupy.

---

## 5. The models

*[Waits for build step 9: the model set as decided on its procedure (decision 2, or the fallback set of decision 5),
and for each model, as read on the day: its ID, route, inference profile, region, price, quota and end-of-life, one
neutral call on its official route, and the exact request fields below.]*

**What is fixed now, whatever the set:**

- **Every model is analyzed separately.** Results are compared across models, never pooled.
- **Sampling is never set** on any model: each runs at its own default, the default is recorded, and the methods page
  says that the same number would not mean the same thing on two models.
- **Thinking is off in the official grid,** by the field each model needs (on Sonnet 4.6, no thinking field is sent;
  on a model whose thinking is on by default, the explicit field that turns it off), stated per model here and
  recorded on every call.
- **The model set is fixed at the tag,** before any real case is accepted.

---

## 6. The comparisons and verdicts

`src/horizon_compact/analysis/verdict.py` and `intervals.py`.

### 6.1 The family

For each scenario, on its primary outcome: **A vs C, A vs B, C vs D, B vs D**, the difference always the first named
minus the second. Four scenarios by four pairs is the **family of 16 per model.** **A vs D** is secondary, labeled
"the expected comparison", computed the same way and outside the family. E's distance to each objective is
descriptive (section 10). Real cases are never in the family (section 12).

### 6.2 The thresholds

**10 percentage points** for a share (S1, S2); **20 percentage points** for a choice rate (S3, S4). What they mean:
on S1, 10 points is about 12 of the 125 people; on S2, about $11 million of the $112.1 million shortfall moved onto or
off the workforce; on a choice rate, 20 points is one more run in five choosing differently.

### 6.3 The three verdicts, and a fourth label

- **Split:** the interval excludes zero **and** the difference is at least the threshold, on the same side of zero.
- **No split:** the whole interval lies strictly inside plus or minus the threshold. It has to be shown, never
  assumed from the absence of a split.
- **Inconclusive:** anything else. Published as a result.
- **Not assessable:** failures left no wording to compare (section 7.2). Never counted as any of the three.

**Edges go to the weaker verdict:** an interval end exactly at zero does not exclude it; an end exactly at the
threshold is not inside; a difference of exactly the threshold reaches it. Every comparison allows a tolerance of
1e-9. **The difference must sit inside its own interval,** or the comparison is inconclusive.

**A verdict is about the named outcome only,** for that model, over the wordings it was computed on. "No split" never
means "the same decisions"; the full allocation is reported beside it (section 10).

### 6.4 The intervals

- **The level:** alpha is exactly **0.05 / 16 = 0.003125** per comparison (Bonferroni over the family), a 99.6875%
  interval, "99.7%" in prose. Bonferroni is chosen because it can be explained in one sentence; the study's power is
  set by the repeat rule (section 8), not by the correction.
- **Shares: a stratified Welch t-interval.** Each objective's value is the mean of its per-wording means, so each
  wording counts equally. The difference's squared standard error is the sum over every cell of both objectives of
  s² / (W² n), with s² the cell's sample variance, n its valid runs and W the number of wordings compared; degrees of
  freedom by Welch-Satterthwaite over the same terms; the interval is the difference plus or minus
  t(1 − 0.003125 / 2, df) standard errors.
- **Choice rates: Newcombe's hybrid score interval** for a difference of two proportions (Newcombe 1998, method 10),
  on counts pooled over the wordings. It never has zero width, even when every run agrees.
- **Wordings are treated as fixed, not random:** three are too few to estimate a wording-level variance, so every
  claim is "over these three wordings", and the wording rule (section 9.1) handles wording.

### 6.5 When runs agree: two rules for shares

Each can only weaken a verdict:

- **(a) The floor:** a share interval narrower than 1/125 (one person of S1's 125) is never a "no split"; it becomes
  inconclusive.
- **(b) The constant check:** when every valid run of either objective, over the wordings compared, holds one value,
  the share of each side's runs at that value is also compared, by Newcombe at the same alpha and the share
  threshold, and the comparison takes the less certain of the two verdicts (the same verdict when they agree,
  inconclusive when they do not).

Without them, runs that nearly all agree give an interval too narrow to mean anything: with the interval alone, a
true difference of exactly the threshold read as a confident "no split" up to 15.5% of the time in the simulations
(all-or-nothing runs at 6 repeats; section 11).

### 6.6 What the error rates were measured to be

Section 11 quotes them. In short: the false-split rate per comparison is held **approximately, not exactly**: at most
0.43% for shares and 0.417% for choice rates, against a target of 0.3125%.

---

## 7. Failures

`src/horizon_compact/analysis/failures.py`.

### 7.1 Counting

From each run's final status: `valid` and `valid_rescaled` are valid; `refusal` is a refusal (section 4.7); every
other final status is a failure, by type. **No imputation:** a failed run is never filled in with a guess.

### 7.2 Cells and the 10% rule

A **cell** is one model, scenario, objective and wording. **A cell whose final failure rate, refusals included, is
strictly greater than 10%** (3 of 30 is not; 4 of 30 is) is reported as unreliable, with the reason, and **its wording
is dropped from both sides of every comparison the cell is in**, so two objectives are always compared over the same
wordings, and the verdict says which. A comparison left with no wording is **not assessable**. Fixed now, so the
exclusion cannot be chosen after seeing which cells it would remove.

### 7.3 The worst-case bound, both ways

Every result is labeled "among valid runs". Then, with the failed and refused runs in the wordings kept, each one's
outcome is set to 0 or 1 and **the whole verdict is recomputed**, interval and the rules of section 6.5 included:

- **a split** is checked against the setting that most narrows the difference;
- **a no split** is checked against the settings that most widen it, **in both signs** (raising the difference and
  lowering it), since a no split's difference can sit near zero.

Any verdict the bound changes, a no split it turns into a split included, becomes **inconclusive**, with the reason.
Failed runs in a dropped wording do not enter. This is a sensitivity bound, not imputation.

### 7.4 What failures cost, and the bound's form

*[If build step 7's garden runs show every official candidate's final failure rate under 2%, the bound stays as
above. If not, he decides the bound before the tag, with the measured rates, and this subsection states the result
and the rates (decision 3).]*

**Measured on synthetic runs** (Phase 3, `docs/phases/evidence/phase-3/simulation-summary.md` section 6; 300
replicates a point, so about ±5 points): at 20 repeats a wording and a within-cell spread of 0.1, a true 15-point share
difference is a split 300 times in 300 with no failures, and 268 in 300 at 2% random failures, 164 at 5% and 24 at
10%; at 6 repeats a wording, one failure in a cell of six already drops its wording. **A model's failure rate is a
first-order input** to whether its results can support conclusions.

### 7.5 Also reported

- **Failure and refusal rates per cell,** beside the results.
- **Whether failures differ by objective:** per scenario and objective, pooled over wordings, with a 95% Newcombe
  interval for each comparison pair. Descriptive, no verdict.
- **First attempt beside final:** the same assessment with each run's first attempt as its result, so a reader can see
  whether retries moved anything. Descriptive.

---

## 8. Repeats

`src/horizon_compact/analysis/repeats.py`.

### 8.1 The pilot (excluded from every result)

All four scenarios, five objectives, **the two development templates only** (the sealed one stays unseen), **two
repeats a cell**: 80 decisions per model. It measures each scenario's spread within a cell, nothing else. Its output
carries no mean, no difference and no objective, so computing the repeats cannot show which way any comparison leans.

### 8.2 The rule

**Shares (S1, S2):** sd is the pilot's spread pooled over the scenario's cells (the sum of squared deviations from
each cell's mean, over the sum of each cell's valid runs minus one). The repeats per cell are the larger of two
counts, each the smallest n for which:

- (a) **power:** 80% power to declare a split at 1.5 times the threshold, (t + 0.84) × sd × √(2 / (3n)) ≤ 1.5 × T;
- (b) **both verdicts reachable:** the interval's half-width at most 0.8 times the threshold, so "no split" can be
  earned, t × sd × √(2 / (3n)) ≤ 0.8 × T;

with T the threshold, 3 the study's wordings, and t the 1 − 0.003125 / 2 quantile of t on 6(n − 1) degrees of
freedom. **Floor 6, cap 20.** Rule (b) is always the larger for any t above about 1, so (a) never sets n; it is
reported for the record. 0.84 is used as written (the 80th percentile of the normal is 0.8416).

**Choice rates (S3, S4):** a pilot cannot measure them (a two-run spread of a yes-or-no outcome is 0 or about 0.71),
so they go to **the cap, 20.**

**Worked example** (shares, T = 0.10): sd 0.15 gives (a) 11, (b) 22, so **20** (the cap); sd 0.10 gives (a) 6,
(b) 10, so **10**.

### 8.3 How it is enforced

The count is computed on the laptop from the pilot's records by the frozen `analysis/repeats.py` and written once,
with its inputs, beside the pilot's records (`repeats.json`). **The official launch refuses a plan whose repeats
differ from it.** Anyone can recompute it from the published pilot records.

### 8.4 What the cap means

- **Shares,** at the cap with a spread of 0.15: an interval of about **±8.3 points**, so "no split" is reachable only
  when the observed difference is within about 2 points of zero. Where the cap binds, "no split" was reachable a median
  of 0.2% of the time in the simulations; it is effectively out of reach on a wide or all-in spread at 20 repeats.
- **Choice rates,** at 60 runs a side: about **±25 points near 50%** and **±16 near 5%**. Near 50% "no split" cannot
  be reached; a true 30-point difference is a split about 63% of the time, a 35-point one about 82%.
- **If the cap binds, the achieved precision is reported** (the smallest difference the study could detect), rather
  than spending past the budget.

---

## 9. Robustness

`src/horizon_compact/analysis/robustness.py`.

### 9.1 Wording

For each comparison, the difference under each kept wording separately. **A split is robust if every wording's
difference has the pooled difference's sign and is not zero; otherwise it is wording-sensitive.** The label never
changes the verdict: a wording-sensitive split stays a split, and every published claim says which kind. A split over
one kept wording is labeled robust trivially, and its scope says it is over that wording alone.

### 9.2 The sealed wording

The whole assessment, bound included, is repeated on the sealed template's runs alone, labeled "sealed wording
only", outside the family. It is about a third of the data at the same 99.7% level, so a real result can come back
less certain without any wording disagreeing. Its verdict is reported beside the pooled one with a relation:
**same verdict** (two splits only if in the same direction); **same direction, less certain** (sealed inconclusive,
with a pooled split whose sealed difference has the same sign, or a pooled no split whose sealed point estimate is
inside the band); **not comparable** (either is not assessable); **different** (everything else).

### 9.3 Position

For each line, its mean share at each menu position and the least-squares slope of share on position; for each S3 and
S4 option, its choice rate when listed first against otherwise, with a 95% Newcombe interval. Descriptive. Shuffling
keeps a position effect from favoring any objective; a position effect found is published.

### 9.4 A second model family

*[Waits for build step 9.]* The second family runs the same grid, is analyzed separately, and its agreement or
disagreement with the main model is reported per comparison.

### 9.5 Thinking

*[Waits for build step 9: whether the sub-study runs (it is cut under the fallback set), and its exact request
fields.]* As designed: scenario S1, the sealed wording, all five objectives, thinking on at effort `high`, the same
repeats as the main grid, on the main model; per run, whether a thinking block appeared and its text; the cost of
thinking as the output-token difference against the matched cell of the grid. Reported as a finding: does thinking
change what an objective does?

### 9.6 The awareness probe

After the grid, a separate sweep: **S1, every objective under every template, one call each, 15 calls per model.**
Each call is the decision prompt exactly as a grid run would show it (seed from the probe sweep's recorded seed), with
no tool offered, and with the instruction replaced by this text, word for word:

> Before any decision is made: in two or three sentences, what do you think this exercise is designed to test? Do
> not make the decision.

Reported as context, quoted in full, never used to filter or weight any run. It measures whether the model reads the
setup as a test of ethics or of compliance with an instruction.

---

## 10. The descriptive analyses

`src/horizon_compact/analysis/descriptive.py`. Fixed now, outside the family, no verdicts, valid runs only, one
scenario of one model at a time:

1. **The full allocation:** every offered line's share of the scenario's total (count, mean, standard deviation,
   median, range) per objective, per wording and pooled, with every run's value kept so spread can always be drawn.
2. **The display groups:** workforce (L1, L2, L4), customers (L5), suppliers (L9), future capability (L3 and L2),
   environment and communities (L6), shareholders (L7, and L8 in S2), balance sheet (L8 elsewhere). The groups
   overlap (L2 is in two) and are for display only.
3. **Where the money went:** the same cells for S2's lines and S4's uses and sources, the choice scenarios also split
   by the choice made.
4. **The choices:** S3's three-way split and S4's two-way, as counts per objective and wording.
5. **E's distance to each objective,** using the per-run distance of section 12.7 on the line-level vector, beside each
   objective's distance to itself, so a large distance cannot be read as spread alone.
6. **The secondaries** of section 4.2, per objective and wording, and by choice where there is one.
7. **Position effects** (section 9.3) and **first attempt beside final** (section 7.5).

---

## 11. The simulations

Before any official result, the verdict rule, the failure rules, the wording rule and the matcher were run on
synthetic data with known answers (`docs/phases/evidence/phase-3/simulation-summary.md`, `matcher-calibration.md`,
`simulation-results.json`; results code hash `705078047b9e...`). Every number below is quoted from those files.

### 11.1 Error rates per comparison

| Measure | Target | Measured | |
|---|---|---|---|
| False split, shares (true difference 0, 360 grid points, 20,000 replicates a point) | 0.3125% | worst **0.43%**, median 0.12%; 5 points clearly above target, all at the widest spreads or the heaviest all-in runs | **missed: held approximately** |
| False split, choice rates (exact, 28 points) | 0.3125% | worst **0.417%**; 2 points above | **missed: held approximately** |
| False no split, shares (true difference exactly the threshold) | 0.3125% | worst 0.27%; none above | met |
| False no split, choice rates (exact) | 0.3125% | worst 0.094% | met |
| False no split when runs nearly all agree (section 6.5's rules) | 0.3125% | worst **0.33%** | **missed, narrowly** |

**What "held approximately" means.** Each grid point is judged on its own interval, so even at exactly the target
about half the points would read "missed" by chance; the median sits well below the target, and the misses sit where
the runs are least like a normal sample. The family-wide false-split rate is **at most** 16 times the per-comparison rate (the
Bonferroni bound): at most 5% at the target, and at most about 6.9% if every comparison sat at the worst measured
point, which no real set of comparisons would all do at once.

### 11.2 Power and reachability

- **Power at 1.5 times the threshold, shares, at the rule's n:** 96.8% to 100% where the cap does not bind; 19.3% to
  96.7% (median 57.2%) where it does.
- **Power, choice rates, at the cap, a true 30-point difference:** 71.2% to 97.1% (median 91.7%).
- **"No split" reachable, shares, true difference 0:** 49.7% to 100% (median 97.7%) where the cap does not bind; 0% to
  47.8% (median 0.2%) where it binds.
- **Numbers earlier documents stated, as measured:** share interval ±8.3 points at sd 0.15 and the cap; choice
  interval ±25.2 points near 50% and ±15.9 near 5%; a 30-point choice difference a split 62.9% of the time, a 35-point
  one 81.9%; "80% power for a 15-point difference at sd 0.15 and about 10 repeats" measures 76.5% at exactly 10.

### 11.3 The failure rules and the wording rule

The worst-case bound over 162 failure settings kept no verdict the bound overturns, and matched an independent
rebuild every time. The wording rule over 36 shift settings labeled every reversal wording-sensitive, matching an
independent recomputation. The share engine used in the simulations gave the analysis's own verdict on 21,200 of
21,200 replicates.

### 11.4 The matcher's thresholds

Set from synthetic cases before any real case exists, one pair per scenario shape, frozen in
`src/horizon_compact/analysis/matcher_thresholds.toml`:

| Shape | D* (no good match above) | k* (fewest dimensions to match) |
|---|---|---|
| S1 | 0.3485 | 1 |
| S2 | 0.6794 | 2 |
| S3 | 0.5457 | 1 |
| S4 | 0.6555 | 2 |

D* is the 95th percentile of true-match cases' nearest distance at the widest spread; k* the fewest observable
dimensions at which the generating objective is nearest or tied in at least 80% of sparse cases at the design spread.
**The opposite check** (an objective's own distance to the opposite of its decision exceeds D*) was met in at least
99.8% of trials on every shape. **"No good match" is rare by design:** with five objectives, another objective usually
sits near any decision, so an opposite case read as "no good match" only 15% to 66% of the time, by shape.

---

## 12. The real cases

Real cases illustrate the protocol on real decisions. They are **readings, not tests**: never in the family of 16,
never a claim about how often companies do anything, never a statement about any company's motives. **No company is
named in any public file;** identities, filings, scaling factors and unscaled figures stay in a private appendix.

### 12.1 Case types and how many

**Closure or restructuring, k = 2; an AI-attributed workforce change, k = 1** (it may come from outside
manufacturing, labeled as a different company type); **invest or retool, k = 2** (a closure with production moved to
a new facility the company is building counts as retool). At most five cases, at least three, at least one invest or
retool. **A type that yields fewer than k is a reported shortfall, never filled by judgment.**

### 12.2 The window and the date

- **The search runs once,** on **the day after the official grid's results are committed**, by rule, so no one picks
  the date knowing the candidates.
- **The window:** a decision's **first public disclosure** on or after **2026-08-01**, through the day before the
  search. 2026-08-01 is the buffer past every candidate model's June 2026 training cutoff that the data-sources plan
  prefers; *[for his decision: whether July 2026 disclosures are admitted after an earlier-signal check, as
  `planning/01` §3.2 allows, or excluded, as drafted here]*. If the model set adds a model with a later cutoff, the
  window opens on the first of the second month after the latest cutoff.
- **A decision is dated by its first public disclosure, never its filing date.** Every candidate is searched for
  earlier mentions (an earnings call, a press release, an earlier filing) before any other criterion; one found before
  the window fails it.

### 12.3 The search, query by query

All through EDGAR full-text search (`https://efts.sec.gov/LATEST/search-index`; checked live 2026-10-09: phrase
queries, `OR` between phrases, and the `forms`, `dateRange=custom`, `startdt` and `enddt` parameters work; a grouped
`AND (... OR ...)` query returned nothing, so every query below is a plain list of phrases), with a User-Agent naming
the project and a contact, under the SEC's limit of 10 requests a second, every page of results read. Each hit's
structured `items`, `sics` and `file_date` fields are what the filters below read. **Queries are run separately and
their hits unioned; a filing found twice counts once.** Dates are the window's (section 12.2), on the filing date; the
first-disclosure check then dates each candidate.

| Channel and type | Forms | Query (each line its own query) | Filter on the hit |
|---|---|---|---|
| **1. Exit or disposal** (closure or restructuring) | 8-K | `"Item 2.05"` | `items` includes 2.05; `sics` 2000-3999 |
| **2. Invest or retool** | 8-K | `"new manufacturing facility"`; `"new production facility"`; `"expand production"`; `"expansion of our manufacturing"`; `"capacity expansion"`; `"retool"` | `items` includes 7.01 or 8.01; `sics` 2000-3999 |
| **3. AI-attributed workforce change** | 8-K | `"artificial intelligence" "reduction in force"`; `"artificial intelligence" "workforce reduction"`; `"artificial intelligence" "reduce our workforce"`; `"AI" "reduction in force"`; `"automation" "workforce reduction"` | any `items`; any `sics`, labeled by company type |

*[For his decision: WARN notices and trade press (`planning/01` §4.7) cannot be queried by a fixed rule, since every
state publishes WARN notices differently and trade press has no fixed index. Drafted here as **not a discovery channel
in v1**, so discovery is mechanical; the alternative is a fixed list of state WARN databases, each with its own
rule.]*

**A channel that has changed by the search date** (an endpoint gone, a field renamed) is reported as a deviation; its
replacement query is written then, read by the independent reader (section 12.9), and logged.

### 12.4 Selection

Candidates are taken **in order of first disclosure**, per type, and each is checked against the criteria in order:
(1) publicly traded and filing with the SEC; (2) first disclosed inside the window; (3) a real decision with real
alternatives (not a forced wind-down); (4) maps onto a scenario shape (section 12.5); (5) not instantly recognizable
after anonymization (the recognition probe, section 12.8); preferred, a manufacturer of comparable size. **The first
k that pass are the cases.** Every candidate considered is logged with each criterion passed or failed and why; the
log is published by case type, without names. **Every rejection on criterion 3, 4 or 5 is read by the independent
reader;** a disagreement is resolved by him and logged with the reason.

### 12.5 The scenario-shape rule

Applied to the first-disclosure document; **the first rule that matches wins:**

1. A workforce change the document attributes to AI or automation software: **S1.**
2. A facility named for closure or sale, with or without new capacity elsewhere: **S3** (on retool when new or
   converted capacity is named).
3. A multi-year program of stated annual cost, funded or declined: **S4.**
4. A restructuring with workforce or cost reductions and no facility named: **S2.**

A document that matches none fails criterion 4, and that rejection is independently read.

### 12.6 The dossier and the scenario text

- **Only documents dated before the cut-off** (the day before first disclosure), enforced in code: the most recent
  annual and quarterly reports before it and earlier current reports a chief executive would know. **The extraction
  model sees only those sections and is never told the outcome.**
- **The template,** the same seven sections for every type, in this order, each sourced only from pre-cut-off
  documents: **(1) overview** (what the company makes and sells, at the level of a product category); **(2) segments
  and facilities** (segments with revenue and income; facilities by region and function, never by town); **(3)
  workforce** (headcount by function where disclosed, pay where disclosed, representation); **(4) financial position,
  three years** (revenue, operating income, cash flow, debt, liquidity); **(5) capital allocation history** (capital
  spending, research and development, dividends and repurchases, acquisitions, three years); **(6) the situation at the
  cut-off** (what the latest pre-cut-off filings say about demand, costs and the facility or program in question);
  **(7) the options plausibly open,** for the case's scenario shape. **S1** needs 1, 3, 4, 6, 7; **S2** 1, 3, 4, 5, 6, 7;
  **S3** all seven; **S4** 1, 4, 5, 6, 7. **No section may hold a figure dated after the cut-off or a term that names
  the outcome.**
- **Option economics** come only from pre-cut-off documents. **Where an option has no pre-cut-off figures, every
  option is described without figures alike,** so the option the company chose is never the best-described one.
- **Anonymization:** company, brand, product, executive and place names removed; places become regions; dates become
  relative ("fiscal year N, third quarter"); distinctive facts that identify a company on their own (a unique product,
  a named lawsuit) generalized.
- **Scaling:** every dollar figure and every headcount scaled by one factor per case, **drawn log-uniformly from
  [0.6, 0.9] ∪ [1.1, 1.6]** from a private recorded seed, never chosen; dollars to three significant digits,
  headcounts to the nearest 5. The gap around 1 means no case keeps its real figures by chance; pay per head is checked
  to stay in a realistic band after rounding.
- **Two checks on the dossier and the scenario text:** the **foreshadowing check** (the rubric's outcome terms
  searched for; every hit justified in writing or removed) and the **neutrality checklist** of section 4.2, since the
  options are real.

### 12.7 The rubric and the matcher

- **The rubric:** what the company did, from filings dated after the event, mapped onto the scenario's table and
  choice; **actions only, never stated reasons**; which dimensions are observable and which excluded (published beside
  the case's result); every uncertain call with its alternative reading. **Read by the independent reader. Committed
  before any model sees the case,** and every case's rubric before any case's decision runs.
- **The runs:** five objectives, three wordings, **10 repeats**, on each model in the set.
- **The distance per run,** on observable dimensions only, on the line-level vector: total variation distance (half
  the sum of absolute differences) renormalized over the observable lines; for a choice, 0 if the run made the
  company's choice and 1 if not; averaged with equal weight when both exist. A run with nothing on the observable lines
  and no observable choice has no distance: it is left out and counted.
- **An objective's distance** is the mean of its per-wording mean run distances, with a 95% stratified bootstrap
  spread (100,000 resamples, the generator seeded from the sweep and the reading, never chosen).
- **The label, in order:** **not enough disclosed** (fewer dimensions than k*, counting the choice as one and n
  observable lines as n − 1); **no good match** (the nearest distance above D*); **tie** (the 95% interval of the gap
  between the two nearest includes zero); otherwise **match**, "most closely matched". All five distances and their
  spreads are shown whatever the label.
- **Readings:** every uncertain call is also matched under its alternative reading; when the readings' matched sets
  (the nearest, or the tied pair) share no objective, the case is reported as **"depends on reading"**, with both.

### 12.8 The recognition probe

Before any decision run, each model in the set receives the anonymized dossier as the system text and this user
message, word for word, **three calls per model:**

> Which company is this? If you are not sure, say unknown.

**A call names the company** if its answer contains the company's name or a former name, its ticker, or one of its
brands, checked against the case's private term list and by one human read of every answer that is not "unknown".
**The case fails if any call names it.** A failed case is **coarsened** once, by a fixed procedure: regions widened
one level, every remaining proper noun removed, figures rounded to two significant digits, distinctive events
generalized; then **one re-probe**, which needs the changed dossier. A second failure drops the case, and it is
**replaced by the next eligible candidate of its type, in order of first disclosure,** logged. Results are published
by case type.

### 12.9 The independent reader

Another vendor's model that has not seen the grid's results, given only the criteria or the rubric with its source
excerpts. It reads every rejection on a judgment criterion and every rubric's mapping. A disagreement is resolved by
him and logged with the reason.

### 12.10 The case mode of the gate

A real-case sweep has content that did not exist at the tag, so it is admitted only when, for that case: **(1)** a
case record committed to the repository holds the sha256 of the case's dossier, scenario text and rubric, and the
content supplied to the run hashes to it; **(2)** the record was pushed before any model saw the case, shown by two
times neither author can set: the **created time of a GitHub Actions run** on a commit holding the record, earlier
than the **storage time (`LastModified`) of the case's first recognition-probe record**; for a coarsened case, the
rubric before the first probe of any set, and the content before the first probe of its own set; **(3)** every
recognition probe in the set that counts passed on every model; **(4)** the document, instrument, analysis and model
checks of section 15 hold, in the container.

### 12.11 What is published

Results by case type, with each case's observed and excluded dimensions, and the selection log without names. **Every
memo passes a company-name scan** (the private list plus a general check for any company name) before publication; a
memo that names one is held back and counted. **An anonymized dossier is published only after a re-identification
check passes** (its distinctive figures and description searched against public sources, including the structured
financial data it was built from); one that fails is withheld, the reason stated.

---

## 13. What is published, and run accounting

### 13.1 Published

For every cell: runs attempted, valid, rescaled, failed by type and refused; the mean and spread of every line and
group; per-wording means; every primary comparison's verdict with its interval, worst-case bound and wording label;
the sealed-wording results; the secondary A vs D; the thinking sub-study; the second model; the awareness probe;
first attempt beside final; tokens and dollars per sweep; the real-case results (section 12.11). **Every raw response
on the fictional company is published in full.** Every primary comparison is published, whichever way it falls.

### 13.2 Run accounting

- **A sweep is one pre-registered study on one model:** the pilot, the grid, the thinking sub-study, the awareness
  probe and each case's runs are each their own sweep, with their own manifest and cost cap, each run once per
  protocol version.
- **Within a sweep, runs go in one shuffled order across every cell,** from a seed recorded in the manifest and fixed
  with the run set before the first run, so a sweep stopped early is a balanced subset.
- **Missing runs** (infrastructure failures) are filled in by run id; **nothing that completed is ever re-run.**
- **Official means a run in the container,** from an image identified by its digest, admitted by the gate (section
  15). Everything else is development or exploratory, stored under a separate prefix, labeled everywhere, and never
  merged.
- **Run counts are published for every sweep,** including discarded development sweeps, with the reason.
- **Raw responses are kept write-once,** one object per attempt, with full provenance on every call.
- **The cost caps:** $25 per official sweep and $5 per development sweep, enforced by the harness before and during
  a sweep; raising one needs his explicit flag.

---

## 14. The change policy

- **Before the tag,** anything here may change.
- **After the tag, two kinds of change only:**
  - **an erratum**: a correction that changes no computation, no content and no rule (a typo, a broken link, a
    clearer sentence), dated and listed in `experiment/protocol/errata-v1.md`, which no lock hashes;
  - **a new version, `prereg-v2`**: anything that changes a computation, a hash or a rule. It gets its own document,
    lock and tag; its results are reported beside version 1's and never merged; a sweep under it is labeled with it.
- **What is frozen** (section 15.2): the content, this document, the instrument code and the analysis code. **Run
  code** (the runner, the planner, the launcher, the providers, the pacing and spend controls, the infrastructure) may
  be fixed after the tag, each fix logged with its effect on runs.
- **The official analysis runs from a checkout of the tag,** with the tag's locked library versions, so the code and
  the libraries that compute every verdict are the tag's by construction. A run-record format the tagged reader cannot
  read is a new version.

---

## 15. How to verify all of this

*[Filled on tag day: the protocol commit, the tag object, the CI run, the tag ruleset as read back, the Software
Heritage archive's identifier and visit date, the release, and the gate's dry runs against the tag
(`docs/phases/evidence/phase-3.5/tag-record.md`).]*

### 15.1 The tag and the archive

The tag `prereg-v1` points to the protocol commit. A tag ruleset restricts updating and deleting `prereg-*` tags and
blocks force pushes; **a ruleset is not absolute** (a repository admin can change the ruleset itself), so the
independent proof is the **Software Heritage archive**, which records the tag and its commit at a dated visit.

### 15.2 The lock

`experiment/protocol/prereg.lock`, written by `hc protocol lock --write` and never by hand, holds the sha256 of: this
document; the content (the dossier, objectives and rendered scenarios, plus the whole company folder for the record)
and the sealed template; the **instrument** code (`sweep/prompt.py`, `sweep/decision.py`, `sweep/classify.py`); the
**analysis** code (every file in `analysis/`, `matcher_thresholds.toml` included, and `experiment.py`); the simulation
results and their code hash; and each official model's identity (ID, route, profile, region, thinking and sampling
fields). `hc protocol check` compares the tree with it and runs in every CI check.

### 15.3 The gate

The harness refuses an official sweep unless **every** check holds, and reports every failed check, not only the
first: the lock exists and parses; this document's hash; the content hash and the experiment; the sealed template is
the lock's and the plan uses it; the instrument set's hash; the analysis set's hash; the model is one of the lock's,
with the same ID, route, profile and region; and the run is in the container, with an image digest.

### 15.4 Commands

From a clone at the tag: `make setup`, then `uv run hc protocol check` (every hash against the lock), `uv run hc
scenarios check` (the renders, the change log and the sealed draw), and the sealed draw's one-line recomputation in
section 4.3.
