import { fmt, num } from "../api";
import type { ModelDescriptionOut } from "../generated/wire";

export function SpecPanel({ model, selectedLayer }: { model: ModelDescriptionOut; selectedLayer: number | null }) {
  const layer = model.layers.find((l) => l.layer_id === selectedLayer) ?? null;
  return (
    <div className="split">
      <section className="panel">
        <h2>Specification</h2>
        {model.input_specs.map((s) => (
          <div key={s.layer_id} className="spec">
            <div className="label">Input domain · {s.kind} (layer {s.layer_id})</div>
            <table className="tbl">
              <thead><tr><th>x</th><th>lower</th><th>upper</th></tr></thead>
              <tbody>
                {s.lb.slice(0, 16).map((lb, i) => (
                  <tr key={i}><td>x{i}</td><td>{fmt(num(lb))}</td><td>{fmt(num(s.ub[i]!))}</td></tr>
                ))}
              </tbody>
            </table>
            {s.lb.length > 16 && <div className="note">{s.lb.length - 16} more input variables not shown</div>}
          </div>
        ))}
        {model.output_spec ? (
          <div className="spec">
            <div className="label">Output property · {model.output_spec.kind} (layer {model.output_spec.layer_id})</div>
            <p className="mono">{model.output_spec.text}</p>
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
