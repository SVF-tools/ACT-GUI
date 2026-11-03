import { fmt } from "../api";
import type { ModelSummary } from "../generated/wire";
import type { QueryState } from "../workspace/useQuery";

export function ModelList({ models, selected, onSelect }: {
  models: QueryState<ModelSummary[]>; selected: string | null; onSelect: (id: string) => void;
}) {
  const groups: [string, ModelSummary[]][] = models.status === "ok"
    ? [["Catalog", models.data.filter((m) => (m.source ?? "catalog") === "catalog")],
       ["Loaded", models.data.filter((m) => (m.source ?? "catalog") !== "catalog")]]
    : [];
  return (
    <section className="panel">
      <h2>Models</h2>
      {models.status === "error" && <div className="error">{models.message}</div>}
      {groups.filter(([, ms]) => ms.length > 0).map(([title, ms]) => (
        <div key={title} className="modelgroup">
          {groups.length > 1 && <h3 className="grouptitle">{title} <small>{ms.length}</small></h3>}
          <ul className="list">
            {ms.map((m) => (
              <li key={m.model_id}>
                <button className={m.model_id === selected ? "item active" : "item"} onClick={() => onSelect(m.model_id)}>
                  <span className="title">{m.model_id}</span>
                  <span className="sub">{m.description}</span>
                  <span className="chips">
                    {m.source && m.source !== "catalog" && <span className="chip">{m.source === "torch" ? "torch" : "vnn-lib"}</span>}
                    {m.source === "torch" && <TorchChips p={m.params ?? {}} />}
                    {Object.entries(m.native).map(([method, r]) => (
                      <span key={method} className={`chip v-${r.status.toLowerCase()}`} title="recorded native ACT result (fixtures/catalog.json)">
                        {method}: {r.status.toLowerCase()}
                      </span>
                    ))}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}

function TorchChips({ p }: { p: Record<string, unknown> }) {
  const eps = typeof p.eps === "number" ? p.eps : null;
  const wrong = typeof p.label === "number" && typeof p.predicted === "number" && p.label !== p.predicted;
  return (
    <>
      <span className="chip">#{String(p.index)}</span>
      {eps !== null && <span className="chip">ε {fmt(eps, 4)}</span>}
      {wrong && <span className="chip warn" title={`clean image predicted ${String(p.predicted)}, label ${String(p.label)}`}>misclassified</span>}
    </>
  );
}
