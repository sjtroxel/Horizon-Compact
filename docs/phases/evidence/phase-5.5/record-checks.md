# Record checks, case sweeps

Protocol `prereg-v1`; tree `fecd23dffb1f plus uncommitted changes`; made 2026-10-30T17:20:51Z. Written by `hc protocol records --cases`; do not edit by hand. Exploratory cases (Phase 5.5 IMPLEMENTATION doc section 0). Counts, ids, hashes and dates only: no objective, allocation, choice, memo or reply is read or shown.

**Result: every check passes.**

| check | result |
|---|---|
| cases | pass |
| one sweep | pass |
| case plan | pass |
| seed | pass |
| case content | pass |
| order | pass |
| model | pass |
| container | pass |
| image | reported |
| request | pass |
| complete | pass |
| after the freeze | pass |
| frozen files | pass |

## image

- case closure-07/case-gpt-oss-openrouter-90dc7f0d: 1 image digest(s): sha256:ef0588f95b3fbf6fc5960a863dec11ac775a4fca23a2a49734736baa809baec7
- case closure-07/case-haiku-5-5-9119a8cd: 1 image digest(s): sha256:ef0588f95b3fbf6fc5960a863dec11ac775a4fca23a2a49734736baa809baec7
- case closure-19/case-gpt-oss-openrouter-1e058732: 1 image digest(s): sha256:ef0588f95b3fbf6fc5960a863dec11ac775a4fca23a2a49734736baa809baec7
- case closure-19/case-haiku-5-5-3d85ff31: 1 image digest(s): sha256:ef0588f95b3fbf6fc5960a863dec11ac775a4fca23a2a49734736baa809baec7
- case pre-11/case-gpt-oss-openrouter-e3ccf78f: 1 image digest(s): sha256:ef0588f95b3fbf6fc5960a863dec11ac775a4fca23a2a49734736baa809baec7
- case pre-11/case-haiku-5-5-13fab9d7: 1 image digest(s): sha256:ef0588f95b3fbf6fc5960a863dec11ac775a4fca23a2a49734736baa809baec7
- case pre-25/case-gpt-oss-openrouter-eb1036dc: 1 image digest(s): sha256:ef0588f95b3fbf6fc5960a863dec11ac775a4fca23a2a49734736baa809baec7
- case pre-25/case-haiku-5-5-30276496: 1 image digest(s): sha256:ef0588f95b3fbf6fc5960a863dec11ac775a4fca23a2a49734736baa809baec7
- case pre-224/case-gpt-oss-openrouter-2b24bdc9: 1 image digest(s): sha256:ef0588f95b3fbf6fc5960a863dec11ac775a4fca23a2a49734736baa809baec7
- case pre-224/case-haiku-5-5-a7525775: 1 image digest(s): sha256:ef0588f95b3fbf6fc5960a863dec11ac775a4fca23a2a49734736baa809baec7

## Run counts, per sweep (protocol 13.2)

| case | sweep | model | runs | finished | calls | calls by status | sessions | cost (USD) |
|---|---|---|---|---|---|---|---|---|
| closure-07 | `case-gpt-oss-openrouter-90dc7f0d` | gpt-oss-openrouter | 150 | 150 | 150 | {'valid': 150} | 1 | 0.0426 |
| closure-07 | `case-haiku-5-5-9119a8cd` | haiku-5-5 | 150 | 150 | 151 | {'schema_invalid': 1, 'valid': 150} | 1 | 0.1667 |
| closure-19 | `case-gpt-oss-openrouter-1e058732` | gpt-oss-openrouter | 150 | 150 | 156 | {'api_error': 6, 'valid': 150} | 1 | 0.0381 |
| closure-19 | `case-haiku-5-5-3d85ff31` | haiku-5-5 | 150 | 150 | 151 | {'schema_invalid': 1, 'valid': 150} | 1 | 0.1459 |
| pre-11 | `case-gpt-oss-openrouter-e3ccf78f` | gpt-oss-openrouter | 150 | 150 | 321 | {'api_error': 164, 'no_tool_call': 7, 'valid': 150} | 3 | 0.0482 |
| pre-11 | `case-haiku-5-5-13fab9d7` | haiku-5-5 | 150 | 150 | 151 | {'schema_invalid': 1, 'valid': 150} | 1 | 0.1861 |
| pre-25 | `case-gpt-oss-openrouter-eb1036dc` | gpt-oss-openrouter | 150 | 150 | 213 | {'api_error': 63, 'valid': 150} | 1 | 0.0446 |
| pre-25 | `case-haiku-5-5-30276496` | haiku-5-5 | 150 | 150 | 154 | {'schema_invalid': 4, 'valid': 150} | 1 | 0.1871 |
| pre-224 | `case-gpt-oss-openrouter-2b24bdc9` | gpt-oss-openrouter | 150 | 150 | 244 | {'api_error': 94, 'valid': 150} | 1 | 0.0420 |
| pre-224 | `case-haiku-5-5-a7525775` | haiku-5-5 | 150 | 150 | 151 | {'schema_invalid': 1, 'valid': 150} | 1 | 0.1660 |
