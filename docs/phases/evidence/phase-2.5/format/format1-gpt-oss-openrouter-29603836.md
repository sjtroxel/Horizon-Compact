# Format report: `format1-gpt-oss-openrouter-29603836`

Experiment `company`, model `gpt-oss-openrouter`, content hash `5bd849beef0d`, templates w1, w3, 3 repeats. Written by `hc sweep report` from the stored records; do not edit by hand. **Blind:** no amount, choice, memo or line appears here, and per objective only valid against not valid (IMPLEMENTATION doc section 11.3). A cell passes with at least one valid run (section 11.2).

| Scenario | Template | Runs | Finished | Valid | Of which rescaled | Valid on the first attempt | Not valid, by type |
|---|---|---|---|---|---|---|---|
| s1 | w1 | 15 | 6 | 6 | 0 | 5 | none |
| s1 | w3 | 15 | 5 | 5 | 0 | 5 | none |
| s2 | w1 | 15 | 12 | 11 | 0 | 8 | schema_invalid 1 |
| s2 | w3 | 15 | 10 | 10 | 0 | 6 | none |
| s3 | w1 | 15 | 9 | 9 | 0 | 9 | none |
| s3 | w3 | 15 | 9 | 9 | 0 | 9 | none |
| s4 | w1 | 15 | 8 | 8 | 0 | 7 | none |
| s4 | w3 | 15 | 9 | 9 | 0 | 9 | none |

## Valid runs per objective

| Scenario | Template | A | B | C | D | E |
|---|---|---|---|---|---|---|
| s1 | w1 | 1 of 1 | 1 of 1 | 0 of 0 | 3 of 3 | 1 of 1 |
| s1 | w3 | 1 of 1 | 1 of 1 | 1 of 1 | 1 of 1 | 1 of 1 |
| s2 | w1 | 2 of 2 | 2 of 2 | 1 of 2 | 3 of 3 | 3 of 3 |
| s2 | w3 | 1 of 1 | 2 of 2 | 1 of 1 | 3 of 3 | 3 of 3 |
| s3 | w1 | 1 of 1 | 3 of 3 | 2 of 2 | 0 of 0 | 3 of 3 |
| s3 | w3 | 1 of 1 | 1 of 1 | 1 of 1 | 3 of 3 | 3 of 3 |
| s4 | w1 | 1 of 1 | 1 of 1 | 2 of 2 | 1 of 1 | 3 of 3 |
| s4 | w3 | 1 of 1 | 2 of 2 | 2 of 2 | 2 of 2 | 2 of 2 |

**Runs finished: 68 of 120.** Every finished cell has at least one valid run.
