import { api } from "../api";
import { useQuery } from "../workspace/useQuery";

export function EngineBadge() {
  const q = useQuery("engine", api.engine);
  if (q.status !== "ok") return <span className="badge muted">{q.status === "error" ? "engine unreachable" : "probing ACT…"}</span>;
  const e = q.data;
  const warn = e.diagnostics.length > 0;
  return (
    <span className={!e.usable ? "badge bad" : warn ? "badge warn" : "badge good"}
      title={[...e.diagnostics.map((d) => `${d.severity}: ${d.message}`), `torch ${e.torch}, CUDA ${e.cuda_available}`].join("\n")}>
      ACT {e.commit?.slice(0, 8) ?? "?"} · {!e.usable ? "unavailable" : warn ? "check diagnostics" : "pinned baseline"}
    </span>
  );
}
