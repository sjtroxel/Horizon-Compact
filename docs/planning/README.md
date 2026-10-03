# Planning

The design of Horizon Compact, written before any code and **closed on 2026-10-03**. These documents stay the
authority for every design decision. A change after that date is a dated patch, noted in the changed
document's status line.

DISCLOSURE LINE: This is sjtroxel typing. While Claude has generated virtually all of the prose (not this particular line) and code in the project it was all - every line, every decision, every judgment - architected, orchestrated, and otherwise owned by me. This project and all my others are my work product and I reserve all rights accordingly. Have a great day!    --sjtroxel, 10/03/26.

## Read order

| # | Document | What it settles |
|---|---|---|
| 00 | [Design brief](00-DESIGN-BRIEF.md) | What the experiment is, what it is not, the definition of done for v1 |
| 01 | [Data sources](01-DATA-SOURCES.md) | The fictional company's sources, and how real cases are found and anonymized |
| 02 | [Architecture](02-ARCHITECTURE.md) | The harness, provenance, AWS shape, what is deliberately left out |
| 03 | [Cost model](03-COST-MODEL.md) | What each part costs, and the spending caps |
| 04 | [Risk register](04-RISK-REGISTER.md) | What could make the result meaningless, and the mitigation for each |
| 05 | [Evolution plan](05-EVOLUTION-PLAN.md) | The phase order, and the order of operations that keeps results unseen until the protocol is fixed |
| 06 | [Narrative and vocabulary](06-NARRATIVE-AND-VOCABULARY.md) | How results are described, the words avoided, the visual direction |
| 07 | [Eval spec](07-EVAL-SPEC.md) | The design of the pre-registration: comparisons, thresholds, repeats |
| 08 | [Review](08-REVIEW.md) | An independent review of `00`-`07`, and what was changed because of it |
| 09 | [Priorities and open decisions](09-PRIORITIES-AND-OPEN-DECISIONS.md) | The patch list, building assignments, and the path to the first commit |

**Records, not part of the read order:** [08a](08a-REVIEW-BRIEF-gpt-6-astra.md) is the brief given to the
independent reviewer, and [08b](08b-REVIEW-RAW-gpt-6-astra.md) is that reviewer's raw reply, unedited. They show
how the review in `08` was made.

The build's current state is in [`../ROADMAP.md`](../ROADMAP.md) and [`../KNOWN-GAPS.md`](../KNOWN-GAPS.md).
