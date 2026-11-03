import { api } from "../api";
import { Empty } from "../workspace/Empty";
import { useQuery } from "../workspace/useQuery";
import { GurobiLicensePanel } from "./GurobiLicensePanel";

export function EngineView({ licenseVersion, onLicenseChanged }: { licenseVersion: number; onLicenseChanged: () => void }) {
  const engine = useQuery("engine", api.engine);
  return (
    <div>
      <h3>ACT engine</h3>
      {engine.status === "ok" ? (
        <div className="kv">
          <span>ACT commit</span><b className="mono">{engine.data.commit?.slice(0, 12) ?? "unknown"}</b>
          <span>Python / torch</span><b>{engine.data.python} / {engine.data.torch ?? "—"}</b>
          <span>CUDA visible</span><b>{engine.data.cuda_available ? "yes" : "no"}</b>
        </div>
      ) : <Empty title={engine.status === "error" ? engine.message : "Probing ACT…"} text="" />}
      <p className="note">Each run records the torch device ACT actually computed on (see the run list).</p>

      <h3>Gurobi license</h3>
      <GurobiLicensePanel version={licenseVersion} onChanged={onLicenseChanged} />
    </div>
  );
}
