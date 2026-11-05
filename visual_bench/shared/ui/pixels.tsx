// Shared image rendering for image-shaped ACT inputs (CHW, as ACT stores them): specs, fuzz seeds, counterexamples.
import { useEffect, useRef, useState } from "react";
import { fmt } from "../wire";

export type Shape = { c: number; h: number; w: number; hwc?: boolean };

/** Image geometry from an ACT tensor shape such as [1, 3, 32, 32]; null unless it is N x C x H x W with C = 1 or 3. */
export function shapeFromTensor(shape: number[] | null | undefined): Shape | null {
  if (!shape || shape.length !== 4) return null;
  const [, c, h, w] = shape as [number, number, number, number];
  return (c === 1 || c === 3) && h >= 8 && w >= 8 ? { c, h, w } : null;
}

/** Fallback when only a flat length is known: C x S x S with C = 1 or 3 and S >= 8. */
export function imageShape(d: number): Shape | null {
  for (const c of [1, 3]) {
    const s = Math.round(Math.sqrt(d / c));
    if (s >= 8 && c * s * s === d) return { c, h: s, w: s };
  }
  return null;
}

/** Image geometry of an input spec: its N x C x H x W shape, or a flat [1, d] input of a known image dataset (VNN-LIB). */
export function specImageShape(shape: number[], dataset: string | null | undefined): Shape | null {
  const s = shapeFromTensor(shape);
  if (s) return s;
  const known = dataset ? (["mnist", "cifar10", "svhn"] as const).some((d) => d === dataset.toLowerCase()) : false;
  const s2 = known && shape.length === 2 && shape[0] === 1 ? imageShape(shape[1]!) : null;
  // Flat VNN-LIB image vectors interleave channels per pixel (H x W x C), e.g. cora_2024's CIFAR-10 properties.
  return s2 && s2.c > 1 ? { ...s2, hwc: true } : s2;
}

const CLASSES: Record<string, string[]> = {
  mnist: ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
  cifar10: ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"],
};

/** "3 · cat" for known datasets, otherwise the bare class index. */
export function classLabel(dataset: string | null | undefined, k: number): string {
  const name = dataset ? CLASSES[dataset.toLowerCase()]?.[k] : undefined;
  return name !== undefined && name !== String(k) ? `${k} · ${name}` : String(k);
}

export type PixelMode = "image" | "signed" | "heat";

/**
 * image: values mapped linearly from [lo, hi] to grey/RGB.
 * signed: channel mean, red for positive and blue for negative, scaled by max(|lo|, |hi|).
 * heat: channel mean from [lo, hi] on a dark-to-amber ramp (magnitudes such as allowed perturbation width).
 */
export function Pixels({ xs, shape, lo, hi, mode = "image", label, size = "small", title }: {
  xs: number[]; shape: Shape; lo: number; hi: number; mode?: PixelMode; label: string;
  size?: "small" | "big" | "huge"; title?: string;
}) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const ctx = ref.current?.getContext("2d");
    if (ctx) paint(ctx, xs, shape, lo, hi, mode);
  }, [xs, shape, lo, hi, mode]);
  return (
    <figure className={`pix ${size}`} title={title}>
      <canvas ref={ref} width={shape.w} height={shape.h} />
      <figcaption>{label}</figcaption>
    </figure>
  );
}

function paint(ctx: CanvasRenderingContext2D, xs: number[], shape: Shape, lo: number, hi: number, mode: PixelMode) {
    const { c, h, w } = shape, n = h * w, img = ctx.createImageData(w, h);
    const at = (k: number, p: number) => xs[shape.hwc ? p * c + k : k * n + p]!;
    const span = hi - lo || 1, m = Math.max(Math.abs(lo), Math.abs(hi)) || 1;
    const unit = (v: number) => Math.max(0, Math.min(1, (v - lo) / span));
    const mean = (p: number) => { let v = 0; for (let k = 0; k < c; k++) v += at(k, p); return v / c; };
    for (let p = 0; p < n; p++) {
      let rgb: [number, number, number];
      if (mode === "signed") {
        const v = mean(p), t = Math.min(1, Math.abs(v) / m) * 255;
        rgb = v >= 0 ? [255, 255 - t, 255 - t] : [255 - t, 255 - t, 255];
      } else if (mode === "heat") {
        const t = unit(mean(p));
        rgb = [20 + 235 * t, 20 + 170 * t * t, 30 + 20 * t];
      } else {
        const r = 255 * unit(at(0, p));
        rgb = c === 3 ? [r, 255 * unit(at(1, p)), 255 * unit(at(2, p))] : [r, r, r];
      }
      img.data.set([rgb[0], rgb[1], rgb[2], 255], p * 4);
    }
    ctx.putImageData(img, 0, 0);
}

/**
 * The input as a PNG at its native resolution (one pixel per value, RGB for 3 channels).
 * Values in [0, 1] map to 0..255 directly; other inputs use [lo, hi], as displayed.
 */
export function imagePng(xs: number[], shape: Shape, lo: number, hi: number): Promise<Blob> {
  const unit = xs.every((v) => v >= 0 && v <= 1);
  const canvas = document.createElement("canvas");
  canvas.width = shape.w;
  canvas.height = shape.h;
  paint(canvas.getContext("2d")!, xs, shape, unit ? 0 : lo, unit ? 1 : hi, "image");
  return new Promise((ok, fail) => canvas.toBlob((b) => (b ? ok(b) : fail(new Error("PNG encoding failed"))), "image/png"));
}

/** Save a blob through the browser's download prompt. */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

/**
 * Base vs perturbed image: both images, the signed difference, and the base with the difference
 * amplified k times so perturbations of a few 1/255 steps become visible. Display only.
 */
export function PerturbCompare({ base, perturbed, shape, lo, hi, baseLabel, perturbedLabel }: {
  base: number[]; perturbed: number[]; shape: Shape; lo: number; hi: number; baseLabel: string; perturbedLabel: string;
}) {
  const delta = perturbed.map((v, i) => v - base[i]!);
  let linf = 0, changed = 0;
  for (const d of delta) { linf = Math.max(linf, Math.abs(d)); if (Math.abs(d) > 1e-9) changed++; }
  const [gain, setGain] = useState(() => Math.max(1, Math.min(50, Math.round((0.4 * (hi - lo)) / (linf || 1)))));
  const amplified = base.map((v, i) => Math.max(lo, Math.min(hi, v + gain * delta[i]!)));
  return (
    <div className="perturb">
      <div className="pixrow">
        <Pixels xs={base} shape={shape} lo={lo} hi={hi} label={baseLabel} size="big" />
        <Pixels xs={perturbed} shape={shape} lo={lo} hi={hi} label={perturbedLabel} size="big" />
        <Pixels xs={delta} shape={shape} lo={-linf} hi={linf} mode="signed" size="big"
          label={`δ (red +, blue −) · ‖δ‖∞ ${fmt(linf, 4)}`} />
        <Pixels xs={amplified} shape={shape} lo={lo} hi={hi} size="big" label={`${baseLabel} + ${gain}·δ`} />
      </div>
      <label className="gain">
        amplify δ ×{gain}
        <input type="range" min={1} max={50} value={gain} onChange={(e) => setGain(Number(e.target.value))} />
        <span className="muted">{changed} of {delta.length} values changed</span>
      </label>
    </div>
  );
}
