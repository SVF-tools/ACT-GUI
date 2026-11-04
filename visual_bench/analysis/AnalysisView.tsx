// Manual propagation through recorded interval layer states (ANA-01, first version).
import { useState } from "react";
import { fmt, num } from "../shared/wire";
import { Empty } from "../shared/ui/Empty";
import type { LayerStateOut, ModelDescriptionOut } from "../generated/wire";
import { useLayers } from "./hooks";

export function AnalysisView({ sel, model, onSelectLayer, onSelectNeuron }: {
  sel: { runId: string | null; layerId: number | null; neuron: number | null }; model: ModelDescriptionOut | null;
  onSelectLayer: (id: number) => void; onSelectNeuron: (i: number | null) => void;
}) {
  const q = useLayers(sel.runId);
  if (!sel.runId) return <Empty title="No run selected" text="Start or pick a run; its interval layer states are recorded with it." />;
  if (q.status === "pending") return <Empty title="Loading layer states…" text="" />;
  if (q.status === "error") return <div className="error">{q.error.message}</div>;
  const st = q.data;
  if (st.availability !== "available") return <Empty title={`Layer states ${st.availability}`} text="Available once the run completes and its record is sealed." />;
  const order = st.layers.map((l) => l.layer_id);
  const idx = sel.layerId === null ? -1 : order.indexOf(sel.layerId);
  const layer = idx >= 0 ? st.layers[idx]! : null;
  const step = (d: number) => {
    const next = idx < 0 ? 0 : Math.min(order.length - 1, Math.max(0, idx + d));
    onSelectLayer(order[next]!);
  };
  return (
    <div className="analysis">
      <div className="stepper">
        <button onClick={() => step(-1)} disabled={idx <= 0}>◀ prev</button>
        <div className="steps">
          {st.layers.map((l) => (
            <button key={l.layer_id} className={l.layer_id === sel.layerId ? "stepdot active" : "stepdot"} onClick={() => onSelectLayer(l.layer_id)}
              title={`layer ${l.layer_id} ${l.kind}`}>{l.layer_id}<small>{l.kind}</small></button>
          ))}
        </div>
        <button onClick={() => step(1)} disabled={idx >= order.length - 1}>next ▶</button>
      </div>
      <div className="note">Method: {st.method} · {st.provenance.act_call} · {st.provenance.recorded}</div>
      {!layer ? <Empty title="Pick a layer" text="Use the stepper or click a node in the network." /> : (
        <LayerBounds layer={layer} before={st.layers.find((l) => l.layer_id === layer.before_layer_ids[0]) ?? null}
          neuron={sel.neuron} onSelectNeuron={onSelectNeuron} model={model} />
      )}
    </div>
  );
}

function LayerBounds({ layer, before, neuron, onSelectNeuron, model }: {
  layer: LayerStateOut; before: LayerStateOut | null; neuron: number | null; onSelectNeuron: (i: number | null) => void;
  model: ModelDescriptionOut | null;
}) {
  const lb = layer.lb.map(num), ub = layer.ub.map(num);
  const blb = before?.lb.map(num) ?? null, bub = before?.ub.map(num) ?? null;
  const sameSize = blb !== null && blb.length === lb.length;
  const finite = [...lb, ...ub, ...(sameSize ? [...blb!, ...bub!] : [])].filter(Number.isFinite);
  const lo = Math.min(0, ...finite), hi = Math.max(0, ...finite);
  const span = hi - lo || 1;
  const x = (v: number) => `${((Math.max(lo, Math.min(hi, v)) - lo) / span) * 100}%`;
  const shown = Math.min(lb.length, 64);
  const kind = model?.layers.find((l) => l.layer_id === layer.layer_id)?.kind ?? layer.kind;
  return (
    <>
      <h3>Layer {layer.layer_id} · {kind} <small>shape [{layer.shape.join("×")}] · stage: after{before ? ` · before = after of layer ${before.layer_id}` : ""}</small></h3>
      <div className="legend">
        {sameSize && <span><i className="sw before" /> before (input to this layer)</span>}
        <span><i className="sw after" /> after (ACT interval bounds)</span>
        <span className="muted">axis [{fmt(lo)}, {fmt(hi)}], 0 marked</span>
      </div>
      <div className="bars" role="list">
        {Array.from({ length: shown }, (_, i) => (
          <button key={i} role="listitem" className={i === neuron ? "barrow active" : "barrow"} onClick={() => onSelectNeuron(i === neuron ? null : i)}
            title={`[${lb[i]}, ${ub[i]}]`}>
            <span className="idx">{i}</span>
            <span className="track">
              <span className="zero" style={{ left: x(0) }} />
              {sameSize && <span className="bar before" style={{ left: x(blb![i]!), width: `calc(${x(bub![i]!)} - ${x(blb![i]!)})` }} />}
              <span className="bar after" style={{ left: x(lb[i]!), width: `max(2px, calc(${x(ub[i]!)} - ${x(lb[i]!)}))` }} />
            </span>
            <span className="vals mono">[{fmt(lb[i]!)}, {fmt(ub[i]!)}]</span>
          </button>
        ))}
      </div>
      {lb.length > shown && <div className="note">{lb.length - shown} more values not drawn (paging not implemented).</div>}
      <BoxProjection lb={lb} ub={ub} />
    </>
  );
}

/** 2-coordinate view of the interval box. This is the box itself, not a tighter set: ACT exports no geometry here. */
function BoxProjection({ lb, ub }: { lb: number[]; ub: number[] }) {
  const [a, setA] = useState(0);
  const [b, setB] = useState(Math.min(1, lb.length - 1));
  if (lb.length < 2) return null;
  const vals = [lb[a]!, ub[a]!, lb[b]!, ub[b]!].filter(Number.isFinite);
  const lo = Math.min(...vals, 0), hi = Math.max(...vals, 0), pad = (hi - lo) * 0.1 || 1;
  const S = 180, s = (v: number) => ((v - (lo - pad)) / (hi - lo + 2 * pad)) * S;
  return (
    <div className="proj">
      <div className="projhead">
        <b>2-D projection</b>
        <label>x <select value={a} onChange={(e) => setA(Number(e.target.value))}>{lb.map((_, i) => <option key={i} value={i}>{i}</option>)}</select></label>
        <label>y <select value={b} onChange={(e) => setB(Number(e.target.value))}>{lb.map((_, i) => <option key={i} value={i} disabled={i === a}>{i}</option>)}</select></label>
      </div>
      <svg width={S} height={S} className="projsvg" role="img" aria-label="interval box projection">
        <line x1={s(0)} x2={s(0)} y1={0} y2={S} className="axis" />
        <line y1={S - s(0)} y2={S - s(0)} x1={0} x2={S} className="axis" />
        <text x={4} y={12} className="plabel">y{b}: [{fmt(lb[b]!)}, {fmt(ub[b]!)}]</text>
        <text x={4} y={S - 4} className="plabel">x{a}: [{fmt(lb[a]!)}, {fmt(ub[a]!)}]</text>
        <rect x={s(lb[a]!)} y={S - s(ub[b]!)} width={Math.max(1, s(ub[a]!) - s(lb[a]!))} height={Math.max(1, s(ub[b]!) - s(lb[b]!))} className="box" />
      </svg>
      <div className="note">Representation: interval box · guarantee: sound outer bound from ACT interval analysis · tighter geometry: unsupported (ACT baseline has no projection export).</div>
    </div>
  );
}
