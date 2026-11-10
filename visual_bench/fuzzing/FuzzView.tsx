// ACTFuzzer progress and result composition; ACT owns all scientific results.
import { useEffect, useState } from "react";
import { fmt } from "../shared/wire";
import type { FuzzingOut, ModelDescriptionOut } from "../generated/wire";
import { Empty } from "../shared/ui/Empty";
import { useFuzzing, useSaveCounterexample } from "./hooks";
import { pct } from "./presentation";
import { FuzzTimeline } from "./FuzzTimeline";
import { FuzzMutations } from "./FuzzMutations";
import { FuzzCounterexamples } from "./FuzzCounterexamples";
import { FuzzSaved } from "./FuzzSaved";
import { FuzzInputs } from "./FuzzInputs";
import { FuzzStrategies } from "./FuzzStrategies";
import { FuzzLiveControls } from "./FuzzLiveControls";

export function FuzzView({ runId, model }: { runId: string | null; model: ModelDescriptionOut | null }) {
  const [frameSel, setFrameSel] = useState<number | null>(null); // null follows the latest frame
  const q = useFuzzing(runId);
  const save = useSaveCounterexample(runId ?? "");
  useEffect(() => { setFrameSel(null); }, [runId]);
  const f = q.data;
  const live = f !== undefined && (f.status === "queued" || f.status === "running");

  if (!runId) return <Empty title="No run selected" text="Pick a model, choose method “fuzz (ACTFuzzer)” and press Run ACT." />;
  if (q.status === "error") return <div className="error">{q.error.message}</div>;
  if (!f) return <Empty title="Loading fuzzing record…" text="" />;
  if (f.availability === "unsupported") return <Empty title="Not a fuzzing run" text="This run used a verification method. Start a run with method “fuzz (ACTFuzzer)”." />;
  const last = f.timeline.at(-1) ?? null;
  const s = f.summary;
  const maxIterations = f.control?.live.max_iterations ?? f.options?.max_iterations;
  const ces = s?.counterexample_count ?? last?.counterexamples ?? 0;
  const frames = f.frames ?? [];
  const savedItems = f.saved ?? [];
  const saved = new Set(savedItems.map((s) => s.counterexample.index));
  const onSave = async (index: number) => { await save.mutateAsync(index); };
  return (
    <div className="fuzz">
      <Banner f={f} ces={ces} />
      <FuzzLiveControls key={f.run_id} f={f} />
      <div className="kv">
        <span>iterations</span><b>{s?.iterations ?? last?.iteration ?? 0}{maxIterations != null ? ` / ${maxIterations}` : ""}</b>
        <span>elapsed</span><b>{fmt(s?.elapsed_s ?? last?.elapsed_s ?? 0, 2)} s{s && s.elapsed_s > 0 ? ` · ${(s.iterations / s.elapsed_s).toFixed(1)} it/s` : ""}</b>
        <span>neuron coverage</span><b>{pct(s?.neuron_coverage ?? last?.coverage ?? 0)}{s ? ` (${s.coverage_strategy})` : ""}</b>
        <span>counterexamples</span><b className={ces ? "state bad" : ""}>{ces}</b>
        <span>seed corpus</span><b>{s?.seeds_explored ?? last?.corpus ?? 0}</b>
        {s && <><span>mutations</span><b>{s.total_mutations}</b></>}
        {s && <><span>never activated</span><b>{s.never_activated_count}{s.never_activated_sample.length ? ` · ${s.never_activated_sample.slice(0, 6).join(", ")}` : ""}</b></>}
        <span>rng seed</span><b>{f.options?.rng_seed ?? "—"}{s ? ` · device ${s.device}` : ""}</b>
        {s?.stop_reason && <><span>stop reason</span><b>{({
          max_iterations: "Iteration limit", timeout: "Time limit", first_violation: "First counterexample", stopped: "Stopped by user",
        } as Record<string, string>)[s.stop_reason] ?? s.stop_reason}</b></>}
      </div>
      <h3>Progress <small>{live ? "live from committed fuzz.progress events" : "recorded timeline"}</small></h3>
      <div className="fuzzlive">
        <div className="fuzzlive-chart">
          <FuzzTimeline points={f.timeline} firstCe={f.counterexamples[0]?.iteration ?? null}
            marker={frames.length ? frames[Math.min(frameSel ?? Infinity, frames.length - 1)]!.iteration : null} />
        </div>
        <FuzzMutations frames={frames} live={live} model={model} sel={frameSel} onSel={setFrameSel} saved={saved} onSave={onSave} />
      </div>
      {savedItems.length > 0 && <FuzzSaved runId={f.run_id} items={savedItems} model={model} />}
      {f.availability === "available" && <FuzzInputs f={f} model={model} />}
      {f.counterexamples.length > 0 && (
        <FuzzCounterexamples items={f.counterexamples} total={ces} model={model} saved={saved} onSave={onSave} live={live} />
      )}
      {f.strategies.length > 0 && <FuzzStrategies f={f} />}
      {Object.keys(f.config).length > 0 && (
        <p className="note">ACT config: {Object.entries(f.config).map(([k, v]) => `${k}=${String(v)}`).join(" · ")}</p>
      )}
      <p className="note">{f.provenance.act_call} · {f.provenance.config}</p>
    </div>
  );
}

function Banner({ f, ces }: { f: FuzzingOut; ces: number }) {
  if (f.status === "failed") return <div className="banner bad"><b>Run failed.</b> The partial timeline below is what ACT reported before the failure.</div>;
  if (f.availability === "pending") {
    return (
      <div className="banner">
        <span><b>Fuzzing…</b> {ces ? `${ces} counterexample(s) found so far.` : "No counterexample yet."}</span>
      </div>
    );
  }
  const stopped = f.summary?.stopped
    ? <> Stopped by the user after {f.summary.iterations} iteration(s); ACT's report covers those iterations only.</> : null;
  if (stopped && ces === 0) return <div className="banner warn"><b>Stopped, no counterexample found.</b>{stopped} Fuzzing is heuristic: this is not a proof.</div>;
  if (ces > 0) {
    return <div className="banner bad"><b>Property violated (falsified).</b> ACT's PropertyChecker accepted {ces} concrete input(s) inside the input spec whose outputs violate the property.{stopped}</div>;
  }
  return <div className="banner warn"><b>No counterexample found.</b> Fuzzing is heuristic: this is not a proof. Use interval or BaB to certify.</div>;
}
