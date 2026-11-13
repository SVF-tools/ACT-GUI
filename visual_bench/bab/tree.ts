// Pure presentation logic of the BaB search tree: replay state per wave, tidy layout, labels and timeline series.
import type { BabBranchOut, BabIntervalOut, BabNodeOut, BabTerminalOut, BabTreeOut, BabWaveOut } from "../generated/wire";
import { fmt, num } from "../shared/wire";

export type NodeState = BabNodeOut["state"];

export const STATES: readonly NodeState[] = ["pending", "branched", "proved", "falsified", "retired", "evicted", "unresolved"];

export const STATE_LABEL: Record<NodeState, string> = {
  pending: "open", branched: "branched", proved: "proved", falsified: "counterexample", retired: "retired",
  evicted: "evicted", unresolved: "unresolved",
};

const OUTCOME_STATE: Record<string, NodeState> = {
  proved_main: "proved", proved_terminal: "proved", branched: "branched",
  retired_max_depth: "retired", retired_terminal: "retired",
};

/** The state ACT had committed for a node by `wave`; null when ACT had not created it yet. */
export function stateAt(node: BabNodeOut, wave: number, terminal: BabTerminalOut | null): NodeState | null {
  if (node.created_wave > wave) return null;
  if (terminal && terminal.node_id === node.node_id && terminal.wave <= wave) {
    if (terminal.status === "FALSIFIED") return "falsified";
    if (terminal.status === "CERTIFIED") return "proved";
  }
  if (node.solved_wave !== null && node.solved_wave <= wave) return OUTCOME_STATE[node.outcome ?? ""] ?? "unresolved";
  if (node.evicted_wave !== null && node.evicted_wave <= wave) return "evicted";
  return "pending";
}

/** The last wave a replay can show: the newest committed wave, or the terminal's when the search ended inside one. */
export function lastWave(tree: Pick<BabTreeOut, "waves" | "terminal">): number {
  return Math.max(tree.waves.at(-1)?.wave ?? 0, tree.terminal?.wave ?? 0);
}

/** Nodes that changed in `wave`: created, solved or evicted then, or named by a terminal record of that wave. */
export function changedAt(node: BabNodeOut, wave: number, terminal: BabTerminalOut | null): boolean {
  return (node.created_wave === wave && node.parent_id >= 0) || node.solved_wave === wave || node.evicted_wave === wave
    || (terminal !== null && terminal.wave === wave && terminal.node_id === node.node_id);
}

export type Placed = { node: BabNodeOut; x: number; depth: number };

/**
 * Tidy top-down layout of the nodes reachable from `root`: leaves take consecutive slots in depth-first order
 * (children by node id), a parent sits midway between its first and last child. x is in slot units, depth is
 * relative to the root. Laying out the whole snapshot keeps positions fixed while a replay steps through waves.
 */
export function layout(nodes: BabNodeOut[], root: number): { placed: Placed[]; slots: number; depth: number } {
  const byId = new Map(nodes.map((n) => [n.node_id, n]));
  const kids = new Map<number, BabNodeOut[]>();
  for (const n of nodes) {
    if (n.node_id !== root && byId.has(n.parent_id)) kids.set(n.parent_id, [...(kids.get(n.parent_id) ?? []), n]);
  }
  for (const list of kids.values()) list.sort((a, b) => a.node_id - b.node_id);
  const placed: Placed[] = [];
  const top = byId.get(root);
  if (!top) return { placed, slots: 0, depth: 0 };
  let next = 0;
  let deepest = 0;
  const visit = (node: BabNodeOut, depth: number): number => {
    deepest = Math.max(deepest, depth);
    const children = kids.get(node.node_id) ?? [];
    const x = children.length === 0 ? next++ : (() => {
      const xs = children.map((c) => visit(c, depth + 1));
      return (xs[0]! + xs.at(-1)!) / 2;
    })();
    placed.push({ node, x, depth });
    return x;
  };
  visit(top, 0);
  return { placed, slots: next, depth: deepest };
}

/** The split that created a node, e.g. "x[35] ∈ [0, 0.05]" or "L3 #12 active". */
export function describeBranch(branch: BabBranchOut | null, specRows?: number): string {
  if (!branch) return "root";
  const intervals = branch.intervals ?? [], phases = branch.phases ?? [];
  if (branch.kind === "input_axis" && intervals.length) {
    return intervals.map((i) => `x[${i.axis}] ∈ [${bound(i.lb)}, ${bound(i.ub)}]`).join(", ");
  }
  if (branch.kind === "neuron" && phases.length) {
    return phases.map((p) => {
      const rows = specRows !== undefined && p.spec_rows.length < specRows ? ` (rows ${p.spec_rows.join(", ")})` : "";
      return `L${p.layer_id} #${p.neuron} ${p.sign > 0 ? "active" : "inactive"}${rows}`;
    }).join(", ");
  }
  return "split not identified by ACT";
}

const bound = (v: BabIntervalOut["lb"]) => (v === null ? "?" : fmt(num(v), 3));

export type WavePoint = { wave: number; frontier: number; solved: number; proved: number; minBound: number | null };

/** Per committed wave: the frontier after it, and nodes solved and proved up to it. */
export function waveSeries(waves: BabWaveOut[]): WavePoint[] {
  let solved = 0;
  let proved = 0;
  return waves.map((w) => {
    solved += w.solved;
    proved += w.proved;
    const m = w.min_bound === null ? null : num(w.min_bound);
    return { wave: w.wave, frontier: w.frontier_size, solved, proved, minBound: m !== null && Number.isFinite(m) ? m : null };
  });
}

/** Node count per state at `wave`, over the nodes of the snapshot. */
export function countsAt(nodes: BabNodeOut[], wave: number, terminal: BabTerminalOut | null): Record<NodeState, number> {
  const out = Object.fromEntries(STATES.map((s) => [s, 0])) as Record<NodeState, number>;
  for (const n of nodes) {
    const s = stateAt(n, wave, terminal);
    if (s) out[s] += 1;
  }
  return out;
}

export type LeafState = Exclude<NodeState, "branched">;

/**
 * The subtree of `root` at `wave` as fractions per leaf state (they sum to 1): every node's share is split equally
 * among its children once ACT created them. A measure of the split tree, not of input volume, and never a verdict.
 */
export function sharesAt(nodes: BabNodeOut[], root: number, wave: number, terminal: BabTerminalOut | null): Record<LeafState, number> {
  const out: Record<LeafState, number> = { proved: 0, falsified: 0, retired: 0, evicted: 0, unresolved: 0, pending: 0 };
  const kids = new Map<number, BabNodeOut[]>();
  for (const n of nodes) {
    if (n.node_id !== root && stateAt(n, wave, terminal) !== null) kids.set(n.parent_id, [...(kids.get(n.parent_id) ?? []), n]);
  }
  const top = nodes.find((n) => n.node_id === root);
  const stack: [BabNodeOut, number][] = top ? [[top, 1]] : [];
  while (stack.length) {
    const [n, share] = stack.pop()!;
    const children = kids.get(n.node_id) ?? [];
    if (children.length) {
      for (const c of children) stack.push([c, share / children.length]);
      continue;
    }
    const s = stateAt(n, wave, terminal) ?? "pending";
    out[s === "branched" ? "unresolved" : s] += share;
  }
  return out;
}

/** Per-pixel width of a node's input box: the input spec's, with the intervals split on its path applied in order. */
export function boxWidths(lb: number[], ub: number[], path: (BabBranchOut | null)[]): { widths: number[]; split: number } {
  const lo = [...lb];
  const hi = [...ub];
  const axes = new Set<number>();
  for (const branch of path) {
    for (const i of branch?.kind === "input_axis" ? branch.intervals ?? [] : []) {
      if (i.axis < 0 || i.axis >= lo.length) continue;
      if (i.lb !== null) lo[i.axis] = num(i.lb);
      if (i.ub !== null) hi[i.axis] = num(i.ub);
      axes.add(i.axis);
    }
  }
  return { widths: lo.map((l, k) => Math.max(0, hi[k]! - l)), split: axes.size };
}
