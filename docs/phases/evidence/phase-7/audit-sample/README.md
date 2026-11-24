# Phase 7 step 7: the audit's sample, re-verified cold

Decision A (the Phase 7 IMPLEMENTATION doc §2): Claude in Chrome, in his browser, Sonnet 5.5 at the panel's default
effort, a new conversation for each batch, with nothing but its brief. The agent had no working history, no memory
store and no checkout: only the public repository, pinned to `4911440`, and the live site. Run on 2026-11-24, about
12:15 to 1:30 PM CST. Each brief gives a row's promise and the audit's claims about it, with links. **No brief states
the audit's status**: the agent gave its own. Claude wrote the briefs and scored the reports; he ran each batch.

| File | What it is |
|---|---|
| `brief-1.md`, `brief-2.md`, `brief-3.md` | The three batches, 28 rows |
| `report-1.md`, `report-2.md`, `report-3.md` | The agent's replies, verbatim |
| `brief-4-recheck.md`, `report-4-recheck.md` | The six rows corrected or disputed, sent to a fresh agent with the corrected claims, and its reply |

**The sample.** Every row the README relies on (25: A1, A2, A3a, A4, A5a, A5b, A5d, A5e, A6, B15, B65, C2, C4, C5,
C6, C12, C14, C15, C16, D1, D2, D3, D5, D6, D7), plus two partials the README does not lean on (A3b, A5f) and one
Part E entry (E6). 28 rows across the five parts. The README flags were pruned before the sample was drawn: the first
draft flagged 36 rows, mostly phase rows repeating a Part A, C or D row, and only the row where the README makes the
claim kept its flag.

## The scoring

**Agrees:** the agent's status equals the audit's, and no claim it checked is contradicted. **Agrees, evidence
corrected:** the same status, but a claim was wrong or unsupported as cited, and the audit's evidence was fixed.
**Disagrees:** a different status. **Could not check:** said where it applies.

| Row | Audit's status (before) | Agent | Score | What was done |
|---|---|---|---|---|
| A1 | met | met | agrees | |
| A2 | partial | met | **disagrees** | Kept partial: `00` §8 is a draft "to be finalized in `05` and `07`", and the done-when finalized there adds the invest-or-retool case. The reason and the anonymization evidence (which the agent could not find) added to the row; re-checked |
| A3a | met | met | agrees | |
| A3b | partial | partial | agrees | |
| A4 | met | met | agrees, evidence corrected | The row misquoted its source ("never computed"; the source says "never bundled") |
| A5a | met | met | agrees | |
| A5b | met | met | agrees, evidence corrected (one claim could not be checked) | "One object per attempt" is protocol §13.2's rule, not `store.py`'s words; re-checked |
| A5d | partial | partial | agrees, evidence corrected | The agent found a second hand-made item: the cost allocation tag's activation, added |
| A5e | met | met | agrees | |
| A5f | partial | partial | agrees | |
| A6 | partial | partial | agrees, evidence corrected | Claim 5 contradicted: only one of the two deleted images was official; the case runs' image still exists. Row corrected; **the same error is on the README and the methods page (E13)**; re-checked |
| B15 | met | met | agrees (live headers could not be checked from the browser) | |
| B65 | met | partial | **disagrees** | Re-marked partial (row 6: check 6 absent on the cards and the video, check 4 one read); re-checked |
| C2 | met | met | agrees | |
| C4 | met | met | agrees | |
| C5 | met | met | agrees, evidence corrected | The tag time was the commit's (01:14); the tag object's is 01:19:15 CDT. Fixed in B35 and D1 |
| C6 | met as changed | partial | **disagrees** | Re-marked partial (the false-split target and reachability held approximately); re-checked |
| C12 | met | met | agrees | |
| C14 | partial | partial | agrees | |
| C15 | met as changed | met | agrees, evidence corrected | The lock order is in each case's entry, not 14d's rows; 14d row 3's late record added |
| C16 | met | met | agrees, evidence corrected | The freeze is protocol §11.4 and §15.2, not §12.7 alone |
| D1 | met | met | agrees | |
| D2 | met | met | agrees | |
| D3 | met | met | agrees | |
| D5 | met | met | agrees | |
| D6 | met | met | agrees | |
| D7 | met | met | agrees | |
| E6 | not scored | (partial) | evidence corrected | Claim 3 contradicted: the boundary is for the roles the deploy role creates, not the deploy role itself; corrected; re-checked |

**First pass:** of the 27 scored rows, 24 agree on status and 3 disagree (A2, B65, C6); 8 rows had their evidence
corrected (A4, A5b, A5d, A6, C5 with B35 and D1, C15, C16, E6). Two of the three disagreements went the agent's way,
both toward partial. **Every disagreement, and every correction to a claim the agent contradicted or could not check,** went to
the re-check batch; the corrections the agent itself supplied (A4, A5d, C5, C15, C16) did not.

**The re-check (a fresh agent, the corrected claims):** A2 partial, A5b met, A6 partial, B65 partial, C6 partial,
E6 confirmed: **six of six agree.** One gap it named, the line saying the skeleton image ran no official sweep, is
now cited in A6 (the skeleton ran on 2026-10-12, before the tag; on tag day nothing existed under `official/`).

**Step 7 is done:** every sampled row agrees, or was corrected and re-checked.

**What the sample did not reach:** the 29 scored rows not sampled, none of them a README row. The agent could not read
GitHub's Actions run pages (one timed out, one refused), so the CI run ids are confirmed by Claude's `gh run view`
reads alone; nor the live response headers (B15).
