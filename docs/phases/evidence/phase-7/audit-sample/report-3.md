# Report, batch 3 (verbatim)

Claude in Chrome, Sonnet 5.5 at the panel's default effort, a new conversation with `brief-3.md` as its only input,
2026-11-24, ending about 1:20 PM CST. Run by him; pasted back as given. The panel's list of page loads and scripts
before the reply is left out; the reply follows exactly.

---

ITEM C14

claim 1: Confirmed: the patch says the pre-registered rule "found no case in any type", with shortfalls "2 (closure), 2 (retool), 1 (ai)" (part A item 1). The doc's Stage B entry says hc case search --date 2026-10-16 ran with run_on 2026-10-16 and deviation null. The ROADMAP Phase 5 row says "the search run 2026-10-16 on the rule date, no deviation" and "closure selection complete 2026-10-18 after the fallback pool: no case, shortfall 2".
claim 2: Confirmed: the patch is headed "Patch 2026-10-19" and "ADOPTED 2026-10-19". It says it "is written after the record of every rejected candidate was seen". It is judged "as an exploratory rule, not as a reading of the protocol".
claim 3: Confirmed: cases.json has 5 cases, each with exploratory: true and an exploratory_label reading "exploratory: selected by 4.6.5 step N, after the pre-registered rule found none". The live /cases/ page shows the same label on all five case entries.
status: partial: the shortfall was reported first, but all five cases were filled afterwards by a relaxed rule written after the rejected candidates were seen, and labelled exploratory. The promise says a shortfall is never filled by judgment.

ITEM C15

claim 1: Confirmed in substance, but the lock-before-probe part is not in rows 3 to 5 themselves. Row 4 says "five rubric reads, all agrees". Row 5 says "four cases six of six on set 1; closure-19 none of six on set 1, coarsened, six of six on set 2". The case entries elsewhere in the doc record the lock as committed and pushed before probing, for example "pre-25 passes probe set 1 … The lock committed and pushed". Row 3 adds a caveat: closure-19's foreshadow-2.json was "run after set 2's probe, so it is a record made late, not a check before the lock".
claim 2: Confirmed: part A item 3 says the window's protection is "replaced in steps 3 and 4 by a knowledge probe". "Each of v1's two official models" appears in step 3 item 4, not in item 3 itself.
claim 3: Confirmed: on /cases/ exactly three entries carry "first disclosed before the main model's training cut-off … admitted after a knowledge probe". The same three are the step 3 and 4 cases in cases.json.
status: met: each case has a dossier, a rubric read by the independent reader and a recognition probe, with the closure-19 coarsening and the late foreshadow record disclosed.

ITEM C16

claim 1: Confirmed with a location caveat. L951 is the heading "12.7 The rubric and the matcher", and the rubric is "committed before any model sees the case". The freeze is in section 11.4: thresholds are "frozen in matcher_thresholds.toml". Section 2.6 lists that file among the analysis code hashed by prereg.lock.
claim 2: Confirmed: row 2 of the DoD audit says "All 20 readings no good match".
claim 3: Confirmed: the methods page says "Two behaviors of the frozen matcher show in the case results". They are the letter-order nearest-goal pick when all five goals are equally far, and the one-observable-line reading (closure-19's second reading) that pulls toward a match. The section anchor #real-cases was not found on the page; I only read the text.
status: met: the matcher was frozen before any real case and the "no good match" outcomes and its two quirks are disclosed.

ITEM D1

claim 1: Confirmed: the release page shows prereg-v1 at 649e8b9, titled "prereg-v1: protocol v1". The release is dated 2026-10-13T06:29:56Z and the commit 2026-10-13T06:19:15Z, and the tags page shows the same commit and date.
claim 2: Confirmed: row 2 says "both grid sessions started 09:52:25 and 09:52:27 UTC" on 2026-10-14, after projection.md was committed at 09:44:55 UTC.
claim 3: Confirmed: section 7 of tag-record.md shows dry runs refused as "content differs", "instrument differs", "analysis differs", "document differs" and "model haiku-5-5 differs from prereg-v1: model id is…".
claim 4: Confirmed: section 2.4 discloses the second family's development runs (50 probe calls and 122 decision calls), read only through blind reports. Section 2.7 says "No allocation, choice or memo from any run on the company's content has been read by either author."
status: met: the tag predates the official runs and the harness refuses changed content, instrument, analysis, document and model identity.

ITEM D2

claim 1: Confirmed: record-checks.md lists content | pass, model | pass and request | pass, and says "Result: every check passes."
claim 2: Confirmed: test_provenance_names_the_request_the_served_model_and_sets_no_sampling is at L231. It asserts provider, api, route kind, model id, served_model and request_id.
status: met: provenance is recorded per call, checked by record checks and covered by a test.

ITEM D3

claim 1: Confirmed: store.py has one put_object (L65) with IfNoneMatch="*" at L70. The docstring says a 412 "means the key exists: never an overwrite".
claim 2: Confirmed: test_results_bucket_is_write_once_and_cannot_be_destroyed at L341 asserts prevent_destroy = true, no force_destroy, no lifecycle configuration, and the s3:if-none-match, s3:if-match and s3:DeleteObjectVersion policy terms.
status: met: the harness and the bucket policy both enforce write-once, and a test covers the bucket.

ITEM D5

claim 1: Confirmed: anthropic.py sets one entry in body["tools"] (L229) and tool_choice = {"type": "auto"} (L236). openrouter.py sends one function tool with "tool_choice": "auto" (L220).
status: met: both provider code paths build one tool with auto choice.

ITEM D6

claim 1: Confirmed: experiment/company holds dossier.toml, objectives.toml, figures.toml, sources.toml, scenario-figures.toml, CHANGELOG.toml, a dossier.template.txt and scenarios/ and probes/ folders.
claim 2: Confirmed: prereg.lock records the protocol document's sha256 and has 6 lines naming company/ content.
claim 3: Confirmed: record-checks.md shows content | pass.
status: met: the content is versioned data files, hashed by the lock and checked by the "content" record check.

ITEM D7

claim 1: Confirmed: .pre-commit-config.yaml has name-guard at L21 (pre-commit stage) and name-guard-message at L31 (commit-msg stage).
claim 2: Confirmed: line 3 of .gitignore is methods-appendix/.
claim 3: Confirmed: rule-zero.md shows "name guard: history clean, 177 commit(s) scanned." It also lists ten binary files the guard did not scan (video, poster, fonts, screenshots), which it says were read as images or carry no text. A surfaces table (repo description, releases, issues, PRs, branches, tags) reads "clean".
status: met: the guards, the ignore rule and the hand-read evidence are all there, though I could not independently verify that no real name exists in the repo.

ITEM E6

claim 1: Confirmed: KNOWN-GAPS.md has "## CARRIED — from Phase 0.5 to Phase 1, 2026-10-04" (L4484), while other entries on the page are headed CLOSED. Phase 1.5 is recorded there as closed on 2026-11-08.
claim 2: Confirmed: classify.py L75 says "Carried from Phase 0.5: Bedrock reports a malformed tool call as ModelErrorException". L76 maps ModelErrorException to _MALFORMED_CODES, and L117–118 return Outcome("malformed_tool_use", retry="model"). malformed_tool_use is in RETRYABLE_MODEL_STATUSES, so it is not in NON_MODEL_STATUSES.
claim 3: Contradicted as worded: iam.tf defines a boundary policy described as "Permissions boundary for every role the deploy role creates". aws_iam_role.github_deploy in oidc.tf has no permissions_boundary attribute. Its comment says "Phase 1 attaches permissions, with a permissions boundary". The boundary exists, but it limits the roles the deploy role creates.
status: partial: the classifier item landed, but the deploy-role boundary lands on created roles, not the deploy role itself. I could not check the other carried items: text beside a tool call not being no_tool_call, thinking tokens inside outputTokens, the refusal stop_details question, and the tool-use overhead.

I did not change anything, sign in or submit anything. I read the raw files by navigating the open tab, which is back on the methods page.
