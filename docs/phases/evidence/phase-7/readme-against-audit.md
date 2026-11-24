# Phase 7 step 8: the README read against the audit, and the card re-read

2026-11-24, about 1:40 to 2:00 PM CST, Claude (Opus). Against `docs/v1-audit.md` as re-verified at step 7.

## The markers and their test (IMPLEMENTATION doc §5.3)

Each claim in `README.md` that is not a number now carries an invisible `<!-- audit:ID -->` after it: 40 markers,
citing 26 rows. `tests/test_readme_figures.py` (section 5.3's block) fails when a marker names no audit row, when a
cited row is marked not met, or when the rows the README cites and the rows the audit flags README differ (Parts A
to D), with one planted case for each.

**The rows cited:** A1, A2, A3a, A3b, A4, A5a, A5b, A5d, A5e, A6, B15, B65, C2, C4, C5, C6, C12, C14, C15, C16, D1,
D2, D3, D5, D6, D7: the 25 rows the audit flagged README at step 7, plus **A3b**, which the README now cites for the
shuffled order (a correction below), flagged README in the audit for it. A3b was in step 7's sample, so every cited
row was re-verified cold. Partial rows are cited (A2, A5d, A6, B65, C6, C14): a cited row may be partial, never
not met, and each claim citing one says no more than the row does.

**Not marked, on purpose:** the opening on the name and the Roundtable's words (facts about the world, not about the
build); the result sentences and tables (numbers, held by the figure markers and the claim tests); "the numbers in
this README are tested" (held by this test file itself, not an audit row); the dates and the retirement line (held
by step 2's tests); the license line (decision C's terms read is still open, E11); and the known limits that are
disclosures rather than claims (the vendor drafted the text; the simplifications; the rule for the results against
the expectation written after them; the memos' echoes), each of which the methods page states.

## The read: each claim against its row

Every marked claim was read against the row it cites. **Five claimed more than the row backs, and were reworded**
(Claude's wording, for his approval):

| Where | Was | Row | Now |
|---|---|---|---|
| How it works | "From one run to the next, the only thing that changes is the goal it is given." | A3b, D6: the order of the options is shuffled for every run, and each goal has three wordings | "the goal it is given is the only thing that changes by design; the order in which its options are listed is shuffled for every run, so that coming first favors no goal" |
| What was built, opening | "Terraform for everything" | A5d, partial: the maintainer's AWS user and the billing tag's activation were made by hand | "its infrastructure in Terraform" |
| What was built, the Terraform bullet | "Terraform for everything ... A full teardown and re-apply was tested before launch." | A5d; B65 row 11; Phase 1.5 doc §25: two teardown tests, the second on the day the site went live (2026-11-21), after it went live | "The infrastructure in Terraform ... Two things were set up by hand: the maintainer's own AWS user, which Terraform runs as, and switching on the billing tag ... tested twice, the second time on the day the site went live." |
| What was built, opening | "a substitution the protocol provides for, not a cut" | C12: the fallback pair was added to the plan on 2026-10-09 (Phase 3.5 IMPLEMENTATION doc, decision 5 as decided), after Bedrock failed on 2026-10-05, and the protocol names it at §5.1; "provides for" suggests a provision made in advance | "a substitution, not a cut" |
| Why containers; the known limits | "deleted two official images ... no run can be repeated in the identical image"; "Two program images are deleted, so no run can be repeated" | A6 and E13: one deleted image was official, the other Phase 1's test image; the case runs' image exists | "deleted the image every official run on the made-up company used ... none of those runs can be repeated"; "A program image is deleted, so no run on the made-up company can be repeated" |

**One kept, and why:** the note's "when only the goal they are given changes" is the scope sentence, read as what
differs between the compared runs, which is true (every wording applies to every goal and the order is shuffled);
it is his approved wording and was left. **Every other marked claim matches its row.**

**The plain-English write-up**, read against the same rows (it carries no markers; §5.3 is the README's):
one sentence claimed more, "From one run to the next, only one thing changed: the goal it was given", reworded to
"only one thing was changed on purpose", with the shuffled order added to the next sentence. Nothing else in it goes
beyond a row.

## The card (step 0's line), re-read

Read live 2026-11-24 (`gh repo view`): *"A pre-registered experiment in corporate objectives: two AI models make the
same capital-allocation decision under five objectives."* Website: `https://horizon-compact.vercel.app`. Against the
finished README and the results: pre-registered (D1), two models (C12), five objectives: right. It states no result,
so nothing in it can overstate one. One word reads narrower than the build: "the same capital-allocation decision"
is singular, and there are four decisions, and real cases. **His call** (his words, typed into GitHub by him): keep it,
or "decisions". **His decision, 2026-11-24, about 1:55 PM: "decisions"**, typed by him; he is "not thrilled about the
repo card but it is what it is".

**His approval of the rewordings, the same time:** "the rewordings I all approve".
