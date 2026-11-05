import { useEngine } from "./hooks";
import { Empty } from "../shared/ui/Empty";
import { GurobiLicensePanel } from "./GurobiLicensePanel";

export function EngineView() {
  const engine = useEngine();
  return (
    <div>
      <h3>ACT engine</h3>
      {engine.status === "success" ? (
        <div className="kv">
          <span>ACT commit</span><b className="mono">{engine.data.commit?.slice(0, 12) ?? "unknown"}</b>
          <span>Python / torch</span><b>{engine.data.python} / {engine.data.torch ?? "—"}</b>
          <span>CUDA visible</span><b>{engine.data.cuda_available ? "yes" : "no"}</b>
        </div>
      ) : <Empty title={engine.status === "error" ? engine.error.message : "Probing ACT…"} text="" />}
      <p className="note">Each run records the torch device ACT actually computed on (see the run list).</p>

      <h3>Gurobi license</h3>
      <GurobiLicensePanel />
    </div>
  );
}
