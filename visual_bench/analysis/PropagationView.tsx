import { useEffect, useMemo, useRef, useState } from "react";
import type { ModelDescriptionOut, PropagationIndexOut, PropagationRecordOut } from "../generated/wire";
import { Empty } from "../shared/ui/Empty";
import { Pixels, shapeFromTensor } from "../shared/ui/pixels";
import { num, fmt } from "../shared/wire";
import { useAnalysisOnline, usePropagation, usePropagationRecords } from "./hooks";
import { useRun } from "../verification/hooks";
import { usePropagationSelection } from "./PropagationContext";
import { groupLayers, laneStatuses, latestRecords, unstableShare, type Pass } from "./propagation";
import { NeuronMap } from "./NeuronMap";
import { NeuronDetail } from "./NeuronDetail";
import "./propagation.css";

type Selection = { runId: string | null; layerId: number | null; neuron: number | null };
// The map needs bounds and status of every neuron; the detail panel fetches all fields of one neuron.
const MAP_FIELDS = { fields: ["lb", "ub", "status"] };

function useEvidence(sel: Selection, model: ModelDescriptionOut | null, index?: PropagationIndexOut) {
  const { state } = usePropagationSelection();
  const selected = useMemo(() => latestRecords(index?.records ?? [], state.cursor ?? Infinity).filter((r) => r.key?.scope === "root"), [index?.records, state.cursor]);
  const layer = model?.layers.find((l) => l.layer_id === sel.layerId);
  const layerRecords = selected.filter((r) =>
    r.key?.layer_id === sel.layerId && (r.key.pass_ === "forward" || r.key.pass_ === state.pass));
  const detail = usePropagationRecords(sel.runId, sel.layerId, layerRecords, MAP_FIELDS);
  const neuron = usePropagationRecords(sel.runId, sel.neuron === null ? null : sel.layerId, layerRecords,
    { neuron: sel.neuron ?? undefined });
  const predecessor = layer?.kind === "RELU" && layer.preds.length === 1 ? layer.preds[0]! : null;
  const hasPre = detail.records.some((r) => r.key?.stage === "pre" && r.values.lb);
  const beforeRecords = hasPre ? [] : selected.filter((r) => r.key?.layer_id === predecessor && r.key?.pass_ === "forward" && r.key.stage === "out");
  const before = usePropagationRecords(sel.runId, hasPre || sel.neuron === null ? null : predecessor, beforeRecords,
    { neuron: sel.neuron ?? undefined });
  const shape = detail.records.find((r) => r.values.lb)?.tensors.lb?.shape
    ?? detail.records.find((r) => r.values.status)?.tensors.status?.shape;
  const lanes = shape?.[0] ?? 1;
  const lane = Math.min(state.lane, lanes - 1);
  const count = shape?.slice(1).reduce((n, v) => n * v, 1) ?? layer?.out_vars ?? 0;
  const output = detail.records.find((r) => r.output_shape.length)?.output_shape ?? layer?.output_shape ?? [];
  const geometry = output.length === 3 ? [lanes, ...output] : output;
  const statuses = laneStatuses(detail.records, lane, count);
  return { selected, detail, neuron, before, layer, lanes, lane, count, geometry, statuses };
}

export function PropagationView({ sel, model, index, onSelectLayer, onSelectNeuron }: {
  sel: Selection; model: ModelDescriptionOut | null; index: PropagationIndexOut;
  onSelectLayer: (id: number) => void; onSelectNeuron: (id: number | null) => void;
}) {
  const { state, update } = usePropagationSelection();
  const run = useRun(sel.runId);
  const online = useAnalysisOnline();
  const live = run.data ? run.data.status === "queued" || run.data.status === "running" : !index.complete;
  const evidence = useEvidence(sel, model, index);
  const { selected, detail, neuron, before, layer, lanes, lane, count, geometry, statuses } = evidence;
  const [playing, setPlaying] = useState(false);
  const [timing, setTiming] = useState("normalized");
  const layerPane = useRef<HTMLDivElement>(null);
  useEffect(() => { layerPane.current?.scrollTo({ top: 0 }); }, [sel.layerId]);
  const records = useMemo(() => [...new Map([...index.records, ...index.phases].map((r) => [r.record_id, r])).values()]
    .sort((a, b) => a.record_id - b.record_id), [index.records, index.phases]);
  const position = state.cursor === null ? records.length - 1 : records.findIndex((r) => r.record_id === state.cursor);
  const current = records[Math.max(0, position)];
  const active = [...records.slice(0, position + 1)].reverse().find((r) => r.key)?.key?.layer_id;
  useEffect(() => {
    if (!playing || live || records.length === 0) return;
    if (position >= records.length - 1) { setPlaying(false); return; }
    const delay = timing === "recorded" ? Math.max(0, records[position + 1]!.t_ms - (current?.t_ms ?? 0)) : 450;
    const timer = window.setTimeout(() => update({ cursor: records[position + 1]!.record_id }), delay);
    return () => window.clearTimeout(timer);
  }, [playing, live, records, position, current, timing, update]);
  const chooseLayer = (id: number) => { onSelectLayer(id); onSelectNeuron(null); update({ level: "layer", lane: 0 }); };
  const chooseNeuron = (id: number) => { onSelectNeuron(id); update({ level: "neuron" }); };
  const passes = [...new Set(selected.filter((r) => r.key?.layer_id === sel.layerId).map((r) => r.key!.pass_))];
  const shownRecords = detail.records.filter((r) => r.key?.pass_ === state.pass);
  const stabilityPass = detail.records.filter((r) => r.values.status).at(-1)?.key?.pass_ ?? "forward";
  const countPass = selected.filter((r) => r.key?.layer_id === sel.layerId && unstableShare(r) !== undefined).at(-1)?.key?.pass_ ?? stabilityPass;
  const imageBounds = shownRecords.filter((r) => r.kind === "LayerBounds" && r.values.lb).at(-1);
  const imageShape = layer?.kind.startsWith("INPUT") ? shapeFromTensor(geometry) : null;
  const lb = imageBounds?.values.lb?.slice(lane * count, (lane + 1) * count).map(num) ?? [];
  const ub = imageBounds?.values.ub?.slice(lane * count, (lane + 1) * count).map(num) ?? [];
  const range = [...lb, ...ub].filter(Number.isFinite);
  const lo = range.length ? Math.min(...range) : 0, hi = range.length ? Math.max(...range) : 1;
  return <section className={`propagation level-${state.level}`} aria-label="Propagation">
    <header className="prop-heading"><h3>Propagation</h3><span>{index.domain} · {state.pass} pass</span><span className="muted">{live ? "Live" : index.complete ? "Recorded" : "Partial record"}</span></header>
    {!online && <p role="status">Offline. Showing cached records; reconnect to load more data and resume live updates.</p>}
    <div className="prop-playback">
      <button className="secondary" disabled={live || !records.length} onClick={() => {
        if (!playing && position >= records.length - 1) update({ cursor: records[0]!.record_id });
        setPlaying(!playing);
      }}>{playing ? "Pause" : "Play"}</button>
      <label className="prop-scrub">Step {Math.max(0, position + 1)} / {records.length}
        <input aria-label="Propagation step" type="range" min={0} max={Math.max(0, records.length - 1)} value={Math.max(0, position)}
          disabled={!records.length} onChange={(e) => { setPlaying(false); update({ cursor: records[Number(e.target.value)]!.record_id }); }} />
      </label>
      <label>Timing <select value={timing} onChange={(e) => setTiming(e.target.value)}><option value="normalized">Even steps</option><option value="recorded">Recorded</option></select></label>
      {state.cursor !== null && <button className="secondary" onClick={() => { setPlaying(false); update({ cursor: null }); }}>Latest</button>}
    </div>
    <div className="note" aria-live="polite">{current ? `${fmt(current.t_ms, 1)} ms · ${current.key ? `Layer ${current.key.layer_id} · ${current.key.pass_} · ${current.key.stage === "pre" ? "pre" : "post"} · version ${current.key.version}` : `${current.metadata.phase ?? "Phase"} · ${current.metadata.status ?? ""}`}` : live ? "Waiting for propagation records." : "No propagation records were produced. Inspect the run diagnostics or select another run."}</div>
    <nav className="prop-breadcrumb" aria-label="Inspection level">
      <button className="secondary" onClick={() => update({ level: "network" })}>Network</button><span>›</span>
      <button className="secondary" disabled={sel.layerId === null} onClick={() => update({ level: "layer" })}>Layer {sel.layerId}</button><span>›</span>
      <button className="secondary" disabled={sel.neuron === null} onClick={() => update({ level: "neuron" })}>Neuron {sel.neuron}</button>
    </nav>
    <div className="prop-split">
      <div className="prop-network">
        {model && <BlockNetwork model={model} selected={selected} layerId={sel.layerId} active={active} onSelect={chooseLayer} pass={state.pass} />}
      </div>
      <div className="prop-layer" ref={layerPane}>
        {!layer ? <Empty title="Select a layer" text="Choose a network layer to see its neurons." /> : <>
          <h3>Layer {layer.layer_id} <small>{layer.kind}</small></h3>
          <div className="prop-controls">
            <label>Pass <select value={state.pass} onChange={(e) => update({ pass: e.target.value as Pass })}>
              {(["forward", "backward", "refine"] as const).filter((p) => p === "forward" || (p === "backward" && index.domain === "dual") || passes.includes(p)).map((p) => <option key={p}>{p}</option>)}
            </select></label>
            {lanes > 1 && <label>Lane <select value={lane} onChange={(e) => { update({ lane: Number(e.target.value) }); onSelectNeuron(null); }}>
              {Array.from({ length: lanes }, (_, n) => <option key={n} value={n}>{n + 1}</option>)}
            </select></label>}
          </div>
          <StatusLegend />
          <LayerTrend records={records.filter((r) => r.key?.scope === "root" && r.key.layer_id === layer.layer_id && r.key.pass_ === countPass && r.record_id <= (state.cursor ?? Infinity))} pass={countPass} />
          {detail.pending ? <Empty title="Loading neurons…" text="Reading the selected recorded tensors." />
            : detail.error ? <div className="error" role="alert">{detail.error.message}<button className="secondary" onClick={detail.retry}>Retry</button></div>
            : shownRecords.length === 0 ? <Empty title={live ? "Waiting for this layer" : "No data at this step"}
              text={live ? "Recorded neurons appear when ACT reaches this layer and pass." : "Advance the replay or choose another pass."} />
            : <>
              <p className="note">Stability: {stabilityPass} pass.{state.pass === "backward" ? " Select an unstable neuron for alpha by specification row." : ""}</p>
              {imageShape && lb.length === count && ub.length === count && <div className="pixrow">
                <Pixels xs={lb} shape={imageShape} lo={lo >= 0 && hi <= 1 ? 0 : lo} hi={lo >= 0 && hi <= 1 ? 1 : hi} size="big" label="Lower bound" />
                <Pixels xs={ub} shape={imageShape} lo={lo >= 0 && hi <= 1 ? 0 : lo} hi={lo >= 0 && hi <= 1 ? 1 : hi} size="big" label="Upper bound" />
              </div>}
              <NeuronMap key={`${layer.layer_id}-${lane}`} statuses={statuses} shape={geometry} selected={sel.neuron} onSelect={chooseNeuron} />
            </>}
        </>}
      </div>
      <div className="prop-mobile-detail">
        {(neuron.error ?? before.error) && <div className="error">{(neuron.error ?? before.error)!.message}</div>}
        <NeuronDetail records={neuron.records} before={before.records} neuron={sel.neuron} lane={lane} domain={index.domain ?? ""} pass={state.pass} status={sel.neuron === null ? undefined : statuses[sel.neuron]} kind={layer?.kind ?? ""} />
      </div>
    </div>
    {index.ignored_records > 0 && <p className="note">{index.ignored_records} unsupported records were omitted by the recorder.</p>}
  </section>;
}

export function PropagationInspector({ sel, model }: { sel: Selection; model: ModelDescriptionOut | null }) {
  const index = usePropagation(sel.runId);
  const { state } = usePropagationSelection();
  const { neuron, before, lane, statuses, layer } = useEvidence(sel, model, index.data);
  if (!sel.runId || sel.neuron === null) return <Empty title="Select a neuron" text="Open a layer in Verification and choose a neuron." />;
  if (neuron.error || before.error) return <div className="error" role="alert">{(neuron.error ?? before.error)!.message}</div>;
  if (neuron.pending || before.pending) return <Empty title="Loading neuron…" text="" />;
  return <NeuronDetail records={neuron.records} before={before.records} neuron={sel.neuron} lane={lane}
    domain={index.data?.domain ?? ""} pass={state.pass} status={statuses[sel.neuron]} kind={layer?.kind ?? ""} />;
}

function StatusLegend() {
  return <div className="prop-legend">{(["active", "inactive", "unstable", "unknown"] as const).map((s) =>
    <span key={s}><i className={`prop-swatch ${s}`} />{s === "unknown" ? "Not recorded" : s === "unstable" ? "Unstable" : `Stable ${s}`}</span>)}</div>;
}

function BlockNetwork({ model, selected, layerId, active, onSelect, pass }: {
  model: ModelDescriptionOut; selected: PropagationRecordOut[]; layerId: number | null; active?: number;
  onSelect: (id: number) => void; pass: Pass;
}) {
  const svg = useRef<SVGSVGElement>(null);
  useEffect(() => { svg.current?.querySelector(".prop-node.selected")?.scrollIntoView({ block: "nearest" }); }, [layerId]);
  const blocks = groupLayers(model.layers);
  const positions = new Map<number, number>();
  let y = 8;
  const groups = blocks.map((block) => { const top = y; y += 22; for (const l of block.layers) { positions.set(l.layer_id, y); y += 56; } y += 12; return { ...block, top }; });
  return <svg ref={svg} className="prop-dag" viewBox={`0 0 216 ${y}`} role="group" aria-label="Block network">
    {model.layers.flatMap((l) => l.preds.filter((p) => positions.has(p)).map((p) =>
      <path key={`${p}-${l.layer_id}`} className="prop-edge" d={`M28 ${positions.get(p)! + 38} C8 ${positions.get(p)! + 50},8 ${positions.get(l.layer_id)!},28 ${positions.get(l.layer_id)! + 12}`} />))}
    {groups.map((block) => <g key={block.layers[0]!.layer_id}>
      <text x="28" y={block.top + 12} className="prop-block-label">{block.label}</text>
      {block.layers.map((l) => {
        const all = selected.filter((r) => r.key?.layer_id === l.layer_id);
        const rs = all.filter((r) => r.key?.pass_ === pass);
        const version = Math.max(0, ...rs.map((r) => r.key!.version));
        const r = rs.filter((r) => unstableShare(r) !== undefined).at(-1) ?? all.filter((r) => unstableShare(r) !== undefined).at(-1) ?? rs.at(-1);
        const c = r?.counts;
        const counts = [c?.n_active ?? 0, c?.n_inactive ?? 0, c?.n_unstable ?? 0];
        const total = counts.reduce((a, b) => a + b, 0);
        const share = unstableShare(r);
        let x = 32;
        return <g key={l.layer_id} transform={`translate(0,${positions.get(l.layer_id)})`} className={`prop-node${layerId === l.layer_id ? " selected" : ""}${active === l.layer_id ? " evaluating" : ""}`}
          role="button" tabIndex={0} aria-label={`Layer ${l.layer_id} ${l.kind}${active === l.layer_id ? ", current" : ""}${share === undefined ? "" : `, ${Math.round(share * 100)}% unstable`}`}
          onClick={() => onSelect(l.layer_id)} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect(l.layer_id); } }}>
          <rect x="28" y="0" width="180" height="48" rx="6" className={share === undefined ? "" : share > 0.5 ? "mostly-unstable" : "mostly-stable"} />
          <text x="36" y="18">{l.layer_id} · {l.kind}</text>
          <text x="36" y="34" className="prop-node-meta">{active === l.layer_id ? "Current · " : ""}{version > 0 ? `Revisit ${version}` : `${l.out_vars} neurons`}{layerId === l.layer_id ? " ✓" : ""}</text>
          {total > 0 && counts.map((n, i) => { const left = x; const width = n / total * 172; x += width; return <rect key={i} x={left} y="41" width={width} height="4" className={`prop-share ${["active", "inactive", "unstable"][i]}`} />; })}
          <title>{total ? `${r?.key?.pass_} pass: ${counts[0]} active, ${counts[1]} inactive, ${counts[2]} unstable` : "No stability counts recorded"}</title>
        </g>;
      })}
    </g>)}
  </svg>;
}

function LayerTrend({ records, pass }: { records: PropagationRecordOut[]; pass: string }) {
  const points = records.filter((r) => unstableShare(r) !== undefined);
  if (!points.length) return <p className="note">No stability counts at this step.</p>;
  const x = (i: number) => 30 + i / Math.max(1, points.length - 1) * 280;
  return <figure className="prop-trend"><figcaption>Unstable share · {pass} pass</figcaption>
    <svg viewBox="0 0 330 90" role="img" aria-label="Recorded unstable neuron share over successive steps">
      <line x1="30" y1="65" x2="310" y2="65" className="prop-axis" />
      <text x="0" y="18">100%</text><text x="12" y="67">0</text>
      <polyline points={points.map((p, i) => `${x(i)},${65 - unstableShare(p)! * 50}`).join(" ")} className="prop-trend-line" />
      {points.map((p, i) => <circle key={p.record_id} cx={x(i)} cy={65 - unstableShare(p)! * 50} r="3" className="prop-trend-dot"><title>{fmt(p.t_ms, 1)} ms: {Math.round(unstableShare(p)! * 100)}%</title></circle>)}
      <text x="30" y="84">{points.length} recorded {points.length === 1 ? "step" : "steps"}</text>
    </svg>
  </figure>;
}
