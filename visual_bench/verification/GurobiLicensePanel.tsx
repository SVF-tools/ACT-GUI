import { useState } from "react";
import { api } from "../api";
import type { SolverStatusOut } from "../generated/wire";
import { Empty } from "../workspace/Empty";
import { useQuery } from "../workspace/useQuery";

type Mode = "wls" | "paste" | "file";
const MODES: { id: Mode; label: string }[] = [
  { id: "wls", label: "WLS credentials" }, { id: "paste", label: "Paste gurobi.lic" }, { id: "file", label: "Upload file" },
];

export const LICENSE_STATE_CLASS: Record<SolverStatusOut["license_state"], string> = {
  licensed: "good", restricted: "warn", invalid: "bad", not_installed: "bad",
};

const VERDICT: Record<SolverStatusOut["license_state"], string> = {
  licensed: "Gurobi accepted this license.",
  restricted: "Gurobi started with its size-limited restricted license only.",
  invalid: "Gurobi rejected this license.",
  not_installed: "gurobipy is not installed in this workbench.",
};

function wlsLicenseFile(accessId: string, secret: string, licenseId: string): string {
  return `WLSACCESSID=${accessId.trim()}\nWLSSECRET=${secret.trim()}\nLICENSEID=${licenseId.trim()}\n`;
}

export function GurobiLicensePanel({ version, onChanged }: { version: number; onChanged: () => void }) {
  const status = useQuery("gurobi", api.gurobi, version);
  const [mode, setMode] = useState<Mode>("wls");
  const [wls, setWls] = useState({ accessId: "", secret: "", licenseId: "" });
  const [pasted, setPasted] = useState("");
  const [file, setFile] = useState<{ name: string; text: string } | null>(null);
  const [busy, setBusy] = useState<"apply" | "remove" | null>(null);
  const [result, setResult] = useState<SolverStatusOut | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const content = mode === "wls"
    ? (wls.accessId.trim() && wls.secret.trim() && /^\d+$/.test(wls.licenseId.trim()) ? wlsLicenseFile(wls.accessId, wls.secret, wls.licenseId) : null)
    : mode === "paste" ? (pasted.trim() || null) : (file?.text ?? null);

  async function run(kind: "apply" | "remove") {
    setBusy(kind);
    setErr(null);
    setResult(null);
    try {
      const out = kind === "apply" ? await api.uploadGurobiLicense({ content: content! }) : await api.removeGurobiLicense();
      if (kind === "apply") {
        setResult(out);
        setWls({ accessId: "", secret: "", licenseId: "" });
        setPasted("");
        setFile(null);
      }
      onChanged();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  if (status.status === "error") return <div className="error">{status.message}</div>;
  if (status.status !== "ok") return <Empty title="Checking Gurobi license…" text="" />;
  const s = status.data;
  const unavailable = s.license_state === "not_installed";

  return (
    <div className="license">
      <div className="kv">
        <span>state</span><b className={`state ${LICENSE_STATE_CLASS[s.license_state]}`}>{s.license_state}</b>
        <span>source</span><b>{s.license_source}{s.license_fingerprint && <span className="mono muted"> · {s.license_fingerprint}</span>}</b>
        <span>gurobipy</span><b>{s.version ?? "not installed"}</b>
        <span>Gurobi says</span><b>{s.message}</b>
      </div>

      <h4>Apply a license</h4>
      <div className="seg" role="tablist" aria-label="license input">
        {MODES.map((m) => (
          <button key={m.id} role="tab" aria-selected={mode === m.id} className={mode === m.id ? "on" : ""}
            onClick={() => { setMode(m.id); setResult(null); setErr(null); }}>{m.label}</button>
        ))}
      </div>

      <form className="licform" onSubmit={(e) => { e.preventDefault(); if (content) void run("apply"); }}>
        {mode === "wls" && (
          <>
            <p className="note">From the Gurobi Web License Manager (license.gurobi.com): API keys → download → copy the three values.</p>
            <label>WLS access ID
              <input autoComplete="off" spellCheck={false} placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                value={wls.accessId} onChange={(e) => setWls({ ...wls, accessId: e.target.value })} />
            </label>
            <label>WLS secret
              <input type="password" autoComplete="off" value={wls.secret} onChange={(e) => setWls({ ...wls, secret: e.target.value })} />
            </label>
            <label>License ID
              <input inputMode="numeric" autoComplete="off" placeholder="123456"
                value={wls.licenseId} onChange={(e) => setWls({ ...wls, licenseId: e.target.value })} />
            </label>
          </>
        )}
        {mode === "paste" && (
          <label>Contents of gurobi.lic
            <textarea rows={6} spellCheck={false} className="mono" placeholder={"# Gurobi license file\nLICENSEID=…"}
              value={pasted} onChange={(e) => setPasted(e.target.value)} />
          </label>
        )}
        {mode === "file" && (
          <label>gurobi.lic file
            <input type="file" accept=".lic,text/plain"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) void f.text().then((text) => setFile({ name: f.name, text })); }} />
            {file && <span className="note">Selected {file.name} ({file.text.length} bytes); its content is not displayed.</span>}
          </label>
        )}
        <div className="actions">
          <button type="submit" className="primary" disabled={!content || busy !== null || unavailable}>
            {busy === "apply" ? "Checking with Gurobi…" : "Apply license"}
          </button>
          <button type="button" className="secondary" disabled={busy !== null || s.license_source !== "uploaded"}
            onClick={() => void run("remove")}>{busy === "remove" ? "Removing…" : "Remove applied license"}</button>
        </div>
      </form>

      {result && (
        <div className={`banner ${LICENSE_STATE_CLASS[result.license_state]}`} role="status">
          <b>{VERDICT[result.license_state]}</b> {result.message}
        </div>
      )}
      {err && <div className="error">{err}</div>}

      <p className="note">
        {s.used_by_methods.length === 0
          ? "The current interval and BaB methods use ACT's TorchLPSolver; a Gurobi license does not change their results."
          : `Used by: ${s.used_by_methods.join(", ")}.`}
        {" "}The license is stored on the workbench server (owner-only file) and passed to each run; it is never sent back
        to the browser. An applied license overrides one mounted by the operator. Host-bound licenses usually fail inside
        containers; WLS and token-server licenses work.
      </p>
    </div>
  );
}
