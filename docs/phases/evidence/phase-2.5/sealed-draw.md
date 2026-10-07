# The sealed draw

Phase 2.5 step 14 (DoD 2, IMPLEMENTATION doc section 13). **Run once, 2026-10-07, by Opus**, from the commit that
records the completed neutrality review. There is no other draw record, and there will be none.

- **The seed:** `67cfac640f1b93e17c4fd7c6c7677a963325176b`, "phase 2.5: steps 11-13, review, reader, changes" (pushed; CI run `37701059850` green, Deploy `37701060141`).
- **The computation:** `index = int(sha256(commit_hash + "|sealed-template"), 16) % 3`, mapped to w1, w2, w3.
- **sha256(`67cfac640f1b93e17c4fd7c6c7677a963325176b|sealed-template`)** = `6e6e0c09dd5b58ab591728f47fcb1ec19fb428396ef6b3913c99d35e484fda20`
- **That number mod 3** = 1
- **The sealed template: `w2`.** It is written to `experiment/company/objectives.toml`, and the draw record in
  `experiment/company/CHANGELOG.toml` holds the same commit, template and content hash change
  (`e7bd77d74cb9...` to `5bd849beef0d...`), chained after entry 13. `hc scenarios check` recomputes the template
  from the commit and fails if the record, the objectives file and the computation disagree.

**What it means:** `w2` is used only by the official sweep. No development run uses it, and the harness
refuses any plan that is not official and includes it. The other two templates are the development templates for
the format runs (step 15).

**What it cannot prove:** that nobody amended the review commit to steer its hash. History shows the commit, which
was pushed before the draw was computed; the honor statement at close-out covers the rest.

To recompute: `python3 -c "import hashlib; print(int(hashlib.sha256(b'67cfac640f1b93e17c4fd7c6c7677a963325176b|sealed-template').hexdigest(), 16) % 3)"`
