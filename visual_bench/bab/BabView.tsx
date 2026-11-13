// BaB tab: the search tree ACT builds wave by wave, its replay, progress and node detail. ACT owns every result.
import { useEffect, useState } from "react";
import type { BabTreeOut, ModelDescriptionOut } from "../generated/wire";
import { Empty } from "../shared/ui/Empty";
import { useRun } from "../verification/hooks";
import { BabNodeDetail } from "./BabNodeDetail";
import { BabTimeline } from "./BabTimeline";
import { BabTree } from "./BabTree";
import { useBabTree, useCoverage } from "./hooks";
import { countsAt, lastWave, type LeafState, sharesAt, STATE_LABEL, STATES, waveSeries } from "./tree";
import "./bab.css";

const REPLAY_MS = 700;
const SHARE_ORDER: LeafState[] = ["proved", "falsified", "retired", "evicted", "unresolved", "pending"];
const pct = (v: number) => `${(100 * v).toFixed(v > 0 && v < 0.01 ? 1 : 0)}%`;
const words = (reason: string) => reason.replaceAll("_", " ");

export function BabView({ runId, model }: { runId: string | null; model: ModelDescriptionOut }) {
  if (!runId) return <Empty title="No run selected" text="Start a BaB run, or pick one in Run history." />;
  return <BabRun key={runId} runId={runId} model={model} />;
}

function BabRun({ runId, model }: { runId: string; model: ModelDescriptionOut }) {
  const [root, setRoot] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [cursor, setCursor] = useState<number | null>(null); // null follows the newest committed wave
  const [playing, setPlaying] = useState(false);
  const run = useRun(runId);
  const q = useBabTree(runId, root);
  const tree = q.data;
  const last = tree ? lastWave(tree) : 0;
  const wave = Math.min(cursor ?? last, last);
  useEffect(() => {
    if (!playing) return;
    if (wave >= last) {
      setPlaying(false);
      return;
    }
    const timer = setTimeout(() => setCursor(wave + 1), REPLAY_MS);
    return () => clearTimeout(timer);
  }, [playing, wave, last]);

  if (q.status === "error") return <div className="error">{q.error.message}</div>;
  if (!tree) return <Empty title="Loading the search tree…" text="" />;
  if (tree.availability !== "available") return <Unavailable tree={tree} runId={runId} />;

  const running = run.data?.status === "queued" || run.data?.status === "running";
  const counts = countsAt(tree.nodes, wave, tree.terminal);
  const shown = STATES.reduce((sum, s) => sum + counts[s], 0);
  const solved = tree.waves.filter((w) => w.wave <= wave).reduce((sum, w) => sum + w.solved, 0);
  const shares = tree.truncated ? (wave === last ? tree.shares : null) : sharesAt(tree.nodes, root, wave, tree.terminal);
  const focus = selected ?? root;
  const replay = (w: number | null) => { setPlaying(false); setCursor(w); };
  return (
    <div className="bab">
      <div className="babhead">
        <div className="babstatus" aria-live="polite">
          {running && cursor === null && <span className="chip s-running">live</span>}
          <b>Wave {wave}</b><span className="muted">of {last}</span>
          <span>{shown} node{shown === 1 ? "" : "s"}</span>
          <span className="muted">{solved} solved</span>
        </div>
        <div className="babreplay">
          <button type="button" className="secondary small" disabled={last === 0}
            onClick={() => { if (playing) { setPlaying(false); return; } if (wave >= last) setCursor(0); setPlaying(true); }}>
            {playing ? "Pause" : "Replay"}</button>
          <input type="range" min={0} max={last} value={wave} disabled={last === 0} aria-label="shown wave"
            onChange={(e) => replay(Number(e.target.value))} />
          <button type="button" className="secondary small" disabled={cursor === null}
            onClick={() => replay(null)}>{running ? "Follow live" : "Latest"}</button>
        </div>
      </div>
      {shares && <ShareBar shares={shares} />}
      {root !== 0 && (
        <nav className="babcrumbs" aria-label="focused subtree">
          <button type="button" className="chip link" onClick={() => { setRoot(0); setSelected(null); }}>whole tree</button>
          {tree.path.filter((n) => n.node_id !== 0).map((n) => (
            <button key={n.node_id} type="button" className="chip link" onClick={() => { setRoot(n.node_id); setSelected(n.node_id); }}>
              #{n.node_id}</button>
          ))}
          <span className="chip">#{root} (focus)</span>
        </nav>
      )}
      <BabTree nodes={tree.nodes} root={root} wave={wave} terminal={tree.terminal} selected={focus} onSelect={setSelected}
        specRows={model.output_spec?.rows} />
      <div className="legend babkeys">
        {STATES.filter((s) => counts[s] > 0).map((s) => (
          <span key={s}><i className={`babdotkey s-${s}`} />{STATE_LABEL[s]} {counts[s]}</span>
        ))}
        {tree.truncated && <span className="muted">first {tree.nodes.length} nodes breadth-first; focus a subtree for the rest</span>}
      </div>
      <div className="bablower">
        <section>
          <BabNodeDetail runId={runId} nodeId={focus} model={model} focusRoot={root} onSelect={setSelected}
            onFocus={(id) => { setRoot(id); setSelected(id); }} />
        </section>
        <section>
          <h4>Progress per wave</h4>
          <BabTimeline points={waveSeries(tree.waves)} marker={wave} onWave={replay} />
        </section>
      </div>
      {tree.terminal && (
        <p className="note">ACT ended the search {tree.terminal.wave === 0 ? "before the first wave" : `in wave ${tree.terminal.wave}`}
          : {tree.terminal.status}, {words(tree.terminal.reason)}{tree.terminal.frontier_size > 0 ? `, ${tree.terminal.frontier_size} subproblems left open` : ""}.</p>
      )}
      {tree.recording_error && <p className="note">Recording stopped early ({tree.recording_error}); ACT's result is unaffected.</p>}
      {(tree.ignored_records ?? 0) > 0 && <p className="note">{tree.ignored_records} ACT record(s) could not be read.</p>}
      <Summary runId={runId} />
    </div>
  );
}

function ShareBar({ shares }: { shares: Record<LeafState, number> }) {
  const parts = SHARE_ORDER.filter((s) => shares[s] > 0);
  return (
    <div className="babshare">
      <div className="babsharebar" role="img" aria-label={parts.map((s) => `${STATE_LABEL[s]} ${pct(shares[s])}`).join(", ")}>
        {parts.map((s) => <span key={s} className={`s-${s}`} style={{ flexGrow: shares[s] }} title={`${STATE_LABEL[s]} ${pct(shares[s])}`} />)}
      </div>
      <span className="note">Split tree: {parts.map((s) => `${STATE_LABEL[s]} ${pct(shares[s])}`).join(" · ")}
        <span className="muted"> (each split shares its parent equally; not a verdict)</span></span>
    </div>
  );
}

function Unavailable({ tree, runId }: { tree: BabTreeOut; runId: string }) {
  return (
    <div className="bab">
      {tree.availability === "pending"
        ? <Empty title="Waiting for ACT's first wave" text={tree.reason} />
        : <p className="note">{tree.reason}</p>}
      <Summary runId={runId} open />
    </div>
  );
}

function Summary({ runId, open = false }: { runId: string; open?: boolean }) {
  const q = useCoverage(runId);
  const summary = q.data?.summary;
  if (!summary) return null;
  return (
    <details className="babsummary" open={open}>
      <summary>ACT BaB summary</summary>
      <table className="tbl">
        <tbody>{Object.entries(summary).map(([k, v]) => <tr key={k}><td>{k}</td><td className="mono">{String(v)}</td></tr>)}</tbody>
      </table>
    </details>
  );
}
