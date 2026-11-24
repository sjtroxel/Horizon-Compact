# Report, batch 1 (verbatim)

Claude in Chrome, Sonnet 5.5 at the panel's default effort, a new conversation with `brief-1.md` as its only input,
2026-11-24, about 12:15 to 12:22 PM CST. Run by him; pasted back as given. The panel's list of page loads and scripts
before the reply is left out; the reply follows exactly.

---

ITEM A1

claim 1: Confirmed: methods.json lists grid-haiku-5-5-0b99fabb with repeats s1 20, s2 6, s3 20, s4 20 and runs_in_manifest 990. It lists grid-gpt-oss-openrouter-fe599ad2 with 20 on every scenario and 1200. It also lists a third sweep, thinking-haiku-5-5-418caa9c (kind "thinking", 100 runs), which is not a grid.
claim 2: Confirmed: both grid entries have scenarios ["s1","s2","s3","s4"] and templates ["w1","w2","w3"].
claim 3: Confirmed: row 2 of the §13 table reads "Repeats from the pilots by the gate; projection committed before the first grid run", result pass. It says projection.md was committed 2026-10-14 09:44:55 UTC and the grid sessions started at 09:52:25 and 09:52:27 UTC.
claim 4: Confirmed: haiku-5-5/s1.json has 5 entries in comparisons, and every one has low and high (the first is −0.535 to −0.261).
claim 5: Confirmed: the s1 page says "Each dot is one run" and has a section "Every run: The same runs as the chart, as a table". The five goals are listed A to E, with "Goal E was given no goal".
status: met: all four scenarios and five goals ran on both models with stated repeats, including Haiku's lower s2 count of 6, and the intervals are reported.

ITEM A2

claim 1: Confirmed: cases.json has 5 cases (closure-07, closure-19, pre-11, pre-25, pre-224), each with type "closure" and exploratory true. Its short_by_type is {"closure":0,"retool":2,"ai":1}.
claim 2: Confirmed: §4.6.5 says "The pre-registered rule found no case in any type". Part A item 1 says the pre-registered selection "stands as recorded", with shortfalls 2 (closure), 2 (retool) and 1 (ai).
claim 3: Confirmed: the ROADMAP Phase 5 row's done-when reads "At least three cases run and matched, including an invest or retool case". Its status cell says "no retool or ai case, so the 'invest or retool' part of the done-when is not met".
claim 4: Confirmed: the cases page has a by-type table (Closure 5 found / 0 short, Invest or retool 0 / 2, AI-attributed 0 / 1). Each case carries "Type: Closure or restructuring" and the label "exploratory: selected by §4.6.5 step 2 (or 3), after the pre-registered rule found none".
status: met: five cases ran and the page presents them by type, but all five are closure cases chosen by the exploratory rule, and I could not confirm anonymization (cases.json marks each case's re-identification check "withheld").

ITEM A3a

claim 1: Confirmed: §9.1 reports the difference under each kept wording separately. §9.2 repeats the whole assessment on the sealed template's runs alone, "labeled 'sealed wording only', outside the family". methods.json shows templates w1, w2 and w3.
claim 2: Confirmed: all 5 comparisons in haiku-5-5/s1.json have per_wording, kept_wordings and sealed. The first has kept ["w1","w2","w3"] and sealed_wording "w2".
claim 3: Confirmed: after I opened a comparison's details, the s1 page showed "Sealed wording: sealed wording only; outside the family of 16: wording w2, inconclusive, −17.2 points, interval −37.4 to +3.0". This sits beside the pooled result, −19.1 points, interval −29.3 to −9.0, and it is the less flattering reading.
status: met: the wording variants ran and the sealed-wording result is shown on the site next to the pooled one, including where it is inconclusive.

ITEM A3b

claim 1: Confirmed: haiku-5-5/s3.json has position.options with chosen_first, runs_first, chosen_not_first, runs_not_first and an interval (alpha 0.05) for each of close, retool and sell. §9.3 matches this, and the quoted phrase "a position effect found is published" appears there.
claim 2: Confirmed: sell has chosen_first 8 of runs_first 106 and chosen_not_first 3 of runs_not_first 194. Its interval is low 0.0132, high 0.1272.
claim 3: Confirmed: there are 10 option intervals across the four files (Haiku s3 3, Haiku s4 2, gpt-oss s3 3, gpt-oss s4 2). Only Haiku s3 sell excludes zero. Haiku s4's two intervals run −0.224 to +0.002, so they include zero by a very small margin.
claim 4: Confirmed: scenario s3 and methods have no position results. The methods page says the order of lines and options "is shuffled for each run", but gives no result. I also found nothing on scenario s4 or the Side studies page.
status: partial: the shuffle ran and the position results are in the repo's data files, but no site page shows or discusses them, including the one nonzero finding (sell, Haiku s3).

ITEM A4

claim 1: Confirmed: /, /methods/, /cases/, /scenario/s1/ and /memos/ all loaded with content (/memos/ is titled "Memo reader"). /nope-404/ shows a page titled "Page not found".
claim 2: Confirmed: the scenario page's nav lists "Model: Haiku 5.5 / gpt-oss-120b". It shows goals A to E and comparisons such as "A vs C: −39.8 points". The memos page shows memos "Written by Haiku 5.5 under goal A … for a fictional company". I did not switch models or operate the compare controls.
claim 3: Confirmed in part: row 1 of the DoD table says "reading only precomputed data" (yes), and it says data "is fetched, never bundled" and there is "no request off the page's origin". That row does not literally say the site computes no result; row 1 supports the "precomputed" part. The cited #L3445 is the table's header row, and row 1 is at line 3447 in the page text as I counted it.
status: met: the pages the promise names load, the explorer offers model choice, goal comparison and memos, and the cited row says it serves only precomputed data.

ITEM A5a

claim 1: Confirmed: ecs.tf line 15 reads requires_compatibilities = ["FARGATE"] in the aws_ecs_task_definition "sweep" resource.
claim 2: Confirmed: record-checks.md has "| container | pass |". Its image section lists all seven sweeps (2 pilot, 2 awareness, 2 grid, 1 thinking), each with "1 image digest(s)" and the same digest, sha256:ff978703…6723.
status: met: the sweep task definition is Fargate, and every sweep ran from one image.

ITEM A5b

claim 1: Could not check in full: the docstring says "Every write is exclusive" and that S3Store sends IfNoneMatch="*" on every put, "never an overwrite". It does not say "one S3 object per attempt", and I did not find that wording there.
status: met: S3Store.put_new is write-once, and the bucket policy refuses a put without the header. The raw-output manifest counts 5,247 objects.

ITEM A5d

claim 1: Confirmed: infra/terraform/main holds ecs.tf, iam.tf, logs.tf, network.tf and site.tf. infra/terraform/bootstrap holds state.tf, results.tf, ecr.tf, budgets.tf, bedrock.tf, oidc.tf, iam.tf and site.tf.
claim 2: Confirmed: §4 says the IAM user horizon-compact-dev is created "in the console" with a managed policy "pasted from the tracked file infra/iam/horizon-compact-dev-policy.json". It calls this "the one resource the phase creates by hand" and "an exception to 'Terraform for everything'". The same doc says the Project cost-allocation tag was activated by hand in the console on 2026-10-04.
claim 3: Confirmed: row 11 of the §11.1 DoD table reads "The teardown test passed after the changes to main", result yes. It cites destroy 44928743719 (21 destroyed) and re-apply 44929157666 (21 added). The cited #L897 is the section heading, and row 11 comes a few lines below it.
status: partial: the project's AWS resources are in Terraform, but the IAM user and its policy, which run Terraform, were made by hand, as was the cost-allocation tag activation.

ITEM A5e

claim 1: Confirmed: deploy.yml line 120 has id-token: write and line 132 has role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}. The file also has the same pattern at lines 162/170 and 210/232. A search for access-key and secret-key strings found none.
claim 2: Confirmed: oidc.tf line 14 is data "aws_iam_openid_connect_provider" "github". A comment at line 11 says no resource "aws_iam_openid_connect_provider" appears anywhere under infra/.
status: met: the deploy workflow assumes a role through OIDC with no stored AWS key, and the OIDC provider is only looked up.
