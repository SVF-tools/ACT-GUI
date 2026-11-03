import { api } from "../api";
import { useQuery } from "../workspace/useQuery";

export function ModelList({ selected, onSelect }: { selected: string | null; onSelect: (id: string) => void }) {
  const q = useQuery("models", api.models);
  return (
    <section className="panel">
      <h2>Models</h2>
      {q.status === "error" && <div className="error">{q.message}</div>}
      {q.status === "ok" && (
        <ul className="list">
          {q.data.map((m) => (
            <li key={m.model_id}>
              <button className={m.model_id === selected ? "item active" : "item"} onClick={() => onSelect(m.model_id)}>
                <span className="title">{m.model_id}</span>
                <span className="sub">{m.description}</span>
                <span className="chips">
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
      )}
    </section>
  );
}
