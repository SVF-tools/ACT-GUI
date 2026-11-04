import { MAX_DIMS, type Box } from "./presentation";

// Signed perturbation per input dimension, scaled by the input box width when the box is known.
export function DeltaBars({ delta, box }: { delta: number[]; box: Box }) {
  const n = Math.min(delta.length, MAX_DIMS);
  const rel = delta.slice(0, n).map((d, i) => (box ? d / ((box.ub[i]! - box.lb[i]!) || 1) : d));
  const m = Math.max(1e-12, ...rel.map(Math.abs));
  const SW = 160, SH = 36, bw = SW / n;
  return (
    <svg className="spark" viewBox={`0 0 ${SW} ${SH}`} width="100%" height={SH} preserveAspectRatio="none"
      role="img" aria-label="perturbation per input dimension">
      <line className="axis" x1={0} y1={SH / 2} x2={SW} y2={SH / 2} />
      {rel.map((r, i) => {
        const h = (Math.abs(r) / m) * (SH / 2 - 1);
        return <rect key={i} className={r >= 0 ? "up" : "down"} x={i * bw + bw * 0.15} width={bw * 0.7} y={r >= 0 ? SH / 2 - h : SH / 2} height={h} />;
      })}
    </svg>
  );
}
