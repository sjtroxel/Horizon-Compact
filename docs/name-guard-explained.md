# The name guard, explained

Written 2026-10-03, during Phase 0. What it protects, how it works, what it cannot do, and what to do when it
blocks a commit.

## The problem it solves

This repository is public from its first commit. The experiment's later phases use **real companies** as test
cases, anonymized. Which companies those are is private: a reader who could name them could check the model's
answers against the news, and the anonymization would mean nothing.

The candidates are kept in a private list outside this repository. The danger is ordinary: during a working
session, a company's name gets pasted into a document, a commit message, or a file name, and is committed and
pushed. **Once a name is in a public repository's history, it cannot be reliably taken back.** Rewriting
history does not reach copies that were already made. So the protection has to act before the push, every time,
without depending on anyone remembering.

## How it works

**A private term file** sits beside the private longlist, outside this repository. It lists every company name,
ticker, brand and plant location to block, plus a few allowed phrases (cloud product names that share a word with
a candidate). Its location reaches the guard through this clone's own git settings, which git never commits.

**The guard checks three moments:**

| When | What it reads |
|---|---|
| Each commit | Every file being added or changed: its name and its full staged content |
| Each commit message | The message itself |
| Each push | Every commit the remote does not have yet, every branch and tag name, and every tag's message |

The push check is the backstop. It catches a commit made with `--no-verify`, which skips the first two checks.
It also looks at every local branch and tag, not only the one being pushed, because the hook framework tells a
hook about only the first of several refs in one push.

**How a term matches.** As a whole word: "Name" matches `Name`, `Name's` and `name_file.md`, but not `Names` or
`Renamed`. Most terms match only with the capital letters they have, because several candidate names are also
ordinary English words; unusual names match in any capitalization. A two-word name still matches when a line
break falls between the words, since Markdown wraps long lines.

**It fails closed.** If the guard cannot find or read its term file, if the file is empty, or if the private
longlist has changed since the term file was last updated, **it refuses the commit** and says why. A check that
quietly passes when its list is missing looks like protection and is not.

**The longlist fingerprint.** The term file records a fingerprint (a SHA-256 hash) of the longlist's contents.
When a candidate is added to the longlist, the fingerprint no longer matches, and the guard blocks every commit
until the term file has been revisited and its fingerprint updated. That is how a new candidate cannot be added
to the longlist without also being blocked. Re-saving the longlist unchanged does not trip it.

## What it cannot do

- **Text typed into GitHub itself**: issues, pull requests, the repository description, release notes. Those
  never pass through git on this machine.
- **A spelling the term file does not contain.**
- **A description that identifies a company without naming it** ("the only maker of X in town Y"). That needs a
  person's judgment, and is checked when real cases are written up (Phases 5 and 6).
- **Binary files** such as images and PDFs. It reports them as not scanned.
- **A clone where `make setup` was never run.** Hooks are not copied by `git clone`. `make check` fails until
  setup has been run, so the gap shows up quickly.

## What CI does

CI runs on GitHub's servers, which never see the private term file, so **CI does not run the name scan**. It runs
two things that need no private file: a check that nothing under `methods-appendix/` is tracked, and the guard's
own tests, which use made-up company names only. The name scan itself happens on the laptop, before anything
reaches GitHub.

## When it blocks a commit

The message names the file, the line and the matched term. Then:

1. **If the name really is a company's**, reword it. Refer to the case by its type and a neutral label.
2. **If it is a false positive**, such as an ordinary word that happens to be a candidate's name, add an `allow:`
   line to the private term file with a comment saying why.
3. **Never remove a term to make a commit pass**, and never bypass the hooks.

## Commands

| Command | Does |
|---|---|
| `make setup` | Once per clone: stores the term file's location, installs the three hooks, checks them |
| `make doctor` | Confirms the hooks are installed and the term file loads with a matching fingerprint |
| `make guard-history` | Scans every commit, branch, tag and tag message ever made |
| `make fingerprint` | Prints the longlist's current fingerprint, for updating the term file |
| `make paths-check` | Fails if anything under `methods-appendix/` is tracked (this is what CI runs) |

The code is `src/horizon_compact/privacy/`, standard library only, so it runs before any other dependency is
installed and cannot be broken by a dependency update. Phase 6 reuses its matcher to scan model-written memos
about real cases before they are published.
