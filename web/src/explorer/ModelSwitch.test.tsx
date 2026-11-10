import { cleanup, fireEvent, render, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { explorerLabels } from "./copy";
import { realIndex } from "./fixtures";
import { ModelSwitch } from "./ModelSwitch";

afterEach(cleanup);

describe("ModelSwitch", () => {
  it("renders one button per model, in the data's order, named from the data", () => {
    const { getByRole } = render(
      <ModelSwitch models={realIndex.models} current="haiku-5-5" onChoose={() => {}} />,
    );
    const group = getByRole("group", { name: explorerLabels.modelSwitch });
    const names = within(group)
      .getAllByRole("button")
      .map((b) => b.textContent);
    expect(names).toEqual(realIndex.models.map((m) => m.model_key));
    expect(names).toHaveLength(2);
  });

  it("marks the current model with aria-pressed and calls back with the model's key", () => {
    const onChoose = vi.fn();
    const { getByRole } = render(
      <ModelSwitch models={realIndex.models} current="gpt-oss-openrouter" onChoose={onChoose} />,
    );
    expect(getByRole("button", { name: "gpt-oss-openrouter" }).getAttribute("aria-pressed")).toBe("true");
    expect(getByRole("button", { name: "haiku-5-5" }).getAttribute("aria-pressed")).toBe("false");
    fireEvent.click(getByRole("button", { name: "haiku-5-5" }));
    expect(onChoose).toHaveBeenCalledWith("haiku-5-5");
  });

  it("never offers both models at once", () => {
    const { queryByRole, getAllByRole } = render(
      <ModelSwitch models={realIndex.models} current="haiku-5-5" onChoose={() => {}} />,
    );
    expect(queryByRole("button", { name: /both|all|pooled|combined/i })).toBeNull();
    expect(getAllByRole("button")).toHaveLength(realIndex.models.length);
  });
});
