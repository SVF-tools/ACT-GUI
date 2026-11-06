import { useId, useState } from "react";
import type { PropagationLayerRecordOut } from "../generated/wire";
import { fmt } from "../shared/wire";
import { Empty } from "../shared/ui/Empty";
import { statusLabel, tensorRows, tensorValue, type Pass } from "./propagation";

const show = (v: number | undefined) => v === undefined ? "Not recorded" : fmt(v, 5);

/** records and before are sliced to the selected neuron by the API, so tensor index 0 is that neuron. */
export function NeuronDetail({ records, before, neuron, lane, domain, pass, status, kind }: {
  records: PropagationLayerRecordOut[]; before: PropagationLayerRecordOut[]; neuron: number | null;
  lane: number; domain: string; pass: Pass; status: number | undefined; kind: string;
}) {
  const [spec, setSpec] = useState(0);
  if (neuron === null) return <Empty title="Select a neuron" text="Choose a cell or enter its index to inspect the recorded bounds." />;
  const pre = records.filter((r) => r.key?.pass_ === "forward" && r.key.stage === "pre" && r.values.lb).at(-1)
    ?? before.filter((r) => r.key?.pass_ === "forward" && r.key.stage === "out" && r.values.lb).at(-1);
  const post = records.filter((r) => r.key?.pass_ === "forward" && r.key.stage === "out" && r.values.lb).at(-1);
  const relax = records.filter((r) => r.kind === "Relaxation").at(-1);
  const backward = records.filter((r) => r.kind === "DualBackward").at(-1);
  const rows = tensorRows(backward, "alpha"), row = Math.min(spec, rows - 1);
  const lo = tensorValue(pre, "lb", lane, 0) ?? tensorValue(relax, "extra.pre_lb", lane, 0);
  const hi = tensorValue(pre, "ub", lane, 0) ?? tensorValue(relax, "extra.pre_ub", lane, 0);
  const outLo = tensorValue(post, "lb", lane, 0), outHi = tensorValue(post, "ub", lane, 0);
  const alpha = tensorValue(backward, "alpha", lane, 0, row);
  const lowerSlope = tensorValue(relax, "lower_slope", lane, 0, row);
  const upperSlope = tensorValue(relax, "upper_slope", lane, 0, row);
  const lowerIntercept = tensorValue(relax, "lower_intercept", lane, 0, row);
  const upperIntercept = tensorValue(relax, "upper_intercept", lane, 0, row);
  return <section className="neuron-detail">
    <h3>Neuron {neuron}</h3>
    <p>{statusLabel(status)} · lane {lane + 1}</p>
    <p className="note">{domain} · {pass} pass</p>
    <h4>Bounds <small>Forward pass</small></h4>
    <BoundsBar label="Pre" lo={lo} hi={hi} />
    {pre && pre.key?.layer_id !== records[0]?.key?.layer_id && <p className="note">Pre = output of layer {pre.key?.layer_id}.</p>}
    <BoundsBar label="Post" lo={outLo} hi={outHi} />
    {kind === "RELU" && <>
      <h4>ReLU relaxation <small>{relax?.key?.pass_ ?? "forward"} pass</small></h4>
      {lo !== undefined && hi !== undefined && Number.isFinite(lo) && Number.isFinite(hi)
        ? <RelaxationPlot lo={lo} hi={hi} domain={domain}
          lowerSlope={lowerSlope}
          lowerIntercept={lowerIntercept}
          upperSlope={upperSlope} upperIntercept={upperIntercept} />
        : <p className="note">Finite pre-activation bounds were not recorded; no curve is inferred.</p>}
      <p className="note">{domain === "interval" ? "Box outer approximation."
        : domain === "hybridz" ? "Exact inactive / active split of this ReLU. Cross-neuron constraints are not projected here."
        : "Solid: ReLU. Dashed: recorded linear envelope."}</p>
      {domain === "dual" && (upperSlope === undefined || lowerSlope === undefined) && <p className="note">Some envelope coefficients are not recorded.</p>}
    </>}
    {domain === "dual" && pass !== "backward" && <p className="note">Choose the backward pass to inspect alpha and the linear envelope.</p>}
    {domain === "dual" && pass === "backward" && <>
      <h4>Alpha <small>Backward pass</small></h4>
      {rows > 1 && <label className="prop-field">Specification row <select value={row} onChange={(e) => setSpec(Number(e.target.value))}>
        {Array.from({ length: rows }, (_, n) => <option key={n} value={n}>{n + 1}</option>)}
      </select></label>}
      <dl className="prop-values"><dt>Alpha</dt><dd>{show(alpha)}</dd><dt>Nu</dt><dd>{show(tensorValue(backward, "nu", lane, 0, row))}</dd></dl>
      {backward?.metadata.alpha_optimized === false
        ? <p className="note">Not optimized: initial chord slope u / (u − l) for unstable neurons.</p>
        : backward?.metadata.alpha_optimized === true ? <p className="note">Optimized by ACT.</p> : <p className="note">Optimization state not recorded.</p>}
      {status !== -1 && <p className="note">Alpha controls the relaxation only for unstable neurons.</p>}
    </>}
    <details className="prop-provenance"><summary>Record details</summary>
      {records.map((r) => <p className="note" key={r.record_id}>{r.kind} · {r.key?.pass_} · {r.key?.stage === "pre" ? "pre" : "post"} · version {r.key?.version} · record {r.record_id}</p>)}
    </details>
  </section>;
}

function BoundsBar({ label, lo, hi }: { label: string; lo: number | undefined; hi: number | undefined }) {
  const finite = lo !== undefined && hi !== undefined && Number.isFinite(lo) && Number.isFinite(hi);
  const min = Math.min(0, lo ?? 0), max = Math.max(0, hi ?? 0), span = max - min || 1;
  return <div className="prop-bound"><span>{label}</span><b>{lo === undefined || hi === undefined ? "Not recorded" : `[${show(lo)}, ${show(hi)}]`}</b>
    {finite && <svg viewBox="0 0 240 18" role="img" aria-label={`${label} bounds ${lo} to ${hi}`}>
      <line x1="4" x2="236" y1="9" y2="9" className="prop-axis" />
      <line x1={4 + (lo! - min) / span * 232} x2={4 + (hi! - min) / span * 232} y1="9" y2="9" className="prop-bound-line" />
      <line x1={4 + -min / span * 232} x2={4 + -min / span * 232} y1="2" y2="16" className="prop-axis" />
    </svg>}
  </div>;
}

function RelaxationPlot({ lo, hi, domain, lowerSlope, lowerIntercept, upperSlope, upperIntercept }: {
  lo: number; hi: number; domain: string; lowerSlope?: number; lowerIntercept?: number; upperSlope?: number; upperIntercept?: number;
}) {
  const clipId = useId();
  const left = Math.min(lo, 0), right = Math.max(hi, 0), span = right - left || 1;
  const top = Math.max(hi, 0) || 1;
  const x = (v: number) => 22 + (v - left) / span * 216;
  const y = (v: number) => 148 - v / top * 120;
  const line = (slope?: number, intercept?: number) => slope !== undefined && intercept !== undefined && Number.isFinite(slope) && Number.isFinite(intercept)
    ? `${x(lo)},${y(slope * lo + intercept)} ${x(hi)},${y(slope * hi + intercept)}` : undefined;
  const lower = line(lowerSlope, lowerIntercept), upper = line(upperSlope, upperIntercept);
  return <svg viewBox="0 0 260 174" className="relaxation-plot" role="img" aria-label={`${domain} ReLU relaxation over ${lo} to ${hi}`}>
    <defs><clipPath id={clipId}><rect x="20" y="8" width="220" height="142" /></clipPath></defs>
    <line x1="20" x2="240" y1={y(0)} y2={y(0)} className="prop-axis" />
    <line x1={x(0)} x2={x(0)} y1="8" y2="150" className="prop-axis" />
    {domain === "interval" && <rect x={x(lo)} y={y(Math.max(0, hi))} width={Math.max(1, x(hi) - x(lo))} height={Math.max(1, y(Math.max(0, lo)) - y(Math.max(0, hi)))} className="relax-box" />}
    <g clipPath={`url(#${clipId})`}>
      <polyline points={`${x(lo)},${y(Math.max(0, lo))} ${x(Math.max(lo, Math.min(hi, 0)))},${y(Math.max(0, lo))} ${x(hi)},${y(Math.max(0, hi))}`} className="relu-line" />
      {domain === "dual" && lower && <polyline points={lower} className="envelope lower" />}
      {domain === "dual" && upper && <polyline points={upper} className="envelope upper" />}
      {domain === "hybridz" && lo < 0 && hi > 0 && <circle cx={x(0)} cy={y(0)} r="4" className="split-point" />}
    </g>
    <text x="22" y="168">{fmt(lo, 3)}</text><text x="238" y="168" textAnchor="end">{fmt(hi, 3)}</text>
  </svg>;
}
