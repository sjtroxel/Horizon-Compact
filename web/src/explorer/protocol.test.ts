import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { PROTOCOL_READINGS, readingFor } from "./protocol";
import type { ReadingKey } from "./protocol";
import { WEB_ROOT, realGrids } from "./fixtures";

const protocol = readFileSync(resolve(WEB_ROOT, "../experiment/protocol/protocol-v1.md"), "utf8");
const TABLE_HEADER = "| If, on a scenario's primary outcome, the results show | Then |";

/** The rows of protocol 1.5's table "What each pattern would mean", after its header and rule. */
function tableRows(): string[] {
  const lines = protocol.split("\n");
  const at = lines.indexOf(TABLE_HEADER);
  expect(at, "the protocol's table header").toBeGreaterThan(-1);
  const rows: string[] = [];
  for (const line of lines.slice(at + 2)) {
    if (!line.startsWith("|")) break;
    rows.push(line);
  }
  return rows;
}

describe("the protocol's readings", () => {
  it("quote every pattern and every reading character for character, from the file on disk", () => {
    for (const [key, { pattern, reading }] of Object.entries(PROTOCOL_READINGS)) {
      expect(protocol, `${key} pattern`).toContain(pattern);
      expect(protocol, `${key} reading`).toContain(reading);
    }
  });

  it("take each pattern and its reading from one row of the table, and cover every row there is", () => {
    const rows = tableRows();
    expect(rows).toHaveLength(Object.keys(PROTOCOL_READINGS).length);
    for (const [key, { pattern, reading }] of Object.entries(PROTOCOL_READINGS)) {
      const matching = rows.filter((row) => row.includes(`**${pattern}**`));
      expect(matching, key).toHaveLength(1);
      expect(matching[0], key).toContain(`| ${reading} |`);
    }
  });
});

describe("which reading applies", () => {
  it("gives C vs D the row of its verdict, and nothing when it could not be assessed", () => {
    expect(readingFor("C", "D", "no_split", null)).toBe("cd_no_split");
    expect(readingFor("C", "D", "split", null)).toBe("cd_split");
    expect(readingFor("C", "D", "inconclusive", null)).toBe("cd_inconclusive");
    expect(readingFor("C", "D", "not_assessable", null)).toBeNull();
  });

  it("gives A vs B its no-split row, and the pulled-apart row only when C vs D is a no split", () => {
    expect(readingFor("A", "B", "no_split", "split")).toBe("ab_no_split");
    expect(readingFor("A", "B", "split", "no_split")).toBe("ab_split_cd_not");
    // Protocol 6.3: a no split "has to be shown, never assumed from the absence of a split". An inconclusive C vs D
    // does not show one, and the row's reading says "not at twenty years" (Opus review, section 26a).
    expect(readingFor("A", "B", "split", "inconclusive")).toBeNull();
    expect(readingFor("A", "B", "split", "split")).toBeNull();
    expect(readingFor("A", "B", "split", "not_assessable")).toBeNull();
    expect(readingFor("A", "B", "split", null)).toBeNull();
    expect(readingFor("A", "B", "inconclusive", "no_split")).toBeNull();
  });

  it("has no row for A vs C, B vs D or A vs D, whatever the verdict", () => {
    for (const [first, second] of [
      ["A", "C"],
      ["B", "D"],
      ["A", "D"],
    ] as const) {
      for (const verdict of ["split", "no_split", "inconclusive", "not_assessable"] as const) {
        expect(readingFor(first, second, verdict, "no_split"), `${first} ${second} ${verdict}`).toBeNull();
      }
    }
  });

  it("gives the pulled-apart row, in the real files, only where that file's C vs D is a no split", () => {
    let inconclusiveCd = 0;
    for (const { label, file } of realGrids) {
      const pair = (a: string, b: string) => file.comparisons.find((c) => c.first === a && c.second === b);
      const ab = pair("A", "B");
      const cd = pair("C", "D");
      expect(ab, `${label} A vs B`).toBeDefined();
      expect(cd, `${label} C vs D`).toBeDefined();
      const key = readingFor("A", "B", ab!.final_verdict, cd!.final_verdict);
      if (key === "ab_split_cd_not") expect(cd!.final_verdict, label).toBe("no_split");
      if (ab!.final_verdict === "split" && cd!.final_verdict === "inconclusive") {
        inconclusiveCd += 1;
        expect(key, label).toBeNull();
      }
    }
    // Haiku 5.5 s2 (grid) and s1 (thinking) are both A vs B split with C vs D inconclusive today: the case C4 got
    // wrong. If the data changes so that none is left, this says so rather than passing on nothing.
    expect(inconclusiveCd).toBeGreaterThan(0);
  });

  it("only ever returns a key the table holds", () => {
    const keys = Object.keys(PROTOCOL_READINGS) as ReadingKey[];
    for (const verdict of ["split", "no_split", "inconclusive", "not_assessable"] as const) {
      for (const cd of ["split", "no_split", "inconclusive", "not_assessable", null] as const) {
        for (const [a, b] of [
          ["C", "D"],
          ["A", "B"],
        ] as const) {
          const key = readingFor(a, b, verdict, cd);
          if (key !== null) expect(keys).toContain(key);
        }
      }
    }
  });
});
