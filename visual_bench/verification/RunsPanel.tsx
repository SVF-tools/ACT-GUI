import { useEffect, useState } from "react";
import { api, followRun } from "../api";
import type { RunOut } from "../generated/wire";
import { useQuery } from "../workspace/useQuery";

export function RunsPanel({ modelId, selectedRun, version, onChanged, onSelect }: {
  modelId: string; selectedRun: string | null; version: number; onChanged: () => void; onSelect: (runId: string) => void;
}) {
  const models = useQuery("models", api.models);
  const runs = useQuery(`runs:${version}`, api.runs);
  const methods = models.status === "ok" ? models.data.find((m) => m.model_id === modelId)?.methods ?? [] : [];
  const [method, setMethod] = useState<"interval" | "bab">("bab");
  const [budget, setBudget] = useState(30);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const effective = methods.includes(method) ? method : methods[0] ?? "interval";
  const mine = runs.status === "ok" ? runs.data.runs.filter((r) => r.model_id === modelId) : [];

  // Follow active runs over SSE; refresh the list when a committed event arrives.
  const activeIds = mine.filter((r) => r.status === "queued" || r.status === "running").map((r) => r.run_id).join(",");
  useEffect(() => {
    if (!activeIds) return;
    const stops = activeIds.split(",").map((id) => followRun(id, (ev) => {
      if (ev.kind === "run.completed" || ev.kind === "run.failed") onChanged();
    }));
    return () => stops.forEach((s) => s());
  }, [activeIds, onChanged]);

  async function start() {
    setBusy(true);
    setErr(null);
    try {
      const run = await api.startRun({ model_id: modelId, method: effective, time_budget_s: budget, client_request_id: crypto.randomUUID() });
      onChanged();
      onSelect(run.run_id);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel">
      <h2>Verification runs</h2>
      <div className="form">
        <label>Method
          <select value={effective} onChange={(e) => setMethod(e.target.value as "interval" | "bab")}>
            {methods.map((m) => <option key={m} value={m}>{m === "bab" ? "BaB (verify_bab_batched)" : "interval (verify_once)"}</option>)}
          </select>
        </label>
        <label>Budget (s)
          <input type="number" min={1} max={600} value={budget} onChange={(e) => setBudget(Number(e.target.value))} />
        </label>
        <button className="primary" disabled={busy || methods.length === 0} onClick={start}>{busy ? "Starting…" : "Run ACT"}</button>
      </div>
      {err && <div className="error">{err}</div>}
      <ul className="list">
        {mine.length === 0 && <li className="note">No runs yet for this model.</li>}
        {mine.map((r) => <RunItem key={r.run_id} run={r} active={r.run_id === selectedRun} onSelect={onSelect} />)}
      </ul>
    </section>
  );
}

function RunItem({ run, active, onSelect }: { run: RunOut; active: boolean; onSelect: (id: string) => void }) {
  const verdict = run.result?.verdict;
  return (
    <li>
      <button className={active ? "item active" : "item"} onClick={() => onSelect(run.run_id)}>
        <span className="title">{run.run_id} <span className="muted">{run.method}</span></span>
        <span className="chips">
          <span className={`chip s-${run.status}`}>{run.status}</span>
          {verdict && <span className={`chip v-${verdict}`} title="ACT verdict">{verdict}</span>}
          {run.result && <span className="chip">{run.result.elapsed_s.toFixed(2)}s</span>}
          {run.result?.device && <span className="chip" title="torch device ACT computed on">{run.result.device}</span>}
          {run.matches_native === true && <span className="chip good" title="matches recorded native ACT result">= native</span>}
          {run.matches_native === false && <span className="chip warn" title={`native: ${run.native_reference?.status}`}>≠ native</span>}
        </span>
        {run.error && <span className="sub err">{run.error.code}: {run.error.message}</span>}
      </button>
    </li>
  );
}
