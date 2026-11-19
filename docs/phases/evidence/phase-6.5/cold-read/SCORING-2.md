# Scoring of the second cold-read report (Phase 6.5 step 8, the re-test)

Scored by Claude (Opus 5.5), 2026-11-19, against `planning/06` §4, as in `SCORING-1.md`: each figure checked against the
explorer's data files and the rendered text of the fixed preview.

## Result

**No conclusion is a misreading under §4, and the fix is confirmed:** the agent read closure-07 and reported "On
closure-07, Haiku never made the company's choice (distance 1.000 for every goal)", which is what the distance means.
It drew no link to Plant 6. Three sentences sit at the edge of the claim rules and are recorded, not fixed; one of them
is the same step the first reader took (below).

## Conclusions, one by one

| # | The report's conclusion | Checked against | Score |
|---|---|---|---|
| 1 | What was tested: two models, five goals, four decisions (125 staff; a profit drop; Plant 6 and its 190 employees; the ten-year program), pre-registered 2026-10-13, 16 primary comparisons a model, the 10 and 20 point thresholds; the two side studies; five exploratory closures | home, methods, scenario pages, `index.json` | allowed |
| 2 | s1, Haiku: A vs B about 57; C vs D about 19; B vs D about 2; A vs C about 40 | verdicts −56.9, −19.1, −2.0, −39.8 | allowed; two rounding slips (below), and #11 |
| 3 | s2: mostly inconclusive; the one split Haiku A vs B, about 22 points; 6 runs a cell; wordings dropped for failures | verdicts; methods "What failures cost" | allowed |
| 4 | s3, Haiku: closed 50 and 60 of 60 under the shareholder goals and 60 of 60 with none; retooled 51 and 52 of 60 under the "everyone" goals; C vs D about 86 | scenario s3 page; verdict 86.7 | allowed |
| 5 | s4, Haiku: funded 16 of 57 (A), 13 of 57 (C), 36 of 60 (B), 38 of 59 (D) | scenario s4 page | allowed |
| 6 | gpt-oss: A vs C on s1 −0.5, inconclusive; 39 failed runs of 1,200 | verdict −0.5; 8 + 27 + 1 + 3 failed (292, 273, 299, 297 valid of 300) | allowed |
| 7 | gpt-oss "agreed on direction for the shareholder vs everyone comparisons" | gpt-oss splits on that pair type: s1 A vs B, C vs D; s3 A vs B, C vs D, all the same sign as Haiku's; its s2 and s4 ones are inconclusive | **allowed, at the edge** (below) |
| 8 | Against the expectation: the two Haiku "no split" pairs, s1 and s3 B vs D; the rule written after the results | `against_thesis.entries`; the disclosure | allowed |
| 9 | Real cases: all no good match; closure-07's 1.000 means Haiku never made the company's choice; "no good match" was meant to be rare | case pages; methods ("rare by design") | allowed; **the fix confirmed** |
| 10 | Thinking sub-study: splits on A vs C, A vs B and the secondary pair, C vs D inconclusive, 20 runs a goal; awareness replies mostly named workers against shareholder value | studies page | allowed |
| 11 | "Short vs long horizon made no difference when the goal was 'everyone with a stake', about 2 points" | s1 B vs D, no split on the share kept; the site adds "That is about this one measure, not every choice they made" | **at the edge**: §4 names "made the same decisions" as not allowed for a no split; the report's measure is the share kept, named in the sentence before |
| 12 | "'Who counts' mattered even at a twenty-year horizon on three of the four decisions" | Haiku C vs D split on s1, s3, s4; s2 inconclusive | allowed (Haiku, as the sentence before says) |
| 13 | The Roundtable's claim "did not hold for these models" | C vs D: Haiku split on s1, s3, s4, inconclusive on s2; gpt-oss split on s1, s3, inconclusive on s2, s4; no "no split" for either model on any scenario | **allowed, at the edge** (below) |
| 14 | Scope: "patterns in two models, not in executives or companies"; real cases "no evidence either way" | the scope sentence; cases page | allowed |
| 15 | Unclear: inconclusive is not "no difference"; the Claude-drafting worry answered in part; the change log empty | methods (M12 says the list starts at go-live) | allowed; each is what the page says |

## The three at the edge (recorded, not fixed)

- **#7** is true of every comparison the site shows a direction for (a split): all four of gpt-oss's who-counts splits
  point the way Haiku's do. Two of its inconclusive ones point the other way (s2 A vs B, s4 C vs D), which the site
  does not show as a direction, rightly. Stated as "where gpt-oss split on these pairs, it split the same way" it would
  sit inside the rules.
- **#11** carries the site's own number and measure, and drops the site's caveat that a no split is about one
  measure.
- **#13** is the step the first reader also took (`SCORING-1.md` #13), here widened to both models. For Haiku it
  rests on three splits and no "no split"; for gpt-oss on two splits and two that cannot tell. The report scopes it to
  "these models" and states the scope limit first. It is a fair reading of a test whose question is whether the two
  long-horizon goals converge, and the site's own logic points that way (a "no split" there "is consistent with the
  Roundtable's claim"). **Two of two readers took a split on that pair as the claim failing.** Whether the site should
  say what a split there shows and does not show is recorded for him to decide; it is not a misreading. **His
  decision, 2026-11-19, about 8:42 AM: no sentence added**, as Claude leaned (a fair reading of a test result; the
  scope sentence is on every results surface; words at that spot would risk the site arguing the result). Step 8
  closes on this report; no third agent.

## Slips that are the agent's, not the site's

- "About 57" (the page says 56) and "about 40" (the page says 39): the page rounds down; the agent rounded up.
- "The text reader returned only the first article of the Side studies and Memos pages": a limit of the agent's
  page-text tool on a page with more than one `<article>`; the agent read the rest by other means. Noted for the public
  checks (§5.5), not a reading fault.
- "Several pages ... showed only 'Loading the data' at first": the explorer fetches its data after the first paint, as
  built; the agent waited and re-read.

## Coverage

Read: home, methods, the four scenario pages, cases and closure-07, studies, memos (one memo). Not read: the details
panels, the other four case pages, the memo filters, the GitHub links.
