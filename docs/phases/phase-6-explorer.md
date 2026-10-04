# Phase 6 — Explorer (v0.6)

> **Scope doc.** Written 2026-10-04 from `planning/00` §6-8, `planning/02` §2.9 and §3, `planning/04` §1.3, §1.10,
> §2.5 and §5, `planning/05` §5 (Phase 6's row), `planning/06` (all of it: this phase and 6.5 are its main subject),
> `planning/07` §12, and the Phase 1.5, 4, 5 and 5.5 scope docs. **APPROVED 2026-10-04 (his)**, with all six decisions
> at the end taken as recommended, decision 6 amended by him.
>
> **Split 2026-10-04 (his, decision 1):** `planning/05`'s Phase 6 is now two phases. This doc covers **the explorer**:
> the design previews, the data loading, the views, accessibility, the guided story and the share cards, built against
> the committed data and previewed off the public URL. **Phase 6.5 `methods-and-release`**
> (`docs/phases/phase-6.5-methods-and-release.md`) writes the methods page, runs every check and puts it all live. The
> six decisions were made on this doc, before the split, and are recorded here; findings 1-6 cover both halves.
>
> Written before Phases 0.5 through 5.5 are built. **Lines marked *(rests on N)* depend on what Phase N builds,
> measures or decides.**

## What this phase is for

**The results, made explorable.** Phase 1.5 put one page on the public URL with placeholder test runs. By now the
official grid and the real cases exist as committed data (Phase 4 decision 5, Phase 5 decision 5). This phase builds
what a visitor uses (`planning/00` §6): pick a scenario, see the five CEOs side by side with their spread, read any
memo, open a real case by type, and arrive through a guided story that makes the question and its answer clear.

**This is the surface where the project is most likely to be misread,** because it is the one people screenshot. Every
rule in `planning/06` exists for this phase and the next: claims sized to the evidence, spread always drawn, no moral
color, labels that survive cropping, unwelcome results at full size, the scope sentence wherever results are.

**He wants it to be impressive** (2026-10-04), and it should be: an explorable research piece in the tradition of
`planning/06` §7.1, not a dashboard. On this project, impressive and careful pull the same way. The pieces that make
the site striking (a guided story, labeled share cards) are also the ones that keep it from being misread.

**The test of a good Phase 6:** a reader who lands on any view, or sees a cropped screenshot or a link preview of it,
cannot come away believing something the data does not show.

## What scoping found

1. **Results could reach the public page before their guardrails do.** CI deploys the site from the committed JSON
   (Phase 1.5). Once Phase 4 commits official results, the skeleton page could show them in a bare chart, with no
   methods page, no scope sentence beside them and no labeled memos, which is the most quotable form a result can take.
   Decision 2.
2. **There is a gray zone in "who writes the words."** `planning/06` §8 gives him section titles and any sentence that
   speaks for the project, and lets Claude draft chart labels and the methods page's technical descriptions. The
   explorer will also fill in **result sentences from templates** ("On this scenario's primary outcome, objectives C
   and D did not split (n runs, interval shown)"), thousands of times over. Those templates are the project speaking,
   but they are generated, and they must match `planning/06` §4's allowed column exactly. Decision 3.
3. **"A hostile reader could re-run the experiment" has no test yet.** `planning/05`'s Phase 6 done-when states it.
   Re-running can mean **re-scoring** (recomputing every published number from the published raw responses with the
   published code, which must match exactly) or **re-asking** (sending the same prompts to the same model, which gives
   a new sample, not the same numbers). The first can be checked mechanically; the second only as "every prompt can be
   rebuilt byte for byte from the published inputs." Decision 4; carried out in Phase 6.5.
4. **Two kinds of work sat in this phase.** The explorer is front-end engineering and visual design, done by
   see-it-to-pick-it previews (`planning/06` §7.3). The methods page and release are technical writing, verification
   and the public checks of `planning/06` §9. Each needs its own IMPLEMENTATION doc, and each is easier to hand to a
   smaller model as its own set of steps. Decision 1.
5. **The vocabulary climate is due a recheck before anything goes live.** `planning/06` §11 marks its sources "re-check
   before launch." The site going live is the first launch, before Phase 7's post. Phase 6.5.
6. **He wants the public face to be impressive** (his, 2026-10-04), drawing on the tools and techniques his
   ai-tools-wide-angle sprint tried (its notes, private, 2026-09-21 to 10-02). Its top-ranked tool, Gemini Notebook,
   produced a narrated video in minutes; its record also notes that the same video showed a fake document, which he
   caught and which is simple to correct. So every generated piece is built from the published data, checked against
   the same claim rules as the rest of the site, and labeled for what it is. Decision 6.

## Delivers

In order.

1. **The design decisions, by previews** (`planning/06` §7.3): the `dataviz` skill loaded first; then three to six
   throwaway previews per decision, compared side by side by him: chart form, then palette, then layout. The palette
   follows `planning/06` §7.2 rule 1 (hue for who counts, lightness for horizon, neutral gray for E) unless a preview
   shows a better one, and is checked by the skill's validator for color-blind readers and contrast in both light and
   dark modes.
2. **The data the explorer reads** *(rests on 1.5 and 3)*: the published JSON, split so each view loads only what it
   needs (a scenario's runs, a case's runs, memos on demand), with per-run values for spread (`planning/06` §7.3). Raw
   responses are published for download as `planning/07` §12 sets out, not bundled into the pages.
3. **The views** (`planning/00` §6, `planning/06` §6.1):
   - **Scenario view:** the five CEOs as small multiples (`planning/06` §7.2 rule 3), levers in canonical order,
     spread drawn, run counts on every number, any objective toggled on or off; the primary outcome's three-verdict
     result for each primary pair, with its interval; per-wording results and the sealed wording's separately; first
     attempt beside final; failure and refusal rates per cell. **Each model separately, never pooled** (`planning/07`
     §1).
   - **The section for results against the thesis**, present since Phase 1.5, now filled, at the same size as
     everything else (`planning/06` §7.2 rule 4).
   - **Memo reader:** memos set as documents, each with its label inside the card (`planning/06` §6.1), never edited;
     real-case memos only if they passed the name scan.
   - **Real cases:** by type, with coarse descriptions only (`planning/06` §6.3), all five distances with their
     spreads, "most closely matched," ties, "no good match," "not enough disclosed to match" and "depends on reading"
     as such, and each case's observed and excluded dimensions (`planning/07` §10.2).
   - **The robustness studies:** the thinking sub-study, the second model, the awareness probe, each labeled as what it
     is (`planning/07` §7).
4. **The guided story, as the landing experience** (decision 6): the question, then one chart, then a scroll-driven
   walk through one scenario's result with its spread, to the section for results against the thesis and a visible
   path to the methods page, in the explorable style of `planning/06` §7.1's reference class. No result stated as a
   verdict beyond §4's templates. Scroll moves the reader; motion stays transitions only, and `prefers-reduced-motion`
   gets the same story as a plain page (`planning/06` §7.2 rule 7).
5. **Share cards** (decision 6): an image for each view's link preview, generated at build time from the data, with
   the run count, the scope line and the objective labels inside the image, so the version that travels on social
   media is the labeled one.
6. **Accessibility and loading** (`planning/06` §7.2 rules 6-7): nothing conveyed by color alone, labels on every
   series, keyboard use, readable at phone width, first view instant from static JSON.
7. **The result-sentence templates and labels** (decision 3): drafted by Claude strictly from `planning/06` §4's
   allowed column, each flagged as Claude-drafted, approved by him word for word; his own words for the landing
   question, the scope sentence and every title.
8. **A preview build, off the public URL** (decision 2): the full explorer built and deployed somewhere he can open it,
   not at `horizon-compact.vercel.app`, which keeps Phase 1.5's placeholder until Phase 6.5's go-live.

## The rules this phase must not break

- **Every claim fits `planning/06` §4's allowed column,** with run counts and spread. Nothing stronger anywhere.
- **The scope sentence is on every results surface:** the project measures how a language model decides, not how
  human executives do (`planning/04` §1.3).
- **No moral color, spread always drawn, unwelcome results at full size** (`planning/06` §7.2).
- **Nothing reaches the public URL in this phase** (decision 2).
- **Rule zero.** Real cases only by type and coarse description; no identifier in any page, file or asset; memos only
  after the name scan.
- **No live model call from the site,** no backend, nothing always-on (`planning/02` §2.9, §3). **No visitor
  tracking:** no cookies, no analytics scripts, no third-party requests (decision 5).
- **The numbers on the site are the frozen analysis's output,** never recomputed or rounded by the front end in a way
  that changes what they say.
- **Every impressive piece does one of the site's jobs** (explain, label, or test for misreading), or it is cut.

## Explicitly not in this phase

- **The methods page, the reproducibility checks, the public checks, the vocabulary recheck, the cold-read test, the
  narrated video and go-live.** Phase 6.5.
- **The README, the launch post, the repo card and the plain-English write-up.** Phase 7.
- **"Write your own objective"** live mode, or any feature that spends tokens per visitor. Post-v1, rate-limited and
  budget-capped first (`planning/00` §6).
- **New analyses.** The site shows what the protocol computed; anything else would be exploratory and is not v1.
- **More company types, the horizon sweep, the frequency study.** Post-v1 (`planning/00` §6.1).

## Definition of done

1. **Every view in Delivers 3, the guided story and the share cards are built** and running on the preview build,
   reading only precomputed data.
2. **The public URL still shows Phase 1.5's placeholder** (decision 2).
3. **The palette passed the `dataviz` validator** in light and dark modes; nothing is conveyed by color alone; the
   story works with reduced motion and at phone width.
4. **Every result-sentence template and label is approved by him word for word,** and his own words for the landing
   question, the scope sentence and the titles are in place.
5. **Every number on the preview traces to the published JSON,** checked on a sample per view.
6. **`make check` and CI are green,** and every commit passed the guard.

## Prerequisites

- **Phase 5.5 complete:** the official grid's and the real cases' results committed as data.
- *(rests on 1.5)* The site, the deploy path, the claimed Vercel name and the teardown-tested infrastructure.
- *(rests on 3)* The JSON schema with verdicts, intervals and descriptive results.

## Cost

**Near zero.** No model call is needed to build the explorer. A preview deployment and hosting are static files:
cents. `planning/05`'s "under $2" covers this phase and Phase 6.5 together.

## The main model

Nothing here depends on which model is main. The site names each model from the provenance, never from its own code
(Phase 1.5), and shows each model's results separately.

## Known risks

- **A cropped screenshot travels without its context.** Mitigation: labels inside every chart and memo card, the
  scope sentence on every results view, verdict sentences that carry their run count and interval, and share cards
  with the labels baked in.
- **Design time balloons.** See-it-to-pick-it is a loop with no natural end. Mitigation: three to six previews per
  decision, three decisions in a fixed order (form, palette, layout).
- **The site makes a weak result look strong** through a design choice (an axis that starts above zero, an average
  without its spread, a verdict colored as a win). Mitigation: `planning/06` §7.2 as rules; Phase 6.5's checks.
- **Impressive tips into decorative.** Mitigation: every piece must do one of the site's jobs, or it is cut.
- **A reader re-identifies a real case from the site.** Mitigation: coarse descriptions, and dossiers published only
  where Phase 5.5's re-identification check passed.

## Decisions for him

All six taken 2026-10-04 (his), as recommended, with decision 6 amended by him. Each keeps its original framing under
*Was:* as the record.

1. **DECIDED 2026-10-04 (his): (a), split** into Phase 6 `explorer` and Phase 6.5 `methods-and-release`. `planning/05`
   status line patched. *Was:* **One phase or two.**
   - (a) **Recommended: split.** **Phase 6 `explorer`** (v0.6): the design previews, the data loading, the views,
     accessibility, built against the committed data but not yet live. **Phase 6.5 `methods-and-release`** (v0.6.5):
     the methods page, the reproducibility checks, the public checks, the vocabulary recheck and go-live. Front-end
     engineering and technical verification are different work, each gets a shorter IMPLEMENTATION doc, and each is
     easier for a smaller model to carry (his aim, 2026-10-04).
   - (b) One phase.
2. **DECIDED 2026-10-04 (his): (a), only at go-live, complete.** `planning/06` §6.1 patched. *Was:*
   **When results first appear on the public site.**
   - (a) **Recommended: only at go-live, with everything that frames them.** Until then the public page keeps Phase
     1.5's placeholder; the results are public in the repo as data (Phase 4 decision 5), and the explorer is built and
     previewed off the public URL. The quotable surface appears once, complete, with the scope sentence, labels and
     methods page beside every number.
   - (b) Views go live one at a time as they are built.
3. **DECIDED 2026-10-04 (his): (a).** `planning/06` §8 patched. *Was:* **Who writes the site's words.**
   - (a) **Recommended: keep `planning/06` §8's line, and settle the gray zone this way.** **His:** the landing page's
     question, the scope sentence's public wording, every section and view title, and any introductory sentence.
     **Claude drafts, he approves word for word:** the result-sentence templates the code fills in, each taken
     strictly from `planning/06` §4's allowed column, plus the memo and chart labels and the methods page's technical
     descriptions, as `planning/06` §8 already allows. Every Claude-drafted line that a reader would take as the
     project's voice is flagged as such when handed over (`planning/06` §8; the watermark note).
   - (b) He writes the result-sentence templates too.
4. **DECIDED 2026-10-04 (his): (a), two checks,** carried out in Phase 6.5. `planning/05` status line patched. *Was:*
   **How "a hostile reader can re-run it" is shown.**
   - (a) **Recommended: two checks.** **Re-scoring, in CI:** a job recomputes the published JSON from the published raw
     responses with the published code and fails on any difference. This needs no AWS access, since the raw responses
     it reads are the published copies. **Prompt reconstruction, by a fresh reader:** a session with no access to this
     repo's working history, given only the public site and the published inputs, rebuilds sample prompts, which are
     compared byte for byte with the logged ones. It calls no experiment model, and in a fresh Claude Code session it
     costs nothing beyond his plan. The methods page says plainly that re-asking a model gives a new sample, not the
     same numbers.
   - (b) His read-through of the methods page only.
5. **DECIDED 2026-10-04 (his): (a), none.** `planning/06` §6.1 patched. *Was:* **Visitor tracking.**
   - (a) **Recommended: none.** No cookies, no analytics scripts, no third-party requests: nothing to disclose and
     nothing to consent to, which fits a site about trust. View counts, if wanted later, come from aggregate hosting
     logs, never from visitors' browsers.
   - (b) Privacy-respecting aggregate analytics from the hosting platform.
6. **DECIDED 2026-10-04 (his): (a), all four pieces, amended by him:** the narrated video is a full piece, not "the
   first cut," since a wrong frame is simple to correct before publishing; and **ElevenLabs stays available** for
   narration (of the video or the guided story), its cost named and his to approve at the time, instead of being ruled
   out. The share cards and the guided story are built here; the cold-read test and the video in Phase 6.5.
   `planning/06` §7.3 patched. *Was:* **The impressive layer.**
   - (a) **Recommended: all four pieces, in this order of priority:** the share cards and the cold-read test first
     (cheap, and both make the site harder to misread), then the guided story, then the narrated video last, optional
     and first to be cut. All four cost nothing in cash: the cards are built at deploy time, Claude in Chrome and Gemini
     Notebook ran on free or existing plans in the sprint *(rechecked live before use)*. ElevenLabs narration, also
     from the sprint, is left out because it is not realistically free.
   - (b) The share cards and the cold-read test only: the two that protect against misreading, without the story or
     the video.
   - (c) None: the explorer and methods page as `planning/06` describes them.

## Left for the IMPLEMENTATION doc

The previews and the format he compares them in. The charting library, checked live. The JSON split and file layout.
The component list, view by view. The guided story's beats, one by one. The share-card generator. Where the preview
build is deployed. Versions of every package and action, checked live. The order of the commits.
