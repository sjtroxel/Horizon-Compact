# Failures view: `proxy-haiku-5-5-70ef2152`

Each run whose final status is not valid, from its final attempt: its status, stop reason and the validator's problems, **with every digit replaced by `#` and every option's key by `<option>`**, and the shape of any text outside the tool call, never its words. No amount, choice or memo (IMPLEMENTATION doc section 11.3, made stricter). Written by `hc sweep report`; do not edit by hand.

**0 of 60 finished runs are not valid.**

## Failed attempts in runs that ended valid

The same fields for every model attempt that was not valid in a run that a later attempt made valid, so a failure that a retry hides is still counted by its cause.

- garden_s4 w1, attempt 1: `sum_mismatch`; problems: uses total #, against ###; text outside the tool call: 274 words; reads as a decline: no; names the tool: no
- garden_s3 w1, attempt 1: `schema_invalid`; problems: amounts.moved_hollin is ###, above its maximum ##; text outside the tool call: 335 words; reads as a decline: no; names the tool: no
- garden_s2 w1, attempt 1: `schema_invalid`; problems: amounts keys differ from the offered lines (missing [], extra ['keep_beds']); text outside the tool call: 213 words; reads as a decline: no; names the tool: no
- garden_s3 w1, attempt 1: `schema_invalid`; problems: amounts.moved_hollin is ###, above its maximum ##; text outside the tool call: 322 words; reads as a decline: no; names the tool: no

**4 failed attempts in runs that ended valid.**
