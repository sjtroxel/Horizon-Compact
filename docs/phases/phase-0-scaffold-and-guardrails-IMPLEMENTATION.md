# Phase 0 — Scaffold and Guardrails (v0.0): IMPLEMENTATION

> **Plan, not an as-built record.** Written 2026-10-03, immediately before the build, from the approved scope doc
> `phase-0-scaffold-and-guardrails.md` and its six decisions. **APPROVED 2026-10-03 (his).** **PHASE 0 COMPLETE
> 2026-10-03:** every step done, all six DoD items pass (one with a caveat, §11a), CI green on the first push
> (run `37160410815`). This doc may turn out wrong; it may not be silently wrong. It is updated as the build
> diverges, and each step is marked `[done]` with its date when it lands.

## 1. What this phase delivers

The name guard, the CI path check, the toolchain, `make check`, CI, `CLAUDE.md` and the planning README, so that
every commit after the guard commit, including every later scope doc, goes through the guard. **$0, nothing in
AWS.** The definition of done is the scope doc's six items; §10 maps each to its proof.

## 2. Versions, checked live 2026-10-03

| Thing | Version | Checked against |
|---|---|---|
| Python | **3.13**, `requires-python = ">=3.13,<3.14"` (the upper bound is Musical Mycelium's lesson: without it uv took 3.14); 3.13.14 already installed by uv | `uv python list` |
| uv | 0.12.0 (local; CI pins the same) | `uv --version` |
| pre-commit | 4.6.2 | PyPI |
| ruff / ruff-pre-commit | 0.16.10 / `v0.16.10` | PyPI, GitHub releases |
| mypy | 2.4.0 | PyPI |
| pytest | 9.1.1 | PyPI |
| pre-commit-hooks | `v6.0.0` | GitHub releases |
| `actions/checkout` | `@v7` (a floating major tag exists; latest v7.0.1) | GitHub tags |
| `astral-sh/setup-uv` | **`@v10.2.0`, exact** (no floating `v10` tag exists, checked; Musical Mycelium's red build came from assuming one) | GitHub tags |

Exact Python package versions are fixed by `uv.lock`, committed; CI runs `uv sync --locked`.

## 3. The private term file (outside this repo)

**Location:** beside the longlist, outside this repo, in private storage. **Its path and file name are written
nowhere in this repo.** It reaches the guard
through `git config --local hc.nameGuardTerms <path>` (decision 2), overridable by the environment variable
`HC_NAME_GUARD_TERMS`. `make setup` asks for the path once and stores it.

**Format,** one directive per line, `#` for comments, blank lines ignored:

```
# Comments go on their own line. Why each allow exists goes in a comment above it.
longlist: /absolute/path/to/the/longlist.md
longlist-sha256: <64 hex characters>
# case-sensitive, whole word (the default)
term: Exact Name
# any capitalization
term-i: Distinctive Name
# blanked out before matching, case-sensitive
allow: Some Product Name
```

*(Corrected during step 2: the first draft showed comments at the end of a line. A `#` inside a term is part
of the term, so comments are on their own line only. Every malformed line is an error, never skipped.)*

The longlist path lives **inside** the private file, so this repo holds no private path at all.

**Drafting it (step 0):** Claude drafts it from the longlist by decision 4's groups: every company name
including rejected and excluded ones, tickers of three or more letters, shorter tickers only where they match
nothing in this repo (any match is brought to him), and plant and site locations. Flags `term-i` only on names
that cannot be ordinary words. Adds the allowed phrases the planning docs need, each with a reason comment. **He
reviews it line by line.** He commits it in job-search-headquarters; Claude does not.

## 4. The matching rule (decision 3, made precise)

For each text scanned:

1. **Blank every allowed phrase** (replace each character with a space, so line numbers and positions survive).
2. **Match every term as a whole word:** not preceded and not followed by a letter or digit. So `Name's`,
   `(NAME)` and `a_name_here.md` match; `Names`, `Namesake` and `renamed` do not. Unicode-aware. *(Corrected
   during step 2: the first draft also counted the underscore as part of a word, which would have let a
   snake_case file name through. Underscores and hyphens are separators.)*
3. **Spaces inside a multi-word term match any run of whitespace, including a line break,** because Markdown
   wraps long lines and a name split across two lines is still a name. *(Found while writing this doc; the scope
   doc did not say it.)*
4. `term` matches case-sensitively; `term-i` ignores case.

**Every match is reported**, not only the first, as `file:line` and the term. In CI output the term is replaced
by `[redacted]` (the scan does not run in CI, §6; this is a second guard).

## 5. The guard: where it lives and what it does

**Location:** `src/horizon_compact/privacy/`, **standard library only** (an architecture test enforces it):

- `names.py`: parsing the term file and matching text. **Pure functions, no git, no files besides the term
  file.** Phase 6's memo scan (`planning/09` A7) imports this instead of writing a second copy.
- `guard.py`: the command line, `python -m horizon_compact.privacy.guard <mode>`.

**Modes:**

| Mode | Run by | Scans |
|---|---|---|
| `pre-commit` | pre-commit hook | every staged path being added, copied, modified or renamed (`--diff-filter=ACMR`), and **the full staged content of each** (read from the index, not the working tree). Refuses any staged path containing `methods-appendix` in any capitalization. Deletions are not scanned: removing a name is the fix |
| `commit-msg` | commit-msg hook | the commit message file |
| `pre-push` | pre-push hook | every commit being pushed that the remote does not already have: each one's message, the paths it adds or changes, and **the full content of each such file at that commit**. Catches a commit made with `--no-verify`. *(Corrected during step 3 from "the lines it adds": added lines alone miss a two-word name split across a new line and an unchanged one)* |
| `history` | by hand, once at step 6, and whenever the term list grows | every commit reachable from any branch, tag or `HEAD`, the same way as `pre-push`, plus ref names and tag messages. Merges are scanned against their first parent |

*(Widened during step 4.)* `pre-push` scans **every commit on any local branch, tag or `HEAD` that the remote
lacks**, plus **all branch and tag names and annotated tag messages**, not only the ref being pushed. Reason,
read from the installed pre-commit 4.6.2 source (`commands/hook_impl.py`, `_pre_push_ns`): the framework hands
a hook only the **first** ref of a multi-ref push that has new commits, and sets no to-ref at all for a first
push that includes the root commit. Scanning wider covers both. The cost is refusing a push while an unpushed
local branch holds a name, which is the safe direction to be wrong in. Tag messages matter here specifically:
Phase 3 creates the annotated `prereg-v1` tag.
| `paths-check` | CI and `make check` | `git ls-files`: fails if any tracked path contains `methods-appendix`, any capitalization. Needs no private file |
| `doctor` | `make check` (skipped in CI, decision 5) | the three hook types are installed; the term-file setting exists; the term file passes every fail-closed check |
| `fingerprint` | by hand | prints the current longlist's SHA-256, for updating the term file |

**Fail closed (exit 2), with a message naming which:** no setting; the term file missing or unreadable; no
`term` lines; no `longlist` or `longlist-sha256` line; the longlist unreadable; **the longlist's hash differs
from the recorded one** (decision 1). A name found exits 1. Clean exits 0.

**When it blocks, the message says what to do:** reword; or, if it is a false positive, add an `allow` line with
a reason to the private file. **Never remove a term to make a commit pass.**

**Binary files are not scanned** (the content is not text). There are none in Phase 0; this is recorded in the
scope doc's "cannot catch" list when the as-built notes are written.

## 6. Hooks, `make`, and CI

**`.pre-commit-config.yaml`:** `default_install_hook_types: [pre-commit, commit-msg, pre-push]`, so one
`pre-commit install` installs all three. A `local` repo with three hooks (`language: system`, `always_run:
true`) running `uv run --no-sync python -m horizon_compact.privacy.guard <mode>`, one per stage. Then
pre-commit-hooks (large files, merge conflicts, toml, yaml, private keys, end of file, trailing whitespace) at
the pre-commit stage, as in Musical Mycelium. **No `no-commit-to-branch`**: he commits to `main`.

*(Two corrections during step 4, both read from the installed pre-commit 4.6.2 source.)* **The commit-msg hook
keeps `pass_filenames` on**: pre-commit delivers the message file as the hook's one "filename"
(`commands/run.py`), and `pass_filenames: false` would hand the guard nothing. The other two keep it off.
**ruff runs as a `local` hook through `uv run`**, not from ruff's own hook repository, so the hook, `make check`
and CI all use the single ruff version in `uv.lock`; a second pin is how a hook and CI come to disagree.

**`Makefile`:**
- `make setup`: `uv sync`, asks for the term-file path if unset and stores it with `git config --local`, runs
  `pre-commit install`, then `doctor`.
- `make check`: format check, lint, types, tests, `root-check`, `paths-check`, then `doctor`. **When `CI` is
  set, `doctor` is skipped and the output says `SKIPPED in CI: doctor` by name.** Everything else is identical,
  so a green local `make check` predicts a green GitHub check (his reason for decision 5).
- `make guard-history`: the history scan. `make fmt`, `make help`.

**`.github/workflows/ci.yml`:** one job, on push to `main`, pull requests and `workflow_dispatch` (the manual
trigger is Musical Mycelium's lesson from a webhook outage). `permissions: contents: read`. Checkout, setup-uv
with uv 0.12.0, `uv sync --locked`, `make check`. **The name scan never runs in CI**: CI never runs pre-commit,
and `doctor` is skipped by name.

**Root cap: 16 entries.** Phase 0 brings the root to 11 (`.claude/`, `.github/`, `.gitignore`,
`.pre-commit-config.yaml`, `CLAUDE.md`, `Makefile`, `docs/`, `pyproject.toml`, `src/`, `tests/`, `uv.lock`).
Planned later: `infra/`, `web/`, `experiment/`, `pipelines/`, `README.md`, which is 16. Raised only for
something that cannot live anywhere else.

**`.claude/settings.json`:** denies `git commit`, `git push`, `terraform apply`, `terraform destroy` and `aws`
commands that change anything, as Musical Mycelium's did. `.gitignore` gains `.claude/settings.local.json`.

## 7. The canary names (fictional)

Used only in tests, in temporary term files the tests create. **None goes in the real term file**, because the
tests that contain them are themselves committed through the guard.

| Canary | Kind | Exercises |
|---|---|---|
| `Quillmere Fastening` | `term` | multi-word, line-wrapped, case-sensitive |
| `Zarnothic` | `term-i` | any capitalization |
| `QXZW` | `term` | a ticker, inside parentheses |
| `Fenwick Hollow` | `term` | a place name, possessive |
| `Brask-Ollen & Vey` | `term` | hyphen, ampersand |
| `Quillmere Cloud Suite` | `allow` | an allowed phrase containing a term |

**The by-hand check (step 5)** stages a scratch file containing **`Plover Ridgeworks`**, a canary that appears
**nowhere** in the repo (checked), with `HC_NAME_GUARD_TERMS` pointing at a temporary term file holding only
that canary (and a matching dummy longlist), and confirms `git commit` is refused, the message names the file
and line, and nothing is committed. Then the file is unstaged and deleted. The real term file is not touched.

*(Corrected during step 4. The first draft used `Quillmere Fastening` here. The step 4 rehearsal showed why
that fails: the test files contain the test canaries on purpose, so a canary list holding them blocks C1. The
by-hand canary must be one the repo never contains.)*

## 8. Tests

`tests/test_names.py` (pure): whole word; case-sensitive miss on lowercase; `term-i` hit on any case;
possessive hit; plural and substring miss; line-wrapped multi-word hit; allowed phrase blanked, and a real term
next to an allowed phrase still caught; punctuation in terms; every match reported with the right line;
redaction under `CI`. Term-file parsing: each malformed line is an error, not a silent skip.

`tests/test_guard_git.py` (temporary git repos through `subprocess`, no network): staged content, staged path,
message and `methods-appendix` path each refused; a clean commit passes; a deletion passes; a rename into a
canary path refused; **a canary committed with `--no-verify` caught by `pre-push`**; `history` finds a canary in
an old commit; `paths-check` fails on a tracked `Methods-Appendix/x.md` and passes otherwise; `doctor` fails with
no hooks installed. **Each fail-closed condition** (no setting, missing file, no terms, no hash, wrong hash,
unreadable longlist) exits 2. The environment variable overrides the git setting.

`tests/test_architecture.py`: `horizon_compact.privacy` imports only the standard library.

## 9. The commits

He runs every `git commit` and `git push`; Claude provides the commands, one at a time.

| # | Contents | Before it |
|---|---|---|
| C1, the guard commit | `pyproject.toml`, `uv.lock`, `src/horizon_compact/__init__.py`, `src/horizon_compact/privacy/`, `tests/`, `.pre-commit-config.yaml`, `Makefile`, `.github/workflows/ci.yml` | steps 1-5: `make check` green, hooks installed, the by-hand canary check passed |
| (no commit) | the history scan over `f214280` and C1, result recorded | step 6 |
| C2, the docs commit | `docs/ROADMAP.md`, `docs/KNOWN-GAPS.md`, `docs/phases/`, the dated note in `docs/planning/05` | step 6 clean |
| C3 | `CLAUDE.md`, `docs/planning/README.md` (his line), `.claude/settings.json`, the `.gitignore` addition, `docs/name-guard-explained.md` | step 8 |
| push | C1-C3 together, through the pre-push hook | then CI is watched to green |

**Nothing is pushed until C3 exists** (fewer CI runs, one push through the pre-push scan). If he would rather push
C1 alone first to see CI green early, that works too; it is his call on the day.

## 10. Definition of done, and the proof of each

| Scope DoD | Proof |
|---|---|
| 1. Refuses canary in content, path, message, at push; passes clean and allowed; fails closed | `test_names.py`, `test_guard_git.py`, and the by-hand check (§7), output pasted into the as-built notes |
| 2. History scan clean, docs commit passes, no term removed | `make guard-history` output recorded; C2 committed through the hook; term file's history in job-search-headquarters |
| 3. CI green on first push; path check shown to fail | the CI run ID; the `paths-check` test plus CI's exact command run in a throwaway local repo, **never** a pushed `methods-appendix/` path |
| 4. `make check` green, root under cap, `make setup` installs all hook types | command output; `doctor` |
| 5. `CLAUDE.md` and the planning README exist, his line his | the files; he wrote the line |
| 6. Nothing in AWS touched | no AWS command run in this phase; `.claude/settings.json` denies them |

## 11. Order of work

0. **[done 2026-10-03]** **Draft the private term file** (§3), run the short-ticker check against this repo,
   compute the fingerprint. **He reviews it.** *Result:* 61 terms, 11 allowed phrases; he reviewed and approved
   it 2026-10-03 (he commits it in job-search-headquarters). Probed against every repo file: one term matched 9
   times, all inside AWS product names, cleared by allowed phrases; the one short ticker matched nothing, so it
   is in. Beyond plain names it holds brands, a plant name, a program name and spelling variants.
1. **[done 2026-10-03]** `pyproject.toml`, the package skeleton, `uv lock`. *Result:* CPython 3.13.14, 24
   packages locked; `mypy` runs in `strict` mode.
2. **[done 2026-10-03]** `names.py` and `test_names.py`. *Result:* 56 tests.
3. **[done 2026-10-03]** `guard.py` and `test_guard_git.py`; the architecture test. *Result:* 57 git-level
   tests (including real `git commit` and `git push` through installed hooks) and 3 architecture tests; **116
   in all, passing**; ruff format, ruff check and strict mypy clean. **Each test file was checked for teeth:**
   five deliberate breaks (read the working tree instead of the index; scan nothing on push; treat `_` as a
   word character; no redaction in CI; accept an empty term list) each failed at least one test, and the code
   was restored. The real term file, run through the new matcher over all 26 working-tree files: 0 matches.
4. **[done 2026-10-03]** `.pre-commit-config.yaml`, `Makefile`, `ci.yml`. `make check` green locally, run the
   way CI runs it too (`CI=true make check`). *Result:*
   - **`CI=true make check` green:** 123 tests (7 added for the wider push scan), root 9 of 16, paths-check clean,
     `doctor` skipped by name. **Plain `make check` fails**, as decision 5 requires, until the hooks are
     installed: "hooks not installed: pre-commit, commit-msg, pre-push. Run 'make setup'."
   - **A clean copy, committed fresh with global git config off, passes CI's exact steps** (`uv sync --locked`,
     `CI=true make check`); **with a tracked `methods-appendix/x.md` added, it fails at paths-check**, path
     redacted. That is scope DoD 3's throwaway-repo proof.
   - **A full rehearsal through the real pre-commit framework** in a throwaway repo, canary term file only: C1
     committed with the config staged and never committed before (all 11 hooks passed, about 3 seconds; this
     resolves §12's first question); a canary in staged content refused; in a commit message refused; a clean
     commit passed; a `--no-verify` canary commit **refused at push, remote received nothing**; after the
     file was deleted in a later commit, **still refused at push**.
   - `setup-uv` v10.2.0's `version` and `enable-cache` inputs checked against its `action.yml` at that tag;
     `pre-commit validate-config` passes.
5. **He runs `make setup`.** Claude runs the by-hand canary check (§7). Then **he commits C1.**
   *[setup and by-hand check done 2026-10-03]* He set the path with `git config --local` and ran `make setup`:
   all three hook types installed; `doctor` loaded the real term file (61 terms, 11 allowed phrases,
   fingerprint matches). **By-hand check, adjusted so Claude never runs `git commit`:** with only a scratch
   file staged, Claude ran the **installed** hook scripts directly (`.git/hooks/pre-commit`,
   `.git/hooks/commit-msg`), which cannot create a commit. With the `Plover Ridgeworks` canary list: the
   staged file was **refused** (`staged byhand-canary.md:1:26`) and a canary commit message was **refused**.
   With the real term file, the same file passed (the canary is not a real name). Then the file was unstaged
   and deleted; before and after, 0 staged and 1 commit; pre-commit's stash of the unstaged `05` change was
   restored intact.
   **C1 committed by him 2026-10-03 as `9c382b8`** ("phase 0: name guard, hooks, toolchain and CI", 12 files):
   every hook passed on its first real run, including the name guard on the staged content and on the message.
6. **[done 2026-10-03]** `make guard-history` over `f214280` and C1 with the real term list. **If it finds
   anything, stop** (scope DoD 2): no further commit or push until he decides. *Result:* **"history clean, 2
   commit(s) scanned"**, exit 0. This is the check that counts for `f214280`, which was pushed before the guard
   existed (`KNOWN-GAPS.md`, 2026-10-03).
7. **[done 2026-10-03]** **He commits C2.** *Result:* `3b769ad`, 5 files, every hook passed. *Found afterwards,
   before any push:* line 32 of this doc named the private term file's folder and file name, beside a sentence
   saying its path was written nowhere. Not a company name and not the full path, but against the rule.
   Reworded. **He folded the fix into C2 with `git commit --amend` before any push** (his decision), so C2 is
   now `f45770b` and no public commit carries the old line.
8. `CLAUDE.md`, `.claude/settings.json`, the `.gitignore` line, `docs/name-guard-explained.md` (the plain-English
   write-up, Claude's draft; it explains the mechanism and is not recruiter-facing). `docs/planning/README.md`
   with the read order; **he writes the disclosure line.** **He commits C3.**
   *[files written 2026-10-03; his line and C3 pending]* `CLAUDE.md` (rule zero on names; the order of
   operations; the one-way doors; how the work is done; the `00` §10 working rules; cost and safety);
   `.claude/settings.json` denies `git commit`, `git push`, `git tag`, `terraform apply`/`destroy` and `aws`;
   `.gitignore` ignores `.claude/settings.local.json` (checked with `git check-ignore`; `settings.json` stays
   tracked); `docs/name-guard-explained.md`; `docs/planning/README.md` with the read order and **a marked gap
   for his line**. Plain `make check`, `doctor` included, passes: 123 tests, root 11 of 16. All five files scanned
   with the real term file: 0 matches.
   **C3 committed by him 2026-10-03 as `4405412`.** His disclosure line is his own words; he chose to keep it
   as written after Claude's critique (one note, on "every line", is recorded in the session, not here).
9. **[done 2026-10-03]** **He pushes.** CI watched to green; the run ID recorded. *Result:* before the push,
   `CI=true make check`, `make guard-history` ("history clean, 4 commit(s) scanned") and the push scan run by
   hand all passed. **He pushed `f214280..4405412`; the push hook passed** (three pre-commit-hooks checks also
   ran at push because their own manifests declare that stage; harmless). **CI run `37160410815` on `4405412`:
   success, first push, 16 seconds**, with the same numbers as local: CPython 3.13.14, 123 passed, root 11 of
   16, paths-check clean (33 tracked files), `doctor` skipped by name.
10. **[done 2026-10-03]** As-built notes in this doc; `KNOWN-GAPS.md` and `ROADMAP.md` updated; Phase 0 closed.
    **Next: the scope docs for Phases 0.5 through 7, in order.**

## 11a. Definition-of-done audit (as built, 2026-10-03)

| Scope DoD | Verdict | Evidence |
|---|---|---|
| 1. Refuses a canary in content, path, message and at push; passes clean and allowed; fails closed | **PASS, one caveat** | 123 tests including real `git commit`/`git push` through installed hooks; the framework rehearsal (§11 step 4); the by-hand check on the installed hooks (step 5). **Caveat:** in this repo the by-hand check ran the installed hook scripts directly rather than through `git commit`, because Claude never runs `git commit`; the refusal *at push* was proven in tests and the rehearsal, not against the real remote, by design |
| 2. History scan clean; docs commit passes; no term removed | **PASS** | "history clean, 2 commit(s) scanned" after C1, "4 commit(s)" before the push; C2 and C3 passed the hook; the term file was not edited after his approval |
| 3. CI green on first push; path check shown to fail | **PASS** | run `37160410815`; the tracked `methods-appendix/x.md` throwaway repo failing at paths-check (step 4) |
| 4. `make check` green, root under cap, `make setup` installs every hook type | **PASS** | plain `make check` green with `doctor`; root 11 of 16; `make setup` installed pre-commit, commit-msg and pre-push |
| 5. `CLAUDE.md` and the planning README exist; the line is his | **PASS** | both in `4405412`; he wrote the line |
| 6. Nothing in AWS created, changed or called | **PASS** | no `aws` or `terraform` command run in this phase; `.claude/settings.json` now denies both |

**What Phase 0 leaves behind:** the private term file must be revisited whenever the longlist changes (the guard
will force it); a fresh clone needs `make setup`; binary files are not scanned; text typed into GitHub is not
scanned. All four are in `CLAUDE.md` and `docs/name-guard-explained.md`.

## 12. Genuinely uncertain

- ~~**Whether pre-commit accepts an untracked `.pre-commit-config.yaml`** at the moment of C1.~~ **Resolved
  2026-10-03, step 4 rehearsal:** with the config staged and never committed, C1 committed and every hook ran.
- ~~**`uv run` startup inside three hooks**~~ **Measured at step 4:** a whole C1-sized commit took about 3
  seconds with every hook, on a first run.
- **The term list's false-positive rate** is unknown until step 6 runs it over the 12 planning files. Any
  allowed phrase added there is recorded with its reason.
- **`pre-push` range on the first push of a branch the remote already has**: the guard computes "commits the
  remote lacks" itself (`git rev-list <ref> --not --remotes=<remote>`) rather than trusting the framework's
  from-ref; tested in `test_guard_git.py`.
