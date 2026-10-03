"""The public/private boundary (``docs/planning/04`` §2.6).

Real-case company names live only in a private longlist outside this repository. This package keeps them
out of it:

- ``names``: parse the private term file and find terms in text. Pure functions; Phase 6's memo scan
  imports this rather than writing a second matcher (``docs/planning/09`` A7).
- ``guard``: the command line run by the pre-commit, commit-msg and pre-push hooks, the one-off history
  scan, and the checks ``make check`` runs.

**Standard library only**, enforced by ``tests/test_architecture.py``: the guard must run before any
third-party dependency is installed or trusted, and must not break when one changes.

Nothing here may name a real company, and no private path may appear in this repository. The term file
reaches the guard through local git config or an environment variable (Phase 0, decision 2).
"""
