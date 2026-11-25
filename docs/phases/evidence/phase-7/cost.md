# The final cost record (Phase 7 step 9)

Written by Claude, 2026-11-25 about 4:00 AM CST, from his readings that morning: the Anthropic Console's home and
API keys pages, OpenRouter's credits page, AWS's billing home, credits page and Cost Explorer (tag `Project`, daily,
unblended). Set against Phase 5.5's measured cost (`../phase-5.5/cost.md`, 2026-11-03), the $60 re-plan point and the
$80 ceiling (`planning/04` §3.4). No experiment call and no paid model call was made in Phases 6, 6.5 or 7 (each
IMPLEMENTATION doc's cost section); no task ran after 2026-10-30.

## The balances

| Pot | 2026-11-03 | Added since | 2026-11-25 | Drawn | This project's |
|---|---|---|---|---|---|
| Anthropic prepaid credit | $11.00 | none | $10.89 | $0.11 | **$0.00** (below) |
| OpenRouter, his cash | $3.46 | none | $3.46 | none | **$0.00** |
| AWS (shared with Musical Mycelium) | November to date $0.01 for the whole account | | November to date $0.17 | at most $0.16 | **$0.12** under the tag; at most $0.16 |

**The Anthropic draw is another project's.** The Console's month spend is $0.21. Its API keys page charges November
to two keys: this project's key $0.08 and the key of another of his projects, a public game, $0.13. This project's
$0.08 is the memo scan's Haiku pass of 2026-11-01 (`../phase-5.5/cost.md`, $0.0817), made before the 11/03 reading.
So the $0.11 drawn since is the game's, and this project drew nothing. The same key probably explains Phase 5.5's
untraced $0.03; that is not re-counted, so the totals below still include it.

**OpenRouter is his cash** (the re-scope's R.3 item 5). Measured from the bills since 2026-10-15: $11.66 plus the
$0.80 card fee (Phase 5), $0.24 (Phase 5.5), none since: **$12.70 of his cash**. Before 2026-10-15, the logs' tally
in `../phase-4/projection.md` item 3 and Phase 4's runs; not re-summed here.

**AWS credit left: $135.38** available (AWS's estimate $135.20 once November's invoice is final), expiring
**2027-07-30**. It is Musical Mycelium's credit too. No AWS cash has been paid.

## The cumulative total

At most about $45 to 2026-10-26 (`../phase-5/cost.md`, $44.89), plus at most $1.37 (Phase 5.5), plus at most $0.16
(AWS since 11/03): **at most about $46** ($46.42). Under the **$60 re-plan point** and the **$80 ceiling**. Passes. It
overstates: it counts the shared AWS account's whole use.

## The idle bill (decision B, as amended 2026-11-25)

Cost Explorer, tag `Project` = `horizon-compact`, daily, unblended, 2026-11-14 to 2026-11-20 UTC (seven whole days):
**$0.04**. Each day shows $0.01, so each was under a cent. Scaled to a month: **about $0.17 a month at that rate**
($0.04 over seven days; with the total's rounding, $0.15 to $0.20).

- **The window is before go-live** (2026-11-21). Decision B asked for seven whole days after C2's Deploy
  (2026-11-23, 16:26 UTC); the first such window, 11/24 to 11/30, cannot be read before 12/01. He chose not to hold
  the phase (2026-11-25, about 3:51 AM). The AWS resources billed were the same before and after go-live (the S3
  site bucket, CloudFront, ECR; go-live changed a response-headers policy and the public host), and before the
  launch post the site's traffic is small either way.
- **Deploys in the window (nine; image builds and `main` applies, no task):** 43609886681 (11/14), 43735395019
  (11/15), 43886443998 (11/16), 44122818155 (11/17), 44344066870, 44364703011 and 44423330858 (11/18), 44547601997
  (11/19), 44795927780 (11/20). More than any later week, so the figure leans high.
- **The charge type filter was not set** (decision B asks for Credit excluded). The figure is positive, so no credit
  was netted against it.
- **Cross-check:** the same report over 2026-11-03 to 2026-11-25 gives $0.12 for 22 whole days, which is about $0.16
  a month: the same rate. That span holds the go-live, the teardown test (`Teardown main` 44928743719, 11/21) and its
  re-apply, and C2, C3 and C5's Deploys.
- **The December note is dropped** (his, 2026-11-25, about 4:12 AM: "i don't think having it will in any way affect
  the outcome of this project"). Decision B had the first full calendar month after close added as a dated note on M8
  and in M12; the seven-day figure stands as the published one and says what it is.
