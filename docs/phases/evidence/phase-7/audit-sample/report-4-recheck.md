# Report, re-check batch (verbatim)

Claude in Chrome, Sonnet 5.5 at the panel's default effort, a new conversation with `brief-4-recheck.md` as its only
input, 2026-11-24, ending about 1:30 PM CST. Run by him; pasted back as given. His one-line greeting to the agent and
the panel's list of page loads and scripts before the reply are left out; the reply follows exactly.

---

ITEM A2

claim 1: Confirmed: cases.json lists five cases (closure-07, closure-19, pre-11, pre-25, pre-224). Each has "type": "closure" and "exploratory": true. short_by_type reads "closure": 0, "retool": 2, "ai": 1.
claim 2: Confirmed: every case has reidentification.status "withheld" and dossier.published false, each with a reason. Four have published descriptions and pre-11's is "status": "withheld" ("a search found the company at the first level and again after one coarsening"). Phase 5.5 doc §14 row 4 says "all five dossiers withheld with their reasons; four descriptions published after their searches, pre-11's withheld". The searches themselves are in a private appendix, so I could not check that they found no company. For pre-25 the reason is "could not confirm the case in SEC's structured data", not a failed check.
claim 3: Confirmed: the ROADMAP Phase 5 row says "At least three cases run and matched, including an invest or retool case". It records "no retool or ai case, so the 'invest or retool' part of the done-when is not met". 05-EVOLUTION-PLAN L186 (Phase 5 row) reads "At least three cases run and matched, including the invest or retool case".
claim 4: Confirmed: phase-5-case-building-search doc L517 says "The pre-registered rule found no case in any type". The L510 heading is "exploratory cases, after the pre-registered rule found none". Each case's exploratory_label names a §4.6.5 step 2, 3 or 4 selection.
status: partial: five anonymized cases were run and shown by type, which covers "at least three". But all are closure and exploratory, none came from the rule, and the finalized done-when's invest or retool case is missing.

ITEM A5b

claim 1: Confirmed: store.py L1 says "Every write is exclusive", and L70 inside put_object is IfNoneMatch="*". L3-4 add that the bucket policy refuses a put without the header.
claim 2: Confirmed: protocol-v1.md L1036 reads "Raw responses are kept write-once, one object per attempt, with full provenance on every call."
claim 3: Confirmed: record-checks.md says "Result: every check passes", with complete | pass. The image row is "reported", not "pass".
status: met: sweep outputs are written to S3 write-once, and the manifest lists 5,247 raw objects under official/ and pilot/.

ITEM A6

claim 1: Confirmed: raw-manifest.json shows "object_count": 5247, with prefixes official/ and pilot/. test_analysis_rescoring.py re-runs the frozen analysis on the published raw records and fails "if anything opens an AWS client". It says a reader "with a clone and no account can repeat every one".
claim 2: Confirmed: cases.json has dossier.published false for all five. The methods page has a "Why no case can be re-run" section: "Each dossier is withheld because its figures, with the scale removed, match fewer than 20 companies… or could not be confirmed to match more." It also says "any real case, since no dossier is published".
claim 3: Confirmed: KNOWN-GAPS (CLOSED 2026-11-04 entry) says "Measured 2026-11-04… only Phase 5.5's image (sha256:ef0588f9...) still exists. The Phase 4 official image (sha256:ff978703...) and Phase 1's skeleton image (sha256:ef2582ed...) have expired". record-checks.md lists ff978703… as the single digest for the pilot, awareness, grid and thinking sweeps. I did not find a line saying the skeleton image "ran no official sweep", only that no Phase 4 sweep used it.
status: partial: the made-up company's runs can be re-scored from published records, and the page says no real case can be re-run. But the real-case dossiers are not published, so the promised re-run "including the anonymized real-case dossiers" is not possible, and no run can be repeated in its identical image.

ITEM B65

claim 1: Confirmed: the §11.1 table has "yes" in all eleven Met cells. Row 5 reads "yes, with two logged departures and two disclosures", row 6 "yes, with two qualifications", and row 10 "yes, closed with this commit".
claim 2: Confirmed: row 5 says the video "came from a script Claude wrote (a departure from §6 item 1) and is shown with one edit (a departure from item 4)". It says "attempt 4 passed on every figure" and the "Captions (59 cues)" were checked.
claim 3: Confirmed: §9 row 6 reads "Every §9 check passes on every surface". The audit says "check 6 passes on / and is accepted as absent on the cards and the video (his decision)". It also says "check 4 is his one read ('fine for now'), not four reads with notes".
status: partial: the audit marks every row "yes", but row 6 (every check on every surface) was met only with two accepted exceptions.

ITEM C6

claim 1: Confirmed: Phase 3 doc §19a row 3 says "the bootstrap's false split (worst 2.22%) was patched out (Welch, planning/07 §6.3)". The audit is dated 2026-10-09, and the methods page says the protocol was tagged prereg-v1 on October 13, 2026. So the change came before the tag.
claim 2: Confirmed: row 3 reads "0.43% worst, 5 of 360 points clearly over 0.3125%" and "49.7% at worst against about 54% stated". The methods page reads "the worst case was 0.43% for shares and 0.417% for choice rates" and "at least 49.7% of the time… against about 54% the plan expected". It also says the false-split chance is "held approximately, not exactly".
status: partial: the interval method was fixed before the tag and the false-split target is held only approximately, at worst 0.43% against 0.3125%. No-split reachability is 49.7% at its worst point against the roughly 54% stated.

ITEM E6

claim 1: Confirmed: KNOWN-GAPS.md L4484 is headed "## CARRIED from Phase 0.5 to Phase 1, 2026-10-04". It has no closing note, though other entries are headed CLOSED.
claim 2: Confirmed: classify.py L75-76 read "Carried from Phase 0.5: Bedrock reports a malformed tool call as ModelErrorException" and _MALFORMED_CODES = frozenset({"ModelErrorException"}). malformed_tool_use appears at L28 and L46. I did not read the code that uses the set.
claim 3: Confirmed: iam.tf L23-25 defines aws_iam_policy "boundary" with "Permissions boundary for every role the deploy role creates". In oidc.tf the github_deploy role has no permissions_boundary attribute, and its comment says "NO PERMISSION POLICY… Phase 1 attaches permissions, with a permissions boundary".
status: partial: the classifier and deploy-role boundary items landed. The Nova, model-route and token items are Bedrock-specific, and the project dropped Bedrock (entry "CLOSED 2026-10-12": "Nova Lite left with Bedrock"). But I did not check the remaining items (thinking tokens, refusal stop_details, tool-use overhead), and the entry was never updated or closed.
