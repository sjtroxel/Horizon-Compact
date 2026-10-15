# Record checks

Protocol `prereg-v1`; tree `8eb3d43cd761`; made 2026-10-15T00:18:23Z. Written by `hc protocol records`; do not edit by hand. Counts, ids, hashes and dates only: no decision, choice, memo or reply is read or shown.

**Result: every check passes.**

| check | result |
|---|---|
| content | pass |
| model | pass |
| labels | pass |
| container | pass |
| image | reported |
| request | pass |
| complete | pass |
| sealed first | pass |
| after the tag | pass |
| frozen files | pass |

## image

- pilot pilot-gpt-oss-openrouter-1f75b653: 1 image digest(s): sha256:ff978703e4b6ae30fd6d4b2cd7a65670a2754a6b6623a1dfc5f1683229436723
- pilot pilot-haiku-5-5-0b9d9e79: 1 image digest(s): sha256:ff978703e4b6ae30fd6d4b2cd7a65670a2754a6b6623a1dfc5f1683229436723
- official awareness-gpt-oss-openrouter-6a05acef: 1 image digest(s): sha256:ff978703e4b6ae30fd6d4b2cd7a65670a2754a6b6623a1dfc5f1683229436723
- official awareness-haiku-5-5-0ce6ad12: 1 image digest(s): sha256:ff978703e4b6ae30fd6d4b2cd7a65670a2754a6b6623a1dfc5f1683229436723
- official grid-gpt-oss-openrouter-fe599ad2: 1 image digest(s): sha256:ff978703e4b6ae30fd6d4b2cd7a65670a2754a6b6623a1dfc5f1683229436723
- official grid-haiku-5-5-0b99fabb: 1 image digest(s): sha256:ff978703e4b6ae30fd6d4b2cd7a65670a2754a6b6623a1dfc5f1683229436723
- official thinking-haiku-5-5-418caa9c: 1 image digest(s): sha256:ff978703e4b6ae30fd6d4b2cd7a65670a2754a6b6623a1dfc5f1683229436723

## Run counts, per sweep (protocol 13.2)

| role | sweep | label | model | runs | finished | calls | calls by status | sessions | cost (USD) |
|---|---|---|---|---|---|---|---|---|---|
| pilot | `pilot-gpt-oss-openrouter-1f75b653` | pilot | gpt-oss-openrouter | 80 | 80 | 95 | {'api_error': 3, 'schema_invalid': 15, 'sum_mismatch': 1, 'valid': 76} | 1 | 0.0368 |
| pilot | `pilot-haiku-5-5-0b9d9e79` | pilot | haiku-5-5 | 80 | 80 | 94 | {'schema_invalid': 5, 'sum_mismatch': 10, 'valid': 79} | 1 | 0.1314 |
| official | `awareness-gpt-oss-openrouter-6a05acef` | awareness | gpt-oss-openrouter | 15 | 15 | 15 | {'replied': 15} | 0 | 0.0028 |
| official | `awareness-haiku-5-5-0ce6ad12` | awareness | haiku-5-5 | 15 | 15 | 15 | {'replied': 15} | 0 | 0.0107 |
| official | `grid-gpt-oss-openrouter-fe599ad2` | grid | gpt-oss-openrouter | 1200 | 1200 | 1333 | {'api_error': 11, 'no_tool_call': 15, 'schema_invalid': 125, 'sum_mismatch': 10, 'truncated': 10, 'unexpected_stop': 1, 'valid': 1158, 'valid_rescaled': 3} | 2 | 0.5422 |
| official | `grid-haiku-5-5-0b99fabb` | grid | haiku-5-5 | 990 | 990 | 1128 | {'schema_invalid': 14, 'sum_mismatch': 134, 'valid': 980} | 1 | 1.5750 |
| official | `thinking-haiku-5-5-418caa9c` | thinking | haiku-5-5 | 100 | 100 | 100 | {'valid': 100} | 1 | 0.3688 |
