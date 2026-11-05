import type { RunOut, RunRequest } from "../generated/wire";
import { StopButton } from "../shared/ui/StopButton";
import { useRuns, useStopRun } from "./hooks";
import { METHOD_LABEL } from "./labels";
type Method = RunRequest["method"];

// Past runs of the selected model for the current method; live updates share the query cache.
export function RunHistory({ modelId, method, selectedRun, onSelect }: {
  modelId: string; method: Method; selectedRun: string | null;
  onSelect: (runId: string) => void;
}) {
  const runs = useRuns();
  const all = runs.status === "success" ? runs.data.runs.filter((r) => r.model_id === modelId) : [];
  const mine = all.filter((r) => r.method === method);

  return (
    <>
      <h2>Run history <small>{modelId} · {METHOD_LABEL[method]} · {mine.length}</small></h2>
      <ul className="list">
        {mine.length === 0 && <li className="note">No {method} runs yet for this model{all.length ? ` (${all.length} with other methods)` : ""}.</li>}
        {mine.map((r) => <RunItem key={r.run_id} run={r} active={r.run_id === selectedRun} onSelect={onSelect} />)}
      </ul>
    </>
  );
}

function RunItem({ run, active, onSelect }: {
  run: RunOut; active: boolean; onSelect: (id: string) => void;
}) {
  const stopRun = useStopRun();
  const verdict = run.result?.verdict;
  const live = run.status === "queued" || run.status === "running";
  return (
    <li className={live ? "runitem live" : "runitem"}>
      <button className={active ? "item active" : "item"} onClick={() => onSelect(run.run_id)}>
        <span className="title">{run.run_id} <span className="muted">{run.method}{run.domain ? ` · ${run.domain}` : ""}</span></span>
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
      {live && <StopButton method={run.method} onStop={() => stopRun.mutateAsync(run.run_id)} />}
    </li>
  );
}
