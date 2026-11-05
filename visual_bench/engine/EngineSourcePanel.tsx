import { useState } from "react";
import { useCheckEngine, useEngineBranches, useEngineSources, useSwitchEngine } from "./hooks";
import type { EngineInfoOut, EngineSourceOut, EngineSwitchRequest } from "../generated/wire";
import { ApiChecks } from "./ApiChecks";
import { Empty } from "../shared/ui/Empty";

const BASELINE = "";
const OTHER = "__other__";

export function sourceLabel(s: EngineSourceOut): string {
  return s.kind === "baseline" ? "pinned baseline" : `${s.remote}/${s.branch}`;
}

export function EngineSourcePanel() {
  const sources = useEngineSources();
  const switcher = useSwitchEngine();
  const checker = useCheckEngine();
  const [checked, setChecked] = useState<{ key: string; info: EngineInfoOut } | null>(null);
  const [remote, setRemote] = useState<string | null>(null);
  const [typedUrl, setTypedUrl] = useState("");
  const [url, setUrl] = useState<string | null>(null);
  const [branch, setBranch] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const active = sources.data?.active;
  const chosenRemote = remote ?? active?.remote ?? BASELINE;
  const repo = chosenRemote === OTHER ? (url ? { url } : null) : chosenRemote === BASELINE ? null : { remote: chosenRemote };
  const branches = useEngineBranches(repo);
  const list = branches.data?.branches ?? [];
  const fallback = chosenRemote === active?.remote && active.branch ? active.branch : list.includes("main") ? "main" : list[0];
  const chosenBranch = branch !== null && list.includes(branch) ? branch : fallback ?? null;

  if (sources.status === "error") return <div className="error">{sources.error.message}</div>;
  if (sources.status !== "success" || !active) return <Empty title="Reading ACT source…" text="" />;

  const isCurrent = chosenRemote === BASELINE
    ? active.kind === "baseline"
    : (chosenRemote === OTHER ? active.url === url : active.remote === chosenRemote) && active.branch === chosenBranch;
  const ready = chosenRemote === BASELINE || (repo !== null && chosenBranch !== null);
  const request: EngineSwitchRequest = repo === null ? {} : { ...repo, branch: chosenBranch };
  const key = `${chosenRemote === OTHER ? url : chosenRemote}/${chosenBranch ?? ""}`;
  const busy = switcher.isPending || checker.isPending;

  async function apply() {
    setErr(null);
    try {
      await switcher.mutateAsync(request);
      setRemote(null);
      setBranch(null);
      setChecked(null);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  async function check() {
    setErr(null);
    try {
      setChecked({ key, info: await checker.mutateAsync(request) });
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="license">
      <div className="kv">
        <span>active</span><b>{sourceLabel(active)}</b>
        {active.kind === "branch" && <>
          <span>commit</span><b className="mono">{active.commit?.slice(0, 12)}</b>
          <span>switched</span><b>{active.switched_at}</b>
        </>}
      </div>

      <form className="licform" onSubmit={(e) => { e.preventDefault(); if (ready && !isCurrent) void apply(); }}>
        <label>Repository
          <select value={chosenRemote} onChange={(e) => { setRemote(e.target.value); setBranch(null); setErr(null); }}>
            <option value={BASELINE}>Pinned baseline</option>
            {sources.data.remotes.map((r) => <option key={r.name} value={r.name} title={r.url}>{r.name}</option>)}
            {sources.data.custom_allowed && <option value={OTHER}>Other repository…</option>}
          </select>
        </label>
        {chosenRemote === OTHER && (
          <label>Repository URL
            <span className="urlrow">
              <input type="url" inputMode="url" spellCheck={false} placeholder="https://github.com/<owner>/ACT.git"
                value={typedUrl} onChange={(e) => setTypedUrl(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); setUrl(typedUrl.trim() || null); setBranch(null); } }} />
              <button type="button" className="secondary" disabled={!typedUrl.trim() || typedUrl.trim() === url}
                onClick={() => { setUrl(typedUrl.trim()); setBranch(null); setErr(null); }}>List branches</button>
            </span>
          </label>
        )}
        {repo !== null && (
          <label>Branch
            {branches.status === "error" ? <span className="error">{branches.error.message}</span> : (
              <select value={chosenBranch ?? ""} disabled={branches.status !== "success"}
                onChange={(e) => { setBranch(e.target.value); setErr(null); }}>
                {branches.status !== "success" && <option value="">Listing branches…</option>}
                {list.map((b) => <option key={b} value={b}>{b}</option>)}
              </select>
            )}
          </label>
        )}
        <div className="actions">
          <button type="button" className="secondary" disabled={!ready || busy} onClick={() => void check()}>
            {checker.isPending ? "Checking ACT API…" : "Check API"}
          </button>
          <button type="submit" className="primary" disabled={!ready || isCurrent || busy}>
            {switcher.isPending ? "Switching and restarting…" : isCurrent ? "Active" : "Switch"}
          </button>
        </div>
      </form>
      {err && <div className="error">{err}</div>}
      {checked && checked.key === key && (
        <div className={`banner ${!checked.info.usable ? "bad" : checked.info.api_checks.some((c) => !c.ok) ? "warn" : "good"}`}>
          <b>{checked.info.usable ? `ACT ${checked.info.commit?.slice(0, 12)} imports.` : "ACT cannot be imported from this checkout."}</b>
          {checked.info.diagnostics.filter((d) => d.code !== "version_mismatch").map((d) => <div key={d.code}>{d.message}</div>)}
          <ApiChecks checks={checked.info.api_checks} />
        </div>
      )}

      <p className="note">
        Any https git repository of an ACT fork can be entered; once its branch imports as ACT it is listed for everyone.
        Check API stages the branch head and verifies every ACT function the workbench calls, without switching.
        Switching restarts the workbench onto that checkout for every user (refused while runs are active); features whose
        API checks fail are disabled. Results on a commit other than the pinned baseline are not baseline-certified.
      </p>
    </div>
  );
}
