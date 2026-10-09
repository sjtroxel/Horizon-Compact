# Phase 3.5 — Pre-registration: IMPLEMENTATION (v0.3.5)

> **IMPLEMENTATION doc.** Written 2026-10-09 (Opus) from the approved scope doc
> (`docs/phases/phase-3.5-preregistration.md`, its six decisions as recorded there), `KNOWN-GAPS.md` read in full
> (START HERE and every OPEN, BLOCKED and RECORDED entry), `planning/07` (all of it, as patched through 2026-10-09),
> `planning/05` §2 and §3.1, `planning/04` §1.2, §1.9 and §2.3, `planning/01` §3-§4, `planning/02` §2.5, `planning/09`
> §5, the Phase 4, 5 and 5.5 scope docs (what they expect the protocol to hold), the Phase 2.5 IMPLEMENTATION doc §22
> (its close-out and honor statements), the Phase 3 IMPLEMENTATION doc §15-§20c, and the harness as built
> (`experiment.py`, `sweep/runner.py`, `sweep/plan.py`, `sweep/prompt.py`, `sweep/decision.py`, `sweep/classify.py`,
> `analysis/`, `simulation/runner.py`, `infra/docker/Dockerfile`, `privacy/guard.py`). **APPROVED 2026-10-09 (his), all ten
> decisions in §15 as recommended, on two conditions of his:** no more than **$5 of OpenRouter, in aggregate, for
> every use from here on**, and **no indefinite wait on AWS**. The second sets a deadline on decision 5 (§15, decision 5
> as decided).
>
> **The doc is written so that the code and the protocol's text can be built without AWS; every model call waits
> for it.** *Amended 2026-10-09 (his, before approval): **no cash by default.*** OpenRouter spends his own money;
> Bedrock spends the shared AWS credits. The tag already waits on AWS (decision 5), so paying to run anything earlier
> buys no time. Every model call this phase makes therefore runs on Bedrock under the credits once quotas return:
> the Nova Lite runs (decision 4), the garden proxy (decision 3) and the review (decision 7). The OpenRouter routes stay
> in the doc as options, priced, for him to choose only if he wants them.
>
> **Vocabulary, for a business reader of the protocol:** *pre-registration* is a research term for publishing the
> full plan of a study, with how its results will be judged, before collecting any data, so the plan cannot be fitted
> to the data afterwards. *Erratum* (plural *errata*): a dated correction that changes no computation and no content.

## 1. Where things stand on 2026-10-09, before this phase

**Done and committed.** Phase 3 closed this morning (DoD audit in its IMPLEMENTATION doc §19a). The analysis engine
is built and tested, the simulations are recorded (`docs/phases/evidence/phase-3/`), and `D*`/`k*` are in
`src/horizon_compact/analysis/matcher_thresholds.toml`. Last commit `84d82d7`, pushed, CI green. **His step 13
close-out (four doc files) is uncommitted and rides in this doc's commit, C1** (his choice, 2026-10-09).

**Decided and carried in** (`KNOWN-GAPS.md` START HERE, 2026-10-09):
- the worst-case bound is kept as built, **to be revisited before the tag on a failure rate measured on the chosen
  model** (his decision 1 of 2026-10-09);
- the share rule's measured worst case (0.43% against 0.3125%) is **stated, not recalibrated** (his finding A);
- the matcher's opposite check is judged on the generating objective (his decision 2 of 2026-10-09).

**Waiting on AWS** (the BLOCKED entry): every Bedrock call has been throttled since 2026-10-05; case
179121856900232 is "Unassigned", left alone on purpose to keep its place in the queue. Behind it: Phase 1 steps 3, 9,
11 and 12; Phase 1.5; the pilot and everything official. **Not behind it:** this doc, the protocol's text, the code
in §5-§8, the independent review, and (decision 4) the Nova Lite runs.

**Open items that land in this phase** (from `KNOWN-GAPS.md`): the Haiku 5.5 model-set question (OPEN 2026-10-08);
Nova Pro's tagged profile (OPEN 2026-10-08); the Nova Lite probes and format runs (OPEN 2026-10-07); and the AWS
fallback (his item 3), which this doc does not decide but must not foreclose (§3 item 12).

## 2. What this phase delivers

From the scope doc's Delivers 1-6, made concrete. In build order:

1. **The frozen code, defined and hashed** (§5): which files a protocol hash covers, in two sets, the *instrument*
   (what the model reads and how a reply is judged) and the *analysis* (verdicts, intervals, matches).
2. **The lock file** (§6): `experiment/protocol/prereg.lock`, the machine-readable half of the protocol, and the
   commands that write and check it.
3. **The gate, extended** (§7): an official sweep is refused unless the content, the instrument, the analysis, the
   protocol document and the model's identity all match the lock; the case mode (§8); the repeat-count check (§7.4).
4. **The model set fixed** (§10), after the open check for a newer non-Anthropic model and the Haiku 5.5 question.
5. **The protocol document** (§9): `experiment/protocol/protocol-v1.md`, self-contained, against the scope doc's
   Delivers 2 list, including the real-case build rules the scope doc's amendment added.
6. **The independent review** (§11): brief, raw reply, every point marked and resolved, before the tag.
7. **The tag** (§12): `prereg-v1`, his, on the protocol commit; a tag ruleset; a Software Heritage archive visit; a
   GitHub release.
8. **The gate proven both ways** without a model call (DoD 4), and the record that nothing official exists (DoD 5).

## 3. What writing this doc found

1. **The prompt frame and the validation rules live in code, not in the hashed content.** `Experiment.content_hash`
   covers `dossier.toml`, `objectives.toml` and the rendered `scenarios/*.toml`. The role sentence, the instruction,
   the menu lines, the tool's schema and descriptions are built by `sweep/prompt.py`; whether a reply is valid,
   rescaled or `sum_mismatch` is decided by `sweep/decision.py`; whether a failure is retried, and whether an error is
   a model failure or an `api_error`, by `sweep/classify.py`. All three set what the model sees or what counts as a
   failure, and the analysis reads their verdicts from the records (`validation.scaled_amounts`, `status`). The scope
   doc's decision 1 calls "model calls, retries, storage" run code that may be fixed after the tag. **Retries and
   failure classification are rules** (`planning/07` §5.1), and the prompt is content. So the frozen set is larger than
   `analysis/`. Decision 1.
2. **The analysis imports the loader.** `analysis/outcomes.py`, `matcher.py`, `results.py`, `robustness.py` and
   `records.py` import from `experiment.py`, which also holds the run-only model config (`ModelConfig`, `ModelsFile`,
   `Prices`). Phase 2.5 changed it for run reasons as well as content ones (the Ollama provider's `num_ctx`, the
   OpenRouter route). Frozen whole, any later model-config change is a new protocol version; left out, the analysis's reading of
   a scenario could change silently. Decision 1.
3. **The analysis libraries are pinned by `uv.lock`, which also pins the run libraries.** Hashing `uv.lock` into the
   analysis set would make a `boto3` bump a protocol change. Running the official analysis from a checkout of the tag
   (`uv sync --frozen` there) pins numpy, scipy and statsmodels exactly, with no hash of the whole lock needed for the
   gate. Decision 1.
4. **"Thinking off" is a different request on each candidate model** (Claude API skill, models table cached
   2026-10-06): on Sonnet 4.6, leaving `thinking` unset means no thinking; on **Haiku 5.5, thinking is on by default**,
   and is off only with an explicit `thinking: {"type": "disabled"}`, accepted only at effort `high` or below (its
   default effort is `medium`); non-default sampling values are refused. So "thinking off, sampling never set" holds
   for both, but the exact request fields differ and the protocol must state them per model. On Bedrock this is
   documented, not observed.
5. **The failure rate that his decision of 2026-10-09 needs cannot be measured on the company's content before the
   tag.** "No official model sees real content before the tag" (scope doc rules). The pilot measures it, after the
   tag, when the bound rule is already frozen. **The only pre-tag measurement on the official model is on
   off-subject content** (a garden copy of each scenario's shape, which the placeholder rule allows: Phase 2.5 step 6a
   ran Sonnet 4.6 on garden content, 10 of 10 valid). That proxy measures format failures, not refusals, which depend
   on the subject. Decision 3.
6. **Nova Lite is on OpenRouter at its Bedrock price** (`amazon/nova-lite-v1`, $0.06 / $0.24 per million tokens, read
   2026-10-09), so the prerequisite *could* run without AWS. **But on OpenRouter it is his cash, and it buys no time:**
   the tag waits for AWS anyway (decision 5). On Bedrock it is credits. Decision 4.
7. **A tag before any official model has answered once would freeze a route nobody has proven.** The model set names
   each model's ID, route and profile. If Bedrock never returns and an OpenRouter route becomes official (the AWS
   fallback, his item 3), a tag made earlier becomes `prereg-v2` before a single official run. Harmless to the
   result, but it spends the one clean version on a route change. Decision 5.
8. **The awareness probe and the recognition probe have no text anywhere.** `planning/07` §7.5 and §10.3 describe
   them; `grep` finds no prompt for either in `src/` or `experiment/`. Their exact wording is part of the instrument,
   and written after the grid's results it would be a lever. The protocol states both texts word for word; Phase 4
   and Phase 5 build from them.
9. **The thinking sub-study's request fields are not in the harness either.** The sweep has no thinking option
   (`sweep/plan.py`, `cli.py`); Phase 0.5's smoke calls sent `thinking: {"type": "adaptive"}` and
   `output_config.effort: "high"` in `additionalModelRequestFields`. The protocol states those fields; Phase 4 builds
   the option to send exactly them.
10. **The real-case search queries are a lever the scope doc did not freeze.** The protocol fixes the channels, the
    window and the date (Phase 5 decision 6), but Phase 5's scope doc leaves "the search queries per channel,
    exactly" to its IMPLEMENTATION doc, written after the grid's results. A query chooses which candidates appear as
    surely as a date does. Decision 6.
11. **Phase 5's scope doc and the amended Phase 3.5 scope doc disagree on two items.** Phase 5's "Left for the
    IMPLEMENTATION doc" lists "the template per case type, section by section" and "the scaling factor's range"; the
    3.5 scope doc's amendment (from Phase 5's own decision 2, the later decision) puts both in the protocol. **The
    amendment governs**: both are written here (§9.3, decision 7), and Phase 5's scope doc gets a dated note.
12. **The case mode cannot read git history in the container.** The image copies `src/`, `experiment/`,
    `pyproject.toml` and `uv.lock` (`infra/docker/Dockerfile`), not `.git`. And a commit's date is set by its author,
    so "the rubric's commit predates the probe" proven by commit dates proves nothing to a stranger. Server-side
    timestamps exist that he cannot set: the GitHub Actions run created on the push, and the S3 object's
    `LastModified` on the probe record. Decision 10.
13. **Real-case content may never be in the public repo** (Phase 5 decision 5: a dossier is published only after a
    re-identification check, and withheld if it fails). So the case mode must work on **committed hashes** with the
    content supplied at run time from private storage, not on committed files. Where that content lives is Phase 5's;
    the check is written here so it does not depend on it.
14. **The repeat rule needs scipy, and the container has none** (Phase 3 decision 2 kept the analysis group out of
    the image). The gate cannot recompute the repeat count inside the task as the scope doc's Delivers 4 imagines.
    Decision 9.
15. **The old tag protection feature is gone.** GitHub replaced tag protection rules with **repository rulesets**
    (sunset announced 2024-05-29, migration 2024-08-30); a tag ruleset can restrict creation, update and deletion of
    matching tags and block force pushes. **A ruleset is not absolute:** a repository admin can edit or delete the
    ruleset itself. The outside archive is what a stranger can trust without trusting him or GitHub (§12).
16. **The name guard already covers the tag.** `privacy/guard.py`'s `pre-push` scans tag names and annotated tag
    messages. The release's title and notes are typed into GitHub and are **not** scanned: his to check (rule zero).
17. **Phase 4's three known run-code items touch one frozen file.** Narrowing the `possible_decline` pattern edits
    `sweep/classify.py` (OPEN entry, Phase 4). If `classify.py` is frozen at the tag, that fix becomes a new protocol
    version. Done before the tag, it costs a few lines. The other two (per-scenario repeats in `plan.py`, forwarding
    `--official` in `launch.py`) are run code under decision 1 and stay in Phase 4.

## 3a. Checks run while writing this doc (live, 2026-10-09)

- **GitHub, through `gh api` (read only):** the repository is public; it has **no rulesets, no tags and no
  releases**. Tag rulesets offer "restrict creations", "restrict updates", "restrict deletions" and "block force
  pushes" (GitHub docs, "Available rules for rulesets"); tag protection rules were sunset in 2024 (GitHub changelog,
  2024-05-29). Whether a ruleset is available on a free personal public repository is not stated on that page;
  build step 11 finds out by creating one.
- **Software Heritage, through its public API (read only):** the origin `https://github.com/sjtroxel/Horizon-Compact`
  is **not yet archived** (404 on `/api/1/origin/.../get/`; no save request). The save endpoint
  (`POST /api/1/origin/save/git/url/<url>/`) is **immediately accepted for GitHub origins**, needs no account, and
  its status reply carries `visit_date` and `snapshot_swhid`. A snapshot holds every branch and tag the visit found,
  so `refs/tags/prereg-v1` and the commit it points to are recorded with a time Software Heritage sets.
- **OpenRouter, public model list (`/api/v1/models`):** `anthropic/claude-haiku-5.5` $0.10 / $0.50 per million;
  `amazon/nova-lite-v1` $0.06 / $0.24; `amazon/nova-pro-v1` $0.80 / $3.20; `openai/gpt-6-astra` $10 / $50 (the
  `planning/08` and Phase 2 reviewer); `google/gemini-3.1-pro-preview` $2 / $12 (the Phase 2.5 blind reader).
  `amazon/nova-2-lite-v1` and `amazon/nova-premier-v1` exist there too.
- **A newer non-Anthropic model than Nova Pro** (`planning/09` §5): AWS announced Nova 2 on Bedrock in December 2025;
  **Nova 2 Pro was a preview for Nova Forge customers** and no general-availability notice was found; Nova 2 Lite is
  offered through global cross-region inference (data routed worldwide, which `planning/02` §2.5 declined for
  Claude). Secondary sources only; the check closes on the account, not on the web (build step 9).
- **Claude Haiku 5.5** (Claude API skill, models table cached 2026-10-06): $0.10 / $0.50 per million up to 100K
  tokens, 1M context; thinking on by default, `disabled` only at effort `high` or below; non-default sampling refused.
  Bedrock availability on this account: unknown; AWS's restricted list of 2026-10-05 predates the model.

## 4. Layout

```
experiment/protocol/
  prereg.lock            the machine-readable protocol (§6); already the path runner.py reads
  protocol-v1.md         the human-readable protocol (§9); hashed by the lock
  errata-v1.md           dated errata (scope decision 6); deliberately NOT hashed
experiment/shapes/       garden copies of the four scenario shapes (decision 3); off-subject placeholders
src/horizon_compact/
  protocol/              new: the frozen sets, the lock writer and checker, the case-mode and repeat checks
    __init__.py
    sets.py              which files are in each frozen set, and their hashes (§5)
    lock.py              build, write and read the lock; compare it with the tree (§6)
    gate.py              the official-sweep checks, one function per check (§7)
    cases.py             the case mode (§8)
  model_config.py        new: ModelConfig, ModelsFile, Prices moved out of experiment.py (decision 1)
docs/phases/evidence/phase-3.5/
  review-brief.md, review-raw.md, review-resolutions.md      (§11)
  failure-proxy.md       the garden runs' failure rates (decision 3)
  model-facts.md         each candidate model's facts as read on the day (§10)
  calls-inventory.md     every model call so far, by phase and label (DoD 5)
  tag-record.md          the tag, its commit, the CI run, the archive visit, the release (§12)
```

The protocol lives under `experiment/` because the image copies `experiment/` and not `docs/`: the gate in the
container can then hash the document it enforces (decision 8). No new root entry; the root stays 13 of 16.

## 5. The frozen code (decision 1)

### 5.1 Three kinds of code

| Kind | Files | After the tag |
|---|---|---|
| **Instrument** | `sweep/prompt.py` (frame, menu, tool), `sweep/decision.py` (validation, rescaling), `sweep/classify.py` (statuses, retries, `api_error`) | frozen: a change is `prereg-v2` |
| **Analysis** | every file in `analysis/` (`matcher_thresholds.toml` included), and `experiment.py` (the loader the analysis reads scenarios through) | frozen: a change is `prereg-v2`; the official analysis runs from a checkout of the tag |
| **Run** | everything else: `sweep/runner.py`, `plan.py`, `launch.py`, `pacing.py`, `spend.py`, `store.py`, `providers/`, `cli.py`, `model_config.py`, infrastructure | may be fixed, each fix logged with its effect on runs (scope decision 1) |

**Why the instrument is frozen and not "run code":** the prompt is what the model reads, and the validation and
classification decide which replies count. A change to either after a result is seen can change the result through
which runs are valid, without touching a hashed content file.

**Why `experiment.py` is in the analysis set, and why `model_config.py` is split out first:** the analysis reads every
scenario through `experiment.py`'s `Scenario` model. Moving the three run-only model classes into their own module
before the tag leaves `experiment.py` holding only content schema and its loader, which is the part the analysis
depends on. `load_experiment` still reads `models.toml`, through an import; a later field on `ModelConfig` then
changes `model_config.py`, not `experiment.py`.

**The official analysis runs from the tag.** Phase 4 runs it in a clean checkout of `prereg-v1` (`git worktree add`,
`uv sync --frozen`), so the code and the library versions are the tag's by construction, and the results object
records the tag's commit and the analysis hash it computed. This removes the need to hash `uv.lock` for the gate;
the lock records `uv.lock`'s hash for the record only. **What it costs:** a run record whose format changes after the
tag must still be readable by the tagged reader (`analysis/records.py`); a format change it cannot read is
`prereg-v2`. `RECORD_VERSION` stays 1, and a test written now pins the fields the reader uses.

### 5.2 How a set is hashed

The same way `simulation/runner.py`'s `code_hash` already does: sha256 over each file's repo-relative path, a zero
byte, its bytes, a zero byte, files in sorted path order. One function in `protocol/sets.py`, used by the lock writer,
the gate and the tests. `__pycache__` and anything not tracked by git is excluded (the set is listed by pattern and
filtered through `git ls-files` on the laptop; in the container, by the same pattern on the copied tree, which holds
no untracked files).

### 5.3 What the content hash covers, and what the lock adds

The content hash stays `Experiment.content_hash` (dossier, objectives, rendered scenarios). The lock adds the hash of
the **whole** `experiment/company/` tree (sources, figures, the change log, probes) for the record, since those prove
where every number came from, but the gate enforces only what the model reads plus the two code sets.

## 6. The lock file

`experiment/protocol/prereg.lock`, TOML, written only by `hc protocol lock --write` and never by hand. Fields:

```toml
lock_version = 1
protocol = "prereg-v1"
document = "experiment/protocol/protocol-v1.md"
document_sha256 = "..."

[content]
experiment = "company"
content_hash = "..."                 # Experiment.content_hash, what runner.py already compares
files = { "company/dossier.toml" = "...", ... }
tree_sha256 = "..."                  # the whole experiment/company/ tree, for the record
sealed_template = "w2"

[instrument]
sha256 = "..."
files = { "src/horizon_compact/sweep/prompt.py" = "...", ... }

[analysis]
sha256 = "..."
files = { ... }
results_version = 2
uv_lock_sha256 = "..."               # record only; the analysis runs from the tag

[simulation]
results_sha256 = "..."               # docs/phases/evidence/phase-3/simulation-results.json
code_sha256 = "705078047b9e..."      # as recorded inside it

[models.sonnet-4-6]                  # one table per official model (decision 2)
model_id = "anthropic.claude-sonnet-4-6"
route = "application_profile"
inference_profile = "horizon-compact-sonnet-4-6"
region = "us-east-1"
thinking = "not set"                 # the exact request fields, as sent (§3 item 4)
sampling = "not set"
role = "main"
```

**Model identity, not model config.** The lock holds the fields that decide which model answers and how it is
asked; prices, quotas and pacing stay in `models.toml`, where they may change (prices are re-checked before each
sweep, `planning/03`).

**`make check` runs `hc protocol check`.** Before the lock exists it passes and says so. Once the lock is committed,
any change to a frozen file fails `make check` and CI, naming the file. That is the intent: after the tag, a frozen
file changes only through `prereg-v2`, which writes a new lock beside the first. **Errata live in `errata-v1.md`,
which no lock hashes** (scope decision 6).

## 7. The gate

### 7.1 The checks, one by one

`runner.check_official` today checks one thing (the content hash) and the container. It becomes a list, each check a
function in `protocol/gate.py` returning a named mismatch or nothing, all run, all reported together:

1. **The lock exists and parses**, and its `lock_version` is known.
2. **The protocol document's hash** equals `document_sha256`.
3. **The content hash** equals `[content].content_hash`, and the experiment is the lock's (`company`).
4. **The sealed template** equals the lock's, and the plan uses it (the official grid includes it; `plan.py`'s
   development refusal of it is unchanged).
5. **The instrument set's hash** equals `[instrument].sha256`; on a mismatch, the message names each differing file.
6. **The analysis set's hash** equals `[analysis].sha256`, same reporting. The sweep does not run the analysis, but a
   changed scoring file is a tripwire the scope doc's DoD 4 asks for.
7. **The model** is one of the lock's `[models.*]`, and its `model_id`, route, profile and region in `models.toml`
   equal the lock's.
8. **In the container**, with an image digest (unchanged).

A refusal prints every failed check, never only the first, in the form `official sweep refused: instrument differs
from prereg-v1: src/horizon_compact/sweep/decision.py`.

### 7.2 The dry run (DoD 4)

`hc sweep run --official --dry-run ...` runs every check, plans the sweep, writes nothing and calls no provider. On the
laptop, check 8 reports "not in the container (dry run)" and the dry run still returns its verdict on 1-7. **Proven
both ways against the tagged commit itself** (a worktree of `prereg-v1`): passes as tagged; refused with one byte
changed in a scenario file (content), in `decision.py` (instrument), in `verdict.py` (analysis), in `protocol-v1.md`
(document), and with Nova Pro's profile changed in `models.toml` (model). Each refusal's message is kept in
`tag-record.md`. The same cases are unit tests on a synthetic lock, so they hold in CI after the tag.

### 7.3 What is not checked, and why

The run code (decision 1). `models.toml`'s prices and quotas. The order of runs and the per-scenario repeats, which
the manifest records and Phase 4's run-set commit fixes before the first official run (Phase 4 decisions 2 and 3).

### 7.4 The repeat count (decision 9)

`protocol/gate.py` gains `required_repeats(pilot: RunSet) -> RepeatDecision`, a thin call to `analysis/repeats.py`
over the pilot's runs, refusing a pilot whose manifest does not say pilot or whose content hash is not the lock's.
**On the laptop**, `hc protocol repeats --pilot <sweep_id>` computes it and writes `repeats.json` once (write-once,
like every run object) under the pilot's prefix, with its inputs (run ids, pooled spread and degrees of freedom per
scenario, the rule's outputs) and no mean, difference or objective. **The official launch** refuses unless the plan's
repeats equal that file's. Anyone can recompute it later from the published pilot records. Phase 4 wires it to the
per-scenario repeats it builds; this phase builds and tests the function on synthetic pilot records.

## 8. The case mode (decision 10)

A real-case sweep has content that did not exist at the tag. It is admitted only when, for that case:

1. **A case record is committed** (`experiment/cases/<label>/case.lock`, Phase 5's to write) holding the sha256 of the
   case's dossier, scenario text and rubric, and the content supplied to the run hashes to it.
2. **The commit that first holds that case record was pushed before any model saw the case**, shown by two times he
   cannot set: the **created time of a GitHub Actions run on a commit containing the record** (GitHub API), earlier
   than the **`LastModified` of the case's first recognition-probe object in S3**.
3. **Every recognition probe for the case passed** on every official model (`planning/07` §10.3), read from the probe
   records; a coarsened case's second probe set is the one that counts, and the first is kept.
4. Checks 2 (document), 5, 6 and 7 of §7.1 hold as for the grid; check 3 is replaced by 1 above.

Check 2 runs on the laptop at launch (it needs the GitHub API and S3) and writes its finding into the manifest; the
container re-checks 1, 3 and 4. **Proven both ways on a synthetic case** with fake GitHub and store objects: admitted
with an earlier CI run and a passed probe; refused with a CI run after the first probe, with no CI run, with a failed
probe, and with content that does not hash to the record.

## 9. The protocol document

### 9.1 How it is written

**Self-contained.** A stranger reads one document and nothing else. Every rule is restated in its final form, without
its patch history, with the source it came from (`planning/07` §6.3, a decision, a phase doc) beside it. Where a
number came from a simulation, the protocol quotes it and names the evidence file. `planning/07` gets a dated status
patch: its rules now live in the protocol, which governs where they differ, and it is no longer amended.

**It does not argue.** Each verdict is described with what it would mean, including the ones in the Roundtable's
favor, in the same register (`planning/06` §1). Vocabulary follows `planning/06` §2.

**Claude drafts it; he reviews every section.** It is a technical document, not public prose in his voice, but it is
the one a hostile reader will quote. The release title is his (scope decision 2).

### 9.2 Its outline (against the scope doc's Delivers 2)

1. **What this is**, the question, and the claim tested.
2. **What was seen before this was written** (Delivers 2, "what was seen"): Phase 0.5's smoke calls on a neutral
   prompt; the Phase 2.5 step 6a diagnostics on garden content (Sonnet 4.6, Nova Lite, `gpt-oss-120b`, the local
   models); Phase 2's realism read and Phase 2.5's blind reader (other vendors' models, reading text, no decision);
   Phase 2.5's development runs on `gpt-oss-120b` and the Nova Lite runs, with the change log and the blind reports;
   **both honor statements quoted in full, with Claude's disclosure** (the S2 failure view named objectives;
   Phase 2.5 §22.3); the garden failure-rate runs (decision 3); every call counted (DoD 5's inventory).
3. **Who drafted the instrument** (Delivers 2): Claude drafted the dossier, scenarios and wordings from cited sources;
   he reviewed every line; the main model is from the same family; the independent readers and the second family
   answer it.
4. **The instrument:** the dossier, the four scenarios, the objectives and the three templates by hash, with the
   rendered text of one prompt per scenario as an appendix; the sealed template and its draw; the shuffles; the tool,
   validation (`planning/07` §2.4) and the statuses (§5.1), exactly as the instrument code implements them.
5. **The models** (§10): each model's ID, route, profile, region, the exact thinking and sampling fields, price and
   end-of-life as read on the day; the thinking sub-study's fields; the awareness-probe text (§3 item 8).
6. **The comparisons and verdicts:** the 16 primary comparisons per model, the secondary and descriptive ones, the
   thresholds, the three verdicts and "not assessable", the interval methods with alpha exact, decision 10's two rules.
7. **Failures:** retries, the 10% exclusion, a wording dropped from both sides, the worst-case bound both ways (or
   the softer bound, if decision 3 leads him there before the tag), first attempt beside final, refusal calls made
   blind and once (Phase 4's OPEN entry).
8. **Repeats:** the pilot (two development wordings, two repeats, excluded) and the rule as patched, the cap and what
   it cannot detect.
9. **Robustness:** wording, positions, the second family, the thinking sub-study, the awareness probe.
10. **The descriptive analyses.**
11. **The simulations,** quoted: what each verdict's error rates were measured to be, the share rule's 0.43% worst
    case beside the nominal 0.3125% (his finding A), what failures cost, reachability, power, the matcher's `D*`/`k*`
    and that "no good match" is rare.
12. **The real cases** (§9.3).
13. **What is published** (`planning/07` §12) and **run accounting** (§11, one sweep per study per model).
14. **The change policy** (scope decision 6), with a pointer to `errata-v1.md`.
15. **How to verify all of this** (§12's record): the tag, the ruleset, the archive's SWHID and visit date, the CI
    run, the lock and the commands that recompute every hash.

### 9.3 The real-case build rules, written out

Each is drafted in the protocol for his review; where a value is a choice, it is decision 6 or 7.

- **Selection** (`planning/07` §10.0, as decided): types and *k*, minimum and maximum, the window, the date rule,
  first-disclosure order, the "previously announced" check, independent reads of judgment rejections.
- **The search, query by query** (decision 6): for each channel (`planning/01` §4.2, §4.3, §4.7), the exact source,
  query text, form types, items, date range expression and SIC filter.
- **The scenario-shape rule**, applied to the first-disclosure document, first match wins: (1) a workforce change the
  document attributes to AI or automation software: S1; (2) a facility named for closure or sale, with or without new
  capacity elsewhere: S3 (with retool when new or converted capacity is named); (3) a multi-year program of stated
  annual cost, funded or declined: S4; (4) a restructuring with workforce or cost reductions and no facility named:
  S2. A document that matches none is rejected on criterion 4, and that rejection is independently read.
- **The dossier template per type**, section by section: the seven sections of `planning/07` §10.1 (overview,
  segments and facilities, workforce, financial position over three years, capital allocation history, the situation
  at the cut-off, the options plausibly open), each with what it must hold and what it may not (no post-cut-off
  figure, no outcome term), and which sections each shape needs.
- **The option-economics rule**, the uncertain-call rule, the replacement rule, the foreshadowing check and the
  neutrality checklist on case text, as decided (`planning/07` §10.1-§10.4).
- **The scaling factor** (decision 7): its range, its draw and its rounding.
- **Coarsening after a failed probe**, defined so it is not chosen case by case: regions widened one level, every
  remaining proper noun removed, figures rounded to two significant digits, distinctive events (a named lawsuit, a
  unique product) generalized; then one re-probe.
- **The recognition-probe text**, word for word, and what counts as naming the company.
- **The independent reader's role**, and the case mode's checks (§8).

## 10. The model set (decision 2)

### 10.1 What decides it

- **The set is fixed before real cases** (`planning/05` §3.1), and every model in it must answer on the official
  route before the tag (decision 5).
- **A model's format failure rate is a first-order input** (Phase 3 §20c finding C): at 20 a wording and a spread of
  0.2, a true 15-point difference is a split 84% of the time with no failures and 24% at 5%. Measured on garden
  shapes by decision 3.
- **End of life:** Sonnet 4.6 not sooner than 2027-02-17; real cases run in Phase 5.5 on the set.
- **Cutoffs and the window:** the strict window (after June 2026, preferably from August 1) already allows for every
  candidate's cutoff, Haiku 5.5's June 2026 included.
- **Cost:** Sonnet 4.6's grid at the cap is about $19 (`planning/07` §13). Haiku 5.5 is about a thirtieth of that per
  token on OpenRouter; Bedrock's own price is read on the day.

### 10.2 The candidates

| | Role today | For | Against |
|---|---|---|---|
| **Sonnet 4.6** | main, fixed 2026-10-05 | proven on the account (smoke calls); thinking off by leaving it unset; the design's costs and the simulations assume it | throttled with everything else; retires not sooner than 2027-02-17 |
| **Haiku 5.5** | candidate (OPEN, 2026-10-08) | about 1/30 of the cost; June 2026 cutoff; later retirement; a size-and-generation comparison inside one vendor | two days old; capability on this task unmeasured (aggregator scores only); likely on AWS's restricted list for new Claude models; thinking off needs an explicit field |
| **Nova Pro** | second family | the only other family on the account; in-region in us-east-1 | its billing line is shared with Musical Mycelium (tagged profile required, OPEN 2026-10-08); one malformed tool call in three smoke calls |
| **A newer Nova** | the `planning/09` §5 check | newer | Nova 2 Pro in preview only, as far as found; Nova 2 Lite global-routed |

### 10.3 Build-time facts, read on the day (build step 9)

For each candidate: the model card (ID, regions, profiles, lifecycle and end-of-life), Bedrock's price from the AWS
Price List, the account's quota, and **one neutral call on the official route** (Phase 0.5's smoke prompt, no
scenario). Recorded in `model-facts.md`. Nova Pro's `models.toml` entry is added with `route = "application_profile"`
and `inference_profile = "horizon-compact-nova-pro"`, with the test the OPEN entry asks for.

## 11. The independent review (scope decision 3; decision 7 picks the reviewer)

As `planning/08` and Phase 2's realism read were made. **Given:** the protocol document, `simulation-summary.md` and
`matcher-calibration.md`, the lock, and a one-page brief. **Asked:** what in this protocol would let a result be bent,
a claim overstated, or a verdict reached for a reason other than the data; what a hostile reader would attack first;
and where the protocol and the evidence disagree. **Not given:** any run record, or anything identifying a real case
(rule zero). **Kept:** the brief and the raw reply, verbatim, committed. **Each point** is marked confirmed, partly
right or rejected, with Claude's reason and his decision; accepted changes are made before the tag, a content change
through the change log with the hashes recomputed. One call, on Bedrock under the credits by default (decision 7
(i)); through his OpenRouter balance only if he chooses the stronger reviewer, with the cost shown before sending.

## 12. Tag day

The order, with who does what. Nothing on this list calls a model.

1. **The protocol commit `P`** (his): the final `protocol-v1.md`, the lock written by `hc protocol lock --write` from
   that tree, `make check` green. Pushed; **CI green on `P`** (its run id goes in the record).
2. **The ruleset** (his, GitHub settings, Rules, New tag ruleset): target `prereg-*`; restrict updates, restrict
   deletions, block force pushes; **no bypass list**. Created before the tag, so the tag is protected from its first
   moment. He reports what the page offered, and Claude reads it back with `gh api .../rulesets`.
3. **The tag** (his): `git tag -a prereg-v1 <P> -m "prereg-v1: protocol v1"`, then `git push origin prereg-v1`. The
   guard scans the tag name and message on push.
4. **The archive visit** (his command, one `curl` POST to Software Heritage's save endpoint, given on the day). Then
   Claude polls the status until `succeeded` and reads the snapshot: `refs/tags/prereg-v1` must point to `P`'s tag
   object and through it to `P`. A few hours for a known forge.
5. **The release** (his): on `prereg-v1`, title in his words, notes either empty or his; checked by him for names
   (the guard does not see text typed into GitHub).
6. **The gate's dry runs against the tag** (§7.2), from a worktree of `prereg-v1`, each message kept.
7. **The record commit `R`** (his): `tag-record.md` with `P`'s hash, the tag object's hash, the CI run id and time,
   the ruleset as read back, the SWHID and `visit_date`, the release URL and the dry runs; the DoD audit;
   `ROADMAP.md`; START HERE; version 0.3.5. `R` changes no frozen file, so `make check` stays green.

**If something goes wrong on the day:** a tag on the wrong commit, before anyone has run anything official, is
deleted (his, after removing the ruleset) and recreated, and `tag-record.md` says so plainly. After the archive visit
it cannot be quietly redone: the archive keeps both, and the record explains both.

## 13. Commits

He runs each one; short one-line messages, no attribution.

- **C1** `phase 3.5: implementation doc` — this doc after approval, with Phase 3's step 13 close-out (the four files
  already modified: `KNOWN-GAPS.md`, `ROADMAP.md`, the Phase 3 IMPLEMENTATION doc, `planning/07`), `ROADMAP.md`'s
  Phase 3.5 row, START HERE, and, once he has decided, the dated notes on the Phase 3.5 and Phase 5 scope docs
  (§3 items 10-11, decisions 6 and 7) and the `KNOWN-GAPS.md` OPEN entries his decisions change.
- **C2** `phase 3.5: model config split, decline pattern` — steps 1-2.
- **C3** `phase 3.5: frozen sets, lock and gate` — steps 3-6.
- **C4** `phase 3.5: garden shapes, nova lite and proxy runs` — steps 7-8, with their evidence.
- **C5** `phase 3.5: model facts and model set` — step 9 (needs AWS).
- **C6** `phase 3.5: protocol draft and review brief` — step 10.
- **C7** `phase 3.5: review and resolutions` — step 11.
- **P** `phase 3.5: protocol v1` — step 12; the commit the tag points to.
- **R** `phase 3.5: tag record and close-out` — steps 13-14.

## 14. Rules this phase must not break

- **No official model sees the company's content, any route, before the tag.** Garden content only (decision 3).
- **No run record on the company's content is opened.** The calls inventory reads manifests and summaries for
  counts, labels and models, never an attempt object; the Nova Lite runs are read only through the blind reports.
- **Nothing in the protocol is chosen by looking at a result.** There are none; the garden runs report failure counts
  and types only, and garden objectives carry no stakeholder or horizon contrast.
- **Rule zero:** no company in the protocol, the lock, the review brief, the tag message or the release.
- **No new number without its source.** Every quoted figure names its evidence file.
- **`make check` before every commit; CI green.** He runs `git commit`, `git push`, `git tag`, the ruleset and the
  release.

## 15. Decisions for him

Ten. Each has a recommendation and its cost.

**ALL TEN DECIDED 2026-10-09 (his), each as recommended**, on his two conditions: **(i)** OpenRouter spend capped at
**$5 in aggregate** for every remaining use in the project (reviews, development runs and, under the fallback below,
official runs); **(ii)** **no indefinite wait on AWS**, which decision 5 as decided turns into a dated fallback.
Decision 7 takes (i), `gpt-oss-120b` on Bedrock. The options stay as the record.

1. **What the tag freezes in code** (§3 items 1-3, §5).
   - (a) **Recommended:** three kinds of code: the **instrument** (`prompt.py`, `decision.py`, `classify.py`) and the
     **analysis** (`analysis/`, `experiment.py`) frozen; everything else run code. Before the tag, the model config
     moves out of `experiment.py` into `model_config.py`, and the `possible_decline` pattern is narrowed (it is in a
     frozen file). The official analysis runs from a checkout of the tag. **Cost:** about an hour of Sonnet for the
     split and the pattern; any later change to validation or retries is a new protocol version, by design; a
     run-record format change the tagged reader cannot read is too.
   - (b) The scope doc's literal reading: `analysis/` alone. The prompt frame and validation could then change after a
     result with no mark in any hash.
   - (c) The whole of `src/`. Any run fix (a throttling code, a provider bug) becomes a new version, which empties
     versioning of meaning (the scope doc's own reason against it).
2. **The model set** (§10). *His call: it reopens "Sonnet 4.6 is the main model, fixed".*
   - (a) **Recommended, as a procedure decided now and applied at build step 9 on the facts:** **Sonnet 4.6 stays the
     main model**; **Haiku 5.5 joins as a third official model** if it answers on Bedrock on this account, with its own
     grid sweep and real cases, no thinking sub-study; **Nova Pro stays the second family**; a newer Nova replaces
     Nova Pro only if it is generally available in a US route on the account. If Haiku 5.5 is not available on
     Bedrock, the set is Sonnet 4.6 and Nova Pro. **Cost:** about $1-2 more for Haiku's grid and cases (an estimate
     from OpenRouter's price; Bedrock's read on the day); one more model in every table; Haiku is so cheap it never
     reaches the cut list.
   - (b) Haiku 5.5 as the main model, Sonnet 4.6 dropped. Saves about $30 of the $80 ceiling and could buy more
     repeats, but rests on a capability nobody has measured on this task, on a two-day-old model, and spends the
     decision of 2026-10-05.
   - (c) As fixed: Sonnet 4.6 and Nova Pro only.
3. **The failure rate before the tag** (§3 item 5; his decision of 2026-10-09).
   - (a) **Recommended:** garden copies of all four scenario shapes (`experiment/shapes/`, off-subject, the
     placeholder's objectives), run on each model-set candidate **on Bedrock, under the credits, once quotas return**
     (Sonnet 4.6, Nova Pro, and Haiku 5.5 if the account has it; three repeats a cell, about 60 calls each), reported
     as failure counts and types only. **If every candidate's final failure rate is under 2%, the bound stays as
     built; if not, he decides the bound before the tag**, with the measured rates. **Cost:** about $2-3 of AWS credits
     (an estimate at Bedrock prices), **$0 cash**; Opus drafts the shapes (an hour or two, no AWS), he reviews them.
     **The limit, stated:** garden text is shorter than the company's and carries no subject that invites a refusal,
     so the proxy measures format failures and understates refusals. *The same runs through OpenRouter would cost him
     about $2-3 cash and buy no time.*
   - (b) No proxy: keep the bound as built and let the pilot report the real rate after the tag. Cheaper; the
     decision of 2026-10-09 then cannot be revisited on a measurement.
   - (c) Pre-register a conditional bound now, applied mechanically from the pilot's pooled failure rate. Uses the
     real rate, but adds a rule whose threshold is chosen today without data.
4. **The Nova Lite prerequisite** (§3 item 6).
   - (a) **Recommended: wait for Bedrock, as the OPEN entry says.** The 40 probes at 5 repeats and the format runs (4 ×
     5 × `w1`, `w3`) on Nova Lite through the blind reports, a failure type fixed by a logged change as in Phase 2.5
     step 15. **Cost:** under $0.15 of AWS credits, **$0 cash**. It delays nothing, since the tag waits on AWS anyway.
   - (b) Run it now through OpenRouter (`amazon/nova-lite-v1`). Under $0.25 of **his own money**, and it buys no time
     unless he also takes decision 5 (b).
5. **When the tag can be made** (§3 item 7).
   - (a) **Recommended:** only after **each official model has answered one neutral call on its official route**
     (build step 9). The protocol can be written, reviewed and approved while waiting. **Cost:** the tag waits on AWS,
     or on his fallback decision if Bedrock never returns.
   - (b) Tag as soon as the protocol is approved, and treat any later route change as `prereg-v2` before any official
     run. Faster; spends the clean v1 on a possible route change.

   **DECIDED 2026-10-09 (his): (a), with a deadline.** *The date is a tentative, very general timetable (his, 2026-10-09), Claude's proposal confirmed by him as the best
   balance of wait against decision time; **adjustable at his will as needed**, and moving it needs no protocol change.* **If Bedrock
   is not answering by Friday 2026-10-16 (tentative)** (one call each on Nova Lite and Sonnet 4.6, `scratch/throttle-check.py`,
   credits only), **the fallback set replaces decision 2's** and the tag proceeds without Bedrock:
   - **Haiku 5.5 the main model, `gpt-oss-120b` the second family**, both through OpenRouter, called **from the
     container** (Fargate tasks already get a public IP, `sweep/launch.py`), so official stays "a container run by
     image digest". The key lives in SSM Parameter Store (standard tier, free) and is read by the task role. A third
     OpenRouter path in the provider seam, with provider pinning (no silent fallback between backends) and the serving
     provider recorded per call. A design change, made and logged before the tag.
   - **Its money, estimated:** all of v1 on both models about **$3-4** (`gpt-oss-120b` about $0.0004 a decision,
     measured in Phase 2.5; Haiku 5.5 about $0.001, from list price), inside the $5 cap with about $1-2 of margin. To
     protect it: the thinking sub-study and Nova Pro are cut; the review uses `gpt-oss-120b`; decision 3's proxy runs
     on the two fallback models only (cents); decision 4's Nova Lite runs move to OpenRouter (under $0.25). **The
     harness's per-sweep caps are set so the project's OpenRouter total cannot pass $5**, and the cash ledger is
     read before every run.
   - **First, a few cents:** Haiku 5.5 on the garden shapes, to measure its failure rate before anything is fixed
     around it. If it fails often, he decides with the numbers in hand.
   - **What it gives up, stated in the protocol:** Sonnet 4.6 (the headline becomes a small current model and an
     open-weights model), Nova Pro, the thinking sub-study, and most of the budget's margin.
   - **If Bedrock returns after the fallback is taken but before the tag,** he chooses which set the protocol names;
     after the tag, a Bedrock set would be its own protocol version.
6. **The real-case search queries** (§3 item 10).
   - (a) **Recommended:** **frozen in the protocol**, query by query, with the shape rule and the coarsening rule of
     §9.3. Phase 5 runs them as written; a channel that has changed by then is reported, and its replacement query
     independently read. **Cost:** the queries are drafted now, months before use, and may need a reported deviation.
   - (b) Left to Phase 5's IMPLEMENTATION doc, as its scope doc says, written after the grid's results.
7. **Two values the protocol needs: the scaling factor and the reviewer.**
   - **The scaling factor (recommended):** drawn log-uniformly from **[0.6, 0.9] ∪ [1.1, 1.6]** per case, from a
     private recorded seed; dollars to three significant digits, headcounts to the nearest 5. The gap around 1 means
     no case keeps its real figures by chance; the range keeps a mid-size manufacturer mid-size. Alternative: any range
     he names, or [0.5, 2.0] without the gap.
   - **The reviewer.** The scope doc's decision 3 (approved) asks for another vendor's model and estimated $1-2,
     written before the no-cash default. Two ways to meet it:
     - **(i) Recommended for cost: `gpt-oss-120b` on Bedrock**, under the credits, **$0 cash**. It answered on this
       account in Phase 0.5's smoke calls (record 7). **The cost is in quality:** it is a smaller, open model, and a
       weaker reviewer finds fewer real problems in a document whose job is to survive a hostile reader. Other
       vendors' models on Bedrock are checked on the day; a stronger one is used if the account has it.
     - **(ii) `openai/gpt-6-astra` through OpenRouter**, the `planning/08` reviewer: the strongest reader available,
       about $1-2 of **his own money**. (`google/gemini-3.1-pro-preview`, about $0.50, if the set ever includes an
       OpenAI model.)
     His call on whether the protocol's review is worth a dollar or two of cash; (i) is the default.
8. **Where the protocol lives** (§4).
   - (a) **Recommended:** `experiment/protocol/`, beside the lock, so it is in the image and the container's gate
     hashes the document it enforces.
   - (b) `docs/protocol/`, with the document's hash checked only on the laptop.
9. **How the repeat count is checked** (§3 item 14, §7.4).
   - (a) **Recommended:** computed on the laptop from the pilot's records by the frozen `analysis/repeats.py`, written
     once to S3 under the pilot's prefix with its inputs, and enforced at launch; anyone can recompute it later.
   - (b) A pure-Python copy of the rule in the container with a frozen t table: the task recomputes it itself, at the
     price of two implementations that must agree.
10. **The case mode's proof of order** (§3 items 12-13, §8).
    - (a) **Recommended:** committed hashes, with the order shown by **a GitHub Actions run's created time before the
      first probe object's S3 `LastModified`**, both set by servers.
    - (b) Git commit dates: simpler, and set by the author, so they prove nothing to a stranger.

## 16. Order of work

Each step ends green under `make check`. Model choice in brackets (`CLAUDE.md`: Opus for design and review, Sonnet for
routine code; he switches with `/model`). **The code and text steps (1-6, the shapes' drafting in 7, and 10) need no
AWS. Every step that calls a model (the runs in 7 and 8, then 9 and 11) waits for Bedrock, so nothing costs his money.**

0. **C1** (him): this doc and the housekeeping in §13, after approval.
1. **[Sonnet] The model-config split** (decision 1) `[done]` 2026-10-09: `ModelConfig`, `ModelsFile`, `Prices` to `model_config.py`;
   imports updated; no behavior change; the placeholder golden test untouched; a test that `analysis/` imports
   nothing from `model_config.py`. *As built:* `model_config.py` carries its own small `_Strict` base (importing
   `experiment._Strict` would be circular); `experiment.py` imports the two classes it loads; `spend.py`, `runner.py`
   and one test import `Prices`/`ModelConfig` from the new module. Test: `test_analysis_imports_nothing_from_model_config`
   in `test_architecture.py`. 1206 tests with step 2.
2. **[Sonnet] The decline pattern** (OPEN, Phase 4) `[done]` 2026-10-09: narrowed so S4's option name alone does not flag, with tests both
   ways. C2. *As built:* `_DECLINE` in `sweep/classify.py` keeps `won't`, `will not`, `cannot`, `can't` and `unable to`,
   keeps a bare `refus` (no option is named that), and replaces the bare `decline` with "decline to" or "declining to"
   within 30 characters of an "I" in the same clause (Opus review: the first build had narrowed `refuse` too). Test:
   `test_an_option_named_decline_alone_is_not_a_decline_but_a_real_refusal_is`. `classify.py` is now final as an instrument file.
3. **[Opus] `protocol/sets.py`** `[done]` 2026-10-09: the three sets by pattern, the hash function, tests that each file is in exactly one
   set and that `__pycache__` and untracked files are not. *As built:* the universe is the package
   (`src/horizon_compact/`); instrument = the three exact paths, analysis = `analysis/**` and `experiment.py`, run =
   the rest; a file takes the first set it matches. Listing walks the disk and, where `.git` exists, keeps only what
   `git ls-files` lists (a git that cannot answer is an error, never "no filter"; `GIT_DIR` and its kin are ignored so
   a hook's environment cannot point it at another repository); without `.git` (the container) the pattern alone.
   A tracked file missing on disk drops out, and `unmatched_patterns` names a frozen pattern that matches nothing, for
   step 4's lock writer. A frozen set that lists empty is an error (wrong root). The hash is `code_hash`'s scheme,
   sorted by path string; `code_hash` itself is untouched, since the simulation results record its value.
   `protocol/` is run code: a change to its patterns changes a set's hash, which the gate then refuses.
   `tests/test_protocol_sets.py`, 20 tests: the real sets pinned file by file (instrument 3, analysis 13 today), the
   partition, the synthetic checkout and container trees, the hash both ways; five mutations of `sets.py` each
   caught. Checked live: the laptop tree and a `git archive` copy give the same two hashes.
   **Two findings.** (a) **Frozen code imports two run files**: `prompt.py` and `classify.py` import
   `providers/base.py` (the seam's types; `RawDecision.tool_call_count` and `tool_input` are logic `classify.py`
   reads), and `experiment.py` imports `model_config.py` (by design, §5.1). A run fix to `base.py` after the tag could
   change classification without touching a frozen hash. Built as decided (run code), with a test that allows exactly
   these two and fails on any new one. **Decided 2026-10-09 (his): `base.py` stays run code** (as recommended:
   `Provenance` lives there and Phase 4 may add fields to it, and every raw response is kept, so a classification can
   be recomputed from the record). A post-tag fix to `RawDecision`'s properties is logged with its effect on runs. (b) **No `.gitattributes`:** every package file is LF today (`git ls-files --eol`),
   and the image is built from CI's Linux checkout; a checkout with `core.autocrlf=true` would hash differently from
   the container and fail the gate closed. No change made; noted for step 4's message on a mismatch.
4. **[Sonnet] `protocol/lock.py` and `hc protocol lock --write` / `hc protocol check`** `[done]` 2026-10-09; `make check` runs the check;
   tests on a synthetic tree (absent lock passes; stale lock fails naming the file; errata file ignored).
   *As built:* `protocol/lock.py` builds the §6 lock from `sets.py` and the loaded experiment, writes it as TOML
   with a small sorted-key writer (no library), reads it back through a strict pydantic model, and checks a tree
   against it, reporting every difference. `hc protocol lock --model KEY ... [--write]` and `hc protocol check`
   are in `cli.py`; the Makefile's `protocol-check` is part of `check`, so CI runs it. `runner.py`'s
   `check_official` and `_lock_matches` are untouched (step 5 replaces them; the old reader refuses a §6 lock,
   the safe direction). `tests/test_protocol_lock.py`, 55 tests as built; ten mutations of `lock.py` each caught.
   Checked live in a scratch copy of the tree with a stand-in document: the writer's lock reads back and checks
   clean, and its analysis and instrument hashes equal step 3's.
   **Choices the doc did not spell out:** (1) `[content.files]`, `[instrument.files]` and `[analysis.files]` are
   sub-tables, one file per line, not the inline tables §6 sketches (same data; diffs show one file each); keys are
   sorted, so `lock_version` is not first. (2) `files` under `[content]` are `Experiment.file_hashes` without
   `models.toml`, whose hash the content hash does not cover either. (3) A set or content mismatch reports the
   per-file lines; the aggregate hash line appears only when no file line explains it. (4) Added and missing
   files are `... differs from prereg-v1: PATH (added)` or `(missing)`; a changed file has no suffix. (5) The
   writer needs at least one `--model` and refuses a duplicate silently by recording it once. (6) It also
   refuses a missing `uv.lock` or simulation-results file, since a lock without its record-only sources is
   incomplete. (7) `lock` without `--write` prints the lock and writes nothing, with every refusal applied. (8) The file is
   created exclusively, so a lock can never be replaced even by a race. (9) `sealed_template` is left out of
   `[content]` when the experiment has none (the placeholder), and the check compares absent with absent. (10)
   Region is recorded for the three Bedrock routes only, from `providers/bedrock.py`'s `REGION`. (11) `thinking`
   and `sampling` are written as `"not set"` for every model and **not compared by the check** (`models.toml` has
   no field to compare them with). **Step 9 must not leave this as is for Haiku 5.5**, whose request needs
   `thinking: {"type": "disabled"}` (§3 item 4): the lock would record the wrong request. (12) A hash mismatch adds
   a note that the lock hashes LF bytes (step 3's finding (b)). (13) The lock's `document` path is checked to be
   relative and free of `..` before it is read. (14) A content file that no longer loads is one failure line
   (`content: experiment ... does not load`), not a per-file list.
   **Opus review, 2026-10-09:** the code matches the brief and the choices stand. One fix: `tree_sha256` had hashed
   every file on disk under `experiment/company/`, untracked ones included, so a scratch file there on tag day would
   record a value no clean clone of the tag reproduces. It now goes through `git ls-files` like the code sets
   (`sets.tracked_files` takes the folder as a parameter, default unchanged), with a test that fails without it.
   56 tests in the file, 1282 in all.
5. **[Opus] `protocol/gate.py`** `[done]` 2026-10-09: §7.1's checks, `check_official` calling them, `--dry-run`, every refusal both ways
   as tests; `required_repeats` with synthetic pilot records (§7.4). *As built:* one function per check, `run_gate`
   runs all of them and reports every failure in check order, `check_official` raises them as one
   `official sweep refused: ...` line each. `runner.check_official` and its old one-field lock reader are gone
   (`cli.py` imports the gate); the checks reuse `lock.py`'s comparisons, made public for it. **Three things the
   section did not say:** (i) **what is hashed is what runs:** the root comes from the running package
   (`horizon_compact.__file__`, editable in the image too, pinned by a test on the Dockerfile), and an experiment
   loaded from any other folder is refused; check 3 compares the experiment in hand, not a fresh read of the disk.
   (ii) **The pilot vs check 4.** Phase 4's pilot runs the tagged content on Sonnet 4.6 with the two development
   wordings only, so "the plan uses the sealed template" would refuse it. Built as `pilot=True`: labeled `pilot`, the
   sealed template never included; a grid labeled `pilot` is refused. The command line does not offer it yet (Phase
   4, OPEN entry). (iii) **`required_repeats` takes the records, not a `RunSet`:** `(source, prefix, experiment,
   lock)`, since the label, content hash, model and templates it must check are in the manifest, which a `RunSet`
   does not carry. It refuses a label other than `pilot`, content or a model not the lock's, the sealed template, an
   unfinished run, and (through the reader) a pilot left under `development/`. It imports `analysis/repeats.py`
   (scipy) inside the function: a test runs `import horizon_compact.cli` with numpy, scipy and statsmodels blocked,
   as in the image. `RepeatDecision.as_record()` is `repeats.json`'s body (no mean, difference or objective; tested);
   the command that writes it and the launch's comparison with it are Phase 4's. **The launch:** `--official` runs
   checks 1-7 on the laptop, then refuses ("not wired yet"), so a mislabeled task can no longer start (OPEN entry of
   2026-10-07 updated). **The dry run** (`hc sweep run --official --dry-run`) needs `--official`, prints the plan and
   the notes, writes nothing and makes no AWS session (tested by snapshotting the tree). `tests/test_protocol_gate.py`,
   48 tests on a synthetic tagged tree (the company experiment, a lock for Sonnet 4.6): passes as tagged, the grid,
   price and run-code changes pass; refused on one byte in a scenario, `decision.py`, `verdict.py` and the document,
   on a model's profile, id or route, on a model outside the lock, on another experiment or experiment folder, on
   each sealed-template rule both ways, on a laptop; the pilot records written by the runner itself. Nineteen
   mutations of `gate.py`, each caught. The real-repository dry run is his to run (`.claude/settings.json` denies
   Claude `hc sweep run`); it refuses there today, since no lock exists. 1327 tests in all.
6. **[Opus] `protocol/cases.py`:** §8, with fake GitHub and store objects, both ways. C3.
7. **[Opus drafts, he reviews] `experiment/shapes/`** (decision 3): four garden scenarios with S1-S4's structural
   rules and the placeholder's objectives; `hc scenarios check` passes on them. **[his runs, needs AWS]** the proxy
   runs on Bedrock, one command per model; Claude reports counts and types from the blind reports only (`failure-proxy.md`).
8. **[his runs, needs AWS] Nova Lite on Bedrock** (decision 4): probes and format runs on the existing `nova-lite` entry;
   **[Opus]** any failure type fixed through the change log, probes re-run if text changed. C4. This closes the OPEN
   entry of 2026-10-07.
9. **[Opus, needs AWS] Model facts and the set** (§10.3, decision 2): live reads, one neutral call per candidate on
   its official route, Nova Pro's tagged entry and its test, the set written into `models.toml` and `model-facts.md`;
   **his decision on the bound** if decision 3's threshold was crossed. C5.
10. **[Opus] The protocol draft** (§9), section by section for his review; the review brief; the calls inventory
    (DoD 5's second half). C6.
11. **[Opus, needs AWS under 7 (i)] The review** (§11): his call to send; the raw reply kept; each point marked; his decisions; changes made.
    C7.
12. **[him, with Claude reading back] Tag day, steps 1-5** (§12). `P`.
13. **[Opus] Tag day, steps 6-7:** the dry runs against the tag, the S3 listing that nothing official exists (DoD 5),
    `tag-record.md`.
14. **[Sonnet] The close-out:** the DoD audit, `ROADMAP.md`, START HERE, version 0.3.5, the OPEN entries closed. `R`.

## 17. Definition of done, and the proof of each

| DoD (scope doc) | Proof |
|---|---|
| 1. The protocol is complete against Delivers 2, and approved | a table in the audit mapping each Delivers 2 item to its protocol section; his approval, dated |
| 2. The independent review is done and committed, every point resolved before the tag | `review-brief.md`, `review-raw.md`, `review-resolutions.md`, all in commits before `P` |
| 3. The tag exists, is protected, and has an outside timestamp that matches | `tag-record.md`: the tag object and `P`; the ruleset read back; the SWHID, its `visit_date` and the snapshot's `refs/tags/prereg-v1` resolving to `P` |
| 4. The gate passes the tagged content and refuses changed content or scoring code; the case mode both ways | the dry runs' messages from a worktree of the tag; the gate and case-mode tests in CI |
| 5. No official result exists; every model call accounted for | an S3 listing showing no object under the official prefix, with the command; `calls-inventory.md` by phase, model and label |
| 6. `make check` and CI green | the CI run ids on `P` and `R` |

## 18. Genuinely uncertain

- **When Bedrock returns.** Steps 9 and 12-13 wait on it under decision 5. If it does not, his AWS fallback comes
  first, and this doc's model set (§10) is revisited with it; nothing written before step 9 depends on the route.
- **Whether Haiku 5.5 is open to this account on Bedrock.** Probably not soon, on AWS's own reasoning about new Claude
  models; one call tells.
- **Whether a ruleset can be made with no bypass on a personal free account,** and whether the admin is listed as able
  to bypass regardless. Step 12 reads what the page allows and records it.
- **How long the archive visit takes.** "A few hours" for a known forge, by Software Heritage's own account.
- **Whether the garden proxy predicts the company's failure rate.** It should bound format failures from below in
  difficulty (shorter text) and says nothing about refusals; the pilot gives the real rate, reported beside it.
- **How long the protocol is.** Probably 700-1,000 lines; drafted in sections over more than one session.

## 19. Cost

**As recommended, $0 of his own money.**

| Item | Paid from | Estimate |
|---|---|---|
| Garden proxy runs (decision 3), up to three candidates | AWS credits | $2-3 |
| Nova Lite probes and format runs (decision 4) | AWS credits | under $0.15 |
| The independent review (decision 7 (i)) | AWS credits | under $0.10 |
| One neutral call per candidate on Bedrock (step 9) | AWS credits | under $0.05 |
| S3 listing, archive, ruleset, release | free | $0 |
| **Total** | | **about $2-3.50 of credits; $0 cash** |

**Cash only if he chooses it:** the review through `gpt-6-astra` (decision 7 (ii)), $1-2; the Nova Lite runs early
through OpenRouter (decision 4 (b)), under $0.25; the proxy through OpenRouter, $2-3. None of them makes the tag
come sooner while the tag waits on AWS. The credits are shared with Musical Mycelium; these amounts are small against
the $80 ceiling, and the harness's caps apply.
