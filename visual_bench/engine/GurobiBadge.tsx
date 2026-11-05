import { useGurobi } from "./hooks";
import { LICENSE_STATE_CLASS } from "./GurobiLicensePanel";

export function GurobiBadge({ onOpen }: { onOpen: () => void }) {
  const q = useGurobi();
  const label = q.status === "success" ? q.data.license_state : q.status === "error" ? "unreachable" : "checking…";
  const tone = q.status === "success" ? LICENSE_STATE_CLASS[q.data.license_state] : "muted";
  return (
    <button className={`badge ${tone}`} onClick={onOpen}
      title={q.status === "success" ? `${q.data.message}\nClick to apply or change the Gurobi license.` : "Gurobi license"}>
      Gurobi · {label}
    </button>
  );
}
