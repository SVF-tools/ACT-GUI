import { api } from "../api";
import { useQuery } from "../workspace/useQuery";
import { LICENSE_STATE_CLASS } from "./GurobiLicensePanel";

export function GurobiBadge({ version, onOpen }: { version: number; onOpen: () => void }) {
  const q = useQuery("gurobi", api.gurobi, version);
  const label = q.status === "ok" ? q.data.license_state : q.status === "error" ? "unreachable" : "checking…";
  const tone = q.status === "ok" ? LICENSE_STATE_CLASS[q.data.license_state] : "muted";
  return (
    <button className={`badge ${tone}`} onClick={onOpen}
      title={q.status === "ok" ? `${q.data.message}\nClick to apply or change the Gurobi license.` : "Gurobi license"}>
      Gurobi · {label}
    </button>
  );
}
