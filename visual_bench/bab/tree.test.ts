import { describe, expect, it } from "vitest";
import type { BabNodeOut, BabTerminalOut, BabWaveOut } from "../generated/wire";
import { boxWidths, changedAt, countsAt, describeBranch, lastWave, layout, sharesAt, stateAt, waveSeries } from "./tree";

const node = (node_id: number, parent_id: number, depth: number, extra: Partial<BabNodeOut> = {}): BabNodeOut => ({
  node_id, parent_id, depth, state: "pending", outcome: null, created_wave: parent_id < 0 ? 0 : 1, solved_wave: null,
  evicted_wave: null, bound: null, branch: null, children: 0, descendants: 0, hidden_children: 0, ...extra,
});

// root 0 split in wave 1 into 1 and 2; node 2 split in wave 2 into 3 and 4; node 1 proved in wave 2; 4 evicted in 3.
const NODES = [
  node(0, -1, 0, { outcome: "branched", solved_wave: 1, state: "branched" }),
  node(1, 0, 1, { outcome: "proved_main", solved_wave: 2, state: "proved" }),
  node(2, 0, 1, { outcome: "branched", solved_wave: 2, state: "branched" }),
  node(3, 2, 2, { created_wave: 2 }),
  node(4, 2, 2, { created_wave: 2, evicted_wave: 3, state: "evicted" }),
];
const UNKNOWN: BabTerminalOut = { seq: 4, wave: 3, t_ms: 0, status: "UNKNOWN", reason: "budget", frontier_size: 1, node_id: null };

describe("replay", () => {
  it("shows exactly what ACT had committed by each wave", () => {
    const at = (w: number) => NODES.map((n) => stateAt(n, w, UNKNOWN));
    expect(at(0)).toEqual(["pending", null, null, null, null]);
    expect(at(1)).toEqual(["branched", "pending", "pending", null, null]);
    expect(at(2)).toEqual(["branched", "proved", "branched", "pending", "pending"]);
    expect(at(3)).toEqual(["branched", "proved", "branched", "pending", "evicted"]);
    expect(countsAt(NODES, 2, UNKNOWN)).toMatchObject({ pending: 2, branched: 2, proved: 1, evicted: 0 });
  });

  it("splits the shares of the tree as it stood at each wave", () => {
    expect(sharesAt(NODES, 0, 1, UNKNOWN)).toMatchObject({ pending: 1, proved: 0 });
    expect(sharesAt(NODES, 0, 3, UNKNOWN)).toMatchObject({ proved: 0.5, pending: 0.25, evicted: 0.25 });
    expect(sharesAt(NODES, 2, 3, UNKNOWN)).toMatchObject({ pending: 0.5, evicted: 0.5 });
  });

  it("marks the node a terminal record names, from that wave on", () => {
    const ce: BabTerminalOut = { ...UNKNOWN, wave: 3, status: "FALSIFIED", node_id: 3 };
    expect(stateAt(NODES[3]!, 2, ce)).toBe("pending");
    expect(stateAt(NODES[3]!, 3, ce)).toBe("falsified");
    expect(lastWave({ waves: [], terminal: ce })).toBe(3);
    expect(changedAt(NODES[3]!, 3, ce) && !changedAt(NODES[1]!, 3, ce)).toBe(true);
    const presolved: BabTerminalOut = { ...UNKNOWN, wave: 0, status: "CERTIFIED", node_id: 0 };
    expect(stateAt(node(0, -1, 0), 0, presolved)).toBe("proved");
  });
});

describe("layout", () => {
  it("gives leaves consecutive slots and centers parents over their children", () => {
    const { placed, slots, depth } = layout(NODES, 0);
    const x = Object.fromEntries(placed.map((p) => [p.node.node_id, p.x]));
    expect(slots).toBe(3);
    expect(depth).toBe(2);
    expect(x).toEqual({ 0: 0.75, 1: 0, 2: 1.5, 3: 1, 4: 2 });
  });

  it("lays out a focused subtree relative to its root", () => {
    const { placed, slots, depth } = layout(NODES, 2);
    expect(placed.map((p) => [p.node.node_id, p.x, p.depth])).toEqual([[3, 0, 1], [4, 1, 1], [2, 0.5, 0]]);
    expect([slots, depth]).toEqual([2, 1]);
  });
});

describe("labels and series", () => {
  it("describes input and ReLU splits", () => {
    expect(describeBranch(null)).toBe("root");
    expect(describeBranch({ kind: "input_axis", phases: [], intervals: [{ axis: 35, lb: 0, ub: 0.05 }] }))
      .toBe("x[35] ∈ [0.000, 0.050]");
    expect(describeBranch({ kind: "neuron", intervals: [], phases: [{ layer_id: 3, neuron: 12, sign: -1, spec_rows: [0] }] }, 9))
      .toBe("L3 #12 inactive (rows 0)");
  });

  it("accumulates solved and proved nodes per wave", () => {
    const wave = (w: number, solved: number, proved: number, min: BabWaveOut["min_bound"]): BabWaveOut => ({
      wave: w, seq: w, t_ms: 0, solved, created: 0, proved, branched: 0, retired: 0, unresolved: 0, evicted: 0,
      frontier_size: 10 - w, min_bound: min,
    });
    expect(waveSeries([wave(1, 1, 0, -2), wave(2, 2, 1, "-Infinity")])).toEqual([
      { wave: 1, frontier: 9, solved: 1, proved: 0, minBound: -2 },
      { wave: 2, frontier: 8, solved: 3, proved: 1, minBound: null },
    ]);
  });

  it("applies the input splits of a path in order", () => {
    const split = (axis: number, lb: number, ub: number) => ({ kind: "input_axis", phases: [], intervals: [{ axis, lb, ub }] });
    const { widths, split: n } = boxWidths([0, 0, 0], [1, 1, 1], [null, split(1, 0, 0.5), split(1, 0.25, 0.5)]);
    expect(widths).toEqual([1, 0.25, 1]);
    expect(n).toBe(1);
  });
});
