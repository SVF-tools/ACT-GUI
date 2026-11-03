import { fmt, num } from "../api";
import type { InputSpecOut, ModelDescriptionOut, OutputSpecOut } from "../generated/wire";
import { classLabel, specImageShape } from "../workspace/pixels";
import { InputDomain } from "./InputDomain";

export function SpecPanel({ model, selectedLayer }: { model: ModelDescriptionOut; selectedLayer: number | null }) {
  const layer = model.layers.find((l) => l.layer_id === selectedLayer) ?? null;
  const images = model.input_specs.some((s) => specImageShape(s.shape, s.dataset) !== null);
  return (
    <div className={images ? "split stack" : "split"}>
      <section className="panel">
        <h2>Specification</h2>
        {model.input_specs.map((s) => {
          const shape = specImageShape(s.shape, s.dataset);
          return (
            <div key={s.layer_id} className="spec">
              <div className="label">Input domain · {s.kind} (layer {s.layer_id}){s.dataset ? ` · ${s.dataset}` : ""}</div>
              {shape ? (
                <>
                  <InputDomain spec={s} shape={shape} />
                  <details><summary className="note">numeric bounds</summary><BoundsTable s={s} /></details>
                </>
              ) : <BoundsTable s={s} />}
            </div>
          );
        })}
        {model.output_spec ? (
          <div className="spec">
            <div className="label">Output property · {model.output_spec.kind} (layer {model.output_spec.layer_id})</div>
            {model.output_spec.kind === "TOP1_ROBUST" && model.output_spec.true_class !== null ? (
              <>
                <Robustness o={model.output_spec} dataset={model.input_specs[0]?.dataset ?? null} classes={model.output_dim} />
                <details><summary className="note">constraints as ACT checks them</summary><p className="mono">{model.output_spec.text}</p></details>
              </>
            ) : <p className="mono">{model.output_spec.text}</p>}
          </div>
        ) : <div className="note">No ASSERT layer: this network carries no output property.</div>}
        <div className="note">sha256 {model.sha256.slice(0, 16)}… · inputs {model.input_dim} · outputs {model.output_dim}</div>
      </section>
      <section className="panel">
        <h2>Layer detail</h2>
        {!layer ? <div className="note">Click a layer in the network.</div> : (
          <>
            <div className="kv"><span>id</span><b>{layer.layer_id}</b><span>kind</span><b>{layer.kind}</b>
              <span>vars</span><b>{layer.in_vars} → {layer.out_vars}</b>
              <span>preds</span><b>{layer.preds.join(", ") || "—"}</b><span>succs</span><b>{layer.succs.join(", ") || "—"}</b></div>
            <table className="tbl">
              <thead><tr><th>param</th><th>shape / value</th></tr></thead>
              <tbody>
                {layer.params.map((p) => (
                  <tr key={p.name}><td>{p.name}</td><td className="mono">{p.shape ? `tensor[${p.shape.join("×")}]` : p.value}</td></tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </section>
    </div>
  );
}

function BoundsTable({ s }: { s: InputSpecOut }) {
  return (
    <>
      <table className="tbl">
        <thead><tr><th>x</th><th>lower</th><th>upper</th></tr></thead>
        <tbody>
          {s.lb.slice(0, 16).map((lb, i) => (
            <tr key={i}><td>x{i}</td><td>{fmt(num(lb))}</td><td>{fmt(num(s.ub[i]!))}</td></tr>
          ))}
        </tbody>
      </table>
      {s.lb.length > 16 && <div className="note">{s.lb.length - 16} more input variables not shown</div>}
    </>
  );
}

function Robustness({ o, dataset, classes }: { o: OutputSpecOut; dataset: string | null; classes: number }) {
  const t = o.true_class!;
  return (
    <div className="robust">
      <p>Every input in the box must still be classified as <b className="chip good">{classLabel(dataset, t)}</b></p>
      <div className="classrow" aria-label="output classes">
        {Array.from({ length: classes }, (_, k) => (
          <span key={k} className={k === t ? "chip good" : "chip"} title={k === t ? "must stay the top score" : `requires y${k} − y${t} ≤ 0`}>
            {classLabel(dataset, k)}
          </span>
        ))}
      </div>
      <p className="note">ACT checks y<sub>k</sub> − y<sub>{t}</sub> ≤ 0 for each of the other {classes - 1} classes.</p>
    </div>
  );
}
