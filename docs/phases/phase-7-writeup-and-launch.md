# Phase 7 — Write-up and Launch (v1.0)

> **Scope doc.** Written 2026-10-04 from `planning/00` §2, §8 and §10, `planning/03` §1, `planning/05` §5 (Phase 7's
> row) and §6, `planning/06` §1, §4-6, §8-9 and §11, and the Phase 6 and 6.5 scope docs. **APPROVED 2026-10-04
> (his)**, with all six decisions at the end taken as recommended. Not split.
> **Re-scoped 2026-11-22, APPROVED 2026-11-22 about 8:51 AM (his):** section "Re-scoped 2026-11-22", answering every
> opening below and correcting five facts (the models, the repo card, the missing README, the hosting, the cost pots);
> two new decisions, R-A (the Short, by bake-off) and R-B (the card now), both DECIDED 2026-11-22 (his).
> **IMPLEMENTATION doc APPROVED 2026-11-22, about 10:27 AM (his):** `phase-7-writeup-and-launch-IMPLEMENTATION.md`.
> Its decision D amends R-A: one Short, Gemini first, the cut from the site's renders only as the fallback.
>
> **Written to be re-scoped.** This phase starts after every other phase is built, probably weeks from now. Its
> purpose and its definition of done are fixed here; much of its content cannot be, because it depends on what the
> experiment found, what was cut, and what the public climate is by then. The section **"What is re-scoped when this
> phase starts"** lists those openings, so the update is a dated amendment, not a rewrite.
>
> Written before Phases 0.5 through 6.5 are built. **Lines marked *(rests on N)* depend on what Phase N builds,
> measures or decides.**

## What this phase is for

**v1.0: the project said in words, checked against its own promises, and sent out.** By now the experiment has run,
the site is live and checkable (Phase 6.5), and the record is public. This phase writes what sends people to it (the
README and the launch post), audits v1 against the definition of done in `planning/00` §8 with evidence for every
item, tags v1.0, and leaves the project in a state that costs nothing to keep and stays true after the model it
measured retires.

**The test of a good Phase 7:** a hiring manager who reads the README's first screen understands the question, sees
rigor, and finds the result stated no more strongly than the data allows; a hostile critic who reads the audit finds
every claim backed, and every shortfall already admitted.

## What scoping found

1. **README numbers can be tested; README claims go stale silently.** Musical Mycelium ties every README number to a
   marker that a test checks against the data, and a later phase still falsified five of its prose claims at once:
   the held-out result, the limits list, and other sentences no test read. Here, the README's numbers come from the
   published JSON, and its claims (limits, what was cut, what the results show) need their own check. Decision 3.
2. **The repo card may presuppose a result.** The description chosen on 2026-10-03 ends "measuring where decisions
   split." If the main result is "no split" on the comparison that tests the Roundtable's claim, the line reads as
   expecting the opposite. `planning/06` §1 makes a result in the Roundtable's favor as publishable as one against it,
   so the card is re-read against the results before launch. Delivers 4.
3. **The public prose has a standing rule and an allowed exception.** The rule (`planning/00` §10, `planning/06` §8):
   README, launch post, card and taglines are his. The exception, in the same rule: Claude drafts a piece when he asks
   on that pass. Both are legitimate; what matters is that each piece is decided on its pass, and that Claude's drafts
   carry an invisible watermark that rewording in his own words removes and retyping does not (`planning/06` §8).
   Decision 1.
4. **The order of release decides what a launch post can promise.** A post that goes out before the audit can cite a
   claim the audit later marks partial. Decision 2.
5. **The project outlives the credits.** The credits expire 2027-07-30 (`planning/03` §1). The site and the record are
   meant to stay up; after that date, whatever AWS still bills would be charged in cash, and the project's budget rule
   is that it never is. Decision 5.
6. **The model under test will retire.** Sonnet 4.6's end of life is not sooner than 2027-02-17. The site stays true
   if every result names its model and dates (`planning/04` §1.9), but a reader in 2027 should also be told, plainly,
   that the model is retired and the results describe it as it was.

## Delivers

In order (decision 2).

1. **The final rule-zero sweep:** `make guard-history` over every commit, branch and tag; the tracked-path check; and a
   read of every public surface (repo, site, releases, video captions) for anything identifying a company that the
   guard cannot catch (`CLAUDE.md`). Nothing is announced until this is clean.
2. **The README** (`planning/06` §6.1): the name explained in its opening (`planning/06` §6.4), the question in the
   Roundtable frame (`planning/06` §1), what was built and how, the honest note on why containers (`planning/02`
   §2.3, `planning/04` §3.1), the results in `planning/06` §4's allowed wording with run counts, the result against
   the thesis visible without scrolling past the end (`planning/06` §9 item 7), links to the site, the methods page,
   the pre-registration and the audit, and the limits. **Every number is tied to the published data by a test**
   (decision 3). Images are real renders from the site (charts, share cards), with light and dark variants; no emoji,
   no stock art.
3. **The plain-English write-up** of the whole project, in the repo, for a reader who will not open the methods page:
   what was asked, what was done, what was found, what it does not show. Drafted by Claude and reviewed by him, like
   the phase docs (`planning/06` §8), unless he chooses to write it.
4. **The repo card, re-read** against the results and the README (scoping finding 2); any change is his.
5. **The definition-of-done audit** (decision 4): every item in `planning/00` §8, and every phase's definition of
   done, marked met, partial or not met, each with its evidence (a commit, a file, a run ID, a URL). Partial passes are
   marked partial. Published in the repo.
6. **The final cost record:** total AWS spend from the bill against the $80 ceiling and the $60 re-plan point; the
   credit balance left for Musical Mycelium; the idle monthly bill measured after launch; OpenRouter and other
   non-AWS spend beside it. Stated on the methods page.
7. **The model's dates on every results surface** (scoping finding 6): the model, the run dates, and, once it
   retires, a dated line saying so.
8. **The v1.0 tag and a GitHub release,** created by him (Claude never runs `git tag`). The release title and notes
   follow decision 1.
9. **The launch post** (`planning/06` §6.1): it opens with the question or the Mayflower line, not a finding stated
   as a verdict; one chart; one sentence from `planning/06` §4's allowed column; the link. The vocabulary recheck
   (`planning/06` §11) is repeated if Phase 6.5's is more than a few weeks old. A second post is planned now
   (decision 6).
10. **The after-v1 list** (`ROADMAP.md` §5, `planning/05` §6) confirmed, each item still needing its own budget
    decision before its scope doc; and **the hosting plan** recorded with a dated reminder (decision 5).

## The rules this phase must not break

- **Every result sentence, anywhere, fits `planning/06` §4's allowed column,** with run counts. The README and the
  post are held to the same rule as the site.
- **The scope sentence is present** wherever results are: the project measures how a language model decides, not how
  human executives do (`planning/04` §1.3).
- **A result in the Roundtable's favor is stated as plainly as one against it** (`planning/06` §1). The project tests
  a claim; it does not argue for one (`CLAUDE.md`).
- **Public prose follows decision 1, piece by piece,** and every Claude-drafted line bound for a surface a reader would
  take as his is flagged when handed over.
- **Rule zero:** no company named, linked or identifiable on any surface, including the post and its image.
- **Nothing is claimed that the audit does not back.**
- **No paid promotion, and no spend that touches cash** (the credits, the ceiling, decision 5).

## Explicitly not in this phase

- **Any new run, analysis or view.** v1 is what Phases 4 to 6.5 produced.
- **Any after-v1 item** (more company types, the horizon sweep, the frequency study and the rest). Each needs its own
  budget decision first (`planning/05` §6).
- **Changes to his other projects' pages,** his profile or his portfolio site. His, outside this repo.

## Definition of done

1. **The final rule-zero sweep is clean** (Delivers 1).
2. **The README is in the repo,** every number tied to the published data by a test that `make check` runs, and its
   claims checked against the audit (decision 3).
3. **The audit is published,** every item marked met, partial or not met with its evidence (decision 4).
4. **The final cost record is on the methods page,** with the idle monthly bill measured.
5. **The v1.0 tag and release exist** (his).
6. **The launch post is published,** or he has set its date (his), and it passed `planning/06` §9's checks.
7. **The hosting plan is recorded** with its dated reminder (decision 5).
8. **`make check` and CI are green,** and every commit passed the guard.

## Prerequisites

- **Phase 6.5 complete:** the site live, every check passed.
- **His words**, or his grant for a draft, for each piece under decision 1.

## Cost

**$0 in AWS** (`planning/05`). Writing, auditing and tagging call no model. The idle bill after launch is measured,
not estimated: the target is under $1 a month (`planning/03` §6).

## The main model

The README and the audit name the model the protocol fixed (Sonnet 4.6, fixed 2026-10-05), with its dates. No
Sonnet 5.5 sweep is planned.

## What is re-scoped when this phase starts

Expected to change, by a dated amendment to this doc before its IMPLEMENTATION doc:

- **What the results say**, which sets the README's lead result and the post's one sentence, chosen from the
  `planning/06` §1 table row that the data actually supports.
- **What was cut** under `planning/05` §5.1, if anything, and how the README and audit say so.
- **The vocabulary climate** and any new Roundtable statement (`planning/06` §11).
- **Which impressive pieces shipped** in Phase 6 and 6.5, and which images the README can use.
- **The tools**, if the post uses any (an image tool, the video): availability and cost, checked live.
- **The launch timing,** his, set against whatever else is happening that week.

## Re-scoped 2026-11-22 (Claude-drafted; APPROVED 2026-11-22, about 8:51 AM, his)

Written at the phase's start, after Phase 6.5's close (`6450b93`). Each opening above is answered from the repo, and
four facts this doc assumed on 2026-10-04 are corrected. **Where this section and the text above disagree, this
section governs.**

### R.1 What the results say

Read 2026-11-22 from the two official grids (`experiment/results/prereg-v1/<model>/grid-*.json`, `final_verdict` on
each primary comparison):

| Pair | Haiku 5.5 (S1 / S2 / S3 / S4) | `gpt-oss-120b` (S1 / S2 / S3 / S4) |
|---|---|---|
| A vs C (horizon, shareholders) | split / inconclusive / inconclusive / inconclusive | inconclusive / not assessable / inconclusive / split |
| A vs B (who counts, four quarters) | split / split / split / split | split / inconclusive / split / inconclusive |
| **C vs D (who counts, twenty years)** | **split / inconclusive / split / split** | **split / inconclusive / split / inconclusive** |
| B vs D (horizon, all stakeholders) | no split / inconclusive / no split / inconclusive | inconclusive / inconclusive / inconclusive / split |

- **The `planning/06` §1 row the data supports is "C and D split":** over twenty years, who counts still changed the
  model's decision, on three of four scenarios for Haiku 5.5 and two of four for `gpt-oss-120b`, every split robust
  across the three wordings. **No scenario shows "no split" on C vs D for either model**, so the row the Roundtable's
  "in the long term" predicts ("A and B split, but C and D do not") appears nowhere. The README's lead result and the
  post's one sentence come from that row, in §4's allowed wording with run counts; which scenario and chart lead is
  his.
- **The inconclusive cells are stated as inconclusive**, not as half a split, and S2 (inconclusive on C vs D for both
  models; one `gpt-oss-120b` comparison not assessable, its failure rate) is named, not dropped.
- **The section for results against the thesis holds two entries,** both Haiku 5.5, both B vs D "no split" (S1 and
  S3): with all stakeholders counted, the longer horizon did not change the decision (`web/explorer-data/index.json`,
  `against_thesis`, by the Phase 6 IMPLEMENTATION doc §19's rule). The README shows them without scrolling past the end
  (`planning/06` §9 item 7).
- **The real cases are reported pre-registered result first:** the rule found no case (shortfalls 2, 2 and 1); the
  five cases are exploratory, all closures, three with a leakage disclosure; all 20 readings are "no good match"
  (methods page ledger lines 16, 20, 20a, 20b). Any README or post line on the cases says that, in that order.

### R.2 What was cut

**Nothing** under `planning/05` §5.1 (Phase 5.5's cost check; methods ledger line 38). Two substitutions are not
cuts and are said as substitutions wherever the models are named: `gpt-oss-120b` for Nova Pro as the second family,
and Haiku 5.5 for Sonnet 4.6 as the Anthropic model, both because Bedrock was blocked (KNOWN-GAPS BLOCKED 2026-10-05;
protocol 5.1; Phase 3.5 IMPLEMENTATION doc §23).

### R.3 Corrections to this doc's 2026-10-04 facts

1. **The main model (replaces "The main model" above).** The official models are **Haiku 5.5** (Anthropic's API) and
   **`gpt-oss-120b`** (OpenRouter), fixed by the protocol before the tag; Sonnet 4.6 is not in v1's official set, and
   no new sweep is planned. Scoping finding 6 and Delivers 7 apply to both: Haiku 5.5's tentative retirement is "Not
   sooner than October 7, 2027" (Anthropic's model deprecations page, read 2026-11-22, with at least 60 days' notice);
   `gpt-oss-120b` has open weights, so it does not retire as such, but the host that served it can stop, and the
   dated line then says so. The README and the audit name both models with their run dates.
2. **The repo card is now wrong on facts,** not only possibly on tone (scoping finding 2). Read live 2026-11-22, it
   says "one AI" (v1 has two models) and "on AWS Bedrock" (the models were reached through Anthropic's API and
   OpenRouter after Bedrock was blocked). Its "measuring where decisions split" does not misdescribe the result. The
   website field is empty. The card is his words (decision 1); when it changes is decision R-B.
3. **There is no README yet.** The root holds 14 entries against the cap of 16; `README.md` makes 15.
4. **The hosting picture under decision 5 changed:** the public URL is already a free host's
   (`horizon-compact.vercel.app`, a Vercel rewrite to the CloudFront distribution, Phase 6.5), and the raw text is
   already in the public repo (Phase 6.5 decision A). So the 2027-06-30 plan is smaller than written: serve the built
   files from the free host directly, then tear down the distribution and bucket, or keep them on a stated cash
   budget. Free hosts' terms are still checked live at the time. The budgets' 2027-10-01 end (the reminder's
   2026-10-08 note) stays in the plan.
5. **The cost record has three pots, not one:** AWS credit (expiring 2027-07-30), Anthropic prepaid credit, and his
   OpenRouter cash (`evidence/phase-5.5/cost.md`). The OpenRouter spend is cash and the record says so; this phase
   itself calls no model.

### R.4 The vocabulary climate

Phase 6.5's recheck (M10, `evidence/phase-6.5/public-checks/README.md`, 2026-11-21) found no new Roundtable statement
on corporate purpose and nothing new for the word list. **"A few weeks" in Delivers 9 is set at three:** if the
launch post goes out after 2026-12-12, the recheck runs again before it.

### R.5 What shipped that the README and post can use

The explorer (14 paths, each with its own share card), the methods page and its ledger, the section for results
against the thesis, the Explainer video (two logged departures, disclosed on M11), the full raw text with the
re-scoring check in CI, and the prompt reconstruction. Images are real renders from the site; the site has light and
dark styles, so both variants exist. The image list is the IMPLEMENTATION doc's.

### R.6 Tools: the Short

Phase 6.5 decision C held **a Short** for this phase's post; this doc predates it. It is not made
(`evidence/phase-6.5/video/README.md`). **It is made (decision R-A), about a minute long, for the LinkedIn post,
by a bake-off:** one candidate from Gemini Notebook's Short format (the existing notebook and source pack, capped at
three attempts) and one cut built from the site's own renders (captured by the headless browser Phase 6 uses, with
motion and burned-in captions, over his voice reading his own script or on-screen text only). Both pass the
Explainer's frame and narration check; he picks by eye. Before either is made, the IMPLEMENTATION doc re-reads live:
Gemini Notebook's formats and cost, any comparable tool worth a third candidate, and LinkedIn's current video specs
(aspect ratio, length, captions). Two rules hold for whichever wins: **the scope sentence appears in substance** (an
end card is enough), and **narration that speaks for him in his post is his words** (the Explainer's Claude-written
script was a logged departure, not a precedent). A generated clip carries the AI-generated label.

### R.7 Launch timing

His. On the calendar: 2026-11-26 is Thanksgiving. The post is his standing choice for LinkedIn, whose Post Inspector
already matched the site (Phase 6.5 step 11). His decision of 2026-10-05 for the post stands: its "The hardest part"
section is about AWS (the quotas set to zero and the support case), with how the build continued (the move to
Anthropic's API and OpenRouter, 2026-10-11). The words are his.

### R.8 Carried in from earlier phases

- **The `horizon-compact-dev` access key** is deleted at this phase's close or on 2027-01-02, whichever is first
  (Phase 1.5 decision 6). Added as Delivers 11 and DoD 9.
- **M12's changelog:** any change to the live site in this phase gets an entry.
- **The search check's two private cross-appearances** (Phase 6.5 step 10, not hits): his call whether to coarsen
  further, made in Delivers 1's sweep.
- **The uncommitted START HERE block and row 1 note** from Phase 6.5's close ride in this phase's first commit (his
  choice, 2026-11-21).

### R.9 Changes to Delivers and the definition of done

- **Delivers 7** covers both models (R.3 item 1).
- **Delivers 4** reads the card against facts as well as results (R.3 item 2). **By decision R-B, a first
  correction comes first** (Delivers 0 below), and Delivers 4 re-reads it against the finished README.
- **Added, Delivers 0, before the rule-zero sweep:** his corrected card line, typed into GitHub by him, fixing "one
  AI" and "on AWS Bedrock", and the website field set to `https://horizon-compact.vercel.app`. A minimal correction;
  the final wording waits for Delivers 4. Rule zero applies to it as to any text typed into GitHub. *Dated note,
  2026-11-22:* **Claude drafted this correction at his request on this pass** (decision 1's allowed exception),
  flagged as Claude's words with the watermark when handed over; it passed the name guard's message check. His
  rewording, if any, is his call at Delivers 4.
- **Delivers 6** states all three pots (R.3 item 5).
- **Added, Delivers 11:** the dev access key deleted (R.8). **DoD 9:** it is deleted, or Phase 7 closed after
  2027-01-02 and it was deleted on that date.
- **Added, Delivers 12 (decision R-A), before the launch post:** the Short, by the bake-off in R.6. **DoD 10:** the
  chosen Short passed the frame and narration check and carries the scope sentence.

### R.10 Two new decisions for him (both DECIDED 2026-11-22, his)

- **R-A. The Short. DECIDED 2026-11-22, about 8:48 AM (his): make it, by bake-off** (R.6). *Amended 2026-11-22, about
  10:12 AM (his, the IMPLEMENTATION doc's decision D): one Short, made well; the Gemini Short first under a
  three-attempt cap, the cut from the site's renders only if no Gemini attempt passes or he wants none that does.
  R.6 and Delivers 12 read accordingly.* "I do think we need a
  dynamically short video of a minute or so for the LinkedIn release." *Was:*
  - (a) Make it, from the same notebook, under the Explainer's check, before the post.
  - (b) Claude's first lean: drop it, a logged departure from Phase 6.5 decision C. **Withdrawn by Claude** in
    discussion: it went against his standing view (2026-11-14) that the video is to be made to work, not dropped, and
    that the launch post is a place a clip helps. The bake-off replaced both options.
- **R-B. When the repo card changes. DECIDED 2026-11-22, about 8:48 AM (his): (a), as leaned.** *Was:*
  - (a) **Claude's lean: now, before the README,** since it is public and false today (R.3 item 2), with the website
    field set to the site; re-read again at Delivers 4 against the finished README.
  - (b) At Delivers 4 only, in the order decision 2 set.

## Known risks

- **The README claims more than the data, or claims something a later fix changed.** Mitigation: decision 3's test for
  numbers and the audit for claims; the README is re-read against the audit before launch.
- **A launch post read as a verdict on companies or executives.** Mitigation: `planning/06` §4 and §9, the scope
  sentence, and the Roundtable frame, which takes executives at their word rather than accusing them.
- **The result is unwelcome to the thesis he started with.** That is a publishable result (`planning/06` §1), and the
  fixed section for results against the thesis has existed since Phase 1.5 so that publishing it is the default.
- **Something identifying slips into the post or its image.** Mitigation: the final rule-zero sweep covers the post
  draft and its image before it goes out.
- **Hosting quietly starts billing cash after the credits expire.** Mitigation: decision 5's plan and its reminder.

## Decisions for him

All six taken 2026-10-04 (his), as recommended. Each keeps its original framing under *Was:* as the record.

1. **DECIDED 2026-10-04 (his): (a), by piece.** *Was:*
   **How each piece of public prose is produced.** Decided on each pass, by this rule:
   - (a) **Recommended: by piece.** **The README and the release notes:** Claude may draft on his grant, with the
     watermark noted once when handed over; he edits. **The launch post and the repo card:**
     his words by default, with Claude interviewing, outlining and critiquing line by line (`planning/00` §10); a
     Claude draft only if he asks for one on that pass, flagged, which he then rewords in his own words if he wants
     the watermark gone. **The plain-English write-up:** Claude drafts, he reviews, like the phase docs.
   - (b) Claude drafts every piece and he approves each one, the watermark kept wherever he approves a draft
     unchanged.
   - (c) Every public piece in his own words, Claude interviewing and critiquing only.
2. **DECIDED 2026-10-04 (his): (a), the launch post last.** *Was:*
   **The order of release.**
   - (a) **Recommended:** the rule-zero sweep, then the README, the write-up and the audit, then the cost record, then
     the v1.0 tag and release, and **the launch post last**, so the post can link the audit and cites nothing it
     marks partial.
   - (b) The post as soon as the site is live, with the README and audit following.
3. **DECIDED 2026-10-04 (his): (a), numbers tied to data, claims tied to the audit.** *Was:*
   **How the README stays true.**
   - (a) **Recommended: numbers tied to data, claims tied to the audit.** Every README number sits between markers that
     a test checks against the published JSON, run by `make check` (the system Musical Mycelium uses). Every README
     claim that is not a number (limits, cuts, what the results show) cites an audit item, and the audit is re-read
     against the README at every later change.
   - (b) A careful read before launch, no test.
4. **DECIDED 2026-10-04 (his): (a), a fresh session re-verifies a sample.** *Was:*
   **How the audit is checked.**
   - (a) **Recommended: Claude audits, then a fresh session re-verifies a sample cold.** Claude marks every item with
     its evidence; a fresh session with no working history, given only the public repo and site, re-checks a sample
     of at least ten items, including every item marked met that the README leans on. Free on his existing plan.
   - (b) Claude and he only.
5. **DECIDED 2026-10-04 (his): (a), planned now so it never bills cash.** Reminder in `KNOWN-GAPS.md`. *Was:*
   **Where the project lives after the credits expire (2027-07-30).**
   - (a) **Recommended: plan now so it never bills cash.** Measure the idle bill monthly from launch. By 2027-06-30,
     either move the static site to a free static host and keep the published record in the public repo, then tear
     down the AWS hosting and archive the raw results bucket's contents where they cost nothing, or decide with him,
     before the date, to keep AWS hosting on a stated cash budget. A dated reminder goes in `KNOWN-GAPS.md`. Free hosts
     and their terms are checked live at the time.
   - (b) Decide when the date is near.
6. **DECIDED 2026-10-04 (his): (a), two posts, planned now.** *Was:*
   **The launch posts.**
   - (a) **Recommended: two, planned now.** The launch post (the question, one chart, the link) and a second, a week
     or two later, on the method: the pre-registration, the sealed wording, and what went against the thesis, which is
     the part a technical reader trusts. Planning the second now keeps it from depending on how the first is received.
     Both his, under decision 1.
   - (b) One launch post.

## Left for the IMPLEMENTATION doc

The README's outline and its image list. The marker scheme and its test. The audit's format and the sample the fresh
session re-checks. The release title and notes. The cost record's sources. The hosting plan's reminder date and
checklist. The post's chart. The order of the commits and of the steps on launch day.
