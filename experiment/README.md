# experiment/

The experiment as versioned, hashed data (`planning/05` §3.1, §4.2). Every file here is built into the container
image, so the image digest pins the code and the content together (Phase 1 decision 5), and every run records the
hash of every file it read.

- `models.toml`: how each model is reached, its request quota and its prices. Config, not content; never in code.
- `placeholder/`: **the walking skeleton's placeholder, off the experiment's subject entirely** (Phase 1 decision 2).
  Its rule is written at the top of each of its files. **The layout every experiment folder follows** (Phase 2.5):
  `dossier.toml`, `objectives.toml` (the objectives, the wording templates `w1` to `w3` and, for an experiment that
  has one, `sealed_template`) and one file per scenario in `scenarios/`, whose name is the scenario's id.
- `shapes/`: **garden copies of the four company scenarios' form** (Phase 3.5 decision 3), under the placeholder
  rule: `garden_sN` has `sN`'s rule, unit, caps as ratios to the total, extra rules and choice, and none of its
  content. They measure format failures on each official candidate before the tag; `hc scenarios check` fails if
  a shape drifts from its scenario's form.
- `company/`: **the fictional company's dossier** (Phase 2): `sources.toml` and `figures.toml` are the data, every
  number in the text is a row; the rendered `dossier.toml` is what the model reads, and `hc dossier check` fails the
  build if it is not a fresh render. It is built out of order, before Phase 1 closes; nothing in it calls a model.

Nothing official runs on anything in this folder until `prereg-v1` exists (`planning/05` §2).
