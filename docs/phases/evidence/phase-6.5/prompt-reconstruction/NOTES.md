# NOTES: rebuilding ten prompts from the published methods page

## Honor statement (what I used, and what I touched that you might not expect)

I used only: the local site at http://127.0.0.1:4173/, this folder (`content/`, `samples.json`, `BRIEF.md`), and
Python's standard library to assemble the text. I did not read any other path in the repository, did not call any
model API, did not use git, and did not follow any link off the site.

Things worth knowing about how I used the site:

- The site is a single-page app: `/methods/` returns an empty HTML shell. The methods text lives in the site's own
  assets, so I fetched `/assets/explorer-*.js`, the page bundles it lazy-loads (`Methods-*.js`, `ScenarioView-*.js`,
  and a few more), and `/assets/methods-B-1EDLJT.json`, which holds the methods page's words. The prompt-building
  rules are all in section M7 of that file ("How each prompt is built"). I also fetched `/data/index.json` and
  `/data/methods.json` (the recorded request settings per sweep).
- I fetched `/data/awareness/haiku-5-5.json` and read its first ~1,500 characters. It holds the model's replies, not
  the prompts. I did not use it for anything, but I did look at it.
- The site's code contains a link to the project's GitHub repository, and the methods page links many "sources"
  (`src/horizon_compact/sweep/prompt.py`, `docs/phases/evidence/phase-5.5/...`, and others) to it. I did not follow
  any of them. They are listed under "Promised but not usable" below.

## How I built them

One script (kept in my scratchpad, not in this folder) reads the TOML content files with Python's `tomllib` and applies
the M7 rules. Output is `rebuilt/<sample>.json`, nine decision files (system, user, tool) and one awareness file
(system, user).

Rules, with where each came from:

| Piece | Rule used | Source |
|---|---|---|
| System text | `role` + blank line + dossier `text` (stripped) + blank line + `currency_note` | Site, methods section M7, "The system text is three pieces"; fields from `content/company/scenarios/sN.toml` and `dossier.toml` |
| User message | `scenario` (stripped), goal sentence, menu, options (s3 and s4 only), `instruction` (stripped), each separated by a blank line | Site M7, "The user message is these pieces" |
| Goal sentence | wording template's `stated` with `{who}` and `{when}` replaced; for E the template's `none` | Site M1 and M7; templates and objective words from `objectives.toml`; wording and objective per sample from `samples.json` |
| Lever line | `- label [key]: up to cap`; people as `125 people`, dollars as `$309,800,000` unrounded; `detail` on the next line after two spaces | Site M7, "Each line" |
| s4 lever line | `use, up to ...` / `source, up to ...` | Site M7, "Each line" ("on the fourth scenario only") |
| Not-offered lever | `- label [key]: note` | Site M7, "Each line" |
| Option line | `- text [key]` | Site M7, "Each line" |
| Order | `menu_order` and `option_order` from `samples.json` | Site M7, "The order"; `samples.json` |
| Tool | name, description by scenario, schema as the page lists it | Site M7, "The tool" |
| Awareness | same prompt, instruction replaced by the quoted question, no tool | Site M7, last bullet of the user-message list, and "The awareness probe's question" |

An independent check on my reading of the page: M7 says the order comes from `random.Random` seeded with the
sample's `menu_order_seed`, shuffling the scenario's levers in file order and then its options. I ran that with the
seeds in `samples.json` and it reproduced the recorded `menu_order` and `option_order` exactly for all ten samples.
That confirms the shuffle rule and that not-offered levers are in the shuffled menu. It says nothing about line
formatting, which I could not check against anything.

## Sure of vs. guessed, per sample

All four scenarios and both models share one assembly, so the doubts below apply across samples. I mark which
sample each doubt touches. I was confident about: the system text for every sample (the rule is explicit and the
inputs are files I hold), the goal sentence in every sample, the lever order and option order, the lever label and
cap text, and the tool's name, description, property names, types and the alphabetical `required` lists inside
`amounts`.

### The doubts the site does not settle

1. **Separator between a heading and its first line (all ten samples).** M7 says the menu is "the menu_heading
   field, then one line for every lever ... the lines separated by single line breaks". It does not say what joins
   the heading to the first line. I used a single line break (so heading and lines form one block, with the blank
   lines only between the pieces). The same guess applies to `options_heading` on s3 and s4. If the real separator is
   a blank line, every sample is wrong at that point.
2. **Top-level `required` list of the tool (nine decision samples).** The page says every property inside `amounts`
   is required and that "every required list (the schema's own and amounts') holds the names in alphabetical order",
   so a top-level required list exists. It never says which top-level properties are in it. I assumed all of them:
   `["amounts", "memo"]` on s1 and s2, `["amounts", "memo", "plant_decision"]` on s3 and `["amounts", "memo",
   "program_decision"]` on s4.
3. **Choice property has no description (s3 and s4 samples).** The page describes `amounts` and `memo` with
   descriptions and describes the choice only as "a string whose enum is the option keys in alphabetical order". I
   gave it no description. If it has one, I cannot know its text.
4. **Not-offered lever on s4 (`grid-haiku-5-5-s4`, `grid-gpt-oss-openrouter-s4`).** The rule puts "use, " or
   "source, " before "up to" on s4. The one not-offered lever there, `pay_suppliers_more`, has kind `not_offered`
   and a note in place of "up to" and the cap. I wrote `- Paying suppliers more [pay_suppliers_more]: not part of
   this decision: ...` with no kind prefix. The page does not say whether a not-offered line carries one. The two s2
   not-offered levers (`payouts`, `keep_people`) are outside the s4-only rule, so I gave them no prefix either; that
   one I am fairly sure of.
5. **Thinking sample (`thinking-haiku-5-5-s1`).** `/data/methods.json` shows that sweep ran with different request
   settings (`max_tokens` 16000, effort high, adaptive thinking). The page says prompts are "built the same way for
   both models" but does not say outright that the thinking sub-study sends the same system, user and tool as the
   grid. I assumed it does, so this file differs from a grid s1 file only in the sample's objective, wording and
   order.
6. **Awareness sample (`awareness-haiku-5-5`).** I assumed "the same prompt" means the system text, the full s1
   scenario, goal sentence and menu all stay, and only the final instruction piece is swapped for the question. A
   reader could take "the same prompt" to mean something thinner. I followed the page's wording literally.
7. **Same text for gpt-oss-120b (four samples).** The page says the prompt is built the same way for both models, so I
   did. I cannot see whether the OpenRouter path wraps or alters the system text; the brief's format has no room for
   it, so I treated it as identical.

### Smaller points I am fairly but not completely sure of

- TOML multi-line strings (`'''...'''`) drop the first newline after the opening quotes; I used a standard parser,
  which does that. The dossier and scenarios are then stripped as the page says. There are no tabs, carriage
  returns or non-ASCII characters in any content file, so those cannot cause a byte mismatch.
- Whether the instruction and scenario "stripped" rules change anything: they do not, since neither field has
  surrounding white space after parsing.
- Whether `cap` text ever needs a singular ("1 person"). No cap in these samples is 1.
- Key order inside `input_schema` does not matter per the brief, so I did not try to match any particular order. The
  `required` lists are ordered because the page says so.

## Promised by the site but not found, or not usable

- **The cited scenarios file** (`docs/phases/evidence/phase-2.5/scenarios-cited.md`): M2 says it holds the full text of
  every scenario. It is in the repository; I did not and could not use it. The rendered scenario files in `content/`
  stood in for it.
- **`src/horizon_compact/sweep/prompt.py`**: cited as the source of the build rules in M7. Repository only; not used.
- **Per-call raw request files** (M7: "one file per API call, each with its request, its reply and its provenance",
  plus the manifest and `hc site raw-verify`). These would settle every doubt above, and they are exactly the thing I
  was not permitted to open. They sit in the repository; I did not follow the link.
- **The protocol** (`experiment/protocol/protocol-v1.md`): cited on most M7 paragraphs. Repository only; not used.
- **Unfinished parts of the methods page itself:** the page has "pending" placeholder blocks in M0, in M7 (between
  "Scoring it again" and "What can and cannot be re-run"), in M10 and M11, and section M11 ("video") has no content
  at all; M12 ("changes") says its list starts when the site goes live. The pending block inside M7, the section that
  describes prompt construction, may be where the answer to one of my doubts was meant to go. I cannot tell.
- **Nothing on the site says what joins a heading to its first line, what the top-level `required` list holds, or
  whether the choice property has a description.** Those are the three doubts most likely to cost bytes or schema
  equality.
