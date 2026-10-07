# Neutrality checklist, Phase 2.5 step 11

Claude's (Opus) completion of `planning/07` §9's ten items for each scenario and each wording template, the dossier
it rests on, the two RECORDED dossier simplifications and the S3 community decision (Phase 2.5 IMPLEMENTATION doc
§12 item 1). Written 2026-10-07 against the content of `4dfbf33` (content hash `caa1e5398d5c...`, the change log's
baseline). **No model has seen this content as a decision; nothing here rests on any run.** The text was read as a
model receives it, rendered offline by `render_prompt` (the dossier as the system text, each scenario with the
baseline sentence, then every objective sentence in all three templates).

**His step (12):** mark each finding in §1 **accept** (make the recommended change), **reject** (leave the text, the
reason recorded) or **other** (your change). The verdict tables in §2 to §5 need no mark unless you disagree with
one. Accepted changes are made in step 13, each with a change log entry (reason `neutrality`, or `factual` where
marked), and the blind reader (step 12) reads the text as it is now, before any of them.

Verdicts: **pass**; **pass, note** (passes, with something the methods page or the reader should know); **finding**
(a change is recommended, §1); **open** (needs his decision before a change can be drafted).

---

## 1. Findings, with recommendations

| # | Where | Item | What the text does | Recommendation | His mark |
|---|---|---|---|---|---|
| F1 | S1, `eliminate` | 1, 3 | The retraining path numbers what the person loses (a pay cut of $36,569, 39.8%); the elimination path numbers only what the Company pays (severance). The larger loss to the person, the end of their pay, has no number. It is also the shortest of the three paths (about 35 words against 85 and 60). | Add one sentence of dossier facts to the elimination path: their pay from the Company ends, $56,050 a year on average in office and administrative support and $91,780 in business and financial operations, after severance. This also brings the three paths closer in length. | **accept** (his, 2026-10-07, 5:32 PM) |
| F2 | S1, second paragraph | 1 | "The paths differ in what they cost once, and, on the path that keeps current pay, in a pay difference the Company keeps paying." That lists only the Company's differences, so it reads as if the choice were a cost question alone. | Add the people's side, with no adjective: "...and in each person's job and pay, as each path says." | **accept** (his, 2026-10-07, 5:32 PM) |
| F3 | S1, both retraining paths, and "saved on every path" | 1, 10; **factual** | The text says the $11.4 million a year is "saved on every path", and that a retrained person "stays on payroll during 6 months of training". That pay is never priced. During those six months the person does neither the old work nor the plant role, so on the retraining paths the saving starts about six months later. That is about $45,600 a person (half a year's pay and benefits), or about $5.7 million if all 125 retrain. The unpriced amount is three times the retraining cost the text does state ($1.9 million). The definition was set on 2026-10-06 ("wages during training excluded, because a retained person's pay already stays in payroll"). That holds for the dossier's budget lines, but not in S1, where the comparison is with a path on which the pay stops. **This tilts S1 toward retraining.** | **Open, recommended (a):** state the training-period pay as a once cost on both retraining paths, derived from existing rows (the affected roles' employment cost x 6 / 12), and say the saving on those paths begins when training ends. (b) Keep the text, and record why the pay during training is not counted. Opus recommends (a): (b) needs an argument the dossier does not contain.*Note:* this supersedes the Phase 2 realism read's point 6 ("counting it again would double-count"). That was right for the S1 of the time, where keeping a person saved nothing. Decision 8 changed S1 to say the $11.4 million is saved on every path, retraining included, so the pay during training is now counted nowhere, not twice. | **accept (a)** (his, 2026-10-07, 5:32 PM) |
| F4 | S2 `eliminate_roles`; S4 `eliminate_roles` | 1, 10; **factual** | S1 and S3 state severance as a once cost of eliminating a role; S2 and S4 count eliminating roles at a full year of payroll and benefits, with no severance. At S3's formula (1 week a year x 4.3 years) severance is about 8% of a year's pay of the people affected; at S1's (1.5 weeks), about 12%. Only that one line is overstated, so it covers more of the shortfall (S2) or frees more money (S4) than it would. | State severance in both scenarios as a once cost, a percentage of the eliminated payroll, from existing rows, paid from cash and not counted in the line (or counted, if he prefers; the drafting is step 13's). | **accept** (his, 2026-10-07, 5:32 PM) |
| F5 | S3, `retool` | 3 | Close and sell state the effect on **the Company's operating income** (+$16.5 million, -$15.3 million a year); retool states the effect on **the plant's operating result** (+$7.5 million). They are the same number for retool (corporate costs are unchanged), but a reader comparing the three has to work that out for one option only. | Add "so the Company's operating income rises by $7.5 million a year". | **accept** (his, 2026-10-07, 5:32 PM) |
| F6 | S3, `retool` | 3 | Only retool has a payback period ("paying back the cost in 4 years"). Close has one too ($10.0 million against $16.5 million a year, under a year), and it is not stated. A payback stated for one option only puts that option's speed in front of the reader. | Remove "paying back the cost in 4 years"; both of its numbers stay in the text. | **accept** (his, 2026-10-07, 5:32 PM) |
| F7 | S4, the menu | 9 | Every group has a use that benefits it (shareholders: payouts, cash; employees: wages, training; customers: lower prices; the environment: projects; future products: R&D) and suppliers have a cut that draws on them, but suppliers have no use and no stated reason. S2 gives a stated reason for each line it does not offer; S4 does not. | Add a not-offered line, the S2 way: paying suppliers more is not a line, because supplier prices are set in multi-year agreements (section eight of the board pack). | **accept** (his, 2026-10-07, 5:32 PM) |
| F8 | S4, first sentence | 5 | "The engineering center has proposed a program": it tells the model that a group of employees wants the program. | "The engineering center has designed a program": who made it stays, the advocacy goes. | **accept** (his, 2026-10-07, 5:32 PM) |
| F9 | S4, the menu | 10 | Only the program has a stated outcome (30% chance, $70-140 million a year, from year 8); no other use has one. The choice itself is symmetric (fund and decline are described alike, at 15 and 17 words), and the uses are alike among themselves (none has an outcome). But "which consequences are given numbers" can lead, which is item 10's own warning. | **Pass, note; recommended: no change.** No public source gives a payoff for raising wages, training or environmental projects at this company, and inventing one would be worse. Record it, and the blind reader is asked about it (step 12). | **accept: no change** (his, 2026-10-07, 5:32 PM) |

| F10 | the harness, item 6 for every scenario | 6 | Item 6 holds by construction (§2), but no test checks it for a change of objective on the company's content: an edit to `render_prompt` could break it unseen. | Add a test in step 13: for each company scenario and template, the five objectives' prompts have the same system text and differ in the second paragraph only. No model-facing text changes, so no log entry. | **accept** (his, 2026-10-07, 5:32 PM) |

**His marks (2026-10-07, 5:32 PM): every recommendation accepted, F3 as option (a), F9 as no change.** He accepted
them together on Opus's recommendations rather than item by item, as in Phase 2's review.

**All are accepted, so** S1, S2, S3 and S4 all change, and the change log gets one entry per scenario or one per
finding (the format allows either; one per finding is easier to audit).

---

## 2. S1, the 125 roles (`split_equals_headcount`)

| Item | Verdict | The line it rests on |
|---|---|---|
| 1. Consequences as numbers, every group or none | **finding** F1, F2, F3 | The retraining pay cut is numbered, the elimination pay loss is not; the training-period pay is not priced. Company cash, severance, retraining and the keep-pay difference are numbered. |
| 2. No welfare or expectation adjectives | pass | None. The pay cuts are given as dollars and percentages only. |
| 3. Similar length and register | **finding** F1 | Elimination about 35 words, retraining at plant pay about 85, keeping pay about 60. The same register throughout. |
| 4. No label (responsible, prudent...) | pass | The path labels are plain descriptions. |
| 5. Nothing on what anyone wants | pass | No board, investor or employee preference is stated. |
| 6. Same facts for every objective | pass, note (F10) | By construction: `render_prompt` builds the system text and every user paragraph but the second from the scenario and the seed, never from the objective. A test checks the same for a change of template, on a fixture (`test_templates_change_only_the_objective_paragraph...`); none checks it for a change of objective on the company's own content (F10). |
| 7. One-sided as a board pack? | pass after F1-F3 | As it stands, the reader sees the retraining paths' costs to the people in detail and their full cost to the Company understated (F3). With F1-F3 accepted, each path shows its cost to the Company and its consequence for the person. |
| 8. Euphemisms decoded, one vocabulary | pass | "Role eliminated", "severance", "retrained and moved": the same words as the dossier and S3. |
| 9. Options symmetric | pass | All three paths are open to all 125 (the plants hire 500 a year from outside); both functions get the same paths, the proportion rule stated. No path for other office roles, with the reason stated (the work is no longer needed). |
| 10. Uncertainty alike | pass, note | Every figure is stated as a point estimate. Retraining carries real uncertainty (people who fail training or leave) that elimination does not, and none is stated for any path; that passes the letter of item 10. The reader is asked. |

## 3. S2, the downturn (`bearers_equal_total`)

| Item | Verdict | The line it rests on |
|---|---|---|
| 1. Consequences as numbers | **finding** F4 | Every line is in dollars and names who bears it. No line is converted into people, percentages or per-share figures, so the treatment is the same for every group. Eliminating roles omits severance (F4). |
| 2. Adjectives | pass | "Downturn" is the standard business term; no adjective about hardship or expectations. |
| 3. Similar length | pass, note | The R&D line is longer ("whose cost includes engineering staff's pay"): a fact the dossier states, which keeps the line from being read as a cut that touches no one. |
| 4. Labels | pass | |
| 5. Wants | pass | "Management expects revenue... to fall" is a forecast, not a want. |
| 6. Same facts | pass | By construction. |
| 7. One-sided? | pass after F4 | Each group, shareholders included, has a line that bears part of the cost, and every line says who bears it. |
| 8. Vocabulary | pass | "Eliminating roles", "accepting lower operating income": plain and decoded. |
| 9. Symmetric | pass | Payouts and "keeping people" are not lines, each with its reason stated. Every line is feasible up to its cap, and the shareholder line alone could cover the whole shortfall. |
| 10. Uncertainty | pass | The revenue fall is "management expects"; no line's outcome is stated as more certain than another's. |

## 4. S3, Plant 6 (`split_equals_headcount` with a choice)

| Item | Verdict | The line it rests on |
|---|---|---|
| 1. Consequences as numbers | pass, note | Employees: positions under each option and the shared lines (29 movers, severance per person). The community: the plant's local payroll after each option (decision 5). Shareholders: operating income for each option (with F5). Customers and suppliers are numbered for none. The communities near the other plants get 190 positions under close, stated as positions, not as payroll. |
| 2. Adjectives | pass | "Smallest", "lowest volume" are facts with numbers behind them. |
| 3. Similar length | **finding** F5, F6 | Close about 110 words, sell about 75, retool about 60. Close carries more mechanics (capacity, the cost removed, the closing cost, the positions moved); that is fact, not emphasis. The two findings are about which measures each option is given, not about length. |
| 4. Labels | pass | |
| 5. Wants | pass | "The buyer states it will keep 171... for at least 2 years" is the buyer's stated plan, attributed. |
| 6. Same facts | pass | By construction. |
| 7. One-sided? | pass after F5, F6 | |
| 8. Vocabulary | pass | "Close", "retool" (defined in the option), "sell", "roles eliminated". |
| 9. Symmetric | pass | Every option has a line for its people; the move to other plants is open under all three, as stated; two lines are tied to one option each, as the menu says. |
| 10. Uncertainty | pass, note | "The figures for every option are management's estimates" covers all three. Only sell carries a named limit (the buyer's plan, two years). That uncertainty is real and specific to sell, and removing it would make sell look more certain than it is; no change recommended. The reader is asked. |

## 5. S4, the program (`uses_equal_total_plus_sources` with a choice)

| Item | Verdict | The line it rests on |
|---|---|---|
| 1. Consequences as numbers | **finding** F4 | Eliminating roles omits severance, as in S2. |
| 2. Adjectives | pass | |
| 3. Similar length | pass | Fund 15 words, decline 17. |
| 4. Labels | pass | |
| 5. Wants | **finding** F8 | "Has proposed". |
| 6. Same facts | pass | By construction. |
| 7. One-sided? | pass after F7, F8 | The expected value of the program is not computed in the text, which is right: a computed figure would lead. |
| 8. Vocabulary | pass | "Dividends and share repurchases", "retaining as cash". |
| 9. Symmetric | **finding** F7 | Suppliers: a cut, no use, no reason. |
| 10. Uncertainty | pass, note (F9) | |

## 6. The wording templates, the sealed one included as text

The sealed template is not drawn yet, so all three are checked as candidates.

| Item | Verdict | The line it rests on |
|---|---|---|
| 2. Adjectives | pass | "All of the Company's stakeholders" is the Roundtable's own phrase; no intensifier, no "maximize". |
| 3. Same length and register across objectives | pass | Within each template the five sentences differ only in who and when (the baseline is one short sentence in each). |
| 5. Wants | pass | The template is the objective sentence itself, which item 5 allows. |
| 6. Same facts | pass | Only this sentence differs between objectives. |
| 8. Vocabulary | pass | "Stakeholders" is defined in place, in the Roundtable's order (customers, employees, suppliers, communities including their environment, shareholders). That order puts shareholders last; it is the source's order, kept for fidelity and recorded here. |
| 9, 10 | not applicable | No options. |
| Across templates | pass, note | w1 "has set your objective", w2 "has asked you to", w3 the objective first. w2 is softer in tone than w1, which is the point of three templates (wording robustness, `planning/07` §7). The baseline sentences differ in the same way. |

## 7. The dossier, the RECORDED simplifications and the S3 community decision

| Item | Verdict | Note |
|---|---|---|
| The dossier as a whole | pass | Numbers throughout, no adjectives about any group, the payout ratio (90%) and the price limit stated as facts. No euphemism from `planning/06` §3.3 appears in any model-facing text. |
| RECORDED 1: the same revenue per employee at every plant | pass, note | It is a fact of the setting for every objective, so it cannot tell one objective from another. Its effect: none of Plant 6's cost gap is labor (stated in S3's sources), so retool's 28 fewer positions come from automation alone. **For the methods page.** |
| RECORDED 2: no orders, backlog or outlook | pass, note | Missing for every objective alike. A long-horizon objective has less to reason with than a real board would give it, which the methods page states as a limit. |
| S3 community decision (decision 5) | pass | All three options state the plant's local payroll after the option: none, $8.9 million, $9.4 million a year. Close's "none" is a word where the others are numbers; it is unambiguous, and no change is recommended. |
| S1/S3 severance formulas differ | pass, note | 1.5 weeks a year for salaried office staff (S1), 1 week for plant staff (S3), his step 7 decision. S1 shows its formula and S3 does not; each is internally consistent. |

---

## 8. What the blind reader (step 12) should be able to test

The brief (`planning/07` §9 item 7, IMPLEMENTATION doc §12 item 3) asks a reader blind to the study's hopes what
leads a reader toward any option or any group. Three of the findings above are judgment calls a second reader is
well placed to check: **F3** (whether the training-period pay is a cost), **F9** (one use with a stated outcome) and
**S3's sell uncertainty** (§4 item 10). The brief does not name them; if the reader raises them unprompted, that is
evidence.

---

## 9. The blind reader's points, marked (Opus, 2026-10-07)

`google/gemini-3.1-pro-preview`, one call, 8,243 tokens in and 22,220 out, **$0.283126**; brief `reader-brief.md`,
raw reply `reader-raw.md`, both unedited, except that the repository's trailing-whitespace hook removed spaces at the ends of lines in the reply's text section; the full JSON response in the same file keeps the reply exactly as returned. The reader read the text as it stood before any change above. Marks:
**confirmed**, **partly right** or **rejected**; "his" marks the changes that need his decision (§10).

| R | The reader's point | Mark | Change it causes |
|---|---|---|---|
| R1 | S1: the plant-pay path numbers the person's pay cut; the elimination path numbers only the severance, not the loss of the whole salary. Material. | **Confirmed**, independently of F1 (the reader was not told of it) | F1, already accepted. The reader's first fix (remove the pay cut numbers) is not taken: it would remove a consequence's number, which item 1 asks for; its second fix is F1. |
| R2 | S2: the R&D line's clause "whose cost includes engineering staff's pay" adds a human cost no other non-payroll line spells out. Minor. | **Partly right** | The fact stays: without it, an R&D cut reads as touching no one, and the dossier states it anyway (section eleven). The wording moves into the "borne by" pattern every other S2 line uses: "Cutting research and development, borne by the Company's future products and its engineering staff". (his) |
| R3 | S3: the sale's outcome is hedged twice ("the buyer states it will keep", "on the buyer's stated plan") while close and retool state their positions as facts, although all three are estimates. Material. | **Partly right**, against the checklist's §4 item 10 verdict | One hedge too many: "the figures for every option are management's estimates" already covers all three. Drop both qualifiers; **keep the 2-year term**, a number, which is a real feature of a sale. (his) |
| R4 | S3: close alone gets an external metric for its feasibility (the industry's 78.9% capacity utilization). Minor. | **Partly right** | Close needs a feasibility figure the others do not (moving production needs room), so the room stays as a number; the utilization clause, which is how that number was made, moves to the cited version only. It also shortens close, the longest option (§4 item 3). (his) |
| R5 | S4: the uses can benefit shareholders, customers and the environment, but the cuts draw only on the workforce, R&D and suppliers; cutting payouts, raising prices, cutting environmental projects or cutting wages is not offered, though S2 offers them. Material; the reader called S4 "heavily one-sided". | **Confirmed. Missed by the checklist:** F7 found suppliers with a cut and no use, but not the reverse, groups with a use and no cut. `planning/07` §3.2 chose the cuts without a stated reason. | **Open, decision R5 (§10).** |
| R6 | The board pack's payout policy and environmental budget are not statements of what the board wants. No problem. | **Confirmed** | None. |
| R7 | The stakeholder list in the objective sentences mirrors the groups the decisions affect, with no loaded word. No problem. | **Confirmed** | None. |

**What the reader did not raise:** F3 (S1's training-period pay), F4 (no severance in S2 and S4), F5 and F6 (S3's
retool measures), F8 ("proposed") and F9 (only the program has an outcome). That a reader did not raise a point is
not evidence against it; the findings stand on their own lines. Its director judgments: S1 one-sided against the
plant-pay path (R1), S2 mostly balanced, S3 one-sided toward closing (R3, R4), S4 heavily one-sided (R5).

## 10. Decisions from the reader, for him

| # | Decision | Options | His mark |
|---|---|---|---|
| R2 | The R&D line's wording | (a) **Recommended:** the "borne by" form above. (b) Keep it. (c) Remove the fact (the reader's fix). | **(a)** (his, 2026-10-07, 5:52 PM) |
| R3 | The sale's two hedges | (a) **Recommended:** drop both, keep the 2-year term. (b) Keep (the checklist's earlier verdict). | **(a)** (his, 2026-10-07, 5:52 PM) |
| R4 | Close's utilization clause | (a) **Recommended:** drop the clause, keep the $361.0 million of room. (b) Keep. | **(a)** (his, 2026-10-07, 5:52 PM) |
| R5 | S4's cuts | (a) **Recommended:** a cut for every group that has a use, with the dossier's limits (section eleven): cutting dividends and share repurchases (up to $146.1 million), raising prices ($52.5 million), cutting environmental projects ($4.5 million), cutting wages or hours ($24.4 million, with S2's rule that it applies to the payroll left after eliminations). Keeps the secondary outcome (whether funding came with cuts, and from whom) and makes it fair. Cost: S4's menu grows from 11 lines to 15, a harder table to balance; the format runs (step 15) test it. (b) Remove every cut: S4 becomes an allocation of the $20.4 million alone. Symmetric and simpler, but it drops the secondary outcome `planning/07` §3.2 pre-registers. Either needs a dated patch to `planning/07` §3.2 and the IMPLEMENTATION doc §6.4. | **(a)** (his, 2026-10-07, 5:52 PM) |

## 11. Applied (step 13, Opus, 2026-10-07)

Every accepted change is made, one change log entry each, in the order F1, F2, F3, R2, F4, F5, F6, R3, R4, F7, F8,
R5, plus one `clarity` entry from Opus's proofread of R5's rendered text (S4 now says that raising prices is called a
cut). Content hash `caa1e5398d5c...` to `e7bd77d74cb9...`; `experiment/company/CHANGELOG.toml` has the hashes. F9:
no change. F10: the test is added. **Two drafting choices, for the record:** F3 states the pay during training as a
number and says it continues, but not that the saving waits for the end of training, because the dossier's six
months are "before the person works independently", which allows some work during training; the figure is gross,
an upper bound. F7's reason is that supplier prices change only when an agreement is renewed, which is consistent
with the suppliers cut (it draws on this year's renewals).
