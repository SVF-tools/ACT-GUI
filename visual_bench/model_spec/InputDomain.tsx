// Image view of an INPUT_SPEC box: clean input, bounds, allowed change per pixel, and sampled perturbations inside the box.
import { useMemo, useState } from "react";
import { fmt, num } from "../api";
import type { InputSpecOut } from "../generated/wire";
import { PerturbCompare, Pixels, type Shape } from "../workspace/pixels";

type Pattern = "sign" | "uniform" | "lower" | "upper";
const PATTERNS: { id: Pattern; label: string }[] = [
  { id: "sign", label: "random corner (each value at lb or ub)" },
  { id: "uniform", label: "uniform random inside the box" },
  { id: "lower", label: "all values at the lower bound" },
  { id: "upper", label: "all values at the upper bound" },
];

function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function sample(lb: number[], ub: number[], pattern: Pattern, seed: number): number[] {
  const rnd = mulberry32(seed);
  return lb.map((l, i) => {
    const u = ub[i]!;
    if (pattern === "lower") return l;
    if (pattern === "upper") return u;
    if (pattern === "sign") return rnd() < 0.5 ? l : u;
    return l + rnd() * (u - l);
  });
}

export function InputDomain({ spec, shape }: { spec: InputSpecOut; shape: Shape }) {
  const lb = useMemo(() => spec.lb.map(num), [spec]);
  const ub = useMemo(() => spec.ub.map(num), [spec]);
  const center = useMemo(() => (spec.center ? spec.center.map(num) : lb.map((l, i) => (l + ub[i]!) / 2)), [spec, lb, ub]);
  const width = useMemo(() => lb.map((l, i) => ub[i]! - l), [lb, ub]);
  const [pattern, setPattern] = useState<Pattern>("sign");
  const [seed, setSeed] = useState(1);
  const perturbed = useMemo(() => sample(lb, ub, pattern, seed), [lb, ub, pattern, seed]);

  const lo = Math.min(0, ...lb), hi = Math.max(1, ...ub);
  const wmax = Math.max(...width);
  const eps = wmax / 2;
  const clipped = width.filter((w) => w < wmax * (1 - 1e-4)).length;
  return (
    <div className="inputdomain">
      <div className="pixrow">
        <Pixels xs={center} shape={shape} lo={lo} hi={hi} size="huge"
          label={spec.center ? "clean input (spec center)" : "box midpoint"} />
        <Pixels xs={lb} shape={shape} lo={lo} hi={hi} size="big" label="lower bound" />
        <Pixels xs={ub} shape={shape} lo={lo} hi={hi} size="big" label="upper bound" />
        <Pixels xs={width} shape={shape} lo={0} hi={wmax || 1} mode="heat" size="big" label="allowed change (ub − lb)"
          title="bright = full ±ε range; dark = range cut by the valid pixel range" />
      </div>
      <p className="note">
        {shape.c}×{shape.h}×{shape.w} {shape.c === 3 ? "RGB" : "grey"} image{shape.hwc ? " (flat input read as H×W×C)" : ""}, {lb.length} input values ·
        each value may move up to ±{fmt(eps, 4)} ({fmt(eps * 255, 2)}/255)
        {clipped > 0 ? ` · ${clipped} values have a narrower range because the box is clipped to [${fmt(lo, 1)}, ${fmt(hi, 1)}]` : ""}
      </p>
      <h4>Perturbation inside the box</h4>
      <div className="perturbctl">
        <select value={pattern} onChange={(e) => setPattern(e.target.value as Pattern)} aria-label="perturbation pattern">
          {PATTERNS.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
        </select>
        <button className="secondary" onClick={() => setSeed((s) => s + 1)}
          disabled={pattern === "lower" || pattern === "upper"}>Resample</button>
      </div>
      <PerturbCompare base={center} perturbed={perturbed} shape={shape} lo={lo} hi={hi}
        baseLabel="clean" perturbedLabel="perturbed (in box)" />
      <p className="note">
        Every image in this box must satisfy the output property. These samples only illustrate the region; they are not
        checked by ACT. Fuzzing searches the same box for violating images.
      </p>
    </div>
  );
}
