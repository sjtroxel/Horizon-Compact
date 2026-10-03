# Known gaps

Open items, newest first. **This file narrows the phase docs:** if it and an older phase doc disagree, this file
governs until the phase doc is amended. Closed items stay, marked closed with the date, so the record shows how
they closed.

**Never write a real company's name in this file, or in anything else under version control.** Refer to a real
case by its type and a neutral label. The names live only in the private longlist outside this repo.

> ## START HERE — where things stand, 2026-10-03
>
> **Two commits.** `f214280` (pushed, public: `.gitignore` and `docs/planning/`), made **before** the name guard
> existed and since confirmed clean by the guard's history scan (entry below); `9c382b8`, the guard commit
> (**local, not pushed**). This file, `ROADMAP.md` and the
> Phase 0 scope doc (`docs/phases/phase-0-scaffold-and-guardrails.md`) are untracked and **not approved**.
>
> **NEXT:** the Phase 0 scope doc is **APPROVED** (2026-10-03, all six decisions made; Phase 0 is the local half
> only, the AWS half is Phase 0.5). The IMPLEMENTATION doc is **written 2026-10-03, not approved**
> (`docs/phases/phase-0-scaffold-and-guardrails-IMPLEMENTATION.md`), **APPROVED**. **Steps 0-3 DONE 2026-10-03:**
> the private term file (he approved it; **he still commits it in job-search-headquarters**), the toolchain,
> the matcher and the guard. **Step 4 DONE 2026-10-03:** the pre-commit config, `Makefile` and CI; 123 tests;
> CI's exact steps pass in a clean copy; a full rehearsal through the real hook framework refused every canary.
> **Step 5 DONE:** hooks installed by `make setup`, the by-hand canary check passed, **C1 committed as
> `9c382b8`** (not pushed). **Step 6 DONE:** the guard's history scan over `f214280` and `9c382b8` is clean.
> **NEXT: step 7**, he commits C2 (the docs). Then step 8 (`CLAUDE.md` and the rest) and C3, then one push.
> Then step 1, the name guard, **as the next commit**. **After Phase 0 is built:** the scope docs for Phases 0.5
> through 7, written in order before any further implementation (his convention; Phase 0 is the one exception).
>
> **The one mistake that cannot be undone** is a real company's name in a public commit (`planning/04` §2.6).
> **Decided 2026-10-03 (his): no further commit or push until the guard is installed and has passed its canary
> test.** **Met 2026-10-03:** installed, canary refused at commit and message, before C1.

---

## FINDING — the first commit went public before the name guard, and it is clean, 2026-10-03

`f214280` ("first commit new project", 15:56 CDT) holds `.gitignore` and the 12 files of `docs/planning/` (13
files in all; `docs/planning/README.md` does not exist yet), and was pushed to `github.com/sjtroxel/Horizon-Compact` (public, confirmed through the GitHub API). `planning/09` §7
put the guard in the first commit, before anything was copied in. That order was not followed.

**The push was his, deliberate.** Another session scanned the same 12 planning files against the longlist
**before** he committed and found nothing (his account, 2026-10-03; that scan's method is not recorded here).

**Checked again the same afternoon, after the push:** every company name, ticker and plant location on the private
longlist was searched for, whole-word and ignoring case, across every file in `f214280` and in its message.
**No reference to any case or candidate.** One longlist term matches 9 times, each one inside a cloud product
name the project uses. No path under `methods-appendix/` is tracked.

**What this check is not:** it was a one-off search over a term list typed by hand from the longlist, run before
the guard or its term file existed. **It is not the guard.** Phase 0 DoD 2 has the guard scan the full history,
`f214280` included, once it is installed. That scan is the check that counts.

**CLOSED 2026-10-03, by the guard itself.** After C1 (`9c382b8`), `make guard-history` scanned both commits with
the real term file (61 terms, 11 allowed phrases, fingerprint matching): **"history clean, 2 commit(s)
scanned."** `f214280` is confirmed clean by the check that counts.

**What it changes:** the scope doc's "first commit" becomes "the guard commit," and the planning commit becomes
a scan of the history that already exists. No rewrite of history is needed or recommended. Rewriting a public
commit that holds nothing private would add risk and protect nothing.

---

## OPEN — the private longlist is prose, not a term list, 2026-10-03

Found while scoping Phase 0's name hook. The longlist was written for a person: candidates appear in table cells,
in comma-separated lists inside sentences, with tickers, plant locations and SIC codes beside them. Three
consequences:

1. **A hook that pulls names out of the longlist automatically will miss some.** Any parser of free-form prose
   has gaps, and a gap here is silent. Missing a name is the costly error.
2. **Using every word as written would over-block.** Measured on 2026-10-03: one longlist term already matches
   **9 places in the planning docs**, none of them a reference to a case. Several other longlist names are also
   ordinary English words or short tickers, and would match common words in this project's prose.
3. **Plant locations are as identifying as company names** for a single-plant closure, and the longlist holds
   them. Whether the hook blocks them is a policy decision, not a mechanical one.

**What follows:** the hook needs an explicit term list, kept private next to the longlist, with a stated
matching rule, and a way to notice when the longlist changes and the term list does not. Options and a
recommendation are in the Phase 0 scope doc. **His decision.**

---

## OPEN — Phase 0.5 checks, from `planning/09` §5, 2026-10-03

`planning/09` calls these the Phase 0 checks; they moved to Phase 0.5 with the AWS half (2026-10-03, his).
Each is Claude's, using live sources only. None blocks Phase 0.

| Check | Source |
|---|---|
| Ollama's install location and whether WSL can reach it (7 GB RAM visible in WSL) | `planning/00` §9.7, `planning/04` §6.3 |
| Whether AWS Budgets can filter on this project's per-model billing lines; whether added budgets cost money; whether application inference profiles could tag spend | `planning/04` §3.3 |
| Converse: one tool with `auto` choice on Sonnet 4.6; how thinking settings are passed and recorded | `planning/07` §14.1 |
| Nova Pro: default temperature, availability, knowledge cutoff | `planning/07` §14.2, `planning/01` §7.5 |
| Claude's default temperature value, for the methods page | `planning/07` §14.3 |
| How a refusal comes back through Converse on Sonnet 4.6 | `planning/07` §14.4 |
| Which Bedrock billing lines Musical Mycelium already spends on, before the development model is named (`planning/09` A1) | `planning/09` A1 |

---

## OPEN — owed by him, 2026-10-03

- ~~**Create the empty public GitHub repo `Horizon-Compact`**~~ **Done 2026-10-03**, with `f214280` pushed to it.
- **The one-line disclosure in `docs/planning/README.md`**, in his words: the planning docs were drafted with
  Claude from his interviews and decisions (`planning/06` §10.4, `planning/09` §6).
- **Claim `horizon-compact.vercel.app`** as a placeholder (`planning/09` §7 step 7). Unclaimed as of 2026-10-02;
  not re-checked since.

---

## WAITING — Sonnet 5.5 access, no action, 2026-10-03

Quota requests open (US: AWS Support case 179097554500679; Global: pending). If access arrives **before** the
`prereg-v1` tag, the main-model choice reopens as his decision. After the tag, Sonnet 5.5 is its own sweep
(`planning/05` §5.2).

---

## RECORDED — later-phase checks, so they are not lost, 2026-10-03

From `planning/09` §5. Not Phase 0's.

- A newer non-Anthropic model than Nova Pro on the account: before the Phase 3 model set is fixed.
- Census AIES and BLS tables; Damodaran's terms of use; whether the SEC Financial Statement Data Sets are
  current: Phase 2, before the dossier.
- Bootstrap, Newcombe intervals and the power rule implemented and tested on synthetic data: Phase 3.
- Measured tokens and cost replacing every estimate in `planning/03`: Phase 4.
- Each real-case candidate's first-disclosure date, public status and recognition: Phase 5.
- Bedrock fine-tuning and custom-model serving costs: before any fine-tuning phase, after v1.
