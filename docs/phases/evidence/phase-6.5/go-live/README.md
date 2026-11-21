# Phase 6.5 step 11: go-live (doc section 7, items 3-8)

Go-live: 2026-11-21. **Step 11 done the same day: every item below is checked.** Built by Claude (Opus) from about 9:45 AM CST, at his go-ahead ("go ahead, i give you
permission", 9:43 AM). Item 1 (every section 5 check passed) is step 10's record; item 2 (serving in `main`) was step 6.

## What the go-live commit changes

| Where | Change |
|---|---|
| `infra/terraform/bootstrap/site.tf` (his apply, first) | `media-src 'self'` added to the content security policy; the `X-Robots-Tag: noindex` header removed (the whole `custom_headers_config`, its only item) |
| `web/vite.config.ts` | the preview serves the same policy, so it no longer blocks the video and sends no noindex |
| `web/explorer.html`, `web/scripts/write-paths.mjs` | the explorer's `noindex` tag removed from every page; the not-found page alone carries one, added by `renderNotFound` |
| `web/scripts/check-dist.mjs` | explorer mode refuses a robots tag on any page but the not-found page, and any placeholder: in `his.json` and in the shipped methods words (`copy.test.ts` holds its markers equal to the code's) |
| `.github/workflows/deploy.yml` | Deploy syncs `web/dist-explorer`, never `.vite/`, with the captions as `text/vtt` and the memo files as `text/plain`; the smoke test checks the explorer's entry, the headers (retried, with `media-src` present and no `x-robots-tag`), each media and data type, `/methods/` serving its own page and the manifest's absence |
| `tests/test_architecture.py` | the headers, sync and smoke-test tests follow |
| M12 | the changelog's first entry, dated |

The placeholder build stays a mode (`npm run build`, checked by `check-dist`), unused.

## The checklist

- [x] 3. His `bootstrap` plan and apply, 2026-11-21 about 10:07 AM. Plan (`scratch/p65-s11-plan.sh`): **0 to add, 1 to
  change, 0 to destroy**, the one change `aws_cloudfront_response_headers_policy.site` in place: the `X-Robots-Tag:
  noindex` item removed, `media-src 'self'` added to the policy, nothing else. Apply: "Apply complete! Resources: 0
  added, 1 changed, 0 destroyed."; the two site ids as before.
- [x] 4. The go-live commit, his: C11 `42e6284` `phase 6.5: c11 go-live`, pushed about 10:08 AM; CI `44922943678` and
  Deploy `44922943677` green, first attempt. Deploy's smoke test, on the distribution's own domain: "the site serves this
  build (attempt 1)" (`explorer-B1sUZ_Th.js`); "headers ok, no x-robots-tag (attempt 1)"; served as `video/mp4`,
  `text/vtt`, `application/json`, `image/png` and (a memo file) `text/plain`; "/methods/ serves its own page: How the
  study was done"; the manifest answers 404; "an unknown address answers the not-found page with 404 (attempt 1)".
  **The site has been public since this Deploy, about 10:15 AM.**
- [x] 5. **The teardown test passes**, 2026-11-21, 11:03 AM to 1:00 PM (Phase 1.5 section 10's procedure, his steps,
  Claude's reads). **Before** (his, `scratch/p15-teardown-counts.sh before`, 17:03:53Z): the shown sweep 15 of 15 valid,
  $0.0140; `development/placeholder/` 257 keys, 257 versions, 0 delete markers; the whole results bucket 9,257, 9,257, 0
  (the same as on 2026-11-07). **Destroy** (his dispatch, run `44928743719`, green in 3m57s): "Plan: 0 to add, 0 to
  change, 21 to destroy" (Phase 1.5's 20 and step 6's CloudFront Function), "Destroy complete! Resources: 21
  destroyed.", the distribution in 3m18s. The check: the deleted cluster still listed and passed over as INACTIVE, 0
  active clusters, no active task definition, 0 distributions with the project's comment, "Nothing billable from main
  remains." **This is the first real run of 2026-11-07's INACTIVE-cluster fix** (Phase 1.5 doc section 25), held until
  now by its test and a simulation; it worked. **Re-apply** (his Deploy dispatch, run `44929157666`, green): "Apply
  complete! Resources: 21 added, 0 changed, 0 destroyed."; the new distribution `E34HK7Y6ZF40HF` at
  `d3e4e283m4fruz.cloudfront.net`; a new image digest, `sha256:2708cc4b...` (C11's Deploy built `sha256:28d351a8...`),
  on which no sweep is planned, as section 10 step 4 expects; the smoke test passed in full on the new distribution, the
  same entry (`explorer-B1sUZ_Th.js`). **The rewrite** (Claude's edit of `infra/vercel/vercel.json`; his deploy,
  `npx vercel@65.2.0 deploy --prod --cwd infra/vercel`, about 12:58 PM): aliased to `horizon-compact.vercel.app`, ready
  in 5 s; he declined the CLI's offer to upgrade (the version is pinned). The public URL answered 502 from the destroy
  until then and 200 after, the same entry, the new policy, no `x-robots-tag`; an unknown path 404. **After** (his,
  18:59:23Z): identical to before, line for line, apart from the timestamp. The browser review re-run on the public URL after the rewrite (`scratch/p65-s5-shoot.mjs`, about 1:00 PM): 56
  loads, 0 with a problem, maximum layout shift 0.047, identical to the first live run. The public site was down for about 1 hour
  45 minutes, from the destroy (about 11:13 AM) to the rewrite (about 12:58 PM), most of it waiting on his return.
- [x] 6. The live site against the preview, about 10:15 to 10:22 AM (Claude). **With no script** (curl on
  `horizon-compact.vercel.app`): all 14 paths answer 200 with their own title and a canonical link to their own address,
  no robots tag, and an `og:image` that answers 200 as `image/png`; an unknown path answers 404; `/methods` redirects
  (301) to `/methods/`. **In the browser** (`scratch/p65-s5-shoot.mjs`, run on the live URL and on a fresh preview of the
  same build with the new policy): 56 loads each (14 paths, 390 and 1280, light and dark): **0 with a problem** (console
  error or warning, failed or off-origin request, policy violation, axe-core, horizontal overflow), maximum layout shift
  0.047, the axis words on all 20 charts in place; the number trace 0 untraced on 13 paths; the two reports **identical**.
  Two flags, both on `/methods/` and the same in both runs, both the script's and not the site's: the crop test counts the
  video's `<figure>` as a chart missing its model, run count and scope line (it is the video, not a chart); and the trace
  misses "1,237", which `methods.json` declares as a figure traced to `KNOWN-GAPS.md` (held by `methods.test.ts`): the
  script strips the number's comma before looking for it in text that keeps it.
- [x] 7. Link previews on LinkedIn's Post Inspector (his, about 2:35 PM): `https://horizon-compact.vercel.app/` shows
  the page's title, description and the story card; his read: "it matches. looks pretty good." Other paths' cards were
  not inspected there; each answers 200 as `image/png` from its page's `og:image` (item 6).
- [x] 8. The changelog starts (M12), with go-live as its first entry.
