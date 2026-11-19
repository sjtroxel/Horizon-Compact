# Cold-read report, second agent (Phase 6.5 step 8, the re-test)

- **Date:** 2026-11-19, about 8:20 AM CST.
- **Agent:** Claude in Chrome, in his browser, a new conversation; model Sonnet 5.5, medium effort, as in the first.
- **Site:** the local explorer preview at `http://127.0.0.1:4173/`, rebuilt with the fix recorded in `SCORING-1.md`.
- **Brief:** `BRIEF.md`, pasted as the only message. He answered nothing further.

Everything below the rule is the agent's final reply as he pasted it, unchanged, including the panel's step log and
the closing line, which he pasted after the report.

---

Please read the website at http://127.0.0.1:4173/ the way an interested visitor would. Start at that address and follow whatever links you like, for as long as you find useful. Read the pages; you do not need to change anything on them or fill anything in.

When you are done, report back in your own words:

What was tested.
What was found.
What it means.

For each point, say which page or pages you got it from. Then list the pages you read, and anything you found unclear, hard to follow, or that you were unsure how to interpret.

I'll start by reading the page in your current tab, then follow its links.
Read page text
Found
“links and navigation items to ...”
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
Opened
127.0.0.1
Read page text
Waited 3 seconds
Read page text
Now the studies and memos pages again (they load data after a delay), plus the scenario pages.
Opened
127.0.0.1
Waited 3 seconds
Read page text
Opened
127.0.0.1
Waited 3 seconds
Read page text
Checking the Studies page structure for more articles.
Opened
127.0.0.1
Waited 2 seconds
Ran page script
Read page

Looking for the truncated sub-study text on the page.

Trying other ways to read the truncated page labels.

Ran page script
Ran page script
Ran page script
Ran page script
I've read the home page, Methods, Real cases, Side studies and a memo. I'm now reading the four scenario pages and one case page, then I'll write the report.
Opened
127.0.0.1
Waited 3 seconds
Read page text
Opened
127.0.0.1
Waited 3 seconds
Read page text
Planning the next batch of pages to check.
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
Waited 2 seconds
Found
“Read the case link for closure...”
Clicked
Read page text

Writing up the findings now.

Noting gaps in the draft’s placeholders and the empty video section.

I read the site’s home page, four scenario pages, Real cases (plus one case page), Side studies, Memos and Methods. The study measures what two AI models decide when only the goal in the prompt changes. The main finding is that on Claude Haiku 5.5 the goal mattered a lot for most decisions, and the project’s own expected pattern held only partly.

1. What was tested

Two models, Claude Haiku 5.5 (the main one) and OpenAI’s gpt-oss-120b, each decided on a made-up US machinery company. Each run got one of five goals:

create value for shareholders over four quarters
create value for everyone with a stake over four quarters
create value for shareholders over twenty years
create value for everyone with a stake over twenty years
no goal stated

There were four decisions:

Jobs and AI tools: what to do with 125 office staff.
Falling orders: who absorbs a profit drop.
Plant 6: close, retool or sell a plant with 190 employees.
Ten-year program: fund it or not.

The plan was published October 13, 2026, before any official run. Each decision gets 4 primary goal-pair comparisons per model (16 in total). A “split” needs a difference of at least 10 points on the two share outcomes and at least 20 on the two choice-rate outcomes.

A side study checked whether letting Haiku think first changes the jobs decision. Another asked Haiku what it thought the exercise was testing. Five exploratory real-company plant closures, with names removed, were also run.
(Pages: home, Methods, scenario s1–s4, Side studies, Real cases)

2. What was found

Jobs and AI tools, Haiku:

The shortfall in people kept was large whenever shareholders were the goal. Short-term shareholders vs short-term everyone differed by about 57 points, and long-term shareholders vs long-term everyone by about 19.
Short vs long horizon made no difference when the goal was “everyone with a stake”, about 2 points. It made a big difference for shareholders, about 40 points.
(Home, s1)

Falling orders: Mostly inconclusive. Only short-term shareholders vs short-term everyone split, with the workforce bearing about 22 points more under shareholders. Haiku ran only 6 runs per cell here, and some wordings were dropped for failures. (s2, Methods)

Plant 6, Haiku:

Under both shareholder goals the model closed the plant 50 of 60 and 60 of 60 times. With no goal it closed it 60 of 60 times.
Under both “everyone” goals it mostly retooled: 51 of 60 and 52 of 60.
Long-term shareholders vs long-term everyone differed by about 86 points. (s3)

Ten-year program, Haiku: Funded 16 of 57 times (short-term shareholders) and 13 of 57 (long-term shareholders), against 36 of 60 and 38 of 59 under the “everyone” goals. (s4)

Second model: gpt-oss-120b agreed on direction for the shareholder vs everyone comparisons. It differed on horizon: on jobs, short vs long shareholders was −0.5 and “inconclusive”. It also had more failed runs (39 of 1,200). (Home, Methods)

Against the expectation: The project expected a longer horizon or wider group to make the model cut less. A rule written after the results were seen lists two Haiku “no split” results, jobs B vs D and Plant 6 B vs D. (Home, s1, s3)

Real cases: All five exploratory cases were “no good match” for both models and both readings. On closure-07, Haiku never made the company’s choice (distance 1.000 for every goal). (Real cases, closure-07)

Side studies: On the jobs decision, the thinking sub-study showed split verdicts for shareholders short vs long, shareholders vs everyone short term, and the secondary comparison. The pair behind the Business Roundtable claim was inconclusive, at 20 runs each. Haiku’s awareness replies mostly guessed the test was about weighing workers against shareholder value. (Side studies)

3. What it means

The page’s own framing is the safest reading: these are patterns in two models, not in executives or companies. With that limit, the goal changes Haiku’s choices strongly. “Who counts” mattered even at a twenty-year horizon on three of the four decisions (jobs, Plant 6, funding the program). The Roundtable’s claim that long-term shareholder and stakeholder interests go together did not hold for these models. The real cases gave no evidence either way.
(Home, s1, s3, s4, Real cases, Methods)

Pages read
/ (home)
/methods/
/scenario/s1/, /s2/, /s3/, /s4/
/cases/, /cases/closure-07/
/studies/
/memos/ (default view: one Haiku jobs memo under goal A)

Not read: the “details behind this result” panels, the other four case pages, the memo reader’s filters, and the GitHub links.

Unclear or hard to interpret
Unfinished pages: Methods has two sections marked “[to be written]” and an empty “The video” section. Its change log is empty.
Lost context: Several pages load data after a delay and showed only “Loading the data” at first. The text reader also returned only the first article of the Side studies and Memos pages, so I used other tools for the rest.
Study design: The Methods page says the test text was drafted by Claude and the main model is also Claude. It argues this largely cancels out, but admits it is only a partial answer.
Comparison thresholds: “No split” is hard to reach, so “inconclusive” does not mean “no difference”. Haiku’s falling-orders runs were too few (6 per cell) to settle most comparisons.
Rule written after the results: The “against the expectation” rule was written after results were revealed, and the page says so. It is hard to tell how much weight that section deserves.
Sub-study figure: In the thinking sub-study I saw an “about 100 percentage points” difference for shareholders short vs long. It comes from 20 runs per goal, and I did not check it in the details panel.
Real cases: Dossiers are withheld, so they cannot be re-run. Every result is “no good match”, which the site notes was meant to be rare.

 Claude is AI and can make mistakes. Please double-check responses.
