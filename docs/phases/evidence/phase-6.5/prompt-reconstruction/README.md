# The prompt-reconstruction check (Phase 6.5 step 7; IMPLEMENTATION doc section 5.3, DoD row 3)

**Result, 2026-11-18: 10 of 10 match.** A fresh Claude Code session, started by him at about 5:00 PM CST in an empty
folder outside the repository (`~/hc-reconstruct`), set to a Claude Sonnet model with `/model sonnet`, was given only
the site's local preview (`http://127.0.0.1:4173/`), the six content files at `prereg-v1` and the ten samples' recorded
settings (`samples.json`), with the brief here (`BRIEF.md`). Not the code and not the raw records. It rebuilt the
system text, the user message and, for a decision, the tool of each sample (`rebuilt/`), and `reconstruct.py compare`
found every one equal to the record's `prompt_sha256`, the hash of what the harness sent (`comparison.md`).

- **The samples, by rule:** the first run by run id of each scenario in Haiku 5.5's grid and in gpt-oss-120b's grid,
  the first of the thinking sub-study, the first call of Haiku 5.5's awareness probe.
- **Its isolation was the folder and the brief, not a guarantee.** Its honor statement (`NOTES.md`): it used only the
  site and the folder, and followed no link off the site; it also fetched one site data file (the awareness replies)
  and did not use it.
- **What it had to guess** (`NOTES.md`, "The doubts the site does not settle"): how a heading joins its first line,
  which of the tool's properties are required, whether the choice property has a description, whether a not-offered
  line on the fourth scenario carries a kind, whether the thinking sub-study's prompt is the grid's, what the awareness
  probe keeps, and whether the second model is sent the same text. Each guess was right; after the check the methods
  page states each one (M7, "How each prompt is built"). The rebuilds were made before that wording existed.
- **Before the session,** Claude found by reading the page that it did not yet say how a prompt is built, and wrote
  M7's section; a script following only those written rules rebuilt all ten (10 of 10). The session tested whether a
  stranger can follow them.
- **To run the comparison again:** `python3 docs/phases/evidence/phase-6.5/prompt-reconstruction/reconstruct.py
  compare <folder>` on a folder holding `rebuilt/` (this one: `.../prompt-reconstruction`), from a clone with
  `experiment/raw/`.
