Phase 6.5 step 9, attempt 1 check (2026-11-20, about 9:20 AM)

Video: Horizon_Compact_AI_Study.mp4, Explainer, Classic style, 417.98 s, 1280x720 h264 24 fps + aac, 19,501,813 bytes.
Notebook: 14 PDFs from scratch/p65-s9-pack (manifest.json there), notebook memory off, instructions blank.
Steering: first prompt (in the session); producer notes reviewed, feedback (6 points) submitted with Enter, which rendered.
Frames: 209 at one per 2 s; 24 distinct (consecutive frames under 150 pixels changed by more than 24 grey levels grouped).
Transcript: faster-whisper 1.2.1, medium.en, CPU int8, 88 segments (transcript.txt).

Verdict: FAILS the gate. Fix by steering and regenerating (doc §6 item 4).

Failures
- Frame f114-f127 (about 3:48-4:14) and narration 241-254 s: "Haiku 5.5 kept 39.8 points fewer people under the
  longer horizon", shown as against the starting expectation. Reversed: s1 A vs C is -39.8, first minus second, so the
  short-term goal (A) kept fewer; expected direction; not in the story's against-expectation list.
- Frame f178-f185 (about 5:56): "Oct 16: Search for real exploratory cases conducted." Oct 16 was the pre-registered
  search, which found none.
- Frame f186-f196 (about 6:10): "Every single response the models gave is published in full." Drops "on the made-up
  company"; real-case responses are not published (rule zero). Narration had the scope right.
- Frame f207 (end): "What do the raw numbers reveal about AI decision-making?" Generalizes past two models.
- Narration 165-174 s: gpt-oss "also based on 60 and 60 runs". Wrong: grid file gpt-oss-openrouter/s1.json, the C vs D
  comparison, reads 58 and 60. (Corrected 11:20 AM: the first note read the A vs C row by mistake.)
- Narration 389-392 s: "That really proves the integrity of the data." Overclaim.
- Narration 373-384 s: "over 5,000 published raw text objects". Not found in the site text.
- Frames f088-f097: 19.1 / 45.4 / 86.7 shown without the compared goal, run counts or interval (planning/06 §4 habits).
- Rating words: "really rigorous", "Rigorous Methodology", "Strict Statistical Limits", "massive", "incredibly
  strict", "absolute verifiability". Energy words ("fascinating", "get this") are his call on tone (kept, 9:23 AM).
- Minor: "pure comparisons"; "manually selected"; "if the interval crosses zero ... inconclusive or no split" looser
  than the site's rule.

Passed: title card; agenda; scope quote (verbatim); goals table; company ($1.5B, six plants, four decisions); 99.7%;
real-case slides ("no good match for both models", "not judgments of any company, and do not prove the method works");
Oct 13; the three-step check slide. Gemini Notebook mark in every frame's corner.
