// ACT verdict of the selected run, shown at the top of the Verification and BaB modes.
// The verdict is ACT's (RunResultOut.verdict / act_status); this view only labels it.
import { fmt, indexRanges } from "../shared/wire";
import { runDomainLabel } from "./labels";
import type { ModelDescriptionOut, RowVerdictOut, RunOut } from "../generated/wire";
import { useModels } from "../model_spec/hooks";
import { useState } from "react";
import { downloadBlob, imagePng, Pixels, specImageShape, type Shape } from "../shared/ui/pixels";
import { savedCounterexampleUrl } from "./api";
import { useRun, useSaveRunCounterexample, useStopRun } from "./hooks";
import { StopButton } from "../shared/ui/StopButton";

const VERDICT: Record<string, { cls: string; title: string; text: string }> = {
  certified: { cls: "good", title: "CERTIFIED", text: "ACT proved the property holds for every input in the input spec." },
  falsified: { cls: "bad", title: "COUNTEREXAMPLE FOUND", text: "ACT found a concrete input inside the input spec whose output violates the property." },
  unknown: { cls: "warn", title: "UNKNOWN", text: "ACT could neither certify nor falsify the property with this method." },
  timeout: { cls: "warn", title: "TIMEOUT", text: "ACT ran out of budget before reaching a verdict." },
  error: { cls: "bad", title: "ERROR", text: "ACT reported an error instead of a verdict." },
};

export function VerdictBanner({ runId, model }: {
  runId: string | null; model: ModelDescriptionOut;
}) {
  const q = useRun(runId);
  const stopRun = useStopRun();
  if (!runId || q.status !== "success") return null;
  const run = q.data;
  if (run.status === "queued" || run.status === "running") {
    return (
      <div className="banner verdict bannerrow">
        <span><b className="vbig">RUNNING</b> {run.method}{runDomainLabel(run)} · {run.run_id} · no verdict yet.</span>
        <StopButton method={run.method} onStop={() => stopRun.mutateAsync(run.run_id)} />
      </div>
    );
  }
  if (run.status === "failed" || !run.result) {
    return (
      <div className="banner verdict bad">
        <b className="vbig">NO VERDICT</b> The run {run.error?.code === "stopped" ? "was stopped" : "failed"}: {run.error?.message ?? "no result recorded"}
      </div>
    );
  }
  const r = run.result;
  const v = VERDICT[r.verdict] ?? VERDICT.unknown!;
  const rows = r.rows ?? [];
  return (
    <div className={`banner verdict ${v.cls}`}>
      <div className="verdicthead">
        <b className="vbig">{v.title}</b>
        <span className="chip">{run.method}{runDomainLabel(run)}</span>
        <span className="chip mono" title="raw ACT status">{r.act_status}</span>
        <span className="chip">{r.elapsed_s.toFixed(2)} s</span>
        {run.matches_native === true && <span className="chip good" title="matches the recorded native ACT result">= native</span>}
        {run.matches_native === false && <span className="chip warn" title={`native: ${run.native_reference?.status}`}>≠ native</span>}
      </div>
      <div>{rows.length > 0 ? `Batch of ${rows.length} images: the verdict holds for the whole batch only when it holds for every image. ` : ""}{v.text}</div>
      {rows.length > 0 && <RowVerdicts rows={rows} modelId={run.model_id} />}
      {r.verdict === "falsified" && r.counterexample && <Counterexample xs={r.counterexample} run={run} model={model} />}
    </div>
  );
}

// Test-image index of each batch row, from the loaded model's parameters ("3,0,7").
function useBatchImages(modelId: string): number[] | null {
  const models = useModels();
  const p = models.status === "success" ? models.data.find((m) => m.model_id === modelId)?.params : undefined;
  return typeof p?.indices === "string" ? p.indices.split(",").map(Number) : null;
}

// ACT's verdict per batch row: counts per verdict with the image indices compressed to ranges, rows listed on demand.
function RowVerdicts({ rows, modelId }: { rows: RowVerdictOut[]; modelId: string }) {
  const images = useBatchImages(modelId);
  const image = (row: number) => images?.[row] ?? row;
  const groups = Object.keys(VERDICT).map((k) => ({ k, xs: rows.filter((x) => x.verdict === k).map((x) => image(x.row)) }))
    .filter((g) => g.xs.length > 0);
  return (
    <details className="batchchips">
      <summary>
        {groups.map((g) => <span key={g.k} className={`chip ${VERDICT[g.k]!.cls}`} title={`test images ${indexRanges(g.xs)}`}>
          {VERDICT[g.k]!.title.toLowerCase()} {g.xs.length}</span>)}
      </summary>
      <div className="chips" aria-label="verdict per batch image">
        {rows.map((x) => <span key={x.row} className={`chip ${VERDICT[x.verdict]?.cls ?? ""}`} title={`row ${x.row + 1}: ${x.act_status}`}>
          #{image(x.row)} {x.act_status}</span>)}
      </div>
    </details>
  );
}

function Counterexample({ xs, run, model }: { xs: number[]; run: RunOut; model: ModelDescriptionOut }) {
  const images = useBatchImages(run.model_id);
  const row = run.result?.counterexample_row ?? null;
  const spec = model.model_id === run.model_id ? model.input_specs[0] : undefined;
  const s = spec ? specImageShape(spec.shape, spec.dataset) : null;
  const shape = s && s.c * s.h * s.w === xs.length ? s : null;
  const lo = Math.min(...xs), hi = Math.max(...xs);
  const unit = lo >= 0 && hi <= 1;
  return (
    <div className="verdictce">
      {shape && <Pixels xs={xs} shape={shape} lo={unit ? 0 : lo} hi={unit ? 1 : hi} label={row === null ? "counterexample input" : `counterexample · test image #${images?.[row] ?? row}`} size="big" />}
      <span className="mono muted">
        x = [{xs.slice(0, 8).map((v) => fmt(v, 3)).join(", ")}{xs.length > 8 ? `, … (${xs.length})` : ""}]
      </span>
      <SaveExport run={run} xs={xs} shape={shape} lo={unit ? 0 : lo} hi={unit ? 1 : hi} />
    </div>
  );
}

// Save ACT's counterexample on the run record, then export it as a VNN-COMP witness and, for images, a PNG.
function SaveExport({ run, xs, shape, lo, hi }: { run: RunOut; xs: number[]; shape: Shape | null; lo: number; hi: number }) {
  const save = useSaveRunCounterexample();
  const [err, setErr] = useState<string | null>(null);
  const noOutput = run.result?.counterexample_output == null;
  async function png() {
    setErr(null);
    try {
      downloadBlob(await imagePng(xs, shape!, lo, hi), `${run.run_id}-ce.png`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }
  if (!run.counterexample_saved_at) {
    return (
      <span className="ceactions">
        <button className="secondary small" disabled={save.isPending} onClick={() => save.mutate(run.run_id)}>
          {save.isPending ? "Saving…" : "Save counterexample"}</button>
        {save.error && <span className="state bad">{save.error.message}</span>}
      </span>
    );
  }
  return (
    <span className="ceactions">
      <span className="chip good" title={`saved on this run's record ${new Date(run.counterexample_saved_at).toLocaleString()}`}>saved</span>
      {noOutput
        ? <span className="chip warn" title={run.result?.counterexample_output_error ?? undefined}>no VNN-LIB export: output not computed</span>
        : <a className="button secondary small" href={savedCounterexampleUrl(run.run_id)} download
            title="VNN-COMP result: sat + VNN-LIB 2.0 command-line assignment of X (input) and Y (output), float64">Export counterexample (VNN-LIB 2.0)</a>}
      {shape && <button className="secondary small" onClick={() => void png()}
        title={`${shape.w}×${shape.h} PNG of the counterexample input at native resolution`}>Export image (.png)</button>}
      {err && <span className="state bad">{err}</span>}
    </span>
  );
}
