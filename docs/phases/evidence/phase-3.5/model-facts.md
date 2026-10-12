# Model facts for the official set (Phase 3.5 build step 9, facts half)

Written 2026-10-12 by Claude (Sonnet 5.5), under the fallback set (Phase 3.5 IMPLEMENTATION doc §23): Haiku 5.5 through
Anthropic's API as the main model, `gpt-oss-120b` through OpenRouter as the second family. **Facts only.** No call was
made for this file (cost $0); the call facts are copied from the runs that already happened and cited. `models.toml`
and the protocol's §5 bracket are not touched by this file; the role change is scoped separately (see the end).

Every live read below carries its URL and the date read (2026-10-12 unless said). Where a number is compared with
`experiment/models.toml`, "same" means equal to the entry as it stands today.

## What this file does not cover, and why (the Bedrock items)

§10.3 asks, for each candidate, for the model card, **Bedrock's price from the AWS Price List**, the account's quota,
and **one neutral call on the official route**; and for Nova Pro's tagged `models.toml` entry. Under the fallback
set these are dropped, as follows:

- **The AWS Price List, inference profiles, the region and the Bedrock quota:** §23.1 and §23.3 ("Does not change ...
  only Bedrock is dropped") and decision 5 (2026-10-09). Neither official model is reached through Bedrock.
- **Nova Pro, its tagged profile entry and its test:** cut from the set by decision 5 (§23.1: "the thinking
  sub-study and Nova Pro cut"). Sonnet 4.6 likewise is replaced as main (§23.3: "the main model (Sonnet 4.6 to Haiku
  5.5)"); its `models.toml` entry is a leftover that Opus scopes (below).
- **The neutral call on the official route:** replaced as §23.8 step 5 says. No laptop call was made (the key
  exists only in SSM); Phase 1 step 9 on Haiku 5.5 in Fargate stands in for it (Phase 1 doc §21a). For
  `gpt-oss-120b` the stand-ins are Phase 1 §21 and `failure-proxy.md`.
- **Still applies, and is not in this file:** §23.8 step 8's prerequisite (Nova Lite probes and format runs). Nova
  Lite is a development model, not an official one.

## 1. `haiku-5-5` (main), route `anthropic`

| Fact | Value | Source, read | Against `models.toml` |
|---|---|---|---|
| Model ID | `claude-haiku-5-5`; "every Claude model ID is a pinned snapshot, including the dateless IDs" | https://platform.claude.com/docs/en/models/overview and .../models/haiku-5-5/overview, 2026-10-12 | same (`model_id`) |
| Route | Anthropic's own API (Claude API), key from SSM `/horizon-compact/anthropic-key` in the container; workspace `horizon-compact`, $10 monthly limit (§23.5 G) | §23.5 B, G; Phase 1 §21a | same (`route = "anthropic"`) |
| Released | 2026-10-07 | haiku-5-5 overview, 2026-10-12 | n/a |
| Status and retirement | Active (latest); **not sooner than 2027-10-07**; Anthropic gives at least 60 days' notice before retiring a publicly released model | https://platform.claude.com/docs/en/about-claude/model-deprecations, 2026-10-12 | n/a (not in the file); same as §23.2 |
| Context window, max output | 1M tokens; 128K tokens (synchronous API) | models overview, 2026-10-12 | n/a (not in the file) |
| Knowledge cutoff | reliable: June 2026; training data: June 2026 | models overview, 2026-10-12 | n/a; same as §23.2 |
| Thinking, effort | adaptive thinking on by default; default effort `medium` | models overview, 2026-10-12 | `thinking = "off"` sends `thinking: {type: disabled}`, effort not sent (§23.5 C) |
| Sampling | `temperature`, `top_p`, `top_k` must be omitted (400 on non-default values) | haiku-5-5 overview "Good to know"; deprecations page, 2026-10-12 | n/a; the design never sets sampling |
| Tokenizer | the newer one, about 30% more tokens than Haiku 4.5 for the same text | haiku-5-5 overview, 2026-10-12 | n/a |
| **Price, prompt up to 100,000 tokens** | **$0.10 input, $0.50 output** per million; cache read $0.01; 5-minute cache write $0.125 | https://platform.claude.com/docs/en/about-claude/pricing and the haiku-5-5 overview, 2026-10-12 | **same**: `input = 0.10`, `output = 0.50`, `cache_read = 0.01`, `cache_write_5m = 0.125` |
| Price, prompt over 100,000 tokens | 5x: $0.50 input, $2.50 output; cache read $0.05; 5-minute write $0.625. The prompt length counts cache reads and writes; each request is priced on its own | pricing page, 2026-10-12 | **Not in `models.toml`** (one price set only). The grid's prompts are about 8,000 tokens; matters only for long dossier extraction (§23.2) |
| Batch API | 50% off; not used (§23.5 E) | pricing page, 2026-10-12 | n/a |
| Data-residency multiplier | US-only inference (`inference_geo`) costs 1.1x; the records show `inference_geo` "global", so no multiplier applies | pricing page, 2026-10-12; Phase 1 §21a | n/a |
| Lifecycle compared with Sonnet 4.6 | Sonnet 4.6: not sooner than 2027-02-17 (same page) | model-deprecations, 2026-10-12 | n/a |

**Differences from `models.toml`, from §23.2, or from any earlier reading: none found.** The prices, the model ID, the
retirement date and the knowledge cutoff match the 2026-10-11 reading. Two small additions to §23.2's table, not
differences: the context window and max output are now written down (1M, 128K), and the long-prompt tier's cache
prices are written down ($0.05 read, $0.625 five-minute write).

**Quota.** Not re-read here (it is his Console, not a public page). The reading of 2026-10-12, already in
`models.toml`'s comment and in `KNOWN-GAPS.md`: his organization's Scale tier showed 10K requests, 10.0M input and 2.0M
output tokens for this model (the unit as recorded there; read as per minute, the Console's usual unit, not
re-checked) (Console, Rate limits page, workspace `horizon-compact`). `models.toml` paces
at `requests_per_minute = 60` (times `pace_fraction` 0.8), far under it. §23.2's table said "Start tier" as a
possibility; the Console showed Scale, so §23.2's tier row is superseded by this reading.

**Neutral-call facts (copied from Phase 1 IMPLEMENTATION doc §21a, the stand-in for the laptop call per §23.8 step 5;
nothing re-run).** Sweeps `skeleton-haiku-5-5-f1467906` (15 runs, $0.0140) and `stoptest-haiku-5-5-c61e6830` (50 runs,
$0.0481), the placeholder, Fargate, image digest `sha256:ef2582ed...1d16f02` (built from `8ab367c`), 65 of 65 `valid`:

- `thinking: {type: disabled}` is **accepted** at the default effort (effort not sent) on all 65 calls; every request
  carries it; `thinking_tokens` 0 and `reasoning_block_count` 0 on all 65. Settles §23.2's "not verified" item.
- `tool_choice` `auto`; `stop_reason` `tool_use` on all 65. Served model `claude-haiku-5-5` on all 65; a unique
  request ID per call; `inference_geo` "global"; `service_tier` "standard"; no cache tokens read or written;
  temperature not sent.
- Tokens per call on the placeholder: input 2,998 to 3,013, output 1,030 to 1,643. Cost per call $0.0008 to $0.0011
  (one attempt recomputed by hand from `models.toml`'s prices, $0.000852, equal to the record's). Latency 5.3 to 9.0 s,
  median 6.6 s (skeleton) and 6.9 s (stoptest).
- The placeholder prompt is about 3,000 tokens, not the grid's expected 8,000, so these per-call costs understate the
  grid's. The garden-shape proxy (`failure-proxy.md`): 64 attempts, **$0.0653** of the credit, 60 of 60 valid, first
  attempts failing about 7% (4 of 60).
- Memos run past the 300 words the prompt asks for in 7 of 15 and 17 of 50 attempts (225 to 350 words); not validated
  or scored (Phase 1 §21a, an observation).
- Spent so far of the $18.19 credit: about $0.0621 (Phase 1 step 9) plus $0.0653 (proxy), that is about $0.12 ($0.1274), by the
  records' own cost field, **not from the Console's bill** (DoD 7, the bill, is not done).

## 2. `gpt-oss-openrouter` (second family), route `openrouter`, pinned `deepinfra/bf16`

Read 2026-10-12, about 18:45 UTC, from OpenRouter's public endpoints API, no key:
`https://openrouter.ai/api/v1/models/openai/gpt-oss-120b/endpoints`.

| Fact | Value | Against `models.toml` |
|---|---|---|
| Model ID | `openai/gpt-oss-120b`; "an open-weight, 117B-parameter Mixture-of-Experts (MoE) language model from OpenAI ... activates 5.1B parameters per forward pass" (the card's description, truncated by the API) | same (`model_id`) |
| Card | tokenizer `GPT`, text in, text out; created 1754414231 (2025-08-05 UTC, from the API's Unix timestamp) | n/a |
| Pinned endpoint | provider DeepInfra, tag `deepinfra/bf16`, quantization `bf16`, context 131,072, max completion 117,964, status 0 (the API's value; read as no reported fault, not looked up further) | same (`openrouter_provider = "deepinfra/bf16"`) |
| **Price at that endpoint** | **$0.000000037 per input token, $0.00000017 per output token**, that is **$0.037 and $0.17 per million**; **no cache-read price listed** | **same**: `input = 0.037`, `output = 0.17`. `cache_read` and `cache_write_5m` are `0.037` (the input price), as the file's comment says: a cached prompt is counted at the input price, an overestimate |
| Parameters the endpoint lists | includes `tools`, `tool_choice`, `structured_outputs`, `response_format`, `reasoning`, `reasoning_effort`, `seed` | n/a |
| Other DeepInfra endpoint | `deepinfra/turbo`, $0.15 and $0.60 per million, max completion 16,384: a different, dearer endpoint; **not the pinned one** | n/a |
| Cheaper endpoints exist | Venice, CoreWeave, DekaLLM and AkashML list $0.03 input, with outputs of $0.15 to $0.187. The pin is to the endpoint the instrument was developed and measured on, not the cheapest | n/a |
| Lifecycle | an open-weights release; no retirement date applies to the weights. **The pinned host's availability is OpenRouter's and DeepInfra's to change**; no end-of-life statement was found, and none is claimed | n/a |

**Added 2026-10-12, about 19:45 UTC (Opus, for protocol section 5), from OpenRouter's models API
(`https://openrouter.ai/api/v1/models`, the `openai/gpt-oss-120b` entry, no key) and the endpoint entry above:**

| Fact | Value |
|---|---|
| Reasoning | `"reasoning": {"mandatory": true, "supported_efforts": ["high", "medium", "low"], "default_effort": "medium"}`: **it cannot be turned off**; OpenRouter's reasoning docs say a model marked mandatory rejects `effort: "none"` (https://openrouter.ai/docs/use-cases/reasoning-tokens, read 2026-10-12). The harness sent no reasoning field until 2026-10-12, so every call before that ran at OpenRouter's default; **since Phase 3.5 section 25 it sends `reasoning: {effort: "medium"}` explicitly, recorded in the lock; DeepInfra accepted it on 5 of 5 answered calls on 2026-10-12 (§25.5)** |
| Knowledge cutoff | `"knowledge_cutoff": "2024-06-30"` (OpenRouter's listing) |
| Expiration | `"expiration_date": null` |
| Pinned endpoint caching | `"supports_implicit_caching": false` (settles Phase 1 section 21's open question: DeepInfra does not cache this prefix) |
| Pinned endpoint uptime | 100% over the last 30 and 5 minutes, about 98.7% over the last day, at the time read |

**Differences from `models.toml`: none.** The prices, the model ID and the pin match; `models.toml`'s comment says the
prices were first read 2026-10-07 and the endpoint checked 2026-10-11, and today's read agrees.

**Quota.** OpenRouter publishes no per-model request quota on this API; the file's `requests_per_minute = 20` is the
harness's own cap. What was **observed** is throttling on the pinned host, below. No limit is claimed beyond that.

**Call facts (copied; nothing re-run).**

- Phase 1 IMPLEMENTATION doc §21, steps 9 and 11, 2026-10-11 (the placeholder as a Fargate task, sweep
  `skeleton-gpt-oss-openrouter-78a37f95`): 15 of 15 `valid`, `stop_reason` `tool_use`, amounts sum to 3000 in each;
  the request carried `allow_fallbacks: false, order: [deepinfra/bf16]`; every reply `served_by: DeepInfra`, no
  `ProviderMismatch`; 27,864 input and 13,625 output tokens; **$0.003349** in all; latency 28 to 63 s a call; no cache
  tokens reported on any attempt (whether DeepInfra caches this prefix is not known). His OpenRouter cash.
- `failure-proxy.md`, 2026-10-12 (garden shapes, two sessions): 100 attempts in all, **$0.0218 of his OpenRouter
  cash**; 60 of 60 valid, first attempts failing about 3% (2 of 60: one `schema_invalid`, one run with two
  `sum_mismatch`); valid calls took 24 to 175 s, **median 74 s**; **37 of the 100 attempts were `api_error`, HTTP 429
  `ThrottlingException` from the pinned host** (the pin allows no fallback), the 10 read from their records each
  costing $0 and the other 27 counted by the status command and not opened; the 429s grew through the day (10 in
  the first 30 minutes, 27 in the next hour). The first session hit the 30-minute default and was resumed with
  `--max-minutes 90`.
- Cost per call about $0.0004 (Phase 2.5, cited in §23.4), not re-measured here.
- Disclosure that belongs beside any of its results: it is the model the instrument's text was developed on
  (protocol §2.4 and §9.4 drafts; §23.5 H dated note).

## What to read from this file

Both entries' prices, IDs and pin agree with `models.toml` as of today; nothing in them needs correcting. The new
facts are the context windows, the over-100,000-token price tier (Haiku), and the throttling and latency of the pinned
`gpt-oss-120b` host, which bears on Phase 4's runs half, not on this file.

## Scoped, not done: what the role change would touch (read-only, no edit made)

*Update, 2026-10-12: the role change was approved and built as Phase 3.5 IMPLEMENTATION doc section 24 (see §24.6
there). This section is kept as the read-only scoping it was written as; where it says "no edit made", it was true
when written.*

`models.toml` today: `sonnet-4-6` `role = "main"`, `haiku-5-5` and `gpt-oss-openrouter` `role = "development"`.

**Where `role` is read in `src/`** (`grep` over `src/`, 2026-10-12; a grep, not proof of absence):

1. `sweep/runner.py:107-117`, `check_route`: **if `role == "main"` and `HC_SONNET_ROUTE` is set and differs from the
   model's `route`, the session refuses.** Called from `cli.py:576` (`sweep run`) and `cli.py:784` (the awareness sweep). The task
   definition always sets `HC_SONNET_ROUTE` (`infra/terraform/main/ecs.tf:37`, from `var.sonnet_route`, which is
   validated to be `application_profile` or `geo_profile` only, `variables.tf:33`; CI passes the repository variable
   `SONNET_ROUTE`, `.github/workflows/deploy.yml:130`). **So if `haiku-5-5` becomes `main`, every Haiku session in the
   container refuses**: `HC_SONNET_ROUTE` is `application_profile` and Haiku's route is `anthropic`. (Phase 4 code
   half doc line 286 and `models.toml`'s own note anticipate this: "a `main` role would also need the task
   definition's route variable".) Fixes are for Opus to scope; the options are to make `check_route` compare only
   Bedrock-route models, to key it on the route rather than the role, or to rename the variable and loosen the
   validation. No edit made.
2. `sweep/plan.py:236-243`, `check_not_official_rules`, and `probes/run.py:60-68`, `check_probe_model`: **any role
   other than `development` is refused real content** (anything not in `OFF_SUBJECT_EXPERIMENTS`, which holds the
   placeholder and `shapes`), for a non-official plan and for every probe.
   *Corrected by Opus in review, 2026-10-12:* the draft said any development run of Haiku on the company's content
   "must happen before the role changes". **That is backwards: no such run may happen at all.** Haiku 5.5 is an
   official model under the fallback set, and the order of operations forbids anyone seeing an official model's
   decision on a pre-registered scenario before `prereg-v1`. **Measured, not inferred:** `hc sweep plan --experiment
   company --template w1 --repeats 1` (local, no call) on 2026-10-12 **accepts `haiku-5-5` and `gpt-oss-openrouter`
   (20 runs each) and refuses `sonnet-4-6`** ("is not the development model"). So the code's guard on the one-way
   door still protects the old main model and **protects neither model of the set that will be pre-registered**;
   today only process stands in front of it. The role change is what re-arms the guard, and that is its main
   purpose, not bookkeeping. For `gpt-oss-120b`, the Phase 2.5 runs it already made are disclosed (protocol §2.4,
   §9.4 drafts); a role other than `development` stops more of them, which is wanted now that it is official.
3. `protocol/lock.py:199, 434`: `role` is part of each locked model's identity and is compared with `models.toml` on
   every gate check. **A role changed after the lock fails the lock (`COMPARED_IDENTITY`)**, so the roles must be set
   before `prereg-v1`; a role change after the tag is a new protocol version.
4. `protocol/gate.py` (`check_model`, line 178): picks official models from the lock by key; I found **no use of
   `role` in `gate.py`**. The gate never reads `main`.
5. `sweep/runner.py:58-67`: `ROLES = ("development", "pilot", "official")` is the **S3 prefix and record label**
   (`development/`, `pilot/`, `official/`), a different thing from `models.toml`'s `role`, which is a free string
   (`model_config.py:33`, `role: str`, no enum). Nothing here changes by renaming a model's role. A role string a
   later reader treats as a value (for example `second`) is unchecked by any code.

**`infra/`:** only `ecs.tf:37-38` (`HC_SONNET_ROUTE`, `HC_SONNET_PROFILE_ARN`), `variables.tf:23-35` (`sonnet_route`,
Bedrock routes only, no default, test `test_main_requires_the_route_and_the_digest_with_no_default`) and `iam.tf:12-26`
(the Bedrock resources) name the Sonnet route. The task and boundary policies already carry the Anthropic key's SSM and
KMS grants (`infra/iam/task.json:32,42`; `boundary.json:38,48`) and no OpenRouter or Anthropic route variable. Nothing
in `infra/` reads a model's `role`. The route variable could stay set as it is if `check_route` is changed so that it
ignores non-Bedrock models; it need not be removed. No edit made.

**Tests that cover or would break** (a grep for `role`, `HC_SONNET_ROUTE` and `sonnet-4-6` in `tests/`):

- `tests/test_sweep_runner.py:407-416`: `check_route` on `sonnet-4-6` (mismatch refused, match and unset pass) and on
  `nova-lite` (ignored). This is the test for item 1; it reads the **real** `models.toml`, so it fails if
  `sonnet-4-6` stops being `main` and is the one to rewrite for a Haiku `main`.
- `tests/test_sweep_cli.py:112-121`: the CLI refuses a route mismatch with `HC_SONNET_ROUTE` set; uses the default
  plan args (`sonnet-4-6`).
- `tests/test_anthropic_provider.py:503`: asserts `haiku-5-5` `role == "development"` "until the protocol names it
  the main model (build step 9)": **a deliberate tripwire that fails on the change**.
- `tests/test_openrouter_provider.py:360-366`: asserts `gpt-oss-openrouter` has role `development`; fails if its role
  changes.
- `tests/test_protocol_lock.py:36, 269-323` (and its `locked` fixture): builds the lock from the **real**
  `models.toml` with `MODEL = "sonnet-4-6"` and asserts its locked identity, role `main` included. About 20 test files
  name `sonnet-4-6` (`grep -ln`); removing the entry would break many, and editing only its role breaks at least this
  one.
- `tests/test_experiment.py:261` pins `qwen-local`'s role (untouched by this change).
- **Not covered by any test I found:** a `main` role on an `anthropic`-route model (nothing exercises item 1's
  refusal for Haiku), and the claim that the real-content refusals (item 2) hold for `second`-type roles.

I ran nothing against these; the above is from reading the code and the test files.
