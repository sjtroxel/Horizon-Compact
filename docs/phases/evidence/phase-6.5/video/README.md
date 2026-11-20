# Phase 6.5 step 9: the video, as run (2026-11-20)

The record of how the methods page's video (M11) was made and checked: doc section 6, "As run, step 9". Every file
named here is in this folder unless a path says otherwise. The videos of attempts 1 to 4, their frames and the end card
were kept in the scratch folder, which git ignores; their sha256 hashes are below.

## The tool and the settings

- **Gemini Notebook** (Google; renamed from NotebookLM in July 2026), in his Google account, a new notebook made for
  this step. Its help page was re-read live on 2026-11-20 and matched the record of 2026-11-14 (doc section 4): three
  formats (Cinematic, Explainer, Short), a steering prompt, producer notes reviewed before rendering, download.
- **Notebook memory off** ("use notebook memory, consider all chats in the notebook when responding" was on; he turned
  it off before anything was generated). The notebook's own instructions box left blank. No chat typed in the notebook.
- **Every attempt: Explainer, English, visual style Classic, "Review producer notes" on, "Generate now".** Producer
  notes were reviewed by Claude before each render. Pressing Enter in the feedback box submits the feedback and renders
  at once; the revised notes are not shown again.
- His usage bar read 89% after attempt 2 (his read; Google states no number). Attempts 3 and 4 ran after it reset.

## The sources

- **Attempts 1 and 2:** the source pack, 14 PDFs, every explorer page printed from the local preview of `c136692` by
  `source-pack.mjs` (light scheme, every details part opened). `source-pack-manifest.json` has each file's path, title,
  size and sha256. The preview was rebuilt from HEAD first.
- **Attempt 3:** the same notebook with only `01-methods.pdf` and `02-story.pdf` ticked.
- **Attempt 4 (kept):** only `narration-script.txt` ticked (the 14 PDFs unticked, not deleted). **This departs from
  doc section 6 item 1** ("nothing else is uploaded"): the script was written by Claude from the site's pages at his
  request (2026-11-20, 11:17 AM, his idea; his edits to tone and close at 11:36-11:40 AM), every figure in it checked against
  the explorer's data files (`web/explorer-data/index.json` `against_thesis`; `web/explorer-data/grid/*/s*.json`, the
  C vs D comparisons). Reason: three attempts from the site's own pages each drifted (below).

## The check (doc section 6 item 4)

`check.sh`: ffmpeg 6.1.1 (Ubuntu build) takes a frame every two seconds; consecutive frames under 150 pixels changed by
more than 24 grey levels are grouped, and the last frame of each group is read (a group's frames carry the same text).
The narration is transcribed locally by faster-whisper 1.2.1 (MIT; released 2025-10-31; model `medium.en`, CPU, int8),
run in scratch and never shipped. Claude read every distinct frame and every transcript line against the site and
`planning/06` section 4; he listened to each attempt through.

At 9:23 AM he chose to keep the narrator's energy ("I liked the hype"); rating words ("rigorous", "proves") stayed out.
At 11:58 AM the gate was split (his agreement): a wrong number, a reversed direction, a claim past section 4, on-screen
text not in the sources and a missing scope fail; tone, agenda slides, plain section titles and length are his call.

| Attempt | Sources | Length | Verdict | Why |
|---|---|---|---|---|
| 1 | 14 PDFs | 6:58 | fail | Haiku s1 A vs C read the wrong way round, as against the expectation; gpt-oss C vs D given 60 and 60 runs (it is 58 and 60); "proves the integrity"; "over 5,000" raw objects (not on the site); the Oct 16 search called exploratory; "every response published" without its scope on screen; "AI decision-making" in general. `attempt1-check.md` |
| 2 | 14 PDFs | 4:37 | fail | arrows between the four decisions (his catch); "300 runs" for one goal (300 is five goals); the against-expectation table lists Haiku s4 A vs C and gpt-oss s3 B vs D, which the site does not, and misses Haiku s1 B vs D; C vs D not reported. `attempt2-check.md` |
| 3 | 2 PDFs | 5:45 | fail | "a goal's horizon, or its compact"; Plant 6 not described; the steering prompt's own words read aloud ("there are no arrows, there is no sequence"); all his catches. Its numbers matched the data. `attempt3-check.md` |
| 4 | the script | 2:39 | kept, one edit | below |

### Attempt 4

Every figure spoken or shown is right with its run count: Haiku C vs D on the jobs decision about 19 points fewer kept
(60 runs of each goal), gpt-oss about 45 (58 and 60); Plant 6 closed more often under the long-term shareholder goal by
both; the ten-year program funded less often by Haiku, gpt-oss inconclusive; falling orders inconclusive for both; the
two Haiku B vs D results that are no split; all five real cases no good match. Twelve distinct frames, each in the
script's words or a title.

Must-fix failures, both at the end: **the scope was missing** (the script's "it doesn't show how real executives decide,
and it predicts nothing about any real company" and "a company that doesn't exist" were dropped), and **"Every response
they gave on it is published" followed the real-cases sentence**, so "it" reads as the real cases, whose replies are not
published.

Kept and disclosed on the page (his call, 12:08 PM): "the prevailing logic" for the project's own expectation;
"macroeconomic pressures" as the cause of falling orders, which the scenario does not state; "the following orders"
(faster-whisper hears "following", 0.91 confidence, on two passes) where the decision is falling orders; Haiku's jobs
count given as "across 60 runs" (it is 60 of each goal).

### The edit: a second departure from doc section 6

Doc section 6 item 4 says a failure "is fixed by steering and regenerating, not by editing around it." **He chose
(12:17 PM) to keep attempt 4 with one edit instead, logged as a deviation.** The reason: the edit removes the one wrong
sentence and adds the site's own words; it does not patch a wrong claim with a new one. With ffmpeg: attempt 4 from 0 to
151.9 s (the silence after "this is a comparison, not a verdict"), then an 8 s silent card of `his.json`'s
`scopeSentence` in Source Sans 3 (the site's face) on the outro's background colour, then attempt 4 from 155.8 s (the
Gemini Notebook outro, silent). Re-encoded H.264 CRF 23 and AAC 128 kb/s, faststart. The kept video was put through
`check.sh` again: 82 frames, 12 distinct, all read; its transcript is attempt 4's less the cut sentence
(`final-transcript.txt`).

## The files shipped (served at `/media/` by the explorer build only, from `web/explorer-media/`)

| File | Bytes | sha256 |
|---|---|---|
| `horizon-compact-explainer.mp4` (2:43, 1280x720, 24 fps) | 4,166,942 | `57dd96860aa1a050035c605bd7cd5046c5d0269f1c4486e8037103ad02f5056f` |
| `horizon-compact-explainer-poster.jpg` (its frame at 1 s) | 54,321 | `2f1a37213574b77465533f2a245d651ed7db5392e0f504b33de81a122aafb499` |
| `horizon-compact-explainer.vtt` (59 cues, from `final-transcript.txt`) | 4,487 | `39d58c398a360a435df4fa92a12d03a92e3b45824f5fb7b8983bf757c00da00e` |

The captions are the kept transcript with spelling only normalised ("GPT OSS 120B" to "gpt-oss-120b", "plant six" to
"Plant 6", "10-year" to "ten-year"); `methods.test.ts` holds the page's transcript equal to them cue by cue.

The folder is `web/explorer-media/`, not `web/public/` as decision F said: both builds copy `public/`, and the
placeholder page must not change before go-live. The video plays on the live site only after go-live adds
`media-src 'self'` to the content security policy in `bootstrap` (doc section 7); the local preview serves the same
policy, so it shows the poster and the transcript but blocks playback (and logs two policy errors on `/methods/`) until then.

## Rule zero

A binary file is the one surface the name guard cannot read. The frame read is its check: every distinct frame of every
attempt was read, and none shows a company's name, a place or anything outside the sources. The source pack is the
site's own pages, and the script names no real company.

## Hashes of what was not shipped

| File | sha256 |
|---|---|
| attempt 1 (`Horizon_Compact_AI_Study.mp4`) | `8c400cd7f241abf5cd89a0ebef691d66374d5305ef04abd71102c246245146e1` |
| attempt 2 (`Horizon_Compact_Study.mp4`) | `7894c5027bbd1ecd9856750f00ea0ba5f5c1984aa3f3075ff30e0d00b3e8d32f` |
| attempt 3 (`draft3.mp4`) | `3e74c1e27c615f80ef10ccb52c1d35146ad85829c9cef8e480e237f4eafced74` |
| attempt 4 (`draft4.mp4`), before the edit | `12859e26b98bea159abe6cb8febd2b287047b0315e6e8ea3a1d2824840c3c525` |
| the end card (`endcard.png`) | `f2880bd4a50d65da86f0d684389bae1520fc9a5c412cba3a53007310336c3f41` |

Still to do with this video: the Short for Phase 7 (doc section 6 item 3) is not made; `media-src 'self'` at go-live.
