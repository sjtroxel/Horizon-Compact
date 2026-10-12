# Independent review of the protocol: the brief

Phase 3.5 build step 11 (scope decision 3; IMPLEMENTATION doc §11 and decision 7). Drafted 2026-10-09 by Claude
(Opus) in step 10; sent in step 11, once the protocol's bracketed values are filled, by him, as one call.

- **Reviewer:** *[Decided 2026-10-12 (his), on Opus's recommendation, replacing decision 7 (i)'s `gpt-oss-120b` on
  Bedrock:]* **Gemini 3.1 Pro (`google/gemini-3.1-pro-preview`) through OpenRouter, reasoning effort `high`,
  `max_tokens` 48,000, his OpenRouter cash.** Price read live 2026-10-12 21:30 UTC from OpenRouter's endpoint list:
  $2 input and $12 output per million tokens on the standard endpoints (a "flex" tier at $1 and $6 is also offered;
  the host that serves it is recorded). Likely about $0.36, worst case about $0.71 (both with the fee). Why not the others: Bedrock is
  unavailable; `gpt-oss-120b` became the second family on 2026-10-12, so it would be reviewing a study of itself, and
  it is the weakest of the candidates; `openai/gpt-6-astra` costs about four times as much. Not Anthropic (the
  drafter's and main model's vendor). Gemini 3.1 Pro was Phase 2.5's blind reader, so it has read the scenarios'
  text, never a decision.
- **Sent with it, as attached files, nothing else:** `experiment/protocol/protocol-v1.md` (as filled for the tag),
  `docs/phases/evidence/phase-3/simulation-summary.md`, `docs/phases/evidence/phase-3/matcher-calibration.md`, and the
  lock **as printed** by `hc protocol lock --model haiku-5-5 --model gpt-oss-openrouter` on the review's commit.
  *[Amended 2026-10-12 (Opus): not `--write`. A written lock can never be replaced, and the review may change the
  protocol; the real lock is written on tag day. The printed lock is kept as `review-lock.txt`.]* Sent by
  `scratch/send-review.py`, which refuses if any sent file is uncommitted and records the commit and each file's
  sha256 in `review-raw.md`.
- **Never sent:** any run record, any reply on the company's content, the private case longlist, or anything that
  identifies a real company (rule zero).
- **Kept:** this brief and the raw reply, verbatim, as `review-raw.md`. Each point is marked confirmed, partly right
  or rejected in `review-resolutions.md`, with Claude's reason and his decision. Accepted changes are made before the
  tag; a change to what a model reads goes through the change log, with the hashes recomputed.

<!-- EVERYTHING BELOW THIS LINE IS SENT, AS ONE USER MESSAGE, WITH THE FOUR FILES ATTACHED -->

You are reviewing a pre-registration protocol before it is frozen. The attached protocol describes an experiment in
which one language model is given the same fictional company and the same four capital-allocation decisions, under
five different objectives set by its board, to test whether the objectives change its decisions. Two simulation
reports measure the error rates of the protocol's verdict rules on synthetic data. The lock file holds the hashes of
everything the protocol freezes.

The protocol will be published, and its results quoted by people who want them to say opposite things. Your job is to
find where it is weak before they do. Agreement is not useful: if you think a likely objection fails, say why. "No
problem found" is a valid answer for a part only with a reason.

Answer three questions:

1. **What in this protocol would let a result be bent, a claim overstated, or a verdict reached for a reason other
   than the data?** Look in particular at: the choices the authors can still make after seeing results; the failure
   and exclusion rules; the rules for when runs agree; how the repeat count is set; how the real cases are found,
   chosen, built and matched; what is frozen and what is not; and anything a verdict depends on that is not stated
   exactly.
2. **What would a hostile reader attack first,** on each side: someone who wants the results to show that the
   objectives make no difference, and someone who wants them to show that they do?
3. **Where do the protocol and the simulation reports disagree,** or where does the protocol state a number, a
   property or a guarantee the reports do not support?

For each point: say where it is (section and sentence), what the problem is, how serious it is (would change a
verdict / would mislead a reader / minor), and a one-line suggested change. Number the points. End with a short list
of what you checked and found sound, with the reason for each.
