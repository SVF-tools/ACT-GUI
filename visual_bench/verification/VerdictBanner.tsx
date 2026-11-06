// ACT verdict of the selected run, shown at the top of the Verification and BaB modes.
// The verdict is ACT's (RunResultOut.verdict / act_status); this view only labels it.
import { fmt, indexRanges } from "../shared/wire";
import { runDomainLabel } from "./labels";
import type { ModelDescriptionOut, RowVerdictOut, RunOut, RunResultOut } from "../generated/wire";
import { useBatchRows } from "../model_spec/hooks";
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
  const [pick, setPick] = useState<{ run: string; row: number | null } | null>(null);
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
  const ces = counterexamples(r);
  const want = pick?.run === run.run_id ? pick.row : r.counterexample_row ?? null;
  const ce = ces.find((c) => c.row === want) ?? ces[0];
  const choose = (row: number | null) => setPick({ run: run.run_id, row });
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
      <div>{rows.length > 0 ? <BatchNote n={rows.length} modelId={run.model_id} /> : ""}{v.text}</div>
      {rows.length > 0 && <RowVerdicts rows={rows} modelId={run.model_id} selected={ce?.row ?? null}
        pickable={new Set(ces.map((c) => c.row))} onPick={choose} />}
      {r.verdict === "falsified" && ce && <Counterexample ce={ce} all={ces} onPick={choose} run={run} model={model} />}
    </div>
  );
}

function BatchNote({ n, modelId }: { n: number; modelId: string }) {
  const noun = useBatchRows(modelId)?.noun ?? "row";
  const plural = noun === "property" ? "properties" : `${noun}s`;
  return <>Batch of {n} {plural}: the verdict holds for the whole batch only when it holds for every {noun}. </>;
}

// ACT's counterexample of one batch row (row null: a single-row net), with the output for its VNN-COMP export.
type RowCe = { row: number | null; xs: number[]; output: number[] | null; outputError: string | null };

// Every counterexample ACT reported: one per falsified batch row; runs recorded before per-row counterexamples (and
// single-row nets) only carry the summary one.
function counterexamples(r: RunResultOut): RowCe[] {
  const perRow = (r.rows ?? []).flatMap((x) => x.counterexample ? [{ row: x.row, xs: x.counterexample,
    output: x.counterexample_output ?? null, outputError: x.counterexample_output_error ?? null }] : []);
  if (perRow.length > 0) return perRow;
  return r.counterexample ? [{ row: r.counterexample_row ?? null, xs: r.counterexample,
    output: r.counterexample_output ?? null, outputError: r.counterexample_output_error ?? null }] : [];
}

// ACT's verdict per batch row: counts per verdict (image indices compressed to ranges), rows listed on demand.
// Rows with a counterexample are clickable and select the counterexample shown (and saved/exported) below.
function RowVerdicts({ rows, modelId, selected, pickable, onPick }: {
  rows: RowVerdictOut[]; modelId: string; selected: number | null; pickable: Set<number | null>; onPick: (row: number) => void;
}) {
  const batch = useBatchRows(modelId);
  const label = (row: number) => batch?.labels[row] ?? `row ${row + 1}`;
  const groups = Object.keys(VERDICT).map((k) => ({ k, rs: rows.filter((x) => x.verdict === k).map((x) => x.row) }))
    .filter((g) => g.rs.length > 0);
  const title = (rs: number[]) => batch?.images
    ? `test images ${indexRanges(rs.map((r) => batch.images![r]!))}` : rs.map(label).join(", ");
  return (
    <details className="batchchips">
      <summary>
        {groups.map((g) => <span key={g.k} className={`chip ${VERDICT[g.k]!.cls}`} title={title(g.rs)}>
          {VERDICT[g.k]!.title.toLowerCase()} {g.rs.length}</span>)}
      </summary>
      <div className="chips" aria-label="verdict per batch row">
        {rows.map((x) => pickable.has(x.row)
          ? <button key={x.row} type="button" className={`chip ${VERDICT[x.verdict]?.cls ?? ""}${x.row === selected ? " active" : ""}`}
              title={`row ${x.row + 1}: ${x.act_status} · show this row's counterexample`} onClick={() => onPick(x.row)}>
              {label(x.row)} {x.act_status}</button>
          : <span key={x.row} className={`chip ${VERDICT[x.verdict]?.cls ?? ""}`} title={`row ${x.row + 1}: ${x.act_status}`}>
              {label(x.row)} {x.act_status}</span>)}
      </div>
    </details>
  );
}

function Counterexample({ ce, all, onPick, run, model }: {
  ce: RowCe; all: RowCe[]; onPick: (row: number | null) => void; run: RunOut; model: ModelDescriptionOut;
}) {
  const batch = useBatchRows(run.model_id);
  const xs = ce.xs, row = ce.row;
  const spec = model.model_id === run.model_id ? model.input_specs[0] : undefined;
  const s = spec ? specImageShape(spec.shape, spec.dataset) : null;
  const shape = s && s.c * s.h * s.w === xs.length ? s : null;
  const lo = Math.min(...xs), hi = Math.max(...xs);
  const unit = lo >= 0 && hi <= 1;
  const name = (r: number) => `${batch?.noun === "image" ? "test image " : ""}${batch?.labels[r] ?? `row ${r + 1}`}`;
  return (
    <div className="verdictce">
      {all.length > 1 && (
        <label className="ceselect" title="ACT found a counterexample on each of these batch rows">
          counterexample of{" "}
          <select value={row ?? ""} onChange={(e) => onPick(Number(e.target.value))}>
            {all.map((c) => <option key={c.row} value={c.row ?? ""}>{name(c.row!)}</option>)}
          </select>
          <small className="muted"> ({all.length} falsified)</small>
        </label>
      )}
      {shape && <Pixels key={row} xs={xs} shape={shape} lo={unit ? 0 : lo} hi={unit ? 1 : hi} label={row === null ? "counterexample input" : `counterexample · ${name(row)}`} size="big" />}
      <span className="mono muted">
        x = [{xs.slice(0, 8).map((v) => fmt(v, 3)).join(", ")}{xs.length > 8 ? `, … (${xs.length})` : ""}]
      </span>
      <SaveExport run={run} ce={ce} shape={shape} lo={unit ? 0 : lo} hi={unit ? 1 : hi} />
    </div>
  );
}

// Save ACT's counterexample (of the selected batch row) on the run record, then export it as a VNN-COMP witness and,
// for images, a PNG.
function SaveExport({ run, ce, shape, lo, hi }: { run: RunOut; ce: RowCe; shape: Shape | null; lo: number; hi: number }) {
  const save = useSaveRunCounterexample();
  const [err, setErr] = useState<string | null>(null);
  const { row, xs } = ce;
  const tag = row === null ? "" : `-row${row}`;
  const saved = (run.saved_counterexample_rows ?? []).includes(row ?? 0);
  async function png() {
    setErr(null);
    try {
      downloadBlob(await imagePng(xs, shape!, lo, hi), `${run.run_id}${tag}-ce.png`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }
  if (!saved) {
    return (
      <span className="ceactions">
        <button className="secondary small" disabled={save.isPending} onClick={() => save.mutate({ id: run.run_id, row })}>
          {save.isPending ? "Saving…" : row === null ? "Save counterexample" : `Save counterexample (row ${row + 1})`}</button>
        {save.error && <span className="state bad">{save.error.message}</span>}
      </span>
    );
  }
  return (
    <span className="ceactions">
      <span className="chip good" title="saved on this run's record">saved</span>
      {ce.output == null
        ? <span className="chip warn" title={ce.outputError ?? undefined}>no VNN-LIB export: output not computed</span>
        : <a className="button secondary small" href={savedCounterexampleUrl(run.run_id, row)} download
            title="VNN-COMP result: sat + VNN-LIB 2.0 command-line assignment of X (input) and Y (output), float64">Export counterexample (VNN-LIB 2.0)</a>}
      {shape && <button className="secondary small" onClick={() => void png()}
        title={`${shape.w}×${shape.h} PNG of the counterexample input at native resolution`}>Export image (.png)</button>}
      {err && <span className="state bad">{err}</span>}
    </span>
  );
}
