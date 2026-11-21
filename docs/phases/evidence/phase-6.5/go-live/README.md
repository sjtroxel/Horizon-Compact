# Phase 6.5 step 11: go-live (doc section 7, items 3-8)

Go-live: 2026-11-21. Built by Claude (Opus) from about 9:45 AM CST, at his go-ahead ("go ahead, i give you
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
- [ ] 4. The go-live commit, its CI and Deploy.
- [ ] 5. The teardown test.
- [ ] 6. The live site against the preview.
- [ ] 7. Link previews on LinkedIn's post inspector.
- [x] 8. The changelog starts (M12), with go-live as its first entry.
