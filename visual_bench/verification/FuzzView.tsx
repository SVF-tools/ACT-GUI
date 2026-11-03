// ACTFuzzer run view (VER-06): live progress, coverage/violation timeline, inputs, counterexamples, strategies,
// saving counterexamples on the run record and exporting saved ones (VNN-LIB 2.0 assignment, image .png).
import { useEffect, useMemo, useState } from "react";
import { api, fmt, followRun, num } from "../api";
import type { FuzzCounterexampleOut, FuzzFrameOut, FuzzPointOut, FuzzingOut, ModelDescriptionOut, SavedCounterexampleOut } from "../generated/wire";
import { Empty } from "../workspace/Empty";
import { useQuery } from "../workspace/useQuery";
import { classLabel, downloadBlob, imagePng, imageShape, PerturbCompare, Pixels, specImageShape, type Shape } from "../workspace/pixels";
import { StopButton } from "./RunsPanel";

export function FuzzView({ runId, version, model }: { runId: string | null; version: number; model: ModelDescriptionOut | null }) {
  const [tick, setTick] = useState(0);
  const [shown, setShown] = useState<FuzzingOut | null>(null);
  const [frameSel, setFrameSel] = useState<number | null>(null); // null follows the latest frame
  const q = useQuery(runId ? `${runId}:${version}:${tick}` : null, () => api.fuzzing(runId!));
  useEffect(() => { if (q.status === "ok") setShown(q.data); }, [q]);
  useEffect(() => { setShown(null); setFrameSel(null); }, [runId]);
  const live = shown !== null && shown.run_id === runId && (shown.status === "queued" || shown.status === "running");
  useEffect(() => {
    if (!live || !runId) return;
    return followRun(runId, () => setTick((t) => t + 1));
  }, [live, runId]);

  if (!runId) return <Empty title="No run selected" text="Pick a model, choose method “fuzz (ACTFuzzer)” and press Run ACT." />;
  if (q.status === "error") return <div className="error">{q.message}</div>;
  if (!shown || shown.run_id !== runId) return <Empty title="Loading fuzzing record…" text="" />;
  const f = shown;
  if (f.availability === "unsupported") return <Empty title="Not a fuzzing run" text="This run used a verification method. Start a run with method “fuzz (ACTFuzzer)”." />;
  const last = f.timeline.at(-1) ?? null;
  const s = f.summary;
  const ces = s?.counterexample_count ?? last?.counterexamples ?? 0;
  const frames = f.frames ?? [];
  const refresh = () => setTick((t) => t + 1);
  const savedItems = f.saved ?? [];
  const saved = new Set(savedItems.map((s) => s.counterexample.index));
  const onSave = async (index: number) => { await api.saveCounterexample(f.run_id, index); refresh(); };
  return (
    <div className="fuzz">
      <Banner f={f} ces={ces} onStopped={refresh} />
      <div className="kv">
        <span>iterations</span><b>{s?.iterations ?? last?.iteration ?? 0}{f.options ? ` / ${f.options.max_iterations}` : ""}</b>
        <span>elapsed</span><b>{fmt(s?.elapsed_s ?? last?.elapsed_s ?? 0, 2)} s{s && s.elapsed_s > 0 ? ` · ${(s.iterations / s.elapsed_s).toFixed(1)} it/s` : ""}</b>
        <span>neuron coverage</span><b>{pct(s?.neuron_coverage ?? last?.coverage ?? 0)}{s ? ` (${s.coverage_strategy})` : ""}</b>
        <span>counterexamples</span><b className={ces ? "state bad" : ""}>{ces}</b>
        <span>seed corpus</span><b>{s?.seeds_explored ?? last?.corpus ?? 0}</b>
        {s && <><span>mutations</span><b>{s.total_mutations}</b></>}
        {s && <><span>never activated</span><b>{s.never_activated_count}{s.never_activated_sample.length ? ` · ${s.never_activated_sample.slice(0, 6).join(", ")}` : ""}</b></>}
        <span>rng seed</span><b>{f.options?.rng_seed ?? "—"}{s ? ` · device ${s.device}` : ""}</b>
      </div>
      <h3>Progress <small>{live ? "live from committed fuzz.progress events" : "recorded timeline"}</small></h3>
      <div className="fuzzlive">
        <div className="fuzzlive-chart">
          <Timeline points={f.timeline} firstCe={f.counterexamples[0]?.iteration ?? null}
            marker={frames.length ? frames[Math.min(frameSel ?? Infinity, frames.length - 1)]!.iteration : null} />
        </div>
        <Mutations frames={frames} live={live} model={model} sel={frameSel} onSel={setFrameSel} saved={saved} onSave={onSave} />
      </div>
      {savedItems.length > 0 && <Saved runId={f.run_id} items={savedItems} model={model} />}
      {f.availability === "available" && <Inputs f={f} model={model} />}
      {f.counterexamples.length > 0 && (
        <Counterexamples items={f.counterexamples} total={ces} model={model} saved={saved} onSave={onSave} live={live} />
      )}
      {f.strategies.length > 0 && <Strategies f={f} />}
      {Object.keys(f.config).length > 0 && (
        <p className="note">ACT config: {Object.entries(f.config).map(([k, v]) => `${k}=${String(v)}`).join(" · ")}</p>
      )}
      <p className="note">{f.provenance.act_call} · {f.provenance.config}</p>
    </div>
  );
}

function Banner({ f, ces, onStopped }: { f: FuzzingOut; ces: number; onStopped: () => void }) {
  if (f.status === "failed") return <div className="banner bad"><b>Run failed.</b> The partial timeline below is what ACT reported before the failure.</div>;
  if (f.availability === "pending") {
    return (
      <div className="banner bannerrow">
        <span><b>Fuzzing…</b> {ces ? `${ces} counterexample(s) found so far.` : "No counterexample yet."}</span>
        {(f.status === "queued" || f.status === "running") && <StopButton runId={f.run_id} method="fuzz" onStopped={onStopped} />}
      </div>
    );
  }
  const stopped = f.summary?.stopped
    ? <> Stopped by the user after {f.summary.iterations} iteration(s); ACT's report covers those iterations only.</> : null;
  if (stopped && ces === 0) return <div className="banner warn"><b>Stopped, no counterexample found.</b>{stopped} Fuzzing is heuristic: this is not a proof.</div>;
  if (ces > 0) {
    return <div className="banner bad"><b>Property violated (falsified).</b> ACT's PropertyChecker accepted {ces} concrete input(s) inside the input spec whose outputs violate the property.{stopped}</div>;
  }
  return <div className="banner warn"><b>No counterexample found.</b> Fuzzing is heuristic: this is not a proof. Use interval or BaB to certify.</div>;
}

const W = 400, H = 150, PL = 34, PR = 34, PT = 8, PB = 22;

function Timeline({ points, firstCe, marker }: { points: FuzzPointOut[]; firstCe: number | null; marker: number | null }) {
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

const PLAY_MS = 700;

// The mutated input beside the progress chart: the latest frame while running, a playable filmstrip afterwards.
function Mutations({ frames, live, model, sel, onSel, saved, onSave }: {
  frames: FuzzFrameOut[]; live: boolean; model: ModelDescriptionOut | null; sel: number | null; onSel: (i: number | null) => void;
  saved: Set<number>; onSave: (index: number) => Promise<void>;
}) {
  const [playing, setPlaying] = useState(false);
  const n = frames.length;
  const idx = Math.min(sel ?? n - 1, n - 1);
  useEffect(() => {
    if (!playing || n < 2) return;
    const t = setInterval(() => onSel((idx + 1) % n), PLAY_MS);
    return () => clearInterval(t);
  }, [playing, idx, n, onSel]);
  useEffect(() => { if (live) setPlaying(false); }, [live]);

  const fr = frames[idx];
  if (!fr) {
    return (
      <div className="mutpanel">
        <div className="note">{live ? "Waiting for the first mutated input…" : "No mutated-input frames in this record (written before they were captured). Re-run to see them."}</div>
      </div>
    );
  }
  const x = fr.input.map(num), seed = fr.seed_input.map(num);
  const delta = x.map((v, i) => v - seed[i]!);
  const linf = delta.reduce((m, d) => Math.max(m, Math.abs(d)), 0);
  const d = x.length, shape = modelShape(model, d), box = inputBox(model, d);
  const [lo, hi] = box ? finiteRange([...box.lb, ...box.ub]) : finiteRange([...x, ...seed]);
  return (
    <div className="mutpanel">
      <div className="muthead">
        <b>Mutated input</b>
        {live ? <span className="chip s-running">live · latest</span> : <span className="muted">frame {idx + 1} / {n}</span>}
        {fr.violation && <span className="chip bad">counterexample</span>}
        {fr.counterexample && <SaveButton index={fr.counterexample.index} saved={saved.has(fr.counterexample.index)} onSave={onSave} />}
      </div>
      {shape ? (
        <div className="mutimgs">
          <Pixels xs={x} shape={shape} lo={lo} hi={hi} label="mutated" size="big" />
          <div className="mutside">
            <Pixels xs={seed} shape={shape} lo={lo} hi={hi} label={`seed row ${fr.seed_row}`} />
            <Pixels xs={delta} shape={shape} lo={-linf} hi={linf} mode="signed" label="δ (red +, blue −)" />
          </div>
        </div>
      ) : <DeltaBars delta={delta} box={box} />}
      <div className="mutmeta mono muted">
        <span>it {fr.iteration} · {fmt(fr.elapsed_s, 2)} s</span>
        <span>{fr.strategy ?? "—"} · depth {fr.depth}</span>
        <span>‖δ‖∞ {fmt(linf, 4)}</span>
      </div>
      {!live && n > 1 && (
        <div className="mutctl">
          <button className="secondary" onClick={() => setPlaying(!playing)}>{playing ? "Pause" : "Play"}</button>
          <input type="range" min={0} max={n - 1} value={idx} aria-label="mutated input frame"
            onChange={(e) => { setPlaying(false); onSel(Number(e.target.value)); }} />
        </div>
      )}
      <div className="note">Lane 0 of the batch ACT mutated, sampled with the progress reports; δ is relative to its INPUT row.</div>
    </div>
  );
}

function Strategies({ f }: { f: FuzzingOut }) {
  const total = f.strategies.reduce((a, s) => a + s.selected, 0) || 1;
  return (
    <>
      <h3>Mutation strategies <small>weights from ACT's fuzzing config</small></h3>
      <table className="tbl">
        <thead><tr><th>strategy</th><th>weight</th><th>iterations</th><th>share</th><th>violations</th></tr></thead>
        <tbody>
          {f.strategies.map((s) => (
            <tr key={s.name} className={s.weight === 0 && s.selected === 0 ? "muted" : ""}>
              <td>{s.name}</td><td className="mono">{s.weight}</td><td className="mono">{s.selected}</td>
              <td><span className="track share"><span className="bar after" style={{ left: 0, width: `${(s.selected / total) * 100}%` }} /></span></td>
              <td className={s.violations ? "mono state bad" : "mono"}>{s.violations}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

const MAX_DIMS = 64;
const GALLERY = 8;
type Box = { lb: number[]; ub: number[] } | null;

// The spec's tensor shape when it matches the input length, else a C x S x S guess from the length alone.
function modelShape(model: ModelDescriptionOut | null, d: number): Shape | null {
  const spec = model?.input_specs[0];
  const s = spec ? specImageShape(spec.shape, spec.dataset) : null;
  return s && s.c * s.h * s.w === d ? s : imageShape(d);
}

function inputBox(model: ModelDescriptionOut | null, d: number): Box {
  const b = model?.input_specs[0];
  return b && b.lb.length === d ? { lb: b.lb.map(num), ub: b.ub.map(num) } : null;
}

function argmax(ys: number[]): number {
  let k = 0;
  for (let i = 1; i < ys.length; i++) if (ys[i]! > ys[k]!) k = i;
  return k;
}

function finiteRange(xs: number[]): [number, number] {
  let lo = Infinity, hi = -Infinity;
  for (const v of xs) if (Number.isFinite(v)) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
  return lo <= hi ? [lo, hi] : [0, 1];
}

// Display-side summary of one ACT counterexample; "predicted" is argmax of the output ACT recorded.
type Ce = {
  ce: FuzzCounterexampleOut; x: number[]; seed: number[]; y: number[]; ySeed: number[] | null;
  pred: number; seedPred: number | null; delta: number[]; linf: number; l2: number; changed: number; misclassified: boolean;
};

function analyze(ce: FuzzCounterexampleOut): Ce {
  const x = ce.input.map(num), seed = ce.seed_input.map(num), y = ce.output.map(num);
  const ySeed = ce.seed_output ? ce.seed_output.map(num) : null;
  const delta = x.map((v, i) => v - seed[i]!);
  let linf = 0, sq = 0, changed = 0;
  for (const d of delta) { linf = Math.max(linf, Math.abs(d)); sq += d * d; if (Math.abs(d) > 1e-9) changed++; }
  const pred = argmax(y);
  return { ce, x, seed, y, ySeed, pred, seedPred: ySeed ? argmax(ySeed) : null, delta, linf, l2: Math.sqrt(sq), changed,
           misclassified: ce.true_class !== null && pred !== ce.true_class };
}

// Signed perturbation per input dimension, scaled by the input box width when the box is known.
function DeltaBars({ delta, box }: { delta: number[]; box: Box }) {
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

function Inputs({ f, model }: { f: FuzzingOut; model: ModelDescriptionOut | null }) {
  const seeds = f.seeds ?? [];
  const d = seeds[0]?.input.length ?? f.counterexamples[0]?.input.length ?? model?.input_dim ?? 0;
  const box = inputBox(model, d);
  const shape = modelShape(model, d);
  const perRow = new Map<number, number>(), expected = new Map<number, number>();
  for (const c of f.counterexamples) {
    perRow.set(c.spec_row, (perRow.get(c.spec_row) ?? 0) + 1);
    if (c.true_class !== null) expected.set(c.spec_row, c.true_class);
  }
  const widths = box ? box.ub.map((u, i) => u - box.lb[i]!) : [];
  const [wlo, whi] = finiteRange(widths);
  const [xlo, xhi] = box ? finiteRange([...box.lb, ...box.ub]) : finiteRange(seeds.flatMap((s) => s.input.map(num)));
  return (
    <>
      <h3>Inputs <small>seeds are the model's INPUT rows; outputs from ACT's model forward</small></h3>
      <p className="note">
        {d} input dims{shape ? ` (drawn as ${shape.c}×${shape.h}×${shape.w})` : ""}
        {box ? ` · input box width ${wlo === whi ? fmt(wlo) : `${fmt(wlo)}…${fmt(whi)}`}, values in [${fmt(xlo)}, ${fmt(xhi)}]` : ""}
        {model?.output_spec ? ` · property: ${model.output_spec.text}` : ""}
      </p>
      {seeds.length === 0 ? <div className="note">This record has no seed outputs (written before they were captured). Re-run to see them.</div> : (
        <div className="tblwrap"><table className="tbl">
          <thead><tr><th>row</th><th>input</th>{box && <th title="seed lies inside INPUT_SPEC">in box</th>}<th>output y</th>{expected.size > 0 && <><th>argmax</th><th>expected</th></>}<th>counterexamples</th></tr></thead>
          <tbody>
            {seeds.map((s) => {
              const x = s.input.map(num), y = s.output.map(num), p = argmax(y), e = expected.get(s.row);
              const inside = box && x.every((v, i) => box.lb[i]! <= v && v <= box.ub[i]!);
              return (
                <tr key={s.row}>
                  <td className="mono">{s.row}</td>
                  <td>{shape ? <Pixels xs={x} shape={shape} lo={xlo} hi={xhi} label="" /> : <span className="mono">{vec(x, 6)}</span>}</td>
                  {box && <td className={inside ? "mono" : "mono state warn"}>{inside ? "yes" : "no"}</td>}
                  <td className="mono">{vec(y, 6)}</td>
                  {expected.size > 0 && <><td className="mono">{p}</td><td className={e !== undefined && e !== p ? "mono state bad" : "mono"}>{e ?? "—"}</td></>}
                  <td className={perRow.get(s.row) ? "mono state bad" : "mono"}>{perRow.get(s.row) ?? 0}</td>
                </tr>
              );
            })}
          </tbody>
        </table></div>
      )}
    </>
  );
}

function Counterexamples({ items, total, model, saved, onSave, live }: {
  items: FuzzCounterexampleOut[]; total: number; model: ModelDescriptionOut | null;
  saved: Set<number>; onSave: (index: number) => Promise<void>; live: boolean;
}) {
  const [sel, setSel] = useState(0);
  const [all, setAll] = useState(false);
  const list = useMemo(() => items.map(analyze), [items]);
  const a = list[Math.min(sel, list.length - 1)]!;
  const d = a.x.length, box = inputBox(model, d), shape = modelShape(model, d);
  const ds = model?.input_specs[0]?.dataset ?? null;
  const [lo, hi] = box ? finiteRange([...box.lb, ...box.ub]) : finiteRange(list.flatMap((c) => [...c.x, ...c.seed]));
  const groups = new Map<string, number>();
  for (const c of list) {
    const k = c.ce.true_class !== null ? `${classLabel(ds, c.ce.true_class)} → ${classLabel(ds, c.pred)}` : `${c.ce.kind} · spec row ${c.ce.spec_row}`;
    groups.set(k, (groups.get(k) ?? 0) + 1);
  }
  const mis = list.filter((c) => c.misclassified).length;
  const linfs = list.map((c) => c.linf).sort((x, y) => x - y);
  return (
    <>
      <h3>Counterexamples <small>{live ? `${items.length} seen live of ${total}` : items.length < total ? `first ${items.length} of ${total}` : `${total}`} · mutated inputs ACT's PropertyChecker accepted</small></h3>
      <div className="findings">
        {list.some((c) => c.ce.true_class !== null) && <span className={mis ? "chip warn" : "chip"}>{mis} of {list.length} misclassified</span>}
        {[...groups].map(([k, n]) => <span key={k} className="chip">{k} ×{n}</span>)}
        <span className="chip" title="L∞ distance between mutated input and its seed">‖δ‖∞ min {fmt(linfs[0]!)} · median {fmt(linfs[Math.floor(linfs.length / 2)]!)}</span>
      </div>
      <div className="cegrid">
        {(all ? list : list.slice(0, GALLERY)).map((c, i) => (
          <button key={c.ce.index} className={i === sel ? "cecard active" : "cecard"} onClick={() => setSel(i)}>
            <span className="cehead"><b>#{c.ce.index + 1}</b><span className="muted">it {c.ce.iteration} · {c.ce.strategy ?? "—"}</span>{saved.has(c.ce.index) && <span className="chip good">saved</span>}</span>
            {shape ? (
              <span className="pixrow">
                <Pixels xs={c.seed} shape={shape} lo={lo} hi={hi} label="seed" />
                <Pixels xs={c.x} shape={shape} lo={lo} hi={hi} label="mutated" />
                <Pixels xs={c.delta} shape={shape} lo={-c.linf} hi={c.linf} mode="signed" label="δ" />
              </span>
            ) : <DeltaBars delta={c.delta} box={box} />}
            <span className="ceclass">
              {c.ce.true_class !== null ? (
                <><b>{classLabel(ds, c.ce.true_class)}</b> → <b className={c.misclassified ? "state bad" : ""}>{classLabel(ds, c.pred)}</b>
                  {c.misclassified && <span className="chip bad">misclassified</span>}</>
              ) : <>{c.ce.kind} · row {c.ce.spec_row}</>}
            </span>
            <span className="cemeta mono muted"><span>severity {fmt(num(c.ce.severity), 3)}</span><span>‖δ‖∞ {fmt(c.linf, 3)}</span></span>
          </button>
        ))}
      </div>
      {list.length > GALLERY && (
        <button className="secondary more" onClick={() => setAll(!all)}>{all ? `Show first ${GALLERY}` : `Show all ${list.length}`}</button>
      )}
      <CounterexampleDetail a={a} model={model} box={box} shape={shape} lo={lo} hi={hi} saved={saved.has(a.ce.index)} onSave={onSave} />
    </>
  );
}

function CounterexampleDetail({ a, model, box, shape, lo, hi, saved, onSave }: {
  a: Ce; model: ModelDescriptionOut | null; box: Box; shape: Shape | null; lo: number; hi: number;
  saved: boolean; onSave: (index: number) => Promise<void>;
}) {
  const { ce, x: xs, seed } = a;
  const ds = model?.input_specs[0]?.dataset ?? null;
  const shown = Math.min(xs.length, MAX_DIMS);
  const top = a.delta.map((v, i) => [i, v] as const).filter(([, v]) => Math.abs(v) > 1e-9)
    .sort((p, q) => Math.abs(q[1]) - Math.abs(p[1])).slice(0, 5);
  return (
    <div className="proj">
      <div className="note">
        Counterexample #{ce.index + 1} from seed row {ce.spec_row}, found at iteration {ce.iteration} ({fmt(ce.elapsed_s, 3)} s) by {ce.strategy ?? "an unknown strategy"}.
        {model?.output_spec ? ` Property: ${model.output_spec.text}` : ""}
        {" "}<SaveButton index={ce.index} saved={saved} onSave={onSave} />
      </div>
      <div className="kv">
        <span>outcome</span>
        <b>
          {ce.true_class !== null
            ? <>expected {classLabel(ds, ce.true_class)}, seed predicts {a.seedPred === null ? "?" : classLabel(ds, a.seedPred)}, mutated predicts <span className={a.misclassified ? "state bad" : ""}>{classLabel(ds, a.pred)}</span></>
            : <>{ce.kind} violated on spec row {ce.spec_row}</>}
        </b>
        <span>severity</span><b>{fmt(num(ce.severity))} <span className="muted">(ACT's signed violation margin)</span></b>
        <span>perturbation</span><b>‖δ‖∞ {fmt(a.linf)} · ‖δ‖₂ {fmt(a.l2)} · {a.changed} of {xs.length} dims changed</b>
        {top.length > 0 && <><span>largest changes</span><b className="mono">{top.map(([i, v]) => `x[${i}] ${v >= 0 ? "+" : ""}${fmt(v, 3)}`).join(" · ")}</b></>}
      </div>
      <h4>Input: seed vs mutated</h4>
      {shape ? (
        <PerturbCompare base={seed} perturbed={xs} shape={shape} lo={lo} hi={hi} baseLabel="seed" perturbedLabel="mutated (counterexample)" />
      ) : (
        <>
          <div className="legend">
            {box && <span><i className="sw before" /> input box (INPUT_SPEC)</span>}
            <span><i className="sw ce" /> counterexample input</span>
            <span><i className="sw seed" /> seed input</span>
          </div>
          <div className="bars">
            {Array.from({ length: shown }, (_, i) => {
              const l = box ? box.lb[i]! : Math.min(xs[i]!, seed[i]!), h = box ? box.ub[i]! : Math.max(xs[i]!, seed[i]!);
              const span = h - l || 1;
              const at = (v: number) => `${((Math.max(l, Math.min(h, v)) - l) / span) * 100}%`;
              return (
                <div key={i} className="barrow" title={`x[${i}] = ${xs[i]} (seed ${seed[i]})${box ? `, box [${l}, ${h}]` : ""}`}>
                  <span className="idx">{i}</span>
                  <span className="track">
                    {box && <span className="bar before" style={{ left: 0, width: "100%" }} />}
                    <span className="pin seed" style={{ left: at(seed[i]!) }} />
                    <span className="pin ce" style={{ left: at(xs[i]!) }} />
                  </span>
                  <span className="vals mono">{fmt(seed[i]!, 3)} → {fmt(xs[i]!, 3)}</span>
                </div>
              );
            })}
          </div>
          {xs.length > shown && <div className="note">Showing {shown} of {xs.length} input values.</div>}
        </>
      )}
      <OutputCompare a={a} />
    </div>
  );
}

function OutputCompare({ a }: { a: Ce }) {
  const ys = a.y, ss = a.ySeed;
  const [vlo, vhi] = finiteRange([0, ...ys, ...(ss ?? [])]);
  const span = vhi - vlo || 1;
  const at = (v: number) => ((Math.max(vlo, Math.min(vhi, v)) - vlo) / span) * 100;
  const n = Math.min(ys.length, MAX_DIMS);
  const exp = a.ce.true_class;
  return (
    <>
      <h4>Output: seed vs mutated</h4>
      <div className="legend">
        {ss && <span><i className="sw seed" /> seed output</span>}
        <span><i className="sw ce" /> counterexample output</span>
        {exp !== null && <span><b>E</b> expected class · <b>P</b> argmax of the mutated output</span>}
      </div>
      <div className="bars">
        {Array.from({ length: n }, (_, i) => {
          const y = ys[i]!, s = ss?.[i];
          const from = s === undefined ? at(0) : at(s), to = at(y);
          return (
            <div key={i} className={`barrow outrow${exp !== null && i === a.pred ? " pred" : ""}`} title={`y[${i}] = ${y}${s !== undefined ? ` (seed ${s})` : ""}`}>
              <span className="idx">{i}</span>
              <span className="track">
                <span className="zero" style={{ left: `${at(0)}%` }} />
                <span className="bar shift" style={{ left: `${Math.min(from, to)}%`, width: `${Math.abs(to - from)}%` }} />
                {s !== undefined && <span className="pin seed" style={{ left: `${from}%` }} />}
                <span className="pin ce" style={{ left: `${to}%` }} />
              </span>
              <span className="vals mono">{s !== undefined ? `${fmt(s, 3)} → ` : ""}{fmt(y, 3)}</span>
              <span className="tags">
                {exp === i && <span className="chip">E</span>}
                {exp !== null && i === a.pred && <span className={a.misclassified ? "chip bad" : "chip"}>P</span>}
              </span>
            </div>
          );
        })}
      </div>
      {ys.length > n && <div className="note">Showing {n} of {ys.length} outputs.</div>}
      {!ss && <div className="note">Seed output not recorded for this run (older record).</div>}
    </>
  );
}

// Saves ACT's counterexample #index on the run record (idempotent on the server).
function SaveButton({ index, saved, onSave }: { index: number; saved: boolean; onSave: (index: number) => Promise<void> }) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  if (saved) return <span className="chip good" title="saved on this run's record; export it under Saved counterexamples">saved #{index + 1}</span>;
  async function save() {
    setBusy(true);
    setErr(null);
    try {
      await onSave(index);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <button className="secondary small" disabled={busy} onClick={save}>{busy ? "Saving…" : `Save counterexample #${index + 1}`}</button>
      {err && <span className="state bad">{err}</span>}
    </>
  );
}

// Counterexamples the user saved on this run, each exportable as a VNN-COMP counterexample file and, for images, a PNG.
function Saved({ runId, items, model }: { runId: string; items: SavedCounterexampleOut[]; model: ModelDescriptionOut | null }) {
  const list = useMemo(() => items.map((s) => ({ s, a: analyze(s.counterexample) })), [items]);
  const d = list[0]!.a.x.length, box = inputBox(model, d), shape = modelShape(model, d);
  const ds = model?.input_specs[0]?.dataset ?? null;
  const [lo, hi] = box ? finiteRange([...box.lb, ...box.ub]) : finiteRange(list.flatMap(({ a }) => [...a.x, ...a.seed]));
  const [err, setErr] = useState<string | null>(null);
  async function png(a: Ce) {
    setErr(null);
    try {
      downloadBlob(await imagePng(a.x, shape!, lo, hi), `${runId}-ce${a.ce.index}.png`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }
  return (
    <>
      <h3>Saved counterexamples <small>{items.length} on this run's record · export ACT's counterexample input</small></h3>
      <div className="cegrid">
        {list.map(({ s, a }) => (
          <div key={a.ce.index} className="cecard saved">
            <span className="cehead"><b>#{a.ce.index + 1}</b><span className="muted">it {a.ce.iteration} · {a.ce.strategy ?? "—"}</span></span>
            {shape ? (
              <span className="pixrow">
                <Pixels xs={a.seed} shape={shape} lo={lo} hi={hi} label="seed" />
                <Pixels xs={a.x} shape={shape} lo={lo} hi={hi} label="mutated" />
                <Pixels xs={a.delta} shape={shape} lo={-a.linf} hi={a.linf} mode="signed" label="δ" />
              </span>
            ) : <DeltaBars delta={a.delta} box={box} />}
            <span className="ceclass">
              {a.ce.true_class !== null
                ? <><b>{classLabel(ds, a.ce.true_class)}</b> → <b className={a.misclassified ? "state bad" : ""}>{classLabel(ds, a.pred)}</b></>
                : <>{a.ce.kind} · row {a.ce.spec_row}</>}
            </span>
            <span className="cemeta mono muted"><span>‖δ‖∞ {fmt(a.linf, 3)}</span><span>saved {new Date(s.saved_at).toLocaleString()}</span></span>
            <span className="ceactions">
              <a className="button secondary small" href={api.savedCounterexampleUrl(runId, a.ce.index)} download
                title="VNN-COMP result: sat + VNN-LIB 2.0 command-line assignment of X (input) and Y (output), float64">Export counterexample (VNN-LIB 2.0)</a>
              {shape && <button className="secondary small" onClick={() => png(a)}
                title={`${shape.w}×${shape.h} PNG of the mutated input at native resolution`}>Export image (.png)</button>}
            </span>
          </div>
        ))}
      </div>
      {err && <div className="error">{err}</div>}
    </>
  );
}

function vec(xs: number[], k: number): string {
  return `[${xs.slice(0, k).map((v) => fmt(v, 3)).join(", ")}${xs.length > k ? `, … (${xs.length})` : ""}]`;
}

function pct(x: number): string {
  return `${(x * 100).toFixed(1)}%`;
}
