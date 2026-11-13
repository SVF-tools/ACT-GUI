// Search progress per committed wave: frontier size, solved and proved nodes, and the lowest node bound.
import type { MouseEvent } from "react";
import { fmt } from "../shared/wire";
import { useWidth } from "./useWidth";
import type { WavePoint } from "./tree";

const H = 170, PL = 34, PR = 52, PT = 10, PB = 22;

export function BabTimeline(props: { points: WavePoint[]; marker: number; onWave: (wave: number) => void }) {
  const [ref, width] = useWidth();
  return (
    <div ref={ref}>
      {props.points.length === 0 ? <div className="note">No committed wave yet.</div>
        : width > 0 && <Chart {...props} W={width} />}
    </div>
  );
}

function Chart({ points, marker, onWave, W }: { points: WavePoint[]; marker: number; onWave: (wave: number) => void; W: number }) {
  const first = Math.min(0, points[0]!.wave), last = Math.max(1, points.at(-1)!.wave);
  const top = Math.max(1, ...points.flatMap((p) => [p.frontier, p.solved]));
  const bounds = points.flatMap((p) => (p.minBound === null ? [] : [p.minBound]));
  const bmin = bounds.length ? Math.min(...bounds) : 0, bmax = bounds.length ? Math.max(...bounds) : 1;
  const pad = 0.05 * (bmax - bmin || Math.abs(bmax) || 1);
  const lo = bmin - pad, hi = bmax + pad;
  const x = (w: number) => PL + ((w - first) / (last - first)) * (W - PL - PR);
  const y = (v: number) => PT + (1 - v / top) * (H - PT - PB);
  const yb = (v: number) => PT + (1 - (v - lo) / (hi - lo)) * (H - PT - PB);
  const line = (value: (p: WavePoint) => number) => points.map((p) => `${x(p.wave)},${y(value(p))}`).join(" ");
  const boundLine = points.flatMap((p) => (p.minBound === null ? [] : [`${x(p.wave)},${yb(p.minBound)}`])).join(" ");
  const pick = (e: MouseEvent<SVGSVGElement>) => {
    const at = first + (e.clientX - e.currentTarget.getBoundingClientRect().left - PL) / (W - PL - PR) * (last - first);
    onWave(Math.max(first, Math.min(last, Math.round(at))));
  };
  return (
    <>
      <div className="legend">
        <span><i className="sw babsw-pending" /> frontier (open)</span>
        <span><i className="sw babsw-branched" /> solved</span>
        <span><i className="sw babsw-proved" /> proved</span>
        {bounds.length > 0 && <span><i className="sw babsw-bound" /> lowest node bound (right axis)</span>}
      </div>
      <svg className="projsvg babchart" width={W} height={H} role="img" onClick={pick}
          aria-label="BaB search progress per wave; click to replay a wave">
          <line className="axis" x1={PL} y1={H - PB} x2={W - PR} y2={H - PB} />
          <line className="axis" x1={PL} y1={PT} x2={PL} y2={H - PB} />
          <text className="plabel" x={PL - 4} y={PT + 8} textAnchor="end">{top}</text>
          <text className="plabel" x={PL - 4} y={H - PB} textAnchor="end">0</text>
          <text className="plabel" x={PL} y={H - 6}>wave {first}</text>
          <text className="plabel" x={W - PR} y={H - 6} textAnchor="end">{last}</text>
          {bounds.length > 0 && <>
            <line className="axis" x1={W - PR} y1={PT} x2={W - PR} y2={H - PB} />
            <text className="plabel" x={W - PR + 4} y={PT + 8}>{fmt(bmax, 3)}</text>
            <text className="plabel" x={W - PR + 4} y={H - PB}>{fmt(bmin, 3)}</text>
            {lo < 0 && hi > 0 && <line className="babzero" x1={PL} y1={yb(0)} x2={W - PR} y2={yb(0)}><title>bound 0</title></line>}
            <polyline className="babbound" points={boundLine} />
          </>}
          <polyline className="babfrontier" points={line((p) => p.frontier)} />
          <polyline className="babsolved" points={line((p) => p.solved)} />
          <polyline className="babproved" points={line((p) => p.proved)} />
          <line className="babmarker" x1={x(marker)} y1={PT} x2={x(marker)} y2={H - PB}><title>shown wave {marker}</title></line>
      </svg>
    </>
  );
}
