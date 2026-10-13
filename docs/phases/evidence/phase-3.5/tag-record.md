# Tag record: `prereg-v1`

Phase 3.5 IMPLEMENTATION doc §12 and §17, DoD 3-6; protocol §15. Tag day ran 2026-10-13, about 12:50 to 1:40 AM
CDT (05:50 to 06:40 UTC). Every step that changes the repository or GitHub was his; Claude read each one back. **No
model was called on tag day.** Every value below was read back from git, the GitHub API or the Software Heritage API
at the time, not copied from a terminal.

## 1. Before `P`

- **His read of the corrected protocol §1.1** ("The order it protects"), with the same correction in §1.6 ("How it
  guards against fooling itself") and §2.7 ("What no one has seen"): "all this reads right to me", 2026-10-13, 12:54
  AM. These are the only three passages marked "Corrected 2026-10-12" (a grep for the marker). The 2026-10-12 handoff
  notes said "§1.6 and §4"; §4 was a slip in the note, not an unread change.
- `0744c26` (`phase 3.5: independent review and resolutions`) pushed before tag day, CI green (run `38313978539`):
  the review files are in commits before `P` (DoD 2).
- **The dry run of the lock**, `hc protocol lock --model haiku-5-5 --model gpt-oss-openrouter` without `--write`:
  nothing written; checked by Claude against §25's recorded proof (both models' tables, the three instrument files,
  `company` with sealed template `w2`) and its `document_sha256` against `sha256sum` of the committed
  `protocol-v1.md`. Then `--write` (his): `wrote experiment/protocol/prereg.lock`, identical in every hash to the dry
  run. A second run of the command refused, as built: "a lock is never overwritten".

## 2. The protocol commit `P`

| | |
|---|---|
| `P` | `649e8b9b8f1dde0e3698be0d279b62fef07ad70b`, `phase 3.5: prereg-v1 lock`, 2026-10-13 01:14:54 -0500 |
| Files | `experiment/protocol/prereg.lock` (new, 68 lines) and three test files (below) |
| `document_sha256` | `6bc5a30c57ae1299f25f24996062d5a3767c5a494e0f6377d14d6a85fa5008c3` (`protocol-v1.md`) |
| `content_hash` | `a31d1f1184a502ce7e9cede35755cbb2c5083b658aed0c7f27e75c12d84df3c3` (`company`, sealed `w2`) |
| instrument `sha256` | `ab19145c204badbbc342e86781211d12388bd0a133020533cebf511594542568` |
| analysis `sha256` | `0cabbfd96fc42da1ecc1f0e7966e540a3ba9735487046c4e84fe7e45b0f50e0a` |
| Models | `haiku-5-5` (`main`, `claude-haiku-5-5`, `anthropic`, thinking off); `gpt-oss-openrouter` (`second_family`, `openai/gpt-oss-120b`, `deepinfra/bf16`, reasoning `medium`) |
| `make check` | green, 2040 tests, `protocol check: ok` |
| CI on `P` | run **`38355727520`**, success, 06:15:49Z to 06:17:37Z; https://github.com/sjtroxel/Horizon-Compact/actions/runs/38355727520 (Deploy `38355727328`, success) |

**Four tests changed in `P`, which the plan did not foresee.** They asserted the state before the lock ("no committed
protocol"), so writing the lock failed them: `make check` went red with 4 failures and 2035 passes. The gate itself
was right in every case; it now refused for the post-lock reasons. Claude rewrote them (tests are not in the lock):

- `test_protocol_gate.py`: the real repository refuses an official sweep on `sonnet-4-6`, a model `prereg-v1` does not
  name.
- `test_sweep_cli.py` (two): the official run and launch now expect "experiment is 'placeholder'; prereg-v1 locks
  'company'" (and, for the run, the laptop refusal).
- `test_sweep_refusals.py`: split in two. A forced analysis difference refuses `hc analyze`; the real gate on the
  real lock accepts it. 2039 tests became 2040.

## 3. The ruleset

Created by him at 01:14 CDT, before the tag. Read back with `gh api repos/{owner}/{repo}/rulesets/24974909`:

| | |
|---|---|
| id, name | `24974909`, `prereg tags` |
| target, enforcement | `tag`, `active` |
| conditions | include `refs/tags/prereg-*`, exclude none |
| rules | `deletion`, `non_fast_forward`, `update` |
| bypass | `bypass_actors: []`, `current_user_can_bypass: "never"` |

The page offered eight rules. Checked: restrict updates, restrict deletions, block force pushes. Left unchecked:
restrict creations (with no bypass list it would have refused the tag itself), require linear history, require
deployments to succeed, require signed commits (his commits are not signed), require status checks to pass (CI on
`P` does that job). As protocol §15.1 says, a ruleset is not absolute: a repository admin can edit the ruleset.

## 4. The tag

| | |
|---|---|
| Tag | `prereg-v1`, annotated, tag object **`c949580e4e9a3a26bb7379ab029dcab697661175`** |
| Points to | `649e8b9b8f1dde0e3698be0d279b62fef07ad70b` (`P`) |
| Message | `prereg-v1: protocol v1` |
| Tagger | sjtroxel, 2026-10-13 01:19:15 -0500 |
| On GitHub | `git ls-remote`: `refs/tags/prereg-v1` `c949580`, peeled `649e8b9` |

**The name guard's pre-push hook printed nothing on the tag push** (a push of a tag whose commit the remote already
had; pre-commit appears to skip its pre-push hooks when no new commits go up, not verified). The guard was run by
hand straight after: `python -m horizon_compact.privacy.guard history` ("history clean, 67 commit(s) scanned"), which
scans branch and tag names and annotated tag messages as the pre-push mode does. KNOWN-GAPS OPEN entry, 2026-10-13.

## 5. The archive (Software Heritage)

One `curl` POST (his) to `https://archive.softwareheritage.org/api/1/origin/save/git/url/https://github.com/sjtroxel/Horizon-Compact/`
at 06:24:50Z; no earlier save request existed for the origin (a GET just before it returned "No save requests found").

| | |
|---|---|
| Save request | `2554911`, `accepted`, task `succeeded`, visit `full` |
| `visit_date` | **`2026-10-13T06:24:52.724000+00:00`** |
| Snapshot | **`swh:1:snp:df7dda44d8cf804cf004e73031249c8e5fe45e00`** |
| In the snapshot | `refs/tags/prereg-v1` -> release `c949580e4e9a3a26bb7379ab029dcab697661175` -> revision `649e8b9b8f1dde0e3698be0d279b62fef07ad70b`, message `prereg-v1: protocol v1`; `refs/heads/main` -> `649e8b9` |
| Status URL | https://archive.softwareheritage.org/api/1/origin/save/2554911/ |

The visit took seconds, not the "few hours" the plan expected.

## 6. The release

https://github.com/sjtroxel/Horizon-Compact/releases/tag/prereg-v1. Title `prereg-v1`, body empty (his choice, as
recommended: no prose, nothing that could name a company), not a draft, not a pre-release, published
2026-10-13T06:29:56Z.

## 7. The gate's dry runs against the tag (DoD 4)

From a detached worktree of `prereg-v1` (HEAD `649e8b9`) with its own environment (`uv sync --frozen`), so the
package that ran, and so the root the gate hashed, was the tag's own:
`.../prereg-v1/src/horizon_compact/__init__.py`. Run by him (`bash scratch/tag-day-dry-runs.sh`; `hc sweep run` is
denied to Claude); each change was undone before the next, and the script stops if the worktree is not clean.
Command for each: `hc sweep run --experiment company --repeats 1 --seed 1 --label grid --official --dry-run --model
<model>`. Every run also printed `note: not in the container (dry run)`; runs 3-6 printed the line-ending note,
which applies only when no frozen file was edited.

| # | Change | Result, verbatim |
|---|---|---|
| 1 | none (`haiku-5-5`) | `official sweep: every check passes (dry run; nothing written, nothing called)`, exit 0 |
| 2 | none (`gpt-oss-openrouter`) | `official sweep: every check passes (dry run; nothing written, nothing called)`, exit 0 |
| 3 | one byte added to `company/scenarios/s1.toml` | `official sweep refused: content differs from prereg-v1: company/scenarios/s1.toml`, exit 2 |
| 4 | one byte added to `sweep/decision.py` | `official sweep refused: instrument differs from prereg-v1: src/horizon_compact/sweep/decision.py`, exit 2 |
| 5 | one byte added to `analysis/verdict.py` | `official sweep refused: analysis differs from prereg-v1: src/horizon_compact/analysis/verdict.py`, exit 2 |
| 6 | one byte added to `protocol-v1.md` | `official sweep refused: document differs from prereg-v1: experiment/protocol/protocol-v1.md`, exit 2 |
| 7 | `haiku-5-5`'s `model_id` changed in `models.toml` | `official sweep refused: model haiku-5-5 differs from prereg-v1: model_id is 'claude-haiku-5-5x', locked 'claude-haiku-5-5'`, exit 2 |

§7.2 named Nova Pro's profile for the model case; Nova Pro left v1 on 2026-10-11 (§23), so the main model's id was
changed instead. The case mode's both ways are tests in CI (`tests/test_protocol_cases.py`), not dry runs.

## 8. Nothing official exists (DoD 5)

Run by him (`bash scratch/tag-day-s3-listing.sh`; `aws` is denied to Claude), 2026-10-13T06:35:12Z, profile
`horizon-compact`:

```
aws s3 ls s3://horizon-compact-results-<account-id>/
                           PRE development/
aws s3 ls s3://horizon-compact-results-<account-id>/official/ --recursive
(no lines, exit 1)
```

No `official/` and no `pilot/` prefix. Every model call before the tag is in `calls-inventory.md`, current through
step 11's review call; no call was made after it.
