# Phase 7, step 1: the rule-zero sweep, first pass

The IMPLEMENTATION doc's step 1 (`docs/phases/phase-7-writeup-and-launch-IMPLEMENTATION.md`), run 2026-11-23 by Claude
(Opus), read-only. Each surface the name guard cannot read was read in full against rule zero's spirit (a name, a
ticker, a brand, a plant location, or a description detailed enough to point to one company), not only its term list.
This record names no term, no private path and no description beyond the coarse ones already public.

## 1. The commands

Run from `main` at `29296ab`, working tree clean.

| Command | Output line |
|---|---|
| `make guard-history` | `name guard: history clean, 177 commit(s) scanned.` |
| `make paths-check` | `paths-check: no tracked path under methods-appendix/ (5977 tracked files).` |
| `make doctor` | `doctor: hooks installed (pre-commit, commit-msg, pre-push); term file loads with 108 terms and 15 allowed phrases; longlist fingerprint matches.` |

`guard-history` reported ten binary files it did not scan: the video and its poster (`web/explorer-media/`), four
fonts (`web/fonts-ttf/`) and four Phase 1.5 screenshots (`docs/phases/screenshots/phase-1.5/`). The video, the poster
and the screenshots are read as images in section 2; the fonts carry no text to read.

## 2. The surfaces the guard cannot read

| Surface | What was read | Result |
|---|---|---|
| Repo description and website | `gh repo view`: the one-line description, the website field (`https://horizon-compact.vercel.app`), no topics | clean |
| Releases | `gh release list`: one, `prereg-v1`; `gh release view prereg-v1`: name `prereg-v1`, empty notes, no assets | clean |
| Issues | `gh issue list --state all`: none | clean |
| Pull requests | `gh pr list --state all`: none | clean |
| Branches | `git branch -a`: `main`, `origin/main` | clean |
| Tags and tag messages | one tag, `prereg-v1`, annotated; its message is scanned by `guard-history` (clean, above); his `git tag -l -n99`, pasted about 9:03 AM: `prereg-v1       prereg-v1: protocol v1`, read by eye | clean |
| The 14 live paths | each rendered in a headless browser from `horizon-compact.vercel.app` and its full text taken (title, meta tags, alt and label text, chart text, body); every line read, the long per-run dot lists aside, which are generated labels (goal, wording, repeat, a percentage) | clean |
| The same text, by term | the 14 extracts and the captions run through the guard's own matcher (`scan_text` with the configured term file; a canary of one term matched, so the file was live) | 0 findings |
| The built site | every text file of the local build, 104 (HTML, JS, JSON, the captions), through the same matcher; its entry bundle is the live site's (`explorer-B1sUZ_Th.js` on both) | 0 findings |
| The video's captions | all 59 cues of `horizon-compact-explainer.vtt`, read in full | clean |
| The video's frames | the shipped MP4 at one frame every two seconds, 82 frames, grouped as Phase 6.5's `check.sh` groups them: 12 distinct, each read as an image | clean |
| The poster | `horizon-compact-explainer-poster.jpg`, read as an image (the title frame) | clean |
| The 14 link-preview cards | `web/dist-explorer/cards/*.png`, each read as an image; three spot-checked against the live site by sha256, identical | clean: the real-case cards show only the label, the exploratory line and the coarse description already public (`pre-11` shows "Description: withheld") |
| The Phase 1.5 screenshots | `page-1280-light.png` read in full as an image (the placeholder garden-club page, test runs only); the other three are the same page at another width or colour scheme, from the same commit, and were not read separately | clean |
| The README images | not made yet (step 4) | for the second pass |

What the full read looked for beyond the term list: on the real-case pages, any detail past the coarse description
(industry group, decision type, revenue band, half-year, in or outside the US), and there is none; the memos page
shows only the made-up company's memos, and the site shows no real-case memo text; the names that do appear (the
Business Roundtable, the Mayflower Compact, the UN Global Compact, Software Heritage, the model vendors and hosts) are
public references, not cases.

## 3. The two private cross-appearances

Phase 6.5's search re-run found a case's company on another case's page, twice (`docs/phases/evidence/phase-6.5/public-checks/README.md`, "Not done here").
Under the rule they are not hits; whether to coarsen further is his call. Claude reminded him on 2026-11-23. **His
call, about 9:03 AM: no further coarsening**; the descriptions stay as published ("let's just go ahead onwards as
is"). No site change follows, and the search check is not re-run.

## 4. Result

**Done.** Every surface is clean, with no finding to fix; the tag message is read and the cross-appearances are left
as published, by his decision. A second, shorter pass runs before the tag (step 12) and before the post (step 13).
This record rides in C2 (`phase 7: c2 rule-zero sweep and dates`) with step 2.
