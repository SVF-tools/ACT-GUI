import type { RunOut, RunRequest } from "../generated/wire";
import { StopButton } from "../shared/ui/StopButton";
import { snapshotUrl } from "./api";
import { useRuns, useStopRun } from "./hooks";
import { METHOD_LABEL, runDomainLabel } from "./labels";
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
  const diag = run.diagnostics;
  // A reproduction snapshot is offered once a run has ended with an error or with ACT warnings.
  const snapshot = !live && (run.status === "failed" || (diag?.warnings ?? 0) > 0 || (diag?.errors ?? 0) > 0);
  return (
    <li className={live ? "runitem live" : snapshot ? "runitem tools" : "runitem"}>
      <button className={active ? "item active" : "item"} onClick={() => onSelect(run.run_id)}>
        <span className="title">{run.run_id} <span className="muted">{run.method}{runDomainLabel(run)}</span></span>
        <span className="chips">
          <span className={`chip s-${run.status}`}>{run.status}</span>
          {verdict && <span className={`chip v-${verdict}`} title="ACT verdict">{verdict}</span>}
          {run.result && <span className="chip">{run.result.elapsed_s.toFixed(2)}s</span>}
          {run.result?.device && <span className="chip" title="torch device ACT computed on">{run.result.device}</span>}
          {run.matches_native === true && <span className="chip good" title="matches recorded native ACT result">= native</span>}
          {run.matches_native === false && <span className="chip warn" title={`native: ${run.native_reference?.status}`}>≠ native</span>}
          {diag && diag.warnings > 0 && (
            <span className="chip warn" title={(diag.messages ?? []).join("\n")}>{diag.warnings} warning{diag.warnings > 1 ? "s" : ""}</span>
          )}
          {diag && diag.errors > 0 && <span className="chip bad" title="ERROR records in ACT's logs">{diag.errors} log error{diag.errors > 1 ? "s" : ""}</span>}
        </span>
        {run.error && <span className="sub err clamp">{run.error.code}: {run.error.message}</span>}
        {diag?.location && <span className="sub clamp" title={diag.exception ?? undefined}>at {diag.location}</span>}
      </button>
      {live && <StopButton method={run.method} onStop={() => stopRun.mutateAsync(run.run_id)} />}
      {snapshot && (
        <a className="button secondary small snapshot" href={snapshotUrl(run.run_id)} download
          title="Download the parameters, model and instance, engine info, logs and error location to reproduce this run">
          Snapshot
        </a>
      )}
    </li>
  );
}
