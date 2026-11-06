import type { LayerOut, PropagationRecordOut, PropagationLayerRecordOut } from "../generated/wire";
import { num } from "../shared/wire";

export type Pass = "forward" | "backward" | "refine";
export type Status = "active" | "inactive" | "unstable" | "unknown";
export const statusClass = (n: number | undefined): Status =>
  n === 1 ? "active" : n === 0 ? "inactive" : n === -1 ? "unstable" : "unknown";
export const statusLabel = (n: number | undefined) =>
  ({ active: "Stable active", inactive: "Stable inactive", unstable: "Unstable", unknown: "Not recorded" })[statusClass(n)];

export function groupLayers(layers: LayerOut[], names: Map<number, string> = new Map()) {
  const blocks: { label: string; layers: LayerOut[] }[] = [];
  for (const layer of layers) {
    const prior = blocks.at(-1);
    const previous = prior?.layers.at(-1);
    const name = names.get(layer.layer_id);
    const chain = previous && previous.succs.length === 1 && layer.preds.length === 1 && layer.preds[0] === previous.layer_id;
    const affine = previous && /DENSE|CONV|AFFINE|LINEAR|BIAS/.test(previous.kind);
    if (prior && chain && ((name && prior.label === name) || (!name && layer.kind === "RELU" && affine))) {
      prior.layers.push(layer);
    } else blocks.push({ label: name ?? (layer.kind === "INPUT" || layer.kind === "INPUT_SPEC" ? "Input" : `Block ${blocks.length + 1}`), layers: [layer] });
  }
  return blocks;
}

/** Latest record for each scientific identity, never a later record during replay. */
export function latestRecords<T extends PropagationRecordOut>(records: T[], cutoff = Infinity): T[] {
  const latest = new Map<string, T>();
  for (const r of records) {
    if (!r.key || r.record_id > cutoff) continue;
    const k = r.key;
    const id = JSON.stringify([r.kind, k.scope, k.parent, k.domain, k.pass_, k.layer_id, k.stage]);
    const prev = latest.get(id);
    if (!prev || r.record_id > prev.record_id) latest.set(id, r);
  }
  return [...latest.values()].sort((a, b) => a.record_id - b.record_id);
}

export function binStatuses(values: (number | undefined)[], limit = 4096) {
  const size = Math.max(1, Math.ceil(values.length / Math.max(1, limit)));
  const bins: { start: number; end: number; status: number | undefined; counts: Record<Status, number> }[] = [];
  for (let start = 0; start < values.length; start += size) {
    const end = Math.min(values.length, start + size);
    const counts = { active: 0, inactive: 0, unstable: 0, unknown: 0 };
    for (let i = start; i < end; i++) counts[statusClass(values[i])]++;
    const status = counts.unstable ? -1 : counts.unknown ? undefined : counts.active ? 1 : 0;
    bins.push({ start, end, status, counts });
  }
  return bins;
}

/** ACT flat order: lane, optional specification row, then flattened neurons. */
export function tensorValue(r: PropagationLayerRecordOut | undefined, field: string, lane: number, neuron: number, spec = 0): number | undefined {
  const shape = r?.tensors[field]?.shape;
  const values = r?.values[field];
  if (!shape?.length || !values || lane < 0 || neuron < 0 || spec < 0) return undefined;
  const perSpec = ["alpha", "nu", "lower_slope", "lower_intercept", "upper_slope", "upper_intercept"].includes(field) && shape.length === 3;
  const rows = perSpec ? shape[1]! : 1;
  const width = shape.slice(perSpec ? 2 : 1).reduce((a, b) => a * b, 1);
  if (lane >= shape[0]! || (perSpec && spec >= rows) || neuron >= width) return undefined;
  const value = values[(lane * rows + (perSpec ? spec : 0)) * width + neuron];
  return value === undefined ? undefined : num(value);
}
export const tensorRows = (r: PropagationLayerRecordOut | undefined, field: string) =>
  (r?.tensors[field]?.shape.length ?? 0) >= 3 ? r!.tensors[field]!.shape[1]! : 1;

export function laneStatuses(records: PropagationLayerRecordOut[], lane: number, count: number): (number | undefined)[] {
  const explicit = records.filter((r) => r.values.status !== undefined).at(-1);
  const pre = records.filter((r) => r.key?.stage === "pre" && r.values.lb && r.values.ub).at(-1);
  return Array.from({ length: count }, (_, neuron) => {
    if (explicit) return tensorValue(explicit, "status", lane, neuron);
    const lo = tensorValue(pre, "lb", lane, neuron), hi = tensorValue(pre, "ub", lane, neuron);
    if (lo === undefined || hi === undefined || Number.isNaN(lo) || Number.isNaN(hi)) return undefined;
    return hi <= 0 ? 0 : lo >= 0 ? 1 : -1;
  });
}

export function unstableShare(r: PropagationRecordOut | undefined): number | undefined {
  if (!r) return undefined;
  const c = r.counts, total = (c.n_active ?? 0) + (c.n_inactive ?? 0) + (c.n_unstable ?? 0);
  return total > 0 ? (c.n_unstable ?? 0) / total : undefined;
}
