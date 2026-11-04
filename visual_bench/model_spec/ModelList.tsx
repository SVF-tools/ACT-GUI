import { useLayoutEffect, useRef, type ReactNode } from "react";
import { fmt, indexRanges } from "../api";
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
          <ScrollList>
            {ms.map((m) => (
              <li key={m.model_id}>
                <button className={m.model_id === selected ? "item active" : "item"} onClick={() => onSelect(m.model_id)}>
                  <span className="title">{m.model_id}</span>
                  <span className="sub clamp" title={m.description}>{m.description}</span>
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
          </ScrollList>
        </div>
      ))}
    </section>
  );
}

// Shows the first VISIBLE items and scrolls the rest inside the group; items vary in height, so measure.
const VISIBLE = 3;
function ScrollList({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLUListElement>(null);
  useLayoutEffect(() => {
    const ul = ref.current;
    if (!ul) return;
    const fit = () => {
      const last = ul.children[VISIBLE - 1] as HTMLElement | undefined;
      ul.style.maxHeight = ul.children.length > VISIBLE && last ? `${last.offsetTop - ul.offsetTop + last.offsetHeight}px` : "";
    };
    fit();
    const ro = new ResizeObserver(fit);
    ro.observe(ul);
    return () => ro.disconnect();
  });
  return <ul ref={ref} className="list scrolllist">{children}</ul>;
}

function TorchChips({ p }: { p: Record<string, unknown> }) {
  const eps = typeof p.eps === "number" ? p.eps : null;
  const wrong = typeof p.label === "number" && typeof p.predicted === "number" && p.label !== p.predicted;
  const missed = typeof p.misclassified === "number" ? p.misclassified : 0;
  return (
    <>
      {typeof p.batch === "number"
        ? <span className="chip" title={`test images ${indexRanges(String(p.indices).split(",").map(Number))}`}>batch {p.batch}</span>
        : <span className="chip">#{String(p.index)}</span>}
      {missed > 0 && <span className="chip warn" title="clean images the model already misclassifies">{missed} misclassified</span>}
      {eps !== null && <span className="chip">ε {fmt(eps, 4)}</span>}
      {wrong && <span className="chip warn" title={`clean image predicted ${String(p.predicted)}, label ${String(p.label)}`}>misclassified</span>}
    </>
  );
}
