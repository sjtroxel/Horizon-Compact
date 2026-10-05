# Phase 1.5 — Publish Path (v0.1.5)

> **Scope doc.** Split out of Phase 1 on 2026-10-04 (his, Phase 1 decision 1), from the half of
> `docs/phases/phase-1-walking-skeleton.md` written as "the publish path." Sources: `planning/05` §1, §4.3 and §5
> (Phase 1's row), `planning/02` §2.8-2.11, `planning/06` §6.1 and §7, and `planning/07` §12. **APPROVED 2026-10-04
> (his)** with Phase 1. The decisions that shape it (2, 4 and 5) were made on the Phase 1 doc and are recorded there.
>
> Written before Phase 0.5 and Phase 1 are built. **Lines marked *(rests on 1)* depend on what Phase 1 builds;** if
> Phase 1 comes out different, they are the lines to amend.

## What this phase is for

The second half of the walking skeleton: Phase 1's placeholder sweep is scored by the real scorer and shown on one
page at `horizon-compact.vercel.app`, through the real CloudFront and Vercel path (`planning/05` §1). When this phase
is done, the skeleton walks end to end, and every later phase thickens it rather than adding to its structure.

**The test of a good Phase 1.5:** any number on the public page can be traced to its run IDs and image digest, the
page cannot be read as a finding, and `terraform destroy` on `main` followed by a re-apply brings the whole thing
back with the raw results untouched.

**The main model:** this phase shows whatever Phase 1's sweep ran on: Sonnet 4.6, fixed 2026-10-05 (Phase 1, "The
main model is a slot"). The model's name comes from the provenance, never from the page's code.

## Delivers

In build order.

1. **The scorer:** a pure function from raw results to static JSON, deterministic, using DuckDB over the run objects.
   In this phase it is descriptive only: counts by status, first-attempt beside final, and per-cell means and spread
   for every lever, **with per-run values in the JSON** so the page can draw spread (`planning/06` §7.3). Verdicts and
   intervals belong to Phase 3. The JSON schema carries a version (`planning/05` §4.3).
2. **Aggregation and publishing** (Phase 1 decision 5): he runs the aggregation on the laptop, and the static JSON is
   committed to the repo, where CI picks it up when it deploys the site. CI never reads raw results
   (`planning/02` §2.11). Development results reach the published JSON only as what they are: labeled test runs.
3. **The site, one page:** `web/`, React and TypeScript, static, on S3 and CloudFront (origin access control, no
   public bucket), behind the Vercel rewrite (`planning/02` §2.9). The page shows the placeholder sweep with spread
   drawn, run counts on every number, and labels on every series. **Plain words on the page say these are test runs
   on placeholder content, not results.** The page already has the fixed section for results against the thesis
   (`planning/06` §6.1: "present from the first build of the page"), with nothing in it yet. `planning/06` §7.2's
   rules apply already: no moral color, spread always drawn, nothing conveyed by color alone. The full visual design
   waits for Phase 6.
4. **CI, the site half of deploying:** build the site, sync it to its bucket, invalidate CloudFront. The deploy role
   gains only the site bucket and that one distribution *(rests on 1: the role's policy as Phase 1 leaves it)*.
5. **The teardown test:** `terraform destroy` on `main`, confirm that nothing billable is left from it, then re-apply,
   update the Vercel rewrite to the new CloudFront domain, redeploy, and confirm the page and its traceability are
   back. The raw results are untouched, because they live in `bootstrap` (Phase 1 decision 4).

## The rules this phase must not break

- **Nothing on the page can be read as a finding.** The content is off the experiment's subject (Phase 1 decision 2),
  and the page says it is a test.
- **The page's public words are his** (`planning/00` §10, `planning/06` §8). Claude outlines and critiques; he writes.
- **No account ID and no email address in a tracked file.** The CloudFront domain in the Vercel rewrite is not an
  account identifier; Musical Mycelium commits its own.
- **Nothing always-on.** The site is static files behind CloudFront, which does not bill by the hour.
- **The page carries per-run values, not only averages,** so the explorer can always draw spread (`planning/06`
  §7.3).

## Explicitly not in this phase

- **The explorer's views:** scenario picker, side-by-side comparison, memo reader, real cases, the methods page.
  Phase 6.
- **The visual design process** (previews, palette, layout). Phase 6, with the `dataviz` skill (`planning/06` §7.3).
  The `dataviz` skill is still loaded before the one chart here is written.
- **Verdicts and intervals on the page.** Phase 3 defines them; Phase 4 produces the first ones.
- **Any live model call from the site.** Never in v1 (`planning/02` §3).

## Definition of done

1. **The page at `horizon-compact.vercel.app` shows the placeholder sweep** with spread and run counts, labeled as a
   test in his words. Any number on it can be traced to its run IDs and image digest.
2. **The published JSON is committed and was produced by the scorer** from the raw results; re-running the
   aggregation on the same results gives byte-identical JSON.
3. **`terraform destroy` on `main` and a re-apply both succeed.** After the destroy, nothing billable from `main`
   remains. After the re-apply and the rewrite update, the page and its traceability are back, and the raw results are
   intact.
4. **The fixed section for results against the thesis is on the page**, with his title.
5. **`make check` and CI are green,** the root stays under its cap, and every commit passed the guard.
6. **The phase's spend is measured from the bill**, and with Phase 1's it is about $1 or less (`planning/05`).

## Prerequisites

- **Phase 1 complete:** a placeholder sweep's results in S3, the image, `main`, and the deploy role.
- **His:** claim `horizon-compact.vercel.app` (owed since `planning/09` §7 step 7). It is a prerequisite here.
- **His words for the page:** the line that says these are test runs, and the title of the section for results
  against the thesis (`planning/06` §6.1: "its title is his to write").
- **Local tools:** Node 22.20.0, checked 2026-10-03 (`ROADMAP.md` §3). Versions of Vite, React, DuckDB and the
  actions are checked live in the IMPLEMENTATION doc.

## Cost

**Cents.** No model call. CloudFront and S3 at this size are fractions of a cent; the teardown and re-apply cost
nothing beyond a few minutes of resources. `planning/05`'s "about $1" covers Phase 1 and this phase together.

## Known risks

- **The rewrite points at a domain that no longer exists** after a re-apply, and the public URL goes dark. Mitigation:
  updating the rewrite is a written step of the teardown test, and the test is not done until the public URL is
  checked.
- **A test page read as a result.** Mitigation: off-subject content, and his plain label in the page itself, not only
  in a footer.
- **The teardown test is skipped because it feels done.** It is in the definition of done because a phase that has
  never turned itself off has not proven it can.
- **A chart that hides spread** sets a habit the explorer inherits. Mitigation: per-run values in the JSON, and spread
  drawn from the first chart.

## Decisions for him

**None open.** The three decisions that shape this phase were made on the Phase 1 doc on 2026-10-04 (2: placeholder
off the subject; 4: raw results in `bootstrap`; 5: inputs in the image, JSON committed). Two items are his to write,
not to decide: the page's test-run line and the section's title.

## Left for the IMPLEMENTATION doc

The DuckDB query and the JSON schema. The page's layout, with the `dataviz` skill loaded before any chart code. The
site bucket, the distribution and its origin access control. The Vercel project's setup and the rewrite's location.
The deploy role's added grants, action by action. The teardown checklist, item by item. Versions of every package and
action, checked live. The order of the commits.
