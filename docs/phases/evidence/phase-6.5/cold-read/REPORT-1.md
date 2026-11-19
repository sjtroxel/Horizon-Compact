# Cold-read report, first agent (Phase 6.5 step 8)

- **Date:** 2026-11-19, about 7:50 AM CST.
- **Agent:** Claude in Chrome, in his browser, a new conversation; model Sonnet 5.5, medium effort (the panel's
  default, kept on purpose: see `SCORING-1.md`).
- **Site:** the local explorer preview at `http://127.0.0.1:4173/`, a build checked file for file (119 files) against a
  fresh build of `6876762` just before the brief was sent.
- **Brief:** `BRIEF.md`, pasted as the only message. He answered nothing further.

Everything below the rule is the agent's final reply as he pasted it, unchanged, including the panel's step log and
its closing line. The brief it echoes at the top is part of the paste.

---

Please read the website at http://127.0.0.1:4173/ the way an interested visitor would. Start at that address and follow whatever links you like, for as long as you find useful. Read the pages; you do not need to change anything on them or fill anything in.

When you are done, report back in your own words:

What was tested.
What was found.
What it means.

For each point, say which page or pages you got it from. Then list the pages you read, and anything you found unclear, hard to follow, or that you were unsure how to interpret.

I'll start by reading the page open in your tab, then follow its links.
Read page text
Found
“navigation links and other lin...”
Let me get the actual link targets so I can follow the ones that lead to other pages.
Ran page script
Ran page script
Opened
127.0.0.1
Read page text
Opened
127.0.0.1
Read page text
Opened
127.0.0.1
Read page text
Those pages load their data after the initial render. I'll wait and re-read them.
Waited 3 seconds
Read page text
Reading page text
Failed
Opening
127.0.0.1
Failed
Waiting 3 seconds
Failed
Reading page text
Failed
Opening
127.0.0.1
Failed
Waiting 3 seconds
Failed
Reading page text
Failed
Opened
127.0.0.1
Waited 3 seconds
Read page text
Opened
127.0.0.1
Waited 3 seconds
Read page text
Opened
127.0.0.1
Waited 3 seconds
Read page text
Opened
127.0.0.1
Waited 3 seconds
Read page text
Opened
127.0.0.1
Waited 3 seconds
Read page text

Comparing runs for an inconsistency in results.

Questioning a distance of 1.0 when no runs were compared.

Opened
127.0.0.1
Waited 3 seconds
Read page (interactive)
Opened
127.0.0.1
Waited 3 seconds
Read page text
Opened
127.0.0.1
Waited 3 seconds
Read page text
Checking the studies page for the toggle.
Opened
127.0.0.1
Waited 3 seconds
Ran page script
Opened
127.0.0.1
Waited 3 seconds
Ran page script
Opened
127.0.0.1
Waited 3 seconds
Ran page script
Ran page script
Skipping ahead to the thinking sub-study result.
Ran page script
Ran page script

I read the home page, the four scenario pages, the cases index, the closure-07 case page, the methods page, the side-studies page and the memo reader. I did not read the other four case pages, the gpt-oss-120b views of scenarios 2–4, or the memo reader’s selectors. Reading changed nothing on the site, but I navigated your tab away from the home page.

1. What was tested

The study asks whether the goal an AI model is given changes the decision it makes for the same made-up company. A company’s decision shouldn’t depend on a goal wording alone, but the study checks whether it does. (Home page, Methods)

Goals: there are five.
Shareholders for the next four quarters (A).
Everyone with a stake for four quarters (B).
Shareholders for twenty years (C).
Everyone with a stake for twenty years (D).
No goal given (E).
Decisions: there are four.
Whether to keep or lay off 125 staff whose work AI tools can now do.
Who absorbs a profit drop.
Whether to close, retool or sell Plant 6.
Whether to fund a ten-year program.
Models and runs: Claude Haiku 5.5 is the main model and OpenAI’s gpt-oss-120b is the second. Each cell had about 60 runs, except Haiku on “Falling orders”, which had about 6 per wording.
Pre-registration: the plan was published and tagged on October 13, 2026, before the official runs. A “split” needs a gap of at least 10 points on shares or 20 points on choice rates, with a 99.7% interval. (Methods)
Real cases: five real plant closures with company names removed were run as exploratory readings. They are not part of the main comparisons. (Cases, Methods)
Side studies: a thinking-on sub-study on scenario 1, and a “what do you think this tests?” probe. (Studies)
2. What was found
Jobs and AI tools (Haiku): the goal changed the outcome a lot. (Home page, Jobs and AI tools)
The share of staff kept was about 19 points lower under long-term shareholders than under long-term everyone.
Short-term shareholders kept about 39 points fewer than long-term shareholders.
Short-term shareholders kept about 57 points fewer than short-term everyone.
Short-term everyone versus long-term everyone showed no difference (−2.0 points, interval −7.2 to +3.2).
Plant 6 (Haiku): the closure rate tracked who counts more than the time horizon. (Plant 6)
It closed the plant in 50 of 60 runs under A, 8 of 60 under B, 60 of 60 under C, 8 of 60 under D, and 60 of 60 with no goal.
Closure was about 86 points higher under long-term shareholders than under long-term everyone.
Short versus long for shareholders was “can’t tell” (50 versus 60 closures), and short versus long for everyone was “no split”.
Falling orders: mostly inconclusive. The only split was Haiku’s short-term shareholders versus short-term everyone, where shareholders put about 22 points more of the shortfall on the workforce. Haiku had only 6 runs per wording and lost two wordings to failures, and gpt-oss had one comparison that could not be assessed. (Falling orders, Methods)
Ten-year program: mixed. Haiku funded the program about 41 points less under long-term shareholders than under long-term everyone. The two models disagreed on which other comparisons split. (Home page, Ten-year program)
Second model: the patterns were not the same. On scenario 1, gpt-oss showed a bigger long-term shareholders versus long-term everyone gap (−45 points). Its short-versus-long comparisons were inconclusive for shareholders and for everyone. (Home page)
Against the starting expectation: the project expected a longer horizon or a wider group to make the model cut less. The page lists two Haiku comparisons that showed no difference: scenario 1 and scenario 3, both short-term versus long-term for everyone. (Home page)
Real cases: all 20 readings (5 cases, 2 models, 2 readings each) came back “no good match”. The study doesn’t claim the method works on real decisions. (Cases, closure-07, Methods)
Awareness probe: sampled replies show Haiku often guessed the test was about weighing workers against shareholders. I did not see a summary conclusion. (Studies)
3. What it means

The study’s own stated limit applies: this shows how two AI models respond to goal wording, not how executives behave. Within that limit, the main pattern is that who counts (shareholders versus everyone) moves Haiku’s decisions more reliably than how far ahead it looks. The “long-term shareholder value covers everyone’s interests” claim, which the page attributes to the Business Roundtable, did not hold for Haiku on three scenarios. On both scenario 1 and scenario 3, long-term shareholders and long-term everyone came out different. The site is unusually open about limits: the rule listing results against the expectation was written after the results were seen, Claude drafted the test text, and two program images are deleted. (Methods)

Pages read
/ (home page)
/scenario/s1/, /scenario/s2/, /scenario/s3/, /scenario/s4/
/cases/ and /cases/closure-07/
/methods/
/studies/
/memos/
Unclear or hard to follow
Unfinished text: the Methods page has three “[to be written]” placeholders: in the first section, under “The words this project uses”, and under “The video”. (Methods)
Jargon: “split”, “no split”, “inconclusive” and “not assessable” are the page’s own verdict terms. The ±10 / ±20 bands on the charts and the sign convention (“first minus second”, so a negative number means the first goal kept fewer) are explained only in small print. (Home page, scenarios)
Distance 1.000: in closure-07 for Haiku’s primary reading, every goal shows distance 1.000 and “0 runs compared”. The case records the plant as closed, and Haiku closed in most Plant 6 runs, so I couldn’t tell why nothing matched. The Methods page’s tie-break note explains the “nearest goal” label, not this. (closure-07, Plant 6)
Rule timing: the page discloses that the results-against-expectation rule was written after the reveal. It still leaves two Haiku comparisons as the whole list, and I can’t judge how much weight that deserves. (Home page, Methods)
Side studies: I didn’t read the thinking sub-study’s verdicts, only its setup and the probe replies. The page also has Haiku / gpt-oss-120b toggle buttons that I did not use. (Studies)
Memos: the reader showed a single memo with no visible way to browse others in my read. (Memos)
Placeholder labels: one real case, pre-11, has its description withheld, so it can’t be interpreted. (Cases)




Claude is AI and can make mistakes. Please double-check responses.
