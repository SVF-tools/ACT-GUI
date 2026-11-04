import { exportUrl } from "./api";
import { Empty } from "../shared/ui/Empty";
import { useRecord } from "./hooks";

export function RecordsView({ runId }: { runId: string | null }) {
  const q = useRecord(runId);
  if (!runId) return <Empty title="No run selected" text="Every run is persisted with a manifest, ordered events, and hashed artifacts." />;
  if (q.status !== "success") return q.status === "error" ? <div className="error">{q.error.message}</div> : <Empty title="Loading…" text="" />;
  const r = q.data;
  return (
    <div>
      <h3>Run record {r.run_id}</h3>
      <div className="kv">
        <span>model</span><b>{r.model_id}</b>
        <span>model sha256</span><b className="mono">{r.model_sha256.slice(0, 20)}…</b>
        <span>ACT commit</span><b className="mono">{r.act_commit?.slice(0, 12)}</b>
        <span>method</span><b>{r.method} · budget {r.time_budget_s}s</b>
        <span>status</span><b>{r.status}</b>
        <span>created</span><b>{r.created_at}</b>
        <span>finished</span><b>{r.finished_at ?? "—"}</b>
        <span>events</span><b>{r.last_seq}</b>
        <span>native ACT</span><b>{r.native_reference ? `${r.native_reference.status} (recorded ${r.native_reference.elapsed_s}s)` : "not recorded"}</b>
      </div>
      {r.error && <div className="error">{r.error.code}: {r.error.message}</div>}
      {r.status === "completed" ? (
        <a className="button primary" href={exportUrl(r.run_id)} download>Export record bundle (.zip)</a>
      ) : <div className="note">Export is available once the run completes and the record is sealed.</div>}
    </div>
  );
}
