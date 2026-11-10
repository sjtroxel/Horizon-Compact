import { describe, expect, it } from "vitest";
import { againstWords } from "./againstWords";
import { explorerLabels } from "./copy";
import type { Comparison } from "./data";
import { realGrids } from "./fixtures";
import { resultSentence, TEMPLATE_IDS } from "./sentences";
import type { SentenceInput } from "./sentences";

const names = explorerLabels.objectiveNames;
const outcome = "the rate of doing the thing";

function input(over: Partial<SentenceInput>): SentenceInput {
  return {
    first: "C",
    second: "D",
    final_verdict: "split",
    difference: -0.398,
    downgrade_reason: null,
    dropped_wordings: [],
    ...over,
  };
}

describe("the result-sentence templates", () => {
  it("split: names the direction by the sign of first minus second, and the points rounded down", () => {
    expect(resultSentence(input({ difference: -0.398 }), names, outcome)).toEqual({
      id: "split",
      text: "“Shareholders, long term” and “Everyone with a stake, long term” came out different: the rate of doing the thing was about 39 points lower under “Shareholders, long term”.",
    });
    expect(resultSentence(input({ difference: 0.25 }), names, outcome).text).toContain(
      "about 25 points higher under",
    );
  });

  it("split: corrects float noise before rounding down", () => {
    expect(resultSentence(input({ difference: 0.29999999999999993 }), names, outcome).text).toContain(
      "about 30 points higher",
    );
  });

  it("no_split: says it is about this one measure, never that the decisions were the same", () => {
    const { id, text } = resultSentence(input({ final_verdict: "no_split", difference: 0 }), names, outcome);
    expect(id).toBe("no_split");
    expect(text).toBe(
      "“Shareholders, long term” and “Everyone with a stake, long term” came out about the same on the rate of doing the thing. That is about this one measure, not every choice they made.",
    );
    expect(text).not.toMatch(/same decision/i);
  });

  it("inconclusive: says the runs can't tell", () => {
    expect(
      resultSentence(input({ final_verdict: "inconclusive", difference: 0.05 }), names, outcome),
    ).toEqual({
      id: "inconclusive",
      text: "The runs can’t tell whether “Shareholders, long term” and “Everyone with a stake, long term” differ on the rate of doing the thing.",
    });
  });

  it("not_assessable: names the reason and the dropped wordings, and claims no run count", () => {
    const { id, text } = resultSentence(
      input({
        final_verdict: "not_assessable",
        difference: null,
        downgrade_reason: "every wording has a cell over the 10% failure limit",
        dropped_wordings: [
          { wording_id: "w1", cells: [] },
          { wording_id: "w2", cells: [] },
          { wording_id: "w3", cells: [] },
        ],
      }),
      names,
      outcome,
    );
    expect(id).toBe("not_assessable");
    expect(text).toContain("every wording has a cell over the 10% failure limit");
    expect(text).toContain("Wordings dropped: w1, w2 and w3.");
    expect(text).not.toMatch(/\b\d+ (runs?|valid)/);
    expect(
      resultSentence(input({ final_verdict: "not_assessable", downgrade_reason: null }), names, outcome).text,
    ).not.toMatch(/\(|Wordings dropped/);
  });

  it("uses a goal's letter when the names do not know it", () => {
    expect(resultSentence(input({ first: "Z", second: "D" }), names, outcome).text).toContain("“Z”");
  });

  it("gives every comparison in every real file the template of its own verdict", () => {
    const seen = new Set<string>();
    for (const { label, file } of realGrids) {
      for (const c of file.comparisons) {
        const sentence = resultSentence(c, names, explorerLabels.outcomePhrases[file.scenario_id]!);
        expect(sentence.id, `${label} ${c.first}-${c.second}`).toBe(c.final_verdict);
        expect(TEMPLATE_IDS).toContain(sentence.id);
        seen.add(sentence.id);
      }
    }
    expect([...seen].sort()).toEqual([...TEMPLATE_IDS].sort()); // the real data exercises all four
  });

  it("writes the real not-assessable comparison from its own fields", () => {
    const file = realGrids.find((g) => g.label === "grid gpt-oss-openrouter s2")!.file;
    const c = file.comparisons.find((x): x is Comparison & typeof x => x.final_verdict === "not_assessable")!;
    expect(resultSentence(c, names, explorerLabels.outcomePhrases["s2"]!).text).toBe(
      "Too many runs failed in every wording to compare “Shareholders, short term” and “Shareholders, long term” on the share of the shortfall borne by the workforce (every wording has a cell over the 10% failure limit). Wordings dropped: w1, w2 and w3.",
    );
  });
});

describe("the words Claude drafted for the rule and the templates", () => {
  it("avoid the words the page must not carry", () => {
    const text = JSON.stringify([againstWords, TEMPLATE_IDS]).toLowerCase();
    for (const word of [
      "insight",
      "powered by",
      "unlock",
      "seamless",
      "delve",
      "leverage",
      "robust",
      "esg",
    ]) {
      expect(text).not.toContain(word);
    }
    expect(text).not.toContain("stakeholder capitalism");
  });
});
