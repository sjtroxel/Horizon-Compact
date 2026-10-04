# Phase 6.5 — Methods and Release (v0.6.5)

> **Scope doc.** Written 2026-10-04 from `planning/00` §8, `planning/04` §1.3, §2.5 and §5, `planning/05` §5 (Phase 6's
> row, as patched 2026-10-04), `planning/06` §4-9 and §11, `planning/07` §11-12, and the Phase 3.5, 4, 5.5 and 6 scope
> docs. **APPROVED 2026-10-04 (his)** with Phase 6: its rules come from Phase 6's decisions 2-6, all approved that day.
> It adds no decision of its own.
>
> **Split out of Phase 6 on 2026-10-04** (his, Phase 6 decision 1). Phase 6's scoping findings cover this half too
> (`docs/phases/phase-6-explorer.md`).
>
> Written before Phases 0.5 through 6 are built. **Lines marked *(rests on N)* depend on what Phase N builds, measures
> or decides.**

## What this phase is for

**The explorer made checkable, then put live.** Phase 6 built the explorer on a preview build. This phase writes the
methods page a hostile reader would need, proves that every published number can be recomputed and every prompt
rebuilt, runs every public check, makes the narrated video, and then replaces the placeholder at
`horizon-compact.vercel.app` with the whole thing in one deploy.

**After this phase, the project is public in the sense that matters:** a stranger can find it, read it, and check it.
Phase 7 then writes the words that send people to it.

**The test of a good Phase 6.5:** a hostile reader with only the public site and the published files can recompute
every number on it, rebuild any prompt, and find nothing on any page that claims more than the data shows.

## Delivers

In order.

1. **The methods page** (`planning/06` §6.1, in that order): the scope sentence first; the objectives in full;
   scenarios and the lever menu with each lever's meaning per scenario; models, dates, run counts; the
   pre-registration (the tag, its outside timestamp, the archive, and what changed after it: the errata and any
   `prereg-v2`); the run-code change log from Phase 4; the disclosure asymmetry and how cases were found, with the
   public selection log; which cases can be re-run from published inputs and which dossiers were withheld (Phase 5
   decision 5); the parallel objective wording and what it traded away; the cut list as applied, if anything was cut;
   cost, measured; known limits; and a plain statement that re-asking a model gives a new sample, not the same numbers.
   Technical descriptions drafted by Claude and approved by him; titles and any sentence that speaks for the project
   his (Phase 6 decision 3).
2. **The re-scoring check, in CI** (Phase 6 decision 4): a job recomputes the published JSON from the published raw
   responses with the published code and fails on any difference. It reads only published files, never S3
   (`planning/02` §2.11).
3. **The prompt-reconstruction check** (Phase 6 decision 4): a fresh session, given only the public site and the
   published inputs, rebuilds sample prompts (at least one per scenario and one real case whose dossier was
   published), compared byte for byte with the logged prompts. Any mismatch is a gap in the methods page, fixed and
   re-checked.
4. **The cold-read test** (Phase 6 decision 6): a browser agent (Claude in Chrome, from his sprint) opens the preview
   build with no context and reports what it concludes. Every conclusion `planning/06` §4 does not allow is a
   misreading, fixed in the site and re-tested.
5. **The narrated video overview** (Phase 6 decision 6): made with Gemini Notebook from the methods page and the
   published results only; narration from the tool, or from ElevenLabs if he chooses it, with its cost named first.
   Checked frame by frame and line by line against the data and §4; anything wrong is corrected or regenerated before
   publishing; labeled on the site as AI-generated, with the tools named. Nothing in it is the only place a fact
   appears.
6. **The public checks** (`planning/06` §9) on every surface, including the story, the share cards and the video; the
   four-reader notes (`planning/06` §5) recorded; the search check on every public case description (`planning/06`
   §6.3); the memo name scan confirmed on what is actually deployed.
7. **The vocabulary recheck** (`planning/06` §11): the sources re-read live, any new Roundtable statement looked for,
   the result dated on the methods page.
8. **The teardown test, again, if `main` changed** since Phase 1.5 (`planning/05` §5): destroy, re-apply, rewrite
   updated, page back, raw results intact.
9. **Go-live** (Phase 6 decision 2): the explorer, the methods page and the video replace the Phase 1.5 placeholder in
   one deploy. The live site is then checked against the preview, view by view.
10. **The changelog** on the methods page, from go-live on: a dated list of every change to the live site.
    Presentation can be fixed; a published number changes only through the protocol's own rules (errata or
    `prereg-v2`, Phase 3.5 decision 6), and the changelog says which.

## The rules this phase must not break

- **Every claim fits `planning/06` §4's allowed column,** on every surface, the video included.
- **The scope sentence is on every results surface,** and first on the methods page (`planning/04` §1.3).
- **Nothing goes live until every check in Delivers 2-7 passes** (Phase 6 decision 2).
- **Generated media is labeled and checked;** a frame or line that says more than the data is fixed before it ships.
- **Rule zero,** on every page, file, asset, video frame and caption.
- **No visitor tracking** (Phase 6 decision 5). The video, if hosted outside the site, is linked, not embedded with a
  third-party player that tracks viewers *(how it is hosted is checked in the IMPLEMENTATION doc)*.
- **Public words are his where `planning/06` §8 says so;** Claude-drafted lines are flagged when handed over.

## Explicitly not in this phase

- **The README, the launch post, the repo card and the plain-English write-up.** Phase 7.
- **New views or analyses.** Phase 6 built the explorer; this phase checks and ships it.
- **Paid promotion of any kind.**

## Definition of done

1. **The methods page is complete** against Delivers 1, and he has approved it.
2. **The re-scoring job is in CI and passes;** it fails when one published number is changed by hand, shown once.
3. **The prompt-reconstruction check passes** for every sample, or every gap it found is fixed and re-checked. Where a
   dossier was withheld, the page says that case cannot be re-run, and why.
4. **The cold-read test's conclusions are all within `planning/06` §4,** after fixes, with its record committed.
5. **The video passed its frame-by-frame check and is labeled,** or he decided not to publish it, with the reason.
6. **Every `planning/06` §9 check passes on every surface;** every public case description fails to identify its
   company in a search; every published real-case memo passed the name scan (`planning/05` Phase 6 done-when, as
   patched 2026-10-04); the vocabulary recheck is dated.
7. **The site is live** at `horizon-compact.vercel.app` and matches the preview.
8. **`make check` and CI are green,** and every commit passed the guard.

## Prerequisites

- **Phase 6 complete:** the explorer on its preview build, his words for titles and the scope sentence in place.
- *(rests on 1.5)* The deploy path and the Vercel name.
- *(rests on 3.5)* The tag, its outside timestamp and the archive, for the methods page to link.
- **His accounts for the sprint's tools,** rechecked live: Claude in Chrome, Gemini Notebook, and ElevenLabs if he
  chooses it.

## Cost

**Under $2 in AWS** (`planning/05`): no experiment call; hosting is cents. **Outside AWS:** Claude in Chrome and the
fresh reader run on his existing Claude plan; Gemini Notebook ran on a free tier in the sprint *(rechecked live)*;
ElevenLabs, if he chooses it, costs what its plan costs, named before he decides. None of it touches the AWS credits.

## The main model

Nothing here depends on which model is main. The methods page names every model from the provenance.

## Known risks

- **The methods page is accurate but unreadable.** Mitigation: the prompt-reconstruction check is the readability
  test that matters, and the four readers (`planning/06` §5) read it too.
- **A generated piece says more than the data.** Mitigation: the frame-by-frame check, the label, and correcting or
  regenerating before publishing.
- **Go-live breaks something the preview did not.** Mitigation: the live site checked against the preview, view by
  view, and the changelog for anything fixed after.
- **The vocabulary climate has shifted** since 2026-10-03. Mitigation: the recheck runs before go-live, and any change
  goes through `planning/06`'s rules before a word moves.

## Left for the IMPLEMENTATION doc

The methods page's outline, section by section. The CI re-scoring job. The fresh reader's brief and the sample prompts
it must rebuild. The cold-read brief and how its findings are recorded. The video's source pack, its checklist and
where it is hosted. The go-live checklist and the live-against-preview check. Versions of every package and action,
checked live. The order of the commits.
