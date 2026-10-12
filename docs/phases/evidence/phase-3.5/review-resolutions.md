# Independent review of the protocol: the resolutions

Phase 3.5 build step 11. The reviewer: Gemini 3.1 Pro through OpenRouter, effort `high`, sent 2026-10-12 from commit
`b1bc34c`, $0.358 of his OpenRouter cash (`review-raw.md`, `review-brief.md`, `review-lock.txt`). Each point was
checked by Claude (Opus) against the protocol and the two simulation reports, not taken on the reviewer's word, and
marked **confirmed**, **partly right** or **rejected**, with the reason. **His decision** on each is recorded beside
it; a change is made to the protocol only after it. None of the ten touches what a model reads (the prompt, the
scenarios, the dossier), so no change goes through the change log and no content hash moves.

## Summary

**His decision, 2026-10-12, about 4:50 PM: all ten accepted as recommended** ("Accept all"), so points 8 and 9 stay
rejected as changes and point 9's one line is added. Each accepted change was made in `protocol-v1.md` the same
evening, marked in place "Review point N, accepted 2026-10-12 (his)".

| # | Point (the reviewer's) | Mark | Recommended | His decision |
|---|---|---|---|---|
| 1 | "Preferred, a manufacturer of comparable size" breaks the strict order of real cases (§12.4) | **confirmed** | delete the preference || **accepted** 2026-10-12 |
| 2 | The author resolves the independent reader's disagreements (§12.4, §12.9) | **partly right** | a disputed rejection keeps the candidate; a disputed rubric reading is published both ways || **accepted** 2026-10-12 |
| 3 | A failed scaling check is "decided by him" (§12.6) | **partly right** | make it mechanical: fix the build error; if none is found, drop the case || **accepted** 2026-10-12 |
| 4 | The extraction model, its settings and prompt are not frozen (§12.6) | **partly right** | fix and commit them before the first real case is built; recorded per case || **accepted** 2026-10-12 |
| 5 | The refusal call is not truly blind: the text can reveal the objective (§4.7) | **partly right** | one sentence: the leak is possible, and cannot move a verdict || **accepted** 2026-10-12 |
| 6 | The repeat cap makes "no split" nearly unreachable (§8.4) | **partly right** | already stated in §8.4; add one pointer in §1.5 || **accepted** 2026-10-12 |
| 7 | Thinking off "hobbles" the main model (§5.3) | **partly right** | state the reason in §5.3; keep thinking off (the sub-study tests it) || **accepted** 2026-10-12 |
| 8 | The worst-case bound uses outcomes the scenarios cannot reach (§7.3) | **rejected** | no change || **accepted** 2026-10-12 |
| 9 | Neutral wording strips the force of real board mandates (§1.4) | **rejected as a change** | no change to the templates; one line in §1.6 on what is not tested || **accepted** 2026-10-12 |
| 10 | §11.3's "labeled every reversal" overstates the simulations | **partly right** | reword with the measured rates || **accepted** 2026-10-12 |

Six of the ten rest on the real-case rules (§12) or how a claim is worded; none finds an error in the verdict rules,
the intervals or the numbers quoted from the simulations, which the reviewer checked and found sound (its last list).

## Each point

### 1. The size preference (§12.4) — confirmed

**The reviewer:** candidates are taken "in order of first disclosure", but the same sentence says "preferred, a
manufacturer of comparable size", undefined, so an older case could be skipped for a newer one said to fit better.

**Checked:** §12.4 says exactly that, and nothing in the protocol defines "comparable" or says how the preference
acts against the order. It is the only judgment in a list that is otherwise mechanical. **A real lever.**

**Recommended:** delete "preferred, a manufacturer of comparable size". The criteria already require a real decision
that maps onto a scenario shape; each case's size against the fictional company's is reported descriptively, never
used to choose. *Alternative:* make size a numbered hard criterion with a stated range (revenue or headcount), applied
before the order. That needs a range chosen now, without seeing any candidate; the delete does not.

**Proposed text:** "(5) not instantly recognizable after anonymization (the recognition probe, section 12.8). **The
first k that pass are the cases.** Each case's size beside the fictional company's (revenue and headcount, scaled) is
reported, and never used to choose."

### 2. The independent reader's disagreements (§12.4, §12.9) — partly right

**The reviewer:** a disagreement "is resolved by him", which gives the author a veto over the independent check.
Suggests resolving every disagreement to the opposite of the author's judgment, or dropping the candidate.

**Checked:** both sections say so. The log is published, which exposes a motivated call but does not prevent one.
**Right about the veto; the suggested fix is wrong**: "the opposite of the author" lets the reader's errors decide, and
"drop the candidate" turns every disagreement into an exclusion, which is the direction a motivated author would want.

**Recommended, two cases:**
- **Selection (§12.4): a rejection the reader disputes does not stand.** The candidate goes on to the next criterion
  as if it had passed this one, and the disagreement is logged. An author can then never exclude a case the
  independent reader says qualifies, and excluding is where selection can be bent.
- **The rubric (§12.9): a disputed mapping is published both ways,** and the case's result is reported under both
  readings when they differ. His reading is the one the headline uses, labeled as his; the other sits beside it.

**Proposed text (§12.4, last sentence):** "Every rejection on criterion 3, 4 or 5 is read by the independent reader;
**a rejection the reader disputes does not stand**: the candidate goes on to the next criterion, and the disagreement
is logged with both reasons." **(§12.9, last sentence):** "A disagreement on a rejection is settled as section 12.4
says. A disagreement on a rubric mapping is logged with both readings, and where they give different results the case
is reported under both, his reading labeled as his."

### 3. A failed scaling check (§12.6) — partly right

**The reviewer:** "decided by him with the reason logged" leaves him free to drop the case or patch figures.

**Checked:** the protocol proves that a correct build always passes (rounding moves pay per head by at most 3.1%,
under the 3.5% check), so a failure means a build error, and it already says the factor is never redrawn. What it
does not say is what happens next. **Right that the step is not mechanical.**

**Recommended:** "A case that fails it has a build error: the error is found, fixed in the builder (never by editing a
figure by hand), and the whole case rebuilt and re-checked, with the factor unchanged. If no error is found, the case
is dropped as failing criterion 4 and the next candidate taken; either way it is a reported deviation."

### 4. The extraction model (§12.6) — partly right

**The reviewer:** the model that turns filings into the dossier is never named, nor its settings or prompt; it should
be in the lock.

**Checked:** true. The Phase 5 scope doc lists "the extraction model and its prompt" for the search half's
IMPLEMENTATION doc, and the code half says it is "chosen in the search half". It **cannot be in the lock**, which is
written at the tag, before the search half. **Right that it is an unfrozen step that shapes every real case**; the
protection that exists (it sees only pre-cut-off sections and is never told the outcome; the foreshadowing check)
limits what it can leak, not how it is chosen.

**Recommended (new bullet, §12.6):** "**The extraction model, its route, its settings and its prompt are fixed and
committed before the first real case's documents are fetched,** and each case record carries the commit and the
prompt's hash. It is not one of the official models of section 5. A change after the first case is built is a
deviation: every case already built is rebuilt with the changed extraction and both are reported." *The reason for
"not an official model":* a model that wrote a case's dossier would then be deciding on its own summary.

### 5. The refusal call's blindness (§4.7) — partly right

**The reviewer:** the objective is hidden, but the reply's text can name it ("I must focus on all stakeholders..."),
so the call is not blind. Suggests a script that scrubs objective words first.

**Checked:** true that the text can reveal it. But §4.7 also says **"A refusal and a failure count the same toward
every rule in section 7"**: the call decides only which column a run sits in, never a verdict. A scrubbing script
would itself be a judgment (which words), applied after seeing replies. **Right about the leak; it cannot bend a
result, so the fix is disclosure, not a scrubber.**

**Recommended (added after "before any official analysis."):** "The reply's own text may reveal the objective; the
call cannot change a verdict, since a refusal and a failure count the same."

### 6. The cap and "no split" (§8.4) — partly right

**The reviewer:** at the 20-repeat cap, "no split" is nearly unreachable on shares; admit it up front.

**Checked:** §8.4 already says it in nearly those words ("effectively out of reach on a wide or all-in spread at 20
repeats"; reachable a median of 0.2% where the cap binds) and requires the achieved precision to be reported. **Not a
hidden weakness**; a reader of §1 alone would still miss it.

**Recommended:** one sentence at the end of §1.5's table text: "**The study can find splits more easily than it can
show their absence:** where the repeat cap binds on a share, 'no split' is effectively out of reach, and a result
there is inconclusive with its precision stated (section 8.4)."

### 7. Thinking off (§5.3) — partly right

**The reviewer:** running the main model with thinking off "hobbles" it; run the grid with thinking on, or justify it.

**Checked:** the reason is in the design (`planning/07` §3: cheapest; the memo already carries the reasoning a reader
sees) and the protocol pre-registers the check, the thinking sub-study (§9.5), whose question is exactly this. But
§5.3 states the setting and not the reason. **Right that the reason is missing from the protocol; running the whole
grid with thinking on is not recommended:** it would cost several times more and change what every result describes.

**Recommended (§5.3, the thinking bullet):** add "**Why off:** it is the cheapest setting, and each decision's memo
already gives the reasoning a reader sees. Whether thinking changes what an objective does is tested directly, on S1,
by the sub-study of section 9.5, and reported as a finding either way."

### 8. The worst-case bound's 0 and 1 (§7.3) — rejected

**The reviewer:** setting a failed run's outcome to 0 or 1 uses values the scenarios cannot reach (it names S2's 10%
wage limit as making 1.0 impossible), which inflates the interval and turns real splits inconclusive.

**Checked, and wrong:** every primary outcome can reach both 0 and 1. **S2:** the "eliminate roles" line is capped at
$309.8 million, above the $112.1 million shortfall, so the workforce can bear all of it; the 10% limit applies to the
wage line only. **S1:** 0 to 125 kept, by the table. **S3, S4:** a run either chooses close (fund) or not. So 0 and 1
are the feasible extremes. **No change.**

### 9. Neutral wording (§1.4) — rejected as a change

**The reviewer:** stripping words like "maximize" makes the objectives sterile, so a "no difference" could be blamed
on missing force; add a forceful template.

**Checked:** the neutrality is deliberate (`planning/06` §2, the vocabulary rules) and is what makes the five
objectives comparable: a forceful word on some templates mixes the objective with its intensity, and choosing which
words are "forceful" is itself a lever. Adding a template now would also change what a model reads after the content
was sealed. **Not recommended.** It is a fair limit on reach, though, and belongs among what is not measured.

**Recommended (§1.6, one line):** "**How forcefully an objective is stated** is not varied: each is stated plainly,
in three neutral templates, with no intensifier. A board that phrases its mandate forcefully is not what is tested."

### 10. "Labeled every reversal" (§11.3) — partly right

**The reviewer:** §11.3 says the wording rule "labeled every reversal wording-sensitive", but the simulation report
shows true reversals labeled robust (it cites `d=0.2, reversed s=0.1`, 217 of 400).

**Checked:** **the cited row is not a reversal**: its true per-wording differences are 0.00, +0.20, +0.40, none below
zero (simulation summary §7); a robust label there is correct by the rule's definition. **But the sentence does
overstate.** The four settings where one wording's true difference has the opposite sign (`d=0.15` and `d=0.1` at
`s=0.1`, n 10 and 20) flagged 87.0%, 94.2%, 98.6% and 100.0% of their splits: high, not "every".

**Recommended (§11.3, second sentence):** "The wording rule, over 36 shift settings, matched an independent
recomputation; **where one wording's true difference had the opposite sign to the others** (four settings), it
labeled **87% to 100%** of the splits wording-sensitive, the rest robust because that wording's observed difference
did not change sign (simulation summary section 7)."

## What the reviewer checked and found sound

Its own list, kept as it gave it: the repeat formula (§8.2); the Bonferroni level 0.05/16 (§6.4); the matcher's D*
thresholds against the calibration report (§11.4); the 10% failure rule at one failure in six (§7.4); the near-all-agree
false no-split rate of 0.33% (§11.1); the cost caps and run accounting (§13.2). Not re-checked by Claude beyond the
points above.

## Found while applying them (Opus, 2026-10-12)

Three more sentences of the kind §2.7 corrected that afternoon, untrue as written once `gpt-oss-120b` became the second
family, were corrected in the same pass and marked in place: **§1.1** ("No official model has made a decision on any of
the experiment's four scenarios before the tag": it made development decisions on them in Phase 2.5, none read),
**§1.6** ("before any official model saw the scenarios") and **§4** ("How the text was tested before any official
model saw it"). Each now names the main model and points to §2.4. The reviewer did not raise them; they follow from his
decision of 2026-10-12 on the second family.
