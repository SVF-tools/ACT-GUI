import { useEffect, useState } from "react";
import { api, followRun } from "../api";
import type { RunOut, RunRequest } from "../generated/wire";
import { useQuery } from "../workspace/useQuery";
import { FuzzSettings, type FuzzSettingsValue } from "./FuzzSettings";

type Method = RunRequest["method"];
type Domain = NonNullable<RunRequest["domain"]>;
const METHOD_LABEL: Record<Method, string> = {
  fuzz: "fuzz (ACTFuzzer)", interval: "verify (verify_once)", bab: "BaB (verify_bab_batched)",
};
// Abstract domains of verify_once; ACT selects them with its solver / transfer-function modes.
const DOMAIN_LABEL: Record<Domain, string> = {
  interval: "interval", dual: "dual", hybridz: "hybridz",
};

// The method is owned by the center mode tabs: switching the mode switches it, and choosing it here switches the mode.
export function RunsPanel({ modelId, method, onMethod, onChanged, onSelect }: {
  modelId: string; method: Method; onMethod: (m: Method) => void; onChanged: () => void; onSelect: (runId: string) => void;
}) {
  const models = useQuery("models", api.models);
  const methods = models.status === "ok" ? models.data.find((m) => m.model_id === modelId)?.methods ?? [] : [];
  const supported = methods.includes(method);
  const [budget, setBudget] = useState(30);
  const [domain, setDomain] = useState<Domain>("interval");
  const fuzzDefaults = useQuery("fuzz-defaults", api.fuzzDefaults);
  const defaults = fuzzDefaults.status === "ok" ? fuzzDefaults.data as FuzzSettingsValue : null;
  const [fuzzEdit, setFuzzEdit] = useState<FuzzSettingsValue | null>(null);
  const fuzzSettings = fuzzEdit ?? defaults;
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function start() {
    setBusy(true);
    setErr(null);
    try {
      const fuzz = method === "fuzz" ? fuzzSettings : null;
      const run = await api.startRun({
        model_id: modelId, method, time_budget_s: budget, client_request_id: crypto.randomUUID(), fuzz,
        domain: method === "interval" ? domain : null,
      });
      onChanged();
      onSelect(run.run_id);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel runs">
      <h2>Verification runs <small>{METHOD_LABEL[method]}{method === "interval" ? ` · ${domain}` : ""}</small></h2>
      <div className="form">
        <label>Method
          <select value={method} onChange={(e) => onMethod(e.target.value as Method)}>
            {(Object.keys(METHOD_LABEL) as Method[]).map((m) => (
              <option key={m} value={m} disabled={!methods.includes(m)}>{METHOD_LABEL[m]}</option>
            ))}
          </select>
        </label>
        {method === "interval" && (
          <label>Abstract domain
            <select value={domain} onChange={(e) => setDomain(e.target.value as Domain)}>
              {(Object.keys(DOMAIN_LABEL) as Domain[]).map((d) => <option key={d} value={d}>{DOMAIN_LABEL[d]}</option>)}
            </select>
          </label>
        )}
        <label>Budget (s)
          <input type="number" min={1} max={600} value={budget} onChange={(e) => setBudget(Number(e.target.value))} />
        </label>
        {method === "fuzz" && (
          <>
            {fuzzDefaults.status === "error" && <div className="error">Fuzz defaults unavailable: {fuzzDefaults.message}</div>}
            {fuzzSettings && defaults && <FuzzSettings value={fuzzSettings} defaults={defaults} onChange={setFuzzEdit} />}
          </>
        )}
        <button className="primary" disabled={busy || !supported || (method === "fuzz" && !fuzzSettings)} onClick={start}>{busy ? "Starting…" : "Run ACT"}</button>
      </div>
      {!supported && models.status === "ok" && <div className="note">This model does not support {METHOD_LABEL[method]}.</div>}
      {err && <div className="error">{err}</div>}
    </section>
  );
}

// Past runs of the selected model for the current method; it also follows active runs so the list refreshes on commit.
export function RunHistory({ modelId, method, selectedRun, version, onChanged, onSelect }: {
  modelId: string; method: Method; selectedRun: string | null; version: number; onChanged: () => void;
  onSelect: (runId: string) => void;
}) {
  const runs = useQuery(`runs:${version}`, api.runs);
  const all = runs.status === "ok" ? runs.data.runs.filter((r) => r.model_id === modelId) : [];
  const mine = all.filter((r) => r.method === method);

  // Every method, so a run started in another mode still lands.
  const activeIds = all.filter((r) => r.status === "queued" || r.status === "running").map((r) => r.run_id).join(",");
  useEffect(() => {
    if (!activeIds) return;
    const stops = activeIds.split(",").map((id) => followRun(id, (ev) => {
      if (ev.kind === "run.completed" || ev.kind === "run.failed") onChanged();
    }));
    return () => stops.forEach((s) => s());
  }, [activeIds, onChanged]);

  return (
    <>
      <h2>Run history <small>{modelId} · {METHOD_LABEL[method]} · {mine.length}</small></h2>
      <ul className="list">
        {mine.length === 0 && <li className="note">No {method} runs yet for this model{all.length ? ` (${all.length} with other methods)` : ""}.</li>}
        {mine.map((r) => <RunItem key={r.run_id} run={r} active={r.run_id === selectedRun} onSelect={onSelect} onChanged={onChanged} />)}
      </ul>
    </>
  );
}

function RunItem({ run, active, onSelect, onChanged }: {
  run: RunOut; active: boolean; onSelect: (id: string) => void; onChanged: () => void;
}) {
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
      {live && <StopButton runId={run.run_id} method={run.method} onStopped={onChanged} />}
    </li>
  );
}

/** Stop a queued or running run: fuzzing ends after its current iteration and keeps what ACT found; verify/BaB are ended. */
export function StopButton({ runId, method, onStopped }: { runId: string; method: Method; onStopped: () => void }) {
  const [state, setState] = useState<"idle" | "stopping" | "error">("idle");
  const [err, setErr] = useState("");
  async function stop() {
    setState("stopping");
    try {
      await api.stopRun(runId);
      onStopped();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }
  return (
    <button className="danger" disabled={state === "stopping"} onClick={stop}
      title={err || (method === "fuzz" ? "ACTFuzzer stops after the current iteration; counterexamples found so far are kept"
        : "Ends the worker; ACT returns no result for this run")}>
      {state === "stopping" ? "Stopping…" : state === "error" ? "Stop failed, retry" : "Stop"}
    </button>
  );
}
