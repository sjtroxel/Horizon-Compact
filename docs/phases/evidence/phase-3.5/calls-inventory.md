# Every model call before the tag: the inventory

Phase 3.5 build step 10 (DoD 5's second half; the IMPLEMENTATION doc §14). Written 2026-10-09 by Claude (Opus) from
**run manifests, session records' status counts, the blind reports and the phase documents only.** No attempt
object, final object or reply on the company's content was opened to write it. Session records hold status counts
and costs, no amount, choice, memo or objective.

**Counting rule.** A "call" is a request that reached a model and got an answer of any kind, including a malformed
one. A request refused before any model answered (throttling, an unrecognized key) is listed separately as "no model
answered". Where only attempts were counted, the number is given as an upper bound and says so.

To be completed before the tag: the garden failure-rate runs (step 7), the Nova Lite runs (step 8), the model-set
calls (step 9) and the review (step 11) add rows here.

## 1. Official models

| Model | Where | Content | Calls | No model answered | Source |
|---|---|---|---|---|---|
| Sonnet 4.6 | Bedrock, Phase 0.5 smoke | a neutral prompt (no scenario, no objective) | 3 (one with adaptive thinking) | 1 (throttled, 2026-10-05) | `docs/phases/evidence/phase-0.5/smoke/` 01, 03, 04, 10 |
| Sonnet 4.6 | OpenRouter, Phase 2.5 step 6a, rounds 5-6 | garden copies of the four shapes (off the subject) | 10, all valid | 0 | Phase 2.5 IMPLEMENTATION doc §17 step 6a |
| Nova Pro | Bedrock, Phase 0.5 smoke | the neutral prompt | 3 (one malformed tool call, `ModelErrorException`) | 0 | smoke 02, 05, 05.2 |
| Sonnet 4.6, Nova Lite | Bedrock, `scratch/throttle-check.py` | "Say ok." | 0 | every one, 2026-10-05 to 2026-10-08 (several runs, one call each per model; each refused with `ThrottlingException`, "Too many tokens per day") | `KNOWN-GAPS.md`, BLOCKED entry |

**No official model has been given any of the four scenarios, on any route.**

## 2. Development and diagnostic models

| Model | Where | Content | Calls | Source |
|---|---|---|---|---|
| Nova Lite | Bedrock, Phase 0.5 smoke | the neutral prompt | 1 | smoke 06 |
| Nova Lite | Bedrock, Phase 1 step 3 development run (`dev-nova-lite-bfd75b30`), the placeholder | garden | 0 (28 attempts, all `api_error`, throttled) | its session record |
| Nova Lite | OpenRouter, Phase 2.5 step 6a, rounds 5-6 | garden shapes | 18 | Phase 2.5 §17 step 6a |
| `gpt-oss-120b` | Bedrock, Phase 0.5 smoke | the neutral prompt | 1 | smoke 07 |
| `gpt-oss-120b` | OpenRouter, Phase 2.5 step 6a, rounds 5-6 | garden shapes | 19 | Phase 2.5 §17 step 6a |
| `gpt-oss-120b` | OpenRouter, `orcheck-gpt-oss-openrouter-4ee2f4c6` | the S4 shape test (garden) | 5, all valid | its session record |
| `gpt-oss-120b` | OpenRouter, comprehension probes `probes1`, `probes2`, `probes3` | **the company's content**: questions on what the text says, no decision asked | 20, 20, 10 (one call per scenario per repeat) | the probe reports in `docs/phases/evidence/phase-2.5/probes/` |
| `gpt-oss-120b` | OpenRouter, format runs `format1-gpt-oss-openrouter-29603836` | **the company's content**, templates `w1` and `w3` only | 80 (67 valid, 12 `schema_invalid`, 1 `no_tool_call`), plus 1 refused by OpenRouter before any model answered (HTTP 401) | its session records; the blind report |
| `gpt-oss-120b` | OpenRouter, `format2-gpt-oss-openrouter-bfc44abd` | **the company's content**, `w1` and `w3` only | 42 (40 valid, 1 `schema_invalid`, 1 `no_tool_call`) | its session record; the blind report |
| `qwen3.5:4b` (local, Ollama) | the placeholder, `qwenlocal-qwen-local-8cadb319` | garden | 15 (13 `sum_mismatch`, 1 `schema_invalid`, 1 `truncated`) | its session record |
| `qwen3.5:4b` (local) | the S4 shape test, `shape-qwen-local-27266cf6` | garden | 15 (10 `sum_mismatch`, 2 `schema_invalid`, 3 `truncated`) | its session record |
| `qwen3.5:4b`, `qwen3:8b` (local) | Phase 2.5 step 6a rounds 1-4 (`scratch/diagnose-s4shape.py`, `survey-shapes.py`) | garden shapes | 60 (32 in rounds 1-2, 28 in rounds 3-4), by the tables in the record | Phase 2.5 §17 step 6a |
| local models (Ollama) | Phase 0.5, `scratch/ollama_five.py` | the neutral smoke prompt | **not recorded** (run by hand, five a model, not kept as evidence) | the script |

**On the company's content, every call was to `gpt-oss-120b`, a development model, on the two development templates:
50 probe calls and 122 decision calls.** None used the sealed template `w2`; the harness refuses it outside the
official sweep. Those runs were read only through the blind reports, with the one disclosure and one exception in the
Phase 2.5 honor statements (protocol §2.4).

## 3. Readers (text read, no decision asked)

| Model | Where | What it read | Calls | Source |
|---|---|---|---|---|
| `openai/gpt-6-astra` | OpenRouter, Phase 2 realism read | the dossier and its assumptions; never a scenario or objective | 1 | `docs/phases/evidence/phase-2/realism-brief.md`, `realism-raw.md` |
| `google/gemini-3.1-pro-preview` | OpenRouter, Phase 2.5 blind reader | the four scenarios, the objectives and the templates; not told the question | 1 | `docs/phases/evidence/phase-2.5/reader-brief.md`, `reader-raw.md` |
| `openai/gpt-6-astra` | OpenRouter, `planning/08` design review | the planning documents, before any instrument text existed | 1 | `docs/planning/08a-REVIEW-BRIEF-gpt-6-astra.md`, `08b-REVIEW-RAW-gpt-6-astra.md` |

## 4. What this inventory cannot show

Calls made outside the harness and its scripts would not appear here; the honor statements cover them. The local
Ollama smoke runs of Phase 0.5 were not recorded. Claude, the drafter, is itself a model, and its drafting sessions
are not "calls" in this sense: it saw the text it wrote, and, by the honor statement, no reply on the company's
content.
