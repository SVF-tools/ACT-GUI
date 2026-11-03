import { useState } from "react";
import { api } from "../api";
import type { SolverStatusOut } from "../generated/wire";
import { Empty } from "../workspace/Empty";
import { useQuery } from "../workspace/useQuery";

const STATE_CLASS: Record<SolverStatusOut["license_state"], string> = {
  licensed: "av-available", restricted: "av-pending", invalid: "av-unsupported", not_installed: "av-unsupported",
};

export function EngineView() {
  const [refresh, setRefresh] = useState(0);
  const engine = useQuery("engine", api.engine);
  const gurobi = useQuery("gurobi", api.gurobi, refresh);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function act(op: () => Promise<SolverStatusOut>) {
    setBusy(true);
    setErr(null);
    try {
      await op();
      setRefresh((n) => n + 1);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function upload(file: File) {
    await act(async () => api.uploadGurobiLicense({ content: await file.text() }));
  }

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
      {gurobi.status === "error" && <div className="error">{gurobi.message}</div>}
      {gurobi.status !== "ok" && gurobi.status !== "error" && <Empty title="Checking Gurobi license…" text="" />}
      {gurobi.status === "ok" && (
        <>
          <div className="kv">
            <span>gurobipy</span><b>{gurobi.data.version ?? "not installed"}</b>
            <span>license source</span><b>{gurobi.data.license_source}</b>
            <span>state</span><b className={STATE_CLASS[gurobi.data.license_state]}>{gurobi.data.license_state}</b>
            <span>fingerprint</span><b className="mono">{gurobi.data.license_fingerprint ?? "—"}</b>
            <span>updated</span><b>{gurobi.data.license_updated_at ?? "—"}</b>
            <span>Gurobi says</span><b>{gurobi.data.message}</b>
          </div>
          <p className="note">
            {gurobi.data.used_by_methods.length === 0
              ? "The current interval and BaB methods use ACT's TorchLPSolver; a Gurobi license does not change their results."
              : `Used by: ${gurobi.data.used_by_methods.join(", ")}.`}
            {" "}The file stays on the workbench server and is never sent back to the browser. Host-bound licenses usually
            fail inside containers; WLS and token-server licenses work.
          </p>
          <div className="form">
            <label>Upload gurobi.lic
              <input type="file" accept=".lic,text/plain" disabled={busy || gurobi.data.license_state === "not_installed"}
                onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ""; if (f) void upload(f); }} />
            </label>
            <button disabled={busy || gurobi.data.license_source !== "uploaded"}
              onClick={() => void act(api.removeGurobiLicense)}>Remove</button>
          </div>
        </>
      )}
      {err && <div className="error">{err}</div>}
    </div>
  );
}
