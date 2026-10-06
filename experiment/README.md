# experiment/

The experiment as versioned, hashed data (`planning/05` §3.1, §4.2). Every file here is built into the container
image, so the image digest pins the code and the content together (Phase 1 decision 5), and every run records the
hash of every file it read.

- `models.toml`: how each model is reached, its request quota and its prices. Config, not content; never in code.
- `placeholder/`: **the walking skeleton's placeholder, off the experiment's subject entirely** (Phase 1 decision 2).
  Its rule is written at the top of each of its files.
- `company/`: **the fictional company's dossier** (Phase 2): `sources.toml` and `figures.toml` are the data, every
  number in the text is a row; the rendered `dossier.toml` is what the model reads, and `hc dossier check` fails the
  build if it is not a fresh render. It is built out of order, before Phase 1 closes; nothing in it calls a model.

Nothing official runs on anything in this folder until `prereg-v1` exists (`planning/05` §2).
