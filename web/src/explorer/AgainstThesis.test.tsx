import { cleanup, render, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { AgainstThesis } from "./AgainstThesis";
import { againstWords } from "./againstWords";
import { IntervalChart } from "./charts";
import { explorerHis, explorerLabels as L } from "./copy";
import type { AgainstThesisEntry, DataIndex } from "./data";
import { realIndex } from "./fixtures";
import { modelName } from "./models";
import { PROTOCOL_READINGS } from "./protocol";
import { ScenarioView } from "./ScenarioView";
import { realApi } from "./fixtures";
import { fireEvent } from "@testing-library/react";

afterEach(cleanup);

const real = realIndex.against_thesis.entries;

/** An entry of the real shape, from the first real one, with overrides. */
function entry(over: Partial<AgainstThesisEntry>): AgainstThesisEntry {
  return { ...structuredClone(real[0]!), ...over };
}

function withAgainst(
  entries: AgainstThesisEntry[],
  scenarios: DataIndex["against_thesis"]["scenarios"] = [],
) {
  return { ...realIndex, against_thesis: { ...realIndex.against_thesis, entries, scenarios } } as DataIndex;
}

const items = (container: HTMLElement) => [...container.querySelectorAll<HTMLElement>("li.x-entry")];

describe("the section, with today's file", () => {
  it("is a section with its own id, focusable by script, headed by his title and introduction", () => {
    const { container } = render(<AgainstThesis index={realIndex} />);
    const section = container.querySelector("section")!;
    expect(section.id).toBe("against-the-thesis");
    expect(section.getAttribute("tabindex")).toBe("-1");
    expect(section.querySelector("h2")!.textContent).toBe(explorerHis.againstTitle);
    expect(section.getAttribute("aria-labelledby")).toBe(section.querySelector("h2")!.id);
    expect(section.textContent).toContain(explorerHis.againstIntro);
  });

  it("states the rule, its sources with their dates, the date it was written and the disclosure, above the list", () => {
    const { container } = render(<AgainstThesis index={realIndex} />);
    const text = container.textContent!;
    for (const paragraph of againstWords.ruleParagraphs) expect(text).toContain(paragraph);
    for (const source of againstWords.sources) expect(text).toContain(source);
    for (const date of ["2026-10-02", "2026-10-03", "2026-10-13", "2026-11-09", "2026-10-15"])
      expect(text).toContain(date);
    expect(text).toContain(againstWords.disclosure);
    expect(text).toContain(realIndex.against_thesis.rule); // the citation, as the data has it
    const list = container.querySelector(".x-entries")!;
    for (const mark of [againstWords.disclosure, againstWords.writtenLine, againstWords.sources[0]!]) {
      // Everything about the rule comes before the list in document order.
      expect(container.textContent!.indexOf(mark)).toBeLessThan(
        container.textContent!.indexOf(list.textContent!),
      );
    }
  });

  it("lists today's two entries, in the file's order, each with its model, scenario, pair, verdict and numbers", () => {
    const { container } = render(<AgainstThesis index={realIndex} />);
    const found = items(container);
    expect(real).toHaveLength(2);
    expect(found).toHaveLength(2);
    found.forEach((li, i) => {
      const e = real[i]!;
      expect(li.dataset["model"]).toBe(e.model_key);
      expect(li.dataset["scenario"]).toBe(e.scenario_id);
      expect(li.dataset["pair"]).toBe(`${e.first}-${e.second}`);
      expect(li.querySelector("h4")!.textContent).toContain(modelName(e.model_key));
      expect(li.querySelector("h4")!.textContent).toContain(`${e.first} vs ${e.second}`);
      expect(li.textContent).toContain(L.verdictWords[e.final_verdict]);
      expect(li.querySelector(".headline")!.textContent).toBe(e.headline); // verbatim
      expect(li.textContent).toContain(["−2.0 points", "0.0 points"][i]!); // the difference, formatted
    });
    expect(found.map((li) => li.dataset["scenario"])).toEqual(["s1", "s3"]);
  });

  it("formats the first entry's difference and interval from its fields", () => {
    const { container } = render(<AgainstThesis index={realIndex} />);
    const first = items(container)[0]!;
    expect(first.textContent).toContain("−2.0 points");
    expect(first.textContent).toContain("−7.2 to +3.2 points");
    expect(first.textContent).toContain(L.runsPair(60, 60));
    expect(first.textContent).toContain(againstWords.clauseNoSplit);
  });

  it("says, for each of today's entries, that the protocol wrote no reading for a B vs D pair, and quotes nothing", () => {
    const { container } = render(<AgainstThesis index={realIndex} />);
    for (const li of items(container)) {
      expect(li.querySelector("blockquote")).toBeNull();
      expect(li.textContent).toContain(L.noReading);
      expect(li.textContent).not.toContain(againstWords.alsoAgainstAuthor);
      expect(li.textContent).not.toContain(againstWords.s4Note);
    }
  });

  it("draws the interval chart's row for each entry, with the verdict word beside it", () => {
    const { container } = render(<AgainstThesis index={realIndex} />);
    for (const li of items(container)) {
      expect(li.querySelectorAll(".intervals .interval-row:not(.interval-axis)")).toHaveLength(1);
      expect(li.querySelector(".interval-row .verdict-word")!.textContent).toBe("no split");
    }
  });

  it("draws an entry's chart row exactly as the details draw the same comparison (same component, same size)", async () => {
    const against = render(<AgainstThesis index={realIndex} />);
    const row = items(against.container)[0]!.querySelector(".interval-row")!.outerHTML;
    cleanup();
    const data = realApi();
    const scenario = render(<ScenarioView id="s1" index={realIndex} model="haiku-5-5" data={data} />);
    await scenario.findByRole("figure");
    const details = scenario.container.querySelector("details")!;
    details.open = true;
    fireEvent(details, new Event("toggle"));
    const rows = [...scenario.container.querySelectorAll(".intervals .interval-row")];
    const bd = rows.find((r) => r.textContent!.startsWith("B vs D"))!;
    expect(bd.outerHTML).toBe(row);
  });
});

describe("the section, with fixtures", () => {
  it("shows a drafted sentence when the rule listed nothing, and no list", () => {
    const { container } = render(<AgainstThesis index={withAgainst([])} />);
    expect(container.querySelector(".x-empty")!.textContent).toBe(againstWords.emptyList);
    expect(container.querySelector(".x-entries")).toBeNull();
    expect(container.querySelector(".x-whole")).toBeNull();
    // The rule is still stated.
    expect(container.textContent).toContain(againstWords.disclosure);
  });

  it("lists the entries in the file's order, never re-sorted or re-filtered", () => {
    const entries = [
      entry({
        model_key: "gpt-oss-openrouter",
        scenario_id: "s4",
        first: "A",
        second: "B",
        clause: "reversed_split",
        final_verdict: "split",
        difference: 0.4,
        low: 0.2,
        high: 0.6,
      }),
      entry({ model_key: "haiku-5-5", scenario_id: "s1", first: "B", second: "D" }),
      entry({
        model_key: "gpt-oss-openrouter",
        scenario_id: "s2",
        first: "A",
        second: "C",
        clause: "reversed_split",
        final_verdict: "split",
        difference: -0.3,
        low: -0.4,
        high: -0.2,
      }),
    ];
    const { container } = render(<AgainstThesis index={withAgainst(entries)} />);
    expect(
      items(container).map((li) => `${li.dataset["model"]}/${li.dataset["scenario"]}/${li.dataset["pair"]}`),
    ).toEqual(["gpt-oss-openrouter/s4/A-B", "haiku-5-5/s1/B-D", "gpt-oss-openrouter/s2/A-C"]);
  });

  it("names the clause that listed each entry", () => {
    const entries = [
      entry({ clause: "no_split" }),
      entry({
        scenario_id: "s2",
        first: "A",
        second: "C",
        clause: "reversed_split",
        final_verdict: "split",
        difference: -0.3,
        low: -0.4,
        high: -0.2,
      }),
    ];
    const { container } = render(<AgainstThesis index={withAgainst(entries)} />);
    const [a, b] = items(container);
    expect(a!.textContent).toContain(againstWords.clauseNoSplit);
    expect(b!.textContent).toContain(againstWords.clauseReversed);
    expect(b!.textContent).not.toContain(againstWords.clauseNoSplit);
  });

  it("gives a C vs D entry both readings: the protocol's row quoted, and the label that it is also against the author's thesis", () => {
    const cd = entry({
      scenario_id: "s1",
      first: "C",
      second: "D",
      roundtable_pair: true,
      clause: "no_split",
      final_verdict: "no_split",
    });
    const { container } = render(<AgainstThesis index={withAgainst([cd])} />);
    const li = items(container)[0]!;
    const quote = li.querySelector("blockquote")!;
    expect(quote.getAttribute("data-reading")).toBe("cd_no_split");
    expect(quote.textContent).toContain(PROTOCOL_READINGS.cd_no_split.reading);
    expect(li.textContent).toContain(againstWords.alsoAgainstAuthor);
    expect(li.querySelector(".protocol-none")).toBeNull();
  });

  it("quotes the A vs B no-split row on an A vs B entry", () => {
    const ab = entry({ first: "A", second: "B", clause: "no_split", final_verdict: "no_split" });
    const { container } = render(<AgainstThesis index={withAgainst([ab])} />);
    expect(container.querySelector("blockquote")!.getAttribute("data-reading")).toBe("ab_no_split");
  });

  it("puts the note on any s4 entry, and only there, saying why s4's direction is the one a reviewer could dispute", () => {
    const s4 = entry({
      model_key: "gpt-oss-openrouter",
      scenario_id: "s4",
      first: "A",
      second: "C",
      clause: "reversed_split",
      final_verdict: "split",
      difference: 0.5,
      low: 0.3,
      high: 0.7,
    });
    const other = entry({ scenario_id: "s1" });
    const { container } = render(<AgainstThesis index={withAgainst([s4, other])} />);
    const [first, second] = items(container);
    expect(first!.textContent).toContain(againstWords.s4Note);
    expect(second!.textContent).not.toContain(againstWords.s4Note);
    expect(againstWords.s4Note).toMatch(/dispute/);
  });

  it("lists whole scenarios with their scenario id", () => {
    const { container } = render(
      <AgainstThesis index={withAgainst([], [{ model_key: "haiku-5-5", scenario_id: "s3" }])} />,
    );
    const whole = container.querySelector(".x-whole")!;
    expect(within(whole as HTMLElement).getAllByRole("listitem")).toHaveLength(1);
    expect(whole.textContent).toContain(againstWords.wholeLine("s3", "Haiku 5.5"));
    expect(whole.textContent).toContain("s3");
  });
});

describe("the interval chart", () => {
  const row = { first: "B", second: "D", secondary: false, threshold: 0.1, verdict: "no_split" as const };

  it("draws a dot, a line and the threshold band, and leaves the verdict to its word", () => {
    // A row whose interval crosses the band's edge still reads by its word: here an interval wider than the band
    // with the verdict "split" (protocol 6.3: a split needs the interval to exclude zero and the difference to reach
    // the threshold, which the geometry alone does not say).
    const { container } = render(
      <IntervalChart
        rows={[{ ...row, difference: 0.2, low: 0.02, high: 0.432, verdict: "split" }]}
        names={L.objectiveNames}
        label="x"
      />,
    );
    expect(container.querySelector("line.interval")).not.toBeNull();
    expect(container.querySelector("circle.diff")).not.toBeNull();
    expect(container.querySelector("rect.band")).not.toBeNull();
    expect(container.querySelector(".verdict-word")!.textContent).toBe("split");
  });

  it("draws no line for a row with no interval, and says so", () => {
    const { container } = render(
      <IntervalChart
        rows={[{ ...row, difference: null, low: null, high: null, verdict: "not_assessable" }]}
        names={L.objectiveNames}
        label="x"
      />,
    );
    expect(container.querySelector("line.interval")).toBeNull();
    expect(container.querySelector("circle.diff")).toBeNull();
    expect(container.textContent).toContain(L.intervalRowNotAssessable);
  });

  it("labels the axis in points and the band's edges from the threshold", () => {
    const { container } = render(
      <IntervalChart
        rows={[{ ...row, difference: 0, low: -0.05, high: 0.05 }]}
        names={L.objectiveNames}
        label="x"
      />,
    );
    const ticks = [...container.querySelectorAll("text.tick")].map((t) => t.textContent);
    expect(ticks).toEqual(["−100", "−50", "0", "+50", "+100", "−10", "+10"]);
  });
});
