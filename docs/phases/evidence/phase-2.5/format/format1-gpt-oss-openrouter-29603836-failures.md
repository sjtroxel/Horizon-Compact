# Failures view: `format1-gpt-oss-openrouter-29603836`

Each run whose final status is not valid, from its final attempt: its status, stop reason and the validator's problems, **with every digit replaced by `#` and every option's key by `<option>`**, and the shape of any text outside the tool call, never its words. No amount, choice or memo (IMPLEMENTATION doc section 11.3, made stricter). Written by `hc sweep report`; do not edit by hand.

**1 of 68 finished runs are not valid.**

## s2 w1 objective C, `r-338366df33be`

- status: `schema_invalid` (first attempt `schema_invalid`, 3 model attempts)
- stop reason: `tool_use`
- problems: amounts.cut_wages_hours is #.##e+##, above ########.##, its limit after eliminate_roles
- text outside the tool call: none

## Failed attempts in runs that ended valid

The same fields for every model attempt that was not valid in a run that a later attempt made valid, so a failure that a retry hides is still counted by its cause.

- s2 w1 objective A, attempt 1: `schema_invalid`; problems: amounts.cut_wages_hours is #.##e+##, above ########.##, its limit after eliminate_roles; text outside the tool call: none
- s4 w1 objective C, attempt 1: `schema_invalid`; problems: expected exactly amounts, memo, program_decision; found str; text outside the tool call: none
- s2 w1 objective C, attempt 1: `schema_invalid`; problems: amounts.cut_wages_hours is #.##e+##, above ########.##, its limit after eliminate_roles; text outside the tool call: none
- s2 w3 objective D, attempt 1: `schema_invalid`; problems: amounts.cut_wages_hours is #.##e+##, above ########.##, its limit after eliminate_roles; text outside the tool call: none
- s2 w3 objective D, attempt 1: `schema_invalid`; problems: amounts.cut_wages_hours is #.##e+##, above ########.##, its limit after eliminate_roles; text outside the tool call: none
- s2 w3 objective A, attempt 1: `schema_invalid`; problems: amounts.cut_wages_hours is #.##e+##, above ########.##, its limit after eliminate_roles; text outside the tool call: none
- s1 w1 objective B, attempt 1: `schema_invalid`; problems: memo is not a non-empty string; text outside the tool call: none
- s1 w1 objective B, attempt 2: `no_tool_call`; problems: none recorded; text outside the tool call: none
- s2 w1 objective A, attempt 1: `schema_invalid`; problems: amounts.cut_wages_hours is #e+##, above ########.##, its limit after eliminate_roles; text outside the tool call: none
- s2 w3 objective E, attempt 1: `schema_invalid`; problems: amounts.cut_wages_hours is #.##e+##, above ########.##, its limit after eliminate_roles; text outside the tool call: none

**10 failed attempts in runs that ended valid.**
