# Report, batch 2 (verbatim)

Claude in Chrome, Sonnet 5.5 at the panel's default effort, a new conversation with `brief-2.md` as its only input,
2026-11-24, ending about 1:10 PM CST. Run by him; pasted back as given. The panel's list of page loads and scripts
before the reply, and its closing disclaimer line, are left out; the reply follows exactly.

---

ITEM A5f

claim 1: Confirmed: budgets.tf has two budgets, sonnet_line (filtered on Service) and project_tag (filtered on TagKeyValue, user:Project$<project>). Every notification has notification_type = "ACTUAL", and both cost_types blocks set include_credit = false. sonnet_line is only created if sonnet_service_name is non-empty.
claim 2: Confirmed: ROADMAP's 2026-10-08 block says "Phase 0.5 aws-foundation closed in the morning ($0.02 spent in all; two budgets live)". Phase 0.5 DoD row 3 is PASS with evidence "the two budgets above". I did not find a separate "applied" date beyond that block.
claim 3: Confirmed: Phase 4 DoD row 2 says both grid sessions "started 09:52:25 and 09:52:27 UTC", with the projection committed 2026-10-14 09:44:55 UTC. The earlier 2026-10-13 pilots are marked as excluded.
claim 4: Confirmed: the protocol's models table gives the Haiku route as "Anthropic's own API" and the gpt-oss-120b route as "OpenRouter, pinned to one host: DeepInfra". The lines I read are about L443-446, not L433 itself.
claim 5: Confirmed: run-log has "$0.31 in all … horizon-compact $0.04 … no Project tag $0.27", and "run_task passes no tags". The log does not say that the tag budget missed the spend. That is my inference from the tag filter. The Service-filtered budget would not catch Fargate compute either.
status: partial: both budgets were live six days before the first full run, but neither filter covered that run's AWS spend ($0.27 untagged Fargate), and its model calls were billed outside AWS.

ITEM A6

claim 1: Confirmed: the manifest has "object_count": 5247 and "total_bytes": 104785272, with 5,247 entries in objects. I fetched 8 of those keys under experiment/raw/. All returned 200, and the two I size-checked matched the manifest (3,278 and 24,586 bytes). I could not list the folder, since github.com pages were blocked, so I did not check all 5,247.
claim 2: Confirmed: the docstring says the frozen analysis runs on published raw records and the tests "fail if anything opens an AWS client while they run". Around L39, AwsClientOpened is "Something asked for an AWS client while the re-scoring test was running."
claim 3: Confirmed: all 5 cases have dossier: {"published": false, "reason": "withheld: …"}. Four give "fewer than 20 filers in SEC's structured data" and one gives "the re-identification check could not confirm".
claim 4: Confirmed: the methods page says "No case's dossier is published, so no real case can be re-run from published inputs", and "for the made-up company it can, and for the real cases it cannot". The page has both a real cases section and a "Checking it yourself" section.
claim 5: Contradicted (in part): KNOWN-GAPS confirms two images expired under the ten-image rule, measured 2026-11-04. But they are the Phase 4 official image ff978703… and Phase 1's skeleton image ef2582ed…, so only one was used by official runs. The methods page calls both "official".
status: partial: the made-up company can be re-scored and its prompts rebuilt from published text, but the real-case dossiers are not published and no run can be repeated in the identical image. The methods page does say so, as the promise requires.

ITEM B15

claim 1: Confirmed: the Phase 1.5 close-out table has "Added by this doc: 7. No request leaves for another host; the security headers are served | yes". Its evidence is the CSP, the built-files check, the smoke test, and five headers seen at the public URL on 2026-11-08.
claim 2: Confirmed: site.tf sets default-src 'none' and script-src, style-src, font-src, connect-src and media-src all 'self'. img-src is 'self' data:, and base-uri 'none', form-action 'none' and frame-ancestors 'none' are also set. So the CSP allows the site's own origin plus data: images. It is a CloudFront policy; vercel.json (infra/vercel/vercel.json) rewrites to CloudFront. I could not fetch the live headers: browser script access was blocked, and the shell cannot reach vercel.app.
status: met: the repo's CSP and audit row support "no other host" and served headers. I did not independently confirm live headers or the absence of cookies.

ITEM B65

claim 1: Confirmed: Phase 6.5 §11.1 marks all 11 rows "yes". Row 5 reads "yes, with two logged departures and two disclosures" and row 6 "yes, with two qualifications".
claim 2: Could not check: the Actions run page would not load (the browser call timed out and the shell got 403). The audit's row 9 lists 44922943678 as the last of the 12 green CI runs. It does not say that run is the go-live commit.
status: partial: rows 5 and 6 are met only with departures. The video is hand-edited with a Claude-written script, where the plan said remake rather than edit. Check 4 was one read, and check 6 is accepted as absent on the cards and the video.

ITEM C2

claim 1: Confirmed: protocol §7.1 says "No imputation", with refusals as outcomes. §7.2 says a cell above 10% failures is unreliable and its wording is dropped from both sides. §7.3 recomputes each verdict with failed runs set to the worst case.
claim 2: Confirmed: the README table shows verdict_gpt_oss_s2_ac as "not assessable". The explorer data for gpt-oss s2 has one primary comparison not_assessable. The methods page says 27 of 300 runs failed (9.0%), 4 cells crossed 10%, and "A against C" was left with no wording. I did not open the live s2 scenario page.
status: met: failures and refusals are counted, the 10% cell rule and the worst-case bound are stated, and one comparison actually became not assessable.

ITEM C4

claim 1: Confirmed: §6.1 says "Four scenarios by four pairs is the family of 16 per model". §6.4 sets "alpha is exactly 0.05 / 16 = 0.003125 … (Bonferroni over the family)".
claim 2: Confirmed: in s1.json the 4 primary comparisons have "alpha": 0.003125. Across both models' s1–s4 files, all 32 primary comparisons carry 0.003125, which is a 99.6875% interval (about 99.7%). The secondary A-vs-D comparison also uses it.
status: met: the primary family is fixed at 16 and corrected by Bonferroni, and the data carry that alpha.

ITEM C5

claim 1: Confirmed: §6.3 lists Split, No split and Inconclusive, plus "Not assessable … Never counted as any of the three", under the heading "The three verdicts, and a fourth label".
claim 2: Confirmed: git ls-remote shows refs/tags/prereg-v1 (tag object c949580, peeled 649e8b9). The repo's tag-record.md gives the tagger date 2026-10-13 01:19:15 -0500, and the grid sessions began 2026-10-14 09:52 UTC. The releases page itself would not load.
status: met: three verdicts are kept and the fourth is only a label for runs that cannot be assessed.

ITEM C6

claim 1: Confirmed: Phase 3 audit row 3 says "the bootstrap's false split (worst 2.22%) was patched out (Welch …), leaving 0.43% worst, 5 of 360 points clearly over 0.3125%", accepted 2026-10-09. That is before the 2026-10-13 tag.
claim 2: Confirmed: the methods page's known limits list "The chance of a false split is held approximately, not exactly". The page text says the worst cases were 0.43% (shares) and 0.417% (choice rates), against a 0.3125% target.
status: partial: the interval method is set and simulated, but the false-split target is met only approximately. The page puts the family-wise rate at up to about 6.9% against 5%. No-split reachability is 49.7% at worst against about 54% planned.

ITEM C12

claim 1: Confirmed: protocol §5.1 says "The fallback set of decision 5, taken on 2026-10-12" with gpt-oss-120b as "the second family", and "Nova Pro … are not in v1". The reason is in §2.4: "When Bedrock stayed unavailable".
claim 2: Confirmed: the 2026-10-12 choice precedes the tag dated 2026-10-13 (see C5 claim 2).
claim 3: Confirmed: §2.4 says the runs on the company's content were "read only through blind reports". It also says one disclosure was made, which S2 objectives had format failures, and "The development model is now the second family".
status: met: a second family (gpt-oss-120b) ran a full grid of 1,200 runs, with its development-model history disclosed before the tag. It always reasons while Haiku ran with thinking off, so differences between the two models cannot be put down to family alone.
