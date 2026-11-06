import { describe, expect, it } from "vitest";
import type { LayerOut, PropagationLayerRecordOut } from "../generated/wire";
import { binStatuses, groupLayers, laneStatuses, latestRecords, statusClass, tensorValue } from "./propagation";

const layer = (id: number, kind: string, preds = id ? [id - 1] : [], succs = [id + 1]): LayerOut =>
  ({ layer_id: id, kind, preds, succs, in_vars: 3, out_vars: 3, params: [], output_shape: [1, 3] });
function record(id: number, version = 0): PropagationLayerRecordOut {
  return { record_id: id, kind: "LayerBounds", key: { domain: "dual", layer_id: 1, origin: "computed", parent: null, pass_: "forward", scope: "root", stage: "pre", version },
    counts: {}, metadata: {}, layer_kind: "RELU", output_shape: [1, 3], shape: [1, 3], t_ms: id,
    tensors: {}, values: {} };
}
describe("propagation view models", () => {
  it("groups affine activation chains, but not branches", () => {
    const xs = [layer(0, "INPUT"), layer(1, "DENSE"), layer(2, "RELU"), layer(3, "DENSE", [2], [4, 5]), layer(4, "RELU")];
    expect(groupLayers(xs).map((b) => b.layers.map((l) => l.layer_id))).toEqual([[0], [1, 2], [3], [4]]);
    expect(groupLayers(xs.slice(1, 3), new Map([[1, "encoder"], [2, "encoder"]]))[0]?.label).toBe("encoder");
  });
  it("maps all ACT status values distinctly without inventing an unknown", () => {
    expect([1, 0, -1, undefined, 5].map(statusClass)).toEqual(["active", "inactive", "unstable", "unknown", "unknown"]);
  });
  it("bins every neuron exactly once, retains minority unstable cells and permits zoom", () => {
    const xs = Array.from({ length: 9001 }, (_, i) => i === 1 ? -1 : 1);
    const bins = binStatuses(xs);
    expect(bins.length).toBeLessThanOrEqual(4096);
    expect(bins[0]?.status).toBe(-1);
    expect(bins.reduce((n, b) => n + b.end - b.start, 0)).toBe(9001);
    expect(bins.at(-1)?.end).toBe(9001);
    expect(binStatuses(xs.slice(bins[0]!.start, bins[0]!.end)).map((b) => b.status)).toEqual([1, -1, 1]);
  });
  it("selects exact historical identities, separates pass and scope, ignores future revisions", () => {
    const a = record(1), b = record(2, 1), c = record(3);
    c.key = { ...c.key!, pass_: "backward" };
    const d = record(4); d.key = { ...d.key!, scope: "child" };
    expect(latestRecords([b, a, c, d], 2).map((r) => r.record_id)).toEqual([2]);
    expect(latestRecords([a, b, c, d]).map((r) => r.record_id)).toEqual([2, 3, 4]);
  });
  it("indexes alpha by lane, specification row, and neuron without flattening rows together", () => {
    const r = record(1);
    r.tensors.alpha = { dtype: "float32", sha256: "fixture", shape: [2, 2, 3] };
    r.values.alpha = Array.from({ length: 12 }, (_, i) => i / 12);
    expect(tensorValue(r, "alpha", 1, 2, 0)).toBe(8 / 12);
    expect(tensorValue(r, "alpha", 1, 0, 1)).toBe(9 / 12);
    expect(tensorValue(r, "alpha", 0, 3, 0)).toBeUndefined();
    expect(tensorValue(r, "alpha", 0, 0, 2)).toBeUndefined();
    r.tensors.lower_slope = r.tensors.alpha;
    r.values.lower_slope = r.values.alpha;
    expect(tensorValue(r, "lower_slope", 1, 0, 1)).toBe(9 / 12);
    r.tensors.upper_slope = { dtype: "float32", sha256: "fixture", shape: [2, 3] };
    r.values.upper_slope = [0, 1, 2, 3, 4, 5];
    expect(tensorValue(r, "upper_slope", 1, 2, 1)).toBe(5);
  });
  it("uses pre-activation bounds, never labels post-ReLU zero as stable active", () => {
    const r = record(1);
    r.tensors.lb = r.tensors.ub = { dtype: "float32", sha256: "fixture", shape: [1, 3] };
    r.values.lb = [-1, 1, -3]; r.values.ub = [2, 3, -1];
    expect(laneStatuses([r], 0, 3)).toEqual([-1, 1, 0]);
    r.key = { ...r.key!, stage: "out" };
    expect(laneStatuses([r], 0, 3)).toEqual([undefined, undefined, undefined]);
  });
});
