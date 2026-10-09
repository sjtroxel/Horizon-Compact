# Independent review of the protocol: the brief

Phase 3.5 build step 11 (scope decision 3; IMPLEMENTATION doc §11 and decision 7). Drafted 2026-10-09 by Claude
(Opus) in step 10; sent in step 11, once the protocol's bracketed values are filled, by him, as one call.

- **Reviewer:** by decision 7 (i), **`gpt-oss-120b` on Bedrock**, under the credits, $0 cash; another vendor's model
  on Bedrock if a stronger one is open to the account on the day. Option (ii), `openai/gpt-6-astra` through
  OpenRouter (about $1-2 of his money, inside the $5 cap), is his call. Not Anthropic (the drafter's and main model's
  vendor) in either case. The model, its route and the price read that day are recorded here before sending.
- **Sent with it, as attached files, nothing else:** `experiment/protocol/protocol-v1.md` (as filled for the tag),
  `docs/phases/evidence/phase-3/simulation-summary.md`, `docs/phases/evidence/phase-3/matcher-calibration.md`, and the
  lock as written by `hc protocol lock --write` on the review's tree.
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
