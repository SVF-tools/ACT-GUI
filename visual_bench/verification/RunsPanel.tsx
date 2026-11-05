import { useState, type ReactNode } from "react";
import type { FuzzOptions, RunRequest } from "../generated/wire";
import { useModels } from "../model_spec/hooks";
import { useStartRun, type useVerifyConfiguration } from "./hooks";
import { VerifySettings } from "./VerifySettings";
import { useCapabilities } from "../engine/hooks";
import { modeForMethod } from "../workspace/modes";
import { METHOD_LABEL } from "./labels";

type Method = RunRequest["method"];
export type Domain = NonNullable<RunRequest["domain"]>;
// Abstract domains of verify_once; ACT selects them with its solver / transfer-function modes.
const DOMAIN_LABEL: Record<Domain, string> = {
  interval: "interval", dual: "dual", hybridz: "hybridz",
};

// The method is owned by the center mode tabs: switching the mode switches it, and choosing it here switches the mode.
// Domain and verify settings are owned by the caller, so they survive the remount that follows a run selection.
export function RunsPanel({ modelId, method, onMethod, onSelect, fuzzOptions, fuzzSettings, domain, onDomain, verify }: {
  modelId: string; method: Method; onMethod: (m: Method) => void; onSelect: (runId: string) => void;
  fuzzOptions: FuzzOptions | null; fuzzSettings: ReactNode;
  domain: Domain; onDomain: (d: Domain) => void; verify: ReturnType<typeof useVerifyConfiguration>;
}) {
  const models = useModels();
  const startRun = useStartRun();
  const lacks = useCapabilities();
  const domainOk = (d: Domain) => lacks(`verify.${d}`) === null;
  const methods = models.status === "success" ? models.data.find((m) => m.model_id === modelId)?.methods ?? [] : [];
  const supported = methods.includes(method);
  const [budget, setBudget] = useState(30);
  const settingsDomain = method === "interval" && domain !== "interval" ? domain : null;
  const dualOptionsMissing = lacks("verify.dual.options");
  const missing = method === "interval" ? lacks(`verify.${domain}`) : lacks(modeForMethod(method).capability);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function start() {
    setBusy(true);
    setErr(null);
    try {
      const fuzz = method === "fuzz" ? fuzzOptions : null;
      const run = await startRun.mutateAsync({
        model_id: modelId, method, time_budget_s: budget, client_request_id: crypto.randomUUID(), fuzz,
        domain: method === "interval" ? domain : null,
        dual: settingsDomain === "dual" && !dualOptionsMissing ? verify.value?.dual ?? null : null,
        hybridz: settingsDomain === "hybridz" ? verify.value?.hybridz ?? null : null,
      });
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
            <select value={domain} onChange={(e) => onDomain(e.target.value as Domain)}>
              {(Object.keys(DOMAIN_LABEL) as Domain[]).map((d) => <option key={d} value={d} disabled={!domainOk(d)}>{DOMAIN_LABEL[d]}</option>)}
            </select>
          </label>
        )}
        {settingsDomain && verify.query.isError && <div className="error">Verification defaults unavailable: {verify.query.error.message}</div>}
        {settingsDomain && verify.value && verify.defaults && (
          <VerifySettings domain={settingsDomain} value={verify.value} defaults={verify.defaults}
            onChange={verify.setValue} optionsMissing={dualOptionsMissing} />
        )}
        <label>Budget (s)
          <input type="number" min={1} max={600} value={budget} onChange={(e) => setBudget(Number(e.target.value))} />
        </label>
        {method === "fuzz" && fuzzSettings}
        <button className="primary" disabled={busy || !supported || missing !== null || (method === "fuzz" && !fuzzOptions)} onClick={start}>{busy ? "Starting…" : "Run ACT"}</button>
      </div>
      {missing ? <div className="note">Disabled on this ACT checkout. {missing}</div>
        : !supported && models.status === "success" && <div className="note">This model does not support {METHOD_LABEL[method]}.</div>}
      {err && <div className="error">{err}</div>}
    </section>
  );
}
