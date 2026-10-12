# Failures view: `proxy-gpt-oss-openrouter-5ead7b2e`

Each run whose final status is not valid, from its final attempt: its status, stop reason and the validator's problems, **with every digit replaced by `#` and every option's key by `<option>`**, and the shape of any text outside the tool call, never its words. No amount, choice or memo (IMPLEMENTATION doc section 11.3, made stricter). Written by `hc sweep report`; do not edit by hand.

**0 of 60 finished runs are not valid.**

## Failed attempts in runs that ended valid

The same fields for every model attempt that was not valid in a run that a later attempt made valid, so a failure that a retry hides is still counted by its cause.

- garden_s4 w1, attempt 1: `schema_invalid`; problems: expected exactly amounts, display_decision, memo; found ['amounts']; text outside the tool call: none
- garden_s4 w1, attempt 1: `sum_mismatch`; problems: uses total ####, against ####; text outside the tool call: none
- garden_s4 w1, attempt 2: `sum_mismatch`; problems: uses total ####, against ####; text outside the tool call: none

**3 failed attempts in runs that ended valid.**
