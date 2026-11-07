# Phase 1.5, the teardown test (2026-11-07)

The record for DoD 3 (the Phase 1.5 IMPLEMENTATION doc §10 and §25). Counts from `scratch/p15-teardown-counts.sh`,
his laptop, read-only; any 12-digit run masked by the script.

## Runs

| Step | What | Run | Result |
|---|---|---|---|
| 2 | Teardown, first dispatch | `42392129939` | failed: 18 of 20 destroyed; the delete waiter's `GetDistribution` refused (tag-fenced, a deleted distribution has no tags) |
| - | `bootstrap` apply (his) | - | `SiteDistributionReadAfterDelete`: 0 added, 1 changed, 0 destroyed |
| 2, 3 | Teardown, second dispatch | `42395590670` | destroy complete (the distribution read as gone, the site bucket deleted: all 20); check failed on one false positive, the INACTIVE cluster still in the tag listing; no ACTIVE cluster, no ACTIVE task definition, no distribution |
| 4 | Deploy, on push of `f49d530` | `42397385746` | green; 20 added; image `sha256:c5f8862f52499773af85bc07695b2379ef08e8002352b0df2c4864c91d78dabe` (unchanged: no code changed, the build reproduced it); distribution `E3N78URQESJO0Y`, `d10219migxiagd.cloudfront.net`; smoke test passed |
| - | CI, the same push | `42397385741` | green |
| 5 | Vercel rewrite to the new domain (his) | - | aliased to `horizon-compact.vercel.app`, ready in 4 seconds |

## Step 1, before

```
teardown test, before, 2026-11-07T16:18:16Z

== hc sweep status, the shown sweep (skeleton-haiku-5-5-f1467906) ==
sweep:           skeleton-haiku-5-5-f1467906
runs finished:   15 of 15  {'valid': 15}
attempts:        15  {'valid': 15}
cost so far:     $0.0140
  session 2026-10-12T13:09:30.899276+00:00  fargate  stopped: complete  15 attempts

== development/placeholder/ ==
keys: 257  versions: 257  delete markers: 0

== the whole results bucket ==
keys: 9257  versions: 9257  delete markers: 0
```

## Step 6, after

```
teardown test, after, 2026-11-07T18:49:51Z

== hc sweep status, the shown sweep (skeleton-haiku-5-5-f1467906) ==
sweep:           skeleton-haiku-5-5-f1467906
runs finished:   15 of 15  {'valid': 15}
attempts:        15  {'valid': 15}
cost so far:     $0.0140
  session 2026-10-12T13:09:30.899276+00:00  fargate  stopped: complete  15 attempts

== development/placeholder/ ==
keys: 257  versions: 257  delete markers: 0

== the whole results bucket ==
keys: 9257  versions: 9257  delete markers: 0
```

**Equal**, line for line but the timestamp.

## Step 6, the public URL (checked by Claude, 2026-11-07)

- `index.html` and all eight built files byte-identical to the reviewed build; the five security headers served.
- The live bundle carries all 15 run ids of `web/src/data/placeholder.json` and its image digest
  `sha256:ef2582ede504536d0c9c64615d9f18bf9dde7b784f66e314cbca6377d1d16f02`, the digest Phase 1 recorded for
  `skeleton-haiku-5-5-f1467906` (the Phase 1 IMPLEMENTATION doc, §21a).
- Headless Chromium at 1280 and 390: four faces loaded, 28 table rows, every request to the page's own host, no
  console message, policy violation or failed request. Full-page screenshots, light and dark at both widths:
  `docs/phases/screenshots/phase-1.5/`.

**Not proved by a real run:** the check's fix for an INACTIVE cluster (his decision, one commit; §25). Its first real
run is the next teardown.
