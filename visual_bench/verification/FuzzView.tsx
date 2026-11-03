// ACTFuzzer run view (VER-06): live progress, coverage/violation timeline, strategies, counterexamples.
import { useEffect, useState } from "react";
import { api, fmt, followRun, num } from "../api";
import type { FuzzCounterexampleOut, FuzzPointOut, FuzzingOut, ModelDescriptionOut } from "../generated/wire";
import { Empty } from "../workspace/Empty";
import { useQuery } from "../workspace/useQuery";

export function FuzzView({ runId, version, model }: { runId: string | null; version: number; model: ModelDescriptionOut | null }) {
  const [tick, setTick] = useState(0);
  const [shown, setShown] = useState<FuzzingOut | null>(null);
  const q = useQuery(runId ? `${runId}:${version}:${tick}` : null, () => api.fuzzing(runId!));
  useEffect(() => { if (q.status === "ok") setShown(q.data); }, [q]);
  useEffect(() => setShown(null), [runId]);
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
  return (
    <div className="fuzz">
      <Banner f={f} ces={ces} />
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
      <Timeline points={f.timeline} firstCe={f.counterexamples[0]?.iteration ?? null} />
      {f.strategies.length > 0 && <Strategies f={f} />}
      {f.counterexamples.length > 0 && <Counterexamples items={f.counterexamples} total={ces} model={model} />}
      {Object.keys(f.config).length > 0 && (
        <p className="note">ACT config: {Object.entries(f.config).map(([k, v]) => `${k}=${String(v)}`).join(" · ")}</p>
      )}
      <p className="note">{f.provenance.act_call} · {f.provenance.config}</p>
    </div>
  );
}

function Banner({ f, ces }: { f: FuzzingOut; ces: number }) {
  if (f.status === "failed") return <div className="banner bad"><b>Run failed.</b> The partial timeline below is what ACT reported before the failure.</div>;
  if (f.availability === "pending") {
    return <div className="banner"><b>Fuzzing…</b> {ces ? `${ces} counterexample(s) found so far.` : "No counterexample yet."}</div>;
  }
  if (ces > 0) {
    return <div className="banner bad"><b>Property violated (falsified).</b> ACT's PropertyChecker accepted {ces} concrete input(s) inside the input spec whose outputs violate the property.</div>;
  }
  return <div className="banner warn"><b>No counterexample found.</b> Fuzzing is heuristic: this is not a proof. Use interval or BaB to certify.</div>;
}

const W = 400, H = 150, PL = 34, PR = 34, PT = 8, PB = 22;

function Timeline({ points, firstCe }: { points: FuzzPointOut[]; firstCe: number | null }) {
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
        <polyline className="cov" points={cov} />
        <polyline className="ces" points={steps.join(" ")} />
      </svg>
    </>
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

function Counterexamples({ items, total, model }: { items: FuzzCounterexampleOut[]; total: number; model: ModelDescriptionOut | null }) {
  const [sel, setSel] = useState(0);
  const ce = items[Math.min(sel, items.length - 1)]!;
  return (
    <>
      <h3>Counterexamples <small>{items.length < total ? `first ${items.length} of ${total}` : `${total}`} · checked by ACT</small></h3>
      <div className="tblwrap"><table className="tbl">
        <thead><tr><th>#</th><th>iteration</th><th>time</th><th>strategy</th><th>kind</th><th>severity</th></tr></thead>
        <tbody>
          {items.map((c) => (
            <tr key={c.index} className={c.index === ce.index ? "rowsel" : "rowlink"} onClick={() => setSel(c.index)}>
              <td>{c.index + 1}</td><td className="mono">{c.iteration}</td><td className="mono">{fmt(c.elapsed_s, 3)}s</td>
              <td>{c.strategy ?? "—"}</td><td>{c.kind}{c.true_class !== null ? ` (class ${c.true_class})` : ""}</td>
              <td className="mono">{fmt(num(c.severity))}</td>
            </tr>
          ))}
        </tbody>
      </table></div>
      <CounterexampleDetail ce={ce} model={model} />
    </>
  );
}

function CounterexampleDetail({ ce, model }: { ce: FuzzCounterexampleOut; model: ModelDescriptionOut | null }) {
  const box = model?.input_specs[0];
  const lb = box?.lb.map(num), ub = box?.ub.map(num);
  const xs = ce.input.map(num), seed = ce.seed_input.map(num);
  const inBox = lb && ub && lb.length === xs.length;
  const shown = Math.min(xs.length, 64);
  return (
    <div className="proj">
      <div className="note">Counterexample #{ce.index + 1}, spec row {ce.spec_row}. {model?.output_spec ? `Property: ${model.output_spec.text}` : ""}</div>
      <div className="legend">
        {inBox && <span><i className="sw before" /> input box (INPUT_SPEC)</span>}
        <span><i className="sw ce" /> counterexample input</span>
        <span><i className="sw seed" /> seed input</span>
      </div>
      <div className="bars">
        {Array.from({ length: shown }, (_, i) => {
          const lo = inBox ? lb![i]! : Math.min(xs[i]!, seed[i]!), hi = inBox ? ub![i]! : Math.max(xs[i]!, seed[i]!);
          const span = hi - lo || 1;
          const at = (v: number) => `${((Math.max(lo, Math.min(hi, v)) - lo) / span) * 100}%`;
          return (
            <div key={i} className="barrow" title={`x[${i}] = ${xs[i]} (seed ${seed[i]})${inBox ? `, box [${lo}, ${hi}]` : ""}`}>
              <span className="idx">{i}</span>
              <span className="track">
                {inBox && <span className="bar before" style={{ left: 0, width: "100%" }} />}
                <span className="pin seed" style={{ left: at(seed[i]!) }} />
                <span className="pin ce" style={{ left: at(xs[i]!) }} />
              </span>
              <span className="vals mono">{fmt(xs[i]!)}</span>
            </div>
          );
        })}
      </div>
      {xs.length > shown && <div className="note">Showing {shown} of {xs.length} input values.</div>}
      <div className="note">Output y = [{ce.output.map((v) => fmt(num(v))).join(", ")}]</div>
    </div>
  );
}

function pct(x: number): string {
  return `${(x * 100).toFixed(1)}%`;
}
