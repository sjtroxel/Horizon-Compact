# Phase 1.5 — Publish Path: IMPLEMENTATION (v0.1.5)

> **IMPLEMENTATION doc. APPROVED 2026-11-04, about 9:05 AM (his): all ten decisions in §11 as recommended, (a).**
> Drafted the same morning (Opus). Written the day Phase 1 closed
> (`01d9758`), immediately before this phase is built, and a month after its scope doc. Sources: the scope doc
> (`docs/phases/phase-1.5-publish-path.md`), the Phase 6 and 6.5 scope docs (what they expect of this phase),
> `planning/02` §1 and §2.8-2.11, `planning/05` §1, §4.3 and §5, `planning/06` §4 and §6-9, `planning/07` §12, the
> Phase 1 IMPLEMENTATION doc (§7-12, §21-22), the Phase 3 and Phase 4 docs where they name this phase, `KNOWN-GAPS.md`
> (START HERE, the CARRIED list for Phase 1.5, the OPEN entry of 2026-10-15), the code at `01d9758`
> (`analysis/records.py`, `analysis/results.py`, `analysis/descriptive.py`, `protocol/sets.py`, `cli.py`,
> `infra/terraform/*`, `infra/iam/deploy.json`, `.github/workflows/*`, `infra/docker/*`), Musical Mycelium's site
> (`infra/terraform/main/frontend.tf`, its deploy workflow and its deploy role), and live checks the same morning
> (§2). The `dataviz` skill was loaded before §7's chart was specified.
>
> **What this doc is.** The scope doc was written on 2026-10-04, before anything it rests on was built. Five
> phases have closed since, out of order, and several of its lines no longer hold. **§0 is the scope review he asked
> for**; the rest is the build plan. Three findings reach outside this phase and need his attention whatever he
> decides about the rest (§3, findings 1-3).
>
> **Rule zero governs every line.** The page shows only the placeholder, which is off the subject by construction.
> No real company appears in this doc, in any file this phase commits, or in anything typed into GitHub or Vercel.

## 0. The scope review: what changed since 2026-10-04 (the scope doc's dated note of 2026-11-04 points here)

Read the scope doc with these changes. Each is measured or cited; none lowers a rule.

1. **The main model** is Haiku 5.5 through Anthropic's API (the fallback set, Phase 3.5 §23, 2026-10-11), not
   Sonnet 4.6. The rule is unchanged: the page takes the model's name from the records, never from its own code.
2. **Delivers 1, the scorer, is built, and it cannot read the placeholder.** Phase 3 built the analysis engine;
   the Phase 4 code half put its JSON writer in the frozen set (`analysis/results.py`, `RESULTS_VERSION` 2), and the
   official and case results files it wrote are committed under `experiment/results/`. **Measured today on local
   copies of the placeholder sweeps:** `build_results` refuses them (`experiment 'placeholder' has no sealed
   template`), and the descriptive layer alone refuses them too (`no outcomes are defined for scenario 'garden'`).
   The engine is frozen at `prereg-v1`, so it is not changed to accept them. **This phase therefore builds a small
   site-data builder** in run code (§6), which reuses the frozen record reader (`analysis/records.read_runs`) as
   tagged and computes only counts, per-run values, means and ranges for the placeholder. It is not "the scorer", and
   no official number ever passes through it. DoD 2 reads "produced by the site-data builder".
3. **DuckDB is dropped.** It was never a dependency; the engine is Python over the run objects, and the placeholder
   is 15 runs. `planning/02` §2.8 gets a dated patch. The static-data contract of `planning/05` §4.3 holds: a pure,
   deterministic function from raw results to versioned JSON, and the site reads only the JSON.
4. **"Development results reach the published JSON only as labeled test runs"** becomes a rule in code. The builder
   accepts `development/placeholder/` and refuses every other prefix and experiment. The site reads only its own data
   file, and a test fails the build if `web/` imports anything outside `web/`. That is how Phase 6 decision 2
   (results reach the public URL only at go-live, complete) is held while the official results sit in the same
   repository.
5. **Delivers 3, the site:** still React and TypeScript, static, on S3 and CloudFront behind the Vercel rewrite.
   Added by this doc: a content security policy that forbids every third-party request, which makes Phase 6 decision
   5 (no visitor tracking) a property of the site and not only a promise; self-hosted fonts, which follow from it;
   and `noindex` until go-live (decision 3).
6. **Delivers 4, CI:** the deploy role's new grants are fenced by tag to this project's own distribution, because
   Musical Mycelium's distribution is in the same account (§3 finding 4, §9). Two CloudFront objects that cannot be
   fenced by tag (the origin access control and the response headers policy) live in `bootstrap` (decision 5).
7. **Delivers 5, the teardown:** run by a dispatch-only workflow on the deploy role, which already holds every delete
   `main` needs; his dev key holds none of them. Consequences the scope doc did not list: the sweep log group is
   deleted with `main` (decision 9), the re-apply builds a new image, and the distribution gets a new domain.
8. **Prerequisites:** Phase 1 is complete (DoD 7 waived, 2026-11-04). `horizon-compact.vercel.app` was claimed on
   2026-10-05 as a CLI-deployed placeholder project, not linked to GitHub (decision 4). Node 22.20.0 is still the
   local version and is supported to 2027-04-30 (§2).
9. **DoD 6** (spend with Phase 1's about $1 or less) starts from Phase 1's about $0.07 (Phase 1 doc §22).
10. **Two obligations from other phases land here** (§3 findings 2 and 3): Phase 4's manifest of raw objects, and
    the ECR images that pin the records.

`planning/06` §7.3 still governs the look: "nothing beyond the skeleton's single page" until Phase 6, whose previews
choose the chart form, palette and layout from real data. His ask on 2026-11-04 (the public face polished, with no
sign of generated filler) is met inside that rule: one page, built with care, with a checkable standard (§8).

## 1. Where things stand on 2026-11-04

- **Phases 0 to 5.5 are closed**, 1 and 2 to 5.5 out of order; Phase 1 closed this morning (`01d9758`, pushed).
  Phase 1.5 is Phase 6's prerequisite and is the only open phase before it.
- **`main`** holds the network, the ECS cluster and task definition, the two task roles and the log group.
  **`bootstrap`** holds the state bucket, the deploy role and its policy, the boundary, the budgets, the results
  bucket (`prevent_destroy`, deny-overwrite and deny-delete policy), ECR and the Bedrock profiles. The deploy
  workflow builds an image and applies `main` on pushes to code, `experiment/`, `infra/` and the lock files.
- **The placeholder sweeps in S3** (`development/placeholder/`): Phase 1's `skeleton-haiku-5-5-f1467906` (15 runs,
  Haiku 5.5, 2026-10-12) and `stoptest-haiku-5-5-c61e6830` (50 runs); Phase 4's final-image checks
  `final-haiku-5-5-dde5ae24`, `final-gpt-oss-openrouter-82194bbe` (15 runs each) and `thinking-haiku-5-5-fd5e6f49`;
  the earlier `skeleton-gpt-oss-openrouter-78a37f95`. Local copies of three are in `scratch/runs/` (gitignored).
- **`horizon-compact.vercel.app`** answers 200 with a one-line `noindex` page (checked today).
- **Spend:** cumulative at most about $46 (`evidence/phase-5.5/cost.md`). This phase makes no model call.

## 2. Versions and facts, checked live 2026-11-04

| Item | Today | Choice and why |
|---|---|---|
| Node | local 22.20.0; LTS lines 22 (maintenance, ends 2027-04-30), 24 (maintenance, ends 2028-04-30), 26 (LTS since 2026-10-28) | **22**, his installed version and Musical Mycelium's; supported past v1. CI pins `22` |
| Vite | 8.3.5 (2026-10-21) | 8.x; needs Node 20.19 or 22.12+ |
| React, React DOM | 19.3.1 (2026-10-14) | 19.3.x |
| TypeScript | 7.0.2 (2026-07-08) | 7.0.x, as Musical Mycelium |
| `@vitejs/plugin-react` | 6.2.1 (2026-11-02, two days old) | the newest 6.x at least 14 days old at install |
| Vitest | 5.1.0 (2026-11-02, a new major); 4.1.12 | **4.1.x**: 5.x is days old |
| jsdom; Testing Library React; Prettier | 30.1.3; 16.3.3; 3.9.10 | as listed, subject to the 14-day rule |
| `axe-core` | 4.14.0 (2026-10-05) | accessibility test in Vitest, no network |
| `actions/setup-node`; `actions/checkout`; `configure-aws-credentials`; `setup-terraform`; `setup-uv` | v7.1.0; v7.0.1; v6.3.0; v4.0.1; v10.3.3 | the repo's current pins stay; `setup-node@v7` is added |
| Terraform AWS provider | 6.71.0 (2026-10-28); locked 6.67.0, `~> 6.67` | stays locked; a bump is not this phase's |
| Vercel CLI | 65.11.0; not installed locally | run with `npx vercel@<exact version>` at the time (decision 4) |
| CloudFront IAM | read today from AWS's machine-readable service reference | **`distribution` supports `aws:ResourceTag`**; `CreateDistribution` and `TagResource` support `aws:RequestTag`; **origin access controls and response headers policies support no tag condition** (§9) |

**The version rule for `web/`:** exact versions in `package.json`, a committed `package-lock.json`, `npm ci` everywhere,
and no version younger than 14 days on the day it is installed. The build re-checks this table on its own day.

## 3. What writing this doc found

1. **The images that pin the records are probably gone, and the rest are at risk (needs his check first).** ECR's
   lifecycle keeps at most ten images (`bootstrap/ecr.tf`, rule 2). Phase 1 §8 item 2 said official images would get a
   protected tag prefix "before Phase 4"; that rule was never written (not found in `ecr.tf` or any later doc). Every
   push touching `experiment/**` builds an image, results-only commits included, and the Deploy workflow has run 94
   times, 46 of them since the official grid ran (2026-10-14). **So the Phase 4 official image (`sha256:ff978703...`, every grid
   record) and Phase 1's skeleton image (`sha256:ef2582ed...`) have very likely expired, and Phase 5.5's
   (`sha256:ef0588f9...`, every case record, built at `101e2df`) is fifth newest by the deploy list.** Inferred, not measured: Claude's read-only ECR
   listing was denied, so his command below settles it. **Consequence for ordering:** the next push that builds an
   image moves Phase 5.5's image one step toward expiry, so the lifecycle fix (decision 7) is applied in `bootstrap`
   **before** any of this phase's code pushes. Writing and committing this doc pushes only `docs/` and builds nothing.
   What an expired image costs: the records still carry the digest, and the code is pinned by the tag, the archive and
   each record's `git_sha`; what is lost is the exact bytes, so the run cannot be repeated on the identical image.
   That is a reproducibility gap to state on the methods page, not a change to any result.
2. **Phase 4's manifest of raw objects was not committed (found only by search, which is not proof of absence).**
   Phase 4's runs half, decision 2 (a), his: "at this phase's close, commit a manifest of every pilot and official
   object (key, bytes, sha256), and publish the full text with the publish path (Phase 1.5, or 6.5 at the latest)."
   Its DoD audit (§13) has no row for it, and no manifest file is tracked. The manifest is what timestamps the raw
   record publicly. Decision 8.
3. **The `horizon-compact-dev` access key was due for deletion at Phase 1's close** (Phase 0.5 decision A, amended by
   Phase 1 decision 2), and this morning's Phase 1 audit missed it. It has carried every laptop command since
   (`--profile horizon-compact`), and this phase needs it: a `bootstrap` apply and S3 reads. Decision 6. Phase 1's
   §22 gets a dated note saying the audit missed it.
4. **Musical Mycelium's deploy role holds CloudFront actions on `*`** (its `bootstrap/oidc.tf`, "CloudFront does not
   support resource-level permissions for the actions that matter"). Copied here, this project's role could update
   or delete Musical Mycelium's distribution. Today's service reference shows distributions do take `aws:ResourceTag`,
   so this project fences its role by tag (§9). **The reverse is not this repo's to fix:** Musical Mycelium's role can
   still touch this project's distribution. That is recorded for him, and Musical Mycelium's Terraform is not
   changed from here (`CLAUDE.md`).
5. **The engine refuses the placeholder** (§0 item 2), so the scope doc's "aggregated by the real scorer" cannot hold
   for the placeholder without editing frozen code. The site-data builder is the honest substitute. Phase 6 reads the
   committed results files the frozen engine wrote; nothing about them changes here.
6. **Results-only commits rebuild the image** for nothing: the image copies all of `experiment/` (`Dockerfile`), the
   results included, though no run code reads `experiment/results/` (only laptop writers do; checked by search). Part
   of decision 7.
7. **The name guard will scan `web/package-lock.json`**, thousands of package names. A collision with a term is
   possible. If one happens, it is handled as every false positive is: he adds an `allow:` line with its reason to the
   private term file. A term is never removed and the hook is never skipped.

**His one command for finding 1** (read-only, free; prints which of the three record digests still exist, and nothing
else):

`aws ecr describe-images --repository-name horizon-compact --profile horizon-compact --region us-east-1 --query 'imageDetails[].imageDigest' --output text | tr '\t' '\n' | grep -E 'ff978703|ef2582ed|ef0588f9'`

Look for up to three `sha256:` lines. A missing prefix means that image has expired. No output means all three are
gone.

*Measured 2026-11-04, about 9:20 AM (his run):* one line, `sha256:ef0588f9...`. **Phase 5.5's image exists; the Phase
4 official image (`ff978703...`) and Phase 1's skeleton image (`ef2582ed...`) have expired.** The inference above
holds. The page this phase builds shows the skeleton sweep, so its provenance block (§7 item 7) states that the image
its digest names is no longer held in the registry, with the reason, rather than implying it can be pulled.

## 4. What this phase delivers

In build order, after the decisions:

1. **`bootstrap` first** (his apply, plan read by Claude): the ECR lifecycle fixed (decision 7), the origin access
   control and the response headers policy (decision 5), and the deploy policy's new grants (§9).
2. **The site-data builder**, `hc site data` (§6): placeholder records to one versioned JSON file, deterministic,
   committed.
3. **Phase 4's raw-object manifest** (decision 8): key, bytes and sha256 of every pilot and official object, committed.
4. **The page** in `web/` (§7), to the standard in §8, with his words.
5. **The site infrastructure in `main`** (§9): the site bucket and the distribution, and the deploy workflow's site
   half.
6. **The public URL:** the Vercel rewrite to the distribution (decision 4).
7. **The teardown test** (§10): destroy `main`, prove nothing billable is left, re-apply, move the rewrite, prove the
   page, its traceability and the raw record are intact.

## 5. Placeholder sweep shown (decision 1)

**Recommended: `skeleton-haiku-5-5-f1467906` alone.** It is the sweep Phase 1's DoD 1 closed on: the main model, 15
runs (five priorities, three repeats), one image, one session, all 15 `valid` on the first attempt. The garden
scenario: the club spends exactly $1,500, drawing from three sources (yearly fund up to $1,000, plant sale up to $400,
raffle up to $300) and spending on four uses (bulbs up to $700, herbs up to $600, irrigation up to $500, mulch and
compost up to $400; a fifth, a tool shed, is listed as not offered), and picks spring or autumn for the open day. The five priorities are color, fragrance, low water use, butterflies,
and none. Nothing in it touches the experiment's subject.

## 6. The site-data builder (run code; Sonnet builds, Opus reviews)

**Where:** `src/horizon_compact/site/` (`data.py`, the pure function; `cli.py` gains `hc site data`). It is run code
under `protocol/sets.py`'s rules: allowed after the tag, logged. It imports `analysis/records.read_runs` and changes
nothing frozen; `hc protocol check` proves that on every commit.

**Command:** `hc site data --experiment placeholder --sweep <id> --store s3|local [--bucket ...] [--profile ...]`.
It writes `web/src/data/placeholder.json` and prints the path, the sweep id and the run count.

**It refuses:** any experiment other than `placeholder`; any prefix other than `development/placeholder/<sweep_id>/`
(the role is fixed in code, not an argument); a sweep with unfinished runs; a run whose final attempt lacks the
provenance fields below; and a file that already holds different bytes. The same bytes again is a no-op, as
`write_results` does; replacing the file means deleting it on purpose first.

**The file (schema `horizon-compact/site-placeholder`, `schema_version` 1),** in this key order, with no timestamp of
its own:

- `schema`, `schema_version`, `kind: "test-run"`, `content: "placeholder"`.
- `sweep`: `sweep_id`, `experiment`, `role`, `model_key`, `served_models` (the distinct `provider_details.served_model`
  values), `runs_planned`, `runs_finished`, `status_counts`, `first_attempt_status_counts`, `cost_usd` (the sum of
  the session summaries' cost, the sweep's measured cost), `image_digests`, `git_shas`, `content_hashes` (each the
  distinct values, sorted), `runner`, `started_at` (earliest attempt), `finished_at` (latest).
- `scenario`: `id`, `total`, `lines` in canonical order (`key`, `label`, `kind` source or use, `cap`), `options` (the
  season choices), all read from `experiment/placeholder/` as hashed in the records.
- `objectives`, in the experiment's order: `id`, and the exact priority sentence the model was given (the template
  filled), so the page shows what was asked, not a paraphrase.
- `cells`, one per objective: `runs`, `valid`, the status counts, the first-attempt counts, and per line `mean`,
  `min`, `max` over valid runs; the choice counts.
- `runs`, sorted by `run_id`: `run_id`, `objective_id`, `wording_id`, `repeat`, `status`, `first_attempt_status`,
  `attempts`, `amounts` (as counted: scaled for `valid_rescaled`, from `read_runs`), `choice`, and the final attempt's
  `image_digest`, `git_sha`, `content_hash`, `served_model`, `runner`, `finished_at`.

**No memo is included.** Memos are model text and belong to Phase 6's memo reader with its labels. No account id can
appear: the records already hold `<account-id>` in the two ARN-shaped fields, and neither is copied; a test asserts no
12-digit run and no `arn:` string in the output.

**Bytes:** `json.dumps(..., indent=2, ensure_ascii=False, allow_nan=False)` plus one newline, floats as the records
hold them. The page formats for display; the file is never rounded.

**Tests** (fixtures are placeholder-shaped records written in the test, no real record): byte-identical output on a
second build; identical output from the S3 store and the local store over the same objects; each refusal above; key
order pinned; means and ranges by hand for one cell; no account-id pattern; no memo text.

**His run:** `hc site data` against S3 (read-only), then against the local copy laid out under `scratch/runs/`, then
`cmp` on the two outputs. The S3 run's file is committed.

## 7. The page

**One page, `web/`, Vite and React with TypeScript, plain CSS** (custom properties, no CSS framework and no component
library; both carry a recognizable default look, and one page does not need them). The data file is imported at build
time, so the first view needs no fetch and shows no loading state.

**What is on it, top to bottom.** The words marked *his* are his to write (`planning/06` §8); the rest are labels,
drafted by Claude, flagged as such when handed over, and approved by him word for word.

1. **The name, and one or two sentences on what the project is** (*his*).
2. **The test notice** (*his*): plain words that these are test runs on placeholder content, not results. Set in the
   page itself, near the top, at body size or larger, not in a footer.
3. **The chart** (§7.1), with a one-line title and a short key.
4. **First attempt beside final:** a small table per priority: runs, valid, valid on the first attempt, each failure
   status (all zero here, shown as zero, not hidden).
5. **The section for results against the thesis** (`planning/06` §6.1), present and empty: *his* title, and one *his*
   sentence saying it holds nothing yet and what it will hold. Same type and spacing as every other section.
6. **Every run, as a table:** run id, priority, status, attempts, each line's amount, the season, and a short image
   digest. This is the chart's table twin and the traceability path: every dot on the chart is a row here.
7. **Provenance:** sweep id, the served model's name from the records, the full image digest, the git SHA (linked to
   that commit on GitHub, a link and not a request), the content hash, the runner, the dates, the measured cost, a
   one-line note that the records are write-once in S3 under that sweep's prefix, and a one-line note that the image
   the digest names is no longer held in the registry (§3 finding 1, measured).
8. **Footer:** a link to the repository. Nothing else: no analytics, no badges, no "built with".

### 7.1 The chart (`dataviz` loaded; checked against its anti-patterns)

- **Form:** small multiples, one panel per priority (`planning/06` §7.2 rule 3), five panels, the lines in canonical
  order in every panel, sources above uses with a hairline and a two-word heading between them. **One shared x-axis**,
  $0 to $1,000 (the largest cap), ticks at $0, $250, $500, $750 and $1,000, starting at zero.
- **Marks:** each run is an 8px dot with a 2px ring in the surface color; the three runs of a line are offset by repeat
  index (fixed, not random jitter), so equal amounts stay visible as three. The mean is a short 2px vertical tick in
  the primary text color. Each line's cap is a hairline end mark in the muted color, so the constraint is visible.
  Gridlines are solid hairlines one step off the surface. No bar sits at the average: spread is the subject
  (`planning/06` §7.2 rule 2).
- **Color:** one series, so **one hue** (the skill's slot 1) for every dot, no categorical palette and no legend box;
  the panel title names the priority. Text never wears the hue. The palette for the five real objectives (`planning/06`
  §7.2 rule 1) is Phase 6's preview decision and is not pre-empted here. The hue and every text token are run through
  the skill's validator against both surfaces, light and dark, and the output is pasted into the build notes.
- **Labels inside the panel:** the priority name, `n = 3 runs`, the season chosen (for example "spring 2, autumn 1"),
  and the short test label, so a cropped screenshot of one panel still says what it is (`planning/06` §6.1's rule for
  memo cards, applied to charts).
- **Hover and focus:** each dot's hit area is at least 24px; a tooltip gives the amount first, then the line, the run
  id and the status. Keyboard: each panel is one tab stop, and the arrow keys move between its dots with the same
  tooltip. The tooltip enhances and never gates: every value is in §7 item 6's table.
- **Motion:** none. Phone width: panels stack in one column with the axis kept; nothing scrolls sideways except the
  run table, which scrolls inside its own frame with its first column fixed.

### 7.2 The frame (decision 2)

Type, measure and spacing set the page's character more than anything else on it. **If decision 2 is (a),** three
static previews of the same page, built from the real data file, differing only in type and frame, are put side by
side for him once; he picks one. The candidates, all open-licensed and self-hosted through npm packages:

- **A:** Source Serif 4 for headings and prose, Source Sans 3 for labels, tables and the chart.
- **B:** IBM Plex Serif and IBM Plex Sans, with Plex Mono for hashes and digests.
- **C:** no web font: the system's serif and sans stacks, zero font bytes.

Each preview: a text column of about 65 characters, a fixed type scale, tabular figures in tables and on axes only,
light and dark. Faces common across generated web apps (Inter, Geist) are left out on purpose, as the most visible
sign of a default.

## 8. What "polished" means here, as checks

His standard (2026-11-04): professional, with no telltale sign of generated filler. Each item below is checked at the
review step (§12, step 8), on screenshots at phone and desktop widths in both modes, and the misses are fixed before
the deploy commit.

- **No template residue:** the Vite starter's logos, counter, `App.css` and default title are gone; a favicon of his
  choice or none; the page title is the project's name.
- **No decoration that does no job** (`planning/06` §7.3's test, applied now): no gradients, glass or blur panels,
  drop-shadowed card stacks, pill badges, icon rows, emoji, hero illustrations, animated counters, or buttons with no
  action.
- **No filler words:** every sentence is his or an approved label. No "insights", "powered by", "unlock", "seamless",
  "delve", "leverage" or "robust" (the last also on `planning/06`'s list); no headline that promises a finding.
- **Typographic hierarchy, not boxes:** sections separated by space and type, a consistent scale, left-aligned text,
  numbers right-aligned in tables.
- **Honest data marks:** spread drawn, run counts in every panel, zero baselines, nothing conveyed by color alone,
  every number reachable as text.
- **Accessible:** `axe-core` reports nothing in the test suite; keyboard paths work; contrast passes the validator;
  `prefers-color-scheme` honored, with the dark steps chosen and validated, not inverted.
- **Small and fast:** an asset budget in `npm run check` (JavaScript under 100 KB gzipped, fonts under 150 KB), and
  no request to any host but the page's own (the content security policy and a test on the built files).

## 9. Infrastructure and permissions

**In `bootstrap`** (his apply with the dev key; the dev policy gains only what these resources need, pasted by him
first, as in Phase 1):

- **ECR lifecycle (decision 7 (a)):** rule 2 ("keep at most ten images") removed; rule 1 (untagged images expire after
  a day) kept. Images share most layers, so the storage this adds is measured at the close, expected to be cents a
  month inside the credits.
- **`aws_cloudfront_origin_access_control`** `horizon-compact-site`, SigV4, always sign.
- **`aws_cloudfront_response_headers_policy`** `horizon-compact-site`: `Content-Security-Policy: default-src 'none';
  script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; base-uri 'none';
  form-action 'none'; frame-ancestors 'none'`; `Strict-Transport-Security`; `X-Content-Type-Options: nosniff`;
  `Referrer-Policy: no-referrer`; `X-Robots-Tag: noindex` (decision 3, removed at go-live). Both objects are free, and
  living here they survive the teardown and never need a delete grant.
- **The deploy policy's new statements** (`infra/iam/deploy.json`, tests extended):
  - `SiteBucket`: `s3:*` on `horizon-compact-site-*` and its objects. Musical Mycelium's reason holds (the provider's
    read path for a bucket calls a dozen `Get*` actions); one bucket-name pattern is a tight boundary, and the
    existing deny on the results bucket stays.
  - `SiteDistributionCreate`: `cloudfront:CreateDistribution`, `cloudfront:TagResource` when `aws:RequestTag/Project`
    is `horizon-compact`.
  - `SiteDistributionManage`: `cloudfront:GetDistribution`, `GetDistributionConfig`, `UpdateDistribution`,
    `DeleteDistribution`, `CreateInvalidation`, `GetInvalidation`, `ListTagsForResource`, `TagResource`, `UntagResource`
    when `aws:ResourceTag/Project` is `horizon-compact`.
  - `SiteRead`: `cloudfront:ListDistributions`, `ListCachePolicies`, `GetCachePolicy`, `GetOriginAccessControl` and
    `GetResponseHeadersPolicy` on the two `bootstrap` objects; `tag:GetResources` (read-only, for §10's check).
  - Nothing that creates, updates or deletes an origin access control or a response headers policy.
- **The permission check** (`aws-permission-check.yml`) gains one attempt: `UpdateDistribution` on a distribution not
  tagged as this project's, with a stale `If-Match`. Authorization is evaluated first, so a denial proves the fence;
  if it were allowed, the stale tag makes the call fail with no change.

**In `main`** (`infra/terraform/main/site.tf`): the site bucket `horizon-compact-site-<account-id>` (all four public
access blocks, `force_destroy = true` because it holds only a build, so the teardown needs no emptying step; the
results bucket keeps `prevent_destroy`); its policy granting `s3:GetObject` to CloudFront only for this distribution
(`AWS:SourceArn`); the distribution (origin through the `bootstrap` access control, `redirect-to-https`, GET and HEAD,
compression, the managed CachingOptimized policy by name, the `bootstrap` headers policy, `PriceClass_100`, the
default certificate, `wait_for_deployment = false`, 403 and 404 served as `/index.html` with status 200, as Musical
Mycelium does). Outputs: the bucket (sensitive), the distribution id, and its domain (not an account identifier).

**The deploy workflow:**

- **Paths:** `web/**` added; `!experiment/results/**` added (decision 7 (a)), and `experiment/results/` added to the
  image's ignore list, so a results commit builds nothing.
- **A `changes` job** reads the push's changed paths (plain `git diff`, no third-party action) and sets two outputs:
  `code` (image and `apply main`) and `site`. A manual dispatch sets both.
- **The `site` job** runs after `infra` when it ran, or alone on a site-only push: Node 22, `npm ci`, `npm run check`
  (again, since a dispatch may target a commit CI never saw), build, then sync assets with a year's immutable cache,
  `index.html` with `no-cache`, invalidate `/*`, and a smoke test against the CloudFront domain: the new asset name
  in `index.html`, the content security policy and `X-Robots-Tag` headers present, the sweep id in the bundle. The
  smoke test never fetches the public URL, whose rewrite is his step, so a teardown day cannot turn it red.

**CI and `make check`:** `make web-check` (`npm --prefix web run check`: Prettier check, `tsc`, Vitest, build, asset
budget) joins `make check`; `make install` runs `npm --prefix web ci`; `ci.yml` adds `setup-node` and the install.
`web/` takes the root to 14 of 16.

## 10. The teardown test (DoD 3)

A dispatch-only workflow, `teardown.yml`, on the deploy role. It runs only when the dispatch input equals `destroy
main`.

1. **Before (his, laptop):** `hc sweep status` on the shown sweep, and a version count of `development/placeholder/`
   (`list-object-versions`: keys, versions, delete markers), saved to the evidence file.
2. **Destroy:** `terraform destroy` on `main` (a placeholder-shaped `image_digest` is passed, since nothing is
   created). The distribution is disabled and then deleted; this takes several minutes of runner time.
3. **Nothing billable from `main` remains:** `tag:GetResources` for `Project = horizon-compact` and `Root = main`
   returns nothing (retried for propagation), and the cluster and distribution are absent by name. Listed in the
   workflow's log.
4. **Re-apply:** he dispatches Deploy, which builds a new image (a new digest, logged; no sweep is planned on it),
   applies `main` and syncs the site to the new distribution.
5. **The rewrite:** the new domain from the log goes into `infra/vercel/vercel.json`; he commits it and deploys it
   (decision 4).
6. **After:** the public URL serves the new build (asset name), the run table's run ids and image digest match the
   records, and his step 1 commands give identical counts. Anything different is a failed test.

## 11. Decisions for him

**All ten DECIDED 2026-11-04 (his), as recommended.** Each keeps its framing below as the record.

1. **DECIDED 2026-11-04 (his): (a).** *Was:* **Which placeholder sweep the page shows.**
   - (a) **Recommended: `skeleton-haiku-5-5-f1467906` alone** (§5): the sweep Phase 1 closed on, one model, one
     chart.
   - (b) Also Phase 4's two final-image checks, one per model, shown separately. It sets the "never pooled" habit
     early, but it is three sweeps on a page whose job is the path, not the content.
2. **DECIDED 2026-11-04 (his): (a).** *Was:* **How much of the look is settled now.**
   - (a) **Recommended: one round of three type-and-frame previews now** (§7.2), and he picks; the chart's form stays as
     §7.1, and the real palette and layout stay Phase 6's. The public URL shows this page for weeks, until Phase 6.5's
     go-live, and type is the part least likely to change once seen with real data.
   - (b) The system stacks now, and every design choice in Phase 6, as the scope doc says.
3. **DECIDED 2026-11-04 (his): (a).** *Was:* **`noindex` until go-live.**
   - (a) **Recommended: yes**, by header and meta tag, removed in Phase 6.5's go-live deploy, so a search never
     returns the test page as the project.
   - (b) Indexable from now.
4. **DECIDED 2026-11-04 (his): (a).** *Was:* **How the Vercel rewrite is deployed.**
   - (a) **Recommended: by him from the tracked `infra/vercel/` folder with the Vercel CLI**, linking the existing
     project once. No third-party app on the repository, no Vercel status checks on commits, and a deploy happens only
     when he means one; the rewrite changes about twice in v1.
   - (b) Git-integrated with Root Directory `infra/vercel`, as Musical Mycelium does: a push redeploys it, and Vercel
     posts a check on commits.
5. **DECIDED 2026-11-04 (his): (a).** *Was:* **Where the two objects that cannot be fenced by tag live.**
   - (a) **Recommended: in `bootstrap`** (§9), applied by him. The deploy role never holds a create, update or delete
     on them, so it cannot touch Musical Mycelium's.
   - (b) In `main`, with those actions on `*`, as Musical Mycelium does. Simpler, and this project's role could then
     alter or delete Musical Mycelium's origin access controls and headers policies.
6. **DECIDED 2026-11-04 (his): (a).** *Was:* **The `horizon-compact-dev` access key** (§3 finding 3).
   - (a) **Recommended: keep it until Phase 7 closes or 2027-01-02, whichever is first** (90 days from its creation),
     then delete it; recorded as Phase 0.5 decision A amended a second time. Phases 1.5 to 6.5 all need laptop reads
     of S3, and this phase needs a `bootstrap` apply.
   - (b) Delete it now and create a short-lived key for each step that needs one.
7. **DECIDED 2026-11-04 (his): (a).** *Was:* **The image record** (§3 findings 1 and 6), after his ECR check.
   - (a) **Recommended: in this phase, first:** remove the ten-image rule in `bootstrap` before any code push, stop
     building images on results-only commits, and record in `KNOWN-GAPS.md` which record digests no longer exist, for
     the methods page.
   - (b) Record the gap and fix the lifecycle in Phase 6.5. Each code push before then can expire Phase 5.5's image.
8. **DECIDED 2026-11-04 (his): (a).** *Was:* **Phase 4's raw-object manifest and the raw text** (§3 finding 2).
   - (a) **Recommended: the manifest in this phase** (a run-code command over the pilot and official prefixes:
     key, bytes, sha256; his read-only run; committed as evidence), **the full text in Phase 6.5** with the re-scoring
     check that reads it.
   - (b) Both in Phase 6.5.
9. **DECIDED 2026-11-04 (his): (a).** *Was:* **The teardown deletes the sweep log group early.** Its retention is 30 days, so Phase 5.5's task logs
   (2026-10-29 to 30) would otherwise expire around 2026-11-29. The record is S3, and the logs' one use (no key-shaped
   string, checked) is done.
   - (a) **Recommended: run the teardown in this phase and accept it**, recorded.
   - (b) Wait until after 2026-11-30 to run the teardown.
10. **DECIDED 2026-11-04 (his): (a).** *Was:* **The version at the close.**
    - (a) **Recommended: 0.5.5 in one step at Phase 1.5's close.** Every phase through 5.5 is then closed, and Phase 2
      decision 4's rule is that the version never claims a phase that is not done; the out-of-order history stays in
      `ROADMAP.md`. The version is not in the lock (checked).
    - (b) 0.1.5 now, then a separate commit for each later version.

**His words, to write rather than decide:** the name line and the one or two sentences on the project (§7 item 1), the
test notice (item 2), the title and the one sentence of the results-against-the-thesis section (item 5), and the
page's meta description if he wants one. The build keeps them in one file, `web/src/copy.ts`; a test fails while any
of them is still a marked placeholder, so the deploy commit cannot ship without them.

## 12. Order of work

0. **[done 2026-11-04, except his ECR command]** **[his]** Read this doc; take the decisions. **His ECR command** (§3). Claude writes the dated notes: scope doc
   (§0), `planning/02` §2.8, Phase 1 §22 (the key), and the `KNOWN-GAPS.md` entries for §3 findings 1-4. **His commit
   C0** (docs only; builds nothing).
1. **[done 2026-11-04: built (Sonnet), reviewed (Opus), applied and committed `0526a2b` (his); CI and Deploy green]** **[Claude, then his]** **C1, `bootstrap`:** the lifecycle change, the two CloudFront objects, the deploy policy and
   its tests, the dev policy's additions. He pastes the dev policy; plans; Claude reads the plan (nothing destroyed;
   only the listed changes); he applies; plans again for "No changes". The deploy paths and the image ignore list go
   in the same commit. He commits and pushes; CI and Deploy green.
2. **[done 2026-11-04 except his commit and push: built (Sonnet), reviewed (Opus); his S3 and local runs, `cmp: identical`]** **[Sonnet builds, Opus reviews]**
   **C2, the site-data builder** (§6) with tests; his S3 and local runs and the `cmp`; the JSON committed with it.
3. **[Sonnet builds, Opus reviews; his run]** **The raw-object manifest** (decision 8 (a)), committed as
   `docs/phases/evidence/phase-4/raw-manifest.json` with the command's code.
4. **[Claude, then his]** **The previews** (decision 2), in `scratch/` (gitignored); he picks.
5. **[Sonnet builds, Opus reviews]** **C3, the page** (§7, §8): `web/`, `make web-check`, `ci.yml`. His words land in
   `copy.ts` before this commit. Built and checked locally (`npm run dev`, then the production build served with the
   content security policy set locally); Deploy does not yet watch `web/**`, so this push runs CI only.
6. **[Sonnet builds, Opus reviews]** **C4, the site in `main`:** `site.tf`, the deploy workflow's `changes` and `site`
   jobs, `teardown.yml`, the permission check's new attempt. He pushes; Claude reads the Deploy log; each missing
   permission is added by name, scoped, with the error recorded, as in Phase 1.
7. **[his]** **The permission check**, dispatched; Claude reads the log.
8. **[his, Claude reading]** **The review against §8**, on the CloudFront domain, at both widths, both modes. Fixes
   before the next step.
9. **[his]** **C5, the rewrite:** `infra/vercel/vercel.json` with the domain; deploy (decision 4); the public URL
   checked.
10. **[his, Claude reading]** **The teardown test** (§10); C6, the evidence and the rewrite's new domain.
11. **A day later:** the spend from the bills (his Console readings: AWS Cost Explorer for the build days, filtered to
    the `Project` tag; no model call means no Anthropic or OpenRouter line), then **the
    close (C7):** the DoD audit, the version (decision 10), `ROADMAP.md`, `KNOWN-GAPS.md`.

## 13. Definition of done, and the proof of each

| Scope DoD (as read through §0) | Proof |
|---|---|
| 1. The page at `horizon-compact.vercel.app` shows the placeholder sweep with spread and run counts, labeled a test in his words; any number traced to run ids and image digest | the live page; the run table against the JSON and the records; a screenshot set committed |
| 2. The published JSON is committed, produced by the site-data builder; a re-run is byte-identical | the builder's tests; his `cmp` |
| 3. Destroy and re-apply both succeed; nothing billable left; page, traceability and raw record back | `teardown.yml` and Deploy run ids; §10 step 3's listing; step 1 and step 6 counts equal |
| 4. The section for results against the thesis is on the page, with his title | the live page; `copy.ts` |
| 5. `make check` and CI green; root under cap; every commit through the guard | CI and Deploy run ids; `make root-check` |
| 6. Spend measured from the bill; with Phase 1's, about $1 or less | his readings, §12 step 11 |
| *Added by this doc:* 7. No request leaves for another host; the security headers are served | the smoke test; the built-files test; the headers at the public URL |
| *Added by this doc:* 8. The deploy role cannot change a distribution that is not this project's | the permission-check run id |
| *Added by this doc:* 9. The image record: the lifecycle no longer expires images, and the lost digests are recorded | the `bootstrap` plan; the `KNOWN-GAPS.md` entry |
| *Added by this doc:* 10. §8's checks pass | the review notes, step 8 |

## 14. Cost

**No model call. AWS: cents,** inside the credits: CloudFront and S3 at this size sit inside CloudFront's free usage
allowance (rechecked at the build); a distribution and an access control cost nothing at rest; the teardown's minutes
cost nothing extra; ECR storage grows by the images no longer expired (measured at the close). **GitHub Actions:** free
for a public repository. **Vercel:** the Hobby plan, free. **Cost Explorer** read in the Console, which is free (the
API is $0.01 a request).

## 15. Genuinely uncertain

- **Whether Vercel passes CloudFront's security headers through the rewrite.** Musical Mycelium's public URL passes
  `cache-control` through (checked today). Checked at step 9; if a header is dropped, the same policy goes into
  `vercel.json`'s `headers`.
- **Whether the provider's create call satisfies `aws:RequestTag`** with `default_tags`. The first deploy shows it; a
  denial is fixed by name.
- **Whether anything Vite emits trips the content security policy.** Checked in step 5 by serving the production
  build locally with the policy set.
- **Which images still exist** (§3 finding 1), until his command runs.
- **The first full destroy of `main` in this repository.** Phase 1 granted every delete but never ran one; a missing
  verb shows in step 10 and is added by name.
- **A name-guard hit in `package-lock.json`** (§3 finding 7).

## 16. Rules this phase must not break

- **Nothing on the page can be read as a finding.** Placeholder content only; his test notice near the top; the
  builder refuses every other record.
- **No official or case result reaches the public URL** before Phase 6.5's go-live (Phase 6 decision 2).
- **Nothing frozen changes:** `hc protocol check` ok on every commit.
- **Public words are his;** labels are flagged as Claude-drafted when handed over.
- **No account id or email address in a tracked file;** the bucket name is computed, never written.
- **Nothing always-on;** Musical Mycelium's resources, budgets and Terraform are not changed from here.
- **He runs every apply, commit, push and dispatch;** Claude reads plans and logs.

## 17. As built, C1 (2026-11-04)

Built by Sonnet from `scratch/p15-c1-build-prompt.md`. Code and tests only: no AWS call, no `terraform plan`, `apply`
or backend `init`, no commit, no push. **Review, his plan and his apply are owed.** *(Done the same day; see below.)*

**What was built**

- `infra/terraform/bootstrap/ecr.tf`: rule 2 ("keep at most ten images") removed; rule 1 (untagged expire after one
  day) kept exactly; the comment rewritten to say why (the old rule expired Phase 4's official image and Phase 1's
  skeleton image; Phase 1 §8 item 2's protected prefix was never written; KNOWN-GAPS OPEN 2026-11-04).
- `infra/terraform/bootstrap/site.tf` (new): `aws_cloudfront_origin_access_control.site` and
  `aws_cloudfront_response_headers_policy.site`, both named `${var.project}-site`, with the headers of §9 exactly
  (the content security policy string as written, override true; Strict-Transport-Security 63072000 with
  `includeSubDomains`; `nosniff`; `no-referrer`; custom `X-Robots-Tag: noindex`, override true). A comment says the
  noindex header goes at Phase 6.5's go-live.
- `outputs.tf`: `site_origin_access_control_id` and `site_response_headers_policy_id`, not sensitive.
- `infra/iam/deploy-site.json` (new), `iam.tf`: the four site statements of §9, as an **inline policy on the deploy
  role** (see the first departure). `SiteRead` is three statements (`SiteRead`, `SiteReadOriginAccessControl`,
  `SiteReadResponseHeadersPolicy`) because the two Get actions name different resources. No create, update or delete
  of an origin access control or a response headers policy, and no `cloudfront:*`, anywhere in either deploy file.
  `deploy.json` is unchanged, so every existing Deny is. Read: no existing Deny reaches the new statements (the
  results-bucket deny names that bucket only; the rest are on ec2, iam, ecs and bedrock). A test holds this.
- `infra/iam/horizon-compact-dev-policy.json`: one statement, `CloudFrontBootstrapObjects` (see the second
  departure). ECR (`ecr:*` on the repository, so the lifecycle change) and the role-policy actions (`ProjectRoles`
  already covers `PutRolePolicy`, `GetRolePolicy`, `DeleteRolePolicy`) were already there; nothing duplicated. Its
  existing denies are kept.
- `.github/workflows/deploy.yml`: `"!experiment/results/**"` added to `on.push.paths` after `"experiment/**"`; nothing
  else, and no `web/**`.
- `infra/docker/Dockerfile.dockerignore`: `experiment/results/` after the `!experiment/` line, with a comment.
- `tests/test_architecture.py`: 13 tests added (3145 pass after, 3132 before): the lifecycle has no
  `imageCountMoreThan` rule and keeps the untagged rule; the access control and the headers policy; the two outputs;
  the four site statements' actions, resources and conditions; no `cloudfront:*` and no write on the two objects;
  `s3:*` only on the site bucket pattern; no Deny reaches the site grants; the dev policy's size and its new
  statement; the deploy paths; the ignore file's order. The size test now covers `deploy-site.json`.

**Schema check (the provider this root has locked).** `terraform -chdir=infra/terraform/bootstrap providers schema
-json` on the already-initialised local root (reads the local plugin; no AWS call), provider `hashicorp/aws` 6.67.0
from `.terraform.lock.hcl`. Confirmed: the access control takes `name`, `origin_access_control_origin_type`,
`signing_behavior`, `signing_protocol` (all required), `description`, and exports `arn` and `id`; the headers policy
takes `security_headers_config` (with `content_security_policy`, `strict_transport_security`, `content_type_options`,
`referrer_policy` blocks) and `custom_headers_config` (`items` with `header`, `value`, `override`), and exports `arn`
and `id`. `terraform validate` and `fmt -check` pass on the root.

**The search for item 7: does anything the container runs read `experiment/results/`?** Searched `src/` for the
three path helpers that name it (`analysis/results.py` `RESULTS_ROOT`, `caseprobe/match.py` `CASE_RESULTS_DIR`,
`caseprobe/reident.py` `PUBLIC_DIR`) and every caller. Callers: `results.write_results` (reached from `hc analyze`),
`match.py` (`hc case match`'s checks) and `memos.py` (`hc case memos`'s scan, and its re-identification verdict
read): all laptop commands. The task definition (`infra/terraform/main/ecs.tf`) sets no command; the entrypoint is
`hc`, and `hc sweep launch` supplies `sweep run` or the case session. Also searched: every `rglob`, `glob`,
`iterdir` over the experiment folder (none reaches `results/`); the protocol lock (`protocol/lock.py` hashes the
frozen code sets, `experiment/protocol/` files, `uv.lock`, the simulation results under `docs/`, and
`experiment/<experiment name>/` for the experiment tree hash, which never names `results`); the gate
(`protocol/gate.py`) and `protocol/sets.py`; and the `Dockerfile` (`COPY experiment ./experiment` only). **Nothing
reads it.** A grep miss is not proof (CLAUDE.md), so the proof is the build: **Docker was available; the image was
built locally from `infra/docker/Dockerfile`, `ls /app/experiment` shows `README.md case-forms cases company
models.toml placeholder protocol readers s4shape shapes` with no `results`, `find` finds no path containing
`results`, and `hc protocol check` inside the image prints `protocol check: ok`.** The local image was removed after.

**Departures: what did not fit, and what was done instead**

1. **The deploy policy's four statements did not fit in `deploy.json`.** It renders to 5,674 of IAM's 6,144 non-space
   characters; the four statements (about 1,430 with the ARN variables) would take it to about 7,100. Done instead:
   they are in a new `infra/iam/deploy-site.json`, attached as an **inline policy** (`aws_iam_role_policy`
   `horizon-compact-deploy-site`) on the existing deploy role. Why inline and not a second managed policy: the dev
   key's `ProjectRoles` statement already covers `PutRolePolicy`, `GetRolePolicy` and `DeleteRolePolicy` on
   `role/horizon-compact-*`, so the dev policy needs nothing for the attach (a second managed policy would have
   needed `AttachDeployPolicyOnly`'s condition widened); and `NeverChangeOwnPermissions` (`iam:*` on the role) already
   covers editing it. The two new ARNs are passed through a separate `site_policy_vars`, so the boundary and the
   deploy policy do not read values unknown until the objects exist and will not show as changed in the plan. The
   statements, actions, resources and conditions are exactly as decided; only the file differs. **Opus to confirm
   inline, or ask for a managed policy and the wider dev attach condition.** Expected new plan lines: one
   `aws_iam_role_policy.github_deploy_site`.
2. **The dev policy's twelve named actions did not fit either.** It was 5,727 characters; twelve named
   CloudFront actions add 558, giving about 6,285. Done instead: two wildcard actions in one statement,
   `cloudfront:*OriginAccessControl*` and `cloudfront:*ResponseHeadersPolic*` (the last one short on purpose, since
   `ListResponseHeadersPolicies` ends "Policies"), on `*`. They cover the twelve decided actions and, by their
   names, nothing else in CloudFront's current action list as Sonnet knows it. **That was not checked against AWS's
   service reference, which Sonnet did not read; Opus to confirm.** The file is now 5,878 characters. A test holds
   the file under the limit.
   **Opus review (2026-11-04):** checked against AWS's service reference (`servicereference.us-east-1.amazonaws.com`,
   CloudFront, 173 actions, read 2026-11-04). The first wildcard matches the six access-control actions exactly. The
   second also matched `ListDistributionsByResponseHeadersPolicyId` (read-only, but not decided), so it was narrowed
   to `cloudfront:*ResponseHeadersPolicy` plus `GetResponseHeadersPolicyConfig` and `ListResponseHeadersPolicies`
   named: the statement now matches the twelve decided actions and nothing else. The file is 5,963 characters.
3. **The outputs test.** `test_outputs_with_account_ids_are_sensitive` required every output in `bootstrap` to be
   sensitive. The two new ids are not (decided point 3), so the test now skips exactly those two by name, and a new
   test checks they come from the two resources and are not marked sensitive.
4. **The whole-service-wildcard test.** `test_deploy_policy_has_no_wildcard_allow_of_a_whole_service` still holds
   for `deploy.json` unchanged. `SiteBucket`'s `s3:*` is in `deploy-site.json`, and a new test allows it only on the
   two site-bucket resources.

**For the review and the plan.** (a) The plan should add exactly: the access control, the headers policy, the inline
role policy, and two outputs; change the ECR lifecycle policy in place (rule 2 gone); and destroy nothing. (b)
`aws:RequestTag` on `CreateDistribution` is untested until C4 (§15). (c) Nothing in `main` changed, and no
CloudFront variable exists in CI yet. (d) `make check`: green, **3145 tests pass**; `hc protocol check` ok.

**Review, plan and apply (2026-11-04, about 11:20 AM to noon).** Opus reviewed the build against the decided points
(see departure 2's review note; departure 1, the inline policy, confirmed: the deploy role has no permissions
boundary, `NeverChangeOwnPermissions` already denies it `iam:*` on itself, and the dev key already holds
`PutRolePolicy` on it). `make check` green, 3145 passed; `hc protocol check` ok. He pasted the dev policy ("Policy
horizon-compact-dev updated."). **His plan: 4 to add, 0 to change, 1 to destroy**, not the 3/1/0 expected above: the
provider marks a change to `aws_ecr_lifecycle_policy`'s `policy` as forcing replacement, so the lifecycle policy was
deleted and recreated (rule 1 unchanged, rule 2 gone). Deleting a lifecycle policy deletes no image. Nothing else
changed or was destroyed; the boundary and the deploy policy were untouched. **His apply: "Apply complete!
Resources: 4 added, 0 changed, 1 destroyed."** Outputs `site_origin_access_control_id = E1L3LEZALRKH6Y`,
`site_response_headers_policy_id = e75c6c69-6030-4efb-ba96-014e5a493e08`. **His second plan: "No changes."** **His ECR
check after the apply (§3's command): Phase 5.5's image `sha256:ef0588f9...` is present**; the KNOWN-GAPS ECR entry is
closed. The commit and its push are owed; the push runs Deploy (it touches `infra/**` and `deploy.yml`) and builds an
image, which is now safe.

**Committed and pushed (2026-11-04, about noon):** his commit `0526a2b`. CI run `41882765796` passed; Deploy run
`41882765814` passed, built the image `sha256:2b95efa8...` (the first without `experiment/results/`), and replaced
only `main`'s sweep task definition to name it ("1 added, 0 changed, 1 destroyed"), as every image-building deploy
does. The task definition it replaced named `sha256:ad14e7b4...`, a later image than Phase 5.5's and named by no
record (not traced). **C1 is done.**

## 18. As built, C2 (2026-11-04)

Built by Sonnet from `scratch/p15-c2-build-prompt.md`. Code, tests and two scripts for him. No AWS call of any kind
(`make check`'s own `terraform init -backend=false` and `validate` aside), no commit, no push. `web/src/data/placeholder.json`
was **not** written: it comes from his S3 run. **Review, his S3 run, his local run and the `cmp` are owed.** *(Done the same day; see below.)*

**What was built**

- `src/horizon_compact/site/data.py` (new, run code, standard library only): `build_site_data(source, sweep_id,
  experiment) -> str`, `write_site_data(text, path) -> Path`, and `SiteDataRefusal`. The builder takes an
  `analysis.records.RecordSource`, never a `Store`; it calls the frozen `read_runs` and nothing else frozen is
  changed. The prefix is `development/placeholder/<sweep_id>/`, built in code; the experiment must be `placeholder`
  and the sweep id must `fullmatch` `[a-z0-9][a-z0-9-]*`.
- `src/horizon_compact/cli.py`: a `site` group with one command, `hc site data --experiment placeholder --sweep <id>
  --store s3|local [--bucket ...] [--profile ...] [--out PATH]`. `--store` is required; the bucket falls back to
  `HC_RESULTS_BUCKET` through the existing `_store` and `_session`. `--out` defaults to
  `<repo top>/web/src/data/placeholder.json`. Hidden test-only arguments: `--experiment-dir` and `--runs-root` (a
  local store's root). It prints the path, the sweep id and the run count. A refusal prints `refused: ...` and
  returns `REFUSED_EXIT`. The module is imported inside the command, as `cmd_analyze` does.
- `tests/test_site_data.py` (new, 50 tests): second build byte-identical; the builder writes nothing to the store;
  `S3Store` (a small fake client with paginated listing) and `LocalStore` give identical text; key order pinned at
  every level; one cell worked by hand, a mean checked against `fsum`, a `valid_rescaled` run counted at its scaled
  amounts, a cell with no valid run (null ranges), the earliest start taken over all attempts, the cost summed over two
  sessions; no memo text, request id, ARN or account-bearing field in the output; the account-id check both ways (a
  lone 12-digit number and an ARN are refused, a digest holding twelve decimal digits in a row is not); each refusal
  of decided point 3, one test each (plus the ones listed below); the writer's no-op, refusal and newline bytes;
  the command end to end on the local store, its refusals, the store being required, and `--store s3` needing a
  profile and a bucket.
- `scratch/p15-c2-s3.sh` and `scratch/p15-c2-local.sh` (gitignored; his).

**Run on the real copy (no AWS).** The skeleton sweep copied to the local store's layout and built: 15 runs, five
cells (three valid each; `color` 2 spring and 1 autumn, the other four 3 autumn), one image digest, one git SHA, one
content hash (`46cc488a...`, equal to `load_experiment("placeholder").content_hash`), runner `fargate`, cost
`0.013993`. No memo text (the first 40 characters of every one of the 15 memos searched for: none), no `arn:`, no
12-digit run. The local script was also run twice end to end: the copy is idempotent, the build is a no-op the second
time, and the `cmp` fails only because the web file does not exist yet.

**Departures: what did not fit, and what was done instead**

1. **`runner` became `runners`** (a sorted list), as for `served_models` and the other distinct-value fields. §6 had a
   single `runner`; a sweep resumed from another place has more than one. Per-run `runner` is unchanged.
2. **`not_offered` was added to `scenario`** (each `key`, `label`, `note`), after `lines` and before `choice`; the
   model saw those levers, so the page may show them. §6's `options` is `choice` (`key`, `label`, `options` as `key`
   and `text`), as decided point 4 says.
3. **Refusals beyond the decided list**, each with a test: an objective with no runs in the sweep; a run whose
   objective or scenario the experiment does not have; a valid run whose amounts do not match the scenario's lines or
   whose choice is not an option; a session summary naming another sweep or with no `cost_usd_this_session`; a sweep
   with no runs. `RecordRefusal` from `read_runs` is re-raised as `SiteDataRefusal`.
4. **The account-id check, as decided, has one known false positive: a run id that is twelve decimal digits.** The
   decided pattern excludes letters and digits on either side, not `-`, so `r-123456789012` matches. A random run id
   (twelve hex characters) is all digits about 0.35 percent of the time, so about 5 percent of the time a sweep of 15
   runs would be refused, loudly and with the output not produced. The skeleton sweep is not affected (it built). The
   test fixtures use ids with a letter in them for this reason.

   **Review (Opus, 2026-11-04): no code change, and the fix first proposed here is wrong.** Adding `-` to the
   lookbehind would stop the check catching an account id after a hyphen, which is exactly how this project's
   bucket name ends: the likeliest leak is the one it would miss. The page shows one sweep (decision 1), which
   built clean, and a false positive refuses loudly rather than leaking, so it stays as decided. If another sweep is
   ever refused this way, the fix is to exempt the run-id values themselves (blank each `"r-[0-9a-f]{12}"` token
   before scanning), not to widen the lookbehind. The same holds for a float whose shortest form has exactly twelve
   decimals (a mean of five integer digits can, as `12345.666666666666` does); at the placeholder's scale (lines of
   at most 1,000, means of three) none occurred in a million trial means.
5. **`cp -rn` prints a coreutils warning** ("behavior of -n is non-portable"). It is harmless; the script copies the
   contents (`.../.`) so a second run is a no-op and never nests a copy.

**The deny list.** `.claude/settings.json` is **not** changed. Its list keeps Claude from the commands that read or
write pilot and official records and spend money. This command can only build a `development/placeholder/` prefix:
the prefix is fixed in code and checked twice (the builder's own rule, then `read_runs`'s refusal of any other
development experiment), and it only reads.

**For later steps.** C3's Prettier check must exclude `web/src/data/` (a `.prettierignore` line), or a reformat would
break the byte identity DoD 2 rests on.

**`make check`: green, 3195 tests pass** (3145 before this step); `hc protocol check` ok. Frozen files untouched.

**His runs (2026-11-04, about 3:20 PM).** `scratch/p15-c2-s3.sh` read the bucket (read-only) and wrote
`web/src/data/placeholder.json`: sweep `skeleton-haiku-5-5-f1467906`, 15 runs. Opus checked the file: 15 runs, five
cells, cost `0.013993`, content hash `46cc488a...`, no `arn:` and no memo text. `scratch/p15-c2-local.sh` built the same
sweep from the local copy and ended **`cmp: identical`** (DoD 2's byte identity holds for this sweep). Opus re-ran
`make check` after the review: green, 3195. **Owed: his commit, which carries the code, the tests, the JSON and these
notes, and its push** (it touches `src/**`, so Deploy builds an image; safe since C1).
