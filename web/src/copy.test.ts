import { describe, expect, it } from "vitest";
import { his, isPlaceholder, labels } from "./copy";

describe("copy", () => {
  // This test fails while any of his values is a marked placeholder (Phase 1.5 IMPLEMENTATION doc section 11): the deploy
  // commit cannot ship while any of his values is still a marked placeholder. An empty description is allowed
  // and means the page has no meta description.
  it("his words are written", () => {
    const unwritten = Object.entries(his)
      .filter(([key, value]) => !(key === "description" && value === ""))
      .filter(([, value]) => isPlaceholder(value))
      .map(([key]) => key);
    expect(unwritten).toEqual([]);
  });

  it("knows a placeholder by its marker", () => {
    expect(isPlaceholder("[his: a sentence]")).toBe(true);
    expect(isPlaceholder("A sentence he wrote.")).toBe(false);
    expect(isPlaceholder("")).toBe(false);
  });

  it("holds a label for every priority the placeholder uses", () => {
    for (const id of ["color", "fragrance", "water", "butterflies", "none"]) {
      expect(labels.priorities[id]).toBeTruthy();
    }
  });

  it("keeps Claude-drafted labels free of the words the page must not carry", () => {
    const text = JSON.stringify(labels).toLowerCase();
    for (const word of ["insight", "powered by", "unlock", "seamless", "delve", "leverage", "robust"]) {
      expect(text).not.toContain(word);
    }
  });
});
