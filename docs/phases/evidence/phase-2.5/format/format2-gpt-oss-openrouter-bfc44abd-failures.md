# Failures view: `format2-gpt-oss-openrouter-bfc44abd`

Each run whose final status is not valid, from its final attempt: its status, stop reason and the validator's problems, **with every digit replaced by `#` and every option's key by `<option>`**, and the shape of any text outside the tool call, never its words. No amount, choice or memo (IMPLEMENTATION doc section 11.3, made stricter). Written by `hc sweep report`; do not edit by hand.

**0 of 40 finished runs are not valid.**

## Failed attempts in runs that ended valid

The same fields for every model attempt that was not valid in a run that a later attempt made valid, so a failure that a retry hides is still counted by its cause.

- s2 w1, attempt 1: `schema_invalid`; problems: amounts.cut_wages_hours is #.##e+##, above ########.##, its limit after eliminate_roles; text outside the tool call: none
- s4 w3, attempt 1: `no_tool_call`; problems: none recorded; text outside the tool call: 255 words; reads as a decline: yes; names the tool: no

**2 failed attempts in runs that ended valid.**
