import { fmt, num } from "../shared/wire";
import type { ModelDescriptionOut, FuzzCounterexampleOut } from "../generated/wire";
import { imageShape, specImageShape, type Shape } from "../shared/ui/pixels";

export const MAX_DIMS = 64;
export type Box = { lb: number[]; ub: number[] } | null;

// The spec's tensor shape when it matches the input length, else a C x S x S guess from the length alone.
export function modelShape(model: ModelDescriptionOut | null, d: number): Shape | null {
  const spec = model?.input_specs[0];
  const s = spec ? specImageShape(spec.shape, spec.dataset) : null;
  return s && s.c * s.h * s.w === d ? s : imageShape(d);
}

export function inputBox(model: ModelDescriptionOut | null, d: number): Box {
  const b = model?.input_specs[0];
  return b && b.lb && b.ub && b.lb.length === d ? { lb: b.lb.map(num), ub: b.ub.map(num) } : null;
}

export function argmax(ys: number[]): number {
  let k = 0;
  for (let i = 1; i < ys.length; i++) if (ys[i]! > ys[k]!) k = i;
  return k;
}

export function finiteRange(xs: number[]): [number, number] {
  let lo = Infinity, hi = -Infinity;
  for (const v of xs) if (Number.isFinite(v)) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
  return lo <= hi ? [lo, hi] : [0, 1];
}

// Display-side summary of one ACT counterexample; "predicted" is argmax of the output ACT recorded.
// shown is false when the service omitted the input vectors as too large to display (x, seed, delta are empty).
export type Ce = {
  ce: FuzzCounterexampleOut; shown: boolean; x: number[]; seed: number[]; y: number[]; ySeed: number[] | null;
  pred: number; seedPred: number | null; delta: number[]; linf: number; l2: number; changed: number; misclassified: boolean;
};

export function analyze(ce: FuzzCounterexampleOut): Ce {
  const shown = ce.input !== null && ce.seed_input !== null;
  const x = shown ? ce.input!.map(num) : [], seed = shown ? ce.seed_input!.map(num) : [], y = ce.output.map(num);
  const ySeed = ce.seed_output ? ce.seed_output.map(num) : null;
  const delta = x.map((v, i) => v - seed[i]!);
  let linf = 0, sq = 0, changed = 0;
  for (const d of delta) { linf = Math.max(linf, Math.abs(d)); sq += d * d; if (Math.abs(d) > 1e-9) changed++; }
  const pred = argmax(y);
  return { ce, shown, x, seed, y, ySeed, pred, seedPred: ySeed ? argmax(ySeed) : null, delta, linf, l2: Math.sqrt(sq), changed,
           misclassified: ce.true_class !== null && pred !== ce.true_class };
}

export function vec(xs: number[], k: number): string {
  return `[${xs.slice(0, k).map((v) => fmt(v, 3)).join(", ")}${xs.length > k ? `, … (${xs.length})` : ""}]`;
}

export function pct(x: number): string {
  return `${(x * 100).toFixed(1)}%`;
}
