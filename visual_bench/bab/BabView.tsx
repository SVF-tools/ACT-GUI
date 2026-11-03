import { api } from "../api";
import { Empty } from "../workspace/Empty";
import { useQuery } from "../workspace/useQuery";

export function BabView({ runId, version }: { runId: string | null; version: number }) {
  const q = useQuery(runId ? `${runId}:${version}` : null, () => api.coverage(runId!));
  if (!runId) return <Empty title="No run selected" text="BaB observation needs a run." />;
  if (q.status !== "ok") return q.status === "error" ? <div className="error">{q.message}</div> : <Empty title="Loading…" text="" />;
  const c = q.data;
  return (
    <div>
      <h3>Observation coverage</h3>
      <div className="kv">
        <span>node events</span><b className={`av-${c.node_events}`}>{c.node_events}</b>
        <span>wave events</span><b className={`av-${c.wave_events}`}>{c.wave_events}</b>
        <span>final summary</span><b className={`av-${c.final_summary}`}>{c.final_summary}</b>
      </div>
      <p className="note">{c.reason}</p>
      {c.summary ? (
        <>
          <h3>ACT BaB summary <small>summary-only; not expanded into a tree</small></h3>
          <table className="tbl">
            <tbody>{Object.entries(c.summary).map(([k, v]) => <tr key={k}><td>{k}</td><td className="mono">{String(v)}</td></tr>)}</tbody>
          </table>
        </>
      ) : <div className="note">No BaB summary for this run (interval runs have none).</div>}
      <div className="placeholder">Search-tree view and node actions are disabled: they require committed node events (plan ACT-03) and safe controls (ACT-05).</div>
    </div>
  );
}
