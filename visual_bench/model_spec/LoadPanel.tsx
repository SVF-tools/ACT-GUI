// Load a model from a VNN-LIB instance or build one from an image classifier with a chosen test image and eps (MSV-04).
import { useEffect, useState } from "react";
import { fmt, indexRanges } from "../shared/wire";
import type { ModelSummary, SourcesOut } from "../generated/wire";
import { classLabel, Pixels } from "../shared/ui/pixels";
import { useSources, useSample, useLoadModel } from "./hooks";
import type { LoadModelBody } from "../generated/wire";

type Mode = "vnnlib" | "torch";
const BATCH_LIMIT = 64; // engine_bridge.model_spec.sources.BATCH_LIMIT

export function LoadPanel({ current, onLoaded }: { current: ModelSummary | null; onLoaded: (m: ModelSummary) => void }) {
  const sources = useSources();
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
      {sources.status === "pending" && <div className="note">Reading sources from ACT…</div>}
      {sources.status === "error" && <div className="error">{sources.error.message}</div>}
      {sources.status === "success" && (mode === "torch"
        ? <TorchForm s={sources.data} current={current?.source === "torch" ? current : null} onLoaded={onLoaded} />
        : <VnnlibForm s={sources.data} current={current?.source === "vnnlib" ? current : null} onLoaded={onLoaded} />)}
    </section>
  );
}

function useLoad(onLoaded: (m: ModelSummary) => void) {
  const mutation = useLoadModel();
  return {
    busy: mutation.isPending,
    error: mutation.error?.message ?? null,
    run: (body: LoadModelBody) => mutation.mutate(body, { onSuccess: onLoaded }),
  };
}

function TorchForm({ s, current, onLoaded }: { s: SourcesOut; current: ModelSummary | null; onLoaded: (m: ModelSummary) => void }) {
  const [sourceId, setSourceId] = useState(s.classifiers[0]?.source_id ?? "");
  // One test image per batch slot; a batch of several is one ACT net with a row per image (fuzz-only).
  const [indices, setIndices] = useState<number[]>([0]);
  const [slot, setSlot] = useState(0);
  const [eps, setEps] = useState(2 / 255);
  useEffect(() => {
    if (!current) return;
    const p = current.params ?? {};
    if (typeof p.source_id === "string") setSourceId(p.source_id);
    if (typeof p.indices === "string") setIndices(p.indices.split(",").map(Number));
    else if (typeof p.index === "number") setIndices([p.index]);
    setSlot(0);
    if (typeof p.eps === "number") setEps(p.eps);
  }, [current]);
  const src = s.classifiers.find((c) => c.source_id === sourceId) ?? null;
  const index = indices[slot] ?? indices[0]!;
  const sample = useSample(src?.dataset ?? null, index);
  const size = sample.status === "success" ? sample.data.size : 10000;
  const load = useLoad(onLoaded);
  if (s.classifiers.length === 0) {
    return <div className="note">No classifier ONNX models or datasets found in the ACT checkout (literature/, data/torchvision/).</div>;
  }
  const clamp = (i: number) => Math.min(size - 1, Math.max(0, Math.trunc(i) || 0));
  const setIndex = (i: number) => setIndices((xs) => xs.map((x, k) => (k === slot ? clamp(i) : x)));
  const step = (d: number) => setIndex(index + d);
  // Growing the batch appends the next unused images after the last slot; shrinking drops the tail.
  const resize = (n: number) => {
    const want = Math.min(BATCH_LIMIT, Math.max(1, Math.trunc(n) || 1));
    setIndices((xs) => {
      if (want <= xs.length) return xs.slice(0, want);
      const out = [...xs];
      for (let i = (xs[xs.length - 1] ?? -1) + 1; out.length < want && i < size; i++) if (!out.includes(i)) out.push(i);
      return out;
    });
    setSlot((k) => Math.min(k, want - 1));
  };
  const duplicate = indices.some((x, k) => indices.indexOf(x) !== k);
  const batched = indices.length > 1;
  return (
    <div className="loadform">
      <label>Model
        <select value={sourceId} onChange={(e) => setSourceId(e.target.value)}>
          {s.classifiers.map((c) => <option key={c.source_id} value={c.source_id}>{c.description}</option>)}
        </select>
      </label>
      <div className="batchrow">
        <label>Batch size
          <input type="number" min={1} max={BATCH_LIMIT} value={indices.length} onChange={(e) => resize(Number(e.target.value))} />
        </label>
        {batched && (
          <label>Edit image
            <select value={slot} onChange={(e) => setSlot(Number(e.target.value))}>
              {indices.map((x, k) => <option key={k} value={k}>{k + 1} of {indices.length} · test image #{x}</option>)}
            </select>
          </label>
        )}
      </div>
      <label>Input: {src?.dataset} test image{batched ? ` (image ${slot + 1} of ${indices.length})` : ""}
        <span className="stepper">
          <button onClick={() => step(-1)} disabled={index <= 0} aria-label="previous image">◀</button>
          <input type="number" min={0} max={size - 1} value={index} onChange={(e) => setIndex(Number(e.target.value))} />
          <button onClick={() => step(1)} disabled={index >= size - 1} aria-label="next image">▶</button>
          <button onClick={() => setIndex(Math.floor(Math.random() * size))}>random</button>
        </span>
      </label>
      {batched && (
        <details className="batchchips">
          <summary title={indexRanges(indices)}>{indices.length} images: {indexRanges(indices)}</summary>
          <div className="chips" aria-label="batch images">
            {indices.map((x, k) => (
              <button key={k} className={k === slot ? "chip active" : indices.indexOf(x) !== k ? "chip warn" : "chip"}
                onClick={() => setSlot(k)} title={`edit image ${k + 1}`}>#{x}</button>
            ))}
          </div>
        </details>
      )}
      {duplicate && <div className="error">Each image of a batch must be a different test image.</div>}
      <div className="samplepreview">
        {sample.status === "success" ? (
          <Pixels xs={sample.data.pixels} shape={{ c: sample.data.shape[0]!, h: sample.data.shape[1]!, w: sample.data.shape[2]! }}
            lo={0} hi={1} size="big" label={`#${index} · label ${classLabel(src?.dataset, sample.data.label)}`} />
        ) : sample.status === "error" ? <div className="error">{sample.error.message}</div> : <div className="note">Loading image…</div>}
      </div>
      <label>eps (L∞ radius) = {fmt(eps, 4)} ≈ {fmt(eps * 255, 1)}/255
        <span className="epsrow">
          <input type="range" min={0} max={0.3} step={1 / 255} value={eps} onChange={(e) => setEps(Number(e.target.value))} aria-label="eps slider" />
          <input type="number" min={0} max={1} step={0.001} value={Number(eps.toFixed(4))} onChange={(e) => setEps(Math.min(1, Math.max(0, Number(e.target.value) || 0)))} aria-label="eps value" />
        </span>
      </label>
      <button className="primary" disabled={load.busy || !src || duplicate}
        onClick={() => load.run({ source: { kind: "torch", source_id: sourceId, index: indices[0]!, eps,
          ...(batched ? { indices: [indices[0]!, ...indices.slice(1)] as [number, ...number[]] } : {}) } })}>
        {load.busy ? "Building through ACT…" : current ? "Rebuild with these settings" : "Build and load"}
      </button>
      {load.error && <div className="error">{load.error}</div>}
      <div className="note">Box = test image ± eps clipped to [0, 1]; property: the model keeps the dataset label (TOP1_ROBUST). Built by ACT's front end; each setting is its own model snapshot.
        {batched ? " A batch is one net with a row per image that ACTFuzzer fuzzes together; ACT's verify_once does not accept it, so it is fuzz-only." : ""}</div>
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
