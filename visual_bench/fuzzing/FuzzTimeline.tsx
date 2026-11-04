import type { FuzzPointOut } from "../generated/wire";

const W = 400, H = 150, PL = 34, PR = 34, PT = 8, PB = 22;

export function FuzzTimeline({ points, firstCe, marker }: { points: FuzzPointOut[]; firstCe: number | null; marker: number | null }) {
  if (points.length === 0) return <div className="note">Waiting for the first progress report…</div>;
  const maxIt = Math.max(1, ...points.map((p) => p.iteration));
  const maxCe = Math.max(1, ...points.map((p) => p.counterexamples));
  const x = (it: number) => PL + (it / maxIt) * (W - PL - PR);
  const yc = (c: number) => PT + (1 - c) * (H - PT - PB);
  const yv = (v: number) => PT + (1 - v / maxCe) * (H - PT - PB);
  const start = { iteration: 0, coverage: points[0]!.coverage, counterexamples: 0 };
  const cov = [start, ...points].map((p) => `${x(p.iteration)},${yc(p.coverage)}`).join(" ");
  const steps: string[] = [`${x(0)},${yv(0)}`];
  let prev = 0;
  for (const p of points) {
    steps.push(`${x(p.iteration)},${yv(prev)}`, `${x(p.iteration)},${yv(p.counterexamples)}`);
    prev = p.counterexamples;
  }
  return (
    <>
      <div className="legend">
        <span><i className="sw after" /> neuron coverage (left axis)</span>
        <span><i className="sw ce" /> counterexamples (right axis)</span>
      </div>
      <svg className="projsvg fuzzchart" viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="fuzzing progress">
        <line className="axis" x1={PL} y1={H - PB} x2={W - PR} y2={H - PB} />
        <line className="axis" x1={PL} y1={PT} x2={PL} y2={H - PB} />
        <line className="axis" x1={W - PR} y1={PT} x2={W - PR} y2={H - PB} />
        <text className="plabel" x={PL - 4} y={PT + 8} textAnchor="end">100%</text>
        <text className="plabel" x={PL - 4} y={H - PB} textAnchor="end">0%</text>
        <text className="plabel" x={W - PR + 4} y={PT + 8}>{maxCe}</text>
        <text className="plabel" x={W - PR + 4} y={H - PB}>0</text>
        <text className="plabel" x={PL} y={H - 6}>0</text>
        <text className="plabel" x={W - PR} y={H - 6} textAnchor="end">{maxIt} iterations</text>
        {firstCe !== null && <line className="firstce" x1={x(firstCe)} y1={PT} x2={x(firstCe)} y2={H - PB}><title>first counterexample at iteration {firstCe}</title></line>}
        {marker !== null && <line className="framemark" x1={x(marker)} y1={PT} x2={x(marker)} y2={H - PB}><title>shown mutated input: iteration {marker}</title></line>}
        <polyline className="cov" points={cov} />
        <polyline className="ces" points={steps.join(" ")} />
      </svg>
    </>
  );
}
