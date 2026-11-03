// Load a model from a VNN-LIB instance or build one from an image classifier with a chosen test image and eps (MSV-04).
import { useEffect, useState } from "react";
import { api, fmt } from "../api";
import type { ModelSummary, SourcesOut } from "../generated/wire";
import { classLabel, Pixels } from "../workspace/pixels";
import { useQuery } from "../workspace/useQuery";

type Mode = "vnnlib" | "torch";

export function LoadPanel({ current, onLoaded }: { current: ModelSummary | null; onLoaded: (m: ModelSummary) => void }) {
  const sources = useQuery("sources", api.sources);
  const [mode, setMode] = useState<Mode>("torch");
  useEffect(() => {
    if (current?.source === "vnnlib" || current?.source === "torch") setMode(current.source);
  }, [current]);
  return (
    <section className="panel loadpanel">
      <h2>Load model</h2>
      <nav className="tabs" role="tablist" aria-label="model source">
        {(["torch", "vnnlib"] as const).map((m) => (
          <button key={m} role="tab" aria-selected={mode === m} className={mode === m ? "tab active" : "tab"} onClick={() => setMode(m)}>
            {m === "torch" ? "Torch model" : "VNN-LIB"}
          </button>
        ))}
      </nav>
      {sources.status === "loading" && <div className="note">Reading sources from ACT…</div>}
      {sources.status === "error" && <div className="error">{sources.message}</div>}
      {sources.status === "ok" && (mode === "torch"
        ? <TorchForm s={sources.data} current={current?.source === "torch" ? current : null} onLoaded={onLoaded} />
        : <VnnlibForm s={sources.data} current={current?.source === "vnnlib" ? current : null} onLoaded={onLoaded} />)}
    </section>
  );
}

function useLoad(onLoaded: (m: ModelSummary) => void) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const run = (body: Parameters<typeof api.loadModel>[0]) => {
    setBusy(true);
    setError(null);
    api.loadModel(body).then(onLoaded, (e: unknown) => setError(e instanceof Error ? e.message : String(e))).finally(() => setBusy(false));
  };
  return { busy, error, run };
}

function TorchForm({ s, current, onLoaded }: { s: SourcesOut; current: ModelSummary | null; onLoaded: (m: ModelSummary) => void }) {
  const [sourceId, setSourceId] = useState(s.classifiers[0]?.source_id ?? "");
  const [index, setIndex] = useState(0);
  const [eps, setEps] = useState(2 / 255);
  useEffect(() => {
    if (!current) return;
    const p = current.params ?? {};
    if (typeof p.source_id === "string") setSourceId(p.source_id);
    if (typeof p.index === "number") setIndex(p.index);
    if (typeof p.eps === "number") setEps(p.eps);
  }, [current]);
  const src = s.classifiers.find((c) => c.source_id === sourceId) ?? null;
  const sample = useQuery(src ? `${src.dataset}:${index}` : null, () => api.sample(src!.dataset, index));
  const size = sample.status === "ok" ? sample.data.size : 10000;
  const load = useLoad(onLoaded);
  if (s.classifiers.length === 0) {
    return <div className="note">No classifier ONNX models or datasets found in the ACT checkout (literature/, data/torchvision/).</div>;
  }
  const step = (d: number) => setIndex((i) => Math.min(size - 1, Math.max(0, i + d)));
  return (
    <div className="loadform">
      <label>Model
        <select value={sourceId} onChange={(e) => setSourceId(e.target.value)}>
          {s.classifiers.map((c) => <option key={c.source_id} value={c.source_id}>{c.description}</option>)}
        </select>
      </label>
      <label>Input: {src?.dataset} test image
        <span className="stepper">
          <button onClick={() => step(-1)} disabled={index <= 0} aria-label="previous image">◀</button>
          <input type="number" min={0} max={size - 1} value={index}
            onChange={(e) => setIndex(Math.min(size - 1, Math.max(0, Math.trunc(Number(e.target.value) || 0))))} />
          <button onClick={() => step(1)} disabled={index >= size - 1} aria-label="next image">▶</button>
          <button onClick={() => setIndex(Math.floor(Math.random() * size))}>random</button>
        </span>
      </label>
      <div className="samplepreview">
        {sample.status === "ok" ? (
          <Pixels xs={sample.data.pixels} shape={{ c: sample.data.shape[0]!, h: sample.data.shape[1]!, w: sample.data.shape[2]! }}
            lo={0} hi={1} size="big" label={`#${index} · label ${classLabel(src?.dataset, sample.data.label)}`} />
        ) : sample.status === "error" ? <div className="error">{sample.message}</div> : <div className="note">Loading image…</div>}
      </div>
      <label>eps (L∞ radius) = {fmt(eps, 4)} ≈ {fmt(eps * 255, 1)}/255
        <span className="epsrow">
          <input type="range" min={0} max={0.3} step={1 / 255} value={eps} onChange={(e) => setEps(Number(e.target.value))} aria-label="eps slider" />
          <input type="number" min={0} max={1} step={0.001} value={Number(eps.toFixed(4))} onChange={(e) => setEps(Math.min(1, Math.max(0, Number(e.target.value) || 0)))} aria-label="eps value" />
        </span>
      </label>
      <button className="primary" disabled={load.busy || !src}
        onClick={() => load.run({ source: { kind: "torch", source_id: sourceId, index, eps } })}>
        {load.busy ? "Building through ACT…" : current ? "Rebuild with these settings" : "Build and load"}
      </button>
      {load.error && <div className="error">{load.error}</div>}
      <div className="note">Box = test image ± eps clipped to [0, 1]; property: the model keeps the dataset label (TOP1_ROBUST). Built by ACT's front end; each setting is its own model snapshot.</div>
    </div>
  );
}

function VnnlibForm({ s, current, onLoaded }: { s: SourcesOut; current: ModelSummary | null; onLoaded: (m: ModelSummary) => void }) {
  const [bench, setBench] = useState(s.vnnlib.find((b) => b.benchmark === "cora_2024")?.benchmark ?? s.vnnlib[0]?.benchmark ?? "");
  const [inst, setInst] = useState(0);
  useEffect(() => {
    if (!current) return;
    const p = current.params ?? {};
    const b = s.vnnlib.find((x) => x.benchmark === p.benchmark);
    if (!b) return;
    setBench(b.benchmark);
    setInst(Math.max(0, b.instances.findIndex((i) => i.onnx === p.onnx && i.vnnlib === p.vnnlib)));
  }, [current, s]);
  const load = useLoad(onLoaded);
  if (s.vnnlib.length === 0) return <div className="note">No VNN-LIB benchmarks found under {s.vnnlib_root}.</div>;
  const b = s.vnnlib.find((x) => x.benchmark === bench) ?? s.vnnlib[0]!;
  const i = b.instances[Math.min(inst, b.instances.length - 1)]!;
  return (
    <div className="loadform">
      <label>Benchmark
        <select value={b.benchmark} onChange={(e) => { setBench(e.target.value); setInst(0); }}>
          {s.vnnlib.map((x) => <option key={x.benchmark} value={x.benchmark}>{x.benchmark} ({x.instances.length})</option>)}
        </select>
      </label>
      <label>Instance (ONNX model · VNN-LIB property)
        <select value={inst} onChange={(e) => setInst(Number(e.target.value))}>
          {b.instances.map((x, k) => <option key={k} value={k}>{shortName(x.onnx)} · {shortName(x.vnnlib)}</option>)}
        </select>
      </label>
      <button className="primary" disabled={load.busy}
        onClick={() => load.run({ source: { kind: "vnnlib", benchmark: b.benchmark, onnx: i.onnx, vnnlib: i.vnnlib } })}>
        {load.busy ? "Loading through ACT…" : "Load instance"}
      </button>
      {load.error && <div className="error">{load.error}</div>}
      <div className="note">ACT converts the ONNX model and parses the VNN-LIB file; its first query becomes the input box and property.</div>
    </div>
  );
}

function shortName(path: string): string {
  return path.split("/").at(-1)!.replace(/\.(onnx|vnnlib)$/, "");
}
