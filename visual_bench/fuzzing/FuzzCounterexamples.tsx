import { useMemo, useState } from "react";
import { fmt, num } from "../shared/wire";
import type { FuzzCounterexampleOut, ModelDescriptionOut } from "../generated/wire";
import { classLabel, Pixels, PerturbCompare, type Shape } from "../shared/ui/pixels";
import { analyze, inputBox, modelShape, finiteRange, MAX_DIMS, type Box, type Ce } from "./presentation";
import { DeltaBars } from "./DeltaBars";
import { SaveButton } from "./SaveButton";

const GALLERY = 5;

export function FuzzCounterexamples({ items, total, model, saved, onSave, live }: {
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
