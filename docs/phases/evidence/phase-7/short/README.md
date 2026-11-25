# Phase 7 step 10: the Short, as run (2026-11-25)

The record of how the launch post's Short was made and checked (the IMPLEMENTATION doc §7). The video files were kept
in the scratch folder, which git ignores; their sha256 hashes are below. The Short is published with the launch post,
not on the site.

## The live reads (2026-11-25, about 4:22 AM)

- **Gemini Notebook's help page** ("Generate Video Overviews in Gemini Notebook"): three formats, Cinematic, Explainer
  and Short, the Short "~60 second videos"; a steering prompt; producer notes reviewed before rendering; visual style
  "excluding Cinematic and Short". No orientation stated on the page; press coverage of the format's launch describes
  it as vertical, and the file came back 720 by 1280.
- **LinkedIn's video help page** ("Video sharing troubleshooting"): aspect ratio 1:2.4 to 2.4:1, so 9:16 fits;
  15 minutes and 5 GB at most. Whether a post may carry a video and an image together is not on the pages read; it
  stays open for step 13 (§0 item 7).

## The tool and the settings

- **Gemini Notebook**, his Google account, a new notebook ("Horizon Compact Short"), notebook memory off, no chat.
- **Sources:** two PDFs printed from the live site at `03ba012` by `scratch/p7-s10-pack.mjs` (Phase 6.5's pack
  script, narrowed to two paths): `01-methods.pdf` (25 pages, sha256 `cbbd42a8...d471b`) and `02-story.pdf` (18 pages,
  `337b4b09...443df7`). Their text was checked for the lead figure and the scope sentence before upload.
- **Short, English, "Review producer notes" on.** The steering topic was Claude's, revised by him: the scope moved
  from the narration to an end card, and the narration ends on the result ("close with something much more
  emotionally grabbing").
- **Producer notes** reviewed by Claude; five changes sent as feedback (the Roundtable's words exactly, the model and
  run counts, the goals' names, "nearly one in five", the staff as the made-up company's).

## The gate (his, 2026-11-25, about 4:40 AM)

"What matters most to me is the emotional/visual presentation on this video not whether it's super nitty gritty
accurate." Agreed the same minute: a wrong number or a reversed direction, the made-up company's people presented as
real, a claim about real companies, real executives or AI in general, and a missing scope fail; paraphrase, rounding,
rating words, pacing and visuals are his call. It extends Phase 6.5's gate split of 2026-11-20.

## The check

Phase 6.5's check script (`scratch/p65-s9-check.sh`) unchanged (ffmpeg 6.1.1, a frame every two seconds, faster-whisper 1.2.1 `medium.en`): 33
frames, 33 distinct, 17 transcript segments, every one read by Claude against the site; he watched it through.

| Attempt | Length | Verdict |
|---|---|---|
| 1 | 1:07 | **kept**, two edits (below) |

**Passes the floor.** The number and direction are right (Haiku 5.5, about 19 percentage points fewer kept under
"Shareholders, long term" than "Everyone with a stake, long term" on the first decision); "a fictional company" is
said at 16 s and on screen before any talk of people losing work; the model is named. **His call, kept as made:** the
Roundtable's words paraphrased as "the interests of shareholders and everyone else perfectly align" (theirs: "in the
long term, the interests of a company's stakeholders are inseparable"); "-19.1% Retained" on screen, which is
percentage points; the bars' heights, which exaggerate the gap; the opening question about AI models and layoffs, a
hook and not a claim; "the two paths completely diverged".

## The two edits (ffmpeg 6.1.1)

1. **The label.** From 42.3 s to 58.05 s the teal bar covered the foot of "Stakeholders" (his catch). A 166 by 34
   pixel patch of the video's own frame at 42.3 s, before the bar appears, is laid over the label (x 440, y 712), so
   the bar's top sits just below the word. Nothing new is drawn.
2. **The end card**, six seconds after Gemini's logo, in the site's font (Source Sans 3, from the built site), his
   text: "Claude Haiku 5.5 · 60 runs under each goal · a made-up company / A second model, gpt-oss-120b, split the
   same way: about 45 points (58 and 60 runs). / This measures how AI models decide, not how real executives decide,
   and it predicts nothing about any company. / Video generated with Gemini Notebook. Full results:
   horizon-compact.vercel.app". It carries the scope sentence in substance (§7.1) and the AI-generated label. Its
   figures are the site's: `web/explorer-data/grid/gpt-oss-openrouter/s1.json`, C minus D −0.454, valid runs 58 and 60.

**He approved the cut** (2026-11-25, about 5:02 AM: "okay yeah it's good").

## Hashes

| File | sha256 |
|---|---|
| `attempt1.mp4` (Gemini's download, 1:06.7, 720x1280, 30 fps) | `feb190b157eadb92b43b36bb346fb728296ed745ea50ce781272b8c924714c7e` |
| `attempt1-final.mp4` (the Short, 1:12.7) | `b702dbf06642dde158258cb88747e186b22ba512f6bf3acf3cd3804f69ad53bf` |
| `endcard.png` | `13351a3ee024e101d5c938b4d354659b261bd0dde7ee2313ddbfda38ff5c5f63` |
| `patch.png` | `525e551b9a9ab9c343db9c08adb0bb969fd4f9b28053276b88b964fa04dfd940` |
