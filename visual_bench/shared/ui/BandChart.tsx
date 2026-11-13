// Box of a vector input, one row per dimension: [lower, upper] on a scale shared by every row, plus point markers
// (source sentence, counterexample, seed).
import { fmt } from "../wire";

export type BandMarker = { label: string; cls: "anchor" | "ce" | "seed"; values: number[] };

export const BAND_MAX_DIMS = 512;

export function bandRange(lb: number[], ub: number[], markers: BandMarker[] = []): [number, number] {
  const xs = [...lb, ...ub, ...markers.flatMap((m) => m.values)].filter(Number.isFinite);
  if (xs.length === 0) return [0, 1];
  const lo = Math.min(...xs), hi = Math.max(...xs);
  return hi > lo ? [lo, hi] : [lo - 1, hi + 1];
}

export function BandChart({ lb, ub, markers = [], label }: {
  lb: number[]; ub: number[]; markers?: BandMarker[]; label: string;
}) {
  const [lo, hi] = bandRange(lb, ub, markers);
  const pos = (v: number) => ((Math.max(lo, Math.min(hi, v)) - lo) / (hi - lo)) * 100;
  const n = Math.min(lb.length, BAND_MAX_DIMS);
  return (
    <div className="band" role="figure" aria-label={label}>
      <div className="legend">
        <span><i className="sw before" /> box</span>
        {markers.map((m) => <span key={m.label}><i className={`sw ${m.cls}`} /> {m.label}</span>)}
        <span className="muted mono">scale {fmt(lo, 3)} … {fmt(hi, 3)}</span>
      </div>
      <div className="bars">
        {Array.from({ length: n }, (_, i) => {
          const l = lb[i]!, u = ub[i]!;
          return (
            <div key={i} className="barrow" title={[`x[${i}] in [${l}, ${u}]`, ...markers.map((m) => `${m.label}: ${m.values[i]}`)].join("\n")}>
              <span className="idx">{i}</span>
              <span className="track">
                {lo < 0 && hi > 0 && <span className="zero" style={{ left: `${pos(0)}%` }} />}
                <span className="bar before" style={{ left: `${pos(l)}%`, width: `${Math.max(pos(u) - pos(l), 0.5)}%` }} />
                {markers.map((m) => m.values[i] === undefined ? null
                  : <span key={m.label} className={`pin ${m.cls}`} style={{ left: `${pos(m.values[i]!)}%` }} />)}
              </span>
              <span className="vals mono">{fmt(l, 3)} … {fmt(u, 3)}</span>
            </div>
          );
        })}
      </div>
      {lb.length > n && <div className="note">Showing {n} of {lb.length} dimensions.</div>}
    </div>
  );
}
