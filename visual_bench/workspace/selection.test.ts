import { describe, expect, it } from "vitest";
import { initialSelection, selectionReducer, type Selection } from "./selection";

const apply = (s: Selection, ...actions: Parameters<typeof selectionReducer>[1][]) => actions.reduce(selectionReducer, s);

describe("selectionReducer", () => {
  it("keeps layer and neuron selections distinct and bumps revision", () => {
    const s = apply(initialSelection, { type: "selectModel", modelId: "m" }, { type: "selectLayer", layerId: 3 },
      { type: "selectNeuron", neuron: 5 });
    expect(s).toMatchObject({ modelId: "m", layerId: 3, neuron: 5, revision: 3 });
    const s2 = selectionReducer(s, { type: "selectLayer", layerId: 4 });
    expect(s2).toMatchObject({ layerId: 4, neuron: null, revision: 4 });
  });

  it("drops run/layer/neuron when a different model is selected", () => {
    const s = apply(initialSelection, { type: "selectRun", runId: "r1", modelId: "a" }, { type: "selectLayer", layerId: 2 });
    expect(selectionReducer(s, { type: "selectModel", modelId: "b" })).toMatchObject({ modelId: "b", runId: null, layerId: null });
  });

  it("keeps the layer when switching between runs of the same model", () => {
    const s = apply(initialSelection, { type: "selectRun", runId: "r1", modelId: "a" }, { type: "selectLayer", layerId: 2 },
      { type: "selectRun", runId: "r2", modelId: "a" });
    expect(s).toMatchObject({ runId: "r2", layerId: 2 });
  });

  it("returns the same object for a no-op selection", () => {
    const s = selectionReducer(initialSelection, { type: "selectModel", modelId: "a" });
    expect(selectionReducer(s, { type: "selectModel", modelId: "a" })).toBe(s);
  });
});
