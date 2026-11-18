# Brief: rebuild ten prompts from a published methods page

You are helping test a published research write-up. The question is whether a careful stranger, with only what is
published, can rebuild the exact prompts an experiment sent to two AI models. You are that stranger.

## What you may use, and nothing else

1. **The site**, running locally at http://127.0.0.1:4173/ . Start with the methods page,
   http://127.0.0.1:4173/methods/ , and read any page of the site you like. Fetch it with curl or any tool you have.
2. **This folder:** `content/` (the experiment's content files, exactly as published), `samples.json` (each sample's
   recorded settings), and this brief.

**Do not** open, search or read any file outside this folder; do not look for the project's repository, its code or its
raw records, on this machine or on the internet; do not fetch any address but http://127.0.0.1:4173/ ; do not call any
AI model's API; do not use git. If the site links somewhere else (GitHub, for example), do not follow the link: note it
in NOTES.md as something you could not use. The test is only fair if you use only what is listed above. Nothing
enforces this; it is on your honor, and your notes should say plainly if you broke it, even by accident.

## What to produce

For each of the ten entries in `samples.json`, write `rebuilt/<sample>.json`, where `<sample>` is the entry's
`sample` field:

- for an entry whose `kind` is `decision`:
  `{"system": "<the system text>", "user": "<the user message>", "tool": {"name": "...", "description": "...",
  "input_schema": {...}}}`
- for an entry whose `kind` is `awareness`: `{"system": "<the system text>", "user": "<the user message>"}`

Each must be exactly what the model was sent: every character, every blank line, every line break, every space. The
tool's `input_schema` is a JSON object, compared as data (key order inside it does not matter); the texts are compared
byte for byte.

Then write `NOTES.md`: for each sample, what you were sure of, what you had to guess, and where on the site (or in
which content file) you found each rule you used. A guess the site does not settle is the most useful thing you can
report. Also list anything the site seemed to promise but you could not find.

You will not be told whether your rebuilds match until you are finished. Do not stop at the first doubt: make your
best rebuild of every sample, and record the doubt in NOTES.md.
