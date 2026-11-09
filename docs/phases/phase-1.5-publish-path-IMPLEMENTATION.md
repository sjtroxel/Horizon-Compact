# Phase 1.5 — Publish Path: IMPLEMENTATION (v0.1.5)

> **IMPLEMENTATION doc. APPROVED 2026-11-04, about 9:05 AM (his): all ten decisions in §11 as recommended, (a).**
> **CLOSED 2026-11-08** (his commit of §26): DoD 1-10 met, the spend $0.01 by his Cost Explorer reading, version `0.5.5`.
>
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

### 7.3 His decisions after the previews (2026-11-05)

- **Type: A,** Source Serif 4 for headings and prose, Source Sans 3 for labels, tables and the chart; the system mono
  stack for ids and hashes (A carries no mono face). Self-hosted from `@fontsource`, weights 400, 400 italic and 600
  for the serif, 400 and 600 for the sans (about 91 KB of WOFF2, inside §8's 150 KB budget).
- **Footer: his footer from every other project** (Patchwork Assurance, Heritage Odyssey, Asteroid Bonanza, Poster
  Pilot): `© 2026 sjtroxel`, the GitHub mark linking to the repository, `. All rights reserved.` It replaces §7 item
  8's bare link and is still nothing else: no analytics, no badges, no "built with".
- **A logo and a favicon,** his pick from previews (§8 already allowed "a favicon of his choice"). No mark that draws
  convergence: whether the long horizons converge is the claim under test. **His ask after round 2: a warm sun,
  yellow or orange, not the chart's blue** (the logo is not data, so the one-series-hue rule does not bind it). A
  warm pair per mode: a deeper step on light surfaces and white tabs, a brighter one on dark; the dark horizon line
  carries the shape on white. **His pick: logo 1b, the sun on the horizon with three rays, in golden** (`#e9a23b` on
  light surfaces, `#f4c04f` on dark), 2026-11-05. The plain half-sun (1) was read by a friend as an egg; the rays fix
  that read and still separate at 16px, where five rays blurred. The honest cost: it sits close to the common
  weather-app "sunrise" glyph. Source: `scratch/previews/sun_variants.py`. **Then his refinement, the same morning:
  1b stays the favicon, and the page header carries 1e** (1c's sun cut by the horizon with a line below, plus 1b's
  three rays; `scratch/previews/sun_pair.py`) at about 56px, where it has room to read; at 16px 1e blurs, which is
  why the two sizes take two marks of one family.
- **The name's face: Big Shoulders Display 800** (his pick from seven, 2026-11-05, `scratch/previews/titles.py`),
  for "Horizon Compact" only. His reason: the serif title over an italic serif lede on cream read as AI-generated.
  **Section headings in Source Sans 3 semibold** (his pick over Source Serif 4, `scratch/previews/heads.py`).
  Source Serif 4 stays for prose, now **upright**: the lede and the notice are no longer italic. So A's type is
  amended: no serif headings, and the serif needs only its 400.
- **Amended 2026-11-06 (his, at the §8 review, §22):** the prose face is **Newsreader 400** (`@fontsource/newsreader`),
  replacing Source Serif 4, and the lede drops from 22px to **19px**; body prose stays 17px. The static file sets one
  step larger than the previewed variable font, so 19 and 17 are deliberate.
- **Drafted labels avoid the rhythm he reads as generated** (his note, 2026-11-05): runs of short one-fact
  sentences of the same length, joined instead where a person would join them; likewise no "not X, it's Y" turns,
  reflexive threes, colon reveals or tidy closers. He still approves every label word for word.
- **Color identity: Ink and paper** (his pick, 2026-11-05): light, a warm paper surface (`#f6f2e9`) with dark-blue
  ink; dark, deep navy (`#0f1520`) with warm ink and a gold accent. Every token validated in both modes
  (`scratch/previews/identities-validator.txt`: text at least 4.5:1, marks at least 3:1).
- **Asked for a marketing-agency splash with motion and vivid color, then chose against it** on the reasons given:
  `planning/06` §7.2 rules 1 and 7, §8 below (his standard of 2026-11-04), and Phase 6 decision 6, whose impressive
  layer is where a splash belongs, built from real results. **Instead, within the rules:** a bold first screen (large
  serif title, his sentences, the chart directly under the notice); a color identity for the page itself, his pick
  from previews, every token validated in both modes, with the data hue still the one series hue; and **transitions
  done exceptionally well**, every one doing a job (`planning/06` §7.2 rule 7): hovering or focusing a run lights its
  dots in every line of its panel and its row in the run table, the rest dimmed; a priority control that brings one
  panel forward and dims the rest; a tooltip that eases in. No entrance animation, no gradient, no glow; every
  transition off under `prefers-reduced-motion`.

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
2. **[done 2026-11-04: built (Sonnet), reviewed (Opus); his S3 and local runs, `cmp: identical`; committed `b9b8ac8` and pushed (his); CI and Deploy green]** **[Sonnet builds, Opus reviews]**
   **C2, the site-data builder** (§6) with tests; his S3 and local runs and the `cmp`; the JSON committed with it.
3. **[done 2026-11-05: built (Sonnet), reviewed (Opus, one fix: errors/ keys count as calls); his S3 run wrote the manifest, 5,247 objects, every sweep's calls matched; committed `3714f44` and pushed (his); CI and Deploy green]** **The raw-object manifest** (decision 8 (a)), committed as
   `docs/phases/evidence/phase-4/raw-manifest.json` with the command's code.
4. **[done 2026-11-05: previews built (Opus), `scratch/previews/`; his pick: A, Source Serif 4 and Source Sans 3]** **[Claude, then his]** **The previews** (decision 2), in `scratch/` (gitignored); he picks.
5. **[built 2026-11-05 (Sonnet); reviewed (Opus, one test fix); his words and the three label redrafts approved by him, the other drafted labels approved 2026-11-06 (one change, §20); `make check` green; committed `ea2bb7d` and pushed (his); CI green, run `42112962435`]** **C3, the page** (§7, §8): `web/`, `make web-check`, `ci.yml`. His words land in
   `copy.ts` before this commit. Built and checked locally (`npm run dev`, then the production build served with the
   content security policy set locally); Deploy does not yet watch `web/**`, so this push runs CI only.
6. **[done 2026-11-06: built (Opus, in session, his call); his `bootstrap` apply and two repository variables; committed `69b88ce` (his); CI and Deploy green, first attempt, no permission added; §21]** **[Sonnet builds, Opus reviews]** **C4, the site in `main`:** `site.tf`, the deploy workflow's `changes` and `site`
   jobs, `teardown.yml`, the permission check's new attempt. He pushes; Claude reads the Deploy log; each missing
   permission is added by name, scoped, with the error recorded, as in Phase 1.
7. **[done 2026-11-06: run `42245451195`, all six refused; §21]** **[his]** **The permission check**, dispatched; Claude reads the log.
8. **[reviewed 2026-11-06: five misses, three departures accepted, his type change; §22. Fixes built 2026-11-06 (Sonnet), reviewed (Opus, one change by his decision: the panel scroll on a phone only); §23, §23a. Done 2026-11-07: committed `a121fc3` (his), CI `42311321663` and Deploy `42311321638` green, the live page matches the reviewed build]** **[his, Claude reading]** **The review against §8**, on the CloudFront domain, at both widths, both modes. Fixes
   before the next step.
9. **[done 2026-11-07: deployed by him, checked by Claude; §24]** **[his]** **C5, the rewrite:** `infra/vercel/vercel.json` with the domain; deploy (decision 4); the public URL
   checked.
10. **[done 2026-11-07: passed, two fixes on the way; §25, `evidence/phase-1.5/teardown.md`]** **[his, Claude reading]** **The teardown test** (§10); C6, the evidence and the rewrite's new domain.
11. **[done 2026-11-08: his Cost Explorer reading $0.01; the close (C7) written, §26]** **A day later:** the spend from the bills (his Console readings: AWS Cost Explorer for the build days, filtered to
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
  `vercel.json`'s `headers`. *(Resolved 2026-11-07, §24: all five come through unchanged; no `headers` block.)*
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
notes, and its push** (it touches `src/**`, so Deploy builds an image; safe since C1). *(Done the same day: committed
`b9b8ac8` and pushed (his); CI and Deploy green, runs `41916412080` and `41916412096`, checked 2026-11-05. C2 is done.)*

## 19. As built, step 3 (2026-11-05)

Built by Sonnet from `scratch/p15-step3-build-prompt.md`. Code, tests, a deny-list change and one script for him. No AWS
call of any kind (`make check`'s own `terraform init -backend=false` and `validate` aside), no commit, no push.
`docs/phases/evidence/phase-4/raw-manifest.json` was **not** written: it comes from his S3 run. **Reviewed by Opus 2026-11-05 (one fix, below); his run done the same night (below).**

**What was built**

- `src/horizon_compact/site/rawmanifest.py` (new, run code, standard library plus a boto3 client handed in):
  `build_raw_manifest(reader, experiments, bucket, progress=None) -> str`, `write_raw_manifest(text, path) -> Path`,
  `RawManifestRefusal`, the `RawReader` Protocol (`versioning`, `list_versions`, `read`; no write call), `S3RawReader`
  (`get_bucket_versioning`, a paginated `list_object_versions` returning versions and delete markers, and `get_object`
  with `VersionId`, streamed through `iter_chunks`), `ObjectVersion`, `repository_experiments(root)` and
  `account_id(bucket)`. The prefixes are `("official/", "pilot/")` in code; there is no prefix, role or experiment
  argument. The sha256 is taken over the stored bytes chunk by chunk and nothing is decoded; objects are read one at a
  time in key order.
- `src/horizon_compact/cli.py`: `hc site raw-manifest [--bucket] [--profile] [--out]`, a second action in the `site`
  group. `--out` defaults to `docs/phases/evidence/phase-4/raw-manifest.json`. It prints `read N of M objects` to
  stderr every 500 objects (counts only), then four lines: `wrote <path>`, `objects:`, `bytes:`, `groups:`. A refusal
  prints `refused: ...` and returns `REFUSED_EXIT`; an AWS error is caught by the `site` group's existing handler.
- `.claude/settings.json`: `hc site raw-manifest` joins the deny list, in both the `uv run hc` and `uv run --no-sync hc`
  forms, beside the other readers. `tests/test_claude_settings.py` lists it under `READERS`. `hc site data` stays
  runnable. The edit went in directly; no script for him is needed.
- `tests/test_site_rawmanifest.py` (new, 32 tests): see the list below.
- `scratch/p15-step3-s3.sh` (gitignored; his).

**The file.** Schema `horizon-compact/raw-manifest`, `schema_version` 1, key order: `schema`, `schema_version`, `kind`
(`raw-object-manifest`), `hash` (`sha256`), `prefixes`, `versioning`, `object_count`, `total_bytes`, `groups`, `objects`.
`groups` are sorted by prefix, one per sweep (the longest `manifest.json` directory above a key; an awareness sweep is
one level deeper) and one `<role>/<experiment>/` group for keys under no sweep; each has `prefix`, `objects`, `bytes`,
`attempt_objects` (the `attempt-N.json` and probe-call shapes, and an awareness API error under `errors/`, which is
how `recordcheck._read_sweep` counts a call; Opus's review added the `errors/` keys: the number to check against
`record-checks.md`'s `calls` column) and `final_objects`. `objects` are sorted by key, **one per line**, each `key`, `bytes`, `sha256`,
`version_id`, `last_modified` (UTC, seconds, a `Z`). Never written: the bucket name, the account id, any object's
content, any ETag or owner. No timestamp of its own.

**The refusals** (one test each): versioning not `Enabled`; an empty prefix; a delete marker; a second version of a key;
a listed version that is not the latest; a key under an experiment this repository lacks; a key outside
`[A-Za-z0-9._/-]`, ending in `/`, with an empty or dot segment, or too shallow to name an experiment; a read whose byte
count differs from the listing's `Size`; an output holding `arn:`, the bucket name or the account id; a bucket name with
no trailing account id (checked before anything is read); and, in the writer, a file that already holds different bytes.

**The account check, and why it is not C2's.** `site data` refuses on `arn:` or a standalone run of twelve digits. This
file holds thousands of run ids (`r-` and twelve hex digits, all decimal about 0.35 percent of the time) and thousands of
sha256 values (a run of twelve decimal digits in about one in five), so that pattern would refuse almost every real
build (§18 departure 4). This builder looks for exactly what could leak: `arn:`, the bucket name, and the account id
taken from the bucket name's last hyphen-separated part. A test pins both directions: the account id in a key is refused;
a twelve-digit run id (`r-100000000001`) and a digest holding twelve decimal digits are not.

**Departures: what did not fit, and what was done instead**

1. **`build_raw_manifest` takes `bucket` and an optional `progress`** besides `reader` and `experiments`. The prompt said
   the bucket is passed "for this check only" and named a progress line but gave the signature with two arguments.
2. **`repository_experiments` is a local copy of `caseprobe/freeze.py`'s `_experiments`**, which is private to its module.
   Both use `EXPERIMENT_FILES`. Today it returns `company`, `placeholder`, `s4shape` and `shapes`.
3. **`SWEEP_MANIFEST` is imported from `protocol/recordcheck.py`** (public there); **`_FINAL`, `_ATTEMPT` and
   `_PROBE_CALL` are copied**, because they are private. A drift would show in the attempt counts, which the review checks
   against the Phase 4 record checks.
4. **The writer mirrors `write_site_data`** rather than reusing it, so each module raises its own refusal class.
5. **The command's test hook is `cli._raw_s3_client(session)`**, a module-level function the tests replace; no hidden
   argument. The profile is checked before the bucket, as in `site data`.

**Tests.** Build twice, byte-identical; key order at every level; one object per line and the whole parsing; objects
sorted and hashed over bytes, including a body that is not valid UTF-8; the time in UTC with a `Z`; totals and groups by
hand (a pilot sweep, a grid sweep with a session summary, an awareness sweep one level deeper, a loose `repeats.json`);
the digit cases above; nothing of the bodies, the bucket or the listing's extras in the output; the reader making only
the three read calls and one GET per object; progress at 500 and 1,000 of 1,002; every refusal; the writer's no-op, its
refusal and its bytes; the experiment folders; and the command end to end, from the environment, refusing without
writing, and needing a profile and a bucket.

**Cost of his run (an estimate, to be measured).** One GET per object, plus the listing and one versioning call: about
Phase 4 decision 2's 100 MB out, and a few thousand objects (`record-checks.md`: about 2,780 calls across the seven
sweeps, plus finals, manifests and session summaries). Cents at most.

**For the review, what to look at.** (a) The first real run may refuse on something legitimate under `official/` or
`pilot/` that the fixtures do not model: that would be a finding to read, not to code around. (b) If versioning was
turned on after the first objects were written, those objects carry the version id `null`; it is passed to `get_object`
as it is and written as it is. (c) The group totals against `record-checks.md`: `attempt_objects` per sweep should equal
that table's `calls` (the pilots 95 and 94, the awareness sweeps 15 and 15, the grids 1,333 and 1,128, the thinking sweep
100).

**`make check`: green, 3229 tests pass** (3195 before this step); `hc protocol check` ok. Frozen files untouched.

**Opus's review (2026-11-05).** One fix: `attempt_objects` now also counts an awareness API error kept under `errors/`,
as `recordcheck._read_sweep` counts a call (Phase 4's awareness sweeps had none, so its numbers were not affected). A
fixture object and its counts were added. Checked and unchanged: the dev policy allows the three read calls on the
results bucket; versioning has been `Enabled` since the bucket was created, and its policy denies every delete, so a
delete marker cannot exist; every key shape the harness writes passes the key check; case sweeps live under `cases/`,
outside both prefixes. `make check` green, 3229.

**His run (2026-11-05, about 3:05 AM), `scratch/p15-step3-s3.sh`.** Refused nothing. Wrote
`docs/phases/evidence/phase-4/raw-manifest.json`: **5,247 objects, 104,785,272 bytes, 7 groups**, versioning `Enabled`,
no `null` version id, last-modified times from `2026-10-14T00:28:27Z` to `2026-10-15T00:10:39Z` (before the record
checks were made, `00:18:23Z`). The file is 5,313 lines, about 1.4 MB.

| group | objects | `attempt_objects` | `record-checks.md` calls | `final_objects` | runs | the rest |
|---|---|---|---|---|---|---|
| pilot gpt-oss `1f75b653` | 178 | 95 | 95 | 80 | 80 | manifest, `repeats.json`, 1 session |
| pilot haiku `0b9d9e79` | 177 | 94 | 94 | 80 | 80 | manifest, `repeats.json`, 1 session |
| awareness gpt-oss `6a05acef` | 16 | 15 | 15 | 0 | 15 | manifest |
| awareness haiku `0ce6ad12` | 16 | 15 | 15 | 0 | 15 | manifest |
| grid gpt-oss `fe599ad2` | 2,538 | 1,333 | 1,333 | 1,200 | 1,200 | manifest, the refusal-calls file and its meta, 2 sessions |
| grid haiku `0b99fabb` | 2,120 | 1,128 | 1,128 | 990 | 990 | manifest, 1 session |
| thinking haiku `418caa9c` | 202 | 100 | 100 | 100 | 100 | manifest, 1 session |

Every sweep's calls match, every finished run has its final, and the session counts match `record-checks.md`'s
`sessions` column. Every object is accounted for: no key outside these shapes. **Cost:** one listing per prefix, one
versioning call and 5,247 GETs, about 105 MB out (Phase 4 decision 2 estimated about 100 MB): cents, to be confirmed in
the close's spend reading.

**The commit's one snag.** The first `git commit` was stopped by `check-added-large-files` (limit 1,024 KB; the
manifest is 1,431 KB). Its exact path was added to that hook's exclude list in `.pre-commit-config.yaml`, beside the
other generated evidence already allowed past the limit (Phase 3's simulation results, Phase 4's results files). The
limit itself is unchanged.

## 20. As built, C3 (2026-11-05)

Built by Sonnet from `scratch/p15-c3-build-prompt.md`. Code, tests and the `make` and CI wiring. No AWS call, no
`terraform` command other than `make check`'s own, no Vercel command, no commit, no push. The deploy workflow is
untouched (C4). **Review (Opus), his words in `web/src/copy.ts` and his commit are owed.**

**What was built**

- `web/`: `package.json`, `package-lock.json`, `index.html`, `vite.config.ts`, `tsconfig.json`, `.prettierrc`,
  `.prettierignore` (it excludes `src/data/`, so a reformat cannot break DoD 2's byte identity), `public/favicon.svg`
  (mark 1b, golden, light and dark in an internal `<style>`), `scripts/check-dist.mjs`, and `src/`: `main.tsx`,
  `App.tsx`, `copy.ts`, `data.ts`, `styles.css`, `components/` (`Logo`, `Control`, `Chart`, `Tables`, `Provenance`,
  `Footer`) and three test files. Stack: Vite, React and TypeScript, plain CSS custom properties; no CSS framework,
  component library, chart library, animation library, router or state library. `web/src/data/placeholder.json` was
  read and never rewritten.
- `Makefile`: `web-check` (`npm --prefix web run check`) joins `check`; `install` also runs `npm --prefix web ci`.
  `.github/workflows/ci.yml`: `actions/setup-node@v7.1.0` (Node 22, npm cache keyed on `web/package-lock.json`) and
  `npm --prefix web ci`, before `make check`.
- `tests/test_web.py` (4 tests): nothing under `web/src` imports from outside `web/` (static, re-export,
  side-effect and dynamic imports, `new URL`, and CSS `url()`; a fixture proves each shape is seen), and the page's
  twelve statuses equal `sweep/classify.py`'s, in order.
- The check script (`web/scripts/check-dist.mjs`, last step of `npm run check`): JavaScript under 100 KB gzipped in all;
  fonts under 150 KB in all and `.woff2` only; no `<script>` without `src`, no `<style>` element and no `style=`
  attribute in `dist/index.html`; every `src` and `href` in it the favicon or a built asset; no CSS `url()` that is a
  host or a `data:` URI, and no `@import`.
- `web/package.json` scripts: `dev`, `build`, `preview`, `test`, `format`, and `check` = Prettier check, `tsc --noEmit`
  (strict, plus `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes`), Vitest run once, `vite build`, the check
  script. `engines.node` is `>=22.13.0 <23`.

**Pinned versions** (every date re-checked 2026-11-05 with `npm view <pkg> time`; none is younger than 14 days, the
newest being Vite 8.3.5 at 15 days)

| Package | Version | Published |
|---|---|---|
| `vite` | 8.3.5 | 2026-10-21 |
| `react`, `react-dom` | 19.3.1 | 2026-10-14 |
| `typescript` | 7.0.2 | 2026-07-08 |
| `@vitejs/plugin-react` | 6.1.2 | 2026-10-05 |
| `vitest` | 4.1.12 | 2026-10-15 |
| `jsdom` | 29.1.1 | 2026-04-30 |
| `@testing-library/react` | 16.3.3 | 2026-08-27 |
| `@testing-library/dom` | 10.4.2 | 2026-09-13 |
| `axe-core` | 4.14.0 | 2026-10-05 |
| `prettier` | 3.9.10 | 2026-10-10 |
| `@types/react`, `@types/react-dom` | 19.3.0 | 2026-09-09 |
| `@types/node` | 22.20.5 | 2026-10-01 |
| `@fontsource/source-serif-4`, `@fontsource/source-sans-3` | 5.3.1 | 2026-10-11 |
| `@fontsource/big-shoulders-display` | 5.3.0 | 2026-07-19 |

`npm audit` at install: 0 vulnerabilities. Fonts: own `@font-face` rules in `styles.css` pointing at the WOFF2 files
(Source Serif 4 400; Source Sans 3 400 and 600; Big Shoulders Display 800; Latin only; `font-display: swap`);
Fontsource's CSS is not imported, so the build holds four font files and no `.woff`.

**The content security policy, proved in a browser.** `vite.config.ts` puts the section 9 policy, word for word, and
`X-Robots-Tag: noindex` in `preview.headers`; `curl -I` on the preview server shows both on every response. The page
was built, served with `vite preview`, and loaded in the headless Chromium (chrome-headless-shell, build 1234, from
the Playwright cache) at 1280 and 390 pixels wide, light and dark, **driven over the DevTools protocol**, not by the
`--enable-logging` flags: a listener installed before the page's scripts recorded every `securitypolicyviolation`
event, and the console, log and network events were collected. Result, all four combinations: **zero policy
violations, zero errors, zero failed requests**; every request went to the page's own origin (the document, one
script, one stylesheet, four WOFF2 files); all four font faces report `loaded`. **A negative control confirmed the
probe sees what it should:** adding a `<style>` element and a `style` attribute by script on the same page gave
`style-src-elem inline` and `style-src-attr inline` and the matching console messages. Dark mode was set with the
protocol's emulated `prefers-color-scheme` media feature, which worked (the body background read `rgb(15, 21, 32)`);
`--force-dark-mode` was not tried. React `style={{...}}` objects (dot positions, tooltip position, the control's bar)
trip nothing, as expected.

**The color tokens**, Ink and paper only, both modes by `prefers-color-scheme` (no toggle, no `data-theme`),
`--sun` `#e9a23b` light and `#f4c04f` dark. The dataviz validator on the one series hue against its surface, run
2026-11-05 (`node validate_palette.js "<hex>" --mode <mode> --surface "<surface>"`):

```
paper light, series #2a6fc9 on #f6f2e9  [PASS] Lightness band (L 0.43-0.77)  [PASS] Chroma floor (>= 0.1)
  [PASS] CVD separation n/a  [PASS] Normal-vision floor n/a  [PASS] Contrast vs surface (>= 3:1)  ALL CHECKS PASS
paper dark,  series #4b8fe6 on #0f1520  [PASS] Lightness band (L 0.48-0.67)  [PASS] Chroma floor (>= 0.1)
  [PASS] CVD separation n/a  [PASS] Normal-vision floor n/a  [PASS] Contrast vs surface (>= 3:1)  ALL CHECKS PASS
```

Contrast against the surface, computed with the WCAG formula: light, ink 15.59, ink2 7.91, accent 10.18, series 4.46,
muted 3.41, sun 1.94, axis 1.74, grid 1.23; dark, ink 14.97, ink2 9.06, accent 11.51, series 5.55, muted 4.98, sun
10.88, axis 1.59, grid 1.18. All text is ink or ink2 (at least 4.5 to 1); the marks that carry data (series, muted for
the cap) are at least 3 to 1. **Two honest notes:** the sun on the light surface is 1.94 to 1, below 3 to 1; the logo
is decoration (`aria-hidden`, the `h1` names the page) and the ink horizon bar carries its shape, as section 7.3
recorded, but it is a real number. The grid and axis hairlines are deliberately recessive (section 7.1). The earlier
six-token run is `scratch/previews/identities-validator.txt`.

**Measured sizes** (`node web/scripts/check-dist.mjs`, after `vite build`): JavaScript, gzipped, in all **75,362 bytes
(73.6 KB)**, budget 100 KB; fonts, 4 files, **66,008 bytes (64.5 KB)**, budget 150 KB, WOFF2 only; 8 files in `dist/`;
`dist/index.html` holds one `<script type="module" src>` and one stylesheet link, nothing inline.

**Tests and `make check`.** Python: **3233 passed** (3229 before this step, plus the 4 above). Vitest: **29 tests, 28
pass and 1 fails by design, `his words are written`** (`src/copy.test.ts`), which fails while any of `lede`, `notice`,
`resultsTitle` or `resultsSentence` still begins with `[his:`. Every other check in `make check` passed:
`ruff`, `mypy`, `root-check` (14 of 16), `paths-check`, `dossier-check`, `scenarios-check`, `hc protocol check` ("ok"),
`tf-check`, Prettier, `tsc`, the production build, and the check script; `make doctor` passed on its own. `make check`
as a whole exits non-zero until he writes his words, and the run stops at `web-check`, which is the last step, so
`doctor` was run by hand. Vitest covers: axe (no violations on the page, and with a priority chosen and a run
traced; the color-contrast rule is off there because jsdom has no layout, so contrast rests on the validator above);
tracing (pointing marks exactly 7 dots and 1 table row, focus does the same, Escape and leaving the panel clear, the
tooltip's order); the control (one panel chosen, 3 rows in, `aria-pressed`); the keyboard (one tab stop per panel,
the four arrows, clamped inside the panel, the tooltip follows focus); every amount for every run and line as text in
the run table; the data check throwing on a wrong `schema`, `schema_version`, `kind`, `content`, `sweep.role` or
`sweep.experiment`, and on a shape the page cannot draw; the display helpers; and the copy file.

**Screenshots** are in `scratch/c3-shots/` (gitignored): `preview-{1280,390}-{light,dark}.png` (the production build
under the policy), the same with `-traced` (the "Fragrance" priority chosen and one dot pointed at), `dev-*` (the
dev server), and `clipA-*` and `clipB-*` (phone-width crops). Compared with `scratch/previews/shots/heads-sans-*.png`:
the header, the type, the logo, the chart, the footer and the dimmed-panel and traced states match. Page height is
about 4,200 px at 1280 and 6,400 px at 390.

**Departures: what did not fit, and what was done instead**

1. **jsdom is 29.1.1, not §2's 30.1.3.** jsdom 30.1.x and three of its dependencies declare `node ^22.22.2 || ...`,
   and his installed Node is 22.20.0 (npm printed `EBADENGINE`). 29.1.1 supports `^22.13.0`; `engines` says so.
2. **`@vitejs/plugin-react` is 6.1.2, not 6.2.1** (6.2.1 was published 2026-11-02, inside the 14 days). Its peer
   range accepts Vite 8.
3. **Dot offsets are by position, not by `repeat` value.** The preview computed `top = 50 + (repeat - 2) * 22`
   percent, which assumes repeats start at 1; the data's repeats are 0, 1 and 2, so the preview's dots sat in the
   upper half of each row. The page uses `50 + (index - (n - 1) / 2) * 22` over the run's position among its panel's
   runs sorted by repeat: 28, 50 and 72 percent, centered, still fixed and not jitter.
4. **Not carried from the preview:** the body's background-and-color transition (it moves only when the operating
   system changes scheme, and the prompt lists the transitions). **Added:** the control's bar is placed, not animated,
   on load, on a resize or wrap, and when the fonts arrive (it animates only on a choice), so nothing moves on load;
   it follows its container with a `ResizeObserver`, not a window `resize` listener (the first version left the bar
   stranded in a screenshot taken at 390 px when the layout changed; found by looking at the screenshot).
5. **A scroll clears a pointer's trace but not a focused dot's.** A keyboard user's arrow keys scroll the page by
   themselves, which would clear the trace at once, so a focused dot keeps its trace and the tooltip is repositioned.
   Leaving the panel, Escape and a blur out of the panel clear either kind.
6. **The tooltip is `aria-hidden`.** The preview's `role="status"` live region would repeat what each dot's
   `aria-label` already says on focus (amount, line, run, status).
7. **Added for accessibility:** each table frame is a keyboard-focusable `role="region"` with a label (a scrollable
   region must be reachable by keyboard), the provenance list uses a `div` per term and description, and each panel's
   two groups sit in a `.kind` wrapper.
8. **The boundary check and the status-list check are in Python** (`tests/test_web.py`), as the prompt allowed, so
   they run in `make check` without Node.
9. **No preload of fonts by hand** (the prompt allowed leaving it out), `assetsInlineLimit` 0 and the module preload
   polyfill off, so nothing is inlined as a `data:` URI. **No meta description** is rendered while `his.description` is
   empty; when it is not, the page renders a `<meta>` in the tree and React 19 hoists it into the head (not exercised,
   since the value is empty).
10. **`ci.yml`'s pin style.** The prompt named `actions/setup-node@v7.1.0` and that exact tag is used (the release
    exists, published 2026-10-08, checked with `gh`); the file's other steps use a mix of floating major tags and exact
    tags, so this one sits with the exact ones.
11. **Not run:** `git commit` hooks (the name guard's scan of `web/package-lock.json` happens at his commit; if it
    refuses, the class of term is reported, never the term, and he adds an `allow:` line, per section 3 finding 7).

**Labels as drafted** (Claude-drafted; he approves each word for word; the source is the `labels` object in
`web/src/copy.ts`). His rule applied (joined facts, no runs of short same-length sentences, no "not X, it's Y", no
reflexive threes, no colon reveals, no tidy closers).

- Chart: title "Amounts by line, three runs per priority"; key "Each dot is one run, the solid tick marks the mean of the
  three, and the thin mark at the end of each line is its cap; point at a dot to follow that run through every line."
  (heads-sans.html's joined sentence); control "Priority", "All five"; priorities "Color", "Fragrance", "Low water use",
  "Butterflies", "No priority set"; group headings "Sources", "Uses"; panel line "n = 3 runs; open day: spring 2,
  autumn 1; test run, placeholder content"; tooltip: the amount, the line, then "<run id>, <status>"; each dot's
  accessible label "$800, Spring plant-sale proceeds, run r-..., valid".
- First attempt and final: title "First attempt and final"; key **(redrafted)** "Each priority shows how its runs
  ended on the first attempt and on the final one, with any status that never occurred counted as zero." (was "How
  each run's call ended, on its first attempt and on its final one, by priority. A status that never happened is
  shown as zero."); headings "Status", "Runs", "first", "final"; region label "First attempt and final status counts,
  by priority".
- Every run: title "Every run"; key **(redrafted)** "Each dot in the chart above has its own row here, one row per
  run." (was "One row per run: each dot in the chart above is a row here."); region label "Every run, one row each";
  columns "Run", "Priority", "Status", "Attempts", the seven line labels from the data, "Open day", "Image".
- Provenance: title "Provenance"; terms "Sweep", "Model, as served", "Image digest", "Code", "Content hash", "Runner",
  "Started", "Finished", "Runs" ("15 of 15 finished"), "Measured cost"; times end "UTC"; **the two notes are now one
  joined sentence (redrafted)**: "The records are kept write-once in S3 under development/placeholder/<sweep id>/, and
  the image this digest names is no longer held in the registry, because an older rule there kept only the ten
  newest." (the reason is section 3 finding 1 and section 17's ECR rule).
- Footer, his: "© 2026 sjtroxel", the GitHub mark (link, new tab, "GitHub, Horizon Compact (opens in a new tab)"), ". All
  rights reserved."
- His to write, placeholders now: `lede`, `notice`, `resultsTitle`, `resultsSentence`, and `description` (empty, so no
  meta tag). They render in the secondary ink, upright.

**For the review, what to look at.** (a) Departure 3, the centered dots (a visible change from the approved preview, for
a reason in the data). (b) Departures 4 and 5, the two interaction changes. (c) The sun's 1.94 to 1 on light. (d) Whether
the page should carry `his.description` at all. (e) The first CI run of `setup-node` and `npm ci` with the lock file
(not run here). The push touches `web/**`, `ci.yml`, `Makefile`, `tests/` and docs, so CI runs and Deploy does not.

**Review (Opus, 2026-11-05, about 10:45 AM). No code change.** Read every file against the build prompt and §7, §7.3,
§8 and §9. Re-run here: `npm run check` (28 of 29 Vitest pass, the one failure the by-design `his words are written`),
then `vite build` and the check script by hand (75,362 bytes of JavaScript gzipped, 66,008 bytes of fonts, ok),
`tests/test_web.py` (4 passed), `hc protocol check` (ok). **The name guard's own scanner, run over the 28 files this
commit adds or changes (counts only, no term printed): 0 findings**, so §3 finding 7's collision did not happen.
Checked live: the six key packages' publish dates and the `actions/setup-node` `v7.1.0` release (2026-10-08) match the
table above. The provenance block's facts hold: the prefix is `sweep_prefix`'s `role/experiment/sweep_id/`, write-once
is the bucket policy and `IfNoneMatch`, the skeleton image `ef2582ed...` was measured gone (§3 finding 1), and the
linked commit `8ab367c` is on `origin/main`. Departures 1 to 11 accepted; departure 3 (centered dots) is right, the
preview's dots sat high. The Right arrow wrapping to the next line at a line's end is the preview's behavior, kept.
The sun's 1.94 to 1 on light stays: a logo is exempt from the non-text contrast rule and the ink bar carries the shape.
`his.description` stays empty until Phase 6.5's go-live (the page is `noindex` until then).

**Labels: three redrafts proposed, his choice.** (1) The run table's key says "Each dot ... has its own row", which is
false: a run is seven dots and one row. (2) The provenance note joins two unrelated facts with "and"; two sentences of
different lengths read more naturally than one forced join. (3) The status key says "Each priority shows", where the
table shows them by priority. **CI goes red until his words are in `copy.ts`, so the push waits for them.**

**His approval and the words (2026-11-05, about 3:15 PM).** He approved the three label redrafts as proposed; they
are in `labels`. **The four `his` values are Claude-drafted at his request** ("draft for me ... since I don't know what
you mean for me to write"), and **approved by him as written**, after one revision: the notice now says why the test
runs are a garden club (a stand-in with the decision's shape and none of its subject, Phase 1 decision 2), after he
asked why. Checked while drafting: "AI models", plural (the runs used more than one); "planned before the experiment
ran", not "before any result existed" (official results exist in the repo; `planning/04` §1.2 is dated 2026-10-03);
the title is first person because the section holds results against his own view (`04` §1.2, principle 1). The lede
explains "compact" by its meaning rather than by the Mayflower and UN Global Compact references `planning/06` §6.4
asks for; he accepted that. `description` stays empty until go-live.

**One test fix (Opus), found by writing the words:** "shows his placeholders in the placeholder class" asserted at
least four placeholders, so it would fail the moment the words were written; my review missed it. It now holds each of
the four values' placeholder class equal to whether it is still a placeholder, in either state. **`make check` green:
Python 3233 passed, Vitest 29 of 29, `hc protocol check` ok, check-dist ok (JavaScript 75,702 bytes gzipped, fonts
66,008), doctor ok.** The name guard's scanner over the 28 files: 0 findings.

**At the handoff (2026-11-05, about 3:30 PM).** The remaining drafted labels (chart title and key, table headings,
provenance terms; the list above) have **no explicit word-for-word approval yet**: asked, unanswered at the close, so
owed before C4 makes the page public. `copy.ts`'s comment says so. Stale "fails until he writes" comments in the
`Makefile` and `copy.test.ts` reworded. `make check` re-run green after: Python 3233, Vitest 29 of 29, check-dist ok,
doctor ok; the guard's scanner, 29 files, 0 findings.

**Committed (2026-11-05, his).** `ea2bb7d` `phase 1.5: c3 the page`, pushed; CI green (run `42112962435`, about
3:28 PM CST). Deploy did not run, as expected (it does not watch `web/**` until C4). The name guard passed at his
commit, so `web/package-lock.json` raised no collision (§3 finding 7). Docs brought current 2026-11-06, about
9:05 AM.

**The remaining labels approved (2026-11-06, about 9:07 AM, his).** Every drafted label in the list above is
approved word for word, with one change: the chart key's "the solid tick marks the mean" is now "the solid tick
shows the mean" (Claude's suggestion; "tick marks" read as a noun). Claude also flagged the panel line's "n =" as
statistics shorthand; **he kept it** (most readers have met it in a statistics class). The provenance terms ("Image
digest", "Content hash", "Runner") were noted as technical and kept, as suited to that block. Every word the page
shows is now approved; nothing in `copy.ts` blocks C4.

## 21. As built, C4 (2026-11-06)

Built by Opus in session (his call, "go ahead and do C4"), from §9, §10 and §12 step 6; no separate build prompt.
Code, tests and docs only: no AWS call, no `terraform plan` or `apply` against AWS, no commit, no push, no dispatch.
**His `bootstrap` apply, his two repository variables, his commit and push, and Claude's read of the Deploy log are
owed, in that order** (below).

**What was built**

- `infra/terraform/main/site.tf` (new), as §9: the bucket `horizon-compact-site-<account-id>` (computed,
  `force_destroy = true`, all four public access blocks); the origin access control and the response headers policy
  read as **data sources by id** from two new variables, so a wrong id fails the plan rather than the page; the
  managed `Managed-CachingOptimized` policy by name; the distribution (`redirect-to-https`, GET and HEAD, compression,
  `PriceClass_100`, the default certificate, `wait_for_deployment = false`, 403 and 404 served as `/index.html` with
  200, comment `horizon-compact site`, no aliases); the bucket policy, `s3:GetObject` to `cloudfront.amazonaws.com`
  only where `AWS:SourceArn` is this distribution. Tags come from the provider's `default_tags`.
- `variables.tf`: `site_origin_access_control_id` and `site_response_headers_policy_id`, no default, each with a shape
  check. `outputs.tf`: `site_bucket` (sensitive), `site_distribution_id` and `site_domain` (not sensitive; neither holds
  the account id).
- `.github/workflows/deploy.yml`: `web/**` in the paths; a **`changes` job** (plain `git diff --name-only` over the
  push's range; a results path matches first and sets nothing; `src`, `experiment`, `pyproject.toml`, `uv.lock` set
  `code`; `infra/**` and `deploy.yml` set both; `web/**` sets `site`; a dispatch or an unknown base sets both); the
  `image` job runs only when `code` is set, so a page-only push builds no image and applies nothing; the plan passes
  the two ids from the repository variables `SITE_ORIGIN_ACCESS_CONTROL_ID` and `SITE_RESPONSE_HEADERS_POLICY_ID`;
  a **`site` job** after `infra`, or alone when `image` and `infra` were skipped, and never after a failure:
  `npm ci`, `npm run check` (which ends with the build and the built-files check), init, then `assets/` synced with a
  year's immutable cache and everything else with `no-cache` (the favicon is not content-hashed, so it is not
  immutable), `--delete` on both, an invalidation of `/*`, and the smoke test against the `*.cloudfront.net` domain
  only (retried for about six minutes): `index.html` names this build's script; the content security policy,
  `X-Robots-Tag: noindex`, `nosniff`, Strict-Transport-Security and `no-referrer` headers are served; the script is
  served as JavaScript and the stylesheet as CSS (`nosniff` would make a browser refuse either otherwise); the bundle
  names the sweep id from `web/src/data/placeholder.json`.
- `.github/workflows/teardown.yml` (new), as §10 steps 2 and 3: dispatch only, runs only when the input is `destroy
  main`, in Deploy's concurrency group and never cancelled; `terraform destroy` on `main` with a zero digest; then the
  tag listing for `Project = horizon-compact` and `Root = main`, retried for about ten minutes, which must hold nothing
  but task definitions; no `ACTIVE` `horizon-compact-sweep` task definition (an access error does not pass as
  absent); no `ACTIVE` cluster named `horizon-compact`; no distribution with this project's comment.
- `.github/workflows/aws-permission-check.yml`: two attempts on another project's distribution (the first listed
  without this project's comment), each of which must be refused with an access error: **delete it with a stale
  ETag**, and **claim it by tag** (`Project = horizon-compact`, plus a second tag whose value is over CloudFront's
  256-character limit). Neither call could change the distribution if the fence were missing.
- `infra/iam/deploy-site.json`: one Deny, **`NeverRetagAnotherProjectsDistribution`** (the finding below). This file is
  `bootstrap`'s, so it lands only with his apply.
- `tests/test_architecture.py`: 15 tests added, 3 changed (the site grants' statement list, the deploy paths, the
  permission check's six attempts). `make check` green: **Python 3248 passed** (3233 before), Vitest 29 of 29, check-dist
  ok, `hc protocol check` ok, doctor ok.

**Finding: the deploy role could take over another project's distribution (bootstrap, from C1).** Checked against
AWS's service reference for CloudFront (read 2026-11-06): `TagResource` accepts `aws:RequestTag`, and C1's
`SiteDistributionCreate` allows `cloudfront:TagResource` on `*` when the request sets `Project = horizon-compact`.
So the role could tag Musical Mycelium's distribution (tagged `Project = musical-mycelium` by its provider's
`default_tags`) as this project's, and `SiteDistributionManage` would then let it update or delete it. Decision 5's
intent was that it never could. `deploy.json` already guards EC2 the same way (`NeverRetagUntaggedNetwork`); the
CloudFront statements had no equivalent. **Fix:** a Deny on `TagResource` and `UntagResource` where the resource
already has a `Project` tag that is not this project's. The `Null` guard leaves a resource with no `Project` tag alone,
because a distribution being created may be evaluated with none, and a stronger deny could block the create.
**Remaining:** an untagged distribution in the account could still be claimed; this account's known distributions are
Musical Mycelium's (tagged) and this one. KNOWN-GAPS OPEN 2026-11-06. The C1 review missed it.

**Departures**

1. **The permission check deletes rather than updates** (§9 named `UpdateDistribution` with a stale `If-Match`). An
   update needs a full distribution config in the request, and the role cannot read another project's
   (`GetDistributionConfig` is tag-fenced). `DeleteDistribution` takes only the id and the ETag, and is fenced by the
   same statement. A second attempt, the tag claim, covers the finding above.
2. **The two ids are read as data sources**, not passed straight into the distribution, so the grants C1 gave
   (`GetOriginAccessControl`, `GetResponseHeadersPolicy`) are used and a wrong variable fails the plan.
3. **Deploy's `check` job gains Node and `npm ci`.** C3 put `web-check` into `make check`, and Deploy's `check` job had
   no Node, so the first Deploy after C3 would have failed there. C3's push ran CI only, so nothing turned red.
4. **`infra/**` sets both halves**, not only `code`: an apply can replace the distribution, and a new distribution
   serves nothing until a sync.

**His steps, in order** (each with the output to look for):

1. **`bootstrap` apply with the dev key** (the deny). Expected plan: **1 to change** (`aws_iam_role_policy.github_deploy_site`,
   updated in place), 0 to add, 0 to destroy. Then a second plan: "No changes".
2. **The two repository variables**, from §17's recorded outputs: `SITE_ORIGIN_ACCESS_CONTROL_ID` and
   `SITE_RESPONSE_HEADERS_POLICY_ID`. Without them the plan fails its variable checks: a red Deploy, nothing changed.
3. **His commit and push.** It touches `infra/**` and `deploy.yml`, so Deploy runs every job: `check`, an image, the
   apply (expected: the bucket, its public access block, its policy and the distribution added, and the task
   definition replaced as on every image-building deploy), then `site`.
4. **Claude reads the Deploy log.** Each missing permission is added by name, scoped, with the error recorded (§12
   step 6). Then §12 step 7, the permission check, his dispatch.

**Step 1 done (2026-11-06, about 9:28 AM, his).** His plan (`scratch/p15-c4-plan.sh`): **0 to add, 1 to change, 0 to
destroy**, the one change `aws_iam_role_policy.github_deploy_site` gaining exactly the Deny above, the other five
statements unchanged. His apply: "Apply complete! Resources: 0 added, 1 changed, 0 destroyed." His second plan: "No
changes." The outputs printed `site_origin_access_control_id = E1L3LEZALRKH6Y` and `site_response_headers_policy_id =
e75c6c69-6030-4efb-ba96-014e5a493e08`, the values §17 recorded.

**Step 2 done (2026-11-06, about 9:30 AM, his).** `gh variable set` for both: "Created variable
SITE_ORIGIN_ACCESS_CONTROL_ID" and "Created variable SITE_RESPONSE_HEADERS_POLICY_ID", each with those values.

**Step 3 done (2026-11-06, about 9:34 AM, his).** Commit `69b88ce` `phase 1.5: c4 the site in main, labels approved`
(every hook passed, the name guard on paths, content and message included), pushed. **CI run `42244341282` passed.
Deploy run `42244341172` passed, every job, on the first attempt.** Read by Claude:

- `what changed`: `code=true site=true` (the push touched `infra/**` and `deploy.yml`).
- The image `sha256:0482bac0...`; the apply's plan **"5 to add, 0 to change, 1 to destroy"** (the distribution, the
  site bucket, its policy and its public access block created; the task definition replaced to name the new image, as
  on every image-building deploy), then "Apply complete! Resources: 5 added, 0 changed, 1 destroyed." **No access
  error anywhere in the log**, so the create met `aws:RequestTag/Project` with the provider's `default_tags` (§15's
  question answered) and no permission had to be added.
- The distribution `E2I9ASU9R5GM22`, domain `d17t61og2l6kuo.cloudfront.net`. The sync uploaded seven files under
  `assets/` and `index.html` and `favicon.svg` beside them; one invalidation of `/*`.
- The smoke test: the new script `index-Dk1RsRTF.js` served on attempt 7 (about a minute, a new distribution's name
  resolving); every header served; the script and stylesheet with their types; the bundle names
  `skeleton-haiku-5-5-f1467906`. "The site serves this build, with its headers."
- No 12-digit account id in the public log (the only 12-digit strings are fragments of image layer hashes).
- Claude's own `curl -I` of the domain afterwards: `HTTP/2 200`, `cache-control: no-cache` on `index.html`, the
  content security policy word for word as §9, `max-age=63072000; includeSubDomains`, `nosniff`, `no-referrer`,
  `x-robots-tag: noindex`.
- Annotations only: GitHub's notice that `ubuntu-latest` moves to Ubuntu 26 from 2026-10-19. Not acted on here.

**Step 7 done (2026-11-06, about 9:43 AM): the permission check.** His dispatch; run `42245451195` passed, read by
Claude: **"All six forbidden actions were refused."** Each with an access error: create a role without the boundary
and create a bucket outside the project (no policy allows them), put an inline policy on its own role and run a task
(explicit deny in `horizon-compact-deploy`), **delete another project's distribution** (no policy allows
`DeleteDistribution` on it: the tag fence), and **claim another project's distribution by tag**, refused "with an
explicit deny in an identity-based policy": the new `NeverRetagAnotherProjectsDistribution`, evaluated before the
over-long tag value was ever read. The distribution tested was the one other distribution listed (Musical
Mycelium's); nothing about it changed. Account ids appear only as `<account-id>`. **DoD 8 proved.** The KNOWN-GAPS
entry of 2026-11-06 is closed.

**Next: §12 step 8, the review against §8** on `d17t61og2l6kuo.cloudfront.net`, at 1280 and 390 pixels, light and
dark (his, Claude reading); fixes before C5. *(Done 2026-11-06: the review is §22, its fixes §23 and §23a.)*

## 22. The review against §8 (2026-11-06, §12 step 8)

Claude's screenshots of the live page on `d17t61og2l6kuo.cloudfront.net` (headless Chromium, 1280 and 390 pixels,
light and dark), and a script driving the live page over the DevTools protocol: hover, the keyboard path, the
priority control, reduced motion, the console and every request's host. He reviewed the screenshots. Headless
Chromium only: not Safari or Firefox, not a real phone. axe, the asset budget and the contrast validator were not
re-run here; they run in `make check` and `npm run check`.

**Passes.** No template residue (the title is the name, the favicon is his). No decoration without a job, no filler
word (a sweep of the rendered text for §8's list and `planning/06`'s found none). Hierarchy by space and type. Every
panel has its run count, the axis starts at $0, spread is drawn. A dot's hit area is 24 by 24 pixels; hovering a dot
lights its run's seven dots and its row in the run table, the tooltip giving the amount first. Tab gives one stop per
panel, the arrow keys move between its dots with the same tooltip, Escape clears, the focus ring is a 2px solid
outline. The priority control dims the other panels and sets `aria-pressed`. Under `prefers-reduced-motion` every
transition is 0s. No console message, no request to any host but the page's own. A faint dark-mode tooltip in one
capture was the capture (computed opacity 1, a plain viewport capture solid).

**Misses, to fix before C5:**

1. **On a phone, choosing a priority leaves its panel off screen.** In one column, choosing Fragrance dims Color and
   Fragrance stays below the fold ("No priority set" is four panels down). Fix: bring the chosen panel into view, with
   no smooth scroll under reduced motion.
2. **The status table's first column scrolls away on a phone.** Only the run table's first column is fixed, so
   scrolling to Butterflies loses the status names. Fix: fix that column too.
3. **At 1280 the run table hides its last five columns** (the seeds line onward) behind a sideways scroll, and an
   overlay scrollbar (macOS) gives no sign of them. §7.1 planned that scroll for phone width only. **Measured on the
   live page:** the table is 1,454px wide at every desktop width, its frame 944px (the text column); with its line
   headings allowed to wrap, its narrowest is 1,022px (without the Image column, 916px). **His decision (2026-11-06,
   about 4:37 PM, "avoid unnecessary scroll", as recommended):** the line headings wrap, and on wide screens the
   table's frame keeps its left edge on the text column and extends right to the page's right margin, so it scrolls
   at no width from about 1,180px up (1280, 1440, 1920 included); at 1024 a small scroll remains, and at phone width
   the scroll §7.1 planned. The Image column stays (§7 item 6). *(Dated note, 2026-11-06, the review of the fixes: as built, with only the
   seven line headings wrapping, the point is about 1,200px, not 1,180; 10px of scroll at 1,180. Accepted by him;
   §23a.)*
4. **The chosen priority's label turns semibold and pushes the labels after it** about 3 pixels ("Color" measured
   moving from x 240 to 237). Fix: reserve the semibold width so nothing moves.
5. **A cold load shows the fallback faces first** (`font-display: swap`, no preload): the first capture caught the
   name on two lines, and the first screen reflows when the fonts arrive. Fix: preload the name's face and the prose
   face.

**Departures from the doc's letter, accepted (a dated note, no fix):**

6. The status table also scrolls sideways at phone width (§7.1 names only the run table). It sits in its own labelled,
   focusable frame and never moves the page.
7. The status counts are centered under their "first" and "final" headings, not right-aligned (§8). Every count is a
   single digit.
8. The dimmed panels sit at opacity 0.22, the run table's dimmed rows at 0.35. **Raised to 0.35 with the fixes**
   (his acceptance of the recommendations, 2026-11-06), so a dimmed panel stays legible.

**His type change (2026-11-06, about 4:30 PM): the prose face becomes Newsreader, and the opening paragraph smaller.**
He found the lede too large between the name and the notice (22px against the notice's 17px) and was not keen on
Source Serif 4. From previews of five faces and then four sizes (`scratchpad` only, not tracked), he chose
**Newsreader with the lede at 20px and body prose at 18px as served by Google Fonts' variable font**, whose optical
sizes set it tighter at those sizes. **Self-hosted, that look is set with the static file at 19px and 17px:**
`@fontsource/newsreader` 5.3.0 (published 2026-07-19, OFL-1.1, checked live), `newsreader-latin-400-normal.woff2`,
22,480 bytes, a single cut for text sizes that sets wider than the variable font, so one step smaller matches it (his
comparison of the three, side by side). He took that over the variable file (`@fontsource-variable/newsreader`,
132,000 bytes for the Latin optical-size file, which would take the fonts to about 178 KB, past §8's 150 KB) and over
a trimmed variable file (a font-processing step and a generated file in the repository). **So the CSS reads 19px and
17px on purpose; do not "correct" them to 20 and 18.** Fonts go from 66,008 bytes to 68,400 (Source Serif 4's 20,088
out). §7.3's type amended by a dated note.

**Next:** the five fixes, item 8 and the type change are built (Sonnet, a fresh session, from
`scratch/p15-review-fixes-build-prompt.md`), Opus reviews, the page is
captured again at both widths and modes, and his commit carries them with today's docs. Then C5. *(Dated note, 2026-11-06,
about 5:20 PM: built and reviewed, §23 and §23a; the "after" captures stand, §23a says why. His commit owed, then
C5.)*

## 23. As built, the §8 review fixes (2026-11-06)

Built by Sonnet in a fresh session from `scratch/p15-review-fixes-build-prompt.md`; Opus reviews; he commits. No AWS
call, no `terraform` command other than `make check`'s own, no Vercel command. `web/src/copy.ts`, the data file and
everything outside `web/` and this doc are untouched; `hc protocol check` prints ok.

**What was built, per item.**

1. **A chosen priority's panel is brought into view.** `Chart` keeps a ref to the chosen panel (set only on that
   panel) and an effect on `chosen`: not for "All five"; if the panel's rectangle is not fully inside the viewport,
   `scrollIntoView({ block: "start", behavior })`, `"smooth"`, or `"auto"` under `prefers-reduced-motion: reduce`;
   `.panel` has `scroll-margin-top: 1rem`. `scrollIntoView` and `matchMedia` are called defensively (jsdom has neither).
2. **The status table's first column is sticky:** the first header cell (it spans both header rows, so it is the only
   header cell in column 0) and each row's name, surface background, `left: 0`. The same rule now also fixes the run
   table's first header cell (see the departures).
3. **The run table stops hiding columns on desktop.** The seven line headings carry `th.amt` (wrap, right-aligned,
   bottom-aligned); every body cell stays on one line. The run table's frame carries `.wide`, with `margin-right:
   calc(-1 * max(0px, (100vw - 64rem) / 2))`, so it keeps its left edge on the text column and runs to the right
   margin. Nothing else widens.
4. **The control no longer shifts.** Each button has `data-label`, and `.control button::after` holds a hidden
   semibold copy of the label (`content: attr(data-label) / ""`, `height: 0`, `overflow: hidden`, `visibility:
   hidden`, `font-weight: 600`), so the button is always as wide as its semibold self.
5. **The two first-screen fonts are preloaded.** `preloadFonts()` in `web/vite.config.ts` finds the emitted Big
   Shoulders Display 800 and Newsreader 400 files in the bundle and adds a `<link rel="preload" as="font"
   type="font/woff2" crossorigin>` for each (it throws if either pattern matches other than once, and does nothing on
   the dev server). `web/scripts/check-dist.mjs` now requires exactly those two preloads, each `as="font"`, each
   `type="font/woff2"`, each with `crossorigin`, each naming a file that exists in `dist/assets/`. Tried against
   three broken copies of `index.html` (no `crossorigin`, one preload missing, one naming a missing file): each fails
   with its own message; the good build passes.
6. **His type change.** `@fontsource/newsreader` pinned at exactly `5.3.0`; `@fontsource/source-serif-4` removed from
   `package.json` and the lock. Checked live against the npm registry today: version 5.3.0, license OFL-1.1, published
   2026-07-19 (110 days, past the 14-day rule), and the `latest` tag. The serif `@font-face` points at
   `newsreader-latin-400-normal.woff2` (22,480 bytes), no Fontsource CSS import; `--serif` starts with "Newsreader".
   The lede is `1.1875rem` (19px), body prose stays `--s0` (17px); a CSS comment citing §22 says why, so nobody
   corrects them to 20 and 18. The comment at the top of `styles.css` is updated.
7. **Dimmed panels:** `.panels.focus .panel:not(.chosen)` is 0.35, as the run table's dimmed rows.

**Browser proof.** Headless Chromium (chrome-headless-shell 1234) driven over the DevTools protocol against `npm run
preview`, the production build under the served content security policy, on localhost. Classic scrollbars on for every
measurement (15px, measured: `innerWidth - clientWidth`); `--hide-scrollbars` only for the screenshots. Scripts are in
the session's scratchpad, not the repository. Chromium only: not Safari, not Firefox, not a phone.

- **Item 1.** At 390 x 844, choosing "No priority set" leaves the panel's top at 16px and its heading at 16-35px: inside
  the viewport (before the fix it was four panels down). The scroll is smooth: after 120ms `scrollY` was 842 of a final
  3,599; under reduced motion it was 3,599 at 120ms. A panel already fully in view (Color, top 120px, bottom 677px)
  did not move the page (`scrollY` 1,043 before and after), and "All five" did not either.
- **Item 2.** At 390, with the status frame scrolled fully right (328px of scroll), the status column's 14 cells (the
  header cell and 13 rows) all stay at x = 16, as before the scroll. The run table, scrolled fully right (689px), keeps
  its first column at x = 16 too.
- **Item 3.** Frame and page, by viewport width:

  | width | page scrolls sideways? | frame's width | table's width | frame's overflow | right gutter |
  |---|---|---|---|---|---|
  | 320 | no (305 of 305) | 273 | 1,032 | 759 | 16 |
  | 390 | no | 343 | 1,032 | 689 | 16 |
  | 768 | no | 673 | 1,032 | 359 | 40 |
  | 1024 | no | 929 | 1,032 | **103** | 40 |
  | 1180 | no | 1,022 | 1,032 | **10** | 33 |
  | 1280 | no | 1,072 | 1,072 | 0 | 33 |
  | 1440 | no | 1,152 | 1,152 | 0 | 33 |
  | 1920 | no | 1,392 | 1,392 | 0 | 33 |

  "Right gutter" is the distance from the frame's right edge to the page's right edge, inside the scrollbar. With a
  classic 15px scrollbar the 2.5rem gutter (40px) absorbs the 7.5px `100vw` overstates, and it is 33px; the frame
  never passes the margin, and the page never scrolls sideways. With an overlay scrollbar (macOS, a phone) there is
  nothing to absorb and the gutter is the full 40px; that case was not measured. The first column stays sticky;
  tracing lights and dims rows (the Vitest tests for it pass, and a traced run is in the screenshots).
- **Item 4.** For each of the six choices, every button's left edge and width are identical to the 0.5px bound: the
  largest difference is 0px ("All five" 160.5/48, Color 232.5/39, Fragrance 295.5/75, Low water use 394.5/105,
  Butterflies 523.5/76, No priority set 623.5/101). With the `::after` rule switched off the buttons do move (Color
  232.5 to 229.5, the review's 3px), so the 0 is the rule's doing. The bar sits under the chosen button (left and width
  equal). The accessible names in Chromium's accessibility tree are the six labels, undoubled, with the alt-text form
  and with plain `content: attr(data-label)` alike. axe reports nothing in the Vitest suite (it cannot see pseudo-element
  content in jsdom; the accessibility tree above is the check for that).
- **Item 5.** Cold load, cache disabled: each of the four font files requested exactly once (the two preloaded ones
  included: `crossorigin` works), one host (`localhost:4173`), no content-security-policy violation, no console or
  exception event, and no "preloaded but not used" warning after waiting past the usual 3 seconds.

**Sizes.** JavaScript 75,874 bytes gzipped (74.1 KB; budget 100 KB). Fonts 68,400 bytes (66.8 KB; budget 150 KB; from
66,008), four WOFF2 files: Big Shoulders Display 800 14.55 KB, Newsreader 400 22.48 KB, Source Sans 3 400 15.69 KB and
600 15.66 KB. CSS 8.70 KB (2.76 KB gzipped).

**Screenshots** (`scratch/p15-review/shots-after/`, gitignored; "before" in `shots-before/`): the full page at 1280 and
390 in light and dark (`desk-*.png`, `phone-*.png`, and `sections/` for the readable crops), the control with Fragrance
chosen at 390 (`m-control-*.png`) and at 1280 (`control-*.png`), a traced run at 1280 (`hover-*.png`), the run table
at 1280 (`runs-table-*.png`), and both tables on a phone scrolled fully right (`m-status-scrolled-*.png`,
`m-runs-scrolled-*.png`). Looked at against the "before" set: the name is on one line, the lede is calmer, all fourteen
columns of the run table show at 1280 with the amounts right-aligned under their wrapped headings, the sticky names hold
on a phone, and a dimmed panel is legible.

**What did not fit, and what was done instead.**

- **At 1180 the run table still scrolls, by 10px, and at 1024 by 103px.** §22 and his decision said the scroll goes
  "from about 1,180px up". Its 1,022px figure was measured with every heading allowed to wrap; the decision wraps only
  the seven line headings, and then the table's narrowest is 1,032px (measured both ways today: 1,022 with every
  heading wrapping, 1,032 as built). The 10px is the two-word "Open day" heading. The frame is `(viewport + 1,024) / 2 -
  80` wide, so the scroll goes at a viewport of about 1,200px, not 1,180. Nothing was changed to chase it; the two
  ways to close it are letting "Open day" wrap as well (it is a heading, not one of the seven) or trimming the cell
  padding by about 1px a column, and either is his call at review.
- **The run table's first header cell is sticky too** (not asked for). Without it the "Run" heading scrolls away from
  its column while the ids stay. The rule is the status table's, and the same one-line selector list.
- **Status table, "the first cell of each header row":** its second header row has no cell in column 0 (the "Status"
  cell spans both rows), so one cell is sticky there, not two.
- **`content: attr(data-label) / ""`** uses the alternative-text form so that engines that count pseudo-element content
  in a name do not double it. Chromium needed no help (it ignores the hidden copy); Firefox and Safari were not tried.
  An engine that does not read the form drops the declaration, and then the buttons shift 3px as before: nothing breaks.
- **Not done, as the prompt says:** a sticky priority control (on a phone the control is above the viewport once the
  panel is in view); new words (none were needed); Safari, Firefox and a real phone.

**`make check`:** green. Python 3,248 passed; Vitest 36 passed (37 after the review, §23a) (29 before; seven added: five for item 1, two for
`data-label` and the `wide` and `amt` hooks); prettier, `tsc`, the build and `check-dist` all pass; `terraform
validate` succeeds; `doctor` ok (hooks installed, term file loads). `hc protocol check`: ok.

### 23a. Opus's review of the fixes (2026-11-06, about 5:15 PM)

Read the whole diff against the build prompt and §8, re-ran `make check` (green: Python 3,248, Vitest 36), and
measured the production build again under `npm run preview` in headless Chromium with classic scrollbars, with
scripts of its own (scratchpad, not tracked). **Every measurement above reproduced to the pixel:** the item 3 table at
all eight widths (and 1,200: no scroll), the item 4 button positions, the four font files requested once each from one
host with no console or policy message, and the two preload tags in `dist/index.html`. The accessibility tree names
the six buttons once each. `@fontsource/newsreader` 5.3.0 re-checked live: OFL-1.1, published 2026-07-19, its
integrity matching the lock.

**One finding, from the prompt, not the build: item 1 also moved the page on desktop.** The prompt asked for the
scroll at every width; the miss in §22 was on a phone. At 1280 by 800, choosing Low water use, Butterflies or No
priority set scrolled the page 700 to 1,150px and carried the control off screen at every choice. **His decision
(2026-11-06, about 5:10 PM, as recommended): only in the one-column layout.** Opus changed it in review: the effect
returns early when `(min-width: 54rem)` matches, the two-column breakpoint in `styles.css` (a comment there now
points back at `Chart.tsx`), and one Vitest test proves it (37 now). In the browser: at 390 and 800 the chosen panel
lands at 16px; at 880 and 1280 the page does not move.

**The 10px at 1180: his decision (about 5:10 PM, as recommended), accepted as built.** The seven-heading rule stands;
the run table scrolls from 1,024 to about 1,199px, and not from about 1,200px up. Letting "Open day" wrap as well was
measured: it moves that point only to about 1,180 (5px still at 1,170). §22's "about 1,180px" reads as about 1,200.

**Nothing else to change.** Departures accepted: the sticky "Run" header cell, and one sticky header cell in the
status table. The `::after` alternative-text form was proven in Chromium only (Firefox and Safari not tried, not checked
live); where an engine does not read it, the declaration drops and the buttons shift 3px as before. The "after" screenshots stand: the desktop shots never
scrolled, and the phone behavior is unchanged.

## 24. As built, C5 (2026-11-07)

**The rewrite.** `infra/vercel/vercel.json` holds one rewrite, every path to `https://d17t61og2l6kuo.cloudfront.net/$1`,
the shape Musical Mycelium uses. `.vercel/` (the CLI's link: project and team ids) is gitignored. The folder was linked
to the existing `horizon-compact` project by copying the link from the 2026-10-05 placeholder deploy, so no
interactive `vercel link` was needed.

**The deploy (his, about 8:45 AM, decision 4):** `npx vercel@65.2.0 deploy --prod` from `infra/vercel`. 65.2.0
(2026-10-22) is the newest release at least 14 days old; 65.3 to 65.12.1 were younger. The saved CLI login had lapsed
and was renewed by the device flow. Ready in 29 seconds; aliased to `https://horizon-compact.vercel.app`.

**Checked by Claude, 2026-11-07:**

- **Headers (§15's open question): all five of CloudFront's security headers come through the rewrite unchanged**:
  `content-security-policy`, `strict-transport-security`, `x-content-type-options`, `referrer-policy` and
  `x-robots-tag: noindex`, each identical to the distribution's. `cache-control: no-cache` on the page too. No
  `headers` block is needed in `vercel.json`.
- **The build:** the public `index.html` is byte-identical to the reviewed local build, and so is each of the seven
  files it names or serves beside it (the script, the stylesheet, the four fonts, the favicon), each with the right
  content type.
- **A missing path answers 200 with the page**, as the distribution does by design (`site.tf` maps 403 and 404 to
  `/index.html`); Vercel passes that through.
- **In headless Chromium at 1280 and 390 pixels:** all four faces loaded (Newsreader 400, Source Sans 3 400 and 600,
  Big Shoulders Display 800), 28 table rows, every request to `horizon-compact.vercel.app` alone, and no console
  message, policy violation or failed request. Screenshots in the scratchpad, not tracked.

**Not checked here:** the run table's run ids and image digest against the records, DoD 1's trace, which C6 commits
with the screenshot set; and Firefox and Safari. *(Checked 2026-11-07 after the teardown test, §25: all 15 run ids and the digest
in the live bundle, the digest Phase 1 recorded; screenshots in `docs/phases/screenshots/phase-1.5/`.)*

**Deploy's path filter, fixed (his ask, 2026-11-07).** `infra/**` set both halves, so a commit touching only
`infra/vercel/` would have built an image and applied `main` with nothing changed in AWS, and would again at the
teardown test's step 5, right after the re-apply. `deploy.yml` now leaves `infra/vercel/**` out of its trigger paths
and matches `infra/vercel/*` first in the `changes` job, setting neither half; two assertions in
`tests/test_architecture.py` hold both. Run by hand on sample paths: the rewrite alone sets neither, the rewrite with
a Terraform file sets both. **The commit carrying this still runs both halves**, because `deploy.yml` itself changed:
a new image is built and `main` applied, with no expected change beyond the task definition's image.
*(Done 2026-11-07: committed `9b18bd4`, his; CI `42385351266` and Deploy `42385351271` green; image
`sha256:c5f8862f52499773af85bc07695b2379ef08e8002352b0df2c4864c91d78dabe`; the apply replaced the task definition
alone, 1 added and 1 destroyed; the public `index.html` unchanged.)*

**Next: step 10, the teardown test** (§10). It gives the distribution a new domain, and step 5 of that test puts the
new domain into this file and deploys it again.

## 25. The teardown test (2026-11-07, §12 step 10)

**Step 1, before (his, 10:18 AM):** `scratch/p15-teardown-counts.sh before`. The shown sweep 15 of 15 valid, $0.0140;
`development/placeholder/` 257 keys, 257 versions, 0 delete markers; the whole results bucket 9,257 keys, 9,257
versions, 0 delete markers.

**Step 2, the destroy, first attempt (his dispatch; run `42392129939`): FAILED after 3 minutes, 18 of 20 destroyed.**
Everything in `main` went but the distribution and the site bucket. Terraform's delete of the distribution was
accepted; its waiter's `GetDistribution` was then refused with `AccessDenied`. **The cause:** `SiteDistributionManage`
allowed `GetDistribution` only on a distribution tagged `Project = horizon-compact`, and a deleted distribution has no
tags, so the read is denied instead of answered "no such distribution". The same refusal would stop a re-run, whose
refresh reads the distribution still in state. The site bucket was not reached (it waits on the distribution); it has
`force_destroy`. The results bucket, ECR, the state and the two `bootstrap` CloudFront objects are not in `main`.

**The fix (Opus, 2026-11-07):** `GetDistribution` moves out of `SiteDistributionManage` into its own statement,
`SiteDistributionReadAfterDelete`, on `distribution/*` with no condition; every write stays fenced by tag, and the
retag deny is unchanged. Accepted cost: the role can read the configuration of any distribution in the account
(Musical Mycelium's included; it could already list them all with `ListDistributions`), and gains no write. The
assertion in `tests/test_architecture.py` holds it. `bootstrap`, his apply.

**The fix applied (his, 11:16 AM):** plan 0 to add, 1 to change, 0 to destroy, exactly the statement move; apply the
same.

**Step 2, second attempt (his dispatch, run `42395590670`): the destroy complete; the check FAILED on a false
positive.** The refresh read the distribution as gone and dropped it from state; the plan was 1 to destroy, the site
bucket, emptied and deleted; "Destroy complete! Resources: 1 destroyed." All 20 of `main`'s resources are gone. Of the
check's four parts, three passed (no ACTIVE cluster by name, no ACTIVE task definition, no distribution with the
project's comment); the tag listing still named `cluster/horizon-compact` at all 20 attempts, about ten minutes, some
50 minutes after its delete. **The cause:** a deleted ECS cluster is INACTIVE and "may remain discoverable in your
account for a period of time" (the ECS DeleteCluster API reference, read 2026-11-07), as an inactive task definition
is, and bills nothing. The check already passed over task definitions and not clusters.

**The fix (Opus, 2026-11-07):** in `teardown.yml`'s check, a listed cluster is described by ARN and passed over only
when its status is INACTIVE; any other status, or a failed describe, keeps it listed and fails the check. The deploy
role already holds `ecs:DescribeClusters` on that cluster. Simulated on a fake listing (INACTIVE passed over, ACTIVE
kept); a new test holds it; the "no ACTIVE task definition" line now prints the AWS error instead of an empty line.

**The order from here (his decision, 2026-11-07): one commit** carrying the check's fix, `deploy-site.json`, the
tests and these docs. Its `infra/` path starts Deploy, which is §10 step 4's re-apply, both halves, with no separate
dispatch. **So the fixed check has not had a real run:** step 3 rests on run `42395590670` (the destroy complete,
three of the check's four parts passed, the fourth failed only on the INACTIVE cluster AWS documents), with the fix
held by its test and the simulation. Its first real run is the next teardown. Two commits (the check alone first,
then a teardown re-run) were offered and declined.

**Step 4, the re-apply (Deploy `42397385746`, on the push of `f49d530`; CI `42397385741`): green.** 20 added; the
distribution `E3N78URQESJO0Y` at `d10219migxiagd.cloudfront.net`; the smoke test passed. **The image digest did not
change** (`sha256:c5f8862f...`, as on `9b18bd4`): §10 step 4 expected a new one, but no code changed and the build
reproduced the same image, so ECR holds no extra image.

**Step 5, the rewrite (his, about 12:45 PM):** `vercel.json` to the new domain, `npx vercel@65.2.0 deploy --prod`,
aliased, ready in 4 seconds.

**Step 6, after (his, 12:49 PM, and Claude):** the counts equal the step 1 counts line for line (15 of 15 valid;
257, 257, 0; 9,257, 9,257, 0). The public page and all eight built files are byte-identical to the reviewed build,
with the five headers; the live bundle carries all 15 run ids and the image digest Phase 1 recorded for the sweep
(Phase 1 doc §21a); headless Chromium clean at both widths. Full-page screenshots, light and dark at 1280 and 390,
committed in `docs/phases/screenshots/phase-1.5/` (not under `evidence/`, whose scan reads every file as text).

**The teardown test passes (DoD 3)**, with two fixes found on the way, both in `f49d530`: the read after delete
(`bootstrap`, applied) and the INACTIVE cluster in the check (not yet proved by a real run). The record is
`evidence/phase-1.5/teardown.md`. **C6** is the commit of that file, the screenshots and `vercel.json`.

## 26. Close-out (C7), 2026-11-08: the spend and the DoD audit

Written by Claude (Opus) on 2026-11-08, the day after the teardown test, from the as-built record above, his Cost
Explorer reading and checks run the same morning.

**The spend (§12 step 11; his reading, about 7:57 AM).** AWS Cost Explorer, 2026-11-04 to 2026-11-07 (UTC), monthly,
unblended, grouped by service, filtered to the tag `Project = horizon-compact`: **$0.01 in all**. ECR $0.01; S3,
CloudFront and CloudWatch $0.00 each. No model call was made this phase, so there is no Anthropic or OpenRouter line.
Three limits on the number, none of which moves it near the bar: AWS calls the current month's figures estimated;
Cost Explorer can lag by up to a day, so 2026-11-07 may be partly missing; and a tag filter counts only tagged
resources (it is the right filter all the same, since Musical Mycelium shares the account). **With Phase 1's about
$0.07 by its records (§22 of the Phase 1 doc), the two phases come to about $0.08**, against DoD 6's "about $1 or
less". The ECR line is the images no longer expired (decision 7), the one cost this phase adds that grows; §14 said
to measure it at the close. **Measured 2026-11-08, about 8:10 AM (his read-only command, `aws ecr describe-images`
summing `imageSizeInBytes`): 16 images, 1,832,897,851 bytes (about 1.8 GB).** At $0.10 per GB-month (ECR's private
storage price, read on its pricing page the same morning; the new-customer free tier does not apply to this account)
that is **at most about $0.18 a month**, inside the credits. It is an upper bound: the sum counts layers shared
between images once per image, and ECR stores a shared layer once. Each image-building push adds about a cent a
month at this size (about 115 MB an image on average, the same upper bound); untagged images still expire.

| Scope DoD (as read through §0) | Met | Proof |
|---|---|---|
| 1. The page at `horizon-compact.vercel.app` shows the placeholder sweep with spread and run counts, labeled a test in his words; any number traced to run ids and image digest | **yes**, 2026-11-07 | §24 and §25 step 6: the public page and all eight built files byte-identical to the reviewed build; the live bundle carries all 15 run ids of `skeleton-haiku-5-5-f1467906` and the image digest Phase 1 recorded (Phase 1 doc §21a); the labels his, word for word (§20); full-page screenshots, light and dark at 1280 and 390, in `docs/phases/screenshots/phase-1.5/`. The page answers 200 on 2026-11-08 |
| 2. The published JSON is committed, produced by the site-data builder; a re-run is byte-identical | **yes**, 2026-11-04 | §18: `tests/test_site_data.py` (a second build byte-identical; the S3 and local stores give identical text); his S3 and local runs, `cmp: identical`; `web/src/data/placeholder.json` committed in `b9b8ac8` |
| 3. Destroy and re-apply both succeed; nothing billable left; page, traceability and raw record back | **yes**, 2026-11-07, with one part proved by test only | §25 and `evidence/phase-1.5/teardown.md`: destroy runs `42392129939` (stopped, fixed) and `42395590670` (all 20 gone; three of the check's four parts passed, the fourth failed only on the INACTIVE cluster AWS documents); re-apply Deploy `42397385746`; step 1 and step 6 counts equal line for line. **The check's INACTIVE-cluster fix has had no real run** (his decision, §25); it is held by its test and a simulation, and its first real run is the next teardown |
| 4. The section for results against the thesis is on the page, with his title | **yes**, 2026-11-05 | `web/src/copy.ts`: `resultsTitle` "Results that go against what I expected" and its sentence, approved by him (§20); on the live page |
| 5. `make check` and CI green; root under cap; every commit through the guard | **yes** | CI green on every Phase 1.5 commit: `0deae78` `41857222175`; `0526a2b` `41882765796` (Deploy `41882765814`); `b9b8ac8` `41916412080` (Deploy `41916412096`); `3714f44` `42002738203` (Deploy `42002738227`); `ea2bb7d` `42112962435`; `69b88ce` `42244341282` (Deploy `42244341172`); `a121fc3` `42311321663` (Deploy `42311321638`); `9b18bd4` `42385351266` (Deploy `42385351271`); `f49d530` `42397385741` (Deploy `42397385746`); `cf1fb71` `42404183618`. The two red runs in the phase are the teardown dispatches above, recorded in §25, not checks. Root 14 of 16 (`make root-check`, 2026-11-08). The guard's proof is the hook (Phase 1 doc §22, row 6); no bypass is recorded in this doc |
| 6. Spend measured from the bill; with Phase 1's, about $1 or less | **yes**, 2026-11-08 | his Cost Explorer reading above: $0.01 for this phase; about $0.08 with Phase 1 |
| *Added by this doc:* 7. No request leaves for another host; the security headers are served | **yes** | the content security policy (`default-src 'none'`, every other source `'self'`) and the built-files check in `npm run check`; Deploy's smoke test (§21, §25 step 4); at the public URL on 2026-11-08 all five headers (`content-security-policy`, `strict-transport-security`, `x-content-type-options`, `referrer-policy`, `x-robots-tag: noindex`), as in §24 |
| *Added by this doc:* 8. The deploy role cannot change a distribution that is not this project's | **yes**, 2026-11-06 | permission-check run `42245451195`, all six refused, the tag claim by the explicit deny (§21); the KNOWN-GAPS entry closed. Widened on purpose 2026-11-07 for reads only (`SiteDistributionReadAfterDelete`, §25): the role can read any distribution's configuration and still change none but its own |
| *Added by this doc:* 9. The image record: the lifecycle no longer expires images, and the lost digests are recorded | **yes**, 2026-11-04 | §17: his `bootstrap` plan and apply, the second plan "No changes", Phase 5.5's image confirmed after it; `KNOWN-GAPS.md`'s ECR entry (closed 2026-11-04) records the two expired digests (`ff978703...`, `ef2582ed...`) as a disclosed limit for the methods page |
| *Added by this doc:* 10. §8's checks pass | **yes**, 2026-11-07 | §22 (the review: five misses, three departures accepted), §23 and §23a (the fixes, Opus's review, one change by his decision); `a121fc3` live and matching the reviewed build |

**C7 as built.** This section; §12 step 11 marked done; **the version to `0.5.5`** (decision 10) in `pyproject.toml`
and `src/horizon_compact/__init__.py`, **and in `uv.lock`**, whose editable entry carries it (decision 10's "not in
the lock (checked)" was wrong; CI's `uv sync --locked` would have refused a stale lock, so `uv lock` was re-run and
changed that one line only). `ROADMAP.md` (the spine row, the phase-doc table, the decision history); `KNOWN-GAPS.md`
(START HERE; the OPEN entry of 2026-10-15 and the CARRIED list of 2026-10-11 closed); a dated note on the scope doc.
The version is recorded as `harness_version` in every record written from here on and compared nowhere (checked:
`cli.py` writes it; no code reads it back). **The close commit changes `src/`, `pyproject.toml` and `uv.lock`, so it
starts Deploy's code half:** a new image (the version line changes its bytes) and `main` applied with the task
definition replaced. That Deploy is owed with the CI.

**Left open by this close:** the INACTIVE-cluster check unproved by a real run (row 3, his decision); Musical
Mycelium's deploy role can still change this project's distribution (OPEN 2026-11-04, that repo's to fix); the
`horizon-compact-dev` access key kept to Phase 7's close or 2027-01-02 (decision 6); `noindex` stays until go-live
(decision 3).

**Phase 1.5 is CLOSED 2026-11-08, with his commit of this section.** Every phase through 5.5 is now closed.

*Dated note, 2026-11-08, about 8:40 AM:* the close commit is `2227a26` (his); CI `42490367867` and Deploy
`42490367866` green. Deploy's code half only (the site half skipped): new image `sha256:ea6bb1cb...` (the version
line changed its bytes), `main` 1 added, 0 changed, 1 destroyed (the task definition replaced).
