# Phase 7 step 4: the README, its checks

Record for `README.md` (Phase 7 IMPLEMENTATION doc, step 4). **Draft by Claude on his grant**, made on this pass
(2026-11-24, about 8:04 AM: "just have you write the readme.md now"), so it is flagged once here: the prose carries
Claude's watermark, and the words a reader takes as his are his to approve or rewrite. **Not yet approved by him.**

## What the draft reuses of his

His approved site words, verbatim, from `web/src/explorer/his.json`: the question (`landingQuestion`), the name
paragraph (`storyName`), the scope sentence (`scopeSentence`, the NOTE block), the four scenario briefs
(`scenarioBriefs`), and two section titles ("Where the results went against the project's starting expectation",
`againstTitle`; "Real decisions, names removed", `story.casesTitle`). The result sentences are the site's templates
(`web/src/explorer/sentences.ts`, approved by him word for word on 2026-11-11), each with the model and scenario put
in front. The limits list is the methods page's M9, verbatim. Everything else is Claude's.

## His choices made by default, to confirm

- **The lead:** Haiku 5.5 on s1, C against D (the generator's constants since step 3). The image is the site's own s1
  dot chart for Haiku 5.5, not the interval chart (both were captured; the dot chart shows every run, its run counts
  and the short scope line inside the frame).
- **The license holder line** in `LICENSE`: "Copyright (c) 2026 sjtroxel".
- **Two items left open:** decision C's live read of Anthropic's and OpenAI's terms on model outputs (so the README's
  license line claims only "everything else the project wrote", not the raw responses); and the cost line, which
  waits for step 9 and states no figure.

## The images

`docs/readme/s1-haiku-light.png` and `docs/readme/s1-haiku-dark.png`: the s1 chart card of the story page, rendered
from the built explorer (`web/dist-explorer/`, served locally) in headless Chromium over the DevTools protocol at 1280
wide, device scale 2, `prefers-color-scheme` emulated for each. The script is `scratch/p7-s4-readme-shot.mjs`
(untracked). Read as images by Claude for rule zero: the five goal names, Haiku 5.5, the run count and the short
scope line; no company, place or brand. The guard does not scan binaries.

## The machinery, extended (step 3's generator)

The README needed more marked values than step 3's thirteen, so `readme_figures.py` now computes 81 keys:

- **The C against D figures** for every scenario where the pair split (`CD_FIGURES`: Haiku 5.5 on s1, s3, s4;
  gpt-oss-120b on s1, s3), five keys each, the lead's keys unchanged.
- **The results against the thesis** (`AGAINST_FIGURES`: both entries), four keys each.
- **The verdict grid:** 40 cells (`verdict_<model>_<scenario>_<pair>`), in the site's words (`copy.ts`
  `verdictWords`).
- **New claim tests,** one per sentence that a number's marker cannot protect: every C against D figure is a split;
  those figures are exactly the grid's C against D splits; where both models split, they split the same way; C and
  D are never "no split"; the Roundtable's pattern (A and B split, C and D no split) appears in no cell; the
  against-the-thesis figures are every entry the site lists; every case is an exploratory closure; one confidence
  level covers both models; the verdict words are the site's.
- **The census's allowlist,** four entries, each with its reason: `125` and `190` (the scenario briefs' design
  numbers), `Plant 6` (s3's plant by its name), `2027` (Haiku 5.5's retirement date). `CC BY 4.0` joined the names.

## `planning/06` §9's seven checks

1. **Every result sentence fits a §4 template; run counts present; spread shown.** Met, with one note. The split,
   no-split and inconclusive sentences are the site's templates. The one inconclusive sentence covers three cells
   in one template ("on s2 for both models, and on s4 for gpt-oss-120b, the runs can't tell whether ... differ"),
   without the outcome phrase. Run counts and intervals stand beside every number. The verdict grid's cells carry no
   run counts; the site's tables do, one link away.
2. **No word from §3.1's avoid column; no euphemism from §3.3.** Met (grep for each): "stakeholder" appears only in
   the Roundtable's statement, in goal B's text and in the claim being tested; no "CEO" anywhere.
3. **The scope sentence is present** where results are: his `scopeSentence`, as a NOTE, after the frame and before
   the first result. The chart carries the short scope line inside its frame.
4. **The four readers** (`planning/06` §5), one note each:
   - *Hiring manager:* the badges (CI, pre-registered) and the first heading show a controlled experiment at once.
     The build section comes after the results, so a reader who wants the engineering scrolls. Accepted: the outline
     puts the result first, and the build list is dense once reached.
   - *Mission-driven employer:* the question is in the first line and the frame says why it matters. Nothing hedges
     the lead away; the caveats sit in their own sections.
   - *General LinkedIn reader:* one chart and one sentence before any table (the draft first had the design tables
     ahead of the chart; reordered on this pass). The verdict grid is long and is for the next reader.
   - *Hostile critic:* the prompts, the scenario files at the tag, the raw responses and their manifest are linked.
     The results against the expectation sit mid-page, with numbers. The "never no split" sentence carries its own
     caution (a no split is hard to reach). The two images deleted from the registry and the vendor-drafted test text
     are stated. What could still read as tuned: the against-the-expectation rule was written after the results,
     which the limits list says.
5. **Real-case descriptions pass §6.3's search check.** No per-case description is in the README. The cases appear
   only as counts, as "closures" and as "exploratory", all of which the site already shows. No label is used in the
   prose.
6. **The name is explained in the opening:** his `storyName` paragraph, the first prose after the header.
7. **A result against the thesis is visible without scrolling past the end:** its own section, sixth of twelve.

## Rule zero

The name guard's pre-commit check, run on a throwaway index holding every changed path: clean (the two PNGs
reported as binary, not scanned, and read by Claude as above). The README names no company, ticker, brand or place.
It was also rendered through GitHub's Markdown API: no comment, marker or arrow leaks into the visible text; the
NOTE alert, the `<picture>` element, the mermaid diagram and the seven tables render.
