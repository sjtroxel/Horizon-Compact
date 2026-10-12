# The garden-shape failure proxy (decision 3)

Phase 3.5 build step 7, run 2026-10-12 under the fallback set (§23.8 step 7): Haiku 5.5 through Anthropic's API and
`gpt-oss-120b` through OpenRouter (pinned to `deepinfra/bf16`), each as a Fargate task. Written by Claude (Opus)
**from the blind reports and session records only**: counts and failure types, never an amount, choice or memo.

**The rule (decision 3, approved 2026-10-09):** if every candidate's **final** failure rate is under 2%, the bound in
protocol §7.4 stays as built; if not, he decides the bound before the tag, with these rates.

**What this measures and what it does not.** The shapes (`experiment/shapes/`) carry each scenario's form and none
of its content: garden text, the placeholder's objectives, one template (`w1`), three repeats a cell. Garden text is
shorter than the company's and carries no subject that invites a refusal, so **this measures format failures and
understates refusals**. Sixty runs is a small sample: no failure in 60 says the true rate is probably under about 5%
(the rule of three), not that it is zero.

## Haiku 5.5 (`proxy-haiku-5-5-70ef2152`)

Command (his): `hc sweep launch --experiment shapes --model haiku-5-5 --repeats 3 --seed 20261012 --label proxy`.
One session, `complete`, 64 attempts, **$0.0653 of the Console credit**. Blind report:
`docs/phases/evidence/phase-2.5/format/proxy-haiku-5-5-70ef2152.md` (and `-failures.md`; the report command writes to
Phase 2.5's folder, its fixed location).

| Shape | Runs | Valid (final) | Valid on the first attempt |
|---|---|---|---|
| `garden_s1` | 15 | 15 | 15 |
| `garden_s2` | 15 | 15 | 14 |
| `garden_s3` | 15 | 15 | 13 |
| `garden_s4` | 15 | 15 | 14 |
| **All** | **60** | **60 (final failure rate 0%)** | **56 (first-attempt failure rate about 7%)** |

**The four failed first attempts, by type** (each fixed by its run's next attempt; from the failures view):
- `schema_invalid`, an amount above its line's cap: 2, both `garden_s3`.
- `schema_invalid`, an amount put on a line that was not offered: 1, `garden_s2`.
- `sum_mismatch`, the amounts not summing to the total: 1, `garden_s4`.

None read as a decline; none named the tool in text; no `no_tool_call`, no `truncated`. Every objective's cell has 3
of 3 valid.

**Against the rule: under 2% final. For Haiku 5.5, the bound stays as built.** The first-attempt rate is reported
beside the final one, as protocol §7.5 requires, and it costs retries: about 7% more calls than runs.

## `gpt-oss-120b` (`proxy-gpt-oss-openrouter-5ead7b2e`)

Command (his): `hc sweep launch --experiment shapes --model gpt-oss-openrouter --repeats 3 --seed 20261012 --label
proxy`, run twice. Two sessions: `stopped: max_minutes` at the 30-minute default (33 attempts, 23 runs), then,
re-launched with `--max-minutes 90`, `complete` (67 attempts). 100 attempts in all, **$0.0218 of his OpenRouter cash**.
Blind report: `docs/phases/evidence/phase-2.5/format/proxy-gpt-oss-openrouter-5ead7b2e.md` (and `-failures.md`).

| Shape | Runs | Valid (final) | Valid on the first attempt |
|---|---|---|---|
| `garden_s1` | 15 | 15 | 15 |
| `garden_s2` | 15 | 15 | 15 |
| `garden_s3` | 15 | 15 | 15 |
| `garden_s4` | 15 | 15 | 13 |
| **All** | **60** | **60 (final failure rate 0%)** | **58 (first-attempt failure rate about 3%)** |

**The three failed model attempts, by type**, all on `garden_s4`, each in a run that ended valid:
- `schema_invalid`, the tool call carrying the amounts only, without the choice or the memo: 1.
- `sum_mismatch`: 2, both in one run (its first and second attempts; its third was valid).

No text outside the tool call on any of them; no `no_tool_call`, no `truncated`. Every objective's cell has 3 of 3
valid.

**The other 37 attempts were `api_error`**, not model answers, and are not in either rate. The first 10, read from
their records, were all **HTTP 429 `ThrottlingException` from the pinned host** (the pin allows no fallback), each
with a cost of $0; the later 27 were counted by the status command and not opened. They grew as the day went on
(10 in the first 30 minutes, 27 in the next hour).

**Against the rule: under 2% final. For `gpt-oss-120b`, the bound stays as built.**

## The result

**Both candidates' final failure rate is 0 of 60, under 2%: by decision 3, the bound in protocol §7.4 stays as
built**, and that subsection's bracketed note is settled by this file. First-attempt failure rates, reported beside
the final ones: about 7% (Haiku 5.5, 4 of 60) and about 3% (`gpt-oss-120b`, 2 of 60). Of the seven failed model
attempts, six were on `garden_s3` and `garden_s4` and one on `garden_s2`: a cap exceeded, a total that did not sum, a
line not offered, a choice left out. None was a decline; refusals are what this proxy cannot measure.

## For Phase 4's runs half (not a decision here)

- **`gpt-oss-120b` is slow and throttled on its pinned host.** Valid calls took 24 to 175 s, median 74 s (Phase 1's
  run, 2026-10-11: 28 to 63 s), plus 429s. At grid scale (over a thousand calls) that is more than a day of task time,
  so the runs-half doc plans its time limits, its pacing and whether the pin stays.
- **Haiku 5.5's retry rate** (about 7% on these shapes) belongs in that doc's cost projection.
